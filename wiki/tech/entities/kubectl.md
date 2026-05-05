---
type: entity
domain: tech
tags: [kubectl, kubernetes, cli, devops]
sources:
  - raw/tech/devops/kubectl 指令.md
  - raw/tech/devops/Kubernetes (K8s).md
created: 2026-05-03
updated: 2026-05-03
---

# kubectl

kubectl 是 Kubernetes 的 CLI 工具，操作 Cluster 的唯一入口。指令透過 kube-apiserver 與 Cluster 溝通。

## 查看資源

| 指令 | 說明 |
| --- | --- |
| `kubectl get pods` | 列出 Pod（`-A` 全 namespace，`-n <ns>` 指定 namespace） |
| `kubectl get pods -o wide` | 顯示更多資訊（Node、IP） |
| `kubectl get all -n <ns>` | 列出 namespace 下所有資源 |
| `kubectl describe pod <name>` | 顯示詳細資訊與 Events（除錯起點） |
| `kubectl explain deployment.spec` | 查看資源欄位說明文件 |
| `kubectl api-resources` | 列出所有資源類型與縮寫 |
| `kubectl api-versions` | 列出支援的 API 版本 |
| `kubectl version` | 顯示 client 與 server 版本 |

## 建立 / 管理

| 指令 | 說明 |
| --- | --- |
| `kubectl apply -f <file>` | 宣告式建立或更新（idempotent，CI/CD 常用） |
| `kubectl create -f <file>` | 一次性建立，資源已存在會報錯 |
| `kubectl delete -f <file>` | 刪除資源 |
| `kubectl delete pod <name>` | 直接指定名稱刪除 |
| `kubectl edit deploy <name>` | 在編輯器直接修改 YAML，存檔即套用 |
| `kubectl patch <kind> <name> --type merge -p '<json>'` | 用 JSON 片段更新特定欄位 |
| `kubectl scale deploy <name> --replicas=3` | 手動調整 replica 數量 |
| `kubectl set image deploy/<name> <container>=<image>` | 更新容器映像 |
| `kubectl rollout history deploy <name>` | 查看部署版本歷史 |
| `kubectl rollout undo deploy <name>` | 回滾到上一版 |
| `kubectl rollout undo deploy <name> --to-revision=2` | 回滾到指定版本 |

## 除錯

| 指令 | 說明 |
| --- | --- |
| `kubectl logs <pod>` | 取得 Pod log |
| `kubectl logs <pod> -f` | 追蹤即時 log |
| `kubectl logs <pod> --previous` | 查看崩潰前的 log |
| `kubectl exec -it <pod> -- /bin/bash` | 進入 Container 互動 shell |
| `kubectl port-forward <pod> 8080:8080` | 本機 port 轉發到 Pod（本地測試） |
| `kubectl port-forward svc/<name> 8080:80` | 本機 port 轉發到 Service |
| `kubectl top pod` | 查看 Pod CPU/Memory 用量（需 metrics-server） |
| `kubectl events` | 列出叢集事件 |
| `kubectl cp <pod>:/path /local` | 複製 Container 內檔案到本機 |

## Cluster 設定

| 指令 | 說明 |
| --- | --- |
| `kubectl config get-contexts` | 列出所有 context |
| `kubectl config use-context <name>` | 切換 context |
| `kubectl cluster-info` | 顯示 API Server 和 CoreDNS 位址 |
| `kubectl auth can-i <verb> <resource>` | 確認 RBAC 權限 |

## 進階

```bash
# 預覽 apply 的變更（不實際執行）
kubectl diff -f <file>

# server-side apply（大型資源、避免 annotation 大小限制）
kubectl apply --server-side -f <file>

# 等待資源到達指定狀態
kubectl wait --for=condition=ready pod -l app=my-app

# 取得 ArgoCD 初始密碼
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

## apply vs create

| | `kubectl create` | `kubectl apply` |
| --- | --- | --- |
| 資源已存在 | 報錯 | 更新（idempotent） |
| 適合情境 | 一次性新建 | CI/CD、GitOps |
| server-side | 無此選項 | `--server-side` |

## 常用縮寫

| 全名 | 縮寫 |
| --- | --- |
| `deployments` | `deploy` |
| `services` | `svc` |
| `pods` | `po` |
| `namespaces` | `ns` |
| `configmaps` | `cm` |
| `persistentvolumeclaims` | `pvc` |

## 連結

- [[kubernetes]] — kubectl 操作的 K8s 概念
- [[minikube]] — 本機 K8s 環境
- [[argocd]] — GitOps 工具（kubectl 配合使用）
