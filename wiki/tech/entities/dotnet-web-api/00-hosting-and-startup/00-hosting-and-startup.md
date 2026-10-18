---
type: concept
domain: tech
tags: [dotnet, aspnet, hosting, kestrel, generic-host, startup, graceful-shutdown]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 00 章：Host 與啟動 — `CreateBuilder` 到 `Run()` 之間發生了什麼

## 一個沒人細看的檔案

每個 ASP.NET Core 專案都從同一個檔案開始，而且長得幾乎一樣：

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();

var app = builder.Build();

app.UseAuthorization();
app.MapControllers();

app.Run();
```

六行。範本產生的，大多數人從來沒有真正讀過它，只是在中間不斷往裡塞 `AddXxx` 和 `UseXxx`。直到某天出現這些狀況：

- 服務在本機跑得好好的，部署到 K8s 之後啟動到一半就掛，log 只有一行 `Unable to start Kestrel`
- 加了一個 `BackgroundService`，結果它在 API 還沒準備好接請求之前就開始打資料庫
- Pod 滾動更新時前端偶爾收到 502，明明 Deployment 設定看起來沒問題
- 在 `Program.cs` 裡想拿一個 Scoped 服務來做資料初始化，直接注入卻炸出 `Cannot resolve scoped service from root provider`

這四個問題的答案，全都藏在那六行程式碼展開後的細節裡。這一章要做的事，就是把這六行完整拆開。

讀完之後，你應該能夠說清楚：`CreateBuilder` 建了哪些東西、`Build()` 這一刻凍結了什麼、`Run()` 之後執行緒卡在哪裡不動、以及當 K8s 送出 SIGTERM 的時候，這個程序是怎麼一步步收工的。

---

## 一、先講清楚「Host」是什麼

在 .NET 的世界裡，**Host（主機）是一個把應用程式的生命週期、設定、DI 容器、logging 包在一起管理的容器物件**。這個詞很容易和「主機」（機器）搞混，但它指的是程式內部的一個物件。

為什麼需要這種東西？回想 .NET Framework 時代的 ASP.NET：應用程式沒有自己的 `Main`，它是一個被 IIS 載入的 DLL。啟動流程、設定讀取、生命週期全由 IIS 掌握，開發者只能在 `Global.asax` 的幾個 hook 點插手。這帶來兩個後果：一是程式無法脫離 IIS 執行（本機開發要裝 IIS Express，跨平台想都別想），二是 Web 應用和 Console 應用、Windows Service 的啟動模型完全不同，同一套設定與 DI 寫法沒辦法共用。

.NET Core 把這件事反轉過來：**應用程式重新擁有自己的 `Main`，是它去啟動 Web Server，而不是 Web Server 來載入它**。這個轉向被稱為「自我主機（self-hosted）」。而 Host 就是那個負責統籌啟動的物件。

Host 的職責可以濃縮成四件事：

| 職責 | 具體內容 |
| --- | --- |
| 設定（Configuration） | 把 appsettings.json、環境變數、命令列參數合併成一份 `IConfiguration` |
| 依賴注入（DI） | 收集所有服務註冊，建出 `IServiceProvider` |
| Logging | 建立 logging pipeline，讓 `ILogger<T>` 可以被注入 |
| 生命週期（Lifetime） | 啟動與停止所有 `IHostedService`，處理關機訊號 |

注意這四件事**沒有一件是 Web 專屬的**。這是刻意的設計：.NET 有一個通用的 `IHost`（Generic Host），Console 排程程式、Worker Service、gRPC 服務都用它；而 Web 應用只是在 Generic Host 上面多掛了一個東西——一個叫做 `IServer` 的服務，它會監聽 port、接收 HTTP 請求。

換句話說：

```text
IHost（設定 + DI + Logging + 生命週期）
  └── 掛上一個 IHostedService：GenericWebHostService
        └── 它啟動 IServer（預設是 Kestrel）
              └── Kestrel 收到請求時，呼叫 pipeline
```

一個 Web API 的本質是「一個 Generic Host，裡面跑著一個叫做『把 HTTP 請求丟進 pipeline』的背景服務」。這個認知在後面談 `BackgroundService` 啟動順序、談 graceful shutdown 的時候會不斷回來。

`WebApplication` 與 `WebApplicationBuilder` 是 .NET 6 引入的簡化門面（Minimal Hosting Model）。它們沒有取代 Generic Host，只是把原本要寫在 `Program.cs` + `Startup.cs` 兩個檔案、十幾行的樣板收攏成幾行。底下轉的還是同一套機器。

---

## 二、`CreateBuilder(args)`：組裝台被架起來

```csharp
var builder = WebApplication.CreateBuilder(args);
```

這一行結束之後，`builder` 身上有四個屬性可以動：

```csharp
builder.Configuration   // IConfigurationBuilder + 已載入的設定值
builder.Services        // IServiceCollection，服務註冊清單
builder.Logging         // ILoggingBuilder
builder.Environment     // IWebHostEnvironment
```

但這一行做的事遠不只是 new 四個空物件。它已經替你載入了設定、註冊了一大批預設服務、決定了執行環境。逐項來看。

### 2.1 環境（Environment）先被決定

`builder.Environment.EnvironmentName` 的值來自環境變數 `ASPNETCORE_ENVIRONMENT`（或 `DOTNET_ENVIRONMENT`）。沒設的話預設是 `Production`。

這是新手最常踩的第一個坑：**沒設環境變數的容器，跑的是 Production 模式**。於是 Swagger 不見了（因為範本把 `UseSwagger` 包在 `if (app.Environment.IsDevelopment())` 裡面）、錯誤頁面變成空白的 500、`appsettings.Development.json` 完全沒被讀進來。人在本機用 `dotnet run` 時 launchSettings.json 幫你設了 `Development`，一進容器就沒了。

```csharp
// 這三個方法只是字串比對的糖衣，字串是大小寫不敏感的
app.Environment.IsDevelopment();   // == "Development"
app.Environment.IsStaging();       // == "Staging"
app.Environment.IsProduction();    // == "Production"

// 環境名稱是自由字串，可以自訂
if (app.Environment.IsEnvironment("QA")) { }
```

在 K8s 上要記得明確注入：

```yaml
env:
  - name: ASPNETCORE_ENVIRONMENT
    value: "Production"
```

看起來多餘（反正預設就是 Production），但寫出來的價值在於**它讓下一個人知道這裡有這個開關**，而不是靠預設值的默契。

### 2.2 設定來源被載入並疊起來

`CreateBuilder` 會依序把這些來源疊上去，後面覆蓋前面同名的 key：

| 順序 | 來源 | 備註 |
| --- | --- | --- |
| 1 | `appsettings.json` | 基礎設定 |
| 2 | `appsettings.{Environment}.json` | 依上一節決定的環境名稱 |
| 3 | User Secrets | **僅在 Development 環境**，存在使用者家目錄，不進版控 |
| 4 | 環境變數 | 容器與 K8s 注入設定的主要管道 |
| 5 | 命令列參數 `args` | 最高優先權 |

「疊起來」這個詞要精確理解：**設定不是合併成一份，而是保留成一疊 provider，讀取時由上往下找第一個有值的**。這解釋了一個常見困惑——為什麼環境變數 `Jwt__Key` 可以覆蓋 `appsettings.json` 裡的 `Jwt:Key`，但 `appsettings.json` 裡的整個 `Jwt` 區塊不會因此消失，其他 key 仍然讀得到。覆蓋是逐 key 發生的，不是逐區塊。

環境變數的巢狀寫法用**雙底線** `__` 代替冒號，因為冒號在部分作業系統的環境變數名稱裡不合法：

```yaml
env:
  - name: ConnectionStrings__Default
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: connection-string
  - name: Jwt__ExpiresInMinutes
    value: "60"
```

注意 `args` 是被傳進 `CreateBuilder(args)` 的那個 `args`。如果你寫了 `WebApplication.CreateBuilder()` 而沒傳參數，命令列覆蓋就失效了——這個細節在需要用 `dotnet run --Jwt:Key=xxx` 臨時覆蓋設定時會顯現。

### 2.3 一批服務已經被註冊好

`CreateBuilder` 回來的時候，`builder.Services` 裡面**已經有上百個註冊了**。這些是框架運轉的基礎設施，包括：

- `IConfiguration`、`IConfigurationRoot`——所以你可以直接注入 `IConfiguration` 而不用註冊
- `ILoggerFactory`、`ILogger<>`——所以 `ILogger<UsersController>` 拿得到
- `IHostEnvironment`、`IWebHostEnvironment`
- `IHostApplicationLifetime`——關機協調用，後面會詳談
- `IOptions<>`、`IOptionsSnapshot<>`、`IOptionsMonitor<>` 的基礎設施
- Kestrel 相關的 server 服務

而 `IHttpContextAccessor` **不在**這批裡面，需要自己 `AddHttpContextAccessor()`。這是刻意的——它有效能成本（需要 `AsyncLocal` 來追蹤跨 await 的當前 context），框架不想預設打開。

### 2.4 Logging 預設接上三個 provider

Console、Debug、EventSource。在容器環境裡真正有用的是 Console——因為容器的慣例是「應用程式只管把 log 寫到 stdout，收集是外部的事」。Docker 的 log driver、K8s 的 kubelet 會接走 stdout，再由 Fluent Bit / Filebeat 送到 Elasticsearch。這個分工在 [[16-logging-and-observability]] 會展開。

---

## 三、中間這段：註冊服務

```csharp
builder.Services.AddControllers();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddDbContext<AppDbContext>(...);
```

這一段是**在寫一張清單，不是在建立物件**。`IServiceCollection` 本質上是 `List<ServiceDescriptor>`，每個 descriptor 記錄三件事：「什麼型別」「怎麼建」「活多久」。

這個「延後建立」的性質有幾個直接後果，值得現在就講清楚：

**後果一：註冊順序不影響解析。** 你可以先註冊 `OrderService`（它依賴 `IEmailService`）再註冊 `IEmailService`，完全沒問題，因為建立的動作發生在解析時，那時整張清單早就完整了。

**後果二：重複註冊同一個介面，最後一個贏——但只在用 `GetService<T>` 拿單一實例時。** 如果用 `GetServices<T>()`（複數），會拿到全部。這是 pipeline 型設計（例如多個驗證器）的基礎。

```csharp
builder.Services.AddScoped<IValidator, EmailValidator>();
builder.Services.AddScoped<IValidator, PhoneValidator>();

// 注入 IValidator          → 拿到 PhoneValidator（最後一個）
// 注入 IEnumerable<IValidator> → 拿到兩個
```

**後果三：`TryAdd` 系列存在是有理由的。** 框架和函式庫用 `TryAddScoped` 註冊預設實作，語意是「如果使用者沒有自己註冊，才用我的」。這讓你可以在呼叫 `AddXxx()` **之前**先註冊自己的實作來覆蓋框架預設值。順序在這裡就有意義了。

**後果四：這個清單在 `Build()` 之後就凍結。** 這是下一節的主題。

---

## 四、`builder.Build()`：凍結的那一刻

```csharp
var app = builder.Build();
```

這一行做了三件關鍵的事。

### 4.1 IServiceCollection 被封裝成 IServiceProvider

服務清單被拿去建出一個 `ServiceProvider`——真正能「解析」型別的容器。**從這一刻起，`builder.Services` 不能再改**。試著在 `Build()` 之後呼叫 `builder.Services.AddXxx()`，會得到 `InvalidOperationException: Cannot modify ServiceCollection after application is built`。

這個限制常讓人不解——為什麼不能動態註冊？答案是效能。容器在建立時會為每個型別預先編譯出「建構表達式」（甚至生成 IL），把「找建構子、找參數、遞迴解析」這些反射工作在啟動時做完一次，之後每個 request 走的是編好的快速路徑。允許後期修改就得放棄這層最佳化，並且引入執行緒安全的難題。

### 4.2 產生 root provider，以及 scope 的起點

`app.Services` 就是 **root provider**。它是所有 scope 的祖先，Singleton 實例存放在它身上，它的生命週期等於整個應用程式。

這解釋了本章開頭的第四個問題。假設你想在啟動時跑一次資料庫遷移或種子資料：

```csharp
// ❌ 這樣會炸：Cannot resolve scoped service from root provider
var db = app.Services.GetRequiredService<AppDbContext>();
db.Database.Migrate();
```

`AppDbContext` 是 Scoped（`AddDbContext` 預設如此），而 `app.Services` 是 root。框架擋下這個操作，因為如果允許，這個 DbContext 會活到程式結束——變成事實上的 Singleton，累積無限的 change tracker 記錄，而且被多執行緒共用（DbContext 不是執行緒安全的）。這叫 **captive dependency**（俘虜依賴），[[02-dependency-injection]] 會專章討論。

正確做法是自己開一個 scope，用完就關：

```csharp
// ✅ 明確建立 scope，using 確保用完釋放
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.MigrateAsync();
}
```

順帶一提，啟動時自動跑 `Migrate()` 在多副本部署下是有風險的——三個 Pod 同時啟動就會有三個程序同時嘗試改 schema。EF Core 的遷移有鎖，通常不會壞掉，但會拉長啟動時間並可能觸發 K8s 的 startup probe 逾時。生產環境的慣例是把遷移抽成獨立的 Job 或 initContainer，這在 [[21-deployment]] 展開。

### 4.3 驗證會不會在這裡發生？

預設情況下，Development 環境會開啟 **scope validation** 與 **build-time validation**：

- **Scope validation**：偵測 Singleton 依賴 Scoped 這種錯誤配對
- **Build-time validation**：嘗試預先解析所有註冊，找出缺失的依賴

關鍵在於**這兩個檢查在 Production 預設是關的**。後果是：一個「Singleton 服務注入了 Scoped 服務」的錯誤，在本機開發時 `Build()` 就會立刻爆炸讓你發現；上了生產環境卻可能一路沉默到第一個 request 進來才炸，或者更糟——完全不炸，只是靜靜地把一個 DbContext 俘虜成 Singleton，然後在流量上來後出現詭異的資料錯亂。

建議明確打開：

```csharp
builder.Host.UseDefaultServiceProvider(options =>
{
    options.ValidateScopes = true;
    options.ValidateOnBuild = true;
});
```

代價是啟動時間增加（要預先解析所有型別）。用「啟動慢半秒」換「設定錯誤在啟動時就顯性失敗，而不是在半夜三點以資料錯亂的形式出現」，這個交換在生產環境幾乎總是划算的。快速失敗（fail fast）勝過帶病運行。

---

## 五、`app.Run()`：卡住的那一行

```csharp
app.Run();
```

多數人知道這行「啟動應用程式」，但很少人注意到它是**阻塞**的——`Main` 的執行緒會停在這裡，直到收到關機訊號才往下走。這一行底下依序發生四件事。

### 5.1 Middleware pipeline 被組裝成一個委派

在 `Run()` 之前寫的所有 `app.UseXxx()` 其實只是在一個 `List<Func<RequestDelegate, RequestDelegate>>` 裡排隊。`Run()` 會把這串東西**由後往前**組合，最終得到一個 `RequestDelegate`——一個簽章為 `Task (HttpContext)` 的委派。

「由後往前」是理解 middleware 的關鍵。這個機制以及順序寫錯的實際後果，是 [[01-request-pipeline]] 整章的主題，這裡先記住結論：pipeline 在啟動時組裝一次，之後每個 request 重複使用同一個委派。

### 5.2 所有 IHostedService 依序啟動

Host 會取出所有註冊的 `IHostedService`，**按註冊順序**依序呼叫 `StartAsync`。而且是**依序等待**——前一個的 `StartAsync` 沒回來，下一個不會開始。

這裡藏著本章開頭的第二個問題。`GenericWebHostService`（那個真正啟動 Kestrel 的服務）是在 `CreateBuilder` 階段就被註冊的，所以它排在你自己寫的 `BackgroundService` 前面。也就是說：

```text
StartAsync 順序：
1. GenericWebHostService  → Kestrel 開始監聽 port，API 可以接請求了
2. 你的 MyBackgroundService
3. 你的 AnotherBackgroundService
```

Kestrel 先開始接請求，然後才輪到你的背景服務。如果背景服務需要在服務開放前完成初始化（例如預熱快取），這個順序就是問題。

反過來，`BackgroundService` 這個基底類別有一個容易誤解的行為：

```csharp
public class MyWorker : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            await DoWorkAsync();
            await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
        }
    }
}
```

`BackgroundService.StartAsync` 呼叫 `ExecuteAsync`，但**只等到第一個 `await` 為止**。第一個真正非同步的 await 一旦讓出控制權，`StartAsync` 就視為完成，Host 繼續啟動下一個服務。所以上面這個 worker 不會卡住啟動流程。

但如果 `ExecuteAsync` 開頭是一段同步的重活：

```csharp
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    Thread.Sleep(30000);   // ❌ 同步阻塞，整個 Host 啟動被卡 30 秒
    // ...
}
```

那麼在遇到第一個 await 之前，整個啟動流程都被卡住。K8s 的 startup probe 可能因此判定失敗並重啟 Pod，形成無限重啟迴圈——而 log 裡什麼錯誤都沒有。這類「啟動階段的同步阻塞」是很難查的問題，因為現象（Pod 一直重啟）和原因（某個 worker 的第一行）看起來毫無關聯。

還有一個更隱蔽的陷阱：**`ExecuteAsync` 裡拋出的未處理例外，在 .NET 6 之前會被靜默吞掉**，背景服務就這樣死了而應用程式繼續跑。.NET 6 起預設行為改成停止整個 Host（由 `HostOptions.BackgroundServiceExceptionBehavior` 控制），但如果你的專案從舊版升上來、或者顯式設成 `Ignore`，就要自己在 `ExecuteAsync` 裡包 try-catch 並記錄。

### 5.3 Kestrel 開始監聽

`GenericWebHostService.StartAsync` 裡面做的事包括：綁定 endpoint（決定監聽哪些位址和 port）、啟動 `IServer`、把組好的 pipeline 交給它。

**Kestrel 是什麼**：一個跨平台、用 C# 寫的高效能 HTTP server，內建在 ASP.NET Core 裡。它不是 IIS 的替代品，也不是 Nginx 的替代品——它是**應用程式內建的 server**。這是 .NET Core 與舊 ASP.NET 最結構性的差異之一。

那為什麼實務上還是常常在 Kestrel 前面放一層反向代理（Nginx、IIS、YARP，或在 K8s 裡是 Ingress Controller）？理由不是 Kestrel 不夠快，而是職責分工：

| 職責 | 誰做比較適合 |
| --- | --- |
| TLS 憑證管理與輪替 | 反向代理（cert-manager、Cloudflare） |
| 多個服務共用 80/443 並依網域分流 | 反向代理 |
| 靜態檔案、快取、壓縮 | 反向代理（或 CDN） |
| 防禦慢速連線攻擊、限流 | 反向代理 |
| 執行你的業務邏輯 | Kestrel |

在 K8s 裡這層分工天然存在：Ingress Controller 處理 TLS 與路由，你的 Pod 裡的 Kestrel 只聽 HTTP。所以容器裡通常**不需要**設定 HTTPS 憑證，也**不應該**開 `UseHttpsRedirection()`——它會在 Pod 內部把 HTTP 請求重導向到不存在的 HTTPS port，造成無限重導或 502。這是本章開頭第三個問題的變體之一。

監聽位址由 `ASPNETCORE_URLS` 環境變數決定。容器裡有一個必須注意的細節：

```yaml
env:
  - name: ASPNETCORE_URLS
    value: "http://+:8080"    # + 表示所有網卡
```

如果寫成 `http://localhost:8080`，Kestrel 只會綁定 loopback 介面，容器外部（包括同一個 Pod 裡的其他 container、以及 kubelet 的 probe）**完全連不進來**。現象是 Pod 內 `curl localhost:8080` 正常，但 Service 怎麼都通不了。用 `+` 或 `0.0.0.0` 才會綁定所有介面。

另外，.NET 8 的官方容器映像預設 port 從 80 改成了 **8080**（為了支援非 root 使用者執行——1024 以下的 port 需要特權）。從 .NET 6/7 升級的專案如果 Deployment 裡還寫 `containerPort: 80`，就會出現「容器起來了但連不上」。

### 5.4 執行緒停在這裡等關機訊號

四件事做完，`Run()` 內部等待一個 `TaskCompletionSource`，它會在收到關機訊號時完成。程式此刻進入穩定狀態：主執行緒睡著，ThreadPool 的執行緒在處理進來的請求。

---

## 六、Graceful Shutdown：滾動更新掉請求的真相

現在回到本章開頭第三個問題：**Pod 滾動更新時前端偶爾收到 502**。

要理解這件事，先看關機的完整序列。當程序收到 `SIGTERM`（K8s 刪 Pod 時送的訊號，或 Ctrl+C 送的 `SIGINT`）：

```text
1. 收到 SIGTERM
2. IHostApplicationLifetime.ApplicationStopping 被觸發（通知：我要關了）
3. 各 IHostedService 的 StopAsync 被呼叫（順序與啟動相反：後啟動的先停）
   └── GenericWebHostService.StopAsync → Kestrel 停止接受新連線，
       並等待進行中的請求完成
4. 等待上限 = ShutdownTimeout（預設 30 秒）
5. 逾時未完成的請求：CancellationToken 被取消，強制收工
6. ApplicationStopped 觸發
7. DI 容器 Dispose（Singleton 中實作 IDisposable 的被釋放）
8. 程序退出
```

框架這邊做得相當完整——**它會等進行中的請求跑完**。那 502 從哪來？

答案在框架之外。K8s 刪除一個 Pod 時，兩件事幾乎同時發生但**不保證順序**：

- kubelet 送 SIGTERM 給容器
- Endpoints controller 把這個 Pod 從 Service 的端點清單移除，然後 kube-proxy / Ingress 更新轉發規則

第二件事是**最終一致**的，需要時間傳播到叢集各處。如果應用程式收到 SIGTERM 後 200 毫秒就乾淨俐落地關掉了，而此時 Ingress 的轉發規則還沒更新完，那麼在這個空窗期打過來的請求會被送到一個已經關掉的 Pod——502。

所以問題不是「關得不夠乾淨」，而是**關得太快**。標準解法是在收到訊號後刻意拖一段時間再開始關閉：

```yaml
lifecycle:
  preStop:
    exec:
      command: ["sh", "-c", "sleep 10"]
terminationGracePeriodSeconds: 60
```

`preStop` 在 SIGTERM 之前執行，這 10 秒足夠端點移除傳播出去，期間應用程式照常服務。而 `terminationGracePeriodSeconds` 必須大於 `preStop 時間 + 應用程式的 ShutdownTimeout`，否則 K8s 會在應用程式排空完之前送 SIGKILL 強制砍掉——那就前功盡棄了。以上面的設定為例：10（preStop）+ 30（ShutdownTimeout）= 40 秒，設 60 秒有餘裕。

應用程式端的關機逾時可以調整：

```csharp
builder.Services.Configure<HostOptions>(options =>
{
    options.ShutdownTimeout = TimeSpan.FromSeconds(30);
});
```

如果服務有長時間執行的請求（大檔上傳、報表產生），這個值要拉長，並且同步拉長 `terminationGracePeriodSeconds`。兩邊要一起改——只改一邊沒有意義。

### 6.1 用 IHostApplicationLifetime 掛鉤

需要在關機時做收尾（沖刷緩衝、通知外部系統、註銷服務發現）就註冊回呼：

```csharp
public class ShutdownHandler
{
    public ShutdownHandler(IHostApplicationLifetime lifetime, ILogger<ShutdownHandler> logger)
    {
        lifetime.ApplicationStarted.Register(() => logger.LogInformation("服務已就緒"));
        lifetime.ApplicationStopping.Register(() => logger.LogInformation("開始排空請求"));
        lifetime.ApplicationStopped.Register(() => logger.LogInformation("已完全停止"));
    }
}
```

三個 token 的差別要分清楚：`ApplicationStopping` 是「宣告要關了，但還在服務中」，這時做通知、拒絕新工作；`ApplicationStopped` 是「請求都處理完了」，這時做最後的資源釋放。把清理邏輯掛在 `ApplicationStopped` 上並且執行超過幾秒，是危險的——那時候 K8s 的寬限期已經在倒數了。

`IHostApplicationLifetime.StopApplication()` 可以主動觸發關機。用途例如：偵測到設定嚴重錯誤、或是排程任務跑完就該退出的一次性 Job。

### 6.2 讓請求處理程式感知取消

關機時，進行中請求的 `HttpContext.RequestAborted` token 會在逾時後被取消。要讓這件事有意義，你的程式碼必須真的把 token 傳下去：

```csharp
[HttpGet]
public async Task<IActionResult> GetAllAsync(CancellationToken ct)
{
    // ct 由框架自動綁定為 HttpContext.RequestAborted，不需要任何 attribute
    var users = await _db.Users.ToListAsync(ct);
    return Ok(users);
}
```

Action 方法的 `CancellationToken` 參數會被 model binding 自動填入。這是零成本的好習慣：客戶端提早斷線時，資料庫查詢會被取消而不是繼續空轉。不傳 token 的程式碼在關機時只能被硬砍，或者拖滿整個寬限期。這個主題在 [[06-async-and-threading]] 深入。

---

## 七、Program.cs 的實際樣貌

把前面所有東西組起來，一個有意識地寫出來的 `Program.cs` 大致長這樣：

```csharp
var builder = WebApplication.CreateBuilder(args);

// 啟動期驗證：寧可啟動慢半秒，也不要設定錯誤在半夜以資料錯亂的形式現形
builder.Host.UseDefaultServiceProvider(options =>
{
    options.ValidateScopes = true;
    options.ValidateOnBuild = true;
});

builder.Services.Configure<HostOptions>(options =>
{
    options.ShutdownTimeout = TimeSpan.FromSeconds(30);
});

builder.Services.AddControllers();
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseOracle(builder.Configuration.GetConnectionString("Default")));
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddHealthChecks().AddDbContextCheck<AppDbContext>();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseExceptionHandler();
app.UseRouting();
app.UseCors("ReactApp");
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.MapHealthChecks("/healthz");

app.Run();
```

注意這裡**沒有** `UseHttpsRedirection()`——因為目標部署環境是 K8s，TLS 終結在 Ingress。如果部署在 IIS 或直接對外，就要加回來。這種「依部署環境決定 pipeline」的判斷貫穿整套教材。

---

## 八、常見誤解

**「`Program.cs` 裡的 `app.UseXxx()` 順序不重要，反正都會執行。」**
大錯。順序決定 pipeline 的巢狀結構，寫錯的後果從「CORS 失效」到「未登入使用者能存取受保護資源」都有。整章見 [[01-request-pipeline]]。

**「`app.Run()` 是啟動應用程式，之後的程式碼會繼續跑。」**
`Run()` 會阻塞到關機為止。寫在 `app.Run()` 後面的程式碼只有在關機流程走完之後才會執行——那通常不是你要的。要跑啟動後的邏輯，用 `lifetime.ApplicationStarted` 或 `IHostedService`。

**「BackgroundService 在 API 開始服務之前就會跑完初始化。」**
反了。Kestrel 的服務排在你的背景服務前面啟動，API 先開放接請求。需要「就緒後才對外」的語意，要靠 readiness probe 配合自訂的 health check 狀態，而不是靠啟動順序。

**「本機沒問題就代表設定正確。」**
本機是 Development 環境，開了 scope validation、載入了 User Secrets、launchSettings 幫你設好了 URLs。上了容器這三樣全部消失。這是「本機好好的、上 K8s 就掛」最常見的成因。

**「Kestrel 不能直接對外，一定要放 Nginx。」**
Kestrel 本身有足夠的效能與安全性可以直接對外（微軟官方支援這種部署）。放反向代理是為了憑證管理、多服務共用 port、集中式限流等**運維**理由，不是因為 Kestrel 有缺陷。

---

## 九、同事會來問你的問題

蓋住下面的答案，先自己講一遍。

**Q：為什麼在 `Program.cs` 裡直接 `app.Services.GetRequiredService<AppDbContext>()` 會炸？**
因為 `app.Services` 是 root provider，而 DbContext 註冊為 Scoped。框架禁止從 root 解析 Scoped 服務，避免它被俘虜成事實上的 Singleton。正解是 `app.Services.CreateScope()` 自己開一個 scope，用完就 dispose。

**Q：Pod 一直重啟，log 沒有任何錯誤，可能是什麼？**
先看 startup/liveness probe 是否過早或逾時太短。應用程式端的常見成因是某個 `IHostedService.StartAsync` 或 `ExecuteAsync` 在第一個 await 之前有同步阻塞，把整個 Host 的啟動流程卡住，導致 probe 判定失敗。用 `kubectl describe pod` 看事件，比看 log 有效。

**Q：Service 通不了，但進 Pod `curl localhost:8080` 正常，為什麼？**
Kestrel 綁定了 loopback 而非所有介面。檢查 `ASPNETCORE_URLS`，要用 `http://+:8080` 或 `http://0.0.0.0:8080`，不能是 `localhost`。

**Q：滾動更新時前端偶爾 502，但應用程式關機看起來很乾淨，怎麼辦？**
問題出在關太快而不是關不乾淨。K8s 移除 Service endpoint 是最終一致的，有傳播延遲。加 `preStop: sleep 10` 讓端點移除先傳播出去，並確認 `terminationGracePeriodSeconds` 大於 preStop 時間加上應用程式的 `ShutdownTimeout`。

**Q：`ValidateOnBuild` 為什麼預設在 Production 是關的？我該打開嗎？**
預設關閉是為了縮短啟動時間。建議打開：它把生命週期配對錯誤從「執行期偶發的詭異行為」變成「啟動時明確失敗」，符合快速失敗原則。代價只是啟動慢一點點。

**Q：Swagger 在測試環境看不到，程式碼明明有寫。**
範本把 `UseSwagger` 包在 `if (app.Environment.IsDevelopment())` 裡，而測試環境的 `ASPNETCORE_ENVIRONMENT` 不是 `Development`。要嘛改判斷條件（例如排除 Production），要嘛在該環境明確設定環境名稱。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[01-request-pipeline]] — 下一章：pipeline 的組裝與順序
- [[02-dependency-injection]] — scope 的建立與釋放、captive dependency
- [[06-async-and-threading]] — CancellationToken 的傳遞與 ThreadPool
- [[21-deployment]] — 容器化、probe 對接、遷移策略
- [[kubernetes]] — 部署環境
- [[k8s-mastery]] — 部署端的對應教材
