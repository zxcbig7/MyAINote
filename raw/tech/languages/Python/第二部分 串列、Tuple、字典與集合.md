# 第二部分 : 串列、Tuple、字典與集合

---

# 串列(List)

[串列(List)](串列(List)%202c98fda15f6f81db97d8c0365487fbc8.md)

# Tuple

[Tuple](Tuple%202c98fda15f6f81538596f2d9a3ac998c.md)

### Tuple V.S. 串列

- Tuple 通常可以用來取代串列，但沒有append()、insert()等等。(Tuple 不可修改)

既然不能修改，為何還要選 Tuple 來取代 List ?

- tuple 佔用空間較小
- 不會不小心破壞 tuple 的項目
- 可以把 tuple 當成字典鍵
- 可以將**具名 tuple** (Named tuple )當成物件的簡化替代品
- 函式引述是已 tuple 的形式傳入

---

# 集合(Set)

[集合(Set)](集合(Set)%202c98fda15f6f8113948fe9a47a30682d.md)

# 字典(Dictionary)

[字典(dictionary)](字典(dictionary)%202c98fda15f6f81298728e32f1860f76f.md)

---

### 比較資料結構

複習 : 

- 用方括號 ( [] ) 來製作串列，用逗號製作 Tuple ，用大括號 ( {} ) 製作字典。
    
    ```python
    >>> marx_list = ['Groucho','Chico','Harpo']
    >>> marx_tuple = 'Groucho','Chico','Harpo'
    >>> marx_dict = {'Groucho':'banjo','Chico':'piano','Harpo':'harp'}
    ```
    
- 都可以用方括號來存取單一元素。
    
    ```python
    >>> marx_list[2]
    'Harpo'
    >>> marx_tuple[2]
    'Harpo'
    >>> marx_dict['Harpo']
    'harp'
    ```
    

---

### 製作更大的資料結構

1. 建立三個不同的串列
    
    ```python
    >>> marxes = ['Groucho','Chico','Harpo']
    >>> pythons = ['Chapman','Cleese','Gilliam','Jones','Palin']
    >>> stooges = ['Moe','Curly','Larry']
    ```
    
2. 製作一個 Tuple，把每一個串列當成元素
    
    ```python
    >>> tuple_of_lists = marxes,pythons,stooges
    >>> tuple_of_lists
    (['Groucho', 'Chico', 'Harpo'], ['Chapman', 'Cleese', 'Gilliam', 'Jones', 'Palin'], ['Moe', 'Curly', 'Larry'])
    ```
    
3. 製作含有串列的串列
    
    ```python
    >>> list_of_lists = [marxes,pythons,stooges]
    >>> list_of_lists
    [['Groucho', 'Chico', 'Harpo'], ['Chapman', 'Cleese', 'Gilliam', 'Jones', 'Palin'], ['Moe', 'Curly', 'Larry']]
    ```
    
4. 製作樂團的字典，其中 Key 是團名，Value 是團員
    
    ```python
    >>> dict_of_lists = {
    	'Marxes':marxes,
    	'Stooges':stooges,
    	'Pythons':pythons
    	}
    
    >>> dict_of_lists
    {'Marxes': ['Groucho', 'Chico', 'Harpo'], 'Stooges': ['Moe', 'Curly', 'Larry'], 'Pythons': ['Chapman', 'Cleese', 'Gilliam', 'Jones', 'Palin']}
    ```
    
5. 只能用 Tuple 當成其他字典的 Key
    - 由於字典的 Key 不可變，所以**不能把串列，字典或集合**變成其他字典的 Key 。
    - Tuple 特色是建立後不可更改
    
    ```python
    >>> houses = {
    	(44.79, -93.14, 285):'My House',
    	(38.89, -77.03, 13):'The Whilt House'
    	}
    ```