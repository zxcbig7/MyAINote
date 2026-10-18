---
type: reference
domain: tech
tags: [kubernetes, k8s, self-assessment, quiz, review, appendix]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 AU：第三份自我檢測（附錄 Y–AT）

附錄 A（[[16-self-assessment]]）考正文 16 章，附錄 X（[[46-advanced-self-assessment]]）考實戰篇與附錄 E–W。

但附錄 X 寫完之後，教材又長出了**附錄 Y 到 AT——22 份文件、約 13 萬字，一題都沒被考過**。這一份補上，理由跟當初寫附錄 X 時一模一樣。

**70 題，全部針對「答錯會造成實際損失」的判斷**，不是名詞背誦。

## 怎麼用

**蓋住答案，先自己講一遍。** 講得出來才算會。

- 🟢 **基礎**：讀過對應章節就該答得出來
- 🔵 **進階**：需要把兩個以上的概念連起來
- 🔴 **紅色警戒**：**答錯會在正式環境造成實際損害**，務必全對

答不出來的，回去讀對應那一份。

---

## 一、介面演進與測試（附錄 Y、Z）

**1. 🔵 在 API 回應裡「新增一個欄位」，什麼時候是破壞性變更？**

<details><summary>答案</summary>

當呼叫方用嚴格反序列化（遇到未知欄位就報錯）、或用回應做簽章／雜湊比對時。「加欄位一定安全」只在呼叫方寬鬆解析時成立——**而你通常無法保證所有呼叫方都是**。→ [[47-api-versioning]]

</details>

**2. 🔴 你要移除一個 API 欄位，第一步該做什麼？**

<details><summary>答案</summary>

**先讓「誰在用」變成可觀測**——加上使用度量，確認實際還有沒有人呼叫。沒有數據就宣布棄用，等於猜。棄用流程的順序是：可觀測 → 公告 → 觀察歸零 → 才移除。→ [[47-api-versioning]]

</details>

**3. 🔵 K8s 上讓 API 多版本並存，最推薦的做法是哪一種？為什麼？**

<details><summary>答案</summary>

**兩個 Deployment + Ingress 路徑分流。** 兩個版本各自是獨立的工作負載，可以分別擴縮、分別回滾、分別觀測；而「同一個 Deployment 內部判斷版本」會讓兩版的問題混在一起，且無法單獨回滾其中一版。→ [[47-api-versioning]]

</details>

**4. 🔴 兩個 API 版本共用同一個資料庫，最大的風險是什麼？**

<details><summary>答案</summary>

**資料庫 schema 變更必須同時相容兩個版本。** 這代表你不能直接改欄位型別或刪欄位，必須走「新增 → 雙寫 → 遷移 → 移除」的多步驟流程。忘記這件事的話，升級新版就會弄壞舊版。→ [[47-api-versioning]]

</details>

**5. 🟢 應用層測試該用 Testcontainers 還是起一個 K8s 叢集？**

<details><summary>答案</summary>

**Testcontainers。** 應用邏輯測試不需要叢集，起叢集只會讓測試變慢又變脆。叢集只在「你要驗證的東西本身是 K8s 行為」時才需要。→ [[48-testing-in-k8s]]

</details>

**6. 🔵 CI 的第一道關卡該擋什麼？**

<details><summary>答案</summary>

**manifest 的靜態驗證**——schema 是否合法、有沒有用到已移除的 API、有沒有違反基線政策。這一關最快、最便宜，能擋掉大部分低級錯誤，不需要任何叢集。→ [[48-testing-in-k8s]]

</details>

**7. 🔴 測試環境永遠測不到什麼？**

<details><summary>答案</summary>

真實流量規模、真實資料分布、真實的節點故障、真實的外部依賴延遲。**所以「測試過了」不能取代漸進式發布與可回滾**——這是為什麼金絲雀與回滾機制不是可選項。→ [[48-testing-in-k8s]]

</details>

**8. 🔵 每個 PR 一套預覽環境，最容易被忽略的成本是什麼？**

<details><summary>答案</summary>

**不是機器成本，是「誰來清理」與「資料從哪來」。** 沒有自動回收機制的預覽環境會累積成殭屍；而沒有可用測試資料的預覽環境沒有人會真的用它。→ [[48-testing-in-k8s]]

</details>

---

## 二、訊息、快取與背景工作（附錄 AA、AB、AC）

**9. 🟢 Kafka 與 RabbitMQ 最根本的差異是什麼？**

<details><summary>答案</summary>

Kafka 是**保留的日誌**（訊息讀完還在，可重放，由 offset 決定讀到哪），RabbitMQ 是**佇列**（訊息被消費就消失）。這決定了「能不能重放」，而重放能力會直接影響你的錯誤處理設計。→ [[49-messaging-and-events]]

</details>

**10. 🔴 Kafka 的 consumer 擴到 20 個副本，但吞吐量沒有變好，為什麼？**

<details><summary>答案</summary>

**並行上限是 partition 數。** partition 只有 6 個的話，最多只有 6 個 consumer 在工作，其餘 14 個閒置。加副本前要先確認 partition 夠多——這是最常見的「擴了沒用」。→ [[49-messaging-and-events]]

</details>

**11. 🔴 「至少一次」的投遞語意，對你的程式碼有什麼強制要求？**

<details><summary>答案</summary>

**處理必須冪等。** 同一則訊息會被處理多次是正常情況，不是例外。沒有冪等設計的話，重試會造成重複扣款、重複發信這類無法挽回的後果。→ [[49-messaging-and-events]]

</details>

**12. 🔵 為什麼 consumer 不適合用一般的 HPA（依 CPU）擴縮？**

<details><summary>答案</summary>

consumer 不是 HTTP 服務，它的忙碌程度反映在**佇列積壓量**而不是 CPU。積壓一萬則但 CPU 不高是常見情況。要依佇列長度擴縮（KEDA 這類）。→ [[49-messaging-and-events]]

</details>

**13. 🔴 consumer 的優雅關閉沒做好會怎樣？**

<details><summary>答案</summary>

正在處理的訊息被中途砍斷，而 offset 可能已提交（訊息遺失）或未提交（重複處理）。滾動更新會頻繁觸發這件事，所以它不是罕見情境。→ [[49-messaging-and-events]]

</details>

**14. 🔴 服務有 3 個副本，每個都用本機記憶體快取，會發生什麼？**

<details><summary>答案</summary>

**同一份資料在三個副本上不一致。** 使用者連到不同副本會看到不同結果，而且清快取只清得掉你連到的那一個。這是多副本下最常見的「時好時壞」來源。→ [[50-caching]]

</details>

**15. 🔵 那本機快取什麼時候仍然是對的？**

<details><summary>答案</summary>

資料**極少變動**（設定、對照表）、或**能接受短暫不一致**、或有明確的失效廣播機制時。判準是「不一致會不會被使用者看見並造成問題」。→ [[50-caching]]

</details>

**16. 🔴 Redis 沒設 `maxmemory` 政策會怎樣？**

<details><summary>答案</summary>

記憶體用滿之後行為取決於預設政策——可能開始拒絕寫入，讓你的快取層變成故障源。**快取應該在滿的時候淘汰舊資料，而不是報錯**，所以這個參數必設。→ [[50-caching]]

</details>

**17. 🔴 快取雪崩是什麼？怎麼避免？**

<details><summary>答案</summary>

大量快取同時到期，請求瞬間全部打到資料庫，把後端壓垮。避免方式是**給 TTL 加隨機抖動**，讓到期時間分散。→ [[50-caching]]

</details>

**18. 🔵 Redis 掛掉時，你的服務應該怎樣？**

<details><summary>答案</summary>

**降級但仍可用**——快取不可用時直接查資料庫（可能變慢），而不是整個服務失敗。快取是加速層，不該是可用性的必要條件。要為此明確設計超時與 fallback。→ [[50-caching]]

</details>

**19. 🔴 應用內的背景排程（例如每小時跑一次），部署成 3 個副本會怎樣？**

<details><summary>答案</summary>

**跑三次。** 每個副本都有自己的排程器。解法是 leader election、外部化成 CronJob、或用分散式鎖。這是「本機開發沒事、上叢集就重複」的經典案例。→ [[51-background-jobs]]

</details>

**20. 🔴 CronJob 的時區預設是什麼？**

<details><summary>答案</summary>

依叢集元件的時區（通常是 UTC），**不是你的本地時區**。「每天凌晨 2 點」寫下去可能變成上午 10 點跑。新版有 `timeZone` 欄位可明確指定，但要確認叢集版本支援。→ [[51-background-jobs]]

</details>

**21. 🔵 CronJob 錯過了執行時間會怎樣？**

<details><summary>答案</summary>

取決於 `startingDeadlineSeconds` 與錯過的次數。錯過太多次時 controller 會停止嘗試並記錄錯誤——**而這個狀況不會有告警，除非你自己加**。→ [[51-background-jobs]]

</details>

**22. 🔴 上一次的 CronJob 還沒跑完，下一次就到了，預設會怎樣？**

<details><summary>答案</summary>

**預設允許重疊執行**（`concurrencyPolicy: Allow`）。長時間任務會累積成多個同時在跑，互相搶資源或造成資料衝突。要明確設成 `Forbid` 或 `Replace`。→ [[51-background-jobs]]

</details>

**23. 🔵 長時間的批次任務怎麼設計才不怕被中斷？**

<details><summary>答案</summary>

**分批處理 + 可續跑**：不要一次撈全表，記錄處理進度，讓中斷後能從斷點繼續。K8s 上的 Pod 隨時可能被驅逐或重排，所以「不會被打斷」不是可以依賴的假設。→ [[51-background-jobs]]

</details>

---

## 三、儲存、設定與開發體驗（附錄 AD、AE、AF）

**24. 🔴 為什麼使用者上傳的檔案不該放 PVC？**

<details><summary>答案</summary>

PVC 多半不支援多節點同時寫、跨區受限、擴容麻煩、備份與生命週期管理都要自己做。**物件儲存才是這件事的正確工具**。PVC 適合的是單一 Pod 的工作區與有狀態服務的資料目錄。→ [[52-file-and-object-storage]]

</details>

**25. 🔵 為什麼上傳與下載不該經過應用？**

<details><summary>答案</summary>

大檔會佔滿應用的記憶體、連線與頻寬，並被 Ingress 的 body 大小限制擋住。正解是**預簽名 URL 讓瀏覽器直接跟物件儲存往來**，應用只負責發放授權。→ [[52-file-and-object-storage]]

</details>

**26. 🔴 用預簽名 URL 直傳，安全上要注意什麼？**

<details><summary>答案</summary>

URL 要**短效**、限定方法與路徑、限制大小與型別；並且要記得**拿到 URL 的人就能上傳**，所以發放前要做完授權檢查。→ [[52-file-and-object-storage]]

</details>

**27. 🟢 為什麼不該用 git 分支來管理環境？**

<details><summary>答案</summary>

分支會分岔、會遺漏 cherry-pick、會讓「哪個環境有哪個修正」變得無法回答。正解是**同一個分支、用 overlay／values 區分環境**。→ [[53-configuration-management]]

</details>

**28. 🔴 設定變更的四道防護是什麼？**

<details><summary>答案</summary>

schema 驗證（CI 就擋）→ 啟動時驗證（壞設定進不了叢集）→ 漸進生效（不要一次全套用）→ 可回滾。**其中「啟動時驗證」最容易被跳過，但它是防止壞設定擴散到所有副本的關鍵。**→ [[53-configuration-management]]

</details>

**29. 🔵 「熱重載」的真相是什麼？**

<details><summary>答案</summary>

ConfigMap 更新到掛載檔案更新有延遲，而且**應用要自己監看檔案變化才會生效**；用環境變數注入的設定則完全不會熱重載。要熱重載必須是應用刻意支援的行為，不是 K8s 自動給的。→ [[53-configuration-management]]

</details>

**30. 🔵 Inner loop 變慢的根本原因是什麼？**

<details><summary>答案</summary>

從「改一行程式」到「看到結果」中間多了建置映像、推送、拉取、重新排程等步驟。**每個步驟都很合理，加起來就從幾秒變成幾分鐘**，而開發者一天要做幾十次。→ [[54-developer-experience]]

</details>

**31. 🔴 團隊層面最重要的開發體驗原則是什麼？**

<details><summary>答案</summary>

**不要讓每個開發者都必須懂 K8s。** 平台該提供讓人不必理解叢集也能開發的路徑（[[37-platform-engineering]] 的 golden path）。要求所有人都精通 K8s 是把平台的複雜度轉嫁出去。→ [[54-developer-experience]]

</details>

---

## 四、日誌、前端與資料庫連線（附錄 AG、AH、AI）

**32. 🔴 日誌的三種用途分別是什麼？為什麼要分開？**

<details><summary>答案</summary>

**除錯**（高細節、短保留）、**監控告警**（結構化、可聚合）、**稽核**（不可竄改、長保留）。三者的保留期、儲存位置與成本結構完全不同，混在一起會同時付出「保留太久」與「保留不夠」兩種代價。→ [[55-logging-strategy]]

</details>

**33. 🔴 什麼絕對不該記進日誌？**

<details><summary>答案</summary>

密碼、token、完整的個資、信用卡號、以及完整的請求內文（很可能含上述任一）。**日誌是最常被忽略的個資外洩管道**，且它通常保留很久、很多人有權限看。→ [[55-logging-strategy]]、[[61-compliance-and-audit]]

</details>

**34. 🔵 日誌成本主要來自哪裡？**

<details><summary>答案</summary>

不是儲存，而是**索引**。全文索引每一個欄位的成本遠高於存放原始文字，這也是 Loki 這類「只索引 label」的方案成本差異的來源。→ [[55-logging-strategy]]

</details>

**35. 🔴 前端部署最經典的事故是什麼？**

<details><summary>答案</summary>

**舊 JS 檔案 404。** 使用者開著舊版頁面，新版部署後把舊的 hash 檔名資產刪掉了，於是使用者切換路由時載入失敗，畫面直接壞掉——**而且他不會自動重整**。→ [[56-frontend-deployment]]

</details>

**36. 🔵 為什麼滾動更新會讓「舊 JS 404」更嚴重？**

<details><summary>答案</summary>

更新期間新舊副本並存，使用者的請求可能一下打到新的、一下打到舊的，拿到不一致的資產組合。**前端的版本切換本質上不是原子的。**→ [[56-frontend-deployment]]

</details>

**37. 🔴 前端的快取標頭該怎麼設？**

<details><summary>答案</summary>

`index.html` **不快取**（每次都要拿到最新的資產清單），帶 hash 的靜態資產設**長效不可變**（內容變了檔名就變）。設反了會造成「更新了但使用者看不到」或「每次都重新下載」。→ [[56-frontend-deployment]]

</details>

**38. 🔵 純 SPA 需不需要跑在 K8s 上？**

<details><summary>答案</summary>

**通常不需要。** 一堆靜態檔案放 CDN／物件儲存更簡單、更快、更便宜。放進 K8s 只是多養一個 Pod。除非有 SSR 或需要與叢集內服務同源。→ [[56-frontend-deployment]]

</details>

**39. 🔴 資料庫實際連線數怎麼算？**

<details><summary>答案</summary>

**Pod 數 × 每個 Pod 的連線池大小。** 這是乘法不是加法——HPA 擴到 20 個副本、每個池 100，就是 2000 條連線，遠超多數資料庫的上限。**擴容這個動作本身會壓垮資料庫。**→ [[57-database-connections]]、[[practice-5-database-and-state]]

</details>

**40. 🔵 連線池中介（如 pgbouncer）該不該用？**

<details><summary>答案</summary>

**多數團隊不需要**——先把每個 Pod 的池調小通常就解決了。中介多一個要維運、要高可用的元件，而且不同 pooling 模式對交易與 prepared statement 的支援不同，用錯會有難查的錯誤。→ [[57-database-connections]]

</details>

**41. 🔴 連線在 K8s 環境常見的殺手是什麼？**

<details><summary>答案</summary>

**NAT／防火牆的閒置逾時**。連線池裡的閒置連線被中間設備默默斷掉，應用拿去用才發現壞了。症狀是間歇性的、與流量低谷相關。要靠連線驗證與 keepalive 處理。→ [[57-database-connections]]

</details>

---

## 五、邊界、Gateway 與 SLO（附錄 AJ、AR、AP）

**42. 🔴 認證該放在哪一層？**

<details><summary>答案</summary>

**分層**：邊界層驗「你是誰」（簽章、有效期）→ 401；應用層驗「你能做什麼」→ 403。**應用層不能省**，因為叢集內其他 Pod 可以直接打 Service 繞過邊界。→ [[58-api-gateway-and-edge]]

</details>

**43. 🔵 多副本下的限流為什麼不準？**

<details><summary>答案</summary>

每個副本各自計數。設「每秒 100 次」而有 5 個副本，實際上限變成 500。要準確就得用共用的計數儲存，但那會增加延遲與一個依賴。→ [[58-api-gateway-and-edge]]

</details>

**44. 🔵 為什麼對外與對內的入口要分開？**

<details><summary>答案</summary>

安全需求與流量特性完全不同：對外要 WAF、嚴格限流、更保守的逾時；對內要低延遲、寬鬆限流。混在一起會讓你只能取兩者的交集，兩邊都不合適。→ [[58-api-gateway-and-edge]]

</details>

**45. 🔴 Ingress 最根本的結構性問題是什麼？**

<details><summary>答案</summary>

**沒有角色分離**——TLS 憑證與路由規則在同一個物件裡，於是只能在「應用團隊也能改 TLS」與「平台團隊變成瓶頸」之間二選一。這是資料模型層面的限制，不是設定問題。→ [[66-ingress-to-gateway-api]]

</details>

**46. 🔵 Gateway API 的核心價值是什麼？（不是「功能比較多」）**

<details><summary>答案</summary>

**功能寫在規格裡而不是 annotation 裡**，所以換 controller 不用重寫路由；以及**三層角色分離**（GatewayClass／Gateway／HTTPRoute）讓 RBAC 對得上真實分工。→ [[66-ingress-to-gateway-api]]

</details>

**47. 🔴 HTTPRoute 建好了但完全沒反應，先看什麼？**

<details><summary>答案</summary>

**看三個 condition**：`Accepted`、`ResolvedRefs`、`Programmed`。最常見的是 `ResolvedRefs: false`——跨 namespace 引用忘了建 `ReferenceGrant`，而它**不會報錯，只是靜默不生效**。→ [[66-ingress-to-gateway-api]]

</details>

**48. 🔵 遷移到 Gateway API 該怎麼進行？**

<details><summary>答案</summary>

**並行，不要規劃切換日**：兩個 controller 各有對外位址，用 DNS 逐服務切，舊路由留著當回滾路徑。先搬沒有 annotation 的簡單服務。→ [[66-ingress-to-gateway-api]]

</details>

**49. 🔴 `CPU > 80%` 這種告警為什麼是壞的？**

<details><summary>答案</summary>

它問的是「零件如何」而非「使用者受不受影響」，因此**同時造成誤報與漏報**——CPU 90% 但請求都正常是誤報，CPU 20% 但下游卡死是漏報。而誤報累積會讓人忽略告警，於是漏報那次也沒人理。→ [[64-slo-and-alerting]]

</details>

**50. 🔴 99.9% 的 SLO，每 30 天可以壞多久？99.99% 呢？**

<details><summary>答案</summary>

99.9% ≈ **43 分鐘**；99.99% ≈ **4 分 19 秒**。後者代表**人為介入來不及**——那是「架構上不存在需要人介入的故障模式」的要求，不是更努力就能達成。→ [[64-slo-and-alerting]]

</details>

**51. 🔵 延遲 SLI 為什麼要寫成比例而不是 P95？**

<details><summary>答案</summary>

「P95 < 300ms」接不上錯誤預算的算術；「99% 的請求在 300ms 內完成」才是一個可以計算預算消耗的比例。這是 SLO 實作最常卡住的一步。→ [[64-slo-and-alerting]]

</details>

**52. 🔴 燃燒率告警為什麼要用兩個時間窗？**

<details><summary>答案</summary>

**長窗判斷「嚴不嚴重」，短窗判斷「還在不在發生」。** 只有短窗會因尖峰誤報；只有長窗則恢復後還會繼續響很久。兩者同時成立才告警。→ [[64-slo-and-alerting]]

</details>

**53. 🔵 哪一類「原因型」告警仍然該叫醒人？**

<details><summary>答案</summary>

**迫近耗盡型**——磁碟四小時內會滿、憑證三天後過期。判準是「它會在人來得及反應的時間內變成使用者可見的故障，而且晚了就來不及」。→ [[64-slo-and-alerting]]

</details>

**54. 🟢 檢驗一條告警該不該叫人，問什麼問題？**

<details><summary>答案</summary>

**「收到之後我要立刻做什麼？」** 答不出具體動作、或答案是「先看一下」，就不該叫人。→ [[64-slo-and-alerting]]

</details>

---

## 六、合規、CI 與 Registry（附錄 AM、AO、AT）

**55. 🟢 安全與合規的差別是什麼？**

<details><summary>答案</summary>

安全問「**有沒有做**」，合規問「**能不能證明有做**」。多數團隊的合規成本集中在後者——證據沒整理，於是稽核季花兩週截圖。→ [[61-compliance-and-audit]]

</details>

**56. 🔴 GitOps 怎麼滿足「職務分離」？前提是什麼？**

<details><summary>答案</summary>

PR review 讓執行者與核准者分離、git 歷史提供變更紀錄。**前提是人類身分在生產環境只有讀取權，寫入權只給 ArgoCD**——如果開發者仍能 `kubectl apply`，職務分離只是紙上的。→ [[61-compliance-and-audit]]

</details>

**57. 🔵 變更管理在 GitOps 下還有哪三個漏洞？**

<details><summary>答案</summary>

手動 `kubectl`（用 `selfHeal` 讓它技術上做不到）、緊急變更（要有事後補登流程）、**平台層變更**（升級、政策調整常不在 manifest repo 裡）。→ [[61-compliance-and-audit]]

</details>

**58. 🔴 個資盤點最常漏掉哪兩個位置？**

<details><summary>答案</summary>

**日誌與備份。** 只列資料庫的盤點，一被問「那日誌裡有沒有」就沒有答案；而刪除請求在備份保留期內基本無解，處理方式要事先決定。→ [[61-compliance-and-audit]]

</details>

**59. 🔴 CI runner 掛載節點的 Docker socket，風險是什麼？**

<details><summary>答案</summary>

**等於把整台節點的控制權交出去**——能對 daemon 下指令就能起特權容器、掛節點根目錄、讀其他容器的檔案。而且 **RBAC 擋不住**，因為整件事發生在節點的 daemon 層，API Server 看不到。→ [[63-ci-in-cluster]]

</details>

**60. 🔴 CI 該不該有叢集的寫入權限？**

<details><summary>答案</summary>

**不該。** 職責到「推映像 + 更新 manifest 版本號」為止，部署由 ArgoCD 拉。否則**任何能改 workflow 檔的人都能直接改生產**——而 workflow 檔就在 repo 裡。→ [[63-ci-in-cluster]]

</details>

**61. 🔵 怎麼判斷你的 CI 快取是「快取」還是「隱藏狀態」？**

<details><summary>答案</summary>

**清空它重跑一次，結果要不變。** 結果不同的話那不是快取，是不可重現的隱藏狀態，而你的 CI 已經壞了，只是還沒被發現。→ [[63-ci-in-cluster]]

</details>

**62. 🔵 為什麼 CI runner 要「用完即丟」？**

<details><summary>答案</summary>

不只是衛生問題，更是**安全問題**：常駐 runner 上，一個惡意 job 可以留下東西等下一個高權限 job 執行。用完即丟從結構上消除這個攻擊面。→ [[63-ci-in-cluster]]

</details>

**63. 🔴 registry 掛掉時，你的監控會告訴你嗎？**

<details><summary>答案</summary>

**通常不會——監控會是綠的。** 現有 Pod 都在跑、SLO 沒變化。問題會在下一次需要拉映像時爆發：擴容、滾動更新、**節點故障後的重排**，而最後那個正是你最需要自我修復的時刻。→ [[68-registry-operations]]

</details>

**64. 🔴 `imagePullPolicy` 沒明寫時，預設值是什麼？**

<details><summary>答案</summary>

**依 tag 決定**：`latest`（或沒寫 tag）→ `Always`；其他 tag → `IfNotPresent`。後者造成一類極難查的 bug——版本 tag 被覆寫，但已有舊映像的節點不會去拉，**於是不同節點跑著不同內容，而所有 YAML 看起來一模一樣**。→ [[68-registry-operations]]

</details>

**65. 🔴 為什麼 GitOps 下 `latest` 特別壞？**

<details><summary>答案</summary>

ArgoCD 比對期望與實際狀態，而寫著 `latest` 的期望狀態**永遠是「同步的」**，即使內容換了三次。**它讓 git 不再是真相來源。**→ [[68-registry-operations]]、[[11-argocd]]

</details>

**66. 🔴 清理舊映像前一定要做什麼？**

<details><summary>答案</summary>

**先掃描叢集實際在用的映像**（含 `initContainers`、`ephemeralContainers`、以及保留的回滾歷史）。刪到正在用的映像**當下毫無症狀**，直到節點重啟或 Pod 重排才爆——而那時已經回不去。→ [[68-registry-operations]]

</details>

---

## 七、規模、決策與接手（附錄 AN、AS、AQ）

**67. 🔴 StatefulSet 沒有給你的五件事是什麼？**

<details><summary>答案</summary>

備份、選主與故障轉移、資料一致性、版本升級的資料遷移、擴縮容的資料重分布。**它只是讓資料庫「有可能被管理」的最低基礎，不是解決方案。**→ [[62-stateful-workloads-decision]]

</details>

**68. 🔴 判斷有狀態服務能不能進叢集，最好用的單一問題是什麼？**

<details><summary>答案</summary>

**「資料掉了能不能重建？」** 可重建（快取、可重放的佇列）風險低；唯一真相（業務資料庫、使用者上傳）風險高。注意中間地帶：**Redis 當快取可重建，當 session store 就不可重建**。→ [[62-stateful-workloads-decision]]

</details>

**69. 🔴 etcd 滿了會怎樣？**

<details><summary>答案</summary>

**整個叢集變成唯讀——連刪東西都不行**，因為刪除也是一次寫入。這是少數會讓你完全動彈不得的故障，所以「etcd 大小接近配額」必須是會叫人的告警。→ [[67-scaling-limits]]

</details>

**70. 🔴 剛接手一座別人建的叢集，最大的風險是什麼？第一週該做什麼？**

<details><summary>答案</summary>

**最大的風險不是你不會的東西，是你不知道它存在的東西。** 第一週**只看不動**（除非有正在燒的火）：跑盤點指令、找出對外暴露面、找出每個 namespace 的 owner、抄下所有憑證到期日。特別注意失效的 admission webhook——它會讓 `apply` 全面失敗而訊息不指向它。→ [[65-inheriting-a-cluster]]

</details>

---

## 紅色警戒清單

全部答對才算安全。這 10 題是本份裡「答錯會造成不可逆損失」的核心：

| # | 題目 | 一句話答案 |
| --- | --- | --- |
| 11 | 至少一次的語意要求什麼 | **處理必須冪等** |
| 19 | 應用內排程 × 3 副本 | **會跑三次** |
| 22 | CronJob 重疊 | 預設**允許重疊**，要設 `Forbid`／`Replace` |
| 39 | 資料庫連線數 | **Pod 數 × 池大小**，擴容會壓垮 DB |
| 50 | 99.99% 的意義 | **每月 4 分鐘，人為介入來不及** |
| 59 | 掛 Docker socket | **交出整台節點，RBAC 擋不住** |
| 63 | registry 掛掉 | **監控是綠的**，節點故障時才爆 |
| 66 | 清理映像 | **刪到在用的當下無症狀，重排時才爆** |
| 67 | StatefulSet 的邊界 | **備份／選主／一致性全都沒有** |
| 69 | etcd 滿了 | **整個叢集唯讀，連刪都不行** |

## 連結

- [[16-self-assessment]] — 附錄 A：正文 16 章的 144 題
- [[46-advanced-self-assessment]] — 附錄 X：實戰篇與附錄 E–W 的 75 題
- [[26-lab-drills]] — 附錄 D：答錯的去做對應實驗
- [[31-glossary]] — 附錄 I：術語查詢
- [[60-advanced-cheatsheet]] — 附錄 AL：進階速查表
- [[k8s-mastery]] — 教材總目錄
