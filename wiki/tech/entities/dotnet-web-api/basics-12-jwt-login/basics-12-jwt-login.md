---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, jwt, jwt-bearer, password-hasher, claims, role, policy, authorize, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 8：Authentication 與 Authorization（JWT）.md
  - raw/Web Framework/NET Web API/NET 6 Web API JWT 驗證與授權完整設定與實作指南.md
created: 2026-11-01
updated: 2026-11-01
---

# 入門第 12 章：JWT 登入 — 登入後怎麼證明「我是我」

## 金鑰進了 repo，沒登入的人也能建立任務

[[basics-11-auth-concepts-and-pipeline]] 把 TaskTracker 的門鎖上了，但沒有鑰匙，同事急著測試，順手把簽章金鑰寫進 `appsettings.json` 並推上了 Git。從此任何能讀 repo 的人，不需要帳號密碼，就能在自己的電腦簽出一個「角色是 Admin」的 token。下面這個請求就是用那把金鑰自己簽的 token 打出去的：

```powershell
'{"title":"Created with a minted token"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H 'Content-Type: application/json' -H "Authorization: Bearer $minted" --data-binary '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Server: Kestrel
Location: http://localhost:5080/api/tasks/58cff5b7-1d57-4a24-b54a-b142e66f620a

{"id":"58cff5b7-1d57-4a24-b54a-b142e66f620a","title":"Created with a minted token","status":"todo","createdAt":"2026-10-31T06:17:37.1842394+00:00"}
```

（`$minted` 的簽法在 4.1 節末。）

201，建立成功，伺服器完全不知道這個人是誰：它只驗簽章，簽章對就相信 payload，整個機制的安全性押在「金鑰只有伺服器知道」。所以 JWT 登入要把幾件事一起做對：密碼怎麼存、登入失敗時回什麼、token 裡放什麼與怎麼簽、驗證時每個欄位各擋什麼。

本章從上一章結束時的 TaskTracker 出發：JWT Bearer 的驗證設定、`JwtOptions`、啟動時的金鑰長度檢查、兩個 middleware 都已就位，寫入端點標了 `[Authorize]`，但沒有任何方式拿到 token。本章補上 `User` 資料表、密碼雜湊、`POST /api/auth/login`，再把授權細分成 Viewer、Editor、Admin 三種角色，完成權限矩陣的後端部分：所有人可看、Editor 與 Admin 可編輯、只有 Admin 可刪除。前端的配合留給 [[basics-13-permissions-with-frontend]]。

機制推導不在本章重複：簽章演算法、金鑰輪替、撤銷見 [[12-jwt-deep-dive]]，Policy 與資源型授權見 [[14-authorization]]，Scheme 與 Claims 的內部運作見 [[11-authentication]]。

---

## 一、密碼：永遠不存明文

登入的第一個前提是資料庫裡有使用者，而最危險的欄位是密碼。最直覺的做法是原樣存進資料表、登入時比字串。問題在於資料庫一旦被讀走（備份檔外流、SQL injection、離職同事帶走一份 dump），攻擊者拿到的是每個人在其他網站可能重複使用的密碼，傷害超出你的系統。

比較好的做法是只存「從密碼算出來、無法反推」的雜湊值，登入時把輸入的密碼用同樣方式算一次再比對。有兩個細節常被忽略。雜湊不是加密：加密有金鑰可以還原，雜湊沒有還原的路，所以「忘記密碼」只能重設，不能寄回原密碼。其次，只做一次 SHA-256 之類的快速雜湊仍然太弱，攻擊者用顯卡每秒能試數十億個猜測；密碼雜湊要刻意設計得慢（重複計算十萬次以上），並混入每人不同的隨機 salt，讓同一組密碼得到不同結果，預先算好的對照表因此失效。迭代次數沒有一勞永逸的數字：.NET 的預設是 10 萬次，OWASP 對 PBKDF2-HMAC-SHA512 的建議是至少 21 萬次，硬體越強，門檻只會越高。

這些不需要自己實作。ASP.NET Core 內建的 `PasswordHasher<TUser>` 已經做好，不需要整個 Identity 的資料表與流程，專案不用額外安裝套件，`IPasswordHasher<User>` 直接可用。

### 1.1 User 資料表

先建立 `Entities/UserRole.cs` 與 `Entities/User.cs`：

```csharp
namespace TaskTracker.Api.Entities;

public enum UserRole
{
    Viewer,
    Editor,
    Admin
}

public class User
{
    public Guid Id { get; set; }

    public string Email { get; set; } = string.Empty;

    public string PasswordHash { get; set; } = string.Empty;

    public UserRole Role { get; set; }
}
```

（兩個型別各放自己的檔案，這裡合併呈現。）屬性叫 `PasswordHash`，沒有任何欄位叫 `Password`，命名本身就是一道防線：沒有地方可以放明文。

接著是 EF Core 的設定 `Data/Configurations/UserConfiguration.cs`，沿用 [[basics-10-efcore-and-oracle]] 的風格（`AppDbContext` 已用 `ApplyConfigurationsFromAssembly` 載入全部設定，只需新增一行 `public DbSet<User> Users => Set<User>();`）：

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using TaskTracker.Api.Entities;

namespace TaskTracker.Api.Data.Configurations;

public sealed class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("USERS");

        builder.HasKey(u => u.Id);
        builder.Property(u => u.Id).HasColumnName("ID").ValueGeneratedNever();
        builder.Property(u => u.Email).HasColumnName("EMAIL").HasMaxLength(256).IsRequired();
        builder.Property(u => u.PasswordHash).HasColumnName("PASSWORD_HASH").HasMaxLength(512).IsRequired();
        builder.Property(u => u.Role).HasColumnName("ROLE").HasConversion<string>().HasMaxLength(16).IsRequired();

        builder.HasIndex(u => u.Email).IsUnique().HasDatabaseName("UX_USERS_EMAIL");
    }
}
```

兩個決定：`Role` 用 `HasConversion<string>()` 存成 `'Admin'` 而不是整數，之後在 enum 中間插入新角色，舊資料不會悄悄變成另一個角色；`Email` 加唯一索引，因為「一個 email 一個帳號」要由資料庫保證，程式裡先查再新增在並行時擋不住。

建立 migration 並看它實際會執行的 SQL（連線字串沿用上一章的設定）：

```powershell
dotnet ef migrations add AddUsers --project src/TaskTracker.Api --output-dir Data/Migrations
dotnet ef migrations script InitialCreate AddUsers --project src/TaskTracker.Api --no-build
```

```text
BEGIN
EXECUTE IMMEDIATE 'CREATE TABLE
"USERS" (
    "ID" RAW(16) NOT NULL,
    "EMAIL" NVARCHAR2(256) NOT NULL,
    "PASSWORD_HASH" NVARCHAR2(512) NOT NULL,
    "ROLE" NVARCHAR2(16) NOT NULL,
    CONSTRAINT "PK_USERS" PRIMARY KEY ("ID")
)';
END;
/

CREATE UNIQUE INDEX "UX_USERS_EMAIL" ON "USERS" ("EMAIL")
/
```

（完整輸出的最後還有一筆寫入 `__EFMigrationsHistory` 的 INSERT，這裡省略。）`PASSWORD_HASH` 預留 512 個字元，遠大於 1.3 節實際的 84 個字元，因為雜湊格式會隨 .NET 版本演進，留餘裕比之後改欄位便宜。

### 1.2 建立示範帳號，密碼不進原始碼

現在需要三個示範帳號，每個角色一個。示範密碼不能寫在 `Program.cs` 或 `appsettings.json`，兩者都會進 Git，所以走和簽章金鑰相同的路：開發機放 User Secrets，部署環境放環境變數。新增 `Options/SeedOptions.cs`：

```csharp
namespace TaskTracker.Api.Options;

public sealed class SeedOptions
{
    public const string SectionName = "Seed";

    public string? Password { get; init; }
}
```

再新增 `Data/DatabaseSeeder.cs`。它只在 `USERS` 表是空的而且有設定密碼時才建立帳號，用 `IPasswordHasher<User>` 把密碼轉成雜湊後存入。沒設密碼時它會在 log 留一行警告再略過，免得啟動後沒有任何帳號卻查不出原因：

```csharp
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using TaskTracker.Api.Entities;
using TaskTracker.Api.Options;

namespace TaskTracker.Api.Data;

public sealed class DatabaseSeeder
{
    private readonly AppDbContext _db;
    private readonly IPasswordHasher<User> _hasher;
    private readonly SeedOptions _seed;
    private readonly ILogger<DatabaseSeeder> _logger;

    public DatabaseSeeder(AppDbContext db, IPasswordHasher<User> hasher, IOptions<SeedOptions> seed, ILogger<DatabaseSeeder> logger)
    {
        _db = db;
        _hasher = hasher;
        _seed = seed.Value;
        _logger = logger;
    }

    public async Task SeedUsersAsync(CancellationToken ct)
    {
        if (string.IsNullOrEmpty(_seed.Password))
        {
            _logger.LogWarning("Seed:Password is not configured, skipping the demo users.");
            return;
        }

        if (await _db.Users.AnyAsync(ct))
        {
            return;
        }

        foreach (var role in Enum.GetValues<UserRole>())
        {
            var user = new User
            {
                Id = Guid.NewGuid(),
                Email = $"{role.ToString().ToLowerInvariant()}@example.com",
                Role = role
            };
            user.PasswordHash = _hasher.HashPassword(user, _seed.Password);
            _db.Users.Add(user);
        }

        await _db.SaveChangesAsync(ct);
        _logger.LogInformation("Seeded {Count} demo users.", Enum.GetValues<UserRole>().Length);
    }
}
```

三個帳號是 `viewer@`、`editor@`、`admin@` 加 `example.com`，email 一律小寫；登入時也先轉小寫再查，`Admin@Example.com` 與 `admin@example.com` 不會變成兩個帳號。

最後登記服務、讀取設定並在啟動時呼叫。`Extensions/ServiceCollectionExtensions.cs` 的 `AddTaskTrackerServices` 加四行，`AddTaskTrackerOptions` 加一個 `SeedOptions` 的綁定（檔案開頭補上 `Microsoft.AspNetCore.Identity` 與 `TaskTracker.Api.Entities` 兩個 using）：

```csharp
// AddTaskTrackerServices
services.AddSingleton<IPasswordHasher<User>, PasswordHasher<User>>();
services.AddSingleton<ITokenService, TokenService>();
services.AddScoped<IAuthService, AuthService>();
services.AddScoped<DatabaseSeeder>();

// AddTaskTrackerOptions
services.AddOptions<SeedOptions>()
    .BindConfiguration(SeedOptions.SectionName);
```

`Extensions/WebApplicationExtensions.cs` 的 `InitializeDatabaseAsync` 在 `MigrateAsync()` 之後加上一行 `await scope.ServiceProvider.GetRequiredService<DatabaseSeeder>().SeedUsersAsync(CancellationToken.None);`。開發環境的 `MigrateOnStartup` 是 `true`（[[basics-10-efcore-and-oracle]] 設定的），所以啟動一次就會建表並建立帳號。先設定示範密碼：

```powershell
dotnet user-secrets set "Seed:Password" "<自訂的示範密碼>" --project src/TaskTracker.Api
```

剛登記的 `TokenService` 與 `AuthService` 還沒寫，現在編譯會失敗。第二節建立 `AuthService`、第四節建立 `TokenService`，第四節的程式碼寫完後再執行 `dotnet run --project src/TaskTracker.Api` 啟動，後面各節的指令都假設服務已經在 `http://localhost:5080` 跑著。

### 1.3 資料庫裡的雜湊長什麼樣子

`PasswordHasher<User>` 實際存了什麼，不需要相信文件，直接查。下面的 PowerShell 取出 admin 的 `PASSWORD_HASH`（`$hash` 的值用 sqlplus 或任何 SQL 工具查 `select password_hash from users where email = 'admin@example.com'` 取得），把 Base64 解開，按 V3 格式的欄位位置讀出內容：

```powershell
$bytes = [Convert]::FromBase64String($hash)
function ReadUInt32BigEndian([byte[]]$b, [int]$offset) { ([uint32]$b[$offset] -shl 24) + ([uint32]$b[$offset + 1] -shl 16) + ([uint32]$b[$offset + 2] -shl 8) + [uint32]$b[$offset + 3] }
"Base64 字串長度：$($hash.Length)；前 12 個字元：$($hash.Substring(0, 12))"
"格式標記：$($bytes[0])（1 表示 V3）"
"PRF：$(ReadUInt32BigEndian $bytes 1)（KeyDerivationPrf：0 是 HMACSHA1，1 是 HMACSHA256，2 是 HMACSHA512）"
"迭代次數：$(ReadUInt32BigEndian $bytes 5)"
"salt 長度：$(ReadUInt32BigEndian $bytes 9) bytes"
```

```text
Base64 字串長度：84；前 12 個字元：AQAAAAIAAYag
格式標記：1（1 表示 V3）
PRF：2（KeyDerivationPrf：0 是 HMACSHA1，1 是 HMACSHA256，2 是 HMACSHA512）
迭代次數：100000
salt 長度：16 bytes
```

這串 84 個字元解開是 61 個 byte：1 byte 格式標記、4 byte 演算法代號、4 byte 迭代次數、4 byte salt 長度，然後是 16 byte 的 salt 與 32 byte 的雜湊結果。演算法、迭代次數與 salt 都存在字串自己身上，所以未來 .NET 調高預設的迭代次數，或你自己用 `PasswordHasherOptions.IterationCount` 調高時，舊雜湊仍然讀得出參數、驗得過；兩個人用同一組密碼，因為 salt 隨機，存的字串也不同。

`VerifyHashedPassword` 的回傳值除了 `Success` 與 `Failed`，還有 `SuccessRehashNeeded`：密碼正確，但雜湊用的是舊參數。下一節的登入流程會在這種情況用同一個密碼重算並存回去，使用者無感升級。

---

## 二、登入：驗證憑證，且失敗時不洩漏資訊

雜湊準備好了，現在寫登入端點。請求的格式用 DTO 定義，沿用 [[basics-06-dto-design]] 與 [[basics-05-model-binding-and-validation]] 的做法。`Dtos/LoginRequest.cs` 與 `Dtos/LoginResponse.cs`：

```csharp
using System.ComponentModel.DataAnnotations;

namespace TaskTracker.Api.Dtos;

public sealed class LoginRequest
{
    [Required]
    [EmailAddress]
    [StringLength(256)]
    public string Email { get; init; } = string.Empty;

    [Required]
    [StringLength(128)]
    public string Password { get; init; } = string.Empty;
}

public sealed record LoginResponse(string AccessToken, string TokenType, int ExpiresIn);
```

`Password` 設 `StringLength(128)` 上限，因為密碼雜湊刻意很慢，不限長度的話，有人送幾 MB 的密碼就能讓伺服器忙很久。回應的三個欄位是 OAuth 2.0 慣用名稱：`expiresIn` 是還有幾秒到期，前端用它決定何時重新登入。

### 2.1 失敗時回什麼

登入失敗有兩種原因：帳號不存在，或帳號存在但密碼錯。如果兩種情況回不同的訊息（「查無此帳號」與「密碼錯誤」），攻擊者拿一份 email 清單去打登入端點，就能從回應分辨出哪些 email 在你的系統裡有帳號，再針對這些帳號猜密碼。比較好的做法是兩種情況回完全相同的狀態碼與訊息。下面是實際打出去的結果：

```powershell
'{"email":"admin@example.com","password":"wrong-password"}' | curl.exe -s -i -X POST http://localhost:5080/api/auth/login -H 'Content-Type: application/json' --data-binary '@-'
```

```text
HTTP/1.1 401 Unauthorized
Content-Type: application/problem+json

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.2","title":"Unauthorized","status":401,"detail":"Invalid email or password.","traceId":"00-a657175eae2eac0d2a0491834d46da30-6fd9068186c881cf-00"}
```

把 email 換成不存在的 `nobody@example.com`：

```powershell
'{"email":"nobody@example.com","password":"wrong-password"}' | curl.exe -s -i -X POST http://localhost:5080/api/auth/login -H 'Content-Type: application/json' --data-binary '@-'
```

```text
HTTP/1.1 401 Unauthorized
Content-Type: application/problem+json

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.2","title":"Unauthorized","status":401,"detail":"Invalid email or password.","traceId":"00-6161919e74555b21583142c69f621bf6-c933a8a732d171cf-00"}
```

除了每次請求不同的 `traceId`，兩個回應一模一樣。但只統一訊息還不夠，另一個管道是回應時間。帳號不存在時，如果程式查不到 user 就直接回 401，會比「查到了、算一次雜湊再比對」快上許多，攻擊者量測回應時間一樣分得出來。所以 `AuthService` 在查不到帳號時，仍然拿一份事先算好的假雜湊跑一次 `VerifyHashedPassword`，讓兩條路徑都付出一次雜湊的成本。

```csharp
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using TaskTracker.Api.Data;
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Entities;
using TaskTracker.Api.Exceptions;

namespace TaskTracker.Api.Services;

public sealed class AuthService : IAuthService
{
    private static readonly User UnknownUser = new() { Email = "unknown@invalid" };

    private readonly AppDbContext _db;
    private readonly IPasswordHasher<User> _hasher;
    private readonly ITokenService _tokens;
    private readonly TimeProvider _timeProvider;
    private readonly string _unknownUserHash;

    public AuthService(AppDbContext db, IPasswordHasher<User> hasher, ITokenService tokens, TimeProvider timeProvider)
    {
        _db = db;
        _hasher = hasher;
        _tokens = tokens;
        _timeProvider = timeProvider;
        _unknownUserHash = hasher.HashPassword(UnknownUser, Guid.NewGuid().ToString("N"));
    }

    public async Task<LoginResponse> LoginAsync(LoginRequest request, CancellationToken ct)
    {
        var email = request.Email.Trim().ToLowerInvariant();
        var user = await _db.Users.FirstOrDefaultAsync(u => u.Email == email, ct);

        // 帳號不存在時仍然驗證一次雜湊，讓兩種失敗的回應時間接近，也回同一個訊息
        var verification = _hasher.VerifyHashedPassword(user ?? UnknownUser, user?.PasswordHash ?? _unknownUserHash, request.Password);
        if (user is null || verification == PasswordVerificationResult.Failed)
        {
            throw new InvalidCredentialsException();
        }

        if (verification == PasswordVerificationResult.SuccessRehashNeeded)
        {
            user.PasswordHash = _hasher.HashPassword(user, request.Password);
            await _db.SaveChangesAsync(ct);
        }

        var token = _tokens.CreateAccessToken(user);
        return new LoginResponse(token.Value, "Bearer", (int)(token.ExpiresAt - _timeProvider.GetUtcNow()).TotalSeconds);
    }
}
```

`Services/IAuthService.cs` 的 `IAuthService` 只有一個方法 `Task<LoginResponse> LoginAsync(LoginRequest request, CancellationToken ct)`。失敗時丟出的例外只有一行：`public sealed class InvalidCredentialsException() : Exception("Invalid email or password.");`（放在 `Exceptions/InvalidCredentialsException.cs`）。

把它對應成 401 的方式，沿用 [[basics-08-middleware-and-exception-handling]] 的 `DomainExceptionHandler`，在 `switch` 裡加一行：

```csharp
InvalidCredentialsException => StatusCodes.Status401Unauthorized,
```

Controller 保持很薄。`Controllers/AuthController.cs`：

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Services;

namespace TaskTracker.Api.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    [AllowAnonymous]
    [HttpPost("login")]
    public async Task<ActionResult<LoginResponse>> LoginAsync(LoginRequest request, CancellationToken ct)
    {
        return Ok(await _authService.LoginAsync(request, ct));
    }
}
```

這裡的 `[AllowAnonymous]` 目前不是必要的（`AuthController` 沒有類別層級的 `[Authorize]`），標它是把意圖寫進程式碼：日後有人加全域 `FallbackPolicy`（見 [[14-authorization]]），登入不會跟著被鎖死。

請求格式本身不合法時，在進到 `AuthService` 之前就由 `[ApiController]` 擋下，回 400：

```powershell
'{"email":"not-an-email","password":"x"}' | curl.exe -s -i -X POST http://localhost:5080/api/auth/login -H 'Content-Type: application/json' --data-binary '@-'
```

```text
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json; charset=utf-8

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.1","title":"One or more validation errors occurred.","status":400,"errors":{"Email":["The Email field is not a valid e-mail address."]},"traceId":"00-6ce88cb33f509fa6172145bc0543fd62-6a033f1f74b407ca-00"}
```

400 只說「格式不對」，沒有透露帳號是否存在，和統一的 401 不衝突。本章的登入端點也沒有擋暴力猜測，限流與帳號鎖定屬於上線前的安全加固，不在入門篇範圍。

---

## 三、JWT 長什麼樣子：解開它，看看 Base64 不是加密

登入成功時，回應是這樣的（`accessToken` 很長，這裡是實際登入 admin 得到的完整值）：

```powershell
'{"email":"admin@example.com","password":"<Seed:Password 的值>"}' | curl.exe -s -i -X POST http://localhost:5080/api/auth/login -H 'Content-Type: application/json' --data-binary '@-'
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"accessToken":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0YXNrdHJhY2tlci13ZWIiLCJpc3MiOiJ0YXNrdHJhY2tlci1hcGkiLCJleHAiOjE3OTM0MjkyMzgsImlhdCI6MTc5MzQyNzQzOCwibmJmIjoxNzkzNDI3NDM4LCJzdWIiOiI2MmVkMWEwZS01YzdmLTRmZWQtYWVjZi1iMjViYzI1NGMzOGYiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwianRpIjoiMjRkNGIyYTktMjg1OC00YjQ0LTg2ODgtZmVmYmEwZTdhYmU4Iiwicm9sZSI6IkFkbWluIn0.gf2jGl3TfIh86zEMx8H7x9ZCbvDRVqWxkmPLdsSXG4Q","tokenType":"Bearer","expiresIn":1799}
```

後續的指令需要把 token 存進變數：把上面的 curl 去掉 `-i`，輸出用 `| ConvertFrom-Json` 接起來，再取 `.accessToken`，例如 `$adminToken = (... | ConvertFrom-Json).accessToken`。
`editor@example.com` 與 `viewer@example.com` 同理，變數名稱用 `$editorToken`、`$viewerToken`。`expiresIn` 是 1799 而不是 1800，因為它是簽發當下起算的剩餘秒數，扣掉處理耗掉的零點幾秒再捨去。

這串字用兩個 `.` 切成 header、payload、signature 三段，每段都是 Base64Url 編碼（Base64 的變體，`+` `/` 換成 `-` `_` 並省略結尾 `=`，可直接放進 URL 與標頭）。前兩段只需要幾行 PowerShell 就能解開：

```powershell
function Get-JwtPart([string]$token, [int]$index) {
    $part = $token.Split('.')[$index].Replace('-', '+').Replace('_', '/')
    $part = $part.PadRight($part.Length + (4 - $part.Length % 4) % 4, '=')
    [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($part))
}
Get-JwtPart $adminToken 0
Get-JwtPart $adminToken 1
```

```text
{"alg":"HS256","typ":"JWT"}
{"aud":"tasktracker-web","iss":"tasktracker-api","exp":1793429238,"iat":1793427438,"nbf":1793427438,"sub":"62ed1a0e-5c7f-4fed-aecf-b25bc254c38f","email":"admin@example.com","jti":"24d4b2a9-2858-4b44-8688-fefba0e7abe8","role":"Admin"}
```

這段輸出回答了好幾個問題。最重要的是：不需要任何金鑰，拿到 token 的人（DevTools、經過的 proxy、貼在 issue 裡的 log）都讀得到 payload 的全部內容，所以 JWT 只是「簽過章」，沒有「加過密」。這就是 claim 裡不能放密碼、身分證字號的原因。header 只說明用什麼演算法（`alg: HS256`）簽的，以及這是一個 JWT（`typ`），裡面沒有任何「加密資訊」。

payload 裡每個 claim 各有用途。`iss` 是簽發者，`aud` 是預定使用者，`exp` 是過期時間點，`iat` 是簽發時間，`nbf`（not before）是此時間之前不可使用；三個時間都是 Unix 時間（秒），`exp` 減 `iat` 是 1800，剛好 30 分鐘。`sub` 放 `User.Id`（GUID），不放 email，因為 email 可能改、可能被重複使用，id 不會。`jti` 是這個 token 自己的唯一 id，日後做黑名單或追蹤單一 token 才用得到。`email` 與 `role` 是 TaskTracker 自己加的。

第三段 signature 是用伺服器金鑰，對「header 段 + `.` + payload 段」算出來的 HMAC-SHA256。驗證端用同一把金鑰重算，與 token 附的簽章比對，任何人改了 header 或 payload 的一個字元，結果就不同。所以簽章保護的是完整性（內容沒被改過、確實是持有金鑰的人簽的），不保護機密性：能讀不等於能改，能改要靠金鑰。

用實驗確認「能改要靠金鑰」。下面把 viewer 的 token payload 解開，把 `"role":"Viewer"` 換成 `"role":"Admin"`，重新編碼，簽章那一段原封不動貼回去：

```powershell
function ConvertTo-Base64Url([byte[]]$bytes) { [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_') }
$parts = $viewerToken.Split('.')
$tampered = (Get-JwtPart $viewerToken 1).Replace('"role":"Viewer"', '"role":"Admin"')
$tamperedToken = "$($parts[0]).$(ConvertTo-Base64Url ([Text.Encoding]::UTF8.GetBytes($tampered))).$($parts[2])"
'{"title":"x"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H 'Content-Type: application/json' -H "Authorization: Bearer $tamperedToken" --data-binary '@-'
```

```text
HTTP/1.1 401 Unauthorized
Content-Type: application/problem+json; charset=utf-8
WWW-Authenticate: Bearer error="invalid_token", error_description="The signature key was not found"

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.2","title":"Unauthorized","status":401,"traceId":"00-d9e733f4bab0286d490ef62ea87d2419-f90cd68cc5f2b36d-00"}
```

401。竄改的 token 沒有通過，這是簽章在工作。但注意 `error_description` 寫的是「找不到簽章金鑰」，實際原因是「簽章對不上」，金鑰明明就在。這個措辭下一節還會再碰到，查問題時要記得：看到 `The signature key was not found`，除了金鑰沒設對，也可能只是 token 被改過。

---

## 四、簽發：claims、過期時間與金鑰

知道 token 的長相之後，簽發的程式就很好讀了。先在 `Services/ITokenService.cs` 定義介面 `ITokenService`（一個方法 `AccessToken CreateAccessToken(User user)`）與 `public sealed record AccessToken(string Value, DateTimeOffset ExpiresAt);`，再寫實作：

```csharp
using System.Security.Claims;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;
using TaskTracker.Api.Entities;
using TaskTracker.Api.Options;

namespace TaskTracker.Api.Services;

public sealed class TokenService : ITokenService
{
    private readonly JwtOptions _jwt;
    private readonly TimeProvider _timeProvider;
    private readonly JsonWebTokenHandler _handler = new();
    private readonly SigningCredentials _credentials;

    public TokenService(IOptions<JwtOptions> jwt, TimeProvider timeProvider)
    {
        _jwt = jwt.Value;
        _timeProvider = timeProvider;
        _credentials = new SigningCredentials(
            new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_jwt.SigningKey)),
            SecurityAlgorithms.HmacSha256);
    }

    public AccessToken CreateAccessToken(User user)
    {
        var now = _timeProvider.GetUtcNow();
        var expires = now.AddMinutes(_jwt.AccessTokenMinutes);
        var descriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(
            [
                new Claim(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
                new Claim(JwtRegisteredClaimNames.Email, user.Email),
                new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
                new Claim("role", user.Role.ToString())
            ]),
            Issuer = _jwt.Issuer,
            Audience = _jwt.Audience,
            IssuedAt = now.UtcDateTime,
            NotBefore = now.UtcDateTime,
            Expires = expires.UtcDateTime,
            SigningCredentials = _credentials
        };
        return new AccessToken(_handler.CreateToken(descriptor), expires);
    }
}
```

這段有幾個設計選擇。`JsonWebTokenHandler` 是 .NET 8 之後 JwtBearer 預設用來驗證的 handler，簽發用同一個；較舊的 `JwtSecurityTokenHandler` 仍然存在，新程式碼不需要。過期時間來自 `JwtOptions.AccessTokenMinutes`，不是寫死的 `AddMinutes(60)`：設定檔宣告了過期時間卻沒被程式使用，改設定看似生效，實際沒有任何改變。時間來自注入的 `TimeProvider`，測試才能控制「現在幾點」（[[basics-15-testing]] 會用到）。類別登記為 singleton，因為 `SigningCredentials` 建立一次就能重複使用。

Claim 的原則是只放識別身分與授權判斷需要的最少資料，不放敏感資料，因為每個 claim 都會跟著每個請求走。一句話概括：JWT 用來表達「你是誰」，不用來保存「系統現在的狀態」，狀態會變，而簽出去的 token 改不了。TaskTracker 只放 `sub`、`email`、`jti` 與 `role`。`role` 用字面字串 `"role"` 當名稱，而不是長 URI 的 `ClaimTypes.Role`，讓 token 裡的名稱和程式讀到的一致（第六節）。角色來自 `user.Role`（資料庫）；示範程式碼常把角色寫死成 `"Admin"`，複製貼上之後所有人都變成 Admin。

### 4.1 金鑰：32 bytes 的門檻與誤導性的錯誤訊息

HS256 用的是對稱金鑰，簽發端與驗證端共用同一個秘密。很多教學寫「至少 16 個字元」，這是錯的：HMAC-SHA256 的金鑰長度不得小於雜湊輸出長度，也就是 256 bits，32 bytes。實測用不同長度的金鑰呼叫 `JsonWebTokenHandler.CreateToken`，結果如下：

| 金鑰長度 | 結果 |
| --- | --- |
| 0 bytes | `ArgumentException`，`IDX10703: ... key length is zero` |
| 1 到 15 bytes | `IDX10653: The encryption algorithm 'HS256' requires a key size of at least '128' bits` |
| 16 到 31 bytes | `IDX10720: ... the key size must be greater than: '256' bits, key has '128' bits` |
| 32 bytes 以上 | 簽發成功 |

這兩句訊息很容易誤導。`IDX10653` 說至少 128 bits，讀的人以為 16 bytes 就夠，但 16 bytes 會得到第二個錯誤；`IDX10720` 說「must be greater than 256 bits」，實際上剛好 256 bits（32 bytes）就成功，應理解成「不小於」。同樣的規則往上推：HS384 要 48 bytes，HS512 要 64 bytes。

更麻煩的是失敗的時機。金鑰太短時應用程式照常啟動，健康檢查全綠，直到第一個使用者登入、程式第一次簽 token 才丟例外，使用者看到的是 500。這是上一章 `JwtOptionsValidator` 存在的理由：`ValidateOnStart()` 讓金鑰不符時應用程式啟動失敗，問題在部署時暴露。

驗證端的症狀完全不同，也更難查。用一把 16 bytes 的金鑰簽出格式合法的 token（依 HMAC-SHA256 的算法），丟給設了同一把金鑰的驗證端，結果不是「金鑰太短」，而是：

```text
SecurityTokenSignatureKeyNotFoundException: IDX10517: Signature validation failed. The token's kid is missing. Keys tried: ...
```

太短的金鑰不會被拿來驗簽，訊息卻指向 `kid`，排查的人很容易往金鑰輪替的方向查錯。在 JwtBearer 底下，這個例外對應第三節的 401 加 `The signature key was not found`。所以那句訊息至少有三種可能：金鑰沒設對、金鑰太短、token 被改過，三個都要檢查。

長度只是門檻，不代表強度：32 個相同字元也能通過檢查，卻是一把形同虛設的金鑰。金鑰要由密碼學隨機數產生，指令和上一章相同：

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$key = [Convert]::ToBase64String($bytes)
dotnet user-secrets set "Jwt:SigningKey" $key --project src/TaskTracker.Api
```

金鑰放 User Secrets，不放 `appsettings.json`。不少教學把 `appsettings.json` 列為「安全的存放位置」，那是錯的：它會進版控，等同硬編碼。開發機用 User Secrets，部署環境用環境變數 `Jwt__SigningKey` 或 K8s Secret（見 [[basics-09-configuration-and-environments]]、[[17-configuration-and-secrets]]）。

為什麼金鑰外洩這麼嚴重？開頭那個 201 的 token 就是這樣來的。假設攻擊者拿到了金鑰，簽一個角色是 Admin 的 token 只需要這樣：

```powershell
function ConvertTo-Base64Url([byte[]]$bytes) { [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_') }
$header = ConvertTo-Base64Url ([Text.Encoding]::UTF8.GetBytes('{"alg":"HS256","typ":"JWT"}'))
$payload = ConvertTo-Base64Url ([Text.Encoding]::UTF8.GetBytes('{"sub":"11111111-1111-1111-1111-111111111111","email":"attacker@example.com","role":"Admin","iss":"tasktracker-api","aud":"tasktracker-web","exp":4102444800}'))
$hmac = New-Object Security.Cryptography.HMACSHA256 -ArgumentList (,[Text.Encoding]::UTF8.GetBytes($jwtKey))
$signature = ConvertTo-Base64Url ($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes("$header.$payload")))
$minted = "$header.$payload.$signature"
```

`$jwtKey` 是 `Jwt:SigningKey` 的原文（在自己的機器上用 `dotnet user-secrets list --project src/TaskTracker.Api` 查）。這幾行不需要任何 ASP.NET Core 程式碼，也不碰資料庫：`sub` 是隨便編的 GUID，資料庫裡根本沒有這個使用者，伺服器只驗簽章，簽章對就認定是 Admin。金鑰外洩的處置只有一個：視為全面淪陷，換新金鑰，所有已簽發的 token 隨之失效。

---

## 五、驗證：`TokenValidationParameters` 每個欄位在擋什麼

簽發端決定 token 裡有什麼，驗證端決定「什麼樣的 token 才算數」。上一章已經設好驗證，這一節回頭逐項看它為什麼是這樣。現在的 `AddTaskTrackerAuthentication` 裡，`JwtBearerOptions` 的設定如下（相對上一章多了 `MapInboundClaims = false` 與 `RoleClaimType = "role"` 兩行，下一節說明）：

```csharp
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer();
services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Configure<IOptions<JwtOptions>>((bearer, jwt) =>
    {
        bearer.MapInboundClaims = false;
        bearer.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwt.Value.Issuer,
            ValidateAudience = true,
            ValidAudience = jwt.Value.Audience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwt.Value.SigningKey)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),
            RoleClaimType = "role"
        };
    });
```

這些欄位可以想成驗收清單，逐項勾選才算有效。每一項對應一種具體的失誤或攻擊：

| 欄位 | 檢查的內容 | 關掉的後果 |
| --- | --- | --- |
| `ValidateIssuerSigningKey` 與 `IssuerSigningKey` | 簽章是否能用這把金鑰重算出來 | 任何人都能偽造 token，直接等於沒有驗證 |
| `ValidateIssuer` 與 `ValidIssuer` | `iss` 是不是預期的簽發者 | 同一把金鑰簽的、但來自別的系統的 token 也被接受 |
| `ValidateAudience` 與 `ValidAudience` | `aud` 是不是預期的接收者 | 簽發給系統 A 的 token 可以拿去呼叫系統 B |
| `ValidateLifetime` | `exp` 與 `nbf` | token 永遠有效，外洩後無法自然失效 |
| `ClockSkew` | 容許簽發端與驗證端的時鐘差 | 見下文 |

簽章那一列在第三節看過了。`ValidateIssuer` 與 `ValidateAudience` 的價值要在多系統情境才看得出來：兩支 API 共用同一把金鑰時，系統 A 簽的 token 本身合法，只是不是給系統 B 的。有些教學的表格註明「單一服務可選擇不驗受眾」，字面成立，風險確實低；但開著不花成本，而金鑰共用範圍擴大時，關掉的開關很少有人記得重開，所以本書預設全開。實測 audience 不符：沿用 4.1 節末的簽法（`$jwtKey` 與同樣的 header），把 payload 的 `aud` 改成 `another-app`，簽出 `$wrongAudience`：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks -H "Authorization: Bearer $wrongAudience"
```

```text
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token", error_description="The audience '(null)' is invalid"
```

401。訊息裡的 audience 顯示 `(null)`，與 token 內實際的 `another-app` 不一致，所以遇到 audience 錯誤時別只讀訊息，把 payload 解開（第三節的函式）對照 `aud` 與 `ValidAudience`。

過期的 token 則有清楚的訊息：同樣的簽法，把 `exp` 改成 `946684800`（2000 年 1 月 1 日）簽出 `$expired`，回 401 與 `error_description="The token expired at '01/01/2000 00:00:00'"`。

三種失敗（簽章、audience、過期）都是 401，且都附 `WWW-Authenticate`，讓呼叫端知道是「token 有問題」；完全沒帶 token 時標頭只有單純的 `Bearer`。

### 5.1 ClockSkew：為什麼預設要多給 5 分鐘

`ClockSkew` 的預設值是 5 分鐘。它存在是因為不同機器的時鐘不會完全一致：簽發的伺服器時鐘快了 30 秒，剛簽出的 token，在驗證的機器看來可能還沒到 `nbf`。給 5 分鐘的容許值，這類誤差就不會造成偶發的 401。

代價是 token 的實際壽命比宣告的長：`exp` 是 10:00 的 token，預設下到 10:05 都被接受，「短壽命 access token」策略因此打折。容器與雲端環境的時鐘通常同步到毫秒級，所以 TaskTracker 縮成 30 秒；設成 `TimeSpan.Zero` 之前先確認各台伺服器真的有校時。深入的取捨見 [[12-jwt-deep-dive]] 的 3.1 節。

---

## 六、Claims 進到程式後的名字：兩個容易出事的設定

token 驗證通過後，payload 的 claim 會變成 `HttpContext.User`（`ClaimsPrincipal`）的內容，授權檢查與你的程式都讀它。這裡有個過去留下的包袱：ASP.NET Core 預設把短名稱改寫成 .NET 慣用的長 URI，`sub` 變成 `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier`，`role` 變成 `http://schemas.microsoft.com/ws/2008/06/identity/claims/role`。這由 `MapInboundClaims` 控制，預設是 `true`。

不同的名字影響兩個地方：`User.FindFirst("sub")` 找不找得到，以及 `[Authorize(Roles = "Admin")]` 認不認得角色。下面用一個只有 `/claims` 端點的最小專案（不是 TaskTracker）對照。`GET /claims`（`[Authorize]`）回傳 `User.Claims`、`User.Identity.Name`、身分的 `NameClaimType` 與 `RoleClaimType`、`User.IsInRole("Admin")`；`GET /claims/admin` 標 `[Authorize(Roles = "Admin")]`。

測試用的 token 帶有 `sub=42`、`email=alice@example.com`、`name=alice`，以及兩個 `role`（`Admin` 與 `Editor`）。依序測三種設定，輸出只留 claim 清單與判斷結果。

A：什麼都不改（預設）。

```text
"http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier = 42",
"http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress = alice@example.com",
"name = alice",
"http://schemas.microsoft.com/ws/2008/06/identity/claims/role = Admin",
"http://schemas.microsoft.com/ws/2008/06/identity/claims/role = Editor",
"identityName":null, "isInRoleAdmin":true
GET /claims/admin -> 200 OK | body: admin ok
```

預設下 `sub`、`email`、`role` 都被改名了，所以 `User.FindFirst("sub")` 找不到任何東西。有一個意外的結果：`identityName` 是 `null`。token 明明有 `name = alice`，`User.Identity.Name` 卻是空的。

B：只把 `MapInboundClaims` 設成 `false`。

```text
"sub = 42",
"email = alice@example.com",
"name = alice",
"role = Admin",
"role = Editor",
"identityName":null, "roleClaimType":"http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
"isInRoleAdmin":false
GET /claims/admin -> 403 Forbidden
```

名字保持了 token 裡的樣子，`User.FindFirst("sub")` 找到了。可是 `isInRoleAdmin` 變成 `false`，`[Authorize(Roles = "Admin")]` 的端點回了 403，而 token 裡明明有 `role = Admin`。原因是身分物件有一個 `RoleClaimType` 屬性，告訴 `IsInRole()` 該去找哪個名字的 claim，它預設是那個長 URI。B 把 claim 的名字改回 `role` 了，但沒有告訴身分物件去找 `role`，於是找不到，判斷成「沒有這個角色」。

C：關掉 `MapInboundClaims`，並設定 `RoleClaimType = "role"` 與 `NameClaimType = "name"`。

```text
"identityName":"alice", "nameClaimType":"name", "roleClaimType":"role",
"isInRoleAdmin":true
GET /claims/admin -> 200 OK | body: admin ok
```

這才是完整的設定。TaskTracker 採用的就是 C（第五節的程式碼），只是沒設 `NameClaimType`，因為它的 token 沒有 `name` claim。

為什麼要關掉對應？讓程式裡讀到的名字和 token 裡的一致，也和前端解開 JWT 看到的一致，不必記一份長 URI 對照表。代價是 B 的陷阱：兩個設定必須成對。只關 `MapInboundClaims` 而漏掉 `RoleClaimType`，沒有編譯錯誤、沒有啟動錯誤，所有 `[Authorize(Roles = ...)]` 的端點對所有人回 403。症狀是 403 而不是 401，查的人會往「權限設定錯了」查，而不是往 claim 的名字查。另外，token 裡的兩個 `role` 會變成兩個獨立的 claim，不是一個陣列字串。

### 6.1 `sub` 不等於 `User.Identity.Name`

常見的教學寫「JWT 驗證預設把 `sub` 對應到 `User.Identity.Name`」，實測是錯的，A 的結果已經證明：預設下 `sub` 被改寫成 `nameidentifier`，`User.Identity.Name` 是 `null`。`User.Identity.Name` 讀的是 `NameClaimType` 指定的 claim，預設名字對不上 token 裡的 `name`；要有值必須自己設 `NameClaimType`，且 token 要有那個 claim。實務後果：拿 `User.Identity.Name` 當使用者 id 去查資料庫，不會出錯，只是查不到。想拿使用者 id，明確讀 `sub`：`User.FindFirst("sub")?.Value`（需要 `MapInboundClaims = false`）。

---

## 七、角色與 Policy：Viewer、Editor、Admin

對應設定正確後，就能用角色限制端點。TaskTracker 的權限矩陣（來自 RuleViewer 的需求）：登入的人都能讀，Editor 與 Admin 可建立與修改，只有 Admin 可刪除。先把角色名稱收進常數，避免到處打字串：

```csharp
namespace TaskTracker.Api.Authorization;

public static class RoleNames
{
    public const string Viewer = "Viewer";
    public const string Editor = "Editor";
    public const string Admin = "Admin";
    public const string EditorOrAdmin = Editor + "," + Admin;
}
```

接著在 `TasksController` 加上限制。類別上的 `[Authorize]` 要求所有 action 都需要登入（所以現在連 `GET` 都要 token，與上一章不同），個別 action 再收緊：

```csharp
[ApiController]
[Authorize]
[Route("api/tasks")]
public class TasksController : ControllerBase
{
    // GET 兩個 action：沿用類別上的 [Authorize]，任何已登入的角色都能讀

    [Authorize(Roles = RoleNames.EditorOrAdmin)]
    [HttpPost]
    public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct)
    // ...

    [Authorize(Roles = RoleNames.EditorOrAdmin)]
    [HttpPut("{id:guid}")]
    public async Task<ActionResult<TaskResponse>> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct)
    // ...

    [Authorize(Roles = RoleNames.Admin)]
    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> DeleteAsync(Guid id, CancellationToken ct)
    // ...
}
```

用三個帳號各登入一次、各打一輪。沒帶 token 的 `GET` 先看：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks
```

```text
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
```

單純的 `Bearer` 沒有 `error=`，表示請求裡根本沒有憑證，與前面 `invalid_token` 的情況不同。接著是各角色的結果，每一格都是實際打出去的狀態碼：

| 身分 | 動作 | 狀態碼 |
| --- | --- | --- |
| 匿名 | `GET /api/tasks` | 401 |
| Viewer | `GET /api/tasks` | 200 |
| Viewer | `POST /api/tasks` | 403 |
| Viewer | `PUT /api/tasks/{id}` | 403 |
| Editor | `POST /api/tasks` | 201 |
| Editor | `PUT /api/tasks/{id}` | 200 |
| Editor | `DELETE /api/tasks/{id}` | 403 |
| Admin | `DELETE /api/tasks/{id}` | 204 |

Viewer 登入後讀取是 200，建立與更新是 403；Editor 建立、更新成功，刪除被擋；Admin 刪除成功。403 的回應內容是：

```text
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json; charset=utf-8

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.4","title":"Forbidden","status":403,"traceId":"00-77d708854fc230dbebee91177a242a52-f7e27ac7b7feeee3-00"}
```

沒有 `WWW-Authenticate` 標頭。Viewer 的 token 完全有效（`GET` 是 200），只是這個身分做不了這件事，這就是 [[basics-11-auth-concepts-and-pipeline]] 說的 401 與 403 的實例。

### 7.1 `Roles = "A,B"` 是 OR，疊 attribute 是 AND

一個很多人答錯的問題：`[Authorize(Roles = "Editor,Admin")]` 是「同時需要」還是「其中一個即可」？直覺上逗號像 and，實測相反。用五種身分各打一次：

| 寫法 | 匿名 | 無角色 | Editor | Admin | Editor 與 Admin |
| --- | --- | --- | --- | --- | --- |
| `Roles = "Editor,Admin"` | 401 | 403 | 200 | 200 | 200 |
| 疊兩個 attribute：`Roles = "Editor"` 加 `Roles = "Admin"` | 401 | 403 | 403 | 403 | 200 |
| policy `RequireRole("Editor", "Admin")` | 401 | 403 | 200 | 200 | 200 |
| policy `RequireRole("Editor").RequireRole("Admin")` | 401 | 403 | 403 | 403 | 200 |

單一 attribute 裡逗號分隔的角色是 OR；疊兩個 attribute 是 AND，因為每個 attribute 各自是一個要求，全部都要滿足。逗號後多一個空白不影響結果。類別上標 `Roles = "Editor"`、action 上標 `Roles = "Admin"` 也是 AND，action 的 attribute 不會取代類別的。TaskTracker 的 `RoleNames.EditorOrAdmin` 用的就是 OR。

### 7.2 角色寫在 token 裡的限制

角色放在 token 裡，簽發後到期前不會變：管理員把某人從 Editor 降成 Viewer，他手上那張 30 分鐘的舊 token 仍寫著 Editor，直到過期（再加 30 秒 `ClockSkew`）。降權不會立即生效，這是無狀態 token 的本質取捨，也是 access token 壽命要短的原因之一。

另一個限制是「角色」的粒度太粗。需求變成「Editor 可以改自己建立的任務」時，單靠 `Roles` 會爆炸成十幾個角色。解法是把授權從「你是什麼角色」改成「你有什麼權限」，用 permission claim 加具名 policy 表達，在 [[basics-13-permissions-with-frontend]] 做，機制見 [[14-authorization]]。

---

## 八、把整條路走一遍，再談 refresh token

所有零件都有了。下面的序列圖畫出一次「登入、然後呼叫 API」，並標出每個會失敗的位置：

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#eef2ff','primaryBorderColor':'#6366f1','actorBkg':'#eef2ff','actorBorder':'#6366f1','lineColor':'#94a3b8','signalColor':'#475569','noteBkgColor':'#f1f5f9'}}}%%
sequenceDiagram
    autonumber
    participant C as 前端或 curl
    participant A as TaskTracker API
    participant D as Oracle USERS

    C->>A: POST /api/auth/login (email, password)
    A->>D: 依 email 查 User
    D-->>A: User 或查無
    A->>A: VerifyHashedPassword
    alt 帳號不存在或密碼錯
        A-->>C: 401 Invalid email or password
    else 密碼正確
        A->>A: 以金鑰簽發 JWT (HS256)
        A-->>C: 200 accessToken, expiresIn
    end

    C->>A: DELETE /api/tasks/{id} + Authorization: Bearer token
    A->>A: UseAuthentication 驗簽章, iss, aud, exp
    alt 沒帶 token 或 token 無效
        A-->>C: 401 + WWW-Authenticate
    else token 有效
        A->>A: UseAuthorization 比對 endpoint 要求的角色
        alt 角色不符
            A-->>C: 403 Forbidden
        else 角色符合
            A-->>C: 204 No Content
        end
    end
```

圖中有三個地方拒絕請求，原因完全不同。第 5 步的 401 是「帳密不對」，發生在登入端點，這時系統還沒簽任何東西；第 10 步的 401 是「token 不對」，發生在 `UseAuthentication()`；第 12 步的 403 才是「你是誰我知道，但你不行」，發生在 `UseAuthorization()`。後兩處都不會執行 Controller 的任何一行程式碼。除錯時先看狀態碼是 401 還是 403，就已經排除了一半的可能。

### 8.1 Refresh token：為什麼需要，以及本章為什麼不做

這張圖還漏了一件事：access token 過期之後怎麼辦？每 30 分鐘叫使用者重輸密碼體驗很差；把壽命拉長到幾天，又因為 JWT 無狀態、伺服器簽出去就不記得它，token 被偷或使用者登出後，在 `exp` 以前它仍然有效，壽命越長損害窗口越大。

Refresh token 是折衷：登入時發兩個東西，壽命短（例如 30 分鐘）的 access token 用來呼叫 API，壽命長（例如 14 天）的 refresh token 只能換新的 access token。關鍵差異是 refresh token 存在伺服器端，可以撤銷：登出、改密碼或偵測到盜用時刪掉那筆記錄，損害最多持續到手上那張 access token 過期。

細節很多（refresh token 要雜湊後才存、每次換新要輪替、被重複使用時要整串作廢），做錯的後果也不小，所以 TaskTracker 在入門篇只做 access token。完整實作見 [[12-jwt-deep-dive]] 第六節，前端怎麼保存 token 見該章第七節與 [[basics-13-permissions-with-frontend]]。

---

## 常見誤解

**「JWT 的內容是加密過的，所以放什麼都安全。」** 第三節的實驗已經證明：payload 只是 Base64Url，任何人幾行程式就能讀。簽章保證的是內容沒被改過，不保證別人看不到。密碼、身分證字號、內部備註都不應該放進 claim。

**「`sub` 會自動變成 `User.Identity.Name`。」** 預設下 `sub` 被改寫成 `nameidentifier`，`User.Identity.Name` 是 `null`。想要 `Identity.Name` 有值，必須設 `NameClaimType` 並且 token 裡有對應的 claim；想要使用者 id，從 `sub` 讀。

**「`[Authorize(Roles = "Editor,Admin")]` 要同時是 Editor 又是 Admin。」** 逗號是 OR，疊兩個 attribute 才是 AND，實測 Editor 單獨就是 200。

**「把 `MapInboundClaims` 關掉，其他不用動。」** 關掉之後 `RoleClaimType` 還指著舊的長 URI，所有 `[Authorize(Roles = ...)]` 對所有人回 403，包括 token 明明有正確角色的人。這兩個設定要成對。

---

## 同事會來問你的問題

**Q：登入失敗時為什麼不告訴使用者是帳號錯還是密碼錯？這樣體驗不是比較差嗎？**
分開回報會讓攻擊者用 email 清單探測誰有帳號，再集中猜那些帳號的密碼。統一回 `Invalid email or password.`，使用者的損失很小，安全收益很大；回應時間也要接近，原因在 2.1 節。

**Q：使用者按「登出」，後端要做什麼？**
單靠 JWT，後端什麼都做不了：伺服器沒有記錄簽出去的 token，無法讓它提前失效，前端只能丟掉本機的 token。要讓登出真的有效，需要 refresh token 或 `jti` 黑名單這類有狀態的機制，見 [[12-jwt-deep-dive]] 第六節。

**Q：access token 壽命設多久？**
本書用 30 分鐘。判準是「token 被偷時你能接受的損害窗口」：越短越安全，但需要 refresh token 搭配，否則使用者會頻繁被登出。加上 30 秒 `ClockSkew`，實際最長壽命是 30 分 30 秒。

**Q：角色改了，使用者要多久才會生效？**
最長是舊 token 的剩餘壽命加 `ClockSkew`，使用者重新登入後才拿到新角色。需要「立即生效」的權限，要每次請求查資料庫，代價是失去 JWT 無狀態的優點。

---

## 這章的位置

讀完這一章，你能說出密碼為什麼存雜湊並用 `PasswordHasher<User>` 實作；寫出不洩漏帳號是否存在的登入端點；解開 JWT 並解釋 Base64 為什麼不是加密；簽發 token，知道 HS256 的金鑰門檻是 32 bytes；說明 `TokenValidationParameters` 每個欄位在擋什麼；正確設定 `MapInboundClaims` 與 `RoleClaimType`，並分辨 `Roles` 逗號與疊 attribute 的語意。TaskTracker 現在三個角色可以登入，依角色得到 200、201、403 或 204。想看簽章演算法、金鑰輪替與撤銷，讀 [[12-jwt-deep-dive]]；想看 Policy 與 Requirement，讀 [[14-authorization]]；[[basics-13-permissions-with-frontend]] 把角色轉成 permission，並讓 React 前端依權限顯示按鈕。

---

## 連結

- 上一章：[[basics-11-auth-concepts-and-pipeline]]
- 下一章：[[basics-13-permissions-with-frontend]]
- 對應深度章：[[12-jwt-deep-dive]]、[[14-authorization]]
- 總目錄：[[dotnet-web-api]]
