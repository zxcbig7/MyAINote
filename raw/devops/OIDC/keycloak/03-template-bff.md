---
tags: [devops, keycloak, template, bff, openid-connect]
---

# Template B — Confidential Client / BFF（沿用現有架構）

Backend 跟 Keycloak 對接、換 code、簽自家 JWT，前端流程跟現在 Google flow 幾乎一樣。

## 適用情境
- 想搬最少 code，把 `GoogleAuthController` 換成 `KeycloakAuthController`
- 沿用現有的 axios + localStorage + AuthContext 架構
- 想讓 client_secret 留在 backend

## npm

前端：不需要新套件
後端：

```powershell
dotnet add package Microsoft.AspNetCore.Authentication.OpenIdConnect
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
```

## env / appsettings.json

```json
{
  "Keycloak": {
    "Authority": "https://sso.company.com/realms/company",
    "ClientId": "mydevweb-backend",
    "ClientSecret": "",
    "CallbackPath": "/signin-oidc"
  },
  "Jwt": {
    "Issuer": "MyDevWebBackend",
    "Audience": "MyDevWebFrontend",
    "Key": "",
    "ExpiresInMinutes": 43200
  },
  "Frontend": {
    "CallbackUrl": "https://viclai.idv.tw/auth/callback"
  }
}
```

---

## 1. Backend — Authentication 設定

`Middleware.cs` — 把現有的 `.AddGoogle(...)` 換成 `.AddOpenIdConnect(...)`：

```csharp
builder.Services.AddAuthentication(options =>
{
    options.DefaultScheme = "Cookies";
    options.DefaultChallengeScheme = "Keycloak";
})
.AddCookie("Cookies", options =>
{
    options.Cookie.SameSite = builder.Environment.IsDevelopment()
        ? SameSiteMode.Lax : SameSiteMode.None;
    options.Cookie.SecurePolicy = builder.Environment.IsDevelopment()
        ? CookieSecurePolicy.None : CookieSecurePolicy.Always;
})
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
})
.AddOpenIdConnect("Keycloak", options =>
{
    options.Authority    = builder.Configuration["Keycloak:Authority"];
    options.ClientId     = builder.Configuration["Keycloak:ClientId"];
    options.ClientSecret = builder.Configuration["Keycloak:ClientSecret"];
    options.CallbackPath = builder.Configuration["Keycloak:CallbackPath"]; // /signin-oidc

    options.ResponseType = "code";
    options.UsePkce = true;          // 即使 confidential client 也用 PKCE，多層保險
    options.SaveTokens = true;       // tokens 存 cookie 給 controller 讀

    options.Scope.Add("openid");
    options.Scope.Add("profile");
    options.Scope.Add("email");

    options.GetClaimsFromUserInfoEndpoint = true;

    options.CorrelationCookie.SameSite = builder.Environment.IsDevelopment()
        ? SameSiteMode.Lax : SameSiteMode.None;
    options.CorrelationCookie.SecurePolicy = builder.Environment.IsDevelopment()
        ? CookieSecurePolicy.None : CookieSecurePolicy.Always;

    // 跟現有 Google flow 一樣：Production 強制 https
    options.Events = new OpenIdConnectEvents
    {
        OnRedirectToIdentityProvider = ctx =>
        {
            ctx.ProtocolMessage.RedirectUri =
                ctx.ProtocolMessage.RedirectUri.Replace(
                    "http://api.viclai.idv.tw", "https://api.viclai.idv.tw");
            return Task.CompletedTask;
        }
    };
});
```

## 2. Backend — Controller（取代 GoogleAuthController）

`Controllers/KeycloakAuthController.cs`

```csharp
[ApiController]
[Route("api/auth/keycloak")]
public class KeycloakAuthController : ControllerBase
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<KeycloakAuthController> _logger;

    public KeycloakAuthController(IConfiguration config, ILogger<KeycloakAuthController> log)
    {
        _configuration = config;
        _logger = log;
    }

    [HttpGet("login")]
    public IActionResult Login()
    {
        var redirectUrl = "/api/auth/keycloak/callback";
        var properties  = new AuthenticationProperties { RedirectUri = redirectUrl };
        return Challenge(properties, "Keycloak");
    }

    [HttpGet("callback")]
    public async Task<IActionResult> Callback()
    {
        var result = await HttpContext.AuthenticateAsync("Cookies");
        if (!result.Succeeded) return Unauthorized();

        var id     = result.Principal!.FindFirst(ClaimTypes.NameIdentifier)?.Value
                  ?? result.Principal!.FindFirst("sub")?.Value;
        var email  = result.Principal!.FindFirst(ClaimTypes.Email)?.Value
                  ?? result.Principal!.FindFirst("email")?.Value;
        var name   = result.Principal!.FindFirst(ClaimTypes.Name)?.Value
                  ?? result.Principal!.FindFirst("name")?.Value;
        var avatar = result.Principal!.FindFirst("picture")?.Value ?? "";

        var token = GenerateJwt(id!, avatar, email!, name!);

        var frontendUrl = _configuration["Frontend:CallbackUrl"]
            ?? "http://localhost:5173/auth/callback";
        return Redirect($"{frontendUrl}?token={token}");
    }

    [HttpGet("me")]
    [Authorize(AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]
    public IActionResult Me()
    {
        var id     = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        var email  = User.FindFirst(ClaimTypes.Email)?.Value;
        var name   = User.FindFirst(ClaimTypes.Name)?.Value;
        var avatar = User.FindFirst("picture")?.Value;
        return Ok(new { id, email, name, avatar });
    }

    [HttpGet("logout")]
    public async Task<IActionResult> Logout()
    {
        await HttpContext.SignOutAsync("Cookies");
        // 也清掉 Keycloak 的 SSO session
        return SignOut(new AuthenticationProperties
        {
            RedirectUri = _configuration["Frontend:CallbackUrl"]
        }, "Keycloak", "Cookies");
    }

    private string GenerateJwt(string id, string avatar, string email, string name)
    {
        var key   = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_configuration["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
        var exp   = DateTime.UtcNow.AddMinutes(
            double.Parse(_configuration["Jwt:ExpiresInMinutes"] ?? "60"));

        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, id ?? ""),
            new Claim("picture", avatar ?? ""),
            new Claim(ClaimTypes.Email, email),
            new Claim(ClaimTypes.Name,  name),
        };

        var jwt = new JwtSecurityToken(
            issuer:   _configuration["Jwt:Issuer"],
            audience: _configuration["Jwt:Audience"],
            claims:   claims,
            expires:  exp,
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(jwt);
    }
}
```

> 對照現有的 [GoogleAuthController.cs](MyDevWebBackend/Controllers/GoogleAuthController.cs)，幾乎就是把 `Google` 字眼換成 `Keycloak`、`GoogleDefaults.AuthenticationScheme` 換成 `"Keycloak"`。

---

## 3. Frontend — 幾乎不動

只改一個檔案，把 endpoint URL 改掉：

`src/auth/authService.ts`

```typescript
loginServerSide(): void {
  window.location.href = `${BACKEND_BASE}/api/auth/keycloak/login`;
}
```

`AuthCallback.tsx`、`AuthContext.tsx`、`decodeToken` 全部保留，因為 backend 還是簽相同格式的自家 JWT。

---

## 4. Google Cloud Console 對等設定

在 Keycloak admin console（或請 IT 幫忙）：

```
Valid Redirect URIs:
  http://localhost:8082/signin-oidc
  https://api.viclai.idv.tw/signin-oidc

Valid Post Logout Redirect URIs:
  http://localhost:5173/login
  https://viclai.idv.tw/login

Web Origins: (此模式不需要，因為瀏覽器不直接打 Keycloak)
```

---

## 5. Migration 步驟（對照現有 Google flow）

| 現有 Google 元件                        | Keycloak BFF 替換                                       |
| --------------------------------------- | ------------------------------------------------------- |
| `.AddGoogle(...)` middleware            | `.AddOpenIdConnect("Keycloak", ...)`                    |
| `GoogleAuthController`                  | `KeycloakAuthController`                                |
| `/signin-google` callback               | `/signin-oidc` callback                                 |
| `Google__ClientId/ClientSecret` env     | `Keycloak__ClientId/ClientSecret` env                   |
| `OnCreatingTicket` 加 picture           | `GetClaimsFromUserInfoEndpoint = true`                  |
| `OnRedirectToAuthorizationEndpoint`     | `OnRedirectToIdentityProvider`                          |
| Frontend `loginServerSide()` URL        | 改成 `/api/auth/keycloak/login`                         |

其他完全不變：
- `AddCookie("Cookies", ...)` 保留
- `AddJwtBearer(...)` 保留
- `DataProtection` 持久化保留
- Cloudflare Tunnel 那套 https 修補保留
- 前端 `AuthContext`、`authService.decodeToken`、`AuthCallback` 全保留

---

## 6. 跟 Template A 的核心差異

|                           | A: PKCE     | B: BFF                       |
| ------------------------- | ----------- | ---------------------------- |
| 前端拿到的 token          | Keycloak 簽 | Backend 自簽                 |
| 後端驗 token              | JWKS 公鑰   | 自己的 symmetric key         |
| Token 過期換新            | 前端 silent renew | 重新登入或 backend refresh |
| iOS Safari cookie 問題    | 無          | 有（同現在）需要 SameSite=None |
| Cloudflare Tunnel 修補     | 不需要       | 需要（同現在）                |

---

## 優缺點

✅ 改動最小，現有架構幾乎照搬
✅ Client secret 安全留在 backend
✅ 前端不用學新 library
✅ Backend 可以塞自訂 claim 進 JWT（例如查 DB 後加 siteId）

❌ Backend 持續扛 OAuth flow 複雜度
❌ Cookie / DataProtection / SameSite 問題還在
❌ 兩層 JWT 邏輯（Keycloak → 自簽）多一層心智負擔
