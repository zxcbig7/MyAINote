---
tags: [devops, keycloak, prerequisites]
---

# 動工前 — 跟 IT 要這些資訊

寫 code 之前先拿到全部，否則任何 template 都跑不起來。

---

## 1. Realm 與 server 資訊

| 項目                  | 範例值                                      | 用途                           |
| --------------------- | ------------------------------------------- | ------------------------------ |
| Keycloak server URL   | `https://sso.company.com`                   | 所有 endpoint 的根             |
| Realm 名稱            | `company`                                   | 多租戶區隔                     |
| Issuer (`iss`)        | `https://sso.company.com/realms/company`    | JWT 驗證用                     |
| OIDC discovery URL    | `…/realms/company/.well-known/openid-configuration` | 一切的目錄；有這個就有全部 |
| JWKS URI              | `…/realms/company/protocol/openid-connect/certs` | backend 驗 JWT 簽章用     |
| Authorization endpoint| `…/realms/company/protocol/openid-connect/auth` | 前端 redirect 登入用       |
| Token endpoint        | `…/realms/company/protocol/openid-connect/token` | code 換 token             |
| Userinfo endpoint     | `…/realms/company/protocol/openid-connect/userinfo` | 拿使用者資訊            |
| Logout endpoint       | `…/realms/company/protocol/openid-connect/logout` | end session              |

> 拿到 discovery URL 一份就夠，其他都可以從那裡讀出來。

---

## 2. Client 註冊資訊

依 template 不同，跟 IT 要不同類型的 client：

### Template A / C：Public Client

```
Client ID:           mydevweb-frontend
Client Type:         OpenID Connect
Access Type:         public
Standard Flow:       ✅ Enabled (Authorization Code)
Direct Access:       ❌ Disabled
PKCE:                ✅ Required (S256)
Valid Redirect URIs: http://localhost:5173/*
                     https://viclai.idv.tw/*
Valid Post Logout:   http://localhost:5173/*
                     https://viclai.idv.tw/*
Web Origins:         http://localhost:5173
                     https://viclai.idv.tw
```

### Template B：Confidential Client

```
Client ID:           mydevweb-backend
Client Type:         OpenID Connect
Access Type:         confidential
Standard Flow:       ✅ Enabled
Service Accounts:    （視需要）
Client Secret:       <由 IT 提供>     ← 重要，K8s Secret 注入
Valid Redirect URIs: http://localhost:8082/signin-oidc
                     https://api.viclai.idv.tw/signin-oidc
Backchannel Logout URL: （視需要）
```

---

## 3. 要確認的權限與設定

| 問題                                       | 為什麼要問                                              |
| ------------------------------------------ | ------------------------------------------------------- |
| Token signature algorithm                  | RS256（最常見）/ ES256 — backend 驗章要對齊             |
| Access token / refresh token 有效期         | 影響前端是否需要 silent refresh                         |
| 有沒有提供 `roles` / `groups` claim         | 影響 backend 怎麼做 RBAC                                |
| 有沒有 mapper 把公司資料（員工編號）放進 token | 你的 multi-tenant siteId 是否能從 token 拿到            |
| 登出要不要走 SSO logout                    | 公司可能要求登出時把整個 SSO session 一起清             |
| 開發環境給不給獨立 realm 或 client          | 不要拿 prod client 跑 localhost                         |

---

## 4. 環境變數骨架

拿到資料後填進這些 env：

### Frontend `.env`（Vite）

```bash
# Template A / C
VITE_AUTH_PROVIDER=keycloak
VITE_KEYCLOAK_URL=https://sso.company.com
VITE_KEYCLOAK_REALM=company
VITE_KEYCLOAK_CLIENT_ID=mydevweb-frontend
VITE_API_BASE=https://api.viclai.idv.tw
```

### Backend `appsettings.json`

```json
{
  "Auth": {
    "Provider": "Keycloak"
  },
  "Keycloak": {
    "Authority": "https://sso.company.com/realms/company",
    "Audience": "mydevweb-frontend",
    "ClientId": "mydevweb-backend",
    "ClientSecret": "",
    "RequireHttpsMetadata": true
  }
}
```

### K8s Secret

| 變數                          | 值來源              |
| ----------------------------- | ------------------- |
| `Keycloak__ClientSecret`      | IT 提供（Template B 需要） |
| `Jwt__Key`                    | 若 backend 仍要簽自家 JWT 才需要 |

---

## 5. 本機開發測試方式

正式接通公司 Keycloak 前，可以先用自己跑一份 Keycloak 開發，再切過去。

### 用 Docker 跑本機 Keycloak

```powershell
docker run -p 8180:8080 `
  -e KEYCLOAK_ADMIN=admin `
  -e KEYCLOAK_ADMIN_PASSWORD=admin `
  quay.io/keycloak/keycloak:26.0 `
  start-dev
```

開 `http://localhost:8180`，建一個 realm + client，把 endpoint 換掉就能跑全部 template。等公司資訊到位再切。

---

## 6. 給 IT 的請求模板

```
Hi，我們要把 MyDevWeb 接到公司 Keycloak SSO，請協助：

1. 建立 Keycloak client：
   - Client ID: mydevweb-frontend
   - Type: public, PKCE required (S256)
   - Redirect URIs: http://localhost:5173/*, https://viclai.idv.tw/*
   - Web Origins: http://localhost:5173, https://viclai.idv.tw

2. 請提供：
   - Keycloak server URL
   - Realm 名稱
   - OIDC discovery URL（…/.well-known/openid-configuration）

3. （若選 BFF 架構額外要：）
   - 另一個 confidential client mydevweb-backend
   - 對應的 client_secret

4. Token claim 確認：
   - 是否有 roles / groups
   - 是否能 mapper 加自訂 claim（員工編號、廠區）

謝謝。
```
