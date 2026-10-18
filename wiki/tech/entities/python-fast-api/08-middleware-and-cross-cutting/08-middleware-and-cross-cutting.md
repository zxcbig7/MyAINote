---
type: concept
domain: tech
tags: [python, fastapi, middleware, asgi, cors, logging, observability, trace-id, reverse-proxy]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 08 章：Middleware 與橫切關注 — 註冊順序是反的，以及那個假的 CORS 錯誤

## 兩個團隊各說各話

前端在群組貼了 console 的紅字：

```text
Access to fetch at 'https://api.example.com/orders' from origin 'https://app.example.com'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
on the requested resource.
```

「你們 CORS 沒設好。」

後端回：「設了啊，`CORSMiddleware` 第一行就加了，而且大部分請求都正常，只有偶爾這樣。」

兩邊都沒說錯。真相是：那個請求的 token 過期了，後端回了 401——但這個 401 是**在 CORS middleware 的外層產生的**，所以回應上沒有 `Access-Control-Allow-Origin`。瀏覽器看到缺少那個 header，就把它報成 CORS 錯誤，**真正的 401 被藏起來了**。

前端於是花了半天調 CORS，後端花了半天證明 CORS 沒問題，而實際的問題是 token 該 refresh 了。

這個事故的根源是一個和 ASP.NET Core **完全相反**的規則：

> **FastAPI 的 middleware，註冊順序與執行順序是反的。最後加的跑在最外層。**

這一章要把 middleware 這一層講清楚：它和 dependency 怎麼分工、順序規則、CORS 的實際踩法、以及怎麼讓每一行 log 自動帶上 trace_id。

---

## 一、ASGI middleware 與那個反過來的順序

### 三種寫法

**寫法一：裝飾器（最常見）**

```python
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response
```

`call_next(request)` 就是「呼叫下一層」，等同 .NET 的 `await next(context)`。前後各做一次工作，這是完全一樣的洋蔥模型。

**寫法二：`add_middleware`（外掛都用這個）**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware, allow_origins=[...])
```

**寫法三：純 ASGI**（效能敏感時用，見第七節）

```python
class TraceMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        ...
        await self.app(scope, receive, send)
```

### 順序：這一節是本章重點

Starlette 的 `add_middleware` 是**插入到清單最前面**（`insert(0, ...)`），所以最後註冊的會包在最外層。完整堆疊：

```python
app.add_middleware(A)      # 第一個加
app.add_middleware(B)
app.add_middleware(CORSMiddleware)   # 最後加
```

實際執行：

```text
ServerErrorMiddleware          ← 框架的，永遠最外層
  └── CORSMiddleware           ← 最後註冊 = 最外層
        └── B
              └── A            ← 最先註冊 = 最內層
                    └── ExceptionMiddleware
                          └── 路由 → dependency → endpoint
```

對照 ASP.NET Core，那邊 `app.UseX()` 的**順序就是執行順序**——先寫的先執行。FastAPI 是反的。這是從 .NET 過來最容易搞錯的一件事，而且它不會報錯，只會讓行為變得詭異。

一句話記住：

> **希望它包在最外層（最早進入、最晚離開）的 middleware，要最後註冊。**

回到開頭的事故：`CORSMiddleware` 加在第一行 = 最內層，它外面那些 middleware 產生的回應（包括驗證失敗的 401）都不會經過它加上 CORS header。修法是把它移到最後一個 `add_middleware`。

實務上建議固定成這個模板：

```python
# 由內而外註冊——順序反過來讀才是執行順序
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestContextMiddleware)      # trace_id
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(CORSMiddleware, **cors_kwargs)  # 最外層
```

---

## 二、middleware 還是 dependency？

這是 FastAPI 特有的抉擇——ASP.NET Core 沒有完全對應的問題，因為那邊橫切關注就是 middleware 或 filter 二選一。

| | middleware | dependency |
| --- | --- | --- |
| 執行範圍 | **每個請求**（含 404、`/docs`、靜態檔） | 只有掛上它的路由 |
| 看得到路由資訊嗎 | **看不到**（它在路由解析之前） | 看得到 |
| 可以用 DI 嗎 | 不行（要自己從 `app.state` 拿） | 可以 |
| `raise HTTPException` | **會變成 500**（第 06 章） | 正常運作 |
| 能改回應嗎 | 可以（加 header、壓縮） | 不行（只能在請求前作用） |
| 出現在 OpenAPI 文件 | 不會 | 會（參數會冒泡上去） |

前兩列決定了大多數情況：

**用 middleware 的時機**——真正對「每一個請求」都成立的事：CORS、壓縮、產生 trace_id、記錄 access log、量測耗時、加安全性 header。

**用 dependency 的時機**——其他全部。認證、授權、分頁參數、租戶解析、稽核記錄。

一個實際的判準：**如果這件事需要知道「這個請求打到哪支 endpoint」，就不能用 middleware。** middleware 執行時路由還沒解析，`request.url.path` 拿得到，但「這支 endpoint 需不需要登入」這種資訊拿不到。

（技術上可以在 middleware 裡用 `request.scope["route"]`，但那只在 `call_next` 之後才有值——也就是說事情已經做完了。）

還有第三列的實務理由：middleware 拿不到 DI，要用資料庫就得自己 `SessionLocal()`，繞過了整套依賴管理與測試覆寫機制。這通常是「這件事其實該用 dependency」的訊號。

---

## 三、CORS

### 先講清楚它不是什麼

CORS **不是後端的安全機制**，它是瀏覽器的規則。同源政策（Same-Origin Policy）禁止網頁的 JavaScript 讀取不同來源的回應，CORS 是伺服器用來說「我允許這個來源讀我」的方式。

三個推論：

- CORS 只約束**瀏覽器**。`curl`、Postman、後端對後端的呼叫完全不受影響。
- 設 `allow_origins=["*"]` **不會**讓你的 API 變不安全——認證授權才是安全邊界。但它會讓任何網站的 JS 都能代表已登入的使用者呼叫你的 API（如果憑證會自動附帶），所以搭配 cookie 時要小心。
- CORS 擋不住任何攻擊者。它保護的是**使用者**，不是伺服器。

### 設定

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
```

### 四個高頻踩點

**一、`allow_credentials=True` 不能配 `allow_origins=["*"]`。**

瀏覽器規範明文禁止 `Access-Control-Allow-Origin: *` 與憑證併用。不同版本的 Starlette 對這個組合的處理不一致（有的回星號，有的回實際 origin），**不要依賴它**——明確列出允許的來源才是正確做法。需要多環境就從設定讀清單：

```python
allow_origins=settings.cors_origins    # 從環境變數讀，逗號分隔
```

**二、preflight。**

跨來源的請求如果不是「簡單請求」（帶了 `Authorization`、`Content-Type: application/json`、或用了 PUT/DELETE），瀏覽器會先送一個 `OPTIONS` 請求問「我可以送嗎」。這個 OPTIONS 由 `CORSMiddleware` 直接回應，不會進到你的路由。

所以如果你在別的 middleware 裡對所有請求做驗證，記得**放行 OPTIONS**——否則 preflight 被擋，真正的請求根本送不出來。這也是「CORSMiddleware 該在最外層」的另一個理由。

`max_age=600` 讓瀏覽器快取 preflight 結果十分鐘，可以明顯減少請求數。

**三、`expose_headers` 沒設，前端讀不到你的自訂 header。**

預設情況下跨來源的回應，JS 只讀得到六個基本 header。你加的 `X-Request-ID`、分頁用的 `X-Total-Count`，不寫進 `expose_headers` 的話前端就是拿不到，而且不會有任何錯誤訊息——`response.headers.get('X-Request-ID')` 就只是回 `null`。

**四、錯誤回應也需要 CORS header。**

就是開頭那個事故。任何在 `CORSMiddleware` 外層產生的回應都不帶 CORS header，於是所有錯誤在前端看來都變成「CORS 錯誤」，真正的狀態碼被掩蓋。

### 一張診斷表

| 前端看到 | 真正的原因 |
| --- | --- |
| `No 'Access-Control-Allow-Origin' header` 但只偶爾發生 | 錯誤回應在 CORS middleware 外層產生 → 把它移到最後註冊 |
| preflight 回 401/403 | 你的驗證 middleware 攔了 OPTIONS |
| 一切正常但讀不到某個 header | 少了 `expose_headers` |
| cookie 沒被送出 | 前端少了 `credentials: 'include'`，或後端少了 `allow_credentials` |
| 改了設定沒生效 | 瀏覽器快取了 preflight（`max_age`），開無痕視窗測 |

---

## 四、Request ID：讓 log 自己帶上下文

第 06 章的錯誤回應裡有一個 `trace_id`。這一節把它做出來。

目標有兩個：每個請求有唯一識別、而且**這個請求裡的每一行 log 都自動帶上它**，不需要每次手動傳。

```python
# app/core/context.py
import contextvars

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
```

`contextvars` 是這裡的關鍵。它是 Python 3.7 引入的機制，**每個 asyncio task 有自己獨立的一份值**——所以並發的請求不會互相污染，這一點是 thread-local 做不到的（因為多個請求共用同一條執行緒）。

```python
# app/core/middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        request.state.trace_id = request_id
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response
```

**沿用上游傳來的 `X-Request-ID`** 是重點：這樣一個請求穿過 Ingress、閘道、多個服務時，同一個 id 會貫串整條鏈，查問題時可以一次撈出全部相關的 log。這對應 .NET 那邊的 `TraceId`／W3C `traceparent`。

（如果環境裡已經有 OpenTelemetry 或 Istio 在注入 `traceparent`，直接沿用那個標準 header 會更好，不要另外發明一套。）

接下來讓 logger 自動帶上：

```python
# app/core/logging.py
import logging

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True
```

掛上之後，程式碼裡任何一行 `logger.info("訂單建立成功")` 產出的 log 都會有 `request_id` 欄位，不需要傳參數。

---

## 五、結構化 logging

容器環境裡的 log 有兩條鐵律：**只寫 stdout/stderr**（不要寫檔案——容器重啟就沒了，而且 K8s 的收集機制是讀 stdout），以及**寫成 JSON**（讓 ELK / Loki 可以依欄位查詢，而不是靠正則去撈）。

```python
# app/core/logging.py
import json
import logging
from logging.config import dictConfig

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def setup_logging(level: str = "INFO") -> None:
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": RequestIdFilter}},
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json",
                "filters": ["request_id"],
            }
        },
        "root": {"handlers": ["default"], "level": level},
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": level, "propagate": False},
            "sqlalchemy.engine": {"level": "WARNING"},
        },
    })
```

三個容易漏的細節：

**要一起接管 uvicorn 的 logger。** 不然你的應用 log 是 JSON、uvicorn 的 access log 是純文字，收集端會有一半解析失敗。`propagate: False` 是避免同一筆 log 被印兩次。

**`ensure_ascii=False`。** 少了它，中文訊息會變成 `訂單` 這種跳脫序列，在 Kibana 上看得很痛苦。

**`disable_existing_loggers: False`。** 設成 True 會把匯入時就建好的第三方 logger 全部關掉，然後你會困惑為什麼 SQLAlchemy 一句話都不說。

### 記錄什麼

| 該記 | 不該記 |
| --- | --- |
| request_id、method、path、狀態碼、耗時 | 密碼、token、完整信用卡號 |
| 業務關鍵事件（訂單建立、付款成功）+ 業務 id | 完整的 request body（可能含個資） |
| 未處理例外的完整 traceback | 每一支 SQL（正式環境關掉 `echo`） |
| 下游呼叫的目標與耗時 | 大量的 DEBUG（正式環境成本很高） |

**access log 建議自己記而不是用 uvicorn 的**，因為你需要 request_id 和耗時：

```python
@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
        },
    )
    return response
```

（`extra` 裡的欄位要讓 `JsonFormatter` 也輸出，上面的簡化版只處理了固定欄位，實際專案通常會把 `record.__dict__` 裡非標準的鍵一併帶出。）

---

## 六、反向代理下的三個設定

K8s 環境裡你的應用永遠在某個東西後面（Ingress、Istio、Cloudflare）。三件事要處理：

**一、`--proxy-headers`。** 不開的話，`request.url` 會是 `http://` 而不是 `https://`，`request.client.host` 會是代理的 IP 而不是使用者的。這會影響 OAuth 的 redirect_uri、產生的絕對連結、以及依 IP 的限流。

```powershell
uvicorn app.main:app --proxy-headers --forwarded-allow-ips="*"
```

`--forwarded-allow-ips` 決定信任哪些來源送的 `X-Forwarded-*`。填 `*` 表示全信——**只有在確定外部流量無法直接到達這個 port 時才可以這樣設**（K8s 裡通常成立，因為 Service 只在叢集內開放）。否則任何人都能偽造來源 IP 繞過你的限流。

**二、`TrustedHostMiddleware`。** 檢查 `Host` header，擋掉 host header 注入（攻擊者送假的 Host，讓你產生的重設密碼連結指向他的網域）。

```python
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.internal"])
```

**三、`GZipMiddleware`。** 如果 Ingress 已經做了壓縮就不要重複做。做兩次不會壞，但白費 CPU。

---

## 七、middleware 的效能成本

`BaseHTTPMiddleware`（也就是 `@app.middleware("http")` 背後那個）有已知的額外開銷：它為了提供 `call_next` 這個好用的介面，內部會多開一個 task 並把回應包成串流。實務上的後果是每個請求多幾百微秒到一兩毫秒，而且**它和串流回應、背景任務的互動有一些邊角問題**。

一般 API 不必在意這個數字。但如果你堆了五六層 `@app.middleware("http")`，或有極低延遲要求，改寫成純 ASGI middleware（第一節的寫法三）會明顯更輕。

更常見的優化其實是**減少 middleware 數量**：很多寫成 middleware 的東西（稽核、租戶解析、權限）本來就該是 dependency，那樣它們只在需要的路由上執行，而不是每個請求——包含健康檢查和 `/docs`——都跑一遍。

順帶一提，**健康檢查端點值得特別對待**。它每幾秒就被打一次，如果每次都走完整條 middleware 鏈並產生一行 access log，正式環境的 log 量會被它主導。實務做法是在 access log 的 middleware 裡跳過 `/health` 這類路徑。

---

## 八、常見誤解

**「middleware 的註冊順序就是執行順序。」**
反的。Starlette 把新的 middleware 插到清單最前面，所以**最後註冊的在最外層**。這和 ASP.NET Core 的 `app.UseX()` 相反，而且不會有任何錯誤提示。

**「CORS 錯誤就是 CORS 設定的問題。」**
很多時候不是。錯誤回應在 CORS middleware 外層產生時不帶 CORS header，瀏覽器就把它報成 CORS 問題，掩蓋了真正的 401/500。看到「偶爾發生的 CORS 錯誤」，先確認 `CORSMiddleware` 是不是最後註冊的。

**「`allow_origins=["*"]` 很危險。」**
它本身不會讓 API 變不安全——認證授權才是安全邊界。但它不能和 `allow_credentials=True` 併用（瀏覽器規範禁止），而且搭配 cookie 認證時確實有風險。正式環境還是明確列出來源。

**「在 middleware 裡做認證比較集中。」**
middleware 看不到路由資訊、拿不到 DI、`raise HTTPException` 會變成 500，而且會對 `/docs`、健康檢查、404 全部執行。認證用 dependency 掛在 router 上，這些問題全都不存在。

**「log 寫檔案比較好保存。」**
容器裡不要寫檔案。容器重啟 log 就沒了，而且 K8s 的收集機制是讀 stdout。寫 JSON 到 stdout，讓 ELK 或 Loki 去處理保存與查詢。

**「`request.url` 就是使用者看到的網址。」**
在反向代理後面不是。沒開 `--proxy-headers` 的話你會拿到 `http://` 和內部 IP，OAuth 的 redirect_uri 和產生的絕對連結都會錯。

---

## 九、同事會來問你的問題

**「middleware 要照什麼順序加？」**
記住順序是反的——最後註冊的在最外層。所以由內而外註冊：壓縮、trace_id、TrustedHost，最後才是 CORS。CORS 一定要最外層，否則錯誤回應不會帶 CORS header。

**「前端說有 CORS 問題，但我設定看起來沒錯。」**
先問是不是「偶爾」發生。是的話多半是錯誤回應（401、500）在 CORS middleware 外層產生，缺了 header 被瀏覽器報成 CORS 錯誤。其次檢查三件事：preflight 的 OPTIONS 有沒有被你的驗證擋掉、自訂 header 有沒有寫進 `expose_headers`、`allow_credentials` 和 `allow_origins=["*"]` 有沒有併用。

**「這個功能該寫 middleware 還是 dependency？」**
問一句話：這件事需要知道請求打到哪支 endpoint 嗎？需要就用 dependency（middleware 在路由解析之前執行）。另外，需要 DI、需要 `raise HTTPException`、只適用部分路由——三者任一成立就用 dependency。middleware 留給真正對每個請求都成立的事：CORS、壓縮、trace_id、access log。

**「怎麼讓每行 log 都帶上 request id？」**
用 `contextvars` 存 id（不能用 thread-local，因為並發請求共用執行緒），middleware 在進入時 set、離開時 reset，再加一個 `logging.Filter` 把它塞進每筆 record。之後所有 `logger.info(...)` 自動帶上，不用傳參數。id 要優先沿用上游的 `X-Request-ID` 或 `traceparent`，這樣才能跨服務貫串。

**「為什麼我的 log 有兩種格式？」**
uvicorn 的 logger 沒被接管。在 `dictConfig` 裡把 `uvicorn`、`uvicorn.access`、`uvicorn.error` 三個 logger 一起設定，並設 `propagate: False` 避免重複輸出。

**「上了 K8s 之後 OAuth 的 redirect_uri 變成 http，怎麼回事？」**
uvicorn 沒開 `--proxy-headers`，所以它不信任 Ingress 送來的 `X-Forwarded-Proto`。加上 `--proxy-headers --forwarded-allow-ips="*"`（後者只在確定外部無法直接連到這個 port 時才能填星號）。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[07-auth-and-jwt]] — 上一章：為什麼認證該用 dependency
- [[09-configuration]] — 下一章：CORS 來源清單怎麼從環境注入
- [[06-error-handling]] — middleware 裡 `raise` 為什麼會變 500
- [[16-logging-and-observability]] — ASP.NET Core 的對應章節（結構化 log 與 TraceId）
- [[01-request-pipeline]] — .NET 那邊的 middleware 洋蔥（順序規則相反）
