# Authentication / Authorization Pipeline

這一節的目標是：

**讓你能精準回答這三個問題**

1. `UseAuthentication` 與 `UseAuthorization` 真正差在哪
2. 為什麼順序錯一行，整個系統就壞
3. `[Authorize]` 到底是「在哪一層」生效的

內容會完全對齊 **ASP.NET Core Web API 實務**，並預設你未來會加 JWT。

## 一、先給結論（非常重要）

### Pipeline 中的正確順序只有一種

```csharp
app.UseAuthentication(); // 身分
app.UseAuthorization(); // 權限
```

**不能交換，不能省略其中一個**

## 二、Authentication vs Authorization 的本質差異

| 項目 | Authentication | Authorization |
| --- | --- | --- |
| 問的問題 | 你是誰 | 你能不能做 |
| 產出 | `HttpContext.User` | Allow / Deny |
| 是否依賴對方 | ❌ 不依賴 | ✅ 依賴 |
| 常見實作 | JWT / Cookie / OAuth | Role / Policy / Claim |

> Authentication 建立身分，Authorization 使用身分做判斷
> 

## 三、`UseAuthentication()` 在 Pipeline 中實際做了什麼

### 1. 它做的事情只有一件

> 嘗試從 Request 中「解析身分」
> 

例如：

- `Authorization: Bearer eyJhbGciOiJI...`
- Cookie
- API Key Header

如果成功：

- 建立 `ClaimsPrincipal`
- 塞進 `HttpContext.User`

如果失敗：

- `HttpContext.User.Identity.IsAuthenticated == false`
- **不會丟 Exception**
- **不會阻擋 Request**

這一點非常關鍵。

### 2. Authentication 本身「不會拒絕請求」

這段話請牢記：

> Authentication 不負責擋人
> 

它只做「解析」，不做「判斷」。

## 四、`UseAuthorization()` 在 Pipeline 中實際做了什麼

### 1. Authorization 是「執法者」

`UseAuthorization()` 會：

- 檢查 Endpoint Metadata
- 查看是否有：
    - `[Authorize]`
    - `[Authorize(Roles = "...")]`
    - Policy

然後用 `HttpContext.User` 來判斷：

- 是否已登入
- 是否符合角色 / 權限

不符合就直接：

- 回傳 `401` 或 `403`
- **Controller 根本不會被執行**

---

### 2. Authorization 一定依賴 Authentication

如果你寫：

```csharp
app.UseAuthorization();
```

但沒有：

```csharp
app.UseAuthentication();
```

結果是：

- `HttpContext.User` 永遠是空的
- 所有 `[Authorize]` 都視為未登入
- 全部 API 變成 401

## 五、為什麼順序不能反

### 錯誤寫法

```csharp
app.UseAuthorization();
app.UseAuthentication();// ❌
```

### 實際發生的事

1. Authorization 執行
2. 發現 `HttpContext.User` 是空的
3. 判定未登入
4. 回傳 401
5. Authentication 根本沒機會跑

所以結論是：

> Authorization 永遠不會幫你做 Authentication
> 

---

## 六、`[Authorize]` 到底在哪一層生效

這是很多人誤解的地方。

### `[Authorize]` 不是 Controller 裡的 if 判斷

它是：

- **Endpoint Metadata**
- 被 `UseAuthorization()` Middleware 讀取

流程是：

```
Request
 ↓
UseAuthentication   → 建立 User
 ↓
UseAuthorization    → 讀取[Authorize]
 ↓
Controller Action   →（只有通過才會進來）
```

所以你在 Controller 裡寫：

```csharp
[Authorize]
public IActionResultGetRules()
{
    ...
}
```

其實代表：

> 「這個 Endpoint 在 Pipeline 的 Authorization 階段就可能被攔截」
> 

---

## 七、401 vs 403 的真正差別

| 狀態碼 | 意義 |
| --- | --- |
| 401 Unauthorized | 沒有登入或 Token 無效 |
| 403 Forbidden | 已登入但權限不足 |

實務上對應：

- 沒帶 JWT → 401
- JWT 正確但 Role 不符 → 403

---

## 八、對應到你未來的 RuleViewerBackend 設計

假設未來你要做：

- Public API：讀取 RuleViewer 規則
- Protected API：新增、修改、刪除規則

實務結構會是：

```csharp
app.UseAuthentication();
app.UseAuthorization();
```

Controller：

```csharp
[ApiController]
[Route("api/[controller]")]
public class RuleViewerController : ControllerBase
{
    [HttpGet]
    public IActionResult GetRules() { } // 公開

    [Authorize]
    [HttpPost]
    public IActionResult CreateRule() { } // 需登入
}

```

**Pipeline 不變，控制權限靠 Attribute**

---

## 九、這一節你應該確實掌握的判斷力

你現在應該能做到：

- 看到 `Program.cs` 就知道 Auth 有沒有寫錯
- 知道 `[Authorize]` 為什麼「不寫也能跑」
- 知道為什麼 Swagger 常被 Auth 擋住
- 知道 401 與 403 的責任歸屬