# Vault

```bash
kubectl exec -n infra vault-0 -- vault operator init -key-shares=3 -key-threshold=2
```

整句意思：**在 vault-0 pod 裡初始化 Vault，產生 3 把 key，解封只需 2 把**。

| 部分 | 說明 |
| --- | --- |
| `kubectl exec` | 在 pod 裡執行指令 |
| `-n infra` | 指定 namespace 為 `infra` |
| `vault-0` | 目標 pod 名稱 |
| `--` | 分隔 kubectl 參數和要執行的指令 |
| `vault operator init` | Vault 初始化指令 |
| `-key-shares=3` | 產生 3 把 unseal key |
| `-key-threshold=2` | 需要其中 2 把才能 unseal |
|  |  |

**初始化**

`kubectl exec -n infra vault-0 -- vault operator init -key-shares=3 -key-threshold=2`

**Unseal（需跑 2 次，各用不同 key）**

`kubectl exec -n infra vault-0 -- vault operator unseal <key-1>`

`kubectl exec -n infra vault-0 -- vault operator unseal <key-2>`

**查看狀態**

`kubectl exec -n infra vault-0 -- vault status`

**登入（Root Token）**

`kubectl exec -n infra vault-0 -- vault login <root-token>`

**開 KV secret engine**

`kubectl exec -n infra vault-0 -- vault secrets enable -path=infra kv-v2`

**存 secret**

`kubectl exec -n infra vault-0 -- vault kv put infra/harbor adminPassword="密碼"`

**Port-forward（UI 用）**

`kubectl port-forward svc/vault -n infra 8200:8200`