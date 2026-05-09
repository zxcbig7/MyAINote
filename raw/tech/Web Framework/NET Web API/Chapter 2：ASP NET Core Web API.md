---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Chapter 2：ASP.NET Core Web API

## 2.1  [ASP.NET](http://asp.net/) Core Web API

- Web API 專案模板已內建：
    - HTTP Pipeline
    - Dependency Injection (DI)
    - Middleware 架構
    - Swagger 整合能力
- **Controller-based API** 適合學習與大型專案：
    - 結構清楚
    - 職責分明
    - 易於測試與擴充
    - 清楚對應 MVC 與 REST 概念

## 2.2 建立專案（標準設定）

### 專案類型

- ASP.NET Core Web API
- .NET 版本：**.NET 8**

### 初始設定建議

- Authentication：None（後續章節再加入）
- HTTPS：啟用
- OpenAPI / Swagger：啟用
- Docker：暫不啟用（部署章節再處理）

## 2.3 專案資料夾結構解析

建立完成後，專案會包含以下核心結構：

```
/Controllers
    WeatherForecastController.cs

/Properties
    launchSettings.json

appsettings.json
appsettings.Development.json
Program.cs
```

### 各項目角色說明

### Controllers

- API 的入口層
- 負責：
    - 接收 HTTP Request
    - 呼叫 Service
    - 回傳 HTTP Response
- **不應包含商業邏輯**

---

### appsettings.json

- 應用程式設定來源
- 常見用途：
    - Connection String
    - Feature Flag
    - 外部服務設定

### appsettings.Development.json

- 開發環境專用設定
- 會覆蓋 appsettings.json

---

### Program.cs

- 應用程式的「啟動與組裝中心」
- 負責：
    - 建立 DI Container
    - 註冊 Middleware
    - 設定 HTTP Pipeline
- **是 Web API 最重要的檔案**

## 2.4 Program.cs 的角色與生命週期

### Program.cs 的核心職責

- 建立 Web Host
- 設定服務（Services）
- 設定中介軟體（Middleware）
- 啟動 HTTP Server

### 高階流程概覽

1. 建立 WebApplicationBuilder
2. 註冊 Services（DI）
3. Build Application
4. 設定 Middleware Pipeline
5. 啟動監聽 HTTP Request

## 2.5 Program.cs（結構化解析）

以下為典型的 .NET 8 Web API Program.cs 結構（語意版）：

```csharp
var builder = WebApplication.CreateBuilder(args);

// ===== Service Registration =====
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// ===== Middleware Pipeline =====
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();

```

### 關鍵設計概念

### Service Registration（服務註冊）

- `builder.Services` 是 **DI Container**
- 所有可被注入的元件都必須先註冊
- 註冊順序不影響執行，但影響可讀性

---

### Middleware Pipeline（中介軟體管線）

- Middleware 依「註冊順序」執行
- 每個 Request 都會依序流過 Pipeline
- 順序錯誤會造成：
    - 授權失效
    - CORS 問題
    - Request 無法到 Controller

---

### MapControllers

- 將 Controller 與 Routing 系統接上
- 沒有這一行：
    - Controller 不會被執行
    - API 全部 404

## 2.6 Middleware Pipeline 的設計原則

- **先安全，再功能**
    - HTTPS
    - Authentication / Authorization
- **最後才是 Endpoint Mapping**
- Middleware 是橫切關注點（Cross-cutting Concern）

## Chapter 2 小結

- Web API 專案不是從 Controller 開始，而是從 Program.cs 開始
- Program.cs 決定：
    - 系統能力
    - 擴充方式
    - 安全與效能上限
- Controller 只是 Pipeline 的其中一站