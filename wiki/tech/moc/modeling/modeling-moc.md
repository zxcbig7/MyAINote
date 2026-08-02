---
type: moc
domain: tech
tags: [optimization, mathematical-programming, linear-programming, integer-programming, operations-research]
created: 2026-07-29
updated: 2026-07-29
---

# 數學規劃建模 MOC

> Map of Content：數學規劃（Mathematical Programming）建模方法論 + 29 個經典案例庫的入口。
> 取材自兩本書：José Manuel García Sánchez《Modelling in Mathematical Programming》（下稱「書1」）與 H. Paul Williams《Model Building in Mathematical Programming》5th ed.（下稱「書2」）。兩本書互補——書1 給一套系統化的建模方法論（怎麼想），書2 給業界經典題型的建模參考庫（怎麼寫）。

## 給第一次學建模的人：建議閱讀順序

1. 先讀 [[mathematical-programming-overview]] 建立「什麼是模型、LP/IP/NLP 怎麼分」的整體地圖。
2. 接著讀書1 的方法論全套（[[mp-model-fundamentals]] → [[system-elements]] → [[decision-activities]] → [[system-calculations]] → [[specification-types]] → [[logical-specifications-guide]] → [[quantitative-nature-of-elements]] → [[gs-worked-examples]]），這套順序本身就是一套「怎麼從零開始拆解一個建模問題」的思考流程。
3. 再讀書2 Part I 的其餘章節（[[building-lp-models]] → [[structured-lp-models]] → [[lp-applications-and-networks]] → [[interpreting-lp-solutions]] → [[nonlinear-and-separable-programming]] → [[integer-programming-fundamentals]] → [[special-integer-programming-structures]] → [[integer-programming-refinement]] → [[mp-implementation-in-practice]]），補上 LP/IP 求解後怎麼解讀、以及各種特殊結構的建模工具箱。
4. 方法論讀完後，回頭挑案例庫的頁面實戰——每篇案例頁的「這題示範的建模技巧」都會點名它對應哪個方法論頁，可以照著連結交叉閱讀。

## 書1 García Sánchez 方法論（8 篇，依章節順序）

- [[mp-model-fundamentals]] — 建模為什麼需要方法論而非經驗、古典四元件如何擴充為五元件（Elements/Decision Activities/Calculations/Specifications/Objective Criterion）、決策活動與計算的判準差異
- [[system-elements]] — 如何從系統描述中識別出元素、判斷資料的 own/shared 與 primary element、individual 對 collective 的量化性質判斷
- [[decision-activities]] — 決策活動如何從系統動詞與參與元素中系統化推導出來，以及為何「有計算值的動作」不該被誤定義成決策變數
- [[system-calculations]] — 三種計算變數（auxiliary/logical/bound）怎麼定義，以及為何決策變數與計算變數的角色必須徹底分開
- [[specification-types]] — 規格(specification)為何不等於限制式(constraint)，五種語意分類加上如何在系統描述中揪出隱含規格
- [[logical-specifications-guide]] — 用 big-M 開關技巧把 NOT/OR/AND/IF-THEN/IFF 等邏輯運算子轉成線性限制式
- [[quantitative-nature-of-elements]] — 元素的「數量性質」是建模者的選擇而非題目給定，教你判斷何時該把元素拆開、何時該合併
- [[gs-worked-examples]] — 六個由淺入深的完整案例，把前七章方法論一次串起來實戰演練

## 書2 Williams Part I 方法論（10 篇，依章節順序）

- [[mathematical-programming-overview]] — 模型是什麼、為什麼要建模、LP/NLP/IP/stochastic programming 模型分類，用 product mix 與 blending 兩個入門範例定義目標函數/限制式/RHS 三要素
- [[building-lp-models]] — 線性為什麼讓 LP 好解、目標函數五種類型與限制式十一種類型完整分類、好模型三要素與建模語言
- [[structured-lp-models]] — 大型 LP 如何由多工廠/多產品/多期小模型組合出 block angular 結構，以及 Dantzig-Wolfe decomposition
- [[lp-applications-and-networks]] — LP 在各產業的應用地圖、input-output 經濟模型，以及七種網路模型（運輸/指派/轉運/最短路徑等）
- [[interpreting-lp-solutions]] — 用 product mix 例子講清楚 dual model、shadow price、reduced cost 的經濟意義，以及 alternative optima/degeneracy 陷阱
- [[nonlinear-and-separable-programming]] — convex/non-convex 決定局部解是否等於全域解，separable programming 用分段線性近似偽裝非線性
- [[integer-programming-fundamentals]] — IP 何時該用、四類求解法概觀，以及指示變數、命題邏輯轉限制式、SOS1/SOS2 等建模工具箱
- [[special-integer-programming-structures]] — set covering/packing/partitioning、knapsack、TSP、VRP、QAP，以及 column generation
- [[integer-programming-refinement]] — IP formulation 好壞對比（symmetry、big-M、bounds tightening）、facet 化簡、IP 版敏感度分析
- [[mp-implementation-in-practice]] — MP 模型從算出答案到被組織採用要跨過哪些坎：決策者參與、集中化 vs 去中心化、資料維護

## 經典案例庫（書2 Part II/III/IV，29 篇，依技巧分組）

### 多期生產與存貨規劃

- [[case-food-manufacture-1]] — 六個月原油調配存貨問題，示範單期 LP 擴充成多期模型，教你正確線性化「品質落在區間內」的比例限制
- [[case-food-manufacture-2]] — 延續案例1，加入三條邏輯規則，示範 0-1 指示變數與 semi-continuous variable
- [[case-factory-planning-1]] — 七產品四製程多期生產排程，示範 product mix 問題與 shadow price 在漲價/擴產決策的應用
- [[case-factory-planning-2]] — 把維修時程從已知變成模型決策，示範整數變數如何避免對稱解爆炸
- [[case-manpower-planning]] — 三種技能人力逐年演變，示範「最小化資遣」vs「最小化成本」兩種目標函數的代價差異
- [[case-farm-planning]] — 牛群依年齡拆世代鏈、作物多期存量流動，示範貸款年金折現避免模型過度舉債

### 多階段製程與資源開採

- [[case-refinery-optimisation]] — 蒸餾/重組/裂解/調和四道工序串成一張 LP，示範 structured multi-stage 製程模型
- [[case-mining]] — 五年四礦選三運作，示範用兩組 0-1 變數分別表達「當期運作」與「永久關閉」
- [[case-opencast-mining]] — 露天採礦區塊前置關係約束，約束矩陣全單模，LP relaxation 自動得整數解
- [[case-tariff-rates]] — 電力機組排程 MIP，示範整數解沒有真正 shadow price 時如何折衷估算邊際電價
- [[case-hydro-power]] — 在火力機組排程骨架上疊加水庫水位變數，示範跨時段庫存平衡取代動態規劃

### 網路流、配送與選址

- [[case-distribution-1]] — 工廠+轉運站+客戶配送網路，示範 transhipment 建模與同骨架換目標函數處理多目標
- [[case-depot-location]] — 在配送網路上疊加 0-1 選址開關，示範 fixed charge 問題在網路節點層級的應用
- [[case-milk-collection]] — 兩天路線容量限制 TSP/VRP，示範子巡迴消除按需追加求解
- [[case-lost-baggage-distribution]] — TSP 改造成不繞回原點的 Hamiltonian path，示範子迴路消去延遲生成
- [[case-car-rental-1]] — 四城市租車調度，把車隊流動建模成循環網路流，示範「現實整數」不代表「模型必須整數」
- [[case-car-rental-2]] — 從既有 LP 敏感度分析長出投資決策，示範 precedence 與 cardinality 邏輯限制式疊加在網路流上

### 組合最佳化與邏輯建模

- [[case-logical-design]] — 用最少 NOR 邏輯閘組出指定真值表，示範命題邏輯真值表轉 0-1 限制式
- [[case-market-sharing]] — 23 家零售商依七指標分配市場，示範 goal programming 在 0-1 指派問題求解異常困難的教訓
- [[case-3d-noughts-and-crosses]] — 3×3×3 立體井字遊戲組合最小化，示範單向邏輯+目標函數方向讓求解器自己補完限制式
- [[case-optimising-a-constraint]] — 把一條 0-1 限制式本身當成待簡化對象，用邏輯等價找出最乾淨寫法
- [[case-decentralisation]] — 二次指派問題(QAP)真實案例，示範 0-1 乘積變數線性化二次目標函數

### 定價、效率與非線性

- [[case-curve-fitting]] — 用 LP 做曲線擬合，示範 goal programming 偏差變數與 minimax 轉線性目標
- [[case-agricultural-pricing]] — 政府牛奶/奶油/起司定價，價格彈性線性化到 separable programming 全流程
- [[case-efficiency-analysis]] — 28 間展示中心 DEA 效率評估，把比率型目標轉成可解 LP
- [[case-yield-management]] — 三期航空票價多階段隨機規劃，情境樹取代連續需求曲線
- [[case-economic-planning]] — 動態 Leontief 三產業經濟模型，三種目標函數導出三種成長路徑

### 進階與跨領域應用

- [[case-protein-folding]] — 蛋白質摺疊翻譯成配對+恰好一次轉折的 0-1 邏輯限制式
- [[case-protein-comparison]] — contact map 最大公共子圖比對，最優值本身就是相似度的答案

## Raw 來源

- `raw/Modeling/(Book)Modelling in Mathematical Programming.pdf` — José Manuel García Sánchez, *Modelling in Mathematical Programming: Methodology and Techniques*（Springer, 2021）
- `raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf` — H. Paul Williams, *Model Building in Mathematical Programming*, 5th ed.（Wiley, 2013）
