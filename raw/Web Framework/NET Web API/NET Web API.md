---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# .NET Web API

# 學習資源

https://github.com/MoienTajik/AspNetCore-Developer-Roadmap/blob/master/ReadMe.zh-Hant.md

# 大綱

# 先備知識

[[HTTP 協議]]

# 開發環境

- .NET SDK：8（目前主流且長期支援）
- IDE：Visual Studio 2022 或 VS Code
- API 範例：Controller-based Web API（學習曲線更清楚）
- 文件：Swagger（Swashbuckle）
- 資料庫：先不接 DB，先把 API 核心流程吃透，再進 EF Core

# 基礎知識

- HTTP / REST 基礎：GET/POST/PUT/PATCH/DELETE、Status Code、Headers、Body
- 建立專案與最小 API / Controller API 的差別
- Controller、Routing、Model Binding、Validation
- Middleware pipeline（UseRouting / UseAuthentication / UseAuthorization / UseCors）
- DI（依賴注入）、Service lifetime（Singleton/Scoped/Transient）
- 設定與環境（appsettings、Options pattern、Secret 管理）

# 資料層

- EF Core：DbContext、Entity、Migration、CRUD
- DTO 與 AutoMapper（可選，但常用）
- 交易與並發（Transaction、RowVersion）

# 品質與安全

- 全域例外處理（Exception Handling Middleware）
- Logging（Serilog 可選）與觀測性（Health checks）
- Authentication / Authorization（JWT、Policy、Role）
- CORS、Rate limiting、API Versioning

# 交付

- Swagger 文件化與版本管理
- 測試（Unit + Integration）
- Docker / 部署策略（IIS、Linux、Nginx 反代）
- 開發環境與工具鏈
- Web API 核心概念（HTTP、REST、Controller、DI、Middleware）
- 專案結構與最佳實務（分層、DTO、驗證、例外處理）
- 資料存取（EF Core、Migration、Repository 可選）
- 認證授權（JWT、Roles/Policies、CORS）
- 文件化與測試（Swagger、Postman、Unit/Integration test）
- 部署（Docker、Reverse Proxy、環境變數）
- 延伸能力（Logging、Health Checks、Rate limit、Versioning）

# 主要課程

[[Chapter 1：HTTP 與 Web API 的核心概念]]

[[Chapter 2：ASP NET Core Web API]]

[[Chapter 3：Controller、Routing 與 Action 設計]]

[[Chapter 4：DTO 與資料模型設計]]

[[Chapter 5：Dependency Injection 與 Service 設計]]

[[Chapter 6：Middleware 與全域處理機制]]

[[Chapter 7：EF Core 與資料存取設計]]

[[Chapter 8：Authentication 與 Authorization（JWT）]]

[[Chapter 9：Swagger、API 文件化與版本管理]]

[[Chapter 10：測試、部署與正式上線準備]]

# 其他補充

[[ASP NET Core Web API 常用 Attribute 整理]]

[[Middleware Pipeline]]

[[Swagger 在 HTTP Pipeline 中的位置與設計理由]]

[[Authentication / Authorization Pipeline]]

[[後端各種權限管理的寫法，搭配前端操作的實務範例]]

[[appsetting.json]]

[[.NET 6 Web API JWT 驗證與授權完整設定與實作指南]]

[[Authentication & Authorization]]