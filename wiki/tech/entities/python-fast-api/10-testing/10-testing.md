---
type: concept
domain: tech
tags: [python, fastapi, testing, pytest, testclient, dependency-overrides, testcontainers, mock]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 10 章：測試 — 全綠的測試為什麼擋不住上線第一天的 500

## 兩百支測試，零信心

某個團隊很自豪：兩百多支測試、覆蓋率 87%、CI 全綠才准合併。上線第一天，五個不同的 500 湧進來：

```text
ORA-12899: value too large for column "ORDERS"."CUSTOMER_NAME" (actual: 73, maximum: 50)
ORA-02291: integrity constraint violated - parent key not found
ORA-01400: cannot insert NULL into ("ORDERS"."NOTE")
```

測試環境用的是 SQLite in-memory——因為它快、不用裝東西、CI 上一行設定就跑得起來。正式環境是 Oracle。

而 SQLite 和 Oracle 在這幾件事上的行為**完全不同**：

| 行為 | SQLite | Oracle |
| --- | --- | --- |
| 外鍵約束 | **預設關閉**，要 `PRAGMA foreign_keys=ON` | 一律檢查 |
| `VARCHAR(50)` 長度 | **不強制**，塞 500 字也收 | 超過就 `ORA-12899` |
| 空字串 | 是空字串 | **等於 NULL**，NOT NULL 欄位會炸 |
| 型別 | 動態，什麼都收 | 嚴格 |
| 併發寫入 | 整個檔案鎖 | 列層級鎖 |

換句話說，**那兩百支測試驗證的是「這段程式碼在 SQLite 上能跑」**，而那不是任何人關心的事。

這一章要處理的就是這種「測了但沒測到」的問題。內容分三塊：FastAPI 的測試工具怎麼用（意外地好用）、測試資料庫該怎麼準備、以及 mock 的邊界該畫在哪。

---

## 一、測試金字塔在 FastAPI 的樣貌

| 層級 | 測什麼 | 比例 | 速度 |
| --- | --- | --- | --- |
| 單元 | 純函式、service 的業務規則（不碰 I/O） | 最多 | 毫秒 |
| 整合 | `TestClient` + 真的資料庫，走完整條 HTTP 路徑 | **比想像中該更多** | 幾十毫秒 |
| 端對端 | 真的部署起來，前端一起測 | 極少 | 秒 |

中間那一列和 .NET 那邊不太一樣。ASP.NET Core 的 `WebApplicationFactory` 要啟動整個 Host，成本不低，所以整合測試通常會被刻意壓在少數；而 FastAPI 的 `TestClient` **不啟動任何伺服器**——它直接在同一個程序裡呼叫 ASGI application，一支測試的開銷跟一般函式呼叫差不了多少。

實務上的結論是：**在 FastAPI 專案裡，多寫整合測試是划算的**。它同時驗證路由、參數解析、驗證規則、依賴鏈、序列化和資料庫互動——這幾件事在 FastAPI 裡高度耦合在函式簽章上，分開測反而測不到真正會出錯的地方。

---

## 二、`TestClient` 基礎

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

`TestClient` 是 httpx 的包裝，介面和一般 HTTP client 一樣（`client.post(url, json=...)`、`client.get(url, params=...)`、`headers=`）。它內部用 anyio 的 portal 在背景 event loop 上執行 ASGI app，所以**同步的測試程式碼也能測 `async def` 的 endpoint**——不需要把整個測試套件改成 async。

### 一個必知的參數

```python
client = TestClient(app, raise_server_exceptions=False)
```

預設情況下，如果 endpoint 丟出未處理例外，`TestClient` 會**把那個例外重新拋到測試裡**，而不是回傳 500。這對除錯很方便（直接看到 traceback），但你就測不到自己寫的 500 處理器。要驗證第 06 章那套錯誤格式，得關掉它：

```python
def test_unhandled_error_returns_problem_json():
    with TestClient(app, raise_server_exceptions=False) as c:
        resp = c.get("/boom")
    assert resp.status_code == 500
    assert resp.json()["title"] == "Internal Server Error"
    assert "trace_id" in resp.json()
```

### `with` 的意義

```python
with TestClient(app) as client:
    ...
```

用 `with` 才會觸發 **lifespan**（第 03 章那個啟動／關閉的 context manager）。如果你的 app 在 lifespan 裡建立 HTTP client 或連線池，不用 `with` 的話那些東西是 `None`，測試會出現莫名其妙的 `AttributeError`。

反過來，不需要 lifespan 的測試不用 `with` 會快一點。

---

## 三、`dependency_overrides`：最重要的工具

第 03 章說過，**依賴函式就是你的測試接縫**。這一節把它用滿。

```python
app.dependency_overrides[get_db] = override_get_db
```

覆寫是全域的，而且會作用在**依賴鏈的任何一層**——不管 `get_db` 是被 endpoint 直接使用，還是被 `get_current_user` 間接使用。

### 用它來模擬不同身分

這是最實用的用法。認證邏輯本身測一次就夠了，其他測試不該每次都真的去簽一個 JWT：

```python
# tests/conftest.py
import pytest
from app.api.deps import get_current_user

@pytest.fixture
def as_user(client):
    def _as(user: User):
        app.dependency_overrides[get_current_user] = lambda: user
        return client
    yield _as
    app.dependency_overrides.pop(get_current_user, None)
```

```python
def test_admin_can_delete(as_user, admin_user):
    resp = as_user(admin_user).delete("/api/v1/users/5")
    assert resp.status_code == 204

def test_normal_user_cannot_delete(as_user, normal_user):
    resp = as_user(normal_user).delete("/api/v1/users/5")
    assert resp.status_code == 403
```

三行就切換了身分。對照 .NET 那邊要寫一個 `TestAuthHandler` 並註冊一個假的 authentication scheme，這個機制簡單得多。

### 一定要清乾淨

`app.dependency_overrides` 是**掛在 app 物件上的全域字典**。忘了清的話，它會活到下一支測試、下一個檔案、整個 session。

症狀很好認：**單獨跑某支測試會過，整批跑就失敗**，而且失敗與否取決於檔案順序。這種問題查起來非常痛苦。

保險做法是加一個自動生效的 fixture：

```python
@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()
```

`autouse=True` 讓它套用到每一支測試，不需要記得引用。

---

## 四、測試資料庫

回到開頭那個事故。原則只有一句：

> **用和正式環境同一種資料庫的同一個大版本。**

### Testcontainers

```powershell
pip install testcontainers pytest
```

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.oracle import OracleDbContainer

from app.models.base import Base

@pytest.fixture(scope="session")
def db_engine():
    with OracleDbContainer() as oracle:
        engine = create_engine(oracle.get_connection_url())
        Base.metadata.create_all(engine)       # 或跑 alembic upgrade head
        yield engine
        engine.dispose()
```

Testcontainers 在測試開始時用 Docker 起一個真的資料庫，結束時自動清掉。`scope="session"` 讓整批測試共用一個容器——啟動 Oracle 容器要幾十秒，每支測試起一次是不可行的。

CI 上需要 Docker（GitHub Actions 的 ubuntu runner 內建）。Oracle 的容器映像較大，第一次拉取會慢，實務上會在 CI 快取它。

**如果環境真的不允許跑容器**，退而求其次是用一個共用的測試資料庫實例（每個 CI job 用不同 schema 避免互撞）。**不要退到 SQLite**——那等於沒測。

### 每支測試的隔離：交易回滾

重建整個 schema 太慢。標準做法是讓每支測試跑在一個**最後會被回滾的交易**裡：

```python
@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()        # 測試寫的所有東西都消失
        connection.close()
```

即使測試裡呼叫了 `session.commit()`，那個 commit 也只是結束內層的 savepoint——外層交易一 rollback，資料庫回到乾淨狀態。

```python
@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

這一組 fixture 是整個測試套件的地基。設好之後，每支測試都拿到一個乾淨的資料庫和一個接好線的 client：

```python
def test_create_order(client, db_session):
    resp = client.post("/api/v1/orders", json={"customer_email": "a@b.c", "items": [...]})
    assert resp.status_code == 201
    assert db_session.scalar(select(func.count()).select_from(Order)) == 1
```

---

## 五、Mock 的邊界

這是測試裡最容易做錯的決策。判準：

| 該 mock | 不該 mock |
| --- | --- |
| 外部 HTTP API（金流、簡訊、Google） | **自己的資料庫** |
| 寄信、推播 | 自己的 service 層 |
| 時間、隨機數、UUID | ORM（別 mock `Session`） |
| 收費或有副作用的操作 | 自己寫的純函式 |

右欄那些如果 mock 掉，測試就只是在驗證「我寫的 mock 符合我對它的想像」。最典型的反面教材是 mock `Session`：

```python
# ✗ 測了什麼？
mock_db = MagicMock()
mock_db.get.return_value = User(id=1, name="A")
```

這種測試永遠會過，因為它不會執行任何 SQL。真正的錯誤（欄位長度、外鍵、NULL 約束、N+1）一個都測不到——就是開頭那個事故的另一種版本。

### mock 外部 HTTP：`respx`

```powershell
pip install respx
```

```python
import respx
import httpx

@respx.mock
def test_payment_failure(client):
    respx.post("https://pay.example.com/charge").mock(
        return_value=httpx.Response(503, json={"error": "service unavailable"})
    )
    resp = client.post("/api/v1/orders/1/pay")
    assert resp.status_code == 502
```

`respx` 攔截 httpx 的請求，不需要改任何應用程式碼。**要記得測失敗路徑**——外部服務逾時、回 500、回了非預期的格式，這些才是上線後真正會發生的事。

### 時間：不要 mock，要注入

```python
# ✗ 到處 patch datetime，脆弱又會影響其他函式庫
with patch("app.services.order.datetime") as m:
    m.now.return_value = ...

# ✓ 把時間變成依賴
def get_now() -> datetime:
    return datetime.now(timezone.utc)

Now = Annotated[datetime, Depends(get_now)]

@router.post("/orders")
def create_order(payload: OrderCreate, now: Now, db: DbSession):
    ...
```

測試時 `app.dependency_overrides[get_now] = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)`。這對應 .NET 8 引入 `TimeProvider` 的同一個理由：**時間是外部依賴，該從外面傳進來**。

---

## 六、async 測試

如果 endpoint 是 `async def`，`TestClient` 仍然可以用（它自己管理 event loop）。真正需要寫 async 測試的情況只有兩種：要直接呼叫 async 的 service 函式，或要用 `AsyncSession`。

```powershell
pip install pytest-asyncio
```

```ini
# pytest.ini 或 pyproject.toml
[pytest]
asyncio_mode = auto
```

`asyncio_mode = auto` 讓所有 `async def test_*` 自動被當成 async 測試，不必每支都寫 `@pytest.mark.asyncio`。

```python
import httpx
from httpx import ASGITransport

async def test_async_endpoint():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/orders")
    assert resp.status_code == 200
```

注意 `ASGITransport`：舊版 httpx 可以直接寫 `httpx.AsyncClient(app=app)`，這個捷徑**已經被移除**。網路上大量範例還是舊寫法，照抄會得到 `TypeError`。

async 測試的另一個常見坑是 **event loop 的作用域**。session 級的 fixture（例如 async engine）如果建立在一個 loop 上、測試跑在另一個 loop 上，會出現 `attached to a different loop` 這類錯誤。解法是讓 loop 相關的 fixture 作用域一致，或乾脆讓 engine 也是 function scope（慢一點但不會出事）。

---

## 七、測試資料：用工廠，不要用共用 fixture

```python
# ✗ 一份大 fixture，所有測試共用
@pytest.fixture
def sample_data(db_session):
    users = [User(...), User(...), User(...)]
    orders = [Order(...), Order(...)]
    ...
```

問題是：改一筆資料會影響不知道多少支測試，而且讀測試的人得跳去 fixture 才知道前提是什麼。

```python
# ✓ 工廠函式，每支測試明確宣告自己要什麼
def make_user(db, **kwargs) -> User:
    defaults = {"email": f"u{uuid4().hex[:8]}@example.com", "is_active": True}
    user = User(**{**defaults, **kwargs})
    db.add(user)
    db.flush()
    return user

def test_inactive_user_cannot_login(client, db_session):
    user = make_user(db_session, is_active=False)      # 前提就在眼前
    resp = client.post("/api/v1/auth/token", data={"username": user.email, "password": "x"})
    assert resp.status_code == 401
```

email 用隨機值避免唯一約束互撞。測試裡**只寫出和這支測試相關的欄位**，其他走預設——讀的人一眼就知道重點是 `is_active=False`。

---

## 八、每支 endpoint 該測什麼

一個實用的最低標準，四種情況：

```python
class TestGetOrder:
    def test_returns_order(self, as_user, owner, order): ...          # happy path
    def test_404_when_missing(self, as_user, owner): ...              # 找不到
    def test_401_without_token(self, client): ...                     # 未認證
    def test_404_for_other_users_order(self, as_user, stranger): ...  # 別人的資源
```

最後一項最容易漏，而它是**唯一能防住越權存取的測試**。第 07 章講的多租戶問題，靠人工 review 很難保證，靠測試可以。

### 不要測框架

```python
# ✗ 你在測 Pydantic
def test_email_validation():
    resp = client.post("/users", json={"email": "not-an-email"})
    assert resp.status_code == 422
```

Pydantic 會不會驗證 email 不是你的責任。**但是**——如果那個規則是你自己寫的 `field_validator` 或 `model_validator`，那就該測，因為那是你的程式碼。

分界線：**驗證這件事本身不用測，你寫的驗證規則要測。**

---

## 九、常見誤解

**「測試用 SQLite 比較快，反正 SQL 是通用的。」**
不通用。SQLite 預設不檢查外鍵、不強制 `VARCHAR` 長度、型別是動態的，而 Oracle 三者都嚴格，還多一條「空字串等於 NULL」。用 SQLite 測出來的綠燈，證明不了任何關於正式環境的事。用 Testcontainers 跑真的資料庫。

**「覆蓋率 87% 代表品質不錯。」**
覆蓋率只說明程式碼被執行過，不說明被驗證過。一支只 assert `status_code == 200` 的測試也算覆蓋。開頭那個團隊有 87%。

**「mock 資料庫可以讓測試變快。」**
也讓測試不再測任何東西。SQL 錯誤、約束違反、N+1、交易問題全部被 mock 掉了。用交易回滾的 fixture 就夠快了——每支測試幾十毫秒。

**「`dependency_overrides` 不用清，反正下支測試會重設。」**
它是掛在 app 物件上的全域字典，會活到整個 session 結束。症狀是「單獨跑會過、整批跑會壞」，而且結果取決於檔案順序。用 `autouse=True` 的 fixture 自動清。

**「`TestClient` 要用 `httpx.AsyncClient(app=app)` 才能測 async endpoint。」**
不用。`TestClient` 自己管理 event loop，同步測試碼就能測 `async def` 的 endpoint。另外那個 `app=app` 捷徑在新版 httpx 已被移除，要改用 `ASGITransport(app=app)`。

**「500 的錯誤處理很難測。」**
`TestClient(app, raise_server_exceptions=False)`。預設它會把例外重新拋進測試（方便除錯），關掉之後就能驗證你自己的 500 回應格式。

---

## 十、同事會來問你的問題

**「測試資料庫可以用 SQLite 嗎？」**
不要。SQLite 預設關外鍵、不管 `VARCHAR` 長度、型別動態，Oracle 全部相反還多一條空字串即 NULL。測出來的綠燈對正式環境沒有參考價值。用 Testcontainers 起一個真的，`scope="session"` 共用一個容器，每支測試用交易回滾隔離。

**「怎麼測需要登入的 endpoint？」**
`app.dependency_overrides[get_current_user] = lambda: some_user`，三行切換身分，不用真的簽 JWT。認證邏輯本身另外測一次就好。記得用 `autouse` 的 fixture 清掉覆寫，否則會污染後面的測試。

**「什麼該 mock？」**
外部世界該 mock：第三方 HTTP（用 `respx`）、寄信、金流、時間、隨機數。自己的東西不該 mock：資料庫、service 層、ORM。mock 掉 `Session` 的測試永遠會過，因為它不執行任何 SQL——所有真正會出錯的地方都被繞過了。

**「測試之間為什麼會互相影響？」**
兩個常見來源。一是 `dependency_overrides` 沒清（全域字典，活到 session 結束）；二是資料庫沒隔離（用交易回滾的 fixture）。判斷方法：單獨跑會過、整批跑會壞，而且和檔案順序有關，那就是污染。

**「時間相關的邏輯怎麼測？」**
不要 patch `datetime`——脆弱而且會影響其他函式庫。把「現在幾點」做成一個依賴（`get_now`），測試時覆寫它。和 .NET 8 的 `TimeProvider` 是同一個設計。

**「每支 endpoint 要測幾種情況？」**
最低四種：正常路徑、資源不存在（404）、沒帶憑證（401）、**存取別人的資源（404）**。最後一項最常被漏，而它是唯一能自動防住越權存取的測試——人工 review 保證不了這件事。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[09-configuration]] — 上一章：測試環境的設定覆寫
- [[11-deployment]] — 下一章：CI 裡怎麼跑這些測試
- [[03-dependency-injection]] — `dependency_overrides` 的機制
- [[05-database-sqlalchemy]] — 為什麼 Oracle 和 SQLite 差這麼多
- [[20-testing]] — ASP.NET Core 的對應章節（`WebApplicationFactory` 與 Testcontainers）
