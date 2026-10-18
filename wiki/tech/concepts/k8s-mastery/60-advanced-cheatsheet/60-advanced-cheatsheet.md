---
type: reference
domain: tech
tags: [kubernetes, k8s, cheatsheet, reference, cli, tools, troubleshooting]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 AL：進階速查表

附錄 B（[[17-cheatsheet]]）是在教材只有 16 章時寫的，涵蓋 kubectl、Docker、Helm、ArgoCD、PromQL、KQL。那些仍然是日常主力。

但後來的 44 份附錄引入了一整批新工具——`trivy`、`cosign`、`istioctl`、`hubble`、`velero`、`kubeconform`、`pluto`、KEDA、Kueue——**它們一個都不在附錄 B 裡**。這一份是補遺。

組織方式是**「你想做什麼」**而不是「這個工具能做什麼」，因為排錯當下你想的是前者。

---

## 升級前的檢查

```powershell
# 誰還在用即將被移除的 API（看真實流量，含不在 git 裡的呼叫者）
kubectl get --raw /metrics | Select-String "apiserver_requested_deprecated_apis"

# 掃描檔案（放進 CI 最有價值）
pluto detect-files -d ./k8s --target-versions k8s=v1.33.0
pluto detect-helm --target-versions k8s=v1.33.0

# 掃描活著的叢集物件
kubent --target-version 1.33

# 轉換舊版 YAML（kubectl convert 是獨立 plugin）
kubectl convert -f old-ingress.yaml --output-version networking.k8s.io/v1

# 升級前的健康檢查（不升級也值得定期跑）
kubeadm upgrade plan
kubeadm certs check-expiration
```

→ [[27-upgrades-and-deprecations]]

---

## YAML 驗證（CI 用）

```powershell
# 1. schema：欄位名、型別、apiVersion 是否存在
kubeconform -strict -summary -kubernetes-version 1.33.0 k8s/

# 2. 最佳實踐：沒設 limits、用 latest、以 root 執行…
kube-linter lint k8s/

# 3. 自訂政策（公司規範）
conftest test k8s/ --policy policies/

# 4. Helm：語法 + 單元測試
helm lint ./charts/my-app
helm unittest ./charts/my-app

# 5. 驗證「渲染後」的結果 —— 最常被忘記的一步
helm template t ./charts/my-app -f ci/values-prod.yaml | kubeconform -strict -
helm template t ./charts/my-app -f ci/values-prod.yaml | kube-linter lint -

# 6. 送進 API Server 驗證但不部署（會回傳補完預設值的完整 YAML）
kubectl apply -f x.yaml --dry-run=server -o yaml
```

→ [[48-testing-in-k8s]]、[[42-helm-chart-design]]

---

## 供應鏈與安全

```powershell
# 映像掃描
trivy image --severity HIGH,CRITICAL harbor.example.com/demo/api:1.0.0

# 原始碼掃描（機密掃描的投報率最高）
trivy fs --scanners vuln,secret,misconfig .

# K8s manifest 的設定檢查
trivy config ./k8s/

# 產生 SBOM（下一個 Log4Shell 來時能在幾分鐘內回答「我們有沒有用到」）
trivy image --format cyclonedx --output sbom.json harbor.example.com/demo/api:1.0.0

# 簽章與驗證
cosign sign harbor.example.com/demo/api@sha256:3f2a9c...
cosign verify --certificate-identity-regexp ".*" --certificate-oidc-issuer-regexp ".*" harbor.example.com/demo/api@sha256:3f2a9c...
```

盤點叢集裡的高風險 Pod：

```powershell
# privileged 容器
kubectl get pods -A -o json | ConvertFrom-Json | ForEach-Object { $_.items } |
  Where-Object { $_.spec.containers.securityContext.privileged -contains $true } |
  ForEach-Object { "$($_.metadata.namespace)/$($_.metadata.name)" }

# 掛了 hostPath 的 Pod
kubectl get pods -A -o json | ConvertFrom-Json | ForEach-Object { $_.items } |
  Where-Object { $_.spec.volumes.hostPath } |
  ForEach-Object { "$($_.metadata.namespace)/$($_.metadata.name)" }

# 這個身分能做什麼（評估被盜用的災情大小）
kubectl auth can-i --list --as=system:serviceaccount:demo:app-sa -n demo
```

事故時的隔離（**不要直接 delete 可疑 Pod**）：

```powershell
kubectl label pod <pod> quarantine=true -n <ns>   # 觸發 quarantine NetworkPolicy
kubectl label pod <pod> app- -n <ns>              # 移出 Service，controller 會補一個健康的
kubectl get pod <pod> -n <ns> -o yaml > evidence-pod.yaml
kubectl logs <pod> -n <ns> --all-containers --previous > evidence-logs.txt
```

→ [[38-security-incident-response]]

---

## 備份與還原

```powershell
# etcd 快照
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F).db `
  --endpoints=https://127.0.0.1:2379 `
  --cacert=/etc/kubernetes/pki/etcd/ca.crt `
  --cert=/etc/kubernetes/pki/etcd/server.crt `
  --key=/etc/kubernetes/pki/etcd/server.key

# 驗證快照沒壞（只要幾秒，一定要做）
etcdutl snapshot status /backup/etcd-2026-08-16.db --write-out=table

# 還原（記得 /etc/kubernetes/pki 也要一起備份與還原）
etcdutl snapshot restore /backup/etcd-2026-08-16.db --data-dir=/var/lib/etcd-restored

# Velero
velero backup create demo-backup --include-namespaces demo --wait
velero backup describe demo-backup --details
velero restore create --from-backup demo-backup --wait

# 還原到旁邊的 namespace 確認資料正確再切換（不要直接蓋回正式）
velero restore create --from-backup demo-backup `
  --namespace-mappings demo:demo-restore
```

→ [[34-multicluster-and-dr]]

---

## 成本盤點

```powershell
# Released 的 PV（PVC 已刪但磁碟還在計費）
kubectl get pv --field-selector=status.phase==Released

# 殘留的已完成 Job
kubectl get jobs -A --field-selector=status.successful=1

# LoadBalancer 型別的 Service（雲端上每個都在計費）
kubectl get svc -A --field-selector=spec.type=LoadBalancer

# 長期 Pending 的 Pod（佔著 quota 不做事）
kubectl get pods -A --field-selector=status.phase=Pending

# 節點的 requests 佔比
kubectl describe nodes | Select-String -Pattern "Allocated resources" -Context 0,6

# VPA 的建議值（updateMode: "Off" 當免費建議引擎）
kubectl describe vpa api-recommender
```

```promql
# 記憶體：P99 實際用量 ÷ requests，低於 0.3 是調整對象
quantile_over_time(0.99, container_memory_working_set_bytes{container!=""}[7d])
/ on(namespace,pod,container) group_left kube_pod_container_resource_requests{resource="memory"}
```

→ [[33-cost-optimization]]

---

## 效能定位

```promql
# ① 先看是整體慢還是尾端慢（三條線放一起）
histogram_quantile(0.50, sum by (le) (rate(http_server_request_duration_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket[5m])))

# ② CPU throttle 比率 —— 「一切正常但就是慢」的頭號嫌疑犯
sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="demo"}[5m]))
/ sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="demo"}[5m]))

# ③ 依 Pod 拆開看延遲 —— 揪出吵鬧鄰居與慢節點
histogram_quantile(0.95, sum by (le, pod) (rate(http_server_request_duration_seconds_bucket[5m])))

# ④ 依路由拆開 —— 是全部慢還是特定端點慢
histogram_quantile(0.95, sum by (le, http_route) (rate(http_server_request_duration_seconds_bucket[5m])))
```

```powershell
# 對照最近的變更（「什麼時候開始的」是最有效率的一問）
kubectl rollout history deployment/api
kubectl get events -A --sort-by=.metadata.creationTimestamp | Select-Object -Last 30

# conntrack 表是否接近滿（症狀是隨機丟包，不對應任何應用層錯誤）
kubectl debug node/<node> -it --image=busybox -- sh -c "cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max"
```

→ [[39-performance-troubleshooting]]

---

## Istio 與 Cilium

```powershell
# Istio：部署前的靜態檢查
istioctl analyze -n demo

# 這個 Pod 被哪些規則影響
istioctl x describe pod <pod> -n demo

# 503 的四種旗標各自看哪裡
istioctl proxy-config route    deploy/istio-ingressgateway -n istio-system   # NR
istioctl proxy-config cluster  deploy/istio-ingressgateway -n istio-system   # NC
istioctl proxy-config endpoint deploy/istio-ingressgateway -n istio-system   # UH
istioctl proxy-config listener deploy/istio-ingressgateway -n istio-system   # TLS

# 設定有沒有真的推下去（STALE 代表你改的還沒生效）
istioctl proxy-status
```

```powershell
# Cilium：整體健康與官方連通性測試套件
cilium status --wait
cilium connectivity test

# Hubble：回答「這個封包為什麼被丟掉」
hubble observe --verdict DROPPED
hubble observe --from-pod demo/api-abc123 --follow
hubble observe --protocol http --to-namespace demo
```

→ [[32-istio-ingress-gateway]]、[[36-ebpf-and-cilium]]

---

## 排程、批次與自動擴縮

```powershell
# 排不進去的原因（訊息幾乎總是直接給答案）
kubectl describe pod <pod> | Select-String -Pattern "FailedScheduling" -Context 0,6

# KEDA：依佇列深度擴縮的狀態
kubectl get scaledobject -A
kubectl describe scaledobject order-consumer -n demo

# Kueue：待准入的工作
kubectl get workloads -A
kubectl describe clusterqueue training-queue

# 手動觸發一次 CronJob（排錯必用）
kubectl create job manual-run-$(Get-Date -Format "MMddHHmm") --from=cronjob/reconcile -n demo

# CronJob 上次排程是什麼時候（偵測「沒跑」）
kubectl get cronjob reconcile -n demo -o jsonpath='{.status.lastScheduleTime}{"\n"}'
```

```promql
# 待排程的 Pod（持續大於 0 就是有東西排不進去）
scheduler_pending_pods

# 「沒跑」的偵測：dead man's switch
time() - batch_job_last_success_timestamp{job="reconcile"} > 26 * 3600
```

→ [[41-advanced-scheduling]]、[[51-background-jobs]]

---

## 訊息、快取與資料庫

```promql
# Kafka consumer lag —— 最重要的一個指標
sum by (consumergroup, topic) (kafka_consumergroup_lag)

# lag 的變化趨勢（告警要對「持續成長」而非絕對值）
deriv(sum(kafka_consumergroup_lag{consumergroup="order-processor"})[10m:])

# Redis 記憶體水位與淘汰速率（命中率降 + 淘汰升 = 記憶體不夠）
redis_memory_used_bytes / redis_memory_max_bytes
rate(redis_evicted_keys_total[5m])

# 快取命中率
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

```powershell
# Redis 現況
kubectl exec -it deploy/redis -- redis-cli INFO memory
kubectl exec -it deploy/redis -- redis-cli INFO stats
kubectl exec -it deploy/redis -- redis-cli CONFIG GET maxmemory-policy
```

→ [[49-messaging-and-events]]、[[50-caching]]、[[57-database-connections]]

---

## 本機開發

```powershell
# 把本機映像直接載進叢集（跳過 registry 這段最不必要的等待）
kind load docker-image my-api:dev
minikube image load my-api:dev

# 自動化 build → 部署 → 檔案同步
skaffold dev

# 遠端除錯：把 Pod 的除錯 port 接到本機
kubectl port-forward deploy/my-api 5005:5005

# distroless 映像沒有 shell 時的唯一排查手段
kubectl debug -it my-api-abc123 --image=busybox:1.36 --target=api

# 直接對節點除錯
kubectl debug node/<node> -it --image=busybox:1.36
```

→ [[54-developer-experience]]

---

## 一頁式：我想做 X

| 我想… | 用 |
| --- | --- |
| 知道升級會不會壞 | `pluto` / `kubent` / `apiserver_requested_deprecated_apis` |
| 在 PR 就擋掉壞 YAML | `kubeconform` + `kube-linter` + `conftest` |
| 知道映像有沒有漏洞 | `trivy image` |
| 知道有沒有把密碼寫進 code | `trivy fs --scanners secret` |
| 回答「我們有沒有用到某個套件」 | SBOM（`trivy --format cyclonedx`） |
| 確認備份能還原 | `etcdutl snapshot status` + `velero restore` 到旁邊的 ns |
| 找出在燒錢的東西 | Released PV / 殘留 Job / LoadBalancer / VPA 建議 |
| 查「服務變慢了」 | P50/95/99 三條線 → **throttle 比率** → 依 Pod 拆開 |
| 查 Istio 的 503 | 日誌旗標（NR/UH/UF/NC）→ 對應的 `proxy-config` |
| 查封包為什麼被丟掉 | `hubble observe --verdict DROPPED` |
| 查 Pod 為什麼排不進去 | `describe` 的 `FailedScheduling` 訊息 |
| 立刻跑一次 CronJob | `kubectl create job --from=cronjob/x` |
| 知道排程有沒有在跑 | dead man's switch（Pushgateway） |
| 除錯 distroless 容器 | `kubectl debug --target=` |
| 評估被盜身分的災情 | `kubectl auth can-i --list --as=` |

---

## 連結

- [[69-third-self-assessment]] — 附錄 AU：查完速查表，用 70 題檢驗自己真的會了
- [[17-cheatsheet]] — 附錄 B：kubectl／Docker／Helm／ArgoCD／PromQL／KQL 的日常速查
- [[46-advanced-self-assessment]] — 附錄 X：這些工具對應的判斷題
- [[59-adoption-roadmap]] — 附錄 AK：什麼階段該引入哪些工具
- [[26-lab-drills]] — 附錄 D：用這些指令實際做一輪
- [[k8s-mastery]] — 教材總目錄
