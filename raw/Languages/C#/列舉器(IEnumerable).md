---
tags: [csharp, programming]
---

> 關聯：[[csharp]]

# 列舉器(IEnumerable)

# 概念

巡訪就是逐一走過資料結構下，內含的所有的資料元素 (Element) 或節點 (Node)，當然在不同的資料結構上，依照內部實作不同，巡訪的演算法也會各有不同。

.Net 透過 **IEnumerable**、**IEnumerator** 這兩個界面 (interface)，與它們的泛型版本︰**IEnumerable<T>**、**IEnumerator<T>**，來提供資料結構這樣的巡訪能力。

事實上整個 .Net 集合 (Collection) 的界面，處在上層的就是 IEnumerable、IEnumerable<T> 與 IEnumerator、IEnumerator<T> 4 個界面。

![Untitled](列舉器(IEnumerable)/Untitled.png)

在 .Net 集合中常用的界面 (**ICollection**、**IList**、**IDictionary**)，都有繼承 IEnumerable 或是 IEnumerable<T>，也因此實作這些界面的集合，也才會都具備資料巡訪的能力。

# **IEnumerable、IEnumerable<T>**

- Enumerable 必實作一個回傳 Enumerator 的 GetEnumerator()

首先我們先檢視 IEnumerable 與 IEnumerable<T> 界面，中文語義上，我們可以理解 IEnumerable 為「資料結構中的資料，是否可被列舉」。

```csharp
public interface IEnumerable
{
    IEnumerator GetEnumerator();
}
```

- 在 IEnumerable 界面的內容中，可以看到只有一個 GetEnumerator() 方法︰
- 可以看到 .Net 對**「是否可被列舉」**這件事的定義上，就是認定是否具備取得**「列舉器」(Enumerator)** 的能力。

# **IEnumerator、IEnumerator<T>**

- Enumerator 是實作 MoveNext()、Reset() 以及具有屬性 Current 的物件

可以將 Enumerator 視為是一個巡覽器，負責將它所附屬的資料集合中的元素，逐一取出並回傳。

.Net Framework 將巡覽器的定義置於 IEnumerator 界面，內含以下兩個方法與一個屬性︰

```csharp
public interface IEnumerator

{
    bool MoveNext();
    object Current { get; }
    void Reset();
}
```

這兩個方法與一個屬性的作用，我們可以參照 C# Cornor 中的一張整理圖如下︰

![Untitled](列舉器(IEnumerable)/Untitled%201.png)

- 將列舉值的內部，視為有一個指標，指向其附屬的資料集合的元素。指標一開始的位置，是在第一個元素之前，也就是不指向任何資料元素。
- Current 屬性，即是回傳目前指標指向的值的內容；
- MoveNext() 則是將指標往下移一個位置，並回傳 true/false 來告知，指標向下移動是否成功？(下一個位置已無資料，則表示失敗)
- Reset() 方法，則是再次將指標移動到資料集合中，第一個元素之前的位置（橘色方塊）。

# 綜合上述，可以整理的關係如下︰

1. 要讓自定義的資料型別，具備「可被列舉」的能力，需要實作 IEnumerable 或是 IEnumerable<T> 界面
2. 在 IEnumerable 與 IEnumerable<T> 界面中，定義了 GetEnumerator() 方法，回傳列舉器 (IEnumerator) 物件
3. 列舉器(IEnumerator)是真正實作，巡訪各個資料元素的主體物件

# 範例程式 - 走訪金木水火土五行

```csharp
public class FiveElements : IEnumerable
{
     private string[] fiveElements = { "金", "木", "水", "火", "土" };
     public IEnumerator GetEnumerator() => new FiveElementsEnumerator(fiveElements);
}
```

```csharp
public class FiveElementsEnumerator : IEnumerator
{
     private string[] fiveElements;
     private int index = -1;
     public FiveElementsEnumerator(string[] elements) => fiveElements = elements;
     public bool MoveNext() => ++index < fiveElements.Length;
     public object Current => fiveElements[index];
     public void Reset() => index = -1;
}
```

```csharp
static void Main(string[] args)
{
     var fiveelements = new FiveElements();
     var enumerator = fiveelements.GetEnumerator();
     while (enumerator.MoveNext())
     {
          Console.Write(enumerator.Current);
     }

     Console.WriteLine();

     foreach (var item in fiveelements)
     {
          Console.Write(item);
     }

     Console.ReadKey();
}
```

走訪所有元素的方式有兩種

- 採用 foreach
- 採用 GetEnumerator() 的方式

Foreach 語法其實就是採用 GetEnumerator 的方式實作 . 也就是說 foreach 其實是做了這四個步驟

1. 呼叫 fiveelements.GetEnumerator() , 得到一個 IEnumerator.
2. 呼叫 iterator.MoveNext() 以判斷走訪是否結束
    - 如果 iterator.MoveNext() 回傳 false 代表走訪完畢.
    - 反之如果回傳 true 則代表尚未走訪完畢 , 且會將 Current 指標移到下一個元素上.
3. 回傳 Current 屬性 .
4. 重複動作 2 & 3

所以下列這一行 , 可以這麼解讀

```csharp
foreach (var item in fiveelements)
```

- foreach : 代表要走訪的進入點.
- fiveelements : 呼叫 GetEnumerator()
- in : 呼叫 MoveNext()
- item :
    - 若回傳 false 則代表走訪結束 , 結束迴圈
    - 若回傳 true , 走訪尚未結束並回傳 Current 屬性

# 總結

1. 自定義的資料集合類別要具備**可被列舉**的能力 , 需實作 IEnumerable 或是 IEnumerable<T>
2. 實作 IEnumerable 與 IEnumerable<T> 界面 , 需要實作 GetEnumerator() 用來回傳列舉器(Enumerator)物件 - 實作IEnumerator
3. 列舉器(Enumerator)是實作走訪各個資料元素的類別的物件

![Untitled](列舉器(IEnumerable)/Untitled%202.png)