# .NET 6 Web API JWT 驗證與授權完整設定與實作指南

## Authentication 與 Authorization：理論差異與關係

**Authentication（身分驗證）指的是確認使用者身分的過程，例如透過帳號密碼登入來驗證「你是誰」。驗證成功後，才進一步進行Authorization（授權）**，也就是根據該使用者的身分與權限決定「你可以做什麼或存取哪些資源」。簡而言之，Authentication 是先確認使用者的身份真偽，Authorization 則在此基礎上決定該用戶可執行的操作或存取的資源。兩者關係密切但功能不同：身分驗證通常是第一步且需要使用者提供憑證，而授權發生在驗證通過之後，自動套用預先定義的策略與規則來控管使用者權限。只有**通過 Authentication** 的使用者，才會進入 Authorization 流程；兩者相輔相成，共同保護應用程式的安全。

## JWT 在 Authentication 中的角色與運作方式

JWT（JSON Web Token）是在 Token-based 驗證中常用的**自包含（self-contained）令牌格式。當使用者成功通過身分驗證（例如登入）後，伺服器會簽發一個 JWT 作為憑證。JWT 內含使用者的身份識別資訊和權限宣告（claims），並經過數位簽章（使用伺服器端的密鑰）以確保無法被竄改。由於 JWT 已包含所需的使用者資訊，後續每次請求時，用戶端都會在 HTTP Header 中附帶此 JWT，讓伺服器據此驗證使用者身份（這實現了無狀態 stateless 認證）。伺服器透過驗證 JWT 的簽章和內容來確認請求者的身份，以及取得其中的權限宣告，進而決定是否授權存取資源。JWT 的運作方式使得伺服器無需保存會話狀態（不像傳統使用 Session 的方式），具備跨服務傳遞身份**的能力：只要 JWT 有效且簽章正確，不同伺服器都可以獨立驗證它並信任其中的資訊。總而言之，在 Authentication 機制中 JWT 扮演了“通行證”的角色——用戶登入後取得 JWT，日後每次呼叫 API 都攜帶此令牌作為身份憑據，伺服器則負責驗證該 JWT 的有效性來完成身份確認與授權判定。

## .NET 6 中設定 JWT 驗證

在 .NET 6 的 Web API 專案中，我們需要透過 **服務註冊** 及 **中介軟體** 設定，讓應用程式使用 JWT 作為身份驗證機制。以下將說明如何在 `.NET 6` 的專案（使用最低主機模式，沒有傳統 Startup.cs 時）進行設定；若使用傳統的 Startup 架構，對應的配置則是在 `Startup.ConfigureServices` 與 `Startup.Configure` 中完成，概念上相同。

### Program.cs 中的服務與中介軟體設定

首先，在 `Program.cs` 裡註冊 **Authentication** 和 **Authorization** 服務，並配置 JWT Bearer 驗證機制：

```csharp
var builder = WebApplication.CreateBuilder(args);

// 1. 添加 JWT 驗證服務
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        // 設定 Token 驗證的參數
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,              // 驗證 Issuer
            ValidateAudience = true,            // 驗證 Audience
            ValidateLifetime = true,            // 驗證 Token 有效期限
            ValidateIssuerSigningKey = true,    // 驗證簽名密鑰 (確保 Token 簽章正確)
            ValidIssuer = "YourIssuerName",     // 預期的 Issuer
            ValidAudience = "YourAudienceName", // 預期的 Audience
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes("YourSecretSigningKey"))
        };
    });

// 2. 添加授權服務
builder.Services.AddAuthorization();

var app = builder.Build();

// 3. 加入驗證與授權中介軟體到管線
app.UseAuthentication();
app.UseAuthorization();

// ... (其他中介軟體與端點設定)

```

上述程式碼完成了 JWT 驗證的主要設定：

1. **AddAuthentication**: 使用 JWT 持有人驗證 (`JwtBearerDefaults.AuthenticationScheme`) 作為預設的驗證方案。
2. **AddJwtBearer**: 設定 JWT Bearer 認證的細節，包括 Token 驗證參數。
3. **TokenValidationParameters**: 定義如何驗證收到的 JWT，例如簽發者、受眾、簽章金鑰等（詳見下節）。
4. **AddAuthorization**: 啟用授權機制，讓 `[Authorize]` 等特性生效。
5. 在建構 `app` 之後，透過 **UseAuthentication()** 和 **UseAuthorization()** 將驗證與授權中介軟體加入 HTTP 要求管線，且須確保它們在需要保護資源的路由之前呼叫。

> **注意：**在傳統 Startup.cs 中，以上服務註冊步驟會寫在 ConfigureServices，中介軟體的 UseAuthentication();、UseAuthorization(); 則放在 Configure 方法中，通常在 UseRouting() 之後、UseEndpoints() 之前。
> 

### Token 驗證參數設定（Issuer、Audience、SigningKey 等）

JWT 驗證時可透過 `TokenValidationParameters` 設定多種驗證條件，確保所收到的 Token 符合預期。以下是常見的參數及其意義：

| **設定項目** | **說明** |
| --- | --- |
| **ValidateIssuer** | 是否驗證 Token 的 Issuer（發行者）。設為 `true` 時，系統會檢查收到的 JWT 之 Issuer 是否匹配 `ValidIssuer`。通常應啟用，以防止來自不明發行者的 Token。 |
| **ValidIssuer** | 合法的 Issuer 名稱。只有 JWT 中的 Issuer 欄位符合此值時才視為通過驗證。例如可設為發行 Token 的服務或域名。 |
| **ValidateAudience** | 是否驗證 Token 的 Audience（受眾）。若設為 `true`，則 JWT 的 `aud` 欄位需匹配 `ValidAudience`。在單一服務應用中可選擇設為 `false`（不驗證受眾）。 |
| **ValidAudience** | 合法的 Audience 值。只有 JWT 中的 Audience 符合此值才會被接受。可用來限定 Token 僅供特定服務/客戶端使用。 |
| **ValidateLifetime** | 是否驗證 Token 的有效期。建議設為 `true`，確保過期的 JWT 會被拒絕。這依賴 JWT 的 `exp`（過期時間）與 `nbf`（生效時間）宣告。 |
| **ValidateIssuerSigningKey** | 是否驗證簽署用的金鑰。設為 `true` 時，系統會使用下方提供的 `IssuerSigningKey` 驗證 JWT 簽章的有效性，確保 Token 未被竄改。一般應啟用此項以驗證簽章。 |
| **IssuerSigningKey** | 用於簽署 Token 的金鑰（對稱密鑰或非對稱私鑰）。驗證時伺服器會用此金鑰來驗證 JWT 的數位簽章是否正確，以判斷 Token 是否未被修改。 |

以上參數可以存放於組態檔（如 *appsettings.json*）中，以便管理。例如可在 *appsettings.json* 設置：

```json
"JwtSettings":{
"Issuer":"JwtAuthDemo",
"Audience":"JwtAuthDemoClient",
"SignKey":"0123456789ABCDEF0123456789ABCDEF"// 至少 16 字元的安全隨機字串
}
```

再從 `Configuration` 中讀取對應值來配置 `TokenValidationParameters`。如此可避免將敏感資訊硬編碼在程式中。

> **補充：**預設情況下，JWT 驗證會將 sub (Subject) 宣告對應到 User.Identity.Name。您也可以透過 TokenValidationParameters.NameClaimType 和 RoleClaimType 來指定哪些 JWT 宣告用於識別使用者名稱和角色。例如，若 JWT Payload 中使用 "roles" 欄位表示角色清單，可將 RoleClaimType 設為 "roles"，讓 [Authorize(Roles="...")] 正確識別。
> 

### 產生 JWT Token 的方式（登入範例）

在伺服器端，我們通常在使用者通過登入驗證後產生 JWT Token。以下提供一個簡化的產生 Token 範例（假設已成功驗證使用者帳密）：

```csharp
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.IdentityModel.Tokens;
using System.Text;

// 假設這些值從組態取得
string issuer = Configuration["JwtSettings:Issuer"];
string audience = Configuration["JwtSettings:Audience"];
string signingKey = Configuration["JwtSettings:SignKey"];

// 建立 JWT 的 Claims (聲明)
var claims =new List<Claim> {
new Claim(JwtRegisteredClaimNames.Sub, user.UserName),// 使用者名稱識別
new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),// 唯一 JWT ID
new Claim(ClaimTypes.Name, user.UserName),// Name 權杖
// 如果有角色資訊，將角色加入權限宣告
new Claim(ClaimTypes.Role,"Admin")// 範例：賦予 Admin 角色，實際應來自使用者角色資料
};

// 產生簽名用的金鑰與認證物件
var securityKey =new SymmetricSecurityKey(Encoding.UTF8.GetBytes(signingKey));
var credentials =new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);

// 建立 JWT Token 內容描述
var tokenDescriptor =new SecurityTokenDescriptor {
    Issuer = issuer,
    Audience = audience,
    Subject =new ClaimsIdentity(claims),
    Expires = DateTime.UtcNow.AddMinutes(30),// 設定 Token 有效期，例如 30 分鐘
    SigningCredentials = credentials
};

// 使用 JwtSecurityTokenHandler 產生 JWT 字串
var tokenHandler =new JwtSecurityTokenHandler();
SecurityToken securityToken = tokenHandler.CreateToken(tokenDescriptor);
string jwtToken = tokenHandler.WriteToken(securityToken);

// 將 Token 字串回傳給客戶端（例如包裝在 JSON 回應中）
```

上述程式會產生一個 JWT，內容包含我們指定的 Issuer、Audience、Claims 和到期時間等，並使用給定的密鑰進行簽名。產生的 `jwtToken`（字串）即可發送給客戶端保存。**切記：**在產生 Token 時應謹慎選擇有效期限（`Expires`），期限太長可能增加安全風險，太短則可能讓使用者頻繁重新登入。

為了安全，JWT 的密鑰（例如上述的 `signingKey`）應足夠複雜且妥善保管。常用的 HMAC-SHA256 簽名演算法要求對稱密鑰至少 16 字元以上。在生產環境中，密鑰通常放在安全的配置中或使用機密管理機制，而不直接寫在程式碼中。

## Authorization 的使用與設定方式

完成 JWT Authentication 設定後，就可以在應用中透過 Authorization 機制來保護 API。典型作法是使用 **[Authorize]** 屬性來裝飾需要保護的控制器或動作：

- `[Authorize]`：未指定參數時，表示要求使用者已通過驗證即可存取（任何已驗證使用者皆可）。
- `[Authorize(Roles = "Admin,Manager")]`：只有當 JWT 中包含角色為 *Admin* 或 *Manager* 的使用者才允許存取。這要求我們在產生 JWT 時已將使用者的角色資訊加入 Token (例如上例中使用 `ClaimTypes.Role`)，且在 TokenValidationParameters 中正確設定 `RoleClaimType` 讓系統識別角色宣告。
- `[Authorize(Policy = "PolicyName")]`：使用預先在 `AddAuthorization` 時設定的授權策略（Policy）來限制存取。例如可以定義特定 **權限** 要求的策略，檢查某個自訂的 Claim 是否存在或符合條件。

要讓某些公開 API 無需驗證即可訪問，可以使用 `[AllowAnonymous]` 屬性跳過驗證/授權。例如登入或註冊的 API 常標註 `[AllowAnonymous]`，以允許未持有 JWT 的請求。

在 .NET 6 Minimal API 中也類似，您可以用 `RequireAuthorization()` 保護路由，或用 `AllowAnonymous()` 開放。例如：

```csharp
app.MapGet("/profile", (ClaimsPrincipal user) => GetUserProfile(user))
   .RequireAuthorization();       // 此路由需要已驗證（等同 [Authorize]）

app.MapPost("/signin", (LoginDto dto) => SignIn(dto))
   .AllowAnonymous();             // 此路由允許匿名（等同 [AllowAnonymous]）
```

配合之前 JWT 的設定，當用戶端請求含有有效 JWT 時，ASP.NET Core 會自動解析 JWT 成功驗證身份，並在 `ClaimsPrincipal user` 中提供 JWT 的 Claim 資訊；如果沒有提供 JWT 或 JWT 驗證失敗，則 `.RequireAuthorization()` 會導致該請求被拒絕（回傳 HTTP 401 或 403 狀態）。

在進一步的授權策略設定中，可以使用 `AddAuthorization(options => { ... })` 來配置 **角色/權限**的策略。例如：

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"));
    options.AddPolicy("Over18Only", policy =>
        policy.RequireClaim("Age","18","19","20"));// 需要 Age 聲明符合條件
});

```

然後對應的控制器方法標註 `[Authorize(Policy = "AdminOnly")]` 或 `[Authorize(Policy = "Over18Only")]` 即可實現更細緻的權限控管。這種**基於策略（Policy-Based）**的授權方式可靈活定義各種規則，包括檢查 JWT 中的自訂 Claims 等，滿足複雜的權限需求。

## 透過 HTTP Header 傳遞 JWT

JWT 通常經由 HTTP **Authorization header** 傳遞。當客戶端拿到 JWT 之後，需在往後的每個請求加入類似如下的 Header 來提供憑證：

```
Authorization: Bearer <JWT 字串>
```

例如，如果取得的 Token 是 `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`，在呼叫受保護的 API 時，HTTP 請求頭應包含：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

其中關鍵字 **Bearer** 後須接空格再附上 Token。本機制利用了 OAuth2 的 Bearer token 傳輸格式，而 **AddJwtBearer** 預設會從 Authorization header 中解析「Bearer 」開頭的 Token 字串並自動進行驗證。

在前端實作上，常見做法是使用 AJAX 或 Fetch API 時，在請求的 header 加入 Authorization。例如：

```jsx
fetch('/api/values', {
headers: {
'Authorization':'Bearer ' +localStorage.getItem('jwtToken')
  }
});
```

或在 Axios 中設定預設 header。無論用何種方式，確保每次呼叫受保護資源時都攜帶正確的 JWT，才能順利通過伺服器端的驗證中介軟體。

## JWT 驗證流程：客戶端與伺服器互動簡圖

![image.png](image.png)

上述圖例展示了**使用 JWT 進行身份驗證的流程**：

1. **使用者登入請求**：用戶端（例如瀏覽器或App）將使用者的帳號/密碼提交到伺服器的登入 API。
2. **伺服器驗證並簽發 JWT**：伺服器驗證登入憑證，成功則為該使用者產生一個 JWT，內含使用者身份資訊、權限Claims等，並以伺服器密鑰簽名後回傳給用戶端。這個 JWT 就相當於後續通信的「通行證」。
3. **用戶端儲存 JWT**：用戶端收到 JWT，通常會將它儲存在**瀏覽器的 Local Storage、Session Storage 或 Cookie**（若存於 Cookie 應設為 HttpOnly）中，方便之後的請求使用。重要的是要妥善保存，避免讓第三方取得。
4. **用戶端隨後請求附帶 JWT**：當用戶端需要呼叫受保護的API時，會在請求的 HTTP Header 中加入先前取得的 JWT（即 `Authorization: Bearer <token>`）。伺服器因此可以在每次請求中拿到該 JWT。
5. **伺服器驗證 JWT**：伺服器在收到請求後，透過前述設定的 JWT 驗證中介軟體，檢查 Authorization Header 中的 JWT 是否存在及有效。如果沒有 JWT 或無法通過驗證（例如簽章不符或已過期），回傳未授權錯誤（HTTP 401 或 403）；如果 JWT 有效，則擷取其中的使用者資訊與權限 Claims。
6. **授權並回應**：基於驗證後取得的身份及權限，伺服器執行對應的業務邏輯。如果使用者具備存取該資源的權限，伺服器就處理請求並回傳所需的資料；若權限不足則回傳拒絕存取的錯誤。整個流程中，伺服器**不需要保存會話狀態**，因為身份/權限資訊都透過JWT在每次請求中傳遞了。

上述流程確保了使用 JWT 進行 Authentication/Authorization 的安全性與便利性：只有持有合法 JWT 的請求才能通過驗證，而 JWT 本身以數位簽章防止竄改。此外，為了增強安全，開發人員可以考慮 JWT 的**過期策略**與**刷新機制**，以及在必要時實作 Token **黑名單**（例如將特定 JWT 的 `jti`加入黑名單，以使其在到期前失效）。總之，JWT 提供了一種無狀態且高效的身分驗證與授權方式，非常適合 .NET 6 Web API 等現代 Web 應用的需求。