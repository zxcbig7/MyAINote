---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Chapter 9：Swagger、API 文件化與版本管理

## 9.1 為什麼 API 文件是工程責任

### API 文件的定位

- API 文件不是附加品
- 是 **API 契約（Contract）的一部分**
- 是前後端、外部系統溝通的唯一依據

### 沒有良好文件的後果

- Client 誤用 API
- 需求溝通成本暴增
- API 改版風險失控

**結論**

> 寫 API 卻不寫文件，等同交付不完整的系統。
> 

---

## 9.2 Swagger / OpenAPI 的角色

### Swagger 是什麼

- Swagger 是 OpenAPI 規範的實作工具
- 可自動產生：
    - API Endpoint 清單
    - Request / Response Schema
    - 測試介面

### 在 ASP.NET Core 中的價值

- 與 Controller / DTO 自動同步
- 降低文件與實作不一致風險
- 可作為測試與驗證工具

---

## 9.3 Swagger 的基本設定（回顧）

### Program.cs 中的基本註冊

```csharp
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
```

```csharp
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}
```

**設計原則**

- Swagger 預設僅在 Development 啟用
- Production 可視需求控管存取

---

## 9.4 使用 Attribute 強化 API 文件品質

### Action 描述（Summary）

```csharp
/// <summary>
/// 取得使用者資料
/// </summary>
[HttpGet("{id}")]
public ActionResult<UserResponse> GetUser(int id)
{
    ...
}
```

### 回傳狀態碼描述

```csharp
[ProducesResponseType(StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
```

### 完整範例

```csharp
/// <summary>
/// 取得指定使用者
/// </summary>
[HttpGet("{id}")]
[ProducesResponseType(typeof(UserResponse), StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
public ActionResult<UserResponse> GetUser(int id)
{
    ...
}
```

---

## 9.5 Request / Response Schema 的可讀性

### DTO 對 Swagger 的影響

- Swagger 直接使用 DTO 定義 Schema
- DTO 設計品質 = 文件品質

### 設計建議

- 欄位命名清楚
- 避免不必要的 Nullable
- 不混用 Request / Response DTO

---

## 9.6 Swagger 與 JWT 認證整合

### 設定 Security Definition

```csharp
builder.Services.AddSwaggerGen(c =>
{
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header
    });

    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

```

### 效果

- Swagger UI 可輸入 JWT
- 直接測試受保護 API

---

## 9.7 API Versioning 的必要性

### 為什麼 API 一定會壞

- 業務需求變更
- 欄位新增或移除
- 行為調整

**原則**

> API 不該因為 Server 升級而破壞 Client。
> 

---

## 9.8 常見 API Versioning 策略

### 1. URL Versioning（最常見）

```
/api/v1/users
/api/v2/users
```

**優點**

- 明確
- 易於理解
- 易於文件化

---

### 2. Header Versioning

```
X-API-Version: 1
```

**優點**

- URL 乾淨
    
    **缺點**
    
- 可讀性較差

---

### 3. Query String Versioning

```
/api/users?version=1
```

**使用較少，不建議新專案**

---

## 9.9 ASP.NET Core API Versioning 基本設定

### 套件

- Microsoft.AspNetCore.Mvc.Versioning

### 基本註冊

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.ReportApiVersions = true;
});
```

### Controller 使用版本

```csharp
[ApiVersion("1.0")]
[Route("api/v{version:apiVersion}/users")]
public class UsersController : ControllerBase
{
}
```

---

## 9.10 多版本 Controller 設計原則

- 不在同一 Action 混版本邏輯
- 新版本建立新 Controller 或新 DTO
- 舊版本僅維護，不新增功能

---

## Chapter 9 設計準則（定稿）

- Swagger 是 API 契約的一部分
- API 文件需與程式碼同步
- DTO 設計直接影響文件品質
- API Versioning 是必備能力
- 不破壞既有 Client 是首要原則

---

## Chapter 9 小結

- 文件化是工程責任，不是選項
- Swagger 提供可視化、可測試的 API 規格
- 版本控管決定 API 的生命週期長度