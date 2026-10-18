---
type: reference
domain: tech
tags: [kubernetes, k8s, status, conditions, troubleshooting, reference, exit-codes, jsonpath]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 G：狀態與 Condition 判讀手冊

附錄 C 那六份講的是 `spec`——你寫進去的東西。這一份講 `status`——K8s 回給你的東西。

多數人排錯時只看兩個地方：`kubectl get pods` 那一欄狀態，跟 `kubectl logs`。但這兩者之間其實還有一整層資訊沒被讀：每個物件的 `status` 裡都有 `conditions` 陣列，裡面明確寫著「哪個條件不滿足、為什麼、從什麼時候開始」。學會讀它，很多問題可以在下第二個指令之前就定位完成。

這一份是那層資訊的解碼器。用法是反查：看到某個狀態字串或 condition，來這裡找它的意義與下一步。

---

## Condition 的通用結構

幾乎所有 K8s 物件的 `status.conditions[]` 都長這樣：

```yaml
status:
  observedGeneration: 4
  conditions:
    - type: Available # 條件名稱
      status: "False" # "True" | "False" | "Unknown"
      reason: MinimumReplicasUnavailable # 機器可讀的短原因
      message: "Deployment does not have minimum availability." # 給人看的說明
      lastTransitionTime: "2026-08-14T02:11:03Z" # 上次變化的時間
```

四個讀法要點：

**`reason` 比 `message` 有用。** `message` 是自由文字、會隨版本改；`reason` 是列舉值，適合寫進告警規則與自動化判斷。

**`lastTransitionTime` 告訴你這個狀態持續多久了。** 「三分鐘前變 False」與「三天前就 False」是完全不同的事件。

**`status: "Unknown"` 不等於 False。** 它代表「無法判定」，通常是回報者本身失聯——例如 Node 的 `Ready=Unknown` 意思是 kubelet 沒在續租，而不是 Node 確定壞了。這個差別決定了你該去查網路還是查該節點。

**`observedGeneration` 要跟 `metadata.generation` 比對。** 兩者不等，代表 controller 還沒處理到你最新的改動——此時看 conditions 是在看**舊狀態**，很容易誤判。

---

## Pod：phase、conditions 與容器狀態三層

Pod 的狀態最複雜，因為它有三層，而 `kubectl get pods` 顯示的那一欄其實是這三層的**綜合結果**，不是任何一個欄位的原值。

### 第一層：`status.phase`

| phase | 意義 |
| --- | --- |
| `Pending` | 已被接受，但至少一個容器還沒跑起來（含排程中、拉映像中） |
| `Running` | 已綁定 Node，所有容器已建立，**至少一個**在執行 |
| `Succeeded` | 所有容器正常結束且不會重啟 |
| `Failed` | 所有容器已結束，至少一個是失敗的 |
| `Unknown` | 無法取得狀態，通常是 Node 失聯 |

注意 `Running` **不代表健康**——它只說容器在跑。一個 CrashLoopBackOff 的 Pod 在重啟間隔中的 phase 仍然是 `Running`。

### 第二層：`status.conditions`

| type | True 代表 |
| --- | --- |
| `PodScheduled` | 已排到某個 Node |
| `PodReadyToStartContainers` | 沙箱與網路已就緒（1.31+） |
| `Initialized` | 所有 init container 成功結束 |
| `ContainersReady` | 所有容器 Ready |
| `Ready` | Pod 可接受流量（＝ContainersReady + 所有 readinessGates） |
| `DisruptionTarget` | 這個 Pod 即將被驅逐（搶佔、drain、Node 壓力） |

`Ready` 與 `ContainersReady` 的差別只在 `readinessGates`。若你看到 `ContainersReady=True` 但 `Ready=False`，就是某個外部 controller 沒把 readiness gate 標成 True。

`DisruptionTarget` 是排查「Pod 為什麼突然不見了」的關鍵——它的 `reason` 會直接寫出 `PreemptionByScheduler`、`EvictionByEvictionAPI`、`TerminationByKubelet` 或 `DeletionByTaintManager`。

### 第三層：`status.containerStatuses[].state`

容器的狀態是三選一的：

```yaml
containerStatuses:
  - name: app
    ready: false
    restartCount: 7
    started: false
    state:
      waiting:
        reason: CrashLoopBackOff
        message: "back-off 5m0s restarting failed container"
    lastState:
      terminated:
        exitCode: 137
        reason: OOMKilled
        startedAt: "2026-08-14T02:10:00Z"
        finishedAt: "2026-08-14T02:10:43Z"
```

**`lastState` 比 `state` 更常是答案所在**——當前狀態只說「正在退避重啟」，上一個狀態才說「上次是被 OOMKill 的」。

### `waiting.reason` 全表

| reason | 意義 | 下一步 |
| --- | --- | --- |
| `ContainerCreating` | 正在建立（拉映像、掛 volume、設定網路） | 卡住超過一分鐘就 `describe` 看 event，多半是 volume 或 CNI |
| `PodInitializing` | init container 還在跑 | `kubectl logs <pod> -c <init-container>` |
| `CrashLoopBackOff` | 反覆啟動失敗，正在指數退避 | `logs --previous` + 看 `lastState.terminated` |
| `ErrImagePull` | 首次拉取失敗 | `describe` 看是 not found 還是 unauthorized |
| `ImagePullBackOff` | 拉取失敗後退避中 | 同上 |
| `InvalidImageName` | 映像名稱格式不合法 | 檢查有沒有多餘空白或大寫 |
| `ErrImageNeverPull` | `imagePullPolicy: Never` 但本機沒有該映像 | 先載入映像或改 policy |
| `CreateContainerConfigError` | **ConfigMap／Secret 引用不存在** | 檢查 `env.valueFrom` 與 volume 引用的名稱 |
| `CreateContainerError` | runtime 建立容器失敗 | 常見於 command 路徑不存在、掛載點衝突 |
| `RunContainerError` | 啟動時失敗 | 看 message，多半是權限或 securityContext |
| `RegistryUnavailable` | 連不上 registry | 網路／NetworkPolicy／DNS |

`CreateContainerConfigError` 值得特別記：它看起來像映像問題，實際上跟映像無關——是你引用的 ConfigMap 或 Secret 不存在。這個誤判每年都會浪費不少人的時間。

### `terminated.reason` 與 exit code

| reason | exit code | 意義 |
| --- | --- | --- |
| `Completed` | 0 | 正常結束 |
| `Error` | 非 0 | 程式自己回報失敗 |
| `OOMKilled` | 137 | 超過 memory limit 被 cgroup 殺掉 |
| `ContainerCannotRun` | 126 | 執行檔存在但不可執行 |
| `DeadlineExceeded` | — | 超過 `activeDeadlineSeconds` |
| `ContainerStatusUnknown` | — | kubelet 無法確認結果 |

exit code 的解讀規則：

| code | 意義 |
| --- | --- |
| `0` | 成功 |
| `1` | 一般錯誤（應用自己定義） |
| `2` | shell 用法錯誤 |
| `126` | 找到檔案但不可執行（權限或架構不符） |
| `127` | **命令不存在**（打錯路徑、映像沒有那支程式、alpine 沒有 bash） |
| `128 + n` | 被訊號 n 終止 |
| `137` | `128 + 9` = SIGKILL → **OOM 或強制終止** |
| `139` | `128 + 11` = SIGSEGV → 程式當掉 |
| `143` | `128 + 15` = SIGTERM → 正常收到終止訊號 |

`137` 與 `143` 的差別是判斷「優雅關閉有沒有做對」的直接證據：正常滾動更新應該看到 `143`（收到 SIGTERM 後自己退出）；看到 `137` 代表應用沒在寬限期內結束，被強制砍掉。

### `kubectl get pods` STATUS 欄的複合值

| 顯示 | 實際意義 |
| --- | --- |
| `Init:0/2` | 正在跑第 1 個 init container，共 2 個 |
| `Init:Error` / `Init:CrashLoopBackOff` | init container 失敗 |
| `PodInitializing` | init 全數完成，主容器準備中 |
| `Terminating` | 有 `deletionTimestamp`，正在刪除（卡住就查 finalizer） |
| `Completed` | phase = Succeeded |
| `NotReady` | 容器在跑但 readiness 沒過 |
| `Evicted` | 被 kubelet 驅逐（`status.reason` 會寫是記憶體還是磁碟壓力） |
| `OutOfcpu` / `OutOfmemory` | 排程後發現 Node 資源不足 |
| `ContainerStatusUnknown` | 通常伴隨 Node 失聯 |

---

## Node

| condition | True 代表 | 處理方向 |
| --- | --- | --- |
| `Ready` | kubelet 健康且準備接受 Pod | `False` 查 kubelet；`Unknown` 查網路與 Lease |
| `MemoryPressure` | 記憶體不足，已開始驅逐 | 調 `evictionHard` 或加節點 |
| `DiskPressure` | 磁碟或 inode 不足 | 常是日誌或映像堆積，查 `containerLogMaxSize` 與映像 GC |
| `PIDPressure` | process 數過多 | 查有沒有 fork 炸彈型應用 |
| `NetworkUnavailable` | 網路未正確設定 | CNI 問題 |

`Ready=Unknown` 的完整故事：kubelet 每 10 秒續一次 `kube-node-lease` 的 Lease（附錄 C-6），超過 `node-monitor-grace-period`（預設 40 秒）沒續約，node controller 就把 `Ready` 標成 `Unknown`，再過一段時間自動為該 Node 上的 Pod 加上 `NoExecute` taint 觸發驅逐。

所以「Node 顯示 NotReady 但機器其實活著」幾乎都是 kubelet 到 apiserver 的連線問題，不是機器問題——查的方向應該是網路、憑證過期或 apiserver 過載，而不是重開機。

---

## Deployment 與 ReplicaSet

```yaml
status:
  observedGeneration: 5
  replicas: 3
  updatedReplicas: 1
  readyReplicas: 2
  availableReplicas: 2
  unavailableReplicas: 1
  conditions:
    - type: Progressing
      status: "False"
      reason: ProgressDeadlineExceeded
```

| condition | reason | 意義 |
| --- | --- | --- |
| `Progressing` | `NewReplicaSetCreated` / `FoundNewReplicaSet` | 正在建立新 RS |
| | `NewReplicaSetAvailable` | **更新完成**（這是成功的終態） |
| | `ReplicaSetUpdated` | 滾動中 |
| | `ProgressDeadlineExceeded` | 超時沒進展，**不會自動回滾** |
| `Available` | `MinimumReplicasAvailable` | 可用副本達標 |
| | `MinimumReplicasUnavailable` | 可用副本不足 |
| `ReplicaFailure` | `FailedCreate` | **RS 無法建立 Pod**——quota 不足、PSA 擋下、node selector 無解 |

`ReplicaFailure` 是最該學會看的一個。當 PSA 或 ResourceQuota 擋下 Pod 時，`kubectl get pods` 什麼都看不到（Pod 根本沒被建出來），真正的錯誤訊息只出現在 ReplicaSet 的這個 condition 裡：

```
kubectl describe rs -l app=my-app | grep -A5 Conditions
```

五個 replicas 計數欄位的分工也值得記清楚：`replicas` 是總數、`updatedReplicas` 是已經是新版的、`readyReplicas` 是 readiness 通過的、`availableReplicas` 是 Ready 且撐過 `minReadySeconds` 的。滾動更新的進度看 `updatedReplicas`，服務容量看 `availableReplicas`。

---

## Job、PVC、HPA 與其他

### Job

| condition | 意義 |
| --- | --- |
| `Complete` | 達到 `completions` |
| `Failed` | 超過 `backoffLimit` 或 `activeDeadlineSeconds` |
| `Suspended` | `spec.suspend: true` |
| `SuccessCriteriaMet` | 符合 `successPolicy` 提前判定成功 |
| `FailureTarget` | 即將被判定失敗（`podFailurePolicy` 觸發） |

status 欄位：`active`、`succeeded`、`failed`、`ready`、`terminating`、`completedIndexes`、`failedIndexes`。Indexed Job 排查用 `completedIndexes` 最快——它直接告訴你哪幾段資料處理完了。

### PV / PVC

| PVC phase | 意義 |
| --- | --- |
| `Pending` | 還沒綁定。**可能正常**（`WaitForFirstConsumer`），看 event 分辨 |
| `Bound` | 已綁定 |
| `Lost` | 對應的 PV 不見了 |

| PV phase | 意義 |
| --- | --- |
| `Available` | 可被綁定 |
| `Bound` | 已被綁定 |
| `Released` | PVC 已刪，但資料還在（`Retain` 政策），**不會自動被重用** |
| `Failed` | 自動回收失敗 |

`Released` 狀態的 PV 需要人工處理：清掉 `spec.claimRef` 才會回到 `Available`。叢集裡累積一堆 `Released` 的 PV 是常見的成本漏洞。

PVC 另有兩個擴容期間的 condition：`Resizing`（正在擴）與 `FileSystemResizePending`（等 Pod 重啟才能擴檔案系統）。

### HPA

| condition | reason | 意義 |
| --- | --- | --- |
| `AbleToScale` | `SucceededGetScale` | 能取得目標的 scale 子資源 |
| | `FailedGetScale` | 目標物件不存在或無 scale 子資源 |
| `ScalingActive` | `ValidMetricFound` | 正常運作 |
| | `FailedGetResourceMetric` | **拿不到指標**（metrics-server 掛了，或 Pod 沒設 requests） |
| `ScalingLimited` | `TooFewReplicas` / `TooManyReplicas` | 已頂到 min/max |
| | `DesiredWithinRange` | 未受限 |

「HPA 顯示 `<unknown>` 不動作」的答案幾乎總是 `ScalingActive=False` 配 `FailedGetResourceMetric`，而根因九成是目標 Pod 沒設 `resources.requests`。

### CRD 與 APIService

| 物件 | condition | 意義 |
| --- | --- | --- |
| CRD | `Established` | API 已註冊可用 |
| | `NamesAccepted` | 名稱沒有衝突 |
| | `NonStructuralSchema` | schema 不符結構化要求，部分功能失效 |
| | `Terminating` | 正在刪除（連同所有 CR） |
| APIService | `Available` | `False` + `FailedDiscoveryCheck` ＝聚合 API 連不上（`kubectl top` 失效的原因） |

### Namespace（卡 Terminating 時）

| condition | 意義 |
| --- | --- |
| `NamespaceDeletionDiscoveryFailure` | 有 API group 無法列舉（通常是壞掉的 APIService） |
| `NamespaceContentRemaining` | 還有資源沒刪完，**message 會列出是哪些** |
| `NamespaceFinalizersRemaining` | 還有 finalizer 沒被移除，**message 會列出是哪個** |

這三個 condition 讓 namespace 卡 Terminating 的診斷變成一件三十秒的事：

```
kubectl get namespace <ns> -o jsonpath='{range .status.conditions[*]}{.type}{"\t"}{.message}{"\n"}{end}'
```

不必再用那些「強制清 finalizer」的危險偏方（附錄 D 的 E3 解釋過為什麼危險）。

---

## 生態系物件的狀態

### ArgoCD Application

兩個**互相獨立**的維度，這是第 11 章強調過的重點：

| Sync Status | 意義 |
| --- | --- |
| `Synced` | 叢集狀態與 git 一致 |
| `OutOfSync` | 有差異（不代表壞，可能只是 mutating webhook 改過） |
| `Unknown` | 無法比對，通常是 repo 連不上 |

| Health Status | 意義 |
| --- | --- |
| `Healthy` | 所有資源健康 |
| `Progressing` | 部署中 |
| `Degraded` | **有資源不健康**（這才是真的出事） |
| `Suspended` | 被暫停（如 suspended CronJob） |
| `Missing` | git 有但叢集沒有 |

`Synced` + `Degraded` 是最常見的組合之一：YAML 已經照 git 部署了，但 Pod 起不來。這時要查的是 Pod 而不是 ArgoCD。反過來 `OutOfSync` + `Healthy` 通常無害——多半是 webhook 或 defaulting 造成的差異，用 `ignoreDifferences` 處理。

另外看 `status.operationState.phase`（`Running` / `Succeeded` / `Failed` / `Error`）可以知道上一次 sync 動作本身的結果。

### cert-manager Certificate

| condition | 意義 |
| --- | --- |
| `Ready` | 憑證已簽發並存進 Secret |
| `Issuing` | 正在簽發／續簽中 |

沒 Ready 就往下一層追：`CertificateRequest` → `Order` → `Challenge`，每層 `describe` 看 event。

---

## 讀 status 的實用指令

```
# 一次看完某物件所有 condition
kubectl get deploy my-app -o jsonpath='{range .status.conditions[*]}{.type}{"="}{.status}{"\t"}{.reason}{"\t"}{.message}{"\n"}{end}'

# 容器上一次為什麼死
kubectl get pod my-pod -o jsonpath='{.status.containerStatuses[0].lastState.terminated}' | jq

# 找出所有非 Running/Completed 的 Pod
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded

# 找出所有 NotReady 的 Node 與原因
kubectl get nodes -o custom-columns='NODE:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,REASON:.status.conditions[?(@.type=="Ready")].reason'

# 找出重啟次數最多的 Pod
kubectl get pods -A --sort-by=.status.containerStatuses[0].restartCount | tail -10

# controller 有沒有看到我最新的改動
kubectl get deploy my-app -o jsonpath='gen={.metadata.generation} observed={.status.observedGeneration}{"\n"}'

# 所有 Released 狀態的 PV（成本盤點）
kubectl get pv --field-selector=status.phase==Released
```

---

## 一頁式：症狀 → 先看哪個欄位

| 症狀 | 第一個要看的 |
| --- | --- |
| Pod 一直 Pending | `status.conditions[PodScheduled].message`（scheduler 直接寫出原因） |
| Pod 反覆重啟 | `lastState.terminated.exitCode` 與 `reason` |
| Pod 起來但沒流量 | `conditions[Ready]`，再看 EndpointSlice |
| 部署卡住不動 | Deployment 的 `Progressing.reason` |
| `kubectl get pods` 空的但部署失敗 | ReplicaSet 的 `ReplicaFailure` |
| Node NotReady | `conditions[Ready].status` 是 False 還是 Unknown |
| PVC Pending | event 是 `waiting for first consumer` 還是真的錯誤 |
| HPA 不動作 | `ScalingActive.reason` |
| `kubectl top` 失效 | APIService 的 `Available` |
| namespace 刪不掉 | namespace 的三個 `NamespaceXxx` condition |
| ArgoCD 紅字 | 先分辨 Sync 還是 Health 出問題 |

---

## 連結

- [[70-node-lifecycle-and-ha]] — 附錄 AV：`NotReady` 各種成因與節點自動修復的風險
- [[13-troubleshooting]] — 分層定位方法論與 Pod 狀態機
- [[18-yaml-fields-pod]] — 附錄 C-1：與這些狀態對應的 spec 欄位
- [[26-lab-drills]] — 附錄 D：親手製造出這裡的每一種狀態
- [[17-cheatsheet]] — 附錄 B：Pod 狀態速查與緊急排錯十連發
- [[11-argocd]] — Sync 與 Health 為何獨立
- [[k8s-mastery]] — 教材總目錄
