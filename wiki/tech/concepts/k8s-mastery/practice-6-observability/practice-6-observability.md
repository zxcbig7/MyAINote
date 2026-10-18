---
type: concept
domain: tech
tags: [kubernetes, k8s, observability, prometheus, grafana, alerting, logging, slo, hands-on]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 實戰第六章：知道它好不好

前五章把服務部署起來、接上資料庫、自動化了。但有一個問題還沒回答：**它現在到底好不好？**

這個問題比想像中難，因為「服務掛了」很好發現，「服務怪怪的」才是日常。回應變慢一倍、錯誤率從 0.1% 升到 2%、某個 API 特別慢——這些不會讓任何 Pod 變紅，`kubectl get pods` 全部 Running，但使用者已經在抱怨了。

這一章的目標很具體：**讓你在使用者告訴你之前就知道出事了，而且知道從哪裡查。**

## 先想清楚：你要回答哪些問題

不要從工具開始想，從問題開始想。維運一個服務時，你需要能回答四類問題：

| 問題 | 靠什麼回答 |
| --- | --- |
| 「現在正常嗎？」「比昨天差嗎？」 | **Metrics**（數字、時間序列） |
| 「這個請求為什麼失敗？」 | **Logs**（單一事件的細節） |
| 「這個請求慢在哪一段？」 | **Traces**（跨服務的呼叫鏈） |
| 「有人在半夜出事時被叫醒嗎？」 | **Alerting**（把前三者變成行動） |

這四者的分工很明確：**metrics 告訴你「有問題」，logs 告訴你「什麼問題」，traces 告訴你「問題在誰身上」。** 只做其中一個都會有明顯的盲區——只有 metrics 你知道錯誤率升高但不知道為什麼；只有 logs 你要在幾百萬行裡撈針，而且看不出趨勢。

以下按這個順序建立。

---

## Part 1：Metrics

### 應用要先吐出指標

Prometheus 是 **pull 模型**——它主動來抓，不是你推給它。所以第一步是讓應用提供一個 `/metrics` 端點。

ASP.NET Core 現在建議走 OpenTelemetry（它同時涵蓋 metrics 與 traces，之後要加追蹤不用重來）：

```csharp
builder.Services.AddOpenTelemetry()
    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()   // HTTP 請求的延遲、狀態碼、路由
        .AddRuntimeInstrumentation()      // GC、ThreadPool、記憶體
        .AddPrometheusExporter());

var app = builder.Build();
app.MapPrometheusScrapingEndpoint();      // 預設 /metrics
```

驗證一下：

```powershell
kubectl port-forward deploy/api 8080:8080
curl.exe http://localhost:8080/metrics | Select-String "http_server"
```

看到一堆 `http_server_request_duration_seconds_bucket{...}` 就對了。

### 讓 Prometheus 找到它

裝了 Prometheus Operator 的話，用 `ServiceMonitor` 宣告「來抓我」（附錄 C-5 有全欄位）：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api
  namespace: demo
  labels:
    release: prometheus # 必須符合 Prometheus 的 serviceMonitorSelector
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: api # 選的是 Service，不是 Pod
  namespaceSelector:
    matchNames: [demo]
  endpoints:
    - port: http # Service 的 port 名稱，不是數字
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

**「Prometheus 抓不到我的服務」有三個原因，按這個順序查：**

1. **ServiceMonitor 自己的 label 不符合 Prometheus 的 `serviceMonitorSelector`**。多數 Helm chart 要求 `release: <你的 helm release 名>`。這是第一名，而且完全沒有錯誤訊息——Prometheus 只是靜靜地忽略你。
2. **`endpoints.port` 寫成數字**。它要的是 Service 裡 `ports[].name` 的值。
3. **`namespaceSelector` 沒涵蓋目標 namespace**。

驗證方式是打開 Prometheus UI 的 **Status → Targets**，你的服務應該在裡面且狀態是 `UP`。不在清單裡就是 1 或 3，在清單裡但 `DOWN` 就是網路或 port 問題。

### 該看哪些指標：四個黃金訊號

不要從「有哪些指標」開始選，從「使用者會抱怨什麼」開始選。**RED 方法**給了對請求型服務最實用的三個，加上飽和度就是四個黃金訊號：

| 訊號 | 意義 | PromQL |
| --- | --- | --- |
| **Rate**（流量） | 每秒請求數 | `sum(rate(http_server_request_duration_seconds_count{job="api"}[5m]))` |
| **Errors**（錯誤） | 5xx 比例 | `sum(rate(http_server_request_duration_seconds_count{job="api",http_response_status_code=~"5.."}[5m])) / sum(rate(http_server_request_duration_seconds_count{job="api"}[5m]))` |
| **Duration**（延遲） | P95 延遲 | `histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{job="api"}[5m])))` |
| **Saturation**（飽和度） | CPU throttle 比例 | `sum(rate(container_cpu_cfs_throttled_seconds_total{pod=~"api-.*"}[5m]))` |

四個裡面最容易被忽略的是最後一個。**CPU throttle 是「服務變慢但所有健康檢查都正常」的隱形殺手**（附錄 D 的實驗 A4 讓你親手做過一次）——Pod 是 Running、probe 全過、日誌乾淨，唯一的症狀是 P95 變差。不把它放進儀表板，你會查很久。

延遲那條的寫法值得說明：`histogram_quantile` **必須先 `rate` 再 `sum by (le)`**，順序反了算出來的數字沒有意義。這是 PromQL 最常見的錯誤之一（正文第 14 章有完整推導）。

### 高基數：會把 Prometheus 打死的寫法

指標的每一組標籤組合都是一條獨立的時間序列。所以這樣加標籤是災難：

```csharp
// 錯：把完整路徑當標籤
counter.Add(1, new("path", "/api/users/12345"));
```

一百萬個使用者 ID 就是一百萬條時間序列，Prometheus 記憶體直接爆掉。

正確做法是用**路由樣板**而不是實際路徑：

```csharp
// 對：/api/users/{id}
counter.Add(1, new("route", "/api/users/{id}"));
```

`AddAspNetCoreInstrumentation()` 預設就是用 `http_route`（樣板），所以照上面的設定不會有事。但自己加指標時要記住這條規則：**標籤的可能值必須是有限且可枚舉的**。使用者 ID、trace ID、完整 URL、時間戳都不能當標籤。

已經產生高基數了，可以在 ServiceMonitor 用 `metricRelabelings` 丟掉（附錄 C-5）。

---

## Part 2：Logs

### 容器日誌的路徑

入門第五章講過：**容器裡的檔案會消失，所以日誌要輸出到 stdout**。完整路徑是：

```
應用 → stdout → container runtime 寫成 Node 上的檔案
    → 收集器（Filebeat / Fluent Bit / Promtail）讀取
    → 送到 Elasticsearch / Loki
```

`kubectl logs` 讀的是 Node 上那個檔案，所以它有兩個限制：**Pod 刪掉就沒了**、**檔案輪替之後舊的就沒了**。這就是為什麼一定要有集中式的日誌收集——你需要查的往往正好是已經被重建的那個 Pod。

Node 上的日誌大小由 kubelet 的 `containerLogMaxSize` × `containerLogMaxFiles` 控制（附錄 C-6）。沒設好會撐爆磁碟，觸發 `DiskPressure` 把整台 Node 上的 Pod 全部驅逐。

### 結構化日誌

寫成文字的日誌只能用關鍵字搜尋，寫成結構化的才能查詢與聚合。

```csharp
// 錯：字串內插，欄位無法被查詢
logger.LogInformation($"User {userId} placed order {orderId}");

// 對：樣板 + 參數，userId 與 orderId 變成可查詢的欄位
logger.LogInformation("User {UserId} placed order {OrderId}", userId, orderId);
```

差別在於後者送出去的是一個帶欄位的物件，你可以在 Kibana 下 `UserId: 12345` 這種查詢，也可以聚合「每個使用者的錯誤數」。前者只能做全文搜尋。

**這個差異在事故當下的價值極大**：「找出所有 user 12345 在過去一小時的失敗請求」用結構化日誌是一行查詢，用字串日誌是一場惡夢。

### 把日誌跟指標串起來

看到指標上的尖峰，要能跳到對應的日誌。串接的鑰匙是 **trace ID**：

```csharp
builder.Logging.Configure(o =>
    o.ActivityTrackingOptions = ActivityTrackingOptions.TraceId | ActivityTrackingOptions.SpanId);
```

ASP.NET Core 會自動產生 W3C 格式的 trace ID 並放進日誌 scope。錯誤回應也把它帶回去給使用者：

```csharp
app.UseExceptionHandler(...);  // ProblemDetails 裡帶上 traceId
```

於是使用者回報「我剛剛下單失敗，代碼 00-4bf92f...」時，你直接拿那串去 Kibana 查，一秒定位。**這是投入產出比最高的可觀測性投資之一。**

### 不要記什麼

- 密碼、token、金鑰、連線字串
- 個資（身分證、信用卡、完整地址）
- 完整的請求 body（可能含上述任何一項）

日誌通常保留數週、多人可讀、可能被匯出。**把密碼寫進日誌等同於外洩**，而且事後很難清乾淨。

---

## Part 3：Traces（簡述）

單體服務時 logs 就夠了。一旦請求跨越多個服務（前端 → API → 另一個 API → 資料庫），你需要知道「這 800ms 花在哪一段」，這就是 tracing。

```csharp
builder.Services.AddOpenTelemetry()
    .WithTracing(t => t
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddOtlpExporter());   // 送到 Tempo / Jaeger
```

兩個實務重點：**採樣率不要設 100%**（正式環境常見 1–10%，全部收集的儲存成本很可觀），以及**確保 trace context 在服務之間傳遞**——`HttpClient` 的 instrumentation 會自動加上 `traceparent` header，但如果中間經過訊息佇列，要自己傳。

還沒有多服務呼叫鏈的話，這部分可以先跳過，但**metrics 用 OpenTelemetry 建置就是為了之後加 traces 不用重來**。

---

## Part 4：告警

### 原則：只對需要人立刻做事的狀況告警

這是最重要的一條，而且最常被違反。CPU 使用率 80% 不是告警（那是儀表板上的一條線），**使用者受影響**才是告警。

判準很簡單：**這條告警半夜把人叫起來，那個人能做什麼？** 答不出來的就不該是告警。

第二條原則：**從 SLO 導出告警，不要從指標導出告警。** 「P95 延遲 > 500ms」是一個指標門檻，很容易誤報；「錯誤預算在一小時內燒掉了 2%」才是真的該有人處理。

### 這組服務實際需要的六條

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  namespace: demo
  labels:
    release: prometheus
spec:
  groups:
    - name: api.rules
      interval: 30s
      rules:
        - alert: ApiHighErrorRate
          expr: |
            sum(rate(http_server_request_duration_seconds_count{job="api",http_response_status_code=~"5.."}[5m]))
            / sum(rate(http_server_request_duration_seconds_count{job="api"}[5m])) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "API 5xx 比例超過 5%"
            runbook_url: "https://wiki/runbooks/api-high-error-rate"

        - alert: ApiHighLatency
          expr: |
            histogram_quantile(0.95,
              sum by (le) (rate(http_server_request_duration_seconds_bucket{job="api"}[5m]))
            ) > 1
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "API P95 延遲超過 1 秒"
            runbook_url: "https://wiki/runbooks/api-latency"

        - alert: ApiPodCrashLooping
          expr: rate(kube_pod_container_status_restarts_total{namespace="demo",pod=~"api-.*"}[15m]) > 0
          for: 15m
          labels:
            severity: critical
          annotations:
            summary: "API Pod 反覆重啟"
            runbook_url: "https://wiki/runbooks/crashloop"

        - alert: ApiNotEnoughReplicas
          expr: kube_deployment_status_replicas_available{namespace="demo",deployment="api"} < 2
          for: 10m
          labels:
            severity: critical
          annotations:
            summary: "API 可用副本少於 2"

        - alert: ApiCpuThrottling
          expr: |
            sum(rate(container_cpu_cfs_throttled_periods_total{namespace="demo",pod=~"api-.*"}[5m]))
            / sum(rate(container_cpu_cfs_periods_total{namespace="demo",pod=~"api-.*"}[5m])) > 0.25
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "API 被 CPU throttle 超過 25%（服務會變慢但不會報錯）"

        - alert: ApiDbConnectionsHigh
          expr: sum(oracle_sessions_active) > 400
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "資料庫連線數接近上限（實戰 5 的乘法問題）"
```

幾個設計上的細節值得說明：

**`for` 是去抖動的關鍵。** 沒有它，任何一個瞬間尖峰都會發告警。`for: 5m` 的意思是「持續五分鐘都成立才真的告警」，這一個欄位就能消掉大部分誤報。

**每條都有 `runbook_url`。** 附錄 H 強調過：半夜被叫起來的人需要的是「下一步做什麼」，不是「哪個指標超標」。

**最後兩條特別重要**，因為它們對應的是「不會讓任何東西變紅」的問題：CPU throttle 讓服務變慢但一切正常，資料庫連線接近上限則是在等一次擴容把它推爆（實戰第五章的乘法問題）。

**分級要對應行動：** `critical` 半夜 page 人，`warning` 上班時間處理。全部都設 critical 的結果是所有人都關掉通知。

---

## Part 5：儀表板

一個服務一頁，由上而下的順序是刻意的——**最上面回答「有沒有事」，往下回答「哪裡出事」**：

| 區塊 | 放什麼 |
| --- | --- |
| 第一排（四個大數字） | 目前 QPS、錯誤率、P95 延遲、可用副本數 |
| 第二排 | 錯誤率與延遲的時間序列（可以看趨勢與比較昨天） |
| 第三排 | 狀態碼分布（2xx/4xx/5xx 堆疊）、依路由的延遲排行 |
| 第四排 | 資源：CPU/記憶體用量 vs limit、**throttle 比例**、重啟次數 |
| 第五排 | 依賴：資料庫連線數、下游服務的延遲與錯誤 |

實務上不必自己從零做——`kube-prometheus-stack` 內建了叢集與工作負載層的儀表板，你只需要額外做一頁「應用層」的。

---

## 驗證：故意弄壞一次

**沒有測過的監控等於沒有監控。** 最後一步是驗證整條鏈真的會動：

```powershell
# 1. 製造錯誤，確認錯誤率指標動了
kubectl exec deploy/api -- sh -c "for i in $(seq 1 50); do wget -q -O- localhost:8080/this-does-not-exist; done"

# 2. 殺掉副本，確認可用副本告警會觸發
kubectl scale deployment api --replicas=1

# 3. 確認告警真的送到收件人手上（不是只在 Prometheus UI 變紅）
# Alertmanager → Slack/Email/PagerDuty 這一段最常斷掉
```

第三步是最常被跳過、也最常出問題的。**告警規則正確、Alertmanager 收到了，但通知管道設定錯誤**，於是它安靜地什麼都沒送出——這種故障只有主動測試才會發現，而發現的時機通常是真的出事之後。

附錄 H 建議的頻率是每季至少驗一次通知鏈路。

---

## 常見坑

| # | 症狀 | 原因 |
| --- | --- | --- |
| 1 | Prometheus 抓不到服務 | ServiceMonitor 的 label 不符合 `serviceMonitorSelector` |
| 2 | Target 存在但 DOWN | `endpoints.port` 寫數字而非名稱；或 NetworkPolicy 擋掉 |
| 3 | Prometheus 記憶體暴增 | 高基數標籤（把 ID、路徑當 label） |
| 4 | P95 數字很怪 | `histogram_quantile` 沒有先 `rate` 再 `sum by (le)` |
| 5 | 告警一直誤報 | 沒設 `for`，瞬間尖峰就觸發 |
| 6 | 沒人理告警 | 太多、沒有 runbook、分級不對 |
| 7 | 查不到昨天的日誌 | 只靠 `kubectl logs`，Pod 已重建 |
| 8 | 日誌搜尋很難用 | 用字串內插而非結構化參數 |
| 9 | 服務變慢但什麼都正常 | 沒監控 CPU throttle |
| 10 | 告警在 UI 紅了但沒人收到 | Alertmanager 通知管道沒測過 |

## 檢查清單

- [ ] 應用曝露 `/metrics`，用 OpenTelemetry 建置（之後加 traces 不用重來）
- [ ] ServiceMonitor 的 label 符合 Prometheus 的 selector，且 Targets 頁面看得到 `UP`
- [ ] 沒有把 ID／完整路徑當標籤
- [ ] 四個黃金訊號都在儀表板上，**包含 CPU throttle**
- [ ] 日誌是結構化的，且帶 trace ID
- [ ] 錯誤回應把 trace ID 回傳給使用者
- [ ] 日誌沒有記密碼與個資
- [ ] 每條告警都有 `for` 與 `runbook_url`
- [ ] 告警分成 page 與 ticket 兩級
- [ ] **通知鏈路實際測過**（不是只在 Prometheus UI 看到紅字）
- [ ] 資料庫連線數有監控（實戰 5 的乘法問題）

## 本章回顧

- metrics 說「有問題」、logs 說「什麼問題」、traces 說「問題在誰身上」
- Prometheus 是 pull 模型，抓不到的第一原因永遠是 ServiceMonitor 的 label
- 四個黃金訊號裡最容易漏的是 **CPU throttle**——它讓服務變慢卻不讓任何東西變紅
- 標籤的可能值必須有限且可枚舉，否則高基數會打死 Prometheus
- 結構化日誌 + trace ID 是投入產出比最高的可觀測性投資
- 告警只對「需要人立刻做事」的狀況發出，每條都要有 runbook
- `for` 欄位消掉大部分誤報
- **沒有測過的監控等於沒有監控**，尤其是通知這一段

## 自我檢查

1. 錯誤率升高了，你會先看 metrics、logs 還是 traces？為什麼？
2. Prometheus 看不到你的服務，第一個檢查什麼？
3. 為什麼不能把使用者 ID 當成指標標籤？
4. 服務變慢但 Pod 全部 Running、probe 全過、日誌乾淨，你懷疑什麼？
5. 告警規則寫好了、Prometheus UI 也變紅了，為什麼還可能沒人知道出事？

實戰篇到此結束——你已經走完「寫程式 → 容器化 → 部署 → 自動化 → 接資料庫 → 看得見」的完整鏈路。接下來把原理補齊，正文十六章與附錄就是為此存在。

## 連結

- [[74-distributed-tracing]] — 附錄 AZ：第三支柱與「告警→metrics→trace→logs」完整動線
- [[64-slo-and-alerting]] — 附錄 AP：「從 SLO 導出告警」具體怎麼做，含可直接抄的 PromQL
- [[practice-5-database-and-state]] — 上一章：接上資料庫
- [[14-prometheus-grafana]] — 正文：pull 模型、四種 metric type、PromQL 深入、USE/RED
- [[15-elk-elastic]] — 正文：日誌收集路徑、倒排索引、KQL
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：ServiceMonitor/PrometheusRule 全欄位
- [[30-production-readiness]] — 附錄 H：必備告警清單與事故流程
- [[29-status-and-conditions]] — 附錄 G：狀態判讀
- [[26-lab-drills]] — 附錄 D：親手製造 CPU throttle 等故障
- [[k8s-mastery]] — 教材總目錄（含各階段的閱讀路徑）
