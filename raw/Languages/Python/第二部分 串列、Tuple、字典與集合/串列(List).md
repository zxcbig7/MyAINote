---
tags: [python, data-structures, programming]
---

> 關聯：[[python]]

# 串列(List)

---

## 特色

1. 同一個值可能出現一次以上
2. 指派後，可更改

---

## 建立

- 用 [] 或 list() 來建立
    
    ```python
    >>> test = ['a','b','c','c']
    >>> test
    ['a', 'b', 'c','c']
    
    >>> test = list()
    >>> test
    []
    ```
    
- 用 list() 來將其他資料類型轉成串列
    
    ```jsx
    >>> test = 'cat'
    >>> list(test)
    ['c', 'a', 't']
    
    >>> a_tuple = ('ready','fire','aim')
    >>> list(a_tuple)
    ['ready', 'fire', 'aim']
    ```
    
- 用 split() 來分割
    
    ```jsx
    >>> birthday = '1/6/1952'
    >>> birthday.split('/')
    ['1', '6', '1952']
    
    #如果字串中有兩個以上 / 的情況
    >>> test = 'a/b//c/d///e'
    >>> test.split('/')
    ['a', 'b', '', 'c', 'd', '', '', 'e']
    
    #改成 split(//) 的時候
    >>> test = 'a/b//c/d///e'
    >>> test.split('//')
    ['a/b', 'c/d', '/e']
    ```
    

---

## 應用

- 串列的串列
    
    ```python
    >>> a = ['a1','a2','a3']
    >>> b = ['b1','b2']
    >>> all_letters = [a,b,]
    >>> all_letters
    [['a1', 'a2', 'a3'], ['b1', 'b2']]
    
    #指定某項
    >>> all_letters[1][0]
    'b1'
    ```
    

---

- 用 [ *位移值* ] 來取得項目
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> test[0]
    'a'
    >>> test[-1]
    'd'
    ```
    
    補充 : 如果是正著數，從0開始算
    
- 用 [ *位移值* ] 來更改項目
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> test[0] = 'e'
    >>> test[0]
    'e'
    
    ```
    
- 用一個範圍的位移值以 Slice 取出項目
    
    ```python
    >>> test = ['a','b','c','d']
    
    #取第 1 個 至 第 2 個
    >>> test[0:2]
    ['a', 'b']
    
    #取第 2 個 至 第 3 個
    >>> test[1:3]
    ['b', 'c']
    
    #第一個開始，之後每兩個取一個
    >>> test[::2]
    ['a', 'c']
    
    #逆向
    >>> test[::-1]
    ['d', 'c', 'b', 'a']
    ```
    

---

- 用 append() 將項目加到結尾
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> test.append('e')
    >>> test
    ['a', 'b', 'c', 'd', 'e']
    ```
    
    注意 : append()只能將項目加到最後面
    
- 用 insert() 與位移值來加入一個項目
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> test.insert(2,'x')
    >>> test
    ['a', 'b', 'x', 'c', 'd']
    ```
    
    注意 : 與append()不同，可以加到任意位移值
    
- 用 extend() 或 += 來結合兩個串列
    
    ```python
    >>> test = ['a','b','c','d']
    >>> test_add = ['d','e','f']
    
    #方法1
    >>> test.extend(test_add)
    >>> test
    ['a', 'b', 'c', 'd', 'd', 'e', 'f']
    
    #方法2
    >>> test += test_add
    >>> test
    ['a', 'b', 'c', 'd', 'd', 'e', 'f']
    ```
    

---

- 用 del 與 *位移值* 刪除一個項目
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> del test[2]
    >>> test
    ['a', 'b', 'd']
    ```
    
- 用 remove() 與 *值* 來刪除項目
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> test.remove('a')
    >>> test
    ['b', 'c', 'd']
    ```
    
    注意 : remove()通常用在不知道該項目位移值為何
    

---

- 用 pop() 與位移值來取得一個項目，並刪除它
    
    ```python
    >>> test = ['a','b','c','d']
    
    ## 此時 b 從 test 中移出
    >>> test.pop(1)
    'b'
    >>> test
    ['a', 'c', 'd']
    
    ##如果沒使用引述，預設 -1
    >>> test.pop()
    'd'
    >>> test
    ['a', 'b', 'c']
    ```
    
- 用 index() 與值來尋找某個項目的位移值
    
    ```python
    >>> test = ['a','b','c','d']
    >>> test.index('d')
    3
    
    ##若有重複，取最前面的數字
    >>> test = ['d','a','b','c','d']
    >>> test.index('d')
    0
    ```
    
- 用 in 來測試是否有該值
    
    ```python
    >>> test = ['a','b','c','d']
    >>> 'a' in test
    True
    >>> 'z' in test
    False
    ```
    
- 用 count() 來算出某個值出現幾次
    
    ```python
    >>> test = ['a','a','b','c','c','c','c','d','d','d']
    >>> test.count('a')
    2
    >>> test.count('d')
    3
    >>> test.count('g')
    0
    ```
    

---

- 用 join() 來轉換成字串
    
    ```python
    >>> test = ['a','b','c','d']
    
    >>> ','.join(test)
    'a,b,c,d'
    
    ```
    
    進階 : join() 是 split() 的相反
    
    ```python
    >>> friends = ['Harry','Hermione','Ron']
    >>> separator = ' * '
    
    ##串列 轉 字串
    >>> joined = separator.join(friends)
    >>> joined
    'Harry * Hermione * Ron'
    
    ##字串 轉回 串列
    >>> joined.split(separator)
    ['Harry', 'Hermione', 'Ron']
    
    ```
    
- 用 sort() 來排序項目
    
    ```python
    >>> test = ['Groucho','Chico','Harpo']
    
    #sort()會就地改變串列順序
    >>> test.sort()
    >>> test
    ['Chico', 'Groucho', 'Harpo']
    
    #無法用sort()新增副本
    >>> test_sorted = test.sort()
    >>> test
    ['Chico', 'Groucho', 'Harpo']
    >>> test_sorted
    >>>
    
    #sorted()會產生一個排列過後的副本，原本的不變
    >>> test_sorted = sorted(test)
    >>> test
    ['Groucho', 'Chico', 'Harpo']
    >>> test_sorted
    ['Chico', 'Groucho', 'Harpo']
    ```
    
    ```python
    
    ## 可以排列多種資料型態
    >>> test = [3,5,1,7,0.5,4.4]
    
    >>> test.sort()
    >>> test
    [0.5, 1, 3, 4.4, 5, 7]
    
    ## 預設是昇冪排列，引述用 reverse = True 改為降冪
    >>> test.sort(reverse = True)
    >>> test
    [7, 5, 4.4, 3, 1, 0.5]
    ```
    
- 用 len() 來取的長度
    
    ```python
    >>> test = [1,2,3,4,5,6,7]
    
    >>> len(test)
    7
    ```
    

---

- 用 = 來指派，用 copy() 來複製
    
    ```python
    >>> a = [1,2,3]
    >>> b = a
    
    >>> b[0] = 4
    
    >>> a
    [4, 2, 3]
    >>> b
    [4, 2, 3]
    ##兩函數互相影響
    ```
    
    ```python
    >>> a = [1,2,3]
    >>> b = a.copy()
    
    >>> a[0] = 4
    
    >>> a
    [4, 2, 3]
    >>> b
    [1, 2, 3]
    ##兩函數互相獨立，不影響
    ```
    
- 三種方式複製出獨立的串列
    
    ```python
    >>> a = [1,2,3]
    
    #1. 串列的copy()函式
    >>> b = a.copy ()
    
    #2. list() 轉換函式
    >>> c = list(a)
    
    #3. 串列 slice[:]
    >>> d = a[:]
    
    >>> b
    [1, 2, 3]
    >>> c
    [1, 2, 3]
    >>> d
    [1, 2, 3]
    ```