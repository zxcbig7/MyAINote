---
type: concept
domain: tech
tags: [dotnet, aspnet, cheatsheet, reference, troubleshooting, snippets]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-15
updated: 2026-08-15
---

# 附錄 B：速查表

出事時第二螢幕開著的那一份。正文回答「為什麼」，這裡只回答「怎麼做」與「先查哪裡」。

---

## 一、緊急排錯十連發

| # | 症狀 | 先查這裡 | 章 |
| --- | --- | --- | --- |
| 1 | CPU 低但請求全部逾時 | 搜尋 `.Result` / `.Wait()` / `GetAwaiter().GetResult()` | 06 |
| 2 | Pod 反覆重啟、log 空的 | `kubectl describe pod` 看事件；查 `ExecuteAsync` 開頭的同步阻塞 | 00/19 |
| 3 | Service 通不了但 Pod 內 curl 正常 | `ASPNETCORE_URLS` 是不是 `localhost`（要用 `+` 或 `0.0.0.0`） | 00 |
| 4 | 列表 API 很慢、DB 慢查詢是空的 | 打開 SQL log 數**條數** → N+1 | 08 |
| 5 | 401 在瀏覽器變成 CORS 錯誤 | `UseCors` 是否排在 `UseAuthorization` 之後 | 01 |
| 6 | POST 進來的 DTO 是 null | Content-Type / `[ApiController]` / 有無 middleware 讀走 body | 04 |
| 7 | 改了 ConfigMap 沒生效 | env 注入不可能熱重載，要 volume 掛載 | 17 |
| 8 | OAuth 無限重導向 | 缺 `UseForwardedHeaders`，scheme 被判成 http | 13 |
| 9 | 記憶體緩慢上升、壓測測不出 | root provider 解析 `IDisposable` Transient；`CreateScope` 沒 `using` | 02 |
| 10 | 滾動更新掉請求 | 加 `preStop: sleep 10`；確認 `terminationGracePeriodSeconds` 夠大 | 00 |

### 診斷指令

```powershell
# ThreadPool 飢餓確認（看 Queue Length 是否長期不為零）
dotnet-counters monitor -p <pid> --counters System.Runtime

# 記憶體與 GC
dotnet-counters monitor -p <pid> --counters System.Runtime[dotnet.gc.heap.size]
dotnet-gcdump collect -p <pid>

# 卡住時抓堆疊
dotnet-stack report -p <pid>

# K8s
kubectl describe pod <pod>              # 事件比 log 更早揭露 probe 問題
kubectl logs <pod> --previous           # 上一個容器的 log（重啟前）
kubectl exec -it <pod> -- sh
```

---

## 二、`Program.cs` 骨架

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Host.UseDefaultServiceProvider(o =>
{
    o.ValidateScopes = true;
    o.ValidateOnBuild = true;
});

builder.Services.Configure<HostOptions>(o => o.ShutdownTimeout = TimeSpan.FromSeconds(30));

// 設定（含啟動時驗證）
builder.Services.AddOptions<JwtOptions>()
    .Bind(builder.Configuration.GetSection("Jwt"))
    .ValidateDataAnnotations()
    .ValidateOnStart();

// 資料
builder.Services.AddDbContext<AppDbContext>(o =>
    o.UseOracle(builder.Configuration.GetConnectionString("Default")));

// 認證授權
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(o => { /* 見第四節 */ });

builder.Services.AddAuthorization(o =>
{
    o.FallbackPolicy = new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build();
});

// 韌性
builder.Services.AddHttpClient<IPaymentClient, PaymentClient>(c =>
{
    c.BaseAddress = new Uri(builder.Configuration["Services:Payment"]!);
    c.Timeout = TimeSpan.FromSeconds(10);
}).AddStandardResilienceHandler();

// 可觀測性
builder.Logging.ClearProviders();
builder.Logging.AddJsonConsole(o => { o.IncludeScopes = true; o.UseUtcTimestamp = true; });
builder.Services.AddHealthChecks().AddDbContextCheck<AppDbContext>(tags: ["ready"]);
builder.Services.AddProblemDetails();

builder.Services.AddControllers();
builder.Services.AddHttpContextAccessor();

var app = builder.Build();

app.UseForwardedHeaders();          // 反向代理後面時必須最前面
app.UseExceptionHandler();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseRouting();
app.UseCors("Frontend");
app.UseAuthentication();
app.UseAuthorization();
app.UseRateLimiter();

app.MapControllers();
app.MapHealthChecks("/healthz/live", new() { Predicate = _ => false }).AllowAnonymous();
app.MapHealthChecks("/healthz/ready", new() { Predicate = c => c.Tags.Contains("ready") })
   .AllowAnonymous();

app.Run();
```

### Middleware 順序（記這個順序就好）

```text
UseForwardedHeaders   → 最前面，其他人才看得到正確的 scheme
UseExceptionHandler   → 要包住下面全部
UseHsts / UseHttpsRedirection  → TLS 終結在 Ingress 時不要開
UseStaticFiles        → 早點短路
UseRouting            → 選出 endpoint
UseCors               → 需要 endpoint metadata，且要在 Authorization 前
UseAuthentication     → 填 HttpContext.User
UseAuthorization      → 需要 User + endpoint metadata
UseRateLimiter
MapControllers        → 終點
```

---

## 三、DI 生命週期決策

| 服務 | Lifetime |
| --- | --- |
| `DbContext`、Repository、業務 Service | Scoped |
| 無狀態工具、快取、`IOptions<T>` | Singleton |
| 記錄「當前使用者」 | Scoped（**絕不** Singleton） |
| `BackgroundService` | Singleton（用 `IServiceScopeFactory` 拿 Scoped） |
| 需要 DbContext 的 `IAuthorizationHandler` | Scoped |
| 需要 DbContext 的 Filter | Scoped + `[ServiceFilter]` |
| Typed `HttpClient` | 框架管（Transient） |

```csharp
// Singleton 裡要用 Scoped 服務
using var scope = _scopeFactory.CreateScope();          // using 不能少
var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();

// Middleware 的 Scoped 依賴放這裡，不要放建構子
public async Task InvokeAsync(HttpContext ctx, IUserService svc)
```

---

## 四、認證授權速查

```csharp
options.TokenValidationParameters = new TokenValidationParameters
{
    ValidateIssuer = true,             // 四個 Validate 全部 true
    ValidateAudience = true,
    ValidateLifetime = true,
    ValidateIssuerSigningKey = true,
    ValidIssuer = cfg["Jwt:Issuer"],
    ValidAudience = cfg["Jwt:Audience"],
    IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(cfg["Jwt:Key"]!)),
    ClockSkew = TimeSpan.FromSeconds(30),   // 預設 5 分鐘，一定要改
    NameClaimType = "name",
    RoleClaimType = "role"                  // 與簽發端一致，否則 Roles 檢查失效
};
options.MapInboundClaims = false;           // 讓 FindFirst("sub") 拿得到值
```

| 需求 | 用什麼 |
| --- | --- |
| 固定角色 | `[Authorize(Roles = "Admin")]`（逗號=OR，兩個 attribute=AND） |
| 條件組合 | `[Authorize(Policy = "...")]` + Requirement/Handler |
| **依資料內容判斷** | `IAuthorizationService.AuthorizeAsync(User, resource, req)` |
| 全域預設關閉 | `options.FallbackPolicy = ...RequireAuthenticatedUser()` |
| 開放例外 | `[AllowAnonymous]`（優先權高於一切） |

| 回應 | 時機 |
| --- | --- |
| `Unauthorized()` 401 | 沒表明身分 / token 無效 |
| `Forbid()` 403 | 已認證但權限不足 |
| `NotFound()` 404 | 敏感資源，不揭露存在性 |

---

## 五、EF Core 速查

```csharp
// 唯讀查詢 —— 首選投影
await _db.Orders
    .Where(o => o.Status == status)
    .Select(o => new OrderDto(o.Id, o.Customer.Name, o.Items.Count(), o.Total))
    .ToListAsync(ct);

// 需要完整實體但不改
await _db.Orders.AsNoTracking().ToListAsync(ct);

// 多個集合導覽
await _db.Orders.Include(o => o.Items).Include(o => o.Payments)
    .AsSplitQuery().ToListAsync(ct);

// 分頁（排序鍵必須唯一）
.OrderByDescending(o => o.CreatedAt).ThenByDescending(o => o.Id)
.Skip((page - 1) * size).Take(size)

// 原子更新（避免 read-modify-write 競爭）
await _db.Tickets.Where(t => t.Id == id && t.Remaining > 0)
    .ExecuteUpdateAsync(s => s.SetProperty(t => t.Remaining, t => t.Remaining - 1), ct);

// 原生 SQL（插值版會自動參數化，安全）
await _db.Users.FromSql($"SELECT * FROM USERS WHERE DEPT_ID = {deptId}").ToListAsync(ct);

// 看產生的 SQL
var sql = query.ToQueryString();
// 看追蹤狀態
_db.ChangeTracker.DebugView.LongView
```

| 要做 | 怎麼做 |
| --- | --- |
| 更新單一欄位 | `FindAsync` 查出來改，**不要** `Update()` |
| 批次插入 | `AddRange` + 一次 `SaveChanges` |
| 並行查兩張表 | `IDbContextFactory` 建兩個 context |
| 大量匯出 | 回傳 `IAsyncEnumerable<T>` |
| 跨多次 SaveChanges | `await using var tx = await db.Database.BeginTransactionAsync(ct)` |

### Oracle 特有

```csharp
// 表名欄位名統一大寫（否則產生帶引號的混合大小寫）
e.ToTable("ORDERS");
e.Property(x => x.CreatedAt).HasColumnName("CREATED_AT");

// 金額務必指定精度
e.Property(o => o.Total).HasPrecision(18, 2);

// 並發控制（Oracle 沒有 [Timestamp]）
e.Property(x => x.Version).IsConcurrencyToken();

// CHAR(1) 的 Y/N 轉 bool
e.Property(u => u.IsActive).HasConversion(v => v ? "Y" : "N", v => v == "Y");
```

| 坑 | 記住 |
| --- | --- |
| 空字串 | 等同 `NULL` |
| `IN` 清單 | 上限 1000，用 `Chunk(1000)` 分批 |
| 字串比對 | 預設大小寫敏感 |
| 識別碼長度 | 12.2 之前上限 30 字元 |
| DDL | 隱含提交，migration 失敗無法整段回滾 |

---

## 六、HTTP 狀態碼

| 碼 | 用在 |
| --- | --- |
| 200 / 201 / 204 | 成功 / 建立（附 `Location`）/ 無內容 |
| 400 | 請求本身有問題（格式、缺欄位） |
| 401 / 403 | 未認證 / 權限不足 |
| 404 / 405 / 409 | 不存在 / 方法不支援 / 衝突（重複、並發） |
| 422 | 格式正確但違反業務規則 |
| 429 | 超過流量限制（附 `Retry-After`） |
| 500 / 502 / 503 / 504 | 內部錯誤 / 下游失敗 / 不可用 / 下游逾時 |

**4xx 不告警，5xx 要告警。** 分錯會造成告警疲勞或事故被埋沒。

---

## 七、Dockerfile 與 Deployment

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["src/MyApp.Api/MyApp.Api.csproj", "src/MyApp.Api/"]
RUN dotnet restore "src/MyApp.Api/MyApp.Api.csproj"     # 先 restore 再 copy
COPY . .
RUN dotnet publish "src/MyApp.Api/MyApp.Api.csproj" -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
RUN adduser --disabled-password --gecos "" --uid 1000 appuser
USER appuser
COPY --from=build --chown=appuser:appuser /app/publish .
EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENTRYPOINT ["dotnet", "MyApp.Api.dll"]
```

```yaml
spec:
  strategy:
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    spec:
      terminationGracePeriodSeconds: 60      # > preStop + ShutdownTimeout
      containers:
        - name: api
          image: registry.example.com/myapp:1.2.3   # 明確版本，不用 latest
          ports: [{ containerPort: 8080 }]
          env:
            - { name: ASPNETCORE_ENVIRONMENT, value: "Production" }
            - { name: ASPNETCORE_URLS, value: "http://+:8080" }
            - name: ConnectionStrings__Default
              valueFrom: { secretKeyRef: { name: db-credentials, key: connection-string } }
          resources:
            requests: { memory: "256Mi", cpu: "200m" }
            limits:   { memory: "512Mi", cpu: "1000m" }
          startupProbe:
            httpGet: { path: /healthz/live, port: 8080 }
            failureThreshold: 30
            periodSeconds: 2
          livenessProbe:                     # 不檢查外部依賴
            httpGet: { path: /healthz/live, port: 8080 }
          readinessProbe:                    # 這裡才檢查資料庫
            httpGet: { path: /healthz/ready, port: 8080 }
          lifecycle:
            preStop: { exec: { command: ["sh", "-c", "sleep 10"] } }
          securityContext:
            runAsNonRoot: true
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
```

環境變數巢狀用 `__`：`Jwt__Key`、`ConnectionStrings__Default`。

---

## 八、常用套件

| 用途 | 套件 |
| --- | --- |
| Oracle | `Oracle.EntityFrameworkCore` |
| 輕量查詢 / 預存程序 | `Dapper` |
| 驗證 | `FluentValidation.AspNetCore` |
| 韌性（.NET 8） | `Microsoft.Extensions.Http.Resilience` |
| 分散式快取 | `Microsoft.Extensions.Caching.StackExchangeRedis` |
| 背景工作 | `Hangfire.AspNetCore` |
| 可觀測性 | `OpenTelemetry.Extensions.Hosting` + `.Instrumentation.AspNetCore` |
| 健康檢查 | `AspNetCore.HealthChecks.*` |
| API 版本 | `Asp.Versioning.Mvc` |
| 測試 | `Microsoft.AspNetCore.Mvc.Testing`、`Testcontainers.Oracle`、`Respawn` |
| 假時間 | `Microsoft.Extensions.TimeProvider.Testing` |

## 九、常用指令

```powershell
# EF Core
dotnet ef migrations add <Name> -p src/MyApp.Infrastructure -s src/MyApp.Api
dotnet ef migrations script --idempotent -o migrate.sql
dotnet ef database update
dotnet ef dbcontext scaffold "<conn>" Oracle.EntityFrameworkCore -o Entities

# User Secrets（本機機密，絕不進版控）
dotnet user-secrets init
dotnet user-secrets set "ConnectionStrings:Default" "<conn>"

# 測試
dotnet test --collect:"XPlat Code Coverage"
```

---

## 連結

- [[dotnet-web-api]] — 教材總目錄
- [[22-self-assessment]] — 附錄 A：自我檢測題庫
- [[k8s-mastery]] — K8s 端的速查與教材
