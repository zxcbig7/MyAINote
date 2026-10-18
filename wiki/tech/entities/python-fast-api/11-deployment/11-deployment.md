---
type: concept
domain: tech
tags: [python, fastapi, deployment, docker, kubernetes, uvicorn, graceful-shutdown, probe, worker]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 11 章：部署 — worker 要開幾個，以及每次上線都掉的那批 502

## 一個準時出現的錯誤

團隊每週四中午部署。每次部署後的三十秒內，前端的錯誤監控就會準時跳出一批 502，大約二三十個，然後恢復正常。

沒有人覺得這是大問題——「滾動更新嘛，難免」——直到某次部署撞上一個大客戶正在批次匯入，那批 502 裡有八十筆訂單。

「難免」是錯的。滾動更新可以做到零掉包，前提是要知道 K8s 移除一個 Pod 時，這兩件事是**同時發生**的：

```text
時間 →
kubelet:   送 SIGTERM ──→ 應用開始關閉 ──→ 程序結束
控制平面:  更新 Endpoints ──→ kube-proxy / Ingress 更新規則 ──→ 流量停止送入
                              ↑
                     這中間有幾百毫秒到幾秒的延遲
```

應用收到 SIGTERM 的那一刻就開始關閉，但**流量還在往它身上送**——因為 Ingress 還沒收到「這個 Pod 不能用了」的消息。那個空窗期送進來的請求，打到一個正在關閉的程序，就是 502。

修法只有五行 YAML（第四節），但要知道該加什麼，得先理解整條關閉路徑。

這一章是整套教材的收束。前面每一章留下的數字——threadpool 40、連線池 15、event loop 單執行緒、設定必須 fail fast——會在這裡被收攏成一組可以實際計算的部署參數，最後用一張「本機好好的、上叢集就掛」對照表結尾。

---

## 一、Dockerfile

```dockerfile
# ---------- builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 先只複製相依清單——這一層在相依沒變時可以重用
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---------- runtime ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser ./app ./app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", \
     "--timeout-graceful-shutdown", "30"]
```

六個決策值得解釋：

**先 `COPY requirements.txt` 再 `COPY ./app`。** Docker 的層快取是逐層比對的，一旦某層變了，後面全部重建。程式碼每次都在變、相依很少變，所以相依安裝要排在程式碼複製**之前**。順序寫反的話，改一行程式碼就要重裝一次所有套件。

**用 `slim` 不要用 `alpine`。** 這是 Python 特有的一條建議。Alpine 用 musl libc，而 PyPI 上的預編譯輪子（manylinux wheel）是為 glibc 建的——所以在 Alpine 上 `pip install` 很多套件會**現場從原始碼編譯**。後果是：建置時間從一分鐘變十分鐘、需要裝一堆編譯工具（映像反而更大）、而且常常因為缺某個標頭檔而失敗。`python:3.12-slim` 才是預設選擇。

**`PYTHONUNBUFFERED=1`。** 沒有它，Python 的 stdout 是有緩衝的，log 會延遲甚至在容器被砍時整批遺失。這一行在容器裡是必要的。

**非 root。** `USER appuser` 加上固定的 UID（讓 K8s 的 `runAsUser` 對得起來）。

**`--host 0.0.0.0`。** 預設綁 `127.0.0.1` 只接受容器內的連線，外面完全連不進來。這是容器化的第一名新手坑。

**`--proxy-headers`** 與 **`--timeout-graceful-shutdown`**——第 08 章和第四節分別會用到。

搭配 `.dockerignore`：

```text
.venv/
__pycache__/
*.pyc
.git/
.env
tests/
.pytest_cache/
```

漏掉 `.venv/` 的後果特別嚴重——它會被整個複製進建置環境，映像大幾百 MB，而且裡面是**本機平台編譯的套件**，在容器裡可能根本不能用。

---

## 二、worker 要開幾個

這一節把第 04、05 章的數字收攏起來。

### 先講結論

> **在 K8s 裡，一個容器跑一個 worker，靠副本數擴展。**

也就是說：**不要用 `--workers 4`**，用 `replicas: 4`。四個理由：

| 理由 | 說明 |
| --- | --- |
| K8s 已經是程序管理器 | uvicorn 的多 worker 監督者和 K8s 做同一件事，疊兩層只是讓故障排查變複雜 |
| 擴展顆粒度 | HPA 調的是 Pod 數。一個 Pod 四個 worker 的話，最小擴展單位就是四倍資源 |
| 資源隔離 | 一個 worker 記憶體洩漏，會拖垮同一個 Pod 裡的其他三個 |
| log 與診斷 | 單程序的 log 不會四份交錯，OOMKilled 也直接對應到一個 Pod |

例外是**不在 K8s 上**（單一 VM、Docker Compose），那時 `--workers` 是合理的，數量抓 `CPU 核心數 × 2 + 1` 起跳再依實測調整。

### 那要開幾個副本

從第 04 章的模型推：一個 worker 能同時處理的請求數，取決於你的 endpoint 是哪一種。

```text
async def endpoint（全非同步 I/O）→ 受限於 event loop，數百個並發沒問題
def endpoint（同步 I/O）        → 受限於 threadpool，預設 40 個
CPU 密集                        → 受限於 1 顆核心，本來就不該放在這裡
```

實務上的算法是反過來的：**從目標吞吐量和平均延遲推**。

```text
單一 worker 的容量 ≈ 併發上限 ÷ 平均回應時間

例：同步模式、threadpool 調成 15、平均回應 100ms
    → 15 ÷ 0.1 = 150 req/s

目標 600 req/s → 需要 4 個副本（再加 buffer → 5~6）
```

然後**回頭檢查第 05 章那條資料庫約束**：

```text
副本數 × (pool_size + max_overflow) ≤ 資料庫 max_connections × 0.8

6 × (10 + 5) = 90  ≤  100 × 0.8 = 80   ✗ 超過了
```

超過就得往回調——降 `pool_size`、或加 PgBouncer / Oracle DRCP 這類連線池代理。**這條約束通常才是真正的天花板**，而不是 CPU。

### CPU limit 的差異

.NET 那邊 CPU limit 會直接影響 ThreadPool 的大小計算，是個關鍵參數。Python 這裡沒有那層自動調整——event loop 就是一條執行緒，你給它 0.5 核或 4 核，它都只用得到大約一核。

所以：

```yaml
resources:
  requests:
    cpu: "200m"
    memory: "256Mi"
  limits:
    memory: "512Mi"        # 記憶體要設 limit
    # cpu 刻意不設 limit
```

**記憶體設 limit，CPU 不設 limit**（只設 request）。理由是 CPU 是可壓縮資源——超用只會變慢；設了 limit 反而會在尖峰時被 throttle，延遲曲線出現詭異的階梯。記憶體是不可壓縮的，不設 limit 的話一個洩漏的 Pod 可以拖垮整個節點。

（這個取捨在不同團隊有不同做法，如果你們的叢集有嚴格的資源治理政策，就照政策走。）

---

## 三、記憶體

Python 有一個容易誤判的性質：**釋放掉的記憶體不一定會還給作業系統**。CPython 用自己的記憶體池（arena）管理小物件，物件被回收後那塊記憶體通常留在池子裡等下次用。

實務後果是：處理過一次大請求（例如載入十萬列做匯出）之後，這個 Pod 的 RSS 就會停在高點不再降下來。看監控會以為是記憶體洩漏，其實不是。

三個處理原則：

**一、`limits.memory` 要抓「尖峰後的高原」而不是平均值。** 觀察一段時間，取最高點再加 30~50%。

**二、真正的洩漏和「不還給 OS」要分開判斷。** 洩漏是**持續**成長，每次尖峰後的基線一次比一次高；正常的高原是漲一次就停在那裡。

**三、大量資料的處理不要一次載入記憶體。** 匯出十萬列要用串流（`StreamingResponse` + 生成器）或分批，不要 `.all()` 之後 `json.dumps`。這比調任何參數都有效。

被 OOMKilled 的診斷：

```powershell
kubectl describe pod <name>       # 看 Last State: Terminated, Reason: OOMKilled
kubectl top pod <name>
```

`OOMKilled` 是 kernel 直接砍掉程序，**沒有任何 Python 層的錯誤訊息**——所以 log 裡什麼都不會有，只會突然中斷。看到「log 沒有例外但 Pod 重啟了」就先查這個。

---

## 四、Graceful shutdown：修掉那批 502

### uvicorn 收到 SIGTERM 會做什麼

1. 停止接受新連線
2. 等待進行中的請求完成（上限是 `--timeout-graceful-shutdown`）
3. 執行 lifespan 的關閉段（關連線池、關 HTTP client）
4. 結束程序

這個行為本身是正確的。問題出在**時序**——回到開頭那張圖，SIGTERM 和「流量停止送入」是並行的兩條線，而後者比較慢。

### 五行 YAML

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
    - name: api
      lifecycle:
        preStop:
          exec:
            command: ["sh", "-c", "sleep 5"]
```

`preStop` 在 SIGTERM **之前**執行。這五秒什麼事都不做，純粹是等 Endpoints 的變更傳播到 kube-proxy 和 Ingress。等流量真的停了，SIGTERM 才送出去，這時候關閉就不會撞到還在飛的請求。

`terminationGracePeriodSeconds` 必須**大於** `preStop 時間 + 最長請求時間`，否則 kubelet 會在中途送 SIGKILL 強制砍掉。三個數字要對齊：

```text
preStop sleep 5s
  + uvicorn --timeout-graceful-shutdown 30s
  = 35s  <  terminationGracePeriodSeconds 60s   ✓
```

### lifespan 裡該做什麼

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    app.state.http = httpx.AsyncClient(timeout=10.0)
    logger.info("application started", extra={"version": settings.version})
    yield
    logger.info("application shutting down")
    await app.state.http.aclose()
    engine.dispose()               # 關掉連線池，讓資料庫端的 session 釋放
```

`engine.dispose()` 特別重要。不關的話那些連線會停留在資料庫端直到逾時，而滾動更新時新舊 Pod 並存，連線數會短暫翻倍——這正是「部署時偶爾撞到連線數上限」的成因。

**不要在 lifespan 的關閉段做耗時的工作**（清理暫存、上傳報表）。那段時間有硬性上限，超過就被 SIGKILL。

---

## 五、三種 Probe

```python
@app.get("/health/live", include_in_schema=False)
async def live():
    return {"status": "ok"}          # 只證明程序活著，不碰任何依賴

@app.get("/health/ready", include_in_schema=False)
async def ready(db: DbSession):
    try:
        db.execute(text("SELECT 1 FROM DUAL"))    # Oracle；PG 用 SELECT 1
    except Exception:
        raise HTTPException(503, "database unavailable")
    return {"status": "ready"}
```

```yaml
startupProbe:
  httpGet: { path: /health/live, port: 8000 }
  periodSeconds: 5
  failureThreshold: 30          # 給 150 秒啟動時間
livenessProbe:
  httpGet: { path: /health/live, port: 8000 }
  periodSeconds: 10
  failureThreshold: 3
readinessProbe:
  httpGet: { path: /health/ready, port: 8000 }
  periodSeconds: 5
  failureThreshold: 2
```

三者分工必須講清楚，因為搞混的代價很大：

| Probe | 失敗時 | 該檢查什麼 |
| --- | --- | --- |
| startup | 還在啟動，不算失敗 | 同 liveness，只是給長一點的寬限 |
| liveness | **重啟容器** | **只檢查程序自己**，絕不碰外部依賴 |
| readiness | 從 Service 移除，不重啟 | 可以檢查依賴 |

**liveness 檢查資料庫是一個會放大故障的設計。** 想像資料庫短暫不可用三十秒：所有 Pod 的 liveness 同時失敗 → K8s 同時重啟全部 Pod → 資料庫恢復時被一大批同時啟動的 Pod 打爆 → 再次失敗。你用一次可以自癒的小故障，換來一場自我攻擊。

readiness 檢查依賴則是對的：Pod 被移出 Service（不再收流量）但**不重啟**，依賴恢復後自動回來。

還有兩個細節：

**liveness 端點要寫成 `async def` 且不做任何 I/O。** 第 04 章講過的理由——這樣它才能當作「event loop 是否被阻塞」的儀器。如果它寫成 `def`，它會佔用 threadpool 名額，而且 event loop 被卡住時它反而還能回應，你就失去了那個訊號。

**`startupProbe` 才是處理慢啟動的正確工具**，不是把 `livenessProbe` 的 `initialDelaySeconds` 調大。前者在啟動完成後就停用，後者會永久拉長偵測到當機的時間。

---

## 六、Migration

第 05 章說過不要在應用啟動時跑。正確做法是獨立一步：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: myapi-migrate
spec:
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: registry.example.com/myapi:1.4.0     # 和應用同一個映像
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - secretRef: { name: myapi-secrets }
```

用 ArgoCD 的話掛成 `PreSync` hook，它會在同步應用之前跑完並確認成功。

### Schema 要向前相容

滾動更新期間，**新舊版本的程式碼會同時連著同一個資料庫**。所以「刪掉一個欄位」這種 migration 不能一次做完——舊版 Pod 還在 SELECT 它。

標準做法是 expand-contract，分三次部署：

| 階段 | migration | 程式碼 |
| --- | --- | --- |
| 1. Expand | 新增欄位（nullable） | 同時寫新舊兩個欄位，讀舊的 |
| 2. Migrate | 回填資料 | 讀新的，仍寫兩個 |
| 3. Contract | 刪掉舊欄位 | 只用新的 |

麻煩，但這是零停機的代價。Oracle 還要多一層考量：**DDL 隱含提交**，所以一份 migration 跑到一半失敗是無法整段回滾的——每一份都要寫得夠小，而且務必在測試環境完整跑過。

---

## 七、完整 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapi
spec:
  replicas: 4
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0        # 0 = 先起新的再關舊的，容量不會下降
  selector:
    matchLabels: { app: myapi }
  template:
    metadata:
      labels: { app: myapi }
    spec:
      terminationGracePeriodSeconds: 60
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
      containers:
        - name: api
          image: registry.example.com/myapi:1.4.0
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef: { name: myapi-config }
          volumeMounts:
            - name: secrets
              mountPath: /run/secrets
              readOnly: true
          resources:
            requests: { cpu: "200m", memory: "256Mi" }
            limits: { memory: "512Mi" }
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          lifecycle:
            preStop:
              exec: { command: ["sh", "-c", "sleep 5"] }
          startupProbe:
            httpGet: { path: /health/live, port: 8000 }
            periodSeconds: 5
            failureThreshold: 30
          livenessProbe:
            httpGet: { path: /health/live, port: 8000 }
            periodSeconds: 10
          readinessProbe:
            httpGet: { path: /health/ready, port: 8000 }
            periodSeconds: 5
      volumes:
        - name: secrets
          secret: { secretName: myapi-secrets }
```

映像**用具體版本標籤，不要用 `latest`**——GitOps 的前提是「git 裡寫的就是叢集上跑的」，`latest` 讓這句話失效。

`readOnlyRootFilesystem: true` 需要注意一點：Python 預設會寫 `.pyc` 檔案。Dockerfile 裡的 `PYTHONDONTWRITEBYTECODE=1` 就是為了讓這個設定成立。如果有函式庫需要寫暫存檔，掛一個 `emptyDir` 到 `/tmp`。

---

## 八、「本機好好的、上叢集就掛」對照表

這張表是整套教材的收束。每一列都是前面某一章埋下的伏筆：

| 症狀 | 章節 | 根因 |
| --- | --- | --- |
| 容器起來但連不上 | 本章 | 沒加 `--host 0.0.0.0`，只綁了 127.0.0.1 |
| Pod `CrashLoopBackOff`，log 只有一行 ValidationError | 09 | 設定驗證擋住了——**這是正確行為**，去看少了哪個環境變數 |
| 一支慢 API 讓 `/health` 也超時 | 04 | `async def` 裡有同步阻塞，event loop 被卡住 |
| 尖峰時 `QueuePool timeout` | 05 | 連線池小於 threadpool 併發數 |
| 副本數一加，資料庫連線就爆 | 05 + 本章 | `副本數 × 池子大小` 超過 DB 上限 |
| 每次部署掉一批 502 | 本章 | 缺 `preStop`，SIGTERM 和 Endpoints 更新是並行的 |
| 部署時偶爾撞到連線數上限 | 本章 | lifespan 沒 `engine.dispose()`，新舊 Pod 連線並存 |
| 資料庫閃斷一下，全部 Pod 一起重啟 | 本章 | liveness 檢查了資料庫，故障被放大成自我攻擊 |
| OAuth redirect_uri 變成 http | 08 | 沒加 `--proxy-headers` |
| 前端偶爾出現 CORS 錯誤 | 08 | 錯誤回應在 CORS middleware 外層產生 |
| log 沒有例外但 Pod 突然重啟 | 本章 | OOMKilled，kernel 直接砍，Python 層沒有訊息 |
| 改了 ConfigMap 沒生效 | 09 | env 注入不能熱重載，要 `rollout restart` |
| 計數器歸零、排程重複執行 | 04 + 本章 | 程序內狀態在多副本下分裂 |
| 測試全綠但上線爆 ORA- 錯誤 | 10 | 測試用 SQLite，行為和 Oracle 不同 |

### 上線前檢查清單

**映像**：非 root、`PYTHONUNBUFFERED=1`、`--host 0.0.0.0`、沒有 `--reload`、`.dockerignore` 含 `.venv`、具體版本標籤。

**設定**：必填項沒有預設值、正式環境的危險組合有 validator 擋、`/docs` 依環境關閉、密鑰走 volume。

**併發**：threadpool 與連線池數字對齊、`副本數 × 池子` 沒超過 DB 上限、逾時全部設過。

**生命週期**：`preStop` sleep、`terminationGracePeriodSeconds` > preStop + graceful timeout、lifespan 有 `dispose()`。

**Probe**：liveness 不碰資料庫且是 `async def`、readiness 檢查依賴、慢啟動用 `startupProbe`。

**資料庫**：migration 走獨立 Job、schema 向前相容、Oracle migration 寫小一點。

---

## 九、常見誤解

**「`--workers 4` 比 `replicas: 4` 省資源。」**
在 K8s 上不划算。多 worker 讓 HPA 的擴展顆粒度變成四倍、一個 worker 洩漏會拖垮同 Pod 的其他三個、log 四份交錯難查。K8s 本來就是程序管理器，不需要在裡面再疊一層。

**「Alpine 映像比較小，用它。」**
Python 是例外。Alpine 的 musl libc 讓 PyPI 的預編譯輪子失效，很多套件要現場編譯——建置變慢十倍、要裝編譯工具反而更大、還常常失敗。用 `python:3.12-slim`。

**「滾動更新掉幾個請求是正常的。」**
不是。加 `preStop: sleep 5` 就沒了。根因是 SIGTERM 和 Endpoints 更新是並行的，應用開始關閉時流量還在進來。

**「liveness probe 要檢查資料庫，才知道服務是不是真的健康。」**
那會把一次可自癒的資料庫閃斷，放大成「所有 Pod 同時重啟、恢復時一起打爆資料庫」的自我攻擊。liveness 只檢查程序自己，依賴檢查放 readiness——它只把 Pod 移出 Service，不重啟。

**「記憶體用量一直不降，一定是洩漏。」**
CPython 釋放的記憶體不一定還給 OS。處理過一次大請求後 RSS 停在高點是正常的。洩漏的特徵是**持續**成長、每次尖峰後的基線一次比一次高。

**「migration 在啟動時跑比較不會忘記。」**
滾動更新會有多個 Pod 同時啟動、同時跑 migration，互相搶鎖甚至產生半套 schema。用獨立的 Job 或 ArgoCD PreSync hook。

---

## 十、同事會來問你的問題

**「uvicorn 的 worker 要開幾個？」**
在 K8s 上開一個，用副本數擴展。理由是 HPA 的顆粒度、資源隔離、log 可讀性，而且 K8s 本來就在做程序管理。副本數從「目標吞吐 ÷ 單 worker 容量」推，然後**回頭檢查 `副本數 × 連線池 ≤ DB 上限 × 0.8`**——那條約束通常才是真正的天花板。

**「為什麼每次部署都掉一批 502？」**
K8s 送 SIGTERM 和把 Pod 移出 Endpoints 是並行的，後者慢幾百毫秒到幾秒。應用已經開始關閉，流量還在進來。加 `preStop: sleep 5` 等傳播完成，並確認 `terminationGracePeriodSeconds` 大於 preStop 加最長請求時間。

**「三種 probe 怎麼分？」**
liveness 只檢查程序自己（失敗會重啟，碰依賴等於把小故障放大成全體重啟）；readiness 檢查依賴（失敗只移出 Service，會自己回來）；慢啟動用 startupProbe 而不是調大 liveness 的 `initialDelaySeconds`——前者啟動完就停用，後者會永久拉長當機偵測時間。另外 liveness 端點要寫 `async def` 且不做 I/O，它才能當作 event loop 是否被阻塞的儀器。

**「CPU limit 要設多少？」**
建議只設 request 不設 limit。Python 的 event loop 是單執行緒，給再多核心也用不到；設了 limit 反而在尖峰被 throttle，延遲出現階梯。記憶體則相反——一定要設 limit，因為它不可壓縮，一個洩漏的 Pod 能拖垮整個節點。

**「Pod 突然重啟但 log 裡什麼都沒有。」**
先看 `kubectl describe pod` 的 `Last State`。如果是 `OOMKilled`，那是 kernel 直接砍掉程序，Python 層完全沒有機會記錄任何東西。調高 `limits.memory`，同時檢查是不是有 endpoint 一次載入了太多資料——那種要改成串流或分批。

**「要刪掉一個資料庫欄位，直接寫 migration 可以嗎？」**
不行。滾動更新期間新舊版本會同時連著同一個資料庫，舊版還在 SELECT 那個欄位。要走 expand-contract 分三次部署：先加欄位並雙寫、再回填並切讀取、最後才刪。Oracle 因為 DDL 隱含提交無法整段回滾，每份 migration 還要寫得更小。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[10-testing]] — 上一章：CI 裡的測試
- [[12-cheatsheet]] — 下一章：附錄 A 速查
- [[04-async-and-concurrency]] — worker 容量的推導基礎
- [[05-database-sqlalchemy]] — 連線池約束
- [[09-configuration]] — 為什麼 CrashLoopBackOff 是好事
- [[21-deployment]] — ASP.NET Core 的對應章節
- [[k8s-mastery]] — 部署端的完整教材
- [[practice-2-deploy-real-app]] — K8s 教材的實戰篇，manifest 逐段解釋
