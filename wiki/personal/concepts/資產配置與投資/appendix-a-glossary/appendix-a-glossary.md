---
type: concept
domain: personal
tags: [investing, glossary, reference, terminology]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 A：術語表 — 把金融黑話翻成人話

> 依英文字母排序。每條給「一句定義 + 為什麼你該在意 + 章節連結」。看到不懂的詞就查這裡。

---

## A

**Accumulating（累積型）**
基金把收到的股息直接在內部再投資，不發給你。相對於配息型（Distributing）。對累積期的台灣投資人稅務上較有利，因為它不製造課稅事件。→ [[05-etf-and-indexing]]、[[08-taiwan-implementation]]

**Active Management（主動管理）**
基金經理人試圖靠選股或擇時打敗指數。扣掉費用後，整體必然落後被動投資（Sharpe 的算術），且十年期約 80~90% 的主動基金落後對照指數。→ [[05-etf-and-indexing]]

**All Weather（全天候組合）**
Ray Dalio 提出的配置概念，讓組合在「成長高/低 × 通膨高/低」四種環境下都有一條腿站著。原版使用槓桿與衍生品，散戶版是簡化模擬。對還在累積期的年輕人偏保守。→ [[07-choose-your-allocation]]

**Anchoring（錨定效應）**
判斷時被第一個接觸到的數字綁住，例如「我的成本是 100 元所以要漲回 100 才賣」。**市場不知道也不在乎你的成本。** → [[11-behavioral-traps]]

**Annualized Return（年化報酬）**
把多年的總報酬換算成「相當於每年成長多少」，用的是幾何平均而非算術平均。看到「平均報酬」要先確認是哪一種。→ [[02-return-and-compounding]]

**Asset Allocation（資產配置）**
決定你的錢分佈在哪幾類資產、各佔多少百分比。它處理「類別與比例」，不是「哪一檔」，而它的重要性遠大於選標的。→ [[00-why-asset-allocation]]

**Asset Class（資產類別）**
性質相近的一群投資標的，例如股票、債券、現金、不動產。判斷一個資產類別該不該進你的組合，要問「它在組合裡做什麼工作」。→ [[04-asset-classes]]

---

## B

**Basis Point（基點，bp）**
0.01 個百分點。100 個基點 = 1%。費用率常用這個單位，例如「7 bp」= 0.07%。

**Behavior Gap（行為差距）**
投資人的實際報酬低於他們所持有基金本身的報酬，差額來自買賣時機。量級大約每年一到三個百分點——這筆錢是被自己的行為拿走的。→ [[11-behavioral-traps]]

**Bid-Ask Spread（買賣價差）**
最高買價與最低賣價的差距。它是一筆隱形成本，不會出現在任何費用揭露裡。成交量低的 ETF 價差大。→ [[05-etf-and-indexing]]

**Bond（債券）**
一張借據。你借錢給政府或公司，收取票息並在到期時取回本金。在組合裡扮演「穩定器」，前提是高信用品質 + 短中天期。→ [[04-asset-classes]]

**Bucketing（分桶）**
把錢按用途與期限分成幾桶，各自有不同配置。最大的價值是心理上的：崩盤時你可以說「近三年要用的錢完全沒事」。→ [[07-choose-your-allocation]]

---

## C

**CAGR（複合年均成長率）**
Compound Annual Growth Rate，即年化報酬的正式名稱。用幾何平均計算，會反映波動拖累。→ [[02-return-and-compounding]]

**Capital Gain（資本利得）**
賣出價格高於買入成本的差額。**台灣目前不課個人證券交易所得稅**，但海外所得走最低稅負制。→ [[08-taiwan-implementation]]

**Compounding（複利）**
報酬本身再產生報酬。因為是指數關係，大部分成果發生在後期——這也是「早開始 10 年勝過多存 20 年」的原因。費用與稅同樣會複利。→ [[02-return-and-compounding]]

**Concentration Risk（集中風險）**
資產過度集中於單一標的、產業或國家。對科技業工程師而言最嚴重的形式是「公司股票 + 台股 + 人力資本」三重疊。→ [[09-rsu-and-concentration]]

**Confirmation Bias（確認偏誤）**
主動尋找支持既有想法的資訊、忽略反面證據。對策是買進前先寫下「什麼證據會證明我錯了」。→ [[11-behavioral-traps]]

**Correlation（相關係數，ρ）**
兩個資產一起變動的程度，範圍 −1 到 +1。**只要小於 1，組合的風險就低於成員風險的加權平均**——這就是「唯一的免費午餐」。→ [[06-correlation-and-rebalancing]]

**Covariance Matrix（共變異數矩陣）**
描述多個資產之間變異與共變關係的矩陣，是計算組合波動的核心輸入。`np.outer(sigma, sigma) * corr` 就能算出來。→ [[13-compute-it-yourself]]

**Credit Risk（信用風險）**
借錢給你的對象違約的風險。高收益債（垃圾債）的信用風險高，且會在股災時一起爆——所以它不能當穩定器。→ [[04-asset-classes]]

---

## D

**DCA（定期定額）**
Dollar-Cost Averaging，固定時間投入固定金額。對領月薪的人而言這不是策略選擇，是現實。好處是完全不用判斷時機。→ [[10-execution-plan]]

**Distributing（配息型）**
基金定期把股息發給你。相對於累積型。在台灣會製造課稅事件（綜所稅 + 可能的補充保費）。→ [[05-etf-and-indexing]]

**Diversification（分散）**
持有多個相關性低的資產以降低風險。它能消除**非系統性風險**，消不掉**系統性風險**。→ [[06-correlation-and-rebalancing]]

**Drawdown（回撤）**
從歷史高點跌到低點的幅度。這才是你真正會痛的數字，因為心理帳戶是以「最多的時候有過多少」為基準。→ [[03-what-risk-really-means]]

**Duration（存續期間）**
債券對利率變化的敏感度，單位是年。近似規則：**利率變動 1% → 價格反向變動約 duration%**。2022 年長天期債券大跌就是這個機制。→ [[04-asset-classes]]

---

## E

**Efficient Frontier（效率前緣）**
在「風險 vs 報酬」平面上，同樣風險下報酬最高的那條邊界。看起來很有說服力，但它的位置對輸入假設極度敏感。→ [[13-compute-it-yourself]]

**Endowment Effect（稟賦效應）**
擁有某樣東西後，對它的估值會系統性升高。破解法是問「如果我現在手上是等值現金，我會買它嗎？」 → [[09-rsu-and-concentration]]

**Emergency Fund（緊急預備金）**
讓你在意外發生時不必被迫賣掉投資部位的一筆現金。科技業建議 6~12 個月的**支出**（不是收入），因為失業與股災會同時發生。→ [[01-money-map]]

**ESPP（員工認股計畫）**
公司讓你用折扣價（常見 85~90%）買自家股票。**參加通常划算，但買到後應盡快賣出**——這是兩個獨立的決定。→ [[09-rsu-and-concentration]]

**Estate Tax（遺產稅）**
過世時對遺產課的稅。重點：**美國對非居民的免稅額只有 6 萬美元**，適用於美國註冊的股票與 ETF，稅率最高 40%。→ [[08-taiwan-implementation]]

**ETF（指數股票型基金）**
在交易所像股票一樣買賣的基金，多數追蹤指數。是本書推薦的主要工具，但要看清楚它追蹤什麼指數、總費用率、註冊地。→ [[05-etf-and-indexing]]

**Expense Ratio（費用率 / TER）**
基金每年從淨值中扣除的總費用比例。**這是你唯一 100% 能控制的變數**：1.5% 的費用率三十年會拿走獲利的約三分之一（約 680 萬）。注意「經理費」不等於總費用率。→ [[05-etf-and-indexing]]

---

## F

**Fat Tails（肥尾）**
極端事件的發生頻率高於常態分布的預測。這是標準差作為風險指標的主要侷限之一。→ [[03-what-risk-really-means]]

**FOMO（錯失恐懼）**
看到別人賺錢而產生的焦慮，導致追高。記住兩件事：沒有人會貼虧損截圖；你不需要參與每一場遊戲。→ [[11-behavioral-traps]]

**Free Lunch（免費的午餐）**
Markowitz 的說法，指分散投資能在不犧牲期望報酬的前提下降低風險。這是資產配置存在的數學理由。→ [[06-correlation-and-rebalancing]]

---

## G

**Geometric Mean（幾何平均）**
考慮複利效果的平均報酬，即 CAGR。永遠小於或等於算術平均，差距來自波動拖累。→ [[02-return-and-compounding]]

**Glide Path（下滑路徑）**
配置隨年齡自動降低股票比例的規劃。目標日期基金內建這個機制，但即使你自己配置也該有一個版本。→ [[07-choose-your-allocation]]

---

## H

**High Yield Bond（高收益債 / 垃圾債）**
信用評等較低的公司債，殖利率高。**它在股災時會跟股票一起崩，所以不是穩定器**，儘管它的名字裡有「債」。→ [[04-asset-classes]]

**Hindsight Bias（後見之明偏誤）**
事後覺得自己「早就知道會這樣」，高估自己的預測能力。唯一的解藥是寫投資日誌。→ [[11-behavioral-traps]]

**Home Bias（本國偏誤）**
過度超配自己國家的股市。台灣佔全球市值約 2%，而多數台灣投資人的股票部位接近 100% 台股。→ [[04-asset-classes]]

**Human Capital（人力資本）**
你未來所有工作收入的現值總和。對三十歲工程師而言通常是金融資產的十倍以上，而且**長得像高波動的科技股**。→ [[00-why-asset-allocation]]

---

## I

**Index（指數）**
一個計算規則（例如「市值前 50 大、按市值加權」）。它本身不能買，只是一個數字。→ [[05-etf-and-indexing]]

**Inflation（通膨）**
物價上漲、購買力下降。它是唯一「什麼都不做也會持續傷害你」的力量，也是「放銀行最安全」這句話的反例。→ [[02-return-and-compounding]]

**IPS（投資政策聲明）**
Investment Policy Statement，你自己寫的財務 runbook：目標、配置、再平衡規則、以及允許/不允許修改的情況。**在冷靜時寫，在情緒時執行。** → [[14-action-checklist]]

---

## L

**Leveraged ETF（槓桿 ETF）**
追蹤指數**每日**報酬倍數的產品。因為每日重設，長期持有會被**波動衰減**侵蝕——指數兩天 +10%/−10% 累計 −1%，正 2 是 −4%。**不是「長期看好的加倍版」。** → [[05-etf-and-indexing]]

**Liquidity（流動性）**
資產能快速以合理價格變現的程度。流動性差的東西在你最需要錢時賣不掉，或要大幅折價。

**Loss Aversion（損失趨避）**
同樣金額，虧損的痛約為獲利快樂的兩倍。它導致崩盤時賣出、以及「賺的急著賣、虧的一直抱」（處分效應）。→ [[11-behavioral-traps]]

**Lump Sum（一次投入）**
把一筆錢一次全部投入市場。期望報酬高於分批投入（約三分之二的歷史期間勝出），但心理壓力較大。→ [[10-execution-plan]]

---

## M

**Marginal Tax Rate（邊際稅率）**
你多賺一塊錢要繳多少稅。它決定了所有節稅決策的價值——例如勞退自提划不划算完全看它。→ [[12-tax-and-safety-net]]

**Market Cap Weighted（市值加權）**
公司越大在指數中權重越高。優點是自動再平衡、周轉率低（所以費用能極低），代價是會集中於大型股與熱門產業。→ [[05-etf-and-indexing]]

**Maximum Drawdown（最大回撤）**
歷史上最大的一次從高點到低點的跌幅。回本是不對稱的：**跌 50% 要漲 100%**。→ [[03-what-risk-really-means]]

**Mental Accounting（心理帳戶）**
把錢貼上不同標籤然後用不同邏輯處理，例如「年終是額外的錢可以賭一把」。錢是可替代的，做總表就能打破它。→ [[11-behavioral-traps]]

**Monte Carlo Simulation（蒙地卡羅模擬）**
用大量隨機模擬產生結果**分布**，而不是單一點估計。正確的用法是問「我的計畫有多容易失敗」，而不是「我會有多少錢」。→ [[13-compute-it-yourself]]

---

## N

**Nominal vs Real（名目 vs 實質）**
名目是帳面數字，實質是扣掉通膨後的購買力。**只有實質報酬是真的。** 定存 1.6% 對通膨 2.2% 的實質報酬是 −0.6%。→ [[02-return-and-compounding]]

**Non-Systematic Risk（非系統性風險）**
個別公司或標的特有的風險（財報造假、工廠失火）。**可以靠分散消除**，因此市場不為它支付報酬。→ [[06-correlation-and-rebalancing]]

**NRA（非居民外國人）**
Non-Resident Alien，美國稅法上的身分。台灣人持有美國資產時適用 NRA 規則：股息預扣 30%、遺產稅免稅額僅 6 萬美元。→ [[08-taiwan-implementation]]

---

## O

**Overconfidence（過度自信）**
高估自己的判斷力。研究顯示高學歷高收入的專業人士過度自信程度**更高**、交易更頻繁，而交易頻率與報酬負相關。→ [[11-behavioral-traps]]

**Overfitting（過擬合）**
在歷史資料上調出的「最佳解」其實只是在擬合雜訊。金融資料訊噪比極低，這個問題比機器學習更嚴重——因為你只有一次測試機會。→ [[13-compute-it-yourself]]

---

## P

**Passive Investing（被動投資）**
持有整個市場、按市值權重，不試圖選股或擇時。基於 Sharpe 的算術，它的整體報酬必然優於主動投資的整體。→ [[05-etf-and-indexing]]

**Percentile（百分位數）**
分布中的位置。蒙地卡羅結果要看 P5（最壞情境的參考）與 P50（中位數），而不是平均值。→ [[13-compute-it-yourself]]

---

## R

**Real Return（實質報酬）**
見 Nominal vs Real。

**Rebalancing（再平衡）**
把偏離的配置調回目標比例，本質是「賣漲多的、買跌多的」。它**確定**能做到的是控制風險水位，提高報酬**不保證**。→ [[06-correlation-and-rebalancing]]

**Recency Bias（近因偏誤）**
最近發生的事在腦中權重過高，導致「連漲三年就以為會一直漲」。解藥是看更長的歷史。→ [[11-behavioral-traps]]

**REITs（不動產投資信託）**
持有商用不動產並分配租金的上市工具。本質上比較像**產業別股票**而非獨立的第三類資產，且廣泛市場指數裡本來就含它。→ [[04-asset-classes]]

**Risk Capacity / Tolerance / Need（承受能力/意願/需要）**
風險承受度的三個獨立維度：客觀條件、主觀心理、目標倒推。**取最小值**。能力可以用緊急預備金買，意願可以訓練。→ [[03-what-risk-really-means]]

**RSU（限制型股票單位）**
公司承諾未來給你股票，條件通常是在職。**歸屬（vest）時才是你的資產，也在那時課稅**。未歸屬的不算資產。→ [[09-rsu-and-concentration]]

---

## S

**Safe Withdrawal Rate（安全提領率）**
退休後每年可提領的比例。經典的 4% 法則（資產 = 年支出 × 25）有五個限制，保守可用 3%~3.5%。→ [[12-tax-and-safety-net]]

**Savings Rate（儲蓄率）**
(稅後收入 − 支出) ÷ 稅後收入。**在前十年，它比報酬率重要得多，而且它是你能控制的。** → [[01-money-map]]

**Sequence of Returns Risk（順序報酬風險）**
在有現金流進出的期間，報酬發生的順序會影響結果。**累積期早跌有利，提領期早跌致命。** → [[03-what-risk-really-means]]

**Sharpe Ratio（夏普比率）**
每承擔一單位風險換到多少超額報酬，`(報酬 − 無風險利率) ÷ 標準差`。用來比較不同風險水位的組合，但同樣受估計誤差影響。→ [[13-compute-it-yourself]]

**Sharpe's Arithmetic（Sharpe 的算術）**
William Sharpe 的論證：主動投資人的整體，扣費用後**必然**落後被動投資人。這是恆等式，不是統計觀察。→ [[05-etf-and-indexing]]

**SIPC**
美國券商的投資人保護機制，總額上限約 50 萬美元（現金部分約 25 萬）。**它保障券商倒閉導致的資產遺失，不保障投資虧損。** → [[08-taiwan-implementation]]

**Standard Deviation（標準差 / 波動度）**
報酬的離散程度，最常用的風險指標。侷限是把漲跌一視同仁、低估肥尾、且不是你實際的體驗。→ [[03-what-risk-really-means]]

**Sub-Brokerage（複委託）**
透過國內券商買賣外國有價證券。方便但通常有**最低手續費（低消）**，小額投入會被吃掉大量成本。→ [[08-taiwan-implementation]]

**Sunk Cost（沉沒成本）**
已經發生、無法收回的成本。「我已經虧 40% 了現在賣就真的虧了」是典型誤用——決策只該看未來的期望值。→ [[11-behavioral-traps]]

**Systematic Risk（系統性風險 / 市場風險）**
整個市場一起承擔的風險（升息、戰爭、衰退）。**分散消除不掉，所以市場為它支付報酬。** → [[06-correlation-and-rebalancing]]

---

## T

**Target Date Fund（目標日期基金）**
隨著接近目標年份自動降低股票比例的基金。是「懶人方案」的極致，理念值得學習即使你自己配置。→ [[07-choose-your-allocation]]

**TER（總費用率）**
Total Expense Ratio。管理費 + 保管費 + 其他費用的合計。**這才是你該比較的數字，不是只看經理費。** → [[05-etf-and-indexing]]

**Three-Fund Portfolio（三基金組合）**
本國股票 + 國際股票 + 債券的極簡配置。**如果你只記一個模型，記這個。** → [[07-choose-your-allocation]]

**Tracking Error（追蹤誤差）**
ETF 的表現與其追蹤指數的差距。長期而言主要來自費用，也可能來自複製方式與現金拖累。→ [[05-etf-and-indexing]]

---

## U

**UCITS**
歐盟的基金監管架構。**愛爾蘭註冊的 UCITS ETF** 對台灣投資人的意義是：美股股息在基金層級約預扣 15%（而非 30%），且通常不涉及美國遺產稅。→ [[08-taiwan-implementation]]

---

## V

**Value at Risk（VaR，風險值）**
在給定信心水準下，一段期間內可能的最大損失。學術與機構常用，但因為低估肥尾而在 2008 年名聲受損。

**Vesting（歸屬）**
RSU 或選擇權真正變成你的東西的時點。**歸屬前不是你的資產，歸屬時課稅。** → [[09-rsu-and-concentration]]

**Volatility（波動度）**
見 Standard Deviation。

**Volatility Drag（波動拖累）**
波動會侵蝕複利報酬。近似關係：`幾何報酬 ≈ 算術報酬 − 標準差² ÷ 2`。**推論：降低波動會直接提高長期報酬，不只是心理需求。** → [[02-return-and-compounding]]

---

## W

**W-8BEN**
向美國證明你是非美國人的表格，據以適用預扣稅率。**有效期限通常數年，到期要重新提交**，否則預扣稅率可能被提高。→ [[08-taiwan-implementation]]

**Withholding Tax（預扣稅）**
在發放股息時直接扣掉的稅。美國註冊 ETF 對台灣人預扣 30%，愛爾蘭 UCITS 在基金層級約 15%。→ [[08-taiwan-implementation]]

---

## 中文專有名詞

**二代健保補充保費**
單筆股利給付達門檻時扣繳的費用。注意是「單筆」計算。→ [[08-taiwan-implementation]]

**最低稅負制（所得基本稅額）**
海外所得的課稅機制：達門檻才計入基本所得額，扣除額之上才課稅。**只在賣出實現時發生。** → [[08-taiwan-implementation]]

**勞退自提**
在雇主法定提繳之外自願提繳到勞退專戶，**可從當年度綜合所得總額中扣除**。價值等於你的邊際稅率，代價是流動性。→ [[12-tax-and-safety-net]]

**證交稅（證券交易稅）**
賣出時課徵，ETF（受益憑證）稅率低於一般股票。

**證所稅（證券交易所得稅）**
對價差課的稅。**台灣目前不課個人證所稅**——這讓「長期持有、低周轉」在台灣特別有利。→ [[08-taiwan-implementation]]

**除息**
發放股利時股價扣除相同金額的機制。**這證明股息不是額外的錢**，只是資產從股票形式變成現金形式。→ [[05-etf-and-indexing]]

---

## 連結

- [[資產配置與投資]] — 全書總目錄
- [[appendix-b-numbers]] — 附錄 B：數字速查
- [[appendix-c-faq]] — 附錄 C：常見問題
- [[14-action-checklist]] — 行動清單與 IPS
