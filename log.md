# Wiki Log

> Append-only。每筆格式：`## [YYYY-MM-DD] <action> | <subject>`
> action 類型：`bootstrap`、`ingest`、`query`、`synthesis`、`lint`、`refactor`

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
