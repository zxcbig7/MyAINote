---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, vehicle-routing, travelling-salesman-problem, network-flow, case-study, williams]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.12〈The Problems〉§12.27, pp.287–289；Ch.13〈Formulation and Discussion of Problems〉§13.27, pp.343–344；Ch.14〈Solutions to Problems〉§14.27, pp.380–381

## 情境：兩小時內把行李送到,還要決定派幾輛車

一家只有六輛廂型車的小公司,和多家航空公司簽了合約,負責在每天晚上六點,從 Heathrow 機場取走倫敦地區旅客的遺失或延誤行李,合約規定每位客戶必須在晚上八點前收到行李——也就是留給公司的時間只有兩小時。公司需要一個模型,能夠在每天傍晚快速求解,告訴他們最少需要派出幾輛車、每輛車該按什麼順序送到哪些客戶。每輛車的容量沒有實際限制(兩小時內能收到的行李量,一輛車都裝得下),某一晚需要送達的地點與地點之間的行車時間(以分鐘計)由一張表給出——這張表(Table 12.24)列出了 Heathrow 加上 Harrow、Ealing、Holborn、Sutton、Dartford、Bromley、Greenwich、Barking、Hammersmith、Kingston、Richmond、Battersea、Islington、Woolwich 共十五個地點兩兩之間的時間,且假設沒有為「卸貨」預留額外時間。為了方便起見,Heathrow 被視為第一個地點。題目要求先求出最少需要幾輛車,再在這個最小車輛數之下,求出讓「跑最久的那輛車」時間最短的一組路線。

這個題目讀起來像個小題目,卻是全書網路模型與組合最佳化技巧的一次交叉考驗:它一方面是不折不扣的「多輛車巡迴」問題,一方面骨子裡的資料結構——一組地點加上兩兩之間的旅行時間——正是 [[lp-applications-and-networks]] 談的網路模型;而「怎麼把巡迴路線問題轉成 0-1 變數限制式」,則要借用 [[special-integer-programming-structures]] 介紹的 travelling salesman problem(TSP)與 vehicle routing problem(VRP)工具。

## 這題示範的建模技巧：把 TSP 改造成「不用繞回原點」的 Hamiltonian path

標準 TSP 求的是一條經過所有城市、最後繞回起點的最短「巡迴」(circuit)。但這裡的情境不太一樣:公司真正在乎的,是車子送完最後一件行李的時間,至於送完貨之後車子要不要開回 Heathrow、開多久,合約完全不關心。Williams 的處理方式很巧妙——他借用 [[special-integer-programming-structures]] 中介紹的「asymmetric」TSP formulation,把「送完最後一站之後回到 Heathrow」這一段路徑的成本,人為地設成 0。這樣一來,雖然形式上每輛車走的仍然是一個「迴路」,但由於回程不計時間,兩小時的限制實際上只約束了「從 Heathrow 出發到抵達最後一個客戶」這一段,等於是在 TSP 的骨架裡,悄悄换成了一條不必繞回起點的 Hamiltonian path。

這是一個很值得記住的建模技巧:當現實問題的「形狀」跟教科書上的標準問題有一點點不對稱的差異時,不必發明一個全新的 formulation,往往只需要調整某幾條邊的成本(這裡是把回程成本設成 0),就能讓標準模型服貼地套用到新情境上。這題也同時是一個多輛車(而非單一業務員)的 VRP 變形——沒有容量限制、沒有明確的時間窗,但多了一個「先決定車輛數,再最小化最大完成時間」的兩階段目標,這種「先求可行性、再在可行的範圍內求品質」的兩段式思路,在排程與路線規劃問題裡非常常見。

## 建模過程：三組 0-1 變數,加上事後才補上的子迴路消去限制式

Williams 定義三組變數,全部是 0-1 整數:$x_{ijk}=1$ 表示第 $k$ 輛車直接從地點 $i$ 走到地點 $j$;$y_{ik}=1$ 表示地點 $i$ 由第 $k$ 輛車造訪;$\delta_k=1$ 表示第 $k$ 輛車被使用。目標函數非常單純——先求最少車輛數:

$$\text{Minimize} \sum_k \delta_k$$

限制式的第一部份確保變數之間彼此一致:如果地點 $i$($i>1$,即除了 Heathrow 之外的任何地點)被第 $k$ 輛車造訪,那麼第 $k$ 輛車顯然是被使用的,即 $y_{ik} \le \delta_k$;每個地點(除了 Heathrow)恰好被一輛車造訪一次,即 $\sum_k y_{ik}=1$;而每一輛被使用的車,都必須造訪 Heathrow,即 $\sum_k y_{1k} \ge \sum_k \delta_k$。流量守恆的部分沿用網路模型的標準寫法:如果地點 $j$ 由第 $k$ 輛車造訪,那麼恰好有一條邊「進入」$j$($\sum_i x_{ijk}=y_{jk}$),也恰好有一條邊「離開」$j$($\sum_i x_{jik}=y_{jk}$)。時間限制式則是這題的核心:對每輛車 $k$,把它「送貨方向」的行車時間(即 $i<j$ 的路段)與「回程方向但尚未回到 Heathrow」的行車時間加總,必須不超過 120 分鐘——回到 Heathrow 的最後一段路,依照前一節提到的技巧,成本設為 0,不計入這個限制式。此外,為了避免車輛之間互相對調造成大量對稱解,還加了一條排序限制式,要求車輛依造訪站點數由多到少排列:$\sum_i y_{i1} \ge \sum_i y_{i2} \ge \cdots \ge \sum_i y_{i6}$。

這個模型總共有 290 條限制式與 1356 個全整數變數——對一個只有十五個客戶地點的問題來說,規模已經相當可觀,這正是 TSP/VRP 類問題「輸入規模不大、模型規模卻爆炸性成長」的典型特徵。更關鍵的是,書中明確指出這個模型其實是一個**relaxation**(鬆弛版本):子迴路消去限制式(subtour elimination constraints)完全沒有寫進去。這不是偷懶,而是刻意的策略——對 TSP/VRP 這類問題,子迴路消去限制式的數量隨地點數呈指數成長,不可能一次全部列出;正確的做法是先用「沒有子迴路限制」的鬆弛模型求解,檢查解裡有沒有出現不合理的小迴圈,如果有,才把對應的子迴路消去限制式一條一條「事後」加進模型裡,重新求解——這是一種延遲限制式生成(delayed constraint generation,亦稱 cutting plane 手法)的實戰範例。

## 解答與洞見：先求「能不能做到」,再求「做得多好」

書中的解法分成三個階段,清楚示範了「先求可行性、再求品質」的兩段式求解邏輯。第一階段,求解不含子迴路消去限制式的鬆弛模型,答案是兩輛車就夠了,但花了 2263 個節點才得到這個結論,而且解出來的路線(Figure 14.10)裡明顯出現了不合理的子迴路——顯然不能拿來當作真正的答案。第二階段,把違反的子迴路,以「限制式」的形式一批一批加回模型——總共分 14 個階段、追加了 31 條子迴路消去限制式,才求得一個沒有子迴路、真正可行的解,這一步在書中提到的「筆記型電腦」上花了 1296 個節點(僅需幾秒鐘,對照當年的運算能力,這是一個值得留意的時代註腳)。第三階段,把車輛數固定在兩輛,把目標函數換成「最小化跑最久的那輛車的時間」,又花了 561 個節點求解(這一步不需要再追加任何子迴路消去限制式),最終得到兩條路線(Figure 14.11),兩輛車抵達各自最遠地點所花的時間分別是 99 分鐘與 100 分鐘——都在兩小時的限制之內,而且相當接近彼此,顯示這組路線的負載分配得相當均衡。

這個案例留給讀者最重要的洞見,不是「兩輛車、99 分鐘」這個具體答案,而是它完整展示了求解困難組合問題的一套實戰方法論:面對一個大到無法窮舉全部限制式的問題,不要試圖一次寫出「完美」的模型,而是從一個較小、較鬆的模型出發,反覆檢查解答哪裡不合理、把違反的限制式補進去,直到收斂為止——這正是往後遇到大型 TSP、VRP,乃至於任何限制式數量隨規模爆炸的問題時,最實用的求解策略。

## 連結

- [[lp-applications-and-networks]] — 本案例的資料結構(地點與地點間的行車時間)正是該章網路模型的骨架,是問題被轉譯成圖論語言的起點
- [[special-integer-programming-structures]] — 本案例的核心技巧借自該章介紹的 TSP/VRP formulation,並示範了子迴路消去限制式的延遲生成手法
- [[case-milk-collection]] — 另一個 TSP 變形的案例,可與本案例的 asymmetric formulation 互相對照
