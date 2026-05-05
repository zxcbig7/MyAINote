# if -else 條件式

> if
> 

```cpp
if( 條件 )
{
    如果條件成立時做什麼...
}
else
{
    否則做什麼...
}
```

- 排版：在{ }內的東西會利用 Tab鍵 向右推。反之可以用 Shift+Tab 向左推。
- 當 { } 內的東西只有一列的時候，可以省略大括號。
    
    ```cpp
    if( 條件 )
        如果條件成立時做什麼...
    else
        否則做什麼...
    ```
    
- 範例
    
    ### c**ode**
    
    ```cpp
    #include<iostream>
    using namespace std;
    
    int main()
    {
        int grade;
    
        cin >> grade;
    
        if( grade >= 60 )
            cout << "You Pass!" << endl;
        else
            cout << "You Fail..." << endl;
    
        return 0;
    }
    
    ```
    
    ### **input1**
    
    ```cpp
    71
    ```
    

> 關係運算
> 
- `=`在C++中是**指派**（詳見指派變數值）
- `==`才是**判斷是否相等**
1. == 等於
2. !=!= 不等於
3. >
4. <
5. >=
6. <=

> 邏輯運算
> 
1. and 且
2. or 或
3. not 反
- 範例
    
    code
    
    ```cpp
    #include <iostream>
    using namespace std;
    
    int main()
    {
        int a;
        
        while (cin >> a)
        {
            if (a == 4 or a == 13)
            {
                cout << "bad!" << endl;
            }
            else
            {
                cout << "good" << endl;
            }
        }
    
        return 0;
    }
    ```
    

> 巢狀 if
> 
- 範例
    
    code
    
    ```cpp
    #include<iostream>
    using namespace std;
    
    int main()
    {
        int sex;
        int age;
    
        cin >> sex >> age;
        if( sex==1 )
        {
            if( age >= 18 )
            {
                cout << "You are marriageable." << endl;
            }
            else
            {
                cout << "You are NOT marriageable." << endl;
            }
        }
        if( sex==2 )
        {
            if( age >= 16 )
            {
                cout << "You are marriageable." << endl;
            }
            else
            {
                cout << "You are NOT marriageable." << endl;
            }
        }
    
        return 0;
    }
    ```