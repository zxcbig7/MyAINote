# SQL 指令語法速查

## SQL 分類

### 資料操作語言(Data Manipulation Language, DML)

資料操作語言就是使用者在查詢、加入、刪除、更新等動作時所需要的語言。

- SELECT 搜尋資料
- INSET 加入資料
- UPDATE 更新資料
- DELETE 刪除資料

### 資料定義語言(Data Definition Language, DDL)

資料定義語言是用來定義儲存資料用的資料庫或表，或是用來定義參照資訊視圖所使用的語言。

- CREATE 建立資料庫、資料表、視圖
- ALTER 變更資料庫、資料表、視圖
- DROP 刪除資料庫、資料表、視圖

### 資料控制語言(Data Control Language, DCL)

資料控制語言是用來設定有關資料庫使用者管理或是操作資料時所需要的語法。

- GRANT 給予資料庫使用者權限
- REVOKE 刪除資料庫使用者權限
- COMMIT 確定資料變更
- ROLLBACK 取消資料變更

---

# 備註功能

```sql
# 可以用井字號備註
-- 也可以用兩槓備註
/* 也可以斜線星號備註 */
```

# SQL資料型態

資料型態大致上分為五類：「數值型態」、「字串型態」、「日期型態」、「二進位型態」、「位元型態」這五類。

|  | 類型 | 資料型別 |
| --- | --- | --- |
| 數值型態 | 整數 | TINYINT 、 SAMLLINT 、 MEDIUMINT 、 INT 、 BIGINT 、 |
| 數值型態 | 實數（小數） | NUMERIC 、 DECIMAL 、 DEC 、 FIXED |
| 數值型態 | 浮點數 | FLOAT 、 DOUBLE |
| 數值型態 | 倍精度浮點數 | DOUBLE DECOSION 、 REAL |
| 字串型態 | 固定長度字串 | CHAR 、 BINARY |
| 字串型態 | 變動常數字串 | VARCHAR 、 VARBINARY 、TINYTEXT 、 TEXT 、 MEDIUMTEXT 、LONGTEXT |
| 日期型態 | 日期 | DATE 、 YEAR |
| 日期型態 | 時間 | TIME |
| 日期型態 | 日期時間 | DATETIME 、 TIMESTAMP |
| 二進位型態 | 可變長度二進位 | TINYLOB 、 BLOB 、 MEDIUMBLOB 、LONGBLOB |
| 位元型態 | 固定長度位元 | BIT |

# 運算子

## 算數運算子

運算子分為加（+）、減（-）、乘（*）、除（/）、餘數（mod）五個基本運算物件，運算子會對左右邊的項目進行運算，語法為：（欄位或數值）（運算子）（欄位或數值）

```sql
SELECT class. price + 50 New_Price FROM ball;
```

- 每個價格+50後，再把price + 50欄位名稱改為New_Price

```sql
SELECT class. price * 10 New_Price FROM ball;
```

```sql
SELECT class, price, qty, price * qty Total FROM ball;
```

- 乘法除了可以乘數字以外還可以讓多個欄位相乘

```sql
select mainid, phase, part_no, dps_day, mod(qty,1) new_QTY from c_lcddps_act_input
```

- 其他SQL的餘數使用%符號，但Oracle只有mod

## 連結運算子

可使用 CONCAT(欄位1，欄位2)，連接最多兩個字串欄位。

```sql
select mainid, CONCAT(fab, phase),part_no, dps_day, qty from c_lcddps_act_input
```

若打算連接多個字串就必須要用巢狀 CONCAT(CONCAT(欄位1，欄位2), 欄位3)。

```sql
select mainid, CONCAT(CONCAT(fab,'-'), phase),part_no, dps_day, qty from c_lcddps_act_input
```

## 比較運算子

比較運算子分為等於『=』；不等於『<>』、『!=』；小於『<』；小於等於『＜=』：大於『>』；大於等於『>=』；存在指定範圍『BETWEEN』；存在指定集合『IN』；萬用字元搜查『LIKE』；是否為空值『IS NULL』；是否不為空值『IS NOT NULL』。

資料庫搜尋進行比較後，結果為真則回傳『1』結果為假則回傳『0』；結果不確定則為『NULL』。

```sql
select mainid, fab, phase, qty from c_lcddps_act_input where qty IS NULL
```

```sql
select mainid, fab, phase, qty from c_lcddps_act_input where qty IS NOT NULL
```

```sql
select mainid, fab, phase, qty from c_lcddps_act_input where qty between 100 and 500
```

```sql
select mainid, fab, phase, qty from c_lcddps_act_input where qty in (785, 700, 150)
```

## 邏輯運算子

分為三類：AND、OR、NOT

```sql
select mainid, fab, qty from c_lcddps_act_input where qty in (785,700, 150) AND mainid = 2003
```

```sql
select mainid, fab, qty from c_lcddps_act_input where qty > 10 OR mainid = 2003
```

```sql
select mainid, fab, qty from c_lcddps_act_input where NOT qty < 10
```

<aside>
⚠️ **優先順序：**NOT > AND > OR
可以用括號( )來控制順序。

</aside>

## 萬用字元與LIKE

LIKE 主要是透過萬用字元『%』、『_』來進行檢查。『%』為零或多字元、『_』為單一字元。

```sql
-- 搜尋名稱中有50但不能在頭尾。
select mainid, fab, part_no, qty from c_lcddps_act_input where 1=1
AND PART_NO LIKE '%50%'
AND PART_NO NOT LIKE '50%'
AND PART_NO NOT LIKE '%50'
```

```sql
-- 搜尋 PART_NO 名稱中有 5 個字元的後接 T 資料。
select mainid, fab, part_no, qty from c_lcddps_act_input where 1=1
AND PART_NO LIKE '_____T%'
```

# 建立及刪除資料庫

### 建立資料庫

```sql
CREATE DATABASE exampledatabases;
select name from v$database; --搜尋DATABASE名稱
```

### 刪除資料庫

```sql
DROP DATABASE exampledatabases;
SELECT name FROM v$database; --搜尋DATABASE名稱
```

# 建立與刪除資料表

## 建立資料表

```sql
CREATE TABLE 資料表名稱(
欄位名稱 資料型別,
欄位名稱 資料型別,
欄位名稱 資料型別,
...);
```

**建立資料表可以設定以下規則**

1. **建立必須有值的欄位：**若該欄位必須非空值，則需要加 NOT NULL
2. **建立唯一值的欄位：**若該欄位的值具有唯一性的話，需要加 UNIQUE
3. **建立預設值的欄位：**若匯入的資料中該欄位為NULL時填入預設值，需要在最後加入DEFAULT

```sql
CREATE TABLE example_table(
ID int NOT NULL UNIQUE,
name varchar(10) NOT NULL,
height varchar(10) DEFAULT 170,
weight varchar(10) DEFAULT 70);
```

## 刪除資料表

```sql
DROP TABLE example_table;
```

# 查詢的基本操作

SELECT 後方加上要搜尋的欄位或是萬用字元（*），FROM後加入要搜尋的資料表。

### 搜尋所有欄位

```sql
SELECT * FROM 資料表名稱;
```

### 搜尋特定欄位

```sql
SELECT 欄位1, 欄位2, 欄位3 FROM 資料表名稱;
```

<aside>
⚠️ 不一定要按照表格順序輸出欄位

</aside>

### 合併欄位中重複的資料

使用 DISTINCT ，搜尋時會自動過濾該欄位相同的資料

```sql
SELECT DISTINCT PART_NO FROM c_lcddps_act_input
```

### 將欄位的結果使用別名

把計算結果的欄位名稱設定為 BMI。

```sql
SELECT name, weight/((height/100)*(height/100)) BMI FROM student
```

# 條件查詢

### 指定單個條件查詢

```sql
SELECT * FROM 資料表 WHERE 條件式
```

### 指定多個條件查詢

```sql
SELECT * FROM 資料表 WHERE 1=1
AND 條件式1
AND 條件式2
OR  條件式3
```

# 排序查詢結果

### 指定欄位排序

使用 ORDER BY 進行排序

```sql
SELECT * FROM 資料表 ORDER BY 指定欄位
```

### 指定遞增、遞減排序

ASC 為遞增、DESC為遞減

```sql
SELECT * FROM 資料表 ORDER BY 指定欄位 (ASC/DESC)
```

<aside>
⚠️ 預設為遞增排序 ASC，所以通常只需要記得 DESC 就好了

</aside>

### 指定多欄位遞增、遞減排序

```sql
SELECT * FROM 資料表 ORDER BY 指定欄位1 ASC, 指定欄位2 DESC
```

# 群組化應用

### 將資料輸出以群組化彙總

使用 GROUP BY 進行群組化

```sql
SELECT * FROM 資料表 GROUP BY 指定欄位
```

GROUP BY 進行群組化以後，還需要使用函數才能將搜尋資料完整呈現。

```sql
SELECT part_no, count(*), sum(qty) FROM c_lcddps_act_input GROUP BY PART_NO;
```

- MIN(欄位) 最小值
- MAX(欄位) 最大值
- SUM(欄位) 資料加總
- AVG(欄位) 資料平均
- count(*) 群組資料比數
- STDDEV(欄位) 母體標準差
- VARIANCE(欄位) 變異數

### 多欄位群組化

```sql
select mainid, part_no, sum(qty) Sum from c_lcddps_act_input GROUP BY mainid, PART_NO;
```

### 將群組化資料設定條件

使用 HAVING，顯示一部分符合條件的群組化資料。

```sql
SELECT * FROM 資料表 GROUP BY 指定欄位 HAVING 指定條件
```

```sql
SELECT part_no, count(*), sum(qty) 
FROM c_lcddps_act_input 
GROUP BY PART_NO
HAVING count(*) > 100; --群組資料筆數要大於100
```

<aside>
⚠️ WHERE 與 HAVING 差別在於 WHERE 用於GROUP BY 之前，因此無法對於GROUP BY之後進行判斷。無論如何再GROUP BY之後都要使用HAVING 來進行判斷。

</aside>

### 群組化資料進行彙整

使用 ROLLUP 可以出現彙整列。(最後一個row會生成加總的資料)

```sql
SELECT part_no, COUNT(*) AS cnt, SUM(qty) AS total_qty
FROM c_lcddps_act_input
GROUP BY ROLLUP (part_no)
HAVING COUNT(*) > 100 OR part_no IS NULL;
```

# 資料表指定與結合

### 搜尋特定資料表

```sql
SELECT ... FROM 資料表1， 資料表2...
```

<aside>
⚠️ 當有任兩個資料表有相同的欄位，會出現錯誤。需要透過『.』指定資料表。

```sql
SELECT 資料表1.欄位1 FROM 指定資料表1， 指定資料表2...
```

</aside>

### 透過別名來指定資料表

```sql
SELECT ... FROM 資料表1 資料表1別名,資料表2 資料表2別名...
```

```sql
SELECT A.mainid, A.part_no, dps_day, qty 
FROM c_lcddps_act_input A, c_lcddps_line_capa L
WHERE A.part_no = L.part_no;
```

### 資料表的結合敘述

資料表的結合分為兩個種類，第一個為交叉結合，第二個為自然結合。

### 交叉結合

兩張資料表格透過外積的方式來結合，也稱為Cross結合。

假設表A為2*3，表B為4*5，則交叉結合後的表為8*15的表格。

```sql
-- 兩個語法都可以
SELECT ... FROM 資料表A CROSS JOIN 資料表B
SELECT ... FROM 資料表A, 資料表B
```

### 自然結合

在兩個資料表進行交叉結合後，將其中一表內特定的欄位值與另一張表內特定的欄位值進行相等的判斷。自然結合可以分為「內部結合」與「外部結合」。

### **內部結合（Inner Join）**

```sql
-- 兩個語法都可以
SELECT ... FROM 資料表A, 資料表B WHERE 資料表A.欄位1 = 資料表B.欄位1;
SELECT ... FROM 資料表A INNER JOIN 資料表B ON 資料表A.欄位1 = 資料表B.欄位1;
```

<aside>
⚠️ 可以用 INNER JOIN 只能用 ON 進行篩選

</aside>

<aside>
⚠️ 由於輸出的資料欄位會出現重複，所以在SELECT的時候可以指定要哪一些欄位

</aside>

<aside>
⚠️ **內部結合**沒有限制資料表的數量，使用WHERE可以直接加FROM後面的資料表，但是用INNER JOIN則是需要再打一次

</aside>

```sql
-- 兩個語法都可以
SELECT ... FROM 資料表A, 資料表B, 資料表C 
WHERE 資料表A.欄位1 = 資料表B.欄位1 AND 資料表A.欄位1 = 資料表C.欄位1;

SELECT ... FROM 資料表A 
INNER JOIN 資料表B ON 資料表A.欄位1 = 資料表B.欄位1
INNER JOIN 資料表C ON 資料表B.欄位1 = 資料表C.欄位1;
```

**內部結合後指定搜尋條件**

```sql
-- 兩個語法都可以
SELECT ... FROM 資料表A, 資料表B, 資料表C 
WHERE 1=1
AND 資料表A.欄位1 = 資料表B.欄位1 
AND 資料表A.欄位1 = 資料表C.欄位1
AND 資料表A.欄位1 = 'Jack';

SELECT ... FROM 資料表A 
INNER JOIN 資料表B ON 資料表A.欄位1 = 資料表B.欄位1
INNER JOIN 資料表C ON 資料表B.欄位1 = 資料表C.欄位1
WHERE 資料表A.欄位1 = 10;
```

### 外部結合**（Outer Join）**

**左外部結合**

主資料表會被保留，而副資料表只有滿足組合條件時才會被保留。

```sql
SELECT ... FROM 主資料表 LEFT OUTER JOIN 副資料表 ON 結合條件式;
```

<aside>
⚠️ 如果主資料表沒有找到結合條件符合的副資料資訊，則會顯示NULL。

</aside>

**右外部結合**

主資料表會被保留，而副資料表只有滿足組合條件時才會被保留。

```sql
SELECT ... FROM 副資料表 RIGHT OUTER JOIN 主資料表 ON 結合條件式;
```

# 子查詢

### 子查詢基本操作

```sql
SELECT ... FROM <資料表> WHERE <欄位> <比較運算子> (SELECT ... FROM <資料表> WHERE <搜尋條件>);
```

<aside>
⚠️ 查詢中的查詢(子查詢)結果只能輸出單一欄位的一資料，如果超過一筆資料則會顯示錯誤。

</aside>

```sql
SELECT * FROM c_lcddps_act_input t where t.part_no = 
(SELECT PART_NO FROM c_lcddps_line_capa 
where part_no = '57.43T10.0E1'
and LINE_ID = 'ODF#1' 
and mainid = 2004);
```

### 子查詢判斷值是否存在

使用 EXISTS 判斷子查詢是否有回傳值。可以配合˙NOT取的反向邏輯。

```sql
SELECT * FROM 指定資料表 WHERE EXISTS (SELECT * FROM 指定資料表 WHERE 指定條件式)
```

```sql
SELECT * FROM 指定資料表 WHERE NOT EXISTS (SELECT * FROM 指定資料表 WHERE 指定條件式)
```

### 滿足任何子查詢條件的資料

當子查詢中回傳結果任一的值滿足主查詢的條件設為真實，使用ANY運算子。

```sql
WHERE (欄位或值) (比較運算子) ANY (子查詢)
```

<aside>
⚠️ 可以透過SOME及IN運算子來得到與ANY相同的結果。語法完全相同。
但是IN只能夠取出值相同的資料

</aside>

### 回傳所有滿足子查詢條件的資料

當子查詢中回傳結果任一的值皆要滿足所有條件為真時，使用 ALL 運算子。

```sql
WHERE (欄位或值) (比較運算子) ALL (子查詢)
```

# 操作資料

### 插入一筆資料

```sql
INSERT INTO 資料表 (欄位1名稱,欄位2名稱,...)
VALUES (欄位1數值,欄位2數值,...)
```

<aside>
⚠️ 欄位資料格式與數值必須要對應。

</aside>

也可以直接輸入欄位值，但依然要對應欄位名稱。

```sql
INSERT INTO 資料表 VALUES (欄位1數值,欄位2數值,...)
```

### 插入搜尋結果

```sql
INSERT INTO 資料表1 (欄位1名稱,欄位2名稱,...)
SELECT (欄位1名稱,欄位2名稱,...) FROM 資料表2
```

<aside>
⚠️ 可以插入NULL值，前提是表格設定該欄並非 NOT NULL

</aside>

### 更新資料

```sql
UPDATE 資料表 SET (欄位) = (指定值) WHERE (搜索條件)
```

UPDATE指令中，會將滿足WHERE 搜尋條件的列的值，更新為SET指令中指定的欄及其對應的值。

### 刪除列

使用 DELETE  刪除表資料

```sql
DELETE FROM (資料表) WHERE (搜索條件)
```

也可以使用 TRUNCATE TABLE，但不會進行記錄log等處理。

```sql
TRUNCATE (資料表) WHERE (搜索條件)
```

# 索引

由平均搜尋次數以及平均搜尋時間來看的話，索引的方式比起對所有資料由第一行開始進行比較搜尋的方式更有效率。

### 建立索引

```sql
CREATE INDEX (索引名稱) ON (資料表) (指定欄位)
```

### 刪除索引

```sql
DROP INDEX (索引名稱) ON (資料表)
```

# 觸發器

有時候會希望資料庫能夠主動或自動進行特定的動作。例如插入資料時，自動刪除他表中對應的列，並且判斷是否有重複。我們可以執行插入(INSERT)、更新(UPDATE)、刪除(DELETE)等對應資料庫上的資料更變處理來進行設定。

### 觸發器的缺點

使用太多觸發器會讓資料庫變得複雜，整體效能下降。

### 建立觸發器

```sql
CREATE TRIGGER (觸發器) (條件) ON (資料表)
(BEGIN) 觸發條件 (END);
```

當執行以下語法

```sql
CREATE TABLE account (acct_num INT, amount DECIMAL(10,2)); -- 創建資料表
```

```sql
-- 創建觸發器
CREATE TRIGGER ins_sum BEFORE INSERT ON account
FOR EACH ROW SET @suum = @sum + NEW.amount;
```

```sql
INSERT INTO account vaues (130,14.98), (140,1924.13);
```

```sql
-- 搜尋@sum變數中的值為剛新增amount欄值的總和。
SELECT @sum 'Total amount inserted'
```

### 刪除觸發器

```sql
DROP TRIGGER (觸發器)
```

---

# 資料定義語言(DDL)

## 新增資料欄位

```sql
ALTER TABLE <資料表> ADD [欄位] <欄位定義>
```

## 刪除資料欄位

```sql
ALTER TABLE <資料表> DROP [欄位]
```

## 更新資料欄位屬性

```sql
ALTER TABLE <資料表> MODIFY [欄位] <欄位定義>
```

## 資料表欄設定欄位預設值

```sql
ALTER TABLE <資料表> ALTER <欄位定義> SET DEFAULT <預設值>
```

## 資料表設定主鍵

```sql
ALTER TABLE <資料表> ADD [CONSTRAINT <限制名>]
PRIMARY KEY (<欄名1>[,<欄名2,...>])
```

## 資料表設定外部鍵

```sql
ALTER TABLE <資料表> ADD [CONSTRAINT <限制名>]
FOREIGN KEY (<欄名1>[,<欄名2,...>])
REFERENCES <外部參照表名> (<欄名1>[,<欄名2,...>])
```

## 資料表刪除設定主鍵

```sql
ALTER TABLE <資料表> DROP CONSTRAINT <限制名>
```

## 使用者設定

### 建立使用者

```sql
CREATE USER <使用者名稱> INDENTIFIED BY <密碼>
```

### 刪除使用者

```sql
DROP USER <使用者名稱>
```

## 視圖

### 建立視圖

```sql
CREATE VIEW <視圖名> [(<欄名1>[,欄名2]...)] AS <SELECT敘述>
```

### 刪除視圖

```sql
DROP VIEW <視圖名>
```

# 資料控制語言 DCL

## 設定使用者權限 - GRANT

```sql
GRANT <權限名1>[<權限名2>...] ON <表名>
TO <使用者名稱1> [IDENTIFIED BY '密碼']
		...<使用者名稱2> [IDENTIFIED BY '密碼']
WITH GRANT OPTION
```

<aside>
⚠️ 給予系統權限要用TO，而給予物件權限則是用ON

</aside>

<aside>
⚠️ 權限若是給 ALL PRIVILEGE的話就會授與所有權限。

</aside>

<aside>
⚠️ 使用者可以設定為 PUBLIC，則是對所有使用者設定權限。

</aside>

<aside>
⚠️ 如果指定 ALL GRANT OPTION ，被賦予權限的使用者也可以對其他使用者進行授權。

</aside>

<aside>
⚠️ 如果指定 HIERARCHY OPTION，則子物件同時進行相同權限的設定。

</aside>

## 刪除使用者權限 - REVOKE

```sql
REVOKE <權限名1>[<權限名2>...] ON <表名>
FROM <使用者名稱1> [IDENTIFIED BY '密碼']
		...<使用者名稱2> [IDENTIFIED BY '密碼']
```

<aside>
⚠️ 如果指定 CASCADE CONSTRAING，則會將REFERENCES設定的參考整合一併刪除。

</aside>

## 更改物件名稱 - RENAME

```sql
RENAME [TABLE] <表名> TO <新表名>
```

## 建立儲存點 - SAVEPOINT

設定一個名為sometime的儲存點。

```sql
SAVEPOINT sometime
```

如果透過UPDATE更了資料，但是仍然可以使用ROLLBACK來將資料回復到somtime這個儲存點的資料狀態，如此就可取消UPDATE這個動作。

## 回復資料 - ROLLBACK

```sql
ROLLBACK
```

## 鎖定資料表

```sql
LOCK TABLES <表名> <模式>
```

1. READ: 可讀，但無法INSERT與UPDATE。
2. READ LOCAL: 與READ很像，但不會鎖定非競爭資料的加入。
3. WRITE: 鎖定由其他SESSION對資料的讀取、加入、更新的動作。