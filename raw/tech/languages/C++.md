# C++

[基礎](基礎%202c98fda15f6f814e8004eb01b1aac708.md)

---

[變數](變數%202c98fda15f6f81eda604c87fd10eb1a7.md)

---

[重複輸入](重複輸入%202c98fda15f6f81fcbbffc9be43b5f53e.md)

---

[if -else 條件式](if%20-else%20條件式%202c98fda15f6f81af9e24ef521e03d51f.md)

---

[while 迴圈](while%20迴圈%202c98fda15f6f8157a7ace8d9d699b89e.md)

[指標](指標%202c98fda15f6f812bb044edc662233cf4.md)

10/22筆記

---

- void
    
    ```cpp
    void main(void)
    {
    }
    /*
    說明
    1. C語言都從main開始執行
    2. main之前void意味沒有回傳值，執行程式不會傳訊給DOS
    3. main之中的void意味不會由作業系統把命令參數傳入main()
    */
    ```
    
- struct
    
    ```cpp
    struct A
    {
    	int a, b;
    	int fa(int i, int j)
    	{
    		return i+j;
    	}
    }; //一定要加;
    
    int main()
    {
    	//A test.a=5; 是錯誤的語法
    	//應該要
    	A test; //以「結構A」建立「結構物件test」
    	test.a = 5;//存取結構物件成員
    	test.b = 10;
    	cout << test.a << endl;
    	cout << test.fa(test.a, test.b) << endl;
    }
    ```
    
- class
    
    比 struct 多區域劃分
    
    public 區域：類別物件成員及類別物件成員函式，可以直接被類別外部的程式碼呼叫而進行存取。可以被其他類別所繼承。
    
    protected 區域：不能外部直接存取，但可以被其他類別所繼承。
    
    private 區域：不能外部直接存取與繼承
    
    ---
    
    定義class
    
    ```cpp
    class A //定義類別叫做 A
    {   
    public: //設定public區域和此區域的成員
        int a; //註：類別和結構一樣，無法在類別中將類別成員初始化
        void set_c(int c_) //可利用public成員函數設定private區域成員的值
        { 
            c = c_; 
        }
        void get_c() //可利用public成員函數取出private區域成員的值
        { cout << c << endl;}
    protected:
        int b;
    private:
        int c;
    };//注意： } 後要加 ;
    ```
    
    class使用
    
    ```cpp
    A test;
    //test.c = 10;  //此行錯誤，c變數在private，無法在類別外存取
    cin >> test.a;
    
    cout << test.a << endl;
    
    test.set_c(10);
    test.get_c();
    ```
    
    ---
    
    class 以外設立一個function
    
    ```cpp
    class A
    {
    public:
        int cut(int a, int b);
    };
    
    class B
    {
    public:
        int cut(int a, int b);
    };
    
    //在類別外才完整地定義函式，稱為對函式的「實做」。
    int A::cut(int a, int b) { return a - b; }
    /*
    注意：要在類別外實做函式，呼叫函式時需使用 類別名稱::函式名稱 來呼叫，
    否則若直接用函式名稱(cut)來呼叫，C++無法分辨要呼叫來自classA還是classB的cut。
    */
    ```
    
    class使用
    
    ```cpp
    A test;
    cout << test.cut(5, 2) << endl;
    ```
    
- class 建構式
    
    ```cpp
    class A
    {
    public:
        int a;
    		//設定此類別第一個建構式
        class A(int a_, int b_, int c_) { a = a_; b = b_; c = c_; }
        //設定此類別第二個建構式
    		class A() { a = 5; b = 10; c = 15; }
    
        int cut(int a, int b);
    
    		//設定輸出所有類別成員的函式
        void printvalue()
        {
            cout << a << "," << b << "," << c  << endl;
        }
    protected:
        int b;
    private:
        int c;
    };
    ```
    
    操作
    
    ```cpp
    //利用第一個建構式建立類別物件，並為類別物件成員設初始值。
    A A1(1, 2, 3);
    //利用第二個建構式建立類別物件，並為類別物件成員設初始值。
    A A2;
    
    A1.printvalue();
    A2.printvalue();
    ```
    
    註1:類別建構式不一定要對所有類別物件成員進行初始化，只對其中幾個類別物件成員進行初始化也可以，沒有被進行初始化的類別物件成員便沒有值，或是也可以其他函式進行初始化。
    
    註2:若在一個類別沒有設定任何類別建構式，C++會自動為該類別建立一個建構式(程式碼中看不到)，相當於 類別名稱(){}，利用此建構式建立物件時，不會對類別物件成員進行任何初始化，如classA A。稱為「備用建構式」。
    
    註3:利用建構式建立類別物件時，也可以使用「動態空間建構方式」，也就是使用指標（pointer）來建構，程式碼如下：
    
    ```cpp
    //類別名稱* 類別物件名稱 = new 類別建構式;
    
    A* A1 = new A(1, 2, 3);
    A* A2 = new A;
    
    /*
    因為是指標所以無法使用 
    類別物件名稱.類別物件成員函式名稱(參數1,參數2)
    而是用 
    類別物件名稱 -> 類別物件成員函式名稱(參數1,參數2)
    */
    
    A1->printvalue();
    A2->printvalue();
    ```
    
- 自訂函數
    
    ```cpp
    void functionA()
    {
    	cout << "此函式不回傳值";
    	//return a + b; 會出現錯誤
    }
    
    int functionB(int a, int b)
    {
    	return a+b;
    }
    
    ```
    
    註(重要):一般來說，程式是由主函式main()開始執行，故所有自訂函式在撰寫上的順序都必需在main()之前。
    
    函式特徵，指的是：
    
    回傳資料型態 函式名稱(參數1資料型態 參數1名稱 , 參數2資料型態 參數2名稱 , 參數3資料型態 參數3名稱)
    
    函式特徵不包括函式內容在內。
    
- 參考（reference）
    
    ```cpp
    int a = 5;
    int& b = a;
    
    b = 15;
    
    cout << a;
    
    //輸出結果 15
    
    //b 是 a 的參考，對var2進行存取，等於直接對var1進行存取。
    //擁有相同記憶體位置
    //&a = &b
    ```
    
    const
    
    ```cpp
    int a = 5;
    const int &b = a;
    
    //b = 15; 
    //因為有const 無法對b做「存」，只能「取」
    //想改變b的值，只能由改a來達成
    
    cout << a;
    ```
    
- 指標（pointer）
    
    ```cpp
    int a = 3;
    int* b = &a;//稱「b為a的指標」，b的意義為：指向a在記憶中的位址。
    cout << b;// 顯示b的意義，也就是a在記憶中的位址，也就是&a。
    cout << *b; //顯示b所指向的變數的值，也就是a，也就是3。
    ```
    
- 參數傳遞方式
    
    值傳方式:將外部資料複製到函式運算後輸出，不改變外部資料
    
    ```cpp
    int setvar(int b){b = 4;return b;}
    
    void main()
    {
    	int a = 5;
    	cout << setvar(a) << endl; //顯示4
    	cout << a; //顯示5
    }
    ```
    
    參考型態傳遞方式:將外部資料道函式運算後輸出，有可能改變外部資料
    
    ```cpp
    int setvar(int &b){b = 4; return b;}
    //此時&b = a(b參考a)，所以b改a也會改
    
    void main()
    {
    	int a = 5;
    	cout << setvar(a) << endl;//顯示4
    	cout << a;//顯示4，a從5變4
    }
    ```
    

繼承

superclass可以繼承fuction給subclass

看OO_part2 p13

- 建構子constructor (superclass)
    
    函式名稱與類別名稱一致
    
    class中預設使用的function
    

解構子 unconstructor