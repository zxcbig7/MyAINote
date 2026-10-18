---
type: concept
domain: tech
tags: [dotnet, aspnet, logging, serilog, opentelemetry, prometheus, elk, health-check, tracing]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 16 章：Logging 與可觀測性 — 出事的時候才發現記錯了東西

## 半夜三點的兩種處境

**處境 A：** 使用者回報「下單失敗」。你打開 Kibana，搜尋 `"下單失敗"`，跳出七千筆結果，全部長這樣：

```text
下單失敗
下單失敗
下單失敗
```

沒有使用者 ID、沒有訂單編號、沒有失敗原因。你不知道哪一筆是他的。

**處境 B：** 使用者附上了錯誤畫面上的追蹤碼 `00-4bf92f35...`。你在 Kibana 搜尋這個 ID，跳出這一次請求從進來到失敗的**十七行 log**，包括收到的參數、查詢耗時、外部服務的回應、以及最後拋出的例外與完整堆疊。三分鐘結案。

兩者的差別不在於「有沒有記 log」，而在於**記的方式**。這一章講的就是從 A 走到 B 需要的東西。

---

## 一、結構化 Logging：最重要的一個習慣

```csharp
// ❌ 字串插值：訊息變成一整串不可查詢的文字
_logger.LogInformation($"使用者 {userId} 建立訂單 {orderId}，金額 {amount}");

// ✅ 訊息模板：參數被保留成獨立欄位
_logger.LogInformation("使用者 {UserId} 建立訂單 {OrderId}，金額 {Amount}",
    userId, orderId, amount);
```

兩者在 console 上看起來一樣。差別在送進 Elasticsearch 之後。

第一種產生的是一個字串欄位，內容是 `"使用者 123 建立訂單 456，金額 999"`。要查「使用者 123 的所有操作」只能做全文比對，而且會誤中訂單編號剛好是 123 的紀錄。

第二種產生的是**結構化資料**：

```json
{
  "@t": "2026-08-14T07:23:11.42Z",
  "@l": "Information",
  "@mt": "使用者 {UserId} 建立訂單 {OrderId}，金額 {Amount}",
  "UserId": 123,
  "OrderId": 456,
  "Amount": 999
}
```

現在可以在 Kibana 用 `UserId: 123 AND Amount > 500` 精確查詢、可以按 `OrderId` 聚合、可以畫金額分布圖。訊息模板本身（`@mt`）也是一個欄位，所以「同一種 log 出現幾次」變成一個簡單的聚合查詢。

**這是結構化 logging 的全部價值，而它只需要把 `$` 換成逗號。** 團隊裡值得設一條 lint 規則強制它（.NET 的 CA2254 分析器就是做這個的）。

參數名稱要用 **PascalCase** 並保持全系統一致——`UserId` 在某處寫成 `userId`、某處寫成 `user_id`，就變成三個不同的欄位，查詢時得寫三個條件。

---

## 二、Log Level 與過濾

| Level | 用途 | 生產環境 |
| --- | --- | --- |
| `Trace` | 極詳細的診斷，含敏感資料 | **絕不開啟** |
| `Debug` | 開發診斷 | 關閉 |
| `Information` | 重要的業務事件（登入、下單、狀態變更） | 開啟 |
| `Warning` | 非預期但可恢復（重試、降級、並發衝突） | 開啟 |
| `Error` | 當前操作失敗，需要有人看 | 開啟 |
| `Critical` | 系統層級失敗（無法連線資料庫、啟動失敗） | 開啟 |

最常見的錯誤是**把 Information 當 Debug 用**——每個方法進出都記一筆。結果是生產環境的 log 量爆炸（成本直接反映在 Elasticsearch 的儲存與授權費用上），而真正重要的事件被淹沒。

判準：**Information 記錄的應該是「業務上有意義的事件」，不是「程式執行到這一行」。**

過濾設定支援按類別（category）分層，越具體的前綴優先：

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning",
      "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
      "MyApp.Services.OrderService": "Debug"
    }
  }
}
```

`Microsoft.AspNetCore` 設成 `Warning` 是實務上幾乎必要的——預設的 `Information` 會為每個請求產生三到四筆框架層的 log，量非常大而資訊價值低（存取記錄應該由專門的 middleware 產生，見第四節）。

`ILogger<T>` 的類別名稱就是 `T` 的完整型別名，所以上面的設定能精準控制到單一類別。

---

## 三、Scope：把一次請求的 log 串起來

處境 B 的關鍵能力是「找出同一次請求的所有 log」。這靠 **scope**：

```csharp
using (_logger.BeginScope(new Dictionary<string, object>
{
    ["OrderId"] = orderId,
    ["CustomerId"] = customerId
}))
{
    _logger.LogInformation("開始處理訂單");
    await _inventory.ReserveAsync(orderId);      // 這裡面的 log 也會帶上 OrderId
    _logger.LogInformation("訂單處理完成");
}
```

Scope 內的**所有** log（包含被呼叫的其他類別產生的）都會自動帶上這些欄位。它靠 `AsyncLocal` 實作，所以能跨 `await` 流動（第 06 章）。

ASP.NET Core 本身也提供了一個更基礎的關聯機制：**W3C Trace Context**。每個請求進來時，框架建立一個 `Activity`，它的 `Id` 長這樣：

```text
00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
│  └─ TraceId（整條呼叫鏈共用）───┘ └─ SpanId ────┘ └flags
```

**TraceId 在跨服務呼叫時會透過 `traceparent` header 傳遞下去**。所以 A 服務呼叫 B 服務，兩邊的 log 帶著同一個 TraceId——這就是分散式追蹤的基礎。

要讓它出現在每一筆 log 裡：

```csharp
builder.Services.AddHttpLogging(o => { });   // 或用下面的自訂 middleware

app.Use(async (ctx, next) =>
{
    var traceId = Activity.Current?.TraceId.ToString() ?? ctx.TraceIdentifier;

    using (logger.BeginScope(new Dictionary<string, object> { ["TraceId"] = traceId }))
    {
        await next();
    }
});
```

再把同一個 traceId 放進錯誤回應（第 15 章），使用者回報時就能直接對應。這是處境 A 到 B 的整條鏈。

---

## 四、容器環境的 log 輸出

容器的慣例很明確：**應用程式只管把 log 寫到 stdout，收集是外部的事。**

不要寫檔案。理由是：容器的檔案系統是暫時的（Pod 重啟就沒了）、寫檔需要處理輪替與清理、而且會佔用容器的可寫層。K8s 的 kubelet 會接走 stdout，由 Filebeat / Fluent Bit 送進 Elasticsearch。

為了讓收集器能解析，輸出應該是 **JSON 一行一筆**：

```csharp
builder.Logging.ClearProviders();
builder.Logging.AddJsonConsole(options =>
{
    options.IncludeScopes = true;              // ⚠️ 預設是 false，scope 不會輸出
    options.TimestampFormat = "yyyy-MM-ddTHH:mm:ss.fffZ";
    options.UseUtcTimestamp = true;
});
```

`IncludeScopes = true` 很重要——**預設是 false**，意味著上一節辛苦設定的 scope 欄位根本不會出現在輸出裡。這是很多人「明明加了 scope 卻在 Kibana 找不到」的原因。

### 4.1 Serilog 還是內建

內建的 `Microsoft.Extensions.Logging` 對多數專案已經夠用。Serilog 的優勢在：

| | 內建 | Serilog |
| --- | --- | --- |
| 結構化輸出 | 支援 | 支援（生態更成熟） |
| Sink 種類 | Console、Debug、EventSource | 數十種（Elasticsearch、Seq、檔案、Slack…） |
| Enricher | 需自己寫 | 現成（機器名、執行緒、環境） |
| 動態調整層級 | 需重啟或自訂 | `LoggingLevelSwitch` |
| 依賴 | 無 | 額外套件 |

在容器 + ELK 的架構下，直接寫 JSON 到 stdout 就夠了——不需要 Serilog 的 Elasticsearch sink（那會讓應用程式直接連 ES，多一個故障點，而且 Pod 掛掉時緩衝中的 log 會遺失）。**讓收集器負責運送**是更可靠的分工。

所以我的建議是：新專案先用內建的 `AddJsonConsole`；需要豐富的 enricher 或動態層級調整時再引入 Serilog。

### 4.2 存取記錄

框架預設的請求 log 太吵，實務上常自己寫一個精簡版：

```csharp
app.Use(async (ctx, next) =>
{
    var sw = Stopwatch.StartNew();
    try
    {
        await next();
    }
    finally
    {
        sw.Stop();
        logger.LogInformation(
            "{Method} {Path} → {StatusCode} in {ElapsedMs}ms",
            ctx.Request.Method,
            ctx.Request.Path,
            ctx.Response.StatusCode,
            sw.ElapsedMilliseconds);
    }
});
```

`finally` 確保例外時也會記錄。放在 pipeline 最前面（但在 exception handler 之後）才能量到完整耗時（第 01 章）。

也可以用內建的 `app.UseHttpLogging()`，但要小心它預設可能記錄 header 與 body——那是敏感資料外洩的風險，見下一節。

---

## 五、不要記錄什麼

log 會被送到 Elasticsearch、被保留數週或數月、被許多人查看。它是一個**低權限、廣泛可讀**的資料儲存。

絕對不要記錄：

- 密碼、API key、token（包括 `Authorization` header 的完整內容）
- 個人識別資訊：身分證字號、完整信用卡號、詳細地址
- 完整的 request body（可能包含以上任何一項）
- 資料庫連線字串
- EF Core 的 `EnableSensitiveDataLogging` 產生的參數值（第 08 章）

需要記錄識別資訊時用遮罩：

```csharp
private static string MaskEmail(string email)
{
    var parts = email.Split('@');
    return parts.Length != 2
        ? "***"
        : $"{parts[0][..Math.Min(2, parts[0].Length)]}***@{parts[1]}";
}
```

`UseHttpLogging` 要特別小心設定：

```csharp
builder.Services.AddHttpLogging(options =>
{
    options.LoggingFields = HttpLoggingFields.RequestPath
                          | HttpLoggingFields.ResponseStatusCode
                          | HttpLoggingFields.Duration;
    // 不要加 RequestBody / RequestHeaders
});
```

---

## 六、Metrics：log 回答不了的問題

Log 回答「這一次發生了什麼」，metrics 回答「整體現在如何」。「P95 延遲是多少」「錯誤率有沒有上升」「ThreadPool 佇列長度」——這些用 log 算是可以，但成本高得多。

.NET 內建了 metrics API（`System.Diagnostics.Metrics`），搭配 OpenTelemetry 匯出到 Prometheus：

```csharp
builder.Services.AddOpenTelemetry()
    .WithMetrics(metrics =>
    {
        metrics
            .AddAspNetCoreInstrumentation()      // 請求數、延遲、狀態碼
            .AddHttpClientInstrumentation()      // 對外呼叫
            .AddRuntimeInstrumentation()         // GC、ThreadPool、例外數
            .AddPrometheusExporter();
    })
    .WithTracing(tracing =>
    {
        tracing
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddEntityFrameworkCoreInstrumentation()
            .AddOtlpExporter();
    });

app.MapPrometheusScrapingEndpoint();             // 預設 /metrics
```

`AddRuntimeInstrumentation()` 提供的 ThreadPool 指標正是第 06 章診斷飢餓所需的——把它做成 Grafana 面板，就不用等到出事才用 `dotnet-counters` 進去看。

自訂業務指標：

```csharp
public class OrderMetrics
{
    private readonly Counter<long> _ordersCreated;
    private readonly Histogram<double> _orderValue;

    public OrderMetrics(IMeterFactory factory)
    {
        var meter = factory.Create("MyApp.Orders");
        _ordersCreated = meter.CreateCounter<long>("orders.created");
        _orderValue = meter.CreateHistogram<double>("orders.value");
    }

    public void RecordOrder(decimal amount, string channel)
    {
        _ordersCreated.Add(1, new KeyValuePair<string, object?>("channel", channel));
        _orderValue.Record((double)amount);
    }
}
```

### 6.1 高基數是 metrics 的頭號殺手

標籤（label / tag）的每一個唯一組合都會產生一條獨立的時間序列。所以：

```csharp
// ❌ 每個使用者一條序列，一百萬使用者就一百萬條序列 → Prometheus 記憶體爆炸
_ordersCreated.Add(1, new KeyValuePair<string, object?>("user_id", userId));

// ✅ 標籤用低基數的維度
_ordersCreated.Add(1, new KeyValuePair<string, object?>("channel", "web"));
```

規則：**標籤的可能值應該是有限且穩定的**——通道、狀態、錯誤類型、環境。使用者 ID、訂單編號、URL 路徑（含 ID）都屬於高基數，應該放 log 而不是 metrics。

「哪個使用者下了哪筆訂單」用 log 查；「每分鐘下單數與 P95 金額」用 metrics 看。兩者分工明確。

---

## 七、Health Checks 與 K8s Probe

```csharp
builder.Services.AddHealthChecks()
    .AddDbContextCheck<AppDbContext>("database", tags: new[] { "ready" })
    .AddUrlGroup(new Uri("https://payment.example.com/health"), "payment",
                 tags: new[] { "ready" });

app.MapHealthChecks("/healthz/live", new HealthCheckOptions
{
    Predicate = _ => false            // 不跑任何檢查，只證明程序活著
}).AllowAnonymous();

app.MapHealthChecks("/healthz/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
}).AllowAnonymous();
```

兩個端點的區別是**部署穩定性的關鍵**：

| Probe | 端點 | 檢查什麼 | 失敗時 K8s 做什麼 |
| --- | --- | --- | --- |
| liveness | `/healthz/live` | **只檢查程序活著** | **重啟 Pod** |
| readiness | `/healthz/ready` | 依賴是否可用 | 從 Service 端點移除，不重啟 |
| startup | `/healthz/live` | 啟動是否完成 | 重啟（給慢啟動更長寬限） |

**liveness 絕對不能檢查資料庫。** 想像資料庫短暫抖動的場景：所有 Pod 的 liveness 同時失敗 → K8s 同時重啟所有 Pod → 服務完全中斷，而且重啟後資料庫還是不通，於是進入無限重啟。資料庫的問題不是重啟應用程式能解決的。

readiness 檢查資料庫則是正確的：Pod 暫時被移出負載平衡，不接收流量，等資料庫恢復後自動回來。**沒有重啟，沒有雪崩。**

別忘了 `.AllowAnonymous()`（第 14 章）——設了 `FallbackPolicy` 之後，健康檢查端點會需要授權，probe 拿到 401 就是持續重啟。

K8s 端的對應設定與 probe 參數調校在 [[k8s-mastery]] 的第 04 章有完整推導。

---

## 八、常見誤解

**「用字串插值寫 log 比較直覺。」**
它讓參數變成不可查詢的文字。改用訊息模板（`{UserId}` 加逗號傳參），代價是零，收益是能在 Kibana 精確查詢與聚合。

**「log 記越多越好，出事才有東西查。」**
量太大時真正重要的訊息被淹沒，儲存成本也是真金白銀。Information 應該只記業務上有意義的事件。

**「設了 `BeginScope` 但 Kibana 看不到那些欄位。」**
`AddJsonConsole` 的 `IncludeScopes` 預設是 false。要明確設成 true。

**「應用程式應該直接把 log 寫進 Elasticsearch。」**
那讓應用程式多一個故障點，Pod 掛掉時緩衝的 log 也會遺失。容器的慣例是寫 stdout，由收集器負責運送。

**「metrics 加上 user_id 標籤才知道是誰。」**
高基數標籤會炸掉 Prometheus。「是誰」用 log 查，metrics 只放有限維度的標籤。

**「liveness 和 readiness 用同一個端點比較省事。」**
liveness 失敗會重啟 Pod。如果它檢查資料庫，資料庫一抖動就會導致所有 Pod 同時重啟。兩者必須分開。

---

## 九、同事會來問你的問題

**Q：使用者說出錯了，怎麼找到他那一次的 log？**
在錯誤回應裡放 `traceId`（來自 `Activity.Current`），前端顯示給使用者。在 Kibana 用這個 ID 搜尋，能撈出整條請求鏈的所有 log，包含跨服務的部分。

**Q：Kibana 裡查不到我加的欄位。**
兩個常見原因：用了字串插值（參數沒有變成獨立欄位），或 `AddJsonConsole` 的 `IncludeScopes` 沒開。

**Q：log 量太大，Elasticsearch 成本失控。**
先把 `Microsoft.AspNetCore` 的層級降到 `Warning`——框架預設每個請求記三四筆。再檢查有沒有把 Debug 級別的內容記成 Information。最後才考慮調整 ILM 的保留策略。

**Q：liveness probe 該檢查資料庫嗎？**
不該。資料庫抖動會讓所有 Pod 同時被重啟，造成雪崩且無助於恢復。liveness 只證明程序活著，依賴檢查放 readiness。

**Q：怎麼監控 ThreadPool 飢餓？**
`AddRuntimeInstrumentation()` 會匯出 ThreadPool 的執行緒數與佇列長度。做成 Grafana 面板並對佇列長度設告警，就不用等出事才進容器跑 `dotnet-counters`。

**Q：Serilog 值得裝嗎？**
容器 + ELK 的架構下，內建的 `AddJsonConsole` 就夠了。需要豐富 enricher、動態調整層級、或非 stdout 的 sink 時才值得引入。

**Q：可以在 log 裡記 request body 方便偵錯嗎？**
不建議。body 可能含密碼、token、個資，而 log 是廣泛可讀且長期保留的。真的需要就白名單特定欄位並遮罩。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[15-error-handling]] — 上一章：traceId 放進錯誤回應
- [[17-configuration-and-secrets]] — 下一章：設定與 Secret
- [[06-async-and-threading]] — ThreadPool 指標的意義
- [[k8s-mastery]] — probe 設定與 ELK/Prometheus 的完整教材
- [[15-elk-elastic]] — Elasticsearch 與 KQL
- [[14-prometheus-grafana]] — PromQL 與告警
