---
type: concept
domain: tech
tags: [python, fastapi, practice, kubernetes, minikube, argocd, github-actions, alembic, docker]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 實戰：把 FastAPI 服務送上叢集 — 和 ASP.NET Core 不一樣的十件事

## 這一章不講什麼

Deployment、Service、Ingress 怎麼寫，ArgoCD 的 Sync 狀態怎麼判讀，GitOps 為什麼要兩個 repo——這些在 [[practice-2-deploy-real-app]] 和 [[practice-3-gitops-pipeline]] 已經寫完了，而且**它們與應用是什麼語言無關**。

這一章只處理一件事：

> **交付鏈已經跑得起來（你已經送過 ASP.NET Core 上去）。現在應用換成 FastAPI，哪些步驟要改？**

答案是十個地方。有些只是換個指令，有些是**照 .NET 的做法會直接失敗**。逐一走一遍。

**起點**：一個本機 `uvicorn app.main:app --reload` 跑得起來的 FastAPI 專案，連 Oracle，有 Alembic migration，有 pytest 測試。
**終點**：推一個 tag，CI 建置推 Harbor、更新 manifest repo，ArgoCD 自動同步，migration 由 PreSync hook 跑完，服務在 minikube 上零掉包滾動更新。

---

## 一、Dockerfile：五個決策和 .NET 不同

```dockerfile
# ---------- builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 只複製相依清單——這一層只有 requirements.txt 變動時才重建
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
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", \
     "--timeout-graceful-shutdown", "30"]
```

### 差異 1：base image 不能挑 alpine

.NET 那邊 `mcr.microsoft.com/dotnet/aspnet:8.0-alpine` 是合理選項。Python **不是**。

Alpine 用 musl libc，而 PyPI 上的預編譯輪子（manylinux wheel）是為 glibc 建的，所以在 Alpine 上 `pip install` 很多套件會**現場從原始碼編譯**——`pydantic-core`（Rust）、`oracledb`、`psycopg` 都會中招。實際後果：

| | `python:3.12-slim` | `python:3.12-alpine` |
| --- | --- | --- |
| 首次建置 | 約 1 分鐘 | 約 10 分鐘以上 |
| 要不要裝編譯工具 | 不用 | 要（`gcc`、`musl-dev`、`rust`…） |
| 最終映像 | 較小 | 因為編譯工具反而更大 |
| 失敗率 | 低 | 常因缺標頭檔失敗 |

**用 slim。** 這是 Python 容器化的第一條規則。

### 差異 2：沒有 publish 這一步，venv 就是產物

.NET 的多階段建置是 `restore` → `build` → `publish`，產物是 `/app/publish` 那堆 DLL。Python 沒有編譯，**產物就是那個裝好套件的虛擬環境**。

所以 builder 階段建 `/opt/venv`，runtime 階段整包 `COPY --from=builder /opt/venv /opt/venv`。這樣 runtime 映像裡沒有 pip 快取、沒有建置暫存。

用 `uv` 的話這一段更快：

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
```

`uv.lock` 是真正的鎖檔（`requirements.txt` 只是一份已解析清單），可重現性更好。

### 差異 3：層快取的切點不同

.NET 是「先 COPY `*.csproj` 再 `dotnet restore`」，Python 是「先 COPY `requirements.txt` 再 `pip install`」。概念一樣，但**Python 這邊更容易寫錯**——因為 `COPY . .` 一行就能跑，很多人就這樣寫了，然後每改一行程式碼都要重裝一次所有套件。

### 差異 4：兩個環境變數是必要的

```dockerfile
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
```

`PYTHONUNBUFFERED=1` 關掉 stdout 緩衝。**沒有它，log 會延遲出現，容器被砍時整批遺失**——這在排查 CrashLoop 時會讓你完全看不到死因。.NET 沒有對應的問題。

`PYTHONDONTWRITEBYTECODE=1` 不寫 `.pyc`。它是 `readOnlyRootFilesystem: true` 能成立的前提。

### 差異 5：`.dockerignore` 漏了 `.venv` 後果更嚴重

```text
.venv/
__pycache__/
*.pyc
.git/
.env
tests/
.pytest_cache/
.ruff_cache/
```

漏掉 `.venv/` 不只是映像變大幾百 MB——那裡面是**你 Windows 本機編譯的套件**，複製進 Linux 容器裡可能根本不能用，而且會蓋掉 builder 階段裝好的正確版本。這比 .NET 漏掉 `bin/obj` 嚴重得多。

---

## 二、健康檢查端點

```python
from sqlalchemy import text

@app.get("/health/live", include_in_schema=False)
async def live():
    return {"status": "ok"}

@app.get("/health/ready", include_in_schema=False)
def ready(db: DbSession):
    try:
        db.execute(text("SELECT 1 FROM DUAL"))      # Oracle；PG 用 SELECT 1
    except Exception:
        raise HTTPException(503, "database unavailable")
    return {"status": "ready"}
```

兩個 FastAPI 特有的要求：

**liveness 必須是 `async def` 而且不做任何 I/O。** 這不只是「輕量一點比較好」——它是一支**儀器**。event loop 被同步阻塞卡住時，`/health/live` 會跟著超時，這正是你要的訊號（見 [[04-async-and-concurrency]]）。如果把它寫成 `def`，它會跑在 threadpool 裡，event loop 卡死時它反而還能正常回應，你就失去了唯一能區分「event loop 被堵」和「下游變慢」的指標。

**readiness 寫成 `def`**（同步 SQLAlchemy），它會被丟到 threadpool，不影響 loop。而且 Oracle 的 `SELECT 1` 必須寫成 `SELECT 1 FROM DUAL`，照 PostgreSQL 教學抄會直接 `ORA-00923`。

`include_in_schema=False` 讓它們不出現在 `/docs`，OpenAPI 乾淨一點。

---

## 三、設定注入：ConfigMap 給 env、Secret 給 volume

```yaml
envFrom:
  - configMapRef:
      name: myapi-config          # LOG_LEVEL、DB_POOL_SIZE、CORS_ORIGINS…
volumeMounts:
  - name: secrets
    mountPath: /run/secrets
    readOnly: true
volumes:
  - name: secrets
    secret:
      secretName: myapi-secrets   # database_url、jwt_secret
```

```python
model_config = SettingsConfigDict(
    env_file=".env",
    secrets_dir="/run/secrets",
    extra="ignore",
)
```

`secrets_dir` 是 FastAPI 側最省事的一個功能：K8s Secret volume 掛出來剛好是「一個 key 一個檔案」，pydantic-settings 直接把**檔名當欄位名、內容當值**讀進來，不用寫任何解析程式碼。.NET 那邊要自己加一個 provider 或用 `KeyPerFile`。

有一個 ConfigMap 的坑要注意：**list 型別必須是 JSON**。

```yaml
data:
  # ✗ 逗號分隔會解析失敗
  # CORS_ORIGINS: "https://a.com,https://b.com"
  CORS_ORIGINS: '["https://a.com","https://b.com"]'
```

在 YAML 裡塞一段 JSON 看起來很怪，但那是 pydantic-settings 對複雜型別的解析方式。要支援逗號分隔得自己加 `field_validator(mode="before")`（見 [[09-configuration]]）。

### 驗證「壞設定進不了叢集」

這是 FastAPI 側最值得刻意測一次的行為。故意讓 Secret 少一個 key，然後部署：

```powershell
kubectl rollout status deployment/myapi --timeout=60s
kubectl get pods -l app=myapi
kubectl logs deployment/myapi
```

你會看到新 Pod 進 `CrashLoopBackOff`，log 裡是一行 `ValidationError: database_url Field required`，而**舊版 Pod 完全沒被移除，服務照常運作**。

這是設計出來的行為，不是意外——`Settings()` 在模組層級建立，驗證發生在 uvicorn 開始監聽之前，所以 Pod 永遠不會 ready，滾動更新自動停住。看過一次之後，你對「必填設定不給預設值」這條規則就不會再有疑慮。

---

## 四、Migration：Alembic Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: myapi-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: harbor.example.com/myapi:1.4.0     # 和應用同一個映像
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - configMapRef: { name: myapi-config }
          volumeMounts:
            - name: secrets
              mountPath: /run/secrets
              readOnly: true
      volumes:
        - name: secrets
          secret: { secretName: myapi-secrets }
```

和 EF Core 的三個差異：

**沒有 `dotnet ef migrations bundle`。** .NET 可以把 migration 打包成一個獨立執行檔。Python 這邊直接用**同一個應用映像**跑 `alembic upgrade head`——`alembic/` 目錄和 `alembic.ini` 要記得 COPY 進映像（第一節的 Dockerfile 有）。

**`alembic.ini` 裡的連線字串要走環境變數。** 預設範本會把 URL 寫死在 ini 檔裡，那個值不能進版控：

```python
# alembic/env.py
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.database_url)
```

直接重用應用的 `Settings`，連線字串就只有一個來源。

**Oracle 的 DDL 隱含提交讓 migration 無法整段回滾。** 一份 migration 跑到一半失敗，前面的 DDL 已經生效。所以 `backoffLimit: 1`（別讓它一直重試把 schema 弄得更亂），而且每份 migration 要寫得夠小。這一點和 [[10-oracle-specifics]] 講的一樣。

---

## 五、副本數與連線池：實際算一次

這是 FastAPI 交付鏈上**唯一需要動筆算的東西**，而且算錯的症狀要到尖峰才會出現。

假設：同步 SQLAlchemy + `def` endpoints、平均回應 100ms、目標 400 req/s、Oracle `sessions` 上限 300（保守用 240）。

**步驟 1：threadpool 與連線池對齊。**

```text
threadpool 預設 40，連線池預設 5+10=15  → 矛盾
```

把 threadpool 縮到 15，連線池設 `pool_size=12, max_overflow=3`：

```python
# lifespan 裡
anyio.to_thread.current_default_thread_limiter().total_tokens = 15
```

**步驟 2：算單一 worker 容量。**

```text
15 併發 ÷ 0.1 秒 = 150 req/s
```

**步驟 3：算副本數。**

```text
400 ÷ 150 ≈ 2.7 → 3 個，加 buffer → 4 個
```

**步驟 4：回頭撞資料庫上限。**

```text
4 副本 × 1 worker × 15 條 = 60  ≤  240   ✓
```

過關。如果這裡超了，往回調 `pool_size` 或加 Oracle DRCP，**不是加副本**——這條約束通常才是真正的天花板。

**步驟 5：滾動更新期間會翻倍。** `maxSurge: 1` 表示最多同時存在 5 個 Pod：

```text
5 × 15 = 75  ≤  240   ✓
```

把這五步的結果寫進 manifest 的註解，下次有人要調副本數時才知道約束在哪。

---

## 六、CI：GitHub Actions

和 .NET 的 pipeline 結構差最多的一段。

```yaml
name: build-and-deploy
on:
  push:
    tags: ["V.*"]

concurrency:
  group: ${{ github.ref }}
  cancel-in-progress: false      # 部署類 workflow 不可取消

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy app
      - run: pytest -q            # Testcontainers 需要 docker，runner 內建

  build:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 取出版本號
        run: echo "VERSION=${GITHUB_REF_NAME#V.}" >> $GITHUB_ENV
      - uses: docker/login-action@v3
        with:
          registry: harbor.example.com
          username: ${{ secrets.HARBOR_USER }}
          password: ${{ secrets.HARBOR_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: harbor.example.com/myapi:${{ env.VERSION }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

四個差異：

**沒有 restore/build/publish 三段，但多了品質關卡。** .NET 的編譯器本身就是一道檢查；Python 沒有，所以 `ruff` 和 `mypy` **必須進 CI**——只在本機跑的型別檢查等於沒有。這一步是 Python 專案品質的下限。

**測試需要 Docker。** Testcontainers 會起一個真的資料庫容器（見 [[10-testing]]）。GitHub 的 ubuntu runner 內建 Docker，自架 runner 要確認。Oracle 的映像大，第一次拉取很慢，值得在 CI 快取。

**`cache: pip` 與 buildx 的 GHA 快取要分開設。** 前者快取 CI 環境裝套件的時間，後者快取 Docker layer。兩個都要，省下來的時間差很多。

**Harbor 的 robot account 密碼裡如果有 `$`，在 shell 展開時會出事。** 走 secret 引用不要用字串內插——這是你們踩過的坑，記在 [[13-troubleshooting]]。

更新 manifest repo 那一段的寫法（用 `yq` 而不是 `sed`）在 [[practice-3-gitops-pipeline]]，和語言無關，這裡不重複。

---

## 七、由內而外五步驗證

部署完不要直接開瀏覽器。照 [[practice-2-deploy-real-app]] 那套順序，但每一步換成 FastAPI 的具體檢查：

```powershell
# 1. Pod Running 且 READY n/n
kubectl get pods -l app=myapi

# 2. 應用真的起來了（不是只有容器起來）
kubectl logs deployment/myapi | Select-String "application started"

# 3. 從容器內部打 liveness（排除網路因素）
kubectl exec deploy/myapi -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health/live').read())"

# 4. readiness 通過代表資料庫連得上
kubectl exec deploy/myapi -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health/ready').read())"

# 5. 從叢集內部測 Service DNS
kubectl run tmp --rm -it --image=curlimages/curl --restart=Never -- curl -s http://myapi:8000/health/ready
```

第 3、4 步用 `python -c` 而不是 `curl`，因為 slim 映像裡**沒有 curl**（也沒有 wget）。這是每個人第一次都會撞到的小事：`kubectl exec ... -- curl` 回 `executable file not found`。

要嘛就這樣用 Python 內建的 `urllib`，要嘛用第 5 步那種丟一個臨時 curl Pod 的做法。**不要為了 debug 方便就把 curl 裝進正式映像**——那是多餘的攻擊面。

---

## 八、第一次部署最常犯的六個錯

| 症狀 | 根因 | 修法 |
| --- | --- | --- |
| 容器 Running 但連不上 | 沒加 `--host 0.0.0.0`，只綁 127.0.0.1 | 改 CMD |
| `CrashLoopBackOff`，log 一行 ValidationError | 設定少了必填項——**這是正確行為** | 看訊息補上那個 key |
| Pod 起來但 log 是空的 | 少了 `PYTHONUNBUFFERED=1` | 加進 Dockerfile |
| 建置十分鐘還在編譯 | 用了 alpine base image | 換 slim |
| `kubectl exec ... curl` 說找不到執行檔 | slim 映像沒有 curl | 用 `python -c` 或臨時 Pod |
| 尖峰時 `QueuePool timeout` | 連線池沒對齊 threadpool | 走第五節那五步重算 |

前四個都是 Python 特有的，在 .NET 交付經驗裡不會遇到。

---

## 九、上線前檢查清單

**映像**
- [ ] base image 是 `slim` 不是 `alpine`
- [ ] `PYTHONUNBUFFERED=1` 與 `PYTHONDONTWRITEBYTECODE=1`
- [ ] 非 root（`USER appuser` + 固定 UID）
- [ ] `--host 0.0.0.0`，沒有 `--reload`
- [ ] `.dockerignore` 含 `.venv/`
- [ ] `alembic/` 與 `alembic.ini` 有 COPY 進去
- [ ] 具體版本標籤，不是 `latest`

**設定**
- [ ] 必填項沒有預設值（故意漏一個測過 CrashLoop）
- [ ] 密鑰走 Secret volume + `secrets_dir`
- [ ] list 型別在 ConfigMap 裡是 JSON 字串
- [ ] `/docs` 依環境關閉

**併發**
- [ ] threadpool 與連線池數字對齊
- [ ] 五步計算做過，結果寫進 manifest 註解
- [ ] `maxSurge` 造成的翻倍算進 DB 上限

**生命週期**
- [ ] `preStop: sleep 5`
- [ ] `terminationGracePeriodSeconds` > preStop + graceful timeout
- [ ] lifespan 有 `engine.dispose()`

**Probe**
- [ ] liveness 是 `async def` 且不碰 I/O
- [ ] readiness 檢查資料庫（Oracle 記得 `FROM DUAL`）
- [ ] 慢啟動用 `startupProbe`

**CI**
- [ ] `ruff check` + `mypy` + `pytest` 都在 CI 裡
- [ ] Testcontainers 能在 runner 上跑
- [ ] migration 走 PreSync hook，`backoffLimit: 1`

---

## 十、本章回顧

十個差異，按「照 .NET 做法會不會直接失敗」分類：

**會直接失敗的四個**：alpine base image（建置爆炸）、缺 `PYTHONUNBUFFERED`（看不到 log）、`.dockerignore` 漏 `.venv`（映像壞掉）、readiness 用 `SELECT 1` 沒加 `FROM DUAL`（Oracle 報錯）。

**會安靜出錯的三個**：連線池沒對齊 threadpool（尖峰才爆）、ConfigMap 的 list 沒寫成 JSON、liveness 寫成 `def`（失去診斷儀器）。

**只是換個做法的三個**：venv 取代 publish 產物、Alembic 取代 EF migrations bundle、CI 多了 ruff/mypy 取代編譯器的檢查。

其餘所有東西——Deployment 怎麼寫、ArgoCD 怎麼判讀、GitOps 怎麼分 repo、Ingress 怎麼設——和你送 ASP.NET Core 上去時**完全一樣**。這是好消息：交付鏈的知識是可以跨語言重用的，需要重新學的只有上面這十件事。

## 自我檢查

蓋住答案先自己講一遍：

1. 為什麼 Python 容器不該用 alpine？（提示：manylinux wheel）
2. 少了 `PYTHONUNBUFFERED=1` 會在什麼時候害到你？
3. liveness 端點為什麼一定要 `async def`？
4. 給你「平均回應 200ms、目標 300 req/s、Oracle 上限 240」，算出副本數與 `pool_size`。
5. 為什麼 `kubectl exec ... -- curl` 會找不到執行檔？該怎麼辦？
6. migration 為什麼不能寫在 lifespan 裡？

答不出來的回對應章節：1、2 → [[11-deployment]]；3 → [[04-async-and-concurrency]]；4 → [[05-database-sqlalchemy]]；6 → [[05-database-sqlalchemy]]。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[11-deployment]] — 部署原理（本章是它的實作版）
- [[practice-1-containerize-your-app]] — K8s 教材的容器化實戰（ASP.NET Core 版）
- [[practice-2-deploy-real-app]] — 七個物件的完整 manifest 與驗證順序
- [[practice-3-gitops-pipeline]] — CI 與 ArgoCD 的完整流程
- [[13-troubleshooting]] — K8s 排錯方法論與踩坑案例庫
- [[argocd]]、[[minikube]]、[[helm]] — 交付鏈工具
