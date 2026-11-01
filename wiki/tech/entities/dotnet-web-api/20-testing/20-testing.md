---
type: concept
domain: tech
tags: [dotnet, aspnet, testing, xunit, webapplicationfactory, testcontainers, mock, timeprovider]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-15
updated: 2026-11-01
---

# 第 20 章：測試 — 測了很多，但沒有信心

## 兩種都不理想的測試

**第一種：測試很多，但都在測框架**

```csharp
[Fact]
public void Controller_Should_Return_Ok()
{
    var mockService = new Mock<IUserService>();
    mockService.Setup(x => x.GetAllAsync()).ReturnsAsync(new List<User>());
    var controller = new UsersController(mockService.Object);

    var result = await controller.GetAllAsync();

    Assert.IsType<OkObjectResult>(result);
}
```

這個測試證明了什麼？證明「呼叫 `Ok()` 會回傳 `OkObjectResult`」——那是框架的行為，微軟已經測過了。它不會發現路由寫錯、驗證屬性漏掉、序列化選項不對、授權設定有洞。**它給了覆蓋率，沒給信心。**

**第二種：用 InMemory provider 測資料存取**

```csharp
var options = new DbContextOptionsBuilder<AppDbContext>()
    .UseInMemoryDatabase(Guid.NewGuid().ToString())
    .Options;
```

測試全綠，上線後才發現：那個 LINQ 查詢在真實資料庫翻譯不出來、唯一約束根本沒被檢查、交易語意完全不同。**InMemory provider 不是資料庫，它是一個假裝成資料庫的字典。**

這一章要建立的是：什麼該測、用什麼工具測、以及怎麼讓測試真的能擋住 bug。

---

## 一、Web API 的測試分層

| 層 | 測什麼 | 工具 | 數量 |
| --- | --- | --- | --- |
| 單元測試 | 業務規則、計算、狀態轉換 | xUnit + 純物件 | 多 |
| 整合測試 | 端點行為、驗證、授權、序列化 | `WebApplicationFactory` | 中 |
| 資料存取測試 | 查詢翻譯、約束、交易 | Testcontainers | 少但關鍵 |
| 端對端 | 完整流程 | 部署後的煙霧測試 | 極少 |

判斷一個測試值不值得寫，我用兩個問題：

**「這個測試失敗時，我會知道哪裡壞了嗎？」** 如果答案是「不知道，要debug 半天」，那個測試的價值有限。

**「這段程式碼壞掉時，這個測試會失敗嗎？」** 如果一個 controller 測試在路由改錯、驗證漏掉、授權設錯時都不會失敗——它保護不了什麼。

---

## 二、單元測試：測業務邏輯

值得單元測試的是**有分支、有計算、有規則**的程式碼：

```csharp
public class OrderPricing
{
    public decimal Calculate(IReadOnlyList<OrderLine> lines, Customer customer)
    {
        var subtotal = lines.Sum(l => l.UnitPrice * l.Quantity);

        var discount = customer.Tier switch
        {
            CustomerTier.Gold when subtotal >= 10000 => 0.15m,
            CustomerTier.Gold => 0.10m,
            CustomerTier.Silver => 0.05m,
            _ => 0m
        };

        return Math.Round(subtotal * (1 - discount), 2, MidpointRounding.AwayFromZero);
    }
}
```

```csharp
[Theory]
[InlineData(CustomerTier.Gold, 10000, 8500)]
[InlineData(CustomerTier.Gold, 9999.99, 8999.99)]
[InlineData(CustomerTier.Silver, 10000, 9500)]
[InlineData(CustomerTier.Regular, 10000, 10000)]
public void Calculate_AppliesTierDiscount(CustomerTier tier, decimal amount, decimal expected)
{
    var lines = new[] { new OrderLine("SKU", amount, 1) };
    var customer = new Customer { Tier = tier };

    var result = new OrderPricing().Calculate(lines, customer);

    Assert.Equal(expected, result);
}
```

注意第二個案例特意測了**邊界值** `9999.99`——「大於等於 10000」這個條件寫成 `>` 還是 `>=` 是最容易出錯的地方，而只測 10000 和 5000 的話兩種寫法都會通過。

這種測試的特徵是：不需要 mock、執行毫秒級、失敗時一眼看出哪個規則錯了。**業務邏輯能抽成這種純函式，測試就會變得容易**——這是「把業務邏輯從 controller 與 DbContext 裡抽出來」的實際回報。

### 2.1 Mock 的邊界

規則很簡單：**mock 你擁有的介面，不要 mock 你不擁有的型別。**

```csharp
// ✅ 自己定義的介面，語意由自己掌握
var payment = new Mock<IPaymentGateway>();
payment.Setup(x => x.ChargeAsync(It.IsAny<decimal>(), default))
       .ReturnsAsync(PaymentResult.Success("tx-123"));

// ❌ 不要 mock DbContext / DbSet
var db = new Mock<AppDbContext>();     // 幾乎必然做出錯誤的假設
```

Mock `DbContext` 的問題在於：你得自己模擬 change tracker、識別對應、查詢翻譯、並發檢查的行為——而你對這些的理解如果有誤，測試就會驗證一個錯誤的假設。測試綠了，生產環境爆炸。

資料存取應該用真實資料庫測（第四節）。

### 2.2 時間：`TimeProvider`

依賴 `DateTime.UtcNow` 的程式碼很難測——你沒辦法讓時間快轉。.NET 8 引入了標準抽象：

```csharp
public class TokenService
{
    private readonly TimeProvider _time;

    public TokenService(TimeProvider time) { _time = time; }

    public string Create(User user) =>
        BuildToken(user, expires: _time.GetUtcNow().AddMinutes(15));
}

// 註冊
builder.Services.AddSingleton(TimeProvider.System);

// 測試
var fake = new FakeTimeProvider(new DateTimeOffset(2026, 8, 15, 0, 0, 0, TimeSpan.Zero));
var service = new TokenService(fake);

var token = service.Create(user);
fake.Advance(TimeSpan.FromMinutes(16));      // 時間快轉

Assert.False(IsValid(token));
```

`FakeTimeProvider` 來自 `Microsoft.Extensions.TimeProvider.Testing` 套件。.NET 8 之前的專案可以自己定義 `IClock` 介面，概念相同。

任何涉及過期、排程、時間窗的邏輯都值得這樣抽象——否則測試只能靠 `Thread.Sleep`，慢且不穩定。

---

## 三、整合測試：`WebApplicationFactory`

這是 Web API 測試裡**投資報酬率最高**的一層。它在記憶體中啟動完整的應用程式（真實的 pipeline、路由、DI、序列化），用 `HttpClient` 送真實的請求：

```csharp
public class ApiFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");

        builder.ConfigureTestServices(services =>
        {
            // 替換外部依賴，保留其餘真實設定
            services.RemoveAll<IPaymentGateway>();
            services.AddScoped<IPaymentGateway, FakePaymentGateway>();
        });
    }
}

public class OrdersApiTests : IClassFixture<ApiFactory>
{
    private readonly HttpClient _client;

    public OrdersApiTests(ApiFactory factory) => _client = factory.CreateClient();

    [Fact]
    public async Task Create_WithoutAuth_Returns401()
    {
        var response = await _client.PostAsJsonAsync("/api/orders", new { });

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task Create_WithInvalidPayload_Returns400WithProblemDetails()
    {
        var client = CreateAuthenticatedClient();

        var response = await client.PostAsJsonAsync("/api/orders",
            new { quantity = -1 });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);

        var problem = await response.Content.ReadFromJsonAsync<ValidationProblemDetails>();
        Assert.Contains("Quantity", problem!.Errors.Keys);
    }
}
```

這種測試**真的能擋住 bug**，因為它覆蓋了單元測試碰不到的東西：路由是否正確註冊、`[Authorize]` 是否生效、驗證屬性是否被執行、JSON 命名策略是否如預期、錯誤格式是否符合契約、middleware 順序是否正確。

`Program` 類別需要對測試專案可見。Minimal hosting model 的 `Program.cs` 沒有明確的類別宣告，在檔案結尾加一行：

```csharp
public partial class Program { }
```

或在 `.csproj` 裡用 `InternalsVisibleTo`。

### 3.1 測試中的認證

每個測試都真的跑一次登入流程既慢又脆弱。標準做法是註冊一個測試專用的 authentication scheme：

```csharp
public class TestAuthHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    public const string SchemeName = "Test";

    public TestAuthHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger, UrlEncoder encoder)
        : base(options, logger, encoder) { }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue("X-Test-User", out var userId))
        {
            return Task.FromResult(AuthenticateResult.NoResult());
        }

        var roles = Request.Headers["X-Test-Roles"].ToString()
            .Split(',', StringSplitOptions.RemoveEmptyEntries);

        var claims = new List<Claim> { new(ClaimTypes.NameIdentifier, userId!) };
        claims.AddRange(roles.Select(r => new Claim(ClaimTypes.Role, r)));

        var identity = new ClaimsIdentity(claims, SchemeName);
        var ticket = new AuthenticationTicket(new ClaimsPrincipal(identity), SchemeName);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
```

```csharp
builder.ConfigureTestServices(services =>
{
    services.AddAuthentication(TestAuthHandler.SchemeName)
        .AddScheme<AuthenticationSchemeOptions, TestAuthHandler>(
            TestAuthHandler.SchemeName, _ => { });
});

// 測試中
client.DefaultRequestHeaders.Add("X-Test-User", "42");
client.DefaultRequestHeaders.Add("X-Test-Roles", "Admin");
```

這讓「不同角色看到不同結果」的授權測試變得容易——而授權邏輯（第 14 章）正是最需要測試覆蓋的部分之一，因為它的錯誤直接是資安漏洞。

**務必確保這個 handler 只在測試環境註冊。** 它出現在生產環境等於任何人都能自稱管理員。放在測試專案裡而不是主專案，是最可靠的隔離。

---

## 四、資料存取測試：不要用 InMemory

`UseInMemoryDatabase` 的問題不是「不完美」，而是它在幾個關鍵行為上**與真實資料庫不同**：

| 行為 | InMemory | 真實資料庫 |
| --- | --- | --- |
| LINQ 翻譯 | 全部在記憶體執行，**永不失敗** | 翻譯不了就拋例外 |
| 唯一約束 | 不檢查 | 檢查 |
| 外鍵約束 | 不檢查 | 檢查 |
| 交易 | 幾乎是空操作 | 真實語意 |
| 並發 token | 行為不同 | 真實檢查 |
| 資料型別 | C# 型別 | Oracle 的 NUMBER、空字串即 NULL… |

第一項最致命：**在 InMemory 上，任何 LINQ 都能執行**——包括那些在真實資料庫會拋 `could not be translated` 的（第 08 章）。所以 InMemory 測試通過，完全不代表查詢能跑。

微軟官方文件現在也明確建議不要用它做測試。

### 4.1 Testcontainers（推薦）

在測試時啟動真實的資料庫容器：

```csharp
public class OracleFixture : IAsyncLifetime
{
    private readonly OracleContainer _container = new OracleBuilder()
        .WithImage("gvenzl/oracle-free:23-slim-faststart")
        .Build();

    public string ConnectionString => _container.GetConnectionString();

    public async Task InitializeAsync()
    {
        await _container.StartAsync();

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseOracle(ConnectionString).Options;

        await using var db = new AppDbContext(options);
        await db.Database.MigrateAsync();      // 順便驗證 migration 能跑
    }

    public Task DisposeAsync() => _container.DisposeAsync().AsTask();
}
```

好處是測的是**真實的 provider、真實的 SQL、真實的約束**——第 10 章講的所有 Oracle 特性（大小寫、空字串、`IN` 上限）都會在測試中如實呈現。連 migration 能不能跑都順便驗證了。

代價是慢（容器啟動需要時間，Oracle 映像尤其）與需要 Docker。實務做法是分開跑：單元測試與 `WebApplicationFactory` 測試每次 commit 都跑，資料庫整合測試在 CI 的獨立階段跑。

### 4.2 測試間的資料隔離

多個測試共用一個資料庫時，彼此的資料會互相污染。三種做法：

**每個測試一個交易並回滾**——最快，但測不到「跨交易」的行為。

**每個測試前清空**——用 Respawn 這類工具重置資料表。可靠但較慢。

**每個測試用不同的資料**——不清空，靠隨機 ID 避免衝突。最快但容易寫出隱性依賴。

我傾向第二種：慢一點，但測試之間真正獨立，失敗時的原因明確。測試的可靠性比執行速度重要——一個偶爾失敗的測試套件很快就會被所有人忽略。

---

## 五、什麼不值得測

明確列出來比較有用：

- **Controller 呼叫 service 後回傳 `Ok()`**——那是框架行為，用整合測試涵蓋端點即可
- **DI 註冊是否正確**——`ValidateOnBuild`（第 00 章）在啟動時就會驗證
- **自動產生的程式碼**、DTO 的 getter/setter
- **私有方法**——透過公開行為測試它。需要單獨測試通常代表它該被抽成獨立類別
- **第三方函式庫的行為**——EF Core、System.Text.Json 有自己的測試

覆蓋率是**診斷工具，不是目標**。80% 的覆蓋率如果全在測 getter，比 50% 但覆蓋了所有業務規則與授權路徑要糟。

值得優先投資的順序是：**業務規則的分支與邊界 → 授權路徑 → 錯誤處理路徑 → 資料存取的查詢翻譯**。前兩者出錯的代價最高。

---

## 六、背景服務的測試

`BackgroundService`（第 19 章）可以直接測 `ExecuteAsync`，但要注意它是個無限迴圈：

```csharp
[Fact]
public async Task Worker_ProcessesPendingItems()
{
    using var cts = new CancellationTokenSource();
    var worker = new OutboxPublisher(scopeFactory, logger, timeProvider);

    await worker.StartAsync(cts.Token);

    // 用 FakeTimeProvider 快轉，觸發下一輪
    timeProvider.Advance(TimeSpan.FromSeconds(5));
    await Task.Delay(50);                  // 讓迴圈有機會執行

    await worker.StopAsync(CancellationToken.None);

    Assert.All(await GetOutboxAsync(), m => Assert.NotNull(m.ProcessedAt));
}
```

`Task.Delay` 這種寫法本質上是不穩定的（時序依賴）。**更好的做法是把工作內容抽成一個可獨立測試的方法**，讓 `ExecuteAsync` 只負責「計時 + 開 scope + 呼叫它」：

```csharp
public class OutboxPublisher : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(5));
        while (await timer.WaitForNextTickAsync(ct))
        {
            using var scope = _scopeFactory.CreateScope();
            await PublishBatchAsync(scope.ServiceProvider, ct);    // ← 測這個
        }
    }

    internal static async Task PublishBatchAsync(IServiceProvider sp, CancellationToken ct)
    {
        // 實際邏輯
    }
}
```

這是一個普遍原則：**難測的程式碼通常是設計問題，不是測試工具的問題。** 把時序、迴圈、框架整合與業務邏輯分開，測試就會變簡單。

---

## 七、常見誤解

**「覆蓋率越高越好。」**
覆蓋率是診斷工具。80% 全在測 getter 比 50% 覆蓋所有業務規則要糟。看的應該是「關鍵路徑有沒有被測到」。

**「用 InMemory provider 測資料存取。」**
它不檢查約束、不做真實的 LINQ 翻譯，所以測試通過不代表查詢能在真實資料庫跑。用 Testcontainers。

**「Controller 要有單元測試。」**
mock 掉所有依賴之後，測的只剩框架行為。用 `WebApplicationFactory` 做整合測試更有價值——它會抓到路由、驗證、授權、序列化的問題。

**「Mock DbContext 可以避免資料庫依賴。」**
你得自己模擬 change tracker 與查詢語意，而錯誤的假設會讓測試驗證錯誤的行為。資料存取用真實資料庫測。

**「整合測試太慢，寫幾個就好。」**
`WebApplicationFactory` 是記憶體內的，通常幾十毫秒。真正慢的是資料庫容器，那部分可以分階段跑。

**「私有方法也要測。」**
透過公開行為測試它。需要單獨測試通常代表它該被抽成獨立的類別。

---

## 八、同事會來問你的問題

**Q：Controller 該怎麼測？**
不要對它做 mock 式的單元測試。用 `WebApplicationFactory` 送真實 HTTP 請求，驗證狀態碼、回應格式、授權行為。業務邏輯抽到 service 層再單獨做單元測試。

**Q：`WebApplicationFactory<Program>` 說找不到 Program。**
Minimal hosting model 的 `Program` 是隱含的 internal 類別。在 `Program.cs` 結尾加 `public partial class Program { }`，或設定 `InternalsVisibleTo`。

**Q：測試需要登入怎麼辦？**
在測試專案裡寫一個 `TestAuthHandler`，從自訂 header 讀使用者與角色，用 `ConfigureTestServices` 替換掉真實的認證。務必確保它不會被打包進生產環境。

**Q：InMemory provider 到底能不能用？**
不建議用來測資料存取。它不做真實的 LINQ 翻譯、不檢查約束、交易語意不同。用 Testcontainers 跑真實的 Oracle。

**Q：涉及時間的邏輯怎麼測？**
注入 `TimeProvider`（.NET 8+）而不是直接用 `DateTime.UtcNow`。測試時用 `FakeTimeProvider` 快轉時間，不需要 `Thread.Sleep`。

**Q：測試之間資料互相干擾。**
每個測試前用 Respawn 重置資料庫。比「每個測試一個交易並回滾」慢一點，但真正獨立，失敗原因明確。

**Q：背景服務怎麼測？**
把工作內容抽成獨立方法，直接測它，不要去驅動那個無限迴圈。難測通常是設計問題——時序與業務邏輯應該分開。

---

## 連結

- [[basics-15-testing]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[19-background-work]] — 上一章
- [[21-deployment]] — 下一章：部署與交付
- [[02-dependency-injection]] — 用 `Replace` 抽換服務
- [[08-efcore-query]] — 為什麼 InMemory 測不到查詢翻譯
- [[14-authorization]] — 授權路徑是最該被測試覆蓋的部分
- [[unit-testing-sop]] — 新手前置：AAA、命名、Fact/Theory、情境對照表，先讀那篇再讀本章
