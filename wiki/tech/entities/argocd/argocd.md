---
type: entity
domain: tech
tags: [argocd, gitops, kubernetes, deployment, cd]
sources: [raw/tech/devops/argocd-tutorial.md]
created: 2026-05-03
updated: 2026-05-03
---

# ArgoCD

> GitOps 部署控制器：把 K8s 期望狀態存在 Git，由 ArgoCD 持續 reconcile 到叢集。

## 一句話定義
ArgoCD 是 K8s 上的 GitOps controller，**Git 是唯一真相來源**，叢集狀態自動 sync 自 git repo（預設每 3 分鐘 poll）。

## 核心元件
| 元件 | 用途 |
|---|---|
| `argocd-application-controller` | 比對 git 與叢集狀態，執行 sync |
| `argocd-applicationset-controller` | 從模板批次產生 Application（多環境） |
| `argocd-repo-server` | 從 git 拉 yaml / Helm chart |
| `argocd-server` | Web UI + API |
| `argocd-redis` | 快取 |
| `argocd-dex-server` | SSO 登入驗證 |
| `argocd-notifications-controller` | 通知 |

## CRD
- **Application** — 一個被管理的 app（一個 git source → 一個 cluster destination）
- **ApplicationSet** — 用 generator + template 批次生成多個 Application（典型用途：dev / stg / prod 三環境）

## syncPolicy 重點
```yaml
syncPolicy:
  automated:
    prune: true       # git 刪 → 叢集刪
    selfHeal: true    # 手動改叢集 → 自動還原成 git
```

## 跨 namespace 管理 Application
預設 Application 只能放在 `argocd` namespace。要放在別的 ns（例如 `infra`）需：
1. `argocd-cmd-params-cm` 設 `application.namespaces: infra`
2. `appproject default` 加 `spec.sourceNamespaces: [infra]`
3. 重啟 `application-controller` 與 `applicationset-controller`

## 私有 Repo 認證
建立 type=git 的 Secret 並打 label `argocd.argoproj.io/secret-type=repository`。注意 `kubectl create secret` **不支援 `-l`**，label 要分步加。

## 常見坑
| 症狀 | 原因 |
|---|---|
| `SSH_AUTH_SOCK not specified` | 用了 SSH URL；改 HTTPS |
| Sync status 一直 `Unknown` | repo 認證或網路問題；`kubectl describe application` 看 conditions |
| ApplicationSet 不產生 Application | repo 認證未設 / namespace 權限缺 / controller log 有錯 |

## 連結
- Source：[[argocd-tutorial-summary]]
- 待建立 entity：[[kubernetes]]、[[helm]]
- 待建立 concept：[[gitops]]
