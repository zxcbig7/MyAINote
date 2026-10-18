---
type: reference
domain: tech
tags: [kubernetes, k8s, production, day-2, sre, capacity, backup, alerting, runbook]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 H：上線前檢查與 Day-2 維運

前面所有內容加起來，回答的是「這東西怎麼運作、怎麼寫、壞了怎麼查」。這一份回答的是另一個問題：**當這座叢集變成你的責任時，你每天、每週、每年該做什麼。**

這是「會用 K8s」與「負責 K8s」之間的真正差距。會用的人能把服務部署起來；負責的人要能回答：這座叢集還能塞多少東西、備份還原過沒有、憑證什麼時候到期、半夜出事誰接、上次演練是什麼時候。這些問題沒有一個能靠 `kubectl` 查出來，全部要靠制度。

內容分成四塊：新叢集上線前的一次性檢查、每個服務上線前的例行檢查、日常維運的節奏，以及事故發生時的流程。

---

## 一、新叢集上線前（一次性）

### 控制平面

- [ ] **etcd 至少三副本**，且分散在不同故障域。兩副本比單副本更糟——它無法形成多數決，任一台掛掉整個叢集就唯讀
- [ ] etcd 有獨立的磁碟，且是 SSD。etcd 對 fsync 延遲極度敏感，跟其他服務共用磁碟是常見的隱形殺手
- [ ] API Server 前面有負載平衡，且健康檢查打的是 `/readyz` 而不是 `/healthz`（後者在還沒準備好服務時也可能回 200）
- [ ] `--audit-policy-file` 已設定，稽核日誌有送到叢集外
- [ ] etcd 落盤加密（`EncryptionConfiguration`，附錄 C-6）已啟用，且 `identity` provider 在最後一個
- [ ] API Priority and Fairness 保持啟用，不要因為某個 controller 打太兇就整個關掉

### 節點

- [ ] `systemReserved` 與 `kubeReserved` 已設定（附錄 C-6）。**沒設等於允許 Pod 把 kubelet 餓死**
- [ ] `evictionHard` 門檻合理，且 `containerLogMaxSize` × `containerLogMaxFiles` × 最大 Pod 數不會撐爆磁碟
- [ ] 節點分組策略確定：control plane 有 taint、特殊工作負載（GPU、大記憶體）有專屬 taint 與 label
- [ ] 時間同步（NTP/chrony）正常——憑證驗證與分散式選主都依賴它
- [ ] 映像 GC 門檻設定合理（`imageGCHighThresholdPercent`）

### 叢集服務

- [ ] CoreDNS 有多副本且設了 autoscaler，`ndots` 影響已評估（附錄 D 的 C3）
- [ ] 有預設 StorageClass，且 `volumeBindingMode` 對多可用區是 `WaitForFirstConsumer`
- [ ] CNI 支援 NetworkPolicy（Flannel 不支援，套了不報錯也不生效）
- [ ] Ingress controller 多副本 + PDB，`use-forwarded-headers` 依前置 LB 情況設定
- [ ] metrics-server 正常（`kubectl top nodes` 有輸出），否則 HPA 完全不會動
- [ ] 私有 registry 的 pull secret 已配置在需要的 namespace，或掛在 ServiceAccount 上

### 安全基線

- [ ] 所有 namespace 都有 Pod Security Admission label（至少 `warn` + `audit`）
- [ ] `default` ServiceAccount 的 `automountServiceAccountToken` 已關閉
- [ ] 沒有任何 binding 把 `cluster-admin` 給了廣泛的 group
- [ ] 有 default-deny 的 NetworkPolicy 基線（至少在正式 namespace）
- [ ] webhook 的 `failurePolicy: Fail` 已排除 `kube-system` 且 webhook 本身多副本 + PDB

### 可回復性

- [ ] etcd 自動快照，且**做過一次完整的還原演練**
- [ ] 工作負載定義全部在 git（GitOps），叢集可以從零重建
- [ ] PV 資料有獨立的備份機制（Velero 或儲存層快照）
- [ ] 憑證到期監控已設（`kubeadm certs check-expiration` 或 Prometheus 規則）

> 這份清單裡只有一項是「沒做就一定會後悔」的：**還原演練**。備份存在不等於能還原——快照檔損壞、還原步驟沒人會、還原後憑證對不上，這些只有真的演練過才會發現。把它排進行事曆，一年至少一次。

---

## 二、每個服務上線前（例行）

技術面直接用附錄 C-4 結尾那份 YAML 檢查清單。這裡補的是**制度面**——技術上正確但沒人知道怎麼維運的服務，仍然不算 production ready。

| 項目 | 具體要有什麼 |
| --- | --- |
| **SLO** | 明確的可用性與延遲目標，例如「99.9% 的請求在 300ms 內完成」 |
| **監控** | 至少四個黃金訊號的儀表板：延遲、流量、錯誤、飽和度 |
| **告警** | 對應 SLO 的告警，且每條告警都有 `runbook_url` |
| **Runbook** | 一頁文件：這服務是什麼、依賴誰、常見故障與處理步驟、誰是負責人 |
| **容量** | 單一副本能扛多少 QPS（壓測過的數字，不是猜的） |
| **依賴圖** | 上游是誰、下游是誰、哪些是硬依賴 |
| **回滾方式** | 一行指令或一個按鈕，且演練過 |
| **資料** | 有沒有狀態、備份怎麼做、還原要多久 |

一份夠用的 runbook 模板：

```markdown
# <服務名> Runbook

## 這是什麼
一句話說明職責。負責團隊 / 值班聯絡方式。

## 依賴
- 上游（誰呼叫我）：
- 下游（我呼叫誰）：硬依賴標注 ★
- 資料存放：

## 儀表板與日誌
- Grafana:
- Kibana query:

## 常見故障
| 症狀 | 可能原因 | 處理 |
| --- | --- | --- |
| 5xx 上升 | 下游 X 逾時 | 看 X 的狀態；必要時開降級開關 |
| 延遲上升 | CPU throttle | 看 throttled 指標，臨時擴 replicas |

## 緊急處理
- 擴容：kubectl scale deploy/<name> --replicas=N
- 回滾：kubectl rollout undo deploy/<name>
- 降級開關：<ConfigMap key 或 feature flag>

## 不要做什麼
（例如：不要直接刪 PVC、不要重啟 leader）
```

最後一節「不要做什麼」是最容易被省略、也最有價值的一段——半夜三點被叫起來的人，需要知道哪些操作會把小事變成大事。

---

## 三、容量規劃

容量問題的核心是三個數字，而且它們常常差很多：

| 數字 | 怎麼查 | 意義 |
| --- | --- | --- |
| **requests 總和** | `kubectl describe node` 的 Allocated resources | scheduler 認為用掉了多少 |
| **allocatable** | `kubectl get node -o jsonpath='{.status.allocatable}'` | 實際可分配上限 |
| **實際使用** | `kubectl top node` / Prometheus | 真的用了多少 |

`requests 總和 / allocatable` 是**排程飽和度**——這個數字到 100% 就再也排不進新 Pod，即使機器實際只用了 30%。`實際使用 / allocatable` 是**真實飽和度**。兩者的差距就是浪費，也是最容易拿回來的成本。

盤點指令：

```
# 各節點的 requests 佔比
kubectl describe nodes | grep -A5 "Allocated resources"

# 用 Prometheus 找出「requests 開很大但實際用很少」的容器
# (P95 實際用量 / requests) 低於 30% 的，就是調整對象
quantile_over_time(0.95,
  container_memory_working_set_bytes{container!=""}[7d]
) / on(pod, container) kube_pod_container_resource_requests{resource="memory"}
```

調整 requests 的正確方法是**看歷史分位數而不是拍腦袋**：記憶體用 P95～P99（因為超過就死），CPU 用 P50～P90（因為超過只是變慢）。VPA 開 `updateMode: "Off"` 跑一段時間，它算出的 recommendation 就是現成的建議值（附錄 C-5）。

**節點規格的取捨**也值得想清楚：大節點裝箱效率好、系統保留的比例低，但單台故障影響面大、且單一 Pod 能拿到的資源上限受限於節點；小節點爆炸半徑小，但每台都要扣掉一份 `systemReserved`，數量一多浪費就可觀。常見的折衷是「單一節點不超過總容量的 10%，且能容納最大 Pod 的三倍」。

**緩衝要留多少**：至少要能承受「一台節點掛掉 + 一次滾動更新」同時發生。實務上叢集整體排程飽和度長期維持在 70% 左右是合理的，超過 85% 就該加節點了。

---

## 四、日常節奏

### 每天

- 看昨晚的告警與 event，確認每一條都有結論（不是「自己好了」）
- `kubectl get pods -A | grep -v Running | grep -v Completed`，處理殘留的異常 Pod
- 檢查有沒有 Pod 在 CrashLoop 或反覆重啟（附錄 G 的重啟排行指令）

### 每週

- 節點容量與飽和度趨勢
- 憑證到期檢查
- 孤兒資源盤點（見下）
- 檢視新增的 Ingress／NetworkPolicy／RBAC 變更是否合理

### 每月

- etcd 備份還原演練（至少讀取驗證）
- 檢查有沒有新的棄用 API 警告（附錄 E）
- 權限審查：`kubectl get clusterrolebinding -o wide` 看有沒有多出來的 cluster-admin
- 依賴元件的版本與 CVE 檢查

### 每季／每年

- K8s 版本升級（一年至少兩次，見附錄 E）
- 完整災難復原演練：從備份重建一座叢集
- SLO 檢討：目標是否仍合理、error budget 用掉多少
- 成本檢討

### 孤兒資源盤點指令

```
# Released 狀態的 PV（PVC 已刪但資料還在，持續計費）
kubectl get pv --field-selector=status.phase==Released

# 沒有任何 Pod 使用的 PVC
kubectl get pvc -A -o json | jq -r '.items[] | .metadata.namespace + "/" + .metadata.name'

# 已完成但沒被清掉的 Job（沒設 ttlSecondsAfterFinished 的後果）
kubectl get jobs -A --field-selector=status.successful=1

# 沒有 endpoints 的 Service（多半是已下線服務的殘留）
kubectl get svc -A -o json | jq -r '.items[] | select(.spec.type!="ExternalName") | .metadata.namespace + "/" + .metadata.name'

# 沒有被任何 Pod 引用的 ConfigMap / Secret
kubectl get cm -A --no-headers | wc -l
```

---

## 五、必備告警清單

告警的原則是**只對「需要人立刻做事」的狀況發出**。CPU 高不是告警（那是儀表板），使用者受影響才是。下面這組是最小可用集合，可直接寫成 `PrometheusRule`（附錄 C-5）。

| 告警 | 條件 | 為什麼要 |
| --- | --- | --- |
| `KubeNodeNotReady` | Node `Ready != True` 持續 5 分鐘 | 容量少一台 |
| `KubePodCrashLooping` | 重啟率 > 0 持續 15 分鐘 | 服務不穩 |
| `KubePodNotReady` | Pod 非 Ready 持續 15 分鐘 | 可能已在掉流量 |
| `KubeDeploymentReplicasMismatch` | 期望 ≠ 可用 持續 15 分鐘 | 部署卡住 |
| `KubePersistentVolumeFillingUp` | 可用空間 < 15% 且趨勢惡化 | 磁碟滿 = 服務死 |
| `KubeMemoryOvercommit` | 所有 requests 總和 > 容量 − 一台節點 | 一台掛就排不下 |
| `KubeCertificateExpiration` | 憑證 < 30 天到期 | 到期 = 全叢集失聯 |
| `KubeAPIErrorBudgetBurn` | API Server 錯誤率燒得太快 | 控制平面異常 |
| `EtcdHighFsyncDuration` | etcd fsync P99 > 500ms | etcd 即將出事的前兆 |
| `HPAMaxedOut` | HPA 在 max 停留超過 30 分鐘 | 容量不足，需要人介入 |
| `CPUThrottlingHigh` | throttle 比例 > 25% 持續 15 分鐘 | 延遲問題的隱形來源 |
| `PVCPending` | PVC Pending 超過 15 分鐘 | 儲存供給有問題 |

三條讓告警不會被無視的規則：**每條告警都要有 runbook 連結**；**分成 page（半夜叫人）與 ticket（上班處理）兩級**，只有使用者受影響的才 page；**每個月檢討一次誤報**，誤報率高的告警不是調閾值就是刪掉——沒人相信的告警比沒有告警更危險。

---

## 六、事故流程

### 嚴重度分級

| 級別 | 定義 | 反應 |
| --- | --- | --- |
| SEV1 | 核心功能完全不可用 | 立即 page，全員投入，對外公告 |
| SEV2 | 部分功能不可用或嚴重降級 | 立即 page |
| SEV3 | 有影響但有 workaround | 上班時間處理 |
| SEV4 | 無使用者影響 | 排入待辦 |

### 第一個小時

順序刻意如此——**先止血，再找根因**。很多事故被拖長，是因為有人堅持要先搞懂為什麼。

1. **確認影響範圍**：哪些使用者、哪些功能、從什麼時候開始
2. **止血優先**：能回滾就回滾、能擴容就擴容、能切流量就切。根因可以事後查
3. **指定一個指揮者**：負責決策與對外溝通，不動手
4. **開一條溝通管道**，所有動作在裡面留下時間戳
5. **每個變更一次只做一件事**，並記錄——同時改三個地方會讓你永遠不知道哪個有效
6. 穩定後再開始蒐證：`kubectl get events`、日誌、metric 截圖（**event 只留一小時，先存下來**）

### 事後檢討

在 48 小時內做完，重點是**時間線與系統性缺陷**，不是責任歸屬。三個必答問題：為什麼會發生、為什麼沒有更早被發現、下次怎麼讓它不發生或影響更小。產出必須是**有負責人與期限的具體行動項**，否則檢討會變成儀式。

---

## 七、把制度寫進叢集

上面很多檢查其實可以自動化，不必靠人記得：

| 想確保的事 | 用什麼強制 |
| --- | --- |
| 每個 Pod 都有 requests/limits | `LimitRange` + `ValidatingAdmissionPolicy`（附錄 C-4） |
| 不准用 `latest` tag | Kyverno / OPA 政策 |
| 每個 namespace 有 quota | 建立 namespace 的流程自動附帶 |
| 安全基線 | Pod Security Admission `enforce: restricted` |
| 棄用 API 不進 repo | CI 跑 `pluto detect-files`（附錄 E） |
| YAML 品質 | CI 跑 `kubeconform` + `kube-linter` |
| 部署一定經過 git | ArgoCD `selfHeal: true`，手改會被改回去 |

最後一項的效果最大：開啟 `selfHeal` 之後，「有人手動改了叢集」這個問題就從制度問題變成技術上不可能的事。這也是 GitOps 除了版本控制之外，最實際的維運價值。

---

## 連結

- [[64-slo-and-alerting]] — 附錄 AP：SLO 怎麼訂、錯誤預算怎麼算、告警清單怎麼砍
- [[12-cluster-operations]] — etcd 備份還原、憑證輪替、Node 維護的實際操作
- [[27-upgrades-and-deprecations]] — 附錄 E：升級與 API 棄用
- [[29-status-and-conditions]] — 附錄 G：日常巡檢時該看的欄位
- [[14-prometheus-grafana]] — 告警設計、USE/RED 與 PromQL
- [[21-yaml-fields-cluster-security]] — 上線前的 YAML 檢查清單
- [[26-lab-drills]] — 附錄 D：把這裡的故障模式親手做一遍
- [[13-troubleshooting]] — 事故當下的分層定位方法
- [[k8s-mastery]] — 教材總目錄
- [[44-knowledge-transfer]] — 附錄 V：讓維運能力不只存在一個人身上
- [[38-security-incident-response]] — 附錄 P：安全事故的特有流程
- [[43-migration-to-k8s]] — 附錄 U：新系統搬進來時的上線節奏
