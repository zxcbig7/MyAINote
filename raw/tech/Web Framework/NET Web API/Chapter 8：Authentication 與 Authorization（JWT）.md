# Chapter 8：Authentication 與 Authorization（JWT）

## 8.1 Authentication 與 Authorization 的角色區分

### Authentication（身分驗證）

- 驗證「你是誰」
- 回答問題：Request 來自哪個使用者
- 常見方式：
    - JWT
    - Cookie
    - OAuth

### Authorization（權限授權）

- 驗證「你能做什麼」
- 回答問題：此使用者是否有權限執行該操作
- 依據：
    - Role
    - Policy
    - Claim

**核心原則**

- Authentication 先於 Authorization
- 沒有身分，不談權限

---

## 8.2 為什麼 Web API 常用 JWT

### JWT（JSON Web Token）的特性

- 無狀態（Stateless）
- 不依賴 Server Session
- 適合前後端分離與微服務架構

### JWT 的組成

- Header：簽章與加密資訊
- Payload：使用者資訊（Claims）
- Signature：防竄改驗證

---

## 8.3 JWT 在 Web API 中的整體流程

### 標準流程

1. Client 傳送帳密至登入 API
2. Server 驗證成功
3. Server 發出 JWT
4. Client 於每次 Request 攜帶 JWT
5. Server 驗證 Token 合法性
6. 根據 Claims 進行授權判斷

---

## 8.4 JWT 設定（Program.cs）

### 設定金鑰（appsettings.json）

```json
{
  "Jwt": {
    "Key": "YourVerySecretKey",
    "Issuer": "DemoApi",
    "Audience": "DemoClient",
    "ExpireMinutes": 60
  }
}
```

---

### 註冊 Authentication

```csharp
builder.Services
    .AddAuthentication("Bearer")
    .AddJwtBearer("Bearer", options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,

            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };
    });

```

### Middleware 註冊順序

```csharp
app.UseAuthentication();
app.UseAuthorization();
```

**順序不可顛倒**

---

## 8.5 建立 Token 的標準作法

### Token 產生範例

```csharp
var claims = new[]
{
    new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
    new Claim(ClaimTypes.Name, user.Name),
    new Claim(ClaimTypes.Role, "Admin")
};

var key = new SymmetricSecurityKey(
    Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));

var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

var token = new JwtSecurityToken(
    issuer: _config["Jwt:Issuer"],
    audience: _config["Jwt:Audience"],
    claims: claims,
    expires: DateTime.UtcNow.AddMinutes(60),
    signingCredentials: creds
);

return new JwtSecurityTokenHandler().WriteToken(token);

```

---

## 8.6 在 Controller 套用授權

### 需要登入

```csharp
[Authorize]
[HttpGet]
public IActionResult GetProfile()
{
    return Ok();
}
```

---

### 依 Role 控制

```csharp
[Authorize(Roles = "Admin")]
[HttpDelete("{id}")]
public IActionResult DeleteUser(int id)
{
    return Ok();
}
```

---

## 8.7 Policy-based Authorization（進階但實務必備）

### Policy 定義（Program.cs）

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));
});
```

### 套用 Policy

```csharp
[Authorize(Policy = "AdminOnly")]
public IActionResult AdminAction()
{
    return Ok();
}
```

**優點**

- 權限規則集中管理
- 適合大型系統

---

## 8.8 Claims 設計原則

### 常見 Claims

- NameIdentifier：使用者 ID
- Name：顯示名稱
- Role：角色
- 自訂業務 Claim

### 設計原則

- Claims 放「身分與權限」
- 不放敏感或大量資料
- Token 大小需控制

---

## 8.9 Refresh Token 策略（概念層）

### 為什麼需要 Refresh Token

- Access Token 壽命應短
- 降低 Token 洩漏風險

### 基本策略

- Access Token：短效
- Refresh Token：長效、Server 管理
- 可撤銷（Revoke）

---

## 8.10 常見安全錯誤

### 錯誤 1：JWT 金鑰寫死在程式碼

- 應使用：
    - appsettings
    - Environment Variable
    - Secret Manager

### 錯誤 2：Token 過期時間過長

- 增加洩漏風險

### 錯誤 3：只做 Authentication，沒做 Authorization

- 等同所有人都能做所有事

---

## Chapter 8 設計準則（定稿）

- Authentication 與 Authorization 明確分離
- JWT 用於身分，不用於狀態
- Middleware 順序固定
- 權限規則集中管理
- Token 設計以安全優先

---

## Chapter 8 小結

- JWT 是 Web API 主流認證方式
- Policy-based Authorization 是可維護的權限設計
- 安全設計錯誤，修正成本極高