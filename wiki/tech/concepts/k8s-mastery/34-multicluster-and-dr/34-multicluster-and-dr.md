---
type: reference
domain: tech
tags: [kubernetes, k8s, disaster-recovery, backup, etcd, velero, multicluster, rto, rpo]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 L：多叢集與災難復原

附錄 H 在檢查清單裡寫了一句話：「**沒有實際還原過的備份等於沒有備份**」，然後就沒有下文了。這一份補上下文——三種災難情境的完整演練程序，以及多叢集拓撲該怎麼選。

先講一個殘酷的事實：**多數團隊的備份是壞的，而他們不知道。** 原因不是沒設備份，而是備份與還原之間有一堆隱含前提從來沒被驗證過——快照檔在不在、憑證有沒有一起備份、還原步驟有沒有人會、還原之後應用連不連得上。這些只有真的走一遍才會發現，而發現的時機不該是叢集已經不見的那天。

## 沒有 RTO / RPO，其他都是空談

任何災難復原討論的第一步，是把兩個數字講清楚。**這兩個數字決定你該花多少錢、做到什麼程度**，跳過它們就會出現「花大錢做雙活，但資料庫只有每日備份」這種不對稱的設計。

| 名詞 | 問題 | 決定什麼 |
| --- | --- | --- |
| **RTO**（Recovery Time Objective） | 「多久要恢復服務？」 | 拓撲架構、自動化程度 |
| **RPO**（Recovery Point Objective） | 「可以掉多少資料？」 | 備份頻率、複寫方式 |

實務上的對應關係大致如下：

| RTO | 需要什麼 | 成本 |
| --- | --- | --- |
| 數天 | 有備份、有文件 | 極低 |
| 數小時 | 備份 + 演練過的還原程序 + IaC | 低 |
| 30 分鐘內 | 主備叢集，DNS 切換 | 中 |
| 幾乎零 | 雙活叢集，資料同步複寫 | **高，且應用要為此設計** |

| RPO | 需要什麼 |
| --- | --- |
| 24 小時 | 每日備份 |
| 1 小時 | 每小時備份 |
| 幾分鐘 | 資料庫 WAL／archive log 持續歸檔 |
| 零 | 同步複寫（效能代價明顯） |

**先問業務要什麼，再決定技術。** 大多數內部系統的答案其實是「RTO 幾小時、RPO 一天」可接受——那你需要的只是「備份 + 演練過的程序」，不是雙活叢集。

---

## 要保護的四層東西

很多人以為備份 K8s 就是備份 etcd。那只是四分之一。

| 層 | 內容 | 怎麼保護 | 不可再生？ |
| --- | --- | --- | --- |
| **1. 叢集狀態** | etcd 裡的所有物件 | etcd 快照 / Velero | 否——GitOps 可重建 |
| **2. 工作負載定義** | Deployment、Service、設定 | **git**（GitOps 已解決） | 否 |
| **3. 應用資料** | PV 裡的東西、資料庫 | 資料庫自己的備份 + Velero | **是** |
| **4. 叢集外的依賴** | DNS、憑證、registry 映像、Vault 的機密、雲端資源 | 各自的機制 | 部分是 |

**第 3 層是唯一真正不可再生的。** 第 1、2 層在有 GitOps 的環境裡幾乎可以從 git 重建；第 4 層常常被完全遺忘，卻是「叢集重建好了但服務還是不通」的原因——DNS 還指向舊的 IP、憑證沒了、Harbor 裡的映像也在同一台掛掉的機器上。

盤點第 4 層是這一節最該做的功課。把「重建這座叢集需要哪些叢集外的東西」列成一張清單，每一項標註它自己的備援方式。

---

## 三種備份手段與各自的邊界

### etcd 快照

```powershell
# 備份（在 control plane 節點上）
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F-%H%M).db `
  --endpoints=https://127.0.0.1:2379 `
  --cacert=/etc/kubernetes/pki/etcd/ca.crt `
  --cert=/etc/kubernetes/pki/etcd/server.crt `
  --key=/etc/kubernetes/pki/etcd/server.key

# 驗證快照本身沒壞（一定要做，這步只要幾秒）
etcdutl snapshot status /backup/etcd-2026-08-16-0300.db --write-out=table
```

**etcd 快照有一個致命的隱含前提：它必須跟 `/etc/kubernetes/pki` 一起備份。** 還原 etcd 之後，如果憑證（尤其是 CA）不是原本那一組，所有元件都無法互相驗證，叢集起不來。這是還原演練最常卡住的地方，而且錯誤訊息（一堆 x509 相關）完全不會指向「你忘了備份憑證」。

```powershell
tar -czf /backup/pki-$(date +%F).tar.gz /etc/kubernetes/pki
```

適用邊界：etcd 快照涵蓋**整座叢集的所有物件**，但**不含 PV 裡的資料**。它適合「叢集控制平面壞掉」的情境，不適合「誤刪某個 namespace」（因為還原是全叢集回到某個時間點，會把其他人的變更一起回滾）。

### Velero

Velero 做的是**物件層級 + 資料層級**的備份，粒度比 etcd 快照細得多，所以是日常最常用的。

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-prod
  namespace: velero
spec:
  schedule: "0 3 * * *"
  template:
    includedNamespaces:
      - demo
      - demo-prod
    excludedResources:
      - events
      - events.events.k8s.io
    snapshotVolumes: true
    defaultVolumesToFsBackup: false
    ttl: 720h # 保留 30 天
    hooks:
      resources:
        - name: db-quiesce
          includedNamespaces: [demo]
          labelSelector:
            matchLabels:
              app: db
          pre:
            - exec:
                container: postgres
                command: ["/bin/sh", "-c", "psql -c 'CHECKPOINT'"]
```

那個 `hooks` 值得注意：**直接對執行中的資料庫做磁碟快照，得到的是「當機瞬間」的狀態**，不保證一致。pre hook 讓資料庫先把緩衝寫入磁碟，還原後的資料才可靠。沒有 hook 的資料庫備份，還原時可能需要跑復原程序，甚至根本起不來。

Velero 需要一個物件儲存（S3、MinIO）當後端，而**那個儲存絕對不能跟叢集在同一個故障域**——放在同一台機器上的備份，機器掛了就一起沒了。

### 資料庫自己的備份

這是第 3 層的主力，而且**不能被 Velero 取代**。

實戰第五章講過：PVC 快照只保證「檔案系統當下的樣子」，不保證資料庫處於一致狀態。正解是資料庫自己的機制——Oracle 的 RMAN、PostgreSQL 的 `pg_dump` + WAL 歸檔——輸出到叢集外的儲存。

三者的分工可以這樣記：**etcd 快照救控制平面、Velero 救工作負載、資料庫備份救資料**。少任何一個，就有一類災難你救不回來。

---

## 演練情境 A：誤刪 namespace

**發生頻率最高，也最該先演練。** 目標 RTO：15 分鐘。

```powershell
# --- 準備（在測試叢集上）---
kubectl create namespace drill-a
kubectl -n drill-a create deployment web --image=nginx:1.25
kubectl -n drill-a create configmap app-config --from-literal=key=value
velero backup create drill-a-backup --include-namespaces drill-a --wait

# --- 製造災難 ---
kubectl delete namespace drill-a

# --- 還原 ---
velero restore create --from-backup drill-a-backup --wait
velero restore describe <restore-name>

# --- 驗收 ---
kubectl -n drill-a get all,configmap
```

**驗收標準**（不是「看起來有東西」就算過）：

- [ ] Deployment 的副本數與原本一致，且全部 Ready
- [ ] ConfigMap / Secret 的內容正確
- [ ] Service 有 endpoints
- [ ] 從叢集內實際打一次 API 有正常回應
- [ ] 記錄實際耗時，與 RTO 目標比對

**有 GitOps 的話還有更快的路**：直接讓 ArgoCD 重新同步就好，因為工作負載定義都在 git 裡。這時候 Velero 只需要救 PV 資料。這正是 GitOps 在災難復原上的實質價值——**它把第 1、2 層變成可再生的**。

---

## 演練情境 B：單一 PV 資料損毀

目標 RTO：30 分鐘到數小時（取決於資料量）。

```powershell
# --- 還原特定的 PVC ---
velero restore create --from-backup daily-prod-20260816030000 `
  --include-resources persistentvolumeclaims,persistentvolumes `
  --selector app=db `
  --namespace-mappings demo:demo-restore
```

`--namespace-mappings` 把資料還原到**另一個 namespace**，這是刻意的：先在旁邊還原、確認資料正確，再決定要不要切換。**直接蓋回正式 namespace 是不可逆的操作**，一旦還原的是壞資料，你連原本的壞狀態都回不去了。

驗收標準：

- [ ] 資料庫能正常啟動且不需要跑復原程序
- [ ] 抽驗幾筆關鍵資料，確認完整性
- [ ] 確認資料的時間點符合 RPO（最新一筆資料是什麼時候的？）

資料庫的話，優先用資料庫自己的還原機制（RMAN restore、`pg_restore`），Velero 的磁碟層還原當備案。

---

## 演練情境 C：整座叢集不見了

這是最花時間、也最少人真的做過的一個。目標 RTO 依拓撲而定，從數小時到數天。

### 路線一：有 GitOps（推薦）

```
1. 用 IaC（Terraform / kubeadm 腳本）建一座新叢集     [30–60 分]
2. 裝回叢集層元件：CNI、Ingress Controller、
   cert-manager、Prometheus、ArgoCD 本身              [30 分]
3. 把 ArgoCD 指向 manifest repo，讓它自己同步所有應用  [15 分]
4. 用 Velero 還原 PV 資料                              [依資料量]
5. 切換 DNS 到新叢集                                   [DNS TTL 時間]
6. 驗證                                                [30 分]
```

**第 2 步是最容易低估的。** 應用可以靠 ArgoCD 自動長回來，但「ArgoCD 自己」和它依賴的那批元件得先有人裝。解法是把叢集層元件也納入 IaC 或一份 bootstrap 腳本——**這件事必須在災難之前做好**，否則你會在最糟的時刻現場摸索安裝順序。

第 5 步的 DNS TTL 也常被忽略：TTL 設 3600 秒的話，切換之後最久要等一小時才全面生效。**知道自己 RTO 目標的人，會提前把關鍵記錄的 TTL 調到 60 秒。**

### 路線二：從 etcd 快照還原

沒有 GitOps、或需要精確還原到某個時間點時用這條。

```powershell
# 在新的 control plane 節點上
# 1. 先還原憑證（否則後面全部失敗）
tar -xzf /backup/pki-2026-08-16.tar.gz -C /

# 2. 停掉 kube-apiserver（kubeadm 環境把 manifest 移走即可）
mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/

# 3. 還原快照到新的資料目錄
etcdutl snapshot restore /backup/etcd-2026-08-16-0300.db `
  --data-dir=/var/lib/etcd-restored

# 4. 讓 etcd 指向新目錄，然後把 apiserver 放回去
mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/

# 5. 驗證
kubectl get nodes
kubectl get pods -A
```

多節點 etcd 的關鍵紀律：**所有 member 必須從同一份快照還原**，而且 `--initial-cluster` 參數要正確。混用不同快照會產生無法收斂的分裂狀態。

還原之後有兩件事一定要檢查：**Node 是否重新註冊**（舊的 Node 物件可能指向已經不存在的機器），以及**PV 是否還指向有效的儲存**（etcd 裡的 PV 物件還在，但實際磁碟可能已經沒了）。

---

## 多叢集拓撲怎麼選

| 拓撲 | RTO | 複雜度 | 成本 | 適合 |
| --- | --- | --- | --- | --- |
| **單叢集 + namespace 隔離** | 數小時–數天 | 低 | 低 | 內部系統、小團隊 |
| **dev / prod 分開的叢集** | 同上 | 低 | 中 | **多數團隊的合理起點** |
| **主備（active-passive）** | 15–30 分 | 中 | 中高 | 有明確 RTO 要求的營運系統 |
| **雙活（active-active）** | 近乎零 | **高** | 高 | 對外服務、跨區容錯 |

三條選型建議：

**dev 與 prod 用不同叢集，不要只用 namespace 隔開。** 理由不只是隔離——叢集升級、CNI 換版、webhook 測試這些高風險操作，需要一個可以弄壞的地方。namespace 提供不了這個。

**主備架構的難點不在 K8s，在資料。** 應用層的主備很簡單（ArgoCD 同時部署到兩座叢集，備援那座 `replicas: 0`），難的是資料庫的複寫與切換——那是資料庫的課題，不是 K8s 的。

**雙活需要應用為它設計。** 兩座叢集同時寫入意味著要處理衝突、要有全域唯一 ID、要接受最終一致性。**沒有為此設計過的應用直接放上雙活架構，結果是資料損毀而不是高可用。**

### 多叢集怎麼管理

ArgoCD 的 `ApplicationSet` 用 cluster generator 一次部署到所有叢集（附錄 C-5）：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: demo-all-clusters
  namespace: argocd
spec:
  goTemplate: true
  generators:
    - clusters:
        selector:
          matchLabels:
            env: prod
  template:
    metadata:
      name: "demo-{{.name}}"
    spec:
      project: default
      source:
        repoURL: https://github.com/org/k8s-manifests.git
        targetRevision: main
        path: "overlays/{{.metadata.labels.region}}"
      destination:
        server: "{{.server}}"
        namespace: demo
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

**用一座「管理叢集」跑 ArgoCD、部署到所有其他叢集**，是多叢集最常見也最實用的模式。但要記得問一個問題：**管理叢集自己掛了怎麼辦？** 答案通常是「它掛了不影響已部署的服務，只是暫時不能部署新版」——確認這個答案可接受，或為它也做備援。

流量層面則靠外部的全域負載平衡（Cloudflare、雲端的 Global LB）依健康狀態把流量導到活著的叢集，這一層不在 K8s 裡面。

---

## 演練節奏與紀律

| 頻率 | 做什麼 | 耗時 |
| --- | --- | --- |
| **每週** | 確認備份任務有跑成功、快照檔存在且大小合理 | 5 分鐘 |
| **每月** | 演練情境 A（誤刪 namespace 還原） | 30 分鐘 |
| **每季** | 演練情境 B（PV 資料還原到旁邊的 namespace） | 2 小時 |
| **每年** | 演練情境 C（從零重建叢集），最好在測試環境全程計時 | 半天 |

四條讓演練有意義的紀律：

**計時。** 沒有計時就不知道實際 RTO 是多少，也就無法判斷目前的架構夠不夠。

**輪流由不同的人執行。** 只有一個人會做的還原程序，等同於單點故障。

**照文件做，卡住就改文件。** 演練的產出之一是一份真的能用的程序文件，而不是「我記得大概是這樣」。

**記錄每次的實際耗時與卡住的地方。** 這是唯一能證明「情況正在變好」的資料。

---

## 常見誤區

| # | 誤區 | 為什麼危險 |
| --- | --- | --- |
| 1 | 有備份就等於能還原 | 快照檔可能損毀、步驟可能沒人會 |
| 2 | 備份 etcd 但沒備份 `/etc/kubernetes/pki` | 還原後憑證對不上，叢集起不來 |
| 3 | 備份放在同一座叢集／同一台機器 | 同時消失 |
| 4 | 用 etcd 快照救「誤刪 namespace」 | 會把全叢集回滾到那個時間點 |
| 5 | 直接對執行中的資料庫做磁碟快照 | 不保證一致，還原後可能起不來 |
| 6 | 忘了叢集外的依賴（DNS、憑證、registry） | 叢集重建好了服務還是不通 |
| 7 | 沒有把叢集層元件納入 IaC | 災難當下現場摸索安裝順序 |
| 8 | DNS TTL 很長卻要求 15 分鐘 RTO | 光等 DNS 生效就超過目標 |
| 9 | 上雙活但應用沒為它設計 | 資料衝突與損毀 |
| 10 | 還原直接蓋回正式 namespace | 不可逆，還原壞資料就全毀 |

## 檢查清單

- [ ] RTO 與 RPO 有明確數字，且是跟業務確認過的
- [ ] 四層資料都有對應的保護機制，特別是**第 4 層叢集外依賴已盤點**
- [ ] etcd 快照與 `/etc/kubernetes/pki` 一起備份
- [ ] 備份存放在叢集外、不同故障域
- [ ] 資料庫用自己的機制備份，不只靠磁碟快照
- [ ] Velero 對資料庫有設 pre hook
- [ ] 叢集層元件（CNI、Ingress、cert-manager、ArgoCD）納入 IaC 或 bootstrap 腳本
- [ ] 關鍵 DNS 記錄的 TTL 與 RTO 目標相符
- [ ] 情境 A 每月演練，且**計時**
- [ ] 情境 C 每年至少一次全程演練
- [ ] 還原程序文件是照著演練修正過的，不是憑記憶寫的
- [ ] 至少兩個人做過完整還原

## 連結

- [[70-node-lifecycle-and-ha]] — 附錄 AV：失去 etcd quorum 時叢集會怎樣
- [[65-inheriting-a-cluster]] — 附錄 AQ：接手後的第一件事就是這裡的還原演練
- [[12-cluster-operations]] — 正文：etcd 備份還原、憑證輪替、Velero 的操作細節
- [[30-production-readiness]] — 附錄 H：上線檢查與維運節奏
- [[27-upgrades-and-deprecations]] — 附錄 E：升級前的可回復性檢查
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：ApplicationSet 的八種 generator
- [[practice-5-database-and-state]] — 實戰 5：資料庫備份與 StatefulSet
- [[practice-3-gitops-pipeline]] — 實戰 3：GitOps 讓第 1、2 層變成可再生
- [[61-compliance-and-audit]] — 附錄 AM：演練要當下就留紀錄——沒紀錄等於沒演練過
- [[62-stateful-workloads-decision]] — 附錄 AN：有狀態服務進叢集前，還原演練是硬性條件
- [[k8s-mastery]] — 教材總目錄
