# Google OAuth 2.0 教學

## 名詞定義

| 術語                  | 說明                                                                 |
| --------------------- | -------------------------------------------------------------------- |
| OAuth 2.0             | 授權框架，讓第三方應用取得使用者資源的存取權，不需要使用者的帳號密碼 |
| OpenID Connect (OIDC) | 建立在 OAuth 2.0 上的身份驗證層，用來確認「你是誰」                  |
| Authorization Code    | Google 授權後給的一次性短效代碼，只能換一次 token                    |
| Access Token          | 用來存取 Google API 的 token（如讀取 Gmail）                         |
| ID Token              | JWT 格式，包含使用者基本資訊（sub、email、name、picture）            |
| Refresh Token         | 長效 token，可換新的 Access Token，需要額外申請 offline_access       |
| Client ID             | 在 Google Cloud Console 建立的應用識別碼，公開的                     |
| Client Secret         | 只有後端才能持有，用來換 token，絕對不能暴露給前端                   |
| Redirect URI          | Google 完成授權後轉回的 URL，必須在 Console 事先註冊                 |
| Scope                 | 申請的權限範圍（`openid email profile`）                             |
| JWT (JSON Web Token)  | 由後端自行簽發的 token，用來維持登入狀態                             |

---

## 三種 Flow 比較

|                      | Server-side Flow                  | SPA Code Exchange                    | GIS One Tap              |
| -------------------- | --------------------------------- | ------------------------------------ | ------------------------ |
| 誰發起 OAuth         | 後端                              | 前端                                 | 前端（Google JS SDK）    |
| 需要後端             | ✅                                | ✅                                   | ❌                       |
| Client Secret        | 安全（只在後端）                  | 安全（只在後端 exchange API）        | 完全不需要               |
| 前端取得             | 後端簽發的 JWT                    | 後端簽發的 JWT                       | Google id_token          |
| 頁面跳轉             | 整頁 redirect                     | 整頁 redirect                        | Popup / FedCM，不離開頁面|
| iOS Safari 支援      | ✅                                | ✅                                   | ⚠️ 不穩定（ITP 擋 cookie）|
| 適用場景             | 傳統 MPA、需要後端參與            | SPA、後端必須運行                    | SPA、純前端驗證、開發測試|

---

## Flow 1：Server-side Redirect Flow

```
使用者點登入
  → 前端導向 GET /api/auth/google/login
  → 後端 Challenge Google（回傳 302 到 Google 登入頁）
  → 使用者完成 Google 登入
  → Google 302 → GET /api/auth/google/callback?code=xxx
  → 後端用 code 換 tokens，解析 ID Token
  → 後端簽發 JWT，302 redirect 前端 /auth/callback?token=xxx
  → 前端儲存 JWT
```

---

## Flow 3：Google Identity Services (GIS) One Tap

不需要後端，前端直接從 Google 拿 id_token。

```
使用者進入頁面
  → google.accounts.id.initialize({ client_id, callback })
  → google.accounts.id.prompt()
  → Google 在頁面上彈出帳號選擇框（不離開頁面）
  → 使用者選擇帳號
  → callback({ credential: id_token }) 被呼叫
  → 前端 decode id_token → 取得 name / email / picture
```

### Google Cloud Console 設定

GIS One Tap 使用「已授權的 JavaScript 來源」，不用設定 redirect URI：

```
http://localhost:5173
https://your-frontend-domain.com
```

### 初始化與顯示

```typescript
window.google.accounts.id.initialize({
  client_id: GOOGLE_CLIENT_ID,
  callback: (response) => {
    const idToken = response.credential;
    // decode 或存起來
  },
  cancel_on_tap_outside: false,
});

window.google.accounts.id.prompt(); // 顯示 One Tap 浮動框
```

### TypeScript 型別宣告

GIS 沒有官方 npm types，需自行宣告：

```typescript
// src/types/google-gis.d.ts
interface Window {
  google: {
    accounts: {
      id: {
        initialize(config: {
          client_id: string;
          callback: (response: { credential: string }) => void;
          cancel_on_tap_outside?: boolean;
          auto_select?: boolean;
        }): void;
        renderButton(element: HTMLElement, options: {
          theme?: "outline" | "filled_blue" | "filled_black";
          size?: "large" | "medium" | "small";
          width?: number;
          locale?: string;
        }): void;
        prompt(): void;
        disableAutoSelect(): void;
        revoke(hint: string, done: () => void): void;
      };
    };
  };
}
```

### 行動裝置支援限制

One Tap 依賴第三方 cookie（Google iframe），iOS Safari 預設啟用 ITP（Intelligent Tracking Prevention）會擋掉這個機制：

| 平台 | 支援狀況 |
| --- | --- |
| Android Chrome | ✅ 正常 |
| iOS Chrome | ⚠️ 不穩定 |
| iOS Safari | ❌ 通常不出現 |

需要跨平台可靠登入時，使用 redirect flow（後端）。

---

## Flow 2：Frontend Code Exchange Flow（SPA 常用）

```
使用者點登入
  → 前端導向 Google 授權頁（帶 client_id、redirect_uri、scope）
  → 使用者完成 Google 登入
  → Google 302 → 前端 /auth/callback?code=xxx
  → 前端 POST /api/auth/google/exchange { code, redirectUri }
  → 後端用 code + client_secret 換 Google tokens
  → 後端解析 ID Token，取出 sub / email / name / picture
  → 後端簽發 JWT 回傳
  → 前端儲存 JWT
```

---

## 前端職責與應設計的 function

### 發起登入
```typescript
const initiateGoogleLogin = () => {
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    redirect_uri: `${window.location.origin}/auth/callback`,
    response_type: 'code',
    scope: 'openid email profile',
  });
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
};
```

### 處理 callback（接收 code，換 JWT）
```typescript
const handleAuthCallback = async (): Promise<void> => {
  const code = new URLSearchParams(window.location.search).get('code');
  if (!code) throw new Error('Missing auth code');

  const { token } = await exchangeCode(code, `${window.location.origin}/auth/callback`);
  localStorage.setItem('token', token);
  navigate('/');
};
```

### 呼叫後端 exchange API
```typescript
const exchangeCode = async (code: string, redirectUri: string): Promise<{ token: string }> => {
  const res = await fetch('/api/auth/google/exchange', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, redirectUri }),
  });
  if (!res.ok) throw new Error('Exchange failed');
  return res.json();
};
```

### 攜帶 JWT 發 API 請求
```typescript
const authFetch = (url: string, options?: RequestInit): Promise<Response> => {
  const token = localStorage.getItem('token');
  return fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${token}`,
    },
  });
};
```

### 登出
```typescript
const logout = (): void => {
  localStorage.removeItem('token');
  navigate('/login');
};
```

---

## 雙模式架構：有後端 / 無後端彈性切換

同一個前端支援兩種登入路徑：

```text
有後端：按鈕 → loginServerSide() → redirect → /auth/callback?token= → loginWithToken(jwt)
無後端：One Tap 自動彈出 → callback(idToken) → loginWithToken(idToken)
```

兩條路最終都呼叫 `loginWithToken(token)`，差別只在 token 的來源與格式。

### 前端直接 decode token（不打後端）

Google id_token 和後端自簽 JWT 都是 JWT 格式，可在前端直接 decode payload 取得使用者資訊：

```typescript
decodeToken(token: string): AuthUser {
  const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  const p = JSON.parse(atob(base64));
  if (p.exp * 1000 < Date.now()) throw new Error("Token expired");

  // Google id_token 用短 claim name，.NET JWT 用長 URI
  const NET_SUB   = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier";
  const NET_EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress";
  const NET_NAME  = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name";

  return {
    id:     p.sub   ?? p[NET_SUB]   ?? "",
    name:   p.name  ?? p[NET_NAME]  ?? "",
    email:  p.email ?? p[NET_EMAIL] ?? "",
    avatar: p.picture ?? "",
  };
}
```

**注意**：JWT payload 用 base64url 編碼（`-` 和 `_`），`atob()` 需要標準 base64（`+` 和 `/`），轉換時要 replace。

### .NET JWT claim name 對照

.NET `ClaimTypes` 產生的 JWT，claim key 是長 URI：

| 欄位 | Google id_token | .NET ClaimTypes |
| --- | --- | --- |
| id | `sub` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier` |
| email | `email` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` |
| name | `name` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name` |
| avatar | `picture` | `picture`（自訂 claim，短名稱） |

若要讓前端 decode 方便，後端 `GenerateJwt` 改用短 claim name：

```csharp
var claims = new[]
{
    new Claim("sub",     id ?? ""),
    new Claim("picture", avatar ?? ""),
    new Claim("email",   email),
    new Claim("name",    name),
};
```

---

## 前端 Auth 邏輯的組織方式（物件模式）

把所有 auth 相關函式打包成一個物件，與 React 狀態層分離：

```typescript
// authService.ts — 純函式，不含 React
export const AuthService = {
  loginServerSide(): void { ... },   // Flow A
  loginSPA(): void { ... },          // Flow B
  extractServerToken(): string | null { ... },
  extractSPACode(): string | null { ... },
  async exchangeCode(code: string): Promise<string> { ... },
  storeToken(token: string): void { ... },
  getStoredToken(): string | null { ... },
  clearToken(): void { ... },
  async fetchMe(token: string): Promise<AuthUser> { ... },
};
```

```typescript
// AuthContext.tsx — React 狀態層，呼叫 AuthService
function login() { AuthService.loginSPA(); }       // 切換 flow 改這一行
async function loginWithToken(token: string) {
  AuthService.storeToken(token);
  const user = await AuthService.fetchMe(token);
  setUser(user);
}
```

**好處：**

- `authService.ts` 可單獨測試，不需要 React
- 切換 Flow A / B 只改一行（`loginSPA` ↔ `loginServerSide`）
- AuthContext 只負責狀態，不混入 OAuth 細節

---

## AuthCallback：同時支援兩種 flow

`/auth/callback` 一個頁面處理兩種情況：

```typescript
useEffect(() => {
  if (called.current) return;  // 防止 StrictMode 雙重觸發
  called.current = true;

  // Flow A：後端帶回 ?token=xxx
  const serverToken = AuthService.extractServerToken();
  if (serverToken) {
    loginWithToken(serverToken).then(() => navigate("/homepage"));
    return;
  }

  // Flow B：Google 帶回 ?code=xxx
  const code = AuthService.extractSPACode();
  if (!code) { navigate("/login"); return; }

  AuthService.exchangeCode(code)
    .then(loginWithToken)
    .then(() => navigate("/homepage"))
    .catch(() => { AuthService.clearToken(); navigate("/login"); });
}, []);  // eslint-disable-line react-hooks/exhaustive-deps
```

---

## 後端職責與應設計的 endpoint（ASP.NET Core）

| Endpoint                         | 說明                                                            |
| -------------------------------- | --------------------------------------------------------------- |
| `GET /api/auth/google/login`     | Server-side flow：觸發 Google Challenge                         |
| `GET /api/auth/google/callback`  | Server-side flow：接收 Google callback，簽發 JWT，redirect 前端 |
| `POST /api/auth/google/exchange` | SPA flow：接收前端的 code，換 token，簽發 JWT                   |
| `GET /api/auth/google/me`        | 驗證 JWT，回傳當前使用者資訊                                    |

### exchange endpoint 核心邏輯

```csharp
// 1. 用 code 換 Google tokens
var tokenResponse = await httpClient.PostAsync(
    "https://oauth2.googleapis.com/token",
    new FormUrlEncodedContent(new Dictionary<string, string>
    {
        ["code"] = request.Code,
        ["client_id"] = _configuration["Google:ClientId"]!,
        ["client_secret"] = _configuration["Google:ClientSecret"]!,
        ["redirect_uri"] = request.RedirectUri,
        ["grant_type"] = "authorization_code"
    }));

// 2. 解析 ID Token（JWT）
var tokenJson = await tokenResponse.Content.ReadFromJsonAsync<JsonElement>();
var idToken = tokenJson.GetProperty("id_token").GetString()!;
var jwtToken = new JwtSecurityTokenHandler().ReadJwtToken(idToken);

// 3. 取使用者資訊
var sub   = jwtToken.Claims.First(c => c.Type == "sub").Value;
var email = jwtToken.Claims.First(c => c.Type == "email").Value;

// 4. 簽發自己的 JWT
```

### 簽發 JWT 的 function

```csharp
private string GenerateJwt(string id, string avatar, string email, string name)
{
    var key     = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_configuration["Jwt:Key"]!));
    var creds   = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
    var expires = DateTime.UtcNow.AddMinutes(double.Parse(_configuration["Jwt:ExpiresInMinutes"] ?? "60"));

    var claims = new[]
    {
        new Claim(ClaimTypes.NameIdentifier, id),
        new Claim("picture", avatar),
        new Claim(ClaimTypes.Email, email),
        new Claim(ClaimTypes.Name, name),
    };

    var jwt = new JwtSecurityToken(
        issuer: _configuration["Jwt:Issuer"],
        audience: _configuration["Jwt:Audience"],
        claims: claims,
        expires: expires,
        signingCredentials: creds
    );

    return new JwtSecurityTokenHandler().WriteToken(jwt);
}
```

---

## 必要設定

### appsettings.json（或 Secret Manager）
```json
{
  "Google": {
    "ClientId": "xxx.apps.googleusercontent.com",
    "ClientSecret": "GOCSPX-xxx"
  },
  "Jwt": {
    "Key": "your-256-bit-secret",
    "Issuer": "your-api-domain",
    "Audience": "your-frontend-domain",
    "ExpiresInMinutes": "60"
  },
  "Frontend": {
    "CallbackUrl": "https://your-frontend/auth/callback"
  }
}
```

### Google Cloud Console 必做
1. 建立 OAuth 2.0 憑證（Web application）
2. 在「已授權的重新導向 URI」加入所有 redirect_uri（含本機）
3. Client Secret 只給後端，不進版控

### 已授權的 JavaScript 來源 vs 已授權的重新導向 URI

|          | 已授權的 JavaScript 來源                           | 已授權的重新導向 URI                                |
| -------- | -------------------------------------------------- | --------------------------------------------------- |
| 用途     | 前端直接呼叫 Google JS SDK                         | OAuth 流程結束後，Google 把 code 送回的目標 URL     |
| 使用時機 | 用 `google.accounts.id.initialize()` 等 JS library | Authorization Code flow（後端換 token）             |
| 填什麼   | 只填 origin（`http://localhost:8082`）             | 填完整路徑（`http://localhost:8082/signin-google`） |
| 架構     | 前端直接跟 Google 溝通                             | 後端跟 Google 溝通，前端只打後端                    |

**後端主導的架構只需填「已授權的重新導向 URI」**，JavaScript 來源不需要填。

---

## 兩種 JWT 的差異

OAuth 流程中存在兩種不同的 JWT，職責完全不同：

|              | Google ID Token                 | 應用自簽 JWT                       |
| ------------ | ------------------------------- | ---------------------------------- |
| 誰發行       | Google                          | 你的 Backend                       |
| 用途         | 證明「Google 確認這人是誰」     | 證明「你的系統允許這人操作」       |
| 驗證方式     | Google 公鑰驗簽名               | 你自己的 secret 驗簽名             |
| 有效期       | 約 1 小時（Google 決定）        | 自訂                               |
| Payload 內容 | sub、email、name、picture       | 自訂（userId、roles、permissions） |
| 使用時機     | 後端換 token 後解析一次，不流出 | 前端每次 API request 都帶          |

流程關係：

```text
Google ID Token → 後端解析 → 建立 / 查詢本地帳號 → 簽發應用 JWT → 前端持有
```

Google ID Token 是「入場門票（用完即棄）」，應用 JWT 是「會員手環（持續使用）」。

---

## /me 端點

`/me` 是一個需要 JWT 驗證的端點，回傳當前登入者的資訊。

### 用途

- 前端重新整理或重新開啟後，持有 JWT 但不知道 token 內的 user 資訊
- 避免前端自行 decode JWT（安全隱患，且格式可能改變）
- 統一由後端決定「目前登入者是誰」

### Request

```http
GET /api/auth/me
Authorization: Bearer <JWT>
```

### Response

```json
{
  "id": "...",
  "email": "user@example.com",
  "name": "...",
  "picture": "..."
}
```

### ASP.NET Core 實作

```csharp
[Authorize]
[HttpGet("me")]
public IActionResult GetMe()
{
    var id      = User.FindFirstValue(ClaimTypes.NameIdentifier);
    var email   = User.FindFirstValue(ClaimTypes.Email);
    var name    = User.FindFirstValue(ClaimTypes.Name);
    var picture = User.FindFirstValue("picture");

    return Ok(new { id, email, name, picture });
}
```

`[Authorize]` attribute 會讓 ASP.NET Core middleware 自動驗證 Bearer JWT，驗證失敗回 401，無需手動解析。

---

## 取得 Google 完整使用者資料（含 picture）

Server-side flow 預設不帶 `picture` claim，需在 `OnCreatingTicket` 手動加入：

```csharp
options.Events.OnCreatingTicket = context =>
{
    var picture = context.User.GetProperty("picture").GetString();
    if (!string.IsNullOrEmpty(picture))
        context.Identity?.AddClaim(new Claim("picture", picture));
    return Task.CompletedTask;
};
```

`context.User` 是 Google 回傳的完整 JSON（`JsonElement`），包含 `sub`、`email`、`name`、`picture`、`locale` 等欄位。

---

## 常見錯誤排查

### redirect_uri_mismatch

|          |                                                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 錯誤訊息 | `400: redirect_uri_mismatch`                                                                                                    |
| 原因     | 發送給 Google 的 `redirect_uri` 與 Google Cloud Console 登記的清單不完全相符（含 http/https、port、trailing slash 都要一致）    |
| 解法     | 在 Console「已授權的重新導向 URI」加入完全相符的 URI。ASP.NET Core Google middleware 預設使用 `{scheme}://{host}/signin-google` |

注意：後端跑 https 時送出的是 `https://`，要登記 https 版本。

---

### The oauth state was missing or invalid / Correlation failed

|          |                                                                                                                                                  |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 錯誤訊息 | `AuthenticationFailureException: The oauth state was missing or invalid` 或 `Correlation failed`                                                 |
| 原因     | OAuth flow 開始時設定的 correlation cookie 無法被解密。常見於：app 重啟導致 DataProtection 金鑰重新產生、或直接打 callback URL 沒有先走 `/login` |
| 解法     | 1. 把 DataProtection 金鑰存到磁碟避免重啟失效；2. 清掉瀏覽器 cookie 重新走完整流程                                                               |

```csharp
var keysFolder = Path.Combine(builder.Environment.ContentRootPath, "DataProtection-Keys");
builder.Services.AddDataProtection()
    .SetApplicationName("app-name")
    .PersistKeysToFileSystem(new DirectoryInfo(keysFolder));
```

`DataProtection-Keys/` 資料夾含加密金鑰，加入 `.gitignore`。

---

### ArgumentNullException: Value cannot be null (Parameter 'value')

|          |                                                                                                |
| -------- | ---------------------------------------------------------------------------------------------- |
| 錯誤訊息 | `ArgumentNullException: Value cannot be null. (Parameter 'value')` 在 `new Claim(type, value)` |
| 原因     | Claim 的 value 參數不能是 null。`FindFirst()?.Value` 在找不到 claim 時回傳 null                |
| 解法     | 加 null 保護：`FindFirst("picture")?.Value ?? ""`，或用 `OnCreatingTicket` 確保 claim 一定存在 |

---

### client_secret is missing

| | |
| --- | --- |
| 錯誤訊息 | `400: invalid_request - client_secret is missing` |
| 原因 | Google token endpoint 對 **Web application** 類型的 credential 強制要求 `client_secret`，即使帶了 PKCE 也一樣。`client_secret` 不能放在前端 JS，所以從瀏覽器直接打 `https://oauth2.googleapis.com/token` 會失敗 |
| 解法 | 改用 GIS One Tap（不走 token endpoint），或改用 **Desktop app** 類型的 credential（Google 不驗其 secret，PKCE 可直接從瀏覽器換 token） |

---

### The given origin is not allowed for the given client ID

| | |
| --- | --- |
| 錯誤訊息 | `[GSI_LOGGER]: The given origin is not allowed for the given client ID.` |
| 原因 | GIS One Tap / renderButton 要求前端 origin 必須在 Google Cloud Console 的「已授權的 JavaScript 來源」清單內 |
| 解法 | Google Cloud Console → APIs & Services → Credentials → 選對應的 OAuth client → **Authorized JavaScript origins** 加入 `http://localhost:5173`（開發）和正式域名 |

注意：GIS 用「JavaScript 來源」不是「重新導向 URI」，兩者要分開設定。

---

## 注意事項

- Authorization Code 只能使用一次，換完即失效
- `redirect_uri` 必須與發起授權時完全一致（包含 trailing slash）
- ID Token 只需 `ReadJwtToken` 解析，不需驗簽（已是 HTTPS 換回來的）；若要嚴格驗證可用 Google Public Keys
- JWT Key 長度建議 256 bits（32 bytes）以上，可用 `[Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Max 256) }))` 產生
- Production 不要把 Client Secret 放 appsettings.json，改用 K8s Secret 或 Vault 注入
- `appsettings.Development.json` 設定 dev 用的 JWT Key，讓本機開發與 Production 金鑰隔離
