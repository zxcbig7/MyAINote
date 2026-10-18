---
type: reference
domain: tech
tags: [kubernetes, k8s, testing, ci, preview-environment, kind, vcluster, chaos]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 Z：測試策略在 K8s 上的落地

這套教材寫到第 61 份，完全沒有講過測試。這不是疏漏，是因為測試本身是應用開發的課題——但**在 K8s 環境測試有一批特有的問題**，而那些問題沒有人在教材裡處理過。

具體來說：`kubectl apply` 成功不代表服務會動、單元測試全綠不代表 probe 設對了、本機 Docker Compose 跑得好好的不代表叢集裡不會掛。這一份講的是**中間那一層**——介於「應用測試」與「上線之後」之間，那些只有在 K8s 環境才會發現的問題該怎麼提前抓到。

---

## Part 1：先分清楚「這個測試在驗證什麼」

K8s 環境的測試最常見的錯誤，是**把所有東西都塞進端對端測試**——起一個完整叢集、部署所有服務、然後跑一個緩慢又不穩定的測試套件。

正確的做法是先分類。任何一個測試都在驗證下面三件事之一：

| 驗證什麼 | 需要叢集嗎 | 例子 |
| --- | --- | --- |
| **應用邏輯** | 否 | 折扣算對了嗎、JWT 驗證擋住了嗎 |
| **部署設定** | 大多不用 | YAML 合法嗎、有沒有設 limits、selector 對得上嗎 |
| **叢集行為** | **是** | probe 真的會擋住流量嗎、NetworkPolicy 真的擋住了嗎、滾動更新真的不掉請求嗎 |

**絕大多數測試屬於前兩類，而前兩類不需要叢集。** 把它們搬出叢集，你的 CI 會快十倍而且穩定得多。真正需要叢集的只有第三類，而它的數量應該很少。

一個實用的反問：**這個測試如果失敗，是誰要修？** 應用開發者 → 前兩類；平台或部署設定 → 第二、三類。分不清楚的測試通常是設計得太大了。

---

## Part 2：不需要叢集的部分

### 應用測試：用 Testcontainers 而不是叢集

需要真實資料庫的整合測試，不需要 K8s——用 Testcontainers 在測試程序裡起一個真的資料庫容器就好。

```csharp
var oracle = new OracleBuilder().WithImage("gvenzl/oracle-free:23-slim").Build();
await oracle.StartAsync();
// 用 oracle.GetConnectionString() 跑真實的 EF Core 測試
```

**這比「連到共用測試資料庫」好得多**：每次測試都是乾淨狀態、可以平行跑、不會互相干擾、而且不需要維護一個長期存在的測試環境。

### Manifest 靜態驗證：CI 的第一道關卡

這一層抓的是「YAML 本身有沒有問題」，完全不需要叢集，而且跑起來只要幾秒：

```powershell
# 1. schema 驗證（欄位名、型別、apiVersion 是否存在）
kubeconform -strict -summary -kubernetes-version 1.33.0 k8s/

# 2. 最佳實踐檢查（沒設 limits、用 latest、以 root 執行…）
kube-linter lint k8s/

# 3. 自訂政策（公司規範）
conftest test k8s/ --policy policies/

# 4. Helm chart 的單元測試
helm unittest ./charts/my-app

# 5. 渲染後再驗一次（Helm/Kustomize 產出的才是真正要部署的）
helm template test ./charts/my-app -f ci/values-prod.yaml | kubeconform -strict -
```

**第 5 步常被忘記**：你驗證的應該是**渲染後的結果**，不是模板本身。模板寫錯導致產出無效 YAML 是很常見的一類 bug（附錄 T）。

`conftest` 讓你把公司規範寫成可測試的政策：

```rego
package main

deny[msg] {
  input.kind == "Deployment"
  not input.spec.template.spec.containers[_].resources.limits.memory
  msg := "每個容器都必須設定 resources.limits.memory"
}
```

**這跟 admission policy（附錄 O）是互補的**：admission 在叢集裡擋、conftest 在 CI 就擋——後者的回饋快得多，開發者在 PR 階段就知道，不必等部署失敗。

### 政策測試

如果你有寫 `ValidatingAdmissionPolicy` 或 Kyverno 政策，那些政策本身也要測：給一份「應該被擋」的 YAML 與一份「應該通過」的，驗證政策的行為符合預期。**沒有測過的政策，可能擋錯東西或什麼都沒擋。**

---

## Part 3：真的需要叢集的部分

這一層在 CI 裡用 **kind**（Kubernetes in Docker）跑最實際——它啟動快（幾十秒）、完全在容器裡、跑完即丟。

```yaml
# GitHub Actions 片段
- uses: helm/kind-action@v1
  with:
    node_image: kindest/node:v1.33.0
- run: |
    kubectl apply -f k8s/
    kubectl wait --for=condition=available --timeout=180s deployment/api
```

值得放在這一層的測試，共同點是**「只有真的部署才驗證得到」**：

**1. 部署得起來嗎**

```powershell
kubectl wait --for=condition=available --timeout=180s deployment/api
kubectl get endpointslice -l kubernetes.io/service-name=api-svc
```

這一步抓的是 selector 對不上、映像拉不到、ConfigMap 引用錯誤這類問題——**它們在靜態驗證階段完全看不出來**。

**2. RBAC 真的限制住了嗎**

```powershell
kubectl auth can-i list secrets --as=system:serviceaccount:demo:app-sa
# 預期輸出 no；輸出 yes 就讓 CI 失敗
```

**把 `auth can-i` 當成測試斷言**是很實用的一招——它讓「權限沒有意外放寬」變成可自動驗證的事，而不是靠 review。

**3. NetworkPolicy 真的擋住了嗎**

```powershell
kubectl run probe --rm -i --image=curlimages/curl --restart=Never -- curl -m 3 http://api-svc
# 預期在被擋的情境下失敗
```

NetworkPolicy 是「寫了但沒生效」的重災區（CNI 不支援、selector 縮排錯、方向沒涵蓋到），而**唯一可靠的驗證方式就是實際打一次**。

**4. 滾動更新真的不掉請求嗎**

附錄 D 的實驗 A6 就是這個測試的手動版：起一個持續打的迴圈，觸發更新，數失敗次數。把它自動化成 CI 的一個步驟，`maxUnavailable` 或 `preStop` 被人改壞時就會被抓到。

> **注意 kind 與真實叢集的差異**：kind 沒有真正的 LoadBalancer、儲存是本機的、預設 CNI 不支援 NetworkPolicy（要換）、也沒有多節點的真實網路。所以它適合驗證「設定是否正確」，不適合驗證「效能」或「跨節點行為」。

---

## Part 4：預覽環境（每個 PR 一套）

### 它解決什麼問題

「這個 PR 我要怎麼試？」——傳統答案是「合併到 develop 然後看測試環境」，但那時候已經來不及，而且多個 PR 會互相污染。

預覽環境讓每個 PR 有自己的一套服務，可以直接點開網址看、可以讓 PM 驗收、可以跑端對端測試而不互相干擾。**對前端與 API 變更特別有價值。**

### 兩種做法

| 做法 | 隔離程度 | 成本 | 適合 |
| --- | --- | --- | --- |
| **每個 PR 一個 namespace** | 中（共用叢集層資源） | 低 | 多數情況 |
| **每個 PR 一個虛擬叢集**（vcluster） | 高（各自的 API Server 與 CRD） | 中 | 需要測 CRD、webhook、叢集層設定時 |

第一種用 ArgoCD 的 `pullRequest` generator 最省事（附錄 C-5）：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: previews
  namespace: argocd
spec:
  goTemplate: true
  generators:
    - pullRequest:
        github:
          owner: org
          repo: my-app
          labels: ["preview"] # 只有貼了 preview 標籤的 PR 才建
        requeueAfterSeconds: 300
  template:
    metadata:
      name: "preview-{{.number}}"
    spec:
      project: previews
      source:
        repoURL: https://github.com/org/my-app.git
        targetRevision: "{{.head_sha}}"
        path: charts/my-app
        helm:
          parameters:
            - name: ingress.host
              value: "pr-{{.number}}.preview.example.com"
            - name: image.tag
              value: "{{.head_sha}}"
      destination:
        server: https://kubernetes.default.svc
        namespace: "preview-{{.number}}"
      syncPolicy:
        automated:
          prune: true
        syncOptions:
          - CreateNamespace=true
```

**PR 關閉時 ApplicationSet 會自動移除對應的 Application**，連帶清掉 namespace——這個自動清理是它相對於手動建環境的最大優勢。

### 三個要想清楚的問題

**資料怎麼辦？** 三個選項：每個預覽環境起一個自己的資料庫（乾淨但慢、耗資源）、共用一個測試資料庫（快但會互相干擾）、或**共用資料庫但各自 schema/租戶**（折衷，通常最實際）。無論哪種，都要有**種子資料**，否則環境起來了但沒東西可看。

**成本怎麼控制？** 預覽環境很容易失控——十個 PR 就是十套服務。控制手段：只對貼了特定標籤的 PR 建立、副本數設 1、資源 requests 設小、**設 TTL 自動清理超過 N 天沒動的**、以及用 namespace 的 ResourceQuota 設上限（附錄 O）。

**要不要對外？** 預覽環境有真實網址很方便，但那也意味著未上線的功能可以被公開存取。至少要加上 IP 白名單或基本認證（附錄 F 的 `auth-type: basic`）。

---

## Part 5：測試環境與正式環境的差異

**「測試環境測不出來」是所有測試策略的極限。** 誠實面對差異，比假裝沒有差異安全。

| 差異 | 能不能消除 | 怎麼處理 |
| --- | --- | --- |
| **規模**（副本數、節點數） | 難 | 接受；效能問題靠正式環境的監控與漸進發布 |
| **資料量與分佈** | 難 | 至少讓測試資料的**形狀**接近（有大租戶、有邊界值） |
| **流量模式** | 難 | 壓測補一部分 |
| **叢集設定**（CNI、policy、PSA） | **能** | **必須一致**，否則測試毫無意義 |
| **部署方式**（chart、values 結構） | **能** | 用同一份 chart，只換 values |
| 外部依賴（第三方 API） | 部分 | 用沙盒或 mock，但要知道行為可能不同 |
| 憑證與網域 | 部分 | 至少走同一套簽發流程 |

**中間那三列是重點：能消除的差異就必須消除。** 測試環境用 Flannel、正式用 Calico，那你的 NetworkPolicy 測試等於沒測；測試環境沒開 PSA、正式開了 `restricted`，那你會在上線那天才發現 Pod 起不來。

### 測試環境永遠測不到的東西

誠實列出來，才知道要靠別的手段補：

- **真實流量的尖峰與分佈**（靠監控 + HPA + 壓測）
- **長時間累積的問題**（記憶體洩漏、磁碟成長 → 靠正式環境的趨勢告警）
- **真實資料的邊界情況**（那個資料特別多的租戶）
- **跨區網路的真實延遲**
- **第三方服務的真實行為**（限流、逾時、間歇性錯誤）
- **並行的真實程度**（測試環境的併發通常低一個量級）

這份清單直接對應到附錄 H 的監控與告警設計——**測不到的東西，就要能在正式環境很快發現。**

---

## Part 6：上線之後也是測試

### 部署後自動 smoke test

部署完成不等於服務正常。在 CI/CD 的最後加一步：

```powershell
kubectl rollout status deployment/api --timeout=300s
curl.exe -f https://api.example.com/healthz
curl.exe -f https://api.example.com/api/v1/ping
```

**任何一步失敗就自動回滾。** 這一步的價值在於它驗證的是「真正的正式環境」——包含 Ingress、憑證、DNS、外部依賴，那些測試環境永遠模擬不了的部分。

### 漸進式發布本身就是測試

金絲雀發布（附錄 F、C-7）的本質是**用真實流量做測試，但限制爆炸半徑**：5% 的流量走新版，觀察錯誤率與延遲，沒問題才擴大。

這是應對「測試環境測不到」的最有效手段——因為它用的就是真實流量、真實資料、真實依賴。搭配自動化的判斷條件（錯誤率超過門檻就自動回滾），它比任何測試環境都可靠。

### 合成監控

定期從外部打幾個關鍵路徑（登入 → 查詢 → 下單），確認整條鏈是通的。它抓的是「所有 Pod 都健康但使用者流程斷了」這類問題——例如某個外部依賴掛了、憑證過期、DNS 被改。

---

## Part 7：混沌工程

**附錄 D 的 20 個實驗其實就是手動版的混沌工程**：故意弄壞、觀察、驗證系統的反應符合預期。

要不要自動化？判準是：**你的系統是否已經穩定到「隨機殺一個 Pod 不會有人注意到」？** 還沒到的話，先把附錄 D 的實驗在測試環境手動做一遍就夠了——自動化混沌會製造你還處理不了的噪音。

真的要開始，順序是由小到大：

| 階段 | 做什麼 | 驗證什麼 |
| --- | --- | --- |
| 1 | 隨機殺 Pod | 副本數與 readiness 設對了 |
| 2 | drain 一個節點 | PDB 與重排程正常 |
| 3 | 注入網路延遲 | 逾時與斷路器有效 |
| 4 | 讓下游服務回錯誤 | 降級與重試策略正確 |
| 5 | 模擬 AZ 故障 | 拓撲分散有效 |

工具方面 Chaos Mesh 與 LitmusChaos 都是 CNCF 專案，用 CRD 定義實驗。但**在導入工具之前，先確認你有能力觀察結果**——沒有好的監控就做混沌，你只是在製造無法解釋的故障。

---

## 檢查清單

**分層**

- [ ] 團隊清楚每個測試在驗證什麼（應用邏輯／部署設定／叢集行為）
- [ ] 需要叢集的測試數量很少，且都是「只有真部署才驗證得到」的

**不需要叢集的**

- [ ] 整合測試用 Testcontainers，不依賴共用測試資料庫
- [ ] CI 跑 `kubeconform` + `kube-linter` + 自訂政策
- [ ] **驗證的是渲染後的結果**，不是模板本身
- [ ] Helm chart 有 `helm unittest`
- [ ] admission 政策本身有測試

**需要叢集的**

- [ ] CI 用 kind 跑，且知道它與真實叢集的差異
- [ ] 有部署驗證（`rollout status` + endpoints 檢查）
- [ ] **RBAC 用 `auth can-i` 當測試斷言**
- [ ] NetworkPolicy 有實際打一次驗證
- [ ] 滾動更新不掉請求有自動化驗證

**預覽環境**

- [ ] 用 ApplicationSet 的 pullRequest generator（PR 關閉自動清理）
- [ ] 有種子資料
- [ ] 有 TTL 與 ResourceQuota 控制成本
- [ ] 有存取控制（不要讓未上線功能公開）

**環境差異**

- [ ] **叢集設定（CNI、PSA、policy）測試與正式一致**
- [ ] 用同一份 chart，只換 values
- [ ] 已列出「測試環境測不到」的清單，並有對應的正式環境監控

**上線後**

- [ ] 部署後有自動 smoke test，失敗即回滾
- [ ] 關鍵路徑有合成監控
- [ ] 高風險變更走金絲雀

---

## 常見誤區

| # | 誤區 | 真相 |
| --- | --- | --- |
| 1 | 什麼都放進端對端測試 | 慢又不穩；先分清楚在驗證什麼 |
| 2 | 整合測試要連測試叢集的資料庫 | Testcontainers 更快更乾淨也不會互相干擾 |
| 3 | 驗證 Helm 模板本身 | 要驗**渲染後**的結果 |
| 4 | `kubectl apply` 成功就算部署成功 | 那只代表 API Server 接受了願望 |
| 5 | 測試環境 CNI 跟正式不同也沒差 | NetworkPolicy 測試會完全失效 |
| 6 | 預覽環境開了就不用管 | 十個 PR 十套服務，要有 TTL 與 quota |
| 7 | 預覽環境不需要存取控制 | 未上線功能會被公開存取 |
| 8 | 有測試環境就不用金絲雀 | 測試環境永遠測不到真實流量與資料 |
| 9 | 混沌工程越早導入越好 | 系統還不穩時只會製造處理不了的噪音 |
| 10 | RBAC 靠 review 就好 | `auth can-i` 可以變成自動化斷言 |

## 連結

- [[71-schema-migration]] — 附錄 AW：「測試環境只有一個版本」的具體代價
- [[63-ci-in-cluster]] — 附錄 AO：跑這些測試的 runner 本身放哪裡
- [[26-lab-drills]] — 附錄 D：20 個實驗，混沌工程的手動版
- [[42-helm-chart-design]] — 附錄 T：chart 的 CI 測試五道
- [[37-platform-engineering]] — 附錄 O：admission policy 與 CI 檢查的分工
- [[practice-3-gitops-pipeline]] — 實戰 3：CI/CD 管線裡放測試的位置
- [[practice-1-containerize-your-app]] — 實戰 1：Compose 驗證與 K8s 的差異
- [[30-production-readiness]] — 附錄 H：測不到的東西要靠監控補
- [[47-api-versioning]] — 附錄 Y：OpenAPI diff 與契約測試
- [[k8s-mastery]] — 教材總目錄
