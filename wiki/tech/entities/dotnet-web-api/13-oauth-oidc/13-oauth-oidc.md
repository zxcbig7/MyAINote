---
type: concept
domain: tech
tags: [dotnet, aspnet, oauth, oidc, google-login, pkce, id-token, forwarded-headers]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 13 章：OAuth 2.0 與 OIDC — 「用 Google 登入」按鈕背後

## 一個按鈕，六個往返

使用者點下「使用 Google 登入」，兩秒後就進到系統首頁。這兩秒裡瀏覽器實際上跑了六趟，中間有三個不同的伺服器參與，交換了三種不同的憑證。

大多數人第一次接 Google 登入的方式是：找一篇教學、複製設定、能跑就好。這在事情順利時沒問題，出事時就完全卡住——`redirect_uri_mismatch` 是什麼意思？為什麼本機好好的、上了正式環境就一直重導向？前端拿到的那串 token 到底該不該傳給後端？

這一章把整個流程拆開。理解它之後，那些錯誤訊息會變得可讀。

---

## 一、OAuth 2.0 與 OIDC 的分工

先釐清兩個常被混用的名詞：

**OAuth 2.0 是「授權」框架。** 它解決的問題是：「我要允許某個應用程式代表我，存取我在另一個服務上的資料」——例如允許某個排程工具讀取我的 Google 日曆。它的產出是 **access token**，代表「持有者被授權存取某些資源」。

**OIDC（OpenID Connect）是蓋在 OAuth 2.0 上的「認證」層。** 它解決的是「這個人是誰」。它的產出是 **ID token**——一個 JWT，內容描述使用者的身分。

「用 Google 登入」需要的是後者。歷史上很多系統誤用 OAuth 2.0 做登入（拿 access token 去呼叫使用者資訊 API，把結果當成身分），這在某些情境下有安全漏洞——access token 沒有綁定「發給誰」的資訊，攻擊者可以把在別處取得的 token 拿來冒充。OIDC 就是為了修正這個誤用而生的。

### 1.1 四個角色

| 角色 | 在「Google 登入」裡是誰 |
| --- | --- |
| Resource Owner | 使用者本人 |
| Client | 你的應用程式 |
| Authorization Server | Google 的帳號伺服器 |
| Resource Server | 你的 API（或 Google 的 API） |

### 1.2 三種 token 別搞混

| Token | 給誰用 | 內容 | 你該做什麼 |
| --- | --- | --- | --- |
| **ID Token** | 你的應用程式 | 使用者是誰（JWT） | **驗證它**，用來確認身分 |
| **Access Token** | 資源伺服器（Google API） | 授權範圍 | 原封不動帶去呼叫 Google API |
| **Refresh Token** | 授權伺服器 | 換新 token 用 | 安全保存，通常只有後端持有 |

一個常見的錯誤是**拿 Google 的 access token 當作自家 API 的認證憑證**。那是給 Google API 用的，你的 API 沒有能力驗證它的完整語意（除非每次都去呼叫 Google 的 tokeninfo 端點——慢且脆弱）。正確做法是驗證 ID token 確認身分，然後**簽發自家的 JWT**（第 12 章）。

---

## 二、授權碼流程（Authorization Code Flow）

這是目前唯一推薦的流程。完整步驟：

```text
1. 使用者點「Google 登入」
   → 瀏覽器導向 Google：
     GET https://accounts.google.com/o/oauth2/v2/auth
       ?client_id=xxx
       &redirect_uri=https://app.example.com/signin-google
       &response_type=code
       &scope=openid email profile
       &state=<隨機值>
       &code_challenge=<PKCE>
       &code_challenge_method=S256

2. 使用者在 Google 頁面登入並同意授權

3. Google 導回你指定的 redirect_uri：
     GET https://app.example.com/signin-google?code=<授權碼>&state=<同一個隨機值>

4. 你的後端驗證 state（防 CSRF），然後用 code 去換 token：
     POST https://oauth2.googleapis.com/token
       code=<授權碼>
       client_id=xxx
       client_secret=yyy          ← 只有後端知道
       code_verifier=<PKCE>
       grant_type=authorization_code

5. Google 回傳：
     { "id_token": "eyJ...", "access_token": "ya29...", "refresh_token": "1//..." }

6. 你驗證 id_token 的簽章與 claims，取出使用者身分，簽發自家的 JWT 給前端
```

### 2.1 為什麼要多一趟「換 token」

最直覺的設計是「Google 直接把 token 放在導回的 URL 裡」——那就是已經被淘汰的 **Implicit Flow**。它的問題是：

- Token 出現在 URL 中，會被記錄在瀏覽器歷史、伺服器存取日誌、Referer header
- 無法驗證接收者的身分（誰拿到那個 URL 誰就有 token）
- 無法安全地取得 refresh token

授權碼流程的關鍵在於：**URL 裡出現的只是一個短命的、一次性的授權碼，它必須配合只有後端知道的 client secret 才能換成 token。** 攻擊者即使攔截到授權碼，沒有 secret 也換不到東西。

### 2.2 `state`：防 CSRF

`state` 是你產生的隨機值，Google 會原封不動送回來。你必須比對它與當初發出去的是否一致。

沒有它的話，攻擊者可以誘導受害者的瀏覽器完成「登入攻擊者帳號」的流程——受害者以為自己在用自己的帳號，實際上操作的是攻擊者的帳號（登入 CSRF）。ASP.NET Core 的內建 handler 會自動處理 `state`，用一個暫時的 cookie 保存。

### 2.3 PKCE：公開客戶端的必需品

原始的授權碼流程假設 client secret 真的是祕密。但**SPA 和行動 App 沒有辦法保守祕密**——JS 程式碼可以被讀取，App 可以被反編譯。

**PKCE**（Proof Key for Code Exchange）補上這個缺口：

```text
1. 客戶端產生一個隨機字串 code_verifier
2. 算出 code_challenge = BASE64URL(SHA256(code_verifier))
3. 授權請求時送出 code_challenge
4. 換 token 時送出原始的 code_verifier
5. 授權伺服器驗證 SHA256(code_verifier) == 先前收到的 code_challenge
```

攻擊者即使攔截到授權碼，也沒有 `code_verifier`（它從未在網路上傳輸過），換不到 token。

現在的建議是**所有客戶端都用 PKCE**，包括有 secret 的後端應用——它是額外一層防護，成本幾乎為零。ASP.NET Core 的 OIDC handler 預設啟用（`options.UsePkce = true`）。

---

## 三、ASP.NET Core 的實作

### 3.1 後端主導（傳統 MVC / 同網域）

```csharp
builder.Services.AddAuthentication(options =>
{
    options.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = GoogleDefaults.AuthenticationScheme;
})
.AddCookie()
.AddGoogle(options =>
{
    options.ClientId = builder.Configuration["Google:ClientId"]!;
    options.ClientSecret = builder.Configuration["Google:ClientSecret"]!;
    options.CallbackPath = "/signin-google";      // 必須與 Google Console 註冊的一致

    options.Scope.Add("email");
    options.Scope.Add("profile");

    options.Events.OnCreatingTicket = context =>
    {
        // 這裡可以把 Google 的資訊寫進本地資料庫、補上自訂 claims
        return Task.CompletedTask;
    };
});
```

流程走完後，使用者身分被寫進一個 cookie（`DefaultScheme` 是 Cookie）。這個模式適合同網域的傳統網站。

注意 `DefaultChallengeScheme = Google`——它的意思是「需要登入時，去 Google」。所以任何 `[Authorize]` 失敗都會觸發 Google 的登入流程。

### 3.2 前後端分離（實務主流）

React SPA + 獨立 API 的架構下，比較實際的做法是：**前端拿到 Google 的 ID token，傳給後端驗證，後端簽發自家 JWT。**

前端用 Google Identity Services 取得 ID token，然後：

```csharp
[HttpPost("auth/google")]
[AllowAnonymous]
public async Task<IActionResult> GoogleLoginAsync(
    [FromBody] GoogleLoginDto dto, CancellationToken ct)
{
    GoogleJsonWebSignature.Payload payload;
    try
    {
        payload = await GoogleJsonWebSignature.ValidateAsync(
            dto.IdToken,
            new GoogleJsonWebSignature.ValidationSettings
            {
                Audience = new[] { _googleOptions.ClientId }    // ⚠️ 必須檢查
            });
    }
    catch (InvalidJwtException)
    {
        return Unauthorized("Invalid Google token");
    }

    if (!payload.EmailVerified)
    {
        return Unauthorized("Email not verified");
    }

    var user = await _userService.FindOrCreateByGoogleAsync(payload.Subject, payload.Email, ct);

    return Ok(new
    {
        accessToken = _tokenService.CreateAccessToken(user),
        refreshToken = await _tokenService.CreateRefreshTokenAsync(user, ct)
    });
}
```

（`GoogleJsonWebSignature` 來自 `Google.Apis.Auth` 套件。也可以用標準的 `JwtBearer` 設定 `Authority = "https://accounts.google.com"` 自行驗證，兩種都可行。）

三個絕對不能省的檢查：

**檢查 `Audience`。** 必須等於你自己的 client ID。少了這個檢查，任何人都能拿「別的網站簽發給他自己的 Google ID token」來登入你的系統——那個 token 是 Google 真簽的、簽章驗得過，但它不是給你的。**這是實務上最常見也最嚴重的 OIDC 實作漏洞。**

**檢查 `EmailVerified`。** 未驗證的 email 可能不屬於這個人。如果你用 email 當作使用者的唯一識別，這會變成帳號接管漏洞。

**用 `Subject`（`sub`）當唯一鍵，不要用 email。** email 可以變更，`sub` 是 Google 對這個使用者的永久識別碼。用 email 當主鍵的話，使用者改了 Google 帳號的 email 之後就變成另一個人了。

### 3.3 兩種模式的取捨

| | 後端主導（AddGoogle） | 前端主導（傳 ID token） |
| --- | --- | --- |
| Client secret | 後端持有，安全 | 前端流程不需要 secret |
| 適合 | 同網域、傳統網站 | SPA、行動 App |
| 跨網域 cookie 問題 | 需處理 | 無 |
| 拿 refresh token 呼叫 Google API | 容易 | 需要額外流程 |
| 實作複雜度 | 框架包好 | 要自己驗證 token |

如果只需要「用 Google 帳號登入」而不需要代表使用者呼叫 Google API，前端主導的模式更簡潔。需要長期存取使用者的 Google 資料（例如同步日曆）就得走後端主導，才拿得到 refresh token。

---

## 四、實務上最常卡住的三個問題

### 4.1 `redirect_uri_mismatch`

Google 要求 redirect URI **完全比對**——協定、網域、port、路徑、結尾斜線，一個字元都不能差。

```text
Google Console 註冊：https://app.example.com/signin-google
實際送出的：      https://app.example.com/signin-google/     ← 多一個斜線，失敗
                  http://app.example.com/signin-google       ← http 不是 https，失敗
                  https://www.app.example.com/signin-google  ← 多了 www，失敗
```

開發時要把 `http://localhost:5173` 之類的本機位址也註冊上去。每個環境（本機、測試、正式）的 URI 都要各自註冊。

### 4.2 反向代理後面的 scheme 錯誤

這是容器化部署後最常見、也最難自己想通的問題。

架構是：使用者 → HTTPS → Ingress / Cloudflare → **HTTP** → 你的 Pod。

你的應用程式看到的是一個 HTTP 請求，於是它產生的 redirect URI 是：

```text
http://app.example.com/signin-google      ← 錯的，Google 那邊註冊的是 https
```

結果是 `redirect_uri_mismatch`，或者更詭異的：登入成功後被導回 `http://`，瀏覽器因為 `Secure` cookie 的關係丟掉 session，於是又被導去登入——**無限重導向迴圈**。

解法是讓應用程式信任反向代理送來的 `X-Forwarded-*` header：

```csharp
builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;

    // 在 K8s 裡代理的 IP 不固定，預設的白名單會擋掉。信任範圍要自己決定
    options.KnownNetworks.Clear();
    options.KnownProxies.Clear();
});

// ⚠️ 必須在所有其他 middleware 之前
app.UseForwardedHeaders();
```

兩個要點：

**位置必須最前面。** 它要在任何讀取 `Request.Scheme` 的 middleware 之前執行，否則後面的元件仍然看到 http。

**清空 `KnownNetworks` / `KnownProxies` 有安全意涵。** 它等於「信任任何來源送來的 `X-Forwarded-Proto`」。在 K8s 裡這通常可以接受（Pod 只接受來自 Ingress 的流量，外部無法直接連），但如果 Pod 可能被直接存取，攻擊者就能偽造這些 header。更嚴謹的做法是明確列出 Ingress Controller 的網段。

### 4.3 Cookie 的 `SameSite`

OAuth 流程中，使用者是**從 Google 的網域被導回你的網域**的。這是一個跨站導覽，瀏覽器對 cookie 的處理很嚴格：

- `SameSite=Strict` 的 cookie 在這種情況下**不會被送出**——於是 ASP.NET Core 找不到當初存 `state` 的 correlation cookie，拋出 `Correlation failed`
- `SameSite=None` 必須配 `Secure=true`，否則現代瀏覽器直接丟棄

框架預設的 correlation cookie 已經設成 `SameSite=None` + `Secure`，所以**本機用 http 測試 OAuth 常常會失敗**——因為 `Secure` cookie 在非 HTTPS 下不會被儲存。本機開發要嘛用 https（`dotnet dev-certs https --trust`），要嘛暫時調整 cookie 設定（但別把調整帶進生產）。

`Correlation failed` 這個錯誤訊息幾乎總是指向這三件事之一：cookie 的 `SameSite`/`Secure` 設定、反向代理的 scheme 問題、或使用者在登入頁停留太久導致 correlation cookie 過期。

---

## 五、Scope 與同意畫面

`scope` 決定你要求的權限範圍：

| Scope | 取得什麼 |
| --- | --- |
| `openid` | **必須有**，才會回傳 ID token |
| `email` | email 與 `email_verified` |
| `profile` | 姓名、頭像、語系 |
| `https://www.googleapis.com/auth/calendar.readonly` | 讀取日曆（需要 Google 審核） |

原則是**只要求真正需要的**。要求越多，使用者在同意畫面看到的清單越長，放棄率越高；敏感範圍還需要通過 Google 的驗證審核，流程冗長。

要拿到 refresh token（長期存取 Google API）需要額外參數：

```csharp
options.AccessType = "offline";        // 要求 refresh token
// 且通常需要 prompt=consent 強制重新同意，否則第二次登入不會再給 refresh token
```

「第二次登入拿不到 refresh token」是很常見的困惑——Google 預設只在**首次授權**時發放，之後除非強制重新同意。所以拿到的 refresh token 必須妥善保存，弄丟了就得引導使用者重新授權。

---

## 六、常見誤解

**「OAuth 2.0 就是拿來做登入的。」**
OAuth 2.0 是授權框架，做認證要用蓋在它上面的 OIDC。直接拿 access token 當身分證明是歷史上的誤用，有安全問題。

**「拿 Google 的 access token 當自家 API 的憑證。」**
那是給 Google API 用的。正確做法是驗證 ID token 取得身分，然後簽發自家的 JWT。

**「ID token 是 Google 簽的，驗簽過就可以信任。」**
還必須檢查 `aud` 等於自己的 client ID。少了這個檢查，別的網站的 Google token 也能登入你的系統——簽章一樣是真的。

**「用 email 當使用者的唯一識別碼。」**
email 可以變更。用 `sub`（Google 的永久使用者識別碼）當唯一鍵，email 只當顯示資訊。

**「Implicit flow 比較簡單，先用著。」**
它已被 OAuth 2.1 淘汰。token 出現在 URL 中會外洩到日誌與歷史紀錄。用授權碼流程 + PKCE。

**「本機能跑就代表設定對了。」**
本機沒有反向代理、沒有跨網域 cookie 問題、`localhost` 在瀏覽器有特殊待遇。正式環境的 scheme、SameSite、redirect URI 都是新的變數。

---

## 七、同事會來問你的問題

**Q：`redirect_uri_mismatch` 怎麼修？**
Google Console 註冊的 URI 與實際送出的必須完全一致，包括協定、port、路徑、結尾斜線。最常見的原因是正式環境在反向代理後面，應用程式以為自己是 http，於是產生了 http 的 redirect URI。

**Q：登入成功後一直重導向，繞不出來。**
典型的 scheme 錯誤。加上 `app.UseForwardedHeaders()`（放在所有 middleware 最前面）並設定信任 `XForwardedProto`。應用程式看到 http 時產生的 `Secure` cookie 會被瀏覽器丟棄，於是又被判定未登入。

**Q：`Correlation failed` 是什麼意思？**
存放 OAuth `state` 的 correlation cookie 沒有被送回來。三個常見原因：cookie 的 `SameSite`/`Secure` 設定與當前協定不符（本機用 http 測試最常見）、反向代理的 scheme 問題、使用者在 Google 登入頁停留太久導致 cookie 過期。

**Q：前端拿到的 Google token 可以直接當我們 API 的 token 嗎？**
不行也不該。後端驗證 ID token（務必檢查 `aud` 與 `email_verified`）取得身分，然後簽發自家的 JWT。這樣才能控制有效期、放自訂 claims、實作撤銷。

**Q：第二次用 Google 登入拿不到 refresh token。**
Google 預設只在首次授權時發放。需要重新取得的話要加 `prompt=consent` 強制重新同意。所以第一次拿到的 refresh token 必須妥善保存。

**Q：PKCE 一定要用嗎？我們是後端流程有 client secret。**
建議用。成本幾乎為零，多一層防護。ASP.NET Core 的 OIDC handler 預設就啟用了。

**Q：可以用 email 判斷是不是同一個使用者嗎？**
不要。email 可以在 Google 帳號設定裡變更。用 `sub` 當唯一鍵，並在資料庫上建唯一索引。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[12-jwt-deep-dive]] — 上一章：簽發自家 JWT
- [[14-authorization]] — 下一章：拿到身分之後的權限判斷
- [[11-authentication]] — scheme 模型與 `DefaultSignInScheme`
- [[21-deployment]] — 反向代理與 forwarded headers 的部署設定
