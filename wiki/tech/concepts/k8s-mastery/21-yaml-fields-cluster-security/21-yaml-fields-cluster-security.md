---
type: reference
domain: tech
tags: [kubernetes, k8s, yaml, reference, rbac, serviceaccount, crd, webhook, pod-security]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 C-4：叢集與安全全欄位

前三份談的是「應用怎麼寫」。這一份談的是「**誰可以寫、寫進來之後誰有權改它**」——也就是叢集管理員每天真正在維護的那一層。

這層物件的共同特徵是：一般開發者很少碰，但一旦碰了就影響全叢集。RBAC 多給一個 verb，等於多開一扇門；webhook 的 `failurePolicy` 選錯，等於把整座叢集的可用性押在一個 Pod 上；namespace 少一個 label，`restricted` 的安全基線就完全沒生效卻不會有任何錯誤訊息。基準版本 **v1.33**。

---

## Namespace

欄位少到幾乎不用查，但它的 **label** 承載了 Pod Security Admission 的全部設定，這件事極容易被忽略。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.33
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
spec:
  finalizers:
    - kubernetes
```

三種 mode × 三種 level：

| mode | 違反時的行為 |
| --- | --- |
| `enforce` | 直接拒絕建立 Pod |
| `audit` | 允許，但在 audit log 留紀錄 |
| `warn` | 允許，但在 `kubectl` 回一行警告給操作者 |

| level | 意義 |
| --- | --- |
| `privileged` | 完全不限制 |
| `baseline` | 擋掉已知的危險設定（hostNetwork、privileged、hostPath 等） |
| `restricted` | 強制最佳實踐：非 root、`allowPrivilegeEscalation: false`、`drop: ["ALL"]`、`seccompProfile: RuntimeDefault` |

導入的正確順序是 `warn` + `audit` 先跑一段時間、確認沒有既有工作負載會被擋，再切 `enforce`。直接上 `enforce: restricted` 的下場通常是整批 Pod 建不起來，而且錯誤訊息出現在 Deployment 的 event 而不是 Pod（因為 Pod 根本沒被建出來）——這是排查時最容易迷路的地方。

`enforce-version` 建議明確釘住版本而不是用 `latest`，否則叢集升級時安全基線可能悄悄變嚴，讓原本能跑的東西突然被擋。

> namespace 卡在 `Terminating` 刪不掉，答案永遠在 `spec.finalizers` 與底下資源的 `metadata.finalizers`（第 9 章）。查法：`kubectl get namespace <ns> -o jsonpath='{.spec.finalizers}'` 與 `kubectl api-resources --verbs=list --namespaced -o name | xargs -n1 kubectl get -n <ns>`。

---

## ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: prod
automountServiceAccountToken: false
imagePullSecrets:
  - name: harbor-cred
```

| 欄位 | 預設 | 說明 |
| --- | --- | --- |
| `automountServiceAccountToken` | `true` | SA 層級的開關；Pod 層級的同名欄位優先權更高 |
| `imagePullSecrets` | — | 用這個 SA 的 Pod 自動帶上，比每份 Deployment 各寫一次乾淨 |
| `secrets` | — | 舊式長期 token 的關聯，1.24 起不再自動產生 |

token 的演進要記清楚：**1.24 之前**建立 SA 會自動生一個永不過期的 Secret token；**1.24 之後**不再自動產生，Pod 用的是投影進去的短期 token（預設一小時輪替，走 `projected.serviceAccountToken`）。臨時要一張 token 拿去測試就用：

```
kubectl create token app-sa --duration=10m
```

還在用手動建立的長期 token Secret（`type: kubernetes.io/service-account-token`）是明確的技術債——它不會過期、外洩就等於永久後門。

---

## RBAC 四物件

RBAC 只有四種物件，配對規則是一張 2×2：

| | namespace 範圍 | 叢集範圍 |
| --- | --- | --- |
| **權限定義** | `Role` | `ClusterRole` |
| **綁定** | `RoleBinding` | `ClusterRoleBinding` |

三種合法組合：`Role` + `RoleBinding`（單一 namespace）、`ClusterRole` + `ClusterRoleBinding`（全叢集）、`ClusterRole` + `RoleBinding`（**寫一次權限定義，綁到多個 namespace**，最實用的一種）。第四種 `Role` + `ClusterRoleBinding` 不存在。

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-reader
rules:
  - apiGroups: [""] # "" 代表核心組（Pod、Service、ConfigMap…）
    resources: ["pods", "pods/log"] # 子資源要單獨列
    resourceNames: ["my-app"] # 選填，限定特定物件名。注意：對 list/watch 無效
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "patch"]
  - nonResourceURLs: ["/healthz", "/metrics"] # 只能用在 ClusterRole
    verbs: ["get"]
```

| verb | 對應操作 |
| --- | --- |
| `get` / `list` / `watch` | 讀取單一／列表／持續訂閱 |
| `create` / `update` / `patch` / `delete` / `deletecollection` | 寫入類 |
| `impersonate` | 冒用其他使用者身份（極高風險） |
| `escalate` | 建立超出自己權限的 Role（預設連 admin 都沒有） |
| `bind` | 把自己沒有的權限綁給別人 |

`ClusterRole` 還可以用聚合，讓自訂權限自動併進內建角色：

```yaml
aggregationRule:
  clusterRoleSelectors:
    - matchLabels:
        rbac.authorization.k8s.io/aggregate-to-admin: "true"
```

綁定物件：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: prod
subjects:
  - kind: ServiceAccount
    name: app-sa
    namespace: prod # ServiceAccount 必填
  - kind: User
    name: vic@example.com # K8s 沒有 User 物件，名稱來自憑證 CN 或 OIDC claim
    apiGroup: rbac.authorization.k8s.io
  - kind: Group
    name: system:serviceaccounts:dev
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole # Role 或 ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

三個關鍵語意：

1. **`roleRef` 建立後不可修改。** 要換角色只能刪掉重建 binding，這是刻意的防提權設計。
2. **RBAC 是純白名單，沒有 deny。** 多條規則的結果是聯集，你無法「先給全部再扣掉某一項」——要縮小範圍只能重新定義更小的白名單。
3. **`resourceNames` 對 `list` 與 `watch` 無效。** 因為 list 的請求本身不帶物件名，API Server 無從過濾。想限制「只能看某幾個 Pod」，RBAC 做不到，要靠 namespace 切分。

驗證權限永遠用這兩個指令，比讀 YAML 可靠：

```
kubectl auth can-i create deployments --as=system:serviceaccount:prod:app-sa -n prod
kubectl auth can-i --list --as=system:serviceaccount:prod:app-sa -n prod
```

---

## Node 與 Taint

Node 物件多數欄位由 kubelet 回報，管理員實際會改的只有兩處：

```yaml
apiVersion: v1
kind: Node
metadata:
  name: worker-3
  labels:
    node-role.kubernetes.io/worker: ""
    topology.kubernetes.io/zone: ap-northeast-1a
spec:
  unschedulable: true # 等同 kubectl cordon
  taints:
    - key: dedicated
      value: gpu
      effect: NoSchedule
```

| `effect` | 對新 Pod | 對已在跑的 Pod |
| --- | --- | --- |
| `NoSchedule` | 沒容忍就排不進來 | 不影響 |
| `PreferNoSchedule` | 盡量避開，但不保證 | 不影響 |
| `NoExecute` | 沒容忍就排不進來 | **直接驅逐**（除非有 `tolerationSeconds`） |

`status` 裡值得會看的：`conditions`（`Ready`、`MemoryPressure`、`DiskPressure`、`PIDPressure`）、`allocatable`（扣掉系統保留後真正可分配的量，排程看的是這個而不是 `capacity`）、`nodeInfo`（kubelet 與 runtime 版本，升級前盤點用）。

實務上不會手改這個物件，而是用指令：`kubectl cordon`（停止新排程）、`kubectl drain --ignore-daemonsets --delete-emptydir-data`（驅逐現有 Pod，會受 PDB 約束）、`kubectl uncordon`（恢復）。

---

## CustomResourceDefinition

CRD 是「教 K8s 認識新名詞」的方式，也是 Operator 模式的地基。

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backups.ops.example.com # 必須是 <plural>.<group>
spec:
  group: ops.example.com
  scope: Namespaced # 或 Cluster
  names:
    plural: backups
    singular: backup
    kind: Backup
    shortNames: [bk]
    categories: [all] # kubectl get all 會不會列出它
  versions:
    - name: v1
      served: true # 這個版本的 API 端點開不開
      storage: true # 實際存進 etcd 的版本，**只能有一個為 true**
      deprecated: false
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [source]
              properties:
                source:
                  type: string
                schedule:
                  type: string
                  pattern: '^(@(daily|hourly))|([0-9*/, -]+)$'
                retention:
                  type: integer
                  minimum: 1
                  default: 7
      subresources:
        status: {} # 開了才有 /status 端點，controller 才能只更新 status
        scale: # 開了才能 kubectl scale
          specReplicasPath: .spec.replicas
          statusReplicasPath: .status.replicas
      additionalPrinterColumns:
        - name: Source
          type: string
          jsonPath: .spec.source
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
  conversion:
    strategy: None # 或 Webhook（多版本間需要轉換時）
```

幾個實務重點：`schema` 在 `apiextensions.k8s.io/v1` 是**必填**的——沒有 schema 就沒有欄位驗證，使用者打錯欄位名會被靜默接受然後什麼都不發生。`storage: true` 只能有一個版本，改版時要先把新版設為 storage、走一次 storage migration，才能把舊版 `served: false`。`additionalPrinterColumns` 常被忽略，但它決定 `kubectl get backups` 好不好用，值得花五分鐘設好。

---

## Admission Webhook

Webhook 是「你送出去的 YAML 為什麼被改了」的答案（第 9 章）。兩種：`MutatingWebhookConfiguration`（改）與 `ValidatingWebhookConfiguration`（擋），欄位幾乎相同。

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: policy.example.com
webhooks:
  - name: validate.pods.example.com # 必須是 FQDN 格式
    clientConfig:
      service:
        name: policy-webhook
        namespace: policy-system
        path: /validate
        port: 443
      caBundle: <base64 CA> # 或改用 cert-manager 的 annotation 自動注入
    rules:
      - operations: ["CREATE", "UPDATE"] # 也可 DELETE、CONNECT、*
        apiGroups: [""]
        apiVersions: ["v1"]
        resources: ["pods"]
        scope: "Namespaced" # Namespaced | Cluster | *
    failurePolicy: Fail # Fail | Ignore
    matchPolicy: Equivalent # Equivalent（等價 GVK 也算）| Exact
    namespaceSelector:
      matchExpressions:
        - key: kubernetes.io/metadata.name
          operator: NotIn
          values: [kube-system, policy-system]
    objectSelector: {}
    matchConditions: # CEL 表達式再過濾一層，GA 1.30
      - name: skip-system-sa
        expression: "!(request.userInfo.username.startsWith('system:serviceaccount:kube-system:'))"
    sideEffects: None # None | NoneOnDryRun，必填
    timeoutSeconds: 5 # 1–30，預設 10
    admissionReviewVersions: ["v1"]
```

`failurePolicy` 是全表最危險的欄位。設 `Fail` 時，webhook 服務掛掉＝所有符合 rules 的請求全部被拒——如果 rules 涵蓋了 Pod 的 CREATE，這意味著**整座叢集無法再建立任何 Pod，包括 webhook 自己的 Pod**，形成無法自救的死鎖。防呆做法有三個，最好同時用：`namespaceSelector` 排除 `kube-system` 與 webhook 自己所在的 namespace、`timeoutSeconds` 設短（5 秒以內）、webhook 本身多副本並加 PDB。

`MutatingWebhookConfiguration` 多一個 `reinvocationPolicy`（`Never` 預設／`IfNeeded`）：後者表示如果其他 webhook 在你之後又改了物件，你會被再叫一次。Istio 的 sidecar 注入就是這類 webhook——這解釋了為什麼你 apply 的 YAML 只有一個容器，`kubectl get pod -o yaml` 卻長出兩個。

如果只是要做簡單的政策檢查，v1.30 起有不需要跑任何服務的原生做法 `ValidatingAdmissionPolicy`（CEL 寫規則，直接在 API Server 內執行，沒有 webhook 的可用性風險）：

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-resource-limits
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "object.spec.template.spec.containers.all(c, has(c.resources.limits))"
      message: "每個容器都必須設定 resources.limits"
```

再用 `ValidatingAdmissionPolicyBinding` 把它綁到指定 namespace。能用它解決的事就別架 webhook——少一個會掛的元件。（對應的 `MutatingAdmissionPolicy` 在 1.33 仍是 alpha，改寫類需求目前還是得用 webhook。）

---

## RuntimeClass 與其他

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc # CRI 端設定的 handler 名稱
overhead:
  podFixed:
    cpu: 50m
    memory: 64Mi
scheduling:
  nodeSelector:
    sandbox: enabled
  tolerations:
    - key: sandbox
      operator: Exists
      effect: NoSchedule
```

Pod 用 `spec.runtimeClassName: gvisor` 套用。`overhead` 會計入排程與 quota，`scheduling` 則自動把 Pod 導到有該 runtime 的 Node——不用每份 YAML 各寫一次 nodeSelector。

其餘管理員偶爾會碰的：`APIService`（把自訂 API 聚合進 API Server）、`CertificateSigningRequest`（簽發使用者憑證）、`FlowSchema` / `PriorityLevelConfiguration`（API Priority and Fairness，決定 API Server 過載時先服務誰）。這幾個平常不會手寫，出事時才會查——知道它們存在就夠了。

---

## Review 任何一份 YAML 的通用檢查清單

這份清單是附錄 C 四份的收束。拿到任何一份要上線的 YAML，照著跑一遍：

**基本正確性**

- `apiVersion` / `kind` 組合正確，且不是已棄用版本（`kubectl api-resources` 確認）
- `metadata.namespace` 明確寫出（別靠當前 context）
- `selector` 與 `template.metadata.labels` 一致
- image 鎖版本或 digest，沒有 `latest`

**可用性**

- `resources.requests` 與 `limits` 都有寫，記憶體單位是 `Mi`/`Gi`
- 三種 probe 齊備，且 liveness 不檢查下游依賴
- `maxSurge` / `maxUnavailable` 符合這個服務的降載容忍度
- `preStop` + `terminationGracePeriodSeconds` 的總預算算得過來
- 多副本服務有 PDB，且不會讓 drain 卡死

**安全性**

- `runAsNonRoot: true`、`allowPrivilegeEscalation: false`、`readOnlyRootFilesystem: true`、`capabilities.drop: ["ALL"]`
- `automountServiceAccountToken: false`（除非真的要打 API）
- 沒有 `privileged`、`hostNetwork`、`hostPID`、`hostPath`
- Secret 不在 git 明文裡，RBAC 沒有多給 `*`

**可維運性**

- 有標準 labels（`app.kubernetes.io/name`、`version`、`part-of`、`managed-by`）
- Job 有 `ttlSecondsAfterFinished`，CronJob 有 `timeZone`
- 有 ConfigMap/Secret 依賴時，確認更新方式（env 要重啟、volume 才會熱更新）

---

## 連結

- [[18-yaml-fields-pod]] — 附錄 C-1：Pod 與 Container 全欄位
- [[19-yaml-fields-workloads]] — 附錄 C-2：Workload 與擴縮全欄位
- [[20-yaml-fields-network-storage]] — 附錄 C-3：網路與儲存全欄位
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：生態系 CRD 全欄位
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：CSR、APF、Admission binding 與元件設定檔
- [[08-security-and-rbac]] — 三道關卡、RBAC 本質與 Vault 信任鏈
- [[09-extending-kubernetes]] — Webhook、CRD、Finalizer 與 GC 的機制說明
- [[12-cluster-operations]] — Node 維護、憑證輪替、版本升級
- [[17-cheatsheet]] — 附錄 B：可直接複製的骨架
- [[k8s-mastery]] — 教材總目錄
