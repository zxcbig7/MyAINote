---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, deployment, logging, structured-logging, health-checks, docker, dockerfile, kestrel, reverse-proxy, forwarded-headers, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 10：測試、部署與正式上線準備.md
  - https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-10.0
  - https://learn.microsoft.com/en-us/aspnet/core/fundamentals/servers/kestrel/endpoints?view=aspnetcore-10.0
  - https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/proxy-load-balancer?view=aspnetcore-10.0
  - https://github.com/dotnet/dotnet-docker/blob/main/README.aspnet.md
created: 2026-11-01
updated: 2026-11-01
---

# 入門第 16 章：部署與上線 — 怎麼安全地上線，上線後怎麼知道它活著

## 三個 Pod 同時重啟的夜晚

某個團隊把 API 放上 Kubernetes 時，從網路上抄了一段 health check：端點裡跑一次 `SELECT 1`，資料庫答得出來就回 200，答不出來就回 503。他們把同一個端點同時設成 liveness 與 readiness probe，測試環境跑得很順。某天凌晨資料庫做例行維護，連線中斷了三十秒。三個 Pod 的探針在同一段時間內連續失敗，Kubernetes 的判斷很單純：這幾個程序壞了，重啟。於是三個 Pod 一起被殺掉、一起重新啟動，啟動時又去連還沒回來的資料庫，再次失敗，再次重啟。資料庫三十秒後恢復，API 卻又掙扎了好幾分鐘才站穩。更麻煩的是事後查原因：log 是一行行純文字，`Task 8f14... failed`，想知道失敗的請求是誰發的、花了多久，只能用眼睛一行行看。

這個故事裡有兩個獨立的錯誤，也是本章要回答的兩個問題。第一個，程式上線後，要怎麼知道它活著，以及活著的意思是什麼：「程序還在跑」和「現在能正確處理請求」是兩件事，混在一起就會出事。第二個，出事之後，記下來的東西能不能被機器查詢，而不只是給人讀。另外還有第三個比較樸素的問題：程式怎麼被包進一個別人（或叢集）可以直接跑起來的東西，而且不把密碼一起包進去。

[[basics-15-testing]] 結束時，TaskTracker 已經有 30 個單元測試與一組對真實 Oracle 容器跑的整合測試，測試證明的是「你寫下來的預期成立」。本章是入門篇最後一個實作章，做四件事：把 log 改成機器可查詢的結構化格式，加上 live 與 ready 兩個健康檢查端點，讓資料庫連不上時回 503 而不是 500，最後寫一個 Dockerfile 把 API 包成非 root 的映像並實際跑起來。中間會把第一章留下的伏筆收掉：HTTP 版本為什麼在源站常常只有 1.1，並說明 Kestrel 和反向代理各管什麼。

---

## 一、本章對 TaskTracker 做的改動

從 [[basics-15-testing]] 結束的狀態出發，本章新增與修改的檔案只有下面這些。後面每一節會逐一出現，這裡先看全貌，讀到一半迷路時可以回來對照。

| 檔案 | 動作 | 為了什麼 |
| --- | --- | --- |
| `Middleware/RequestLoggingMiddleware.cs` | 修改 | 加上使用者與 trace 欄位、依狀態碼與路徑決定 log 等級 |
| `appsettings.json`、`appsettings.Development.json` | 修改 | 正式環境輸出 JSON，開發環境輸出單行文字 |
| `Extensions/HealthCheckExtensions.cs` | 新增 | `/healthz/live` 與 `/healthz/ready` |
| `Exceptions/DatabaseUnavailableExceptionHandler.cs` | 新增 | 資料庫連不上時回 503 加 `Retry-After` |
| `Program.cs` | 修改 | 註冊並對應上面兩項 |
| `TaskTracker.Api.csproj` | 修改 | 加一個 NuGet 套件 |
| `Dockerfile`、`.dockerignore` | 新增 | 建置非 root 的映像 |

套件只加一個，專案根目錄執行：

```powershell
dotnet add src/TaskTracker.Api package Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore --version 10.0.14
```

這個套件提供 `AddDbContextCheck<TContext>`，後面會用到。

---

## 二、結構化 log：寫給機器查，也寫給人看

### 2.1 同樣一行 log，兩種寫法

ASP.NET Core 的 `ILogger` 有兩種寫法看起來幾乎一樣，輸出的資訊量卻差很多。下面這個小程式用 JSON console 格式把兩種寫法並排印出來（獨立的小專案，不是 TaskTracker 的一部分）：

```csharp
var taskId = Guid.Parse("8f14e45f-ceea-4672-a1d9-0c1b6b7c2f01");
var elapsedMs = 42.1234;

logger.LogInformation("Task {TaskId} marked done in {ElapsedMs:0.0} ms", taskId, elapsedMs);
logger.LogInformation($"Task {taskId} marked done in {elapsedMs:0.0} ms");
```

```text
{"EventId":0,"LogLevel":"Information","Category":"Demo","Message":"Task 8f14e45f-ceea-4672-a1d9-0c1b6b7c2f01 marked done in 42.1 ms","State":{"TaskId":"8f14e45f-ceea-4672-a1d9-0c1b6b7c2f01","ElapsedMs":42.1234,"{OriginalFormat}":"Task {TaskId} marked done in {ElapsedMs:0.0} ms"}}
{"EventId":0,"LogLevel":"Information","Category":"Demo","Message":"Task 8f14e45f-ceea-4672-a1d9-0c1b6b7c2f01 marked done in 42.1 ms","State":{"{OriginalFormat}":"Task 8f14e45f-ceea-4672-a1d9-0c1b6b7c2f01 marked done in 42.1 ms"}}
```

兩筆的 `Message` 一模一樣，人眼讀不出差別。差別在 `State`：第一種寫法（message template）把 `{TaskId}` 與 `{ElapsedMs}` 當成具名欄位保留下來，連 `ElapsedMs` 都保持原本的數字 `42.1234`，`:0.0` 只影響 `Message` 裡顯示的樣子；`{OriginalFormat}` 則是模板本身。第二種寫法在呼叫 `LogInformation` 之前，C# 就已經把字串內插完成，logger 只收到一個成品字串，結構在這一步被丟掉了，`State` 裡什麼欄位都沒有。

這個差別在出事時才顯現。想找「這個任務最近的所有紀錄」，第一種寫法可以在 ELK 之類的 log 平台上直接查 `State.TaskId`；第二種寫法只能對整行字串做全文比對，一旦格式稍微改過就找不到。想統計「同一種事件出現幾次」，第一種用 `{OriginalFormat}` 分組即可，第二種每一行因為值不同而成為一種獨立的訊息。還有一個比較小的差異：內插字串在呼叫前就會被組出來，即使該等級的 log 被設定過濾掉，組字串的成本照樣付出；message template 則等確定要輸出時才格式化。

所以規則很簡單：`ILogger` 的第一個參數永遠是常數模板，值依序傳在後面，不用 `$""`，也不用 `+` 串接。反例要強調，因為編譯器完全不會抱怨，只有輸出的 `State` 默默變空。

### 2.2 TaskTracker 的 request log

[[basics-08-middleware-and-exception-handling]] 寫過一個 `RequestLoggingMiddleware`，記錄方法、路徑、狀態碼與耗時。本章把它補成上線能用的樣子：加上「誰」（使用者 id）和「哪一次」（trace id），並讓 log 等級隨結果改變。修改後的完整檔案：

```csharp
using System.Diagnostics;
using System.Security.Claims;
using Microsoft.IdentityModel.JsonWebTokens;
using TaskTracker.Api.Extensions;

namespace TaskTracker.Api.Middleware;

public sealed class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var started = Stopwatch.GetTimestamp();
        var statusCode = StatusCodes.Status500InternalServerError;
        try
        {
            await _next(context);
            statusCode = context.Response.StatusCode;
        }
        finally
        {
            _logger.Log(
                ResolveLevel(context.Request.Path, statusCode),
                "HTTP {Method} {Path} responded {StatusCode} in {ElapsedMs:0.0} ms (user {UserId}, trace {TraceId})",
                context.Request.Method,
                context.Request.Path,
                statusCode,
                Stopwatch.GetElapsedTime(started).TotalMilliseconds,
                context.User.FindFirstValue(JwtRegisteredClaimNames.Sub) ?? "anonymous",
                Activity.Current?.Id ?? context.TraceIdentifier);
        }
    }

    private static LogLevel ResolveLevel(PathString path, int statusCode)
    {
        if (statusCode >= StatusCodes.Status500InternalServerError)
        {
            return LogLevel.Error;
        }

        return path.StartsWithSegments(HealthCheckExtensions.PathPrefix) ? LogLevel.Debug : LogLevel.Information;
    }
}
```

幾個決定值得說明。使用者 id 取自 token 的 `sub` claim，匿名請求記成 `anonymous`；這裡記的是 id 而不是 email，因為 log 的保存與存取範圍通常比資料庫寬，能不放個資就不放。`TraceId` 用的是 W3C 的 trace-id（`00-<trace>-<span>-00` 那一串），和錯誤回應 `application/problem+json` 的 `traceId` 欄位是同一個值，前端同事貼來一段錯誤回應，就能在 log 裡用它直接找到那次請求。等級的規則有兩條：狀態碼 5xx 一律是 `Error`，這樣告警規則只要盯 Error 即可；`/healthz` 底下的請求降到 `Debug`，因為 Kubernetes 每隔幾秒就會探一次，把它們記成 Information 會讓真正的請求淹沒在探針裡，而正式環境的 `Default` 等級是 Information，Debug 不會出現。（`Debug` 這一刀只對成功的探針有效，探針失敗是 5xx，仍然是 Error，這是刻意的。）

這個 middleware 在 `Program.cs` 裡放在 pipeline 最外層，位於 `UseExceptionHandler` 之前，原因是它要記到的是例外處理完之後的最終狀態碼，順序的道理在 [[basics-08-middleware-and-exception-handling]]。

### 2.3 開發看文字，正式輸出 JSON

人在開發機上看 log，要的是一行一筆、能一眼掃過；log 平台收 log，要的是每筆能被解析。同一份程式碼可以兩者兼顧，因為輸出格式屬於設定，不屬於程式。`appsettings.json` 寫正式環境要的 JSON，`appsettings.Development.json` 覆寫成單行文字，疊層規則 [[basics-09-configuration-and-environments]] 已經講過。

`appsettings.json` 新增 `Logging:Console`：

```json
"Console": {
  "FormatterName": "json",
  "FormatterOptions": {
    "IncludeScopes": true,
    "UseUtcTimestamp": true,
    "TimestampFormat": "yyyy-MM-ddTHH:mm:ss.fffZ"
  }
}
```

`appsettings.Development.json` 覆寫：

```json
"Console": {
  "FormatterName": "simple",
  "FormatterOptions": {
    "SingleLine": true,
    "IncludeScopes": false,
    "UseUtcTimestamp": false,
    "TimestampFormat": "HH:mm:ss "
  }
}
```

時間一律用 UTC 是上線後的習慣：同一個服務多個副本、叢集在不同時區的節點，log 平台排序時才不會錯亂。

重新建置並在開發環境啟動後，登入、查任務、故意查一個不存在的任務、再不帶 token 打一次，console 上的 request log 會長這樣（只留這幾行，其餘是 EF Core 的 SQL）：

```text
07:29:42 info: TaskTracker.Api.Middleware.RequestLoggingMiddleware[0] HTTP POST /api/v1/auth/login responded 200 in 598.2 ms (user anonymous, trace 00-d9f2d9913413d95174dbb64956fdd942-0cbf1ad1e6cff340-00)
07:29:43 info: TaskTracker.Api.Middleware.RequestLoggingMiddleware[0] HTTP GET /api/v1/tasks responded 200 in 340.8 ms (user 1f94e144-f6eb-449e-bc48-20f0d7bc0fd4, trace 00-c4fc4523b498461bfdacde1130403a52-51197345080036d6-00)
07:29:44 info: TaskTracker.Api.Middleware.RequestLoggingMiddleware[0] HTTP GET /api/v1/tasks responded 401 in 12.6 ms (user anonymous, trace 00-754c174330bf0552d5fabab2a047afe4-ac8b0bf6c5077051-00)
```

換成 Production 環境後（第五節的容器預設就是 Production；在本機要重現，得設 `ASPNETCORE_ENVIRONMENT=Production`，而且 User Secrets 只在 Development 載入，連線字串與簽章金鑰要改用環境變數提供），同樣的請求輸出變成 JSON，一行一筆，下面把最後一筆（401）展開，省略 `Scopes`（記錄 ConnectionId、RequestId 等，內容與 State 的 TraceId 重疊）：

```text
{
    "Timestamp":  "2026-10-31T23:29:52.257Z",
    "EventId":  0,
    "LogLevel":  "Information",
    "Category":  "TaskTracker.Api.Middleware.RequestLoggingMiddleware",
    "Message":  "HTTP GET /api/v1/tasks responded 401 in 46.3 ms (user anonymous, trace 00-75f6615ed62bc2d60f95c308b54ad11a-ca2f4923917892cb-00)",
    "State":  {
                  "Method":  "GET",
                  "Path":  "/api/v1/tasks",
                  "StatusCode":  401,
                  "ElapsedMs":  46.2948,
                  "UserId":  "anonymous",
                  "TraceId":  "00-75f6615ed62bc2d60f95c308b54ad11a-ca2f4923917892cb-00",
                  "{OriginalFormat}":  "HTTP {Method} {Path} responded {StatusCode} in {ElapsedMs:0.0} ms (user {UserId}, trace {TraceId})"
              },
    ...
}
```

模板裡的每一個 `{Xxx}` 都成了 `State` 的一個欄位，`StatusCode` 是數字 401 而不是字串，`ElapsedMs` 保留 46.2948。有了這些欄位，log 平台才能做「5 分鐘內 `StatusCode >= 500` 的筆數」「`ElapsedMs` 的 p95」這類查詢，不需要寫任何正規表示式。

輸出到 stdout 而不是寫檔，是容器環境的慣例：容器平台負責收集每個容器的 stdout，應用程式不用管輪替與路徑。收集之後怎麼匯集、保存多久、哪些東西不能記（密碼、token、完整的個資），以及 Serilog 與內建 logging 的取捨，是 [[16-logging-and-observability]] 的內容。

---

## 三、Health checks：活著，和準備好，是兩個問題

### 3.1 兩個端點，兩種問題

開頭的故事裡，同一個端點被拿去回答兩個不同的問題。Kubernetes 的探針（probe）有兩種主要用途，各自失敗時的後果完全不同：

- liveness：這個程序還活著嗎？失敗的後果是殺掉容器並重啟。
- readiness：這個程序現在可以接請求嗎？失敗的後果是把這個 Pod 從 Service 的流量清單中拿掉，不重啟，等它恢復再放回來。

把這兩個後果放在資料庫短暫中斷的場景裡看，答案就出來了。資料庫掛了，重啟 API 程序對資料庫毫無幫助，API 依然連不上，所以 liveness 不該檢查資料庫；但在資料庫恢復之前，把流量導到這些 Pod 上只會得到錯誤，從負載平衡裡拿掉是對的，所以 readiness 應該檢查資料庫。如果 liveness 碰資料庫，所有副本會在同一時間一起失敗、一起被重啟，這就是開頭的連鎖反應；readiness 失敗則只是暫時停止接流量，沒有任何東西被重啟。Kubernetes 端的探針參數（`initialDelaySeconds`、`failureThreshold`）與連線池在多副本下的行為，見 [[57-database-connections]]；ASP.NET Core 這邊的 health check 設計見 [[16-logging-and-observability]]。

### 3.2 TaskTracker 的實作

`Extensions/HealthCheckExtensions.cs`：

```csharp
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using TaskTracker.Api.Data;

namespace TaskTracker.Api.Extensions;

public static class HealthCheckExtensions
{
    public const string PathPrefix = "/healthz";
    public const string LivePath = PathPrefix + "/live";
    public const string ReadyPath = PathPrefix + "/ready";

    private const string ReadyTag = "ready";

    public static IServiceCollection AddTaskTrackerHealthChecks(this IServiceCollection services)
    {
        services.AddHealthChecks()
            .AddDbContextCheck<AppDbContext>("database", tags: [ReadyTag]);
        return services;
    }

    public static WebApplication MapTaskTrackerHealthChecks(this WebApplication app)
    {
        app.MapHealthChecks(LivePath, new HealthCheckOptions { Predicate = _ => false }).AllowAnonymous();
        app.MapHealthChecks(ReadyPath, new HealthCheckOptions { Predicate = check => check.Tags.Contains(ReadyTag) }).AllowAnonymous();
        return app;
    }
}
```

重點在兩個 `Predicate`。health check 的註冊是一份清單，每個檢查可以掛 tag；每個端點用 `Predicate` 決定要跑清單中的哪些。live 的 `Predicate` 永遠回 `false`，意思是一個檢查都不跑，只要這個端點還能回應，就證明程序、Kestrel 與 pipeline 都還活著。ready 只跑掛了 `ready` tag 的檢查，目前就是 `database`，內部呼叫 `DbContext` 的 `CanConnectAsync`。以後 API 若多了一個外部相依，例如寄信的 SMTP，新增檢查時掛上同一個 tag，ready 就自動涵蓋。

`.AllowAnonymous()` 在目前的 TaskTracker 裡其實不是必要的：`[Authorize]` 寫在各個 controller 上，`MapHealthChecks` 建立的端點沒有任何授權 metadata，本來就不需要 token。但它是便宜的保險。團隊常在上線前加固時改成「全站預設要求登入」（`FallbackPolicy` 或 `MapControllers().RequireAuthorization()`），一旦這麼做，探針沒有 token，Kubernetes 會一直收到 401 並當成失敗，對 liveness 而言就是不斷重啟。端點明確標成匿名，這類全域改動就不會連帶弄壞探針。回應內容只有 `Healthy` 或 `Unhealthy` 一個字，不回各個檢查的細節，因為端點是匿名的，任何人都能打，不應該洩漏資料庫位址或內部元件名稱。

`Program.cs` 加兩行：

```csharp
builder.Services.AddTaskTrackerHealthChecks();
// ... 其餘服務註冊
app.MapTaskTrackerHealthChecks();
```

`AddTaskTrackerHealthChecks` 接在 `AddTaskTrackerDatabase` 之後，`MapTaskTrackerHealthChecks` 接在 `app.MapControllers()` 之後。

### 3.3 資料庫關掉的時候

啟動 API（開發環境即可，資料庫要先在跑），資料庫正常時兩個端點都是 200：

```powershell
curl.exe -s -i http://localhost:5080/healthz/ready
```

```text
HTTP/1.1 200 OK
Content-Type: text/plain
Cache-Control: no-store, no-cache
...

Healthy
```

（`Date`、`Server`、`Expires`、`Pragma`、`Transfer-Encoding` 等標頭省略；`Cache-Control: no-store, no-cache` 是 health check 端點預設就會加的，避免探針結果被中間層快取。）接著關掉 Oracle 容器，再各打一次：

```powershell
docker stop tasktracker-oracle
curl.exe -s -i http://localhost:5080/healthz/live
curl.exe -s -i http://localhost:5080/healthz/ready
```

```text
HTTP/1.1 200 OK
...
Healthy

HTTP/1.1 503 Service Unavailable
...
Unhealthy
```

live 仍然是 200，ready 變成 503。這就是兩個端點該有的行為：資料庫掛了，Kubernetes 看到的是「程序活著，但暫時不接流量」。同一段時間的伺服器 console 也記下了這件事：

```text
07:30:18 fail: TaskTracker.Api.Middleware.RequestLoggingMiddleware[0] HTTP GET /healthz/ready responded 503 in 4216.1 ms (user anonymous, trace 00-729cd23e34941acdfad00abc9f5319cc-341cd2f66565b35c-00)
```

這一行有兩個值得留意的地方。等級是 `fail`（Error），符合前面「5xx 都記 Error」的規則，資料庫掛掉時探針每失敗一次就會有一筆，告警規則自然會觸發。耗時是 4216 毫秒，因為 `ready` 檢查要等 Oracle 連線逾時才知道連不上。Kubernetes 的探針預設 `timeoutSeconds` 是 1 秒，所以實際上探針常常是「逾時」而不是收到 503，兩者效果相同，但如果日後要調整探針參數，需要知道這個數字：檢查本身的耗時會直接影響探針的行為。

資料庫重新啟動後，API 不需要重啟。Oracle 容器從 `docker start` 到真的能接連線要等一段時間（容器的 healthcheck 轉為 healthy 才算好，通常要幾十秒），所以先等容器健康，再輪詢 `/healthz/ready`：

```powershell
docker start tasktracker-oracle
do { Start-Sleep -Seconds 3; $health = docker inspect --format "{{.State.Health.Status}}" tasktracker-oracle } while ($health -ne 'healthy')
curl.exe -s -o NUL -w "%{http_code}" http://localhost:5080/healthz/ready
```

```text
200
```

資料庫一回來，第一次輪詢就是 200。如果不等容器健康就打，會先看到幾次 503，然後轉成 200，這也是正確的行為。

連線池會自行丟棄壞掉的連線並重建，這也是為什麼「重啟 API」對資料庫抖動沒有幫助。

---

## 四、資料庫連不上：回 500 還是 503

### 4.1 [[basics-02-rest-api-design]] 留下的問題

第二章在談 500 與 503 時，TaskTracker 的資料庫連不上會回 500：沒有人接住的例外，框架統一轉成 `500 Internal Server Error`。當時就說明了 503 的語意：「我知道自己現在無法服務，晚點再來」，可以搭配 `Retry-After`。現在有了健康檢查、有了真正會暫時中斷的資料庫，這個取捨該決定了。

兩種回應對呼叫端的訊息不同。500 說的是「我出錯了，原因我自己也沒預料到」，客戶端通常不會自動重試（重試一個程式 bug 沒有意義），告警系統看到的是「疑似程式缺陷」。503 說的是「這是暫時的」，重試元件與前端可以據此安排退避重試，維運看到的是「相依服務出問題」而不是「有 bug」，兩者的處理流程不同。TaskTracker 決定：已經確認是「資料庫暫時連不上」的錯誤回 503，其他任何沒預期到的例外維持 500。判準是能不能把錯誤明確分類成暫時性；分類不出來的例外，回 500 是誠實的。

### 4.2 實作：一個 `IExceptionHandler`

[[basics-08-middleware-and-exception-handling]] 已經用 `DomainExceptionHandler` 把業務例外轉成 ProblemDetails，這次是同一個機制再加一個處理器。`Exceptions/DatabaseUnavailableExceptionHandler.cs`：

```csharp
using System.Globalization;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Net.Http.Headers;
using Oracle.ManagedDataAccess.Client;

namespace TaskTracker.Api.Exceptions;

public sealed class DatabaseUnavailableExceptionHandler : IExceptionHandler
{
    public const int RetryAfterSeconds = 5;

    // ORA-50201 是 ODP.NET 對「連不上伺服器」的統一包裝，ORA-12541 這類細節在內層；其餘是 Oracle 文件列出的「資料庫暫時不可用」錯誤
    private static readonly HashSet<int> UnavailableErrorNumbers = [50201, 12541, 12514, 12170, 12545, 3113, 3114, 1033, 1034];

    private readonly IProblemDetailsService _problemDetailsService;
    private readonly ILogger<DatabaseUnavailableExceptionHandler> _logger;

    public DatabaseUnavailableExceptionHandler(IProblemDetailsService problemDetailsService, ILogger<DatabaseUnavailableExceptionHandler> logger)
    {
        _problemDetailsService = problemDetailsService;
        _logger = logger;
    }

    public async ValueTask<bool> TryHandleAsync(HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        var oracleError = FindUnavailableError(exception);
        if (oracleError is null)
        {
            return false;
        }

        _logger.LogWarning("Database unavailable (ORA-{OracleErrorNumber}), responding 503 with Retry-After {RetryAfterSeconds}s", oracleError.Number, RetryAfterSeconds);
        httpContext.Response.StatusCode = StatusCodes.Status503ServiceUnavailable;
        httpContext.Response.Headers[HeaderNames.RetryAfter] = RetryAfterSeconds.ToString(CultureInfo.InvariantCulture);
        return await _problemDetailsService.TryWriteAsync(new ProblemDetailsContext
        {
            HttpContext = httpContext,
            Exception = exception,
            ProblemDetails = new ProblemDetails
            {
                Status = StatusCodes.Status503ServiceUnavailable,
                Title = "Service Unavailable",
                Detail = "The database is temporarily unavailable. Retry later."
            }
        });
    }

    private static OracleException? FindUnavailableError(Exception exception)
    {
        for (var current = exception; current is not null; current = current.InnerException)
        {
            if (current is OracleException oracle && UnavailableErrorNumbers.Contains(oracle.Number))
            {
                return oracle;
            }
        }

        return null;
    }
}
```

`TryHandleAsync` 回 `false` 表示「這不是我的事」，框架會把例外交給下一個處理器，全部都不處理時才落到預設的 500。所以 `Program.cs` 只要再註冊一行，加在 `DomainExceptionHandler` 後面：

```csharp
builder.Services.AddExceptionHandler<DomainExceptionHandler>();
builder.Services.AddExceptionHandler<DatabaseUnavailableExceptionHandler>();
```

處理器依註冊順序被呼叫，第一個回傳 `true` 的就是贏家。`FindUnavailableError` 沿著 `InnerException` 往內找，因為 EF Core 會把 `OracleException` 包在自己的例外裡，直接檢查最外層會漏掉。清單中的 50201 是 ODP.NET 對「連不上伺服器」的統一包裝；其餘是 Oracle 文件中代表「資料庫暫時不可用」的錯誤（找不到 listener、逾時、資料庫正在啟動或關閉等）。

### 4.3 實測

資料庫關閉時打需要資料庫的端點：

```powershell
curl.exe -s -i http://localhost:5080/api/v1/tasks -H "Authorization: Bearer $editorToken"
```

```text
HTTP/1.1 503 Service Unavailable
Content-Type: application/problem+json
Cache-Control: no-cache,no-store
Retry-After: 5
...

{"type":"https://tools.ietf.org/html/rfc9110#section-15.6.4","title":"Service Unavailable","status":503,"detail":"The database is temporarily unavailable. Retry later.","traceId":"00-2580880171d720bae73eff3d80a1fc58-d3a429e39110fc67-00"}
```

登入端點也一樣是 503，但不需要資料庫的端點不受影響，同一段時間打 `GET /api/v1/auth/me`（只讀 token 裡的 claim）仍然回 200。這是 503 比整個服務掛掉更好的地方：API 的某些功能依然可用。伺服器 log 這段期間的記錄：

```text
07:30:22 warn: TaskTracker.Api.Exceptions.DatabaseUnavailableExceptionHandler[0] Database unavailable (ORA-50201), responding 503 with Retry-After 5s
07:30:22 fail: TaskTracker.Api.Middleware.RequestLoggingMiddleware[0] HTTP GET /api/v1/tasks responded 503 in 4168.3 ms (user 1f94e144-f6eb-449e-bc48-20f0d7bc0fd4, trace 00-2580880171d720bae73eff3d80a1fc58-d3a429e39110fc67-00)
```

處理器自己記一筆 `warn`（說明原因），request log 仍然是 `fail`（5xx 一律 Error），兩者透過同一個 trace id 可以對起來。注意 503 並沒有讓告警消失：5xx 的 Error log 還在，只是維運現在能從 `Retry-After` 與 warn 那一行看出這是資料庫的暫時問題。

### 4.4 這個決定的代價

三件事要誠實交代。第一，延遲沒有變好：上面的 503 花了 4168 毫秒，因為請求要等連線逾時才知道連不上，503 只是讓失敗的訊息更準確，不會讓失敗更快。要快速失敗需要另外設定連線逾時與熔斷（circuit breaker），那是 [[18-resilience-and-performance]] 的主題。第二，`Retry-After: 5` 是固定值，只是一個合理的建議，不代表資料庫五秒後一定恢復。第三，也是最需要小心的，清單裡的 3113 與 3114 代表「連線在途中斷了」。對 `GET` 來說重試沒有風險（[[basics-01-http-and-web-api]] 講過 safe 與 idempotent）；對 `POST` 新增任務來說，連線可能是在伺服器已經把資料寫入、回應還沒送到時斷的，客戶端依 503 重試就會新增第二筆。TaskTracker 目前沒有冪等鍵，這個風險存在；設計冪等機制是 [[expert-01-advanced-api-design]] 的題目，在那之前，要不要把 3113、3114 留在清單裡是一個真實的取捨。

測試也跟著補上。`DatabaseDownTests` 把連線字串指向一個沒有人在聽的位址（`127.0.0.1:1`），驗證三件事：live 仍是 200、ready 是 503、需要資料庫的端點回 503 加 `Retry-After: 5` 與 `application/problem+json`。這組測試不需要 Docker，在任何機器與 CI 上都會跑，不像連真實 Oracle 容器的整合測試會被跳過。

---

## 五、Dockerfile：把 API 包成一個可以直接跑的映像

### 5.1 完整內容

專案根目錄新增 `Dockerfile`：

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY src/TaskTracker.Api/TaskTracker.Api.csproj src/TaskTracker.Api/
RUN dotnet restore src/TaskTracker.Api/TaskTracker.Api.csproj
COPY src/TaskTracker.Api/ src/TaskTracker.Api/
RUN dotnet publish src/TaskTracker.Api/TaskTracker.Api.csproj -c Release --no-restore -p:UseAppHost=false -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
ENV ASPNETCORE_HTTP_PORTS=8080
EXPOSE 8080
USER $APP_UID
ENTRYPOINT ["dotnet", "TaskTracker.Api.dll"]
```

與 `.dockerignore`：

```text
**/bin/
**/obj/
.git/
.vs/
.idea/
.vscode/
TestResults/
tests/
```

很多教學（包含 .NET 8 以前的寫法）裡常見的 Dockerfile 是 `COPY . .` 再一次 `dotnet publish`，沒有 `USER`，也沒有設定 port。那些寫法在今天會踩到好幾個坑，下面一層一層看 TaskTracker 的版本為什麼這樣寫。

### 5.2 為什麼有兩個 `FROM`

第一個 `FROM` 用的是 `sdk` 映像，內含編譯器與 NuGet 工具，只在建置時需要；第二個 `FROM` 用的是 `aspnet` 映像，只有執行 ASP.NET Core 所需的 runtime。最後交付的映像是第二個，第一個階段（`build`）只負責產出 `/app/publish` 這個資料夾，`COPY --from=build` 把產物搬過來，SDK 與原始碼完全不會留在最終映像裡。這就是多階段建置（multi-stage build）。為什麼要這樣？因為執行階段不需要編譯器，帶著它只會讓映像變大，也讓攻擊者進入容器後多了可以利用的工具。實測的最終映像是 247 MB，容器裡只有 runtime，沒有 SDK：

```powershell
docker run --rm --entrypoint dotnet tasktracker-api:basics-16 --list-runtimes
```

```text
Microsoft.AspNetCore.App 10.0.14 [/usr/share/dotnet/shared/Microsoft.AspNetCore.App]
Microsoft.NETCore.App 10.0.14 [/usr/share/dotnet/shared/Microsoft.NETCore.App]
```

### 5.3 為什麼先 `restore` 再複製原始碼

Docker 建置映像時，每一條指令產生一層（layer），並且把結果快取起來。下一次建置，只要某一層的指令與輸入沒變，就直接用快取；一旦某一層失效，它之後的所有層都必須重跑。這個規則決定了指令的順序：變動頻率低的放前面，變動頻率高的放後面。

TaskTracker 的版本先只複製 `.csproj`，執行 `dotnet restore`（下載所有 NuGet 套件，慢），再複製其餘原始碼、執行 `publish`。改一行 C# 程式碼時，`.csproj` 沒變，前面的 restore 層直接用快取，只有複製原始碼與 publish 這兩層重跑。反過來，如果一開始就 `COPY . .`，任何檔案變動都會讓 restore 失效，每次都要重新下載套件。實際跑 `--no-cache` 建置時，restore 這一步花了 3.48 分鐘（`Restored ... (in 3.48 min)`，視網路而定），而 publish 只要約 11 秒。這個差距就是快取順序省下來的時間：

```text
#10 [build 3/6] COPY src/TaskTracker.Api/TaskTracker.Api.csproj src/TaskTracker.Api/
#11 [build 4/6] RUN dotnet restore src/TaskTracker.Api/TaskTracker.Api.csproj
#12 [build 5/6] COPY src/TaskTracker.Api/ src/TaskTracker.Api/
#13 [build 6/6] RUN dotnet publish src/TaskTracker.Api/TaskTracker.Api.csproj -c Release --no-restore -p:UseAppHost=false -o /app/publish
#14 [final 3/3] COPY --from=build /app/publish .
```

另外兩個細節。指令明確指定 `.csproj` 路徑，因為映像裡只複製了 API 這一個專案，工作目錄 `/src` 底下沒有 solution 檔，直接 `dotnet publish` 會因為找不到專案而失敗。`-p:UseAppHost=false` 不產生 Windows/Linux 的原生執行檔，因為容器入口是 `dotnet TaskTracker.Api.dll`，那個檔案用不到。`.dockerignore` 則排除 `bin/`、`obj/`、`.git/` 與測試專案：這些東西不排除，會被送進建置內容（build context），拖慢每一次建置，也可能讓本機編譯產生的 `obj/` 干擾容器內的 restore。

### 5.4 非 root 與 port 8080

這兩個設定在 .NET 8 以後是連在一起的。.NET 8 之前，官方映像預設以 root 執行、監聽 80；從 .NET 8 起，映像內建了一個叫 `app` 的使用者（uid 由環境變數 `APP_UID` 提供，值為 1654），預設 port 改成 8080，因為 1024 以下的 port 要特權才能綁，非 root 的程序辦不到。要注意的是，映像只是準備好這個使用者，並沒有自動切換過去，一般的 `aspnet:10.0` 映像仍然以 root 啟動，必須在 Dockerfile 自己寫 `USER $APP_UID`。

`ASPNETCORE_HTTP_PORTS=8080` 本來就是映像的預設值，Dockerfile 再寫一次是為了讓讀的人不用去查映像文件，一眼看出程式監聽哪個 port；`EXPOSE 8080` 也只是文件性質的標記，不會真的對外開放 port，真正對外是 `docker run -p` 或 Kubernetes 的 `containerPort` 決定。

啟動容器之後驗證，不要只相信 Dockerfile 的寫法。`docker exec` 看使用者、再試著寫系統目錄：

```powershell
docker exec tasktracker-api id
docker exec tasktracker-api touch /etc/should-fail
docker exec tasktracker-api touch /app/should-fail
```

```text
uid=1654(app) gid=1654(app) groups=1654(app)
touch: cannot touch '/etc/should-fail': Permission denied
touch: cannot touch '/app/should-fail': Permission denied
```

程序以 uid 1654 執行，寫不進系統目錄，也寫不進自己的程式目錄。為什麼這很重要？一旦應用程式被攻破（例如上傳漏洞被當成寫檔的入口），攻擊者只繼承非 root 的權限，無法修改容器內的系統檔，也很難逃出容器；許多叢集啟用了 Pod Security Standards 的 restricted 等級，這個等級要求容器不得以 root 執行，違反的 Pod 會被拒絕建立。

### 5.5 建置、執行與讀它的第一份 log

```powershell
docker build -t tasktracker-api:basics-16 .
```

執行前要先處理設定。容器裡沒有 User Secrets（那是開發環境才載入的來源），機密要在啟動時由外部注入。`docker run -e 名稱` 只寫名稱、不寫值，Docker 會從目前的 PowerShell 環境變數取值，所以機密不會出現在指令列、也不會進入 shell 歷史。需要的三個環境變數：

```powershell
$env:ConnectionStrings__Default = "User Id=tasktracker;Password=$env:APP_USER_PASSWORD;Data Source=host.docker.internal:1521/FREEPDB1"
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$env:Jwt__SigningKey = [Convert]::ToBase64String($bytes)
docker run -d --name tasktracker-api -p 5080:8080 -e Jwt__SigningKey -e ConnectionStrings__Default -e Cors__AllowedOrigins__0=https://tasktracker.example.com tasktracker-api:basics-16
```

`host.docker.internal` 是 Docker Desktop 提供的、從容器連回開發機的名稱（Linux 要加 `--add-host=host.docker.internal:host-gateway`）；API 在容器裡，Oracle 在開發機的另一個容器，兩者不在同一個網路位址。`APP_USER_PASSWORD` 是 [[basics-10-efcore-and-oracle]] 建 Oracle 容器時用的同一個值。`-p 5080:8080` 把本機 5080 對應到容器的 8080，之後 `curl.exe` 打 5080 的方式不變；如果先前用 `dotnet run` 佔著 5080，要先停掉。第一次部署用的資料庫在開發環境啟動時已經遷移完成並有種子帳號，容器是 Production 環境，`Database:MigrateOnStartup` 沒有開，所以容器不會碰 schema。

啟動之後，探針兩個都是 200（容器經由 `host.docker.internal` 連到 Oracle，ready 才會是 Healthy），再看 `docker logs`。正式環境輸出 JSON，這裡用 `ConvertFrom-Json` 取出三個欄位：

```powershell
docker logs tasktracker-api | ForEach-Object { $entry = $_ | ConvertFrom-Json; "$($entry.LogLevel) $($entry.Category): $($entry.Message)" }
```

```text
Warning Microsoft.AspNetCore.DataProtection.Repositories.FileSystemXmlRepository: Storing keys in a directory '/home/app/.aspnet/DataProtection-Keys' that may not be persisted outside of the container. Protected data will be unavailable when container is destroyed. For more information go to https://aka.ms/aspnet/dataprotectionwarning
Warning Microsoft.AspNetCore.DataProtection.KeyManagement.XmlKeyManager: No XML encryptor configured. Key {c6e647ca-e160-4918-a58d-4bc750a55337} may be persisted to storage in unencrypted form.
Information Microsoft.Hosting.Lifetime: Now listening on: http://[::]:8080
Information Microsoft.Hosting.Lifetime: Application started. Press Ctrl+C to shut down.
Information Microsoft.Hosting.Lifetime: Hosting environment: Production
Information Microsoft.Hosting.Lifetime: Content root path: /app
Warning Microsoft.AspNetCore.HttpsPolicy.HttpsRedirectionMiddleware: Failed to determine the https port for redirect.
```

中間四行是預期內的：監聽 `http://[::]:8080`、環境是 Production、內容根目錄在 `/app`。三則警告各說明一件上線時會遇到的事。前兩則來自 Data Protection：ASP.NET Core 有一個內建的金鑰系統，用來保護 cookie、antiforgery token 這類東西，金鑰預設存在容器內的 `/home/app/.aspnet/DataProtection-Keys`，容器一銷毀金鑰就消失，多個副本之間也不共用。TaskTracker 是純 JWT 的 API，沒有依賴這套機制，所以這兩則目前無害；但如果以後加了 cookie 或 antiforgery，就必須把金鑰放到共用儲存（[[expert-04-security-hardening]]）。第三則來自 `UseHttpsRedirection`：容器裡只聽 HTTP 8080，找不到 HTTPS port 可以重導，於是警告並放行。TLS 在容器外面（見第七節）終結時，這個 middleware 在源站沒有作用，保留它只是多一則警告，上線清單會把它列為要處理的項目。

驗完把容器清掉：

```powershell
docker rm -f tasktracker-api
```

---

## 六、設定與機密：環境變數注入，不烤進映像

剛才的 `docker run` 其實已經示範了正確的做法，這裡把理由說清楚。映像是一個可以被複製、推到 registry、被很多人拉下來的東西；機密一旦寫進映像，所有能拿到映像的人都拿到了機密，而且 `docker history` 與 `docker inspect` 都能直接讀出 `ENV` 的值。就算之後把檔案刪掉，舊的層還在。壞做法有三種：Dockerfile 裡寫 `ENV Jwt__SigningKey=...`、用 `COPY` 把含機密的 `appsettings.Production.json` 複製進映像、在 `RUN` 指令裡用 `--build-arg` 傳入再留在層裡。好做法是映像裡完全沒有機密，同一個映像在測試與正式環境都能跑，差別只在啟動時注入的環境變數。

這件事能成立，靠的是 [[basics-09-configuration-and-environments]] 講過的疊層：環境變數的優先權高於 `appsettings.json`，`__`（雙底線）對應設定階層的冒號，所以 `Jwt__SigningKey` 就是 `Jwt:SigningKey`，TaskTracker 的程式碼完全不用改。`appsettings.json` 刻意沒有連線字串與簽章金鑰，缺少它們時 `ValidateOnStart` 會讓程式在啟動階段就失敗，而不是等到第一個請求才爆炸。在 Kubernetes 上，這些值由 Secret 物件以 `secretKeyRef` 注入成環境變數，非機密設定（CORS 白名單、分頁大小）放 ConfigMap，同樣最後都變成環境變數。細節見 [[17-configuration-and-secrets]] 與 [[practice-2-deploy-real-app]]。

---

## 七、Kestrel 與反向代理：誰負責什麼

上面的容器裡只有 Kestrel 在聽 HTTP 8080，沒有 HTTPS 憑證。正式環境的使用者卻是用 `https://` 連來的。中間差的那一段，是反向代理（reverse proxy）的工作。Kestrel 是 ASP.NET Core 內建的 HTTP server，能直接面對網際網路，但實務上常在前面放一層代理，是職責分工的結果：TLS 憑證的管理與輪替、多個服務共用 443 並依網域分流、靜態內容的快取與壓縮、擋住惡意的慢速連線與限流，這些由代理或 CDN 處理比較合適，Kestrel 專心執行 API 的程式碼。在 Kubernetes 裡，這個角色是 Ingress；在作者的環境裡是 Cloudflare Tunnel；在傳統機房可能是 Nginx 或 IIS。Kestrel 內部的運作見 [[00-hosting-and-startup]]。

這個分工順帶解釋三件事：為什麼源站常常只有 HTTP/1.1、CDN 與源站的連線為什麼互不相干、代理後面的程式看到的請求長什麼樣。

### 7.1 為什麼源站常常只有 HTTP/1.1

[[basics-01-http-and-web-api]] 提到瀏覽器常見的是 HTTP/2 或 HTTP/3。HTTP/2 和 HTTP/3 在瀏覽器場景裡都是經由 TLS 協商出來的（連線建立時雙方交換支援的協定清單，稱為 ALPN）。純 http 端點沒有 TLS，也就沒有協商的機會，Kestrel 對它的預設就是只講 HTTP/1.1。可以直接實測：一個預設設定的 Kestrel 聽在 http://127.0.0.1，用 .NET 的 `HttpClient` 分別以「最高 2.0、可降級」與「強制 2.0」兩種版本策略發請求：

```csharp
var request = new HttpRequestMessage(HttpMethod.Get, "http://127.0.0.1:5791/")
{
    Version = HttpVersion.Version20,
    VersionPolicy = HttpVersionPolicy.RequestVersionExact // 另一次用 RequestVersionOrLower
};
```

```text
default RequestVersionOrLower: 200 HTTP/1.1 body=server saw HTTP/1.1
default RequestVersionExact: HttpRequestException: The HTTP/2 server closed the connection. HTTP/2 error code 'HTTP_1_1_REQUIRED' (0xd). (HttpProtocolError)
```

可降級的請求被悄悄降到 1.1 並成功；強制 HTTP/2 的請求得到 `HTTP_1_1_REQUIRED`，意思是伺服器明確告訴你「這個連線只能用 1.1」。如果日後在 log 或例外訊息看到這個錯誤碼，意思就是：客戶端要求 HTTP/2，但那個端點不提供。

那如果真的想在明文 http 上提供 HTTP/2（稱為 h2c），可以讓端點只講 HTTP/2：

```csharp
builder.WebHost.ConfigureKestrel(k => k.ConfigureEndpointDefaults(o => o.Protocols = HttpProtocols.Http2));
```

此時強制 HTTP/2 的客戶端成功了，可是普通的 HTTP/1.1 客戶端反而被擋：

```text
h2only RequestVersionOrLower: 400 HTTP/1.1 body=An HTTP/1.x request was sent to an HTTP/2 only endpoint.
h2only RequestVersionExact: 200 HTTP/2.0 body=server saw HTTP/2
```

這有實際後果。Kubernetes 的 HTTP 探針、對 `http://` 網址預設不嘗試 HTTP/2 的 `curl.exe`、大部分的負載平衡健康檢查，發出的都是 HTTP/1.1，端點只開 HTTP/2 時，它們全部收到 400。所以除非有 gRPC 這類必須使用 HTTP/2 的需求，否則 API 的明文端點留在預設值最安全。

想一次開三種版本，設定是 `HttpProtocols.Http1AndHttp2AndHttp3`。但 HTTP/3 建立在 QUIC 上，一定要 TLS，把它設在明文端點時，Kestrel 會警告並降回 1.1：

```text
warn: Microsoft.AspNetCore.Server.Kestrel[65]
      HTTP/3 is not enabled for 127.0.0.1:5791. HTTP/3 requires TLS. Connections to this endpoint will use HTTP/1.1.
```

也就是說，這個設定只在 Kestrel 自己終結 TLS 的場景才有意義。

### 7.2 CDN 與源站是兩段連線

結論是：瀏覽器與使用者看到的協定版本，只取決於瀏覽器到最外層（CDN 或 Ingress）那一段。CDN 到源站是另一段獨立的連線，版本各自協商。Cloudflare 在邊緣對瀏覽器開 h3，不代表 TaskTracker 的容器要開 h3；容器維持 http/1.1 並不影響使用者體驗，反而讓設定最簡單。這也是為什麼容器裡不需要憑證：TLS 在邊緣就終結了。

### 7.3 代理後面，Kestrel 看到的是什麼

TLS 在代理終結之後，Kestrel 收到的是明文 http，來源 IP 是代理的 IP。對程式來說，`Request.Scheme` 變成 `http`，`Connection.RemoteIpAddress` 是代理的位址，而不是真正的使用者。代理會把原始資訊放在 `X-Forwarded-Proto` 與 `X-Forwarded-For` 標頭，但 ASP.NET Core 預設不採信這些標頭。實測：同一個請求帶上這兩個標頭，沒設定與設定了 `ASPNETCORE_FORWARDEDHEADERS_ENABLED=true` 的對比：

```text
scheme=http remote=127.0.0.1
scheme=https remote=203.0.113.7
```

第一行是預設行為：標頭被忽略。第二行打開環境變數後，Forwarded Headers middleware 生效，scheme 與來源 IP 都被還原。這個環境變數是為容器環境準備的捷徑；它同時讓 middleware 信任所有來源的轉發標頭，所以只適用於 Pod 只能從 Ingress 到達的情況，如果 Pod 的 port 可以被任意客戶端直連，攻擊者可以偽造 `X-Forwarded-For`。需要更精細的信任範圍時，要在程式裡設定 `ForwardedHeadersOptions` 的已知代理，細節見 [[21-deployment]]。

為什麼 TaskTracker 值得在意？依 IP 限流、記錄真正的來源 IP、產生絕對網址（例如 `201 Created` 的 `Location`）、`UseHttpsRedirection` 判斷要不要重導，全部依賴 `Request.Scheme` 和 `RemoteIpAddress`。沒還原的話，限流會把所有使用者當成同一個人，log 裡的 IP 全是代理的位址。

---

## 八、上線前檢查清單

前面的內容可以收斂成一份上線前的檢查清單。結構沿用「安全、穩定性、效能」三類，再補上部署一類；每一項都是前面章節出現過的，括號指向出處。清單的用意是上線前能逐項核對，而不是取代理解。

**安全**
- [ ] JWT 簽章金鑰與資料庫連線字串來自環境變數或 Secret，不在 `appsettings*.json`，不在映像裡（本章第六節）
- [ ] 簽章金鑰至少 32 bytes（[[basics-12-jwt-login]]）
- [ ] OpenAPI 與 Scalar 文件只在 Development 開放；若 staging 需要，要放在授權後面（[[basics-14-openapi-and-versioning]]）
- [ ] CORS 白名單列出明確的來源，沒有萬用字元（[[basics-09-configuration-and-environments]]）
- [ ] 容器以非 root 執行，並用 `docker exec ... id` 驗證過（本章第五節）
- [ ] TLS 在哪一層終結是明確的；TLS 在代理終結時，源站的 `UseHttpsRedirection` 要處理掉，並設定 Forwarded Headers（本章第七節）
- [ ] 健康檢查端點是匿名的，且回應不含內部細節（本章第三節）

**穩定性**
- [ ] 全域例外處理已啟用，錯誤回應是 ProblemDetails，不含堆疊追蹤（[[basics-08-middleware-and-exception-handling]]）
- [ ] log 輸出 JSON 到 stdout，5xx 記 Error，沒有記密碼與 token（本章第二節）
- [ ] liveness 不碰任何外部相依，readiness 才檢查資料庫（本章第三節）
- [ ] 資料庫暫時不可用時回 503 加 `Retry-After`，其他未預期的例外維持 500（本章第四節）
- [ ] 設定都有 `ValidateOnStart`，缺漏在啟動階段就失敗（[[basics-09-configuration-and-environments]]）
- [ ] 正式環境不開 `MigrateOnStartup`，schema 變更由獨立的步驟執行（[[basics-10-efcore-and-oracle]]）
- [ ] 收到終止訊號時能優雅關閉，進行中的請求不被切斷（[[00-hosting-and-startup]]）

**效能**
- [ ] I/O 一律 async 並傳遞 `CancellationToken`，沒有 `.Result` 或 `.Wait()`（[[basics-10-efcore-and-oracle]]）
- [ ] `DbContext` 是 scoped，沒有被 singleton 持有（[[basics-07-dependency-injection-and-services]]）
- [ ] 連線池大小乘以副本數，在資料庫能承受的連線數之內（[[57-database-connections]]）
- [ ] 容器有設定記憶體與 CPU 的 requests 和 limits（[[21-deployment]]）

**部署**
- [ ] 映像 tag 是明確的版本，不是 `latest`
- [ ] 探針指向 `/healthz/live` 與 `/healthz/ready`，埠號與映像的 8080 一致
- [ ] 本機用 `docker run` 跑過完整流程，包含「關掉資料庫、再打開」
- [ ] CI 的測試回合 skipped 數為 0。[[basics-15-testing]] 的整合測試在沒有 Docker 的環境會被整批跳過卻仍是綠燈，pipeline 要把「跳過數大於 0」當成失敗條件；GitHub Actions 的 workflow 寫法屬於 pipeline 設定，本書入門篇沒有展開

「關掉資料庫、再打開」那一項值得再強調：除了 CI 那一項，這張清單裡的每一項，本章都在 TaskTracker 上實際操作過。從檢查表上打勾和親眼看過的差別很大，開頭那個三個 Pod 一起重啟的夜晚，如果事先在測試環境把資料庫關掉過一次，在第一次演練就會看到。

---

## 九、Kubernetes 只點到這裡

本章刻意沒有寫任何 Kubernetes YAML。入門篇該帶走的是 API 這一側的準備：映像要能在不改的前提下換環境、有 live 與 ready 兩個端點可以給探針用、log 能被平台收走、資料庫掛掉時有明確的 503。這些準備好之後，Deployment 的 replicas、探針參數、資源限制、Ingress、Secret 的寫法，是叢集那一側的事：[[21-deployment]] 從 ASP.NET Core 的角度寫了完整的 Deployment 骨架，[[practice-2-deploy-real-app]] 則是在叢集上實際部署一個應用程式的練習。

---

## 十、你已經走完什麼，接下來怎麼讀

回頭看這十六章，起點是一個「聽過 HTTP，沒寫過 Web API」的人。第一到二章建立了 HTTP 的模型與 REST 的設計規則，並產出 TaskTracker 的 API 規格。第三到八章把規格變成實際的端點：專案結構與 Program.cs、Controller 與路由、model binding 與驗證、DTO、依賴注入、middleware 與例外處理。第九到十章加上設定與環境，並把資料真正存進 Oracle。第十一到十三章處理誰能呼叫：驗證與授權的 pipeline、JWT 登入、權限與前端的對齊。第十四到十六章讓它可以被交付：OpenAPI 與版本、測試、以及本章的上線。

這時你手上有一個可以在容器裡跑、有測試、有文件、有權限、能被監控的 API，並且知道每個部分為什麼長這樣。入門篇到這裡結束，但「知道怎麼做」和「知道它內部怎麼運作」之間還有一段距離，這就是深度篇要補的。

深度篇不需要從頭讀到尾。建議的順序：先讀 [[00-hosting-and-startup]] 與 [[01-request-pipeline]]，它們解釋 `Program.cs` 與 pipeline 的運作機制，後面所有章節都以此為底；接著依你最近碰到的問題挑：想知道為什麼登入偶爾失敗，讀 [[11-authentication]] 與 [[12-jwt-deep-dive]]；資料庫相關的效能與一致性，讀 [[07-efcore-internals]] 到 [[10-oracle-specifics]]；準備上線與維運，讀 [[16-logging-and-observability]]、[[18-resilience-and-performance]] 與 [[21-deployment]]。每一章的結尾都有「同事會來問你的問題」，可以當成自我測驗。入門篇的最後一章 [[basics-17-attribute-reference]] 是附錄，列出所有 attribute 的用途與常見誤解，查閱用，不需要順序讀。

---

## 常見誤解

**「Health check 回 200 就代表服務正常。」** 這取決於它檢查了什麼。TaskTracker 的 `/healthz/live` 一定是 200，因為它什麼都不檢查，只回答程序還活著；資料庫掛了它仍是 200。判斷「能不能接流量」要看 `/healthz/ready`。把兩者混用，要嘛在資料庫抖動時全部 Pod 一起重啟，要嘛程序卡死卻永遠不被重啟。

**「`logger.LogInformation($"...")` 和 `LogInformation("... {X}", x)` 只是寫法不同。」** Message 看起來一樣，`State` 不一樣：內插字串在呼叫前就被組成成品，結構化欄位全部消失，log 平台無法依欄位查詢，也無法依模板分組。規則是第一個參數永遠是常數模板。

**「Dockerfile 的 `EXPOSE 8080` 讓容器可以從外面連。」** `EXPOSE` 只是文件性質的標記。要能從外面連，必須用 `docker run -p`，或在 Kubernetes 以 Service 與 `containerPort` 開放。真正決定程式監聽哪個 port 的是 `ASPNETCORE_HTTP_PORTS`。

**「用官方 aspnet 映像就已經是非 root 了。」** 映像準備好了 `app` 使用者，但預設仍以 root 啟動。要寫 `USER $APP_UID`，並且用 `docker exec ... id` 驗證，而不是相信自己寫的 Dockerfile。（chiseled 映像另當別論，它預設就是非 root。）

**「HTTP/2 比較快，所以源站應該強制 HTTP/2。」** 瀏覽器到 CDN 與 CDN 到源站是兩段連線。明文端點只開 HTTP/2 時，HTTP/1.1 的探針與工具會收到 400；HTTP/3 設在明文端點則直接降回 1.1。除非有 gRPC 這類必須用 HTTP/2 的場景，源站保持預設。

---

## 同事會來問你的問題

**Q：為什麼資料庫連不上要回 503，不是 500？**
503 告訴呼叫端與維運這是暫時的、相依服務的問題，重試有意義；500 代表我沒預期到，可能是 bug。TaskTracker 只對已確認是「資料庫暫時不可用」的 Oracle 錯誤回 503，其他沒預期到的例外維持 500。要留意 3113 與 3114 這類「連線中斷」的錯誤，對寫入請求而言，客戶端重試可能造成重複新增，這個取捨在冪等機制出現之前是真實存在的。

**Q：readiness 失敗，Pod 的流量會被切掉，那所有 Pod 都失敗怎麼辦？**
所有副本同時 not ready 時，Service 沒有可用的後端，客戶端會收到 Ingress 或代理回的錯誤（通常是 502 或 503）。這是資料庫真的掛了時該有的結果，比起收到各種不確定的 500 好得多。避免它的方法是排查資料庫本身，而不是放寬 readiness。

**Q：為什麼 `/healthz/live` 不能順便檢查一下資料庫？**
因為 liveness 失敗的後果是重啟，重啟 API 並不能讓資料庫恢復。所有副本會在資料庫抖動時同時被重啟，重啟時又去連資料庫，造成連鎖反應。想知道依賴是否可用，交給 readiness。

**Q：log 要用 Serilog 嗎？**
不一定。本章用內建的 JSON console formatter 就足以輸出結構化 log，並由容器平台收走 stdout。需要把 log 直接寫入特定 sink、做更細的 enrich 或過濾時才考慮 Serilog，取捨見 [[16-logging-and-observability]]。

**Q：能不能把 `appsettings.Production.json` 連同機密一起放進映像，這樣最簡單？**
不要。映像會被複製與推送，機密一旦寫進就很難收回，而且可以用 `docker history` 找到。映像不放機密，啟動時用環境變數或 Secret 注入。這樣同一個映像可以不改地通過測試、staging 與正式環境。

---

## 這章的位置

學完這一章，你能把 TaskTracker 變成可以上線的樣子：用 message template 寫出機器可查詢的 log，用 live 與 ready 兩個端點把「活著」和「能接流量」分開，讓資料庫暫時連不上時回 503 加 `Retry-After`，寫出多階段、非 root、依快取順序排列的 Dockerfile，並透過環境變數注入機密。你也能說明 Kestrel 與反向代理的分工，以及為什麼源站常常只有 HTTP/1.1。想看 Host 內部怎麼啟動與關閉，去 [[00-hosting-and-startup]]；想深入 log、metrics 與探針設計，去 [[16-logging-and-observability]]；想看完整的 Deployment 骨架、migration 的執行位置與滾動更新，去 [[21-deployment]]。下一章 [[basics-17-attribute-reference]] 是附錄，把前面各章出現的 attribute 整理成可以查閱的表。

---

## 連結

- 上一章：[[basics-15-testing]]
- 下一章：[[basics-17-attribute-reference]]
- 對應深度章：[[16-logging-and-observability]]、[[21-deployment]]、[[00-hosting-and-startup]]
- 相關：[[57-database-connections]]、[[practice-2-deploy-real-app]]、[[17-configuration-and-secrets]]
- 總目錄：[[dotnet-web-api]]
