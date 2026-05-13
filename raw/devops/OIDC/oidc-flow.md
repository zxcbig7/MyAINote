---
tags: [devops, oidc, oauth2, google, jwt, aspnetcore, react]
---

> 關聯：[[google-oauth-tutorial]]、[[Authentication-Authorization-Pipeline]]、[[cloudflare-tunnel]]

# OIDC 完整流程（MyDevWeb 實作）

把這份當作「你打開 Google 登入按鈕，到拿到自家 JWT」的逐步追蹤紀錄。所有檔名都對應到 MyDevWeb repo 真實存在的程式碼。

---

## 1. 名詞快速釐清

| 術語                 | 一句話說明                                                       |
| -------------------- | ---------------------------------------------------------------- |
| OAuth 2.0            | 授權框架，回答「你能做什麼」                                     |
| OpenID Connect(OIDC) | 蓋在 OAuth 2.0 上的身份層，回答「你是誰」                        |
| Authorization Code   | Google 給的一次性短效代碼，只能在 server 換 token                |
| ID Token             | JWT 格式，Google 簽的，內含 `sub` / `email` / `name` / `picture` |
| Access Token         | 拿來打 Google API 用（本專案沒用到）                             |
| Client ID            | 公開值，可寫前端                                                 |
| Client Secret        | 機密值，只能在 backend，K8s Secret 注入                          |
| Redirect URI         | Google 完成授權後 callback 的 URL，要與 Console 完全一致         |
| 自簽 JWT             | Backend 自己用 `Jwt:Key` 簽的，前端持有來通過 `[Authorize]`      |

---

## 2. 兩種 JWT 不要搞混

OIDC 流程中存在兩個都叫 JWT 的東西，職責不同：

|              | Google ID Token              | 自簽 JWT（MyDevWebBackend）                |
| ------------ | ---------------------------- | ------------------------------------------ |
| 誰簽         | Google                       | Backend (`Jwt:Key`)                        |
| 驗簽方式     | Google 公鑰                  | Backend 自己的 symmetric key（HmacSha256） |
| 有效期       | ~1 小時                      | `Jwt:ExpiresInMinutes = 43200`（30 天）    |
| Payload      | `sub`, `email`, `name`, `picture` | 同上 + 用 .NET `ClaimTypes` 長 URI       |
| 用途         | Backend 解一次拿身份就丟     | 前端每次 API 都帶在 `Authorization: Bearer`|

對照圖：

```
Google ID Token → backend 解析 → 簽自家 JWT → 前端 localStorage 保存 → API 帶 Bearer
       (入場票，用完即棄)             (會員手環，持續使用)
```

---

## 3. 本專案支援的兩條登入路徑

| 路徑           | 觸發點                              | 是否需要 backend  |
| -------------- | ----------------------------------- | ----------------- |
| Server-side flow | 使用者點「使用 Google 帳號登入」    | ✅ 必須           |
| GIS One Tap    | 進入 `/login` 頁面自動彈窗          | ❌ 純前端可運作   |

兩條路最終都呼叫 `loginWithToken(token)`，把 token 存進 `localStorage` 後 navigate 到 `/homepage`。差別只在 token 的來源與簽名者。

---

## 4. Flow A：Server-side Redirect Flow（主要流程）

### 4.1 序列圖

```
使用者                Frontend(React)         Backend(ASP.NET Core)         Google
  │                       │                       │                          │
  │ 點按鈕                 │                       │                          │
  ├──────────────────────►│                       │                          │
  │                       │ window.location =     │                          │
  │                       │ /api/auth/google/login│                          │
  │                       ├──────────────────────►│                          │
  │                       │                       │ Challenge Google scheme  │
  │                       │                       │ (302 → accounts.google)  │
  │                       │◄──────────────────────┤                          │
  │ 整頁跳到 Google 登入頁                                                     │
  │◄──────────────────────────────────────────────────────────────────────────│
  │                       │                       │                          │
  │ 同意授權              │                       │                          │
  ├──────────────────────────────────────────────────────────────────────────►│
  │                       │                       │                          │
  │ 302 → /signin-google?code=xxx&state=xxx                                   │
  │◄──────────────────────────────────────────────────────────────────────────│
  │                       │                       │                          │
  │ 瀏覽器照著跳            │                       │                          │
  ├──────────────────────────────────────────────►│                          │
  │                       │                       │ Google middleware:       │
  │                       │                       │ 1. 驗 state cookie       │
  │                       │                       │ 2. 用 code 換 tokens     ├─────────►│
  │                       │                       │                          │◄─────────┤
  │                       │                       │ 3. 解 id_token 拿 claims │
  │                       │                       │ 4. 寫 Cookie scheme      │
  │                       │                       │ 5. 302 → /api/auth/google│
  │                       │                       │   /callback              │
  │◄──────────────────────────────────────────────┤                          │
  │ 跟著 302               │                       │                          │
  ├──────────────────────────────────────────────►│                          │
  │                       │                       │ GoogleCallback action:   │
  │                       │                       │ 讀 Cookie → 簽自家 JWT   │
  │                       │                       │ 302 → /auth/callback?    │
  │                       │                       │   token=<自簽 JWT>       │
  │◄──────────────────────────────────────────────┤                          │
  │ 跟著 302               │                       │                          │
  ├──────────────────────►│                       │                          │
  │                       │ AuthCallback.tsx:     │                          │
  │                       │ token 存 localStorage │                          │
  │                       │ navigate /homepage    │                          │
```

### 4.2 程式碼追蹤點

**Step 1 — 前端發起**

[authService.ts:30](MyDevWebFrontend/src/auth/authService.ts#L30)

```typescript
loginServerSide(): void {
  window.location.href = `${BACKEND_BASE}/api/auth/google/login`;
}
```

**Step 2 — Backend Challenge**

[GoogleAuthController.cs:102](MyDevWebBackend/Controllers/GoogleAuthController.cs#L102)

```csharp
[HttpGet("login")]
public IActionResult LoginWithGoogle()
{
    var redirectUrl = "/api/auth/google/callback";
    var properties = new AuthenticationProperties { RedirectUri = redirectUrl };
    return Challenge(properties, GoogleDefaults.AuthenticationScheme);
}
```

`Challenge(GoogleDefaults.AuthenticationScheme)` 觸發 ASP.NET Core Google middleware，內部組出 Google 授權網址、寫入 correlation cookie、回 302。`RedirectUri` 是「Google 流程跑完之後，要把使用者送到哪個 controller action」。

**Step 3 — Middleware 接收 Google callback**

不是你自己寫的 action，是 `.AddGoogle()` 註冊的內建 middleware 在攔截 `CallbackPath = "/signin-google"`：

[Middleware.cs:87](MyDevWebBackend/Middleware.cs#L87)

```csharp
.AddGoogle(options =>
{
    options.ClientId = builder.Configuration["Google:ClientId"]!;
    options.ClientSecret = builder.Configuration["Google:ClientSecret"]!;
    options.CallbackPath = "/signin-google";  // ← Google 把 code 送回這裡
    ...
});
```

Middleware 接收 `code` 後做四件事：
1. 驗 correlation cookie（state）→ 確保是同一 session
2. 拿 `code` + `client_secret` 去 Google `oauth2.googleapis.com/token` 換 `id_token`
3. 解析 `id_token` → 把 claims 寫入 `Cookies` scheme
4. 302 redirect 到 Challenge 時設定的 `RedirectUri`（也就是 `/api/auth/google/callback`）

**Step 4 — 補 picture claim**

預設 Google middleware 不會把 `picture` 放進 ClaimsPrincipal，必須手動加：

[Middleware.cs:105](MyDevWebBackend/Middleware.cs#L105)

```csharp
options.Events.OnCreatingTicket = context =>
{
    var picture = context.User.GetProperty("picture").GetString();
    if (!string.IsNullOrEmpty(picture))
        context.Identity?.AddClaim(new Claim("picture", picture));
    return Task.CompletedTask;
};
```

`context.User` 是 Google `userinfo` 回傳的完整 JSON（`JsonElement`），含 `sub`, `email`, `name`, `picture`, `locale`。

**Step 5 — Backend 簽自家 JWT 跳回前端**

[GoogleAuthController.cs:112](MyDevWebBackend/Controllers/GoogleAuthController.cs#L112)

```csharp
[HttpGet("callback")]
public async Task<IActionResult> GoogleCallback()
{
    var result = await HttpContext.AuthenticateAsync("Cookies");
    if (!result.Succeeded) return Unauthorized();

    var email  = result.Principal!.FindFirst(ClaimTypes.Email)?.Value;
    var name   = result.Principal!.FindFirst(ClaimTypes.Name)?.Value;
    var id     = result.Principal!.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var avatar = result.Principal!.FindFirst("picture")?.Value ?? "";

    var token = GenerateJwt(id!, avatar, email!, name!);
    var frontendUrl = _configuration["Frontend:CallbackUrl"]
        ?? "http://localhost:5173/auth/callback";

    return Redirect($"{frontendUrl}?token={token}");
}
```

`AuthenticateAsync("Cookies")` 從 Cookie scheme 讀回上一步寫入的 Google claims，不會再打 Google。然後用 `Jwt:Key` 簽自家 JWT，把 token 接在 query string 帶回前端。

**Step 6 — 前端 callback 收 token**

[AuthCallback.tsx:12](MyDevWebFrontend/src/pages/auth/AuthCallback.tsx#L12)

```typescript
const token = new URLSearchParams(window.location.search).get("token");
if (!token) { navigate("/login", { replace: true }); return; }

loginWithToken(token)
  .then(() => navigate("/homepage", { replace: true }))
  .catch(() => { AuthService.clearToken(); navigate("/login", { replace: true }); });
```

`loginWithToken` 把 token 存進 `localStorage`，並 decode payload 拿使用者資訊塞進 `AuthContext` state：

[AuthContext.tsx:61](MyDevWebFrontend/src/auth/AuthContext.tsx#L61)

```typescript
async function loginWithToken(token: string): Promise<void> {
  AuthService.storeToken(token);
  setUser(AuthService.decodeToken(token));
}
```

---

## 5. Flow B：GIS One Tap（無 backend 備援）

### 5.1 序列圖

```
使用者進入 /login → GIS SDK 載入
       ↓
google.accounts.id.initialize({ client_id, callback })
       ↓
google.accounts.id.prompt()  ← 在頁面右上角彈窗
       ↓
使用者選帳號（不跳離當前頁）
       ↓
callback({ credential: <Google id_token> })
       ↓
loginWithToken(idToken) ← 直接用 Google 簽的 JWT
       ↓
navigate /homepage
```

### 5.2 程式碼追蹤點

[AuthPage.tsx:26](MyDevWebFrontend/src/pages/auth/AuthPage.tsx#L26)

```typescript
useEffect(() => {
  AuthService.initGIS(async (idToken) => {
    await loginWithToken(idToken);
    navigate("/homepage", { replace: true });
  });
  AuthService.promptOneTap();
}, []);
```

[authService.ts:36](MyDevWebFrontend/src/auth/authService.ts#L36)

```typescript
initGIS(onCredential: (idToken: string) => void): void {
  window.google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: (response) => onCredential(response.credential),
    cancel_on_tap_outside: false,
  });
},
promptOneTap(): void {
  window.google.accounts.id.prompt();
}
```

### 5.3 One Tap 的限制

- iOS Safari 不穩定（ITP 擋第三方 cookie）
- Google Cloud Console 必須加「Authorized JavaScript origins」（不是 redirect URI）
- 前端直接拿到的是 **Google 簽的 id_token**，不是自家 JWT，所以後端 `[Authorize]` 不會通過（Issuer / Audience / SigningKey 都對不上）
- 適合：純前端 demo、登入後不打後端 API 的場景

---

## 6. 前端 Token 解碼（同時支援兩種 JWT）

Google id_token 與 .NET 自簽 JWT 用不同的 claim 名稱，前端要相容兩種：

[authService.ts:56](MyDevWebFrontend/src/auth/authService.ts#L56)

```typescript
decodeToken(token: string): AuthUser {
  const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  const p = JSON.parse(atob(base64));
  if (p.exp * 1000 < Date.now()) throw new Error("Token expired");

  const NET_SUB   = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier";
  const NET_EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress";
  const NET_NAME  = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name";

  return {
    id:     p.sub     ?? p[NET_SUB]   ?? "",
    name:   p.name    ?? p[NET_NAME]  ?? "",
    email:  p.email   ?? p[NET_EMAIL] ?? "",
    avatar: p.picture ?? "",
  };
}
```

| 欄位   | Google id_token | .NET ClaimTypes                                                       |
| ------ | --------------- | --------------------------------------------------------------------- |
| id     | `sub`           | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier` |
| email  | `email`         | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`   |
| name   | `name`          | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`           |
| avatar | `picture`       | `picture`（自訂短名稱）                                                |

> JWT payload 用 base64url（`-`、`_`），`atob()` 要的是標準 base64（`+`、`/`），所以要 replace。

---

## 7. Backend Authentication Pipeline

[Middleware.cs:39](MyDevWebBackend/Middleware.cs#L39)

```csharp
builder.Services.AddAuthentication(options =>
{
    options.DefaultScheme = "Cookies";
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddCookie("Cookies", ...)        // Google OAuth flow 中暫存身份
.AddJwtBearer(...)                // [Authorize] 驗自家 JWT
.AddGoogle(...)                   // 處理 Google OAuth flow
```

三個 scheme 分工：

| Scheme   | 用途                                        | 觸發時機                          |
| -------- | ------------------------------------------- | --------------------------------- |
| Cookies  | OAuth flow 中暫存 Google 回傳的 claims       | `/signin-google` middleware 寫入   |
| JwtBearer| 驗證前端帶來的自家 JWT                       | 任何 `[Authorize]` endpoint        |
| Google   | 與 Google 溝通（換 code、解 id_token）       | `Challenge(GoogleDefaults...)`     |

`DefaultScheme = "Cookies"` ＝ 一般請求預設用 Cookie 辨識身份。
`DefaultChallengeScheme = JwtBearer` ＝ `[Authorize]` 沒過時，要求帶 Bearer JWT。

### JwtBearer 兩種帶 token 方式

預設只看 `Authorization: Bearer <token>` header，這裡額外支援從 Cookie 讀：

[Middleware.cs:61](MyDevWebBackend/Middleware.cs#L61)

```csharp
options.Events = new JwtBearerEvents
{
    OnMessageReceived = context =>
    {
        var token = context.Request.Cookies["access_token"];
        if (!string.IsNullOrEmpty(token)) context.Token = token;
        return Task.CompletedTask;
    }
};
```

---

## 8. Production 特殊處理

### 8.1 Cloudflare Tunnel 的 scheme 問題

Cloudflare Tunnel → minikube → ingress-nginx → backend 這條鏈中，backend 收到的 `Request.Scheme` 是 `http`（內部通訊），但對外是 `https`。如果不處理：

- redirect_uri 會組成 `http://api.viclai.idv.tw/signin-google`
- Google 拒絕：Production OAuth 要求 https

兩道修補：

**(1) UseForwardedHeaders 讀 `X-Forwarded-Proto`**

[Middleware.cs:138](MyDevWebBackend/Middleware.cs#L138)

```csharp
builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders =
        ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;
    options.KnownNetworks.Clear();
    options.KnownProxies.Clear();
});
```

`KnownNetworks/Proxies` 清空 ＝ 信任所有來源轉發的 header（適合封閉的 k8s 環境）。

**(2) Production 強制 scheme = https**

[Middleware.cs:246](MyDevWebBackend/Middleware.cs#L246)

```csharp
if (!app.Environment.IsDevelopment())
{
    app.Use((context, next) =>
    {
        context.Request.Scheme = "https";
        return next();
    });
}
```

**(3) 萬一還是組出 http，最後一道防線**

[Middleware.cs:116](MyDevWebBackend/Middleware.cs#L116)

```csharp
options.Events.OnRedirectToAuthorizationEndpoint = context =>
{
    var redirectUri = context.RedirectUri.Replace(
        "http://api.viclai.idv.tw",
        "https://api.viclai.idv.tw");
    context.Response.Redirect(redirectUri);
    return Task.CompletedTask;
};
```

### 8.2 Cookie SameSite/Secure 環境分流

Production 跨域（前端 `viclai.idv.tw` ↔ 後端 `api.viclai.idv.tw`）要 `SameSite=None; Secure`，否則 correlation cookie 帶不過去。

[Middleware.cs:48](MyDevWebBackend/Middleware.cs#L48)

```csharp
options.Cookie.SameSite = builder.Environment.IsDevelopment()
    ? SameSiteMode.Lax : SameSiteMode.None;
options.Cookie.SecurePolicy = builder.Environment.IsDevelopment()
    ? CookieSecurePolicy.None : CookieSecurePolicy.Always;
```

CorrelationCookie 同處理：[Middleware.cs:96](MyDevWebBackend/Middleware.cs#L96)

### 8.3 DataProtection 金鑰持久化

ASP.NET Core 用 DataProtection 加密 correlation cookie。預設金鑰存記憶體，Pod 重啟就遺失，造成 `Correlation failed` 錯誤。要存到磁碟：

[Middleware.cs:131](MyDevWebBackend/Middleware.cs#L131)

```csharp
var keysFolder = Path.Combine(builder.Environment.ContentRootPath, "DataProtection-Keys");
builder.Services.AddDataProtection()
    .SetApplicationName("my-devweb-be")
    .PersistKeysToFileSystem(new DirectoryInfo(keysFolder));
```

> k8s 部署時這個資料夾應該掛 PVC，否則 Pod 重建還是會丟失。

---

## 9. Secrets 管理

[appsettings.json](MyDevWebBackend/appsettings.json) 結構：

```json
{
  "Jwt": {
    "Issuer": "MyDevWebBackend",
    "Audience": "MyDevWebFrontend",
    "Key": "",                  // ← 空字串，從 K8s Secret 注入
    "ExpiresInMinutes": 43200
  },
  "Google": {
    "ClientId": "1008974...apps.googleusercontent.com",  // 公開可寫
    "ClientSecret": ""          // ← 空字串，從 K8s Secret 注入
  }
}
```

ASP.NET Core 環境變數對應規則：雙底線 `__` 表示巢狀。K8s Secret key 用：

| 設定路徑              | 環境變數名稱          |
| --------------------- | --------------------- |
| `Jwt:Key`             | `Jwt__Key`            |
| `Google:ClientId`     | `Google__ClientId`    |
| `Google:ClientSecret` | `Google__ClientSecret`|

產生 256-bit JWT Key（PowerShell）：

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Max 256) }))
```

---

## 10. Google Cloud Console 設定

### Authorized JavaScript origins（給 GIS One Tap）

```
http://localhost:5173
https://viclai.idv.tw
```

### Authorized redirect URIs（給 Server-side flow）

```
http://localhost:8082/signin-google
https://api.viclai.idv.tw/signin-google
```

> 注意 path 是 Google middleware 預設的 `/signin-google`，不是 `/api/auth/google/callback`。後者是 backend 內部 redirect 的目標，Google 看不到。

---

## 11. 常見錯誤排查

### redirect_uri_mismatch

| | |
|---|---|
| 訊息 | `400: redirect_uri_mismatch` |
| 原因 | Backend 送出的 `redirect_uri` 與 Console 登記的不完全一致（scheme/port/path/trailing slash 任一不同都會擋） |
| 解法 | 確認 Console 有 `https://api.viclai.idv.tw/signin-google`；Production 確認 Cloudflare 進來後 scheme 被改成 https |

### Correlation failed

| | |
|---|---|
| 訊息 | `AuthenticationFailureException: The oauth state was missing or invalid` |
| 原因 | DataProtection 金鑰找不到，無法解 correlation cookie。常見於 Pod 重啟金鑰丟失 |
| 解法 | `PersistKeysToFileSystem` + 掛 PVC，或清瀏覽器 cookie 重走流程 |

### ArgumentNullException at `new Claim`

| | |
|---|---|
| 訊息 | `Value cannot be null. (Parameter 'value')` 在 GoogleCallback |
| 原因 | `FindFirst("picture")?.Value` 在 Google 沒回 picture 時是 null，`new Claim` 不吃 null |
| 解法 | `FindFirst("picture")?.Value ?? ""`（[GoogleAuthController.cs:126](MyDevWebBackend/Controllers/GoogleAuthController.cs#L126) 已加） |

### client_secret is missing

| | |
|---|---|
| 訊息 | `400: invalid_request - client_secret is missing` |
| 原因 | Google token endpoint 對 Web application 類型強制要 `client_secret`，前端不能持有 |
| 解法 | 改走 backend Server-side flow，或前端改用 GIS One Tap |

### The given origin is not allowed

| | |
|---|---|
| 訊息 | `[GSI_LOGGER]: The given origin is not allowed for the given client ID` |
| 原因 | GIS One Tap 要求前端 origin 在 Console「Authorized JavaScript origins」清單內 |
| 解法 | Console 加入 `http://localhost:5173`、`https://viclai.idv.tw` |

---

## 12. 流程速查總圖

```
┌─────────────────────────────────────────────────────────────────┐
│  Flow A: Server-side（按按鈕）                                    │
│                                                                  │
│  /login 按按鈕                                                    │
│     │                                                            │
│     ▼ window.location                                            │
│  GET /api/auth/google/login                                      │
│     │                                                            │
│     ▼ Challenge(Google)                                          │
│  302 → accounts.google.com/o/oauth2/v2/auth?...                  │
│     │                                                            │
│     ▼ 使用者同意                                                  │
│  302 → /signin-google?code=...                                   │
│     │                                                            │
│     ▼ Google middleware：換 token、解 id_token、寫 Cookie scheme  │
│  302 → /api/auth/google/callback                                 │
│     │                                                            │
│     ▼ GoogleCallback action：讀 Cookie、簽自家 JWT                │
│  302 → /auth/callback?token=<JWT>                                │
│     │                                                            │
│     ▼ AuthCallback.tsx：存 localStorage                           │
│  navigate /homepage                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Flow B: GIS One Tap（自動彈窗）                                  │
│                                                                  │
│  /login useEffect                                                │
│     │                                                            │
│     ▼ initGIS + promptOneTap                                     │
│  Google 在頁面彈出選帳號框                                         │
│     │                                                            │
│     ▼ 使用者選帳號（不跳離頁面）                                    │
│  callback({ credential: id_token })                              │
│     │                                                            │
│     ▼ loginWithToken(idToken)                                    │
│  navigate /homepage                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. 設計權衡備忘

| 決定                           | 為什麼這樣做                                              |
| ------------------------------ | --------------------------------------------------------- |
| 主流程選 Server-side 而非 SPA  | iOS Safari 穩定、`client_secret` 不外露                   |
| 同時保留 GIS One Tap          | 後端掛掉時前端還能 demo；省一次 redirect 體驗較好         |
| 自簽 JWT 而非直接用 Google JWT | 控制過期時間、塞自己的 claims（未來加 roles 較容易）       |
| `Jwt:ExpiresInMinutes = 43200` | 30 天，個人專案不想每天重登；正式產品應更短 + refresh token |
| Token 存 `localStorage` 而非 httpOnly cookie | SPA 跨域場景簡單；風險是 XSS 取走，靠 CSP 防 |
