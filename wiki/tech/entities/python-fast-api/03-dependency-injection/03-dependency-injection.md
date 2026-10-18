---
type: concept
domain: tech
tags: [python, fastapi, dependency-injection, depends, yield, lifespan, scoped, testing]
sources: []
created: 2026-08-15
updated: 2026-08-15
---

# 第 03 章：Depends — FastAPI 的依賴注入，以及它和 .NET DI 不一樣的地方

## 一個關不掉的 session

上線後偶爾出現的 500，log 裡是這一行：

```text
sqlalchemy.exc.ResourceClosedError: This Connection is closed
```

出錯的程式碼看起來很正常——收到 webhook，先回 202 讓對方別等，實際處理丟到背景：

```python
@app.post("/webhook", status_code=202)
def webhook(payload: Event, db: DbSession, background: BackgroundTasks):
    background.add_task(save_event, db, payload)   # ← 問題在這
    return {"accepted": True}
```

`db` 是從 `yield` dependency 拿到的 session。而 `yield` 之後的收尾程式碼，**在回應送出之前就已經執行了**——session 早就關掉，背景任務拿到的是一個死掉的連線。

這段程式碼在幾年前的 FastAPI 是能動的。0.106 版改了 `yield` dependency 的執行時機，於是所有照著舊文章寫的專案都會在這裡踩一次。

要看懂這種問題，需要知道三件事：`Depends` 到底做了什麼、依賴的生命週期由誰決定、以及 `yield` 前後那兩段程式碼各自在什麼時候跑。這一章把它們講完。

讀完之後，你應該能夠對照出 FastAPI 的依賴機制與 .NET DI 容器的三個根本差異，並且知道 Singleton、Scoped、Transient 這三種生命週期在 FastAPI 裡分別要怎麼實作。

---

## 一、`Depends` 做的事只有一句話

```python
from typing import Annotated
from fastapi import Depends

def get_current_user(token: Annotated[str, Header()]) -> User:
    return decode(token)

@app.get("/me")
def me(user: Annotated[User, Depends(get_current_user)]):
    return user
```

`Depends(get_current_user)` 的意思是：**請求進來時呼叫 `get_current_user`，把回傳值填進 `user` 這個參數**。

就這樣。沒有容器、沒有註冊、沒有介面對應表。`Depends` 收的就是一個可呼叫物件，而 FastAPI 會像對待 path operation 一樣讀它的簽章——所以 `get_current_user` 自己需要的 `token` 也會被自動解析（從 header 取），這件事是遞迴的。

從 .NET 過來的人要調整三個預設想法：

| | ASP.NET Core | FastAPI |
| --- | --- | --- |
| 註冊 | `builder.Services.AddScoped<IFoo, Foo>()` 集中註冊 | 沒有註冊表，`Depends(函式)` 直接指定 |
| 抽象 | 註冊介面→實作，換實作改一行設定 | 沒有這層對應；換實作用 `dependency_overrides` 或自己傳工廠 |
| 解析時機 | 啟動時建好依賴圖並驗證，缺註冊會在啟動時炸 | **每個 request 現場解析**，寫錯到執行時才知道 |

第三點的實務意義最大。ASP.NET Core 啟動時就會告訴你「`IFoo` 沒註冊」；FastAPI 只有在那條路由被打到的時候才會發現問題。這讓測試覆蓋率變得比較重要——沒被測到的 endpoint，你不知道它的依賴鏈是否成立。

換來的好處是**沒有「服務註冊在哪個檔案」這種考古工作**。`Depends(get_db)` 點進去就是實作，依賴關係在簽章上一目了然。

### 用 `Annotated` 抽別名

同一個依賴會出現在幾十支函式上，每次寫全稱太囉唆：

```python
# app/api/deps.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

```python
@app.get("/orders")
def list_orders(db: DbSession, user: CurrentUser):
    ...
```

簽章乾淨、型別提示完整、IDE 補全正常。這是目前的主流寫法，本教材後面一律這樣用。

---

## 二、依賴可以是任何 callable

### 函式（最常見）

```python
def pagination(skip: int = 0, limit: int = Query(default=20, le=100)) -> dict:
    return {"skip": skip, "limit": limit}

Pagination = Annotated[dict, Depends(pagination)]
```

注意這個依賴自己宣告了 query 參數。掛上它的 endpoint 會**自動獲得 `skip` 和 `limit` 兩個 query 參數**，而且出現在 `/docs` 上。這是 FastAPI 依賴機制最漂亮的一點：依賴不只提供值，還會把自己的參數需求「往上冒泡」到 endpoint 的介面契約裡。

ASP.NET Core 沒有直接對應——那邊要用 model binding 加自訂 binder，或用 `[FromQuery] PaginationDto` 綁一個物件。

### 類別

```python
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 20):
        self.skip = skip
        self.limit = limit

@app.get("/items")
def list_items(page: Annotated[Pagination, Depends()]):
    ...
```

FastAPI 讀的是 `__init__` 的簽章。`Depends()` 括號留空是簡寫——型別已經寫在 `Annotated` 裡了，不必重複。回傳的是型別明確的物件，比 dict 好用。

### 可呼叫的實例（參數化依賴）

需要「同一個邏輯、不同設定」的時候：

```python
class RequireRole:
    def __init__(self, role: str):
        self.role = role

    def __call__(self, user: CurrentUser) -> User:
        if self.role not in user.roles:
            raise HTTPException(403, "權限不足")
        return user

@app.delete("/users/{user_id}", dependencies=[Depends(RequireRole("admin"))])
def delete_user(user_id: int): ...
```

`RequireRole("admin")` 建出一個實例，這個實例因為有 `__call__` 所以是可呼叫的，FastAPI 讀它 `__call__` 的簽章。這是 FastAPI 版的授權 policy，第 07 章會擴充。

---

## 三、巢狀依賴與快取

依賴可以依賴別的依賴，形成一張圖：

```python
def get_db(): ...

def get_token(authorization: Annotated[str, Header()]) -> str: ...

def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(get_token)],
) -> User: ...

def get_active_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_active:
        raise HTTPException(403, "帳號已停用")
    return user
```

```text
endpoint
  └── get_active_user
        └── get_current_user
              ├── get_db
              └── get_token
                    └── Header
```

FastAPI 會拓撲排序這張圖，由葉往根解析。同一個 request 內，**同一個依賴預設只會被呼叫一次**，結果快取起來給所有需要它的地方共用。

這件事非常重要，因為它就是「Scoped」的實作方式：

```python
@app.get("/report")
def report(
    db: DbSession,                 # get_db
    user: CurrentUser,             # 內部也用了 get_db
):
    ...   # 兩處拿到的是同一個 session
```

沒有這個快取，一個 request 會開出好幾個資料庫連線，而且它們在不同的交易裡——資料一致性直接崩掉。

快取的鍵是**依賴物件本身**。所以 `Depends(get_db)` 出現幾次都是同一個；但 `Depends(RequireRole("admin"))` 和 `Depends(RequireRole("editor"))` 是兩個不同的實例，各自呼叫。

要關掉快取（每次都重新呼叫，等同 .NET 的 Transient）：

```python
value: Annotated[str, Depends(new_uuid, use_cache=False)]
```

實務上很少用。真的需要「每次都不同」的東西，多半直接在函式裡呼叫就好。

---

## 四、`yield`：帶收尾的依賴

需要「用完要關掉」的資源時，用 `yield` 取代 `return`：

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

執行順序是：

1. 請求進來，執行到 `yield`，把 `db` 交給 endpoint
2. endpoint（以及所有依賴它的東西）執行
3. endpoint 結束，回到 `yield` 之後，執行 `finally`
4. 回應送給客戶端

**第 3 步在第 4 步之前**——這就是開頭那個 bug 的成因。0.106 版之前順序是反過來的（先送回應再收尾），所以舊文章裡「在 background task 裡用 session」的寫法現在不成立了。

需要在背景任務裡存取資料庫，就在任務內自己開一個 session：

```python
def save_event(payload: Event):
    with SessionLocal() as db:          # 自己開、自己關
        db.add(Event(**payload.model_dump()))
        db.commit()

@app.post("/webhook", status_code=202)
def webhook(payload: Event, background: BackgroundTasks):
    background.add_task(save_event, payload)
    return {"accepted": True}
```

（更進一步的建議：背景任務進程內執行，程序被砍就消失。要保證不掉的工作應該進佇列，這件事 [[16-background-work]] 談。）

### `try/finally` 不能省

```python
# ✗ 不好：endpoint 丟例外時 session 不會被關，連線池會慢慢耗盡
def get_db():
    db = SessionLocal()
    yield db
    db.close()

# ✓ 好
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

例外會沿著依賴鏈往上傳播，所以 `yield` 那一行有機會拋出例外。沒有 `finally` 就漏了。

### 在依賴裡處理交易

`yield` 依賴也可以攔截例外，這讓「交易邊界」可以統一管理：

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()          # 沒有例外才提交
    except Exception:
        db.rollback()
        raise                # 一定要重新拋出，否則例外被吃掉
    finally:
        db.close()
```

這個寫法的取捨在第 05 章討論——它很方便，但也讓交易邊界變成隱性的，一支 endpoint 想要兩個獨立交易時會綁手綁腳。

---

## 五、三個層級掛依賴

有些依賴只是要「執行檢查」，回傳值用不到。這時用 `dependencies=[...]` 參數，不佔用函式簽章：

```python
# 單一 endpoint
@app.delete("/items/{item_id}", dependencies=[Depends(require_admin)])
def delete_item(item_id: int): ...

# 整個 router
router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])

# 整個 app
app = FastAPI(dependencies=[Depends(verify_api_key)])
```

這對應 .NET 的三個層級：`[Authorize]` 掛在 action、掛在 controller、或設 `FallbackPolicy`。掛在 router 或 app 上的好處和那邊一樣——**漏寫不再是漏洞**。新增一支 endpoint 忘了加驗證，如果保護是掛在 router 上的，它自動就受保護。

執行順序是由外而內：app → router → path operation → 函式簽章裡的依賴。

---

## 六、生命週期對照

.NET 的三種生命週期在 FastAPI 各有對應做法，但**沒有一個是靠設定切換的**，都是靠寫法：

| .NET | FastAPI 做法 | 說明 |
| --- | --- | --- |
| Transient | `Depends(f, use_cache=False)` | 每次注入重新呼叫 |
| Scoped | 一般的 `Depends(f)` | 依賴快取讓它一 request 一份 |
| Singleton | `@lru_cache` 的工廠 / lifespan + `app.state` | 程序層級共用 |

### Singleton 寫法一：`@lru_cache`

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()          # 讀環境變數，只做一次

Config = Annotated[Settings, Depends(get_settings)]
```

`lru_cache` 讓這個函式無論被呼叫幾次都回傳同一個物件。這是官方文件的建議做法，適合設定這種**建立成本低但不必重複做**的東西。

### Singleton 寫法二：`lifespan`

需要在啟動時建立、關閉時釋放的東西（連線池、HTTP client、機器學習模型），用 `lifespan`：

```python
from contextlib import asynccontextmanager
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=10.0)   # 啟動
    yield
    await app.state.http.aclose()                       # 關閉

app = FastAPI(lifespan=lifespan)

def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http

HttpClient = Annotated[httpx.AsyncClient, Depends(get_http)]
```

`lifespan` 是 ASGI 規格的一部分，對應 .NET 的 `IHostApplicationLifetime` 加 `IHostedService`。舊寫法 `@app.on_event("startup")` 已棄用，看到就換掉。

**HTTP client 一定要走這條路。** 每個 request 建一個 `httpx.AsyncClient` 會讓連線無法重用、port 耗盡，症狀和 .NET 那邊 `new HttpClient()` 造成的 socket exhaustion 完全一樣。

### 一張決策表

| 這個東西… | 用什麼 |
| --- | --- |
| 設定值 | `@lru_cache` 工廠 |
| 資料庫 session | `yield` dependency |
| 連線池 / HTTP client / 模型 | `lifespan` + `app.state` |
| 目前登入者 | 一般 `Depends`（會被快取） |
| 每次都要新的隨機值 | 直接在函式裡產生，不要用 DI |

---

## 七、`dependency_overrides`：測試的關鍵

FastAPI 沒有介面到實作的註冊表，那測試時要怎麼把真資料庫換成測試資料庫？答案是覆寫：

```python
# tests/conftest.py
from app.main import app
from app.api.deps import get_db

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

之後所有用到 `Depends(get_db)` 的地方——不管在依賴鏈的哪一層——都會拿到測試版本。要還原就 `app.dependency_overrides.clear()`。

這個機制在架構上有個重要含意：**你的依賴函式就是你的接縫（seam）**。把外部世界（資料庫、第三方 API、時鐘）都包在依賴函式後面，測試時才有地方替換。反過來說，在 endpoint 裡直接 `SessionLocal()` 或 `httpx.get(...)`，那段程式碼就沒辦法測。

完整的測試寫法在第 10 章。

---

## 八、`def` 還是 `async def`？

依賴函式和 endpoint 一樣有這個選擇，規則也一樣：

- `async def` 的依賴在 event loop 上執行
- `def` 的依賴會被丟到 threadpool 執行

所以 `def get_db()` 用同步的 SQLAlchemy 是**安全**的——它在 threadpool 裡阻塞，不會擋住 event loop。反過來，在 `async def` 依賴裡呼叫同步的阻塞 I/O 才是災難。

完整的推導在下一章。現在只要記住一條紀律：**函式裡有阻塞呼叫，就用 `def`；全部是 `await` 的非同步呼叫，才用 `async def`。**

---

## 九、常見誤解

**「`Depends` 就是 .NET 的建構式注入。」**
用途類似，機制差很多。沒有註冊表、沒有介面對應、解析發生在每個 request 而不是啟動時。最實際的差別是：依賴缺失或寫錯，FastAPI 要等到那條路由被呼叫才會報錯，啟動時完全看不出來。

**「同一個 request 裡多處注入 `get_db`，會開多個 session。」**
不會。依賴結果在單一 request 內有快取，同一個依賴只呼叫一次。這正是它能扮演 Scoped 的原因。要關掉快取才會每次重新呼叫（`use_cache=False`）。

**「`yield` 後面的程式碼在回應送出後才跑。」**
0.106 之前是，之後不是——收尾在回應送出**之前**執行。所以背景任務不能使用 `yield` 出來的資源，必須自己開。這是版本行為變更，舊文章都是錯的。

**「依賴只能回傳值。」**
它也可以什麼都不回傳，純粹做檢查（驗證 API key、檢查角色）並在失敗時 `raise HTTPException`。這種依賴用 `dependencies=[Depends(f)]` 掛在 endpoint、router 或 app 上，不佔用函式簽章。

**「設定物件要在每個 request 讀一次環境變數。」**
不必。用 `@lru_cache` 包住工廠函式，整個程序共用一份。每次重讀不但慢，而且會讓「設定在執行期改變」變成可能，反而更難除錯。

---

## 十、同事會來問你的問題

**「FastAPI 的 DI 和 .NET 的 DI 差在哪？」**
三點：沒有集中註冊表（`Depends` 直接指向函式）、沒有介面到實作的對應（要替換得用 `dependency_overrides`）、解析在每個 request 現場進行而非啟動時建圖（所以漏掉的依賴不會在啟動時被抓到）。好處是依賴關係全寫在簽章上，不需要翻註冊檔。

**「Scoped 在 FastAPI 怎麼做？」**
就是一般的 `Depends`。同一個 request 內同一個依賴只會被呼叫一次，結果共用，這就是 Scoped 的語意。需要收尾（關 session）就用 `yield` 版本。

**「Singleton 怎麼做？」**
兩種。建立成本低的（設定）用 `@lru_cache` 包工廠函式；需要啟動建立、關閉釋放的（連線池、HTTP client、模型）用 `lifespan` 存進 `app.state`，再寫一個小依賴從 `request.app.state` 取出來。

**「為什麼我的背景任務說 session 已關閉？」**
因為 `yield` 依賴的收尾在回應送出前就跑完了，背景任務啟動時 session 早就 close。背景任務要自己開 session（`with SessionLocal() as db:`）。順帶一提，`BackgroundTasks` 是程序內執行的，程序被砍任務就沒了，重要工作要進佇列。

**「一個依賴要怎麼同時服務兩種角色檢查？」**
把它寫成有 `__init__` 和 `__call__` 的類別，用 `Depends(RequireRole("admin"))` 建出參數化的實例。注意每個不同參數的實例是不同的快取鍵，所以它們各自執行。

**「測試時怎麼換掉資料庫？」**
`app.dependency_overrides[get_db] = 測試版本`，整條依賴鏈上所有用到它的地方都會被換掉，結束後 `clear()`。這也是為什麼所有外部資源都該包在依賴函式後面——那是你唯一的替換接縫。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[02-pydantic-and-validation]] — 上一章：驗證與 model 分層
- [[04-async-and-concurrency]] — 下一章：`def` 與 `async def` 的完整推導
- [[05-database-sqlalchemy]] — session 生命週期與交易邊界
- [[10-testing]] — `dependency_overrides` 的完整用法
- [[02-dependency-injection]] — ASP.NET Core 的對應章節（含 captive dependency）
