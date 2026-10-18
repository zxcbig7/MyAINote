---
type: entity
domain: tech
tags: [python, fastapi, asgi, pydantic, web-api, backend, async, dependency-injection, curriculum]
sources: []
created: 2026-08-15
updated: 2026-08-15
---

# FastAPI

FastAPI 是 Python 的 ASGI Web 框架，用型別提示（type hints）同時完成參數解析、資料驗證、序列化與 API 文件產生。

這一頁有兩個身分。上半部是**教材總目錄**——一套寫給「已經會 ASP.NET Core、第一次碰 Python 後端」的讀者的教材，回答「為什麼」；下半部是**速查**，回答「怎麼寫」。趕時間查語法就跳到速查區，想搞懂機制就從第 00 章開始。

---

## 教材：從會抄範例到說得出機制

FastAPI 的入門體驗好到有點危險。三十行就跑出一個帶互動式文件的 API，型別寫上去驗證就自己生效，看起來沒什麼需要理解的。於是很多人是在下面這些時刻才第一次意識到自己不懂它：

- 某支 endpoint 一被呼叫，**整個服務**其他請求全部卡住幾秒
- 明明參數帶了，卻一直回 422，訊息說某個欄位是 `body` 但你以為它是 query
- `/users/me` 永遠回傳「找不到使用者 me」
- 資料庫 session 偶爾在 background task 裡爆 `Session is closed`
- 本機四個 worker 跑得好好的，上 K8s 之後計數器歸零、排程重複執行

這五個症狀分別對應五章的內容，而它們共同的根因只有一個：**FastAPI 把很多決策藏在型別註解和函式簽章裡，你沒讀懂那些規則，就等於在猜。**

### 誰該讀

預設讀者寫過 Web API（哪個語言都行，教材會大量對照 ASP.NET Core），Python 語法看得懂（`def`、class、decorator 大致知道在幹嘛），但沒真正搞清楚 `async` 在 Python 裡代表什麼、也沒建立過生產級的 Python 服務。

讀完之後，應該能夠獨立判斷一段 endpoint 會不會拖垮 event loop、審查別人的 PR 並指出 dependency 生命週期用錯的地方、從「偶發 500」推理到 session 在錯的時機被關閉，以及在被同事追問「為什麼這裡要 `async def` 那裡不用」的時候答得出機制。

### 進度總覽

**全書 12 章 + 3 附錄 + 1 實戰完成。** 每章以一個真實會出事的場景開篇，收尾固定「常見誤解」與「同事會來問你的問題」兩段自我檢測。

| 篇 | 章節 | 核心問題 | 狀態 |
| --- | --- | --- | --- |
| **起步篇** | [[00-why-fastapi-and-setup]] | ASGI 解決了什麼？型別提示為什麼能在執行期生效？ | ✅ |
| | [[01-routing-and-path-operations]] | 一個參數該去 path、query 還是 body，是誰決定的？ | ✅ |
| | [[02-pydantic-and-validation]] | 422 是誰產生的？`response_model` 到底擋掉什麼？ | ✅ |
| | [[03-dependency-injection]] | `Depends` 怎麼對應 .NET 的 Scoped？`yield` 在收拾什麼？ | ✅ |
| | [[04-async-and-concurrency]] | `def` 與 `async def` 差在哪？誰會把 event loop 堵死？ | ✅ |
| **實務篇** | [[05-database-sqlalchemy]] | session 的邊界該畫在哪？async ORM 值不值得？ | ✅ |
| | [[06-error-handling]] | 例外該在哪一層接？什麼錯回什麼 status code？ | ✅ |
| | [[07-auth-and-jwt]] | `OAuth2PasswordBearer` 做了什麼？授權寫在哪一層？ | ✅ |
| | [[08-middleware-and-cross-cutting]] | ASGI middleware 與 dependency 的分工、CORS、request id | ✅ |
| | [[09-configuration]] | `BaseSettings`、環境變數、K8s ConfigMap/Secret 注入 | ✅ |
| | [[10-testing]] | `TestClient` 與 `dependency_overrides`、async 測試 | ✅ |
| | [[11-deployment]] | 容器化、worker 數量、lifespan 與 graceful shutdown | ✅ |
| **附錄** | [[12-cheatsheet]] | 速查：骨架、參數規則表、常見錯誤對照 | ✅ |
| | [[13-aspnet-mapping]] | ASP.NET Core ↔ FastAPI 完整對照 | ✅ |
| | [[14-self-assessment]] | 58 題自我檢測，蓋住答案自己講一遍才算會 | ✅ |
| **實戰** | [[15-practice-deploy-to-k8s]] | 應用換成 FastAPI 之後，交付鏈上哪十件事要改？ | ✅ |
| **補充篇** | [[16-background-work]] | 三個副本，排程跑了三次——背景工作該放哪？ | ✅ |
| | [[17-resilience]] | 下游變慢時怎麼不被拖死？逾時、重試、斷路器、快取、限流 | ✅ |

### 怎麼用

**第一遍求通不求精。** 卡住的段落標記起來繼續往下——例如 `Depends` 的快取行為要先知道一個 request 內依賴圖怎麼解析才理解得了。

**第二遍動手拆。** 回到標記處，開一個空專案把每個機制實際跑一次。特別是「反例」那些段落，親手把它弄壞一次比讀十遍有效。

**第三遍反過來考自己。** 每章末尾的「同事會來問你的問題」蓋住答案先自己講一遍，講得出來才算會。

教材以 **Python 3.12 + FastAPI 0.115+ + Pydantic v2** 為基準撰寫。Pydantic v1 與 v2 的 API 差異極大，網路上大量舊文章仍是 v1 寫法，教材會在容易混淆處明確標注。

### 這套教材的取向

它假設的部署環境是 **K8s + Oracle/PostgreSQL + JWT/Google OAuth + 前後端分離**，和 [[dotnet-web-api]] 那套教材同一個場景。所以有兩件事會反覆出現：

一是**與 ASP.NET Core 的對照**。既有的心智模型是資產不是包袱——`Depends` 對應建構式注入、`yield` dependency 對應 Scoped、`BaseSettings` 對應 `IOptions<T>`。但對照也會誤導，教材會明講哪些地方「看起來一樣，其實不一樣」（最大的一個是 DI 的解析時機）。

二是**單執行緒 event loop 的後果**。ASP.NET Core 的 ThreadPool 會替你吸收掉大部分同步阻塞的錯誤；Python 的 event loop 不會。同一個寫法在 .NET 只是慢，在 FastAPI 是整台服務停止回應。這件事會從第 04 章一路影響到部署章的 worker 數量計算。

---

## 速查

### 最小可跑的 app

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

```powershell
uvicorn app.main:app --reload
```

啟動後開 `http://127.0.0.1:8000/docs` 就有互動式文件，不需要任何額外套件。

### ASP.NET Core 心智映射

| ASP.NET Core | FastAPI | 備註 |
| --- | --- | --- |
| Kestrel | Uvicorn | ASGI server，與框架分離 |
| `WebApplication` / `Program.cs` | `app = FastAPI()` | |
| Controller | `APIRouter` | 分模組用，不是必要的 |
| `[HttpGet("/x")]` | `@app.get("/x")` | |
| DTO + DataAnnotations | Pydantic `BaseModel` | 驗證規則寫在型別上 |
| ModelState 失敗回 400 | `RequestValidationError` 回 **422** | status code 不同 |
| 建構式注入 | `Depends()` | 解析時機不同，見 [[03-dependency-injection]] |
| Scoped | `yield` dependency | |
| Middleware | `@app.middleware("http")` | 兩者都是洋蔥 |
| Filter | dependency（多半用它取代） | |
| `IOptions<T>` | `BaseSettings`（pydantic-settings） | |
| Swashbuckle / Swagger | 內建 `/docs`、`/openapi.json` | 不用裝套件 |
| EF Core | SQLAlchemy | |
| EF Migrations | Alembic | |
| `IHostedService` / 啟動關閉事件 | `lifespan` | |

### 參數來源判斷規則

宣告一個參數之後，FastAPI 依這個順序決定它從哪裡來：

| 條件 | 來源 |
| --- | --- |
| 名稱出現在路徑模板中（`/items/{item_id}`） | path |
| 型別是 Pydantic model | body |
| 其餘的單純型別（`int`、`str`、`bool`…） | query |
| 明確標注 `Query()` / `Path()` / `Body()` / `Header()` / `Cookie()` / `Form()` | 依標注 |

有預設值即為選填，沒有預設值就是必填。完整推導見 [[01-routing-and-path-operations]]。

### 常用回應寫法

```python
from fastapi import HTTPException, status

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    user = repo.find(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return user

@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate):
    return repo.create(payload)
```

### Pydantic v2 常用片段

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: str
    age: int | None = Field(default=None, ge=0, le=150)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 可直接從 ORM 物件轉換
    id: int
    name: str
    email: str
```

| v1 寫法 | v2 寫法 |
| --- | --- |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes=True` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `parse_obj()` | `model_validate()` |
| `@validator` | `@field_validator` |

### Depends 骨架

```python
from typing import Annotated
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]

@app.get("/users")
def list_users(db: DbSession):
    return db.query(User).all()
```

`Annotated` 是目前建議的寫法，好處是可以把 `DbSession` 這種別名重複使用。詳見 [[03-dependency-injection]]。

### CORS 設定（開發環境）

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_credentials=True` 時 `allow_origins` **不能**用 `["*"]`，這是瀏覽器規範不是框架限制。

### 專案結構建議

```text
app/
├── main.py            # FastAPI() 實例、middleware、router 掛載
├── api/
│   ├── deps.py        # 共用 dependency
│   └── routers/
│       ├── users.py
│       └── orders.py
├── core/
│   ├── config.py      # BaseSettings
│   └── security.py    # JWT 簽發驗證
├── models/            # SQLAlchemy ORM
├── schemas/           # Pydantic model
└── services/          # 業務邏輯
tests/
```

`models`（資料庫）與 `schemas`（API 契約）分開，理由和 .NET 那邊 Entity 與 DTO 要分開一樣：見 [[02-pydantic-and-validation]]。

### 常用指令（PowerShell）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "fastapi[standard]" uvicorn

uvicorn app.main:app --reload                  # 開發
uvicorn app.main:app --host 0.0.0.0 --port 8000  # 容器內
pytest -q                                       # 測試
```

## 連結

- [[python]] — 語言本身
- [[dotnet-web-api]] — 對照組，同一套場景的 .NET 版教材
- [[docker]] — 容器化部署
- [[kubernetes]] — 部署目標環境
- [[react]] — 前端框架，需設定 CORS 對接
- [[oracle]] — 資料庫，SQLAlchemy provider 對接
