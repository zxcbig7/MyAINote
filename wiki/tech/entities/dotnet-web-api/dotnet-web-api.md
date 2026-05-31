---
type: entity
domain: tech
tags: [dotnet, aspnet, csharp, web-api, backend, middleware, routing, filters, clean-architecture]
sources:
  - raw/tech/web-dev/NET Web API.md
  - raw/ASP Web API/aspnet-web-api-web-research.md
created: 2026-05-03
updated: 2026-05-09
---

# .NET Web API

ASP.NET Core Web API 是建立 RESTful API 的框架，使用 C# 開發，支援 DI、Middleware Pipeline、JWT 等企業級功能。

## 技術堆疊選擇

- **.NET SDK**：8（LTS）
- **API 類型**：Controller-based（學習曲線清楚）
- **文件**：Swagger（Swashbuckle）
- **資料庫**：EF Core + Oracle（或其他）

## 學習路徑

### 1. 基礎知識

- HTTP / REST：GET/POST/PUT/PATCH/DELETE、Status Code、Headers、Body
- Controller、Routing、Model Binding、Validation
- Middleware Pipeline（`UseRouting` → `UseAuthentication` → `UseAuthorization` → `UseCors`）
- DI（依賴注入）、Service Lifetime（Singleton/Scoped/Transient）
- 設定：appsettings.json、Options pattern、Secret 管理

### 2. 資料層

- EF Core：DbContext、Entity、Migration、CRUD
- DTO 與 AutoMapper
- 交易與並發（Transaction、RowVersion）

### 3. 品質與安全

- 全域例外處理（Exception Handling Middleware）
- Logging（Serilog）與 Health Checks
- Authentication / Authorization（JWT、Policy、Role）
- CORS、Rate limiting、API Versioning

### 4. 交付

- Swagger 文件化
- 測試（Unit + Integration）
- Docker / 部署（IIS、Linux + Nginx 反代）

## Controller 架構

```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;

    public UsersController(IUserService userService)
    {
        _userService = userService;
    }

    [HttpGet]
    public async Task<IActionResult> GetAllAsync()
    {
        var users = await _userService.GetAllAsync();
        return Ok(users);
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetByIdAsync(int id)
    {
        var user = await _userService.GetByIdAsync(id);
        if (user == null) return NotFound();
        return Ok(user);
    }

    [HttpPost]
    public async Task<IActionResult> CreateAsync([FromBody] CreateUserDto dto)
    {
        var user = await _userService.CreateAsync(dto);
        return CreatedAtAction(nameof(GetByIdAsync), new { id = user.Id }, user);
    }
}
```

## Middleware Pipeline

![Middleware Pipeline](middleware-pipeline.png)

每個 middleware 元件選擇是否把 request 傳給下一個，可在前後各做一次工作。

| 方法 | 說明 |
| --- | --- |
| `Use` | 鏈接 middleware，呼叫 `next.Invoke()` 往下傳 |
| `Run` | Terminal middleware，結束 pipeline |
| `Map` | 依路徑前綴分支 |
| `MapWhen` | 依任意 Predicate 分支 |

```csharp
// Program.cs 的 Pipeline 順序（非常重要）
app.UseHttpsRedirection();
app.UseCors("ReactApp");           // CORS 要在 Auth 前
app.UseAuthentication();           // 先驗證身份
app.UseAuthorization();            // 再驗證權限
app.UseRouting();
app.MapControllers();
```

注意：response 開始後不能修改 header；Exception middleware 要放最前面。

## DI（依賴注入）

### 核心概念

DI 容器負責「建立物件」和「管理物件的生命週期」。你只需要：

1. **登記**：`builder.Services.AddXxx<Interface, Impl>()` — 告訴容器「有人要 Interface，給他 Impl」
2. **宣告需求**：在建構子加參數 — 容器收到 request 要建物件時，自動把依賴塞進來

```csharp
// ❌ 傳統做法：自己 new，緊耦合
public class OrderService
{
    private readonly EmailService _email = new EmailService(); // 無法替換、無法測試
}

// ✅ DI：只依賴介面，容器負責給實作
public class OrderService
{
    private readonly IEmailService _email;
    public OrderService(IEmailService email) { _email = email; }
}
```

### 何時注入（建構子注入時機）

| 物件類型 | 建立時機 | 注入時機 |
| --- | --- | --- |
| Controller | 收到 request，routing 決定用哪個 controller | 同時建立，建構子參數自動注入 |
| Scoped Service | 同上，每個 request 一個 | 同上 |
| Singleton Service | app 啟動時第一次被要求時 | 一次建立，之後共用 |

### 三種 Lifetime

```csharp
builder.Services.AddSingleton<IMyService, MyService>();      // 整個應用共用一個實例
builder.Services.AddScoped<IUserService, UserService>();      // 每個 HTTP Request 一個實例
builder.Services.AddTransient<IEmailService, EmailService>(); // 每次注入一個新實例
```

| Lifetime | 存活範圍 | 適用場景 |
| --- | --- | --- |
| Singleton | app 整個生命週期 | 無狀態工具、快取、設定 |
| Scoped | 一個 HTTP request | DB context、業務邏輯 Service |
| Transient | 每次被注入就新建 | 輕量、無狀態的小工具 |

### ASP.NET Core 內建自動註冊（不需手動加）

| 服務 | 說明 |
| --- | --- |
| `IConfiguration` | 設定系統，`CreateBuilder` 時自動建立 |
| `ILogger<T>` | Logging，自動注入 |
| `IWebHostEnvironment` | 環境資訊（Development / Production） |
| `IHttpContextAccessor` | 需手動加 `AddHttpContextAccessor()` |

### IHttpClientFactory

```csharp
// 登記（避免直接 new HttpClient 造成 socket 耗盡）
builder.Services.AddHttpClient();

// 使用：建構子注入 IHttpClientFactory，之後 CreateClient() 拿一個乾淨的 HttpClient
var httpClient = _httpClientFactory.CreateClient();
```

`CreateClient()` 回傳全新實例，沒有 BaseAddress / Header 等預設值。
`CreateClient("name")` 回傳預先用 `AddHttpClient("name", c => {...})` 設好的版本。

## DTO 設計

```csharp
// 避免直接暴露 Entity，使用 DTO 作為 API 的資料契約
public record CreateUserDto(string Name, string Email, string Password);
public record UpdateUserDto(string? Name, string? Email);
public record UserDto(int Id, string Name, string Email);  // 不含 Password
```

## JWT 驗證設定

```csharp
// Program.cs
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };
    });
```

## CORS 設定（開發環境）

```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("ReactApp", policy =>
    {
        policy.WithOrigins("http://localhost:5173")  // Vite 預設 port
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});
```

## 常用 Attribute

| Attribute | 說明 |
| --- | --- |
| `[ApiController]` | 自動驗證 ModelState、自動推斷 [FromBody] |
| `[Route("api/[controller]")]` | 路由模板，`[controller]` 替換為 Controller 名稱 |
| `[HttpGet]` / `[HttpPost]` | HTTP 方法 |
| `[FromBody]` | 從 Request Body 綁定 |
| `[FromRoute]` | 從路由參數綁定 |
| `[FromQuery]` | 從 Query String 綁定 |
| `[Authorize]` | 需要認證 |
| `[AllowAnonymous]` | 允許匿名存取 |

## IConfiguration 設定系統

### 資料來源與合併順序

`WebApplication.CreateBuilder(args)` 執行時自動建立，**不需要手動 `AddXxx`**，依序載入以下來源（後面蓋前面）：

| 順序 | 來源 | 說明 |
| --- | --- | --- |
| 1 | `appsettings.json` | 基礎設定 |
| 2 | `appsettings.{Environment}.json` | 環境覆蓋（如 `appsettings.Production.json`） |
| 3 | 環境變數 | K8s Secret、Docker env 等 |
| 4 | 命令列參數 `args` | 最高優先權 |

### 讀取方式

```csharp
// 直接讀 key（冒號分隔巢狀結構）
var key = _configuration["Jwt:Key"];

// Options Pattern（強型別，推薦用於複雜設定）
builder.Services.Configure<JwtOptions>(builder.Configuration.GetSection("Jwt"));
// 之後注入 IOptions<JwtOptions>
```

### appsettings.json 結構

```json
{
  "ConnectionStrings": {
    "Default": "Data Source=..."
  },
  "Jwt": {
    "Key": "your-secret-key",
    "Issuer": "your-api",
    "Audience": "your-frontend",
    "ExpiresInMinutes": "60"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

### 何時注入

`IConfiguration` 在 `WebApplication.CreateBuilder(args)` 時就建好並自動進 DI，**不需要手動 `builder.Services.AddXxx`**。當 DI 容器要建立有 `IConfiguration` 建構子參數的物件時，自動塞進去。

### 不同環境的設定來源

| 環境 | 建議做法 |
| --- | --- |
| 本機開發 | `appsettings.Development.json` 或 User Secrets |
| K8s / Docker | 環境變數（覆蓋 appsettings.json 的同名 key） |
| 生產敏感資料 | K8s Secret → 環境變數 / Vault，**不進版控** |

## Routing

Routing 比對 incoming request 並 dispatch 到對應的 endpoint。

### Route Template 語法

| Template | 說明 |
| --- | --- |
| `{id}` | 必填路由參數 |
| `{id?}` | 可選參數 |
| `{id=1}` | 有預設值的參數 |
| `{**slug}` | Catch-all，匹配所有剩餘路徑 |

### Route Constraints

```csharp
// Minimal API
app.MapGet("/hello/{name:alpha}", (string name) => $"Hello {name}!");

// Controller
[Route("users/{id:int:min(1)}")]
public User GetUserById(int id) { }
```

常用 constraint：`:int`、`:bool`、`:guid`、`:alpha`、`:minlength(N)`、`:maxlength(N)`、`:regex(pattern)`

### Route Groups（Minimal API）

```csharp
app.MapGroup("/api/todos")
    .MapTodosApi()
    .RequireAuthorization();
```

### URL Matching 優先順序

具體路由 > 參數路由；Literal segment > 參數 segment；有 constraint > 無 constraint

### Short-circuit

```csharp
app.MapGet("/fast", () => "Fast!").ShortCircuit();
app.MapShortCircuit(404, "robots.txt", "favicon.ico");
```

## Filters

Filter 讓程式碼在 request pipeline 的特定階段前後執行，處理 cross-cutting concerns。

### Filter Pipeline

```text
Authorization → Resource → Model Binding → Action → Exception → Result → Response
```

### Filter 類型

| 類型 | 時機 | 用途 |
| --- | --- | --- |
| Authorization | 最先 | 驗證授權，可 short-circuit |
| Resource | Authorization 後 | Model binding 前後，適合快取 |
| Action | Action method 前後 | 修改參數或結果 |
| Exception | 未處理例外 | 全域錯誤處理 |
| Result | Action result 執行前後 | 包裝 view/formatter |

### 範例

```csharp
public class SampleActionFilter : IActionFilter
{
    public void OnActionExecuting(ActionExecutingContext context) { }
    public void OnActionExecuted(ActionExecutedContext context) { }
}

// 全域注冊
builder.Services.AddControllersWithViews(options =>
{
    options.Filters.Add<SampleActionFilter>();
});
```

有 DI 需求時用 `ServiceFilterAttribute` 或 `TypeFilterAttribute`；實作 `IOrderedFilter` 可覆蓋執行順序。

## 架構模式

### Clean Architecture

![Clean Architecture Onion](clean-architecture-onion.png)

依賴方向：由外往內（UI / Infrastructure → Application Core），核心不依賴外層。

| 層 | 內容 |
| --- | --- |
| Application Core | Entities、Interfaces、Domain Services、DTOs |
| Infrastructure | EF Core DbContext、Repository、外部服務 |
| UI Layer | Controllers、Middleware、Filters、Program.cs |

ASP.NET Core 完整架構：![Clean Architecture ASP.NET Core](clean-architecture-aspnetcore.png)

### 傳統 N-Layer

```text
UI → BLL → DAL
```

缺點：BLL 依賴 DAL 實作細節，難以單元測試；Clean Architecture 透過 DI + Interface 解決。

### Monolith vs Microservices

| | Monolith | Microservices |
| --- | --- | --- |
| 部署 | 單一 container | 多個獨立服務 |
| Scaling | 整體複製 | 個別服務 scale |
| 複雜度 | 低 | 高 |
| 適合 | 早期 / 小型 | 需獨立 scale 的大型系統 |

## 連結

- [[csharp]] — .NET Web API 使用的語言
- [[react]] — 前端框架，需設定 CORS 對接
- [[docker]] — 部署 Web API 到容器
- [[kubernetes]] — 容器編排，部署後端服務
