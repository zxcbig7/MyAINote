# Wiki Log

> Append-only。每筆格式：`## [YYYY-MM-DD] <action> | <subject>`
> action 類型：`bootstrap`、`ingest`、`query`、`synthesis`、`lint`、`refactor`

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

## [2026-05-03] ingest | Notion notes 批次整合

- 來源：`Notion notes/Dev/` 下 27 個主題檔（4 批次）
- 產出：15 個 wiki 頁面
  - entities（14）：docker、kubernetes、minikube、helm、kubectl、vault、typescript、react、dotnet-web-api、csharp、git、oracle、linux
  - concepts（2）：cicd-pipeline、domain-networking
- 涵蓋：Docker、K8s、Minikube、Helm、kubectl、Vault、TypeScript、React、.NET Web API、C#、Git、Oracle、Linux、CI/CD Pipeline、Domain/Networking
- 同步建立 `wiki/tech/concepts/` 目錄
