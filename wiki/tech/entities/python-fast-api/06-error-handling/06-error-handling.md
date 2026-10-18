---
type: concept
domain: tech
tags: [python, fastapi, error-handling, exception, http-status, problem-details, logging]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 06 章：錯誤處理 — 例外該在哪一層接，什麼錯回什麼狀態碼

## 「你們的錯誤格式有四種」

前端工程師在群組裡貼了四段回應：

```jsonc
// 驗證失敗
{ "detail": [ { "type": "missing", "loc": ["body", "email"], "msg": "Field required" } ] }

// 找不到資源
{ "detail": "order not found" }

// 未處理例外
{ "detail": "Internal Server Error" }

// 某支 endpoint 自己刻的
{ "success": false, "error": "庫存不足" }        // 而且 HTTP 狀態碼是 200
```

「`detail` 有時候是陣列、有時候是字串，還有一支根本不用 `detail`，而且失敗卻回 200。我要寫幾套解析邏輯？」

這個抱怨完全合理。前三種是 FastAPI 的預設行為——它們各自都很合理，但湊在一起沒有一致性；第四種是有人繞過了框架自己發明格式。

錯誤處理不是「加個 try/except」這麼簡單的事。它牽涉三個決策：**例外在哪一層被攔截**、**什麼錯對應什麼狀態碼**、以及**回給客戶端的東西長什麼形狀**。這一章把三件事講完，並給出一份可以直接抄進專案的統一處理器。

讀完之後，你應該能夠設計一套一致的錯誤契約、知道 service 層為什麼不該丟 `HTTPException`、以及看到一個資料庫例外就知道它該變成 409 還是 500。

---

## 一、FastAPI 的例外處理架構

請求進來之後，一個例外可能在很多地方被丟出來。FastAPI（底層是 Starlette）的處理結構長這樣：

```text
ServerErrorMiddleware        ← 最外層，接住所有漏網的例外，回 500
  └── 你註冊的 middleware
        └── ExceptionMiddleware   ← 查表：這個例外有沒有註冊 handler
              └── 路由 → dependency → endpoint
```

`ExceptionMiddleware` 持有一份對照表（`app.exception_handlers`），把例外型別對應到處理函式。預設表裡有兩筆：

| 例外 | 預設處理 | 回應 |
| --- | --- | --- |
| `HTTPException` | 轉成對應狀態碼 | `{"detail": ...}` |
| `RequestValidationError` | 422 | `{"detail": [ ...錯誤清單... ]}` |

沒有登記的例外會一路穿到最外層的 `ServerErrorMiddleware`，回一個 500。

### 一個重要的位置細節

注意 `ExceptionMiddleware` 在**你註冊的 middleware 內側**。這代表：

> **在自訂 middleware 裡丟出的 `HTTPException`，不會被 exception handler 處理。**

它會直接穿到 `ServerErrorMiddleware` 變成 500。想在 middleware 裡回錯誤，必須自己回傳一個 `Response` 物件，不能 `raise`：

```python
@app.middleware("http")
async def check_api_key(request: Request, call_next):
    if request.headers.get("X-API-Key") != settings.api_key:
        return JSONResponse(status_code=401, content={"detail": "invalid api key"})  # ✓
        # raise HTTPException(401)  ← ✗ 會變成 500
    return await call_next(request)
```

這是 FastAPI 一個著名的坑，而且錯誤訊息完全不會提示你。多數情況下**用 dependency 取代 middleware 就沒這個問題**——dependency 在 `ExceptionMiddleware` 內側，`raise` 是正常運作的。這也是為什麼上一章說「FastAPI 裡 dependency 常常取代了 .NET 的 Filter」。

---

## 二、`HTTPException`：用 `raise` 不用 `return`

```python
from fastapi import HTTPException, status

@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: DbSession):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "order not found")
    return order
```

為什麼是 `raise` 而不是 `return`？

因為 `return` 只能在 endpoint 本體用。實際上大部分的錯誤判斷發生在更深的地方——dependency 裡（權限不足）、service 裡（庫存不足）、repository 裡（找不到）。那些地方的回傳值有自己的用途，沒辦法「回傳一個 HTTP 錯誤」。`raise` 可以從任何深度直接中止整條呼叫鏈。

需要附加 header 時用第三個參數，最典型的是 401：

```python
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)
```

`WWW-Authenticate` 是 HTTP 規範要求 401 必須附帶的，說明該用什麼方式認證。第 07 章會用到。

---

## 三、狀態碼決策表

這張表是本章最實用的部分。每一列都是實際會爭論的邊界：

| 狀況 | 狀態碼 | 說明 |
| --- | --- | --- |
| 請求語法錯誤（JSON 壞掉、參數型別不對） | 400 | 客戶端根本沒把請求組對 |
| 語法對但語意不通過（缺必填、超出範圍） | **422** | FastAPI 的預設；.NET 是 400 |
| 沒帶憑證，或憑證無效／過期 | **401** | 「我不知道你是誰」 |
| 身分確認了但權限不足 | **403** | 「我知道你是誰，但你不能做這件事」 |
| 資源不存在 | 404 | |
| 資源存在但不該讓這個人知道它存在 | **404**（不是 403） | 回 403 等於確認了資源存在 |
| 狀態衝突（重複 email、樂觀鎖失敗、訂單已出貨不能取消） | **409** | |
| 請求太頻繁 | 429 | 要附 `Retry-After` |
| 伺服器自己出錯 | 500 | 不要洩漏細節 |
| 下游依賴掛了（資料庫連不上、外部 API 逾時） | **503** | 要附 `Retry-After`，讓呼叫端知道可以重試 |
| 上游服務回了無效內容 | 502 | |

三個最容易吵的：

**401 vs 403。** 分界是「身分」而不是「有沒有登入」。token 過期是 401（身分無法確認），一般使用者想刪別人的訂單是 403（身分確認了，權限不夠）。

**403 vs 404。** 多租戶系統裡這是個資安判斷。使用者 A 查詢使用者 B 的訂單，回 403 等於告訴 A「這張訂單存在」——那本身就是資訊洩漏。**看不到的東西一律回 404**。實作上這通常不需要特別處理，因為查詢本來就會加上租戶條件，查不到自然是 404。

**500 vs 503。** 這個區分對維運很重要。500 表示「程式有 bug」，重試沒用；503 表示「暫時不可用」，重試會成功。監控告警的處理方式完全不同——500 要叫工程師起床，503 通常先看下游。

---

## 四、統一錯誤格式

回到開頭的抱怨。解法是**覆寫全部三個處理器**，讓所有錯誤走同一個形狀。

格式建議直接採用 **RFC 9457（Problem Details for HTTP APIs）**，也就是 ASP.NET Core 的 `ProblemDetails` 用的那個標準。理由是它已經被廣泛實作、欄位語意清楚、而且允許自由擴充：

```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 422,
  "detail": "請求內容有 2 個欄位不符合規則",
  "instance": "/api/v1/orders",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "errors": [
    { "field": "body.customer_email", "message": "value is not a valid email address" },
    { "field": "body.items", "message": "List should have at least 1 item" }
  ]
}
```

實作：

```python
# app/core/errors.py
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def problem(status_code: int, title: str, detail: str, request: Request, **extra):
    body = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "trace_id": getattr(request.state, "trace_id", None),
        **extra,
    }
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type="application/problem+json",
    )

def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(RequestValidationError)
    async def on_validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return problem(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation Error",
            f"請求內容有 {len(errors)} 個欄位不符合規則",
            request,
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def on_http_exception(request: Request, exc: StarletteHTTPException):
        return problem(exc.status_code, exc.detail, exc.detail, request)

    @app.exception_handler(Exception)
    async def on_unhandled(request: Request, exc: Exception):
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return problem(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "伺服器發生未預期的錯誤，請聯絡管理員並提供 trace_id",
            request,
        )
```

三個實作細節值得說明：

**註冊在 `StarletteHTTPException` 而不是 `fastapi.HTTPException`。** FastAPI 的 `HTTPException` 繼承自 Starlette 的，但**框架內部產生的 404（路由不存在）、405（method 不允許）丟的是 Starlette 那個**。註冊在父類別上才能一網打盡。

**`logger.exception` 只寫在未處理例外那個 handler 裡。** `HTTPException` 是預期中的流程（找不到、權限不足），不該產生 error 級別的 log，否則正式環境的錯誤 log 會被 404 淹沒。

**回應裡帶 `trace_id` 但不帶 stack trace。** 客戶端拿到 id 回報，工程師用 id 去 log 裡撈完整內容。這是把「使用者需要的資訊」和「工程師需要的資訊」分開的標準做法，第 08 章會補上產生 `trace_id` 的 middleware。

### `Exception` handler 的一個特性

Starlette 的 `ServerErrorMiddleware` 在呼叫你的 `Exception` handler 送出回應之後，**會把原本的例外重新拋出**，讓 ASGI server（uvicorn）也記錄一次。所以你會在 log 裡看到兩份紀錄：你自己 `logger.exception` 那份（有 trace_id 和請求資訊），加上 uvicorn 的那份。這是預期行為，不是重複處理。

### 順帶把 `debug` 關掉

```python
app = FastAPI(debug=True)     # ✗ 絕對不要用在正式環境
```

`debug=True` 會把完整的 stack trace 寫進回應內容。那裡面有檔案路徑、程式碼片段，有時候還有變數值——等於把伺服器內部結構送給任何一個能觸發錯誤的人。

---

## 五、如果團隊規範要求 422 改成 400

前一節的處理器已經接管了 `RequestValidationError`，改狀態碼只要動一個常數：

```python
return problem(
    status.HTTP_400_BAD_REQUEST,       # ← 從 422 改成 400
    "Validation Error",
    ...,
)
```

但要注意 **OpenAPI 文件不會跟著改**——`/docs` 上仍然標示 422，因為那是 FastAPI 產生 schema 時寫死的。要文件也一致，得覆寫 `responses` 或後製 OpenAPI schema，通常不值得。

我的建議是**留著 422**。它語意更精確，而且既然前端已經要為統一格式改一次程式碼，順便對齊語意是划算的。真正該避免的是「同一個團隊裡兩種後端回不同狀態碼」——先講好比選哪個重要。

---

## 六、領域例外：service 層不該知道 HTTP

一個很常見的寫法：

```python
# app/services/order_service.py
def cancel(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "order not found")          # ✗
    if order.owner_id != user.id:
        raise HTTPException(403, "not your order")           # ✗
    if order.status == "shipped":
        raise HTTPException(409, "已出貨的訂單不能取消")        # ✗
    ...
```

能動，而且對小專案來說完全可以接受。但它有兩個成本：

**一、service 層被 HTTP 綁死。** 同一段業務邏輯想被排程 worker、CLI 工具、或訊息佇列的 consumer 呼叫時，`HTTPException` 在那些情境毫無意義——沒有 HTTP 回應可以送。

**二、業務規則的語意被壓縮成數字。** `409` 說不出是「已出貨」還是「已取消」還是「已退款」，而前端往往需要區分它們來顯示不同訊息。

比較耐久的做法是分成兩層：

```python
# app/core/exceptions.py
class DomainError(Exception):
    code = "domain_error"
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404

class PermissionDeniedError(DomainError):
    code = "permission_denied"
    status_code = 403

class ConflictError(DomainError):
    code = "conflict"
    status_code = 409

class OrderAlreadyShippedError(ConflictError):
    code = "order_already_shipped"
```

service 層只丟領域例外，完全不知道 HTTP 的存在：

```python
def cancel(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise NotFoundError("找不到訂單")
    if order.owner_id != user.id:
        raise PermissionDeniedError("無權操作此訂單")
    if order.status == "shipped":
        raise OrderAlreadyShippedError("已出貨的訂單不能取消")
    ...
```

API 層註冊一個處理器做轉換：

```python
    @app.exception_handler(DomainError)
    async def on_domain_error(request: Request, exc: DomainError):
        return problem(exc.status_code, exc.code, exc.message, request, code=exc.code)
```

現在前端拿到的是 `"code": "order_already_shipped"` 這種可以直接 switch 的機器可讀識別，而不是一個要靠訊息字串猜的 409。而且**新增一種業務錯誤不需要改 API 層**——定義一個新的子類別就好。

這和 .NET 那邊「領域例外由統一的 `IExceptionHandler` 轉成 `ProblemDetails`」是完全一樣的設計。

---

## 七、資料庫例外

```python
from sqlalchemy.exc import IntegrityError

@app.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: DbSession):
    user = User(email=payload.email, ...)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("此 email 已被註冊")
    return user
```

三個原則：

**唯一約束衝突是 409，不是 500。** 這是使用者可以自己修正的問題，不是伺服器錯誤。同理，外鍵約束失敗通常是 400 或 409。

**永遠不要把資料庫的錯誤訊息直接回給客戶端。** `IntegrityError` 的 `str()` 裡包含完整的 SQL、資料表名、約束名，有時還有實際的參數值。那是攻擊者的地圖。要區分是哪個約束衝突，去檢查 `exc.orig`（原始的 DBAPI 例外）裡的錯誤碼，而不是把訊息轉發出去。

**「先查再寫」防不住競態。** 這個寫法看起來比較友善：

```python
if db.scalar(select(User).where(User.email == payload.email)):
    raise ConflictError("此 email 已被註冊")
db.add(User(...))
db.commit()
```

但兩個請求同時進來時，兩邊都會通過檢查，然後其中一個在 commit 時失敗。**唯一索引才是真正的保證，`try/except IntegrityError` 才是真正的處理**。先查一次只是為了給出更友善的訊息，不能取代它。

### Oracle 的錯誤碼

`ORA-00001` 是唯一約束衝突，`ORA-02291` 是外鍵不存在，`ORA-01400` 是必填欄位為 NULL。需要精細區分時：

```python
    except IntegrityError as exc:
        db.rollback()
        code = getattr(exc.orig, "code", None)      # oracledb 的錯誤物件
        if code == 1:
            raise ConflictError("資料重複")
        raise
```

不確定要不要細分的時候，**全部當成 409 加上一句通用訊息**就好。過度細分會讓錯誤處理程式碼比業務邏輯還長。

---

## 八、例外不該拿來做控制流程

```python
# ✗ 用例外表達「正常的沒有」
def get_user(db, user_id):
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("找不到")
    return user

@app.get("/users/{user_id}/badge")
def badge(user_id: int, db: DbSession):
    try:
        user = get_user(db, user_id)
        return {"badge": user.badge}
    except NotFoundError:
        return {"badge": "guest"}          # 用例外做 if/else
```

例外的成本比 `if` 高，而且它讓程式流程變得難以追蹤。「找不到」如果是一種**正常的預期結果**，就用 `None` 表達，讓呼叫端決定要不要變成錯誤：

```python
def find_user(db, user_id) -> User | None:
    return db.get(User, user_id)

@app.get("/users/{user_id}/badge")
def badge(user_id: int, db: DbSession):
    user = find_user(db, user_id)
    return {"badge": user.badge if user else "guest"}
```

命名慣例很有幫助：`find_x` 回傳 `X | None`，`get_x` 找不到就丟例外。看到函式名就知道要不要處理 `None`。

---

## 九、記錄什麼、記錄到什麼層級

| 情況 | 層級 | 記什麼 |
| --- | --- | --- |
| 驗證失敗（422） | 不記，或 DEBUG | 量大且無行動價值 |
| 找不到、權限不足（404/403） | 不記，或 INFO | 大量 403 才值得注意（可能是攻擊） |
| 業務衝突（409） | INFO | 帶上業務識別碼 |
| 下游逾時（503/502） | WARNING | 帶上下游名稱與耗時 |
| 未處理例外（500） | **ERROR + stack trace** | 完整 traceback、trace_id、請求路徑 |

最常見的錯誤是**每個 `except` 都寫 `logger.error`**，於是正式環境的 error log 裡九成是預期中的 404 和驗證失敗，真正的 bug 被埋掉。

反過來的錯誤是**吞掉例外**：

```python
try:
    ...
except Exception:
    pass          # ✗ 最糟的一行程式碼
```

如果真的要忽略，至少要記錄，並且明確寫出忽略的理由：

```python
except ExternalServiceError as exc:
    logger.warning("通知寄送失敗，不影響主流程: %s", exc)
```

完整的結構化 logging 與 trace_id 產生方式在第 08 章。

---

## 十、常見誤解

**「錯誤回 200 加一個 `success: false` 比較好處理。」**
不好。HTTP 狀態碼是整條鏈路上所有元件都看得懂的訊號——監控、負載平衡器、CDN、瀏覽器的 `fetch`、重試機制全部依賴它。回 200 表示「一切正常」，會讓錯誤率監控永遠是 0%，也讓前端的 `response.ok` 判斷失效。

**「在 middleware 裡 `raise HTTPException` 就會回對應的狀態碼。」**
不會，會變成 500。`ExceptionMiddleware` 在使用者 middleware 的內側，攔不到外側丟出的例外。要在 middleware 裡回錯誤得直接 `return JSONResponse(...)`，或改用 dependency。

**「500 的回應內容多一點細節比較好除錯。」**
給客戶端的只該有 trace_id，詳細內容進 log。stack trace 會洩漏檔案路徑、程式碼結構、有時還有變數值。`debug=True` 更是絕對不能出現在正式環境。

**「service 層丟 `HTTPException` 比較省事。」**
小專案可以。但那段邏輯一旦要被 worker、CLI 或訊息佇列的 consumer 重用，`HTTPException` 就沒有意義了。而且 409 這個數字說不出是哪一種衝突，前端沒辦法針對不同情況顯示不同訊息。

**「先查詢再寫入就能避免重複資料。」**
擋不住競態。兩個並行請求會同時通過檢查。唯一索引加 `try/except IntegrityError` 才是真正的保證，先查只是為了給出比較友善的訊息。

---

## 十一、同事會來問你的問題

**「這個錯誤該回幾？」**
沿著決策表走：沒帶或帶錯憑證是 401，權限不足是 403（但不該讓對方知道資源存在時回 404），狀態衝突是 409，我們自己壞掉是 500，下游壞掉是 503（要附 `Retry-After`）。最容易錯的是把「下游掛了」記成 500——那會讓告警把工程師叫起來查一個不是自己的問題。

**「為什麼我在 middleware 裡 raise 的 404 變成 500？」**
`ExceptionMiddleware`（負責查 handler 對照表的那層）在你的 middleware 內側，接不到外側丟出的例外。middleware 裡要回錯誤就直接 `return JSONResponse(...)`。更好的做法是改用 dependency，它在內側，`raise` 是正常運作的。

**「怎麼讓所有錯誤格式一致？」**
覆寫三個處理器：`RequestValidationError`、`StarletteHTTPException`（要註冊在 Starlette 的父類別上，才接得到框架內部產生的 404/405）、以及 `Exception`。全部走同一個 builder 函式產生 RFC 9457 格式，並統一附上 trace_id。

**「service 層要丟什麼例外？」**
自訂的領域例外，不要丟 `HTTPException`。在 API 層註冊一個處理器把 `DomainError` 轉成 HTTP。好處是 service 可以被非 HTTP 的呼叫端重用，而且可以回傳 `code` 這種機器可讀的識別讓前端 switch，比一個 409 有用得多。

**「唯一約束衝突要怎麼處理？」**
`try/except IntegrityError` 加 `rollback()`，轉成 409。不要把資料庫的錯誤訊息回給客戶端——裡面有 SQL 和資料表結構。也不要用「先查再寫」取代它，那擋不住併發。

**「error log 太多看不完怎麼辦？」**
多半是每個 `except` 都寫了 `logger.error`。預期中的流程（404、403、422）不該進 error 級別，只有未處理例外才是 ERROR + stack trace。業務衝突用 INFO，下游問題用 WARNING。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[05-database-sqlalchemy]] — 上一章：資料庫例外的來源
- [[07-auth-and-jwt]] — 下一章：401 與 403 的實際產生位置
- [[08-middleware-and-cross-cutting]] — trace_id 的產生與結構化 logging
- [[15-error-handling]] — ASP.NET Core 的對應章節（`ProblemDetails` 與 `IExceptionHandler`）
