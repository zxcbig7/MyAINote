---
type: entity
domain: tech
tags: [dotnet, aspnet, csharp, web-api, backend]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-05-03
updated: 2026-05-03
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

```csharp
// Program.cs 的 Pipeline 順序（非常重要）
app.UseHttpsRedirection();
app.UseCors("ReactApp");           // CORS 要在 Auth 前
app.UseAuthentication();           // 先驗證身份
app.UseAuthorization();            // 再驗證權限
app.UseRouting();
app.MapControllers();
```

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

## 連結

- [[csharp]] — .NET Web API 使用的語言
- [[react]] — 前端框架，需設定 CORS 對接
- [[docker]] — 部署 Web API 到容器
