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

```csharp
// 三種 Lifetime
builder.Services.AddSingleton<IMyService, MyService>();   // 整個應用共用一個實例
builder.Services.AddScoped<IUserService, UserService>();   // 每個 HTTP Request 一個實例
builder.Services.AddTransient<IEmailService, EmailService>(); // 每次注入一個新實例
```

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

## appsettings.json

```json
{
  "ConnectionStrings": {
    "Default": "Data Source=..."
  },
  "Jwt": {
    "Key": "your-secret-key",
    "Issuer": "your-api",
    "Audience": "your-frontend"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

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
