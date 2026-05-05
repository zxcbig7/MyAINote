# Vault 教學

## 一、什麼是 Vault

HashiCorp Vault 是密碼管理工具，專門安全存放敏感資訊（密碼、API key、憑證）。

**解決的問題：** 不用把密碼明文寫在 `values.yaml` 或 Git 裡，改由應用程式啟動時從 Vault 拉取。

---

## 二、目前架構

- Namespace：`infra`（與 Harbor 同一個）
- 部署方式：ArgoCD 管理，Helm chart `hashicorp/vault 0.29.1`
- 對外：`https://vault.viclai.idv.tw`（Cloudflare Tunnel）
- 儲存：file storage，PVC `data-vault-0`（1Gi）

---

## 三、Vault 生命週期

### 啟動流程
```
Pod 啟動 → Sealed 狀態 → 執行 unseal（2 次）→ Unsealed → 可使用
```

Vault 每次重啟後都是 **Sealed**，需要重新 unseal，已寫進 `start.bat` 自動處理。

### 狀態說明
| 狀態 | 說明 |
|------|------|
| `Initialized: false` | 全新安裝，需要 init |
| `Sealed: true` | 已初始化但鎖定，需要 unseal |
| `Sealed: false` | 正常可使用 |

---

## 四、初始化（全新安裝才需要）

```bash
kubectl exec -n infra vault-0 -- vault operator init -key-shares=3 -key-threshold=2
```

會產生：
- **3 把 Unseal Key** — 解封用，需要任意 2 把
- **1 個 Root Token** — 管理員登入用

> **重要：** 這些 key 只會顯示一次，務必存在安全的地方，且不能放進 Git！

---

## 五、解封（Unseal）

每次重啟後執行（需要 2 把不同的 key）：

```bash
kubectl exec -n infra vault-0 -- vault operator unseal <key-1>
kubectl exec -n infra vault-0 -- vault operator unseal <key-2>
```

確認狀態：
```bash
kubectl exec -n infra vault-0 -- vault status
# Sealed: false 代表解封成功
```

---

## 六、登入

```bash
kubectl exec -n infra vault-0 -- vault login <root-token>
```

或直接開 `https://vault.viclai.idv.tw`，用 Root Token 登入 UI。

---

## 七、KV Secret Engine

### 啟用（只需做一次）
```bash
kubectl exec -n infra vault-0 -- vault login <root-token>
kubectl exec -n infra vault-0 -- vault secrets enable -path=kv-infra kv-v2
```

### v2 與 v1 差異
| | KV v1 | KV v2 |
|--|-------|-------|
| 歷史版本 | ❌ | ✅ 保留多個版本 |
| 刪除後還原 | ❌ | ✅ soft delete |
| 元數據 | ❌ | ✅ 建立時間、版本號 |

### 存入 Secret
```bash
kubectl exec -n infra vault-0 -- vault kv put kv-infra/harbor adminPassword="密碼"
kubectl exec -n infra vault-0 -- vault kv put kv-infra/database host="localhost" user="admin" password="密碼"
kubectl exec -n infra vault-0 -- vault kv put kv-infra/jwt secret="jwt-secret-key"
kubectl exec -n infra vault-0 -- vault kv put kv-infra/google clientId="xxx" clientSecret="yyy"
```

### 讀取 Secret
```bash
kubectl exec -n infra vault-0 -- vault kv get kv-infra/harbor
kubectl exec -n infra vault-0 -- vault kv get -field=adminPassword kv-infra/harbor
```

### 建議結構
```
kv-infra/
├── harbor          ← Harbor 帳密
├── database        ← DB 連線資訊
├── jwt             ← JWT secret
└── google-oauth    ← Google OAuth credentials
```

---

## 八、整合 K8s（External Secrets Operator）

讓 K8s 自動從 Vault 同步 secret，應用程式不需要直接呼叫 Vault API。

```
Vault → ESO → K8s Secret → Pod 讀取
```

### 概念說明

**ESO（External Secrets Operator）**
跑在 K8s 裡的 controller，持續監聽 `ExternalSecret` 資源，定期去外部系統（Vault、AWS Secrets Manager 等）拉取 secret，寫進 K8s Secret。

**CRD（Custom Resource Definition）**
K8s 的擴充機制，讓第三方工具可以定義自己的資源類型。ESO 安裝時會在 cluster 新增 `SecretStore`、`ExternalSecret` 等資源類型，之後就可以像操作原生 K8s 資源一樣操作它們。

**整體關係：**
```
Vault          ← 存放真正的密碼
ExternalSecret ← 描述「從哪裡拿、放哪裡」的規則
ESO            ← 執行這個規則的 controller
K8s Secret     ← 最終產出，Pod 直接讀這個
```

### 元件說明

| 元件 | 用途 |
|------|------|
| `SecretStore` | 設定 ESO 如何連到 Vault（位置、認證方式） |
| `ExternalSecret` | 設定要同步哪個 Vault secret 到哪個 K8s Secret |

### SecretStore 範例

```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: infra
spec:
  provider:
    vault:
      server: "http://vault.infra.svc.cluster.local:8200"
      path: "kv-infra"
      version: "v2"
      auth:
        tokenSecretRef:
          name: vault-token
          key: token
```

`vault-token` 是一個 K8s Secret，需要預先建立：
```bash
kubectl create secret generic vault-token --from-literal=token=<root-token> -n infra
```

### ExternalSecret 範例

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: harbor-admin-secret
  namespace: infra
spec:
  refreshInterval: "1h"
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: harbor-admin-secret
    creationPolicy: Owner
  data:
    - secretKey: adminPassword       # K8s Secret 裡的 key 名
      remoteRef:
        key: harbor                  # Vault secret 名稱（kv-infra/harbor）
        property: adminPassword      # 該 secret 的欄位
```

### 確認同步狀態

```bash
kubectl get externalsecret <name> -n <namespace>
```

`STATUS` 為 `SecretSynced`、`READY` 為 `True` 代表同步成功。

### 強制立即同步

`ExternalSecret` 預設依 `refreshInterval` 定期同步（預設 1 小時）。以下情況需要強制立即觸發：

- 剛修改 Vault secret，不想等下次定期同步
- 排查問題時想確認最新狀態
- 修改了 SecretStore 或 policy 後驗證是否生效

```bash
kubectl annotate externalsecret <name> -n <namespace> force-sync=1 --overwrite
```

每次要重新觸發就把值改成不同的數字即可。

---

## 九、注意事項

- Vault 資料存在 PVC，`minikube delete` 後**全部消失**，需要重新 init
- Root Token 和 Unseal Keys **不能放進 Git**
- start.bat 已設定自動 unseal，但 key 改為啟動時手動輸入
