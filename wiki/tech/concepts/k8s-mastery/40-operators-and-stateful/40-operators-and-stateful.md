---
type: reference
domain: tech
tags: [kubernetes, k8s, operator, crd, controller, statefulset, reconcile, kubebuilder]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 R：Operator 與有狀態工作負載

正文第 9 章講清楚了機制：CRD 怎麼教 K8s 認識新名詞、webhook 怎麼攔截請求、finalizer 怎麼卡住刪除、ownerReference 怎麼讓垃圾回收連帶清理。但它沒有回答兩個實務問題：**什麼時候該做一個 Operator**，以及**已經有 StatefulSet 了，日常要怎麼運維它**。

這一份補這兩塊。先講一個立場：**多數團隊需要的不是自己寫 Operator，而是知道什麼時候不該寫。** 寫一個能動的 controller 不難，寫一個在正式環境不會製造麻煩的 controller 很難——而它一旦部署，就變成你叢集裡另一個需要維護、升級、排錯的東西。

---

## Part 1：你真的需要 Operator 嗎

先走這個決策階梯，**由上而下，能停就停**：

| 需求 | 用什麼 |
| --- | --- |
| 只是部署一組固定的資源 | **Helm chart 或 Kustomize**，結束 |
| 部署 + 安裝前後要跑點東西（migration、初始化） | **Helm hooks** 或 ArgoCD 的 PreSync hook |
| 部署 + 需要依環境產生不同結構 | Helm 模板邏輯，或 Kustomize overlay |
| 需要**持續**調和某個狀態，而且該狀態會自己漂移 | 這時候才輪到 controller |
| 上述需求，而且已經有成熟的社群方案 | **用現成的 Operator** |
| 上述需求，且是公司特有的運維知識 | 自己寫 |

**判準只有一句話：有沒有「需要持續執行的運維知識」。**

「安裝一套 PostgreSQL」不需要 Operator——Helm 就能做。「當主節點掛掉時，選出一個副本升為主節點、更新連線端點、通知其他副本重新指向它」**才需要**——因為這件事沒有人下指令，它必須由一個持續運行的東西在事件發生時自動完成。

一個實用的反問：**如果沒有人在，這件事還需要發生嗎？** 答案是「不需要，等人來做就好」的話，你要的是文件與腳本，不是 Operator。

---

## Part 2：Operator 成熟度五級

社群有一套能力分級，用它來檢視「我要做的東西落在哪一級」很有幫助：

| 級別 | 能力 | 例子 |
| --- | --- | --- |
| **L1 基本安裝** | 部署出資源 | 建一組 StatefulSet + Service |
| **L2 無縫升級** | 處理版本升級與設定變更 | 升級資料庫版本、滾動換版 |
| **L3 完整生命週期** | 備份、還原、故障轉移 | 主從切換、定期備份 |
| **L4 深度洞察** | 曝露指標、告警、分析 | 產生 ServiceMonitor、健康度評估 |
| **L5 自動駕駛** | 自動調校、自動修復、自動擴縮 | 依負載自動調整參數 |

**這張表最有價值的用法是自我檢查**：如果你打算寫的 Operator 只做到 L1、甚至 L2，那它跟一份 Helm chart 的差別在哪？多數情況答案是「沒有明顯差別，但多了一個要維護的元件」。

**真正的價值從 L3 開始**——備份與故障轉移是必須「持續有人盯著」的事，而那正是 controller 的本質。

---

## Part 3：選用既有 Operator 的檢查清單

大部分情況你該用現成的（CloudNativePG、Strimzi、Prometheus Operator 這類）。但選之前要問：

- [ ] **維護狀態**：最近的 commit 與 release 是什麼時候？有幾個維護者？
- [ ] **CRD 穩定性**：API 版本是 `v1` 還是 `v1alpha1`？升級時 CRD 會不會有破壞性變更？
- [ ] **升級路徑**：能不能跳版升級？有沒有明確的升級文件？
- [ ] **逃生門**：**如果我要移除這個 Operator，我的資料與工作負載會怎樣？** 能不能退回手動管理？
- [ ] **Operator 自己掛了會怎樣**？已部署的服務會繼續跑，還是一起停？
- [ ] **權限範圍**：它要求 cluster-admin 嗎？能不能限縮到特定 namespace？
- [ ] **finalizer 行為**：刪除 CR 時它會不會連帶刪掉資料？（這一項要在測試環境驗證，不要在正式環境學）

**「逃生門」那一項最常被忽略，也最重要。** Operator 用 CRD 管理你的資料庫，意味著你的資料庫生命週期跟這個第三方專案綁在一起。專案停止維護時你要有退路——通常是「CR 刪除時設定為保留底層資源」，然後接手手動管理。

**權限那一項也值得堅持**：一個要求 cluster-admin 的 Operator，等於把整座叢集的信任交給那個專案。能限縮就限縮。

---

## Part 4：自己寫的話，六個設計原則

假設你確定要寫。這六條是「能動」與「正式環境能用」之間的差距。

### 1. Reconcile 必須冪等

`Reconcile` 會被呼叫很多次——同一個物件、同樣的狀態、可能一秒內好幾次。**每一次都必須產生相同的結果**。

```go
func (r *BackupReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    var backup opsv1.Backup
    if err := r.Get(ctx, req.NamespacedName, &backup); err != nil {
        // 找不到通常代表已被刪除，忽略即可
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    // 讀取「現在的實際狀態」，跟 spec 比對，做出差異
    // 絕對不要寫成「收到事件就建立一個新的 Job」
    return ctrl.Result{}, nil
}
```

**反例**：在 reconcile 裡無條件 `Create` 一個 Job。結果是每次觸發都多一個 Job，很快就有幾百個。正確做法是先查「符合條件的 Job 存在嗎」，不存在才建。

### 2. Level-triggered，不是 edge-triggered

**不要依賴「事件內容」，要讀「當前狀態」。**

K8s 的事件機制不保證每個變化都會產生剛好一個事件——事件可能合併、可能重送、controller 重啟後會收到全部物件的重新同步。所以正確的心智模型是：**「有東西可能變了，去看看現在長怎樣」**，而不是「發生了 X 事件，所以做 Y」。

這也是整個 K8s 的設計哲學（正文第 2 章的 reconciliation loop）。你的 controller 只是加入這個模式，不是發明新的。

### 3. status 與 spec 嚴格分離

`spec` 是使用者的願望，`status` 是你回報的現實。**controller 不應該寫 `spec`**——那是使用者的欄位，你改它會造成無限迴圈（你改 spec → 觸發事件 → 你又改 spec）。

CRD 要開啟 status 子資源（附錄 C-4）：

```yaml
subresources:
  status: {}
```

開了之後 `r.Status().Update()` 只會動 status，不會誤觸 spec。並且用 `observedGeneration` 讓使用者知道你處理到哪一版（附錄 G）：

```go
backup.Status.ObservedGeneration = backup.Generation
```

### 4. 錯誤處理與重試節奏

```go
// 暫時性錯誤：回傳 error，controller-runtime 會指數退避重試
return ctrl.Result{}, err

// 需要稍後再檢查（例如等某個外部作業完成）
return ctrl.Result{RequeueAfter: 30 * time.Second}, nil

// 完成，不需要主動重排
return ctrl.Result{}, nil
```

**兩個常見錯誤**：一是把永久性錯誤（例如使用者的 spec 根本不合法）當成暫時性錯誤一直重試——那會產生無止盡的日誌與 API 呼叫，正確做法是把錯誤寫進 `status.conditions` 並停止重試；二是用 `RequeueAfter: 1 * time.Second` 這種短間隔輪詢，那會對 API Server 造成不必要的壓力。

### 5. Finalizer 要有釋放路徑

Finalizer 讓你能在物件被刪除前做清理（正文第 9 章）。但它也是「namespace 卡在 Terminating」的頭號原因，所以要小心：

```go
if !backup.DeletionTimestamp.IsZero() {
    if controllerutil.ContainsFinalizer(&backup, myFinalizer) {
        if err := r.cleanupExternalResources(ctx, &backup); err != nil {
            // 清理失敗就先不移除 finalizer，但要記錄原因讓人看得到
            return ctrl.Result{}, err
        }
        controllerutil.RemoveFinalizer(&backup, myFinalizer)
        if err := r.Update(ctx, &backup); err != nil {
            return ctrl.Result{}, err
        }
    }
    return ctrl.Result{}, nil
}
```

**三條紀律**：清理邏輯必須冪等（可能被呼叫多次）、清理失敗要把原因寫進 status 或 event（否則使用者只看到「刪不掉」而不知道為什麼）、以及**要有一個明確的手動移除程序寫在文件裡**——你的 controller 也可能掛掉，那時候得有人能手動解開。

### 6. 用 ownerReference 讓 GC 幫你收拾

你建立的子資源（Job、ConfigMap、Service）都應該設 ownerReference 指向 CR：

```go
if err := controllerutil.SetControllerReference(&backup, job, r.Scheme); err != nil {
    return ctrl.Result{}, err
}
```

這樣 CR 被刪除時，K8s 的垃圾回收會自動清掉子資源，**你完全不需要寫刪除邏輯**（正文第 9 章）。只有「叢集外的東西」（雲端資源、外部系統的紀錄）才需要 finalizer。

**這個區分很重要**：能靠 ownerReference 的就不要用 finalizer，因為 finalizer 是有風險的機制而 GC 不是。

### 常見的坑

| # | 坑 | 後果 |
| --- | --- | --- |
| 1 | 在 reconcile 裡無條件建立資源 | 資源無限增生 |
| 2 | controller 寫 `spec` | 無限 reconcile 迴圈 |
| 3 | 在 reconcile 裡阻塞（長時間等待） | 卡住 worker，其他物件不被處理 |
| 4 | 對永久性錯誤無限重試 | API Server 壓力、日誌爆炸 |
| 5 | finalizer 沒有失敗路徑 | 物件永遠刪不掉 |
| 6 | 沒開 status 子資源 | 更新 status 會誤觸 spec 事件 |
| 7 | 沒設 ownerReference | 子資源變孤兒 |
| 8 | 直接用 client 打 API 而不用 cache | 大量不必要的 API 呼叫 |

---

## Part 5：StatefulSet 的實際運維

不寫 Operator 的話，有狀態服務就是靠 StatefulSet 手動管。這一節是它的日常操作手冊。

### 擴容與縮容

**擴容**：`kubectl scale sts db --replicas=5`，新的 Pod 依序建立（`db-3`、`db-4`），各自產生自己的 PVC。若 `podManagementPolicy` 是預設的 `OrderedReady`，會等前一個 Ready 才建下一個。

**縮容**：由高序號往低序號刪。**PVC 預設會保留**（附錄 C-2 的 `persistentVolumeClaimRetentionPolicy.whenScaled`），這是刻意的資料保護——但也是「縮容之後帳單沒降」的原因（附錄 K）。

再擴回去時，新的 `db-3` 會**重新綁上原本那個 PVC**（因為名稱是固定的 `data-db-3`）。這個行為多數時候是你要的，但如果那份資料已經過期，你會得到一個帶著舊資料的成員——**縮容後要清理的話，記得連 PVC 一起處理**。

### 換版與金絲雀

StatefulSet 的 `partition` 是原生的金絲雀機制：

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2 # 只更新序號 >= 2 的 Pod
```

`replicas: 3` 配 `partition: 2` 的話，只有 `db-2` 會被更新，`db-0` 與 `db-1` 保持舊版。驗證沒問題之後把 partition 逐步調成 1、0，就完成全部更新。**出問題時把 partition 調回去，只影響已更新的那幾個。**

這比 Deployment 的滾動更新可控得多，代價是要手動推進。

### 改不了的欄位怎麼辦

`volumeClaimTemplates` 建立後不可修改。要改（例如換 StorageClass 或調整標籤）有一個標準手法：

```powershell
# 1. 刪除 StatefulSet 但保留 Pod 與 PVC
kubectl delete sts db --cascade=orphan

# 2. 修改 YAML 後重新建立
kubectl apply -f statefulset.yaml

# 3. StatefulSet 會「認領」既有的 Pod（因為名稱與 selector 相符）
kubectl get sts db
```

`--cascade=orphan` 是關鍵——它只刪 StatefulSet 這個物件，Pod 與 PVC 留著。重建之後 StatefulSet 靠名稱與 selector 認領它們，服務不中斷。

**但這招有邊界**：它能改 template 的內容，**不能真的換掉已存在 PVC 的 StorageClass**。PVC 的 `storageClassName` 是不可變的，換儲存類型只能：建新的 PVC → 把資料複製過去 → 切換。沒有原地轉換的方法。

### 擴充儲存

```powershell
# 逐一改每個 PVC 的容量（StorageClass 要 allowVolumeExpansion: true）
kubectl patch pvc data-db-0 -p '{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"50Gi\"}}}}'
```

**只能調大不能調小。** 改 `volumeClaimTemplates` 沒有用（它只影響之後新建的副本），必須逐個 PVC 改。檔案系統需要重掛才生效的話，重啟該 Pod 即可。

### 主從切換

StatefulSet **不管這件事**——它只保證身分穩定與有序啟動，誰是主節點是應用層的事。

手動切換的一般流程是：確認副本的資料落後量 → 在資料庫層執行提升 → 更新指向主節點的 Service（通常是改 selector 或改一個標籤）→ 讓舊主節點以副本身分重新加入。

**這正是「需要持續執行的運維知識」的典型例子**——如果你希望它在半夜自動發生，那就是 Operator 的用武之地（Part 1 的判準）。

---

## Part 6：工具選擇

| 工具 | 語言 | 適合 |
| --- | --- | --- |
| **kubebuilder / controller-runtime** | Go | 主流選擇，社群資源最多 |
| **Operator SDK** | Go / Ansible / Helm | 基於 kubebuilder，多了 Ansible 與 Helm 模式 |
| **shell-operator / kopf** | Shell / Python | 輕量，適合簡單的自動化 |
| **Metacontroller** | 任何語言（webhook） | 用 webhook 寫 controller 邏輯，不必碰 Go |

**Operator SDK 的 Helm 模式值得注意**：它讓你用一份 Helm chart 當作 controller 的實作——CR 的 spec 變成 values，controller 負責持續套用。這正好對應 Part 2 的 L1/L2，**而且完全不用寫程式碼**。要做的事情落在 L1/L2 時，這是比自己寫 Go 好得多的選擇。

不用 Go 的另一條路是 `kopf`（Python）或 `shell-operator`——它們把 K8s 的 watch 機制包好，你只要寫「收到變化時做什麼」。適合公司內部的簡單自動化（例如「有新 namespace 就自動建一組資源」，附錄 O 的自助化）。

---

## 檢查清單

**決定要不要寫**

- [ ] 走過決策階梯，確認 Helm / Helm hooks 真的不夠
- [ ] 目標能力至少到 L3（有持續執行的運維知識），否則重新考慮
- [ ] 確認沒有成熟的社群方案可用

**選用既有 Operator**

- [ ] 維護狀態、CRD 版本穩定性、升級路徑都確認過
- [ ] **逃生門**：移除它之後資料與服務怎麼辦，已在測試環境驗證
- [ ] 權限範圍已限縮，不是 cluster-admin
- [ ] finalizer 的刪除行為已在測試環境驗證

**自己寫**

- [ ] Reconcile 冪等
- [ ] Level-triggered，不依賴事件內容
- [ ] CRD 開了 status 子資源，且有 `observedGeneration`
- [ ] 永久性錯誤不重試，寫進 conditions
- [ ] finalizer 有失敗路徑與手動移除程序（寫進文件）
- [ ] 子資源都設了 ownerReference
- [ ] 有 metrics 與告警（controller 自己也會壞）

**StatefulSet 運維**

- [ ] 知道縮容後 PVC 會保留，且有盤點機制
- [ ] 換版用 `partition` 做金絲雀
- [ ] 知道 `--cascade=orphan` 的用法與邊界
- [ ] 擴充儲存要逐個 PVC 改，且只能調大
- [ ] 主從切換程序已寫成 runbook 並演練過

## 常見誤區

| # | 誤區 | 真相 |
| --- | --- | --- |
| 1 | 「用 Operator 比較專業」 | 多一個要維護的元件；Helm 夠用就用 Helm |
| 2 | Operator 只是「自動化部署」 | 部署是 L1；價值從 L3 的生命週期管理才開始 |
| 3 | 收到事件才做事 | 事件會漏會重送，要 level-triggered |
| 4 | controller 可以改 spec | 會造成無限迴圈 |
| 5 | 什麼都用 finalizer 清理 | 叢集內資源用 ownerReference，GC 更可靠 |
| 6 | 縮容 StatefulSet 就會釋放儲存 | PVC 預設保留 |
| 7 | 改 `volumeClaimTemplates` 能擴充現有磁碟 | 只影響新副本，現有的要逐個改 PVC |
| 8 | StatefulSet 會處理主從切換 | 它只管身分與順序，切換是應用層的事 |
| 9 | 裝了 Operator 就不用懂底層 | 它出問題時你還是要看 StatefulSet 與 PVC |
| 10 | 社群 Operator 一定比較安全 | 要查維護狀態與權限範圍 |

## 連結

- [[62-stateful-workloads-decision]] — 附錄 AN：**這份講「怎麼操作」，那份講「該不該做」**——決策框架、進叢集的八項底線、六種災難模式
- [[09-extending-kubernetes]] — 正文：CRD、admission webhook、finalizer、ownerReference 的機制
- [[04-workloads]] — 正文：StatefulSet 三保證
- [[19-yaml-fields-workloads]] — 附錄 C-2：StatefulSet 全欄位與 PVC 保留策略
- [[21-yaml-fields-cluster-security]] — 附錄 C-4：CRD 全欄位與 status 子資源
- [[29-status-and-conditions]] — 附錄 G：conditions 與 `observedGeneration` 的讀法
- [[practice-5-database-and-state]] — 實戰 5：資料庫該不該進叢集
- [[37-platform-engineering]] — 附錄 O：用輕量 controller 做 namespace 自助化
- [[k8s-mastery]] — 教材總目錄
