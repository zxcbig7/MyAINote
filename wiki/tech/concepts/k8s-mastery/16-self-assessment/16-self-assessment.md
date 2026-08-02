---
type: concept
domain: tech
tags: [kubernetes, k8s, self-assessment, quiz, review, interview]
sources: []
created: 2026-08-01
updated: 2026-08-01
---

# 附錄 A：自我檢測題庫

這份題庫是整套雲原生部署教材（Docker → Kubernetes → Helm／ArgoCD → Prometheus／ELK）的最後一道關卡。讀懂一章跟「答得出來」是兩件事：眼睛掃過文字時，大腦會有一種「這我懂」的錯覺，但錯覺撐不住同事在茶水間隨口丟來的一句「欸那個 RWO 是不是只能一個 Pod 掛」。真正的驗收方式，是蓋住答案，自己先講一遍——講得完整、講得出「為什麼」，才算真的吸收；卡住的地方，就是要回頭翻書的地方。

每一題都標了三級難度。🟢 基礎題確認你記得住核心事實與定義，這是及格線，讀完一章這些題目應該都答得出來；🔵 進階題要求你不只記得定義，還理解機制怎麼運作、為什麼要這樣設計，這是能不能在面試裡講出「所以然」的分水嶺；🔴 專家題大多是陷阱、反直覺的細節，或需要跨小節串連知識的情境診斷，這些題目就算現在答不出來也不用挫折——它們的目的正是替你標出「多數人會在這裡跌倒」的位置，先知道自己不知道，比什麼都不知道好得多。

建議的使用節奏：讀完一章立刻蓋答案測一次，錯的地方馬上回去對應小節重讀；一週之後不看書再測一次同一章，這次答得出來的，才是真正進了長期記憶而不是短期印象。距離「完全不會被問倒」最近的路，不是把十六章再讀一次，而是把這份題庫錯過的地方，回頭補到答對為止。

## 第 00 章｜Docker 基礎

容器技術是整套教材的地基，這一章的題目故意把重點放在「原理」而非「指令背誦」：namespace 和 cgroup 怎麼分工、layer 為什麼要用 Copy-on-Write、以及那些長得很像、很容易被搞混的指令組合（CMD vs ENTRYPOINT、COPY vs ADD、ARG vs ENV）。這些底層原理沒搞懂，後面十五章談到「Pod 共享 network namespace」「容器怎麼被排到 Node 上」時都會少一塊地基。

**Q1.** 🟢 三大 Linux 基石中，namespace 負責什麼、cgroup 負責什麼？

<details>
<summary>看答案</summary>

namespace 負責「隔離視野」，讓程序以為自己獨佔一台機器的 PID、網路、掛載點等資源；cgroup 負責「限制與計量」，控制程序實際能用多少 CPU、記憶體等資源。兩者合作才構成容器的假象：程序看到的世界被 namespace 裁切過，能用的資源額度被 cgroup 卡住。

→ 詳見 [[00-docker-foundations]]
</details>

**Q2.** 🟢 Image 的每一層為什麼要設計成唯讀，再靠 Copy-on-Write 才能修改？

<details>
<summary>看答案</summary>

因為唯讀的 layer 可以被多個 container 安全共用，不會互相污染，也節省磁碟空間；當某個 container 執行中要修改檔案時，才把該檔案複製一份到最上層專屬的可寫層再修改，其餘沒動到的檔案仍指向共用的唯讀層。這正是 Copy-on-Write 的意義：只有真的要寫入時才複製，不寫就不用複製。

→ 詳見 [[00-docker-foundations]]
</details>

**Q3.** 🟢（辨析）CMD 和 ENTRYPOINT 是二選一的關係嗎？

<details>
<summary>看答案</summary>

不是，兩者通常合併使用。ENTRYPOINT 定義容器啟動時一定會執行的主程式，CMD 則提供可以被 `docker run` 後面的參數覆蓋的預設參數。如果只寫 CMD 不寫 ENTRYPOINT，整段指令都可能被使用者的參數整個覆蓋掉；兩者都寫才能兼顧「行為固定」與「參數可調整」。

→ 詳見 [[00-docker-foundations]]
</details>

**Q4.** 🟢（辨析）ARG 和 ENV 都能定義變數，差別是什麼？

<details>
<summary>看答案</summary>

ARG 只在建置期間存在，image 建置完成後容器執行期完全看不到它；ENV 會寫進 image 的 metadata，容器執行時依然存在，也能被 `docker run -e` 覆蓋。建置階段的一次性參數（版本號、下載連結）用 ARG，執行期需要讀取的設定用 ENV。

→ 詳見 [[00-docker-foundations]]
</details>

**Q5.** 🔵（辨析）COPY 和 ADD 差在哪？什麼時候不該用 ADD？

<details>
<summary>看答案</summary>

ADD 比 COPY 多了兩個「魔法」：自動解壓縮本地 tar 檔、支援直接抓取遠端 URL；這些魔法行為不透明，容易造成非預期結果，例如以為只是單純複製檔案，結果自動幫你解壓縮了。除非明確需要自動解壓本地 tar 檔，否則官方建議一律用行為單純、可預期的 COPY。

→ 詳見 [[00-docker-foundations]]
</details>

**Q6.** 🔵（情境診斷）同事抱怨他的 Dockerfile 每次改一行程式碼、`docker build` 就要重跑十分鐘，你會請他先檢查 Dockerfile 裡指令的順序，為什麼？

<details>
<summary>看答案</summary>

因為 Docker 對每一層 layer 都做快取，只要某一層的指令與輸入內容沒變就直接複用快取，但一旦有一層快取失效，其後所有層都要重建。如果把常變動的「複製原始碼」寫在前面、把不常變動的「安裝套件」寫在後面，每次改一行程式碼就會讓後面所有層全部重建；正確順序應該是不常變的放前面、常變的放後面，讓大部分建置都能命中快取。

→ 詳見 [[00-docker-foundations]]
</details>

**Q7.** 🔵 多階段建置（multi-stage build）只是讓 Dockerfile 檔案變短嗎？

<details>
<summary>看答案</summary>

不是，真正目的是縮小最終 image 的體積與攻擊面。build 階段可以安裝完整的編譯工具鏈、暫存檔與原始碼，但最終只用 `COPY --from` 把編譯產物複製到乾淨的執行期 image（甚至 distroless），建置工具、原始碼、快取都不會出現在最終產物裡，體積變小、可被利用的漏洞也變少。

→ 詳見 [[00-docker-foundations]]
</details>

**Q8.** 🔴（情境診斷）同事說「我們用 Docker 建的 image，K8s 1.24 之後把 dockershim 拿掉了，是不是不能跑了？」你會怎麼回答？

<details>
<summary>看答案</summary>

不會受影響。dockershim 只是 kubelet 用來跟 Docker Engine 溝通的相容層，被移除的是「執行期整合」，不是「image 格式」。Docker 建出來的 image 遵循 OCI 標準，只要節點上有支援 CRI 的執行期（containerd、CRI-O）就能正常拉取並執行，跟 image 是用什麼工具建的完全無關。

→ 詳見 [[00-docker-foundations]]
</details>

**Q9.** 🔴（情境診斷）同事的 image 從兩百 MB 建到快兩 GB，你會先問他 Dockerfile 裡哪幾件事？

<details>
<summary>看答案</summary>

先問三件事：有沒有用多階段建置把編譯工具留在 build 階段而不帶進最終 image；base image 選的是不是臃腫的完整發行版而非 alpine 或 distroless；有沒有先裝套件又清快取但清除動作沒放在同一個 `RUN` 層裡（例如 `apt-get install` 之後另起一行才 `rm -rf`，這樣舊層的體積早已定型，之後刪除也不會讓 image 變小，一定要跟安裝寫在同一層才有效）。

→ 詳見 [[00-docker-foundations]]
</details>

## 第 01 章｜為什麼需要 Kubernetes

這一章的題目測的不是「K8s 有哪些功能」，而是「你能不能講清楚它到底解決了什麼問題、又付出了什麼代價」。能不能在同事或老闆丟出「聽說 K8s 很潮，我們也上一套」這種提案時，冷靜地問出對的問題，是這一章真正的驗收標準。

**Q1.** 🟢 從單機部署到容器編排，大致經過哪些演進階段？

<details>
<summary>看答案</summary>

大致是：單機直接跑程式，到用虛擬機器切割資源，到用容器解決「在我機器上可以跑」的環境一致性問題，最後因為容器數量一多、手動管理存活與擴縮太累，於是出現編排系統把這些操作自動化。每個階段都是為了解決前一階段留下的新問題才出現的。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q2.** 🟢 有了 Docker，為什麼還不夠？舉出編排要解決的其中兩個問題。

<details>
<summary>看答案</summary>

例如容器掛掉了該由誰負責重啟（自我修復），以及流量進來要分給哪一個容器實例（服務發現與負載平衡）。Docker 只解決「怎麼打包、怎麼跑單一容器」，沒有回答「一大群容器在一群機器上怎麼互相協調」。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q3.** 🟢（辨析）「宣告式」和「命令式」部署差在哪？

<details>
<summary>看答案</summary>

命令式是一步步下指令告訴系統怎麼做；宣告式是只描述「最終想要的狀態」，交給系統自己想辦法達成並持續維持。K8s 的 YAML 就是宣告式：你寫「我要三個副本」，怎麼建立、怎麼修復都不用你操心。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q4.** 🔵 K8s 的設計哲學裡，宣告式加上 controller 模式為什麼是它勝出的關鍵之一？

<details>
<summary>看答案</summary>

宣告式加上不斷比對「期望狀態」與「實際狀態」的 controller，讓系統天生具備自我修復能力，不需要人工介入；同時 K8s 用一致的 API 物件模型描述所有資源，生態系可以在此之上疊加擴充（CRD、Operator），這種可擴充性是它相對其他編排系統勝出的重要原因。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q5.** 🔵（辨析）K8s 之外常見的選型還有哪些？各自適合什麼場景？

<details>
<summary>看答案</summary>

Docker Swarm 較簡單但生態與功能已停滯發展；Nomad 更輕量、可跨排程虛擬機與容器混合的工作負載；雲端全代管的 PaaS（Cloud Run、Fargate、ECS）省去叢集維運但彈性與可攜性較低。選型應該回到「團隊需要多少自訂彈性」與「願意花多少維運成本」的取捨，而不是單純比誰的功能表比較長。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q6.** 🔴（設計決策）什麼情況下你會建議團隊不要導入 K8s？

<details>
<summary>看答案</summary>

例如團隊規模小、服務數量少，維運人力撐不起 K8s 的學習曲線與維運成本；或工作負載單純到用 PaaS 就能滿足，導入 K8s 只是徒增複雜度而沒有對應的彈性收益。K8s 的價值要在規模與複雜度夠高時，才會超過它本身的維運成本，否則就是拿大砲打小鳥。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q7.** 🔴（情境診斷）老闆說「聽說 K8s 很潮，我們也上一套」，你會先問哪些問題？

<details>
<summary>看答案</summary>

先問目前有多少個服務、部署頻率多高，以及現在具體的痛點是什麼——是擴縮容困難、部署不一致，還是缺乏自我修復；再問團隊有沒有人力學習與維運 K8s。如果痛點用更輕量的方案就能解決，或團隊撐不起維運負擔，導入 K8s 反而會製造新問題而不是解決舊問題。

→ 詳見 [[01-why-kubernetes]]
</details>

**Q8.** 🟢 minikube 這種本機練習環境和正式環境的落差主要在哪？

<details>
<summary>看答案</summary>

minikube 通常是單節點、資源有限，網路與儲存都是簡化模擬（例如用 hostPath 代替雲端硬碟），沒有真正的高可用 control plane、沒有真實的雲端 LoadBalancer，也不會遇到多節點網路的複雜狀況。在 minikube 上能跑，不代表正式環境的多節點、高可用場景一定也沒問題。

→ 詳見 [[01-why-kubernetes]]
</details>

## 第 02 章｜叢集內部運作

這一章的核心是拆解「`kubectl apply` 之後到底發生了什麼事」這條完整的故事線。多數人對 K8s 的誤解都出在同一個地方：以為 apiserver 會主動把 Pod「推」到某台機器上。這一章的題目會反覆逼你回答「到底是誰在主動做事」，把這條 pull-based 的因果鏈講清楚，才算真的懂了叢集怎麼運轉。

**Q1.** 🟢 Control Plane 的四個核心元件分別是什麼？

<details>
<summary>看答案</summary>

kube-apiserver 是唯一對外窗口，所有請求都要經過它；etcd 是唯一的資料儲存，記錄叢集全部狀態；kube-scheduler 決定 Pod 該排到哪個 Node；kube-controller-manager 跑各種 controller，持續讓實際狀態趨近期望狀態。四者分工明確、互不直接溝通，全部透過 apiserver 交換資訊。

→ 詳見 [[02-cluster-internals]]
</details>

**Q2.** 🟢 Node 上的三個元件分別做什麼？

<details>
<summary>看答案</summary>

kubelet 是節點上的代理人，負責跟 apiserver 溝通、確保指派給它的 Pod 真的在跑；kube-proxy 維護節點上的網路規則，讓 Service 的流量能轉發到正確的 Pod；container runtime 實際負責拉取 image、啟動與停止容器。

→ 詳見 [[02-cluster-internals]]
</details>

**Q3.** 🔵（機制原理）`kubectl apply` 之後，Pod 是被 apiserver 主動推派到 Node 上的嗎？

<details>
<summary>看答案</summary>

不是。整個系統是 pull-based：apply 只是把 Deployment 物件寫進 etcd；controller-manager 看到差異後建立 Pod 物件（此時還沒有 nodeName）；scheduler watch 到未綁定的 Pod 後幫它決定要去哪個 Node，寫回 nodeName；該 Node 上的 kubelet watch 到有 Pod 被指派給自己，才主動去拉 image、建立容器。全程沒有任何元件把東西「推」給 Node，都是各自 watch 後主動處理自己負責的那一段。

→ 詳見 [[02-cluster-internals]]
</details>

**Q4.** 🟢（情境診斷）同事問你「為什麼 K8s 是 pull-based 而不是 push-based？這樣設計有什麼好處？」

<details>
<summary>看答案</summary>

因為所有元件（scheduler、controller、kubelet）都是主動 watch apiserver、發現該做的事再自己動手，apiserver 本身不會主動呼叫 kubelet 下指令。好處是解耦：任何元件重啟或斷線，只要重新 watch 就能接續工作，不會因為某次「推送」遺失而狀態不一致。

→ 詳見 [[02-cluster-internals]]
</details>

**Q5.** 🟢 Reconciliation Loop 是什麼？為什麼系統會「自己修復自己」？

<details>
<summary>看答案</summary>

Reconciliation Loop 是每個 controller 不斷執行的迴圈：讀取期望狀態、讀取實際狀態、比較兩者差異、採取行動讓實際狀態趨近期望狀態，然後無限重複。例如 Pod 被刪掉，ReplicaSet controller 下一輪迴圈發現實際數量少於期望數量，就會自動補建一個，這就是「自我修復」的來源，不需要人工介入。

→ 詳見 [[02-cluster-internals]]
</details>

**Q6.** 🔵（情境診斷）同事問「為什麼 K8s 元件之間是用 watch 而不是輪詢？跟 resourceVersion 又有什麼關係？」

<details>
<summary>看答案</summary>

輪詢需要不斷發請求問「有沒有變化」，在大型叢集裡會對 apiserver 造成巨大負擔；watch 是建立一條長連線，由 apiserver 有變化時主動推送事件，配合 informer 在本地維護一份快取，大幅減少重複查詢。resourceVersion 則像一個單調遞增的版本戳記，watch 斷線重連時可以從上次的 resourceVersion 繼續接收後續事件，避免遺漏或重複處理。

→ 詳見 [[02-cluster-internals]]
</details>

**Q7.** 🔵（辨析）spec 和 status 的分工是什麼？誰可以寫哪一個？

<details>
<summary>看答案</summary>

spec 是使用者或上層物件宣告的期望狀態，例如「我要三個副本」，應該只由使用者或管理該資源的上層 controller 修改；status 是系統回報的實際觀測狀態，例如「目前有兩個副本就緒」，只應該由對應的 controller 或 kubelet 寫入。使用者手動改 status 通常會在下一輪 reconcile 被蓋掉，因為它反映的是真實觀測結果而非期望。

→ 詳見 [[02-cluster-internals]]
</details>

**Q8.** 🟢 etcd 在整個架構裡扮演什麼角色？

<details>
<summary>看答案</summary>

etcd 是叢集唯一的「真實來源」，一個分散式的 key-value store，儲存了所有物件的 spec 與 status。除了 apiserver 之外，沒有其他元件會直接讀寫 etcd，所有存取都要經過 apiserver 這道關卡。

→ 詳見 [[02-cluster-internals]]
</details>

**Q9.** 🔴（情境診斷）同事說「etcd 掛了，但 apiserver 好像還活著，`kubectl get pod` 卻一直逾時」，這代表什麼？

<details>
<summary>看答案</summary>

代表 apiserver 進程本身還在跑，但它完全依賴 etcd 才能讀寫任何物件資料；etcd 不可用時，apiserver 收到請求會因為連不上後端儲存而逾時或回錯，看起來「活著」但實質上無法服務任何需要讀寫狀態的請求。這也是為什麼 etcd 通常被視為叢集裡最關鍵、最需要優先復原的元件。

→ 詳見 [[02-cluster-internals]]
</details>

## 第 03 章｜API 與 YAML

YAML 檔案是每天都在寫的東西，但這一章要問的是「你真的懂它背後對應的 API 模型嗎」。GVK、apply 的兩代機制、annotation 的上限、YAML 本身的語言陷阱——這些都是那種「平常不會出事，一出事就是一場硬仗」的細節。

**Q1.** 🟢 GVK 和 GVR 分別代表什麼？兩者的差別是什麼？

<details>
<summary>看答案</summary>

GVK 是 Group、Version、Kind，用來描述「這是哪一種資源類型」，例如 `apps/v1 Deployment`；GVR 是 Group、Version、Resource，Resource 是 Kind 的複數小寫形式（例如 `deployments`），用在 API 路徑與 RESTful 操作上。Kind 是給人與物件辨識用的名詞，Resource 是給 URL 路徑用的集合名稱。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q2.** 🟢 為什麼 Pod、Service 這些核心資源的 apiVersion 只寫 `v1`，沒有 group 名稱？

<details>
<summary>看答案</summary>

因為它們屬於「core group」（又稱 legacy group），這是 K8s 最早期就存在的一組資源，為了相容性保留了沒有 group 前綴的寫法；後來新增的資源類型幾乎都歸屬於明確命名的 group（如 `apps`、`batch`、`networking.k8s.io`），只有 core group 是特例。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q3.** 🟢 `kubectl explain` 的用途是什麼？為什麼管理員該養成用它的習慣？

<details>
<summary>看答案</summary>

`kubectl explain` 可以直接查詢某個資源欄位的官方文件與型別說明，資料來源是叢集當前版本的 API schema，保證跟你正在操作的叢集版本一致，比對著網路上版本不明的範例更可靠，尤其在欄位命名記不清楚或不確定某欄位吃什麼型別時非常實用。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q4.** 🔵 API 版本從 alpha 到 GA 的演進規則是什麼？管理員要注意什麼？

<details>
<summary>看答案</summary>

大致順序是 alpha（可能隨時變動或消失，預設不啟用）到 beta（功能穩定但欄位可能微調，預設啟用）到 GA／stable（正式版，向下相容承諾）。管理員要注意的是：alpha／beta 版本可能在未來版本被棄用甚至移除，升級叢集前務必確認自己用的 apiVersion 是否會失效；同時 apiserver 有 discovery cache，安裝 CRD 或切換版本後有時需要等待或重新整理才能反映最新可用資源。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q5.** 🟢（辨析）labels 和 annotations 都是 key-value，差在哪裡？

<details>
<summary>看答案</summary>

labels 是用來被「選取」的，例如 Service 用 selector 找 Pod，因此有格式限制（DNS-1123）也會被索引；annotations 是純粹的描述性 metadata，不能被 selector 選取，但內容可以放更自由的資訊，例如工具產生的 checksum 或上次套用的完整設定。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q6.** 🔵（情境診斷）同事想把一整份憑證內容塞進 annotation，結果寫入失敗，你會怎麼跟他解釋？

<details>
<summary>看答案</summary>

K8s 對單一 annotation 的內容有 256KB 的上限，把大量資料、完整設定檔或憑證塞進 annotation 很容易超過限制導致寫入失敗。這種需求應該改用 ConfigMap 或 Secret 承載，annotation 只適合放小型的描述性 metadata，不該拿來當資料庫用。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q7.** 🔵（情境診斷）同事不確定該用 create 還是 apply 來套用他的 YAML，你會怎麼幫他分辨這幾個寫入動詞？

<details>
<summary>看答案</summary>

create 只能建立不存在的資源，資源已存在就報錯；replace 會用提供的完整內容整個覆蓋現有資源，沒寫到的欄位視同要清空；patch 只針對指定的欄位做局部修改；apply 是宣告式的三方合併，可以重複執行且能正確處理欄位的增刪。日常維運多半建議用 apply，因為它冪等又能安全地重複套用同一份 YAML。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q8.** 🔴（機制原理）client-side apply 和 server-side apply 的差別是什麼？field manager 衝突是怎麼發生的？

<details>
<summary>看答案</summary>

client-side apply 是 kubectl 在本地比對存在 annotation 裡的 last-applied-configuration 來算出差異，缺點是不同工具各自為政，容易互相覆蓋彼此的修改而不自知；server-side apply 則把「誰擁有哪個欄位」記錄在 apiserver 端的 managedFields，每個寫入者都有自己的 field manager 身分。當兩個不同的 field manager 想同時擁有同一個欄位、且沒有加 force，apiserver 會拒絕請求並回報衝突，逼你明確決定誰該贏，避免靜默互相覆蓋。

→ 詳見 [[03-api-and-yaml]]
</details>

**Q9.** 🔴（情境診斷）同事的 YAML 寫了 `enabled: no`，結果程式讀到的卻是布林值 `false` 而不是字串，這是什麼陷阱？

<details>
<summary>看答案</summary>

這就是有名的 Norway Problem：YAML 1.1 規格會把 `no`、`yes`、`on`、`off`、`NO`（挪威的 ISO 國別代碼）這類字串自動解析成布林值或做非預期轉換。凡是不想被誤判型別的字串，都應該明確加上引號（如 `"no"`），縮排也一律用空格、絕對不能混入 tab，否則會直接解析失敗。

→ 詳見 [[03-api-and-yaml]]
</details>

## 第 04 章｜工作負載

Pod 是最小單位，但幾乎沒有人會直接手寫裸 Pod——這一章的重點在於「為什麼」要疊上 Deployment、StatefulSet、DaemonSet、Job 這些上層抽象，以及每一種抽象各自解決了 Pod 本身解決不了的問題。Probe 設錯、優雅關閉順序沒搞懂，都是實務上真正會炸鍋的地方。

**Q1.** 🟢 Pod 裡的多個容器共享什麼？pause container 的作用是什麼？

<details>
<summary>看答案</summary>

同一個 Pod 內的所有容器共享同一個 network namespace，因此共用同一個 IP、可以用 localhost 互相溝通，也可以選擇共享 volume；pause container 是 Pod 啟動時第一個建立的隱形容器，唯一工作是持有這個共享的 network namespace，即使其他業務容器重啟，network namespace 也不會消失，Pod 的 IP 因此能維持不變。

→ 詳見 [[04-workloads]]
</details>

**Q2.** 🟢 Init Container 和一般容器有什麼不同？

<details>
<summary>看答案</summary>

Init Container 會在所有一般容器啟動之前依序執行完畢，一個成功才換下一個，常用來做前置準備工作，例如等待相依服務就緒、下載設定檔；它跟一般容器共享 volume，但不會跟業務容器同時執行，全部 Init Container 成功結束後，Pod 內的主容器才會一起啟動。

→ 詳見 [[04-workloads]]
</details>

**Q3.** 🔵（辨析）三種 Probe（liveness、readiness、startup）分別回答什麼問題？

<details>
<summary>看答案</summary>

livenessProbe 回答「這個容器是不是卡死了、該不該重啟」；readinessProbe 回答「這個容器現在能不能接受流量」，失敗只會把它從 Service 的 Endpoints 移除，不會重啟容器；startupProbe 回答「這個容器啟動得夠久了嗎」，用來保護啟動緩慢的應用不會在還沒就緒時就被 liveness 誤判為卡死而提前重啟。

→ 詳見 [[04-workloads]]
</details>

**Q4.** 🔴（情境診斷）同事的 Pod 一直 CrashLoopBackOff，你發現是 livenessProbe 設定的問題，最可能是什麼誤設？

<details>
<summary>看答案</summary>

最常見的誤設是 livenessProbe 的 `initialDelaySeconds` 或 `timeoutSeconds` 設得太短、太嚴苛，導致應用其實還在正常啟動或處理一個較慢的請求，就已經被判定為存活失敗而被強制重啟，於是永遠來不及完成啟動，陷入重啟又被殺的迴圈。正確做法是用 startupProbe 給足夠寬鬆的啟動緩衝期，liveness 只在應用真正卡死時才觸發。

→ 詳見 [[04-workloads]]
</details>

**Q5.** 🔵 Pod 被刪除時，優雅關閉的順序是什麼？preStop hook 扮演什麼角色？

<details>
<summary>看答案</summary>

順序大致是：Pod 狀態變成 Terminating，同時從 Service 的 Endpoints 移除，讓新流量不再進來；接著 kubelet 執行容器的 preStop hook（若有設定）；等 preStop 執行完，再送出 SIGTERM 給主程序；若在 terminationGracePeriodSeconds 時限內程序還沒結束，才強制送 SIGKILL。preStop 常用來補一段等待時間，確保「從 Endpoints 移除」與「容器真正停止接受連線」之間不會有請求被斷在半路。

→ 詳見 [[04-workloads]]
</details>

**Q6.** 🔵（情境診斷）同事希望滾動更新過程中服務容量完全不縮水，你會建議他怎麼調整 maxSurge 和 maxUnavailable？

<details>
<summary>看答案</summary>

maxSurge 控制更新過程中最多可以超出期望副本數多少，maxUnavailable 控制最多可以有多少比例的副本同時處於不可用狀態。要容量完全不縮水，應該把 maxUnavailable 設為 0、maxSurge 設為足夠的正值（例如 25% 或固定數量），讓新版本先多開幾個副本上線就緒後，才逐步把舊版本汰換掉，全程不減少可用容量。

→ 詳見 [[04-workloads]]
</details>

**Q7.** 🟢 StatefulSet 提供 Deployment 給不了的三個保證是什麼？

<details>
<summary>看答案</summary>

穩定的網路識別（每個 Pod 有固定格式的名稱與 DNS，重建後名稱不變）；穩定的持久化儲存（透過 volumeClaimTemplates，每個 Pod 對應固定的 PVC，重建後接回同一份資料）；有序的部署與擴縮（依序啟動、依序擴縮，不會一次全部亂序上線）。這三點讓需要維持身份與資料一致性的有狀態服務能正確運作。

→ 詳見 [[04-workloads]]
</details>

**Q8.** 🟢（辨析）DaemonSet 和一般用副本數控制的 workload 有什麼本質差異？

<details>
<summary>看答案</summary>

DaemonSet 不是指定「要幾個副本」，而是「每個符合條件的 Node 上都要有一份」，新加入的 Node 會自動被排上一個副本、Node 被移除副本也會跟著消失，適合用在節點層級的 agent 類服務，例如日誌收集或監控 agent，這種需求用 Deployment 調整副本數是做不到的。

→ 詳見 [[04-workloads]]
</details>

**Q9.** 🔵（情境診斷）同事想拿 Deployment 硬跑一個批次匯出任務，你會建議他改用什麼、為什麼？

<details>
<summary>看答案</summary>

應該改用 Job：Deployment 是為「長期維持一定副本數的常駐服務」設計的，容器跑完任務正常結束時，Deployment 會判定它「異常結束」而不斷重啟，永遠沒完沒了；Job 則保證跑到成功或達到重試上限為止，跑完就不會再重啟。若這個任務需要固定排程時間重複觸發，則進一步改用 CronJob。

→ 詳見 [[04-workloads]]
</details>

## 第 05 章｜網路

網路是最容易把人問倒的一章，因為它的每一層都建立在上一層的假設之上：四條鐵律撐起 CNI，CNI 撐起 Service，Service 撐起 DNS 與 Ingress。任何一層卡住，症狀都是同一句話——「連不到」——但根因可能落在完全不同的層級，這正是這一章題目設計的重點。

**Q1.** 🟢 K8s 網路模型的四條鐵律是什麼？

<details>
<summary>看答案</summary>

每個 Pod 都有自己獨立的 IP；Pod 之間彼此可以直接通訊，不需要 NAT；Node 上的 agent 可以直接跟該 Node 上的所有 Pod 通訊，不需要 NAT；Pod 看到自己的 IP，跟外部看到它的 IP 是一致的。這四條假設是 Service、DNS、NetworkPolicy 等上層網路功能能正常運作的地基。

→ 詳見 [[05-networking]]
</details>

**Q2.** 🟢（辨析）CNI 的 overlay 網路和路由式網路，差在哪？

<details>
<summary>看答案</summary>

overlay 網路（如 VXLAN）是在既有實體網路上再包一層封裝，把 Pod 對 Pod 的封包包進一個 UDP 封包裡穿越底層網路，優點是對底層網路需求低，缺點是有封裝解封裝的效能損耗；路由式網路則直接讓底層網路知道怎麼把封包送到正確的 Pod 網段，沒有封裝開銷，但要求底層網路基礎設施配合設定路由。

→ 詳見 [[05-networking]]
</details>

**Q3.** 🟢（辨析）Service 的 port、targetPort、nodePort 分別是什麼？

<details>
<summary>看答案</summary>

port 是 Service 自己對外曝露的埠號；targetPort 是流量最終要轉發到 Pod 上的哪個埠，也就是容器實際監聽的埠；nodePort 只在 Service type 是 NodePort 或 LoadBalancer 時才有意義，是在每個 Node 實體機器上開的埠，用來讓叢集外部直接打進來。

→ 詳見 [[05-networking]]
</details>

**Q4.** 🔴（陷阱）ClusterIP 常被誤認為「一張虛擬網卡」，實際上是什麼？

<details>
<summary>看答案</summary>

ClusterIP 並不對應任何真實網路介面，它只是被 kube-proxy 寫進節點 iptables 或 IPVS 規則裡的一個位址；當封包的目的地是這個 IP 時，這些規則會攔截並把封包目的地改寫成後面某一個實際 Pod 的 IP。ClusterIP 更像是一條「轉發規則的入口」，而不是一張實體或虛擬網卡。

→ 詳見 [[05-networking]]
</details>

**Q5.** 🔵 kube-proxy 的 iptables 模式和 IPVS 模式差在哪？

<details>
<summary>看答案</summary>

iptables 模式用一長串規則鏈依序比對來決定轉發，Service 數量一多，規則鏈會線性增長，查找效率變差；IPVS 模式用核心內建的雜湊表做負載平衡，查找時間不受 Service 數量影響，在大型叢集下效能明顯優於 iptables 模式，也支援更多負載平衡演算法。

→ 詳見 [[05-networking]]
</details>

**Q6.** 🟢 headless Service 和一般 Service 差在哪？什麼情境會用它？

<details>
<summary>看答案</summary>

一般 Service 會分配一個 ClusterIP 並做負載平衡；headless Service（clusterIP 設為 None）不分配 ClusterIP，DNS 查詢會直接回傳所有後端 Pod 的 IP 列表，不經過負載平衡。這在 StatefulSet 場景很常見，因為每個 Pod 需要被個別定址，而不是被隨機負載平衡到任一個。

→ 詳見 [[05-networking]]
</details>

**Q7.** 🔵（情境診斷）同事發現連叢集外部的 API 常常有延遲，你懷疑跟 DNS 的 `ndots:5` 設定有關，這是什麼機制？

<details>
<summary>看答案</summary>

K8s 預設把 Pod 的 ndots 設為 5，意思是如果查詢的名稱裡點的數量少於 5 個，resolver 會先依序嘗試附加各層 search domain 組成完整名稱去查，全部失敗才把原始名稱當作絕對網域直接查一次。對外部網域（例如只有兩個點的名稱）而言，這代表要先做好幾次注定失敗的內部查詢才查到真正答案，拖慢延遲；常見緩解方式是在名稱後面補一個點做成絕對網域。

→ 詳見 [[05-networking]]
</details>

**Q8.** 🟢（辨析）Ingress 和 Ingress Controller 是同一個東西嗎？

<details>
<summary>看答案</summary>

不是。Ingress 只是一份描述路由規則的 K8s 資源物件，本身不會做任何事；真正讀取這份規則、動態產生反向代理設定並實際處理流量的是 Ingress Controller（如 nginx-ingress、Traefik），這是另外部署的元件。單獨套用 Ingress 物件而叢集裡沒有對應的 Controller 在跑，規則永遠不會生效。

→ 詳見 [[05-networking]]
</details>

**Q9.** 🔵（情境診斷）同事以為裝了 CNI 就代表叢集有網路隔離，你會怎麼糾正他？

<details>
<summary>看答案</summary>

K8s 預設沒有任何網路隔離，若不建立任何 NetworkPolicy 物件，所有 Pod 之間預設全通；即使寫了 NetworkPolicy，也要底層 CNI plugin 本身支援 NetworkPolicy 的執行才有效，某些簡化版 CNI 不支援，這時規則物件會建立成功但實際上完全沒有作用，形成以為有隔離、其實沒有的假安全感。

→ 詳見 [[05-networking]]
</details>

**Q10.** 🔵（情境診斷）同事說他建立了 Service，但 `curl` ClusterIP 完全連不到，你會先查什麼？

<details>
<summary>看答案</summary>

先查 `kubectl get endpoints <service-name>`，看看 Service 底下有沒有掛到任何實際 Pod IP；如果 Endpoints 是空的，通常是 Service 的 selector 跟 Pod 的 labels 對不起來，或是符合 selector 的 Pod 全部沒有通過 readinessProbe；如果 Endpoints 有東西但還是連不到，才進一步查 kube-proxy 規則或 NetworkPolicy。

→ 詳見 [[05-networking]]
</details>

## 第 06 章｜設定與儲存

「設定跟映像檔分離」聽起來理所當然，難的是它牽出來的一整串細節：env 不會熱更新但 volume 會、Secret 只是編碼不是加密、RWO 的真正定義幾乎所有人第一次都會誤解。這一章的題目特別聚焦在「同事跟你抱怨某個行為沒有發生」的情境，因為這正是設定與儲存問題最常見的樣貌。

**Q1.** 🟢 ConfigMap 有哪三種常見的注入方式？

<details>
<summary>看答案</summary>

當作環境變數注入；掛成 Volume 讓容器以檔案形式讀取；當作 command 或 args 的參數直接帶入啟動指令。三種方式各有取捨，會直接影響「改了 ConfigMap 之後服務會不會自動反映」。

→ 詳見 [[06-config-and-storage]]
</details>

**Q2.** 🔵（情境診斷）同事說「我改了 ConfigMap，但服務行為完全沒變」，你會先問他哪一個問題？

<details>
<summary>看答案</summary>

先問他 ConfigMap 是用環境變數還是 Volume 方式注入的。如果是環境變數，改 ConfigMap 完全不會反映到已存在的 Pod 上，因為環境變數只在容器啟動那一刻讀取一次，必須重建 Pod 才會生效；如果是 Volume 掛載，kubelet 會定期同步更新掛載的檔案內容，但若用了 subPath 掛載單一檔案，這個自動更新機制會失效。

→ 詳見 [[06-config-and-storage]]
</details>

**Q3.** 🔵（機制原理）checksum annotation 這個技巧是用來解決什麼問題？

<details>
<summary>看答案</summary>

即使 ConfigMap 用 Volume 方式掛載會自動更新內容，Deployment 本身並不知道「內容變了」，所以不會觸發滾動更新讓應用重新載入設定。常見做法是在 Pod template 的 annotation 裡放一個 ConfigMap 內容的雜湊值，只要 ConfigMap 一變，雜湊值跟著變，Pod template 就被視為有變化，自然觸發滾動更新，等同人為製造一次強制重啟去讀新設定。

→ 詳見 [[06-config-and-storage]]
</details>

**Q4.** 🟢（情境診斷）同事把 Secret 的 YAML 明文提交進 Git，還說反正 Secret 有 base64 加密保護，你會怎麼糾正他？

<details>
<summary>看答案</summary>

Secret 的值只是做了 base64 編碼，這只是一種讓內容能放進 YAML 的編碼方式，完全不具備加密或保護效果，任何能讀到這份 YAML 的人都能直接還原出明文。真正的保護要靠 etcd 靜態加密、嚴格的 RBAC，以及絕對不要把 Secret 的 YAML 明文提交進 Git。

→ 詳見 [[06-config-and-storage]]
</details>

**Q5.** 🟢 Vault 加上 External Secrets Operator 這套組合解決了什麼問題？

<details>
<summary>看答案</summary>

直接把敏感資訊寫進 K8s Secret，即使加密仍代表機密資料的生命週期跟 K8s 綁死、難以做集中輪替與稽核；Vault 專門管理機密的儲存、動態產生、輪替與存取稽核，External Secrets Operator 負責把 Vault 裡的機密同步成 K8s Secret 物件，讓應用程式照常用原生 Secret 的方式讀取，同時把機密的源頭管理交給更專業的系統。

→ 詳見 [[06-config-and-storage]]
</details>

**Q6.** 🔴（陷阱）RWO 是不是代表這個 Volume 只能被一個 Pod 掛載？

<details>
<summary>看答案</summary>

不是，這是最常見的誤解。RWO（ReadWriteOnce）的真正定義是「只能被一個 Node 以讀寫模式掛載」，如果同一個 Node 上有多個 Pod，理論上它們可以共用同一個掛載到該 Node 的 RWO Volume（實務上是否允許取決於 CSI driver 實作）。真正限制「只能一個 Pod」的存取模式是後來才新增的 ReadWriteOncePod，語意更精確。

→ 詳見 [[06-config-and-storage]]
</details>

**Q7.** 🟢（辨析）PV、PVC、StorageClass 為什麼要拆成三層？

<details>
<summary>看答案</summary>

PV 代表叢集裡實際存在的一塊儲存資源；PVC 是使用者對儲存的申請單，只描述需要多大容量、什麼存取模式，不用管底層細節；StorageClass 定義怎麼動態生出符合條件的 PV。這樣拆分讓開發者只需要寫 PVC 就能拿到儲存，完全不用知道底層是哪種硬碟或哪個雲端供應商，達到儲存的解耦與自動化供應。

→ 詳見 [[06-config-and-storage]]
</details>

**Q8.** 🔴（機制原理）`volumeBindingMode: WaitForFirstConsumer` 解決了什麼問題？

<details>
<summary>看答案</summary>

如果 StorageClass 一收到 PVC 就立刻在某個可用區建好 PV，但排定該 Pod 的 Node 剛好在另一個可用區，就會發生 PV 跟 Pod 所在位置對不上、Pod 永遠排不進去的問題。`WaitForFirstConsumer` 讓 PV 的實際建立延後到有 Pod 真的要使用這個 PVC、且 scheduler 已經決定要排到哪個 Node 之後才發生，確保儲存跟運算落在同一個可用區。

→ 詳見 [[06-config-and-storage]]
</details>

**Q9.** 🔵（情境診斷）同事的 PVC 一直卡在 Pending，你會依序檢查什麼？

<details>
<summary>看答案</summary>

先看 `kubectl describe pvc` 的 Events，通常會直接告訴你原因。常見情形包括：StorageClass 名稱打錯或不存在、要求的容量超過底層供應商上限、`WaitForFirstConsumer` 模式下沒有 Pod 在使用它所以本來就會停在 Pending，或叢集根本沒有可用的 CSI driver，只能手動預先建好 PV 才能被綁定。

→ 詳見 [[06-config-and-storage]]
</details>

## 第 07 章｜排程與資源管理

這一章存在的理由，是「同一台 Node 上為什麼有的 Pod 變慢、有的 Pod 直接暴斃」。requests 跟 limits 的分工、CPU 節流跟 Memory OOMKill 的不對稱、QoS 決定驅逐順序——這些都是資源緊繃時，決定「誰先倒下」的規則，也是最容易被半知半解帶過的一章。

**Q1.** 🟢 Scheduler 決策 Pod 排到哪個 Node，分成哪兩個階段？

<details>
<summary>看答案</summary>

先是 Filter（過濾）階段，把不符合條件（資源不足、有不相容的 taint、不符合 nodeSelector 等）的 Node 直接刷掉；剩下候選 Node 進入 Score（打分）階段，依照多個評分策略算出分數，選出分數最高的 Node，最後把結果寫回 Pod 的 nodeName 完成綁定。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q2.** 🔴（辨析）requests 和 limits 都是資源設定，實際作用差在哪？

<details>
<summary>看答案</summary>

requests 是「保證要拿到的最低資源量」，scheduler 只看 requests 判斷某個 Node 有沒有足夠餘量放這個 Pod，因此 Node 可以被超賣；limits 是 kubelet 設定給 cgroup 的使用上限，跟排程決策完全無關，只在容器實際跑起來後由核心負責是否強制限制或處罰超用的容器。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q3.** 🔴（情境診斷）同事的 Pod 一直被 OOMKilled 而不是變慢，你會怎麼跟他解釋 CPU 和 Memory 超用後果為什麼不同？

<details>
<summary>看答案</summary>

CPU 是可壓縮資源，超過 limits 時 cgroup 只會做 throttle 節流，把程序的 CPU 時間片硬性壓低，程序不會被殺掉只是變慢；Memory 是不可壓縮資源，一旦容器實際用量超過 limits，核心沒有「借一點慢慢還」的選項，只能直接觸發 OOM Killer 把程序殺死。這也是為什麼記憶體的 limits 要抓得比 CPU 更保守精確。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q4.** 🔵 QoS Class 的三個等級是怎麼從 requests／limits 推導出來的？

<details>
<summary>看答案</summary>

Guaranteed：每個容器都同時設定 requests 且等於 limits；Burstable：至少設定了 requests 或 limits 其中一項，但不完全相等；BestEffort：完全沒設定 requests 也沒設定 limits。這個等級直接決定 Node 資源緊繃需要驅逐 Pod 時的優先順序，BestEffort 最先被犧牲，Guaranteed 最後才會被動。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q5.** 🟢（辨析）Taint 的三種 effect 分別是什麼？

<details>
<summary>看答案</summary>

NoSchedule：新 Pod 若沒有對應的 toleration 就不會被排到這個 Node，但已經在上面跑的不受影響；PreferNoSchedule：盡量避免排上去，但不是硬性規則；NoExecute：不只擋新 Pod 排入，連已經在這個 Node 上、沒有對應 toleration 的 Pod 都會被驅逐。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q6.** 🔵（對比）nodeAffinity、podAffinity、podAntiAffinity 各自解決什麼排放需求？

<details>
<summary>看答案</summary>

nodeAffinity 是 Pod 對 Node 特性的偏好，例如一定要排在有 SSD 標籤的 Node；podAffinity 是希望這個 Pod 跟另一群特定 Pod 排在一起，例如跟快取服務同 Node 降低延遲；podAntiAffinity 相反，希望這個 Pod 盡量不要跟另一群 Pod 排在同一個 Node 或拓樸，例如同一個服務的多個副本要分散避免單點故障。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q7.** 🔵 PriorityClass 和 Preemption 一起使用時，被搶佔的 Pod 會怎樣？

<details>
<summary>看答案</summary>

當高優先權的 Pod 無法被排程、且 scheduler 判斷驅逐某些低優先權 Pod 後就能空出資源時，會觸發 preemption，把低優先權 Pod 直接刪除騰出空間；這些被搶佔的 Pod 如果隸屬於會自動補建的物件，會被重新排程到別的 Node，但這對它們而言是一次非自願的中斷，若沒有配合 PDB 保護，可能同時搶掉太多副本影響服務可用性。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q8.** 🟢（辨析）HPA、VPA、Cluster Autoscaler 三者的分工是什麼？

<details>
<summary>看答案</summary>

HPA 根據指標調整 Pod 的副本數量；VPA 調整單一 Pod 的 requests／limits 大小；Cluster Autoscaler 則是當叢集整體資源不足以排下所有 Pod 時，自動增加或減少 Node 的數量。三者作用的維度完全不同，但同時對同一個 workload 的同一種資源用 HPA 和 VPA 容易互相打架，通常不建議同時套用。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q9.** 🔴（情境診斷）同事的 namespace 設定了 ResourceQuota，結果有些 Pod 建立失敗、報錯要求設定 requests，你會怎麼解釋並解決？

<details>
<summary>看答案</summary>

只要在某個 namespace 對 CPU 或 Memory 設下總量限制，K8s 就會要求該 namespace 裡每一個 Pod 都必須明確寫出對應資源的 requests，因為 quota 系統需要能加總計算才能判斷有沒有超額，沒寫就會被拒絕建立。解法是搭配 LimitRange 幫沒有明確設定的 Pod 自動補上預設的 requests／limits，避免每個開發者都要手動填。

→ 詳見 [[07-scheduling-and-resources]]
</details>

**Q10.** 🟢（情境診斷）同事要對某個 Deployment 做版本升級，滾動更新卻卡住不動，你懷疑跟 PDB 有關，你會怎麼確認？

<details>
<summary>看答案</summary>

查這個 Deployment 有沒有對應的 PodDisruptionBudget，以及它設定的 `minAvailable` 或 `maxUnavailable` 數值；如果滾動更新加上 PDB 的限制，算出來會導致同時不可用的副本數超過 PDB 允許的範圍，K8s 會卡住不繼續往下驅逐舊 Pod，直到有新 Pod 先變成 Ready 騰出空間。這常發生在副本數本來就很少又設了嚴格 PDB 的情境。

→ 詳見 [[07-scheduling-and-resources]]
</details>

## 第 08 章｜安全與 RBAC

安全這一章最重要的心態轉變是：K8s 完全不知道「使用者」是誰，也沒有內建的拒絕規則。這聽起來反直覺，卻是整套權限模型設計的起點。這一章的題目會反覆確認你是不是真的理解「三道關卡」與「純白名單」這兩個核心概念，而不是只會背 RBAC 的四個物件名稱。

**Q1.** 🟢 一個請求進到 apiserver，要通過哪三道關卡？

<details>
<summary>看答案</summary>

Authentication 驗證你是誰；Authorization 確認你有沒有權限做這件事，K8s 內建主要用 RBAC；Admission Control 在請求真正寫入 etcd 之前做最後一層檢查與修改，分 Mutating 和 Validating 兩階段。三道關卡依序把關，任何一關沒過，請求就會被拒絕。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q2.** 🔴（陷阱）K8s 有 User 這種原生物件可以查詢或管理嗎？

<details>
<summary>看答案</summary>

沒有。K8s 完全不儲存「使用者」這個概念的物件，使用者的身份完全依賴外部認證機制（憑證、token、OIDC provider 等）在請求時提供的資訊來辨識，K8s 只是信任這些認證結果、把使用者名稱套用到 RBAC 規則上。唯一有原生物件、可以被查詢管理的身份是 ServiceAccount，代表的是 Pod 這種機器身份而非人類使用者。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q3.** 🔵（情境診斷）同事不小心把簽好的 cluster-admin 等級 client 憑證傳到公開頻道，你會怎麼處理，為什麼不能單純撤銷它？

<details>
<summary>看答案</summary>

X.509 client 憑證在到期之前沒有內建的單獨撤銷機制，除非叢集額外部署了 CRL 或 OCSP 撤銷檢查，因此不建議簽發長效期的 cluster-admin 等級憑證到處發放。一旦外洩，比較安全的處置是輪替整個 CA 讓所有舊憑證失效，或改用可以被主動撤銷的認證方式，例如 OIDC token 或短效期的 ServiceAccount token。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q4.** 🔵 ServiceAccount token 從舊機制到新機制經歷了什麼演進？

<details>
<summary>看答案</summary>

早期版本 K8s 會自動幫每個 ServiceAccount 建立一個長效期、掛在 Secret 物件裡的 token，一旦外洩就長期有效、難以追蹤；1.24 版之後改用 TokenRequest API 產生的 projected token，這種 token 預設短效期會自動輪替、綁定特定的 audience，也不再自動建立永久 Secret，大幅降低了 token 外洩後的風險視窗。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q5.** 🟢（辨析）RBAC 的四個物件怎麼配對使用？

<details>
<summary>看答案</summary>

Role 定義在某個 namespace 內可以做哪些操作，要靠 RoleBinding 綁定給使用者、群組或 ServiceAccount 才會生效；ClusterRole 定義的權限範圍是整個叢集或跨 namespace 共用的資源，可以搭配 ClusterRoleBinding 綁定成叢集全域生效，也可以搭配 RoleBinding 把同一份 ClusterRole 的權限限縮綁定在單一 namespace 內使用。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q6.** 🔵（情境診斷）同事想寫一條 RBAC 規則明確禁止某人刪除 Pod，你會怎麼跟他說明為什麼做不到？

<details>
<summary>看答案</summary>

RBAC 是純白名單機制，只有允許的規則，沒有拒絕的規則；一個使用者最終擁有的權限是所有綁定給他的 Role／ClusterRole 權限的聯集，只會累加不會相減。想限制某人不能做某事，唯一辦法是從一開始就不要給他那個權限，或設計更細粒度的 Role，不能靠寫一條 deny 規則來排除。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q7.** 🔵 K8s 怎麼防止使用者透過 RBAC 權限提升給自己更大的權力？

<details>
<summary>看答案</summary>

K8s 有內建的權限提升防護：使用者不能建立或編輯一個權限比自己現有權限還大的 Role／ClusterRole，也不能透過 RoleBinding／ClusterRoleBinding 把自己沒有的權限授予別人，除非額外擁有 escalate、bind 這類特殊動詞的權限。這確保了「你不能給出你自己都沒有的東西」，避免權限像滾雪球一樣被濫用擴大。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q8.** 🟢 `kubectl auth can-i` 和 `--as` impersonation 分別怎麼用來排查權限問題？

<details>
<summary>看答案</summary>

`kubectl auth can-i <verb> <resource>` 可以直接問 apiserver「我能不能做這件事」，快速確認自己的權限範圍；`--as=<user>` 則是用自己的高權限身份假扮成另一個使用者或 ServiceAccount 發送請求，用來驗證某個特定身份實際上有沒有權限做某件事，在除錯別人回報的權限問題時特別有用，不需要真的拿到對方的憑證。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q9.** 🔵（辨析）Pod Security Admission 的三個等級和三種模式分別是什麼？

<details>
<summary>看答案</summary>

三個等級是 Privileged（完全不限制）、Baseline（阻擋已知的權限提升手法但保留彈性）、Restricted（最嚴格，強制遵循加固最佳實踐，例如禁止 root、禁止特權容器）；三種模式是 enforce（不符合就直接拒絕建立）、audit（記錄違規但仍允許建立）、warn（回傳警告訊息但仍允許）。這套機制是舊版 PodSecurityPolicy 被移除後的替代方案，用 namespace 層級的 label 套用。

→ 詳見 [[08-security-and-rbac]]
</details>

**Q10.** 🟢（情境診斷）同事說他的 ServiceAccount 在某個 namespace 明明有 Role，卻還是收到 403 Forbidden，你會怎麼排查？

<details>
<summary>看答案</summary>

先用 `kubectl auth can-i --as=system:serviceaccount:<ns>:<sa> <verb> <resource> -n <ns>` 直接驗證這個身份到底有沒有權限；再檢查 RoleBinding 綁的 subject（namespace、name、kind）是否精確對應到這個 ServiceAccount；也要確認他操作的資源是不是屬於另一個 apiGroup，RBAC 的 rule 要精確匹配 apiGroups、resources、verbs，任何一項對不上都會導致 403。

→ 詳見 [[08-security-and-rbac]]
</details>

## 第 09 章｜擴充 Kubernetes

這一章解釋的是 K8s 為什麼能「長出」CRD、Operator 這些原本不存在的資源類型，以及背後那條看不見的 Admission Controller 鏈怎麼默默修改你的 YAML。理解這一章之後，同事問「我的 YAML 怎麼被改了」「namespace 怎麼刪不掉」這類問題，你就有明確的排查方向而不是憑感覺猜。

**Q1.** 🟢 Admission Controller 鏈裡，Mutating 和 Validating 誰先執行？為什麼順序很重要？

<details>
<summary>看答案</summary>

Mutating Admission Webhook 一定先於 Validating 執行。因為 Mutating 階段可能會修改請求內容，例如自動注入 sidecar 容器、補上預設值，如果順序反過來，Validating 驗證到的會是還沒被修改前的舊內容，可能讓本該被攔下的設定通過驗證，或讓修改後才合規的設定被誤判為不合規。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q2.** 🔵（情境診斷）同事發現自己送出的 YAML 跟 apiserver 裡實際存的內容不一樣，多了一些他沒寫的欄位，這是誰做的？

<details>
<summary>看答案</summary>

很可能是某個 Mutating Admission Webhook 在幫他加料，例如 Istio 自動注入 sidecar 容器、某個 Policy 工具自動補上預設的 resources 或 SecurityContext。要確認可以查叢集裡安裝了哪些 MutatingWebhookConfiguration，看它們的 rules 是否匹配到這個資源類型，就能找出是哪個 webhook 動的手腳。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q3.** 🔴（陷阱）admission webhook 的 `failurePolicy` 設成 Fail，會造成什麼潛在災難？

<details>
<summary>看答案</summary>

`failurePolicy: Fail` 代表當這個 webhook 服務連不上或逾時無回應時，apiserver 會直接拒絕該請求；如果這個 webhook 部署在叢集內，又剛好因為某次事故而不可用，就會形成雞生蛋蛋生雞的死結：所有相關資源的建立或更新都被卡死，包括想要修復問題所需要的操作，可能導致整個叢集局部癱瘓。因此關鍵性的 webhook 需要謹慎設計高可用性與逾時時間，審慎評估 Fail 與 Ignore 的取捨。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q4.** 🟢 CRD 讓自訂資源做到什麼程度的「原生化」？

<details>
<summary>看答案</summary>

CRD 可以讓使用者自訂的資源類型享有跟原生資源幾乎一樣的待遇：一樣可以用 `kubectl get`、`describe`、`apply` 操作，一樣可以被 RBAC 控管，一樣可以被 watch，一樣可以套用 validation schema。它讓開發者能把任何業務邏輯的期望狀態都用 K8s 慣用的宣告式模型來表示。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q5.** 🔵 Operator Pattern 的核心概念是什麼？

<details>
<summary>看答案</summary>

Operator 是「CRD 加上自訂 controller」的組合：CRD 定義某個領域物件的期望狀態，例如一個資料庫叢集要有幾個節點、什麼版本；自訂 controller 把原本需要人類維運人員手動判斷的邏輯（備份、故障轉移、版本升級）寫成程式碼，持續 watch 這個 CRD 物件並自動執行對應動作，等於把資深維運人員的操作經驗編碼成可以自動運行的軟體。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q6.** 🔵（情境診斷）同事說某個 namespace 一直刪不掉，卡在 Terminating 好幾個小時，你會先查什麼？

<details>
<summary>看答案</summary>

先查這個 namespace 裡卡住的資源（或 namespace 本身）的 `metadata.finalizers` 欄位有沒有值。Finalizer 是一種刪除前必須先完成清理工作的機制，只要 finalizer 列表沒有清空，物件就會一直卡在 Terminating 狀態；常見原因是負責清除該 finalizer 的 controller 已經掛掉或對應的 Operator 已被移除，這時候可能需要手動 patch 拿掉 finalizer 才能讓刪除完成，但要先確認清楚不會留下孤兒資源。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q7.** 🔵（辨析）刪除一個 Deployment 會連帶清掉旗下的 Pod，這是靠什麼機制？三種 propagation policy 差在哪？

<details>
<summary>看答案</summary>

這是靠 OwnerReference：ReplicaSet、Pod 這些子資源身上都記錄著擁有者是誰，垃圾回收器依此判斷父資源被刪除後子資源該怎麼處理。Foreground 會先刪光所有子資源、確認都清乾淨了才真正刪掉父資源本身；Background（預設）立刻刪掉父資源，子資源交給垃圾回收器非同步在背景清理；Orphan 則刪掉父資源但保留所有子資源，讓它們變成沒有主人的獨立物件。

→ 詳見 [[09-extending-kubernetes]]
</details>

**Q8.** 🟢 CRI、CNI、CSI 這三個可插拔介面各自負責哪個領域？

<details>
<summary>看答案</summary>

CRI（Container Runtime Interface）讓 kubelet 可以對接不同的容器執行期，如 containerd、CRI-O；CNI（Container Network Interface）讓 K8s 可以對接不同廠商的網路方案，如 Calico、Cilium；CSI（Container Storage Interface）讓 K8s 可以對接不同雲端或儲存廠商的儲存系統。三者都是同一種設計哲學：K8s 自己只定義標準介面，實作交給生態系百花齊放。

→ 詳見 [[09-extending-kubernetes]]
</details>

## 第 10 章｜Helm

Helm 的坑幾乎都藏在 Go template 的細節裡：`indent` 跟 `nindent` 差一個換行、`include` 跟 `template` 差在能不能接管線、`with` 會偷偷改變 `.` 指向的範圍。這一章題目的目的，是讓你下次遇到「渲染出來的 YAML 縮排怪怪的」或「nil pointer」錯誤時，能立刻定位到根因而不是亂試。

**Q1.** 🟢 一個標準 Helm Chart 的基本目錄結構有哪些必要組成？

<details>
<summary>看答案</summary>

`Chart.yaml` 描述這個 chart 的名稱、版本等 metadata；`values.yaml` 是預設的可覆蓋參數；`templates/` 是實際的 K8s YAML 樣板檔案；可選的 `charts/` 存放依賴的子 chart。`helm install` 時就是拿 values 去渲染 templates 底下的樣板，產出最終要送進叢集的 YAML。

→ 詳見 [[10-helm]]
</details>

**Q2.** 🔵（辨析）`indent` 和 `nindent` 差在哪？什麼時候一定要用 nindent？

<details>
<summary>看答案</summary>

`indent` 單純把接下來的每一行往右縮排指定的空格數；`nindent` 做的事一樣，但會在縮排之前先加一個換行。在 YAML 樣板裡通常已經在管線前面寫了 key，如果直接接 `indent`，第一行內容會跟 key 黏在同一行造成格式錯誤；用 `nindent` 才能讓內容從下一行開始、且每一行都有正確縮排，這是撰寫多行區塊的標準寫法。

→ 詳見 [[10-helm]]
</details>

**Q3.** 🔵（辨析）`include` 和 `template` 都能呼叫定義好的片段，差在哪？為什麼多數場合建議用 include？

<details>
<summary>看答案</summary>

`template` 是 Go template 原生的呼叫方式，它是一個動作而不是函式，因此不能被放進管線串接後續函式；`include` 是 Helm 額外提供的函式，把同樣的渲染結果當作字串回傳，因此可以被放進管線繼續傳給 `nindent`、`trunc` 等函式處理。因為模板片段幾乎都需要控制縮排，實務上絕大多數情況都該用 include 而非 template。

→ 詳見 [[10-helm]]
</details>

**Q4.** 🔴（情境診斷）同事的 Helm 模板在 `with` 區塊裡怎麼都抓不到外層的值，你會怎麼幫他解釋這個陷阱？

<details>
<summary>看答案</summary>

`with .Values.foo` 會把區塊內的 `.` 暫時改成指向 `.Values.foo`，這時候如果在區塊裡想存取原本最外層的 `.Values.bar` 或 `.Release.Name`，直接寫會失敗，因為 `.` 已經不是原本的根層級了。`$` 這個特殊變數從模板一開始就固定綁定根層級的上下文，不會因為進入 `with`、`range` 而改變，所以在巢狀 scope 裡要拿最外層的值，一律改用 `$.Values.bar` 這種寫法才安全。

→ 詳見 [[10-helm]]
</details>

**Q5.** 🟢 Helm 的 values 覆蓋優先序大致是什麼？

<details>
<summary>看答案</summary>

大致由低到高：chart 自帶的 `values.yaml` 預設值，到父 chart 對子 chart 傳入的值，到使用者透過 `-f` 傳入的檔案（多個檔案依指定順序疊加，後面蓋前面），到命令列 `--set` 直接指定的參數，優先權最高。理解這個順序才能預期最終渲染出來的值到底是哪一層決定的。

→ 詳見 [[10-helm]]
</details>

**Q6.** 🟢 Chart 依賴裡的 `global` 值有什麼特殊用途？

<details>
<summary>看答案</summary>

一般子 chart 只能存取自己 `values.yaml` 定義的值，看不到父 chart 或其他兄弟 chart 的設定；`global` 區塊底下的值會被所有層級的 chart 共同看到，適合用來放跨 chart 都需要一致的設定，例如 image registry 位址，避免每個子 chart 都要重複設定一次。

→ 詳見 [[10-helm]]
</details>

**Q7.** 🟢 一次 `helm install` 之後，release 的資訊實際存在哪裡？

<details>
<summary>看答案</summary>

Helm 3 預設會把每個 release 的完整資訊（包含渲染後的 manifest、values）以 Secret 物件的形式存在該 release 所在的 namespace 裡，每次 upgrade 都會產生一個新版本的 Secret 記錄歷史，這也是 `helm rollback` 能夠回到先前版本的資料來源。

→ 詳見 [[10-helm]]
</details>

**Q8.** 🔵（情境診斷）同事的 Chart 渲染出來的 YAML 明顯不對，但看不出哪裡錯，你會請他依序跑哪三個除錯指令？

<details>
<summary>看答案</summary>

依序建議：`helm template` 純粹在本地渲染出最終 YAML 而不真的安裝，先確認渲染結果對不對；`helm install --dry-run --debug`（或 upgrade 加上這兩個 flag）會實際跟叢集互動驗證但不真的套用，同時把渲染過程與最終送出的內容印出來；如果懷疑是某個特定 release 的狀態問題，`helm get manifest <release>` 可以拿出目前叢集裡實際生效的版本做比對。

→ 詳見 [[10-helm]]
</details>

**Q9.** 🔴（情境診斷）同事的 `helm template` 一直報 nil pointer 錯誤，你會怎麼幫他排查？`required` 和 `default` 函式怎麼分工避免它？

<details>
<summary>看答案</summary>

這種錯誤通常代表模板嘗試存取一個路徑不存在的值，例如使用者根本沒在 values 裡提供某個巢狀 key，Go template 對不存在的巢狀路徑會回傳 nil，再往下取欄位就會直接爆錯。`default` 函式可以在值不存在或為空時提供一個備援值，讓模板不會因為缺值而崩潰；`required` 函式則用於這個值絕對必須由使用者提供的場合，若沒提供就主動印出清楚的錯誤訊息提前中止，比讓它產生模糊的 nil pointer 錯誤更好除錯。

→ 詳見 [[10-helm]]
</details>

## 第 11 章｜ArgoCD

GitOps 的核心信念是「Git 裡寫的，就是叢集裡跑的」，但實務上 Sync 顯示 Synced 不代表服務健康、顯示 OutOfSync 也不代表真的壞了——這一章的題目專門在拆解這種「看起來一樣、狀態卻不同」的落差，這也是實務上 ArgoCD 最常讓人卡關的地方。

**Q1.** 🟢 GitOps 的四大原則大致是什麼？

<details>
<summary>看答案</summary>

描述式：系統的期望狀態用宣告式方式描述並版本控制；版本化與不可變：Git 是唯一真實來源，變更記錄在版本歷史裡；自動拉取：agent 主動從 Git 拉取變更套用到系統，而非外部推送；持續調和：agent 持續比對實際狀態與 Git 裡的期望狀態，發現偏差自動或提示修正。這四點合起來讓 Git 的 commit 歷史直接對應到系統狀態的變更歷史。

→ 詳見 [[11-argocd]]
</details>

**Q2.** 🔵 為什麼 GitOps 強調 pull 而不是傳統 CI/CD 常見的 push？

<details>
<summary>看答案</summary>

push 模式代表叢集的存取憑證必須交給叢集外部的 CI 系統保管，擴大了攻擊面，也讓叢集實際狀態容易因為手動操作而跟 Git 記錄的期望狀態產生分歧且難以察覺；pull 模式由叢集內的 agent 主動去讀 Git、用自己的權限套用到自己所在的叢集，權限收斂在叢集內部，agent 也會持續比對、主動回報或修正任何偏移。

→ 詳見 [[11-argocd]]
</details>

**Q3.** 🔵（辨析）Sync Status 和 Health Status 為什麼是兩條獨立的軸線？

<details>
<summary>看答案</summary>

Sync Status 回答叢集目前的實際內容，跟 Git 裡宣告的期望內容是否一致；Health Status 回答這個應用程式現在運作起來健不健康。一個應用可以 Synced 但 Degraded，例如設定完全照 Git 套用了，但 image 拉取失敗導致服務跑不起來；也可以 OutOfSync 但 Healthy，例如有人手動改了一個不影響運作的欄位。兩者必須分開看才能正確判斷狀況。

→ 詳見 [[11-argocd]]
</details>

**Q4.** 🔵（情境診斷）同事手動改了叢集裡的一個資源，結果過一下子又被 ArgoCD 改回去了，這是什麼機制？

<details>
<summary>看答案</summary>

這是 syncPolicy 裡的 `selfHeal` 在起作用：當有人手動修改叢集內的資源產生 drift 時，開啟 selfHeal 後，ArgoCD 會主動把它改回 Git 裡宣告的樣子，而不是被動等下一次 Git 變更才修正。這正是 GitOps「Git 是唯一真實來源」原則的具體體現，任何跟 Git 不一致的手動修改都會被視為需要修正的偏差。

→ 詳見 [[11-argocd]]
</details>

**Q5.** 🔴（機制原理）Sync Waves 和 Resource Hooks 用來解決什麼問題？

<details>
<summary>看答案</summary>

一份 Application 底下常常有多種資源需要按照特定順序上線，例如要先跑資料庫 migration 再啟動吃這個資料庫的服務，單純的 `kubectl apply` 沒有原生的順序保證。Sync Waves 透過 annotation 給資源標上波次編號，讓 ArgoCD 依序套用，前一波全部 Healthy 才進下一波；Resource Hooks（PreSync、Sync、PostSync 等）可以在同步流程的特定時間點插入一次性任務，讓部署流程能表達更複雜的前後依賴關係。

→ 詳見 [[11-argocd]]
</details>

**Q6.** 🔴（情境診斷）Application 顯示 OutOfSync，但你比對 Git 跟叢集內容看起來明明一樣，你會怎麼排查？

<details>
<summary>看答案</summary>

常見原因之一是某個 controller 或 webhook 會在資源建立後自動幫欄位補值或做正規化，導致 ArgoCD 比對出差異但人眼看不出來，這時候應該用 `argocd app diff` 精確比對差異在哪個欄位；另一個常見原因是快取沒有反映最新狀態，可以做一次 hard refresh 強迫重新讀取叢集實際內容與 Git 內容再比對；如果差異確實是合理但不重要的欄位，可以用 `ignoreDifferences` 明確告訴 ArgoCD 忽略它，避免一直誤判為 OutOfSync。

→ 詳見 [[11-argocd]]
</details>

**Q7.** 🟢 AppProject 除了把 Application 分組，更重要的安全邊界作用是什麼？

<details>
<summary>看答案</summary>

AppProject 可以限制底下的 Application 只能部署到指定的目的地叢集或 namespace、只能來自指定的 Git repo 來源、只能使用白名單內的資源類型，例如禁止部署 ClusterRole 這種叢集層級的高權限資源。這讓多團隊共用同一個 ArgoCD 時，可以畫出清楚的權限邊界，防止某團隊的 Application 意外或惡意部署到別人的 namespace。

→ 詳見 [[11-argocd]]
</details>

**Q8.** 🟢 ApplicationSet 解決了什麼痛點？

<details>
<summary>看答案</summary>

當團隊需要幫多個叢集或多個環境各自建立一份幾乎相同、只有少數參數不同的 Application 時，一個一個手寫非常重複；ApplicationSet 用 generator 自動依照某個來源批次產生一整組 Application，來源增加或減少時也會自動跟著增減對應的 Application，不需要手動維護。

→ 詳見 [[11-argocd]]
</details>

**Q9.** 🟢（設計決策）同事說「我們 prod 環境的 Application targetRevision 設成 HEAD 比較方便」，你會怎麼提醒他風險？

<details>
<summary>看答案</summary>

`targetRevision: HEAD` 代表永遠追蹤某個分支的最新 commit，任何人 merge 進這個分支的變更都會立刻或下次 sync 時被自動套用，等於環境的部署內容完全繫於分支當下的內容，沒有明確版本釘選，容易造成非預期部署，也難以重現上週某個時間點到底部署的是哪個版本。正式環境通常建議釘選明確的 tag 或 commit SHA，透過 PR 明確推進版本。

→ 詳見 [[11-argocd]]
</details>

## 第 12 章｜叢集維運

這一章是把前面十一章的知識搬到「真正的正式環境」去驗證：etcd 為什麼要奇數節點、備份還原有沒有真的演練過、升級順序錯了會發生什麼事。這裡的每一題幾乎都對應著一次可能發生的重大事故，也是你即將擔任 K8s 管理員後，最直接會被拿來考驗的一章。

**Q1.** 🟢 為什麼 etcd 叢集節點數要是奇數？

<details>
<summary>看答案</summary>

etcd 用 Raft 共識演算法，寫入需要多數決節點同意才算成功；奇數節點在同樣的容錯能力下比偶數節點更有效率，例如三節點跟四節點都只能容忍一個節點掛掉才能繼續運作，四節點多花一個節點的成本卻沒換到更高的容錯度，所以慣例上都選奇數，例如三、五、七個節點。

→ 詳見 [[12-cluster-operations]]
</details>

**Q2.** 🔴（辨析）etcd 備份與 Velero 備份的範圍差異是什麼？為什麼兩者都需要？

<details>
<summary>看答案</summary>

etcd 備份備份的是 K8s 物件本身的定義，還原後能重建整個叢集的物件配置，但不包含 PV 底層實際的資料內容；Velero 則是針對 K8s 資源加上底層 volume 資料的快照做備份還原，能處理應用程式實際資料的部分。兩者互補：etcd 備份救叢集的骨架，Velero 搭配 volume snapshot 救資料的肉。

→ 詳見 [[12-cluster-operations]]
</details>

**Q3.** 🔵（情境診斷）同事說某個節點的憑證快過期了，會出現什麼症狀？你會怎麼確認與處理？

<details>
<summary>看答案</summary>

症狀通常是該節點的 kubelet 或該憑證對應的元件開始出現認證失敗、無法跟 apiserver 建立連線的錯誤，嚴重時該節點會被標記為 NotReady。可以用對應工具先確認各憑證的到期時間，若接近到期就主動輪替，並記得憑證輪替後要重新啟動相關元件讓新憑證生效，同時建議建立監控主動提醒即將到期的憑證，而不是等出事才發現。

→ 詳見 [[12-cluster-operations]]
</details>

**Q4.** 🟢 K8s 叢集升級為什麼要先升 control plane、再升 node？

<details>
<summary>看答案</summary>

K8s 有明確的 version skew 規則：control plane 的版本必須大於等於 node（kubelet）的版本，不能反過來。如果先升級 node 再升 control plane，中間會出現 kubelet 版本比 apiserver 還新這種不支援的組合，可能導致相容性問題；因此標準順序永遠是先升級 control plane，確認穩定後才逐步升級各個 Node。

→ 詳見 [[12-cluster-operations]]
</details>

**Q5.** 🔴（機制原理）`kubectl drain` 遇到 PDB 保護的 Pod 時會怎麼處理？`--ignore-daemonsets` 又是為了什麼？

<details>
<summary>看答案</summary>

drain 會嘗試以自願驅逐的方式一個個把節點上的 Pod 請走，這個請求會先檢查對應的 PDB，如果驅逐這個 Pod 會導致其所屬應用低於 PDB 允許的最小可用數量，這次驅逐請求就會被拒絕，drain 因此可能卡住等待；`--ignore-daemonsets` 是因為 DaemonSet 管理的 Pod 本質上綁定在每個節點上，drain 一個節點本來就預期會讓上面的 DaemonSet Pod 消失，如果不加這個參數，drain 會因為無法正常驅逐 DaemonSet Pod 而卡住或報錯。

→ 詳見 [[12-cluster-operations]]
</details>

**Q6.** 🟢 RTO 和 RPO 分別代表什麼？

<details>
<summary>看答案</summary>

RPO（Recovery Point Objective）代表最多能接受遺失多少時間範圍內的資料，決定了備份頻率該多密；RTO（Recovery Time Objective）代表發生災難後，最多能容忍多久才恢復服務，決定了復原流程與工具要多快、多自動化。這兩個指標是設計備份與災難復原策略時最先要跟業務方確認清楚的數字。

→ 詳見 [[12-cluster-operations]]
</details>

**Q7.** 🔵（情境診斷）同事的 Node 在高負載時頻繁出現異常，你懷疑跟 `kube-reserved` 設定有關，這個設定的用途是什麼？

<details>
<summary>看答案</summary>

kube-reserved 以及 system-reserved 會在 Node 的可分配資源計算裡預先扣掉一部分 CPU／Memory，保留給 kubelet、container runtime 等系統元件自己使用，避免業務 Pod 把資源用到滿，導致連 kubelet 自己都資源不足或被系統 OOM，進而影響整個 Node 的穩定性。沒設定或設得太少，容易在高負載時發生節點層級的異常。

→ 詳見 [[12-cluster-operations]]
</details>

**Q8.** 🟢（設計決策）同事說「我們在 minikube 上測試升級流程都順利，正式環境應該也沒問題」，你會提醒他哪些落差？

<details>
<summary>看答案</summary>

minikube 通常只有單一 control plane 節點，不會遇到多節點 etcd 的 quorum、多 control plane 節點滾動升級的順序問題；minikube 的網路與儲存都是簡化模擬，不會暴露正式環境雲端 LoadBalancer、跨可用區儲存綁定的真實狀況；正式環境還有正在承載真實流量的服務與 PDB 的限制，這些都是 minikube 演練無法覆蓋到的風險，實際升級前應該在盡量貼近正式環境拓樸的 staging 叢集先演練過一輪。

→ 詳見 [[12-cluster-operations]]
</details>

**Q9.** 🔵 規劃一次 etcd 還原演練，會依照什麼流程走？

<details>
<summary>看答案</summary>

先在非正式環境定期排練整套流程，而不是只在真正出事才第一次嘗試：取得最新的 etcd snapshot、確認 snapshot 完整性、依照文件的還原指令把 snapshot 還原到一個獨立的測試 etcd 上、重新指向 apiserver 驗證叢集物件是否正確回復、記錄整個流程實際花費的時間並對照 RTO 是否達標。定期演練的意義在於備份檔案存在不等於還原得回來，唯一能驗證的方式就是真的跑一次還原。

→ 詳見 [[12-cluster-operations]]
</details>

## 第 13 章｜故障排除

排錯這一章沒有新知識，考的是「舊知識能不能在壓力下被正確調用」。分層定位法、Pod 狀態機、`kubectl describe` 的 Events——這些工具你可能都聽過，但真正的考驗是同事丟一句「連不到」的時候，你能不能在腦中排出正確的檢查順序，而不是亂槍打鳥。

**Q1.** 🟢 分層定位法建議先問「壞在哪一層」，大致有哪些層？

<details>
<summary>看答案</summary>

大致由外而內可以分成：使用者／流量入口層（DNS、Ingress）、Service／網路層、Pod／容器層、排程／資源層、K8s API／RBAC 權限層，以及交付層（CI/CD、Helm、ArgoCD 有沒有正確把東西送出去）。先判斷問題落在哪一層，能大幅縮小要檢查的範圍，避免在錯的層級瞎繞。

→ 詳見 [[13-troubleshooting]]
</details>

**Q2.** 🔵 Pod 的 Pending、ContainerCreating、CrashLoopBackOff、ImagePullBackOff 這幾個狀態各自指向什麼方向去查？

<details>
<summary>看答案</summary>

Pending 通常指向排程階段的問題，例如資源不足、taint／toleration 不合，或 PVC 綁定不了；ContainerCreating 卡住通常是 image 拉取慢或 volume 掛載有問題；ImagePullBackOff 明確指向 image 名稱錯誤、tag 不存在或 registry 認證失敗；CrashLoopBackOff 代表容器有啟動、但很快就結束或被判定失敗然後不斷重試，要看應用本身的 log 或探針設定。

→ 詳見 [[13-troubleshooting]]
</details>

**Q3.** 🟢 `kubectl describe` 裡的 Events 區塊為什麼常常是排查的第一站？

<details>
<summary>看答案</summary>

Events 記錄了這個物件從建立以來，K8s 各元件針對它做過的重要動作與失敗訊息，用時間序列呈現，例如排程失敗的具體原因、探針失敗的次數與訊息、image 拉取失敗的錯誤內容，通常不需要深入 log 就能先掌握大概方向，是診斷流程裡性價比最高的第一步。

→ 詳見 [[13-troubleshooting]]
</details>

**Q4.** 🔵（情境診斷）容器一直重啟，`kubectl logs` 卻看不到有意義的錯誤訊息，你會怎麼繼續查？

<details>
<summary>看答案</summary>

先用 `kubectl logs <pod> --previous` 去看上一次重啟前那個容器實例的 log，因為預設 `kubectl logs` 只顯示目前這個容器實例的紀錄，如果它剛重啟沒多久，可能還沒印出真正導致上次崩潰的錯誤；如果 previous log 也沒有線索，改用 `kubectl describe` 看 Events 裡有沒有 OOMKilled 或探針失敗的紀錄，也可能是被 liveness probe 直接殺掉，而不是應用自己主動報錯結束。

→ 詳見 [[13-troubleshooting]]
</details>

**Q5.** 🔵 `kubectl debug` 這個指令解決了什麼傳統排查方式做不到的事？

<details>
<summary>看答案</summary>

很多正式環境的容器 image 為了安全與體積考量根本沒有 shell、沒有任何除錯工具，`kubectl exec` 進去也無從下手；`kubectl debug` 可以在不修改原本 Pod 定義的情況下，附加一個帶有完整除錯工具的臨時容器到目標 Pod，共享它的 network／process namespace，讓你能用熟悉的工具檢查一個原本連進去都無計可施的容器環境。

→ 詳見 [[13-troubleshooting]]
</details>

**Q6.** 🔴（情境診斷）服務 A 打服務 B 的 Service 名稱連不上，你發現對應的 Endpoints 是空的，你會依序往哪裡查？

<details>
<summary>看答案</summary>

Endpoints 空代表沒有任何 Pod 被這個 Service 選中，優先查 Service 的 `selector` 跟目標 Pod 的 `labels` 是否真的完全相符；再查符合 selector 的 Pod 是否存在且處於 Running；最後查這些 Pod 有沒有通過 readinessProbe，沒通過的 Pod 即使 Running 也不會出現在 Endpoints 裡。這三項是 Endpoints 為空最常見的成因，依序排除即可定位。

→ 詳見 [[13-troubleshooting]]
</details>

**Q7.** 🔵（情境診斷）同事的請求收到 403 Forbidden，你會怎麼一步步定位是哪個環節的 RBAC 問題？

<details>
<summary>看答案</summary>

先確認是哪個身份在發請求；用 `kubectl auth can-i` 搭配 `--as` 直接驗證這個身份有沒有權限；如果沒有，往回查對應的 RoleBinding／ClusterRoleBinding 是否存在、subject 是否精確指向這個身份，綁定的 Role／ClusterRole 裡的 rules 是否真的涵蓋這個 apiGroup、resource、verb 的組合，逐項比對通常就能找出漏掉的那一環。

→ 詳見 [[13-troubleshooting]]
</details>

**Q8.** 🟢 為什麼「交付層」也要被納入排查範圍，而不是只看叢集內部？

<details>
<summary>看答案</summary>

有些問題的根因根本不在叢集內，而是在把設定送進叢集之前的環節：Helm values 傳錯、ArgoCD 的 targetRevision 指向舊分支、CI pipeline 建置出的 image tag 沒有真的更新，或 ArgoCD 的 Sync 根本沒有被觸發。如果只在叢集裡打轉檢查 Pod、Service，卻沒想到叢集裡跑的根本不是以為推上去的那個版本，就會在錯誤的地方一直繞圈子。

→ 詳見 [[13-troubleshooting]]
</details>

**Q9.** 🟢 為什麼本章要用十九個真實踩坑案例做總結，而不只是條列排查步驟？

<details>
<summary>看答案</summary>

因為真實世界的問題往往是好幾個因素疊加造成的非典型組合，例如「ConfigMap 改了但用了 subPath 所以沒更新」或「NetworkPolicy 裝了但 CNI 不支援所以沒生效」，單看抽象的排查步驟不容易建立症狀對應根因的直覺；透過大量真實案例反覆練習「看到症狀、聯想可能根因、驗證」的思考路徑，才能培養出經驗老道的維運直覺。

→ 詳見 [[13-troubleshooting]]
</details>

## 第 14 章｜Prometheus 與 Grafana

監控這一章最容易被輕忽的地方，是把「有裝 Prometheus」跟「真的看得懂 PromQL 在算什麼」畫上等號。這一章的題目會逼你解釋 rate 跟 irate 為什麼不一樣、Histogram 為什麼能跨副本聚合而 Summary 不行，因為這些正是寫出一條「看起來對、其實在騙你」的告警規則的常見來源。

**Q1.** 🟢 可觀測性的三支柱是什麼？各自回答什麼問題？

<details>
<summary>看答案</summary>

Metrics 回答系統現在整體狀況如何、有沒有異常趨勢，適合做告警與長期趨勢分析；Logs 回答當下發生的具體事件細節是什麼，適合深入追查單一事件；Traces 回答一個請求橫跨多個服務時，時間都花在哪一段，適合微服務架構下的延遲分析。三者互補，不能只靠其中一種就涵蓋所有排查需求。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q2.** 🔵（情境診斷）同事的 CronJob 每次執行完，Prometheus 上都抓不到那次執行的數據，你會怎麼跟他解釋、又該怎麼解決？

<details>
<summary>看答案</summary>

Prometheus 用 Pull 模型，主動去對象那裡抓數據，但短生命週期的批次任務可能在 Prometheus 下次來抓之前就已經結束消失，數據自然抓不到；這種情況需要讓任務在結束前主動把最後的數據推給 Pushgateway 暫存著，等 Prometheus 之後照常來抓取 Pushgateway 上的資料，藉此彌補 Pull 模型對短生命週期任務不友善的缺口。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q3.** 🟢（辨析）cAdvisor、kube-state-metrics、metrics-server 三者常被搞混，分工是什麼？

<details>
<summary>看答案</summary>

cAdvisor 提供容器層級的實際資源使用數據，例如 CPU、記憶體、網路用量；kube-state-metrics 提供的是 K8s API 物件狀態本身的指標，例如 Deployment 期望副本數是多少、目前有幾個 Pod 是 Ready；metrics-server 是一個輕量、只在記憶體保存短期資料的服務，專門提供給 HPA、`kubectl top` 這類即時查詢使用，不是給長期歷史分析用的。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q4.** 🔴（情境診斷）同事把 user ID 當成 metric 的 label 加進去，結果 Prometheus 突然記憶體暴增、查詢變慢，這是什麼問題？

<details>
<summary>看答案</summary>

這就是 cardinality 爆炸：Prometheus 的每一組獨特 label 組合都會產生一條獨立的時間序列，label 的可能值數量越多，時間序列的總數就以乘積方式暴增。user ID 這種高基數欄位如果拿來當 label，等於瞬間製造出數十萬條時間序列，讓 Prometheus 的記憶體用量與查詢效能急遽惡化。高基數的維度資訊應該放進 log 而非 metric label。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q5.** 🟢 四種 Metric 類型（Counter、Gauge、Histogram、Summary）分別用在什麼場景？

<details>
<summary>看答案</summary>

Counter 是只會累加不會減少的計數器，例如累計請求數，適合搭配 rate() 看變化率；Gauge 是可以上下浮動的即時數值，例如目前記憶體用量；Histogram 把觀測值分佈到預先定義的桶裡，可以在伺服器端做跨實例聚合並算出分位數；Summary 在客戶端直接算好分位數再回報，適合單一實例的精確分位數，但無法跨實例正確聚合。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q6.** 🔴（辨析）Histogram 和 Summary 都能算分位數，為什麼說只有 Histogram 可以跨 Pod 聚合？

<details>
<summary>看答案</summary>

Summary 的分位數是在應用程式端當下直接計算完成後才回報，這是這一個實例的統計結果，把多個實例算好的分位數加總平均在數學上是不正確的；Histogram 回報的是每個桶的累計次數，這種原始計數資料可以先跨多個實例把每個桶的次數加總，再用 `histogram_quantile()` 對加總後的桶分佈算一次分位數，這樣算出來的才是整體而非單一實例的正確分位數，這是多副本服務監控通常選 Histogram 而非 Summary 的關鍵原因。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q7.** 🔵（情境診斷）同事的告警規則用了 `irate` 結果一直誤觸發，你會怎麼解釋 rate、irate、increase 這三個函式的差異？

<details>
<summary>看答案</summary>

`increase()` 回傳指定時間範圍內的總增量；`rate()` 把這段範圍內的增量換算成每秒平均增長率，適合用在告警規則與圖表上做平滑趨勢觀察；`irate()` 只用範圍內最後兩個資料點算瞬時增長率，對突發尖峰更敏感，但曲線更抖動、也更容易受單一雜訊點影響。告警規則建議用 rate 而非 irate，irate 通常只適合互動式的即時儀表板。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q8.** 🔵（機制原理）`histogram_quantile` 搭配 `by (le)` 是在做什麼？

<details>
<summary>看答案</summary>

`by (le)` 是刻意保留 `le`（桶的上界標籤）這個維度不被聚合掉，讓 `sum(rate(...))` 把其他維度（例如不同 Pod 副本）加總、但仍然保留每個桶各自的加總結果；`histogram_quantile` 需要看到完整的桶分佈才能正確內插算出分位數，如果連 `le` 都被 sum 掉，就會失去桶的邊界資訊，算出來的分位數會是錯的。

→ 詳見 [[14-prometheus-grafana]]
</details>

**Q9.** 🟢 USE 和 RED 這兩套監控方法論分別適合用在什麼類型的對象上？

<details>
<summary>看答案</summary>

USE（Utilization、Saturation、Errors）適合用在資源型的對象，例如 CPU、記憶體、磁碟這類資源本身的健康狀況；RED（Rate、Errors、Duration）適合用在服務或請求型的對象，關注這個服務每秒處理多少請求、錯誤率多少、延遲多少。兩者不是互斥的，實務上通常同時對基礎設施資源用 USE、對應用服務本身用 RED，組合出完整的監控覆蓋。

→ 詳見 [[14-prometheus-grafana]]
</details>

## 第 15 章｜ELK 與 Elastic Stack

這一章的起點是 `kubectl logs` 的三個限制：看不到檔案日誌、不持久、不能跨服務關聯搜尋。ELK 整套系統存在的理由，就是把這三個限制一一補起來。題目裡也刻意放進磁碟水位、JVM heap 上限這類「平常沒感覺、一出事就是整個叢集寫入全部失敗」的維運細節。

**Q1.** 🟢 `kubectl logs` 有哪三個限制，導致大型環境需要一整套集中式日誌系統？

<details>
<summary>看答案</summary>

只能看容器的 stdout／stderr，應用寫進檔案裡的日誌它看不到；日誌沒有真正持久化保存，容器被刪除或節點被回收後日誌就跟著消失；也沒有跨多個 Pod、多個服務彙整搜尋與長期保存的能力，出事後想做跨時間、跨服務的關聯分析幾乎做不到。這些限制正是 ELK 這類集中式日誌系統存在的理由。

→ 詳見 [[15-elk-elastic]]
</details>

**Q2.** 🔵 容器的日誌是透過什麼路徑，最終進到集中式日誌系統的？

<details>
<summary>看答案</summary>

容器的 stdout／stderr 預設會被 container runtime 寫到節點本機的檔案；節點上跑的 log agent（如 Filebeat，通常以 DaemonSet 形式部署，每個 Node 都有一份）負責即時監看、讀取這些本機日誌檔案，做基本的解析與 metadata 補充，例如加上 Pod 名稱、namespace 標籤，再把資料轉送到後端，可能先經過 Logstash 做更複雜的處理，也可能直接送進 Elasticsearch 做索引儲存。

→ 詳見 [[15-elk-elastic]]
</details>

**Q3.** 🟢（情境診斷）同事想用 term query 精確比對一個 text 欄位卻怎麼都查不到，你會怎麼解釋 text 和 keyword 的差別？

<details>
<summary>看答案</summary>

text 型別的欄位在索引時會經過 analyzer 拆解成一個個詞元，適合做全文檢索，但不適合直接拿來做精確比對，因為它存的是拆開後的詞而非完整原始字串；keyword 型別完整保留原始字串不做任何拆解，適合做精確比對、排序、聚合。實務上常見做法是同一個欄位同時建立 text 與 keyword 兩種子欄位，各自用在對的場景。

→ 詳見 [[15-elk-elastic]]
</details>

**Q4.** 🔵 Elasticsearch 的 shard 為什麼說是「不可變」的？這跟它查得快有什麼關係？

<details>
<summary>看答案</summary>

Elasticsearch 底層每個 shard 由多個不可變的 Lucene segment 組成，資料寫入時是先寫進一個新的 segment，而不是修改既有 segment 的內容；更新或刪除文件實際上是標記舊文件為刪除、再寫入一份新文件到新的 segment，背景才會定期合併舊 segment。這種不可變特性讓底層可以放心利用作業系統的檔案快取，並針對唯讀資料建立高效的倒排索引結構，是查詢速度快的重要原因之一。

→ 詳見 [[15-elk-elastic]]
</details>

**Q5.** 🔵（辨析）query context 和 filter context 的差別是什麼？為什麼能過濾的條件盡量放 filter？

<details>
<summary>看答案</summary>

query context 會計算每份文件跟查詢條件的相關性分數，結果依分數排序，適合用在需要判斷哪個結果更相關的全文檢索場景；filter context 只單純判斷符合或不符合，是二元的是非題，不計算分數，Elasticsearch 對 filter context 的結果會自動做快取。像是時間範圍內、某個欄位等於某值這類是非判斷，放進 filter context 既能受益於快取又不會浪費算力去計算用不到的相關性分數。

→ 詳見 [[15-elk-elastic]]
</details>

**Q6.** 🔴（情境診斷）同事說 Elasticsearch 突然全部索引變成唯讀，寫入請求都失敗，你會先懷疑什麼？

<details>
<summary>看答案</summary>

最常見的原因是磁碟使用率觸發了 disk watermark 保護機制：Elasticsearch 有 low、high、flood-stage 三個水位門檻，一旦磁碟使用率超過 flood-stage，為了防止把磁碟塞爆，Elasticsearch 會自動把受影響節點上的索引切成唯讀模式，拒絕新的寫入。排查時應該先查各節點磁碟使用率，清出空間或調整 ILM 保留策略之後，還要記得手動把索引的唯讀設定解除，因為即使磁碟空間騰出來了，唯讀狀態不會自動恢復。

→ 詳見 [[15-elk-elastic]]
</details>

**Q7.** 🟢 ILM（索引生命週期管理）大致把索引分成哪幾個階段？解決了什麼營運痛點？

<details>
<summary>看答案</summary>

典型分成 Hot（剛寫入、查詢頻繁，用效能較好的硬體）、Warm（不再寫入但偶爾還會查詢）、Cold（很少查詢、可以用更便宜的儲存）、Delete（超過保留期限自動刪除）幾個階段。它解決的痛點是日誌資料量會持續累積，若沒有自動化的生命週期管理，磁碟遲早會被塞滿；透過 ILM 定義好每個階段的天數與動作，可以自動把日漸老舊的索引移到便宜儲存、最終自動刪除，不需要人工手動維護。

→ 詳見 [[15-elk-elastic]]
</details>

**Q8.** 🔴（情境診斷）同事把 Elasticsearch node 的 JVM heap 從 30GB 加到 64GB，結果查詢反而變慢，為什麼？

<details>
<summary>看答案</summary>

這跟 JVM 的指標壓縮技術有關：當 heap 大小在一個門檻以下時，JVM 可以用壓縮後的指標定址到更大的記憶體範圍，效率較高；一旦 heap 超過這個門檻，實務上大約是三十二 GB 左右，JVM 就必須切換回未壓縮的指標，每個物件參照占用的空間反而變大，等於堆更多記憶體給 JVM，實際可用的有效容量卻可能不增反減。因此 heap 建議設定在這個甜蜜點附近，剩餘記憶體留給作業系統的檔案快取，這對 Elasticsearch 的讀取效能同樣重要。

→ 詳見 [[15-elk-elastic]]
</details>

## 紅色警戒清單

以下十八個知識點是全書裡最容易被誤解、也最常在面試與實務事故中出現的地雷。如果你能不看答案就把「正確理解」欄講清楚，這套教材就真的內化了。

| 知識點 | 多數人的錯誤認知 | 正確理解 | 章節 |
| --- | --- | --- | --- |
| RWO 存取模式 | 只能被一個 Pod 掛載 | 只能被一個 Node 以讀寫模式掛載，同 Node 上多個 Pod 理論上可共用；只有 ReadWriteOncePod 才真正限定單一 Pod | [[06-config-and-storage]] |
| Secret 的保護力 | base64 就是加密 | base64 只是編碼，沒有任何保護效果，需靠 etcd 加密與 RBAC 才有安全性 | [[06-config-and-storage]] |
| requests 與 limits 的分工 | limits 決定排到哪個 Node | scheduler 只看 requests 做排程決策，limits 只影響執行期 cgroup 的用量上限 | [[07-scheduling-and-resources]] |
| kubectl apply 的資料流向 | apiserver 主動把 Pod 推給 Node | 全程 pull-based，kubelet 主動 watch 到指派給自己的 Pod 才動手 | [[02-cluster-internals]] |
| ClusterIP 的本質 | 是一張真實或虛擬網卡 | 只是 kube-proxy 寫進 iptables／IPVS 的轉發規則入口，不對應任何網路介面 | [[05-networking]] |
| ConfigMap 更新行為 | 改了 ConfigMap 服務就自動變 | 環境變數注入不會熱更新；Volume 掛載會但有延遲，subPath 掛載則完全不會更新 | [[06-config-and-storage]] |
| NetworkPolicy 的預設行為 | 裝了 CNI 就有隔離 | 沒有 NetworkPolicy 物件時預設全通，且需要 CNI 本身支援才會真正生效 | [[05-networking]] |
| RBAC 的規則型態 | 可以寫規則明確拒絕 | RBAC 是純白名單，只累加不相減，沒有 deny 規則 | [[08-security-and-rbac]] |
| 憑證外洩的可撤銷性 | 憑證跟 token 一樣可以撤銷 | X.509 client 憑證到期前無法單獨撤銷，除非額外部署 CRL／OCSP | [[08-security-and-rbac]] |
| CMD 與 ENTRYPOINT 的關係 | 兩者互斥擇一 | 通常合併使用，ENTRYPOINT 定主程式、CMD 給可覆蓋的預設參數 | [[00-docker-foundations]] |
| dockershim 移除的影響範圍 | Docker 建的 image 不能跑在新版 K8s | 被移除的是執行期整合，OCI image 標準跟 image 建置工具無關 | [[00-docker-foundations]] |
| HPA 與 VPA 的相容性 | 兩者可以互補疊加 | 同時對同一個 workload 的同一種資源用 HPA 和 VPA 容易互相打架 | [[07-scheduling-and-resources]] |
| PVC 容量調整方向 | 可以隨意擴容也能縮容 | 多數 CSI 只支援擴容，不支援縮容 | [[06-config-and-storage]] |
| ArgoCD 的兩條狀態軸線 | Synced 就等於服務正常 | Sync Status 與 Health Status 是兩條互相獨立的軸線，需分開判讀 | [[11-argocd]] |
| etcd 節點數的取捨 | 節點越多可用性越高 | 需要奇數節點維持 quorum 效率，節點過多反而拖慢寫入延遲 | [[12-cluster-operations]] |
| Histogram 與 Summary 的聚合性 | 兩者都能跨副本算出正確分位數 | 只有 Histogram 能用 histogram_quantile 跨實例正確聚合，Summary 的分位數無法跨實例平均 | [[14-prometheus-grafana]] |
| text 與 keyword 欄位 | 都能直接做精確比對 | text 會被 analyzer 拆詞，精確比對與排序需要用 keyword | [[15-elk-elastic]] |
| kubectl logs 的能力邊界 | 是持久化的日誌系統 | 只存當前容器 stdout／stderr、有大小限制，Pod 刪除後即消失，需搭配 --previous 或集中式日誌系統 | [[13-troubleshooting]] |

## 連結

- [[k8s-mastery]]
- [[00-docker-foundations]]
- [[01-why-kubernetes]]
- [[02-cluster-internals]]
- [[03-api-and-yaml]]
- [[04-workloads]]
- [[05-networking]]
- [[06-config-and-storage]]
- [[07-scheduling-and-resources]]
- [[08-security-and-rbac]]
- [[09-extending-kubernetes]]
- [[10-helm]]
- [[11-argocd]]
- [[12-cluster-operations]]
- [[13-troubleshooting]]
- [[14-prometheus-grafana]]
- [[15-elk-elastic]]
