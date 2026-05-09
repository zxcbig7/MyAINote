# Function 參數設計

# this

---

```csharp
using System;

namespace StringExt
{
    public static class MyString
    {
        //                          VVVV
        public static string concat(this string src1, string src2)
        {
            return src1 + src2;
        }
    }
}

namespace Example
{
    using StringExt; // 放在不同 namespace，所以要 using

    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello ".concat("World!"));
            // C# 內建 string 類別並沒有 concat 這個方法。
            // 我從外面(MyString)掛一個上去。

            // 如果 concat 第一個參數宣告時沒有加上 this 修飾字。
            // 那呼叫時只能這樣寫:
            Console.WriteLine(MyString.concat("Hello ", "World!"));
        }
    }
}
```

具體來說， C# 編譯器的運作方式是從第一個參數有 ***this*** 修飾字的靜態方法中，找到符合型態簽章的靜態方法來用。 本例 `"Hello ".concat("world")` 就是找符合 `concat(this string, string)` 簽章的靜態方法。 如果程式寫 `1.concat("xyz")` 那就會錯誤。因為 C# 編譯器找不到符合 `concat(this int, string)` 簽章的靜態方法。

- C# 內建的 string 類別並沒有 concat 這個方法。
- 這個方法是定義在 MyClass 類別中的靜態方法。
- 在沒用 ***this*** 修飾字之前，只能按靜態方法的方式呼叫它，例如 `MyString.concat(a, b)` 。
- 在第一個參數上加 ***this*** 修飾字後， C# 就會讓它看起來像一個實例方法，而可以寫成 `a.concat(b)` 。
- 從設計人員的角度看，就像是把 MyString 裡的方法，外掛到 string 上面了。

# params

---

```csharp
class Program
{
    static void Main(string[] args)
    {
        Sum();
        Sum(1, 2);
        Sum(1, 2, 3);
        
        Console.ReadKey();
    }

    private static void Sum (params int[] values)
    {
        Console.WriteLine(values.Sum().ToString());
    }
}
```

- params 運用在 method 的參數區塊，讓原本固定的參數個數變為可變動。
- 由範例可以發現 Sum 的參數是可以變動的，不用因為參數個數的不一樣而多載相同邏輯的程式。

### 使用規則

1. params的參數必須要同一型別，整數就只能搭配整數，不能一個整數一個字串
2. params的參數個數可0～n個
3. params要搭配一個一維陣列來宣告
4. params的參數必須要在參數中的最後一個，且只能一個

### 比較

params 與 List<> 合適的使用情境比較如下：

params：參數清單是程式碼 hard code 決定的

List<>：程式碼只是設定好條件，然後動態去獲取參數個數

# ref

---

```tsx
static void AddOne(ref int value)
{
    value += 1; // 改外面的變數
}

int x = 5; // 在外面定義
AddOne(ref x);
Console.WriteLine(x); // 6, x 被改掉了
```

**使用時機：**讓Function 直接修改Function外面的變數(不用在Function內另外定義，占記憶體)

# out

---

```tsx
static void ParsePerson(string input, out string name, out int age, out bool isValid)
{
    // input 格式假設是 "Vic,30"
    var parts = input.Split(',');

    if (parts.Length == 2 && int.TryParse(parts[1], out int parsedAge))
    {
        name = parts[0];
        age = parsedAge;
        isValid = true;
    }
    else
    {
        name = "";
        age = 0;
        isValid = false;
    }
}

static void Main()
{
    ParsePerson("Vic,30", out string name, out int age, out bool isValid);

    if (isValid)
    {
		    // 沒有在前面明確定義變數但就是可以用
		    // 因為已經定義在有out的那些變數了
        Console.WriteLine($"Name: {name}, Age: {age}"); // Name: Vic, Age: 30
    }
}
```

- 通常搭配 TryParse
- `out` 就是 Function 的一種return方式 ,差別是可以同時有多個return值, `return` 只能有一個
- 有 out 的 return 值在外面可以當已經定義的變數用了

# in

---

**用途：**給**大型 struct** 用的,避免複製開銷, 同時保證Function不會修改它。

**簡單講：**該 Struct 在Function內只能拿來用，嘗試修改會報錯(防呆機制)

**優化的點：**Struct 越大,`in` 省下的複製成本越明顯

```tsx
// 模擬一個大型 struct (實際上 Vector3D 可能有更多欄位)
struct Vector3D
{
    public double X, Y, Z;

    public Vector3D(double x, double y, double z)
    {
        X = x; Y = y; Z = z;
    }
}

static double Length(in Vector3D v)
{
    // v.X = 999; // 編譯錯誤,in 參數是唯讀的
    return Math.Sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z);
}

static void Main()
{
    var vec = new Vector3D(1, 2, 3);
    Console.WriteLine(Length(in vec)); // 或直接寫 Length(vec) 也可以
}
```