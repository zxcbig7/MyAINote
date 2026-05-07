# Wiki Index

> 本檔列出 `wiki/` 內所有頁面。回答問題時**先查此檔找線索**。
> 每次 ingest / synthesis 後即時更新。

## Tech / Entities

- [[argocd]] — GitOps 部署控制器，監控 git repo 並 sync 到 K8s 叢集
- [[docker]] — 容器化平台，Image / Container / Repository 核心概念 + Compose
- [[kubernetes]] — 容器編排平台，Pod/Node/Cluster 四元件 + YAML 架構
- [[istio]] — Service mesh，Sidecar 注入、流量攔截、xDS、啟動 race condition 與偵錯
- [[minikube]] — 本機單節點 K8s 開發環境
- [[helm]] — K8s 應用部署打包工具，Chart / Release / values.yaml
- [[kubectl]] — K8s CLI 工具，get/apply/describe/logs/exec 常用指令速查
- [[raw/tech/devops/Vault]] — HashiCorp Secret 管理，K8s 整合、Unseal 流程
- [[typescript]] — 型別系統、Interface vs Type、泛型、Utility Types
- [[react]] — React Hooks 完整說明（useState/useEffect/useCallback/useRef/useContext）+ Zustand
- [[dotnet-web-api]] — ASP.NET Core Web API 架構、Controller、DI、Middleware、JWT
- [[csharp]] — C# 語法重點、OOP、LINQ、async/await
- [[git]] — Git 四種物件、常用指令、日常開發 SOP、Branch 策略
- [[oracle]] — Oracle SQL 基本指令、CMD 操作、C# 連接方式
- [[linux]] — Linux 目錄結構、權限、常用指令、Ubuntu 設定

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

- `raw/tech/devops/Docker.md` ✓ → [[docker]]（已整合 Docker 觀念.md）
- `raw/tech/devops/Docker Compose.md` ✓ → [[docker]]（已整合 Compose yaml 架構 + Compose 重開）
- `raw/tech/devops/Docker 部屬範例.md` ✓ → [[docker]]
- ~~`raw/tech/devops/Docker 觀念.md`~~ → 已整合至 Docker.md
- ~~`raw/tech/devops/Docker Compose yaml 架構.md`~~ → 已整合至 Docker Compose.md
- ~~`raw/tech/devops/Docker Compose 重開.md`~~ → 已整合至 Docker Compose.md
- `raw/tech/devops/Kubernetes (K8s).md` ✓ → [[kubernetes]]
- `raw/tech/devops/K8s YAML 概念與架構.md` ✓ → [[kubernetes]]
- `raw/tech/devops/Minikube 介紹.md` ✓ → [[minikube]]
- `raw/tech/devops/Helm Chart.md` ✓ → [[helm]]
- `raw/tech/devops/kubectl 指令.md` ✓ → [[kubectl]]
- `raw/tech/devops/Vault.md` ✓ → [[raw/tech/devops/Vault]]
- `raw/tech/devops/Azure Pipeline.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/部署筆記.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/部屬後端.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/argocd-tutorial.md` ✓ → [[argocd]]
- `raw/tech/devops/azure-pipelines.md`
- `raw/tech/devops/complete-tutorial.md`
- `raw/tech/devops/harbor-tutorial.md`
- `raw/tech/devops/helm-tutorial.md`
- `raw/tech/devops/k8s-rbac.md`
- `raw/tech/devops/kubectl-api-version.md`
- `raw/tech/devops/minikube-tutorial.md`
- `raw/tech/devops/postgresql-k8s.md`
- `raw/tech/devops/vault-tutorial.md`
- `raw/tech/devops/troubleshooting.md`

### Tech / Web Dev

- `raw/tech/web-dev/TypeScript.md` ✓ → [[typescript]]
- `raw/tech/web-dev/React.md` ✓ → [[react]]
- `raw/tech/web-dev/React/React + TypeScript 開發手冊.md` ✓ → [[react]], [[typescript]]
- `raw/tech/web-dev/NET Web API.md` ✓ → [[dotnet-web-api]]
- `raw/tech/web-dev/HTML.md`
- `raw/tech/web-dev/CSS.md`
- `raw/tech/web-dev/react-hooks-gotchas.md`
- `raw/tech/web-dev/uiux-notes.md`

### Tech / Languages

- `raw/tech/languages/C#.md` ✓ → [[csharp]]
- `raw/tech/languages/C++.md`
- `raw/tech/languages/Python.md`
- `raw/tech/languages/R.md`
- `raw/tech/languages/Assembly Language.md`
- `raw/tech/languages/csharp-debug-test.md`

### Tech / Database

- `raw/tech/database/SQL 資料庫基本指令.md` ✓ → [[oracle]]
- `raw/tech/database/Oracle CMD 指令筆記.md` ✓ → [[oracle]]
- `raw/tech/database/Oracle To C#.md` ✓ → [[oracle]]
- `raw/tech/database/SQL 建立資料表.md`
- `raw/tech/database/SQL Basic Functions.md`
- `raw/tech/database/SQL 指令語法速查.md`
- `raw/tech/database/Oracle Server操作.md`
- `raw/tech/database/PL SQL.md`
- `raw/tech/database/Procedure & Function.md`

### Tech / Git

- `raw/tech/git/Git 指令筆記.md` ✓ → [[git]]
- `raw/tech/git/Git 每日開發 SOP.md` ✓ → [[git]]
- `raw/tech/git/Github 心得.md` ✓ → [[git]]
- `raw/tech/git/Git 指令筆記 (舊版).md`
- `raw/tech/git/Github 心得 (舊版).md`
- `raw/tech/git/SourseTree(Local) 筆記.md`
- `raw/tech/git/SourseTree(Local) 筆記 (舊版).md`
- `raw/tech/git/git-tutorial.md`

### Tech / System

- `raw/tech/system/Linux 觀念.md` ✓ → [[linux]]
- `raw/tech/system/Ubuntu 筆記.md` ✓ → [[linux]]
- `raw/tech/system/xrdp 設定.md`
- `raw/tech/system/網路設定.md`

### Tech / Networking

- `raw/tech/networking/網域小知識.md` ✓ → [[domain-networking]]
- `raw/tech/networking/google-oauth-tutorial.md`

### Tech / CS Basics

- `raw/tech/cs-basics/演算法筆記.md`
- `raw/tech/cs-basics/資料結構.md`
- `raw/tech/cs-basics/LeetCode.md`

### Tech / Tools

- `raw/tech/tools/Visual Studio Code.md`
- `raw/tech/tools/LaTex.md`
- `raw/tech/tools/VBA.md`
- `raw/tech/tools/markdown哲學.md`

### Tech / Simulation

- `raw/tech/simulation/NetLogo.md`
- `raw/tech/simulation/Flexsim.md`
- `raw/tech/simulation/Game Notes (Godot).md`

### Tech / Optimization

- `raw/tech/optimization/GLPK.md`
- `raw/tech/optimization/AMPL.md`
