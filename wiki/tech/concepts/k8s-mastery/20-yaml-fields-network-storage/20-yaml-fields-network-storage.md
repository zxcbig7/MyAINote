---
type: reference
domain: tech
tags: [kubernetes, k8s, yaml, reference, service, ingress, networkpolicy, pv, pvc, storageclass]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 C-3：網路與儲存全欄位

網路與儲存這兩塊放在同一份，是因為它們有一個共同的性格：**欄位少，但每個欄位的影響半徑都很大**。

Deployment 寫錯一個欄位，通常最多影響那個服務自己。Service 的 `externalTrafficPolicy` 寫錯，會讓來源 IP 全部變成 Node IP，你的稽核日誌從此失真；NetworkPolicy 的 selector 空一格，整個 namespace 的流量會被切斷；StorageClass 的 `volumeBindingMode` 選錯，Pod 會在多可用區的叢集裡永遠排不進去。這些都不是「Pod 起不來」那種一眼可見的錯，而是要等到出事才會發現的錯。基準版本 **v1.33**。

---

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
    - name: http
      port: 80
      targetPort: 8080
      protocol: TCP
      appProtocol: http
  sessionAffinity: None
  internalTrafficPolicy: Cluster
  ipFamilyPolicy: SingleStack
```

### 核心欄位

| 欄位 | 型別 | 預設 | 說明 |
| --- | --- | --- | --- |
| `type` | string | `ClusterIP` | 見下表四種 |
| `selector` | map | — | 選中哪些 Pod。**不寫**代表要自己維護 EndpointSlice（外部服務接進叢集的手法） |
| `ports[].port` | int32 | 必填 | Service 自己對外的 port |
| `ports[].targetPort` | IntOrString | 同 `port` | Pod 上的 port，可寫容器的 `ports[].name` |
| `ports[].nodePort` | int32 | 自動分配 | 只對 NodePort/LoadBalancer 有效，範圍預設 30000–32767 |
| `ports[].protocol` | string | `TCP` | `TCP`｜`UDP`｜`SCTP` |
| `ports[].appProtocol` | string | — | 提示上層元件（Ingress controller、service mesh）這是什麼協定 |
| `ports[].name` | string | — | 多 port 時**必填**，且要唯一 |

四種 `type`：

| `type` | 行為 | 用在哪 |
| --- | --- | --- |
| `ClusterIP` | 分配一個叢集內部虛擬 IP | 預設，叢集內互連 |
| `NodePort` | 在**每台** Node 上開同一個 port | 本機測試、沒有 LB 的環境 |
| `LoadBalancer` | 向雲端要一個外部 LB（同時自動包含 NodePort 行為） | 雲端對外服務 |
| `ExternalName` | 只回一筆 CNAME，不做代理 | 把外部 DNS 名包裝成叢集內名稱 |

> ClusterIP 是 iptables/IPVS 規則造出來的虛擬 IP，**沒有任何機器持有它**，所以 `ping` 不通是正常的（第 5 章）。要驗證只能用實際的 port，例如 `curl <svc>:80` 或 `nc -zv`。

### 流量政策與 IP 家族

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `externalTrafficPolicy` | `Cluster` | `Cluster`＝可轉給其他 Node 上的 Pod，負載均勻但**來源 IP 被 SNAT 蓋掉**；`Local`＝只轉給本機 Pod，**保留來源 IP** 但本機沒 Pod 就丟包 |
| `internalTrafficPolicy` | `Cluster` | 同理，但作用於叢集**內部**發起的流量。設 `Local` 可做節點親和（如 DaemonSet 型 agent） |
| `healthCheckNodePort` | 自動 | `externalTrafficPolicy: Local` 時，雲端 LB 用這個 port 判斷該 Node 上有沒有 Pod |
| `sessionAffinity` | `None` | 或 `ClientIP`（同來源 IP 固定打同一個 Pod） |
| `sessionAffinityConfig.clientIP.timeoutSeconds` | `10800` | 黏著時間（3 小時） |
| `ipFamilyPolicy` | `SingleStack` | `SingleStack`｜`PreferDualStack`｜`RequireDualStack` |
| `ipFamilies` | 依叢集 | `[IPv4]`、`[IPv6]` 或兩者，順序決定主要家族 |
| `trafficDistribution` | — | 設 `PreferClose` 讓流量優先走同一 zone，省跨區流量費（1.31+ beta） |
| `publishNotReadyAddresses` | `false` | `true` 時連還沒 Ready 的 Pod 也放進 endpoints；StatefulSet 的 headless Service 常用（成員要在啟動階段就互相看得見） |

`externalTrafficPolicy` 是這張表裡最該記熟的一個。預設 `Cluster` 讓後端拿到的來源 IP 全部是 Node IP，任何依賴來源 IP 的功能（白名單、限流、稽核）都會失效；改成 `Local` 保留真實來源 IP，代價是流量分佈跟 Pod 在 Node 上的分佈綁在一起，副本不均時會傾斜。

### LoadBalancer 專屬

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `loadBalancerClass` | — | 多個 LB 實作並存時指定由誰處理（如 MetalLB） |
| `loadBalancerSourceRanges` | — | CIDR 白名單，由雲端 LB 或防火牆執行 |
| `allocateLoadBalancerNodePorts` | `true` | 設 `false` 可省下 NodePort（LB 直連 Pod IP 時才適用） |
| `loadBalancerIP` | — | **已棄用**，改用各雲端的 annotation |
| `externalIPs` | — | 手動指定由哪些 IP 進來的流量算這個 Service 的 |

### 三種特殊寫法

```yaml
# 1. Headless Service：不分配 ClusterIP，DNS 直接回所有 Pod IP
spec:
  clusterIP: None
  selector:
    app: my-db

# 2. ExternalName：只做 DNS 別名，不經過 kube-proxy
spec:
  type: ExternalName
  externalName: db.example.com

# 3. 無 selector：手動指定後端（把外部服務包裝成叢集內 Service）
spec:
  ports:
    - port: 5432
# 另外自行建立同名的 EndpointSlice
```

---

## EndpointSlice

`Endpoints`（舊版）已被 `EndpointSlice` 取代，後者能分片、承載大量後端。平常由 controller 自動維護，只有「無 selector 的 Service」才需要手寫。

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: my-external-db-1
  labels:
    kubernetes.io/service-name: my-external-db # 必填，靠這個 label 綁 Service
addressType: IPv4 # IPv4 | IPv6 | FQDN
ports:
  - name: postgres
    port: 5432
    protocol: TCP
endpoints:
  - addresses: ["10.0.0.42"]
    conditions:
      ready: true
      serving: true
      terminating: false
    zone: ap-northeast-1a
    nodeName: node-1
```

排錯時最有用的一句話：`kubectl get endpointslice -l kubernetes.io/service-name=<svc>`。Service 連不通時，先看這裡有沒有後端——空的就是 selector 對不上或 Pod 沒 Ready，跟網路一點關係都沒有。

---

## Ingress 與 IngressClass

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  defaultBackend:
    service:
      name: fallback
      port:
        number: 80
  tls:
    - hosts: ["example.com"]
      secretName: example-tls # 型別必須是 kubernetes.io/tls
  rules:
    - host: example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port:
                  number: 80
```

| 欄位 | 說明 |
| --- | --- |
| `ingressClassName` | 指定由哪個 controller 處理。取代舊的 `kubernetes.io/ingress.class` annotation |
| `defaultBackend` | 沒有規則命中時的去處 |
| `tls[].hosts` / `secretName` | 憑證。Secret **必須與 Ingress 在同一個 namespace** |
| `rules[].host` | 支援萬用字元 `*.example.com`（只匹配一層） |
| `pathType` | `Exact`｜`Prefix`（以 `/` 分段比對）｜`ImplementationSpecific`（交給 controller 自己解讀，行為不可攜） |
| `backend.service.port` | `number` 或 `name` 二擇一 |
| `backend.resource` | 指向非 Service 的後端（如 object storage），與 `service` 互斥 |

Ingress 的真相是：**規格本身只定義了很少的東西，真正的能力全在 annotation 裡**，而 annotation 是各 controller 自訂的。重寫路徑、限流、body size、逾時、canary 權重——這些在 ingress-nginx、Traefik、HAProxy 上寫法完全不同，換 controller 幾乎等於重寫。這也是 Gateway API 出現的原因：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
spec:
  parentRefs:
    - name: my-gateway
  hostnames: ["example.com"]
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            add:
              - name: X-Env
                value: prod
      backendRefs:
        - name: api-svc
          port: 80
          weight: 90
        - name: api-svc-canary
          port: 80
          weight: 10
```

Gateway API 把「誰管基礎設施（`GatewayClass`／`Gateway`）」與「誰管路由（`HTTPRoute`）」拆成不同物件、不同角色，並把權重分流、header 改寫這些能力寫進規格本身而不是 annotation。新叢集值得直接評估，但 Ingress 仍是目前多數環境的現況。

`IngressClass` 本身也是一個物件：

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: k8s.io/ingress-nginx
  parameters: # 選填，指向 controller 自訂設定物件
    apiGroup: k8s.example.com
    kind: IngressParameters
    name: external-lb
```

---

## NetworkPolicy

這是全 K8s 最容易寫出「以為有防護、其實沒有」與「以為只擋一點、其實全斷」的物件。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
        - ipBlock:
            cidr: 10.0.0.0/8
            except: ["10.0.5.0/24"]
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector: {} # 整個叢集任何 namespace
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

| 欄位 | 說明 |
| --- | --- |
| `podSelector` | 這條規則**保護誰**。`{}` ＝該 namespace 全部 Pod |
| `policyTypes` | `Ingress`／`Egress`。**沒列到的方向完全不受這條規則管** |
| `ingress[].from` / `egress[].to` | 允許的對象，三種來源：`podSelector`、`namespaceSelector`、`ipBlock` |
| `ports[].port` | 單一 port，可寫名稱 |
| `ports[].endPort` | 配合 `port` 形成範圍 |

四條必須背下來的語意規則：

1. **NetworkPolicy 是純白名單。** 一個 Pod 只要被任何一條 policy 的 `podSelector` 選中，該方向就從「全通」變成「只通列出的」。
2. **多條 policy 是 OR。** 沒有優先序、沒有 deny 規則，結果是所有 policy 允許集合的聯集。
3. **`- podSelector` 與 `- namespaceSelector` 分開兩個項目是 OR，寫在同一個項目裡才是 AND。** 這一個 YAML 縮排差異，是白名單「意外放行整個叢集」的頭號原因：

```yaml
# A：OR —— 任一 namespace 的 frontend，或 monitoring 內的任何 Pod（範圍大得多）
from:
  - podSelector:
      matchLabels: {app: frontend}
  - namespaceSelector:
      matchLabels: {name: monitoring}

# B：AND —— 只有 monitoring namespace 裡、且 label 是 frontend 的 Pod
from:
  - namespaceSelector:
      matchLabels: {name: monitoring}
    podSelector:
      matchLabels: {app: frontend}
```

4. **擋了 egress 就會擋掉 DNS。** 一旦寫下 `policyTypes: [Egress]`，若沒有明確放行 UDP/TCP 53 到 kube-dns，所有網域解析立刻失敗，症狀是應用大量 timeout 而不是「連線被拒」——非常容易誤判成應用問題。

最後一句提醒：**NetworkPolicy 需要 CNI 支援才會生效**。Flannel 預設不支援，套下去不會報錯，只是完全沒作用。minikube 要驗證得換成 Calico 或 Cilium。

---

## PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-data
spec:
  capacity:
    storage: 100Gi
  accessModes: ["ReadWriteOnce"]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  volumeMode: Filesystem
  mountOptions: ["noatime"]
  csi:
    driver: ebs.csi.aws.com
    volumeHandle: vol-0abc123
    fsType: ext4
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: topology.kubernetes.io/zone
              operator: In
              values: [ap-northeast-1a]
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `capacity.storage` | 必填 | 容量 |
| `accessModes` | 必填 | 見下表 |
| `persistentVolumeReclaimPolicy` | 動態供給時由 SC 決定 | `Retain`（保留資料，PV 變 `Released` 需人工處理）｜`Delete`｜`Recycle`（已棄用） |
| `storageClassName` | — | 與 PVC 配對的依據 |
| `volumeMode` | `Filesystem` | 或 `Block`（裸裝置，資料庫偶爾用） |
| `claimRef` | — | 預先綁定給指定 PVC |
| `nodeAffinity` | — | 本地儲存必填，否則 Pod 可能排到拿不到磁碟的 Node |

四種 `accessModes`：

| 模式 | 縮寫 | 語意 |
| --- | --- | --- |
| `ReadWriteOnce` | RWO | 單一 **Node** 可讀寫（同 Node 上多個 Pod 仍可共用） |
| `ReadOnlyMany` | ROX | 多 Node 唯讀 |
| `ReadWriteMany` | RWX | 多 Node 可讀寫，需要 NFS/CephFS 這類支援的後端 |
| `ReadWriteOncePod` | RWOP | 全叢集只有**一個 Pod** 能掛（GA 1.29），真正的互斥保證 |

> RWO 的常見誤解是「只有一個 Pod 能用」。不是——它的邊界是 Node。兩個 Pod 排到同一台 Node 上照樣能同時掛同一個 RWO volume，需要嚴格互斥要用 RWOP。這也解釋了為什麼 Deployment 掛 RWO PVC 做滾動更新時，新 Pod 常卡在 `Multi-Attach error`：新舊 Pod 被排到不同 Node 了。

---

## PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
  volumeMode: Filesystem
  dataSource: # 從快照或既有 PVC 複製
    apiGroup: snapshot.storage.k8s.io
    kind: VolumeSnapshot
    name: db-snapshot-0812
```

| 欄位 | 說明 |
| --- | --- |
| `storageClassName` | 不寫＝用叢集預設 SC；寫 `""`（空字串）＝**明確關閉動態供給**，只綁現成 PV |
| `volumeName` | 直接指定要綁哪個 PV（靜態綁定） |
| `selector` | 用 label 挑 PV，與動態供給互斥 |
| `dataSource` / `dataSourceRef` | 從 VolumeSnapshot 或既有 PVC 複製；`dataSourceRef` 支援跨 namespace 與自訂型別 |
| `volumeAttributesClassName` | 上線後動態調整 IOPS 等參數（1.31+ beta） |

擴容的正確做法是直接改 `resources.requests.storage` 調大（**不能調小**），前提是 SC 有 `allowVolumeExpansion: true`。若檔案系統需要重掛才生效，Pod 重啟一次即可。

PVC 卡在 `Pending` 的三大原因，照這個順序查：沒有預設 StorageClass、SC 的 `volumeBindingMode: WaitForFirstConsumer` 正在等 Pod 被排程（這是正常現象）、或 accessModes 與後端能力不符（要 RWX 但後端只給 RWO）。

---

## StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  encrypted: "true"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
mountOptions: ["noatime"]
allowedTopologies:
  - matchLabelExpressions:
      - key: topology.kubernetes.io/zone
        values: [ap-northeast-1a, ap-northeast-1c]
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `provisioner` | 必填 | CSI driver 名稱；`kubernetes.io/no-provisioner` 代表只做靜態綁定 |
| `parameters` | — | driver 自訂，**值一律是字串**（`iops: "3000"` 不能寫成數字） |
| `reclaimPolicy` | `Delete` | 由它產生的 PV 繼承此值。正式環境資料庫建議 `Retain` |
| `allowVolumeExpansion` | `false` | 沒開就永遠無法擴容，事後改 SC 也**不影響已建立的 PV** |
| `volumeBindingMode` | `Immediate` | `WaitForFirstConsumer` 會等 Pod 排程後才在對的 zone 建磁碟 |
| `allowedTopologies` | — | 限制可建立的區域 |

多可用區叢集一定要用 `WaitForFirstConsumer`。用 `Immediate` 的話，磁碟會先在隨機一個 zone 建好，然後 Pod 因為 `nodeAffinity` 排不到別的 zone，直接卡死在 `Pending`——而且錯誤訊息會指向排程失敗，很難聯想到 SC 設定。

搭配的快照三件套：`VolumeSnapshotClass`（用哪個 driver 拍）、`VolumeSnapshot`（拍一張，指定 `source.persistentVolumeClaimName`）、`VolumeSnapshotContent`（實際的快照物件），需要安裝 snapshot CRD 與 controller 才有。

---

## ConfigMap 與 Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
immutable: false
data:
  LOG_LEVEL: "info"
  app.yaml: |
    server:
      port: 8080
binaryData:
  logo.png: <base64>
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
immutable: true
data:
  password: cGFzc3dvcmQ= # base64
stringData:
  username: admin # 明文寫入，API Server 自動轉成 base64 存進 data
```

| 欄位 | 說明 |
| --- | --- |
| `data` | ConfigMap 是明文、Secret 是 base64。單一物件總大小上限 **1 MiB**（etcd 限制） |
| `binaryData` | ConfigMap 專用，放二進位 |
| `stringData` | Secret 專用，**只寫不讀**：寫進去會被轉成 `data`，`kubectl get -o yaml` 看不到它 |
| `immutable` | 設 `true` 後不可再修改（只能刪除重建），可大幅降低 kubelet 的 watch 負擔。大規模叢集建議開 |

常見 Secret `type`：

| `type` | 用途 | 必要 key |
| --- | --- | --- |
| `Opaque` | 一般用途（預設） | 無 |
| `kubernetes.io/dockerconfigjson` | 私有 registry | `.dockerconfigjson` |
| `kubernetes.io/tls` | Ingress 憑證 | `tls.crt`、`tls.key` |
| `kubernetes.io/basic-auth` | 帳密 | `username`、`password` |
| `kubernetes.io/ssh-auth` | SSH 私鑰 | `ssh-privatekey` |
| `kubernetes.io/service-account-token` | SA 長期 token | 由 controller 填 |

> **base64 不是加密。** `kubectl get secret x -o jsonpath='{.data.password}' | base64 -d` 一行就還原。真正的保護來自 RBAC（誰讀得到）、etcd encryption at rest（落盤加密）、以及不要把 Secret 明文放進 git。第 6、8 章的 Vault + External Secrets Operator 走的就是這條路。
> 另一個常被忽略的：用 `envFrom` 注入的 ConfigMap/Secret **不會熱更新**，改了要重啟 Pod；用 volume 掛載的才會自動更新（約一分鐘內），但用了 `subPath` 就又失效。

---

## 常見誤設十連

| # | 誤設 | 症狀 | 正解 |
| --- | --- | --- | --- |
| 1 | `ping` ClusterIP 不通就以為壞了 | 白查半天 | ClusterIP 是 iptables 虛擬 IP，用 `curl <svc>:<port>` 驗 |
| 2 | Service 有 selector 但沒 endpoints | 502／連線被拒 | `kubectl get endpointslice`，多半是 label 不符或 Pod 沒 Ready |
| 3 | `targetPort` 寫成 Service 的 port | 連得上但無回應 | `targetPort` 是**容器**的 port |
| 4 | 需要來源 IP 卻用預設 `Cluster` | 稽核／白名單全部看到 Node IP | 改 `externalTrafficPolicy: Local` |
| 5 | NetworkPolicy 的 `from` 縮排錯位 | 白名單意外放行全叢集 | 同一項目內才是 AND |
| 6 | 開了 Egress policy 沒放行 DNS | 大量 timeout，像應用壞掉 | 明確允許 UDP 53 到 kube-dns |
| 7 | CNI 不支援卻套 NetworkPolicy | 套下去毫無作用也不報錯 | 確認 CNI（Calico/Cilium） |
| 8 | 多 zone 用 `volumeBindingMode: Immediate` | Pod 永遠 Pending | 改 `WaitForFirstConsumer` |
| 9 | SC 沒開 `allowVolumeExpansion` | 磁碟滿了無法擴容 | 建 SC 時就開，事後改不影響既有 PV |
| 10 | TLS Secret 與 Ingress 不同 namespace | 憑證載不到，退回預設憑證 | 兩者必須同 namespace |

---

## 連結

- [[66-ingress-to-gateway-api]] — 附錄 AR：Ingress 欄位的後繼者與遷移路徑
- [[18-yaml-fields-pod]] — 附錄 C-1：Pod 與 Container 全欄位
- [[19-yaml-fields-workloads]] — 附錄 C-2：Workload 與擴縮全欄位
- [[21-yaml-fields-cluster-security]] — 附錄 C-4：叢集與安全全欄位
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：生態系 CRD 全欄位（含 Gateway API、cert-manager 完整版）
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：冷門內建資源（CSI 家族、Endpoints）與元件設定檔
- [[05-networking]] — 網路四鐵律與完整封包路徑
- [[06-config-and-storage]] — ConfigMap 更新語意與 PV/PVC 三層關係
- [[13-troubleshooting]] — 網路與儲存的分層排查流程
- [[17-cheatsheet]] — 附錄 B：可直接複製的骨架
- [[k8s-mastery]] — 教材總目錄
