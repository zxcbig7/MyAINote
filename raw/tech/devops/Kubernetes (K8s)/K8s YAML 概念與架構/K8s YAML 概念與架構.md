# K8s YAML 概念與架構

<aside>
💡

 K8s YAML 有兩個層次的架構規則
第一層：所有資源共用的骨架
第二層：不同 kind 的 spec

</aside>

<aside>
💡

都用 `Key:Value` 格式進行儲存

</aside>

# 概念與架構

- Custom Resource Definition (CRD) 是讓你或第三方工具可以**自己定義新的 kind**，註冊到 K8s 裡面。

## 第一層：所有資源共用的骨架

> 每個資源物件的通用結構，所有資源都長這樣
> 

### 通用骨架

```yaml
apiVersion: <group>/<version>   # 用哪個 API 群組/版本或只有 <version>，例如 v1
kind: <資源類型>                 # 資源類型 (Pod、Deployment、Service 等)
metadata:                       # 名稱、namespace、labels 等
  name: <名稱>                   # 操作資源時用的識別碼
  namespace: <命名空間>          # 決定資源的隔離範圍，預設是 default
  labels:                       # 資源之間互相找到對方的機制（selector 配對）
    <key>: <value>
  annotations:                  # 給工具和人讀的附加資訊，K8s 本身不解讀內容
    <key>: <value>
spec:                           # 期望的狀態（該 kind 主要內容）
  <各 kind 自己定義的內容>
status:                         # 目前實際狀態（不用寫，K8s 會自己維護）
  ...
```

### apiVersion 的本質與設定

送出 YAML 給 K8s 的時候，實際上是在呼叫 K8s 的 REST API，而`apiVersion` 就是告訴 API Server 要打哪個 K8s 的端點。

```bash
kubectl apply -f pod.yaml
        ↓
HTTP POST 到 API Server
        ↓
/api/v1/namespaces/default/pods        (v1)
/apis/apps/v1/namespaces/default/deployments  (apps/v1)
```

**確認當前Cluster版本與支援的api**

> `apiVersion`決定 K8s 的 API Server 用哪個版本的規格來解讀和處理你的資源，版本不對就找不到端點，版本太舊可能被移除，所以要跟叢集的 K8s 版本對齊。
> 
- **K8s 的 API 分成幾個群組，不同資源屬於不同群組：**

```bash
# 列出所有支援的 API 群組和版本
kubectl api-versions

# 列出所有資源及其對應的 apiVersion
kubectl api-resources

# 看到的清單反映的是「這個 Cluster 現在認識哪些資源」
# 只能用清單裡有的 apiVersion 和 kind，寫了清單以外的東西就會報錯。
```

**常見的 apiVersion**

- **概念：**核心資源用 `v1`，其他功能群組用 `群組名稱/v1`。

| apiVersion | 包含哪些常用 kind |
| --- | --- |
| `v1` | Pod、Service、ConfigMap、Secret、Namespace、PersistentVolume |
| `apps/v1` | Deployment、StatefulSet、DaemonSet、ReplicaSet |
| `batch/v1` | Job、CronJob |
| `networking.k8s.io/v1` | Ingress |
| `rbac.authorization.k8s.io/v1` | Role、ClusterRole、RoleBinding |

### metadata 概念

```yaml
metadata:                       # 名稱、namespace、labels 等
  name: <名稱>                  # 操作資源時用的識別碼
  namespace: <命名空間>          # 省略的話預設是 default
  labels:
    <key>: <value>
  annotations:
    <key>: <value>
```

- 同一個 namespace 裡，同一個 kind 的 name 不能重複
    - production namespace 裡不能有兩個叫 my-app 的 Deployment
    - production 和 staging 各自 namespace 可以有一個 my-app
- 同一個 cluster 可以切成多個 namespace，資源預設只能看到同 namespace 的其他資源

```bash
Cluster
├── production namespace
│     ├── Deployment: my-app
│     └── Service: my-app      ← 這個 Service 可以找到同 namespace 的 Pod
│
└── staging namespace
      ├── Deployment: my-app   ← 雖然名字一樣，但完全獨立
      └── Service: my-app
```

- 下 kubectl 指令操作資源，靠的就是 name 來指定

```yaml
kubectl get deployment **my-app** -n production
kubectl delete service **my-app** -n production
```

- labels 是資源之間互相找到對方的機制，K8s 資源靠 label selector 互相連結
    
    ```yaml
    # Pod 身上貼的標籤
    metadata:
      labels:
        app: my-app        # 貼了這個標籤
    
    ---
    
    # Service 用 selector 去找
    spec:
      selector:
        app: my-app        # 找所有貼了這個標籤的 Pod
    ```
    
    ```bash
    Service
      └── selector: app=my-app
            ↓ 掃描叢集裡所有 Pod
            ↓ 找到有 app=my-app 標籤的
            └── 流量導過去
    ```
    
    - Deployment 管理 Pod 也是同樣機制
        
        ```yaml
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: my-app
        spec:
          selector:
            matchLabels:
              app: my-app          # Deployment 管理這些 Pod
        
          template:
            metadata:
              labels:
                app: my-app        # 產生出來的 Pod 會貼這個標籤
        ```
        
        <aside>
        💡
        
        `spec.selector` 和 `template.metadata.labels` 必須對得起來，否則 Deployment 找不到自己建立的 Pod。
        
        </aside>
        
- annotations 和 labels 的差別：
    
    
    |  | labels | annotations |
    | --- | --- | --- |
    | 用途 | 資源互相選取 | 存放額外資訊給工具讀 |
    | 可以用 selector 篩選 | 可以 | 不行 |
    | 常見使用者 | K8s 本身 | Ingress controller、cert-manager 等第三方工具 |

### 各 kind 關係

```yaml
Deployment
  └── 管理 ReplicaSet
        └── 管理 Pod（實際跑的容器）
              └── 用 ConfigMap / Secret 注入設定
                  用 PersistentVolumeClaim 掛載儲存

Service
  └── 透過 label selector 找到 Pod，提供穩定的網路入口

Ingress
  └── 依照 HTTP 路徑/域名，把流量導向不同 Service
```

## 第二層：不同 kind 的 spec

> `Pod`、`Deployment`、`Service`、`ConfigMap`、`Ingress` 各自的 `spec` 欄位都不一樣，
> 

### **計算層 (Container 的管理)**

| Kind | 職責 |
| --- | --- |
| `Pod` | 最小部署單位，直接包容器，通常不直接用 |
| `Deployment` | 管理無狀態應用，支援滾動更新、回滾 |
| `StatefulSet` | 管理有狀態應用（資料庫），Pod 有固定名稱和儲存 |
| `DaemonSet` | 每個 Node 都跑一份，適合 log agent、監控 agent |
| `Job` | 跑完就結束的任務 |
| `CronJob` | 定時執行的 Job |

#### Pod

- 直接寫 Pod 有個問題：Pod 掛掉不會自動重建。
- 實務上幾乎都是寫 Deployment，讓 Deployment 管理所有 Pod 的生命週期。
- 一個 Pod 可以跑多個 container，但大多數情況只跑一個。
- env 注入環境變數
    - 敏感資料不要直接寫 `value`，應該放 Secret 再引用。
- 資源限制概念
    - `requests`: K8s 排程 Pod 到哪個 Node 的依據，保證有這麼多資源
    - `limits`:超過這個量就被限制，memory 超過會被 OOMKill
    - cpu 單位 `250m` 是 250 millicores，也就是 0.25 顆 CPU。
- livenessProbe 和 readinessProbe
    - 實務上兩個都要設，否則 container 啟動中還沒 ready，流量就進來了。
    
    |  | 失敗後的行為 |
    | --- | --- |
    | `livenessProbe` | 重啟 container |
    | `readinessProbe` | 從 Service 的流量中移除，但不重啟 |
- 必要架構
    
    ```yaml
    apiVersion: v1        # 必填
    kind: Pod             # 必填
    metadata:
      name: my-pod        # 必填
    spec:
      containers:
        - name: xxx       # 必填
          image: xxx      # 必填
    ```
    
- 完整架構
    
    ```yaml
    # ==============================
    # Pod 基本資訊
    # ==============================
    apiVersion: v1        # Pod 屬於核心 API 群組，固定用 v1
    kind: Pod             # 資源類型
    metadata:
      name: my-pod        # Pod 名稱，同 namespace 下不可重複
      namespace: default  # 省略的話預設就是 default
      labels:
        app: my-app       # 給 Service / Deployment 的 selector 用來配對
        env: production   # 自定義標籤，方便篩選和管理
    
    # ==============================
    # Pod 的期望狀態
    # ==============================
    spec:
      containers:
        - name: my-container    # container 名稱，同一個 Pod 內不可重複
          image: nginx:1.25     # 映像檔，永遠指定版本，不要用 latest
                                # 用 latest 會導致每次拉的版本不可控
          ports:
            - containerPort: 80 # 純粹宣告用途，不寫也不影響實際網路行為
                                # 但寫出來讓人一眼知道這個服務監聽哪個 port
    
          # --------------------------
          # 環境變數注入
          # --------------------------
          env:
            - name: ENV_NAME        # 環境變數名稱
              value: "hello"        # 直接寫值，適合非敏感設定
    
            - name: APP_CONFIG      # 從 ConfigMap 取值
              valueFrom:
                configMapKeyRef:
                  name: my-configmap  # ConfigMap 的 metadata.name
                  key: config-key     # ConfigMap 裡面的哪個 key
    
            - name: DB_PASSWORD     # 從 Secret 取值
              valueFrom:            # 敏感資料不要直接寫 value
                secretKeyRef:
                  name: my-secret   # Secret 的 metadata.name
                  key: password     # Secret 裡面的哪個 key
    
          # --------------------------
          # 資源限制
          # --------------------------
          resources:
            requests:
              memory: "64Mi"    # 排程時保證分配的記憶體
              cpu: "250m"       # 排程時保證分配的 CPU，250m = 0.25 顆
                                # K8s 根據 requests 決定 Pod 排到哪個 Node
            limits:
              memory: "128Mi"   # 記憶體上限，超過會被 OOMKill（強制重啟）
              cpu: "500m"       # CPU 上限，超過會被throttle（降速，不重啟）
    
          # --------------------------
          # 存活探針，判斷是否需要重啟
          # --------------------------
          livenessProbe:
            httpGet:
              path: /health     # 打這個路徑，回傳 2xx 就算存活
              port: 80
            initialDelaySeconds: 10   # 啟動後等 10 秒才開始探測，給應用程式初始化的時間
            periodSeconds: 5          # 之後每 5 秒探測一次，連續失敗超過 failureThreshold（預設3次）就重啟
    
          # --------------------------
          # 就緒探針，判斷是否接收流量
          # --------------------------
          readinessProbe:
            httpGet:
              path: /ready      # 打這個路徑，回傳 2xx 才算就緒
              port: 80
            initialDelaySeconds: 5    # 比 liveness 早一點開始
            periodSeconds: 3          # 3 秒探測一次，失敗的話從 Service 流量中移除，但不重啟
    
      # --------------------------
      # 重啟策略
      # --------------------------
      restartPolicy: Always     # Always：掛掉就重啟（預設值，適合長駐服務）
                                # OnFailure：只有非正常結束才重啟（適合 Job）
                                # Never：不重啟
    ```
    

#### Deployment

Deployment 跟 Pod 的結構差異：`template` 裡面就是一個完整的 Pod 定義，所以學會寫 Pod 之後，Deployment 只是在外面多包一層。

```yaml
Pod
└── spec
      └── containers

Deployment
└── spec
      ├── replicas         # 新增，幾個 Pod
      ├── selector         # 新增，怎麼找到自己的 Pod
      ├── strategy         # 新增，怎麼更新
      └── template         # Pod 的完整定義包在這裡
            ├── metadata
            └── spec
                  └── containers  # 跟 Pod 完全一樣
```

- 完整架構
    
    ```yaml
    # ==============================
    # Deployment 基本資訊
    # ==============================
    apiVersion: apps/v1   # Deployment 屬於 apps 群組，用 apps/v1
    kind: Deployment
    metadata:
      name: my-deployment
      namespace: default
      labels:
        app: my-app       # Deployment 本身的標籤，方便管理用
                          # 注意：這裡的 labels 是貼在 Deployment 上
                          # 不是貼在 Pod 上
    
    # ==============================
    # Deployment 的期望狀態
    # ==============================
    spec:
      replicas: 3         # 要維持幾個 Pod 同時運行
                          # Deployment 會持續確保這個數量
                          # Pod 掛掉會自動重建，這是跟直接寫 Pod 最大的差別
    
      # --------------------------
      # selector，Deployment 用來找自己管理的 Pod
      # --------------------------
      selector:
        matchLabels:
          app: my-app     # 找所有貼了 app=my-app 標籤的 Pod 來管理
                          # 這裡必須跟下面 template.metadata.labels 對得起來
                          # 對不起來的話 Deployment 找不到自己建立的 Pod，會報錯
    
      # --------------------------
      # 更新策略
      # --------------------------
      strategy:
        type: RollingUpdate       # 預設值，滾動更新
                                  # 另一個選項是 Recreate（先全刪再重建，會有停機時間）
        rollingUpdate:
          maxSurge: 1             # 更新過程中，最多可以多出幾個 Pod
                                  # 例如 replicas=3，更新時最多同時存在 4 個 Pod
          maxUnavailable: 0       # 更新過程中，最多允許幾個 Pod 不可用
                                  # 設 0 代表更新過程中保持全部 Pod 都在線
    
      # --------------------------
      # Pod 模板，Deployment 根據這個建立 Pod
      # --------------------------
      template:
        metadata:
          labels:
            app: my-app   # 建立出來的 Pod 會貼這個標籤
                          # 必須跟上面 selector.matchLabels 一致
                          # 這是 Deployment 和 Pod 之間的連結點
    
        # --------------------------
        # 以下跟直接寫 Pod 的 spec 完全相同
        # --------------------------
        spec:
          containers:
            - name: my-container
              image: nginx:1.25       # 永遠指定版本，不要用 latest
              ports:
                - containerPort: 80
    
              env:
                - name: ENV_NAME
                  value: "hello"
    
                - name: APP_CONFIG
                  valueFrom:
                    configMapKeyRef:
                      name: my-configmap
                      key: config-key
    
                - name: DB_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: my-secret
                      key: password
    
              resources:
                requests:
                  memory: "64Mi"
                  cpu: "250m"
                limits:
                  memory: "128Mi"
                  cpu: "500m"
    
              livenessProbe:
                httpGet:
                  path: /health
                  port: 80
                initialDelaySeconds: 10
                periodSeconds: 5
    
              readinessProbe:
                httpGet:
                  path: /ready
                  port: 80
                initialDelaySeconds: 5
                periodSeconds: 3
    
          restartPolicy: Always
    ```
    

### **網路層（讓別人連進來）**

| Kind | 職責 |
| --- | --- |
| `Service` | 給一組 Pod 一個穩定 IP 和 DNS，做 load balancing |
| `Ingress` | HTTP/HTTPS 層的路由規則，對外的唯一入口 |

#### Service

- 完整範例
    
    ```yaml
    # ==============================
    # Service 基本資訊
    # ==============================
    apiVersion: v1          # Service 屬於核心 API 群組，固定用 v1
    kind: Service
    metadata:
      name: my-service      # Service 名稱，同 namespace 下不可重複
      namespace: default    # 省略的話預設就是 default
      labels:
        app: my-app         # 這個 Service 本身的標籤，方便管理用
    
    # ==============================
    # Service 的期望狀態
    # ==============================
    spec:
      # --------------------------
      # selector，決定流量導到哪些 Pod
      # --------------------------
      selector:
        app: my-app         # 找到所有貼了 app=my-app 標籤的 Pod
                            # Pod 新增或消失，Service 會即時更新流量池
                            # 這裡的值要跟 Pod 的 metadata.labels 對得起來
    
      # --------------------------
      # ports，定義 port 對應關係
      # --------------------------
      ports:
        - name: http        # 選填，有多個 port 時方便識別
          protocol: TCP     # 預設 TCP，大多數情況不需要特別寫
          port: 80          # 其他資源連到這個 Service 用的 port
          targetPort: 3000  # 實際轉發到 Pod 監聽的 port
                            # port 和 targetPort 可以不一樣
                            # 對外統一用 80，Pod 內部跑 3000
    
      # --------------------------
      # type，決定 Service 的網路範圍
      # --------------------------
      type: ClusterIP       # ClusterIP：只有叢集內部可以存取（預設值）
                            # NodePort：開 Node 的 port 對外，測試環境用
                            # LoadBalancer：請雲端平台建立 LB，生產環境用
                            # ExternalName：對應到外部 DNS，存取叢集外服務用
    ```
    
- NodePort 額外欄位
    
    ```yaml
    spec:
      type: NodePort
      ports:
        - port: 80
          targetPort: 3000
          nodePort: 30080   # 選填，不寫會自動分配 30000-32767 之間的值
                            # 外部用 <Node IP>:30080 連進來
    ```
    
- ExternalName 額外欄位
    
    ```yaml
    spec:
      type: ExternalName
      externalName: my-database.example.com  # 對應到外部的 DNS 名稱
                                              # Pod 用 Service 名稱存取
                                              # K8s 自動解析到這個外部位址
    ```
    
    #### Ingress
    

#### **Ingress**

**Ingress 在整體架構裡的位置**

- Ingress 是整個叢集對外的統一入口，後面接多個 Service。

```yaml
外部流量
    ↓
Ingress（HTTP 路由規則）
    ↓ 依照 host / path 分流
Service A | Service B | Service C
    ↓           ↓          ↓
  Pod 群      Pod 群      Pod 群
```

**Ingress Controller 是什麼**

- Ingress YAML 本身只是一份 Rule，需要有 Ingress Controller 才能真正運作。

```yaml
你寫的 Ingress YAML（規則）
        ↓
Ingress Controller 讀取規則（實際執行的程式）
        ↓
真正處理進來的 HTTP 流量
```

**常見的 Ingress Controller**

- 叢集裡沒裝 Ingress Controller，寫了 Ingress 也不會動。

| Controller | 說明 |
| --- | --- |
| `ingress-nginx` | 最常用，基於 nginx |
| `traefik` | 自動服務發現，設定簡單 |
| `AWS ALB` | AWS 環境專用 |
| `GCE` | GCP 環境專用 |

**pathType 兩種差別**

```yaml
path: /api
pathType: Prefix    # /api、/api/users、/api/orders 都符合
pathType: Exact     # 只有 /api 完全符合，/api/users 不符合
```

**多個 host 的路由邏輯**

```yaml
Request 進來
    ↓
比對 host header
    ├── example.com     → 走 example.com 的 rules
    └── admin.example.com → 走 admin.example.com 的 rules
            ↓
        比對 path
        ├── /     → frontend-svc
        └── /api  → backend-svc
```

- 必填欄位
    
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: my-ingress
    spec:
      rules:
        - host: example.com
          http:
            paths:
              - path: /
                pathType: Prefix
                backend:
                  service:
                    name: my-service
                    port:
                      number: 80
    ```
    
- 完整範例
    
    ```yaml
    # ==============================
    # Ingress 基本資訊
    # ==============================
    apiVersion: networking.k8s.io/v1    # Ingress 在 networking 群組，K8s 1.19 之後用這個
    kind: Ingress
    metadata:
      name: my-ingress
      namespace: default
      annotations:
        kubernetes.io/ingress.class: nginx        # 告訴叢集用哪個 Ingress Controller 處理
        cert-manager.io/cluster-issuer: letsencrypt-prod  # 告訴 cert-manager 自動申請 SSL 憑證
    
    # ==============================
    # Ingress 的期望狀態
    # ==============================
    spec:
      # --------------------------
      # TLS，HTTPS 設定
      # --------------------------
      tls:
        - hosts:
            - example.com               # 這個憑證負責哪個 domain
          secretName: example-tls       # 憑證存放在哪個 Secret
                                        # cert-manager 會自動建立這個 Secret
    
      # --------------------------
      # rules，HTTP 路由規則
      # --------------------------
      rules:
        - host: example.com             # 這條規則負責哪個 domain
          http:
            paths:
              - path: /                 # 根路徑，所有請求都導到這個 Service
                pathType: Prefix        # Prefix：開頭符合就算，Exact：完全符合才算
                backend:
                  service:
                    name: frontend-svc  # 導到哪個 Service
                    port:
                      number: 80        # 導到 Service 的哪個 port
    
              - path: /api              # /api 開頭的請求導到另一個 Service
                pathType: Prefix
                backend:
                  service:
                    name: backend-svc
                    port:
                      number: 80
    
        - host: admin.example.com       # 不同 subdomain 導到不同 Service
          http:
            paths:
              - path: /
                pathType: Prefix
                backend:
                  service:
                    name: admin-svc
                    port:
                      number: 80
    ```
    

### **設定層（注入設定和密碼）**

| kind | 職責 | 儲存方式 |
| --- | --- | --- |
| `ConfigMap` | 存非敏感設定，例如環境變數、設定檔 | 明文 |
| `Secret` | 存敏感資料，例如密碼、token、憑證 | base64 編碼（非加密） |

#### ConfigMap

ConfigMap 有三種方式注入到 Pod

- 方式一：env，單獨取某個 key
- 方式二：envFrom，整包 ConfigMap 全部變成環境變數
- 方式三：volumeMount，掛載成檔案

### 三種方式的使用情境

| 方式 | 適合情境 |
| --- | --- |
| `env 單一 key` | 只需要部分設定值 |
| `envFrom 整包` | 設定值全部都要，key 名稱剛好可以當環境變數 |
| `volumeMount` | 需要整份設定檔，例如 nginx.conf、application.properties |
- 必填欄位
    
    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: my-configmap
    data:
      KEY: "value"
    ```
    
- 完整架構
    
    ```yaml
    # ==============================
    # ConfigMap 基本資訊
    # ==============================
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: my-configmap
      namespace: default
    
    # ==============================
    # 資料內容
    # ==============================
    data:
      # --------------------------
      # 方式一：簡單的 key-value
      # --------------------------
      DB_HOST: "localhost"
      DB_PORT: "5432"
      APP_ENV: "production"
    
      # --------------------------
      # 方式二：整份設定檔當作值
      # --------------------------
      app.properties: |          # | 代表保留換行，整段文字原樣存入
        server.port=8080
        server.timeout=30
        log.level=info
    
      nginx.conf: |
        server {
          listen 80;
          location / {
            proxy_pass http://backend;
          }
        }
    ```
    

#### Secret

### **儲存層（資料持久化）**

| Kind | 職責 |
| --- | --- |
| `PersistentVolume (PV)` | 管理員預先準備的一塊儲存空間 |
| `PersistentVolumeClaim (PVC)` | 應用程式「申請」要用多少儲存 |

# 其他

## 同一個 `.yaml` 檔案寫多個資源

> 每個 kind 都是獨立的規格，需要各別處理撰寫，不過可以用YAML 的多文件語法 `---` 分隔，把多kind寫在同一個yaml檔案內。(如下範例)
> 

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  ...

--- # 分隔

apiVersion: v1
kind: Service
metadata:
  name: my-app-svc
spec:
  ...
```

- 務上通常會把相關資源放在同一個檔案，或是一個資料夾下用 `kubectl apply -f ./` 一次套用全部設定。