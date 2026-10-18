---
type: reference
domain: tech
tags: [kubernetes, k8s, ebpf, cilium, cni, networkpolicy, hubble, kube-proxy]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 N：eBPF 與 Cilium

CNI 的選擇通常在建叢集那天決定，然後五年沒人再想起。但有三種情況它會重新回到你面前：**NetworkPolicy 套下去沒作用**（Flannel 不支援）、**Service 數量大到 kube-proxy 開始拖慢**、或是**你需要知道「這個封包為什麼被丟掉」而現有工具答不出來**。

這一份講的是目前最主流的答案 Cilium，以及它背後的 eBPF。先講結論：**多數團隊不需要換**，這一份的主要價值是讓你在需要判斷時有依據，而不是跟風。

---

## Part 1：先理解 kube-proxy 的極限

正文第 5 章講過 ClusterIP 是 iptables 規則造出來的虛擬 IP。這個設計有一個結構性問題：**規則數量與 Service 數量成正比，而 iptables 的規則鏈是線性比對的**。

具體來說，每個 Service 的每個後端 Pod 都需要幾條規則。一千個 Service、每個五個副本，就是數萬條規則。帶來三個後果：

- **封包比對變慢**：最壞情況要走過整條鏈
- **規則同步變慢**：任何一個 Pod 變動，kube-proxy 需要重新計算並套用整份規則集，大叢集可能要數秒到數十秒
- **這段延遲期間，流量可能被送到已經不存在的 Pod**

IPVS 模式改善了第一點（用 hash 表查找，O(1)），但規則同步與 netfilter 框架的開銷仍在。

**這是設計的極限，不是調校能解決的。** 小叢集完全感覺不到——幾十個 Service 時 iptables 完全夠用。但服務數量到數百上千時，它會變成真實的瓶頸。

---

## Part 2：eBPF 是什麼

用最白話的方式說：**eBPF 讓你把一小段程式掛進 Linux kernel 裡執行，而不需要改 kernel 原始碼、不需要寫核心模組、也不需要重開機。**

以前要在 kernel 層做事只有兩條路：改 kernel（要重編譯、重開機、每次升級都要重來）或寫核心模組（寫錯直接讓整台機器當掉）。eBPF 是第三條路，而且安全得多。

它的安全性來自一個叫 **verifier** 的元件。程式載入前，verifier 會靜態檢查它：不能有無界迴圈（保證會結束）、不能存取任意記憶體、堆疊大小受限。**驗證不通過就不准載入**——這讓 eBPF 程式無法讓 kernel 當機，這是它能被廣泛採用的根本原因。

程式可以掛在幾種位置（hook 點），對網路最重要的是前兩個：

| hook 點 | 位置 | 用途 |
| --- | --- | --- |
| **XDP** | 網卡驅動層，**最早** | 極高效能的丟包／轉發（DDoS 防護） |
| **tc（traffic control）** | 網路堆疊入口 | Cilium 的主要工作位置 |
| **socket** | socket 操作時 | 同節點 Pod 之間直接轉發，繞過網路堆疊 |
| **kprobe / tracepoint** | 任意 kernel 函式 | 可觀測性、追蹤 |

還有一個關鍵概念是 **eBPF map**：kernel 程式與使用者空間程式共享的資料結構（hash table、array 等）。Cilium 就是把「Service → 後端 Pod」的對應表放進 eBPF map，查找是 O(1) 的雜湊查表，而且**更新單一 Service 只要改 map 裡的一筆，不必重算整份規則集**——這正好解決了 Part 1 的兩個問題。

> 對網路特別有價值的一點：eBPF 可以在封包**進入 netfilter 之前**就處理完。同節點的兩個 Pod 互連時，Cilium 甚至可以在 socket 層直接轉發，完全跳過網路堆疊——延遲比走 iptables 低一個量級。

---

## Part 3：Cilium 實際做了什麼

### 取代 kube-proxy

```yaml
# Helm values 片段
kubeProxyReplacement: true
```

開啟之後 kube-proxy 可以完全移除，Service 的處理改由 eBPF map 完成。這需要較新的 kernel（實務上 5.x 以上比較安全，確切版本以官方文件為準——這是遷移前一定要先確認的前提）。

### Identity-based 安全模型

**這是 Cilium 與傳統 CNI 最根本的差異，值得單獨理解。**

標準 NetworkPolicy 最終是被翻譯成「允許來源 IP X 連到目標 IP Y」的規則。問題是 Pod 的 IP 一直在變——每次重建、每次擴縮，規則都要重算。Pod 數量越多，這個問題越嚴重。

Cilium 的做法是：**依 Pod 的標籤計算出一個「安全身分（security identity）」數字**，標籤相同的所有 Pod 共用同一個身分。政策是以身分為單位執行的，不是以 IP。

後果很實際：

- **一萬個 Pod 但只有五十種標籤組合 → 只有五十個身分**，政策規則數量與 Pod 數量脫鉤
- Pod 重建、擴縮、換 IP 都**不需要重算政策**（身分沒變）
- 封包上帶著身分資訊，接收端直接查表判斷

這個設計讓 NetworkPolicy 在大規模下仍然可用，而不是「理論上支援、實際上一啟用就變慢」。

### L7 政策

標準 NetworkPolicy 只能到 L4（IP + port）。Cilium 可以做到 HTTP 方法與路徑層級：

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7
  namespace: demo
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: api
  ingress:
    - fromEndpoints:
        - matchLabels:
            app.kubernetes.io/name: web
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: "GET"
                path: "/api/v1/.*"
              - method: "POST"
                path: "/api/v1/orders"
```

意思是「前端只能對 API 發 `GET /api/v1/*` 與 `POST /api/v1/orders`，其他一律拒絕」。這是標準 NetworkPolicy 表達不了的。

**代價要知道**：L7 政策的封包會被導進一個 Envoy proxy 處理，有效能開銷。只在真正需要的路徑上用，不要全叢集套。

### 依網域名稱的 egress 政策

這一個在實務上非常有用——「只允許連到 `api.payment.com`」：

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-egress
  namespace: demo
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: api
  egress:
    # 1. DNS 一定要放行，且要走 Cilium 的 DNS proxy
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
          rules:
            dns:
              - matchPattern: "*"
    # 2. 只允許這個網域
    - toFQDNs:
        - matchName: "api.payment.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
    # 3. 叢集內的資料庫
    - toEntities:
        - host
```

標準 NetworkPolicy 只能用 `ipBlock` 寫 CIDR，但外部 API 的 IP 會變（CDN、雲端服務更是天天變）。`toFQDNs` 靠攔截 DNS 回應動態維護允許清單，解決了這個問題。

注意第一段：**用了 `toFQDNs` 就必須把 DNS 查詢也納入 Cilium 的可見範圍**（那段 `rules.dns`），否則 Cilium 看不到解析結果，FQDN 規則不會生效。這是設定 `toFQDNs` 最常見的失敗原因。

`toEntities` 是另一個好用的捷徑，可用值包括 `world`（叢集外）、`cluster`、`host`（節點本身）、`remote-node`、`kube-apiserver`。

### Hubble：看得見的網路

Cilium 附帶的可觀測性元件。它最大的價值是回答一個標準工具答不出來的問題：**「這個封包為什麼被丟掉？」**

```powershell
# 看所有被丟掉的流量與原因
hubble observe --verdict DROPPED

# 特定 Pod 的進出流量
hubble observe --from-pod demo/api-abc123 --follow

# 只看 HTTP，並顯示方法與路徑
hubble observe --protocol http --to-namespace demo
```

輸出會直接寫出 `Policy denied` 之類的判定原因與對應的政策。**排查 NetworkPolicy 時，這比在 YAML 之間推理快一個量級**——附錄 D 的實驗 C4（NetworkPolicy 切斷 DNS）如果有 Hubble，三十秒就能定位。

### 其他值得知道的能力

| 能力 | 解決什麼 |
| --- | --- |
| **ClusterMesh** | 跨叢集的 Service 探索與政策，附錄 L 的多叢集拓撲會用到 |
| **Egress Gateway** | 讓出叢集的流量從固定 IP 出去（給對方防火牆白名單用） |
| **透明加密**（WireGuard / IPsec） | 節點之間流量加密，不需要 service mesh |
| **Gateway API / Ingress** | 內建實作，可省掉另一個 ingress controller |
| **Bandwidth Manager** | Pod 層級的頻寬限制 |

Egress Gateway 值得特別提：實戰第五章講過「Pod 來源 IP 被 SNAT 成 Node IP，所以 DBA 要放行所有 Node」。有了 Egress Gateway，你可以指定所有出去的流量都從一個固定 IP 出去，白名單就只需要一條——**這是一個具體、可量化的維運改善**。

---

## Part 4：該不該換

誠實的判準表：

| 你的情況 | 建議 |
| --- | --- |
| 現有 CNI 運作正常，Service 數量在數百以內 | **不要換**。收益不明顯，風險是真的 |
| 用 Flannel，但需要 NetworkPolicy | 換。Flannel 不支援，Calico 或 Cilium 都可以 |
| Service 數量上千、kube-proxy 同步明顯變慢 | 換 Cilium，這是它最直接的價值 |
| 需要 L7 或 FQDN 層級的網路政策 | 換 Cilium（或用 service mesh，但那更重） |
| 需要跨叢集的 Service 與政策 | Cilium ClusterMesh |
| 網路問題查不出來，缺可觀測性 | Hubble 的價值很高 |
| 已經有 Istio 且滿足需求 | 先確認需求重疊，兩套都上是不必要的複雜度 |

**換 CNI 是一個高風險操作。** 它牽動叢集裡每一個 Pod 的網路，多數情況需要重啟所有工作負載，過程中可能有網路中斷。要做的話：先在測試叢集完整演練、選一個維護窗口、準備回滾方案，而不是「反正它比較新」。

新建叢集則沒有這個包袱——**如果是從零開始，Cilium 是一個合理的預設選擇**。

---

## Part 5：與標準 NetworkPolicy 的對照

`CiliumNetworkPolicy` 是 CRD，語法與標準的不同。對照表：

| 標準 NetworkPolicy | CiliumNetworkPolicy |
| --- | --- |
| `podSelector` | `endpointSelector` |
| `ingress[].from[].podSelector` | `ingress[].fromEndpoints[]` |
| `egress[].to[].podSelector` | `egress[].toEndpoints[]` |
| `ipBlock` | `toCIDR` / `toCIDRSet` |
| （不支援） | `toFQDNs` — 依網域名稱 |
| （不支援） | `toEntities` — `world`/`cluster`/`host` 等 |
| （不支援） | `toPorts[].rules.http` — L7 |
| namespace 範圍 | 另有 `CiliumClusterwideNetworkPolicy` 全叢集範圍 |

**重要：Cilium 同時支援標準的 `NetworkPolicy`。** 所以不必一次全部改寫——既有的標準政策照樣生效，只有需要 L7 或 FQDN 的地方才用 CRD。這讓遷移可以漸進。

有一個語意差異要注意：標準 NetworkPolicy 裡 `- podSelector` 與 `- namespaceSelector` 分開兩項是 OR、寫在同一項是 AND（附錄 C-3 的頭號陷阱）。Cilium 的 `fromEndpoints` 是把 namespace 當成一個標籤（`k8s:io.kubernetes.pod.namespace`）來寫，語意更直觀但**跟你熟悉的寫法不一樣**，轉換時要逐條驗證，不要憑印象翻譯。

---

## Part 6：遷移路徑

真的要做的話，這是務實的順序：

1. **確認前提**：kernel 版本、雲端環境是否支援（EKS/GKE 各有對應的安裝模式）
2. **在測試叢集裝一次**，跑完整的應用與網路測試
3. **決定要不要取代 kube-proxy**——可以先不取代，只當一般 CNI 用，降低變數
4. **正式環境選維護窗口**，準備回滾（保留原 CNI 的設定與安裝方式）
5. **裝完之後所有 Pod 要重啟**才會拿到新的網路設定
6. **驗證**：Pod 之間互連、DNS、Service、Ingress、既有 NetworkPolicy 是否仍生效
7. **開 Hubble**，觀察一段時間有沒有非預期的 drop
8. 穩定後再考慮啟用進階功能（L7 政策、Egress Gateway、加密）

第 3 步值得強調：**一次只改一個變數**。同時換 CNI 又取代 kube-proxy，出事時你不知道是哪一個造成的。

驗證指令：

```powershell
cilium status --wait          # 整體健康狀態
cilium connectivity test      # 官方的連通性測試套件，會跑數十個情境
hubble observe --verdict DROPPED --last 100
```

`cilium connectivity test` 特別值得跑——它會自動部署一組測試工作負載，驗證各種網路情境（同節點、跨節點、對外、DNS、政策），比自己手動測完整得多。

---

## 常見誤解

| # | 誤解 | 真相 |
| --- | --- | --- |
| 1 | eBPF 是新的虛擬機技術 | 它是在 kernel 裡執行受驗證的小程式，跟虛擬化無關 |
| 2 | eBPF 程式寫錯會讓 kernel 當掉 | verifier 會擋下無界迴圈與非法記憶體存取，載入不了 |
| 3 | 換 Cilium 就自動變快 | 小叢集感覺不到；收益出現在 Service 數量大的時候 |
| 4 | Cilium 可以取代 service mesh | 部分重疊（L7 政策、加密），但沒有完整的流量管理（重試、熔斷、金絲雀） |
| 5 | `toFQDNs` 設了就會生效 | 必須同時讓 DNS 查詢經過 Cilium 的 DNS 規則 |
| 6 | L7 政策沒有成本 | 走 Envoy proxy，有效能開銷，別全叢集套 |
| 7 | 換 CNI 可以線上無痛切換 | 牽動所有 Pod 的網路，需要重啟與維護窗口 |
| 8 | 有 Cilium 就不需要標準 NetworkPolicy | 標準的照樣支援，可以混用，適合漸進遷移 |
| 9 | Hubble 只是好看的 UI | 它回答「為什麼被丟掉」，這是排查政策問題的關鍵能力 |
| 10 | 新技術所以應該換 | **多數團隊的現有 CNI 沒有問題**，換的風險大於收益 |

## 檢查清單

要評估或導入時：

- [ ] 有明確的**問題**要解決（政策不支援／規模瓶頸／可觀測性缺口），不是因為它比較新
- [ ] kernel 版本與雲端環境確認支援
- [ ] 在測試叢集完整演練過，含 `cilium connectivity test`
- [ ] 決定是否取代 kube-proxy，且**一次只改一個變數**
- [ ] 既有的標準 NetworkPolicy 逐條驗證仍生效
- [ ] 有維護窗口與回滾方案
- [ ] Hubble 已啟用並觀察過一段時間的 drop 紀錄
- [ ] L7 政策只用在真正需要的路徑
- [ ] 團隊知道怎麼用 `hubble observe` 排查

## 連結

- [[05-networking]] — 正文：Service 選擇鏈、kube-proxy 與完整封包路徑
- [[20-yaml-fields-network-storage]] — 附錄 C-3：標準 NetworkPolicy 全欄位與四條語意規則
- [[26-lab-drills]] — 附錄 D：實驗 C4 的 NetworkPolicy 切斷 DNS
- [[24-yaml-fields-istio]] — 附錄 C-7：service mesh 的能力對照
- [[34-multicluster-and-dr]] — 附錄 L：多叢集拓撲（ClusterMesh 的使用場景）
- [[35-cloud-networking]] — 附錄 M：雲端 CNI 與 Pod IP 模型
- [[00-docker-foundations]] — 正文：namespace 與 cgroup，eBPF 的鄰居
- [[k8s-mastery]] — 教材總目錄
