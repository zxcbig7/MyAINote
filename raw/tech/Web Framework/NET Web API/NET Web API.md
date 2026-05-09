---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# .NET Web API

# 學習資源

https://github.com/MoienTajik/AspNetCore-Developer-Roadmap/blob/master/ReadMe.zh-Hant.md

# 大綱

# 先備知識

[ **HTTP 協議**](NET%20Web%20API/HTTP%20%E5%8D%94%E8%AD%B0%2033c8fda15f6f80f39056cce3dac69202.md)

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

[Chapter 1：HTTP 與 Web API 的核心概念](NET%20Web%20API/Chapter%201%EF%BC%9AHTTP%20%E8%88%87%20Web%20API%20%E7%9A%84%E6%A0%B8%E5%BF%83%E6%A6%82%E5%BF%B5%203158fda15f6f8167af9ac36b1550f86d.md)

[Chapter 2：[ASP.NET](http://asp.net/) Core Web API ](NET%20Web%20API/Chapter%202%EF%BC%9AASP%20NET%20Core%20Web%20API%203158fda15f6f81c7a50aff477ba7a873.md)

[Chapter 3：Controller、Routing 與 Action 設計](NET%20Web%20API/Chapter%203%EF%BC%9AController%E3%80%81Routing%20%E8%88%87%20Action%20%E8%A8%AD%E8%A8%88%203158fda15f6f819b8febc7d5705c1fbc.md)

[Chapter 4：DTO 與資料模型設計](NET%20Web%20API/Chapter%204%EF%BC%9ADTO%20%E8%88%87%E8%B3%87%E6%96%99%E6%A8%A1%E5%9E%8B%E8%A8%AD%E8%A8%88%203158fda15f6f81c2ab84fe67eccbf1cb.md)

[Chapter 5：Dependency Injection 與 Service 設計](NET%20Web%20API/Chapter%205%EF%BC%9ADependency%20Injection%20%E8%88%87%20Service%20%E8%A8%AD%E8%A8%88%203158fda15f6f81508fe0d19a1250781b.md)

[Chapter 6：Middleware 與全域處理機制](NET%20Web%20API/Chapter%206%EF%BC%9AMiddleware%20%E8%88%87%E5%85%A8%E5%9F%9F%E8%99%95%E7%90%86%E6%A9%9F%E5%88%B6%203158fda15f6f8187a878e0da755a39ef.md)

[Chapter 7：EF Core 與資料存取設計](NET%20Web%20API/Chapter%207%EF%BC%9AEF%20Core%20%E8%88%87%E8%B3%87%E6%96%99%E5%AD%98%E5%8F%96%E8%A8%AD%E8%A8%88%203158fda15f6f81d7bab3e0652cd4865c.md)

[Chapter 8：Authentication 與 Authorization（JWT）](NET%20Web%20API/Chapter%208%EF%BC%9AAuthentication%20%E8%88%87%20Authorization%EF%BC%88JWT%EF%BC%89%203158fda15f6f8120a071e6a94067ad92.md)

[Chapter 9：Swagger、API 文件化與版本管理](NET%20Web%20API/Chapter%209%EF%BC%9ASwagger%E3%80%81API%20%E6%96%87%E4%BB%B6%E5%8C%96%E8%88%87%E7%89%88%E6%9C%AC%E7%AE%A1%E7%90%86%203158fda15f6f8108aee9eb6100745e5a.md)

[Chapter 10：測試、部署與正式上線準備](NET%20Web%20API/Chapter%2010%EF%BC%9A%E6%B8%AC%E8%A9%A6%E3%80%81%E9%83%A8%E7%BD%B2%E8%88%87%E6%AD%A3%E5%BC%8F%E4%B8%8A%E7%B7%9A%E6%BA%96%E5%82%99%203158fda15f6f81d4b650fb75852c0c35.md)

# 其他補充

[[ASP.NET](http://asp.net/) Core Web API 常用 Attribute 整理](NET%20Web%20API/ASP%20NET%20Core%20Web%20API%20%E5%B8%B8%E7%94%A8%20Attribute%20%E6%95%B4%E7%90%86%2032f8fda15f6f808db4c2ce9b8b202de1.md)

[Middleware Pipeline](NET%20Web%20API/Middleware%20Pipeline%203158fda15f6f8153b354c77ab24693a6.md)

[Swagger 在 HTTP Pipeline 中的位置與設計理由](NET%20Web%20API/Swagger%20%E5%9C%A8%20HTTP%20Pipeline%20%E4%B8%AD%E7%9A%84%E4%BD%8D%E7%BD%AE%E8%88%87%E8%A8%AD%E8%A8%88%E7%90%86%E7%94%B1%203158fda15f6f81bf812dec60e373fa4c.md)

[Authentication / Authorization Pipeline](NET%20Web%20API/Authentication%20Authorization%20Pipeline%203158fda15f6f81228863ecc583c55361.md)

[後端各種權限管理的寫法，搭配前端操作的實務範例](NET%20Web%20API/%E5%BE%8C%E7%AB%AF%E5%90%84%E7%A8%AE%E6%AC%8A%E9%99%90%E7%AE%A1%E7%90%86%E7%9A%84%E5%AF%AB%E6%B3%95%EF%BC%8C%E6%90%AD%E9%85%8D%E5%89%8D%E7%AB%AF%E6%93%8D%E4%BD%9C%E7%9A%84%E5%AF%A6%E5%8B%99%E7%AF%84%E4%BE%8B%203158fda15f6f81c78724f5e862397af8.md)

[appsetting.json](NET%20Web%20API/appsetting%20json%203158fda15f6f8189a846d16437754ce2.md)

[.NET 6 Web API JWT 驗證與授權完整設定與實作指南](NET%20Web%20API/NET%206%20Web%20API%20JWT%20%E9%A9%97%E8%AD%89%E8%88%87%E6%8E%88%E6%AC%8A%E5%AE%8C%E6%95%B4%E8%A8%AD%E5%AE%9A%E8%88%87%E5%AF%A6%E4%BD%9C%E6%8C%87%E5%8D%97%203158fda15f6f81f4a4cbfa53bc830c84.md)

[Authentication & Authorization ](NET%20Web%20API/Authentication%20&%20Authorization%2032f8fda15f6f80d09d06f5d891562e78.md)