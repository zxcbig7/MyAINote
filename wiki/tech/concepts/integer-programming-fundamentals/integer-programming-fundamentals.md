---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, 0-1-variables, branch-and-bound, special-ordered-sets]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.8〈Integer Programming〉, pp.155–164 與 Ch.9〈Building Integer Programming Models I〉§9.1–9.4, pp.165–188

## 從「偽裝成線性」到「真的容許離散」

[[nonlinear-and-separable-programming]] 講到最後,留下了一個沒有完全解決的問題:separable programming 用 $\lambda$-form 把非線性函數近似成分段線性,但那條「最多兩個相鄰 $\lambda_i$ 非零」的規定,只有在問題是 convex 時才會在最佳解中自動成立;一旦問題是 non-convex,或者我們需要精確保證(而不只是「大部分時候管用」),這條規定就沒辦法單靠線性限制式表達,必須引入貨真價實的整數變數才能強制執行。這正是本章要接手的地方——**integer programming(IP)**,也稱 **discrete programming**,是在 LP 的基礎上,容許部分或全部變數只能取整數值的一套建模與求解技術。

IP 的適用範圍,乍看之下容易被誤解得太窄。最直覺的用法,是拿整數變數去表示「不能拆開的東西」——車子、飛機、房子、員工,這些天生就是整數個的量。但 Williams 特別強調,這種「顯而易見」的用法反而不是 IP 真正的威力所在;IP 真正被大量使用的場合,是拿 **0-1(binary)變數**去表示「是/否」這種二元決策,再用線性限制式在這些 0-1 變數之間建立邏輯關聯。一個變數只能取 0 或 1,就足以編碼一整套「如果...則...」「至少一個成立」「不能同時發生」之類的條件——這也是本章(第 9 章前半)真正的重心。

一個模型如果只含整數變數,稱為 **pure integer programming(PIP)**模型;如果整數變數與一般連續變數並存(這是實務上更常見的情形),則稱為 **mixed integer programming(MIP)**模型。無論哪一種,IP 都比同樣規模的 LP 難解得多——LP 有 simplex algorithm 這套成熟到近乎萬能的工具,一個牽涉數千條限制式與變數的 LP 模型幾乎必然能在合理時間內解完;IP 沒有這種保證。建了一個 IP 模型,卻發現它在合理時間內無法求解,是建模者必須認真提防的風險,這也是為什麼 8.3 節要先花一點篇幅談求解方法——不是要讀者變成演算法專家,而是要讓建模者具備最基本的判斷力,知道自己的模型「大概好不好解」,以及求解過程能不能被介入、引導。

## 8.2 整數規劃適用在哪裡:五種問題型態

Williams 用一套鬆散的分類,勾勒出 IP 通常在什麼情境下派上用場。這個分類不是嚴謹的數學定義,類別之間也有重疊,但作為一張「什麼時候該考慮 IP」的檢核清單相當實用。

**離散的輸入輸出(8.2.1)。** 這是最直覺的一類——變數本身代表不可分割的數量,例如生產的飛機架數、雇用的員工人數。但作者提醒,這類「顯而易見」的 IP 應用其實不多見:如果變數的最適值原本就會是大數字(例如上百架飛機),直接用 LP 求解、再把小數解四捨五入到最近的整數,誤差通常微不足道,遠比認真解一個 IP 模型划算;只有當變數的值天生就很小(例如小於 5)時,四捨五入才可能把可行解變成不可行解,這時才真正需要 IP。另一種常見情境是「產能只能以離散的方式擴充」——例如加購整台機器才能提升處理能力,FACTORY PLANNING 2 案例(見 [[case-factory-planning-2]])就示範了這種情況。這一類還包括 **knapsack problem**:給定一個容量有限的容器(例如倉庫),要在容量限制下選擇一組不可分割的物品以極大化總價值——這個問題極少單獨出現,但作為子問題大量出現在更大的 LP 或 IP 模型裡(尤其是 cutting stock 問題,見 [[special-integer-programming-structures]] 的 column generation 討論)。

**帶有邏輯條件的問題(8.2.2)。** 這一類才是 IP 模型建構中最常見的情境:一個原本單純的 LP 模型(例如決定各產品的產量),想再加上一條「邏輯性」的額外規定,像是「如果生產產品 A,就必須也生產產品 B 或 C」。這種條件無法用傳統 LP 表達,但只要引入額外的 0-1 變數與限制式就能做到,這正是 9.2 節要系統性教的技巧。FOOD MANUFACTURE 2 案例同時示範了這種邏輯條件,以及另一種常見用途——限制一份配方裡能使用的原料種類數上限。

**組合問題(8.2.3)。** 這一類的特徵是可行解的數量astronomically 龐大,可以再細分成 **sequencing problems**(操作或造訪順序的最佳化,例如 job-shop scheduling、travelling salesman problem)與 **allocation problems**(把物件或人員分配到位置,例如 MARKET SHARE 問題——把客戶分派到公司內的各個服務部門,見 [[case-market-sharing]])。這一類裡有兩個容易被誤會、但其實**不需要** IP 的特例:**transportation problem** 與 **assignment problem**——這兩個問題的 LP 最適解,因為係數矩陣的結構特性,天生就會是整數,詳見 [[lp-applications-and-networks]]。反過來,assignment problem 一旦推廣成 **quadratic assignment problem**(指派的「成本」不再彼此獨立,而是跟其他指派互相牽動,產生二次項目標函數),就變成貨真價實、出了名難解的 IP 問題;DECENTRALISATION 案例正是一種簡化版的二次指派問題(見 [[case-decentralisation]])。組合問題裡還有兩個值得記住的特殊子類:**set partitioning problem**(常見於 assembly line balancing、機組員排班 aircrew scheduling)與帶有邏輯電路性質的 **logical design**(見 [[case-logical-design]])。這一整類問題的細節結構,留到 [[special-integer-programming-structures]] 深入展開。另外還有一個常見的實務應用是 **depot location problem**——決定要在哪些地點蓋倉庫或工廠,同時考慮建設成本與配送成本,DEPOT LOCATION 案例正是代表(見 [[case-depot-location]])。

**非線性問題(8.2.4)。** [[nonlinear-and-separable-programming]] 已經說明,可分的非線性問題可以用 separable programming 處理,但 non-convex 情況下只能保證局部最佳解。IP 提供了一條不同的路:如果願意付出更高的計算成本,IP 可以在 non-convex 問題上保證取得真正的全域最佳解。**special ordered sets**(SOS,見本頁 9.3 節)是把這種想法系統化、且能被求解器有效利用的工具。這一類還包括 **fixed charge problem**——當一項活動只要「有沒有進行」就會產生一筆與活動水準無關的固定門檻成本,這種不連續的成本結構用傳統 LP 無法表達,卻可以很自然地用 IP 建模(見本頁 9.1.3 節 Example 9.1)。

**網路問題(8.2.5)。** 大多數網路問題(運輸、指派、轉運、最短路徑等)本身就能用 LP 解決,見 [[lp-applications-and-networks]]。但少數衍生問題需要 IP,例如 PERT 網路上的**資源配置問題**(在有限人力或設備下,決定各項活動的排程順序以縮短專案總工期)——雖然可以formulate成 IP,但計算成本極高,實務上通常改用不保證最適、但可用的啟發式方法。圖論(graph theory)裡的**四色問題**(為地圖上色,使相鄰國家顏色不同,最少需要幾種顏色)也可以表達成 IP,但這類問題主要屬於理論領域,超出本書實務建模的範圍。

作者在這一節結尾特別提醒:上面五個類別涵蓋了大部分 IP 的應用場景,但實務上真正最常見的其實是第二類——一個原本的 LP 模型,被加上額外的邏輯條件,再用 0-1 變數與限制式擴充進去。純 PIP 模型(不含任何連續變數)反而較少見,通常是規模比較大的組合問題。無論落在哪個類別,IP 都有一個共同的風險:相較於 LP,IP 模型的求解難度對「怎麼寫這個模型」極度敏感——同一個問題,不同的 formulation 可能造成求解時間天壤之別,這也是 [[integer-programming-refinement]] 要深入處理的主題。

## 8.3 求解方法概觀:建模者需要知道多少

本書的立場很清楚:這一節無意完整交代 IP 演算法,只想讓模型建構者具備**最低限度**的理解,知道自己的模型會被怎麼解、以及有沒有辦法反過來影響求解的效率。求解 IP 的方法大致可分四類,彼此有重疊,某些成功處理大型問題的策略甚至同時借用了好幾類的元素。

**Cutting planes(8.3.1)。** 這類方法適用於一般的 MIP 問題。做法是先把整數限制拿掉,把 IP 問題當成 LP 來解(這稱為 **LP relaxation**);如果連續最適解剛好是整數,那就同時是 IP 的最適解,萬事大吉。如果不是整數,就有系統地加入額外的限制式(**cutting planes**,割平面),把目前這個非整數解「切」出可行域之外,但不切掉任何真正的整數可行解,然後重新求解、視需要重複這個過程。這個想法在數學上相當優雅(Gomory 1958 提出原始方法),但單獨使用在大型問題上並不特別成功;不過,與 branch and bound 結合之後(所謂 **branch and cut**),威力就大得多。

**Enumerative methods(8.3.2)。** 這類方法專門處理 0-1 PIP 問題。理論上,0-1 問題的可能解只有有限(雖然數量極為龐大)種組合;透過 tree search,可以只檢視其中一部分,把其餘的解系統性地判定為不可行或非最適而排除,不需要真的窮舉所有組合。Balas(1965)提出的 additive algorithm 是這類方法裡最知名的代表。

**Pseudo-Boolean methods(8.3.3)。** 這類方法試圖直接利用 0-1 PIP 問題與布林代數(Boolean algebra)之間的類比,把限制式改寫成布林表達式求解,而不是走一般的等式/不等式路線。在某些問題上,這樣寫出來的表達式相當精簡;但在另一些問題上,反而龐大而笨拙。就作者所知,當時沒有商用套裝軟體採用這類方法。

**Branch and bound methods(8.3.4)。** 這是**目前為止在實務 MIP 問題上最成功的方法**,幾乎所有商用 IP 套件的核心都是它。它的基本流程跟 cutting planes 一樣,先解 LP relaxation;如果連續最適解本身是整數,問題就解決了;否則,選一個不是整數值的變數,把它的可行範圍一分為二(例如某變數的 LP 解是 3.4,就分成「這個變數 $\le 3$」與「這個變數 $\ge 4$」兩個子問題),分別當成新的 LP 問題求解,如此建構出一棵搜尋樹,不斷往下分支、往下解,並利用已經找到的最好整數解,把子樹裡不可能比它更好的分支提早剪掉(這就是「bound」的作用)。這個方法本身在數學技巧上並不特別高深——這正是它出人意料成功的地方,而且它極具彈性,同一套框架可以用非常不同的分支策略去使用,聰明地運用這個彈性,往往能讓求解時間出現戲劇性的改善。這也解釋了為什麼一本談模型建構(而非演算法)的書,仍然值得花篇幅介紹它:branch and bound 進行的方式,會直接受到模型怎麼寫所影響,而這正是建模者能夠發揮影響力的地方,詳見 [[integer-programming-refinement]]。

有了「模型會怎麼被解」這個背景知識,接下來 9.1 到 9.4 節要正式進入建模本身:怎麼決定該用哪種離散變數、怎麼把邏輯條件轉成限制式、怎麼用 special ordered sets、以及一系列常見的「額外條件」該怎麼加進一個原本的 LP 模型裡。

## 9.1 離散變數的三種用途

在動手把邏輯條件寫成限制式之前,有必要先弄清楚:一個整數(或 0-1)變數,在模型裡到底可能扮演哪幾種角色。Williams 歸納出三種。

**不可分割的數量(9.1.1)。** 就是 8.1 節一開始提到的那種直覺用法——變數代表車子、飛機、房子這類天生整數個的量,不需要額外解釋。

**決策變數(9.1.2)。** 這是 IP 作為「建模語言」的核心用法:用整數變數表示「該從幾個可能的決策裡選哪一個」。最常見的形式是 0-1 變數,書中約定用希臘字母 $\delta$ 表示 0-1 變數,拉丁字母保留給連續(實數)變數;例如 $\delta=1$ 表示「應該蓋一座 depot」,$\delta=0$ 表示「不應該」。決策變數不一定得是 0-1——如果一個變數 $\gamma$ 代表三種互斥選項之一(例如 $\gamma=0$ 表示不建 depot、$\gamma=1$ 表示建 A 型 depot、$\gamma=2$ 表示建 B 型 depot),同樣可以用一個帶上界的整數變數表達;要確保一個整數變數只能取 0 或 1,只需要給它一個簡單上界(SUB)1 即可(所有變數預設下界為 0)。

**指示變數(9.1.3)。** 這是三種用途裡最精細、也最常被誤用的一種:當我們想在一個 LP 模型上「額外」施加條件時,通常會引入一個 0-1 變數 $\delta$,把它「連結(link)」到模型裡某個既有的連續變數,用來標示某種狀態。舉例來說,設 $x$ 是某原料在配方裡的用量,我們想用一個指示變數 $\delta$ 去區分「$x=0$」與「$x>0$」這兩種狀態。要強迫「只要 $x>0$,$\delta$ 就必須等於 1」,可以加入限制式

$$x - M\delta \le 0 \tag{9.1}$$

其中 $M$ 是 $x$ 的一個已知上界。這條式子的邏輯效果是 $x>0 \rightarrow \delta=1$(9.2)。注意這只是「單向」的連結:它保證了 $\delta=1$ 是 $x>0$ 的必要條件,卻沒有反過來保證 $\delta=0$ 時 $x$ 一定等於 0——如果模型本身的目標函數會傾向把 $\delta$ 壓到最小(例如 $\delta$ 有正的成本),那麼「$x=0$ 時 $\delta$ 也應該是 0」這件事通常會在最適解中自動成立,不需要額外限制式強制。

如果應用場景**確實**需要反向的保證(即 $x=0 \rightarrow \delta=0$,見 Equation 9.3),就必須額外加入限制式。但這裡有一個容易被忽略的哲學細節:「$\delta=1$ 就代表 $x>0$」這個條件,嚴格來說**沒有辦法**完全用一條限制式精確表達——因為這等於要求「哪怕原料只用了一個分子,也必須讓 $\delta=1$」,而現實中這種無窮小的門檻沒有實務意義。務實的做法,是選定一個夠小的門檻值 $m$,把條件放寬成「$\delta=1 \rightarrow x \ge m$」,對應的限制式是

$$x - m\delta \ge 0 \tag{9.7}$$

把 (9.1) 與 (9.7) 合起來,就同時保證了 $\delta=1 \leftrightarrow x>0$(在門檻 $m$ 的精度下)這個雙向的邏輯等價關係。

這一套「指示變數 + 大 $M$/小 $m$」的技巧,最經典的示範是 **Example 9.1:固定成本問題(fixed charge problem)**。設 $x$ 是某產品的產量,每單位邊際成本 $C_1$,但只要有生產(不論多少),就會額外產生一筆與產量無關的固定門檻成本 $C_2$。整個成本函數是

$$x=0: \text{總成本}=0, \qquad x>0: \text{總成本}=C_1 x + C_2$$

這既不是線性函數,甚至在原點還有一個不連續點,傳統 LP 完全無法表達。解法是引入指示變數 $\delta$,用限制式 (9.1) 保證只要有生產 $\delta$ 就必須是 1,再讓目標函數裡 $\delta$ 帶有係數 $C_2$,總成本就變成線性的 $C_1 x + C_2 \delta$。這裡有個值得玩味的地方:理論上 $x=0,\delta=1$ 這組解並不違反限制式(9.1)——它跟 $x=0,\delta=0$ 一樣可行,只是前者的目標值(成本)比較差。既然模型本身是在**極小化**成本,求解過程自然會避開這個劣解,不需要額外用限制式強制 $\delta=0$ 的一致性。

**Example 9.2:摻配問題** 則展示了另一種情境——反向保證確實必要的情況。設 $x_A, x_B$ 分別是原料 A、B 在配方裡的比例,想加入條件「如果 A 被使用,B 也必須被使用」。引入指示變數 $\delta$,用 $x_A - \delta \le 0$(這裡 $M$ 取 1,因為 $x_A$ 本身是比例)偵測 A 是否被使用,再用 $x_B - 0.01\delta \ge 0$ 強制「$\delta=1$ 時 $x_B$ 至少要達到門檻 0.01」。跟 Example 9.1 不同,這裡如果不加第二條限制式,模型完全沒有內在誘因去保證 B 真的被使用——這正是為什麼有時候只需要單向連結,有時候雙向都要,取決於目標函數會不會自動替我們排除掉「不一致」的解。

這一整套用 $M$、$m$、$\varepsilon$(容忍值,處理嚴格不等式)構造指示變數限制式的通用公式(對應 $\le$、$\ge$、$=$ 三種型態的限制式各有一套,見書中 (9.11)–(9.22)),與 [[logical-specifications-guide]] 裡介紹的 big-M 開關技巧,本質上是同一套思路的兩種獨立呈現——讀者可以互相對照,加深理解。

## 9.2 邏輯條件與 0-1 變數:借用命題邏輯的語言

9.1 節建立了指示變數的機制之後,自然的下一步,是系統性地探討:各種邏輯條件,能不能、又該怎麼轉換成這種指示變數之間的線性限制式?答案是可以,而且出乎意料地,幾乎所有常見的邏輯連接詞都有對應的轉換公式。

Williams 借用命題邏輯(propositional logic)的記號來組織這套技巧:用 $\vee$ 表示「或」(inclusive,即 A 或 B 或兩者皆是)、$\cdot$ 表示「且」、$\sim$ 表示「非」、$\rightarrow$ 表示「若...則」、$\leftrightarrow$ 表示「若且唯若」。這些連接詞之間有幾條重要的等價關係(De Morgan's laws 是其中最著名的一組):$\sim(P\vee Q)$ 等於 $\sim P\cdot\sim Q$;$\sim(P\cdot Q)$ 等於 $\sim P\vee\sim Q$。

設 $X_i$ 代表命題「$\delta_i=1$」,其中 $\delta_i$ 是 0-1 指示變數,則下列命題與限制式一一對應:

| 邏輯命題 | 對應限制式 |
| --- | --- |
| $X_1 \vee X_2$ | $\delta_1+\delta_2 \ge 1$ |
| $X_1 \cdot X_2$ | $\delta_1=1, \delta_2=1$ |
| $\sim X_1$ | $\delta_1=0$ |
| $X_1 \rightarrow X_2$ | $\delta_1-\delta_2 \le 0$ |
| $X_1 \leftrightarrow X_2$ | $\delta_1-\delta_2=0$ |

**Example 9.4:製造問題** 示範了如何把一句稍微複雜一點的邏輯陳述,轉成完整的限制式。條件是「如果產品 A 或 B(或兩者)被生產,則產品 C、D、E 裡至少要有一項也被生產」,寫成命題邏輯就是 $(X_A\vee X_B)\rightarrow(X_C\vee X_D\vee X_E)$。做法分三步:先用指示變數 $\delta_A,\delta_B$ 各自標示「A 是否被製造」「B 是否被製造」,用 $\delta_A+\delta_B\ge 1 \rightarrow \delta=1$(這裡 $\delta$ 標示「$X_A\vee X_B$」整體是否成立)套用 9.1 節的大 $M$ 公式得到 $\delta_A+\delta_B-2\delta\le 0$;再用同樣手法處理後件 $X_C\vee X_D\vee X_E \ge 1 \rightarrow \delta=1$ 這個反方向的蘊含,得到 $-\delta_C-\delta_D-\delta_E+\delta \le 0$。兩條限制式合起來,就完整表達了原本那句「如果...則...」的邏輯陳述。書中也指出,同一個條件其實有更精簡的寫法(利用等價關係 (9.32) 把它拆成兩個獨立的 $\rightarrow$),用 $\delta_A-\delta\le 0$ 與 $\delta_B-\delta\le 0$ 取代前面那條較鬆的限制式,雖然數學上等價,但在計算上通常更有效率——這提醒我們,同一個邏輯條件往往有不只一種正確的建模方式,選擇更「緊」的那一種對求解效率有實質幫助,詳見 [[integer-programming-refinement]]。

除了這些基本連接詞,0-1 變數之間的**乘積項**也是常見的非線性來源。如果模型中出現 $\delta_1\delta_2$(意即「$\delta_1$ 且 $\delta_2$ 同時為 1」的判斷),可以引入新的 0-1 變數 $\delta_3$ 取代這個乘積,再用三條限制式 $-\delta_1+\delta_3\le 0$、$-\delta_2+\delta_3\le 0$、$\delta_1+\delta_2-\delta_3\le 1$ 強制 $\delta_3=1 \leftrightarrow \delta_1=1\cdot\delta_2=1$。這種做法如果 $n$ 個原始 0-1 變數兩兩都有乘積關係,最多會需要 $n(n-1)$ 個新變數與 $3n(n-1)$ condition 條限制式,規模膨脹得很快;Glover(1975)提出了更精簡的替代公式,利用一個連續變數 $w$ 收集所有跟 $\delta_1$ 相關的乘積項,大幅減少新增變數的數量(前提是變數之間的「連結」不要太密集,否則精簡的效果有限)。就連 0-1 變數與連續變數的乘積 $x\delta$,也可以用類似的手法,引入新變數 $y$ 取代 $x\delta$,再用一組大 $M$ 限制式保證 $\delta=0\rightarrow y=0$、$\delta=1\rightarrow y=x$。DECENTRALISATION 案例(見 [[case-decentralisation]])正是需要線性化 0-1 乘積項的實例。

Williams 特別坦承一個觀察:很多人根本沒意識到邏輯條件可以用 0-1 變數建模;即使意識到了,也常常抓不準該怎麼精確捕捉想要的限制;而正確運用布林代數的概念,是避免「模型錯誤地放寬或收緊了條件」這種容易發生、卻難以察覺的錯誤的最佳方法。

## 9.3 Special ordered sets:當選項之間有順序關係

有兩種很常見的限制型態,傳統上要靠一整組 0-1 變數加限制式才能表達,但如果求解器能直接把它們當成一種「演算法層級」的概念來處理,計算效率會好上很多——這就是 **special ordered set(SOS)** 的由來(Beale and Tomlin, 1969)。

一個 **SOS1** 是一組變數(可以是連續或整數),當中**恰好一個**變數可以是非零。一個 **SOS2** 是一組變數,當中**最多兩個**可以非零,且這兩個非零變數在集合原本給定的排序中必須**相鄰**。這兩種限制型態理論上都可以用一般的 0-1 變數與限制式表達出來(本節稍後會示範怎麼做),但如果求解器有 SOS 專屬的演算法支援(修改過的 branch and bound,细節超出本書範圍),用起來會有相當可觀的計算優勢。

**Example 9.5:Depot 選址** 展示 SOS1 最直接的用途。假設一座 depot 只能蓋在 A、B、C、D、E 五個候選位置之一,只能蓋一座。用指示變數 $\delta_i$($i$ 為 A 到 E)表示是否在位置 $i$ 蓋 depot,則集合 $(\delta_1,\ldots,\delta_5)$ 是一個 SOS1;SOS1 的條件再加上限制式 $\delta_1+\delta_2+\delta_3+\delta_4+\delta_5=1$(9.56),就保證了整數性,甚至不需要額外聲明這些 $\delta_i$ 是整數變數。只有當候選位置之間本身帶有某種自然順序時,SOS 型態的建模才會帶來明顯的優勢——這也是為什麼書中緊接著用一個「有順序」的例子作對照。

**Example 9.6:產能擴充** 就是那個有順序的例子。一座工廠的產能 $C$ 可以透過不同的投資水準 $I$ 離散地擴充。若把集合 $(\delta_0,\delta_1,\ldots,\delta_5)$ 視為 SOS1,則可以寫出 $C=\sum_i C_i\delta_i$、$I=\sum_i I_i\delta_i$,再加上 $\sum_i \delta_i=1$。這裡最值得記住的概念性收穫是:**SOS 應該被當成一個「實體(entity)」來理解**——我們可以把 $C$ 看成 $I$ 的一個離散函數,這其實是把「0-1 變數表達二選一」這個概念,推廣成「一組有序的變數表達多選一」,比起用一大串普通整數變數硬湊,這種推廣往往更貼近問題的本質,也更好用。

**Example 9.7:單變數非線性函數** 把 SOS2 接回 [[nonlinear-and-separable-programming]] 已經介紹過的 $\lambda$-form。回顧一下,piecewise linear approximation 需要「凸性條件」$\sum\lambda_i=1$,再加上「最多兩個相鄰 $\lambda_i$ 非零」這條邏輯規定——這條規定在 non-convex 情況下無法只靠線性限制式保證,而 SOS2 恰好就是在講這件事:只要宣告 $(\lambda_1,\ldots,\lambda_n)$ 是一個 SOS2,這條邏輯規定就自動被(演算法層級地)強制執行,不需要額外的 0-1 變數與限制式,也不會被局限在 convex 才有效——這正是 SOS2 相對於一般 IP 建模的實務價值所在。

**Example 9.8:雙變數(以上)非線性函數** 進一步把這個想法推廣到 $z=g(x,y)$ 這種雙變數函數。做法是在 $(x,y)$ 平面上取一個網格,每個網格點 $(X_s,Y_k)$ 對應一個權重 $\lambda_{sk}$,用 $x=\sum\sum X_s\lambda_{sk}$、$y=\sum\sum Y_k\lambda_{sk}$、$z=\sum\sum g(X_s,Y_k)\lambda_{sk}$、$\sum\sum\lambda_{sk}=1$ 表達函數值。這裡的邏輯規定變成「最多四個相鄰的 $\lambda_{sk}$ 非零」,做法是把 $\lambda$ 依列、依欄各自加總成兩組新變數,分別宣告為 SOS2——這是 SOS2 概念的推廣。書中也指出一個微妙的非唯一性問題(同一組 $(\xi,\eta)$ 座標可能對應不只一種 $\lambda$ 組合),需要額外的限制式把非零的 $\lambda$ 限制在網格中每個小三角形的頂點上才能徹底排除。若不需要在網格點之間內插,則可以退而求其次,使用 Beale(1980)提出的 **chain of linked SOS sets**,用演算法直接處理,不必顯式引入額外變數。

如果求解套件沒有 SOS 專屬支援,仍然可以用普通 0-1 變數把 SOS 限制表達出來:對 SOS1,引入 0-1 指示變數 $\delta_i$,用 $x_i-M_i\delta_i\le 0$、$x_i-m_i\delta_i\le 0$ 連結,再加 $\sum\delta_i=1$;對 SOS2 則更複雜一些,需要 $n-1$ 個 0-1 變數搭配一組階梯狀的限制式(見書中 (9.71)–(9.72))才能保證「最多兩個相鄰非零」。

值得一提的是,Sherali(2001)後來提出了一種對 $\lambda$-formulation 的改良,能得到更緊的 LP relaxation,還能處理不連續的分段線性函數(用一對權重 $\lambda_L,\lambda_R$ 綁住每段線段的兩端,並確保每次恰好只有一對權重為正,把函數限定在某一段區間內)。

DECENTRALISATION 與 LOGICAL DESIGN 兩個案例都是能有效利用 SOS1 的實例(見 [[case-decentralisation]]、[[case-logical-design]])。

## 9.4 把額外條件加到既有的 LP 模型上

實務上絕大多數的 IP 應用,骨子裡其實是一個 LP 模型,只是被加上了某些額外條件。這一節整理出七種最常見的手法。

**Disjunctive constraints(9.4.1):不要求全部限制式同時成立。** 有時我們不希望模型的所有限制式**同時**成立,而只需要其中某個子集合成立,即 $R_1\vee R_2\vee\cdots\vee R_N$(其中 $R_i$ 是「第 $i$ 組限制式被滿足」這個命題)。做法是替每組限制式引入指示變數 $\delta_i$,用 9.1 節的大 $M$ 技巧建立「$\delta_i=1\rightarrow R_i$」,再加上 $\sum\delta_i\ge 1$。這個想法還能推廣成「$N$ 組裡至少要有 $k$ 組成立」($\sum\delta_i\ge k$)或「最多 $k$ 組成立」的變體。這裡有個值得記住的對比:邏輯連接詞「且」天生就對應 LP(把所有限制式都列出來,同時成立即可),而「或」則天生對應 IP——這也是為什麼 disjunctive constraints 必須靠額外的整數變數才能表達。

**Non-convex regions(9.4.2):用凸區域的聯集逼近非凸可行域。** 這是 disjunctive constraints 一個很有畫面感的應用。一個 non-convex 的可行域,往往可以被拆解成幾個 convex 子區域的**聯集**(這些子區域即使重疊也無妨),每個子區域各自用一組限制式描述,再用跟 9.4.1 節一樣的手法,要求「至少落在其中一個子區域裡」。另外,如果 non-convex 區域本身是連通的、且從原點到任何可行點的連線都完全落在可行域內,還有一種替代做法:把區域的每個頂點都賦予一個權重變數 $\lambda$,將這些 $\lambda$ 限制成一個 SOS2,用「$\le 1$」而非「$=1$」的方式加總——這其實是 Example 9.7 那套 SOS2 分段線性技巧的推廣。

**限制解中非零變數的個數(9.4.3)。** LP 有個性質:最適解裡非零變數的個數,最多不會超過限制式的個數。但有時需要把這個上限壓得更低(到某個 $k$)。做法是對每個連續變數 $x_i$ 引入指示變數 $\delta_i$(用 9.1 節的手法連結),再加上 $\sum\delta_i\le k$。FOOD MANUFACTURE 2 案例正是這種「限制配方裡原料種類數上限」的實例。

**循序相依的決策(9.4.4)。** 有時候某個時期做的決策,會限制之後時期能做的決策。例如一個多期模型裡,決策變數 $\gamma_t$ 代表「第 $t$ 期 depot 應該永久關閉($\gamma_t=0$)、暫時關閉($\gamma_t=1$)還是使用($\gamma_t=2$)」,若想強制「一旦永久關閉,之後每一期都必須維持關閉」,可以用一連串限制式 $-2\gamma_{t}+\gamma_{t+1}\le 0$ 串接起來。MINING 案例(見 [[case-mining]])正是這種循序相依決策的實例。

**規模經濟(9.4.5)。** [[nonlinear-and-separable-programming]] 已經指出,規模經濟(economies of scale,單位成本遞減)會讓成本函數呈現 non-convex 的形狀,單靠分段線性近似無法保證全域最佳解。這裡的做法,是把 $\lambda$-formulation 的權重集合 $(\lambda_0,\ldots,\lambda_n)$ 宣告為 SOS2,就能在 IP 的架構下取得真正的全域最佳解,而不只是局部最佳解——這正是 9.3 節 SOS2 概念在成本結構上的直接應用。

**離散的產能擴充(9.4.6)。** 有時 LP 的一條限制式(通常是產能限制)在現實中並非完全剛性,可以用某種成本代價違反或放寬它——但這個放寬往往不是連續可調的,而是只能一次跳一大階(例如整批添購新設備)。做法是為每個可能的右手邊值 $b_0,b_1,\ldots,b_n$ 引入 0-1 變數 $\delta_0,\ldots,\delta_n$,把它們視為 SOS1,用 $\sum a_jx_j-\sum b_i\delta_i\le 0$ 連結,並在目標函數中加上對應的擴充成本 $\sum c_i\delta_i$。

**Maximax objectives(9.4.7)。** 有一種目標函數形式是「極大化其中最大的那一項」($\max(\max_i(\sum_j a_{ij}x_j))$),這跟 minimax 目標(可以直接用 LP 表達)剛好相反,**無法**單純用 LP 處理。但可以把它當成 disjunctive constraint 的一個特例,用 IP 求解:引入一個自由變數 $z$ 作為要極大化的目標,對每個 $i$ 各自建立一組「$z$ 等於這一項」的限制式,再要求其中至少一組成立。

這七種手法,加上 9.1–9.3 節建立的指示變數、邏輯轉換、SOS 工具,構成了「怎麼把離散決策塞進一個 LP 模型」的完整工具箱。但 Williams 也在多處提醒:同一個邏輯條件,往往有不只一種正確的建模方式,選得好不好,對求解時間的影響可以是天壤之別——這正是 [[integer-programming-refinement]] 要處理的主題。9.4 節之後,書中(9.5、9.6 節)轉向另一個方向:一系列已經被研究得很透徹、擁有專屬名稱與理論結構的**特殊 IP 問題型態**——set covering、set packing、set partitioning、knapsack、travelling salesman、vehicle routing、quadratic assignment,以及用來對付「變數多到無法窮舉」的 column generation 技巧,詳見 [[special-integer-programming-structures]]。

## 連結

- [[nonlinear-and-separable-programming]] — 上一章:separable programming 在 non-convex 情況下需要靠 IP(尤其是 SOS2)才能保證全域最佳解,是銜接到本頁的直接動機
- [[special-integer-programming-structures]] — 下一節:9.5–9.6 節深入介紹的一系列特殊 IP 問題結構(set covering/packing/partitioning、knapsack、TSP、VRP、QAP)與 column generation
- [[logical-specifications-guide]] — 另一本書(García Sánchez)對「命題邏輯轉線性限制式」這套技巧的獨立系統化整理,兩相對照能加深對 big-M 開關邏輯的理解
- [[integer-programming-refinement]] — 下一章:好壞 formulation 的取捨、如何化簡模型、對稱性問題,直接呼應本頁多次提到「同一條件有不只一種寫法」的伏筆
- [[case-depot-location]]、[[case-decentralisation]]、[[case-logical-design]]、[[case-mining]] — 本頁各節提到的具體案例,示範這些建模手法在真實問題中的應用
