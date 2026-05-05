# Tuple

---

## 特色

1. 同一個值可能出現一次以上
2. 指派後，不可變(無法添加、刪除、更改)

## 建立

- 用 () 來建立 Tuple
    
    ```python
    >>> test = ('a','b','c')
    >>> test
    ('a', 'b', 'c')
    ```
    
- ***tuple*** 開箱 **( *unpacking* )，**可以被一次指派給多個變數
    
    ```python
    >>> test = ('Larry','Matty','Vic')
    
    >>> a, b, c = test
    
    >>> a
    'Larry'
    >>> b
    'Matty'
    >>> c
    'Vic'
    ```
    
- 用 tuple()  轉換函式
    
    ```python
    
    >>> list_test = ['Hi','Ya','Bye']
    >>> tuple(list_test)
    ('Hi', 'Ya', 'Bye')
    ```
    
- 用 tuple 來交換值
    
    ```python
    >>> passward = 'swordfish'
    >>> icecream = 'tuttifrutti'
    
    >>> passward, icecream = icecream, passward
    
    >>> passward
    'tuttifrutti'
    >>> icecream
    'swordfish'
    ```
    

---

# Tuple V.S. 串列

- Tuple 通常可以用來取代串列，但沒有append()、insert()等等。(Tuple 不可修改)

既然不能修改，為何還要選 Tuple 來取代 List ?

- tuple 佔用空間較小
- 不會不小心破壞 tuple 的項目
- 可以把 tuple 當成字典鍵
- 可以將**具名 tuple** (Named tuple )當成物件的簡化替代品
- 函式引述是已 tuple 的形式傳入