---
type: concept
domain: tech
tags: [dotnet, csharp, async, await, threadpool, cancellation, valuetask, concurrency]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 06 章：async 與執行緒 — 它省的不是時間，是執行緒

## 一個下午三點的故事

系統平常好好的。某天下午三點左右，監控開始出現大量請求逾時。看資料庫——CPU 很閒，慢查詢紀錄是空的。看應用程式 Pod——CPU 大約 20%，記憶體正常，沒有 OOM。看 log——沒有例外，只是很多請求就是慢，而且慢得離譜，本來 50 毫秒的查詢變成 30 秒。

重啟 Pod，一切恢復正常。過兩天又發生。

這是 **ThreadPool 飢餓（thread pool starvation）**，而它幾乎總是由同一件事引起：程式碼裡某個地方在同步等待非同步操作。這種寫法在低流量時完全不會出事，流量一過某個門檻就雪崩式惡化——這正是「平常好好的、某個下午突然爆炸」的特徵。

要理解為什麼，得先把 async 到底在做什麼講清楚。因為關於 async 最普遍的誤解是：**以為它讓程式變快**。

---

## 一、async 省的是什麼

先看非同步之前的世界。傳統的同步 Web 伺服器模型是「一個請求一個執行緒」：

```csharp
public IActionResult GetUser(int id)
{
    var user = _db.Users.Find(id);      // 阻塞 50 毫秒等資料庫
    return Ok(user);
}
```

這 50 毫秒裡，執行緒在做什麼？**什麼也沒做。** 它送出查詢、然後停在那裡等網路回應。但這個執行緒仍然被佔用——1 MB 左右的堆疊記憶體，加上作業系統的排程負擔。

現在換成非同步：

```csharp
public async Task<IActionResult> GetUserAsync(int id)
{
    var user = await _db.Users.FindAsync(id);
    return Ok(user);
}
```

執行到 `await` 時，方法**讓出執行緒**——執行緒回到 ThreadPool，去服務其他請求。等資料庫回應到達，執行時期從池中取一個（不一定是原來那個）執行緒，從 `await` 之後繼續執行。

關鍵結論：

**單一請求不會因為 async 變快。** 資料庫查詢還是 50 毫秒，甚至因為狀態機的開銷還慢一點點。

**但整個系統的吞吐量大幅提升。** 同樣 100 個執行緒，同步模型只能同時處理 100 個請求；非同步模型在請求主要是等待 I/O 的情況下，可以同時處理數千個。

所以判斷「該不該用 async」的標準只有一個：**這個操作是不是在等待 I/O（資料庫、HTTP、檔案、訊息佇列）**。是就用 async。純 CPU 運算（排序、計算、加密）用 async 沒有意義——沒有等待可以讓出，反而多付一層狀態機成本。

---

## 二、await 之後的程式碼在哪個執行緒上跑

```csharp
public async Task<IActionResult> GetAsync(int id)
{
    // 執行緒 A
    var user = await _db.Users.FindAsync(id);
    // 執行緒 A 或 B 或 C——不保證
    return Ok(user);
}
```

在 ASP.NET Core 裡，`await` 之後的程式碼會在 **ThreadPool 的任意執行緒**上繼續，不保證是原來那個。

這和舊 ASP.NET（.NET Framework）有本質差異。舊版有 `SynchronizationContext`——一個「把 continuation 排回原本上下文」的機制，用來保證 `HttpContext.Current` 這類執行緒相關狀態能跨 await 存活。它帶來兩個後果：效能損耗，以及惡名昭彰的死結（在有 context 的環境呼叫 `.Result` 會死鎖）。

**ASP.NET Core 移除了 `SynchronizationContext`。** 這帶來兩個直接影響：

**影響一：不需要寫 `ConfigureAwait(false)`。** 這個呼叫的作用是「不要排回原本的 context」，而 ASP.NET Core 本來就沒有 context，所以它是無操作的。應用程式碼裡不用寫。

但**函式庫程式碼仍然應該寫**——因為函式庫不知道自己會被誰呼叫，可能是 WPF 或舊 ASP.NET 那種有 context 的環境。判準是：寫應用程式（有 `Program.cs` 的那個專案）不用寫；寫要發布給別人用的類別庫要寫。

**影響二：執行緒相關的狀態不能跨 await 依賴。** `Thread.CurrentPrincipal`、`ThreadStatic` 欄位、以及任何綁在執行緒上的東西，await 之後可能就不見了。需要跨 await 流動的狀態要用 `AsyncLocal<T>`——`IHttpContextAccessor` 內部正是這樣實作的。

---

## 三、ThreadPool 飢餓：開頭那個故事的解答

ThreadPool 的行為有一個關鍵特性：**它不會立刻建立大量執行緒**。

池子有一個「最小執行緒數」（預設等於 CPU 核心數，容器裡則是配置的 CPU 限制）。工作量超過這個數字時，池子不會馬上擴充——它每隔一段時間（歷史上約 500 毫秒，新版有調整）才新增一個執行緒。這個節流設計是刻意的：突發的工作尖峰通常很快消退，盲目建立執行緒只會製造更多上下文切換。

現在看這段程式碼：

```csharp
public IActionResult GetUser(int id)
{
    var user = _userService.GetUserAsync(id).Result;   // ❌ 同步等待非同步
    return Ok(user);
}
```

`.Result` 做的事是：**佔住當前執行緒，阻塞等待。** 於是：

```text
1. 請求進來，從 ThreadPool 拿一個執行緒
2. 呼叫 GetUserAsync，它發出資料庫查詢後回傳一個未完成的 Task
3. .Result 阻塞這個執行緒等 Task 完成
4. 資料庫回應到達，continuation 需要一個執行緒來執行
5. 但那個執行緒正卡在第 3 步等它自己——需要「另一個」執行緒
6. 池裡沒有空閒執行緒了？那就等 500 毫秒新增一個
```

在低流量下這完全不會被注意到：池裡永遠有空閒執行緒，第 5 步立刻拿到。但當並行請求數超過池的最小執行緒數，每個請求都佔一個執行緒去阻塞等待，池子被榨乾。新請求排隊，每隔 500 毫秒才多一個執行緒可用。

**於是形成正回饋：越慢 → 積壓越多 → 佔用越多執行緒 → 更慢。** 這就是「本來 50 毫秒的查詢變成 30 秒」的來源——那 30 秒幾乎全是排隊等執行緒，不是查詢本身。

也解釋了為什麼看 CPU 完全正常：執行緒是**阻塞**的，不是忙碌的。CPU 圖表上是一片祥和。

### 3.1 三種 sync-over-async 寫法都一樣壞

```csharp
task.Result;                       // ❌
task.Wait();                       // ❌
task.GetAwaiter().GetResult();     // ❌（只是例外不會被包成 AggregateException）
```

第三種常被誤以為「比較安全」——它安全的只是例外的形狀，阻塞行為完全相同。

### 3.2 怎麼診斷

現象特徵：

- 回應時間隨並行量非線性惡化
- CPU 使用率低，但請求塞住
- 重啟後恢復，一段時間又復發

實際指標可以用 `dotnet-counters` 觀察：

```powershell
dotnet-counters monitor -p <pid> --counters System.Runtime
```

關注三個值：`ThreadPool Thread Count`（持續上升是警訊）、`ThreadPool Queue Length`（長期不為零就是積壓）、`ThreadPool Completed Work Item Count`（成長停滯代表卡住）。

在容器裡可以用 `kubectl exec` 進去跑，或者更實際的做法是把這些 counter 透過 OpenTelemetry 匯出到 Prometheus 長期監控（見 [[16-logging-and-observability]]）。

### 3.3 治本：async 一路到底

修正方式不是調大 ThreadPool 的最小執行緒數——那只是把爆炸點往後推，而且浪費記憶體。治本是**讓非同步從頭貫穿到尾**：

```csharp
public async Task<IActionResult> GetUserAsync(int id)
{
    var user = await _userService.GetUserAsync(id);
    return Ok(user);
}
```

「一路到底」意味著呼叫鏈上每一層都是 `async Task`：controller → service → repository → EF Core。任何一層寫了 `.Result`，整條鏈的好處就消失了。

那如果某個第三方函式庫只提供同步 API 呢？誠實的答案是：**沒有辦法把同步變成真正的非同步**。用 `Task.Run(() => LegacyCall())` 包起來只是把阻塞轉移到另一個 ThreadPool 執行緒，總佔用量沒變（在 Web 場景下甚至更差，因為多了排程成本）。這種情況下的務實選擇是隔離——把這類呼叫集中到獨立的背景服務或獨立的部署單元，不要讓它拖垮主要的請求處理路徑。

---

## 四、`async void`：唯一該恐懼的關鍵字組合

```csharp
public async void ProcessAsync()     // ❌
{
    await DoWorkAsync();
}
```

`async void` 有三個致命問題：

**呼叫端無法 await。** 沒有回傳 `Task`，就無法知道它何時完成、也無法等它。

**例外無法被捕捉。** `async Task` 裡的例外會被存進 Task 物件，await 時重新拋出。`async void` 沒有 Task 可以存，例外會直接拋到 `SynchronizationContext`——在 ASP.NET Core 裡就是拋到 ThreadPool，結果是**整個程序當掉**。不是回 500，是程序終止、Pod 重啟。

```csharp
try
{
    ProcessAsync();          // async void
}
catch (Exception ex)
{
    // 永遠不會進來——方法一遇到 await 就回傳了，例外發生在之後
}
```

**無法測試。** 測試無法等待它完成，斷言會在操作結束前就執行。

唯一合法的用途是**事件處理常式**（`button.Click += async (s, e) => ...`），因為事件的委派簽章要求回傳 void。Web API 裡沒有這種情況，所以規則很簡單：**Web API 裡不該出現 `async void`。**

順帶一提，`async Task` 的方法如果沒被 await 也有類似風險（fire-and-forget）：

```csharp
_ = SendEmailAsync(user);    // 沒 await，例外會變成未觀察的 Task 例外
```

.NET 4.5 之後未觀察的 Task 例外不再讓程序當掉（只是靜靜消失），但那代表**錯誤被吞掉了**。真的要 fire-and-forget，至少要包一層記錄：

```csharp
_ = Task.Run(async () =>
{
    try { await SendEmailAsync(user); }
    catch (Exception ex) { logger.LogError(ex, "背景寄信失敗"); }
});
```

但更好的答案通常是**不要 fire-and-forget**。請求結束後 scope 就釋放了，那個背景工作可能正在用一個已經被 dispose 的 DbContext；Pod 關閉時它也不會被等待。需要背景執行的東西應該進佇列，由 `BackgroundService` 或 Hangfire 處理（見 [[19-background-work]]）。

---

## 五、`CancellationToken`：讓取消真的有效

```csharp
[HttpGet]
public async Task<IActionResult> SearchAsync(string q, CancellationToken ct)
{
    var results = await _db.Products
        .Where(p => p.Name.Contains(q))
        .ToListAsync(ct);

    return Ok(results);
}
```

Action 方法的 `CancellationToken` 參數會被 model binding 自動填入 `HttpContext.RequestAborted`，不需要任何 attribute。它在兩種情況下被觸發：客戶端斷線，以及應用程式關機（第 00 章）。

價值在於**不做白工**。使用者按了取消、關掉分頁、或網路斷了，資料庫查詢會被真的取消，連線立刻歸還連線池。沒傳 token 的話，查詢會跑完整個過程、序列化整份結果，然後發現沒人要——在慢查詢多的系統上這是可觀的浪費。

規則：**能傳的地方都傳**，一路傳到最底層的 I/O 呼叫。中間任何一層漏掉，取消就在那裡斷了。

要注意取消會拋 `OperationCanceledException`。這不是錯誤，是預期行為，不該被記錄成 error 也不該回 500：

```csharp
catch (OperationCanceledException) when (ct.IsCancellationRequested)
{
    // 客戶端主動取消，正常路徑
    return new StatusCodeResult(499);   // 非標準但常用的「客戶端已關閉請求」
}
```

實務上更常見的做法是在全域例外處理裡統一辨識並降級記錄（見 [[15-error-handling]]），因為這種例外在流量大時會非常多，全部記成 error 會淹沒真正的問題。

---

## 六、`Task` 與 `ValueTask`

```csharp
public async Task<User> GetAsync(int id)         // 每次呼叫配置一個 Task 物件
public async ValueTask<User> GetAsync(int id)    // 同步完成時不配置
```

`ValueTask<T>` 是一個 struct。當方法**經常同步完成**時（例如快取命中），它避免了堆積配置：

```csharp
public async ValueTask<User?> GetUserAsync(int id)
{
    if (_cache.TryGetValue<User>(id, out var cached))
    {
        return cached;                  // 同步返回，不配置 Task
    }

    return await _db.Users.FindAsync(id);
}
```

但它有嚴格的使用限制：

- **只能 await 一次**。await 兩次是未定義行為
- **不能同時 await 多個**（`Task.WhenAll` 不接受它，要先 `.AsTask()`）
- **不能阻塞等待**（`.Result` 在未完成的 `ValueTask` 上是錯誤的）

建議：**預設用 `Task`。** 只在效能剖析證明某個高頻方法的 Task 配置是瓶頸、且它經常同步完成時，才改用 `ValueTask`。過早使用它換來的是一組容易誤用的限制，而收益通常在測量誤差範圍內。

---

## 七、並行執行

`await` 是**依序**的：

```csharp
var user = await _userService.GetAsync(id);          // 50ms
var orders = await _orderService.GetByUserAsync(id); // 50ms
// 總共 100ms
```

兩個查詢彼此獨立，卻排隊執行。改成並行：

```csharp
var userTask = _userService.GetAsync(id);            // 兩個都先啟動
var ordersTask = _orderService.GetByUserAsync(id);

await Task.WhenAll(userTask, ordersTask);            // 一起等
var user = userTask.Result;                          // 已完成，取值不阻塞
var orders = ordersTask.Result;
// 總共約 50ms
```

（這裡的 `.Result` 是安全的——Task 已經完成，不會阻塞。但為了避免和 sync-over-async 混淆，`await userTask` 更清楚。）

**一個重要的例外：EF Core 的 `DbContext` 不支援並行操作。**

```csharp
// ❌ 同一個 DbContext 上兩個並行查詢 → A second operation was started
var usersTask = _db.Users.ToListAsync();
var ordersTask = _db.Orders.ToListAsync();
await Task.WhenAll(usersTask, ordersTask);
```

要並行查資料庫，必須用不同的 DbContext 實例——注入 `IDbContextFactory<AppDbContext>` 各自建立。這在 [[07-efcore-internals]] 詳談。

### 7.1 限制並行度

對外部服務發起大量並行呼叫要有節制，否則會壓垮對方或耗盡自己的連線：

```csharp
await Parallel.ForEachAsync(items, new ParallelOptions
{
    MaxDegreeOfParallelism = 8,
    CancellationToken = ct
}, async (item, token) =>
{
    await ProcessAsync(item, token);
});
```

`Parallel.ForEachAsync`（.NET 6+）是處理「一批項目、每個都要非同步處理、但不要一次全開」的標準工具。沒有它的話得自己用 `SemaphoreSlim` 控制。

### 7.2 `Task.WhenAll` 的例外行為

多個 Task 都失敗時，`await Task.WhenAll(...)` **只會拋出第一個例外**。其他的被藏在 Task 的 `AggregateException` 裡。要看全部：

```csharp
var all = Task.WhenAll(tasks);
try
{
    await all;
}
catch
{
    foreach (var ex in all.Exception!.InnerExceptions)
    {
        logger.LogError(ex, "批次項目失敗");
    }
}
```

批次處理時漏掉這一點，會導致「十個失敗只看到一個錯誤」。

---

## 八、串流回應：`IAsyncEnumerable`

```csharp
[HttpGet("export")]
public async IAsyncEnumerable<ProductDto> ExportAsync(
    [EnumeratorCancellation] CancellationToken ct)
{
    await foreach (var p in _db.Products.AsAsyncEnumerable().WithCancellation(ct))
    {
        yield return ToDto(p);
    }
}
```

回傳 `IAsyncEnumerable<T>` 時，ASP.NET Core 會**邊產生邊寫出 JSON**，而不是把整份結果先組在記憶體裡。對大量資料匯出，這是記憶體用量從「整份資料」降到「一筆」的差別。

三個注意事項：`[EnumeratorCancellation]` 屬性必須加，否則 token 傳不進迭代器；串流開始後就無法改變狀態碼（第 01 章的 `HasStarted`），所以中途失敗只能截斷連線；以及 DbContext 必須在整個串流期間存活，所以不能在方法內用 `using`。

---

## 九、常見誤解

**「加了 async 程式會變快。」**
單一請求不會變快，甚至略慢（狀態機開銷）。它提升的是吞吐量——同樣的執行緒數能服務更多並行請求。

**「ASP.NET Core 要寫 `ConfigureAwait(false)`。」**
不用。ASP.NET Core 沒有 `SynchronizationContext`，這個呼叫是無操作的。發布給他人使用的類別庫仍然應該寫。

**「`.Result` 只是不好看，功能是一樣的。」**
它會阻塞執行緒，在並行量上來後引發 ThreadPool 飢餓——症狀是 CPU 很閒但請求全部逾時。這是生產環境最典型的效能事故之一。

**「`GetAwaiter().GetResult()` 比 `.Result` 安全。」**
只有例外的包裝形式不同，阻塞行為完全一樣。

**「`ValueTask` 比 `Task` 好，應該全面改用。」**
只在「經常同步完成的高頻方法」上有意義，而且帶來一組嚴格限制（只能 await 一次、不能阻塞、不能直接 `WhenAll`）。預設用 `Task`。

**「可以用 `Task.Run` 把同步函式庫變成非同步。」**
不能。它只是把阻塞搬到另一個 ThreadPool 執行緒，總佔用量不變，還多了排程成本。

**「請求結束後開個背景 Task 繼續處理，反正回應已經送出去了。」**
那個 Task 用的 scope 已經被釋放（DbContext 可能已 dispose），Pod 關閉時也不會等它。要背景處理就進佇列交給 `BackgroundService`。

---

## 十、同事會來問你的問題

**Q：CPU 很低但請求全部逾時，重啟就好，過幾天又發生。**
典型的 ThreadPool 飢餓。找程式碼裡的 `.Result`、`.Wait()`、`GetAwaiter().GetResult()`——同步等待非同步會佔住執行緒，並行量超過池的最小執行緒數之後就雪崩。用 `dotnet-counters` 看 `ThreadPool Queue Length` 確認。

**Q：為什麼 `await` 之後 `Thread.CurrentThread.ManagedThreadId` 變了？**
ASP.NET Core 沒有 `SynchronizationContext`，continuation 在 ThreadPool 的任意執行緒上執行。任何綁在執行緒上的狀態都不能跨 await 依賴，要用 `AsyncLocal<T>`。

**Q：這個方法可以寫成 `async void` 嗎？**
不行。例外無法被捕捉，會直接讓程序當掉；呼叫端也無法等待或測試。Web API 裡沒有 `async void` 的合法用途。

**Q：兩個查詢想並行跑，`Task.WhenAll` 為什麼報 `A second operation was started`？**
同一個 `DbContext` 不支援並行操作。要並行查資料庫必須用不同的 DbContext 實例，注入 `IDbContextFactory<T>` 各自建立。

**Q：Action 的 `CancellationToken` 參數要加什麼 attribute？**
不用。Model binding 會自動把 `HttpContext.RequestAborted` 綁進去。重點是把它一路往下傳到最底層的 I/O 呼叫。

**Q：取消請求時 log 出現一堆 `OperationCanceledException` error。**
那是預期行為不是錯誤。在全域例外處理裡辨識這個型別並降級為 debug/info，否則流量大時會淹沒真正的問題。

**Q：匯出十萬筆資料記憶體就爆了。**
不要先 `ToListAsync()` 再回傳。改回傳 `IAsyncEnumerable<T>` 讓框架邊查邊寫，記憶體用量從整份資料降到單筆。記得加 `[EnumeratorCancellation]`。

---

## 連結

- [[basics-10-efcore-and-oracle]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[05-filters-and-mvc-internals]] — 上一章：filter 的非同步版本
- [[07-efcore-internals]] — 下一章：DbContext 為什麼不能並行
- [[00-hosting-and-startup]] — 關機時的 CancellationToken
- [[16-logging-and-observability]] — ThreadPool 指標的長期監控
- [[19-background-work]] — 背景工作的正確做法
- [[csharp]] — C# 語言層面的 async/await
