---
type: concept
domain: tech
tags: [optimization, mathematical-programming, linear-programming, network-flow, transportation-problem, input-output-model]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.5〈Applications and special types of mathematical programming model〉, pp.67–101

## 本章要回答的問題

前面幾章講的是「怎麼把一個情境正確地寫成 LP」的通用技巧；這一章換了個角度，先花一節的篇幅環顧一整圈，看看 LP 到底被實務界用在哪些產業、解決什麼問題（5.1 節），然後深入兩種特別重要、值得花時間學透的「特殊型態」模型：economic models（5.2 節，即 input–output / Leontief 模型）與 network models（5.3、5.4 節）。這兩種特殊型態之所以值得獨立成節，不是因為它們用了什麼 LP 以外的新數學，而是因為它們的係數矩陣天生帶有規律結構，一旦認出這個結構，就能用比通用 simplex 更有效率的專用演算法求解，還可能白白得到「整數解」這個意外的紅利。這件事對後面研讀 Part II 的經典案例極其重要——DISTRIBUTION、DEPOT LOCATION 這類案例，骨子裡就是本章講的 transportation / transhipment 問題外加一點額外限制。

## 5.1 LP 典型應用一覽

Williams 開宗明義說清楚：這一節的目的不是嚴謹地窮舉「LP 能用在哪裡、不能用在哪裡」——那件事本來就不可能做到——而是替讀者建立一種「感覺」（feel），知道當你遇到哪一類產業或哪一類問題時，值得考慮用 LP 試試看。也因此，各產業底下多半只給簡短說明加上幾篇參考文獻當作進一步閱讀的窗口，很多實務問題最終也不會停留在純 LP，而是自然地延伸成 integer programming 或 nonlinear programming（詳見 [[integer-programming-fundamentals]]、[[nonlinear-and-separable-programming]]）。

石油業是目前為止最大的 LP 使用者，模型動輒上千甚至上萬條限制式，同時涵蓋原油怎麼買、怎麼運、煉成什麼產品的整條供應鏈，這種橫跨 distribution、resource allocation、blending、甚至 marketing 的模型稱為「corporate model」；Part II 的 REFINERY OPTIMISATION 案例就是這類模型的縮影。化學業的應用型態與石油業相近（同樣重視 blending 與 resource allocation），只是規模通常小得多。製造業則最常見的是「product mix」問題（決定要生產多少各種產品以善用有限的產能、原料、人力），FACTORY PLANNING 案例正是一個橫跨多期的製造業資源分配問題。

運輸與配送領域,最經典的兩類問題——transportation problem 與 transhipment problem——本身就是網路模型，會在 5.3 節深入展開；DISTRIBUTION 案例是最單純的版本，DISTRIBUTION 2 進一步加入 depot location（要不要在某處設立轉運站）而需要 integer programming；MILK COLLECTION 這類排程問題（安排運奶車、飛機、船班的路線）通常也得靠 integer programming 處理。金融業最早的一個 mathematical programming 應用是 Markowitz 的投資組合選擇問題（給定期望報酬率的目標，最小化報酬的變異數——這其實是一個 quadratic programming 模型）；LP 也被用來設計政府稅制、支援會計上的成本歸屬分析，以及訂定機票、飯店房價這類會隨時間變動的動態定價（yield / revenue management，對應 Part II 的 YIELD MANAGEMENT 案例）。

農業方面，LP 常用來規劃該種什麼作物、怎麼輪作、要不要擴大生產（FARM PLANNING 案例即為代表），也常用來做飼料或肥料的 blending，牛奶等農產品的配送問題則同樣落回 5.3 節的網路模型；至於農產品的最適定價（例如政府對牛奶的補貼定價），因為牽涉到需求曲線的非線性關係，往往要用到 quadratic programming，AGRICULTURAL PRICING 案例即是一例。健康照護領域的應用常是資源分配的變形——醫生、護士、病床這些稀缺資源該怎麼配置，資料的準確度本身常有疑慮，但即使如此模型仍能提出有參考價值的政策選項；具體例子包括排護士班表、決定放射治療的射束強度與方向。礦業的應用主要也是資源分配（人力、機具怎麼調度），MINING 案例是連續多年該開採哪幾座礦場的決策，OPENCAST MINING 案例則是決定露天礦場邊界該畫在哪裡；MANPOWER PLANNING 案例則專門處理人員在不同職務間流動（招募、升遷、再訓練）的規劃問題。

食品業大量使用 blending（香腸、派、人造奶油、冰淇淋的配方最適化，模型通常不大且容易求解），FOOD MANUFACTURE 案例正是食品業多期 blending 問題的代表；食品業的配送問題一樣屬於 5.3 節的網路模型。能源產業方面，電力與瓦斯公司都用 mathematical programming 處理資源分配問題，TARIFF RATES（POWER GENERATION）案例是在一天不同時段的用電負載下如何調度發電機組，HYDRO POWER 案例則進一步把水力發電這種蓄能特性納入考量。造紙與紙漿業同樣有資源分配與 blending 的問題（例如考慮回收廢紙），但這個產業還有一個很特別的問題：**trim loss（裁切損耗）問題**——如何裁切不同寬度的紙捲訂單以最小化浪費，這個問題用 LP（有時要用 integer programming）處理，後面 [[special-integer-programming-structures]] 會用它來示範 column generation 技巧。廣告業有所謂的 media scheduling 問題（如何在電視、報紙等各種媒體管道間分配廣告預算），但學界對 mathematical programming 在這個領域是否真的實用意見不一。國防領域的應用同樣多屬資源分配，也包括飛彈基地選址這類問題。

**供應鏈（supply chain）** 是個值得特別點名的整合型應用：一個組織的採購（買什麼原料、跟誰買、何時買）、進貨配送（用什麼運具、路線怎麼排）、庫存規劃（存多少原料與成品）、財務規劃（要不要借款、借多少）、生產（用哪些產能生產多少）、行銷（用哪些通路、投入多少行銷資源）這些功能理論上都能各自用 mathematical programming 最適化，但如果只個別最適化其中一項而忽略了「大局」，反而可能造成整體受害（例如只顧著最大化生產量，卻做出配送或行銷上不可行的方案）。真正有價值的是把這些功能串成一個 **integrated model**，讓輸出彼此餵養、進行全域最適化（例如以最大化總利潤為目標）。但書中也提醒一個現實的風險：這種整合模型如果貪多、一次做太大，很容易變得笨重難用（書中舉英國國民保健署 NHS 那個著名失敗的大型 IT 系統為例）；務實的做法通常是讓整合模型從既有的、規模較小的專門模型逐步演化長成，而不是一步到位重建一切。

除了以上這些主要領域，書中也列出一系列容易被忽略、卻同樣值得留意的應用：土地開發的多期規劃、研發資源分配的效益評估、用 knapsack 型 integer programming 設計選擇題考卷、用 integer programming 挑選最有價值的郵寄名單、用 LP 做林業經營規劃、用 integer programming 處理污染防制、用 0-1 integer programming 幫圖書館挑選該訂閱哪些期刊、電腦設計中的 integer programming 模型、用 integer programming 建構滿足給定重量的最適桁架結構、運動賽程編排、把 DNA 定序問題類比成（較容易的）考古地層排序問題（本質上是 Travelling Salesman Problem 的變形，詳見 [[special-integer-programming-structures]] 的 Ch.9）。最後，公部門績效評估常用一種特別的模型——**Data Envelopment Analysis (DEA)**，用來比較多個決策單位（例如多家分店、多家醫院）的相對效率，對應 Part II 的 EFFICIENCY ANALYSIS 案例。

讀完這一整節，真正該帶走的不是「LP 可以用在 47 個產業」這種清單式印象，而是一種辨識能力：resource allocation、blending、distribution、scheduling、pricing 這幾種基本問題形態會反覆出現在完全不同的產業外衣底下，學會看穿外衣、認出底層的問題形態，才是這一節真正的價值所在。

## 5.2 經濟模型（input–output / Leontief models）

### 5.2.1 靜態模型：一個三產業的小型經濟

國家經濟層級最常見的 mathematical programming 模型是 **input–output model**（又稱 **Leontief model**，因其發明人 Leontief 而得名），描述一個經濟體中各產業之間「你的產出是我的投入」的相互依存關係。這類模型背後藏著兩個相當強烈（也因此常被質疑過度簡化）的假設：第一，每個產業的產出與其投入成正比（把所有投入加倍，產出也剛好加倍）；第二，每個產業所需的各種投入之間的比例是固定的，無法用增加某種投入來抵換減少另一種投入——用書中的話說，就是 **non-substitutability of inputs**，這個投入比例完全由生產技術決定。

書中用一個三產業（煤、鋼鐵、運輸）的小經濟體示範。要生產 £1 的煤，需要投入 £0.1 的煤（自用電力）、£0.1 的鋼鐵（機具耗損）、£0.2 的運輸（把煤從礦坑運出來），外加 £0.6 的勞力；鋼鐵、運輸兩欄的係數同理列在一張 input–output matrix 裡。設 $x_c, x_s, x_t$ 分別為煤、鋼鐵、運輸的總產出，模型的核心是三條「產出必須等於各項投入需求加總」的等式：

$$x_c = 20 + 0.1x_c + 0.5x_s + 0.4x_t,\qquad x_s = 5+0.1x_c+0.1x_s+0.2x_t,\qquad x_t=25+0.2x_c+0.1x_s+0.2x_t$$

其中 20、5、25 是三個產業各自要滿足的外部（exogenous）需求，稱為 **bill of goods**。這是一個「未知數個數 = 方程式個數」的線性方程組，可以唯一求解（本例解出 $x_c=56.1,\ x_s=22.4,\ x_t=48.1$，勞力需求則可由此反推得到 50）。這個階段其實還稱不上真正的 LP——因為解是唯一的，加不加目標函數、要最大化還是最小化，都不影響答案，目標函數在這裡毫無用武之地。

真正讓它變成一個「有意義的」LP 模型的關鍵，是加入**產能限制**。如果勞力供給本身有上限（例如限制在 40），我們就不能再假設每個產業「想生產多少就生產多少」，而要反過來問：在勞力供給有限的情況下，這個經濟體到底能不能生產出某個 bill of goods？這時候原本的等式關係改成描述「產出 $x$ 與 bill of goods $y$」之間的關係（$0.9x_c-0.5x_s-0.4x_t-y_c=0$ 等），再加上一條勞力限制式 $0.6x_c+0.3x_s+0.2x_t\le40$，就得到一個貨真價實的 LP：有無限多組可行的 bill of goods，需要一個目標函數（例如最大化總產出 $x_c+x_s+x_t$，或只想著重某個產業而單獨最大化 $x_s$）才能選出其中一個「最好」的。這種在多個目標之間權衡取捨的處理方式，呼應了 [[building-lp-models]] 3.2 節提到的多目標問題。像勞力這種只提供投入、本身不作為任何產業產出的資源，稱為 **primary goods**；一旦把 input–output 模型當 LP 求解，還可以順便得到這些 primary goods 的 **shadow price**（詳見 [[interpreting-lp-solutions]] 6.2 節），等於免費附贈一套定價系統。ECONOMIC PLANNING 案例即建立在這類模型之上。

### Samuelson substitution theorem：為什麼「混合製程」通常是白費力氣

Non-substitutability 假設聽起來很不真實——難道真的沒有辦法多用點電力、少用點機具來煉鋼嗎？書中用一個延伸例子回答這個疑惑：假設每個產業其實有兩種可能的生產製程可選（例如煉煤有製程 1、製程 2，各自的投入比例不同），直覺上似乎應該按照 bill of goods 混合使用兩種製程才划算。但**只要整個模型只有一種 primary good（本例中只有勞力）**，Samuelson substitution theorem 告訴我們這個直覺是錯的：無論 bill of goods 怎麼變動，每個產業永遠只會選定同一種製程、完全不使用另一種，而且這個「最佳製程」的選擇跟 bill of goods 本身無關,只跟目標函數有關。書中的數值例子驗證了這一點——延伸後的模型加入六個製程變數，最適解只用到其中三個（$x_{c1}, x_{s1}, x_{t2}$），另外三個恰好都是零。

這個定理的實務意義很大：一旦只有單一種 primary good，就不必煩惱這 non-substitutability 假設的限制，因為每個產業本來就只會用一種、且是「最好的」那種生產方式；只要找出這個最佳製程一次，之後不管面對什麼樣的 bill of goods，都可以直接把 input–output matrix 精簡成只保留這些最佳製程的欄位。但這個結論一旦超過一種 primary good，就不再成立——多種資源同時稀缺時，混合使用不同製程反而可能變得有利。

### 5.2.2 動態模型與 5.2.3 聚合

靜態模型假設「產出馬上就能被拿去當投入」，忽略了現實中投入與產出之間必然存在的時間落差（例如今年蓋的工廠明年才能開始生產）。**Dynamic input–output model** 就是為了修正這一點而生：一部分的產出即時被消費掉，另一部分則被投資回去，用來擴大未來的生產能力，這正呼應了 [[structured-lp-models]] 4.1 節提到的多期模型精神——事實上，把 input–output 模型延伸成多期版本，跟把一般 LP 模型延伸成多期模型，用的是完全一樣的手法。ECONOMIC PLANNING 案例正式在 Part III 處理了這種 dynamic input–output 模型的建模細節。

另一個實務問題是 **aggregation（聚合）**：真實經濟體有成千上萬種商品與服務，硬要把它們濃縮進一張 input–output matrix 的每一欄，勢必要把許多性質不盡相同的產業合併看待。到底該怎麼分類合併，理論上並沒有一套嚴謹的數學判準,書中提出三個常識性的判斷依據：substitutability（彼此可替代的產業適合合併）、complementarity（互補使用的產業適合合併）以及生產製程的相似性。實務上多數 input–output 模型會把整個經濟體聚合成不到 1000 個產業。值得留意的是一個計算上的反直覺現象：一般 LP 模型的係數矩陣通常非常稀疏（1000 條限制式的模型裡，非零係數可能只占 1%），但 input–output 模型聚合之後往往非常「密」（非零係數比例可能高達 50%），這使得它們求解起來可能特別耗時、甚至遇到數值上的困難，因此常需要利用其特殊結構設計的專用演算法（如 Dantzig 1955 針對 input–output 結構調整過的 simplex 演算法）。

## 5.3 網路模型（network models）

Distribution、assignment、路徑規劃這幾類問題在 operational research 裡出現的頻率極高，而它們有一個共同的性質：都可以被畫成一張「節點（node）+ 有向弧（arc）」的圖，也都可以被規約成 LP 模型的特例——但用專為網路設計的演算法求解，通常會比把它們丟進通用的 revised simplex 演算法快得多。這一節依序介紹七種經典網路模型：transportation、assignment、transhipment、minimum cost flow、shortest path、maximum flow、critical path analysis，每一種都附一個具體情境幫助建立直覺。理解這七種模型，是讀懂後面 [[case-distribution-1]]、[[case-depot-location]] 這類案例的必要地基。

### 5.3.1 Transportation problem——最基本的配送問題

**情境直覺**：想像三座工廠（供應商 $S_1, S_2, S_3$，年產能分別是 135、56、93 個單位）要把某種商品送到四個客戶（$T_1,\ldots,T_4$，年需求分別是 62、83、39、91），每一對「工廠到客戶」的單位運費不同，某些工廠甚至不能供應某些客戶（用一個非常大的數字 $M$ 當作那條路線的運費，等於變相禁止使用它）。問題是：在不超過各工廠產能、滿足各客戶需求的前提下，怎麼分配運送量才能讓總運費最小？

這正是 **transportation problem** 的標準形式（首見於 Hitchcock 1941）。設 $x_{ij}$ 為由供應商 $i$ 送到客戶 $j$ 的數量，模型是

$$\text{Minimize} \sum_{i,j} c_{ij}x_{ij} \quad \text{s.t.} \sum_j x_{ij}\le(\text{供應商 } i \text{ 產能})\ \forall i,\qquad \sum_i x_{ij}=(\text{客戶 } j \text{ 需求})\ \forall j,\qquad x_{ij}\ge0$$

前面 $m$ 條稱為 **availability constraints**，後面 $n$ 條稱為 **requirement constraints**。如果總產能與總需求剛好相等，前面的 availability constraints 也可以一律改寫成等式；如果（像本例）總產能 284 大於總需求 275，可以引入一個**虛擬客戶**（dummy customer，本例需求設為 9、運費全設為 0）把兩邊補平，這樣一來所有限制式都能整齊地寫成等式。把這個問題畫成圖，會得到一個左邊是供應商節點、右邊是客戶節點、中間用弧線連接可行運送路線的二部圖（bipartite graph）：節點上標示的正負數字就是該節點的供給量或需求量，弧線上的數字就是單位運費。

Transportation problem 有兩個非常重要的性質。第一，只要所有供應量、需求量都是整數，最適解中每一條弧上的運送量也保證會是整數——這個 **integrality property** 意味著我們完全不需要動用 integer programming，用普通 LP 求解就能自動得到整數答案。第二，因為矩陣結構特別規律，可以用比通用 simplex 更精簡的專用演算法求解（例如 Dantzig 1951 的簡化 simplex 版本，或 Ford–Fulkerson 1956 的演算法），對於供應商、客戶數目龐大的實際問題（$m$ 個供應商、$n$ 個客戶會產生 $mn$ 個變數）尤其重要。此外，如果每條路線的運量還有上下限（**capacitated transportation problem**），只需要在變數上加簡單的上下界 $0\le l_{ij}\le x_{ij}\le u_{ij}$ 即可，不影響前述兩個性質。

有趣的是，transportation problem 的應用範圍遠遠超出字面上的「運送貨物」。書中舉了一個生產排程的例子：一家公司要在連續四個月裡，用「正常班」與「加班」兩種產能生產某項商品滿足逐月需求，也可以提前生產、用儲存成本存到未來月份出貨。如果把「某月的某種產能」看成一個供應商、把「某月的需求」看成一個客戶、把「生產成本 + 儲存成本」當作運費（不能為過去的需求生產，用 $M$ 或「-」擋掉），整個問題的數學結構跟前面的配送問題一模一樣——這正是本章反覆強調的重點：辨認出問題背後的網路結構，比問題表面看起來是不是在講「運輸」更重要。

### 5.3.2 Assignment problem——當每個節點只能配對一次

**情境直覺**：想像要把 $n$ 個人分配到 $n$ 個工作上，每個人做每項工作各有不同的預估耗時 $t_{ij}$，希望所有工作都有人做、每個人都恰好指派到一項工作，且總耗時最小。

這正是 transportation problem 的一個特例——把每個人看成供應量恰好是 1 的供應商、每項工作看成需求恰好是 1 的客戶：

$$\text{Minimize}\sum_{i,j}t_{ij}x_{ij}\quad\text{s.t.}\sum_i x_{ij}=1\ \forall j,\quad\sum_j x_{ij}=1\ \forall i$$

其中 $x_{ij}$ 理論上該是 0/1 變數（第 $i$ 人是否指派給第 $j$ 項工作），乍看之下需要 integer programming 才能保證整數解。但因為 assignment problem 是 transportation problem 的特例，前述的 integrality property 同樣適用：只要把它當一般 LP 求解，最適解會自動落在 0 或 1 上,完全不需要額外用 integer programming 強制。書中甚至引用 Dantzig 的一句玩笑話：如果把婚姻看成一種 assignment problem，這個 integrality property 恰好說明「一夫一妻制帶來最大的整體幸福」。

雖然理論上可以把 assignment problem 當普通 LP 求解，但當 $n$ 一大（例如 100 人配 100 項工作，就會產生一萬個變數），用專門為它設計的 **Hungarian method**（Kuhn 1955，衍生自更一般的 Ford–Fulkerson 方法）會遠比通用 LP 求解有效率得多。

### 5.3.3 Transhipment problem——貨物可以繞道

**情境直覺**：如果延伸前面配送問題的情境，允許貨物先從一個供應商送到另一個供應商、或先送到某個客戶手上再轉送給別的客戶（例如某些商品在到達最終客戶前，先經過某個中繼點比較划算），問題就不再是單純的「供應商直送客戶」，而變成 **transhipment problem**（Orden 1956）——供應商與客戶之間、供應商彼此之間、客戶彼此之間都可能有帶成本的弧線相連。

Transhipment problem 有一個很優雅的處理技巧：把每一個節點同時當作「供應商」與「客戶」來看待——原本的供應商，作為「客戶」時需求設為 0；原本的客戶，作為「供應商」時可用量設為 0；不允許逆向流動的路線就把對應可用量或需求設為 0 排除。這樣一來，transhipment problem 就能被直接**轉換成一個（節點數更多的）transportation problem** 來求解，前面兩個重要性質（整數解保證、專用演算法可用）自然一併繼承下來。

### 5.3.4 Minimum cost flow problem——統一的一般形式

Transportation、transhipment、assignment 這三種問題,其實都是 **minimum cost flow problem**（一般化的最小成本網路流問題）的特例。一般形式允許任意數目的來源節點（sources，有正的可用量）、去向節點（sinks，有正的需求量）、以及純粹轉運用的中繼節點,弧線上附有單位成本（也可能附有流量上下限）。

**情境直覺**：兩個貨源節點（可用量 10、15）要透過一個中繼網路,把貨物送到三個目的地節點（需求 9、10、6），部分弧線是雙向的（用兩條方向相反的弧表示），每條弧線都有各自的單位運送成本。

寫成 LP 時,最自然的方式是在每一個節點都寫一條「流量平衡」（material balance）限制式：流入該節點的總流量，減去流出該節點的總流量，要等於該節點的外部淨需求（依慣例，流出節點的弧給負係數、流入節點的弧給正係數）。例如某個純轉運節點的平衡限制式就是「流入的兩條弧之和 = 流出的三條弧之和」，寫成等式後右手邊是 0；一個 sink 節點的平衡限制式則是「流入的弧 = 流出的弧 + 該節點的需求量」。這些限制式的係數矩陣稱為該網路的 **incidence matrix**,同樣具備前面反覆提到的 integrality property——只要各節點的可用量、需求量、以及各弧的容量上下限都是整數,最適解中每條弧上的流量必然也是整數。書中也提示一個容易忽略的建模陷阱:如果某條弧允許負的單位成本,而這條弧又落在一個「迴圈」上，理論上可以無限次繞這個迴圈壓低總成本,導致問題無界(unbounded)——因此一般要求弧的單位成本非負。

如果某條弧的流量有上限 $u$（或下限 $l$）,有一個很巧妙的通用手法可以把「有界弧」轉換回「無界弧」的標準形式:新增一個節點 $i'$,把原本 $i$ 到 $j$ 的弧改成先連到 $i'$、再由 $i'$ 接到 $j$,並且在 $i'$ 上額外附加一筆等於該上（下）限的外部流量。這個技巧的價值在於,如果手上的求解程式只支援無界弧網路,仍然可以透過加點技巧間接處理有界弧問題。

Minimum cost flow problem 有兩個重要的延伸,分別會讓前述的美好性質打折扣。第一個是 **minimum cost multi-commodity network flow problem**——如果同一個網路裡同時流動好幾種不同的商品(各自有各自的來源與去向,也可能共用某些弧的總容量上限),仍然可以寫成 LP(其矩陣結構正好是 [[structured-lp-models]] 4.1 節談到的 block angular 結構,因此 Dantzig–Wolfe decomposition 天生適用),但**這個延伸會破壞 integrality property**——即使所有可用量、需求量、容量都是整數,多商品流動問題的 LP 最適解仍然可能出現非整數的流量,如果現實中一定要整數解,就必須訴諸 integer programming。第二個延伸是 **generalized network flow model**(又稱 network with gains):弧上除了單位成本,還多了一個「增益係數」,流量經過這條弧之後會依這個係數放大或縮小(例如因蒸發、耗損,或利率隨時間增值),這個延伸同樣可能需要用 integer programming 才能保證整數流量,但仍可以利用其特殊結構設計高效演算法。

### 5.3.5 Shortest path problem——最小成本流的特例

**情境直覺**：給定一張標示了每段道路距離的地圖,想找出從節點 0 到節點 8 的最短路徑。

乍看之下這是完全不同的問題,但書中指出一個相當漂亮的洞見:shortest path problem 可以被規約成 minimum cost flow problem 的特例——只要把起點節點給予「可用量為 1」的來源身分、終點節點給予「需求為 1」的去向身分,其餘節點都是純轉運節點,再求解這個網路的最小成本流。因為 minimum cost flow 保證整數最適解,起點流出的弧當中必然恰有一條流量為 1(其餘為 0),沿途每個中繼節點也恰好一進一出流量為 1 的弧——這一條「流量為 1」的路徑,正好就是成本最小的那條路徑,也就是最短路徑。雖然理論上可以這樣用 LP 求解,實務上用專為此設計的 **Dijkstra (1959) 演算法** 效率高得多。

### 5.3.6 Maximum flow problem——目標不再是成本,而是流量本身

**情境直覺**：一個網路的每條弧線都有流量上限(容量),但這次沒有單位成本的概念,單純想知道:從所有來源節點總共最多能把多少流量送到所有去向節點?

這類問題的建模手法跟 minimum cost flow 幾乎一樣(節點平衡限制式、弧的容量上限),差別在於目標函數換成了「最大化流入來源節點與流出去向節點的總流量」,因此需要為每個來源、去向節點各自新增一個代表「額外流入/流出量」的變數,目標函數就是這些新變數的加總最大化。同樣地,只要所有弧容量是整數,最適解保證整數;實務上通常用專門設計的 **Ford–Fulkerson (1962) 演算法** 求解,而不是通用 LP。

### 5.3.7 Critical path analysis（CPM）——網路也可以拿來排工期

**情境直覺**：蓋一棟房子牽涉一連串前後有相依關係的工作(挖地基、砌牆、配線、油漆……),某些工作必須等其他工作完成才能開始。想知道整個專案最快幾天能完工?哪些工作稍微delay也不會拖累整體工期,哪些工作一旦delay就會拖累整個專案?

Critical path analysis(又稱 PERT)把整個專案畫成一張網路:弧代表各項有工期長度的活動(activity),節點代表活動的起訖時間點。有些依存關係本身沒有實際的工作內容,只是純粹表達「某活動必須等某活動完成才能開始」的先後順序,這種弧稱為 **dummy activity**(工期為 0)。

建模時,為每個活動的起始時間設一個變數 $t_i$,外加一個代表整個專案完工時間的變數 $z$,每一條「先後relation」的弧就對應一條限制式,形如「後續活動的起始時間 $\ge$ 前置活動的起始時間 + 前置活動工期」。整個模型的目標是**最小化** $z$。書中的範例(蓋房子,七項活動加一個 dummy activity)求解後得到完工時間 26 天,而 **critical path**——那些一旦delay就會拖累整體工期的活動所連成的路徑——在網路裡其實就是**從起點到終點的最長路徑**(這點恰好與前面 shortest path 的「最短」相反,值得對照記憶)。

雖然 critical path analysis 形式上也是一個 LP 問題,但跟前面幾種網路模型一樣,它的特殊結構讓專用演算法遠比通用 LP 求解划算,市面上也有大量現成的專案排程軟體針對這個結構設計。這個模型還有幾個常見的延伸:如果多項活動要競爭同一批有限的人力或設備資源(**resource allocation to activities**),問題就會變成 integer programming(在 [[special-integer-programming-structures]] 9.5 節進一步討論);另外也可能想「平滑」資源在時間軸上的使用量,避免忽多忽少。與 CPM 精神相近、但結構更簡單的還有 **job-shop scheduling** 問題——把機台加工的先後順序看成網路裡的先後relation,機台本身就是要被爭奪的有限資源。

### 小結:辨認網路結構為什麼值得

回顧這七種模型,一個共通的主題貫穿全場:每一種都保留了「只要輸入資料是整數,最適解自動是整數」這個 integrality property,讓我們完全避開昂貴得多的 integer programming;也都存在遠比通用 revised simplex 更有效率的專用演算法。即使一個實際的 LP 模型本身不是純粹的網路模型,只要它內含一個夠大的網路子結構,也值得利用(例如透過 **generalized upper bound, GUB** 這種限制式類型,詳見 [[building-lp-models]] 3.3 節提到的 SOS/GUB 概念),讓大部分變數仍能在最適解中自動落在整數值上,大幅減輕之後 integer programming 的計算負擔。書中也提醒,一個 LP 模型的**對偶**(dual,見 [[interpreting-lp-solutions]] 6.2 節)有時恰好就是某個網路流模型——[[special-integer-programming-structures]] 提到的 OPENCAST MINING 案例就是網路流模型的對偶,MINING 案例則主要是網路流模型的對偶再加上 integer programming。唯一一個「看起來很像卻怎麼也套不進網路框架」的經典問題是 **travelling salesman problem**——儘管表面上跟 assignment problem 神似,它終究不能用純 LP 求解,必須透過 integer programming 延伸來處理(詳見 [[special-integer-programming-structures]] 9.5 節)。

## 5.4 把 LP 轉換成網路形式

前面幾節示範的都是「問題本身天生就是網路」的情況,但如果一個 LP 模型不是一眼看出是網路,有沒有辦法系統性地檢驗、甚至自動把它轉換成網路流模型?書中概述了 Baston et al. (1991) 提出的一套程序(另有 Bixby and Cunningham 1980 用 matroid theory 語言表達的等價方法),大致步驟是:先透過縮放(scaling)行列,設法讓所有係數變成 0 或 $\pm1$(如果做不到,代表這個模型無法轉換成網路);把代表 slack / surplus / artificial 變數的「邏輯變數」安排成一棵**生成樹(spanning tree)**;每個原始變數則依它在矩陣裡出現的列,對應生成樹上的一個「多邊形」(polygon);再依循一套方向規則替生成樹以外的弧定向;最後把原始變數的目標函數係數當作對應弧的單位成本,把每個節點的淨右手邊係數當作該節點的外部流量。書中用一個五條限制式、九個變數的數值例子完整示範了這套轉換程序,最終得到一個等價的 minimum cost network flow 模型。這套程序不保證每個 LP 都能被轉換成網路——但一旦成功轉換,就能直接套用本節前面介紹的高效專用演算法,並免費獲得整數解的保證,對於原本必須動用 integer programming 才能求整數解的場合,是非常划算的一步。

## 連結

- [[building-lp-models]] — LP 建模的基礎技巧(目標函數類型、限制式類型、SOS/GUB),是理解本章網路模型與經濟模型的前置知識
- [[structured-lp-models]] — 多商品網路流問題的 block angular 結構與 Dantzig–Wolfe decomposition 直接呼應本章 4.1、4.3 節
- [[interpreting-lp-solutions]] — shadow price 與對偶的正式定義,用於理解 input–output 模型的定價系統,以及網路流模型與其對偶的關係
- [[case-distribution-1]] — transportation problem 的直接應用案例,骨架就是本章 5.3.1 節
- [[case-depot-location]] — 在 transportation/transhipment 結構之上加入設站與否的 0-1 決策,是網路模型與 integer programming 結合的代表案例
