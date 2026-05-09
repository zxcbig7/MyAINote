---
type: entity
domain: tech
tags: [istio, service-mesh, envoy, sidecar, kubernetes, networking]
sources: []
created: 2026-05-07
updated: 2026-05-07
---

# Istio

Kubernetes 上的 service mesh 平台，以 sidecar 模式在每個 Pod 旁掛載 Envoy proxy，統一處理流量路由、mTLS、可觀測性。

## 名詞解釋

| 名詞 | 說明 |
|------|------|
| **Service Mesh** | 在微服務之間加一層基礎設施層，統一處理服務間通訊（加密、重試、限流、tracing），應用程式本身不需改動 |
| **Sidecar** | 與 main container 共存於同一 Pod 的輔助容器，共享網路與儲存 namespace |
| **Envoy** | CNCF 開源的高效能 L7 proxy，Istio data plane 的核心元件 |
| **istiod** | Istio control plane，整合 Pilot（xDS server）、Citadel（憑證管理）、Galley（設定驗證） |
| **xDS** | Envoy 的動態設定協議族（LDS/RDS/CDS/EDS），istiod 透過它推送路由規則給所有 sidecar |
| **mTLS** | Mutual TLS，雙向驗證，Istio 預設在 mesh 內所有服務間啟用 |
| **iptables NAT** | Linux 核心的網路封包轉發規則，`istio-init` 用它把所有流量攔截進 Envoy |
| **pilot-agent** | istio-proxy container 內的管理程式，負責啟動 Envoy、監控健康狀態、接收 `/quitquitquit` 指令 |
| **VirtualService** | Istio CRD，定義流量路由規則（版本切分、重試、timeout） |
| **DestinationRule** | Istio CRD，定義 upstream 連線策略（load balancing、circuit breaker、mTLS 模式） |
| **PeerAuthentication** | Istio CRD，控制 mTLS 模式（STRICT / PERMISSIVE / DISABLE） |
| **IPv6** | IP 位址第六版，格式為 `2001:db8::1`；現代叢集為應對 IPv4 位址不足開始採用 |
| **Dual-Stack** | 叢集同時支援 IPv4 + IPv6，每個 Pod 同時拿到兩種位址；「誰優先」決定 kubelet probe 用哪個 address family |
| **Sidecar Ready** | istio-proxy（Envoy）通過 `15021/healthz/ready` 回 200 的狀態；未達到前 Pod 不收流量、`pilot-agent wait` 不解除 |
| **Dual-Stack Sidecar** | Envoy sidecar 同時監聽 IPv4（`0.0.0.0`）和 IPv6（`[::]`）的模式；啟用後不論 kubelet 用哪個 address family 打 probe 都能回應 |

## 架構概覽

```
Control Plane：istiod（Pilot + Citadel + Galley）
Data Plane：每個 Pod 內的 Envoy sidecar（istio-proxy）
```

istiod 透過 **xDS protocol** 動態推送設定給所有 Envoy。

---

## Sidecar 注入方式

| 方式 | 說明 |
|------|------|
| Automatic injection | namespace 加 `istio-injection: enabled` label，Webhook 自動注入 |
| Manual injection | `istioctl kube-inject -f pod.yaml` |

注入後 Pod 會多出兩個容器：
- `istio-init`（init container）— 寫 iptables 規則
- `istio-proxy`（sidecar container）— 執行 Envoy

---

## 流量攔截機制

`istio-init` 在 Pod network namespace 寫入 iptables NAT rules：

```
所有 outbound traffic → REDIRECT → 127.0.0.1:15001（Envoy outbound listener）
所有 inbound traffic  → REDIRECT → 127.0.0.1:15006（Envoy inbound listener）
```

App、Envoy、`istio-init` 三者**共用同一個 Pod network namespace**，所以 iptables 規則對所有容器同時生效。

---

## 重要 Port 清單

| Port | 用途 |
|------|------|
| 15000 | Envoy admin（config dump、stats） |
| 15001 | Envoy outbound listener（iptables 導向處） |
| 15006 | Envoy inbound listener |
| 15020 | pilot-agent（`/quitquitquit`、merged metrics） |
| 15021 | Envoy readiness 健康檢查（K8s readiness probe + `pilot-agent wait`） |
| 15012 | istiod xDS over mTLS |
| 15014 | istiod monitoring |

---

## Pod 啟動順序與 Race Condition

K8s 保證 init containers **序列**完成後才啟動一般 containers，但一般 containers 是**並行**啟動，不保證誰先 ready。

**Race condition 空窗**：

```
istio-init 完成 → iptables 規則立即生效
                ↓
App container 與 istio-proxy 並行啟動
                ↓
App 發出第一個 outbound 請求
iptables 攔截 → 轉到 127.0.0.1:15001
Envoy 尚未 bind port → kernel 回 ECONNREFUSED
```

---

## 解法一：holdApplicationUntilProxyStarts（postStart hook）

在 `istio-proxy` container 上設 `postStart` hook，執行 `pilot-agent wait`。

kubelet 語意：**postStart 完成前不會啟動下一個 container**（實際上是不會送 STARTED 事件，但 containers 仍並行啟動；效果是 main container 的 postStart 等 sidecar ready）。

啟用方式（IstioOperator）：

```yaml
meshConfig:
  defaultConfig:
    holdApplicationUntilProxyStarts: true
```

`pilot-agent wait` 會輪詢 `127.0.0.1:15021/healthz/ready` 直到 Envoy ready，default timeout 60 秒。

---

## 解法二：K8s 1.28+ Native Sidecar

K8s 1.28 新增 `SidecarContainers` feature gate，讓 init container 可設 `restartPolicy: Always`，變成 long-running sidecar。

```yaml
initContainers:
  - name: istio-proxy
    restartPolicy: Always   # 這行讓它成為 native sidecar
    ...
```

**保證語意**：kubelet 確保該 init container readinessProbe 通過後，才啟動後續 containers。

Istio 啟用方式：

```bash
istioctl install --set values.pilot.env.ENABLE_NATIVE_SIDECARS=true
```

Native sidecar 同時解決了 **Job/CronJob 終止問題**（見下節）。

---

## Job / CronJob 終止問題

Envoy 是 long-running process。Job main container 結束後，Envoy 繼續存活 → Pod 永遠停在 `Running`，Job 永不 Complete。

**解法：main 結束前通知 sidecar 退出**

```bash
#!/bin/bash
trap 'curl -sS -X POST http://localhost:15020/quitquitquit' EXIT

# ... 主要工作 ...
```

`trap ... EXIT` 確保不管正常結束還是錯誤，都會呼叫 `/quitquitquit`。

---

## pilot-agent wait 失敗根因樹

| Exit Code | 意義 |
|-----------|------|
| 255 | `pilot-agent wait` 自身 timeout（default 60 秒），Envoy 始終未 ready |
| 137 | 被 SIGKILL（OOM 或 postStart hook 整體 timeout） |

**Envoy ready 不了的五大根因**：

1. **NetworkPolicy 擋 egress** — Envoy 連不到 istiod 15012 取不到 xDS 設定
2. **istiod 不可達** — control plane 本身問題
3. **Cloud metadata server 被擋** — cert provisioning 失敗（mTLS 憑證拿不到）
4. **Sidecar OOM** — memory limit 過低
5. **60 秒 timeout 不夠** — 網路慢或 istiod 負載高，可調整 `PILOT_PROXY_CONVERGENCE_TIMEOUT`

---

## NetworkPolicy 與 Sidecar 相容性

有 NetworkPolicy 的 namespace，Envoy 至少需要以下 egress 才能 ready：

| 目標 | Port | 用途 |
|------|------|------|
| istiod | 15012 TCP | xDS 設定拉取 |
| istiod | 15014 TCP | monitoring |
| kube-dns | 53 UDP/TCP | DNS 解析 |

**少一條 egress → sidecar ready 不了 → pilot-agent wait timeout。**

---

## 攔截規則的逃生門

有些服務（Vault、cloud metadata server）需要在 Envoy ready 前就連到，可以排除出 iptables 攔截範圍：

```yaml
# Pod annotation（per-pod）
traffic.sidecar.istio.io/excludeOutboundIPRanges: "169.254.169.254/32,10.0.0.5/32"

# MeshConfig（全域）
meshConfig:
  defaultConfig:
    proxyMetadata:
      ISTIO_META_DNS_CAPTURE: "false"
```

**代價**：排除的流量繞過 mesh，**無 mTLS、無 observability**。

---

## xDS 與 Control Plane

xDS 是 Envoy 的 dynamic configuration protocol，包含四種 API：

| API | 全名 | 用途 |
|-----|------|------|
| LDS | Listener Discovery Service | Envoy listener 設定 |
| RDS | Route Discovery Service | HTTP 路由規則 |
| CDS | Cluster Discovery Service | upstream cluster 定義 |
| EDS | Endpoint Discovery Service | cluster 成員 IP:port |

istiod 作為 xDS server，Envoy 啟動後連到 istiod **15012（mTLS）**，訂閱上述四種 API。xDS 設定推送完成 + cert provisioning 完成 → Envoy ready。

---

## 偵錯方法論

**1. 確認錯誤類型**

```bash
kubectl describe pod <pod> -n <ns>
# 找 Events 欄位的 FailedPostStartHook
```

**2. 看 sidecar 上次 crash 原因**

```bash
kubectl logs <pod> -c istio-proxy --previous -n <ns>
```

**3. 手動確認 Envoy 狀態**

```bash
# 在 Pod 內執行
curl http://localhost:15021/healthz/ready   # Envoy readiness
curl http://localhost:15000/config_dump     # Envoy 完整設定
curl http://localhost:15000/stats           # Envoy metrics
```

**4. 測試 sidecar 到 control plane 連線**

```bash
kubectl exec <pod> -c istio-proxy -- nc -zv istiod.istio-system 15012
```

**5. 確認 NetworkPolicy**

```bash
kubectl get networkpolicy -n <ns>
# 確認有 egress 到 istiod namespace 15012/15014 和 kube-dns 53
```

---

## Sidecar 完整生命週期

```
Pod 建立
  → istio-init 寫 iptables（inbound 15006、outbound 15001）
  → istio-proxy 與 app 並行啟動
    → Envoy 連 istiod:15012 取 xDS 設定
    → cert provisioning（mTLS 憑證）
    → Envoy bind 15001/15006/15021
    → /healthz/ready 回 200 → pilot-agent wait 解除
  → app 開始正常收發流量（流量走 Envoy）

Pod 終止
  → preStop：app 收到 SIGTERM 前有機會做 graceful shutdown
  → app 結束（Job 需手動呼叫 /quitquitquit）
  → Envoy 收到 SIGTERM → drain connections → 退出
```

---

## Troubleshooting：IPv6 / Dual-Stack 環境 Sidecar Ready 失敗

### 症狀

log 出現 `[::]port` + `connection refused`，記憶體正常、app 有在跑，但 Pod 一直死掉：

```
pilot-agent wait: waiting for Envoy to be ready...
dial tcp [::]:15021: connect: connection refused
```

### 根因

**三個層次的關係：**

```
Node
└── CNI 負責網路設定，決定 Pod 拿到什麼 IP
    └── Pod
        ├── IPv4：10.x.x.x
        └── IPv6：2001:db8::x   ← IPv6-first 時這個是主要 IP
```

**Readiness Probe 的打法：**

kubelet 跑在 Node 上，用 Pod 的**主要 IP** 去打 readiness probe：

```
kubelet → http://[2001:db8::x]:15021/healthz/ready   （IPv6）
```

**Envoy 的監聽行為：**

Envoy 跑在 Pod 內，預設只 bind IPv4：

```
Envoy bind → 0.0.0.0:15021   （IPv4 only）
```

**mismatch 發生點：**

```
kubelet（Node）→ 打 [2001:db8::x]:15021  （IPv6）
                              ↓
              Pod 內的 Envoy 沒有在 IPv6 監聽
                              ↓
                       connection refused
```

問題起點是 **Node 的網路配置（IPv6-first）** 決定了 Pod 的主要 IP，進而影響 kubelet probe 的 address family；但實際 mismatch 發生在 **Pod 內部 Envoy 只監聽 IPv4** 這件事。

### 如何確認是否為 Dual-Stack / Envoy 監聽哪個 address

| 查什麼 | Kubernetes Dashboard | CLI |
|--------|---------------------|-----|
| Pod 有沒有同時拿到 IPv4 + IPv6 | ✓ Pod 詳細頁面看 IP 欄位 | |
| istio-proxy log 有沒有 `[::]` 錯誤 | ✓ Logs → 切換 container | |
| Envoy 實際 bind 哪個 address | ✗ 無法查 | ✓ |

**Dashboard 查 Pod IP：**

Pod 詳細頁面 → `Pod IP` 欄位：
- 只有 IPv4 → 叢集不是 dual-stack
- 同時有 IPv4 + IPv6 → 是 dual-stack，有可能觸發 mismatch

**CLI 確認 Envoy 實際監聽：**

```bash
kubectl exec <pod> -c istio-proxy -n <ns> -- netstat -tlnp | grep 15021
```

| 結果 | 意義 |
|------|------|
| `0.0.0.0:15021` 只有一行 | Envoy 只監聽 IPv4，dual-stack 未啟用 |
| `:::15021` 或兩行都有 | Dual-Stack Sidecar 已啟用 |

### 這是 App YAML 的問題嗎？

**不是。** `15021/healthz/ready` 失敗是 kubelet 打 readiness probe 的行為，由 Node 網路配置和 Envoy bind 方式決定，與 app 的 YAML 無關。

唯一需要檢查 YAML 的例外：

```yaml
annotations:
  sidecar.istio.io/proxyMemory: "64Mi"  # 設太低 → sidecar OOM
  sidecar.istio.io/inject: "false"      # sidecar 根本沒注入
```

排除以上兩個後，去查**叢集的網路配置**，不是 app YAML。

### 確認方式

```bash
# 查叢集是否為 dual-stack
kubectl get node -o jsonpath='{.items[*].status.addresses}'

# 查 namespace label
kubectl get namespace <ns> --show-labels

# 測 istiod 連線（在 istio-proxy container 內）
kubectl exec <pod> -c istio-proxy -n <ns> -- nc -zv istiod.istio-system.svc.cluster.local 15012
```

### 解法

社群主要三種做法，依優先順序：

#### 做法一：官方 experimental dual-stack（最正確，Istio 1.17+）

參考：https://istio.io/latest/blog/2023/experimental-dual-stack/

同時在兩個地方設，缺一不可：

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    defaultConfig:
      proxyMetadata:
        ISTIO_DUAL_STACK: "true"
  values:
    pilot:
      env:
        ISTIO_DUAL_STACK: "true"
```

啟用後 Envoy 同時 bind `0.0.0.0`（IPv4）和 `[::]`（IPv6），probe 不管打哪個都能回應。目前仍是 experimental。

#### 做法二：升級 Istio 版本

參考：https://github.com/istio/istio/issues/41462

Issue #41462 已透過 PR #43892 修復，舊版本才有這個問題。先確認版本再決定是否需要升級。

**CLI：**

```bash
istioctl version
```

**Kubernetes Dashboard（不想下指令）：**

Namespaces → `istio-system` → Deployments → `istiod` → Containers 欄位 → 看 Image tag：

```text
docker.io/istio/pilot:1.18.0
                      ↑ 這就是版本號
```

版本 `< 1.17` → 升版本；`>= 1.17` → 改用做法一加設定。

#### 做法三：強制關掉 IPv6（最快，代價大）

參考：https://github.com/istio/istio/issues/41271

```yaml
values:
  pilot:
    env:
      IPV6_ENABLED: "false"
```

讓 Istio 忽略 IPv6，probe 不會打到 IPv6 位址。**代價是整個 mesh 失去 IPv6 支援**，僅適合測試環境急著跑通。

### 多副本間歇性失敗（附加情況）

單副本正常，scale 到 2+ 才有 pod 失敗 → 並非 IPv6 問題，而是多 pod 同時啟動資源競爭，Envoy 初始化來不及：

```yaml
# 調高 readiness probe 容忍時間
readinessProbe:
  initialDelaySeconds: 30
  failureThreshold: 10
```

### 參考 Issue

- https://github.com/istio/istio/issues/45970 — dual-stack sidecar 監聽錯誤 IP
- https://github.com/istio/istio/issues/41462 — IPv6-first 叢集 gateway/sidecar 全部 ready 不了（已在 PR #43892 修復）
- https://github.com/istio/istio/issues/48358 — EKS 多 replica 間歇性 probe 失敗
- https://github.com/istio/istio/issues/34314 — IngressGateway 15021 refused（CNI / 網路設定）

---

## 連結

- [[kubernetes]]
- [[argocd]]
- [[vault]]
- [[cicd-pipeline]]
