# Chapter 7：EF Core 與資料存取設計

## 7.1 為什麼選擇 EF Core

### EF Core 的角色

- EF Core 是 **ORM（Object–Relational Mapper）**
- 負責在：
    - C# 物件
    - 關聯式資料庫
        
        之間做轉換
        

### 使用 EF Core 的價值

- 避免大量手寫 SQL
- 型別安全
- 與 LINQ 整合
- 與 ASP.NET Core DI 深度整合

**定位**

- EF Core 是資料存取工具
- 不是商業邏輯層

---

## 7.2 DbContext 的設計角色

### DbContext 的責任

- 資料庫連線管理
- Entity 追蹤（Change Tracking）
- Transaction 管理
- SQL 生成與執行

### DbContext 的生命週期

- **必須是 Scoped**
- 一個 HTTP Request 對應一個 DbContext

---

## 7.3 Entity 的設計原則

### Entity 是什麼

- 對應資料表的模型
- 代表資料庫狀態

### 範例 Entity

```csharp
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = null!;
    public string Email { get; set; } = null!;
}
```

### 設計原則

- Entity 不包含 API 驗證邏輯
- Entity 不直接暴露給 Client
- Entity 是資料層模型，不是 DTO

---

## 7.4 建立 DbContext

### DbContext 定義

```csharp
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();
}
```

### 設計說明

- `DbSet<T>` 對應資料表
- DbContext 不處理業務邏輯

---

## 7.5 在 Program.cs 註冊 DbContext

### 設定 Connection String（appsettings.json）

```json
{
  "ConnectionStrings": {
    "Default": "Server=localhost;Database=DemoDb;Trusted_Connection=True;"
  }
}
```

### 註冊 DbContext

```csharp
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(
        builder.Configuration.GetConnectionString("Default")));
```

**重點**

- DbContext 預設為 Scoped
- 不要手動改成 Singleton

---

## 7.6 Migration 與資料庫版本控管

### Migration 的用途

- 控制資料庫 Schema 變更
- 可追蹤歷史版本
- 可安全部署至不同環境

### 基本流程

1. 修改 Entity
2. 建立 Migration
3. 更新資料庫

### 指令範例

```bash
dotnet ef migrations add InitialCreate
dotnet ef database update
```

---

## 7.7 API 與 EF Core 的標準互動流程

### 正確分層流程

```
Controller
   ↓
Service
   ↓
DbContext
   ↓
Database
```

### Service 中使用 DbContext

```csharp
public class UserService : IUserService
{
    private readonly AppDbContext _db;

    public UserService(AppDbContext db)
    {
        _db = db;
    }

    public UserResponse GetUser(int id)
    {
        var user = _db.Users.Find(id);
        if (user == null)
            throw new Exception("User not found");

        return new UserResponse
        {
            Id = user.Id,
            Name = user.Name
        };
    }
}
```

---

## 7.8 非同步（Async）資料存取

### 為什麼一定要用 Async

- Web API 是 I/O 密集應用
- 阻塞 Thread 會降低吞吐量

### 正確寫法

```csharp
var user = await _db.Users.FindAsync(id);
```

```csharp
await _db.SaveChangesAsync();
```

**原則**

- 只要有 I/O，一律 Async
- Controller、Service 一路 Async 到底

---

## 7.9 Transaction 與一致性

### EF Core 預設行為

- `SaveChanges()` 本身具 Transaction
- 多次 SaveChanges 才需要顯式 Transaction

### 顯式 Transaction 範例

```csharp
using var tx = await _db.Database.BeginTransactionAsync();
// operations
await _db.SaveChangesAsync();
await tx.CommitAsync();
```

---

## 7.10 常見錯誤與踩雷點

### 錯誤 1：在 Controller 直接使用 DbContext

- 破壞分層
- 難以測試

### 錯誤 2：DbContext 設為 Singleton

- Thread Safety 問題
- 資料錯亂

### 錯誤 3：同步呼叫資料庫

- 效能嚴重下降

---

## Chapter 7 設計準則（定稿）

- DbContext 必須是 Scoped
- Entity 不直接對外
- 所有資料存取經由 Service
- I/O 操作全面使用 Async
- Migration 是必備工具，不是可選項

---

## Chapter 7 小結

- EF Core 是資料存取層，不是商業邏輯層
- 正確分層能大幅降低未來維護成本
- Async 與生命週期是穩定系統的關鍵