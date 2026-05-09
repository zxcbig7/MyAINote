---
tags: [devops, kubernetes, k8s]
---

> 關聯：[[kubernetes]]

# PostgreSQL on Kubernetes

## 部署方式

使用 Bitnami Helm Chart 部署，資料持久化透過 PVC。

### 加入 Repo

```bash
helm repo add bitnami https://raw.githubusercontent.com/bitnami/charts/archive-full-index/bitnami
helm repo update
```

> 注意：`https://charts.bitnami.com/bitnami` 舊 URL 已失效，需使用上方的 archive URL。

### 安裝

```bash
# CMD
helm install postgresql bitnami/postgresql -n <namespace> --set auth.postgresPassword="<password>" --set primary.persistence.size=2Gi

# PowerShell（用反引號換行）
helm install postgresql bitnami/postgresql -n <namespace> `
  --set auth.postgresPassword="<password>" `
  --set primary.persistence.size=2Gi
```

### 確認狀態

```bash
kubectl get pods -n <namespace> | grep postgresql
# postgresql-0   1/1   Running
```

---

## 連線資訊

| 項目 | 值 |
|------|----|
| Cluster 內部 DNS | `postgresql.<namespace>.svc.cluster.local` |
| Port | `5432` |
| 預設 user | `postgres` |

### 取得密碼

```bash
# Linux/macOS
kubectl get secret --namespace <namespace> postgresql -o jsonpath="{.data.postgres-password}" | base64 -d

# PowerShell（需要 WSL 協助）
kubectl get secret --namespace <namespace> postgresql -o jsonpath="{.data.postgres-password}"
# 輸出是 base64，自行解碼
```

### 測試連線（在 cluster 內）

```bash
kubectl run postgresql-client --rm --tty -i --restart=Never --namespace <namespace> \
  --image bitnami/postgresql:latest \
  --env="PGPASSWORD=<password>" \
  --command -- psql --host postgresql -U postgres -d postgres -p 5432
```

### Port-forward（從本機連）

```bash
kubectl port-forward --namespace <namespace> svc/postgresql 5432:5432
```

---

## 整合 Vault

把連線資訊存進 Vault：

```bash
vault kv put kv-infra/database \
  host="postgresql.<namespace>.svc.cluster.local" \
  port="5432" \
  user="postgres" \
  password="<password>"
```

再用 ExternalSecret 同步成 K8s Secret，後端從 Secret 讀取連線字串。

---

## 注意事項

- PVC 存在時重新安裝，`--set auth.postgresPassword` 不會更新密碼（舊密碼仍在 PVC 裡），需先刪除 PVC
- 不建議使用 `latest` tag，production 環境請固定版本號
- Bitnami 自 2025 年 8 月起部分 image 需付費訂閱，免費版仍可使用但更新受限
