---
tags: [devops, helm, kubernetes]
---

> 關聯：[[helm]]、[[kubernetes]]

# Helm 教學

## 一、什麼是 Helm

Helm 是 Kubernetes 的套件管理工具，概念類似 apt / npm。

沒有 Helm 時，你要管一堆獨立的 YAML：
```
deployment.yaml
service.yaml
configmap.yaml
```

有 Helm 後，這些打包成一個 **Chart**，用一個指令部署：
```bash
helm install nginx-web ./nginx-web
```

---

## 二、核心概念

| 名詞         | 說明                                          |
| ------------ | --------------------------------------------- |
| **Chart**    | Helm 的打包單位，就是你的 `nginx-web/` 資料夾 |
| **Release**  | 一次部署的實例，`helm install` 後產生         |
| **Values**   | 可調整的參數，定義在 `values.yaml`            |
| **Template** | 帶有變數的 K8s YAML，放在 `templates/`        |

---

## 三、Chart 結構

```
nginx-web/
├── Chart.yaml        # chart 的描述（名稱、版本）
├── values.yaml       # 預設變數值
└── templates/        # K8s manifest 模板
    ├── deployment.yaml
    ├── configmap.yaml
    └── service.yaml
```

---

## 四、Chart.yaml

描述這個 Chart 是什麼：

```yaml
apiVersion: v2
name: nginx-web
description: Nginx web server with TLS
type: application
version: 0.1.0      # Chart 本身的版本
appVersion: "latest" # 應用程式版本（nginx 版本）
```

---

## 五、values.yaml

定義所有可調整的參數，**集中管理**：

```yaml
replicaCount: 2

image:
  repository: nginx
  tag: latest

resources:
  requests:
    cpu: "100m"
    memory: "64Mi"
  limits:
    cpu: "200m"
    memory: "128Mi"
```

---

## 六、Template 語法

Template 是普通的 K8s YAML，加上 `{{ }}` 變數語法。

### 常用語法

**讀取 values：**
```yaml
replicas: {{ .Values.replicaCount }}
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

**讀取 Release 資訊：**
```yaml
name: {{ .Release.Name }}-deployment
# helm install nginx-web ./nginx-web → 產生 nginx-web-deployment
```

**條件判斷：**
```yaml
{{- if .Values.tls.enabled }}
- containerPort: 443
{{- end }}
```

**迴圈：**
```yaml
{{- range .Values.ports }}
- port: {{ .port }}
  targetPort: {{ .targetPort }}
{{- end }}
```

**預設值：**
```yaml
{{ .Values.replicas | default 1 }}
```

---

## 七、本專案範例

`values.yaml` 定義，`templates/deployment.yaml` 使用：

```yaml
# values.yaml
replicaCount: 2
image:
  repository: nginx
  tag: latest

# templates/deployment.yaml
spec:
  replicas: {{ .Values.replicaCount }}      # → 2
  containers:
    - image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"  # → nginx:latest
      name: {{ .Release.Name }}-container   # → nginx-web-container
```

---

## 八、常用指令

```bash
# 安裝（第一次部署）
helm install nginx-web ./nginx-web

# 更新（之後每次改動）
helm upgrade nginx-web ./nginx-web

# 安裝或更新（懶人指令）
helm upgrade --install nginx-web ./nginx-web

# 覆蓋 values（不改檔案，臨時調整）
helm upgrade nginx-web ./nginx-web --set replicaCount=3

# 查看目前部署的 release
helm list

# 刪除
helm uninstall nginx-web

# 預覽產生的 YAML（不實際部署）
helm template nginx-web ./nginx-web
```

---

## 九、Helm Repo

Helm Repo 是存放第三方 Chart 的倉庫，類似 npm registry。

### 常用指令

```bash
# 新增 repo
helm repo add <alias> <url>

# 更新所有 repo 的 index
helm repo update

# 列出已新增的 repo
helm repo list

# 搜尋 chart
helm search repo <keyword>

# 查看 chart 可用的 values
helm show values <repo>/<chart>
```

### 安裝第三方 Chart

```bash
helm install <release-name> <repo>/<chart> \
  --namespace <namespace> \
  --set key=value \
  --set key2=value2
```

`--set` 直接覆蓋 values，適合密碼等不想寫進 yaml 的設定。多個參數要覆蓋時，建議改用 `-f custom-values.yaml`。

### Repo URL 遷移問題

第三方 repo 可能因維護方遷移而導致舊 URL 失效：

```
Error: looks like "<url>" is not a valid chart repository or cannot be reached
```

遇到此錯誤，先查官方文件確認最新 repo URL，移除舊 repo 後重新加入：

```bash
helm repo remove <alias>
helm repo add <alias> <new-url>
helm repo update
```

---

## 十、搭配 ArgoCD

`argocd-app.yaml` 告訴 ArgoCD 用 Helm 部署：

```yaml
source:
  path: nginx-web          # Chart 的位置
  helm:
    releaseName: nginx-web # 等同於 helm install nginx-web
```

ArgoCD 會自動執行 `helm template` 產生 YAML 再套用到 K8s，不需要手動跑 `helm install`。

---

## 十、何時修改什麼

| 要改什麼                          | 改哪個檔案         |
| --------------------------------- | ------------------ |
| 副本數、image tag、資源限制       | `values.yaml`      |
| K8s 資源結構（新增 port、volume） | `templates/*.yaml` |
| Chart 版本號                      | `Chart.yaml`       |

---

## 十一、Ingress

Ingress 是 K8s 的 HTTP/HTTPS 流量入口，用域名路由流量取代 NodePort。

**啟用 minikube ingress addon：**
```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx  # 等 controller Running
```

**在 values.yaml 加入：**
```yaml
ingress:
  enabled: true
  host: nginx-web.local
  tls:
    enabled: true
    secretName: nginx-web-tls
```

**templates/ingress.yaml：**
```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    {{- if .Values.ingress.tls.enabled }}
    - hosts:
        - {{ .Values.ingress.host }}
      secretName: {{ .Values.ingress.tls.secretName }}
    {{- end }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-service
                port:
                  number: 443
{{- end }}
```

`ingress.enabled: true/false` 可以快速開關，不需刪檔案。

---

## 十二、Secret

K8s Secret 用來存放敏感資料（密碼、API key），不明文寫在 `values.yaml` 或 Git 裡。

### 方式一：環境變數
```yaml
env:
  - name: APP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: nginx-web-secret
        key: password
```
Pod 內用 `$APP_PASSWORD` 取值，更新需重啟 Pod。

### 方式二：檔案掛載（建議）
```yaml
volumeMounts:
  - name: secret-volume
    mountPath: /etc/secrets
    readOnly: true

volumes:
  - name: secret-volume
    secret:
      secretName: {{ .Release.Name }}-secret
```
Pod 內讀取 `/etc/secrets/password`，Secret 更新後約 1 分鐘自動生效，不需重啟。

|              | 環境變數                | 檔案掛載   |
| ------------ | ----------------------- | ---------- |
| **更新**     | 需重啟 Pod              | 自動更新   |
| **安全性**   | 較低（可能被 log 洩漏） | 較高       |
| **適合場景** | 一般設定                | 密碼、憑證 |

> ⚠️ **注意：** 把密碼寫在 `values.yaml` 等於明文存進 Git，正式環境應搭配 Vault 或 Sealed Secrets。

---

## 十三、CronJob

CronJob 是 K8s 的定時任務，使用標準 cron 語法。

**templates/cronjob.yaml：**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ .Release.Name }}-logger
spec:
  schedule: "* * * * *"           # 每分鐘執行
  successfulJobsHistoryLimit: 3   # 保留最近 3 個成功的 Job
  failedJobsHistoryLimit: 1       # 保留最近 1 個失敗的 Job
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: logger
              image: busybox
              command:
                - sh
                - -c
                - echo "[$(date '+%Y-%m-%d %H:%M:%S')] nginx-web is running"
          restartPolicy: OnFailure
```

**Cron 語法：**
```
* * * * *
│ │ │ │ └── 星期（0-7，0和7都是週日）
│ │ │ └──── 月份（1-12）
│ │ └────── 日（1-31）
│ └──────── 時（0-23）
└────────── 分（0-59）
```

常用範例：
```
"* * * * *"      每分鐘
"0 * * * *"      每小時整點
"0 0 * * *"      每天午夜
"0 9 * * 1-5"    週一到週五早上九點
```

**查看 log：**
```bash
kubectl get pods -n default          # 找 logger 開頭的 Pod
kubectl logs <logger-pod-name> -n default
```

---

## Chart 目錄完整結構

```text
my-chart/
├── Chart.yaml            # 套件元資料與依賴宣告（必要）
├── Chart.lock            # 依賴版本鎖定檔（自動產生，應納入版控）
├── values.yaml           # 預設參數值
├── values.schema.json    # 參數的 JSON Schema 驗證（選用）
├── templates/            # Go template 模板目錄
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── serviceaccount.yaml
│   ├── _helpers.tpl      # 共用具名模板（不會產生輸出）
│   ├── NOTES.txt         # 安裝後顯示的提示訊息
│   └── tests/
│       └── test-connection.yaml
├── charts/               # 下載的依賴套件（.tgz）
├── crds/                 # CRD 定義（在 templates 之前套用）
└── README.md
```

- **Release**：Chart 安裝到 Cluster 後的運行實例。一個 Chart 可以多次安裝，每次產生不同的 Release。
