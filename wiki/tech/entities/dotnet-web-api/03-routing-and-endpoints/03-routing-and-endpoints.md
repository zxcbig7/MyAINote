---
type: concept
domain: tech
tags: [dotnet, aspnet, routing, endpoint, minimal-api, controller, url-matching]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 03 章：Routing 與 Endpoint — 路徑怎麼變成一段程式碼

## 三個看起來沒問題的路由

```csharp
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet("{id}")]
    public IActionResult GetById(int id) => Ok();

    [HttpGet("active")]
    public IActionResult GetActive() => Ok();

    [HttpGet("{name}")]
    public IActionResult GetByName(string name) => Ok();
}
```

啟動沒問題。呼叫 `/api/users/active` 會發生什麼？

多數人的直覺是「`active` 是字面字串，應該匹配 `GetActive`」。這個直覺**是對的**，但理由不是「因為它排在中間」，而是路由有一套明確的優先序規則。

那 `/api/users/5` 呢？`{id}` 和 `{name}` 都能匹配 `5`——這裡就會拋 `AmbiguousMatchException: The request matched multiple endpoints`。應用程式啟動時完全沒有警告，直到有人打了這個網址才在執行期炸開。

而如果把 `{id}` 改成 `{id:int}`，`/api/users/5` 就明確走 `GetById`，`/api/users/john` 走 `GetByName`——衝突消失了。

這三個現象背後是同一套規則。這一章要把它講清楚，順帶回答一個更根本的問題：**Controller 和 Minimal API 到底是不是同一個東西？**

---

## 一、Endpoint：路由系統的核心名詞

ASP.NET Core 2.2 起引入了 **Endpoint Routing**，它把「一個可以被請求執行的東西」抽象成 `Endpoint` 物件。一個 Endpoint 包含三樣東西：

| 組成 | 內容 |
| --- | --- |
| `RequestDelegate` | 真正要執行的程式碼 |
| `RoutePattern` | 什麼樣的路徑會匹配到它 |
| `EndpointMetadata` | 一堆附加資訊：`[Authorize]`、`[HttpGet]`、CORS policy、限流策略、Swagger 描述… |

第三項是理解 endpoint routing 設計的關鍵。在舊的 MVC 路由裡，「這個 action 需不需要授權」這種資訊只有 MVC 內部知道，pipeline 上的 middleware 看不到。Endpoint routing 把這些資訊**提升到 metadata**，讓路由選擇之後、執行之前的所有 middleware 都能查詢。

這正是第 01 章講的兩階段設計的目的：

```csharp
app.UseRouting();        // 階段一：選出 Endpoint，放進 HttpContext
// ↓ 這中間的 middleware 都能呼叫 ctx.GetEndpoint() 查 metadata
app.UseAuthorization();  // 讀 metadata 裡的 [Authorize] 決定要不要放行
app.MapControllers();    // 階段二：執行選中的 Endpoint
```

所有 endpoint 的來源是 `EndpointDataSource`。`MapControllers()` 註冊一個掃描所有 Controller 的資料來源，`MapGet(...)` 直接加一筆。應用程式啟動時這些來源被彙整成一張表，交給 matcher。

---

## 二、Route Template：路徑模板的完整語法

```csharp
[HttpGet("orders/{orderId:int}/items/{itemId:int?}")]
```

模板由 **segment**（用 `/` 分隔）組成，每個 segment 可以是字面字串或參數。

| 語法 | 意義 | 匹配範例 |
| --- | --- | --- |
| `orders` | 字面字串，必須完全相同（大小寫不敏感） | `/orders` |
| `{id}` | 必填參數 | `/5`、`/abc` |
| `{id?}` | 可選參數，**只能放在模板最後** | `/5` 或空 |
| `{id=1}` | 有預設值，等同可選但填入預設 | 空 → `id = 1` |
| `{id:int}` | 帶 constraint | `/5`（`/abc` 不匹配） |
| `{*rest}` | Catch-all，吃掉剩餘全部路徑 | `/a/b/c` → `rest = "a/b/c"` |
| `{**rest}` | Catch-all，且產生 URL 時不編碼斜線 | 同上 |
| `{{` `}}` | 跳脫，代表字面的大括號 | — |

幾個容易踩的細節：

**可選參數只能在最後。** `{a?}/{b}` 是無效的——如果 `a` 省略，路徑會變成 `/value`，無法判斷那個值是 `a` 還是 `b`。啟動時就會拋例外。

**一個 segment 裡可以有多個參數，但不能相鄰。** `{name}-{ext}` 合法（用 `-` 分隔）；`{name}{ext}` 不合法，因為無法決定邊界在哪。

**Catch-all 會吃掉斜線。** 這是它和一般參數最大的差異，一般參數不會跨 segment。

---

## 三、Constraint 不是驗證

```csharp
[HttpGet("{id:int:min(1)}")]
public IActionResult GetById(int id)
```

常見的 constraint：

| Constraint | 說明 |
| --- | --- |
| `:int` `:long` `:bool` `:guid` `:datetime` `:decimal` | 型別 |
| `:min(n)` `:max(n)` `:range(a,b)` | 數值範圍 |
| `:minlength(n)` `:maxlength(n)` `:length(n)` | 字串長度 |
| `:alpha` | 只有英文字母 |
| `:regex(pattern)` | 正規表示式 |
| `:required` | 非空 |

這裡有一個觀念必須說清楚，因為誤解它會導致真正的安全與可用性問題：

**Constraint 的用途是「消歧義」，不是「驗證輸入」。**

差別在失敗時的行為。`{id:int}` 遇到 `/api/users/abc` 時，這個 endpoint **不匹配**——路由系統會繼續找別的 endpoint，都找不到就回 **404**。它不會回 400，也不會告訴使用者「id 必須是整數」。

從 API 設計的角度，這通常不是你要的。使用者傳了格式錯誤的參數，語意上是 `400 Bad Request`，回 404 會讓人以為資源不存在。

所以規則是：

- **需要區分兩個競爭路由**（像本章開頭的 `{id}` vs `{name}`）→ 用 constraint
- **需要驗證業務規則**（年齡必須大於 18、email 格式）→ 用 model validation，回 400 並附帶錯誤訊息（見 [[04-model-binding-and-validation]]）

`:regex(...)` 還有一個實務陷阱：正規表示式裡的 `\` 在 C# 字串裡要跳脫，模板裡的 `{` `}` 也要跳脫成 `{{` `}}`，寫出來的東西幾乎不可讀，而且複雜的 regex 有 ReDoS（正規表示式阻斷服務）風險——攻擊者用精心構造的輸入讓比對進入指數時間。路由層是每個請求都會經過的地方，這個風險不容忽視。需要複雜格式檢查時，放到驗證層而不是路由層。

---

## 四、優先序：`/api/users/active` 為什麼走對了

當多個 endpoint 都能匹配同一個路徑時，路由系統依序比較每個 segment，規則是：

```text
字面字串  >  有 constraint 的參數  >  無 constraint 的參數  >  catch-all
```

從左到右逐 segment 比較，第一個分出高下的 segment 決定勝負。

用開頭的例子驗證，請求 `/api/users/active`：

| 候選 | 第三個 segment | 等級 |
| --- | --- | --- |
| `api/users/active` | 字面字串 | 最高 |
| `api/users/{id}` | 無 constraint 參數 | 較低 |
| `api/users/{name}` | 無 constraint 參數 | 較低 |

`active` 勝出，走 `GetActive`。直覺是對的，但理由是規則而非撰寫順序——**把 `GetActive` 移到檔案最下面，結果完全一樣**。

再看 `/api/users/5`：字面路由不匹配，剩下 `{id}` 和 `{name}` 都是「無 constraint 參數」，**同級**。同級且都匹配 → `AmbiguousMatchException`。

加上 constraint 之後：

```csharp
[HttpGet("{id:int}")]
public IActionResult GetById(int id) => Ok();

[HttpGet("{name}")]
public IActionResult GetByName(string name) => Ok();
```

`/api/users/5` → `{id:int}` 是「有 constraint 參數」，等級高於 `{name}`，勝出。
`/api/users/john` → `{id:int}` 根本不匹配，只剩 `{name}`，也不需要比較。

衝突消失了。這是 constraint 作為消歧義工具最典型的用法。

### 4.1 用 Order 強制覆蓋

真的無法用 constraint 分辨時，可以手動指定順序（數字小的優先）：

```csharp
[HttpGet("{name}", Order = 1)]
```

但這應該是最後手段。`Order` 讓路由行為依賴於一個散落在各處的數字，新人讀 code 時很難看出全貌。能用 constraint 或重新設計 URL 結構解決的，就別用 `Order`。

### 4.2 HTTP 方法也參與比對

`[HttpGet]` 和 `[HttpPost]` 產生的 metadata 會參與匹配。同一個路徑上 GET 和 POST 各有一個 action 完全沒問題，那不是衝突。

值得注意的是，如果路徑匹配但方法不匹配（例如對只有 `[HttpGet]` 的路徑送 POST），框架回 **405 Method Not Allowed** 而不是 404。這是正確的 HTTP 語意，前端偵錯時看到 405 就該往「方法用錯了」而不是「網址錯了」的方向查。

---

## 五、Attribute Routing 的細節

Web API 幾乎都用 attribute routing（把路由寫在 action 上），而不是 MVC 傳統的 `MapControllerRoute` 慣例路由。原因是 API 的 URL 結構通常不規則，用一條慣例套不住。

### 5.1 Token 替換

```csharp
[Route("api/[controller]")]        // → api/Users
[Route("api/v1/[controller]/[action]")]
```

`[controller]` 會替換成 controller 類別名去掉 `Controller` 後綴的部分（`UsersController` → `Users`），大小寫照類別名稱原樣保留，不會自動轉小寫。路由比對不分大小寫，所以 `/api/users` 照樣打得通；大小寫只會出現在產生出來的 URL（例如 `CreatedAtAction` 的 `Location`）與 OpenAPI 的 path 上，要統一成小寫得靠第八節的 `LowercaseUrls`。這帶來一個常被忽略的耦合：**改類別名字會改變 API 網址**。重新命名一個 controller 是純內部重構，但它會靜默地破壞所有呼叫端。

在對外 API 上，建議把路徑寫死：

```csharp
[Route("api/users")]              // 明確，重新命名類別不影響對外契約
```

`[action]` 更不建議用在 REST API 上——REST 的語意由 HTTP 方法承載，把方法名放進 URL（`/api/users/getbyid`）是 RPC 風格，兩種風格混用會讓 API 難以理解。

### 5.2 相對與絕對路徑

Action 上的模板預設是**相對**於 controller 上的模板。要跳脫這個組合，用 `/` 或 `~/` 開頭：

```csharp
[Route("api/users")]
public class UsersController : ControllerBase
{
    [HttpGet("{id}")]              // → api/users/{id}
    public IActionResult Get(int id) => Ok();

    [HttpGet("/health/users")]     // → health/users（絕對，忽略 controller 模板）
    public IActionResult Health() => Ok();
}
```

### 5.3 `[ApiController]` 帶來什麼

這個 attribute 不只是標記，它啟動了一組行為：

| 行為 | 效果 |
| --- | --- |
| 自動 400 | `ModelState` 無效時自動回 `400` + `ValidationProblemDetails`，不需要手寫 `if (!ModelState.IsValid)` |
| 推斷 binding source | 複雜型別參數自動視為 `[FromBody]`，簡單型別自動從路由/query 取 |
| 要求 attribute routing | 該 controller 不能用慣例路由 |
| 錯誤回應格式 | 統一使用 `ProblemDetails`（RFC 7807） |

第二項在 [[04-model-binding-and-validation]] 詳談，因為推斷規則有幾個容易誤判的邊界。第一項的自動 400 可以關閉或客製，這在需要統一錯誤格式時常用：

```csharp
builder.Services.Configure<ApiBehaviorOptions>(options =>
{
    options.SuppressModelStateInvalidFilter = true;   // 關掉自動 400，自己處理
});
```

---

## 六、Minimal API：底層是同一套嗎

```csharp
app.MapGet("/api/users/{id:int}", async (int id, IUserService svc) =>
{
    var user = await svc.GetByIdAsync(id);
    return user is null ? Results.NotFound() : Results.Ok(user);
});
```

**是同一套路由。** `MapGet` 建立的一樣是 `Endpoint`，一樣進同一張表，一樣走同樣的優先序規則。所以 Minimal API 和 Controller 可以在同一個應用程式裡混用，路由會統一排序，甚至會互相衝突。

差別在 endpoint 內部那個 `RequestDelegate` 是怎麼來的。

| | Controller | Minimal API |
| --- | --- | --- |
| 執行者 | MVC 的 action invoker | 直接呼叫委派 |
| Filter pipeline | 完整五種 Filter（見 [[05-filters-and-mvc-internals]]） | 只有 endpoint filter（.NET 7+），較簡化 |
| Model binding | 完整 MVC binder，支援複雜情境 | 簡化版，支援 `TryParse` / `BindAsync` 自訂 |
| 自動 400 驗證 | `[ApiController]` 提供 | **沒有**，要自己驗或裝套件 |
| 每請求開銷 | 較高（invoker、filter、reflection） | 較低 |
| 適合 | 大型 API、需要豐富 filter | 小型服務、健康檢查、高吞吐端點 |

最大的實務差異是**驗證**。Controller + `[ApiController]` 會自動把 `ModelState` 錯誤轉成 400；Minimal API 沒有這層，`[Required]` 之類的 DataAnnotations 預設完全不會被檢查。從 Controller 搬程式碼到 Minimal API 時，這是最容易漏掉的一環——驗證屬性還在，但不再生效，無效資料就這樣進了資料庫。

Minimal API 的參數綁定規則也比較直白，值得記住：

```text
1. 路由模板裡有同名參數 → 從路由取
2. 型別是特殊型別（HttpContext、CancellationToken、ClaimsPrincipal）→ 直接給
3. 型別註冊在 DI 裡 → 從 DI 解析
4. 簡單型別（有 TryParse）→ 從 query string 取
5. 其他 → 從 body 取（JSON），且一個 handler 最多一個
```

第 3 條和第 5 條的互動是常見困惑來源：一個沒註冊在 DI 的複雜型別會被當成 body，但如果剛好註冊了同型別的服務，就變成從 DI 取——同一段程式碼在別的專案行為不同。需要明確時就加 `[FromBody]` / `[FromServices]`，別依賴推斷。

### 6.1 Route Groups

```csharp
var users = app.MapGroup("/api/users")
    .RequireAuthorization()
    .WithTags("Users");

users.MapGet("/", GetAllAsync);
users.MapGet("/{id:int}", GetByIdAsync);
users.MapPost("/", CreateAsync);
```

`MapGroup` 把共同的路徑前綴、授權需求、metadata 一次套用到組內所有 endpoint。這是 Minimal API 在 .NET 7 之後真正變得可用於中型專案的關鍵功能——沒有它的話，每個 endpoint 都要重複寫 `.RequireAuthorization()`。

---

## 七、產生 URL：比想像中容易出錯

路由是雙向的：比對進來的 URL，也產生出去的 URL。

```csharp
[HttpPost]
public async Task<IActionResult> CreateAsync([FromBody] CreateUserDto dto)
{
    var user = await _userService.CreateAsync(dto);
    return CreatedAtAction(nameof(GetByIdAsync), new { id = user.Id }, user);
}
```

`CreatedAtAction` 回 `201 Created` 並在 `Location` header 放上新資源的 URL——這是 REST 的標準做法。但它有一個惡名昭彰的陷阱：

**`nameof(GetByIdAsync)` 產生的字串是 `"GetByIdAsync"`，但 MVC 在建立路由表時會把 action 名稱的 `Async` 後綴移除**（`SuppressAsyncSuffixInActionNames` 預設為 true）。於是路由表裡登記的是 `GetById`，用 `"GetByIdAsync"` 去找找不到，執行期拋 `InvalidOperationException: No route matches the supplied values`。

三種解法：

```csharp
// 解法 1：不要用 nameof，直接寫去掉 Async 的名字（脆弱，改名不會被編譯器抓到）
return CreatedAtAction("GetById", new { id = user.Id }, user);

// 解法 2：關掉後綴移除行為（全域一致，推薦）
builder.Services.AddControllers(options =>
{
    options.SuppressAsyncSuffixInActionNames = false;
});

// 解法 3：用具名路由（明確，不依賴方法名）
[HttpGet("{id:int}", Name = "GetUserById")]
public async Task<IActionResult> GetByIdAsync(int id) { }

return CreatedAtRoute("GetUserById", new { id = user.Id }, user);
```

解法 3 最穩健：路由名稱是明確的契約，重構方法名不會影響它。

在 controller 之外（例如 background service 產生 email 裡的連結）要產生 URL 時，注入 `LinkGenerator`：

```csharp
var url = _linkGenerator.GetUriByName(
    httpContext, "GetUserById", new { id = 42 });
```

沒有 `HttpContext` 的情境（背景服務）必須明確提供 scheme 與 host，因為那些資訊本來是從當前請求推導的。實務上這個 base URL 應該來自設定而不是猜測——在反向代理後面，請求裡的 host 可能是內部位址而非對外網域。

---

## 八、大小寫、尾斜線與正規化

**路徑比對是大小寫不敏感的。** `/api/Users` 和 `/api/users` 都能匹配。但**產生**的 URL 預設保留你寫的大小寫，於是同一個資源可能出現兩種寫法，對快取和記錄分析都不理想。要統一成小寫：

```csharp
builder.Services.AddRouting(options =>
{
    options.LowercaseUrls = true;
    options.LowercaseQueryStrings = true;
});
```

**尾斜線在比對時會被忽略。** `/api/users` 和 `/api/users/` 命中的是同一個 endpoint（實測兩者都回 200），不會因為多一個斜線而 404。`options.AppendTrailingSlash` 只影響產生的 URL，不影響比對。如果希望對外只留一種寫法（為了快取或 SEO），需要在 middleware 層做 URL 正規化或 redirect，或交給反向代理處理。

**Query string 完全不參與路由比對。** `?page=2` 對選哪個 endpoint 沒有任何影響，它是 model binding 階段的事。想用 query 參數區分不同 endpoint（例如 `?format=xml` 走另一個 action），路由層做不到，要靠自訂的 `IActionConstraint` 或在 action 內部分支。

---

## 九、常見誤解

**「路由按撰寫順序比對，先寫的先贏。」**
不是。順序由優先序規則決定：字面 > 有 constraint 參數 > 無 constraint 參數 > catch-all。撰寫順序完全不影響結果（除非明確指定 `Order`）。

**「加了 `{id:int}` 就等於驗證了 id 是數字。」**
Constraint 不匹配時的結果是「這個 endpoint 不適用」，最終通常回 404 而非 400，而且沒有錯誤訊息。它是消歧義工具，不是驗證工具。

**「Minimal API 只是語法糖，行為和 Controller 一樣。」**
路由層一樣，執行層不一樣。最關鍵的差異是 Minimal API **沒有自動的 ModelState 驗證**——`[Required]` 等屬性預設不生效。

**「`[controller]` token 很方便，到處用。」**
它把類別名稱變成對外 API 契約的一部分，重新命名類別會靜默破壞呼叫端。對外 API 建議把路徑寫死。

**「`CreatedAtAction(nameof(GetByIdAsync), ...)` 很安全，有編譯期檢查。」**
`nameof` 確實有編譯期檢查，但它產生的字串包含 `Async` 後綴，而路由表裡的名稱已經去掉了。用具名路由 + `CreatedAtRoute` 才真正安全。

---

## 十、同事會來問你的問題

**Q：`AmbiguousMatchException` 是什麼意思，怎麼修？**
兩個以上的 endpoint 在優先序上同級且都匹配這個路徑。最常見的是 `{id}` 和 `{name}` 這種同形參數。加 constraint（`{id:int}`）讓其中一個等級升高，或重新設計 URL 讓它們不再重疊。

**Q：為什麼傳錯格式的 id 回 404 而不是 400？**
因為 `{id:int}` 是路由 constraint。不匹配代表「這個 endpoint 不適用」，路由繼續找別的，都找不到就 404。要回 400 就把型別檢查從路由移到參數驗證層。

**Q：`/api/users` 和 `/api/users/` 是同一個路徑嗎？**
是。路由比對會忽略尾斜線，兩者命中同一個 endpoint。如果要對外只保留一種寫法，才需要在 middleware 或反向代理層做 redirect。

**Q：我在 middleware 裡想知道這個請求會打到哪個 action，怎麼拿？**
`ctx.GetEndpoint()`，但這個 middleware 必須排在 `UseRouting` 之後，否則永遠是 null。拿到 endpoint 後可以從 `endpoint.Metadata` 取出 `[Authorize]`、`ControllerActionDescriptor` 等資訊。

**Q：`CreatedAtAction` 一直說找不到路由。**
`nameof(GetByIdAsync)` 帶了 `Async` 後綴，但路由表裡的 action 名稱已經被移除後綴。改用具名路由 + `CreatedAtRoute`，或設定 `SuppressAsyncSuffixInActionNames = false`。

**Q：Minimal API 和 Controller 該選哪個？**
中大型 API、需要完整 filter pipeline 與自動驗證，用 Controller。健康檢查、webhook 接收、追求極致吞吐的小端點，用 Minimal API。兩者可以在同一個專案共存，路由層是統一的。

**Q：想用 `?version=2` 來區分不同版本的 API，路由做得到嗎？**
路由不看 query string，做不到。API 版本控制的標準做法是路徑（`/api/v2/users`）或 header，用 `Asp.Versioning` 套件處理。見 [[21-deployment]]。

---

## 連結

- [[basics-04-controllers-and-routing]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[02-dependency-injection]] — 上一章：服務解析
- [[04-model-binding-and-validation]] — 下一章：參數怎麼被填進去、驗證怎麼回 400
- [[01-request-pipeline]] — `UseRouting` 在 pipeline 的位置
- [[05-filters-and-mvc-internals]] — endpoint 被選中之後 MVC 做了什麼
- [[21-deployment]] — API 版本控制
