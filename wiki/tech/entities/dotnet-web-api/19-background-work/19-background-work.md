---
type: concept
domain: tech
tags: [dotnet, aspnet, background-service, hangfire, hosted-service, channel, outbox, leader-election]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 19 章：背景工作 — 三個副本，同一封信寄了三次

## 擴容之後才出現的 bug

每天早上九點寄送對帳通知，用 `BackgroundService` 加一個計時器實作，跑了半年都很正常。

某天為了應付流量把 Deployment 的副本數從 1 調到 3。隔天早上，每個客戶收到**三封**一模一樣的通知信。

原因很直白：`BackgroundService` 是**應用程式內**的機制，每個 Pod 都是一個完整的應用程式，於是每個 Pod 都在九點整跑了同一件事。程式碼完全沒錯，錯的是「背景工作」與「水平擴展」之間的假設不相容。

這一章要處理的就是：什麼工作適合放在應用程式裡、多副本下怎麼保證只跑一次、以及工作跑到一半 Pod 被砍掉怎麼辦。

---

## 一、`IHostedService` 與 `BackgroundService`

第 00 章講過 Host 會啟動所有 `IHostedService`。它的介面很簡單：

```csharp
public interface IHostedService
{
    Task StartAsync(CancellationToken cancellationToken);
    Task StopAsync(CancellationToken cancellationToken);
}
```

`BackgroundService` 是一個抽象基底類別，把「長時間執行的迴圈」這個常見模式包好：

```csharp
public class ReportWorker : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly ILogger<ReportWorker> _logger;

    public ReportWorker(IServiceScopeFactory scopeFactory, ILogger<ReportWorker> logger)
    {
        _scopeFactory = scopeFactory;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromMinutes(5));

        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            try
            {
                using var scope = _scopeFactory.CreateScope();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                await ProcessAsync(db, stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;                      // 正常關機
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "背景處理失敗，等下一輪重試");
                // 吞掉例外讓迴圈繼續 —— 但一定要記錄
            }
        }
    }
}

builder.Services.AddHostedService<ReportWorker>();
```

這段短短的程式碼裡有五個容易寫錯的地方，逐一說明。

### 1.1 用 `PeriodicTimer` 而不是 `Task.Delay`

```csharp
// 舊寫法：週期會漂移
while (!ct.IsCancellationRequested)
{
    await DoWorkAsync();                       // 花了 40 秒
    await Task.Delay(TimeSpan.FromMinutes(5), ct);   // 再等 5 分鐘 → 實際間隔 5:40
}

// PeriodicTimer：固定節奏
using var timer = new PeriodicTimer(TimeSpan.FromMinutes(5));
while (await timer.WaitForNextTickAsync(ct))
{
    await DoWorkAsync();
}
```

`Task.Delay` 的間隔是「工作結束後再等 N」，所以實際週期是「工作時間 + N」，會逐漸漂移。`PeriodicTimer`（.NET 6+）維持固定節奏——如果一輪工作超過週期，下一次會立刻觸發（不會累積補跑）。

### 1.2 每一輪開一個 scope

`BackgroundService` 是 Singleton，不能直接注入 `DbContext`（第 02 章）。而 scope 的邊界要開在**迴圈內**——每一輪一個新的 DbContext，對應一個邏輯工作單元。開在迴圈外就變成一個活好幾天的 DbContext，回到 captive dependency 的處境。

### 1.3 例外必須自己接

**`ExecuteAsync` 拋出未處理的例外，.NET 6 起預設會停止整個 Host**（`HostOptions.BackgroundServiceExceptionBehavior` 預設是 `StopHost`）。一個背景工作的失敗會讓整個 API 掛掉。

這個預設值是合理的（總比靜靜死掉好），但對「偶爾失敗、下一輪重試就好」的工作太激烈。所以迴圈內要包 try-catch，把可恢復的錯誤吞掉並記錄。

不要無腦設成 `Ignore`：

```csharp
builder.Services.Configure<HostOptions>(o =>
    o.BackgroundServiceExceptionBehavior = BackgroundServiceExceptionBehavior.Ignore);
```

那會讓背景服務靜靜死掉而應用程式繼續跑——你完全不會發現對帳任務已經三天沒執行了。要嘛在迴圈內處理，要嘛讓它停掉並被監控發現。

### 1.4 區分「取消」與「錯誤」

關機時 `stoppingToken` 被觸發，進行中的 `await` 會拋 `OperationCanceledException`。這不是錯誤，不該記成 error（第 15 章）。用 `when (stoppingToken.IsCancellationRequested)` 過濾掉。

### 1.5 啟動時不要阻塞

第 00 章講過：`ExecuteAsync` 在遇到第一個真正的 await 之前，會卡住整個 Host 的啟動流程。開頭不要有同步的重活或長時間的初始化——那會讓 K8s 的 startup probe 逾時，Pod 陷入重啟迴圈而 log 裡什麼都沒有。

需要啟動時的預熱，用 `IHostApplicationLifetime.ApplicationStarted` 回呼，或在 `ExecuteAsync` 開頭先 `await Task.Yield()`。

---

## 二、多副本：開頭那個問題

### 方案一：交給 K8s CronJob（最推薦）

排程工作本來就不該住在 Web API 裡。它是獨立的關注點，有獨立的失敗模式與資源需求。

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-reconciliation
spec:
  schedule: "0 9 * * *"
  concurrencyPolicy: Forbid          # 上一次沒跑完就不啟動新的
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: job
              image: myapp:1.2.3
              args: ["--job", "reconciliation"]
```

同一個映像檔，用參數決定「這次是跑 API 還是跑任務」：

```csharp
if (args.Contains("--job"))
{
    var host = Host.CreateApplicationBuilder(args).Build();
    // 跑完就退出
    await RunJobAsync(host.Services, args);
    return;
}
```

好處：K8s 保證只跑一次、有獨立的資源配額與逾時、失敗有 `backoffLimit` 重試、執行歷史可查、而且 API Pod 可以自由擴縮不受影響。

### 方案二：分散式鎖

工作必須在應用程式內（需要共用記憶體狀態、或部署形態不允許額外的 Job）時，用資料庫或 Redis 做互斥：

```csharp
private async Task<bool> TryAcquireLockAsync(AppDbContext db, string jobName, CancellationToken ct)
{
    try
    {
        db.JobLocks.Add(new JobLock
        {
            JobName = jobName,
            RunDate = DateOnly.FromDateTime(DateTime.UtcNow),   // 唯一索引 (JobName, RunDate)
            AcquiredBy = Environment.MachineName,
            AcquiredAt = DateTimeOffset.UtcNow
        });
        await db.SaveChangesAsync(ct);
        return true;
    }
    catch (DbUpdateException)
    {
        return false;      // 唯一約束衝突 = 別人已經搶到了
    }
}
```

關鍵是**靠資料庫的唯一索引做互斥**，而不是「先查再插」——後者有競爭視窗（第 09 章）。

Oracle 上也可以用 `SELECT ... FOR UPDATE NOWAIT` 或 `DBMS_LOCK`。要注意鎖必須有過期機制，否則持有鎖的 Pod 被砍掉之後，那個工作就永遠不會再執行了。

### 方案三：Leader Election

只讓一個 Pod 扮演 leader，所有排程工作在 leader 上執行。K8s 有現成的 `Lease` 資源可以用，但實作起來比前兩個方案複雜（要處理續約、失效轉移、腦裂），除非有多個工作需要協調，否則不值得。

---

## 三、Hangfire：帶持久化的背景工作

`BackgroundService` 的工作**存在記憶體裡**——Pod 重啟就沒了。如果需要「這個工作一定要執行」的保證，就需要持久化的佇列。

Hangfire 把工作存進資料庫：

```csharp
builder.Services.AddHangfire(config => config
    .UseOracleStorage(builder.Configuration.GetConnectionString("Default")));

builder.Services.AddHangfireServer(options =>
{
    options.WorkerCount = 5;
    options.Queues = new[] { "critical", "default" };
});

app.UseHangfireDashboard("/hangfire");   // ⚠️ 一定要加授權
```

四種排入方式：

```csharp
// 立即執行（背景）
BackgroundJob.Enqueue<IEmailService>(x => x.SendAsync(userId, "welcome"));

// 延遲執行
BackgroundJob.Schedule<IEmailService>(x => x.SendReminderAsync(orderId),
                                      TimeSpan.FromDays(3));

// 週期性
RecurringJob.AddOrUpdate<IReportService>("daily-report",
    x => x.GenerateAsync(), Cron.Daily(9));

// 接續（前一個成功才執行）
var id = BackgroundJob.Enqueue<IOrderService>(x => x.ProcessAsync(orderId));
BackgroundJob.ContinueJobWith<IEmailService>(id, x => x.SendConfirmationAsync(orderId));
```

### 3.1 Hangfire 的多副本行為

**這是它相對 `BackgroundService` 的關鍵優勢：** 多個 Pod 都跑 Hangfire server 時，它們共用同一個資料庫佇列，工作只會被其中一個取走。`RecurringJob` 也只會觸發一次。

所以開頭那個「寄了三封信」的問題，用 Hangfire 就不存在。

### 3.2 三個實務注意事項

**方法必須可序列化。** Hangfire 存的是「呼叫哪個方法、參數是什麼」，所以參數必須能序列化。傳實體物件是壞習慣——存的是舊快照，執行時資料可能已經變了。**傳 ID，執行時重新查。**

```csharp
// ❌ 序列化整個物件，執行時可能已經過期
BackgroundJob.Enqueue<IOrderService>(x => x.ProcessAsync(order));

// ✅ 傳 ID
BackgroundJob.Enqueue<IOrderService>(x => x.ProcessAsync(order.Id));
```

**工作必須冪等。** Hangfire 預設會自動重試（10 次，指數退避）。加上「執行成功但標記失敗」的可能性，同一個工作可能被執行多次。第 09 章的冪等性原則在這裡完全適用。

**Dashboard 必須加授權。** `/hangfire` 預設**只允許本機存取**，但很多人為了遠端查看而放寬設定，結果把「可以觸發任意工作、刪除佇列」的介面公開到網路上。要自訂授權：

```csharp
public class HangfireAuthFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var httpContext = context.GetHttpContext();
        return httpContext.User.Identity?.IsAuthenticated == true
               && httpContext.User.IsInRole("Admin");
    }
}

app.UseHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization = new[] { new HangfireAuthFilter() }
});
```

### 3.3 什麼時候用哪個

| | `BackgroundService` | Hangfire | K8s CronJob |
| --- | --- | --- | --- |
| 持久化 | ✗（重啟即失） | ✓ | ✓（Job 物件） |
| 多副本安全 | ✗ | ✓ | ✓ |
| 重試 | 自己寫 | 內建 | `backoffLimit` |
| 儀表板 | ✗ | ✓ | `kubectl` |
| 額外依賴 | 無 | 資料庫表 | 無 |
| 適合 | 常駐輪詢、記憶體佇列消費 | 使用者觸發的非同步工作 | 定時批次作業 |

實務上三者常常並存：K8s CronJob 跑每日批次、Hangfire 處理「使用者按下按鈕後非同步執行」的工作、`BackgroundService` 跑 outbox 輪詢這類高頻的常駐任務。

---

## 四、`Channel<T>`：程序內的生產者—消費者

需要「請求快速回應，實際工作稍後處理」而**不需要持久化**時，`Channel<T>` 是最輕量的選擇：

```csharp
public class TaskQueue
{
    private readonly Channel<Func<CancellationToken, ValueTask>> _channel =
        Channel.CreateBounded<Func<CancellationToken, ValueTask>>(
            new BoundedChannelOptions(100)
            {
                FullMode = BoundedChannelFullMode.Wait      // 滿了就等，形成背壓
            });

    public ValueTask EnqueueAsync(Func<CancellationToken, ValueTask> work, CancellationToken ct)
        => _channel.Writer.WriteAsync(work, ct);

    public IAsyncEnumerable<Func<CancellationToken, ValueTask>> ReadAllAsync(CancellationToken ct)
        => _channel.Reader.ReadAllAsync(ct);
}

public class QueuedHostedService : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var work in _queue.ReadAllAsync(stoppingToken))
        {
            try { await work(stoppingToken); }
            catch (Exception ex) { _logger.LogError(ex, "佇列工作失敗"); }
        }
    }
}
```

**用 `CreateBounded` 而不是 `CreateUnbounded`。** 無界佇列在消費速度跟不上時會無限成長，最終 OOMKilled。有界佇列在滿的時候讓生產者等待（背壓），把壓力反映回去而不是累積在記憶體。

必須清楚它的限制：**工作只存在記憶體，Pod 重啟就全部遺失。** 適合「掉了也沒關係」的工作（寄通知、更新統計、清理暫存）。任何「一定要完成」的工作都要用 Hangfire 或訊息佇列。

這是第 06 章「不要 fire-and-forget」的正解——不要 `_ = Task.Run(...)`，而是進佇列由專門的消費者處理，這樣才有 scope 管理、例外處理、以及關機時的收尾。

---

## 五、Outbox 投遞服務

第 09 章的 outbox 模式需要一個投遞者：

```csharp
public class OutboxPublisher : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(5));

        while (await timer.WaitForNextTickAsync(ct))
        {
            try
            {
                using var scope = _scopeFactory.CreateScope();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                var publisher = scope.ServiceProvider.GetRequiredService<IMessagePublisher>();

                var messages = await db.OutboxMessages
                    .Where(m => m.ProcessedAt == null && m.RetryCount < 5)
                    .OrderBy(m => m.CreatedAt)
                    .Take(100)
                    .ToListAsync(ct);

                foreach (var message in messages)
                {
                    try
                    {
                        await publisher.PublishAsync(message, ct);
                        message.ProcessedAt = DateTimeOffset.UtcNow;
                    }
                    catch (Exception ex)
                    {
                        message.RetryCount++;
                        message.LastError = ex.Message[..Math.Min(500, ex.Message.Length)];
                        _logger.LogWarning(ex, "Outbox 訊息 {Id} 投遞失敗", message.Id);
                    }
                }

                await db.SaveChangesAsync(ct);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Outbox 輪詢失敗");
            }
        }
    }
}
```

四個設計要點：

**多副本要處理競爭。** 三個 Pod 同時輪詢會取到同一批訊息。Oracle 上可以用 `SELECT ... FOR UPDATE SKIP LOCKED`（第 09 章）——每個 worker 各自鎖住不同的列，天然分工。

**保留訊息順序時要小心。** `OrderBy(CreatedAt)` 加上並行處理，順序其實沒有保證。需要嚴格順序就得單執行緒處理，或按聚合根分區。

**重試次數要有上限。** 超過就標記為毒性訊息移到另一張表，並告警。否則一則永遠失敗的訊息會佔滿每一輪的處理額度。

**已處理的訊息要清理。** 加一個定期刪除的工作，否則 outbox 表會無限成長。

---

## 六、關機時的處理

第 00 章講過關機序列。對背景工作而言，關鍵是 `StopAsync` 有時間限制（`ShutdownTimeout`，預設 30 秒）。

```csharp
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (await timer.WaitForNextTickAsync(stoppingToken))
    {
        // 開始一輪工作前先檢查，避免在快關機時開始新的長工作
        if (stoppingToken.IsCancellationRequested) break;

        await ProcessBatchAsync(stoppingToken);
    }

    _logger.LogInformation("背景服務已停止");
}
```

如果單一輪工作可能超過 30 秒，要同步調整三個地方：`HostOptions.ShutdownTimeout`、K8s 的 `terminationGracePeriodSeconds`、以及工作本身的分批大小（讓每一批都能在寬限期內完成）。

更穩健的設計是**讓工作可以中斷並在下次繼續**——處理到哪裡記錄在資料庫裡，重啟後從斷點接續。這樣就不怕被砍。

---

## 七、常見誤解

**「背景工作放在 API 裡比較方便。」**
它會隨著 API 的副本數一起複製。定時任務用 K8s CronJob，需要保證只跑一次的用 Hangfire 或分散式鎖。

**「`BackgroundService` 的例外會被記錄然後繼續。」**
.NET 6 起預設會**停止整個 Host**。迴圈內要自己 try-catch，或明確接受服務停止並讓監控發現。

**「用 `Task.Delay` 做週期性工作。」**
週期會漂移（實際間隔 = 工作時間 + 延遲時間）。用 `PeriodicTimer`。

**「`_ = Task.Run(...)` 就能做背景處理。」**
沒有 scope 管理（DbContext 可能已 dispose）、例外被吞掉、關機時不會被等待。用 `Channel<T>` + `BackgroundService`。

**「Hangfire 的工作可以傳實體物件。」**
它會被序列化存起來，執行時是舊快照。傳 ID，執行時重新查。

**「Hangfire dashboard 只有內部人看得到。」**
放寬本機限制後就是公開的，而它能觸發任意工作、刪除佇列。一定要加授權 filter。

---

## 八、同事會來問你的問題

**Q：擴容之後通知信寄了三次。**
`BackgroundService` 在每個 Pod 都跑一份。改用 K8s CronJob（排程工作的正解），或用 Hangfire（共用資料庫佇列，只會被一個 worker 取走），或自己用唯一索引做分散式鎖。

**Q：背景服務跑了幾天就不見了，也沒有錯誤。**
可能是 `BackgroundServiceExceptionBehavior` 被設成 `Ignore`，例外讓 `ExecuteAsync` 結束但沒有任何跡象。改成在迴圈內處理例外，並對「上次執行時間」設監控告警。

**Q：`BackgroundService` 裡怎麼用 `DbContext`？**
注入 `IServiceScopeFactory`，每一輪工作用 `using var scope = factory.CreateScope()` 開 scope 再解析。scope 要開在迴圈內，對應一個邏輯工作單元。

**Q：Pod 啟動時卡住，probe 一直失敗但 log 沒東西。**
某個 `IHostedService` 的 `ExecuteAsync` 在第一個 await 之前有同步阻塞，卡住整個 Host 啟動。在開頭加 `await Task.Yield()`，或把初始化移到 `ApplicationStarted` 回呼。

**Q：Hangfire 的工作重複執行了。**
它預設會重試，加上「執行成功但標記失敗」的可能性，同一個工作可能跑多次。工作必須冪等——用冪等鍵或在執行前檢查狀態。

**Q：outbox 三個 Pod 一起輪詢會不會重複投遞？**
會。Oracle 上用 `SELECT ... FOR UPDATE SKIP LOCKED` 讓每個 worker 鎖住不同的列，天然分工且不互相等待。

**Q：關機時進行中的背景工作會被砍掉嗎？**
`StopAsync` 有 `ShutdownTimeout`（預設 30 秒）的限制，超過就強制結束。工作可能超時的話要調整三個值（HostOptions、terminationGracePeriodSeconds、批次大小），更好的做法是讓工作可以中斷並從斷點續跑。

---

## 連結

- [[basics-07-dependency-injection-and-services]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[18-resilience-and-performance]] — 上一章
- [[20-testing]] — 下一章：測試策略
- [[00-hosting-and-startup]] — IHostedService 的啟動與關機
- [[02-dependency-injection]] — `IServiceScopeFactory` 的正確用法
- [[09-transactions-and-concurrency]] — outbox 模式與冪等性
- [[hangfire]] — Hangfire entity 頁
