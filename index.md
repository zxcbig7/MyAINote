# Wiki Index

> 本檔列出 `wiki/` 內所有頁面。回答問題時**先查此檔找線索**。
> 每次 ingest / synthesis 後即時更新。

## Tech / MOC（主題入口）

- [[devops-moc]] — Docker / K8s / Helm / Argo / Vault / CI-CD
- [[web-frontend-moc]] — React / TypeScript / CSS / UI/UX
- [[web-backend-moc]] — .NET Web API / C# / Auth
- [[database-moc]] — Oracle / SQL / PL-SQL
- [[languages-moc]] — C# / TypeScript / Python / VBA
- [[tools-system-moc]] — Git / Linux / Networking / 開發工具
- [[modeling-moc]] — 數學規劃建模方法論（García Sánchez + Williams）+ 29 個經典案例庫

## Tech / Entities

- [[argocd]] — GitOps 部署控制器，監控 git repo 並 sync 到 K8s 叢集
- [[raw/devops/Docker/Docker]] — 容器化平台，Image / Container / Repository 核心概念 + Compose
- [[kubernetes]] — 容器編排平台，Pod/Node/Cluster 四元件 + YAML 架構
- [[istio]] — Service mesh，Sidecar 注入、流量攔截、xDS、啟動 race condition 與偵錯
- [[minikube]] — 本機單節點 K8s 開發環境
- [[helm]] — K8s 應用部署打包工具，Chart / Release / values.yaml
- [[kubectl]] — K8s CLI 工具，get/apply/describe/logs/exec 常用指令速查
- [[raw/devops/Vault]] — HashiCorp Secret 管理，K8s 整合、Unseal 流程
- [[raw/Web Framework/TypeScript]] — 型別系統、Interface vs Type、泛型、Utility Types
- [[wiki/tech/entities/react]] — React Hooks 完整說明（useState/useEffect/useCallback/useRef/useContext）+ Zustand
- [[dotnet-web-api]] — ASP.NET Core Web API 架構、Controller、DI、Middleware、JWT
- [[aspnetcore-webapi-complete]] — ASP.NET Core Minimal API 完整教學：路由、參數綁定、Middleware、DI、Health Check、快取等 18 章
- [[csharp]] — C# 語法重點、OOP、LINQ、async/await
- [[msbuild]] — MSBuild 與 .csproj：兩大積木（PropertyGroup/ItemGroup）、三動詞、CopyToOutputDirectory、Target、Directory.Build.props
- [[git]] — Git 四種物件、常用指令、日常開發 SOP、Branch 策略
- [[oracle]] — Oracle SQL 基本指令、CMD 操作、C# 連接方式
- [[linux]] — Linux 目錄結構、權限、常用指令、Ubuntu 設定
- [[claude-code-skills]] — Claude Code 自訂 slash command，Skills 定義方式、檔案格式與適用時機
- [[python]] — Python 基礎（stub，待整合 raw 內容）

## Tech / Concepts

- [[cicd-pipeline]] — GitLab/Azure DevOps + Harbor + Helm + ArgoCD 完整 CI/CD 流程
- [[domain-networking]] — DNS 概念、Record 類型、Cloudflare、TLS Binding

### K8s Mastery 教材（詳見 [[k8s-mastery]]）

涵蓋 Docker → K8s → Helm/ArgoCD → Prometheus/ELK 完整交付鏈的 16 章教材 + 2 附錄，約 143,700 字、60 張圖。**全數完成並通過驗收**。

- [[k8s-mastery]] — 總目錄、進度表與七天學習路徑
- [[00-docker-foundations]] — 容器三大 Linux 基石（namespace/cgroup/OverlayFS）、image layer、Dockerfile 逐指令、多階段建置、dockershim 真相
- [[02-cluster-internals]] — Control Plane/Node 元件、`kubectl apply` 完整旅程、Reconciliation Loop 與 pull-based 心智模型
- [[04-workloads]] — Pod 剖析與多容器模式、三種 Probe 誤設災難、優雅關閉與 preStop、Deployment 滾動更新推演、StatefulSet 三保證、Job/CronJob
- [[05-networking]] — 網路四鐵律、Service 選擇鏈與 kube-proxy、DNS 與 ndots 陷阱、Ingress/TLS、NetworkPolicy、完整封包路徑
- [[06-config-and-storage]] — ConfigMap env vs volume 更新差異、Secret 非加密真相、PV/PVC/StorageClass 三層、Vault + ESO
- [[07-scheduling-and-resources]] — Scheduler 決策、requests/limits 真義、CPU throttle vs Memory OOMKill、QoS 與驅逐、Taint/Affinity、三種 Autoscaler
- [[08-security-and-rbac]] — Authentication/Authorization/Admission 三道關卡、RBAC 四物件配對與純白名單本質、ServiceAccount token 演進、Pod Security Admission、Vault 信任鏈、ArgoCD AppProject 權限邊界
- [[09-extending-kubernetes]] — Admission webhook（為什麼 YAML 被改了）、CRD/Operator、Finalizer（namespace 卡 Terminating）、OwnerReference 與 GC
- [[10-helm]] — Chart 結構、`include` vs `template`、`nindent`、values 覆蓋優先序、Hooks、除錯三件套
- [[11-argocd]] — GitOps pull 模型、Application 解剖、Sync 與 Health 獨立性、Sync Waves、OutOfSync 診斷、ApplicationSet、AppProject 邊界
- [[13-troubleshooting]] — 分層定位方法論、Pod 狀態機、網路排查流程、19 個真實踩坑案例庫
- [[14-prometheus-grafana]] — pull 模型、四種 metric type、PromQL 深入（rate/irate/histogram_quantile）、Alertmanager、USE/RED、Grafana
- [[15-elk-elastic]] — 容器日誌收集路徑、倒排索引、shard/mapping、`text` vs `keyword`、KQL 與 Query DSL、Logstash/Filebeat、ILM、ELK vs Loki
- [[16-self-assessment]] — 附錄 A：144 題自我檢測題庫，三級難度＋18 條紅色警戒清單
- [[17-cheatsheet]] — 附錄 B：速查表，緊急排錯十連發、17 種 YAML 骨架、kubectl/Helm/ArgoCD/PromQL/KQL 速查

### 建模與最佳化 Modeling（詳見 [[modeling-moc]]）

- [[mp-model-fundamentals]] — 建模為什麼需要方法論而非經驗、古典四元件如何擴充為五元件、決策活動與計算的判準差異
- [[system-elements]] — 如何從系統描述中識別出元素、判斷資料的 own/shared 與 primary element、individual 對 collective 的量化性質判斷
- [[decision-activities]] — 決策活動如何從系統動詞與參與元素中系統化推導出來，以及為何「有計算值的動作」不該被誤定義成決策變數
- [[system-calculations]] — 三種計算變數（auxiliary/logical/bound）怎麼定義，以及為何決策變數與計算變數的角色必須徹底分開
- [[specification-types]] — 規格(specification)為何不等於限制式(constraint)，五種語意分類加上如何揪出隱含規格
- [[logical-specifications-guide]] — 用 big-M 開關技巧把 NOT/OR/AND/IF-THEN/IFF 等邏輯運算子轉成線性限制式
- [[quantitative-nature-of-elements]] — 元素的「數量性質」是建模者的選擇而非題目給定，教你判斷何時該拆開、何時該合併
- [[gs-worked-examples]] — 六個由淺入深的完整案例，把前七章方法論一次串起來實戰演練
- [[mathematical-programming-overview]] — 模型是什麼、為什麼要建模、LP/NLP/IP/stochastic programming 模型分類
- [[building-lp-models]] — 線性為什麼讓 LP 好解、目標函數五種類型與限制式十一種類型完整分類、好模型三要素
- [[structured-lp-models]] — 大型 LP 如何由多工廠/多產品/多期小模型組合出 block angular 結構，以及 Dantzig-Wolfe decomposition
- [[lp-applications-and-networks]] — LP 在各產業的應用地圖、input-output 經濟模型，以及七種網路模型
- [[interpreting-lp-solutions]] — dual model、shadow price、reduced cost 的經濟意義，以及 alternative optima/degeneracy 陷阱
- [[nonlinear-and-separable-programming]] — convex/non-convex 決定局部解是否等於全域解，separable programming 分段線性近似
- [[integer-programming-fundamentals]] — IP 何時該用、四類求解法概觀，指示變數、命題邏輯轉限制式、SOS1/SOS2 建模工具箱
- [[special-integer-programming-structures]] — set covering/packing/partitioning、knapsack、TSP、VRP、QAP、column generation
- [[integer-programming-refinement]] — IP formulation 好壞對比（symmetry、big-M、bounds tightening）、facet 化簡
- [[mp-implementation-in-practice]] — MP 模型從算出答案到被組織採用要跨過哪些坎：決策者參與、集中化 vs 去中心化、資料維護
- [[case-food-manufacture-1]] — 六個月原油調配存貨問題，示範單期 LP 擴充成多期模型，正確線性化品質區間限制
- [[case-food-manufacture-2]] — 延續案例1，加入三條邏輯規則，示範 0-1 指示變數與 semi-continuous variable
- [[case-factory-planning-1]] — 七產品四製程多期生產排程，示範 product mix 問題與 shadow price 在擴產決策的應用
- [[case-factory-planning-2]] — 把維修時程從已知變成模型決策，示範整數變數如何避免對稱解爆炸
- [[case-manpower-planning]] — 三種技能人力逐年演變，示範「最小化資遣」vs「最小化成本」兩種目標函數的代價差異
- [[case-refinery-optimisation]] — 蒸餾/重組/裂解/調和四道工序串成一張 LP，示範 structured multi-stage 製程模型
- [[case-mining]] — 五年四礦選三運作，示範用兩組 0-1 變數分別表達「當期運作」與「永久關閉」
- [[case-farm-planning]] — 牛群依年齡拆世代鏈、作物多期存量流動，示範貸款年金折現避免模型過度舉債
- [[case-economic-planning]] — 動態 Leontief 三產業經濟模型，三種目標函數導出三種成長路徑
- [[case-decentralisation]] — 二次指派問題(QAP)真實案例，示範 0-1 乘積變數線性化二次目標函數
- [[case-curve-fitting]] — 用 LP 做曲線擬合，示範 goal programming 偏差變數與 minimax 轉線性目標
- [[case-logical-design]] — 用最少 NOR 邏輯閘組出指定真值表，示範命題邏輯真值表轉 0-1 限制式
- [[case-market-sharing]] — 23 家零售商依七指標分配市場，示範 goal programming 在 0-1 指派問題求解異常困難的教訓
- [[case-opencast-mining]] — 露天採礦區塊前置關係約束，約束矩陣全單模，LP relaxation 自動得整數解
- [[case-tariff-rates]] — 電力機組排程 MIP，示範整數解沒有真正 shadow price 時如何折衷估算邊際電價
- [[case-hydro-power]] — 在火力機組排程骨架上疊加水庫水位變數，示範跨時段庫存平衡取代動態規劃
- [[case-3d-noughts-and-crosses]] — 3×3×3 立體井字遊戲組合最小化，示範單向邏輯+目標函數方向讓求解器自己補完限制式
- [[case-optimising-a-constraint]] — 把一條 0-1 限制式本身當成待簡化對象，用邏輯等價找出最乾淨寫法
- [[case-distribution-1]] — 工廠+轉運站+客戶配送網路，示範 transhipment 建模與同骨架換目標函數處理多目標
- [[case-depot-location]] — 在配送網路上疊加 0-1 選址開關，示範 fixed charge 問題在網路節點層級的應用
- [[case-agricultural-pricing]] — 政府牛奶/奶油/起司定價，價格彈性線性化到 separable programming 全流程
- [[case-efficiency-analysis]] — 28 間展示中心 DEA 效率評估，把比率型目標轉成可解 LP
- [[case-milk-collection]] — 兩天路線容量限制 TSP/VRP，示範子巡迴消除按需追加求解
- [[case-yield-management]] — 三期航空票價多階段隨機規劃，情境樹取代連續需求曲線
- [[case-car-rental-1]] — 四城市租車調度，把車隊流動建模成循環網路流，示範「現實整數」不代表「模型必須整數」
- [[case-car-rental-2]] — 從既有 LP 敏感度分析長出投資決策，示範 precedence 與 cardinality 邏輯限制式疊加在網路流上
- [[case-lost-baggage-distribution]] — TSP 改造成不繞回原點的 Hamiltonian path，示範子迴路消去延遲生成
- [[case-protein-folding]] — 蛋白質摺疊翻譯成配對+恰好一次轉折的 0-1 邏輯限制式
- [[case-protein-comparison]] — contact map 最大公共子圖比對，最優值本身就是相似度的答案

## Tech / Summaries

- [[argocd-tutorial-summary]] — 既有 ArgoCD 教學筆記摘要

## Personal / Entities

（尚無頁面）

## Personal / Concepts

（尚無頁面）

## Personal / Summaries

（尚無頁面）

## Synthesis

（尚無頁面）

---

## Raw Sources（速查）

✓ = 已 ingested 並建立 wiki 頁

### Tech / DevOps

- `raw/tech/devops/Docker/Docker/Docker.md` ✓ → [[raw/devops/Docker/Docker]]
- `raw/tech/devops/Docker/Docker Compose/Docker Compose.md` ✓ → [[raw/devops/Docker/Docker]]
- `raw/tech/devops/Docker/Docker 部屬範例/Docker 部屬範例.md` ✓ → [[raw/devops/Docker/Docker]]
- ~~`raw/tech/devops/Docker/Docker Compose yaml 架構.md`~~ → 已整合
- ~~`raw/tech/devops/Docker/Docker Compose 重開.md`~~ → 已整合
- `raw/tech/devops/Kubernetes (K8s)/Kubernetes (K8s).md` ✓ → [[kubernetes]]
- `raw/tech/devops/K8s YAML 概念與架構/K8s YAML 概念與架構.md` ✓ → [[kubernetes]]
- `raw/tech/devops/Minikube 介紹/Minikube 介紹.md` ✓ → [[minikube]]
- `raw/tech/devops/Helm Chart/Helm Chart.md` ✓ → [[helm]]
- `raw/tech/devops/kubectl 指令/kubectl 指令.md` ✓ → [[kubectl]]
- `raw/tech/devops/Vault/Vault.md` ✓ → [[raw/devops/Vault]]
- `raw/tech/devops/Azure Pipeline/Azure Pipeline.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/部署筆記/部署筆記.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/部屬後端/部屬後端.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/argocd-tutorial/argocd-tutorial.md` ✓ → [[argocd]]
- `raw/tech/devops/azure-pipelines/azure-pipelines.md`
- `raw/tech/devops/complete-tutorial/complete-tutorial.md`
- `raw/tech/devops/harbor-tutorial/harbor-tutorial.md`
- `raw/tech/devops/helm-tutorial/helm-tutorial.md`
- `raw/tech/devops/k8s-rbac/k8s-rbac.md`
- `raw/tech/devops/kubectl-api-version/kubectl-api-version.md`
- `raw/tech/devops/minikube-tutorial/minikube-tutorial.md`
- `raw/tech/devops/postgresql-k8s/postgresql-k8s.md`
- `raw/tech/devops/vault-tutorial/vault-tutorial.md`
- `raw/tech/devops/troubleshooting/troubleshooting.md`

### Tech / Web Dev

- `raw/tech/web-dev/TypeScript/TypeScript.md` ✓ → [[raw/Web Framework/TypeScript]]
- `raw/tech/web-dev/React/React.md` ✓ → [[wiki/tech/entities/react]]
- `raw/tech/web-dev/React/React + TypeScript 開發手冊.md` ✓ → [[wiki/tech/entities/react]], [[raw/Web Framework/TypeScript]]
- `raw/tech/web-dev/NET Web API/NET Web API.md` ✓ → [[dotnet-web-api]]
- `raw/tech/web-dev/HTML/HTML.md`
- `raw/tech/web-dev/CSS/CSS.md`
- `raw/tech/web-dev/react-hooks-gotchas/react-hooks-gotchas.md`
- `raw/tech/web-dev/uiux-notes/uiux-notes.md`

### Tech / Languages

- `raw/Languages/languages/Typescript/typescript-web-research.md` ✓ → [[raw/Web Framework/TypeScript]]（由淺至深完整語法，含進階型別操作）
- `raw/Languages/languages/C#/C#.md` ✓ → [[csharp]]
- `raw/Languages/languages/csharp-debug-test/csharp-debug-test.md`

### Tech / Database

- `raw/tech/database/SQL 資料庫基本指令/SQL 資料庫基本指令.md` ✓ → [[oracle]]
- `raw/tech/database/Oracle CMD 指令筆記/Oracle CMD 指令筆記.md` ✓ → [[oracle]]
- `raw/tech/database/Oracle To C#/Oracle To C#.md` ✓ → [[oracle]]
- `raw/tech/database/SQL 建立資料表/SQL 建立資料表.md`
- `raw/tech/database/SQL Basic Functions/SQL Basic Functions.md`
- `raw/tech/database/SQL 指令語法速查/SQL 指令語法速查.md`
- `raw/tech/database/Oracle Server操作/Oracle Server操作.md`
- `raw/tech/database/PL SQL/PL SQL.md`
- `raw/tech/database/Procedure & Function/Procedure & Function.md`

### Tech / Git

- `raw/tech/git/Git 指令筆記/Git 指令筆記.md` ✓ → [[git]]
- `raw/tech/git/Git 每日開發 SOP/Git 每日開發 SOP.md` ✓ → [[git]]
- `raw/tech/git/Github 心得/Github 心得.md` ✓ → [[git]]
- `raw/tech/git/SourseTree(Local) 筆記/SourseTree(Local) 筆記.md`
- `raw/tech/git/git-tutorial/git-tutorial.md`

### Tech / System

- `raw/tech/system/Linux 觀念/Linux 觀念.md` ✓ → [[linux]]
- `raw/tech/system/Ubuntu 筆記/Ubuntu 筆記.md` ✓ → [[linux]]
- `raw/tech/system/xrdp 設定/xrdp 設定.md`
- `raw/tech/system/網路設定/網路設定.md`

### Tech / Networking

- `raw/tech/networking/網域小知識/網域小知識.md` ✓ → [[domain-networking]]
- `raw/tech/networking/google-oauth-tutorial/google-oauth-tutorial.md`

### Tech / Tools

- `raw/tech/tools/Visual Studio Code/Visual Studio Code.md`
- `raw/tech/tools/LaTex/LaTex.md`
- `raw/tech/tools/VBA/VBA.md`
- `raw/tech/tools/markdown哲學/markdown哲學.md`

### Tech / Simulation

- `raw/tech/simulation/NetLogo/NetLogo.md`
- `raw/tech/simulation/Flexsim/Flexsim.md`
- `raw/tech/simulation/Game Notes (Godot)/Game Notes (Godot).md`

### Tech / Optimization

- `raw/tech/optimization/GLPK/GLPK.md`
- `raw/tech/optimization/AMPL/AMPL.md`

### Tech / Modeling

- `raw/Modeling/(Book)Modelling in Mathematical Programming.pdf` ✓ → [[modeling-moc]]（書1，García Sánchez 方法論全書 8 章）
- `raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf` ✓ → [[modeling-moc]]（書2，Williams Part I 方法論 11 章 + Part II/III/IV 全部 29 個經典案例）
