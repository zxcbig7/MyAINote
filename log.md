# Wiki Log

> Append-only。每筆格式：`## [YYYY-MM-DD] <action> | <subject>`
> action 類型：`bootstrap`、`ingest`、`query`、`synthesis`、`lint`、`refactor`

## [2026-07-29] ingest | 建模資料庫（García Sánchez + Williams 兩本書）

- 來源：`raw/Modeling/(Book)Modelling in Mathematical Programming.pdf`（José Manuel García Sánchez，方法論全書 8 章）、`raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf`（H. Paul Williams，Part I 方法論 11 章 + Part II/III/IV 全部 29 個經典案例）
- 產出：新建 `wiki/tech/moc/modeling/modeling-moc.md` 入口，加上 47 個 `wiki/tech/concepts/` 頁面（8 個書1方法論 + 10 個書2方法論 + 29 個經典案例），全部依 kebab-case 同名資料夾規範建立，frontmatter 含 sources/created/updated，內文書本式散文並互相 wikilink
- 用途：建一個完整的數學規劃建模知識庫，給未來想學建模的人系統化參考——先讀方法論建立思考框架，再讀案例庫看經典題型怎麼實際建模
- 過程備註：因一次派出 16 個背景 subagent 平行處理，撞到並發上限被系統砍掉 9 個（各自留下部分進度），之後分兩批（5+3）重新派工補齊缺漏檔案，最終 47 個頁面全數到位
- 已更新 `index.md`（新增 MOC 入口、47 個頁面條目、2 筆 raw source）

## [2026-05-09] refactor | raw/ 相關資源整合至同主題資料夾

- 刪除孤立頂層資料夾：`ASP Web API/`（→ `tech/web-dev/NET Web API/`）、`DevOps/`（空）、`assets/`（空）
- devops 同主題整合：`K8s YAML`、`k8s-rbac`、`kubectl`、`postgresql-k8s` → `Kubernetes (K8s)/`；`helm-tutorial` → `Helm Chart/`；`vault-tutorial` → `Vault/`；`minikube-tutorial` → `Minikube/`；`azure-pipelines` → `Azure Pipeline/`
- web-dev 整合：`react-hooks-gotchas` → `React/`
- Languages 整合：`Typescript/typescript-web-research.md` → `tech/web-dev/TypeScript/`；`csharp-debug-test/` → `Languages/C#/`
- 更新 CLAUDE.md 圖片規範：改為 `assets/` 子資料夾 + 相對路徑

## [2026-05-09] refactor | 統一資料夾結構（文章 + 圖片同層）

- 動機：raw/ 文章與圖片分離（`Article.md` 在外層，`Article/images` 在同名子資料夾），搬移文章後圖片路徑失效
- 結果：raw/ 和 wiki/ 所有文章改為「同名資料夾 + .md 與圖片同層」格式
- 移動 raw/ 約 90+ 篇文章、wiki/ 19 個頁面
- 更新 25 個有圖片文章的 `![alt](FolderName/img)` → `![alt](img)` 相對路徑
- dotnet-web-api 圖片從 `raw/assets/aspnet-web-api/` 移至 `wiki/tech/entities/dotnet-web-api/`
- 更新 CLAUDE.md 資料夾結構圖、index.md 全部 raw source 路徑

## [2026-05-03] bootstrap | 第二大腦初始化

- 建立三層架構：`raw/`、`wiki/`、`CLAUDE.md`
- 既有 17 篇技術筆記移至 `raw/tech/legacy-notes/`，視為已 ingested source
- 寫入 schema、index、log 三個骨架檔案
- 保留 `.obsidian/` vault 設定不動

## [2026-05-03] ingest | argocd-tutorial.md

- 來源：`raw/tech/legacy-notes/argocd-tutorial.md`
- 產出：
  - `wiki/tech/summaries/argocd-tutorial-summary.md`
  - `wiki/tech/entities/argocd.md`
- 用途：示範第一個 ingest workflow，建立 ArgoCD 概念錨點

## [2026-05-03] refactor | raw 重複內容清理

- kubectl-api-version.md → 合入 kubectl 指令.md（troubleshooting 章節）
- git-tutorial.md → 合入 Git 指令筆記.md（Merge Conflict + 修改歷史章節）
- Helm Chart.md → 合入 helm-tutorial.md（完整目錄結構）
- Minikube 介紹.md → 合入 minikube-tutorial.md（Driver 比較表）
- Vault.md → 內容已在 vault-tutorial.md，標記待刪

## [2026-05-03] refactor | Docker raw 整合

- Docker.md + Docker 觀念.md + 子頁（容器、資料管理、Dockerfile）→ 單一 Docker.md
- Docker Compose yaml 架構.md + Docker Compose 重開.md → Docker Compose.md
- Docker 部屬範例.md 保持獨立（.NET 部署流程完整）

## [2026-05-07] ingest | Istio IPv6 Dual-Stack Troubleshooting

- 來源：GitHub issues #45970、#41462、#48358、#34314
- 產出：`wiki/tech/entities/istio.md` 新增 `Troubleshooting：IPv6 / Dual-Stack` 章節
- 涵蓋：`[::]` port mismatch 根因、ISTIO_DUAL_STACK workaround、多副本 probe 失敗、四個參考 issue URL

## [2026-05-07] ingest | Istio Sidecar 完整生命週期

- 來源：對話整理（web 補充）
- 產出：`wiki/tech/entities/istio.md`
- 涵蓋：iptables 流量攔截、race condition、holdApplicationUntilProxyStarts、K8s 1.28 native sidecar、Job 終止問題、pilot-agent wait 失敗根因、NetworkPolicy 相容性、xDS、偵錯方法論

## [2026-05-03] ingest | Notion notes 批次整合

- 來源：`Notion notes/Dev/` 下 27 個主題檔（4 批次）
- 產出：15 個 wiki 頁面
  - entities（14）：docker、kubernetes、minikube、helm、kubectl、vault、typescript、react、dotnet-web-api、csharp、git、oracle、linux
  - concepts（2）：cicd-pipeline、domain-networking
- 涵蓋：Docker、K8s、Minikube、Helm、kubectl、Vault、TypeScript、React、.NET Web API、C#、Git、Oracle、Linux、CI/CD Pipeline、Domain/Networking
- 同步建立 `wiki/tech/concepts/` 目錄

## [2026-05-09] ingest | Claude Code Skills 系統

- 來源：對話整理（/write-tutorial 觸發，主題：Skills 是哪裡來的）
- 產出：`wiki/tech/entities/claude-code-skills.md`
- 涵蓋：Skills 存放路徑、Markdown 格式、呼叫方式、與 Memory/Hooks 的差異、適用時機

## [2026-05-09] ingest | TypeScript 由淺至深語法教學（web research）

- 來源：typescriptlang.org handbook、freecodecamp、TypeScript 官方文件（generics、utility-types、conditional-types）
- 產出：
  - `raw/Languages/languages/Typescript/typescript-web-research.md`（新建）
  - `wiki/tech/entities/typescript.md`（大幅擴充：Class、Enum、Narrowing 進階、Generic Constraint、Utility Types 完整、Conditional Types、Mapped Types、Template Literal Types、keyof/typeof/Indexed Access、Satisfies、tsconfig）
- 下載圖片：0 張（官方文件以文字為主）

## [2026-05-09] ingest | ASP.NET Core Web API（web research）

- 來源：Microsoft Learn（middleware、routing、filters、architecture 各頁）
- 產出：
  - `raw/ASP Web API/aspnet-web-api-web-research.md`（新建）
  - `wiki/tech/entities/dotnet-web-api.md`（補充 Routing、Filters、Architecture、Middleware 圖示）
- 下載圖片（3 張）：`raw/assets/aspnet-web-api/`
  - `middleware-pipeline.png`
  - `clean-architecture-onion.png`
  - `clean-architecture-aspnetcore.png`

## [2026-07-17] synthesis | MSBuild 與 .csproj 功能性寫法總覽

- 來源：對話中學到的 csproj 知識（無 raw 來源檔）
- 產出：`wiki/tech/entities/msbuild/msbuild.md`（新建 entity 頁）
- 涵蓋：PropertyGroup vs ItemGroup 兩大積木、Include/Remove/Update 三動詞（含 NETSDK1022 排查）、常用 item 型別、CopyToOutputDirectory 三值與資料隨 build 複製到 bin 的機制、Condition、Target 生命週期 hook、$()/@()/%() 變數語法、Directory.Build.props 跨專案共用
- cross-link：[[dotnet-web-api]]、[[csharp]]

## [2026-07-31] synthesis | K8s Mastery 教材（關鍵四章）

- 動機：使用者準備成為公司 K8s 管理員，目標「寫 YAML 管理、分析 ArgoCD、解決同事部署問題」，要求專業到問不倒
- 規劃 13 章教材大綱（基礎/資源/治理/交付/維運五篇），先產出最能拉開專業度的關鍵四章驗證風格
- 產出：`wiki/tech/concepts/k8s-mastery/` 下 `k8s-mastery.md`（總目錄+一週學習路徑）、`02-cluster-internals`、`07-scheduling-and-resources`、`09-extending-kubernetes`、`13-troubleshooting`
- 來源整合：既有 K8s/Helm/ArgoCD/minikube raw 筆記，並將 `raw/devops/troubleshooting/troubleshooting.md` 的 19 個真實踩坑（Harbor robot account $ 展開、Cloudflare 1016、WSL2 記憶體、ArgoCD hard refresh 等）全數吸收進第 13 章方法論與案例庫
- 待辦：其餘九章（0/2/3/4/5/7/9/10/11）依此四章風格續寫

## [2026-08-01] synthesis | 雲原生部署體系教材擴充（12/16 章）

- 範圍從 K8s 擴大到 Docker / Helm / ArgoCD / Prometheus+Grafana / ELK 完整交付鏈，重規劃為 16 章
- 本輪新增 8 章：`00-docker-foundations`(10,004字)、`04-workloads`(11,801)、`05-networking`(10,813)、`06-config-and-storage`(9,445)、`10-helm`(7,017)、`11-argocd`(7,733)、`14-prometheus-grafana`(9,151)、`15-elk-elastic`(11,067)
- 累計 12 章、約 104,000 字、45 張 Mermaid 圖，全數落在 `wiki/tech/concepts/k8s-mastery/`
- 使用者實務踩坑持續吸收：Harbor robot account $ 展開、Cloudflare 1016 與 100MB 上限、Bitnami PostgreSQL PVC 密碼不更新、TLS secret 缺失致 nginx CrashLoop、ArgoCD AppProject sourceNamespaces
- 待補：`01-why-kubernetes`、`03-api-and-yaml`、`08-security-and-rbac`、`12-cluster-operations`（第 8 章兩度遇 API session limit 中斷）

## [2026-08-01] synthesis | 第八章：安全與權限（08-security-and-rbac，第三次嘗試完成）

- 產出：`wiki/tech/concepts/k8s-mastery/08-security-and-rbac/08-security-and-rbac.md`，約 12,500 字、4 張 Mermaid 圖
- 骨架：Authentication／Authorization／Admission 三道關卡（呼應第二章 apply 旅程），全章沿此展開
- 核心內容：K8s 不存 User 物件、憑證 CN/O 對應身份、x509 無 revocation list 的外洩風險；ServiceAccount 1.24 前後長期 Secret token 到短期 projected token 的演進；RBAC 四物件配對矩陣（點出 `Role`+`ClusterRoleBinding` 不合法、`ClusterRole`+`RoleBinding` 最省事卻常被忽略）、純白名單無 deny、權限提升防護、aggregated ClusterRole；三組可直接套用的 RBAC 範例（唯讀開發者／CI 部署 SA／只能重啟 Deployment 的 SRE）；Pod Security Admission 三等級三模式；SecurityContext 加固逐項回扣第零章 kernel 機制；Vault/ESO 信任鏈（TokenReview 驗證角度重寫，與第六章互補而非重複）；供應鏈安全（Trivy、digest 釘選、Harbor robot account）；NetworkPolicy 作為第二維度安全邊界；Audit Policy 四級／kube-bench／憑證到期監控；ArgoCD 雙層授權模型（K8s RBAC 管 ArgoCD 自身 SA vs `policy.csv` 管人類使用者）與 `sourceNamespaces` 踩坑三步修法
- 來源整合：`raw/devops/Kubernetes (K8s)/k8s-rbac/k8s-rbac.md`、`raw/devops/Vault/Vault.md`、`raw/devops/argocd-tutorial/argocd-tutorial.md`，並與既有 `02-cluster-internals`、`06-config-and-storage`、`09-extending-kubernetes`、`11-argocd`、`13-troubleshooting` 交叉呼應避免重複
- 累計 13/16 章、約 116,500 字、49 張 Mermaid 圖
- 過程備註：初稿因偶發使用半形逗號、冒號、括號與一處簡體字（風險、權限），寫完後用腳本化掃描（保護 code fence 與 inline code span）批次修正為全形標點，並將 PowerShell 重寫過程中誤入的 CRLF 換行統一轉回 LF
- 待補：`01-why-kubernetes`、`03-api-and-yaml`、`12-cluster-operations`

## [2026-08-01] synthesis | 雲原生部署體系教材完成（16/16 章）

- 補齊最後四章：`01-why-kubernetes`(7,277字)、`03-api-and-yaml`(10,580)、`08-security-and-rbac`(12,493)、`12-cluster-operations`(9,267)
- 全書 16 章、約 143,700 中文字、60 張 Mermaid 圖，路徑 `wiki/tech/concepts/k8s-mastery/`
- 全書驗收（fresh-context verifier，V1-V8 八項）：124 個 wikilink 零失效、150+ 處「第 N 章」交叉引用零錯誤、118 個 YAML 區塊無縮排壓平、無 BOM/CRLF/簡體字、H1 唯一且 H2 無編號
- 驗收後修正：總目錄進度表同步為 16/16、7 處中文語境半形標點（15-elk 六處冒號、09-extending 一處括號），修正後全書標點殘留 0
- 教材涵蓋完整交付鏈：容器(Docker) → 編排(K8s 十章) → 打包交付(Helm/ArgoCD) → 可觀測性(Prometheus/Grafana、ELK)

## [2026-08-01] synthesis | 教材附錄完成，全案交付

- 附錄 A `16-self-assessment`：144 題自我檢測題庫（🟢44.4%／🔵36.8%／🔴18.8%，情境診斷題 29.9%），每題含 details 摺疊答案與章節 wikilink，另附 18 條紅色警戒清單
- 附錄 B `17-cheatsheet`：1,348 行速查表，15 區塊含緊急排錯十連發、Pod 狀態速查、17 種 YAML 骨架（21 區塊全通過 PyYAML 驗證）、kubectl/Docker/Helm/ArgoCD/PromQL/KQL/維運指令速查
- 題庫獨立驗收：抽驗 20 題（8 題專家級＋6 題情境診斷＋6 題分散章節）對照教材原文，20/20 正確；結構檢查與警戒清單逐條核對全數 PASS
- 全案交付：16 章教材（143,700 字、60 圖）＋ 2 附錄，index.md 與總目錄同步完成

## [2026-08-07] synthesis | 執行時資料目錄的雙向資料流

- 新增 `wiki/tech/concepts/runtime-data-directory-flow/`：補齊 [[msbuild]] 只講單向複製（原始碼樹 → bin）的缺口，主題是程式在執行期回寫輸出目錄形成的反向流
- 核心內容：`AppDomain.BaseDirectory` 為何讓程式只看得到輸出目錄；`PreserveNewest` 以時間戳仲裁，導致程式回寫過一次後分岔永久保留；產物指紋（UTF-8 BOM／CRLF／欄名大寫）與 `git ls-files`／`git check-ignore` 判斷 source；三種複製策略對應「誰有話語權」；回收 SOP 與三段式排查
- 來源：對 OptimFoundation（CPLEX 建模框架）匯入流程的 codebase 分析，具體元件對照收在最後一節

## [2026-08-14] synthesis | K8s YAML 欄位百科（附錄 C，四份）

- 新增 `18-yaml-fields-pod` / `19-yaml-fields-workloads` / `20-yaml-fields-network-storage` / `21-yaml-fields-cluster-security`，共 2,006 行、約 21,400 字，基準 **K8s v1.33**
- 動機：既有 16 章教材回答「為什麼這樣寫」，速查表給骨架，但缺一份「有哪些欄位、預設值是什麼」的逐欄位參考。抽驗 37 個欄位確認 `hostAliases`、`subPathExpr`、`ipFamilyPolicy`、`runtimeClassName`、`ephemeralContainers`、`matchLabelKeys`、`resourceFieldRef`、HPA `behavior` 等在全書零出現
- 每份含常見誤設對照表（C-1/C-2/C-3 各十連），C-4 收尾附「上線前通用檢查清單」四大項；開篇教 `kubectl explain --recursive` / `--dry-run=server` 自查法，避免欄位知識隨版本過期
- bookkeeping：修正 index.md 舊有 drift（`01-why-kubernetes`、`03-api-and-yaml`、`12-cluster-operations` 三章從未被列入），並同步總目錄進度表為 16 章 + 6 附錄

## [2026-08-14] synthesis | 附錄 C 補完（C-5 生態系 CRD、C-6 冷門內建與元件設定檔）

- 自我稽核發現 C-1~C-4 只涵蓋內建 API，缺兩塊：實務天天用的第三方 CRD、以及各元件自己的設定檔
- 新增 `22-yaml-fields-ecosystem`：ArgoCD Application/AppProject/ApplicationSet（含 syncOptions、sync-wave/hook annotation、8 種 generator）、Helm Chart.yaml 與模板函式、Prometheus Operator ServiceMonitor/PodMonitor/PrometheusRule、cert-manager Issuer/Certificate、External Secrets SecretStore/ExternalSecret、VPA、Gateway API 完整（GatewayClass/Gateway/HTTPRoute/ReferenceGrant）、kustomization.yaml
- 新增 `23-yaml-fields-rare-builtins`：遺留 kind（Endpoints/RC/ComponentStatus）、Event/Lease、CSI 四物件與快照、CSR/ClusterTrustBundle、APIService、FlowSchema/PriorityLevelConfiguration、ServiceCIDR、DRA 四物件、AdmissionPolicyBinding；後半是元件設定檔 kubeadm v1beta4 / KubeletConfiguration / KubeProxyConfiguration / KubeSchedulerConfiguration / EncryptionConfiguration / Audit Policy / kubeconfig
- C-6 結尾明列「仍未逐欄位收錄」四項（status 子物件、Windows 專屬、alpha 欄位、controller 專屬 annotation）並說明理由，避免日後誤以為已全覆蓋
- 附錄 C 累計六份、3,220 行；驗收：84/84 YAML 區塊通過 PyYAML 解析、無 BOM/CRLF、wikilink 全數解析成功。總目錄與 index.md 同步為 16 章 + 8 附錄

## [2026-08-14] synthesis | 附錄 C-7/C-8 與附錄 D 實驗手冊

- 主動掃缺口找出三處：Istio 的流量/安全 CRD 只在 entity 頁被提名（VirtualService/DestinationRule/AuthorizationPolicy 各 1 次）、實際在用的 GHA + cloudflared 交付鏈零覆蓋（`workflow_dispatch` 全 wiki 零命中）、整套教材無動手實驗
- 新增 `24-yaml-fields-istio`（563 行）：Gateway/VirtualService/DestinationRule/ServiceEntry/Sidecar 全欄位 + PeerAuthentication/RequestAuthentication/AuthorizationPolicy/Telemetry/EnvoyFilter；重點釐清「RequestAuthentication 不擋無 token 請求，必須配 AuthorizationPolicy 的 requestPrincipals」與「ALLOW 一出現即轉白名單制」
- 新增 `25-yaml-fields-pipeline`（459 行）：GHA workflow 全欄位（on/permissions/concurrency/jobs/matrix/context/函式）+ 對應 tag `V.*.*.*.*.*` 的完整 release workflow 範例（含 yq 精準改 tag、Harbor robot 走 secret 兩個第 13 章踩坑的預防寫法）；cloudflared config.yml 全欄位與 K8s 部署形式；Compose Spec 全欄位 + Compose↔K8s 欄位對照表
- 新增 `26-lab-drills`（880 行，附錄 D）：20 個破壞—診斷—修復實驗分五組，每個含「弄壞的 YAML／你會看到什麼／先自己查的指令／details 摺疊的根因與修法」，收尾 10 題自我檢查對應實驗編號
- 修正兩處表格 render bug：Helm 函式表與 container `command` 說明的 `|` 未跳脫導致欄數錯亂（markdownlint MD056 抓到，已改 `\|`）
- 教材規模：16 章 + 11 附錄（A 題庫、B 速查、C-1~C-8 欄位、D 實驗），附錄 C+D 累計 5,122 行

## [2026-08-14] synthesis | .NET Web API 深度教材啟動（執行模型篇 00–06）

- 動機：既有 `dotnet-web-api` entity 頁是速查性質（條列 + 程式碼片段），回答「怎麼寫」但答不出「為什麼」。使用者要往「觀念與細節」深入，決定比照 k8s-mastery 的書本式教材規格另建章節，但依使用者裁決放在 `wiki/tech/entities/dotnet-web-api/` 底下分章，而非另開 concepts 資料夾
- 大綱定案 22 章 + 2 附錄，分四篇：執行模型（00–06）、資料層與 EF Core + Oracle（07–10）、認證授權（11–14）、工程實務（15–21）
- entity 頁改造成雙身分：上半部教材總目錄 + 進度表，下半部保留原速查內容並補上指向各章的 wikilink
- 本輪完成執行模型篇 7 章。每章以「一個真實會出事的場景」開篇，收尾固定「常見誤解」+「同事會來問你的問題」兩段自我檢測；貼合使用者實際 stack（K8s 部署、Oracle、JWT/Google OAuth）挑選案例，例如 graceful shutdown 一節直接推導 K8s 滾動更新 502 的 preStop 解法

## [2026-08-14] synthesis | 附錄 E–I：升級、Ingress annotation、狀態判讀、Day-2 維運、術語百科

- 依「對 K8s 管理員的實際價值」排序自選五個主題續寫，全部是既有 16 章 + 附錄 A–D 沒覆蓋的面向
- `27-upgrades-and-deprecations`（附錄 E）：version skew 圖解與升級順序、1.22/1.25 兩次大移除完整對照表 + 1.26→1.32 後續、dockershim/SA token/seccomp annotation 三個「不是 API 移除但會咬人」的變更、四種掃描手段（`apiserver_requested_deprecated_apis` metric、pluto、kubent、kubectl convert）、升級前四大類檢查清單（相容性/可回復性/不會卡住/觀測）、kubeadm 流程與升級後驗證
- `28-ingress-nginx-annotations`（附錄 F）：十組 annotation 表 + 全域 ConfigMap；開頭先講 snippet annotation 預設停用與 IngressNightmare 系列 CVE 的安全立場；含 oauth2-proxy 外部認證完整範例（對應使用者的 Google OAuth 架構）、rewrite-target 兩種用法的差異、canary 三種觸發的優先序
- `29-status-and-conditions`（附錄 G）：condition 五欄位讀法（reason 比 message 有用、Unknown ≠ False、observedGeneration 比對）、Pod 三層狀態 + 全部 waiting/terminated reason 表 + exit code 表（137/143 判斷優雅關閉）、Node/Deployment(ReplicaFailure)/Job/PV-PVC/HPA/CRD/APIService/Namespace conditions、ArgoCD 雙維度組合判讀、jsonpath 實用指令、症狀→欄位一頁式
- `30-production-readiness`（附錄 H）：新叢集五類上線檢查、服務 runbook 模板（含「不要做什麼」一節）、容量規劃三個數字與 requests 調校方法、每日/週/月/季維運節奏、孤兒資源盤點指令、12 條必備告警、事故四級分類與第一小時止血流程、「把制度寫進叢集」對照表
- `31-glossary`（附錄 I）：A–Z 約 140 條術語，每條 2–3 句定義 + 章節 wikilink，作為 22 萬字的導航與複習層
- 教材規模：16 章 + 16 附錄（A 題庫、B 速查、C-1~C-8 欄位、D 實驗、E 升級、F Ingress、G 狀態、H 維運、I 術語）

## [2026-08-14] synthesis | 入門篇 6 章（Level 0，零基礎台階）

- 使用者要求「把我當入門小白」。既有 22.8 萬字全部預設讀者「會用 Docker、看過 K8s YAML」，連第 0 章都從 Linux namespace 講起——真正的入門者前面沒有台階，這是結構性缺口
- 新增 `intro-0-start-here` ~ `intro-6-error-messages`，接在正文第 0 章之前，完全不預設 Linux/網路/容器知識
- `intro-1-server-and-process`：程式 vs 程序、伺服器是角色不是硬體、port 是房號（一個 port 一個程序）、systemd 四職責預告 kubelet、「在我電腦上跑得好好的」的環境差異、部署＝送過去/跑起來/找得到/活著四步與各工具的分工
- `intro-2-linux-and-terminal`：三種 shell 的差異（本機 PowerShell vs 容器內 bash）、路徑與 Linux 目錄、15 指令雙欄對照、管線與重導向、rwx 權限與 600/755/777、環境變數「改了要重啟」直通 K8s env 語意、vi 逃生門 `:q!`
- `intro-3-network-basics`：一次請求五階段、私有 IP 直通 Pod IP/ClusterIP、DNS TTL 與 hosts、狀態碼 4xx/5xx 分界與 502/503/504 對應、TLS 憑證三種問題、反向代理＝Ingress Controller 本質、綁 0.0.0.0 vs 127.0.0.1、排錯四步與「你剛學的↔K8s 對應」翻譯表
- `intro-4-yaml-syntax`：三種結構、縮排三規則、五種要加引號（含 Norway problem 與 `1.10` 被吃成 1.1）、四種多行符號、錯誤訊息表與「行號常不是真正出錯處」、`--dry-run=server` 看預設值、四錯練習題含 details 答案
- `intro-5-first-container-and-pod`：全手把手——docker run 逐參數拆解 → exec 進去看見小 Linux → **改檔案再重建證明容器可拋棄** → Dockerfile 兩行建自己的映像 → minikube → Pod → 刪掉不會復活 → Deployment 自動補回（reconciliation loop 的體感時刻）→ Service 靠標籤找 Pod → docker/kubectl 指令對照
- `intro-6-error-messages`：40+ 條訊息分六組（Docker/kubectl 連線/YAML apply/Pod 起不來/服務連不通/其他），每條給「白話意思＋最常見原因＋第一步」，附 mermaid 排錯決策樹與「求助時該附的五樣東西」
- 總目錄新增入門篇區塊與「完全沒有基礎怎麼辦」導引，七天路徑前加註需要先花一個週末讀入門篇；index.md 同步
- 教材規模：入門篇 6 章 + 正文 16 章 + 16 附錄，約 25 萬字

## [2026-08-15] synthesis | 實戰篇 3 章 + 教材驗收腳本

- 實戰篇補的是入門篇與正文之間的缺口：入門篇跑官方 nginx 映像，正文講原理，但「把**自己寫的** ASP.NET Core + React 送上叢集」這條路沒人走過一遍
- `practice-1-containerize-your-app`：先講應用本身要改的四件事（綁 0.0.0.0、設定外部化、日誌到 stdout、healthz/readyz 分開）再寫 Dockerfile；多階段建置為何必要、先 COPY csproj 再 COPY 原始碼的層快取原理、`USER $APP_UID`、`.dockerignore` 漏寫的兩種後果、React SPA 的 try_files 與「前端環境變數 build 時就固定」的兩難（相對路徑 + Ingress vs runtime config.json）、Compose 先驗證但 K8s 沒有 depends_on 等待能力
- `practice-2-deploy-real-app`：七個物件完整 manifest 逐段解釋——標準 labels 但 selector 不放 version、maxSurge/maxUnavailable 組合、三種 probe 分工（startupProbe 保護慢啟動而非拉長 initialDelaySeconds）、只設記憶體 limit 不設 CPU limit 的有意識取捨、restricted 安全基線 + readOnlyRootFilesystem 配 emptyDir、preStop 解決的 502 窗口、**由內而外五步驗證順序**、第一次部署六大錯、Kustomize overlay
- `practice-3-gitops-pipeline`：app/manifest repo 分離的三個理由、tag 觸發 workflow（cancel-in-progress:false、yq 而非 sed、Harbor 憑證走 secret）、ArgoCD Application 四個關鍵欄位（selfHeal/prune/allowEmpty/ignoreDifferences replicas）、**Sync×Health 四種組合判讀表**（Synced+Degraded 該查 Pod 不是查 ArgoCD）、PreSync hook 跑 DB migration、git revert vs argocd rollback、七個常見坑
- 驗收工具：新增可重複執行的 `verify_k8s_mastery.py`（scratchpad），一次檢查 BOM/CRLF、wikilink、表格欄數、YAML 解析；自動略過 Helm/Go 模板區塊，並以白名單標記三個**刻意寫錯的教學範例**（intro-4 兩個、10-helm 的 indent 誤用），且會反向驗證「標為錯誤示範者確實無法解析」
- 全庫驗收：39 檔、298 個 YAML 區塊，BOM/CRLF/失效連結/表格欄數/YAML 全數 0 問題
- 教材規模：入門篇 6 + 實戰篇 3 + 正文 16 + 附錄 16，約 26.6 萬字

## [2026-08-15] synthesis | .NET Web API 教材完稿（07–23，資料層／認證授權／工程實務＋兩份附錄）

- 續完剩餘 17 份：資料層篇 07–10（EF Core 內部、查詢、交易並發、Oracle 特有）、認證授權篇 11–14、工程實務篇 15–21、附錄 A/B
- Oracle 獨立成章（10）而非散在各處：識別碼引號與大小寫、12.2 前 30 字元上限、空字串即 NULL、CLOB 讀取成本、序列快取跳號、DDL 隱含提交導致 migration 無法整段回滾、`ORA-01795` IN 上限、何時該換 Dapper。這些是照抄 SQL Server 教學會踩的坑
- 貫串全書的伏筆在 21 章收束成一張「本機好好的、上容器就掛」對照表（9 個症狀 → 章節 → 根因），並附按篇分類的上線前檢查清單
- 附錄 A 65 題分 L1 基礎／L2 應用／L3 診斷三級，答案用 `<details>` 摺疊強制先自己講一遍；收尾 25 條紅色警戒清單全部標註對應章節
- 附錄 B 為第二螢幕用途：緊急排錯十連發（症狀→先查哪裡）、`Program.cs` 骨架、middleware 順序表、DI 決策表、EF Core/Oracle 速查、Dockerfile 與 Deployment 骨架、診斷指令
- entity 頁 `dotnet-web-api.md` 進度表全數轉 ✅，補上「這套教材的取向」說明假設環境為 K8s + Oracle + JWT/Google OAuth；index.md 補齊 07–23 條目

## [2026-08-15] synthesis | 實戰 4（從零寫 YAML 的方法論）+ 附錄 J（Istio Ingress Gateway）

- 使用者問「有地方寫 IGW?」——掃全庫確認**兩種解讀都沒寫**：`IngressGateway` 僅 2 處順帶提及（一個 label 範例、一個 issue 連結），AWS Internet Gateway/VPC 完全空白。確認指的是 Istio Ingress Gateway 後補上專章
- 使用者另指出 YAML 卡點是「不知道怎麼從零開始寫」——既有附錄 C 八份是**查詢**用，intro-4 是語法，但「拿到需求推導出 manifest」的方法論確實沒有
- `practice-4-write-yaml-from-scratch`：核心是「永遠不從空白開始」——列出 12 條 `kubectl create ... --dry-run=client -o yaml` 產骨架指令；**五問法**（什麼性質→啟動需要什麼→誰要連→壞掉怎麼辦→吃多少/影響誰）各自對應欄位組；兩個完整推導示範（對帳 CronJob：逐句需求對應到 timeZone/concurrencyPolicy/backoffLimit/ttl，並示範「失敗要通知」是 YAML 做不到、須靠告警的有效產出；Web Deployment：三十秒啟動為何是 startupProbe 而非 initialDelaySeconds）；反向讀 YAML 練習表；三個自問工具；四步驗證鏈（yaml→kubeconform→dry-run=server→kube-linter）；五題練習含解題方向
- `32-istio-ingress-gateway`（附錄 J）：IGW 本質是「獨立部署的 Envoy」、與 ingress-nginx 七項對照與選型表（含「沒有明確理由需要 mesh 就別用」的誠實建議）、Service 與 Gateway CRD 的職責分界（443→8443 因非 root）、**三條綁定規則**（selector/gateways 跨 ns 寫法/hosts 交集）與「VirtualService 沒寫 gateways 預設只管 mesh」這個最常見單一錯誤、15xxx port 對照、**Envoy response flags 表**（NR/UH/UF/NC/UO/URX/UT/DC）把四種長得一樣的 503 分開、UF 與 mTLS STRICT vs DestinationRule DISABLE 的衝突、憑證三坑（Secret 要在 gateway 的 namespace、HTTP-01 需要 80、萬用字元只能 DNS-01）、istioctl 七條診斷指令、與 Gateway API 的同名不同 group 提醒
- cross-link：istio entity 頁與附錄 C-7 都加上指向附錄 J
- 教材規模：入門篇 6 + 實戰篇 4 + 正文 16 + 附錄 17（A–J），約 27.5 萬字

## [2026-08-15] synthesis | FastAPI 教材開篇（hub + 起步篇 00–03）

- 新開 `wiki/tech/entities/python-fast-api/`，格式對齊 `dotnet-web-api`（hub 頁上半教材目錄、下半速查；章節各自同名資料夾）
- 大綱定案 12 章 + 2 附錄：起步篇 00–04（為什麼是 FastAPI／路由／Pydantic／Depends／async）、實務篇 05–11（DB／錯誤處理／JWT／middleware／設定／測試／部署）、附錄 12–13（速查／ASP.NET Core 對照）
- 讀者設定為「已會 ASP.NET Core、第一次碰 Python 後端」，所以全書隱含主軸是**對照**——但刻意標出「看起來一樣其實不一樣」的地方，最大的一個是 DI 解析時機（.NET 啟動時建圖並驗證，FastAPI 每 request 現場解析，漏掉的依賴啟動時抓不到）
- `00-why-fastapi-and-setup`：WSGI 同步簽章導致一 worker 一 request、ASGI 三差異表；核心賭注是「型別提示存在 `__annotations__` 裡、FastAPI 執行期讀出來，一份宣告四處用」；`@app.get` 是**當場執行的 decorator** 不是 C# 的中繼資料 attribute（推導出後面路由順序會咬人）；venv/PowerShell ExecutionPolicy/`uvicorn app.main:app` 逐段拆解
- `01-routing-and-path-operations`：六條參數來源推導規則表為本章核心；三個高頻坑——`str | None` 不等於選填（只看有沒有預設值）、`list[str]` 少 `Query()` 會被判成 body、單一 `str` 想進 body 要 `Body(embed=True)`；`/users/me` 被 `/users/{user_id}` 攔截（且警告別靠 `int` 轉換失敗來繞，那回 422 且改字串 id 就破功）；尾斜線 307 在反向代理與 CORS 下的失敗
- `02-pydantic-and-validation`：定位為「解析器不是型別檢查器」（建構成功即代表已驗證）；422 的 `loc` 第一個元素就是診斷「參數收不到」的工具；validator 只能丟 `ValueError`；Create/Update/Out 三分的三個理由（`password_hash` 外洩、over-posting 提權、契約與資料表解耦）；**回應驗證失敗是 500 不是 422**；v1→v2 對照表（含 `Optional` 不再隱含預設值這條遷移地雷）
- `03-dependency-injection`：以「背景任務拿到已關閉 session」開篇——0.106 起 `yield` 收尾改在回應送出**前**執行，舊文章寫法全部失效；依賴快取（同 request 同依賴只呼叫一次）即 Scoped 的實作原理；Singleton 兩種寫法（`lru_cache` 工廠 vs `lifespan` + `app.state`，HTTP client 必須走後者否則 port 耗盡）；`dependency_overrides` 定位為「依賴函式就是你的測試接縫」
- cross-link：`python.md` 補指向、index.md 新增 FastAPI 教材小節
- 04–13 尚未撰寫，hub 進度表以 ⬜ 標記

## [2026-08-16] synthesis | FastAPI 第 04 章（async 與並發）— 起步篇完成

- `04-async-and-concurrency`：全書樞紐章，後面 DB／HTTP client／部署章的 worker 計算都建立在這個模型上
- 開篇事故：`async def` 裡跑同步查詢 → **連 `/health` 都超時**，因為 event loop 是單執行緒協作式，沒有 `await` 就沒人能打斷
- 核心反直覺結論寫成一句話：「在 FastAPI 裡，用 `async def` 包住同步程式碼，比用 `def` 危險得多」——`def` 會被 Starlette 丟進 threadpool 隔離，對 .NET 出身者尤其反直覺（C# 的 async 加了沒壞處）
- 附五分鐘可驗證實驗（`/blocking-async` vs `/blocking-sync` 各 `time.sleep(5)`，再打 `/ping` 比較）
- **兩種卡法的診斷對照表**：全部端點（含純 async 的 `/health`）一起停 = event loop 被阻塞，一個請求就夠；只有 `def` 端點排隊 = threadpool 40 條用完。推導出「健康檢查必須是 `async def` 且不做 I/O」——它是區分這兩種狀態的儀器
- threadpool 調高是治標，且要先確認 DB 連線池跟得上，否則只是換個地方排隊
- CPU 密集三層解法（`ProcessPoolExecutor` → 任務佇列 → 根本別在 Python 做），界線給數字：>100ms 考慮搬、>1s 一定搬；例外是 NumPy/Pillow 這類會釋放 GIL 的 C 擴充
- 另收：阻塞呼叫對照表（`time.sleep`/`requests`/同步 SQLAlchemy/`boto3`…）、`asyncio.to_thread` 混合寫法、`gather` vs `TaskGroup`（前者失敗後其餘仍在背景跑）、漏 `await` 只有 `RuntimeWarning` 不會報錯
- 起步篇 00–04 完成，hub 與 index 進度同步

## [2026-08-16] synthesis | FastAPI 第 05 章（資料庫與 SQLAlchemy）

- 開篇事故刻意接續 04 章的數字：`QueuePool limit of size 5 overflow 10 reached` —— threadpool 預設 40 條對上連線池預設 15 條，**兩個預設值互相矛盾**，且只在尖峰出現所以拖兩週才發現
- 給出明確立場：**預設用同步 SQLAlchemy + `def`**，不是保守而是 04 章推導的結果；async 的四項代價逐條列出（整條鏈不能有同步、lazy load 直接不合法、驅動選擇少、stack trace 穿 greenlet 難讀），並給「什麼訊號才該換 async」的判準
- **三條連線池計算規則**：①池子 ≥ threadpool 併發數 ②`worker × Pod 副本 × 池子 ≤ DB max_connections × 0.8`（本機 30 條、上叢集 360 條，又一個「本機好好的」）③`pool_recycle` < 中間設備閒置逾時 + `pool_pre_ping`；另建議 `pool_timeout` 從預設 30 秒調短——等 30 秒才失敗會被重試放大成惡性循環
- 交易邊界三種寫法並列取捨（依賴只開關／依賴代管 commit／service 層），明確反對版本二用在有外部副作用的專案——它讓「有沒有原子性」變成要翻三層才能回答
- `expire_on_commit=False` 標為 FastAPI + SQLAlchemy 幾乎必開
- `DetachedInstanceError` / `MissingGreenlet` 收斂成同一根因（序列化時機晚於載入時機），給可寫進 review 清單的紀律：**`response_model` 上有什麼關聯，查詢 `options()` 就要有對應 loader**
- Alembic：autogenerate 偵測得到/不到對照表，點名**欄位改名會被產成 drop + add，正式環境資料直接消失**；反對啟動時跑 migration（K8s 滾動更新多 Pod 同時執行）
- Oracle 四坑對齊 `10-oracle-specifics`：`python-oracledb` thin mode 免 Instant Client（容器化大幅簡化）、空字串即 NULL、`IN` 上限 1000（**`selectinload` 產生的查詢也會撞到**，且那條 SQL 不是你寫的）、DDL 隱含提交使 migration 無法整段回滾

## [2026-08-16] synthesis | FastAPI 第 06 章（錯誤處理）

- 開篇用前端視角：FastAPI 預設會產出**四種不同形狀**的錯誤（422 的 `detail` 是陣列、`HTTPException` 的是字串、500 的是固定字串、外加有人自己刻的 200 + `success:false`），各自合理但湊起來沒有契約
- 畫出例外處理三層結構圖，點出一個沒有任何錯誤訊息提示的坑：**`ExceptionMiddleware` 在使用者 middleware 的內側，所以 middleware 裡 `raise HTTPException` 會變成 500**，必須 `return JSONResponse`；並推導出「用 dependency 取代 middleware 就沒這問題」
- 狀態碼決策表挑三組最會吵的展開：401/403 分界是「身分」不是「有沒有登入」；403 vs 404 是資安判斷（回 403 等於確認資源存在）；500 vs 503 是**告警語意**（500 叫工程師起床，503 先看下游）
- 統一格式採 RFC 9457（對齊 .NET `ProblemDetails`），給可直接抄的完整實作；三個實作細節：handler 要註冊在 **`StarletteHTTPException`** 父類別上才接得到框架內部的 404/405、`logger.exception` 只寫在未處理例外那支（否則 error log 被 404 淹沒）、回應只帶 `trace_id` 不帶 stack trace
- 領域例外與 HTTP 解耦：service 丟 `DomainError` 子類別、API 層一支 handler 轉換；理由給兩個（service 要能被 worker/CLI 重用、409 這個數字說不出是哪種衝突，前端需要 `code` 才能 switch）
- 資料庫例外三原則：唯一約束是 409 不是 500、**永遠不要把 `IntegrityError` 訊息轉發給客戶端**（含 SQL 與表結構）、**「先查再寫」擋不住競態**（唯一索引才是保證，先查只為了友善訊息）
- 另收：例外不該做控制流程 + `find_x`/`get_x` 命名慣例、記錄層級對照表（點名「每個 except 都 logger.error」是 error log 失效的主因）、`debug=True` 會把 stack trace 寫進回應

## [2026-08-16] synthesis | FastAPI 第 07 章（認證與授權）

- 開篇是漏洞級誤解：`Depends(oauth2_scheme)` 看起來像門鎖，實際 `curl -H "Authorization: Bearer abc"` 直接通過——**`OAuth2PasswordBearer` 只做兩件事**（從 header 取字串、產生 `/docs` 授權按鈕），不驗簽章不檢查過期
- 點明與 ASP.NET Core 最大的架構差異：**FastAPI 沒有 authentication 系統，一行都沒有**；`fastapi.security` 全是取值器 + OpenAPI 中繼資料。附完整對照表，並推導出紀律「驗證掛 router/app 層級」（對應 .NET 的 `FallbackPolicy`：讓忘記加的預設是拒絕）
- 五個安全關鍵逐條展開：①`algorithms=["HS256"]` 白名單防 `alg:none` 與**演算法混淆**（用公開的 RS256 公鑰當 HMAC 密鑰簽） ②`aud`/`iss` 必驗 ③`leeway=30`（.NET 預設 5 分鐘太寬、PyJWT 預設 0 太嚴） ④過期與其他錯誤分開讓前端能決定 refresh 還是回登入 ⑤最後查一次 DB 讓停用即時生效
- 授權分三層，第三層（資源歸屬）是重點：dependency 答不了「這張訂單是不是你的」，解法是**把租戶條件寫進查詢並包成 dependency**，讓「忘記檢查」在結構上不可能發生；且回 404 不回 403
- 登出四方案對照表，並誠實建議：**單一後端 + 同源就直接用 session + httpOnly cookie**，JWT 的優勢在跨服務/跨網域，沒這需求等於付了複雜度沒拿到好處
- Google OIDC：`audience=client_id` 這一行是整段最關鍵——少了它，任何人拿自己 Google 應用簽的**合法** token 就能登入任何帳號；另收 `PyJWKClient` 快取、`iss` 兩種寫法都要接受、`email_verified` 要查、用 `sub` 不用 email 對應使用者
- 套件現況更正：**passlib 與 python-jose 都已停止維護**（passlib + 新版 bcrypt 會噴 `__about__` 錯誤），改用 pwdlib / PyJWT，與 FastAPI 官方文件現況一致；另記 bcrypt 72 位元組靜默截斷、登入失敗訊息要一致避免帳號列舉

## [2026-08-16] synthesis | FastAPI 第 08 章（Middleware 與橫切關注）

- 開篇是前後端各說各話的真實情境：前端看到 `No 'Access-Control-Allow-Origin' header`，後端堅稱設了 CORS——**真相是 token 過期回的 401 在 CORS middleware 外層產生，沒帶 CORS header，瀏覽器把它報成 CORS 錯誤，真正的 401 被掩蓋**，兩邊各查半天錯方向
- 核心規則且與 .NET **完全相反**：Starlette 的 `add_middleware` 是 `insert(0, ...)`，所以**最後註冊的在最外層**；ASP.NET Core 的 `app.UseX()` 則是註冊序即執行序。這個差異不會報錯，只會讓行為變詭異。給了固定註冊模板（由內而外：GZip → RequestContext → TrustedHost → CORS）
- middleware vs dependency 決策表，關鍵判準一句話：**這件事需要知道請求打到哪支 endpoint 嗎**——需要就不能用 middleware（它在路由解析之前）；另加三條（要 DI／要 `raise HTTPException`／只適用部分路由）
- CORS 定位先講清楚「它是瀏覽器規則不是後端安全機制」，推導出三個結論（curl 不受影響、`*` 本身不危險但不能配 credentials、它保護使用者不是伺服器）；四個高頻踩點 + **一張「前端看到什麼 → 真正原因」診斷表**（含「改了設定沒生效 = preflight 被 max_age 快取，開無痕」）
- request_id 用 **`contextvars` 而非 thread-local**（並發請求共用執行緒，thread-local 會互相污染），middleware set/reset + `logging.Filter` 注入，之後每行 log 自動帶上；強調要沿用上游 `X-Request-ID`/`traceparent` 才能跨服務貫串
- 結構化 logging 三個易漏細節：要一起接管 `uvicorn`/`uvicorn.access`/`uvicorn.error`（否則 log 兩種格式、收集端半數解析失敗）、`ensure_ascii=False`（中文不變跳脫序列）、`disable_existing_loggers: False`
- 反向代理三設定：`--proxy-headers`（不開則 `request.url` 是 http、OAuth redirect_uri 會錯）、`--forwarded-allow-ips` 的信任邊界警告、TrustedHost 擋 host header 注入
- 效能：`BaseHTTPMiddleware` 有已知開銷（內部多開 task 並把回應包成串流）；但更常見的優化是**減少 middleware 數量**——很多寫成 middleware 的東西本來就該是 dependency；另建議 access log 跳過 `/health` 免得健康檢查主導 log 量

## [2026-08-16] synthesis | FastAPI 第 09 章（設定與環境）

- 開篇事故：`os.getenv("DATABSE_URL", "sqlite:///./app.db")` 少一個字母 → 服務**一切正常**（啟動、健康檢查、寫入、查詢全綠）但資料寫進容器內 SQLite，滾動更新後訂單消失。提煉出全章命題：**設定錯誤最可怕的形式不是啟動失敗，而是靜默用錯值繼續跑**
- 全章目標定為「讓錯誤設定在啟動那一秒失敗」，三條規則：①必填不給預設值 ②`model_validator` 主動擋危險預設（`changeme`、萬用字元 CORS、debug 開著）③模組層級建立實例讓驗證早於監聽 port
- 關鍵論證：**Pod 起不來反而是最安全的失敗**——CrashLoopBackOff 會讓滾動更新自動停住、舊 Pod 不被移除，正式環境毫髮無傷；比帶錯設定安靜跑著好一百倍。這是對「驗證失敗會掛掉太危險」的直接反駁
- env vs volume 決策表：一般設定走 env，**密鑰走 volume + `secrets_dir`**（pydantic-settings 直接把「檔名=欄位名、內容=值」讀進來，與 K8s Secret volume 結構天然吻合，且不進環境變數／`kubectl describe`／子程序）；並點明「不重啟就生效」在 K8s 多半是偽需求
- pydantic-settings 三個實際踩點：複雜型別走 `json.loads`（**逗號分隔會失敗**，附 `mode="before"` validator 解法）、巢狀用**雙**底線、v2 的 `extra` 預設 forbid 會讓 `.env` 多餘變數炸掉
- `SecretStr` 的價值在 `repr` 是星號——不小心把 settings 印進 log 不會洩漏，讀值要明確 `.get_secret_value()`，這個摩擦是刻意的
- 密鑰外洩處置**順序**：先輪替（唯一真正有效）→ 查稽核 → 最後才清 git 歷史；顛倒的話清理那兩小時密鑰是活的
- 反對 `if environment == "production"` 分岔，判準一句話：**會讓正式與測試跑不同程式碼的分岔就不該存在**；只有 `/docs` 開關這種不影響業務路徑的邊界設定例外
- 另收：什麼不該進設定（頻繁變動的業務參數判準「改這個值需不需要工程師介入」、大量 feature flag、可衍生值用 `computed_field`）

## [2026-08-16] synthesis | FastAPI 第 10 章（測試）

- 開篇：200 支測試、覆蓋率 87%、CI 全綠，上線第一天五個 500（`ORA-12899`/`ORA-02291`/`ORA-01400`）——因為測試用 SQLite、正式用 Oracle。附**五項行為差異表**（外鍵預設關、VARCHAR 長度不強制、空字串≠NULL、動態型別、檔案級鎖），結論：那些測試驗證的是「這段程式碼在 SQLite 上能跑」，而沒人關心這件事
- 與 .NET 的比例差異：`WebApplicationFactory` 要啟動整個 Host 所以整合測試通常刻意壓少，但 **`TestClient` 不啟動伺服器**（同程序直呼 ASGI app），所以 FastAPI 專案**該多寫整合測試**——路由/參數解析/驗證/依賴鏈/序列化在 FastAPI 裡高度耦合於函式簽章，分開測反而測不到真正會錯的地方
- `TestClient` 兩個必知：`raise_server_exceptions=False` 才測得到自己寫的 500 格式（預設會把例外重拋進測試）、要用 `with` 才觸發 lifespan（否則 `app.state` 上的東西是 None）
- `dependency_overrides` 最實用的用法是**覆寫 `get_current_user` 三行切換身分**，不必真簽 JWT（對照 .NET 要寫 TestAuthHandler + 註冊假 scheme）；並強調它是掛在 app 上的**全域字典**，忘了清的症狀是「單獨跑過、整批跑失敗且與檔案順序有關」，用 `autouse=True` fixture 自動清
- 測試資料庫給完整 conftest 骨架：Testcontainers（`scope="session"` 共用容器）+ **每支測試包在會被回滾的交易裡**（即使測試內 `commit()` 也只結束內層 savepoint）
- mock 邊界表，點名反面教材 mock `Session`——那種測試永遠會過因為不執行任何 SQL，所有真正會錯的地方（欄位長度、外鍵、NULL、N+1、交易）全被繞過，等於開篇事故的另一種版本
- 時間處理主張「注入不要 patch」，做成 `get_now` dependency，明確對應 .NET 8 的 `TimeProvider`
- httpx 版本現況更正：`httpx.AsyncClient(app=app)` 捷徑**已被移除**，要用 `ASGITransport(app=app)`，網路上大量範例仍是舊寫法會噴 `TypeError`
- 每支 endpoint 最低四測，點名**「存取別人的資源要回 404」是最常漏且唯一能自動防越權的測試**（呼應 07 章多租戶）；另給分界線「驗證這件事本身不用測，你寫的驗證規則要測」

## [2026-08-16] synthesis | FastAPI 第 11 章（部署）— 正文完稿

- 收束章。前面各章留下的數字（threadpool 40、連線池 15、event loop 單執行緒、設定 fail fast）在此收攏成可計算的部署參數
- 開篇「每次部署準時掉一批 502」，根因是**K8s 送 SIGTERM 與更新 Endpoints 是並行而非循序**——應用已開始關閉但 Ingress 還在送流量。修法五行（`preStop: sleep 5` + 三個逾時數字對齊：preStop 5 + graceful 30 < terminationGracePeriod 60）
- **worker 數量給明確立場**：K8s 上一容器一 worker、靠 `replicas` 擴展，四個理由（K8s 已是程序管理器、HPA 顆粒度、資源隔離、log 可讀）；副本數從「目標吞吐 ÷ 單 worker 容量」推，再**回頭撞第 05 章的 `副本 × 池子 ≤ DB 上限 × 0.8`**——點明那條約束通常才是真天花板而非 CPU
- 與 .NET 的關鍵差異：CPU limit 在 .NET 會影響 ThreadPool 計算，Python 沒有那層——event loop 就一條執行緒，給再多核也用不到。故建議**記憶體設 limit、CPU 只設 request**（可壓縮 vs 不可壓縮）
- Python 特有的容器坑：**不能用 Alpine**（musl 讓 manylinux wheel 失效 → 現場編譯，建置慢十倍、要裝編譯工具反而更大、常失敗）、`PYTHONUNBUFFERED=1` 否則 log 會延遲或整批遺失、`.dockerignore` 漏 `.venv` 會把本機平台編譯的套件複製進去
- 記憶體：CPython 釋放的記憶體不一定還給 OS（arena），大請求後 RSS 停在高原**是正常的**；洩漏的特徵是持續成長、基線一次比一次高。`OOMKilled` 是 kernel 直接砍，**Python 層完全沒有訊息**——「log 沒例外但 Pod 重啟」的第一診斷
- liveness 檢查資料庫的完整因果鏈：DB 閃斷 30 秒 → 全部 Pod liveness 同時失敗 → 同時重啟 → 恢復時被一批同時啟動的 Pod 打爆 → 再次失敗。**用一次可自癒的小故障換一場自我攻擊**。另強調 liveness 端點要 `async def` 且不做 I/O，它是「event loop 是否被阻塞」的儀器（呼應 04 章）
- 另收：`engine.dispose()` 漏了會讓滾動更新期間新舊 Pod 連線並存撞上限、expand-contract 三階段表（Oracle DDL 隱含提交所以每份要更小）、完整 Deployment manifest、`readOnlyRootFilesystem` 需要 `PYTHONDONTWRITEBYTECODE` 配合
- **教材收束：「本機好好的、上叢集就掛」14 列對照表**（症狀 → 章節 → 根因），每一列都是前面某章埋的伏筆；加六組上線前檢查清單
- 進度：正文 00–11 全數完成，剩附錄 12（速查）、13（ASP.NET Core 對照）

## [2026-08-16] synthesis | FastAPI 附錄 A（速查）

- 定位第二螢幕用：不解釋原理，只給症狀對應、可直接貼的骨架、決策表、指令；每節標對應章號
- 十三節：緊急排錯十連發（症狀→先查哪裡）、專案骨架含完整 `main.py`/`deps.py`、參數來源規則、Pydantic v2 + v1 對照、依賴生命週期對照 .NET、狀態碼、SQLAlchemy（含三條池子約束）、async 決策、測試 `conftest.py` 全文、Dockerfile + Deployment、PowerShell 診斷指令
- 兩個原創彙整價值最高：**數字速查表**把散落十二章的預設值與建議值集中（threadpool 40／pool 5+10／pool_timeout 預設 30 建議 10／leeway 30s／preStop 5s／graceful 30s／terminationGracePeriod 60s），並分出「硬性上限」一區（bcrypt 72 位元組、Oracle IN 1000、識別碼 30/128、PG max_connections 100）；以及 **Oracle 錯誤碼 → HTTP 狀態碼對應表**（ORA-00001→409、ORA-12899→400…）
- **20 條紅色警戒清單**做成 checkbox，每條標章號，可直接當 code review 或上線前逐項核對

## [2026-08-16] synthesis | FastAPI 附錄 B（ASP.NET Core 對照）+ 教材完稿驗收

- 附錄 B 定位給兩種人：要讀懂 FastAPI 程式碼的 .NET 開發者、要把 ASP.NET Core 服務搬過來的人
- 開頭先立**三個世界觀差異**（不是 API 對照而是設計哲學）：①型別何時生效（編譯期強制 vs 執行期讀 `__annotations__`）②依賴是註冊還是宣告（`Build()` 建圖驗證 vs 每 request 現場解析）③誰吸收阻塞（ThreadPool 自動長大 vs 單 event loop）。後面所有差異都從這三條長出來
- 十二組逐項對照表（啟動/路由/參數驗證/DI/middleware/認證/錯誤/資料/設定/測試/部署）+ 四段程式碼並排（CRUD、DI、錯誤處理、測試）
- 全書價值最高的一節是**「看起來一樣其實不一樣」14 列**——每列都是「照 .NET 直覺寫會出事」：async 的風險方向相反、middleware 順序相反、驗證失敗 400 vs 422、DI 錯誤發現時機、路由消歧義、`Depends(oauth2_scheme)` 不驗證、middleware 裡 raise 變 500、Scoped 是快取不是容器、CPU limit 無影響、記憶體不還 OS、`ClockSkew` 5 分鐘 vs `leeway` 0、SQLite 與 InMemory 同樣不可靠、沒 `response_model` 就整列外洩、`str | None` 仍是必填
- 遷移實務給順序（設定與健康檢查 → model/schema → 認證 → 逐 router → 背景工作）與**不該照搬的 .NET 慣例表**（泛型 Repository 基底、AutoMapper、每 service 一介面、三層專案結構、`Result<T>`、`I` 前綴），點名最常犯的錯是「用 Python 語法寫的 C# 程式」
- 雙方各自缺什麼：FastAPI 獨有（dependency 參數冒泡進 OpenAPI、`dependency_overrides`、內建 `/docs`、`Annotated` 別名）；.NET 獨有（完整 authentication 系統、編譯期型別安全、啟動時 DI 驗證、`IHttpClientFactory`+Polly、`BackgroundService` 一級支援、OTel 深度整合）
- 收尾一句話：**ASP.NET Core 給完整框架讓你填空，FastAPI 給好零件讓你自己組**；知道「哪些事沒人替你做」就是這套教材的全部價值
- **驗收**：新增可重複執行的 `verify_fastapi.py`（scratchpad），檢查 BOM/CRLF/frontmatter 五欄位/wikilink 解析/表格欄數/code fence 閉合。首輪 3 個告警經查全為腳本誤判——2 個是 GFM 表格內合法的跳脫管線 `\|`、1 個是連結解析未比照 Obsidian 的不分大小寫；修正腳本後另發現 `resolved` 未同步轉小寫的第二個腳本 bug
- 唯一實際修改：09 章的 `[[raw/devops/Vault]]` 改為 `[[vault]]`（連 wiki entity 頁而非 raw 路徑，符合本庫慣例）
- 最終：**15 檔、6,659 行、258 個程式碼區塊、69 張表、111 個 wikilink 全數解析成功**，BOM/CRLF/frontmatter/表格/fence 全數 0 問題

## [2026-08-16] synthesis | FastAPI 附錄 C（自我檢測）— 補齊與 .NET 教材對等的缺口

- 補的是上一輪自己指出的缺口：dotnet 教材有 `22-self-assessment`，FastAPI 原大綱沒排。使用者續下「繼續寫」即視為要補
- 58 題三級：**L1 基礎 22 題**（事實與定義）、**L2 應用 20 題**（給情境要決策並說理由）、**L3 診斷 16 題**（給症狀反推根因）。答案一律 `<details>` 摺疊，強制先自己講一遍
- 難度分級的判準寫進開頭：L1 答不出來是沒讀、L2 答不出來是知 what 不知 why、**L3 才是分水嶺**——答得出來代表上線後撐得住
- L3 十六題全部取自各章開篇的真實事故，形式統一為「症狀 → 根因 → 修法 →（若有）辨識訊號」：連 `/health` 都超時、`QueuePool` timeout、query 收不到 list、`/users/me` 回 404、`DetachedInstanceError`、偶發假 CORS、middleware raise 變 500、背景任務 session 已關、**訂單寫進容器內 SQLite**、部署掉 502、DB 閃斷引發全體重啟、log 無例外卻重啟（OOMKilled）、部署撞連線上限、測試順序相依、ConfigMap 改了沒生效、redirect_uri 變 http
- 收尾給**題號→章節對照表**與過關標準（L1 18/22、L2 14/20、L3 10/16 為門檻，並說明各自代表什麼程度）
- hub 與 index 同步改為「12 章 + 3 附錄」
- 重跑驗收：**16 檔、7,285 行、259 個程式碼區塊、71 張表、191 個 wikilink**，全數通過（`<details>` 區塊內的 wikilink 也一併解析驗證）
- **補上先前漏掉的雙向 cross-link**（本庫 CLAUDE.md 要求）：掃出 FastAPI hub 原本只被 `index.md`／`log.md`／`python.md` 連到，於是 `web-backend-moc` 加入 FastAPI 與 Python 兩個 entity 並改寫定位句（點明兩套後端教材共用同一部署場景、可互相對照）、`dotnet-web-api` 的連結區加上指向 FastAPI 與附錄 B 的翻譯表

## [2026-08-16] ingest | python entity 頁脫離 stub（給 C# 開發者的 Python）

- 動機：`python.md` 掛著 stub 半年，而 FastAPI 教材整套預設「讀者 Python 語法看得懂」——這頁撐不起那個假設
- **先盤點 raw 覆蓋範圍再定大綱**：`raw/Languages/Python/` 十三個檔約 2,500 行，紮實涵蓋型別／四大容器／控制流程與生成式，但**完全沒有函式、類別、模組、例外、型別提示**——而那五項恰好是寫 FastAPI 的前提。故第五節之後為補寫，並在頁首誠實標注來源覆蓋到哪
- **關鍵編排決策**：不做語法教學（那種到處都有、且對本讀者無用），改組織成**「你的 C# 直覺會在哪裡壞掉」**——與 FastAPI 教材同一套框架法。壞的地方講深，不壞的地方一筆帶過
- 開頭立**五個會壞的直覺**當全頁骨架：變數是名牌不是盒子（Python 沒有值型別）、縮排即語法、型別提示執行期不生效（推導出「一定要把 mypy/Pyright 加進 CI」）、沒有 private（雙底線是 name mangling 不是存取控制）、沒有多載與介面（duck typing + `Protocol`）
- 各節都掛 C# 對照表：型別（`int` 無上限、`/` 永遠回 float、`decimal`→`Decimal`）、四大容器對 `List/ValueTuple/Dictionary/HashSet`、型別提示對 `User?`→`User | None`、`Func<int,string>`→`Callable[[int], str]`
- **生成式直接對照 LINQ**（`Where().Select()` ↔ 串列生成式、`ToDictionary` ↔ 字典生成式、未具體化的 `IEnumerable` ↔ 小括號產生器），這是 C# 出身最快能上手的一節
- 兩個文化差異寫成獨立段落：**EAFP vs LBYL**（Python 用例外處理預期失敗是正常的，因為成本低且沒有 check-then-act 競態）、以及 truthiness（`if not x` 會吃掉 `0`/`""`/`[]`，判 None 一律 `is None`）
- 收進的高頻坑：**可變預設參數**（`def f(x, bucket=[])` 在 `def` 執行時求值一次，全部呼叫共用；並註明 FastAPI 參數宣告裡的 `= []` 是例外）、淺拷貝、單元素 tuple 要逗號、`x in list` 是 O(n)、**Windows 上 `open()` 不寫 `encoding="utf-8"` 會用 cp950 讀中文炸掉**
- 工具鏈給明確建議：venv 必須、ruff 取代 flake8+isort+black、mypy/Pyright 擇一但**要進 CI 才有意義**、uv 可取代 pip
- tkinter 判定與現行技術路線無關，不整合進正文，只在 raw 來源區保留指標並標注原因
- 驗收：653 行、無 BOM/CRLF、fence 平衡、全部 wikilink（含 12 個 raw 頁）解析成功
- index.md 的條目從「stub，待整合 raw 內容」改為實際定位

## [2026-08-16] synthesis | FastAPI 實戰章（送上叢集的十個差異）

- **先掃 k8s-mastery 的 practice 1–3 才動筆**，確認 Deployment/Service/Ingress/ArgoCD/GitOps 兩 repo 都已寫透且與語言無關 → 決定寫成**差異章**而非完整實戰，避免大幅重複；K8s 側概念一律指回去
- 全章命題收斂成一句：「交付鏈已經跑得起來（你送過 ASP.NET Core），現在應用換成 FastAPI，哪些步驟要改」——答案十個
- Dockerfile 五個決策逐一對照 .NET：**alpine 不可用**（musl 讓 manylinux wheel 失效，附建置時間/映像大小/失敗率四項對照表）、**venv 就是產物**（沒有 publish 這一步，附 uv 版寫法）、層快取切點是 `requirements.txt`、`PYTHONUNBUFFERED` 缺了會在排查 CrashLoop 時看不到死因、`.dockerignore` 漏 `.venv` 比 .NET 漏 `bin/obj` 嚴重（Windows 編譯的套件會蓋掉正確版本）
- probe 一節點出 FastAPI 特有要求：**liveness 是儀器不只是檢查**——寫成 `def` 會跑在 threadpool，event loop 卡死時它反而還能回應，於是失去唯一能區分「loop 被堵」與「下游變慢」的訊號；readiness 的 Oracle 要 `SELECT 1 FROM DUAL`
- 設定注入給了一個**值得刻意做一次的驗證**：故意讓 Secret 少一個 key 部署，觀察新 Pod CrashLoop 而舊 Pod 不被移除、滾動更新自動停住——看過一次就不會再質疑「必填不給預設值」
- **副本數與連線池五步實算**（threadpool 對齊 → 單 worker 容量 → 副本數 → 撞 DB 上限 → maxSurge 翻倍），用一組具體數字走完，並建議把結果寫進 manifest 註解
- CI 差異：沒有 restore/build/publish 三段，但**必須加 ruff + mypy 補上 Python 缺的編譯器檢查**；Testcontainers 需要 runner 有 Docker；pip cache 與 buildx GHA cache 要分開設；沿用既有 Harbor robot account `$` 展開的踩坑指標
- 驗證段給的是**能在 slim 映像裡跑的指令**——`kubectl exec ... -- curl` 會 `executable file not found`（slim 沒有 curl/wget），改用 `python -c` 的 `urllib` 或臨時 curl Pod；明確反對為了 debug 把 curl 裝進正式映像
- 回顧段把十個差異按「照 .NET 做法會不會直接失敗」三分：**會直接失敗 4 個**（alpine／缺 UNBUFFERED／漏 .venv／`SELECT 1` 沒 FROM DUAL）、**會安靜出錯 3 個**（池子沒對齊／ConfigMap list 沒寫 JSON／liveness 寫成 def）、**只是換做法 3 個**；並明說其餘交付鏈知識完全可跨語言重用
- 教材規模：12 章 + 3 附錄 + 1 實戰＝**17 檔、7,773 行、278 個程式碼區塊、73 張表、214 個 wikilink**，驗收全數通過

## [2026-08-16] synthesis | FastAPI 補充篇 16–17（背景工作、韌性）— 修掉兩條斷鏈

- **起因是 grep 出兩條斷掉的前向引用**，不是新增題目：03 章寫「要進佇列，這件事第 11 章談」但 11 章沒談；05 章寫「重試策略（第 08 章）」但 08 章是 middleware/CORS/logging。且 .NET 那套有 `19-background-work` 與 `18-resilience-and-performance` 兩章對應，FastAPI 側全缺
- 編號決定：既有 12–14 是附錄、15 是實戰，新增章接在 16/17 並在 hub 表另立「補充篇」；**不重編號**以免破壞既有全部 cross-link
- `16-background-work`：開篇「三副本讓對帳跑三次、財務收到三封信」，點名根因是從單機帶過來的假設「這段程式碼只會有一份在跑」，且**沒有任何錯誤訊息**。四種做法邊界表 + 一句選擇規則「這件事掉了會怎樣」
  - 揭一個陰險的坑：**`asyncio.create_task` 裡的例外不會傳播**——任務靜默停止、log 空的、健康檢查綠的，且持有 task 參考連 `Task exception was never retrieved` 都不會印。對照 .NET 的 `BackgroundService` 例外會停掉整個 Host（至少你會知道）
  - Redis 鎖兩個不能省的細節：TTL（持鎖 Pod 掛掉會永遠鎖著）、**釋放要用 Lua 比對 token**（超時→鎖過期→別人拿到→你跑完 DEL 刪掉別人的鎖）；並誠實說明單一 Redis 在 failover 不保證互斥
  - 全章立論收在**冪等性**：佇列是 at-least-once、CronJob 的 Forbid 只擋並行、鎖在 failover 可能雙開——exactly-once 不存在，**唯一可靠策略是讓重複執行無害**。冪等鍵必須由呼叫端決定且穩定（用 `uuid4()` 等於沒有冪等性），唯一索引是保證、`if existing` 只是最佳化
  - outbox 模式解「DB commit 成功但入隊失敗」；投遞用 `_job_id=outbox:{id}` 讓 arq 去重、`FOR UPDATE SKIP LOCKED` 讓多投遞者並行
  - CronJob 只講兩個最常錯的（`timeZone` 不設是 UTC、`concurrencyPolicy: Forbid`），欄位完整推導指回 `practice-4-write-yaml-from-scratch` 避免重複
- `17-resilience`：開篇「下游沒掛只是慢十倍，你的服務全面 503」，用 04 章的數字實算——40 條 threadpool ÷ 2 秒 = 20 req/s，且**連不碰那個下游的 endpoint 也一起卡住**。提煉出「**變慢比掛掉危險**」（掛掉是快速失敗、資源立刻釋放）
  - 逾時定位為「唯一沒有它就全盤皆輸」的設定：httpx 四維度（connect 要遠短於 read）、**逾時會疊加**、`asyncio.timeout` 包整體、總逾時必須小於上游給的
  - 重試三紀律 + **重試預算**（3 次 × 5 秒 ≈ 16 秒，上游只等 10 秒的話後面是對沒人要的結果做工）；點名「沒有抖動的重試不是韌性機制，是一次同步化的 DDoS」
  - 斷路器要**包在重試外面**（否則三次重試被算成三次失敗）、每個下游一個、多副本不共用狀態可接受
  - 快取三層 + `cachetools` 非執行緒安全（threadpool 下要加 lock）+ 雪崩三解法（TTL 抖動→single-flight→提前刷新）+ 明列不該快取的三類（授權資料會讓撤權延遲生效）
  - 限流定位更正：**保護自己不是保護對方**，優先放 Ingress；並補第三層——**訊號量隔艙**，直接解決開篇問題且成本最低
  - 收尾給調參順序：逾時 → 隔艙 → 重試/斷路器 → 快取，並強調「先加快取常常只是把問題藏起來」
- 同步修掉兩條斷鏈為 wikilink；另 grep 確認殘留的「第 N 章」全是指向已存在章節的向後引用，非斷鏈，保留散文寫法
- 教材規模：**14 章 + 3 附錄 + 1 實戰＝19 檔、8,734 行、313 個程式碼區塊、81 張表、238 個 wikilink**，驗收全數通過

## [2026-08-16] lint | 全庫健檢（首次執行）

- 建立可重複執行的 `lint_vault.py`（scratchpad）：斷鏈／孤兒頁／frontmatter／BOM-CRLF／index 漂移／同名衝突六項；掃 379 個 `.md`（wiki/ 內 199），`.obsidian` 與 `.trash` 排除
- **wiki/ 編碼全數乾淨**（0 BOM、0 CRLF）。`raw/` 有 72+ 個 CRLF 但依規則永不修改，列為不處理
- 發現九項，已輸出報告交使用者裁決，**本次不自動修復**（依 CLAUDE.md 的 Lint operation 定義）
- 高：`aspnetcore-webapi-complete.md` 躺在 vault 根目錄（違反「同名資料夾」與「wiki 頁在 wiki/」兩條結構規範）；`building-lp-models/mathematical-programming-overview.md` 是只有一行標題的空殼，且與 `mathematical-programming-overview/` 下的 94 行正本**同名衝突**導致 wikilink 解析不確定
- 中：`資產配置與投資` 教材 08–14 + 附錄 A/B/C 共 10 份未寫（hub 已誠實標 ⬜，24 條斷鏈全源於此，屬已知待辦非缺陷）；`database-moc` 9 條、`web-backend-moc` 3 條、`tools-system-moc` 1 條斷鏈；`[[gitops]]` 全庫被提及 20 次卻無專頁（CLAUDE.md 定義的「缺漏概念」）
- 低：孤兒頁 2（`52-file-and-object-storage` 編號脫離 k8s-mastery 既有序列、`session-transaction-gtt`）；index.md 漏收 4 頁（cron-expression、hangfire、上述兩個孤兒）
- 觀察：`docker`／`vault`／`python`／`typescript`／`react` 五組 raw 與 wiki 同名，Obsidian 解析可能落到 raw 版；影響全庫導航但修法涉及大範圍改名，列入待裁決

## [2026-08-16] synthesis | 實戰 5：接上資料庫（loop 第一輪）

- 實戰篇原本停在 GitOps，但整套教材沒有一章講「應用怎麼接資料庫」——這是實戰鏈上最大的斷點，尤其使用者的 stack 是 Oracle
- `practice-5-database-and-state`：第一節先做「資料庫該不該進 K8s」的決策表，結論是已有 Oracle 主機就留在外面（含授權面與生態成熟度的誠實說明）；再分兩條路線
- 路線 A（連外部庫）：ExternalName / 直接設定 / 無 selector Service + EndpointSlice 三種接法與各自的能力邊界（ExternalName 只做 DNS，不受 NetworkPolicy 管）、`$(VAR)` 展開順序陷阱、egress NetworkPolicy 必須放行 DNS、Pod 來源 IP 被 SNAT 成 Node IP 對 DBA 白名單的影響
- **連線池乘法**（本章最實用）：資料庫連線數 = Pod 數 × 每 Pod 池大小，.NET Oracle 預設 100 × HPA 20 副本 = 2000 條，擴容本身就是壓垮資料庫的動作；給了從資料庫容量反推每 Pod 上限的公式，並點出 HPA maxReplicas 與批次 Job 都要納入計算
- Migration 三不可：不在應用啟動時跑（多副本競態）、不假設新舊版不共存（**expand-contract 三階段**改欄位名的完整推演）、不能沒有回滾計畫（只往前、破壞性操作前備份、兩階段間隔一個發版週期）
- K8s 沒有 depends_on 的三種處理方式對照，推薦「應用重試 + readiness 失敗」而非 initContainer 等待（後者每次重啟都要再等一次），並回扣實戰 1 堅持 liveness/readiness 分兩端點的價值
- 路線 B（跑在叢集內）：為何必須 StatefulSet（RWO Multi-Attach）、fsGroup 與 PGDATA 指子目錄兩個踩坑、備份不是快照就好、正式環境應該用 Operator 而非自己拼
- 10 個常見坑對照表 + 12 項檢查清單
- 教材規模：入門篇 6 + 實戰篇 5 + 正文 16 + 附錄 17，約 28.1 萬字

## [2026-08-16] synthesis | 實戰 6：可觀測性（loop 第二輪，實戰篇收尾）

- `practice-6-observability`：實戰鏈的最後一環——服務跑起來了，但「怎麼知道它好不好」
- 開場先定分工：**metrics 說「有問題」、logs 說「什麼問題」、traces 說「問題在誰身上」**，不從工具而從「要回答哪些問題」倒推
- Metrics：ASP.NET Core 用 OpenTelemetry 建置（之後加 traces 不用重來）、ServiceMonitor 接線、**「抓不到」的三個原因排序**（label 不符 serviceMonitorSelector 為第一名且完全無錯誤訊息、port 寫數字、namespaceSelector）、四個黃金訊號的實際 PromQL、`histogram_quantile` 必須先 rate 再 sum by (le)、高基數標籤（ID/完整路徑）會打死 Prometheus
- 特別強調 **CPU throttle 是四訊號裡最易漏的一個**：服務變慢但 Pod Running、probe 全過、日誌乾淨，不放進儀表板會查很久（回扣附錄 D 的實驗 A4）
- Logs：容器日誌路徑與 `kubectl logs` 的兩個限制、結構化 logging（樣板參數 vs 字串內插在事故當下的價值差）、trace ID 串接 metrics↔logs 並回傳給使用者、不該記的三類內容
- Alerting：只對「需要人立刻做事」告警、從 SLO 而非指標導出、給了六條可直接用的 PrometheusRule（含 CPU throttle 與資料庫連線數兩條「不會讓任何東西變紅」的告警）、`for` 去抖動、每條都要 runbook_url、page/ticket 分級
- 收尾強調 **沒有測過的監控等於沒有監控**，尤其 Alertmanager → Slack/Email 這一段最常安靜地斷掉，只有主動測試才會發現
- 10 個常見坑 + 11 項檢查清單
- 實戰篇至此完整：寫程式 → 容器化 → 部署 → 自動化 → 接資料庫 → 看得見
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 17，約 28.7 萬字

## [2026-08-16] synthesis | 附錄 K：成本優化與資源調校（loop 第三輪）

- 附錄 H 只談「該做什麼」，這份補「怎麼做」——多數叢集利用率 20–35%，浪費是結構性的（requests 拍腦袋填、填大沒代價、沒人回頭改）
- 三個數字先分清：allocatable / requests 總和 / 實際使用，導出**排程飽和度**與**真實飽和度**，兩者差距就是買到的空氣（典型 85% vs 25%）
- requests 調校方法論：**記憶體用 P99、CPU 用 P90**，理由是超限行為不同（一個 OOMKilled 立刻死、一個只是 throttle 變慢）；給了兩條可直接跑的 PromQL 算「實際用量 ÷ requests」與四段判讀表；VPA `updateMode: "Off"` 當免費建議引擎（明確建議不要用 Auto）；三條調整紀律與三種「不該調」的情況
- CPU limit 該不該設：這是社群有爭議的題目，給四列判準表而非單一答案，並回扣實戰 2 那份 manifest 為何只設記憶體 limit；記憶體 limit 則永遠要設（不可壓縮）
- 節點層：碎片化為何讓 70% 就排不進去（經驗法則：單 Pod requests ≤ 節點 allocatable 1/4）、大/小節點六項對照（含常被忽略的 systemReserved 佔比）、**autoscaler 縮不掉節點的四個原因**、spot 節點的適用條件與配套
- 孤兒資源盤點：七條可直接執行的指令（Released PV、未掛載 PVC、殘留 Job、無 endpoint Service、0 副本 RS、LoadBalancer、Pending Pod）+ registry/日誌/metrics 保留策略 + 跨區流量 + StatefulSet 縮容不刪 PVC 的提醒
- 成本歸屬：標籤規範先於工具（沒有一致標籤，OpenCost/Kubecost 也算不出可行動的報表），並用 ValidatingAdmissionPolicy 強制
- 10 個常見誤區 + 12 項檢查清單 + 四種頻率的節奏表
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 18（A–K），約 29.3 萬字

## [2026-08-16] synthesis | 附錄 L：多叢集與災難復原（loop 第四輪）

- 補上附錄 H 那句「沒還原過的備份等於沒有備份」的下文——整套教材原本沒有可照著跑的演練程序
- 開場先要求 **RTO/RPO 兩個數字**，並給「RTO 目標 → 需要什麼架構」與「RPO 目標 → 需要什麼備份頻率」兩張對應表，避免出現「花大錢做雙活但資料庫只有每日備份」這種不對稱設計
- **要保護的四層**：叢集狀態 / 工作負載定義 / 應用資料 / **叢集外依賴**。點出只有第 3 層真正不可再生（GitOps 讓 1、2 層可重建），而第 4 層（DNS、憑證、registry、Vault）最常被完全遺忘，是「叢集重建好了但服務還是不通」的根因
- 三種備份手段的分工與邊界：**etcd 快照救控制平面、Velero 救工作負載、資料庫備份救資料**；強調 etcd 快照必須連 `/etc/kubernetes/pki` 一起備（否則還原後憑證對不上，錯誤訊息全是 x509 完全不指向真因），以及 Velero 對資料庫要設 pre hook（直接快照執行中的 DB 得到的是當機瞬間狀態）
- **三個完整演練腳本**，每個含指令、驗收標準（不是「看起來有東西」）、預期耗時：A 誤刪 namespace（15 分，GitOps 環境可更快）、B 單一 PV 損毀（還原到旁邊的 namespace 而非直接蓋回，因為蓋回不可逆）、C 整座叢集重建（GitOps 路線六步 + etcd 快照路線五步，點出「第 2 步裝叢集層元件」最常被低估、DNS TTL 要提前調短）
- 四種多叢集拓撲對照表 + 三條選型建議（dev/prod 要分叢集因為需要可以弄壞的地方、主備的難點在資料不在 K8s、**雙活需要應用為它設計否則是資料損毀而非高可用**）；ApplicationSet cluster generator 與「管理叢集自己掛了怎麼辦」
- 演練節奏表（週/月/季/年）+ 四條紀律（計時、輪流執行、照文件做卡住就改文件、記錄耗時）
- 10 個誤區 + 12 項檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 19（A–L），約 29.9 萬字

## [2026-08-16] synthesis | 附錄 M：雲端網路與託管 K8s（loop 第五輪）

- 補上上次確認過完全空白的一塊，順帶完整回答使用者最初問的「AWS IGW」（當時選了 Istio 那個解讀，這輪把雲端那個也補齊）
- VPC 五件套：VPC/Subnet/Route Table/IGW/NAT Gateway，含 mermaid 流量路徑圖與 GCP/Azure 對應名詞
- **IGW 的三個關鍵**：public subnet 不是設定選項而是「route table 有 0.0.0.0/0 → igw」的推論結果；IGW 是 VPC 層級且雙向；只有路由不夠，實例還要有公有 IP 否則封包回不來
- NAT Gateway：單向、要放在 public subnet、單一 AZ 資源（高可用要每 AZ 一個）、按小時 + 每 GB 資料處理費
- SG vs NACL 四項對照，強調 NACL 無狀態容易寫出「進得來出不去」，且雲端 SG 與 K8s NetworkPolicy 是**疊加**的兩層
- **Pod IP 兩種模型**（本章最重要）：Overlay vs VPC 原生。VPC 原生（EKS 預設）帶來兩種 IP 耗盡——subnet CIDR 不夠（建立後不可改）、以及**單節點 ENI×IP 額度上限與 CPU/記憶體無關**，這是「節點資源還很多但 Pod 排不進去」的真因；三個解法（換機型/prefix delegation/secondary CIDR）
- `type: LoadBalancer` 背後：cloud-controller-manager 的角色、`<pending>` 三個排查順序（controller/subnet ELB 標籤/配額）、NLB vs ALB vs **NLB+ingress-nginx 收斂**（每個 LoadBalancer Service 都是獨立計費資源）、`externalTrafficPolicy` 在雲端的具體後果與 IP 目標模式
- IRSA/Workload Identity：不該把權限掛節點 instance profile（該節點所有 Pod 都拿到，等於繞過 RBAC）；OIDC 信任鏈與正文第 8 章的 Vault 信任鏈同構；三雲的 SA annotation 對照；aws-auth ConfigMap → Access Entries
- EBS 綁單一 AZ 導致必須用 `WaitForFirstConsumer`，並作為「有狀態服務留在叢集外」的另一個支撐理由
- 雲端特有成本陷阱五項（跨 AZ 流量、NAT 資料處理費、LB 數量、未刪 EBS、跨區傳輸）+ VPC Endpoint 的實際效益
- 12 項遷移檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 20（A–M），約 30.5 萬字

## [2026-08-16] synthesis | 附錄 N：eBPF 與 Cilium（loop 第六輪）

- 補上教材裡只出現過名字的一塊。定位刻意保守：**多數團隊不需要換**，這份的價值是判斷依據而非推銷
- Part 1 先講 kube-proxy 的**結構性極限**（規則數與 Service 數成正比、規則同步要重算整份、同步期間流量可能送到已消失的 Pod），說明 IPVS 只改善了查找沒改善同步
- Part 2 eBPF 白話原理：讓小程式掛進 kernel 而不必改原始碼／寫模組；**verifier** 靜態檢查（無界迴圈、非法記憶體）是它能被廣泛採用的根本；四種 hook 點；**eBPF map 的 O(1) 查找與單筆更新**正好對應 Part 1 的兩個問題
- Part 3 Cilium 能力：kube-proxy replacement、**identity-based 安全模型**（依標籤算出安全身分，一萬個 Pod 五十種標籤就只有五十個身分，政策規則數與 Pod 數脫鉤，重建擴縮不必重算）、L7 政策（走 Envoy 有開銷）、`toFQDNs`（含「必須讓 DNS 查詢經過 Cilium 的 DNS 規則」這個最常見失敗原因）、Hubble 回答「為什麼被丟掉」、ClusterMesh／Egress Gateway／透明加密
- Egress Gateway 特別對照實戰 5 的「DBA 要放行所有 Node IP」——用它可收斂成單一固定出口 IP，是可量化的維運改善
- Part 4 誠實判準表七列 + 明說換 CNI 是高風險操作（牽動所有 Pod 網路、需重啟與維護窗口），新建叢集才是 Cilium 的合理預設
- Part 5 與標準 NetworkPolicy 的欄位對照表，並點出 Cilium **同時支援標準 NetworkPolicy** 所以可漸進遷移；以及 namespace 選取語意不同、轉換要逐條驗證不能憑印象翻譯
- Part 6 遷移八步 + `cilium connectivity test`；強調「一次只改一個變數」（別同時換 CNI 又取代 kube-proxy）
- 10 個常見誤解（含「eBPF 寫錯會讓 kernel 當掉」「Cilium 可取代 service mesh」「新技術所以該換」）
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 21（A–N），約 31.1 萬字

## [2026-08-16] synthesis | 附錄 O：平台工程與多團隊治理（loop 第七輪）

- 教材原本全部從單一團隊視角寫，但使用者的目標角色是公司 K8s 管理員——「另外五個團隊要部署而他們不會 K8s」是完全不同性質的問題
- 開場給三條路的對比：代寫（自己變瓶頸）／叫他們自己學（五種寫法、基線參差）／**做平台**（把正確做法變成預設值）
- 責任邊界表十列 + 三條劃線原則：**應用團隊必須擁有自己的 YAML**（代寫會被鎖死在維護別人的 manifest）、平台提供預設值不提供決策、**能自動強制的就不要靠 review**
- Golden path 的定位：**最好走的路不是唯一的路**，偏離要付出成本但不禁止；一份內部 Helm chart 當安全基線的載體（應用團隊只寫十幾行 values，chart 自動產生 securityContext/probe/preStop/PDB/ServiceMonitor），並提醒它是所有服務的共同依賴要當正式產品維護
- Namespace 自助化：把「一個 namespace 該長什麼樣」變成宣告檔 + PR 流程，附完整 YAML（Namespace+PSA label / ResourceQuota / LimitRange / default-deny NetworkPolicy / RoleBinding）；三個設計決定——**quota 與 LimitRange 必須成對**（否則忘寫 requests 被拒且錯誤藏在 ReplicaSet condition）、`services.loadbalancers: "0"` 強制走共用 Ingress、**給 `edit` 不給 `admin`**（不能自行提權）
- 隔離七維度對照表（權限/資源/網路 namespace 夠，節點/控制平面/kernel/CRD 要拆叢集）+ 五種必須拆叢集的具體情況 + 共用叢集的隱形共用資源（CoreDNS/Ingress/API Server）與 APF 的用途
- 政策即程式碼：三層工具選擇、ValidatingAdmissionPolicy 實例（成本標籤/記憶體 limit/禁 latest）、**該擋什麼的優先序清單**、以及 **audit → warn → enforce 的導入節奏**（直接 enforce 會讓既有工作負載全掛且錯誤訊息對新手極不友善）
- 不當瓶頸的三個做法：**三次法則**（同問題問三次就做成自助，含四種問題性質對應的產出）、支援分層（刻意不設一對一私訊，公開頻道回答讓下一個人搜得到）、**平台自己也要有 SLO**（才有依據拒絕無止盡臨時請求）
- 度量用 DORA 四指標 + golden path 採用率 + 自助完成率；點出**採用率低代表範本不好用而不是團隊不配合**
- 10 種失敗模式，其中「抽象漏水」展開說明：好的平台不是讓人永遠不必懂底層，而是不需要懂時不必懂、需要懂時查得到
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 22（A–O），約 31.7 萬字

## [2026-08-16] synthesis | 附錄 P：安全事故應變與供應鏈（loop 第八輪）

- 正文第 8 章講的全是預防（認證/授權/准入），教材完全沒有「已經出事了怎麼辦」；這份補應變，並補上預防裡最後一塊：供應鏈
- 開場立一個原則：**安全事故當下最大的敵人是慌張造成的證據破壞**
- 供應鏈：基底映像四選項對照（distroless 的價值是「沒有 shell 大幅提高入侵者成本」）、digest 釘選、掃描三位置（PR/建置後/**registry 定期重掃**，因為今天乾淨不代表明天乾淨）、「擋還是報」的務實判準與**豁免必須有到期日**、SBOM 的價值用 Log4Shell 情境說明、cosign 簽章與 admission 強制驗章
- 機密外洩：三種洩漏管道；**映像層刪不掉東西**所以 `COPY` 進去再 `RUN rm` 無效、唯一修法是重建；**處置順序先輪替再清理**（多數人直覺相反——清 git 歷史期間密碼仍有效，且無法確定沒人看過，正確心智模型是「外洩即已失效」）；六類憑證的輪替方式表
- 叢集被入侵：偵測訊號表（**挖礦是最常見形態**，特徵是 CPU 滿載 + 連礦池 + 偽裝成正常名稱）；**第一小時不要 `kubectl delete pod`**（毀證據且 controller 會重建一個一樣被入侵的）；正確順序隔離→蒐證→評估→清理，含 quarantine NetworkPolicy 與「改掉 app 標籤讓 controller 補新 Pod、可疑 Pod 變孤兒留存」的技巧、七條蒐證指令、用 `auth can-i --list` 評估被盜身分的權限決定災情大小、節點可能被逃逸影響時**重建比清理可靠**
- 容器逃逸六條路徑（全部是設定給的不是漏洞給的）、PSA `restricted` 一個 label 消滅絕大多數、但涵蓋不了 kernel 漏洞；附兩條盤點現有 privileged/hostPath Pod 的指令
- audit log 五種調查查詢方向；強調**必須送到叢集外**否則攻擊者取得節點就清掉
- 事故後：通報義務要事前寫進 runbook；檢討四問，其中「同一類問題還有哪些地方存在」最有價值
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 23（A–P），約 32.3 萬字

## [2026-08-16] synthesis | 附錄 Q：效能問題定位（loop 第九輪）

- 「慢」原本散在第 13/14 章與附錄 K，沒有一份把它當主題。這份從使用者感受的延遲一路往下拆到根因
- 核心方法一句話：**先確認慢在哪一段，再深入那一段**；把延遲拆成六段（客戶端/Ingress/Service 網路/Pod/應用/下游）並給各段量測方式，其中 nginx `$request_time` 減 `$upstream_response_time` 可分離「nginx 自己排隊」與「後端慢」
- **先問四個問題**（花五分鐘常直接指出方向）：全部慢還部分慢（依 route 拆）、持續還尖峰、**什麼時候開始的**（對照 rollout history 與 events，最有效率的一問）、平均慢還尾端慢（P50 vs P99 根因完全不同）
- 逐層排查 L0–L5，每層給 PromQL 或指令。**L3 的 CPU throttle 是頭號嫌疑犯**，並解釋反直覺的關鍵：CFS 以 100ms 為週期，`limit: 500m` 表示每 100ms 只有 50ms 額度，需要密集運算 80ms 的請求會被凍結到下個週期——**所以平均 CPU 用量低仍可能大量 throttle，要看 throttle 比率不是使用率**
- 補 conntrack 表滿（症狀是隨機丟包逾時、不對應任何應用層錯誤）、吵鬧鄰居的判斷法（依 Pod 拆開看延遲）、連線池排隊（應用不忙 DB 不忙但在等連線，實戰 5 的乘法反方向也成立）
- **尾端延遲六因**表：GC pause／CPU throttle／連線池排隊／冷啟動／**重試放大**（Istio 預設就重試，一次失敗變三次，形成正回饋）／慢節點
- 三個完整推演（部署後 P95 變四倍→CPU limit 被調小；只有早上九點慢→HPA 頂到 max 且 DB 連線也接近上限，兩問題疊加；偶發五秒→ndots 造成 CoreDNS 過載），示範「四問定位→針對該層驗證」而非猜測
- 平時準備四件事：日誌帶延遲分解、儀表板固定五格（含 throttle 比率）、分散式追蹤、**記錄基線**（沒有基線連「有沒有變慢」都證明不了）
- 10 個誤區 + 排查與準備兩份檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 24（A–Q），約 32.9 萬字

## [2026-08-16] synthesis | 附錄 R：Operator 與有狀態工作負載（loop 第十輪）

- 正文第 9 章講機制（CRD/webhook/finalizer/ownerReference），這份講「什麼時候該做、怎麼做」，並明確立場：**多數團隊需要的是知道什麼時候不該寫 Operator**
- 決策階梯（Helm → Helm hooks → 既有 Operator → 自己寫）與單一判準：**有沒有「需要持續執行的運維知識」**；實用反問「如果沒有人在，這件事還需要發生嗎」
- Operator 成熟度五級表，用途是自我檢查——只做到 L1/L2 的話跟一份 Helm chart 沒有明顯差別但多一個要維護的元件，**價值從 L3（備份、故障轉移）才開始**
- 選用既有 Operator 的七項檢查，其中**逃生門**（移除它之後資料與服務怎麼辦、能否退回手動管理）最常被忽略也最重要；權限範圍要限縮不接受 cluster-admin
- 自己寫的六個設計原則：reconcile 冪等（反例：無條件 Create 造成資源無限增生）、**level-triggered 而非 edge-triggered**（事件會漏會重送）、status/spec 嚴格分離（controller 寫 spec 會無限迴圈）+ status 子資源與 observedGeneration、錯誤處理與 requeue 節奏（永久性錯誤不該無限重試）、finalizer 三紀律（冪等、失敗要寫進 status、**文件要有手動移除程序**）、**能用 ownerReference 就不用 finalizer**（GC 比 finalizer 可靠）；附八個常見坑
- StatefulSet 運維手冊：擴縮容與 PVC 保留/重新綁定的行為、**`partition` 做金絲雀**（比 Deployment 滾動更新可控）、`--cascade=orphan` 改不可變欄位的手法**與它的邊界**（不能真的換 PVC 的 StorageClass）、擴充儲存要逐個 PVC 改且只能調大、主從切換 StatefulSet 不管（正是 Operator 的用武之地）
- 工具選擇表，特別點出 **Operator SDK 的 Helm 模式**（L1/L2 需求完全不用寫 Go）與 kopf/shell-operator 適合內部簡單自動化
- 10 個誤區 + 四組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 25（A–R），約 33.5 萬字

## [2026-08-16] synthesis | 附錄 S：進階排程與批次工作負載（loop 第十一輪）

- 第 7 章的排程機制預設場景是線上服務，這份補「非典型工作負載」：批次、分散式訓練、GPU、spot
- 線上 vs 批次五項對照，說明混跑同叢集對成本有利但需要明確的優先級與資源邊界
- 優先級：**七層 PriorityClass 分配建議**（事先規劃而非隨手取值）、`preemptionPolicy: Never` 對批次的意義（排隊有優先序但不打斷別人）；搶佔三個副作用——被搶佔是驅逐不是暫停、**PDB 對搶佔只是偏好對 drain 才是硬約束**（很少人知道的差異）、層級太密會連鎖；優先級通膨用 RBAC + quota `scopeSelector` 防（比禁止務實）
- Gang scheduling：先講死鎖長什麼樣（8 個 worker 排上 6 個 → 互等且佔資源）、K8s 原生沒有；**Kueue 用 Job 的 `suspend` 欄位實作**（不取代 scheduler，只在前面加一道准入），附 ResourceFlavor/ClusterQueue/LocalQueue 三物件範例與佇列借用
- GPU：三條硬規則（requests=limits、不能小數、不能只寫 requests）、**一張卡預設只能一個容器**、time-slicing vs MIG 對照（前者無顯存隔離不建議用於訓練）、GPU 節點必須加 taint、**監控實際使用率而非分配率**（分配 100% 但使用 20% 很常見，是附錄 K 的 GPU 版本且金額大得多）
- Spot 跑批次五個配套，其中 **`podFailurePolicy` 把被搶佔造成的失敗排除在 `backoffLimit` 之外**最關鍵（不設的話幾次回收就把 Job 判定失敗）
- 分散策略：topologySpreadConstraints 優於 podAntiAffinity 的四項理由；**`matchLabelKeys: [pod-template-hash]` 在滾動更新時必要**（否則新舊 revision 混算導致更新卡住）——很難自己想到但踩到很難查；`IgnoredDuringExecution` 只在排程當下檢查
- `FailedScheduling` 訊息七種關鍵字對照表（訊息幾乎總是直接給答案）+ 兩個 scheduler 層級指標
- 五組檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 26（A–S），約 34.1 萬字

## [2026-08-16] synthesis | 附錄 T：Chart 設計與內部共用（loop 第十二輪）

- 第 10 章講「用 Helm」，這份講「設計一份給別人用的 chart」，直接接上附錄 O 的 golden path 載體
- 核心心智模型：**chart 是 API、values.yaml 是它的介面**；五項對照說明自用與共用 chart 的本質差異，導出判準「每加一個 values 欄位前先問我準備好永遠支援它了嗎」
- 介面設計：最小可用要在五行內（要三十行的話使用者會複製別人的 values 而不理解，安全基線跟著失效）、命名對齊社群慣例、**逃生門決定採用率**（沒有 extraEnv/extraObjects 使用者只能 fork，之後基線更新推不到他們身上）、`values.schema.json` + `required` 讓錯誤訊息指向具體欄位
- 實作：**`labels` 與 `selectorLabels` 必須分開**（selector 不可變，含 version 會讓升級被拒且只能刪掉重建）、checksum annotation 內建、**`lookup` 是陷阱**（ArgoCD 用 helm template 沒有叢集連線，一律回空，「沿用既有 Secret」邏輯每次走 else 產生新密碼——無聲的資料破壞），結論是不要在 chart 裡產生機密
- library chart（`type: library`）作為多 chart 共用安全基線的正確結構；subchart 三陷阱（values 作用域與 global、生命週期綁在一起、條件啟用導致開發與正式跑不同架構），判準是「跟應用生命週期一致且不含重要資料」才用
- 版本：`version` vs `appVersion` 分工與 ArgoCD 靠 `version` 判斷重新渲染、SemVer 三級對 chart 的具體意義、**破壞性變更三步**（並存 → 公告 → 用 `fail` 給遷移訊息；直接移除會讓設定被靜默忽略，比報錯難查）
- Helm×ArgoCD：根本差異是 ArgoCD 用 `helm template` 不是 `helm install`，列出六項行為差異表與四個具體的坑（隨機值造成永遠 OutOfSync、`lookup` 靜默失效、hook 語意不等價、Helm `crds/` 升級不更新）、建議配置含 `forceString` 解型別陷阱
- CI 測試五道（lint/template/kubeconform/kube-linter/unittest）+ `ci/` 多組代表性 values；點出「測錯誤訊息是否清楚」正是共用 chart 的品質指標
- 五組檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 27（A–T），約 34.7 萬字

## [2026-08-16] synthesis | 附錄 U：從既有系統遷移上 K8s（loop 第十三輪）

- 教材原本假設應用已在 K8s 或即將部署（實戰篇甚至從乾淨專案開始），但多數公司真正面對的是「把跑了三五年的系統搬過去」——原作者可能已離職、依賴沒有文件、不能停
- **Part 0 先問該不該搬**：好理由五項 vs 不是理由三項，加上六類該留在原地的系統（一年一次的批次、授權綁硬體、特殊硬體、已排定汰除、延遲極度敏感、資料庫）；明確立場「**不搬是合法的專案結論**」
- 盤點三件事：應用清單與依賴圖（**「有沒有可重現的建置流程」最關鍵**，很多老系統是某台機器編出來的）、容器化難度七維度評分表找試點、**隱性依賴要用觀察而非詢問**（問「有什麼依賴」的答案通常是「沒有」；改用看那台機器還跑什麼、看排程工作清單、測試環境斷網一次）
- 三波節奏：**試點選難度最低且非關鍵的系統**（第一個專案的目標是建立能力不是創造價值），第一波產出是可複製的 chart + CI/CD + runbook 樣板而不只是「一個服務上線」；第二波同類推廣驗證樣板；第三波困難個案，且可以回頭用 Part 0 重新判斷
- 應用要改的五件事（設定外部化、日誌改 stdout 含 sidecar 妥協方案、檔案儲存三選項、session 外部化、**排程工作抽成 CronJob** 順便解決「排程藏在 OS 設定裡沒人知道」）；並提醒「RWO + 單副本」是合理的分階段起點但**要記錄成技術債否則三年後還是單副本**
- 流量切換：三種並行方式（影子/權重/依使用者），**影子流量對有副作用的請求會送兩次訂單**；**優先用前置代理而非 DNS**（TTL 讓回滾速度不受控）；回滾點設計四問；**雙跑期盡量共用資料庫**（不同資料庫的雙寫同步是整個專案最容易出錯的部分）
- Windows 應用三條路對照，指出「改寫成現代 .NET 的成本常被高估」；Windows container 的五項現實限制與 nodeSelector/toleration 配置
- 專案節奏：每一波五項驗收（含「穩定兩週涵蓋月結」「runbook 由他人驗證」「**舊環境有明確關閉日期**」），三個該停下來檢討的訊號（同類問題重複＝樣板有問題、事故頻率高於舊環境、**團隊開始繞過流程＝設計問題不是紀律問題**）
- 10 種失敗模式 + 四階段檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 28（A–U），約 35.3 萬字

## [2026-08-16] synthesis | 附錄 V：知識傳承與團隊能力建立（loop 第十四輪）

- 附錄 O 講平台的技術與制度，這份講人。是整套教材唯一一份不談技術的，但對 K8s 管理員的實際處境影響很大
- 開場用三題自測（請假兩週誰處理 P1、離職後公司剩什麼、上次有人獨立完成生產變更是何時），並點出「**只有我會在短期是安全感，長期是負債**」——它讓你無法休假、無法做更高價值的事，組織也會把你困在原地
- **分層而非全員學全部**：四種角色的「必須會 / 不必會」對照表，明確主張「一般開發者不需要懂 etcd」——要求所有人學到平台工程師深度的實際結果是沒有人學
- **用本教材設計的四條培訓路徑**，各附時數估計與驗收方式：開發者 8–10h、資深開發 +10–12h、值班 +8h（**唯一該用實作測驗驗收的路徑**，且附錄 D 的 20 個實驗必做）、平台工程師 3–6 個月且必須配合實際維運
- 文件四分法（教學/操作指南/參考/說明），並指出**本教材本身就是這個分類的實踐**（入門篇/實戰篇/附錄 C/正文）；最常見錯誤是把 runbook 寫成教學；四類不該寫進文件的資訊與判準「已有權威來源就指向它不要複製」（過期的文件比沒有文件更危險）
- 五種讓知識流動的機制：輪值（新人 shadow→陪同→獨立三階段、**事故指揮也該輪流**）、**配對排錯**（把「我來處理」換成「我陪你處理一次」是最直接的槓桿）、事故檢討當教材（正文第 13 章的 19 案例即此產物）、分享用 live 排錯而非投影片、**用「新人第一週能否自己部署」當品質指標**
- 防腐：**用可執行的東西取代文件**（policy/CI/PDB/告警/腳本+演練六項對照），因為可執行的東西不會過期——要嘛能跑要嘛壞掉被發現；剩下真需要文件的用輕量決策紀錄
- 你自己該改的四件事：不當唯一解答者、刻意讓別人做、把推理過程說出來、**定期休假且真的不接**（唯一誠實的測試；不測試的結果是永遠不知道自己多脆弱，而非計畫性缺席不會事先通知）
- 10 種失敗模式 + 五組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 29（A–V），約 35.9 萬字

## [2026-08-16] synthesis | 附錄 W：微服務拆分與服務間通訊（loop 第十五輪）

- 附錄 C-7/J 講 Istio 怎麼用，但跳過更前面的問題：該把系統拆成幾個服務。K8s 讓「多開一個服務」變容易，而**容易不等於該做**
- 先攤成本：單體內一次函式呼叫拆開後變網路呼叫的五項差異表，其中「**逾時之後你不知道對方做了沒**」是最根本且無完美解的難題；每多一個服務的固定成本（CI、監控、on-call、版本、文件）**幾乎與服務大小無關**，所以「拆越細越好」是錯的
- **模組化 ≠ 分散式**：邊界沒想清楚的單體拆開會變成邊界沒想清楚的分散式系統；正確順序是先在單體裡劃清模組邊界並確認穩定
- 六個好理由（獨立擴縮/發布節奏/團隊邊界/技術棧/故障隔離/合規）全部是**營運面而非程式碼面**；四個壞理由；實用判準「永遠一起部署、一起擴縮、同一人維護 → 不該是兩個服務」
- 怎麼拆：沿業務邊界而非技術層次（拆成 UI/邏輯/資料會讓任何變更都要動三個服務）、**資料所有權才是真正的邊界**（共用資料表＝分散式單體，同時有兩者缺點）、Strangler 漸進且每步可回滾
- 四種通訊模式對照表；同步呼叫的**可用性相乘**（三個 99.9% 串起來是 99.7%）與 gRPC 長連線黏在同一 Pod 的 K8s 具體坑；非同步是「複雜度轉移而非消失」；共用資料庫僅在遷移過渡期可接受且必須有結束日期
- 分散式五堂必修課：逾時必填且要小於上游、重試三條件（冪等/退避抖動/上限）且**要知道整條鏈有幾層在重試**、斷路器、**冪等鍵只能在應用層做**、分散式追蹤從加分變必要
- **mesh 能與不能**兩張表，重點在後者（邊界劃錯、資料一致性、冪等、依賴鏈長度、共享資料庫耦合都幫不了）；結論「加 mesh 不會讓爛的拆分變好，只會讓你更清楚看到它有多爛」；並給輕量替代組合（Gateway API + 函式庫 + NetworkPolicy）
- Part 7 反向討論**何時該合併服務**（五個訊號），立場是「合併是修正決策不是失敗」
- 三組檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 30（A–W），約 36.5 萬字

## [2026-08-16] lint | 教材導航健檢 + 附錄 X 進階題庫（loop 第十六輪）

- 寫到 59 份、36.5 萬字，停下來做全面盤點而非再加新主題
- 新增可重複執行的 `audit_navigation.py`（scratchpad）：檢查孤兒頁、總目錄/index 漏列、入站連結數、以及「第 N 章」交叉引用是否超出正文範圍
- **健檢結果**：0 孤兒頁、總目錄與 index 零漏列、無錯誤章節引用。但浮出真實弱點——**最新九份附錄（36–45）入站連結都只有 1**（僅總目錄連到），縱向導航健全但橫向發現路徑不足：讀第 5 章的人不會發現附錄 N，讀第 8 章的人不會發現附錄 P
- 修法：以腳本批次為 12 個核心章節/附錄補上 24 條側向連結（05→N/M/W、07→S/K/Q、08→P、09→R、10→T、13→Q/G/P、01→U/W、12→L/E、14→Q/實戰6、04→R/S、30→V/P/U、37→T/V），最低入站數由 1 提升到 2–3
- 第二個缺口：**附錄 A 的 144 題只涵蓋正文 16 章**，後來新增的實戰篇 6 章與附錄 E–W（20 份、約 13 萬字）一題都沒被考過
- 新增 `46-advanced-self-assessment`（附錄 X）：**75 題**分七組（實戰篇 21／升級棄用 5／Ingress+狀態 10／維運成本 7／DR+雲端 8／平台安全效能 14／Operator+排程+Chart+遷移 10），難度標記 🟢3 / 🔵33 / 🔴43，全部針對「答錯會造成實際損失」的判斷而非名詞背誦；收尾附 **30 條紅色警戒濃縮清單**
- 每題答案都帶回對應文件的 wikilink，答錯可直接跳去複習或做附錄 D 的對應實驗
- 在附錄 A 開頭加上指引，說明它的涵蓋範圍與附錄 X 的分工
- 修正兩處 `<details>` 標籤打錯（寫入時誤植），驗證 75/75 配對正確；並修正 index.md 條目編號亂序（46 插到 45 前面），現已完整遞增 0–46
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 31（A–X），約 37.2 萬字

## [2026-08-16] synthesis | 附錄 Y：API 演進與版本管理（loop 第十七輪）

- 附錄 W 講服務怎麼溝通，但沒講「介面怎麼變」——那是拆分之後最持久的痛，而單體裡有編譯器當安全網、拆開後完全消失
- 三個結構性原因：不再控制所有呼叫方、**部署不是原子的**（滾動更新期間新舊必然並存）、呼叫方升級節奏不受控。導出原則：任何介面變更都要假設舊呼叫方會存在一段比你以為更長的時間
- 破壞性變更 11 列判定表，特別警告 **「改變欄位語意」是最陰險的一種**（型別沒變、名稱沒變，schema diff 與契約測試都抓不到，但下游帳全錯）——必須當成移除+新增處理；並說明「加欄位」在呼叫方嚴格反序列化時也是破壞性的
- **相容性有兩個方向**：向後相容（提供方負責）與**向前相容（呼叫方負責）**，後者常被忽略但它決定了你能不能安全加欄位。給了 Tolerant Reader 四條與 C# 對照範例，並建議把它訂成團隊規範
- 版本化三策略對照，先強調 **多數變更根本不需要新版本**（版本化是給破壞性變更的最後手段）；K8s 上 URL 路徑版本最務實因為可直接在 Ingress 分流
- 多版本並存三做法（兩個 Deployment + Ingress 分流 / 單一 Deployment 內部分派 / Istio header 分流）含完整 YAML 與判準；點出**兩版共用資料庫要走 expand-contract，而這正是「並存必須有結束日期」的實際原因**（schema 被鎖住）
- 棄用四步，核心是**順序**：使用量監控（含呼叫方維度）必須**先於**公告就位，否則時程只能靠猜；附 PromQL、`Deprecation`/`Sunset` (RFC 8594) header、主動聯繫、軟性降級、關閉時回 **410 而非 404**；各對象時程表（行動 App 要一年以上）
- 內部 vs 外部 API 五項對照，反駁「內部 API 可以隨便改」——團隊一多協調成本接近外部，而內部通常更沒有監控與契約
- CI 防護：單元測試抓不到破壞性變更（改欄位時測試也一起改了）；建議 OpenAPI diff 擋 PR + metric 帶版本與呼叫方標籤，兩者都是幾小時工作量且覆蓋大部分風險
- 四組檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 32（A–Y），約 37.8 萬字

## [2026-08-16] synthesis | 附錄 Z：測試策略在 K8s 上的落地（loop 第十八輪）

- 教材寫到第 61 份完全沒講過測試。定位刻意收窄：不談應用測試本身，只談「介於應用測試與上線之間、只有在 K8s 環境才會發現的問題」
- **先分清楚每個測試在驗證什麼**（應用邏輯／部署設定／叢集行為）——絕大多數屬於前兩類而**前兩類不需要叢集**；把它們搬出叢集，CI 會快十倍且穩定得多。實用反問：「這個測試失敗是誰要修？」
- 不需要叢集：Testcontainers 取代共用測試資料庫（乾淨、可平行、免維護長期環境）；CI 五道靜態驗證（kubeconform / kube-linter / conftest / helm unittest / **渲染後再驗一次**——最後這道常被忘記，模板產出無效 YAML 是常見 bug）；並說明 conftest 與 admission policy 是互補（CI 擋回饋快、叢集擋是最後防線）；政策本身也要測
- 需要叢集：CI 用 **kind**，四種「只有真部署才驗證得到」的測試——部署驗證（抓 selector 對不上、映像拉不到、ConfigMap 引用錯）、**`kubectl auth can-i` 當測試斷言**（讓「權限沒被意外放寬」變成可自動驗證）、NetworkPolicy 實際打一次（寫了沒生效的重災區）、滾動更新不掉請求（附錄 D 實驗 A6 的自動化版）；並明列 kind 與真實叢集的四項差異
- 預覽環境：兩種做法對照（per-PR namespace vs vcluster）、ArgoCD `pullRequest` generator 完整 YAML（**PR 關閉自動清理是最大優勢**）、三個要想清楚的問題（資料策略三選項、成本控制五手段、存取控制別讓未上線功能公開）
- **環境差異七列表，核心主張是「能消除的必須消除」**——測試環境用 Flannel 正式用 Calico，NetworkPolicy 測試等於沒測；沒開 PSA 會在上線那天才發現 Pod 起不來。另誠實列出「測試環境永遠測不到的六件事」，並指出它直接對應到附錄 H 的監控設計
- 上線後也是測試：部署後 smoke test 失敗即回滾（驗證的是含 Ingress/憑證/DNS 的真正正式環境）、**金絲雀的本質是用真實流量測試但限制爆炸半徑**、合成監控抓「Pod 都健康但使用者流程斷了」
- 混沌工程：點出附錄 D 就是手動版；判準是「系統是否穩定到隨機殺 Pod 不會有人注意到」，還沒到就別自動化（只會製造處理不了的噪音）；五階段由小到大
- 六組檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 33（A–Z），約 38.4 萬字

## [2026-08-16] synthesis | 新教材開工：資產配置與投資（給工程師的第一本理財書）

- 新主題，與既有 wiki 完全無交集。目標讀者設定為「科技業工程師 + 投資完全新手」，`wiki/tech/concepts/資產配置與投資/`（frontmatter `domain: personal`，路徑依使用者指定）
- 先完成全書大綱再動筆：四部 15 章 + 3 附錄。第一部認清處境（人力資本／盤點／報酬／風險）、第二部積木（資產類別／ETF／相關性）、第三部組裝（配置模型／台灣落地／RSU／執行）、第四部長期作戰（行為／稅保／自己算／檢查清單）
- 本輪產出：總目錄 + 第 0 章 + 第 1 章
- **第 0 章的核心論點**（整本書的起點）：工程師最大的資產是人力資本（約 2000~3000 萬，是金融資產的十倍），而它是一個完全未分散的科技業部位；更關鍵的是它與股市**同時受傷**——裁員那年就是組合最慘那年。導出「資產配置要看的是職涯 + 金融資產的整體風險」。另釐清 Brinson「90%」是解釋報酬的時間變異而非獲利來源
- 第 1 章的核心：**儲蓄率在前十年勝過報酬率**（兩組試算對照：儲蓄率 10%→25% 的效果大於報酬 4%→10%，且前者可控後者不可控）；地基四件事的嚴格順序與利率分界表；緊急預備金科技業建議 6~12 個月（理由同上：失業與股災同時發生）；投資型保單為何兩邊都不夠好；勞退自提的節稅誘因與流動性代價
- 全書刻意排除：推薦標的、預測市場、選股／技術分析、槓桿與衍生品。所有稅制數字都標註「以當年度公告為準」

## [2026-08-16] synthesis | 附錄 AA：事件驅動與訊息系統（loop 第十九輪）

- 附錄 W 把非同步訊息列為四種通訊模式之一就跳過了，這份把「複雜度轉移到哪裡」展開；聚焦 K8s 環境特有的三件事：consumer 怎麼擴縮、優雅關閉、at-least-once 逼出的冪等
- 先問要不要用：四項能力 vs 三項代價；明確指出**為了「重試」而引入訊息系統是錯的**（同步呼叫 + 重試與斷路器就夠）
- 選型：Kafka（可重播的日誌）vs RabbitMQ（佇列）的**根本差異是「能不能重播」**，八項對照；雲端優先用託管（同實戰 5 的決策邏輯）；**絕對不要自己拼 StatefulSet 跑 Kafka**（broker 重啟順序、partition 搬遷、controller 選舉全要自己寫）
- Broker 設定四要點：`min.insync.replicas: 2` 配三副本、**JVM 堆積不要等於記憶體 limit**（Kafka 依賴 page cache）、`deleteClaim: false` 當逃生門、跨 AZ 分散
- **Consumer 不是 HTTP 服務**（本章核心）：沒有請求進來造成三個具體問題——CPU 指標的 HPA 完全不動（佇列堆十萬筆）、readiness 語意不同、優雅關閉的時間需求差一個量級；解法是 KEDA 依佇列深度擴縮（含完整 ScaledObject），並點出 **Kafka 的 partition 數是並行硬上限**（6 個 partition 擴 20 副本會有 14 個閒置，且 partition 只能增不能減）
- 訊息語意必修：at-least-once 是預設且重複來源有四種 → **冪等只能在應用層做**（同附錄 W 的「mesh 無法讓重試變安全」）；順序保證只在 partition/queue 內，且順序與吞吐是取捨；poison message 會卡住整個佇列 → DLQ，但**DLQ 不是垃圾桶是待辦清單**（要監控、要有人看、要能重新投遞）；背壓三個方向，最糟的是沒有明確決定
- 可觀測性：六項指標，**consumer lag 最重要**，且**告警要對「持續成長」而非絕對值**（尖峰時 lag 衝高是正常的）；trace context 要跨越訊息邊界否則追蹤斷開
- 12 個常見設計錯誤 + 五組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 34（A–Z + AA），約 39 萬字

## [2026-08-16] synthesis | 資產配置教材第 2-3 章：報酬來源與風險真義（loop 第二輪）

- 第一部（認清處境）完成。這兩章刻意不碰任何產品，先把「報酬從哪來」「風險是什麼」講清楚，後面所有決定都靠這兩章的概念
- **第 2 章核心**：用 Bogle 三來源拆解（股息＋盈餘成長＋估值變化）當成過濾器——問「報酬從哪來」，答不出現金流與盈餘成長的就是擊鼓傳花；估值變化長期趨近零，所以近十年高報酬有一部分是**借用未來的報酬**
- 第 2 章另外三個實用點：實質報酬才是真的（定存 1.6% vs 通膨 2.2%，30 年購買力剩 84%）；**費用也在複利**（1.5% 費用率 30 年吃掉 640 萬，這是唯一 100% 可控的變數）；三個數字誤用——算術平均掩蓋波動拖累（+50%/−50% 實際是 −25%，導出「降波動會直接提高複利報酬」）、年化 7% 不等於每年 7%（給了年報酬分布形狀）、規劃建議用 6% 基準 / 3% 壓力測試
- **第 3 章核心**：把「風險」拆成可決策的面向。最大回撤才是真正會痛的數字，**回本不對稱表（跌 50% 要漲 100%）**是「避免大虧勝過追求大賺」的數學理由，對應到工程師熟悉的「避免不可逆失敗優先於優化平均效能」
- 第 3 章的決策工具：風險承受度**三維度取最小**（能力客觀／意願主觀／需求從目標倒推），並說明能力可以用緊急預備金買、意願可以訓練、能力不行；風險問卷沒用，改用「把百分比換成實際金額」與「回想上次下跌你做了什麼」兩個測試
- 另收錄兩個新手很少聽過但會改變判斷的概念：**順序報酬風險**（同樣平均報酬、持續投入下順序不同差 120 萬；累積期早跌有利、提領期早跌致命）與**時間分散迷思**（時間縮小年化報酬離散度，卻放大終值離散度）
- 進度：15 章中完成 4 章（00–03），第一部收尾。下一輪進第二部：第 4 章各類資產的角色

## [2026-08-16] synthesis | 附錄 AB：快取策略（loop 第二十輪）

- 快取是「看起來最簡單、實際上最容易出錯」的優化，而 K8s 的多副本預設把問題放大
- 先確認需要：要先用附錄 Q 的方法量測（常見情況是以為 DB 慢、實際慢在 throttle 或連線池）；**命中率估算要在動手前做**（命中率 30% 的快取讓系統更慢也更複雜）
- **本章重點：本機快取在多副本下的四個陷阱**——使用者重新整理看到不同結果（極難重現）、「清除快取」只會打到一個副本、**擴容時新副本是冷的**（尖峰擴容正好加重下游負擔，同實戰 5 的乘法問題）、記憶體佔用是副本數的倍數；並給判準「兩個使用者同一秒看到不同結果會不會出事」
- Redis 在 K8s：**純快取資料可重建**所以是少數適合進叢集的有狀態服務，但要警覺 Redis 常慢慢變成唯一真相來源；四個必設參數，其中 **`maxmemory` 沒設會 OOMKilled 導致快取瞬間全空、下游被穿透流量打爆**，而設了之後 Redis 會自己淘汰；`maxmemory-policy` 預設 `noeviction` 對快取是錯的；純快取關持久化；Redis 客戶端是多工不是連線池
- **Redis 掛掉時該降級而非一起掛**：短逾時 + 斷路器 + **壓測「沒有快取」的容量**；沒做這個決定的下場是所有請求卡在等逾時、執行緒耗盡、資料庫還好好的但服務全掛
- 失效策略：cache-aside 為預設；**寫入後要刪除而不是更新**（併發下更新會留下舊值且錯到過期）；版本化 key 做批次失效
- Cache stampede 三形態與四解法，強調 **TTL 加隨機抖動是一行程式碼解決最常見一種雪崩**；並補 K8s 特有的冷啟動（預熱或改用共享快取——這也是多副本該用分散式快取的另一個理由）
- **「加了快取反而更慢」五成因**，其中「序列化成本超過查詢成本」最容易忽略（快取一筆 0.5ms 的查詢卻要 1.5ms 往返 = 慢三倍）
- 六項監控指標，點出「命中率下降 + 淘汰率上升 = 記憶體不夠」的組合判讀
- 12 個誤區 + 六組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 35（A–Z + AA/AB），約 39.6 萬字

## [2026-08-16] synthesis | 資產配置教材第 4-5 章：資產角色與 ETF/指數化（loop 第三輪）

- 第二部開始。第 4 章刻意不寫「XX 是什麼」的百科式定義，改成統一問「**它在組合裡做什麼工作**」，並給四種角色框架（成長引擎／穩定器／流動性／保險）——說不出角色就不該買，這條規則直接擋掉市面上多數商品
- 第 4 章對台灣讀者最重要的兩個點：**本國偏誤的三重代價**（台灣佔全球市值僅約 2%、台股 ETF 單一成分股權重可能過半、且與工程師人力資本高度重疊）；**高收益債是假穩定器**——判準是「股市大跌時也大跌的東西不能當穩定器，不管它叫什麼名字」
- 另收 duration 的實用近似（利率動 1% → 價格反向動 duration%），解釋 2022 長債 −30% 的成因；並提出一個與多數網路文章不同的主張：**對資產規模還不大的台灣人，台幣定存作為穩定器未必比美債 ETF 差**——穩定器的工作是穩定，多疊一層匯率波動是反效果
- **第 5 章的骨幹是 Sharpe 的算術**：主動投資人整體扣費用後必然落後被動，這是恆等式而非統計觀察；再補 SPIVA 十年期 80~90% 落後，以及「過去績效對未來預測力極弱」讓『挑贏家基金』也失效
- 費用率專節（本書最確定的一筆錢）：三十年 1.5% 費用率吃掉 640 萬 ≈ 總報酬的三到四成；給了心算法「費用率 × 資產 = 每年付出去的錢」比看百分比有感；並點名台灣資料頁常只揭露經理費，**經理費 ≠ 總費用率**
- 台灣兩個坑寫成專節：**高股息 ETF**——用除息機制證明「股息不是額外的錢」，累積期的人拿到的是稅＋再投入摩擦＋選股限制；**槓桿 ETF 每日重設造成波動衰減**（+10%/−10% 兩天，指數 −1% 而正2 是 −4%），附主題型 ETF 在題材最熱時發行的結構性問題
- 進度：15 章完成 6 章（00–05）。下一輪第 6 章相關性與再平衡（資產配置的核心機制），第二部收尾

## [2026-08-16] synthesis | 附錄 AC：排程任務與背景工作（loop 第二十一輪）

- 附錄 C-2 有 Job/CronJob 欄位但沒有「背景工作該怎麼設計」；這類東西在遷移時最容易出事（附錄 U 提過排程常藏在 OS 設定裡沒有文件）
- 四種形式決策樹（Job／**CronJob 為預設**／應用內背景服務／專用排程系統），CronJob 優先的三個理由：天然單例、內建重試與歷史、**排程本身變成 git 裡的 YAML**
- **多副本重複執行**（最常見的遷移事故）：`BackgroundService` + `PeriodicTimer` 在三副本下每小時跑三次；三種解法對照，並明確指出**「只跑一個副本」不是解法**（放棄高可用且滾動更新期間仍會重疊）；K8s 原生 Lease-based leader election 的 RBAC 與三個實作注意事項（換手期間仍需冪等）
- CronJob 四陷阱：時區（不設就 UTC）、**錯過超過 100 次排程會永久停止且無告警**（少人知道，`startingDeadlineSeconds` 設太短就會撞到）、`Forbid` 卡住會讓後續全部靜默跳過所以必須配 `activeDeadlineSeconds`、Job 的 Pod 跟其他 Pod 一樣會被驅逐
- 長任務設計：**分批 + checkpoint**（一次撈全表的三個問題：OOM、長交易、中斷全重來）、正確處理 SIGTERM 停在安全批次邊界（即附錄 S 說的 spot checkpoint 具體實作）、冪等、`activeDeadlineSeconds` 當保險絲
- **監控的核心差異：「沒跑」比「跑錯」更難發現**——線上服務掛了有人抱怨，背景工作沒跑是安靜的，直到月底對帳才發現三週前就停了。三種偵測方式，推薦 **dead man's switch + Pushgateway**（Prometheus pull 抓不到短命 Job），且該模式涵蓋所有失敗形態；另強調「執行時間趨勢」——原本五分鐘跑成五十分鐘仍然算「成功」但已在往超時走
- 10 個批次反模式，其中「應用啟動時做重活」是遷移常見模式（拖慢啟動、每副本各做一次、擴容再做一次）
- 四組檢查清單 + 10 個誤區
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 36（A–Z + AA/AB/AC），約 40.2 萬字

## [2026-08-16] synthesis | 資產配置教材第 6-7 章：相關性/再平衡與配置決策（loop 第四輪）

- 第二部收尾 + 第三部開場。第 6 章是全書機制層的核心，第 7 章是第一次產出「可執行的數字」
- **第 6 章的骨幹是一條不等式**：組合期望報酬是線性加權、風險不是（附組合變異數公式與實算表——股 60/債 40 固定 5.4% 期望報酬，ρ 從 +1 到 −0.5 波動由 13.2% 降到 9.8%）。這就是「唯一的免費午餐」，且串回第 2 章的波動拖累 → 這頓午餐還會加菜
- 由「分散只消得掉非系統性風險」導出全書反覆用的結論：**市場只為不可分散的風險付錢**，所以持有個股多出來的波動是白付的（第 4 章埋的伏筆在這裡收）
- 誠實寫了三個陷阱避免讀者高估分散：**危機時相關性趨近 +1**（分散在最需要時打折）、**2022 股債同跌是「低通膨環境假設」失效**（推論出現金作為第三支柱有理由）、相關矩陣是後照鏡且對最佳化極度敏感
- 再平衡部分刻意把兩個效果分開：**控制風險水位是確定的、提高報酬不保證**（單邊上漲市場反而有害），糾正被誇大的「再平衡紅利」；實務規則收斂成「每年或半年檢查 + 偏離 5 個百分點才動」；並強調**累積期最好的工具是新資金導流**（零成本、零稅務事件、心理阻力最小）
- **第 7 章的方法論創新是用最壞情況反推**取代「100 減年齡」這類單變數公式：組合最大回撤 ≈ 股票比例 × 50%，代入實際金額後自問撐不撐得住；並算出「用配置追報酬缺口效率極差」（80%→100% 股票只多 0.8% 預期報酬卻多 10 個百分點回撤）→ 缺口要用儲蓄率補
- **分桶（bucketing）當成心理工具而非技術工具**：崩盤時能說「近三年要用的錢完全沒事，跌的是十五年後那桶」——同一筆錢不同框架導向不同行為
- 五個經典模型逐一寫出「假設 + 何時失效 + 適合誰」（60/40 的核心假設 2022 失效、全天候原版用槓桿且對累積期太保守、永久組合只有 25% 在成長引擎）；台股比例給 10~40% 的決策框架而非標準答案，並區分「加重台股的理由哪些成立哪些是偏誤」
- 收尾點名工程師的過度設計四警訊，主張 3~5 個部位可達成 15 個部位 95% 的效果，**可維護性是真實價值**（維護者是二十年後失去熱情的你）
- 進度：15 章完成 8 章（00–07）。下一輪第 8 章台灣實務落地（複委託 vs 海外券商、稅、匯率、美國遺產稅）

## [2026-08-16] synthesis | 附錄 AD：檔案與物件儲存（loop 第二十二輪）

- 實戰 1 提過「本機檔案是遷移最常見的卡點」但只給三個選項就帶過；這份展開，因為「把使用者上傳的檔案放進 PVC」是多數團隊第一次都會做錯的決定（單副本正常，擴容那天才發現檔案已散在三個 PVC 裡）
- 不該放 PVC 的五個理由（RWO 無法水平擴展／RWX 有自己的代價／備份難以單檔還原／容量變硬約束／**檔案流量穿過應用**），並列出 PVC 仍然正確的四種場景與判準「這個檔案掉了會不會有人抱怨」
- 物件儲存三個心智模型調整：**沒有目錄只有扁平 key**（改「資料夾」名是 O(n)）、不能 append 只能覆寫、大檔用 multipart；一致性方面提醒 list 可能有延遲所以 metadata 要記在資料庫
- **本章重點：上傳下載不要經過應用**。列出經過應用的四個代價（記憶體緩衝／佔住 worker 數十秒／Ingress body size 那條鏈／雙倍流量與跨區費），改用**預簽名 URL** 一次全解；附 mermaid 四步流程圖與 C# 範例
- 直傳的五條安全設計，核心是**「預簽名只授權可以傳，不保證內容安全」**——路徑必須由伺服器決定（否則可覆寫他人檔案）、有效期短、限制型別大小、**上傳後仍要後端驗證**（magic number 而非副檔名）、DB 沒記錄前那個檔案不算存在
- 補 CORS 是直傳第一個障礙且錯誤只出現在瀏覽器 console；以及沒用直傳時 Ingress/CDN/框架三層大小限制（任一層漏改都是 413 且應用日誌無紀錄）
- 檔案處理工作：事件驅動而非同步做、**worker 應該是獨立 Deployment**（影像處理的資源需求與 API 完全不同）、冪等靠「輸出 key 是確定性的」、大檔要串流
- 成本：生命週期規則、**孤兒檔案對帳**（DB 記錄刪了檔案還在，最常見的浪費，正好是附錄 AC 的 CronJob 用例）、版本控制每個版本都計費要配清理規則；對照附錄 K 的叢集內盤點——物件儲存因為「不會滿」更容易被忽略
- 12 個誤區 + 五組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 37（A–Z + AA~AD），約 40.8 萬字

## [2026-08-16] synthesis | 附錄 AE：設定管理的完整策略（loop 第二十三輪）

- 10 分鐘排程重複觸發五次，合併為一次執行（寫五份倉促的不如一份紮實的）
- 正文第 6 章講機制、附錄 C-1 講欄位，但沒有「一個系統的設定該怎麼組織」。切入點：**設定變更造成的事故比程式碼變更多**，原因很結構性——沒有型別檢查、沒有單元測試、review 草率、生效速度快
- 依「變更頻率 × 敏感度」分四類（環境差異／機密／調校參數／**功能開關**），關鍵區分是最後一類的變更頻率差一個量級，**不該用 ConfigMap 做**；判準「這個值改了我能接受等一次滾動更新嗎」
- 多環境：**不要用 git 分支管環境**（會漂移、無法 diff、在最不該衝突的地方衝突）；用 base + overlay，並提出**「能不能 diff 兩個環境的最終產出」是判斷設定組織好壞的最直接指標**；overlay 越薄越好（每個出現在 overlay 的值都是環境不一致的風險點，呼應附錄 Z）
- 設定變更的四道防護，其中最有價值的是 **`ValidateOnStart`**——它把設定錯誤變成部署失敗而非執行期故障；配合滾動更新的效果是「新 Pod 起不來、舊 Pod 不被砍、線上不受影響」
- **熱重載的真相**：三種注入方式的行為對照（`env` 完全不變、volume 掛目錄會變但應用要自己重讀、`subPath` 完全不變）；並主張**預設該用滾動更新而非熱重載**——熱重載的隱藏代價是各副本不一致與「不知道當時跑的是哪一版設定」導致故障難重現；只保留給緊急降級與日誌等級
- Feature flag 與 ConfigMap 五項分工對照、三種值得用 flag 的場景（**把「部署」與「發布」拆開**、緊急降級開關要事前做好並寫進 runbook）、以及 **flag 是會累積的債務**（二十個 flag 理論上一百萬種組合）與三條清理紀律
- 機密的組織（分層授權、應用不該知道機密從哪來、輪替要能不停機）
- 五種常見設定事故，展開最陰險的一種：**打錯字靜默使用預設值**（服務正常啟動、健檢通過、只有實際查詢才失敗，若預設值指向真實存在的東西可能數天後才發現）；解法是**必填的環境設定不給預設值**
- 10 個誤區 + 六組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 38（A–Z + AA~AE），約 41.4 萬字

## [2026-08-16] synthesis | 資產配置教材第 8-10 章：台灣落地、RSU、執行計畫（loop 第五輪）

- 第三部完成。這三章是全書對台灣科技業工程師最直接可執行的部分，也是網路上資訊最零碎、錯誤最多的區塊
- **第 8 章的主論點**：三條管道（台灣 ETF／複委託／海外券商）**最大的差別是稅，不是手續費**——多數人比較的手續費恰好是最不重要的一項
- 第 8 章的具體結論：台灣不課個人證所稅 → 低配息、低周轉、長期持有在稅務上最有效率（第三次補強「別買高股息」的理由）；海外所得走最低稅負制且**只在賣出時實現**；**ETF 註冊地決定股息預扣**（美國 30% vs 愛爾蘭 UCITS 約 15% 且累積型連分配都沒有），粗算法「美國 ETF 額外成本 ≈ 殖利率 × 15%」
- **美國遺產稅寫成獨立專節**（台灣理財文章幾乎不提）：非居民免稅額僅 6 萬美元、最高 40%、適用美國註冊股票與 ETF；誠實標註**複委託是否適用實務見解不一**，並用「資料庫選型」類比說明——規模會成長就一開始選愛爾蘭註冊，避免未來遷移產生的稅務成本
- 匯率的正確問法改成「哪種暴露符合我的未來支出」：成長引擎可全球化、**穩定器應以台幣為主**；並給出按資產規模分三階段的路徑決策框架，附「不要為了最優解而拖延開始」
- **第 9 章的核心工具是一個反問**：「如果公司給我等值現金，我會拿去買自家股票嗎？」——答案幾乎都是不會 → 那就該賣。關鍵在於**持有與買進在經濟上等價**，反問法同時破解稟賦效應與不作為偏誤
- 第 9 章其他要點：雙重曝險用「單點故障」類比並附股價腰斬+裁員同時發生的實算對照（50% 集中度 vs 10%）；**歸屬即賣是預設**，最強論據是「按高價課稅、按低價持有」的泡沫教訓；ESPP 的**參加與持有是兩個決定**；未上市股票在規劃上當成 0；**賣掉 RSU 後別再買同產業 ETF**（分散看實質相關性不看標的數量）
- **第 10 章把計畫變成流水線**：一次投入期望報酬較高（約 2/3 期間勝出）但分批是心理保險，決策看金額佔比且期間必須事先訂好——特別警告「別把分批投入偷換成等跌再進場」（前者有結束時間後者沒有）
- 執行面三個可直接照抄的東西：投入頻率判準（固定成本佔比 <0.5%，複委託低消反推出每季投一次）、**「先付給自己」的自動轉帳流水線圖**、年度檢視 30 分鐘流程（含賣出優先順序：公司股票 → 台灣部位 → 海外部位，理由是稅）
- 收尾強調**查看頻率應與投資期限成反比**（短視損失趨避讓頻繁檢視者長期報酬更差），並給出「市場大跌時的動作清單」——第一條是「什麼都不做」，最後一條是「不要打開試算表算自己虧了多少」
- 進度：15 章完成 11 章（00–10），第三部收尾。下一輪進第四部：第 11 章心理陷阱

## [2026-08-16] synthesis | 附錄 AF：本機開發與 Inner Loop（loop 第二十四輪）

- 附錄 O 講平台讓團隊能上線、附錄 V 講知識傳承，但都跳過開發者每天感受最深的事：**他們怎麼寫程式、怎麼測改動**
- 用算術立論：一天改動驗證五十次 × 每次三分鐘 = **兩個半小時**，比任何架構優化省下的都多且天天發生；並指出它會影響行為——**inner loop 慢的團隊傾向「一次改很多再測」**，讓除錯變難、改動變大、review 變痛苦
- 四種策略對照表（速度／真實度／複雜度）：完全本機 + Compose（**不要因為用 K8s 就放棄它**）、本機 K8s + Skaffold（關鍵是 `sync` 讓靜態資源改動從兩分鐘壓到兩秒）、遠端同步、**流量攔截**（Telepresence/mirrord = 本機速度 + 叢集真實度，可在 IDE 下中斷點接真實上游流量），並列出攔截的三個限制
- **判準：高估真實度需求是最常見的錯誤**——「要跟五個服務溝通所以一定要在叢集開發」，但若這次改動沒觸及那些呼叫，mock 掉完全沒問題；另提出**真實度可分階段**（日常最快、推 PR 前才高真實度）
- 避免本機與叢集漂移三原則：同一份 chart 只換 values、**程式碼裡不要加 `if (isLocal)`**（差異應該在設定不在程式碼，否則本機測試價值下降）、依賴版本一致
- 團隊層面：呼應附錄 O/V——**一般開發者不該需要懂「怎麼設定本機叢集」**，平台要提供一鍵腳本；共用開發叢集用 per-developer namespace + quota；**流量攔截在共用叢集預設會搶走所有人的流量**，必須用 header 過濾模式
- 開發叢集成本三手段（下班縮容 CronJob、spot 節點、盤點跑更勤）
- 除錯三方式，強調 **`kubectl debug` 臨時容器是「正式環境用 distroless」之後唯一的排查手段**
- 10 個反模式（含「每個人 push 映像到共用 registry」——本機 K8s 可用 `kind load` 完全跳過 registry）+ 10 個誤區 + 五組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 39（A–Z + AA~AF），約 42 萬字

## [2026-08-16] synthesis | 資產配置教材第 11-12 章：心理陷阱與稅/保險/退休試算（loop 第六輪）

- 第四部開場。第 11 章的定位是「前面十章建立的計畫，失敗主因不是計畫錯而是執行的人是你」
- **第 11 章的開場證據是行為差距**：投資人實際報酬長期低於他持有的基金本身，每年約一到三個百分點——這筆錢不是被市場拿走的，是被自己的行為拿走的
- 用「為草原演化的決策系統被搬進統計性質完全相反的環境」建立框架（附五列對照：看到危險立刻逃→崩盤賣在最低點），並用工程師熟悉的話收束：**不是不夠理性，是架構假設不成立，修法是改架構不是叫它更努力**
- 十個陷阱各給「機制＋在投資裡的樣子＋對策」；特別點名**過度自信對工程師殺傷力最大**（高學歷高收入者過度自信程度更高、交易更頻繁，而交易頻率與報酬負相關），對策是自問「我憑什麼比幾萬個全職做這件事的人知道得多」
- 三個高風險情境寫成**可直接照做的動作清單**（大跌時／別人賺很多時／有人推薦時），其中最實用的是第三個的**7 天冷靜期**——「所有需要你立刻決定的投資機會，都是在利用情緒繞過思考」
- **關鍵主張：知道偏誤幾乎不會降低你受它影響的程度**（偏誤在直覺系統、閱讀在分析系統）→ 有效的是五道結構性防禦（規則化／自動化／降低查看頻率／減少資訊攝入／加入摩擦），設計原則是「讓正確行為成為預設值、讓錯誤行為需要額外力氣」，直接對應工程師寫危險操作確認與 dry-run 的直覺
- 收尾寫工程師特有三陷阱：把它當最佳化問題（追求穩健而非最佳）、相信能寫程式打敗市場（倖存者偏誤／未計滑價稅費／多重測試）、**把技術理解誤認為投資優勢**（股價反映的是「相對於預期的意外」，技術好且人人知道＝已在價格裡）
- **第 12 章的立論**：稅、保險、退休試算的報酬是**確定的**，而投資報酬不確定——把 90% 注意力放在不確定的東西上是本末倒置
- 稅的部分以**邊際稅率**為軸心（決定所有節稅決策的價值），台灣不課證所稅推出三個推論（低周轉最有利／配息在累積期是負擔／股利二擇一要試算），節稅四順序並警告**別讓稅務尾巴搖狗**
- 保險部分給兩種保額算法（遺屬需求法／人力資本法）與十列檢查表，點名**失能保障是工程師最大破洞**、單身無扶養者不需大額壽險；投資型保單用第 5 章的費用框架拆解為何兩邊都不夠好，並給「已經買了怎麼辦」的三路徑未來現金流比較（不要衝動解約）
- 退休試算：三層結構、**勞保年金保守起見先當 0 或打折**（足額是驚喜而非假設）、勞退專戶要查一次並列進資產負債表；**4% 法則寫出五個限制**（美國資料／30 年假設／隱含股債配置／未計稅費／對順序報酬敏感）→ 保守改用 3~3.5%（年支出 × 28~33）
- 收尾用「缺口四槓桿」呼應全書主線：提高儲蓄率與延後退休效果最大，**提高投資報酬率效果最小且不可控**
- 進度：15 章完成 13 章（00–12）。剩第 13 章（Python 實作）與第 14 章（IPS 行動清單）+ 三個附錄

## [2026-08-16] synthesis | 附錄 AG：日誌策略與成本（loop 第二十五輪）

- 正文 15 章講 ELK 機制、實戰 6 講結構化與 trace ID，但沒有「該記什麼、留多久、為什麼這麼貴」。切入點：日誌是「寫的時候不痛、帳單來才痛」的東西
- **三種用途三套要求**（除錯 7–30 天／趨勢告警／稽核半年到七年），核心紀律是**不要用日誌做監控**（想知道數量比例趨勢 → metric；想知道這一筆發生什麼 → log），以及稽核日誌要單獨存放（否則為了留稽核而付出留住所有 DEBUG 的代價）
- 該記五類（**「決策點」最容易忽略也最有價值**——事故當下想知道的往往是「為什麼系統做了那個決定」）；不該記六類，其中完整 body 是「最大的量、最高的外洩風險、最可能含個資」；自我檢查「誰會在什麼情況下看它」
- 等級紀律：**`Error` 的定義是「需要人採取行動」**，每天幾千筆沒人看的 ERROR 不是 ERROR 而是誤標，且會淹沒真的；WARN 不是垃圾桶而是「異常但已處理」；動態調整等級是附錄 AE 說的熱重載合理用例，但要有自動關閉機制（忘了關是常見成本事故）
- **成本算術範例**：200 rps × 5 行 × 500B = 43GB/天，留 30 天加索引與副本約 **4TB，而這只是一個服務**；四個減量手段（把 metric 移出日誌／成功請求取樣／分級保留／不查詢的欄位不建索引）
- Loki 的取捨表：只索引 label 所以便宜，但要查詢模式對得上（多數團隊實際是「先過濾服務再看內容」正好適合）；**label 高基數同樣會爆**
- ILM 五階段，指出**設定 ILM 是日誌成本控制投報率最高的單一動作**（一次性、自動生效、應用不用改）
- 收集架構：DaemonSet 為預設、sidecar 只在應用無法輸出 stdout 時的妥協；並再次強調 **kubelet 日誌輪替沒設會撐爆磁碟觸發 DiskPressure 驅逐整台節點的 Pod**（日誌設定造成叢集事故的真實路徑）
- 12 個誤區 + 六組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 40（A–Z + AA~AG），約 42.6 萬字

## [2026-08-16] synthesis | 資產配置教材第 13-14 章：Python 實作與 IPS 行動清單（正文完結，loop 第七輪）

- **15 章正文全數完成**（00–14）。剩三個附錄（術語表／數字速查／FAQ）
- **第 13 章的核心不是教 numpy，是用程式親手推翻「最佳化」**。八段可直接跑的程式：複利與目標反推、組合報酬與波動（矩陣版）、ρ 對波動的曲線、效率前緣散點、**最佳化敏感度**、蒙地卡羅、順序報酬、費用率
- 第 13 章的關鍵實驗（程式 5）：把股票期望報酬假設動 **1 個百分點**，隨機搜尋出的最佳股票權重從 14% 跳到 40%。而任何人對長期期望報酬的估計誤差都遠大於 1pp → 導出「均值-變異數最佳化是**誤差最大化器**」，它會系統性把權重推向你剛好高估的資產。用「在驗證集調 hyperparameter」類比，並點出差別：**投資的測試集是你的下半輩子，只能跑一次**
- 蒙地卡羅段落刻意教「**看分布不看平均**」（P5 才是你要能接受的下限、達標機率決定要不要調目標或儲蓄率），並誠實列三個模型限制（常態低估肥尾、假設報酬獨立、輸入仍是猜的），附 t 分布替代寫法
- 順序報酬風險用一個乾淨的實驗證明：同一組 30 個報酬打亂順序，提領期結果差好幾倍甚至歸零；**把提領金額改成 0，三種順序結果完全相同**——這就是「只有在有現金流進出時順序才重要」的證明
- 收尾給「該這樣用 / 不要這樣用」對照表，明確定位這些程式是理解工具與壓力測試工具，不是預測工具或策略搜尋工具
- **第 14 章是全書的收斂層**，三個可直接使用的產出：
  1. **30 天啟動計畫**四週分工——前三週完全不投資（盤點／補地基／紙上決定配置），第四週才執行；並標出「如果只能做一件事，做自動轉帳」
  2. **完整 IPS 模板**（十節，可直接複製填寫），最關鍵的設計是第 7、8 節把「允許修改」與「不允許修改」的情況分開明列，以及第 10 節「寫給崩盤時的自己」的一段話
  3. **20 條紅色警戒**分四類（結構性／成本稅務／配置／行為），按嚴重程度排序
- 另附月/季/年週期檢查清單（每月人工動作 0 次）、RSU 歸屬與市場大跌的動作清單、13 列一頁式決策樹
- 收尾刻意寫成正面的：科技業工程師的儲蓄率天花板高、看得懂數學，**不需要打敗市場**——存夠多、買夠廣夠便宜、別亂動、等夠久，四件事沒有一件需要天分，難在持續二十年，而那正是 IPS 與自動化存在的理由
- 進度：正文 15/15 完成。下一輪寫附錄 A 術語表

## [2026-08-16] synthesis | 附錄 AH：前端在 K8s 上的部署（loop 第二十六輪）

- 實戰 1 只帶到 Dockerfile/try_files/環境變數兩難；多數 K8s 教材完全不談前端，導致前端的部署事故常常「查很久才發現思路跟後端完全不同」
- **三個根本差異**（產物是靜態檔案／執行在使用者瀏覽器／**版本切換不是原子的**），第三點是所有問題的根源：使用者十分鐘前載入的 HTML 引用了一組特定 JS，那個工作階段持續到他關閉分頁為止
- 四種部署形態對照，並給誠實建議：**純 SPA 放物件儲存 + CDN 在幾乎每個維度都更好**（更快、更便宜、更可靠、且根本沒有舊檔 404 問題）；用 K8s 的三個合理理由（同網域避 CORS/cookie、已有 Ingress、地端無 CDN），以及「CDN + Ingress 路徑分流」的折衷
- **「舊 JS 檔案 404」完整推演**：症狀特徵是「只有部分使用者、只在部署後一段時間、重整就好」所以難重現；**滾動更新讓它更嚴重**（新舊 Pod 並存，整個更新窗口內都可能發生）；四個解法，其中「前端攔截 chunk load error 並提示重整」是無論如何都該做的安全網——**白畫面是最糟的失敗形態**
- 快取策略的正解與其邏輯：`index.html` 必須 `no-cache`（它是版本入口）、帶 hash 的資源可以且應該 `immutable, max-age=31536000`（內容變檔名就變）；設反的兩種後果；CDN 部署後**只需 purge index.html**
- 環境變數三解法完整比較（延伸實戰 1），並補一個安全提醒：**前端的所有設定都是公開的**，API key 一律不能放，需要金鑰的第三方呼叫要用後端代理
- SSR 四個特殊考量：**`NODE_OPTIONS --max-old-space-size` 要小於 memory limit**（同附錄 AA 的 JVM 堆積道理）、CPU 需求比靜態服務高一個量級、需要快取層且不能只用本機快取、冷啟動要 startupProbe
- 前端可觀測性三塊（錯誤收集、**RUM**、trace 串到瀏覽器），點出「使用者說很慢但後端 metric 正常」的答案通常在 RUM；並強調前端錯誤要帶建置版本（因為舊版使用者會存在一段時間）
- 12 個誤區 + 七組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 41（A–Z + AA~AH），約 43.2 萬字

## [2026-08-16] synthesis | 資產配置教材附錄 A、B：術語表與數字速查（loop 第八輪）

- 附錄 A（術語表）：約 90 條依英文字母 A–Z，每條統一格式「一句定義 + 為什麼你該在意 + 章節連結」。刻意不寫百科式定義，每條都帶判準——例如 High Yield Bond 直接寫「名字裡有債但股災時跟股票一起崩，不是穩定器」、Leveraged ETF 寫「不是長期看好的加倍版」
- 附錄 A 另收中文專有名詞區（二代健保補充保費、最低稅負制、勞退自提、證交稅、證所稅、除息），這些查英文字母表查不到但台灣讀者最常遇到
- 附錄 B（數字速查）把散落十五章的數字集中成十一節：規劃假設值（基準 6%／壓力 3%／通膨 2.5%）、各資產報酬與波動量級表、歷史回撤與**回本不對稱表**、配置對應最壞回撤與預期報酬（含實質）、費用率三十年帳與各類產品合理費用率、72 法則與複利表、**儲蓄率 vs 報酬率雙表對照**、台灣稅制與美國預扣/遺產稅數字、緊急預備金與債務利率分界、配置與再平衡的規則值（含公司股票 10% 上限、7 天冷靜期、投入頻率 0.5% 判準）、退休試算與缺口四槓桿
- 附錄 B 第十節收錄**十一條常用公式**（複利終值、年金終值、72 法則、實質報酬、回本漲幅、組合期望報酬與變異數的純量與矩陣版、波動拖累、債券價格對利率、Sharpe、回撤近似、ESPP 折扣換算），第十一節放 20 條紅色警戒濃縮版
- 全書所有稅制與制度數字統一標註「以當年度公告為準」，歷史報酬統一標註「量級估計非預測」
- 進度：正文 15 章 + 附錄 2 完成，剩附錄 C（FAQ）。下一輪寫完即全書完結

## [2026-08-16] synthesis | 附錄 AI：資料庫連線的深入（loop 第二十七輪）

- 實戰 5 的連線池乘法只是入口；這份補中介、讀寫分離、失效偵測、故障轉移，重點是**這些問題在 K8s 上比 VM 上更容易出現**
- 連線為何貴（TCP+TLS+認證+**資料庫端建立 session**，Oracle dedicated server 每條連線一個 OS 程序）；四個池參數的意義，並點出 **`Min Pool Size` 也會 × Pod 數常駐佔用**（Min=5 × 20 Pod = 100 條即使系統閒置）
- 連線池中介：解決 N×M 收斂問題；三種 pooling 模式對照，**transaction pooling 會壞掉的五類東西**（session 變數、prepared statement、暫存表、advisory lock、LISTEN/NOTIFY），且症狀隱晦；**sidecar 形態收斂效果差很多**（每 Pod 各一組池）這點常被搞混；判準是先做完「池上限反推 + Min 調整 + maxReplicas 檢查」，多數團隊到此就夠
- 讀寫分離：兩個池要算兩次乘法、複製延遲的「寫完讀不到」在 K8s 上更容易發生（請求打到不同 Pod）；三種處理方式，建議**從「預設讀主庫、只把明確安全的查詢移到副本」開始**（反過來做會產生難重現的 bug）；並指出多數團隊該先看索引/N+1/快取
- **連線失效（K8s 特有的嚴重性）**：路徑上多了 NAT/conntrack，任何一環認為閒置太久就單方面丟棄且不通知應用，症狀是低流量時段後的偶發連線錯誤；四個常見殺手（**雲端 NAT 只容忍幾分鐘**最常見）；三道防護優先序 **連線生命週期上限 > TCP keepalive（Linux 預設兩小時太長）> 取出時驗證**
- **故障轉移的三個必做**：liveness 不查 DB（否則資料庫切換 → 所有 Pod 同時重啟 → **把十秒的切換變成完整服務中斷**）、重連要有退避**與抖動**（沒抖動只是把打雷群效應延後而非分散）、斷路器
- 交易與 Pod 生命週期：長交易在 K8s 幾乎一定會被驅逐打斷 → 改分批提交；優雅關閉要涵蓋交易；寫入要冪等（同附錄 AA 的「逾時後不知道對方做了沒」）
- 監控：**「等待連線的時間」是最有診斷價值的指標**——它把「應用慢（池不夠）」與「資料庫慢」分開，正是附錄 Q 的 L4 定位依據
- 12 個誤區 + 七組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 42（A–Z + AA~AI），約 43.8 萬字

## [2026-08-16] synthesis | 資產配置教材附錄 C 完成，全書 15 章 + 3 附錄完結（loop 第九輪）

- 附錄 C（FAQ）45 題分八組：開始之前／**「我朋友說……」系列**／標的與工具／台灣實務與稅／公司股票／市場狀況與時機／人生階段／心態
- 「我朋友說」是本附錄的設計核心——把讀者一定會從同事群組聽到的八句話逐一拆解（買 0050 就好、高股息每年配 8%、美股年化 10% 躺著賺、年輕就該 100% 股票、定存最安全、保險要買終身的、勞保會倒不要指望、買房才是最好的投資）。每題不是否定，而是指出它「對在哪、漏了什麼」
- 幾題刻意寫得直接：Q4 說明理專的收入來自產品佣金而非你的報酬（誘因結構決定行為，不是人品問題）；Q15 直說 0050 vs 006208「是全書最不重要的決定之一，不要花超過十分鐘」；Q36 說明廣泛分散的指數化配置不需要停損（在指數上停損等於保證賣在低點）
- Q43「我怎麼知道自己做對了」給五題判準，**全部是可控項目**（儲蓄率／費用率／是否符合 IPS／有無計畫外決定／下跌時有無照計畫執行），明確排除報酬率——呼應全書主線
- Q45「這本書會過時嗎」給了讀者自檢方法：講「為什麼」的內容大概率還有效，講「多少」或「哪一檔」的去查最新——這也是整份教材寫作時的取捨原則
- **全書完結**：15 章正文（00–14）+ 3 附錄（A 術語表約 90 條／B 數字速查十一節／C FAQ 45 題），共 18 份頁面
- 總目錄加上「只有一個晚上就讀 00 + 07 + 14 三章然後照 30 天計畫做」的快速路徑

## [2026-08-16] synthesis | 附錄 AJ：對外 API 的邊界（loop 第二十八輪）

- 附錄 F/J/C-5 都在講路由，但沒講「認證、限流、配額、WAF 該放哪一層」——放太多在邊界會變成瓶頸與單點，放太少則每個服務各自實作、漏一個就是漏洞
- 職責判準：**這件事對所有服務都一樣嗎**；不該放邊界的共同點是「需要知道業務規則」，一旦邊界理解訂單/租戶/權限模型就會產生協調成本、爆炸半徑、架構耦合；實用反問「這規則改了要重新部署邊界層嗎」
- **認證分層**（接使用者的 Google OAuth + JWT）：**邊界做認證（你是誰）→ 401、應用做授權（你能做什麼）→ 403**；理由是簽章驗證對所有服務都一樣可以早擋，授權需要業務知識；三種實作做法對照
- 兩個必須知道的陷阱：**`RequestAuthentication` 只驗有帶 token 的請求、沒帶的直接放行**（必須配 `AuthorizationPolicy`，最常見的安全誤設）；**應用不能假設請求一定經過邊界**（叢集內可直接打 Service），信任邊界注入的 header 必須有 NetworkPolicy/mTLS 保證來源，否則等於把繞過方法寫在文件上
- 限流兩層都要：邊界擋濫用、應用做商業配額；重申 **ingress-nginx 限流是每副本各自計數**（實際上限 = 值 × 副本數），商業配額必須用 Redis 共享狀態精確計數；429 **必須帶 `Retry-After`**（否則客戶端立刻重試讓情況更糟）
- API key 生命週期五階段，強調**輪替要新舊並存**（同附錄 AI 的資料庫密碼、附錄 Y 的 API 版本，是同一個模式）與「撤銷立即生效 vs 快取」的張力解法
- 對外/對內分離：兩個 Ingress、`/admin` `/metrics` 不掛對外、**不要以為內網就安全**（叢集內任何 Pod 都連得到）、網路層與應用層雙重保護
- WAF 四項取捨表 + **先偵測模式再阻擋**的導入方式（同附錄 O 的政策節奏）+ 誤擋處理流程；並指出 CDN 是比叢集內更有效的攔截位置
- **邊界層是單點**：多副本跨 AZ、PDB、專屬節點或較高 PriorityClass、資源不能被 throttle；五項監控（含 `$request_time` − `$upstream_response_time` 揭露邊界自身排隊）
- 12 個誤區 + 七組檢查清單
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 43（A–Z + AA~AJ），約 44.4 萬字

## [2026-08-16] synthesis | 資產配置教材附錄 D 自我檢測 + 交叉連結驗收（loop 第十輪）

- 先做交叉連結驗收：盤點全教材 18 個 wikilink 目標，全部有對應資料夾；外部連結僅 `index` 與 `python`，兩者皆存在。無斷鏈
- 補附錄 D（60 題自我檢測），體例對齊 vault 內既有教材（k8s-mastery 附錄 A、FastAPI 附錄 C）：答案用 `<details>` 摺疊，強制先自己講一遍
- 三級難度分配：**L1 基礎 20 題**（能不能說出機制）／**L2 應用 22 題**（給情境做判斷）／**L3 反推與陷阱 18 題**（給症狀找根因、揪出錯誤）
- L3 是本附錄的價值所在，全是診斷題而非背誦題：照著書做卻十年輸給指數（要能列出四個與市場無關的原因）、2022 股債同跌就說「分散沒用」錯在哪對在哪、看到年化 15% 的回測該問哪五個問題、「不賣不算做決定」的謬誤、RSU 高點歸屬沒賣的稅務災難、55 歲已達標卻 90% 股票、以及一組「0050+006208+半導體 ETF+公司股票」的組合診斷（實質上零分散）
- **12 題標記 🔴 紅色警戒**（答錯會造成實際財務損害），並在過關標準明說「🔴 全對比總分高更重要」
- 附題號→章節對照表（15 章全覆蓋），錯題可直接回查
- 教材最終規模：**15 章正文 + 4 附錄 = 19 份頁面**

## [2026-08-16] synthesis | 附錄 AK：導入路線圖（loop 第二十九輪）

- 教材有 72 份、四十幾萬字且是**主題式組織**（查得到），但沒回答剛接手的人最需要的問題：**這些該按什麼順序做**。這份把全書重排成時間軸
- Phase 0（1–2 週，唯一產出是決策紀錄，沒有任何 YAML）：要不要用 K8s／託管 vs 自建／資料庫進不進／第一個搬什麼／哪些不搬；點出**最常見錯誤是「先建叢集再想要放什麼」**（叢集本身沒有價值，規格與設定要有工作負載當依據）
- Phase 1（1 個月，能跑起來）：六件事，其中**附錄 D 的實驗是最高投報率的一項**（只花一天，但親手做過 OOMKilled/throttle/CrashLoop 之後遇到真問題的反應速度完全不同）；並明確列出五項**不要做**（mesh、多叢集、Operator、複雜 CI、平台化）
- Phase 2（1 季，能安全地重複）：GitOps + CI + PSA + 可觀測性 + 日誌保留期 + 連線池乘法 + **做一次真的還原演練**；驗收是「部署完全透過 git，沒有人手動 apply」
- Phase 3（半年，能交給別人）：責任邊界、golden path、namespace 自助化、政策強制、值班與 runbook、知識傳承、開發者體驗；**唯一真正的驗收標準是「另一個團隊自己上線過一個服務，而你只做 review」**，其他都是手段
- Phase 4（1 年，能承擔變化）：升級節奏、DR 演練並計時、成本治理、容量規劃、效能方法論、安全事故準備；終點是**「你休過一次假，沒被找」**
- 三條橫向線（安全每階段都要推進、**成本 Phase 1 刻意不管**因為東西還在變、知識傳承從第一天就要做）
- **六個常見順序錯誤**，展開兩個最容易被合理化的：監控留到最後（那個「之後」通常是第一次半夜出事的時候，而 kube-prometheus-stack 只要半天）、以及太早平台化（只有一個團隊時 golden path 就是你自己的 manifest，抽象成 chart 只有成本沒有收益）
- 各階段「還沒準備好」的訊號表，主張基礎沒穩就往上疊會在最糟時機崩塌
- 一頁式總表（五階段 × 時間 × 目標 × 唯一驗收標準）
- 同時在總目錄「怎麼用這套教材」加上導引：本頁是主題式導航、附錄 AK 是時間式導航
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 44（A–Z + AA~AK），約 45 萬字

## [2026-08-16] synthesis | 資產配置教材補充篇：房地產（loop 第十一輪）

- 第 4 章原本明確把房地產劃在範圍外（「值得單獨一本書」），但這個切割在實務上撐不住：**對台灣工程師而言買房是單筆金額最大的財務決定，且它會同時改變配置的每一個部分**。補成補充篇，並回頭修正總目錄的「刻意不做的事」
- 定位刻意收窄：不談選房（地段、屋況、議價），只回答三個財務問題——租買怎麼正確比較、買了配置怎麼變、房貸這個槓桿怎麼看
- **核心論點一：正確的比較不是「房貸 vs 房租」，是「持有成本 vs 房租」**。因為本息均攤前期利息佔比極高，房貸月付金不等於儲蓄。持有成本清單裡特別點出**頭期款的機會成本**是最常被漏掉的一項（400 萬 × 5% ≈ 每年 20 萬，不會出現在任何帳單上）
- 給了房價租金比的判讀門檻（>30 則租房通常較划算），並指出**台灣雙北租金收益率長期僅 1.5~2.5%**（房價租金比 40+）→ 誠實推論：買房的財務報酬有很大一部分押在「房價會繼續漲」，用第 2 章的框架講就是現金流報酬極低、其餘全靠估值變化。同時完整列出非財務價值（居住穩定、可裝修、心理安全感）並肯定它們是正當理由
- **核心論點二：房貸是多數人一生中承擔過的最高槓桿**，而多數人沒意識到。附槓桿放大表：頭期款兩成＝4 倍，**房價跌 25% 頭期款歸零**；並與第 5 章的槓桿 ETF 對照說明機制相同
- 台灣實務三點：**多為機動利率**（必做升息 1.5pp 壓力測試，不要用當下利率算到剛好）、**寬限期是陷阱**（判準：沒它就買不起＝買的是超過能力的房子）、提前還款 vs 投資要在利率之外加三個修正（確定性、機動利率上升、心理負擔）
- **核心論點三：買房會讓前十四章決定的配置在一天內作廢**。用買房前後對照表呈現「股票 37%/現金 63%」變成「不動產 82%/股票 15%/現金 3%」，且淨資產因交易成本先減少 5~10%
- 集中風險從第 0 章的三重擴充為**四重**（薪水/公司股票/台股台幣/房子），並點出房價與就業市場正相關 → 壞事會一起來
- 配置調整給了 A/B 兩種對立說法各自的邏輯，再給分階段判準（買房初期偏保守、預備金補足後可較積極），但**共同的一條是「金融資產應大幅偏向海外」**——因為不動產、工作、貨幣已 100% 在台灣
- 寫了一般理財書不會談的**工程師特有考量：買房＝地理流動性歸零**，而換城市/換工作是薪資成長主要來源，這是買房的隱性成本
- 收尾：五段檢查清單（資金/負擔/比較/配置/生活），並明訂「負擔面有任一項打不了勾 → 不是再想想，是還不該買」；另專節說明「租房是完全正當的長期選擇」，但但書是省下的錢要真的投資出去——而讀者讀完本書已把紀律問題自動化解決
- 教材規模：15 章正文 + 1 補充篇 + 4 附錄 = 20 份頁面

## [2026-08-16] synthesis | 附錄 AL：進階速查表（loop 第三十輪，深化而非開新主題）

- 上一輪判定教材結構已完整，轉向深化。先驗證一個具體缺口：**附錄 B 的速查表寫於只有 16 章時**，抽查 21 個後來引入的工具，**16 個完全沒被收錄**（trivy/cosign/istioctl/hubble/cilium/keda/kueue/skaffold/kind/oasdiff/kubeconform/kube-linter/kubent/etcdutl/conftest/helm unittest）——跟附錄 A 題庫的情況完全相同
- 新增 `60-advanced-cheatsheet`，按**「你想做什麼」**而非「這個工具能做什麼」組織（排錯當下想的是前者），十個任務分組：升級前檢查／YAML 驗證／供應鏈與安全／備份還原／成本盤點／效能定位／Istio 與 Cilium／排程批次擴縮／訊息快取資料庫／本機開發
- 每組都標註對應的附錄連結，且收錄的是**實際會用到的形式**而非工具的完整用法；例如 Istio 那組直接把「503 的四種旗標」對應到各自該看的 `proxy-config` 子指令
- 收尾一頁式「我想做 X → 用哪個」15 列對照表
- 同時在附錄 B 開頭加上說明，指出它的涵蓋範圍與附錄 AL 的分工（與附錄 A→X 的處理方式一致）
- 教材規模：入門篇 6 + 實戰篇 6 + 正文 16 + 附錄 45（A–Z + AA~AL），約 45.6 萬字

## [2026-08-16] refactor | 資產配置教材數字一致性驗收與修正（loop 第十二輪）

- 對全書 20 份頁面做跨章數字一致性驗收，**找到一組真實矛盾並修正**
- **問題**：費用率三十年試算表（出現在第 2 章、第 5 章、附錄 B、index.md）用的是「年初投入」的年金終值，但第 13 章讀者實際會執行的 `with_fee()` 程式寫的是「年底投入」——**同一本書的表格與程式對不上，且表格本身的數值也算得不夠精確**
- **修正方式**：統一為「年初投入」（與第 13 章蒙地卡羅那段的 `(values + contrib) * (1 + r)` 一致），改掉 `future_value` / `required_contribution` / `with_fee` 三個函式，並用本書自己的程式重跑驗算表格
- 修正後的數值（每年投入 30 萬、gross 7%、30 年）：2,970 / 2,860 / 2,760 / 2,510 / 2,290 / 2,090 萬；差額 110 / 210 / 460 / 680 / 880 萬
- **全書最常引用的簽名數字「1.5% 吃掉 640 萬」更正為 680 萬**，同步 5 個檔案（02、05、14、附錄 A、附錄 D）+ index.md
- 另修正一個表述精度問題：「吃掉總報酬三到四成」→ **「吃掉獲利約三分之一」**（實算 32.9%）。原表述的問題在於「總報酬」語意含混（含不含本金），改為明確的「獲利」並在第 5 章補上推導（投入本金 900 萬、低費用獲利 2,070 萬 vs 高費用 1,390 萬）
- 第 13 章補上一則方法論提醒：**所有程式假設年初投入，改成年底會小約 6%——這是不同來源試算結果對不上的常見原因**，看到任何試算表先確認期初/期末假設。把這次的內部矛盾轉成給讀者的教訓
- 其餘跨章重複數字（回撤 ≈ 股票比例 × 50%、跌 50% 要漲 100%、美國遺產稅 6 萬美元、ESPP 17.6%、60/40 的 5.4%/13.2%/9.8%、100 萬 30 年 761 萬、定存購買力剩 84 萬）逐一比對，**全部一致，無需修改**
- wikilink 斷鏈檢查：18 個內部目標全部存在，外部僅 `index` 與 `python`，皆有對應頁

## [2026-08-16] lint | 正文 16 章與後續附錄的一致性稽核（loop 第三十一輪）

- 教材已 45.6 萬字，正文 16 章是最早寫的。本輪不開新主題，改做前後一致性稽核：挑出「後續附錄補正或延伸的判斷」，逐條驗證正文有沒有跟上
- 七組 claim-pair 檢查結果：**五組已一致、兩組真缺口**
  - ✅ 第 7 章 CPU limit：原文就寫了「多數時候答案是把 limits.cpu 調高、或乾脆去掉 CPU limit」，與附錄 K 的判準表一致
  - ✅ 第 4 章 liveness：完整警告了「偷查下游依賴 → 資料庫一抖 → 一整層服務集體重啟」，附錄 AI 只是把它延伸到 DB 故障轉移情境
  - ✅ 第 5 章 kube-proxy 規模、第 11 章 ArgoCD 的 helm template、第 14 章 Pushgateway、第 3 章棄用掃描、第 8 章事故——均已涵蓋
  - ❌ **第 12 章 etcd 備份沒有提到 `/etc/kubernetes/pki` 必須一起備**（pki 只出現在 etcdctl 的參數裡，不在備份脈絡）——這正是附錄 L 指出「還原演練最常卡住、且錯誤訊息全是 x509 完全不指向真因」的地方
  - ❌ **第 6 章 Secret 沒有給外洩的處置順序**（提到輪替但沒有「先輪替再清理」的排序與理由）
- 兩處都以行內補充區塊修正（不重寫原文）：第 12 章加上 `tar -czf pki` 指令與「錯誤訊息不會指向忘了備憑證」的警告；第 6 章加上「外洩即已失效」的心智模型與為何直覺（先清理）是反的，兩處都連回對應附錄
- 修正後重跑檢查，兩處均通過

## [2026-08-16] refactor | 資產配置教材補 5 張 Mermaid 圖解（loop 第十三輪）

- 對照 vault 標準發現的缺口：k8s-mastery 有 70 張圖，本教材原本 **0 張**。依專案 CLAUDE.md 的 dispatch 規則走 `mermaid-diagrams` skill
- 先確認 vault 既有圖用的是**淺色 init**（`theme:base` + Tailwind 50/500 系配色），沿用以保持全 vault 視覺一致
- 五張圖各自對應該章最需要「一眼看懂」的結構：

  | 章 | 圖 | 圖型 | 為什麼是這張 |
  |---|---|---|---|
  | 00 | 曝險集中結構 | flowchart LR | 六個看似獨立的來源匯聚到單一風險源，橫向匯聚最直觀 |
  | 01 | 地基執行順序 | flowchart TD | 取代原 ASCII，三個決策菱形讓「什麼情況跳過哪步」變清楚 |
  | 06 | 分散消除什麼 | flowchart TD | 總風險拆兩支 → 一支歸零一支留著 → 導出「市場只為不可分散風險付錢」 |
  | 07 | 分桶架構 | flowchart LR + subgraph | 三個平行的桶各有期限與配置，subgraph 把「桶」的概念視覺化 |
  | 10 | 自動化流水線 | flowchart TD | 取代原 ASCII，加上「累積到門檻」的迴圈判斷 |

- 全部套語義 classDef（primary/success/warn/error/decision/accent/muted），**無逐節點 style**；第 0 章的圖刻意把六個來源上 muted、匯聚點上 error，讓「你以為的六個部位其實是同一個」在視覺上成立
- 交付前寫了一支檢查腳本掃全部 5 個 mermaid block：base theme / curve basis / 顏色必須 hex / 單 `%` 註解 / 裸 `end` 節點 / 逐節點 style / class 使用但未定義 —— **0 問題**；另修掉第 0 章一個定義但未使用的 classDef
- 教材規模：15 章正文 + 1 補充篇 + 4 附錄 + 5 張圖解

## [2026-08-16] lint | 一致性稽核自動化 + 18 項修正（loop 第三十二輪）

- 上一輪靠手動挑 claim-pair，本輪寫成可重複執行的 `audit_consistency.py`（scratchpad），三類檢查：
  - **A. claim-pair**：宣告式表格，記錄「後續附錄補正過的判斷，正文應該要有」
  - **B. 主題歸屬**（泛化版）：13 個主題各自的「正主檔案」，任何檔案提及某主題 ≥ 2 次卻沒連到正主就標記——這把上一輪的人工判斷變成自動偵測
  - **C. 結構**：frontmatter 五欄位、`## 連結` 區塊、是否連回總目錄
- 首次執行找出 **18 項**，其中 1 項是**腳本自己的誤報**（第 00 章的 frontmatter 只掃前 400 字元，被很長的 sources 清單擠出去）——修正腳本改為正確解析 frontmatter 區塊，而非「修正」沒問題的內容
- 真問題 17 項全部修正：
  - **B 類 6 處缺連結**：附錄 A/B 提及 Velero 卻沒連附錄 L、第 3 章提及 pluto/kubent ×4 沒連附錄 E、**第 14 章提及 ServiceMonitor ×10 卻沒連附錄 C-5**（最明顯的一處）、附錄 O 同樣
  - **C 類 11 處**：入門篇 1–5 與實戰篇 1–6 全部沒有連回總目錄——這是給新手看的入口檔案，卻是最沒有回頭路的一批
- 修正後重跑：**A/B/C 三類全數 0 項待處理**
- 此腳本與 `verify_k8s_mastery.py`、`audit_navigation.py` 構成三支可重複執行的檢查，之後新增附錄時可直接跑，不必靠記憶

## [2026-08-16] refactor | 補圖解五處（loop 第三十三輪）

- 盤點：74 檔中 28 檔含圖、共 72 張；43 檔無圖。但題庫／速查表／術語表／欄位參考本來就不需要圖——挑「核心洞見本身是結構性的」那幾份
- 補上五張，全部沿用既有的 mermaid base theme 與語義 classDef（紅=危險/錯誤路徑、黃=警告、綠=正確、藍=一般）：
  - **附錄 AI（57）連線失效路徑**：Pod → 節點/conntrack → 雲端 NAT → 防火牆 → DB，每一層標 ⚠ 表示會單方面丟棄且不通知應用；一張圖說明「為什麼防護要做在最上層的主動汰換」
  - **附錄 AB（50）多副本本機快取不一致**：三個 Pod 各自一份（舊值／新值／剛擴容是空的），使用者重整三次拿到三種結果——這是該章的核心洞見，文字要三段、圖只要一眼
  - **附錄 P（38）事故應變的分岔**：把「直覺反應 → `kubectl delete pod` → 證據全毀 + controller 重建一個一樣被入侵的」與「正確順序 隔離→蒐證→評估→清理」畫成兩條路徑對照
  - **附錄 AE（53）三種注入方式的熱重載行為**：env／volume 掛目錄／volume+subPath 三條各自的結果，用顏色區分「完全不變（紅）」與「會更新但要自己重讀（黃）」
  - **附錄 AK（59）Phase 0–4 路線圖**：橫向時間軸，每個節點帶該階段的唯一驗收標準
- 圖解總數 72 → 77，總目錄與 index 的數字同步更新

## [2026-08-16] refactor | 補圖解再五處（loop 第三十四輪）

- 延續上一輪，挑「文字描述會繞、圖一眼就懂」的結構再補五張：
  - **附錄 AA（49）Kafka partition 並行上限**：3 個 partition 對 5 個 consumer，後兩個標紅為「完全閒置」——這是文字講三句還會被誤解、但圖只要一眼的典型
  - **附錄 S（41）gang scheduling 死鎖**：把「沒有 gang scheduling → 6 個排上 2 個 Pending → 互等且持續佔資源」與「Kueue 先評估整組、拿不到就保持 suspend 完全不產生 Pod」畫成兩條路徑對照
  - **附錄 AH（56）舊 JS 404 的時間軸**：改用 `sequenceDiagram`（全書第一張），因為這個問題的本質是**時間順序**——10:00 載入 v1 HTML、10:05 部署 v2、10:07 點擊觸發載入已被覆蓋的 chunk
  - **附錄 W（45）可用性相乘**：三層 99.9% → 99.7%（每月多 1.3 小時）與五層 → 99.5%（每月多 3.6 小時）並排，並點出「每個服務都很可靠、串起來卻不可靠，而且不會出現在任何單一服務的儀表板上」
  - **附錄 Y（47）相容性的兩個方向**：向後相容（提供方負責）與向前相容（呼叫方負責）畫成雙向箭頭，說明「② 決定了你能不能安全加欄位，而它不是你能單方面控制的」
- 圖解總數 77 → 82；總目錄與 index 同步

## [2026-08-16] refactor | 補圖解收尾四處（loop 第三十五輪）

- 補圖路線收尾，最後四張：
  - **附錄 K（33）飽和度落差**：allocatable 100% 之下，排程飽和度 85%（已排不進新 Pod）vs 真實飽和度 25%（機器幾乎閒著），差距 60% 標紅為「你付錢買的空氣」；並補一句「這也是為什麼『加節點』常常是錯的第一反應」
  - **附錄 AJ（58）認證授權分工**：邊界層驗簽章 → 401、應用層驗權限 → 403，並用虛線標出「叢集內其他 Pod 可直接打 Service 繞過邊界，所以應用仍要驗」的縱深防禦路徑
  - **實戰 5 連線池乘法**：HPA 3→20 副本 × 預設 100 = 2000 條 → Oracle processes 上限 500 → 全站掛掉 → **擴容這個動作本身就是壓垮資料庫的原因**，把整條因果鏈畫成一條線
  - **附錄 O（37）責任邊界**：以「這件事對所有服務都一樣嗎」當決策節點分流到平台團隊/應用團隊，並標出「平台提供預設值與工具、不提供決策」
- 過程中修正一處自己的失誤：practice-5 的第一次編輯只在程式碼區塊裡多插了一行空白（anchor 選錯），已改正並補上正確的圖
- 圖解總數 82 → 86（41 檔含圖）；總目錄與 index 同步
- **補圖路線至此結束**——其餘無圖的檔案（題庫、速查表、術語表、欄位參考）本質上不需要圖，再補會變成為了畫圖而畫圖

## [2026-08-16] ingest | 附錄 AM：合規與稽核（loop 第三十六輪）

- 先驗證缺口：`ISO 27001|SOC 2|PCI` 0 篇、「職務分離」0 篇、「存取審查」0 篇、「資料保存政策」0 篇、`audit trail` 僅 1 篇——**安全講了預防（第 8 章）與應變（附錄 P），但沒講「怎麼向稽核者證明」**，對公司環境的管理員是真缺口
- 核心區分：**安全問「有沒有做」，合規問「能不能證明有做」**；多數團隊的合規成本集中在後者（稽核季花兩週截圖）
- 八類控制項對應表：存取控制→RBAC、職務分離→GitOps PR review、變更管理→git 歷史、稽核軌跡→audit log、資料保護→etcd 加密、可用性→還原演練、供應鏈→掃描簽章、設定基線→PSA
- **反過來讀這張表**：照本教材建了 GitOps/PSA/audit log/演練的人，其實已滿足大部分控制項，只是證據沒整理成稽核者看得懂的形式
- 變更管理的三個漏洞：手動 kubectl（`selfHeal` 讓它技術上做不到，比規定有效）、緊急變更（要有事後補登流程）、**平台層變更常不在 manifest repo 裡**
- audit log 的五種稽核查詢；其中「篩非 ArgoCD ServiceAccount 的寫入操作」同時是合規證據與漂移偵測
- 個資盤點最常漏掉的兩處：**日誌與備份**；刪除請求在備份保留期內無解，要事先決定三種處理方式之一
- Part 6 是重點：**policy as code 同時做到強制執行、證明存在、證明有效**三件事，傳統環境要分別準備；演練與檢討紀錄要當下就記，事後回想沒有證據力
- 附十個常見稽核提問與「你該能拿出什麼」對照、五類檢查清單、十項誤區
- 教材規模：74 → **75 份文件**，45 → **46 附錄**，約 46.2 萬字

## [2026-08-16] ingest | 附錄 AN：有狀態服務要不要進叢集（loop 第三十七輪）

- 驗證缺口時先撞到一個自己的疏漏：初次 grep 用「StatefulSet 的限制／要不要搬進叢集」等窄字串得 0 篇，**但其實已有附錄 R `40-operators-and-stateful`**。補查後確認兩者互補而非重複——R 是「決定要做了，怎麼操作」（擴縮容、換版、主從切換、寫 operator 六原則），AN 是「該不該做」；`PDB`／`反親和`／`還原演練`／`託管服務`／`quorum`／`HPA` 在 R 裡全部 0 篇
- 據此把 AN 的 operator 評估清單砍掉與 R 重複的六項通用準則，改為「那份先讀」+ 只補資料庫場景額外的三題；並在 R 的連結區加一行點明分工
- 核心論點：**StatefulSet 不是資料庫的解決方案，只是讓資料庫「有可能被管理」的最低基礎**；它沒給的五件事（備份／選主故障轉移／資料一致性／版本升級的資料遷移／擴縮容資料重分布）全都是資料庫維運的核心工作
- 決策樹四題 + **「資料掉了能不能重建」是最好用的單一判準**；中間地帶特別提醒 Redis 當快取可重建、當 session store 不可重建，Kafka 當緩衝可重建、當 event sourcing 是唯一真相
- 進叢集的八項底線（前三項 PDB／反親和／可靠儲存**會在同一時刻一起爆炸**：升級叢集 → drain → 沒 PDB → 副本同機 → 全滅）；反親和要用 `required` 不是 `preferred`
- Part 7 明講「應用進叢集、資料庫留外面」是多數企業的合理終點，附四階段遷移順序與一條晉級標準：**上一步經歷過真實非計畫性故障並順利恢復**
- 順手修正 markdownlint MD036：61、62 兩份的檢查清單分組用粗體當標題，改為 `###`（corpus 慣例）；腳本過度匹配把兩句強調句也轉成標題，已還原
- 教材規模：75 → **76 份文件**，46 → **47 附錄**，約 46.8 萬字、87 張圖

## [2026-08-16] refactor | 資產配置教材搬遷至 wiki/personal/ 並結束 loop（第十四輪，收尾）

- 使用者裁決兩件從第一輪就懸著的事：① loop 停止 ② 教材搬到 `wiki/personal/concepts/`
- **搬遷**：`wiki/tech/concepts/資產配置與投資/` → `wiki/personal/concepts/資產配置與投資/`，21 個 .md 全數移動，原位置無殘留。這是 vault 首次建立 `wiki/personal/` 分支，符合 CLAUDE.md 的三層架構語意（主題是理財不是技術，frontmatter 原本就標 `domain: personal`）
- Obsidian wikilink 不寫完整路徑，搬遷不會造成斷鏈；`index.md` 的路徑註記已同步更新，log.md 舊條目依 append-only 原則不修改
- cron job `ce59569a` 已刪除，撰寫循環結束

### 教材最終交付清單

| 項目 | 內容 |
| --- | --- |
| 正文 | 15 章，四部（認清處境／認識積木／組裝配置／長期作戰）|
| 補充篇 | 1 章（房地產與資產配置）|
| 附錄 | A 術語表約 90 條、B 數字速查十一節、C FAQ 45 題、D 自我檢測 60 題 |
| 圖解 | 5 張 Mermaid（曝險集中／地基順序／風險拆解／分桶／自動化流水線）|
| 驗收 | 跨章數字重算並修正費用率表（640→680 萬）、wikilink 18 目標無斷鏈、mermaid 語法自查 0 問題 |

### 全書主線（供日後查詢時快速定位）

1. **起點**：工程師的人力資本是金融資產十倍且完全未分散，且與股市同時受傷 → 配置要看「職涯＋金融資產」的整體風險
2. **可控 vs 不可控**：成本、稅、配置比例、儲蓄率、行為可控；報酬不可控。前十年儲蓄率勝過報酬率
3. **核心機制**：報酬線性相加、風險不是（ρ<1 就是免費午餐）；分散只消得掉非系統性風險 → 市場只為不可分散的風險付錢
4. **台灣落地**：三條管道最大差別是稅不是手續費；不課證所稅 → 低配息低周轉最有利；ETF 註冊地決定股息預扣與遺產稅
5. **最大風險是自己**：行為差距每年一到三個百分點；知道偏誤不會免疫 → 改架構（IPS、自動化、降低查看頻率、7 天冷靜期）

## [2026-08-16] ingest | 附錄 AO：在叢集裡跑 CI 與建置（loop 第三十八輪）

- 這次先把 76 篇的完整目錄讀過一遍再挑題（上一輪窄字串 grep 漏掉既有附錄 R 的教訓），比對出兩個候選：SLO/錯誤預算（`burn rate` 0 篇但 14 章與 practice-6 已覆蓋告警基礎 → 只是**深度**不足）、在叢集內跑 CI（`kaniko`/`buildkit`/`dind`/`build cache` **全 0** → 真空白）。選後者，且直接對應使用者的 GitHub Actions stack
- 三個正當驅動力：託管 runner 成本、要連內網資源、需要特殊規格；但風險結構與跑一般應用完全不同——**runner 執行的是任意程式碼**
- 建容器三條路的風險差：**掛節點 Docker socket ＝ 交出整台節點控制權，而且 RBAC 擋不住**（整件事發生在節點 daemon 層，API Server 看不到）→ DinD 需 privileged，讓 Pod Security 形同虛設 → 無 daemon 建置器是預設
- 快取是「搬進叢集後變慢」的主因：要分開處理基礎映像／建置層／套件相依三層；registry 後端無狀態較佳，PVC 有並行競態且易變成隱藏狀態。判準：**清空快取重跑，結果必須不變**，否則 CI 已經壞了只是還沒被發現
- runner 用完即丟不只是衛生問題也是安全問題（惡意 job 可在常駐 runner 留東西等下一個高權限 job）
- 最重要的一條：**CI 只推映像 + 改版本號，不該有叢集寫入權**——否則任何能改 workflow 檔的人就能改生產；這一刀同時讓附錄 AM 的職務分離成立
- 資源面：CI 是突發型且**中斷容忍度高**，適合低優先級 + 專用節點池 + spot 機器
- 決策表六種情況，並指出混合最務實；附一個常被低估的提醒：**CI 掛掉是整個團隊停止交付，包含緊急修復所需的發布**
- 教材規模：76 → **77 份文件**，47 → **48 附錄**，約 47.4 萬字

## [2026-08-16] ingest | 附錄 AP：SLO、錯誤預算與告警設計（loop 第三十九輪）

- 上一輪標記的深度缺口。先確認既有覆蓋只到**原則層**：實戰 6 有一句「從 SLO 導出告警」、附錄 H 清單一行「每條告警對應 SLO」、14 章講機制（Recording/Alerting Rules、Alertmanager）——**沒有一份說怎麼訂、怎麼算、怎麼寫成規則**
- 開場論證為何指標門檻式告警必然失敗：`CPU > 80%` 問的是「零件如何」，但你在乎的是「使用者受不受影響」；三列對照顯示它同時造成誤報與漏報，而**誤報累積會讓人忽略告警，於是漏報那次也沒人理——兩種錯誤互相放大**
- 錯誤預算換算表（自行核算過）：99% = 7h12m／月、99.9% = **43 分鐘**、99.95% = 21 分鐘、99.99% = **4 分 19 秒**、五個九 = 26 秒。用途是壓下不切實際的目標：**超過 99.99% 不是「更努力」能達成的，它要求架構上不存在需要人介入的故障模式**
- 訂 SLO 的三個常見錯：把 4xx 算成失敗（服務正常運作，SLO 會被使用者行為綁架）、用含健康檢查的全端點平均、第一次就訂得太嚴（該先量兩週、訂在略低於現況）
- **延遲 SLI 要寫成比例而非 P95 門檻**——這是 SLO 實作最常卡住的一步，因為 P95 接不上錯誤預算
- Part 4 核心：多視窗燃燒率。長窗判斷「嚴不嚴重」、短窗判斷「還在不在發生」，兩者同時成立才告警（附圖）；四組標準門檻 14.4/1h、6/6h、3/1d、1/3d 皆核算過（14.4×1/720 = 2%），**上兩列叫人、下兩列開工單，這個分界就是告警疲勞的解方**；附兩條可直接抄的 PromQL 與「用 Recording Rules 先算長區間」的實務提醒
- 告警四分類：症狀叫人、**迫近耗盡叫人**（磁碟／憑證，判準是「晚了就來不及」）、原因進儀表板、資訊進儀表板；檢驗法「收到之後我要立刻做什麼」答不出來就不該叫人
- runbook 最小四段，**第 4 段「升級給誰」最常被漏掉卻最重要**；並主張「這一季刪掉幾條告警」是比新增更健康的指標
- 教材規模：77 → **78 份文件**，48 → **49 附錄**，約 48 萬字、88 張圖

## [2026-08-16] ingest | 附錄 AQ：接手一座既有叢集（loop 第四十輪）

- 本輪先否決兩個候選才定案：**多租戶隔離**（37 章 Part 4 已有軟硬隔離維度表、何時拆叢集、共享 CoreDNS/APF，再寫會大幅重疊）、**叢集建置**（`control plane HA`／`CNI 選型` 雖 0 篇，但 12 章已有「叢集組成與生命週期」「minikube 與正式環境差異」）。最後選了 `現況盤點` 0 篇、`找出未知數` 0 篇的真空白
- 定位：附錄 AK 是**從零導入**（白紙、可以照順序做對），這份是**接手**（叢集在跑、建它的人要走、下週起是你的）。兩者難度不同——從零導入你知道每個決定怎麼做的，接手是要在不知道裡面有什麼的情況下負責
- 核心心法：**你最大的風險不是你不會的東西，是你不知道它存在的東西**；不會的可以查可以問，不知道存在的會在半夜自己出現
- 第一週只看不動（不是膽小——你還不知道誰依賴那個「明顯該修」的東西），附完整 PowerShell 盤點指令與「每個指令在找什麼／危險訊號」對照；特別點出 **`webhookconfiguration` 是最容易被埋伏的一項**：失效的 webhook 讓相關 apply 全面失敗，而訊息不會指向它是三年前的實驗遺留
- 六個要證據不要口頭保證的問題，其中第 3 題最關鍵：**「叢集裡的東西有多少在 git 裡」決定你接下來三個月的工作內容**；三種答案對應三種工作量，「不在 git 裡」＝叢集是唯一真相、掛了無法重建
- 風險排序準則 **爆炸半徑 × 發生機率 × 能不能復原**，第三項最常被忽略；P0 的共同特徵是「發生了就回不來」，排第一不是因為機率高而是沒有第二次機會。核心主張：**先做能止血的，不要先做能展示的**——順序反了的代價不對稱
- 前 90 天五項安全網（還原演練 → 現況進 git 即使很醜 → 最小告警集 → 三頁 runbook → 逃生門）；並主張「未整理但在 git 裡，勝過整理中但只在叢集裡」
- Part 5 是技術盤點沒有的那一半：交接該問前任的十題（第 1、5、9 題最有價值，問的是文件裡不會有的東西）、期待管理（**前三個月的產出是「可理解、可復原」，不是「加了什麼新東西」**）、以及「這個我不知道」是專業回答
- 90 天三個里程碑全部寫成**「做過」而非「知道」**：重建過、告警真的響過、別人照 runbook 跑過
- 教材規模：78 → **79 份文件**，49 → **50 附錄**，約 48.6 萬字、89 張圖

## [2026-08-16] ingest | 附錄 AR：從 Ingress 遷移到 Gateway API（loop 第四十一輪）

- 缺口驗證：`Gateway API` 欄位在 22 章（第 486 行起）、05、20 章已有，但 **`Ingress 遷移`／`Ingress 凍結` 皆 0 篇**——有欄位參考、沒有遷移指引
- 開場論點：**附錄 F 那份 ingress-nginx annotation 百科的存在本身，就是 Ingress 出問題的證據**——如果規格夠用，就不需要一整份文件來記某個 controller 私有的擴充語法
- Ingress 的三個結構性問題：規格太小導致 annotation 地獄（換 controller 時那些設定**靜默地不生效**）、**沒有角色分離**（TLS 與路由規則混在同一物件，只能在「應用團隊能改 TLS」與「平台團隊變瓶頸」之間二選一）、表達力不足
- 核心澄清：**Gateway API 的價值不是功能比較多，而是這些功能寫在規格裡而不是 annotation 裡**——所以換 controller 不用重寫路由；三層拆分（GatewayClass／Gateway／HTTPRoute）本身就是設計目的，是附錄 O 責任邊界在網路層的實作（附圖）
- annotation 對照表**右半邊才是重點**：能對應的直接翻譯、實作專屬的（逾時／body 大小）功能還在但可攜性又沒了、**無標準對應的（限流／外部認證）要往上或往下搬層**——而這往往是好事，因為它逼你把職責分層想清楚
- 遷移策略：**並行而非切換日**，兩個 controller 各有對外位址、用 DNS 逐服務切、舊路由留著當回滾路徑；強調「比對新舊回應」不可跳過，因為路徑改寫在尾斜線／編碼字元上的差異測試環境常看不出來
- Part 5 誠實列出**不該換**的情況，並提出中間立場：**新服務用 Gateway API、既有服務不動——遷移可以是一個預設值而不是一個專案**
- 實作卡點：`ResolvedRefs: false`（多半是忘了 `ReferenceGrant`）症狀是「路由完全沒反應」而非報錯，故養成「先看三個 condition 再測流量」的習慣
- 教材規模：79 → **80 份文件**，50 → **51 附錄**，約 49.2 萬字、90 張圖

## [2026-08-16] ingest | 附錄 AS：叢集長大之後——規模瓶頸與 API Server 保護（loop 第四十二輪）

- 先否決 DNS 深入（`ndots` 7 檔、`conntrack`、NodeLocal、`dnsPolicy`／`dnsConfig` 均已覆蓋）。真缺口：**`watch cache` 0 篇、`大量 list`／`API Server 記憶體` 0 篇、`etcd 大小` 僅 1 篇**
- 核心翻案：多數人以為規模瓶頸是「節點不夠」或「Pod 排不下」——**幾乎不是**。那兩個有明確訊息與現成解法；真正會讓管理員半夜起來的是**控制平面被拖垮**（kubectl 變慢、部署卡住，而節點 CPU 都很閒）
- 官方上限（110 Pod/節點、5000 節點、15 萬 Pod）標註為隨版本演進、以自己版本文件為準；並指出**你幾乎不會先撞到它們**，會先撞的是 etcd 容量、API Server 記憶體、watch 連線、Event 洪水
- 最重要的觀念：**規模問題通常不是「總量」問題，是「某個東西行為不當」的問題**——一個寫得差的 controller 能打垮 50 節點的叢集，所以「我們叢集不大不用擔心」是錯的推論
- etcd 是最硬的牆：**滿了整個叢集唯讀，連刪東西都不行（刪除也是寫入）**；三個常見意外來源是 Event、Helm release 歷史、沒設 `ttlSecondsAfterFinished` 的 Job 累積
- API Server 那節點出最惡劣的性質：一次大 `list` 可吃數 GB 記憶體導致 OOM，而**復原時所有 controller 同時重新連線、重新 list，會重現造成它掛掉的負載**；找兇手最快的路徑是 `userAgent` label
- 四道防線（源頭 informer → APF → 減量 → 監看，附圖）；強調 **APF 是唯一能單方面部署、不需別人配合的防線**，也是附錄 O「一個團隊打爆 API Server」的直接解方
- 領先指標：**etcd 寫入延遲**變差時還有時間，等 `kubectl` 變慢通常已在事故裡
- Part 6 拆叢集判準：**拆是為了縮小爆炸半徑，不是為了效能**；動機若是效能就先做完三道調校
- 教材規模：80 → **81 份文件**，51 → **52 附錄**，約 49.8 萬字、91 張圖

## [2026-08-16] ingest | 附錄 AT：映像 Registry 的營運（loop 第四十三輪）

- 本輪否決三個候選：`ephemeral container`／`kubectl debug`（11 檔已覆蓋）、service mesh 決策（45 章 Part 6「Service Mesh 解決什麼、不解決什麼」已有）、DNS 深入（上輪已否決）。剩下的真零：**`registry 掛`／`immutable tag`／`多架構`／`映像清理` 全 0**——K8s 這端的欄位（`imagePullPolicy`／`imagePullSecrets`／`ImagePullBackOff`／`digest`）都寫過，但 **registry 作為要維運的系統**是空白
- 開場最重要的觀察：**registry 掛掉時，你的監控大概率是綠的**——現有 Pod 都在跑、SLO 沒變化，直到某個觸發拉取的事件發生，而那事件常常正是「節點故障」，也就是你最需要系統自我修復的時刻。結論：**registry 的可用性要求等同於你最重要服務的可用性要求**
- `imagePullPolicy` 的隱含規則：沒明寫時依 tag 決定預設（`latest` → `Always`，其他 → `IfNotPresent`），造成一類極難查的 bug——**同一個版本 tag 被覆寫，A 節點有舊的就不去拉，於是不同節點跑著不同內容，而所有 YAML 看起來一模一樣**
- GitOps 視角：`latest` 讓 ArgoCD 永遠顯示「同步」即使 registry 上的內容換了三次——**它讓 git 不再是真相來源**，與 GitOps 前提直接衝突。建議 tag 不可變 + 生產用 digest 釘死、由 CI 寫回 manifest
- 速率限制型 `ImagePullBackOff`：映像存在、名字正確、權限也對，但拉不下來，關鍵字是 `toomanyrequests`；**而且是間歇性的**，因此常被誤判成「網路不穩」而長期存在。pull-through cache 一次解決速率限制／速度／外部不可用／離線四件事
- 保留政策最大的陷阱：**刪掉正在用的映像當下毫無症狀**（Pod 在跑、映像在節點本機），直到節點重啟或重排才爆，而那時已回不去。故清理前必先掃叢集在用的映像，且別漏 initContainers、ephemeralContainers 與保留的回滾歷史
- 另補 pull secret 是 namespace 範圍造成的輪替漏網、admission 限制映像來源前綴（成本最低卻最常被忽略）、以及 `exec format error` 與多架構 manifest list——並明講**單一架構就不要做多架構建置**
- 教材規模：81 → **82 份文件**，52 → **53 附錄**，約 50.4 萬字、92 張圖

## [2026-08-16] ingest | 附錄 AU：第三份自我檢測（loop 第四十四輪）

- 這輪改補**結構缺口**而非新主題。驗證方式是比對兩份既有檢測實際引用到的章節：附錄 A 涵蓋正文 00–15，附錄 X 涵蓋實戰篇與附錄 E–W（27–45）——**附錄 Y–AT（47–68）共 22 份、約 13 萬字，一題都沒被考過**，與當初附錄 X 誕生的理由完全相同
- 出題前先抓 47–58 的章節骨架當事實依據（那批不是本次 session 寫的），避免自我檢測出現與原文不符的答案——這比憑印象出題重要，因為錯的答案比沒有答案更糟
- 70 題，七個主題分區（介面演進與測試／訊息快取背景工作／儲存設定開發體驗／日誌前端資料庫連線／邊界 Gateway SLO／合規 CI registry／規模決策接手），沿用附錄 X 的 🟢🔵🔴 三級標記與 `<details>` 摺疊格式
- 全部針對「答錯會造成實際損失」的判斷而非名詞背誦，例如：Kafka 擴 consumer 沒用（並行上限是 partition 數）、應用內排程 × 3 副本會跑三次、CronJob **預設允許重疊**、連線數是 Pod 數 × 池大小的乘法、`imagePullPolicy` 依 tag 決定預設值造成不同節點跑不同內容、registry 掛掉時**監控是綠的**、etcd 滿了**整個叢集唯讀連刪都不行**
- 收尾附 10 題紅色警戒清單（一句話答案），是全份「答錯不可逆」的核心
- 修正一處自己的 markdown 失誤：題 67 標題內層再用粗體造成巢套（`**… **沒有** …**`）會 render 錯，已改；驗證 `<details>` 70/70 配對、題號 70 題完整、無巢套粗體殘留
- 教材規模：82 → **83 份文件**，53 → **54 附錄**，約 51 萬字；三份自我檢測合計 **289 題**

## [2026-08-16] ingest | 附錄 AV：節點生命週期與控制平面高可用（loop 第四十五輪）

- 上一輪說剩下的都是窄題，這輪把幾個零合併成一個主軸：`節點退役`／`不可變基礎設施`／`SSH 上節點`／`control plane HA`／`節點自動修復`／`gVisor|Kata` **全部 0 篇**，而它們共享的主題是「節點層」。allocatable 三塊保留已在 12 章第 344 行寫透，故本份不重複
- Part 1 心態題：SSH 上節點修東西的真實傷害不是「不優雅」，而是**新節點不會有你的修改**——修好了、症狀消失、叢集半夜自動擴容一台新的，症狀回來而你已經不記得怎麼修的。判準：「這台節點現在消失，我能不能十分鐘內得到設定完全一樣的一台」
- Part 2 一條必須知道的時間線：節點失聯 → 約 40 秒標記 `NotReady` 並加 taint → 約 5 分鐘 toleration 到期才驅逐，**預設空窗約五分半鐘**（附圖，並註明各版本／託管平台預設不同要自己查）。關鍵推論：**單副本服務在節點故障時中斷數分鐘是設計上的正常行為**，想更快的方向是多副本 + 跨節點分散，不是調短參數（調太短會讓網路抖動觸發大規模誤驅逐）
- 自動修復的反噬：若讓節點不健康的原因是叢集層面的（壞掉的 DaemonSet、網路元件），自動修復會輪流重建所有節點而每台重建後仍不健康——**陷入全叢集重建迴圈，比原問題嚴重得多**。故必須有速率限制且動作時通知
- Part 3 最反直覺的一列：**兩台 etcd 比一台更糟**——過半數是 2，任一台掛就失去 quorum，可容忍故障數同樣是 0 但機器數加倍即故障機率加倍；4 台的容錯與 3 台完全相同。並釐清四個控制平面元件的 HA 模式不同：API Server 無狀態可水平擴展、controller-manager／scheduler 是 leader election（多台只是熱備）、**只有 etcd 有過半數限制**
- 失去 quorum 的準確描述：叢集停止寫入，但**現有 Pod 繼續跑（kubelet 不需要 API Server 就能維持），失去的是所有自我修復能力**
- Part 4 沙箱執行時給出順序建議：**先用專用節點池 + taint，不夠再上 gVisor/Kata**——節點池成本低得多且解決大部分場景；多數內部工作負載不需要
- Part 5 汰換四要點：先加再減、PDB 擋住是保護不是問題（不要 `--force`）、一次一台、有狀態的最後動；並指出定期汰換的第三個理由是**確認汰換流程真的能用**——沒演練過的流程在緊急時不會順利
- 教材規模：83 → **84 份文件**，54 → **55 附錄**，約 51.6 萬字、93 張圖

## [2026-08-16] ingest | 附錄 AW：資料庫 Schema 變更與部署的交界（loop 第四十六輪）

- 候選比較：egress 固定出站 IP（05/35 已寫 SNAT 與來源 IP，`egress gateway` 0 但屬補丁）vs schema migration。選後者，因為核心陷阱 **`多副本同時 migrate` 0 篇**，且既有零件散落三處（11 章寫 `PreSync` 機制、47 章五行 expand-contract、practice-5 提及）**缺的正是交界處的整合**
- 核心洞見：**滾動更新讓每一次部署都變成「新舊版本並存」**，只是並存期很短——所以 expand-contract 不是「有多版本 API 才需要的進階技巧」，而是**每一次 schema 變更都需要的基本功**。這一句把 47 章的特例翻轉成通則
- 危險區間 T2（migration 已跑、舊 Pod 未退場）的四種致命變更；其中 **加 `NOT NULL` 無預設值最陰**：不影響讀取所以健康檢查是綠的、首頁正常，只有寫入路徑全掛，你會從使用者回報而非監控得知
- 把 expand-contract 展開成跨三次部署的可執行步驟（欄位改名完整例），並附「每一步可不可回滾」對照——前兩步天生可回滾、第三步不可逆故須獨立部署。點名多數團隊的錯誤是**把三步壓成一次部署**
- Part 3 是本份最實用的一段：五種 migration 執行形式對照，**應用啟動時與 `initContainer` 都會讓每個副本各跑一次**；即使工具有鎖也帶來三個實際問題（啟動變長撞 `startupProbe` 形成重啟迴圈、鎖在連線中斷時可能不釋放導致整個服務起不來、自寫腳本根本沒鎖）。推薦 `PreSync` 單一 Job + **`backoffLimit: 0` 刻意不重試**——部分套用的狀態重試只會更亂
- Part 4 回滾：**應用可以回滾，schema 不行**；down script 對刪除類變更是幻覺（**結構能還原，資料不行**），真正的回滾能力來自 expand-contract 的紀律。提出一個比任何清單都有效的問題：**「如果我五分鐘後要回滾，會發生什麼？」**
- Part 5 長 migration 的雙重問題：鎖表時監控顯示的是「延遲暴增」而非「migration 在跑」；且 `PreSync` 卡住會**擋掉包含緊急修復在內的所有部署**。原則：超過幾分鐘的不該在部署路徑上，把快的結構變更留下、慢的資料回填拆成分批背景工作
- 附六題可直接貼進 PR 模板的規則，第 1 題答「不能」即代表這個 PR 本身就錯了
- 教材規模：84 → **85 份文件**，55 → **56 附錄**，約 52.2 萬字、94 張圖

## [2026-08-16] ingest | 附錄 AX：級聯失敗與韌性模式（loop 第四十七輪）

- 缺口掃描：`重試風暴`／`超時預算`／`艙壁`／`級聯失敗` **全 0**；`熔斷` 那 6 筆是 Istio 欄位與 probe 脈絡、`重試放大` 2 筆是附錄 Q/W 的簡略提及。也就是說教材寫了「怎麼定位變慢」（附錄 Q）與「四種通訊模式」（附錄 W），但沒寫**為何一個非關鍵下游變慢會讓整站掛掉**
- 全份核心一句：**慢比掛更危險**。掛掉是快速失敗、執行緒馬上釋放；變慢是每個請求都佔著執行緒與連線，幾秒後池滿、於是你也慢了。故障沿呼叫鏈往上傳染的是「慢」不是「錯」（附圖：非關鍵的推薦服務 → 商品 API → BFF → 整站不能用，含登入結帳）
- 補一個常被誤解的點：**多副本救不了共同依賴變慢**——副本數提供的是單副本故障的冗餘，10 個副本會同時被同一個慢下游卡住
- 重試放大把算術做完：三層各重試 3 次 = **27 倍**，且發生時機是對方已經有問題的時候——**重試的本質是在對方最脆弱時給對方 27 倍負載**；很多事故的規模是重試造成的而非原始故障。三條規則：只在單層重試、只重試冪等、退避**必須加抖動**（沒抖動只是把持續過載變成週期性尖峰）
- 超時那節點出最常見的做錯法：**內層超時比外層長 = 內層超時永遠不會生效**，外層放棄了但內層請求還在跑、還佔著資源，而且沒有人在等它的結果。並提醒外層預算要涵蓋內層的「超時 × 重試次數」
- Part 5 講 K8s 自身機制的極限：**readinessProbe 不該檢查下游依賴**，否則所有副本同時被移出 endpoint =「服務完全消失」，而它們其實還能提供部分功能——**降級的服務遠好過沒有服務**；以及 **下游是瓶頸時 HPA 是加油不是滅火**（延遲上升 → 擴容 → 更多副本打同一個過載下游 → 更慢 → 繼續擴容）
- Part 6 給明確優先序並反對過早導入 mesh：**多數團隊的問題不是缺少進階韌性模式，而是超時根本沒設**；第 1 項做完就解決了大部分級聯失敗，且不需要任何新元件。收尾強調沒被注入故障驗證過的韌性設定「跟沒設定的差別只在你的自信程度」
- 教材規模：85 → **86 份文件**，56 → **57 附錄**，約 52.8 萬字、95 張圖

## [2026-08-16] ingest | 附錄 AY：長連線（gRPC／WebSocket）在 K8s 上的行為（loop 第四十八輪）

- 缺口：`HTTP/2` 0 篇、`L4 負載平衡` 0 篇、`WebSocket` 僅出現在 28 章的 annotation 表、`負載不均` 1 篇。而 45 章對這題只有**兩行**（line 153 + 誤區 #9），05 章的連結還註明「gRPC 長連線的負載平衡坑」指向 45——等於教材自己承認有這個主題卻沒寫
- 全份的統一視角：**四個看起來無關的症狀根源同一個**——HPA 擴了沒改善、部分 Pod 滿載其他閒置、部署後使用者斷線、WebSocket 每 60 秒斷一次。原因是 **K8s 的預設網路模型是為短連線設計的**，而 gRPC／WebSocket／SSE 都是長連線
- Part 1 機制：kube-proxy 在**建立連線的那一刻**分配一次，之後不再介入；HTTP/2 把「多條連線」壓縮成「一條」，於是把 HTTP/1.1 的輕微不均放大成嚴重問題。點出最強指紋：**「重啟客戶端就好了」**——也解釋了為何這問題常被誤判成客戶端 bug
- 四種解法中特別標記**限制連線壽命是被低估的一項**：純伺服器端、不需客戶端配合、不需 mesh，對「只是想讓負載均勻一點」通常就夠
- Part 3 部署斷線：Pod 終止流程對短連線完美、對長連線不夠（寬限期到就硬砍）。三件事要做，並強調**第三項「客戶端自動重連」才是根本**——因為節點故障與網路抖動都會斷線，前兩項只是把「有感中斷」變成「無感重連」。呼應附錄 AV：**Pod 可拋棄，所以連線必須可重建**
- Part 4 路徑上每一層的逾時：「WebSocket 每 60 秒斷一次」幾乎一定是 Ingress 讀取逾時；而 NAT 那層調不了，正解是應用層 keepalive，且**間隔必須短於路徑上最短的閒置逾時**
- Part 5 三個少被提及的互動：HPA 對長連線反應遲鈍（既有連線不會搬家，擴容要更早更保守）、**同時連線數本身是一種容量維度**（閒置連線也佔資源，只看 CPU 會漏掉真正瓶頸）、**金絲雀權重只影響新連線**故觀察期要拉長
- 教材規模：86 → **87 份文件**，57 → **58 附錄**，約 53.4 萬字、96 張圖

## [2026-08-16] ingest | 附錄 AZ：分散式追蹤（loop 第四十九輪）

- 本輪先否決標籤治理（03 章 244–289 行已有 labels/annotations 之別、推薦標準 labels、selector 用法，再寫會重疊）。改查可觀測性第三支柱，發現一個很乾淨的缺口：**教材到處推薦「導入分散式追蹤」——它甚至出現在附錄 Q 的檢查清單裡——但 `context propagation` 0 篇、`取樣` 僅 1 篇（且是日誌脈絡）**。metrics 有完整一章、logs 有兩章，第三支柱只有推薦沒有做法
- 價值定義成一句：**把「哪裡慢」從推理變成觀察**；並指出服務數越多價值越大，因為推理的分支數是指數成長的。附一段 ASCII 時間軸示範「800ms 花在哪」是一個畫面而非一串猜測
- Part 2 只留三個必要概念（span／trace／context propagation），並把重點放在 **context propagation 是最容易失敗又最難察覺的一環**——斷一處後面全是孤兒 trace，然後團隊會得出「追蹤沒什麼用」的結論。四個常見斷點中**訊息佇列最痛**：非同步流程本來就最難除錯，卻正好是 trace 最容易斷的地方（附圖）
- 導入順序主張自動優先：一開始就手動埋點會埋在「你以為重要」的地方，而那通常不是實際瓶頸——先讓自動的告訴你瓶頸在哪，再去那裡加細節
- Part 4 取樣是成本與價值的核心取捨：**head-based 取樣 1% 的意思是 99% 的錯誤 trace 也被丟掉了**，而你需要 trace 的時刻恰恰是出問題的時刻；tail-based 的操作限制（同一 trace 的所有 span 要進同一 collector 實例）也寫明，那是多層 collector 架構存在的主要理由
- 一個容易產生難察覺錯誤的副作用：**不要用取樣後的 trace 算 metrics**——錯誤偏向取樣讓資料在統計上是偏的，儀表板的錯誤率會比實際高好幾倍
- Part 5 是全份重點：**很多團隊導入了追蹤然後沒人用，原因幾乎都是沒有從告警走到 trace 的動線**。三支柱各自漂亮的儀表板沒有價值，連結才有：trace ID 進日誌（最便宜、投報率最高）、exemplar 從延遲圖跳到真實慢請求，並畫出「告警 → metrics → trace → logs」完整動線——**走得通，可觀測性才算做完**
- 另補：span 屬性夾帶查詢參數與使用者資料是被忽略的個資風險（沒有人在「讀」trace）；以及導入要按**呼叫鏈順序**推進，因為鏈路中斷一處之後就全黑，價值不是線性累加的
- 教材規模：87 → **88 份文件**，58 → **59 附錄**，約 54 萬字、97 張圖

## [2026-09-02] ingest | 新手向單元測試 SOP（unit-testing-sop）

- 缺口：vault 有 [[20-testing]]（dotnet-web-api 第 20 章）但它從「兩種不理想的測試」開講，預設讀者已經會寫測試；`AAA`、`Theory`、`InlineData`、`Assert` 用法 0 篇。等於進階篇有了、入門台階沒有
- 本頁只收兩種內容：**照著做的 SOP**（建專案四步 + 寫測試五步 + 跑測試）與**情境對照表**（12 種狀況 → 該用哪個 API），原理只講到夠用
- 核心是第五節那張表：新手真正缺的不是「什麼是單元測試」，是「我手上這段程式該用哪一招」。把 Fact/Theory/MemberData/不變式/Record.Exception/Assert.Throws/集合斷言/IsType 逐層剝/golden/假物件/async/private 排成一張查表
- 兩個刻意寫進去的判斷句：**「程式很難測時先改設計，不要硬測」**（情境 10）、**「把內部重寫但 public 行為不變時測試應全綠」**（情境 12，private 不測的判準）
- 坑清單第 1 條是 record 含集合屬性的相等性——record 自動 Equals 對集合走參考比較，內容相同也不相等。這條在測樹狀結構 / 回傳集合的 record 時必踩，且錯誤訊息完全看不出原因
- 雙向 cross-link：本頁 → [[20-testing]]（進階篇），[[20-testing]] 結尾 → 本頁（新手前置）
## [2026-10-17] ingest | React frontend source collection

- 將 `raw/Web Framework/React/` 的核心教材整合為 [[react-frontend-development-roadmap]]，以先備知識與可交付專題排序。
- 路線涵蓋 React 心智模型、Hooks、UI、路由與 Auth、資料層、架構與選修進階主題，方便依產品需求取用。
## [2026-10-17] synthesis | JavaScript, TypeScript, and React foundations

- 建立 [[javascript-typescript-react-foundations]]，用同一個 Task Tracker 說明 JavaScript、TypeScript 與 React 的分工與依賴。
- 將必要基礎與後續再學的進階主題分開，讓 JavaScript 基礎較弱時仍能循序開始 React。
## [2026-10-17] ingest | DOM 節點觀念

- 以 `raw/Web Framework/React/DOM 節點觀念.md` 為底，建立書本式 concept 頁 [[dom]]：HTML vs DOM、節點與繼承鏈、渲染流程、原生 API、Layout Thrashing、事件三階段與委派、React Virtual DOM、錯誤排查。
- 校正原始筆記三處：渲染流程補上 CSSOM、事件補上 Capture 階段、「Virtual DOM 比直接操作 DOM 快」改為精確說法；另補 innerHTML 的 XSS 風險。
- 雙向連結：[[web-frontend-moc]]、[[react]]、[[javascript-typescript-react-foundations]]、[[react-frontend-development-roadmap]] 皆加入 [[dom]]。
## [2026-10-17] query | DOM 冒泡機制擴寫

- 依使用者提問擴寫 [[dom]] 第七章：為什麼事件要在樹上傳遞、三階段驗證範例、路徑派送前固定、target/currentTarget（含 await 後變 null）、stopPropagation vs stopImmediatePropagation、濫用 stopPropagation 的反例、preventDefault 時間點與 passive、不冒泡事件可用 capture 委派、自訂事件預設不冒泡。
- 第八章補 React 冒泡沿元件樹走（Portal 差異）；第九章新增兩個排查項；速查表補四列。
## [2026-10-17] query | DOM EventListener 概念

- 於 [[dom]] 第五章新增「監聽事件：EventListener」：Observer 模式、三要素、傳函式不要呼叫、event 物件、三種登記方式比較、執行時機、options、移除與記憶體洩漏（含 React useEffect cleanup）。
- 原第七章「移除 listener」併入第五章；第七章開頭改為承接第五章；速查表補三列。
## [2026-10-18] query | C# 語法糖

- 依使用者提問（expression-bodied member 等價於什麼、語法糖定義）建立書本式 concept 頁 [[csharp-syntactic-sugar]]：定義與判斷標準、Roslyn lowering 流程、expression-bodied member、各類糖展開對照、重度糖、非糖功能、觀察工具、使用原則、九個排查項、速查表。
- 刻意強調「糖最多只缺型別、非糖缺 runtime 能力」作為舊 target framework 能否用新語法的判準；`int?` 與 `string?` 本質不同列為獨立陷阱。
- 雙向連結：[[csharp]]、[[languages-moc]] 加入本頁；index.md Tech / Concepts 新增一列。
