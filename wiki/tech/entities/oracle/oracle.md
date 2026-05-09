---
type: entity
domain: tech
tags: [oracle, sql, database, csharp]
sources:
  - raw/tech/database/SQL 資料庫基本指令.md
  - raw/tech/database/Oracle CMD 指令筆記.md
  - raw/tech/database/Oracle To C#.md
created: 2026-05-03
updated: 2026-05-03
---

# Oracle

Oracle Database 是企業級關聯式資料庫。本頁涵蓋 SQL 基本指令、Oracle 特有語法、CMD 操作、以及從 C# 連接的方式。

## SQL 基本指令

### SELECT / WHERE

```sql
-- 基本查詢
SELECT Store_Name, Sales
FROM Store_Information
WHERE Sales > 1000
  OR (Sales < 500 AND Sales > 275);

-- DISTINCT 去重
SELECT DISTINCT Store_Name FROM Store_Information;

-- IN
SELECT * FROM Store_Information
WHERE Store_Name IN ('Los Angeles', 'San Diego');

-- BETWEEN
SELECT * FROM Store_Information
WHERE Txn_Date BETWEEN '06-Jan-1999' AND '10-Jan-1999';

-- LIKE + 萬用字元（% 多字元，_ 單字元）
SELECT * FROM Store_Information
WHERE Store_Name LIKE '%AN%';
```

### 排序與函數

```sql
-- ORDER BY（ASC 預設升冪，DESC 降冪）
SELECT Store_Name, Sales FROM Store_Information
ORDER BY Sales DESC;

-- 聚合函數
SELECT AVG(Sales) FROM Store_Information;   -- 平均
SELECT COUNT(*) FROM Store_Information;     -- 計數
SELECT MAX(Sales), MIN(Sales) FROM Store_Information;
SELECT SUM(Sales) FROM Store_Information;

-- GROUP BY（非函數欄位都要放 GROUP BY）
SELECT Store_Name, SUM(Sales)
FROM Store_Information
GROUP BY Store_Name;

-- HAVING（對函數結果設條件）
SELECT Store_Name, SUM(Sales)
FROM Store_Information
GROUP BY Store_Name
HAVING SUM(Sales) > 1500;
```

### 別名 / JOIN

```sql
-- 欄位別名
SELECT A1.Store_Name AS Store, SUM(A1.Sales) AS "Total Sales"
FROM Store_Information A1
GROUP BY A1.Store_Name;

-- INNER JOIN（兩表都有才顯示）
SELECT A1.Region_Name, SUM(A2.Sales)
FROM Geography A1, Store_Information A2
WHERE A1.Store_Name = A2.Store_Name
GROUP BY A1.Region_Name;

-- Oracle OUTER JOIN（(+) 符號）
SELECT A1.Store_Name, SUM(A2.Sales)
FROM Geography A1, Store_Information A2
WHERE A1.Store_Name = A2.Store_Name (+)
GROUP BY A1.Store_Name;
```

### 字串函數

```sql
-- Oracle 字串連接（|| 符號，或 CONCAT）
SELECT Region_Name || ' ' || Store_Name FROM Geography
WHERE Store_Name = 'Boston';

-- REPLACE
SELECT REPLACE(Region_Name, 'ast', 'astern') FROM Geography;
```

## Oracle 資料庫狀態

Oracle 資料庫有四個狀態：

| 狀態 | 說明 |
| --- | --- |
| **shutdown** | 完全關閉 |
| **nomount** | 讀取參數檔，配置 SGA，啟動背景程序 |
| **mount** | 開啟 control file，讀取 data file / redo log 狀態 |
| **open** | 使用者可連線，開啟 data file 與 redo log |

## Oracle CMD 指令

### 登入

```bash
# 格式：sqlplus account/password@host/dbSID
sqlplus sys/password@192.168.1.100/xe as sysdba

# 啟動資料庫
cmd > sqlplus /nolog
sql > connect / as sysdba
sql > startup
```

### 監聽器

```bash
lsnrctl status   # 查看狀態
lsnrctl start    # 啟動
lsnrctl stop     # 停止
```

### 使用者管理

```sql
-- 建立使用者
ALTER SESSION SET "_ORACLE_SCRIPT"=true;
CREATE USER myuser IDENTIFIED BY mypassword;

-- 解鎖帳號並設密碼
ALTER USER myuser IDENTIFIED BY mypassword ACCOUNT UNLOCK;

-- 授權
GRANT CONNECT, RESOURCE TO myuser;
```

### 常用查詢

```sql
-- 顯示 SGA 記憶體配置
SHOW PARAMETER sga;

-- 查詢資料表
SELECT * FROM user_tables;
SELECT * FROM all_tables WHERE owner = 'MYUSER';
```

## Oracle To C#

使用 **Oracle.ManagedDataAccess.Core** NuGet 套件連接（ODAC）。

### 連線設定

```csharp
// appsettings.json
{
  "ConnectionStrings": {
    "Oracle": "Data Source=192.168.1.100/xe;User Id=myuser;Password=mypassword;"
  }
}

// EF Core 設定
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseOracle(builder.Configuration.GetConnectionString("Oracle")));
```

### 基本 CRUD（EF Core）

```csharp
public class AppDbContext : DbContext
{
    public DbSet<User> Users { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>()
            .ToTable("USERS")          // Oracle 表名預設大寫
            .HasKey(u => u.Id);
    }
}

// 查詢
var users = await _db.Users.Where(u => u.IsActive).ToListAsync();

// 新增
_db.Users.Add(new User { Name = "Alice" });
await _db.SaveChangesAsync();
```

### ADO.NET 直接查詢

```csharp
using Oracle.ManagedDataAccess.Client;

await using var conn = new OracleConnection(connectionString);
await conn.OpenAsync();

await using var cmd = conn.CreateCommand();
cmd.CommandText = "SELECT * FROM USERS WHERE ID = :id";
cmd.Parameters.Add(":id", userId);

await using var reader = await cmd.ExecuteReaderAsync();
while (await reader.ReadAsync())
{
    Console.WriteLine(reader["NAME"].ToString());
}
```

## 連結

- [[csharp]] — C# 連接 Oracle 資料庫
- [[dotnet-web-api]] — Web API 中使用 Oracle 資料層
