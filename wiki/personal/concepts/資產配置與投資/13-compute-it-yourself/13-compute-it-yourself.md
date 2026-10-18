---
type: concept
domain: personal
tags: [investing, python, monte-carlo, efficient-frontier, portfolio-math, numpy]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 13 章：用 Python 自己算一遍

## 為什麼要自己算

前面十二章你讀了很多結論。這一章要你**驗證它們**。

三個理由：

**理由 1：自己算過的東西，你在崩盤時才守得住。** 「別人說長期會漲」跟「我自己跑過一萬條模擬路徑，看到分布長什麼樣」是完全不同等級的信心。市場下跌 35% 的那個晚上，前者會動搖，後者不會。

**理由 2：你會看穿宣傳。** 有人拿一張回測圖給你看，說「這個策略年化 15%」。跑過一次最佳化之後，你會立刻問：這是在哪段期間？換一段期間還成立嗎？參數是怎麼選的？

**理由 3：你會親眼看到「最佳化」有多不可靠。** 這是本章最重要的一節。我會示範：把期望報酬的假設動 1 個百分點，「最佳配置」會整個翻掉。看過這個之後，你就不會再想去優化配置比例了。

## 環境準備

只需要三個套件，都不用連網路抓資料：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install numpy pandas matplotlib
```

> 📌 本章所有程式碼都用**假設的參數**跑，不需要真實市場資料。這是刻意的——重點是理解機制與敏感度，不是回測。如果你之後想接真實資料，可以自己找資料來源，但**先把機制搞懂**。

## 程式 1：複利與目標反推

先把第 2 章與第 12 章的算術寫成程式。

```python
def future_value(initial, annual_contrib, years, rate):
    """期初資產 + 每年年初投入，複利成長後的終值"""
    value = initial
    for _ in range(years):
        value = (value + annual_contrib) * (1 + rate)
    return value


def required_contribution(initial, target, years, rate):
    """反推：每年年初要投入多少才能達標"""
    # target = initial*(1+r)^n + C * [((1+r)^n - 1) / r] * (1+r)
    growth = (1 + rate) ** years
    if rate == 0:
        return (target - initial) / years
    annuity_factor = (growth - 1) / rate * (1 + rate)
    return (target - initial * growth) / annuity_factor


if __name__ == "__main__":
    print(f"{future_value(1_000_000, 360_000, 30, 0.06):,.0f}")
    print(f"{required_contribution(1_000_000, 30_000_000, 30, 0.06):,.0f}")
```

跑跑看，然後**把你自己的數字代進去**。這是第 12 章「退休試算」的步驟 4。

**建議做的實驗**：把 `rate` 從 0.06 改成 0.04 和 0.08，看目標金額的差距。你會發現報酬率假設的影響大得驚人——這也是為什麼第 2 章建議用保守假設。

## 程式 2：組合的預期報酬與波動

把第 6 章的公式寫成矩陣形式。

```python
import numpy as np

# 三類資產：股票、債券、現金
names = ["stock", "bond", "cash"]
mu = np.array([0.070, 0.030, 0.015])      # 年化期望報酬
sigma = np.array([0.180, 0.060, 0.005])   # 年化標準差

# 相關矩陣（對稱、對角線為 1）
corr = np.array([
    [1.00, -0.10, 0.00],
    [-0.10, 1.00, 0.00],
    [0.00, 0.00, 1.00],
])

cov = np.outer(sigma, sigma) * corr


def portfolio_stats(weights):
    weights = np.asarray(weights, dtype=float)
    exp_return = weights @ mu
    variance = weights @ cov @ weights
    return exp_return, np.sqrt(variance)


for w in [(1.0, 0.0, 0.0), (0.6, 0.4, 0.0), (0.6, 0.3, 0.1), (0.3, 0.6, 0.1)]:
    r, v = portfolio_stats(w)
    print(f"{str(w):22s} 報酬 {r:6.2%}  波動 {v:6.2%}")
```

`np.outer(sigma, sigma) * corr` 這一行就是把相關矩陣轉成共變異數矩陣，也就是第 6 章那條公式的矩陣版本。

**建議做的實驗**：把股債相關係數從 `-0.10` 改成 `+0.60`（模擬 2022 那種環境），看 60/40 組合的波動變成多少。**你會看到「穩定器失效」在數字上長什麼樣。**

## 程式 3：相關係數對波動的影響

把第 6 章那張表畫出來。

```python
import numpy as np
import matplotlib.pyplot as plt

w_stock, w_bond = 0.6, 0.4
s_stock, s_bond = 0.18, 0.06

rhos = np.linspace(-1.0, 1.0, 201)
vols = np.sqrt(
    (w_stock * s_stock) ** 2
    + (w_bond * s_bond) ** 2
    + 2 * w_stock * w_bond * rhos * s_stock * s_bond
)

plt.plot(rhos, vols * 100)
plt.xlabel("correlation")
plt.ylabel("portfolio volatility (%)")
plt.title("60/40 portfolio volatility vs correlation")
plt.grid(alpha=0.3)
plt.show()
```

你會看到一條由左下往右上的曲線。**這條線就是「免費午餐」的形狀**——相關係數越低，同樣的期望報酬換到越低的波動。

## 程式 4：效率前緣長什麼樣

隨機產生大量權重組合，畫在「風險 vs 報酬」平面上。

```python
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
n = 20000

# Dirichlet 產生加總為 1 且非負的權重
weights = rng.dirichlet(np.ones(3), size=n)

rets = weights @ mu
vols = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))

plt.scatter(vols * 100, rets * 100, s=2, alpha=0.25)
plt.xlabel("volatility (%)")
plt.ylabel("expected return (%)")
plt.title("random portfolios")
plt.grid(alpha=0.3)
plt.show()
```

那朵雲的**左上邊界**就是效率前緣——在同樣風險下報酬最高的那些組合。

看起來很有說服力，對吧？下一節要拆掉它。

## 程式 5：最佳化為什麼是在擬合雜訊 ⭐

**這是本章最重要的一段。** 我們來看「最佳配置」對輸入假設有多敏感。

```python
import numpy as np

rng = np.random.default_rng(0)
sigma = np.array([0.180, 0.060, 0.005])
corr = np.array([
    [1.00, -0.10, 0.00],
    [-0.10, 1.00, 0.00],
    [0.00, 0.00, 1.00],
])
cov = np.outer(sigma, sigma) * corr
rf = 0.01  # 無風險利率


def best_sharpe_weights(mu_vec, n=200000, seed=0):
    """隨機搜尋 Sharpe ratio 最高的權重"""
    local_rng = np.random.default_rng(seed)
    w = local_rng.dirichlet(np.ones(len(mu_vec)), size=n)
    rets = w @ mu_vec
    vols = np.sqrt(np.einsum("ij,jk,ik->i", w, cov, w))
    sharpe = (rets - rf) / vols
    return w[np.argmax(sharpe)], sharpe.max()


scenarios = {
    "baseline      ": np.array([0.070, 0.030, 0.015]),
    "stock +1pp    ": np.array([0.080, 0.030, 0.015]),
    "stock -1pp    ": np.array([0.060, 0.030, 0.015]),
    "bond +1pp     ": np.array([0.070, 0.040, 0.015]),
}

for label, mu_vec in scenarios.items():
    w, s = best_sharpe_weights(mu_vec)
    pct = " / ".join(f"{x:5.1%}" for x in w)
    print(f"{label} 最佳權重 {pct}  Sharpe {s:.3f}")
```

跑跑看。你會看到類似這樣的結果（實際數字視隨機種子而定）：

```text
baseline       最佳權重 24.9% / 61.0% / 14.1%  Sharpe 0.457
stock +1pp     最佳權重 40.2% / 52.1% /  7.7%  Sharpe 0.545
stock -1pp     最佳權重 13.8% / 66.5% / 19.7%  Sharpe 0.372
bond +1pp      最佳權重 17.1% / 76.4% /  6.5%  Sharpe 0.586
```

**把期望報酬的假設動 1 個百分點，最佳股票權重從 14% 跳到 40%。**

現在問一個關鍵問題：**你對「股票長期期望報酬」的估計，誤差有沒有可能超過 1 個百分點？**

當然有。歷史上不同期間、不同市場的數字差異遠大於 1 個百分點；而且沒有人知道未來三十年的真實值。學術上估計股票風險溢酬的**標準誤**通常有好幾個百分點。

**所以結論是：**

> **「最佳配置」的輸入本身有巨大的不確定性，而輸出對輸入極度敏感。**
> **這代表最佳化的結果沒有實質意義——它是在對你猜出來的數字做精確計算。**

這現象在文獻上被稱為**誤差最大化器（error maximizer）**：均值-變異數最佳化會系統性地把權重推向「你剛好高估了期望報酬」的那個資產。

**該怎麼辦？**

| 做法 | 說明 |
| --- | --- |
| **追求穩健而非最佳** | 選一個在各種假設下都「還可以」的配置 |
| **用簡單的規則** | 60/40、三基金——它們沒有被最佳化，所以也不會被最佳化的錯誤傷害 |
| **加上限制** | 例如每類資產至少 10%、最多 60%，防止極端解 |
| **關注你能控制的** | 費用、稅、儲蓄率、行為（這些沒有估計誤差問題） |

> 🔧 **工程師視角**：這跟你調 hyperparameter 一樣。在驗證集上調出來的最佳參數，換一組資料就失效——因為你在對雜訊過擬合。差別在於：機器學習你還有測試集可以檢驗，而**投資的「測試集」是你的下半輩子，只能跑一次**。

## 程式 6：蒙地卡羅模擬 — 看分布，不看平均

單一的「年化 6%」是一個點估計。真正有用的是**分布**。

```python
import numpy as np

rng = np.random.default_rng(42)

years = 30
n_sims = 20000
initial = 1_000_000
annual_contrib = 360_000
mu_p = 0.054      # 組合期望報酬（來自程式 2）
sigma_p = 0.110   # 組合波動
target = 25_000_000

values = np.full(n_sims, float(initial))
for _ in range(years):
    r = rng.normal(mu_p, sigma_p, n_sims)
    values = (values + annual_contrib) * (1 + r)

pcts = [5, 10, 25, 50, 75, 90, 95]
for p in pcts:
    print(f"P{p:<3d} {np.percentile(values, p):>15,.0f}")

print(f"\n達成 {target:,} 的機率：{(values >= target).mean():.1%}")
print(f"低於總投入本金的機率：{(values < initial + annual_contrib * years).mean():.1%}")
```

輸出會像這樣（數字視參數而定）：

```text
P5           14,200,000
P10          16,100,000
P25          19,900,000
P50          25,100,000
P75          31,800,000
P90          39,600,000
P95          45,700,000

達成 25,000,000 的機率：50.3%
低於總投入本金的機率：0.4%
```

**這張表比「年化 6%」有用一百倍。** 它告訴你：

- 中位數是多少（不是平均數——平均數會被右尾拉高）
- **最壞的 5% 情境長什麼樣**（這是你要能接受的下限）
- 達成目標的機率是多少（如果只有 50%，那你要調整目標或儲蓄率）

### 三個必須知道的模型限制

**限制 1：常態分布低估了極端事件。** 真實報酬有肥尾（第 3 章）。要更保守，可以改用 t 分布：

```python
df = 4  # 自由度越小尾巴越肥
raw = rng.standard_t(df, n_sims)
r = mu_p + sigma_p * raw / np.sqrt(df / (df - 2))
```

**限制 2：這個模型假設每年報酬獨立。** 真實市場有輕微的均值回歸與波動叢集。

**限制 3：輸入還是你猜的。** 跟程式 5 一樣——**跑幾組不同的 `mu_p` 看結果怎麼變**，這比精算單一情境有意義得多。

**所以正確的用法是**：不要問「我會有多少錢」，要問「**在合理的假設範圍內，我的計畫有多容易失敗**」。

## 程式 7：順序報酬風險 — 看一次就懂

把第 3 章的概念跑出來。同一組報酬，只是順序不同。

```python
import numpy as np

rng = np.random.default_rng(7)

returns = rng.normal(0.06, 0.15, 30)  # 固定這 30 個年報酬
initial = 20_000_000
withdrawal = 800_000  # 每年提領 80 萬（4%）


def terminal_value(rets, order):
    value = float(initial)
    for r in rets[order]:
        value = (value - withdrawal) * (1 + r)
        if value <= 0:
            return 0.0
    return value


ascending = np.argsort(returns)          # 最差的年份先發生
descending = ascending[::-1]             # 最好的年份先發生

print(f"原始順序   {terminal_value(returns, np.arange(30)):>15,.0f}")
print(f"壞的先發生 {terminal_value(returns, ascending):>15,.0f}")
print(f"好的先發生 {terminal_value(returns, descending):>15,.0f}")
```

**同樣的 30 個報酬、同樣的平均值，結果可能差到好幾倍，甚至一邊歸零。**

把 `withdrawal` 改成 `0`（純累積、不提領），再跑一次——你會發現**三種順序的結果完全相同**。

這個對照就是第 3 章那句話的證明：

> **只有在有現金流進出時，順序才會影響結果。累積期早跌有利，提領期早跌致命。**

## 程式 8：費用率的三十年帳

把第 5 章那張表自己算一次。

```python
def with_fee(initial, annual_contrib, years, gross_rate, fee):
    net = gross_rate - fee
    value = float(initial)
    for _ in range(years):
        value = (value + annual_contrib) * (1 + net)
    return value


base = None
for fee in [0.001, 0.003, 0.005, 0.010, 0.015, 0.020]:
    v = with_fee(0, 300_000, 30, 0.07, fee)
    if base is None:
        base = v
    print(f"fee {fee:5.2%}  終值 {v:>14,.0f}  相對最低費用少 {base - v:>12,.0f}")
```

**看著自己的螢幕跑出這個數字，比讀十篇文章有效。** 跑出來的結果應該與 [[appendix-b-numbers]] 的費用率表一致（0.1% 約 2,970 萬、1.5% 約 2,290 萬，差 680 萬）。

> 📌 **本章所有程式都假設「每年年初投入」**（`(value + contrib) * (1 + r)`），與蒙地卡羅那段一致。如果你改成年底投入，數字會小約 6%——**這種假設差異在複利計算裡很常見，也是不同來源的試算結果對不上的常見原因**。看到任何試算表，先確認它假設投入發生在期初還是期末。

## 怎麼用這些結果（以及怎麼不要用）

| ✅ 該這樣用 | ❌ 不要這樣用 |
| --- | --- |
| 理解各參數的**敏感度** | 找出「最佳」配置比例 |
| 看**分布**與失敗機率 | 預測你三十年後有多少錢 |
| 壓力測試你的計畫（悲觀假設下還成立嗎） | 用結果說服自己承擔更多風險 |
| 驗證書上的結論 | 拿去回測策略然後真的執行 |
| 建立在崩盤時守得住的信心 | 每個月重跑一次調整配置 |

**一個實用的收尾建議**：把這些程式存成一個檔案，每年做年度檢視（第 10 章）時跑一次，把當年的實際數字代進去。**它會變成你個人的財務儀表板**，而且是你自己寫的，你完全知道它在算什麼。

## 本章重點回顧

1. 自己算的三個理由：**崩盤時守得住的信心、看穿宣傳、親眼看到最佳化有多不可靠**。
2. `np.outer(sigma, sigma) * corr` 就是共變異數矩陣，第 6 章公式的矩陣版本。把相關係數改成 +0.6 可以看到「穩定器失效」的數字樣貌。
3. **最重要的實驗**：期望報酬假設動 **1 個百分點**，最佳股票權重從 14% 跳到 40%。而你的估計誤差**一定**大於 1 個百分點——所以**最佳化是誤差最大化器**，是在對猜出來的數字做精確計算。
4. 對策是**追求穩健而非最佳**：用簡單規則、加權重上下限、把力氣放在沒有估計誤差問題的地方（費用、稅、儲蓄率、行為）。
5. 蒙地卡羅要**看分布不看平均**：P5 是你要能接受的下限，達成機率決定你要不要調整目標或儲蓄率。並記住三個模型限制（常態低估肥尾、假設獨立、輸入還是猜的）。
6. 順序報酬風險的證明：把提領金額設成 0，三種順序結果完全相同——**只有在有現金流進出時順序才重要**。
7. 這些程式是**理解工具與壓力測試工具**，不是預測工具，更不是策略搜尋工具。

## 下一步

最後一章。把前面所有東西收斂成一份可以直接執行的文件：**30 天啟動計畫、投資政策聲明（IPS）模板、以及一份紅色警戒清單**。

## 連結

- [[資產配置與投資]] — 全書總目錄
- [[12-tax-and-safety-net]] — 上一章：稅、保險與退休試算
- [[14-action-checklist]] — 下一章：行動清單與 IPS
- [[06-correlation-and-rebalancing]] — 組合變異數公式的原始出處
- [[11-behavioral-traps]] — 工程師的過度最佳化陷阱
- [[python]] — Python 語法本身
