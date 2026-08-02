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
