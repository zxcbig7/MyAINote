# Enum/Struct/Delegate 比較

### **Enum**

```csharp
enum GameState { START, PAUSE, STOP }

class Program
{
	static void Main(string[] args)
	{
		GameSatae state = GameState.START;
		if(state != GameState.STOP)
		{
			state = GameState.STOP;
			Console.WriteLine("結束遊戲");
		}
		Console.ReadKey();
	}
}
```

### **Struct**

```csharp
enum Direction { EAST, WEST, NORTH, SOUTH }

struct Path 
{
	public Direction direction;
	public float distance;
}

class Program
{
	static void Main(string[] args)
	{
		Path path;  //定義結構變數
		path.direction = Direaction.South;
		path.distance = 1000f;
	}
}
```

### **Delegate**

```csharp
public delegate int MeDelegate(params int[] nums); //定義委託

class Program
{
	public static int Getsum(params int[] nums);
	{
		int sum = 0;
		for(int i = 0, i<nums.Length; i++)
		{
			sum += nums[i];
		}
		return sum;
	}

	static void Main(string[] args)
	{
		MyDelegate de; //定義
		de = Getsum; //委託指向Getsum
		int sum = de(10,20,30,40);
		Console.WriteLine(sum);
		Console.ReadKey();
	}
}
```

- 委託是一種儲存函數的引用類型，本質上是函數
- 委託的定義指定了一個return值和一個參數列表
- 委託的定義需要用關鍵字Delegate
- 委託沒有函數體
- 可以把一個函數直接賦值給委託，該函數的return值和參數類型必須一致

## 委託進階

[https://dotblogs.com.tw/daniel/2017/11/16/175138](https://dotblogs.com.tw/daniel/2017/11/16/175138)

[https://dotblogs.com.tw/daniel/2017/11/21/145211](https://dotblogs.com.tw/daniel/2017/11/21/145211)

[https://dotblogs.com.tw/daniel/2018/01/09/151636](https://dotblogs.com.tw/daniel/2018/01/09/151636)

### Action和FuncAction

- C# 還有定義兩種內置的委託類型
- Action是void不回傳值的委託
- Func是有回傳值的委託

```csharp
Action<int> a; //int 代表參數類型
Func<int,int,int> f; //<>中，最後一個泛型表示return值類型，前面表示參數類型
```

- Func固定最後一個泛型參數為方法回傳值，其餘是傳入參數

```csharp
public delegate TResult Func<in T, out TResult>(T arg);
```

### Func 範例

1. 宣告一個Func<Person,string>委託 _thunkCheckAge
2. _thunkCheckAge委託指向CheckAge方法
3. 執行_thunkCheckAge委託 (執行CheckAge方法)

```csharp
public class Person
{
    public int Age { get; set; }
    public string Name { get; set; }
}

/// <summary>
/// 年紀超過10歲算老人
/// </summary>
/// <param name="person"></param>
/// <returns></returns>
public static string CheckAge(Person person)
{
    string result = "年紀剛剛好";
    if (person.Age >= 10)
    {
        result = "老人";
    }
    return result;
}
static void Main(string[] args)
{
    //Init一個Person物件
    Person p = new Person()
    {
        Age = 10,
        Name = "tom"
    };

    #region Func
    //宣告一個Func<Person,string>委託 _thunkCheckAge
    Func<Person, string> _thunkCheckAge;

    //_thunkCheckAge委託指向CheckAge方法
    _thunkCheckAge = new Func<Person, string>(CheckAge);

    //執行_thunkCheckAge委託 (執行CheckAge方法)
    string result = _thunkCheckAge(p);

    //最後將結果顯示出來
    Console.WriteLine(result); 
    #endregion

            

    Console.ReadKey();
}
```

Action這個委託是Void，傳入參數型態是由泛型來決定

```csharp
public delegate void Action<in T>(T obj);
```

### Action 範例

1. 宣告一個Action<Person>委託的 _thunkPerson物件
2. 將CallPersonInfo方法 賦予給_thunkPerson
3. 執行_thunkPerson (就是執行CallPersonInfo方法)

```csharp
public class Person
{
    public int Age { get; set; }
    public string Name { get; set; }
}
static void Main(string[] args)
{
    //宣告_thunkPerson為Action<Person>委託
    //此Action傳入參數是Person由泛型來決定
    Action<Person> _thunkPerson;
    //Init一個Person物件
    Person p = new Person()
    {
        Age = 10,
        Name = "tom"
    };
    //將CallPersonInfo方法 賦予給_thunkPerson
    _thunkPerson = new Action<Person>(CallPersonInfo);

    //執行_thunkPerson (就是執行CallPersonInfo方法)
    _thunkPerson(p);
    Console.ReadKey();
}

public static void CallPersonInfo(Person person)
{
    Console.WriteLine($"Age:{person.Age} Name:{person.Name}");
}
```

### 分析

實現我們自己的Linq Where 和 Linq Select，先來分析 Where 方法簽章

```csharp
public static IEnumerable<TSource> Where<TSource>(this IEnumerable<TSource> source, Func<TSource, bool> predicate)
```

如果我要找一個大於10歲的人,撰寫一般Linq Where 如下在where中塞選此集合的條件，那我要怎麼自己實現呢？(重點在於[**執行塞選條件**]這個動作)

```csharp
List<Person> pList = new List<Person>()
{
    new Person() { Age=100,Name="daniel"},
    new Person() { Age=20,Name="Tom" },
    new Person() { Age = 10,Name = "Amy"},
    new Person() { Age=5,Name = "rjo"}
};
pList.Where(per => per.Age > 10);
```

重點在`if(where(item))`判斷物件是否符合條件，如符合就回傳此物件

```csharp
public static class LinqExtension
{
    /// <summary>
    /// 自訂一個Where 
    /// </summary>
    /// <typeparam name="TSource"></typeparam>
    /// <param name="source"></param>
    /// <param name="where"></param>
    /// <returns></returns>
    public static IEnumerable<TSource> MyWhere<TSource>(this IEnumerable<TSource> source
        ,Func<TSource, bool> where)
    {
        foreach (var item in source)
        {
            if (where(item))
            {
                yield return item;
            }
        }
    }
}
```

### 總結

委託把不確定的動作，轉移給呼叫端來撰寫，而不是寫死在程式中

上面的MyWhere挖了一個洞，關於判斷是否符合條件，給呼叫端實現

雖然在裡面一樣是一個一個判斷是否符合條件，符合再返回

但利用委託和泛型就可以對於任何條件和任何型別來做比較 提升了程式效率