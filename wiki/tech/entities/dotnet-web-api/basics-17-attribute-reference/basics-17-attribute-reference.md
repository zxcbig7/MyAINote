---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, attribute, metadata, reference, taskTracker]
sources:
  - raw/Web Framework/NET Web API/ASP NET Core Web API 常用 Attribute 整理.md
created: 2026-11-01
updated: 2026-11-01
---

# 入門附錄：Attribute 速查 — 它自己什麼都不做，是框架在讀它

## 一個明明加了 `[Authorize]` 卻放行的 action

有位同事要把 controller 裡的一支 action 收緊。這個 controller 類別上原本標了 `[AllowAnonymous]`，因為裡面大部分都是公開端點，只有一支需要登入。他的直覺很合理：越靠近 action 的設定越具體，所以在那支 action 上加一個 `[Authorize]`，應該就會蓋過類別上的 `[AllowAnonymous]`。部署之後，沒登入的人照樣收到 200。

這件事在一個獨立的小專案裡實測過。類別上標 `[AllowAnonymous]`，其中一個 action 標 `[Authorize]`，用三種身分各打一次（匿名、已登入但沒有角色、Admin）：

```text
GET /anon-class/authorize-action -> 匿名 200，alice 200，root(Admin) 200
GET /anon-class/plain-action -> 匿名 200，alice 200，root(Admin) 200
```

匿名請求拿到 200，action 上的 `[Authorize]` 被默默蓋掉。建置時編譯器其實有警告：`warning ASP0026: This [Authorize] attribute is overridden by an [AllowAnonymous] attribute from farther away on 'AnonClassController'`。警告很容易在一堆 build 輸出裡被忽略，但它說的就是這件事。規則是：只要 endpoint 的 metadata 裡出現 `[AllowAnonymous]`，不論它在類別還是在 action，所有 `[Authorize]` 都失效。「越近越優先」在這裡不成立。

這個例子點出本附錄的核心：一個 attribute 本身什麼都不做。它只是編譯時寫進組件的一段標記，真正決定行為的是「誰在什麼時候讀它」，而每個讀它的程式各自定義怎麼合併類別與 action 兩層的標記。不知道讀者是誰，就沒辦法預測結果。本附錄把 TaskTracker 與常見專案會用到的 attribute 按「它在解決什麼問題」分成八組，每組先說誰讀、什麼時候讀，再逐個列出作用、容易誤會的地方與最小例子。需要機制推導的地方，會指向深度篇對應章節。

[[basics-16-deployment-and-go-live]] 把 TaskTracker 帶到可以上線的狀態。前面十六章零散地用過二十多種 attribute，這一章把它們收攏成一份可以查閱的清單，並修正幾個流傳很廣、但實測結果相反的說法。

---

## 一、先知道誰在讀：四種讀者

Attribute 是掛在類別、方法或屬性上的宣告式標記。C# 編譯器把它存進組件的 metadata，本身沒有任何執行邏輯。ASP.NET Core 在不同時間點，由不同的元件去讀它們，大致分四類：

| 讀者 | 何時讀 | 讀哪些 attribute |
| --- | --- | --- |
| Routing 與 action 探索 | 應用程式啟動時，建立 route table | `[Route]`、`[HttpGet]` 等、`[NonAction]`、`[ActionName]`、`[ApiVersion]` |
| Middleware | 每個請求，endpoint 被選中之後，讀該 endpoint 身上的 metadata | `[Authorize]`、`[AllowAnonymous]`、`[EnableCors]`、`[EnableRateLimiting]` |
| MVC 的 binding、filter、formatter | 請求進入 action 前後 | `[ApiController]`、`[From*]`、`[BindNever]`、DataAnnotations、`[Produces]`、`[Consumes]`、`[ResponseCache]`、`[ServiceFilter]` |
| 文件產生器與序列化器 | 要求 OpenAPI 文件時；序列化 JSON 時 | `[ProducesResponseType]`、`[ApiExplorerSettings]`、`[JsonPropertyName]`、`[JsonIgnore]` |

這張表的用處是排錯。attribute 寫了卻沒效果時，先問「讀它的人有沒有在場」：`[EnableCors]` 需要 pipeline 裡有 `UseCors()`，`[EnableRateLimiting]` 需要 `UseRateLimiter()`，`[Authorize]` 需要 `UseAuthorization()`（[[basics-11-auth-concepts-and-pipeline]] 講過順序）。沒有讀者，attribute 就只是一段不會被執行的註記，而且編譯不會報錯。

第二個要記住的是合併規則沒有通則。以下三個都已實測確認，後面各節會再逐一展開：

- `[Route]` 與 `[HttpGet("x")]`：類別上的 `[Route]` 是前綴，action 上的 template 接在後面。
- `[Authorize]`：類別與 action 兩層疊加，全部都要通過（AND）。
- `[AllowAnonymous]`：出現在任何一層，就讓所有 `[Authorize]` 失效。

深度篇把這套機制稱為 endpoint metadata，推導過程在 [[03-routing-and-endpoints]] 與 [[05-filters-and-mvc-internals]]。

---

## 二、路由：這個 URL 該交給哪個 action

Routing 要回答的問題是「請求進來的 method 與路徑，對應哪一段程式」。讀這組 attribute 的是 routing 系統，時機是應用程式啟動：框架掃過所有 controller，把每個 action 的 template 收集成 route table，之後每個請求只做比對。因此改 template 必須重新啟動，執行中不會變。

| Attribute | 作用 | 常見誤解 |
| --- | --- | --- |
| `[Route("api/v{version:apiVersion}/tasks")]` | 設定 controller 的路徑前綴；放在 action 上則是完整的 template | 以為 `[controller]` 會變小寫，見下 |
| `[HttpGet("{id:guid}")]` 等 | 同時宣告 HTTP method 與 action 這一段的 template | 以為 template 以 `/` 開頭仍會接在前綴後面；實際上會取代前綴 |
| `[NonAction]` | 這個 public 方法不是 endpoint | 以為 `private` 才能避開；public 方法在 controller 裡預設可能被當 action |
| `[ActionName("Rename")]` | 改 action 在框架內部的名稱 | 以為會改 URL，其實不會 |

TaskTracker 的 `TasksController` 用的就是第一與第二列：

```csharp
[ApiController]
[ApiVersion(1.0)]
[Authorize(Policy = Permissions.TasksRead)]
[Route("api/v{version:apiVersion}/tasks")]
public class TasksController : ControllerBase
{
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<TaskResponse>> GetByIdAsync(Guid id, CancellationToken ct) { ... }
}
```

最終 `GetByIdAsync` 的路徑是 `api/v{version:apiVersion}/tasks/{id:guid}`。`:guid` 是 route constraint，不是驗證，這個差別在 [[basics-04-controllers-and-routing]] 與 [[03-routing-and-endpoints]] 講過。

### `[controller]` 展開後是 `Users` 還是 `users`

「`[controller]` 會展開成小寫，所以網址是 `/api/users`」是流傳很廣的說法，另一個版本是「路由比對區分大小寫，所以大小寫打錯會 404」。兩者都不對。用 `UsersController` 與 `OrderItemsController` 實測，預設設定下 route table 裡存的是：

```text
RoutePattern.RawText：api/OrderItems, api/Users, api/Users, api/Users/{id:int}
GET /api/Users -> 200 OK
GET /api/users -> 200 OK
GET /API/USERS -> 200 OK
GET /api/uSeRs/7 -> 200 OK
GET /api/order-items -> 404 Not Found
```

`[controller]` 只是把類別名稱去掉 `Controller` 後綴，大小寫保持不變，所以是 PascalCase 的 `api/Users`。比對時完全不分大小寫，打錯大小寫不會 404。大小寫真正會出現的地方是「產生出來的網址」：`CreatedAtAction` 組出的 `Location` 預設就是 `/api/Users/42`，OpenAPI 文件裡的 path 也是 `/api/Users`。這才是 Swagger 畫面上看到大寫開頭網址的來源。

想讓產生的網址變小寫，設 `RouteOptions.LowercaseUrls = true`。這只影響產生出來的網址（`Location` 與 OpenAPI path），route pattern 本身不變。想把 `OrderItems` 變成 `order-items`，要加 `RouteTokenTransformerConvention` 與一個 parameter transformer，這會改掉 route pattern 本身，原本的 `/api/OrderItems` 隨即變成 404，所以對已上線的 API 是 breaking change。最保險的做法是跟 TaskTracker 一樣，路徑直接寫字面值：`[Route("api/v{version:apiVersion}/tasks")]`，不依賴 token，也就不會因為類別改名而讓網址跟著變。

### `[NonAction]` 與 `[ActionName]`

在獨立專案實測：標了 `[NonAction]` 的 public 方法，請求打進去是 404，等於不存在。`[ActionName("Rename")]` 標在 `RenameAsync` 上之後，URL 完全不受影響（路徑仍由 `[HttpPut("rename/{id:int}")]` 決定），它影響的是「用 action 名稱去反查路徑」的地方。在另一個 action 裡寫 `CreatedAtAction("Rename", new { id = 9 }, dto)`，`Location` 正確解析成 `.../api/Things/rename/9`。

這就是 [[basics-04-controllers-and-routing]] 提過的 `Async` 後綴問題的另一半：MVC 預設（`SuppressAsyncSuffixInActionNames = true`）把 action 名稱的 `Async` 後綴去掉，所以 `nameof(GetByIdAsync)` 查不到。TaskTracker 的解法是在 `AddControllers` 把這個選項關掉，讓登記名稱保留 `Async`、`nameof` 繼續可用。不想動全域設定時，在該 action 標 `[ActionName("GetById")]` 明確命名，也能避開這個坑。

---

## 三、HTTP method：只接受這幾種動詞

`[HttpGet]`、`[HttpPost]`、`[HttpPut]`、`[HttpDelete]`、`[HttpPatch]`、`[HttpHead]`、`[HttpOptions]` 同時做兩件事：宣告這個 action 接受哪個 method，並可選擇帶 template。讀者仍是 routing，啟動時讀。如果 action 完全沒有任何 `[Http*]` attribute，它會接受所有 method，這通常不是你要的。需要同時接受幾種 method 時用 `[AcceptVerbs("GET", "HEAD")]`。

路徑對但 method 不對，回的是 405 而不是 404，這是判斷「路徑寫錯」還是「動詞用錯」的快速線索。[[basics-03-first-project]] 的 `curl.exe -i` 練習就出現過這種差別。

一個容易踩到的組合是 `[HttpGet]` 搭配複合型別參數。`[ApiController]` 的綁定推斷與 HTTP method 無關：`[HttpGet]` action 上沒標來源的複合型別一樣會被推斷成從 body 綁定，GET 沒有 body 就是 415，詳見下一節。

```csharp
[HttpGet("search/by-name/{name}")]
public ActionResult Search(string name) { ... }
```

template 可以串接子路徑與參數，若類別前綴是 `api/things`，`GET /api/things/search/by-name/abc` 會把 `abc` 綁進 `name`。這種寫法簡單的查詢可以，但路徑一長就該回頭檢查資源設計（[[basics-02-rest-api-design]]），很多時候把條件放進 query string 才是正確答案。

---

## 四、Binding：請求裡的字串如何變成參數

Binding 這組解決的問題是「資料在請求的哪個位置」。請求同一份資料可能出現在路徑、query string、header、body 或表單，框架必須知道每個參數去哪找。讀者是 MVC 的 model binding，時機是 action 執行之前。

先講最重要的那個：

### `[ApiController]`：不只是自動 400

`[ApiController]` 標在 controller 類別上，是一整包行為的開關：要求使用 attribute routing、驗證失敗自動回 400、綁定來源推斷、`multipart/form-data` 推斷，以及把 4xx 錯誤轉成 `ProblemDetails`。

很多人把它理解成「就是多了自動 400」。這個說法漏了最關鍵的一項：它同時改變了複合型別參數的預設綁定來源。在獨立專案裡用同一組 action，有無 `[ApiController]` 對照實測：

```text
有 [ApiController]
GET /with-api/search?keyword=a&page=2 -> 415 Unsupported Media Type
POST /with-api/items?name=from-query -> 200 OK | body: {"name":"widget","quantity":3}
POST /with-api/items（form 內容） -> 415 Unsupported Media Type

沒有 [ApiController]
GET /without-api/search?keyword=a&page=2 -> 200 OK | body: {"keyword":"a","page":2}
POST /without-api/items（JSON body） -> 200 OK | body: {"name":null,"quantity":0}
POST /without-api/items?name=from-query -> 200 OK | body: {"name":"from-query","quantity":0}
```

有 `[ApiController]` 時，複合型別（自訂 class）一律推斷成 `[FromBody]`，與 HTTP method 無關：GET 搭配複合型別，若沒有 JSON body 就是 415，即使 query string 帶了正確的值。POST 時 query string 的同名值會被忽略。簡單型別（`string`、`int`）則從 route 與 query string 綁定，不需要標註。

沒有 `[ApiController]` 時規則反過來：複合型別從 route、query string、form 綁定，永遠不會從 JSON body 來。POST 一份 JSON 進去，沒有任何錯誤，欄位全是預設值，回 200。這是最危險的組合，因為看起來成功了。而且沒有自動 400，`ModelState.IsValid` 是 `false` 時 action 照樣執行。

所以 TaskTracker 的 `GetAllAsync` 必須明確標 `[FromQuery]`：

```csharp
[HttpGet]
public async Task<ActionResult<PagedResponse<TaskResponse>>> GetAllAsync([FromQuery] TaskListQuery query, CancellationToken ct)
```

`TaskListQuery` 是複合型別，不標的話會被推斷成 `[FromBody]`，GET 沒有 body，就是 415。而 `CreateAsync(CreateTaskRequest request, ...)` 沒有標任何東西，是因為推斷的結果剛好是要的 `[FromBody]`。

### 來源指定 attribute

| Attribute | 資料從哪來 | 常見誤解 |
| --- | --- | --- |
| `[FromRoute]` | 路徑中的 `{id}` | 參數名稱要與 template 的名稱相同；`Create` 這種沒有 `{id}` 的 action 標它，永遠是預設值 |
| `[FromQuery]` | `?a=1&b=2` | 可用 `Name = "..."` 改比對名稱；複合型別要標它才會展開成屬性 |
| `[FromBody]` | request body，用 input formatter（預設 JSON）解析 | 一個 action 只能有一個；與 `[FromForm]` 不能並存 |
| `[FromHeader]` | request header | 拿來傳 token 不合宜，認證交給 `Authorization` 標頭與 middleware |
| `[FromForm]` | `multipart/form-data` 或 `application/x-www-form-urlencoded`，上傳檔案用 | 與 `[FromBody]` 互斥 |
| `[FromServices]` | 從 DI 容器取服務 | 在 Controller 裡通常 constructor injection 就夠了；只在某個 action 才需要的服務才用 |
| `[FromKeyedServices("key")]` | 從 DI 容器取 keyed service | .NET 8 起的 keyed services 才有 |

前述「一個 action 同時標五個來源」的範例，常見於各種速查文章，但它本身不能執行：`[FromBody]` 與 `[FromForm]` 不能並存，`[FromBody]` 最多一個，沒有 `{id}` 的 action 標 `[FromRoute] id` 毫無意義。要示範各種來源，應該分開寫，每個 action 只示範一種：

```csharp
[HttpGet("{id:guid}")]
public ActionResult<TaskResponse> Get([FromRoute] Guid id) { ... }

[HttpGet]
public ActionResult<PagedResponse<TaskResponse>> List([FromQuery] TaskListQuery query) { ... }

[HttpPost]
public ActionResult<TaskResponse> Create([FromBody] CreateTaskRequest request) { ... }

[HttpPost("upload")]
public ActionResult Upload([FromForm] IFormFile file) { ... }
```

`[FromKeyedServices]` 在 controller action 上實測可用：註冊 `AddKeyedSingleton<string>("a", "keyed-a")` 後，`Keyed([FromKeyedServices("a")] string s)` 回 `keyed-a`。

### `[BindNever]` 與 `[BindRequired]`：只管 model binding

這兩個 attribute 標在屬性上，控制 model binding 要不要處理它。實測用一個有 `[BindRequired]` 的 `Page` 與 `[BindNever]` 的 `Secret` 的 query 物件：

```csharp
public class Q
{
    [BindRequired] public int Page { get; set; }
    [BindNever] public string? Secret { get; set; }
}
```

```text
GET /api/things/bind?page=2&secret=leak -> 200 OK | {"page":2,"secret":null}
GET /api/things/bind?secret=leak -> 400 Bad Request
```

`Secret` 不會被 query string 綁定，`Page` 缺少時直接 400。這符合預期。但同一組 attribute 用在 JSON body 的物件上，結果就不一樣了：

```csharp
public class Over
{
    public string Name { get; set; } = "";
    [BindNever] public bool IsAdmin { get; set; }
    [JsonIgnore] public string? Hidden { get; set; }
    [JsonPropertyName("rn")] public string? Renamed { get; set; }
}
```

用 body `{"name":"n","isAdmin":true,"hidden":"h","renamed":"r"}` POST 進去：

```text
POST /api/things/bind-json -> 200 OK | {"name":"n","isAdmin":true,"hidden":null,"renamed":null}
```

`isAdmin` 被設成 `true`。`[BindNever]` 擋得住 query string 與 form，擋不住 JSON body，因為 JSON 是 `System.Text.Json` 在反序列化，不走 model binding 的屬性層級邏輯。要排除 JSON 屬性用 `[JsonIgnore]`（`hidden` 確實是 `null`），要改 JSON 名稱用 `[JsonPropertyName("rn")]`（改名之後，用舊名稱 `renamed` 送的值收不到，也是 `null`）。

結論很直接：防 over-posting 最可靠的做法，是不要讓請求 DTO 帶有不該被客戶端設定的屬性，而不是替它們加 `[BindNever]`。這是 [[basics-06-dto-design]] 的主張，也是 [[04-model-binding-and-validation]] 4.1 的內容。

---

## 五、驗證：輸入合不合規格

驗證 attribute 屬於 `System.ComponentModel.DataAnnotations`，它們描述「這個值合法的條件」。讀者是 MVC 的 model validation，時機是 binding 完成之後、action 執行之前。`[ApiController]` 在其中扮演關鍵：它自動插入一個 filter，檢查 `ModelState`，無效就直接回 400，action 完全不會被呼叫。沒有 `[ApiController]` 的話，驗證仍會執行，`ModelState.IsValid` 也會是 `false`，但沒有人替你擋，action 照樣跑（前面的實測就是 `modelStateValid: false` 而 action 仍回 200）。

| Attribute | 作用 | 常見誤解 |
| --- | --- | --- |
| `[Required]` | 值不能是 `null`（字串另外不能是空字串或只有空白） | 標在非 nullable 的值型別（如 `int`、enum）上永遠通過，因為預設值 0 不是 `null` |
| `[StringLength(100)]` | 字串長度上限（可設下限） | 只驗證，不會裁切；也不會建立資料庫欄位限制 |
| `[Range(1, 100)]` | 數值範圍 | 用在 `int?` 時，沒傳值（`null`）不檢查 |
| `[EmailAddress]` | 格式像 email | 只是格式的簡單檢查，不代表信箱存在 |
| `[EnumDataType(typeof(T))]` | 值必須是 enum 的合法成員 | 單獨不處理缺值 |
| `[RegularExpression]`、`[MinLength]`、`[MaxLength]`、`[Compare]` | 同名意義 | 正規表達式的錯誤訊息預設很難讀，建議自訂 `ErrorMessage` |

TaskTracker 的 DTO 示範了前三條的互動：

```csharp
public sealed class UpdateTaskRequest
{
    [Required]
    [StringLength(100)]
    public string Title { get; init; } = string.Empty;

    [Required]
    [EnumDataType(typeof(TaskItemStatus))]
    public TaskItemStatus? Status { get; init; }
}
```

`Status` 宣告成 `TaskItemStatus?`（可為 null）而不是 `TaskItemStatus`，是刻意的。如果它不可為 null，沒傳 `status` 的 JSON 會得到列舉的預設值（`default`），`[Required]` 看不出來「沒傳」和「傳了預設值」的差別。把它宣告成 nullable，`[Required]` 才有東西可以檢查。這個細節在 [[basics-05-model-binding-and-validation]] 展開過；`TaskListQuery` 的 `[Range(1, 100)]` 也是同樣的邏輯，`PageSize` 宣告成 `int?` 代表「沒傳就用預設」。

兩個提醒。第一，驗證 attribute 是第一道防線，不是安全邊界：它只檢查你標了的屬性，檢查不到業務規則（例如 title 在同一使用者下不能重複，TaskTracker 用資料庫唯一索引加 409 處理）。第二，在 `#nullable enable` 的專案裡，非 nullable 的參考型別屬性（`string Title`）已被當成隱含的 `[Required]`，缺值時的 400 訊息來自這個隱含規則。[[04-model-binding-and-validation]] 的 2.3 節解釋了它造成的意外 400。

---

## 六、授權：誰可以呼叫

授權 attribute 回答的是「這個 endpoint 要什麼資格」。讀者是 `UseAuthorization()` 中介軟體，時機是 endpoint 被選中、尚未進入 action 的那一刻：它收集 endpoint 身上所有的授權 metadata，逐一評估。`[Authorize]` 本身只是一個標記，不做驗證（[[basics-11-auth-concepts-and-pipeline]]）；真正驗證 token 的是 `UseAuthentication()`，沒有它，授權永遠看到的是匿名使用者，結果是永遠 401。

| Attribute | 作用 | 常見誤解 |
| --- | --- | --- |
| `[Authorize]` | 要求已登入 | 類別與 action 兩層是疊加（AND），不是後者蓋過前者 |
| `[Authorize(Roles = "Editor,Admin")]` | 要求具備角色之一 | 逗號是 OR，不是 AND |
| `[Authorize(Policy = "tasks:write")]` | 要求通過指定的 policy | policy 要先用 `AddAuthorization` 註冊，名稱打錯會在請求時丟例外 |
| `[AllowAnonymous]` | 放行未登入者 | 放在類別上會蓋掉所有 action 上的 `[Authorize]` |

### 疊加（AND）與 `[AllowAnonymous]` 的優先關係

開頭的實測是三種 controller（類別上分別是 `[AllowAnonymous]`、`[Authorize]`、`[Authorize(Roles = "Admin")]`）搭配每種 action（`[Authorize]`、`[AllowAnonymous]`、什麼都不標），用匿名、已登入無角色（alice）、Admin（root）三種身分打的結果：

```text
GET /auth-class/allowanonymous-action -> 匿名 200，alice 200，root(Admin) 200
GET /auth-class/plain-action -> 匿名 401，alice 200，root(Admin) 200
GET /roles-class/allowanonymous-action -> 匿名 200，alice 200，root(Admin) 200
GET /roles-class/authorize-action -> 匿名 401，alice 403，root(Admin) 200
```

整理成三條規則：

- 只要 endpoint 的 metadata 裡有 `[AllowAnonymous]`，位置在類別或 action 都一樣，整個 endpoint 不需要授權。`roles-class/allowanonymous-action` 連類別上的 `Roles = "Admin"` 一起放行。
- `[Authorize]` 是累加的。`roles-class/authorize-action` 的類別要求 Admin，action 只標 `[Authorize]`，結果匿名 401、alice 403、Admin 200：action 上的 `[Authorize]` 沒有取代類別的要求。
- 因此「大部分公開、少數受保護」的設計不能把 `[AllowAnonymous]` 放在類別上。正確的方向是反過來：類別預設 `[Authorize]`，要公開的 action 個別標 `[AllowAnonymous]`。

TaskTracker 的疊加規則是這樣用的。`TasksController` 類別上有 `[Authorize(Policy = Permissions.TasksRead)]`，建立與修改的 action 再標 `[Authorize(Policy = Permissions.TasksWrite)]`，刪除標 `[Authorize(Policy = Permissions.TasksDelete)]`。兩層疊加的意思是：建立任務需要 `tasks:read` 與 `tasks:write` 兩個權限都有，刪除需要 `tasks:read` 與 `tasks:delete`。Viewer 只有 `tasks:read`，嘗試建立任務：

```powershell
'{"title":"Nope"}' | curl.exe -s -i -X POST http://localhost:5080/api/v1/tasks -H "Content-Type: application/json" -H "Authorization: Bearer $viewerToken" -d '@-'
```

```text
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json; charset=utf-8

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.4","title":"Forbidden","status":403,"traceId":"00-2f805acbf75e62e75db331c878af7451-56bff6f345b67749-00"}
```

（省略 Date、Server 標頭。）已登入但資格不夠是 403；沒登入是 401，這個分野在 [[basics-11-auth-concepts-and-pipeline]] 講過。healthz 端點在 Minimal API 風格的註冊裡用 `.AllowAnonymous()`（TaskTracker 的 `MapHealthChecks(...).AllowAnonymous()`），它是 `[AllowAnonymous]` 的 endpoint 版本，寫進同一份 metadata，所以規則一樣。

### `Roles` 的 OR 與 AND

「逗號分隔的角色是同時需要（AND），疊多個 attribute 才是其中之一（OR）」是另一個說法完全相反的常見錯誤。用 `Editor`、`Admin`、同時有兩個角色的使用者實測：

```text
[Authorize(Roles = "Editor,Admin")]
  匿名=401，無角色=403，Editor=200，Admin=200，Editor+Admin=200
[Authorize(Roles = "Editor")] 加 [Authorize(Roles = "Admin")]
  匿名=401，無角色=403，Editor=403，Admin=403，Editor+Admin=200
```

逗號分隔是 OR：持有任何一個即可，逗號後的空白不影響結果。疊多個 attribute 是 AND：每個 attribute 各自是一道要求，全部都要通過，只有同時具備兩個角色的人才是 200。類別上的 `Roles = "Editor"` 加 action 上的 `Roles = "Admin"` 也是同樣的 AND。policy 的 `RequireRole("Editor", "Admin")` 是 OR，`RequireRole("Editor").RequireRole("Admin")` 是 AND，邏輯與 attribute 一致。

在實務中，「Editor 或 Admin 都可以」是最常見的需求，寫成 `Roles = "Editor,Admin"`；「必須同時是兩者」很罕見。但更可持久的做法是 TaskTracker 採用的：把角色轉成權限 claim，每個 endpoint 只要求一個 policy，不用再為角色清單吵架（[[basics-13-permissions-with-frontend]]、[[14-authorization]]）。

另外 `[Authorize]` 用 `Roles` 需要 JWT 的 role claim 對得上 `RoleClaimType`，TaskTracker 的 token 驗證參數設了 `RoleClaimType = "role"`（[[basics-12-jwt-login]]）。

---

## 七、回應與文件：告訴呼叫端會得到什麼

這組 attribute 的讀者有兩種。一種是 OpenAPI 文件產生器，在要求文件時讀，用來描述 API 的回應形狀；另一種是 MVC 的 formatter 與 routing，在請求處理時讀，會真的改變行為。把它們混成「全部只是給 Swagger 看的」是個典型誤解，下面逐個區分。

| Attribute | 作用 | 何時生效 | 常見誤解 |
| --- | --- | --- | --- |
| `[ProducesResponseType<T>(201)]` | 宣告這個 action 可能回的 status code 與型別 | 只在產生文件時讀 | 以為寫了就會強制；其實 action 實際回什麼不受影響 |
| `[Produces("application/json")]` | 限制輸出用的 formatter 與 Content-Type | 請求處理時，會影響結果 | 以為只是文件 |
| `[Consumes("application/json")]` | 限制接受的 request Content-Type | 請求處理時 | 以為只是文件 |
| `[ApiExplorerSettings(IgnoreApi = true)]` | 不出現在 OpenAPI 文件 | 只在產生文件時 | 以為會讓 endpoint 無法呼叫 |
| `[ResponseCache(Duration = 60)]` | 加 `Cache-Control` 回應標頭 | 請求處理時 | 以為伺服器會快取 |

### `[ProducesResponseType]`：宣告，不強制

TaskTracker 的建立 action 這樣標：

```csharp
[ProducesResponseType<TaskResponse>(StatusCodes.Status201Created)]
[ProducesResponseType<ProblemDetails>(StatusCodes.Status409Conflict)]
```

泛型寫法（`[ProducesResponseType<T>(...)]`）從 .NET 7 開始支援，比 `typeof(T)` 寫法短。這些宣告最終出現在 OpenAPI 文件裡，前端產生器看得到 409 時回傳的是 `ProblemDetails`。它只描述，不強制：action 回 200 卻宣告 201，編譯過、執行過、客戶端收到 200，只有文件說謊。所以宣告的 status code 要與 action 實際回的一致。讀取（GET）宣告成 201 就是典型錯誤，讀取成功是 200。

`ActionResult<T>` 會讓文件產生器推斷出 200 與型別 `T`，因此成功回應常常不需要再寫 `[ProducesResponseType]`，寫的重點是失敗路徑（404、409 這些）。

### `[Produces]` 與 `[Consumes]`：會動到執行

在獨立專案實測，三個 action 都回匿名物件：

```text
GET /api/things/plain (Accept: application/xml) -> 200，Content-Type: application/json
GET /api/things/produces-json (Accept: application/xml) -> 200，Content-Type: application/json
GET /api/things/produces-xml (Accept: */*) -> 406 Not Acceptable
POST /api/things/consumes-json（Content-Type: text/plain） -> 415 Unsupported Media Type
POST /api/things/consumes-json（Content-Type: application/json） -> 200 OK
```

前兩行表示：預設的 MVC 只有 JSON formatter，沒有 XML，client 要求 XML 時不會 406，而是照給 JSON。`[Produces("application/json")]` 在這個預設設定下看不出差別，它的價值在於把 Content-Type 固定下來。第三行才露出它的本質：`[Produces("application/xml")]` 要求輸出 XML，而專案沒有註冊 XML formatter，框架找不到對應的 formatter，就回 406，執行期的 console 也有警告 `No output formatter was found for content types 'application/xml, application/xml' to write the response.`。可見 `[Produces]` 是執行期行為，不只是文件。

`[Consumes("application/json")]` 則在 Content-Type 不符時回 415，還沒進到 action。

### `[ResponseCache]`：只寫標頭

```text
GET /api/things/cached -> 200 OK | Cache-Control: public, max-age=60
GET /api/things/plain -> 200 OK | （沒有 Cache-Control）
```

`[ResponseCache(Duration = 60)]` 做的事就是輸出 `Cache-Control: public, max-age=60`，告訴瀏覽器與中間的 proxy 可以快取六十秒。它不會讓 ASP.NET Core 自己把回應存起來，那是 Response Caching middleware 的工作（`AddResponseCaching` 與 `UseResponseCaching`），而且該 middleware 不會快取帶 `Authorization` 標頭的請求。在 .NET 7 起的 output caching（`[OutputCache]`）是另一套機制。對需要登入的 API，`public` 的快取標頭尤其危險，會讓共用的 proxy 有機會把某個使用者的回應存起來給別人；需要快取個人化資料時，要明確設定 `Location = ResponseCacheLocation.None` 或用 `private`。

### 其他

`[ApiExplorerSettings(IgnoreApi = true)]` 在內建 OpenAPI 實測：被標的 action 不出現在 `/openapi/v1.json` 的 `paths`，同一個 controller 其他 action 正常出現。它影響的是文件，不是 routing。同樣在文件裡，`[ProducesResponseType<Dto>(200)]` 讓 `produces-json` 的 `200` 回應帶 `application/json` 與 `Dto` 的 schema。

### Swashbuckle 專屬的 attribute

TaskTracker 用的是 .NET 10 內建的 `Microsoft.AspNetCore.OpenApi`（[[basics-14-openapi-and-versioning]]）。很多教學的範例來自 Swashbuckle：`[SwaggerOperation]`、`[SwaggerResponse]`、`[SwaggerSchema]`、`[SwaggerTag]` 這類 attribute 屬於 `Swashbuckle.AspNetCore.Annotations` 套件，要在 Swashbuckle 啟用 annotations 才會被讀。內建 OpenAPI 的產生器不認得它們，貼上去編譯可以過（只要裝了套件），但文件沒有任何變化。上面這一節出現的 `[ProducesResponseType]`、`[Produces]`、`[Consumes]`、`[ApiExplorerSettings]`，則是 ASP.NET Core 本身的 attribute，兩套文件產生器都會讀。要在內建 OpenAPI 裡補描述，走 XML 註解或 document、operation transformer（TaskTracker 的 `BearerSecuritySchemeTransformer` 與 `SecurityRequirementOperationTransformer` 就是這樣做）。

---

## 八、版本：同一個資源的不同契約

API 版本 attribute 屬於 `Asp.Versioning.Mvc` 套件，不是 ASP.NET Core 框架本身。讀者是版本化套件的 routing 與 middleware，啟動時建立「這個 action 屬於哪個版本」的對照，請求時依 `ApiVersionReader` 設定從路徑、header 或 query 取出版本做比對。

| Attribute | 作用 | 常見誤解 |
| --- | --- | --- |
| `[ApiVersion(1.0)]` | 宣告這個 controller 支援 1.0 版 | 沒有 `AddApiVersioning` 就沒有人讀它 |
| `[MapToApiVersion(2.0)]` | 把某個 action 對應到 controller 宣告的其中一個版本 | 只有 controller 宣告多個版本時才需要 |
| `[ApiVersionNeutral]` | 不分版本，任何版本請求都接受 | 通常用在 health 這種和契約無關的端點 |

TaskTracker 的 controller 標 `[ApiVersion(1.0)]`，路由是 `api/v{version:apiVersion}/tasks`，`ApiVersionReader` 設成 `UrlSegmentApiVersionReader`，也就是版本在路徑裡。實際行為如下：

```text
GET /api/v1/tasks -> 200 OK，回應標頭 api-supported-versions: 1.0
GET /api/tasks -> 404 Not Found
GET /api/v2/tasks -> 404 Not Found
```

`ReportApiVersions = true` 才會多出 `api-supported-versions` 標頭，讓呼叫端看得到伺服器支援哪些版本。沒有版本的舊路徑 `/api/tasks` 是 404，因為路徑模板裡的 `v{version:apiVersion}` 是必要的一段；要讓舊客戶端繼續運作，需要另外設計過渡（[[basics-14-openapi-and-versioning]]）。版本化與 OpenAPI 的整合是 `AddApiExplorer(...).AddOpenApi()`，產生每個版本一份文件。

---

## 九、Filter 與其他行為控制

最後一組是各種「橫切」的行為：CORS、限流、請求大小、防偽、依賴注入的 filter。它們的共同點是讀者各不相同，所以最容易出現「attribute 寫了但沒反應」的狀況。表格先列清楚誰在讀：

| Attribute | 讀者 | 前提 |
| --- | --- | --- |
| `[EnableCors("name")]`、`[DisableCors]` | CORS middleware | `AddCors` 註冊 policy、pipeline 有 `UseCors()` |
| `[EnableRateLimiting("name")]`、`[DisableRateLimiting]` | Rate limiting middleware | `AddRateLimiter` 註冊 policy、pipeline 有 `UseRateLimiter()` |
| `[RequestSizeLimit(n)]`、`[RequestFormLimits]` | MVC filter，限制該 action 的 body 與表單大小 | 單位是位元組；沒標時 Kestrel 預設 body 上限約 30 MB |
| `[ServiceFilter(typeof(T))]`、`[TypeFilter(typeof(T))]` | MVC filter pipeline | `ServiceFilter` 要求 T 已註冊到 DI；`TypeFilter` 不用 |
| `[IgnoreAntiforgeryToken]` | 防偽 filter | cookie 驗證的 API 才需要防偽 |

CORS 與 rate limiting 在獨立專案裡實測。註冊一個名為 `open` 的 CORS policy（只允許 `http://example.test`），並只在一個 action 上標 `[EnableCors("open")]`：

```text
GET /api/things/cors-open (Origin: http://example.test) -> 200 | Access-Control-Allow-Origin: http://example.test
GET /api/things/plain (Origin: http://example.test) -> 200 | （沒有 Access-Control-Allow-Origin）
```

沒標的 action 不會帶 CORS 標頭。CORS policy 的白名單與預設 policy 的取捨，在 [[basics-09-configuration-and-environments]] 做了處理。

限流的測試用「每分鐘一次」的 fixed window policy，標在 controller 類別上，其中一個 action 另外標 `[DisableRateLimiting]`：

```text
GET /api/limited/a #1 -> 200 OK
GET /api/limited/a #2 -> 503 Service Unavailable
GET /api/limited/free #1 -> 200 OK
GET /api/limited/free #2 -> 200 OK
```

第二次請求被拒絕，狀態碼是 503，不是多數人預期的 429。`RateLimiterOptions.RejectionStatusCode` 的預設值就是 503，要回 429 必須明確設定 `options.RejectionStatusCode = StatusCodes.Status429TooManyRequests`。這是一個沒設定就會讓呼叫端誤判成「伺服器壞了」的預設值。`[DisableRateLimiting]` 如預期讓該 action 不受類別層級限流影響。

`[IgnoreAntiforgeryToken]` 的前提要記清楚：防偽 token 是為了擋 CSRF，這個攻擊依賴瀏覽器會自動帶上 cookie。用 `Authorization: Bearer` 標頭的 API，瀏覽器不會自動帶，所以不需要；但如果你的 API 用 cookie 驗證，就不能隨便忽略。`[ServiceFilter]` 與 `[TypeFilter]` 的差別、filter 的執行順序與短路，完整的推導在 [[05-filters-and-mvc-internals]]。

---

## 常見誤解

**「Controller 與 Action 有同一個 attribute 時，Action 層級優先。」** 沒有通則。`[Authorize]` 兩層疊加，每一個都要通過；`[AllowAnonymous]` 放在任何一層都蓋過所有 `[Authorize]`；`[Route]` 與 `[HttpGet]` 的 template 是串接。實測中，類別上 `[AllowAnonymous]` 加 action 上 `[Authorize]`，匿名請求照樣 200。

**「`[Route("api/[controller]")]` 的 `[controller]` 會變小寫，而且路由比對區分大小寫。」** 都不對。它展開成 `Users` 這種 PascalCase，比對不分大小寫，`/API/USERS` 一樣是 200。大小寫只出現在產生出來的 `Location` 與 OpenAPI path，要小寫設 `LowercaseUrls`。

**「`Roles = "A,B"` 要同時是 A 與 B。」** 剛好相反：逗號是 OR。要 AND 需要疊多個 `[Authorize(Roles = ...)]`，實測只有同時具備兩個角色的使用者才是 200。

**「`[ApiController]` 只是多了自動 400。」** 它還改變了複合型別的預設綁定來源：有它時 GET 搭配複合型別沒有 body 就是 415；沒有它時 POST 的 JSON body 綁不進來，欄位全是預設值卻回 200。

**「`[BindNever]` 可以防止 over-posting。」** 只對 query、route、form 這些經過 model binding 的來源有效。JSON body 由 `System.Text.Json` 處理，標了 `[BindNever]` 的 `IsAdmin` 仍被設成 `true`；要排除用 `[JsonIgnore]`，或乾脆不要把它放進請求 DTO。

---

## 同事會來問你的問題

**Q：attribute 放在 class 上和 action 上，到底差在哪？**
放在 class 上是套用到整個 controller 的所有 action，放在 action 上只管那一支。合併方式依 attribute 而定：`[Authorize]` 疊加，`[AllowAnonymous]` 一出現就蓋過全部，`[Route]` 串接。設計上，讓預設最安全：類別上放限制（`[Authorize]`），個別 action 放寬（`[AllowAnonymous]`），不要反過來。

**Q：我標了 `[EnableCors]`（或 `[EnableRateLimiting]`），但沒反應，為什麼？**
先檢查讀它的 middleware 在不在：CORS 需要 `AddCors` 加 `UseCors()`，限流需要 `AddRateLimiter` 加 `UseRateLimiter()`，授權需要 `UseAuthorization()`。attribute 本身不會報錯。再檢查名稱是否與註冊的 policy 一致，以及 middleware 的順序是否在 endpoint 之前（[[01-request-pipeline]]）。

**Q：Swagger 教學裡的 `[SwaggerOperation]`，在內建 OpenAPI 能用嗎？**
不能。它屬於 `Swashbuckle.AspNetCore.Annotations` 套件，只有 Swashbuckle 讀它。內建的 `Microsoft.AspNetCore.OpenApi` 讀 ASP.NET Core 本身的 attribute（`[ProducesResponseType]`、`[Produces]`、`[ApiExplorerSettings]` 等）、XML 註解與 transformer。專案換用內建 OpenAPI 時，這類 attribute 要改寫成 XML 註解或 transformer。

**Q：`[ProducesResponseType]` 不寫會怎樣？**
執行行為完全不變，只是 OpenAPI 文件缺了那條回應，前端產生的型別就少了錯誤分支。建議至少把非預期成功的路徑（404、409）寫上。

**Q：attribute 的順序有影響嗎？**
不要依賴。同一個 action 上的 `[Authorize]` 疊多個，結果與書寫順序無關（全部都要通過）。需要順序的是 filter，用 `Order` 屬性明確指定，不靠書寫位置。

---

## 這章的位置

學完這一章，你手上有一份分組的 attribute 查閱表，也知道遇到「attribute 沒反應」時該怎麼排查：先找讀者是誰、再看讀者有沒有在 pipeline 裡、最後看合併規則。常被誤解的四件事——`[AllowAnonymous]` 的優先關係、`[controller]` 的大小寫、`Roles` 的 OR 與 AND、`[ApiController]` 的推斷——都已經用實測校正過。這份清單可以隨著專案成長回來查，也可以當作程式審查時的對照。

入門篇到此結束。TaskTracker 從一個空的 `dotnet new` 專案，走到有 Oracle、JWT、權限、OpenAPI、測試與 Docker 的狀態。接下來的深度篇不再往 TaskTracker 加功能，而是回頭拆開前面用過的每個機制，從 Host 內部怎麼啟動與關閉開始：[[00-hosting-and-startup]]。

---

## 連結

- 上一章：[[basics-16-deployment-and-go-live]]
- 下一章：[[00-hosting-and-startup]]
- 對應深度章：[[03-routing-and-endpoints]]、[[04-model-binding-and-validation]]、[[05-filters-and-mvc-internals]]、[[14-authorization]]
- 相關入門章：[[basics-04-controllers-and-routing]]、[[basics-05-model-binding-and-validation]]、[[basics-11-auth-concepts-and-pipeline]]、[[basics-14-openapi-and-versioning]]
- 總目錄：[[dotnet-web-api]]
