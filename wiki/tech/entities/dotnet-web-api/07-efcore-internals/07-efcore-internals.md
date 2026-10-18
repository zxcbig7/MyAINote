---
type: concept
domain: tech
tags: [dotnet, efcore, dbcontext, change-tracker, orm, unit-of-work, tracking]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 07 章：EF Core 內部 — Change Tracker 到底在追蹤什麼

## 一段沒有呼叫 Update 的更新

```csharp
[HttpPut("{id}")]
public async Task<IActionResult> UpdateAsync(int id, UpdateUserDto dto)
{
    var user = await _db.Users.FindAsync(id);
    if (user is null) return NotFound();

    user.Name = dto.Name;          // 只是改了一個物件的屬性

    await _db.SaveChangesAsync();  // 沒有呼叫 Update，資料庫卻真的被改了
    return NoContent();
}
```

這段程式碼能正常運作，而且是 EF Core 的標準寫法。但它讓第一次接觸 ORM 的人非常困惑：**`_db.Users.Update(user)` 呢？為什麼不用寫也會存進去？**

同一個機制的另一面則會咬人：

```csharp
[HttpGet]
public async Task<IActionResult> GetAllAsync()
{
    var users = await _db.Users.ToListAsync();

    foreach (var u in users)
    {
        u.Name = MaskName(u.Name);       // 只是為了回應遮罩，不想存回去
    }

    // 這裡沒有 SaveChanges，看起來安全
    return Ok(users);
}
```

這段確實安全——因為沒有 `SaveChanges`。但如果這個 action 上掛了第 05 章提到的「交易 filter」，或者同一個 request 裡稍後有別的程式碼呼叫了 `SaveChanges`，這些遮罩過的名字就會被寫進資料庫。真實發生過的事故正是這個形狀：一個「只讀」的操作污染了資料。

兩個現象、一個機制：**Change Tracker**。

---

## 一、DbContext 是什麼

`DbContext` 同時扮演兩個經典模式：

**Unit of Work（工作單元）**——它累積一批變更，最後一次性提交。`SaveChanges` 是提交點，在那之前的所有修改都只存在於記憶體。

**Repository（儲存庫）**——`DbSet<T>` 提供對某個實體集合的查詢與存取。

這解釋了為什麼「再包一層 Repository 模式」在 EF Core 上是有爭議的。`DbSet<T>` 本身就是 repository，`DbContext` 本身就是 unit of work，再包一層常常只是把 `IQueryable` 的能力包掉，換來一堆 `GetByXxx` 方法。

值得包的情況是：需要隔離持久化技術以便測試或替換、需要把複雜查詢集中管理、或團隊約定領域層不得引用 EF Core。不值得的情況是：只是因為「教科書說要有 Repository」。

---

## 二、Change Tracker 與五種狀態

DbContext 內部有一個 `ChangeTracker`，記錄每一個「被追蹤的實體」及其狀態：

| 狀態 | 意義 | `SaveChanges` 時 |
| --- | --- | --- |
| `Detached` | 不被追蹤 | 什麼都不做 |
| `Unchanged` | 追蹤中，與資料庫一致 | 什麼都不做 |
| `Added` | 新實體，尚未存在於資料庫 | `INSERT` |
| `Modified` | 追蹤中，有屬性被改過 | `UPDATE`（只更新變動的欄位） |
| `Deleted` | 標記為刪除 | `DELETE` |

現在回答開頭的問題。`FindAsync` 從資料庫讀出一筆資料時，EF Core 做了兩件事：建立 `User` 物件，以及**把這個物件的所有屬性值拍一張快照（snapshot）存進 change tracker**，狀態標為 `Unchanged`。

當你寫 `user.Name = dto.Name`，EF Core 其實**當下什麼都不知道**（除非實體有實作變更通知介面）。它在 `SaveChanges` 被呼叫時，才把每個追蹤中的物件與當初的快照逐屬性比對，發現 `Name` 不一樣了，於是把狀態改成 `Modified` 並產生 `UPDATE`。

所以 `Update()` 不是必要的——**只要物件是被追蹤的**。

也因為是逐屬性比對，產生的 SQL 只更新真正變動的欄位：

```sql
UPDATE "USERS" SET "NAME" = :p0 WHERE "ID" = :p1
```

而不是把整列所有欄位都寫一遍。這在寬表（幾十個欄位）上是明顯的差異。

### 2.1 查看追蹤狀態

除錯時很有用：

```csharp
var entry = _db.Entry(user);
Console.WriteLine(entry.State);                            // Modified
Console.WriteLine(entry.Property(u => u.Name).IsModified); // true
Console.WriteLine(entry.Property(u => u.Name).OriginalValue);

// 全部追蹤中的實體
Console.WriteLine(_db.ChangeTracker.DebugView.LongView);
```

`ChangeTracker.DebugView` 是排查「為什麼多了一條 SQL」「為什麼這筆資料被改了」的第一工具。

---

## 三、Identity Map：同一筆資料只有一個物件

Change tracker 還維護一張以主鍵為索引的表。**同一個 DbContext 內，同一個主鍵永遠對應同一個物件實例。**

```csharp
var a = await _db.Users.FindAsync(1);
var b = await _db.Users.FirstAsync(u => u.Id == 1);

Console.WriteLine(ReferenceEquals(a, b));   // True——同一個物件
```

這帶來幾個實際後果。

**`FindAsync` 可能不查資料庫。** 它先檢查 identity map，找到就直接回傳，一條 SQL 都不發。這是它和 `FirstOrDefaultAsync` 的關鍵差異——後者永遠會查資料庫（但如果查到的主鍵已在追蹤中，回傳的仍是既有物件，資料庫來的新值會被丟棄）。

**讀到的可能是過期資料。** 承上，如果另一個 request 在這期間改了這筆資料，你的 DbContext 仍然回傳記憶體裡的舊版本。在 request 範圍的短生命週期裡這幾乎不成問題（第 02 章反覆強調 Scoped 的理由之一），但在長壽的 DbContext 裡就是嚴重問題。

需要強制重讀：

```csharp
await _db.Entry(user).ReloadAsync();
```

**追蹤的實體越多越慢。** 每次 `SaveChanges` 都要遍歷所有追蹤中的實體做快照比對。追蹤一萬筆時，即使只改了一筆，比對成本也是一萬筆的量級。這是下一節的動機。

---

## 四、`AsNoTracking`：什麼時候該關掉追蹤

```csharp
var users = await _db.Users.AsNoTracking().ToListAsync();
```

加上 `AsNoTracking()` 之後，EF Core 不建立快照、不放進 identity map，只是把資料庫的列轉成物件就丟給你。

好處是明確的：記憶體用量降低（沒有快照）、`SaveChanges` 不用比對它們、查詢本身也略快。在「查一大堆資料只為了回傳給前端」這種唯讀場景，這是免費的效能。

判斷規則：**查出來的資料如果不會被修改後存回去，就加 `AsNoTracking()`。**

具體到 Web API：

| 場景 | 追蹤 |
| --- | --- |
| GET 列表、GET 單筆（純回傳） | `AsNoTracking()` |
| GET 用於後續修改（先查再改再存） | 追蹤 |
| POST/PUT/DELETE 前的查詢 | 追蹤 |
| 報表、匯出、統計 | `AsNoTracking()` |
| 投影成 DTO（`Select`） | 不需要——投影結果本來就不被追蹤 |

最後一項值得展開：**投影到匿名型別或 DTO 時，結果自動不被追蹤**，因為那不是實體。

```csharp
// 這已經不被追蹤了，不需要 AsNoTracking()
var dtos = await _db.Users
    .Select(u => new UserDto(u.Id, u.Name, u.Email))
    .ToListAsync();
```

而且投影還有另一個更大的好處：SQL 只 `SELECT` 需要的欄位，不是 `SELECT *`。這在有 CLOB/BLOB 欄位的表上是數量級的差異（Oracle 的部分見 [[10-oracle-specifics]]）。所以查詢用的首選是投影，`AsNoTracking()` 是「必須拿完整實體但不想改」時的方案。

要全域改成預設不追蹤：

```csharp
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseOracle(cs)
       .UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking));
```

我不建議這樣做。它讓「先查再改」的程式碼靜默失效——改了物件、呼叫 `SaveChanges`、什麼事都沒發生、也沒有任何錯誤。這種靜默的行為改變比多打幾個 `AsNoTracking()` 危險得多。

---

## 五、`SaveChanges` 做了什麼

```csharp
await _db.SaveChangesAsync();
```

展開來是五個步驟：

```text
1. DetectChanges：遍歷所有追蹤中的實體，與快照比對，更新狀態
2. 決定順序：依外鍵相依關係排序（先 INSERT 父，再 INSERT 子）
3. 開啟交易（若尚未有交易）
4. 執行 SQL（可能批次化）
5. 提交交易；回寫資料庫產生的值（自增主鍵、計算欄位、並發 token）
```

幾個關鍵性質：

**它是原子的。** `SaveChanges` 內部自動包一個交易。一次呼叫裡的所有 INSERT/UPDATE/DELETE 要嘛全成功、要嘛全回滾。所以「同一個工作單元的所有變更放在同一次 `SaveChanges`」是重要的原則——拆成多次呼叫就變成多個交易，中間失敗會留下不一致的狀態。

**它會批次化。** EF Core 會把多筆操作合併成較少的往返（round trip）。批次大小由 provider 決定。這是為什麼「迴圈裡每次都 `SaveChanges`」效能很差——一千筆資料呼叫一千次，就是一千個交易、一千次網路往返：

```csharp
// ❌ 一千個交易
foreach (var item in items)
{
    _db.Items.Add(item);
    await _db.SaveChangesAsync();
}

// ✅ 一個交易，批次送出
_db.Items.AddRange(items);
await _db.SaveChangesAsync();
```

**它會回寫。** 資料庫產生的值（自增 ID、`DEFAULT` 欄位、觸發器改的值）會被讀回填進物件。所以 `SaveChanges` 之後 `user.Id` 才有值：

```csharp
var user = new User { Name = "Vic" };
_db.Users.Add(user);
Console.WriteLine(user.Id);          // 0 或負的臨時值
await _db.SaveChangesAsync();
Console.WriteLine(user.Id);          // 資料庫產生的真實 ID
```

在 `SaveChanges` 之前，EF Core 給新實體一個**臨時鍵值**（負數），用來在記憶體中建立關聯。這是為什麼可以在存檔前就把父子物件關聯起來——臨時鍵在儲存時會被替換成真實值並修正所有參考。

---

## 六、關聯與導覽屬性

```csharp
public class Order
{
    public int Id { get; set; }
    public int CustomerId { get; set; }
    public Customer Customer { get; set; } = null!;      // 導覽屬性
    public List<OrderItem> Items { get; set; } = new();  // 集合導覽
}
```

### 6.1 關聯修正（fix-up）

EF Core 會自動把追蹤中的實體「接起來」：

```csharp
var order = await _db.Orders.FirstAsync(o => o.Id == 1);
Console.WriteLine(order.Customer);        // null——還沒載入

var customer = await _db.Customers.FindAsync(order.CustomerId);
Console.WriteLine(order.Customer);        // 不是 null 了！
```

第二個查詢載入 Customer 之後，change tracker 發現「這個 Customer 的主鍵等於那個 Order 的外鍵」，於是自動把 `order.Customer` 填上。這叫關聯修正。

它很方便，但也是「為什麼有時候導覽屬性有值、有時候沒有」這種不確定感的來源。要明確控制，就用顯式載入（`Include`），見 [[08-efcore-query]]。

### 6.2 用外鍵還是導覽屬性

```csharp
// 方式 A：設外鍵
var order = new Order { CustomerId = 5, Total = 100 };

// 方式 B：設導覽屬性
var customer = await _db.Customers.FindAsync(5);
var order = new Order { Customer = customer, Total = 100 };
```

方式 A 少一次查詢，在只知道 ID 的情況下更直接。方式 B 在需要驗證「這個 customer 真的存在」時比較自然（但那也可以用 `AnyAsync` 檢查）。

實務建議：**實體上同時保留外鍵屬性與導覽屬性**。只有導覽屬性的話，每次建立關聯都被迫載入完整的關聯實體。

### 6.3 串聯刪除

刪除父實體時子實體怎麼辦，由關聯的 `DeleteBehavior` 決定：

| 行為 | 效果 |
| --- | --- |
| `Cascade` | 一併刪除子實體（必要外鍵的預設） |
| `ClientSetNull` | 子實體外鍵設為 null（可選外鍵的預設） |
| `Restrict` | 有子實體就拒絕刪除 |
| `NoAction` | 交給資料庫處理 |

重點是：**這些行為由 EF Core 在記憶體中執行，前提是子實體已被載入。** 如果子實體沒載入，EF Core 不知道它們存在，`Cascade` 也不會發生——最終由資料庫的外鍵約束決定，可能直接拋出違反約束的錯誤。

刪除有關聯的資料時，要嘛先 `Include` 子實體、要嘛在資料庫層設好 `ON DELETE CASCADE`，不能假設 EF Core 會自己處理。

---

## 七、斷開情境（Disconnected）

Web API 的本質是**無狀態**的：一個 request 查出資料回給前端，DbContext 就 dispose 了；下一個 request 帶著修改過的資料回來，那是一個全新的 DbContext，完全不認識這個物件。

這就是斷開情境，處理方式與「查出來改再存」不同。

```csharp
[HttpPut("{id}")]
public async Task<IActionResult> UpdateAsync(int id, UpdateUserDto dto)
{
    // 方式 A：先查再改（推薦）
    var user = await _db.Users.FindAsync(id);
    if (user is null) return NotFound();

    user.Name = dto.Name;
    user.Email = dto.Email;
    await _db.SaveChangesAsync();
    return NoContent();
}
```

```csharp
// 方式 B：直接 Update（少一次查詢，但有代價）
var user = new User { Id = id, Name = dto.Name, Email = dto.Email };
_db.Users.Update(user);
await _db.SaveChangesAsync();
```

`Update()` 的語意是「附加這個物件並把**所有屬性**標為 Modified」。代價有三個：

1. 產生的 SQL 更新**每一個**欄位，即使只改了一個
2. DTO 沒有的欄位會被寫成預設值——`CreatedAt` 變成 `0001-01-01`、`PasswordHash` 變成 null。**這是實務上最常見的資料損毀來源之一**
3. 資料不存在時不會回 404，而是拋出「更新影響了 0 列」的並發例外

所以方式 A 幾乎總是正確的選擇。多一次查詢換來的是欄位安全與明確的 404 語意。只有在確定 DTO 涵蓋所有欄位、且效能真的關鍵時才考慮方式 B。

要精確控制更新哪些欄位：

```csharp
var user = new User { Id = id };
_db.Users.Attach(user);                            // 附加，狀態 Unchanged
user.Name = dto.Name;                              // 只有這個被標為 Modified
await _db.SaveChangesAsync();
```

`Attach` 與 `Update` 的差別就在初始狀態：前者 `Unchanged`（之後的修改才會被偵測），後者 `Modified`（全部欄位）。

---

## 八、DbContext 的生命週期與效能

第 02 章從 DI 角度講過「DbContext 必須 Scoped」。這裡補上 EF Core 這一側的理由：

- **非執行緒安全**：change tracker 是普通的字典，並行存取會損毀或拋 `A second operation was started`
- **change tracker 會累積**：長壽的 DbContext 追蹤的實體只增不減，是標準的記憶體洩漏
- **identity map 會過期**：越活越久，讀到的快取資料越可能與資料庫不一致

### 8.1 DbContext Pooling

建立 DbContext 有固定成本（初始化內部服務、建立 change tracker）。高吞吐場景可以啟用池化：

```csharp
builder.Services.AddDbContextPool<AppDbContext>(opt => opt.UseOracle(cs));
```

它保留一組 DbContext 實例重複使用，每次歸還時重置狀態（清空 change tracker）而不是丟棄。

限制是：**DbContext 不能有自訂的 request 狀態**。因為實例會被重複使用，如果你在建構子注入了「當前使用者」這種東西並存成欄位，第二個 request 拿到的會是第一個 request 的值——一個嚴重且極難察覺的資料外洩。

用池化的前提是 DbContext 只依賴設定，不依賴當前請求。多租戶（每個請求連不同資料庫）的場景通常不能用。

### 8.2 `IDbContextFactory`

需要在單一請求中同時使用多個 DbContext（並行查詢、或第 02 章的背景服務）時：

```csharp
builder.Services.AddDbContextFactory<AppDbContext>(opt => opt.UseOracle(cs));

public class ReportService
{
    private readonly IDbContextFactory<AppDbContext> _factory;

    public async Task<Report> BuildAsync(CancellationToken ct)
    {
        // 兩個獨立的 DbContext，可以真正並行
        await using var db1 = await _factory.CreateDbContextAsync(ct);
        await using var db2 = await _factory.CreateDbContextAsync(ct);

        var salesTask = db1.Sales.CountAsync(ct);
        var ordersTask = db2.Orders.CountAsync(ct);

        await Task.WhenAll(salesTask, ordersTask);
        return new Report(salesTask.Result, ordersTask.Result);
    }
}
```

這是第 06 章「並行查詢會拋 `A second operation was started`」的正解。注意兩個 DbContext 意味著兩條資料庫連線與兩個獨立交易——如果需要一致性快照，這樣做反而是錯的。並行查詢適用於彼此獨立的統計，不適用於必須看到同一時間點的關聯資料。

---

## 九、常見誤解

**「改了物件要呼叫 `Update()` 才會存進去。」**
只要物件是被追蹤的，`SaveChanges` 就會透過快照比對偵測到變更。`Update()` 是給斷開情境用的，而且它會把所有欄位標為已修改。

**「`AsNoTracking()` 是效能微調，可有可無。」**
在唯讀查詢上它省下快照建立與 `SaveChanges` 的比對成本，資料量大時差異明顯。更重要的是它防止「唯讀操作意外寫回資料庫」。

**「`FindAsync` 和 `FirstOrDefaultAsync` 一樣。」**
`FindAsync` 會先查 identity map，命中就不發 SQL；`FirstOrDefaultAsync` 一定查資料庫。前者只能用主鍵查。

**「`Update()` 比先查再改有效率。」**
它省一次 SELECT，但會更新所有欄位，且 DTO 沒帶到的欄位會被寫成預設值造成資料損毀。除非確定涵蓋所有欄位，否則先查再改。

**「DbContext 建立很貴，應該重複使用。」**
建立成本不高（要更省就用 pooling）。長壽的 DbContext 帶來的執行緒安全問題、記憶體累積、快取過期，代價遠大於節省的建立成本。

**「EF Core 會自動處理串聯刪除。」**
只對**已載入**的子實體有效。沒載入的話 EF Core 不知道它們存在，最終由資料庫的外鍵約束決定，通常是拋錯。

---

## 十、同事會來問你的問題

**Q：我沒呼叫 `SaveChanges`，資料怎麼被改了？**
同一個 request 裡別處呼叫了 `SaveChanges`（可能在 filter 或 service 裡），而你修改的物件正被同一個 DbContext 追蹤。追蹤中的物件只要被改過，任何一次 `SaveChanges` 都會把它寫出去。唯讀查詢加 `AsNoTracking()` 可以徹底避免。

**Q：更新之後 `CreatedAt` 變成 `0001-01-01` 了。**
用了 `_db.Update(entity)` 搭配只有部分欄位的 DTO。`Update` 把所有欄位標為 Modified，DTO 沒帶到的就寫成 CLR 預設值。改成先 `FindAsync` 查出實體再逐欄位賦值。

**Q：迴圈裡插一千筆很慢。**
迴圈內每次都呼叫 `SaveChanges` 就是一千個交易、一千次往返。改成 `AddRange` 後呼叫一次 `SaveChanges`。資料量更大（十萬筆以上）時考慮批次工具或原生批次插入。

**Q：兩個查詢用 `Task.WhenAll` 為什麼炸？**
同一個 DbContext 不支援並行操作。用 `IDbContextFactory` 建立兩個獨立實例，但要意識到那是兩條連線、兩個交易。

**Q：查出來的資料是舊的，資料庫明明已經改了。**
identity map 的效果——同一個 DbContext 內同一主鍵回傳同一個物件實例，不會用資料庫的新值覆蓋。用 `Entry(x).ReloadAsync()` 強制重讀，或確認 DbContext 沒有活過一個 request 的範圍。

**Q：`AddDbContextPool` 可以直接換上去嗎？**
先確認 DbContext 沒有 request 相關的狀態欄位（當前使用者、租戶 ID）。實例會被重複使用，這類狀態會跨請求殘留，造成資料外洩。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[06-async-and-threading]] — 上一章：為什麼 DbContext 不能並行
- [[08-efcore-query]] — 下一章：LINQ 怎麼變成 SQL
- [[02-dependency-injection]] — DbContext 的生命週期與 captive dependency
- [[09-transactions-and-concurrency]] — 交易邊界與並發控制
- [[10-oracle-specifics]] — Oracle provider 的特殊行為
- [[oracle]] — 資料庫 entity 頁
