---
type: reference
domain: tech
tags: [kubernetes, k8s, yaml, reference, argocd, helm, prometheus, cert-manager, gateway-api, kustomize]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 C-5：生態系 CRD 全欄位

附錄 C-1 到 C-4 涵蓋的是 Kubernetes 內建的 API。但實務上，你每天寫的 YAML 有很大一部分**根本不是內建 API**——ArgoCD 的 `Application`、Prometheus 的 `ServiceMonitor`、cert-manager 的 `Certificate`，這些都是靠 CRD 加進叢集的自訂資源（機制見第 9 章）。

它們有一個共同的麻煩：`kubectl explain` 對 CRD 的支援取決於該 CRD 有沒有寫好 schema description，很多社群 CRD 的說明是空的，於是你只能翻官網文件。這一份就是把最常用的那幾套攤平在同一個地方。

因為是第三方專案，版本節奏與 K8s 本身無關，所以每節標的是**該專案的版本**而不是 K8s 版本。欄位變動比內建 API 頻繁得多，落地前請對照你實際安裝的版本。

---

## ArgoCD Application（argoproj.io/v1alpha1）

GitOps 的核心物件。機制與 Sync/Health 的獨立性見第 11 章，這裡只攤欄位。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd # Application 必須放在 ArgoCD 所在的 namespace
  finalizers:
    - resources-finalizer.argocd.argoproj.io # 刪 Application 時連帶刪掉它部署的資源
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    targetRevision: HEAD # 分支、tag、commit SHA
    path: charts/my-app
    helm:
      releaseName: my-app
      valueFiles: ["values-prod.yaml"]
      values: | # 內嵌覆蓋，優先序高於 valueFiles
        replicaCount: 3
      parameters:
        - name: image.tag
          value: "1.4.0"
          forceString: true
      ignoreMissingValueFiles: false
      skipCrds: false
  destination:
    server: https://kubernetes.default.svc # 或用 name: in-cluster
    namespace: prod
  syncPolicy:
    automated:
      prune: true # git 刪掉的資源要不要跟著刪
      selfHeal: true # 有人手動改叢集就自動改回來
      allowEmpty: false # 防止 git 空目錄把整組資源刪光
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
      - PruneLast=true
      - ApplyOutOfSyncOnly=true
      - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers: ["/spec/replicas"] # 交給 HPA 管的欄位別再比對
  revisionHistoryLimit: 10
```

| 欄位 | 說明 |
| --- | --- |
| `source` / `sources` | 單一來源用 `source`；多來源（例如 chart 在 A repo、values 在 B repo）用 `sources[]` 並加 `ref` 互相引用 |
| `source.directory` | 純 YAML 目錄時用，`recurse: true` 遞迴、`include`/`exclude` 過濾檔案 |
| `source.kustomize` | `namePrefix`、`images`、`patches`、`commonLabels` |
| `syncPolicy.automated` | **不寫就是手動 sync**。`selfHeal` 沒開時，有人 `kubectl edit` 改了叢集，ArgoCD 只會顯示 OutOfSync 而不修正 |
| `ignoreDifferences` | 支援 `jsonPointers`、`jqPathExpressions`、`managedFieldsManagers`（依 field manager 忽略，最精準） |

常用的 syncOption：

| 選項 | 作用 |
| --- | --- |
| `CreateNamespace=true` | 目標 namespace 不存在就建 |
| `ServerSideApply=true` | 改用 SSA，解決大型 CRD 超過 annotation 大小上限的問題 |
| `PruneLast=true` | 所有資源同步完才刪舊資源，避免中途服務斷掉 |
| `Replace=true` | 用 `kubectl replace` 取代 apply，最後手段 |
| `Validate=false` | 跳過 schema 驗證 |
| `SkipDryRunOnMissingResource=true` | CRD 與 CR 同批部署時必備 |

搭配的 annotation（寫在**被部署的資源**上，不是 Application 上）：

| annotation | 值 | 作用 |
| --- | --- | --- |
| `argocd.argoproj.io/sync-wave` | 整數（可負） | 部署順序，小的先。DB migration 常設 `-1` |
| `argocd.argoproj.io/hook` | `PreSync`/`Sync`/`PostSync`/`SyncFail`/`Skip` | 生命週期鉤子 |
| `argocd.argoproj.io/hook-delete-policy` | `HookSucceeded`/`HookFailed`/`BeforeHookCreation` | hook Job 何時清掉 |
| `argocd.argoproj.io/compare-options` | `IgnoreExtraneous` | 這個資源不列入 OutOfSync 判定 |

---

## ArgoCD AppProject

權限邊界物件。多團隊共用一座 ArgoCD 時，這是唯一能防止 A 團隊部署到 B 團隊 namespace 的機制。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-a
  namespace: argocd
spec:
  description: "Team A 的部署範圍"
  sourceRepos:
    - https://github.com/org/team-a-*
  destinations:
    - server: https://kubernetes.default.svc
      namespace: team-a-*
  clusterResourceWhitelist: [] # 空陣列＝完全禁止部署 cluster-scoped 資源
  namespaceResourceBlacklist:
    - group: ""
      kind: ResourceQuota
  roles:
    - name: deployer
      policies:
        - p, proj:team-a:deployer, applications, sync, team-a/*, allow
      groups: ["team-a@example.com"] # 對應 OIDC group
  syncWindows:
    - kind: deny
      schedule: "0 9-18 * * 1-5" # cron 格式
      duration: 9h
      applications: ["*"]
      manualSync: true # 視窗內仍允許手動 sync
  orphanedResources:
    warn: true
```

`syncWindows` 是「上班時間禁止自動部署」這種需求的原生解法，比在 CI 加判斷乾淨。

---

## ArgoCD ApplicationSet

一份模板生出 N 個 Application，用於「同一套服務部署到多環境／多叢集」。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app-envs
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
          - env: prod
            namespace: prod
  template:
    metadata:
      name: "my-app-{{.env}}"
    spec: {} # 就是上面那份 Application spec
  strategy:
    type: RollingSync
    rollingSync:
      steps:
        - matchExpressions:
            - key: env
              operator: In
              values: [dev]
        - matchExpressions:
            - key: env
              operator: In
              values: [prod]
  syncPolicy:
    preserveResourcesOnDeletion: false
```

八種 generator：

| generator | 來源 |
| --- | --- |
| `list` | 手寫清單，最直接 |
| `cluster` | ArgoCD 註冊的叢集，可用 `selector` 過濾 |
| `git` | repo 內的目錄（`directories`）或檔案（`files`，讀 JSON/YAML 當參數） |
| `matrix` | 兩個 generator 的笛卡兒積（如「每個叢集 × 每個服務」） |
| `merge` | 合併多個 generator 的結果，後者覆蓋前者 |
| `scmProvider` | 掃 GitHub/GitLab organization 下所有 repo |
| `pullRequest` | 每個開著的 PR 生一個預覽環境 |
| `clusterDecisionResource` | 交給外部 CRD 決定 |

`strategy.type: RollingSync` 讓多環境依序更新（dev 綠了才推 prod），是 ApplicationSet 最被低估的欄位。

---

## Helm Chart.yaml（Helm 3）

```yaml
apiVersion: v2 # Helm 3 一律 v2；v1 是 Helm 2 遺留
name: my-app
version: 1.4.0 # chart 自己的版本，必須是 SemVer
appVersion: "2.1.0" # 應用的版本，字串，不必是 SemVer
type: application # 或 library（只提供 template，不能安裝）
description: My application
kubeVersion: ">=1.28.0-0" # 不符就拒絕安裝
keywords: [api, backend]
home: https://example.com
sources: ["https://github.com/org/repo"]
icon: https://example.com/icon.png
deprecated: false
maintainers:
  - name: Vic
    email: vic@example.com
dependencies:
  - name: postgresql
    version: "15.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled # values 裡這個值為 true 才安裝
    tags: [database]
    alias: primary-db
    import-values: []
annotations:
  artifacthub.io/changes: "- 修正 probe 逾時"
```

`version` 與 `appVersion` 的分工是最常被搞混的：改了 template 但應用沒變 → 只加 `version`；應用升版 → 兩個都要動。ArgoCD 以 `version` 判斷要不要重新渲染。

模板端的關鍵語法（完整說明見第 10 章）：

| 寫法 | 用途 | 陷阱 |
| --- | --- | --- |
| `{{ include "chart.labels" . }}` | 呼叫具名模板並取得字串 | 能接 pipe，優先用它 |
| `{{ template "chart.labels" . }}` | 同上但直接輸出 | **不能接 pipe**，無法 `nindent` |
| `{{ toYaml .Values.resources \| nindent 12 }}` | 物件轉 YAML 並縮排 | `nindent` 會先換行再縮排，`indent` 不會 |
| `{{ .Values.x \| default "v" \| quote }}` | 預設值與加引號 | 數字型 tag 沒 `quote` 會被當數字 |
| `{{ required "必須提供 x" .Values.x }}` | 缺值直接讓渲染失敗 | 比事後除錯省時 |
| `{{ .Release.Name }}` / `.Namespace` / `.IsUpgrade` | 安裝資訊 | `.Release.IsInstall` 可分辨首裝 |
| `{{ .Capabilities.APIVersions.Has "..." }}` | 依叢集能力分支 | `helm template` 離線渲染時會失準 |
| `{{ .Files.Get "config/app.yaml" }}` | 讀 chart 內檔案 | 適合塞進 ConfigMap |
| `{{ tpl .Values.tplString . }}` | 把 values 裡的字串當模板再渲染一次 | 讓使用者能在 values 裡寫模板 |

Helm hook annotation：

```yaml
metadata:
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install
    "helm.sh/hook-weight": "-5" # 小的先跑
    "helm.sh/hook-delete-policy": hook-succeeded
    "helm.sh/resource-policy": keep # 就算 helm uninstall 也保留（PVC 常用）
```

hook 可用值：`pre-install`、`post-install`、`pre-upgrade`、`post-upgrade`、`pre-delete`、`post-delete`、`pre-rollback`、`post-rollback`、`test`。

values 的覆蓋優先序，由低到高：chart 的 `values.yaml` → 父 chart 覆蓋子 chart → `-f custom.yaml`（多個時後者勝） → `--set` → `--set-string` / `--set-file`。

---

## Prometheus Operator

`ServiceMonitor` 讓 Prometheus 知道要抓誰。這是「我的服務有 `/metrics` 但 Prometheus 抓不到」的答案所在。

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  labels:
    release: prometheus # 必須符合 Prometheus CR 的 serviceMonitorSelector
spec:
  jobLabel: app.kubernetes.io/name
  selector:
    matchLabels:
      app: my-app # 選的是 **Service**，不是 Pod
  namespaceSelector:
    matchNames: [prod] # 或 any: true
  endpoints:
    - port: metrics # Service 的 port **名稱**，不是數字
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
      scheme: http
      honorLabels: false
      relabelings:
        - sourceLabels: [__meta_kubernetes_pod_node_name]
          targetLabel: node
      metricRelabelings:
        - sourceLabels: [__name__]
          regex: "go_gc_.*"
          action: drop # 抓進來但丟掉，省儲存
  targetLabels: [environment] # 把 Service 的 label 帶進 metric
  podTargetLabels: [version]
  sampleLimit: 10000
```

三個最常見的失敗原因，照順序查：ServiceMonitor 自己的 label 不符合 Prometheus 的 `serviceMonitorSelector`（多數 Helm chart 要求 `release: <helm release 名>`）、`endpoints.port` 寫了數字而不是 Service 的 port 名稱、以及 `namespaceSelector` 沒涵蓋到目標 namespace。

`PodMonitor` 結構相同，但 `selector` 選 Pod、端點欄位叫 `podMetricsEndpoints`，用於沒有 Service 的工作負載（如 Job）。

`PrometheusRule` 同時承載告警與預先計算規則：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  labels:
    release: prometheus
spec:
  groups:
    - name: my-app.rules
      interval: 30s
      rules:
        - record: job:http_request_latency:p95 # 預先算好，儀表板讀這個
          expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job))
        - alert: HighErrorRate
          expr: sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
          for: 5m # 持續 5 分鐘才真的告警，去抖動
          keep_firing_for: 10m # 恢復後仍維持告警一段時間，避免抖動
          labels:
            severity: critical
          annotations:
            summary: "5xx 比例超過 5%"
            runbook_url: https://wiki/runbooks/high-error-rate
```

`for` 是把「瞬間尖峰」與「真的出事」分開的關鍵欄位，沒設等於每個抖動都吵人。

---

## cert-manager（cert-manager.io/v1）

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer # 或 Issuer（只在單一 namespace 有效）
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            ingressClassName: nginx
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-token
              key: api-token
        selector:
          dnsZones: ["example.com"] # 萬用字元憑證只能走 dns01
```

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
spec:
  secretName: example-tls # 產出的 Secret，型別自動是 kubernetes.io/tls
  duration: 2160h # 90 天
  renewBefore: 360h # 到期前 15 天續簽
  commonName: example.com
  dnsNames: ["example.com", "www.example.com"]
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
    group: cert-manager.io
  privateKey:
    algorithm: RSA
    size: 2048
    rotationPolicy: Always # 每次續簽都換新私鑰
  usages: ["digital signature", "key encipherment"]
```

多數情況不必手寫 `Certificate`——在 Ingress 加 `cert-manager.io/cluster-issuer: letsencrypt-prod` annotation，cert-manager 會自動生一個。手寫的時機是需要 `duration`、`rotationPolicy` 這類細節控制時。

排查順序固定：`Certificate` → `CertificateRequest` → `Order` → `Challenge`，每一層 `kubectl describe` 看 event，失敗原因幾乎都在最後一層（DNS 記錄沒生效或 HTTP-01 路徑被 Ingress 攔走）。

---

## External Secrets Operator（external-secrets.io/v1beta1）

把 Vault 的機密同步成 K8s Secret，讓 git 裡不出現任何明文（第 6、8 章的 Vault 信任鏈）。

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: https://vault.example.com
      path: secret
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: my-app-role
          serviceAccountRef:
            name: app-sa
            namespace: prod
```

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-secret
  namespace: prod
spec:
  refreshInterval: 1h # 設 0 代表只同步一次
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: db-secret
    creationPolicy: Owner # Owner | Merge | Orphan | None
    deletionPolicy: Retain # Delete | Merge | Retain
    template:
      type: Opaque
      data:
        connection-string: "Host={{ .host }};Password={{ .password }}" # 組裝成應用要的格式
  data:
    - secretKey: password
      remoteRef:
        key: prod/db
        property: password
  dataFrom:
    - extract:
        key: prod/db # 整包取出，key 直接變成 Secret 的 key
```

`target.template` 是最實用的欄位：應用要的是一整條連線字串，而 Vault 存的是拆開的欄位，用 template 在同步時組裝，就不必改應用。

---

## VerticalPodAutoscaler（autoscaling.k8s.io/v1）

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Off" # Off | Initial | Recreate | Auto
    minReplicas: 2
  resourcePolicy:
    containerPolicies:
      - containerName: "*"
        mode: Auto # Auto | Off
        minAllowed:
          cpu: 100m
          memory: 128Mi
        maxAllowed:
          cpu: "2"
          memory: 4Gi
        controlledResources: ["cpu", "memory"]
        controlledValues: RequestsAndLimits # 或 RequestsOnly
```

| `updateMode` | 行為 |
| --- | --- |
| `Off` | 只計算建議值，不動任何東西。**建議先跑這個模式**，用 `kubectl describe vpa` 看建議再手動調 |
| `Initial` | 只在 Pod 建立時套用 |
| `Recreate` | 需要調整就殺掉 Pod 重建 |
| `Auto` | 目前等同 `Recreate`；等 in-place resize 成熟後才會真正原地調整 |

**VPA 與 HPA 不能同時管同一個資源指標**（兩者都調 CPU 會互相打架）。合法組合是 HPA 管 CPU 橫向、VPA 只管記憶體（用 `controlledResources: ["memory"]`）。

---

## Gateway API（gateway.networking.k8s.io/v1）

Ingress 的後繼者。設計上把角色拆開：叢集管理員管 `GatewayClass` 與 `Gateway`，應用團隊只寫 `HTTPRoute`。

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: nginx
spec:
  controllerName: gateway.nginx.org/nginx-gateway-controller
  parametersRef:
    group: gateway.nginx.org
    kind: NginxProxy
    name: proxy-config
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: prod-gateway
  namespace: infra
spec:
  gatewayClassName: nginx
  listeners:
    - name: https
      port: 443
      protocol: HTTPS
      hostname: "*.example.com"
      tls:
        mode: Terminate # 或 Passthrough
        certificateRefs:
          - name: example-tls
      allowedRoutes:
        namespaces:
          from: Selector # All | Same | Selector
          selector:
            matchLabels:
              gateway-access: "true"
        kinds:
          - kind: HTTPRoute
```

`HTTPRoute` 完整欄位：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api
  namespace: prod
spec:
  parentRefs:
    - name: prod-gateway
      namespace: infra
      sectionName: https # 綁定到指定 listener
  hostnames: ["api.example.com"]
  rules:
    - matches:
        - path:
            type: PathPrefix # Exact | PathPrefix | RegularExpression
            value: /v1
          method: GET
          headers:
            - name: X-Canary
              value: "true"
          queryParams:
            - name: debug
              value: "1"
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            set:
              - name: X-Env
                value: prod
            remove: ["X-Internal"]
        - type: URLRewrite
          urlRewrite:
            path:
              type: ReplacePrefixMatch
              replacePrefixMatch: /
      backendRefs:
        - name: api-svc
          port: 80
          weight: 90
        - name: api-canary
          port: 80
          weight: 10
      timeouts:
        request: 10s
        backendRequest: 5s
```

`filters` 型別：`RequestHeaderModifier`、`ResponseHeaderModifier`、`RequestMirror`（複製流量到影子服務）、`RequestRedirect`、`URLRewrite`、`ExtensionRef`。這些在 Ingress 時代全部是 controller 專屬 annotation，現在寫進規格本身——這就是 Gateway API 最大的價值：**換 controller 不用重寫路由**。

跨 namespace 引用需要被引用方明確授權：

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: ReferenceGrant
metadata:
  name: allow-prod-routes
  namespace: infra
spec:
  from:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
      namespace: prod
  to:
    - group: ""
      kind: Service
```

`GRPCRoute`、`TLSRoute`、`TCPRoute`、`UDPRoute` 結構類似，差在 `matches` 的維度。

---

## kustomization.yaml（kustomize.config.k8s.io/v1beta1）

不是 CRD，但也是你會寫的 YAML，而且 ArgoCD 原生支援。

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: prod
namePrefix: prod-
nameSuffix: -v2
resources:
  - ../../base
  - extra-configmap.yaml
components:
  - ../../components/monitoring
labels:
  - pairs:
      env: prod
    includeSelectors: false # 加到 selector 會導致 Deployment 無法更新，通常設 false
commonAnnotations:
  owner: team-a
images:
  - name: my-app
    newName: harbor.example.com/team-a/my-app
    newTag: 1.4.0
replicas:
  - name: my-app
    count: 5
patches:
  - target:
      kind: Deployment
      name: my-app
    patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/image
        value: my-app:1.4.0
configMapGenerator:
  - name: app-config
    files: [config/app.yaml]
    literals: [LOG_LEVEL=info]
    options:
      disableNameSuffixHash: false # 預設會加 hash 後綴，改了自動觸發滾動更新
secretGenerator:
  - name: db-secret
    envs: [.env.secret]
replacements:
  - source:
      kind: ConfigMap
      name: app-config
      fieldPath: data.VERSION
    targets:
      - select:
          kind: Deployment
        fieldPaths: [spec.template.metadata.annotations.version]
```

`configMapGenerator` 的 name hash 是 kustomize 最好用的特性：ConfigMap 內容一變，名稱後綴跟著變，引用它的 Deployment 因此改變、自動觸發滾動更新——正好解決第 6 章那個「改了 ConfigMap 但 Pod 沒重啟」的問題。

`labels.includeSelectors` 要留意：設 `true` 會把 label 加進 `spec.selector`，而 selector 是不可變欄位，既有 Deployment 會直接更新失敗。

已棄用但仍常在舊 repo 見到：`commonLabels`（改用 `labels`）、`patchesStrategicMerge` / `patchesJson6902`（都改用 `patches`）、`vars`（改用 `replacements`）、`bases`（改用 `resources`）。

---

## 連結

- [[66-ingress-to-gateway-api]] — 附錄 AR：這些 Gateway API 欄位怎麼從既有 Ingress 遷移過來
- [[18-yaml-fields-pod]] — 附錄 C-1：Pod 與 Container 全欄位
- [[19-yaml-fields-workloads]] — 附錄 C-2：Workload 與擴縮全欄位
- [[20-yaml-fields-network-storage]] — 附錄 C-3：網路與儲存全欄位
- [[21-yaml-fields-cluster-security]] — 附錄 C-4：叢集與安全全欄位
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：冷門內建資源全欄位
- [[24-yaml-fields-istio]] — 附錄 C-7：Istio 全欄位
- [[25-yaml-fields-pipeline]] — 附錄 C-8：GitHub Actions／cloudflared／Compose
- [[26-lab-drills]] — 附錄 D：破壞—診斷—修復實驗手冊
- [[10-helm]] — Helm 模板機制與除錯三件套
- [[11-argocd]] — GitOps pull 模型、Sync Wave、OutOfSync 診斷
- [[14-prometheus-grafana]] — PromQL 與告警設計
- [[k8s-mastery]] — 教材總目錄
