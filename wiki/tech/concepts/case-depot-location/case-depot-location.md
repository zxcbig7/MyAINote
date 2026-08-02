---
type: concept
domain: tech
tags: [optimization, mathematical-programming, mixed-integer-programming, facility-location, network-flow, fixed-charge, case-study]
sources: [raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf]
created: 2026-07-29
updated: 2026-07-29
---

> 📖 來源：H. Paul Williams, *Model Building in Mathematical Programming* 5th ed., Ch.12〈The Problems〉§12.20 pp.275–276, Ch.13〈Formulation and Discussion of Problems〉§13.20 pp.332–333, Ch.14〈Solutions to Problems〉§14.20 p.371。

## 情境：從「怎麼送」到「該不該蓋」

[[case-distribution-1]] 已經把配送網路的骨架建好了：兩座工廠、四個既有轉運站、六名客戶,模型的任務是在**既定的網路形狀**下,找出最省錢的流量分配。Depot location（書中副標題直接寫成 distribution 2）把問題往前推了關鍵的一步：轉運站的位置與數量，本身也變成了模型要決定的東西。公司在考慮是否在 Bristol、Northampton 新設轉運站,或者乾脆擴建既有的 Birmingham 轉運站；同時,基於成本考量,公司也不排斥關掉 Newcastle 或 Exeter（甚至兩個都關），但有一條硬性規定：轉運站總數最多維持四個。

題目給了具體的財務數字：新設或擴建每個選項都有對應的月成本（以利息費用計算）與可能帶來的月吞吐量——Bristol 月成本 £12,000、可提供吞吐量 30,000 噸；Northampton 月成本 £4,000、可提供 25,000 噸；擴建 Birmingham 月成本 £3,000、可額外提供 20,000 噸吞吐量。另一方面,如果關掉 Newcastle,每月可以省下 £10,000；關掉 Exeter 則可省下 £5,000。書裡也補上了新轉運站（Bristol、Northampton）與既有工廠、客戶之間的運費表,延伸了 [[case-distribution-1]] 原本的運費矩陣。四個問題自然浮現：該不該蓋新的轉運站？該不該擴建 Birmingham？該不該關掉 Exeter 或 Newcastle？考慮所有這些選址決策之後，最省錢的配送模式又是什麼？

## 這題示範的建模技巧：網路模型 + 0-1 開關,設施選址問題的經典範式

這一題是 [[lp-applications-and-networks]] 談到的網路模型,與 [[integer-programming-fundamentals]]、[[special-integer-programming-structures]] 談到的離散決策,結合在一起的教科書級示範。上一個案例的網路流變數（$x_{ij}$、$y_{ik}$、$z_{jk}$）本身仍然是連續變數,遵循一模一樣的物料平衡邏輯；真正的變化,是在每個「候選轉運站」節點上,疊加了一個 0-1 開關變數,決定這個節點到底存不存在、或存在到什麼規模。這正是 [[integer-programming-fundamentals]] 在講 fixed charge problem（固定成本問題）時的核心邏輯,被搬到了整張網路的節點層級來用：只要一個節點被「打開」,才能使用它的產能,而打開這個節點本身要付出一筆與流量無關的固定成本（這裡是利息費用）；一旦關閉,不管潛在需求有多大,這個節點的吞吐量就得鎖死在 0。設施選址問題（facility location problem）——不管是倉庫該設在哪、電信機房該擺在哪、服務據點該開在哪——幾乎都是這個「網路流 + 節點開關」樣板的變形,Depot location 正是這個樣板最乾淨的一次具體示範。

## 建模過程：五個 0-1 開關,疊加在延伸後的流量網路上

延續 [[case-distribution-1]] 對轉運站的編號（1=Newcastle、2=Birmingham、3=London、4=Exeter）,模型引入五個新的 0-1 變數：

$$\delta_1=1\text{ 若 Newcastle 保留}\qquad\delta_2=1\text{ 若 Birmingham 擴建}\qquad\delta_4=1\text{ 若 Exeter 保留}$$
$$\delta_5=1\text{ 若在 Bristol 新設}\qquad\delta_6=1\text{ 若在 Northampton 新設}$$

細心的讀者會發現索引裡少了 $\delta_3$——這不是疏漏,而是因為 London（編號 3）從頭到尾都不在選址決策的討論範圍內,它永遠保留,沒有對應的開關變數；同樣地,Birmingham（編號 2）也永遠保留,$\delta_2$ 管的不是「留不留」而是「要不要擴建」,這跟 $\delta_1$、$\delta_4$ 管的「關不關」在語意上並不對稱,讀模型時值得特別留意。除了這五個 0-1 變數,模型還引入延伸的連續流量變數 $x_{i5}$、$x_{i6}$（工廠 $i$ 送到 Bristol／Northampton）與 $z_{5k}$、$z_{6k}$（Bristol／Northampton 送到客戶 $k$）,把 [[case-distribution-1]] 的網路往外擴充了兩個候選節點。

新增的限制式,把離散的「開／關」決策跟連續的流量變數銜接起來：

- **關閉或未建的轉運站不能有任何流量進出**：$\sum_i x_{ij}\le T_j\delta_j$，$j\in\{1,4,5,6\}$（$T_j$ 是轉運站 $j$ 的吞吐量上限）。這條限制式的結構,正是 fixed charge problem 裡「$x\le M\delta$」這種連續變數被二元變數「鎖住」的經典寫法——只要 $\delta_j=0$,右手邊直接歸零,流量也就被迫歸零。
- **Birmingham 擴建限制式**：$\sum_i x_{i2}\le50+20\delta_2$，基礎吞吐量 50,000 噸永遠可用,但只有在 $\delta_2=1$（決定擴建）時,才能多用那額外的 20,000 噸。
- **轉運站總數上限**：$\delta_1+\delta_4+\delta_5+\delta_6\le2$。因為 Birmingham 與 London 本來就穩坐兩個名額,這條限制式等於是在剩下的四個候選轉運站（Newcastle、Exeter、Bristol、Northampton）裡,最多只能同時留下兩個啟用,恰好對應題目「轉運站總數不超過四個」的規定。
- **目標函數**：在 [[case-distribution-1]] 的配送成本目標之上,加上一段代表選址決策財務衝擊的線性項 $10\delta_1+3\delta_2+5\delta_4+12\delta_5+4\delta_6-15$——保留 Newcastle 相當於放棄關閉它原本能省下的 £10,000、保留 Exeter 相當於放棄 £5,000,擴建 Birmingham 要多付 £3,000,新建 Bristol、Northampton 則分別要付 £12,000、£4,000,末尾的常數項則是把整段式子校正回與既有基準線一致的調整量。

整個模型合計 21 條限制式、65 個變數（其中 5 個是 0-1 整數變數）——跟 [[case-distribution-1]] 的 16 條限制式、44 個變數相比,規模只是略為擴張,但問題的性質已經從純 LP 變成了 MIP。

## 解答與洞見

最佳解是：關閉 Newcastle、在 Northampton 新建轉運站、擴建 Birmingham（Exeter 與 London 維持不變）。計入關閉 Newcastle 省下的費用後,整體每月總成本是 £174,000。跟 [[case-distribution-1]] 在**固定網路**下算出的 £198,500 相比,兩者雖然不是完全同一個問題（畢竟這裡多了轉運站的財務成本,也允許了不同的網路形狀）,但這個對照本身就傳達了一個很直接的訊息：只要放寬「網路形狀不能變」這個假設,讓模型自己決定該在哪裡設站、該關哪裡,往往能挖出單純調整既有網路流量所觸及不到的更低成本方案——這正是選址問題之所以在物流規劃裡如此重要的原因。

計算過程還藏著一個值得留意的細節：這個模型只花了 40 次 simplex 疊代就求出最佳解,而且**LP 鬆弛解本身恰好就是整數解**,完全不需要動用 branch and bound 做樹狀搜尋。這不是巧合——[[lp-applications-and-networks]] 談網路模型時反覆強調的 integrality property（只要輸入資料是整數,網路流問題的最適解自然是整數）,即使在疊加了幾個 0-1 開關變數之後,依然在很大程度上發揮作用：模型的骨幹畢竟還是一張網路,只是額外綁了少數幾個離散決策,而不是徹底失去網路結構。這也呼應了 [[special-integer-programming-structures]] 反覆強調的態度——認出一個問題「骨子裡有網路結構」,即使它不完全是七種經典網路模型裡的任何一種,實務上求解時仍然常常能享受到又快又乾淨的整數解這個紅利。

把 [[case-distribution-1]] 與本案例放在一起讀,正好呈現了網路規劃裡一個很自然的演進順序：先在固定的網路上把流量安排到最優（Distribution 1）,再讓模型連網路的形狀本身都一併決定（Depot location）。這個「先優化流量、再優化網路形狀」的兩階段思路,遠遠不只適用於這裡的配送公司——倉儲網路設計、電信機房佈局、服務據點選址,幾乎都是這個樣板的變形應用。

## 連結

- [[case-distribution-1]] — 前一案例:同一張網路,但轉運站的位置與數量是固定的
- [[lp-applications-and-networks]] — 網路模型與 integrality property 的方法論基礎
- [[special-integer-programming-structures]] — 認出問題背後網路結構的價值,與選址問題在組合最佳化中的定位
- [[integer-programming-fundamentals]] — fixed charge problem 的原型,是本案例 $\delta_j$ 開關變數與流量上限式的直接來源
