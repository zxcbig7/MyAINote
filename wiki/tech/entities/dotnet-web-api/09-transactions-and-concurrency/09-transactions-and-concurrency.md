---
type: concept
domain: tech
tags: [dotnet, efcore, transaction, concurrency, isolation-level, optimistic-locking, outbox]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 09 章：交易與並發 — 兩個人同時按下按鈕的時候

## 只剩一張票，兩個人同時買

```csharp
[HttpPost("{id}/purchase")]
public async Task<IActionResult> PurchaseAsync(int id)
{
    var ticket = await _db.Tickets.FindAsync(id);
    if (ticket is null) return NotFound();

    if (ticket.Remaining <= 0)
    {
        return Conflict("票已售完");
    }

    ticket.Remaining -= 1;
    await _db.SaveChangesAsync();

    return Ok();
}
```

這段程式碼在單人操作時完全正確。兩個人在同一毫秒按下購買時，發生的事是：

```text
時間  請求 A                          請求 B
 t1   讀出 Remaining = 1
 t2                                  讀出 Remaining = 1
 t3   檢查 1 > 0，通過
 t4                                  檢查 1 > 0，通過
 t5   算出 0，UPDATE SET Remaining=0
 t6                                  算出 0，UPDATE SET Remaining=0
```

兩張票賣出去了，庫存卻只扣了一次。這叫**遺失更新（lost update）**，是並發問題最基本的形態。

值得注意的是：**加上交易並不能解決它**。在預設的 Read Committed 隔離級別下，上面的序列在交易裡跑出來的結果完全一樣。交易保證的是原子性與一致性，不自動保證「我讀到的值在我寫回去之前沒被別人改過」。

這一章要回答的就是這個差別，以及三種真正能解決它的做法。

---

## 一、EF Core 的交易行為

### 1.1 `SaveChanges` 自帶交易

```csharp
_db.Users.Add(user);
_db.Orders.Add(order);
await _db.SaveChangesAsync();       // 兩個 INSERT 在同一個交易裡
```

一次 `SaveChanges` 內的所有操作是原子的。這是最常被忽略、卻最重要的一條性質——它意味著**大部分情況你根本不需要明確寫交易**。

推論是：**同一個工作單元的所有變更必須放在同一次 `SaveChanges`**。

```csharp
// ❌ 兩個交易。第二個失敗時，第一個已經提交了
_db.Orders.Add(order);
await _db.SaveChangesAsync();

_db.Inventory.Update(inventory);
await _db.SaveChangesAsync();       // 這裡失敗 → 訂單建了但庫存沒扣

// ✅ 一個交易
_db.Orders.Add(order);
_db.Inventory.Update(inventory);
await _db.SaveChangesAsync();
```

### 1.2 什麼時候需要明確交易

三種情況：

**跨多次 `SaveChanges`。** 例如需要先存主檔取得自增 ID，再用這個 ID 存明細：

```csharp
await using var tx = await _db.Database.BeginTransactionAsync(ct);
try
{
    _db.Orders.Add(order);
    await _db.SaveChangesAsync(ct);        // 取得 order.Id

    foreach (var item in items)
    {
        item.OrderId = order.Id;
        _db.OrderItems.Add(item);
    }
    await _db.SaveChangesAsync(ct);

    await tx.CommitAsync(ct);
}
catch
{
    await tx.RollbackAsync(ct);
    throw;
}
```

（其實這個例子不需要交易——EF Core 能處理臨時鍵，直接把兩段合成一次 `SaveChanges` 就好。但當中間需要呼叫預存程序或原生 SQL 時，就真的需要。）

**混用 EF Core 與原生 SQL。** `ExecuteSqlAsync` 和 `SaveChangesAsync` 是兩次獨立的資料庫操作，要放同一個交易才有原子性。

**需要指定隔離級別。**

```csharp
await using var tx = await _db.Database.BeginTransactionAsync(
    IsolationLevel.Serializable, ct);
```

### 1.3 `await using` 不是可選的

交易物件持有資料庫連線與伺服器端資源。忘記釋放的後果是連線不歸還連線池，累積到耗盡。`await using` 保證即使拋例外也會釋放（未提交的交易在 dispose 時自動回滾）。

用 `await using` 而不是 `using`，因為交易的 dispose 是非同步的（要送 ROLLBACK 給資料庫）。用同步版本會變成 sync-over-async（第 06 章）。

---

## 二、隔離級別與讀取現象

隔離級別決定「一個交易能看到其他交易的哪些狀態」。SQL 標準定義四級：

| 級別 | 髒讀 | 不可重複讀 | 幻讀 |
| --- | --- | --- | --- |
| Read Uncommitted | 可能 | 可能 | 可能 |
| Read Committed | 不會 | 可能 | 可能 |
| Repeatable Read | 不會 | 不會 | 可能 |
| Serializable | 不會 | 不會 | 不會 |

三種現象的意思：

- **髒讀（dirty read）**：讀到別的交易還沒提交的資料，對方回滾後你手上是幻影
- **不可重複讀（non-repeatable read）**：同一交易內讀同一筆資料兩次，值不一樣
- **幻讀（phantom read）**：同一交易內執行同一個範圍查詢兩次，結果集多了或少了列

**Oracle 只實作兩級：Read Committed（預設）與 Serializable。** 它用多版本並發控制（MVCC）達成——讀取不會被寫入阻塞，讀到的是交易開始時（或語句開始時）的一致快照。所以 Oracle 上不存在髒讀，而 `Repeatable Read` 這個設定會被當成 Serializable 處理。

實務建議：**維持預設的 Read Committed。** 提高隔離級別的代價是鎖競爭與 `ORA-08177: can't serialize access` 這類序列化失敗，而大部分並發問題用下一節的樂觀併發解決得更漂亮。

---

## 三、樂觀併發：正確解法

回到開頭的售票問題。樂觀併發的思路是：**不加鎖，但在寫入時檢查「這筆資料自從我讀取以來有沒有被改過」**。

### 3.1 並發 Token

在實體上標記一個欄位為並發 token：

```csharp
public class Ticket
{
    public int Id { get; set; }
    public int Remaining { get; set; }

    [Timestamp]                       // SQL Server 的 rowversion
    public byte[] RowVersion { get; set; } = null!;
}
```

有了它，EF Core 產生的 UPDATE 會多一個條件：

```sql
UPDATE TICKETS SET REMAINING = :p0
WHERE ID = :p1 AND ROW_VERSION = :p2
```

如果別人已經改過（`ROW_VERSION` 變了），這條 UPDATE 影響 0 列。EF Core 偵測到「預期影響 1 列但實際 0 列」就拋出 `DbUpdateConcurrencyException`。

回到剛才的時間線：

```text
 t5   A：UPDATE ... WHERE Id=1 AND Version=7  → 影響 1 列，成功，Version 變 8
 t6   B：UPDATE ... WHERE Id=1 AND Version=7  → 影響 0 列 → 拋例外
```

超賣被阻止了。

### 3.2 Oracle 沒有 rowversion

`[Timestamp]` 依賴資料庫自動維護的版本欄位，Oracle 沒有對應機制。兩種替代方案：

**方案一：自己維護版本欄位（推薦）**

```csharp
public class Ticket
{
    public int Id { get; set; }
    public int Remaining { get; set; }

    [ConcurrencyCheck]
    public int Version { get; set; }
}

// 更新時自己遞增
ticket.Remaining -= 1;
ticket.Version += 1;
await _db.SaveChangesAsync();
```

`[ConcurrencyCheck]` 把這個欄位加進 `WHERE` 條件。缺點是每個更新路徑都要記得遞增版本——漏掉一處就失去保護。可以用 `SaveChanges` 攔截器統一處理：

```csharp
public override int SaveChanges()
{
    foreach (var entry in ChangeTracker.Entries<IVersioned>()
                                       .Where(e => e.State == EntityState.Modified))
    {
        entry.Entity.Version++;
    }
    return base.SaveChanges();
}
```

**方案二：用 `ORA_ROWSCN`**

Oracle 每一列都有系統變更編號，可以映射成唯讀的並發 token。但預設是**區塊層級**的粒度（同一個資料區塊上其他列的變更也會讓 SCN 改變），造成大量誤判。要精確到列必須建表時指定 `ROWDEPENDENCIES`，而既有表無法追加此設定。實務上方案一更可控。

**也可以把「值本身」當並發 token**，適合特定欄位：

```csharp
modelBuilder.Entity<Ticket>().Property(t => t.Remaining).IsConcurrencyToken();
```

UPDATE 變成 `WHERE ID = :p1 AND REMAINING = :p2`——「只有在庫存還是我讀到的那個值時才更新」。對單一欄位的計數器場景，這是最輕量的做法。

### 3.3 處理衝突

```csharp
try
{
    await _db.SaveChangesAsync(ct);
}
catch (DbUpdateConcurrencyException ex)
{
    var entry = ex.Entries.Single();
    var databaseValues = await entry.GetDatabaseValuesAsync(ct);

    if (databaseValues is null)
    {
        return Conflict("資料已被刪除");
    }

    // 策略一：Store wins——放棄我的修改，回報衝突
    return Conflict(new
    {
        message = "資料已被他人修改，請重新載入",
        current = databaseValues.ToObject()
    });

    // 策略二：Client wins——用資料庫的值當基準，硬蓋過去
    // entry.OriginalValues.SetValues(databaseValues);
    // await _db.SaveChangesAsync(ct);

    // 策略三：Merge——逐欄位決定，通常需要業務規則介入
}
```

三種策略的選擇是**業務決策**，不是技術決策。編輯表單通常用 store wins（告訴使用者資料變了，請重新載入）；計數器類的操作通常用重試（下一節）。

### 3.4 更好的做法：讓資料庫做計算

對「扣庫存」這種操作，還有一個更簡潔的解法——不要在應用程式端算：

```csharp
var affected = await _db.Tickets
    .Where(t => t.Id == id && t.Remaining > 0)
    .ExecuteUpdateAsync(s => s.SetProperty(t => t.Remaining, t => t.Remaining - 1), ct);

if (affected == 0)
{
    return Conflict("票已售完");
}
```

一條 SQL：`UPDATE TICKETS SET REMAINING = REMAINING - 1 WHERE ID = :p0 AND REMAINING > 0`。

檢查與扣減在同一個原子操作裡完成，由資料庫的列鎖保證。完全沒有 read-modify-write 的視窗，也不需要並發 token 與重試。

**能用單條 SQL 表達的更新，就不要繞經應用程式記憶體。** 這是並發控制最簡單也最可靠的一招。代價是繞過 change tracker（第 08 章），所以不適合需要複雜業務規則的路徑。

---

## 四、悲觀鎖

有些場景真的需要「我讀的時候就鎖住，別人不准動」——例如需要讀取多筆相關資料做複雜計算再寫回，而樂觀併發的重試成本太高。

EF Core 沒有內建 API，要用原生 SQL：

```csharp
await using var tx = await _db.Database.BeginTransactionAsync(ct);

var ticket = await _db.Tickets
    .FromSql($"SELECT * FROM TICKETS WHERE ID = {id} FOR UPDATE")
    .FirstOrDefaultAsync(ct);

// 這一列現在被鎖住，其他交易的 FOR UPDATE 會等待

ticket!.Remaining -= 1;
await _db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);
```

`FOR UPDATE NOWAIT` 會在鎖不到時立刻報錯而不是等待；`FOR UPDATE SKIP LOCKED` 會跳過被鎖的列，是實作「工作佇列」的經典手法。

使用悲觀鎖的三個紀律：

1. **交易必須短**。鎖持有期間其他人在等，長交易會讓吞吐量崩潰
2. **鎖定順序必須一致**。A 先鎖 1 再鎖 2、B 先鎖 2 再鎖 1，就是死結
3. **絕對不要在持有鎖時呼叫外部服務**。一個逾時 30 秒的 HTTP 呼叫會讓鎖也持有 30 秒

第三點延伸出一條更普遍的原則：**交易裡不要有 I/O 以外的等待**。寄 email、呼叫第三方 API、寫檔案——這些都應該在交易提交之後做，或者更好的做法是進佇列。

---

## 五、重試與冪等

### 5.1 連線層級的重試

暫時性錯誤（網路抖動、資料庫短暫不可用）可以自動重試：

```csharp
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseOracle(cs, o => o.UseOracleSQLCompatibility("19")
                            .EnableRetryOnFailure(
                                maxRetryCount: 3,
                                maxRetryDelay: TimeSpan.FromSeconds(5),
                                errorNumbersToAdd: null)));
```

有一個重要的限制：**啟用重試後，不能使用明確交易**——會拋出「已設定執行策略，不支援使用者發起的交易」。因為重試策略需要重新執行整個操作，但它無法重播你手寫的交易區塊。

需要兩者並存時，要把整段包進執行策略：

```csharp
var strategy = _db.Database.CreateExecutionStrategy();

await strategy.ExecuteAsync(async () =>
{
    await using var tx = await _db.Database.BeginTransactionAsync(ct);
    // ... 操作
    await tx.CommitAsync(ct);
});
```

### 5.2 冪等性

重試的前提是**操作可以安全地執行多次**。查詢天生冪等；`UPDATE ... SET X = 5` 冪等；但 `UPDATE ... SET Balance = Balance - 100` **不冪等**——重試兩次就扣了兩百。

這在網路層面尤其危險：請求送出去了、資料庫執行成功了、但回應在網路上遺失，客戶端重試——扣款發生兩次。

處理方式是**冪等鍵（idempotency key）**：

```csharp
[HttpPost("payments")]
public async Task<IActionResult> PayAsync(
    [FromHeader(Name = "Idempotency-Key")] string key,
    PaymentDto dto, CancellationToken ct)
{
    var existing = await _db.Payments
        .AsNoTracking()
        .FirstOrDefaultAsync(p => p.IdempotencyKey == key, ct);

    if (existing is not null)
    {
        return Ok(ToDto(existing));      // 已處理過，回傳原結果
    }

    var payment = new Payment { IdempotencyKey = key, /* ... */ };
    _db.Payments.Add(payment);
    await _db.SaveChangesAsync(ct);      // IdempotencyKey 上有唯一索引

    return Ok(ToDto(payment));
}
```

`IdempotencyKey` 欄位上必須有**唯一索引**——這才是真正的保證。上面的「先查再插」之間仍有競爭視窗，但唯一索引會讓第二筆插入失敗，捕捉該例外後回傳既有結果即可。任何有金流或不可逆副作用的 API 都應該支援這個機制。

---

## 六、分散式交易與 Outbox

當一個操作需要同時修改資料庫**和**呼叫外部系統時，事情變得根本困難：

```csharp
await using var tx = await _db.Database.BeginTransactionAsync(ct);

_db.Orders.Add(order);
await _db.SaveChangesAsync(ct);

await _paymentGateway.ChargeAsync(order.Total, ct);   // ⚠️ 外部呼叫

await tx.CommitAsync(ct);
```

問題在於：付款成功了，但 `CommitAsync` 失敗（連線斷了、程序被砍了）。錢扣了，訂單沒建立。反過來也一樣糟。

**沒有辦法讓「資料庫交易」和「外部 HTTP 呼叫」變成一個原子操作。** 分散式交易（兩階段提交）理論上能做到，但它要求所有參與者都支援、而且會在協調者當機時把資源鎖死。現代系統普遍避開它。

主流解法是 **Outbox 模式**——把「要做的外部動作」當成資料寫進同一個資料庫交易：

```csharp
_db.Orders.Add(order);
_db.OutboxMessages.Add(new OutboxMessage
{
    Type = "ChargePayment",
    Payload = JsonSerializer.Serialize(new { order.Id, order.Total }),
    CreatedAt = DateTimeOffset.UtcNow
});

await _db.SaveChangesAsync(ct);      // 訂單與待辦訊息，同一個交易，原子
```

然後由背景服務輪詢 outbox 表，逐筆執行外部呼叫並標記完成：

```text
訂單建立 + outbox 訊息  →  同一交易，要嘛都成功要嘛都失敗
背景服務讀 outbox       →  執行外部呼叫 → 成功則標記已處理
```

這把「原子性」問題轉化成「最終一致性 + 至少一次投遞」。外部呼叫可能重複執行（背景服務標記完成前當掉），所以**接收端必須冪等**——回到上一節的冪等鍵。

完整的 outbox 實作（訊息排序、重試退避、毒性訊息處理）超出本章範圍，但知道這個模式的存在很重要：看到「交易裡有外部呼叫」就該想到它。背景服務的實作細節見 [[19-background-work]]。

---

## 七、連線池與長交易

每個開啟的交易佔用一條資料庫連線。連線池的大小有限（Oracle 的預設 `Max Pool Size` 是 100），耗盡時新請求會等待，逾時後拋出「連線池已滿」。

會拖長交易的常見錯誤：

```csharp
await using var tx = await _db.Database.BeginTransactionAsync(ct);

var orders = await _db.Orders.ToListAsync(ct);

foreach (var order in orders)
{
    await _emailService.SendAsync(order.CustomerEmail, ct);   // ❌ 每封信 200ms
}

await tx.CommitAsync(ct);      // 1000 筆訂單 = 交易開了 200 秒
```

修正方向是把外部呼叫移出交易（或改用 outbox）：

```csharp
List<Order> orders;

await using (var tx = await _db.Database.BeginTransactionAsync(ct))
{
    orders = await _db.Orders.ToListAsync(ct);
    // ... 資料庫操作
    await tx.CommitAsync(ct);
}

// 交易已提交，連線已歸還
foreach (var order in orders)
{
    await _emailService.SendAsync(order.CustomerEmail, ct);
}
```

原則：**交易只包資料庫操作，而且越短越好。**

---

## 八、常見誤解

**「加了交易就不會有並發問題。」**
交易保證原子性與一致性，不保證「我讀到的值在寫回之前沒被改過」。遺失更新在預設隔離級別下照樣發生，要靠並發 token、原子 UPDATE 或悲觀鎖。

**「隔離級別調到 Serializable 就安全了。」**
它會顯著增加鎖競爭與序列化失敗（Oracle 的 `ORA-08177`），而且你仍然要處理失敗後的重試。多數情況樂觀併發更實用。

**「每個 action 都應該包一個交易。」**
`SaveChanges` 自帶交易，單次呼叫已經是原子的。多包一層只是增加程式碼與出錯機會。真正需要明確交易的是跨多次 `SaveChanges` 或混用原生 SQL 的情況。

**「重試機制打開就不用管暫時性錯誤了。」**
重試要求操作冪等。`Balance = Balance - 100` 這類操作重試兩次會扣兩次。有副作用的 API 需要冪等鍵。

**「Oracle 可以用 `[Timestamp]` 做並發控制。」**
不行，那是 SQL Server 的 rowversion。Oracle 要自己維護版本欄位配合 `[ConcurrencyCheck]`，或把業務欄位本身設為並發 token。

**「交易裡呼叫外部 API 可以保證一致性。」**
不能。資料庫交易與 HTTP 呼叫無法原子化。用 outbox 模式把外部動作轉成同一交易內的資料，再由背景服務投遞。

---

## 九、同事會來問你的問題

**Q：庫存偶爾會扣成負數，加了交易還是會發生。**
典型的遺失更新。三種解法：用 `ExecuteUpdate` 寫成單條原子 SQL（`WHERE Remaining > 0`，最簡單）；加並發 token 讓衝突變成例外再重試；或用 `SELECT ... FOR UPDATE` 悲觀鎖。優先選第一種。

**Q：`DbUpdateConcurrencyException` 該怎麼處理？**
先確認業務語意：編輯表單通常回 409 並附上目前資料庫的值請使用者重新載入；計數器類的操作通常是讀取最新值後重試。沒有通用答案，這是業務決策。

**Q：Oracle 上怎麼做樂觀併發？**
自己加一個 `Version` 整數欄位，標記 `[ConcurrencyCheck]`，在 `SaveChanges` 攔截器裡統一遞增。`ORA_ROWSCN` 預設是區塊粒度會誤判，除非建表時指定 `ROWDEPENDENCIES`。

**Q：開了 `EnableRetryOnFailure` 之後 `BeginTransaction` 就報錯。**
執行策略無法重播使用者發起的交易。把整段包進 `Database.CreateExecutionStrategy().ExecuteAsync(...)`。

**Q：交易裡可以呼叫其他微服務嗎？**
不應該。外部呼叫的延遲會拖長交易、佔住連線，而且無法與資料庫交易原子化。用 outbox 模式：把要做的事寫進同一交易的 outbox 表，由背景服務投遞。

**Q：「連線池已滿」怎麼查？**
先找長交易——交易裡有沒有外部呼叫、迴圈、或忘記 dispose 的 scope（第 02 章）。再確認沒有把 DbContext 從 root provider 解析出來長期持有。連線池大小是最後才調的參數，不是第一個。

**Q：`SELECT ... FOR UPDATE SKIP LOCKED` 有什麼用？**
實作工作佇列的標準手法。多個 worker 同時搶任務時，每個各自鎖住不同的列，跳過已被別人鎖住的，不會互相等待。

---

## 連結

- [[basics-10-efcore-and-oracle]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[08-efcore-query]] — 上一章：`ExecuteUpdate` 與原生 SQL
- [[10-oracle-specifics]] — 下一章：Oracle provider 的特殊行為
- [[07-efcore-internals]] — `SaveChanges` 的隱含交易
- [[19-background-work]] — outbox 投遞服務的實作
- [[05-filters-and-mvc-internals]] — 用 filter 管理交易邊界的取捨
- [[oracle]] — 資料庫 entity 頁
