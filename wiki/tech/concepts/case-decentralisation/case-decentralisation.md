---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, quadratic-assignment-problem, linearization, facility-location, case-study]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.12〈The Problems〉§12.10, Ch.13〈Formulation and Discussion of Problems〉§13.10, Ch.14〈Solutions to Problems〉§14.10, pp.265, 317–319, 361

## 情境：把部門搬出倫敦，省下的錢夠不夠付溝通成本？

一間大公司想把部分部門搬出倫敦——理由很現實：郊區房租便宜、政府有搬遷獎勵、招募人才也容易些，這些好處都已經被估算成具體金額。公司有五個部門（A、B、C、D、E），可以選擇留在倫敦，或搬去布里斯托（Bristol）、布萊頓（Brighton）；同時規定倫敦、布里斯托、布萊頓這三個城市，每個城市最多容納三個部門。

問題是，部門之間需要互相溝通協作，而搬遷會讓部門散落在不同城市，跨城市溝通比同城溝通貴。溝通成本的結構是「兩個部門之間的溝通量 $\times$ 溝通兩地之間的單位成本」——也就是說，成本不是取決於單一部門搬到哪，而是取決於**每一對**互相溝通的部門，分別被安排到哪兩個城市。這正是問題的困難所在：你不能孤立地決定「A 部門該去哪」，因為 A 的最佳位置取決於它常溝通的 B、C 在哪，而 B、C 的最佳位置又反過來取決於 A 在哪。

公司該把每個部門放在哪個城市，才能讓「搬遷帶來的好處」減去「增加的溝通成本」淨值最大？

## 這題示範的建模技巧：把二次項拆解成 0-1 變數的乘積

這一題的原型是**二次指派問題**（quadratic assignment problem, QAP）的簡化版本，題目本身也直接點名這是 Beale 與 Tomlin（1972）處理過的真實案例。QAP 之所以難，是因為目標函數裡有「兩個指派決策相乘」的二次項：如果你直接寫 $\delta_{ij}\delta_{kl}$（部門 $i$ 在城市 $j$ 且部門 $k$ 在城市 $l$ 的乘積）當作目標函數的一部分，這就不再是線性規劃，一般的 LP/IP 求解器處理不了。

Williams 採用的解法，是這本書裡反覆出現的一個核心技巧：**引入新的 0-1 變數來代表兩個 0-1 變數的乘積**，把二次項「線性化」。這個手法在 [[integer-programming-fundamentals]] 談 0-1 變數與邏輯條件時就已經鋪陳過，而 QAP 本身則是 [[special-integer-programming-structures]] 列舉的經典組合最佳化結構之一——本案例可以說是把那套抽象技巧，套用在一個具體、真實的企業決策問題上的示範。

## 建模過程：用線性約束綁住乘積變數

**決策變數**：
- $\delta_{ij}$：0-1 變數，若部門 $i$（$i=$A,B,C,D,E）被安排在城市 $j$（$j=$L 倫敦、S 布里斯托、G 布萊頓）則為 1，否則為 0。共 15 個這樣的變數。
- $\gamma_{ijkl}$：0-1 變數，若 $\delta_{ij}=1$ 且 $\delta_{kl}=1$ 同時成立則為 1，否則為 0。$\gamma_{ijkl}$ 只在 $i<k$ 且部門 $i$、$k$ 之間有溝通量（$C_{ik}\neq0$）時才需要定義，共 54 個。

**限制式**分四組：

1. 每個部門恰好落在一個城市：$\sum_j \delta_{ij} = 1$（對每個 $i$），共 5 條。這組限制式的結構其實就是一組 special ordered set of type 1（SOS1）。
2. 每個城市最多容納三個部門：$\sum_i \delta_{ij} \le 3$（對每個 $j$），共 3 條。
3. 為了讓 $\gamma_{ijkl}$ 正確代表「$\delta_{ij}$ 與 $\delta_{kl}$ 同時為 1」，需要兩個方向的邏輯條件都被線性約束綁住。第一個方向是「$\gamma_{ijkl}=1$ 蘊含 $\delta_{ij}=1$ 且 $\delta_{kl}=1$」，用 $\gamma_{ijkl} - \delta_{ij} \le 0$ 與 $\gamma_{ijkl} - \delta_{kl} \le 0$ 達成（共 108 條）——這保證只要 $\delta_{ij}$、$\delta_{kl}$ 有任一個是 0，$\gamma_{ijkl}$ 就被迫等於 0。
4. 第二個方向是「$\delta_{ij}=1$ 且 $\delta_{kl}=1$ 蘊含 $\gamma_{ijkl}=1$」，用 $\delta_{ij}+\delta_{kl}-\gamma_{ijkl} \le 1$ 達成（共 54 條）——這保證只要兩者都是 1，$\gamma_{ijkl}$ 就必須被推到 1（因為目標函數是在追求 $\gamma_{ijkl}=1$ 帶來的懲罰，求解器不會平白無故把它設成 1，需要這條限制式反過來逼它）。

整個模型合計 162 條限制式、69 個全部都是 0-1 的變數。

**目標函數**是最小化「搬遷淨成本」：

$$\text{minimize} \quad -\sum_{i,j} B_{ij}\delta_{ij} + \sum_{i,j,k,l:\,k>i} C_{ik} D_{jl} \gamma_{ijkl}$$

其中 $B_{ij}$ 是部門 $i$ 搬到城市 $j$ 的效益（留在倫敦則 $B_{ij}=0$），$C_{ik}$、$D_{jl}$ 分別是部門間溝通量與城市間單位溝通成本，兩者相乘、再乘上 $\gamma_{ijkl}$，就還原出「部門 $i$、$k$ 分別在城市 $j$、$l$」時的實際溝通成本。書中也提到，Beale 與 Tomlin 原本的作法是先用更精簡的方式建模（先不展開所有限制式），因為完整展開會讓 LP relaxation 比實際需要的更鬆散（less constrained），之後才視情況擴增限制式並搭配特定的分支策略（branching strategy）——這是一個「模型精簡度」與「求解效率」互相權衡的實務提醒。

## 解答與洞見：分散未必只是為了省錢，也可能讓溝通更便宜

最終最適解是：部門 A、D 留在布里斯托，部門 B、C、E 搬到布萊頓——換句話說，倫敦最後一個部門都不留。這個安排帶來每年 £80,000 的搬遷效益，但也產生 £65,100 的溝通成本，淨效益是每年 £14,900。

真正有意思的洞見藏在一個容易被忽略的細節裡：如果五個部門全部留在倫敦不動，溝通成本反而會是 £78,000——比搬遷後的 £65,100 還要高。也就是說，搬離倫敦不只是為了拿到搬遷補貼、省房租，連溝通成本本身都因此下降了。回頭看題目給的城市間單位溝通成本表就能理解原因：倫敦對倫敦的單位溝通成本是 10，而布里斯托對布里斯托、布萊頓對布萊頓的同城成本都只要 5——同樣是「同城溝通」，倫敦的基礎成本結構就是比郊區貴。這打破了一個直覺上的假設（「大家都待在同一個城市，溝通一定最便宜」），提醒建模者：真實資料裡的成本結構常常違反直覺，不能靠拍腦袋猜測，必須讓模型把所有排列組合真的算過一輪。

這個案例也示範了一個純 0-1 IP 模型即使規模不大（69 個二元變數），只要目標函數帶有「決策之間交互作用」的本質（這裡是任兩個部門的溝通關係），限制式的數量與邏輯複雜度就會迅速膨脹——這正是為什麼像 QAP 這樣的問題，即便維度不算誇張，仍然是組合最佳化裡出了名難解的一類。

## 連結

- [[mp-implementation-in-practice]] — MP 模型導入企業決策流程，呼應本案例作為真實企業搬遷決策工具的定位
- [[special-integer-programming-structures]] — 二次指派問題（QAP）在組合最佳化結構分類中的位置
- [[integer-programming-fundamentals]] — 0-1 變數乘積線性化的一般技巧來源
- [[case-economic-planning]] — 同屬 Part II/III/IV 相鄰案例，同樣涉及跨部門/跨產業的資源配置抉擇
