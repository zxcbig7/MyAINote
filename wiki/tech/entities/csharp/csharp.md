---
type: entity
domain: tech
tags: [csharp, dotnet, backend, oop, linq]
sources:
  - raw/tech/languages/C#.md
created: 2026-05-03
updated: 2026-10-18
---

# C#

C# 是微軟的靜態型別、物件導向語言，用於 ASP.NET Core 後端開發。

## 基礎語法重點

### 型別與變數

```csharp
// 基本型別
int count = 0;
string name = "Alice";
bool isActive = true;
decimal price = 9.99m;

// 可空型別
string? nullableStr = null;
int? nullableInt = null;

// var 型別推論
var list = new List<string>();

// 常數
const int MaxRetry = 3;
```

### 類別與屬性

```csharp
// PascalCase for class/method/property
public class User
{
    // private field：_camelCase
    private readonly int _id;

    // Auto property
    public string Name { get; set; } = string.Empty;
    public string Email { get; init; } = string.Empty;  // init-only setter

    // Constructor
    public User(int id, string name)
    {
        _id = id;
        Name = name;
    }

    // Method：PascalCase + Async suffix
    public async Task<string> GetDisplayNameAsync() =>
        await Task.FromResult($"{Name} <{Email}>");
}

// Record（不可變資料類型，適合 DTO）
public record CreateUserDto(string Name, string Email, string Password);
```

## 物件導向（OOP）

### 繼承與多型

```csharp
// 抽象類別
public abstract class Shape
{
    public abstract double Area();
    public virtual string Describe() => $"Shape with area {Area():F2}";
}

// 繼承
public class Circle : Shape
{
    public double Radius { get; }
    public Circle(double radius) => Radius = radius;
    public override double Area() => Math.PI * Radius * Radius;
}
```

### Interface

```csharp
// Interface：定義行為契約，不含實作
public interface IUserRepository
{
    Task<User?> GetByIdAsync(int id);
    Task<IEnumerable<User>> GetAllAsync();
    Task<User> CreateAsync(User user);
}

// 實作 Interface（依賴注入的基礎）
public class UserRepository : IUserRepository
{
    private readonly AppDbContext _db;
    public UserRepository(AppDbContext db) => _db = db;

    public async Task<User?> GetByIdAsync(int id) =>
        await _db.Users.FindAsync(id);

    public async Task<IEnumerable<User>> GetAllAsync() =>
        await _db.Users.ToListAsync();

    public async Task<User> CreateAsync(User user)
    {
        _db.Users.Add(user);
        await _db.SaveChangesAsync();
        return user;
    }
}
```

## LINQ

```csharp
var users = new List<User> { ... };

// 查詢語法
var adults = from u in users
             where u.Age >= 18
             orderby u.Name
             select u;

// 方法語法（更常用）
var activeAdults = users
    .Where(u => u.IsActive && u.Age >= 18)
    .OrderBy(u => u.Name)
    .Select(u => new { u.Name, u.Email })
    .ToList();

// 聚合
int count = users.Count(u => u.IsActive);
int maxAge = users.Max(u => u.Age);
var grouped = users.GroupBy(u => u.Role);

// FirstOrDefault（找不到回 null，不丟例外）
var user = users.FirstOrDefault(u => u.Id == id);
```

## async / await

```csharp
// Async method 加 Async 後綴
public async Task<User> GetUserAsync(int id)
{
    // await 等待非同步操作
    var user = await _repository.GetByIdAsync(id);
    if (user == null)
        throw new NotFoundException($"User {id} not found");
    return user;
}

// 並行執行
var [user, orders] = await Task.WhenAll(
    GetUserAsync(userId),
    GetOrdersAsync(userId)
);
```

## 例外處理

```csharp
public async Task<IActionResult> GetUserAsync(int id)
{
    try
    {
        var user = await _userService.GetByIdAsync(id);
        return Ok(user);
    }
    catch (NotFoundException ex)
    {
        return NotFound(ex.Message);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "取得 User {Id} 失敗", id);
        return StatusCode(500, "Internal Server Error");
    }
}
```

## 泛型

```csharp
// 泛型類別
public class Repository<T> where T : class
{
    private readonly DbContext _db;
    public Repository(DbContext db) => _db = db;

    public async Task<T?> GetByIdAsync(int id) =>
        await _db.Set<T>().FindAsync(id);
}

// 泛型方法
public T DeserializeJson<T>(string json) =>
    JsonSerializer.Deserialize<T>(json)!;
```

## Enum / Struct / Delegate

```csharp
// Enum：具名常數集合
public enum Status { Active, Inactive, Pending }

// Struct：值型別，適合小型不可變資料
public struct Point { public int X; public int Y; }

// Delegate：函式的型別（Func / Action 更常用）
public delegate string Formatter(int value);
Func<int, string> formatter = x => x.ToString("N0");
Action<string> logger = msg => Console.WriteLine(msg);
```

## using 陳述式

```csharp
// using：自動呼叫 Dispose（釋放非受控資源）
using var connection = new SqlConnection(connectionString);
await connection.OpenAsync();
// connection 在 scope 結束後自動 Dispose
```

## 連結

- [[dotnet-web-api]] — C# 在 Web API 中的應用
- [[oracle]] — C# 連接 Oracle 資料庫
- [[csharp-syntactic-sugar]] — 本頁用到的 `=>`、`?.`、`using`、`async` 等簡寫，編譯器實際改寫成什麼
