# Kubernetes 完整教學
## 從本機部署到公開服務

---

# 目錄

1. [基礎概念](#基礎概念)
2. [環境準備](#環境準備)
3. [Minikube 部署](#minikube-部署)
4. [ArgoCD GitOps](#argocd-gitops)
5. [Cloudflare Tunnel 對外服務](#cloudflare-tunnel-對外服務)

---

# 基礎概念

## 什麼是 Kubernetes？

Kubernetes（K8s）是一個自動化部署、擴展和管理容器化應用的平台。

核心概念：

| 概念           | 說明                                             |
| -------------- | ------------------------------------------------ |
| **Pod**        | 最小部署單位，包含一個或多個容器                 |
| **Deployment** | 管理 Pod 的生命週期，確保指定數量的 Pod 持續運行 |
| **Service**    | 提供穩定的網路入口，將流量分配給後端 Pod         |
| **ConfigMap**  | 存放設定檔（非機密資料）                         |
| **Secret**     | 存放機密資料（憑證、密碼等）                     |
| **Namespace**  | 將叢集資源分組隔離                               |
| **ReplicaSet** | 確保指定數量的 Pod 副本運行，Deployment 自動管理 |

## 什麼是 GitOps？

GitOps 是一種運維方式：

> 「Git 是唯一的真相來源」

```
開發者 git push → GitHub → ArgoCD 偵測變更 → 自動部署到 K8s
```

不需要手動 `kubectl apply`，所有變更都透過 Git 管理，可追蹤、可回滾。

## 兩個 Tunnel 的分工

這個架構需要同時跑兩個 tunnel，缺一個就斷線：

### minikube tunnel

把 K8s 叢集內部的 ingress 暴露到 Windows 本機（`127.0.0.1:80`）。

```
127.0.0.1:80 → ingress-nginx → K8s 裡的 Pod
```

沒有它，Windows 本機看不到 K8s 裡的任何服務。

### cloudflared tunnel（k8s-tunnel）

把 Windows 本機的 port 暴露到外部網路（Cloudflare）。

```
網際網路 → Cloudflare → cloudflared → 127.0.0.1:80
```

沒有它，外面（手機、其他裝置）連不到你的電腦。

### 完整流向

```
手機
 ↓
Cloudflare（viclai.idv.tw）
 ↓  cloudflared tunnel（k8s-tunnel）
127.0.0.1:80（Windows 本機）
 ↓  minikube tunnel
ingress-nginx（K8s）
 ↓
frontend Pod（prod namespace）
```

> 兩個 tunnel 都需要透過 `start.bat` 啟動，重開電腦後都要重新執行。

---

# 環境準備

## 安裝工具

- **minikube**：本機 K8s 叢集 → https://minikube.sigs.k8s.io/docs/start/
- **kubectl**：K8s 指令工具（minikube 內建）
- **cloudflared**：Cloudflare Tunnel 客戶端

```bash
winget install Cloudflare.cloudflared
```

---

# Minikube 部署

## 啟動叢集

```bash
minikube start    # 啟動
minikube status   # 確認狀態
minikube stop     # 停止（保留狀態）
minikube delete   # 完全清除
```

## 撰寫 deployment.yaml

一個 yaml 檔可以包含多個資源，用 `---` 分隔。

```yaml
# ============================================================
# Deployment：管理 Pod 生命週期
# ============================================================
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-web-deployment
spec:
  replicas: 2                   # 同時跑幾個 Pod
  revisionHistoryLimit: 5       # 保留 5 個舊版本供回滾
  selector:
    matchLabels:
      app: nginx-web            # 管理帶這個 label 的 Pod
  template:
    metadata:
      labels:
        app: nginx-web          # Pod 的 label
    spec:
      containers:
        - name: nginx-web-container
          image: nginx:latest
          resources:
            requests:
              cpu: "100m"       # 保證 0.1 顆 CPU
              memory: "64Mi"    # 保證 64MB 記憶體
            limits:
              cpu: "200m"       # 最多 0.2 顆 CPU
              memory: "128Mi"   # 最多 128MB，超過 OOMKill
          ports:
            - containerPort: 80
            - containerPort: 443
          volumeMounts:
            - name: nginx-tls-volume
              mountPath: /etc/nginx/certs
              readOnly: true
            - name: nginx-config-volume
              mountPath: /etc/nginx/conf.d
              readOnly: true
      volumes:
        - name: nginx-tls-volume
          secret:
            secretName: nginx-web-tls      # 從 Secret 掛載憑證
        - name: nginx-config-volume
          configMap:
            name: nginx-web-config         # 從 ConfigMap 掛載設定
---
# ============================================================
# ConfigMap：nginx 設定檔
# ============================================================
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-web-config
data:
  default.conf: |
    server {
        listen 80;
        return 301 https://$host$request_uri;  # HTTP 跳轉 HTTPS
    }
    server {
        listen 443 ssl;
        ssl_certificate     /etc/nginx/certs/tls.crt;
        ssl_certificate_key /etc/nginx/certs/tls.key;
        location / {
            root   /usr/share/nginx/html;
            index  index.html;
        }
    }
---
# ============================================================
# Service：網路入口
# ============================================================
apiVersion: v1
kind: Service
metadata:
  name: nginx-web-service
spec:
  type: NodePort          # 允許外部存取
  selector:
    app: nginx-web        # 導流到帶這個 label 的 Pod
  ports:
    - name: http
      port: 80
      targetPort: 80
    - name: https
      port: 443
      targetPort: 443
```

## Label 機制

Label 是 K8s 資源互相識別的方式：

```
Deployment selector → 找帶指定 label 的 Pod 來管理
Service selector    → 找帶指定 label 的 Pod 來導流
```

## Resource Limits

```yaml
resources:
  requests:   # K8s 排程保證，Node 沒有這麼多資源就不放 Pod 上去
    cpu: "100m"
    memory: "64Mi"
  limits:     # 超過限制的處理方式
    cpu: "200m"      # 超過：限速（不會死）
    memory: "128Mi"  # 超過：OOMKill 重啟
```

不設 limits 會有 **noisy neighbor** 問題：單一 Pod 吃光 Node 資源影響其他 Pod。

## 建立 TLS 憑證 Secret

```bash
# Windows PowerShell 產生自簽憑證
$env:OPENSSL_CONF="NUL"; openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=nginx-web.local"; kubectl create secret tls nginx-web-tls --cert=tls.crt --key=tls.key
```

> K8s Secret 是 base64 編碼，不是加密，有 kubectl 權限的人都能看到原始內容。
> 正式環境需搭配 Sealed Secrets 或 Vault。

## 部署

```bash
kubectl apply -f deployment.yaml
kubectl get pods              # 確認 Pod 狀態
kubectl get svc               # 確認 Service
```

## 常用 kubectl 指令

```bash
# Pod
kubectl get pods                            # 列出所有 Pod
kubectl get pods -o wide                    # 含詳細資訊
kubectl get pods -w                         # 即時監控
kubectl describe pod <pod-name>             # 詳細資訊與 Events
kubectl logs <pod-name>                     # 查看 log
kubectl exec -it <pod-name> -- bash         # 進入 Pod
kubectl delete pod <pod-name>               # 刪除（Deployment 管理的會自動重建）

# Deployment
kubectl get deployments
kubectl scale deployment nginx-web-deployment --replicas=3   # 調整數量
kubectl rollout restart deployment nginx-web-deployment      # 重啟
kubectl rollout status deployment nginx-web-deployment       # 更新進度
kubectl rollout undo deployment nginx-web-deployment         # 回滾

# 更新映像版本（Rolling Update）
kubectl set image deployment/nginx-web-deployment nginx-web-container=nginx:1.25
```

## Rolling Update 機制

更新時 K8s 逐步替換 Pod，確保服務不中斷：

```
原本：Pod1(舊) Pod2(舊) Pod3(舊)
更新：Pod1(新) Pod2(舊) Pod3(舊)  ← 逐步替換
完成：Pod1(新) Pod2(新) Pod3(新)
```

## ReplicaSet 歷史版本

每次更新會產生新的 ReplicaSet，舊的保留供回滾：

```
rev1（舊）→ rev2（舊）→ rev3（目前）
```

`revisionHistoryLimit: 5` 最多保留 5 個，超過自動刪除。

## 資源監控

```bash
minikube addons enable metrics-server   # 啟用（等約 1 分鐘）
kubectl top nodes                       # Node 資源使用
kubectl top pods                        # Pod 資源使用
```

若出現 `Metrics API not available`，需修補 metrics-server：

```bash
kubectl patch deployment metrics-server -n kube-system \
  --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

原因：minikube 的 kubelet 使用自簽憑證，metrics-server 預設不信任。

---

# ArgoCD GitOps

## 什麼是 ArgoCD？

ArgoCD 監控 Git repo，自動將變更同步到 K8s，實現 GitOps 流程。

## 安裝

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

等待所有 Pod Running（約 2～3 分鐘）：

```bash
kubectl get pods -n argocd -w
```

| Pod                              | 用途                 |
| -------------------------------- | -------------------- |
| argocd-application-controller    | 監控叢集狀態         |
| argocd-applicationset-controller | 管理多個 Application |
| argocd-dex-server                | 登入驗證             |
| argocd-notifications-controller  | 通知功能             |
| argocd-redis                     | 快取                 |
| argocd-repo-server               | 從 Git 拉取 yaml     |
| argocd-server                    | Web UI 和 API        |

## 開啟 Web UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

瀏覽器開 `https://localhost:8080`（憑證警告點進階繼續）

## 取得登入密碼

帳號：`admin`

密碼（CMD 取得 base64，再解碼）：
```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}"
```

> CMD 沒有內建 base64 解碼，把輸出貼到 [base64decode.org](https://www.base64decode.org/) 解碼，或用 PowerShell（需要 PowerShell）：
> ```powershell
> kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
> ```

> 登入後至 User Info → Update Password 修改密碼

## 把 yaml 推到 GitHub

```bash
git init
git add deployment.yaml .gitignore
git commit -m "add nginx deployment"
git remote add origin https://github.com/<帳號>/<repo>.git
git push -u origin master
```

> 使用 HTTPS 而非 SSH，ArgoCD 連 SSH 需要額外設定 SSH Agent

## 建立 ArgoCD Application

`argocd-app.yaml`：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-web-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<帳號>/<repo>.git
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true       # Git 刪掉的資源，K8s 也自動刪
      selfHeal: true    # 有人手動改 K8s，自動還原回 Git 狀態
```

```bash
kubectl apply -f argocd-app.yaml
kubectl get application -n argocd   # 確認狀態
```

看到 `Synced` + `Healthy` 代表成功。

## Web UI 功能說明

| 按鈕                 | 功能                         |
| -------------------- | ---------------------------- |
| DETAILS              | 查看 Application 設定        |
| DIFF                 | 對比 Git 與 K8s 當前差異     |
| SYNC                 | 手動立即同步                 |
| HISTORY AND ROLLBACK | 查看部署歷史，回滾到任意版本 |
| REFRESH              | 重新從 Git 拉取狀態          |

## 日常 GitOps 流程

```
修改 yaml → git commit + git push
    → ArgoCD 自動偵測（每 3 分鐘 poll 一次）
    → 自動 kubectl apply
    → 完成
```

## 常見問題

### SSH_AUTH_SOCK not-specified
改用 HTTPS URL：
```
https://github.com/username/repo.git   ✓
git@github.com:username/repo.git       ✗
```

### SYNC STATUS 一直是 Unknown
```bash
kubectl describe application nginx-web-app -n argocd
```
看 Conditions 欄位的錯誤訊息。

---

# Cloudflare Tunnel 對外服務

## 架構說明

```
外部使用者
    ↓ HTTPS（Cloudflare 公開憑證）
Cloudflare
    ↓ 加密隧道（cloudflared 主動連出，不需開 port）
你的電腦（cloudflared）
    ↓
kubectl port-forward
    ↓
minikube nginx（Cloudflare Origin CA 憑證）
```

## 為何不用 Let's Encrypt？

Let's Encrypt 需要驗證你擁有 domain，驗證方式是從公網連到你的服務。本機 minikube 是內網，Let's Encrypt 連不到，所以無法使用。

Cloudflare Tunnel 是更好的替代方案。

## Step 1：把 Domain 加入 Cloudflare

1. 到 cloudflare.com 註冊並新增網域
2. Cloudflare 會給你兩個 Nameserver
3. 到 Domain 註冊商後台更換 Nameserver
4. 等待 DNS 生效（約 24 小時）

> 確認生效：Cloudflare 後台顯示「您的網域現在受到 Cloudflare 保護」

## Step 2：安裝 cloudflared

```bash
winget install Cloudflare.cloudflared
cloudflared --version   # 確認安裝成功
```

## Step 3：登入並建立 Tunnel

```bash
cloudflared tunnel login                  # 開瀏覽器授權
cloudflared tunnel create k8s-tunnel      # 建立 Tunnel，記下 Tunnel ID
cloudflared tunnel route dns k8s-tunnel <你的domain>   # 設定 DNS
```

## Step 4：申請 Cloudflare Origin CA 憑證

1. Cloudflare 後台 → SSL/TLS → **Origin Server**
2. Create Certificate
3. Hostnames：`yourdomain.com, *.yourdomain.com`
4. Validity：15 years
5. 下載 `certificate.pem` 和 `private-key.pem`

把憑證存入 K8s Secret：

```bash
kubectl create secret tls nginx-web-tls \
  --cert=certificate.pem \
  --key=private-key.pem \
  --dry-run=client -o yaml | kubectl apply -f -
```

> Origin CA 憑證只有 Cloudflare 信任，瀏覽器直連會顯示不安全，但透過 Cloudflare Tunnel 是完全信任的。

## Step 5：設定 Cloudflare SSL 模式

Cloudflare 後台 → SSL/TLS → Overview → 選 **Full (Strict)**

| 模式              | 說明                                  |
| ----------------- | ------------------------------------- |
| Off               | 不加密                                |
| Flexible          | Cloudflare 到你電腦不加密             |
| Full              | Cloudflare 到你電腦加密，但不驗證憑證 |
| **Full (Strict)** | 全程加密，驗證憑證（最安全）          |

## Step 6：設定 config.yml

`C:\Users\<你的帳號>\.cloudflared\config.yml`：

```yaml
tunnel: <你的Tunnel ID>
credentials-file: C:\Users\<帳號>\.cloudflared\<Tunnel ID>.json

ingress:
  - hostname: yourdomain.com
    service: https://127.0.0.1:8443
    originRequest:
      noTLSVerify: true        # 跳過本機憑證驗證（因為是 127.0.0.1）
  - service: http_status:404
```

## Step 7：固定 port-forward

Windows minikube 用 Docker driver，NodePort 只能透過 `127.0.0.1` 存取，且 port 每次重啟都會變。用 `kubectl port-forward` 固定 port：

```bash
kubectl port-forward svc/nginx-web-service 8443:443
```

## Step 8：啟動 Tunnel

```bash
cloudflared tunnel run k8s-tunnel
```

## 一鍵啟動腳本

`start.bat`：

```bat
@echo off
echo Starting K8s services...

start "port-forward" cmd /k "kubectl port-forward svc/nginx-web-service 8443:443"
timeout /t 3 /nobreak
start "cloudflared" cmd /k "cloudflared tunnel run k8s-tunnel"

echo All services started!
```

## 完整憑證流程說明

```
使用者瀏覽器
    ↓ 信任 Cloudflare 公開憑證（由知名 CA 簽發）
Cloudflare
    ↓ 信任 Origin CA 憑證（Cloudflare 自己簽發）
你的 nginx（掛載 Origin CA 憑證）
```

這樣全程加密，外部看到的是 Cloudflare 的公開憑證（綠色鎖頭），內部是 Origin CA 憑證保護傳輸安全。

## .gitignore 重要事項

以下檔案絕對不能推上 Git：

```
tls.key
tls.crt
certificate.pem
private-key.pem
```

私鑰一旦外洩，任何人都能偽裝成你的服務器。

---

## 整體架構總覽

```
GitHub (deployment.yaml)
    ↓ ArgoCD 自動同步
Kubernetes (minikube)
    ├── nginx-web-deployment (2 Pod)
    ├── nginx-web-service (NodePort)
    └── nginx-web-config (ConfigMap)
    ↑
kubectl port-forward (固定 8443)
    ↑
cloudflared Tunnel
    ↑
Cloudflare (viclai.idv.tw)
    ↑
外部使用者 (HTTPS)
```

---

## Pod 健康檢查：Liveness 與 Readiness Probe

K8s 透過 probe 機制確認 Pod 是否正常運作，有三種探測方式（最常用 `httpGet`）。

### 兩種 Probe 的差異

|                  | readinessProbe                | livenessProbe              |
| ---------------- | ----------------------------- | -------------------------- |
| **問的問題**     | 「Pod 準備好接流量了嗎？」    | 「Pod 還活著嗎？」         |
| **失敗時的動作** | 從 Service 移除，不再收到流量 | 重啟 container             |
| **適合偵測**     | 啟動中、暫時無法服務          | 無限迴圈、死鎖、記憶體洩漏 |
| **恢復後**       | 自動重新加回 Service          | 重啟後自動恢復             |

### 範例設定

```yaml
containers:
  - name: frontend
    image: zxcbig7/rule-viewer-frontend:1.0.0
    readinessProbe:
      httpGet:
        path: /        # 打這個路徑，回 200 表示 ready
        port: 80
      initialDelaySeconds: 5    # 容器啟動後等 5 秒再開始檢查
      periodSeconds: 10         # 每 10 秒檢查一次
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 10   # 給容器更多時間啟動再開始檢查
      periodSeconds: 30         # 每 30 秒檢查一次（不需要太頻繁）
```

### 為什麼 initialDelay 不同？

- **readiness** 等 5 秒：nginx 啟動很快，早點確認可以接流量
- **liveness** 等 10 秒：避免容器還在啟動中就被誤判為掛掉而重啟

### 只有 readiness 沒有 liveness 可以嗎？

可以。readiness 負責流量控制，liveness 負責自動重啟。
如果 Pod 壞掉時 container 不會 crash（例如 nginx 陷入死鎖但程序還在），
就需要 liveness 來強制重啟。靜態網站通常只設 readiness 也夠用。

---

# 各環境設定通則

## 環境定義

| 環境  | 目的                 | 對外 URL             |
| ----- | -------------------- | -------------------- |
| Local | 快速開發、hot reload | localhost            |
| Dev   | 驗證 K8s 設定        | localhost（ingress） |
| Stg   | 上 prod 前的整合測試 | stg.viclai.idv.tw    |
| Prod  | 對外正式服務         | viclai.idv.tw        |

---

## Local（本機開發）

**目的：** 快速開發、即時 hot reload，不需要 Docker 或 K8s。

```bash
# Frontend
cd RuleViewerFrontend
npm run dev        # → localhost:5173

# Backend
cd RuleViewerBackend
dotnet run         # → localhost:8082
```

| 項目          | 設定                                 |
| ------------- | ------------------------------------ |
| Frontend port | 5173                                 |
| Backend port  | 8082                                 |
| 設定檔        | `appsettings.Development.json`       |
| CORS          | 允許 `localhost:5173`                |
| 特色          | 改 code 立即生效，不需要 build image |

---

## Dev（K8s dev namespace）

**目的：** 驗證 Helm chart、ingress、probe 等 K8s 設定是否正常。
改了部署設定（不是 code）時在這裡先測。

| 項目      | 設定                               |
| --------- | ---------------------------------- |
| Image tag | 開發中版本（不需要最新）           |
| Replica   | 1                                  |
| Resource  | 最小（省資源）                     |
| URL       | `http://localhost`（本機 ingress） |
| 何時用    | 修改 Helm chart / K8s 設定時       |

---

## Stg（K8s stg namespace）

**目的：** 上 prod 前的最終驗證，環境盡量接近 prod。

| 項目      | 設定                         |
| --------- | ---------------------------- |
| Image tag | 準備發布的版本               |
| Replica   | 1                            |
| Resource  | 接近 prod                    |
| URL       | `https://stg.viclai.idv.tw`  |
| 何時用    | 功能完成、準備升版到 prod 前 |

---

## Prod（K8s prod namespace）

**目的：** 對外正式服務，只部署經過 stg 驗證的版本。

| 項目      | 設定                            |
| --------- | ------------------------------- |
| Image tag | 經過 stg 驗證的版本             |
| Replica   | 2（HA，一個掛掉另一個繼續服務） |
| Resource  | 最高上限                        |
| URL       | `https://viclai.idv.tw`         |
| 何時用    | stg 測試通過才升版              |

---

## 發版節奏

```
Local 開發（code 功能）
  ↓ 功能完成
Dev（驗證 K8s 設定沒問題）
  ↓ K8s 設定 OK
Stg（整合測試、QA）
  ↓ 測試通過
Prod（對外上線）
```

---

# 現行架構（多環境 GitOps）

## 架構總覽

```
GitHub
    ├── RuleViewerFrontend（.github/workflows/）
    │   ├── ci.yml        push to main → build + lint
    │   └── release.yml   push tag V.* → build image → push Docker Hub
    │                                  → 更新 Deployment repo values-prod.yaml
    │
    ├── RuleViewerBackend（.github/workflows/）
    │   ├── ci.yml        push to main → build + test
    │   └── release.yml   push tag V.* → build image → push Docker Hub
    │                                  → 更新 Deployment repo values-prod.yaml
    │
    └── Deployment-Apps（Deployment repo）
        ├── web-app/                    ← Helm Chart（前後端服務）
        │   ├── values.yaml             ← 共用預設值
        │   ├── values-dev.yaml         ← DEV 覆蓋
        │   ├── values-stg.yaml         ← STG 覆蓋
        │   └── values-prod.yaml        ← PROD 覆蓋（tag 由 CI 自動更新）
        │
        └── argocd/                     ← ArgoCD Application 定義
            ↓
        ArgoCD（自動 sync）
            ↓
        Kubernetes（minikube）
        ├── namespace: dev
        │   ├── web-app-dev-frontend (0 Pod，平常關閉)
        │   └── web-app-dev-backend  (0 Pod，平常關閉)
        ├── namespace: stg
        │   ├── web-app-stg-frontend (0 Pod，平常關閉)
        │   └── web-app-stg-backend  (0 Pod，平常關閉)
        └── namespace: prod
            ├── web-app-prod-frontend (1 Pod)
            └── web-app-prod-backend  (1 Pod)
            ↑
        minikube tunnel（127.0.0.1:80）
            ↑
        cloudflared（k8s-tunnel）
            ↑
        Cloudflare DNS（viclai.idv.tw）
            ↑
        外部使用者（手機、瀏覽器）
```

---

## 三個環境的差異

|               | DEV                     | STG                         | PROD                    |
| ------------- | ----------------------- | --------------------------- | ----------------------- |
| **用途**      | 本機開發測試            | 上線驗證，不公開            | 正式對外服務            |
| **存取方式**  | `localhost`（本機限定） | `stg.viclai.idv.tw`（外網） | `viclai.idv.tw`（公開） |
| **replicas**  | 1                       | 1                           | 2                       |
| **Vault**     | 關閉                    | 關閉                        | 關閉（待啟用）          |
| **CronJob**   | 關閉                    | 關閉                        | 開啟                    |
| **Namespace** | `dev`                   | `stg`                       | `prod`                  |

---

## Helm Chart 設計

Chart 採用「base + 環境覆蓋」模式：

```
values.yaml          ← 所有預設值（全部 disabled）
    +
values-dev.yaml      ← DEV 開啟的功能與設定
    =
最終部署設定
```

Helm 合併規則：環境 values 的值**覆蓋** base values，沒出現的欄位沿用 base。

### 目前 Chart 包含的資源

```
templates/
├── frontend-deployment.yaml   ← React 前端 Pod
├── frontend-service.yaml      ← ClusterIP Service
└── frontend-ingress.yaml      ← Ingress（hostname 路由）
```

---

## ArgoCD Application 設定

每個環境對應一個 Application yaml：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app-dev
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/zxcbig7/k8s-demo.git
    path: web-app
    helm:
      releaseName: web-app-dev
      valueFiles:
        - values.yaml       ← 先套用 base
        - values-dev.yaml   ← 再套用環境覆蓋
  destination:
    namespace: dev          ← 部署到對應 namespace
  syncPolicy:
    automated:
      prune: true           ← Git 刪掉的資源，K8s 也刪
      selfHeal: true        ← 手動改 K8s 會被自動還原
    syncOptions:
      - CreateNamespace=true  ← namespace 不存在自動建立
```

---

## Cloudflare Tunnel 路由

```
config.yml
├── stg.viclai.idv.tw → 127.0.0.1:80（Host: stg.viclai.idv.tw）
│                                  ↓
│                       K8s Ingress 比對 host
│                                  ↓
│                       stg namespace frontend service
│
└── viclai.idv.tw     → 127.0.0.1:80（Host: viclai.idv.tw）
                                   ↓
                        K8s Ingress 比對 host
                                   ↓
                        prod namespace frontend service
```

**httpHostHeader** 的作用：確保送到 K8s 的請求帶有正確的 Host header，讓 ingress controller 能路由到對應的服務。

---

## CI/CD 架構

前後端各有兩個 GitHub Actions workflow：

| Workflow      | 觸發           | 做什麼                                                |
| ------------- | -------------- | ----------------------------------------------------- |
| `ci.yml`      | push to main   | build + test（不部署）                                |
| `release.yml` | push tag `V.*` | build image → push Docker Hub → 更新 values-prod.yaml |

ArgoCD 偵測到 `values-prod.yaml` 變更後自動同步到 prod namespace。

```
push code to main
    → CI：build + test（只驗證，不部署）

git tag V.1.0.0.0.0 + push tag
    → release.yml：build image
    → push image to Docker Hub（tag: V.1.0.0.0.0）
    → 更新 Deployment repo values-prod.yaml
    → ArgoCD 自動 sync → pod rolling update
```

---

## 發版流程

### 前端發版

```bash
# 在 RuleViewerFrontend 目錄
git tag V.1.0.0.0.0
git push origin V.1.0.0.0.0
```

GitHub Actions 自動完成後續所有步驟。

### 後端發版

```bash
# 在 RuleViewerBackend 目錄
git tag V.1.0.0.0.0
git push origin V.1.0.0.0.0
```

### 確認部署狀態

```bash
kubectl get pods -n prod -w
kubectl get applications -n argocd
```

---

## Backend Secret（首次部署時需手動建立）

Backend pod 需要 K8s Secret 才能啟動，Secret 不屬於 Helm chart，需手動建立一次：

```bash
kubectl create secret generic web-app-prod-backend-secrets -n prod ^
  --from-literal=Jwt__Key="..." ^
  --from-literal=Google__ClientId="..." ^
  --from-literal=Google__ClientSecret="..."
```

> ASP.NET Core 環境變數用 `__` 代替設定檔的 `:` 分隔（例如 `Google:ClientId` → `Google__ClientId`）。

---

## 對外開放 Backend API

### 概念

Backend Service 預設是 `ClusterIP`，只有 cluster 內部能連。要讓外部（手機、其他裝置）打 API，需要加 Ingress 並設定 Cloudflare Tunnel 路由。

```
外部
  ↓ https://api.viclai.idv.tw
Cloudflare
  ↓ k8s-tunnel（cloudflared config.yml）
127.0.0.1:80（minikube tunnel）
  ↓
ingress-nginx（比對 Host: api.viclai.idv.tw）
  ↓
backend Service（ClusterIP:8082）
  ↓
backend Pod
```

### Step 1：新增 backend ingress Helm template

`templates/backend-ingress.yaml`：

```yaml
{{- if and .Values.backend.enabled .Values.backend.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-backend-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "{{ .Values.backend.ingress.tls.enabled }}"
spec:
  ingressClassName: nginx
  rules:
    - host: {{ .Values.backend.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-backend-service
                port:
                  number: 8082
{{- end }}
```

### Step 2：在 values.yaml 加預設值

```yaml
backend:
  ingress:
    enabled: false
    host: ""
    tls:
      enabled: false
```

### Step 3：在 values-prod.yaml 啟用

```yaml
backend:
  ingress:
    enabled: true
    host: api.viclai.idv.tw
    tls:
      enabled: false
```

### Step 4：Cloudflare DNS 加路由

```cmd
cloudflared tunnel route dns k8s-tunnel api.viclai.idv.tw
```

> 如果出現「record already exists」表示有舊的 CNAME，到 Cloudflare DNS 後台刪掉再重跑。

### Step 5：cloudflared config.yml 加 hostname

`C:\Users\zxcbi\.cloudflared\config.yml`：

```yaml
- hostname: api.viclai.idv.tw
  service: http://127.0.0.1:80
  originRequest:
    httpHostHeader: api.viclai.idv.tw
```

### Step 6：重啟 cloudflared

```cmd
cloudflared tunnel run k8s-tunnel
```

### 確認

```cmd
kubectl get ingress -n prod
```

看到 `web-app-prod-backend-ingress` 有 ADDRESS 表示成功。打：

```
https://api.viclai.idv.tw/api/ruleviewer/phases
```

---

## 本機啟動流程（start.bat）

```
start.bat
├── 1. 檢查 minikube 狀態，沒跑才 start
└── 2. 開 6 個 Windows Terminal tab
    ├── argocd-creds    顯示 ArgoCD 帳密
    ├── minikube-tunnel 讓 Ingress 接到 127.0.0.1:80
    ├── argocd          port-forward ArgoCD UI → localhost:8080
    ├── cloudflared     啟動 Cloudflare Tunnel（對外通道）
    ├── dashboard       開 K8s Dashboard 瀏覽器
    └── top             每 2 秒顯示所有 Pod 資源用量
```

---

## 常用指令

```bash
# 查看所有環境的 Pod
kubectl get pods -A | grep web-app

# 查看特定環境
kubectl get pods -n dev
kubectl get pods -n stg
kubectl get pods -n prod

# 查看 ArgoCD Application 狀態
kubectl get applications -n argocd

# 手動觸發 sync
kubectl annotate application web-app-dev -n argocd \
  argocd.argoproj.io/refresh=hard --overwrite

# 部署新環境（只需執行一次）
kubectl apply -f argocd/

# 刪除孤兒資源
kubectl get all -n <namespace>
kubectl delete <resource> <name> -n <namespace>
```
