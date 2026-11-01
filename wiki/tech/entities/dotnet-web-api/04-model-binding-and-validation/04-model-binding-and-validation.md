---
type: concept
domain: tech
tags: [dotnet, aspnet, model-binding, validation, dataannotations, system-text-json, problemdetails]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 04 章：Model Binding 與驗證 — 參數是怎麼被填進去的

## 為什麼參數是 null

`dto` 是 null，或者 `dto` 不是 null 但裡面每個屬性都是預設值。這大概是 ASP.NET Core 開發最常遇到、也最讓人抓狂的問題，因為前端明明送了資料，後端 log 印出來卻是空的。

它至少有六種成因，而且症狀幾乎一樣：

1. 前端沒有送 `Content-Type: application/json`
2. JSON 的屬性名稱與 DTO 對不上（大小寫、底線）
3. DTO 用了 `record` 或 init-only 屬性，但序列化器找不到合適的建構子
4. 有 middleware 先把 request body 讀掉了（第 01 章）
5. 參數被推斷成從 query string 綁定，而不是 body
6. 一個 action 有兩個複雜型別參數，框架只綁定得了一個

要能在三十秒內分辨是哪一種，就得知道 model binding 實際上做了什麼。

---

## 一、Binding Source：資料從哪來

Model binding 的第一個問題永遠是「這個參數的值要去哪裡找」。ASP.NET Core 定義了六個來源：

| Attribute | 來源 | 典型用途 |
| --- | --- | --- |
| `[FromRoute]` | 路由模板的參數 | `/users/{id}` 的 `id` |
| `[FromQuery]` | Query string | `?page=2&size=20` |
| `[FromBody]` | Request body（反序列化） | POST/PUT 的 JSON |
| `[FromForm]` | 表單資料（`multipart/form-data`） | 檔案上傳 |
| `[FromHeader]` | Request header | `X-Tenant-Id` |
| `[FromServices]` | DI 容器 | 直接注入服務到 action |

明確標注永遠是安全的。問題出在**不標注時的推斷規則**。

### 1.1 `[ApiController]` 的推斷規則

有 `[ApiController]` 時，框架按這個順序推斷：

```text
1. 參數名稱與路由模板中的參數同名 → [FromRoute]
2. 型別是「簡單型別」（string、int、DateTime、Guid、enum，以及可轉換的型別）→ [FromQuery]
3. 型別註冊在 DI 容器裡 → [FromServices]
4. 其他（複雜型別）→ [FromBody]
5. IFormFile / IFormFileCollection → [FromForm]
```

這解釋了成因 5。看這個 action：

```csharp
[HttpGet]
public IActionResult Search(SearchFilter filter)   // filter 有 Keyword、Page、Size 屬性
```

`SearchFilter` 是複雜型別 → 推斷成 `[FromBody]`。但 GET 請求通常沒有 body，前端送的是 `?keyword=abc&page=1`，於是 `filter` 是 null。

修正是明確標注：

```csharp
[HttpGet]
public IActionResult Search([FromQuery] SearchFilter filter)
```

`[FromQuery]` 套在複雜型別上時，框架會**逐屬性**去 query string 找同名的值。這是很好用但很少人知道的功能——它讓「一大包查詢條件」可以用一個型別表達，而不是十個平鋪的參數。

### 1.2 一個 action 只能有一個 `[FromBody]`

成因 6 的答案。Request body 是一個只能讀一次的串流，反序列化會把它整個消耗掉。所以框架限制：**一個 action 最多一個 `[FromBody]` 參數**。

```csharp
// ❌ 執行期拋例外
public IActionResult Create([FromBody] UserDto user, [FromBody] AddressDto address)
```

需要傳兩個物件，就包成一個：

```csharp
public record CreateUserRequest(UserDto User, AddressDto Address);

public IActionResult Create([FromBody] CreateUserRequest request)
```

### 1.3 沒有 `[ApiController]` 會怎樣

推斷規則完全不同：**複雜型別預設從 query/form 綁定，而不是 body**。這是 MVC（回傳 View 的那種）的傳統行為，因為表單提交是主流。

所以少寫一個 `[ApiController]`，POST 進來的 JSON 就完全不會被綁定，所有屬性都是預設值。這是成因清單裡最容易被忽略的一項，因為程式碼看起來毫無問題。

---

## 二、JSON 反序列化的坑

`[FromBody]` 的實際工作是把 body 交給 `System.Text.Json`（.NET Core 3.0 起取代 Newtonsoft.Json 成為預設）。這一層有幾個必須知道的行為。

### 2.1 屬性名稱比對

預設是**大小寫不敏感**的（`PropertyNameCaseInsensitive = true` 是 ASP.NET Core 的預設，注意這和直接使用 `JsonSerializer` 的預設不同）。所以 `{"userName": "x"}` 能綁到 `public string UserName { get; set; }`。

但底線不會被處理。`{"user_name": "x"}` 綁不到 `UserName`。遇到 snake_case 的外部 API 時要明確設定：

```csharp
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;   // .NET 8+
});

// Controller 用的是另一組設定
builder.Services.AddControllers().AddJsonOptions(options =>
{
    options.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
});
```

注意這裡有兩組設定：`AddJsonOptions` 給 MVC/Controller 用，`ConfigureHttpJsonOptions` 給 Minimal API 用。設錯地方是常見的「明明設了卻沒生效」原因。

單一屬性可以用 attribute 覆蓋：

```csharp
public class UserDto
{
    [JsonPropertyName("user_name")]
    public string UserName { get; set; } = string.Empty;
}
```

### 2.2 `record` 與 init-only 屬性

```csharp
public record CreateUserDto(string Name, string Email);
```

這個寫法很受歡迎（簡潔、不可變、值相等），但它產生的是一個**只有帶參數建構子、屬性是 init-only** 的型別。`System.Text.Json` 從 .NET 5 起支援用參數化建構子反序列化，條件是：**只有一個公開建構子，或用 `[JsonConstructor]` 明確標注**。

```csharp
// ❌ 兩個建構子，序列化器不知道用哪個
public record CreateUserDto(string Name, string Email)
{
    public CreateUserDto(string name) : this(name, "") { }
}

// ✅ 明確指定
[JsonConstructor]
public CreateUserDto(string Name, string Email) { ... }
```

還有一個細節：建構子參數名稱與 JSON 屬性的比對**也是大小寫不敏感**的，但如果用了 `JsonPropertyName` 改名，要確保建構子參數能對應上。

### 2.3 Nullable Reference Types 造成的意外 400

這是 .NET 6 之後新專案最常見的困惑之一，而且錯誤訊息完全不指向真正的原因。

專案範本預設開啟 `<Nullable>enable</Nullable>`。在這個模式下：

```csharp
public class CreateUserDto
{
    public string Name { get; set; }   // 不可為 null，沒有初始值
    public string? Nickname { get; set; }   // 可為 null
}
```

`Name` 是不可為 null 的參考型別。ASP.NET Core 的驗證系統會**自動把它視為 `[Required]`**。於是前端送 `{"nickname": "x"}` 沒帶 `name`，`Name` 維持預設值 `null`，得到的是 400 加上「The Name field is required.」——即使你從來沒寫過 `[Required]`。（編譯器會對這個沒有初始值的屬性發出 CS8618 警告，這也是不少人順手補上 `= string.Empty` 的原因。）

這裡有個容易誤會的細節：隱含的必填檢查只在**值為 `null`** 時才觸發。如果寫成 `public string Name { get; set; } = string.Empty;`，沒帶 `name` 時屬性保有初始值 `""`，不是 `null`，驗證通過，action 會收到空字串而不是 400。實測也是如此，回應 body 是 `{"name":""}`。所以 `= string.Empty` 等於悄悄關掉了「缺欄位就 400」的保護，需要擋空值時要另外加 `[Required]`（它會連空字串一起擋）或 `[MinLength]`。

隱含必填通常正是你要的行為（不可為 null 就是必填，語意一致）。問題出在它跟另一個場景衝突：**PATCH 式的部分更新**。

```csharp
public class UpdateUserDto
{
    public string Name { get; set; }   // 使用者只想改 email，沒送 name → 400
    public string Email { get; set; }
}
```

部分更新的 DTO 必須把所有欄位設成 nullable：

```csharp
public class UpdateUserDto
{
    public string? Name { get; set; }
    public string? Email { get; set; }
}
```

但這又帶來新問題：**分不出「沒送這個欄位」和「送了 null 表示要清空」**。真正需要區分時，要用 `JsonPatchDocument` 或包一層 `Optional<T>` 型別。多數業務不需要走到這一步，但如果需求裡出現「把備註清空」這種操作，就得想清楚。

要全域關掉這個行為：

```csharp
builder.Services.AddControllers(options =>
{
    options.SuppressImplicitRequiredAttributeForNonNullableReferenceTypes = true;
});
```

不建議關——它是一個好的預設。針對 PATCH DTO 個別調整型別即可。

### 2.4 型別轉換失敗

送 `{"age": "abc"}` 給 `public int Age { get; set; }`，`System.Text.Json` 會拋出反序列化例外，被框架轉成 `ModelState` 錯誤，最終回 400。錯誤訊息預設是 `The JSON value could not be converted to System.Int32`——對前端不太友善但至少方向明確。

要讓字串數字（`"25"`）能綁到 `int`，需要開啟寬鬆模式：

```csharp
options.JsonSerializerOptions.NumberHandling = JsonNumberHandling.AllowReadingFromString;
```

這在對接某些會把所有值都送成字串的前端或第三方系統時很有用。

### 2.5 `DateTime` 與時區

`System.Text.Json` 預期 ISO 8601 格式。收到 `"2026-08-14T10:00:00Z"` 時，`DateTime` 的 `Kind` 會是 `Utc`；收到 `"2026-08-14T10:00:00"`（無時區資訊）時是 `Unspecified`；收到 `"2026-08-14T10:00:00+08:00"` 會被轉成本地時間，`Kind` 是 `Local`——而「本地」是**伺服器的時區**，容器裡通常是 UTC。

這是跨時區系統最常見的資料污染來源。實務建議：**API 邊界一律用 `DateTimeOffset`**。它明確攜帶偏移量，不會有 `Kind` 的歧義，也不依賴伺服器時區設定。資料庫端則統一存 UTC。

---

## 三、驗證：`ModelState` 與自動 400

綁定完成後，框架對綁定出來的物件執行驗證，結果放進 `ModelState`。

### 3.1 DataAnnotations

```csharp
public class CreateUserDto
{
    [Required(ErrorMessage = "姓名為必填")]
    [StringLength(50, MinimumLength = 2)]
    public string Name { get; set; } = string.Empty;

    [Required]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    [Range(0, 150)]
    public int Age { get; set; }

    [RegularExpression(@"^09\d{8}$", ErrorMessage = "手機格式錯誤")]
    public string? Phone { get; set; }
}
```

### 3.2 自動 400 的實際輸出

有 `[ApiController]` 時，`ModelState` 無效會**在 action 執行之前**自動回應。這是由一個內建的 action filter（`ModelStateInvalidFilter`）完成的，所以 action 裡的程式碼一行都不會執行。

回應是 RFC 7807 的 `ValidationProblemDetails`：

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "One or more validation errors occurred.",
  "status": 400,
  "traceId": "00-8a3f...-00",
  "errors": {
    "Name": ["姓名為必填"],
    "Email": ["The Email field is not a valid e-mail address."]
  }
}
```

`errors` 是一個「欄位名 → 錯誤訊息陣列」的字典，前端可以直接對應到表單欄位顯示。這是標準格式，值得保留而不是自創一套。

要客製格式（例如統一包一層 `{ code, message, data }`）：

```csharp
builder.Services.Configure<ApiBehaviorOptions>(options =>
{
    options.InvalidModelStateResponseFactory = context =>
    {
        var errors = context.ModelState
            .Where(e => e.Value?.Errors.Count > 0)
            .ToDictionary(
                e => e.Key,
                e => e.Value!.Errors.Select(x => x.ErrorMessage).ToArray());

        return new BadRequestObjectResult(new
        {
            code = "VALIDATION_ERROR",
            message = "輸入資料有誤",
            errors
        });
    };
});
```

改之前先想清楚：偏離標準格式意味著失去現成工具的支援（Swagger 的錯誤描述、部分前端函式庫的自動處理）。除非有跨系統的既有錯誤格式契約，否則保留 `ProblemDetails` 通常更好。錯誤格式的整體策略在 [[15-error-handling]] 統一討論。

### 3.3 驗證屬性只是第一道

DataAnnotations 能表達的是**格式與範圍**。它表達不了：

- 「email 不能重複」（需要查資料庫）
- 「結束日期必須晚於開始日期」（跨欄位）
- 「只有管理員能設定這個欄位」（需要當前使用者身分）

跨欄位驗證可以用 `IValidatableObject`：

```csharp
public class DateRangeDto : IValidatableObject
{
    public DateTimeOffset Start { get; set; }
    public DateTimeOffset End { get; set; }

    public IEnumerable<ValidationResult> Validate(ValidationContext context)
    {
        if (End <= Start)
        {
            yield return new ValidationResult("結束時間必須晚於開始時間", new[] { nameof(End) });
        }
    }
}
```

需要資料庫或服務的驗證，屬於**業務規則**，應該放在 service 層而不是 DTO 上。硬塞進自訂 ValidationAttribute（透過 `ValidationContext.GetService` 拿 DI）技術上可行，但會讓 DTO 依賴基礎設施，且該驗證在單元測試 DTO 時無法獨立執行。

### 3.4 FluentValidation

當驗證規則變複雜時，DataAnnotations 的表達力會不夠。FluentValidation 是主流替代方案：

```csharp
public class CreateUserValidator : AbstractValidator<CreateUserDto>
{
    public CreateUserValidator(IUserRepository repo)
    {
        RuleFor(x => x.Name).NotEmpty().Length(2, 50);
        RuleFor(x => x.Email)
            .NotEmpty().EmailAddress()
            .MustAsync(async (email, ct) => !await repo.ExistsAsync(email, ct))
            .WithMessage("此 email 已被註冊");
    }
}
```

取捨很清楚：

| | DataAnnotations | FluentValidation |
| --- | --- | --- |
| 規則位置 | 混在 DTO 屬性上 | 獨立類別 |
| 複雜條件 | 難（要自訂 attribute） | 容易（鏈式 API） |
| 非同步驗證 | 不支援 | 支援 |
| DI | 彆扭 | 原生 |
| Swagger 產生 | 自動反映 | 需額外套件 |
| 額外依賴 | 無 | 有（且 v11 起商業授權有變化） |

建議：簡單專案用 DataAnnotations；驗證規則多且有跨欄位、需查資料庫的情境用 FluentValidation。混用也可以，但要清楚劃分「格式用 DataAnnotations、業務用 FluentValidation」，否則規則散落兩處難以維護。

---

## 四、驗證不是安全邊界

這一節比前面所有內容都重要，因為它關係到資料完整性而不只是使用體驗。

### 4.1 Over-posting（大量賦值）

假設偷懶直接用 Entity 當作 API 的輸入型別：

```csharp
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public bool IsAdmin { get; set; }          // ⚠️
    public decimal Balance { get; set; }       // ⚠️
}

[HttpPost]
public async Task<IActionResult> Create([FromBody] User user)
```

攻擊者送：

```json
{ "name": "hacker", "email": "h@x.com", "isAdmin": true, "balance": 999999 }
```

Model binding 會**忠實地**把每個欄位填進去，包括 `IsAdmin` 和 `Balance`。沒有任何驗證屬性能阻止這件事——因為從框架的角度，這些欄位本來就是這個型別的一部分，資料格式完全合法。

這就是為什麼**DTO 不是為了「好看」或「解耦」而存在，它是安全邊界**。DTO 只宣告「這個端點允許客戶端設定的欄位」，沒宣告的欄位物理上綁不進來：

```csharp
public record CreateUserDto(string Name, string Email);   // 沒有 IsAdmin，綁不進來

[HttpPost]
public async Task<IActionResult> Create([FromBody] CreateUserDto dto)
{
    var user = new User
    {
        Name = dto.Name,
        Email = dto.Email,
        IsAdmin = false                // 由伺服器決定，不接受客戶端輸入
    };
    // ...
}
```

同樣的道理適用於輸出方向：直接回傳 Entity 會把 `PasswordHash`、內部欄位、以及所有 navigation property 一起序列化出去。輸出也要用 DTO。

### 4.2 驗證發生在伺服器

前端驗證是使用體驗，不是安全機制。任何人都可以用 curl 繞過整個前端。**每一條規則都必須在伺服器端存在**，前端的那份只是為了讓使用者不用等來回一趟。

### 4.3 上傳檔案的額外檢查

`IFormFile` 的 `FileName` 和 `ContentType` 都是**客戶端提供的字串**，可以任意偽造。

```csharp
// ❌ 相信客戶端說的
if (file.ContentType == "image/png") { /* 安全 */ }

// ❌ 直接用客戶端給的檔名（可能含 ../../ 造成路徑穿越）
var path = Path.Combine(uploadDir, file.FileName);
```

正確做法是：自己產生檔名（GUID）、驗證副檔名白名單、讀取檔頭 magic number 確認實際型別、限制大小（在 Kestrel 與反向代理兩端都要設）。

---

## 五、自訂綁定

### 5.1 `TryParse`：最輕量的方式

型別只要有符合簽章的靜態 `TryParse`，就能直接從 route/query 綁定：

```csharp
public readonly record struct TenantId(string Value)
{
    public static bool TryParse(string? s, IFormatProvider? provider, out TenantId result)
    {
        if (!string.IsNullOrWhiteSpace(s) && s.StartsWith("T-"))
        {
            result = new TenantId(s);
            return true;
        }
        result = default;
        return false;
    }
}

// 直接可用
app.MapGet("/tenants/{id}", (TenantId id) => Results.Ok(id));
```

這是把「原始字串」轉成「有意義的領域型別」的好方法，讓非法值在進入業務邏輯之前就被擋掉。

### 5.2 `IModelBinder`：完整控制

需要跨多個來源組合、或處理非標準格式時：

```csharp
public class CommaSeparatedArrayBinder : IModelBinder
{
    public Task BindModelAsync(ModelBindingContext bindingContext)
    {
        var value = bindingContext.ValueProvider
            .GetValue(bindingContext.ModelName).FirstValue;

        if (string.IsNullOrEmpty(value))
        {
            return Task.CompletedTask;   // 不設 Result 表示「我沒處理」
        }

        var ids = value.Split(',', StringSplitOptions.RemoveEmptyEntries)
                       .Select(int.Parse)
                       .ToArray();

        bindingContext.Result = ModelBindingResult.Success(ids);
        return Task.CompletedTask;
    }
}

[HttpGet]
public IActionResult GetByIds([ModelBinder(typeof(CommaSeparatedArrayBinder))] int[] ids)
```

注意上面的 `int.Parse` 在遇到非數字時會拋例外——真實的 binder 應該用 `TryParse` 並在失敗時呼叫 `bindingContext.ModelState.AddModelError(...)`，讓它變成一個 400 而不是 500。

---

## 六、常見誤解

**「DTO 是為了解耦，小專案可以直接用 Entity。」**
DTO 首先是安全邊界。直接用 Entity 當輸入型別會開啟 over-posting 漏洞；當輸出型別會洩漏內部欄位。專案大小不影響這一點。

**「加了 `[Required]` 就一定會被檢查。」**
在 Minimal API 裡預設**不會**——它沒有 MVC 的驗證管線。在 Controller 裡則需要 `[ApiController]`（或自己檢查 `ModelState`）。

**「Nullable 只是編譯器提示，不影響執行期。」**
在 ASP.NET Core 的驗證系統裡，不可為 null 的參考型別**自動視為必填**。這是實際影響 400 回應的行為。

**「`ModelState.IsValid` 要自己檢查。」**
有 `[ApiController]` 時框架已經在 action 執行前檢查並回應了，手寫的 `if (!ModelState.IsValid)` 永遠是 false 分支，屬於死程式碼。除非明確關閉了 `SuppressModelStateInvalidFilter`。

**「JSON 屬性名稱要完全一致。」**
ASP.NET Core 預設大小寫不敏感，`userName`、`UserName`、`username` 都能綁到 `UserName`。但底線不會被自動處理。

**「前端驗證過了，後端可以簡化。」**
前端驗證是體驗，不是安全。任何規則都必須在伺服器端完整存在。

---

## 七、同事會來問你的問題

**Q：POST 進來的 dto 是 null，怎麼查？**
依序檢查：`Content-Type` 是不是 `application/json`；controller 有沒有 `[ApiController]`（沒有的話複雜型別預設不從 body 綁）；JSON 屬性名有沒有底線之類的差異；DTO 是不是多建構子的 record；有沒有 middleware 先讀走了 body（第 01 章）。

**Q：GET 帶查詢條件，用一個物件接為什麼收不到？**
複雜型別預設推斷成 `[FromBody]`，但 GET 沒有 body。加上 `[FromQuery]`，框架就會逐屬性去 query string 找。

**Q：明明沒寫 `[Required]`，為什麼說欄位必填？**
專案開了 nullable reference types，不可為 null 的 `string` 被自動視為必填。PATCH 式的部分更新 DTO 應該把欄位宣告成 `string?`。

**Q：可以在 action 裡加 `if (!ModelState.IsValid) return BadRequest()` 嗎？**
可以但沒用。`[ApiController]` 已經在 action 執行前擋掉了無效的 ModelState，所以這段程式碼永遠不會進去。要自己處理就得先關掉 `SuppressModelStateInvalidFilter`。

**Q：驗證錯誤訊息想改成自己的格式，怎麼做？**
設定 `ApiBehaviorOptions.InvalidModelStateResponseFactory`。但先確認有必要——預設的 `ValidationProblemDetails` 是 RFC 7807 標準格式，偏離它會失去工具支援。

**Q：時間欄位在不同環境算出來差 8 小時。**
`DateTime` 的 `Kind` 依 JSON 字串是否帶時區資訊而定，帶偏移量時會轉成伺服器本地時間，而容器通常是 UTC。API 邊界改用 `DateTimeOffset`，資料庫統一存 UTC。

**Q：DataAnnotations 還是 FluentValidation？**
格式與範圍檢查用 DataAnnotations 就夠。需要跨欄位條件、非同步查資料庫、複雜分支時用 FluentValidation。混用時要劃清界線，別讓同一條規則出現在兩個地方。

---

## 連結

- [[basics-05-model-binding-and-validation]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[basics-06-dto-design]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[03-routing-and-endpoints]] — 上一章：參數來源之一的路由值
- [[05-filters-and-mvc-internals]] — 下一章：驗證的自動 400 是哪個 filter 做的
- [[01-request-pipeline]] — request body 只能讀一次
- [[15-error-handling]] — ProblemDetails 與統一錯誤格式
