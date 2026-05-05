# VS C# Code 筆記

# LINQ to Entity

LINQ to Entity 須經過一些設定手續：

建立專案 → 設定 Entity framework 環境 → 從資料庫把資料表加入實體資料模型（edmx） 
→ 編譯完產出 dll 組件檔案 →在 LINQPad 中設定 LINQ to Entity 的連線

IQueryable<T> 介面的 ObjectQuery<T> 泛型類別的執行個體會當做 LINQ to Entities 查詢的資料來源。ObjectQuery<T> 泛型類別表示傳回零個或多個具型別物件之集合的查詢。

# LINQ to XML

```csharp
void Main()
{
	//定義第一段XML資料
	XElement bookXML = new XElement("Books",
		new XElement("Book1", "C++程式設計"),
		new XElement("Book2", "演算法與資料結構"),
		new XElement("Book3", "作業系統")
	);

	bookXML.Dump("節點添加之前的XML資料："); //輸出第一段XML資料

	//定義第二段XML資料
	XElement languageBookXML = new XElement("Books",
		new XElement("Book4", "Javascript實戰"),
		new XElement("Book5", "HTML5開發應用"),
		new XElement("Book6", "C#完全學習手冊")
	);

	//找到一個特定的節點
	XNode child1 = bookXML.Element("Book1");

	//在節點後面添加新的元素
	child1.AddAfterSelf(
		//將languageBookXML的所有元素添加到節點後面
		from el in languageBookXML.Elements()
		select el
	);
	//輸出添加完畢的XML資料
	bookXML.Dump("節點添加之後的XML資料：");
}

/* 最後的輸出結果：
C++程式設計
Javascript實戰
HTML5開發應用
C#完全學習手冊
演算法與資料結構
作業系統
*/
```

# 基本語法範例

LINQ 的查詢運算式（Query Expressions）跟Select – From – Where 這種資料庫查詢語法幾乎雷同，差別只在把 Select 放到最後，語法從「From」開始。

```csharp
void Main()
{
     //建立一組匿名型別陣列做為資料來源
    var customers = new[]{
     new {  Name = "小李", Discount = 5.0 },
     new {  Name = "老王", Discount = 3.0 },
     new {  Name = "阿華", Discount = 4.5 },
     new {  Name = "明明", Discount = 4.0 }
    };

    //定義類似 SQL Script 的 LINQ 查詢運算式，並設定輸出一組新的匿名型別清單
    var query =
       from c in customers
       where c.Discount > 3
       orderby c.Discount
       select new { c.Name, Perc = c.Discount / 100 };
    //執行查詢
    query.Dump();
}
```

先透過「型別推斷+匿名型別+物件初始化設定式」建立一組資料來源，然後使用 LINQ 查詢運算式撰寫查詢語句，最後再利用 LINQPad 提供的 Dump 方法將結果輸出。這裡的 Dump 方法，可視為以下 For each 的方法：

```csharp
foreach (var x in query)
{
    Console.WriteLine(x);
}
Console.Read();
```

### 語法架構

> 查詢運算式必須以 from 子句開頭，並以 select 或 group 子句結尾。 

在第一個 from 子句和最後的 select 或 group 子句中間，也可以包含下列一個或多個子句：where、orderby、join、let，甚至是額外的 from 子句。 

也可以使用 into 關鍵字，讓 join 或 group 子句的結果變成同一個查詢運算式中其他查詢子句的來源。
> 
> 
> ![Untitled](VS%20C#%20Code%20%E7%AD%86%E8%A8%98/Untitled.png)
> 
> ```csharp
> IEnumerable<T> query-expression-identifier = 
>     from identifier in expression
>     let identifier = expression
>     where boolean-expression
>     join identifier in expression 
>         on expression equals expression 
>         into identifier
>     orderby ordering-clause ascending|descending
>     group expression by expression 
>         into identifier
>     select expression 
>         into identifier
> ```
> 
> | 符號 | 用途 |
> | --- | --- |
> | identifier  | 表示「識別子」，通常也就是個變數 |
> | expression | 運算式，可能是一個儲存資料的 List<T>、簡單數學運算、字串處理等等 |
> | ordering-caluse | 排序子句，也就是要排序的欄位 |

# 延遲執行概念

LINQ 預設使用延後查詢執行，也就是說當寫好 LINQ 查詢語法時，「通常」當下是不會執行取資料的行為，得等到真正要「接觸」查詢結果時，才會觸發取資料的行為，取回查詢結果，這也就意味著：

1. 可以在取得查詢結果前，異動來源資料的內容，稍後取得查詢結果時，可取到最後異動過的資料。
2. 可以撰寫一個查詢語法，先執行一次以取得異動前的資料，再異動來源資料的內容，然後再執行一次取得異動後的資料，不需重新撰寫查詢子句。

更簡單的說法就是：我們可以定義一個查詢語法，然後多次列舉查詢結果，每次列舉行為發生時，都可以取得資料來源中，查詢當下最新的資料：

```csharp
//初始化資料來源
int[] intAry = new int[]{0, 1, 2};
//建立查詢
var query = from n in intAry select n;

//第一次執行查詢
query.Dump("第一次查詢-原始資料");
//修改資料來源
intAry[0] = 99;
intAry[2] = 97;
//第二次執行查詢（並未異動查詢語法）
query.Dump("第二次查詢-延後執行的效果");
```

![Untitled](VS%20C#%20Code%20%E7%AD%86%E8%A8%98/Untitled%201.png)

請注意，並不是 LINQ 語法就一定是延後執行，要看語法中所應用到的「標準查詢運算子」為何。
辨識方法：只要是能以「查詢運算式」撰寫的運算子，都屬於延後執行的標準查詢運算子。

若是回傳單一值，例如：fFirst、Average、Sum、Count、Any 等等運算子，就是產生立即執行（Immediately execution）的效果：

```csharp
//初始化資料來源
var list = new List<int>(){1,5,10};
//建立查詢呼叫加總(Sum)運算子
var querySum = (from n in list select n).Sum (c => c);

//第一次執行查詢
querySum.Dump("第一次查詢-原始資料加總");

//修改資料來源
list.Add(99);

//第二次執行查詢（並未異動查詢語法）
querySum.Dump("第二次查詢");

//重新定義 LINQ 查詢子句
querySum = (from n in list select n).Sum (c => c);
querySum.Dump("第三次查詢");
```

![Untitled](VS%20C#%20Code%20%E7%AD%86%E8%A8%98/Untitled%202.png)

- 第二次沒變
- 第三次因為重新定義而改變