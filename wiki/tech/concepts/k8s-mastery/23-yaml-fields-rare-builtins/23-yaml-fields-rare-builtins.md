---
type: reference
domain: tech
tags: [kubernetes, k8s, yaml, reference, csi, csr, apf, kubeadm, kubelet, kubeconfig]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 C-6：冷門內建資源與元件設定檔

這一份收的是前五份沒收進去的東西，分成兩類。

第一類是**內建但你平常不會手寫的 kind**——CSI 家族、`Lease`、`FlowSchema` 之類。它們平常由系統自己維護，但出事的時候你得看得懂：Pod 掛不上磁碟要查 `VolumeAttachment`，API Server 回 429 要查 `FlowSchema`，控制平面選主異常要查 `Lease`。

第二類是**元件自己的設定檔**——kubelet、kube-proxy、scheduler、kubeadm 的 YAML。這些不是 K8s API 物件（不存在 etcd 裡，也不能 `kubectl apply`），但它們同樣是 YAML，而且是叢集管理員真正會改的東西。放進來，「所有 YAML 設定」這句話才算兌現。

基準 **v1.33**。

---

## 遺留資源：認得就好，不要新寫

| kind | 狀態 | 說明 |
| --- | --- | --- |
| `Endpoints` | 被 `EndpointSlice` 取代 | 單一物件塞所有後端，超過約 1000 個位址會出問題。舊 YAML 才有 |
| `ReplicationController` | 被 `Deployment`/`ReplicaSet` 取代 | selector 只支援等值比對，不支援 `matchExpressions` |
| `ComponentStatus` | 1.19 起棄用 | `kubectl get cs` 的來源，回報常不準，改看各元件的 `/healthz` |
| `PodTemplate` | 幾乎沒人用 | 獨立存在的 Pod 模板物件 |
| `Binding` | 內部用 | scheduler 把 Pod 綁到 Node 的動作物件，不手寫 |
| `HorizontalPodAutoscaler`（`autoscaling/v1`） | 舊版 | 只有 `targetCPUUtilizationPercentage`，沒有 `metrics` 也沒有 `behavior`。一律用 `autoscaling/v2` |

```yaml
# Endpoints 舊寫法，僅供讀舊 repo 時對照
apiVersion: v1
kind: Endpoints
metadata:
  name: legacy-db # 名稱必須與 Service 同名
subsets:
  - addresses:
      - ip: 10.0.0.42
    ports:
      - port: 5432
        protocol: TCP
```

---

## Event 與 Lease

`Event` 是排錯時最常看卻最少人知道它是一個 API 物件的東西。預設只保留一小時（`--event-ttl`），所以「昨天的事故」在 event 裡通常已經查不到——這是為什麼日誌收集（第 15 章）要納入 event。

```yaml
apiVersion: events.k8s.io/v1
kind: Event
metadata:
  name: my-pod.17a3f
  namespace: prod
type: Warning # Normal | Warning
reason: FailedScheduling
note: "0/3 nodes are available: insufficient cpu."
regarding: # 舊版 v1 叫 involvedObject
  kind: Pod
  name: my-pod
  namespace: prod
reportingController: default-scheduler
reportingInstance: default-scheduler-node1
action: Scheduling
deprecatedCount: 12
```

實用查法：`kubectl get events --sort-by=.metadata.creationTimestamp -A`，或鎖定單一物件 `kubectl get events --field-selector involvedObject.name=my-pod`。

`Lease` 是分散式選主與心跳的載體。每個 Node 在 `kube-node-lease` namespace 有一份租約，kubelet 每 10 秒續約一次——Node 變 `NotReady` 的判定就是看這個，而不是看整個 Node 物件的更新。

```yaml
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: kube-scheduler
  namespace: kube-system
spec:
  holderIdentity: node1_8a2f... # 誰是目前的 leader
  leaseDurationSeconds: 15
  acquireTime: "2026-08-14T00:00:00.000000Z"
  renewTime: "2026-08-14T00:10:31.000000Z"
  leaseTransitions: 3 # 換手過幾次，頻繁增加＝控制平面不穩
```

控制平面「看起來活著但沒在工作」時，查 `kubectl get lease -n kube-system` 的 `renewTime` 是最快的判斷方式。

---

## CSI 家族

這四個都由 CSI driver 自己註冊與維護，你只讀不寫。

```yaml
apiVersion: storage.k8s.io/v1
kind: CSIDriver
metadata:
  name: ebs.csi.aws.com
spec:
  attachRequired: true # 掛載前是否需要 attach 階段（決定有沒有 VolumeAttachment）
  podInfoOnMount: false # 掛載時是否把 Pod 資訊傳給 driver
  volumeLifecycleModes: ["Persistent", "Ephemeral"]
  storageCapacity: true # 是否回報 CSIStorageCapacity 供排程參考
  fsGroupPolicy: File # File | ReadWriteOnceWithFSType | None
  requiresRepublish: false
  seLinuxMount: true
```

| kind | 內容 | 什麼時候看它 |
| --- | --- | --- |
| `CSIDriver` | driver 的能力宣告 | 判斷這個 driver 支不支援某種模式 |
| `CSINode` | 每個 Node 上註冊了哪些 driver、topology key、可掛載上限 | Pod 排到某台就掛不上磁碟時 |
| `CSIStorageCapacity` | 各 topology 的剩餘容量 | 配合 `WaitForFirstConsumer` 讓 scheduler 避開容量不足的 zone |
| `VolumeAttachment` | 某個 volume 是否已 attach 到某台 Node | `Multi-Attach error` 的真相所在 |

```yaml
apiVersion: storage.k8s.io/v1
kind: VolumeAttachment
spec:
  attacher: ebs.csi.aws.com
  nodeName: node-2
  source:
    persistentVolumeName: pvc-3f2a...
status:
  attached: true
```

Node 突然失聯時，舊的 `VolumeAttachment` 可能殘留，導致新 Pod 在別台 Node 上永遠掛不上磁碟。確認方式是 `kubectl get volumeattachment | grep <pv>`，看它還綁在哪台。

快照側的兩個物件：

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete # Delete | Retain
parameters: {}
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-snapshot-0814
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: data-my-db-0
```

`VolumeSnapshotContent` 是對應的叢集層物件（類比 PV 之於 PVC），欄位有 `driver`、`deletionPolicy`、`source.volumeHandle`（既有快照匯入時用 `snapshotHandle`）、`volumeSnapshotRef`。

---

## 憑證與 API 聚合

```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: vic-csr
spec:
  request: <base64 的 PEM CSR>
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400
  usages: ["client auth"]
```

四種內建 `signerName`：`kubernetes.io/kube-apiserver-client`（使用者/元件客戶端憑證）、`kubernetes.io/kube-apiserver-client-kubelet`（kubelet 客戶端）、`kubernetes.io/kubelet-serving`（kubelet 伺服器憑證）、`kubernetes.io/legacy-unknown`（不再簽發）。核准用 `kubectl certificate approve <name>`，簽好的憑證在 `status.certificate`（base64）。這是「幫新同事開一組 kubeconfig」的正規流程。

`ClusterTrustBundle`（1.33 為 beta）用來散佈 CA 憑證束，讓工作負載透過 projected volume 取得可信 CA，取代把 CA 塞進每個 ConfigMap 的做法。

```yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1beta1.metrics.k8s.io
spec:
  service:
    name: metrics-server
    namespace: kube-system
    port: 443
  group: metrics.k8s.io
  version: v1beta1
  groupPriorityMinimum: 100
  versionPriority: 100
  insecureSkipTLSVerify: true
```

`APIService` 是把外部服務接成 API Server 一部分的機制（Aggregation Layer）。`kubectl top` 失效時第一個要查的就是它：`kubectl get apiservice v1beta1.metrics.k8s.io`，`Available: False` 代表 metrics-server 連不上。

---

## API Priority and Fairness

API Server 過載時，決定誰先被服務、誰被回 429。預設規則通常夠用，但自訂控制器把 API Server 打爆時，你需要看得懂這兩個物件。

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1
kind: FlowSchema
metadata:
  name: my-controller
spec:
  priorityLevelConfiguration:
    name: workload-low
  matchingPrecedence: 1000 # 1–10000，數字小的先比對
  distinguisherMethod:
    type: ByUser # ByUser | ByNamespace
  rules:
    - subjects:
        - kind: ServiceAccount
          serviceAccount:
            name: my-controller
            namespace: prod
      resourceRules:
        - verbs: ["*"]
          apiGroups: ["*"]
          resources: ["*"]
          namespaces: ["*"]
---
apiVersion: flowcontrol.apiserver.k8s.io/v1
kind: PriorityLevelConfiguration
metadata:
  name: workload-low
spec:
  type: Limited # Limited | Exempt
  limited:
    nominalConcurrencyShares: 10
    lendablePercent: 50 # 閒置時可借出多少額度給別人
    borrowingLimitPercent: 100
    limitResponse:
      type: Queue # Queue | Reject
      queuing:
        queues: 64
        handSize: 6
        queueLengthLimit: 50
```

排查用 `kubectl get --raw /debug/api_priority_and_fairness/dump_priority_levels`，或看 `apiserver_flowcontrol_rejected_requests_total` 這個 metric。

---

## 新一代網路與裝置資源

```yaml
# ServiceCIDR / IPAddress（1.33 為 beta）：讓 Service 網段可以動態擴充
apiVersion: networking.k8s.io/v1beta1
kind: ServiceCIDR
metadata:
  name: extra-range
spec:
  cidrs: ["10.96.0.0/16", "2001:db8::/112"]
```

以往 Service 網段是 API Server 的啟動參數，改一次要重啟整個控制平面；有了 `ServiceCIDR` 就能線上追加。`IPAddress` 是每個已配發 IP 的物件表示，由系統維護。

Dynamic Resource Allocation（1.33 為 beta，`resource.k8s.io`）是 GPU 這類裝置的新配置模型，取代舊的 device plugin「數量」語意，改成可以描述「我要一張至少 40GB 顯存、支援 MIG 的卡」：

| kind | 角色 |
| --- | --- |
| `DeviceClass` | 管理員定義的裝置類別與篩選條件 |
| `ResourceClaim` | 一次具體的裝置請求 |
| `ResourceClaimTemplate` | 讓每個 Pod 各自生一份 claim |
| `ResourceSlice` | driver 回報各 Node 上有哪些裝置 |

Pod 端用 `spec.resourceClaims[]` 引用，容器再用 `resources.claims[]` 取用（見附錄 C-1）。

---

## Admission 的其餘物件

`MutatingWebhookConfiguration` 的欄位與附錄 C-4 的 validating 版本相同，多兩個：

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `reinvocationPolicy` | `Never` | 設 `IfNeeded` 時，若其他 webhook 後續又改了物件，你會被再呼叫一次 |
| `webhooks[].clientConfig.url` | — | 指向叢集外的服務（`service` 的替代，兩者擇一） |

`ValidatingAdmissionPolicy` 要真正生效必須有 binding：

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-limits-binding
spec:
  policyName: require-resource-limits
  validationActions: ["Deny"] # Deny | Warn | Audit，可多選
  matchResources:
    namespaceSelector:
      matchLabels:
        policy: enforced
  paramRef:
    name: limits-params
    parameterNotFoundAction: Deny
```

只寫 policy 不寫 binding，是「規則明明寫了卻沒作用」的標準原因。想先觀察不擋人，把 `validationActions` 設成 `["Warn", "Audit"]`。

（`MutatingAdmissionPolicy` 在 1.33 仍是 alpha，改寫類需求目前仍需 webhook。`StorageVersionMigration` 則用於 CRD 換 storage version 後的資料遷移，屬升級流程的一環。）

---

## 元件設定檔：不是 API 物件，但你會改

以下這些**不能 `kubectl apply`**。它們是各元件啟動時從磁碟讀的設定檔，改完要重啟該元件（kubeadm 叢集多半放在 `/var/lib/kubelet/config.yaml` 與 `/etc/kubernetes/manifests/` 底下）。

### kubeadm ClusterConfiguration

```yaml
apiVersion: kubeadm.k8s.io/v1beta4
kind: ClusterConfiguration
kubernetesVersion: v1.33.0
controlPlaneEndpoint: "k8s-api.example.com:6443"
networking:
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
  dnsDomain: cluster.local
etcd:
  local:
    dataDir: /var/lib/etcd
apiServer:
  certSANs: ["k8s-api.example.com", "10.0.0.10"]
  extraArgs: # v1beta4 起是 list，不再是 map（同一參數可重複）
    - name: audit-log-path
      value: /var/log/kubernetes/audit.log
    - name: encryption-provider-config
      value: /etc/kubernetes/enc/enc.yaml
controllerManager:
  extraArgs:
    - name: node-monitor-grace-period
      value: 40s
```

同一份檔案裡可用 `---` 接 `InitConfiguration`（本機初始化參數、`nodeRegistration`）、`JoinConfiguration`（加入叢集用）與 `KubeletConfiguration`。升級叢集前用 `kubeadm config print init-defaults` 對照目前版本的欄位差異。

### KubeletConfiguration

管理員最常調的一份，直接決定 Node 的穩定性。

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd # 必須與 container runtime 一致，不一致 Node 會 NotReady
maxPods: 110
systemReserved: # 留給作業系統
  cpu: 200m
  memory: 512Mi
kubeReserved: # 留給 kubelet 與 runtime
  cpu: 200m
  memory: 512Mi
evictionHard: # 觸發驅逐的硬門檻
  memory.available: "200Mi"
  nodefs.available: "10%"
  imagefs.available: "15%"
evictionSoft:
  memory.available: "500Mi"
evictionSoftGracePeriod:
  memory.available: "1m30s"
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
containerLogMaxSize: 10Mi
containerLogMaxFiles: 5
serializeImagePulls: false
rotateCertificates: true
staticPodPath: /etc/kubernetes/manifests
featureGates:
  InPlacePodVerticalScaling: true
```

`systemReserved` + `kubeReserved` 決定 Node 的 `allocatable`（＝排程真正能用的量）。兩者都不設，等於允許 Pod 把記憶體吃到連 kubelet 都活不下去，症狀是整台 Node 一起失聯而不是單一 Pod 被殺。`containerLogMaxSize` 沒設好則是磁碟被日誌撐爆、`DiskPressure` 驅逐全部 Pod 的常見原因。

### KubeProxyConfiguration

```yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: ipvs # iptables | ipvs | nftables
ipvs:
  scheduler: rr # rr | lc | dh | sh | sed | nq
  syncPeriod: 30s
  strictARP: true # MetalLB L2 模式必須開
conntrack:
  maxPerCore: 32768
  tcpEstablishedTimeout: 24h
clusterCIDR: 10.244.0.0/16
```

Service 數量大時 `iptables` 模式的規則同步會變慢（規則數與 Service 數成正比），`ipvs` 用 hash 表因此擴展性好得多；`nftables` 是更新的選項。

### KubeSchedulerConfiguration

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
percentageOfNodesToScore: 50 # 大叢集只評分一半節點以換取速度
profiles:
  - schedulerName: default-scheduler
    plugins:
      score:
        enabled:
          - name: NodeResourcesFit
            weight: 5
        disabled:
          - name: NodeResourcesBalancedAllocation
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated # 裝箱優先，配合 cluster-autoscaler 省錢
  - schedulerName: spread-scheduler # 第二個 profile，Pod 用 spec.schedulerName 指定
    plugins: {}
leaderElection:
  leaderElect: true
```

`scoringStrategy` 的 `LeastAllocated`（預設，平均分散）與 `MostAllocated`（集中裝箱）是一個真實的成本 / 韌性取捨：想讓 autoscaler 能縮節點就選後者。

### EncryptionConfiguration 與 Audit Policy

etcd 落盤加密（第 8 章提過 Secret 只是 base64，這是補救之一）：

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: ["secrets", "configmaps"]
    providers:
      - kms: # 優先序由上而下，第一個用於加密
          apiVersion: v2
          name: vault-kms
          endpoint: unix:///var/run/kmsplugin/socket.sock
      - aescbc:
          keys:
            - name: key1
              secret: <base64 32 bytes>
      - identity: {} # 不加密。放最後代表「可以讀舊的未加密資料」
```

`identity` 放在**第一位**等於全部不加密，放在最後才是正確的過渡設定。啟用後既有資料不會自動加密，要跑一次 `kubectl get secrets -A -o json | kubectl replace -f -` 觸發重寫。

稽核政策：

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages: ["RequestReceived"]
rules:
  - level: None # 雜訊來源直接不記
    users: ["system:kube-proxy"]
    verbs: ["watch"]
  - level: RequestResponse # 機密資源記完整內容
    resources:
      - group: ""
        resources: ["secrets"]
  - level: Metadata # 其餘只記中繼資料
```

四種 `level`：`None`、`Metadata`（誰在什麼時候對什麼做了什麼）、`Request`（含請求內容）、`RequestResponse`（含回應）。規則由上而下比對，第一個命中就決定，所以把 `None` 的雜訊規則放前面。

---

## kubeconfig

嚴格說不是叢集裡的東西，但它是你天天在用的 YAML。

```yaml
apiVersion: v1
kind: Config
current-context: minikube
clusters:
  - name: minikube
    cluster:
      server: https://127.0.0.1:50814
      certificate-authority-data: <base64>
      insecure-skip-tls-verify: false
users:
  - name: minikube
    user:
      client-certificate-data: <base64>
      client-key-data: <base64>
  - name: oidc-user
    user:
      exec: # 動態取 token，雲端叢集與 OIDC 都走這條
        apiVersion: client.authentication.k8s.io/v1
        command: kubelogin
        args: ["get-token", "--oidc-issuer-url=https://accounts.google.com"]
        env: []
        interactiveMode: IfAvailable
        provideClusterInfo: false
contexts:
  - name: minikube
    context:
      cluster: minikube
      user: minikube
      namespace: default
preferences: {}
```

`context` ＝（cluster, user, namespace）三元組。多叢集時最實用的是在 context 裡設好 `namespace`，就不必每個指令都打 `-n`。合併多份設定用 `KUBECONFIG=~/.kube/config:~/.kube/prod-config kubectl config view --flatten`。

---

## 到這裡，還沒寫的是什麼

誠實收尾——附錄 C 六份之後，仍然沒有逐欄位收錄的東西：

- **`status` 子物件的完整欄位**：唯讀、由控制器維護，逐欄位列出價值低。關鍵的幾個（`observedGeneration`、`conditions`、Pod 狀態機）已散在附錄 C-1 與第 13 章。
- **Windows 節點專屬欄位**：`windowsOptions`、`hostProcess` 等，你的環境用不到。
- **alpha 階段欄位**：變動太快，寫了很快就錯。需要時用 `kubectl explain` 現查。
- **各 Ingress controller 的 annotation 全集**：ingress-nginx 一家就有兩百多個，且版本間會變。查官方 annotation 列表比查筆記可靠。
- **雲端供應商專屬 annotation**：AWS/GCP/Azure 的 LB 設定，屬各雲文件範圍。

---

## 連結

- [[67-scaling-limits]] — 附錄 AS：APF 為何是共用叢集的必備品，而不是進階選項
- [[18-yaml-fields-pod]] — 附錄 C-1：Pod 與 Container 全欄位
- [[19-yaml-fields-workloads]] — 附錄 C-2：Workload 與擴縮全欄位
- [[20-yaml-fields-network-storage]] — 附錄 C-3：網路與儲存全欄位
- [[21-yaml-fields-cluster-security]] — 附錄 C-4：叢集與安全全欄位
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：生態系 CRD 全欄位
- [[24-yaml-fields-istio]] — 附錄 C-7：Istio 全欄位
- [[25-yaml-fields-pipeline]] — 附錄 C-8：GitHub Actions／cloudflared／Compose
- [[26-lab-drills]] — 附錄 D：破壞—診斷—修復實驗手冊
- [[02-cluster-internals]] — 這些元件在做什麼
- [[12-cluster-operations]] — 升級、備份與憑證輪替的實際流程
- [[13-troubleshooting]] — 出事時的分層定位方法
- [[k8s-mastery]] — 教材總目錄
