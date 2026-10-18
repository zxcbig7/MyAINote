---
type: concept
domain: tech
tags: [python, fastapi, sqlalchemy, orm, session, connection-pool, alembic, oracle, transaction]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 05 章：資料庫與 SQLAlchemy — session 的邊界該畫在哪

## 一個算術沒對上的連線池

服務跑了兩週，開始出現間歇性 500，log 裡是這一行：

```text
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 30.00
```

資料庫本身沒有壓力，CPU 15%，慢查詢清單是空的。應用程式碼也沒改過。

問題出在兩個數字沒有對齊。上一章講過，FastAPI 的 threadpool 預設可以同時跑 **40 個** `def` endpoint。而 SQLAlchemy 的連線池預設是 `pool_size=5` 加 `max_overflow=10`，總共 **15 條**連線。

於是尖峰時段的實際情況是：40 條執行緒同時醒著，前 15 條拿到連線開始工作，剩下 25 條全部堵在 `QueuePool` 前面等。等超過 `pool_timeout`（預設 30 秒）就丟例外。

**這不是資料庫的問題，是應用程式的併發設定內部矛盾。** 而且它只會在尖峰出現，所以拖了兩週才被發現。

這一章要把資料庫這一層講到能夠自己算出這些數字。它的內容順序刻意跟著三個問題走：要不要用 async ORM、session 的生命週期歸誰管、以及交易的邊界該畫在哪。

讀完之後，你應該能夠獨立設定一組連線池參數並說出每個數字的來源、看到 `DetachedInstanceError` 或 `MissingGreenlet` 就知道是哪裡出錯、以及知道 migration 為什麼不該在應用啟動時跑。

---

## 一、第一個決定：同步還是非同步

SQLAlchemy 從 1.4 起同時提供同步與非同步兩套 API。很多人看到 FastAPI 是 async 框架，直覺就選 async 版本，然後在接下來三個月裡不斷撞牆。

先給結論：

> **除非你有明確理由，先用同步 SQLAlchemy 配 `def` endpoint。**

這不是保守，是上一章推導出來的結果。`def` 的 endpoint 會被丟到 threadpool，阻塞被隔離，event loop 完全不受影響。這個組合能撐住的併發量遠比多數人以為的高，而且**整個生態系都站在這一邊**——絕大多數的教學、外掛、除錯經驗都是同步的。

| 情境 | 建議 |
| --- | --- |
| 一般 CRUD API，每個請求 1–10 次查詢 | **同步 + `def`** |
| 已經大量使用 async（呼叫多個外部 API、WebSocket） | async |
| 單一請求要並行發出多個獨立查詢 | async（可以 `gather`） |
| 極高併發、查詢短而多 | async（省下執行緒切換成本） |
| 團隊第一次寫 Python 後端 | **同步**，先把東西做出來 |

async 版本的實際代價有四項，選之前要知道：

**一、整條鏈都必須是 async。** 一個同步的呼叫混進來就毀了整支函式的非同步性質，而且錯誤訊息（`MissingGreenlet`）完全不會告訴你這件事。

**二、lazy loading 不能用。** 同步版本裡 `order.items` 會自動發一次查詢；async 版本會直接丟 `MissingGreenlet`，所有關聯都必須明確 eager load。這是紀律上的好事，但初期會讓人挫折。

**三、驅動選擇變少。** PostgreSQL 的 `asyncpg` 很成熟；Oracle 要 `python-oracledb` 2.0 以上才有 async API；某些 legacy 資料庫根本沒有 async 驅動。

**四、除錯困難。** stack trace 會穿過 greenlet 與 event loop，可讀性明顯變差。

本章的範例以同步為主，async 的差異會在需要時標出來。

---

## 二、三個核心物件

從 EF Core 過來的人可以先建立這組對應：

| SQLAlchemy | EF Core | 生命週期 |
| --- | --- | --- |
| `Engine` | （沒有直接對應；接近 provider + 連線池） | **程序層級，一個就好** |
| `Session` | `DbContext` | **一個 request 一個** |
| Declarative model | Entity | 靜態定義 |

### Engine：連線池的持有者

```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

`Engine` **建立成本很高而且持有連線池，必須是程序層級的單例**。每個請求 `create_engine()` 一次的後果是連線數暴增、資料庫端 session 耗盡——和 .NET 那邊每次 `new HttpClient()` 是同一類錯誤。

放在模組層級（像上面這樣）就已經是單例了，因為 Python 的模組只會被載入一次。

### Session：工作單元

`Session` 對應 EF Core 的 `DbContext`，職責一樣：追蹤物件變更、維護 identity map（同一個主鍵在同一個 session 內是同一個 Python 物件）、在 flush 時把變更轉成 SQL。

它**不是執行緒安全的**，一個 session 只能被一條執行緒／一個請求使用。這就是為什麼它必須是「Scoped」——用上一章的 `yield` dependency 實作。

### Model：2.0 的宣告式寫法

```python
# app/models/order.py
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_email: Mapped[str] = mapped_column(String(255), index=True)
    total: Mapped[Decimal]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    sku: Mapped[str] = mapped_column(String(32))
    quantity: Mapped[int]

    order: Mapped["Order"] = relationship(back_populates="items")
```

`Mapped[int]` 與 `Mapped[str | None]` 這種寫法是 SQLAlchemy 2.0 的風格——**型別註解直接決定欄位是否 nullable**，`Mapped[str]` 是 `NOT NULL`，`Mapped[str | None]` 允許 NULL。網路上大量文章仍是 1.x 的 `Column(Integer, primary_key=True)` 寫法，兩者可以並存但別混用。

**這些是資料庫的形狀，不是 API 的形狀。** 第 02 章講的 Pydantic model 分層在這裡才真正發揮作用——`Order` 會隨資料表演進，`OrderOut` 是對外契約，兩者本來就該分開。

---

## 三、session 的生命週期與交易邊界

`get_db` 這個依賴有三種常見寫法，差別在交易由誰負責。

### 版本一：只負責開關（建議）

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]
```

commit 由呼叫端明確執行：

```python
@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: DbSession):
    order = Order(customer_email=payload.customer_email, total=payload.total)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
```

**優點是交易邊界是顯性的。** 讀 endpoint 就知道它會寫入什麼、在哪裡提交。需要在一支 endpoint 裡做兩個獨立交易（少見但存在）也做得到。

缺點是要記得 commit，忘了就是資料靜靜地沒進去。

### 版本二：依賴代管交易

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

**優點是不會忘記 commit，也不會忘記 rollback。** 一個請求就是一個交易，語意乾淨。

缺點有兩個，而且都不小：交易邊界變成隱性的（讀 endpoint 看不出來哪裡提交）；而且如果在 endpoint 裡做了非資料庫的副作用（寄信、呼叫外部 API），它們不會跟著 rollback，而你會以為會。

### 版本三：交給 service 層

```python
@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: DbSession):
    return order_service.create(db, payload)     # commit 在 service 裡
```

endpoint 只負責 HTTP，交易在業務邏輯層。這是專案長大之後的自然歸宿，和 .NET 那邊「交易邊界畫在應用服務層」是同一個結論。

### 該選哪個

小專案用版本一，中大型專案用版本三。版本二很誘人但**別在有外部副作用的專案裡用**——它會讓「這個操作到底有沒有原子性」變成一個需要翻三層程式碼才能回答的問題。

### `expire_on_commit=False` 很重要

SQLAlchemy 預設在 `commit()` 之後把所有物件標記為過期，下次存取任何屬性都會重新查一次資料庫。在 FastAPI 裡這會出事：

```python
@app.post("/orders", response_model=OrderOut)
def create_order(payload: OrderCreate, db: DbSession):
    order = Order(...)
    db.add(order)
    db.commit()
    return order        # 序列化 order.id 時 → 觸發 refresh 查詢
```

如果 session 這時已經關閉（例如 commit 由依賴代管、收尾已經跑完），就會爆 `DetachedInstanceError`。設 `expire_on_commit=False` 讓 commit 之後物件仍然可讀，是 FastAPI + SQLAlchemy 幾乎必開的設定。

---

## 四、連線池的數學

回到開頭那個事故。連線池參數與它們的意義：

| 參數 | 預設 | 意義 |
| --- | --- | --- |
| `pool_size` | 5 | 常駐連線數 |
| `max_overflow` | 10 | 尖峰時可額外開的連線數（用完會被關掉） |
| `pool_timeout` | 30 | 等不到連線時等多久才丟例外 |
| `pool_recycle` | -1（不回收） | 連線活多久就重建，秒 |
| `pool_pre_ping` | False | 取出前先 ping 一下確認還活著 |

### 三條計算規則

**規則一：連線池要跟得上 threadpool。**

同步模式下，每個 `def` endpoint 執行時都佔一條執行緒加一條連線。所以：

```text
pool_size + max_overflow  ≥  同時執行的 def endpoint 數量
```

預設的 40 條 threadpool 對上 15 條連線就是開頭那個事故。兩個做法：把連線池放大到接近 40，或把 threadpool 縮小到接近連線池。**通常後者更好**——執行緒不夠時請求是排隊等待（可預期），連線不夠時是等 30 秒後丟例外（使用者看到 500）。

**規則二：總連線數不能超過資料庫的上限。**

```text
worker 程序數 × Pod 副本數 × (pool_size + max_overflow)  ≤  資料庫 max connections × 0.8
```

這是最容易被忽略的一條，因為它跨越了應用與部署兩個領域。實際例子：

```text
4 個 uvicorn worker × 3 個 Pod 副本 × (20 + 10) = 360 條連線
```

PostgreSQL 預設 `max_connections=100`，Oracle 的 `sessions` 也有上限。360 遠遠超過。而且這個數字在本機（1 worker、1 副本 = 30 條）完全看不出來——又一個「本機好好的、上叢集就掛」。

超過的話有三個方向：降低每個 worker 的 pool_size、減少 worker 數（改用更多 Pod 但每 Pod 少 worker）、或加一層連線池代理（PgBouncer、Oracle 的 DRCP）。

**規則三：`pool_recycle` 要小於中間設備的閒置逾時。**

雲端的負載平衡器、防火牆、資料庫本身都會砍掉閒置太久的連線。連線被對方砍掉但池子還以為它活著，下次取用就是 `Lost connection` 或 `ORA-03113`。

設 `pool_recycle=1800`（30 分鐘）主動回收，並開 `pool_pre_ping=True` 作為第二道保險。`pre_ping` 每次取連線多一次 round trip，但它換掉的是「半夜第一個請求必定失敗」這種難查的問題，很划算。

### 一組合理的起手值

```python
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=5,
    pool_timeout=10,        # 不要用預設 30 秒——那太久了，快點失敗比較好
    pool_recycle=1800,
    pool_pre_ping=True,
)
```

搭配把 threadpool 調到 15（`limiter.total_tokens = 15`），兩個數字就對齊了。

`pool_timeout` 特別建議調短：等 30 秒才失敗的請求，使用者早就重試了，而那些重試又會再吃掉連線，形成惡性循環。快速失敗加上重試策略（[[17-resilience]]）比長時間等待健康得多。

---

## 五、查詢：2.0 style

```python
from sqlalchemy import select

# 單筆
order = db.get(Order, order_id)                    # 主鍵查詢，會走 identity map

# 條件查詢
stmt = select(Order).where(Order.customer_email == email).order_by(Order.created_at.desc())
orders = db.scalars(stmt).all()

# 分頁
stmt = select(Order).offset(skip).limit(limit)

# 聚合
from sqlalchemy import func
total = db.scalar(select(func.count()).select_from(Order))
```

1.x 的 `db.query(Order).filter(...)` 仍可用但已是 legacy，新程式碼用 `select()`。

### N+1

和 EF Core 完全一樣的問題：

```python
# ✗ 1 + N 次查詢
orders = db.scalars(select(Order)).all()
for o in orders:
    print(len(o.items))       # 每次存取 o.items 都發一次查詢

# ✓ 2 次查詢（一次撈 orders，一次用 IN 撈全部 items）
from sqlalchemy.orm import selectinload
stmt = select(Order).options(selectinload(Order.items))
orders = db.scalars(stmt).all()
```

兩種 eager loading 的取捨：

| 策略 | SQL | 適用 |
| --- | --- | --- |
| `selectinload` | 主查詢 + 一次 `WHERE id IN (...)` | **一對多的預設選擇** |
| `joinedload` | 單一 LEFT OUTER JOIN | 一對一、多對一 |

一對多用 `joinedload` 會產生笛卡兒式的列數膨脹（10 筆訂單各 20 個品項 = 200 列），`selectinload` 沒有這個問題。注意 `selectinload` 的 IN 清單在 Oracle 上會撞到 1000 個元素的上限（見第九節）。

要診斷實際發出的 SQL，開 `create_engine(..., echo=True)`（僅限開發環境），或設定 SQLAlchemy 的 logger 層級。

### 深分頁

`OFFSET 100000 LIMIT 20` 要求資料庫掃過並丟棄十萬列。資料量大時改用 keyset（游標式）分頁：

```python
stmt = (
    select(Order)
    .where(Order.id < last_seen_id)      # 用上一頁最後一筆的 id
    .order_by(Order.id.desc())
    .limit(20)
)
```

代價是不能跳頁。這個取捨和 [[08-efcore-query]] 那邊講的完全一樣。

---

## 六、ORM 物件與 Pydantic 的交界

這是 FastAPI + SQLAlchemy 最經典的一組坑，三個症狀來自同一個根因：**序列化的時機晚於 session 的存活期，或晚於資料被載入的時機。**

### `DetachedInstanceError`

```text
Parent instance <Order> is not bound to a Session; lazy load operation of
attribute 'items' cannot proceed
```

`response_model=OrderOut` 而 `OrderOut` 裡有 `items` 欄位，但查詢時沒有 eager load，序列化時才要去 lazy load——這時 session 可能已經關了。

解法：**回應需要的關聯，查詢時就要載入。**

```python
@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: DbSession):
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    order = db.scalars(stmt).first()
    if order is None:
        raise HTTPException(404)
    return order
```

一個實用的紀律：**`response_model` 上有什麼關聯，查詢的 `options()` 就要有對應的 loader**。這條規則把「回應形狀」和「查詢形狀」綁在一起，值得寫進 code review 清單。

### `MissingGreenlet`（async 專屬）

async 模式下 lazy load 直接不合法，訊息是 `greenlet_spawn has not been called`。同樣的解法：全部明確 eager load。這也是前面說 async 版本紀律更嚴的意思。

### 序列化到一半才發現欄位是 None

`OrderOut.total` 宣告成必填但資料庫那一列是 NULL → `ResponseValidationError` → 500。第 02 章講過回應驗證失敗是伺服器的錯。修法是讓 Pydantic model 誠實反映資料庫的 nullable 狀態，或在查詢時就過濾掉不完整的資料。

---

## 七、Alembic：schema 版本控制

Alembic 是 SQLAlchemy 作者寫的 migration 工具，對應 EF Core Migrations。

```powershell
alembic init alembic
alembic revision --autogenerate -m "add orders table"
alembic upgrade head
alembic downgrade -1
```

`--autogenerate` 會比對 model 與資料庫現況產生差異腳本，但它**看不到所有東西**：

| autogenerate 偵測得到 | 偵測不到 |
| --- | --- |
| 新增／刪除資料表、欄位 | 欄位改名（會變成 drop + add，**資料會消失**） |
| 型別變更、nullable 變更 | 表格改名 |
| 索引與唯一約束 | 資料轉換（把一欄拆成兩欄） |
| 外鍵 | 部分資料庫特有物件（序列、觸發器） |

所以**每一份產生出來的 migration 都必須人工讀過再提交**。欄位改名是最危險的一項，autogenerate 會產生「刪掉舊欄位、新增新欄位」，跑下去正式環境的資料就沒了。正確做法是手改成 `op.alter_column(..., new_column_name=...)`。

### 不要在應用啟動時跑 migration

```python
# ✗ 別這樣
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)     # 或 alembic upgrade
    yield
```

理由和 .NET 那邊完全一樣，而且在 K8s 下更嚴重：滾動更新時會有多個 Pod 同時啟動，同時對同一個資料庫跑 migration，互相搶鎖甚至產生半套 schema。

正確做法是把 migration 做成獨立的一步：K8s 的 `Job`（或 ArgoCD 的 PreSync hook）先跑完，成功之後才更新 Deployment。細節在第 11 章。

`Base.metadata.create_all()` 只適合本機開發和測試，它不做版本管理，也處理不了任何 schema 變更。

---

## 八、Oracle 特有的事

你們的環境是 Oracle，有幾件事和 PostgreSQL 教學寫的不一樣。

**驅動用 `python-oracledb`。** 它是舊 `cx_Oracle` 的後繼者（同一批人維護），預設是 **thin mode**——純 Python 實作，**不需要安裝 Oracle Instant Client**，這對容器化是巨大的簡化（省掉一整層 base image 的麻煩）。需要進階功能（某些 LOB 操作、Advanced Queuing、Kerberos）才需要 thick mode 並掛上 client 函式庫。

```python
# thin mode，連線字串
create_engine("oracle+oracledb://user:pwd@host:1521/?service_name=ORCLPDB1")
```

**識別碼大小寫。** Oracle 未加引號的識別碼會被轉成大寫。SQLAlchemy 知道這個規則，但如果你的資料表當初是用引號建成小寫的，就必須在 model 裡明確標注，否則會找不到表。

**空字串等於 NULL。** Oracle 把 `''` 視為 NULL，所以 `Mapped[str]`（NOT NULL）的欄位存入空字串會違反約束。應用層要決定「沒填」到底是 `None` 還是預設值，不能靠資料庫區分。

**`IN` 清單上限 1000。** `ORA-01795: maximum number of expressions in a list is 1000`。這會在兩個地方咬人：自己寫的 `where(Order.id.in_(ids))`，以及 **`selectinload` 產生的 IN 查詢**——後者特別陰險，因為那條 SQL 不是你寫的。資料量大時要分批。

**序列與主鍵。** Oracle 12c 之後有 `IDENTITY` 欄位，SQLAlchemy 支援；舊 schema 用序列加觸發器的話要在 model 裡明確設定。

**DDL 隱含提交。** Oracle 的每一句 DDL 都會提交當前交易，所以 migration 無法整段回滾——一份 migration 跑到一半失敗，前面的 DDL 已經生效。這代表 Oracle 的 migration 應該**寫得更小、更保守**，而且一定要在測試環境完整跑過。

這些和 [[10-oracle-specifics]] 講的是同一組坑，只是換了語言。

---

## 九、常見誤解

**「FastAPI 是 async 框架，所以一定要用 async ORM。」**
不是。`def` endpoint 會被丟到 threadpool，同步 SQLAlchemy 在裡面阻塞完全安全。async ORM 的代價（整條鏈不能有同步、不能 lazy load、驅動選擇少、除錯難）多數專案不值得付。

**「連線池用預設的就好。」**
預設是 5 + 10 = 15，對上 FastAPI 預設 40 條的 threadpool 就是本章開頭那個事故。而且預設不回收連線、不 pre-ping，中間設備砍掉閒置連線之後會出現「每天早上第一個請求失敗」。

**「`Session` 可以放在模組層級共用。」**
不行。它不是執行緒安全的，而且會累積 identity map 造成記憶體洩漏，還會讓不同請求看到彼此未提交的資料。**`Engine` 是單例，`Session` 是每請求一個**——兩者不要搞反。

**「migration 在應用啟動時跑比較方便。」**
K8s 滾動更新會讓多個 Pod 同時啟動並同時跑 migration。要用獨立的 Job，跑完再更新 Deployment。

**「`--autogenerate` 產生的 migration 可以直接提交。」**
欄位改名會被它產生成 drop + add，正式環境跑下去資料就沒了。每一份都要人工讀過。

**「N+1 在 ORM 裡是無法避免的。」**
用 `selectinload` / `joinedload` 明確指定即可。一對多優先用 `selectinload`，避免 join 造成的列數膨脹。

---

## 十、同事會來問你的問題

**「同步還是 async SQLAlchemy？」**
先用同步配 `def`。async 的代價是整條依賴鏈都不能有同步呼叫、關聯必須全部 eager load、驅動選擇變少、stack trace 難讀。真正需要它的訊號是「單一請求要並行發多個獨立查詢」或「已經大量使用 async」，不是「因為 FastAPI 是 async 框架」。

**「連線池要開多大？」**
三條規則。一，`pool_size + max_overflow` 要跟得上 threadpool 的併發數（預設 40 對 15 就是矛盾的）。二，`worker 數 × Pod 副本數 × 池子大小` 不能超過資料庫 max connections 的八成。三，`pool_recycle` 要小於中間設備的閒置逾時，並開 `pool_pre_ping`。另外把 `pool_timeout` 從預設 30 秒調短，快速失敗比長時間等待健康。

**「`DetachedInstanceError` 是什麼意思？」**
序列化的時候才要去 lazy load 某個關聯，但 session 已經關了。修法是查詢時就用 `options(selectinload(...))` 把回應需要的關聯載入。實用紀律：`response_model` 上有什麼關聯，查詢的 `options()` 就要有對應的 loader。

**「commit 要寫在哪？」**
小專案讓 `get_db` 只負責開關與 rollback，commit 在 endpoint 裡明確寫；中大型專案交給 service 層。讓依賴自動 commit 很方便，但它會讓交易邊界變成隱性的，而且非資料庫的副作用（寄信、呼叫外部 API）不會跟著回滾，容易誤以為有原子性。

**「migration 要怎麼上正式？」**
獨立的 K8s Job 或 ArgoCD PreSync hook，跑完成功才更新 Deployment。不要在應用啟動時跑——滾動更新會有多個 Pod 同時執行。Oracle 還要多注意 DDL 隱含提交，一份 migration 跑到一半失敗是無法整段回滾的，所以要寫小一點。

**「Oracle 有什麼要特別注意的？」**
四件事：`python-oracledb` 的 thin mode 不需要 Instant Client（容器化大幅簡化）；空字串等於 NULL，NOT NULL 欄位存 `''` 會炸；`IN` 清單上限 1000，`selectinload` 產生的查詢也會撞到；DDL 隱含提交讓 migration 無法整段回滾。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[04-async-and-concurrency]] — 上一章：threadpool 的數字從哪來
- [[06-error-handling]] — 下一章：資料庫例外該怎麼轉成 HTTP 回應
- [[11-deployment]] — worker 數量與總連線數的計算
- [[oracle]] — Oracle entity 頁
- [[07-efcore-internals]] — EF Core 的對應章節（DbContext 與 change tracker）
- [[10-oracle-specifics]] — .NET 那邊的 Oracle 專章，同一組坑
