---
type: concept
domain: tech
tags: [optimization, mathematical-programming, calculation-variables, logical-calculations, model-formulation]
sources: [raw/Modeling/(Book)Modelling in Mathematical Programming.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：José Manuel García Sánchez, *Modelling in Mathematical Programming*, Ch.5〈Calculations in a System〉, pp.113–134

## 承接上一章：那些「不該是決策」的變數,該怎麼處理

[[decision-activities]] 花了整章篇幅在教一件事：怎麼從系統的動詞裡挑出真正獨立、未確定值的 decision activities。但過程中我們也一再撞見另一種動作——它看起來也有動詞、也有參與元素，值卻永遠可以從其他變數算出來（賣出量是買進量的一半、罰金是否要付取決於某個條件）。上一章的結論是：這種動作不該被定義成決策活動，而該被定義成 **calculation**。Ch.5 要做的，就是把這一類「calculation」變數講清楚——它們有哪些種類、怎麼定義、以及為什麼要如此謹慎地把它們跟決策變數切割開來。

García Sánchez 在本章開頭就把 calculation 的本質講得很直白：calculation 代表的是「值可以從其他變數（通常是決策變數，有時候是別的 calculation）算出來的變數」。它跟決策活動一樣落在系統的元素上，也一樣帶有型態（continuous、integer、binary），表面上兩者長得很像。但書裡緊接著點出兩者本質上的差異，而這正是全書方法論最重要的主張之一：

> Calculations can sometimes be considered as activities, due to their semantics or their importance in the system, but they will never be of primary decision, since their value will be obtained from the value of other variables. **They always carry constraints that define their meaning, that is, they define the calculation.**

換句話說，decision variable 的角色是「被自由選擇」，calculation variable 的角色是「被定義」。決策變數在模型裡只需要限制式去約束它的可行範圍，但 calculation 變數除了可行範圍之外，還必須有一條（或一組）約束式明確規定它「等於什麼」——這條約束式不是選擇性的裝飾，而是這個變數存在的理由本身。如果建模者誤把一個 calculation 當成決策活動來定義，最危險的後果不是模型「跑得動但比較慢」，而是很可能在潛意識裡跳過了那條「定義它的約束式」，因為決策變數通常不需要這種東西。一旦漏寫，這個變數在數學上會變成完全自由的，求解器可能給出一個語意上前後矛盾的解（例如「賣出量」跟「買進量」毫無關聯）。因此，把 decision variables 與 calculation variables 在方法論上徹底分成兩個範疇，本身就是一種防呆設計：只要你把某個變數歸類成 calculation，你就會被提醒「這裡欠一條定義式」，而不會誤以為它跟其他決策變數一樣可以自由取值。這也是為什麼本書要不厭其煩地把 calculation 獨立成一整章，而不是把它併入決策活動的章節裡輕輕帶過。

書中把 calculation 分成三種類型，各自對應不同的建模動機：

- **Auxiliary calculations**（輔助計算）：值直接等於其他變數的線性函數，用途是讓模型更簡潔好讀，或是強制某個線性組合必須是整數。
- **Logical calculations**（邏輯計算）：值由一個邏輯命題（logical proposition）決定，通常是 binary，用來表達條件式的行動或元素的條件性質。
- **Lower/Upper bound calculations**（上下界計算）：用來計算一組變數的上界或下界，主要服務於 equilibrium 型目標函數（例如 minimax）。

以下依序展開這三種類型。

## Auxiliary Calculations：把重複算式收斂成一個變數

Auxiliary calculation 的定義最單純：它的值直接等於某個線性函數。書裡的第一個例子（Illustration 5.1）是把 $n$ 個供應商的採購量加總成一個變數 $x=x_1+x_2+\dots+x_n$，並用一條約束式 $x=\sum_i x_i$ 定義它。這類 calculation 的存在**不是必要的**——你隨時可以把 $x$ 展開回原本的加總式——它存在的唯一理由是讓後續的限制式或目標函數寫起來更清楚。唯一「必要」使用 auxiliary calculation 的情境，是當你需要強制這個線性組合的結果必須是 integer 值時，此時定義一個 integer 型態的輔助變數就成了唯一手段。

書裡特別花篇幅講解一種極為常見的 auxiliary calculation 樣式，稱為 **auxiliary calculation of value selection**（選擇性輔助計算）：當我們用一組 logical 決策變數（$\alpha_i=1$ 表示選中元素 $i$）搭配一條「只能選一個」的規則（$\sum_i \alpha_i=1$）時，可以定義一個新變數去收集「被選中元素的某個屬性值」：

$$x=\sum_{i=1}^n A_i\alpha_i$$

這個 pattern 可以往兩個方向推廣：一是跨兩個集合的配對選擇（$x=\sum_i\sum_j A_{ij}\alpha_{ij}$，選中的是某一對元素的屬性），二是「對第二個集合的每個元素各自做一次選擇」（$x_j=\sum_i A_i\alpha_{ij}$，$\forall j$），也就是每個 $j$ 都各自選出屬於它的那個 $i$。書中的超市配送案例（Illustration 5.2）示範了第一種用法：每個 supermarket 都要指派到某個 distribution location，而每個 supermarket 與 location 的距離就是透過這種 value selection 的方式取得，再拿去做目標函數的加總最小化。

更進一步的 worker–work center 重新分配案例（Illustration 5.3）則展示了 value selection 可以疊加多層：worker 屬於某個城市，work center 也屬於某個城市，兩者之間的距離要先透過「城市對城市」的距離資料，經過兩層加總選出正確的 $D_{kk'}$，才能得到 $y_i$（worker $i$ 實際移動的距離）。書中同時給出三種版本的同一個模型：**individual 版本**（每個 worker 個別建模）、**grouped 版本**（把相同城市的 worker 合併成一個 collective 元素，決策變數變成「有多少個 worker 從群組 $i$ 被分配到 center $j$」）、以及**簡化版本**（如果城市與城市之間的距離資料可以直接對應到 worker 與 center 的距離屬性，就能省略掉「城市」這個元素，直接把距離內建進 worker–center 的資料表裡）。這三個版本的並列很有教學價值：同一個 auxiliary calculation 的概念，可以隨著元素表的抽象層次（個別 vs collective）而有不同的實作方式，但背後的 value-selection 邏輯完全一致。

## Logical Calculations：從命題邏輯出發

當系統裡的條件變得複雜時（某個行動是否發生取決於別的變數的值、某個元素是否符合某個性質），auxiliary calculation 的線性函數就不夠用了，需要靠邏輯命題來定義變數的值——這就是 logical calculation 的用武之地。書裡認為，沒有 logical calculation 的系統通常很容易建模；一旦系統開始出現條件式的邏輯，複雜度就會顯著上升，因此本節也順勢引入了貫穿全書後續章節的基礎：propositional logic（命題邏輯）。

### 命題與邏輯運算子

書中把邏輯命題（proposition）分成兩類。**Atomic（simple）proposition** 是不能再拆分的單一敘述,在數學規劃裡對應到一條線性等式或不等式，格式是「線性函數 (<,≤,=,≥,>) 數值」，例如 $x_1+x_2+x_3\le100$。任何一個模型的限制式本質上都是一條 atomic proposition，我們強制模型的解必須讓它為真。**Molecular（compound）proposition** 則是由一個或多個 atomic proposition 透過邏輯運算子組合而成，書中列出的運算子包括 negation（¬，NOT）、disjunction（∨，OR）、conjunction（∧或&，AND）、conditional（→，IF...THEN）、biconditional（↔，IF AND ONLY IF）、以及 exclusive disjunction（⊕，EITHER...OR）。

有兩組等價關係在後續定義 calculation 時會不斷用到：

- $\phi\leftrightarrow\psi$ 等價於同時成立 $\phi\to\psi$ 與 $\psi\to\phi$（雙條件式可以拆成兩個單向條件式）
- $\phi\to\psi$ 等價於其 contrapositive（逆反）$\lnot\psi\to\lnot\phi$

這兩組等價之所以重要，是因為 logical calculation 的定義本身幾乎都是用 ↔ 寫成的（「$\beta=1$ 若且唯若條件成立」），而要把這個雙條件式拆成模型可以直接使用的限制式，就要靠第一組等價把它拆成兩個方向；如果某個方向寫起來不順手，還可以用第二組等價換成逆反命題來寫。

### 邏輯計算會在哪些地方冒出來

書裡歸納出三種會需要 logical calculation 的情境,這三種情境其實都能對回上一章 [[decision-activities]] 談過的內容：

1. **作為 conditioned action**：這正是上一章「actions with calculated value」裡「conditioned action」那個子類別的延伸。若條件式行動的值是 binary（要不要付某筆固定罰金），就定義一個 binary logical calculation；若條件式行動的值其實是某個線性函數（罰金是總採購量的某個百分比），為了避免模型出現非線性項，反而要定義一個 **non-binary** 的 logical calculation 去承接那個函數值,而不是用 binary 變數乘上函數這種寫法。
2. **作為 conditioned characteristic of an element**：用來表達「某元素是否符合某個以函數表示的條件」，例如「某供應商是否被採用」「某客戶是否買了超過 100 單位」。這種情況下 calculation 幾乎都是 binary,之後常常被拿去做其他限制式或目標函數裡的計數與加總。
3. **作為 compound proposition 建模過程中的中繼變數**：當我們要把一個複合命題轉成模型限制式時，經常需要先定義一個 binary 變數去收集某個 atomic proposition 的真偽值，再用這個變數去組合成最終的複合命題。

書中用一個「向四家供應商採購」的完整例子（Illustration 5.7）把這三種情境一次串起來示範：同一個系統裡，「超過 100 單位要付 50 元罰金」定義了一個 binary logical calculation（$\beta_1$，情境 1 的 determined-value 子類）；「買滿 1000 單位享 2% 折扣」既示範了 binary 版本、也示範了為了避免非線性而改用 non-binary 版本（情境 1 的 conditional-linear-value 子類，直接讓變數 $y_2$ 承接 $0.02\sum x_i$ 這個值）；「使用的供應商數必須等於 2」定義了「該供應商是否被使用」的 binary calculation（情境 2）；「至少要有一個供應商採購超過 50 單位」則定義了另一個條件性質的 binary calculation，直接被拿進目標函數做加總。這個例子的價值在於：同一組決策變數 $x_1,\dots,x_4$，隨著 specification 的敘述方式不同，會衍生出好幾個各自獨立、各自有明確定義約束式的 calculation 變數，彼此互不干擾。

### 化簡 Logical Calculation 的定義

Ch.5 另一個很實用的技巧，是**並非每次都需要把 binary calculation 的兩個真值（1 與 0）都完整定義出來**。標準做法是用 ↔ 把兩個方向都寫出來（$\beta_1=1 \text{ IFF } \sum x_i>100$，拆成「若 $\sum x_i>100$ 則 $\beta_1=1$」與「若 $\sum x_i\le100$ 則 $\beta_1=0$」兩條）,但書裡指出，如果這個變數在目標函數裡**只帶有成本、沒有收益**（例如 $\beta_1$ 只會在目標函數裡增加一筆罰金），那麼求解器本來就沒有誘因把它硬設成 1（除非約束式逼它），因此「若 $\sum x_i\le100$ 則 $\beta_1=0$」這個方向其實可以省略不寫——省略之後模型依然正確，只是最佳解不會主動幫你把 $\beta_1$ 設成 0（但反正也沒有必要,因為目標函數本身就會迴避付罰金)。

另一種可以化簡的情況，是當某條 specification 本身已經保證了「至少會有一個變數為真」的邏輯（例如 $\sum_i\beta_i\ge1$，Illustration 5.8 的賣貨給 10 個客戶案例），此時只需要定義「什麼條件下 $\beta_i$ 必須是 0」（$x_i\le100\Rightarrow\beta_i=0$），不需要再定義「什麼條件下 $\beta_i$ 必須是 1」——因為既然已經有別的限制式保證至少一個 $\beta_i=1$，多定義的那個方向只是重複資訊。書裡也提醒了這個技巧的代價：化簡後的變數不再精確對應到原本語意上「$x_i>100$」的真正條件（可能有 $\beta_i=0$ 的客戶其實也買了超過 100 單位，只是沒被特別標出來），只是能保證整體 specification 的要求被滿足。書中用符號 $\text{Ref. } S_V$ 標記所有用了這種化簡手法的地方，提醒讀者這類變數的真值不能拿去做其他精確用途。

## Lower/Upper Bound Calculations：抓出一組變數的極值

第三種 calculation 專門用來取得一組變數 $x_i\ (i=1\dots n)$ 的上界或下界，定義方式非常直接：

$$x_{UP}: \forall i,\ x_i\le x_{UP} \qquad x_{LOW}: \forall i,\ x_i\ge x_{LOW}$$

這種 calculation 的主要用途，是 **equilibrium 型目標函數**——當你要「讓最小值盡量大」（$\max\ x_{LOW}$）、「讓最大值盡量小」（$\min\ x_{UP}$）、或「讓一組變數的極差盡量小」（$\min\ x_{UP}-x_{LOW}$）時，若不先定義這兩個 bound 變數，就必須用邏輯計算去枚舉整組變數兩兩比較，徒增變數與限制式的數量，效率遠不如直接用 bound calculation。

書裡也順道展示了 bound calculation 一個很巧的額外用途：取得連續變數的整數部分。若 $x$ 是連續變數，想取它的下取整（floor，即 $\lfloor x\rfloor$），可以定義一個 integer 的下界變數 $x_{LOW}$，加上 $x_{LOW}\ge x-(1-\xi)$（$\xi$ 為無窮小量），逼迫 $x_{LOW}$ 必須是不超過 $x$ 且最接近的整數；要取上取整（ceil）則用對稱的上界寫法。

### 只對「有條件參與」的變數取界

當 bound calculation 要套用的對象不是全部變數，而是「只有滿足某條件的變數才要納入比較」時，就必須用邏輯命題來限定計算範圍，而不能直接對所有變數取界——否則沒被選中、值為 0（或無意義）的變數會錯誤地拉低下界或拉高上界。書中的飛行員排班案例（Illustration 5.9）示範了這個陷阱：每個 pilot 可能被指派多趟 double flight，要計算每個 pilot 當天最早開始時間與最晚結束時間（進而限制單日工時不得超過 12 小時），如果直接對所有 flight 的輔助時間變數取下界，會把「沒有指派給這個 pilot 的班次」也算進去，導致下界被錯誤地拉到 0。正確做法是只對 $\alpha_{ij}=1$（即真的被指派給該 pilot 的 flight）的那些 pair 取界：

$$\forall j,\forall i:\ \text{IF } \alpha_{ij}=1 \text{ THEN } x_j^{INF}\le x_{ij}$$

這個例子同時也呼應了 [[decision-activities]] 裡「Rules of Participation」第 5 條的精神——凡是參與條件不確定的關係，都要靠邏輯命題（而不是硬性的線性約束）來限定範圍。

## 為什麼這個區分是全書的核心主張

讀到這裡，值得把整章的邏輯串起來看一次：Ch.4 教我們怎麼辨認「真正未確定值、獨立的」決策活動；Ch.5 則接手處理所有「值可以被算出來」的變數，並進一步把它們分成 auxiliary（線性直接定義）、logical（命題邏輯定義）、bound（極值定義）三種。這個三分法不是為了分類而分類——它的實際效果，是強迫建模者在定義任何一個非決策變數時，都同時寫下「定義它的那條約束式」，而不會誤用決策變數那種「先宣告、之後靠其他限制式慢慢收斂可行域」的隨性態度。這正是本書方法論想要達成的紀律：**先想清楚一個變數的角色是「被選擇」還是「被定義」，模型出錯的機率就會大幅下降**——因為絕大多數的建模錯誤，追根究底都是把這兩種角色搞混所造成的。

## 連結

- [[decision-activities]] — 上一章：怎麼辨認真正未確定值的決策活動，以及「actions with calculated value」如何預示了本章三種 calculation 的存在
- [[specification-types]] — 下一章：本章定義 logical calculation 用到的命題邏輯（atomic/compound proposition、各種運算子），會在該章被正式收編進 specification 的分類體系中延伸使用
