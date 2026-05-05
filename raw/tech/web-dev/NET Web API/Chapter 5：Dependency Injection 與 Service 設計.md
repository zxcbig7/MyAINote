# Chapter 5：Dependency Injection 與 Service 設計

## 5.1 為什麼 ASP.NET Core 強制你使用 DI

### 傳統寫法的問題

```csharp
public class UsersController : ControllerBase
{
    private readonly UserService _service = new UserService();
}
```

這種寫法會造成：

- Controller 與實作類別強耦合
- 無法替換實作（測試、Mock、版本切換）
- 生命週期不可控
- 隱性資源洩漏（DB、HttpClient）

### Dependency Injection (DI) 解決的核心問題

- **解耦（Decoupling）**
- **生命週期管理**
- **可測試性**
- **系統可擴充性**

**結論**

> 在 ASP.NET Core 中，不使用 DI，等同放棄框架的設計優勢。
> 

## 5.2 DI 在 ASP.NET Core 的整體角色

### 系統架構中的位置

- Controller 不負責建立依賴
- DI Container 負責：
    - 建立物件
    - 注入相依物件
    - 管理生命週期

### 執行流程摘要

1. Request 進入系統
2. Framework 建立 Controller
3. DI Container 注入所需 Service
4. Controller 執行 Action

## 5.3 Service 的基本設計方式

### 定義介面（Interface）

```csharp
public interface IUserService
{
    UserResponse GetUser(int id);
}
```

### 實作 Service

```csharp
public class UserService : IUserService
{
    public UserResponse GetUser(int id)
    {
        return new UserResponse
        {
            Id = id,
            Name = "Demo User"
        };
    }
}

```

### 在 Controller 中注入

```csharp
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;

    public UsersController(IUserService userService)
    {
        _userService = userService;
    }
}

```

**設計原則**

- Controller 只依賴介面
- 實作細節交給 DI Container

## 5.4 在 Program.cs 註冊 Service

### 基本註冊方式

```csharp
builder.Services.AddScoped<IUserService, UserService>();
```

### 註冊語意

- `IUserService`：對外使用的抽象
- `UserService`：實際建立的類別

## 5.5 Service Lifetime（非常重要）

ASP.NET Core 提供三種生命週期。

### 1. Transient

- 每次請求都建立新實例
- 適合：
    - 無狀態服務
    - 輕量邏輯

```csharp
builder.Services.AddTransient<IService, Service>();
```

---

### 2. Scoped（Web API 最常用）

- 每個 HTTP Request 共用同一實例
- 適合：
    - DB Context
    - 業務服務

```csharp
builder.Services.AddScoped<IService, Service>();
```

---

### 3. Singleton

- 整個應用程式只建立一個實例
- 適合：
    - Cache
    - 設定物件
    - 無狀態工具類

```csharp
builder.Services.AddSingleton<IService, Service>();
```

## 5.6 常見錯誤與災難級問題

### 錯誤 1：Singleton 注入 Scoped

```csharp
builder.Services.AddSingleton<MyService>();
builder.Services.AddScoped<MyDbContext>();
```

- 會導致：
    - Runtime Exception
    - 不可預期行為

> 長生命週期不可依賴短生命週期。
> 

---

### 錯誤 2：Service 中 new DbContext

- 繞過 DI
- 無法正確管理 Transaction
- 容易造成連線耗盡

---

### 錯誤 3：Controller 承擔過多邏輯

- DI 使用正確，但分層錯誤
- 導致：
    - Controller 肥大
    - 難以測試

## 5.7 Service Layer 的標準責任

Service 應負責：

- 商業邏輯
- 流程控制
- Domain 規則
- 呼叫 Repository / External Service

Controller 應只負責：

- HTTP 相關處理
- Request / Response 封裝

## 5.8 一個標準分層示意

```
Controller
   ↓
Service(ApplicationLogic)
   ↓
Repository/DbContext
```

- Controller：HTTP
- Service：業務
- Data：資料

## Chapter 5 設計準則（定稿）

- 所有依賴皆由 DI 注入
- Controller 不建立物件
- Service 依賴介面而非實作
- Web API 中優先使用 Scoped
- 嚴格遵守生命週期規則

---

## Chapter 5 小結

- DI 是 ASP.NET Core 的核心架構能力
- 正確使用 DI 能顯著提升可測試性與可維護性
- Service 設計品質，直接影響專案壽命