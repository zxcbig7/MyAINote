---
type: concept
domain: tech
tags: [dotnet, aspnet, authentication, scheme, claims, cookie, bearer, identity]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 11 章：認證 — Scheme、Claims，以及 401 與 403 的分界

## 一個 302 引起的整天偵錯

前端呼叫 API，預期收到 401 好跳轉到登入頁。結果瀏覽器的網路面板顯示：

```text
GET /api/orders   →  302 Found
Location: /Account/Login?ReturnUrl=%2Fapi%2Forders
```

然後是對 `/Account/Login` 的請求，回了一個 404（因為這是純 API 專案，根本沒有這個頁面）。前端的錯誤處理完全失效——它在等 401，收到的卻是一串重導向最後變成 404。

原因是專案裡同時裝了 Cookie 認證與 JWT 認證，而**預設 scheme 是 Cookie**。Cookie handler 的「挑戰（challenge）」行為就是導向登入頁，這對 MVC 網站是正確的，對 API 是災難。

要理解這件事，必須先建立一個很多人跳過的概念：**scheme**。

---

## 一、認證與授權的分工

兩個常被混用的詞，界線其實很清楚：

| | 認證（Authentication） | 授權（Authorization） |
| --- | --- | --- |
| 問題 | 你是誰？ | 你可以做什麼？ |
| 產出 | `HttpContext.User`（一個 `ClaimsPrincipal`） | 允許 / 拒絕 |
| 失敗回應 | **401 Unauthorized** | **403 Forbidden** |
| Middleware | `UseAuthentication()` | `UseAuthorization()` |

HTTP 狀態碼的命名有歷史包袱：**401 的字面是 "Unauthorized"，但它的意思其實是「未認證」**。「已認證但權限不足」是 403 Forbidden。

判斷規則：

- 沒帶 token、token 過期、簽章錯誤 → **401**，語意是「你沒表明身分，或表明得不對」
- 帶了有效 token，但這個使用者不是管理員 → **403**，語意是「我知道你是誰，但你不能做這件事」

這個差別對前端很重要：401 應該觸發「重新登入」流程，403 應該顯示「權限不足」訊息。混淆的話，使用者會在權限不足時被反覆踢回登入頁，登入成功又被踢出來——一個經典的無限迴圈。

---

## 二、Scheme：認證的可插拔單位

**一個 scheme = 一個名字 + 一個 handler + 一組設定。**

```csharp
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)   // 預設 scheme 的名字
    .AddJwtBearer(JwtBearerDefaults.AuthenticationScheme, options => { /* 設定 */ });
```

`AddAuthentication(...)` 的參數是**預設 scheme 的名稱**（一個字串，`"Bearer"`）。之後 `AddJwtBearer` 註冊了一個叫這個名字的 handler。

Handler 是實際幹活的東西，它要能回答四種請求：

| 動作 | 何時被呼叫 | Cookie handler 的行為 | JWT handler 的行為 |
| --- | --- | --- | --- |
| **Authenticate** | 每個請求，由 `UseAuthentication` 觸發 | 讀 cookie、解密、還原 principal | 讀 `Authorization` header、驗簽、解析 claims |
| **Challenge** | 需要認證但沒有身分時 | **302 導向登入頁** | **401 + `WWW-Authenticate` header** |
| **Forbid** | 有身分但權限不足時 | 302 導向 AccessDenied 頁 | **403** |
| **SignIn / SignOut** | 明確登入 / 登出 | 寫入 / 清除 cookie | **不支援**（JWT 無狀態） |

開頭那個 302 的答案就在這張表：預設 scheme 是 Cookie 時，challenge 走的是 Cookie handler 的行為——導向登入頁。

修正方式是把預設 scheme 設成 Bearer：

```csharp
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(...)
    .AddCookie();      // 仍然註冊，但不是預設
```

### 2.1 四種「預設」可以分開設定

更精細的控制：

```csharp
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultForbidScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultSignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;
});
```

`DefaultSignInScheme` 在 OAuth 流程裡特別重要：外部登入（Google）驗證成功後，要把結果「簽入」到某個地方——通常是一個暫時的 cookie，讓後續步驟能取用。這在 [[13-oauth-oidc]] 會用到。

### 2.2 多 scheme 並存

同一個應用程式可以同時支援多種認證方式：

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer()                                   // 前端 SPA 用
    .AddCookie()                                      // 後台管理頁面用
    .AddJwtBearer("ExternalApi", options => { ... }); // 第三方系統用不同的簽發者
```

然後在需要時指定：

```csharp
[Authorize(AuthenticationSchemes = "ExternalApi")]
public class WebhookController : ControllerBase
```

或者允許多種：

```csharp
[Authorize(AuthenticationSchemes = "Bearer,Cookies")]
```

多 scheme 的常見場景是：主 API 用 JWT、Swagger UI 或管理後台用 Cookie、對外的 webhook 用另一組簽發者的 token。

---

## 三、`UseAuthentication` 到底做了什麼

```csharp
app.UseAuthentication();
```

它做的事只有一件：**呼叫預設 authenticate scheme 的 handler，把結果填進 `HttpContext.User`。**

關鍵性質是：**它不會拒絕任何請求。**

沒帶 token？`HttpContext.User` 就是一個匿名的 `ClaimsPrincipal`（`Identity.IsAuthenticated == false`），請求繼續往下走。Token 無效？一樣，只是 User 仍然是匿名的。

拒絕請求是 `UseAuthorization` 的工作。這個分工解釋了第 01 章講的順序問題——`UseAuthentication` 必須在 `UseAuthorization` 之前，否則授權檢查時 `User` 還是空的。

也解釋了另一個常見困惑：**為什麼沒有 `[Authorize]` 的 action，帶不帶 token 都能進去？** 因為認證只負責「識別身分」，不負責「要求身分」。要求是 `[Authorize]` 的事。

### 3.1 手動觸發認證

需要用非預設 scheme 驗證時：

```csharp
var result = await HttpContext.AuthenticateAsync("ExternalApi");

if (result.Succeeded)
{
    var principal = result.Principal;
}
```

---

## 四、Claims：身分的資料結構

認證的產出是 `ClaimsPrincipal`，它有三層結構：

```text
ClaimsPrincipal（一個人）
  └── ClaimsIdentity（一個身分，可以有多個）
        └── Claim（一則主張：type + value）
```

一個人可以有多個身分（同時用公司帳號和 Google 帳號登入），每個身分帶著一組 claim。實務上 Web API 通常只有一個 identity。

```csharp
var claims = new List<Claim>
{
    new(ClaimTypes.NameIdentifier, user.Id.ToString()),
    new(ClaimTypes.Name, user.Name),
    new(ClaimTypes.Email, user.Email),
    new(ClaimTypes.Role, "Admin"),
    new("department", user.Department),          // 自訂 claim
};

var identity = new ClaimsIdentity(claims, "Bearer");
var principal = new ClaimsPrincipal(identity);
```

讀取：

```csharp
var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
var email = User.FindFirst(ClaimTypes.Email)?.Value;
var isAdmin = User.IsInRole("Admin");
var departments = User.FindAll("department").Select(c => c.Value);
```

### 4.1 Claim type 的命名混亂

這是實務上第二個折磨人的地方。`ClaimTypes.NameIdentifier` 展開來是一個長 URI：

```text
http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier
```

而 JWT 標準用的是短名稱 `sub`（subject）。ASP.NET Core 的 JWT handler **預設會做映射**——把 JWT 裡的 `sub` 轉成那個長 URI。於是：

```csharp
// Token 裡明明是 "sub"，這樣拿卻是 null
var id = User.FindFirst("sub")?.Value;              // null！

// 要用映射後的名稱
var id = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;   // 有值
```

這個自動映射經常造成混亂（尤其在跨系統對接、或前端也要解析 token 的時候）。要關掉它：

```csharp
// 在 AddAuthentication 之前
JwtSecurityTokenHandler.DefaultInboundClaimTypeMap.Clear();

// 或針對單一 handler
options.MapInboundClaims = false;
```

關掉之後 `User.FindFirst("sub")` 就有值了，claim 名稱與 token 內容一一對應。**新專案建議關掉**——「所見即所得」比隱式映射好維護。但要記得同步調整所有讀取 claim 的程式碼，以及 `TokenValidationParameters` 裡的 `NameClaimType` / `RoleClaimType`：

```csharp
options.TokenValidationParameters.NameClaimType = "name";
options.TokenValidationParameters.RoleClaimType = "role";
```

`RoleClaimType` 特別重要——`User.IsInRole()` 和 `[Authorize(Roles = "Admin")]` 都靠它決定要看哪個 claim。設錯的話角色檢查會全部失敗，而且沒有任何錯誤訊息。

### 4.2 Claim 不該放什麼

Claim 會被寫進 token 或 cookie，每個請求都攜帶。所以：

- **不要放大量資料**：使用者的完整個人檔案、權限清單（幾百個項目）會讓每個請求的 header 膨脹，甚至超過伺服器的 header 大小限制
- **不要放敏感資料**：JWT 的 payload 只是 Base64 編碼，**任何人都能解開讀取**（見 [[12-jwt-deep-dive]]）
- **不要放會頻繁變動的資料**：token 簽發後就固定了，使用者的權限在後台被改了，token 裡的舊值仍然有效直到過期

一個好的 claim 集合是：使用者識別碼、顯示名稱、角色（少量）、租戶識別碼。其他的用識別碼去查。

### 4.3 存取當前使用者的正確方式

在 controller 裡直接用 `User` 屬性。在 service 層則需要 `IHttpContextAccessor`：

```csharp
public class CurrentUserService : ICurrentUserService
{
    private readonly IHttpContextAccessor _accessor;

    public CurrentUserService(IHttpContextAccessor accessor) { _accessor = accessor; }

    public string? UserId =>
        _accessor.HttpContext?.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
}

builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ICurrentUserService, CurrentUserService>();
```

注意兩點：`IHttpContextAccessor` 需要明確註冊（第 00 章）；這個服務必須是 **Scoped**，絕不能是 Singleton——第 02 章的反模式 6.2 就是這個。

背景服務裡沒有 `HttpContext`，`_accessor.HttpContext` 會是 null。所以這個服務的所有使用點都要處理 null，或者確保它只在請求路徑上被使用。

---

## 五、Cookie 還是 Bearer

前後端分離的專案最常見的架構問題。

| | Cookie | Bearer Token |
| --- | --- | --- |
| 傳輸 | 瀏覽器自動附帶 | 前端手動放進 header |
| 跨網域 | 需要 CORS + `SameSite` 設定 | 天然支援 |
| CSRF 風險 | **有**（自動附帶的特性） | 無（需要手動附帶） |
| XSS 風險 | 較低（`HttpOnly` 讓 JS 讀不到） | **較高**（存在 JS 可讀之處） |
| 伺服器狀態 | 可撤銷（有 session 時） | 難以撤銷（見第 12 章） |
| 行動 App | 不方便 | 方便 |
| 微服務轉發 | 不方便 | 方便 |

沒有絕對答案，但可以給出判斷路徑：

**同網域的 SPA（前端由同一個服務提供）**：Cookie 通常更安全。設 `HttpOnly` + `Secure` + `SameSite=Strict/Lax`，XSS 拿不到憑證，CSRF 由 SameSite 加 anti-forgery token 防護。

**跨網域的 SPA、行動 App、第三方整合**：Bearer token。這時要處理的是「token 存哪裡」——`localStorage` 會被 XSS 讀走，記憶體變數在刷新頁面後消失。折衷做法是 access token 放記憶體、refresh token 放 `HttpOnly` cookie，兼顧兩邊。這在 [[12-jwt-deep-dive]] 展開。

**Cookie 的 `SameSite` 設定要特別小心**：`Strict` 會讓從外部連結點進來的請求也不帶 cookie（使用者看起來像沒登入）；`None` 必須配 `Secure`，否則現代瀏覽器直接丟棄。前後端不同網域時只能用 `None`，也就必須有 HTTPS。

---

## 六、自訂 Authentication Handler

第三方系統用 API Key 而不是標準 token 時，可以寫一個 scheme 而不是塞進 middleware：

```csharp
public class ApiKeyAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    private readonly IApiKeyValidator _validator;

    public ApiKeyAuthenticationHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        IApiKeyValidator validator)
        : base(options, logger, encoder)
    {
        _validator = validator;
    }

    protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue("X-Api-Key", out var key))
        {
            return AuthenticateResult.NoResult();      // 沒帶就是沒帶，不是失敗
        }

        var client = await _validator.ValidateAsync(key.ToString());
        if (client is null)
        {
            return AuthenticateResult.Fail("Invalid API key");
        }

        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, client.Id),
            new Claim("client_type", "external")
        };
        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var ticket = new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme.Name);

        return AuthenticateResult.Success(ticket);
    }
}

builder.Services.AddAuthentication()
    .AddScheme<AuthenticationSchemeOptions, ApiKeyAuthenticationHandler>("ApiKey", null);
```

`NoResult()` 與 `Fail()` 的差別值得注意：前者表示「這個 scheme 不適用於這個請求」（多 scheme 時會繼續嘗試其他的），後者表示「適用但驗證失敗」。

寫成 scheme 而不是 middleware 的好處：能和 `[Authorize]` 整合、能與其他 scheme 並存、challenge/forbid 行為統一、`HttpContext.User` 的填法一致。

---

## 七、常見誤解

**「401 是沒權限，403 是沒登入。」**
反了。401 = 未認證（沒表明身分或身分無效），403 = 已認證但權限不足。混淆會導致前端在權限不足時反覆跳轉登入頁。

**「`UseAuthentication()` 會擋掉沒帶 token 的請求。」**
不會。它只負責填 `HttpContext.User`，沒帶 token 就填一個匿名身分，請求照樣往下走。拒絕是 `UseAuthorization` 加 `[Authorize]` 的事。

**「JWT 的 payload 是加密的，可以放敏感資料。」**
不是。它只是 Base64 編碼，任何人都能解開。簽章保護的是「不可竄改」，不是「不可讀取」。

**「`User.FindFirst("sub")` 應該拿得到 token 裡的 sub。」**
預設有 inbound claim 映射，`sub` 被轉成長 URI。要嘛用 `ClaimTypes.NameIdentifier`，要嘛設 `MapInboundClaims = false` 關掉映射。

**「多個認證方式要寫在 middleware 裡分支處理。」**
不用。註冊多個 scheme，用 `[Authorize(AuthenticationSchemes = "...")]` 指定即可，行為更一致也更容易維護。

**「Bearer token 比 cookie 安全。」**
各有各的風險面。Cookie 怕 CSRF 但可以 `HttpOnly` 防 XSS 讀取；Bearer 免疫 CSRF 但存在 JS 可讀之處就怕 XSS。選擇取決於部署形態，不是絕對的安全性排序。

---

## 八、同事會來問你的問題

**Q：API 回 302 導向登入頁，但這是純 API 專案。**
預設 challenge scheme 是 Cookie，它的 challenge 行為就是導向登入頁。把 `AddAuthentication` 的預設 scheme 設成 `JwtBearerDefaults.AuthenticationScheme`，或明確設定 `DefaultChallengeScheme`。

**Q：`[Authorize(Roles = "Admin")]` 一直失敗，token 裡明明有 role。**
檢查 `RoleClaimType`。JWT 裡的 claim 名稱（`role` 或 `roles`）必須與 `TokenValidationParameters.RoleClaimType` 一致，否則框架看的是另一個 claim。關掉 inbound 映射時尤其容易出這個問題。

**Q：Service 層怎麼拿當前使用者？**
注入 `IHttpContextAccessor`（記得 `AddHttpContextAccessor()`），包成一個 Scoped 的 `ICurrentUserService`。絕不能把使用者資訊存在 Singleton 服務裡——那會跨請求洩漏。

**Q：可以把使用者的所有權限都放進 token 嗎？**
不建議。token 會膨脹（每個請求都帶）、權限變更要等 token 過期才生效、而且 payload 是可讀的。放使用者識別碼與少量角色，細緻權限即時查。

**Q：同一個 API 要同時支援瀏覽器 cookie 登入和第三方 token，怎麼做？**
註冊兩個 scheme，用 `[Authorize(AuthenticationSchemes = "Bearer,Cookies")]` 允許兩者，或在不同 controller 上分別指定。

**Q：第三方系統用 API Key，要寫 middleware 嗎？**
寫成自訂 `AuthenticationHandler` 更好——能與 `[Authorize]` 整合、與其他 scheme 並存、challenge/forbid 行為一致。

---

## 連結

- [[basics-11-auth-concepts-and-pipeline]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[10-oracle-specifics]] — 上一章
- [[12-jwt-deep-dive]] — 下一章：JWT 驗證的每個參數
- [[13-oauth-oidc]] — Google 登入的完整流程
- [[14-authorization]] — 授權：policy、requirement、resource-based
- [[01-request-pipeline]] — `UseAuthentication` 在 pipeline 的位置
