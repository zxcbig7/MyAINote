---
tags: [devops, keycloak, template, keycloak-js, sdk]
---

# Template C — keycloak-js + @react-keycloak/web（官方 SDK）

用 Keycloak 官方 JS library，refresh / logout / silent SSO 都包好。

## 適用情境
- 想要最少自寫 auth 邏輯
- 願意綁定 keycloak-js（換 IdP 要重寫）
- 需要 Keycloak 進階功能（silent check SSO、impersonation 等）

## npm

```powershell
npm i keycloak-js @react-keycloak/web
```

## .env

```bash
VITE_KEYCLOAK_URL=https://sso.company.com
VITE_KEYCLOAK_REALM=company
VITE_KEYCLOAK_CLIENT_ID=mydevweb-frontend
VITE_API_BASE=https://api.viclai.idv.tw
```

---

## 1. 建立 Keycloak instance

`src/auth/keycloak.ts`

```typescript
import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url:      import.meta.env.VITE_KEYCLOAK_URL,
  realm:    import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
});

export default keycloak;
```

> Keycloak instance 必須是「全域只 new 一次」，否則 SDK 內部 state 會亂掉。

## 2. Provider 包 App

`src/main.tsx`

```tsx
import { ReactKeycloakProvider } from "@react-keycloak/web";
import keycloak from "./auth/keycloak";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <ReactKeycloakProvider
    authClient={keycloak}
    initOptions={{
      onLoad: "check-sso",                       // 不強制登入，只檢查 SSO session
      silentCheckSsoRedirectUri:
        `${window.location.origin}/silent-check-sso.html`,
      pkceMethod: "S256",
      checkLoginIframe: false,                   // 避免 ITP 問題
    }}
  >
    <App />
  </ReactKeycloakProvider>
);
```

## 3. 建立 silent-check-sso.html

在 `public/silent-check-sso.html`：

```html
<!doctype html>
<html><body>
  <script>parent.postMessage(location.href, location.origin)</script>
</body></html>
```

silent SSO 用一個隱藏 iframe 偷偷檢查 Keycloak session，這個檔案是必要的。

## 4. 登入頁

`src/pages/auth/AuthPage.tsx`

```tsx
import { useKeycloak } from "@react-keycloak/web";
import { Navigate } from "react-router-dom";

export default function AuthPage() {
  const { keycloak, initialized } = useKeycloak();

  if (!initialized) return <div>載入中…</div>;
  if (keycloak.authenticated) return <Navigate to="/homepage" replace />;

  return (
    <button onClick={() => keycloak.login({ redirectUri: window.location.origin + "/homepage" })}>
      使用 SSO 登入
    </button>
  );
}
```

## 5. 取得使用者資訊

```tsx
import { useKeycloak } from "@react-keycloak/web";

function UserBadge() {
  const { keycloak } = useKeycloak();
  if (!keycloak.authenticated) return null;

  const profile = keycloak.tokenParsed as {
    sub: string; email: string; name: string; preferred_username: string;
  };
  return <div>{profile.name} ({profile.email})</div>;
}
```

`keycloak.tokenParsed` 是已 decode 的 access token payload。

## 6. 打 API 帶 token + 自動 refresh

`src/api/axios.ts`

```typescript
import axios from "axios";
import keycloak from "../auth/keycloak";

export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE });

api.interceptors.request.use(async config => {
  // 過期前 30 秒會自動 refresh
  await keycloak.updateToken(30);
  config.headers.Authorization = `Bearer ${keycloak.token}`;
  return config;
});
```

`updateToken(minValidity)`：token 還有 `minValidity` 秒內到期時自動 refresh。

## 7. 路由保護

```tsx
import { useKeycloak } from "@react-keycloak/web";
import { Navigate, Outlet } from "react-router-dom";

export function ProtectedRoute() {
  const { keycloak, initialized } = useKeycloak();
  if (!initialized) return <div>載入中…</div>;
  if (!keycloak.authenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}
```

## 8. 登出

```tsx
<button onClick={() => keycloak.logout({ redirectUri: window.location.origin + "/login" })}>
  登出
</button>
```

會跳到 Keycloak end_session、清掉 SSO session、跳回前端。

---

## 9. Backend — 同 Template A

Backend 設定跟 [Template A](02-template-pkce.md#7-backend--只驗-jwt) 完全一樣：只用 `AddJwtBearer` + Keycloak Authority + JWKS 驗章，不需 controller。

---

## 10. Migration 步驟

1. 安裝 `keycloak-js` 與 `@react-keycloak/web`
2. 建 `keycloak.ts` instance
3. 加 `public/silent-check-sso.html`
4. `main.tsx` 包 `<ReactKeycloakProvider>`，移除原本的 `<AuthProvider>`（from AuthContext）
5. 改 `AuthPage` 用 `useKeycloak()`
6. 改 axios interceptor 用 `keycloak.updateToken` + `keycloak.token`
7. 刪除 `src/auth/AuthContext.tsx`、`src/auth/authService.ts`、`src/pages/auth/AuthCallback.tsx`
8. Backend：同 Template A 拔光 Cookie / Google middleware，只留 `AddJwtBearer`

---

## 11. 跟 Template A 的差別

|                          | A: react-oidc-context           | C: keycloak-js                   |
| ------------------------ | ------------------------------- | -------------------------------- |
| Library 通用性           | 所有 OIDC IdP                   | 只給 Keycloak                    |
| Refresh 機制             | 自動 silent renew               | 手動 `updateToken()` / 自動 timer |
| Silent SSO check         | 沒有                            | ✅ 有                            |
| Logout 清 SSO session    | 用 `signoutRedirect()`          | 用 `keycloak.logout()`           |
| Token 存哪               | localStorage / sessionStorage   | 記憶體（refresh token 視設定）   |
| Bundle size              | 較小（~30KB）                    | 較大（~80KB）                    |
| 換 IdP（未來 Auth0 等）  | 改 config 就好                   | 整套換掉                          |

---

## 優缺點

✅ Keycloak 官方支援，bug 修最快
✅ Silent check SSO（不用 redirect 就知道有沒有登入）
✅ Auto refresh 內建
✅ Logout 清 SSO session 一行解決

❌ 綁 Keycloak SDK，換 IdP 重寫
❌ Bundle 較大
❌ `keycloak.tokenParsed` 是 any，要自己宣告型別
❌ React Strict Mode 雙重 init 偶爾有問題（要 `useRef` 鎖）
