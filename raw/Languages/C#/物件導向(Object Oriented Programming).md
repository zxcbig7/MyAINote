---
tags: [csharp, programming]
---

> 關聯：[[csharp]]

# 物件導向(Object Oriented Programming)

---

# **物件導向程式設計(Object Oriented Programming)**

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled.png)

**實例（instance）和物件（object）之間的區別**

從整部車的角度來看，把整部車子當作一個實例（instance），那組成車子的引擎、方向盤、油壓系統、電路、輪子、座椅…等系統都會被你當作是物件（object）。但若再把引擎當作是一個實例，則噴油嘴、汽缸、連桿、活塞、火星塞 … 等就會被視作物件。

<aside>
💡 可以說車子都有引擎（或任何種類的動力系統），但卻不能說每部車子的引擎都一樣。
⇒ 一個個體必定是一個物件，但一個物件卻不一定是一個實例。

</aside>

**實體化（instaniate）：指從抽象的類別，創造出具體的物件。**

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%201.png)

## 類別(Class)

> **類別（class）定義了一件事物的抽象特點**
類別的定義包含了資料的形式(屬性, Field)以及對資料的操作(方法, Method)。
一個類別的方法和屬性被稱為「成員」。
類別：汽車的設計藍圖(blueprint)
屬性：汽車的資訊
方法：汽車的行為
> 

```csharp
class Demo
{
    public string M;   //宣告欄位

    public string DoSomething(string s)  //宣告方法
    {
        return s;  //回傳值
    }

    public void PrintM() //宣告方法
    {
        Console.WriteLine(m);
    }
}
```

<aside>
💡 **string** 是指 DoSomething() 的回傳值型態 (return type)

</aside>

<aside>
💡 宣告為 **public**，才能其他類別的 Main() 方法中呼叫

</aside>

<aside>
💡 參數列 (parameter list) 是以逗號間隔的型態名稱與參數 (parameter) 名稱，像是
`型態1 參數1, 型態2 參數2, 型態3 參數3, ...`

</aside>

<aside>
💡 如果方法不需要回傳值 (return value) ，就要將方法宣告為 **void**

</aside>

## 物件**(Object)**

> 物件（object）是類別（class）的實例（instance）（也稱作實體）。
> 

```csharp

namespace ClassDemo01
{
    class Demo
    {
        public string m;

        public string DoSomething(string s)
        {
            return s;
        }

        public void PrintM()
        {
            Console.WriteLine(m);
        }
    }
		
		// 在 Program class 寫 Main() 方法來建立 Demo 型態的物件
    class Program
    {
        static void Main(string[] args)
        {
            Demo d = new Demo(); // 實體Demo類別
            d.m = "There is no spoon.";
            string s = d.DoSomething("Free your mind.");
            Console.WriteLine(s);
            d.PrintM();
        }
    }
}

//執行結果如下:
//Free your mind.
//There is no spoon.
```

<aside>
💡 Main() 預設的參數為字串陣列的 args

```csharp
static void Main(string[] args)
{
    Demo d = new Demo();
    d.m = "There is no spoon.";
    string s = d.DoSomething("Free your mind.");
    Console.WriteLine(s);
    d.PrintM();
}
```

</aside>

<aside>
💡 **void** 之前還有個 **static** 關鍵字，這個關鍵字是個修飾詞， **static** 就中文而言是靜態的意思，在程式裡頭是指可以直接透過類別名稱呼叫。

```csharp
Program.Main()
```

就會執行這個程式，這也是 C# 程式的執行方式， C# 可執行程式的執行程式碼就會寫在 Main() 方法中。

</aside>

<aside>
💡 建立變數 d 為 Demo() 型態的物件，注意變數 d 為參考 (reference)

```csharp
Demo d = new Demo();
```

</aside>

# **建構子(constructor)與屬性(property)**

- 建構子 (constructor) 是建立物件 (object) 時所執行的特殊方法 (method)
- 屬性 (property) 則是封裝私有欄位 (field) 後，替私有欄位設定的存取子 (accessor)

# 封裝 (encapsulation)

- 目的是保護欄位，不讓欄位直接被外界程式存取及修改
- 私有欄位 _seconds 之前的底線是習慣上的寫法，目的是說這個欄位已被封裝
- _seconds 就只能在類別 (class) 內進行存取

```csharp
private int _seconds = 0;
```

> 由於欄位已封裝，程式中如果要存取欄位就要定義屬性及存取子
> 

```csharp
using System;

namespace ClassDemo02
{
    class Timer
    {
        private int _seconds = 0;

        public Timer(int s) 
        {
            _seconds = s;
        }

        public int Minutes
        {
            get {return _seconds / 60;}
            set {
                _seconds += value * 60;
            }
        }

        public int Seconds
        {
            get {return _seconds % 60;}
            set {
                _seconds += value;
            }
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            Timer t = new Timer(699);
            Console.WriteLine("{0}:{1}", t.Minutes, t.Seconds);
            t.Seconds = 10;
            Console.WriteLine("{0}:{1}", t.Minutes, t.Seconds);
            t.Minutes = 19;
            Console.WriteLine("{0}:{1}", t.Minutes, t.Seconds);
        }
    }
}

//執行結果：
//11:39
//11:49
//30:49
```

Minutes ：

關鍵字 **get** 定義的存取子是取得 Minutes 的方式，這裡是取得總秒數除以 60 的商

```csharp
get {return _seconds / 60;}
```

關鍵字 **set** 定義的存取子是**設定 Minutes 之後的動作**
**value** 是內容關鍵字，意思是指派運算子右邊的值，這裡將 **value** 乘以 60 ，再加入到 _second 中

```csharp
set {
    _seconds += value * 60;
}
```

<aside>
💡 內容關鍵字是在特定場合才具有關鍵字的效力。

</aside>

Seconds ：

把總秒數 _seconds 用分及秒顯示

Timer ：

在 Program 類別的 Main() 方法建立 Timer 物件

<aside>
💡 Ｍain() 中建立 Timer 型態的變數 t 之後，
再將變數 t 的 Seconds 設定 10 ， Minutes 設定 19 ，
這樣會連動替已封裝的 _seconds **增加秒數**

```csharp
static void Main(string[] args)
{
    Timer t = new Timer(699);
    Console.WriteLine("{0}:{1}", t.Minutes, t.Seconds);
    t.Seconds = 10;
    Console.WriteLine("{0}:{1}", t.Minutes, t.Seconds);
    t.Minutes = 19;
    Console.WriteLine("{0}:{1}", t.Minutes, t.Seconds);
}
```

</aside>

## 繼承(inheritance)與類別(class)

繼承的寫法是在類別名稱用冒號，冒號後接所繼承的類別名稱

```csharp
class Elephant: Animal
//這樣 Elephant 類別就繼承了 Animal 類別。
```

- 繼承自其他類別的類別稱之為子類別 (subclass) ，如 Elephant 是 Animal 的子類別，
- 被繼承的類別稱之為父類別 (superclass) ，如 Animal 是 Elephant 的父類別。

```csharp
using System;
using System.Collections.Generic;

namespace ClassDemo03
{
    class Animal 
    {
        protected string name;

        public Animal()
        {
            name = "動物";
        }

        public Animal(string s)
        {
            name = s;
        }

        public void speak()
        {
            Console.WriteLine("哈囉，我是{0}．．．．", name);
        }
    }

    class Elephant: Animal
    {
        public Elephant()
        {
            name = "大象";
        }
    }

    class Mouse: Animal
    {
        public Mouse()
        {
            name = "老鼠";
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            var animals = new List<Animal>
            {
                new Animal(),
                new Elephant(),
                new Mouse()
            };
            foreach (var animal in animals)
            {
                animal.speak();
            }
        }
    }
}

/*執行結果:
哈囉，我是動物．．．．
哈囉，我是大象．．．．
哈囉，我是老鼠．．．．
*/
```

1. 用關鍵字 **var** 宣告 animals 變數
    1. **var** 宣告的變數可以不直接指定型態，由指派運算子設定的值來決定型態
    2. 下面 animals 是 List ， List 之後用角括弧圍住 Animal 型態名稱，這是設定 List 裡頭的元素必須是 Animal 或 Animal 的子類別。
    
    ```csharp
    var animals = new List<Animal>
    {
        new Animal(),
        new Elephant(),
        new Mouse()
    };
    ```
    
    <aside>
    💡 角括弧的寫法是泛型 (generics) 程式設計的概念，也就是在定義時先不明確設定型態，由建立實體物件時再實際設定。
    
    </aside>
    
2. 用 **foreach** 迴圈裡的變數 animal 依序取得 animals 中的每個元素
    
    ```csharp
    foreach (var animal in animals)
    {
        animal.speak();
    }
    ```
    

# 介面(Interface)

> 介面 (interface) 用關鍵字 (keyword) **interface** 定義
> 
- 介面就像契約，要求時做的class需要具備指定的能力
- 命名習慣以大寫I開頭
- 跟繼承不同，一個class可以實作多個interface
- 實作Interface定義的method必須
    - 不可以是static(確保要是物件來去存取method)
    - 必須是public
    - signature(Input、名稱、return值)必須要完全相同
- **繼承不同base class（父類別）的class也能實作相同interface**
    - interface 可以用在各種 class，並沒有受限

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%202.png)

```csharp
abstract class Creature
{
	protected int hp = 100;
	public virtual string say()
	{
		return "I'm" + getName() + ", I have " + hp + " HP.";
	}
	public void injured(int damage)
	{
		hp -= damage;
	}
	public abstract string getName();
}

class Player: Creature
{
	public override string getName()
	{
		return "Player";
	}
}

class Villager: Creature
{
	public override string getName()
	{
		return "Villager";
	}
}

class Moster: Creature
{
	public override string say()
	{
		return "I'm a monster!!";
	}
	public override string getName()
	{
		return "Moster";
	}
}
```

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%203.png)

```csharp
interface IAttackable
{
	void attack(Creature target);
}

interface ITalkable
{
	string Talk(Creature target);
}

class Villager: Creature, ITalkable //繼承介面
{
	public override string getName()
	{
		return "Villager";
	}
	public void talk(Creature target)
	{
		return "Hello";
	}
}

class Player: Creature, IAttackable, ITalkable //繼承介面
{
	public override string getName()
	{
		return "Player";
	}
	
	public void attack(Creature target)
	{
		target.injured(30);
	}
	
	public void talk(Creature target)
	{
		return "Hi";
	}

}

class Moster: Creature, IAttackable //繼承介面
{
	public override string say()
	{
		return "I'm a monster!!";
	}
	public override string getName()
	{
		return "Moster";
	}
	public void attack(Creature target)
	{
		target.injured(5);
	}
}
```

> 此時的attack函式有abstract的概念，在interface只定義了有這東西，等到繼承過去後再去決定函式的內容。
> 

<aside>
💡 與abstract不同的地方是不用寫override。

</aside>

<aside>
💡 實作的內容必須是public。

</aside>

```csharp
Creature creature = new Villager();
IAttackable someone = new Monster(); //Monster有實作IAttackable介面
someone.attack(creature);

someone.say(); //但 IAttackable沒有定義say()，這行會有錯誤
```

# **命名空間(**namespace**)與 using**

> 命名空間 (namespace) 用關鍵字 **namespace** 定義
> 

> 關鍵字 **using** 用來引入命名空間，基本上只要用 **using** 引入命名空間後，就可以使用該命名空間中的定義，例如有以下的命名空間 NewDemo
> 

```csharp
namespace NewDemo
{
    class Demo
    {
        public int DemoField;

        public Demo(int n)
        {
            DemoField = n;
        } 
    }
}
```

<aside>
💡 把以上的檔案放在專案資料夾中，專案資料夾裡的其他程式檔案就可以用關鍵字 **using**
引入

</aside>

```csharp
using NewDemo;
```

# **this 與 base**

## this

透過 this 關鍵字可以直接存取所屬物件的屬性與方法，常用於 method 的參數名稱與屬性名稱重複的時候。

```csharp
class Fruits
{
    private string type = "香蕉";        //私有變數與方法參數名稱相同
    
    public void GetFruit(string type)
    {
        Console.WriteLine(type);        //顯示：芭樂
        Console.WriteLine(this.type);   //顯示：香蕉
    }
}
class Program
{
    static void Main(string[] args)
    {
        Fruits fruits = new Fruits();
        fruits.GetFruit("芭樂");
    }
}
```

## base

base 關鍵字存取的對象是基底類別 (base class)

當衍生類別中出現了名稱相同的屬性，若想存取基底類別中的屬性而非衍生類別的屬性，就可以使用 base 來存取

```csharp
class Fruits
{
    protected string type = "水果";    
}
class Apple : Fruits
{
    private string type = "蘋果";
    
    public Apple()
    {
        //用 base 存取基底類別變數
        Console.WriteLine(base.type);    //顯示：水果
        Console.WriteLine(type);         //顯示：蘋果        
    }
}
class Program
{
    static void Main(string[] args)
    {
        Apple apple = new Apple();
    }
}
```

- 當衍生類別 override 了一個基底類別的 method，若想存取原版 (原本在基底類別內的版本) 的 method，就可以用 base

```csharp
class Fruits
{
    private string type = "水果";
    
    public virtual void GetFruit()
    {
        Console.WriteLine("基底類別:" + type);
    }
}
class Apple : Fruits
{
    private string type = "蘋果";
    
    public override void GetFruit()
    {
        //用 base 存取基底類別方法
        base.GetFruit();                         //顯示：基底類別:水果
        Console.WriteLine("衍生類別:" + type);    //顯示：衍生類別:蘋果
    }
}
class Program
{
    static void Main(string[] args)
    {
        Apple apple = new Apple();
        apple.GetFruit();
    }
}
```

- 想要呼叫基底類別的建構子 (constructor) 時，可以在自己的建構子後加上 base 來呼叫

```csharp
class Fruits
{ 
    public Fruits(string type)
    {       
        Console.WriteLine("基底類別:" + type);
    }
}
class Apple : Fruits
{
    private string type = "蘋果";
    //用 base 存取基底類別建構子
    public Apple(string type) : base(type)
    {
       Console.WriteLine("衍生類別:" + this.type);    //顯示：衍生類別:蘋果
    }
}
class Program
{
    static void Main(string[] args)
    {
        Apple apple = new Apple("水果");    //顯示：基底類別:水果
    }
}
```

# abstract、virtual、override

# Public、Private、Protected差異

public： 全範圍可讀可寫

private： Class 內可讀可寫、但繼承不可以直接更改

protected： 可以繼承範圍內可以修改

internal：

> 開放程度: public > protected > private
> 

# 抽象類別與方法（abstract class & method）

> 基底類別(父類別)中，abstract method 可以不需要內容
衍伸類別(子類別)需用override該函式的內容（強迫所有繼承的子類別實作該函式）
> 

```csharp
abstract class Monster
{
	public abstract string attack(); // 只有定義函式，之後需要Override
}

public class Slime: Monster
{
	public override string attack()
	{
		return "史萊姆使用攻擊";
	}
}
```

<aside>
💡 當 Class 被設定為 abstract class 時，該物件無法被實體化（不能 new 它）。

</aside>

在基底類別(base class)宣告 abstract method，不讓衍伸類別自己寫想寫的東西 ，可以避免多建立一些變數

```csharp
public void startEvenet()
{
	Monster monster = new Slime();
	Console.WriteLine("" + monster.attack()); // 此處用是Slime的Attack()
}

// 如果沒有寫abstract、override，attack()函式會因為沒有內容導致monster無法呼叫該韓式。
```

# static、const、readonly

static: 屬性不需要實體化物件就可以直接使用

const: 固定常數、編譯時替換成定值(編譯後換了其他數值無法同時更改其他變數)

> const 函數宣告時，變數名稱通常要是全部大寫
> 

ststic readonly: 唯讀、執行時再去換成定值

# switch & enum

switch & enum 可以配合使用

enum 表示各內容以0開始給予數值。

多維陣列

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%204.png)

先看垂直在看水平

垂直由上往下看，水平由左往右看

# 封裝、繼承、多型

## **封裝 (Encapsulation)**

> **確保資料變化在掌握範圍內**
將物件內部的資料隱藏起來，只能透過物件本身所提供的介面(interface)取得物件內部屬性或者方法，物件內部的細節資料或者邏輯則隱藏起來，其他物件即無法瞭解此物件的內部細節，若不經過物件提供之方法便無從更動此物件的資料。
> 

**精神：**對一件事情只需要理解他的外在就好，不需要了解裡面內部的構造。

**例如：**透過getInformation()取得車子資訊，並不需要知道他是如何取得資訊的。

```csharp
class Car{
    private String brand;
    private String type;
    private int hp;
    public String getInformation(){
      return "廠牌："+brand+"，型號："+type+"，馬力："+hp;     
    }
}
```

## **繼承 (Inheritance)**

> **減少程式編寫的重複性**
在某種情況下，一個Class會有「子類別」。子類別比原本的類別(稱為父類別)要更加具體化（理解成更詳細的內容），也就是說子類別繼承了父類別。
> 

例如：計程車(子類別)繼承了汽車(父類別)原有的屬性以及方法，也新增了自己特有的屬性(driverName)。

```csharp
class Car{
    public String brand;
    public String type;
    public int hp;
    public String getInformation(){
      return "廠牌"+brand+"型號"+type+"馬力"+hp;     
    }
}
class Taxi extends Car{
    public String driverName;
}
```

## **多型 (Polymorphism)**

> **提高物件彈性、統一基底類別、降低對實作的依賴(呼叫最上層就可)**
相同名稱的方法(Method)，多個相同名稱的方法，傳入不同的參數，會執行不同的敘述。
> 
- 多型(Polymorphism)則包含多載(Overloading)和複寫(Overriding)。

## **多載(Overloading)**

在**相同類別**中，定義**名稱相同**，但是**參數個數不同**，或是**參數型態不同**的函式，這樣就可以利用參數個數或者參數型態，呼叫到對應的方法。
例如：一個計算面積的方法，如果傳入一個參數，就當正方形來算面積；傳入兩個參數，就當成長方形來算面積。

```csharp
public int computeArea(int length){
    return length * length;
}
public int computeArea(int length, int width){
    return length * width;
}
```

## **複寫(Overriding)**

指覆寫掉父類別中的函式。

例如：動物類別(父類別) getLegs()方法被鳥類別(子類別)覆蓋。

```csharp
class Animal{
    protected int legs = 1;
    protected virtual int getLegs(){
      return legs*4;
    }
}
class Bird extends Animal{
    protected override int getLegs(){
      return legs*2;
    }
}
```

<aside>
💡 extends 可以用 “:” 取代

```csharp
class Bird : Animal{
	  protected override int getLegs(){
	  return legs*2;
}
```

</aside>

# List<T>

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%205.png)

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%206.png)

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%207.png)

# 泛型

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%208.png)

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%209.png)

![Untitled](物件導向(Object%20Oriented%20Programming)/Untitled%2010.png)

> 泛型語法:宣告泛型
>