---
type: concept
domain: tech
tags: [python, fastapi, routing, path-operation, query-params, apirouter, annotated]
sources: []
created: 2026-08-15
updated: 2026-08-15
---

# 第 01 章：路由與 Path Operation — 一個參數該從哪裡來，是誰決定的

## 一個永遠找不到的使用者

專案上線兩週後，前端回報：呼叫 `/users/me` 拿目前登入者的資料，後端回 `404 user not found`。但資料庫裡明明有那個人。

程式碼看起來完全正常：

```python
@app.get("/users/{user_id}")
def get_user(user_id: str):
    return repo.find(user_id)

@app.get("/users/me")
def get_current_user():
    return repo.find(current_user_id())
```

問題在於**這兩行的順序**。`/users/me` 這個請求進來時，FastAPI 從路由清單的頭開始比對，第一條 `/users/{user_id}` 就匹配上了——`user_id` 被填成字串 `"me"`，然後拿去查資料庫，查不到，回 404。第二條路由永遠不會被執行。

在 ASP.NET Core 裡這段程式碼是正常的：它的 endpoint routing 有一套優先序演算法，字面片段（literal segment）優先於參數片段，`/users/me` 會贏。FastAPI 沒有這套演算法——**它就是一個 list，由上往下 `for` 迴圈找第一個匹配的**。

這一章要把路由這件事講到不會再被咬。核心是一組規則：**一個參數會被從 path、query 還是 body 取出，完全由它的名字和型別決定**。這組規則是 FastAPI 入門期最大的認知落差，也是 422 錯誤最主要的來源。

讀完之後，你應該能看著任何一支函式簽章，準確說出每個參數從哪裡來、是必填還是選填、驗證失敗會回什麼。

---

## 一、Path operation 這個詞

FastAPI 的文件用「path operation」稱呼一個 endpoint，因為它由兩個東西定義：**path**（`/users/{user_id}`）與 **operation**（HTTP method，也就是 OpenAPI 規格裡的用詞）。一個 decorator 加一個函式，就是一個 path operation。

```python
@app.get("/users/{user_id}")      # ← path operation decorator
def get_user(user_id: int):       # ← path operation function
    ...
```

八個 method decorator 對應八個動詞：`get`、`post`、`put`、`patch`、`delete`、`options`、`head`、`trace`。實務上前五個就涵蓋九成。

有個小細節：宣告 `@app.get` 的路由會**自動同時接受 HEAD**（這是 Starlette 的行為，HEAD 的語意就是「GET 但不要 body」），所以健康檢查工具用 HEAD 打你的 `/health` 也會通。

`@app.api_route("/x", methods=["GET", "POST"])` 可以一次註冊多個 method，但除非有特殊理由，分開寫比較清楚——因為 OpenAPI 文件裡它們是不同的 operation，描述、回應模型都該分開。

---

## 二、參數來源的推導規則

這是本章的核心。FastAPI 拿到一支函式後，逐一檢視每個參數，依下列順序判斷來源：

| 判斷順序 | 條件 | 來源 |
| --- | --- | --- |
| 1 | 參數名出現在路徑模板中 | **path** |
| 2 | 有明確標注 `Query()` / `Path()` / `Body()` / `Header()` / `Cookie()` / `Form()` / `File()` | 依標注 |
| 3 | 型別是特殊物件（`Request`、`Response`、`BackgroundTasks`…） | 框架注入 |
| 4 | 值是 `Depends(...)` | 依賴注入（第 03 章） |
| 5 | 型別是 Pydantic `BaseModel` | **body** |
| 6 | 其餘（`int`、`str`、`float`、`bool`、`UUID`、`datetime`、`Enum`…） | **query** |

而必填/選填只看一件事：**有沒有預設值**。有預設值就是選填，沒有就是必填。跟型別標不標 `| None` 無關——這點特別容易搞混，下面會單獨講。

把規則套到一個例子上：

```python
@app.put("/items/{item_id}")
def update_item(
    item_id: int,                  # 名字在路徑裡 → path，必填
    payload: ItemUpdate,           # Pydantic model → body
    notify: bool = False,          # 單純型別 + 有預設值 → query，選填
    x_trace_id: str = Header(),    # 明確標注 → header，必填
):
    ...
```

對照 ASP.NET Core，那邊是 `[FromRoute]`、`[FromQuery]`、`[FromBody]` 明寫在參數上（`[ApiController]` 也會做推斷，但推斷規則比較單純：複雜型別→body，其餘→route/query）。FastAPI 的推斷更積極，好處是簽章乾淨，代價是你必須把上面那張表背起來。

### Path 參數

```python
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    ...
```

path 參數**永遠是必填**（路徑裡沒有它就匹配不到這條路由，根本進不來）。型別會做轉換與驗證：`/orders/abc` 會得到 422，訊息裡 `loc` 是 `["path", "order_id"]`。

加約束用 `Path()`：

```python
from typing import Annotated
from fastapi import Path

@app.get("/orders/{order_id}")
def get_order(order_id: Annotated[int, Path(ge=1)]):
    ...
```

有一個特殊轉換器 `:path`，讓參數吃下含斜線的剩餘路徑，等同 .NET 的 catch-all `{**slug}`：

```python
@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    ...   # /files/a/b/c.txt → file_path = "a/b/c.txt"
```

用它的時候務必檢查路徑穿越（`../`），否則就是一個目錄遍歷漏洞。

### Query 參數

沒出現在路徑裡的單純型別，一律是 query：

```python
@app.get("/items")
def list_items(skip: int = 0, limit: int = 20, keyword: str | None = None):
    ...
```

`/items?skip=0&limit=10&keyword=abc` 會正確填入。幾個要知道的細節：

**bool 的解析很寬鬆。** `?flag=true`、`?flag=True`、`?flag=1`、`?flag=on`、`?flag=yes` 都會變成 `True`。這是 Pydantic 的行為，不是 HTTP 規範。

**必填的 query 就是不給預設值。** 這在 `Query()` 上很容易寫錯：

```python
q: Annotated[str, Query()]                     # 必填
q: Annotated[str | None, Query()] = None       # 選填，預設 None
q: Annotated[str, Query()] = "default"         # 選填，預設 "default"
```

**只標 `| None` 不會讓它變選填。** `q: str | None` 沒有預設值時，它是「必填、但允許傳空值」，跟你想的不一樣。這是最常見的誤會之一。

**接收同名多值用 `list`：**

```python
@app.get("/items")
def list_items(tag: Annotated[list[str], Query()] = []):
    ...   # /items?tag=a&tag=b → tag = ["a", "b"]
```

這裡的 `Query()` 不能省略。少了它，`list[str]` 不是「單純型別」，會被規則第 5/6 條判成 body，於是 query 傳什麼都收不到——這是「參數明明帶了卻收不到」的典型成因。

（附帶一提，`= []` 這種可變預設值在一般 Python 是著名地雷，因為預設值物件在函式間共用。在 FastAPI 的參數宣告裡它會被當成 schema 的預設，實際不會被改動，所以是安全的；但養成習慣寫 `= None` 再處理仍然比較好。）

### Body 參數

型別是 Pydantic model，就是 body：

```python
class ItemCreate(BaseModel):
    name: str
    price: float

@app.post("/items")
def create_item(payload: ItemCreate):
    ...
```

送進來的 JSON 直接對應到 model 的欄位。驗證規則寫在 model 上（第 02 章）。

宣告**兩個以上** model 時，FastAPI 會自動把 body 包成巢狀結構，鍵名是參數名：

```python
@app.post("/orders")
def create_order(customer: Customer, items: ItemList):
    ...
```

```json
{
  "customer": { "...": "..." },
  "items": { "...": "..." }
}
```

這個行為很合理但常被忘記，前端照著單一物件送就會 422。

反過來，如果只有一個 model 但你希望它有一層外殼，或想在 body 裡塞一個單純型別，用 `Body(embed=True)`：

```python
@app.post("/items")
def create_item(payload: Annotated[ItemCreate, Body(embed=True)]):
    ...   # 期望 {"payload": {...}}

@app.post("/items/{item_id}/rename")
def rename(item_id: int, name: Annotated[str, Body(embed=True)]):
    ...   # 期望 {"name": "新名字"}
```

沒有 `embed=True` 的話，`name: str` 會被判成 query 參數（規則第 6 條），這又是一個「為什麼我的 body 沒收到」。

### Header 與 Cookie

```python
@app.get("/me")
def me(
    authorization: Annotated[str, Header()],
    user_agent: Annotated[str | None, Header()] = None,
    session_id: Annotated[str | None, Cookie()] = None,
):
    ...
```

`Header()` 預設會把參數名的底線轉成連字號（`user_agent` → `User-Agent`），因為 Python 的變數名不能有連字號。要關掉這個轉換用 `Header(convert_underscores=False)`。HTTP header 名稱本身不分大小寫。

實務上 `Authorization` 很少這樣手動讀——第 07 章會用 dependency 把它封裝掉。

### 框架物件

```python
from fastapi import Request, Response, BackgroundTasks

@app.post("/webhook")
async def webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()      # 原始 bytes，驗簽名時會用到
    background.add_task(process, raw)
    return {"accepted": True}
```

`Request` 對應 .NET 的 `HttpContext.Request`。需要它的時機不多：驗 webhook 簽章（需要未經處理的原始 body）、讀 `request.client.host`、讀 middleware 塞進 `request.state` 的東西。**日常參數不要走 `Request` 手動解析**，那等於放棄驗證與文件。

---

## 三、`Annotated` 是目前建議的寫法

同一件事有兩種寫法：

```python
# 舊寫法：把 Query() 當預設值
def list_items(q: str | None = Query(default=None, max_length=50)):
    ...

# 新寫法：Annotated
def list_items(q: Annotated[str | None, Query(max_length=50)] = None):
    ...
```

舊寫法仍然支援，但新寫法有三個實質好處：

**預設值回到它該在的位置。** `= None` 就是預設值，不用去 `Query(default=...)` 裡找。

**這個函式可以正常被直接呼叫。** 舊寫法下，`list_items()` 直接呼叫會拿到一個 `Query` 物件當參數值，不是 `None`；測試或內部重用時會出怪事。

**型別檢查工具看得懂。** mypy / Pyright 在舊寫法下會抱怨預設值型別不符。

最實用的一點是可以把常用組合抽成別名重複使用：

```python
Pagination = Annotated[int, Query(ge=0, le=100)]

@app.get("/items")
def list_items(limit: Pagination = 20):
    ...
```

這個技巧在第 03 章講 `Depends` 時會變成主力寫法。

---

## 四、路由順序：宣告順序就是匹配順序

回到開頭的問題。FastAPI 的路由儲存在一個 list 裡，請求進來時由前往後找第一個匹配的，**沒有優先序演算法**。所以規則只有一條：

> 具體的路徑寫在前面，帶參數的寫在後面。

```python
@app.get("/users/me")             # ✓ 先宣告
def get_current_user(): ...

@app.get("/users/{user_id}")      # ✓ 後宣告
def get_user(user_id: int): ...
```

有個容易誤導的觀察：如果把 `user_id` 標成 `int`，`/users/me` **看起來**會正常運作——因為 `"me"` 轉 int 失敗。但這時候回的是 **422**，不是路由沒匹配到，前端拿到的錯誤訊息會很難懂。而且一旦 id 型別改成 `str`（UUID、帳號名），問題立刻復活。**別依賴型別轉換來做路由消歧義**，順序才是正解。

第二個要知道的是**尾斜線**。Starlette 預設開啟 `redirect_slashes`：註冊了 `/items`，請求 `/items/` 會收到 **307 Temporary Redirect** 導到 `/items`（反之亦然）。

307 會保留原本的 method 和 body，所以 POST 通常還是能成功。但它在兩個場景會炸：

- 前端用 `fetch` 且伺服器在反向代理後面時，重導的 `Location` 可能是內部位址（`http://10.x.x.x:8000/items`）
- CORS 預檢後的重導在部分瀏覽器組合下會失敗

解法是**團隊內統一約定**（建議：集合用 `/items`，不加尾斜線），並在 API 文件裡寫死。

---

## 五、回應：狀態碼與模型

預設回 200。要改用 `status_code`：

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate):
    ...

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    repo.delete(item_id)
    # 204 不能有 body，所以什麼都不回
```

用 `status.HTTP_201_CREATED` 而不是裸數字 `201`，理由和 .NET 用 `StatusCodes.Status201Created` 一樣：可讀、可被 IDE 補全、不會打錯。

`response_model` 宣告回應的形狀，它同時做三件事——過濾欄位、驗證輸出、產生文件：

```python
@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int) -> Any:
    return repo.find(user_id)     # 就算回傳含 password_hash，也會被濾掉
```

也可以直接用回傳型別註解（FastAPI 會採用它）：

```python
@app.get("/users/{user_id}")
def get_user(user_id: int) -> UserOut:
    ...
```

兩者衝突時 `response_model` 參數優先。**這個過濾行為是安全機制不是格式化工具**，第 02 章會展開。

### 文件用的中繼資料

```python
@app.post(
    "/items",
    status_code=201,
    response_model=ItemOut,
    tags=["items"],
    summary="建立品項",
    responses={409: {"description": "名稱重複"}},
)
def create_item(payload: ItemCreate):
    """
    建立一個新品項。

    價格必須大於 0，名稱在同一分類下唯一。
    """
```

docstring 會變成 `/docs` 上的詳細說明，支援 Markdown。`responses` 用來補上那些不是正常路徑的狀態碼——否則文件上只看得到 200 和 422。

---

## 六、`APIRouter`：把路由拆成模組

所有東西堆在 `main.py` 撐不過三個禮拜。`APIRouter` 是 FastAPI 的分模組單位，地位相當於 Controller：

```python
# app/api/routers/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def list_users(): ...

@router.get("/{user_id}")
def get_user(user_id: int): ...
```

```python
# app/main.py
from fastapi import FastAPI
from app.api.routers import users, orders

app = FastAPI()
app.include_router(users.router)
app.include_router(orders.router)
```

`APIRouter` 的建構參數幾乎都可以在 `include_router` 時再指定或疊加：

| 參數 | 作用 |
| --- | --- |
| `prefix` | 路徑前綴，**不能以斜線結尾** |
| `tags` | 文件分組 |
| `dependencies` | 整組路由共用的 dependency（常用於驗證，見第 03、07 章） |
| `responses` | 共用的額外回應說明 |

版本前綴這樣掛：

```python
app.include_router(users.router, prefix="/api/v1")
# 最終路徑：/api/v1/users
```

注意 router 內的路徑寫 `@router.get("")` 而不是 `@router.get("/")`——後者會讓最終路徑變成 `/api/v1/users/`，就踩到前面說的尾斜線重導。

**匯入順序仍然決定匹配順序。** 前綴不重疊時不會有事；一旦有 `/users/{user_id}` 和另一個 router 的 `/users/search` 這種跨檔案的重疊，順序問題會變得很難查。這也是為什麼「同一個資源的路由放在同一個檔案」是值得堅持的紀律。

---

## 七、常見誤解

**「`str | None` 就是選填。」**
不是。選填只取決於**有沒有預設值**。`q: str | None` 沒給預設值時是「必填，但可以傳 null」；要選填必須寫 `q: str | None = None`。

**「路由順序不重要，框架會挑最精確的。」**
那是 ASP.NET Core 的行為。FastAPI 是由上往下找第一個匹配，先宣告先贏。`/users/me` 必須寫在 `/users/{user_id}` 前面。

**「參數沒收到，是前端送錯了。」**
先看你的簽章。`list[str]` 少了 `Query()` 會被判成 body；單一 `str` 想放 body 少了 `Body(embed=True)` 會被判成 query。看 422 回應裡的 `loc` 欄位——它明確告訴你 FastAPI 認為這個參數該從哪裡來，`["query", "tag"]` 就是它在 query 找。

**「`response_model` 只是拿來產文件的。」**
它會**實際過濾回傳資料**。回傳物件上有而 model 上沒有的欄位會被丟掉。這是防止密碼雜湊、內部欄位外洩的機制，不是裝飾。

**「加了尾斜線只是小事。」**
307 重導在反向代理與 CORS 場景下會產生難以診斷的失敗。統一約定，不要靠重導。

---

## 八、同事會來問你的問題

**「我這個參數 FastAPI 會從哪裡拿？」**
四步：名字在路徑模板裡就是 path；有 `Query()`/`Body()`/`Header()` 這類標注就依標注；型別是 Pydantic model 就是 body；其餘單純型別是 query。必填與否只看有沒有預設值。

**「為什麼 `/users/me` 打不到？」**
路由是一個 list，由上往下匹配第一個成功的，`/users/{user_id}` 先宣告就先攔截。把具體路徑移到參數路徑前面。不要靠 `user_id: int` 的轉換失敗來繞過——那回的是 422，而且改成字串 id 就破功。

**「我想在 body 傳一個字串，為什麼收不到？」**
單純型別預設被判成 query。要放 body 得寫 `Annotated[str, Body(embed=True)]`，客戶端則要送 `{"參數名": "值"}`。多數情況下更好的做法是定義一個只有一個欄位的 Pydantic model——之後要加欄位不會破壞契約。

**「`Annotated` 和把 `Query()` 當預設值，差在哪？」**
效果一樣，但 `Annotated` 讓預設值留在原位、讓函式可以被直接呼叫（舊寫法直接呼叫會拿到 `Query` 物件）、也讓型別檢查工具不報錯。而且可以抽成型別別名重複使用。新程式碼一律用 `Annotated`。

**「`/items` 和 `/items/` 有差嗎？」**
有。Starlette 預設會 307 重導把兩者接起來，method 和 body 會保留，所以多半「看起來能動」。但在反向代理後面重導的 Location 可能指向內部位址，CORS 預檢後的重導也可能失敗。團隊統一一種寫法，別依賴重導。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[00-why-fastapi-and-setup]] — 上一章：ASGI 與型別提示
- [[02-pydantic-and-validation]] — 下一章：body 進來之後由誰驗證
- [[03-dependency-injection]] — `Depends` 參數的完整機制
- [[03-routing-and-endpoints]] — ASP.NET Core 的對應章節（有優先序演算法的那一套）
