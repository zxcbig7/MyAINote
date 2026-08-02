---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, formulation, symmetry, sensitivity-analysis]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.10〈Building Integer Programming Models II〉, pp.207–241

# 第十章：把 IP 模型從「寫得出來」磨到「跑得動」

在 [[integer-programming-fundamentals]] 與 [[special-integer-programming-structures]] 裡，我們學會了什麼時候該用 integer programming（IP）、怎麼用 0-1 變數表達邏輯條件，以及 set covering、knapsack、TSP 這些經典結構長什麼樣子。但知道「該不該用 IP」跟「怎麼寫出一個 IP 模型」，離「這個模型能不能在合理時間內被求解出來」還有一段不小的距離。這正是本章要處理的問題。在 linear programming（LP）的世界裡，同一個實際問題的不同寫法通常只會讓求解速度差個幾倍；但在 IP 的世界裡，同一個問題的好寫法跟壞寫法，求解時間可能差上幾個數量級——一個看似合理的 formulation，可能讓求解變得「昂貴到不可行」，而稍加改寫的另一個 formulation，卻能在眨眼間解出答案。本章會依序談五件事：什麼是好的、什麼是壞的 formulation；如何在模型建好之後進一步化簡它；IP 能不能像 LP 一樣提供 shadow price 之類的經濟資訊；IP 模型的敏感度分析與穩定性；最後，收斂成一份「什麼時候該用 IP、該怎麼用」的實務指南。全書預設之後的 branch and bound 求解策略沿用 [[integer-programming-fundamentals]] 介紹過的方法，這裡不再重複。

## 10.1 好與壞的 formulation

### 10.1.1 模型裡的變數數量該多還是該少

直覺上，一個 IP 模型的 0-1 變數越多，可能的組合數 $2^n$ 就越大，理應越難解——如果有 $n$ 個 0-1 變數，解答樹底部就有 $2^n$ 個可能的節點，整棵樹總共有 $2^{n+1}-1$ 個節點。對稍微大一點的 $n$，$2^n$ 大得驚人：$2^{100}$ 已經超過一百萬的五次方。但這個直覺其實嚴重高估了 branch and bound 的困難度。Branch and bound 會把大片潛在的樹排除在檢驗範圍之外——因為那些分支不是不可行，就是劣於已知的解——實務上，一個 100 個 0-1 變數的問題，往往只需要幾百個節點就能解完，這只佔潛在總節點數的 $0.00\ldots001\%$（小數點後 28 個零）。正因為 branch and bound 展現出的效率遠超乎預期，0-1 變數的數量本身其實是一個相當差的難度指標。

既然如此，反直覺的結論是：有時候刻意**增加**模型裡的整數變數，反而對求解有利。第一個工具是把一個一般整數變數展開成一串 0-1 變數：若 $\gamma$ 是已知上界為 $u$ 的一般非負整數變數，

$$0 \le \gamma \le u,$$

可以改寫成

$$\gamma = \delta_0+2\delta_1+4\delta_2+8\delta_3+\cdots+2^r\delta_r, \tag{10.1}$$

其中 $\delta_i$ 是 0-1 變數，$2^r$ 是大於等於 $u$ 的最小的 2 的次方。這種二進位展開大約需要 $\log_2 u$ 個 0-1 變數，實務上 $u$ 通常不大，展開後的規模不會太誇張；但除非是為了套用某個只吃 0-1 變數的專用演算法，一般展開帶來的好處有限，這裡不深入討論。

真正有意思的是下面這個例子——它示範了「有意義的 0-1 變數」如何幫上忙。

**Example 10.1（Jeffreys, 1974）。** 一間新工廠要蓋，決策由四個 0-1 變數表示：

$$\delta_{n,b}=\begin{cases}1 & \text{北廠、批次生產}\\0&\text{否則}\end{cases}\quad \delta_{n,c}=\begin{cases}1 & \text{北廠、連續生產}\\0&\text{否則}\end{cases}$$
$$\delta_{s,b}=\begin{cases}1 & \text{南廠、批次生產}\\0&\text{否則}\end{cases}\quad \delta_{s,c}=\begin{cases}1 & \text{南廠、連續生產}\\0&\text{否則}\end{cases}$$

「只能蓋一座廠」這個條件寫成

$$\delta_{n,b}+\delta_{n,c}+\delta_{s,b}+\delta_{s,c}=1. \tag{10.2}$$

問題是：這四個變數沒有任何一個能單獨表達「蓋北廠還是蓋南廠」這個二分決策——這個決策資訊被拆散在四個變數的組合裡。既然這是一個重要決策，如果能有一個獨立的 0-1 變數直接代表它，會非常有價值。做法是新增一個變數 $\delta$，連同兩條額外限制式：

$$\delta_{n,b}+\delta_{n,c}-\delta=0, \tag{10.3}$$
$$\delta_{s,b}+\delta_{s,c}+\delta=1. \tag{10.4}$$

$\delta$ 因此變成一個很有價值的變數——branch and bound 在搜尋樹上可以直接拿它來分支，一分支就等於問「北廠還是南廠」這個真正的決策問題，而不是在四個糾纏在一起的變數之間繞圈子。「批次還是連續生產」這個二分決策，也可以用同樣手法再引入一個 0-1 變數。

另一個增加整數變數的巧妙用法，是把限制式裡的 slack 變數本身宣告為整數。如果一條限制式

$$\sum_j a_j x_j \le b \tag{10.5}$$

裡所有變數、係數、右手邊都是整數，我們可以放入一個整數 slack 變數 $u$：

$$\sum_j a_j x_j + u = b. \tag{10.6}$$

一般情況下，這個 slack 變數會被求解套件自動加入，但只當作連續變數處理。把 $u$ 宣告為整數、並在分支優先序中優先處理它，是有好處的：一旦 $u$ 被拿來分支，(10.6) 這條限制式會產生類似 cutting plane 的效果，收緊對應 LP 問題的可行域（這個想法出自 Mitra, 1973）。

歸納起來：在 IP 模型裡，只要新增的整數變數能被善用在分支策略上，增加整數變數的數量往往是有利的，而不是有害的。

不過，有另一種情況正好相反——增加整數變數的數量反而有害，那就是模型裡存在 **symmetry**（對稱性）的時候。下面這個例子把「壞」formulation 跟「好」formulation 放在一起對照，是本章最重要的示範之一。

**Example 10.2（symmetry：貨車派遣問題）。**

一個較大 IP 模型的一部分，引入了這樣的變數：

$$\delta_{ij}=\begin{cases}1 & \text{貨車 } i \text{ 被派去跑第 } j \text{ 趟}\\0&\text{否則}\end{cases}$$

其中 $i=\{1,2,3\}$，$j=\{1,2\}$。這些貨車在運行成本、容量等各方面都無法區分——它們是完全相同的貨車。

**這是壞的 formulation。** 每一個整數可行解，都會對應到一整組「對稱等價解」。例如

$$\delta_{11}=1,\ \delta_{22}=1,\ \delta_{32}=1 \tag{10.7}$$

跟

$$\delta_{12}=1,\ \delta_{21}=1,\ \delta_{32}=1 \tag{10.8}$$

其實代表的是完全相同的實際安排——都是「派兩輛車跑第 2 趟、一輛車跑第 1 趟」，只是把哪一輛具體的車貼在哪一個角色上而已。但因為貨車在模型裡是有編號的個體，branch and bound 的搜尋樹會把 (10.7) 跟 (10.8) 當成兩個不同的節點分別探索——貨車數量一多，這種對稱重複會讓搜尋樹以組合數量的方式暴增，白白浪費大量計算。

**這是好的 formulation。** 既然貨車彼此無法區分，真正有意義的資訊只是「有幾輛車跑第 $j$ 趟」，而不是「哪一輛車跑第 $j$ 趟」。用這個角度重新定義變數：

$$n_j = \text{派去跑第 } j \text{ 趟的貨車數量}$$

(10.7) 與 (10.8) 這兩個原本對稱的解，現在會被同一組數字表達：

$$n_1=1,\quad n_2=2. \tag{10.9}$$

整數變數的數量少了（從 6 個 $\delta_{ij}$ 變成 2 個 $n_j$），對稱重複也隨之消失——這正是 10.1.1 節開頭那個「變數越多越好」的直覺失靈的地方：symmetry 是少數幾種「減少整數變數數量對計算明顯有利」的情況之一。

### 10.1.2 模型裡的限制式數量該多還是該少

在 LP 模型裡，難度很大程度上取決於限制式的數量（[[building-lp-models]] 已經討論過這點）。但在 IP 模型裡，這個效應常常被其他考量完全蓋過——事實上，一個 IP 模型往往可以透過**增加**限制式數量而變得更容易解。

原因在於 LP 跟 IP 尋找解的方式本質不同。LP 是在可行域的邊界上尋找頂點解；對應的 IP 模型，我們真正關心的卻是可能落在可行域內部的整數格點。想像一個由 ABCD 圍成的 LP 可行域，裡面散布著一些整數格點——這個 LP 模型就是對應 IP 模型的 **LP relaxation**（LP 鬆弛）。

理想情況下，我們會想把 IP 模型改寫成一個新的 formulation，讓它的 LP relaxation 恰好就等於「所有可行整數點的**凸包**（convex hull）」——如果做得到，IP 問題就能直接當 LP 問題解，因為 LP 的最佳頂點解本身就會是整數點。這樣的 formulation 稱為 **sharp**。可以分成三種情況討論：

1. 直接寫出來的 formulation，恰好就已經是凸包了。
2. 稍加改寫，就能得到凸包 formulation。
3. 改寫雖然拿不到完整凸包，但能讓可行域更靠近凸包。

**情況一：某些問題天生就是凸包。** transportation problem、minimum cost network flow problem、assignment problem 都屬於這一類：即使表面上看起來是 pure integer programming（PIP）模型，對應 LP 問題的最佳解永遠自動是整數。這類「不用付出 IP 計算代價，就能拿到整數解」的性質非常珍貴，值得能辨認就辨認出來。

背後的數學條件叫 **total unimodularity**（完全單模性，TU）：如果 $A\mathbf{x}=\mathbf{b}$，$\mathbf{x}\ge 0$（已經把 slack 變數併入等式），且矩陣 $A$ 的每一個方形子矩陣的行列式都是 $0$ 或 $\pm1$，則 $A$ 是 totally unimodular；此時對任何整數目標係數向量 $\mathbf{c}$ 與整數右手邊 $\mathbf{b}$，LP 最佳解都保證是整數（Garfinkel and Nemhauser, 1972, p.67）。可惜這個定義本身很難拿來檢驗——要驗證每一個方形子矩陣的行列式，計算量太大。書中改用一個更容易檢查、但只是**充分而非必要**條件的 **property P**：

1. $A$ 的每個元素只能是 $0$、$1$ 或 $-1$。
2. 每一欄最多只有兩個非零元素。
3. 各列可以被分成兩個子集 $P_1$、$P_2$，使得：若某欄的兩個非零元素同號，則兩者分屬不同子集；若異號，則兩者屬於同一子集。

一個特殊情形是 $P_1$ 為空、$P_2$ 涵蓋所有列——這時每一欄必須是單一元素 $\pm1$，或一正一負的兩個非零元素。以第五章的 transportation problem 為例：

$$-x_{11}-x_{13}-x_{14}-x_{15}=-135$$
$$-x_{21}-x_{22}-x_{25}=-56$$
$$-x_{31}-x_{32}-x_{33}-x_{34}-x_{35}=-93$$
$$x_{11}+x_{21}+x_{31}=62,\quad x_{22}+x_{32}=84,\quad x_{13}+x_{33}=39,\quad x_{14}+x_{34}=91,\quad x_{15}+x_{25}+x_{35}=9 \tag{10.10}$$

每一欄都恰好有一個 $+1$ 和一個 $-1$，property P 成立，TU 因此得到保證。（若 $A$ 是 TU，轉置矩陣 $A'$ 也一定是 TU——這對應到「每列剛好有一個 $+1$ 和一個 $-1$」的情形。）值得一提的是，許多 IP 模型的矩陣即使不滿足 TU，仍然經常（雖然不保證）能讓對應 LP 得到整數解——[[special-integer-programming-structures]] 提到的 set packing、partitioning、covering 問題就常常如此，背後的技術性原因超出本書範圍（Garfinkel and Nemhauser, 1972, Ch.8；set partitioning 的特定右手邊條件見 Padberg, 1974）。

**情況二：改寫成 TU 結構。** 考慮一個常見的邏輯條件的一般化寫法：

$$\delta_1+\delta_2+\cdots+\delta_n - n\delta \le 0, \tag{10.11}$$

其中 $\delta_i,\delta$ 都是 0-1 變數。這條限制式代表的邏輯是「只要有任何一個 $\delta_i=1$，就必須 $\delta=1$」：

$$\delta_1=1 \lor \delta_2=1 \lor \cdots \lor \delta_n=1 \to \delta=1, \tag{10.12}$$

或等價地：

$$\delta=0 \to \delta_1=0,\ \delta_2=0,\ \ldots,\ \delta_n=0. \tag{10.13}$$

[[integer-programming-fundamentals]] 已經示範過類似的邏輯條件可以拆成兩條限制式；同樣的手法可以套用在這裡，把 (10.11) 拆成 $n$ 條限制式：

$$\delta_1-\delta\le 0,\quad \delta_2-\delta\le 0,\quad \ldots,\quad \delta_n-\delta\le 0. \tag{10.14}$$

如果模型裡所有限制式都長成 (10.14) 這種樣子，dual 問題會滿足 property P，TU 因此得到保證——這代表我們可以完全繞過 IP 的高計算成本，直接當 LP 解（[[case-opencast-mining]] 給出這種 formulation 的實際應用）。

值得特別注意的是：(10.11) 恰好是把 (10.14) 裡所有限制式加總起來得到的結果，但在 **LP 意義上**，(10.11) 跟 (10.14) 並不等價——加總的過程會削弱限制的效果。例如

$$\delta_1=\frac12,\ \delta_2=\delta_3=\frac14,\ \delta=\frac1n,\ \text{其餘 } \delta_i=0 \tag{10.15}$$

滿足 (10.11)，卻在 $n\ge3$ 時違反 (10.14)。也就是說，雖然 (10.11) 與 (10.14) 在「整數」意義上完全等價（同一組整數解集合），(10.14) 卻能更有效地排除不想要的分數解——這正是「用更多限制式換取更緊 LP relaxation」這個原則的具體體現。這個做法跟 [[case-food-manufacture-2]]（MIP 模型）、以及 [[case-decentralisation]]、[[case-logical-design]]（兩者都是 PIP 模型）都直接相關。

**情況三：改寫拿不到完整凸包，但能更靠近它。** 如果模型裡只有部分限制式長成 (10.11) 這種形式，把它們展開成 (10.14) 也能讓 LP 的可行域縮小，即使模型裡其他限制式的存在使我們無法確定 LP 最佳解是否真的變成了整數，這樣的解通常會「更接近」整數最佳解。這種改寫值得一試，即使代價是限制式數量的擴張。

除了 TU 之外，還有一個經常被忽略、但同樣重要的實務細節：連結 0-1 指示變數 $\delta$ 與連續變數 $x$ 時所用的 **big-$M$ 係數** 該取多大。最簡單的情況是我們想表達

$$x>0 \to \delta=1, \tag{10.16}$$

寫成限制式

$$x-M\delta \le 0. \tag{10.17}$$

只要 $M$ 是 $x$ 的一個真上界，不論多大，(10.16) 的邏輯都成立。但 $M$ **越小越好**——因為 $M$ 越小，對應 LP 問題的可行域就越受限制。假設我們把 $M$ 取成 1000，而實際上 $x$ 從不超過 100，以下這個分數解會滿足 (10.17)：

$$x=70,\quad \delta=\frac12, \tag{10.18}$$

但如果 $M$ 取 100，同一組數字就會違反 (10.17)——換句話說，$M$ 取太大，會讓 LP relaxation 允許本來不該存在的分數解。更糟的是，同樣把 $M$ 取 1000，下面這組解也滿足 (10.17)：

$$x=5,\quad \delta=0.005, \tag{10.19}$$

這麼小的 $\delta$ 很可能落在求解套件判定「整數與否」的容忍值以下，會被直接當成 0，產生一個似是而非的解

$$x=5,\quad \delta=0. \tag{10.20}$$

如果 $M$ 取得小一點，這種情況就比較不會發生。此外，係數大小相差過於懸殊本身就不是好事（[[building-lp-models]] 3.4 節已經談過），也是傾向把 $M$ 取小的另一個理由。

同樣的「拆解換取更緊的 LP relaxation」原則，也能套用在把一條含 $M$ 係數的限制式拆成多條上。

**Example 10.3（供應站配送：壞的聚合式 vs 好的拆解式）。**

$$\delta=\begin{cases}1&\text{倉庫已建}\\0&\text{否則}\end{cases}\qquad x_i=\text{供應給客戶 } i \text{ 的數量}$$

若倉庫已建，可以供應客戶 $i$ 至多 $M_i$ 單位；若倉庫未建，任何客戶都無法被供應。

**壞的 formulation**：用一條聚合限制式表達：

$$x_1+x_2+\cdots+x_n-M\delta\le 0, \tag{10.21}$$

其中 $M=M_1+M_2+\cdots+M_n$。

**好的 formulation**：拆成每個客戶各自一條限制式：

$$x_1-M_1\delta\le 0,\quad x_2-M_2\delta\le 0,\quad \ldots,\quad x_n-M_n\delta\le 0. \tag{10.22}$$

(10.22) 對應的 LP relaxation 明顯比 (10.21) 更受限制——這正是同一套「拆解優於聚合」的邏輯，只是換了一個場景。

**總結 10.1 節**，一個好的 IP formulation，應該追求以下三個目標：

1. 使用能在 branch and bound 分支過程中派上真正用場的整數變數；必要時，新增額外的 0-1 變數來明確表達具有意義的二分決策。
2. 讓對應 IP 模型的 LP 問題盡可能受限制（LP relaxation 越緊越好）。
3. 如果求解套件支援，盡量使用 special ordered sets（見 [[integer-programming-fundamentals]] 對 SOS 的介紹）。

還有兩個實務建議值得放在心上。第一，在動手建一個大型 IP 模型之前，先建一個小規模版本做實驗，測試不同的化簡與求解策略——這能在投入大量心力於完整模型之前，先累積寶貴的經驗。第二，光是仔細檢視模型結構、收緊限制式，威力可以有多大，書裡舉了一個驚人的真實案例：Daniel (1978) 描述過一個原本在 4757 個節點後被放棄的搜尋樹，經過重新 formulation 之後，僅用 171 個節點就解出了答案——同一個問題，formulation 的品質造成了近 30 倍的計算量差距。IP formulation 的自動化收緊化簡，可參考 Crowder et al. (1983) 與 Van Roy and Wolsey (1984)；facet-defining 限制式的推導，見 Wolsey (1976, 1989)。

## 10.2 化簡一個整數規劃模型

前一節談的是「建模時」的設計選擇；這一節談的是模型已經建好之後，如何在**不改變它代表的實際問題**的前提下，進一步改寫它，讓它更容易求解。

### 10.2.1 收緊 bounds

在 [[building-lp-models]] 3.4 節，我們介紹過 Brearley et al. (1975) 簡化 LP 模型的程序，其中一步是移除 LP 模型裡多餘的簡單上下界。但對整數變數而言，移除多餘的 bounds 通常**不值得**；比較好的做法反而是**收緊** bounds——道理跟 10.1 節「讓 LP relaxation 更受限制」的論證是一致的：收緊 bounds 之後，對應 LP 問題的最佳解會更靠近整數最佳解。

下面這個取自 Balas (1965) 的小例子，展現了收緊 bounds 的威力可以有多驚人。

**Example 10.4。**

$$\text{Minimize}\quad 5\delta_1+7\delta_2+10\delta_3+3\delta_4+\delta_5$$
$$\text{subject to}\quad \delta_1-3\delta_2+5\delta_3+\delta_4-\delta_5\ge 2 \quad(\text{R1})$$
$$-2\delta_1+6\delta_2-3\delta_3-2\delta_4+2\delta_5\ge 0 \quad(\text{R2})$$
$$-\delta_2+2\delta_3-2\delta_4-\delta_5\ge 1 \quad(\text{R3})$$

所有 $\delta_i$ 都是 0-1 變數。純粹靠邏輯推導，不需要任何 branch and bound：

1. 由 (R3)：$2\delta_3 \ge 1+\delta_2+\delta_4+\delta_5 \ge 1$，故 $\delta_3\ge 1/2$。既然 $\delta_3$ 是 0-1 變數，這個隱含下界可以收緊——$\delta_3$ 只能被設為 1，並可從問題中移除。
2. 由 (R2)：$6\delta_2 \ge 3+2\delta_1+2\delta_4-2\delta_5 \ge 1$，故 $\delta_2\ge 1/6$。同理，$\delta_2$ 的下界可收緊為 1，固定 $\delta_2=1$。
3. 由 (R3)：$\delta_4 \le -\delta_5 \le 0$，故 $\delta_4$ 可以固定為 0。
4. 由 (R3)：$\delta_5\le 0$，故 $\delta_5$ 也固定為 0。
5. 此時所有限制式都變成多餘的，可以整條移除。剩下唯一的變數 $\delta_1$，顯然應該設為 0（因為它只出現在目標函數裡，係數為正、要極小化）。

這個例子是收緊 bounds 效果的一個極端案例——光靠這個程序，就已經把整個問題完全解開，完全不需要動用 branch and bound 搜尋樹。

### 10.2.2 把單一整數限制式化簡成另一個單一限制式

考慮這條整數限制式：

$$4\gamma_1+6\gamma_2\le 9, \tag{10.23}$$

其中 $\gamma_1,\gamma_2$ 是一般整數變數。用幾何角度看（把 (10.23) 畫成圖），很容易看出它其實可以改寫成

$$\gamma_1+2\gamma_2\le 2. \tag{10.24}$$

圖上，原限制式 (10.23) 要求可行點落在直線 AB 的左側；把 AB 平移到 CD，**沒有排除任何原本可行的整數點，也沒有納入任何新的整數點**——但 CD 對應的 LP 可行域比 AB 小，因此 (10.24) 比 (10.23) 更受限制，在對應 LP 問題上更有利。這種一般整數變數的限制式在實務中不常見，因此我們把焦點放回 0-1 變數的情形：給定一條

$$a_1\delta_1+a_2\delta_2+\cdots+a_n\delta_n \le a_0, \tag{10.25}$$

目標是找到等價（在整數解集合上）但更受限制（在 LP relaxation 上）的

$$b_1\delta_1+b_2\delta_2+\cdots+b_n\delta_n\le b_0. \tag{10.26}$$

不失一般性，可以假設所有係數非負（若原本有負係數 $a_i$，把對應變數用 $\delta_i=1-\delta_i'$ 互補即可）；'$\ge$' 限制式可先轉成 '$\le$'；等式限制式則拆成一條 '$\le$' 加一條 '$\ge$' 分別化簡。這種單一限制式的化簡本身也可以formulation 成一個 LP 問題求解，細節超出本章範圍，[[case-optimising-a-constraint]] 給出一個具體案例與完整討論；[[case-market-sharing]] 也是這種化簡值得動手做的實際例子。整體而言，書裡誠實地提醒：化簡單一整數限制式的效益，很多時候並不值得投入——許多限制式代表的是邏輯條件，本來就已經是最簡形式；真正划算的場合主要是專案選擇（project selection）與資本預算（capital budgeting）類問題。

### 10.2.3 把單一限制式化簡成一組限制式（facets）

理想情況下，我們希望把單一 0-1 限制式，改寫成定義**可行 0-1 點凸包**的整組限制式。

**Example 10.5。**

$$3\delta_1+3\delta_2-2\delta_3+2\delta_4+2\delta_5 \le 4, \tag{10.30}$$

$\delta_i$ 皆為 0-1 變數。滿足 (10.30) 的 0-1 解的凸包，可以由以下限制式給出：

$$\delta_1+\delta_2-\delta_3+\delta_4\le 1, \tag{10.31}$$
$$\delta_1+\delta_2-\delta_3+\delta_5\le 1, \tag{10.32}$$
$$\delta_1+\delta_2+\delta_4+\delta_5\le 2, \tag{10.33}$$
$$2\delta_1+\delta_2-\delta_3+\delta_4+\delta_5\le 2, \tag{10.34}$$
$$\delta_1+2\delta_2-\delta_3+\delta_4+\delta_5\le 2, \tag{10.35}$$

加上簡單的 $\delta_i\ge0,\ \delta_i\le1$。這種構成可行域邊界的面稱為 **facets**（面）：兩變數問題的 facets 是一維的直線（如 10.2.2 節的圖）；三變數問題的 facets 是二維平面；$n$ 變數問題的 facets 是 $(n-1)$ 維的超平面。

可惜的是，目前並沒有一個實用的一般程序，能替任意單一 0-1 限制式產生完整的凸包限制式集合。Hammer et al. (1975) 給出一張表，列出所有涉及最多五個變數的 0-1 限制式的凸包 facets——要用這張表，得先用上一節的方法把限制式化簡成單一限制式形式。對於涉及超過五個變數的**特定類型**限制式，也可能求出凸包。雖然產生任意單一 0-1 限制式凸包 facets 的一般程序尚不存在，Balas (1975) 給出一個能產生**部分** facets 的程序，Hammer et al. (1975) 與 Wolsey (1975) 也給出類似程序——這些程序都只能得到係數僅含 $0$ 與 $\pm1$ 的那些 facets。

**Balas 的 cover 程序。** 考慮一條純 0-1 限制式（同樣不失一般性假設係數非負）：

$$a_1\delta_1+a_2\delta_2+a_3\delta_3+\cdots+a_n\delta_n\le a_0. \tag{10.36}$$

- **Cover**：指標子集 $\{i_1,i_2,\ldots,i_r\}$，若 $a_{i_1}+a_{i_2}+\cdots+a_{i_r}>a_0$，就稱為一個 cover——因為顯然這些指標對應的 $\delta_i$ 不可能同時全部為 1，這個條件可以寫成

$$\delta_{i_1}+\delta_{i_2}+\cdots+\delta_{i_r}\le r-1. \tag{10.37}$$

- **Minimal cover**：如果一個 cover 的任何真子集都不再是 cover，就稱為 minimal cover。
- **Extended cover**：把一個 minimal cover 用以下方式擴充：選出 cover 中係數最大的 $a_{i_j}$；把 cover 外所有係數 $a_{i_{r+k}}\ge a_{i_j}$ 的指標都加進來，得到擴充後的集合 $\{i_1,\ldots,i_{r+s}\}$。對應限制式 (10.37) 也隨之擴充為

$$\delta_{i_1}+\delta_{i_2}+\cdots+\delta_{i_{r+s}}\le r-1. \tag{10.38}$$

- **Strong cover**：若一個 minimal cover 產生的 extended cover，不是任何「指標數量相同」的其他 minimal cover 所產生的 extended cover 的真子集，這個原始 minimal cover 就稱為 strong cover。

Balas 證明：如果一個 extended cover 源自 strong cover，那麼 (10.38) 這樣的限制式，就涵蓋了 (10.33) 這類凸包裡所有係數為 0 或 1 的 facets。這代表可以設計出一套系統化、計算上快速的方法，產生某個 0-1 限制式對應的所有 strong cover，藉此得到所有能用 0 與 $\pm1$ 係數表達的凸包 facets。

**Example 10.6**（延續 Example 10.5，示範如何真正找出 (10.31)–(10.33)）。把 (10.30) 改寫成正係數形式（令 $\delta_3'=1-\delta_3$）：

$$3\delta_1+3\delta_2+2\delta_3'+2\delta_4+2\delta_5\le 6. \tag{10.39}$$

(10.39) 的 minimal covers 有八個：$\{1,2,3\}$、$\{1,2,4\}$、$\{1,2,5\}$、$\{1,3,4\}$、$\{1,3,5\}$、$\{1,4,5\}$、$\{2,3,4\}$、$\{2,3,5\}$、$\{2,4,5\}$（依 (10.40)–(10.48) 編號）。經過擴充，前三個 minimal cover $\{1,2,3\}$、$\{1,2,4\}$、$\{1,2,5\}$ 分別是後面幾個 cover 擴充結果的真子集，因此**不是** strong cover；剩下六個才是 strong cover，它們的擴充結果給出三條 facet 限制式：

$$\delta_1+\delta_2+\delta_3'+\delta_4\le 2, \tag{10.55}$$
$$\delta_1+\delta_2+\delta_3'+\delta_5\le 2, \tag{10.56}$$
$$\delta_1+\delta_2+\delta_4+\delta_5\le 2. \tag{10.57}$$

把 $\delta_3'$ 換回 $1-\delta_3$，就得到 Example 10.5 裡的 (10.31)–(10.33)——這正是 Balas 程序如何把一條抽象的單一限制式，機械化地展開成一組 facet 限制式的完整示範。

**Example 10.7**（回到供應站問題，用 cover 理論重新驗證 10.1 節的直覺）。設

$$\delta_{n+1}=\begin{cases}1&\text{倉庫已建}\\0&\text{否則}\end{cases}\qquad \delta_i=\begin{cases}1&\text{客戶 } i \text{ 被此倉庫供應}\\0&\text{否則}\end{cases}\quad i=1,\ldots,n$$

至多 $r$（$r<n$）個客戶可以被供應，若倉庫未建則沒人可被供應：

$$\delta_1+\delta_2+\cdots+\delta_n-r\delta_{n+1}\le 0. \tag{10.58}$$

這條限制式的 minimal covers 是所有 $\{i,n+1\}$（$i=1,\ldots,n$，無法再被擴充），以及 $\{1,\ldots,n\}$ 中任何 $r+1$ 個指標的子集，而後者全都會擴充成同一個 extended cover $\{1,\ldots,n,n+1\}$。這兩類 cover 化簡出的 facet 限制式，正是

$$\delta_i-\delta_{n+1}\le 0,\quad i=1,\ldots,n \tag{10.64}$$

以及

$$\delta_1+\delta_2+\cdots+\delta_n-\delta_{n+1}\le r-1. \tag{10.65}$$

(10.64) 正是 Example 10.3 裡「按客戶拆解」的 $x_i-M_i\delta\le0$ 好 formulation 的 0-1 版本！這說明 10.1 節憑直覺得到的「拆解優於聚合」，跟 10.2.3 節用嚴謹的 cover 理論推出的 facet 限制式，其實是同一件事的兩種呈現方式——一個是經驗法則，一個是可以證明的凸包邊界。這種拆解方式，在 [[case-market-sharing]] 問題上格外有價值。

### 10.2.4 化簡整組限制式

到目前為止談的都是逐條化簡個別限制式。真正理想的目標，是把**所有**限制式一起化簡成定義完整可行整數點凸包的整組限制式。必須誠實指出：逐條化簡個別限制式，並不保證整個模型的 LP relaxation 會因此變成整數解——即使這麼做對最終解 IP 問題通常仍有計算上的幫助。下面這個例子清楚示範了這個限制。

**Example 10.8。**

$$\text{Maximize}\quad \delta_1+2\delta_2+\delta_3$$
$$\text{subject to}\quad 2\delta_1+3\delta_2+2\delta_3\le 3 \tag{10.66}$$
$$\delta_1+\delta_2-2\delta_3\le 0 \tag{10.67}$$

$\delta_1,\delta_2,\delta_3$ 皆為 0-1 變數。原始模型對應 LP 問題的最佳解是 $\delta_1=0,\delta_2=3/4,\delta_3=3/8$，目標值 $15/8$。

如果把 (10.66) 換成它自己的 facets（(10.68) 來自 (10.66)，(10.69)(10.70) 來自 (10.67) 的兩個 facets），得到化簡後的模型：

$$\text{Maximize}\quad \delta_1+2\delta_2+\delta_3$$
$$\text{subject to}\quad \delta_1+\delta_2+\delta_3\le 1 \tag{10.68}$$
$$\delta_1-\delta_3\le 0 \tag{10.69}$$
$$\delta_2-\delta_3\le 0 \tag{10.70}$$

這個化簡後模型對應 LP 問題的最佳解是 $\delta_1=0,\delta_2=1/2,\delta_3=1/2$，目標值 $3/2$——比原本的 $15/8$ **更靠近**整數最佳解，但**仍然是分數解**，並沒有得到整數最佳解！真正的整數最佳解是 $\delta_1=0,\delta_2=0,\delta_3=1$，目標值 $1$。

這個例子清楚說明：逐條限制式各自化簡，並沒有把整個模型收緊到足以保證整數解——只有找到整個模型的**聯合凸包**才能保證這件事，而目前並沒有一個實用的一般程序，能對任意一組純 0-1 限制式的集合做到這一點。這方面有實際成果的特殊限定類別，最著名的是 matching problem（Edmonds, 1965）；Hammer et al. (1975) 也對他們稱為 "regular" 的一類問題（包含 set covering 與 knapsack 問題）給出了部分結果——這些局部成果目前為止還沒有給出一個對一般實務問題有價值的化簡工具，本章不再深入。

值得一提的是，也有人研究過相反方向的程序：把一組純整數等式限制式逐步合併成單一個等式限制式，形成一個 knapsack problem（Bradley, 1971）。不過這麼做通常會產生極其龐大的係數，如果目標是拿這個合併結果去解 IP 問題，意義不大——合併限制式的整體效果通常是**削弱**而非收緊對應的 LP 問題（Chvátal and Hammer, 1975 也描述過合併純 0-1 不等式的程序；較新的文獻見 Bienstock and McClosky, 2012）。

本節的討論大致集中在為模型加入額外的限制式，以收緊對應的 LP 模型——這可以放在 cutting plane 演算法的脈絡下理解：我們是在加入 cuts 來消除某些可能的分數解。大多數 cutting plane 演算法會在最佳化過程中自動生成這類額外限制式；本書身為一本建模書，我們關心的只是**在初始模型裡**就加入這些 cuts。

### 10.2.5 不連續變數

有時我們需要限制一個連續變數只能落在幾段不連續的範圍內，例如

$$x=0 \text{ 或 } a\le x\le b \text{ 或 } x=c, \tag{10.71}$$

其中 $0<a<b<c$。最直接的做法，是沿用 [[integer-programming-fundamentals]] 談 disjunctive constraints 時介紹的手法：用 0-1 變數各自代表三種（或更多）可能性中的一種。

另一種替代 formulation（Brearley, 1975，沿用 Thomas et al., 1978 對摻配問題邏輯限制的更傳統寫法）是：

$$x=a y_1+b y_2+c\delta_2, \tag{10.72}$$
$$\delta_1+y_1+y_2+\delta_2=1, \tag{10.73}$$

其中 $\delta_1,\delta_2$ 是 0-1 整數變數，$y_1,y_2$ 是非負連續變數。(10.71) 可以一般化或特殊化。一個常見的特例是 **semi-continuous variable**（半連續變數）：

$$x=0 \text{ 或 } x\ge a\quad(a>0). \tag{10.74}$$

要 formulation 這個條件，必須先給 $x$ 指定一個上界 $M$：

$$x=a y_1+M y_2, \tag{10.75}$$
$$\delta+y_1+y_2=1, \tag{10.76}$$

其中 $\delta$ 是 0-1 變數，$y_1,y_2$ 是非負連續變數。

### 10.2.6 Disjunctive constraints 的另一種 formulation

Jeroslow and Lowe (1984) 為 disjunction of constraints 提出了一種替代 formulation，同時建立了一套「Mixed Integer Programming Representability 理論」，把整個主題放在更系統化的基礎上。這種 "disjunctive formulation" 除了理論上的優勢，在大型模型上也展現出實務上的優勢（計算經驗見 Jeroslow and Lowe, 1985；完整討論見 Jeroslow, 1989 的講義）。

假設我們有一個像 [[integer-programming-fundamentals]] 討論過的那種 disjunction，其中每個 $R_k$ 代表一組限制式：

$$\sum_j a_{ijk}x_j\le b_{ik},\quad i=1,2,\ldots,m_k. \tag{10.77}$$

假設每一組 (10.77) 都有一個**封閉**（closed）的可行域（必要時可透過已知的變數上界達成）。每個變數 $x_j$ 被拆成對應每個析取項的獨立變數 $x_{jk}$：

$$x_j=x_{j1}+x_{j2}+\cdots+x_{jN}. \tag{10.78}$$

新變數取代原變數，代入對應的限制式集合 $R_k$，得到：

$$\sum_j a_{ijk}x_{jk}-b_{ik}\delta_k\le 0,\quad i=1,2,\ldots,m_k, \tag{10.79}$$
$$\sum_k \delta_k=1, \tag{10.80}$$

其中 $\delta_k$ 是 0-1 整數變數。(10.80) 強制恰好一個 $\delta_k$ 為 1，其餘為 0；當 $\delta_k=0$ 時，(10.79)（配合可行域封閉的假設）會強制對應的 $x_{jk}$ 全部為零，使得對每個 $j$，只有一個分量 $x_{jk}$ 可以非零、等於 $x_j$——恰好對應到被選中的 $R_k$。

這個 formulation 有一個強大的理論性質：如果每組 (10.77) 本身都是 **sharp**（即它自己的 LP relaxation 就是凸包），那麼整個析取的 Jeroslow formulation 結果**也一定是 sharp**——換句話說，這種拆變數的做法，不像單純的 big-$M$ 析取寫法那樣會犧牲緊緻性。（如果 (10.77) 裡的變數全是連續變數，這個性質同樣成立。）

在 Boolean 代數裡，任何命題都可以寫成標準的 **disjunctive normal form**（DNF），只用 and（$\cdot$）、or（$\vee$）、not（$\sim$）三種連接詞，例如

$$(R_{11}\cdot R_{12}\cdots R_{1m_1})\vee(R_{21}\cdot R_{22}\cdots R_{2m_2})\vee\cdots\vee(R_{N1}\cdot R_{N2}\cdots R_{Nm_2}) \tag{10.81}$$

其中每個 clause 是若干陳述式 $R_{ij}$（部分可能被否定）的 conjunction。Jeroslow 建議，一般而言最好先把模型表達成這種 disjunctive normal form，再套用他的 disjunctive formulation。理論上，任何（有界的）整數變數本身就代表一種可能性的 disjunction，例如

$$x=0\vee x=1\vee x=2\vee\cdots\vee x=m, \tag{10.82}$$

因此理論上任何 IP 都可以這樣寫。實務上的限制是：這種拆變數的 formulation，可能把變數數量拆到過於龐大，必須採取折衷——結果通常不再是 sharp，但通常比傳統 formulation 更緊（可以再搭配一些簡化程序，例如引入額外變數的 reduction procedure）。是否能得到更緊的限制式，Martin (1987) 與 Williams and Brailsford (1997) 有進一步討論。

Jeroslow 還提出兩個值得記住的觀察。第一，從 sharpness 的角度看，應該**先套用 and 連接詞、再做 IP formulation**，而不是先把各個部分分別 formulation 成 IP、再用 and 把它們接起來——這是因為（用集合記號表示）

$$\text{Con}(S\cap T)\subseteq \text{Con}(S)\cap\text{Con}(T) \tag{10.83}$$

其中 $S,T$ 是集合，$\text{Con}$ 表示取凸包——「先交集再取凸包」得到的集合，永遠是「先各自取凸包再交集」的子集或相等，絕不會更大。換句話說，順序做錯了，會白白損失緊緻性。第二，我們應該追求 **hereditarily sharp** 的 formulation：也就是說，當某些整數變數被 branch and bound 固定下來之後，剩下的子模型依然保持 sharp。

### 10.2.7 Symmetry

10.1.1 節已經用貨車派遣的例子（Example 10.2）示範了 symmetry 對計算的傷害。這裡給出更一般化的處理手法。一個模型如果存在大量等價解，例如配送問題裡的變數 $\delta_{ij}=1$ 若且唯若車輛 $i$ 造訪客戶 $j$，當車輛彼此相同時，$\delta_{12}=1,\delta_{22}=0$ 跟 $\delta_{12}=0,\delta_{22}=1$ 其實是等價的解。為了避免為了生成、探索這兩個等價解付出雙倍計算成本，可以加入額外的**對稱破壞**限制式：

$$\delta_{1j}\ge\delta_{2j}\ge\cdots\ge\delta_{nj}\quad\text{對所有 } j. \tag{10.84}$$

這條限制式強制一個「規範化」的順序：如果要有車輛造訪客戶 $j$，一定先由編號較小的車輛開始造訪，排除掉單純把哪輛車貼上哪個角色而產生的重複。

另一個替代方案，是跟 Example 10.2 一樣，把這些變數聚合成 $n_j$（造訪客戶 $j$ 的車輛數）。但要注意：這種聚合有時候會**削弱** LP relaxation——這正是對稱性處理上一個真實的取捨：加對稱破壞限制式，保留了原本的變數結構跟較緊的 LP relaxation，但限制式數量增加；改用聚合變數，直接消除對稱性、也減少變數數量，但可能讓 LP relaxation 變鬆。消除對稱解生成的方法，通常必須依賴模型本身的特性量身打造，沒有放諸四海皆準的公式。這裡也點出一個有趣的對照：symmetry 在數學的其他分支裡，往往被視為值得利用的優美結構；但在 IP 的計算世界裡，symmetry 幾乎純粹是計算上的負擔，值得優先辨認、優先處理。

## 10.3 整數規劃能提供的經濟資訊

在 [[interpreting-lp-solutions]] 6.2 節，我們看到 LP 模型除了最佳解本身，還能透過 shadow price 與 reduced cost 提供豐富的經濟資訊，dual model 與 primal model 之間存在乾淨的對應關係。這一節要問：同樣的經濟資訊，能不能從 IP 模型裡拿到？答案是：遠比 LP 困難，而且在某些情況下相當模稜兩可。

先從理論上釐清問題的根源。假設我們有一個 IP 極大化問題 $P$；對應的 LP 問題 $P'$（LP relaxation）。只要 $P'$ 可行且不是 unbounded，就存在一個可解的 dual 問題 $Q'$。從 LP 對偶定理，我們知道

$$\max\ \text{obj}(P')=\min\ \text{obj}(Q').$$

而由於加上整數限制之後 $P$ 比 $P'$ 更受限制（對極大化問題來說，限制越多解只會越差或持平），我們有

$$\max\ \text{obj}(P)\ \le\ \max\ \text{obj}(P')\ =\ \min\ \text{obj}(Q').$$

$Q'$ 的最小目標值，是我們透過對限制式做一組估價，所能得到的 $P$ 目標值的**最小上界**——這跟 LP 情形形成對比：在 LP 裡，dual 給出的是一個**嚴格**上界（恰好在最佳解達到）。這個「$P$ 的最大目標值」跟「$P'$ 的最大目標值（或 $Q'$ 的最小目標值）」之間的差距，有時被稱為 **duality gap**，可以（相當粗略地）理解成：如果硬要拿 dual 估價當作 IP 問題的 shadow price 使用，這個估價會有多不可靠的一個度量。

**Example 10.9（product mix，IP 版本）。**

$$\text{Maximize}\quad 12\gamma_1+5\gamma_2+15\gamma_3+10\gamma_4$$
$$\text{subject to}\quad 5\gamma_1+\gamma_2+9\gamma_3+12\gamma_4\le 15, \tag{10.85}$$
$$2\gamma_1+3\gamma_2+4\gamma_3+\gamma_4\le 10, \tag{10.86}$$
$$3\gamma_1+2\gamma_2+4\gamma_3+10\gamma_4\le 8, \tag{10.87}$$

$\gamma_1,\gamma_2,\gamma_3,\gamma_4$ 皆為非負整數變數。整數最佳解是 $\gamma_1=2,\gamma_2=1,\gamma_3=0,\gamma_4=0$，目標值 29。對應 LP 問題的最佳解是 $\gamma_1=8/3,\gamma_2=\gamma_3=\gamma_4=0$，目標值 32——duality gap 是 3。

拿到 IP 最佳解之後，管理者自然還是會問跟 LP 時一樣的問題：（Q1）已經用滿的產能，邊際價值是多少？（Q2）沒有被生產的產品，價格要漲多少才值得生產？在 LP 情形下，這兩題的答案分別來自 shadow price 與 reduced cost，一旦得到最佳估價，最佳生產政策可以直接靠簡單的算術推導出來，而且所有產能的總估價恰好等於最佳生產政策帶來的總利潤。可惜在 IP 情形下，並沒有這麼乾淨的估價可以套用。

**第一個差異（A）：IP 裡有正的 slack，不代表零經濟價值。** 例如 (10.85) 這條限制式，在 IP 最佳解裡並沒有被用滿——在 LP 情形下，這樣的限制式代表一個 **free good**（見 [[interpreting-lp-solutions]] 6.2 節），shadow price 應該是零，甚至可以直接把這條限制式從模型移除而不影響最佳解。但在 IP 情形下，這條限制式**不能**被忽略——移除它會改變最佳解。原因不難理解：雖然 (10.85) 目前右手邊值 15 稍微增加一點點沒有意義，但只要至少增加 3，就能把兩個 $\gamma_1$ 或一個 $\gamma_2$，換成兩個 $\gamma_3$，明顯有利可圖。所以這條「看似有餘裕」的限制式，其實仍然帶有正的經濟價值。

**Example 10.10（更尖銳的反例：一般根本不存在合理的估價）。**

$$\text{Maximize}\quad 4\gamma_1+3\gamma_2+\gamma_3$$
$$\text{subject to}\quad 2\gamma_1+2\gamma_2+\gamma_3\le 7, \tag{10.88}$$

$\gamma_1,\gamma_2,\gamma_3\ge0$ 且為整數。最佳解是 $\gamma_1=3,\gamma_2=0,\gamma_3=1$。我們嘗試給這條限制式一個估價 $\pi$（"shadow price" 或 accounting value）：要讓 $\gamma_3$ 划算（值得被生產），必須 $\pi\le1$；但這同時意味著 $2\pi<3$，也就是說 $\gamma_2$ 同樣看起來划算——然而我們已經知道最佳解裡 $\gamma_3$ 值得生產，$\gamma_2$ 卻不值得生產。**沒有任何一個單一估價 $\pi$ 能同時解釋這兩件事。**

**第二個差異（B）：對一般 IP 問題，並不存在任何能像 LP 那樣、透過估價機制重現最佳決策的合理估價方式。**（這裡的「限制式」不包含可行性限制式 $\gamma_i\ge0$。）

擺脫這個困境的一種方式，是設法取得代表**可行整數點凸包**的限制式（若是 MIP 模型，則是整數維度上點的凸包）。有了凸包限制式，模型就能當 LP 問題處理，重新拿到性質良好的 shadow price。雖然如 10.2 節所述，一般求凸包的計算成本往往高到不切實際，但在某些特定問題類型上，這麼做確實能提供有價值的經濟資訊——下面的 shared fixed cost 問題（Example 10.12）就是一個絕佳示範。這裡先用 Example 10.9 的凸包 formulation 做個過渡練習：

**Example 10.11**（Example 10.9 的凸包 formulation）：

$$\text{Maximize}\quad 12\gamma_1+5\gamma_2+15\gamma_3$$
$$\text{subject to}\quad \gamma_1+\gamma_3\le 2, \tag{10.89}$$
$$\gamma_1+\gamma_2+\gamma_3\le 3, \tag{10.90}$$
$$2\gamma_1+\gamma_2+3\gamma_3\le 5, \tag{10.91}$$
$$\gamma_3\le 1, \tag{10.92}$$

$\gamma_1,\gamma_2,\gamma_3\ge0$ 且為整數（$\gamma_4$ 一旦取整數值就會被 (10.87) 強制為零，因此可以省略）。這組限制式（10.89）–（10.92）對應的 shadow price 分別是 2、0、5、0。（因為 Example 10.11 是 degenerate 的，如 [[interpreting-lp-solutions]] 討論過的那樣，也存在其他組合的替代 shadow price。）不幸的是，這些新限制式的 shadow price，該如何對應回原本 (10.85)–(10.87) 的物理意義，並不清楚——凸包 formulation 雖然數學上乾淨，卻常常失去了跟原始限制式的直接對應關係。

**Gomory-Baumol 定價法（1960）。** 另一條路是對 IP 模型套用 cutting plane 演算法，逐步加入限制式直到得到整數解，然後對原始限制式跟新加入的限制式一起求出 shadow price，再把新增限制式的 shadow price 歸算（impute）回它們衍生自的原始限制式。可惜這種做法得出的估價**不唯一**，取決於 cutting plane 演算法實際套用的順序；此外，這套方法還必須把可行性條件 $\gamma_i\ge0$ 也納入被估價的「原始限制式」之列，結果這些純粹的可行性條件也可能被賦予非零的經濟估價——即使對應的 $\gamma_i$ 在最佳解裡取正值。一種合理化的說法是：把這個估價，理解成一種因為 $\gamma_i$「不可分割」而附加的成本——不只要為 $\gamma_i$ 使用掉的稀缺產能付費，還要為它必須以整數量出現這件事，付出額外代價。

這帶出**第三個差異（C）：IP 裡的 free good（正 slack），不保證 Gomory-Baumol 估價一定是零。**（跟差異 A 相似，但這次的成因更接近一種退化現象：這個差異其實沒有初看起來那麼嚴重，因為類似的非唯一性，在有 degeneracy 的 LP 問題裡也會發生，只是程度輕微得多。）

**實務上真正被使用的（不完美的）折衷方法**有兩種：第一，直接沿用 branch and bound 搜尋樹中、給出最佳整數解的那個節點所對應的 LP 子問題的經濟資訊。這個做法的缺點跟前面討論的困難類似：整數變數應該只能以離散量變動，而這種經濟資訊反映的卻是連續、邊際式的變化；此外，某些（尤其是 0-1）整數變數在搜尋樹過程中早已被固定在某個界限上，根本無法評估任何變動對它們的影響。第二種變化版：把所有整數變數**固定**在它們的最佳值，只針對剩下的連續部分做敏感度分析。這個做法有一定的道理，因為主要的操作決策（整數變數所代表的）已經被接受，我們真正關心的，只是在既定操作模式**之內**、邊際變化帶來的影響。實務上「必須」為 MIP 模型的限制式賦予估價的一個例子，是 [[case-tariff-rates]] 問題——不同電價費率之間隱含地為模型的限制式賦予了估價。

儘管一般情況下困難重重，仍然有辦法透過巧妙的**改寫**，從 IP 模型取得有用的經濟資訊（Williams, 1981 討論過這點）。下面用一個結合 10.2 節「shared fixed cost」概念的完整例子示範。

**Example 10.12（Rhys, 1970：資本成本分攤問題）。**

在圖 10.3 的網路中，節點代表需要投入資金的資本設施，弧代表能創造營收的活動；要進行任何一條弧（活動），必須同時使用該弧兩端節點所代表的資源——例如節點 D 的資本成本，該怎麼在連到 D 的弧 AD、BD、CD、DE 之間公平分攤？（可以把節點想像成車站，弧想像成連接車站的鐵路線。）

先考慮一個較簡單的子問題：決定要保留哪些節點（車站），讓整個網路（鐵路系統）盡可能獲利——切掉一個節點，就必須連帶切掉所有通往它的弧（線路）。這可以直接formulation 成一個 IP 問題，用以下 0-1 變數（$i,j$ 為 A、B、C、D、E）：

$$\delta_i=\begin{cases}1&\text{節點 } i \text{ 保留}\\0&\text{節點 } i \text{ 被切除}\end{cases}\qquad \delta_{ij}=\begin{cases}1&\text{弧 } (ij) \text{ 保留}\\0&\text{弧 } (ij) \text{ 被切除}\end{cases}$$

目標函數（極大化）：

$$-5\delta_A-4\delta_B-8\delta_C-8\delta_D-4\delta_E+7\delta_{AB}+3\delta_{AC}+3\delta_{AD}+8\delta_{BD}+4\delta_{CD}+\delta_{DE}+2\delta_{CE}. \tag{10.93}$$

限制條件：某些弧的存在需要對應的節點也存在，$\delta_{ij}=1\to\delta_i=1,\delta_j=1$（10.94）。跟 10.1 節討論過的一樣，這個邏輯條件有兩種寫法：

**壞的（單一限制式）formulation**：

$$-\delta_i-\delta_j+2\delta_{ij}\le 0. \tag{10.95}$$

**好的（拆成兩條）formulation**：

$$-\delta_i+\delta_{ij}\le 0,\qquad -\delta_j+\delta_{ij}\le 0. \tag{10.96}$$

跟 10.1.2 節的邏輯完全一致：拆開的 (10.96) 這個 formulation 具有 **total unimodularity**，可以直接當 LP 問題解，並保證得到整數最佳解！

因為我們現在有的是一個貨真價實的 LP 問題，(10.96) 幾何上恰好就是可行整數點的凸包，於是 shadow price 重新變得性質良好、有明確的經濟意義：$-\delta_i+\delta_{ij}\le0$ 的 shadow price，代表節點 $i$ 的資本成本裡，應該由弧 $(ij)$ 的營收分攤的金額；$-\delta_j+\delta_{ij}\le0$ 的 shadow price 同理對應節點 $j$。這樣一來，我們就找到了一套在弧之間公平分攤節點資本成本的方法：如果某個活動負擔不起分配給它的資本成本，就應該被切除。用圖 10.3 給定的數字，得到的 shadow price 如下表：

| 限制式 | Shadow Price |
| --- | --- |
| $-\delta_A+\delta_{AB}\le0$ | 5 |
| $-\delta_B+\delta_{AB}\le0$ | 2 |
| $-\delta_A+\delta_{AC}\le0$ | 0 |
| $-\delta_C+\delta_{AC}\le0$ | 3 |
| $-\delta_A+\delta_{AD}\le0$ | 0 |
| $-\delta_D+\delta_{AD}\le0$ | 3 |
| $-\delta_B+\delta_{BD}\le0$ | 2 |
| $-\delta_D+\delta_{BD}\le0$ | 6 |
| $-\delta_C+\delta_{CD}\le0$ | 4 |
| $-\delta_D+\delta_{CD}\le0$ | 0 |
| $-\delta_C+\delta_{CE}\le0$ | 0 |
| $-\delta_E+\delta_{CE}\le0$ | 2 |
| $-\delta_D+\delta_{DE}\le0$ | 0 |
| $-\delta_E+\delta_{DE}\le0$ | 1 |

以節點 C 為例：它從 AC 收到 3、從 CD 收到 4、從 CE 收到 0，合計 7，仍不足以覆蓋它自己 8 的資本成本——節點 C 顯然已經不再有存在的價值，必須被切除。對其他節點套用同樣的論證，最後留下圖 10.4 所示的最佳網路（保留 A、B、D 及其間的弧，C、E 皆被切除）。

從 LP 對偶延伸出一個有趣的觀察：換一種方式在弧之間分攤節點的資本成本，並不可能得到一個**更**有利可圖的網路，卻很可能得到一個**更差**的網路——這正是 LP 對偶理論的自然推論。這個例子完整示範了：只要能找到一個恰好給出凸包（在這裡恰好是靠 total unimodularity）的 formulation，IP 問題就能重新變回一個貨真價實的 LP 問題，[[interpreting-lp-solutions]] 那一整套 shadow price 機器便可以原封不動地搬回來使用。

在此之外，一般而言 IP 模型很難像 LP 那樣，得到令人滿意的附屬經濟資訊，這仍然是數學規劃理論裡一塊相當大的空白（更完整的討論見 Williams, 1979, 1997；Appa, 1997 指出，固定 MIP 模型的整數變數之後，剩餘 LP 的結構性對偶關係有時可以被利用；Greenberg, 1998 提供了相關文獻書目）。

## 10.4 敏感度分析與模型的穩定性

### 10.4.1 IP 的敏感度分析

一個理論上乾淨的做法，是把限制式換成代表可行整數點凸包的限制式，然後把模型當 LP 問題，套用 [[interpreting-lp-solutions]] 6.3 節介紹的 objective ranging 與 RHS ranging 程序。對於那些容易改寫出凸包 formulation 的 PIP 模型，這確實是相當直接可行的做法。但對其他模型而言，這並不是一條實用的路——而且它也無法用來做 right-hand side ranging。

對於用 branch and bound 求解的 MIP 模型，可以在給出最佳整數解的那個節點所對應的 LP 子問題上做敏感度分析；或者，把整數變數固定在最佳值，只對連續部分做敏感度分析。這兩種做法，跟 10.3 節從 IP 模型推導經濟資訊時遇到的缺點完全相同——都只是近似、都有各自的盲點。

**唯一真正令人滿意的 IP 敏感度分析方法**，是老老實實地拿改變後的係數重新求解一次模型，再比較前後兩組最佳解。求解這個「重新來一次」的時間，當然應該可以透過利用前一次解的資訊（warm start）來縮短。

### 10.4.2 蓋一個穩定的模型

在 LP 模型裡，隨著右手邊或目標係數連續變化，最佳目標值也會連續變化（[[interpreting-lp-solutions]] 已建立這個性質）。在 IP 模型裡，這件事**未必成立**。下面這個例子清楚示範了問題所在。

**Example 10.13（壞的：預算模型的不穩定行為）。**

$$\text{Maximize}\quad 40\delta_1+35\delta_2+15\delta_3+8\delta_4+9\delta_5$$
$$\text{subject to}\quad 8\delta_1+8\delta_2+5\delta_3+4\delta_4+3\delta_5\le 16, \tag{10.97}$$

$\delta_1,\ldots,\delta_5$ 皆為 0-1 變數。這個模型的最佳解是 $\delta_1=1,\delta_2=1$，目標值 75。但如果把右手邊的 16 稍微調降一點點，最佳解會**突然跳成** $\delta_1=1,\delta_4=1,\delta_5=1$，目標值變成 57——僅僅是預算的極小削減，就造成目標值 18 的斷崖式下跌，最佳解也整個換掉。

最佳目標值顯然不是右手邊係數的連續函數，這在許多實務情境裡並不合理。假設 (10.97) 代表的是一項預算限制，這五個 0-1 變數代表資本投資決策：現實中，預算小幅度的削減，通常不太可能讓我們徹底改變整個投資計畫；比較可能發生的情況，是把預算稍微拉緊一點、多花一點成本去撐住原計畫，或者只把其中一項資本投資稍微削減。如果現實情況確實如此，模型就應該把這種漸進調整的彈性表達出來——現狀的模型 (10.97)，正是這種情境下的一個**壞模型**。

**好的：加入 surplus 變數換取穩定性。** 重新改寫 (10.97)，加入一個連續的（surplus）變數 $u$，並在目標函數裡給它一個成本（假設是 20）：

$$\text{Maximize}\quad 40\delta_1+35\delta_2+15\delta_3+8\delta_4+9\delta_5-20u$$
$$\text{subject to}\quad 8\delta_1+8\delta_2+5\delta_3+4\delta_4+3\delta_5-u\le 16. \tag{10.98}$$

在右手邊為 16 時，最佳解仍然是 $\delta_1=\delta_2=1$，目標值 75。一旦右手邊稍微調降，$u$ 的效果會是「用每單位 20 的代價，把預算補回到 16」——例如右手邊降到 $15\frac12$，$u$ 會變成 $\frac12$，最佳解仍維持 $\delta_1=\delta_2=1$ 不變，目標值平滑地下降 10，變成 65。隨著右手邊繼續下降，目標值會持續平緩下滑，直到右手邊降到 $15\frac1{10}$，此時 $\delta_1=1,\delta_4=1,\delta_5=1$ 這個替代方案才會變成另一個同樣最佳的解。加入這個 surplus 變數的做法，帶來兩個非常值得追求的效果：

1. 最佳目標值變成右手邊係數的**連續函數**。
2. 最佳解的數值不再「突然」跳動——它們變成右手邊係數的「半連續」（semi-continuous）函數。

在某些應用中，也可以同時加入一個連續的 slack 變數 $v$（給它某個成本，例如 8）：

$$\text{Maximize}\quad 40\delta_1+35\delta_2+15\delta_3+8\delta_4+9\delta_5-20u-8v$$
$$\text{subject to}\quad 8\delta_1+8\delta_2+5\delta_3+4\delta_4+3\delta_5-u+v=16. \tag{10.99}$$

這個「用懲罰成本讓限制式可以被違反」的技巧，正是 [[interpreting-lp-solutions]] 6.1 節（模型驗證除錯）與 6.3 節（建立穩定 LP 模型）介紹過的同一套手法——只是這次套用在 IP 模型上，解決的是離散跳動而非單純的 infeasibility。要注意，對於 MIP 模型裡許多純粹**邏輯型**的 0-1 限制式，「花錢買預算」這種解讀往往沒有實際意義，這個技巧只適合套用在真正代表資源或預算的限制式上。有些類別的 MIP 模型，不需要額外改寫就能證明具有這種連續性質，相關討論見 A. C. Williams (1989)。

## 10.5 什麼時候該用、該怎麼用 integer programming

作為前三章的收尾，這裡簡短整理成一份實用指南：

1. 如果一個實際問題具有 [[integer-programming-fundamentals]] 8.2 節描述的那些特徵，就值得考慮用 IP 模型。
2. 在決定動手建 IP 模型之前，先估計模型的潛在規模。如果整數變數的數量超過幾百個，且問題沒有特殊結構，IP 很可能在計算上過於昂貴。
3. 仔細檢視 IP 模型可能具有的結構永遠是值得的：如果模型是 PIP 且具有 total unimodular 結構，直接用 LP 求解，即使涉及數千條限制式與變數也能在合理時間內解出；如果是 PIP 但不具 TU 結構，值得看看能不能像 10.2 節那樣容易地改寫成已知的 TU 結構；對 MIP 模型，或找不到明顯 TU 結構的模型，通常值得盡量收緊對應的 LP 問題；如果模型明顯具有 [[special-integer-programming-structures]] 提到的其他特殊結構，值得去查閱相關文獻與該類問題的計算經驗，估計難度。
4. 在動手建完整規模的模型之前，先建一個小得多的版本做實驗。針對這個小模型，應該嘗試 10.2 節描述的化簡改寫，也應該實驗不同的求解策略（見 [[integer-programming-fundamentals]] 8.3 節）。
5. 如果問題看起來以 IP 模型求解太過困難，在做完上述調查之後，可能需要動用某種**heuristic**（啟發式）方法。作業研究方面存在大量不同的啟發式演算法文獻，超出本書範圍；但對一個明顯困難的問題，即使只是花點時間求出一個不錯（雖然可能不是最佳）的 heuristic 解，也很值得——這個好的解可以拿來當搜尋樹的 cut-off 值，加速後續的 tree search。
6. 建好 IP 模型之後，非常重要的一點是要善用對這個實際問題的知識，配合一套聰明的求解策略——8.3 節簡短提過這點，但這已經超出本書作為建模書的範圍，Forrest et al. (1974) 對此有非常好的完整說明。

最後值得一提：IP 領域的理論與計算進展仍在持續發生，使得越來越大、越來越複雜的模型變得可解。

把一個 IP 模型從「寫得出來」磨到「跑得動」，只是故事的一半。即使我們花了大把力氣做出一個既正確又高效的模型，真正決定它有沒有價值的，是它有沒有真的走進組織、改變決策——這正是下一章 [[mp-implementation-in-practice]] 要談的主題。

## 連結

- [[integer-programming-fundamentals]] — 上一章：IP 適用時機、求解方法、0-1 變數與邏輯條件的基礎，是本章「化簡」與「經濟資訊」討論的起點
- [[special-integer-programming-structures]] — 前一章介紹的特殊結構（set covering/packing、knapsack、TSP 等）本身往往就是「天生 formulation 良好」的範例，可與本章的好壞對比互相印證
- [[interpreting-lp-solutions]] — LP 的敏感度分析與 shadow price，是本章 10.3、10.4 節「IP 版經濟資訊/敏感度分析」全程對照、也全程對比出差異的基準
- [[mp-implementation-in-practice]] — 下一章：模型化簡到能求解只是一半，如何讓它在組織裡真正被採用
