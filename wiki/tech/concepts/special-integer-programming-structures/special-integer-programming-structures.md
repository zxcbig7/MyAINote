---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, combinatorial-optimization, column-generation, vehicle-routing]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.9〈Building Integer Programming Models I〉§9.5–9.6, pp.189–205

## 為什麼要替特定的 IP 問題單獨立傳

[[integer-programming-fundamentals]] 教的是一套通用工具箱——指示變數、邏輯轉換、SOS、七種額外條件——用來把任意的邏輯需求塞進一個原本的 LP 模型。但工具箱之外,IP 領域裡還存在一群**已經被研究到出了名字、累積了大量理論與求解經驗**的問題型態:它們的結構如此常見、如此規律,以至於「認出自己的問題其實是某某已知結構」這件事本身,就能省下大量重新發明輪子的力氣——你可以直接借用文獻裡針對這個結構量身打造的演算法、近似方法,甚至只是借用「這類問題通常有多難解」的經驗值,提前預估自己的模型會不會失控。這一節要介紹的,正是這樣一組特殊結構:set covering、set packing、set partitioning 三兄弟、knapsack problem、travelling salesman problem 及其推廣 vehicle routing problem、quadratic assignment problem,最後以 column generation——一套專門對付「變數多到天文數字」的技巧——收尾。Williams 也提醒,這些結構雖然在理論文獻裡佔據大量篇幅,但實務上大多數 IP 模型並不屬於這幾類,而是像 [[integer-programming-fundamentals]] 講的那樣,由額外條件擴充出來的一般 MIP 模型;讀這一節時,重點不是背誦每個問題的公式,而是培養「看到問題描述,聯想到它可能是哪種結構」的辨識力。

## 9.5.1 Set covering problem:用最少的成本覆蓋每一個對象

這類問題的抽象描述是:給定一個物件集合 $S=\{1,2,\ldots,m\}$,以及 $S$ 的一族子集合 $\mathscr{G}$,$\mathscr{G}$ 裡每個子集合都各自帶有一個成本。目標是從 $\mathscr{G}$ 裡選出若干個子集合,讓它們的聯集**覆蓋(cover)**整個 $S$,同時使選中子集合的總成本最小。書中給了一個具體的小例子:$S=(1,2,3,4,5)$,$\mathscr{G}=\{(1,2),(1,3,5),(2,4,5),(3),(1),(4,5)\}$,每個成員成本都是 1;$(1,2)$、$(1,3,5)$、$(2,4,5)$ 就是一個可行的 cover。

建成 0-1 PIP 模型的方式,是為 $\mathscr{G}$ 的每個成員(每個候選子集合)引入一個 0-1 變數:

$$\delta_i = \begin{cases}1 & \text{若 } \mathscr{G} \text{ 的第 } i \text{ 個成員被選入 cover}\\0 & \text{否則}\end{cases}$$

限制式的邏輯是:對 $S$ 裡的每一個對象,至少要有一個「包含它」的候選子集合被選中。以書中的例子而言,要覆蓋成員 1,就必須在 $(1,2)$、$(1,3,5)$、$(1)$ 這三個含有 1 的候選子集合裡至少選一個,寫成限制式就是「這三個候選子集合對應的 $\delta_i$ 加總 $\ge 1$」;$S$ 裡其他每個成員也各自對應一條類似的限制式。如果目標只是單純極小化用到的候選子集合個數,完整模型就是

$$\text{Minimize } \delta_1+\delta_2+\delta_3+\delta_4+\delta_5+\delta_6$$

搭配五條「每個 $S$ 成員至少被覆蓋一次」的 $\ge 1$ 限制式(對應書中的 (9.107)–(9.111))。如果不同候選子集合的成本不同,只需要把目標函數換成加權和即可。

這個模型有三個一起出現、定義了「set covering problem」這個名稱的結構特徵:問題是**極小化**;所有限制式都是 **$\ge$** 型;右手邊(RHS)係數全部是 **1**;矩陣裡其餘的係數全部是 **0 或 1**。只要一個 0-1 PIP 模型同時具備這三項特徵,就可以歸類為 set covering problem。放寬 RHS 恆為 1 這項(允許某些 RHS 是更大的正整數,代表某個對象需要被覆蓋不只一次),得到 **weighted set covering problem**;如果連矩陣係數也放寬到允許 $\pm1$,則得到 **generalized set covering problem**。

Set covering problem 最著名的應用是**機組員排班(aircrew scheduling)**:$S$ 的成員是航空公司必須涵蓋的每一段航班(leg),$\mathscr{G}$ 的成員是一份份可能的機組員排班表(roster,涵蓋一段時間裡的一連串航班組合)。常見的目標,是在涵蓋所有航班的前提下,用最少數量的機組員排班表達成。

值得記住的一個計算性質:set covering problem 的 LP relaxation 最適解,必然是這個 LP 可行域的一個 vertex(頂點)解——這跟 [[lp-applications-and-networks]] 提到的 transportation/assignment problem 有相似之處。但這個 vertex 解一般而言**不會**剛好等於對應 IP 模型的整數最適解(雖然有時候會)——不過,從這個連續最適解出發,通常只需要相對少的幾步就能找到整數最適解。實務上,set covering problem 真正的困難,往往不是來自問題本身的結構,而是來自它的**規模**——候選子集合 $\mathscr{G}$ 的數量經常是天文數字,遠遠超過限制式的數量。這正是為什麼 9.6 節的 column generation 技巧,經常是處理 set covering problem 的關鍵配套手段。

## 9.5.2 Set packing problem:在不重疊的前提下塞入最多價值

Set packing problem 的抽象描述,跟 set covering problem 幾乎一模一樣共用同一套語言:給定物件集合 $S=\{1,2,\ldots,m\}$,以及一族子集合 $\mathscr{G}$,這次每個子集合帶有的是**價值**(而非成本)。但目標反過來了:在**不允許任何重疊**的前提下,盡量把 $\mathscr{G}$ 的成員「塞(pack)」進 $S$ 裡,使總價值最大。書中的例子:$S=(1,2,3,4,5,6)$,$\mathscr{G}=\{(1,2,5),(1,3),(2,4),(3,6),(2,3,6)\}$,一個可行的 packing 是 $(1,2,5)$ 與 $(3,6)$。

同樣用 0-1 變數 $\delta_i$ 表示 $\mathscr{G}$ 的第 $i$ 個成員是否入選,但限制式的邏輯換成「$S$ 的每個成員最多只能出現在一個入選的子集合裡」,也就是每條限制式改成 **$\le 1$**。目標函數則是極大化 $\sum\delta_i$(或加權版本)。

Set packing problem 的三項結構特徵是:問題是**極大化**;所有限制式都是 **$\le$** 型;RHS 係數全部是 **1**;其餘矩陣係數是 **0 或 1**——恰好是 set covering problem 三項特徵的鏡像。書中還指出一個有趣但實務意義有限的觀察:如果目標係數都設為 1,set packing 問題對應的 LP,恰好是同樣把目標係數設為 1 的 set covering 問題所對應 LP 的**對偶(dual)**——不過要小心,這裡的兩個問題所指涉的 $S$ 與 $\mathscr{G}$ 通常是不同的集合,對偶關係只在數學結構上成立,不代表兩者是同一個實際問題。跟 set covering 一樣,放寬 RHS 或矩陣係數範圍,可以得到 weighted / generalized set packing problem。

Set packing problem 有一個值得記住的特例——**matching problem**:如果 $S$ 的成員可以表示成一張圖(graph)的節點(node),而 $\mathscr{G}$ 的每個成員剛好是連接兩個節點的一條邊(arc),這個「盡量配對(pair up)最多節點」的問題就是 matching problem。Set packing problem 與下面要介紹的 set partitioning problem,彼此可以互相轉換,關係非常緊密。

## 9.5.3 Set partitioning problem:覆蓋且不重疊,兩者兼具

Set partitioning problem 同樣共用 $S$、$\mathscr{G}$ 的語言,但這次要求**同時**達成 set covering 的「每個對象都要被覆蓋」與 set packing 的「不能有任何重疊」——換句話說,$\mathscr{G}$ 選出的子集合要構成 $S$ 的一個**分割(partition)**,每個對象恰好出現在一個入選的子集合裡。建模上非常直接:把 set covering 模型裡原本的 $\ge$ 限制式,全部換成**等式** $=1$。用前面 set covering 的同一個例子,原本的 (9.107)–(9.111) 換成等式後,一個可行的分割是 $(1,2)$、$(1,3,5)$... (需要重選使其不重疊)——書中示範的可行分割是 $(1,2)$、$(3)$ 與 $(4,5)$。

Set partitioning problem 最直觀的應用場景,同樣是**機組員排班**:如果規定機組員不能以「乘客」身分搭乘其他航班(也就是每段航班恰好、且只能被一份排班表涵蓋一次,不允許重複涵蓋),就會從 set covering 變成 set partitioning。另一個常見應用是**政治選區劃分(political districting)**——把選民劃分成若干選區,每位選民恰好屬於一個選區,通常還會加上「選區總數固定」的額外限制式,目標一般是極小化「各選區選民人數」對「平均選民人數」的最大偏差(這是一種 minimax 目標)。

Set packing 與 set partitioning 之間有一個值得記住的等價關係:如果對 set packing 問題裡每一條 $\le$ 限制式引入一個(只能取 0 或 1 的)slack 變數,這條限制式就變成等式,而這個 slack 變數本身也可以被當成 $\mathscr{G}$ 裡新增的一個(只覆蓋一個虛擬對象的)成員——這樣一來,set packing 問題就變成了一個 set partitioning 問題。反過來,把 set partitioning 的等式限制式 $\sum_j a_j\delta_j=1$ 改寫成 $\sum_j a_j\delta_j\le 1$,再引入一個新的 0-1 變數 $\delta$、給它一個夠大(對極小化問題而言是正、對極大化問題而言是負)的目標函數係數強迫它在最適解中為 0,也能把 set partitioning 轉換回 set packing 或(用類似手法)set covering 問題。

這裡有一個容易被忽略、卻很值得記住的不對稱性:set partitioning(或 packing)問題,一般而言比對應的 set covering 問題**更容易求解**——因為等式限制式比 $\ge$/$\le$ 限制式更「緊」,把對應的 LP 可行域限制得更小,因此更貼近 IP 解的凸包。可以把一個 set partitioning(或 packing)問題轉換成一個 set covering 問題(如上所述),但反過來——把一個 set covering 問題轉換成 set partitioning——一般並不可行。這個不對稱性,恰好也解釋了為什麼 set covering problem(儘管結構上與另外兩者如此相似)在實務上被公認是比較難處理的一類。

## 9.5.4 Knapsack problem:只有一條限制式的 IP

**Knapsack problem** 是只含**單一限制式**的 PIP 問題,一般形式是

$$\text{Maximize } p_1\gamma_1+p_2\gamma_2+\cdots+p_n\gamma_n$$
$$\text{subject to } a_1\gamma_1+a_2\gamma_2+\cdots+a_n\gamma_n\le b$$

其中 $\gamma_1,\ldots,\gamma_n\ge 0$ 且必須取整數值。「knapsack(背包)」這個名字來自一個生動的比喻:一位健行者想在背包容量限制下,從一堆各有價值與重量的物品裡挑選要帶走的東西,以極大化總價值——這正是這個模型的單一限制式(總重量 $\le$ 背包容量)所對應的情境。如果再加上每個變數本身的上界限制(通常是 1),就得到最常見的 **0-1 knapsack problem**。

Knapsack problem 單獨、直接作為應用出現的機會其實不算太多,常見的例子包括 **project selection**(在預算限制下,從一堆候選專案裡挑選要執行哪些)、**capital budgeting**(資本預算分配),以及倉庫用不可分割單位的貨物填滿有限容量以極大化總價值的問題。knapsack problem 真正大量出現的場合,是作為 LP 或 IP 模型在求解過程中(尤其是產生新變數列時)反覆出現的**子問題**——這種用法的原始應用正是 **cutting stock problem**(見 Gilmore and Gomory, 1963, 1965,以及本頁 9.6 節的詳細示範)。

在計算上,knapsack problem 本身相對容易求解——branch and bound 可以處理,但如果需要大量反覆求解 knapsack 子問題(例如在 column generation 的過程中,每一輪都要解一次),更有效率的做法是用 **dynamic programming**。

## 9.5.5 Travelling salesman problem:最短的巡迴路線

**Travelling salesman problem(TSP)** 因為敘述極其簡單、卻異常難解,長期受到大量關注。情境是:一位業務員要從家裡出發,依序拜訪一批客戶,最後回到家,要找出總距離最短的拜訪順序。這個問題有很多變形與特例——不一定要求回到起點;距離常常是對稱的($A\to B$ 與 $B\to A$ 距離相同);它的推廣版本 **vehicle routing problem**(9.5.6 節)是把配送任務用數輛車完成的問題,反過來的「收件」問題(例如從郵筒收信件)也可以用同樣的方式處理。**Job sequencing**(排序一連串操作以極小化總轉換成本)也可以化約成 TSP,「城市之間的距離」對應到「操作之間的轉換(setup)成本」——書中甚至舉了一個生動的例子:在一連串噴漆作業中,排序顏色的順序以極小化總清潔刷子的時間,也是一個 TSP。

TSP 有多種 IP formulation,書中介紹了最基本的一種。設城市編號為 $0,1,\ldots,n$,引入 0-1 變數

$$\delta_{ij} = \begin{cases}1 & \text{若巡迴路線直接從 } i \text{ 走到 } j\\0 & \text{否則}\end{cases}$$

目標函數是極小化 $\sum_{i,j}c_{ij}\delta_{ij}$($c_{ij}$ 是 $i$、$j$ 之間的距離或成本)。有兩個顯然必須滿足的條件:「每個城市之後恰好緊接著一個城市」與「每個城市之前恰好緊接著一個城市」,分別對應限制式

$$\sum_{j=0,j\ne i}^{n}\delta_{ij}=1,\ i=0,1,\ldots,n \qquad\qquad \sum_{i=0,i\ne j}^{n}\delta_{ij}=1,\ j=0,1,\ldots,n$$

但問題在於:光靠這兩組限制式(其實就是一個 assignment problem,見 [[lp-applications-and-networks]])還不夠——它們允許出現**子巡迴(subtour)**,也就是把 $n+1$ 個城市拆成好幾個各自獨立、彼此不相連的小圈圈,而不是一條貫穿所有城市的完整路線。書中用一個八個城市的例子具體示範:滿足上述所有限制式的解,可能是「城市 0,1,2,3,5 圍成一圈」加上「城市 4,6,7 另外圍成一圈」這種兩個互不相連的子巡迴,而不是我們要的單一完整巡迴。

要排除子巡迴,原則上需要對**每一種**可能出現的子巡迴組合,各自加入一條「這個子集合裡的城市之間,邊的總數不能圍成完整的圈」的限制式,但這種限制式的數量隨城市數呈指數成長,不可能一次全部顯式寫出來。實務上的做法,是採取「按需添加(as needed)」的策略——先解一個沒有子巡迴限制的鬆弛模型,一旦解出來的結果出現子巡迴,就針對這個具體出現的子巡迴,臨時追加一條限制式排除它,然後重新求解,如此反覆,直到解出的巡迴不再有子巡迴為止。實務經驗顯示,通常只需要追加指數量級中極小的一部分,就能得到不含子巡迴的最適解。

除了這種「事後追加」的做法,文獻裡也發展出幾種**非指數規模**的 formulation,一次就能把子巡迴排除掉,雖然除了其中一種之外,其餘的 LP relaxation 都比傳統(Dantzig et al., 1954)formulation 更弱:**sequential formulation**(Miller et al., 1960)引入額外的變數代表每個城市被造訪的序號,用這些序號建立限制式排除子巡迴;**flow-based formulation**(Gavish and Graves, 1978)引入流量變數,只允許流量出現在巡迴確實使用到的邊上,搭配跟 [[lp-applications-and-networks]] 網路流問題同樣的物料平衡限制式來排除子巡迴——這種變體的 LP relaxation 強度跟傳統 formulation 相同,但需要的變數與限制式數量是 $n^3$ 量級,大到不適合一次性求解整個模型;**time-staged formulation**(Vajda, 1961; Fox et al., 1980)則多引入一個代表「時間(階段)」的索引 $t$,讓變數 $\delta_{ijt}$ 表示第 $t$ 階段是否從城市 $i$ 走到城市 $j$,藉此在限制式中排除子巡迴。Orman and Williams(2006)系統性比較了八種不同的 formulation,依 LP relaxation 的強弱排出名次,結果顯示這個排名與具體問題實例無關,是一個相當穩定的結論。

實務上求解 TSP 有相當顯著的進展——Held and Karp(1971)提出的 branch and bound 演算法是至今最成功的方法之一,近年更有大幅度的計算能力突破(Applegate et al., 2006)。書中收錄的 MILK COLLECTION 案例(見 [[case-milk-collection]])與 LOST BAGGAGE DISTRIBUTION 案例(見 [[case-lost-baggage-distribution]]),都是 TSP 的變形應用。

## 9.5.6 Vehicle routing problem:多輛車、有容量限制的巡迴問題

**Vehicle routing problem(VRP)** 是 TSP 在實務上最重要的延伸:除了要決定拜訪客戶的**順序**(跟 TSP 一樣),還要決定**用哪一輛車**去拜訪哪些客戶——因為現在有數輛容量有限的車輛需要調度,而不是單一一位業務員。每位客戶有已知的需求量(通常假設只涉及單一種商品,但不難推廣到多種商品),此外常常還會有**time window**限制,要求某些客戶只能在特定時段之間收到配送。

書中把 VRP 表述為 TSP formulation 的延伸。設 $m$ 為車輛數,車輛 $k$ 的容量為 $Q_k$,客戶 $i$(客戶 0 為 depot,不計入)的需求量為 $q_i$,客戶 $i$、$j$ 之間所需時間為 $d_{ij}$,客戶 $i$ 必須在時間 $a_i$ 到 $b_i$ 之間收到配送。引入三組變數:

$$\delta_{ijk}=1 \text{ 若車輛 } k \text{ 直接從客戶 } i \text{ 開往客戶 } j$$
$$\gamma_{ik}=1 \text{ 若車輛 } k \text{ 拜訪客戶 } i$$
$$\tau_i = \text{車輛拜訪客戶 } i \text{ 的時間}$$

假設每位客戶(depot 除外)恰好由一輛車拜訪(沒有「拆單」配送)。以極小化總成本 $\sum_{ijk}c_{ij}\delta_{ijk}$ 為目標(書中也提到極小化所需車輛數、極小化最大耗時等其他可能目標),模型包含以下限制式:

- **流量守恆**:$\sum_j\delta_{ijk}=\sum_j\delta_{jik}=\gamma_{ik}$——若車輛 $k$ 拜訪客戶 $i$,則它恰好進入一次、離開一次。
- **客戶恰好被一輛車服務**:$\sum_k\gamma_{ik}=1$,對每個客戶 $i$(不含 depot)。
- **車輛若被使用必須造訪起點**:$\sum_i\gamma_{ik}\le\gamma_{1k}$——若車輛 $k$ 被用上,它必須拜訪第一個城鎮(作為出發的錨點)。
- **容量限制**:$\sum_iq_i\gamma_{ik}\le Q_k$——車輛 $k$ 服務的所有客戶需求總和,不能超過它的容量。
- **時間遞移(大 $M$ 技巧)**:$\tau_i-\tau_j\le M(1-\delta_{ijk})-d_{ij}$——若客戶 $j$ 緊接在客戶 $i$ 之後被拜訪,則 $j$ 的拜訪時間至少要比 $i$ 晚 $d_{ij}$;若 $\delta_{ijk}=0$(這段行程沒被使用),則大 $M$ 讓限制式自動失效。
- **time window**:$a_i\le\tau_i\le b_i$。

跟 TSP 一樣,這個 formulation 同樣容易出現子巡迴,實務上通常也要靠「按需追加」子巡迴排除限制式的策略。由於規模與難度都比單純的 TSP 更高,這種完整寫出所有變數與限制式的 formulation,對中大型實例往往難以直接求解;另一種常見的替代做法是 **column generation**(9.6 節):把「一輛車的可行路線」(同時滿足容量與 time window 限制)當成一整個單位,獨立於主模型之外生成,再由主模型負責挑選與組合這些路線(Desrosiers et al., 1984)。MILK COLLECTION 與 LOST BAGGAGE DISTRIBUTION 兩個案例(見 [[case-milk-collection]]、[[case-lost-baggage-distribution]])同時也是 VRP 概念的具體示範。

## 9.5.7 Quadratic assignment problem:當指派彼此互相牽動

**Quadratic assignment problem(QAP)**是 [[lp-applications-and-networks]] 介紹過的 assignment problem 的推廣。回顧一下,assignment problem 本身可以當成 LP 求解、天生就有整數最適解;但 QAP 是一個貨真價實、通常非常難解的 IP 問題。

設 $S$、$T$ 是兩個大小相同(皆為 $n$)的物件集合,問題是把 $S$ 的每個成員恰好指派給 $T$ 的一個成員。跟 assignment problem 一樣,引入 0-1 變數

$$\delta_{ij} = \begin{cases}1 & \text{若 } i(\in S) \text{ 被指派給 } j(\in T)\\0 & \text{否則}\end{cases}$$

搭配兩組標準指派限制式:$\sum_j\delta_{ij}=1$(對每個 $i$)、$\sum_i\delta_{ij}=1$(對每個 $j$)。到這裡為止跟 assignment problem 完全一樣;真正的差異在**目標函數**。QAP 引入成本係數 $c_{ijkl}$,代表「$i$ 指派給 $j$」**同時**「$k$ 指派給 $l$」時所產生的成本——也就是說,這筆成本只有在 $\delta_{ij}=1$ 且 $\delta_{kl}=1$(即乘積 $\delta_{ij}\delta_{kl}=1$)時才會發生。目標函數因此是一個 0-1 變數的**二次**表達式:

$$\text{Minimize } \sum_{\substack{i,j,k,l=1\\k>i}}^{n}c_{ijkl}\delta_{ij}\delta_{kl}$$

其中 $k>i$ 這個條件是為了避免每一對指派的成本被重複計算兩次。係數 $c_{ijkl}$ 常見的產生方式,是拆成兩組獨立係數的乘積 $c_{ijkl}=t_{ik}d_{jl}$。

書中用兩個經典應用來讓這個抽象模型變得具體。**工廠選址**:$S$ 是 $n$ 間工廠,$T$ 是 $n$ 座城市,問題是把每間工廠指派到一座城市,以極小化工廠彼此之間的總通訊成本。$t_{ik}$ 代表工廠 $i$、$k$ 之間的通訊頻率,$d_{jl}$ 代表城市 $j$、$l$ 之間的單位通訊成本(與距離相關);兩間工廠之間的通訊成本,取決於它們彼此的通訊頻率**乘上**它們所在城市之間的距離成本——這正是 $c_{ijkl}=t_{ik}d_{jl}$ 這個乘積結構的來源。**電路板模組佈局**:$S$ 是要安裝的電子模組,$T$ 是背板上的預定位置,目標是極小化連接所有模組所需的總線長;$t_{ik}$ 是模組 $i$、$k$ 之間需要的連接線數,$d_{jl}$ 是位置 $j$、$l$ 之間的距離。

DECENTRALISATION 案例(見 [[case-decentralisation]])是 QAP 的一個修改版本——$S$、$T$ 不要求成員數相同,指派關係也不必是一對一。求解 QAP 的一種思路,是套用 [[integer-programming-fundamentals]] 9.2 節介紹過的 0-1 乘積線性化技巧,把 $\delta_{ij}\delta_{kl}$ 換成新的 0-1 變數,將二次目標函數轉換成線性形式——但對稍大的模型,這種轉換會讓變數與限制式數量急遽膨脹。整體而言,QAP 是數學規劃裡數一數二難解的組合問題;即使拿同樣規模的 TSP 相比,QAP 通常還要更難。

## 9.6 Column generation:當變數多到無法窮舉

到目前為止,不論是 set covering、set packing/partitioning,還是 vehicle routing problem,都指向同一個現實困境:候選變數(候選子集合、候選路線)的數量往往是天文數字,而最終出現在最適解裡的,只是其中極小一部分。既然如此,與其在求解一開始就把所有可能的變數(欄位,column)全部枚舉出來,不如反過來——只在求解過程中,**視需要才產生**看起來有機會進入最適解的變數,把它們逐一附加到模型裡。這正是 **column generation** 的核心想法,它與 [[structured-lp-models]] 提到的 decomposition 技巧一脈相承:decomposition 是把一個大模型拆成主模型(master)與子模型(subproblem),column generation 則是讓子模型負責產生候選解的組成部分(例如機組員排班表裡的一份份 roster、或空對空的一條條配送路線),交給主模型去挑選與組合。

書中用 **cutting stock problem**(Gilmore and Gomory, 1961, 1963)完整示範這套技巧的操作過程。這個問題也可以看成 **bin packing problem** 的一個特例——把不同大小的物件,盡量少用幾個固定大小的容器(bin)裝完。

**情境**:一位水管工人庫存著長度都是 19 公尺的標準水管。他手上有以下訂單:12 段 4 公尺、15 段 5 公尺、22 段 6 公尺。問題是:該怎麼從這些標準水管裁切出訂單所需的長度,才能使用最少數量的標準水管?

**壞的 formulation**。書中先示範一個直覺、但實務上很糟糕的寫法:設 $x_{ij}$ 為從編號 $j$ 的標準水管裁出的長度 $i$(4、5 或 6 公尺)水管數量,$\delta_j=1$ 表示標準水管 $j$ 有被使用。限制式包括「標準水管 $j$ 只有在被使用時才可能被裁切」($x_{1j}\le4\delta_j$ 等,即書中所謂的 SUB 型態限制)、「每根標準水管裁出的總長度不能超過 19 公尺」($4x_{1j}+5x_{2j}+6x_{3j}\le19$,對每個 $j$)、以及「訂單必須被滿足」($\sum_jx_{1j}\ge12$、$\sum_jx_{2j}\ge15$、$\sum_jx_{3j}\ge22$),目標函數是極小化 $\sum_j\delta_j$。這個模型最大的缺陷,是標準水管彼此完全**無法區分**,造成大量**對稱(symmetric)**的等價解——同一個實際切法,只要把哪一根「編號」為 1、哪一根編號為 2 互換,就會產生看起來不同、實際上完全等價的解。即使加上對稱破壞限制式(見 [[integer-programming-refinement]] 的討論),這個小到不能再小的例子,用一般套裝軟體求解也要花上出乎意料久的時間。

**用 column generation 改寫的好 formulation**。關鍵的觀察是:上面那個壞模型裡,真正核心的限制式是第二條(每根標準水管的長度限制)——這其實就是一個 **knapsack constraint**;它所有可行的解,對應到一種種可以從一根標準水管切出來的**裁切模式(pattern)**(包含裁切後剩下的廢料 $W$)。與其把 $x_{ij}$、$\delta_j$ 這種按「哪一根管子」編號的變數攪在一起,不如直接把每一種裁切模式當成一個變數:設 $\gamma_j$ = 模式 $j$ 被使用的次數。書中先列出三種可能的模式:

| 模式 | 組成 |
| --- | --- |
| 1 | 4, 4, 5, 5, W |
| 2 | 4, 4, 5, 6 |
| 3 | 4, 5, 5, 5 |

用這三種模式建出的模型是

$$\text{Minimize } \gamma_1+\gamma_2+\gamma_3$$
$$\text{subject to } 2\gamma_1+2\gamma_2+\gamma_3\ge12,\quad 2\gamma_1+\gamma_2+3\gamma_3\ge15,\quad \gamma_2\ge22$$

每個變數的一整欄係數,對應這個裁切模式裡各種長度出現的次數,RHS 則是各長度的訂單需求量。求解這個(只含三種模式的)IP,得到 $\gamma_1=0,\gamma_2=22,\gamma_3=0$,需要 22 根標準水管——顯然這還不是最好的答案,因為模型裡根本沒有考慮到其他可能更有效率的裁切模式。

**用 shadow price 找出「有用」的新模式**。這裡正是 column generation 的精髓所在:與其猜測還有哪些模式沒被考慮到,不如利用目前這個(小規模)LP relaxation 的 **shadow price** 來系統性地找。目前模型的 shadow price 是 $(0,0,1)$。如果打算引入一種新模式,包含 $a$ 段 4 公尺、$b$ 段 5 公尺、$c$ 段 6 公尺,它的 **reduced cost**(引入這個模式對目標函數的邊際改善量)是 $c-1$。因此,尋找「最有價值」新模式的做法,就是解一個新的 knapsack 子問題:

$$\text{Maximize } c-1 \quad \text{subject to } 4a+5b+6c\le19$$

這個子問題的最適解是 $a=b=0,c=3$(對應模式 4:6, 6, 6, W),目標值為 2,表示這個新模式確實能讓(LP relaxation 下的)標準水管使用量下降。把這條新的欄位附加進模型,重新求解,得到 $\gamma_1=0,\gamma_2=4,\gamma_3=4,\gamma_4=6$,只需要 14 根標準水管——比之前的 22 根有大幅改善。

用這一輪的新 shadow price($1/3,0,1/3$)再解一次子問題 $\text{Maximize }(1/3)a+(1/3)c-1$ 且 $4a+5b+6c\le19$,得到最適解 $a=4,b=c=0$,目標值 $1/3$(仍然大於 0,代表還有改善空間),對應模式 5:4, 4, 4, 4, W。附加這條新欄位、重新求解,結果得到的解跟前一輪(14 根標準水管)完全相同——這表示我們已經在**沒有窮舉那天文數字般龐大的候選模式集合**的情況下,得到了整個問題真正的最適解。

這個由淺入深的小例子,完整示範了 column generation 的操作循環:用當前(有限欄位的)LP relaxation 的 shadow price,驅動一個結構更簡單的子問題(這裡剛好是 9.5.4 節介紹過的 knapsack problem),找出下一個「有改善空間」的新欄位;不斷重複附加、重解,直到子問題再也找不到能帶來正向改善的新欄位為止,便能保證已經(在 LP 意義下)得到最適解。這套思路,正是實務上處理 set covering(機組員排班的候選 roster)、vehicle routing(候選車輛路線)這類候選變數多到無法窮舉的問題時,真正被大量使用的求解框架。

## 連結

- [[integer-programming-fundamentals]] — 上一節:指示變數、邏輯條件轉換、SOS、七種額外條件,是理解本頁這些特殊結構「為什麼可以這樣建模」的共同基礎
- [[lp-applications-and-networks]] — transportation problem 與 assignment problem 的 LP 最適解天生就是整數,是理解 set covering/packing 的 vertex 解性質、以及 QAP 為何比 assignment problem 難得多的重要對照
- [[integer-programming-refinement]] — 下一章:cutting stock 那個「壞 formulation」的對稱性問題,直接對應到這一章要講的 symmetry-breaking 技巧
- [[case-distribution-1]] — 案例研究:網路流與配送問題的具體建模示範,可與 TSP/VRP 的網路結構互相對照
- [[case-depot-location]] — 案例研究:選址問題的具體實例,可與 8.2 節提到的 depot location 分類、以及本頁 QAP 的工廠選址應用互相呼應
- [[case-milk-collection]]、[[case-lost-baggage-distribution]] — TSP/VRP 的具體變形應用案例
- [[case-decentralisation]] — QAP 的簡化實例
