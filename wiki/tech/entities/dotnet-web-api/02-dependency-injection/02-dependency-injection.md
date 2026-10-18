---
type: concept
domain: tech
tags: [dotnet, aspnet, dependency-injection, di, lifetime, scope, idisposable]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 02 章：依賴注入 — Scope 是誰開的、誰負責關

## 一個過得了 code review 的 bug

```csharp
public class CacheService
{
    private readonly Dictionary<int, User> _cache = new();
    private readonly AppDbContext _db;

    public CacheService(AppDbContext db)
    {
        _db = db;
    }

    public async Task<User?> GetUserAsync(int id)
    {
        if (_cache.TryGetValue(id, out var cached)) return cached;

        var user = await _db.Users.FindAsync(id);
        if (user is not null) _cache[id] = user;
        return user;
    }
}

builder.Services.AddSingleton<CacheService>();
builder.Services.AddDbContext<AppDbContext>(opt => opt.UseOracle(cs));
```

這段程式碼看起來完全合理：一個快取服務，快取當然要 Singleton 才有意義，不然每個 request 一份快取等於沒快取。

它會在 Development 環境啟動時直接爆炸（`Cannot consume scoped service 'AppDbContext' from singleton 'CacheService'`），在 Production 環境則**安靜地跑起來**，然後在流量上來之後開始出現這些症狀：

- 偶發的 `A second operation was started on this context before a previous operation completed`
- 記憶體持續成長，重啟後歸零，過幾天又滿
- 使用者回報看到別人的舊資料
- 資料庫連線數莫名居高不下

四個症狀，一個根因。要能從症狀反推到這裡，就必須知道 scope 是誰建立的、什麼時候釋放、以及當一個 Scoped 物件被 Singleton 抓住的時候，這條規則是怎麼被繞過的。

第 00 章提過 captive dependency 這個詞，這一章把它徹底講完。

---

## 一、三個型別，三個階段

DI 在 ASP.NET Core 裡有清楚的三段式結構，混淆它們是很多困惑的來源。

| 型別 | 階段 | 本質 |
| --- | --- | --- |
| `ServiceDescriptor` | 描述 | 一筆記錄：什麼型別、怎麼建、活多久 |
| `IServiceCollection` | 註冊 | 一個 `List<ServiceDescriptor>` |
| `IServiceProvider` | 解析 | 能把型別變成實例的容器 |

`builder.Services.AddScoped<IUserService, UserService>()` 做的事，展開來就是：

```csharp
services.Add(new ServiceDescriptor(
    serviceType: typeof(IUserService),
    implementationType: typeof(UserService),
    lifetime: ServiceLifetime.Scoped));
```

一筆記錄而已。真正建立物件的時機在 `IServiceProvider.GetService()` 被呼叫的那一刻，而那通常發生在請求進來之後。

### 1.1 建構子怎麼選

當容器要建立 `UserService` 時，它會檢查這個型別的所有公開建構子，選擇**參數最多、且所有參數都能被解析**的那一個。

```csharp
public class UserService
{
    public UserService() { }                                    // 候選 1
    public UserService(IUserRepository repo) { }                // 候選 2
    public UserService(IUserRepository repo, ILogger<UserService> log) { }   // 候選 3
}
```

三個都能滿足的話選候選 3。如果 `IUserRepository` 沒註冊，候選 2 和 3 都不可行，就選候選 1。

這個規則有一個副作用值得警惕：**忘記註冊某個依賴時，容器可能悄悄選了較短的建構子，而不是報錯**。於是服務跑起來了，只是某個功能靜靜地不作用。實務建議是**每個服務只留一個公開建構子**——這樣缺依賴時會直接拋出明確的 `Unable to resolve service for type 'X'`，錯誤在啟動或第一次解析時就顯性化。

也是因為這條規則，第 00 章建議的 `ValidateOnBuild = true` 特別有價值：它在啟動時就把所有註冊試著解析一遍，把「缺依賴」從執行期問題變成啟動期問題。

---

## 二、Scope 是誰開的

三種 lifetime 的教科書定義大家都會背，但真正決定行為的問題是：**「一個 scope」的邊界是誰畫的？**

答案是：ASP.NET Core 在**每個 HTTP request 開始時建立一個 scope，在 request 結束時釋放它**。這件事發生在 pipeline 的最外層，比你寫的任何 middleware 都早。

```text
Kestrel 收到請求
  └── 建立 IServiceScope                      ← scope 開始
        └── HttpContext.RequestServices = scope.ServiceProvider
              └── 執行 middleware pipeline
                    └── Controller、Service、DbContext 都從這個 scope 解析
        └── scope.Dispose()                    ← scope 結束
```

`HttpContext.RequestServices` 就是那個 scope 的 provider。Controller 的建構子注入、middleware 的 `InvokeAsync` 參數注入，全都從它解析。

於是三種 lifetime 的語意變得具體：

| Lifetime | 實例存放在哪 | 何時建立 | 何時釋放 |
| --- | --- | --- | --- |
| Singleton | root provider | 第一次被解析時（或註冊實例時立刻） | 應用程式關閉、root provider dispose |
| Scoped | 當前 scope | 該 scope 中第一次被解析時 | scope dispose（request 結束） |
| Transient | 不快取，每次新建 | 每次解析 | **由解析它的 scope 負責**（見第四節） |

「Scoped = 每個 request 一個」是**結論**，不是定義。定義是「每個 scope 一個」，而 request 剛好各自有一個 scope。這個區別在背景服務裡會變得關鍵——`BackgroundService` 沒有 request，也就沒有人替你開 scope。

---

## 三、Captive Dependency：規則是怎麼被繞過的

回到開頭那段程式碼。

`CacheService` 是 Singleton，它在應用程式生命週期內只被建立一次。建立的那一刻，容器要滿足它的建構子參數 `AppDbContext`，於是解析出一個 DbContext 實例，**存進 `CacheService` 的欄位**。

從此之後，這個 DbContext 的實際壽命等於 `CacheService` 的壽命——也就是整個應用程式。它被「俘虜」了。DI 註冊上寫的 Scoped 完全失效，因為壽命不是由註冊決定的，而是**由誰持有它的參考決定的**。

一個物件的實際壽命 = 持有它的那個物件的壽命。這是垃圾回收的基本事實，DI 容器沒辦法違反它。

四個症狀因此可以逐一解釋：

**`A second operation was started on this context`**——DbContext 不是執行緒安全的，設計上假設「同一時間只有一個操作」。變成 Singleton 後，多個並行 request 同時用它查資料，兩個查詢撞在一起就是這個錯誤。

**記憶體持續成長**——DbContext 的 change tracker 會記住所有查詢出來的實體（用於偵測變更）。正常情況下 request 結束就整個丟掉。變成 Singleton 之後永遠不丟，每查一筆就多累積一筆，直到 OOM。

**看到別人的舊資料**——change tracker 有 identity map 語意：同一個 key 查第二次，直接回傳快取中的實例而不打資料庫。資料在別處被改了，這個 Singleton DbContext 也不知道。

**連線數居高不下**——實際上這個症狀比較間接，但長壽的 DbContext 加上未被釋放的 tracking 狀態，會讓連線池的行為變得難以預測。

### 3.1 一般規則

**一個服務只能依賴壽命大於或等於自己的服務。**

| 消費者 | 可以依賴 | 不可以依賴 |
| --- | --- | --- |
| Singleton | Singleton | Scoped、Transient（若持有參考） |
| Scoped | Singleton、Scoped | Transient（若跨 scope 持有） |
| Transient | 全部 | — |

「Transient 被 Singleton 注入」同樣是問題——那個 Transient 實例也會活到應用程式結束。Transient 的語意是「每次都給新的」，被 Singleton 抓住之後就只有那一個了。

框架的 scope validation 只檢查 Scoped 被 Singleton 消費這一種（因為那個最危險），Transient 的情況不檢查。所以不能完全依賴檢查器。

### 3.2 Singleton 真的需要 Scoped 服務時怎麼辦

這個需求本身是合理的：一個 Singleton 的背景排程器，每隔五分鐘要去資料庫撈資料。解法是**不要持有它，而是需要的時候自己開 scope**：

```csharp
public class SyncWorker : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory;   // Singleton，安全

    public SyncWorker(IServiceScopeFactory scopeFactory)
    {
        _scopeFactory = scopeFactory;
    }

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            // 每一輪開一個 scope，用完釋放——語意等同於「一次 request」
            using (var scope = _scopeFactory.CreateScope())
            {
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                await DoSyncAsync(db, ct);
            }

            await Task.Delay(TimeSpan.FromMinutes(5), ct);
        }
    }
}
```

`IServiceScopeFactory` 本身是 Singleton，注入它完全安全。關鍵是那個 `using`——**scope 一定要釋放**，否則裡面所有 Scoped 服務（包含 DbContext 及其資料庫連線）都不會被回收。少寫這個 `using`，症狀會是「跑幾天之後連線池耗盡」，而且極難追查。

scope 的邊界該畫在哪裡也要想清楚。上面的例子把 scope 開在迴圈**內**，每一輪一個新的 DbContext。如果開在迴圈外，就變成一個活了好幾天的 DbContext——又回到 captive dependency 的處境。**一個 scope 對應一個邏輯工作單元**，這是選擇邊界的判準。

回到開頭的 `CacheService`，正確的寫法是：

```csharp
public class CacheService
{
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly IMemoryCache _cache;              // Singleton，執行緒安全

    public CacheService(IServiceScopeFactory scopeFactory, IMemoryCache cache)
    {
        _scopeFactory = scopeFactory;
        _cache = cache;
    }

    public async Task<User?> GetUserAsync(int id)
    {
        if (_cache.TryGetValue<User>(id, out var cached)) return cached;

        using var scope = _scopeFactory.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var user = await db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Id == id);

        if (user is not null)
        {
            _cache.Set(id, user, TimeSpan.FromMinutes(5));
        }
        return user;
    }
}
```

三個修正同時發生：DbContext 改成用完即棄的短生命週期；`Dictionary` 換成執行緒安全且支援過期的 `IMemoryCache`（原本那個 `Dictionary` 在並行寫入下可能損毀內部結構甚至無限迴圈）；查詢加上 `AsNoTracking()`，因為快取的實體不該掛在任何 change tracker 上。第三點的理由在 [[07-efcore-internals]] 展開。

---

## 四、誰負責 Dispose

這是 DI 裡第二個容易失血的地方，而且比 captive dependency 更隱蔽。

規則是：**容器負責 dispose 它自己建立的、且實作了 `IDisposable` 的實例。** 「它自己建立的」這個限定很重要。

```csharp
// 容器建立 → 容器負責 dispose
builder.Services.AddScoped<IFileService, FileService>();

// 你建立的實例 → 容器不負責（.NET 6+ 的行為）
builder.Services.AddSingleton(new FileService());
```

釋放的時機：

- **Scoped**：scope dispose 時（request 結束）
- **Singleton**：root provider dispose 時（應用程式關閉）
- **Transient**：**由解析它的那個 scope 負責，在該 scope 結束時**

最後一條是陷阱所在。很多人以為 Transient 是「用完就丟、由 GC 回收」，但如果它實作了 `IDisposable`，容器**必須**追蹤它才能在適當時機呼叫 `Dispose()`——於是容器在 scope 裡保留了一份參考。

在 request scope 裡這通常沒事（request 很短）。但在長壽的 scope 裡就是洩漏：

```csharp
builder.Services.AddTransient<IReportGenerator, ReportGenerator>();   // 實作 IDisposable

// ❌ 從 root provider 解析 Transient + IDisposable
var gen = app.Services.GetRequiredService<IReportGenerator>();
```

root provider 的壽命是整個應用程式。每解析一次，容器就在 root 的清單裡多記一筆，永遠不釋放。這是典型的「跑一個月才 OOM」型記憶體洩漏——壓測跑不出來，因為它需要時間累積。

實務準則：

1. **`IDisposable` 的服務不要註冊成 Transient**，改用 Scoped，讓 request 邊界替你收尾
2. **不要從 root provider（`app.Services`）解析 Transient**，一定要開 scope
3. 需要在方法內建立可拋棄物件時，考慮改用工廠模式明確管理生命週期
4. `IAsyncDisposable` 的服務**必須**在支援非同步釋放的 scope 中解析——用 `await using` 建立 scope，否則會拋 `InvalidOperationException`

---

## 五、註冊的各種形態

### 5.1 工廠註冊

當建立邏輯不只是「呼叫建構子」時：

```csharp
builder.Services.AddScoped<IPaymentGateway>(sp =>
{
    var config = sp.GetRequiredService<IConfiguration>();
    var mode = config["Payment:Mode"];
    return mode == "sandbox"
        ? new SandboxGateway()
        : new LiveGateway(config["Payment:ApiKey"]!);
});
```

`sp` 是當前 scope 的 provider，可以在裡面解析其他服務。注意工廠委派每次解析都會執行（Singleton 除外，只執行一次），所以裡面別放重活。

### 5.2 開放泛型

```csharp
builder.Services.AddScoped(typeof(IRepository<>), typeof(EfRepository<>));
```

之後注入 `IRepository<User>` 會拿到 `EfRepository<User>`。這是 Repository 泛型化的標準做法，也是 `ILogger<T>` 能對任何 `T` 生效的原理。

### 5.3 TryAdd 與 Replace

```csharp
services.TryAddScoped<IEmailService, SmtpEmailService>();   // 已有註冊就不加
services.Replace(ServiceDescriptor.Scoped<IEmailService, FakeEmailService>());   // 取代
services.RemoveAll<IEmailService>();
```

寫函式庫時用 `TryAdd` 提供預設實作，讓使用者可以覆蓋。整合測試時用 `Replace` 把真實服務換成假的，這在 [[20-testing]] 是核心技巧。

### 5.4 Keyed Services（.NET 8+）

同一個介面要有多個具名實作時，過去只能靠工廠或包一層 resolver。.NET 8 起有原生支援：

```csharp
builder.Services.AddKeyedScoped<INotifier, EmailNotifier>("email");
builder.Services.AddKeyedScoped<INotifier, SmsNotifier>("sms");

public class OrderService
{
    public OrderService([FromKeyedServices("email")] INotifier notifier) { }
}
```

需要 .NET 8 以上。在 .NET 6/7 專案裡看到有人用 `Func<string, INotifier>` 或自訂 factory 介面，通常就是在補這個缺口。

---

## 六、反模式

### 6.1 Service Locator

```csharp
// ❌ 注入 IServiceProvider，需要什麼自己拿
public class OrderService
{
    private readonly IServiceProvider _sp;

    public OrderService(IServiceProvider sp) { _sp = sp; }

    public async Task ProcessAsync()
    {
        var payment = _sp.GetRequiredService<IPaymentGateway>();
        var notifier = _sp.GetRequiredService<INotifier>();
        // ...
    }
}
```

這叫 Service Locator，它讓 DI 的主要好處全部消失：**依賴關係從建構子簽章上消失了**。看這個類別的宣告，你不知道它需要什麼；寫測試時不知道要準備什麼 mock；容器的啟動驗證也檢查不出缺漏，因為解析發生在方法執行時。

例外情況確實存在（動態決定要用哪個實作、外掛式架構），但那些情況通常有更好的表達方式——工廠介面、`IEnumerable<T>` 全注入後篩選、或 keyed services。

### 6.2 在 Singleton 裡持有 request 狀態

```csharp
// ❌ 用 Singleton 存當前使用者
public class CurrentUserHolder
{
    public string? UserId { get; set; }   // 所有 request 共用！
}
```

這在低流量測試時「看起來能用」，上線後會出現使用者 A 看到使用者 B 的資料——一種非常嚴重的資安缺陷。request 範圍的狀態要嘛放 Scoped 服務，要嘛從 `IHttpContextAccessor.HttpContext.User` 現拿。

### 6.3 過度使用 Transient

Transient 看起來最安全（每次都新的，不會有共用問題），於是有人全部註冊成 Transient。代價是：

- 每次注入都建立新物件，在深層依賴樹裡是可觀的配置壓力
- 若實作 `IDisposable`，容器會追蹤它們直到 scope 結束（見第四節）
- 失去「同一個 request 內共用同一實例」的能力——這在需要共用交易或快取的場景是必要的

判斷順序建議是：**預設 Scoped；確定無狀態且執行緒安全就 Singleton；只有真的需要「每次都是全新、且很輕」時才 Transient。**

---

## 七、決策表

| 服務類型 | 建議 lifetime | 理由 |
| --- | --- | --- |
| `DbContext` | Scoped | 非執行緒安全、change tracker 需要 request 邊界 |
| Repository / 業務 Service | Scoped | 通常依賴 DbContext，必須跟著它 |
| 純運算工具（無狀態） | Singleton | 沒有共用風險，省去重複建立 |
| 設定物件（`IOptions<T>`） | Singleton | 框架已處理，直接注入 |
| `HttpClient` 相關 | 用 `IHttpClientFactory` | 有自己的生命週期管理，見 [[18-resilience-and-performance]] |
| 記錄「當前使用者」 | Scoped | request 範圍的狀態 |
| 快取 | Singleton（`IMemoryCache`） | 跨 request 才有意義，但內部必須執行緒安全 |
| 背景排程器 | Singleton（`BackgroundService`） | 用 `IServiceScopeFactory` 取得 Scoped 依賴 |

---

## 八、常見誤解

**「Scoped 就是每個 HTTP request 一個。」**
是「每個 scope 一個」，request 剛好各有一個 scope。背景服務、gRPC 串流、SignalR 連線的 scope 邊界都不同，`BackgroundService` 更是完全沒有 scope，要自己建。

**「Singleton 比較快，能用就用。」**
Singleton 只省下建立成本，通常微不足道。它帶來的是執行緒安全責任——所有欄位都可能被並行存取。用錯的代價遠大於省下的那點時間。

**「Transient 最安全。」**
它會製造更多配置，而且若實作 `IDisposable`，實例會被 scope 追蹤到 scope 結束為止。從 root provider 解析 Transient + `IDisposable` 是標準的記憶體洩漏配方。

**「框架會擋住所有生命週期錯誤。」**
scope validation 只檢查 Singleton 消費 Scoped，且**預設只在 Development 開啟**。Transient 被俘虜、自己用 `new` 繞過容器、透過 Service Locator 動態解析，全都檢查不到。

**「注入 `IServiceProvider` 比較彈性。」**
那是 Service Locator，會讓依賴關係從型別簽章上消失，測試與啟動驗證都失效。需要動態選擇實作時用工廠介面或 keyed services。

---

## 九、同事會來問你的問題

**Q：為什麼 `DbContext` 一定要 Scoped？我改成 Singleton 效能會不會比較好？**
不會比較好，而且會壞。DbContext 非執行緒安全，並行操作會拋 `A second operation was started`；change tracker 會無限累積造成記憶體洩漏；identity map 會讓你讀到過期資料。它的設計假設就是短生命週期。

**Q：`BackgroundService` 裡怎麼用 `DbContext`？直接注入為什麼不行？**
`BackgroundService` 是 Singleton，直接注入 Scoped 的 DbContext 就是 captive dependency。注入 `IServiceScopeFactory`，每一輪工作用 `using var scope = factory.CreateScope()` 開一個 scope，從裡面解析 DbContext。scope 的邊界要對應一個邏輯工作單元。

**Q：服務跑起來了但某個功能沒作用，也沒有任何錯誤，可能是什麼？**
檢查該服務是不是有多個公開建構子。缺少某個依賴時，容器會選擇「參數較少但能滿足」的那個建構子，於是物件建起來了、對應功能卻沒接上。每個服務只留一個公開建構子，缺依賴時就會直接報錯。

**Q：記憶體慢慢漲，重啟就好，壓測又測不出來，怎麼查？**
先找從 root provider（`app.Services`）解析的 Transient + `IDisposable` 組合，以及沒有 `using` 的 `CreateScope()`。這兩者都會讓實例被永久持有，特徵正是「需要時間累積、短時間壓測看不出來」。

**Q：`AddSingleton<IFoo, Foo>()` 和 `AddSingleton<IFoo>(new Foo())` 有差嗎？**
有。前者由容器建立，容器負責在關閉時 dispose；後者是你建立的實例，.NET 6 之後容器不負責釋放。若 `Foo` 持有非受管資源，第二種寫法會漏掉釋放。

**Q：我想在同一個 request 裡讓兩個 Service 共用同一個交易，怎麼做？**
把 DbContext 註冊為 Scoped（預設就是），兩個 Service 也是 Scoped，它們會拿到同一個 DbContext 實例，自然共用同一個交易範圍。這正是「Scoped = 每個 request 一個」的實際用途。交易邊界的完整討論在 [[09-transactions-and-concurrency]]。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[01-request-pipeline]] — 上一章：middleware 的 DI 特例
- [[03-routing-and-endpoints]] — 下一章：endpoint 的選擇與執行
- [[07-efcore-internals]] — DbContext 的 change tracker 與生命週期
- [[19-background-work]] — 背景服務中的 scope 管理
- [[20-testing]] — 用 `Replace` 抽換服務做整合測試
