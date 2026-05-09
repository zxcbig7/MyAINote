# Middleware Pipeline

# 一、什麼是 HTTP Pipeline

**HTTP Pipeline** 是指一個 HTTP Request 從進入 ASP.NET Core 應用程式，到產生 HTTP Response 回傳給 Client 之間，所經過的一連串「中介處理流程」。

這條管線的核心特性是：

- **線性處理**
- **由多個 Middleware 組成**
- **可控制是否繼續往下傳遞**
- **同時影響 Request 與 Response**

簡化來看：

> Request → Middleware A → Middleware B → Middleware C → Controller
> 
> 
> Response ← Middleware C ← Middleware B ← Middleware A
> 

# 二、HTTP Pipeline 的視覺化概念

![image.png](image.png)

![image.png](image%201.png)

每一個 **Middleware** 都像是一個「關卡」：

- 可以檢查或修改 Request
- 可以決定要不要繼續往下
- 在 Response 回傳時，可以再做後處理

# 三、Pipeline 的核心元件：Middleware

## 1. Middleware 是什麼

Middleware 是一段可以：

- 存取 `HttpContext`
- 執行前置邏輯（Before next）
- 呼叫下一個 Middleware
- 執行後置邏輯（After next）

的元件。

## 2. Middleware 的基本結構（概念）

```csharp
public async Task InvokeAsync(HttpContext context, RequestDelegate next)
{
    // Before
    await next(context);
    // After
}
```

# 四、ASP.NET Core 中 Pipeline 的定義位置

HTTP Pipeline 是在 **`Program.cs`** 中建立的。

```csharp
var app = builder.Build();
```

從這一行開始，後續的 `app.UseXxx()`、`app.MapXxx()`，**順序就是 Pipeline 的順序**。

# 五、常見 Middleware 與實際意義

以下依照「實務最常見」順序說明。

---

### 1. `UseHttpsRedirection`

```csharp
app.UseHttpsRedirection();
```

用途：

- 將 HTTP 重新導向至 HTTPS
- 安全性需求

特性：

- 非 HTTPS 請求會被攔截
- 可能直接回傳 Redirect Response，不會進入後續 Pipeline

---

### 2. `UseRouting`

```csharp
app.UseRouting();
```

用途：

- 解析 Request URL
- 決定要對應到哪一個 Endpoint（Controller / Minimal API）

注意：

- **只做「路由解析」**
- 不會真正執行 Controller

---

### 3. `UseCors`

```csharp
app.UseCors("AllowFrontend");
```

用途：

- 處理瀏覽器的跨網域請求（CORS）
- 檢查 Origin、Method、Header

順序非常重要：

- 必須在 `UseRouting` 之後
- 必須在 `MapControllers` 之前

---

### 4. `UseAuthentication`（若有）

```csharp
app.UseAuthentication();
```

用途：

- 驗證使用者身分（JWT、Cookie、OAuth）
- 產生 `HttpContext.User`

---

### 5. `UseAuthorization`

```csharp
app.UseAuthorization();
```

用途：

- 判斷使用者是否有權限存取該 Endpoint
- 搭配 `[Authorize]`、Policy 使用

---

### 6. `MapControllers`

```csharp
app.MapControllers();
```

用途：

- **真正執行 Controller Action**
- Pipeline 的「終點之一」

特性：

- 通常是 Pipeline 的最後階段
- 之後 Response 開始往回傳遞

# 六、完整 Pipeline 範例（標準 Web API）

```csharp
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseRouting();

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
```

# 七、Pipeline 的「進」與「出」行為（關鍵理解）

### Request 流向（進）

```
Client
 ↓
UseHttpsRedirection
 ↓
UseRouting
 ↓
UseCors
 ↓
UseAuthentication
 ↓
UseAuthorization
 ↓
Controller
```

### Response 流向（出）

```
Controller
 ↑
UseAuthorization
 ↑
UseAuthentication
 ↑
UseCors
 ↑
UseRouting
 ↑
UseHttpsRedirection
 ↑
Client
```

這就是為什麼 Middleware 可以：

- 記錄 Response Time
- 統一包裝回傳格式
- 捕捉 Exception

# 八、自訂 Middleware 的實務用途

常見情境：

- 全站 Request / Response Log
- 統一錯誤處理
- Header 檢查（API Key）
- 效能監控（Elapsed Time）

### 範例：簡單的 Request 計時 Middleware

```csharp
app.Use(async (context, next) =>
{
    var start = DateTime.UtcNow;

    await next();

    var elapsed = DateTime.UtcNow - start;
    Console.WriteLine($"Request took {elapsed.TotalMilliseconds} ms");
});

```

# 九、常見錯誤與陷阱

### 1. Middleware 順序錯誤

```csharp
app.MapControllers();
app.UseCors();// ❌ 不會生效
```

原因：

- `MapControllers` 已經終止 Pipeline

### 2. 忘記呼叫 `next()`

```csharp
app.Use(async (context, next) =>
{
    // 沒有 await next()
});
```

結果：

- Request 被卡住
- Controller 永遠不會被執行