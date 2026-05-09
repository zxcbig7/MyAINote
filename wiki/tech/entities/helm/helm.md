---
type: entity
domain: tech
tags: [helm, kubernetes, devops, chart, deployment]
sources:
  - raw/tech/devops/Helm Chart.md
  - raw/tech/devops/Kubernetes (K8s).md
created: 2026-05-03
updated: 2026-05-03
---

# Helm

Helm 是 Kubernetes 的應用部署**打包工具**，把一個服務的所有 K8s YAML 統一打包成一個叫 Chart 的集合，透過給參數的方式同時管理與設定這些 YAML 檔。

**Helm = Chart + Release + Repository**

- **Chart**：描述 K8s 資源配置的套件
- **Release**：Chart 安裝到 Cluster 後的運行實例。一個 Chart 可多次安裝，每次是不同 Release
- **Repository**：存放 Chart 的地方

## Chart 目錄結構

```
my-chart/
├── Chart.yaml            # 套件元資料與依賴宣告（必要）
├── Chart.lock            # 依賴版本鎖定（自動產生）
├── values.yaml           # 預設參數值
├── values.schema.json    # 參數 JSON Schema 驗證（選用）
├── templates/            # Go template 模板目錄
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── _helpers.tpl      # 共用具名模板（不產生輸出）
│   └── NOTES.txt         # 安裝後顯示的提示訊息
├── charts/               # 下載的依賴套件（.tgz）
└── crds/                 # CRD 定義（在 templates 之前套用）
```

## values.yaml 與 Template 語法

`values.yaml` 定義所有可覆寫的參數，`templates/` 裡的 YAML 用 Go template 語法引用：

```yaml
# values.yaml
replicaCount: 2
image:
  repository: nginx
  tag: "1.25"
service:
  type: ClusterIP
  port: 80
```

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-chart.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

## 多環境 values 管理

```
helm/
├── values.yaml           # 預設值（共用）
├── values-dev.yaml       # dev 環境覆寫
├── values-stg.yaml       # staging 環境覆寫
└── values-prod.yaml      # prod 環境覆寫
```

安裝時指定環境：
```bash
helm install my-release ./my-chart -f values-prod.yaml
```

## 常用指令

```bash
# 建立新 Chart 骨架
helm create my-chart

# 安裝 Chart（首次部署）
helm install <release-name> <chart-path>
helm install my-app ./my-chart -f values-prod.yaml

# 升級 Release（已部署的更新）
helm upgrade <release-name> <chart-path>
helm upgrade my-app ./my-chart -f values-prod.yaml

# 解除安裝 Release
helm uninstall my-app

# 列出所有 Release
helm list

# 查看 Release 狀態
helm status my-app

# 查看渲染後的 YAML（不實際部署）
helm template my-app ./my-chart -f values-prod.yaml

# 語法檢查
helm lint ./my-chart

# 打包 Chart
helm package ./my-chart

# 回滾到指定版本
helm rollback my-app 1
```

## 與 ArgoCD 整合

ArgoCD 監控 Git repo，讀取 Helm Chart 並用指定 values 渲染後同步到 K8s：

```yaml
# ArgoCD Application 範例
spec:
  source:
    repoURL: https://github.com/myorg/myapp-manifest
    path: helm
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    namespace: prod
```

## 連結

- [[kubernetes]] — Helm 管理的目標平台
- [[argocd]] — GitOps 工具，監控 Helm Chart 並部署
- [[cicd-pipeline]] — CI/CD 流程中 Helm 的角色
