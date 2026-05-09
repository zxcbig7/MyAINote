---
tags: [python, data-structures, programming]
---

> 關聯：[[python]]

# 集合(Set)

## 描述

Set 像是被移除 Value，只留下 Key 的字典

- 如果有交集，只取一個
- *null* 或 *空集合* 表示 0 個元素的集合
    
    ![](S__40837123.jpg)
    

## 特色

1. 沒有順序(跟字典一樣)
2. 每個 Key 都是獨一無二的
3. 可利用轉換成set的方式，移除任何重複的值

## 建立

- 用 set() 來建立
    
    ```python
    >>> empty_set = set()
    >>> empty_set
    set()
    #以set()表示空集合，而非{}
    
    >>> even_number = {0,2,4,6,8}
    >>> even_number
    {0, 2, 4, 6, 8}
    
    >>> odd_number = {1,3,5,7,9}
    >>> odd_number
    {1, 3, 5, 7, 9}
    ```
    
    注意 : 如果用{}建立，python預設建立字典，而非集合
    
    ```python
    
    >>> empty_set = {}
    >>> empty_set
    {}
    
    ```
    

## ㄉ應用

- 用 set() 轉換其他類型
    
    ```python
    >>> set('letters')
    {'s', 't', 'l', 'e', 'r'}
    #注意:只剩一個 t 及 e
    
    #List 轉 Set
    >>> set(['Dasher','Dancer','Prancer','Mason-Dixon'])
    {'Prancer', 'Dasher', 'Mason-Dixon', 'Dancer'}
    
    #Tuple 轉 Set
    >>> set(('Ummagumma','Echoes','Atom Heart Mother'))
    {'Ummagumma', 'Atom Heart Mother', 'Echoes'}
    
    #Dictionary 轉 Set 時，只保留Key並移除Value
    >>> set({'apple':'red','orange':'orange','cherry':'red'})
    {'apple', 'cherry', 'orange'}
    ```
    
- 用 in 來測試值
    
    ```python
    #以下是調酒及成分
    >>> drinks = {
    	'martini':{'vodka','vermouth'},
    	'black russian':{'vodka','kahlua'},
    	'white russian':{'cream','vodka','kahlua'},
    	'manhattan':{'rye','vermouth','bitters'},
    	'screwdriver':{'orange juice','vodka'}
    	}
    
    #尋找成分有vodka的調酒
    >>> for name, contents in drinks.items():
    				if 'vodka' in contents:
    						print(name)
    
    		
    martini
    black russian
    white russian
    screwdriver
    
    #尋找成分有vodka，但不要有牛奶成分的調酒，而且討厭vermouth的味道
    >>> for name, contents in drinks.items():
    				if 'vodka' in contents and not ('vermouth' in contents or 'cream' in contents):
    						print(name)
    
    		
    black russian
    screwdriver
    ```
    
- 結合 與 運算子
    - 基本
        
        ```python
        >>> a = {1,2}
        >>> b = {2,3}
        >>> c = {1,2,3}
        
        ## 交集運算子「&」或 intersction() 函式
        >>> a & b
        {2}
        >>> a.intersection(b)
        {2}
        
        ## 連集運算子「|」或 union() 函式
        >>> a|b
        {1, 2, 3}
        >>> a.union(b)
        {1, 2, 3}
        
        ## 差集運算子「-」或 difference() 函式
        ## 差集:屬於第一個集合，但不屬於第二個集合的成員
        >>> a - b
        {1}
        >>> a.difference(b)
        {1}
        
        ## 互或斥運算子「^」或 symmetric_difference() 函式
        ## 互或斥:只屬於其中一個集合的項目
        >>> a.symmetric_difference(b)
        {1, 3}
        
        ## 用 <= 或 issubset() 判斷某集合是否為另一個集合的**子集合**
        ## 子集合:第一個集合的所有成員都屬於第二個集合
        >>> a <= b
        False
        >>> a.issubset(b)
        False
        ## 補充:所有的 Set 是自己的子集合
        >>> a <= a
        True
        
        ## 用 < 判斷某集合是否為另一個集合的**真子集**
        ## 真子集:第二個集合必須擁有第一個集合的所有成員
        ## 所有集合都不是自己的真子集
        >>> a < b
        False
        >>> a < c
        True
        >>> a < a
        False
        
        ## 用 >= 或 issuperset() 判斷某集合是否為另一個集合的**超集合**
        ## 超集合 : 子集合的相反(第二個集合的所有成員都屬於第一個集合)
        ## 所有集合都是自己的超集合
        >>> a >= b
        False
        >>> a.issuperset(b)
        False
        >>> c >= a
        True
        
        ## 用 > 判斷某集合是否為另一個集合的**真超集合***(proper superset)*
        ## 真超集合 : 真子集的相反
        ## 所有集合都不是自己的真超集合
        >>> a > b
        False
        >>> c > a
        True
        >>> a > a
        False
        
        ```
        
    - 範例
        
        ```python
        >>> drinks = {
        	'martini':{'vodka','vermouth'},
        	'black russian':{'vodka','kahlua'},
        	'white russian':{'cream','vodka','kahlua'},
        	'manhattan':{'rye','vermouth','bitters'},
        	'screwdriver':{'orange juice','vodka'}
        	}
        
        ##先將 兩款飲料的材料Set 放到變數中
        >>> bruss = drinks['black russian']
        >>> wruss = drinks['white russian']
        
        ##交集(兩種飲料共同的材料)
        >>> bruss & wruss
        {'kahlua', 'vodka'}
        
        ##聯集(兩種飲料所有的材料)
        >>> wruss|bruss
        {'vodka', 'kahlua', 'cream'}
        
        ##差集(飲料 A 有，但飲料 B 沒有的材料)
        >>> bruss - wruss
        set()
        >>> wruss-bruss
        {'cream'}
        
        ##互或斥(兩種飲料中，找出只屬於其中一種的材料)
        >>> bruss^wruss
        {'cream'}
        
        ##子集合(black russian 加入 cream 就變成 white russian)
        ## bruss 是 wruss 的子集合，wruss 是 bruss 的超集合
        >>> bruss <= wruss
        True
        
        ##真子集(white 比 black 多了 cream，其他材料一樣)
        >>> bruss < wruss
        True
        
        ## 超集合(子集合的相反)
        >>> bruss >= wruss
        False
        >>> wruss >= bruss
        True
        
        ##真超集合(真子集的相反)
        >>> wruss > bruss
        True
        
        ```
        
    - 應用
        
        ```python
        ## 尋找含有 vermouth 或 orange juice 的酒
        >>> for name, contents in drinks.items():
        	      if contents & {'vermouth','orange juice'}:
        		       print(name)
        
        		
        martini
        manhattan
        screwdriver
        
        ## 尋找含有 vodka，但沒有 cream 與 vermouth 的酒
        >>> for name, contents in drinks.items():
        	      if 'vodka'in contents and (not contents & {'vermouth','cream'}):
        		        print(name)
        
        		
        black russian
        screwdriver
        
        ```