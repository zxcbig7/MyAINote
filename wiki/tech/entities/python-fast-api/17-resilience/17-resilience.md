---
type: concept
domain: tech
tags: [python, fastapi, resilience, timeout, retry, circuit-breaker, cache, rate-limit, httpx, tenacity]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 17 章：韌性 — 下游只是變慢，你的服務卻死了

## 沒有人掛掉，但全部都停了

某天下午，訂單服務開始大量回 503。查監控：

- CPU 15%，記憶體正常
- 資料庫沒有慢查詢
- 依賴的金流 API **沒有掛**，只是回應時間從 200ms 變成 2 秒

就這樣。下游沒有故障，只是慢了十倍。而你的服務全面停止服務。

原因用第 04 章的數字算一次就懂了。假設那支呼叫金流的 endpoint 寫成 `def`（同步的 `httpx`），它會佔用 threadpool 的一個名額：

```text
正常：threadpool 40 條 ÷ 0.2 秒 = 200 req/s 的處理能力
變慢：threadpool 40 條 ÷ 2.0 秒 =  20 req/s
```

流量沒變，處理能力掉到十分之一，其餘請求全部排隊——**而且排的是那個 40 條的池子，所以連完全不碰金流的 endpoint 也一起被卡住**。

這就是**級聯故障**：一個下游的效能退化，透過共用的資源池，變成整個服務的可用性事故。

關鍵認知是：

> **下游「變慢」比「掛掉」危險。** 掛掉是快速失敗，你的資源立刻釋放；變慢是把你的資源一個一個佔住，直到耗盡。

這一章講五個工具——逾時、重試、斷路器、快取、限流——以及一個比它們都重要的原則：**量測優先於猜測**。

（這一章補上第 05 章提到「快速失敗加上重試策略」卻沒有展開的部分。）

---

## 一、逾時：唯一一個沒有它就全盤皆輸的設定

其他四個工具都是可選的。逾時不是。

### httpx 的四個維度

```python
import httpx

timeout = httpx.Timeout(
    connect=2.0,      # 建立 TCP 連線
    read=5.0,         # 等對方送出下一段資料
    write=5.0,        # 送出請求
    pool=1.0,         # 等一條可用的連線（連線池滿的時候）
)
client = httpx.AsyncClient(timeout=timeout, limits=httpx.Limits(max_connections=50))
```

`httpx` 的預設是全部 5 秒——這比 `requests`（**預設無限等待**）和 .NET 的 `HttpClient`（預設 100 秒）都好，但仍然應該依情境明確設定。

四個維度裡 **`connect` 要設得比 `read` 短很多**。連不上通常是對方掛了或網路不通，等兩秒就夠了；`read` 則要容忍對方正常但比較慢的處理。

`pool` 常被忘記：連線池滿的時候，你會停在「等一條連線」這一步。這個等待預設也是 5 秒，加上 `read` 的 5 秒，實際最壞情況是 10 秒——**逾時是會疊加的**。

### 包住整體

單一呼叫的逾時擋不住「重試三次，每次五秒」這種累加：

```python
import asyncio

async with asyncio.timeout(8):          # Python 3.11+，整段的硬上限
    result = await call_with_retry()
```

**規則：你的總逾時必須小於呼叫端給你的逾時。** 前端等 10 秒，你就不能花 15 秒去重試——那 15 秒的工作沒有任何人在等結果，純粹是白白佔住資源。

### 資料庫那一側

第 05 章的 `pool_timeout=10` 是同一件事的另一個面向。三個數字要一起看：

```text
threadpool 名額  ← 被 HTTP 呼叫佔住
連線池          ← 被 DB 查詢佔住
pool_timeout    ← 等不到連線多久放棄
```

任何一個沒設上限，就有一條路徑可以把資源耗到底。

---

## 二、重試：三條紀律，缺一條都會變成攻擊

```powershell
pip install tenacity
```

```python
from tenacity import (
    retry, stop_after_attempt, wait_exponential_jitter,
    retry_if_exception_type, before_sleep_log,
)
import httpx, logging

logger = logging.getLogger(__name__)

RETRIABLE = (httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.2, max=3.0),
    retry=retry_if_exception_type(RETRIABLE),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def fetch_payment_status(http: httpx.AsyncClient, order_id: int) -> dict:
    resp = await http.get(f"/payments/{order_id}")
    if resp.status_code >= 500 or resp.status_code == 429:
        resp.raise_for_status()          # 讓它變成可重試的例外
    resp.raise_for_status()
    return resp.json()
```

### 紀律一：只重試冪等的操作

`GET` 重試安全。`POST /payments` 重試可能**扣兩次款**。

不冪等但必須重試的操作，要先讓它冪等——帶一個由呼叫端決定的冪等鍵（見 [[16-background-work]]）。沒有冪等鍵就不要重試寫入操作，寧可回 503 讓上游決定。

### 紀律二：只重試暫時性錯誤

| 重試 | 不要重試 |
| --- | --- |
| 連線失敗、逾時 | 400、401、403、404、422 |
| 503、504 | 任何 4xx（除了 429） |
| 429（要看 `Retry-After`） | 業務邏輯錯誤 |

重試 4xx 是純粹的浪費——請求本身有問題，再送一百次還是一樣。而重試 400 的程式碼會讓你在排查時完全看不懂：明明是參數錯誤，log 裡卻有三次相同的失敗。

### 紀律三：指數退避 **加上抖動**

```text
沒有抖動：所有客戶端都在 0.2s、0.4s、0.8s 重試
        → 下游剛喘過氣就被同一批請求同時打死
        → 這叫重試風暴（thundering herd）

有抖動：  每個客戶端的等待時間隨機分散
```

`wait_exponential_jitter` 幫你做掉這件事。**沒有抖動的重試不是韌性機制，是一次同步化的 DDoS。**

### 重試預算

三次重試在最壞情況會花掉：

```text
0.2 + 0.4 + 0.8（等待） + 3 × 5（每次 read timeout） ≈ 16.4 秒
```

如果上游只等 10 秒，這個設定完全沒有意義——最後那幾次重試是在對一個沒人等待的結果做無用功，同時佔著你的 threadpool 名額。所以重試次數與逾時**必須一起算**，並用 `asyncio.timeout` 加一個硬上限。

**重試會放大負載。** 下游已經在過載時，你的重試讓它收到三倍的請求。這正是下一節的存在理由。

---

## 三、斷路器：知道什麼時候該停手

重試處理的是「偶發抖動」。下游**真的掛了**的時候，重試只是加壓，而且每一次嘗試都在浪費你自己的資源。

斷路器的邏輯是：連續失敗到一定次數就**直接拒絕後續呼叫**，過一段時間再放一個請求試水溫。

```text
CLOSED（正常）──連續失敗 N 次──▶ OPEN（拒絕，不實際呼叫）
   ▲                                   │
   │                              等待 reset_timeout
   │                                   ▼
   └────試探成功────── HALF_OPEN（只放行少數請求）
                            │
                       試探失敗 → 回到 OPEN
```

```powershell
pip install purgatory-circuitbreaker    # async 原生；同步專案可用 pybreaker
```

```python
from purgatory import AsyncCircuitBreakerFactory

breakers = AsyncCircuitBreakerFactory(default_threshold=5, default_ttl=30)

async def fetch_payment(http, order_id: int) -> dict:
    async with await breakers.get_breaker("payment-api"):
        resp = await http.get(f"/payments/{order_id}", timeout=5.0)
        resp.raise_for_status()
        return resp.json()
```

三個實務要點：

**OPEN 狀態要回 503 不是 500。** 這是「暫時不可用、稍後再試」，不是「我有 bug」。附上 `Retry-After`（見第 06 章的狀態碼決策表）。

**每個下游一個斷路器。** 金流掛掉不該讓寄信也被拒絕。用下游名稱當 key。

**多副本下狀態不共用。** 每個 Pod 各有一份計數，所以「連續五次失敗」是以單一 Pod 為單位。這和 .NET 的 Polly 一樣，通常可以接受——真正的下游故障每個 Pod 都會遇到。要共用狀態就得放 Redis，複雜度不一定值得。

### 搭配降級

斷路器打開時，最好不要只是回錯誤：

```python
async def get_shipping_eta(http, order_id: int) -> str:
    try:
        return (await fetch_eta(http, order_id))["eta"]
    except CircuitBreakerError:
        return "暫時無法取得，請稍後查詢"      # 降級：頁面其他部分照常
```

**部分功能失效遠比整頁 500 好。** 這是韌性設計的核心取捨——先想清楚「這個下游掛了，我能不能還做點什麼」。

---

## 四、快取：最有效但最容易做錯的一個

### 三層

| 層 | 工具 | 範圍 | 適合 |
| --- | --- | --- | --- |
| 程序內 | `cachetools.TTLCache` | **單一 Pod** | 設定、少量熱資料 |
| 分散式 | Redis | 全叢集共用 | 查詢結果、session |
| HTTP | `Cache-Control` / ETag | 客戶端與 CDN | 靜態或半靜態回應 |

### 程序內快取的兩個坑

```python
from cachetools import TTLCache, cached
from threading import Lock

_cache = TTLCache(maxsize=1000, ttl=300)
_lock = Lock()

@cached(_cache, lock=_lock)          # ← lock 不能省
def get_exchange_rate(currency: str) -> Decimal:
    ...
```

**坑一：`cachetools` 不是執行緒安全的。** `def` 的 endpoint 跑在 threadpool，多條執行緒會同時碰這個 dict。不加 `lock` 的話在高併發下會出現詭異的 `KeyError` 或髒資料。

**坑二：每個 Pod 一份。** 四個副本就是四份快取、四種可能不一致的值，而且「清快取」需要重啟全部 Pod。所以程序內快取只適合**變動極慢且不一致無傷**的資料。

### 快取雪崩（stampede）

一個熱門 key 過期的瞬間，所有進行中的請求同時發現快取沒了，**全部一起打向資料庫**。原本一秒一次的查詢瞬間變成一千次。

三個解法：

**一、TTL 加抖動**——最簡單，先做這個：

```python
ttl = 300 + random.randint(0, 60)      # 讓大量 key 不會同時過期
```

**二、single-flight**——同一個 key 只讓一個請求去重算，其餘等它：

```python
_inflight: dict[str, asyncio.Future] = {}

async def get_or_compute(key: str, compute):
    if (fut := _inflight.get(key)) is not None:
        return await fut                      # 別人正在算，等它
    fut = asyncio.get_running_loop().create_future()
    _inflight[key] = fut
    try:
        value = await compute()
        fut.set_result(value)
        return value
    except Exception as exc:
        fut.set_exception(exc)
        raise
    finally:
        _inflight.pop(key, None)
```

**三、提前刷新**——快取還沒過期時就在背景更新，永遠不讓它真的空掉。最順暢但最複雜。

### 什麼不該快取

- **會影響授權判斷的資料**（使用者權限、租戶歸屬）——快取讓「撤銷權限」延遲生效
- **寫入後要立刻讀到的東西**——那是一致性需求不是效能需求
- **命中率低的查詢**——每次都 miss 只是多了一次 Redis round trip

---

## 五、限流：保護自己，不是保護對方

限流的目的常被誤解。它不是「防止別人用太多」，而是**確保過載時你還能服務一部分請求，而不是全部一起爛掉**。

沒有限流的系統在過載時的行為是：所有請求都變慢 → 全部逾時 → 沒有人拿到結果 → 而你的資源全部浪費在那些沒人要的結果上。有限流的話是：一部分請求被快速拒絕（429），其餘正常完成。

### 該放在哪一層

| 層 | 工具 | 說明 |
| --- | --- | --- |
| **Ingress** | `nginx.ingress.kubernetes.io/limit-rps` | **優先選這裡**——請求還沒進到你的程序就被擋掉 |
| 應用 | `slowapi` | 需要依使用者/方案做細緻規則時 |
| 下游呼叫端 | 訊號量 | 限制自己對某個下游的並行數 |

第一層通常就夠了，而且成本最低（見 [[28-ingress-nginx-annotations]]）。應用層限流的價值在於它知道「這個請求是誰、屬於哪個方案」——這是 Ingress 做不到的。

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/reports")
@limiter.limit("5/minute")
async def request_report(request: Request, ...):
    ...
```

用 `slowapi` 時記得 `key_func` 在反向代理後面要取真實 IP——這需要 `--proxy-headers`（見 [[08-middleware-and-cross-cutting]]），否則所有請求看起來都來自同一個 Ingress IP，限流會誤傷全部人。

**回應要附 `Retry-After`。** 沒有它，客戶端只能猜什麼時候能重試，多半會立刻再打一次。

### 第三層：限制自己的並行數

```python
_payment_sem = asyncio.Semaphore(10)      # 同時最多 10 個呼叫金流

async def call_payment(http, ...):
    async with _payment_sem:
        return await http.post("/charge", ...)
```

這一層很少人做，但它直接解決了開篇那個問題——就算金流變慢，最多只有 10 個名額被佔住，其餘 30 條 threadpool 還能服務別的請求。**用一個訊號量把「共用資源池」切開，是最便宜的隔艙（bulkhead）實作。**

---

## 六、量測優先於猜測

前面五個工具都有參數要調，而**沒有數據就調參數是在做迷信**。

上線前至少要能回答這幾個問題：

| 問題 | 從哪裡看 |
| --- | --- |
| 每支 endpoint 的 p50 / p95 / p99 | access log（第 08 章那支 middleware） |
| 哪個下游最慢、佔多少時間 | 呼叫前後的耗時 log |
| threadpool 用掉幾個名額 | `anyio` 的 limiter，或用「`/health/live` 是否變慢」推斷 |
| 連線池等了多久 | SQLAlchemy 的 pool 事件 |
| 錯誤率與狀態碼分布 | access log 的 `status` 欄位 |

一個實用的最小實作——把下游呼叫的耗時記下來：

```python
import time

async def timed_call(name: str, coro):
    start = time.perf_counter()
    try:
        return await coro
    finally:
        logger.info(
            "downstream call",
            extra={"downstream": name, "duration_ms": round((time.perf_counter() - start) * 1000, 1)},
        )
```

有了這個，開篇那個事故的診斷會從「查了三小時」變成「看一眼 Kibana」——`downstream=payment` 的 p95 從 200 跳到 2000，一目了然。

**調參數的順序**也很重要：先設逾時（沒有它其他都沒意義），再加隔艙訊號量（成本最低、效果最直接），然後才是重試與斷路器，最後才考慮快取。反過來做——先加快取——常常只是把問題藏起來。

---

## 七、常見誤解

**「下游掛掉才是問題，變慢還好。」**
反了。掛掉是快速失敗，資源立刻釋放；變慢會把你的 threadpool 名額或連線一個一個佔住，直到整個服務停止回應——包括完全不碰那個下游的 endpoint。

**「`httpx` 有預設逾時，不用另外設。」**
預設 5 秒是比 `requests` 的無限等待好，但四個維度（connect/read/write/pool）該分開設，而且**逾時會疊加**——等連線 5 秒加讀取 5 秒就是 10 秒。還要用 `asyncio.timeout` 包一個整體上限。

**「加重試比較保險。」**
不冪等的操作重試會重複扣款；重試 4xx 是純浪費；沒有抖動的重試會在下游剛恢復時同時打過去。三條紀律缺一條，重試就從韌性機制變成攻擊。

**「重試三次很合理。」**
要看總時間。三次重試加上每次五秒逾時是十六秒——如果上游只等十秒，後面那些重試是在對沒人要的結果做工，同時佔著你的資源。重試次數與逾時必須一起算。

**「快取加下去效能就好了。」**
先確認命中率。命中率低的快取只是多一次 round trip。而且熱門 key 過期瞬間會有雪崩，TTL 至少要加抖動。授權相關的資料更不該快取——那會讓撤權延遲生效。

**「限流是為了防止別人濫用。」**
主要是為了保護自己：過載時讓一部分請求快速失敗，好過全部逾時而沒有人拿到結果。而且它該優先放在 Ingress，請求根本不用進到你的程序。

**「斷路器的狀態應該全叢集共用。」**
通常不需要。真正的下游故障每個 Pod 都會遇到，各自計數就夠了。放 Redis 共用會多一個依賴、多一次 round trip，還讓 Redis 變成新的單點。

---

## 八、同事會來問你的問題

**「金流變慢，為什麼連 `/health` 都受影響？」**
因為它們共用同一個資源池。`def` 的 endpoint 佔 threadpool 名額，`async def` 佔 event loop——下游從 200ms 變 2s，你的處理能力就掉到十分之一，其餘請求全部排隊。解法有兩層：逾時讓它快速失敗，訊號量把那個下游的並行數限制住（隔艙），不讓它吃光整個池子。

**「逾時要設多少？」**
看 p95 再乘一個係數，不要拍腦袋。`connect` 設短（2 秒，連不上就是連不上），`read` 容忍正常的慢。然後檢查兩件事：四個維度會疊加、以及你的總時間（含重試）必須小於上游給你的逾時。

**「這個呼叫可以重試嗎？」**
三個問題。一，操作冪等嗎（不冪等就先加冪等鍵，否則寧可不重試）？二，這個錯誤是暫時的嗎（4xx 除了 429 一律不重試）？三，退避有加抖動嗎（沒有的話所有客戶端會同步重試，把剛恢復的下游再打死）？

**「重試和斷路器差在哪，要兩個都用嗎？」**
重試處理偶發抖動，斷路器處理持續故障。下游真的掛了的時候重試只是加壓，斷路器讓你直接停手不浪費資源。兩個要一起用，而且斷路器要包在重試外面——不然三次重試會被算成三次失敗，斷路器一下就開了。

**「快取加了怎麼還是慢？」**
先看命中率。命中率低的話快取只是多一次 round trip。其次看是不是雪崩——熱門 key 同時過期，全部打向資料庫。TTL 加抖動是最便宜的解法，需要更強保證就做 single-flight。

**「限流放應用層還是 Ingress？」**
優先 Ingress，請求還沒進到你的程序就被擋掉，成本最低。應用層限流的價值在於它知道請求屬於哪個使用者或方案——需要這種細緻規則時才加，而且反向代理後面要記得開 `--proxy-headers`，否則所有人看起來都是同一個 IP。

**「要先做哪一個？」**
逾時，而且是全部的逾時（HTTP 四維度、`asyncio.timeout` 整體、DB 的 `pool_timeout`）。沒有逾時，其他四個工具都沒有意義。接著是隔艙訊號量——成本最低、直接解決共用資源池被吃光的問題。重試與斷路器排第三，快取最後，因為快取常常只是把問題藏起來。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[04-async-and-concurrency]] — threadpool 40 條這個數字的來源
- [[05-database-sqlalchemy]] — 連線池與 `pool_timeout`
- [[06-error-handling]] — 503 vs 500 的告警語意
- [[08-middleware-and-cross-cutting]] — access log 與 `--proxy-headers`
- [[16-background-work]] — 冪等鍵讓寫入操作可以安全重試
- [[18-resilience-and-performance]] — ASP.NET Core 的對應章節（`HttpClient` 與 Polly）
- [[28-ingress-nginx-annotations]] — Ingress 層限流的設定
