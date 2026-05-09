---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# appsetting.json

> 它的角色不是「寫程式邏輯」，而是集中管理所有「會變動、與環境相關、與部署相關」的設定值。
> 

## 一、`appsettings.json` 的本質定位

一句話定義：

> appsettings.json 是用來存放「不應該硬寫在程式碼中的設定值」
> 

這些設定值通常具備以下特性之一：

- 會因 **環境不同（Dev / Test / Prod）而改變**
- 屬於 **部署設定、連線資訊、行為參數**
- **不希望重新編譯程式**就能調整
- 與 **商業邏輯無直接耦合**

## 二、`appsettings.json` 可以做的事情（核心用途）

### 1. 管理資料庫連線字串（最常見）

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=RuleViewer;User Id=sa;Password=***;"
  }
}

```

用途：

- 切換資料庫位置
- 切換帳號密碼
- 不把敏感資訊寫死在程式碼中

實務意義：

- 同一份程式碼，可部署到不同環境
- 不用改 code 就能換 DB

---

### 2. 管理環境差異（Dev / Staging / Prod）

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning"
    }
  }
}
```

搭配：

- `appsettings.Development.json`
- `appsettings.Production.json`

實務意義：

- 開發環境 log 詳細
- 正式環境 log 保守
- 行為因環境切換，而不是 if-else 寫死

---

### 3. 控制 Middleware / 系統行為參數

例如：

```json
{
  "Cors": {
    "AllowedOrigins": [
      "http://localhost:5173",
      "https://ruleviewer.com"
    ]
  }
}
```

可控制的事情包括：

- CORS 白名單
- API 行為限制
- Feature 開關
- Request Size 上限
- Timeout、Retry 次數

**重點：這些不是「業務邏輯」，而是「系統策略」**

---

### 4. 存放 JWT / Authentication / Authorization 設定

```json
{
  "Jwt": {
    "Issuer": "RuleViewer",
    "Audience": "RuleViewerFrontend",
    "Key": "SuperSecretKey",
    "ExpireMinutes": 60
  }
}
```

用途：

- Token 發行規則
- 驗證參數
- 過期時間

實務意義：

- 不把金鑰硬寫在程式碼
- 不同環境用不同金鑰
- 安全性與程式碼分離

---

### 5. Feature Toggle（功能開關）

```json
{
  "Features": {
    "EnableInspector": true,
    "EnableExperimentalApi": false
  }
}
```

用途：

- 新功能灰度開啟
- 測試功能不影響正式用戶
- 不用重新部署即可關閉功能

---

## 三、為什麼不用常數或寫死在程式碼？

### ❌ 不好的作法

```csharp
const string ConnectionString = "...";
```

問題：

- 換環境就要改 code
- 容易洩漏敏感資訊
- CI/CD 困難
- 無法讓 Ops 或 DevOps 控制

---

### ✅ 正確的分層觀念

| 類型 | 放哪裡 |
| --- | --- |
| 商業規則 | C# 程式碼 |
| 流程邏輯 | Controller / Service |
| 系統策略 | appsettings.json |
| 機密資訊 | appsettings + Secret / Env |

---

## 四、`appsettings.json` 在整個系統中的位置

概念架構：

```
┌─────────────┐
│ Program.cs  │ ← 讀取設定
└─────▲───────┘
      │
┌─────┴───────────┐
│  IConfiguration │
└─────▲───────────┘
      │
┌─────┴──────────────┐
│ appsettings.json   │ ← 設定來源
│ appsettings.Dev    │
│ appsettings.Prod   │
└────────────────────┘

```

程式碼 **只知道「要讀設定」**

實際值來自 **設定檔 / 環境變數**

---

## 五、實務中常見的分類方式（建議）

```json
{
  "ConnectionStrings": {},
  "Logging": {},
  "Jwt": {},
  "Cors": {},
  "Features": {},
  "ExternalServices": {},
  "AppSettings": {}
}
```

原則：

- 一個區塊一個責任
- 名字反映用途
- 不混雜商業資料

---

## 六、你現在學到哪一層，下一步可以怎麼進

以你目前的 Web API 學習路線，下一步建議依序是：

1. **如何在 `Program.cs` 讀取設定**
2. **如何用 `IOptions<T>` 綁定設定類別**
3. **如何搭配 DI 注入設定**
4. **如何用環境變數覆蓋 appsettings**
5. **JWT / CORS / Logging 實戰配置**

如果你願意，我可以直接幫你整理成：

- 一章完整教學（像你前面的 Chapter）
- 或直接用「標準企業級 Web API 架構」來講解

## 一、總覽：`appsettings.json` 是怎麼被讀進系統的

在 **.NET 6+（Minimal Hosting Model）** 中：

```csharp
var builder = WebApplication.CreateBuilder(args);
```

這一行已經自動幫你做完以下事情：

- 載入 `appsettings.json`
    - 載入 `appsettings.{Environment}.json`
- 載入 Environment Variables
- 建立 `IConfiguration`

你不需要自己寫任何「讀檔程式碼」。

---

## 二、讀取方式總覽（正式分級）

| 等級 | 方式 | 使用時機 |
| --- | --- | --- |
| Lv1 | `IConfiguration["Key"]` | 快速、簡單 |
| Lv2 | `GetSection()` | 讀取區塊 |
| Lv3 | `IOptions<T>` | 正式專案標準 |
| Lv4 | `IOptionsSnapshot<T>` | 需要熱更新 |
| Lv5 | `IOptionsMonitor<T>` | 長生命週期服務 |

下面一個一個拆解。

---

## 三、方式一：`IConfiguration["Key"]`（最基礎）

### 設定檔

```json
{
  "AppSettings": {
    "AppName": "RuleViewer",
    "Version": "1.0"
  }
}
```

### 讀取方式

```csharp
public class DemoController : ControllerBase
{
    private readonly IConfiguration _config;

    public DemoController(IConfiguration config)
    {
        _config = config;
    }

    [HttpGet]
    public string GetAppName()
    {
        return _config["AppSettings:AppName"];
    }
}

```

### 特點

- Key 使用 `:` 表示階層
- 回傳型別永遠是 `string?`
- 沒有型別安全

### 適合

- Demo
- 快速測試
- 少量設定

---

## 四、方式二：`GetSection()`（讀取整個區塊）

```csharp
var section = _config.GetSection("AppSettings");

string appName = section["AppName"];
string version = section["Version"];
```

### 特點

- 邏輯結構更清楚
- 仍然是字串導向
- 沒有編譯期檢查

---

## 五、方式三：`IOptions<T>`（正式專案標準）

這是 **企業級、正式推薦方式**。

---

### Step 1：定義設定類別（Strongly Typed）

```csharp
public class AppSettings
{
    public string AppName { get; set; } = string.Empty;
    public string Version { get; set; } = string.Empty;
}
```

> 原則：
> 
> - 類別結構 = JSON 結構
> - 屬性名稱 = Key 名稱

---

### Step 2：在 `Program.cs` 註冊

```csharp
builder.Services.Configure<AppSettings>(
    builder.Configuration.GetSection("AppSettings")
);
```

---

### Step 3：在需要的地方注入

```csharp
using Microsoft.Extensions.Options;

public class DemoController : ControllerBase
{
    private readonly AppSettings _settings;

    public DemoController(IOptions<AppSettings> options)
    {
        _settings = options.Value;
    }

    [HttpGet]
    public string GetInfo()
    {
        return $"{_settings.AppName} v{_settings.Version}";
    }
}
```

---

### 為什麼這是標準作法？

- 型別安全
- IntelliSense
- 可測試
- 符合 DI 架構
- 避免 magic string

---

## 六、方式四：`IOptionsSnapshot<T>`（Request Scoped）

```csharp
public DemoController(IOptionsSnapshot<AppSettings> options)
{
    _settings = options.Value;
}
```

### 特點

- 每個 HTTP Request 重新讀一次設定
- 適合 Web API
- 支援「設定檔變更後立即生效」

---

## 七、方式五：`IOptionsMonitor<T>`（Singleton 用）

```csharp
public class BackgroundService
{
    public BackgroundService(IOptionsMonitor<AppSettings> monitor)
    {
        monitor.OnChange(settings =>
        {
            // 設定變更時觸發
        });
    }
}
```

### 使用時機

- Background Service
- Singleton Service
- 長時間執行元件

---

## 八、五種方式怎麼選？

| 情境 | 建議方式 |
| --- | --- |
| Demo / 教學 | IConfiguration |
| 正式 Web API | IOptions / Snapshot |
| 背景服務 | IOptionsMonitor |
| 熱更新需求 | Snapshot / Monitor |
| 可測試架構 | IOptions |