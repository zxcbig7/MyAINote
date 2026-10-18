---
type: concept
domain: tech
tags: [csharp, dotnet, syntactic-sugar, compiler, lowering, roslyn]
sources: []
created: 2026-10-18
updated: 2026-10-18
---

> **一句話**：語法糖（syntactic sugar）是「不增加語言能力、只讓寫法更短更好讀」的語法。編譯器會在型別檢查之後，把它依固定規則改寫（lowering）成更基本的等價程式碼，所以用糖的版本和手寫展開的版本，產出的 IL 完全一樣。

## 導讀

寫 C# 一段時間後，程式碼裡會充滿各種簡寫：`=>`、`?.`、`??`、`$""`、`using var`、`foreach`。它們用起來很順手，但如果被問到「這行到底等於什麼」，很多人只能回答「大概就是那個意思」。這份筆記要把那個「大概」變成「精確」。

本篇預設你已經會寫基本的 C#（class、method、property、lambda），但沒想過編譯器在背後幫你做了多少事。讀完之後，你應該能做到五件事：說清楚語法糖的定義與判斷標準；把常見的 C# 語法糖還原成展開後的寫法；分辨哪些功能是糖、哪些是真正需要 runtime 支援的新能力；知道糖背後藏著哪些效能成本與行為陷阱；以及自己動手看到編譯器改寫後的結果。

章節由淺入深：先建立定義與判斷標準，再從 expression-bodied member 這個最單純的例子切入，接著逐類拆解常見語法糖，然後進入編譯器會生成整個 class 的「重度語法糖」，再對照「不是糖」的功能，最後以實務陷阱與速查表收尾。

## 一、什麼是語法糖

「語法糖」這個詞由英國電腦科學家 Peter Landin 在 1964 年提出。他當時研究如何用 lambda calculus 描述程式語言，發現 ALGOL 一類語言裡的 `where`、`let` 寫法，其實都能翻譯成最基本的函式定義與呼叫。這些寫法沒有讓語言多做到什麼，只是讓人讀寫起來比較「甜」，因此稱為 sugar。

精確地說，語法糖是滿足這個條件的語法：**編譯器能依照固定規則，把它改寫成語言中既有的、更基本的寫法，而且改寫前後的意義完全相同。** 這個改寫過程叫 **desugaring**，在編譯器實作裡通常稱為 **lowering**，意思是把高階結構「降」成低階結構。

C# 編譯器 Roslyn 處理一份原始碼的流程大致如下：

```text
原始碼 → Parser → Syntax Tree → Binding（名稱解析、型別檢查）→ Bound Tree → Lowering（拆糖）→ 只剩基本結構的 Bound Tree → Emit IL → 執行時 JIT → 機器碼
```

這個流程有兩個值得注意的地方。第一，lowering 發生在型別檢查**之後**，所以編譯錯誤永遠以你寫的原始語法回報，不會出現「展開後第 37 行有錯」這種訊息。第二，lowering 結束後糖就徹底消失了，IL 裡沒有任何「這裡原本是 `?.`」的痕跡。這就是為什麼說語法糖沒有執行期差異：手寫展開版和用糖的版本，IL 一模一樣。

既然執行起來沒差，語法糖的價值就在**人**身上。程式碼被讀的次數遠多於被寫的次數，糖把反覆出現的樣板（boilerplate）壓縮掉，讓讀者一眼看見意圖，而不是被 `try` / `finally`、null 檢查、暫存變數淹沒。

## 二、怎麼判斷一個語法是不是糖

定義聽起來簡單，實際判斷時卻常卡住，例如「`async/await` 算糖嗎？」「泛型算糖嗎？」。下面三個問題可以當作檢查清單：

| 判斷問題 | 回答「是」代表 |
|---|---|
| 能不能用語言既有的其他語法，手寫出完全等價的程式碼？ | 傾向是糖 |
| 這個改寫是否只需看局部程式碼、套固定規則就能完成？ | 是「輕度」糖 |
| 拿掉這個語法後，有沒有任何事情變得**做不到**（而不只是變囉嗦）？ | 不是糖 |

第二個問題區分了糖的輕重。像 `a ?? b` 這種，只看這一個 expression 就能改寫，屬於輕度糖。lambda 閉包、`yield return`、`async/await` 雖然也是編譯器改寫，但改寫範圍會擴及整個 method，甚至生成全新的 class，這類通常稱為**重度語法糖**，也有人乾脆把它們歸為語言功能。兩種說法都有道理，重點是看清它們的本質：**都是編譯期改寫，執行期沒有特殊支援。**

第三個問題是最終判準。真正的「新功能」需要 runtime（CLR）本身提供新的能力，例如泛型、預設介面方法，這類功能光靠編譯器翻譯無法完成，第六章會詳細對照。

還有一個常被混淆的點：語法糖可以**依賴某個型別存在**，但仍然是糖。`foreach` 需要呼叫 `GetEnumerator()`，`async` 需要 `Task` 與 `AsyncTaskMethodBuilder`。這些只是函式庫裡的普通型別，編譯器把糖改寫成「呼叫這些型別的 method」，runtime 不需要認識任何新規則。

## 三、從一個例子開始：expression-bodied member

先看一個最單純、也最常見的例子：

```csharp
public Order CreateDraft(Customer customer, OrderOptions? options = null) =>
    Create(customer, OrderKind.Draft, null, options);
```

這是 C# 6 引入的 **expression-bodied member**，完全等價於只有一行 `return` 的一般 method：

```csharp
public Order CreateDraft(Customer customer, OrderOptions? options = null)
{
    return Create(customer, OrderKind.Draft, null, options);
}
```

規則只有一條：`=>` 右邊必須是**單一 expression**，它的值就是回傳值。如果 method 回傳 `void`，右邊的 expression 就只是被執行，不回傳任何東西：

```csharp
public void Log(string message) => Console.WriteLine(message);
```

一旦需要兩個以上的 statement，例如宣告區域變數、`if`、`try`、迴圈，就必須回到 `{ }` 的 block body。

### 它不是 lambda

`=>` 這個符號也用在 lambda（`x => x * 2`），所以初學者常以為 expression-bodied member 是「把 lambda 指派給 method」。這是錯的。lambda 會產生 delegate 物件，捕捉變數時還會產生閉包；expression-bodied member 只是 method 宣告的另一種寫法，編譯後就是一個普通 method，沒有 delegate，也沒有額外配置。兩者只是共用了同一個符號。

### 哪些成員可以這樣寫

| 成員 | 寫法 | 等價於 | 起始版本 |
|---|---|---|---|
| Method | `int Square(int x) => x * x;` | `{ return x * x; }` | C# 6 |
| 唯讀 property | `string Name => _name;` | `{ get { return _name; } }` | C# 6 |
| 唯讀 indexer | `int this[int i] => _items[i];` | `{ get { return _items[i]; } }` | C# 6 |
| Operator | `static Money operator +(Money a, Money b) => new Money(a.Value + b.Value);` | `{ return new Money(...); }` | C# 6 |
| Constructor | `Point(int x) => X = x;` | `{ X = x; }` | C# 7.0 |
| Finalizer | `~Resource() => Release();` | `{ Release(); }` | C# 7.0 |
| get / set accessor | `string Name { get => _name; set => _name = value; }` | 各自的 block body | C# 7.0 |

### 什麼時候用、什麼時候不用

expression-bodied member 適合**一眼就能看完**的成員：轉呼叫（forwarding）、簡單計算、回傳欄位。它讓類別裡「薄」的成員看起來就是薄的，讀者可以快速掃過。

反過來，如果右邊的 expression 長到要折好幾行，或塞了巢狀三元運算子，硬用 `=>` 只會讓程式碼更難讀，也更難下中斷點（偵錯器在單一 expression 裡能停的位置比較少）。這時候老老實實寫 block body 才是對的。

### 最常見的陷阱：`=>` 和 `=` 只差一個字元

```csharp
public List<string> Tags => new List<string>(); // 每次讀取都建立新的 List
public List<string> Tags { get; } = new List<string>(); // 只在建構時建立一次
```

第一行是 expression-bodied property，**每次讀取都會重新執行右邊的 expression**；第二行是 auto-property 加初始值，只在物件建構時執行一次。寫成第一種的話，`obj.Tags.Add("a")` 加進去的是一個用完即丟的 List，下一次讀 `obj.Tags` 永遠是空的。這個 bug 沒有任何編譯錯誤或警告，只能靠理解語法本身來避免。

理解了最單純的糖之後，下一章把 C# 裡常見的糖逐類拆開。

## 四、C# 常見語法糖拆解

每個例子都分成「你寫的」與「編譯器改寫後的」兩段。改寫後的程式碼是概念上的等價寫法；實際上編譯器會使用 `<>c__DisplayClass` 這類 C# 不允許的名稱，以免和你的變數撞名。

### Null 相關：`??`、`?.`、`??=`

```csharp
var name = input ?? "unknown";
```

```csharp
var tmp = input;
var name = tmp != null ? tmp : "unknown";
```

注意暫存變數 `tmp`：左邊的 expression **只會被評估一次**。如果左邊是 `GetInput()`，它不會因為你用了 `??` 而被呼叫兩次。

`?.`（null-conditional operator）也是同樣的道理：

```csharp
var length = customer?.Name.Length;
```

```csharp
var tmp = customer;
int? length = tmp == null ? (int?)null : tmp.Name.Length;
```

這裡有兩件事要留意。第一，`?.` 會讓整條成員存取鏈「短路」：`customer` 為 null 時，後面的 `.Name.Length` 全部跳過，不會拋例外；但如果是 `Name` 本身為 null，`.Length` 照樣會拋 `NullReferenceException`，要寫成 `customer?.Name?.Length` 才能一路保護。第二，原本回傳 `int` 的成員，經過 `?.` 之後型別變成 `int?`，因為結果必須能表達「沒有值」。

`??=`（C# 8）則是「為 null 時才指派」：

```csharp
_cache ??= LoadCache();
```

```csharp
if (_cache == null)
{
    _cache = LoadCache();
}
```

### 宣告相關：`var`、auto-property、initializer、`int?`

`var` 是編譯期的型別推論，不是動態型別：

```csharp
var count = 10;
var users = new List<User>();
```

```csharp
int count = 10;
List<User> users = new List<User>();
```

編譯完成後 `count` 就是 `int`，之後不能再指派字串。這是它和 JavaScript 的 `var`、C# 的 `dynamic` 最大的不同。

Auto-property 讓你不必手寫 backing field：

```csharp
public string Name { get; set; }
```

```csharp
private string _name; // 實際名稱是 <Name>k__BackingField
public string Name
{
    get { return _name; }
    set { _name = value; }
}
```

Object initializer 讓建立物件與設定屬性寫在一起：

```csharp
var user = new User { Name = "Amy", Age = 30 };
```

```csharp
var tmp = new User();
tmp.Name = "Amy";
tmp.Age = 30;
var user = tmp;
```

這裡的暫存變數同樣有意義：如果某個 setter 拋出例外，`user` 永遠不會指向一個只設定一半的物件。Collection initializer 是同類的糖，`new List<int> { 1, 2, 3 }` 會被改寫成建立 List 之後連續呼叫三次 `Add`，所以任何實作 `IEnumerable` 且有 `Add` method 的型別都能這樣寫。

最後是 `int?`，它只是 `Nullable<int>` 的別名：

```csharp
int? age = null;
```

```csharp
Nullable<int> age = new Nullable<int>();
```

這裡要特別小心一個常見誤解：**`string?` 和 `int?` 完全是兩回事**。`int?` 會變成另一個型別 `Nullable<int>`；`string?`（C# 8 的 nullable reference types）編譯後仍然是 `string`，只多了一個給編譯器看的 attribute。它只會讓編譯器發出警告，執行期沒有任何檢查，第九章會再談這個差異造成的陷阱。

### 流程相關：`foreach`、`using`、`lock`

`foreach` 是最經典的糖之一：

```csharp
foreach (var item in items)
{
    Process(item);
}
```

```csharp
var e = items.GetEnumerator();
try
{
    while (e.MoveNext())
    {
        var item = e.Current;
        Process(item);
    }
}
finally
{
    e.Dispose(); // enumerator 有實作 IDisposable 才會產生
}
```

`foreach` 的改寫是 **pattern-based** 的：編譯器只找「有沒有 `GetEnumerator()` method、它回傳的東西有沒有 `MoveNext()` 和 `Current`」，並不要求型別實作 `IEnumerable`。另外，如果走訪的對象是陣列，編譯器會直接改寫成用索引的 `for` 迴圈，完全不配置 enumerator。

`using` 確保資源一定被釋放：

```csharp
using (var reader = new StreamReader(path))
{
    Read(reader);
}
```

```csharp
var reader = new StreamReader(path);
try
{
    Read(reader);
}
finally
{
    if (reader != null)
    {
        ((IDisposable)reader).Dispose();
    }
}
```

C# 8 的 `using var reader = ...;` 是同一套改寫，差別只在 `try` 的範圍一路延伸到**所在區塊的結尾**。

`lock` 則是 `Monitor` 的包裝：

```csharp
lock (_gate)
{
    Work();
}
```

```csharp
bool lockTaken = false;
try
{
    Monitor.Enter(_gate, ref lockTaken);
    Work();
}
finally
{
    if (lockTaken)
    {
        Monitor.Exit(_gate);
    }
}
```

C# 13 起，如果 `_gate` 的型別是 .NET 9 新增的 `System.Threading.Lock`，編譯器會改用 `_gate.EnterScope()` 搭配 `using` 的形式。同一個語法依型別改寫成不同結果，正好說明語法糖就是一組翻譯規則。

### 字串相關：`$""` 字串插值

```csharp
var message = $"Hi {name}, you are {age}";
```

C# 6 到 C# 9 會改寫成 `string.Format("Hi {0}, you are {1}", name, age)`，其中 `age` 是 `int`，必須裝箱（boxing）成 `object` 才能傳進去。C# 10 搭配 .NET 6 以上，改寫方式換成 `DefaultInterpolatedStringHandler`：

```csharp
var handler = new DefaultInterpolatedStringHandler(13, 2);
handler.AppendLiteral("Hi ");
handler.AppendFormatted(name);
handler.AppendLiteral(", you are ");
handler.AppendFormatted(age);
var message = handler.ToStringAndClear();
```

原始碼一個字都沒改，只是換新版編譯器重新編譯，就少掉了裝箱與中間配置。這是語法糖的另一個好處：**改寫規則可以隨編譯器進步而更有效率**，使用者不必改程式碼。

### 呼叫相關：extension method、LINQ query syntax

Extension method 讓靜態 method 看起來像實例 method：

```csharp
public static class StringExtensions
{
    public static bool IsBlank(this string? s) => string.IsNullOrWhiteSpace(s);
}

var blank = title.IsBlank();
```

```csharp
var blank = StringExtensions.IsBlank(title);
```

因為本質是靜態呼叫，`title` 為 null 時呼叫端**不會**拋 `NullReferenceException`，null 會被直接當成參數傳進去。這有時是好處（如上例），有時則會讓錯誤延後到 method 內部才爆出來。

LINQ 的 query syntax 則是 method chain 的糖：

```csharp
var emails =
    from u in users
    where u.IsActive
    orderby u.Name
    select u.Email;
```

```csharp
var emails = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.Name)
    .Select(u => u.Email);
```

它同樣是 pattern-based：任何型別只要有對應名稱的 `Where`、`Select` 等 method，就能使用 query syntax。

### 其他常見的糖

| 你寫的 | 編譯器改寫成 | 版本 |
|---|---|---|
| `(string Name, int Age) p = ("Amy", 30);` 與 `p.Name` | `ValueTuple<string, int>` 與 `p.Item1` | C# 7.0 |
| `var (name, age) = p;` | `var name = p.Item1; var age = p.Item2;`（或呼叫 `Deconstruct`） | C# 7.0 |
| `if (obj is User u)` | 型別檢查 + 轉型 + 指派給 `u` | C# 7.0 |
| `x switch { 1 => "a", _ => "b" }` | `if` 鏈或 `switch` 跳躍表 | C# 8 |
| `arr[^1]` | `arr[arr.Length - 1]` | C# 8 |
| `nameof(User.Name)` | 編譯期常數字串 `"Name"` | C# 6 |
| `a + b + c`（皆為 string） | `string.Concat(a, b, c)` | C# 1 |

Tuple 那一列特別值得記住：`Name`、`Age` 這些欄位名稱**只存在於編譯期**，執行期只有 `Item1`、`Item2`，這在序列化時會造成意外（見第九章）。

以上都是只改寫局部程式碼的輕度糖。接下來的幾個功能，編譯器得生成整個新的 class 才能完成。

## 五、重度語法糖：編譯器替你寫了一整個 class

### Lambda 與閉包

沒有捕捉外部變數的 lambda 很單純，編譯器把它變成一個私有 method，再快取一個指向它的 delegate。真正有趣的是**捕捉了外部變數**的 lambda：

```csharp
int threshold = 10;
Func<int, bool> isLarge = x => x > threshold;
```

```csharp
sealed class Closure // 實際名稱是 <>c__DisplayClass0_0
{
    public int threshold;
    public bool Invoke(int x) => x > threshold;
}

var closure = new Closure();
closure.threshold = 10;
Func<int, bool> isLarge = closure.Invoke;
```

區域變數 `threshold` 被提升（hoist）成閉包物件的欄位，method 裡之後所有對 `threshold` 的讀寫，其實都在存取 `closure.threshold`。這解釋了兩件事：第一，lambda 捕捉的是**變數本身**而不是當下的值，之後修改 `threshold`，lambda 看到的也會跟著變；第二，閉包要在 heap 上配置一個物件，在高頻呼叫的路徑上會增加 GC 壓力。C# 9 的 `static` lambda（`static x => x > 10`）可以讓編譯器保證不捕捉任何變數。

### `yield return`：iterator

```csharp
IEnumerable<int> Evens(int max)
{
    for (int i = 0; i <= max; i += 2)
    {
        yield return i;
    }
}
```

這個 method 被呼叫時，**裡面的程式碼一行都不會執行**。編譯器會生成一個同時實作 `IEnumerable<int>` 與 `IEnumerator<int>` 的 class，把迴圈拆解成 state machine。簡化後大致如下：

```csharp
sealed class EvensIterator : IEnumerable<int>, IEnumerator<int>
{
    private int _state;
    private int _i;
    public int max;
    public int Current { get; private set; }

    public bool MoveNext()
    {
        switch (_state)
        {
            case 0:
                _i = 0;
                break;
            case 1:
                _i += 2;
                break;
            default:
                return false;
        }

        if (_i <= max)
        {
            Current = _i;
            _state = 1;
            return true;
        }

        _state = -1;
        return false;
    }

    // GetEnumerator、Reset、Dispose 省略
}
```

外部每呼叫一次 `MoveNext()`，state machine 就從上次停下的地方繼續跑到下一個 `yield return`。區域變數 `i` 被提升成欄位，才能在兩次呼叫之間保留狀態。這就是 LINQ「延遲執行」（deferred execution）的底層機制。

### `async` / `await`

`async/await` 是 C# 最重的一顆糖，原理和 iterator 非常相似：

```csharp
async Task<string> LoadAsync(string url)
{
    var html = await _http.GetStringAsync(url);
    return html.Trim();
}
```

編譯器會生成一個實作 `IAsyncStateMachine` 的 struct，以每個 `await` 為切點把 method 拆成數個狀態，區域變數同樣提升成欄位，再由 `AsyncTaskMethodBuilder<string>` 負責建立並完成回傳的 `Task`。執行流程如下：

```text
呼叫 LoadAsync → MoveNext()（狀態 0）→ 遇到未完成的 await → 登記 continuation → 把未完成的 Task 回傳給呼叫端
GetStringAsync 完成 → 觸發 continuation → MoveNext()（狀態 1）→ return → Task 標記為完成
```

正因為它只是編譯期改寫，`async/await` 在 .NET Framework 4.5 上就能使用，runtime 不需要任何特殊支援，只需要 `Task` 這些型別存在。

### `record`

```csharp
public record User(string Name, int Age);
```

這一行會展開成：一個建構式、兩個 `init` property、`Deconstruct`、值相等比較的 `Equals`、`GetHashCode`、`ToString`、`==` 與 `!=` 運算子，以及一個給 `with` expression 用的 clone method。`var older = user with { Age = 31 };` 就是「clone 一份，再設定 `Age`」。手寫這些要四、五十行，而且每次新增欄位都得記得同步修改 `Equals` 與 `GetHashCode`，這正是 record 想消滅的錯誤來源。要注意自動生成的 `Equals` 對集合型別的屬性只比較參考，兩個內容相同的 `List` 不會被視為相等。

語法糖再重，終究是編譯器一手包辦。下一章來看哪些功能是編譯器自己做不到的。

## 六、不是語法糖的功能

### 泛型：runtime 原生支援

C# 的泛型從 .NET Framework 2.0 起就由 CLR 直接支援，稱為 reified generics。`List<int>` 和 `List<string>` 在執行期是兩個不同的型別；遇到 value type 參數，JIT 會產生專屬的機器碼，所以 `List<int>` 存 `int` 完全不用裝箱；`typeof(T)` 在執行期也拿得到真實型別。

對照 Java 會更清楚。Java 的泛型採用 **type erasure**，編譯後 `List<Integer>` 和 `List<String>` 都變成同一個 `List`，元素一律存成 `Object`，編譯器只是在取值處自動插入轉型。所以 Java 不能 `new T()`，也不能 `instanceof List<String>`。從這個角度看，**Java 的泛型反而比較接近語法糖**，C# 的泛型則是真正的 runtime 功能。

### 需要新版 runtime 的語言功能

以下 C# 功能除了編譯器，還需要 CLR 本身的支援，只能在對應版本以上的 runtime 執行：

| 功能 | C# 版本 | 最低 runtime |
|---|---|---|
| 預設介面方法（default interface methods） | C# 8 | .NET Core 3.0 |
| 共變回傳型別（covariant return types） | C# 9 | .NET 5 |
| 介面的 static abstract 成員 | C# 11 | .NET 7 |

這些功能改變的是型別系統本身的規則：介面能不能帶實作、override 能不能換回傳型別。這些規則由 runtime 在載入型別時檢查，編譯器再怎麼改寫也模擬不出來。

### 實務意義：舊專案能用哪些新語法

區分糖與非糖最實際的用途，是判斷**舊 target framework 的專案能不能用新語法**。在 .NET Framework 4.x 專案的 `.csproj` 把 `<LangVersion>` 調高之後（官方不支援這種組合，但實務上很常見），結果如下：

| 語法 | 能否使用 | 原因 |
|---|---|---|
| expression-bodied、`?.`、`??=`、pattern matching、switch expression | 可以 | 純編譯期改寫 |
| nullable reference types | 可以 | 只產生 attribute 與編譯器警告 |
| `record`、`init` | 補 polyfill 後可以 | 編譯器需要 `IsExternalInit` 型別存在 |
| `^1`、`..`（Index / Range） | 補 polyfill 後可以 | 需要 `System.Index`、`System.Range` 型別 |
| 預設介面方法、共變回傳型別、static abstract | 不行 | 需要 runtime 支援，補任何型別都沒用 |

規律很清楚：**糖最多只缺型別，補上就能用；非糖缺的是 runtime 能力，補不了。**

## 七、親眼看到改寫結果

理解語法糖最快的方式，是直接看編譯器改寫後的程式碼。

**SharpLab**（sharplab.io）在瀏覽器打開就能用。左邊貼 C# 程式碼，右邊的 Results 選 `C#`，就會顯示 lowering 後再反編譯回來的 C#；選 `IL` 則顯示 IL。適合快速驗證單一語法。

**ILSpy** 用來反編譯已建置的 dll。圖形介面版可以在工具列把 C# 語言版本調到很舊（例如 C# 1.0），反編譯器就不會把 IL 還原成新語法，你看到的就是拆糖後的樣子。命令列版本如下：

```powershell
dotnet tool install --global ilspycmd
dotnet build
ilspycmd -lv CSharp1 -t MyApp.Services.UserService .\bin\Debug\net8.0\MyApp.dll
```

`-lv` 指定反編譯時使用的語言版本，`-t` 指定只輸出某個型別。把 `CSharp1` 換成 `Latest` 再跑一次，就能對照糖被「還原」回來的樣子。

## 八、語法糖的代價與使用原則

Alan Perlis 在 1982 年的〈Epigrams on Programming〉裡寫過一句名言：

> Syntactic sugar causes cancer of the semicolon.

糖吃多了也會出問題。語法糖本身沒有執行期成本，但它**藏起來的東西**有成本，而且藏得越深越容易被忽略。

第一種代價是**隱藏的配置**。閉包會配置物件；`async` method 遇到真正需要等待的 `await` 時，會把 state machine 搬到 heap；用 `foreach` 走訪一個宣告型別為 `IEnumerable<T>` 的 `List<T>` 時，原本是 struct 的 enumerator 會被裝箱；LINQ 每串一個運算子就多一層 iterator 物件。這些成本在一般商業邏輯裡微不足道，但在每秒執行百萬次的熱路徑上就值得注意。

第二種代價是**隱藏的語意**。`yield` 讓程式碼延後執行、`?.` 讓型別悄悄變成 nullable、`using var` 讓資源活到區塊結尾。寫的人如果不知道展開後的樣子，就會寫出看起來正確、實際上有 bug 的程式碼。

因此使用語法糖有三個原則：

1. **能還原才用**：用任何一顆糖之前，你應該能在腦中把它展開。展開不了，代表你還不清楚它的成本與邊界。
2. **以可讀性為準**：糖的目的是讓意圖更清楚。如果用了之後反而要多讀兩遍，就不要用。
3. **團隊統一**：同一個專案裡要不要用 expression-bodied、`var` 用在哪裡，應該靠 `.editorconfig` 統一，而不是每個人各寫各的。

```ini
[*.cs]
csharp_style_expression_bodied_methods = when_on_single_line:suggestion
csharp_style_expression_bodied_properties = true:suggestion
csharp_style_var_when_type_is_apparent = true:suggestion
```

## 九、常見問題排查

### 新語法編譯失敗：Feature is not available

**錯誤訊息**

```text
error CS8370: Feature 'nullable reference types' is not available in C# 7.3. Please use language version 8.0 or greater.
```

錯誤代碼會隨版本不同（CS8107、CS8370、CS8400 等），訊息格式相同。

**原因**：每個 target framework 都有預設的 C# 版本。.NET Framework 專案預設 C# 7.3，.NET 8 是 C# 12，.NET 9 是 C# 13，.NET 10 是 C# 14。語法糖雖然不需要 runtime 支援，但需要認得它的編譯器版本。

**解法**：優先升級 target framework；若無法升級，在 `.csproj` 指定語言版本，並先對照第六章的表，確認要用的功能不需要 runtime 支援。

```xml
<PropertyGroup>
  <LangVersion>12.0</LangVersion>
</PropertyGroup>
```

### record / init 在舊專案找不到型別

**錯誤訊息**

```text
error CS0518: Predefined type 'System.Runtime.CompilerServices.IsExternalInit' is not defined or imported
```

**原因**：`init` accessor 在編譯時需要一個標記型別 `IsExternalInit`，它只存在於 .NET 5 以上的 BCL。

**解法**：自己宣告一個同名型別即可，編譯器只檢查它是否存在。也可以改裝 `PolySharp` 這類 polyfill 套件，一次補齊多個型別。

```csharp
namespace System.Runtime.CompilerServices
{
    internal static class IsExternalInit { }
}
```

### 集合屬性加了元素卻一直是空的

**症狀**：`obj.Items.Add(x)` 之後，`obj.Items.Count` 仍然是 0，沒有任何錯誤或警告。

**原因**：屬性寫成 `public List<T> Items => new List<T>();`，expression-bodied property 每次讀取都建立新的 List。

**解法**：改成 `public List<T> Items { get; } = new List<T>();`。

### 迴圈裡建立的 lambda 都拿到同一個值

**症狀**：

```csharp
var actions = new List<Action>();
for (int i = 0; i < 3; i++)
{
    actions.Add(() => Console.WriteLine(i));
}
actions.ForEach(a => a()); // 印出 3、3、3
```

**原因**：閉包捕捉的是變數 `i` 本身，三個 lambda 共用同一個閉包物件，執行時 `i` 已經是 3。`foreach` 的迴圈變數從 C# 5 起每一輪都是新變數，沒有這個問題；`for` 仍然有。

**解法**：在迴圈內複製一份區域變數，讓每一輪各自捕捉自己的變數。

```csharp
for (int i = 0; i < 3; i++)
{
    var copy = i;
    actions.Add(() => Console.WriteLine(copy));
}
```

### `await obj?.MethodAsync()` 拋出 NullReferenceException

**錯誤訊息**

```text
System.NullReferenceException: Object reference not set to an instance of an object.
```

**原因**：`obj` 為 null 時，`obj?.MethodAsync()` 的結果是 null 的 `Task`，而 `await null` 必然拋例外。`?.` 保護了呼叫，沒有保護 `await`。

**解法**：

```csharp
if (obj != null)
{
    await obj.MethodAsync();
}
```

### iterator 的參數檢查沒有在呼叫時觸發

**症狀**：`var evens = Evens(-1);` 沒有拋例外，直到 `foreach` 開始走訪才拋出 `ArgumentOutOfRangeException`。

**原因**：含 `yield return` 的 method 整個被改寫成 state machine，連開頭的參數檢查也一起延後到第一次 `MoveNext()` 才執行。

**解法**：拆成「立即檢查參數的外層 method」與「負責 yield 的 local function」。

```csharp
public IEnumerable<int> Evens(int max)
{
    ArgumentOutOfRangeException.ThrowIfNegative(max);
    return Iterate();

    IEnumerable<int> Iterate()
    {
        for (int i = 0; i <= max; i += 2)
        {
            yield return i;
        }
    }
}
```

### Tuple 序列化後欄位名稱不見了

**症狀**：API 回傳 `(string Name, int Age)`，`System.Text.Json` 輸出 `{}`；換成 Newtonsoft.Json 則輸出 `{"Item1":"Amy","Item2":30}`。

**原因**：tuple 的欄位名稱只存在於編譯期，執行期只有 `Item1`、`Item2`；而且它們是 field 而不是 property，`System.Text.Json` 預設不序列化 field。

**解法**：對外的資料結構一律用 `record` 或 class，tuple 只用在 method 內部或私有 helper 的回傳值。

### `using var` 讓檔案被鎖住太久

**錯誤訊息**

```text
System.IO.IOException: The process cannot access the file '...' because it is being used by another process.
```

**原因**：`using var` 的 `Dispose` 要到所在區塊結尾才執行。同一個 method 稍後再開同一個檔案時，前一個 stream 還沒釋放。

**解法**：需要提早釋放時改回 `using (...) { }` 區塊寫法，或把讀檔抽成獨立 method。

### 宣告成 `string?` 卻還是拋 NullReferenceException

**症狀**：編譯時只看到警告 `CS8602: Dereference of a possibly null reference.`，執行期照樣拋 `NullReferenceException`。

**原因**：nullable reference types 只是編譯期的註記，`string?` 編譯後仍是 `string`，runtime 不做任何檢查。它和真的會變成 `Nullable<int>` 的 `int?` 完全不同。

**解法**：把 nullable 警告升級為錯誤（`<WarningsAsErrors>nullable</WarningsAsErrors>`），並且在對外邊界（API 輸入、反序列化結果）仍然做 null 驗證。

## 十、速查表

| 項目 | 重點 |
|---|---|
| 語法糖 | 不增加語言能力、只讓寫法更短的語法 |
| lowering / desugaring | 編譯器在型別檢查後把糖改寫成基本寫法，IL 和手寫展開版相同 |
| 判斷標準 | 能用既有語法手寫出等價程式碼，拿掉後沒有任何事情做不到 |
| 重度語法糖 | lambda 閉包、`yield`、`async/await`、`record`：會生成整個 class |
| 不是糖 | 泛型、預設介面方法、共變回傳型別、static abstract：需要 runtime 支援 |
| `M() => expr;` | `M() { return expr; }`，不是 lambda |
| `Prop => new X()` vs `Prop { get; } = new X()` | 前者每次讀取都建新物件，後者只建一次 |
| `a ?? b` | `tmp != null ? tmp : b`，左邊只評估一次 |
| `a?.B` | `tmp == null ? null : tmp.B`，結果型別變成 nullable |
| `x ??= y` | `if (x == null) x = y;` |
| `var` | 編譯期推論出的具體型別，不是動態型別 |
| `{ get; set; }` | 編譯器生成 backing field |
| `new T { A = 1 }` | 暫存變數 + 逐一設定屬性 |
| `int?` / `string?` | 前者是 `Nullable<int>`，後者只是編譯期註記 |
| `foreach` | `GetEnumerator` + `while (MoveNext())` + `Dispose`；陣列改成 `for` |
| `using` | `try` / `finally` + `Dispose` |
| `lock` | `Monitor.Enter` / `Monitor.Exit` 包在 `try` / `finally` |
| `$"..."` | C# 10 起改用 `DefaultInterpolatedStringHandler`，避免裝箱 |
| extension method | 靜態 method 呼叫，null 接收者不會在呼叫端拋例外 |
| tuple 欄位名稱 | 只存在編譯期，執行期是 `Item1`、`Item2` |
| 看改寫結果 | SharpLab、ILSpy（把語言版本調低） |

## 連結

- [[csharp]] — C# 語法總覽，本篇深入其中各種簡寫背後的改寫規則
- [[languages-moc]] — 程式語言主題入口
- [[web-backend-moc]] — .NET / C# 後端主題入口
- [[03-routing-and-endpoints]] — 拆解「Minimal API 只是語法糖」這個常見誤解
- [[unit-testing-sop]] — record 含集合屬性時的相等性陷阱
- [[進階語法]] — `??` 運算子的原始筆記
- [[using 陳述式]] — `using` 的原始筆記
- [[列舉器(IEnumerable)]] — `IEnumerable` 與 `foreach` 的原始筆記
