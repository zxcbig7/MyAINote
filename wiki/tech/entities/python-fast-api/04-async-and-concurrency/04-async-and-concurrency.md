---
type: concept
domain: tech
tags: [python, fastapi, async, asyncio, event-loop, threadpool, gil, concurrency, performance]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 04 章：async 與並發 — `def` 和 `async def` 差在哪，誰會把整台服務堵死

## 一支 endpoint 拖垮全部

上線後某天，監控顯示服務的 p99 延遲從 80 毫秒跳到 6 秒，健康檢查開始失敗，K8s 把 Pod 重啟了三次。查下去發現尖峰時段有人在用這支報表匯出：

```python
@app.get("/reports/export")
async def export_report(month: str):
    data = fetch_all_rows(month)          # 同步的資料庫查詢，約 3 秒
    return {"rows": len(data)}
```

奇怪的是——**其他完全無關的 endpoint 也跟著慢了**。`/health` 這種只回 `{"status": "ok"}` 的路由，在報表跑的那三秒裡也要等三秒。

這不是資料庫壓力大，不是網路問題，也不是 CPU 滿載。這是 Python 非同步模型最典型的一次事故：`async def` 的函式裡出現了阻塞呼叫，整個 event loop 被卡住三秒，那三秒裡**這個程序不處理任何請求**。

諷刺的是，把 `async def` 改成 `def`——看起來更「舊」的寫法——問題就消失了。

這一章要把這件事講到你以後看一眼函式簽章就知道有沒有危險。它是整套教材的樞紐：後面的資料庫章、HTTP client 章、部署章的 worker 數量計算，全部建立在這一章的模型上。

讀完之後，你應該能夠說清楚：一個 uvicorn worker 裡到底有幾條執行緒在跑、`def` 和 `async def` 分別走哪條路、為什麼「反而是 `def` 比較安全」、以及 CPU 密集的工作為什麼兩條路都不該走。

---

## 一、先建立正確的心智模型

### ASP.NET Core 的模型

.NET 那邊，請求由 **ThreadPool** 處理。ThreadPool 有一組工作執行緒（預設數量與 CPU 核心數相關），而且**會自動長大**——當現有執行緒都被佔住，執行時期會慢慢注入新的執行緒。

所以在 .NET 裡寫出一段同步阻塞的程式碼，後果是「這條執行緒被佔住」。其他請求還有別的執行緒可用，服務整體仍然在動。只有當阻塞的量大到把 ThreadPool 耗光（ThreadPool 飢餓），才會全面崩壞——而那需要相當高的併發量才做得到。

**.NET 的執行緒模型會替你吸收掉大部分錯誤。**

### Python 的模型

一個 uvicorn worker 是**一個作業系統程序**，裡面有：

```text
程序（uvicorn worker）
├── 主執行緒：跑著一個 event loop  ← 所有 async 程式碼都在這裡
└── 一個 threadpool（預設上限 40 條）← 同步程式碼被丟到這裡
```

關鍵在第一行：**event loop 是單執行緒的**。所有 `async def` 的程式碼在同一條執行緒上輪流執行。它們的「並發」來自於在 `await` 的地方主動讓出控制權，讓 loop 去跑別的任務。

這是一種**協作式（cooperative）**的並發。協作的意思是：每個任務必須自己主動讓出，沒有人能強制打斷它。一個任務如果不讓出——例如它在做同步 I/O 或純運算——那 event loop 就停在那裡，**其他所有任務一律停擺**。

這就是開頭那個事故的完整解釋。`fetch_all_rows()` 是同步的，它在 event loop 上跑了三秒，期間 loop 無法處理任何其他事情，包括 `/health`。

### 為什麼不用多執行緒解決

因為 **GIL**（Global Interpreter Lock）。CPython 有一把全域鎖，同一時間只允許一條執行緒執行 Python bytecode。多開執行緒對純運算工作沒有幫助（它們會輪流拿鎖，總量不變），只對 I/O 有幫助（等待 I/O 時會釋放 GIL）。

（Python 3.13 起有實驗性的 free-threaded 建置版本可以關掉 GIL，但生態系支援還不完整，生產環境目前仍應以「有 GIL」為前提設計。）

所以 Python 的並發策略是：**用 event loop 處理 I/O 密集、用多程序處理 CPU 密集**。執行緒只是一個折衷的中間層。

---

## 二、FastAPI 怎麼處理這兩種函式

這是 FastAPI（其實是 Starlette）一個非常貼心的設計，也是它和純 asyncio 框架最大的差異：

| 你寫的 | FastAPI 的處理 | 執行位置 |
| --- | --- | --- |
| `async def endpoint()` | 直接 `await` 它 | **event loop（主執行緒）** |
| `def endpoint()` | 用 `run_in_threadpool` 包起來 | **threadpool（另一條執行緒）** |

換句話說，**寫 `def` 的時候，FastAPI 幫你把阻塞隔離掉了**。它跑在另一條執行緒上，event loop 完全不受影響，其他請求照常處理。

這條規則對 **dependency 一體適用**：`def get_db()` 也會被丟到 threadpool，`async def get_something()` 則在 loop 上執行。

所以開頭那個事故的最小修法是刪掉一個字：

```python
@app.get("/reports/export")
def export_report(month: str):        # ← async 拿掉
    data = fetch_all_rows(month)      # 在 threadpool 裡阻塞，不影響 loop
    return {"rows": len(data)}
```

這件事非常反直覺，值得寫成一句話貼在牆上：

> **在 FastAPI 裡，用 `async def` 包住同步程式碼，比用 `def` 危險得多。**

從 .NET 過來的人特別容易踩，因為 C# 的 `async` 是「加了沒壞處」的，而這裡加了會炸。

### 動手驗證

開一個空專案，貼這兩支 endpoint：

```python
import time

@app.get("/blocking-async")
async def blocking_async():
    time.sleep(5)                 # 同步睡，卡住 loop
    return {"done": True}

@app.get("/blocking-sync")
def blocking_sync():
    time.sleep(5)                 # 同步睡，但在 threadpool
    return {"done": True}

@app.get("/ping")
async def ping():
    return {"pong": True}
```

開兩個瀏覽器分頁。先打 `/blocking-async`，趁它還在跑的時候打 `/ping`——`/ping` 要等五秒。換成先打 `/blocking-sync`，`/ping` 立刻回應。

這個實驗五分鐘就能做完，做過一次之後這一章的內容就再也忘不掉了。

---

## 三、哪些呼叫是「阻塞」的

判斷的標準很單純：**這一行會不會讓執行緒停下來等**。以下全部是阻塞的，出現在 `async def` 裡就是地雷：

| 阻塞呼叫 | 非阻塞替代 |
| --- | --- |
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `requests.get(...)` | `await httpx.AsyncClient().get(...)` |
| 同步 SQLAlchemy `session.query(...)` | `await AsyncSession.execute(...)` |
| `open(...).read()` 大檔 | `aiofiles`，或改用 `def` |
| `subprocess.run(...)` | `await asyncio.create_subprocess_exec(...)` |
| `boto3` / 多數傳統 SDK | 對應的 async SDK，或改用 `def` |
| 純運算迴圈、影像處理、加解密 | 都不對，見第六節 |

一個實用的判斷法：**如果這個函式的呼叫前面沒有 `await`，而它做的事需要等待，那它就是阻塞的。**

反過來也要注意——`await` 不代表安全，重點是被 await 的東西是不是真的非同步。`await` 一個內部其實在做同步 I/O 的函式，一樣會卡住 loop。

---

## 四、`def` 也會出事：threadpool 是有上限的

前面說 `def` 比較安全，但它不是無限的。FastAPI 用的 threadpool（AnyIO 提供）**預設上限是 40 條執行緒**。

同時有超過 40 個 `def` endpoint 在執行，第 41 個請求就得排隊等別人做完。症狀和 event loop 被卡住不一樣：

| | event loop 被卡住 | threadpool 被用完 |
| --- | --- | --- |
| 症狀 | **全部**請求停止回應，包含純 async 的 | `def` 的請求開始排隊，`async def` 的仍然正常 |
| 惡化方式 | 瞬間、全面 | 漸進、部分 |
| 診斷線索 | `/health`（async）也超時 | `/health`（async）正常但業務端點慢 |

所以健康檢查端點**應該寫成 `async def` 且不做任何 I/O**——這樣它才能區分這兩種狀態。這也是 .NET 那邊「liveness probe 不可以檢查資料庫」的同一個道理，但理由更強烈：在 Python 這邊，一支同步的健康檢查會佔用你僅有的 40 個名額之一。

上限可以調：

```python
import anyio

@asynccontextmanager
async def lifespan(app: FastAPI):
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = 100
    yield
```

但**調它通常是治標**。40 條執行緒對一個程序來說已經不小，如果不夠用，代表你的服務在做大量同步 I/O，正確的方向有三個：改用 async 驅動、增加 worker 程序數、或把慢工作移出請求路徑。調高 threadpool 只是把記憶體和 context switch 的成本堆上去。

實務上真正需要調高的情境是：整個專案用同步 SQLAlchemy（很常見、也很合理），而查詢本身很快，只是併發數高。這時候調到 60–100 是合理的，但要同步確認資料庫連線池的大小跟得上——**執行緒數超過連線池大小，多出來的執行緒只是換個地方排隊**。

---

## 五、決策表

| 這支函式裡有什麼 | 用哪個 |
| --- | --- |
| 全部都是 `await` 的非同步呼叫 | `async def` |
| 完全沒有 I/O（純記憶體運算，微秒級） | 兩個都行，`async def` 少一次執行緒切換 |
| 任何同步 I/O（同步 ORM、`requests`、檔案） | **`def`** |
| 同步與非同步混雜 | `async def` + 把同步的部分包進 `asyncio.to_thread` |
| CPU 密集（超過幾十毫秒的運算） | 兩個都不對，見下一節 |

第四種情況的寫法：

```python
import asyncio

@app.post("/documents")
async def create_document(payload: DocIn, http: HttpClient):
    meta = await http.get(payload.source_url)              # 非同步 I/O
    text = await asyncio.to_thread(parse_pdf, meta.content)  # 同步函式丟去 threadpool
    return {"chars": len(text)}
```

`asyncio.to_thread`（Python 3.9+）是在 async 程式碼裡呼叫同步函式的標準做法。Starlette 也提供 `run_in_threadpool`，兩者效果相同，前者是標準庫的所以優先。

**不要因為「大部分是 async」就把那一個同步呼叫留在 loop 上。** 一行 `requests.get()` 就足以毀掉整支函式的非同步性質。

---

## 六、CPU 密集的工作

純運算（大量資料轉換、影像處理、加解密、產生 PDF、跑模型推論）兩條路都不該走：

- 放在 `async def` 裡 → 卡住 event loop，全服務停擺
- 放在 `def` 裡（threadpool）→ 因為 GIL，多條執行緒無法真正並行運算，只會互相搶鎖，反而更慢

正確的做法是**離開這個程序**。三個層次：

**一、`ProcessPoolExecutor`**——同機多程序，繞過 GIL：

```python
from concurrent.futures import ProcessPoolExecutor

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = ProcessPoolExecutor(max_workers=4)
    yield
    app.state.pool.shutdown()

@app.post("/render")
async def render(payload: RenderIn, request: Request):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(request.app.state.pool, heavy_render, payload.data)
    return {"result": result}
```

注意參數與回傳值必須可 pickle（跨程序要序列化），而且每次呼叫都有序列化成本。適合「幾百毫秒到幾秒、量不大」的工作。

**二、任務佇列**（Celery、arq、Dramatiq、RQ）——API 只負責收件與回 job id，實際運算在另一組 worker 程序：

```python
@app.post("/reports", status_code=202)
async def request_report(payload: ReportIn):
    job_id = await queue.enqueue("build_report", payload.model_dump())
    return {"job_id": job_id, "status_url": f"/reports/{job_id}"}
```

這是超過幾秒的工作的標準答案。好處是 API 的延遲與 worker 的負載脫鉤、worker 可以獨立擴縮、失敗可以重試。代價是要多一個 Redis 或訊息佇列，以及一套查詢狀態的介面。

**三、根本不要在 Python 裡做**——交給資料庫（聚合查詢下推）、交給專門的服務、或用有 C 擴充的函式庫（NumPy、Pillow、`pydantic-core`）。這些函式庫在做重運算時**會釋放 GIL**，所以放在 threadpool 裡其實是有效的並行——這是 `def` + threadpool 唯一適合 CPU 工作的例外。

判斷界線：**超過 100 毫秒的純運算就該考慮搬出去；超過 1 秒的一定要搬。**

---

## 七、寫對的 async 長什麼樣

### 用非同步的 client 與驅動

```python
# ✗ 阻塞
import requests

@app.get("/proxy")
async def proxy():
    return requests.get("https://api.example.com/data").json()

# ✓ 非同步
@app.get("/proxy")
async def proxy(http: HttpClient):       # 從 lifespan 拿的 httpx.AsyncClient
    resp = await http.get("https://api.example.com/data")
    return resp.json()
```

`HttpClient` 這個依賴的來源見上一章——client 要建在 `lifespan` 裡共用，不是每個請求 new 一個。

### 真正的並行：`asyncio.gather`

async 最大的價值在這裡。三個互不相依的外部呼叫，循序做要 300 毫秒，並行只要 100：

```python
@app.get("/dashboard")
async def dashboard(http: HttpClient):
    orders, users, alerts = await asyncio.gather(
        http.get("/orders/summary"),
        http.get("/users/active"),
        http.get("/alerts/open"),
    )
    return {"orders": orders.json(), "users": users.json(), "alerts": alerts.json()}
```

這對應 .NET 的 `Task.WhenAll`。要注意 `gather` 預設在任一個失敗時會把例外往外拋，但**其他任務仍在背景繼續執行**；需要「一個失敗就全部取消」的語意，用 `asyncio.TaskGroup`（Python 3.11+）：

```python
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(fetch_orders())
    t2 = tg.create_task(fetch_users())
# 離開 with 時全部完成；任一個失敗，其餘會被取消
```

### 逾時是必要的，不是可選的

沒有逾時的外部呼叫，會在對方變慢的時候把你的連線與執行緒全部佔住，變成級聯故障：

```python
# client 層級（建議，一次設好）
httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0))

# 呼叫層級
async with asyncio.timeout(3):          # Python 3.11+
    result = await slow_operation()
```

httpx 預設逾時是 5 秒（比 `requests` 的「無限等待」好很多），但仍應該依情境明確設定。這件事和 .NET 那邊 `HttpClient` 預設 100 秒逾時造成級聯故障是同一類問題。

---

## 八、三個容易寫錯的地方

### 忘記 `await`

```python
@app.get("/items")
async def list_items(db: AsyncSession):
    result = db.execute(select(Item))    # ← 忘了 await
    return result.scalars().all()        # AttributeError 或更怪的錯
```

漏掉 `await` 得到的是一個**協程物件**，它根本沒有開始執行。Python 只會在垃圾回收時印一行 `RuntimeWarning: coroutine ... was never awaited`，而這行警告在正式環境的 log 裡幾乎不會有人注意到。

防禦方式是開啟型別檢查（mypy / Pyright 抓得到），以及在開發環境把 asyncio 的偵錯模式打開（`PYTHONASYNCIODEBUG=1`）。

### 在 async 裡不小心用了同步 library

最常見的是隨手 `import requests`，或用了某個內部共用模組而它裡面是同步的。**依賴鏈上任何一層有同步 I/O，整條路徑就是同步的。**

程式碼審查時值得養成一個習慣：看到 `async def`，就把函式體裡每一個呼叫都問一次「這個會等嗎、有沒有 `await`」。

### 在 async 裡持有同步的鎖或全域狀態

```python
_counter = 0

@app.post("/count")
async def count():
    global _counter
    _counter += 1        # 在單一 event loop 內其實是安全的（沒有 await 就不會被切換）
    return _counter      # 但多 worker 之後這個數字沒有意義
```

單執行緒 event loop 有一個附帶好處：兩個 `await` 之間的程式碼不會被打斷，所以不需要鎖。但這個保證只在**同一個 event loop 內**成立——一旦 `--workers 4`，就有四個獨立的程序、四個獨立的 `_counter`。

任何跨請求的狀態都必須放在程序外（Redis、資料庫）。這件事在第 11 章會展開，它也是 K8s 環境下「本機好好的、上叢集就不對」的常見成因。

---

## 九、這一章的邊界

前面講的全部是**單一 worker 程序內部**的事。實際部署時會有多個 worker（`uvicorn --workers 4`）或多個 Pod 副本，那是另一個維度的並發：

```text
Pod A ── worker 1 ── event loop + threadpool
      └─ worker 2 ── event loop + threadpool
Pod B ── worker 1 ── event loop + threadpool
      └─ worker 2 ── event loop + threadpool
```

每個 worker 都是完整獨立的一份，記憶體不共用。worker 數量怎麼算、資料庫連線池要乘以幾、K8s 的 CPU limit 如何影響這個計算——第 11 章。

---

## 十、常見誤解

**「`async def` 比較快。」**
對單一請求沒有任何加速效果，反而多一點協程排程開銷。它提升的是**高 I/O 等待下的並發能力**——在等待期間讓出執行緒去處理別的請求。純運算的 endpoint 改成 async 只會變慢，還可能卡住整台服務。

**「`def` 是舊寫法，應該全部改成 `async def`。」**
完全相反。用同步函式庫（同步 SQLAlchemy、`requests`、傳統 SDK）時，`def` 是**正確且安全**的選擇，FastAPI 會把它隔離到 threadpool。錯的是「寫了 `async def` 但函式體是同步的」——那是最糟的組合。

**「服務卡住是因為請求量太大。」**
先看是哪一種卡法。全部端點（包含純 async 的 `/health`）一起停止回應，是 event loop 被阻塞，量再小也會發生——一個請求就夠了。只有部分端點變慢而 async 端點正常，才是 threadpool 或下游容量問題。

**「加執行緒就能解決。」**
threadpool 上限調高只在「同步 I/O 併發數略微超標」時有效，而且要配合資料庫連線池一起放大。對 CPU 密集工作完全無效——GIL 讓多執行緒無法真正並行運算。

**「單執行緒 event loop 不需要考慮競態條件。」**
兩個 `await` **之間**的程式碼確實不會被打斷，所以單一 loop 內的簡單讀改寫是安全的。但跨越 `await` 的邏輯就可能被交錯執行，而且多 worker 之後任何程序內狀態都會分裂。

---

## 十一、同事會來問你的問題

**「這支 endpoint 該寫 `def` 還是 `async def`？」**
看函式體裡有沒有同步 I/O。全部是 `await` 的非同步呼叫就用 `async def`；只要有一個同步阻塞（同步 ORM、`requests`、讀大檔）就用 `def`，FastAPI 會把它丟到 threadpool 隔離。混合的話用 `async def` 加 `asyncio.to_thread` 包住同步那段。

**「為什麼我打了一支慢的 API，連 `/health` 都超時？」**
那支慢的 endpoint 是 `async def` 但裡面有同步阻塞呼叫。event loop 是單執行緒的，被卡住的期間整個程序不處理任何請求。把它改成 `def`（或把阻塞呼叫改成非同步版本）就好了。

**「threadpool 40 條夠嗎？要不要調高？」**
先確認是不是真的撞到上限——症狀是 `def` 端點排隊但 `async def` 端點正常。真的撞到，調高之前要先確認資料庫連線池大小跟得上，否則只是換個地方排隊。更根本的方向是換 async 驅動、加 worker 程序、或把慢工作移出請求路徑。

**「一個要跑 30 秒的報表要怎麼做？」**
不要在請求裡做。丟任務佇列（Celery/arq），API 回 202 加一個 job id，另外提供查詢狀態的端點。`BackgroundTasks` 不適合——它在同一個程序內執行，程序被砍任務就消失，而且 30 秒的 CPU 工作照樣會影響這個 worker。

**「為什麼 CPU 密集的東西放 threadpool 沒有變快？」**
GIL：同一時間只有一條執行緒能執行 Python bytecode，多開執行緒只是輪流拿鎖。要真正並行運算得用多程序（`ProcessPoolExecutor`）或外部 worker。例外是 NumPy、Pillow 這類 C 擴充函式庫，它們在重運算時會釋放 GIL，放 threadpool 是有效的。

**「`asyncio.gather` 和 `TaskGroup` 選哪個？」**
需要「任一失敗就取消其餘」的語意用 `TaskGroup`（3.11+），它是目前建議的預設。`gather` 在其中一個丟例外時會把例外拋出，但其他任務仍在背景跑完，容易留下沒人處理的結果或洩漏的資源。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[03-dependency-injection]] — 上一章：`Depends` 與生命週期
- [[05-database-sqlalchemy]] — 下一章：同步與非同步 ORM 的取捨
- [[11-deployment]] — worker 數量與連線池的計算
- [[06-async-and-threading]] — ASP.NET Core 的對應章節（ThreadPool 飢餓）
