---
type: concept
domain: tech
tags: [dotnet, aspnet, error-handling, problemdetails, exception, http-status, result-pattern]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 15 章：錯誤處理 — 什麼錯回什麼碼，以及誰負責接

## 三種都不對的錯誤處理

**第一種：每個 action 自己包 try-catch**

```csharp
[HttpGet("{id}")]
public async Task<IActionResult> GetAsync(int id)
{
    try
    {
        var user = await _userService.GetAsync(id);
        return Ok(user);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "查詢失敗");
        return StatusCode(500, "系統錯誤");
    }
}
```

問題：一百個 action 就是一百份重複的樣板；每個人寫的錯誤格式都不一樣；而且它把**所有**例外都變成 500，包括那些其實應該是 404 或 409 的。

**第二種：完全不處理**

未處理的例外會讓框架回一個 500。在 Development 環境會附上完整的堆疊追蹤與原始碼片段——如果這個設定不小心帶到生產環境，等於把內部結構、檔案路徑、甚至連線字串片段公開出去。

**第三種：全部包成 200**

```csharp
return Ok(new { success = false, message = "找不到使用者" });
```

HTTP 狀態碼變成永遠 200，語意消失。監控系統看到的錯誤率是零；快取層會快取這個「成功」回應；前端必須解析 body 才知道成功與否；重試邏輯無從判斷。

正確的做法有清楚的分層與慣例，這一章要把它建立起來。

---

## 一、分層：誰負責接什麼

```text
┌─ UseExceptionHandler（middleware）──────── 最後防線，接住一切
│   ┌─ Exception Filter ─────────────────── MVC 內特定例外的語意轉換
│   │   ┌─ Service 層 try-catch ─────────── 可以處理並繼續的情況
│   │   │   └─ 業務邏輯
```

原則是：**越靠內層越具體，越靠外層越通用。**

- **Service 層的 try-catch**：只在「我知道怎麼處理並且能繼續」時使用。例如呼叫外部 API 失敗後改用快取的舊資料。單純記個 log 再往上拋不算處理，那只是製造重複的 log。
- **Exception Filter**：把領域例外轉成適當的 HTTP 語意（`InsufficientStockException` → 409）。限制是接不到 model binding 與 result 執行階段的例外（第 05 章）。
- **Exception Handler Middleware**：接住所有漏網之魚，保證任何情況都不會洩漏堆疊，並產生統一格式的回應。

這三層不是三選一，是互補的。

---

## 二、`ProblemDetails`：標準錯誤格式

RFC 7807（已被 RFC 9457 取代但格式相容）定義了 HTTP API 的標準錯誤格式：

```json
{
  "type": "https://example.com/errors/insufficient-stock",
  "title": "庫存不足",
  "status": 409,
  "detail": "商品 ABC 目前庫存 3，需求 10",
  "instance": "/api/orders",
  "traceId": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
}
```

| 欄位 | 意義 |
| --- | --- |
| `type` | 錯誤類型的 URI（可以是文件連結） |
| `title` | 人類可讀的簡短說明，同類型錯誤應該一致 |
| `status` | HTTP 狀態碼 |
| `detail` | 這一次錯誤的具體說明 |
| `instance` | 發生錯誤的資源路徑 |

**用標準格式而不是自創的好處**是實在的：ASP.NET Core 的驗證錯誤（第 04 章）本來就用這個格式、Swagger 能正確產生錯誤 schema、部分前端 HTTP 客戶端有內建處理、跨團隊對接時不用解釋自家格式。

啟用：

```csharp
builder.Services.AddProblemDetails(options =>
{
    options.CustomizeProblemDetails = context =>
    {
        context.ProblemDetails.Instance =
            $"{context.HttpContext.Request.Method} {context.HttpContext.Request.Path}";

        // 加上追蹤識別碼，讓使用者回報問題時能對應到 log
        context.ProblemDetails.Extensions["traceId"] =
            Activity.Current?.Id ?? context.HttpContext.TraceIdentifier;
    };
});
```

`traceId` 非常值得加。使用者截圖回報「出現錯誤」時，有這個 ID 就能在 ELK 裡直接撈出那一次請求的完整 log（第 16 章）。

---

## 三、`IExceptionHandler`（.NET 8+）

.NET 8 引入了比 lambda 更結構化的寫法：

```csharp
public class DomainExceptionHandler : IExceptionHandler
{
    private readonly ILogger<DomainExceptionHandler> _logger;

    public DomainExceptionHandler(ILogger<DomainExceptionHandler> logger)
    {
        _logger = logger;
    }

    public async ValueTask<bool> TryHandleAsync(
        HttpContext context, Exception exception, CancellationToken ct)
    {
        if (exception is not DomainException domainEx)
        {
            return false;          // 不是我負責的，交給下一個 handler
        }

        _logger.LogWarning(domainEx, "業務規則違反：{Code}", domainEx.Code);

        var problem = new ProblemDetails
        {
            Type = $"https://errors.example.com/{domainEx.Code}",
            Title = domainEx.Title,
            Status = StatusCodes.Status422UnprocessableEntity,
            Detail = domainEx.Message
        };

        context.Response.StatusCode = problem.Status.Value;
        await context.Response.WriteAsJsonAsync(problem, ct);

        return true;               // 已處理
    }
}
```

註冊多個，依序嘗試：

```csharp
builder.Services.AddExceptionHandler<DomainExceptionHandler>();
builder.Services.AddExceptionHandler<ConcurrencyExceptionHandler>();
builder.Services.AddExceptionHandler<FallbackExceptionHandler>();   // 最後一個接住其他

builder.Services.AddProblemDetails();

app.UseExceptionHandler();       // 沒有參數，會使用註冊的 handlers
```

回傳 `false` 表示「這個例外不歸我管」，框架繼續問下一個 handler。全部都回 `false` 的話，框架回一個預設的 `ProblemDetails`。

這個模式比一個巨大的 `switch` 好：每種錯誤一個類別、各自可以注入需要的服務、可以單元測試、新增類型不用改既有程式碼。

### 3.1 .NET 6/7 的寫法

```csharp
app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        var feature = context.Features.Get<IExceptionHandlerFeature>();
        var exception = feature?.Error;

        var (status, title) = exception switch
        {
            DomainException => (StatusCodes.Status422UnprocessableEntity, "業務規則違反"),
            KeyNotFoundException => (StatusCodes.Status404NotFound, "找不到資源"),
            DbUpdateConcurrencyException => (StatusCodes.Status409Conflict, "資料已被修改"),
            UnauthorizedAccessException => (StatusCodes.Status403Forbidden, "權限不足"),
            _ => (StatusCodes.Status500InternalServerError, "伺服器錯誤")
        };

        context.Response.StatusCode = status;
        await context.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Title = title,
            Status = status,
            // ⚠️ 只在非 500 時揭露細節
            Detail = status == 500 ? "請聯絡系統管理員" : exception?.Message
        });
    });
});
```

### 3.2 絕對不要洩漏內部細節

```csharp
// ❌ 把例外訊息直接回給客戶端
Detail = exception.Message
```

例外訊息可能包含：資料庫連線字串片段、內部主機名稱、檔案路徑、SQL 語句、其他使用者的資料。這些對攻擊者是有價值的偵察資訊。

原則是：**預期內的錯誤（400/404/409/422）可以給具體訊息；非預期的錯誤（500）只給通用訊息加 traceId。** 細節寫進 log，不寫進回應。

`UseDeveloperExceptionPage()` 會顯示完整堆疊與原始碼，**只能在 Development 環境使用**。範本產生的程式碼有這個判斷，但手動改過 `Program.cs` 之後常常會不小心破壞它。

---

## 四、狀態碼對應

| 情境 | 狀態碼 | 說明 |
| --- | --- | --- |
| 輸入格式錯誤、驗證失敗 | **400** Bad Request | 第 04 章的自動驗證 |
| 未認證、token 無效或過期 | **401** Unauthorized | 第 11 章 |
| 已認證但權限不足 | **403** Forbidden | 第 14 章 |
| 資源不存在 | **404** Not Found | |
| HTTP 方法不支援 | **405** Method Not Allowed | 框架自動 |
| 資源衝突（重複建立、並發修改） | **409** Conflict | 第 09 章 |
| 格式正確但違反業務規則 | **422** Unprocessable Entity | 例如「庫存不足」 |
| 超過流量限制 | **429** Too Many Requests | 第 18 章 |
| 伺服器內部錯誤 | **500** Internal Server Error | 未預期的例外 |
| 下游服務失敗 | **502** Bad Gateway | 呼叫的外部服務掛了 |
| 服務暫時不可用 | **503** Service Unavailable | 維護中、過載 |
| 下游逾時 | **504** Gateway Timeout | |

### 4.1 400 與 422 的界線

這兩個最常被混用。實用的區分是：

- **400**：請求本身有問題——JSON 格式錯誤、缺必填欄位、型別不對。**光看請求就知道錯了。**
- **422**：請求格式完全正確，但業務規則不允許——庫存不足、帳戶餘額不夠、狀態不允許此操作。**需要業務邏輯判斷才知道錯了。**

不強求區分也可以（很多 API 全部用 400），但團隊內要一致。

### 4.2 4xx 與 5xx 的界線

這條線比 400/422 更重要，因為它影響監控與告警：

- **4xx 是客戶端的問題**——不應該觸發告警。使用者輸入錯誤、token 過期，這些都是正常運作的一部分。
- **5xx 是伺服器的問題**——應該告警。它代表系統沒有正確運作。

把「找不到使用者」回成 500，會讓錯誤率指標失真、半夜被叫起來，然後發現只是有人打錯網址。把真正的系統錯誤回成 400，則會讓真實故障被埋沒。

---

## 五、例外的正確用法

### 5.1 不要用例外做控制流程

```csharp
// ❌ 用例外表達「正常的查無資料」
public async Task<User> GetAsync(int id)
{
    var user = await _db.Users.FindAsync(id);
    if (user is null) throw new NotFoundException($"User {id} not found");
    return user;
}
```

「查不到資料」是**預期內**的結果，不是異常。用例外表達它有三個代價：例外的建立與拋出成本遠高於一般回傳（要捕捉堆疊）；用例外做控制流程讓程式難以閱讀；而且在高頻路徑上會成為效能問題。

```csharp
// ✅ 回傳 null 或 Result，由呼叫端決定語意
public async Task<User?> GetAsync(int id) =>
    await _db.Users.FindAsync(id);

// Controller 決定這代表 404
var user = await _userService.GetAsync(id);
if (user is null) return NotFound();
```

**判準：這件事是「預期可能發生」還是「不該發生」？** 前者用回傳值，後者用例外。

### 5.2 領域例外

真正的例外情況值得定義自己的型別：

```csharp
public class DomainException : Exception
{
    public string Code { get; }
    public string Title { get; }

    public DomainException(string code, string title, string message)
        : base(message)
    {
        Code = code;
        Title = title;
    }
}

public class InsufficientStockException : DomainException
{
    public InsufficientStockException(string sku, int available, int requested)
        : base("INSUFFICIENT_STOCK", "庫存不足",
               $"商品 {sku} 目前庫存 {available}，需求 {requested}")
    {
    }
}
```

好處是 handler 可以按型別分派，而且 `Code` 讓前端能做程式化處理（而不是比對中文訊息字串）。

### 5.3 Result Pattern：例外的替代

當「失敗」是常態而非異常時，用回傳值表達更清楚：

```csharp
public readonly record struct Result<T>
{
    public T? Value { get; }
    public string? Error { get; }
    public bool IsSuccess => Error is null;

    private Result(T? value, string? error) { Value = value; Error = error; }

    public static Result<T> Success(T value) => new(value, null);
    public static Result<T> Failure(string error) => new(default, error);
}

public async Task<Result<Order>> PlaceOrderAsync(OrderRequest req, CancellationToken ct)
{
    var stock = await _inventory.GetStockAsync(req.Sku, ct);
    if (stock < req.Quantity)
    {
        return Result<Order>.Failure("INSUFFICIENT_STOCK");
    }
    // ...
    return Result<Order>.Success(order);
}
```

取捨：**明確**（失敗出現在方法簽章上，呼叫端不能忽略）且**沒有例外的效能成本**，但**冗長**（每一層都要傳遞與檢查），且與框架的錯誤處理機制不那麼契合。

務實的建議：業務驗證失敗這類高頻的預期失敗用 Result；真正的異常狀況（資料庫連不上、程式邏輯錯誤）用例外。不要為了「純粹」而全面禁用例外。

---

## 六、記錄策略

不是每個例外都該記成 error。過度記錄會讓真正的問題被淹沒，而告警疲勞比沒有告警更危險。

| 情況 | 層級 | 理由 |
| --- | --- | --- |
| 驗證失敗（400） | Debug 或不記 | 正常的使用者輸入錯誤，量很大 |
| 認證失敗（401） | Information | 有價值（可以偵測暴力破解），但不是錯誤 |
| 權限不足（403） | Warning | 可能是設定錯誤或攻擊嘗試 |
| 找不到資源（404） | Debug | 常態 |
| 業務規則違反（422） | Information | 正常的業務流程分支 |
| 並發衝突（409） | Warning | 頻繁出現代表設計有問題 |
| 未預期的例外（500） | **Error** | 需要有人看 |
| 客戶端取消 | Debug | 第 06 章：不是錯誤 |

客戶端取消特別值得處理，否則流量大時會產生大量假的 error：

```csharp
public async ValueTask<bool> TryHandleAsync(
    HttpContext context, Exception exception, CancellationToken ct)
{
    if (exception is OperationCanceledException
        && context.RequestAborted.IsCancellationRequested)
    {
        _logger.LogDebug("客戶端取消請求 {Path}", context.Request.Path);
        context.Response.StatusCode = 499;      // 非標準但廣泛使用
        return true;
    }
    // ...
}
```

記錄時要帶上足夠的上下文（使用者、資源 ID、traceId），但**不要記錄敏感資料**——密碼、完整的 token、個資。這在 [[16-logging-and-observability]] 展開。

---

## 七、常見誤解

**「所有錯誤都回 200，用 body 裡的欄位表示成功與否。」**
這讓 HTTP 語意消失：監控看不到錯誤率、快取會快取錯誤回應、前端必須解析 body 才知道結果、重試邏輯無從判斷。用狀態碼表達結果。

**「例外訊息直接回給前端比較好除錯。」**
例外訊息可能含連線字串、內部路徑、SQL 語句。500 只回通用訊息加 traceId，細節寫進 log。

**「每個 action 都要包 try-catch。」**
那是一百份重複樣板與一百種格式。用 `UseExceptionHandler` 統一處理，只在「能處理並繼續」時才在內層 catch。

**「Exception Filter 就是全域錯誤處理。」**
它接不到 model binding、result 執行、middleware 層的例外，也不涵蓋非 MVC 端點。最後防線必須是 middleware。

**「查不到資料就丟 `NotFoundException`。」**
查無資料是預期結果不是異常。用 null 或 Result 表達，由 controller 決定它對應 404。例外用於「不該發生」的情況。

**「所有例外都該記成 error。」**
驗證失敗、客戶端取消、找不到資源都是常態。全記成 error 會淹沒真正的問題，也會讓告警失去意義。

---

## 八、同事會來問你的問題

**Q：全域錯誤處理該用 middleware 還是 filter？**
兩個都要。Middleware（`UseExceptionHandler`）是最後防線，保證任何例外都不會洩漏堆疊；filter 或 `IExceptionHandler` 做特定例外的語意轉換。互補而非二選一。

**Q：業務錯誤該回 400 還是 422？**
請求本身有問題（格式、缺欄位）用 400；格式正確但違反業務規則（庫存不足）用 422。團隊內一致即可，全用 400 也不算錯。

**Q：使用者說看到錯誤，怎麼找到對應的 log？**
在 `ProblemDetails` 加上 `traceId`（來自 `Activity.Current?.Id`），前端顯示給使用者。回報時用這個 ID 去 ELK 搜尋，能撈出整條請求鏈的 log。

**Q：log 裡一堆 `OperationCanceledException` error。**
那是客戶端取消或應用程式關機，不是錯誤。在 handler 裡辨識並降級成 debug，回 499。

**Q：可以用 Result pattern 完全取代例外嗎？**
可以但通常不划算。高頻的預期失敗（業務驗證）用 Result 很好；真正的異常（資料庫連不上、程式錯誤）用例外更合適。混用不是不純潔，是務實。

**Q：500 的錯誤率突然上升怎麼查？**
先確認那些是不是真的 5xx——常見狀況是有人把 404 或 409 誤回成 500。確認後用 traceId 在 log 裡找最頻繁的例外型別。這就是 4xx/5xx 分界重要的原因：它直接對應「要不要叫人起床」。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[14-authorization]] — 上一章：401/403 的產生
- [[16-logging-and-observability]] — 下一章：log 與 traceId 的串接
- [[05-filters-and-mvc-internals]] — Exception Filter 的限制
- [[04-model-binding-and-validation]] — 驗證錯誤的 400 格式
- [[09-transactions-and-concurrency]] — 並發衝突回 409
