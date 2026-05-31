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
- [[git]] — Git 四種物件、常用指令、日常開發 SOP、Branch 策略
- [[oracle]] — Oracle SQL 基本指令、CMD 操作、C# 連接方式
- [[linux]] — Linux 目錄結構、權限、常用指令、Ubuntu 設定
- [[claude-code-skills]] — Claude Code 自訂 slash command，Skills 定義方式、檔案格式與適用時機
- [[python]] — Python 基礎（stub，待整合 raw 內容）

## Tech / Concepts

- [[cicd-pipeline]] — GitLab/Azure DevOps + Harbor + Helm + ArgoCD 完整 CI/CD 流程
- [[domain-networking]] — DNS 概念、Record 類型、Cloudflare、TLS Binding

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
