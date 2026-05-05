# SQL 建立資料表

# 基本概念

---

- 表格被分為欄位 (column) 及列位 (row)。每一列代表一筆資料，而每一欄代表一筆資料的一部份。
- 當我們對表格下定義時，需要註明欄位的標題，以及那個欄位的資料種類。

# **CREATE TABLE**

```sql
CREATE TABLE "表格名"
("欄位 1" "欄位 1 資料種類",
"欄位 2" "欄位 2 資料種類",
... );
```

- 建立資料表，內容包含姓名、地址、生日
- ( 50 ) 代表一個 50 個字元的字串

```sql
CREATE TABLE Customer
(First_Name char(50),
Last_Name char(50),
Address char(50),
City char(50),
Country char(25),
Birth_Date datetime);
```

# ALTER TABLE

建立在資料庫中後，我們常常會發現，這個表格的結構需要有所改變。

```sql
ALTER TABLE "table_name"
[改變方式];
```

Customer 表格

| 欄位名稱 | 資料種類 |
| --- | --- |
| First_Name | char(50) |
| Last_Name | char(50) |
| Address | char(50) |
| City | char(50) |
| Country | char(25) |
| Birth_Date | datetime |

1. 加一個欄位: 加入一個叫做 "Gender" 的欄位。
    
    ```sql
    ALTER TABLE Customer ADD Gender char(1);
    ```
    
    | 欄位名稱 | 資料種類 |
    | --- | --- |
    | First_Name | char(50) |
    | Last_Name | char(50) |
    | Address | char(50) |
    | City | char(50) |
    | Country | char(25) |
    | Birth_Date | datetime |
    | Gender | char(1) |
    

1. 改變欄位名稱: 把 "Address" 欄位改名為 "Addr"。
    
    ```sql
    ALTER TABLE Customer CHANGE Address Addr char(50);
    ```
    
    | 欄位名稱 | 資料種類 |
    | --- | --- |
    | First_Name | char(50) |
    | Last_Name | char(50) |
    | Addr | char(50) |
    | City | char(50) |
    | Country | char(25) |
    | Birth_Date | datetime |
    | Gender | char(1) |
    

1. 改變欄位的資料種類: 將 "Addr" 欄位的資料種類改為 char(30)。
    
    ```sql
    ALTER TABLE Customer MODIFY Addr char(30);
    ```
    
    | 欄位名稱 | 資料種類 |
    | --- | --- |
    | First_Name | char(50) |
    | Last_Name | char(50) |
    | Addr | char(30) |
    | City | char(50) |
    | Country | char(25) |
    | Birth_Date | datetime |
    | Gender | char(1) |

1. 刪去一個欄位: 刪除 "Gender" 欄位。
    
    ```sql
    ALTER TABLE Customer DROP Gender;
    ```
    
    | 欄位名稱 | 資料種類 |
    | --- | --- |
    | First_Name | char(50) |
    | Last_Name | char(50) |
    | Addr | char(30) |
    | City | char(50) |
    | Country | char(25) |
    | Birth_Date | datetime |

# Constraint

- 可以限制哪一些資料可以存入表格中。這些限制可以在表格初創時藉由 CREATE TABLE 語句來指定，或是之後藉由 ALTER TABLE 語句來指定。

1. **NOT NULL**
    
    在沒有做出任何限制的情況下，一個欄位是允許有 NULL 值得。如果我們不允許一個欄位含有 NULL 值，我們就需要對那個欄位做出 NOT NULL 的指定。
    
    > "SID" 和 "Last_Name" 這兩個欄位是不允許有 NULL 值，而 "First_Name" 這個欄位是可以有 NULL 值得。
    > 

```sql
CREATE TABLE Customer
(SID integer NOT NULL,
Last_Name varchar (30) NOT NULL,
First_Name varchar(30));
```

1. **UNIQUE**
    
    UNIQUE 限制是保證一個欄位中的所有資料都是有不一樣的值。
    
    > "SID" 欄位不能有重複值存在，而 "Last_Name" 及 "First_Name" 這兩個欄位則是允許有重複值存在。
    > 

```sql
CREATE TABLE Customer
(SID integer UNIQUE,
Last_Name varchar (30),
First_Name varchar(30));
```

1. **CHECK**
    
    CHECK 限制是保證一個欄位中的所有資料都是符合某些條件。
    
    > "SID" 攔只能包含大於 0 的整數。
    > 

```sql
CREATE TABLE Customer
(SID integer CHECK (SID > 0),
Last_Name varchar (30),
First_Name varchar(30));
```

1. **主鍵 (Primary Key)**
    
    每一筆資料都是表格中的唯一值，主鍵可以包含一或多個欄位。當主鍵包含多個欄位時，稱為組合鍵 (Composite Key)。
    
    - 主鍵可以在建置新表格時設定 (運用 CREATE TABLE 語句)，或是以改變現有的表格架構方式設定 (運用 ALTER TABLE 語句)。
    - 在用 **ALTER TABLE** 語句來添加主鍵之前，我們需要確認被用來當做主鍵的欄位是設定為 『NOT NULL』 ；也就是說，那個欄位一定不能沒有資料。

建置新表格時設定（運用 CREATE TABLE 語句）

改變現有的表格架構方式設定（運用 ALTER TABLE 語句）

```sql
## MySQL:
CREATE TABLE Customer
(SID integer,
Last_Name varchar(30),
First_Name varchar(30),
PRIMARY KEY (SID));
```

```sql
##MySQL:

ALTER TABLE Customer ADD PRIMARY KEY (SID);
```

```sql
##SQL Server:
CREATE TABLE Customer
(SID integer PRIMARY KEY,
Last_Name varchar(30),
First_Name varchar(30));
```

```sql
##Oracle:

ALTER TABLE Customer ADD PRIMARY KEY (SID);
```

```sql
## Oracle:
CREATE TABLE Customer
(SID integer PRIMARY KEY,
Last_Name varchar(30),
First_Name varchar(30));
```

```sql
##SQL Server:

ALTER TABLE Customer ADD PRIMARY KEY (SID);
```

1. **外來鍵**
    
    一個(或數個)指向另外一個表格主鍵的欄位。目的是確定資料的參考完整性 (Referential Integrity)。換言之，只有被准許的資料值才會被存入資料庫內。
    

***CUSTOMER*** 表格記錄所有顧客的資料； ***ORDERS*** 表格記錄所有顧客訂購的資料。所有的訂購資料中的顧客都一定是要跟在 ***CUSTOMER*** 表格中存在。在這裡，我們就會在 ***ORDERS*** 表格中設定一個外來鍵，而這個外來鍵是指向 ***CUSTOMER*** 表格中的主鍵。這樣一來就可以確定所有在 ***ORDERS*** 表格中的顧客都存在 ***CUSTOMER*** 表格中。換句話說，***ORDERS*** 表格之中，不能有任何顧客是不存在於 ***CUSTOMER*** 表格中的資料。

**CUSTOMER**

| 欄位名 | 性質 |
| --- | --- |
| SID | 主鍵 |
| Last_Name |  |
| First_Name |  |

> 在以上的例子中，***ORDERS*** 表格中的 Customer_SID 欄位是一個指向 ***CUSTOMER*** 表格中 SID 欄位的外來鍵。
> 

**ORDERS**

| 欄位名 | 性質 |
| --- | --- |
| Order_ID | 主鍵 |
| Order_Date |  |
| Customer_SID | 外來鍵 |
| Amount |  |

建置新表格時設定（運用 CREATE TABLE 語句）

改變現有的表格架構方式設定（運用 ALTER TABLE 語句）

```sql
## MySQL:

CREATE TABLE ORDERS
(Order_ID integer,
Order_Date date,
Customer_SID integer,
Amount double,
PRIMARY KEY (Order_ID),
FOREIGN KEY (Customer_SID) REFERENCES CUSTOMER (SID));
```

```sql
## MySQL:

ALTER TABLE ORDERS
ADD FOREIGN KEY (Customer_SID) REFERENCES CUSTOMER (SID);
```

```sql
## Oracle:

CREATE TABLE ORDERS
(Order_ID integer PRIMARY KEY,
Order_Date date,
Customer_SID integer REFERENCES CUSTOMER (SID),
Amount double);
```

```sql
## Oracle:

ALTER TABLE ORDERS
ADD (CONSTRAINT fk_orders1) FOREIGN KEY (Customer_SID) REFERENCES CUSTOMER (SID);
```

```sql
## SQL Server:

CREATE TABLE ORDERS
(Order_ID integer PRIMARY KEY,
Order_Date datetime,
Customer_SID integer REFERENCES CUSTOMER (SID),
Amount double);
```

```sql
## SQL Server:

ALTER TABLE ORDERS
ADD FOREIGN KEY (Customer_SID) REFERENCES CUSTOMER (SID);
```

# DROP TABLE

資料庫中**徹底刪除**一個表格

```sql
DROP TABLE "表格名";
```

# **TRUNCATE TABLE**

清除一個表格中的所有資料，表格本身會繼續存在。

```sql
TRUNCATE TABLE "表格名";
```

```sql
TRUNCATE TABLE Customer;
```

# **INSERT INTO**

一次輸入一筆資料

> 在 January 10, 1999，Los Angeles 店有 $900 的營業額
> 

```sql
INSERT INTO "表格名" ("欄位1", "欄位2", ...)
VALUES ("值1", "值2", ...);
```

Store_Information 型態

| 欄位名稱 | 資料種類 |
| --- | --- |
| Store_Name | char(50) |
| Sales | float |
| Txn_Date | datetime |

```sql
INSERT INTO Store_Information (Store_Name, Sales, Txn_Date)
VALUES ('Los Angeles', 900, 'Jan-10-1999');
```

Store_Information 表

| Store_Name | Sales | Txn_Date |
| --- | --- | --- |
| **'Los Angeles'** | **900** | **'Jan-10-1999'** |

一次輸入多筆的資料

> 將 1998 年的營業額資料放入 ***Sales_Information*** 表格，而我們知道資料的來源是可以由 ***Sales_Information*** 表格取得
> 

```sql
INSERT INTO "表格1" ("欄位1", "欄位2", ...)
SELECT "欄位3", "欄位4", ...
FROM "表格2";
```

```sql
INSERT INTO Store_Information (Store_Name, Sales, Txn_Date)
SELECT Store_Name, Sales, Txn_Date
FROM Sales_Information
WHERE Year(Txn_Date) = 1998;
```

# **UPDATE**

修改表格中的資料。

> Los Angeles 在 1999 年 1 月 8 號的營業額 $300 改為 $500
> 

```sql
UPDATE "表格名"
SET "欄位1" = [新值]
WHERE "條件";
```

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

```sql
UPDATE Store_Information
SET Sales = 500
WHERE Store_Name = 'Los Angeles'
AND Txn_Date = 'Jan-08-1999';
```

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 500 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

也可以同時修改好幾個欄位。這語法如下：

```sql
UPDATE "表格"
SET "欄位1" = [值1], "欄位2" = [值2]
WHERE "條件";
```

# **DELETE FROM**

直接由資料庫中去除一些資料。

> 將有關 Los Angeles 的資料全部刪除。
> 

```sql
DELETE FROM "表格名"
WHERE "條件";
```

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| Los Angeles | 1500 | 05-Jan-1999 |
| San Diego | 250 | 07-Jan-1999 |
| Los Angeles | 300 | 08-Jan-1999 |
| Boston | 700 | 08-Jan-1999 |

```sql
DELETE FROM Store_Information
WHERE Store_Name = 'Los Angeles';
```

Store_Information 表格

| **Store_Name** | **Sales** | **Txn_Date** |
| --- | --- | --- |
| San Diego | 250 | Jan-07-1999 |
| Boston | 700 | Jan-08-1999 |