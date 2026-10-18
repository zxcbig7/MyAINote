---
type: concept
domain: tech
tags: [python, fastapi, cheatsheet, reference, troubleshooting, boilerplate]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 A：速查 — 第二螢幕用

這一份不解釋原理，只給「現在就要用」的東西：症狀對應、可直接貼的骨架、決策表、診斷指令。需要知道為什麼的時候，每一節都標了對應章節。

---

## 一、緊急排錯十連發

| 症狀 | 先查哪裡 | 章 |
| --- | --- | --- |
| 一支 API 慢，**連 `/health` 都超時** | `async def` 裡有同步阻塞 → 改 `def` 或換非同步驅動 | 04 |
| `QueuePool limit ... timed out` | 連線池小於 threadpool 併發數 → 兩個數字對齊 | 05 |
| 參數明明帶了卻收不到 | 看 422 回應的 `loc[0]`，它說了 FastAPI 認為該從哪拿 | 01 |
| `/users/me` 回 404 | 被 `/users/{id}` 先攔截 → 具體路徑移到前面 | 01 |
| `DetachedInstanceError` / `MissingGreenlet` | 序列化時才 lazy load → 查詢時 `options(selectinload(...))` | 05 |
| 前端「偶爾」CORS 錯誤 | 錯誤回應在 CORS middleware 外層產生 → CORS 移到**最後**註冊 | 08 |
| middleware 裡 `raise HTTPException` 變成 500 | `ExceptionMiddleware` 在內側 → 改 `return JSONResponse` 或用 dependency | 06 |
| 每次部署掉一批 502 | 缺 `preStop: sleep 5` | 11 |
| Pod 重啟但 log 沒有例外 | `kubectl describe pod` 看 `OOMKilled` | 11 |
| 單獨跑測試會過、整批跑失敗 | `dependency_overrides` 沒清 → `autouse` fixture | 10 |

---

## 二、專案骨架

```text
app/
├── main.py              # FastAPI 實例、middleware、router 掛載
├── api/
│   ├── deps.py          # 共用 dependency 與 Annotated 別名
│   └── routers/
│       ├── auth.py
│       └── orders.py
├── core/
│   ├── config.py        # BaseSettings
│   ├── errors.py        # 例外處理器
│   ├── logging.py       # JSON formatter
│   └── security.py      # 密碼雜湊、JWT
├── db/
│   └── session.py       # engine、SessionLocal
├── models/              # SQLAlchemy ORM
├── schemas/             # Pydantic
└── services/            # 業務邏輯
tests/
├── conftest.py
└── ...
```

### `main.py`

```python
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routers import auth, orders
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    app.state.http = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.http.aclose()
    engine.dispose()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# 由內而外註冊——最後加的在最外層
app.add_middleware(RequestContextMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

register_error_handlers(app)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")

@app.get("/health/live", include_in_schema=False)
async def live():
    return {"status": "ok"}
```

### `api/deps.py`

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.models.user import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

---

## 三、參數來源規則（01 章）

| 判斷順序 | 條件 | 來源 |
| --- | --- | --- |
| 1 | 名稱在路徑模板中 | path |
| 2 | 標注 `Query()`/`Path()`/`Body()`/`Header()`/`Cookie()`/`Form()` | 依標注 |
| 3 | 型別是 `Request`/`Response`/`BackgroundTasks` | 框架注入 |
| 4 | 值是 `Depends(...)` | 依賴 |
| 5 | 型別是 Pydantic model | body |
| 6 | 其餘單純型別 | query |

**必填/選填只看有沒有預設值。** `str | None` 不給預設值仍是必填。

```python
q: Annotated[str, Query()]                        # 必填 query
q: Annotated[str | None, Query()] = None          # 選填 query
tags: Annotated[list[str], Query()] = []          # 多值 query（少了 Query() 會變 body）
name: Annotated[str, Body(embed=True)]            # 單一值放 body
file_path: str                                    # 搭配路徑 /files/{file_path:path}
```

---

## 四、Pydantic v2 速查（02 章）

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(pattern=r".+@.+")
    quantity: int = Field(gt=0, le=999)
    note: str | None = Field(default=None, max_length=200)
    tags: list[str] = Field(default_factory=list)

    @field_validator("email", mode="before")
    @classmethod
    def normalize(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @model_validator(mode="after")
    def check(self):
        if ...:
            raise ValueError("...")     # 只能丟 ValueError，不能丟 HTTPException
        return self

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # 吃 ORM 物件
    id: int
```

| v1 | v2 |
| --- | --- |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes=True` |
| `allow_population_by_field_name` | `populate_by_name` |
| `.dict()` / `.json()` | `.model_dump()` / `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `@validator` / `@root_validator` | `@field_validator` / `@model_validator` |
| `Field(regex=)` | `Field(pattern=)` |
| `Optional[str]` 隱含選填 | **必須明寫** `= None` |

| 約束 | 用於 |
| --- | --- |
| `gt` `ge` `lt` `le` | 數值 |
| `min_length` `max_length` | 字串、list、dict |
| `pattern` | 字串 |
| `decimal_places` `max_digits` | Decimal |
| `default_factory` | 可變預設值 |

---

## 五、依賴生命週期（03 章）

| .NET | FastAPI | 寫法 |
| --- | --- | --- |
| Transient | `Depends(f, use_cache=False)` | 每次重新呼叫 |
| Scoped | 一般 `Depends(f)` | 一 request 一次（快取） |
| Singleton（輕） | `@lru_cache` 工廠 | 設定 |
| Singleton（重） | `lifespan` + `app.state` | 連線池、HTTP client、模型 |

```python
# yield dependency：try/finally 不能省
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 三個層級掛「不取回傳值」的依賴
@app.get("/x", dependencies=[Depends(require_admin)])
router = APIRouter(dependencies=[Depends(require_admin)])
app = FastAPI(dependencies=[Depends(verify_api_key)])
```

`yield` 之後的收尾在**回應送出前**執行 → 背景任務不能用 yield 出來的資源。

---

## 六、狀態碼（06 章）

| 狀況 | 碼 |
| --- | --- |
| 語法錯（JSON 壞、型別不對） | 400 |
| 語意不通過（缺必填、超範圍） | **422** |
| 沒帶／無效憑證 | 401 + `WWW-Authenticate` |
| 身分確認但權限不足 | 403 |
| 資源不存在 | 404 |
| **不該讓對方知道存在** | **404**（不是 403） |
| 狀態衝突（重複、樂觀鎖、已出貨） | 409 |
| 太頻繁 | 429 + `Retry-After` |
| 自己壞了 | 500 |
| 下游壞了 | 503 + `Retry-After` |

```python
raise HTTPException(status.HTTP_401_UNAUTHORIZED, "...", headers={"WWW-Authenticate": "Bearer"})
```

例外處理器要註冊三個：`RequestValidationError`、**`StarletteHTTPException`**（父類別，才接得到框架內部的 404/405）、`Exception`。

---

## 七、SQLAlchemy 速查（05 章）

```python
from sqlalchemy import select, func

db.get(Order, order_id)                                    # 主鍵
db.scalars(select(Order).where(Order.email == e)).all()    # 多筆
db.scalars(stmt).first()                                   # 單筆
db.scalar(select(func.count()).select_from(Order))         # 聚合

# eager loading
from sqlalchemy.orm import selectinload, joinedload
select(Order).options(selectinload(Order.items))    # 一對多（預設選這個）
select(Order).options(joinedload(Order.customer))   # 多對一 / 一對一

# 分頁
select(Order).offset(skip).limit(limit)                    # 一般
select(Order).where(Order.id < cursor).limit(20)           # 深分頁改 keyset
```

```python
engine = create_engine(
    url,
    pool_size=10,
    max_overflow=5,
    pool_timeout=10,        # 別用預設 30
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

**三條約束**：
1. `pool_size + max_overflow` ≥ threadpool 併發數
2. `副本數 × 池子大小` ≤ DB `max_connections` × 0.8
3. `pool_recycle` < 中間設備閒置逾時

```powershell
alembic revision --autogenerate -m "msg"    # 產生後一定人工讀過
alembic upgrade head
alembic downgrade -1
alembic history
```

⚠️ autogenerate 會把**欄位改名**產生成 drop + add，資料會消失。

---

## 八、async 決策（04 章）

| 函式裡有什麼 | 用 |
| --- | --- |
| 全部是 `await` 的非同步呼叫 | `async def` |
| 任何同步 I/O | **`def`** |
| 混合 | `async def` + `asyncio.to_thread(同步函式, ...)` |
| CPU 密集（>100ms） | 都不對 → `ProcessPoolExecutor` 或任務佇列 |

| 阻塞 | 非阻塞 |
| --- | --- |
| `time.sleep` | `await asyncio.sleep` |
| `requests.get` | `await httpx.AsyncClient().get` |
| 同步 `session.query` | `await AsyncSession.execute` |
| `subprocess.run` | `await asyncio.create_subprocess_exec` |

```python
# 並行
results = await asyncio.gather(a(), b(), c())      # 失敗時其餘仍在背景跑
async with asyncio.TaskGroup() as tg:              # 3.11+，一個失敗全取消
    tg.create_task(a())

# 逾時
async with asyncio.timeout(3):                     # 3.11+
    await slow()
```

```python
# 調 threadpool 上限（先確認 DB 連線池跟得上）
import anyio
anyio.to_thread.current_default_thread_limiter().total_tokens = 15
```

---

## 九、測試骨架（10 章）

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.oracle import OracleDbContainer

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.base import Base

@pytest.fixture(scope="session")
def db_engine():
    with OracleDbContainer() as c:
        engine = create_engine(c.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        engine.dispose()

@pytest.fixture
def db_session(db_engine):
    conn = db_engine.connect()
    tx = conn.begin()
    session = sessionmaker(bind=conn, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        tx.rollback()
        conn.close()

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def as_user(client):
    def _as(user):
        app.dependency_overrides[get_current_user] = lambda: user
        return client
    return _as
```

```python
# 測 500 要關掉重拋
with TestClient(app, raise_server_exceptions=False) as c:
    assert c.get("/boom").status_code == 500

# async 測試（httpx 新版必須用 ASGITransport）
from httpx import ASGITransport, AsyncClient
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    resp = await ac.get("/x")
```

每支 endpoint 最低四測：happy path、404、401、**存取別人的資源回 404**。

---

## 十、部署骨架（11 章）

```dockerfile
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
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

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
    - name: api
      resources:
        requests: { cpu: "200m", memory: "256Mi" }
        limits: { memory: "512Mi" }          # CPU 不設 limit
      lifecycle:
        preStop:
          exec: { command: ["sh", "-c", "sleep 5"] }
      startupProbe:
        httpGet: { path: /health/live, port: 8000 }
        periodSeconds: 5
        failureThreshold: 30
      livenessProbe:                          # 不可碰資料庫
        httpGet: { path: /health/live, port: 8000 }
      readinessProbe:                         # 可以碰資料庫
        httpGet: { path: /health/ready, port: 8000 }
```

`.dockerignore`：`.venv/` `__pycache__/` `*.pyc` `.git/` `.env` `tests/`

---

## 十一、診斷指令（PowerShell）

```powershell
# 本機
uvicorn app.main:app --reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
python -c "from app.core.config import settings; print(settings.model_dump())"   # 設定實際值
pytest -q
pytest -q -k "test_name" -x --lf                    # 只跑上次失敗的

# 相依
pip list --outdated
pip show pydantic                                    # 確認是 v1 還 v2

# 容器
docker build -t myapi:dev .
docker run --rm -p 8000:8000 --env-file .env myapi:dev
docker exec -it <id> sh

# K8s
kubectl logs -f deployment/myapi
kubectl logs deployment/myapi --previous            # 上一個掛掉的容器
kubectl describe pod <name>                          # 看 Last State / OOMKilled
kubectl exec -it <pod> -- python -c "import app.main"
kubectl rollout restart deployment/myapi             # 改了 ConfigMap 之後
kubectl port-forward svc/myapi 8000:8000
kubectl top pod
```

---

## 十二、數字速查

散落各章的預設值與建議值，集中在這裡。

| 項目 | 預設 | 建議 | 章 |
| --- | --- | --- | --- |
| threadpool（AnyIO） | 40 | 對齊連線池 | 04 |
| `pool_size` | 5 | 10 | 05 |
| `max_overflow` | 10 | 5 | 05 |
| `pool_timeout` | 30 s | **10 s** | 05 |
| `pool_recycle` | 不回收 | 1800 s | 05 |
| `pool_pre_ping` | False | **True** | 05 |
| access token 效期 | — | 15 min | 07 |
| JWT `leeway` | 0 | 30 s | 07 |
| httpx timeout | 5 s | 明確設定 | 04 |
| CORS `max_age` | 600 s | 600 s | 08 |
| `preStop` sleep | 無 | **5 s** | 11 |
| `--timeout-graceful-shutdown` | 30 s | 30 s | 11 |
| `terminationGracePeriodSeconds` | 30 s | **60 s** | 11 |

**硬性上限**（不是設定，是限制）：

| 限制 | 值 |
| --- | --- |
| bcrypt 密碼長度 | **72 位元組**（超過靜默截斷） |
| Oracle `IN` 清單 | **1000** 個（`ORA-01795`） |
| Oracle 識別碼長度 | 30（12.2 前）／128 |
| PostgreSQL `max_connections` 預設 | 100 |

**Oracle 錯誤碼**：

| 碼 | 意義 | 對應 HTTP |
| --- | --- | --- |
| `ORA-00001` | 唯一約束衝突 | 409 |
| `ORA-01400` | NOT NULL 欄位為 NULL | 400 / 500 |
| `ORA-01795` | IN 清單超過 1000 | 500（要改程式） |
| `ORA-02291` | 外鍵父鍵不存在 | 400 / 409 |
| `ORA-12899` | 值超過欄位長度 | 400 |

---

## 十三、紅色警戒清單

看到這些就要停下來：

- [ ] `async def` 裡有 `requests.` / `time.sleep` / 同步 ORM 查詢 — 04
- [ ] `jwt.decode` 沒傳 `algorithms` — 07
- [ ] `jwt.decode` 沒驗 `audience` — 07
- [ ] `Depends(oauth2_scheme)` 被當成認證用 — 07
- [ ] endpoint 直接回傳 ORM 物件，沒有 `response_model` — 02
- [ ] request body 直接用 ORM model 接 — 02
- [ ] `os.getenv("X", "預設值")` 用在必填設定上 — 09
- [ ] `CORSMiddleware` 不是最後一個 `add_middleware` — 08
- [ ] `allow_credentials=True` 配 `allow_origins=["*"]` — 08
- [ ] 測試用 SQLite 但正式用 Oracle — 10
- [ ] 測試 mock 掉 `Session` — 10
- [ ] `Base.metadata.create_all()` 或 alembic 寫在 lifespan 裡 — 05
- [ ] livenessProbe 打的端點會查資料庫 — 11
- [ ] Dockerfile 用 `alpine` — 11
- [ ] 沒有 `--host 0.0.0.0` — 11
- [ ] 沒有 `preStop` — 11
- [ ] `except Exception: pass` — 06
- [ ] 資料庫錯誤訊息直接回給客戶端 — 06
- [ ] 「先查再寫」當成唯一約束的替代 — 06
- [ ] 密鑰進了 git（先輪替，再清歷史）— 09

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[11-deployment]] — 上一章：部署
- [[13-aspnet-mapping]] — 下一章：附錄 B，ASP.NET Core 完整對照
- [[23-cheatsheet]] — .NET 那邊的對應附錄
