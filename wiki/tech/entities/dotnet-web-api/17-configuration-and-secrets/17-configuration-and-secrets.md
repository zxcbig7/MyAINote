---
type: concept
domain: tech
tags: [dotnet, aspnet, configuration, options-pattern, secrets, vault, configmap, feature-flags]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-14
updated: 2026-08-14
---

# 第 17 章：設定與 Secret — 改了為什麼沒生效

## 兩個都很花時間的問題

**問題一：** 改了 K8s 的 ConfigMap，`kubectl get configmap` 確認新值已經進去了，但應用程式的行為完全沒變。重啟 Pod 之後就正常了。

**問題二：** 新人把 `appsettings.json` 裡的資料庫密碼一起 commit 進 git 了。改掉密碼、刪掉那一行、再 commit——但 git 歷史裡永遠留著。

第一個問題的答案取決於 ConfigMap 是用**環境變數**還是**volume 掛載**注入的，而且和 .NET 這一側選用哪個 Options 介面有關。第二個問題的答案是「密碼從一開始就不該出現在那個檔案裡」。

這一章把設定系統從 provider 鏈講到 Options pattern，再到 Secret 的分層管理。

---

## 一、Provider 鏈：後面蓋前面

第 00 章講過 `CreateBuilder` 載入的順序：

| 順序 | 來源 | 備註 |
| --- | --- | --- |
| 1 | `appsettings.json` | |
| 2 | `appsettings.{Environment}.json` | |
| 3 | User Secrets | **僅 Development** |
| 4 | 環境變數 | 容器注入的主要管道 |
| 5 | 命令列參數 | 最高優先權 |

要精確理解的是：**設定不是合併成一份，而是保留成一疊 provider，讀取時由後往前找第一個有值的 key。**

推論一：覆蓋是**逐 key** 發生的。環境變數 `Jwt__Key` 覆蓋 `appsettings.json` 的 `Jwt:Key`，但同一個 `Jwt` 區塊裡的 `Issuer`、`Audience` 完全不受影響。

推論二：**陣列的覆蓋很反直覺**。設定裡的陣列是以索引為 key 展開的（`Servers:0`、`Servers:1`），所以「覆蓋」是逐索引進行的：

```json
// appsettings.json
{ "Servers": ["a", "b", "c"] }
```

用環境變數 `Servers__0=x` 之後，結果是 `["x", "b", "c"]`，**不是** `["x"]`。要真正替換整個陣列，得逐一覆蓋每個索引，或者改用逗號分隔的字串自己解析。這個行為讓「用環境變數覆蓋清單型設定」變得很痛苦，設計設定結構時值得避開陣列。

環境變數的巢狀分隔符是**雙底線** `__`（冒號在部分系統的環境變數名稱裡不合法）：

```yaml
env:
  - name: ConnectionStrings__Default
    valueFrom:
      secretKeyRef: { name: db-secret, key: connection-string }
  - name: Jwt__ExpiresInMinutes
    value: "60"
```

### 1.1 加入自訂 provider

```csharp
builder.Configuration
    .AddJsonFile("features.json", optional: true, reloadOnChange: true)
    .AddEnvironmentVariables(prefix: "MYAPP_");   // 只讀特定前綴，避免污染
```

順序就是優先序——後加的蓋前面的。

---

## 二、讀取設定的三種方式

### 2.1 直接索引（最不推薦）

```csharp
var key = _configuration["Jwt:Key"];
var minutes = _configuration.GetValue<int>("Jwt:ExpiresInMinutes");
```

問題是：字串 key 打錯不會有編譯錯誤、拿到的是 `string?` 要自己轉型、沒有任何驗證、而且散落各處難以追蹤誰用了哪個設定。

適合用在 `Program.cs` 裡少數幾個一次性的讀取。業務程式碼裡不該出現。

### 2.2 Bind 到物件

```csharp
var jwtOptions = new JwtOptions();
builder.Configuration.GetSection("Jwt").Bind(jwtOptions);

// 或
var jwtOptions = builder.Configuration.GetSection("Jwt").Get<JwtOptions>();
```

適合在 `Program.cs` 裡需要立刻用到設定值的場合（例如設定 JWT 驗證參數）。

### 2.3 Options Pattern（推薦）

```csharp
public class JwtOptions
{
    public const string SectionName = "Jwt";

    public string Key { get; set; } = string.Empty;
    public string Issuer { get; set; } = string.Empty;
    public string Audience { get; set; } = string.Empty;
    public int ExpiresInMinutes { get; set; } = 60;
}

builder.Services.Configure<JwtOptions>(
    builder.Configuration.GetSection(JwtOptions.SectionName));

// 使用
public class TokenService
{
    private readonly JwtOptions _options;

    public TokenService(IOptions<JwtOptions> options)
    {
        _options = options.Value;
    }
}
```

好處是強型別、可以注入、可以驗證、而且**依賴關係明確**——看建構子就知道這個服務需要哪些設定。

---

## 三、三個 Options 介面的差別

這是實務上最常搞混的地方，而且它直接決定了「改了設定會不會生效」。

| 介面 | 生命週期 | 何時讀取新值 | 用在 |
| --- | --- | --- | --- |
| `IOptions<T>` | Singleton | **永不**（啟動時讀一次） | 不會變的設定 |
| `IOptionsSnapshot<T>` | **Scoped** | 每個 request 重新計算 | 需要熱重載的設定 |
| `IOptionsMonitor<T>` | Singleton | 隨時（有變更通知） | Singleton 服務、背景服務 |

### 3.1 `IOptions<T>`

值在第一次被要求時計算，之後永遠是同一份。設定檔改了也不會變。

適合金鑰、連線字串這類「本來就該重啟才生效」的設定。

### 3.2 `IOptionsSnapshot<T>`

**它是 Scoped 的**，所以每個 request 會重新計算一次。這意味著：

- 同一個 request 內多次讀取，值一致（不會中途變化）
- 下一個 request 就能看到新值
- **不能注入到 Singleton 服務裡**——那是第 02 章的 captive dependency

### 3.3 `IOptionsMonitor<T>`

Singleton，但提供 `CurrentValue` 屬性隨時取得最新值，以及變更通知：

```csharp
public class RateLimitService
{
    private readonly IOptionsMonitor<RateLimitOptions> _monitor;

    public RateLimitService(IOptionsMonitor<RateLimitOptions> monitor)
    {
        _monitor = monitor;

        _monitor.OnChange(newOptions =>
        {
            _logger.LogInformation("限流設定已更新為 {Limit}", newOptions.PermitLimit);
        });
    }

    public bool IsAllowed(string key)
    {
        var limit = _monitor.CurrentValue.PermitLimit;   // 每次都拿最新值
        // ...
    }
}
```

背景服務（Singleton）需要熱重載的設定時，只能用這個。

注意 `OnChange` 回呼**可能被觸發多次**（檔案系統的寫入事件常常成對出現），所以裡面不該做昂貴或不冪等的操作。

---

## 四、驗證：讓錯誤在啟動時就爆炸

設定錯誤最糟糕的形態是「靜默地用了預設值」——JWT 金鑰是空字串、逾時是 0、連線字串指向本機。程式跑起來了，錯誤在幾小時後以奇怪的形式出現。

```csharp
public class JwtOptions
{
    [Required(AllowEmptyStrings = false)]
    [MinLength(32, ErrorMessage = "HS256 金鑰至少需要 32 位元組")]
    public string Key { get; set; } = string.Empty;

    [Required]
    [Url]
    public string Issuer { get; set; } = string.Empty;

    [Range(1, 1440)]
    public int ExpiresInMinutes { get; set; } = 60;
}

builder.Services.AddOptions<JwtOptions>()
    .Bind(builder.Configuration.GetSection(JwtOptions.SectionName))
    .ValidateDataAnnotations()
    .Validate(o => o.ExpiresInMinutes <= 1440, "有效期不可超過一天")
    .ValidateOnStart();          // ⚠️ 關鍵：啟動時就驗證
```

**`ValidateOnStart()` 是重點。** 沒有它的話，驗證要等到第一次注入 `IOptions<T>` 時才執行——那可能是上線幾小時後第一個使用者登入的時候，而且錯誤會表現成一個 500。

有了它，設定錯誤的 Pod **根本啟動不起來**，K8s 的 rollout 會卡住，舊版本繼續服務。這正是我們要的行為：**壞的設定不該被部署上去**（第 00 章的快速失敗原則）。

---

## 五、熱重載：開頭第一個問題的答案

`appsettings.json` 預設是 `reloadOnChange: true` 的——檔案改了會自動重新載入。但在 K8s 裡，設定是怎麼進來的決定了它會不會變。

| 注入方式 | 檔案會變嗎 | 熱重載 |
| --- | --- | --- |
| ConfigMap → **環境變數** | 不會 | **不可能**，必須重啟 Pod |
| ConfigMap → **volume 掛載** | 會（kubelet 定期同步） | 可以 |
| Secret → 環境變數 | 不會 | 不可能 |
| Secret → volume 掛載 | 會 | 可以 |

**環境變數在程序啟動時就固定了。** 這是作業系統層級的事實，不是 .NET 的限制——kubelet 更新 ConfigMap 時，已經在跑的程序看不到任何變化。所以「改了 ConfigMap 沒生效」的第一個檢查點是：它是用 env 還是 volume 注入的。

要熱重載就得用 volume 掛載：

```yaml
volumeMounts:
  - name: config
    mountPath: /app/config
volumes:
  - name: config
    configMap:
      name: myapp-config
```

```csharp
builder.Configuration.AddJsonFile(
    "/app/config/appsettings.Override.json",
    optional: true,
    reloadOnChange: true);
```

搭配 `IOptionsSnapshot` 或 `IOptionsMonitor`，新值就能在不重啟的情況下生效。

（注意 kubelet 同步 volume 有延遲，通常是分鐘級；而且它用 symlink 原子替換整個目錄，某些檔案監看實作在這種情況下可能收不到事件。實際行為值得在自己的環境驗證一次。ConfigMap 更新機制的完整討論見 [[k8s-mastery]] 的第 06 章。）

**但熱重載真的是好主意嗎？** 我的看法是：對「行為開關」（feature flag、限流閾值、log 層級）很有價值；對「基礎設定」（連線字串、金鑰）不值得——那些改變本來就應該伴隨一次受控的重新部署，而滾動更新的成本很低。

用 `IOptions<T>` 明確表達「這個設定不熱重載」，比讓所有設定都可能在執行期改變要好維護——後者意味著任何時候讀到的值都可能與五分鐘前不同，除錯時多一個變數。

---

## 六、Secret 的分層管理

### 6.1 開發環境：User Secrets

```powershell
dotnet user-secrets init
dotnet user-secrets set "ConnectionStrings:Default" "Data Source=localhost:1521/XE;User Id=dev;Password=devpass"
dotnet user-secrets list
```

它存在使用者家目錄（`%APPDATA%\Microsoft\UserSecrets\<id>\secrets.json`），**在專案目錄之外**，所以不可能被誤 commit。只在 Development 環境自動載入。

新人第一天就該用它，而不是「先寫在 appsettings.json 裡，記得別 commit」——那個「記得」遲早會失效。

### 6.2 生產環境：K8s Secret

```yaml
env:
  - name: ConnectionStrings__Default
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: connection-string
```

必須知道的一件事：**K8s Secret 預設只是 Base64 編碼，不是加密。**

```powershell
kubectl get secret db-credentials -o jsonpath='{.data.connection-string}' | base64 -d
```

任何有該 namespace read 權限的人都能讀出明文。etcd 裡存的也是未加密的內容（除非叢集開啟了 encryption at rest）。

所以 K8s Secret 提供的是「與 ConfigMap 分開管理、可以用 RBAC 限制存取」的隔離，不是加密。真正的機密管理需要更上一層。

### 6.3 更進一步：Vault / External Secrets

HashiCorp Vault 或雲端的 secret manager 提供的是：加密儲存、存取稽核、動態憑證（用完即棄的短期資料庫帳密）、集中輪替。

實務上常見的接法是 **External Secrets Operator**——Vault 裡的機密自動同步成 K8s Secret，應用程式端不需要改任何程式碼：

```text
Vault → External Secrets Operator → K8s Secret → 環境變數 → IConfiguration
```

應用程式仍然只是讀環境變數，但機密的來源、輪替、稽核都由 Vault 管理。這個鏈路的細節見 [[vault]] 與 [[k8s-mastery]] 的第 06 章。

### 6.4 Secret 洩漏之後

密碼一旦進了 git 歷史，**改掉檔案是不夠的**——歷史裡永遠留著，任何 clone 過 repo 的人都有。

正確的處理是：

1. **立刻輪替該憑證**（這是唯一真正有效的動作）
2. 檢查是否有異常存取紀錄
3. 清理 git 歷史（`git filter-repo` 或 BFG），但要意識到已經被 fork/clone 的副本無法回收
4. 加上 pre-commit hook 或 CI 掃描（gitleaks、truffleHog）防止再次發生

第 1 步的優先順序遠高於其他步驟。很多團隊花大量時間清理歷史，卻忘了那個密碼在清理期間仍然有效。

---

## 七、設定結構的設計建議

```json
{
  "ConnectionStrings": {
    "Default": ""
  },
  "Jwt": {
    "Issuer": "https://api.example.com",
    "Audience": "https://app.example.com",
    "ExpiresInMinutes": 15
  },
  "RateLimit": {
    "PermitLimit": 100,
    "WindowSeconds": 60
  },
  "ExternalServices": {
    "Payment": {
      "BaseUrl": "https://payment.example.com",
      "TimeoutSeconds": 30
    }
  }
}
```

幾個原則：

**分組要對應到 Options 類別。** 一個 section 一個類別，讓「哪些設定屬於誰」一目了然。

**敏感值在版控的檔案裡留空字串**，由環境變數注入。留空而不是省略，是為了讓讀 code 的人知道有這個設定存在。

**避免陣列**（第一節解釋過覆蓋行為很反直覺）。真的需要清單時考慮用逗號分隔的字串，或改成以 key 命名的物件。

**預設值寫在 C# 類別的屬性初始值裡**，而不是只寫在 json 裡。這樣即使設定漏了也有合理行為，而且預設值與型別在同一個地方。

---

## 八、Feature Flag

需要「不重新部署就切換功能」時：

```csharp
// 最簡單的形式：設定 + IOptionsMonitor
public class FeatureOptions
{
    public bool NewCheckoutFlow { get; set; }
    public bool EnableExperimentalSearch { get; set; }
}

if (_features.CurrentValue.NewCheckoutFlow)
{
    return await _newCheckout.ProcessAsync(dto, ct);
}
return await _legacyCheckout.ProcessAsync(dto, ct);
```

需要更複雜的規則（依使用者百分比、依租戶）時，`Microsoft.FeatureManagement` 套件提供了 filter 機制。

實務提醒：**feature flag 是技術債**。每個 flag 都是一個分支，兩條路徑都要測試、都要維護。要有明確的清理計畫——功能穩定後就移除 flag 與舊路徑，否則幾年後會累積出幾十個沒人敢刪的開關。

---

## 九、常見誤解

**「改了 ConfigMap 應用程式就會看到新值。」**
用環境變數注入的話不會——環境變數在程序啟動時固定。要熱重載必須用 volume 掛載，並搭配 `IOptionsSnapshot` 或 `IOptionsMonitor`。

**「`IOptions<T>` 會自動更新。」**
不會，它是 Singleton 且只計算一次。要更新用 `IOptionsSnapshot`（Scoped）或 `IOptionsMonitor`（Singleton 但可監看）。

**「K8s Secret 是加密的。」**
預設只是 Base64 編碼。有 namespace read 權限的人都能讀出明文。真正的加密需要 etcd encryption at rest 或外部的 secret manager。

**「設定驗證不重要，錯了自然會發現。」**
沒有 `ValidateOnStart()` 的話，錯誤會在執行期以奇怪的形式出現。加上它，壞設定的 Pod 根本起不來，rollout 會卡住而舊版繼續服務。

**「把密碼從檔案刪掉再 commit 就沒事了。」**
git 歷史裡永遠留著。唯一有效的動作是立刻輪替該憑證。

**「所有設定都支援熱重載比較好。」**
那意味著任何時候讀到的值都可能與五分鐘前不同，除錯時多一個變數。行為開關值得熱重載，基礎設定不值得。

---

## 十、同事會來問你的問題

**Q：改了 ConfigMap 為什麼沒生效？**
先看是用 env 還是 volume 注入。環境變數在程序啟動時固定，不可能熱重載，必須重啟 Pod（`kubectl rollout restart`）。要熱重載得改用 volume 掛載並搭配 `IOptionsSnapshot`。

**Q：`IOptionsSnapshot` 注入到背景服務為什麼報錯？**
它是 Scoped，而 `BackgroundService` 是 Singleton——captive dependency。背景服務要用 `IOptionsMonitor`。

**Q：怎麼確保設定沒填錯就不會上線？**
用 `AddOptions<T>().ValidateDataAnnotations().ValidateOnStart()`。設定錯誤的 Pod 起不來，K8s rollout 卡住，舊版本繼續服務。

**Q：本機開發的資料庫密碼放哪？**
`dotnet user-secrets`。它存在使用者家目錄，在專案目錄外，不可能被誤 commit，而且只在 Development 環境載入。

**Q：密碼不小心 commit 了怎麼辦？**
第一件事是輪替該憑證，這是唯一真正有效的動作。之後才是清理 git 歷史（已被 clone 的副本無法回收）並加上 CI 的機密掃描。

**Q：用環境變數覆蓋設定裡的陣列，為什麼只換掉第一個元素？**
陣列在設定系統裡是以索引為 key 展開的，覆蓋是逐索引進行的。設 `Servers__0` 只換掉索引 0。避免在設定裡用陣列，或改用逗號分隔的字串。

**Q：連線字串該用 `IOptions` 還是直接讀 `IConfiguration`？**
連線字串通常在 `Program.cs` 註冊 DbContext 時就用掉了，直接 `GetConnectionString("Default")` 即可。業務程式碼裡需要的設定才用 Options pattern。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[16-logging-and-observability]] — 上一章
- [[18-resilience-and-performance]] — 下一章：逾時、重試、快取、限流
- [[00-hosting-and-startup]] — provider 鏈的載入時機
- [[12-jwt-deep-dive]] — 金鑰的輪替
- [[vault]] — Secret 管理
- [[k8s-mastery]] — ConfigMap env vs volume 的完整推導
