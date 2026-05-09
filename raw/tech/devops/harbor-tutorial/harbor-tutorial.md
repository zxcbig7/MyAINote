# Harbor 教學

## 一、什麼是 Harbor

Harbor 是 CNCF 的開源私有 container registry，提供：
- Docker image 的存放與版本管理
- 存取控制（帳號、project 權限）
- Image 漏洞掃描（Trivy）
- 支援 Helm chart 存放

**用途：** 取代 Docker Hub，自建私有 registry，CI/CD 推 image 到自己的 Harbor，不需要對外。

---

## 二、部署架構

```
ArgoCD → Helm chart (harbor/harbor) → infra namespace
         ↓
         Harbor 由多個 Deployment 組成：
         core / portal / jobservice / registry / database / redis
```

- 部署方式：ArgoCD 管理，Helm chart `harbor/harbor 1.15.1`
- Namespace：`infra`
- 對外：`http://harbor.viclai.idv.tw`（Cloudflare Tunnel → ingress-nginx）

---

## 三、Helm values 重要設定

### expose 設定
```yaml
expose:
  type: ingress
  ingress:
    hosts:
      core: harbor.viclai.idv.tw
  tls:
    enabled: false
externalURL: http://harbor.viclai.idv.tw
```
- `type: ingress`：透過 ingress-nginx 對外
- `externalURL` 必須與 ingress host 一致，Harbor 內部用這個 URL 產生 image pull 路徑

### Admin 密碼（透過 ExternalSecret）
```yaml
existingSecretAdminPassword: harbor-admin-secret
existingSecretAdminPasswordKey: adminPassword
```
不在 values.yaml 直接寫密碼，改由 K8s Secret `harbor-admin-secret` 提供，由 ESO 從 Vault 同步建立。

### 停用非必要元件（省資源）
```yaml
trivy:
  enabled: false
notary:
  enabled: false
```

### Resource limits（minikube 環境調低）
| 元件 | CPU request | Memory request |
|------|-------------|----------------|
| core | 50m | 128Mi |
| portal | 10m | 32Mi |
| jobservice | 50m | 64Mi |
| registry | 50m | 64Mi |
| database | 50m | 128Mi |
| redis | 10m | 32Mi |

---

## 四、Admin 密碼管理（Vault + ESO）

### 架構
```
Vault (kv-infra/harbor) → ESO → K8s Secret (harbor-admin-secret) → Harbor
```

### 1. 在 Vault 存入密碼
```bash
kubectl exec -n infra vault-0 -- vault kv put kv-infra/harbor adminPassword="your-password"
```

### 2. SecretStore（設定 ESO 如何連 Vault）
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

`vault-token` 是一個 K8s Secret，存放 Vault 的 Root Token（或 policy token），ESO 用它認證 Vault。

建立方式：
```bash
kubectl create secret generic vault-token --from-literal=token=<root-token> -n infra
```

### 3. ExternalSecret（描述同步規則）
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
    - secretKey: adminPassword
      remoteRef:
        key: harbor
        property: adminPassword
```

- `key: harbor` → Vault 裡的 secret 名稱（`kv-infra/harbor`）
- `property: adminPassword` → 該 secret 的欄位
- `secretKey: adminPassword` → 寫進 K8s Secret 的 key 名稱

### 4. 確認同步狀態
```bash
kubectl get externalsecret harbor-admin-secret -n infra
```
`STATUS: SecretSynced`、`READY: True` 代表成功。

---

## 五、ArgoCD Application 設定重點

Harbor 的 ArgoCD Application 放在 `infra` namespace，需要先設定 ArgoCD 允許管理此 namespace：

```bash
# patch argocd-cmd-params-cm
kubectl patch configmap argocd-cmd-params-cm -n argocd \
  --type merge --patch '{"data":{"application.namespaces":"infra"}}'

# patch default project
kubectl patch appproject default -n argocd \
  --type merge -p '{"spec":{"sourceNamespaces":["infra"]}}'
```

---

## 六、常用操作

### 登入 Harbor UI
```
http://harbor.viclai.idv.tw
帳號：admin
密碼：Vault 裡 kv-infra/harbor 的 adminPassword
```

### 登入 Docker
```bash
docker login harbor.viclai.idv.tw -u admin
```

### Push image
```bash
docker tag myimage:latest harbor.viclai.idv.tw/<project>/myimage:latest
docker push harbor.viclai.idv.tw/<project>/myimage:latest
```

### 查看 Harbor 所有 pod 狀態
```bash
kubectl get pods -n infra -l app=harbor
```

---

## 七、CI/CD 整合

### Project 與 Repository 結構

```
Harbor
└── Project（需手動建立）
    └── Repository（push image 時自動建立）
```

例如 push `harbor.example.com/myapp/frontend:v1`，Harbor 會自動在 `myapp` project 下建立 `frontend` repository。

### Robot Account（推薦用於 CI/CD）

Admin 帳密不適合用在 CI/CD，應改用 Robot Account：

1. Harbor UI → Project → **機器人帳號** → 新增
2. 設定名稱與權限（Push、Pull）
3. 複製產生的 token（只顯示一次）

Robot Account 使用者名稱格式：
```
robot$<project-name>+<robot-name>
```

### GitHub Actions 設定

在 repo Settings → Secrets 加入：
```
HARBOR_URL      = harbor.example.com
HARBOR_USERNAME = robot$myproject+ci-bot
HARBOR_PASSWORD = <robot-account-token>
```

workflow 登入範例：
```yaml
- name: Login to Harbor
  uses: docker/login-action@v3
  with:
    registry: ${{ secrets.HARBOR_URL }}
    username: ${{ secrets.HARBOR_USERNAME }}
    password: ${{ secrets.HARBOR_PASSWORD }}
```

### externalURL 必須用 HTTPS

若 Harbor 經由 Cloudflare 等反向代理對外提供 HTTPS，`externalURL` 必須設為 `https://`，否則 push token 驗證會失敗：

```yaml
externalURL: https://harbor.example.com
```

---

## 八、TLS 憑證設定（cert-manager + Let's Encrypt）

### 適用時機

- Docker push/pull 需要 HTTPS（Docker 預設拒絕非 localhost 的 HTTP registry）
- 流量不走 Cloudflare Proxy（DNS-only），Cloudflare 不幫補 TLS
- Cloudflare Proxy 有 100MB 請求大小限制，不適合作為 Docker registry 的代理層

### 架構

```
GitHub Actions → harbor.viclai.idv.tw (Cloudflare DNS-only)
    → 本機 port 443 → ingress-nginx → Harbor
       ↑
       TLS cert 由 cert-manager 從 Let's Encrypt 取得
```

### 前置條件

- 路由器將外部 port 443 forward 到本機 IP:443
- Cloudflare API Token（Zone:DNS:Edit 權限），用於 DNS-01 challenge

### 1. 安裝 cert-manager（ArgoCD Application）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cert-manager
  namespace: infra
spec:
  project: default
  source:
    repoURL: https://charts.jetstack.io
    chart: cert-manager
    targetRevision: v1.16.2
    helm:
      releaseName: cert-manager
      values: |
        crds:
          enabled: true
  destination:
    server: https://kubernetes.default.svc
    namespace: cert-manager
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### 2. 建立 Cloudflare API Token Secret

```powershell
kubectl create secret generic cloudflare-api-token-secret `
  --from-literal=api-token=<token> `
  -n cert-manager
```

### 3. ClusterIssuer（Cloudflare DNS-01）

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: <your-email>
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - dns01:
        cloudflare:
          apiTokenSecretRef:
            name: cloudflare-api-token-secret
            key: api-token
```

```bash
kubectl apply -f cluster-issuer.yaml
kubectl get clusterissuer letsencrypt-prod   # READY 要是 True
```

### 4. Harbor Helm values 啟用 TLS

```yaml
expose:
  type: ingress
  tls:
    enabled: true
    certSource: secret
    secret:
      secretName: "harbor-tls"
  ingress:
    hosts:
      core: harbor.example.com
    annotations:
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
      nginx.ingress.kubernetes.io/proxy-body-size: "0"
externalURL: https://harbor.example.com
```

- `certSource: secret` + `secretName: harbor-tls`：Harbor ingress 使用這個 TLS secret
- cert-manager 看到 ingress 的 annotation 後自動 issue 憑證並寫入 `harbor-tls` secret
- `proxy-body-size: "0"` 移除 nginx 對 request body 的大小限制，避免大 image layer 被擋

### 5. 確認憑證狀態

```bash
kubectl get certificate -n infra
```

`READY=True` 後再將 Cloudflare DNS 改成灰色（DNS only）。

---

## 九、注意事項

- Harbor 依賴 database（PostgreSQL）和 redis，啟動時間較長，需等所有元件 Ready
- `externalURL` 設錯會導致 image push/pull URL 異常
- Admin 密碼若修改必須同時更新 Vault 和重啟 Harbor core pod
- ESO 的 `vault-token` Secret 需要在 ExternalSecret apply 之前存在，否則 ESO 無法認證
