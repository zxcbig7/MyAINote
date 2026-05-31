---
type: entity
domain: tech
tags: [hangfire, background-jobs, scheduling, dotnet, csharp, aspnet-core, sql-server]
sources:
  - https://github.com/HangfireIO/Hangfire
  - https://docs.hangfire.io/en/latest/
created: 2026-05-31
updated: 2026-05-31
---

# Hangfire

Hangfire 是 .NET 的背景工作處理框架，不需要 Windows Service 或獨立 Process，直接在 ASP.NET Core 應用程式內執行。工作狀態持久化到資料庫，即使應用程式重啟也不會遺失。

## 核心概念

| 概念 | 說明 |
| --- | --- |
| **Job** | 序列化的方法呼叫（type + method + arguments） |
| **Queue** | 待執行的 job 清單，worker 從此取件 |
| **Server** | 背景執行緒池，輪詢 queue 並執行 job |
| **Storage** | 持久化 job 狀態的後端（SQL Server、Redis 等） |
| **Dashboard** | 內建 Web UI，可檢視、重試、刪除 job |

Hangfire 使用 **expression tree**（非 delegate）序列化工作，序列化內容包含 type name、method name、parameter types、arguments。

## 安裝

```xml
<!-- .csproj -->
<ItemGroup>
  <PackageReference Include="Hangfire.Core" Version="1.8.*" />
  <PackageReference Include="Hangfire.SqlServer" Version="1.8.*" />
  <PackageReference Include="Hangfire.AspNetCore" Version="1.8.*" />
  <PackageReference Include="Microsoft.Data.SqlClient" Version="*" />
</ItemGroup>
```

## ASP.NET Core 設定

### appsettings.json

```json
{
  "ConnectionStrings": {
    "Hangfire": "Server=.\\sqlexpress;Database=HangfireDB;Integrated Security=SSPI;"
  },
  "Logging": {
    "LogLevel": {
      "Hangfire": "Information"
    }
  }
}
```

### Program.cs

```csharp
using Hangfire;
using Hangfire.SqlServer;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHangfire(config => config
    .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
    .UseSimpleAssemblyNameTypeSerializer()
    .UseRecommendedSerializerSettings()
    .UseSqlServerStorage(builder.Configuration.GetConnectionString("Hangfire"), new SqlServerStorageOptions
    {
        CommandBatchMaxTimeout = TimeSpan.FromMinutes(5),
        SlidingInvisibilityTimeout = TimeSpan.FromMinutes(5),
        QueuePollInterval = TimeSpan.Zero,
        UseRecommendedIsolationLevel = true,
        DisableGlobalLocks = true
    }));

builder.Services.AddHangfireServer();

var app = builder.Build();

app.UseRouting();
app.UseAuthorization();

app.UseHangfireDashboard();        // 預設路徑：/hangfire

app.MapControllers();

app.Run();
```

SQL Server 首次啟動時會自動建立 Hangfire schema（約 7 張資料表）。

## Job 類型

### Fire-and-Forget（立即執行）

呼叫後立刻入 queue，worker 取得後執行。

```csharp
BackgroundJob.Enqueue(() => Console.WriteLine("Hello, world!"));

// 使用 DI 注入的 service（推薦）
BackgroundJob.Enqueue<IEmailService>(svc => svc.SendAsync(userId, "Welcome!"));
```

### Delayed（延遲執行）

在指定時間後才入 queue。

```csharp
BackgroundJob.Schedule(
    () => Console.WriteLine("Delayed!"),
    TimeSpan.FromMinutes(30));

// 或指定絕對時間
BackgroundJob.Schedule<IReportService>(
    svc => svc.GenerateMonthlyReport(),
    DateTimeOffset.UtcNow.AddDays(1));
```

Server 預設每 **15 秒** 輪詢一次排程表。可調整：

```csharp
builder.Services.AddHangfireServer(options =>
{
    options.SchedulePollingInterval = TimeSpan.FromSeconds(5);
});
```

### Recurring（週期執行）

依 cron 表達式反覆觸發，每次觸發時建立一個 fire-and-forget job。

```csharp
// 使用內建 Cron helper
RecurringJob.AddOrUpdate(
    "daily-cleanup",
    () => Console.WriteLine("Cleanup!"),
    Cron.Daily);

// 使用 cron 表達式
RecurringJob.AddOrUpdate<IReportService>(
    "weekly-report",
    svc => svc.SendWeeklyReport(),
    "0 8 * * 1");            // 每週一 08:00 UTC

// 移除
RecurringJob.RemoveIfExists("daily-cleanup");

// 立即觸發一次
RecurringJob.Trigger("weekly-report");
```

`Cron` 類別提供的 helper：`Cron.Minutely`、`Cron.Hourly`、`Cron.Daily`、`Cron.Weekly`、`Cron.Monthly`、`Cron.Yearly`。

> 時區預設為 UTC。1.8+ 可在第四個參數指定 `TimeZoneInfo.FindSystemTimeZoneById("Asia/Taipei")`。

### Continuations（串接執行）

前一個 job 成功完成後才執行。

```csharp
var jobId = BackgroundJob.Enqueue(() => Console.WriteLine("Step 1"));

BackgroundJob.ContinueJobWith(
    jobId,
    () => Console.WriteLine("Step 2, runs after Step 1"));
```

## Dependency Injection

推薦使用 instance method 而非 static method，讓 Hangfire 透過 DI container 解析依賴。

```csharp
// 定義 service
public class EmailService
{
    private readonly ISmtpClient _smtp;

    public EmailService(ISmtpClient smtp)  // 由 DI 注入
    {
        _smtp = smtp;
    }

    public async Task SendAsync(int userId, string message)
    {
        // ...
    }
}

// 入 queue
BackgroundJob.Enqueue<EmailService>(svc => svc.SendAsync(userId, message));
```

`Hangfire.AspNetCore` 套件自動整合 ASP.NET Core 的 DI container，不需要額外設定 `JobActivator`。

> 注意：job 執行時 **沒有 HttpContext**，request-scoped 的 dependency 會失敗。改用 Transient 或 Singleton scope。

## Dashboard

```csharp
// 基本掛載（預設 /hangfire，僅限 localhost）
app.UseHangfireDashboard();

// 自訂路徑與存取控制
app.UseHangfireDashboard("/jobs", new DashboardOptions
{
    Authorization = new[] { new HangfireAuthFilter() },
    IsReadOnlyFunc = ctx => !ctx.GetHttpContext().User.IsInRole("Admin")
});
```

實作授權 filter：

```csharp
public class HangfireAuthFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var http = context.GetHttpContext();
        return http.User.Identity?.IsAuthenticated ?? false;
    }
}
```

> 生產環境**必須**設定授權 filter，否則預設只有 localhost 能存取。

## 例外處理與重試

### 預設行為

job 拋出例外時 Hangfire 自動重試，預設最多 **10 次**，每次間隔時間遞增（指數退避）。

### 自訂重試次數

```csharp
// 單一 method
[AutomaticRetry(Attempts = 3)]
public void ProcessOrder(int orderId) { ... }

// 完全停用重試
[AutomaticRetry(Attempts = 0)]
public void SendOnce() { ... }

// 全域修改預設值（Program.cs）
builder.Services.AddHangfire(config => config
    // ...
    .WithJobExpirationTimeout(TimeSpan.FromDays(7)));

GlobalJobFilters.Filters.Add(new AutomaticRetryAttribute { Attempts = 5 });
```

### 失敗狀態

超過重試上限後 job 狀態變為 `Failed`，在 Dashboard 可手動重試或刪除，不會自動過期。

## SQL Server Storage 選項說明

| 選項 | 建議值 | 說明 |
| --- | --- | --- |
| `SlidingInvisibilityTimeout` | `5 min` | worker 處理中的 job 鎖定時間 |
| `QueuePollInterval` | `TimeSpan.Zero` | 搭配 SlidingInvisibilityTimeout 使用，近即時輪詢 |
| `CommandBatchMaxTimeout` | `5 min` | 批次 SQL 指令最大逾時 |
| `UseRecommendedIsolationLevel` | `true` | 使用 Read Committed 避免鎖定問題 |
| `DisableGlobalLocks` | `true` | 停用全域鎖（需 Schema 7+，避免 distributed lock 衝突） |

## Job 生命週期

```
Enqueue / Schedule
    ↓
Enqueued（在 queue 等待）
    ↓
Processing（worker 取件，開始執行）
    ↓ 成功              ↓ 例外
Succeeded          Failed / Scheduled（重試）
```

## 適用時機

| 場景 | 建議 Job 類型 |
| --- | --- |
| 寄送驗證信（非同步，不擋 request） | Fire-and-Forget |
| 30 分鐘後自動取消訂單 | Delayed |
| 每天凌晨清理舊資料 | Recurring |
| 圖片上傳後產生縮圖，再通知使用者 | Continuations |

## 注意事項

- Job method **必須是 public**，且參數需可 JSON 序列化
- 避免在 job 中存取 `HttpContext`（執行時無 request context）
- Recurring job 的時間以 **UTC** 為基準
- 同一台機器多個 process 都掛 `AddHangfireServer` 時，worker 會競爭同一個 queue（這是設計行為，可水平擴展）
- 若需要分散式部署，確保所有 instance 連到同一個 Storage

## 連結

- [[cron-expression]] — Recurring job 的排程語法
- [[csharp]] — C# 語言基礎
- [[kubernetes]] — K8s 上部署時需考量 CronJob vs Hangfire 的取捨
