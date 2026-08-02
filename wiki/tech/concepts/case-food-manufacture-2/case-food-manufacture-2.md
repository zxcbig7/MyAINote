---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, blending-problem, semi-continuous-variables, case-study]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.12〈The problems〉§12.2, p.255
> 📖 來源：同書 Ch.13〈Formulation and discussion of problems〉§13.2, pp.299–300
> 📖 來源：同書 Ch.14〈Solutions to problems〉§14.2, pp.349–350

## 情境

Food Manufacture 2 直接接續 [[case-food-manufacture-1]]:同一家工廠、同一批五種原料油(VEG 1、VEG 2、OIL 1、OIL 2、OIL 3)、同樣的六個月調配與購買問題,但這次額外加上三條「業務端」提出的限制:

1. 每個月配方裡使用的原料油種類不能超過三種。
2. 如果某種油在某個月被使用,用量至少要 20 噸(不能只加一點點意思意思)。
3. 如果 VEG 1 或 VEG 2 這兩種植物油任一種被用了,那個月就必須同時使用 OIL 3。

這三條規則在食品調配業界其實很常見:配方種類太多會拉高生產與品管複雜度(條件 1),用量太少不符合經濟效益、也可能只是四捨五入誤差(條件 2),某些油品搭配則是配方口感或穩定性的經驗法則(條件 3)。題目要求把這三條規則加進 Food Manufacture 1 的模型裡,重新求出新的最佳解。

## 這題示範的建模技巧

Food Manufacture 1 是純 LP,而這三條新規則沒有一條可以用傳統線性規劃直接表達——它們都是「有沒有用」這種開關式的邏輯條件,而不是連續數量上的限制。這正是這本書用來示範**如何用 0-1 整數變數把邏輯條件(logical condition)嵌入 LP 模型**的教材案例,對應方法論見 [[integer-programming-fundamentals]] 裡「離散變數用法」與「邏輯條件與 0-1 變數」的討論。條件 2 這種「若使用則至少要達到某個下限」的模式,在 OR 文獻裡有個專有名稱叫 **semi-continuous variable**(半連續變數):一個變數要嘛是 0,要嘛落在 [下限, 上限] 這個區間,中間的灰色地帶(0 到下限之間)是不允許的。

## 建模過程

解法的核心手法是:對每一個「使用量」變數,配一個對應的 0-1 指示變數(indicator variable),表示這個原料油這個月「有沒有」被用。以 1 月的 UVEG 11(1 月使用的 VEG 1 數量)為例,配一個 0-1 變數 δ₁(書裡記作 DVEG 11),兩者用兩條限制式綁在一起:

```
x₁ - 200δ₁ ≤ 0
x₁ -  20δ₁ ≥ 0
```

因為 δ₁ 只能是 0 或 1,這兩條式子合起來的效果正是「半連續」:δ₁=0 時 x₁ 被鎖死在 0;δ₁=1 時 x₁ 必須落在 [20, 200] 之間(200 是植物油的精煉產能上限)。同樣的手法對其餘四種油、六個月都重複一次,總共引入 30 個 0-1 變數(δ₁…δ₅ 每種油、每月各一個)。這樣一來,**條件 2 已經被這組配對限制式自動滿足了**,不需要再額外寫任何式子。

條件 1(每月最多三種油)直接用 δ 變數的和來表達,每個月一條:

```
δ₁ + δ₂ + δ₃ + δ₄ + δ₅ ≤ 3
```

條件 3(VEG 1 或 VEG 2 用了就要用 OIL 3,δ₅ 對應 OIL 3)則有兩種寫法可選。第一種是單一限制式:

```
δ₁ + δ₂ - 2δ₅ ≤ 0
```

第二種是拆成一對限制式:

```
δ₁ - δ₅ ≤ 0
δ₂ - δ₅ ≤ 0
```

這兩種寫法在整數解的意義上完全等價,但書裡明確指出**拆開的那一對限制式在連續鬆弛(continuous relaxation)下比較「緊」(tighter)**——也就是說,把整數限制暫時放鬆成 0≤δ≤1 之後,拆開版本圍出的可行域比單一版本更貼近真正的整數可行域,能讓 branch and bound 更早剪枝,加速求解。這是 [[integer-programming-refinement]] 裡「好壞 formulation」與「simplify」討論的一個具體示範:同樣邏輯意義的限制式,寫法不同,對求解效率影響很大。

整個模型因此新增了 30 個 0-1 整數變數、60 條連結限制式(每個 δ 配兩條)、6 條條件 1 的限制式,加上條件 3(用拆開版本)的 12 條限制式,合計 78 條額外限制式,外加所有 30 個整數變數都要設上界 1。書裡還補了一個實務技巧:在 branch and bound 的搜尋樹裡,為變數指定分支優先順序(priority order)通常有幫助——這裡建議把六個月份的 δ₅(OIL 3 指示變數)設為優先分支變數,因為條件 3 把其他變數的可行性都掛在 δ₅ 身上,先固定 δ₅ 能更快讓其餘變數的分支收斂。

## 解答與洞見

書裡直言「這個模型比較難解」(comparatively hard to solve)。最佳解(Table 14.2)顯示新利潤是 **£100,279**,明顯低於 Food Manufacture 1 的 £107,843——這完全合理,因為新增的三條業務規則只會讓可行域變小、不會變大,利潤只能持平或下降,不可能上升。同樣存在多組同樣好的交替最佳解。真正值得記住的數字是求解過程:這組解在 branch and bound 搜尋到第 645 個節點時就已經找到,但要「證明」它就是全域最佳解,總共檢查了 2007 個節點。

這組節點數字是一個很好的教材:同一個問題,LP 版本(Food Manufacture 1)幾乎是秒解,但只不過加了 30 個 0-1 變數之後,雖然實際找到最佳解的過程不算太久,「證明最佳性」卻要多探索三倍以上的節點——這正是 [[integer-programming-fundamentals]] 反覆強調的:IP 的困難不在於「找到一個好解」,而在於窮舉式的搜尋要花很大力氣才能排除「還有沒有更好的解」這個疑慮。也因此,像上一段提到的緊限制式(tighter formulation)、以及合理的分支優先順序,才會在實務上如此重要——它們直接決定了搜尋樹的大小。

## 連結

- [[case-food-manufacture-1]]
- [[integer-programming-fundamentals]]
- [[integer-programming-refinement]]
- [[structured-lp-models]]
