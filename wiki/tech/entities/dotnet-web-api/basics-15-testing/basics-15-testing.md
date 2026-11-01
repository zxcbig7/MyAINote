---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, testing, xunit, xunit-v3, webapplicationfactory, testcontainers, oracle, integration-test, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 10：測試、部署與正式上線準備.md
  - https://xunit.net/docs/getting-started/v3/getting-started
  - https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests?view=aspnetcore-10.0
  - https://dotnet.testcontainers.org/
created: 2026-11-01
updated: 2026-11-01
---

# 入門第 15 章：測試 — 改了程式，怎麼知道沒弄壞東西

## 一個編譯通過、審查也過的錯誤

TaskTracker 的權限矩陣寫得很清楚：Viewer 只能讀，Editor 可以新增與修改，只有 Admin 能刪除。刪除端點上掛的是 `[Authorize(Policy = Permissions.TasksDelete)]`。某天有人在 `TasksController` 旁邊新增另一支需要寫入權限的 action，複製了上一個 action 的屬性，順手把刪除端點那一行也改成了 `Permissions.TasksWrite`。diff 只有一個單字，審查的人掃過去，看起來像是對齊命名。專案編譯成功，`dotnet run` 正常啟動，Scalar 的 API 文件頁看起來也沒變。

直到有一位 Editor 刪掉了不該刪的任務，才有人發現這件事。這個錯誤沒有任何一個階段會主動喊出來：編譯器看不出 policy 名稱寫錯，因為它只是字串常數；啟動時不會檢查，因為每個 policy 都有註冊；文件也不會變，因為 OpenAPI 只記錄「這支端點需要登入」，不記錄需要哪一種權限。

[[basics-14-openapi-and-versioning]] 把整組路由改成 `api/v{version:apiVersion}/...` 時，同樣的事已經發生過一次：原本的 `/api/tasks` 從此是 404，沒有任何東西事先告訴改動的人，前端能不能繼續用。這類改動的共同特徵是：每一行單獨看都合理，壞掉的是行與行之間的組合。要在合併之前知道組合有沒有壞，唯一的辦法是把「預期的行為」寫成會自動執行的程式，每次改完就跑一遍。這就是測試。本章替 TaskTracker 建一個測試專案，分兩層：用單元測試驗證 Service 的商業規則，用整合測試讓請求走過真實的 pipeline、真實的授權、真實的 Oracle。最後會把上面那個複製貼上的錯誤重現一次，看哪一層的測試會變紅。

---

## 一、兩種測試各自抓得到什麼

測試分層的依據是「這個測試啟動了多少真實的東西」。單元測試只建立被測的類別，用 `new` 把它需要的物件（時間、設定、資料庫）直接餵進去，呼叫方法，檢查結果。沒有 Web server，沒有 pipeline，沒有 DI container。整合測試則是啟動整個應用程式（在記憶體內，不佔用真實連接埠），透過 `HttpClient` 送出真正的 HTTP 請求，請求會經過 routing、authentication、authorization、model binding、驗證、Controller、Service、EF Core，直到資料庫，再原路回來。

兩者抓到的錯誤幾乎不重疊。以 TaskTracker 現有的程式碼為例：

| 錯誤類型 | 單元測試 | 整合測試 |
| --- | --- | --- |
| 業務規則寫錯（修改自己的標題被當成重複） | 抓得到，而且失敗訊息直接指向 Service | 抓得到，但要從狀態碼往回推 |
| 路由或版本字串打錯，端點變 404 | 抓不到，Controller 沒被執行 | 抓得到 |
| `[Authorize]` 的 policy 寫錯 | 抓不到，屬性只是 metadata | 抓得到 |
| DTO 欄位改名、JSON 大小寫改變 | 抓不到 | 抓得到 |
| 驗證失敗沒有回 400 ProblemDetails | 抓不到 | 抓得到 |
| DI 少註冊一個服務 | 抓不到，單元測試自己 `new` | 抓得到，請求打到用它的 Controller 時回 500 |
| LINQ 翻成 SQL 後行為不同、唯一索引 | 抓不到 | 抓得到（前提是跑在真實 Oracle 上） |
| 各種輸入組合的分支（空白、大小寫、邊界） | 便宜、快、適合窮舉 | 太慢，不適合窮舉 |

這張表也解釋了常見的分工原則為什麼成立：業務邏輯用單元測試，API 行為用整合測試。反過來的分配會出問題。用整合測試窮舉分支，一次測試要走完整條 pipeline 並碰資料庫，幾十個分支就要等幾分鐘，沒人願意在存檔時跑；用單元測試驗證 API 行為，則等於測了一個永遠不會碰到路由和授權的世界，全綠但什麼都沒保證。

另一句值得保留的原則是「測試你的邏輯，不測框架」。`[Required]` 會讓空字串被擋下，這是 ASP.NET Core 保證的行為，不需要另寫一個測試證明它；值得測的是「TaskTracker 把 `Title` 標了 `[Required]`，所以空白標題真的回 400，而且錯誤欄位叫 `Title`」，因為這是專案自己的設定。

---

## 二、建立測試專案：.NET 10 與 xunit.v3 的幾個差異

測試專案是一個獨立的 csproj，放在 `tests/` 底下，引用 API 專案。TaskTracker 的版本如下：

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <OutputType>Exe</OutputType>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="10.0.14" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.InMemory" Version="10.0.14" />
    <PackageReference Include="Testcontainers.Oracle" Version="4.16.0" />
    <PackageReference Include="xunit.v3" Version="4.0.2" />
  </ItemGroup>

  <ItemGroup>
    <Using Include="Xunit" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\src\TaskTracker.Api\TaskTracker.Api.csproj" />
  </ItemGroup>

</Project>
```

和多數舊教學不同的地方有三處。第一，套件叫 `xunit.v3`，不是 `xunit`。xUnit v3 已經正式發行（4.0 系列），範本與文件都往它靠攏；舊的 `xunit` 2.x 還能用，網路上大部分範例也還是它，但新專案沒有理由從舊版開始。第二，`<OutputType>Exe</OutputType>`：v3 的測試專案是一個自帶進入點的可執行檔，所以才能直接以 `dotnet run` 的方式啟動，也才能對接新的測試平台。第三，專案裡沒有 `Microsoft.NET.Test.Sdk` 與 `xunit.runner.visualstudio`，那是 VSTest 時代的配套，這裡用不到。

`<Using Include="Xunit" />` 讓每個檔案不必再寫 `using Xunit;`，純粹是省行數。接著把測試專案加進 solution，也就是在 `TaskTracker.slnx` 加一個 `tests` 資料夾：

```xml
<Folder Name="/tests/">
  <Project Path="tests/TaskTracker.Api.Tests/TaskTracker.Api.Tests.csproj" />
</Folder>
```

API 專案的 csproj 也要補上一行 `<PackageReference Include="Microsoft.EntityFrameworkCore.Relational" Version="10.0.14" />`，測試程式碼會用到 EF Core 關聯式資料庫專用的 API，本章的程式碼是在這個狀態下建置通過的。

### `global.json`：告訴 `dotnet test` 使用哪個 runner

這是最容易讓人卡住的一步。.NET 10 SDK 的 `dotnet test` 預設不再支援舊的 VSTest 模式去跑 xunit.v3 這種自帶進入點的專案，要明確選用新的 Microsoft.Testing.Platform（MTP）。選用的方式是在 `global.json` 加上 `test` 區段：

```json
{
  "sdk": {
    "version": "10.0.301",
    "rollForward": "latestFeature"
  },
  "test": {
    "runner": "Microsoft.Testing.Platform"
  }
}
```

沒有這一段時會看到什麼？把它拿掉再跑一次，實際輸出是：

```text
error : Testing with VSTest target is no longer supported by Microsoft.Testing.Platform on .NET 10 SDK and later. If you use dotnet test, you should opt-in to the new dotnet test experience. For more information, see https://aka.ms/dotnet-test-mtp-error [...\TaskTracker.Api.Tests.csproj]
```

訊息雖然指向一個網址，但解法就是上面那段 `global.json`。兩處語法跟著變：一是專案要用 `--project` 指定（`dotnet test --project tests/TaskTracker.Api.Tests`，不再是位置參數），二是篩選用 MTP 的參數，例如 `--filter-namespace` 與 `--filter-method`，不是舊的 `--filter "FullyQualifiedName~..."`。這些在本章後面都會用到。

### 不再需要 `public partial class Program`

整合測試要用 `WebApplicationFactory<Program>`，需要一個測試專案看得到的 `Program` 型別。`Program.cs` 使用 top-level statements 時，編譯器產生的 `Program` 預設是 `internal`，所以 .NET 8、9 的教學都會要求在 `Program.cs` 末尾手寫 `public partial class Program { }`。.NET 10 起，ASP.NET Core 的 source generator 會自動產生這個宣告，手寫的反而會被 analyzer 建議移除。TaskTracker 的 `Program.cs` 沒有這一行，下一節的 `WebApplicationFactory<Program>` 照樣編譯。如果專案停在 .NET 8 或 9，才需要補上。

---

## 三、單元測試：把 Service 的規則釘住

[[basics-07-dependency-injection-and-services]] 把商業規則集中到 `TaskService`，這時候的好處才完整兌現：Controller 薄，邏輯在 Service，Service 的相依（資料庫、時鐘、分頁設定）全部從建構子進來，測試可以自己決定餵什麼。

`TaskService` 依賴 `TimeProvider`，用來決定任務的建立時間。如果它直接寫 `DateTimeOffset.UtcNow`，測試就沒辦法斷言「建立時間是某個確定的值」，也沒辦法測「依建立時間排序」。.NET 8 起內建的 `TimeProvider` 抽象就是為此而生，測試自己實作一個固定的時鐘即可：

```csharp
internal sealed class FixedTimeProvider : TimeProvider
{
    private DateTimeOffset _now;

    public FixedTimeProvider(DateTimeOffset now)
    {
        _now = now;
    }

    public override DateTimeOffset GetUtcNow() => _now;

    public void Advance(TimeSpan by) => _now += by;
}
```

單元測試還需要一個隨用隨丟的資料庫。`TestDb.Create()` 每次用新的 Guid 當名稱建一個 EF Core InMemory 資料庫，所以每個測試各自拿到一份空資料（InMemory 能不能信任，下面有專門一節交代）：

```csharp
internal static class TestDb
{
    public static AppDbContext Create()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        return new AppDbContext(options);
    }
}
```

有了時鐘和資料庫，測試就能寫得像一句規格。下面是 `TaskServiceTests` 的兩個代表性測試，檔案開頭另有 `using MsOptions = Microsoft.Extensions.Options.Options;`：專案裡有 `TaskTracker.Api.Options` 這個命名空間，直接寫 `Options.Create(...)` 會被解析成命名空間而編譯失敗，所以用別名指向 `Microsoft.Extensions.Options.Options` 這個靜態類別。

```csharp
public class TaskServiceTests
{
    private static readonly DateTimeOffset Start = new(2026, 10, 31, 8, 0, 0, TimeSpan.Zero);

    private readonly FixedTimeProvider _clock = new(Start);
    private readonly TaskService _service;

    public TaskServiceTests()
    {
        _service = new TaskService(TestDb.Create(), _clock, MsOptions.Create(new PaginationOptions { DefaultPageSize = 2 }));
    }

    private static CancellationToken Ct => TestContext.Current.CancellationToken;

    [Fact]
    public async Task Create_sets_todo_status_and_creation_time_from_the_clock()
    {
        var created = await _service.CreateAsync(new CreateTaskRequest { Title = "  Write tests  " }, Ct);

        Assert.Equal("Write tests", created.Title);
        Assert.Equal(TaskItemStatus.Todo, created.Status);
        Assert.Equal(Start, created.CreatedAt);
        Assert.NotEqual(Guid.Empty, created.Id);
    }

    [Fact]
    public async Task Update_keeping_its_own_title_is_not_a_conflict()
    {
        var created = await _service.CreateAsync(new CreateTaskRequest { Title = "Mine" }, Ct);

        var updated = await _service.UpdateAsync(created.Id, new UpdateTaskRequest { Title = "Mine", Status = TaskItemStatus.Done }, Ct);

        Assert.Equal(TaskItemStatus.Done, updated.Status);
    }
}
```

幾個值得學的細節。xUnit 對每個測試方法建立新的測試類別實例，所以建構子裡建立的 `_service`、`_clock` 與資料庫，每個測試都是全新的，測試之間不會互相污染。方法名稱寫成完整句子（`Update_keeping_its_own_title_is_not_a_conflict`），失敗時測試報告的那一行本身就是說明，不必打開程式碼才知道哪個規則壞了。每個測試都是「準備、執行、斷言」三段，中間用空行隔開。`Ct` 取自 `TestContext.Current.CancellationToken`，這是 xUnit v3 提供的取消權杖：測試被中止或逾時時，它會被取消，所以傳遞給每個 `...Async` 呼叫，非同步測試不會在背景掛著不退出。這也符合全書 I/O 一律傳 `CancellationToken` 的規則。

`TaskServiceTests` 一共涵蓋建立、重複標題、不分大小寫的比對規則、查無資料、更新、更新時標題衝突的兩種情況、分頁預設值、狀態篩選，以及取消權杖。其中「取消」的那個測試值得單獨看，因為它檢查的是 Service 有沒有把權杖傳到底：

```csharp
[Fact]
public async Task A_cancelled_token_aborts_the_query()
{
    using var source = new CancellationTokenSource();
    await source.CancelAsync();

    await Assert.ThrowsAnyAsync<OperationCanceledException>(() => _service.ListAsync(new TaskListQuery(), source.Token));
}
```

如果有人在 Service 內部忘了把 `ct` 傳給 `ToListAsync`，這個測試會變紅。

### 斷言要用什麼

TaskTracker 只用 xUnit 內建的 `Assert`，沒有引入任何斷言函式庫。理由有兩個。其一，`Assert.Equal`、`Assert.Contains`、`Assert.ThrowsAsync`、`Assert.All` 對這個規模的測試已經夠用。其二，FluentAssertions 這個長期是 .NET 斷言首選的套件，從 8.0 版起改為商業授權（開源專案與非商業使用免費，商業使用要付費購買，授權方是 Xceed）；7.x 以前仍是 Apache-2.0。公司專案隨手 `dotnet add package FluentAssertions` 會拿到 8.x，授權問題要由法務判斷。需要流暢語法的團隊有兩個替代：社群 fork 的 AwesomeAssertions（API 相容，從 FluentAssertions 搬過來幾乎只改命名空間）與 Shouldly。沒有流暢斷言的需求就別多一個相依。

### 單元測試用的資料庫：InMemory 能不能用

上面的 `TestDb.Create()` 用了 EF Core 的 InMemory provider。這需要交代清楚，因為不少教學會推薦 InMemory 與 SQLite InMemory 當「測試資料庫」，這個建議用在整合測試的位置並不恰當。

InMemory provider 不是關聯式資料庫，只是把 LINQ 對記憶體中的集合執行。它不檢查唯一約束，不檢查外鍵，交易幾乎是空操作，最危險的是 LINQ 永遠不會翻譯失敗：在 Oracle 上會丟 `could not be translated` 的查詢，在 InMemory 上照樣執行，測試全綠而上線後出錯。SQLite 看起來更接近真實資料庫，但它的型別系統、字串比較、日期處理、交易與鎖定行為都與 Oracle 不同，用它通過的測試，只能證明「在 SQLite 上沒問題」。對作者的技術棧（Oracle）來說，這兩種都是在測一個不存在於正式環境的資料庫。

TaskTracker 的做法是劃一條界線：單元測試裡的資料庫只是讓 Service 有地方存取資料，測試的主題是 Service 自己的規則（標題要 trim、重複要丟 `ConflictException`、頁數怎麼算），結論不依賴資料庫的行為。任何結論取決於資料庫行為的測試，都一律移到整合測試，在真實的 Oracle 上跑。測試檔案開頭的註解就是這條界線的證據：InMemory 不支援 `ExecuteDeleteAsync`（刪除的實作），也不會強制唯一索引，所以刪除與資料庫層的衝突只在整合測試驗證。這個劃法有成本：Service 裡的每一個查詢，在單元測試和 Oracle 上各有一個測試覆蓋，兩邊都要維護。判準很簡單，測試失敗或通過時，你是否相信它在 Oracle 上也成立？如果答案是「不一定」，它就不屬於單元測試。深度篇對 InMemory 的立場更保守，連單元測試也建議避開，見 [[20-testing]]。

---

## 四、整合測試：讓請求走過真實的 pipeline

單元測試通過後，剩下的風險全在「接起來」的部分。`WebApplicationFactory<TEntryPoint>` 就是為此設計的：它用應用程式本身的 `Program` 建出完整的 host，但把 server 換成記憶體內的 TestServer，因此不佔連接埠，也不需要先 `dotnet run`；`CreateClient()` 回傳的 `HttpClient` 直接打進這個 host。

TaskTracker 的工廠繼承 `WebApplicationFactory<Program>`，只做一件事：用組態覆寫替換連線字串與機密。

```csharp
public sealed class ApiFactory : WebApplicationFactory<Program>
{
    private readonly string _connectionString;

    public ApiFactory(string connectionString)
    {
        _connectionString = connectionString;
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureAppConfiguration((_, configuration) => configuration.AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["ConnectionStrings:Default"] = _connectionString,
            ["Jwt:SigningKey"] = ApiFixture.SigningKey,
            ["Seed:Password"] = ApiFixture.SeedPassword,
            ["Database:MigrateOnStartup"] = "true",
            ["Logging:LogLevel:Default"] = "Warning"
        }));
    }
}
```

這裡的設計取捨與 [[basics-09-configuration-and-environments]] 一脈相承：機密永遠不進 repo，測試用的金鑰是只存在於測試程式碼裡的字串，長度超過 HS256 要求的 32 bytes，不對應任何真實環境。`Database:MigrateOnStartup` 打開，讓應用程式啟動時自己套用 migration，所以測試資料庫的結構不是手寫 SQL 建出來的，而是用正式環境會用的 migration，順便驗證了 migration 本身能在 Oracle 上跑通。

預設環境也值得知道：`WebApplicationFactory` 預設以 Development 環境啟動，TaskTracker 還特地寫了一個測試確認這件事。這代表 DI container 會在 `Build()` 時驗證 scope（[[basics-07-dependency-injection-and-services]] 的 captive dependency 會在測試啟動時就炸），是個便宜的附帶好處；也代表測試行為與 Production 在 Development 專屬的設定上會有差異，要記得這個前提。

### Testcontainers：測試啟動一個真的 Oracle

測試需要的是真的 Oracle。Testcontainers 的作法是：測試開始時，用 Docker 啟動一個資料庫容器，測試結束時把它刪掉。`Testcontainers.Oracle` 套件封裝了這件事，TaskTracker 指定映像為 `gvenzl/oracle-free:23-slim-faststart`：

```csharp
public sealed class ApiFixture : IAsyncLifetime
{
    public const string SigningKey = "test-only-signing-key-that-is-longer-than-32-bytes";
    public const string SeedPassword = "Test-Only-Passw0rd!";

    private OracleContainer? _container;
    private ApiFactory? _factory;

    public async ValueTask InitializeAsync()
    {
        if (!DockerAvailability.IsAvailable)
        {
            return;
        }

        _container = new OracleBuilder("gvenzl/oracle-free:23-slim-faststart")
            .WithDatabase("FREEPDB1")
            .Build();
        await _container.StartAsync();
        _factory = new ApiFactory(_container.GetConnectionString());
        using var warmUp = _factory.CreateClient();
    }

    public async ValueTask DisposeAsync()
    {
        if (_factory is not null)
        {
            await _factory.DisposeAsync();
        }

        if (_container is not null)
        {
            await _container.DisposeAsync();
        }
    }
}
```

xUnit v3 的 `IAsyncLifetime` 使用 `ValueTask`，寫成 v2 的 `Task` 版本編譯會失敗。`CreateClient()` 那一行的作用是預熱：第一次建立 client 才會真的啟動 host 並執行 migration，放在 fixture 初始化裡，等於在第一個測試開始之前就把最慢的部分做完。

Oracle 容器啟動很慢。TaskTracker 的實測，全部 72 個測試（含一個容器）約一分鐘，而在筆者機器的另一次執行中，容器通過就緒檢查花了超過一分鐘。如果每個測試類別各自啟動一個容器，總時間會線性增加，所以容器必須共用。xUnit 的 collection fixture 就是這個用途：

```csharp
[CollectionDefinition("Api")]
public sealed class ApiCollection : ICollectionFixture<ApiFixture>
{
}
```

所有標了 `[Collection("Api")]` 的測試類別共用同一個 `ApiFixture`，所以整個測試回合只啟動一個 Oracle、一個 host。代價是同一個 collection 內的測試不會平行執行，且共用同一份資料，這帶出下面兩節的問題。

---

## 五、測試裡的認證：走真實登入

TaskTracker 的端點幾乎都需要 token，整合測試怎麼過這一關有兩條路。第一條是替換掉 authentication handler，讓所有請求自動視為某個角色，測試寫起來最短。第二條是跟真實使用者一樣：先呼叫 `POST /api/v1/auth/login` 拿 JWT，再放進 `Authorization` header。

TaskTracker 選第二條，理由寫在 fixture 的註解裡：JWT 驗證參數、claim 對應與 policy 是最容易設錯的地方，換成測試用的 handler，這些會全部被繞過，測試變綠而什麼都沒驗證。前面那個把 `TasksDelete` 改成 `TasksWrite` 的錯誤，如果測試是用假的 handler，handler 會直接給出所有權限，不會抓到。深度篇示範的是註冊測試專用 authentication scheme 的做法（見 [[20-testing]]），那是登入流程很慢或很難重現時的權衡；TaskTracker 的登入只是一次 `POST`，每個角色只做一次，沒有理由放棄驗證真實的 JWT 設定。

```csharp
public async Task<HttpClient> CreateClientAsync(string? role, CancellationToken ct)
{
    var client = CreateClient();
    if (role is not null)
    {
        client.DefaultRequestHeaders.Authorization = new("Bearer", await TokenAsync(role, ct));
    }

    return client;
}

public async Task<string> TokenAsync(string role, CancellationToken ct)
{
    if (_tokens.TryGetValue(role, out var cached))
    {
        return cached;
    }

    using var client = CreateClient();
    var response = await client.PostAsJsonAsync("/api/v1/auth/login", new { email = $"{role}@example.com", password = SeedPassword }, ct);
    response.EnsureSuccessStatusCode();
    var login = await response.Content.ReadFromJsonAsync<LoginResponse>(ct);
    return _tokens.GetOrAdd(role, login!.AccessToken);
}
```

測試資料庫在啟動時會由應用程式啟動時的種子機制建立三個帳號（`viewer@example.com`、`editor@example.com`、`admin@example.com`），密碼就是 `Seed:Password` 組態值。每個角色只登入一次，之後重複使用同一個 token，因為密碼雜湊是刻意設計得很慢的運算，每個測試都重新登入會讓測試套件慢上許多。`role` 為 `null` 代表不帶 token 的匿名請求，用來驗證 401。

認證也有專屬的測試。`AuthApiTests` 驗證錯誤密碼與不存在的帳號回同樣的 401（避免洩漏帳號是否存在）、缺少 token 時回帶 `WWW-Authenticate: Bearer` 的 401、被另一把金鑰簽出來的 token 一律被拒絕。最後一個尤其重要：它確認的是「驗證簽章」這個行為真的有發生，而不是只有「合法 token 能通過」。

---

## 六、測試資料的隔離

共用一個資料庫意味著測試之間可能互相影響：A 測試建立的任務出現在 B 測試的列表裡，B 的總數斷言就會偶爾失敗。常見的隔離策略有三種：每個測試包一個交易最後回滾，每個測試前清空資料表，或者每個測試只用自己獨有的資料。

TaskTracker 選第三種，用最簡單的方式實作：標題一律加上 `Guid`，彼此不衝突。

```csharp
private static string UniqueTitle(string prefix) => $"{prefix} {Guid.NewGuid():N}";
```

交易回滾的問題是，整合測試走的是 HTTP，請求在伺服器端自己開自己的 DbContext 與交易，測試沒辦法把它們包進同一個交易；要做就得把應用程式的 DbContext 換成共用同一條連線與交易的版本，等於動了正式的接線，驗證的就不是原本那套程式了。清空資料表（例如 Respawn 之類的工具）可靠，但每次清空都要付出時間，而且在共用 collection 下測試不能平行。唯一標題的做法最快，但它對測試的寫法有約束：斷言不能依賴全域狀態。比如分頁測試只能斷言 `TotalCount >= 3` 而不是 `== 3`，因為資料庫裡可能還有別的測試留下的任務；篩選測試則斷言「回傳的每一筆都是 done」與「我建立的那一筆在裡面」，而不是整個列表等於什麼。

```csharp
var page = await client.GetFromJsonAsync<PagedResponse<TaskResponse>>("/api/v1/tasks?page=1&pageSize=2", Ct);

Assert.Equal(2, page!.Items.Count);
Assert.Equal(2, page.PageSize);
Assert.True(page.TotalCount >= 3);
```

這個取捨有明確的缺點：忘了用唯一值的測試會在某次執行時意外撞上別人的資料，而且是偶發失敗，最難除錯。深度篇偏向每個測試前清空資料的做法，取捨是更慢但測試真正獨立（見 [[20-testing]]）。選哪一種，看測試套件的規模：TaskTracker 現階段只有幾十個整合測試，唯一資料夠用；當測試要驗證精確的全域數字（報表、統計）時，就該改成清空資料。

資料隔離之外，還有一個測試只能在真實資料庫上寫：直接繞過 Service 的重複檢查，把兩筆相同標題寫進 `DbContext`，斷言資料庫的唯一索引會擋下並丟出 `DbUpdateException`。Service 裡的檢查只是第一道防線（給使用者友善的 409），並發的兩個請求同時通過檢查的話，唯一索引才是最後防線，這個測試證明最後防線真的存在。InMemory 做不到這件事，因為它不強制唯一索引。

---

## 七、沒有 Docker 的時候

整合測試依賴 Docker。新同事剛拉下 repo、公司電腦沒裝 Docker、CI runner 沒開 Docker daemon，這些情況都會發生。如果測試的處理方式是直接丟例外，那麼 `dotnet test` 一跑就是幾十個紅燈，看起來像是程式壞了，實際上只是環境缺東西。

TaskTracker 的處理是讓整合測試在沒有 Docker 時明確標示為「跳過」，而且附上原因。實作分兩步。第一步是在測試程式啟動時探測一次 `docker info`，結果快取在靜態屬性：

```csharp
public static class DockerAvailability
{
    public const string SkipReason = "Docker is not available, so the Oracle container cannot start.";

    public static bool IsAvailable { get; } = Probe();

    private static bool Probe()
    {
        try
        {
            using var process = Process.Start(new ProcessStartInfo("docker", "info --format {{.ServerVersion}}")
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            });
            if (process is null)
            {
                return false;
            }

            if (!process.WaitForExit(TimeSpan.FromSeconds(20)))
            {
                process.Kill(entireProcessTree: true);
                return false;
            }

            return process.ExitCode == 0;
        }
        catch (Exception)
        {
            return false;
        }
    }
}
```

第二步是自訂 `[OracleFact]` 與 `[OracleTheory]`，在 xUnit v3 的 `SkipUnless` 機制上封裝，整合測試只要用它們取代 `[Fact]`、`[Theory]`：

```csharp
public sealed class OracleFactAttribute : FactAttribute
{
    public OracleFactAttribute([CallerFilePath] string? sourceFilePath = null, [CallerLineNumber] int sourceLineNumber = -1)
        : base(sourceFilePath, sourceLineNumber)
    {
        Skip = DockerAvailability.SkipReason;
        SkipUnless = nameof(DockerAvailability.IsAvailable);
        SkipType = typeof(DockerAvailability);
    }
}
```

`ApiFixture.InitializeAsync` 在探測失敗時直接 `return`，不嘗試啟動容器，所以跳過的測試根本不會碰到不存在的工廠。實測的做法是把 `docker` 從 `PATH` 拿掉再跑完整測試。輸出（只留跳過的幾行與總結）：

```text
skipped TaskTracker.Api.Tests.Integration.TasksApiTests.Create_with_a_duplicate_title_returns_409_problem_details
skipped TaskTracker.Api.Tests.Integration.TasksApiTests.The_permission_matrix_holds(role: "editor", operation: "delete", expected: Forbidden)
...

Test run summary: Passed!
  total: 72
  failed: 0
  succeeded: 30
  skipped: 42
  duration: 3s 008ms
```

72 個測試裡 30 個單元測試照跑，42 個整合測試被跳過，整個回合用 3 秒，結束碼是 0（成功）。

這個設計有一個必須知道的陷阱：跳過不算失敗，所以沒有 Docker 的環境會看到綠燈。本機開發時這是合理的，開發者可以用 `dotnet test --project tests/TaskTracker.Api.Tests --filter-namespace "TaskTracker.Api.Tests.Unit"` 明確只跑單元測試，不需要 Docker。但 CI 上這會變成漏洞：runner 的 Docker 一旦壞掉，管線仍是綠的，整合測試卻整批沒跑。因此在 CI 要把「跳過 0 個」當作條件，或至少看一眼總結裡的 `skipped` 數字，這個檢查如何寫進 GitHub Actions，留到 [[basics-16-deployment-and-go-live]]。

---

## 八、故意弄壞程式，看測試變紅

回到本章開頭的情境，用實驗看兩層測試各自的反應。以下實驗都在 TaskTracker 的複本上做，做完還原。

### 實驗一：改壞 Service 的規則

`TaskService.EnsureTitleIsUniqueAsync` 有一行：更新時，重複檢查要排除任務自己。

```csharp
if (exceptId is { } id)
{
    sameTitle = sameTitle.Where(t => t.Id != id);
}
```

把中間那行改成 `sameTitle = sameTitle;`（模擬重構時不小心弄丟條件）。編譯器只給一個警告 CS1717，建置成功。跑單元測試：

```powershell
dotnet test --project tests/TaskTracker.Api.Tests --no-build --filter-namespace "TaskTracker.Api.Tests.Unit"
```

```text
failed TaskTracker.Api.Tests.Unit.TaskServiceTests.Update_keeping_its_own_title_is_not_a_conflict (3ms)
  Xunit.MicrosoftTestingPlatform.XunitException: TaskTracker.Api.Exceptions.ConflictException : A task titled 'Mine' already exists.
failed TaskTracker.Api.Tests.Unit.TaskServiceTests.List_filters_by_status_and_honours_an_explicit_page_size (5ms)
  Xunit.MicrosoftTestingPlatform.XunitException: TaskTracker.Api.Exceptions.ConflictException : A task titled 'Done one' already exists.

Test run summary: Failed!
  total: 30
  failed: 2
  succeeded: 28
  skipped: 0
```

兩個測試變紅：一個正是專門檢查這條規則的，另一個是在準備資料時順手更新自己的標題而受到牽連。失敗訊息直接是 `ConflictException`，加上測試名稱，已經足夠定位。整個回合 5 秒。

### 實驗二：改壞 `[Authorize]` 的 policy

把 `TasksController` 刪除端點的 `Permissions.TasksDelete` 改成 `Permissions.TasksWrite`，這就是開頭那個複製貼上的錯誤。建置同樣成功，0 個錯誤。先跑單元測試：

```text
Test run summary: Passed!
  total: 30
  failed: 0
  succeeded: 30
  skipped: 0
```

30 個全過。單元測試完全看不到這個錯誤，因為屬性只在 pipeline 裡才會被讀取。再跑整合測試中的權限矩陣：

```powershell
dotnet test --project tests/TaskTracker.Api.Tests --no-build --filter-method "*The_permission_matrix_holds*"
```

```text
failed TaskTracker.Api.Tests.Integration.TasksApiTests.The_permission_matrix_holds(role: "editor", operation: "delete", expected: Forbidden) (31ms)
  Assert.Equal() Failure: Values differ
  Expected: Forbidden
  Actual:   NoContent
```

結論一目了然：Editor 刪除任務時預期 403，實際回 204。20 個矩陣案例中只有這 1 個失敗，其餘 19 個通過，所以錯誤範圍也一起被描述了出來。整個過程花了約 1 分半，大部分是啟動 Oracle 容器的時間。這兩個實驗放在一起，剛好是第一節那張表的實例：商業規則壞了，單元測試最快；接線壞了，只有整合測試看得到。

---

## 九、每支 endpoint 該測哪幾種情況

測試永遠寫不完，需要一個判準決定「夠了」。對 TaskTracker 這類 CRUD 端點，每支端點至少要有下面幾類案例，缺一類就有一類錯誤會漏過：

1. 成功路徑，而且要斷言「形狀」：狀態碼（建立是 201 不是 200）、`Location` header 指向帶版本的網址、回應 JSON 的欄位名稱與值的格式（`status` 是 `"todo"`，不是 `"Todo"`）。前端依賴的就是這些。
2. 沒登入是 401，權限不夠是 403，權限夠才成功。三種結果都測，因為 401 與 403 的處理路徑不同（[[basics-11-auth-concepts-and-pipeline]]）。
3. 輸入不合法回 400，並斷言錯誤欄位名稱（`errors` 裡有 `Title`），否則回應格式改了也沒人發現。
4. 資源狀態不對：查無資料回 404，標題重複回 409，並斷言回應是 `application/problem+json`。
5. 副作用真的發生：刪除後再讀一次確認是 404，第二次刪除也是 404；建立後可以用 GET 讀到。只看刪除回 204 不能證明資料真的刪了。
6. 邊界：`pageSize` 超過上限要 400，不是被默默截斷。

權限矩陣是第 2 類的最佳實作。五個操作乘上四種身分（匿名、Viewer、Editor、Admin）共 20 個案例，用 xUnit 的 `[Theory]` 加 `MemberData` 寫成一張表：

```csharp
public static TheoryData<string?, string, HttpStatusCode> PermissionMatrix => new()
{
    { null, "list", HttpStatusCode.Unauthorized },
    { "viewer", "create", HttpStatusCode.Forbidden },
    { "editor", "delete", HttpStatusCode.Forbidden },
    { "admin", "delete", HttpStatusCode.NoContent }
    // 其餘 16 列省略
};

[OracleTheory]
[MemberData(nameof(PermissionMatrix))]
public async Task The_permission_matrix_holds(string? role, string operation, HttpStatusCode expected)
{
    using var admin = await _api.CreateClientAsync("admin", Ct);
    var fixture = await CreateTaskAsync(admin, UniqueTitle("Matrix fixture"));
    using var client = await _api.CreateClientAsync(role, Ct);

    var response = operation switch
    {
        "list" => await client.GetAsync("/api/v1/tasks", Ct),
        "get" => await client.GetAsync($"/api/v1/tasks/{fixture.Id}", Ct),
        "create" => await client.PostAsJsonAsync("/api/v1/tasks", new { title = UniqueTitle("Matrix create") }, Ct),
        "update" => await client.PutAsJsonAsync($"/api/v1/tasks/{fixture.Id}", new { title = UniqueTitle("Matrix update"), status = "done" }, Ct),
        "delete" => await client.DeleteAsync($"/api/v1/tasks/{fixture.Id}", Ct),
        _ => throw new ArgumentOutOfRangeException(nameof(operation))
    };

    Assert.Equal(expected, response.StatusCode);
}
```

這張表就是 [[basics-13-permissions-with-frontend]] 那張權限矩陣的可執行版本：文件裡的表格和測試裡的表格若不一致，測試會先紅。以後新增角色或端點，補一列，不需要新增測試方法。

最後是什麼不值得測：框架本身的行為（`[Required]` 是否生效，除非是驗證 TaskTracker 自己的設定）、只是把呼叫轉給下一層的 getter、為了湊覆蓋率而斷言「方法有被呼叫」的 mock 驗證。判準是：這個測試失敗時，是不是代表使用者可見的行為壞了？如果不是，它多半在測實作細節，下一次重構就會無故變紅，讓人養成「紅燈沒什麼」的習慣，這比沒有測試更糟。

OpenAPI 文件也是行為的一部分。`OpenApiTests` 驗證 v1 文件宣告了 Bearer scheme，且只有受保護的操作帶 `security`、`status` 在文件裡是小寫字串，這是上一章的成果被守住的方式。

---

## 十、本章留給進階篇的題目

單元測試裡 mock 的邊界要劃在哪裡（TaskTracker 刻意不 mock `DbContext`）、時間注入在排程與逾時情境怎麼用、背景服務怎麼測、測試組織與命名慣例，這些是 [[20-testing]] 的主題。測試專案怎麼進 CI 管線，以及 CI 上怎麼確認「跳過 0 個」，在 [[basics-16-deployment-and-go-live]] 接手。

---

## 常見誤解

**「測試資料庫用 InMemory 或 SQLite 就好，跟真的差不多。」** InMemory 沒有唯一約束、外鍵與真實交易，LINQ 也永遠不會翻譯失敗；SQLite 的型別、字串比較與鎖定行為與 Oracle 不同。要驗證資料庫相關行為，就要用同一種資料庫，Testcontainers 啟動真實 Oracle 是目前最可重現的做法。

**「整合測試全綠，就不需要單元測試了。」** 整合測試每個要走完整條 pipeline 並碰資料庫，能窮舉的分支有限，失敗時也只告訴你「回了 409 不是 200」，要自己往回推原因。業務規則的各種邊界仍然應該用單元測試窮舉。

**「測試覆蓋率 90% 就代表安全。」** 覆蓋率只說明哪些程式碼被執行過，沒說明有沒有被檢查。本章實驗二的改壞版本，單元測試的覆蓋率不會變，30 個全過，錯誤卻確實存在。

**「沒有 Docker 的環境，整合測試一定會失敗。」** TaskTracker 的整合測試會明確跳過，結束碼為 0；這比失敗溫和，也比失敗更容易被忽略。CI 上要檢查 `skipped` 為 0。

**「為了方便，整合測試把 authentication 換成假的 handler 就好。」** 假 handler 會繞過 JWT 驗證參數、claim 對應與 policy 三個最容易設錯的地方，測試變綠，而這三處正是最需要保護的。除非測試的主題不是授權、且測試套件因為登入而慢到無法接受，否則走真實登入。

---

## 同事會來問你的問題

**Q：測試要不要 mock `DbContext`？**
TaskTracker 的選擇是不 mock。`DbContext` 與 LINQ 的行為太複雜，mock 出來的版本幾乎一定與真實行為不同，測試變成在驗證自己寫的 mock。需要隔離資料庫的規則測試，用 EF Core InMemory 加上前面的界線；需要驗證資料庫行為的，直接用 Testcontainers。

**Q：整合測試太慢，每次存檔都跑怎麼辦？**
不要每次存檔都跑。單元測試用 `--filter-namespace` 單獨執行，30 個測試約 5 秒，可以頻繁跑；整合測試在 push 前或 CI 上跑。容器共用一個 fixture，是把時間壓低的第一步，不要每個測試類別各啟動一個容器。

**Q：測試通過了，是不是可以直接部署？**
測試通過說明「你寫下來的預期」成立，沒寫下來的行為不在保證範圍。部署前還要有環境面的檢查（設定、健康檢查、映像），見 [[basics-16-deployment-and-go-live]]。

**Q：FluentAssertions 授權改了，要不要換？**
取決於公司：商業專案使用 8.x 以上要付授權費。TaskTracker 的方案是只用 xUnit `Assert`，沒有額外相依。要流暢語法時，考慮 AwesomeAssertions 或 Shouldly，或是停在 7.x（Apache-2.0）。

**Q：為什麼不是每個測試前清空資料庫？**
TaskTracker 的整合測試走 HTTP，伺服器端自己開交易，所以交易回滾做不到；清空資料表可靠但慢，也不能平行。目前用唯一資料避免衝突，條件是斷言不依賴全域狀態。測試要驗精確總數時再改成清空。

---

## 這章的位置

學完這一章，你能替 Web API 專案建出 xunit.v3 測試專案，在 .NET 10 下設定好 `global.json` 讓 `dotnet test` 能跑；用單元測試釘住 Service 的商業規則，用 `WebApplicationFactory` 加真實的 Oracle 容器驗證整條 pipeline；知道為什麼不用 InMemory 與 SQLite 當整合測試資料庫、為什麼走真實登入而不換 authentication handler；也能判斷一支 endpoint 該測哪幾類案例，並讀懂「跳過」與「失敗」的差別。想看 mock 邊界、時間注入、背景服務測試的深入做法，見 [[20-testing]]。

測試只是在開發機與 CI 上證明程式沒壞。下一章 [[basics-16-deployment-and-go-live]] 處理另一端的問題：程式要上線時，如何記錄、如何知道它還活著，以及怎麼把它放進容器。

---

## 連結

- 上一章：[[basics-14-openapi-and-versioning]]
- 下一章：[[basics-16-deployment-and-go-live]]
- 對應深度章：[[20-testing]]
- 本章用到的先修內容：[[basics-07-dependency-injection-and-services]]、[[basics-09-configuration-and-environments]]、[[basics-11-auth-concepts-and-pipeline]]、[[basics-12-jwt-login]]、[[basics-13-permissions-with-frontend]]
- 總目錄：[[dotnet-web-api]]
