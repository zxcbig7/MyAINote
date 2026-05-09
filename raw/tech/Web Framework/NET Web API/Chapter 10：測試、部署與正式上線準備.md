---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Chapter 10：測試、部署與正式上線準備

## 10.1 為什麼 Web API 一定要測試

### 測試的工程價值

- 驗證行為是否符合設計
- 防止未來修改破壞既有功能
- 提供系統行為的「可執行文件」

### 沒有測試的風險

- 重構成本極高
- Bug 回歸頻繁
- 上線品質不可控

**定位**

- 測試是系統的一部分
- 不是額外負擔

---

## 10.2 Web API 的測試層級

### Unit Test（單元測試）

- 測試範圍：
    - Service
    - Domain Logic
- 特性：
    - 不啟動 Web Server
    - 不連資料庫（可 Mock）

### Integration Test（整合測試）

- 測試範圍：
    - Controller
    - Routing
    - Middleware
    - DI 設定
- 使用真實 HTTP Pipeline

**建議策略**

- 業務邏輯：Unit Test
- API 行為：Integration Test

---

## 10.3 Unit Test（Service 層）

### 測試專案建議

- 使用 xUnit
- 專案命名：
    - `YourProject.Tests`

### 範例：測試 Service

```csharp
public class UserServiceTests
{
    [Fact]
    public void GetUser_Returns_User()
    {
        var service = new UserService();
        var result = service.GetUser(1);

        Assert.NotNull(result);
        Assert.Equal(1, result.Id);
    }
}
```

**原則**

- 測試邏輯，不測框架
- 不測 Controller

---

## 10.4 Integration Test（Web API 行為）

### WebApplicationFactory 的角色

- 啟動完整 Web API Pipeline
- 使用記憶體 Host
- 不需真正部署

### 基本設定

```csharp
public class ApiTestFactory 
    : WebApplicationFactory<Program>
{
}
```

### 測試 API Endpoint

```csharp
public class UsersApiTests : IClassFixture<ApiTestFactory>
{
    private readonly HttpClient _client;

    public UsersApiTests(ApiTestFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetUser_Returns_200()
    {
        var response = await _client.GetAsync("/api/users/1");

        response.EnsureSuccessStatusCode();
    }
}
```

---

## 10.5 測試中的資料庫策略

### 常見做法

- InMemory Database（簡單）
- SQLite InMemory（較接近真實 DB）

### 設計原則

- 測試資料可重建
- 不共用 Production DB
- 每個測試獨立

---

## 10.6 環境設定管理（非常重要）

### 環境區分

- Development
- Staging
- Production

### appsettings 設計原則

- 共用設定放 appsettings.json
- 環境差異放 appsettings.{Environment}.json
- **敏感資訊不進版控**

---

## 10.7 Logging 與 Monitoring（上線必備）

### Logging 的目標

- 問題追蹤
- 行為回溯
- 系統健康觀察

### 基本建議

- 結構化 Logging
- 區分：
    - Info
    - Warning
    - Error

### 延伸工具（選用）

- Serilog
- Application Insights
- ELK Stack

---

## 10.8 Docker 化 Web API（實務主流）

### 為什麼要 Docker

- 環境一致
- 部署可重現
- 易於 CI/CD

### 基本 Dockerfile（概念）

```docker
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "YourProject.dll"]
```

---

## 10.9 Production 上線前檢查清單

### 安全

- JWT 金鑰使用環境變數
- Swagger 是否限制存取
- CORS 設定是否正確

### 穩定性

- 全域 Exception Handling 已啟用
- Logging 已設定
- Health Check 可用

### 效能

- Async 全面使用
- DbContext 生命週期正確
- 無阻塞呼叫

---

## Chapter 10 設計準則（定稿）

- 測試是交付的一部分
- Integration Test 驗證整體行為
- 環境設定不可硬編碼
- Docker 是現代部署標準
- Production 需有明確檢查流程

---

## Chapter 10 小結（也是整套課程總結）

- 你已完成一條完整 Web API 開發鏈
- 從 HTTP → Controller → DI → Middleware → DB → Security → 文件 → 測試 → 部署
- 這套結構可直接複製到實務專案