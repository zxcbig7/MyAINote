---
type: concept
domain: tech
tags: [python, fastapi, dotnet, aspnetcore, comparison, migration, reference]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 B：ASP.NET Core ↔ FastAPI 完整對照

這一份給兩種人用：要讀懂一份 FastAPI 程式碼的 .NET 開發者，以及要把一個 ASP.NET Core 服務搬到 FastAPI 的人。

前半是翻譯表，後半是「**看起來一樣其實不一樣**」清單——那才是真正會出事的地方。

---

## 一、三個世界觀差異

在查任何對照表之前，先接受這三件事。它們不是 API 的差別，是設計哲學的差別，其他所有差異都從這裡長出來。

### 差異一：型別在什麼時候起作用

**C#**：型別在編譯期就存在且被強制。執行期的 model binding 拿得到型別資訊是天經地義的，因為那是組件的中繼資料。

**Python**：型別提示預設**被直譯器完全忽略**，只存在 `__annotations__` 這個字典裡。FastAPI 主動去讀它，然後用 Pydantic 建出執行期的驗證器。

實務後果：型別只在 FastAPI 管轄的邊界上生效（path operation 的參數、`response_model`）。你自己寫的一般函式標了 `x: int` 傳字串進去，沒有任何錯誤。

### 差異二：依賴是註冊的還是宣告的

**ASP.NET Core**：`builder.Services.AddScoped<IFoo, Foo>()` 集中註冊，`Build()` 那一刻建出依賴圖並驗證。缺註冊在**啟動時**就會炸。

**FastAPI**：沒有註冊表。`Depends(get_foo)` 直接指向函式，依賴圖在**每個 request 現場解析**。寫錯的依賴要等到那條路由被呼叫才會發現。

實務後果：FastAPI 的測試覆蓋率比 .NET 更重要——沒被測到的 endpoint，你不知道它的依賴鏈是否成立。

### 差異三：誰在吸收阻塞

**ASP.NET Core**：ThreadPool 有很多執行緒且會自動長大。一段同步阻塞只是佔住一條執行緒，服務整體還在動。**框架替你吸收了大部分錯誤。**

**FastAPI**：一個 worker 只有一條 event loop 執行緒。`async def` 裡的一次同步阻塞會讓**整個程序**停止回應。

實務後果：這是本教材最重要的一句話——**在 FastAPI 裡，用 `async def` 包住同步程式碼比用 `def` 危險得多**。C# 的 `async` 是加了沒壞處，Python 這裡加了會炸。

---

## 二、逐項對照

### 啟動與 Host

| ASP.NET Core | FastAPI |
| --- | --- |
| `WebApplication.CreateBuilder(args)` | `app = FastAPI()` |
| `builder.Build()`（凍結設定） | 沒有對應——設定是 import 時逐步累積的 |
| `app.Run()` | `uvicorn app.main:app` |
| Kestrel | Uvicorn（可換 hypercorn、granian） |
| `IHostApplicationLifetime` | `lifespan` context manager |
| `IHostedService` / `BackgroundService` | `lifespan` 裡 `asyncio.create_task`，或外部佇列 |
| `appsettings.json` | `.env` + 環境變數 |

### 路由

| ASP.NET Core | FastAPI |
| --- | --- |
| `[HttpGet("/x")]` | `@app.get("/x")` |
| Controller 類別 | `APIRouter`（或就是一堆函式） |
| `[Route("api/[controller]")]` | `APIRouter(prefix="/api/users")` |
| `{id:int}` 路由約束 | `item_id: int`（型別即約束） |
| `{**slug}` catch-all | `{file_path:path}` |
| **優先序演算法**（字面優先於參數） | **宣告順序**（由上往下第一個匹配） |
| `MapGroup("/x").RequireAuthorization()` | `APIRouter(prefix="/x", dependencies=[...])` |

### 參數與驗證

| ASP.NET Core | FastAPI |
| --- | --- |
| `[FromRoute]` | 名稱出現在路徑模板中 |
| `[FromQuery]` | 單純型別且不在路徑中 |
| `[FromBody]` | 型別是 Pydantic model |
| `[FromHeader]` | `Annotated[str, Header()]` |
| `[FromForm]` | `Annotated[str, Form()]` |
| DTO + DataAnnotations | Pydantic `BaseModel` + `Field` |
| `[Required]` | 不給預設值 |
| `[StringLength(50)]` | `Field(max_length=50)` |
| `[Range(1, 100)]` | `Field(ge=1, le=100)` |
| `IValidatableObject` / FluentValidation | `@model_validator(mode="after")` |
| ModelState 失敗 → **400** | `RequestValidationError` → **422** |
| `[ApiController]` 自動驗證 | 預設就是自動的 |

### DI

| ASP.NET Core | FastAPI |
| --- | --- |
| `AddSingleton<T>` | `@lru_cache` 工廠 / `lifespan` + `app.state` |
| `AddScoped<T>` | 一般 `Depends(f)`（依賴快取讓它一 request 一份） |
| `AddTransient<T>` | `Depends(f, use_cache=False)` |
| 建構式注入 | 函式參數 `Annotated[T, Depends(f)]` |
| `IServiceScope` / `CreateScope()` | 沒有對應——需要就自己開資源 |
| `IDisposable` 由容器釋放 | `yield` dependency 的 `finally` |
| 註冊介面→實作 | 沒有對應；測試用 `dependency_overrides` |
| `IServiceProvider`（Service Locator） | 沒有；一律走參數 |

### Middleware 與 Filter

| ASP.NET Core | FastAPI |
| --- | --- |
| `app.UseX()` | `app.add_middleware(X)` |
| **註冊順序 = 執行順序** | **註冊順序相反**（最後加的最外層） |
| `await next(context)` | `await call_next(request)` |
| Authorization Filter | dependency |
| Action Filter | dependency（前置）／middleware（後置） |
| Exception Filter | `@app.exception_handler(...)` |
| Result Filter | 沒有直接對應 |
| `UseCors()` | `CORSMiddleware`（要最後註冊） |
| `UseHttpsRedirection()` | 通常交給 Ingress |
| `UseResponseCompression()` | `GZipMiddleware` |

### 認證與授權

| ASP.NET Core | FastAPI |
| --- | --- |
| `AddAuthentication().AddJwtBearer(...)` | **沒有對應**，自己寫 dependency |
| Authentication middleware | 沒有——驗證發生在 dependency 裡 |
| `[Authorize]` | `dependencies=[Depends(get_current_user)]` |
| `[Authorize(Roles = "Admin")]` | `Depends(RequireRole("admin"))` |
| `[Authorize(Policy = "X")]` | 自訂 dependency |
| `[AllowAnonymous]` | 放進另一個沒掛依賴的 router |
| `FallbackPolicy` | 把依賴掛在 `FastAPI(dependencies=[...])` |
| `ClaimsPrincipal` / `User.Identity` | 自己回傳的 `User` 物件 |
| `TokenValidationParameters` | `jwt.decode(..., algorithms=, audience=, issuer=, leeway=)` |
| `ClockSkew`（預設 5 分鐘） | `leeway`（預設 0，建議 30 秒） |
| `IAuthorizationHandler`（resource-based） | 把條件寫進查詢並包成 dependency |

### 錯誤處理

| ASP.NET Core | FastAPI |
| --- | --- |
| `ProblemDetails`（RFC 9457） | 自己實作（格式一樣） |
| `IExceptionHandler`（.NET 8） | `@app.exception_handler(Exception)` |
| `UseExceptionHandler()` | 框架內建的 `ServerErrorMiddleware` |
| `NotFound()` / `BadRequest()` | `raise HTTPException(404)` |
| `StatusCodes.Status201Created` | `status.HTTP_201_CREATED` |
| 開發環境例外頁 | `FastAPI(debug=True)`（**正式環境絕不可開**） |

### 資料存取

| ASP.NET Core | FastAPI |
| --- | --- |
| EF Core | SQLAlchemy |
| `DbContext` | `Session` |
| `DbSet<T>` | `select(Model)` |
| Entity | Declarative model |
| Change tracker | Identity map + unit of work（概念相同） |
| `AsNoTracking()` | `execute(...).scalars()` 搭配輕量查詢，或 Core 層 |
| `Include()` | `options(selectinload(...))` / `joinedload(...)` |
| `SaveChanges()` | `commit()` |
| EF Migrations | Alembic |
| `Add-Migration` / `Update-Database` | `alembic revision --autogenerate` / `alembic upgrade head` |
| 連線池（`Max Pool Size`） | `create_engine(pool_size=, max_overflow=)` |
| `DbContextPool` | `create_engine` 本身就是池 |

### 設定

| ASP.NET Core | FastAPI |
| --- | --- |
| `IConfiguration` | `Settings`（pydantic-settings） |
| `IOptions<T>` | `Annotated[Settings, Depends(get_settings)]` |
| `IOptionsSnapshot<T>` | 沒有對應（設定在程序內不變） |
| `Configure<T>(section)` | 巢狀 `BaseModel` + `env_nested_delimiter="__"` |
| `ValidateOnStart()` | 模組層級建立 + `model_validator` |
| `Jwt:Key`（冒號分隔） | `JWT__KEY`（雙底線） |
| User Secrets | `.env`（不進版控） |

### 測試

| ASP.NET Core | FastAPI |
| --- | --- |
| `WebApplicationFactory<T>` | `TestClient(app)`（**不啟動伺服器，便宜很多**） |
| 覆寫 `ConfigureTestServices` | `app.dependency_overrides[dep] = fake` |
| `TestAuthHandler` + 假 scheme | `dependency_overrides[get_current_user] = lambda: user` |
| xUnit `[Fact]` / `[Theory]` | pytest `def test_x` / `@pytest.mark.parametrize` |
| `IClassFixture<T>` | `@pytest.fixture(scope="class")` |
| Testcontainers.NET | testcontainers-python |
| `TimeProvider` | 自己做 `get_now` dependency |
| InMemory provider（不可靠） | SQLite（**同樣不可靠**） |

### 部署

| ASP.NET Core | FastAPI |
| --- | --- |
| `mcr.microsoft.com/dotnet/aspnet:8.0` | `python:3.12-slim`（**不要 alpine**） |
| `ASPNETCORE_URLS=http://+:8080` | `--host 0.0.0.0 --port 8000` |
| `UseForwardedHeaders()` | `--proxy-headers --forwarded-allow-ips` |
| CPU limit 影響 ThreadPool 大小 | **沒有影響**（event loop 是單執行緒） |
| Server GC 與容器記憶體 | CPython arena 不還記憶體給 OS |
| `AddHealthChecks()` | 自己寫 `/health/live` 與 `/health/ready` |
| migration 由 Job 執行 | 一樣 |

---

## 三、並排：同一支 API

### CRUD

```csharp
[ApiController]
[Route("api/orders")]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _service;
    public OrdersController(IOrderService service) => _service = service;

    [HttpGet("{id:int}")]
    public async Task<ActionResult<OrderDto>> GetAsync(int id)
    {
        var order = await _service.FindAsync(id);
        if (order is null) return NotFound();
        return Ok(order);
    }

    [HttpPost]
    [Authorize]
    public async Task<ActionResult<OrderDto>> CreateAsync([FromBody] CreateOrderDto dto)
    {
        var order = await _service.CreateAsync(dto);
        return CreatedAtAction(nameof(GetAsync), new { id = order.Id }, order);
    }
}
```

```python
router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: DbSession):
    order = order_service.find(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "order not found")
    return order

@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: DbSession, user: CurrentUser):
    return order_service.create(db, payload, user)
```

三個對應點：`[Authorize]` 變成簽章上的 `user: CurrentUser`（同時完成認證與取得使用者）、`ActionResult<T>` 變成 `response_model`、`NotFound()` 變成 `raise`。

### DI

```csharp
// Program.cs
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddSingleton<IClock, SystemClock>();
builder.Services.AddDbContext<AppDbContext>(o => o.UseOracle(cs));

// 使用
public OrdersController(IOrderService service) { }
```

```python
# app/api/deps.py —— 沒有註冊，直接宣告
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]

@lru_cache
def get_settings() -> Settings:
    return Settings()

# 使用
def create_order(db: DbSession): ...
```

### 錯誤處理

```csharp
public class AppExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext ctx, Exception ex, CancellationToken ct)
    {
        var problem = new ProblemDetails { Status = 500, Title = "Internal Server Error" };
        ctx.Response.StatusCode = 500;
        await ctx.Response.WriteAsJsonAsync(problem, ct);
        return true;
    }
}
builder.Services.AddExceptionHandler<AppExceptionHandler>();
```

```python
@app.exception_handler(Exception)
async def on_unhandled(request: Request, exc: Exception):
    logger.exception("unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"type": "about:blank", "title": "Internal Server Error", "status": 500},
        media_type="application/problem+json",
    )
```

### 測試

```csharp
public class OrdersTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;
    public OrdersTests(WebApplicationFactory<Program> factory) =>
        _client = factory.WithWebHostBuilder(b => b.ConfigureTestServices(s =>
        {
            s.AddScoped<IOrderService, FakeOrderService>();
        })).CreateClient();
}
```

```python
def test_get_order(client, db_session):
    order = make_order(db_session)
    resp = client.get(f"/api/orders/{order.id}")
    assert resp.status_code == 200
```

---

## 四、看起來一樣，其實不一樣

這一節是整份附錄最重要的部分。以下每一項都是「照著 .NET 的直覺寫，會出事」。

| # | 主題 | .NET 的直覺 | FastAPI 的現實 | 章 |
| --- | --- | --- | --- | --- |
| 1 | **async** | 加了沒壞處，只有好處 | `async def` 裡有同步阻塞 → **整個程序停止回應** | 04 |
| 2 | **middleware 順序** | 先註冊先執行 | **反的**，最後註冊的在最外層 | 08 |
| 3 | **驗證失敗狀態碼** | 400 | **422** | 02 |
| 4 | **DI 錯誤何時發現** | 啟動時（`Build()` 驗證） | **第一次呼叫那條路由時** | 03 |
| 5 | **路由消歧義** | 優先序演算法，字面優先 | **宣告順序**，`/users/me` 要寫在前面 | 01 |
| 6 | **`[Authorize]` 的等價物** | 加了就有效 | `Depends(oauth2_scheme)` **不驗證任何東西** | 07 |
| 7 | **middleware 裡丟例外** | Exception Filter 會接到 | **變成 500**，handler 接不到 | 06 |
| 8 | **Scoped 的實作** | 容器管理的 scope | 依賴結果的**快取**（同一 request 只呼叫一次） | 03 |
| 9 | **CPU limit** | 影響 ThreadPool 大小計算 | **沒有影響**，event loop 只用一核 | 11 |
| 10 | **記憶體回收** | GC 會還給 OS | CPython **不一定還**，高原是正常的 | 11 |
| 11 | **`ClockSkew`** | 預設 5 分鐘（太寬鬆） | `leeway` 預設 **0**（太嚴格），要自己設 | 07 |
| 12 | **測試用的假資料庫** | InMemory provider 不可靠 | SQLite **同樣不可靠**（而且更多人踩） | 10 |
| 13 | **回傳 Entity** | 有 DTO 慣例擋著 | 沒有 `response_model` 就**整列序列化出去** | 02 |
| 14 | **Optional 參數** | `string?` 就是可選 | `str \| None` **仍是必填**，要看有沒有預設值 | 01 |

---

## 五、遷移實務

### 建議順序

1. **先搬設定與健康檢查**——最小可部署單元，先把 CI/CD 與 K8s manifest 打通
2. **再搬 model 與 schema**——SQLAlchemy model 與 Pydantic schema，這一步最花時間但沒有風險
3. **再搬認證**——它是所有 endpoint 的前提
4. **一個 router 一個 router 搬**——舊服務仍在跑，用 Ingress 依路徑分流，可以逐步切換
5. **最後才處理背景工作**——這一塊差異最大（見第七節）

### 不要照搬的東西

| .NET 慣例 | 在 Python 該怎麼做 |
| --- | --- |
| 泛型 `IRepository<T>` 基底類別 | 直接用 SQLAlchemy 的 `select()`，多一層通常沒有價值 |
| AutoMapper | `OrderOut.model_validate(order)`，或直接 `response_model` |
| 每個 service 一個介面 | Python 沒有編譯期契約檢查，介面的收益低；需要替換就用 `dependency_overrides` |
| 三層專案結構（.Api / .Core / .Infra） | 一個 package 裡分資料夾就夠，Python 沒有組件邊界 |
| `Result<T>` pattern | 用例外（Python 的例外成本比 .NET 低，社群慣例也是用例外） |
| 大量的 `I` 前綴介面 | 不需要，用 `Protocol` 只在真的需要型別檢查時 |

最容易犯的錯誤是**把 C# 的結構原封不動翻譯成 Python**。結果是一份「用 Python 語法寫的 C# 程式」，別的 Python 開發者看了會覺得繁瑣，而且失去了 FastAPI 那套「型別即契約」的簡潔。

---

## 六、FastAPI 有、.NET 沒有的

**dependency 的參數會冒泡進 OpenAPI。** 一個 dependency 宣告了 `skip` 和 `limit` 兩個 query 參數，掛上它的 endpoint **自動獲得**這兩個參數，而且出現在 `/docs` 上。.NET 那邊要寫自訂 model binder 才做得到類似的事。

**`dependency_overrides`。** 全域、單行、作用在依賴鏈任何一層。.NET 要重建 `WebApplicationFactory` 並重新註冊服務。

**內建的 `/docs`。** 不用裝 Swashbuckle、不用設定，而且永遠和程式碼同步（因為它是從函式簽章即時產生的）。

**`Annotated` 型別別名。** `DbSession = Annotated[Session, Depends(get_db)]` 之後所有地方寫 `db: DbSession`。C# 沒有這種輕量的組合方式。

---

## 七、.NET 有、FastAPI 沒有的

**完整的 authentication 系統。** scheme、handler、challenge/forbid 的分工，FastAPI 全部要自己寫。優點是透明，缺點是漏寫就是漏洞。

**編譯期型別安全。** 這是最大的一項。C# 的重構（改名、改簽章）由編譯器保證，Python 只能靠測試與 mypy/Pyright。**專案超過一定規模，一定要把型別檢查加進 CI**，否則會很痛苦。

**啟動時的 DI 驗證。** 缺註冊會在啟動時炸掉，這是很有價值的一道保護。FastAPI 沒有，所以測試覆蓋率的重要性提高。

**`IHttpClientFactory` + Polly。** 連線管理、重試、斷路器的一級支援。Python 這邊要自己在 `lifespan` 管 `httpx.AsyncClient`，重試與斷路器用 `tenacity`、`pybreaker` 之類的套件自行組裝。

**`BackgroundService` / `IHostedService`。** .NET 的背景工作是框架一級公民。FastAPI 的 `BackgroundTasks` 只是「回應送出後在同程序執行」，程序被砍就沒了；真正的背景工作要靠外部佇列（Celery、arq）或 K8s CronJob。

**成熟的 metrics 與 tracing 整合。** .NET 內建 `System.Diagnostics.Metrics` 與 OpenTelemetry 的深度整合。Python 這邊要裝 `opentelemetry-instrumentation-fastapi`，可用但整合度沒那麼深。

---

## 八、一句話總結

**ASP.NET Core 給你一個完整的框架，你在它的結構裡填空。FastAPI 給你一組很好的零件，你自己組裝。**

前者的代價是要學框架的規則（scheme、filter、policy、provider 疊層），好處是很多事情它替你做對了。後者的代價是很多事情你要自己做對（認證、錯誤格式、logging、背景工作），好處是沒有隱藏的機制——出問題時，整條路徑都在你自己寫的那幾十行裡。

知道哪些事情「沒人替你做」，就是這套教材的全部價值。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[12-cheatsheet]] — 上一章：附錄 A 速查
- [[dotnet-web-api]] — .NET 那套教材的總目錄
- [[00-why-fastapi-and-setup]] — 回到第 00 章
- [[csharp]] — C# 語言
- [[python]] — Python 語言
