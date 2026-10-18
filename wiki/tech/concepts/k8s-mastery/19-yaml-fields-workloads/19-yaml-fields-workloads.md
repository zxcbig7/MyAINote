---
type: reference
domain: tech
tags: [kubernetes, k8s, yaml, reference, deployment, statefulset, job, hpa, quota]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 C-2：Workload 與擴縮全欄位

上一份把 Pod 這個「最小單位」的欄位攤平了。這一份往外包一層：那些**管理 Pod 的物件**自己有哪些欄位。

這層的欄位有個共同特徵——它們幾乎都在描述「變更的時候該怎麼做」。要一次換掉幾個？舊的什麼時候砍？失敗了要不要停下來？副本要不要照順序來？寫錯這些欄位的代價，通常不是 Pod 起不來（那很容易發現），而是滾動更新的那三十秒掉了請求、或者半夜自動擴縮抖成鋸齒狀。基準版本一樣是 **v1.33**。

所有 workload 都共用同一組核心三件套，先說清楚：

| 欄位 | 說明 |
| --- | --- |
| `replicas` | 期望副本數（DaemonSet 沒有，由 Node 數決定） |
| `selector` | 用哪組 label 認領 Pod。**apps/v1 起建立後不可修改**，要改只能刪掉重建 |
| `template` | 就是一份完整的 PodTemplateSpec，內容＝附錄 C-1 的 metadata + PodSpec |

`selector.matchLabels` 必須是 `template.metadata.labels` 的子集，否則 API Server 直接拒絕——這是新手最常撞的第一道牆。

---

## Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  minReadySeconds: 10
  revisionHistoryLimit: 5
  progressDeadlineSeconds: 600
  paused: false
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:1.4.0
```

| 欄位 | 型別 | 預設 | 說明 |
| --- | --- | --- | --- |
| `replicas` | int32 | `1` | 被 HPA 接管時**不要**寫在 git 裡，否則會跟 HPA 互相拉扯（ArgoCD 需配 `ignoreDifferences`） |
| `strategy.type` | string | `RollingUpdate` | 或 `Recreate`（先全殺再全開，一定有 downtime，但可避免新舊版同時寫同一份資料） |
| `strategy.rollingUpdate.maxSurge` | IntOrString | `25%` | 允許超出 `replicas` 的數量 |
| `strategy.rollingUpdate.maxUnavailable` | IntOrString | `25%` | 允許同時不可用的數量。**兩者不可同時為 0** |
| `minReadySeconds` | int32 | `0` | Pod Ready 之後還要「安穩活過」幾秒才算數，防止起來就死的版本一路滾完 |
| `revisionHistoryLimit` | int32 | `10` | 保留幾個舊 ReplicaSet 供回滾。設 `0` 就無法 `rollout undo` |
| `progressDeadlineSeconds` | int32 | `600` | 超時沒進展就標記 `ProgressDeadlineExceeded`（**只是標記，不會自動回滾**） |
| `paused` | bool | `false` | 暫停 reconcile，用於「改多個欄位後一次放行」 |

`maxSurge` / `maxUnavailable` 的組合直接決定更新期間的服務能力：

| 組合 | 行為 | 適用 |
| --- | --- | --- |
| `maxSurge: 1, maxUnavailable: 0` | 先開新的、Ready 後才殺舊的 | 要求零降載的線上服務（最常用） |
| `maxSurge: 0, maxUnavailable: 1` | 先殺舊的再開新的 | 資源吃緊、或有 licence／單例限制 |
| `maxSurge: 25%, maxUnavailable: 25%` | 預設值，更新快但容量會短暫下降 | 內部服務 |

> 常見誤解：`progressDeadlineSeconds` 到期會自動回滾。不會。它只在 `status.conditions` 標一筆 `Progressing=False`，Pod 會繼續卡在那裡直到有人處理。真正的自動回滾要靠 CI 或 Argo Rollouts 這類工具。

---

## ReplicaSet

實務上不直接寫，由 Deployment 生成。欄位只有 `replicas`、`selector`、`template`、`minReadySeconds`。知道它存在的價值在排錯：`kubectl get rs` 看到兩個 RS 都還有 Pod，就是滾動更新卡在中間；看到舊 RS 的 `DESIRED` 沒歸零，就往 PDB 或 probe 失敗的方向查。

---

## StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
spec:
  serviceName: my-db-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
      maxUnavailable: 1
  persistentVolumeClaimRetentionPolicy:
    whenDeleted: Retain
    whenScaled: Retain
  ordinals:
    start: 0
  selector:
    matchLabels:
      app: my-db
  template: {}
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 10Gi
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `serviceName` | 必填 | 對應的 **headless Service**（`clusterIP: None`），Pod 的穩定 DNS 由它而來 |
| `podManagementPolicy` | `OrderedReady` | 或 `Parallel`（同時建立／刪除，不等前一個 Ready）。**建立後不可改** |
| `updateStrategy.type` | `RollingUpdate` | 或 `OnDelete`（改了 spec 也不動，要人手動刪 Pod 才換版） |
| `updateStrategy.rollingUpdate.partition` | `0` | 只更新序號 **≥ partition** 的 Pod，做金絲雀發布的原生手段 |
| `updateStrategy.rollingUpdate.maxUnavailable` | `1` | 允許同時更新幾個（beta，需確認叢集有開） |
| `volumeClaimTemplates` | — | 每個副本各自生成一份 PVC，名稱為 `<template>-<sts>-<序號>` |
| `persistentVolumeClaimRetentionPolicy.whenDeleted` | `Retain` | 刪 StatefulSet 時 PVC 留或刪（`Retain`｜`Delete`） |
| `persistentVolumeClaimRetentionPolicy.whenScaled` | `Retain` | 縮容時多出來的 PVC 留或刪 |
| `ordinals.start` | `0` | 起始序號，跨叢集搬遷時避免序號撞號用（1.31+） |
| `minReadySeconds` / `revisionHistoryLimit` | `0` / `10` | 同 Deployment |

三個保證（穩定網路身份、穩定儲存、有序部署）的完整推演見第 4 章。這裡只補兩個欄位層面的坑：

- **`volumeClaimTemplates` 建立後幾乎不可改。** 想擴容儲存要直接改各個 PVC 的 `resources.requests.storage`（且 StorageClass 要 `allowVolumeExpansion: true`），改 template 本身會被拒絕。
- **縮容不會自動刪 PVC**（除非設了 `whenScaled: Delete`）。這是刻意的保護，但也是「叢集裡一堆孤兒 PVC 在燒錢」的主因。

---

## DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 0
  selector:
    matchLabels:
      app: node-agent
  template:
    spec:
      tolerations:
        - operator: Exists # 連 control plane 與有汙點的 Node 都要跑
      containers:
        - name: agent
          image: node-agent:2.1
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `updateStrategy.type` | `RollingUpdate` | 或 `OnDelete` |
| `rollingUpdate.maxUnavailable` | `1` | 同時更新幾台 Node 上的副本 |
| `rollingUpdate.maxSurge` | `0` | 允許先開新的再殺舊的，設 `1` 時 `maxUnavailable` 必須是 `0` |
| `minReadySeconds` / `revisionHistoryLimit` | `0` / `10` | 同上 |

沒有 `replicas`——副本數＝符合 `nodeSelector` / `affinity` / `tolerations` 的 Node 數。要限定只在部分 Node 跑，就在 `template.spec.nodeSelector` 下條件。

---

## Job

```yaml
apiVersion: batch/v1
kind: Job
spec:
  completions: 5
  parallelism: 2
  completionMode: Indexed
  backoffLimit: 4
  activeDeadlineSeconds: 3600
  ttlSecondsAfterFinished: 600
  suspend: false
  template:
    spec:
      restartPolicy: OnFailure # 只能是 OnFailure 或 Never
      containers:
        - name: worker
          image: batch-worker:1.0
```

| 欄位 | 型別 | 預設 | 說明 |
| --- | --- | --- | --- |
| `completions` | int32 | `1` | 要成功幾次才算整個 Job 完成 |
| `parallelism` | int32 | `1` | 同時最多跑幾個 Pod |
| `completionMode` | string | `NonIndexed` | `Indexed` 會給每個 Pod 一個 `JOB_COMPLETION_INDEX` 環境變數，適合切分資料 |
| `backoffLimit` | int32 | `6` | 整個 Job 容許的失敗次數；重試間隔指數退避，上限 6 分鐘 |
| `backoffLimitPerIndex` | int32 | — | 改成「每個 index 各自算」（1.29 beta） |
| `maxFailedIndexes` | int32 | — | 搭配上者：壞掉的 index 超過幾個就整個放棄 |
| `activeDeadlineSeconds` | int64 | — | 牆鐘時間上限，**優先於 `backoffLimit`**，到點直接終止 |
| `ttlSecondsAfterFinished` | int32 | — | 結束後幾秒自動刪除 Job 與其 Pod。不設就會一直堆積 |
| `suspend` | bool | `false` | `true` 時不建立 Pod（已建的會被刪），排隊系統用 |
| `podFailurePolicy` | object | — | 依 exit code 或 Pod condition 決定「這次失敗算不算數」（GA 1.31） |
| `successPolicy` | object | — | 提前判定成功，例如「index 0-2 成功就算贏」（1.31 beta） |
| `podReplacementPolicy` | string | `TerminatingOrFailed` | 設 `Failed` 可等舊 Pod 完全消失才補新的（1.29 beta） |
| `managedBy` | string | — | 交給外部 controller（如 Kueue）接管（1.32 beta） |

`podFailurePolicy` 解決的是「明知是資料格式錯，重試 6 次也沒用」這種浪費：

```yaml
podFailurePolicy:
  rules:
    - action: FailJob # 直接讓整個 Job 失敗，不再重試
      onExitCodes:
        containerName: worker
        operator: In
        values: [42]
    - action: Ignore # 不計入 backoffLimit
      onPodConditions:
        - type: DisruptionTarget # 被搶佔／驅逐造成的失敗不該算工人的錯
```

`action` 可用值：`FailJob`、`Ignore`、`Count`（照常計數，預設行為）、`FailIndex`（只讓該 index 失敗）。

---

## CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
spec:
  schedule: "0 3 * * *"
  timeZone: "Asia/Taipei"
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 300
  suspend: false
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec: {} # 就是上面那份 Job spec
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `schedule` | 必填 | 標準 5 欄 cron。支援 `@daily`、`@hourly` 等縮寫 |
| `timeZone` | 控制平面時區（多為 UTC） | IANA 名稱，1.27 起正式支援。**沒設就是 UTC**，這是「排程差 8 小時」的頭號原因 |
| `concurrencyPolicy` | `Allow` | `Allow`（可重疊）｜`Forbid`（前一次沒跑完就跳過）｜`Replace`（殺掉舊的換新的） |
| `startingDeadlineSeconds` | — | 錯過排程後還允許補跑的時窗。設太小會整段被跳過；不設而錯過 100 次以上，controller 會停止排程並報錯 |
| `suspend` | `false` | 暫停，不影響已建立的 Job |
| `successfulJobsHistoryLimit` | `3` | 保留成功紀錄數 |
| `failedJobsHistoryLimit` | `1` | 保留失敗紀錄數，排錯時建議調大 |

---

## HorizontalPodAutoscaler（autoscaling/v2）

HPA 是這一份裡欄位最容易寫得不完整的物件——多數人只寫 `metrics`，然後在事故後才發現問題出在沒寫的 `behavior`。

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization # Utilization | AverageValue | Value
          averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      selectPolicy: Max
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      selectPolicy: Min
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

五種 metric 型別：

| `type` | 資料來源 | 用途 |
| --- | --- | --- |
| `Resource` | metrics-server | CPU / 記憶體，最常用。`Utilization` 是相對 **requests** 的百分比——沒設 requests 就完全不會運作 |
| `ContainerResource` | metrics-server | 只看 Pod 內某個容器，避免 sidecar 的用量稀釋判斷 |
| `Pods` | custom metrics API | 每個 Pod 的自訂指標平均值，如「每秒請求數」 |
| `Object` | custom metrics API | 某個物件的單一指標，如 Ingress 的總 QPS |
| `External` | external metrics API | 叢集外指標，如 SQS 佇列長度 |

`behavior` 的預設值（沒寫時實際生效的）：

| 方向 | 穩定視窗 | 政策 |
| --- | --- | --- |
| `scaleUp` | 0 秒 | 每 15 秒最多加倍或加 4 個，取較大者 |
| `scaleDown` | 300 秒 | 每 15 秒最多移除當前的 100% |

擴容快、縮容慢是刻意設計：擴錯只是多花錢，縮錯會直接掉服務。若服務啟動慢（例如要暖 JVM 或載模型），把 `scaleDown.stabilizationWindowSeconds` 拉到 600–900 秒，可以顯著減少「剛縮完流量又來、再重新擴」的鋸齒。要完全禁止自動縮容則設 `selectPolicy: Disabled`。

---

## PodDisruptionBudget

PDB 管的是**自願性中斷**（`kubectl drain`、Node 升級、autoscaler 縮節點），對 Node 直接斷電這種非自願中斷無效。

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
spec:
  minAvailable: 2 # 與 maxUnavailable 二擇一，不可並存
  selector:
    matchLabels:
      app: my-app
  unhealthyPodEvictionPolicy: AlwaysAllow
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `minAvailable` | — | 最少要留幾個可用（可寫百分比） |
| `maxUnavailable` | — | 最多允許幾個不可用 |
| `selector` | 必填 | 空的 `{}` 代表選中該 namespace **全部** Pod |
| `unhealthyPodEvictionPolicy` | `IfHealthyBudget` | 設 `AlwaysAllow` 讓已經壞掉的 Pod 隨時可被驅逐（1.27+） |

> 最常見的事故：`replicas: 1` 配 `minAvailable: 1`。這會讓 `kubectl drain` **永遠卡住**——驅逐這唯一的 Pod 就違反預算，於是 Node 維護做不下去。單副本服務要嘛不要設 PDB，要嘛用 `maxUnavailable: 1`。
> 第二常見的是 `unhealthyPodEvictionPolicy` 沒設：Pod 已經 CrashLoopBackOff 了，PDB 仍算它「應該可用」，drain 一樣卡死。

---

## PriorityClass

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "線上服務，可搶佔批次工作"
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `value` | 必填 | 數字越大越優先。使用者自訂建議 < 10 億 |
| `globalDefault` | `false` | 全叢集只能有一個設為 true |
| `preemptionPolicy` | `PreemptLowerPriority` | 設 `Never` 則自己排隊優先，但不趕別人走 |

系統保留的兩個：`system-cluster-critical`（2000000000）與 `system-node-critical`（2000001000），一般應用不要借用。

---

## ResourceQuota

namespace 層級的總量閘門。一旦設了某個 quota，該 namespace 內**所有** Pod 都必須明確宣告對應欄位，否則直接被拒絕建立。

```yaml
apiVersion: v1
kind: ResourceQuota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    persistentvolumeclaims: "10"
    requests.storage: 500Gi
    standard.storageclass.storage.k8s.io/requests.storage: 200Gi
    services.loadbalancers: "2"
    services.nodeports: "5"
    count/deployments.apps: "20"
    count/secrets: "50"
  scopes:
    - NotBestEffort
```

| `scopes` 值 | 只算哪些 Pod |
| --- | --- |
| `Terminating` / `NotTerminating` | 有／沒有設 `activeDeadlineSeconds` |
| `BestEffort` / `NotBestEffort` | 完全沒設資源／有設資源 |
| `PriorityClass` | 搭配 `scopeSelector` 針對特定優先級 |
| `CrossNamespacePodAffinity` | 限制跨 namespace 的 affinity 使用 |

```yaml
scopeSelector:
  matchExpressions:
    - scopeName: PriorityClass
      operator: In
      values: [high-priority]
```

---

## LimitRange

Quota 管總量，LimitRange 管**單體**，並且能補上預設值——這是配合 quota 使用的關鍵，否則開發者每份 YAML 都得手寫 requests/limits。

```yaml
apiVersion: v1
kind: LimitRange
spec:
  limits:
    - type: Container
      default: # 沒寫 limits 時自動補
        cpu: 500m
        memory: 512Mi
      defaultRequest: # 沒寫 requests 時自動補
        cpu: 100m
        memory: 128Mi
      min:
        cpu: 50m
        memory: 64Mi
      max:
        cpu: "4"
        memory: 8Gi
      maxLimitRequestRatio: # limits 不得超過 requests 的幾倍，防止超賣
        cpu: "10"
    - type: PersistentVolumeClaim
      min:
        storage: 1Gi
      max:
        storage: 100Gi
```

`type` 可為 `Container`、`Pod`（整個 Pod 加總）、`PersistentVolumeClaim`。注意 `default` / `defaultRequest` 只對 `Container` 有意義。

---

## 一頁選型與常見誤設

| 需求 | 用什麼 | 關鍵欄位 |
| --- | --- | --- |
| 無狀態服務 | Deployment | `strategy.rollingUpdate` |
| 需要固定身份與各自儲存 | StatefulSet | `serviceName` + `volumeClaimTemplates` |
| 每台 Node 一份 | DaemonSet | `tolerations: [{operator: Exists}]` |
| 跑完就結束 | Job | `backoffLimit` + `ttlSecondsAfterFinished` |
| 定時觸發 | CronJob | `timeZone` + `concurrencyPolicy` |
| 依負載自動增減 | HPA | `metrics` + `behavior` |
| 維護時保住服務 | PDB | `maxUnavailable` |

| # | 誤設 | 症狀 | 正解 |
| --- | --- | --- | --- |
| 1 | `selector` 與 `template.labels` 不一致 | apply 直接被拒 | selector 必須是 labels 的子集 |
| 2 | git 裡寫死 `replicas` 又開 HPA | 兩者互相覆寫，副本數抖動 | 移除 `replicas` 或設 ArgoCD `ignoreDifferences` |
| 3 | CronJob 沒設 `timeZone` | 半夜三點的任務跑在上午十一點 | 明確寫 `Asia/Taipei` |
| 4 | Job 沒設 `ttlSecondsAfterFinished` | 幾千個 Completed Pod 堆滿 etcd | 設幾百到幾千秒 |
| 5 | `replicas: 1` + `minAvailable: 1` | `kubectl drain` 永遠卡住 | 改 `maxUnavailable: 1` 或不設 PDB |
| 6 | HPA 用 `Utilization` 但沒設 requests | HPA 完全不動，狀態顯示 `unknown` | 一定要有 `resources.requests` |
| 7 | 只設 ResourceQuota 沒設 LimitRange | 開發者忘了寫 requests，Pod 全被拒 | 用 LimitRange 補預設值 |
| 8 | `maxSurge: 0` 且 `maxUnavailable: 0` | 更新永遠不會開始 | 至少一個要大於 0 |
| 9 | 以為 `progressDeadlineSeconds` 會回滾 | 卡住卻沒人發現 | 靠 CI 檢查 rollout status |
| 10 | StatefulSet 縮容後忘了 PVC | 孤兒 PVC 持續計費 | 設 `whenScaled: Delete` 或定期盤點 |

---

## 連結

- [[67-scaling-limits]] — 附錄 AS：`ttlSecondsAfterFinished` 不設會累積成叢集變慢的主因之一
- [[18-yaml-fields-pod]] — 附錄 C-1：Pod 與 Container 全欄位
- [[20-yaml-fields-network-storage]] — 附錄 C-3：網路與儲存全欄位
- [[21-yaml-fields-cluster-security]] — 附錄 C-4：叢集與安全全欄位
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：生態系 CRD 全欄位（含 VPA、ArgoCD）
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：冷門內建資源與元件設定檔
- [[04-workloads]] — 各 workload 的設計意圖與滾動更新推演
- [[07-scheduling-and-resources]] — QoS、驅逐與三種 Autoscaler
- [[12-cluster-operations]] — drain 與升級時 PDB 的實際影響
- [[17-cheatsheet]] — 附錄 B：可直接複製的骨架
- [[k8s-mastery]] — 教材總目錄
