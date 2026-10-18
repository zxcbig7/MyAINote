---
type: concept
domain: tech
tags: [kubernetes, k8s, docker, argocd, helm, prometheus, elk, mastery, curriculum, devops]
sources:
  - raw/devops/Docker/01-基礎概念/Docker/Docker.md
  - raw/devops/Kubernetes (K8s)/Kubernetes (K8s).md
  - raw/devops/Kubernetes (K8s)/K8s YAML 概念與架構/K8s YAML 概念與架構.md
  - raw/devops/Helm Chart/helm-tutorial/helm-tutorial.md
  - raw/devops/argocd-tutorial/argocd-tutorial.md
  - raw/devops/ELK/Kibana Query Language (KQL).md
  - raw/devops/troubleshooting/troubleshooting.md
created: 2026-07-31
updated: 2026-08-14
---

# 雲原生部署體系 — 從會用到問不倒

這不是一份速查手冊。速查手冊回答「怎麼做」，而這套教材要回答的是「為什麼」。

兩者的差別在被追問的第二層就會現形。知道 `kubectl apply` 怎麼下的人很多，能說清楚這個指令送出去之後，請求經過哪些關卡、誰決定 Pod 該去哪台機器、為什麼 API 回了 200 但 Pod 還沒跑起來的人很少。前者遇到沒見過的錯誤只能貼上 Google，後者能從症狀反推根因。這套教材的目標是把讀者送到後者那一側。

涵蓋範圍是一條完整的交付鏈：**容器（Docker）→ 編排（Kubernetes）→ 打包與交付（Helm、ArgoCD）→ 可觀測性（Prometheus/Grafana、ELK）**。這幾樣東西在實務上從來不是分開學的，一個部署問題可能起因於 Dockerfile 的一行 `COPY`，表現成 ArgoCD 的 OutOfSync，最後在 Kibana 的日誌裡才找到真相。

## 誰該讀這套教材

正文預設讀者會用 Docker、看過 K8s 的 YAML，也許已經照著教學把服務部署起來過，但心裡清楚自己是在照抄範例——不確定每個欄位為什麼要那樣寫，也不確定出事的時候該從哪裡查起。

讀完之後，應該能夠獨立設計 YAML 而不是拼湊、審查別人的部署設定並指出問題、從一個模糊的「服務怪怪的」推理到具體根因，以及在被同事追問「為什麼」的時候，答得出機制而不只是現象。

### 完全沒有基礎怎麼辦

如果上面那個預設對你不成立——你沒真的部署過東西、看到終端機會緊張、或第 0 章開頭的「namespace、cgroup、OverlayFS」讓你想關掉——**先讀 [[intro-0-start-here]] 入門篇**。

入門篇是正文之前的六章台階，完全不預設 Linux、網路、容器的知識，從「程序是什麼」「port 是什麼」開始，帶你親手跑起第一個容器與第一個 Pod，並看懂常見的錯誤訊息。讀完再回來讀正文第 0 章，會順很多。

### 想直接動手做自己的專案

入門篇跑的是官方 nginx 映像。想把**自己寫的**應用送上叢集，走[[practice-1-containerize-your-app|實戰篇]]——三章走完「容器化 → 部署一整組服務 → GitOps 自動化」的完整鏈路，以 ASP.NET Core + React + Harbor + ArgoCD 為例，每個欄位都解釋為什麼。它跟正文是互補的：實戰篇給你一條能跑通的路，正文告訴你這條路為什麼這樣鋪。

## 進度總覽

**入門篇 6 章 + 實戰篇 6 章 + 正文 16 章 + 59 附錄完成**，約 **540,000 字**、**97 張圖解**。

| 篇 | 章節 | 核心問題 | 狀態 |
| --- | --- | --- | --- |
| **入門篇** | [[intro-0-start-here]] | 完全沒基礎該從哪開始、這條路長什麼樣 | ✅ |
| | [[intro-1-server-and-process]] | 伺服器、程序、port 到底在講什麼？部署是哪四件事？ | ✅ |
| | [[intro-2-linux-and-terminal]] | 終端機那些指令在做什麼？怎麼在別人的機器上找檔案看日誌？ | ✅ |
| | [[intro-3-network-basics]] | 打一個網址按 Enter 之後發生了幾件事？4xx 跟 5xx 差在哪？ | ✅ |
| | [[intro-4-yaml-syntax]] | 為什麼縮排一直錯？為什麼版本號要加引號？ | ✅ |
| | [[intro-5-first-container-and-pod]] | 手把手跑起第一個容器，再用 K8s 做一次 | ✅ |
| | [[intro-6-error-messages]] | 這行紅字在說什麼？我下一步該做什麼？ | ✅ |
| **實戰篇** | [[practice-1-containerize-your-app]] | 把自己的 ASP.NET Core + React 容器化，而不是跑官方 nginx | ✅ |
| | [[practice-2-deploy-real-app]] | 一組真實服務需要哪七個物件？每個欄位為什麼這樣寫？ | ✅ |
| | [[practice-3-gitops-pipeline]] | push tag 之後怎麼自動部署？誰在拉、誰在推？ | ✅ |
| | [[practice-4-write-yaml-from-scratch]] | 對著空檔案寫不出來？從需求推導出 YAML 的五問法 | ✅ |
| | [[practice-5-database-and-state]] | 資料庫該不該進叢集？連線數為何是乘法？schema 怎麼零停機改 | ✅ |
| | [[practice-6-observability]] | 服務「怪怪的」怎麼看出來？告警該對什麼發？ | ✅ |
| **容器篇** | [[00-docker-foundations]] | 容器在 kernel 層到底是什麼？image layer 為什麼刪不掉東西？ | ✅ |
| **基礎篇** | [[01-why-kubernetes]] | 部署的痛從哪來，K8s 的取捨是什麼 | ✅ |
| | [[02-cluster-internals]] | `kubectl apply` 的完整旅程、為什麼是 pull-based | ✅ |
| | [[03-api-and-yaml]] | GVK、apiVersion 棄用、labels/selector、server-side apply | ✅ |
| **資源篇** | [[04-workloads]] | 三種 Probe 差在哪？滾動更新為什麼還是掉請求？ | ✅ |
| | [[05-networking]] | ClusterIP 為什麼 ping 不通？封包從外部到容器的完整路徑 | ✅ |
| | [[06-config-and-storage]] | 改了 ConfigMap 為什麼沒生效？PVC 為什麼一直 Pending？ | ✅ |
| **治理篇** | [[07-scheduling-and-resources]] | requests/limits 真義、CPU throttle vs Memory OOMKill、QoS | ✅ |
| | [[08-security-and-rbac]] | 認證授權三道關卡、RBAC 四物件配對、Pod Security | ✅ |
| | [[09-extending-kubernetes]] | 為什麼 YAML 被改了？namespace 為何卡 Terminating？ | ✅ |
| **交付篇** | [[10-helm]] | `include` vs `template`、`nindent`、values 覆蓋優先序 | ✅ |
| | [[11-argocd]] | Sync 與 Health 為何獨立？OutOfSync 但看起來一樣怎麼辦？ | ✅ |
| **維運篇** | [[12-cluster-operations]] | etcd 備份還原、憑證輪替、版本升級、Velero | ✅ |
| | [[13-troubleshooting]] | 分層定位方法論、Pod 狀態機、19 個真實案例庫 | ✅ |
| **可觀測性篇** | [[14-prometheus-grafana]] | PromQL、`rate` vs `irate`、histogram 算 P95、USE/RED | ✅ |
| | [[15-elk-elastic]] | 倒排索引、`text` vs `keyword`、KQL、ILM、ELK vs Loki | ✅ |
| **附錄** | [[16-self-assessment]] | 144 題自我檢測，蓋住答案自己講一遍才算會 | ✅ |
| | [[17-cheatsheet]] | 緊急排錯十連發、17 種 YAML 骨架、PromQL/KQL 速查 | ✅ |
| | [[18-yaml-fields-pod]] | metadata / PodSpec / Container 逐欄位，含預設值與版本門檻 | ✅ |
| | [[19-yaml-fields-workloads]] | Deployment/STS/DS/Job/CronJob、HPA `behavior`、PDB、Quota | ✅ |
| | [[20-yaml-fields-network-storage]] | Service/Ingress/NetworkPolicy、PV/PVC/SC、ConfigMap/Secret | ✅ |
| | [[21-yaml-fields-cluster-security]] | Namespace/PSA、RBAC 四物件、Node/Taint、CRD、Webhook | ✅ |
| | [[22-yaml-fields-ecosystem]] | ArgoCD/Helm/Prometheus/cert-manager/ESO/VPA/Gateway API/Kustomize | ✅ |
| | [[23-yaml-fields-rare-builtins]] | CSI 家族、CSR、APF、DRA + kubelet/kube-proxy/scheduler/kubeadm 設定檔 | ✅ |
| | [[24-yaml-fields-istio]] | VirtualService/DestinationRule/AuthorizationPolicy 等 Istio 全欄位 | ✅ |
| | [[25-yaml-fields-pipeline]] | GitHub Actions workflow、cloudflared config、Docker Compose | ✅ |
| | [[26-lab-drills]] | 附錄 D：20 個破壞—診斷—修復實驗，在 minikube 上親手弄壞 | ✅ |
| | [[27-upgrades-and-deprecations]] | 附錄 E：版本升級、已移除 API 對照表、升級前檢查清單 | ✅ |
| | [[28-ingress-nginx-annotations]] | 附錄 F：ingress-nginx annotation 百科與全域 ConfigMap | ✅ |
| | [[29-status-and-conditions]] | 附錄 G：status/conditions/exit code 判讀，症狀→欄位對照 | ✅ |
| | [[30-production-readiness]] | 附錄 H：上線前檢查、容量規劃、告警清單、事故流程 | ✅ |
| | [[31-glossary]] | 附錄 I：約 140 條術語百科，全書導航層 | ✅ |
| | [[32-istio-ingress-gateway]] | 附錄 J：Istio Ingress Gateway，與 ingress-nginx 的取捨、503 四種旗標 | ✅ |
| | [[33-cost-optimization]] | 附錄 K：requests 調校方法論、節點碎片化、孤兒資源盤點 | ✅ |
| | [[34-multicluster-and-dr]] | 附錄 L：RTO/RPO、三種還原演練腳本、多叢集拓撲選型 | ✅ |
| | [[35-cloud-networking]] | 附錄 M：VPC/IGW/NAT、Pod IP 從哪來、LoadBalancer 背後、IRSA | ✅ |
| | [[36-ebpf-and-cilium]] | 附錄 N：kube-proxy 的極限、eBPF 原理、Cilium 該不該換 | ✅ |
| | [[37-platform-engineering]] | 附錄 O：責任邊界、golden path、namespace 自助化、政策即程式碼 | ✅ |
| | [[38-security-incident-response]] | 附錄 P：供應鏈與 SBOM、機密外洩處置、叢集被入侵的應變與蒐證 | ✅ |
| | [[39-performance-troubleshooting]] | 附錄 Q：「服務變慢了」的分層定位、尾端延遲六因、三個完整推演 | ✅ |
| | [[40-operators-and-stateful]] | 附錄 R：該不該寫 Operator、reconcile 六原則、StatefulSet 運維手冊 | ✅ |
| | [[41-advanced-scheduling]] | 附錄 S：優先級分層與搶佔、gang scheduling、GPU、spot 批次 | ✅ |
| | [[42-helm-chart-design]] | 附錄 T：設計給別人用的 chart——介面、逃生門、破壞性變更、ArgoCD 相容 | ✅ |
| | [[43-migration-to-k8s]] | 附錄 U：既有系統搬上 K8s——盤點、分波、雙跑切換、Windows 應用 | ✅ |
| | [[44-knowledge-transfer]] | 附錄 V：知識傳承——分層培訓路徑、文件四分法、讓知識流動的機制 | ✅ |
| | [[45-microservices-and-communication]] | 附錄 W：該不該拆微服務、四種通訊模式、mesh 解決與解決不了什麼 | ✅ |
| | [[46-advanced-self-assessment]] | 附錄 X：75 題進階自我檢測，涵蓋實戰篇與附錄 E–W | ✅ |
| | [[47-api-versioning]] | 附錄 Y：介面怎麼演進而不打破呼叫方、多版本並存、棄用流程 | ✅ |
| | [[48-testing-in-k8s]] | 附錄 Z：測試分層、kind 在 CI、預覽環境、環境差異與混沌 | ✅ |
| | [[49-messaging-and-events]] | 附錄 AA：訊息系統選型、consumer 擴縮與 KEDA、至少一次與冪等 | ✅ |
| | [[50-caching]] | 附錄 AB：多副本下的本機快取陷阱、Redis 設定、雪崩與降級 | ✅ |
| | [[51-background-jobs]] | 附錄 AC：背景工作四種形式的選擇、多副本重複執行、CronJob 陷阱 | ✅ |
| | [[52-file-and-object-storage]] | 附錄 AD：使用者檔案不放 PVC、預簽名 URL 直傳、生命週期與孤兒檔 | ✅ |
| | [[53-configuration-management]] | 附錄 AE：設定分類、多環境 overlay、四道防護、熱重載的真相 | ✅ |
| | [[54-developer-experience]] | 附錄 AF：inner loop 為何變慢、四種本機開發策略、避免設定漂移 | ✅ |
| | [[55-logging-strategy]] | 附錄 AG：日誌三種用途、該記什麼、成本算術與四個減量手段 | ✅ |
| | [[56-frontend-deployment]] | 附錄 AH：前端版本切換不是原子的、舊 JS 404、快取策略、SSR | ✅ |
| | [[57-database-connections]] | 附錄 AI：連線池中介、讀寫分離、連線失效偵測、故障轉移行為 | ✅ |
| | [[58-api-gateway-and-edge]] | 附錄 AJ：邊界層的職責邊界、認證授權分層、限流兩層、對外對內分離 | ✅ |
| | [[59-adoption-roadmap]] | **附錄 AK：導入路線圖**——把全書排成 Phase 0–4 的時間軸與各階段驗收 | ✅ |
| | [[60-advanced-cheatsheet]] | 附錄 AL：進階速查表，附錄 E–AK 引入的工具與指令補遺 | ✅ |
| | [[61-compliance-and-audit]] | 附錄 AM：合規與稽核，把「有沒有做」變成「能不能證明」，讓證據自動產生 | ✅ |
| | [[62-stateful-workloads-decision]] | 附錄 AN：有狀態服務要不要進叢集，決策框架與缺一就出事的底線 | ✅ |
| | [[63-ci-in-cluster]] | 附錄 AO：在叢集裡跑 CI 與建置，三種建容器方式的風險差、快取、runner 安全 | ✅ |
| | [[64-slo-and-alerting]] | 附錄 AP：SLO 與錯誤預算怎麼訂、多視窗燃燒率告警、不被半夜吵醒的設計 | ✅ |
| | [[65-inheriting-a-cluster]] | 附錄 AQ：接手一座既有叢集，前 90 天把未知變成已知的盤點與排序 | ✅ |
| | [[66-ingress-to-gateway-api]] | 附錄 AR：從 Ingress 遷移到 Gateway API，角色分離、annotation 對照與並行策略 | ✅ |
| | [[67-scaling-limits]] | 附錄 AS：叢集長大之後會先撞到什麼牆、怎麼保護控制平面不被一行指令打垮 | ✅ |
| | [[68-registry-operations]] | 附錄 AT：映像 registry 的營運，掛了就起不了新 Pod 的單點依賴、tag 與保留政策 | ✅ |
| | [[69-third-self-assessment]] | 附錄 AU：第三份自我檢測，70 題涵蓋附錄 Y–AT | ✅ |
| | [[70-node-lifecycle-and-ha]] | 附錄 AV：節點生命週期與控制平面高可用，牲畜非寵物、etcd quorum、沙箱與汰換 | ✅ |
| | [[71-schema-migration]] | 附錄 AW：資料庫 schema 變更與部署的交界，滾動更新期的並存、expand-contract、回滾 | ✅ |
| | [[72-cascading-failure]] | 附錄 AX：級聯失敗與韌性模式，慢比掛更危險、重試放大 27 倍、超時預算 | ✅ |
| | [[73-long-lived-connections]] | 附錄 AY：gRPC／WebSocket 長連線，負載為何不均、部署為何斷線、路徑逾時 | ✅ |
| | [[74-distributed-tracing]] | 附錄 AZ：分散式追蹤，第三支柱的實作——context 傳遞、取樣策略、三支柱串接 | ✅ |

## 學習路徑

每天的份量抓在兩到三小時，重點是**邊讀邊在 minikube 上動手驗證**。教材裡的 YAML 範例都應該實際套下去看結果，尤其是那些「如果不這樣寫會出什麼事」的反例——親手把它弄壞一次，比讀十遍都有效。

> 沒有基礎的話，這七天路徑之前還要加一個週末給入門篇（[[intro-0-start-here]]，六章、每章一到兩小時）。跳過那個週末直接上路，第二天就會卡住。

| 天 | 章節 | 這天結束後你能回答 |
| --- | --- | --- |
| Day 1 | 00 | 容器和虛擬機到底差在哪？為什麼 Dockerfile 的順序會影響 build 速度？ |
| Day 2 | 01–03 | K8s 解決了什麼問題？`kubectl apply` 之後發生了什麼事？ |
| Day 3 | 04 | Deployment 滾動更新時，舊 Pod 什麼時候才真的被砍掉？ |
| Day 4 | 05–06 | 為什麼 Service 連得到但 Ingress 連不到？ConfigMap 改了為什麼沒生效？ |
| Day 5 | 07–09 | 為什麼這個 Pod 排不進去？為什麼我送出去的 YAML 被改了？ |
| Day 6 | 10–11 | ArgoCD 顯示 OutOfSync 但兩邊看起來一樣，怎麼回事？ |
| Day 7 | 12–15 | 同事說「服務掛了」，你的第一個指令下什麼？P95 延遲怎麼從 Prometheus 撈？ |

## 怎麼用這套教材

**第一遍求通不求精。** 遇到卡住的段落先標記起來繼續往下，很多概念要看過後面才回頭理解得了——例如 Finalizer 為什麼存在，要先知道 controller 怎麼運作。

**第二遍動手拆。** 回到標記處，在 minikube 上實際把每個機制跑一次。特別是治理篇與可觀測性篇的內容，光讀不做幾乎留不住。

**第三遍反過來考自己。** 教材裡的「常見誤解」與「同事會來問你的問題」小段落，蓋住答案先自己講一遍。講得出來才算會。

**不知道從哪開始的話，先看 [[59-adoption-roadmap]]（附錄 AK）**——它把整套教材排成「第一個月 / 第一季 / 半年 / 一年」的時間軸，並明確列出每個階段**不該做**什麼。本頁的表格是主題式導航（查得到），那一份是時間式導航（知道順序）。

**四種附錄各有各的時機。** 附錄 A（[[16-self-assessment]]）是讀完之後驗收用的；附錄 B（[[17-cheatsheet]]）是出事時第二螢幕開著的；附錄 C 這八份（[[18-yaml-fields-pod]] 起）則是寫 YAML 與 review 別人 YAML 時查的——它按資源逐欄位列出型別、預設值與版本門檻，回答的是「有哪些欄位可以寫、不寫的話預設是什麼」，跟正文回答「為什麼要這樣寫」剛好互補；附錄 C 以 **v1.33** 為基準，落地前記得用 `kubectl explain` 在自己的叢集驗證一次。

附錄 D（[[26-lab-drills]]）是唯一要你動手的一份：20 個實驗，每個都先把東西弄壞，讓你在自己的 minikube 上看見症狀、自己診斷，再展開答案。本書從第一頁就在說「親手把它弄壞一次，比讀十遍都有效」——那份手冊就是把這句話兌現。**建議的用法是每讀完一組章節，就去做對應的實驗**，而不是全部讀完才開始動手。

附錄 E 到 I 則是**當你開始為一座叢集負責之後**才會頻繁翻開的五份：[[27-upgrades-and-deprecations]]（每年至少用兩次的升級與棄用對照）、[[28-ingress-nginx-annotations]]（Ingress 真正的能力所在）、[[29-status-and-conditions]]（讀懂 `kubectl get -o yaml` 的下半截）、[[30-production-readiness]]（上線檢查、容量、告警、事故流程）、[[31-glossary]]（約 140 條術語，忘記某個名詞在哪一章時從這裡回去）。

## 這套教材的獨特之處

第 13 章的案例庫收錄了 **19 個來自實際環境的踩坑紀錄**——Harbor robot account 名稱含 `$` 被 shell 展開、Cloudflare Tunnel 的 1016 錯誤與 100MB 上傳上限、WSL2 記憶體吃滿、CI 用全域 `sed` 改 tag 導致多服務互蓋、ArgoCD hard refresh 的時機。這些不是教科書上找得到的東西，而是真的在這套環境上出過事、查過、修好的紀錄，並且散布在各章對應的機制說明裡。

## 連結

- [[kubernetes]] — K8s entity 頁，速查用
- [[docker]] — Docker entity 頁
- [[kubectl]] — CLI 指令速查
- [[helm]] — Helm 打包工具
- [[argocd]] — GitOps 部署控制器
- [[minikube]] — 本機練習環境
- [[cicd-pipeline]] — CI/CD 完整流程
- [[devops-moc]] — DevOps 主題入口
