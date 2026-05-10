---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Authentication & Authorization

先搞清楚兩個詞

| 詞 | 意思 | 例子 |
| --- | --- | --- |
| **Authentication (驗證)** | 你是誰 | 登入、JWT Token |
| **Authorization (授權)** | 你能做什麼 | 只有 Admin 能刪除 |

## ASP.NET Core 的驗證流程

> Request 進來 → Middleware 讀 Token→ 解析出是誰 (Identity) → Controller 的 [Authorize] 決定能不能進來→ 執行 Action
> 

## 最常見方案：JWT Bearer Token

### Step 1. 安裝套件

```bash
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
```