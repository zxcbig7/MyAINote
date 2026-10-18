---
type: reference
domain: tech
tags: [kubernetes, k8s, glossary, reference, terminology, index]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 I：術語百科

二十萬字讀下來，最容易發生的不是「沒學過」，而是「學過但想不起來在哪一章」。這一份是整套教材的導航層——約 140 個術語，每條兩三句話說清楚它是什麼、為什麼存在，然後指向該去讀的章節。

用法有兩種。**查詢**：看到不認識的名詞，來這裡找兩句話的解釋，需要細節再點進去。**複習**：從頭掃一遍，看到哪一條說不出所以然，就是知識的破口——這比重讀整章有效率得多。

排序依英文字母。中文名詞放在括號裡，因為實務溝通幾乎都用英文。

---

## A

**Admission Controller**（准入控制器）— API Server 在把物件寫進 etcd 之前的最後一道關卡，分成會改物件的 mutating 與只驗證的 validating 兩類。你 apply 的 YAML 為什麼多了東西，答案通常在這裡。→ [[09-extending-kubernetes]]、[[21-yaml-fields-cluster-security]]

**Affinity / Anti-Affinity**（親和性／反親和性）— 表達「我想跟誰在一起」或「我不想跟誰在一起」的排程規則，分 node 與 pod 兩種、硬性與軟性兩級。反親和性最常見的用途是把副本打散到不同節點。→ [[07-scheduling-and-resources]]

**Aggregation Layer**（API 聚合層）— 讓外部服務把自己的 API 掛進 API Server 的機制，靠 `APIService` 物件註冊。`kubectl top` 就是走這條路。→ [[23-yaml-fields-rare-builtins]]

**Allocatable**（可分配量）— 節點扣掉 `systemReserved`、`kubeReserved` 與驅逐門檻之後，真正能給 Pod 用的資源。**scheduler 看的是這個數字，不是 capacity。** → [[30-production-readiness]]

**Annotation**（註解）— metadata 裡的鍵值對，給人與工具讀，不能被 selector 選中，但可以存大字串。Ingress controller 的能力幾乎全靠它。→ [[03-api-and-yaml]]、[[28-ingress-nginx-annotations]]

**API Group**（API 群組）— 把資源分類的命名空間，如 `apps`、`batch`、`networking.k8s.io`。核心資源（Pod、Service）的群組是空字串 `""`。→ [[03-api-and-yaml]]

**APF（API Priority and Fairness）**— API Server 過載時決定誰先被服務、誰被回 429 的機制，由 `FlowSchema` 與 `PriorityLevelConfiguration` 兩個物件設定。→ [[23-yaml-fields-rare-builtins]]

**ApplicationSet**— ArgoCD 的物件，用一份模板配上 generator 生出多個 Application，解決「同一套服務部署到多環境／多叢集」。→ [[22-yaml-fields-ecosystem]]

**ArgoCD**— GitOps 控制器，持續比對 git 裡的期望狀態與叢集實際狀態並拉平。它是 pull 模型，叢集主動去拉，而不是 CI 推進來。→ [[11-argocd]]

---

## B

**backoffLimit**— Job 容許的失敗次數上限，預設 6，重試間隔採指數退避。用 `podFailurePolicy` 可以讓某些失敗不計入。→ [[19-yaml-fields-workloads]]

**Bin Packing**（裝箱）— 讓 Pod 盡量集中在少數節點以便縮減節點數的排程策略，對應 scheduler 的 `MostAllocated` 評分。與韌性是取捨關係。→ [[23-yaml-fields-rare-builtins]]

---

## C

**cAdvisor**— 內建在 kubelet 裡的容器資源監控元件，Prometheus 的容器層 metric 幾乎都源自它。→ [[14-prometheus-grafana]]

**Canary**（金絲雀）— 讓一小部分流量先走新版本的發布策略。ingress-nginx 用另一條標記 canary 的 Ingress 實作，Istio 與 Gateway API 則用權重欄位。→ [[28-ingress-nginx-annotations]]、[[24-yaml-fields-istio]]

**Capabilities**（能力）— Linux 把 root 的權限拆成的細項（如 `NET_BIND_SERVICE`）。加固的標準做法是 `drop: ["ALL"]` 之後只加回必要的。→ [[08-security-and-rbac]]

**cgroup**（控制群組）— Linux kernel 限制與計量 process 資源用量的機制，是 `resources.limits` 背後的實作。記憶體超限被殺、CPU 超限被限流都由它執行。→ [[00-docker-foundations]]

**ClusterIP**— Service 的預設型別，分配一個叢集內部虛擬 IP。它由 iptables/IPVS 規則造出來，**沒有任何機器持有它，所以 ping 不通是正常的**。→ [[05-networking]]

**ClusterRole**— 叢集範圍的權限定義。搭配 `RoleBinding` 使用時可以「寫一次、綁到多個 namespace」，是最實用的組合。→ [[08-security-and-rbac]]

**CNI（Container Network Interface）**— 容器網路的外掛規格，Calico、Cilium、Flannel 都是實作。NetworkPolicy 能不能生效取決於 CNI 支不支援。→ [[05-networking]]

**ConfigMap**— 存非敏感設定的物件。用 volume 掛整個目錄會自動更新，用 `subPath` 或 `env` 注入則不會——這三種行為的差異是「改了設定沒生效」的標準答案。→ [[06-config-and-storage]]

**containerd**— 目前主流的 container runtime，透過 CRI 與 kubelet 溝通。K8s 1.24 移除 dockershim 之後，多數叢集改用它。→ [[00-docker-foundations]]

**Control Plane**（控制平面）— API Server、etcd、scheduler、controller-manager 的合稱，負責叢集的決策。與負責執行的 worker node 分工。→ [[02-cluster-internals]]

**Controller**（控制器）— 持續比對期望狀態與實際狀態並縮小差距的迴圈。K8s 的一切幾乎都是由某個 controller 維護的。→ [[02-cluster-internals]]

**CoreDNS**— 叢集內的 DNS 服務，把 Service 名稱解析成 ClusterIP。`ndots` 設定造成的多次無效查詢是常見的效能問題。→ [[05-networking]]

**CRD（CustomResourceDefinition）**— 教 API Server 認識新資源型別的物件，是 Operator 模式的地基。在 `apiextensions.k8s.io/v1` 中 schema 是必填的。→ [[09-extending-kubernetes]]、[[21-yaml-fields-cluster-security]]

**CRI（Container Runtime Interface）**— kubelet 與 container runtime 之間的標準介面。dockershim 就是為了讓不支援 CRI 的 Docker Engine 能被 kubelet 使用的轉接層。→ [[00-docker-foundations]]

**CSI（Container Storage Interface）**— 儲存外掛的標準介面。in-tree 的雲端儲存欄位陸續被移除後，一律改走 CSI driver。→ [[06-config-and-storage]]

**CSR（CertificateSigningRequest）**— 向叢集 CA 申請憑證的物件，是替新使用者簽發 kubeconfig 憑證的正規流程。→ [[23-yaml-fields-rare-builtins]]

**Cordon**— 把節點標成不可排程（`spec.unschedulable: true`），但不驅逐既有 Pod。維護的第一步，對應指令 `kubectl cordon`。→ [[12-cluster-operations]]

---

## D

**DaemonSet**— 保證每個（符合條件的）節點都跑一份 Pod 的工作負載，用於日誌收集、監控 agent、網路外掛。沒有 `replicas` 欄位。→ [[04-workloads]]

**Deployment**— 管理無狀態服務的標準工作負載，透過 ReplicaSet 間接管理 Pod，提供滾動更新與回滾。→ [[04-workloads]]

**DNS Policy**— Pod 的 DNS 行為設定。開了 `hostNetwork` 卻沒改成 `ClusterFirstWithHostNet`，叢集內名稱就會解析不到。→ [[18-yaml-fields-pod]]

**Downward API**— 讓容器取得自己的中繼資料（Pod 名稱、Node 名稱、資源上限）的機制，可透過 env 或 volume 注入。把 memory limit 餵給 JVM 參數是經典用法。→ [[06-config-and-storage]]

**DRA（Dynamic Resource Allocation）**— GPU 等特殊裝置的新配置模型，取代舊 device plugin 的「數量」語意，可描述裝置屬性需求。1.33 為 beta。→ [[23-yaml-fields-rare-builtins]]

**Drain**— 驅逐節點上所有 Pod 以便維護，受 PDB 約束。單副本配 `minAvailable: 1` 會讓它永遠卡住。→ [[12-cluster-operations]]、[[26-lab-drills]]

---

## E

**EndpointSlice**— 記錄 Service 後端有哪些 Pod IP 的物件，取代舊的 `Endpoints`。**Service 連不通時的第一個檢查點**。→ [[05-networking]]、[[20-yaml-fields-network-storage]]

**Envoy**— 高效能代理，Istio 的資料平面就是每個 Pod 旁的 Envoy sidecar。它透過 xDS 協定從控制平面取得設定。→ [[istio]]

**Ephemeral Container**（臨時容器）— 用 `kubectl debug` 注入到既有 Pod 的除錯容器，不能寫在 YAML 裡 apply。適合 distroless 映像的除錯。→ [[18-yaml-fields-pod]]

**etcd**— 存放叢集所有狀態的分散式鍵值資料庫。它對磁碟 fsync 延遲極度敏感，也是備份還原的唯一真相來源。→ [[02-cluster-internals]]、[[12-cluster-operations]]

**Eviction**（驅逐）— kubelet 在節點資源不足時主動殺掉 Pod 的行為，順序依 QoS 等級決定。與 API 發起的自願驅逐（drain）是不同機制。→ [[07-scheduling-and-resources]]

---

## F

**Field Manager**— server-side apply 記錄「哪個欄位是誰寫的」的機制，衝突時的仲裁依據，存在 `metadata.managedFields`。→ [[03-api-and-yaml]]

**Finalizer**— 阻止物件被真正刪除的標記，等對應的 controller 完成清理後才移除。namespace 卡在 Terminating 幾乎都是它造成的。→ [[09-extending-kubernetes]]

---

## G

**Gateway API**— Ingress 的後繼規格，把「管基礎設施」與「管路由」拆成不同物件與角色，並把權重分流、header 改寫寫進規格本身而非 annotation。→ [[22-yaml-fields-ecosystem]]

**GitOps**— 以 git 為唯一真相來源、由叢集內的控制器主動拉取並收斂的部署模型。相對於 CI 直接 `kubectl apply` 的 push 模型。→ [[11-argocd]]

**GVK / GVR**— Group-Version-Kind 與 Group-Version-Resource，唯一定位一種資源的座標。`kind: Deployment` 是 Kind，`deployments` 是 Resource。→ [[03-api-and-yaml]]

---

## H

**Headless Service**— 設 `clusterIP: None` 的 Service，DNS 直接回傳所有 Pod IP 而不做負載平衡。StatefulSet 的穩定網路身份靠它。→ [[04-workloads]]

**Helm**— K8s 應用的打包工具，用模板加 values 產生最終 YAML。`include` 與 `template` 的差別、`nindent` 的縮排是最常見的坑。→ [[10-helm]]

**HPA（HorizontalPodAutoscaler）**— 依指標自動增減副本數。`Utilization` 是相對 `requests` 的百分比，所以**沒設 requests 就完全不會動作**。→ [[07-scheduling-and-resources]]、[[19-yaml-fields-workloads]]

**hostNetwork**— 讓 Pod 直接使用節點的網路 namespace，Pod IP 等於 Node IP。方便但放棄了網路隔離，且會佔用節點 port。→ [[18-yaml-fields-pod]]

---

## I

**Image Layer**（映像層）— 容器映像由唯讀層疊成，每個 Dockerfile 指令產生一層。**後面的層刪不掉前面層的檔案**，只能遮蔽——這是敏感資料誤入映像後無法靠 `RUN rm` 移除的原因。→ [[00-docker-foundations]]

**Ingress**— HTTP/HTTPS 層的路由規則物件。規格本身只定義 host、path、backend、TLS，其餘能力全靠 controller 的 annotation。→ [[05-networking]]、[[28-ingress-nginx-annotations]]

**Init Container**— 在主容器之前依序執行、必須成功結束的容器。加上 `restartPolicy: Always` 就變成原生 sidecar。→ [[04-workloads]]

**IPVS**— kube-proxy 的一種模式，用 hash 表取代 iptables 的線性規則鏈，Service 數量大時效能明顯較好。→ [[05-networking]]

**Istio**— service mesh 實作，透過注入 Envoy sidecar 接管流量，提供 mTLS、流量分流、可觀測性而不必改應用程式。→ [[istio]]、[[24-yaml-fields-istio]]

---

## J

**Job**— 跑完就結束的工作負載，用 `completions` 與 `parallelism` 控制數量與並行度。沒設 `ttlSecondsAfterFinished` 會堆積大量已完成的 Pod。→ [[04-workloads]]

**JSONPath**— `kubectl -o jsonpath=` 使用的查詢語法，是精準取出 status 欄位的主要工具。→ [[29-status-and-conditions]]

---

## K

**kubeadm**— 官方的叢集初始化與升級工具，設定檔是 `ClusterConfiguration` 等一組 YAML。→ [[23-yaml-fields-rare-builtins]]、[[27-upgrades-and-deprecations]]

**kubectl**— 操作叢集的 CLI。它與 API Server 的版本差距允許 ±1 個小版本。→ [[17-cheatsheet]]

**kubelet**— 每個節點上的代理程式，負責讓該節點上的 Pod 符合期望狀態、回報狀態、執行 probe 與驅逐。它的設定檔（`KubeletConfiguration`）直接決定節點穩定性。→ [[02-cluster-internals]]

**kube-proxy**— 維護節點上的轉發規則（iptables/IPVS/nftables），讓 ClusterIP 真的能通。→ [[05-networking]]

**kube-scheduler**— 決定 Pod 該去哪個節點的元件，流程是過濾（filter）再評分（score）。→ [[07-scheduling-and-resources]]

**Kustomize**— 以覆蓋（overlay）方式組合 YAML 的工具，內建於 kubectl。`configMapGenerator` 的名稱 hash 能自動觸發滾動更新。→ [[22-yaml-fields-ecosystem]]

---

## L

**Label**（標籤）— 可被 selector 查詢的鍵值對，是 K8s 內部物件互相找到彼此的唯一方式。Service 找 Pod、Deployment 認領 Pod 都靠它。→ [[03-api-and-yaml]]

**Label Selector**— 選取標籤的表達式，支援 `matchLabels` 與 `matchExpressions`。空的 `{}` 代表選中全部，這在 NetworkPolicy 裡是危險的差異。→ [[03-api-and-yaml]]

**Lease**— 分散式選主與節點心跳的載體。kubelet 每 10 秒續約，超時就被標成 `Ready=Unknown`。→ [[23-yaml-fields-rare-builtins]]

**LimitRange**— namespace 內單一物件的資源上下限與**預設值**。它是搭配 ResourceQuota 的必需品，否則開發者忘了寫 requests 就會被拒。→ [[19-yaml-fields-workloads]]

**Liveness Probe**— 失敗會重啟容器的健康檢查。**只該檢查自己**，把下游依賴寫進去會造成連鎖重啟。→ [[04-workloads]]

---

## M

**managedFields**— 記錄各 field manager 擁有哪些欄位的中繼資料，server-side apply 衝突時的證據。→ [[03-api-and-yaml]]

**metrics-server**— 提供 `kubectl top` 與 HPA 所需的即時資源用量。它透過 Aggregation Layer 註冊，掛掉時 HPA 會停止運作。→ [[07-scheduling-and-resources]]

**minikube**— 單機的 K8s 開發環境，這套教材所有實驗的執行場所。→ [[minikube]]、[[26-lab-drills]]

**mTLS**（雙向 TLS）— 雙方都出示憑證的加密連線。Istio 的 `PeerAuthentication` 用它做工作負載之間的身份驗證。→ [[24-yaml-fields-istio]]

**Mutating Webhook**— 會修改送進來的物件的 admission webhook。Istio 的 sidecar 注入就是這類——這解釋了為什麼你 apply 一個容器卻跑出兩個。→ [[09-extending-kubernetes]]

---

## N

**Namespace**— 資源的邏輯隔離範圍。它同時承載 Pod Security Admission 的設定（透過 label），這點常被忽略。→ [[03-api-and-yaml]]、[[21-yaml-fields-cluster-security]]

**ndots**— DNS 解析設定，決定查詢字串要有幾個點才視為絕對名稱。預設 5 會讓外部網域查詢多繞好幾圈。→ [[05-networking]]

**NetworkPolicy**— Pod 層級的流量白名單。純白名單、沒有 deny 規則、多條之間是聯集，且**需要 CNI 支援才生效**。→ [[05-networking]]、[[20-yaml-fields-network-storage]]

**Node**— 執行 Pod 的機器。它的 `conditions` 與 `allocatable` 是排查與容量規劃的核心欄位。→ [[02-cluster-internals]]

**NodePort**— 在每台節點上開同一個 port 對外的 Service 型別，預設範圍 30000–32767。→ [[05-networking]]

---

## O

**OCI（Open Container Initiative）**— 容器映像與 runtime 的標準規格，讓不同工具建出的映像可以互通。→ [[00-docker-foundations]]

**OOMKilled**— 容器超過記憶體 limit 被 cgroup 強制終止，exit code 137。**沒有寬限期，`preStop` 不會執行**。→ [[07-scheduling-and-resources]]、[[29-status-and-conditions]]

**Operator**— 用 CRD 加上自訂 controller 把維運知識程式化的模式，例如自動處理資料庫的備份與主從切換。→ [[09-extending-kubernetes]]

**OutOfSync**— ArgoCD 的同步狀態，代表叢集與 git 有差異。**不等於不健康**——它與 Health 是兩個獨立維度。→ [[11-argocd]]

**OverlayFS**— 容器檔案系統的聯合掛載機制，把唯讀映像層與可寫層疊成一個視圖。→ [[00-docker-foundations]]

**OwnerReference**— 物件之間的從屬關係，父物件被刪時垃圾回收會連帶刪除子物件。Deployment → ReplicaSet → Pod 這條鏈就是靠它。→ [[09-extending-kubernetes]]

---

## P

**pause container**— 每個 Pod 背後隱藏的極簡容器，負責撐開共享的 network namespace。Pod IP 錨定在它身上，所以應用容器重啟 IP 不變。→ [[04-workloads]]

**PDB（PodDisruptionBudget）**— 限制自願性中斷期間最多能有多少 Pod 不可用。對 Node 直接斷電這類非自願中斷無效。→ [[19-yaml-fields-workloads]]

**PV / PVC**— PersistentVolume 是實際的儲存資源，PersistentVolumeClaim 是應用對儲存的申請。兩者綁定後才能被 Pod 掛載。→ [[06-config-and-storage]]

**Pod**— K8s 排程與部署的最小單位，一組共享網路與儲存的容器。**本身沒有自我修復能力**，所以實務上都用 controller 包起來。→ [[04-workloads]]

**Pod Security Admission (PSA)**— 內建的 Pod 安全基線機制，用 namespace label 設定 `privileged`/`baseline`/`restricted` 三級與 `enforce`/`audit`/`warn` 三種模式。取代已移除的 PodSecurityPolicy。→ [[08-security-and-rbac]]

**PriorityClass**— 定義 Pod 優先序與搶佔行為的叢集物件。數字越大越優先，可設 `preemptionPolicy: Never` 只排隊不搶佔。→ [[07-scheduling-and-resources]]

**Preemption**（搶佔）— 高優先序 Pod 排不進去時，驅逐低優先序 Pod 騰出空間的機制。→ [[07-scheduling-and-resources]]

**Projected Volume**— 把 ConfigMap、Secret、Downward API、ServiceAccount token 合併掛在同一個目錄的 volume 型別。短期 SA token 就是靠它輪替。→ [[06-config-and-storage]]

**Prometheus**— pull 模型的監控系統，主動去抓各目標的 `/metrics`。它的查詢語言是 PromQL。→ [[14-prometheus-grafana]]

**PromQL**— Prometheus 的查詢語言。`rate` 與 `irate` 的差別、用 `histogram_quantile` 算 P95 是最常用也最常錯的兩處。→ [[14-prometheus-grafana]]

---

## Q

**QoS Class**（服務品質等級）— 依 requests 與 limits 的關係自動判定的三級：`Guaranteed`（兩者相等）、`Burstable`（有 requests 但不等）、`BestEffort`（都沒設）。節點資源不足時的驅逐順序由它決定。→ [[07-scheduling-and-resources]]

---

## R

**RBAC**— 以 Role/ClusterRole 定義權限、以 RoleBinding/ClusterRoleBinding 綁定主體的授權模型。**純白名單，沒有 deny**，且 `resourceNames` 對 list/watch 無效。→ [[08-security-and-rbac]]

**Readiness Probe**— 失敗會把 Pod 從 Service endpoints 移除但**不重啟**的健康檢查。與 liveness 不同，它可以合理地包含下游依賴。→ [[04-workloads]]

**Reconciliation Loop**（調和迴圈）— 「觀察現狀 → 比對期望 → 採取行動」的無限迴圈，是 K8s 所有 controller 的共同骨架。→ [[02-cluster-internals]]

**ReplicaSet**— 維持指定副本數的 controller，由 Deployment 自動管理。排查滾動更新卡住時要看它。→ [[04-workloads]]

**resourceVersion**— 物件的樂觀鎖版本號，用於衝突偵測與 watch 續接。→ [[03-api-and-yaml]]

**Rollout**— Deployment 的更新過程。`kubectl rollout status/undo/history` 是最常用的三個動詞。→ [[04-workloads]]

**RWO / ROX / RWX / RWOP**— PV 的四種存取模式。RWO 的邊界是**節點**不是 Pod（同節點多個 Pod 仍可共用），真正的互斥要用 RWOP。→ [[20-yaml-fields-network-storage]]

---

## S

**seccomp**— 限制容器可用的系統呼叫。設 `seccompProfile.type: RuntimeDefault` 是成本最低的加固手段。→ [[08-security-and-rbac]]

**Secret**— 存放敏感資料的物件。**base64 不是加密**，真正的保護來自 RBAC、etcd 落盤加密與不把它放進 git。→ [[06-config-and-storage]]

**Server-Side Apply**— 由 API Server 主導欄位合併的 apply 機制，用 field manager 記錄欄位歸屬，取代舊的 `last-applied-configuration` annotation。→ [[03-api-and-yaml]]

**Service**— 給一組 Pod 穩定的虛擬 IP 與 DNS 名稱並做負載平衡。四種型別：ClusterIP、NodePort、LoadBalancer、ExternalName。→ [[05-networking]]

**ServiceAccount**— Pod 的 API 身份。1.24 起不再自動產生長期 token Secret，改用短期的投影 token。→ [[08-security-and-rbac]]

**ServiceMonitor**— Prometheus Operator 的 CRD，宣告要抓哪些 Service 的 metric。它自己的 label 必須符合 Prometheus 的 `serviceMonitorSelector`，這是抓不到資料的頭號原因。→ [[22-yaml-fields-ecosystem]]

**Sidecar**（邊車）— 與主容器共存、提供橫切能力的容器。K8s 1.33 起的正式做法是寫在 `initContainers` 並加 `restartPolicy: Always`。→ [[04-workloads]]、[[18-yaml-fields-pod]]

**StatefulSet**— 提供穩定網路身份、穩定儲存與有序部署三項保證的工作負載，用於資料庫這類有狀態服務。→ [[04-workloads]]

**StorageClass**— 動態供給儲存的樣板，決定 provisioner、回收政策與綁定時機。多可用區必須用 `volumeBindingMode: WaitForFirstConsumer`。→ [[06-config-and-storage]]

**Sync Wave**— ArgoCD 控制部署順序的 annotation，數字小的先部署。DB migration 常設成負數。→ [[11-argocd]]

**systemReserved / kubeReserved**— kubelet 設定，保留給作業系統與 kubelet 自己的資源。沒設等於允許 Pod 把節點吃到失聯。→ [[23-yaml-fields-rare-builtins]]

---

## T

**Taint / Toleration**（汙點／容忍）— Node 用 taint 排斥 Pod，Pod 用 toleration 表示可以接受。三種 effect 中只有 `NoExecute` 會驅逐已在跑的 Pod。→ [[07-scheduling-and-resources]]

**Topology Spread Constraints**— 控制 Pod 在拓撲域（節點、可用區）之間分佈均勻度的排程約束，比 anti-affinity 更精細。→ [[07-scheduling-and-resources]]

**TLS Termination**（TLS 終結）— 在哪一層解密 HTTPS。在 Ingress 終結最常見；`ssl-passthrough` 則是不終結、直接把加密流量丟給後端，代價是失去所有 L7 能力。→ [[28-ingress-nginx-annotations]]

---

## U

**Uncordon**— 解除節點的不可排程標記。drain 中止之後很容易忘記做，導致節點一直沒有新 Pod 進駐。→ [[12-cluster-operations]]

---

## V

**Vault**— HashiCorp 的機密管理系統，透過 TokenReview 驗證 Pod 的 ServiceAccount token 來建立信任鏈。→ [[08-security-and-rbac]]

**Velero**— 工作負載層的備份還原工具，可備份物件定義與 PV 資料。與 etcd 快照互補而非重複。→ [[12-cluster-operations]]

**VirtualService**— Istio 的路由規則物件，決定流量怎麼分。引用的 subset 必須先在 `DestinationRule` 定義，否則 503。→ [[24-yaml-fields-istio]]

**VPA（VerticalPodAutoscaler）**— 自動調整 requests/limits 的 autoscaler。建議先用 `updateMode: "Off"` 只取建議值，且**不能與 HPA 管同一個指標**。→ [[22-yaml-fields-ecosystem]]

---

## W

**WaitForFirstConsumer**— StorageClass 的綁定模式，等到有 Pod 使用時才在正確的拓撲域建立磁碟。多可用區叢集的必要設定。→ [[06-config-and-storage]]

**Webhook**— 見 Admission Controller。`failurePolicy: Fail` 且沒排除 `kube-system` 時，webhook 掛掉會讓整個叢集無法建立 Pod。→ [[09-extending-kubernetes]]

**Workload**（工作負載）— Deployment、StatefulSet、DaemonSet、Job、CronJob 的合稱，也就是管理 Pod 的那一層物件。→ [[04-workloads]]

---

## X

**xDS**— Envoy 從控制平面動態取得設定的一組協定（LDS/RDS/CDS/EDS）。Istio 的 istiod 就是 xDS 伺服器。→ [[istio]]

---

## Y

**YAML anchor**— YAML 的共用片段語法（`&name` 定義、`*name` 引用、`<<:` 合併）。K8s manifest 不常用，但 Docker Compose 與 CI 設定很常見。→ [[25-yaml-fields-pipeline]]

---

## Z

**Zero-downtime Deployment**（零停機部署）— 更新期間服務不中斷。要同時做對四件事：`maxUnavailable: 0`、正確的 readinessProbe、`preStop` 給 kube-proxy 移除端點的時間、以及應用正確處理 SIGTERM。→ [[04-workloads]]、[[26-lab-drills]]

---

## 連結

- [[k8s-mastery]] — 教材總目錄
- [[16-self-assessment]] — 附錄 A：144 題自我檢測
- [[17-cheatsheet]] — 附錄 B：指令與 YAML 骨架速查
- [[18-yaml-fields-pod]] — 附錄 C-1：欄位百科的起點
- [[26-lab-drills]] — 附錄 D：動手實驗
- [[29-status-and-conditions]] — 附錄 G：狀態判讀
- [[30-production-readiness]] — 附錄 H：上線與維運
