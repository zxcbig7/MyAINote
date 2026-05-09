# SQL 資料庫基本指令

---

### 基本SQL架構（SELECT, FROM, WHERE）

- 條件可以用 >, <, =
- 可以用 ( ) 來代表條件的先後次序
- { }+ ：代表{ }之內的情況會發生一或多次，可用 AND 與 OR 連接不同條件。
- WHERE 不是必要的條件，可打可不打

> 在 ***Store_Information*** 表格中選出所有 Sales 高於 $1,000 或是 Sales 在 $500 及 $275 之間的名稱資料
> 

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| San Francisco | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

---

```sql
SELECT "欄位名"
FROM "表格名"
WHERE "條件"
{[AND|OR] "簡單條件"}+
```

```sql
SELECT Store_Name
FROM Store_Information
WHERE Sales > 1000
OR (Sales < 500 AND Sales > 275);
```

<aside>
➡️ 結果
Store_Name
Los Angeles
San Francisco

</aside>

---

### 知道表格/欄位內有哪些不同的值

- SELECT 後面加 DISTINCT

```sql
SELECT DISTINCT "欄位名"
FROM "表格名";
```

---

### IN 的使用

- 配合WHERE使用
- 括弧內可以有一或多個值，而不同值之間由逗點分開。值可以是數目或是文字。若在括弧內只有一個值，那這個子句就等於

範例:

> ***Store_Information*** 表格中找出所有含蓋 Los Angeles 或 San Diego 的資料
> 

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| San Francisco | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

```sql
SELECT *
FROM Store_Information
WHERE Store_Name IN ('Los Angeles', 'San Diego');
```

<aside>
➡️ 結果

Store_Name 	Sales 	Txn_Date
Los Angeles 	1500 	Jan-05-1999
San Diego 	250   	Jan-07-1999

</aside>

---

### **BETWEEN**

- 配合WHERE使用
- 可以運用一個範圍 (range) 內抓出資料庫中的值。
- 在不同的資料庫中，日期的儲存法可能會有所不同。

> ***Store_Information*** 表格中找出所有介於 January 6, 1999 及 January 10, 1999 中的資料
> 

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| San Francisco | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

```sql
SELECT "欄位名"
FROM "表格名"
WHERE "欄位名" BETWEEN '值一' AND '值二';
```

```sql
SELECT *
FROM Store_Information
WHERE Txn_Date BETWEEN 'Jan-06-1999' AND 'Jan-10-1999';
```

<aside>
➡️ 結果

Store_Name 	Sales 	Txn_Date
San Diego 	250 	Jan-07-1999
San Francisco 	300 	Jan-08-1999
Boston 	700 	Jan-08-1999

</aside>

---

### 萬用字元

- % (百分比符號)：代表零個、一個、或數個字母。
- _ (底線)：代表剛好一個字母。
- 配合LIKE關鍵詞使用

例子

- 'A_Z’：'ABZ' 和 'A2Z' 都符合這一個模式，而 'AKKZ' 並不符合。（只能有一個字）
- 'ABC%'：'ABCD' 和 'ABCABC' 都符合這個模式。
- '%XYZ': 'WXYZ' 和 'ZZXYZ' 都符合這個模式。
- '%AN%':  'LOS ANGELES' 和 'SAN FRANCISCO' 都符合這個模式。
- '_AN%'： 'SAN FRANCISCO' 符合這個模式，而 'LOS ANGELES' 則不符合這個模式。

---

### LIKE

- **WHERE** 子句中會用到的指令
- **LIKE** 能像**IN**或**BETWEEN**一樣，讓我們依據一個模式 (pattern) 來找出我們要的資料。
- {模式} 經常包括萬用字元 (wildcard)。

> 要找出所有名稱內包含 AN 這兩個字串的資訊
> 

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| San Francisco | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

```sql
SELECT "欄位名"
FROM "表格名"
WHERE "欄位名" LIKE {模式};
```

```sql
SELECT *
FROM Store_Information
WHERE store_name LIKE '%AN%';
```

<aside>
➡️ 結果

Store_Name  	Sales  	Txn_Date
LOS ANGELES 	1500 	Jan-05-1999
SAN FRANCISCO 	300 	Jan-08-1999
SAN DIEGO 	250 	Jan-07-1999

</aside>

---

### **ORDER BY**

- ORDER 一定在 WHERE 後面
- **ASC**（預設）代表結果會以由小往大的順序列出，而 **DESC** 代表結果會以由大往小的順序列出。
- 也可用欄位的順序 (依據 SQL 句中的順序)來指定排序欄位。
- 可以多欄位排序：範例為”欄位一" 由小往大排。 若 "欄位一" 相等，再依據 "欄位二" 由小往大排。
    
    
    | **Store_Name** | **Sales** | **Txn_Date** |
    | --- | --- | --- |
    | Los Angeles | 1500 | 05-Jan-1999 |
    | San Diego | 250 | 07-Jan-1999 |
    | San Francisco | 300 | 08-Jan-1999 |
    | Boston | 700 | 08-Jan-1999 |
    
    ```sql
    ORDER BY "欄位一" ASC, "欄位二" ASC
    ```
    

```sql
SELECT "欄位名"
FROM "表格名"
[WHERE "條件"]
ORDER BY "欄位名" [ASC, DESC];
```

```sql
SELECT Store_Name, Sales, Txn_Date
FROM Store_Information
ORDER BY Sales DESC;
```

```sql
SELECT Store_Name, Sales, Txn_Date
FROM Store_Information
ORDER BY 2 DESC;
```

<aside>
➡️ 結果

Store_Name 	Sales 	Txn_Date
Los Angeles 	1500 	Jan-05-1999
Boston 	700 	Jan-08-1999
San Francisco 	300 	Jan-08-1999
San Diego 	250 	Jan-07-1999

</aside>

---

### 函數

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

**AVG (平均)：**求出 Sales 欄位的平均值

```sql
SELECT AVG(Sales) FROM Store_Information;
```

<aside>
➡️ AVG(Sales)

687.5

</aside>

**COUNT (計數)：**有幾筆 Store_Name 欄不是空白的資料

```sql
SELECT COUNT (Store_Name)
FROM Store_Information
WHERE Store_Name IS NOT NULL;
```

```sql
SELECT COUNT (DISTINCT Store_Name)
FROM Store_Information;
```

<aside>
➡️ COUNT (Store_Name)

4

</aside>

- "IS NOT NULL" 是 "這個欄位不是空白" 的意思。

<aside>
➡️ COUNT (DISTINCT Store_Name)

3

</aside>

- 計算有多少筆不同的資料

**MAX (最大值) / MIN (最小值)**

```sql
SELECT MAX (Sales) FROM Store_Information;
```

<aside>
➡️ MAX (Sales)

1500

</aside>

**SUM (總合)**

```sql
SELECT SUM (Sales) FROM Store_Information;
```

<aside>
➡️ SUM (Sales)

2750

</aside>

---

### GROUP BY

- 配合函式使用，依照群組使用該函數
- 當選擇不只一個欄位，且其中至少一個欄位有包含函數的運用時，就需要用到 **GROUP BY** 這個指令。
- **除了有包括函數的欄位外，都需要將其他的欄位放在 GROUP BY 的子句中。**

```sql
SELECT "欄位1", SUM("欄位2")
FROM "表格名"
GROUP BY "欄位1";
```

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

```sql
SELECT Store_Name, SUM(Sales)
FROM Store_Information
GROUP BY Store_Name;
```

| **Store_Name** | **SUM(Sales)** |
| --- | --- |
| **Los Angeles** | **1800** |
| **San Diego** | **250** |
| **Boston** | **700** |

---

### HAVING

- 功能：針對函數產生的值來設定條件呢（WHERE針對欄位值）
- 通常放在語法架構的最後

```sql
SELECT "欄位1", SUM("欄位2")
FROM "表格名"
GROUP BY "欄位1"
HAVING (函數條件);
```

```sql
SELECT Store_Name, SUM(Sales)
FROM Store_Information
GROUP BY Store_Name
HAVING SUM(Sales) > 1500;
```

- 如果被 **SELECT** 的只有函數欄， 那就不需要 **GROUP BY** 子句。

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

| **Store_Name** | **SUM(Sales)** |
| --- | --- |
| **Los Angeles** | **1800** |

---

### 別名

- 常用別名有兩種：欄位別名及表格別名。

> Store_Information被改成A1, SUM函式被改成"Total Sales"
> 

```sql
SELECT "表格別名"."欄位1" "欄位別名"
FROM "表格名" "表格別名";
```

```sql
SELECT A1.Store_Name Store, SUM(A1.Sales) "Total Sales"
FROM Store_Information A1
GROUP BY A1.Store_Name;
```

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

| **Store** | **Total Sales** |
| --- | --- |
| **Los Angeles** | **1800** |
| **San Diego** | **250** |
| **Boston** | **700** |

---

### AS

- 用來指定欄位別名或是表格別名。它是被放在欄位名和欄位別名之間，或是放在表格名和表格別名之間。

```sql
SELECT "表格別名"."欄位1" AS "欄位別名"
FROM "表格名" AS "表格別名";
```

```sql
SELECT A1.Store_Name AS Store, SUM(A1.Sales) AS 'Total Sales'
FROM Store_Information AS A1
GROUP BY A1.Store_Name;
```

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

| **Store** | **Total Sales** |
| --- | --- |
| **Los Angeles** | **1800** |
| **San Diego** | **250** |
| **Boston** | **700** |

---

### JOIN 概念

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

Geography 表格

| **Region_Name** | **Store_Name** |
| --- | --- |
| East | Boston |
| East | New York |
| West | Los Angeles |
| West | San Diego |

***Geography*** 表格告訴我們每一區有哪些店，而 ***Store_Information*** 告訴我們每一個店的營業額。若我們要知道每一區的營業額，我們需要將這兩個不同表格中的資料串聯起來。會發現它們可經由一個相同的欄位，Store_Name，連接起來。

```sql
SELECT A1.Region_Name REGION, SUM(A2.Sales) SALES
FROM Geography A1, Store_Information A2
WHERE A1.Store_Name = A2.Store_Name
GROUP BY A1.Region_Name;
```

| **REGION** | **SALES** |
| --- | --- |
| **East** | **700** |
| **West** | **2050** |

第一行中，我們告訴 SQL 去選出兩個欄位：第一個欄位是 ***Geography*** 表格中的 Region_Name 欄位 (我們取了一個別名叫做 REGION)；第二個欄位是 ***Store_Information*** 表格中的 Sales 欄位 (別名為 SALES)。請注意在這裡我們有用到表格別名：***Geography*** 表格的別名是 A1，***Store_Information*** 表格的別名是 A2。

第三行中， **WHERE** 子句是闡述連接條件的地方。要確認 ***Geography*** 表格中 Store_Name 欄位的值與 ***Store_Information*** 表格中 Store_Name 欄位的值是相等的。

- 如果 **WHERE** 子句是錯誤的，我們就極可能得到一個笛卡兒連接 (Cartesian join)。笛卡兒連接會造成我們得到所有兩個表格每兩行之間所有可能的組合。在這個例子中，笛卡兒連接會讓我們得到 4 x 4 = 16 行的結果。
- 若我們沒有用表格別名（A1,A2）的話，需要特別指定表個的欄位值（如下範例），所以用別名比較易讀

```sql
SELECT Geography.Region_Name REGION, SUM(Store_Information.Sales) SALES
```

---

### 外部連結

- 上方JOIN例子屬於左連接 (left join)，又稱內部連接 (INNER JOIN)，要兩個表格內都有同樣的值，那一筆資料才會被選出。
- 右連結(right join)，又稱外部連結(OUTER JOIN)，用來列出一個表格中每一筆的資料，無論它的值在另一個表格中有沒有出現。
- 外部連接的語法是依資料庫的不同而有所不同的。在 Oracle 上，會在 **WHERE** 子句中要選出所有資料的那個表格之後加上一個 "(+)" 來代表說這個表格中的所有資料我們都要。

Store_Information

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

Geography

| **Region_Name** | **Store_Name** |
| --- | --- |
| East | Boston |
| East | New York |
| West | Los Angeles |
| West | San Diego |

```sql
SELECT A1.Store_Name, SUM(A2.Sales) SALES
FROM Georgraphy A1, Store_Information A2
WHERE A1.Store_Name = A2.Store_Name (+)
GROUP BY A1.Store_Name;
```

> 此例子如果沒有打+符號會導致New York不會出現在結果表中
> 

| **Store_Name** | **SALES** |
| --- | --- |
| **Boston** | **700** |
| **New York** |  |
| **Los Angeles** | **1800** |
| **San Diego** | **250** |

---

### 字串連結

- MySQL: CONCAT( )
- Oracle: CONCAT( ), ||
    - Oracle 的 CONCAT( ) 只允許兩個參數；換言之，一次只能將兩個字串串連起來。不過可以用 '||' 來一次串連多個字串。
- SQL Server: +

Geography 表格

| **Region_Name** | **Store_Name** |
| --- | --- |
| East | Boston |
| East | New York |
| West | Los Angeles |
| West | San Diego |

**MySQL/Oracle**:

```sql
SELECT CONCAT(Region_Name, Store_Name) FROM Geography
WHERE Store_Name = 'Boston';
```

> 結果：**'EastBoston'**
> 

**Oracle**:

```sql
SELECT Region_Name || ' ' || Store_Name FROM Geography
WHERE Store_Name = 'Boston';
```

> 結果：**'East Boston'**
> 

**SQL Server**:

```sql
SELECT Region_Name + ' ' + Store_Name FROM Geography
WHERE Store_Name = 'Boston';
```

> 結果：**'East Boston'**
> 

---

### Replace

- 改變字串的內容
- 在字串 str1 中，當 str2 出現時，將其以 str3 替代。

```sql
Replace (str1, str2, str3)
```

Geography

| **Region_Name** | **Store_Name** |
| --- | --- |
| East | Boston |
| East | New York |
| West | Los Angeles |
| West | San Diego |

```sql
SELECT REPLACE (Region_Name, 'ast', 'astern')
FROM Geography;
```

| Region_Name |
| --- |
| Eastern |
| Eastern |
| West |
| West |