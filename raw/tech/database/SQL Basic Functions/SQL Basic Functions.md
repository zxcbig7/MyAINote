---
tags: [database, sql]
---

> 關聯：[[oracle]]

# SQL Basic Functions

### **一般常用字元的functons**

1. LOWER 將字串轉換小寫
    
    ```sql
    LOWER(user_name)
    ```
    
2. UPPER：將字串轉換大寫
    
    ```sql
    UPPER(user_name)
    ```
    
3. NITCAP：將字串第一個字轉成大寫，其他轉換成小寫
    
    ```sql
    INITCAP(user_name)
    ```
    
4. CONCAT：連接兩個字串，與(||)用法相同
    
    ```sql
    CONCAT('Hello','World') --回傳'HelloWorld '
    ```
    
5. SUBSTR：切割字串
    
    ```sql
    SUBSTR('HellowWorld',1,5) --回傳'Hello'
    ```
    
6. LENGTH：
    
    ```sql
    LENGTH('HellowWorld')--回傳10
    ```
    
7. INSTR:
    
    ```sql
    INSTR('HellowWorld','W')--回傳6
    ```
    
8. LPAD：
    
    ```sql
    LPAD(salary,'5','@') --回傳@@@@@36000
    ```
    
9. RPAD：
    
    ```sql
    RPAD(salary,'5','@')--回傳36000@@@@@
    ```
    
10. TRIM：
    
    ```sql
    TRIM('H' FROM 'HelloWorld')--回傳elloWorld
    ```
    
11. REPLACE：
    
    ```sql
    REPLACE('HELLO','HELLO','World')--回傳World
    ```
    

### **數值的 Functons**

1. ROUND 四捨五入
    
    ```sql
    ROUND(45.926, 2) --回傳45.93
    ```
    
2. TRUNC 無條件捨去
    
    ```sql
    TRUNC(45.926, 2) --回傳45.92
    
    ```
    
3. MOD 餘數
    
    ```sql
    MOD(1600,300) --回傳100
    ```
    

<aside>
⚠️ 在oracle中，若要使用SELECT測試語法又沒有資料表，可以使用DUAL來下SQL語法，而不用另外在新增資料表。

```sql
select ROUND(45.923,2) from dual  -- 回傳資料表結果。
```

</aside>

### 其他常用語法

1. IS NULL ：配合 where 用來找哪個欄位是NULL，進行資料操作。
2. INSERT 與SELECT的綜合運用，用於調整、新增大量或特定資料。

```sql
INSERT INTO [dbo].[Tcode01]

 ([SEQ],[單位代號],[單位名稱],[主管],[電話])

SELECT [SEQ],[單位代號],[單位名稱],[主管],[電話]

  FROM [dbo].[Tcode01] WHERE 單位代號 = "11"
```

### **常用single row function**

1. NVL：如果expr1為null，則回傳expr2
    
    ```sql
    NVL(expr1,expr2)
    ```
    
2. NVL2：如果expr1不為null，則回傳expr2；若expr1為，則回傳expr3。
    
    ```sql
    NVL2(expr1,expr2,expr3)
    ```
    
3. NULLIF：expr1與expr2比較，若相同回傳NULL，否則回傳expr1
    
    ```sql
    NULLIF(expr1,expr2)
    ```
    
4. COALESCE：回傳非null的expr
    
    ```sql
    COALESCE(expr1,expr2,...exprn)
    ```
    

### **條件式 Single Row Function：**

1. CASE: 若expr符合comparison_expr1 則回傳return_expr1, 依此類推..
    
    ```sql
    CASE expr WHEN comparison_expr1 THEN return_expr1
    
    [WHEN comparison_expr2 THEN return_expr2
    
    WHEN comparison_exprn THEN return_exprn
    
    ELSE else_expr]
    ```
    
2. DECODE：與CASE類似，但可以將欄位作為比較條件，回傳符合查詢條件的結果。
    
    ```sql
    DECODE( col|expression, search1, result1
    
    [,search2, result2, ...,]
    
    [, default] )
    ```
    

### **巢狀使用 Single Row Function：**

```sql
select last_name, UPPER(CONCAT(SUBSTR(LAST_NAME,1,8),_US))

from employee

where department_id = 60
```

### **Group function**

1. AVG: 平均值
2. COUNT：計數
3. MAX：最大值
4. MIN：最小值
5. SUM：總和

```scss
select count(*) from table

select AVG(salary) , MAX(salary), MIN(salary) ,SUM(salary)

FROM employee
```