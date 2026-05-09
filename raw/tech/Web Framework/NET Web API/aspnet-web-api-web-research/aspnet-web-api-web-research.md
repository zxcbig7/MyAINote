# ASP.NET Core Web API — Web Research

來源 URL：
- https://learn.microsoft.com/en-us/aspnet/core/?view=aspnetcore-10.0
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/?view=aspnetcore-10.0
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/?view=aspnetcore-10.0
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/routing?view=aspnetcore-10.0
- https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/filters?view=aspnetcore-10.0
- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures

---

## Middleware Pipeline

>Middleware 是組合到 app pipeline 的軟體，用來處理 request 和 response。
每個 middleware 元件：
- 選擇是否把 request 傳給 pipeline 中的下一個元件
- 可在下一個元件執行前後做工作

Pipeline 圖：

![middleware-pipeline](../assets/aspnet-web-api/middleware-pipeline.png)

### Use / Run / Map

| 方法      | 說明                                                     |
| --------- | -------------------------------------------------------- |
| `Use`     | 鏈接多個 middleware，呼叫 `next.Invoke()` 把控制權往下傳 |
| `Run`     | Terminal middleware，不接收 `next` 參數，會結束 pipeline |
| `Map`     | 依路徑前綴分支 pipeline                                  |
| `MapWhen` | 依任意條件（Predicate）分支 pipeline                     |

```csharp
app.Use(async (context, next) =>
{
    // before
    await next.Invoke(context);
    // after
});

app.Run(async context =>
{
    await context.Response.WriteAsync("Hello world!");
});

app.Map("/map1", HandleMap1);
app.MapWhen(ctx => ctx.Request.Query.ContainsKey("branch"), HandleBranch);
```

### 注意事項
- `Run` 之後的 `Use` 永遠不會執行
- response 開始傳送後不能再修改 header 或 status code
- Exception-handling middleware 要在 pipeline 最前面（才能 catch 後面的例外）

---

## Routing

Routing 負責比對 incoming HTTP request 並 dispatch 到對應的 endpoint。

### Endpoint 概念

Endpoint 是可執行 request-handling 的程式單元，具備：
- `RequestDelegate`（可執行）
- Metadata collection（可延伸）
- Route information（可選擇）

### Route Template 語法

| Template                      | 說明                        |
| ----------------------------- | --------------------------- |
| `hello`                       | 只匹配 `/hello`             |
| `{Page=Home}`                 | 有預設值的參數              |
| `{controller}/{action}/{id?}` | `?` 表示可選參數            |
| `{**slug}`                    | Catch-all，匹配所有剩餘路徑 |

### Route Constraints

```csharp
app.MapGet("/hello/{name:alpha}", (string name) => $"Hello {name}!");

[Route("users/{id:int:min(1)}")]
public User GetUserById(int id) { }
```

常用 constraint：`:int`、`:bool`、`:guid`、`:minlength(4)`、`:maxlength(8)`、`:regex(pattern)`

### Route Groups

```csharp
app.MapGroup("/public/todos")
    .MapTodosApi()
    .WithTags("Public");

app.MapGroup("/private/todos")
    .MapTodosApi()
    .RequireAuthorization();
```

### Short-circuit

```csharp
app.MapGet("/fast", () => "Fast!").ShortCircuit();
app.MapShortCircuit(404, "robots.txt", "favicon.ico");
```

### URL Matching 順序
1. Template Matching
2. Constraint Filtering
3. Policy Filtering（MatcherPolicy）
4. Endpoint Selection（EndpointSelector）

優先順序：具體路由 > 參數路由；Literal segment > 參數 segment；有 constraint > 無 constraint

---

## Filters

Filter 讓程式碼可以在 request processing pipeline 的特定階段前後執行，處理 cross-cutting concerns（授權、快取、錯誤處理、Logging）。

### Filter 類型與執行順序

```
Authorization → Resource → Model Binding → Action → Exception → Result → Response
```

| Filter 類型       | 執行時機               | 用途                                   |
| ----------------- | ---------------------- | -------------------------------------- |
| **Authorization** | 最先                   | 判斷使用者是否有授權，可 short-circuit |
| **Resource**      | Authorization 後       | Model binding 前後執行，適合快取       |
| **Action**        | Action method 前後     | 修改參數或結果（不適用 Razor Pages）   |
| **Exception**     | 未處理例外時           | 全域錯誤處理                           |
| **Result**        | Action result 執行前後 | 包裝 view / formatter 執行             |

### 執行順序（以 Action Filter 為例）

```
1. Global filter OnActionExecuting
2. Controller filter OnActionExecuting
3. Action filter OnActionExecuting
4. Action filter OnActionExecuted
5. Controller filter OnActionExecuted
6. Global filter OnActionExecuted
```

### 程式碼範例

```csharp
// 同步 Filter
public class SampleActionFilter : IActionFilter
{
    public void OnActionExecuting(ActionExecutingContext context) { }
    public void OnActionExecuted(ActionExecutedContext context) { }
}

// 非同步 Filter
public class SampleAsyncActionFilter : IAsyncActionFilter
{
    public async Task OnActionExecutionAsync(
        ActionExecutingContext context, ActionExecutionDelegate next)
    {
        await next();
    }
}

// 自訂 Attribute
public class ResponseHeaderAttribute : ActionFilterAttribute
{
    public override void OnResultExecuting(ResultExecutingContext context)
    {
        context.HttpContext.Response.Headers.Add("X-Custom", "value");
        base.OnResultExecuting(context);
    }
}

// 全域注冊
builder.Services.AddControllersWithViews(options =>
{
    options.Filters.Add<GlobalSampleActionFilter>();
});
```

### 注意事項
- 有 DI 需求的 Filter 用 `ServiceFilterAttribute` 或 `TypeFilterAttribute`
- 實作 `IOrderedFilter` 可覆蓋預設執行順序

---

## 架構模式

### N-Layer（傳統分層）

```
UI → BLL (Business Logic Layer) → DAL (Data Access Layer)
```

缺點：compile-time dependency 從上到下，BLL 依賴 DAL 實作細節，難以單元測試。

### Clean Architecture（Onion Architecture）

圖示：

![clean-architecture-onion](../assets/aspnet-web-api/clean-architecture-onion.png)

ASP.NET Core 對應圖：

![clean-architecture-aspnetcore](../assets/aspnet-web-api/clean-architecture-aspnetcore.png)

依賴方向：由外往內（Infrastructure → Application Core），核心不依賴外層。

| 層                   | 內容                                         |
| -------------------- | -------------------------------------------- |
| **Application Core** | Entities、Interfaces、Domain Services、DTOs  |
| **Infrastructure**   | EF Core DbContext、Repository 實作、外部服務 |
| **UI Layer**         | Controllers、Middleware、Filters、Startup    |

核心優點：Application Core 不依賴 Infrastructure → 容易寫單元測試

### Monolith vs Microservices

|         | Monolith           | Microservices                            |
| ------- | ------------------ | ---------------------------------------- |
| 部署    | 單一 container     | 多個獨立服務                             |
| Scaling | 整體複製           | 個別服務 scale                           |
| 複雜度  | 低                 | 高（需 event bus、eventual consistency） |
| 適合    | 早期開發、小型應用 | 大型、需獨立 scale 的系統                |

---

## 圖片

- `assets/aspnet-web-api/middleware-pipeline.png` — Middleware Pipeline 執行流程圖（Microsoft Learn）
- `assets/aspnet-web-api/clean-architecture-onion.png` — Clean Architecture Onion 視圖（依賴由外往內）
- `assets/aspnet-web-api/clean-architecture-aspnetcore.png` — ASP.NET Core Clean Architecture 完整架構圖
