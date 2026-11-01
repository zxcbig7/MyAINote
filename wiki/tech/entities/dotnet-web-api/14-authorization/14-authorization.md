---
type: concept
domain: tech
tags: [dotnet, aspnet, authorization, policy, requirement, rbac, multi-tenancy]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 14 章：授權 — 從 `[Authorize(Roles = "Admin")]` 到真正的權限模型

## 一個 attribute 表達不了的需求

```csharp
[Authorize(Roles = "Admin")]
[HttpDelete("{id}")]
public async Task<IActionResult> DeleteOrderAsync(int id)
```

這行程式碼能表達「只有管理員能刪除訂單」。但真實的需求通常是這樣的：

> 管理員可以刪除任何訂單；一般使用者只能刪除**自己的**訂單，而且只有在訂單**還沒出貨**的情況下；客服人員可以刪除**自己負責的客戶**的訂單，不限狀態。

沒有任何 attribute 能表達這件事。原因很根本：**這個判斷需要知道「哪一筆訂單」，而授權 filter 跑在 model binding 之前、資料庫查詢之前**（第 05 章）。

這一章要解決的就是「從屬性標記走到真正的權限模型」這條路。

---

## 一、三種授權模型

### 1.1 Role-based

```csharp
[Authorize(Roles = "Admin")]
[Authorize(Roles = "Admin,Manager")]      // 逗號是 OR：其中一個即可
```

多個 attribute 疊加則是 AND：

```csharp
[Authorize(Roles = "Admin")]
[Authorize(Roles = "Auditor")]            // 必須同時是 Admin 且 Auditor
```

角色來自 claim，用哪個 claim 由 `RoleClaimType` 決定（第 11 章的常見坑）。

Role-based 的問題在於**角色與權限被綁死在程式碼裡**。今天業務說「客服也要能退款」，你得改程式碼、重新編譯、重新部署。角色一多，散落在幾百個 action 上的字串就變成維護惡夢——沒有人說得出「Manager 這個角色到底能做哪些事」，只能全域搜尋。

### 1.2 Claims-based

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("HasDepartment", policy =>
        policy.RequireClaim("department"));

    options.AddPolicy("FinanceOnly", policy =>
        policy.RequireClaim("department", "Finance", "Accounting"));
});

[Authorize(Policy = "FinanceOnly")]
```

比角色細緻一點，但本質仍是「檢查某個 claim 的值」。

### 1.3 Policy-based：真正的抽象

這是 ASP.NET Core 的統一模型——**上面兩種其實都是 policy 的特例**。`[Authorize(Roles = "Admin")]` 內部會被轉成一個要求「role claim 包含 Admin」的 policy。

Policy 由一或多個 **requirement** 組成，每個 requirement 由一或多個 **handler** 評估：

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("CanApproveExpense", policy =>
    {
        policy.RequireAuthenticatedUser();
        policy.RequireClaim("department", "Finance");
        policy.Requirements.Add(new MinimumApprovalLimitRequirement(10000));
    });
});
```

Policy 的價值在於**把「什麼條件」與「哪些 action 需要它」分離**。業務規則變了改一個地方，不用去動幾百個 attribute。

---

## 二、Requirement 與 Handler

一個自訂 requirement 的完整實作：

```csharp
// 1. Requirement：只是一個資料載體，描述「要求什麼」
public class MinimumAgeRequirement : IAuthorizationRequirement
{
    public int MinimumAge { get; }
    public MinimumAgeRequirement(int minimumAge) => MinimumAge = minimumAge;
}

// 2. Handler：實際評估邏輯
public class MinimumAgeHandler : AuthorizationHandler<MinimumAgeRequirement>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        MinimumAgeRequirement requirement)
    {
        var birthDateClaim = context.User.FindFirst("birthdate");
        if (birthDateClaim is null)
        {
            return Task.CompletedTask;      // 不呼叫 Succeed，視為未通過
        }

        var birthDate = DateTimeOffset.Parse(birthDateClaim.Value);
        var age = (DateTimeOffset.UtcNow - birthDate).Days / 365;

        if (age >= requirement.MinimumAge)
        {
            context.Succeed(requirement);   // 明確標記通過
        }

        return Task.CompletedTask;
    }
}

// 3. 註冊
builder.Services.AddSingleton<IAuthorizationHandler, MinimumAgeHandler>();

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("Adult", policy =>
        policy.Requirements.Add(new MinimumAgeRequirement(18)));
});
```

### 2.1 三個關鍵語意

**不呼叫 `Succeed` 就是不通過。** Handler 沒有「拒絕」的預設動作——它只能主動標記通過。什麼都不做等於保持未通過狀態。這是「預設拒絕」的安全設計。

**`context.Fail()` 是硬性否決。** 一旦呼叫，即使其他 handler 呼叫了 `Succeed` 也無法挽回。用於「這個條件絕對不能違反」的場景（例如帳號被停權）。

**同一個 requirement 有多個 handler 時是 OR 語意。** 任一個呼叫 `Succeed` 就算通過：

```csharp
// 兩種方式都能通過「編輯文件」的要求
builder.Services.AddSingleton<IAuthorizationHandler, DocumentOwnerHandler>();  // 我是作者
builder.Services.AddSingleton<IAuthorizationHandler, DocumentAdminHandler>();  // 我是管理員
```

這個特性很好用——新增一種「也可以通過」的途徑時，只要多寫一個 handler，完全不用動既有邏輯。

**一個 policy 裡的多個 requirement 是 AND 語意。** 全部都要被滿足。

### 2.2 Handler 的生命週期

上面註冊成 Singleton。如果 handler 需要 DbContext（要查資料庫判斷權限），就必須註冊成 Scoped：

```csharp
builder.Services.AddScoped<IAuthorizationHandler, DocumentOwnerHandler>();
```

否則就是第 02 章的 captive dependency。這是實務上很容易漏掉的一點——教學文件多半用 Singleton 示範，抄過來加上 DbContext 就出事。

---

## 三、Resource-based Authorization：開頭那個需求的解法

當判斷需要「那筆資料本身」時，授權必須發生在資料載入之後——也就是在 action 內部：

```csharp
public class OrderAuthorizationHandler
    : AuthorizationHandler<OperationAuthorizationRequirement, Order>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        OperationAuthorizationRequirement requirement,
        Order resource)                                    // ← 資源本身
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (requirement.Name == "Delete")
        {
            if (context.User.IsInRole("Admin"))
            {
                context.Succeed(requirement);
            }
            else if (resource.CustomerId.ToString() == userId
                     && resource.Status == OrderStatus.Pending)
            {
                context.Succeed(requirement);
            }
        }

        return Task.CompletedTask;
    }
}
```

在 action 裡呼叫：

```csharp
[HttpDelete("{id}")]
[Authorize]                                   // 先確保已登入
public async Task<IActionResult> DeleteAsync(int id, CancellationToken ct)
{
    var order = await _db.Orders.FindAsync(new object[] { id }, ct);
    if (order is null) return NotFound();

    var result = await _authorizationService.AuthorizeAsync(
        User, order, new OperationAuthorizationRequirement { Name = "Delete" });

    if (!result.Succeeded)
    {
        return Forbid();                      // 403，不是 401
    }

    _db.Orders.Remove(order);
    await _db.SaveChangesAsync(ct);
    return NoContent();
}
```

`IAuthorizationService` 從 DI 注入。這個模式的價值是**權限邏輯仍然集中在 handler 裡**，action 只負責「載入資源 → 詢問 → 回應」，而不是散落一堆 `if (order.CustomerId != userId)`。

### 3.1 `Forbid()` 與 `Unauthorized()` 的選擇

```csharp
return Forbid();          // 403：我知道你是誰，但你不能做這件事
return Unauthorized();    // 401：你沒表明身分（或身分無效）
```

已經通過 `[Authorize]` 進到 action，代表使用者已認證。此時權限不足應該回 **403**（第 11 章）。回 401 會讓前端誤以為要重新登入，形成登入迴圈。

### 3.2 洩漏資訊的取捨

回 403 等於告訴對方「這筆資料存在，只是你不能碰」。對敏感資源（例如其他使用者的私人文件），回 **404** 反而更安全——不揭露資源是否存在。

這是安全性與可用性的取捨，需要按資源類型決定。訂單編號這種可枚舉的識別碼尤其值得考慮回 404。

---

## 四、全域預設：讓「忘記加 `[Authorize]`」不再是漏洞

最危險的授權缺陷往往不是邏輯寫錯，而是**忘記寫**。新增一個 controller、忘記加 `[Authorize]`，它就對全世界開放，而且沒有任何警告。

解法是把預設反過來——**全域要求授權，明確開放例外**：

```csharp
builder.Services.AddAuthorization(options =>
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser()
        .Build();
});
```

`FallbackPolicy` 的語意是：**沒有任何授權設定的 endpoint，套用這個 policy**。從此忘記寫 `[Authorize]` 的 endpoint 預設是關閉的，而不是開放的。

需要公開的端點明確標記：

```csharp
[AllowAnonymous]
[HttpPost("auth/login")]
public async Task<IActionResult> LoginAsync(LoginDto dto)
```

**`[AllowAnonymous]` 的優先權高於一切**——包括 fallback policy、default policy、以及 controller 上的 `[Authorize]`。這是刻意的設計（登入端點必須能被未登入的人存取），但也意味著誤用它會直接開一個洞。Code review 時看到 `[AllowAnonymous]` 應該停下來想一下。

別忘記健康檢查端點：

```csharp
app.MapHealthChecks("/healthz").AllowAnonymous();
```

否則 K8s 的 probe 會拿到 401，Pod 被判定不健康而反覆重啟——一個因為授權設定造成的部署事故。

### 4.1 `DefaultPolicy` 與 `FallbackPolicy` 的差別

| | 何時套用 |
| --- | --- |
| `DefaultPolicy` | `[Authorize]` 沒指定 policy 時 |
| `FallbackPolicy` | endpoint 上**完全沒有**任何授權 metadata 時 |

修改 `DefaultPolicy` 會影響所有寫了 `[Authorize]` 的地方；`FallbackPolicy` 只影響什麼都沒寫的地方。要「全域預設需要登入」用 `FallbackPolicy`。

---

## 五、權限模型設計

Role-based 在系統長大之後會失控。比較能撐的做法是**分離角色與權限**：

```text
使用者 → 擁有多個角色 → 每個角色擁有多個權限（permission）
程式碼檢查的是 permission，不是 role
```

```csharp
// ❌ 角色寫死在程式碼裡，業務調整就要改程式
[Authorize(Roles = "Admin,Manager,Supervisor")]
public IActionResult ApproveExpense() { }

// ✅ 檢查權限，角色與權限的對應是資料
[Authorize(Policy = "expense:approve")]
public IActionResult ApproveExpense() { }
```

Policy 可以動態產生，避免為每個權限手寫註冊：

```csharp
public class PermissionPolicyProvider : IAuthorizationPolicyProvider
{
    private readonly DefaultAuthorizationPolicyProvider _fallback;

    public PermissionPolicyProvider(IOptions<AuthorizationOptions> options)
    {
        _fallback = new DefaultAuthorizationPolicyProvider(options);
    }

    public Task<AuthorizationPolicy?> GetPolicyAsync(string policyName)
    {
        if (policyName.Contains(':'))          // 慣例：權限名稱含冒號
        {
            var policy = new AuthorizationPolicyBuilder()
                .AddRequirements(new PermissionRequirement(policyName))
                .Build();
            return Task.FromResult<AuthorizationPolicy?>(policy);
        }

        return _fallback.GetPolicyAsync(policyName);
    }

    public Task<AuthorizationPolicy> GetDefaultPolicyAsync() => _fallback.GetDefaultPolicyAsync();
    public Task<AuthorizationPolicy?> GetFallbackPolicyAsync() => _fallback.GetFallbackPolicyAsync();
}

builder.Services.AddSingleton<IAuthorizationPolicyProvider, PermissionPolicyProvider>();
```

Handler 則去查這個使用者實際擁有的權限：

```csharp
public class PermissionHandler : AuthorizationHandler<PermissionRequirement>
{
    private readonly IPermissionService _permissions;      // Scoped，會查資料庫

    protected override async Task HandleRequirementAsync(
        AuthorizationHandlerContext context, PermissionRequirement requirement)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (userId is null) return;

        if (await _permissions.HasAsync(userId, requirement.Permission))
        {
            context.Succeed(requirement);
        }
    }
}
```

**這裡一定要加快取。** 每個請求查一次資料庫的權限表，在高流量下會成為瓶頸。用 `IMemoryCache` 或分散式快取，以使用者為鍵，設定合理的 TTL（例如 5 分鐘）。權限變更時主動清除該使用者的快取。

這個模型的好處：新增權限不用改程式碼、角色與權限的對應可以在後台調整、能回答「這個角色到底能做什麼」這個問題。

---

## 六、多租戶

SaaS 系統最重要的授權規則往往是「使用者只能看到自己租戶的資料」。這條規則如果靠每個查詢自己記得加條件，遲早會有人忘記——而那是一次跨租戶的資料外洩。

比較可靠的做法是用 EF Core 的**全域查詢篩選器**：

```csharp
public class AppDbContext : DbContext
{
    private readonly ICurrentUserService _currentUser;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Order>()
            .HasQueryFilter(o => o.TenantId == _currentUser.TenantId);

        modelBuilder.Entity<Customer>()
            .HasQueryFilter(c => c.TenantId == _currentUser.TenantId);
    }
}
```

之後所有對 `Orders` 的查詢都會自動帶上 `WHERE TENANT_ID = :p0`，包括 `Include` 進來的關聯。忘記寫條件也不會洩漏。

三個注意事項：

**`IgnoreQueryFilters()` 能繞過它。** 管理後台需要跨租戶查詢時用得上，但每個使用點都是潛在的漏洞，應該集中管理並加註解。

**寫入端不受保護。** 查詢篩選器只影響讀取。新增資料時仍要自己設定 `TenantId`，可以在 `SaveChanges` 覆寫裡統一處理。

**DbContext pooling 不能用。** 這個 DbContext 依賴 `ICurrentUserService`（request 範圍的狀態），第 07 章講過池化會讓實例跨請求重用——那會導致 A 租戶的請求用到 B 租戶的篩選條件。這是嚴重的資料外洩，必須避免。

---

## 七、常見誤解

**「授權就是 `[Authorize(Roles = "...")]`。」**
那只是最基本的形態。需要根據資料內容判斷（「只能改自己的」）時，attribute 完全表達不了，必須用 resource-based authorization。

**「Handler 裡要呼叫 `Fail()` 來拒絕。」**
不用。不呼叫 `Succeed` 就是未通過。`Fail()` 是硬性否決——連其他 handler 的 `Succeed` 都會被推翻，只在「絕對不能違反」時使用。

**「權限不足應該回 401。」**
已認證但權限不足是 403。回 401 會讓前端誤判為需要重新登入，造成登入迴圈。敏感資源可以考慮回 404 以免洩漏存在性。

**「忘記加 `[Authorize]` 的話，review 時會發現。」**
不會，那正是最容易漏掉的東西。設定 `FallbackPolicy` 讓預設變成「需要登入」，並明確用 `[AllowAnonymous]` 開放例外。

**「權限檢查放在 handler 裡查資料庫會很慢。」**
所以要加快取。但不要因此把整份權限清單塞進 JWT——那會讓 token 膨脹，而且權限變更要等 token 過期才生效（第 12 章）。

**「多租戶只要每個查詢記得加 `WHERE TenantId = x` 就好。」**
遲早有人會忘記，而後果是跨租戶資料外洩。用全域查詢篩選器，讓「忘記」不再可能。注意這樣就不能用 DbContext pooling。

---

## 八、同事會來問你的問題

**Q：「使用者只能刪除自己的訂單」怎麼寫？**
Attribute 做不到，因為授權 filter 跑在資料載入之前。用 resource-based authorization：action 裡先載入訂單，再呼叫 `IAuthorizationService.AuthorizeAsync(User, order, requirement)`，失敗回 `Forbid()`。

**Q：Handler 註冊成 Singleton 還是 Scoped？**
不需要 DI 服務的用 Singleton；需要查資料庫（注入 DbContext 或 repository）的必須用 Scoped，否則是 captive dependency。

**Q：怎麼確保沒有 endpoint 忘記加授權？**
設定 `AuthorizationOptions.FallbackPolicy` 要求已認證使用者。這讓預設變成關閉，公開端點必須明確標 `[AllowAnonymous]`。記得健康檢查端點要開放，否則 K8s probe 會拿到 401。

**Q：角色越加越多，快管不動了。**
把角色與權限分離：程式碼檢查權限（`expense:approve`），角色與權限的對應存在資料庫由後台維護。用自訂 `IAuthorizationPolicyProvider` 動態產生 policy，避免手寫幾百個註冊。記得加快取。

**Q：`[Authorize(Roles = "A,B")]` 和寫兩個 attribute 有什麼差別？**
逗號分隔是 OR（其中一個角色即可）；疊兩個 attribute 是 AND（兩個角色都要有）。

**Q：多租戶怎麼確保不會查到別人的資料？**
用 EF Core 的 `HasQueryFilter` 全域篩選 `TenantId`。注意寫入端要另外處理，且這個 DbContext 不能用 pooling——池化會讓租戶上下文跨請求殘留。

**Q：權限檢查要不要放進 JWT？**
少量角色可以，完整權限清單不要。token 會膨脹、payload 可讀、而且權限變更要等過期才生效。放使用者識別碼，權限即時查並快取。

---

## 連結

- [[basics-12-jwt-login]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[basics-13-permissions-with-frontend]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[13-oauth-oidc]] — 上一章：取得身分
- [[15-error-handling]] — 下一章：401/403 之外的錯誤處理
- [[11-authentication]] — 401 與 403 的分界
- [[05-filters-and-mvc-internals]] — 為什麼 authorization filter 拿不到資料
- [[07-efcore-internals]] — 全域查詢篩選器與 pooling 的衝突
