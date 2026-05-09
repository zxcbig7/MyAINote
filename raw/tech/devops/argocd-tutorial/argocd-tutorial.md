# ArgoCD 教學 — 從安裝到自動部署

## 什麼是 ArgoCD？

ArgoCD 是一個 **GitOps** 工具，核心概念是：

> 「Git 是唯一的真相來源」

你把 K8s yaml 推到 Git，ArgoCD 自動偵測變更並同步到叢集，不需要手動執行 `kubectl apply`。

```
開發者 git push → GitHub → ArgoCD 偵測變更 → 自動部署到 K8s
```

---

## 前置條件

- minikube 已安裝並運行
- kubectl 已安裝
- 有 GitHub 帳號（用來放 yaml 檔案）

---

## Step 1：安裝 ArgoCD

建立專屬 namespace 並安裝：

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

等待所有 Pod 變成 Running（約 2～3 分鐘）：

```bash
kubectl get pods -n argocd -w
```

看到以下 Pod 都是 `Running` 才算完成：

| Pod 名稱                         | 用途                 |
| -------------------------------- | -------------------- |
| argocd-application-controller    | 監控叢集狀態         |
| argocd-applicationset-controller | 管理多個 Application |
| argocd-dex-server                | 登入驗證             |
| argocd-notifications-controller  | 通知功能             |
| argocd-redis                     | 快取                 |
| argocd-repo-server               | 從 Git 拉取 yaml     |
| argocd-server                    | Web UI 和 API        |

---

## Step 2：開啟 ArgoCD Web UI

用 port-forward 把 ArgoCD UI 導到本機（保持這個視窗開著）：

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

瀏覽器開啟：`https://localhost:8080`

> 會出現憑證警告，點「進階」→「繼續前往」即可

---

## Step 3：取得登入密碼

帳號：`admin`

密碼（CMD 執行）：

```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}"
```

輸出是 base64 編碼，手動解碼或貼給工具解碼即可。

> 登入後建議到 User Info → Update Password 修改密碼

---

## Step 4：把 yaml 推到 GitHub

1. 在 GitHub 建立新 repo（例如 `k8s-demo`）
2. 在專案目錄初始化 git：

```bash
git init
git add deployment.yaml .gitignore
git commit -m "add nginx deployment"
git remote add origin https://github.com/<你的帳號>/k8s-demo.git
git push -u origin master
```

> **注意**：使用 HTTPS 而非 SSH，ArgoCD 連 SSH 需要額外設定 SSH Agent

---

## Step 5：建立 ArgoCD Application

建立 `argocd-app.yaml`：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-web-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<你的帳號>/k8s-demo.git  # 用 HTTPS，不要用 SSH
    targetRevision: HEAD
    path: .                      # yaml 檔案在 repo 的根目錄
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true       # Git 刪掉的資源，K8s 也自動刪
      selfHeal: true    # 有人手動改 K8s，自動還原回 Git 狀態
```

套用：

```bash
kubectl apply -f argocd-app.yaml
```

---

## Step 6：確認同步狀態

```bash
kubectl get application -n argocd
```

看到 `Synced` 和 `Healthy` 代表成功：

```
NAME            SYNC STATUS   HEALTH STATUS
nginx-web-app   Synced        Healthy
```

也可以在 Web UI 上看到視覺化的同步狀態圖。

---

## 體驗 GitOps 流程

修改 `deployment.yaml`（例如改 replicas），然後推上 Git：

```bash
git add deployment.yaml
git commit -m "scale down to 2 replicas"
git push
```

約 3 分鐘後 ArgoCD 自動同步，`kubectl get pods` 就會反映變更。

手動觸發立即同步：

```bash
kubectl get application -n argocd   # 確認狀態
```

或在 Web UI 點擊 **Sync** 按鈕。

---

## 常見問題

### SSH agent requested but SSH_AUTH_SOCK not-specified

ArgoCD 無法使用 SSH 連 GitHub，改用 HTTPS URL：

```
# 錯誤
git@github.com:username/repo.git

# 正確
https://github.com/username/repo.git
```

### SYNC STATUS 一直是 Unknown

ArgoCD 還在連 Git 拉取資料，等 1～2 分鐘再查。若持續 Unknown，執行：

```bash
kubectl describe application nginx-web-app -n argocd
```

看 `Conditions` 欄位的錯誤訊息。

---

## 常用指令

```bash
# 查看所有 Application 狀態
kubectl get application -n argocd

# 查看 Application 詳細資訊與錯誤
kubectl describe application nginx-web-app -n argocd

# 查看 ArgoCD 所有 Pod
kubectl get pods -n argocd
```

---

## 日常使用流程

```
修改 yaml 檔案
    → git commit + git push
    → ArgoCD 自動偵測（預設每 3 分鐘 poll 一次）
    → 自動同步到 K8s
    → 完成，不需要手動 kubectl apply
```

---

## 私有 Repo 認證設定

ArgoCD 存取私有 GitHub repo 需要先建立 repository secret：

```bash
kubectl create secret generic repo-<name> \
  -n argocd \
  --from-literal=type=git \
  --from-literal=url=https://github.com/<user>/<repo>.git \
  --from-literal=username=<github-user> \
  --from-literal=password=<github-pat>

kubectl label secret repo-<name> -n argocd argocd.argoproj.io/secret-type=repository
```

**注意**：`kubectl create secret` 不支援 `-l` flag，label 要分開加。

確認 repo 已被 ArgoCD 認識：

```bash
kubectl get secret -n argocd -l argocd.argoproj.io/secret-type=repository
```

---

## ApplicationSet — 多環境批次建立 Application

ApplicationSet 用一個模板自動產生多個 Application（例如 dev/stg/prod）：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
  namespace: infra          # ApplicationSet 放的 namespace
spec:
  generators:
  - list:
      elements:
      - env: dev
      - env: stg
      - env: prod
  template:
    metadata:
      name: 'my-app-{{env}}'
      namespace: infra      # 產生的 Application 放的 namespace
    spec:
      project: default
      source:
        repoURL: https://github.com/<user>/<deployment-repo>.git
        targetRevision: HEAD
        path: helm-chart
        helm:
          releaseName: 'my-app-{{env}}'
          valueFiles:
          - values.yaml
          - 'values-{{env}}.yaml'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{env}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
```

**ApplicationSet 不產生 Application 的常見原因：**

| 原因 | 排查方式 |
|------|---------|
| Repo 沒有設定認證 | `kubectl get secret -n argocd -l argocd.argoproj.io/secret-type=repository` |
| ArgoCD 沒有 infra namespace 權限 | 確認 argocd-cmd-params-cm 有設 `application.namespaces: infra` |
| ApplicationSet controller log 有錯 | `kubectl logs -n argocd deployment/argocd-applicationset-controller` |

---

## ArgoCD 管理非 argocd namespace 的 Application

預設 ArgoCD Application 只能放在 `argocd` namespace。要讓它放在其他 namespace（如 `infra`）：

```bash
# 1. 告訴 ArgoCD 允許哪些 namespace 放 Application
kubectl patch configmap argocd-cmd-params-cm -n argocd \
  --type merge --patch '{"data":{"application.namespaces":"infra"}}'

# 2. 讓 default project 允許來自 infra namespace 的 Application
kubectl patch appproject default -n argocd \
  --type merge -p '{"spec":{"sourceNamespaces":["infra"]}}'

# 3. 重啟相關 controller 讓設定生效
kubectl rollout restart deployment argocd-applicationset-controller -n argocd
kubectl rollout restart statefulset argocd-application-controller -n argocd
```