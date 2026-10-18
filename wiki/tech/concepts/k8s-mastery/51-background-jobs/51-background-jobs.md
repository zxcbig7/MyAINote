---
type: reference
domain: tech
tags: [kubernetes, k8s, cronjob, background-jobs, leader-election, batch, scheduling]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 AC：排程任務與背景工作

附錄 C-2 把 `Job` 與 `CronJob` 的欄位攤平了，但沒有回答一個更前面的問題：**這個背景工作到底該用哪一種形式？**

這件事在遷移上 K8s 時特別容易出錯，原因附錄 U 提過一次——**舊系統的排程常常藏在作業系統的設定裡**（Windows 排程工作、crontab、或應用內的 Timer），沒有文件、沒人記得，搬過去之後才發現「那個對帳每天跑了三次」。

這一份講背景工作的形式選擇、多副本帶來的重複執行問題、CronJob 的實際陷阱，以及長時間任務該怎麼設計。

---

## Part 1：四種形式怎麼選

| 形式 | 適合 | 不適合 |
| --- | --- | --- |
| **CronJob** | 定時、獨立、可重跑的工作 | 秒級精度、需要複雜依賴關係 |
| **Job** | 一次性任務（migration、資料修補） | 週期性 |
| **應用內背景服務** | 需要共用應用狀態、高頻輪詢、事件驅動 | **多副本下會重複執行** |
| **專用排程系統**（Hangfire / Temporal） | 複雜工作流、需要重試視覺化、動態排程 | 簡單的定時任務（殺雞用牛刀） |

決策順序：

1. **是一次性的嗎？** → `Job`
2. **是固定週期、且能獨立跑完就結束嗎？** → **`CronJob`（優先選這個）**
3. **需要一直活著監聽（訊息、事件）嗎？** → 應用內背景服務 或 consumer Deployment（附錄 AA）
4. **有複雜的工作流、依賴、動態排程需求嗎？** → 專用排程系統

**CronJob 是預設選擇**，理由有三個：它天然是單例執行（不會重複）、有內建的重試與歷史紀錄、而且**排程本身變成 git 裡的一份 YAML**——不會再有「排程藏在某台機器的設定裡」這種事。

---

## Part 2：應用內背景工作的多副本問題

**這是遷移上 K8s 最常見的事故之一。**

單機時，在應用裡寫一個定時器很自然：

```csharp
public class ReportService : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromHours(1));
        while (await timer.WaitForNextTickAsync(ct))
            await GenerateReportAsync(ct);   // 每小時產一次報表
    }
}
```

**部署三個副本之後，這段程式碼每小時執行三次。** 而且症狀不一定明顯——如果它是「產生報表」可能只是多幾份檔案，如果它是「發送提醒信」就是使用者收到三封，如果它是「扣款」那就是事故。

### 三種解法

| 解法 | 做法 | 取捨 |
| --- | --- | --- |
| **抽成 CronJob**（推薦） | 把工作從應用裡拿出來，變成獨立的 CronJob | 最乾淨；但需要能獨立執行的進入點 |
| **Leader election** | 多副本選出一個 leader，只有它執行 | 應用複雜度增加，但不必拆程式碼 |
| **分散式鎖** | 執行前先搶鎖（Redis / DB） | 簡單，但要處理鎖過期與死鎖 |

**「只跑一個副本」不是解法**——那放棄了高可用，而且滾動更新期間仍然可能有兩個副本同時存在。

### K8s 原生的 Leader Election

K8s 自己的 controller 就是用 `Lease` 物件選主（附錄 C-6），你的應用也可以用同一套機制：

```yaml
# 需要的 RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: leader-election
  namespace: demo
rules:
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "create", "update"]
```

概念上的運作方式：每個副本嘗試建立／更新一個 Lease，成功的成為 leader 並持續續約；其他副本觀察到 Lease 還在有效期內就不動作。leader 掛掉之後 Lease 過期，其他副本接手。

**三個實作上的注意事項**：續約間隔要遠小於租約期限（否則網路抖一下就換手）、**leader 換手期間可能有短暫的重疊或空窗**（所以工作仍需冪等）、以及要處理「我以為我是 leader 但其實已經失去」的情況。

**多數情況下抽成 CronJob 更簡單。** Leader election 適合「需要持續執行、無法拆成獨立進入點」的工作，例如一個持續消費事件並維護記憶體狀態的元件。

---

## Part 3：CronJob 的實際陷阱

### 陷阱一：時區

`spec.timeZone` 不設就是 **UTC**。凌晨三點的排程會跑在上午十一點。這在附錄 C-2 講過，但它值得再提一次，因為它是最常見的單一錯誤：

```yaml
spec:
  schedule: "0 3 * * *"
  timeZone: "Asia/Taipei"   # 不寫就是 UTC
```

還有一個延伸問題：**有日光節約時間的時區，某些時刻會不存在或出現兩次**。台灣沒有這個問題，但如果排程是給跨國系統用的，要意識到「凌晨 2:30」在切換日可能不會發生或發生兩次。

### 陷阱二：錯過的執行

CronJob controller 不是隨時醒著的。如果控制平面重啟、或叢集忙碌，排程時間可能被錯過。這時候 `startingDeadlineSeconds` 決定行為：

| 設定 | 行為 |
| --- | --- |
| 不設 | 錯過多久都會補跑 |
| 設 `300` | 錯過超過五分鐘就跳過這次 |

而有一個**很少人知道但會咬人的規則**：如果 controller 發現**錯過超過 100 次排程**，它會停止排程並在 event 記錄錯誤——`CronJob` 從此不再執行，直到有人介入。

這在什麼情況會發生？`startingDeadlineSeconds` 設得很短（例如 10 秒）而 controller 短暫不可用，或者 CronJob 被 `suspend` 了很久之後才恢復。**症狀是「這個排程突然就不跑了」，而且不會有告警。**

務實的設定：`startingDeadlineSeconds` 給一個合理的寬限（幾分鐘到幾十分鐘），不要設得太短。

### 陷阱三：重疊執行

前一次還沒跑完、下一次時間到了：

| `concurrencyPolicy` | 行為 |
| --- | --- |
| `Allow`（預設） | 兩個同時跑 |
| `Forbid` | 跳過這次 |
| `Replace` | 殺掉舊的、跑新的 |

**預設值 `Allow` 對多數批次工作是錯的。** 對帳、報表、資料同步這類工作同時跑兩份，輕則浪費資源、重則資料重複。**需求裡只要出現「不能同時跑兩份」，就要設 `Forbid`。**

但注意 `Forbid` 的副作用：如果某一次卡住不結束，**後續所有排程都會被跳過**，而且同樣不會有告警。所以 `Forbid` 一定要配 `activeDeadlineSeconds` 給它一個上限。

### 陷阱四：長時間任務被打斷

Job 的 Pod 跟其他 Pod 一樣會被驅逐——節點資源不足、`kubectl drain`、spot 節點被收回、或優先級較高的 Pod 搶佔（附錄 S）。

三個保護手段：

```yaml
spec:
  jobTemplate:
    spec:
      template:
        spec:
          priorityClassName: batch-normal          # 明確的優先級
          terminationGracePeriodSeconds: 300       # 給它時間收尾
          containers:
            - name: job
              lifecycle:
                preStop:
                  exec:
                    command: ["/bin/sh", "-c", "touch /tmp/stopping"]
```

但**最根本的保護是讓工作可以被中斷並續跑**（Part 4）。長時間的批次工作不該假設自己能不被打斷地跑完。

---

## Part 4：長時間任務的設計

### 分批處理，不要一次撈全表

```csharp
// 反模式：一次載入全部
var all = await db.Orders.Where(o => !o.Reconciled).ToListAsync();

// 正解：分批 + 記錄進度
var lastId = await LoadCheckpointAsync();
while (!ct.IsCancellationRequested)
{
    var batch = await db.Orders
        .Where(o => !o.Reconciled && o.Id > lastId)
        .OrderBy(o => o.Id).Take(1000).ToListAsync(ct);
    if (batch.Count == 0) break;

    await ProcessAsync(batch, ct);
    lastId = batch[^1].Id;
    await SaveCheckpointAsync(lastId);   // 每批之後存進度
}
```

**一次撈全表的三個問題**：記憶體用量隨資料成長（早晚 OOMKilled）、交易時間過長（鎖住資料表、佔用連線）、以及**被中斷就要全部重來**。

分批之後三個問題都解決了，而且進度可以被觀察。

### 讓中斷變成可接受的事

```csharp
protected override async Task ExecuteAsync(CancellationToken ct)
{
    // ct 在收到 SIGTERM 時會被取消
    // 應用要做的是：停在一個安全的批次邊界，存好 checkpoint，然後正常退出
}
```

配合 `terminationGracePeriodSeconds` 給足時間，Pod 被驅逐時工作能乾淨地停在某個進度，下次啟動從那裡繼續。**這正是附錄 S 說「spot 節點跑批次要有 checkpoint」的具體實作。**

### 冪等仍然是必須

跟附錄 AA 的訊息處理一樣：工作可能被重跑（重試、驅逐後續跑、人為重新觸發），所以**每一批的處理都要能安全地重複執行**。實作上通常是「處理完標記狀態」而不是「假設只會處理一次」。

### 上限與取消

```yaml
spec:
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 7200   # 牆鐘時間上限，優先於 backoffLimit
      ttlSecondsAfterFinished: 86400
```

`activeDeadlineSeconds` 是避免「卡住的任務永遠佔著資源」的保險絲。設一個比預期最長執行時間寬鬆但有限的值。

---

## Part 5：監控——「沒跑」比「跑錯」更難發現

**這是背景工作與線上服務最大的差異。**

線上服務掛了，使用者會抱怨、錯誤率會上升、告警會響。**背景工作沒跑，通常是安靜的**——沒有人在等它的回應，直到月底對帳對不上才發現「那個排程三週前就停了」。

所以背景工作需要**主動監控「它有沒有跑」**，而不只是「跑的時候有沒有錯」。

### 三種偵測「沒跑」的方式

**1. 用 kube-state-metrics 看最後執行時間**

```promql
# 距離上次排程超過 26 小時（給每日任務一點寬限）
time() - kube_cronjob_status_last_schedule_time{cronjob="reconcile"} > 26 * 3600
```

**2. Dead man's switch（推薦）**

讓工作**成功完成時**主動送一個訊號出去；告警規則反過來偵測「訊號消失」。

Prometheus 是 pull 模型，抓不到短命的 Job（附錄 AA 的 consumer 至少是長期存在的，Job 跑完就沒了）。所以要用 **Pushgateway**：

```powershell
# Job 成功結束前推一個時間戳
echo "batch_job_last_success_timestamp $(date +%s)" | curl.exe --data-binary @- http://pushgateway:9091/metrics/job/reconcile
```

```promql
# 超過 26 小時沒有成功紀錄就告警
time() - batch_job_last_success_timestamp{job="reconcile"} > 26 * 3600
```

**這個模式的好處是它涵蓋所有失敗形態**——Job 沒被建立、Pod 沒排上、程式跑到一半當掉、或整個 CronJob 被誤刪，症狀都是「訊號消失」。

**3. 業務層的檢查。** 最可靠但也最貴：直接查「昨天的對帳結果存在嗎」。適合關鍵任務。

### 其他該監控的

| 指標 | 為什麼 |
| --- | --- |
| 執行時間趨勢 | 逐漸變長 = 資料成長，早晚會撞到 `activeDeadlineSeconds` |
| 失敗率 | `kube_job_status_failed` |
| 處理筆數 | 突然變成 0 可能是查詢條件出錯（而不是「沒資料」） |
| 佇列／待處理量 | 有沒有處理不完 |

**「執行時間趨勢」值得特別看**：一個原本跑五分鐘的對帳，半年後跑五十分鐘——它還是「成功」的，但已經在往超時的方向走。這種問題只有看趨勢才會發現。

---

## Part 6：批次工作的反模式

| # | 反模式 | 後果 | 正解 |
| --- | --- | --- | --- |
| 1 | 一次撈全表 | OOMKilled、長交易、中斷要重來 | 分批 + checkpoint |
| 2 | 沒有斷點續跑 | 跑到 95% 被驅逐，全部重來 | 每批存進度 |
| 3 | 用 `while(true) + sleep` 輪詢資料庫 | 浪費連線與 CPU；改設定要重部署 | 用 CronJob，或事件驅動 |
| 4 | 在應用啟動時做重活 | 拖慢啟動、多副本重複做、probe 逾時 | 抽成獨立的 Job |
| 5 | 沒有 `activeDeadlineSeconds` | 卡住的任務永遠佔資源 | 設一個保險絲 |
| 6 | 沒有 `ttlSecondsAfterFinished` | Completed Pod 堆積撐爆 etcd | 設幾百到幾千秒 |
| 7 | `concurrencyPolicy` 用預設 `Allow` | 重疊執行造成資料重複 | 需要就設 `Forbid` + deadline |
| 8 | 失敗就無限重試 | 燒資源且掩蓋問題 | `backoffLimit` + DLQ 思維 |
| 9 | 只在失敗時告警 | 「沒跑」完全不會被發現 | Dead man's switch |
| 10 | 排程寫死在程式碼裡 | 改時間要重新部署 | 放在 CronJob 的 `schedule` |

第 4 項值得展開：**「應用啟動時做重活」是遷移時常見的模式**——單機時在 `Startup` 裡跑資料初始化很方便，但在 K8s 上它會拖慢啟動（`startupProbe` 可能逾時）、每個副本都做一次、而且擴容時又做一次。正確做法是抽成獨立的 Job，用 ArgoCD 的 PreSync hook 在部署前跑（實戰第三章）。

---

## 檢查清單

**形式選擇**

- [ ] 定時且可獨立跑完的工作**優先用 CronJob**，不要寫在應用裡
- [ ] 應用內的背景工作已確認多副本下不會重複執行
- [ ] 用 leader election 的話，工作本身仍然是冪等的
- [ ] **沒有用「只跑一個副本」當作去重手段**

**CronJob 設定**

- [ ] `timeZone` 有設（不設就是 UTC）
- [ ] `concurrencyPolicy` 依需求設定，`Forbid` 時配 `activeDeadlineSeconds`
- [ ] `startingDeadlineSeconds` 有合理寬限（不要太短）
- [ ] `backoffLimit` 與 `ttlSecondsAfterFinished` 都有設
- [ ] `failedJobsHistoryLimit` 調大一點方便排查

**長時間任務**

- [ ] 分批處理，不一次撈全表
- [ ] 每批存 checkpoint，可斷點續跑
- [ ] 處理是冪等的
- [ ] 正確處理 SIGTERM，停在安全的批次邊界
- [ ] `terminationGracePeriodSeconds` 足夠收尾

**監控**

- [ ] **有偵測「沒跑」的機制**（dead man's switch 或 last_schedule_time）
- [ ] 執行時間趨勢有在看
- [ ] 處理筆數突然歸零會被發現
- [ ] 失敗有告警且有 runbook

---

## 常見誤區

| # | 誤區 | 真相 |
| --- | --- | --- |
| 1 | 應用裡寫個 Timer 就好 | 多副本下會執行 N 次 |
| 2 | 「只跑一個副本」可以避免重複 | 放棄高可用，且滾動更新期間仍會重疊 |
| 3 | CronJob 的時間是本地時間 | 不設 `timeZone` 就是 UTC |
| 4 | `concurrencyPolicy` 預設是安全的 | 預設 `Allow` 會重疊執行 |
| 5 | 設了 `Forbid` 就高枕無憂 | 一次卡住會讓後續全部跳過且無告警 |
| 6 | CronJob 錯過就會補跑 | 錯過超過 100 次會**永久停止排程** |
| 7 | Job 的 Pod 不會被驅逐 | 跟其他 Pod 一樣會 |
| 8 | 批次工作跑完就結束，不用監控 | **「沒跑」是安靜的**，要主動偵測 |
| 9 | Prometheus 抓得到 Job 的指標 | pull 模型抓不到短命 Pod，要用 Pushgateway |
| 10 | 成功就代表健康 | 執行時間逐漸變長是超時的前兆 |

## 連結

- [[71-schema-migration]] — 附錄 AW：大表回填該拆成分批的背景工作，不要留在部署路徑上
- [[19-yaml-fields-workloads]] — 附錄 C-2：Job/CronJob 全欄位、`podFailurePolicy`
- [[41-advanced-scheduling]] — 附錄 S：批次的優先級、spot 節點與 checkpoint
- [[49-messaging-and-events]] — 附錄 AA：事件驅動的背景處理與冪等
- [[43-migration-to-k8s]] — 附錄 U：舊系統的排程藏在 OS 設定裡
- [[practice-3-gitops-pipeline]] — 實戰 3：用 PreSync hook 跑一次性任務
- [[practice-6-observability]] — 實戰 6：告警設計原則
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：`Lease` 物件與選主機制
- [[k8s-mastery]] — 教材總目錄
