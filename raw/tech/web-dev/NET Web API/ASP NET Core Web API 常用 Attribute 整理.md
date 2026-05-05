# ASP.NET Core Web API 常用 Attribute 整理

## ASP.NET Core Web API 常用 Attribute 整理

---

### 1. Controller 層級

```csharp
[ApiController]
[Route("api/[controller]")]
public class RulesController : ControllerBase { }
```

| Attribute | 作用 |
| --- | --- |
| `[ApiController]` | 啟用自動 Model 驗證、自動 400 回應、推斷參數來源 |
| `[Route("api/[controller]")]` | 設定路由前綴，`[controller]` 會自動替換為 class 名稱 |

---

### 2. HTTP 動詞

```csharp
[HttpGet]
[HttpGet("{id}")]
[HttpPost]
[HttpPut("{id}")]
[HttpDelete("{id}")]
[HttpPatch("{id}")]
```

也可以串接子路徑：

```csharp
[HttpGet("search/by-name/{name}")]
public ActionResult Search(string name) { ... }
// GET /api/rules/search/by-name/abc
```

---

### 3. 參數來源

```csharp
public ActionResult Create(
    [FromBody] RuleDto dto,        // 從 request body (JSON)
    [FromQuery] string filter,     // 從 ?filter=xxx
    [FromRoute] int id,            // 從 URL /api/rules/123
    [FromHeader] string token,     // 從 request header
    [FromForm] IFormFile file      // 從 form-data (上傳檔案)
)
```

> 加了 `[ApiController]` 之後，多數情況 [ASP.NET](http://ASP.NET) Core 會自動推斷參數來源，不需要手動標註；但明確寫出來會更好讀。
> 

---

### 4. 回應格式宣告

```csharp
[Produces("application/json")]
[ProducesResponseType(StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
[ProducesResponseType(typeof(RuleDto), StatusCodes.Status201Created)]
public ActionResult<RuleDto> GetRule(string name) { ... }
```

這些主要是給 **Swagger / OpenAPI** 使用的，讓文件更完整，對實際執行沒有影響。

---

### 5. 授權與認證

```csharp
[Authorize]                          // 需要登入
[Authorize(Roles = "Admin")]         // 需要特定 Role
[Authorize(Policy = "CanEditRule")]  // 需要符合 Policy
[AllowAnonymous]                     // 開放給未登入的人
```

---

### 6. CORS

```csharp
[EnableCors("MyPolicy")]    // 套用指定 CORS 政策
[DisableCors]               // 關閉這個 action 的 CORS
```

---

### 7. 快取與限流

```csharp
[ResponseCache(Duration = 60)]        // 回應快取 60 秒
[RequestSizeLimit(1_000_000)]         // 限制 request body 大小 (bytes)
[RequestFormLimits(MultipartBodyLengthLimit = 5_000_000)]
```

---

### 8. 過濾與行為控制

```csharp
[IgnoreAntiforgeryToken]    // 忽略 CSRF token 驗證 (API 通常不需要)
[NonAction]                 // 這個 public 方法不是 API endpoint
[ActionName("Rename")]      // 給這個 action 取別名
[ApiExplorerSettings(IgnoreApi = true)]  // 不出現在 Swagger 文件
```

---

### 組合範例

```csharp
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class RulesController : ControllerBase
{
    [HttpGet("{ruleName}")]
    [AllowAnonymous]
    [ProducesResponseType(typeof(IEnumerable<RTDRuleBlock>), 200)]
    [ProducesResponseType(404)]
    public ActionResult<IEnumerable<RTDRuleBlock>> GetRule(string ruleName)
    {
        ...
    }
}
```

---

### 優先順序提醒

當 Controller 和 Action 都有同一個 Attribute 時，**Action 層級優先**。例如上面 Controller 有 `[Authorize]`，但 `GetRule` 有 `[AllowAnonymous]`，結果是這個 endpoint 不需要登入。