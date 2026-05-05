# Minikube 教學 — 本機 Kubernetes 環境

## 什麼是 Minikube？

Minikube 是一個在本機電腦上跑 **單節點 Kubernetes 叢集** 的工具，適合學習和開發測試用。

---

## 安裝

前往官網下載安裝：https://minikube.sigs.k8s.io/docs/start/

確認安裝成功：

```bash
minikube version
kubectl version --client
```

---

## 基本操作

### 啟動 / 停止

```bash
minikube start       # 啟動叢集
minikube stop        # 停止叢集（保留狀態）
minikube delete      # 刪除叢集（完全清除）
minikube status      # 查看目前狀態
```

### 開啟 Dashboard（視覺化 UI）

```bash
minikube dashboard
```

---

## 部署第一個應用

### 1. 撰寫 deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-web-deployment
spec:
  replicas: 4
  selector:
    matchLabels:
      app: nginx-web
  template:
    metadata:
      labels:
        app: nginx-web
    spec:
      containers:
        - name: nginx-web-container
          image: nginx:latest
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          ports:
            - containerPort: 80
            - containerPort: 443
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-web-service
spec:
  type: NodePort
  selector:
    app: nginx-web
  ports:
    - name: http
      port: 80
      targetPort: 80
    - name: https
      port: 443
      targetPort: 443
```

### 2. 套用並確認

```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get svc nginx-web-service
```

### 3. 用瀏覽器開啟

```bash
minikube service nginx-web-service
```

或取得完整 URL：

```bash
minikube service nginx-web-service --url
```

---

## 常用 kubectl 指令

### Pod 管理

```bash
kubectl get pods                          # 列出所有 Pod
kubectl get pods -o wide                  # 含 Node IP 等詳細資訊
kubectl get pods -w                       # 即時監控狀態變化
kubectl describe pod <pod-name>           # 查看 Pod 詳細資訊與事件
kubectl logs <pod-name>                   # 查看 Pod log
kubectl logs -l app=nginx-web --tail=20   # 用 label 查多個 Pod log
kubectl exec -it <pod-name> -- bash       # 進入 Pod 內部
kubectl delete pod <pod-name>             # 刪除 Pod（Deployment 管理的會自動重建）
```

### Deployment 管理

```bash
kubectl get deployments                                    # 列出所有 Deployment
kubectl describe deployment nginx-web-deployment          # 查看詳細資訊
kubectl scale deployment nginx-web-deployment --replicas=2 # 調整 Pod 數量
kubectl rollout restart deployment nginx-web-deployment   # 重啟 Deployment
kubectl rollout status deployment nginx-web-deployment    # 查看更新進度
kubectl rollout undo deployment nginx-web-deployment      # 回滾到上一版
```

### 版本更新（Rolling Update）

```bash
# 更新映像版本
kubectl set image deployment/nginx-web-deployment nginx-web-container=nginx:1.25

# 觀察滾動更新過程
kubectl rollout status deployment/nginx-web-deployment
```

Rolling Update 會逐步替換 Pod，確保服務不中斷。

### Service 管理

```bash
kubectl get svc                    # 列出所有 Service
kubectl describe svc nginx-web-service  # 查看 Service 詳細資訊
```

---

## 取得叢集 IP

```bash
minikube ip
```

搭配 `kubectl get svc` 查到的 NodePort，即可從外部存取服務：

```
http://<minikube ip>:<NodePort>
```

---

## 資源監控

### 安裝 metrics-server

```bash
minikube addons enable metrics-server
```

> 啟用後約等 1 分鐘讓它收集數據

```bash
kubectl top nodes    # 查看 Node 資源使用量
kubectl top pods     # 查看 Pod 資源使用量
```

### 常見問題：Metrics API not available

metrics-server 需要跳過 kubelet 的 TLS 驗證：

```bash
kubectl patch deployment metrics-server -n kube-system \
  --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

---

## 自簽 TLS 憑證（HTTPS）

在本機環境無法使用 Let's Encrypt，改用自簽憑證：

```bash
# 產生憑證並存成 K8s Secret（PowerShell）
$env:OPENSSL_CONF="NUL"; openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=nginx-web.local"; kubectl create secret tls nginx-web-tls --cert=tls.crt --key=tls.key
```

憑證建立後，Pod 掛載 Secret 即可啟用 HTTPS。

> 瀏覽器會顯示「不安全」警告，這是正常的，因為自簽憑證不是受信任 CA 發出的。

---

## Addons 管理

```bash
minikube addons list                        # 列出所有可用 addon
minikube addons enable <addon-name>         # 啟用 addon
minikube addons disable <addon-name>        # 停用 addon
```

常用 addon：

| Addon                 | 用途                   |
| --------------------- | ---------------------- |
| `metrics-server`      | Pod / Node 資源監控    |
| `ingress`             | HTTP/HTTPS 路由        |
| `dashboard`           | 視覺化 Web UI          |
| `storage-provisioner` | 動態 PVC（預設已啟用） |

---

## Label 機制

Label 是 K8s 資源之間互相識別的方式：

```
Deployment selector → 找到帶有指定 label 的 Pod 來管理
Service selector    → 找到帶有指定 label 的 Pod 來導流
```

查詢特定 label 的 Pod：

```bash
kubectl get pods -l app=nginx-web
```

---

## Resource Limits 說明

```yaml
resources:
  requests:
    cpu: "100m"      # 排程保證：0.1 顆 CPU
    memory: "64Mi"   # 排程保證：64MB 記憶體
  limits:
    cpu: "200m"      # 上限：超過會被限速
    memory: "128Mi"  # 上限：超過會被 OOMKill 重啟
```

- **requests**：K8s 排程時確保 Node 有這麼多資源才放 Pod 上去
- **limits**：防止單一 Pod 佔用過多資源影響其他 Pod（noisy neighbor）

---

## 正式環境的差異

|              | Minikube             | 正式環境                 |
| ------------ | -------------------- | ------------------------ |
| 節點數       | 1                    | 多個                     |
| 憑證         | 自簽                 | Let's Encrypt / 商業憑證 |
| Service 類型 | NodePort             | LoadBalancer             |
| 存取方式     | minikube ip          | 公開 IP / Domain         |
| 資源監控     | metrics-server addon | Prometheus + Grafana     |

---

## Driver 選擇

| Driver | 說明 |
| --- | --- |
| `docker` | 用 Docker container 模擬節點，最常用（跨平台） |
| `hyperkit` | macOS 原生 VM |
| `hyper-v` | Windows 原生 VM |
| `virtualbox` | 跨平台 VM |
