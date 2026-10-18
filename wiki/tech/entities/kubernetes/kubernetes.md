---
type: entity
domain: tech
tags: [kubernetes, k8s, container, orchestration, devops]
sources:
  - raw/tech/devops/Kubernetes (K8s).md
  - raw/tech/devops/K8s YAML 概念與架構.md
created: 2026-05-03
updated: 2026-08-14
---

# Kubernetes (K8s)

Kubernetes 是一個容器編排平台，以高層次抽象化自動操作與管理容器，解決三大問題：
- **Deployment**：部署多 Container 到多設備
- **Scaling**：隨服務 Loading 自動擴縮
- **Management**：偵測並重啟故障容器

## 四大核心元件

### Pod（應用環境）
- 運作的**最小單位**，對應一個 Application（如 API Server）
- 每個 Pod 有一份 YAML 身分證
- 通常一個 Pod 跑一個 Container，但可多個
- 同 Pod 內 Containers 共享網路與資源，透過 local port 溝通
- **實務上不直接寫 Pod，用 Deployment 管理生命週期**

### Worker Node（執行設備）
- 運作的**最小硬體單位**，對應一台機器（電腦、EC2、VM）
- 每個 Node 有三個組件：
  - `kubelet`：管理該 Node 上所有 Pod 狀態，與 Master 溝通
  - `kube-proxy`：更新 Node iptables，讓其他物件得知 Pod 最新狀態
  - `Container Runtime`：負責容器執行（如 Docker Engine）

### Master Node（指揮中心）
- 特化的 Node，管理所有其他 Node
- 四個組件：
  - `kube-apiserver`：整個 K8s 的 API 接口，所有 kubectl 指令送到這裡；負責身份認證與節點溝通橋樑
  - `etcd`：備份 Cluster 資料，Master 故障時還原狀態
  - `kube-controller-manager`：監視 Cluster 狀態，確保實際狀態符合期望狀態（Desired State）
  - `kube-scheduler`：決定新 Pod 要排到哪個 Node 執行

### Cluster
- 多個 Node 與 Master 的集合，在同一環境中所有 Node 的集合
- 通常有多個 Master 作為備援
- `kubectl` 是操作 Cluster 的 CLI 工具

## K8s YAML 架構

### 通用骨架（所有資源共用）

```yaml
apiVersion: <group>/<version>   # API 群組/版本，例如 v1 或 apps/v1
kind: <資源類型>                 # Pod、Deployment、Service、Ingress 等
metadata:
  name: <名稱>                   # 同 namespace 下同 kind 不可重複
  namespace: <命名空間>          # 預設 default
  labels:                       # 資源間互相選取（selector 配對）
    app: my-app
  annotations:                  # 給工具讀的附加資訊
spec:                           # 期望狀態（各 kind 自己定義）
  ...
status:                         # 實際狀態（K8s 自動維護，不需寫）
```

### 常見 apiVersion

| apiVersion | 常用 kind |
| --- | --- |
| `v1` | Pod、Service、ConfigMap、Secret、Namespace |
| `apps/v1` | Deployment、StatefulSet、DaemonSet |
| `batch/v1` | Job、CronJob |
| `networking.k8s.io/v1` | Ingress |
| `rbac.authorization.k8s.io/v1` | Role、ClusterRole |

## 計算層資源

### Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app
spec:
  containers:
    - name: my-container
      image: nginx:1.25       # 永遠指定版本，不用 latest
      ports:
        - containerPort: 80
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: my-secret
              key: password
      resources:
        requests:
          memory: "64Mi"
          cpu: "250m"         # 250 millicores = 0.25 顆 CPU
        limits:
          memory: "128Mi"
          cpu: "500m"
      livenessProbe:          # 失敗 → 重啟 container
        httpGet:
          path: /health
          port: 80
        initialDelaySeconds: 10
        periodSeconds: 5
      readinessProbe:         # 失敗 → 移除 Service 流量，不重啟
        httpGet:
          path: /ready
          port: 80
```

### Deployment

Deployment = Pod 外面多包一層（replicas、selector、strategy、template）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app             # 必須與 template.metadata.labels 一致
  strategy:
    type: RollingUpdate       # 滾動更新，預設值
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-container
          image: nginx:1.25
```

- `replicas`：期望 Pod 數量（Desired State）
- 支援 **Zero Downtime Rollout**：更新時先啟動新 Pod，確認 Running 後才停舊 Pod
- `kubectl rollout undo deploy <name>`：回滾到上一版
- `kubectl rollout history deploy <name>`：查看版本歷史

## 網路層資源

### Service
給一組 Pod 一個穩定 IP 和 DNS，做 load balancing。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: my-app
  ports:
    - port: 80          # Service 對外 port
      targetPort: 3000  # Pod 實際監聽 port
  type: ClusterIP       # ClusterIP（叢集內）/ NodePort（測試）/ LoadBalancer（雲端）
```

### Ingress
HTTP/HTTPS 層路由，叢集對外的統一入口，依 host/path 分流到不同 Service。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts: [example.com]
      secretName: example-tls
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-svc
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend-svc
                port:
                  number: 80
```

- Ingress 需搭配 Ingress Controller 才能運作（常用 `ingress-nginx`）

## 設定層資源

| Kind | 職責 | 儲存方式 |
| --- | --- | --- |
| `ConfigMap` | 非敏感設定（env、設定檔） | 明文 |
| `Secret` | 敏感資料（密碼、token、憑證） | base64 編碼 |

ConfigMap 三種注入方式：`env` 單一 key、`envFrom` 整包、`volumeMount` 掛載成檔案

## 各 Kind 關係總覽

```
Deployment → ReplicaSet → Pod（跑 Container）
                               ↑
                    ConfigMap / Secret 注入設定
                    PVC 掛載儲存

Service → 透過 label selector 找 Pod，提供穩定網路入口
Ingress → 依 host/path 把流量導向 Service
```

## 其他重要概念

- **Namespace**：資源隔離範圍。同 namespace 同 kind name 不可重複；不同 namespace 可以有同名資源（dev/staging/prod）
- **etcd**：K8s 的資料庫，存所有 Cluster 狀態
- **PVC（PersistentVolumeClaim）**：應用程式申請的持久化儲存空間

## 連結

- [[k8s-mastery]] — 完整教材總目錄（16 章 + 6 附錄）；本頁只是速查摘要
- [[18-yaml-fields-pod]] — Pod/Container 逐欄位百科，本頁 YAML 骨架的完整版
- [[19-yaml-fields-workloads]] — Deployment/StatefulSet/Job/HPA 全欄位
- [[20-yaml-fields-network-storage]] — Service/Ingress/PVC 全欄位
- [[21-yaml-fields-cluster-security]] — RBAC/CRD/Webhook 全欄位
- [[docker]] — K8s 管理的 Container 技術
- [[minikube]] — 本機單節點 K8s 環境
- [[helm]] — K8s 應用打包工具
- [[kubectl]] — K8s CLI 操作指令
- [[argocd]] — GitOps 部署到 K8s 的控制器
- [[wiki/tech/entities/vault]] — K8s Secret 管理強化方案
