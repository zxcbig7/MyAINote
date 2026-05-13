---
tags: [devops, keycloak, template, pkce, react-oidc-context]
---

# Template A — Public Client + PKCE（SPA 現代化標準）

前端跟 Keycloak 直接對接，backend 只驗 JWT。

## 適用情境
- 想拔掉 backend 的 OAuth 邏輯，讓 backend 變單純
- 純 SPA，沒有 server-side session
- 走業界 SPA 標準（OAuth 2.1 推薦）

## npm

```powershell
npm i react-oidc-context oidc-client-ts
```

## .env

```bash
VITE_KEYCLOAK_URL=https://sso.company.com
VITE_KEYCLOAK_REALM=company
VITE_KEYCLOAK_CLIENT_ID=mydevweb-frontend
VITE_API_BASE=https://api.viclai.idv.tw
```

---

## 1. 前端：OIDC Provider 設定

`src/auth/oidcConfig.ts`

```typescript
import { WebStorageStateStore } from "oidc-client-ts";
import type { AuthProviderProps } from "react-oidc-context";

const url      = import.meta.env.VITE_KEYCLOAK_URL;
const realm    = import.meta.env.VITE_KEYCLOAK_REALM;
const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID;

export const oidcConfig: AuthProviderProps = {
  authority:    `${url}/realms/${realm}`,
  client_id:    clientId,
  redirect_uri: `${window.location.origin}/auth/callback`,
  post_logout_redirect_uri: `${window.location.origin}/login`,
  response_type: "code",
  scope: "openid profile email",
  // PKCE 自動啟用，不需手動設
  userStore: new WebStorageStateStore({ store: window.localStorage }),
  // 用 silent renew 換新 token，不打擾使用者
  automaticSilentRenew: true,
  // 把 callback URL 的 ?code= 清掉，避免 history 留下
  onSigninCallback: () => {
    window.history.replaceState({}, document.title, window.location.pathname);
  },
};
```

## 2. 包到 App root

`src/main.tsx`

```tsx
import { AuthProvider } from "react-oidc-context";
import { oidcConfig } from "./auth/oidcConfig";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <AuthProvider {...oidcConfig}>
    <App />
  </AuthProvider>
);
```

> 注意：與你現有的 `AuthContext` (`src/auth/AuthContext.tsx`) 衝突，要二擇一。

## 3. 登入頁

`src/pages/auth/AuthPage.tsx`

```tsx
import { useAuth } from "react-oidc-context";
import { Navigate } from "react-router-dom";

export default function AuthPage() {
  const auth = useAuth();

  if (auth.isLoading)        return <div>載入中…</div>;
  if (auth.error)            return <div>登入錯誤：{auth.error.message}</div>;
  if (auth.isAuthenticated)  return <Navigate to="/homepage" replace />;

  return (
    <button onClick={() => auth.signinRedirect()}>
      使用 SSO 登入
    </button>
  );
}
```

## 4. Callback 頁（多數情況不用自己寫）

`react-oidc-context` 會自動處理 `redirect_uri` 進來的 `?code=&state=`，只要 `App` 在 `AuthProvider` 內，重新整理 `/auth/callback` 就會走完流程。

要客製：

```tsx
import { useAuth } from "react-oidc-context";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function AuthCallback() {
  const auth = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (auth.isAuthenticated) navigate("/homepage", { replace: true });
  }, [auth.isAuthenticated, navigate]);
  return <div>驗證中…</div>;
}
```

## 5. 打 API 帶 Access Token

`src/api/axios.ts`

```typescript
import axios from "axios";
import { User } from "oidc-client-ts";

function getUser(): User | null {
  const key = `oidc.user:${import.meta.env.VITE_KEYCLOAK_URL}/realms/${import.meta.env.VITE_KEYCLOAK_REALM}:${import.meta.env.VITE_KEYCLOAK_CLIENT_ID}`;
  const raw = localStorage.getItem(key);
  return raw ? User.fromStorageString(raw) : null;
}

export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE });
api.interceptors.request.use(config => {
  const user = getUser();
  if (user?.access_token) {
    config.headers.Authorization = `Bearer ${user.access_token}`;
  }
  return config;
});
```

## 6. 登出

```tsx
<button onClick={() => auth.signoutRedirect()}>登出</button>
```

會跳到 Keycloak 的 end_session endpoint，登出整個 SSO session。

---

## 7. Backend — 只驗 JWT

### 安裝

```powershell
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
```

### `appsettings.json`

```json
{
  "Keycloak": {
    "Authority": "https://sso.company.com/realms/company",
    "Audience": "mydevweb-frontend",
    "RequireHttpsMetadata": true
  }
}
```

### `Middleware.cs` — 替換掉現有 Google/Cookie 設定

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Keycloak:Authority"];
        options.Audience  = builder.Configuration["Keycloak:Audience"];
        options.RequireHttpsMetadata =
            builder.Configuration.GetValue<bool>("Keycloak:RequireHttpsMetadata");

        // Keycloak 的 audience 預設不是 client_id，需放寬或加 client scope mapper
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Keycloak:Authority"],
            ValidAudience = builder.Configuration["Keycloak:Audience"],
            NameClaimType = "preferred_username",
            RoleClaimType = "realm_access.roles",
        };
    });
```

`Authority` 設好後，ASP.NET Core 會自動去打 `…/.well-known/openid-configuration` 拿 JWKS，免手動設公鑰。

### 拔掉的東西

以下都可以從 [Middleware.cs](MyDevWebBackend/Middleware.cs) 移除：
- `AddCookie("Cookies", …)`
- `AddGoogle(…)`
- `OnRedirectToAuthorizationEndpoint` 的 https 修補
- `DataProtection` 金鑰持久化（沒有 cookie 加密了）
- `OnMessageReceived` 從 cookie 讀 token（前端統一帶 Bearer）

[GoogleAuthController.cs](MyDevWebBackend/Controllers/GoogleAuthController.cs) 整個刪除，不再需要。

### 讀使用者資訊

```csharp
[HttpGet("me")]
[Authorize]
public IActionResult Me()
{
    var id     = User.FindFirst("sub")?.Value;
    var email  = User.FindFirst("email")?.Value;
    var name   = User.FindFirst("name")?.Value;
    var roles  = User.FindAll("realm_access.roles").Select(c => c.Value);
    return Ok(new { id, email, name, roles });
}
```

---

## 8. Audience 常見地雷

Keycloak access token 預設的 `aud` 不是 client_id，會驗證失敗。三種解法：

| 解法                                | 操作位置                                                       |
| ----------------------------------- | -------------------------------------------------------------- |
| Backend 容忍 audience               | `ValidateAudience = false`（不建議 production）                |
| Keycloak 加 audience mapper        | Client → Client Scopes → Mappers → Audience → include in access token |
| 後端驗 `azp` (authorized party)     | `ValidAudiences = new[] { clientId }` + 額外檢 `azp`           |

正規作法是 IT 在 Keycloak 設 audience mapper，把 `mydevweb-frontend` 加進 access token 的 `aud`。

---

## 9. Migration 步驟

1. 安裝 npm package
2. 寫 `oidcConfig.ts` + 包 `AuthProvider`
3. 改 `AuthPage` 改用 `useAuth()` 取代現有 `useAuth` from `AuthContext`
4. 寫 axios interceptor 帶 token
5. Backend 換 `AddJwtBearer` 設定
6. 刪除 `GoogleAuthController` 與 Cookie / Google middleware
7. K8s deployment：移除 `Google__*`、加 `Keycloak__*`
8. 前端 build 後上 stg 驗證

---

## 優缺點

✅ Backend 變超單純，沒有 OAuth flow 程式碼
✅ 業界 SPA 標準（OAuth 2.1）
✅ 沒有 cookie / session 管理問題
✅ 沒有 Cloudflare Tunnel 的 scheme 問題（不用 redirect）

❌ Access token 存在前端（XSS 風險，靠 CSP 防）
❌ 前端要重寫 `AuthService`、`AuthContext`
❌ Refresh token 也存前端
