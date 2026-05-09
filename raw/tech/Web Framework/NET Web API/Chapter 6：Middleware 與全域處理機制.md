# Chapter 6：Middleware 與全域處理機制

## 6.1 Middleware 的核心概念

### Middleware 的定義

Middleware 是 **HTTP Request / Response 管線中的處理節點**，負責處理橫切關注點（Cross-cutting Concerns）。

每一個 Request：

- 依序流過所有 Middleware
- 最終到達 Endpoint（Controller）
- Response 再反向流回

### Middleware 能處理的事情

- 驗證與授權
- 例外處理
- Logging
- CORS
- Request/Response 轉換
- 效能監控

**關鍵特性**

- Middleware 與業務邏輯無關
- 一次實作，全系統適用

---

## 6.2 Middleware Pipeline 的執行模型

### Pipeline 結構概念

```
Request
  ↓
MiddlewareA
  ↓
MiddlewareB
  ↓
Controller (Endpoint)
  ↑
MiddlewareB
  ↑
MiddlewareA
Response
```

### 執行特性

- **順序非常重要**
- Middleware 可以：
    - 在 Request 前處理
    - 在 Response 後處理
- Middleware 可決定是否「中斷管線」

---

## 6.3 Program.cs 中的 Middleware 設定順序

### 典型 Web API Pipeline

```csharp
app.UseExceptionHandler();
app.UseHttpsRedirection();
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
```

### 設計原則

- 安全相關 Middleware 放前面
- Routing 與 Endpoint Mapping 放最後
- 全域攔截型 Middleware 優先註冊

---

## 6.4 Middleware 的三種註冊方式

### Use

- 標準 Middleware
- 可呼叫下一個 Middleware

```csharp
app.Use(async (context, next) =>
{
    await next();
});
```

---

### Run

- 終結管線
- 不呼叫下一個 Middleware

```csharp
app.Run(async context =>
{
    await context.Response.WriteAsync("End");
});
```

---

### Map

- 根據路徑分支 Pipeline

```csharp
app.Map("/health", app =>
{
    app.Run(async ctx =>
    {
        await ctx.Response.WriteAsync("OK");
    });
});
```

---

## 6.5 自訂 Middleware 的標準寫法

### Middleware 類別結構

```csharp
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestLoggingMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Before
        await _next(context);
        // After
    }
}

```

### 註冊 Middleware

```csharp
app.UseMiddleware<RequestLoggingMiddleware>();
```

---

## 6.6 全域例外處理（必做）

### 為什麼不能在 Controller try-catch

- 重複、容易漏、不一致

### 正確作法

- 使用全域 Exception Handling Middleware
- 統一錯誤格式與狀態碼

### 設計原則

- Client 不應看到系統例外細節
- Server 應完整記錄錯誤資訊

---

## 6.7 一個簡化的全域例外 Middleware 範例

```csharp
public class GlobalExceptionMiddleware
{
    private readonly RequestDelegate _next;

    public GlobalExceptionMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            context.Response.StatusCode = 500;
            context.Response.ContentType = "application/json";

            var result = new
            {
                message = "Internal Server Error"
            };

            await context.Response.WriteAsJsonAsync(result);
        }
    }
}

```

---

## 6.8 Logging 與 Request Trace

### Middleware 在 Logging 的角色

- 記錄：
    - Request Path
    - Method
    - Status Code
    - 執行時間
- 提供問題追蹤能力

### 設計建議

- Logging 不應寫在 Controller
- Logging 應集中在 Middleware 或 Filter

---

## 6.9 Middleware 與 Filter 的分工

### Middleware

- 處理整體 HTTP Pipeline
- 與 Routing 無關
- 適合全域功能

### Filter（後續章節詳述）

- 綁定 Controller / Action
- 適合：
    - 驗證
    - 權限檢查
    - 行為前後處理

---

## Chapter 6 設計準則（定稿）

- 所有橫切關注點使用 Middleware
- Middleware 順序不可隨意更動
- 全域例外處理必須集中
- Controller 不處理系統層邏輯
- Logging 與安全應全域化

---

## Chapter 6 小結

- Middleware 是 Web API 的「系統骨幹」
- 設計正確的 Pipeline，能避免大量重複程式碼
- 全域處理機制是穩定系統的必要條件