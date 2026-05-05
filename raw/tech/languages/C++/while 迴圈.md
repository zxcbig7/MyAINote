# while 迴圈

```
while( A.條件式 )
{
    B.當條件成立時，就重覆做的事...
}
```

- 範例：成績加總
    
    Rock老師在學期末打算相加學生的期中考、期末考分數做為學期總成績。期中考、期末考滿分各是50分。Rock老師有上千位學生，不太可能每個人一一計算，請你寫出一個程式，替Rock老師達成這項任務。
    
    **code**
    
    ```cpp
    #include <iostream>
    using namespace std;
    
    int main()
    {
    	int g1, g2, n, i;
    
    	i = 1;
    
    	cin >> n;
    
    	while (i <= n)
    	{
    		cin >> g1 >> g2;
    		cout << "grade: " << g1 + g2 << endl;
    		i = i + 1;
    	}
    
        return 0;
    }
    ```
    
- 範例：吃漢堡
    
    Eric覺得麥蒂勞的39元漢堡實在太便宜、太好吃了，因此他決定晚餐要把口袋裡所有錢通通拿來吃39元漢堡。假設他每5分鐘就能吃一個漢堡，請你記錄他吃漢堡的過程。
    
    **code**
    
    ```cpp
    #include <iostream>
    using namespace std;
    
    int main()
    {
    	int money, i;
    
    	cin >> money;
    	i = 0;
    
    	while (money >= 39)
    	{
    		money = money - 39;
    		i = i + 1;
    		cout << "Time: " << 5 * i << "min" << endl;
    		cout << "Number: " << i << endl;
    		cout << "Money: " << money << endl << endl;
    
    	}
    
        return 0;
    }
    ```