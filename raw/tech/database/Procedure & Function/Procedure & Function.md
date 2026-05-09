# Procedure & Function

# WITH

> 把一段 SELECT 結果暫時命名成一張表，供後面的 SQL 使用。
> 

```sql
WITH
sales30 AS (
    SELECT * FROM sales WHERE sale_date >= SYSDATE - 30
),
top_emp AS (
    SELECT emp_id, SUM(amount) amt
    FROM sales30
    GROUP BY emp_id
)
SELECT *
FROM top_emp
WHERE amt > 50000;
```

# Procedure 語法架構

```sql
CREATE OR REPLACE PROCEDURE 程序名稱 (參數) 
IS
    宣告區
BEGIN
    執行主體區
END
```

```sql
CREATE OR REPLACE PROCEDURE MY_TEST_SP (
    STORE_CODE     IN     VARCHAR2,   -- 輸入參數：傳入店代號
    TOTAL_AMOUNT   OUT    NUMBER,     -- 輸出參數：回傳總金額
    STATUS_MSG     IN OUT VARCHAR2    -- 進出參數：可用來回傳訊息
)
IS
    ---------------------------------------------------------------------
    -- 區域變數宣告
    ---------------------------------------------------------------------
    sellDate        DATE;              -- 日期型態
    strTodayDate    VARCHAR2(8);       -- 存放今天日期（字串）
    dataType        VARCHAR2(2) := '15';  -- 預設類別
    maxAmount       NUMBER(5);         -- 最大金額
    v_count         PLS_INTEGER := 0;  -- 計數器
    flag_done       BOOLEAN := FALSE;  -- 布林變數示意

    ---------------------------------------------------------------------
    -- Cursor 宣告（查詢用）
    ---------------------------------------------------------------------
    CURSOR cur_store IS                -- 不帶參數的 Cursor
        SELECT store_id, store_name FROM stores;

    CURSOR cur_sales(p_store VARCHAR2) IS  -- 帶參數的 Cursor
        SELECT amount FROM sales WHERE store_id = p_store;

    ---------------------------------------------------------------------
    -- Record 型別示範
    ---------------------------------------------------------------------
    TYPE rec_sales IS RECORD (
        amount NUMBER,
        sale_date DATE
    );
    v_rec rec_sales;   -- Record 變數，用來存放 FETCH 結果
    
    ---------------------------------------------------------------------
    -- 自訂例外
    ---------------------------------------------------------------------
    ex_no_data_found EXCEPTION;
    
BEGIN
    ---------------------------------------------------------------------
    -- IF / ELSIF / ELSE 判斷式示範
    ---------------------------------------------------------------------
    IF STORE_CODE IS NULL THEN
        STATUS_MSG := 'Store code cannot be null.';
        RAISE_APPLICATION_ERROR(-20001, 'STORE_CODE is required');  -- 丟錯誤
    ELSEIF STORE_CODE = 'A001' THEN
        SELECT TO_CHAR(SYSDATE, 'YYYYMMDD') INTO strTodayDate FROM dual;
    ELSE
        strTodayDate := '00000000';  -- 其他情況預設值
    END IF;

    ---------------------------------------------------------------------
    -- CASE 判斷（適合多選一）
    ---------------------------------------------------------------------
    CASE dataType
        WHEN '15' THEN maxAmount := 150;
        WHEN '20' THEN maxAmount := 200;
        ELSE maxAmount := 0;
    END CASE;

    ---------------------------------------------------------------------
    -- FOR LOOP：固定次數迴圈
    ---------------------------------------------------------------------
    FOR i IN 1..10 LOOP
        v_count := v_count + i;
    END LOOP;

    ---------------------------------------------------------------------
    -- WHILE LOOP：條件成立則持續執行
    ---------------------------------------------------------------------
    WHILE v_count < 100 LOOP
        v_count := v_count + 5;

        IF v_count > 80 THEN
            EXIT;  -- 提前跳出迴圈
        END IF;
    END LOOP;

    ---------------------------------------------------------------------
    -- 使用 Cursor FOR LOOP（自動 Open/Fetch/Close）
    ---------------------------------------------------------------------
    FOR rec IN cur_store LOOP
        DBMS_OUTPUT.PUT_LINE('STORE: ' || rec.store_name);
    END LOOP;

    ---------------------------------------------------------------------
    -- 顯式 Cursor 操作：Open / Fetch / Close（較低階）
    ---------------------------------------------------------------------
    OPEN cur_sales(STORE_CODE);
    LOOP
        FETCH cur_sales INTO v_rec.amount;   -- 只取 amount 欄位
        EXIT WHEN cur_sales%NOTFOUND;        -- 若查無資料則結束
        TOTAL_AMOUNT := NVL(TOTAL_AMOUNT, 0) + v_rec.amount;
    END LOOP;
    CLOSE cur_sales;

    ---------------------------------------------------------------------
    -- 隱含變數 SQL%FOUND / SQL%ROWCOUNT 示範
    ---------------------------------------------------------------------
    UPDATE sales SET amount = amount + 10 WHERE store_id = STORE_CODE;

    IF SQL%FOUND THEN
        STATUS_MSG := 'Rows updated: ' || SQL%ROWCOUNT;
    ELSE
        STATUS_MSG := 'No rows updated';
    END IF;

    ---------------------------------------------------------------------
    -- 動態 SQL（常用於動態指定條件、表名等）
    ---------------------------------------------------------------------
    EXECUTE IMMEDIATE 'UPDATE sales SET amount = 0 WHERE store_id = :1'
        USING STORE_CODE;

    ---------------------------------------------------------------------
    -- SAVEPOINT / ROLLBACK / COMMIT 交易控制示範
    ---------------------------------------------------------------------
    SAVEPOINT sp_before_insert;   -- 設定一個回滾點

    INSERT INTO sales_log VALUES (STORE_CODE, SYSDATE);

    ROLLBACK TO sp_before_insert; -- 回到插入前狀態

    COMMIT;  -- 提交所有已成功的變更

EXCEPTION
    ---------------------------------------------------------------------
    -- 例外處理區：捕捉可能發生的錯誤
    ---------------------------------------------------------------------

    WHEN NO_DATA_FOUND THEN
        STATUS_MSG := 'No data found.';  -- 查不到資料

    WHEN TOO_MANY_ROWS THEN
        STATUS_MSG := 'Query returned more than one row.'; -- 期望一筆卻查到多筆

    WHEN ex_no_data_found THEN
        STATUS_MSG := 'Custom exception happened.';  -- 自訂例外

    WHEN OTHERS THEN
        STATUS_MSG := 'Unexpected error: ' || SQLERRM; -- 其他未預期錯誤
        ROLLBACK;
END MY_TEST_SP;
/

```

```sql
DECLARE
    CODE VARCHAR(5) := ‘252’;
    MONEY NUMBER;
BEGIN
    MY_TEST_SP(CODE, MONEY);
    DBMS_OUTPUT.PUT_LINE(MONEY);
END;
```

# Function

```sql
CREATE OR REPLACE FUNCTION demo_full_function (
    p_store IN VARCHAR2
)
RETURN NUMBER
IS
    ---------------------------------------------------------------------
    -- 區域變數與型別
    ---------------------------------------------------------------------
    v_today       VARCHAR2(8);
    v_result      NUMBER := 0;
    v_count       PLS_INTEGER := 0;

    TYPE rec_sales IS RECORD (
        amount NUMBER,
        sale_date DATE
    );
    v_rec rec_sales;

    TYPE t_numtab IS TABLE OF NUMBER;
    v_list t_numtab;

    ---------------------------------------------------------------------
    -- Cursor 宣告
    ---------------------------------------------------------------------
    CURSOR cur_sales IS
        SELECT amount FROM sales;

    CURSOR cur_sales_by_store(p VARCHAR2) IS
        SELECT amount FROM sales WHERE store_code = p;

    ---------------------------------------------------------------------
    -- 自訂例外
    ---------------------------------------------------------------------
    ex_zero_amount EXCEPTION;

BEGIN
    ---------------------------------------------------------------------
    -- IF / ELSIF / ELSE
    ---------------------------------------------------------------------
    IF p_store IS NULL THEN
        RETURN -1;
    ELSIF p_store = 'A001' THEN
        SELECT TO_CHAR(SYSDATE,'YYYYMMDD') INTO v_today FROM dual;
    ELSE
        v_today := '00000000';
    END IF;

    ---------------------------------------------------------------------
    -- CASE
    ---------------------------------------------------------------------
    CASE p_store
        WHEN 'A001' THEN v_count := 10;
        WHEN 'B002' THEN v_count := 20;
        ELSE v_count := 0;
    END CASE;

    ---------------------------------------------------------------------
    -- FOR LOOP
    ---------------------------------------------------------------------
    FOR i IN 1..v_count LOOP
        v_result := v_result + i;
    END LOOP;

    ---------------------------------------------------------------------
    -- WHILE LOOP
    ---------------------------------------------------------------------
    WHILE v_result < 100 LOOP
        v_result := v_result + 3;
        EXIT WHEN v_result > 80;
    END LOOP;

    ---------------------------------------------------------------------
    -- Cursor FOR LOOP
    ---------------------------------------------------------------------
    FOR rec IN cur_sales LOOP
        v_result := v_result + rec.amount;
    END LOOP;

    ---------------------------------------------------------------------
    -- 顯式 Cursor（帶參數）
    ---------------------------------------------------------------------
    OPEN cur_sales_by_store(p_store);
    LOOP
        FETCH cur_sales_by_store INTO v_rec.amount;
        EXIT WHEN cur_sales_by_store%NOTFOUND;

        IF v_rec.amount = 0 THEN
            RAISE ex_zero_amount;
        END IF;

        v_result := v_result + v_rec.amount;
    END LOOP;
    CLOSE cur_sales_by_store;

    ---------------------------------------------------------------------
    -- Bulk Collect
    ---------------------------------------------------------------------
    SELECT amount BULK COLLECT INTO v_list
    FROM sales
    WHERE store_code = p_store;

    FOR i IN 1..v_list.COUNT LOOP
        v_result := v_result + v_list(i);
    END LOOP;

    ---------------------------------------------------------------------
    -- 自訂例外
    ---------------------------------------------------------------------
    IF v_result IS NULL THEN
        RAISE ex_zero_amount;
    END IF;

    ---------------------------------------------------------------------
    -- 必須 RETURN
    ---------------------------------------------------------------------
    RETURN v_result;

EXCEPTION
    WHEN ex_zero_amount THEN
        RETURN -999;

    WHEN OTHERS THEN
        RETURN -1;
END demo_full_function;
/

```

## ❗ 不能放進 FUNCTION 的東西是：

❌ COMMIT、ROLLBACK

❌ INSERT / UPDATE / DELETE（可，但強烈不建議）

❌ OUT 參數

❌ Autonomous Transaction

❌ DBMS_OUTPUT（在 SQL 裡不會動）

# View

```sql
-------------------------------------------------------------------------------
-- 基本 VIEW
-------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_basic AS
SELECT emp_id, emp_name, salary
FROM employees;

-------------------------------------------------------------------------------
-- 指定欄位名稱
-------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_alias (id, name, pay) AS
SELECT emp_id, emp_name, salary
FROM employees;

-------------------------------------------------------------------------------
-- JOIN View
-------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_emp_dept AS
SELECT e.emp_id, e.emp_name, d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id;

-------------------------------------------------------------------------------
-- GROUP BY View（不可更新）
-------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_dept_agg AS
SELECT dept_id, COUNT(*) AS emp_cnt
FROM employees
GROUP BY dept_id;

-------------------------------------------------------------------------------
-- FORCE View
-------------------------------------------------------------------------------
CREATE OR REPLACE FORCE VIEW v_force AS
SELECT * FROM table_not_exist;

-------------------------------------------------------------------------------
-- WITH CHECK OPTION
-------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_sales_emp AS
SELECT *
FROM employees
WHERE dept_id = 10
WITH CHECK OPTION;

-------------------------------------------------------------------------------
-- WITH READ ONLY
-------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_readonly AS
SELECT * FROM employees
WITH READ ONLY;

-------------------------------------------------------------------------------
-- Materialized View
-------------------------------------------------------------------------------
CREATE MATERIALIZED VIEW mv_emp
BUILD IMMEDIATE
REFRESH FAST ON COMMIT
AS
SELECT emp_id, salary
FROM employees;
```