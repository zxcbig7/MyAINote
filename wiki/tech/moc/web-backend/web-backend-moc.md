---
type: moc
domain: tech
tags: [web-backend, dotnet, csharp, python, fastapi, api]
created: 2026-05-10
updated: 2026-08-16
---

# Web Backend MOC

> Map of Content：.NET Web API、FastAPI、C#、Auth 相關筆記入口。

## 核心 Entities

- [[dotnet-web-api]] — ASP.NET Core Web API、Controller、DI、Middleware、JWT（含 22 章 + 2 附錄教材）
- [[python-fast-api]] — FastAPI：ASGI、型別驅動驗證、`Depends`、Pydantic v2（含 12 章 + 3 附錄教材）
- [[csharp]] — C# 語法、OOP、LINQ、async/await
- [[python]] — Python 語言基礎

兩套後端教材假設同一個部署場景（K8s + Oracle + JWT/Google OAuth + 前後端分離），可互相對照；跨框架的翻譯表見 [[13-aspnet-mapping]]。

## Raw 來源（依主題）

### .NET Web API（Chapter 系列）

- [[Chapter 1：HTTP 與 Web API 的核心概念]]
- [[Chapter 2：ASP NET Core Web API]]
- [[Chapter 3：Controller、Routing 與 Action 設計]]
- [[Chapter 4：DTO 與資料模型設計]]
- [[Chapter 5：Dependency Injection 與 Service 設計]]
- [[Chapter 6：Middleware 與全域處理機制]]
- [[Chapter 7：EF Core 與資料存取設計]]
- [[Chapter 8：Authentication 與 Authorization（JWT）]]
- [[Chapter 9：Swagger、API 文件化與版本管理]]
- [[Chapter 10：測試、部署與正式上線準備]]

### .NET 主題

- [[NET Web API]]
- [[ASP NET Core Web API 常用 Attribute 整理]]
- [[Authentication & Authorization]] / [[Authentication Authorization Pipeline]]
- [[NET 6 Web API JWT 驗證與授權完整設定與實作指南]]
- [[後端各種權限管理的寫法，搭配前端操作的實務範例]]
- [[Middleware Pipeline]]
- [[Swagger 在 HTTP Pipeline 中的位置與設計理由]]
- [[HTTP 協議]]
- [[appsetting json]]
- [[Microsoft]]
- [[aspnet-web-api-web-research]]

### C# 語言基礎

- [[C#]]
- [[基礎語法]] / [[進階語法]]
- [[物件導向(Object Oriented Programming)]]
- [[介面(interface)、抽象( abstract)、虛擬(virtual)]]
- [[Function 參數設計]]
- [[Enum Struct Delegate 比較]]
- [[泛型應用]]
- [[修飾詞範圍]]
- [[列舉器(IEnumerable)]]
- [[功能性註解]]
- [[using 陳述式]]
- [[CSV 操作]] / [[Table Library]]
- [[連接SQL]]
- [[LINQ 筆記]] / [[LINQPad]] / [[VS C# Code 筆記]] / [[區域型別推斷]] / [[語法應用]]
- [[C# Framwork]]
- [[csharp-debug-test]]
