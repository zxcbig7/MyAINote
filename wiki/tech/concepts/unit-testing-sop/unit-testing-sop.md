---
type: concept
domain: tech
tags: [testing, xunit, dotnet, csharp, sop, tdd]
sources: []
created: 2026-09-02
updated: 2026-09-02
---

## 這份筆記解決什麼

`dotnet new xunit` 產生一個空專案，裡面有個叫 `UnitTest1` 的空方法，然後你卡住：不知道要測什麼、不知道測試長什麼樣、不知道什麼情況該用什麼寫法。

這份筆記只講兩件事：**照著做的 SOP**，以及**遇到什麼狀況用哪一招的對照表**。原理只講到夠用為止。

---

## 一、先建立唯一的心智模型：測試就是三段

一個測試永遠是這三段，沒有例外。業界叫它 **AAA**：

```csharp
[Fact]
public void Add_TwoPositiveNumbers_ReturnsSum()
{
    var calculator = new Calculator();     // Arrange：準備輸入

    var result = calculator.Add(2, 3);     // Act：呼叫一次受測方法

    Assert.Equal(5, result);               // Assert：驗證結果
}
```

用空行把三段隔開，你的測試就永遠可讀。三段各自的規矩：

| 段落 | 做什麼 | 規矩 |
|---|---|---|
| Arrange | 準備輸入資料、建立受測物件 | 值一律寫死，不要算出來 |
| Act | 呼叫受測方法 | **只有一行**，只呼叫一次 |
| Assert | 驗證結果 | 只驗**一個行為** |

`Assert.Equal` 的參數順序是 `(預期, 實際)`，寫反了不會錯但失敗訊息會反過來，會看得很混亂。

---

## 二、SOP A：建立測試專案（整個 repo 只做一次）

```powershell
# 1. 在 repo 內建立測試專案（注意：要在 repo 裡面，不要建在 repo 外）
dotnet new xunit -o tests/MyProject.Tests

# 2. 加進 solution
dotnet sln add tests/MyProject.Tests/MyProject.Tests.csproj

# 3. 讓測試專案看得到主專案
dotnet add tests/MyProject.Tests/MyProject.Tests.csproj reference src/MyProject/MyProject.csproj

# 4. 確認能跑（此時 0 個測試，但要是綠的）
dotnet test
```

三個**建完馬上要檢查**的地方，這三件事錯了後面寫再多測試都跑不起來：

| 檢查項 | 為什麼 |
|---|---|
| 測試專案在 git repo 內 | CI 只 checkout repo，solution 若指向 repo 外的路徑，CI 一 build 就失敗 |
| 測試專案的 `TargetFramework` 與主專案相容 | 測試專案的 TFM 不能比主專案舊 |
| CI 安裝的 SDK 版本涵蓋測試專案的 TFM | CI 裝 8.0.x 卻有 net10.0 專案 → restore 直接死 |

最後刪掉範本產生的 `UnitTest1.cs`，改成**一個受測類別對一個測試檔**：

```text
src/MyProject/Services/PriceCalculator.cs
tests/MyProject.Tests/Services/PriceCalculatorTests.cs
```

測試檔的資料夾結構鏡射原始碼結構，找測試不用想。

---

## 三、SOP B：寫一個測試（每次都跑這五步）

**第 1 步 — 挑一個「行為」，不是挑一個「方法」**

不要想「我要測 `Add` 這個方法」，要想「我要測 `Add` 遇到負數時會怎樣」。一個方法通常對應多個測試。

**第 2 步 — 用行為當名字**

格式固定：`方法_情境_預期結果`

```text
Add_TwoPositiveNumbers_ReturnsSum
Add_ResultOverflowsInt_ThrowsOverflowException
GetById_IdNotFound_ReturnsNull
Parse_EmptyInput_ReturnsEmptyList
```

名字會直接印在測試報告與 CI 上。叫 `Test1` 的話，CI 紅了你得點進去才知道壞在哪。

**第 3 步 — 輸入寫死**

```csharp
var input = "2026-09-02";                    // 好：一眼看出測什麼
var input = DateTime.Now.ToString("d");      // 壞：明天結果就變了
```

測試不可以依賴現在時間、亂數、機器環境、網路。這些一旦進來，測試就會「有時候紅」——那比沒有測試更糟。

**第 4 步 — Act 只有一行**

如果你需要呼叫三次才能驗證，代表你其實想測三個行為，拆成三個測試。

**第 5 步 — Assert 只驗一件事**

```csharp
// 壞：紅了不知道哪個壞
Assert.Equal(3, result.Count);
Assert.Equal("A", result[0].Name);
Assert.True(result[0].IsActive);

// 好：拆成三個測試，各自有名字
```

例外：驗證「同一個行為的完整樣貌」時可以多行，例如驗一個座標的 X 和 Y。判準是「這幾條會不會同時失敗」——會，就留在一起。

---

## 四、SOP C：跑測試

```powershell
dotnet test                                              # 全部跑
dotnet test --filter "FullyQualifiedName~PriceCalculatorTests"   # 只跑一個類別
dotnet test --filter "DisplayName~Overflow"              # 名字含關鍵字的
dotnet test --logger "console;verbosity=detailed"        # 看每個測試的名字與結果
```

紅燈時先看兩行：**哪個測試名字**、**Expected / Actual 差在哪**。xUnit 的失敗訊息會直接印出這兩者，所以斷言要用對的 API（見第六節），用錯的話只會得到 `Assert.True() Failure` 這種毫無資訊的訊息。

---

## 五、測試情境對照表 ★

這是本篇的核心。遇到狀況先查這張表，再看下面對應小節。

| 你面對的狀況 | 用哪一招 | 關鍵 API |
|---|---|---|
| 固定輸入 → 固定輸出 | 單一案例 | `[Fact]` + `Assert.Equal` |
| 同一段邏輯要試很多組資料 | 參數化 | `[Theory]` + `[InlineData]` |
| 參數不是常數（物件、集合、enum 陣列） | 參數化（資料來源版） | `[Theory]` + `[MemberData]` + `TheoryData` |
| 有一條規則「不管輸入什麼都成立」 | 不變式測試 | 用迴圈驗性質，不寫預期輸出 |
| 壞輸入**不可以**讓程式爆炸 | 不爆炸測試 | `Record.Exception` + `Assert.Null` |
| 壞輸入**應該**要丟例外 | 例外測試 | `Assert.Throws<T>` |
| 回傳是集合 | 集合斷言 | `Assert.Single` / `Assert.Contains` / `Assert.Empty` |
| 回傳是巢狀物件或樹狀結構 | 逐層剝型別 | `Assert.IsType<T>` |
| 回傳是一大段文字（報表、序列化結果） | 基準比對（golden） | 原始字串常值 `"""` |
| 受測對象會呼叫 DB / HTTP / 現在時間 | 把相依抽成介面或參數 | 手寫假物件 或 Moq |
| 非同步方法 | async 測試 | `async Task` + `await` |
| `private` 方法 | **不測**，透過 public 入口測 | — |

### 情境 1：固定輸入 → 固定輸出

九成的測試都是這種。用 `[Fact]`。

```csharp
[Fact]
public void Truncate_LongerThanLimit_CutsAndAppendsEllipsis()
{
    var result = TextUtil.Truncate("abcdefgh", 5);

    Assert.Equal("abcde…", result);
}
```

### 情境 2：同一段邏輯要試很多組資料

不要複製貼上五個 `[Fact]`。用 `[Theory]`，每組 `[InlineData]` 會被當成**獨立的測試**，紅了只紅那一組。

```csharp
[Theory]
[InlineData("abcdefgh", 5, "abcde…")]
[InlineData("abc", 5, "abc")]
[InlineData("", 5, "")]
[InlineData(null, 5, "")]
public void Truncate_VariousInputs_ReturnsExpected(string? input, int limit, string expected)
{
    Assert.Equal(expected, TextUtil.Truncate(input, limit));
}
```

要加一個案例的成本是一行。這是投報率最高的寫法。

### 情境 3：參數不是編譯期常數

`[InlineData]` 只吃字串、數字、bool、null。要餵物件或集合時改用 `TheoryData` + `[MemberData]`：

```csharp
public static TheoryData<string, string[]> SplitCases => new()
{
    { "a,b,c", ["a", "b", "c"] },
    { "a", ["a"] },
    { "", [] },
};

[Theory]
[MemberData(nameof(SplitCases))]
public void Split_VariousInputs_ReturnsParts(string input, string[] expected)
{
    Assert.Equal(expected, CsvUtil.Split(input));
}
```

`TheoryData<T1, T2>` 有型別檢查，比舊寫法 `IEnumerable<object[]>` 安全。

### 情境 4：不管輸入什麼都要成立的規則（不變式）

有些規則不是「這個輸入該得到那個輸出」，而是「任何輸入都必須滿足某個性質」。這種測試**不需要寫預期輸出**，只驗性質：

```csharp
[Theory]
[InlineData("")]
[InlineData("normal text")]
[InlineData("含中文與 emoji 🙂")]
[InlineData("\"未閉合的引號")]
public void Split_PartsAlwaysReassembleToOriginal(string input)
{
    var parts = Tokenizer.Split(input);

    Assert.Equal(input, string.Concat(parts));
}
```

**一個測試守住整個模組的地基**，而且加輸入的成本是一行。適用時機：切割 / 序列化 / 編碼解碼 / 排序 / 任何「拆開再合回去應該一樣」的邏輯。

### 情境 5：壞輸入不可以讓程式爆炸

有些元件的規格是「無論輸入多爛都要回傳結果，不准丟例外」（解析器、防禦性的 public API 常見）。

xUnit 刻意**沒有** `Assert.DoesNotThrow`，因為那等於「這段有跑完」。標準寫法是 `Record.Exception`：

```csharp
[Theory]
[InlineData(null)]
[InlineData("")]
[InlineData("((((")]
[InlineData("� 亂碼")]
public void Parse_MalformedInput_DoesNotThrow(string? input)
{
    var ex = Record.Exception(() => Parser.Parse(input));

    Assert.Null(ex);
}
```

### 情境 6：壞輸入應該要丟例外

反過來的情況，用 `Assert.Throws<T>`。它會**回傳**那個例外，可以繼續驗訊息或參數名：

```csharp
[Fact]
public void Withdraw_AmountExceedsBalance_ThrowsInvalidOperation()
{
    var account = new Account(balance: 100);

    var ex = Assert.Throws<InvalidOperationException>(() => account.Withdraw(200));

    Assert.Contains("餘額不足", ex.Message);
}
```

非同步版本是 `await Assert.ThrowsAsync<T>(() => ...)`。

`Assert.Throws<T>` 要求型別**完全相同**；要允許子類別用 `Assert.ThrowsAny<T>`。

### 情境 7：回傳是集合

```csharp
Assert.Empty(result);                          // 空的
var only = Assert.Single(result);              // 剛好一個，且回傳那一個元素
Assert.Contains(result, x => x.Name == "A");   // 至少有一個滿足條件
Assert.Equal(new[] { 1, 2, 3 }, result);       // 順序與內容都一樣
```

`Assert.Single` 回傳元素這點很好用，比「先驗 Count 再取 [0]」乾淨，失敗訊息也更清楚。

### 情境 8：回傳是巢狀物件或樹

不要一次比整棵樹（見第七節的坑），改成逐層剝。`Assert.IsType<T>` 會回傳轉型後的物件，可以串起來：

```csharp
var node = Assert.IsType<IfNode>(result.Root);
var inner = Assert.IsType<IfNode>(node.Then);
Assert.IsType<LiteralNode>(inner.Else);
```

只斷言你這個測試關心的部分，其他不管。

### 情境 9：回傳是一大段文字

報表、序列化輸出、格式化結果這種「輸出格式本身就是規格」的東西，用原始字串常值直接比對：

```csharp
[Fact]
public void Render_SingleItem_ProducesExpectedText()
{
    var text = Renderer.Render(item);

    var expected = """
        名稱: 測試項目
        數量: 3
        小計: 300
        """;
    Assert.Equal(expected, text.TrimEnd());
}
```

這叫 **golden test / 基準測試**。代價要先知道：**格式一改，這類測試會整片變紅**。所以只用在輸出格式是規格的地方，不要拿來測邏輯細節。

### 情境 10：受測對象會呼叫 DB / HTTP / 現在時間

這是新手最大的卡點。**卡住不是測試技巧不夠，是受測程式沒有留介面。**

```csharp
// 不可測：相依寫死在裡面
public decimal GetDiscount(int userId)
{
    var user = new SqlUserRepository().Find(userId);   // 一定要有資料庫
    if (DateTime.Now.Month == 12) return 0.8m;         // 結果隨月份變
    ...
}

// 可測：相依從外面傳進來
public decimal GetDiscount(IUserRepository repo, DateTime now, int userId)
{
    var user = repo.Find(userId);
    if (now.Month == 12) return 0.8m;
    ...
}
```

改成後者以後，測試傳一個假的 repo 和寫死的日期進去就行。假物件兩種做法：

```csharp
// 做法 A：手寫（相依少的時候最清楚，不用學套件）
private sealed class FakeUserRepository : IUserRepository
{
    public User? Find(int id) => new User(id, "測試使用者");
}

// 做法 B：Moq（相依多、要驗「有沒有被呼叫」時）
var repo = new Mock<IUserRepository>();
repo.Setup(x => x.Find(1)).Returns(new User(1, "測試使用者"));
var result = service.GetDiscount(repo.Object, new DateTime(2026, 12, 1), 1);
```

**結論：如果一段程式很難測，先改它的設計，不要硬測。** 純函式（同輸入必同輸出、不碰外界）永遠最好測——所以能寫成純函式的邏輯就寫成純函式。

### 情境 11：非同步方法

測試方法回傳 `async Task`，正常 `await`。

```csharp
[Fact]
public async Task GetByIdAsync_NotFound_ReturnsNull()
{
    var result = await service.GetByIdAsync(999);

    Assert.Null(result);
}
```

**絕對不要寫 `async void`**——例外會被吞掉，測試會假綠。也不要用 `.Result` / `.Wait()`，會 deadlock。

### 情境 12：private 方法

不測。不要為了測改成 `public`，也不要加 `InternalsVisibleTo`。

private 方法的行為 100% 可以從 public 入口觀察到。判準：**把內部整個重寫、但 public 行為不變時，測試應該全綠。** 測試綁內部實作的話，每次重構都要改測試，測試就從資產變成負債。

---

## 六、斷言速查

| 想驗的事 | 寫法 |
|---|---|
| 相等 | `Assert.Equal(expected, actual)` |
| 浮點數相等 | `Assert.Equal(expected, actual, precision: 2)` |
| 是 null / 不是 null | `Assert.Null(x)` / `Assert.NotNull(x)` |
| 布林 | `Assert.True(x)` / `Assert.False(x)` |
| 字串包含 | `Assert.Contains("片段", text)` |
| 字串開頭 | `Assert.StartsWith("前綴", text)` |
| 集合為空 / 剛好一個 | `Assert.Empty(c)` / `Assert.Single(c)` |
| 集合含符合條件的元素 | `Assert.Contains(c, x => x.Id == 1)` |
| 型別是 T（並取得該物件） | `Assert.IsType<T>(obj)` |
| 會丟例外 | `Assert.Throws<T>(() => ...)` |
| 不會丟例外 | `Assert.Null(Record.Exception(() => ...))` |

一條原則：**能用專用斷言就不要用 `Assert.True`**。

```csharp
Assert.True(actual == 5);      // 失敗訊息：Assert.True() Failure（等於沒說）
Assert.Equal(5, actual);       // 失敗訊息：Expected: 5, Actual: 3
```

---

## 七、新手最常踩的坑

**1. record 含集合屬性時，相等性不是你想的那樣**

```csharp
public record Result(string Name, IReadOnlyList<int> Items);

Assert.Equal(new Result("a", [1, 2]), actual);   // 會 fail
```

record 自動產生的 `Equals` 對每個屬性用 `EqualityComparer<T>.Default`，對 `List` / `IReadOnlyList` 來說那是**參考比較**，不是逐元素比較。內容一樣也不相等。

解法：改成逐欄位斷言（`Assert.Equal(expected.Name, actual.Name)` + `Assert.Equal(expected.Items, actual.Items)`），或比對序列化後的字串。

`readonly record struct` 若欄位全是 `int` / `string` 這類值型別，值相等正常，可以直接比。

**2. 一個測試驗五件事** → 紅了不知道哪裡壞。拆開。

**3. 測試之間共用狀態**

`static` 欄位、共用的 List、共用的暫存檔——這會讓測試依賴執行順序，而 xUnit 預設**平行執行不同測試類別**，順序不保證。每個測試自己準備自己的資料。

**4. 測到框架而不是自己的邏輯**

驗證「呼叫 `Ok()` 會回傳 `OkObjectResult`」測的是微軟的程式碼。要測的是**你自己寫的判斷、計算、轉換**。

**5. 追覆蓋率百分比**

覆蓋率高只代表程式碼被執行過，不代表行為被驗證過——一個 `Assert.NotNull` 也能刷出 100%。判準應該是「需求條目有沒有被逐條驗到」。

**6. 為了讓紅燈變綠而改測試**

測試紅了，先確認是「程式錯」還是「測試寫錯」。是程式錯就改程式。習慣性改測試遷就實作的話，測試就完全失去意義了。

---

## 八、什麼時候算寫夠了

不看覆蓋率，看這三類有沒有覆蓋到：

1. **正常路徑**：最典型的一組輸入
2. **邊界**：空字串、空集合、null、0、負數、最大值、剛好等於門檻值
3. **錯誤路徑**：每一種會丟例外或回傳失敗的情況各一個

如果專案有規格文件或驗收條件清單，**一條驗收條件 = 一個測試方法**，逐條打勾就是最好的判準。

---

## 九、把 SOP 濃縮成一頁

```text
建專案（一次）
  dotnet new xunit -o tests/X.Tests
  → dotnet sln add
  → dotnet add reference
  → 檢查：在 repo 內？TFM 相容？CI SDK 夠新？
  → 刪掉 UnitTest1.cs

寫測試（每次）
  挑一個行為
  → 命名 方法_情境_預期
  → Arrange 寫死輸入
  → Act 只有一行
  → Assert 只驗一件事
  → dotnet test

不知道怎麼寫時
  → 查第五節的情境對照表

寫不出來時
  → 通常不是測試問題，是受測程式相依寫死了 → 先改設計（情境 10）
```

---

## 連結

- [[20-testing]] — 進階篇：測試分層、Mock 邊界、`WebApplicationFactory` 整合測試、Testcontainers、什麼不值得測
- [[csharp]] — C# 語言本身
- [[dotnet-web-api]] — ASP.NET Core Web API 教材總目錄
- [[cicd-pipeline]] — 測試要在 CI 上跑才有意義
