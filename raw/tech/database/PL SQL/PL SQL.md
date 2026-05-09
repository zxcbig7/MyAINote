---
tags: [database, oracle, plsql, sql]
---

> 關聯：[[oracle]]

# PL SQL

# **一、PL/SQL簡介**

## **1. PL/SQL簡介**

1. PL/SQl是過程語言PL與結構化語言SQL結合而成的程式語言
2. PL/SQL引擎駐留在Oracle伺服器中
3. 該引擎接收PL/SQL塊並對其進行編譯

## **2. PL/SQL要點**

PL/SQL是一種強型別的程式語言,所有的變數都要求在declare部分進行宣告,

對於變數名稱有如下規定:

1. 變數名可以是字母數位下劃線$#等組成
2. 所有的變數名稱要求以字母開頭,不能是Oracle中的關鍵字
3. 變數的長度最多隻能為30個字元
4. 為了提高PL/SQL的可讀性,所有變數採用"v_變數名"進行定義

## **3.PL/SQL 塊**

PL/SQL 塊是構成PL/SQL的基本組成單元,將邏輯上相關的宣告和語句組合在一起
PL/SQL分為三個部分「宣告部分,可執行部分,和例外處理部分」。

# **二、 PL/SQL 語法和格式:**

## **1.語法格式:**

```sql
declare 
       宣告部分
begin
       可執行部分      
 exception
       例外處理部分   
 end;
```

## **2.宣告變數**

> 變數名 資料型別
> 

## **3.宣告變數時賦值**

> 變數名 資料型別 := 值 ;
> 
- 注意這裡的「:」不可省略

## **4.PL/SQL中的輸出函數**

> dbms_output.put_line(要輸出的值或者字串)
> 
- 字串使用””包裹

## **5.PL/SQL格式舉例**

```sql
declare
   v_name varchar2(20) :='我是誰?';
begin
 -- 輸出操作
	 dbms_output.put_line('pl/sql的輸出操作' || v_name); -- PL/SQL 中字串使用||連線
end;
```

- 測試發現中文輸出會導致亂碼

## 6. **結合SQL語句使用into為變數賦值**

```sql
declare
   v_name varchar2(20);
begin
  -- 通過SQL語句和into關鍵字為變數賦值
   select uname into v_name from user_book where userid = 9999;
   dbms_output.put_line(v_name); -- 列印
end;
```

# **三、兩個特殊的欄位型別**

## **1. %type指定的欄位的型別**

> **變數名 表名.屬性名%type;**
> 

```sql
declare 
   v_name user_book.uname%type;
   v_id user_book.userid%type;
   begin
     -- 為欄位賦值
         select user_book.uname,user_book.userid into v_name,v_id 
                from user_book 
                where user_book.userid=9999;
  -- 輸出看結果
  dbms_output.put_line(v_id || v_name);
end;
```

## **2. %rowtype 代表表中的整行的資料**

> **變數名 表名.屬性名%rowtype;**
> 

```sql
declare 
   v_row user_book%rowtype;
begin
  -- 賦值
  select * into v_row from user_book  where user_book.userid=9999; 
  -- 輸出行中的資料: 注意此時必須手動將行內的所有欄位寫入輸出語句,否則會報錯
  dbms_output.put_line(v_row.uname||v_row.userid||v_row.urole );
end;
```

# 四、常用的判斷語句

## **1.if else條件判斷語句**

```sql
if  條件1
		then 滿足條件1時執行的語句
else 條件2
    then 滿足條件2時執行的語句
```

## **2.case when 語句**

```sql
case 
	when 條件1
		then 滿足條件1時執行的程式碼
	when 條件2
		then 滿足條件2時執行的程式碼
	when 條件3
		then 滿足條件3時執行的程式碼
	else 以上條件都不滿足時執行的程式碼
end case;
```

# 五、**常用的迴圈語句**

## **1. exit when 退出迴圈:**

```
  loop
    迴圈執行的語句塊;
    exit when迴圈結束條件;
         步進語句;
  end loop;
```

```sql
declare
      v_i int := 0; -- 宣告變數
begin
  loop
    dbms_output.put_line(v_i); -- 迴圈塊: 列印v_i
    exit when v_i >= 10; -- 結束條件
    v_i := v_i+1; -- 步進語句
  end loop;
end;
```

## 2. **while迴圈:**

```sql
while 迴圈結束條件
loop
迴圈體;
步進語句;
end loop;
```

```sql
declare
      v_i int := 0; -- 宣告變數
begin
  while v_i <= 10 loop -- 結束條件
	    dbms_output.put_line(v_i); -- 迴圈塊: 列印v_i
	    v_i := v_i+1; -- 步進語句
	  end loop;
end;
```

## **3.for in 迴圈:**

```sql
for 迴圈索引變數 in [recerse] 迴圈區域下限..迴圈區域上線 
loop
迴圈語句塊;
end loop ;

```

– reverse: 反向 可打可不打

例如: 倒序列印1到10(即10到1)

```sql
declare 
begin
  for i in reverse 1..10  -- 從1到10 正序
    loop
    dbms_output.put_line(i); -- 列印i
    end loop;
end;
```

# 六、異常

## **1. 什麼是異常?**

> 在執行異常時出現的錯誤叫做異常
> 

發生異常後,語句將停止執行,控制權轉移到PL/SQL塊的例外處理部分

## **2. 異常的三種型別:**

1. 預定義異常:當PL/SQL程式違反Oracle規則或超越系統限制時隱式引發; 
    1. 使用者不需要在程式中定義;
2. 非預定義異常:當PL/SQL程式違反Oracle規則或超越系統限制時引發;
    1. 使用者需要在程式中定義;
3. 使用者定義異常:需要使用者在程式中定義,顯式的在程式中引發;

## **3.例外處理程式的語法:**

```sql
   begin
     常規程式碼塊;
   exception
     when 異常條件1滿足 then 異常條件1滿足時執行的程式碼
       when 異常條件2滿足 then 異常條件2滿足時執行的程式碼
          when others then 都不滿足時執行的程式碼
   end;
```

## **4.常見的預定義異常:**

```
    -- 資料過多: too_many_rows
    --  查詢的資料不存在: no_data_found
```

例如:

```sql
declare
   v_error exception;
   v_name user_book.uname%type;
 begin
   select uname into v_name from user_book where user_book.userid=100000; -- 此時的userid是不存在的
 end;
```

![Untitled](raw/tech/database/PL%20SQL/Untitled.png))

## **5.使用者自定義異常**

```sql
  declare
   v_error exception;
   v_name user_book.uname%type;
 begin
   select uname into v_name from user_book where user_book.userid=1001;
    if v_name = '張三' then  -- 如果滿足條件則返回v_error
      raise v_error;
      end if;
          exception
            when v_error then  -- 當出現此異常的時候觸發
             dbms_output.put_line('原來是張三啊,拋個異常給你吧');
 end;
```

![Untitled](raw/tech/database/PL%20SQL/Untitled%201.png))