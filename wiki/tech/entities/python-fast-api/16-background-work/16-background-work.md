---
type: concept
domain: tech
tags: [python, fastapi, background-work, celery, arq, cronjob, idempotency, outbox, distributed-lock]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 16 章：背景工作與排程 — 三個副本，對帳跑了三次

## 一筆帳對了三遍

需求很單純：每天凌晨兩點跑一次對帳，把前一天的訂單和金流平台的紀錄比對，差異寄信給財務。

實作也很單純——在應用裡裝一個 `APScheduler`，`lifespan` 啟動時排程：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reconcile, "cron", hour=2)
    scheduler.start()
    yield
    scheduler.shutdown()
```

測試環境跑了兩週完全正常。上正式環境之後，財務收到三封內容相同的信。

因為正式環境是 `replicas: 3`。**三個 Pod 各自跑了一次。**

這還算好的——那次只是重複寄信。如果那個排程是「補寄未付款提醒」，客戶會收到三封；如果是「重試失敗的扣款」，那就是重複扣款。

根因是一個從單機時代帶過來的假設：**「這段程式碼只會有一份在跑」**。這個假設在容器編排的世界裡從一開始就不成立，而且**它不會有任何錯誤訊息**——每個 Pod 都覺得自己做得很對。

這一章處理三件事：背景工作的四種做法各自的邊界在哪、多副本重複執行怎麼解、以及為什麼「冪等性」才是這整個主題真正的核心。

（這一章補上第 03、04 章多次提到「要進佇列」卻沒有展開的部分。）

---

## 一、四種做法，四種邊界

| 做法 | 執行位置 | 程序被砍會怎樣 | 多副本 | 適合 |
| --- | --- | --- | --- | --- |
| `BackgroundTasks` | **同程序**，回應送出後 | **任務消失** | 不會重複（跟著請求） | 可以掉的小事 |
| `lifespan` + `create_task` | 同程序，常駐 | 任務消失 | **會重複** | 幾乎都不該用 |
| 外部佇列（arq / Celery） | 獨立 worker 程序 | 任務留在佇列，會重試 | 不會重複（佇列分派） | 不能掉的工作 |
| K8s CronJob | 獨立 Pod | K8s 依設定重試 | 不會重複（K8s 保證單一） | **定時任務** |

對照 ASP.NET Core：那邊的 `BackgroundService` / `IHostedService` 是框架一級公民，加上 Hangfire 就有了持久化與重試。FastAPI 這邊**沒有任何一級支援**——`BackgroundTasks` 只是「回應送出後在同程序執行一個函式」，其餘都要靠外部元件。

選擇規則可以濃縮成一句：

> **這件事掉了會怎樣？** 沒差 → `BackgroundTasks`。有差 → 佇列或 CronJob。

---

## 二、`BackgroundTasks` 能做什麼

```python
from fastapi import BackgroundTasks

def write_audit(user_id: int, action: str) -> None:
    with SessionLocal() as db:                 # 自己開 session
        db.add(AuditLog(user_id=user_id, action=action))
        db.commit()

@router.post("/orders", status_code=201, response_model=OrderOut)
def create_order(payload: OrderCreate, user: CurrentUser, db: DbSession, bg: BackgroundTasks):
    order = order_service.create(db, payload, user)
    bg.add_task(write_audit, user.id, "order.created")
    return order
```

三個限制要記牢：

**一、它在同一個程序內執行。** Pod 被砍、滾動更新、OOMKilled——任務直接消失，沒有任何紀錄說它沒做完。

**二、沒有重試、沒有持久化。** 函式丟例外就是丟例外，不會有第二次機會。

**三、它會佔用這個 worker 的資源。** `def` 的任務跑在 threadpool（吃掉你僅有的名額），`async def` 的任務跑在 event loop（一次同步阻塞就卡住整個程序）。**耗時的東西放進來等於把慢請求的成本轉嫁到其他請求身上。**

還有一個第 03 章講過的坑：**不要把 `yield` dependency 給的 session 傳進去**。`yield` 之後的收尾在回應送出前就執行了，任務啟動時 session 早就 close。上面的範例用 `with SessionLocal() as db:` 自己開，就是這個原因。

適合它的工作只有一類：**可以掉、快、且失敗不需要有人知道**。寄一封通知信、寫一筆稽核記錄、清一個快取。除此之外都該往下看。

---

## 三、程序內常駐任務：幾乎都不該用

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_queue())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
```

這是 `BackgroundService` 最直接的對應，但它有兩個問題，其中一個很陰險。

### 陰險的那個：例外會被靜默吞掉

```python
async def poll_queue():
    while True:
        await process_one()        # 這裡丟例外的話…
        await asyncio.sleep(5)
```

`asyncio.Task` 裡的例外**不會傳播到任何地方**。任務直接停止，程式繼續跑，沒有 log、沒有告警、健康檢查也是綠的。你只會在幾天後發現「那個東西好像從上週就沒在動了」。

（Python 會在 task 物件被垃圾回收時印一行 `Task exception was never retrieved`，但如果你持有 task 的參考——像上面那樣——連這行都不會出現。）

正確寫法必須自己兜住：

```python
async def poll_queue():
    while True:
        try:
            await process_one()
        except asyncio.CancelledError:
            raise                                    # 取消要往外傳，不能吞
        except Exception:
            logger.exception("poll_queue 迭代失敗")   # 記錄後繼續，不讓整個迴圈死掉
        await asyncio.sleep(5)
```

`except Exception` 要放在 `except asyncio.CancelledError` **後面**——`CancelledError` 在 Python 3.8+ 繼承自 `BaseException` 而不是 `Exception`，所以其實不會被 `except Exception` 抓到，但明確寫出來讓意圖清楚，也避免有人改成 `except BaseException`。

對照 .NET：那邊 `BackgroundService` 的未處理例外會**停掉整個 Host**（.NET 6 起的預設），至少你會立刻知道。Python 這邊是靜默死亡，更難發現。

### 另一個問題：多副本會重複

這就是開篇那個事故。三個 Pod 各有一份常駐任務。

**結論**：需要常駐輪詢時，把它做成獨立的 Deployment（`replicas: 1`）而不是塞進 API 服務裡。需要定時執行時用 CronJob。塞進 API 程序裡幾乎沒有好處，卻同時繼承了「會重複」和「會靜默死掉」兩個問題。

---

## 四、多副本重複執行：三個解法

### 解法一：K8s CronJob（定時任務的預設答案）

把排程從應用裡搬出來，交給 K8s：

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: myapi-reconcile
spec:
  schedule: "0 2 * * *"
  timeZone: "Asia/Taipei"          # 沒設會用 UTC，凌晨兩點變成早上十點
  concurrencyPolicy: Forbid        # 上一次還沒跑完就跳過這次
  startingDeadlineSeconds: 300
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 86400
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: reconcile
              image: harbor.example.com/myapi:1.4.0    # 和 API 同一個映像
              command: ["python", "-m", "app.jobs.reconcile"]
              envFrom:
                - configMapRef: { name: myapi-config }
```

```python
# app/jobs/reconcile.py
import logging
from app.core.logging import setup_logging
from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

def main() -> None:
    setup_logging(settings.log_level)
    with SessionLocal() as db:
        diffs = reconcile_yesterday(db)
        db.commit()
    logger.info("對帳完成", extra={"diff_count": len(diffs)})

if __name__ == "__main__":
    main()
```

**用同一個映像**，只是換一個 entrypoint。這樣業務邏輯、model、設定全部共用，不會出現「排程用的那份程式碼忘了跟上」。

CronJob 各欄位的完整推導在 [[practice-4-write-yaml-from-scratch]]（那邊剛好也是用對帳當例子），這裡只強調兩個最常錯的：**`timeZone` 不設就是 UTC**（台灣會差八小時），以及 **`concurrencyPolicy: Forbid`**——不設的話上一次還在跑就會再起一個，對帳這種工作會直接撞在一起。

### 解法二：分散式鎖

任務必須留在應用程序內（例如它需要 API 的記憶體狀態）時，用鎖讓只有一個副本能執行：

```python
import uuid
from redis.asyncio import Redis

RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

async def with_lock(redis: Redis, key: str, ttl_ms: int = 300_000):
    token = uuid.uuid4().hex
    got = await redis.set(key, token, nx=True, px=ttl_ms)
    if not got:
        return False, None
    return True, token

async def release(redis: Redis, key: str, token: str) -> None:
    await redis.eval(RELEASE_LUA, 1, key, token)      # 只刪自己那把
```

兩個細節不能省：

**TTL 必須設。** 拿到鎖的 Pod 如果當掉，沒有 TTL 的鎖會永遠鎖著，那個任務再也不會執行。

**釋放要比對 token。** 直接 `DEL` 有一個競態：你的任務執行超過 TTL、鎖自動過期、另一個 Pod 拿到鎖，這時你跑完了去 `DEL`，就把**別人的鎖**刪掉了。用 Lua 腳本做「比對後刪除」讓這一步原子化。

也要誠實承認限制：**單一 Redis 的鎖在 Redis 故障或 failover 時不保證互斥**（Redlock 演算法有名的爭議就在這裡）。所以鎖是「減少重複」的機制，**不能取代冪等性**——這是下一節的重點。

用 PostgreSQL 的話 `pg_try_advisory_lock` 更簡單且免額外元件；Oracle 對應的是 `DBMS_LOCK`，但需要額外授權，實務上多半直接用 CronJob 繞開。

### 解法三：交給佇列

工作本來就該進佇列的話，這個問題自動消失——佇列只會把一個任務分派給一個 worker。

### 三者怎麼選

| 情境 | 選 |
| --- | --- |
| 定時執行的批次工作 | **K8s CronJob** |
| 由請求觸發的耗時工作 | **任務佇列** |
| 必須留在 API 程序內的常駐輪詢 | 獨立 Deployment `replicas: 1`，或分散式鎖 |

.NET 那邊多了一個 Hangfire 選項（把排程與重試存進資料庫）。Python 沒有等價物——最接近的是 Celery Beat，但它本身就要一整套 Celery。

---

## 五、任務佇列：arq 還是 Celery

| | arq | Celery |
| --- | --- | --- |
| 非同步 | **原生 async** | 同步為主 |
| 後端 | 只有 Redis | Redis、RabbitMQ、SQS… |
| 體積 | 小，幾百行就讀完 | 大，功能極多 |
| 生態 | 小 | 極大（監控、路由、rate limit…） |
| 適合 | **FastAPI 專案的預設選擇** | 已有 Celery 經驗、需要複雜路由 |

`arq` 是 Pydantic 作者寫的，設計上就是給 async 應用用的，和 FastAPI 的搭配最自然。**沒有特殊需求就從 arq 開始**——Celery 的功能你多半用不到，但它的複雜度你一定要付。

### API 端：入隊並立刻回應

```python
# app/main.py（lifespan）
from arq import create_pool
from arq.connections import RedisSettings

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    yield
    await app.state.arq.close()
```

```python
# app/api/routers/reports.py
@router.post("/reports", status_code=202)
async def request_report(payload: ReportIn, request: Request, user: CurrentUser):
    job = await request.app.state.arq.enqueue_job(
        "build_report", payload.model_dump(), user.id
    )
    return {"job_id": job.job_id, "status_url": f"/api/v1/reports/{job.job_id}"}

@router.get("/reports/{job_id}")
async def report_status(job_id: str, request: Request):
    from arq.jobs import Job
    job = Job(job_id, request.app.state.arq)
    return {"status": (await job.status()).value, "result": await job.result_info()}
```

**回 202 而不是 200**——語意是「收到了，還沒做完」，而且要給客戶端一個查詢進度的位址。

### Worker 端：獨立的程序

```python
# app/worker.py
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.logging import setup_logging

async def build_report(ctx, payload: dict, user_id: int) -> dict:
    with SessionLocal() as db:          # worker 自己開 session
        result = report_service.build(db, payload, user_id)
        db.commit()
    return {"rows": result.row_count}

async def startup(ctx):
    setup_logging(settings.log_level)

class WorkerSettings:
    functions = [build_report]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_tries = 3
    job_timeout = 600
```

```yaml
# 獨立的 Deployment，和 API 分開擴縮
command: ["arq", "app.worker.WorkerSettings"]
```

Worker 是**獨立的 Deployment**，用同一個映像。這帶來兩個好處：API 的延遲與 worker 的負載脫鉤，而且可以依佇列長度單獨對 worker 做 HPA。

---

## 六、冪等性：這一章真正的重點

前面所有機制都無法給你「剛好執行一次」。

- 佇列是 **at-least-once**：worker 做完了但在回報前掛掉 → 任務重新分派 → 做第二次
- CronJob 的 `Forbid` 只擋並行，不擋「同一份工作被重跑」
- 分散式鎖在 Redis failover 時可能同時給出兩把

「exactly-once」在分散式系統裡基本上不存在。所以**唯一可靠的策略是：讓重複執行不造成傷害**。

### 冪等鍵

```python
def process_payment(db: Session, order_id: int, idempotency_key: str) -> Payment:
    existing = db.scalar(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )
    if existing:
        return existing                      # 做過了，直接回上次的結果

    payment = Payment(
        order_id=order_id,
        idempotency_key=idempotency_key,     # 這個欄位有唯一索引
        amount=...,
    )
    db.add(payment)
    try:
        db.commit()
    except IntegrityError:                   # 併發下另一邊先寫進去了
        db.rollback()
        return db.scalar(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
    return payment
```

三個關鍵：

**鍵要由呼叫端決定且穩定。** `f"reconcile:{date}"`、`f"order:{order_id}:refund"`。用 `uuid4()` 當鍵是沒有意義的——每次重試都不一樣，等於沒有冪等性。

**唯一索引是保證，`if existing` 只是最佳化。** 併發下兩邊會同時通過檢查，靠 `IntegrityError` 兜住（和第 06 章「先查再寫擋不住競態」是同一條規則）。

**檢查與寫入要在同一個交易裡。** 分開的話中間那個空隙就是競態視窗。

### 天生冪等的操作

有些操作本來就重複執行無害，優先往這個方向設計：

| 不冪等 | 冪等 |
| --- | --- |
| `balance = balance - 100` | `status = 'paid'`（設定成固定值） |
| `INSERT` | `UPSERT` / `MERGE`（依唯一鍵） |
| 「寄一封信」 | 「確保這個通知已寄出」（查表再決定） |

---

## 七、Outbox：資料庫與訊息的原子性

一個看起來沒問題的寫法：

```python
def create_order(db: Session, payload: OrderCreate) -> Order:
    order = Order(...)
    db.add(order)
    db.commit()                              # ← 這裡成功了
    queue.enqueue_job("notify_shipping", order.id)   # ← 這裡如果失敗？
    return order
```

兩個系統（資料庫、佇列）之間沒有共同的交易。commit 成功但入隊失敗，訂單就永遠不會被通知；反過來先入隊再 commit，則可能通知了一張不存在的訂單。

**Outbox 模式**把訊息也寫進資料庫，讓它們共用同一個交易：

```python
def create_order(db: Session, payload: OrderCreate) -> Order:
    order = Order(...)
    db.add(order)
    db.add(OutboxMessage(                    # 同一個交易
        topic="notify_shipping",
        payload={"order_id": order.id},
    ))
    db.commit()                              # 兩者一起成功或一起失敗
    return order
```

再由一個獨立的投遞程序（CronJob 或常駐 worker）輪詢 outbox 表，把未投遞的訊息送進佇列，成功後標記：

```python
def dispatch_outbox(db: Session, arq) -> int:
    stmt = (
        select(OutboxMessage)
        .where(OutboxMessage.dispatched_at.is_(None))
        .order_by(OutboxMessage.id)
        .limit(100)
        .with_for_update(skip_locked=True)   # 多個投遞者不會搶到同一批
    )
    sent = 0
    for msg in db.scalars(stmt):
        arq.enqueue_job(msg.topic, msg.payload, _job_id=f"outbox:{msg.id}")
        msg.dispatched_at = now()
        sent += 1
    db.commit()
    return sent
```

`_job_id` 用 outbox 的 id——arq 對相同 job_id 會去重，這樣即使投遞程序在標記前掛掉、下次重送，也不會產生兩個任務。這是把冪等性做進基礎設施的例子。

`with_for_update(skip_locked=True)` 讓多個投遞者可以並行處理不同批次。Oracle 支援 `FOR UPDATE SKIP LOCKED`。

**代價**：多一張表、多一個投遞程序、訊息會有幾秒延遲。所以**只對「絕對不能掉」的訊息用它**（付款、出貨、對外通知），一般的內部事件直接入隊就好。

---

## 八、排程失敗要有人知道

這是最常被忽略的一環：**排程任務失敗時，沒有人在看**。API 出錯有使用者抱怨，凌晨兩點的對帳沒跑，可能兩週後才有人發現。

三件事要做：

**一、任務結束時記錄結構化的結果。**

```python
logger.info("job finished", extra={"job": "reconcile", "diff_count": n, "duration_ms": ms})
```

**二、對「應該發生但沒發生」告警。** 這是關鍵——監控「失敗次數」抓不到「根本沒執行」。做法是讓任務成功時更新一個時間戳（資料庫的一列，或 Prometheus 的 Pushgateway），再對「這個時間戳超過 26 小時沒更新」告警。

**三、明確知道 YAML 表達不了「失敗要通知」。** CronJob 的 `backoffLimit` 只控制重試次數，K8s 不會替你發通知。這件事一定要靠監控系統，[[practice-4-write-yaml-from-scratch]] 裡把它列為「YAML 做不到、必須靠告警」的典型例子。

---

## 九、常見誤解

**「排程放在應用裡比較方便，反正只有一個服務。」**
`replicas: 3` 就是三份。這個假設不會有任何錯誤訊息，每個 Pod 都覺得自己做得對。定時任務用 CronJob，常駐輪詢做成獨立的 `replicas: 1` Deployment。

**「`BackgroundTasks` 是 FastAPI 版的 `BackgroundService`。」**
差很遠。它只是「回應送出後在同程序執行一個函式」——沒有持久化、沒有重試、程序被砍就消失，而且會佔用這個 worker 的 threadpool 或 event loop。只適合可以掉的小事。

**「`asyncio.create_task` 的任務掛了我會知道。」**
不會。Task 裡的例外不會傳播，任務靜默停止，log 是空的、健康檢查是綠的。必須自己在迴圈裡 `try/except` 並記錄。

**「用了佇列就不會重複執行了。」**
佇列是 at-least-once。worker 做完但回報前掛掉，任務就會被重新分派。**冪等性是唯一可靠的防線**，佇列和鎖都只是降低機率。

**「冪等鍵用 UUID 產生就好。」**
每次重試都產生新 UUID 等於沒有冪等性。鍵必須由呼叫端決定且對同一件事穩定不變，例如 `order:{id}:refund`。

**「先 commit 再入隊，順序對就沒問題。」**
兩個系統之間沒有共同交易。commit 成功、入隊失敗，訊息就永遠消失了。不能掉的訊息要走 outbox。

**「CronJob 排 `0 2 * * *` 就是凌晨兩點。」**
不設 `timeZone` 的話是 UTC 的兩點，台灣時間早上十點。這個坑很常見而且很久才會被發現。

---

## 十、同事會來問你的問題

**「這個工作該用哪一種背景機制？」**
先問「掉了會怎樣」。沒差就 `BackgroundTasks`；有差就看觸發方式——定時的用 K8s CronJob，請求觸發的耗時工作用任務佇列。塞進 API 程序裡常駐幾乎沒有好處，卻同時繼承「多副本會重複」和「例外靜默吞掉」兩個問題。

**「為什麼排程跑了三次？」**
`replicas: 3`，每個 Pod 各跑一份。把排程搬到 K8s CronJob（K8s 保證單一），或把常駐任務做成獨立的 `replicas: 1` Deployment。真的必須留在 API 裡就要加分散式鎖——但鎖只降低機率，不能取代冪等性。

**「Redis 鎖怎麼寫才對？」**
`SET key token NX PX ttl` 拿鎖（**TTL 必須有**，否則持鎖的 Pod 掛掉就永遠鎖著），釋放時用 Lua 腳本比對 token 再刪（直接 `DEL` 可能刪到別人的鎖——你的任務超時、鎖過期、別人拿到了，你才跑完去刪）。而且要接受單一 Redis 在 failover 時不保證互斥。

**「arq 還是 Celery？」**
沒有特殊需求就 arq——原生 async、體積小、和 FastAPI 最搭。Celery 的功能你多半用不到，但複雜度一定要付。已經有 Celery 經驗或需要複雜路由、多種 broker 才選它。

**「怎麼確保任務不會做兩次？」**
確保不了，只能讓做兩次無害。用**呼叫端決定的穩定冪等鍵**加唯一索引，檢查與寫入在同一個交易裡，併發撞上時靠 `IntegrityError` 兜住。設計時也優先選天生冪等的操作（設定成固定值而不是遞增、UPSERT 而不是 INSERT）。

**「訂單建立了但通知沒發出去，怎麼避免？」**
資料庫和佇列之間沒有共同交易。把訊息當成一列資料寫進 outbox 表（和訂單同一個交易），再由獨立的投遞程序輪詢送進佇列。代價是多一張表和幾秒延遲，所以只對「絕對不能掉」的訊息用。

**「排程沒跑要怎麼發現？」**
監控「失敗次數」抓不到「根本沒執行」。讓任務成功時更新一個時間戳，再對「超過 N 小時沒更新」告警。K8s 的 `backoffLimit` 只管重試次數，它不會通知任何人。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[03-dependency-injection]] — `BackgroundTasks` 拿到已關閉 session 的成因
- [[04-async-and-concurrency]] — CPU 密集工作為什麼要離開這個程序
- [[06-error-handling]] — 「先查再寫擋不住競態」的同一條規則
- [[11-deployment]] — 多副本造成的狀態分裂
- [[practice-4-write-yaml-from-scratch]] — CronJob 各欄位的完整推導（同樣用對帳當例子）
- [[19-background-work]] — ASP.NET Core 的對應章節（`BackgroundService` 與 Hangfire）
