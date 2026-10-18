---
type: reference
domain: tech
tags: [kubernetes, k8s, ci, build, runner, buildkit, security, cache, github-actions]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 AO：在叢集裡跑 CI 與建置

教材寫了 GitHub Actions 的 workflow 欄位（[[25-yaml-fields-pipeline]]）、也寫了 push tag 之後的完整交付鏈（[[practice-3-gitops-pipeline]]）。但那整條鏈裡，**CI 一直被當成「叢集外面的東西」**——它在別人的機器上跑，產出映像，推到 registry，然後 ArgoCD 接手。

當你成為管理員之後，遲早會有人問：

> 「runner 可不可以搬進我們的叢集？」

這個問題背後通常有三個真實驅動力，而它們都很正當：

| 驅動力 | 具體情境 |
| --- | --- |
| **成本** | 託管 runner 的分鐘數用超了，而叢集的機器晚上是閒的 |
| **內網存取** | 測試需要連地端資料庫、內部 registry、或受防火牆保護的服務 |
| **規格** | 需要大記憶體、GPU、或某個託管環境沒有的東西 |

但這件事的風險結構跟跑一般應用**完全不同**，因為 CI runner 執行的是**任意程式碼**。這一份講清楚三個難點（建容器、快取、安全）與該怎麼決定。

---

## Part 1：為什麼「在容器裡建容器」是個難題

CI 的核心動作是 `docker build`。而 `docker build` 需要一個 daemon——**Pod 裡沒有。**

這是所有「CI 上 K8s」方案的第一道門檻，而它有三條路，安全性差很多：

| 做法 | 怎麼運作 | 風險 |
| --- | --- | --- |
| **掛載節點的 Docker socket** | 把 `/var/run/docker.sock` 掛進 Pod | **等於把整台節點交出去** |
| **DinD（Docker-in-Docker）** | 在 Pod 裡跑一個完整 daemon，需要 `privileged: true` | 容器逃逸的風險大幅提高 |
| **無 daemon 建置器** | BuildKit rootless、或其他不需特權的建置工具 | **建議的預設**；相容性偶有例外 |

### 掛 socket 為什麼是最糟的

這一項要特別講，因為它最方便所以最常被選：

> 掛了節點的 Docker socket，Pod 裡的程式就能對**節點上的 daemon** 下指令。而 daemon 能做的事包含：以 `privileged` 啟動任意容器、掛載節點的根目錄、讀取節點上**其他所有容器**的檔案。
>
> 也就是說——**任何能發起一次建置的人，都能拿到那台節點的完整控制權。** 而「能發起建置」通常等於「能對 repo 推一個分支」。

這條路徑很難用 RBAC 擋，因為它繞過了 API Server：整件事發生在節點的 daemon 層，K8s 的權限系統根本看不到。

### DinD 的取捨

DinD 至少把 daemon 關在 Pod 裡，但它需要 `privileged: true`，而那會拿掉多數的核心防護（[[08-security-and-rbac]] 講的 Pod Security 那一層形同虛設）。它的另一個問題是**每個 Pod 一個新 daemon，代表每次都是空快取**——這會直接把建置時間拉長，接到 Part 2。

### 預設走無 daemon

除非有明確的相容性理由，**無 daemon 的建置器是預設選擇**：不需要特權、可以用 registry 當快取、跟 K8s 的安全模型相容。

選具體工具之前，**先確認該專案目前的維護狀態**（近期的 release、issue 有沒有人回）——這個領域的工具汰換較快，附錄 R 的「逃生門」思路在這裡同樣適用。

---

## Part 2：建置快取——叢集裡最痛的一點

**這是「搬進叢集之後大家開始抱怨變慢」的主因。**

託管 runner 通常有現成的快取機制；而在叢集裡，**每個 job 是一個全新的 Pod，什麼都沒有**。第一次跑完感覺良好，第二次跑還是一樣慢，因為上一次的成果隨著 Pod 一起消失了。

要快取的其實是三層不同的東西，混為一談就會解錯問題：

| 層 | 內容 | 怎麼處理 |
| --- | --- | --- |
| **基礎映像** | `FROM` 拉下來的那些 | 叢集內架 pull-through registry（就近、不重複拉） |
| **建置層（layer）** | Dockerfile 每一步的結果 | 用 registry 當快取後端（`--cache-to` / `--cache-from`） |
| **套件相依** | `node_modules`、NuGet、Maven | 掛持久卷，或用套件 proxy |

### registry 當快取後端

無 daemon 建置器多半支援把 layer 快取推到 registry，下次建置再拉回來：

```bash
# 概念示意：把快取寫進 registry 的一個 tag，下次從那裡讀
buildctl build \
  --output type=image,name=registry.internal/app:$TAG,push=true \
  --export-cache type=registry,ref=registry.internal/app:buildcache,mode=max \
  --import-cache type=registry,ref=registry.internal/app:buildcache
```

**這條路的好處是無狀態**——快取存在 registry，任何節點上的任何 Pod 都能用，不需要處理卷的掛載與競態。

### 掛持久卷的陷阱

用 PVC 存 `node_modules` 這類相依很直覺，但有兩個坑：

**第一，並行的 job 會互相踩。** 兩個 job 同時寫同一個快取目錄，輕則彼此覆蓋、重則寫壞。要嘛每個 job 一個獨立卷（就失去共用的意義），要嘛用支援並行的套件 proxy。

**第二，也是更嚴重的：快取會變成隱藏狀態。** 建置結果開始取決於「這個卷裡剛好有什麼」，於是出現「在 CI 上會過、重跑就不會過」的鬼故事。

> **判準：快取必須能被整個丟掉、重建，而結果不變。** 做不到這一點，它就不是快取，是不可重現的隱藏狀態。
>
> 實務上就是：清空快取重跑一次，如果結果不同，你的 CI 已經壞了，只是還沒被發現。

---

## Part 3：runner 的生命週期

### 常駐 vs 用完即丟

| 模型 | 運作 | 問題 |
| --- | --- | --- |
| **常駐 runner** | 一個長期執行的 Pod，接連跑很多 job | 前一個 job 的殘留（檔案、環境變數、背景程序）污染下一個 |
| **用完即丟（ephemeral）** | 每個 job 開一個新 Pod，跑完銷毀 | 冷啟動成本；但**這才是對的預設** |

「狀態污染」聽起來像小問題，但它同時是**安全問題**：一個惡意 job 可以在常駐 runner 上留下東西，等下一個有更高權限的 job 來執行。用完即丟從結構上消除這個攻擊面。

### 冷啟動與擴縮

用完即丟的代價是每個 job 都要拉映像、初始化。壓低它的方法就是 [[07-scheduling-and-resources]] 的老套路——**把 runner 映像做小**、讓節點上有現成的映像層、必要時保留少量暖機的 runner。

擴縮方面，CI 的負載是典型的**突發型**：白天尖峰、晚上為零。這正是縮到 0 的合理場景（[[49-messaging-and-events]] 的 KEDA 思路同樣適用——依佇列中的待跑 job 數擴縮）。

**而縮到 0 的前提是你願意接受冷啟動延遲**，這個取捨要跟使用 CI 的人講清楚，否則抱怨會變成「叢集很慢」。

---

## Part 4：安全——最容易出事的地方

**CI runner 是你叢集裡風險最高的東西，因為它的工作就是執行別人寫的程式碼。**

一般應用跑的是你自己審查過、透過 GitOps 部署的映像。runner 跑的是**任何人在 PR 裡寫的任何指令**。這個差異要放在心上。

### 把 CI 放進叢集後新增的攻擊面

| 攻擊面 | 說明 | 對策 |
| --- | --- | --- |
| **建置權限過大** | 特權容器或掛 socket → 節點淪陷 | 用無 daemon 建置器 |
| **同節點的鄰居** | runner 與生產 Pod 同節點 | 專用節點池 + taint |
| **runner 的 ServiceAccount** | 有部署權 → 任意 PR 能改生產 | **CI 只推映像，不碰叢集** |
| **fork 的 PR** | 外部貢獻者的程式碼在你的內網跑 | 需要核准才跑；不給機密 |
| **出站網路** | 被植入的相依可以往外傳資料 | NetworkPolicy 限制出站 |
| **快取污染** | 惡意 job 寫壞共用快取，影響後續建置 | 快取分區、可丟棄性 |

### 最重要的一條：CI 不該有叢集寫入權

這一條同時是安全要求與 GitOps 原則，兩邊指向同一個答案：

> **CI 的職責到「推出映像 + 更新 manifest repo 的版本號」為止。實際部署由 ArgoCD 拉取。**

如果 CI 有 `kubectl apply` 的權限，那麼**任何能改 workflow 檔的人都能直接改生產環境**——而 workflow 檔就在 repo 裡，改它跟改程式一樣容易。這一刀切下去，順帶讓 [[61-compliance-and-audit]] 的職務分離成立。

### 機密要用短期憑證

runner 需要推映像、可能需要讀資料庫。**把長期有效的密碼放進 CI 的機密，是外洩風險最高的做法之一**——因為它會出現在很多人有權限查看的地方，也可能被印進日誌。

較好的做法是用 OIDC 換取**短期**憑證：CI 用工作流程的身分向雲端/registry 換一個幾分鐘有效的 token。外洩的東西很快失效（呼應 [[06-config-and-storage]] 的「外洩即已失效」）。

### fork 的 PR 要特別處理

外部貢獻者送 PR 時，如果 CI 自動跑，等於**讓陌生人在你的內網執行程式碼**。多數 CI 平台預設不會把機密傳給來自 fork 的 PR，但**「不給機密」不等於「安全」**——程式碼仍然在你的網路裡跑，仍然能掃描內網、仍然能耗盡資源。

實務底線是：來自 fork 的 PR 要**經過核准才跑**，而且跑在**無法連到內網**的環境。

---

## Part 5：資源與干擾

CI 的資源曲線跟線上服務相反：**平常是零，一有人推程式就瞬間吃滿**。把它放進生產叢集而不設限，結果就是某天有人一次推了十個分支，然後線上服務開始被驅逐。

三件事要一起做：

```yaml
# 1. 專用節點池，用 taint 隔開
#    節點上：kubectl taint nodes ci-node-1 workload=ci:NoSchedule
tolerations:
  - key: workload
    operator: Equal
    value: ci
    effect: NoSchedule
nodeSelector:
  workload: ci
---
# 2. 低優先級——資源不足時先被搶佔的是 CI，不是線上服務
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: ci-low
value: -10 # 低於預設的 0
globalDefault: false
description: CI 工作負載，資源不足時優先被搶佔
---
# 3. namespace 層級的總量上限
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ci-quota
  namespace: ci
spec:
  hard:
    requests.cpu: "40"
    requests.memory: 80Gi
    pods: "50"
```

| 面向 | 線上服務 | CI 工作負載 |
| --- | --- | --- |
| QoS | Guaranteed | Burstable 即可 |
| 優先級 | 高 | **低（可被搶佔）** |
| 節點 | 一般節點池 | **專用池，可用 spot／可搶佔機器** |
| 中斷容忍 | 低 | **高——重跑就好** |

**最後一列是關鍵**：CI 是少數「被殺掉也沒關係」的工作負載，這讓它成為 spot／可搶佔機器的理想使用者（[[41-advanced-scheduling]]）。省下的成本常常就是搬進叢集的主要動機。

---

## Part 6：該不該做

| 情況 | 建議 |
| --- | --- |
| 只是覺得「都用 K8s 了 CI 也該進來」 | **不要**——沒有實際問題要解 |
| 託管 runner 分鐘數成本明顯偏高 | 值得評估，但要算進維運人力 |
| 建置需要連內網資源 | **這是最強的理由**——託管 runner 做不到 |
| 需要特殊規格（大記憶體、GPU） | 值得，而且能跟其他批次工作共用節點池 |
| 團隊只有一個人懂 K8s | **先不要**——CI 壞掉時全公司都停下來 |
| 有合規要求程式碼不能離開內網 | 幾乎是必須做 |

### 混合是最務實的答案

不必二選一：**一般 job 繼續用託管 runner，只有「需要內網」或「需要特殊規格」的 job 用叢集內的自架 runner。**

這樣你只承擔了必要那部分的維運責任，而不是把整條 CI 的可用性都變成自己的問題。

> **一個提醒：CI 掛掉的影響範圍比你想的大。** 線上服務掛了影響使用者，CI 掛了**整個開發團隊停止交付**——包含修復線上問題所需的緊急發布。
>
> 所以「把 CI 搬進叢集」實際上是把一個新的**關鍵路徑**接進你要負責的範圍，這個決定的份量跟它聽起來的輕鬆程度不成比例。

---

## 檢查清單

### 決定之前

- [ ] 有明確要解的問題（成本／內網／規格），不是「都用 K8s 了」
- [ ] 算過維運人力成本，不只是機器費用
- [ ] 知道 CI 掛掉會讓**整個團隊停止交付**，包含緊急修復

### 建置方式

- [ ] **沒有**掛載節點的 Docker socket
- [ ] **沒有**用 `privileged` 跑 DinD（除非有不可繞過的理由並已評估）
- [ ] 用無 daemon 建置器，且確認過該專案的維護狀態
- [ ] 快取用 registry 後端，而非共用可寫卷
- [ ] **清空快取重跑，結果不變**（否則那是隱藏狀態）

### 安全

- [ ] runner 用完即丟，不是常駐
- [ ] **runner 的 ServiceAccount 沒有叢集寫入權**（CI 只推映像）
- [ ] 機密用 OIDC 短期憑證，不放長期密碼
- [ ] 來自 fork 的 PR 需核准才跑，且跑在連不到內網的環境
- [ ] 用 NetworkPolicy 限制 runner 的出站
- [ ] runner 不與生產工作負載同節點、同 namespace

### 資源

- [ ] 專用節點池 + taint
- [ ] 低優先級 PriorityClass（可被線上服務搶佔）
- [ ] namespace ResourceQuota 設了總量上限
- [ ] 考慮 spot／可搶佔機器（CI 中斷容忍度高）
- [ ] 閒置時能縮到 0，且冷啟動延遲已跟使用者說明

---

## 常見誤區

| # | 誤區 | 真相 |
| --- | --- | --- |
| 1 | 掛 Docker socket 只是方便一點 | **等於把整台節點的控制權交出去**，且 RBAC 擋不住 |
| 2 | DinD 用 `privileged` 沒差 | 那會讓 Pod Security 那一層形同虛設 |
| 3 | 搬進叢集就會變快 | 通常**變慢**——託管 runner 的快取沒了 |
| 4 | 快取放 PVC 最直覺 | 並行會踩、且容易變成不可重現的隱藏狀態 |
| 5 | runner 常駐比較省 | 前一個 job 的殘留會污染、也是攻擊面 |
| 6 | CI 需要部署權限才能自動化 | **不需要**——推映像 + 改版本號，部署由 ArgoCD 拉 |
| 7 | fork 的 PR 不給機密就安全 | 程式碼仍在你的網路裡執行 |
| 8 | CI 跟線上服務放一起沒關係 | CI 是突發型，會把節點吃光 |
| 9 | CI 掛掉只是不方便 | **整個團隊停止交付**，含緊急修復 |
| 10 | 要嘛全搬進來、要嘛都不搬 | 混合最務實：只搬需要內網／特殊規格的部分 |

## 連結

- [[68-registry-operations]] — 附錄 AT：建置產出之後——tag 策略、保留政策與多架構
- [[practice-3-gitops-pipeline]] — 實戰 3：push tag 到部署的完整交付鏈
- [[25-yaml-fields-pipeline]] — 附錄 C-7：GitHub Actions workflow 全欄位
- [[00-docker-foundations]] — 正文：image layer 與建置的底層機制
- [[41-advanced-scheduling]] — 附錄 S：優先級搶佔、spot 機器、批次工作負載
- [[08-security-and-rbac]] — 正文：Pod Security、特權容器為何危險
- [[06-config-and-storage]] — 正文：機密管理與「外洩即已失效」
- [[61-compliance-and-audit]] — 附錄 AM：CI 沒有部署權，職務分離才成立
- [[48-testing-in-k8s]] — 附錄 Z：kind 在 CI、預覽環境
- [[37-platform-engineering]] — 附錄 O：CI 是平台團隊的責任還是應用團隊的
- [[k8s-mastery]] — 教材總目錄
