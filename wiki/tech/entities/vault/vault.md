---
type: entity
domain: tech
tags: [vault, secret, kubernetes, security, devops]
sources:
  - raw/tech/devops/Vault.md
created: 2026-05-03
updated: 2026-05-03
---

# Vault

HashiCorp Vault 是一個 Secret 管理工具，用於安全儲存、存取和輪換敏感資料（密碼、API Key、憑證）。在 K8s 環境中，Vault 提供比 K8s Secret（base64 非加密）更強的安全保障。

## 核心概念

- **Secret Engine**：儲存不同類型 secret 的後端（KV、Database、PKI 等）
- **Auth Method**：驗證存取者身份（K8s SA、GitHub、LDAP 等）
- **Policy**：控制哪些 path 可以讀寫
- **Seal / Unseal**：Vault 啟動後處於狀態，需用 Unseal Key 解封才能存取資料

## Vault 啟動流程（K8s 環境）

```bash
# 1. 初始化（產生 key shares 和 root token）
kubectl exec -n infra vault-0 -- \
  vault operator init -key-shares=3 -key-threshold=2

# 2. Unseal（需跑 2 次，各用不同 key）
kubectl exec -n infra vault-0 -- vault operator unseal <key-1>
kubectl exec -n infra vault-0 -- vault operator unseal <key-2>

# 3. 查看狀態
kubectl exec -n infra vault-0 -- vault status

# 4. 登入（Root Token）
kubectl exec -n infra vault-0 -- vault login <root-token>
```

## 常用操作

```bash
# 開 KV v2 secret engine
kubectl exec -n infra vault-0 -- \
  vault secrets enable -path=infra kv-v2

# 存 secret
kubectl exec -n infra vault-0 -- \
  vault kv put infra/harbor adminPassword="my-password"

# 讀 secret
kubectl exec -n infra vault-0 -- \
  vault kv get infra/harbor

# Port-forward（UI 用）
kubectl port-forward svc/vault -n infra 8200:8200
```

## K8s 整合：External Secrets / VSO

在 MyDevWeb 架構中使用 **External Secrets Operator** 或 **Vault Secrets Operator (VSO)**，將 Vault 的 secret 同步到 K8s Secret 資源：

```yaml
# ClusterSecretStore（連接 Vault）
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "http://vault.infra.svc:8200"
      path: "infra"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
```

## Seal / Unseal 說明

| 狀態         | 說明                                       |
| ------------ | ------------------------------------------ |
| **Sealed**   | 啟動初始狀態，無法存取任何 secret          |
| **Unsealed** | 輸入足夠數量的 unseal key 後解封，正常運作 |

- `-key-shares=3`：產生 3 把 unseal key
- `-key-threshold=2`：只需 2 把即可解封（防止單點持有）
- Pod 重啟後需重新 unseal

## 連結

- [[kubernetes]] — Vault 部署的平台
- [[argocd]] — GitOps 工具，可配合 Vault 管理 secret
