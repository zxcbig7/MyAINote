---
type: concept
domain: tech
tags: [dotnet, efcore, oracle, provider, dapper, clob, sequence, migration]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 10 章：Oracle 特有問題 — EF Core 遇上大寫世界

## 教學文件不會告訴你的事

網路上的 EF Core 教學九成是用 SQL Server 或 SQLite 寫的。這造成一個實際問題：**很多「標準做法」在 Oracle 上不成立或行為不同**。

最典型的幾個：

- `[Timestamp]` 並發控制——SQL Server 專屬，Oracle 沒有（第 09 章已處理）
- 查詢 `WHERE Name = 'vic'` 找不到 `'Vic'`——Oracle 預設大小寫敏感
- 存進去空字串，讀出來變 null——Oracle 把空字串當 NULL
- `ids.Contains(...)` 超過 1000 個直接報錯
- `bool` 欄位在資料庫是 `NUMBER(1)`，DBA 看不懂那是什麼
- Migration 產生的表名帶雙引號，SQL*Plus 手動查詢時必須也帶引號

這一章把這些一次講完。**版本行為請以自己環境的實測為準**——Oracle 的版本差異（11g / 12c / 19c / 21c）與 provider 版本組合很多，這裡標注的門檻是常見情況，落地前值得用 `SELECT * FROM v$version` 確認。

---

## 一、Provider 與連線

Oracle 官方的 EF Core provider 是 `Oracle.EntityFrameworkCore`：

```csharp
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseOracle(builder.Configuration.GetConnectionString("Default")));
```

連線字串有兩種主要寫法。**Easy Connect**（不需要 tnsnames.ora，容器環境的首選）：

```text
User Id=APPUSER;Password=xxx;Data Source=oracle-host:1521/ORCLPDB1
```

**完整描述子**（需要指定更多連線參數時）：

```text
User Id=APPUSER;Password=xxx;Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=oracle-host)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=ORCLPDB1)))
```

容器化部署時優先用 Easy Connect——它是一行字串，可以乾淨地放進 K8s Secret，不需要額外掛載設定檔。

### 1.1 Schema 就是 User

這是 Oracle 與 SQL Server 心智模型上最大的差異之一。SQL Server 的 database 和 schema 是兩層獨立概念；**Oracle 的 schema 基本上等同於 user**——`APPUSER` 這個使用者擁有的所有物件就構成 `APPUSER` schema。

所以 EF Core 裡的 `HasDefaultSchema` 對應的是使用者名稱：

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.HasDefaultSchema("APPUSER");
}
```

不指定的話，物件建在連線使用者自己的 schema 下。跨 schema 存取需要明確授權（`GRANT SELECT ON OTHER.TABLE TO APPUSER`），這在多應用共用資料庫的企業環境很常見。

### 1.2 連線池

連線字串可以直接控制池化行為：

```text
...;Pooling=true;Min Pool Size=5;Max Pool Size=100;Connection Timeout=15
```

`Min Pool Size` 設大於 0 可以避免「第一個請求特別慢」（建立 Oracle 連線的成本不低）。但要注意這個數字乘上 Pod 副本數就是資料庫端的連線數——三個副本、每個最少 5 條，就是 15 條常駐連線。資料庫的 `processes` 參數有上限，擴展副本前要跟 DBA 確認。

---

## 二、識別碼大小寫：最容易踩的坑

Oracle 的規則是：**未加引號的識別碼一律轉成大寫**。

```sql
CREATE TABLE users (id NUMBER);     -- 實際建出來的是 USERS 表、ID 欄位
SELECT * FROM Users;                -- 可以，因為也被轉成 USERS
```

但**加了雙引號就變成大小寫敏感**：

```sql
CREATE TABLE "Users" ("Id" NUMBER); -- 建出來就是 Users，區分大小寫
SELECT * FROM Users;                -- ❌ ORA-00942: table or view does not exist
SELECT * FROM "Users";              -- ✅ 必須帶引號
```

而 EF Core 的 Oracle provider **會為識別碼加引號**。於是預設情況下，C# 的 `public DbSet<User> Users` 會建出一個叫做 `Users`（混合大小寫）的表，之後任何人用 SQL*Plus 手動查詢都必須寫 `SELECT * FROM "Users"`。

這會讓 DBA 很不高興，也讓所有既有的維運腳本失效。標準做法是**明確指定全大寫的名稱**：

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<User>(e =>
    {
        e.ToTable("USERS");
        e.Property(u => u.Id).HasColumnName("ID");
        e.Property(u => u.Name).HasColumnName("NAME");
        e.Property(u => u.CreatedAt).HasColumnName("CREATED_AT");
    });
}
```

逐欄位寫很囉唆。既有資料庫（database-first）的情況下用 scaffold 產生就好；新建資料庫（code-first）則可以寫一個慣例統一轉換：

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    foreach (var entity in modelBuilder.Model.GetEntityTypes())
    {
        entity.SetTableName(ToUpperSnake(entity.GetTableName()!));

        foreach (var property in entity.GetProperties())
        {
            property.SetColumnName(ToUpperSnake(property.Name));
        }

        foreach (var key in entity.GetKeys())
        {
            key.SetName(ToUpperSnake(key.GetName()!));
        }

        foreach (var fk in entity.GetForeignKeys())
        {
            fk.SetConstraintName(ToUpperSnake(fk.GetConstraintName()!));
        }
    }
}

// UserProfile → USER_PROFILE
private static string ToUpperSnake(string name) =>
    string.Concat(name.Select((c, i) =>
        i > 0 && char.IsUpper(c) ? "_" + c : c.ToString())).ToUpperInvariant();
```

記得索引與約束名稱也要一起處理——它們同樣受引號規則影響。

### 2.1 名稱長度限制

Oracle **12.2 之前**的識別碼上限是 **30 個字元**，12.2 起放寬到 128。

如果目標環境是 11g 或 12.1，EF Core 自動產生的名稱很容易超標：

```text
IX_OrderItems_OrderId_ProductId_CreatedAt   → 43 字元，11g 上直接失敗
FK_OrderItems_Orders_OrderId                → 28 字元，剛好過關
```

錯誤是 `ORA-00972: identifier is too long`，而且它在執行 migration 時才出現。目標環境是舊版時，所有索引與外鍵都要明確命名：

```csharp
e.HasIndex(x => new { x.OrderId, x.ProductId }).HasDatabaseName("IX_OI_ORD_PROD");
```

---

## 三、型別對應

| C# | Oracle | 注意 |
| --- | --- | --- |
| `int` | `NUMBER(10)` | |
| `long` | `NUMBER(19)` | |
| `decimal` | `NUMBER(p,s)` | **務必明確指定精度** |
| `bool` | `NUMBER(1)` | Oracle 沒有布林欄位型別（23c 前） |
| `string` | `NVARCHAR2(2000)` 或 `CLOB` | 長度未指定時的行為要確認 |
| `DateTime` | `TIMESTAMP(7)` | |
| `DateTimeOffset` | `TIMESTAMP(7) WITH TIME ZONE` | 推薦 |
| `Guid` | `RAW(16)` | 查詢時人不可讀 |
| `byte[]` | `BLOB` 或 `RAW` | |

### 3.1 `decimal` 一定要指定精度

不指定的話，provider 會選一個預設精度，而 Oracle 的 `NUMBER` 預設可以存非常大的數，兩邊對不上時會出現靜默的精度遺失或溢位例外。

```csharp
e.Property(o => o.Total).HasPrecision(18, 2);
// 或 e.Property(o => o.Total).HasColumnType("NUMBER(18,2)");
```

金額欄位尤其重要。`float`/`double` 絕對不要拿來存金額——二進位浮點數無法精確表示 0.1，累加會產生誤差。這不是 Oracle 的問題，是浮點數的本質。

### 3.2 `bool` 是 `NUMBER(1)`

Oracle 直到 23c 才有原生 `BOOLEAN` 欄位型別。在那之前，`bool` 映射成 `NUMBER(1)`，`true` 是 1、`false` 是 0。

實務影響：DBA 或報表工具看到的是數字欄位，需要在資料字典或註解裡說明語意。如果既有資料庫用的是 `CHAR(1)` 存 `'Y'`/`'N'`（Oracle 世界的常見慣例），要寫轉換器：

```csharp
e.Property(u => u.IsActive)
    .HasConversion(
        v => v ? "Y" : "N",
        v => v == "Y")
    .HasColumnType("CHAR(1)");
```

值轉換器（value converter）是對接既有 Oracle schema 的關鍵工具。要注意它的代價：**轉換後的欄位在查詢中無法有效使用索引的情況變多**，因為 EF Core 必須把 C# 端的值轉成資料庫端的表示才能比對——簡單的相等比較沒問題，但範圍查詢或函式運算可能翻譯不出來。

### 3.3 空字串就是 NULL

這是 Oracle 最著名的特性：**`''` 與 `NULL` 在 Oracle 裡是同一件事**。

```csharp
user.Nickname = "";
await _db.SaveChangesAsync();

var reloaded = await _db.Users.FindAsync(user.Id);
Console.WriteLine(reloaded.Nickname is null);    // True——存進去的空字串變成 null
```

後果：

- C# 的 `""` 存進去、讀出來變 `null`，如果屬性宣告是不可為 null 的 `string`，就會出現「宣告說不會 null 但實際上是 null」的狀況
- `WHERE NICKNAME = ''` 永遠不會匹配任何列（要用 `IS NULL`）
- 依賴「空字串與 null 語意不同」的業務邏輯在 Oracle 上會壞掉

處理方式是在應用層統一：進資料庫前把 `""` 正規化成 `null`，讀出來後把 `null` 正規化成 `""`（如果業務需要）。**不要在兩種表示之間搖擺**，選一種並貫徹。

### 3.4 CLOB 的效能陷阱

大文字欄位映射成 `CLOB`。它的讀取成本遠高於 `VARCHAR2`——CLOB 資料存在獨立的區段，讀取需要額外的往返。

於是這種查詢會意外地慢：

```csharp
// ❌ SELECT * 會把 CLOB 也讀出來
var orders = await _db.Orders.Where(o => o.Status == "Open").ToListAsync();
```

即使根本不需要那個備註欄位。解法是第 08 章的投影：

```csharp
// ✅ 只讀需要的欄位，CLOB 不會被碰到
var orders = await _db.Orders
    .Where(o => o.Status == "Open")
    .Select(o => new OrderListDto(o.Id, o.CustomerName, o.Total))
    .ToListAsync();
```

這是「列表查詢用投影」這條原則在 Oracle 上收益最大的地方。有 CLOB 欄位的表，投影與否可能差好幾倍。

`VARCHAR2` 在 Oracle 的上限是 4000 位元組（開啟擴展模式後 32767）。超過就必須用 CLOB。設計 schema 時值得多想一下：真的需要無限長度嗎？加個 `HasMaxLength(2000)` 讓它留在 `VARCHAR2` 通常是更好的選擇。

---

## 四、主鍵生成

### 4.1 IDENTITY（12c+）

```csharp
e.Property(u => u.Id).ValueGeneratedOnAdd();
```

在 12c 以上會產生 `GENERATED BY DEFAULT AS IDENTITY`，行為接近 SQL Server 的自增欄位。這是新專案的首選。

### 4.2 序列 + 觸發器（傳統做法）

11g 沒有 IDENTITY，傳統做法是序列配觸發器：

```sql
CREATE SEQUENCE USERS_SEQ START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER USERS_BI
BEFORE INSERT ON USERS FOR EACH ROW
BEGIN
  IF :NEW.ID IS NULL THEN
    SELECT USERS_SEQ.NEXTVAL INTO :NEW.ID FROM DUAL;
  END IF;
END;
```

用 EF Core 對接既有的這種 schema 時，關鍵是要讓 EF Core 知道「這個值是資料庫產生的」：

```csharp
e.Property(u => u.Id).ValueGeneratedOnAdd();
```

否則 EF Core 會把 C# 端的 0 當成有效值送進去。

也可以讓 EF Core 直接使用序列而不透過觸發器：

```csharp
modelBuilder.HasSequence<int>("USERS_SEQ").StartsAt(1).IncrementsBy(1);
e.Property(u => u.Id).HasDefaultValueSql("USERS_SEQ.NEXTVAL");
```

### 4.3 序列的快取與跳號

Oracle 序列預設有快取（通常 20），意味著**編號會跳**：資料庫重啟或 RAC 節點切換時，快取中未使用的號碼直接丟棄。

如果業務要求「單據號碼連續不可跳號」，序列**不能**用來產生它。那需要一張獨立的號碼表配合鎖，或接受「編號唯一但不連續」的設計。這是實務上常見的需求誤解——技術上能做到連續，但代價是所有插入操作序列化，吞吐量大幅下降。

---

## 五、查詢層面的差異

### 5.1 分頁

`Skip`/`Take` 在 **12c+** 翻譯成 `OFFSET ... ROWS FETCH NEXT ... ROWS ONLY`。更舊的版本會產生巢狀的 `ROWNUM` 子查詢——功能一樣但可讀性差、某些情況執行計畫也較差。

第 08 章講的所有分頁原則（必須有 `ORDER BY`、排序鍵要唯一、深分頁改用 keyset）在 Oracle 上完全適用，而且深分頁的代價更明顯。

### 5.2 大小寫敏感比對

Oracle 預設的比對是**大小寫敏感**的：

```csharp
_db.Users.Where(u => u.Name == "vic")     // 找不到 "Vic"
```

常見解法與各自的代價：

```csharp
// 方式 A：兩邊都轉大寫——索引失效（除非建函式索引）
_db.Users.Where(u => u.Name.ToUpper() == keyword.ToUpperInvariant())

// 方式 B：建函式索引，讓方式 A 能用索引
// CREATE INDEX IX_USERS_NAME_UPPER ON USERS (UPPER(NAME));

// 方式 C：資料庫層設定不分大小寫的排序規則（session 或 column 層級）
// 影響範圍大，要跟 DBA 確認
```

實務上方式 A + B 的組合最常見。要注意函式索引必須與查詢中的函式**完全一致**才會被使用——`UPPER(NAME)` 的索引救不了 `LOWER(NAME)` 的查詢。

### 5.3 `IN` 清單上限 1000

```csharp
var ids = GetTenThousandIds();
var users = await _db.Users.Where(u => ids.Contains(u.Id)).ToListAsync();
// ORA-01795: maximum number of expressions in a list is 1000
```

處理方式：

```csharp
// 分批
var results = new List<User>();
foreach (var batch in ids.Chunk(1000))
{
    results.AddRange(await _db.Users.Where(u => batch.Contains(u.Id)).ToListAsync());
}
```

批次很多時（幾萬筆 ID），更好的做法是把 ID 寫進全域暫存表（GTT）後 JOIN，一次查完。這需要原生 SQL 配合，但避免了 N 次往返。

### 5.4 綁定變數與執行計畫

Oracle 對 SQL 文字的重用非常敏感。硬編值的 SQL：

```sql
SELECT * FROM ORDERS WHERE ID = 1
SELECT * FROM ORDERS WHERE ID = 2
```

是兩條**不同**的 SQL，各自佔用 shared pool 中的一個游標、各自做一次硬解析（hard parse）。高頻查詢這樣寫會造成 shared pool 碎片化與閂鎖競爭。

EF Core 預設會把查詢中的變數參數化，產生 `WHERE ID = :p0`，這正是我們要的。但有兩種情況會退化成常數：

```csharp
// 常數直接寫在運算式裡 → 可能被內嵌成常數
_db.Orders.Where(o => o.Status == "Open")

// 用區域變數 → 一定參數化
var status = "Open";
_db.Orders.Where(o => o.Status == status);
```

實際行為取決於 EF Core 版本與運算式形態。高頻查詢建議用區域變數並用 `ToQueryString()` 確認產生的 SQL 帶的是 `:p0` 而不是字面值。

---

## 六、Migration 的實務問題

`dotnet ef migrations add` 在 Oracle 上可以運作，但企業環境常常不允許應用程式直接改 schema——DBA 要審核每一段 DDL。

務實的流程是**用 migration 產生 SQL 腳本，交給 DBA 執行**：

```powershell
dotnet ef migrations script --idempotent --output migrate.sql
dotnet ef migrations script 20260801_Prev 20260814_Next --output delta.sql
```

`--idempotent` 產生的腳本會檢查每個 migration 是否已套用，可以重複執行。

另外三個實務注意事項：

**應用程式啟動時不要自動 `Migrate()`。** 第 00 章提過：多副本同時啟動會有多個程序搶著改 schema。把它做成獨立的 Job 或 initContainer，或者交給 DBA 手動執行。

**Oracle 的 DDL 是隱含提交的。** 每一句 `CREATE`/`ALTER` 都會提交當前交易，所以 migration 失敗時**無法整段回滾**——會停在中間的某個狀態。這與 SQL Server 或 PostgreSQL 的行為不同。所以 Oracle 上的 migration 要寫得可以重複執行，並且事先在測試環境驗證過。

**Down migration 幾乎不可靠。** 理論上 EF Core 能產生降版腳本，但實際上「刪掉一個欄位」是不可逆的資料損失。生產環境的正確做法是永遠向前修（roll forward）——出問題就發一個新的 migration 修正，而不是回滾。

---

## 七、什麼時候該離開 EF Core

EF Core 不是所有場景的答案。以下情況值得考慮 Dapper 或直接 ADO.NET：

| 場景 | 理由 |
| --- | --- |
| 複雜報表查詢 | 多層 CTE、視窗函式、`CONNECT BY` 階層查詢，LINQ 表達不出或翻譯很糟 |
| 呼叫既有預存程序 | 企業 Oracle 環境有大量 PL/SQL 資產，EF Core 對 out 參數與 ref cursor 的支援有限 |
| 極高頻的簡單查詢 | Dapper 的物件對應開銷比 EF Core 低 |
| 批次資料處理 | Oracle 的陣列繫結（array binding）能一次送出上萬筆，EF Core 的批次能力不及 |

```csharp
// Dapper 範例：複雜查詢直接寫 SQL
using var conn = new OracleConnection(cs);
var results = await conn.QueryAsync<ReportRow>(@"
    SELECT DEPT_ID, COUNT(*) AS CNT,
           RANK() OVER (ORDER BY COUNT(*) DESC) AS RNK
    FROM EMPLOYEES
    WHERE HIRE_DATE >= :cutoff
    GROUP BY DEPT_ID", new { cutoff });
```

**兩者可以共存**，而且這是很常見的組合：EF Core 負責 CRUD 與領域模型的一致性，Dapper 負責報表與複雜查詢。共用同一個連線字串沒有問題；如果需要在同一個交易裡混用，要把 EF Core 的 `DbConnection` 拿出來給 Dapper 用：

```csharp
var conn = _db.Database.GetDbConnection();
var tx = _db.Database.CurrentTransaction?.GetDbTransaction();
var rows = await conn.QueryAsync<Row>(sql, param, tx);
```

呼叫預存程序時，如果它回傳 ref cursor，需要用 `OracleParameter` 明確指定型別：

```csharp
var cursor = new OracleParameter("p_result", OracleDbType.RefCursor,
                                 ParameterDirection.Output);
```

這類程式碼用 Dapper 或原生 ADO.NET 寫比在 EF Core 裡繞路乾淨得多。

---

## 八、常見誤解

**「EF Core 的 Oracle provider 跟 SQL Server 版本用法一樣。」**
大部分 API 一樣，但識別碼大小寫、空字串語意、`bool` 型別、並發 token、`IN` 上限、DDL 隱含提交都不同。照抄 SQL Server 教學會踩坑。

**「表名不用管，EF Core 會處理。」**
provider 會加引號，產生混合大小寫的表名，導致所有手寫 SQL 都必須帶引號。務必明確指定全大寫名稱或寫慣例統一轉換。

**「空字串和 null 是兩回事。」**
在 Oracle 裡是同一回事。存進 `""` 讀出來是 `null`，`WHERE X = ''` 永遠不匹配。要在應用層統一正規化。

**「`decimal` 不指定精度也沒關係。」**
會用預設精度，可能與資料庫端不一致造成靜默的精度遺失。金額欄位一定要 `HasPrecision`。

**「序列可以拿來當連續單號。」**
序列有快取，資料庫重啟或 RAC 切換會跳號。要連續號碼得用別的機制，且要接受吞吐量下降。

**「Migration 失敗可以回滾。」**
Oracle 的 DDL 隱含提交，失敗會停在中間狀態無法整段回滾。腳本要能重複執行，且必須先在測試環境驗證。

---

## 九、同事會來問你的問題

**Q：SQL*Plus 查 `SELECT * FROM USERS` 說表不存在，但 API 明明跑得好好的。**
EF Core 建的表名帶引號、是混合大小寫的 `Users`。要嘛查詢時寫 `SELECT * FROM "Users"`，要嘛（更好）在 `OnModelCreating` 統一把表名與欄位名指定為全大寫。

**Q：存了空字串，讀出來是 null，是 bug 嗎？**
是 Oracle 的行為，不是 bug。Oracle 把 `''` 視同 `NULL`。在應用層統一正規化，並且不要設計依賴「空字串 ≠ null」的業務邏輯。

**Q：列表查詢很慢，但同樣的 SQL 手動執行很快。**
檢查表上有沒有 CLOB 欄位。EF Core 查完整實體會 `SELECT` 所有欄位包含 CLOB，成本遠高於手動查的那幾個欄位。改用投影 `Select` 只取需要的欄位。

**Q：`ORA-00972: identifier is too long`。**
目標資料庫是 12.2 之前的版本，識別碼上限 30 字元，而 EF Core 自動產生的索引或外鍵名稱超標。明確用 `HasDatabaseName` 指定短名稱。

**Q：可以在應用程式啟動時跑 `Database.Migrate()` 嗎？**
不建議。多副本會同時搶著改 schema，且 Oracle 的 DDL 隱含提交，失敗會停在中間狀態。改用獨立的 Job、initContainer，或產生腳本交給 DBA。

**Q：這個報表查詢用 LINQ 寫不出來怎麼辦？**
用 Dapper 或 `FromSql` 直接寫 SQL。EF Core 與 Dapper 共存是常見且健康的組合——EF Core 管 CRUD 與領域模型，Dapper 管複雜查詢與預存程序。需要同一交易時把 `DbConnection` 和 `DbTransaction` 傳給 Dapper。

**Q：DBA 說我們的應用程式造成 shared pool 競爭。**
檢查產生的 SQL 是不是帶了字面值而非綁定變數。用 `ToQueryString()` 看看條件是 `:p0` 還是硬編的值；把條件值放進區域變數通常能讓 EF Core 參數化。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[09-transactions-and-concurrency]] — 上一章：Oracle 的隔離級別與並發 token
- [[11-authentication]] — 下一章：認證的 scheme 模型
- [[08-efcore-query]] — 投影、分頁、參數化的通則
- [[oracle]] — Oracle entity 頁
