---
type: concept
domain: tech
tags: [dotnet, efcore, linq, iqueryable, n-plus-one, pagination, sql, performance]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 08 章：查詢 — LINQ 怎麼變成 SQL，以及什麼時候變不了

## 一個回應要三秒的列表 API

```csharp
[HttpGet]
public async Task<IActionResult> GetOrdersAsync()
{
    var orders = await _db.Orders.ToListAsync();

    var result = orders.Select(o => new OrderDto(
        o.Id,
        o.Customer.Name,              // 導覽屬性
        o.Items.Count,                // 集合導覽
        o.Total));

    return Ok(result);
}
```

程式碼很乾淨，測試環境（20 筆訂單）跑起來 80 毫秒。上線後有 500 筆訂單，回應時間變成三秒多，資料庫的 CPU 開始有明顯波動。

打開 SQL 記錄，會看到 **1001 條查詢**：

```sql
SELECT * FROM ORDERS;                              -- 1 條
SELECT * FROM CUSTOMERS WHERE ID = 1;              -- 第 1 筆訂單的客戶
SELECT * FROM ORDER_ITEMS WHERE ORDER_ID = 1;      -- 第 1 筆訂單的品項
SELECT * FROM CUSTOMERS WHERE ID = 2;
SELECT * FROM ORDER_ITEMS WHERE ORDER_ID = 2;
-- ... 重複 500 次
```

這是 **N+1 查詢問題**，ORM 最經典的效能陷阱。它的可怕之處在於：程式碼完全看不出來有問題，而且資料量小的時候完全不會被發現。

（順帶一提，這段程式碼在較新的 EF Core 版本可能直接拋 `NavigationBaseIncludeIgnored` 之類的警告，或者 `o.Customer` 是 null 導致 `NullReferenceException`——因為延遲載入預設是關閉的。無論哪種結果，根因都是同一個：**沒有搞清楚查詢在哪裡執行**。）

---

## 一、`IQueryable` 與延遲執行

理解 EF Core 查詢的第一件事：`DbSet<T>` 實作的是 `IQueryable<T>`，不是 `IEnumerable<T>`。

```csharp
var query = _db.Users.Where(u => u.IsActive);      // 還沒查資料庫
query = query.OrderBy(u => u.Name);                // 還沒
query = query.Take(10);                            // 還沒
var users = await query.ToListAsync();             // 這一刻才發出 SQL
```

`IQueryable` 上的每個 LINQ 方法都在**建構一棵表達式樹（expression tree）**——一個描述「你想做什麼」的資料結構。只有在需要實際結果時，EF Core 才把整棵樹翻譯成一條 SQL 送出去。

觸發執行的操作有：

| 類別 | 方法 |
| --- | --- |
| 具體化 | `ToList` / `ToArray` / `ToDictionary` |
| 取單筆 | `First` / `FirstOrDefault` / `Single` / `Last` |
| 聚合 | `Count` / `Sum` / `Max` / `Any` / `All` |
| 迭代 | `foreach`、`await foreach` |

在 EF Core 裡永遠用非同步版本（`ToListAsync`、`FirstOrDefaultAsync`），理由見第 06 章。

### 1.1 `IQueryable` 變成 `IEnumerable` 的那一刻

這是最關鍵的一條線。看這兩段：

```csharp
// A：篩選在資料庫做
var users = await _db.Users.Where(u => u.IsActive).ToListAsync();

// B：篩選在記憶體做
var users = (await _db.Users.ToListAsync()).Where(u => u.IsActive);
```

A 送出 `SELECT ... WHERE IS_ACTIVE = 1`，只傳回符合的資料。
B 送出 `SELECT * FROM USERS`——**把整張表拉進記憶體**，然後在應用程式端過濾。

一百萬列的表，B 會把一百萬列全部讀進來。這是「加了 `ToList()` 之後就沒事了」這種習慣造成的災難。

同樣的陷阱藏在方法簽章裡：

```csharp
// ❌ 回傳 IEnumerable，呼叫端後續的 Where 都在記憶體做
public IEnumerable<User> GetActiveUsers() => _db.Users.Where(u => u.IsActive);

// ✅ 保持 IQueryable，讓呼叫端能繼續組合
public IQueryable<User> GetActiveUsers() => _db.Users.Where(u => u.IsActive);
```

但 `IQueryable` 外露也有代價：呼叫端可以組出任意查詢，領域層失去對資料存取的控制，而且 DbContext 的生命週期變得隱晦（查詢在呼叫端執行時，DbContext 可能已經被 dispose）。這是 Repository 模式支持者的主要論點。折衷做法是：內部服務之間傳 `IQueryable`，跨層邊界回傳具體化的結果。

---

## 二、翻譯不了的東西

EF Core 3.0 起有一個重要的行為改變：**無法翻譯成 SQL 的表達式會直接拋例外**，而不是靜靜地退回記憶體執行。

```csharp
// ❌ InvalidOperationException: could not be translated
var users = await _db.Users
    .Where(u => IsValidUser(u))          // 自訂方法，SQL 不認識
    .ToListAsync();
```

這個改變常被抱怨（「以前能跑的現在壞了」），但它救了無數效能事故——舊版會靜默地把整張表拉進記憶體再篩選，開發者完全不知情。

常見翻譯不了的情況：

| 寫法 | 問題 | 替代 |
| --- | --- | --- |
| 自訂方法 `IsValid(u)` | SQL 不認識 | 把邏輯展開成布林運算式 |
| `u.Name.ToUpper() == x.ToUpper()` | 部分 provider 不支援 | 用 `EF.Functions.Like` 或資料庫層設定 |
| 複雜的 `GroupBy` 後投影 | 翻譯規則有限 | 拆成兩段，或用原生 SQL |
| `DateTime.Now.AddDays(-7)` 在運算式內 | 有時可翻譯，有時不行 | 先算好存進區域變數 |
| 呼叫其他實體的方法 | 同自訂方法 | 展開 |

最後一項的處理方式值得寫下來：

```csharp
// ❌ 每次比對都可能重算，也可能翻譯失敗
var recent = await _db.Orders.Where(o => o.CreatedAt > DateTime.UtcNow.AddDays(-7)).ToListAsync();

// ✅ 先算好，變成一個參數
var cutoff = DateTimeOffset.UtcNow.AddDays(-7);
var recent = await _db.Orders.Where(o => o.CreatedAt > cutoff).ToListAsync();
```

第二種寫法產生的 SQL 帶一個參數 `:p0`，而不是把時間硬編進 SQL 字串。這對查詢計畫快取很重要——參數化的 SQL 文字固定，資料庫可以重複使用執行計畫（Oracle 的 shared pool 特別在意這件事，見 [[10-oracle-specifics]]）。

要明確表達「這一段我就是要在記憶體做」，用 `AsEnumerable()` 畫出分界：

```csharp
var results = await _db.Orders
    .Where(o => o.Status == "Open")      // 資料庫端
    .ToListAsync();

var processed = results
    .Select(o => new { o.Id, Label = FormatLabel(o) });   // 記憶體端，明確
```

---

## 三、N+1：成因與四種解法

回到開頭那個問題。根因是：`orders` 已經具體化了（`ToListAsync`），之後存取 `o.Customer` 時，EF Core 必須**為每個訂單單獨去查一次**。

### 解法一：`Include`

```csharp
var orders = await _db.Orders
    .Include(o => o.Customer)
    .Include(o => o.Items)
    .ToListAsync();
```

一條 SQL（用 JOIN）帶回所有資料。但這裡有一個新問題。

### 3.1 笛卡兒爆炸

`Include` 多個**集合**導覽時，JOIN 會產生列的相乘：

```text
1 筆訂單 × 10 個品項 × 5 個付款紀錄 = 50 列
```

每一列都重複了訂單本身的所有欄位。訂單有 30 個欄位、其中有個 CLOB 備註欄位的話，那份備註會被傳輸 50 次。這叫笛卡兒爆炸（cartesian explosion），資料量大時網路傳輸會成為瓶頸。

EF Core 5 起提供分割查詢：

```csharp
var orders = await _db.Orders
    .Include(o => o.Items)
    .Include(o => o.Payments)
    .AsSplitQuery()               // 拆成多條 SQL，各自查
    .ToListAsync();
```

它產生三條 SQL（訂單、品項、付款）然後在記憶體中組裝。取捨是：

| | 單一查詢（預設） | 分割查詢 |
| --- | --- | --- |
| 往返次數 | 1 | N |
| 資料重複 | 可能爆炸 | 無 |
| 一致性 | 單一快照 | **多條查詢之間可能不一致** |
| 適合 | 單一集合導覽、資料量小 | 多個集合導覽、資料量大 |

一致性那一項要注意：分割查詢的多條 SQL 不在同一個交易快照裡（除非外層有明確交易），中間資料被改的話會組裝出不一致的結果。

### 解法二：投影（通常最好）

```csharp
var orders = await _db.Orders
    .Select(o => new OrderDto(
        o.Id,
        o.Customer.Name,          // 翻譯成 JOIN，只取這個欄位
        o.Items.Count(),          // 翻譯成子查詢或 JOIN + COUNT
        o.Total))
    .ToListAsync();
```

一條 SQL，而且**只取需要的欄位**。不需要 `Include`、不需要 `AsNoTracking`（投影結果本來就不追蹤）、沒有笛卡兒爆炸。

這是列表型 API 的首選寫法。理由很簡單：API 回傳的是 DTO，不是實體。既然最終只需要四個欄位，何必把整個實體圖載入記憶體。

### 解法三：篩選式 Include（EF Core 5+）

只要關聯資料的一部分時：

```csharp
var orders = await _db.Orders
    .Include(o => o.Items.Where(i => i.Quantity > 0).OrderBy(i => i.LineNumber))
    .ToListAsync();
```

注意：**同一個導覽只能有一個篩選條件**，而且被篩掉的資料在該 DbContext 內就永遠看不到了（因為關聯修正只會接上已載入的）。

### 解法四：顯式載入

確定只有少數幾筆需要關聯資料時：

```csharp
var order = await _db.Orders.FindAsync(id);
await _db.Entry(order).Collection(o => o.Items).LoadAsync();
```

### 3.2 為什麼延遲載入是預設關閉的

某些 ORM（包括舊版 EF）會在存取導覽屬性時自動去查資料庫——這叫延遲載入（lazy loading）。EF Core 預設**不啟用**它，需要額外安裝 proxy 套件才能開。

這是刻意的設計決定：延遲載入讓 N+1 變得**完全隱形**。一個 `foreach` 迴圈裡的 `o.Customer.Name` 看起來只是屬性存取，實際上每次都是一次資料庫往返。關掉它之後，導覽屬性沒載入就是 null，問題在開發階段就會浮現。

強烈建議不要開啟延遲載入。它省下的打字量遠不及它製造的效能問題。

---

## 四、SQL 記錄：診斷的起點

看不到 SQL 就無法診斷查詢問題。開發環境務必打開：

```csharp
builder.Services.AddDbContext<AppDbContext>(opt =>
{
    opt.UseOracle(cs);

    if (builder.Environment.IsDevelopment())
    {
        opt.EnableSensitiveDataLogging();     // 顯示參數值
        opt.EnableDetailedErrors();
        opt.LogTo(Console.WriteLine, LogLevel.Information);
    }
});
```

`EnableSensitiveDataLogging` **只能在開發環境開**——它會把參數值（含密碼、個資）寫進 log。在生產環境開啟等於把敏感資料寫進 ELK，是資料外洩事故。

生產環境要看 SQL 的話，用 logging 分類過濾：

```json
{
  "Logging": {
    "LogLevel": {
      "Microsoft.EntityFrameworkCore.Database.Command": "Information"
    }
  }
}
```

只印 SQL 文字不印參數值。長期建議搭配 EF Core 的診斷事件與 OpenTelemetry，把慢查詢做成指標而不是靠翻 log（見 [[16-logging-and-observability]]）。

單一查詢也可以直接印出來：

```csharp
var sql = _db.Orders.Where(o => o.Total > 100).ToQueryString();
```

這是 EF Core 5+ 的方法，在寫複雜查詢時比開整套 logging 方便。

---

## 五、分頁

```csharp
var page = await _db.Orders
    .OrderByDescending(o => o.CreatedAt)
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .ToListAsync();
```

翻譯成 `OFFSET ... FETCH NEXT ...`（Oracle 12c+ 支援；更舊的版本會用 `ROWNUM` 巢狀子查詢）。

三個必須知道的細節：

**必須有 `OrderBy`。** 沒有排序的分頁在關聯式資料庫裡是未定義行為——資料庫不保證每次回傳順序相同，於是第一頁和第二頁可能出現重複或遺漏的資料。EF Core 不會強制你寫，但少了它就是 bug。

**排序鍵必須唯一。** 只用 `CreatedAt` 排序，同一秒建立的多筆資料順序仍不確定。加上主鍵作為決勝鍵：

```csharp
.OrderByDescending(o => o.CreatedAt).ThenBy(o => o.Id)
```

**深分頁很慢。** `OFFSET 100000` 意味著資料庫要掃過並丟棄十萬列才開始回傳。這是 `OFFSET` 分頁的本質限制，加索引也救不了。

資料量大時改用 **keyset pagination**（游標分頁）：

```csharp
// 前端傳回上一頁最後一筆的排序鍵
var page = await _db.Orders
    .Where(o => o.CreatedAt < lastCreatedAt
             || (o.CreatedAt == lastCreatedAt && o.Id < lastId))
    .OrderByDescending(o => o.CreatedAt).ThenByDescending(o => o.Id)
    .Take(pageSize)
    .ToListAsync();
```

它靠索引直接定位，效能與頁碼無關。代價是不能跳頁（只能上一頁／下一頁），且需要前端配合傳游標。無限捲動的列表用它最合適；需要「第 57 頁」的管理後台則只能用 OFFSET，並限制最大頁數。

分頁還需要總數時：

```csharp
var query = _db.Orders.Where(o => o.Status == status);

var total = await query.CountAsync();                        // 一條 COUNT
var items = await query.OrderBy(...).Skip(...).Take(...).ToListAsync();
```

兩條查詢是正常的。注意 `query` 被重複使用——因為 `IQueryable` 是不可變的組合，每次都從頭翻譯，不會互相污染。

---

## 六、幾個具體翻譯行為

### 6.1 `Contains` 變成 `IN`

```csharp
var ids = new[] { 1, 2, 3 };
var users = await _db.Users.Where(u => ids.Contains(u.Id)).ToListAsync();
// → WHERE ID IN (1, 2, 3)
```

清單很大時要小心：Oracle 的 `IN` 清單上限是 **1000 個元素**，超過會拋 `ORA-01795`。EF Core 較新版本會參數化這個清單，但仍受資料庫限制。大量 ID 的情況要分批處理，或改用暫存表 / JOIN。

### 6.2 字串比對與大小寫

```csharp
_db.Users.Where(u => u.Name.Contains(keyword))     // → LIKE '%keyword%'
_db.Users.Where(u => u.Name.StartsWith(keyword))   // → LIKE 'keyword%'
```

`Contains` 產生前綴萬用字元的 `LIKE`，**無法使用一般索引**。搜尋功能建議用資料庫的全文檢索（Oracle Text）或外部搜尋引擎。

大小寫敏感度由資料庫定序決定，不是由 C# 決定。Oracle 預設**大小寫敏感**，所以 `Where(u => u.Name == "vic")` 找不到 `"Vic"`。用 `ToUpper()` 比對會導致索引失效（除非建了函式索引）。這在 [[10-oracle-specifics]] 展開。

### 6.3 `GroupBy` 的限制

簡單聚合能翻譯：

```csharp
var stats = await _db.Orders
    .GroupBy(o => o.Status)
    .Select(g => new { Status = g.Key, Count = g.Count(), Total = g.Sum(o => o.Total) })
    .ToListAsync();
```

但 `GroupBy` 之後想拿到「每組的完整實體清單」（`g.ToList()`）通常翻譯不了——SQL 的 `GROUP BY` 本來就不回傳明細。需要這種結果就得查回所有資料再在記憶體分組，或改用視窗函式配合原生 SQL。

### 6.4 批次更新與刪除（EF Core 7+）

```csharp
// 舊做法：查出來 → 追蹤 → 逐筆 UPDATE
var users = await _db.Users.Where(u => u.LastLogin < cutoff).ToListAsync();
foreach (var u in users) u.IsActive = false;
await _db.SaveChangesAsync();

// EF Core 7+：直接翻譯成一條 UPDATE ... WHERE
await _db.Users
    .Where(u => u.LastLogin < cutoff)
    .ExecuteUpdateAsync(s => s.SetProperty(u => u.IsActive, false));

await _db.Orders.Where(o => o.CreatedAt < old).ExecuteDeleteAsync();
```

差異巨大：不載入實體、不追蹤、一條 SQL 搞定。但要注意**它繞過 change tracker**——不觸發 `SaveChanges` 的攔截、不更新已追蹤實體的狀態、不套用並發 token 檢查。所以它適合批次維護作業，不適合需要業務規則介入的更新。

---

## 七、原生 SQL

LINQ 表達不了或效能不足時，可以直接寫 SQL：

```csharp
// 查詢，回傳實體
var users = await _db.Users
    .FromSql($"SELECT * FROM USERS WHERE DEPT_ID = {deptId}")
    .ToListAsync();

// 非查詢
await _db.Database.ExecuteSqlAsync($"UPDATE USERS SET IS_ACTIVE = 0 WHERE ID = {id}");
```

**這裡的插值字串是安全的。** `FromSql` 和 `ExecuteSql` 接受的是 `FormattableString`，EF Core 會把插值的部分轉成參數而不是字串串接。產生的是 `WHERE DEPT_ID = :p0`。

危險的是名字很像的另一組方法：

```csharp
// ❌ SQL injection
_db.Users.FromSqlRaw("SELECT * FROM USERS WHERE NAME = '" + name + "'");

// ✅ Raw 版本要自己傳參數
_db.Users.FromSqlRaw("SELECT * FROM USERS WHERE NAME = {0}", name);
```

規則：**優先用 `FromSql` / `ExecuteSql`（插值版）**。只有在 SQL 字串需要動態組合時才用 `Raw` 版本，且所有使用者輸入必須走參數。

`FromSql` 的結果仍是 `IQueryable`，可以繼續組合：

```csharp
var users = await _db.Users
    .FromSql($"SELECT * FROM USERS WHERE DEPT_ID = {deptId}")
    .Where(u => u.IsActive)         // 會包成子查詢
    .OrderBy(u => u.Name)
    .ToListAsync();
```

要回傳非實體型別，用 `SqlQuery<T>`（EF Core 8+）或改用 Dapper——後者在「大量自訂 SQL」的場景通常更順手，取捨在 [[10-oracle-specifics]] 討論。

---

## 八、常見誤解

**「加了 `ToList()` 之後再 `Where` 也一樣。」**
完全不一樣。`ToList()` 之後是記憶體篩選，意味著整張表已經被拉進應用程式。篩選條件永遠要在具體化之前。

**「`Include` 是解決 N+1 的標準答案。」**
它解決往返次數，但多個集合導覽會造成笛卡兒爆炸。列表型 API 的首選是投影（`Select`），只取需要的欄位。

**「延遲載入很方便，開起來吧。」**
它讓 N+1 完全隱形——屬性存取看起來無害，實際上每次都是一次資料庫往返。EF Core 預設關閉它是正確的。

**「`ExecuteUpdate` 就是更快的 `SaveChanges`。」**
它繞過 change tracker、不觸發攔截器、不做並發檢查。適合批次維護，不適合需要業務規則的更新。

**「參數化只是為了防 SQL injection。」**
也為了執行計畫快取。把值硬編進 SQL 文字會讓每個不同的值產生不同的 SQL 文字，資料庫無法重用執行計畫。

**「分頁不用寫 `OrderBy`，反正資料庫會照主鍵順序回。」**
沒有 `ORDER BY` 時關聯式資料庫不保證任何順序。少了它，翻頁會出現重複或遺漏的資料。

---

## 九、同事會來問你的問題

**Q：列表 API 很慢，查資料庫又看不出慢查詢。**
多半是 N+1——大量的小查詢，每條都很快但總數驚人。打開 SQL 記錄看查詢條數。解法優先順序：改成投影 `Select`；需要完整實體時用 `Include`；多個集合導覽時加 `AsSplitQuery()`。

**Q：`could not be translated` 這個錯誤怎麼修？**
表達式裡有 SQL 不認識的東西（自訂方法、複雜運算）。把邏輯展開成資料庫看得懂的運算式，或用 `AsEnumerable()` 明確畫出「這之後在記憶體做」的界線——但要確保界線之前已經篩掉大部分資料。

**Q：`Include` 兩個集合之後資料量暴增。**
笛卡兒爆炸。加 `AsSplitQuery()` 拆成多條查詢，或改用投影只取需要的欄位。注意分割查詢的多條 SQL 之間沒有一致性保證。

**Q：分頁到第 500 頁就變超慢。**
`OFFSET` 需要掃過並丟棄前面所有列，深分頁的本質限制。改用 keyset pagination（用上一頁最後一筆的排序鍵當游標），效能與頁碼無關，代價是不能跳頁。

**Q：`ids.Contains(u.Id)` 在 Oracle 上報 ORA-01795。**
`IN` 清單超過 1000 個元素。分批查詢（每批 1000 筆以下）再合併，或把 ID 寫進暫存表後 JOIN。

**Q：可以用字串串接組 SQL 嗎？只是內部系統。**
不行。`FromSqlRaw` + 字串串接是 SQL injection。用 `FromSql`（插值版，EF Core 會自動參數化）或 `FromSqlRaw` 搭配參數佔位符。內部系統一樣有風險——攻擊者拿到任一入口就能橫向移動。

**Q：`EnableSensitiveDataLogging` 可以在測試環境開嗎？**
測試環境如果有真實資料就不要開，它會把參數值寫進 log。如果測試環境只有假資料則可以，但要確認 log 不會流到共用的 ELK。

---

## 連結

- [[basics-10-efcore-and-oracle]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[07-efcore-internals]] — 上一章：change tracker 與投影不追蹤的原因
- [[09-transactions-and-concurrency]] — 下一章：交易邊界與並發控制
- [[10-oracle-specifics]] — Oracle 的分頁、大小寫、IN 上限
- [[16-logging-and-observability]] — 慢查詢的長期監控
- [[oracle]] — 資料庫 entity 頁
