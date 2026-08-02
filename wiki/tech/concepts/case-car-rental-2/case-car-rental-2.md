---
type: concept
domain: tech
tags: [optimization, mathematical-programming, integer-programming, capacity-expansion, logical-constraints, case-study, williams]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.12〈The Problems〉§12.26, p.287；Ch.13〈Formulation and Discussion of Problems〉§13.26, pp.342–343；Ch.14〈Solutions to Problems〉§14.26, p.380

## 情境：解完一個 LP,才知道下一個問題是什麼

[[case-car-rental-1]] 求出的答案,除了「該擁有幾輛車、車該怎麼調度」之外,還附帶了一個意外收穫：敏感度分析顯示 Manchester 與 Birmingham 這兩個維修 depot,在一週七天裡全部滿載,而且它們的 shadow price 高達每輛每天 £617 至 £646——這是一個高到不尋常的數字,直接說明維修產能才是整個租車事業獲利能力的真正瓶頸。Car rental 2 要問的問題,正是從這個發現直接長出來的：既然維修產能這麼值錢,公司該不該花錢擴充它?如果要擴充,該擴充哪一個 depot?擴充到什麼程度?

Williams 給出五個具體的擴充方案,每個方案都有一個「每週固定成本」(這個成本已經把貸款利息攤提在內)：在 Birmingham 擴充 5 輛/天的維修產能,每週固定成本 £18,000;在此基礎上「再」擴充 5 輛/天,每週 £8,000;在 Manchester 擴充 5 輛/天,每週 £20,000;在此基礎上「再」擴充 5 輛/天,每週 £5,000;以及在 Plymouth——這個原本完全沒有維修能力的 depot——從零開始建立 5 輛/天的維修產能,每週 £19,000。這五個選項不是互相獨立的：如果選了「任何一個」,就必須整個採用,不能只做一半;而「再擴充 5 輛」的選項,只有在對應的「先擴充 5 輛」選項也被選中時才能被選;此外,公司最多只願意同時執行三個擴充方案。

這個題目值得細讀的地方,不在於它又示範了一次網路流建模——那件事 Car rental 1 已經做過了——而在於它示範了「當你已經有一個運作良好的 LP 模型時,該怎麼在它上面疊加一層離散的投資決策」,以及這一層決策裡藏著的幾種常見邏輯關係:互斥的「先後順序」(option 2 沒有 option 1 就不能選)、以及「最多選 k 個」的資源限制。

## 這題示範的建模技巧：在既有 LP 上疊加一層「要不要投資」的 0-1 決策

Car rental 1 建立的是一個純網路流 LP,呼應 [[lp-applications-and-networks]] 談的網路模型精神。Car rental 2 沒有推翻或重寫那個模型,而是選擇在它之上「疊加」——引入五個新的 0-1 變數代表五個擴充選項,把每個被選中的選項的固定成本從利潤中扣掉,並且把它對應的維修產能加回到原本的 $rp_{it} \le R_i$ 限制式裡。這是一個很值得學的建模習慣：面對「既有連續模型 + 新的離散投資決策」這種情境,不必從零建一個新模型,而是直接在既有限制式與目標函數上「掛」新的項目與新的限制式,這樣做既省工,也讓兩個模型之間的關係一目了然。

這一層新增的邏輯關係,也正好對應到 [[integer-programming-fundamentals]] 討論的「邏輯條件與 0-1 變數」：「先做 A 才能做 B」是一種蘊含關係(implication),用 $\delta_{B2} \le \delta_{B1}$ 這樣一條簡單的不等式就能表達;「最多選三個」則是一條 cardinality 限制式,把所有 0-1 變數加總、限制在某個上界之下。這兩種寫法在往後遇到「專案選擇」「投資組合」這類問題時會反覆出現,Car rental 2 是它們第一次以完整案例的形式登場。

## 建模過程：五個新變數,寥寥幾條新限制式

Williams 引入五個 0-1 變數：$\delta_{B1}$(Birmingham 擴充 5 輛/天)、$\delta_{B2}$(Birmingham 再擴充 5 輛/天)、$\delta_{M1}$(Manchester 擴充 5 輛/天)、$\delta_{M2}$(Manchester 再擴充 5 輛/天)、$\delta_P$(Plymouth 從零建立 5 輛/天維修產能)。

目標函數只需要多扣掉一項——五個選項各自的每週固定成本：

$$18000\delta_{B1} + 8000\delta_{B2} + 20000\delta_{M1} + 5000\delta_{M2} + 19000\delta_P$$

新增的限制式也只有三條。前兩條是「先後順序」關係,直接翻譯題目裡「沒選 option 1 就不能選 option 2」的規則：

$$\delta_{B1} \ge \delta_{B2}, \qquad \delta_{M1} \ge \delta_{M2}$$

第三條是「最多選三個」的 cardinality 限制:

$$\delta_{B1} + \delta_{B2} + \delta_{M1} + \delta_{M2} + \delta_P \le 3$$

最後,原本 Car rental 1 裡三條維修產能限制式($rp_{it} \le R_i$,分別對應 Manchester、Birmingham、Plymouth)被個別加上對應的擴充量：Birmingham 的限制式加上 $5\delta_{B1}+5\delta_{B2}$、Manchester 加上 $5\delta_{M1}+5\delta_{M2}$、Plymouth 加上 $5\delta_P$。注意 Plymouth 原本完全沒有維修能力,這裡等於是讓一個全新的維修據點,從無到有地成為模型的一部分——這也是為什麼 Plymouth 的選項不需要「先後順序」限制,它是唯一一個「從零開始」的選項。

整個新增的部分,相對於 Car rental 1 的 84 條限制式與 337 個變數而言,只是輕輕一筆:五個新變數、三條新限制式,外加三條既有限制式的微調。

## 解答與洞見：錢該花在哪裡,答案往往比想像中集中

書中的解答是：五個選項裡,只有 Birmingham 的兩個選項(option 1 與 option 2)值得採用,Manchester 與 Plymouth 的擴充都不划算。採用這兩個選項後,公司的車隊規模可以從 624 輛擴大到 895 輛,每週利潤從 £122,398 提升到 £135,511——這是一次顯著的獲利成長,而且求解只花了 5 個 branch and bound 節點,幾乎和求解原本的 LP 一樣輕鬆。

(這裡有一個值得提醒讀者小心查證的地方：書中原文把 Birmingham 擴充後的產能寫成「22 輛/天」,但根據 12.26 節列出的選項,兩個 Birmingham 選項各自增加 5 輛/天,兩者都採用理論上應該是 $20+5+5=30$ 輛/天,而不是 22。這個數字對不上選項本身列出的增量,很可能是原書的一處勘誤;若要親自重現這個模型,建議以選項定義(每個 +5 輛/天)反推驗證,而不要照抄書中這個數字。)

這個案例最重要的教訓,其實不在於「該擴充哪裡」這個具體答案,而在於它示範了敏感度分析如何自然地「餵出」下一個要問的問題——Car rental 1 的 shadow price 分析告訴我們維修產能是瓶頸,Car rental 2 緊接著把「投資是否划算」這個問題,用最小的建模成本(幾個 0-1 變數、幾條邏輯限制式)接到既有模型上,一次解決。這正是 [[interpreting-lp-solutions]] 談敏感度分析時想強調的精神：一個 LP 的解答本身,往往比它的最優值更值得閱讀。

## 連結

- [[case-car-rental-1]] — 本案例延伸的基礎模型,敏感度分析的 shadow price 結果直接催生了這裡的擴充決策問題
- [[lp-applications-and-networks]] — Car rental 2 疊加的仍是 Car rental 1 的網路流骨架,擴充決策只是掛在其上的新增部分
- [[integer-programming-fundamentals]] — 本案例的「先後順序」與「最多選 k 個」限制式,是邏輯條件轉譯為 0-1 變數限制式的典型範例
