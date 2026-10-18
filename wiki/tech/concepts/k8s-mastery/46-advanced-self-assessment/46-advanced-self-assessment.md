---
type: reference
domain: tech
tags: [kubernetes, k8s, self-assessment, quiz, review, advanced]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 X：進階自我檢測

附錄 A（[[16-self-assessment]]）那 144 題涵蓋的是正文 16 章。但那份寫完之後，教材又長出了實戰篇 6 章與附錄 E 到 W——大約 13 萬字、20 份文件，一題都沒被考過。

這一份補上。**75 題，全部針對「答錯會造成實際損失」的判斷**，而不是名詞背誦。

## 怎麼用

**蓋住答案，先自己講一遍。** 講得出來才算會——這是附錄 A 就強調過的規則，這裡同樣適用。

三種難度標記：

- 🟢 **基礎**：讀過對應章節就該答得出來
- 🔵 **進階**：需要把兩個以上的概念連起來
- 🔴 **紅色警戒**：**答錯會在正式環境造成實際損害**，這些務必全對

答不出來的，回去讀對應的那一份；答錯的，去做附錄 D 的對應實驗。

---

## 一、實戰篇：從程式碼到上線

**1. 🔴 為什麼應用不能綁 `127.0.0.1`？**

<details><summary>答案</summary>

綁 `127.0.0.1` 表示只接受本機連線，在容器裡等於**外面永遠連不進來**。症狀是 connection refused，看起來像服務沒起來。必須綁 `0.0.0.0`。→ [[practice-1-containerize-your-app]]

</details>

**2. 🔵 Dockerfile 為什麼要先 COPY 專案檔再 COPY 原始碼？**

<details><summary>答案</summary>

利用映像層快取。套件還原很慢但套件清單很少變，原始碼天天改。先複製清單並還原（這層被快取），再複製原始碼。反過來寫的話，改一個字元就要重新下載所有套件——這是 CI 慢的頭號原因。→ [[practice-1-containerize-your-app]]

</details>

**3. 🔴 你在 Dockerfile 裡 `COPY secret.json` 之後又 `RUN rm secret.json`，安全嗎？**

<details><summary>答案</summary>

**不安全。** 映像層是唯讀且疊加的，後面的層刪不掉前面層的東西——那個檔案仍然在前一層裡，任何人都能取出來。唯一的修法是重建映像，而且要輪替那份機密。→ [[38-security-incident-response]]、[[00-docker-foundations]]

</details>

**4. 🔵 前端的 API 位址為什麼不能用一般的環境變數處理？**

<details><summary>答案</summary>

React 的環境變數在 **build 時**就被烤進 JS 檔案，不是執行時讀的。用它的話每個環境要各 build 一份映像，違背「同一映像到處跑」。解法是用相對路徑 `/api` 由 Ingress 分流，或啟動時產生 `config.json`。→ [[practice-1-containerize-your-app]]

</details>

**5. 🟢 一組真實服務至少需要哪七個物件？**

<details><summary>答案</summary>

Namespace、ConfigMap、Secret、Deployment ×2（前後端）、Service ×2、Ingress。→ [[practice-2-deploy-real-app]]

</details>

**6. 🔴 `selector.matchLabels` 為什麼不該放 version 標籤？**

<details><summary>答案</summary>

selector 建立後**不可修改**。放了會變的標籤，升版時就得刪掉整個 Deployment 重建。selector 只能放永不改變的標籤。→ [[practice-2-deploy-real-app]]、[[42-helm-chart-design]]

</details>

**7. 🔵 設了 `readOnlyRootFilesystem: true` 之後為什麼還要掛一個 emptyDir？**

<details><summary>答案</summary>

因為應用通常需要寫暫存檔（.NET 需要 `/tmp`）。唯讀根檔案系統擋掉所有寫入，所以要把真正需要寫的路徑用 `emptyDir` 掛回來。這是這組加固設定的標準搭配。→ [[practice-2-deploy-real-app]]

</details>

**8. 🔴 `preStop` 的 sleep 在解決什麼問題？**

<details><summary>答案</summary>

Pod 開始關閉與「它從 Service endpoints 被移除」是**並行**的，中間有一個窗口流量還在進來。`preStop` 睡幾秒讓 kube-proxy 與 Ingress 有時間更新轉發表。沒有它，更新期間會偶發 502。→ [[practice-2-deploy-real-app]]

</details>

**9. 🔵 服務連不通時，第一個要看的東西是什麼？**

<details><summary>答案</summary>

`kubectl get endpointslice`。有後端就是網路問題，沒後端就是 selector 對不上或 Pod 沒 Ready——這一個指令把排查範圍砍半。→ [[practice-2-deploy-real-app]]、[[intro-6-error-messages]]

</details>

**10. 🔴 ArgoCD 顯示 `Synced` + `Degraded`，你該去查什麼？**

<details><summary>答案</summary>

**查 Pod，不是查 ArgoCD。** `Synced` 代表 ArgoCD 的工作已經完成（YAML 照 git 部署了），`Degraded` 代表資源本身不健康——是應用起不來。這是最容易誤判的組合。→ [[practice-3-gitops-pipeline]]

</details>

**11. 🔴 用 HPA 的服務，ArgoCD 一定要設什麼？**

<details><summary>答案</summary>

`ignoreDifferences` 忽略 `/spec/replicas`。否則 HPA 改副本數 → ArgoCD 改回 git 的值 → HPA 又改 → 無限打架。→ [[practice-3-gitops-pipeline]]

</details>

**12. 🔵 你手動改了線上設定，五分鐘後變回去了。發生什麼事？**

<details><summary>答案</summary>

ArgoCD 的 `selfHeal: true` 在工作——你的手改被視為漂移並自動修正。**這是正確行為**，要改就改 git。它把「不准手改線上」從規定變成技術上做不到。→ [[practice-3-gitops-pipeline]]

</details>

**13. 🟢 要寫一個新的 Deployment，第一個動作是什麼？**

<details><summary>答案</summary>

`kubectl create deployment x --image=y --dry-run=client -o yaml` 產生骨架。**永遠不要從空白檔案開始。**→ [[practice-4-write-yaml-from-scratch]]

</details>

**14. 🔵 「這個程式跑完會自己結束嗎」這個問題在決定什麼？**

<details><summary>答案</summary>

決定 kind。會結束 → Job 家族；不會結束 → Deployment 家族。第二個問題「兩個副本可以完全一樣互相取代嗎」則決定 Deployment 還是 StatefulSet。→ [[practice-4-write-yaml-from-scratch]]

</details>

**15. 🔴 HPA 最大 20 副本、每個 Pod 連線池 100，資料庫會看到幾條連線？**

<details><summary>答案</summary>

**2000 條**。連線數是乘法：Pod 數 × 每 Pod 池大小。多數資料庫的 `processes` 沒設這麼高——結果是**擴容這個動作本身把資料庫壓垮**。要從資料庫容量反推每個 Pod 的池上限。→ [[practice-5-database-and-state]]

</details>

**16. 🔴 為什麼不能在 `Program.cs` 裡呼叫 `Migrate()`？**

<details><summary>答案</summary>

三個副本同時啟動就是三個同時跑 migration，輕則互等鎖、重則資料損壞。要抽成獨立的 Job，用 ArgoCD 的 PreSync hook 在部署前執行。→ [[practice-5-database-and-state]]

</details>

**17. 🔴 要把一個欄位改名，零停機的做法是幾步？**

<details><summary>答案</summary>

三步（expand-contract）：①只加不刪，新增欄位可為 NULL；②部署新版程式同時寫新舊欄位，背景回填；③確認沒有程式再用舊欄位後才刪除。因為滾動更新期間**新舊版必然共存**，一次改完會讓舊版直接爆炸。→ [[practice-5-database-and-state]]

</details>

**18. 🔵 K8s 沒有 `depends_on`，應用啟動時資料庫還沒好怎麼辦？**

<details><summary>答案</summary>

讓應用重試而不是退出，並讓 readiness 失敗——不收流量但不重啟，資料庫好了自動恢復。**不要用 initContainer 等待**，那會讓每次重啟都再等一次，且資料庫抖動時所有 Pod 卡在 Init。→ [[practice-5-database-and-state]]

</details>

**19. 🔴 Prometheus 抓不到你的服務，第一個檢查什麼？**

<details><summary>答案</summary>

ServiceMonitor **自己的 label** 是否符合 Prometheus 的 `serviceMonitorSelector`（多數 chart 要求 `release: <helm release 名>`）。這是第一名原因，而且**完全沒有錯誤訊息**——Prometheus 只是靜靜地忽略你。→ [[practice-6-observability]]

</details>

**20. 🔴 為什麼不能把使用者 ID 當成指標標籤？**

<details><summary>答案</summary>

每個標籤組合是一條獨立時間序列。一百萬個 ID 就是一百萬條，Prometheus 記憶體直接爆掉。標籤的可能值必須**有限且可枚舉**——用路由樣板 `/api/users/{id}` 而非實際路徑。→ [[practice-6-observability]]

</details>

**21. 🔴 告警規則寫好了、Prometheus UI 也變紅了，為什麼還可能沒人知道出事？**

<details><summary>答案</summary>

Alertmanager → Slack/Email 這一段可能斷掉，而且它會**安靜地什麼都不送**。這種故障只有主動測試才會發現，發現時機通常是真的出事之後。**沒有測過的監控等於沒有監控。**→ [[practice-6-observability]]

</details>

---

## 二、升級與棄用（附錄 E）

**22. 🔴 K8s 1.30 要升到 1.33，可以直接跳嗎？**

<details><summary>答案</summary>

**不行。** 一次只能跳一個小版本，必須走 1.31 → 1.32 → 1.33。強行跨版的後果不是報錯，而是 etcd 裡的物件可能無法被新版正確讀取。patch 版（1.33.1 → 1.33.4）則可以直接跳。→ [[27-upgrades-and-deprecations]]

</details>

**23. 🔵 升級順序是什麼？為什麼？**

<details><summary>答案</summary>

etcd → apiserver → controller-manager/scheduler → kubelet/kube-proxy → kubectl。因為 version skew 規則允許 kubelet 比 apiserver **舊**最多三版，但不允許比它新。先升 kubelet 是明確不支援的組合。→ [[27-upgrades-and-deprecations]]

</details>

**24. 🔴 升級前，哪一種既有設定可能讓整座叢集鎖死？**

<details><summary>答案</summary>

`failurePolicy: Fail` 且沒排除 `kube-system` 的 admission webhook。升級中 API Server 會重啟，若此時 webhook 服務也在被驅逐，所有符合 rules 的請求都被拒絕——**包含建立 webhook 自己的 Pod**，形成無法自救的死鎖。→ [[27-upgrades-and-deprecations]]

</details>

**25. 🔵 怎麼知道叢集裡還有誰在用即將被移除的 API？**

<details><summary>答案</summary>

四個互補手段：`apiserver_requested_deprecated_apis` metric（看真實流量，含不在 git 裡的呼叫者）、`pluto detect-files`（掃檔案）、`kubent`（掃活著的物件）、audit log（查是誰）。→ [[27-upgrades-and-deprecations]]

</details>

**26. 🔴 哪一種升級變更「不會報錯但會讓安全設定失效」？**

<details><summary>答案</summary>

seccomp 與 AppArmor 從 annotation 改成正式欄位。舊 annotation **靜默失效**——Pod 照樣起來，只是原本以為生效的保護沒了。升級後要抽驗 `securityContext.seccompProfile` 是否真的存在。→ [[27-upgrades-and-deprecations]]

</details>

---

## 三、Ingress 與狀態判讀（附錄 F、G）

**27. 🔴 annotation 打錯字會怎樣？**

<details><summary>答案</summary>

**完全靜默失效**，沒有任何錯誤訊息。API Server 不驗證 annotation 內容，controller 認不得的 key 直接忽略。唯一可靠的驗證是進 controller Pod 看產生的 `nginx.conf`。→ [[28-ingress-nginx-annotations]]

</details>

**28. 🔵 `rewrite-target: /` 配 `pathType: Prefix` 有什麼問題？**

<details><summary>答案</summary>

會把 `/api` 底下**所有**路徑都改寫成 `/`，`/api/users` 與 `/api/orders` 都變成 `/`。要保留後段必須用捕獲群組 + `use-regex`。→ [[28-ingress-nginx-annotations]]

</details>

**29. 🔴 上傳大檔失敗但應用日誌完全沒紀錄，為什麼？**

<details><summary>答案</summary>

`proxy-body-size` 預設 1m，請求在 Ingress 就被 413 擋掉，**根本沒到應用**。而且這條鏈上每一層都有上限（CDN、Ingress、應用框架），任何一層漏改症狀都一樣。→ [[28-ingress-nginx-annotations]]

</details>

**30. 🔵 為什麼不該為了方便打開 snippet annotation？**

<details><summary>答案</summary>

它等於讓任何能建立 Ingress 的人往 nginx 設定檔注入任意內容。2025 年的 IngressNightmare 系列漏洞正是這條路徑的 RCE。保持 `allow-snippet-annotations: "false"`。→ [[28-ingress-nginx-annotations]]

</details>

**31. 🔴 exit code 137 代表什麼？OOM 時 `preStop` 會執行嗎？**

<details><summary>答案</summary>

137 = 128 + 9（SIGKILL），是 OOMKilled 的指紋。**OOM 沒有寬限期**，`preStop` 與優雅關閉邏輯完全不會執行。相對地 143（SIGTERM）代表正常收到終止訊號——正常滾動更新應該看到 143。→ [[29-status-and-conditions]]

</details>

**32. 🔵 `CreateContainerConfigError` 是映像問題嗎？**

<details><summary>答案</summary>

**不是。** 它是引用的 ConfigMap 或 Secret 不存在。這個誤判每年浪費不少人的時間。→ [[29-status-and-conditions]]

</details>

**33. 🔴 部署失敗但 `kubectl get pods` 什麼都沒有，去哪裡看原因？**

<details><summary>答案</summary>

ReplicaSet 的 `ReplicaFailure` condition：`kubectl describe rs -l app=x`。當 PSA 或 ResourceQuota 擋下 Pod 時，Pod 根本沒被建出來，錯誤訊息只在這裡。→ [[29-status-and-conditions]]

</details>

**34. 🔵 Node 顯示 `Ready=Unknown` 跟 `Ready=False` 差在哪？**

<details><summary>答案</summary>

`False` 是 kubelet 回報自己不健康；`Unknown` 是**沒有人回報**——kubelet 沒在續 Lease，通常是網路、憑證過期或 apiserver 過載，不是機器壞了。查的方向完全不同。→ [[29-status-and-conditions]]

</details>

**35. 🔵 namespace 卡在 Terminating，三十秒內怎麼定位？**

<details><summary>答案</summary>

看它的三個 condition：`NamespaceDeletionDiscoveryFailure`、`NamespaceContentRemaining`、`NamespaceFinalizersRemaining`——**message 會直接列出是哪些資源、哪個 finalizer**。不必用強制清 finalizer 的偏方。→ [[29-status-and-conditions]]

</details>

**36. 🔵 HPA 顯示 `<unknown>` 不動作，九成是什麼原因？**

<details><summary>答案</summary>

目標 Pod 沒設 `resources.requests`。`Utilization` 是相對 requests 的百分比，沒有 requests 就無從計算。condition 會顯示 `ScalingActive=False` 配 `FailedGetResourceMetric`。→ [[29-status-and-conditions]]

</details>

---

## 四、維運與成本（附錄 H、K）

**37. 🔴 「備份存在」與「能還原」差在哪？**

<details><summary>答案</summary>

差一次演練。快照檔可能損毀、還原步驟可能沒人會、**還原後憑證可能對不上**——這些只有真的做過才會發現。沒有實際還原過的備份等於沒有備份。→ [[30-production-readiness]]、[[34-multicluster-and-dr]]

</details>

**38. 🔵 為什麼 etcd 兩副本比單副本更糟？**

<details><summary>答案</summary>

兩副本無法形成多數決——任一台掛掉整個叢集就唯讀。單副本至少行為單純。要 HA 就要三副本以上（奇數）。→ [[30-production-readiness]]

</details>

**39. 🔴 排程飽和度 85% 但真實飽和度 25%，代表什麼？**

<details><summary>答案</summary>

requests 開得太大。機器看起來滿了（排不進新 Pod）但實際幾乎閒著——**兩者的差距就是你在買的空氣**。優化的第一步是調 requests，不是加節點。→ [[33-cost-optimization]]

</details>

**40. 🔴 調 requests 時，記憶體與 CPU 為什麼要用不同的分位數？**

<details><summary>答案</summary>

因為超限行為完全不同。記憶體超限 **OOMKilled 立刻死**，猜低的代價是服務中斷，所以用 P99 甚至 max；CPU 超限只是被 throttle 變慢，所以可以積極用 P90。用同一套標準是最常見的方法論錯誤。→ [[33-cost-optimization]]

</details>

**41. 🔵 開了 cluster-autoscaler 但節點數從來沒降過，查什麼？**

<details><summary>答案</summary>

四個原因：沒有 controller 管理的裸 Pod、PDB 不允許驅逐（單副本 + `minAvailable: 1`）、使用 `emptyDir` 的 Pod、有 local storage 或 node affinity 綁死的 Pod。→ [[33-cost-optimization]]

</details>

**42. 🔵 StatefulSet 縮容之後帳單為什麼沒降？**

<details><summary>答案</summary>

PVC **預設會保留**（`persistentVolumeClaimRetentionPolicy.whenScaled` 預設 `Retain`），磁碟繼續計費。這是刻意的資料保護，但要納入盤點。→ [[33-cost-optimization]]、[[40-operators-and-stateful]]

</details>

**43. 🔴 什麼時候該設 CPU limit、什麼時候不該？**

<details><summary>答案</summary>

線上服務且節點自己掌控 → **不設**（讓它在尖峰借用閒置 CPU）；多團隊共用需要防呆 → 設，但給 requests 的 2–4 倍；批次工作 → 設；延遲敏感要求完全可預測 → 設成等於 requests。**但記憶體 limit 永遠要設**，因為它不可壓縮。→ [[33-cost-optimization]]

</details>

---

## 五、災難復原與雲端（附錄 L、M）

**44. 🔴 備份 etcd 時，還必須一起備份什麼？**

<details><summary>答案</summary>

`/etc/kubernetes/pki`。還原 etcd 後若憑證不是原本那組，所有元件無法互相驗證，叢集起不來——而**錯誤訊息全是 x509 相關，完全不指向「你忘了備份憑證」**。這是還原演練最常卡住的地方。→ [[34-multicluster-and-dr]]

</details>

**45. 🔵 「誤刪 namespace」該用 etcd 快照還原嗎？**

<details><summary>答案</summary>

不該。etcd 快照是**全叢集**回到某個時間點，會把其他人的變更一起回滾。這種情境要用 Velero（或有 GitOps 的話直接讓 ArgoCD 重新同步，只用 Velero 救 PV 資料）。→ [[34-multicluster-and-dr]]

</details>

**46. 🔴 還原 PV 資料時，為什麼不該直接蓋回正式 namespace？**

<details><summary>答案</summary>

**蓋回是不可逆的**——如果還原的是壞資料，你連原本的壞狀態都回不去。正確做法是用 `--namespace-mappings` 還原到旁邊，確認資料正確再切換。→ [[34-multicluster-and-dr]]

</details>

**47. 🔵 四層要保護的東西裡，哪一層最常被完全遺忘？**

<details><summary>答案</summary>

**第四層：叢集外的依賴**——DNS、憑證、registry 裡的映像、Vault 的機密、雲端資源。這是「叢集重建好了但服務還是不通」的根因。→ [[34-multicluster-and-dr]]

</details>

**48. 🔴 什麼決定一個 subnet 是不是 public？**

<details><summary>答案</summary>

它的 route table 裡有沒有 `0.0.0.0/0 → igw-xxxxx`。**「public subnet」不是一個設定選項，是路由的推論結果**。而且只有路由還不夠——實例還要有公有 IP，否則封包回不來。→ [[35-cloud-networking]]

</details>

**49. 🔴 EKS 上節點 CPU 只用了 20%，Pod 卻排不進去，為什麼？**

<details><summary>答案</summary>

**IP 額度用完了**。VPC 原生 CNI 讓 Pod 拿真實 VPC IP，而每台 EC2 的 ENI 數 × 每 ENI 的 IP 數由**機型**決定，這個上限跟 CPU/記憶體無關。解法是換機型、開 prefix delegation、或加 secondary CIDR。→ [[35-cloud-networking]]

</details>

**50. 🔵 為什麼不該把雲端權限掛在節點的 instance profile 上？**

<details><summary>答案</summary>

那台節點上的**每一個 Pod 都拿到那份權限**，包含不該有的，等於繞過 RBAC。正解是 IRSA / Workload Identity，用 SA 身分換臨時憑證——結構跟 Vault 的信任鏈相同。→ [[35-cloud-networking]]

</details>

**51. 🔵 多可用區叢集為什麼 StorageClass 必須用 `WaitForFirstConsumer`？**

<details><summary>答案</summary>

EBS 綁在單一 AZ。用 `Immediate` 會先隨機挑一個 AZ 建磁碟，然後 Pod 因為 nodeAffinity 排不到其他 AZ，永遠 Pending——而且錯誤訊息指向排程失敗，很難聯想到 StorageClass。→ [[35-cloud-networking]]

</details>

---

## 六、平台、安全與效能（附錄 N–Q）

**52. 🔵 Cilium 的 identity-based 安全模型解決了什麼問題？**

<details><summary>答案</summary>

標準 NetworkPolicy 最終翻譯成「IP X 允許連 IP Y」，Pod IP 一直變所以規則一直重算。Cilium 依標籤算出「安全身分」——一萬個 Pod 但五十種標籤組合就只有五十個身分，**政策規則數與 Pod 數脫鉤**。→ [[36-ebpf-and-cilium]]

</details>

**53. 🔴 設了 `toFQDNs` 但規則沒生效，最常見原因？**

<details><summary>答案</summary>

沒有讓 DNS 查詢經過 Cilium 的 DNS 規則。Cilium 靠攔截 DNS 回應維護允許清單，看不到解析結果就無法運作。→ [[36-ebpf-and-cilium]]

</details>

**54. 🔴 應用團隊該不該擁有自己的 YAML？**

<details><summary>答案</summary>

該。平台代寫的話，出事時沒有人真正理解那份設定，而且平台會被鎖死在維護幾十份別人的 manifest 上。平台提供**預設值與工具**，不提供決策。→ [[37-platform-engineering]]

</details>

**55. 🔴 `ResourceQuota` 為什麼一定要配 `LimitRange`？**

<details><summary>答案</summary>

設了 quota 之後，沒寫 requests 的 Pod 會被直接拒絕，而**錯誤訊息藏在 ReplicaSet 的 condition 裡**，對新手極不友善。LimitRange 補上預設值就沒這個問題。→ [[37-platform-engineering]]

</details>

**56. 🔵 給團隊 `edit` 而不是 `admin`，差在哪？**

<details><summary>答案</summary>

`edit` 不含修改 RBAC 的權限——團隊無法自行提權。這是多租戶的重要邊界。→ [[37-platform-engineering]]

</details>

**57. 🔴 政策為什麼不能直接上 `enforce`？**

<details><summary>答案</summary>

既有工作負載會整批被擋、所有部署突然掛掉，而且錯誤出現在 ReplicaSet 不是 Pod。必須走 `audit` → `warn` → `enforce`，並給明確的截止日與遷移指南。**新建的 namespace 可以直接 enforce**，只有既有的需要過渡期。→ [[37-platform-engineering]]

</details>

**58. 🔴 發現密碼進了 git，第一件事做什麼？**

<details><summary>答案</summary>

**輪替憑證**，不是清 git 歷史。清歷史要時間、要協調所有人，而這段期間密碼仍然有效；而且你無法確定沒人看過（fork、CI 快取、搜尋引擎）。正確心智模型是「**外洩即已失效**」。→ [[38-security-incident-response]]

</details>

**59. 🔴 發現一個可疑的 Pod 在挖礦，第一個動作是什麼？**

<details><summary>答案</summary>

**不是 `kubectl delete pod`**——那會毀掉證據，而且 controller 會立刻重建一個一樣（一樣被入侵）的。正確順序是隔離（quarantine NetworkPolicy）→ 蒐證 → 評估 → 清理。技巧是改掉它的 `app` 標籤，controller 會補一個健康的新 Pod，可疑的那個變孤兒留存供調查。→ [[38-security-incident-response]]

</details>

**60. 🔵 怎麼判斷入侵的災情大小？**

<details><summary>答案</summary>

看被入侵的 Pod 用哪個 ServiceAccount，然後 `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>`。只能讀自己 namespace 的 ConfigMap → 災情有限；是 cluster-admin → 假設整座叢集失守。→ [[38-security-incident-response]]

</details>

**61. 🔵 容器逃逸的六條常見路徑有什麼共同點？**

<details><summary>答案</summary>

**全部是設定給的，不是漏洞給的**（privileged、hostPath 掛 `/`、docker.sock、hostPID、`CAP_SYS_ADMIN`、allowPrivilegeEscalation）。所以 PSA `restricted` 一個 label 就能消滅絕大多數——但它涵蓋不了 kernel 漏洞。→ [[38-security-incident-response]]

</details>

**62. 🔴 CPU 使用率只有 20%，還可能被大量 throttle 嗎？**

<details><summary>答案</summary>

**會。** CFS 以 100ms 為週期，`limit: 500m` 表示每 100ms 只有 50ms 額度。一個需要密集運算 80ms 的請求會在 50ms 被凍結、等下個週期才繼續——平白多 50ms 延遲，但一分鐘平均看只有 20%。**要看 throttle 比率，不是使用率。**→ [[39-performance-troubleshooting]]

</details>

**63. 🔵 P50 也高，跟 P50 正常但 P99 高，根因方向差在哪？**

<details><summary>答案</summary>

P50 也高 → 每個請求都在做同樣多的工作（程式邏輯、查詢效率、下游本來就慢）；P50 正常 P99 高 → 多數請求很快、少數卡住（排隊、GC、throttle、鎖競爭）。只看平均會完全錯過第二種。→ [[39-performance-troubleshooting]]

</details>

**64. 🔵 查效能問題時，最有效率的第一個問題是什麼？**

<details><summary>答案</summary>

**「什麼時候開始的？」** 把延遲曲線跟 `kubectl rollout history` 與 events 對齊，如果對得上某次部署或設定變更，你已經找到嫌疑犯了。→ [[39-performance-troubleshooting]]

</details>

**65. 🔴 尾端延遲查到一半，為什麼要先確認「整條鏈有幾層在重試」？**

<details><summary>答案</summary>

重試會放大。Istio 預設就有重試，加上應用層自己的，實際請求數可能是你以為的九倍。下游稍微變慢時，重試把負載放大讓它更慢，形成正回饋。→ [[39-performance-troubleshooting]]

</details>

---

## 七、Operator、排程與 Chart（附錄 R–T）

**66. 🔴 什麼時候該寫 Operator？**

<details><summary>答案</summary>

有「**需要持續執行的運維知識**」時。實用反問：如果沒有人在，這件事還需要發生嗎？答案是「等人來做就好」的話，你要的是文件與腳本。只做到 L1/L2（安裝、升級）的話，Helm chart 就夠，寫 Operator 只是多一個要維護的元件。→ [[40-operators-and-stateful]]

</details>

**67. 🔴 controller 為什麼不能寫 `spec`？**

<details><summary>答案</summary>

會造成無限迴圈（你改 spec → 觸發事件 → 你又改）。`spec` 是使用者的願望、`status` 是你回報的現實，兩者必須嚴格分離，且 CRD 要開 status 子資源。→ [[40-operators-and-stateful]]

</details>

**68. 🔵 為什麼「能用 ownerReference 就不要用 finalizer」？**

<details><summary>答案</summary>

ownerReference 讓 GC 自動清理子資源，你完全不用寫刪除邏輯；finalizer 是有風險的機制（namespace 卡 Terminating 的頭號原因）。finalizer 只留給**叢集外的資源**。→ [[40-operators-and-stateful]]

</details>

**69. 🔵 要改 StatefulSet 的 `volumeClaimTemplates`，怎麼做？邊界在哪？**

<details><summary>答案</summary>

`kubectl delete sts x --cascade=orphan` 保留 Pod 與 PVC，改完 YAML 再 apply，StatefulSet 靠名稱與 selector 認領回來。**但它換不掉已存在 PVC 的 StorageClass**——那只能建新 PVC 複製資料。→ [[40-operators-and-stateful]]

</details>

**70. 🔴 PDB 能保護 Pod 不被搶佔嗎？**

<details><summary>答案</summary>

**不能。** PDB 對 `kubectl drain` 是硬約束，對搶佔只是**偏好**——scheduler 會盡量避免違反，但找不到其他方案時仍會違反。→ [[41-advanced-scheduling]]

</details>

**71. 🔵 分散式訓練的 8 個 worker 只排上 6 個，會發生什麼？**

<details><summary>答案</summary>

死鎖。那 6 個啟動後互等另外 2 個，永遠等不到但持續佔用資源，讓其他工作也排不進來。K8s 原生沒有 gang scheduling，要用 Kueue——它靠 Job 的 `suspend` 欄位，拿不到整組資源就完全不產生 Pod。→ [[41-advanced-scheduling]]

</details>

**72. 🔴 spot 節點跑 Job，一定要設什麼才不會被誤判失敗？**

<details><summary>答案</summary>

`podFailurePolicy` 加上 `action: Ignore` + `onPodConditions: DisruptionTarget`，把被搶佔造成的失敗排除在 `backoffLimit` 之外。不設的話幾次回收就把重試用完，Job 被判定失敗但工作本身沒問題。→ [[41-advanced-scheduling]]

</details>

**73. 🔴 chart 裡用 `lookup` 沿用既有 Secret，在 ArgoCD 底下會怎樣？**

<details><summary>答案</summary>

ArgoCD 用 `helm template` 渲染、沒有叢集連線，`lookup` **一律回空且不報錯**，於是每次同步都走 else 分支產生新密碼——**無聲的資料破壞**。結論：不要在 chart 裡產生機密。→ [[42-helm-chart-design]]

</details>

**74. 🔵 內部 chart 要移除一個 values 欄位，該怎麼做？**

<details><summary>答案</summary>

三步：①新舊並存（MINOR 版）②公告期，給明確截止版本 ③MAJOR 版移除，且舊欄位若被設定要用 `fail` 給明確遷移訊息。**直接移除會讓設定被靜默忽略**，服務用預設值跑起來但行為不對，比報錯難查。→ [[42-helm-chart-design]]

</details>

**75. 🔴 遷移專案該從哪個系統開始？**

<details><summary>答案</summary>

**難度最低、且不是關鍵的那個。** 第一個專案的目標是建立能力與樣板（chart、CI/CD、runbook），不是創造最大價值。從最重要的系統開始的話，第一次就出大事，專案會失去信任。→ [[43-migration-to-k8s]]

</details>

---

## 紅色警戒清單

上面 🔴 標記的判斷，濃縮成一頁。**這些答錯會在正式環境造成實際損害：**

1. 映像層刪不掉東西——`COPY` 進去的機密要重建映像並輪替
2. `selector` 不可修改，不要放會變的標籤
3. 沒有 `preStop` 的滾動更新會偶發 502
4. `Synced` + `Degraded` 該查 Pod 不是查 ArgoCD
5. HPA + GitOps 必須 `ignoreDifferences` 忽略 replicas
6. 連線數是 Pod 數 × 連線池的**乘法**，擴容可能壓垮資料庫
7. 不要在應用啟動時跑 migration
8. schema 破壞性變更要走 expand-contract 三步
9. Prometheus 抓不到服務時**沒有任何錯誤訊息**
10. 高基數標籤會打死 Prometheus
11. **沒測過的通知鏈路等於沒有告警**
12. 升級一次只能跳一版
13. `failurePolicy: Fail` 的 webhook 可能讓升級死鎖
14. seccomp/AppArmor 從 annotation 改欄位是**靜默失效**
15. Ingress annotation 打錯字**靜默失效**
16. exit 137 = OOMKilled，且 `preStop` 不會執行
17. 部署失敗時 Pod 可能根本沒被建出來，要看 ReplicaSet
18. 沒還原演練過的備份等於沒有備份
19. etcd 快照必須連 `/etc/kubernetes/pki` 一起備
20. 還原不要直接蓋回正式 namespace
21. EKS 上「排不進去」常常是 IP 額度而非 CPU
22. requests 的記憶體用 P99、CPU 用 P90
23. 記憶體 limit 永遠要設
24. 密碼外洩**先輪替再清理**
25. 不要 `delete` 可疑的 Pod
26. **CPU 使用率低仍可能大量 throttle**
27. 重試會放大，要知道整條鏈有幾層
28. PDB 對搶佔只是偏好不是硬保證
29. spot 上的 Job 要用 `podFailurePolicy` 排除搶佔失敗
30. chart 裡的 `lookup` 在 ArgoCD 下是無聲的資料破壞

---

## 連結

- [[69-third-self-assessment]] — 附錄 AU：**接續這份**——附錄 Y–AT 的 70 題
- [[16-self-assessment]] — 附錄 A：涵蓋正文 16 章的 144 題
- [[26-lab-drills]] — 附錄 D：答錯的題目去做對應實驗
- [[17-cheatsheet]] — 附錄 B：速查表
- [[31-glossary]] — 附錄 I：術語百科
- [[k8s-mastery]] — 教材總目錄
