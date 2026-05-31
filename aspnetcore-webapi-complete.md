# ASP.NET Core Web API 完整教學

> 整理自 [practical-aspnetcore](https://github.com/dodyg/practical-aspnetcore) repository

---

## 目錄

1. [最小 API 入門](#1-最小-api-入門)
2. [路由與端點](#2-路由與端點)
3. [參數綁定](#3-參數綁定)
4. [HTTP Methods 與 MapMethods](#4-http-methods-與-mapmethods)
5. [Route Constraints](#5-route-constraints)
6. [Route Groups](#6-route-groups)
7. [Endpoint Filters](#7-endpoint-filters)
8. [Typed Results](#8-typed-results)
9. [Middleware](#9-middleware)
10. [Dependency Injection](#10-dependency-injection)
11. [Configuration 與 Options Pattern](#11-configuration-與-options-pattern)
12. [Health Check](#12-health-check)
13. [Exception Handler](#13-exception-handler)
14. [Problem Details](#14-problem-details)
15. [IHttpClientFactory](#15-ihttpclientfactory)
16. [Memory Cache](#16-memory-cache)
17. [OpenAPI / Scalar](#17-openapi--scalar)
18. [Anti-Forgery](#18-anti-forgery)

---

## 1. 最小 API 入門

### 兩種建立方式

| 方式 | 使用時機 |
|---|---|
| `WebApplication.Create()` | 只需 HTTP pipeline，不需要 DI 設定 |
| `WebApplication.CreateBuilder()` | 需要註冊 service（DI、設定、middleware）|

```csharp
// 最簡版
var app = WebApplication.Create();
app.Run(async context =>
{
    await context.Response.WriteAsync("Hello World");
});
app.Run();

// 有 DI 的版本
var builder = WebApplication.CreateBuilder();
builder.Services.AddSingleton<MyService>();
var app = builder.Build();
app.Run();
```

### 應用啟動方式

```bash
dotnet run
dotnet watch run   # 開發用，檔案變更自動重啟
```

---

## 2. 路由與端點

### MapGet / MapPost / MapPut / MapDelete

```csharp
var app = WebApplication.Create();

app.MapGet("/", () => Results.Json(new { message = "Hello" }));
app.MapPost("/items", (Item item) => Results.Created("/items/1", item));
app.MapPut("/items/{id}", (int id, Item item) => Results.Ok(item));
app.MapDelete("/items/{id}", (int id) => Results.NoContent());

app.Run();
```

### 使用具名函式作為 handler（推薦，方便測試）

```csharp
IResult GetGreeting(string name) => Results.Json(new Person(name));

var app = WebApplication.Create();
app.MapGet("/greet", GetGreeting);
app.Run();

public record Person(string Name);
```

### 讀取 Request Path 與 PathBase

```csharp
app.Map("/hello", (HttpContext ctx) =>
    ctx.Response.WriteAsync($"Path: {ctx.Request.Path} - Base: {ctx.Request.PathBase}"));
```

---

## 3. 參數綁定

### 綁定來源對照表

| 來源 | 方式 | 範例 |
|---|---|---|
| Route | 隱式（型別吻合）/ `[FromRoute]` | `/{id:int}` → `int id` |
| Query String | 隱式（參數名稱吻合）/ `[FromQuery]` | `?name=vic` → `string name` |
| JSON Body | 隱式（複雜型別）/ `[FromBody]` | POST body → `Greeting greet` |
| Header | `[FromHeader]` 明確宣告 | `X-Custom` → `string header` |
| 特殊型別 | 自動注入 | `HttpContext`、`ILogger<T>` 等 |

```csharp
// Route - 隱式
app.MapGet("/{number:int}/{name:alpha}", (int number, string name) =>
    Results.Ok($"Hello {name}, #{number}"));

// Query String - 隱式
app.MapGet("/search", (string keyword, int page) =>
    Results.Ok(new { keyword, page }));

// JSON Body - 隱式（POST + Content-Type: application/json）
app.MapPost("/greet", (Greeting greet) =>
    Results.Json(new { Message = greet.Message + " from server" }));

// JSON Body - 明確宣告
app.MapPost("/greet-explicit", ([FromBody] Greeting greet) =>
    Results.Json(new { greet.Message }));

// Header
app.MapGet("/header", ([FromHeader(Name = "X-Custom-Header")] string value) =>
    Results.Ok(value));
```

### 自訂綁定：BindAsync

```csharp
public class SortOrder
{
    public string Field { get; set; }
    public bool Descending { get; set; }

    public static async ValueTask<SortOrder?> BindAsync(HttpContext context, ParameterInfo parameter)
    {
        var field = context.Request.Query["sort"].FirstOrDefault();
        var desc = context.Request.Query["desc"].FirstOrDefault() == "true";
        return new SortOrder { Field = field, Descending = desc };
    }
}

app.MapGet("/items", (SortOrder sort) => Results.Ok(sort));
```

### 自訂綁定：TryParse

```csharp
public record Point(int X, int Y)
{
    public static bool TryParse(string value, out Point? result)
    {
        var parts = value.Split(',');
        if (parts.Length == 2 && int.TryParse(parts[0], out int x) && int.TryParse(parts[1], out int y))
        {
            result = new Point(x, y);
            return true;
        }
        result = null;
        return false;
    }
}

// /location?point=10,20
app.MapGet("/location", (Point point) => Results.Ok(point));
```

---

## 4. HTTP Methods 與 MapMethods

### MapMethods：一個 endpoint 接受多種 method

```csharp
using Microsoft.AspNetCore.Mvc;

object Greet([FromBody] Greeting greet, HttpContext context)
    => new { Message = context.Request.Method + ": " + greet.Message };

app.MapMethods("/greet", new[] { "POST", "PUT", "PATCH" }, Greet);
```

### 適用時機

- 同一資源的 POST / PUT / PATCH 共用相同邏輯時
- 或需要支援非標準 method 時

---

## 5. Route Constraints

### 內建 Constraints

| Constraint | 說明 | 範例 |
|---|---|---|
| `int` | 整數 | `{id:int}` |
| `alpha` | 只含英文字母 | `{name:alpha}` |
| `decimal` | 小數 | `{price:decimal}` |
| `min(n)` | 最小值 | `{id:min(1)}` |
| `max(n)` | 最大值 | `{id:max(100)}` |
| `range(a,b)` | 範圍 | `{id:range(1,10)}` |
| `guid` | GUID 格式 | `{id:guid}` |
| `length(n)` | 字串長度 | `{code:length(5)}` |

```csharp
app.MapGet("/items/{id:int}", (int id) => Results.Ok(id));
app.MapGet("/items/{id:min(1)}", (int id) => Results.Ok(id));
app.MapGet("/code/{code:alpha:length(5)}", (string code) => Results.Ok(code));
```

### 不符合 constraint 的結果

回傳 404，不是 400。Constraint 的用途是**路由匹配**，不是驗證。

---

## 6. Route Groups

### 基本 Group

```csharp
app.MapGroup("/about").MapAboutApi();

public static class AboutApi
{
    public static RouteGroupBuilder MapAboutApi(this RouteGroupBuilder group)
    {
        group.MapGet("/", () => Results.Ok("about"));
        group.MapGet("/us", () => Results.Ok("Us"));
        group.MapGet("/all", () => Results.Ok("All"));
        return group;
    }
}
```

生成路由：`/about/`、`/about/us`、`/about/all`

### Group 加上 OpenAPI 標籤

```csharp
app.MapGroup("/about")
    .MapAboutApi()
    .WithTags("about_apis")
    .WithDescription("About APIs group");
```

### 適用時機

- 同一前綴下有多個 endpoint（例如 `/api/v1/users`）
- 需要對整個 group 套用共同的 filter、auth、tag

---

## 7. Endpoint Filters

### 單一 Filter（inline lambda）

```csharp
app.MapGet("/", (HttpContext context) => Results.Ok(context.Items["message"]))
   .AddEndpointFilter((context, next) =>
   {
       context.HttpContext.Items["message"] = "hello from filter";
       return next(context);
   });
```

### 多個 Filter（依序執行）

```csharp
app.MapGet("/", (HttpContext context) => Results.Ok(context.Items["message"]))
   .AddEndpointFilter((context, next) =>
   {
       context.HttpContext.Items["message"] = "filter 1";
       return next(context);
   })
   .AddEndpointFilter((context, next) =>
   {
       context.HttpContext.Items["message"] += " filter 2";
       return next(context);
   });
```

執行順序：filter 1 → filter 2 → handler → filter 2 after → filter 1 after（洋蔥模型）

### 適用時機 vs Middleware

| | Endpoint Filter | Middleware |
|---|---|---|
| 作用範圍 | 單一 endpoint 或 group | 全域 pipeline |
| 存取 endpoint metadata | 可以 | 不行 |
| 典型用途 | 驗證、權限、logging per endpoint | 通用 request/response 處理 |

---

## 8. Typed Results

### `Results` vs `TypedResults`

```csharp
// Results：回傳 IResult，難以在 unit test 中驗證型別
IResult handler() => Results.Json(new Person("vic"));

// TypedResults：回傳具體型別，可在測試中直接 Assert
JsonHttpResult<Person> handler() => TypedResults.Json(new Person("vic"));
```

### 單元測試 Typed Results

```csharp
public static class Hello
{
    public static IResult GetGreeting(string name) => TypedResults.Json(new Person(name));
}

// xUnit test
[Fact]
public void TestGetGreeting()
{
    var result = Hello.GetGreeting("vic");
    Assert.IsType<JsonHttpResult<Person>>(result);

    var json = (JsonHttpResult<Person>)result;
    Assert.Equal("vic", json.Value.Name);
}
```

### 常用 TypedResults

| 方法 | HTTP Status | 說明 |
|---|---|---|
| `TypedResults.Ok(value)` | 200 | 成功並回傳資料 |
| `TypedResults.Created(uri, value)` | 201 | 建立資源 |
| `TypedResults.NoContent()` | 204 | 成功無回傳 |
| `TypedResults.BadRequest(error)` | 400 | 請求錯誤 |
| `TypedResults.NotFound()` | 404 | 資源不存在 |
| `TypedResults.Json(value)` | 200 | JSON 回應 |

---

## 9. Middleware

### Middleware Pipeline 概念

```
Request → MW1 → MW2 → MW3 → Handler
         ←      ←      ←
```

每個 middleware 可在 `next()` 前後執行邏輯。

### 三種寫法

```csharp
// Use：傳遞給下一個
app.Use(async (context, next) =>
{
    context.Items["key"] = "value";  // before
    await next(context);
    // after: response 已寫入後執行
});

// Run：終止 pipeline（terminal middleware）
app.Run(async context =>
{
    await context.Response.WriteAsync("End of pipeline");
});

// Map：依 path 分支
app.Map("/hello", branch =>
{
    branch.Run(async context =>
        await context.Response.WriteAsync("Hello branch"));
});

// MapWhen：依條件分支
app.MapWhen(
    ctx => ctx.Request.Path.Value.Contains("/api"),
    branch => branch.Run(ctx => ctx.Response.WriteAsync("API branch"))
);
```

### 注意事項

- `Use` 裡的 `await next()` 之後不能再寫 Response header（已送出）
- Response 只能由一個 middleware 寫入，否則會 exception
- Middleware 的**順序很重要**，越早 `Use` 的越外層

### 自訂 Middleware Class

```csharp
public class RequestTimingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestTimingMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext context)
    {
        var sw = Stopwatch.StartNew();
        await _next(context);
        sw.Stop();
        // 此處已無法寫 header，但可寫 log
    }
}

// 註冊
app.UseMiddleware<RequestTimingMiddleware>();
```

---

## 10. Dependency Injection

### 三種 Lifetime

| Lifetime | 建立時機 | 銷毀時機 |
|---|---|---|
| `Singleton` | App 啟動時（首次使用） | App 關閉 |
| `Scoped` | 每次 HTTP request | Request 結束 |
| `Transient` | 每次從 DI container 取得 | 取得後即可 GC |

```csharp
builder.Services.AddSingleton<SingletonDate>();
builder.Services.AddScoped<ScopedDate>();
builder.Services.AddTransient<TransientDate>();
```

**觀察行為**：同一個 request 內解析兩次 `TransientDate` → 兩個不同實例；`ScopedDate` → 同一實例；`Singleton` → 整個 App 同一實例。

### 工廠式註冊

```csharp
builder.Services.AddSingleton(sp => new MyService(sp.GetRequiredService<ILogger<MyService>>()));
```

### Keyed Service（.NET 8+）

同一 interface 有多個實作，用 key 區分：

```csharp
builder.Services.AddKeyedSingleton<IGreeting, MorningGreeting>("morning");
builder.Services.AddKeyedSingleton<IGreeting, EveningGreeting>("evening");

app.MapGet("/", (IServiceProvider sp) =>
{
    var key = DateTime.Now.Hour < 18 ? "morning" : "evening";
    var greeting = sp.GetRequiredKeyedService<IGreeting>(key);
    return Results.Ok(greeting.Message);
});
```

### Minimal API 中直接注入

```csharp
app.MapGet("/", (IMyService svc, ILogger<Program> logger) =>
{
    logger.LogInformation("Handling request");
    return svc.GetData();
});
```

框架會自動從 DI container 注入已知型別的參數。

---

## 11. Configuration 與 Options Pattern

### 基本 Configuration

```csharp
var app = WebApplication.Create();
app.Configuration["greeting"] = "Hello World";

app.Run(ctx => ctx.Response.WriteAsync(app.Configuration["greeting"]));
```

### 從 appsettings.json 讀取

```json
{
  "AppSettings": {
    "Name": "MyApp",
    "MaxItems": 100
  }
}
```

```csharp
var name = app.Configuration["AppSettings:Name"];
```

### Options Pattern（強型別設定）

```csharp
// 從 DI 設定
builder.Services.Configure<AppOptions>(o =>
{
    o.Name = "MyApp";
    o.MaxItems = 100;
});

// 從 appsettings.json 綁定
builder.Services.Configure<AppOptions>(
    builder.Configuration.GetSection("AppSettings"));

var app = builder.Build();

app.MapGet("/", (IOptions<AppOptions> opts) =>
    Results.Ok(new { opts.Value.Name, opts.Value.MaxItems }));

public class AppOptions
{
    public string Name { get; set; }
    public int MaxItems { get; set; }
}
```

### IOptions 三種介面比較

| 介面 | 特性 |
|---|---|
| `IOptions<T>` | 啟動時讀取，不重新載入 |
| `IOptionsSnapshot<T>` | 每個 request 重新讀取（Scoped） |
| `IOptionsMonitor<T>` | 即時監控變更（Singleton） |

### 環境變數設定

```csharp
// 讀取環境變數
var connString = app.Configuration["DATABASE_URL"];
// 或
var connString = Environment.GetEnvironmentVariable("DATABASE_URL");
```

---

## 12. Health Check

### 基本 Health Check

```csharp
builder.Services.AddHealthChecks();
app.MapHealthChecks("/health");
```

訪問 `/health` → 回傳 `Healthy`（HTTP 200）或 `Unhealthy`（HTTP 503）

### 自訂回應格式

```csharp
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        context.Response.ContentType = "application/json";
        var result = new
        {
            status = report.Status.ToString(),
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                description = e.Value.Description
            })
        };
        await context.Response.WriteAsJsonAsync(result);
    }
});
```

### 自訂 Health Check 邏輯

```csharp
public class DatabaseHealthCheck : IHealthCheck
{
    private readonly IDbConnection _db;
    public DatabaseHealthCheck(IDbConnection db) => _db = db;

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken ct = default)
    {
        try
        {
            await _db.QueryAsync("SELECT 1");
            return HealthCheckResult.Healthy("Database is reachable");
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("Database unreachable", ex);
        }
    }
}

builder.Services.AddHealthChecks()
    .AddCheck<DatabaseHealthCheck>("database");
```

### 多個 Check 並設定 Tag

```csharp
builder.Services.AddHealthChecks()
    .AddCheck<DatabaseHealthCheck>("db", tags: new[] { "database" })
    .AddCheck<CacheHealthCheck>("cache", tags: new[] { "cache" });

// 只跑 database tag 的 check
app.MapHealthChecks("/health/db", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("database")
});
```

### HealthCheckResult 三種狀態

| 狀態 | HTTP Status | 說明 |
|---|---|---|
| `Healthy` | 200 | 服務正常 |
| `Degraded` | 200 | 功能降級，仍可服務 |
| `Unhealthy` | 503 | 服務不可用 |

---

## 13. Exception Handler

### 方式一：UseExceptionHandler（全域）

```csharp
app.UseExceptionHandler("/error");

app.MapGet("/error", (HttpContext context) =>
{
    var feature = context.Features.Get<IExceptionHandlerFeature>();
    return Results.Problem(
        title: "An error occurred",
        detail: feature?.Error.Message
    );
});
```

### 方式二：IExceptionHandler interface（.NET 8+）

```csharp
builder.Services.AddExceptionHandler<DefaultExceptionHandler>();
app.UseExceptionHandler(opt => { });

public class DefaultExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        httpContext.Response.StatusCode = StatusCodes.Status500InternalServerError;
        await httpContext.Response.WriteAsJsonAsync(new
        {
            error = exception.Message,
            path = httpContext.Request.Path.Value
        }, cancellationToken);
        return true;  // true = exception 已處理；false = 繼續找下一個 handler
    }
}
```

### 多個 IExceptionHandler（依序嘗試）

```csharp
builder.Services.AddExceptionHandler<NotFoundExceptionHandler>();
builder.Services.AddExceptionHandler<DefaultExceptionHandler>();
```

第一個回傳 `true` 就停止，`false` 則轉給下一個。

---

## 14. Problem Details

### 什麼是 Problem Details

RFC 9457 定義的標準錯誤回應格式，用於 API 錯誤回應：

```json
{
  "type": "https://tools.ietf.org/html/rfc9457#section-2",
  "title": "An error occurred while processing your request.",
  "status": 500,
  "detail": "We got problems",
  "instance": "/problems"
}
```

### 基本設定

```csharp
builder.Services.AddProblemDetails();
app.UseExceptionHandler();

app.MapGet("/error", () => { throw new ApplicationException("Something broke"); });
```

未處理的 exception → 自動轉為 Problem Details JSON 回應。

### 自訂 Problem Details

```csharp
builder.Services.AddProblemDetails(opts =>
{
    opts.CustomizeProblemDetails = ctx =>
    {
        ctx.ProblemDetails.Extensions["traceId"] = ctx.HttpContext.TraceIdentifier;
        ctx.ProblemDetails.Extensions["timestamp"] = DateTimeOffset.UtcNow;
    };
});
```

### 手動回傳 Problem Details

```csharp
app.MapGet("/items/{id}", (int id) =>
{
    if (id <= 0)
        return Results.Problem(
            title: "Invalid ID",
            detail: "ID must be greater than 0",
            statusCode: 400,
            type: "https://example.com/errors/invalid-id"
        );
    return Results.Ok(new { id });
});
```

---

## 15. IHttpClientFactory

### 為什麼要用 IHttpClientFactory

直接 `new HttpClient()` 的問題：
- socket exhaustion（連線不釋放）
- DNS 不更新（長時間運行的 HttpClient）

`IHttpClientFactory` 管理 HttpClient 的生命週期與 handler pool。

### 方式一：基本工廠模式

```csharp
builder.Services.AddHttpClient();

app.MapGet("/fetch", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var result = await client.GetStringAsync("https://api.example.com/data");
    return Results.Ok(result);
});
```

### 方式二：具名 Client（預設設定）

```csharp
builder.Services.AddHttpClient("github", client =>
{
    client.BaseAddress = new Uri("https://api.github.com");
    client.DefaultRequestHeaders.Add("User-Agent", "MyApp/1.0");
    client.Timeout = TimeSpan.FromSeconds(30);
});

app.MapGet("/repos", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient("github");
    return await client.GetFromJsonAsync<object[]>("/repos/dotnet/aspnetcore");
});
```

### 方式三：Typed Client（最推薦）

```csharp
public class GitHubClient
{
    private readonly HttpClient _client;
    public GitHubClient(HttpClient client) => _client = client;

    public async Task<string[]> GetReposAsync() =>
        await _client.GetFromJsonAsync<string[]>("/orgs/dotnet/repos");
}

builder.Services.AddHttpClient<GitHubClient>(client =>
{
    client.BaseAddress = new Uri("https://api.github.com");
    client.DefaultRequestHeaders.Add("User-Agent", "MyApp");
});

app.MapGet("/repos", async (GitHubClient github) =>
    await github.GetReposAsync());
```

### 方式四：Interface-based Typed Client

```csharp
public interface IGitHubClient
{
    Task<string[]> GetReposAsync();
}

public class GitHubClient : IGitHubClient { /* ... */ }

builder.Services.AddHttpClient<IGitHubClient, GitHubClient>(client => { /* ... */ });
```

---

## 16. Memory Cache

### 基本使用

```csharp
builder.Services.AddMemoryCache();

app.MapGet("/data", (IMemoryCache cache) =>
{
    const string KEY = "my-data";
    if (!cache.TryGetValue(KEY, out string value))
    {
        value = $"Generated at {DateTimeOffset.UtcNow}";
        var options = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(TimeSpan.FromMinutes(5));
        cache.Set(KEY, value, options);
    }
    return Results.Ok(value);
});
```

### 過期策略比較

| 策略 | 說明 | 使用情境 |
|---|---|---|
| `SetAbsoluteExpiration` | 固定時間後過期 | 資料有明確的 TTL |
| `SetSlidingExpiration` | 多久沒存取就過期 | 活躍使用的 session 資料 |
| 兩者並用 | Sliding 但不超過 Absolute | 推薦的安全設定 |

```csharp
var options = new MemoryCacheEntryOptions()
    .SetAbsoluteExpiration(TimeSpan.FromHours(1))
    .SetSlidingExpiration(TimeSpan.FromMinutes(10));
```

### 快取移除事件

```csharp
var options = new MemoryCacheEntryOptions();
options.RegisterPostEvictionCallback((key, value, reason, state) =>
{
    Console.WriteLine($"Cache evicted: {key}, reason: {reason}");
});
```

### Redis 分散式快取

```csharp
builder.Services.AddStackExchangeRedisCache(opts =>
{
    opts.Configuration = "localhost:6379";
});

app.MapGet("/data", async (IDistributedCache cache) =>
{
    var value = await cache.GetStringAsync("key");
    if (value is null)
    {
        value = "cached value";
        await cache.SetStringAsync("key", value, new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10)
        });
    }
    return Results.Ok(value);
});
```

---

## 17. OpenAPI / Scalar

### 設定

```csharp
using Scalar.AspNetCore;

builder.Services.AddOpenApi();
var app = builder.Build();

app.MapOpenApi();               // 提供 /openapi/v1.json
app.MapScalarApiReference();    // 提供 /scalar（互動式 UI）
```

### Scalar 取代 Swagger UI

.NET 9 起官方推薦 Scalar 取代 Swashbuckle。

```bash
dotnet add package Scalar.AspNetCore
```

### 為 endpoint 加上文件

```csharp
/// <summary>
/// Get greeting by name
/// </summary>
public static IResult GetGreeting(
    /// <param name="name">Person's name</param>
    string name) => Results.Ok(new Person(name));

app.MapGet("/greet", Hello.GetGreeting)
   .WithName("GetGreeting")
   .WithSummary("Get a greeting")
   .WithDescription("Returns a personalized greeting")
   .Produces<Person>(200)
   .ProducesProblem(404);
```

### Group 加 Tag

```csharp
app.MapGroup("/api/v1/users")
   .MapUserApi()
   .WithTags("Users")
   .RequireAuthorization();
```

---

## 18. Anti-Forgery

### 用途

防止 CSRF（Cross-Site Request Forgery）攻擊。適用於有 cookie session 的 Minimal API。

### 設定

```csharp
builder.Services.AddAntiforgery();
var app = builder.Build();

// 產生 token 並放入 cookie
app.MapGet("/form", (IAntiforgery antiforgery, HttpContext ctx) =>
{
    var tokens = antiforgery.GetAndStoreTokens(ctx);
    return Results.Content($"""
        <form method="POST" action="/submit">
            <input type="hidden" name="{tokens.FormFieldName}" value="{tokens.RequestToken}" />
            <button type="submit">Submit</button>
        </form>
    """, "text/html");
});

// 驗證 token
app.MapPost("/submit", async (IAntiforgery antiforgery, HttpContext ctx) =>
{
    await antiforgery.ValidateRequestAsync(ctx);
    return Results.Ok("Form submitted");
});
```

### 注意事項

- 純 JSON API（無 cookie session）不需要 Anti-Forgery
- SPA 搭配 JWT 也不需要，因為 JWT 在 Authorization header，不受 CSRF 影響
- 只有「使用 cookie 驗證 + 有表單 POST」的場景才需要

---

## 附錄：常用 Results 回傳方法

```csharp
Results.Ok(data)                        // 200
Results.Created("/resource/1", data)    // 201
Results.Accepted("/status/1", data)     // 202
Results.NoContent()                     // 204
Results.BadRequest(error)               // 400
Results.Unauthorized()                  // 401
Results.Forbid()                        // 403
Results.NotFound()                      // 404
Results.Conflict(data)                  // 409
Results.UnprocessableEntity(data)       // 422
Results.Problem(title, detail, status)  // ProblemDetails
Results.Json(data, options)             // 自訂 JSON 序列化
Results.Text("plain text")             // text/plain
Results.Content(html, "text/html")      // 自訂 content type
Results.File(path, contentType)         // 檔案回應
Results.Redirect("/new-url")           // 302
```

---

## 附錄：Minimal API vs Controller API 比較

| 特性 | Minimal API | Controller API |
|---|---|---|
| 適用版本 | .NET 6+ | 所有版本 |
| 啟動設定 | 極簡 | 需要 `AddControllers()` |
| 路由 | `MapGet`、`MapPost` 等 | `[HttpGet]`、`[Route]` attribute |
| 程式碼量 | 少 | 多（class + method） |
| 測試性 | 需用 `TypedResults` | 容易 unit test |
| 適合場景 | Microservice、小 API | 大型應用、複雜路由邏輯 |
| Middleware | 相同 | 相同 |
| DI | 相同 | 相同 |
