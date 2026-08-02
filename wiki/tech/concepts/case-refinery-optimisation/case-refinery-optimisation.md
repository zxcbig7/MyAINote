---
type: concept
domain: tech
tags: [optimization, mathematical-programming, linear-programming, process-industry, blending, williams-casebook]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed.
> Part II 問題敘述 §12.6〈Refinery optimisation〉, pp.258–260
> Part III 建模過程 §13.6〈Refinery optimization〉, pp.306–310
> Part IV 解答 §14.6〈Refinery optimization〉, pp.356–357

## 情境：一座煉油廠，四道工序，一張利潤表

石油工業是 linear programming 最大的產業用戶之一，實務上一座煉油廠的模型動輒數千條限制式，還可能好幾座煉油廠彼此串接成一個更大的 structured model。Williams 在本書給的版本刻意縮小規模，但保留了完整的製程邏輯，目的是讓讀者看清楚：一條原油從進廠到變成汽油、噴射燃料賣出去，中間到底發生了什麼事，而這整條路徑又要怎麼變成一組線性限制式。

情境本身是這樣的：煉油廠採購兩種原油（crude 1、crude 2），把它們送進四道依序相連的工序——**distillation（蒸餾）**、**reforming（重組）**、**cracking（裂解）**、**blending（調和）**——最後產出可以賣錢的成品油。

蒸餾是第一關：把每桶原油依沸點拆解成六種餾分——light naphtha、medium naphtha、heavy naphtha、light oil、heavy oil、residuum。兩種原油拆出來的餾分比例不同（crude 2 拆出的 residuum 比例略低、light oil 比例也較低），而且拆解會有耗損：crude 1 的六個餾分比例加總是 0.95，crude 2 是 0.97，代表蒸餾過程本身就會蒸發或損耗掉一小部分原油，這是題目特別註記的細節。

三種 naphtha 可以直接拿去調和汽油，也可以先送進 **reforming**：把辛烷值較低的 naphtha（light 90、medium 80、heavy 70）轉成辛烷值高達 115 的 reformed gasoline，代價是產出的桶數會打折（light naphtha 一桶只變回 0.6 桶 reformed gasoline，heavy naphtha 甚至只剩 0.45 桶）。light oil 與 heavy oil 則面臨另一個岔路：直接拿去調和 jet fuel／fuel oil，或是送進 **catalytic cracking**，裂解成 cracked oil 與辛烷值 105 的 cracked gasoline。residuum 也有兩條路——變成 lube-oil，或送去調和 jet fuel 與 fuel oil。

走完前三道工序，所有的中間產物最後都匯流到 **blending**：premium 與 regular 兩種汽油要滿足辛烷值下限（94／84）、jet fuel 要滿足蒸氣壓上限、fuel oil 則被要求用固定比例 10:4:3:1 調和 light oil、heavy oil、cracked oil、residuum。再加上原油供應量、蒸餾/重組/裂解的產能上限、lube-oil 的產銷區間、premium 至少是 regular 四成的市場限制，題目問的就是一句話：**該怎麼安排這一整條生產鏈，才能讓總利潤最大？**

## 這題示範的建模技巧：把一連串物理工序串成一張 LP

Refinery optimisation 之所以是這套案例庫裡經典中的經典，是因為它示範了 **structured multi-stage process LP** 最核心的技巧：不是為每個工序各建一個模型再拼起來，而是讓「上一道工序的產出」直接變成「下一道工序的輸入變數」，靠一連串 **material balance（物料平衡）** 限制式把整條生產鏈串成一個變數共享的線性系統。這正是 [[structured-lp-models]] 討論的「多工廠、多產品、多階段模型」在真實產業中的具體樣貌——蒸餾、重組、裂解、調和不是四個獨立問題，而是同一個決策變數網絡裡的四層節點。

同時，這題也是 [[lp-applications-and-networks]] 提到的「產業應用」裡最常被引用的教科書級案例：石油產業幾乎是 LP 在企業界最早、也最成熟的應用領域（書中提及 Manne 1956 的先驅工作），值得作為「LP 走出教室、進入真實工廠」的第一個範例來讀。

## 建模過程：36 個變數，29 條限制式

Williams 在這題示範了一個很實用的建模習慣：用 **mnemonic 名稱**（CRA、LN、RG、PMF……）取代 $x_1, x_2, \dots$ 這種抽象下標，讓每個變數一看名字就知道代表什麼桶裝物料。全模型共有 36 個這樣的變數，從兩種原油（CRA、CRB）、六種蒸餾餾分（LN、MN、HN、LO、HO、R）、reforming 與 cracking 的中間產物（RG、CO、CG），一路到五種依用途拆分的中間變數（例如 LNPMF 表示「用於 premium 汽油的 light naphtha 桶數」），最後匯總成五個成品變數：PMF（premium 汽油）、RMF（regular 汽油）、JF（jet fuel）、FO（fuel oil）、LBO（lube-oil）。

限制式可以分成四類，這個分類本身就是一套值得記住的通用寫法：

**Availabilities（供應上限）**：兩個原油的簡單上界，CRA ≤ 20000、CRB ≤ 30000（單位皆為桶/日）。

**Capacities（產能上限）**：蒸餾產能 CRA + CRB ≤ 45000；重組產能 LNRG + MNRG + HNRG ≤ 10000；裂解產能 LOCGO + HOCGO ≤ 8000；外加 lube-oil 產量必須落在 500–1000 之間的上下界。

**Continuities（物料平衡）**：這是整個模型的骨幹，每一個「中間產物」都要有一條等式，把它的產出量用上游投入表示出來。例如 $-0.1\,\text{CRA} - 0.15\,\text{CRB} + \text{LN} = 0$ 定義了 light naphtha 的產量；$-0.6\,\text{LNRG} - 0.52\,\text{MNRG} - 0.45\,\text{HNRG} + \text{RG} = 0$ 定義了 reformed gasoline 的產量。同一種寫法一路套用到 cracked oil、cracked gasoline、lube-oil，甚至每一種中間物料「有多少被用到哪個下游用途」也都要用一條等式收斂（例如 $-\text{LN} + \text{LNRG} + \text{LNPMF} + \text{LNRMF} = 0$，保證 light naphtha 沒有憑空消失或多出來）。

其中 fuel oil 的處理特別值得注意：由於 fuel oil 的四種成分必須維持固定比例 10:4:3:1，書裡並沒有另外引入一個「fuel oil 裡光油佔比」的變數，而是直接把光油用量的係數設成 $10/18 \approx 0.55$，寫成 $-\text{LO} + \text{LOCGO} + \text{LOJF} + 0.55\,\text{FO} = 0$。這其實是把「調和 fuel oil」整個當成一個**固定配方的活動（activity）**，而不是拆成獨立的比例決策——這正呼應了 [[building-lp-models]] 談到的 modal formulation 概念：當一個製程只有一種運轉模式、配方比例是物理上固定死的，就不需要為比例本身另設變數，直接把配方內嵌進係數裡即可，模型反而更簡潔也更不容易寫錯。

**Qualities（品質限制）**：辛烷值與蒸氣壓都假設**線性調和**（blend linearly by volume），所以可以直接寫成加權和的限制式，例如 premium 汽油辛烷值下限 94 寫成 $-90\,\text{LNPMF} - 80\,\text{MNPMF} - 70\,\text{HNPMF} - 115\,\text{RGPMF} - 105\,\text{CGPMF} + 94\,\text{PMF} \le 0$。這個「線性調和」假設是整個煉油模型能維持線性、不需要 nonlinear programming 的關鍵前提。

最後，premium 至少是 regular 四成的市場限制寫成 $\text{PMF} - 0.4\,\text{RMF} \ge 0$；整個模型共有 29 條限制式，外加三個變數（CRA、CRB、LBO）帶有簡單上下界。目標函數只涉及五個最終產品，以每桶利潤（換算成英鎊）加總：

$$7\,\text{PMF} + 6\,\text{RMF} + 4\,\text{JF} + 3.5\,\text{FO} + 1.5\,\text{LBO}$$

## 解答與洞見：把利潤留給附加價值最高的路徑

最佳解的總利潤是 £211,365，而數字本身講的故事，比目標值更有教學意義。

首先看原油用量：CRB（crude 2）用滿 30000 桶上限，CRA（crude 1）只用了 15000 桶，兩者加總剛好等於蒸餾產能上限 45000——也就是說，**真正卡住產量的是蒸餾產能，不是原油供應量本身**：crude 2 被優先用滿，crude 1 只補上蒸餾產能剩下的空間。這是讀 LP 解答時該養成的習慣：先看哪些限制式是 tight（等式成立）的，往往比看目標值更能理解模型在做什麼決策（這也是 [[interpreting-lp-solutions]] 談 shadow price 之前，最基本的一步）。

其次看 reforming：LNRG = MNRG = 0，只有 HNRG = 5407（全數重組），意味著模型只把辛烷值最差的 heavy naphtha（70）送去 reforming 拉高辛烷值，辛烷值原本就不差的 light naphtha（90）與 medium naphtha（80）則直接保留去調和汽油。這是一個很直覺、但唯有透過最佳化才會被精確量化的策略：**把加值工序留給最需要它的原料**。

裂解也呈現類似分工：light oil（LO = 4200）全部送進 cracking（LOJF = 0），heavy oil（HO = 8700）則一部分裂解（HOCGO = 3800）、一部分直接調和 jet fuel（HOJF = 4900），兩者加總剛好等於 HO 總量。residuum（R = 5550）也是部分（RLBO = 1000）拿去做 lube-oil，其餘 4550 桶全數用於 jet fuel（RJF = 4550），一滴都沒有流向 fuel oil。

而 **FO = 0**——最佳解完全不生產 fuel oil，儘管它在目標函數裡明明有 3.5 的利潤係數。這正說明了線性規劃「機會成本」的精髓：fuel oil 的獲利能力雖然不是零，但它需要的成分（light oil、heavy oil、cracked oil、residuum）在其他用途（尤其是 jet fuel）上創造的利潤更高，於是模型寧可把這些成分全部導向 jet fuel，一滴都不留給 fuel oil。同樣地，**LBO 剛好卡在下限 500**（而非上限 1000），因為 lube-oil 每桶只值 1.5，遠低於把 residuum 留給 jet fuel 的價值，因此只生產法規／訂單要求的最低量。

最後，PMF = 6818、RMF = 17044，兩者比值恰好是 0.4——premium 至少四成的市場限制**剛好卡在邊界上（binding）**，代表如果能放寬這個行銷限制，總利潤還有進一步提升的空間。這些觀察合起來說明了一件事：讀一個 LP 的解答，不是看目標值多漂亮，而是看「哪裡被卡住、哪裡被完全放棄、哪裡剛好壓線」——這三種訊號分別對應了產能瓶頸、機會成本、以及有價值的邊界限制，是後續學習 duality 與 sensitivity analysis 前，最值得先練成的直覺。

## 連結

- [[structured-lp-models]] — 多工廠/多產品/多階段模型的方法論，本案例的四道工序串接正是其具體實例
- [[lp-applications-and-networks]] — LP 在石油等產業的應用背景
- [[building-lp-models]] — modal formulation（固定配方活動）的概念，用在本案例的 fuel oil 調和限制式
- [[interpreting-lp-solutions]] — 如何從「哪些限制式 binding、哪些變數卡在上下界」讀出模型的經濟意涵
