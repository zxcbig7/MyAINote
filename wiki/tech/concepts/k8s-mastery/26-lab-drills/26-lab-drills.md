---
type: reference
domain: tech
tags: [kubernetes, k8s, lab, minikube, troubleshooting, hands-on, drills]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 D：破壞—診斷—修復實驗手冊

這套教材從第一頁就在講一件事：「親手把它弄壞一次，比讀十遍都有效。」但前面十六章加六份欄位附錄，沒有一處真的告訴你**該怎麼弄壞**。這一份補上。

裡面是 20 個實驗，每一個都對應一種你遲早會在正式環境遇到的故障。設計原則有三條。第一，**故障要真實**——這些不是為了教學而編的情境，而是把第 13 章案例庫與各章「常見誤設」表格裡的東西，還原成可以在 minikube 上重現的最小 YAML。第二，**先診斷再看答案**——每個實驗都給你「你會看到什麼」與「先自己查」的指令，根因與修法收在摺疊區塊裡。忍住不展開，是這份手冊唯一的使用規則。第三，**每個實驗都指回教材**，你卡住的時候知道該回去讀哪一章。

一輪跑完大約需要四到六小時。不必一次做完，但**同一組實驗建議連著做**，因為後面的實驗常會用到前面留下的資源。

---

## 環境準備

```
minikube start --cpus=4 --memory=6g --kubernetes-version=v1.33.0
minikube addons enable metrics-server
minikube addons enable ingress

kubectl create namespace lab
kubectl config set-context --current --namespace=lab
```

全部做完之後清場：`kubectl delete namespace lab`。

有兩個實驗（C4 NetworkPolicy、B2 taint）需要額外條件，各自在該實驗開頭註明。整份手冊的指令都預設你已經把 context 的 namespace 切到 `lab`。

---

## A 組 · 工作負載與生命週期

### A1 · 映像拉不下來

**練的欄位**：`image`、`imagePullPolicy`（附錄 C-1）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a1-bad-image
spec:
  containers:
    - name: app
      image: nginx:1.25-this-tag-does-not-exist
```

**你會看到**：Pod 停在 `ImagePullBackOff` 或 `ErrImagePull`。

**先自己查**：

```
kubectl get pod a1-bad-image
kubectl describe pod a1-bad-image | tail -20
```

<details>
<summary>根因與修法</summary>

`describe` 的 Events 會直接寫出 `Failed to pull image ... not found`。修法是改成存在的 tag。

重點在於**分辨三種相似狀態**：`ErrImagePull` 是第一次拉取失敗，`ImagePullBackOff` 是重試中的退避狀態，而 `CreateContainerConfigError` 完全不是映像問題——那是引用的 ConfigMap/Secret 不存在（見 D3 的變形）。

換成私有 registry 時，同樣的症狀多半是缺 `imagePullSecrets`，Events 會顯示 `unauthorized`。這時要檢查 Secret 的型別是不是 `kubernetes.io/dockerconfigjson`。

</details>

**延伸**：把 image 改成 `nginx`（不寫 tag），用 `kubectl get pod -o yaml | grep imagePullPolicy` 看 K8s 補上的預設值是什麼，對照附錄 C-1 的規則。

---

### A2 · 啟動指令寫錯

**練的欄位**：`command`、`args`（附錄 C-1）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a2-bad-command
spec:
  restartPolicy: Always
  containers:
    - name: app
      image: busybox:1.36
      command: ["echo $HOME && sleep 3600"]
```

**你會看到**：`CrashLoopBackOff`，重啟次數持續增加。

**先自己查**：

```
kubectl logs a2-bad-command
kubectl logs a2-bad-command --previous
kubectl describe pod a2-bad-command | grep -A5 "Last State"
```

<details>
<summary>根因與修法</summary>

`command` 不經過 shell，整個字串被當成**一個執行檔名**，於是 runtime 找不到叫做 `echo $HOME && sleep 3600` 的檔案。

```yaml
command: ["/bin/sh", "-c"]
args: ["echo $HOME && sleep 3600"]
```

順帶記住 `--previous`：CrashLoopBackOff 時當前容器可能還沒產生日誌，你要看的是**上一個**已死容器的輸出。這是排查 crash 最常用的一個旗標。

</details>

---

### A3 · 記憶體被 OOMKill

**練的欄位**：`resources.limits.memory`（附錄 C-1、第 7 章）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a3-oom
spec:
  containers:
    - name: hog
      image: polinux/stress
      command: ["stress"]
      args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "1"]
      resources:
        requests:
          memory: "50Mi"
        limits:
          memory: "100Mi"
```

**你會看到**：容器反覆重啟，`Last State` 顯示 `OOMKilled`，exit code `137`。

**先自己查**：

```
kubectl describe pod a3-oom | grep -A8 "Last State"
kubectl get pod a3-oom -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
```

<details>
<summary>根因與修法</summary>

程式要 200 MB，limit 只給 100 MiB，cgroup 直接殺掉容器。修法是把 limit 調到 `256Mi`。

三個要一起記住的細節：exit code **137 = 128 + 9（SIGKILL）**，這是 OOMKilled 的指紋；OOM 是**沒有寬限期的**，`terminationGracePeriodSeconds` 與 `preStop` 完全不會執行；而記憶體與 CPU 的超限行為完全不同——CPU 超限只會被 throttle 變慢（見 A4），記憶體超限直接死。

</details>

---

### A4 · CPU 被 throttle

**練的欄位**：`resources.limits.cpu`（第 7 章）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a4-throttle
spec:
  containers:
    - name: burner
      image: polinux/stress
      command: ["stress"]
      args: ["--cpu", "2"]
      resources:
        requests:
          cpu: "100m"
        limits:
          cpu: "200m"
```

**你會看到**：Pod 一直是 `Running`，沒有任何錯誤，但實際用量卡在 200m 上不去。

**先自己查**：

```
kubectl top pod a4-throttle
kubectl exec a4-throttle -- cat /sys/fs/cgroup/cpu.stat
```

<details>
<summary>根因與修法</summary>

`cpu.stat` 裡的 `nr_throttled` 與 `throttled_usec` 會持續增加——這就是被限流的直接證據。Pod 健康、probe 正常、日誌乾淨，唯一的症狀是「慢」。

這是正式環境最難查的一類問題：所有 K8s 層的指標都正常，只有應用的 P95 延遲變差。**排查延遲問題時，`container_cpu_cfs_throttled_seconds_total` 應該是你的前三個檢查項目之一**（第 14 章）。

修法是調高 limit，或評估是否該移除 CPU limit（許多團隊只設 requests 不設 CPU limit，用 requests 保證下限、讓尖峰可以借用閒置 CPU）。

</details>

---

### A5 · liveness 把健康的服務殺掉

**練的欄位**：`livenessProbe.timeoutSeconds`、`startupProbe`（附錄 C-1、第 4 章）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a5-probe-kill
spec:
  containers:
    - name: app
      image: nginx:1.25
      livenessProbe:
        exec:
          command: ["/bin/sh", "-c", "sleep 5; exit 0"]
        periodSeconds: 5
        timeoutSeconds: 1
        failureThreshold: 2
```

**你會看到**：Pod 每十幾秒重啟一次，但 nginx 本身完全正常。

**先自己查**：

```
kubectl describe pod a5-probe-kill | grep -A5 Events
kubectl get pod a5-probe-kill -w
```

<details>
<summary>根因與修法</summary>

探測要 5 秒才回應，`timeoutSeconds: 1` 判定逾時，連兩次失敗就重啟。應用完全健康，卻被自己的健康檢查殺掉。

修法是把 `timeoutSeconds` 調到大於實際回應時間。但更重要的是理解**這正是正式環境「服務莫名重啟」的頭號原因**：負載升高 → 回應變慢 → probe 逾時 → 重啟 → 剩餘副本負載更高 → 連鎖重啟。

預防的正確做法有三層：`timeoutSeconds` 要有餘裕、慢啟動用 `startupProbe` 保護而不是拉長 `initialDelaySeconds`、以及 liveness 端點只檢查自己（見 C1 延伸）。

</details>

---

### A6 · 滾動更新掉請求

**練的欄位**：`readinessProbe`、`maxUnavailable`、`preStop`（附錄 C-2、第 4 章）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a6-rollout
spec:
  replicas: 4
  selector:
    matchLabels:
      app: a6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 3 # 刻意設得很糟
  template:
    metadata:
      labels:
        app: a6
    spec:
      containers:
        - name: app
          image: nginx:1.25
          # 刻意不設 readinessProbe
```

建一個 Service 之後，用另一個 Pod 持續打它，同時觸發更新：

```
kubectl expose deployment a6-rollout --port=80
kubectl run curl-loop --image=busybox:1.36 --restart=Never -- \
  /bin/sh -c 'while true; do wget -q -O- -T2 http://a6-rollout || echo FAIL; sleep 0.2; done'
kubectl set image deploy/a6-rollout app=nginx:1.26
kubectl logs -f curl-loop | grep FAIL
```

<details>
<summary>根因與修法</summary>

兩個問題疊在一起。`maxUnavailable: 3` 允許四個副本同時掛掉三個，容量瞬間只剩四分之一；沒有 `readinessProbe` 則讓 K8s 一看到容器啟動就把它加進 Service endpoints，即使應用還沒準備好接受請求。

修法：

```yaml
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
minReadySeconds: 5
```

再加上 `readinessProbe` 與 `preStop` 的 sleep（讓 kube-proxy 有時間把舊 Pod 從轉發表移除）。改完再跑一次同樣的迴圈，`FAIL` 應該歸零——**這個前後對比是整份手冊裡最值得親手做一次的實驗**。

</details>

---

## B 組 · 排程

### B1 · 排不進去：資源不足

**練的欄位**：`resources.requests`（第 7 章）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: b1-too-big
spec:
  containers:
    - name: app
      image: nginx:1.25
      resources:
        requests:
          memory: "100Gi"
```

**先自己查**：

```
kubectl describe pod b1-too-big | grep -A10 Events
kubectl describe node minikube | grep -A8 "Allocated resources"
```

<details>
<summary>根因與修法</summary>

Events 直接寫出 `0/1 nodes are available: 1 Insufficient memory`。

關鍵觀念：scheduler 比對的是 **`requests` 與 Node 的 `allocatable`**，不是 `limits`，也不是 Node 的 `capacity`。`allocatable` = `capacity` 減去 `systemReserved`、`kubeReserved` 與 eviction 門檻（見附錄 C-6 的 KubeletConfiguration）。用 `kubectl describe node` 對照這兩個數字，你會看到它們差了不少——這個差額就是保留給系統的部分。

</details>

---

### B2 · 排不進去：taint 沒容忍

**練的欄位**：`tolerations`、Node `taints`（附錄 C-1）

```
kubectl taint nodes minikube lab=drill:NoSchedule
kubectl run b2-pod --image=nginx:1.25
```

<details>
<summary>根因與修法</summary>

Events 顯示 `1 node(s) had untolerated taint {lab: drill}`。加上容忍即可：

```yaml
tolerations:
  - key: lab
    operator: Equal
    value: drill
    effect: NoSchedule
```

做完把 taint 移除：`kubectl taint nodes minikube lab=drill:NoSchedule-`（結尾的減號是移除）。

進階版：把 effect 換成 `NoExecute` 再套一次，觀察**已經在跑的 Pod 被直接驅逐**——這正是 Node 出現壓力狀況時發生的事，也是 `tolerationSeconds` 存在的理由。

</details>

---

### B3 · PDB 讓維護卡死

**練的欄位**：`minAvailable`、`unhealthyPodEvictionPolicy`（附錄 C-2）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: b3-single
spec:
  replicas: 1
  selector:
    matchLabels:
      app: b3
  template:
    metadata:
      labels:
        app: b3
    spec:
      containers:
        - name: app
          image: nginx:1.25
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: b3-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: b3
```

```
kubectl drain minikube --ignore-daemonsets --delete-emptydir-data --force
```

<details>
<summary>根因與修法</summary>

`drain` 會卡在 `Cannot evict pod as it would violate the disruption budget`，而且**會永遠卡下去**——唯一的副本一旦被驅逐就違反 `minAvailable: 1`，於是驅逐永遠不被允許。

修法有三種：副本數提高到 2 以上、改用 `maxUnavailable: 1`、或單副本服務乾脆不設 PDB。

按 Ctrl+C 中止之後記得 `kubectl uncordon minikube`，否則後面的實驗都排不進去——這個「drain 中止但 Node 還是 cordon 狀態」本身也是常見的維護事故。

</details>

---

## C 組 · 網路

### C1 · Service 沒有後端

**練的欄位**：`selector`、EndpointSlice（附錄 C-3）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: c1-svc
spec:
  selector:
    app: typo-here # 故意打錯，沒有 Pod 有這個 label
  ports:
    - port: 80
      targetPort: 80
```

**先自己查**：

```
kubectl get endpointslice -l kubernetes.io/service-name=c1-svc
kubectl describe svc c1-svc
```

<details>
<summary>根因與修法</summary>

EndpointSlice 是空的。**Service 連不通時，這永遠是第一個要看的地方**：有後端就是網路問題，沒後端就是 selector 或 Pod 健康問題，兩條路徑完全不同。

沒有後端只有兩種可能：selector 對不上任何 Pod，或是 Pod 存在但 `readinessProbe` 沒過（未 Ready 的 Pod 不會進 endpoints）。用 `kubectl get pods --show-labels` 對照 selector 即可分辨。

</details>

**延伸**：把 A5 那個會被 liveness 殺掉的 Pod 加上正確 label，觀察它在重啟循環中如何反覆進出 endpoints——這就是「服務間歇性 502」的成因。

---

### C2 · targetPort 寫錯

**練的欄位**：`port` vs `targetPort`（附錄 C-3）

```
kubectl run c2-pod --image=nginx:1.25 --labels=app=c2
kubectl expose pod c2-pod --port=80 --target-port=8080 --name=c2-svc
kubectl run tester --rm -it --image=busybox:1.36 --restart=Never -- wget -q -O- -T3 http://c2-svc
```

<details>
<summary>根因與修法</summary>

連線被拒或逾時。EndpointSlice **有後端**（所以不是 C1 那種問題），但 nginx 聽在 80、Service 卻把流量轉到 8080。

記憶法：`port` 是「Service 對外開的門」，`targetPort` 是「容器實際聽的門」。改用容器 port 的**名稱**當 `targetPort` 可以完全避免這類錯誤，因為名稱對不上時 K8s 會直接告訴你。

</details>

---

### C3 · DNS 短名與 ndots

**練的欄位**：`dnsConfig`、`ndots`（附錄 C-1、第 5 章）

```
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -- /bin/sh
# 在容器內：
cat /etc/resolv.conf
nslookup c2-svc
nslookup c2-svc.lab.svc.cluster.local
nslookup google.com
```

<details>
<summary>根因與修法</summary>

`/etc/resolv.conf` 裡的 `options ndots:5` 意思是：查詢字串裡的點少於 5 個時，先逐一嘗試 `search` 清單裡的後綴，全部失敗才查絕對名稱。

`google.com` 只有一個點，所以會先依序查 `google.com.lab.svc.cluster.local`、`google.com.svc.cluster.local`、`google.com.cluster.local`……全部 NXDOMAIN 之後才查到真正的 `google.com`。**一次外部查詢變成四到五次 DNS 往返**，在高流量服務上這是實質的延遲與 CoreDNS 負載來源。

兩種修法：外部網域結尾加點（`google.com.`）走絕對查詢，或在 Pod 設 `dnsConfig.options` 把 `ndots` 調成 2。

</details>

---

### C4 · NetworkPolicy 切斷 DNS

**練的欄位**：`policyTypes`、`egress`（附錄 C-3）

> 需要支援 NetworkPolicy 的 CNI。minikube 用 `minikube start --cni=calico` 重建叢集，否則規則套下去完全沒作用（這本身也是一個值得知道的坑）。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: c4-deny-egress
spec:
  podSelector:
    matchLabels:
      app: c4
  policyTypes: [Egress]
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: some-backend
```

```
kubectl run c4-pod --image=busybox:1.36 --labels=app=c4 --restart=Never -- sleep 3600
kubectl exec c4-pod -- nslookup kubernetes.default
```

<details>
<summary>根因與修法</summary>

DNS 查詢逾時。一旦寫下 `policyTypes: [Egress]`，該 Pod 的出站就從「全通」變成「只通列出的」，而清單裡沒有 kube-dns。

症狀的欺騙性在於：應用看到的是**大量 timeout**，不是「連線被拒」，非常容易誤判成下游服務掛了或應用有 bug。

修法是任何 egress policy 都必須明確放行 DNS：

```yaml
egress:
  - to:
      - namespaceSelector: {}
        podSelector:
          matchLabels:
            k8s-app: kube-dns
    ports:
      - protocol: UDP
        port: 53
      - protocol: TCP
        port: 53
```

</details>

**延伸**：把兩個 `- podSelector` / `- namespaceSelector` 從分開兩項改成同一項（OR 變 AND），用 `kubectl exec` 驗證放行範圍如何劇烈縮小。這個縮排差異是白名單意外放行整個叢集的頭號原因（附錄 C-3）。

---

### C5 · Ingress 的 pathType

**練的欄位**：`pathType`、`ingressClassName`（附錄 C-3）

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: c5-ing
spec:
  ingressClassName: nginx
  rules:
    - host: lab.local
      http:
        paths:
          - path: /api
            pathType: Exact # 換成 Prefix 再測一次
            backend:
              service:
                name: c2-svc
                port:
                  number: 80
```

```
minikube ip
curl -H "Host: lab.local" http://$(minikube ip)/api
curl -H "Host: lab.local" http://$(minikube ip)/api/users
```

<details>
<summary>根因與修法</summary>

`Exact` 時 `/api` 通、`/api/users` 回 404；改成 `Prefix` 之後兩者都通。

`Prefix` 是**以 `/` 分段**比對，不是字串前綴——所以 `/api` 這條 Prefix 規則會命中 `/api/users`，但不會命中 `/apifoo`。這個細節在拆分微服務路由時很重要。

順帶驗證另一件事：把 `ingressClassName` 拿掉，觀察 Ingress 的 `ADDRESS` 欄位一直空著——沒有 controller 認領它，規則等於沒寫，而且**不會有任何錯誤訊息**。

</details>

---

## D 組 · 設定與儲存

### D1 · ConfigMap 改了沒生效

**練的欄位**：`subPath`、volume vs env（附錄 C-1、第 6 章）

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: d1-cm
data:
  app.conf: "version=1"
---
apiVersion: v1
kind: Pod
metadata:
  name: d1-pod
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["/bin/sh", "-c", "while true; do cat /cfg-dir/app.conf; cat /cfg-file/app.conf; sleep 10; done"]
      volumeMounts:
        - name: cfg
          mountPath: /cfg-dir # 掛整個目錄
        - name: cfg
          mountPath: /cfg-file/app.conf
          subPath: app.conf # 掛單一檔案
  volumes:
    - name: cfg
      configMap:
        name: d1-cm
```

```
kubectl patch configmap d1-cm --type merge -p '{"data":{"app.conf":"version=2"}}'
kubectl logs -f d1-pod
```

<details>
<summary>根因與修法</summary>

大約一分鐘後，`/cfg-dir/app.conf` 變成 `version=2`，而 `/cfg-file/app.conf` **永遠停在 `version=1`**。

原因是 kubelet 靠 symlink 原子替換整個目錄來更新 ConfigMap volume，而 `subPath` 掛的是掛載當下那個 inode 的快照，不參與後續替換。

修法是掛整個目錄、讓應用讀目錄下的檔案。若非用 `subPath` 不可（例如要注入到 `/etc/nginx/conf.d/` 這種已有其他檔案的目錄），就必須接受「改設定要重啟 Pod」，並用 checksum annotation 自動觸發滾動更新：

```yaml
template:
  metadata:
    annotations:
      checksum/config: '{{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}'
```

</details>

---

### D2 · env 注入的設定不會更新

**練的欄位**：`envFrom`（附錄 C-1）

沿用 D1 的 ConfigMap，另建一個用 `envFrom` 注入的 Pod，改完 ConfigMap 後用 `kubectl exec <pod> -- env | grep app` 觀察。

<details>
<summary>根因與修法</summary>

環境變數在容器啟動時就固定了，**不論等多久都不會變**。這是 K8s 的設計，不是 bug。

因此「ConfigMap 能不能熱更新」的完整答案是三層的：volume 掛目錄 → 會（約一分鐘內）；volume 掛 `subPath` → 不會；`env` / `envFrom` → 不會。

把這三層記牢，「改了設定沒生效」這類問題你可以在三十秒內定位。

</details>

---

### D3 · PVC 卡在 Pending

**練的欄位**：`storageClassName`、`volumeBindingMode`（附錄 C-3）

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: d3-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: fast-ssd-typo # 不存在的 SC
  resources:
    requests:
      storage: 1Gi
```

**先自己查**：

```
kubectl describe pvc d3-pvc | grep -A6 Events
kubectl get storageclass
```

<details>
<summary>根因與修法</summary>

Events 顯示找不到對應的 StorageClass。改成 minikube 的 `standard` 即可綁定。

但更值得練的是**另一種 Pending 是正常的**：把 `storageClassName` 改成一個 `volumeBindingMode: WaitForFirstConsumer` 的 SC，PVC 會停在 Pending 直到有 Pod 使用它——這不是故障。

分辨方法看 Events：`waiting for first consumer to be created` 是正常等待，`no persistent volumes available` 或找不到 SC 才是真的有問題。誤把前者當故障去查，是很常見的時間浪費。

</details>

---

## E 組 · 安全與平台

### E1 · Pod Security Admission 擋下部署

**練的欄位**：PSA namespace labels（附錄 C-4）

```
kubectl label namespace lab \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted

kubectl run e1-pod --image=nginx:1.25
```

<details>
<summary>根因與修法</summary>

Pod 直接被拒絕，訊息列出所有違反項目：`allowPrivilegeEscalation != false`、`unrestricted capabilities`、`runAsNonRoot != true`、`seccompProfile`。

修法就是附錄 C-1 那份加固基線。注意 nginx 官方映像預設以 root 啟動並綁 80 port，在 `restricted` 下需要改用 `nginxinc/nginx-unprivileged` 這類非 root 映像——**這正是導入 PSA 時最真實的阻力：不是設定寫不出來，而是既有映像不符合**。

最重要的實務教訓在下一步：把它包成 Deployment 再套一次。你會發現 `kubectl get pods` 什麼都沒有，錯誤訊息藏在 **Deployment 的 event 與 ReplicaSet 的 condition** 裡，因為 Pod 根本沒被建出來。查 `kubectl describe rs` 才看得到真相。

做完記得移除 label：`kubectl label namespace lab pod-security.kubernetes.io/enforce- pod-security.kubernetes.io/warn-`

</details>

---

### E2 · RBAC 403

**練的欄位**：Role / RoleBinding / `auth can-i`（附錄 C-4）

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: e2-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: e2-role
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: e2-rb
subjects:
  - kind: ServiceAccount
    name: e2-sa
    namespace: lab
roleRef:
  kind: Role
  name: e2-role
  apiGroup: rbac.authorization.k8s.io
```

```
kubectl auth can-i list pods --as=system:serviceaccount:lab:e2-sa -n lab
kubectl auth can-i create deployments --as=system:serviceaccount:lab:e2-sa -n lab
kubectl auth can-i list pods --as=system:serviceaccount:lab:e2-sa -n kube-system
kubectl auth can-i --list --as=system:serviceaccount:lab:e2-sa -n lab
```

<details>
<summary>根因與修法</summary>

四個答案依序是 yes / no / no / 完整清單。

`--as` 是排查權限問題最快的工具，比讀 YAML 推理可靠得多。第三個查詢的 no 展示了 RoleBinding 的邊界：權限只在 binding 所在的 namespace 有效。

再練一個 RBAC 的重要限制：在 Role 加上 `resourceNames: ["e2-pod"]`，然後分別測 `get` 與 `list`。你會發現 `get` 被正確限制、`list` 卻完全不受影響——因為 list 請求本身不帶物件名，API Server 無從過濾。「只能看某幾個 Pod」這個需求，RBAC 做不到。

</details>

---

### E3 · Namespace 卡在 Terminating

**練的欄位**：`finalizers`（附錄 C-1、第 9 章）

```
kubectl create namespace e3-stuck
kubectl -n e3-stuck create configmap victim --from-literal=a=b
kubectl -n e3-stuck patch configmap victim -p '{"metadata":{"finalizers":["lab.example.com/never-removed"]}}'
kubectl delete namespace e3-stuck --timeout=30s
```

<details>
<summary>根因與修法</summary>

namespace 停在 `Terminating`。原因是它底下的 ConfigMap 有一個 finalizer，而沒有任何 controller 會來移除它——namespace 必須等所有資源真正消失才能結束刪除。

正確的診斷順序：先 `kubectl get namespace e3-stuck -o jsonpath='{.status.conditions}'` 看它在等什麼，再逐一列出殘留資源。

修法是移除卡住的 finalizer：

```
kubectl -n e3-stuck patch configmap victim -p '{"metadata":{"finalizers":null}}'
```

**不要**直接去改 namespace 自己的 `spec.finalizers`（網路上很多文章教你用 `/finalize` 端點強制清掉）。那會讓底下的資源變成沒人清理的孤兒，尤其當 finalizer 屬於真正的 controller（例如 ArgoCD 的 `resources-finalizer`）時，強制清除等於跳過了「先刪掉它部署的所有資源」這個步驟。

</details>

---

## 做完之後

清場：

```
kubectl delete namespace lab e3-stuck --ignore-not-found
kubectl uncordon minikube
kubectl taint nodes minikube lab=drill:NoSchedule- 2>/dev/null || true
```

自我檢查——下面每一題你都應該能不查資料回答。答不出來的，回去重做對應的實驗，而不是重讀那一章：

| # | 問題 | 對應實驗 |
| --- | --- | --- |
| 1 | exit code 137 代表什麼？OOM 時 `preStop` 會執行嗎？ | A3 |
| 2 | 應用完全健康卻一直重啟，第一個懷疑對象是什麼？ | A5 |
| 3 | Pod 一直 Running 但服務很慢，怎麼證明是被 throttle？ | A4 |
| 4 | Service 連不通，第一個指令下什麼？ | C1 |
| 5 | 為什麼加了 egress policy 之後應用開始大量 timeout？ | C4 |
| 6 | ConfigMap 熱更新的三種行為分別是什麼？ | D1、D2 |
| 7 | PVC Pending 什麼時候是正常的？ | D3 |
| 8 | 為什麼 `kubectl get pods` 看不到被 PSA 擋掉的 Pod？ | E1 |
| 9 | RBAC 為什麼無法限制「只能 list 某幾個 Pod」？ | E2 |
| 10 | namespace 卡 Terminating，為什麼不該直接清 namespace 的 finalizer？ | E3 |

答得出十題裡的八題，你已經超過多數「會用 K8s」的人。剩下的差距不在知識，而在你有沒有在**正式環境**處理過同樣的事——那部分只能靠時間，但至少你不會是第一次見到這些症狀。

---

## 連結

- [[69-third-self-assessment]] — 附錄 AU：第三份自我檢測，答錯的回來做對應實驗
- [[16-self-assessment]] — 附錄 A：144 題自我檢測題庫（理論側的驗收）
- [[17-cheatsheet]] — 附錄 B：速查表，實驗時第二螢幕開著
- [[18-yaml-fields-pod]] — 附錄 C-1：實驗裡出現的每個 Pod 欄位
- [[13-troubleshooting]] — 分層定位方法論與 19 個真實案例
- [[minikube]] — 本機環境設定
- [[k8s-mastery]] — 教材總目錄
