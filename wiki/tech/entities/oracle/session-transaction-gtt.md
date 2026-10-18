---
type: note
domain: tech
tags: [oracle, sql, database, transaction, session, temporary-table]
created: 2026-08-13
updated: 2026-08-13
---

# Oracle：Session、Transaction 與 Global Temporary Table

## 核心概念

```text
連線成功 → Session 開始 → 執行多個 Transaction → 中斷連線 → Session 結束
```

- **Session（連線工作階段）**：應用程式連上 Oracle 到連線中斷之間的狀態。
- **Transaction（交易）**：一組必須一起成功或一起失敗的資料異動（`INSERT`、`UPDATE`、`DELETE`）。

一個 Session 可執行多個 Transaction。`COMMIT` 或 `ROLLBACK` 只會結束目前的 Transaction，不會結束 Session。

```text
同一個 Session
├─ Transaction A：INSERT → COMMIT
├─ Transaction B：UPDATE → ROLLBACK
└─ Transaction C：DELETE → COMMIT
```

## Session

Session 保有該連線專屬的狀態，例如：登入使用者、`ALTER SESSION` 設定、游標，以及暫存表資料。

```sql
ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD';
```

這個設定只影響目前的 Session，不會影響其他使用者的連線。

## Transaction

Transaction 用來保證多個異動的原子性：要嘛都成功，要嘛都取消。

```sql
UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

COMMIT; -- 兩個異動一起正式生效
```

- `COMMIT`：確認目前 Transaction 的變更；確認後不能再用 `ROLLBACK` 還原。
- `ROLLBACK`：取消目前 Transaction 中尚未提交的變更。
- Oracle 的 DDL，例如 `CREATE TABLE`、`ALTER TABLE`、`DROP TABLE`，通常會隱含提交；不要把它們混在需要回滾的業務 Transaction 中。

## Global Temporary Table（GTT）

GTT 的**表結構**會永久保留在資料庫；表內的**資料**則是暫時的，且每個 Session 各自獨立。

```sql
CREATE GLOBAL TEMPORARY TABLE temp_order_ids (
    order_id NUMBER PRIMARY KEY
)
ON COMMIT DELETE ROWS;
```

`GLOBAL` 指的是表定義建立一次後可供有權限的使用者使用，**不是所有 Session 共用同一批暫存資料**。

```text
同一張 GTT 定義
├─ Session A：只能看見 A 插入的資料
└─ Session B：只能看見 B 插入的資料
```

## GTT：ON COMMIT 資料生命週期

| 設定 | 資料清除時機 | 適用情境 |
| --- | --- | --- |
| `ON COMMIT DELETE ROWS` | 每次 Transaction `COMMIT` 後 | 單次交易中的計算或匯入中繼資料 |
| `ON COMMIT PRESERVE ROWS` | Session 結束（連線中斷）後 | 同一條連線跨多個 Transaction 的暫存工作資料 |

### ON COMMIT DELETE ROWS

```sql
CREATE GLOBAL TEMPORARY TABLE temp_calc (
    id NUMBER
) ON COMMIT DELETE ROWS;

INSERT INTO temp_calc VALUES (1);
COMMIT;

SELECT * FROM temp_calc; -- 查不到資料：已在 COMMIT 時清除
```

記憶方式：資料跟著 **Transaction** 走。

### ON COMMIT PRESERVE ROWS

```sql
CREATE GLOBAL TEMPORARY TABLE temp_selected_users (
    user_id NUMBER
) ON COMMIT PRESERVE ROWS;

INSERT INTO temp_selected_users VALUES (101);
COMMIT;

SELECT * FROM temp_selected_users; -- 仍可看見 101
```

記憶方式：資料跟著 **Session** 走。

`PRESERVE` 不表示永久保存，也不表示其他 Session 看得到資料；Session 中斷後資料仍會清除。

## Connection Pool 注意事項

在 Web API 或應用程式使用 connection pool 時，程式歸還連線不一定會讓 Oracle Session 中斷；該 Session 可能被下一個請求重複使用。

因此 `ON COMMIT PRESERVE ROWS` 要謹慎使用：使用完成後明確清除暫存資料，或優先選擇 `ON COMMIT DELETE ROWS`。

