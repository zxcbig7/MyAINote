---
type: concept
domain: tech
tags: [optimization, mathematical-programming, linear-programming, production-planning, multi-period-planning, case-study]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.12〈The problems〉§12.3, pp.255–256
> 📖 來源：同書 Ch.13〈Formulation and discussion of problems〉§13.3, pp.300–302
> 📖 來源：同書 Ch.14〈Solutions to problems〉§14.3, pp.350–351

## 情境

Factory Planning 1 把場景從食品調配廠換成一間工程工廠,生產七種產品(PROD 1 到 PROD 7),要用四種加工程序:磨床(grinding)、垂直鑽床(vertical drilling)、水平鑽床(horizontal drilling)、鏜孔(boring)與刨床(planing)。工廠裡總共有 4 台磨床、2 台垂直鑽床、3 台水平鑽床、1 台鏜床、1 台刨床。每種產品每單位的利潤貢獻(售價減原料成本)、以及在每種機器上需要的加工時數,書裡都用一張表列出;有些產品不需要某些工序(表中用「-」表示)。

問題的複雜之處在於:未來六個月(1 月到 6 月)裡,某些機器會被排入維修保養(maintenance),期間完全無法使用——例如 1 月有一台磨床要維修、2 月有兩台水平鑽床要維修,依此類推,每個月的機台可用產能都不一樣。此外,每個月每種產品的市場需求上限(marketing limitation)也不同,不能無限生產。工廠允許把做好的產品存起來待日後賣(每單位每月倉儲成本 £0.5,最多存 100 單位),目前沒有庫存,但要求 6 月底每種產品都要留 50 單位庫存。工廠每週工作 6 天、每天兩班各 8 小時,不需考慮加工順序(sequencing)問題,且假設每個月固定 24 個工作日。題目除了要工廠決定何時、生產什麼以達到利潤最大化之外,還要求評估「調漲售價」與「添購新機台」各自的價值——這個延伸問題直接指向 shadow price 的應用。本案例(與後續的 [[case-factory-planning-2]])都取材自已停業的康瓦爾工程公司 Holman Brothers 的真實模型。

## 這題示範的建模技巧

如果說 [[case-food-manufacture-1]] 示範的是「原料調配 + 存貨」的多期模型,Factory Planning 1 示範的則是更典型、更常見的**多期生產排程與產品組合(product mix)問題**:在有限的機台產能與市場需求之間找出每個月的最佳生產量、銷售量與庫存量,對應方法論見 [[structured-lp-models]] 談的多期規劃架構,也呼應 [[building-lp-models]] 對目標函數與限制式類型的分類。

## 建模過程

### 單期模型(只看 1 月)

若不考慮儲存,1 月的模型是一個乾淨的產品組合 LP。令 x₁…x₇ 為七種產品的生產量:

```
Maximize PROFIT = 10x₁ + 6x₂ + 8x₃ + 4x₄ + 11x₅ + 9x₆ + 3x₇
subject to
GR: 0.5x₁ +0.7x₂                +0.3x₅+0.2x₆+0.5x₇ ≤ 1152
VD: 0.1x₁ +0.2x₂        +0.3x₄        +0.6x₆       ≤  768
HD: 0.2x₁        +0.8x₃                            ≤ 1152
BR: 0.05x₁+0.03x₂       +0.07x₄+0.1x₅        +0.08x₇ ≤  384
PL:              0.01x₃        +0.05x₅       +0.05x₇ ≤  384
```

GR、VD、HD、BR、PL 分別代表磨床、垂直鑽床、水平鑽床、鏜孔、刨床的可用工時上限,右手邊的數字就是當月這五種機台扣掉維修後剩下的總產能(小時)。此外每個產品還有當月的市場需求上限(1 月依序是 500、1000、300、300、800、200、100),當作變數的 upper bound。其他月份的單期模型結構完全相同,只是市場上限與機台產能(因維修排程不同)會變。

### 多期模型(完整六個月)

延伸到六個月時,同樣需要把「生產、銷售、庫存」拆成各自的變數。書裡用 MPROD1t(製造)、SPROD1t(銷售)、HPROD1t(持有/庫存)這種命名法,對七種產品、六個月分別定義。三者之間一樣要用平衡式串起來:

```
上月庫存 + 本月製造量 = 本月銷售量 + 本月庫存
```

期初(月0)沒有庫存,期末(月6,即 6 月底)每種產品要留 50 單位。以 PROD 1 為例:

```
MPROD11 - SPROD11 - HPROD11                     = 0
HPROD11 + MPROD12 - SPROD12 - HPROD12           = 0
HPROD12 + MPROD13 - SPROD13 - HPROD13           = 0
HPROD13 + MPROD14 - SPROD14 - HPROD14           = 0
HPROD14 + MPROD15 - SPROD15 - HPROD15           = 0
HPROD15 + MPROD16 - SPROD16                     = 50
```

其餘六種產品各自需要同樣結構的六條限制式。目標函數裡,銷售變數依各產品的單位利潤給係數,持有(庫存)變數給 -0.5 的係數(倉儲成本)。整個模型最終有 126 個變數(42 製造 + 42 銷售 + 42 持有)、72 條限制式(30 條產能限制 + 42 條月度連鎖限制),另外每個月的市場上限與庫存上限(每產品最多存 100)又構成 84 條上界限制。

## 解答與洞見

Part IV 給出的最佳生產/銷售/庫存計畫(Table 14.3)使總利潤達到 **£93,715**。這道題目除了要工廠知道「該生產什麼」,還額外問了「新增機台的價值」與「調漲售價的建議」——這正是 LP 對偶理論裡 **shadow price(影子價格)** 最直接的應用場景,對照 [[interpreting-lp-solutions]] 的敏感度分析討論。書裡給出幾個具體例子:1 月磨床(GR)產能吃緊到滿載,增加一小時磨床產能的邊際價值是 £8.57;2 月水平鑽床(HD)滿載時,一小時的邊際價值只有 £0.625(遠低於磨床,反映水平鑽床產能相對寬鬆);3 月鏜床(BR)的邊際價值高達 £200——但書裡特別提醒,3 月鏜床其實**沒有被用到滿載**(not in use),這個 £200 的數字反映的是「如果強迫多用一小時鏜床,能帶來多大的價值」,是一個指標性的邊際訊號,而不是「目前產能已經滿載、每多一小時值多少錢」的常規解讀——這也呼應 [[interpreting-lp-solutions]] 裡對 shadow price 使用限制的提醒:它只在很小的容量變動範圍內有效,不能無限外推。

這個案例把多期生產規劃的完整套路示範了一遍:先寫清楚單期模型抓住產能與市場限制的結構,再用「製造/銷售/持有」三件套變數把時間維度接起來,最後靠對偶價格回答「值不值得多買一台機器」這種管理層真正關心的問題。它同時也是 [[case-factory-planning-2]] 的基礎版本——下一個案例會把「機台何時維修」這個目前寫死的假設,變成模型自己要決定的變數。

## 連結

- [[case-factory-planning-2]]
- [[structured-lp-models]]
- [[building-lp-models]]
- [[interpreting-lp-solutions]]
