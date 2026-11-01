---
type: concept
domain: tech
tags: [dotnet, aspnet, jwt, bearer, token, security, refresh-token, jwks]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 12 章：JWT 深入 — 為什麼登出沒有用

## 三個讓人愣住的問題

**問題一：** 使用者按了登出，前端清掉了 token。但如果有人在登出前複製了那串 token，它到期之前仍然完全有效。伺服器不知道使用者登出了。

**問題二：** 管理員在後台把某個使用者停權了。但那個人手上的 token 還在有效期內，繼續呼叫 API 全部成功。

**問題三：** Token 的 `exp` 明明是三分鐘前，測試卻發現它還能用。

三個問題分別對應 JWT 的三個本質特性：**無狀態**、**簽發時快照**、**時鐘偏移容許值**。這一章要把 JWT 的每個環節攤開，包括那些預設值造成的意外。

---

## 一、JWT 的結構

一個 JWT 是三段 Base64URL 編碼的字串，用 `.` 連接：

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjE3NTUxNjgwMDB9.dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
└──────── Header ────────┘└─────────── Payload ───────────┘└────── Signature ──────┘
```

**Header** 描述簽章演算法：

```json
{ "alg": "HS256", "typ": "JWT" }
```

**Payload** 是 claims：

```json
{
  "sub": "123",
  "name": "Vic",
  "role": "Admin",
  "iss": "https://api.example.com",
  "aud": "https://app.example.com",
  "exp": 1755168000,
  "iat": 1755164400,
  "jti": "a3f8-..."
}
```

**Signature** 是對前兩段的簽章。

必須先講清楚一件事，因為誤解它會直接造成資安事故：

**Base64 不是加密。** 任何人拿到 token，貼進任何一個 Base64 解碼器（或 jwt.io）就能讀出完整的 payload。不需要金鑰，不需要破解。

所以 **JWT 的 payload 絕對不能放敏感資料**——密碼、身分證字號、內部系統識別碼、完整的個人資料。簽章保護的是「不可竄改」，不是「不可讀取」。

### 1.1 標準 claims

| Claim | 全名 | 意義 |
| --- | --- | --- |
| `iss` | Issuer | 誰簽發的 |
| `sub` | Subject | 這個 token 代表誰（通常是使用者 ID） |
| `aud` | Audience | 這個 token 給誰用的 |
| `exp` | Expiration | 過期時間（Unix 秒） |
| `nbf` | Not Before | 生效時間 |
| `iat` | Issued At | 簽發時間 |
| `jti` | JWT ID | 唯一識別碼，用於防重放與黑名單 |

---

## 二、簽章：對稱與非對稱

### 2.1 HMAC（HS256）

用同一把金鑰簽發與驗證：

```csharp
var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));
var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
```

簡單，效能好。缺點是**簽發者和驗證者必須共用同一把祕密**。如果有五個微服務都要驗證 token，那把祕密就得散布到五個地方——任何一個洩漏，攻擊者就能簽發任意 token。

**HS256 的金鑰長度至少要 256 位元（32 位元組）。** 太短會拋出 `ArgumentOutOfRangeException`，錯誤碼依長度而不同：1 到 15 位元組是 `IDX10653`（訊息寫「at least '128' bits」，容易讓人以為 128 位元就夠），16 到 31 位元組是 `IDX10720`（key size must be greater than 256 bits），剛好 32 位元組才成功。教學範例常見的 16 字元金鑰就屬於後者。而且不能用「密碼」等級的字串——它必須是高熵的隨機值：

```powershell
# 產生一把足夠的金鑰
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

（更嚴謹的做法是用 `System.Security.Cryptography.RandomNumberGenerator`，上面這行只是快速產生用。）

### 2.2 RSA / ECDSA（RS256、ES256）

用私鑰簽發、公鑰驗證。私鑰只有簽發者持有，公鑰可以公開發布。

這是多服務架構的正解：認證服務持有私鑰，所有 API 用公鑰驗證。公鑰洩漏無害——它本來就是公開的。

公鑰的發布通常透過 **JWKS**（JSON Web Key Set）端點：

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = "https://auth.example.com";   // 自動抓 JWKS
        options.Audience = "my-api";
    });
```

設定 `Authority` 之後，handler 會自動去 `{Authority}/.well-known/openid-configuration` 抓設定、再抓 JWKS 取得公鑰，並且**自動處理金鑰輪替**（透過 header 裡的 `kid` 對應）。Google、Auth0、Entra ID 等外部身分提供者都是這樣接的。

實務建議：自己簽發、單一服務驗證 → HS256 夠用；多服務或使用外部身分提供者 → RS256 + JWKS。

### 2.3 `alg: none` 與演算法混淆攻擊

JWT 規格允許 `alg: none`（不簽章）。早期有很多函式庫會傻傻接受這種 token——攻擊者只要把 header 改成 `none`、payload 改成 `"role": "Admin"`、簽章段留空，就能偽造任意身分。

另一種是**演算法混淆**：系統用 RS256 驗證，攻擊者把 `alg` 改成 `HS256`，並用**公鑰**（公開可得）當作 HMAC 的祕密去簽。如果函式庫盲目依照 header 的 `alg` 選擇驗證方式，就會用公鑰驗過這個偽造的 token。

ASP.NET Core 使用的 `Microsoft.IdentityModel` 函式庫預設已經防範這兩者。但這解釋了為什麼有一個參數絕對不能關：

```csharp
ValidateIssuerSigningKey = true      // 永遠不要設 false
```

也可以更嚴格地限定允許的演算法：

```csharp
options.TokenValidationParameters.ValidAlgorithms = new[] { SecurityAlgorithms.RsaSha256 };
```

---

## 三、`TokenValidationParameters` 逐項

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],

            ValidateAudience = true,
            ValidAudience = builder.Configuration["Jwt:Audience"],

            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),          // ⚠️ 預設是 5 分鐘

            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!)),

            NameClaimType = "name",
            RoleClaimType = "role"
        };
    });
```

| 參數 | 作用 | 關掉的後果 |
| --- | --- | --- |
| `ValidateIssuer` | 檢查 `iss` | 別人簽發的 token 也被接受 |
| `ValidateAudience` | 檢查 `aud` | 給其他系統的 token 能用在這裡 |
| `ValidateLifetime` | 檢查 `exp` / `nbf` | **token 永不過期** |
| `ValidateIssuerSigningKey` | 驗證簽章 | **任何人都能偽造 token** |

四個都應該是 `true`。開發時為了方便關掉其中一個，然後忘記打開，是真實發生過的資安事故。

### 3.1 `ClockSkew`：開頭第三個問題的答案

**預設值是 5 分鐘。**

設計理由是分散式系統中各機器的時鐘不完全同步——簽發者的時鐘快 30 秒的話，剛簽出來的 token 在驗證者看來可能還沒生效。給一點容許值是合理的。

但 5 分鐘太寬鬆了。它意味著：

- 標示 10 分鐘過期的 token，實際上最多可用 15 分鐘
- 測試「token 過期後應該回 401」時，要等超過 5 分鐘才看得到預期行為

現代環境（容器、雲端）的時鐘同步通常在毫秒級，設成 30 秒甚至 `TimeSpan.Zero` 都合理：

```csharp
ClockSkew = TimeSpan.FromSeconds(30)
```

如果打算用「短期 access token」策略（例如 5 分鐘），不調這個值等於策略失效——實際有效期變成 10 分鐘。

---

## 四、簽發 Token

```csharp
public class TokenService : ITokenService
{
    private readonly JwtOptions _options;

    public TokenService(IOptions<JwtOptions> options) { _options = options.Value; }

    public string CreateAccessToken(User user)
    {
        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new("name", user.Name),
        };

        claims.AddRange(user.Roles.Select(r => new Claim("role", r)));

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_options.Key));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _options.Issuer,
            audience: _options.Audience,
            claims: claims,
            notBefore: DateTime.UtcNow,
            expires: DateTime.UtcNow.AddMinutes(_options.AccessTokenMinutes),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}
```

三個細節：

**時間一律用 UTC。** `DateTime.Now` 在時區設定不同的環境會產生錯誤的 `exp`（第 04 章的時區問題在這裡的後果特別嚴重——可能簽出一個已經過期或永不過期的 token）。

**`jti` 要有。** 它是這個 token 的唯一識別碼，是實作黑名單與重放偵測的基礎。

**角色 claim 的名稱要與 `RoleClaimType` 一致。** 這裡用 `"role"`，驗證端也設 `RoleClaimType = "role"`。不一致的話 `[Authorize(Roles = "Admin")]` 會靜默失敗。

---

## 五、金鑰管理

金鑰洩漏等於整個認證體系失守——攻擊者能簽發任意身分的 token。

**絕對不要進版控。** `appsettings.json` 裡不能有真實金鑰。開發用 User Secrets，生產用 K8s Secret 或 Vault：

```yaml
env:
  - name: Jwt__Key
    valueFrom:
      secretKeyRef:
        name: jwt-secret
        key: signing-key
```

注意 K8s 的 Secret **預設只是 Base64 編碼，不是加密**——任何有 namespace read 權限的人都能讀出來。要真正的加密需要開啟 etcd encryption at rest 或改用 Vault / External Secrets Operator。

**要能輪替。** 金鑰洩漏時必須能換掉。但直接換掉會讓所有現存 token 立刻失效（所有人被登出）。平順的做法是支援多把金鑰同時有效：

```csharp
options.TokenValidationParameters.IssuerSigningKeys = new[]
{
    new SymmetricSecurityKey(Encoding.UTF8.GetBytes(currentKey)),
    new SymmetricSecurityKey(Encoding.UTF8.GetBytes(previousKey))
};
```

簽發用新金鑰，驗證接受新舊兩把。等舊 token 全部過期後再移除舊金鑰。用 RS256 + JWKS 時這件事由 `kid` 自動處理，是非對稱簽章的另一個優勢。

---

## 六、撤銷：JWT 最大的弱點

回到開頭的問題一和二。JWT 是**無狀態**的——伺服器不保存任何 session，驗證只靠簽章與 `exp`。這是它的優點（水平擴展不需要共用 session store），也是它的根本限制：

**簽發出去的 token 在過期之前無法收回。**

登出、停權、改密碼、權限調整——這些都無法讓已簽發的 token 失效。有四種應對方式。

### 6.1 短期 access token + refresh token（主流方案）

```text
Access token：5–15 分鐘，無狀態驗證，用於呼叫 API
Refresh token：7–30 天，儲存在資料庫，用於換新的 access token
```

撤銷時刪掉資料庫裡的 refresh token。使用者手上的 access token 仍然有效，但**最多再撐 15 分鐘**就無法續期了。這是「無狀態的效能」與「可撤銷性」之間的務實折衷。

```csharp
[HttpPost("refresh")]
public async Task<IActionResult> RefreshAsync(RefreshRequest req, CancellationToken ct)
{
    var stored = await _db.RefreshTokens
        .FirstOrDefaultAsync(t => t.TokenHash == Hash(req.RefreshToken), ct);

    if (stored is null || stored.ExpiresAt < DateTimeOffset.UtcNow || stored.RevokedAt is not null)
    {
        return Unauthorized();
    }

    // 輪替：舊的立刻作廢，發一組新的
    stored.RevokedAt = DateTimeOffset.UtcNow;

    var user = await _db.Users.FindAsync(new object[] { stored.UserId }, ct);
    var newRefresh = CreateRefreshToken(user!);
    _db.RefreshTokens.Add(newRefresh);
    await _db.SaveChangesAsync(ct);

    return Ok(new
    {
        accessToken = _tokenService.CreateAccessToken(user!),
        refreshToken = newRefresh.PlainValue
    });
}
```

三個設計要點：

**存雜湊而非明文。** Refresh token 存在資料庫裡，如果資料庫被讀走，明文 token 等同於帳號被接管。存 SHA-256 雜湊，比對時雜湊後比對。

**輪替（rotation）。** 每次刷新都作廢舊的、發新的。這讓失竊的 refresh token 只能用一次。

**重用偵測。** 如果收到一個已經被作廢的 refresh token，代表它被竊取了（合法使用者已經用過它換新的，攻擊者拿舊的來用，或反之）。這時應該**撤銷該使用者的所有 refresh token**，強制重新登入。

### 6.2 黑名單

登出時把 `jti` 寫進 Redis，設定 TTL 等於 token 剩餘壽命，每次驗證時檢查：

```csharp
options.Events = new JwtBearerEvents
{
    OnTokenValidated = async context =>
    {
        var jti = context.Principal?.FindFirst(JwtRegisteredClaimNames.Jti)?.Value;
        var cache = context.HttpContext.RequestServices
            .GetRequiredService<IDistributedCache>();

        if (jti is not null && await cache.GetStringAsync($"revoked:{jti}") is not null)
        {
            context.Fail("Token has been revoked");
        }
    }
};
```

代價是每個請求多一次快取查詢——這讓 JWT 失去了「無狀態」的效能優勢。折衷方案是只黑名單「明確登出」與「停權」這類事件，量不大。

### 6.3 版本號

在使用者資料上放一個 `SecurityStamp`，簽發時放進 claim。改密碼或停權時遞增它，驗證時比對。

一樣需要每次查資料庫（可以快取），但比黑名單更精確——它能一次作廢某個使用者的所有 token。ASP.NET Core Identity 內建這個機制。

### 6.4 就是接受它

如果 access token 只有 5 分鐘，「停權後最多還能用 5 分鐘」對很多業務是可接受的風險。不要為了理論上的完美，把系統改成每個請求都查資料庫——那還不如直接用 session。

---

## 七、Token 存在前端哪裡

| 位置 | XSS | CSRF | 刷新頁面後 |
| --- | --- | --- | --- |
| `localStorage` | **可被讀走** | 免疫 | 保留 |
| `sessionStorage` | **可被讀走** | 免疫 | 分頁關閉即失 |
| JS 記憶體變數 | 較難竊取 | 免疫 | **消失** |
| `HttpOnly` cookie | JS 讀不到 | **需防護** | 保留 |

主流的折衷方案：

```text
Access token  → 存在 JS 記憶體（頁面刷新就沒了，但很快能換回來）
Refresh token → 存在 HttpOnly + Secure + SameSite cookie
```

XSS 攻擊者拿不到 refresh token（`HttpOnly`），access token 即使被拿到也很快過期。刷新頁面時前端呼叫 `/refresh`，瀏覽器自動帶上 cookie，換回新的 access token。

代價是 refresh 端點要防 CSRF（`SameSite=Strict` 或 anti-forgery token）。

---

## 八、`JwtBearerEvents`：擴充點

```csharp
options.Events = new JwtBearerEvents
{
    OnMessageReceived = context =>
    {
        // SignalR 或 WebSocket 無法帶 Authorization header，改從 query string 取
        var token = context.Request.Query["access_token"];
        var path = context.HttpContext.Request.Path;

        if (!string.IsNullOrEmpty(token) && path.StartsWithSegments("/hubs"))
        {
            context.Token = token;
        }
        return Task.CompletedTask;
    },

    OnAuthenticationFailed = context =>
    {
        if (context.Exception is SecurityTokenExpiredException)
        {
            // 讓前端能區分「過期」與「無效」，決定要刷新還是重新登入
            context.Response.Headers["Token-Expired"] = "true";
        }
        return Task.CompletedTask;
    },

    OnChallenge = context =>
    {
        // 自訂 401 的回應內容
        return Task.CompletedTask;
    }
};
```

`OnMessageReceived` 的 query string 用法要注意：**URL 會被記錄在存取日誌、瀏覽器歷史、Referer header 裡**。只在真的無法用 header 的協定（WebSocket）上使用，並限制路徑範圍。

---

## 九、常見誤解

**「JWT 是加密的。」**
不是。payload 是 Base64 編碼，任何人都能讀。要保密內容需要 JWE（加密的 JWT），但那很少用——正確做法是不要把敏感資料放進 token。

**「登出後 token 就失效了。」**
不會。JWT 無狀態，伺服器不知道你登出。前端清掉 token 只是自己不再使用它；被複製走的副本仍然有效到過期。

**「`exp` 到了就一定不能用了。」**
預設有 5 分鐘的 `ClockSkew` 容許值。標示 10 分鐘的 token 實際可用 15 分鐘。要精確就把它調小。

**「token 有效期設長一點比較方便。」**
有效期就是「被竊取後的攻擊視窗」。長期 access token 加上無法撤銷，等於把帳號交出去。用短期 access token + refresh token。

**「refresh token 可以明文存資料庫。」**
資料庫被讀走等於所有帳號被接管。存雜湊，並實作輪替與重用偵測。

**「把所有權限放進 token，就不用每次查資料庫了。」**
權限變更要等 token 過期才生效，而且 token 會膨脹、payload 可讀。放使用者識別碼與少量角色即可。

---

## 十、同事會來問你的問題

**Q：使用者被停權了，為什麼還能繼續呼叫 API？**
JWT 無狀態，簽發時的資訊是快照。停權不會讓已簽發的 token 失效。解法是縮短 access token 有效期（5–15 分鐘）並撤銷 refresh token，或加黑名單 / SecurityStamp 檢查。

**Q：token 明明過期了測試還能用。**
`ClockSkew` 預設 5 分鐘。設成 `TimeSpan.FromSeconds(30)` 或 `TimeSpan.Zero`。

**Q：`IDX10653`／`IDX10720` 金鑰太短是什麼意思？**
HS256 要求金鑰至少 256 位元（32 位元組）；不足 16 位元組報 `IDX10653`，16 到 31 位元組報 `IDX10720`。而且必須是高熵的隨機值，不能用人類可記憶的密碼。

**Q：token 放 localStorage 還是 cookie？**
主流折衷是 access token 放 JS 記憶體、refresh token 放 `HttpOnly` cookie。前者讓 XSS 難以竊取長期憑證，後者讓刷新頁面後還能續期。refresh 端點記得防 CSRF。

**Q：微服務之間怎麼共用 JWT 驗證？**
改用非對稱簽章（RS256）+ JWKS。認證服務持有私鑰，各 API 設定 `Authority` 自動抓公鑰。不要把 HS256 的對稱金鑰散布到每個服務。

**Q：SignalR 連線帶不了 `Authorization` header。**
用 `OnMessageReceived` 事件從 query string 取 `access_token`，並限制只在 hub 路徑生效。注意 URL 會進日誌與瀏覽器歷史。

**Q：前端要怎麼知道該刷新 token 還是重新登入？**
在 `OnAuthenticationFailed` 裡辨識 `SecurityTokenExpiredException` 並加一個回應 header（例如 `Token-Expired: true`）。前端看到這個就走刷新流程，否則導向登入。

---

## 連結

- [[basics-12-jwt-login]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[11-authentication]] — 上一章：scheme 與 claims
- [[13-oauth-oidc]] — 下一章：Google 登入與 OIDC
- [[14-authorization]] — 用 claims 做授權決策
- [[17-configuration-and-secrets]] — 金鑰的注入與輪替
- [[vault]] — Secret 管理
