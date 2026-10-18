---
type: entity
domain: tech
tags: [python, programming, language, csharp-comparison, type-hints, generator, duck-typing]
sources:
  - raw/Languages/Python/Python.md
  - raw/Languages/Python/第一部分：數字、字串與變數.md
  - raw/Languages/Python/第二部分 串列、Tuple、字典與集合.md
  - raw/Languages/Python/第三部分：程式結構.md
  - raw/Languages/Python/第一堂(2020 3 3).md
  - raw/Languages/Python/第二堂(2020 3 10).md
  - raw/Languages/Python/GUI套件-tkinter.md
created: 2026-05-10
updated: 2026-08-16
---

# Python

Python 是動態型別、直譯執行的通用語言。這一頁**不是語法教學**——那種東西到處都有。它寫給一個特定的讀者：**已經熟悉 C#，需要看懂並寫出像樣 Python 的人**。

所以組織方式不是「從變數講到類別」，而是「**你的 C# 直覺會在哪裡壞掉**」。會壞的地方講深一點，不會壞的地方一筆帶過。

> **來源覆蓋說明**：`raw/Languages/Python/` 那批是 2020 年的課程筆記，紮實地涵蓋了型別、四大容器、控制流程與生成式（本頁第二到四節的事實基礎來自它們）。但它沒有函式、類別、模組、例外、型別提示這幾章——而那些恰好是寫 [[python-fast-api]] 的前提，所以第五節之後是補寫的。tkinter 那部分與目前的技術路線無關，只在最後保留指標。

---

## 一、五個會壞掉的直覺

先講這五件事，後面所有細節都是它們的展開。

### 1. 變數是「名牌」，不是「盒子」

C# 的 `int x = 5` 是「配置一塊記憶體叫 x，裡面放 5」。Python 的 `x = 5` 是「建立物件 5，然後把 `x` 這張名牌貼上去」。

差別在有東西被共享的時候：

```python
a = [1, 2, 3]
b = a           # 不是複製，是第二張名牌貼到同一個物件上
b.append(4)
print(a)        # [1, 2, 3, 4]  ← a 也變了
```

C# 的 `List<int>` 也是參考型別，這裡行為一樣。真正的差異在於 **Python 沒有值型別**——`int`、`str`、`tuple` 全都是物件，只是它們**不可變**，所以你感覺不出來。

「不可變」與「參考語意」這兩件事合起來，解釋了 Python 大部分看起來奇怪的行為。

### 2. 縮排就是語法

沒有大括號。縮排錯誤不是風格問題，是**語法錯誤**（或更糟——是能跑但邏輯錯的程式）。

```python
for x in items:
    process(x)
    log(x)      # 在迴圈內
log("done")     # 在迴圈外
```

團隊一律用四個空格，並讓 formatter（`ruff format` 或 `black`）強制。混用 tab 與空格在 Python 3 是直接報錯。

### 3. 型別提示不會被執行

```python
def add(a: int, b: int) -> int:
    return a + b

add("x", "y")     # 'xy'——沒有任何錯誤
```

型別提示（PEP 484）是給 mypy、Pyright、IDE 和**框架**看的，直譯器完全忽略。它們被存在 `__annotations__` 裡，任何人都可以在執行期讀出來——[[python-fast-api]] 整套機制就建立在這件事上。

實務結論：**專案超過一定規模，一定要把型別檢查加進 CI**。C# 的重構由編譯器保證，Python 只有 mypy/Pyright 加測試。

### 4. 沒有 private

```python
class User:
    def __init__(self):
        self.name = "x"        # public
        self._token = "y"      # 慣例上是內部用，但誰都能存取
        self.__secret = "z"    # name mangling，變成 _User__secret，仍然拿得到
```

單底線是**約定**（「這是內部的，別碰」），雙底線是 name mangling（為了避免子類別意外覆蓋，不是為了安全）。Python 沒有語言層級的存取控制。

這不是缺陷，是哲學差異——Python 假設使用者是成年人。但它代表**封裝要靠紀律和 code review，不能靠編譯器**。

### 5. 沒有多載，也不需要介面

```python
# ✗ 這不是多載，第二個定義直接蓋掉第一個
def send(msg: str): ...
def send(msg: str, retry: int): ...
```

要「多載」就用預設值或 `*args`。要「介面」則靠 **duck typing**——不看型別，只看有沒有那個方法：

```python
def render(target):
    target.draw()          # 任何有 draw() 的東西都行
```

需要靜態檢查得到的契約時用 `typing.Protocol`（結構化型別，不需要明確繼承）：

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render(target: Drawable) -> None:
    target.draw()
```

`Protocol` 是 C# 介面最接近的對應，但**只在型別檢查時生效**，執行期不強制。

---

## 二、型別與變數

### 數值

| | C# | Python |
| --- | --- | --- |
| 整數上限 | `int` 32 位元、`long` 64 位元 | **`int` 沒有上限**，記憶體多大就多大 |
| 浮點 | `double` / `float` | `float`（等同 C# 的 `double`） |
| 精確小數 | `decimal` | `decimal.Decimal` |
| 整數除法 | `7 / 2 == 3` | `7 / 2 == 3.5`（**永遠是 float**） |
| 取整除法 | — | `7 // 2 == 3` |
| 次方 | `Math.Pow(2, 10)` | `2 ** 10` |

`/` 和 `//` 是最容易錯的一對。C# 的 `int / int` 給整數，Python 給 float——寫索引計算時忘了用 `//` 會得到 `TypeError: list indices must be integers`。

金額一律用 `Decimal`，理由和 C# 用 `decimal` 一樣：二進位浮點數表示不了 0.1。

### 字串

字串**不可變**（和 C# 一樣），所以迴圈裡 `s += x` 會不斷產生新物件。大量拼接用 `"".join(parts)`，對應 C# 的 `StringBuilder`。

格式化用 f-string，它是目前唯一該用的寫法：

```python
name, count = "訂單", 3
print(f"{name} 共 {count} 筆，單價 {price:.2f}")
print(f"{count=}")          # count=3，除錯時很好用
```

多行字串用三引號。原始字串加 `r` 前綴（寫正則和 Windows 路徑時必用）：

```python
pattern = r"\d+\.\d+"
path = r"C:\Users\zxcbi\Desktop"
```

### 真假值（truthiness）

C# 的 `if` 只吃 `bool`。Python 的 `if` 吃任何東西，以下**全部視為 False**：

| False | 說明 |
| --- | --- |
| `False` | 布林 |
| `None` | 相當於 C# 的 `null` |
| `0`、`0.0`、`Decimal(0)` | 零 |
| `""` | 空字串 |
| `[]`、`()`、`{}`、`set()` | 空容器 |

其餘一律是 True。所以檢查空清單直接寫 `if not items:`，很簡潔——但**這也是一個著名的 bug 來源**：

```python
def process(count=None):
    if not count:          # ✗ count=0 也會進來
        count = 10
    ...

    if count is None:      # ✓ 明確檢查
        count = 10
```

判斷 `None` 一律用 `is None` / `is not None`，不要用 `==`。

---

## 三、四大容器

這是 Python 最核心的資料結構組合，也是 raw 筆記寫得最紮實的部分。

| Python | C# 對應 | 可變 | 有序 | 可重複 | 字面語法 |
| --- | --- | --- | --- | --- | --- |
| `list` | `List<T>` | ✓ | ✓ | ✓ | `[1, 2, 3]` |
| `tuple` | `ValueTuple` / 唯讀陣列 | ✗ | ✓ | ✓ | `(1, 2, 3)` |
| `dict` | `Dictionary<K,V>` | ✓ | ✓（3.7+ 保序） | key 不重複 | `{"a": 1}` |
| `set` | `HashSet<T>` | ✓ | ✗ | ✗ | `{1, 2, 3}` |

四個都是**異質的**——一個 list 可以同時裝 int、str 和另一個 list。這是彈性也是風險，型別提示（`list[int]`）就是用來把契約寫回去的。

### 切片：Python 最好用的語法之一

```python
items = [0, 1, 2, 3, 4, 5]
items[2:5]      # [2, 3, 4]     起點含、終點不含
items[:3]       # [0, 1, 2]
items[-2:]      # [4, 5]        負索引從尾端算
items[::2]      # [0, 2, 4]     每隔一個
items[::-1]     # [5, 4, 3, 2, 1, 0]   反轉
```

切片對字串也成立。C# 8 的範圍語法（`items[2..5]`、`items[^2..]`）就是借鏡這個設計。

### `tuple` 的兩個實際用途

**一、多重回傳值**（不用定義類別）：

```python
def divide(a: int, b: int) -> tuple[int, int]:
    return a // b, a % b

quotient, remainder = divide(17, 5)      # 解構，對應 C# 的 ValueTuple
```

**二、當 dict 的 key**——因為它不可變所以可雜湊，list 不行：

```python
cache: dict[tuple[str, int], Result] = {}
cache[("orders", 42)] = result
```

單元素 tuple 要寫 `(1,)`，少了逗號就只是一個括號括起來的數字。這個坑每個人都踩過一次。

### `dict` 的安全存取

```python
d = {"a": 1}
d["b"]                  # KeyError
d.get("b")              # None
d.get("b", 0)           # 0，對應 C# 的 TryGetValue
d.setdefault("b", [])   # 沒有就建一個並回傳
```

計數與分組用 `collections` 裡的專門型別，比手刻乾淨：

```python
from collections import Counter, defaultdict

Counter(words).most_common(3)
groups = defaultdict(list)
for order in orders:
    groups[order.status].append(order)
```

### `set` 的集合運算

```python
a, b = {1, 2, 3}, {2, 3, 4}
a & b       # {2, 3}      交集
a | b       # {1,2,3,4}   聯集
a - b       # {1}         差集
a ^ b       # {1, 4}      對稱差
```

實務上最常用的是**去重**（`list(set(items))`，但會失去順序）和**成員測試**——`x in some_set` 是 O(1)，`x in some_list` 是 O(n)。在迴圈裡對大 list 做 `in` 是很常見的效能地雷。

### 可變預設參數：最經典的坑

```python
# ✗ 這個預設值在函式「定義時」就建好了，所有呼叫共用同一個
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket

add_item(1)     # [1]
add_item(2)     # [1, 2]  ← 上一次的還在

# ✓
def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

根因是 Python 的預設值**在 `def` 執行的那一刻求值一次**，不是每次呼叫都重新求值。C# 要求預設值是編譯期常數，所以不會有這個問題。

規則很簡單：**預設值只能是不可變的東西**（數字、字串、`None`、tuple）。

（例外：FastAPI 的參數宣告裡 `= []` 是安全的，因為那個物件只被當成 schema 的預設，不會被改動。見 [[01-routing-and-path-operations]]。）

### 拷貝

```python
import copy

b = a                    # 同一個物件
b = a.copy()             # 淺拷貝——巢狀的內容仍然共用
b = copy.deepcopy(a)     # 深拷貝
```

淺拷貝之後改動巢狀元素會影響原物件，這是「以為複製了但沒有」的主要來源。

---

## 四、控制流程與生成式

### 迴圈

Python 只有 `for ... in`（迭代）與 `while`，**沒有 C 式的 `for(i=0; i<n; i++)`**。需要索引用 `enumerate`：

```python
for i, item in enumerate(items, start=1):
    print(i, item)

for name, score in zip(names, scores):      # 同時迭代多個序列
    ...

for i in range(0, 10, 2):                   # 0, 2, 4, 6, 8
    ...
```

`range` 是惰性的（不會真的產生一個十億元素的 list），對應 C# 的 `Enumerable.Range`。

### `for-else` / `while-else`

C# 沒有這個東西：**迴圈正常跑完（沒有被 `break`）才執行 `else`**。

```python
for order in orders:
    if order.status == "failed":
        notify(order)
        break
else:
    log("全部正常")        # 沒有任何 break 才會到這裡
```

它取代了「設一個 `found` 旗標然後在迴圈後檢查」的樣板。不常見但看到要認得。

### 生成式：Python 版的 LINQ

這是 Python 最有辨識度的語法，也是從 C# 過來最快能上手的部分：

```python
# 對照 LINQ
[x * 2 for x in items if x > 0]                    # items.Where(x => x > 0).Select(x => x * 2)
{o.id: o.total for o in orders}                    # ToDictionary(o => o.id, o => o.total)
{o.status for o in orders}                         # Select(...).Distinct() → HashSet
(x * 2 for x in items)                             # 產生器：惰性，對應未具體化的 IEnumerable
```

前三個立刻產生完整的 list/dict/set；**第四個用小括號，回傳的是產生器**——惰性求值，只在被迭代時才逐一產生元素。

處理大檔案或大結果集時這個差別是關鍵：

```python
# ✗ 十萬列全部進記憶體
rows = [parse(line) for line in open("big.csv")]

# ✓ 一次只有一列在記憶體裡
rows = (parse(line) for line in open("big.csv"))
for row in rows:
    ...
```

生成式**巢狀超過兩層就該改回 for 迴圈**。可讀性優先，這一點和 LINQ 的鏈式查詢寫太長是同一個問題。

### 產生器函式

用 `yield` 寫的函式回傳產生器，對應 C# 的 `yield return`：

```python
def read_batches(path: str, size: int = 1000):
    batch = []
    for line in open(path, encoding="utf-8"):
        batch.append(parse(line))
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch
```

概念幾乎一樣。但要注意 Python 的 `yield` 還有第二個用途——[[03-dependency-injection]] 裡那種「yield 前是 setup、yield 後是 teardown」的資源管理寫法。

---

## 五、函式

```python
def create_order(
    customer_id: int,                    # 位置或關鍵字
    *items: Item,                        # 可變位置參數 → C# 的 params
    notify: bool = False,                # 只能用關鍵字傳（因為在 *items 之後）
    **extra: str,                        # 可變關鍵字參數，C# 沒有對應
) -> Order:
    ...

create_order(1, item_a, item_b, notify=True, source="web")
```

三個和 C# 不同的地方：

**關鍵字引數是一級公民。** `func(timeout=30)` 是常態寫法，不是特例。參數多的時候強制用關鍵字（在參數列放一個 `*`）可以大幅提升可讀性：

```python
def resize(image, *, width: int, height: int):    # width/height 必須用關鍵字傳
    ...
resize(img, width=100, height=50)                 # resize(img, 100, 50) 會報錯
```

**函式是物件。** 可以指派、當參數傳、當回傳值。decorator 就是建立在這件事上——`@app.get("/x")` 的本質是 `f = app.get("/x")(f)`。

**沒有 `ref` / `out`。** 要回傳多個值就回傳 tuple。

---

## 六、類別

```python
from dataclasses import dataclass, field

class Order:
    def __init__(self, customer_id: int, total: Decimal) -> None:
        self.customer_id = customer_id
        self.total = total

    def apply_discount(self, rate: Decimal) -> None:
        self.total *= (1 - rate)

    @property
    def is_large(self) -> bool:
        return self.total > 10000

    def __repr__(self) -> str:
        return f"Order(customer_id={self.customer_id}, total={self.total})"
```

`self` 必須明確寫出來（對應 C# 隱含的 `this`）。`__init__` 是建構式，`__repr__` 是除錯用的字串表示——**值得為每個資料類別實作它**，否則 log 裡只會看到 `<Order object at 0x...>`。

單純裝資料的類別直接用 `dataclass`，它自動產生 `__init__`、`__repr__`、`__eq__`：

```python
@dataclass
class Order:
    customer_id: int
    total: Decimal
    tags: list[str] = field(default_factory=list)   # 可變預設值要用 factory
```

這對應 C# 的 `record`。注意 `field(default_factory=list)`——直接寫 `= []` 會觸發第三節那個可變預設值的坑，`dataclass` 會直接報錯擋下來。

需要驗證與序列化時用 Pydantic 的 `BaseModel` 取代（見 [[02-pydantic-and-validation]]）。三者的分工：`dataclass` 是純資料容器、`BaseModel` 是有驗證的資料契約、一般 `class` 是有行為的物件。

繼承支援多重繼承（C# 不支援），但**除非在寫框架，否則別用**——MRO（方法解析順序）的規則很快就會變得沒人說得清楚。組合優於繼承在 Python 更成立。

---

## 七、模組與匯入

一個 `.py` 檔就是一個模組，一個含 `__init__.py` 的資料夾就是一個 package。沒有組件（assembly）這一層。

```python
from app.services.order import create_order      # 明確匯入（建議）
import app.services.order as order_service       # 匯入模組
from app.models import *                         # ✗ 幾乎不該用
```

三件事要知道：

**模組層級的程式碼在第一次 import 時執行一次。** 這就是為什麼 `settings = get_settings()` 寫在模組層級等於「程序啟動時驗證」（見 [[09-configuration]]），也是為什麼 decorator 的註冊會在 import 時發生。

**循環匯入是真實問題。** A import B、B import A 會炸。解法是把共用的東西抽到第三個模組，或把 import 移進函式內部（延後到呼叫時）。專案結構分層清楚就很少遇到。

**`if __name__ == "__main__":`** 讓一個檔案既能被 import 也能被直接執行——裡面的程式碼只在直接執行時跑。

---

## 八、例外：EAFP 而不是 LBYL

這是一個文化差異，不只是語法差異。

C# 的慣例是 **LBYL**（Look Before You Leap，先檢查再做）：

```csharp
if (dict.ContainsKey(key)) { var v = dict[key]; }
```

Python 的慣例是 **EAFP**（Easier to Ask Forgiveness than Permission，先做，錯了再處理）：

```python
try:
    v = d[key]
except KeyError:
    v = default
```

理由是 Python 的例外成本相對低，而且 EAFP 沒有 check-then-act 之間的競態問題。所以在 Python 裡**用例外處理「預期中的失敗」是正常的**，不像 C# 那樣要盡量避免。

```python
try:
    result = risky()
except (ValueError, KeyError) as exc:      # 一次接多種
    logger.warning("失敗: %s", exc)
    raise DomainError("...") from exc      # from 保留原始 traceback
else:
    commit()                                # 沒有例外才執行
finally:
    cleanup()                               # 一定執行
```

四個紀律：**接具體的例外型別**（`except Exception` 只用在最外層）、**絕不寫 `except: pass`**、**重新拋出時用 `raise ... from exc`** 保留因果鏈、**`finally` 一定要有**（或用 `with`）。

`with` 就是 C# 的 `using`：

```python
with open("f.txt", encoding="utf-8") as f:      # 離開時自動 close
    data = f.read()
```

**檔案一律明確指定 `encoding="utf-8"`**。不指定的話 Windows 上會用系統預設編碼（多半是 cp950），讀中文直接亂碼或炸掉。這是 Windows 開發者最常踩的一個坑。

---

## 九、型別提示

雖然執行期不強制，但在任何超過玩具規模的專案裡都該寫——它是 [[python-fast-api]] 的前提，也是 Python 專案唯一的重構安全網。

```python
from typing import Annotated, Any, Protocol

def find(user_id: int) -> User | None: ...          # 3.10+ 的聯集寫法
def process(items: list[str]) -> dict[str, int]: ...  # 3.9+ 內建泛型
def handler(cb: Callable[[int], str]) -> None: ...
```

| C# | Python |
| --- | --- |
| `User?` | `User \| None` |
| `List<string>` | `list[str]` |
| `Dictionary<string,int>` | `dict[str, int]` |
| `IEnumerable<T>` | `Iterable[T]` |
| `Func<int,string>` | `Callable[[int], str]` |
| `object` | `Any`（放棄檢查）或 `object`（保留檢查） |
| interface | `Protocol` |

`Any` 會關掉那一段的所有檢查，用它等於宣告放棄。真的不知道型別時用 `object` 比較誠實。

檢查工具兩選一：**mypy**（成熟、社群大）或 **Pyright/Pylance**（快、VS Code 內建）。加進 CI 才有意義——只在本機跑的檢查等於沒有。

---

## 十、環境與工具

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip freeze > requirements.txt
```

虛擬環境是**必須的**，因為 `pip install` 預設裝到全域，兩個專案要不同版本的同一個套件就會互相踩。`.venv/` 要進 `.gitignore`。

現代專案常用 `uv` 取代 pip（快一個數量級，有 `uv.lock` 真正鎖版本），指令是 `uv add x` / `uv run ...`。

工具鏈建議：

| 用途 | 工具 | 說明 |
| --- | --- | --- |
| Lint + Format | **ruff** | 一個工具取代 flake8 + isort + black，快很多 |
| 型別檢查 | mypy 或 Pyright | 加進 CI |
| 測試 | pytest | 見 [[10-testing]] |
| 相依管理 | pip + requirements.txt，或 uv | |

`ruff` 幾乎是目前的預設答案，一個設定檔搞定風格與靜態檢查。

---

## 十一、常見誤解

**「型別提示會做檢查。」**
直譯器完全忽略它們。`def add(a: int)` 傳字串進去不會有任何錯誤。是 mypy/Pyright 這類外部工具，或 FastAPI 這類主動讀 `__annotations__` 的框架，才讓它們產生效果。

**「`if not x` 就是檢查 None。」**
`0`、`""`、`[]`、`False` 全部都會進去。判斷 None 一律用 `is None`。這是最高頻的邏輯 bug 來源之一。

**「`b = a.copy()` 就複製好了。」**
那是淺拷貝，巢狀的內容仍然共用。要完全獨立得用 `copy.deepcopy()`。

**「預設參數寫 `= []` 沒問題。」**
預設值在 `def` 執行時求值**一次**，所有呼叫共用同一個 list。用 `= None` 再在函式內建立。

**「雙底線是 private。」**
那是 name mangling（`__x` 變成 `_ClassName__x`），目的是避免子類別意外覆蓋，不是存取控制。Python 沒有 private，封裝靠紀律。

**「多重繼承很方便。」**
MRO 的規則在繼承圖稍微複雜之後就沒人說得清楚。除非在寫框架，用組合。

**「讀檔不用管編碼。」**
Windows 上不指定 `encoding="utf-8"` 會用系統預設（cp950），讀中文直接出事。`open()` 一律明寫編碼。

---

## 十二、同事會來問你的問題

**「Python 的變數和 C# 差在哪？」**
Python 沒有值型別，所有東西都是物件，變數是貼在物件上的名牌。`b = a` 不是複製而是多一張名牌。感覺不出來是因為 `int`、`str`、`tuple` 不可變——不可變加上參考語意，解釋了 Python 大部分看起來奇怪的行為。

**「怎麼做介面？」**
duck typing——不看型別只看有沒有那個方法。需要靜態檢查得到的契約就用 `typing.Protocol`（結構化型別，不需要明確繼承），但它只在型別檢查時生效，執行期不強制。

**「`7 / 2` 為什麼是 3.5？」**
Python 的 `/` 永遠回傳 float，取整除法要用 `//`。忘了改的典型症狀是 `TypeError: list indices must be integers`。

**「為什麼這個函式第二次呼叫時保留了上次的資料？」**
可變預設參數。`def f(x, bucket=[])` 的 `[]` 在 `def` 執行時建立一次，所有呼叫共用。改成 `bucket=None` 再在函式內建立。

**「例外用來做流程控制不會很慢嗎？」**
Python 的慣例是 EAFP（先做，錯了再處理），例外成本相對低，而且沒有 check-then-act 的競態問題。用例外處理預期中的失敗在 Python 是正常的——但仍然要接具體型別，不要 `except Exception` 全包，更不要 `except: pass`。

**「型別提示到底要不要寫？」**
超過玩具規模就要，而且要把 mypy 或 Pyright 加進 CI。C# 的重構由編譯器保證，Python 沒有那層保護——型別檢查加測試是唯一的替代品。

---

## 生態定位

| 領域 | 主流選擇 |
| --- | --- |
| Web API | **FastAPI** → [[python-fast-api]]、Django、Flask |
| 資料處理 | pandas、polars |
| 科學運算 | NumPy、SciPy |
| 自動化腳本 | 標準庫 + `pathlib`、`subprocess` |
| 桌面 GUI | tkinter（標準庫）、PyQt |

Python 在**膠水程式碼**與**資料**這兩塊有壓倒性優勢；重運算靠 C 擴充（NumPy 那類會釋放 GIL 的函式庫）；高併發服務要理解 event loop 的限制（見 [[04-async-and-concurrency]]）。

---

## Raw 來源

本頁第二到四節的事實基礎來自這批 2020 年課程筆記，需要更多入門級範例時可直接看原文：

- [[Python]] — 主索引
- [[第一部分：數字、字串與變數]]、[[Python 運算子]] — 型別與運算子
- [[串列(List)]]、[[Tuple]]、[[字典(dictionary)]]、[[集合(Set)]] — 四大容器的完整方法清單
- [[第三部分：程式結構]] — 控制流程與生成式
- [[第一堂(2020 3 3)]]、[[第二堂(2020 3 10)]] — 課程流水記錄
- [[GUI套件-tkinter]]、[[常見GUI介面]] — 桌面 GUI（與目前技術路線無關，保留指標）

---

## 連結

- [[python-fast-api]] — 用 Python 寫後端 API 的完整教材
- [[csharp]] — 對照組
- [[typescript]] — 另一個「有型別註解但執行期不強制」的語言，處境類似
- [[docker]] — Python 服務的容器化（不要用 alpine，見 [[11-deployment]]）
