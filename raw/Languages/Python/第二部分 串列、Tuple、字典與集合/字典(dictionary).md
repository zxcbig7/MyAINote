---
tags: [python, data-structures, programming]
---

> 關聯：[[python]]

# 字典(dictionary)

# 特色

1. 沒有順序
2. 無法使用0或1等位移值選擇項目
3. 每一個值(**value**)指定一個鍵(**Key**)
4. Value 以及 Key 可變

# 建立

- 用 { } 來建立，大括號包住 *Key : Value* 以及[ , ]分開
    
    ```python
    >>> test = {
    	'a' : "This is Terry",
    	'b' : 'This is Larry',
    	'c' : 'This is Batta'
    	}
    
    >>> test
    {'a': 'This is Terry', 'b': 'This is Larry', 'c': 'This is Batta'}
    ```
    
- 用 dict() 來轉換
    
    條件:
    
    只能轉換**雙值**序列，例如 " A, 90, B, 70 "
    
    第一個值會被當作Key，第二則被當作Value。
    
    ```python
    #雙項目 Tuple 的 List
    >>> lol = [['a','b'],['c','d'],['e','f']]
    >>> dict(lol)
    {'a': 'b', 'c': 'd', 'e': 'f'}
    
    #雙項目 List 的 Tuple
    >>> lot = (['a','b'],['c','d'],['e','f'])
    >>> dict(lot)
    {'a': 'b', 'c': 'd', 'e': 'f'}
    
    #雙字元字串的 List
    >>> los = ['ab','cd','ef']
    >>> dict(los)
    {'a': 'b', 'c': 'd', 'e': 'f'}
    
    #雙字元字串的 Tuple
    >>> tos = ('ab','cd','ef')
    >>> dict(tos)
    {'a': 'b', 'c': 'd', 'e': 'f'}
    ```
    

# 應用

- 用 [Key] 來添加或更變項目
    
    ```python
    #姓是Key，名是Value
    >>> pythons = {
        'Jones':'Terry',
        'Palin':'Michael'
        }
    >>> pythons
    {'Jones': 'Terry', 'Palin': 'Michael'}
    
    #添加資料:Garry Gilliam
    >>> pythons['Gilliam'] = 'Garry'
    >>> pythons
    {'Jones': 'Terry', 'Palin': 'Michael', 'Gilliam': 'Garry'}
    
    #更改資料:Tarry Gilliam
    >>> pythons['Gilliam'] = 'Tarry'
    >>> pythons
    {'Jones': 'Terry', 'Palin': 'Michael', 'Gilliam': 'Tarry'}
    ```
    
    - 注意:如果有多個相同的Key，只會取最後一個 (Key是獨一無二的)
        
        ```python
        >>> some_pythons = {
            'Chapman':'Graham',
            'Jones':'Terry',
            'Jones':'Berry',
            'Palin':'Michae',
            'Palin':'Larry',
            'Palin':'Henrry',
            'Palin':'Harry'
            }
        >>> some_pythons
        {'Chapman': 'Graham', 'Jones': 'Berry', 'Palin': 'Harry'}
        ```
        
- 用 update() 來合併字典
    
    ```python
    >>> pythons = {
        'a':'b',
        'c':'d',
        }
    >>> others = {
        'e':'f',
        'g':'h'
        }
    
    >>> pythons.update(others)
    >>> pythons
    {'a': 'b', 'c': 'd', 'e': 'f', 'g': 'h'}
    ```
    
    注意 : 如果有相同Key則會取最後一個
    
- 用 del 與 Key 來刪除項目
    
    ```python
    >>> test = {
    	'a' : "This is Terry",
    	'b' : 'This is Larry',
    	'c' : 'This is Batta'
    	}
    
    >>> del test['b']
    >>> test
    {'a': 'This is Terry', 'c': 'This is Batta'}
    ```
    
- 用 clear() 來刪除所有項目
    
    ```python
    >>> test = {
    	'a' : "This is Terry",
    	'b' : 'This is Larry',
    	'c' : 'This is Batta'
    	}
    
    #刪除
    >>> test.clear()
    
    >>> test
    {}
    
    ```
    
- 用 in 來測試 Key
    
    ```python
    >>> test = {
    	'a' : "1",
    	'b' : '2',
    	'c' : '3'
    	}
    
    >>> 'a' in test
    True
    >>> 'd' in test
    False
    ```
    
- **兩個取得 Value 的方法**
    
    方法1 : 用 [Key] 
    
    ```python
    >>> test = {
    	'a' : "1",
    	'b' : '2',
    	'c' : '3'
    	}
    
    >>> test['a']
    '1'
    ```
    
    方法2 : 用 get()
    
    ```python
    >>> test = {
    	'a' : "1",
    	'b' : '2',
    	'c' : '3'
    	}
    
    >>> test.get('a')
    '1'
    
    >>> test.get('d')
    
    #如果沒有，輸出後面的引述
    >>> test.get('d','Not in test')
    'Not in test'
    ```
    
- 用 Keys() 來取得所有的 Key
    
    ```python
    >>> test = {
    	'a' : "1",
    	'b' : '2',
    	'c' : '3'
    	}
    
    >>> test.keys()
    dict_keys(['a', 'b', 'c'])
    ```
    
- 用 Values() 來取得所有的 Value
    
    ```cpp
    >>> test = {
    	'a' : '1',
    	'b' : '2',
    	'c' : '3'
    	}
    
    >>> list(test. values())
    ['1','2','3']
    ```
    
- 用 items() 來取得所有的 Key / Value 成對項目
    
    ```jsx
    >>> test = {
        	'a' : '1',
        	'b' : '2',
        	'c' : '3'
        	}
    
    >>> test.items()
    dict_items([('a', '1'), ('b', '2'), ('c', '3')])
    ```
    
    注意 : 項目以 Tuple 形式回傳，例如 ('a', '1')
    
- 用 = 指派，用 copy() 複製
    
    ```jsx
    >>> test = {
        	'a' : '1',
        	'b' : '2',
        	'c' : '3'
        	}
    
    #用 = 指派，兩個變數會因對方更變而更變
    >>> test_save = test
    >>> test_save['a'] = '4'
    
    >>> test
    {'a': '4', 'b': '2', 'c': '3'}
    >>> test_save
    {'a': '4', 'b': '2', 'c': '3'}
    
    #用 copy()複製，兩個變數互相獨立而互不影響
    >>> test_save = test.copy()
    >>> test_save['a'] = '4'
    
    >>> test
    {'a': '1', 'b': '2', 'c': '3'}
    >>> test_save
    {'a': '4', 'b': '2', 'c': '3'}
    
    ```