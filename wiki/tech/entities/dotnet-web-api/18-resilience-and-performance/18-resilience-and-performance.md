---
type: concept
domain: tech
tags: [dotnet, aspnet, httpclient, polly, resilience, cache, rate-limiting, circuit-breaker, performance]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 18 章：韌性與效能 — 別讓下游拖垮你

## 一個下游服務變慢，整個系統死掉

架構是：你的 API 在下單流程中呼叫一個外部的付款服務。平常那個呼叫是 100 毫秒。

某天付款服務出了狀況——**沒有掛掉，只是變慢**，回應時間變成 30 秒。接下來發生的事：

```text
1. 下單請求開始堆積，每個都卡在等付款服務 30 秒
2. 每個等待中的請求佔用一條連線、一個 request scope、一份記憶體
3. HttpClient 的連線池被耗盡，新的呼叫連建立連線都要排隊
4. 資料庫連線也被佔住（如果交易包住了外部呼叫，見第 09 章）
5. 你的 API 對「完全不需要付款服務」的請求也開始逾時
6. 上游的服務因為你變慢，也開始堆積
```

**一個下游服務的降級，變成整條鏈的全面中斷。** 這叫級聯故障（cascading failure），而它的根因通常只是一件事：**沒有設定合理的逾時**。

預設的 `HttpClient.Timeout` 是 **100 秒**。在微服務架構裡這個值形同沒有逾時。

這一章講的是怎麼把「下游出問題」控制成「這個功能暫時不可用」，而不是「整個系統死掉」。

---

## 一、`HttpClient` 的三個陷阱

### 1.1 每次 `new HttpClient()` → socket 耗盡

```csharp
// ❌ 每個請求都 new 一個
public async Task<string> GetAsync(string url)
{
    using var client = new HttpClient();
    return await client.GetStringAsync(url);
}
```

`HttpClient` 實作了 `IDisposable`，直覺會用 `using`。但 dispose 之後，底層的 TCP 連線會進入 **TIME_WAIT** 狀態，在作業系統層級停留 4 分鐘左右才真正釋放。

高頻呼叫下，可用的 socket 會被耗盡，症狀是 `SocketException: Only one usage of each socket address is normally permitted`。而且這個錯誤有延遲性——服務跑了一小時才開始出現，重啟後又正常一陣子。

### 1.2 用 Singleton → DNS 過期

於是有人改成靜態的單一實例：

```csharp
// ❌ 另一個問題
private static readonly HttpClient _client = new();
```

Socket 耗盡解決了，但產生新問題：`HttpClient` 建立連線後會**永久保持**，不會重新解析 DNS。當下游服務的 IP 變了（K8s Pod 重新排程、藍綠部署切換、雲端服務的 IP 輪替），這個 client 仍然往舊的 IP 送——直到重啟應用程式為止。

### 1.3 正解：`IHttpClientFactory`

它把兩個問題分開解決：**`HttpMessageHandler`（持有連線池）被池化重用，而 `HttpClient` 本身是輕量的短命物件。** Handler 有生命週期（預設 2 分鐘），到期後被回收重建，於是 DNS 會被重新解析。

三種用法：

```csharp
// 基本
builder.Services.AddHttpClient();

// 具名
builder.Services.AddHttpClient("payment", client =>
{
    client.BaseAddress = new Uri("https://payment.example.com/");
    client.Timeout = TimeSpan.FromSeconds(10);
    client.DefaultRequestHeaders.Add("X-Api-Version", "2");
});

// Typed client（推薦）
builder.Services.AddHttpClient<IPaymentClient, PaymentClient>(client =>
{
    client.BaseAddress = new Uri("https://payment.example.com/");
    client.Timeout = TimeSpan.FromSeconds(10);
});
```

Typed client 最好——強型別、設定與使用在一起、可以直接注入介面、容易 mock 測試：

```csharp
public class PaymentClient : IPaymentClient
{
    private readonly HttpClient _http;

    public PaymentClient(HttpClient http) { _http = http; }

    public async Task<PaymentResult> ChargeAsync(ChargeRequest req, CancellationToken ct)
    {
        var response = await _http.PostAsJsonAsync("charge", req, ct);
        response.EnsureSuccessStatusCode();
        return (await response.Content.ReadFromJsonAsync<PaymentResult>(ct))!;
    }
}
```

**Typed client 註冊的生命週期是 Transient**，所以不要在裡面存跨請求的狀態。也不要把 typed client 注入 Singleton 服務——那會把它變成長壽物件，繞過 handler 輪替機制。

---

## 二、逾時：三個層次

```csharp
// 層次 1：HttpClient 整體逾時（預設 100 秒 —— 一定要改）
client.Timeout = TimeSpan.FromSeconds(10);

// 層次 2：單次呼叫的取消
using var cts = CancellationTokenSource.CreateLinkedTokenSource(requestAborted);
cts.CancelAfter(TimeSpan.FromSeconds(5));
await _http.GetAsync(url, cts.Token);

// 層次 3：Polly 的 timeout 策略（可以只套用在重試的單次嘗試上）
```

**逾時設定的原則：從外往內遞減。**

```text
使用者的耐心         30 秒
  你的 API 的逾時    25 秒
    下游呼叫的逾時    5 秒（含重試總計 15 秒）
      單次嘗試        5 秒
```

內層逾時大於外層是常見的錯誤——外層已經放棄了，內層還在等，那些等待中的資源就是白白佔用的。

第 06 章講的 `CancellationToken` 傳遞在這裡有直接價值：客戶端斷線時，`RequestAborted` 被觸發，如果一路傳到 `HttpClient`，那個外部呼叫會立刻被取消，連線立刻釋放。

---

## 三、重試、斷路器與 .NET 8 的 Resilience

### 3.1 重試的紀律

重試不是「加上去就好」的東西，它有三條紀律：

**只重試冪等操作。** GET 天生冪等；POST 通常不是——重試一次可能扣兩次款。有副作用的操作需要冪等鍵（第 09 章）。

**只重試暫時性錯誤。** 網路逾時、503、429 值得重試；400、401、404 重試一百次也是同樣的結果，只是浪費資源並延後失敗。

**必須有指數退避與 jitter。** 固定間隔的重試會製造「重試風暴」——所有客戶端在同一時刻一起重試，把剛要恢復的下游再次打垮。Jitter（隨機抖動）把重試時間打散：

```text
第 1 次重試：1 秒  ± 隨機
第 2 次重試：2 秒  ± 隨機
第 3 次重試：4 秒  ± 隨機
```

### 3.2 斷路器：不要對著已知故障的服務繼續敲

如果下游已經連續失敗 20 次，第 21 次幾乎不可能成功。繼續嘗試只會：佔用自己的執行緒與連線、讓每個請求都等滿逾時、並且對正在恢復的下游持續施壓。

斷路器有三個狀態：

```text
Closed（正常）
  └─ 失敗率超過閾值 → Open

Open（斷開）
  └─ 所有呼叫立刻失敗，不實際發出請求（快速失敗）
  └─ 等待一段時間 → Half-Open

Half-Open（試探）
  └─ 放行少量請求試探
       ├─ 成功 → Closed
       └─ 失敗 → Open
```

關鍵價值是 **Open 狀態下的快速失敗**——請求在 1 毫秒內就得到「服務不可用」，而不是等 10 秒逾時。這讓你的 API 在下游故障時仍然保持回應能力，只是那個特定功能降級。

### 3.3 .NET 8 的內建支援

```csharp
builder.Services.AddHttpClient<IPaymentClient, PaymentClient>(client =>
{
    client.BaseAddress = new Uri("https://payment.example.com/");
})
.AddStandardResilienceHandler(options =>
{
    options.Retry.MaxRetryAttempts = 3;
    options.Retry.BackoffType = DelayBackoffType.Exponential;
    options.Retry.UseJitter = true;
    options.Retry.DisableForUnsafeHttpMethods();   // 預設連 POST 都會重試

    options.CircuitBreaker.FailureRatio = 0.5;
    options.CircuitBreaker.MinimumThroughput = 10;
    options.CircuitBreaker.BreakDuration = TimeSpan.FromSeconds(30);

    options.AttemptTimeout.Timeout = TimeSpan.FromSeconds(5);
    options.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(20);
});
```

`Microsoft.Extensions.Http.Resilience`（.NET 8+，底層是 Polly v8）提供了一組經過調校的預設值。它組合了五個策略：總逾時 → 重試 → 斷路器 → 單次逾時 → 實際呼叫。

回頭對照 3.1 的紀律有一個陷阱：標準 handler 的重試**預設對所有 HTTP 方法生效，連 POST 也會重試**，不會替你判斷冪等性。呼叫扣款這類非冪等端點時，要用 `options.Retry.DisableForUnsafeHttpMethods()` 把 POST、PUT、PATCH、DELETE 等排除（或用 `DisableFor(HttpMethod.Post)` 指定個別方法），或確定對方支援冪等鍵再放行。

在 .NET 6/7 上用 Polly 直接寫也可以，但這個標準組合省去了「策略順序該怎麼排」的思考——那個順序是有講究的（重試必須包在斷路器外面，否則斷路器開啟時重試會白費）。

### 3.4 降級（fallback）

斷路器開啟時，回什麼？

```csharp
try
{
    return await _paymentClient.GetStatusAsync(orderId, ct);
}
catch (BrokenCircuitException)
{
    _logger.LogWarning("付款服務斷路器開啟，回傳快取狀態");
    return await _cache.GetAsync<PaymentStatus>($"payment:{orderId}", ct)
           ?? PaymentStatus.Unknown;
}
```

**降級是業務決策。** 「顯示稍舊的資料」對商品列表可以接受，對帳戶餘額不行。設計時要問：這個功能不可用時，使用者看到什麼比較好？

---

## 四、快取三層

### 4.1 `IMemoryCache`：程序內

```csharp
builder.Services.AddMemoryCache();

public async Task<Product?> GetProductAsync(int id, CancellationToken ct)
{
    return await _cache.GetOrCreateAsync($"product:{id}", async entry =>
    {
        entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10);
        entry.SetSize(1);
        return await _db.Products.AsNoTracking()
            .FirstOrDefaultAsync(p => p.Id == id, ct);
    });
}
```

最快（沒有序列化、沒有網路），但有兩個限制：

**每個 Pod 一份。** 三個副本就有三份快取，各自獨立過期，使用者可能在不同請求看到不同版本的資料。而且無效化很困難——你沒辦法通知其他 Pod「這筆資料變了」。

**佔用 Pod 的記憶體。** 沒有限制的話會一路長到 OOMKilled（第 07 章的 change tracker 也是類似的機制）。務必設上限：

```csharp
builder.Services.AddMemoryCache(options =>
{
    options.SizeLimit = 10000;      // 設了這個之後，每個項目都必須呼叫 SetSize
});
```

### 4.2 `IDistributedCache`：跨 Pod

```csharp
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "myapp:";
});
```

所有 Pod 共用，可以集中無效化。代價是網路往返與序列化成本（通常 1–5 毫秒），以及 Redis 本身成為一個需要維運的依賴。

**Redis 掛掉時你的 API 要能繼續運作**——快取是最佳化，不是必需品。所有 Redis 操作都應該包容錯：

```csharp
try
{
    var cached = await _cache.GetStringAsync(key, ct);
    if (cached is not null) return Deserialize(cached);
}
catch (Exception ex)
{
    _logger.LogWarning(ex, "快取讀取失敗，回退到資料庫");
}

return await LoadFromDatabaseAsync(ct);
```

### 4.3 Output Caching（.NET 7+）

快取整個 HTTP 回應，連 action 都不執行：

```csharp
builder.Services.AddOutputCache(options =>
{
    options.AddBasePolicy(b => b.Expire(TimeSpan.FromSeconds(30)));
    options.AddPolicy("products", b => b
        .Expire(TimeSpan.FromMinutes(5))
        .SetVaryByQuery("category", "page")
        .Tag("products"));
});

app.UseOutputCache();

[HttpGet]
[OutputCache(PolicyName = "products")]
public async Task<IActionResult> GetProductsAsync(...)
```

它比舊的 Response Caching 好用——**伺服器端儲存**（不依賴客戶端行為）、支援標籤式無效化：

```csharp
await _outputCacheStore.EvictByTagAsync("products", ct);
```

適合公開的、不因使用者而異的內容。要注意**絕對不要對含個人化資料的回應使用**，否則 A 使用者的資料會被快取後回給 B——這是最嚴重的一類資安事故。有 `[Authorize]` 的端點要特別謹慎，或用 `SetVaryByHeader("Authorization")`（但那也讓快取命中率趨近於零）。

### 4.4 Cache Stampede

快取過期的瞬間，如果同時有 100 個請求進來，它們會**同時**發現快取失效，**同時**去查資料庫。這叫快取踩踏，往往在流量高峰時把資料庫打垮——而快取本來是為了保護資料庫的。

`GetOrCreateAsync` 本身不保證只執行一次。要真正防護需要加鎖：

```csharp
private readonly SemaphoreSlim _lock = new(1, 1);

public async Task<Product?> GetAsync(int id, CancellationToken ct)
{
    if (_cache.TryGetValue<Product>($"product:{id}", out var cached)) return cached;

    await _lock.WaitAsync(ct);
    try
    {
        // 雙重檢查：等鎖的期間可能別人已經填好了
        if (_cache.TryGetValue<Product>($"product:{id}", out cached)) return cached;

        var product = await LoadAsync(id, ct);
        _cache.Set($"product:{id}", product, TimeSpan.FromMinutes(10));
        return product;
    }
    finally
    {
        _lock.Release();
    }
}
```

（這個 semaphore 是全域的，會讓不同 key 的載入也互相阻塞。精確的做法是每個 key 一個鎖，或使用現成的函式庫。）

另一個常被忽略的做法是**過期時間加隨機抖動**——避免大量同時建立的快取項目在同一秒集體過期：

```csharp
var ttl = TimeSpan.FromMinutes(10) + TimeSpan.FromSeconds(Random.Shared.Next(0, 120));
```

---

## 五、Rate Limiting（.NET 7+）

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("fixed", o =>
    {
        o.PermitLimit = 100;
        o.Window = TimeSpan.FromMinutes(1);
        o.QueueLimit = 0;
    });

    // 按使用者分別限流
    options.AddPolicy("per-user", context =>
        RateLimitPartition.GetTokenBucketLimiter(
            context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value
                ?? context.Connection.RemoteIpAddress?.ToString()
                ?? "anonymous",
            _ => new TokenBucketRateLimiterOptions
            {
                TokenLimit = 100,
                TokensPerPeriod = 10,
                ReplenishmentPeriod = TimeSpan.FromSeconds(1)
            }));

    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
});

app.UseRateLimiter();

[EnableRateLimiting("per-user")]
public class OrdersController : ControllerBase
```

四種演算法各有適用場景：

| 演算法 | 特性 |
| --- | --- |
| Fixed Window | 簡單，但視窗邊界可能瞬間放行兩倍 |
| Sliding Window | 平滑，成本略高 |
| Token Bucket | **允許突發但長期受限**，最貼近真實需求 |
| Concurrency | 限制同時進行數，適合保護昂貴資源 |

實務上 Token Bucket 通常最合適——使用者偶爾的突發操作不會被擋，持續的濫用會被限制。

**這是程序內的限流，每個 Pod 各自計數。** 三個副本、每個限 100，實際總量是 300。需要全域精確限流得用 Redis 實作分散式計數，或者交給 Ingress / API Gateway 層處理——後者通常是更好的分工（K8s Ingress 有現成的限流 annotation）。

記得回 `Retry-After` header 讓客戶端知道何時能重試：

```csharp
options.OnRejected = async (context, ct) =>
{
    if (context.Lease.TryGetMetadata(MetadataName.RetryAfter, out var retryAfter))
    {
        context.HttpContext.Response.Headers.RetryAfter =
            ((int)retryAfter.TotalSeconds).ToString();
    }
    await context.HttpContext.Response.WriteAsync("請求過於頻繁", ct);
};
```

---

## 六、其他效能項目

**回應壓縮**：

```csharp
builder.Services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;      // 預設關閉（歷史上的 BREACH 攻擊考量）
    options.Providers.Add<BrotliCompressionProvider>();
    options.Providers.Add<GzipCompressionProvider>();
});
app.UseResponseCompression();
```

在 K8s 裡通常由 Ingress 負責壓縮更合適——省下應用程式的 CPU。兩邊都開是浪費。

**JSON 序列化**：`System.Text.Json` 已經很快。極致效能可以用 source generator 消除反射：

```csharp
[JsonSerializable(typeof(ProductDto))]
[JsonSerializable(typeof(List<ProductDto>))]
internal partial class AppJsonContext : JsonSerializerContext { }

builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.TypeInfoResolverChain.Insert(0, AppJsonContext.Default));
```

它也是 AOT 編譯的前提。但除非有實測數據支持，這個最佳化的優先序低於資料庫查詢與快取。

**量測優先於猜測。** 效能問題的順序通常是：資料庫查詢（第 08 章的 N+1）→ 外部呼叫 → 序列化 → 其他。花時間最佳化 JSON 序列化卻放著 N+1 不管，是很常見的錯置。

---

## 七、常見誤解

**「`HttpClient` 要用 `using` 包起來。」**
會導致 socket 耗盡（TIME_WAIT）。用 `IHttpClientFactory`，它池化底層的 handler 而 client 本身是輕量的。

**「用 static `HttpClient` 就解決了。」**
Socket 問題解決了，但連線永不重建，DNS 變更不會被感知。`IHttpClientFactory` 透過 handler 輪替同時解決兩者。

**「重試能提高可用性。」**
只在暫時性錯誤且操作冪等時成立。對 4xx 重試沒有意義；沒有退避與 jitter 的重試會製造重試風暴，把正在恢復的下游再次打垮。

**「快取能解決效能問題。」**
它把問題換成「快取一致性」與「快取踩踏」。而且沒有上限的 `IMemoryCache` 會把 Pod 吃到 OOMKilled。

**「Output caching 加上去就對了。」**
對含個人化資料的回應使用，會把 A 使用者的資料回給 B。只用於公開內容。

**「限流設 100 就是每分鐘 100 次。」**
那是每個 Pod 100 次。三個副本就是 300。要全域精確得用分散式計數或交給 Ingress。

---

## 八、同事會來問你的問題

**Q：偶爾出現 `SocketException`，重啟就好。**
典型的 socket 耗盡——某處在每次呼叫時 `new HttpClient()` 並 dispose。改用 `IHttpClientFactory` 的 typed client。

**Q：下游服務換了 IP，我們一直連舊的。**
用了 static `HttpClient`，連線永不重建。`IHttpClientFactory` 的 handler 有生命週期（預設 2 分鐘），到期重建時會重新解析 DNS。

**Q：下游服務變慢，我們整個 API 都掛了。**
預設的 `HttpClient.Timeout` 是 100 秒，等於沒有逾時。設定合理逾時（5–10 秒）並加上斷路器，讓下游故障時快速失敗而不是堆積。

**Q：加了重試之後下游反而更容易掛。**
沒有指數退避與 jitter，所有客戶端同時重試，形成重試風暴。用 `AddStandardResilienceHandler` 的預設組合，它包含了退避與斷路器。

**Q：Redis 掛了整個 API 就 500。**
快取是最佳化不是必需品。所有快取操作都要包 try-catch，失敗時回退到資料庫並記 warning。

**Q：加了快取之後資料庫負載反而在尖峰時更高。**
Cache stampede——快取同時過期，大量請求同時回源。加鎖（雙重檢查）並在 TTL 上加隨機抖動。

**Q：限流該做在應用程式還是 Ingress？**
全域精確的限流交給 Ingress 或 API Gateway 更合適（應用程式端是每個 Pod 各自計數）。應用程式端的限流適合保護特定的昂貴端點。

---

## 連結

- [[basics-01-http-and-web-api]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[17-configuration-and-secrets]] — 上一章
- [[19-background-work]] — 下一章：背景工作與排程
- [[06-async-and-threading]] — CancellationToken 與逾時的傳遞
- [[08-efcore-query]] — 效能問題的第一順位：查詢
- [[09-transactions-and-concurrency]] — 交易裡不要有外部呼叫
