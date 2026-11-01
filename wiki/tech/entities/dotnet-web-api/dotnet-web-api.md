---
type: entity
domain: tech
tags: [dotnet, aspnet, csharp, web-api, backend, middleware, routing, filters, clean-architecture, efcore, oracle, jwt, oauth, mastery, curriculum, book]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
  - raw/Web Framework/NET Web API/Chapter 1：HTTP 與 Web API 的核心概念.md
  - raw/Web Framework/NET Web API/Chapter 2：ASP NET Core Web API.md
  - raw/Web Framework/NET Web API/Chapter 3：Controller、Routing 與 Action 設計.md
  - raw/Web Framework/NET Web API/Chapter 4：DTO 與資料模型設計.md
  - raw/Web Framework/NET Web API/Chapter 5：Dependency Injection 與 Service 設計.md
  - raw/Web Framework/NET Web API/Chapter 6：Middleware 與全域處理機制.md
  - raw/Web Framework/NET Web API/Chapter 7：EF Core 與資料存取設計.md
  - raw/Web Framework/NET Web API/Chapter 7.1 Authentication Authorization Pipeline.md
  - raw/Web Framework/NET Web API/Chapter 7.2 Authentication & Authorization.md
  - raw/Web Framework/NET Web API/chapter 7.3 後端各種權限管理的寫法，搭配前端操作的實務範例.md
  - raw/Web Framework/NET Web API/Chapter 8：Authentication 與 Authorization（JWT）.md
  - raw/Web Framework/NET Web API/Chapter 9：Swagger、API 文件化與版本管理.md
  - raw/Web Framework/NET Web API/Chapter 10：測試、部署與正式上線準備.md
  - raw/Web Framework/NET Web API/ASP NET Core Web API 常用 Attribute 整理.md
  - raw/Web Framework/NET Web API/ASP.NET Core 開發人員指南.md
  - raw/Web Framework/NET Web API/HTTP 協議.md
  - raw/Web Framework/NET Web API/Middleware Pipeline.md
  - raw/Web Framework/NET Web API/NET 6 Web API JWT 驗證與授權完整設定與實作指南.md
  - raw/Web Framework/NET Web API/Swagger 在 HTTP Pipeline 中的位置與設計理由.md
  - raw/Web Framework/NET Web API/appsetting json.md
  - raw/Web Framework/NET Web API/aspnet-web-api-web-research/aspnet-web-api-web-research.md
created: 2026-05-03
updated: 2026-11-01
---

# ASP.NET Core Web API：從入門到專家

這是一本書的目錄。全書分成三篇，一章一個檔案：入門篇從 HTTP 寫到把第一支 API 部署上線，深度篇拆開框架內部機制與生產維運，專家篇處理設計取捨、安全與效能工程。

會寫 ASP.NET Core Web API 的人很多。能說清楚一個 request 從 Kestrel 收到 socket 之後、到 `IActionResult` 被序列化寫回去之前，中間經過哪幾層、每層改了什麼、哪一層攔得住例外的人很少。前者遇到「本機好好的、上 K8s 就 500」只能加 log 亂試，後者能從症狀反推到 scope 被誰提早釋放。這本書的目標是把讀者從前者送到後者，而且不假設你一開始會寫。

下半部另有一份[速查](#速查)，趕時間查語法直接跳過去。

---

## 起點與終點

**起點**：會基本 C# 語法，聽過 HTTP，沒寫過 Web API。

**讀完入門篇**：能獨立寫出一支有資料庫、有登入與權限、有文件、有測試、能以容器部署的 API，而且知道每一行為什麼在那裡。

**讀完深度篇**：能判斷一段設定會不會在高併發下出事，能審查別人的 PR 並指出生命週期用錯的地方，能從「偶發逾時」推理到 ThreadPool 飢餓或連線池耗盡。

**讀完專家篇**：能為專案選架構並說明代價，能沿著 OWASP 清單找出自己 API 的洞，能用量測而不是直覺解決效能問題，能設計跨服務的一致性，能教別人。

## 怎麼讀

**從零開始**：入門篇 01 到 16 依序跟著做，每章都會往同一個範例專案加東西，跳章會接不上。第 17 章是附錄，查閱用。接著讀深度篇，最後專家篇。

**已經寫過 Controller、串過 JWT**：直接從深度篇 [[00-hosting-and-startup]] 開始，入門篇當查閱。如果你的認知來自 .NET 6 時代的教學，先掃過入門篇的「常見誤解」段落，有些當時的說法到 .NET 10 已經不成立。

**手上有 .NET 8 專案要升級**：讀 [[expert-08-dotnet-8-to-10]]。.NET 8 與 .NET 9 都在 2026-11-10 終止支援。

**正在救火**：[[23-cheatsheet]] 的緊急排錯十連發，效能問題看 [[expert-05-performance-engineering]] 的症狀對照表。

每一遍的讀法也不同。第一遍求通不求精，卡住的段落標記起來繼續往下，很多概念要看過後面才回頭理解得了。第二遍動手拆，把章節裡的反例親手弄壞一次，比讀十遍有效。第三遍反過來考自己，把每章末尾的「同事會來問你的問題」蓋住答案先講一遍，講得出來才算會。

---

## 第一部：入門篇

寫給沒寫過 Web API 的讀者。主線是一支 TaskTracker API，對齊 [[javascript-typescript-react-foundations]] 的前端資料形狀，從空資料夾長成可以上線的服務。

| 章 | 回答的問題 |
| --- | --- |
| [[basics-01-http-and-web-api]] | 瀏覽器與伺服器到底在交換什麼？GET 和 POST 只是名字不同嗎？ |
| [[basics-02-rest-api-design]] | 一支 API 的 URL 與狀態碼該怎麼決定，才不會每個人寫得不一樣？ |
| [[basics-03-first-project]] | `dotnet new` 產生的東西各是什麼？請求進來時 Program.cs 在做什麼？ |
| [[basics-04-controllers-and-routing]] | 怎麼把 API 規格變成可以呼叫的端點？ |
| [[basics-05-model-binding-and-validation]] | 請求裡的字串怎麼變成 C# 參數？不合法的輸入誰來擋？ |
| [[basics-06-dto-design]] | 為什麼不能直接把 entity 回傳給前端？ |
| [[basics-07-dependency-injection-and-services]] | Controller 越來越胖，邏輯該放哪？物件誰來 new？ |
| [[basics-08-middleware-and-exception-handling]] | 每支 API 都要做的事放哪？為什麼順序會影響結果？ |
| [[basics-09-configuration-and-environments]] | 開發與正式環境設定不同時怎麼辦？機密放哪？ |
| [[basics-10-efcore-and-oracle]] | 資料怎麼真的存進 Oracle？ |
| [[basics-11-auth-concepts-and-pipeline]] | 誰可以呼叫這支 API？驗證與授權差在哪？ |
| [[basics-12-jwt-login]] | 登入後怎麼證明「我是我」？JWT 怎麼簽、怎麼驗？ |
| [[basics-13-permissions-with-frontend]] | 前端要依權限顯示按鈕，前後端怎麼對齊才安全？ |
| [[basics-14-openapi-and-versioning]] | 前端同事怎麼知道這支 API 怎麼用？改版怎麼不弄壞他們？ |
| [[basics-15-testing]] | 改了程式怎麼知道沒弄壞東西？ |
| [[basics-16-deployment-and-go-live]] | 怎麼安全地上線、上線後怎麼知道它活著？ |
| [[basics-17-attribute-reference]] | 附錄：這個 Attribute 到底做什麼？ |

### 範例專案怎麼驗證

書裡的程式碼與回應內容都來自實際執行。TaskTracker 以 .NET SDK 10.0.301 與 Oracle Database 23ai Free 建置，每章結束時的狀態都單獨建置過（14 個階段全部成功、零警告），最終狀態 77 個測試全過，其中整合測試跑在 Testcontainers 啟動的真實 Oracle 上。舊筆記與舊教材裡有疑慮的 15 項框架行為，例如省略 `UseAuthentication()` 會怎樣、`next()` 沒呼叫回什麼，也都用最小程式實測過，書中以實測結果為準。

專案本身不放在這個 vault 裡，各章都給了足夠的程式碼與步驟，跟著做就會得到它。

---

## 第二部：深度篇

預設讀者已經寫過 Controller、設過 DI、串過 JWT，也許已經把服務部署到容器裡跑過，但心裡清楚很多地方是照抄範例。每章以一個真實會出事的場景開篇，收尾固定「常見誤解」與「同事會來問你的問題」。

這一部以 **.NET 8 LTS** 為基準撰寫，機制到 .NET 10 大多不變，有變化的地方集中在 [[expert-08-dotnet-8-to-10]]。它假設的部署環境是 K8s + Oracle + JWT/Google OAuth + 前後端分離，所以很多章節會走到框架邊界之外：graceful shutdown 一節直接推導到 K8s 滾動更新掉請求的 `preStop` 解法，設定一章區分 ConfigMap 用 env 與 volume 注入的差別，資料層有一整章專講 Oracle provider 的坑（大小寫、空字串即 NULL、`IN` 上限 1000、DDL 隱含提交）。

| 主題 | 章節 | 核心問題 |
| --- | --- | --- |
| **執行模型** | [[00-hosting-and-startup]] | `WebApplication.CreateBuilder` 到 `app.Run()` 之間到底發生什麼事？ |
| | [[01-request-pipeline]] | Middleware 為什麼是洋蔥？順序寫錯會怎樣？ |
| | [[02-dependency-injection]] | scope 什麼時候建、什麼時候放？captive dependency 怎麼咬人？ |
| | [[03-routing-and-endpoints]] | Endpoint routing 的兩階段、Minimal API 和 Controller 的底層差異 |
| | [[04-model-binding-and-validation]] | 參數是怎麼被填進去的？驗證失敗的 400 是誰產生的？ |
| | [[05-filters-and-mvc-internals]] | Filter 和 Middleware 差在哪？五種 Filter 的執行順序 |
| | [[06-async-and-threading]] | async 到底省了什麼？ThreadPool 飢餓怎麼發生的？ |
| **資料層** | [[07-efcore-internals]] | DbContext 為什麼一定要 Scoped？change tracker 在追蹤什麼？ |
| | [[08-efcore-query]] | LINQ 怎麼變成 SQL？N+1 怎麼看出來？ |
| | [[09-transactions-and-concurrency]] | 交易邊界該畫在哪？兩個人同時改一筆資料怎麼辦？ |
| | [[10-oracle-specifics]] | Oracle + EF Core 的坑：大小寫、序列、CLOB、分頁 |
| **認證授權** | [[11-authentication]] | Scheme 是什麼？Challenge 和 Forbid 差在哪？ |
| | [[12-jwt-deep-dive]] | JWT 驗了哪些東西？登出為什麼沒用？ |
| | [[13-oauth-oidc]] | Google 登入的完整流程、前後端分離的取捨 |
| | [[14-authorization]] | Role、Claim、Policy、Requirement 該用哪個？ |
| **工程實務** | [[15-error-handling]] | 例外該在哪一層接？什麼錯回什麼 status code？ |
| | [[16-logging-and-observability]] | 結構化 log、correlation id、對接 ELK 與 Prometheus |
| | [[17-configuration-and-secrets]] | Provider 鏈、Options 三介面、K8s Secret 注入 |
| | [[18-resilience-and-performance]] | HttpClientFactory、Polly、快取、rate limiting |
| | [[19-background-work]] | BackgroundService 與 Hangfire、多副本重複執行問題 |
| | [[20-testing]] | 單元測試該測到哪？WebApplicationFactory 整合測試 |
| | [[21-deployment]] | 容器化、probe 對接、graceful shutdown、API 版本 |
| **附錄** | [[22-self-assessment]] | 自我檢測題，蓋住答案自己講一遍才算會 |
| | [[23-cheatsheet]] | 速查：pipeline 骨架、生命週期決策表、常見錯誤對照 |

---

## 第三部：專家篇

入門篇教怎麼做對，深度篇教為什麼這樣才對，這一部處理沒有標準答案的問題：什麼時候該選哪個、代價是什麼、怎麼證明。

| 章 | 回答的問題 | 狀態 |
| --- | --- | --- |
| [[expert-01-advanced-api-design]] | 分頁、部分更新、併發、重送、長任務這些真實需求怎麼設計？ | 撰寫中 |
| [[expert-02-architecture]] | 專案長大之後程式該怎麼組織？Clean Architecture 一定是答案嗎？ | 撰寫中 |
| [[expert-03-minimal-api-and-aot]] | 範本預設就是 Minimal API，它和 Controller 到底差在哪？ | 撰寫中 |
| [[expert-04-security-hardening]] | 功能都對了之後，API 還會怎麼被打穿？ | 撰寫中 |
| [[expert-05-performance-engineering]] | API 變慢了，怎麼從症狀查到根因並證明修好了？ | 撰寫中 |
| [[expert-06-streaming-and-realtime]] | 請求一回應不夠用時，大檔案、即時推送、服務間呼叫怎麼做？ | 撰寫中 |
| [[expert-07-messaging-and-distributed-consistency]] | 一個操作要改資料庫又要通知別的服務，怎麼不掉事件、不重複處理？ | 撰寫中 |
| [[expert-08-dotnet-8-to-10]] | 深度篇以 .NET 8 為基準，到了 .NET 10 哪些地方不一樣？ | 撰寫中 |
| [[expert-09-roadmap-and-capstone]] | 讀完這本書，怎麼才算專家？接下來具體要做什麼？ | 撰寫中 |

部署與維運的完整教材在 [[k8s-mastery]]，同一個場景的 Python 版本在 [[python-fast-api]]，跨框架翻譯表見 [[13-aspnet-mapping]]。

---

## 來源對照

入門篇由 `raw/Web Framework/NET Web API/` 底下的筆記改寫而成。原始筆記沒有更動。

| 來源 | 收進哪裡 |
| --- | --- |
| Chapter 1、HTTP 協議 | [[basics-01-http-and-web-api]]、[[basics-02-rest-api-design]] |
| Chapter 2、NET Web API、開發人員指南、Microsoft | [[basics-03-first-project]]、[[expert-09-roadmap-and-capstone]] |
| Chapter 3 | [[basics-04-controllers-and-routing]]、[[basics-05-model-binding-and-validation]] |
| Chapter 4 | [[basics-05-model-binding-and-validation]]、[[basics-06-dto-design]] |
| Chapter 5 | [[basics-07-dependency-injection-and-services]] |
| Chapter 6、Middleware Pipeline | [[basics-08-middleware-and-exception-handling]] |
| appsetting json | [[basics-09-configuration-and-environments]] |
| Chapter 7 | [[basics-10-efcore-and-oracle]] |
| Chapter 7.1、7.2 | [[basics-11-auth-concepts-and-pipeline]] |
| Chapter 8、NET 6 JWT 指南 | [[basics-11-auth-concepts-and-pipeline]]、[[basics-12-jwt-login]] |
| chapter 7.3 | [[basics-13-permissions-with-frontend]] |
| Chapter 9、Swagger 在 Pipeline 中的位置 | [[basics-14-openapi-and-versioning]] |
| Chapter 10 | [[basics-09-configuration-and-environments]]、[[basics-15-testing]]、[[basics-16-deployment-and-go-live]] |
| Attribute 整理 | [[basics-04-controllers-and-routing]]、[[basics-05-model-binding-and-validation]]、[[basics-17-attribute-reference]] |
| aspnet-web-api-web-research | [[basics-04-controllers-and-routing]]、[[basics-08-middleware-and-exception-handling]]、[[expert-02-architecture]] |
| DTO、HTTP Server | 空檔，沒有內容 |

### 改寫時修正的主要錯誤

原始筆記是不同時期累積的，有些說法過時或不正確。以下都經實測或官方文件查證，書中以修正後的內容為準；如果你記得的是舊說法，這張表值得看一次。

| 主題 | 筆記的說法 | 實際情況 |
| --- | --- | --- |
| Transient | 每次請求建立新實例 | 每次解析建立新實例，同一請求注入兩次得到兩個物件 |
| Singleton 注入 Scoped | 會丟 runtime 例外 | Development 預設在 `Build()` 失敗，Production 靜默變成 singleton |
| 沒呼叫 `next()` | 請求卡住 | 回 200、`Content-Length: 0`、空 body |
| `MapControllers()` 之後的 middleware | 不會執行 | `WebApplication` 下照常在 endpoint 之前執行 |
| Swagger 在 pipeline 的位置 | 同一篇說是 endpoint 又說是 middleware，還會被 `[Authorize]` 擋 | `MapOpenApi` 是 endpoint，.NET 9 起範本不含 Swashbuckle |
| 隱式綁定 | 依 HTTP method 判斷 | 依 `[ApiController]` 與型別判斷，複合型別在 GET 也推斷為 body |
| `[controller]` | 展開成小寫 | 保留 PascalCase，比對時不分大小寫 |
| `[AllowAnonymous]` | Action 層級優先 | 出現在任何層級都略過授權 |
| JWT 金鑰存放 | appsettings 是安全存放處 | 不能有真實金鑰，開發用 User Secrets，正式環境用 Secret 或 Vault |
| HS256 金鑰長度 | 16 字元範例 | 至少 32 bytes，錯誤訊息不會直接指出是長度問題 |
| `sub` | 對應 `User.Identity.Name` | 兩者無關，`MapInboundClaims` 預設還會把 `sub` 改名 |
| 測試資料庫 | 推薦 InMemory 或 SQLite | 用 Testcontainers 跑真實資料庫，與資料庫行為有關的測試才可信 |
| API 版本套件 | `Microsoft.AspNetCore.Mvc.Versioning` | 已改為 `Asp.Versioning.*` |
| 錯誤回應 | 自創 `{ message }` | `ProblemDetails`（RFC 9457，取代 7807） |

---

## 速查

以下程式碼取自 TaskTracker 最終狀態，已建置並通過測試。

### 技術堆疊

- **.NET**：10（LTS，支援到 2028-11）
- **API 類型**：Controller（`dotnet new webapi --use-controllers`，範本預設是 Minimal API）
- **文件**：內建 `Microsoft.AspNetCore.OpenApi` + Scalar
- **版本**：`Asp.Versioning.*`
- **資料庫**：EF Core 10 + `Oracle.EntityFrameworkCore`
- **測試**：xUnit v3 + `WebApplicationFactory` + Testcontainers

### Controller

```csharp
[ApiController]
[ApiVersion(1.0)]
[Authorize(Policy = Permissions.TasksRead)]
[Route("api/v{version:apiVersion}/tasks")]
public class TasksController : ControllerBase
{
    private readonly ITaskService _taskService;

    public TasksController(ITaskService taskService)
    {
        _taskService = taskService;
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<TaskResponse>> GetByIdAsync(Guid id, CancellationToken ct)
    {
        return Ok(await _taskService.GetByIdAsync(id, ct));
    }

    [Authorize(Policy = Permissions.TasksWrite)]
    [HttpPost]
    [ProducesResponseType<TaskResponse>(StatusCodes.Status201Created)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status409Conflict)]
    public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct)
    {
        var task = await _taskService.CreateAsync(request, ct);
        return CreatedAtAction(nameof(GetByIdAsync), new { id = task.Id }, task);
    }
}
```

`CreatedAtAction(nameof(GetByIdAsync))` 要搭配 `AddControllers(o => o.SuppressAsyncSuffixInActionNames = false)`，否則框架登記的 action 名稱沒有 `Async`，建立成功後回 500。

### Program.cs 順序

```csharp
var app = builder.Build();

app.UseMiddleware<RequestLoggingMiddleware>();
app.UseExceptionHandler();
app.UseStatusCodePages();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi().WithDocumentPerVersion();
    app.MapScalarApiReference();
}

app.UseHttpsRedirection();
app.UseCors(CorsPolicyOptions.PolicyName);
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.MapTaskTrackerHealthChecks();

app.Run();
```

順序即行為。記錄放最外層才記得到最終狀態碼，例外處理要包住所有可能丟例外的 middleware，驗證在授權之前。順序的完整推導見 [[01-request-pipeline]]。

### Middleware Pipeline

![Middleware Pipeline](middleware-pipeline.png)

每個 middleware 選擇是否把 request 傳給下一個，可在前後各做一次工作。

| 方法 | 說明 |
| --- | --- |
| `Use` | 鏈接 middleware，呼叫 `next` 往下傳 |
| `Run` | Terminal middleware，結束 pipeline |
| `Map` | 依路徑前綴分支 |
| `MapWhen` | 依任意 predicate 分支 |

注意：response 開始寫入後不能修改 header，也不能再回 ProblemDetails；沒呼叫 `next` 且沒寫回應，結果是 200 空 body。

### DI 三種 Lifetime

```csharp
builder.Services.AddSingleton<IMyService, MyService>(); // 整個應用共用一個實例
builder.Services.AddScoped<IUserService, UserService>(); // 每個 scope（HTTP request）一個實例
builder.Services.AddTransient<IEmailService, EmailService>(); // 每次解析一個新實例
```

| Lifetime | 存活範圍 | 適用場景 |
| --- | --- | --- |
| Singleton | app 整個生命週期 | 無狀態工具、快取、設定 |
| Scoped | 一個 HTTP request | `DbContext`、業務邏輯 Service |
| Transient | 每次解析就新建 | 輕量、無狀態的小工具 |

詳細機制與踩坑見 [[02-dependency-injection]]。

### 內建自動註冊（不需手動加）

| 服務 | 說明 |
| --- | --- |
| `IConfiguration` | 設定系統，`CreateBuilder` 時自動建立 |
| `ILogger<T>` | Logging，自動注入 |
| `IWebHostEnvironment` | 環境資訊（Development / Production） |
| `IHttpContextAccessor` | 這個不是內建，需手動加 `AddHttpContextAccessor()` |

### DTO 設計

```csharp
// API 的資料契約，不直接暴露 entity
public record CreateUserDto(string Name, string Email, string Password);
public record UpdateUserDto(string? Name, string? Email);
public record UserDto(int Id, string Name, string Email); // 不含 Password
```

### JWT 驗證設定

```csharp
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer();
services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Configure<IOptions<JwtOptions>>((bearer, jwt) =>
    {
        bearer.MapInboundClaims = false;
        bearer.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwt.Value.Issuer,
            ValidateAudience = true,
            ValidAudience = jwt.Value.Audience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwt.Value.SigningKey)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),
            RoleClaimType = "role"
        };
    });
```

三個坑：HS256 金鑰至少 32 bytes；`MapInboundClaims = false` 時要同時設 `RoleClaimType`，否則 `[Authorize(Roles = ...)]` 一律 403；`ClockSkew` 預設是 5 分鐘。

### CORS 設定（開發環境）

```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("ReactApp", policy =>
    {
        policy.WithOrigins("http://localhost:5173") // Vite 預設 port
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials();
    });
});
```

CORS 是瀏覽器的機制，不是伺服器的安全防線。`AllowAnyOrigin` 搭配 `AllowCredentials` 會在啟動時丟例外。

### 常用 Attribute

| Attribute | 說明 |
| --- | --- |
| `[ApiController]` | 自動回 400、推斷 `[FromBody]`、要求 attribute routing |
| `[Route("api/[controller]")]` | 路由模板，`[controller]` 換成類別名稱（保留大小寫） |
| `[HttpGet]` / `[HttpPost]` | HTTP 方法 |
| `[FromBody]` / `[FromRoute]` / `[FromQuery]` | 指定綁定來源 |
| `[Authorize]` | 需要認證；`Roles = "A,B"` 是 OR，疊兩個是 AND |
| `[AllowAnonymous]` | 允許匿名，出現在任何層級都略過授權 |

完整內容見 [[basics-17-attribute-reference]]。

### IConfiguration 合併順序

`WebApplication.CreateBuilder(args)` 執行時自動建立，依序載入，後面蓋前面：

| 順序 | 來源 | 說明 |
| --- | --- | --- |
| 1 | `appsettings.json` | 基礎設定 |
| 2 | `appsettings.{Environment}.json` | 環境覆蓋 |
| 3 | User Secrets | 只在 Development 載入 |
| 4 | 環境變數 | K8s Secret、Docker env 等，巢狀用 `__` |
| 5 | 命令列參數 `args` | 最高優先權 |

```csharp
var key = _configuration["Jwt:Key"]; // 冒號分隔巢狀結構

// Options Pattern（強型別，推薦用於複雜設定）
builder.Services.AddOptions<JwtOptions>()
    .BindConfiguration("Jwt")
    .ValidateDataAnnotations()
    .ValidateOnStart();
```

| 環境 | 建議做法 |
| --- | --- |
| 本機開發 | `appsettings.Development.json` 或 User Secrets |
| K8s / Docker | 環境變數（覆蓋 `appsettings.json` 的同名 key） |
| 生產敏感資料 | K8s Secret → 環境變數 / Vault，**不進版控** |

### Routing 速查

| Template | 說明 |
| --- | --- |
| `{id}` | 必填路由參數 |
| `{id?}` | 可選參數 |
| `{id=1}` | 有預設值的參數 |
| `{**slug}` | Catch-all，匹配所有剩餘路徑 |

常用 constraint：`:int`、`:bool`、`:guid`、`:alpha`、`:minlength(N)`、`:maxlength(N)`、`:regex(pattern)`。Constraint 是消歧義不是驗證，不符合時回 404 而不是 400。

```csharp
[Route("users/{id:int:min(1)}")]
public User GetUserById(int id) { }

app.MapGroup("/api/todos").MapTodosApi().RequireAuthorization();
```

### Filter Pipeline

```text
Authorization → Resource → Model Binding → Action → Exception → Result → Response
```

| 類型 | 時機 | 用途 |
| --- | --- | --- |
| Authorization | 最先 | 驗證授權，可 short-circuit |
| Resource | Authorization 後 | Model binding 前後，適合快取 |
| Action | Action method 前後 | 修改參數或結果 |
| Exception | 未處理例外 | MVC 範圍內的錯誤處理 |
| Result | Action result 執行前後 | 包裝回應或 formatter |

有 DI 需求時用 `ServiceFilterAttribute` 或 `TypeFilterAttribute`；實作 `IOrderedFilter` 可覆蓋執行順序。完整推導見 [[05-filters-and-mvc-internals]]。

### 架構模式

![Clean Architecture Onion](clean-architecture-onion.png)

依賴方向：由外往內（UI / Infrastructure → Application Core），核心不依賴外層。

| 層 | 內容 |
| --- | --- |
| Application Core | Entities、Interfaces、Domain Services、DTOs |
| Infrastructure | EF Core DbContext、Repository、外部服務 |
| UI Layer | Controllers、Middleware、Filters、Program.cs |

ASP.NET Core 完整架構：![Clean Architecture ASP.NET Core](clean-architecture-aspnetcore.png)

傳統 N-Layer（`UI → BLL → DAL`）的缺點是 BLL 依賴 DAL 實作細節，難以單元測試；Clean Architecture 透過 DI + Interface 解決。各種架構的適用條件與代價見 [[expert-02-architecture]]。

| | Monolith | Microservices |
| --- | --- | --- |
| 部署 | 單一 container | 多個獨立服務 |
| Scaling | 整體複製 | 個別服務 scale |
| 複雜度 | 低 | 高 |
| 適合 | 早期 / 小型 | 需獨立 scale 的大型系統 |

## 連結

- [[csharp]] — .NET Web API 使用的語言
- [[react]] — 前端框架，需設定 CORS 對接
- [[javascript-typescript-react-foundations]] — TaskTracker 前端的資料形狀
- [[docker]] — 部署 Web API 到容器
- [[kubernetes]] — 容器編排，部署後端服務
- [[oracle]] — 資料庫，EF Core provider 對接
- [[hangfire]] — 背景排程工具
- [[k8s-mastery]] — 部署端的對應教材
- [[python-fast-api]] — 同一場景的 Python 版教材；跨框架翻譯表見 [[13-aspnet-mapping]]
- [[web-backend-moc]] — 後端主題入口
