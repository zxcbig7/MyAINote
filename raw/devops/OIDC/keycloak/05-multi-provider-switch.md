---
tags: [devops, keycloak, multi-provider, feature-flag]
---

# Env 切換多 IdP 架構（Google ↔ Keycloak）

同一份 code 用環境變數決定走 Google 或 Keycloak，平順過渡或 dev/prod 分流。

## 適用情境
- 從 Google 過渡到 Keycloak 要平順切換、可隨時 rollback
- 個人 demo 走 Google，公司環境走 Keycloak
- A/B 測試或 staged rollout

---

## 1. 設計原則

| 層              | 切換方式                                                     |
| --------------- | ------------------------------------------------------------ |
| Frontend        | `VITE_AUTH_PROVIDER=google\|keycloak`，service 用工廠模式產生對應 impl |
| Backend         | 兩個 named scheme 都註冊；`[Authorize]` 同時接受兩種          |
| K8s             | 同一個 image，靠 ConfigMap / Secret 餵不同 env                |

---

## 2. Frontend — Provider Interface 抽象

`src/auth/types.ts`

```typescript
export type AuthUser = {
  id: string;
  name: string;
  email: string;
  avatar: string;
};

export interface AuthProviderImpl {
  init(): Promise<void>;
  login(): void;
  logout(): void;
  getUser(): AuthUser | null;
  getAccessToken(): string | null;
  onChange(cb: (user: AuthUser | null) => void): () => void;
}
```

### Google impl（包現有 code）

`src/auth/providers/googleProvider.ts`

```typescript
import { AuthService } from "../authService";
import type { AuthProviderImpl, AuthUser } from "../types";

export function createGoogleProvider(): AuthProviderImpl {
  const listeners = new Set<(u: AuthUser | null) => void>();
  let user: AuthUser | null = null;

  return {
    async init() {
      const token = AuthService.getStoredToken();
      if (token) {
        try { user = AuthService.decodeToken(token); }
        catch { AuthService.clearToken(); }
      }
    },
    login()  { AuthService.loginServerSide(); },
    logout() { AuthService.clearToken(); user = null; listeners.forEach(cb => cb(null)); },
    getUser() { return user; },
    getAccessToken() { return AuthService.getStoredToken(); },
    onChange(cb) { listeners.add(cb); return () => listeners.delete(cb); },
  };
}
```

### Keycloak impl（用 react-oidc-context 底層 `oidc-client-ts`）

`src/auth/providers/keycloakProvider.ts`

```typescript
import { UserManager } from "oidc-client-ts";
import type { AuthProviderImpl, AuthUser } from "../types";

export function createKeycloakProvider(): AuthProviderImpl {
  const url      = import.meta.env.VITE_KEYCLOAK_URL;
  const realm    = import.meta.env.VITE_KEYCLOAK_REALM;
  const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID;

  const um = new UserManager({
    authority:    `${url}/realms/${realm}`,
    client_id:    clientId,
    redirect_uri: `${window.location.origin}/auth/callback`,
    response_type: "code",
    scope: "openid profile email",
    automaticSilentRenew: true,
  });

  const listeners = new Set<(u: AuthUser | null) => void>();
  let cached: AuthUser | null = null;

  function toUser(profile: any): AuthUser {
    return {
      id:     profile.sub,
      name:   profile.name ?? profile.preferred_username,
      email:  profile.email,
      avatar: profile.picture ?? "",
    };
  }

  return {
    async init() {
      // 處理 callback redirect
      if (window.location.search.includes("code=")) {
        const u = await um.signinRedirectCallback();
        cached = toUser(u.profile);
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        const u = await um.getUser();
        cached = u && !u.expired ? toUser(u.profile) : null;
      }
    },
    login()  { um.signinRedirect(); },
    logout() { cached = null; um.signoutRedirect(); listeners.forEach(cb => cb(null)); },
    getUser() { return cached; },
    getAccessToken() {
      const key = `oidc.user:${url}/realms/${realm}:${clientId}`;
      const raw = sessionStorage.getItem(key) ?? localStorage.getItem(key);
      return raw ? JSON.parse(raw).access_token : null;
    },
    onChange(cb) { listeners.add(cb); return () => listeners.delete(cb); },
  };
}
```

### 工廠

`src/auth/providers/index.ts`

```typescript
import type { AuthProviderImpl } from "../types";
import { createGoogleProvider }   from "./googleProvider";
import { createKeycloakProvider } from "./keycloakProvider";

export function createAuthProvider(): AuthProviderImpl {
  const which = import.meta.env.VITE_AUTH_PROVIDER ?? "google";
  switch (which) {
    case "keycloak": return createKeycloakProvider();
    case "google":   return createGoogleProvider();
    default: throw new Error(`未知的 VITE_AUTH_PROVIDER: ${which}`);
  }
}
```

### AuthContext 改吃工廠

`src/auth/AuthContext.tsx`

```tsx
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AuthUser } from "./types";
import { createAuthProvider } from "./providers";

const AuthContext = createContext<{
  user: AuthUser | null;
  loading: boolean;
  login: () => void;
  logout: () => void;
} | null>(null);

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth 必須在 AuthProvider 內使用");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const provider = useMemo(() => createAuthProvider(), []);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    provider.init().then(() => {
      setUser(provider.getUser());
      setLoading(false);
    });
    return provider.onChange(setUser);
  }, [provider]);

  return (
    <AuthContext.Provider value={{
      user, loading,
      login:  () => provider.login(),
      logout: () => provider.logout(),
    }}>
      {children}
    </AuthContext.Provider>
  );
}
```

頁面層（`AuthPage`、`Header` 等）完全不變，繼續用 `useAuth()`。

---

## 3. Backend — 同時驗兩種 JWT

註冊兩個 named scheme，policy 接受任一通過。

`Middleware.cs`

```csharp
builder.Services.AddAuthentication("MultiAuth")
    .AddJwtBearer("Backend", options =>  // 自簽 JWT（Google flow 用）
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidIssuer   = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!)),
            ValidateIssuer = true, ValidateAudience = true,
            ValidateLifetime = true, ValidateIssuerSigningKey = true,
        };
    })
    .AddJwtBearer("Keycloak", options =>
    {
        options.Authority = builder.Configuration["Keycloak:Authority"];
        options.Audience  = builder.Configuration["Keycloak:Audience"];
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true, ValidateAudience = true,
            ValidateLifetime = true, ValidateIssuerSigningKey = true,
        };
    })
    .AddPolicyScheme("MultiAuth", "MultiAuth", options =>
    {
        // 看 token issuer 決定走哪個 scheme
        options.ForwardDefaultSelector = context =>
        {
            var auth = context.Request.Headers.Authorization.ToString();
            if (!auth.StartsWith("Bearer ")) return "Backend";

            var token = auth["Bearer ".Length..];
            try
            {
                var jwt = new JwtSecurityTokenHandler().ReadJwtToken(token);
                return jwt.Issuer == builder.Configuration["Keycloak:Authority"]
                    ? "Keycloak" : "Backend";
            }
            catch { return "Backend"; }
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.DefaultPolicy = new AuthorizationPolicyBuilder()
        .AddAuthenticationSchemes("MultiAuth")
        .RequireAuthenticatedUser()
        .Build();
});
```

`AddPolicyScheme` 是 ASP.NET Core 提供的「動態挑 scheme」機制：看 token 的 `iss` claim 決定要交給 `Backend` 還是 `Keycloak` 驗章。

---

## 4. Backend — Controller 雙路徑共存

直接保留現有 `GoogleAuthController`，新增 `KeycloakAuthController`（如 Template B），前端按 `VITE_AUTH_PROVIDER` 打不同 URL。

或者，前端只暴露一個 `/api/auth/login`，由 backend 依環境 redirect：

```csharp
[HttpGet("/api/auth/login")]
public IActionResult Login()
{
    var provider = _configuration["Auth:Provider"] ?? "Google";
    return provider switch
    {
        "Keycloak" => RedirectToAction("Login", "KeycloakAuth"),
        "Google"   => RedirectToAction("LoginWithGoogle", "GoogleAuth"),
        _ => BadRequest("Unknown auth provider"),
    };
}
```

---

## 5. K8s 部署層

同一個 image，靠 ConfigMap 餵 env：

`values-prod.yaml`

```yaml
backend:
  env:
    Auth__Provider: "Keycloak"
    Keycloak__Authority: "https://sso.company.com/realms/company"
    Keycloak__Audience: "mydevweb-frontend"
  secrets:
    Keycloak__ClientSecret: from-keycloak-secret
    Jwt__Key: from-jwt-secret   # 過渡期還留著

frontend:
  env:
    VITE_AUTH_PROVIDER: "keycloak"
    VITE_KEYCLOAK_URL: "https://sso.company.com"
    VITE_KEYCLOAK_REALM: "company"
    VITE_KEYCLOAK_CLIENT_ID: "mydevweb-frontend"
```

> ⚠️ Vite 的 env 是 **build-time** 寫死進 bundle，K8s 切換要重 build image。若要 runtime 切換，把 config 改成從 `/api/config` endpoint 拿，前端 boot 時讀。

---

## 6. 移除過渡用 code 的時機

切到 Keycloak 穩定運作 ~1 個月後可移除：

- `src/auth/authService.ts`（Google flow 用）
- `src/auth/providers/googleProvider.ts`
- `Controllers/GoogleAuthController.cs`
- `.AddGoogle(...)`、`.AddCookie(...)`、`AddJwtBearer("Backend", ...)`
- 改回單一 `AddJwtBearer` 只驗 Keycloak

留一個 PR 標籤 `cleanup/remove-google-auth`，等切換驗證期過了一次刪光。

---

## 7. 風險與注意事項

| 問題                                | 對策                                              |
| ----------------------------------- | ------------------------------------------------- |
| 既有 user 怎麼對應到 Keycloak     | 用 email 對 Keycloak `preferred_username` 或 `sub` |
| 過渡期同時兩種 token 在前端 storage | 切換時 `localStorage.clear()` 強制重登             |
| Vite env build-time 限制            | 改用 runtime config endpoint                      |
| Backend 兩個 JWT 驗證來源    | `AddPolicyScheme` 動態挑，避免 [Authorize] 重複指定 |
| Logout 不同行為                     | Google: 清 localStorage；Keycloak: 跳 end_session |
