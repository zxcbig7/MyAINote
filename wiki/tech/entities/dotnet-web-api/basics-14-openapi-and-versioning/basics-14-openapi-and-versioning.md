---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, openapi, scalar, swagger, api-versioning, asp-versioning, xml-documentation, jwt, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 9：Swagger、API 文件化與版本管理.md
  - raw/Web Framework/NET Web API/Swagger 在 HTTP Pipeline 中的位置與設計理由.md
  - https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/aspnetcore-openapi?view=aspnetcore-10.0
  - https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/customize-openapi?view=aspnetcore-10.0
created: 2026-10-31
updated: 2026-11-01
---

# 入門第 14 章：OpenAPI 與版本管理 — 讓前端自己讀懂 API，改版時別弄壞他們

## 一則聊天訊息，和一次悄悄的改名

前端同事在聊天室丟來一句話：「建立任務的 `status` 欄位，要傳 `Todo` 還是 `todo`？回應裡的 `createdAt` 有時區嗎？登入之後 token 要放哪個 header？」後端回答了一輪，隔天另一位前端同事問了幾乎一樣的問題。每個新來的人都要把這些問題再問一遍，答案散落在聊天紀錄裡，沒有人知道哪一則才是最新的。這是第一種代價：API 沒有一份隨時能查、保證和程式一致的說明，溝通成本會隨人數線性增加。

第二種代價更危險。後端同事覺得 `title` 這個欄位名稱太籠統，順手在 `TaskResponse` 裡改成 `name`，編譯通過，單元測試通過，部署上線。前端沒有任何錯誤訊息，畫面上每一筆任務的標題只是變成空白，因為 JavaScript 讀不到的欄位會安靜地變成 `undefined`。直到使用者回報才有人發現。改動的人沒有做錯任何「語法上」的事，他只是不知道有多少程式碼依賴那個名字，也沒有一套機制讓他在改之前知道。

[[basics-13-permissions-with-frontend]] 結束時，TaskTracker 已經有完整的登入與權限，前端可以動手串接了。這一章處理的就是上面這兩個問題：用 OpenAPI 文件讓前端不必再問，用版本管理讓後端改版時有一條不弄壞前端的路。過程中會順便清掉一個常見的混亂，就是「Swagger 在 pipeline 的哪個位置、會不會被 `[Authorize]` 擋住」，這個問題的答案很容易靠實測確認，不需要憑印象猜。

---

## 一、先把名詞分清楚：規格、工具、套件

OpenAPI 是一份規格，規定怎麼用 JSON（或 YAML）描述一支 HTTP API：有哪些路徑、接受什麼參數、回傳哪些狀態碼與 body、用什麼方式驗證身分。它只是描述格式，本身不會執行任何東西。這份規格早期叫 Swagger，後來改名為 OpenAPI；Swagger 今天指的是 SmartBear 公司的一組工具品牌，最有名的是 Swagger UI，把 OpenAPI 文件畫成可互動網頁。Scalar 是另一套同類的網頁工具，用途相同，介面比較新。

在 .NET 裡還有第三個層次：誰把 Controller 和 DTO 轉成 OpenAPI 文件。過去十年這件事大多由社群套件 Swashbuckle 負責，舊教材裡的 `AddSwaggerGen()`、`UseSwagger()` 都是它。.NET 9 起，`dotnet new webapi` 的範本不再包含 Swashbuckle，改為內建 `Microsoft.AspNetCore.OpenApi` 與 `AddOpenApi()`；.NET 10 的內建產生器預設輸出 OpenAPI 3.1。內建套件只產生 JSON 文件，不附網頁介面，介面要自己選：Swagger UI（`Swashbuckle.AspNetCore.SwaggerUi` 套件）或 Scalar（`Scalar.AspNetCore` 套件）都可以。Swashbuckle 專案本身仍在維護，現有專案用它沒有問題，只是新專案不再是預設選項。

所以「我們要用 Swagger」這句話在 2026 年有四種可能的意思，開會時先問清楚是要規格、產生器，還是網頁介面。TaskTracker 用內建的 `AddOpenApi()` 產生文件，用 Scalar 當介面。

常見的說法是「API 文件是前後端、外部系統溝通的唯一依據」，稍微過頭了。OpenAPI 文件是機器可讀的那一部分契約：路徑、參數、結構、狀態碼。但「每分鐘最多呼叫幾次」「某個欄位什麼情況下為 `null`」這類行為承諾不會自動出現在文件裡，需要文字說明補上。保留下來的是更重要的觀念：文件是契約的一部分，寫 API 卻不寫文件，等於交付一個不完整的系統。

---

## 二、`MapOpenApi` 是 endpoint：用實測釐清它在 pipeline 的位置

網路上關於 Swagger 的位置有一段流傳很廣的說法：Swagger 要放在 `UseAuthorization` 之前，否則 Swagger JSON 會被 `[Authorize]` 擋住；放在 `MapControllers()` 之後則「永遠不會被執行」。同一批文章又一下說 Swagger 是 endpoint，一下說它是 middleware。這幾句話彼此矛盾，而且和 .NET 6 之後的實際行為不符。與其比較誰的說法比較有道理，不如直接做實驗。

先弄清楚一個前提。[[basics-11-auth-concepts-and-pipeline]] 講過，`[Authorize]` 是掛在 Controller 或 action 上的 metadata，授權 middleware 在路由比對出 endpoint 之後，才讀取該 endpoint 身上的 metadata 來決定要不要放行。因此「某個路徑會不會被擋」取決於兩件事：這個路徑最後是不是對應到某個 endpoint，以及那個 endpoint 身上有沒有授權 metadata。

內建的 `MapOpenApi()` 名字裡有 `Map`，它註冊的是一個 endpoint（回傳值是 endpoint 的 convention builder，可以繼續接 `RequireAuthorization()` 這類方法）。下面這支最小程式（建一個全新的 `dotnet new web` 專案，加入 `Microsoft.AspNetCore.Authentication.JwtBearer` 套件即可執行，與 TaskTracker 無關）把「授權 middleware 在前、`MapOpenApi` 在後」的情境都放進去，並分別測三種設定：

```csharp
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication().AddJwtBearer();
builder.Services.AddAuthorization();
builder.Services.AddOpenApi();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapOpenApi();
app.MapGet("/secure", () => "secret").RequireAuthorization();
app.MapGet("/public", () => "hello");

app.Run();
```

三種設定分別是：上面這份原樣、在 `MapOpenApi()` 後面接 `.RequireAuthorization()`、以及在 `AddAuthorization` 裡設定 `FallbackPolicy`（要求所有沒有指定授權設定的 endpoint 都必須登入）。不帶 token 發請求，三種設定下各路徑的狀態碼是：

```text
plain /openapi/v1.json -> 200
plain /secure -> 401
plain /public -> 200
protect /openapi/v1.json -> 401
protect /secure -> 401
protect /public -> 200
fallback /openapi/v1.json -> 401
fallback /secure -> 401
fallback /public -> 401
```

第一組說明了上述說法不成立。`UseAuthorization()` 明明排在 `MapOpenApi()` 之前，`/openapi/v1.json` 卻回 200，因為這個 endpoint 身上沒有任何授權 metadata，授權 middleware 看了一眼就放行。`/secure` 同樣經過授權 middleware，只因為它自己宣告了 `RequireAuthorization()` 才回 401。換句話說，擋人的不是「Swagger 排在授權的前面還是後面」，而是 endpoint 身上有沒有被標上要求。

第二組證明了 `MapOpenApi` 確實是 endpoint：只有 endpoint 才能對它宣告 `RequireAuthorization()`，宣告之後它就像 `/secure` 一樣被擋。第三組則說明了真正會「意外」擋掉文件的情況：`FallbackPolicy` 或對整個 route group 套用授權，會一視同仁地套在所有沒有明確例外的 endpoint 上，包含文件和 `/public`。如果團隊設了全域登入要求，又想公開文件，就必須在 `MapOpenApi()` 後面接 `.AllowAnonymous()`。

至於「`Map*` 之後的 middleware 不會執行」，這是 .NET 5 以前 `UseEndpoints` 時代的圖像。在 .NET 6 以後的 `WebApplication`，`Map*` 只是註冊 endpoint，真正執行 endpoint 的步驟由框架補在 pipeline 的最後，所以寫在 `MapControllers()` 之後的 middleware 依然會在 endpoint 之前執行（`Use*` 與 `Map*` 的細節見 [[01-request-pipeline]]）。把 `Map*` 放在最後是慣例，不是不這樣寫就會失效。

Swashbuckle 的 `UseSwagger()` 與 `UseSwaggerUI()` 則是另一種東西：它們是一般 middleware，檢查請求路徑符合時直接寫出回應，不經過 endpoint routing。這是兩個看起來相似的 API 本質上的差別，也是許多文章把兩者混在一起說的原因。使用內建的 `MapOpenApi()`，就用 endpoint 的規則思考，用 metadata 控制誰能存取，不需要再糾結先後順序。

---

## 三、正式環境要不要開放文件

TaskTracker 的 `Program.cs` 把文件與 Scalar 放在 `IsDevelopment()` 判斷裡，也就是只有開發環境才存在。這是範本的預設寫法，並不是框架強制。要不要在正式環境開放，答案取決於誰會看這份文件。

一般的建議有三個理由，它們成立：第一，文件會暴露所有路徑、DTO 結構與參數，對一支公開在網際網路上的 API 來說，等於把規格書交給所有探測的人，攻擊者省下了大量猜測的時間。第二，文件的受眾是開發者、前端與 QA，不是終端使用者，正式環境沒有人需要打開它。第三，正式環境有更合適的替代品：在 CI 裡產生 OpenAPI JSON 檔，交給 Postman、Redoc 或內部文件網站，文件流通的範圍可以另外控制。

這三個理由有一個前提：API 只服務自己的前端。如果你的 API 本來就是要給外部合作夥伴整合的產品，文件就是產品的一部分，應該公開（或至少放在登入後的開發者入口）。判準很簡單：誰是這份文件的讀者，就讓誰讀得到，其他人讀不到。

要在正式環境保留文件、又不想對全世界公開時，用 `app.MapOpenApi().RequireAuthorization("某個 policy")`，把文件當成一般的受保護 endpoint；Scalar 的介面頁面同樣用 endpoint 的方式保護。代價是網頁介面讀文件時也需要 token，適合有權限管理的內部網站。多數只服務自家前端的 API，用環境判斷關掉，再用 CI 輸出文件檔，是最省事的組合。

---

## 四、讓文件知道哪些端點要登入：JWT security scheme

打開 Scalar 後，前端同事會想直接按「試用」呼叫 `POST /api/v1/tasks`，這時候文件必須告訴工具兩件事：這支 API 用 Bearer token 驗證（定義一次），以及哪些端點需要它（登入端點不需要）。OpenAPI 把前者稱為 security scheme，後者稱為 security requirement。內建的產生器不會自動從 `[Authorize]` 推導這些資訊，要用 transformer 補。

transformer 是內建 OpenAPI 提供的擴充點：產生文件的過程中，會在不同層級呼叫你的程式，讓你修改結果。文件層級的 transformer（`IOpenApiDocumentTransformer`）適合放「整份文件只有一份」的東西，像 security scheme 的定義；操作層級的 transformer（`IOpenApiOperationTransformer`）每個端點呼叫一次，適合放「每個端點不同」的東西，像是否需要登入。TaskTracker 兩個都用。

定義 scheme 的文件 transformer：

```csharp
using Microsoft.AspNetCore.OpenApi;
using Microsoft.OpenApi;

namespace TaskTracker.Api.OpenApi;

internal sealed class BearerSecuritySchemeTransformer : IOpenApiDocumentTransformer
{
    public Task TransformAsync(OpenApiDocument document, OpenApiDocumentTransformerContext context, CancellationToken cancellationToken)
    {
        document.Components ??= new OpenApiComponents();
        document.Components.SecuritySchemes ??= new Dictionary<string, IOpenApiSecurityScheme>();
        document.Components.SecuritySchemes["Bearer"] = new OpenApiSecurityScheme
        {
            Type = SecuritySchemeType.Http,
            Scheme = "bearer",
            BearerFormat = "JWT",
            Description = "Access token returned by POST /api/v1/auth/login."
        };
        return Task.CompletedTask;
    }
}
```

宣告哪些端點要登入的操作 transformer：

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.OpenApi;
using Microsoft.OpenApi;

namespace TaskTracker.Api.OpenApi;

internal sealed class SecurityRequirementOperationTransformer : IOpenApiOperationTransformer
{
    public Task TransformAsync(OpenApiOperation operation, OpenApiOperationTransformerContext context, CancellationToken cancellationToken)
    {
        var metadata = context.Description.ActionDescriptor.EndpointMetadata;
        if (metadata.OfType<IAllowAnonymous>().Any() || !metadata.OfType<IAuthorizeData>().Any())
        {
            return Task.CompletedTask;
        }

        operation.Security ??= [];
        operation.Security.Add(new OpenApiSecurityRequirement
        {
            [new OpenApiSecuritySchemeReference("Bearer", context.Document)] = []
        });
        operation.Responses ??= [];
        operation.Responses.TryAdd("401", new OpenApiResponse { Description = "Missing, expired or invalid access token." });
        operation.Responses.TryAdd("403", new OpenApiResponse { Description = "The signed-in user lacks the required permission." });
        return Task.CompletedTask;
    }
}
```

這段程式的邏輯值得逐行理解。端點身上的 metadata 就是 [[basics-11-auth-concepts-and-pipeline]] 說的那堆附加資訊：`[Authorize]` 實作了 `IAuthorizeData`，`[AllowAnonymous]` 實作了 `IAllowAnonymous`。transformer 讀同一份 metadata，邏輯就和授權 middleware 的判斷一致：有 `[AllowAnonymous]` 就跳過（它蓋過任何 `[Authorize]`，包含 Controller 層級的），完全沒有 `[Authorize]` 也跳過，其餘的端點加上 Bearer 要求，同時補上 401 與 403 兩個回應。把 401、403 交給 transformer 而不是在每個 action 上重複 `[ProducesResponseType(401)]`，是因為這兩個狀態碼完全由授權設定決定，用程式推導比每個 action 手寫更不容易漏。

另一個選擇是對文件裡所有端點一律加上 Bearer 要求，程式更短。壞處是登入端點本身也會顯示上鎖圖示，前端同事會困惑：還沒登入怎麼打登入？文件不精確，比沒有文件還糟，所以值得多寫那幾行判斷。

注意 `OpenApiSecuritySchemeReference("Bearer", context.Document)` 這種寫法。內建產生器在 .NET 9 到 10 之間換了底層的 `Microsoft.OpenApi` 函式庫（2.x 版），命名空間從 `Microsoft.OpenApi.Models` 改為 `Microsoft.OpenApi`，引用 scheme 的方式也從過去的 `new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }` 變成 `OpenApiSecuritySchemeReference`。網路上大量的 Swashbuckle 範例與 `AddSecurityDefinition` 寫法，在內建產生器上都不能用。連官方文件裡也有一頁的範例仍停留在舊寫法，和同一頁上方的新寫法不一致；遇到舊式 `OpenApiReference`，以本節的寫法為準。

這兩個 transformer 的註冊在第七節，和版本管理的設定放在一起。

---

## 五、讓文件可讀：XML 註解與 `ProducesResponseType`

自動產生的文件有結構，但缺少意圖。`POST /api/v1/tasks` 的文件知道它收 `CreateTaskRequest`、回 `TaskResponse`，卻不知道它需要什麼權限、成功時 Location header 指向哪裡。這些補充說明用 C# 原本就有的 XML 註解寫在程式碼旁邊，文件和程式碼一起改，比另外維護一份文件不容易過期：

```csharp
/// <summary>Creates a task in the todo status. Requires the tasks:write permission.</summary>
/// <param name="request">The new task.</param>
/// <returns>The created task. The Location header points at it.</returns>
[Authorize(Policy = Permissions.TasksWrite)]
[HttpPost]
[ProducesResponseType<TaskResponse>(StatusCodes.Status201Created)]
[ProducesResponseType<ProblemDetails>(StatusCodes.Status409Conflict)]
public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct)
```

常聽到「寫了 `/// <summary>` 就會顯示在 Swagger」，少了一個條件：編譯器必須先把註解輸出成 XML 檔。專案檔要加上 `GenerateDocumentationFile`。.NET 10 的內建產生器會在編譯期處理這些註解並寫進文件（Swashbuckle 時代則要另外呼叫 `IncludeXmlComments` 指定檔案路徑，這一步在內建產生器不需要）：

```xml
<PropertyGroup>
  <GenerateDocumentationFile>true</GenerateDocumentationFile>
  <NoWarn>$(NoWarn);CS1591;CS1573</NoWarn>
</PropertyGroup>
```

`NoWarn` 那一行解決一個副作用：一旦開啟文件輸出，編譯器會對每個沒有註解的公開成員發出 CS1591 警告，對有些參數有註解、有些沒有的方法發出 CS1573 警告。TaskTracker 的 DTO 與 service 不打算逐一寫註解，所以把這兩個警告關掉；真正要看的 Controller action 則由團隊約定要寫。

`[ProducesResponseType]` 的角色是補足「成功以外的結果」。`ActionResult<TaskResponse>` 讓產生器知道成功時回 `TaskResponse`，但看不出會有 404 或 409，那些回應是 service 丟出 exception、由 [[basics-08-middleware-and-exception-handling]] 的 exception handler 轉成 ProblemDetails 的，在 action 的簽名上不留痕跡。要讓文件完整，就在 action 上補。.NET 7 起可以用泛型寫法 `[ProducesResponseType<ProblemDetails>(StatusCodes.Status404NotFound)]`，不必再寫 `typeof(...)`。有些教學範例把 201 掛在一個純讀取的 GET 上，那是狀態碼選錯了（[[basics-02-rest-api-design]] 講過，讀取成功是 200），標註與實際行為不一致時，文件就變成誤導。

下一個陷阱要靠輸出才看得到，放在第八節。

---

## 六、改版為什麼會弄壞前端：破壞性變更

回到開頭那個悄悄的改名。為什麼改 `title` 為 `name` 會出事，而新增一個 `dueAt` 欄位卻不會？差別在前端程式碼對 API 做了什麼假設。前端程式碼是「讀」回應：它會依名字取欄位、依型別處理值、依狀態碼走分支。凡是讓這些既有假設失效的改動，都是破壞性變更（breaking change）。反過來，新增前端沒有讀過的東西，它自然不會察覺。

具體來說，下面這些改動會破壞既有的 client：移除或改名欄位、改變欄位的型別（`status` 從字串變成數字）、新增必填的請求欄位或參數（舊 client 沒送，請求被擋下）、改變錯誤情境的狀態碼（前端依 409 顯示「標題重複」，改成 400 之後整個分支失效）、縮小欄位可以接受的值域。反過來，新增選填的請求欄位、在回應裡新增欄位、新增全新的端點，通常是安全的。「通常」二字有它的意義：如果前端有一段程式把回應物件整個展開再送回後端，多出來的欄位也可能被當成輸入，是否破壞要看 client 怎麼寫。

這個判準帶來一個設計習慣：把「新增」當成預設的演進方式，把「修改與刪除」當成需要版本的事件。版本管理讓必須破壞的時候有一條退路：舊 client 繼續打舊版，新 client 打新版，兩邊各自在方便的時間遷移。

---

## 七、版本放在哪裡：URL、Header、Query String 的取捨

版本資訊要從請求裡讀出來，常見有三個位置。

URL 路徑版本（`/api/v1/tasks`）是最常見的做法。它的優點在於版本寫在最顯眼的地方：瀏覽器網址列、log、監控圖表、`curl.exe` 的指令列都看得到，快取與 API gateway 的路由規則也最容易寫，因為版本就是路徑的一部分。缺點是版本號進入了資源的位址，嚴格的 REST 論者認為「同一個任務」不該因為版本不同而有兩個網址；實務上這個潔癖的代價遠小於可見性的好處。

Header 版本（例如 `X-Api-Version: 2.0`）讓網址保持乾淨，同一個資源只有一個位置。代價是版本藏在 header 裡：瀏覽器直接貼網址測試時看不到、log 預設不會記、快取要設定依 header 區分（`Vary`），忘記帶 header 的請求要有明確的預設行為。團隊內部有統一 HTTP client 封裝時，這些代價可以接受；要讓外部開發者拿著 `curl.exe` 就能試，URL 比較友善。還有一種 media type 版本（把版本放在 `Accept` header 的媒體類型裡），原理相近，使用得更少。

Query string 版本（`/api/tasks?api-version=1.0`）最容易加上去，不需要改路由，也是 `Asp.Versioning` 套件在你沒有指定時預設使用的讀取方式。弱點是它讓版本看起來像一個可有可無的篩選參數：快取 key 要特別處理，漏掉參數時行為模糊，所以新專案不建議用。

TaskTracker 選 URL 路徑。理由很實際：前端、`curl.exe`、log、將來的 gateway 都最容易處理，而且路徑版本最適合在書裡一步步示範。為了看看另外兩種選擇在實際程式碼裡的樣子，下面第九節會用一個小專案同時支援 URL 與 header 兩種讀法。

---

## 八、動手：把 TaskTracker 改成有文件、有版本

先交代起點。[[basics-13-permissions-with-frontend]] 結束時，`Program.cs` 還保留範本留下的兩行：`builder.Services.AddOpenApi()` 與開發環境下的 `app.MapOpenApi()`，路由是 `api/tasks` 與 `api/auth`。本章要做的修改：

1. 安裝 Scalar 與三個 `Asp.Versioning` 套件。
2. 專案檔加上 XML 文件輸出。
3. 新增兩個 transformer（第四節的程式）。
4. 新增 `AddTaskTrackerOpenApi()` 擴充方法，集中版本與 OpenAPI 的設定。
5. 修改 `Program.cs`。
6. 兩個 Controller 加上版本、改路由、補註解。

### 步驟 1：安裝套件

```powershell
dotnet add src/TaskTracker.Api package Scalar.AspNetCore --version 2.18.6
dotnet add src/TaskTracker.Api package Asp.Versioning.Mvc --version 10.2.1
dotnet add src/TaskTracker.Api package Asp.Versioning.Mvc.ApiExplorer --version 10.2.1
dotnet add src/TaskTracker.Api package Asp.Versioning.OpenApi --version 10.2.3
dotnet list src/TaskTracker.Api package
```

輸出的清單裡，這四個套件的版本都應該對上（Scalar.AspNetCore 2.18.6、Asp.Versioning.Mvc 與 Mvc.ApiExplorer 10.2.1、Asp.Versioning.OpenApi 10.2.3）。

這四個套件的分工：`Asp.Versioning.Mvc` 負責在 Controller 上讀取版本、依版本選出 action；`Asp.Versioning.Mvc.ApiExplorer` 把版本資訊提供給文件產生器；`Asp.Versioning.OpenApi` 把兩者接到內建的 `AddOpenApi`，讓每個版本產生一份文件。舊教材常見的 `Microsoft.AspNetCore.Mvc.Versioning` 已經淘汰，命名空間是舊的，現行套件的命名空間是 `Asp.Versioning`。Minimal API 另外使用 `Asp.Versioning.Http`，本書用 Controller 不需要。

### 步驟 2：專案檔

在 `TaskTracker.Api.csproj` 的 `PropertyGroup` 加入第五節那兩行（`GenerateDocumentationFile` 與 `NoWarn`）。

### 步驟 3：兩個 transformer

在專案裡建立 `OpenApi` 資料夾，放入第四節的 `BearerSecuritySchemeTransformer.cs` 與 `SecurityRequirementOperationTransformer.cs`。

### 步驟 4：集中設定的擴充方法

在 `Extensions/ServiceCollectionExtensions.cs` 加入（記得補上 `using Asp.Versioning;`、`using Microsoft.AspNetCore.OpenApi;`、`using TaskTracker.Api.OpenApi;`）：

```csharp
public static IServiceCollection AddTaskTrackerOpenApi(this IServiceCollection services)
{
    services.AddApiVersioning(options =>
        {
            options.DefaultApiVersion = new ApiVersion(1, 0);
            options.ReportApiVersions = true;
            options.ApiVersionReader = new UrlSegmentApiVersionReader();
        })
        .AddMvc()
        .AddApiExplorer(options =>
        {
            options.GroupNameFormat = "'v'VVV";
            options.SubstituteApiVersionInUrl = true;
        })
        .AddOpenApi();

    services.ConfigureAll<OpenApiOptions>(options =>
    {
        options.AddDocumentTransformer<BearerSecuritySchemeTransformer>();
        options.AddOperationTransformer<SecurityRequirementOperationTransformer>();
    });
    return services;
}
```

這幾個選項各有原因。`DefaultApiVersion` 是沒有標版本的 Controller 會被視為哪一版。`ReportApiVersions` 讓每個回應帶上 `api-supported-versions` header，告訴 client 這支 API 目前支援哪些版本，之後要棄用舊版時，也靠它通知。`ApiVersionReader = new UrlSegmentApiVersionReader()` 明確指定從路徑讀版本；不寫的話，預設讀 query string，套件的分析器還會提示（AV0015）建議明確設定，因為隱含的預設讀法很容易讓團隊誤會。`.AddMvc()` 是新套件要求的一步，把版本機制接進 MVC Controller。`GroupNameFormat = "'v'VVV"` 決定文件的分組名稱：版本 1.0 的文件名稱是 `v1`，也就是 `/openapi/v1.json` 的由來。`SubstituteApiVersionInUrl` 讓文件裡的路徑顯示成 `/api/v1/tasks`，而不是帶著 `{version}` 佔位符的樣板。最後的 `.AddOpenApi()` 讓每個版本各自產生一份文件。

這裡刻意沒有設 `AssumeDefaultVersionWhenUnspecified`。不少範例會開它，意思是「client 沒有指定版本時當作預設版本」。但在路徑版本裡，版本是路由的必要片段，沒帶就根本比對不到這個 Controller，這個選項沒有作用；套件的分析器（AV0016）也提醒它只適合「原本沒有版本、後來才補版本」的既有 API，必須相容舊網址的情境。

因為每個版本都是一份獨立的文件，各自有自己的 `OpenApiOptions`，所以兩個 transformer 用 `ConfigureAll` 一次套用到全部，不必每一份文件各登記一次。

### 步驟 5：`Program.cs`

把 `builder.Services.AddOpenApi();` 換成 `builder.Services.AddTaskTrackerOpenApi();`，開發環境區塊換成：

```csharp
using Scalar.AspNetCore;

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi().WithDocumentPerVersion();
    app.MapScalarApiReference();
}
```

`using Scalar.AspNetCore;` 放在檔案最上方。`WithDocumentPerVersion()` 把文件 endpoint 調整成每個版本一個網址：`/openapi/v1.json`、將來的 `/openapi/v2.json`。`MapScalarApiReference()` 掛上 Scalar 的網頁介面。兩者都在 `IsDevelopment()` 之內，所以正式環境沒有這兩個 endpoint。放在 pipeline 的哪個位置無關緊要（第二節證明過），本書放在 `UseHttpsRedirection()` 之前，純粹是讓「開發專用」的區塊靠在一起。

### 步驟 6：Controller 加上版本與註解

`TasksController` 與 `AuthController` 做三件事：宣告 `[ApiVersion(1.0)]`、路由改成 `api/v{version:apiVersion}/...`、補上第四與第五節那樣的註解與 `ProducesResponseType`。以 `AuthController` 為例：

```csharp
using Asp.Versioning;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Services;

namespace TaskTracker.Api.Controllers;

/// <summary>Sign-in and the current user's identity.</summary>
[ApiController]
[ApiVersion(1.0)]
[Route("api/v{version:apiVersion}/auth")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    /// <summary>Exchanges an email and password for a JWT access token.</summary>
    /// <param name="request">The credentials.</param>
    [AllowAnonymous]
    [HttpPost("login")]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<LoginResponse>> LoginAsync(LoginRequest request, CancellationToken ct)
    {
        return Ok(await _authService.LoginAsync(request, ct));
    }
}
```

（這裡只列出 `LoginAsync`；`Me` 的修改是同樣模式，加一行註解。）`TasksController` 的差異則是 `[Route("api/v{version:apiVersion}/tasks")]`，以及每個 action 上第五節那樣的註解與回應標註：`GetByIdAsync` 加 404（先照這樣寫，第九節會看到它造成的問題並修正），`CreateAsync` 加 201 與 409，`UpdateAsync` 加 404 與 409，`DeleteAsync` 加 204 與 404。

路由字串 `v{version:apiVersion}` 裡的 `apiVersion` 是 `Asp.Versioning` 註冊的路由 constraint，確保這個片段是合法的版本號。`[ApiVersion(1.0)]` 的屬性參數是 `double`，簡單直觀；但 Minimal API 的 `HasApiVersion` 與 `MapToApiVersion` 要傳 `new ApiVersion(1, 0)` 物件，傳 `double` 會得到編譯錯誤，兩種 API 看起來相似，注意別混用。

建置（`dotnet build`），應該是 `0 Warning(s)`、`0 Error(s)`。

---

## 九、讀文件：實際產生了什麼

啟動 API（Development 環境，連接埠 5080）後，先用 PowerShell 讀回 OpenAPI JSON，列出每個端點的安全性與回應：

```powershell
$doc = curl.exe -s http://localhost:5080/openapi/v1.json | ConvertFrom-Json
"openapi：$($doc.openapi)"
"info：$($doc.info.title) / $($doc.info.version)"
"servers：$($doc.servers.url -join ', ')"
"paths："
foreach ($path in $doc.paths.PSObject.Properties) {
    foreach ($operation in $path.Value.PSObject.Properties) {
        $security = if ($operation.Value.security) { 'security=Bearer' } else { 'security=none' }
        $responses = ($operation.Value.responses.PSObject.Properties.Name) -join ','
        "  $($operation.Name.ToUpper()) $($path.Name) operationId=$($operation.Value.operationId) $security responses=$responses"
    }
}
"securitySchemes：$($doc.components.securitySchemes.PSObject.Properties.Name -join ', ')"
"schemas：$($doc.components.schemas.PSObject.Properties.Name -join ', ')"
```

```text
openapi：3.1.1
info：TaskTracker.Api | v1 / 1.0
servers：http://localhost:5080/
paths：
  POST /api/v1/auth/login operationId= security=none responses=401
  GET /api/v1/auth/me operationId= security=Bearer responses=200,401,403
  GET /api/v1/tasks operationId= security=Bearer responses=200,401,403
  POST /api/v1/tasks operationId= security=Bearer responses=201,409,401,403
  GET /api/v1/tasks/{id} operationId= security=Bearer responses=404,401,403
  PUT /api/v1/tasks/{id} operationId= security=Bearer responses=404,409,401,403
  DELETE /api/v1/tasks/{id} operationId= security=Bearer responses=204,404,401,403
securitySchemes：Bearer
schemas：CreateTaskRequest, LoginRequest, MeResponse, PagedResponseOfTaskResponse, ProblemDetails, TaskItemStatus, TaskResponse, UpdateTaskRequest
```

這份輸出可以讀出好幾件事。`openapi` 是 `3.1.1`，.NET 10 內建產生器的預設版本（.NET 9 是 3.0；需要退回 3.0 給舊工具時，在 `AddOpenApi` 的 options 設 `OpenApiVersion`）。路徑已經是 `/api/v1/...`，`{version}` 被取代掉了，這是 `SubstituteApiVersionInUrl` 的效果。登入端點 `security=none`，其他端點 `security=Bearer`，這是第四節那個 `IAllowAnonymous` 判斷的成果。`operationId` 欄位是空的，現階段沒有影響；之後若要用文件自動產生前端的呼叫程式碼，這是需要補的一項。

文件裡的 `TaskItemStatus` 長這樣：

```text
{"enum":["todo","done"]}
```

這回答了開頭那個問題：`status` 要傳小寫的 `todo`。`TaskResponse` 的 schema 同樣回答了時區的疑問（`createdAt` 的格式是 `date-time`）以及哪些欄位一定存在：

```text
{"required":["id","title","status","createdAt"],"type":"object","properties":{"id":{"type":"string","format":"uuid"},"title":{"type":"string"},"status":{"$ref":"#/components/schemas/TaskItemStatus"},"createdAt":{"type":"string","format":"date-time"}}}
```

這呼應一個實務經驗：DTO 的設計品質就是文件的品質。欄位命名清楚、不必要的 nullable 不寫、Request 與 Response 分開，文件才會直接可讀；第六章分出的 DTO 在這裡派上用場。

XML 註解也進了文件。`POST /api/v1/tasks` 這個 operation 裡有 `"summary":"Creates a task in the todo status. Requires the tasks:write permission."`，這就是 `<summary>` 的內容。Bearer scheme 的內容則是：

```text
{"Bearer":{"type":"http","description":"Access token returned by POST /api/v1/auth/login.","scheme":"bearer","bearerFormat":"JWT"}}
```

### 輸出裡藏著一個陷阱

再看一次 `responses` 那一欄：`GET /api/v1/tasks/{id}` 是 `404,401,403`，沒有 200；`POST /api/v1/auth/login` 只有 `401`。成功的回應不見了。原因是：一旦在 action 上加了任何 `[ProducesResponseType]`，產生器就改用你宣告的清單，不再從回傳型別 `ActionResult<TaskResponse>` 補上預設的 200。沒有加任何標註的 action（例如 `GET /api/v1/tasks`，`responses=200,401,403`）反而是完整的。換句話說，為了補充錯誤狀態碼而加標註，反而可能讓成功回應消失，前端工具看到的是一支「永遠不會成功」的 API。

用一個小專案實測了三種寫法，各自產生的狀態碼：

```text
probe/a responses=404
probe/b responses=200,404
probe/c responses=200
```

`a` 只宣告 404，結果只有 404；`b` 同時宣告 200 與 404，兩者都在；`c` 完全不宣告，自動得到 200。結論是只要在 action 上寫了任何一個 `[ProducesResponseType]`，就把成功的那一個也一併寫上：

```csharp
[HttpGet("{id:guid}")]
[ProducesResponseType<TaskResponse>(StatusCodes.Status200OK)]
[ProducesResponseType<ProblemDetails>(StatusCodes.Status404NotFound)]
public async Task<ActionResult<TaskResponse>> GetByIdAsync(Guid id, CancellationToken ct)
```

登入端點同理，補上 `[ProducesResponseType<LoginResponse>(StatusCodes.Status200OK)]`。許多教學範例每個 action 都把 200 也一起寫了，剛好避開這個陷阱，卻沒有說明為什麼要這樣寫。[[basics-15-testing]] 會把「文件內容」納入自動化測試，包含哪些端點有 Bearer 要求、`status` 的 enum 值是什麼，讓這類問題在 CI 就被發現。

### Scalar 介面

文件是給機器讀的 JSON，人用的介面是 Scalar。`curl.exe -s -i http://localhost:5080/scalar` 會得到 `302 Found`，`Location: scalar/`；真正的頁面在 `/scalar/v1`，回 `200 OK`、`Content-Type: text/html`，內容是 `<title>Scalar API Reference</title>` 開頭的一頁 HTML。

用瀏覽器打開 `http://localhost:5080/scalar/v1`，左側是依 Controller 分組的端點清單，右側是請求範例與回應結構。要試打受保護的端點，先在 `POST /api/v1/auth/login` 送出帳號密碼，把回應裡的 `accessToken` 貼到介面的 Bearer 欄位，之後的請求就會自動帶上 `Authorization` header。這正是第四節 security scheme 的用途：沒有它，介面不知道要提供輸入 token 的地方。

---

## 十、版本化之後的行為

路由變了，行為也變了，逐一用 `curl.exe` 看。先登入取得 token（登入端點本身也在 `/api/v1/` 之下），並確認版本化的列表路由：

```powershell
curl.exe -s -i http://localhost:5080/api/v1/tasks -H "Authorization: Bearer $editorToken"
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 06:25:42 GMT
Server: Kestrel
Transfer-Encoding: chunked
api-supported-versions: 1.0

{"items":[],"page":1,"pageSize":20,"totalCount":0}
```

`api-supported-versions: 1.0` 就是 `ReportApiVersions` 的效果。前一章為止一直使用的舊路徑 `/api/tasks`，現在不存在了：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks -H "Authorization: Bearer $editorToken"
```

```text
HTTP/1.1 404 Not Found
Content-Type: application/problem+json
Date: Sat, 31 Oct 2026 06:25:43 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.5","title":"Not Found","status":404,"traceId":"00-306b221611f3a80917cd9d37de180e5a-3e3795c0dda978e2-00"}
```

這是本章最值得停下來想的一幕：為了防止將來弄壞前端，第一件事就把現有的前端弄壞了。TaskTracker 還沒有正式的 client，所以可以直接切換，並且在同一個變更裡通知前端把 base path 改成 `/api/v1`；這也是為什麼版本管理應該在第一個外部 client 出現之前就導入，之後每一次切換都要協調。已經有 client 在跑的 API 要補版本，需要和前端約定切換日，或在一段過渡期同時保留舊路徑，做法留給 [[expert-01-advanced-api-design]] 處理。尚未存在的版本（例如 `/api/v2/tasks`）同樣是 404，body 一樣是 ProblemDetails。

建立任務時，`Location` header 也帶著版本，這是 `CreatedAtAction` 依目前的路由產生網址的結果，不需要額外處理：

```powershell
'{"title":"Write chapter 14"}' | curl.exe -s -i -X POST http://localhost:5080/api/v1/tasks -H "Content-Type: application/json" -H "Authorization: Bearer $editorToken" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 06:25:45 GMT
Server: Kestrel
Location: http://localhost:5080/api/v1/tasks/e98533f9-59bd-43c2-9165-4ea0dbff8a50
Transfer-Encoding: chunked
api-supported-versions: 1.0

{"id":"e98533f9-59bd-43c2-9165-4ea0dbff8a50","title":"Write chapter 14","status":"todo","createdAt":"2026-10-31T06:25:45.8208928+00:00"}
```

最後確認「只在開發環境開放」確實生效。以 `Production` 環境啟動後，`/openapi/v1.json` 與 `/scalar/v1` 都回 `404 Not Found`，body 是 `application/problem+json` 的 Not Found，和「路徑從沒存在過」沒有任何區別，探測的人看不出這裡曾經有文件。

---

## 十一、第二個版本真的出現時：DTO 分版本

目前只有 v1，版本機制還沒展現威力。假設產品要求任務多一個截止時間，而且 `status` 字串要改成布林的 `done`，後者是破壞性變更，必須開 v2。下面用一個獨立的小專案示範：兩個版本並存、v1 標記為即將棄用。

```csharp
public record TaskV1(Guid Id, string Title, string Status);
public record TaskV2(Guid Id, string Title, bool Done, DateTimeOffset? DueAt);

[ApiController]
[ApiVersion(1.0, Deprecated = true)]
[Route("api/v{version:apiVersion}/tasks")]
public class TasksV1Controller : ControllerBase
{
    [HttpGet("{id:guid}")]
    public ActionResult<TaskV1> Get(Guid id) => new TaskV1(id, "demo", "todo");
}

[ApiController]
[ApiVersion(2.0)]
[Route("api/v{version:apiVersion}/tasks")]
public class TasksV2Controller : ControllerBase
{
    [HttpGet("{id:guid}")]
    public ActionResult<TaskV2> Get(Guid id) => new TaskV2(id, "demo", false, null);
}
```

註冊時的 `ApiVersionReader` 改成同時讀 URL 與 `X-Api-Version` header 兩個位置（完整註冊碼在下面）：

```csharp
o.ApiVersionReader = ApiVersionReader.Combine(new UrlSegmentApiVersionReader(), new HeaderApiVersionReader("X-Api-Version"));
```

這個結構體現多版本設計的幾個原則：不在同一個 action 裡用 `if` 混合版本邏輯；新版本建立新的 Controller 與新的 DTO；舊版本只維護，不新增功能。版本邏輯一旦混在同一個 action，每次修改都得同時推演所有版本，測試案例乘以版本數，改 v2 時也容易不小心動到 v1。分開之後，兩個版本共用下層的 service 與 entity（業務規則只有一份），各自的 DTO 與 Controller 只負責這個版本的 client 看到什麼，這正是 [[basics-06-dto-design]] 把 DTO 和 entity 分開的最大好處：資料庫結構不變，對外的形狀可以演進。

小專案的 `Program.cs` 不需要別的東西，把上面兩個 Controller 與兩個 record 放進同一個檔案（或各自一檔）後，再加這幾行；專案要安裝 `Asp.Versioning.Mvc`、`Asp.Versioning.Mvc.ApiExplorer`、`Asp.Versioning.OpenApi` 三個套件，版本同第八節：

```csharp
using Asp.Versioning;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
builder.Services.AddApiVersioning(o =>
    {
        o.DefaultApiVersion = new ApiVersion(1, 0);
        o.ReportApiVersions = true;
        o.ApiVersionReader = ApiVersionReader.Combine(new UrlSegmentApiVersionReader(), new HeaderApiVersionReader("X-Api-Version"));
    })
    .AddMvc()
    .AddApiExplorer(o =>
    {
        o.GroupNameFormat = "'v'VVV";
        o.SubstituteApiVersionInUrl = true;
    })
    .AddOpenApi();

var app = builder.Build();
app.MapControllers();
app.MapOpenApi().WithDocumentPerVersion();
app.Run();
```

啟動這個小專案（Development 環境）後，實際請求兩個版本與一個不存在的版本：

```text
--- GET /api/v1/tasks/26247b22-a988-4af7-95fd-b1087c160343
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 14:00:22 GMT
Server: Kestrel
Transfer-Encoding: chunked
api-supported-versions: 2.0
api-deprecated-versions: 1.0

{"id":"26247b22-a988-4af7-95fd-b1087c160343","title":"demo","status":"todo"}--- GET /api/v2/tasks/26247b22-a988-4af7-95fd-b1087c160343
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 14:00:22 GMT
Server: Kestrel
Transfer-Encoding: chunked
api-supported-versions: 2.0
api-deprecated-versions: 1.0

{"id":"26247b22-a988-4af7-95fd-b1087c160343","title":"demo","done":false,"dueAt":null}--- GET /api/v3/tasks/26247b22-a988-4af7-95fd-b1087c160343
HTTP/1.1 404 Not Found
Content-Length: 0
Date: Sat, 31 Oct 2026 14:00:22 GMT
Server: Kestrel
```

v1 與 v2 各自回傳自己的形狀（v1 是 `"status":"todo"`，v2 是 `"done":false,"dueAt":null`），v3 同樣是 404。

注意兩個版本的回應都帶著兩個 header：`api-supported-versions: 2.0` 列出仍受支援的版本，`api-deprecated-versions: 1.0` 通知 client v1 已標記為棄用。這是機器可讀的棄用訊號，client 的 HTTP 封裝層可以在收到時記 log 或提醒開發者遷移。要注意的是，標記為 `Deprecated` 只是廣播訊息，本身不會讓舊版停止運作，什麼時候真正下線是另一個決定（流程見 [[expert-01-advanced-api-design]]）。

同一個小專案另有 header 版本的 Controller（路由 `api/tasks`，用 `MapToApiVersion` 把兩個 action 分別對應到 1.0 與 2.0）。不帶 header 時回 `400 Bad Request`，body 為空（這個小專案沒有註冊 ProblemDetails），同樣帶著上面兩個版本 header。帶上 `X-Api-Version: 2.0` 得到 v2 的 JSON，帶 `1.0` 得到 v1 的 JSON。沒帶 header 的請求被明確拒絕，而不是偷偷當作某個預設版本，這對版本管理比較安全：client 在不知情的情況下被升級或降級，通常比被拒絕更難除錯。

最後，這個小專案的兩份文件分別是：

```text
1.0
/api/v1/tasks/{id}, /api/tasks/{id}
2.0
/api/v2/tasks/{id}, /api/tasks/{id}
```

`/openapi/v1.json` 只含 v1 的路徑，`/openapi/v2.json` 只含 v2 的路徑，各自的 `info.version` 是 `1.0` 與 `2.0`。每一個 client 只需要讀對應自己版本的那一份文件，不會被另一個版本的描述干擾。

---

## 十二、前端同事現在怎麼工作

回到開頭的兩個問題。「`status` 傳什麼？」同事打開 `/scalar/v1`，從 schema 讀到 `todo` 與 `done`，直接用介面送一個請求試試，不必再問後端，也不會讀到過期的說明，因為文件從程式碼產生，改了 DTO 文件就同步。悄悄的改名則變成一個要開新版本的決定：把 `title` 改成 `name`，就是新增 `TaskV2` 與 `TasksV2Controller`，v1 繼續回 `title`，透過 `api-deprecated-versions` 通知前端並給遷移期限。

文件還有更進階的用法：前端可以用 `openapi-typescript` 之類的社群工具，從 `/openapi/v1.json` 產生 TypeScript 型別，讓欄位改名在編譯期就報錯，[[basics-13-permissions-with-frontend]] 提到的 `Permission` 型別同步問題也可走同一條路。要走到這一步，`operationId` 等細節需要補強，已超出入門範圍。

---

## 常見誤解

**「Swagger 要放在 `UseAuthorization` 前面，否則會被 `[Authorize]` 擋住。」** 擋人的是 endpoint 身上的授權 metadata，不是 middleware 的先後。`MapOpenApi()` 是 endpoint，預設沒有授權 metadata，排在授權 middleware 之前或之後都回 200；只有 `RequireAuthorization()` 或 `FallbackPolicy` 才會擋它。

**「寫了 `/// <summary>` 文件就會顯示。」** 專案檔要開 `GenerateDocumentationFile`，編譯器才會輸出 XML 註解，產生器才讀得到。

**「補上 `[ProducesResponseType]` 只會讓文件更完整。」** 一旦 action 上有任何一個，產生器就不再自動補 200。只標了 404，文件就會變成「這支 API 只有 404」。

**「導入 API 版本號之後，舊的網址還會繼續能用。」** 路由改成 `api/v{version:apiVersion}/...` 之後，原本的 `/api/tasks` 會直接 404。版本機制保護的是未來的改版，導入的那一刻本身就是一次破壞性變更。

---

## 同事會來問你的問題

**Q：正式環境該不該開 Swagger／Scalar？**
先問讀者是誰。API 只服務自家前端：關掉，用 CI 輸出 OpenAPI JSON 檔給需要的人。API 是給外部合作夥伴整合的產品：文件本來就該公開，或放在需要登入的開發者入口。要保留又不想公開，用 `MapOpenApi().RequireAuthorization(...)` 保護，但網頁介面讀文件時也會需要 token。

**Q：URL 版本、header 版本、query string 版本，到底選哪一個？**
團隊內部、前後端都由自己控制：任何一種都能用，URL 路徑在 log、監控、快取、`curl.exe` 試打上都最直觀，是 TaskTracker 的選擇。要讓外部開發者容易上手，也選 URL。偏好乾淨網址、client 都經過統一封裝，才考慮 header。query string 最容易被漏掉，新專案不建議。

**Q：每次改 API 都要開新版本嗎？**
不用。新增選填欄位、新增端點通常不是破壞性變更，直接加在現有版本即可。需要新版本的是移除或改名欄位、改型別、新增必填參數、改變錯誤的狀態碼。為每個小改動開版本，會讓需要維護的版本數量失控。

**Q：`AddSwaggerGen` 和 `Microsoft.AspNetCore.Mvc.Versioning` 在舊專案裡還能用嗎？**
`Swashbuckle.AspNetCore` 仍在維護，舊專案繼續使用沒問題，只是新專案的範本不再包含它，而且它從 10.2.1 起相依 Microsoft.OpenApi 2.x，舊寫法（`Microsoft.OpenApi.Models`、`OpenApiReference`）需要跟著調整。`Microsoft.AspNetCore.Mvc.Versioning` 則已經被 `Asp.Versioning.Mvc` 取代，命名空間也不同，新程式碼不應再引用舊套件。

---

## 這章的位置

學完這一章，你能分清楚 OpenAPI、Swagger UI、Scalar 與 Swashbuckle 各自是什麼，用內建的 `AddOpenApi` 產生文件，用 Scalar 當介面；知道 `MapOpenApi` 是 endpoint，能用 `RequireAuthorization` 控制誰看得到文件；會寫 transformer 補上 JWT 的 security scheme；會用 XML 註解與 `ProducesResponseType` 讓文件可讀，並避開「成功回應消失」的陷阱；也能判斷什麼是破壞性變更、為何選 URL 版本、怎麼把 TaskTracker 改成 `api/v1`，以及第二個版本出現時用新 Controller 與新 DTO 並存。想看版本管理的部署面（滾動更新期間新舊版本並存的相容性）見 [[21-deployment]]；路由的運作機制見 [[03-routing-and-endpoints]]；棄用流程、sunset 與相容性演進的完整策略見 [[expert-01-advanced-api-design]]。

接下來 [[basics-15-testing]] 處理另一個問題：改了程式之後，怎麼知道沒有弄壞既有的行為，包括剛剛產生的這份文件。

---

## 連結

- 上一章：[[basics-13-permissions-with-frontend]]
- 下一章：[[basics-15-testing]]
- 對應深度章：[[21-deployment]]、[[03-routing-and-endpoints]]
- 本章用到的先修內容：[[basics-06-dto-design]]、[[basics-08-middleware-and-exception-handling]]、[[basics-11-auth-concepts-and-pipeline]]
- 後續：[[expert-01-advanced-api-design]]
- 總目錄：[[dotnet-web-api]]
