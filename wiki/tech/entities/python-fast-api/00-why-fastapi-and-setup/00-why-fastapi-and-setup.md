---
type: concept
domain: tech
tags: [python, fastapi, asgi, wsgi, uvicorn, type-hints, setup]
sources: []
created: 2026-08-15
updated: 2026-08-15
---

# 第 00 章：為什麼是 FastAPI — 從 ASGI 與型別提示講起

## 一段看起來沒什麼好講的程式碼

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

六行。跑起來之後你會發現：`/items/42` 回傳的 `item_id` 是數字 `42` 而不是字串 `"42"`；`/items/abc` 會回一個結構完整的 422 錯誤說明；`/items/42?q=hello` 的 `q` 自動填進去了；而且完全沒有寫任何文件，`http://127.0.0.1:8000/docs` 卻已經有一份可以直接點按測試的 API 說明。

從 ASP.NET Core 過來的人看到這裡，第一反應通常是「所以它幫我做了 model binding 和 Swagger」。這個類比是對的，但它會讓你錯過一個更重要的問題：**C# 的型別在編譯期就存在，執行期的 model binding 有型別資訊可用是天經地義。Python 的 `item_id: int` 在執行期預設是被完全忽略的一段註解——那 FastAPI 是怎麼拿到它的？**

這個問題的答案，決定了 FastAPI 的一切設計。這一章要回答它，順便把兩件事講清楚：Python 的 Web 生態為什麼會演進到需要 ASGI，以及一個 FastAPI 專案該怎麼從零建起來。

讀完之後，你應該能說清楚：ASGI 和 WSGI 差在哪、`app = FastAPI()` 這個物件到底是什麼、`@app.get(...)` 那一行執行的時候發生了什麼事、以及 `uvicorn app.main:app` 這串字裡每個部分的意思。

---

## 一、Python Web 的兩個世代：WSGI 與 ASGI

### WSGI：一個 request 佔住一個 worker

2003 年 Python 社群定下了 WSGI（Web Server Gateway Interface），它的規格簡單到可以一句話講完：**一個 Web 應用就是一個可呼叫物件，接收環境字典和一個回呼，回傳 response body。**

```python
def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello"]
```

Flask、Django（3.0 之前）、Bottle 全都建立在這個介面上。它的價值在於解耦：應用不必知道自己跑在 Apache 還是 Gunicorn 上。

但這個簽章有個無法補救的性質——**它是同步的**。函式回傳的那一刻，這個 request 就結束了；在它回傳之前，執行它的那條執行緒完全被佔住。這代表一件事：

> 一個 WSGI worker 同一時間只能處理一個請求。

如果請求的內容是「查資料庫等 200 毫秒」，那這 200 毫秒裡這條 worker 什麼都不做，只是等著。要提高吞吐量只能開更多 worker（更多程序、更多記憶體），或改用 gevent 這類 monkey-patch 方案硬把同步 I/O 換成協程——後者長年是 Python 社群一個「能動但沒人想解釋為什麼能動」的地帶。

更麻煩的是 WebSocket、Server-Sent Events 這種長連線。WSGI 的模型裡連線只有「進來、處理、出去」三個狀態，沒有地方擺一個「持續開著」的連線。

### ASGI：把非同步和長連線寫進規格

Python 3.4 之後有了 `asyncio`，3.5 有了 `async`/`await` 語法，語言層級具備了非同步能力，但 WSGI 用不到它。於是 ASGI（Asynchronous Server Gateway Interface）出現，介面長這樣：

```python
async def app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": [...]})
    await send({"type": "http.response.body", "body": b"Hello"})
```

三個關鍵差異：

| | WSGI | ASGI |
| --- | --- | --- |
| 函式性質 | 同步 `def` | 非同步 `async def` |
| 回應方式 | 回傳 body | 用 `send` 送出多個訊息（可串流） |
| 連線類型 | 只有 HTTP request/response | HTTP、WebSocket、lifespan 事件 |

`scope` 描述這次連線是什麼（`{"type": "http", ...}` 或 `{"type": "websocket", ...}`），`receive` 用來收訊息，`send` 用來送訊息。因為送出是多次的、非同步的，串流回應和長連線就自然成立了。

而 `async def` 帶來的效果是：當一個 request 停在 `await`（等資料庫、等外部 API）的時候，**執行緒可以回去處理別的 request**。這和 ASP.NET Core 裡 `await` 把執行緒還給 ThreadPool 是同一個概念，差別在於 Python 這邊通常只有**一條**執行緒（一個 event loop）在轉。

這個「通常只有一條」是後面所有並發問題的根源，第 04 章整章都在講它。

### 三個框架的定位

| 框架 | 介面 | 定位 | 什麼時候選它 |
| --- | --- | --- | --- |
| Django | WSGI（4.x 起也支援 ASGI） | 全家桶：ORM、admin、樣板、驗證一應俱全 | 需要後台管理介面、以伺服器渲染頁面為主 |
| Flask | WSGI | 微框架：只給路由和 request 物件，其他自己選 | 小工具、既有專案、團隊已熟悉 |
| FastAPI | ASGI | 專攻 API：型別驅動的驗證與文件 | 前後端分離、給前端或其他服務用的 JSON API |

FastAPI 本身不是從零寫的。它站在兩個套件上：**Starlette** 負責 ASGI、路由、middleware、測試客戶端這些 Web 層的事；**Pydantic** 負責資料驗證與序列化。FastAPI 的貢獻是把兩者黏起來，並發明了那套「從函式簽章推導一切」的機制。

知道這個分工有實際用處：當你查到的錯誤訊息裡出現 `starlette.` 或 `pydantic_core.`，你就知道問題發生在哪一層，該去哪個專案的文件找答案。

---

## 二、FastAPI 的核心賭注：把型別提示當成執行期契約

回到開頭那個問題。這行程式碼：

```python
def read_item(item_id: int, q: str | None = None):
```

在**純 Python** 的世界裡，`: int` 對執行期毫無影響。你傳字串進去，Python 照收不誤，不會有任何錯誤。型別提示（PEP 484，Python 3.5 引入）的設計初衷是給 mypy、Pyright 這類靜態檢查工具和 IDE 用的，直譯器本身不理它。

但「不理它」不等於「丟掉它」。這些註解被存在函式物件的 `__annotations__` 屬性裡：

```python
>>> read_item.__annotations__
{'item_id': <class 'int'>, 'q': str | None}
```

任何人都可以在執行期把它讀出來。FastAPI 做的就是這件事——用 `inspect.signature()` 和 `typing.get_type_hints()` 讀出每個參數的名稱、型別、有沒有預設值，然後**根據這些資訊決定行為**。

這就是 FastAPI 的核心賭注：**同一份型別宣告，一次寫，四個地方用。**

| 用途 | FastAPI 從型別得到什麼 |
| --- | --- |
| 參數來源判斷 | `item_id` 出現在路徑模板裡 → 從 path 取；`q` 沒有 → 從 query 取 |
| 資料驗證 | `int` → 收到 `"abc"` 就回 422；`str \| None` 且有預設值 → 選填 |
| 型別轉換 | URL 裡的 `"42"` 轉成 Python 的 `42` |
| API 文件 | 產出 OpenAPI schema，`/docs` 直接渲染 |

在 ASP.NET Core 裡，這四件事分別由 model binder、DataAnnotations（或 FluentValidation）、型別轉換器、Swashbuckle 的反射掃描負責，是四套獨立機制，寫法各不相同。FastAPI 把它們收攏到同一個來源。

代價是**規則變成隱性的**。C# 的 `[FromQuery] string q` 一看就知道從哪來；FastAPI 的 `q: str | None = None` 從哪來取決於一組你必須背下來的推導規則。這是入門期最大的認知落差，也是 422 錯誤最常見的來源，所以第 01 章會用一整節把規則攤開。

**好的做法**是讓型別承載意義，讓框架自動處理：

```python
@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate) -> OrderOut:
    ...
```

**不好的做法**是把 Python 當成沒有型別的語言，退回手動解析：

```python
@app.post("/orders")
async def create_order(request: Request):
    data = await request.json()
    if "amount" not in data:
        return {"error": "amount required"}   # 手刻驗證、非標準錯誤格式、文件是空的
    ...
```

第二種寫法能動，但你放棄了 FastAPI 的全部價值——沒有驗證、沒有文件、沒有型別安全，還多寫了幾行。看到既有專案裡出現這種寫法，通常是從 Flask 搬過來沒改乾淨。

---

## 三、環境建置

### Python 版本

用 **3.12**（或 3.11）。理由不是新功能，是型別語法：`str | None` 這種寫法在 3.10 才成為執行期合法（PEP 604），而它會出現在你寫的每一支函式簽章上。3.9 以下要退回 `Optional[str]`，能動但囉唆。

```powershell
python --version
```

### 虛擬環境：為什麼一定要

.NET 的相依性天生是專案層級的（`.csproj` + `obj/`），Python 不是——`pip install` 預設裝到全域。兩個專案要不同版本的同一個套件就會互相踩。虛擬環境是每個專案一份獨立的套件目錄。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

啟用後提示字元前面會出現 `(.venv)`。如果 PowerShell 擋下腳本執行（`因為這個系統上已停用指令碼執行`），對當前使用者放行一次即可：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

`.venv/` 要進 `.gitignore`，它是可重建的產物，不是原始碼。

### 安裝

```powershell
pip install "fastapi[standard]"
```

`[standard]` 是 extras 語法，會一併帶進 uvicorn、`httpx`、表單與檔案上傳所需的套件等常用相依。想精簡到最小就裝 `fastapi` 加 `uvicorn` 兩個。

裝完把清單釘住：

```powershell
pip freeze > requirements.txt
```

`requirements.txt` 對應 .NET 的 `PackageReference`，差別是它記錄的是**已解析的完整版本清單**，比較接近 `packages.lock.json`。實務上團隊常用 `uv`（新一代套件管理工具，速度快一個數量級，且有 `uv.lock`）取代 pip，指令是 `uv add fastapi` / `uv run uvicorn ...`；本教材維持 pip 寫法，因為它到處都能用。

### 專案骨架

```text
myapi/
├── .venv/
├── .gitignore
├── requirements.txt
└── app/
    ├── __init__.py
    └── main.py
```

`__init__.py` 是空檔案，它的作用是讓 `app/` 成為一個 package，這樣 `app.main` 這種匯入路徑才成立。少了它，`uvicorn app.main:app` 在某些情況下會找不到模組。

---

## 四、第一支程式，逐行拆

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="My API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}
```

### `app = FastAPI()` 建了什麼

`app` 是一個 **ASGI application**——白話講，是一個「可以被呼叫、簽章符合 `async def app(scope, receive, send)` 的物件」。它繼承自 Starlette 的 `Starlette` 類別，內部主要持有：一份 router（路由表）、一份 middleware 堆疊、一份例外處理器對照表、以及產生 OpenAPI 文件所需的中繼資料。

對照 ASP.NET Core：它同時扮演 `WebApplicationBuilder`（累積設定）和 `WebApplication`（最終被 server 呼叫）兩個角色。差別在於 .NET 有明確的 `builder.Build()` 這一刻把設定凍結，FastAPI 沒有——路由和 middleware 是在模組被 import 的過程中逐步累積上去的。

這帶來一個實務後果：**middleware 必須在 app 啟動前加完**。在應用跑起來之後才呼叫 `add_middleware()`，行為是未定義的（新版會直接報錯）。

### `@app.get("/health")` 執行了什麼

這是這一章最容易被誤解的一行。它**不是**在描述函式，而是在模組被載入的當下，實際執行了一次呼叫：

```python
health = app.get("/health")(health)
```

`app.get("/health")` 回傳一個 decorator，這個 decorator 收到 `health` 函式後做三件事：讀出它的簽章與型別註解、把「GET /health → 這個函式」註冊進 router、然後把原函式原封不動回傳。

所以 decorator 的效果是**註冊**，不是包裝。這解釋了兩個新手常見的疑惑：一是為什麼被裝飾的函式仍然可以在測試裡直接呼叫（因為它沒被改掉）；二是為什麼路由的**宣告順序會影響匹配結果**（因為它們是按執行順序被 append 進同一個 list 的）——這件事在第 01 章會咬人。

### 回傳值怎麼變成 JSON

函式回傳了一個 dict，客戶端收到的是 `application/json`。中間發生的是 `jsonable_encoder`：FastAPI 把回傳值遞迴轉換成 JSON 可表示的基本型別（Pydantic model 會呼叫 `model_dump()`、`datetime` 轉 ISO 字串、`Decimal` 轉數字），再交給 `JSONResponse` 序列化。

你也可以直接回傳 `Response` 物件跳過這整套（要回 CSV、檔案、自訂 header 時會用到），代價是失去 `response_model` 的過濾與文件產生。

### 跑起來

```powershell
uvicorn app.main:app --reload
```

這串字每個部分都有意義：

| 片段 | 意思 |
| --- | --- |
| `uvicorn` | ASGI server，地位等同 .NET 的 Kestrel |
| `app.main` | 模組路徑，對應 `app/main.py` |
| `:app` | 模組裡那個變數的名字，即 `app = FastAPI()` |
| `--reload` | 監看檔案變動自動重啟 |

`--reload` **只能用於開發**。它會另外開一個監看程序，記憶體與 CPU 成本明顯，而且重啟時所有記憶體狀態（連線池、快取）全部重來。生產環境的啟動指令見第 11 章。

框架與 server 分離這一點值得停一下。ASP.NET Core 也是這個結構（Kestrel 是 `IServer` 的一個實作），所以你可以理解成同一種設計。實務上你可能會遇到 uvicorn、hypercorn、granian 等不同 ASGI server，換掉不需要改應用程式碼。

### `/docs` 從哪來

`app` 建立時預設掛了三條路由：`/openapi.json`（依你的函式簽章即時產生的 OpenAPI 規格）、`/docs`（Swagger UI）、`/redoc`（ReDoc）。

它們是預設開啟的。**上生產前要決定是否關閉**：

```python
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
```

內部服務通常留著（對前端同事很有用），對外服務多半關掉或加上驗證，因為 OpenAPI 等於把所有 endpoint 和參數結構公開。這是 .NET 那邊 `if (app.Environment.IsDevelopment()) app.UseSwagger();` 的同一個判斷。

---

## 五、把它變成一支像樣的 API

把前面所有東西合起來，一支帶驗證、狀態碼與文件的 endpoint 長這樣：

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="My API")

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)

class ItemOut(BaseModel):
    id: int
    name: str
    price: float

_items: dict[int, ItemOut] = {}
_next_id = 1

@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate):
    global _next_id
    item = ItemOut(id=_next_id, name=payload.name, price=payload.price)
    _items[item.id] = item
    _next_id += 1
    return item

@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int):
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")
    return item
```

這段程式碼裡有四個之後要展開的伏筆：

- `ItemCreate` 與 `ItemOut` 為什麼要分成兩個類別 → 第 02 章（安全邊界，等同 .NET 的 DTO 與 over-posting）
- 用 `raise` 而不是 `return` 來回錯誤 → 第 06 章（例外處理層次）
- `_items` 這個模組層級的 dict 一旦多開幾個 worker 就會分裂 → 第 11 章（無狀態與水平擴展）
- 這裡全部用 `def` 而不是 `async def`，是有意的 → 第 04 章

現在先讓它跑起來，開 `/docs` 點兩下，感受一下「型別寫對，其他自動發生」是什麼意思。

---

## 六、常見誤解

**「FastAPI 快，是因為它是 async。」**
不精確。它快的主因有兩個：Starlette 的 ASGI 實作本身輕量，以及 Pydantic v2 的驗證核心是 Rust 寫的（`pydantic-core`）。async 提升的是**高 I/O 等待場景下的並發能力**，不是單一請求的執行速度。一支純運算的 endpoint 改成 `async def` 不會變快，反而可能拖垮整個服務——原因見第 04 章。

**「加了型別提示，Python 就會做型別檢查。」**
不會。Python 直譯器永遠忽略型別提示。是 FastAPI 主動讀取註解並用 Pydantic 執行驗證，而且**只在它管轄的邊界上做**——path operation 的參數、`response_model`。你自己寫的一般函式標了 `x: int` 傳字串進去，照樣不會有任何錯誤。

**「`@app.get` 就像 C# 的 `[HttpGet]`。」**
效果相似，機制不同。C# 的 attribute 是中繼資料，由框架在啟動時掃描；Python 的 decorator 是**當場執行的程式碼**。所以在 Python 裡，路由註冊的時機取決於模組被 import 的時機與順序，這在拆分 router、循環匯入時會直接影響行為。

**「驗證失敗應該回 400。」**
FastAPI 回 **422 Unprocessable Entity**。這是刻意的：400 表示請求語法有問題，422 表示語法正確但語意不通過（欄位型別錯、缺必填）。ASP.NET Core 的 `[ApiController]` 預設回 400，所以前端如果同時對接兩種後端，要先講好。要改成 400 的做法見第 06 章。

---

## 七、同事會來問你的問題

**「Python 的型別提示執行期會被忽略，那 FastAPI 的驗證是怎麼生效的？」**
提示被存在函式的 `__annotations__` 裡。FastAPI 在註冊路由（也就是 decorator 執行）的當下用 `inspect` 讀出簽章與型別，替每個參數建出一份 Pydantic 驗證器；請求進來時是那些驗證器在跑，不是直譯器。所以驗證只發生在 FastAPI 管轄的邊界上。

**「WSGI 和 ASGI 差在哪，為什麼 FastAPI 一定要 ASGI？」**
WSGI 的介面是同步的，回傳即結束，一條 worker 同時只能服務一個請求，也放不下 WebSocket 這種長連線。ASGI 把介面改成 `async def app(scope, receive, send)`，回應可以分多次送出，連線類型寫進 `scope`。FastAPI 要支援 `async def` 的 endpoint 和串流回應，只能建立在 ASGI 上。

**「`uvicorn app.main:app` 這串是什麼意思？」**
`app.main` 是模組路徑（`app/main.py`），冒號後面的 `app` 是那個模組裡的變數名，也就是 `app = FastAPI()` 建出來的 ASGI application。uvicorn 匯入該模組、取出這個物件、開始監聽 port 並把請求轉成 ASGI 呼叫。這和 Kestrel 拿到 `WebApplication` 之後做的事是同一件。

**「decorator 和 C# 的 attribute 一樣嗎？」**
用途重疊，機制不同。attribute 是編譯進組件的中繼資料，框架靠反射掃描；decorator 是一個函式，在模組載入時**立刻執行**，`@app.get("/x")` 的實際效果是當場把路由 append 進 router 的清單。因此路由的宣告順序就是匹配的嘗試順序，而 C# 那邊有一套獨立的優先序演算法。

**「`/docs` 可以直接上生產嗎？」**
技術上可以，但等於公開全部 endpoint、參數結構與範例值。內部服務通常保留，對外服務建議關閉（`docs_url=None, openapi_url=None`）或放在需驗證的路徑後面。決策點和 .NET 那邊要不要 `UseSwagger()` 完全一樣。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[01-routing-and-path-operations]] — 下一章：參數來源的完整規則
- [[04-async-and-concurrency]] — `def` 與 `async def` 的抉擇
- [[dotnet-web-api]] — 對照組
- [[00-hosting-and-startup]] — ASP.NET Core 的對應章節（Host 與啟動）
