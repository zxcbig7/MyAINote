---
type: concept
domain: tech
tags: [dotnet, aspnet, filters, mvc, actionresult, content-negotiation, endpoint-filter]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 05 章：Filter 與 MVC 內部 — 橫切關注點該放哪一層

## 同一個需求，兩種做法

需求：**每個 API 呼叫都要寫一筆稽核記錄，內容包含操作者、目標資源、以及送進來的參數。**

用 middleware 做：

```csharp
app.Use(async (ctx, next) =>
{
    await next();
    // 想記錄「送進來的參數」→ 只能自己重新讀 body、自己解析 JSON
    // 想記錄「操作了哪個資源」→ 只有 URL 字串，得自己反推
});
```

用 filter 做：

```csharp
public class AuditFilter : IAsyncActionFilter
{
    public async Task OnActionExecutionAsync(
        ActionExecutingContext context, ActionExecutionDelegate next)
    {
        var actionName = context.ActionDescriptor.DisplayName;
        var args = context.ActionArguments;        // 已經綁定好、驗證過的參數物件
        var user = context.HttpContext.User;

        var result = await next();

        // result.Result 是 action 回傳的 IActionResult，看得到成功或失敗
    }
}
```

差別一目了然：**filter 拿得到 MVC 的上下文**。已綁定的參數物件、action 的識別、`ModelState`、回傳的 `IActionResult`——這些在 middleware 層全部不存在，因為 middleware 執行時 model binding 還沒發生（進去時）或已經結束（回來時）。

這一章要講的就是 middleware 之內、action 之外的那一層：MVC 到底怎麼執行一個 action，以及五種 filter 各自卡在哪個位置。

---

## 一、Endpoint 被選中之後

第 03 章結束在「`UseRouting` 選出了 endpoint」。當 pipeline 走到 `MapControllers()` 那一層，MVC 接手，執行的流程是：

```text
1. 建立 Controller 實例（從 request scope 解析建構子依賴）
2. Authorization Filter
3. Resource Filter（前段）
4. Model Binding + Validation           ← 第 04 章的內容
5. Action Filter（前段）
6. 執行 Action 方法
7. Action Filter（後段）
   └─ 若有例外未處理 → Exception Filter
8. Result Filter（前段）
9. 執行 IActionResult（序列化、寫 response）
10. Result Filter（後段）
11. Resource Filter（後段）
```

幾個位置關係值得特別注意：

**Authorization 在最前面，比 model binding 更早。** 這是刻意的——沒有權限的請求不該浪費資源去解析 body。所以授權邏輯拿不到綁定後的參數，只能看 URL、header 和 claims。需要「根據資料內容決定權限」（例如「只能改自己的訂單」）就不能用 authorization filter，得用 resource-based authorization，見 [[14-authorization]]。

**Resource Filter 包住 model binding。** 這是唯一能在「參數解析之前」介入、又在「回應寫完之後」收尾的位置。回應快取就是靠它——快取命中時直接短路，連 body 都不用讀。

**Exception Filter 只包住 action 與 action filter。** 它接不到 model binding 的錯誤、接不到 result 執行時的例外（例如序列化失敗）、更接不到 middleware 的例外。這個限制是實務上選擇「用 exception filter 還是用 exception middleware」的關鍵，第五節會展開。

---

## 二、五種 Filter

| 類型 | 介面 | 位置 | 典型用途 |
| --- | --- | --- | --- |
| Authorization | `IAuthorizationFilter` / `IAsyncAuthorizationFilter` | 最先 | 權限檢查（通常用內建的就好） |
| Resource | `IResourceFilter` / `IAsyncResourceFilter` | 包住 binding 與整個執行 | 快取、短路、限流 |
| Action | `IActionFilter` / `IAsyncActionFilter` | 包住 action 方法 | 稽核、參數改寫、交易邊界 |
| Exception | `IExceptionFilter` / `IAsyncExceptionFilter` | action 拋例外時 | 特定例外轉換 |
| Result | `IResultFilter` / `IAsyncResultFilter` | 包住 result 執行 | 統一包裝回應、加 header |

### 2.1 同步與非同步不要同時實作

每種 filter 都有同步與非同步兩個版本。**同時實作兩個時，框架只會呼叫非同步版本**，同步版本靜靜地不執行。這是很難察覺的 bug——程式碼在那裡，看起來會跑，實際上不會。

原則：**一律用非同步版本**（`IAsync*Filter`）。即使目前邏輯是同步的，非同步版本也能正確表達，而且未來要加 `await` 時不用改介面。

非同步版本的形態是「一個方法 + 一個 `next` 委派」，和 middleware 是同一個模式：

```csharp
public async Task OnActionExecutionAsync(
    ActionExecutingContext context, ActionExecutionDelegate next)
{
    // 前段
    var executed = await next();      // 執行 action（以及更內層的 filter）
    // 後段，executed.Result 是 action 的回傳值
}
```

而同步版本是兩個獨立方法（`OnActionExecuting` / `OnActionExecuted`），無法用區域變數在前後段之間傳遞狀態——想量測耗時就得把 `Stopwatch` 塞進 `HttpContext.Items`。這是偏好非同步版本的另一個理由。

### 2.2 短路

在前段設定 `context.Result`，就會跳過後續執行直接進入 result 階段：

```csharp
public class MaintenanceModeFilter : IAsyncResourceFilter
{
    public async Task OnResourceExecutionAsync(
        ResourceExecutingContext context, ResourceExecutionDelegate next)
    {
        if (IsUnderMaintenance())
        {
            context.Result = new ObjectResult(new { message = "系統維護中" })
            {
                StatusCode = StatusCodes.Status503ServiceUnavailable
            };
            return;                    // 不呼叫 next()，action 完全不執行
        }

        await next();
    }
}
```

第 04 章提到的「自動 400」就是這個機制的內建實例：`ModelStateInvalidFilter` 是一個 action filter，在前段發現 `ModelState` 無效就設定 `context.Result` 為 `BadRequestObjectResult` 並短路。

---

## 三、Filter 的作用範圍與執行順序

同一個 filter 可以套在三個層級：

```csharp
// 全域
builder.Services.AddControllers(options =>
{
    options.Filters.Add<AuditFilter>();
});

// Controller
[ServiceFilter(typeof(AuditFilter))]
public class UsersController : ControllerBase

// Action
[ServiceFilter(typeof(AuditFilter))]
public IActionResult Get()
```

預設順序是 **Global → Controller → Action**（前段），後段則相反（Action → Controller → Global）。同樣是洋蔥，範圍越大的包在越外面。

要覆蓋這個順序，實作 `IOrderedFilter`：

```csharp
public class AuditFilter : IAsyncActionFilter, IOrderedFilter
{
    public int Order => -1;    // 數字小的先執行（前段）
}
```

排序規則是：**先比 `Order`（小的先），`Order` 相同才比範圍（Global → Controller → Action）**。所以一個 `Order = -1` 的 action filter 會跑在 `Order = 0` 的 global filter 前面。

實務上 `Order` 用得越少越好。它讓執行順序依賴散落各處的數字，難以從程式碼一眼看出全貌。真的需要時（例如交易 filter 必須包在稽核 filter 外面），要在註解裡寫清楚為什麼。

---

## 四、Filter 與 DI：三種註冊方式

Filter 也有和 middleware 類似的生命週期問題，但解法不同。

### 4.1 直接用 Attribute（不能有 DI）

```csharp
public class SimpleLogAttribute : ActionFilterAttribute
{
    public override void OnActionExecuting(ActionExecutingContext context)
    {
        Debug.WriteLine($"執行 {context.ActionDescriptor.DisplayName}");
    }
}

[SimpleLog]
public IActionResult Get() => Ok();
```

Attribute 的實例由 CLR 在載入 metadata 時建立，**不經過 DI**，所以建構子不能有服務依賴。只能透過 attribute 的建構子傳入常數。

需要服務時，可以從 `context.HttpContext.RequestServices` 拿——但那是 Service Locator（第 02 章的反模式），只在 attribute 這個受限場景下勉強可接受。更好的做法是下面兩種。

### 4.2 `ServiceFilter`：從 DI 解析

```csharp
public class AuditFilter : IAsyncActionFilter
{
    private readonly IAuditService _audit;      // 建構子注入，正常運作

    public AuditFilter(IAuditService audit) { _audit = audit; }
    // ...
}

builder.Services.AddScoped<AuditFilter>();      // 必須註冊

[ServiceFilter(typeof(AuditFilter))]
public IActionResult Get() => Ok();
```

`ServiceFilter` 從 DI 容器解析實例，所以生命週期由你註冊時決定。註冊成 Scoped 就每個 request 一個，可以安全地注入 DbContext。忘記註冊會在執行期拋錯。

### 4.3 `TypeFilter`：DI 解析 + 額外建構子參數

```csharp
[TypeFilter(typeof(AuditFilter), Arguments = new object[] { "UserModule" })]
```

`TypeFilter` 不要求 filter 本身註冊在 DI，它用 `ActivatorUtilities` 建立實例——服務參數從 DI 拿，其餘從 `Arguments` 拿。適合需要「同一個 filter 帶不同參數用在不同 action」的情況。

代價是每次都建立新實例（除非設 `IsReusable = true`，但那會讓它變成事實上的 Singleton，又回到 captive dependency 的風險）。

| | Attribute | ServiceFilter | TypeFilter |
| --- | --- | --- | --- |
| 建構子 DI | ✗ | ✓ | ✓ |
| 需註冊到 DI | ✗ | ✓ | ✗ |
| 可傳自訂參數 | ✓（常數） | ✗ | ✓ |
| 生命週期 | 隨 attribute | 由註冊決定 | 每次新建 |

---

## 五、每種 Filter 的實際用途

### 5.1 Resource Filter：快取與短路

它的獨特價值是位置——包住 model binding。回應快取命中時可以連 body 都不解析：

```csharp
public class CacheResponseFilter : IAsyncResourceFilter
{
    private readonly IMemoryCache _cache;

    public CacheResponseFilter(IMemoryCache cache) { _cache = cache; }

    public async Task OnResourceExecutionAsync(
        ResourceExecutingContext context, ResourceExecutionDelegate next)
    {
        var key = context.HttpContext.Request.Path.ToString();

        if (_cache.TryGetValue<IActionResult>(key, out var cached))
        {
            context.Result = cached;        // 短路，action 不執行
            return;
        }

        var executed = await next();

        if (executed.Result is OkObjectResult ok)
        {
            _cache.Set(key, ok, TimeSpan.FromMinutes(1));
        }
    }
}
```

（實際的快取要考慮 query string、使用者身分、Vary header 等，這裡只示範位置的價值。生產級的回應快取建議用內建的 Output Caching，見 [[18-resilience-and-performance]]。）

### 5.2 Action Filter：交易邊界

一個經典用法是把「開交易、成功則提交、失敗則回滾」抽成 filter：

```csharp
public class TransactionFilter : IAsyncActionFilter
{
    private readonly AppDbContext _db;

    public TransactionFilter(AppDbContext db) { _db = db; }

    public async Task OnActionExecutionAsync(
        ActionExecutingContext context, ActionExecutionDelegate next)
    {
        await using var tx = await _db.Database.BeginTransactionAsync();

        var executed = await next();

        if (executed.Exception is null && IsSuccessResult(executed.Result))
        {
            await tx.CommitAsync();
        }
        else
        {
            await tx.RollbackAsync();
        }
    }
}
```

這個做法有支持者也有反對者。支持的理由是消除每個 action 裡重複的交易樣板；反對的理由是**交易邊界是業務決策，藏在 filter 裡會讓人看不見它**，而且 filter 無法表達「這個 action 需要兩段獨立交易」這類需求。

我的建議是：簡單的 CRUD 用 filter 統一處理可以接受；一旦業務出現「部分成功」「補償」「跨服務」的語意，就把交易明確寫在 service 層。詳見 [[09-transactions-and-concurrency]]。

### 5.3 Exception Filter：它的限制比用途更重要

```csharp
public class DomainExceptionFilter : IAsyncExceptionFilter
{
    public Task OnExceptionAsync(ExceptionContext context)
    {
        if (context.Exception is DomainException ex)
        {
            context.Result = new ObjectResult(new ProblemDetails
            {
                Title = "業務規則違反",
                Detail = ex.Message,
                Status = StatusCodes.Status422UnprocessableEntity
            })
            { StatusCode = StatusCodes.Status422UnprocessableEntity };

            context.ExceptionHandled = true;    // 標記已處理，否則會繼續往上拋
        }
        return Task.CompletedTask;
    }
}
```

限制清單：

- 只捕捉 **action 方法與 action filter** 裡的例外
- **接不到** model binding 階段的例外
- **接不到** result 執行階段的例外（JSON 序列化失敗、串流寫入失敗）
- **接不到** middleware 或 filter 之外任何地方的例外
- 只作用於走進 MVC 的請求（靜態檔案、健康檢查端點不經過）

所以它不能作為「全域錯誤處理」的唯一機制。正確的分層是：

```text
UseExceptionHandler middleware  ← 最後防線，接住一切
    └── Exception Filter        ← 針對 MVC 內部特定例外做語意轉換
```

Middleware 負責「不讓任何例外洩漏成未處理的 500 與堆疊追蹤」，filter 負責「把 `DomainException` 轉成 422 這種業務語意」。兩者互補而非二選一。完整策略在 [[15-error-handling]]。

### 5.4 Result Filter：統一回應格式

```csharp
public class EnvelopeResultFilter : IAsyncResultFilter
{
    public async Task OnResultExecutionAsync(
        ResultExecutingContext context, ResultExecutionDelegate next)
    {
        if (context.Result is OkObjectResult ok)
        {
            context.Result = new OkObjectResult(new
            {
                success = true,
                data = ok.Value,
                timestamp = DateTimeOffset.UtcNow
            });
        }

        await next();
    }
}
```

「把所有回應包一層 envelope」是很多團隊的既有慣例。技術上可行，但值得提醒：**這會讓 API 偏離 HTTP 語意**——狀態碼已經表達了成功與否，再包一層 `success: true` 是重複資訊，而且會讓 Swagger 產生的型別描述失真（描述的是 `data` 的型別，實際回的是外層物件）。

如果是新專案，優先考慮直接用 HTTP 語意 + `ProblemDetails`。如果是要對接既有前端契約，那就用 result filter 統一處理，至少比每個 action 手動包一層好。

---

## 六、`IActionResult` 與內容協商

Action 回傳的東西有三種形態：

```csharp
public IActionResult A() => Ok(dto);                    // 只有型別資訊：IActionResult
public ActionResult<UserDto> B() => Ok(dto);            // 有型別，Swagger 能推斷
public UserDto C() => dto;                              // 直接回物件，框架自動包成 200
```

`ActionResult<T>` 是推薦寫法：它同時允許回傳 `T`（隱含 200）和各種 `IActionResult`（`NotFound()`、`BadRequest()`），而且型別資訊保留給 Swagger 與 API 分析器。

`IActionResult` 的執行發生在流程的第 9 步。以 `ObjectResult` 為例，它會走**內容協商（content negotiation）**：

```text
1. 讀 request 的 Accept header
2. 從註冊的 output formatter 中挑一個能產生該格式的
3. 用它把物件序列化寫入 response body
```

預設只註冊了 JSON formatter，所以無論 `Accept` 寫什麼，回的都是 JSON（找不到匹配時退回第一個 formatter）。要支援 XML 得明確加：

```csharp
builder.Services.AddControllers()
    .AddXmlSerializerFormatters();
```

加了之後，`Accept: application/xml` 就會回 XML。要嚴格一點——不支援的格式直接回 406 而不是硬給 JSON：

```csharp
builder.Services.AddControllers(options =>
{
    options.ReturnHttpNotAcceptable = true;
});
```

多數內部 API 不需要內容協商（只講 JSON）。但理解這個機制有助於解釋「為什麼我設了 `Accept: text/csv` 還是回 JSON」這類問題。

`Results` / `TypedResults`（Minimal API 用）是另一套 API，語意相同但不走 MVC 的 formatter 選擇邏輯，直接寫 JSON。`TypedResults` 比 `Results` 多了強型別回傳值，對測試和 OpenAPI 產生更友善。

---

## 七、Minimal API 的 Endpoint Filter（.NET 7+）

Minimal API 沒有五種 filter，但有一個統一的 endpoint filter：

```csharp
app.MapPost("/users", CreateUser)
   .AddEndpointFilter(async (context, next) =>
   {
       var dto = context.GetArgument<CreateUserDto>(0);

       if (string.IsNullOrWhiteSpace(dto.Name))
       {
           return Results.ValidationProblem(new Dictionary<string, string[]>
           {
               ["Name"] = new[] { "姓名為必填" }
           });
       }

       return await next(context);
   });
```

它的位置相當於 MVC 的 action filter——在參數綁定之後、handler 執行之前。可以讀取與修改參數（`context.Arguments`），可以短路。

因為 Minimal API 沒有內建的 `ModelState` 驗證（第 04 章），endpoint filter 是補上驗證的標準做法。可以寫成泛型的可重用版本：

```csharp
public class ValidationFilter<T> : IEndpointFilter where T : class
{
    private readonly IValidator<T> _validator;

    public ValidationFilter(IValidator<T> validator) { _validator = validator; }

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context, EndpointFilterDelegate next)
    {
        var arg = context.Arguments.OfType<T>().FirstOrDefault();
        if (arg is not null)
        {
            var result = await _validator.ValidateAsync(arg);
            if (!result.IsValid)
            {
                return Results.ValidationProblem(result.ToDictionary());
            }
        }

        return await next(context);
    }
}

app.MapPost("/users", CreateUser).AddEndpointFilter<ValidationFilter<CreateUserDto>>();
```

搭配 `MapGroup` 可以一次套用到整組 endpoint。

---

## 八、常見誤解

**「Filter 和 middleware 差不多，選哪個都行。」**
層級不同。Middleware 涵蓋所有請求但看不到 MVC 上下文；Filter 只作用於 MVC 請求但拿得到參數、`ModelState`、`IActionResult`。需要 action 資訊就必須用 filter。

**「Exception Filter 可以當全域錯誤處理。」**
它接不到 model binding、result 執行、middleware 層的例外，也不涵蓋非 MVC 的端點。全域最後防線必須是 `UseExceptionHandler` middleware，filter 只做特定例外的語意轉換。

**「同時實作同步和非同步版本比較保險。」**
框架只會呼叫非同步版本，同步版本靜靜不執行。一律只實作非同步版本。

**「Filter 上的 attribute 可以注入服務。」**
純 attribute 不經過 DI，建構子不能有服務依賴。要 DI 就用 `[ServiceFilter]` 或 `[TypeFilter]`。

**「Authorization filter 可以檢查『使用者只能改自己的資料』。」**
不行，它跑在 model binding 之前，拿不到請求內容也還沒查資料庫。這種需求要用 resource-based authorization，在 action 或 service 層做，見 [[14-authorization]]。

**「回傳 `IActionResult` 和 `ActionResult<T>` 沒差。」**
`ActionResult<T>` 保留型別資訊，Swagger 能正確產生回應 schema，API 分析器也能檢查。優先用它。

---

## 九、同事會來問你的問題

**Q：這個橫切需求該用 middleware 還是 filter？**
問一句：它需不需要知道「綁定後的參數」「是哪個 action」「ModelState」「回傳的 IActionResult」。需要就是 filter；需要涵蓋靜態檔案、健康檢查等非 MVC 請求就是 middleware。

**Q：我寫的 Exception Filter 沒有接到錯誤。**
確認例外是不是發生在 action 之外——model binding 失敗、JSON 序列化失敗（result 執行階段）、或是 middleware 拋的。這三種 exception filter 都接不到，要靠 `UseExceptionHandler`。

**Q：`[ServiceFilter]` 說找不到服務。**
`ServiceFilter` 要求 filter 型別本身註冊在 DI 裡。加上 `builder.Services.AddScoped<AuditFilter>()`。或者改用 `[TypeFilter]`，它不需要註冊。

**Q：Filter 的執行順序怎麼決定？我兩個 filter 順序不如預期。**
先比 `IOrderedFilter.Order`（小的先），相同時才按 Global → Controller → Action 排。後段順序相反。真的需要精確控制就實作 `IOrderedFilter` 並註解說明理由。

**Q：想在 filter 裡用 `DbContext`，可以嗎？**
可以，但要用 `[ServiceFilter]` 並把 filter 註冊成 Scoped。純 attribute 或 `IsReusable = true` 的 `TypeFilter` 會變成長生命週期，把 DbContext 俘虜（第 02 章）。

**Q：Minimal API 怎麼做參數驗證？**
沒有內建的。用 `AddEndpointFilter` 寫一個泛型驗證 filter，搭配 FluentValidation，再用 `MapGroup` 一次套用到整組 endpoint。

**Q：為什麼 `Accept: application/xml` 還是回 JSON？**
預設只註冊 JSON formatter，找不到匹配的 formatter 時會退回第一個。要支援 XML 得呼叫 `AddXmlSerializerFormatters()`；要讓不支援的格式回 406 就設 `ReturnHttpNotAcceptable = true`。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[04-model-binding-and-validation]] — 上一章：filter 前後的綁定與驗證
- [[06-async-and-threading]] — 下一章：async 在這些管線裡的真實行為
- [[01-request-pipeline]] — middleware 層與 filter 層的分工
- [[15-error-handling]] — exception filter 與 exception middleware 的分層
- [[14-authorization]] — resource-based authorization
