---
type: concept
domain: tech
tags: [dotnet, aspnet, docker, kubernetes, deployment, api-versioning, gc, migration]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-15
updated: 2026-08-15
---

# 第 21 章：部署 — 從 `dotnet run` 到叢集裡的三個副本

## 「本機好好的」的完整清單

這本教材裡反覆出現同一句話：本機好好的，上了容器就掛。到這一章可以把散落各處的原因收攏成一張表：

| 症狀 | 章節 | 根因 |
| --- | --- | --- |
| Swagger 不見了、錯誤變成空白 500 | 00 | `ASPNETCORE_ENVIRONMENT` 沒設，跑 Production |
| Service 通不了但 Pod 內 curl 正常 | 00 | Kestrel 綁 loopback 而非 `0.0.0.0` |
| 容器起來但連不上 | 00 | .NET 8 預設 port 從 80 改成 8080 |
| 滾動更新掉請求 | 00 | 關太快，端點移除還沒傳播 |
| 生命週期錯誤沒被擋下 | 00/02 | scope validation 預設只在 Development 開 |
| 無限重導向 | 13 | 反向代理後面 scheme 是 http |
| 改了 ConfigMap 沒生效 | 17 | 用環境變數注入，程序啟動後就固定 |
| Pod 反覆重啟且 log 沒東西 | 19 | `ExecuteAsync` 啟動時同步阻塞 |
| probe 拿到 401 | 14/16 | `FallbackPolicy` 把健康檢查也擋了 |

這一章把部署這一側補完。

---

## 一、Dockerfile

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# 先只複製專案檔還原套件 —— 這一層只在 csproj 變動時才失效
COPY ["src/MyApp.Api/MyApp.Api.csproj", "src/MyApp.Api/"]
COPY ["src/MyApp.Core/MyApp.Core.csproj", "src/MyApp.Core/"]
RUN dotnet restore "src/MyApp.Api/MyApp.Api.csproj"

# 再複製其餘原始碼
COPY . .
RUN dotnet publish "src/MyApp.Api/MyApp.Api.csproj" \
    -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app

# 非 root 執行
RUN adduser --disabled-password --gecos "" --uid 1000 appuser
USER appuser

COPY --from=build --chown=appuser:appuser /app/publish .

EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080

ENTRYPOINT ["dotnet", "MyApp.Api.dll"]
```

四個關鍵決策：

**先 restore 再 copy 原始碼。** Docker 的 layer 快取以指令為單位——`COPY . .` 之後的所有層在任何檔案變動時都會失效。把 `restore`（慢、依賴少變）放在前面，改一行 C# 程式碼時就不用重新下載所有 NuGet 套件。這通常把建置時間從幾分鐘降到幾十秒。

**多階段建置。** 最終映像用 `aspnet` 而非 `sdk`——後者含編譯器與 SDK 工具，體積大好幾倍，而且在生產環境是不必要的攻擊面。

**非 root 執行。** 容器逃逸漏洞在 root 下的危害大得多，而且很多叢集的 Pod Security Standards 直接禁止 root 容器。注意這也是 .NET 8 把預設 port 改成 8080 的原因——1024 以下的 port 需要特權。

**基底映像的選擇：**

| 映像 | 特性 |
| --- | --- |
| `aspnet:8.0` | 標準，Debian，工具齊全 |
| `aspnet:8.0-alpine` | 小，但用 musl libc，某些原生依賴（含部分 Oracle client 元件）可能不相容 |
| `aspnet:8.0-jammy-chiseled` | 極小、無 shell、無套件管理器，攻擊面最小 |

`chiseled` 的取捨很實際：**沒有 shell 意味著不能 `kubectl exec` 進去查東西**。對已經成熟、有完整可觀測性的服務很好；對還在頻繁除錯的服務會很痛苦。可以先用標準映像，穩定後再收緊。

用 Oracle 時要特別驗證 Alpine 的相容性——`Oracle.ManagedDataAccess` 是純受管的所以通常沒問題，但如果有其他原生依賴就要實測。

---

## 二、容器裡的執行時期設定

### 2.1 GC 模式

.NET 有兩種 GC 模式：

- **Workstation GC**：低延遲，適合桌面應用
- **Server GC**：每個核心一個堆積與 GC 執行緒，吞吐量高，但**記憶體用量明顯較大**

ASP.NET Core 專案預設啟用 Server GC。這在專用機器上是對的，在小記憶體的容器裡可能造成問題——每個核心一個堆積，加上更晚才回收的策略，容易撞上 memory limit 被 OOMKilled。

```dockerfile
# 記憶體受限（例如 limit 512Mi）的容器可考慮
ENV DOTNET_gcServer=0
```

.NET 也有容器感知能力——它會讀取 cgroup 的限制來決定堆積大小。但這需要 limit 有被正確設定：

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

`requests` 影響排程與 QoS 等級，`limits` 是硬上限。**記憶體超過 limit 直接 OOMKilled（不是變慢，是立刻被砍）；CPU 超過 limit 則是被 throttle（變慢）。** 這個差異決定了兩者該怎麼設：記憶體要留餘裕，CPU 可以設得緊一點。

還有一個容易忽略的互動：**CPU limit 影響 `Environment.ProcessorCount`**，進而影響 ThreadPool 的最小執行緒數（第 06 章）。設成 `500m`（半個核心）時，ThreadPool 的起始執行緒數會很小，第 06 章講的飢餓問題更容易觸發。

完整的 requests/limits 與 QoS 推導見 [[k8s-mastery]] 的第 07 章。

### 2.2 必要的環境變數

```yaml
env:
  - name: ASPNETCORE_ENVIRONMENT
    value: "Production"
  - name: ASPNETCORE_URLS
    value: "http://+:8080"           # 必須是 + 或 0.0.0.0，不能是 localhost
  - name: TZ
    value: "Asia/Taipei"             # 影響 log 時間與本地時間運算
  - name: ConnectionStrings__Default
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: connection-string
```

`TZ` 值得設，但**不要因此改用本地時間**——資料庫存 UTC、API 邊界用 `DateTimeOffset`（第 04 章）的原則不變。`TZ` 只是讓 log 與人工查看時比較直覺。

---

## 三、Migration 的執行位置

第 10 章講過不要在應用程式啟動時 `Migrate()`——多副本會同時搶著改 schema，而且 Oracle 的 DDL 隱含提交，失敗會停在中間狀態。

三個選項：

**選項一：K8s Job（推薦）**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: myapp-migrate-1-2-3
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: myapp:1.2.3            # 同一個映像
          args: ["--migrate"]
          envFrom:
            - secretRef: { name: db-credentials }
```

在 Deployment 更新之前執行。搭配 ArgoCD 的 sync wave 或 Helm hook 可以自動化這個順序。

**選項二：交給 DBA**。企業環境常見——用 `dotnet ef migrations script --idempotent` 產生腳本送審。

**選項三：initContainer**。比 Job 簡單，但每個 Pod 都會跑一次（雖然 EF Core 的 migration 有鎖不會壞，但會拖長啟動時間並可能觸發 startup probe 逾時）。

無論哪種，都要遵守**向前相容**的原則：新版 schema 必須能被舊版程式碼使用。因為滾動更新期間，新舊版本會同時運行。

「刪除欄位」這種變更要拆成兩次部署：

```text
部署 1：程式碼停止使用該欄位（欄位仍存在）
部署 2：migration 刪除欄位
```

一次做完的話，滾動更新期間還在跑的舊 Pod 會因為欄位不見而全部報錯。

---

## 四、API 版本控制

公開的 API 一旦有外部使用者，就不能隨意做破壞性變更。

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;              // 回應 header 標示支援的版本
    options.ApiVersionReader = new UrlSegmentApiVersionReader();
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});

[ApiVersion("1.0")]
[ApiVersion("2.0")]
[Route("api/v{version:apiVersion}/[controller]")]
public class OrdersController : ControllerBase
{
    [HttpGet, MapToApiVersion("1.0")]
    public IActionResult GetV1() => Ok();

    [HttpGet, MapToApiVersion("2.0")]
    public IActionResult GetV2() => Ok();
}
```

四種版本表達方式：URL 路徑（最直觀、快取友善）、query string、自訂 header、media type。**內部 API 通常用路徑就好**——它在 log、監控、快取設定上都最容易處理。

真正的重點是**判斷什麼是破壞性變更**：

| 變更 | 破壞性？ |
| --- | --- |
| 新增可選欄位到回應 | 否 |
| 新增可選參數 | 否 |
| **移除或重新命名欄位** | **是** |
| **修改欄位型別** | **是** |
| **新增必填參數** | **是** |
| **改變錯誤的狀態碼** | **是** |
| 修正錯誤的行為 | 視情況（客戶端可能已依賴那個 bug） |

只有破壞性變更需要新版本。為了每個小改動開新版本，會讓需要維護的版本數量迅速失控。

---

## 五、部署流程

以 tag 觸發的 GitHub Actions 流程為例：

```text
1. 開發者推 tag（例如 V.1.2.3.0.0）
2. CI：restore → build → test → 建置映像 → 推到 registry（tag 就是版本）
3. CI：更新 GitOps repo 裡的映像 tag
4. ArgoCD 偵測到變更 → sync
5. K8s：先跑 migration Job，再滾動更新 Deployment
6. readiness probe 通過後才接流量
7. 煙霧測試
```

幾個實務要點：

**映像 tag 用明確版本，不要用 `latest`。** `latest` 讓「現在跑的是哪一版」變成不可知，而回滾需要知道上一版是什麼。

**改 tag 時要精準。** 用 `yq` 或 `kustomize edit set image` 修改特定欄位，不要用全域 `sed` ——後者會意外改到其他服務的 tag（這是 [[k8s-mastery]] 第 13 章記錄的真實事故之一）。

**readiness probe 是滾動更新的安全帶。** 它決定「新 Pod 什麼時候開始接流量」。設得太寬鬆（例如只檢查 TCP port）會讓還沒準備好的 Pod 接到請求；設得太嚴格則會拖慢部署。

**回滾要能一鍵執行。** `kubectl rollout undo` 或 ArgoCD 的版本回退。但要注意 **migration 通常不可回滾**——所以向前相容的 schema 變更策略（第三節）才是回滾能力的真正基礎。

### 5.1 完整的 Deployment 骨架

把整本書講到的部署相關設定組起來：

```yaml
spec:
  replicas: 3
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0          # 確保容量不下降
  template:
    spec:
      terminationGracePeriodSeconds: 60     # > preStop + ShutdownTimeout
      containers:
        - name: api
          image: registry.example.com/myapp:1.2.3
          ports:
            - containerPort: 8080
          env:
            - name: ASPNETCORE_ENVIRONMENT
              value: "Production"
            - name: ASPNETCORE_URLS
              value: "http://+:8080"
          resources:
            requests: { memory: "256Mi", cpu: "200m" }
            limits:   { memory: "512Mi", cpu: "1000m" }
          startupProbe:
            httpGet: { path: /healthz/live, port: 8080 }
            failureThreshold: 30
            periodSeconds: 2                # 最多給 60 秒啟動
          livenessProbe:
            httpGet: { path: /healthz/live, port: 8080 }
            periodSeconds: 10
          readinessProbe:
            httpGet: { path: /healthz/ready, port: 8080 }
            periodSeconds: 5
          lifecycle:
            preStop:
              exec:
                command: ["sh", "-c", "sleep 10"]    # 等端點移除傳播
          securityContext:
            runAsNonRoot: true
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
```

`readOnlyRootFilesystem: true` 需要應用程式不寫入本地檔案。如果有暫存檔需求（例如檔案上傳的緩衝、`Request.EnableBuffering` 超過門檻時的落地），要掛一個 `emptyDir` 到 `/tmp`。

用 `chiseled` 映像時 `preStop` 的 `sh -c` 不可用（沒有 shell），要改用 `httpGet` 形式的 preStop hook 或調整策略。

---

## 六、上線前檢查清單

按本書章節順序：

**啟動與設定**
- [ ] `ASPNETCORE_ENVIRONMENT` 明確設定
- [ ] `ASPNETCORE_URLS` 用 `+` 或 `0.0.0.0`，port 與 `containerPort` 一致
- [ ] `ValidateScopes` / `ValidateOnBuild` 已開啟（第 00 章）
- [ ] 設定有 `ValidateOnStart()`（第 17 章）
- [ ] 沒有任何機密在版控裡（第 17 章）

**Pipeline 與安全**
- [ ] middleware 順序正確，`UseForwardedHeaders` 在最前面（第 01、13 章）
- [ ] `UseHttpsRedirection` 在 TLS 終結於 Ingress 時**不要**啟用（第 00 章）
- [ ] `FallbackPolicy` 已設定，健康檢查端點 `AllowAnonymous`（第 14、16 章）
- [ ] JWT 四個 `Validate*` 全為 true，`ClockSkew` 已調整（第 12 章）
- [ ] CORS 白名單不含萬用字元（第 01 章）

**資料**
- [ ] 沒有 `EnableSensitiveDataLogging`（第 08 章）
- [ ] 列表查詢用投影，沒有 N+1（第 08 章）
- [ ] Migration 由 Job 執行，且 schema 變更向前相容（第 10、21 章）
- [ ] 連線池大小 × 副本數在資料庫的承載範圍內（第 10 章）

**韌性**
- [ ] 所有 `HttpClient` 走 `IHttpClientFactory`，逾時已設（第 18 章）
- [ ] 沒有 `.Result` / `.Wait()`（第 06 章）
- [ ] 背景工作在多副本下不會重複執行（第 19 章）

**部署**
- [ ] liveness 不檢查外部依賴（第 16 章）
- [ ] `terminationGracePeriodSeconds` > preStop + `ShutdownTimeout`（第 00 章）
- [ ] 資源 requests/limits 已設定
- [ ] 映像 tag 是明確版本，非 root 執行

---

## 七、常見誤解

**「Dockerfile 就是把檔案複製進去。」**
layer 順序決定建置速度。先 restore 再 copy 原始碼，能讓改一行程式碼的重建從幾分鐘降到幾十秒。

**「用 SDK 映像當 runtime 比較方便除錯。」**
體積大好幾倍，且包含編譯器等不必要的攻擊面。用多階段建置，runtime 用 `aspnet`。

**「Server GC 效能比較好，一定要開。」**
它每個核心一個堆積，記憶體用量明顯較大。小記憶體的容器可能因此 OOMKilled，值得實測後決定。

**「應用程式啟動時跑 migration 最方便。」**
多副本同時搶著改 schema，Oracle 的 DDL 隱含提交會停在中間狀態，而且會拖長啟動時間觸發 probe 逾時。用 Job。

**「回滾就是把映像換回舊版。」**
如果 migration 已經刪了欄位，舊版程式碼跑不起來。回滾能力的基礎是向前相容的 schema 變更策略。

**「API 每次改動都要開新版本。」**
只有破壞性變更需要。新增可選欄位不是破壞性的。過度版本化會讓維護成本失控。

---

## 八、同事會來問你的問題

**Q：改一行程式碼，Docker build 要跑五分鐘。**
`COPY . .` 放在 `dotnet restore` 之前，導致每次都重新還原套件。先只複製 `.csproj` 做 restore，再複製其餘原始碼。

**Q：Pod 一直 OOMKilled，本機測記憶體明明夠。**
Server GC 在容器裡的記憶體用量較大。確認 limits 設定合理（讓 .NET 的容器感知能正確計算堆積），必要時測試 `DOTNET_gcServer=0`。也要排除第 07 章的 change tracker 累積與第 18 章的無上限 `IMemoryCache`。

**Q：CPU limit 設 `500m` 之後偶發逾時變多。**
CPU limit 影響 `Environment.ProcessorCount`，進而影響 ThreadPool 的最小執行緒數。半個核心會讓第 06 章的飢餓問題更容易觸發。要嘛放寬 limit，要嘛確保程式碼裡沒有任何同步阻塞。

**Q：migration 該放哪裡執行？**
獨立的 K8s Job，在 Deployment 更新前跑。用 ArgoCD sync wave 或 Helm hook 控制順序。企業環境也可以產生 idempotent 腳本交給 DBA。

**Q：滾動更新時舊版報錯，因為新 migration 刪了欄位。**
schema 變更必須向前相容。刪欄位拆成兩次部署：先讓程式碼停止使用，下一次部署才真的刪除。

**Q：`readOnlyRootFilesystem` 開了之後應用程式起不來。**
應用程式在寫本地檔案。掛一個 `emptyDir` 到 `/tmp`，並確認 log 是寫 stdout 而不是檔案（第 16 章）。

**Q：什麼算破壞性 API 變更？**
移除或重新命名欄位、改型別、新增必填參數、改變錯誤狀態碼。新增可選欄位與可選參數不是。只有破壞性變更才需要開新版本。

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[20-testing]] — 上一章
- [[22-self-assessment]] — 下一章：自我檢測
- [[00-hosting-and-startup]] — 容器裡的啟動與關機
- [[16-logging-and-observability]] — probe 端點的設計
- [[17-configuration-and-secrets]] — 設定與 Secret 注入
- [[k8s-mastery]] — K8s 端的完整教材
- [[docker]] — 容器基礎
