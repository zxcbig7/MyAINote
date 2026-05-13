---
tags: [devops, oidc, keycloak, sso, template-index]
---

> 關聯：[[oidc-flow]]、[[01-prerequisites]]、[[05-multi-provider-switch]]

# Keycloak 整合 — Template 總覽

三套 template 可選，依「誰負責跟 Keycloak 對接」分類。

---

## 1. 三種 Template 對照

|                          | A: Public Client + PKCE     | B: Confidential Client (BFF) | C: keycloak-js SDK            |
| ------------------------ | --------------------------- | ---------------------------- | ----------------------------- |
| **誰跟 Keycloak 對接**   | 前端                        | 後端                         | 前端（用官方 SDK）            |
| **Backend 角色**         | 只驗 JWT                    | 換 code、簽 JWT、驗 JWT     | 只驗 JWT                      |
| **需要 client_secret**   | ❌                          | ✅（後端持有）              | ❌                            |
| **Token 流向**           | Keycloak → 前端 → backend  | Keycloak → backend → 前端  | Keycloak → 前端 → backend    |
| **誰簽 JWT**             | Keycloak                    | Keycloak 或 backend 自簽    | Keycloak                      |
| **Refresh token 處理**   | 前端 library 自動處理        | 後端處理                     | SDK 自動處理                  |
| **登出**                 | 跳 Keycloak end_session     | 後端清 cookie + redirect    | SDK 提供 `keycloak.logout()` |
| **跟 Google flow 相似度**| 完全不同（前端主導）         | ⭐ 幾乎一樣（搬 controller）| 完全不同                      |
| **改動量**               | 中（拔 controller、改前端） | 小（換掉 GoogleAuthController）| 中（換成 SDK）              |
| **iOS Safari 友善**      | ✅（PKCE 標準）             | ✅                          | ✅                            |
| **適合場景**             | 純 SPA 現代化做法            | 沿用現有架構、需 backend session| 想用官方 SDK 最少自寫       |

---

## 2. 怎麼選

**現在的 Google flow 已穩定運作 → Template B**
搬 `GoogleAuthController` 成 `KeycloakAuthController`，前端幾乎不動。最快上線。

**想跟著業界 SPA 標準走 → Template A**
backend 變單純（只驗 JWT），但前端要重寫 `AuthService`。長期最乾淨。

**想偷懶用官方 SDK → Template C**
auto refresh、silent SSO、logout 都包好。代價：綁定 keycloak-js。

---

## 3. 三種 Flow 架構圖

### Template A: Public Client + PKCE

```
React ──Authorization Code + PKCE──► Keycloak
  │                                     │
  │◄──────────── id_token + access_token ─┘
  │
  └─Bearer access_token──► ASP.NET Core ──verify via JWKS──► Keycloak
```

### Template B: Confidential Client (BFF)

```
React ──/api/auth/keycloak/login──► ASP.NET Core
                                       │
                                       ▼ Challenge OIDC
React ◄──302──── Keycloak login page ◄──┘
   │
   ▼ user login
Keycloak ──code──► ASP.NET Core ──code + secret──► Keycloak
                       │                              │
                       │◄──── id_token + tokens ─────┘
                       │
                       ▼ 簽自家 JWT
React ◄──302 ?token=── ASP.NET Core
```

### Template C: keycloak-js SDK

```
React (keycloak-js) ──redirect──► Keycloak ──code──► back to React
   │                                                       │
   │◄────── SDK 換 token、auto refresh、silent check ─────┘
   │
   └─Bearer access_token──► ASP.NET Core ──verify via JWKS──► Keycloak
```

---

## 4. npm package 對照

| Template | 前端                                         | 後端                                                         |
| -------- | -------------------------------------------- | ------------------------------------------------------------ |
| A: PKCE  | `react-oidc-context` + `oidc-client-ts`     | `Microsoft.AspNetCore.Authentication.JwtBearer`              |
| B: BFF   | （無，沿用現有 axios）                       | `Microsoft.AspNetCore.Authentication.OpenIdConnect`          |
| C: SDK   | `keycloak-js` + `@react-keycloak/web`       | `Microsoft.AspNetCore.Authentication.JwtBearer`              |

---

## 5. 檔案導覽

- [`01-prerequisites.md`](01-prerequisites.md) — 動工前要跟 IT 拿的資訊清單
- [`02-template-pkce.md`](02-template-pkce.md) — Template A 實作
- [`03-template-bff.md`](03-template-bff.md) — Template B 實作
- [`04-template-keycloak-js.md`](04-template-keycloak-js.md) — Template C 實作
- [`05-multi-provider-switch.md`](05-multi-provider-switch.md) — 用 env 在 Google / Keycloak 之間切換
