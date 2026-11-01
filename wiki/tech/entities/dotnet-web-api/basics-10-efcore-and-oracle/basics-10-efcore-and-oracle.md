---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, efcore, oracle, migration, dbcontext, docker-compose, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 7：EF Core 與資料存取設計.md
created: 2026-10-31
updated: 2026-10-31
---

# 入門第 10 章：EF Core 與 Oracle — 資料怎麼真的存進資料庫

## 重啟一次，三筆任務全沒了

前九章的 TaskTracker 有一個沒拿出來講的缺點：任務清單住在 `TaskService` 的一個集合裡，那個集合在行程的記憶體中。用 `curl.exe` 建立三筆任務，`GET` 看得到；按 `Ctrl+C` 再 `dotnet run`，再 `GET` 一次，`items` 是空的。前面的章節刻意不碰資料庫，專心學 Controller、DI、Middleware 與設定。但是資料撐不過一次重啟的 API，只是示範程式，沒有人敢把它當系統。

本章把它補成真的：`TaskService` 不再持有集合，改為透過 EF Core 讀寫 Oracle，API 對外的網址、DTO、狀態碼完全不變。順序是先用 Docker Compose 在本機跑一個 Oracle，再裝套件、寫 `DbContext` 與 entity 設定、用 migration 建表，然後把 `TaskService` 換成資料庫版，接著看兩種出錯情境（標題重複與資料庫連不上），最後談交易，以及兩種幾乎每個初學者都會寫的低效寫法。

起點是 [[basics-09-configuration-and-environments]] 結束時的 TaskTracker：設定分層、Options 與 User Secrets 都已就位，`ITaskService` 以 Singleton 註冊，實作是記憶體版。終點是同一支 API 背後接著 Oracle，重啟後資料還在。

機制推導不在本章重複：Change Tracker 見 [[07-efcore-internals]]，查詢翻譯見 [[08-efcore-query]]，交易與並發見 [[09-transactions-and-concurrency]]，Oracle 特有行為見 [[10-oracle-specifics]]。

## 一、先把資料庫跑起來

EF Core 是 ORM（Object-Relational Mapper），不自帶資料庫，所以先要有一個 Oracle 可連。公司的開發用 Oracle 通常由 DBA 提供；在自己的機器上，最省事的是用容器（本機要先裝好 Docker Desktop 或其他能執行 `docker compose` 的環境）。本書用社群維護的 `gvenzl/oracle-free` 映像（Oracle Database 23ai Free）。`23-slim-faststart` 這個 tag 的 `slim` 去掉不常用的元件，`faststart` 預先建好資料庫檔案，啟動時不必從頭初始化。

TaskTracker 的 `compose.yaml` 放在 repo 根目錄：

```yaml
name: tasktracker

services:
  oracle:
    image: gvenzl/oracle-free:23-slim-faststart
    container_name: tasktracker-oracle
    ports:
      - "1521:1521"
    environment:
      ORACLE_PASSWORD: ${ORACLE_PASSWORD:?請先設定環境變數 ORACLE_PASSWORD}
      APP_USER: tasktracker
      APP_USER_PASSWORD: ${APP_USER_PASSWORD:?請先設定環境變數 APP_USER_PASSWORD}
    healthcheck:
      test: ["CMD", "healthcheck.sh"]
      interval: 10s
      timeout: 5s
      retries: 30
      start_period: 30s
```

這份檔案有三處值得停下來看。第一，密碼不寫在檔案裡。`${ORACLE_PASSWORD:?訊息}` 是 Compose 的語法：環境變數有值就代入，沒有值就中止並印出冒號後面的訊息。這樣 `compose.yaml` 可以放心進 git，而忘了設定密碼時得到的是一個明確的錯誤，不是一個密碼為空的資料庫。實際的行為如下：

```powershell
docker compose config --quiet
```

```text
error while interpolating services.oracle.environment.APP_USER_PASSWORD: required variable APP_USER_PASSWORD is missing a value: 請先設定環境變數 APP_USER_PASSWORD
```

第二，`ORACLE_PASSWORD` 是資料庫管理者（SYS、SYSTEM）的密碼，`APP_USER` 與 `APP_USER_PASSWORD` 則讓映像在第一次啟動時額外建立一個應用程式專用的使用者。API 應該用後者連線，不用管理者帳號。在 Oracle，schema 就是使用者，`tasktracker` 擁有的資料表就在 `TASKTRACKER` schema（見 [[10-oracle-specifics]]）。

第三，`healthcheck` 讓 Compose 知道容器何時「真的可以連」：行程啟動不代表資料庫已接受連線。`start_period: 30s` 表示前 30 秒的失敗不計入重試次數，搭配 `docker compose up -d --wait`，指令會等到健康檢查通過才返回。

在 PowerShell 裡設定兩個密碼（換成自己的值，這兩個值不進版本控制）並啟動：

```powershell
$env:ORACLE_PASSWORD = "<管理者密碼>"
$env:APP_USER_PASSWORD = "<應用程式使用者密碼>"
docker compose up -d --wait
```

```text
 Network tasktracker_default  Creating
 Network tasktracker_default  Created
 Container tasktracker-oracle  Creating
 Container tasktracker-oracle  Created
 Container tasktracker-oracle  Starting
 Container tasktracker-oracle  Started
 Container tasktracker-oracle  Waiting
 Container tasktracker-oracle  Healthy
```

這些輸出走標準錯誤，有些終端機會標成紅字，屬正常；第一次執行還要先下載映像，上面是映像已在本機的畫面。用 `docker compose ps` 看到 `(healthy)` 才算好。從這一刻起，連線位址是 `localhost:1521`，服務名稱（service name）是 `FREEPDB1`，使用者是 `tasktracker`。Oracle 23ai Free 把應用程式資料放在名為 `FREEPDB1` 的 pluggable database，連線時必須指定它。

## 二、套件與 `dotnet-ef`

連 Oracle 需要 provider，也就是 EF Core 與特定資料庫之間的翻譯層。Oracle 官方的套件是 `Oracle.EntityFrameworkCore`，它的主版本號對應 EF Core 的主版本：8.21.x 對 EF Core 8，9.23.x 對 EF Core 9，10.23.x 對 EF Core 10。本書基準是 .NET 10，所以裝 10.23 這一條：

```powershell
dotnet add src/TaskTracker.Api package Oracle.EntityFrameworkCore --version 10.23.26400
```

```text
warn : NU1903: Package 'System.Security.Cryptography.Pkcs' 8.0.1 has a known high severity vulnerability, https://github.com/advisories/GHSA-846f-f764-76mx
```

第一行是警告，不是錯誤，但不能忽略。它的意思是：這個套件帶進了有已知弱點的相依套件。查是誰帶進來的：

```powershell
dotnet nuget why src/TaskTracker.Api System.Security.Cryptography.Pkcs
```

```text
Oracle.EntityFrameworkCore (v10.23.26400)
└── Oracle.ManagedDataAccess.Core (v23.26.400)
    └── System.Security.Cryptography.Pkcs (v8.0.1)
```

這是遞移相依（transitive dependency）：你沒有直接要它，是 Oracle 驅動 `Oracle.ManagedDataAccess.Core` 要它。NuGet 的規則是直接相依優先於遞移相依，所以在自己的專案直接參考已修補的版本即可：

```powershell
dotnet add src/TaskTracker.Api package System.Security.Cryptography.Pkcs --version 10.0.14
```

再執行 `dotnet list src/TaskTracker.Api package --vulnerable --include-transitive`，輸出 `has no vulnerable packages given the current sources`，警告消失。

下一個套件是 `Microsoft.EntityFrameworkCore.Design`：

```powershell
dotnet add src/TaskTracker.Api package Microsoft.EntityFrameworkCore.Design --version 10.0.14
```

這個套件只有 `dotnet ef` 在設計階段（建 migration、產生 script）才需要，所以 `.csproj` 裡它帶著 `PrivateAssets="all"`，不會傳給參考此專案的其他專案。

最後是 `dotnet ef` 指令列工具。常見教法是 `dotnet tool install --global dotnet-ef`，但團隊開發時全域工具會造成版本漂移：兩位同事的版本不同，產生的 migration 與 model snapshot 可能有與功能無關的 diff。更穩當的做法是裝成 local tool，版本寫進 repo 裡的 tool manifest（`dotnet-tools.json`，`dotnet new tool-manifest` 建立），所有人與 CI 用同一版：

```powershell
dotnet new tool-manifest
dotnet tool install dotnet-ef --version 10.0.14
```

之後新同事 clone 專案，只要執行一次 `dotnet tool restore` 就拿到相同版本的工具。`dotnet-ef` 的版本號與 `Microsoft.EntityFrameworkCore.Design` 保持一致（這裡都是 10.0.14），可以避免工具與專案對 EF Core 內部格式的認知不同。

## 三、DbContext 與 entity 設定

套件到位後要寫兩樣東西：`DbContext`，以及告訴 EF Core 每個 entity 如何對應到資料表的設定。entity 本身 `TaskItem`（`Id`、`Title`、`Status`、`CreatedAt` 四個屬性）在 [[basics-06-dto-design]] 就已存在，沒有改動。

`DbContext` 是 EF Core 的核心物件，代表「與資料庫的一次工作階段」。它做幾件事：管理連線、追蹤你載入的物件有沒有被改過（Change Tracker）、產生並執行 SQL、在 `SaveChanges` 時把變更寫回去。`AppDbContext` 的寫法很精簡：

```csharp
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    public DbSet<TaskItem> TaskItems => Set<TaskItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}
```

建構函式接收 `DbContextOptions<AppDbContext>`，裡面裝著「用哪個 provider、連線字串是什麼」，由 DI 在註冊時填好，`DbContext` 不必知道連線字串從哪來。`DbSet<TaskItem>` 代表資料表，對它做 LINQ 查詢就是查表，對它呼叫 `Add` 就是準備新增一列。

`OnModelCreating` 只有一行，是刻意的。對應設定可以全寫在這個方法裡，但 entity 一多就會膨脹成幾百行。`IEntityTypeConfiguration<T>` 讓每個 entity 有自己的設定類別，`ApplyConfigurationsFromAssembly` 自動找出並套用。以後新增 entity 只需新增一個設定檔，`AppDbContext` 不必動：

```csharp
publicclass TaskItemConfiguration : IEntityTypeConfiguration<TaskItem>
{
    public void Configure(EntityTypeBuilder<TaskItem> builder)
    {
        builder.ToTable("TASK_ITEMS");

        builder.HasKey(t => t.Id);
        builder.Property(t => t.Id).HasColumnName("ID").ValueGeneratedNever();
        builder.Property(t => t.Title).HasColumnName("TITLE").HasMaxLength(100).IsRequired();
        builder.Property(t => t.Status).HasColumnName("STATUS").HasConversion<string>().HasMaxLength(16).IsRequired();
        builder.Property(t => t.CreatedAt).HasColumnName("CREATED_AT").IsRequired();

        builder.HasIndex(t => t.Title).IsUnique().HasDatabaseName("UX_TASK_ITEMS_TITLE");
    }
}
```

設定檔的每一行都是一個決定。`ValueGeneratedNever()` 表示主鍵由程式產生（`CreateAsync` 直接 `Guid.NewGuid()`），不是資料庫產生，新增後不必再問資料庫剛才那筆的 id。

`HasMaxLength(100)` 與 [[basics-05-model-binding-and-validation]] 裡 DTO 的長度驗證一致，兩邊各擋一次：DTO 驗證讓使用者在請求階段就得到 400，資料庫限制是最後防線，即使有人繞過 API 直接寫資料也不會越界。不設長度的話，EF Core 對 Oracle 的 `string` 預設建成 `NVARCHAR2(2000)`，那是一個沒有人決定過的上限。

`HasConversion<string>()` 讓 enum 以名稱（`Todo`、`Done`）存進資料庫，不以整數存。用 SQL 查表的人看得懂 `Done`，看不懂 `1`；enum 成員重新排序或在中間插入新值時，整數會悄悄變成另一個意思，名稱不會。代價是成員改名就是破壞性變更。資料庫存 `Todo`，API 回應卻是 `todo`，因為 JSON 另用 `JsonStringEnumMemberName` 指定對外名稱，兩者是獨立的對應。

`HasIndex(...).IsUnique()` 為 `TITLE` 建立唯一索引，「標題不能重複」這條規則在資料庫層也有一份。為什麼不只在 `TaskService` 檢查就好，第八節會用 ORA-00001 說明。

## 四、為什麼表名是 `TASK_ITEMS`：Oracle 的引號

上面的設定檔把表名、欄名全部寫成大寫加底線（`TASK_ITEMS`、`CREATED_AT`），這與 C# 的 PascalCase 習慣不同，不是個人偏好，而是 Oracle 的規則造成的。

Oracle 對沒有加雙引號的識別字（表名、欄名）一律轉成大寫：`select title from task_items` 會被當作 `SELECT TITLE FROM TASK_ITEMS`。可是 EF Core 產生的 SQL 一律替識別字加雙引號，加了引號的名稱大小寫敏感。entity 若完全用預設命名，EF Core 會建出叫 `"LabTaskItems"` 的表與 `"Title"` 欄。EF Core 自己查沒有問題，出問題的是 DBA、報表工具與 ETL 作業，它們通常寫不加引號的 SQL。以下在同一個 schema 裡用預設命名建一張表（`LabTaskItems`）、用大寫蛇形命名建另一張表（`LAB_TASK_ITEMS`），再以不經過 EF Core 的 SQL 查詢：

```text
select count(*) from LabTaskItems => ORA-00942: table or view "TASKTRACKER"."LABTASKITEMS" does not exist
select title from "LabTaskItems" => ORA-00904: "TITLE": invalid identifier
select "Title" from "LabTaskItems" => 成功
select title from lab_task_items => 成功
```

預設命名的那張表，每一個識別字都必須照原樣加引號才查得到，漏掉一個就是 ORA-00942（找不到表）或 ORA-00904（找不到欄）。大寫命名的表，加不加引號都查得到。所以 TaskTracker 的決定是：表、欄、索引一律大寫蛇形命名，用 `IEntityTypeConfiguration` 明確寫出來。

這裡有兩個容易想當然耳的地方。其一，PostgreSQL 圈常用的小寫蛇形命名（`task_items`）搬到 Oracle 沒有用：小寫的名稱在 Oracle 裡一樣是需要加引號的大小寫敏感名稱。其二，本專案只有一個 entity，明確寫出來容易搜尋也容易審查；entity 變多時再改成在 `OnModelCreating` 走訪 model 統一轉換也不遲（見 [[10-oracle-specifics]] 的識別碼大小寫一節）。

另外兩個對應也值得知道。`Guid` 在 Oracle 預設存成 `RAW(16)`，只佔 16 位元組，但 SQL 工具看到的十六進位和 `Guid.ToString()` 不同：前三組是 .NET 的小端序。`00112233-4455-6677-8899-aabbccddeeff` 在資料庫裡是 `33221100554477668899AABBCCDDEEFF`，照字串順序寫 `where id = hextoraw('00112233...')` 會查到 0 筆。團隊若無法接受，替代方案是 `HasConversion<string>()` 存成 `VARCHAR2(36)`，可讀但索引較大；TaskTracker 維持 `RAW(16)`。另外，`NVARCHAR2(100)` 在資料字典的 `data_length` 會顯示 200，因為它以 UTF-16 存放，每個字元 2 位元組，不是設定錯誤。

## 五、連線字串走設定，不寫死

`UseOracle(...)` 需要連線字串，而它包含密碼。規則只有一條：不寫在程式碼裡，也不放進進版控的 `appsettings.json`。[[basics-09-configuration-and-environments]] 已鋪好路：用 Options 類別接設定，開發時放 User Secrets，部署時放環境變數或 Secret。

```csharp
publicclass ConnectionStringOptions
{
    public const string SectionName = "ConnectionStrings";

    [Required]
    public string Default { get; init; } = string.Empty;
}
```

反面的做法是把整串連線字串寫進 `appsettings.json`，或直接寫成 `UseOracle("User Id=tasktracker;Password=...")`。這種寫法一旦 commit，密碼就進了 git 歷史，刪掉也還查得到，只能換密碼。用 Options 接，進版控的檔案裡就只有欄位名稱，沒有值。

註冊時用 `AddOptions<ConnectionStringOptions>().BindConfiguration(...).ValidateDataAnnotations().ValidateOnStart()`。`ValidateOnStart()` 把檢查提前到應用程式啟動時。少了它，忘記設定連線字串的後果要等到第一個請求碰到資料庫才爆，而且是難以辨認的連線錯誤；有了它，啟動即失敗，訊息直接指出 `Default` 欄位是必填。

接著是 `AddDbContext`。TaskTracker 把它包成擴充方法：

```csharp
public static IServiceCollection AddTaskTrackerDatabase(this IServiceCollection services)
{
    services.AddDbContext<AppDbContext>((serviceProvider, options) =>
    {
        var connectionString = serviceProvider.GetRequiredService<IOptions<ConnectionStringOptions>>().Value.Default;
        options.UseOracle(connectionString);
    });
    return services;
}
```

這個多載的 lambda 拿得到 `serviceProvider`，能從 DI 取出已驗證的 Options。直接用 `builder.Configuration.GetConnectionString("Default")` 也能跑，但繞過了 Options 的驗證。`Program.cs` 只多兩行：`builder.Services.AddTaskTrackerDatabase();` 與稍後說明的 `await app.InitializeDatabaseAsync();`。

開發機上把連線字串放進 User Secrets（`UserSecretsId` 在 [[basics-09-configuration-and-environments]] 已經設好）：

```powershell
dotnet user-secrets set "ConnectionStrings:Default" "User Id=tasktracker;Password=<APP_USER_PASSWORD>;Data Source=localhost:1521/FREEPDB1" --project src/TaskTracker.Api
```

`Data Source=主機:埠/服務名稱` 是 Oracle 的 Easy Connect 寫法，不需要 `tnsnames.ora`，在容器與 K8s 環境是首選。`<APP_USER_PASSWORD>` 要與 Compose 用的是同一個值。等價的做法是環境變數 `ConnectionStrings__Default`（雙底線代表設定階層的冒號），容器部署用這種形式。

## 六、Migration：把 C# model 變成資料表

`DbContext` 寫好了，資料庫裡卻還沒有 `TASK_ITEMS`。把 model 的變化同步到資料庫，EF Core 的機制叫 migration：每次 model 改變，就產生一個「從上一個狀態到這個狀態」的 C# 檔案描述 DDL；資料庫裡的 `__EFMigrationsHistory` 表記錄哪些 migration 已套用；套用時只執行還沒記錄的。schema 的演進因此也有歷史、能進版控。

建立第一個 migration：

```powershell
dotnet build
dotnet ef migrations add InitialCreate --project src/TaskTracker.Api --output-dir Data/Migrations
```

```text
Build started...
Build succeeded.
Done. To undo this action, use 'ef migrations remove'
```

`--output-dir` 讓檔案落在 `Data/Migrations`。產生三個檔案：

```text
20261030143404_InitialCreate.cs
20261030143404_InitialCreate.Designer.cs
AppDbContextModelSnapshot.cs
```

檔名開頭的數字是時間戳記，保證 migration 的套用順序。三個檔案各有分工。主檔 `InitialCreate.cs` 是你會閱讀與審查的，裡面有 `Up`（往前）與 `Down`（回退）：

```csharp
protected override void Up(MigrationBuilder migrationBuilder)
{
    migrationBuilder.CreateTable(
        name: "TASK_ITEMS",
        columns: table => new
        {
            ID = table.Column<Guid>(type: "RAW(16)", nullable: false),
            TITLE = table.Column<string>(type: "NVARCHAR2(100)", maxLength: 100, nullable: false),
            STATUS = table.Column<string>(type: "NVARCHAR2(16)", maxLength: 16, nullable: false),
            CREATED_AT = table.Column<DateTimeOffset>(type: "TIMESTAMP(7) WITH TIME ZONE", nullable: false)
        },
        constraints: table =>
        {
            table.PrimaryKey("PK_TASK_ITEMS", x => x.ID);
        });

    migrationBuilder.CreateIndex(
        name: "UX_TASK_ITEMS_TITLE",
        table: "TASK_ITEMS",
        column: "TITLE",
        unique: true);
}

protected override void Down(MigrationBuilder migrationBuilder)
{
    migrationBuilder.DropTable(
        name: "TASK_ITEMS");
}
```

可以在這裡驗證上一節的設定：表名欄名是大寫，`TITLE` 是 `NVARCHAR2(100)`，`Guid` 是 `RAW(16)`。`Designer.cs` 帶著這個 migration 當下的 model 描述，給 EF Core 內部使用。`AppDbContextModelSnapshot.cs` 是目前最新 model 的樣子，下次 `migrations add` 時 EF Core 用它和現在的 model 比對出差異。這兩個檔案都不要手動編輯。

在把 migration 打到資料庫之前，先看它會產生什麼 SQL。這是 DBA 審查時要看的東西，而且不需要連資料庫：

```powershell
dotnet ef migrations script --idempotent --project src/TaskTracker.Api --no-build
```

`--idempotent`（冪等）表示這份 script 可重複執行，套用過的 migration 會被跳過，所以能交給 DBA 在各環境執行，不必先確認該環境停在哪個版本。

要套用到資料庫，有兩條路：執行 `dotnet ef database update`，或者在程式裡呼叫 `Database.MigrateAsync()`。兩者最終走的是同一個 migrator，做的事情相同。TaskTracker 在開發環境採用後者，讓 `dotnet run` 啟動時就自動建表：

```csharp
public static async Task InitializeDatabaseAsync(this WebApplication app)
{
    if (!app.Services.GetRequiredService<IOptions<DatabaseOptions>>().Value.MigrateOnStartup)
    {
        return;
    }

    await using var scope = app.Services.CreateAsyncScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.MigrateAsync();
}
```

因為 `DbContext` 是 Scoped，而應用程式啟動時沒有任何 HTTP 請求（也就沒有請求範圍），所以必須自己用 `CreateAsyncScope()` 開一個範圍再取出 `DbContext`。

自動 migrate 由 `Database:MigrateOnStartup` 這個旗標控制。它對應一個簡單的 Options 類別，註冊方式和 `ConnectionStringOptions` 相同（不需要驗證，預設值 `false` 就是安全的選擇）：

```csharp
publicclass DatabaseOptions
{
    public const string SectionName = "Database";

    public bool MigrateOnStartup { get; init; }
}
```

旗標只在 `appsettings.Development.json` 開啟，`Program.cs` 在 `builder.Build()` 之後、`app.Run()` 之前呼叫 `await app.InitializeDatabaseAsync();`：

```json
"Database": {
  "MigrateOnStartup": true
}
```

為什麼只在開發環境開？正式環境通常不只一個副本，多個副本同時啟動就會搶著改 schema；Oracle 的 DDL 又是隱含提交的，migration 中途失敗無法整段回滾。正式環境的做法是把 `migrations script --idempotent` 產生的 SQL 交給 DBA 審查執行，或在部署流程用獨立 job 跑 migration，見 [[10-oracle-specifics]] 的 Migration 一節與 [[21-deployment]]。

同一個 `appsettings.Development.json` 還多開了一行：

```json
"Microsoft.EntityFrameworkCore.Database.Command": "Information"
```

這個類別名稱讓 EF Core 把每一個送給資料庫的 SQL 都印在 console。第一次啟動時，`MigrateAsync` 做了什麼從 log 一目了然：

```text
Applying migration '20261030143404_InitialCreate'.
CREATE TABLE "TASK_ITEMS" (...)
CREATE UNIQUE INDEX "UX_TASK_ITEMS_TITLE" ON "TASK_ITEMS" ("TITLE")
INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion") VALUES (N'20261030143404_InitialCreate', N'10.0.14')
```

順序是：確認（必要時建立）歷史表、讀出已套用的 migration、對還沒套用的執行 DDL，最後在歷史表寫入一列。這一列就是下次啟動時「已經做過了」的證據。

## 七、把 Service 從記憶體換成資料庫

資料表建好之後，終於可以動 `TaskService`。這一節有三個決定：lifetime 要改；每個方法要變成 async 並傳遞 `CancellationToken`；讀取與寫入用不同的 EF Core 用法。

### 7.1 Singleton 改 Scoped

記憶體版的 `ITaskService` 是 Singleton，因為它要持有那個集合，整個應用程式只能有一份。換成資料庫版之後，`TaskService` 的建構函式會注入 `AppDbContext`，而 `AddDbContext` 預設把 `DbContext` 註冊成 Scoped：每個 HTTP 請求一個實例，請求結束就釋放。

```csharp
public static IServiceCollection AddTaskTrackerServices(this IServiceCollection services)
{
    services.AddSingleton(TimeProvider.System);
    services.AddScoped<ITaskService, TaskService>();
    return services;
}
```

只改了一個字，理由來自 [[basics-07-dependency-injection-and-services]] 的規則：長壽命的服務不能依賴短壽命的服務。`TaskService` 若還是 Singleton，它拿到的 `AppDbContext` 會被一直握著，整個應用程式共用同一個 `DbContext`。`DbContext` 不是執行緒安全的，Change Tracker 還會累積所有請求載入過的物件。這種錯誤不一定立刻現形：Development 預設開啟 scope 驗證，`Build()` 階段就丟例外；Production 預設不驗證，會靜默通過，直到流量變大才出現難以重現的並發錯誤（實測見 [[02-dependency-injection]]）。看到 `AddDbContext`，就該同步檢查依賴它的服務是不是至少 Scoped。`TimeProvider.System` 沒有狀態，維持 Singleton。

### 7.2 Async 與 CancellationToken

資料庫呼叫是 I/O。同步呼叫讓執行緒站著等 Oracle 回應；非同步呼叫則讓出執行緒，回應到了再由任何可用的執行緒接手。同時處理許多請求時，這決定執行緒夠不夠用（機制見 [[06-async-and-threading]]）。所以碰資料庫的方法一律用 `Async` 版本並一路 `await`，不用 `.Result` 或 `.Wait()`。

`CancellationToken ct` 從 Controller 的 action 一路傳到 `ToListAsync(ct)`、`SaveChangesAsync(ct)`。model binding 會把這個型別的參數綁到「請求被中止」的訊號：使用者關掉分頁或呼叫端逾時斷線時，進行中的資料庫呼叫就被取消，不再占著連線。

### 7.3 讀取：`AsNoTracking`

先看列表：

```csharp
public async Task<PagedResponse<TaskResponse>> ListAsync(TaskListQuery query, CancellationToken ct)
{
    var pageSize = query.PageSize ?? _pagination.DefaultPageSize;
    var tasks = _db.TaskItems.AsNoTracking();
    if (query.Status is { } status)
    {
        tasks = tasks.Where(t => t.Status == status);
    }

    var totalCount = await tasks.CountAsync(ct);
    var page = await tasks
        .OrderBy(t => t.CreatedAt)
        .ThenBy(t => t.Id)
        .Skip((query.Page - 1) * pageSize)
        .Take(pageSize)
        .ToListAsync(ct);
    return new PagedResponse<TaskResponse>(page.Select(t => t.ToResponse()).ToList(), query.Page, pageSize, totalCount);
}
```

`AsNoTracking()` 之後接的 `Where`、`OrderBy`、`Skip`、`Take` 都不會馬上查資料庫，只是在累積查詢描述（`IQueryable`）；`CountAsync` 與 `ToListAsync` 這類「把結果拿出來」的呼叫才送出 SQL。所以這段程式送兩條 SQL，一條算總數，一條取這一頁，過濾與排序都在資料庫完成。伺服器 console 看到的是：

```text
info: Microsoft.EntityFrameworkCore.Database.Command[20101]
      Executed DbCommand (3ms) [Parameters=[], CommandType='Text', CommandTimeout='0']
      SELECT COUNT(*)
      FROM "TASK_ITEMS" "t"
info: Microsoft.EntityFrameworkCore.Database.Command[20101]
      Executed DbCommand (30ms) [Parameters=[:p_p='?' (DbType = Int32), :p_p1='?' (DbType = Int32)], CommandType='Text', CommandTimeout='0']
      SELECT "t"."ID", "t"."CREATED_AT", "t"."STATUS", "t"."TITLE"
      FROM "TASK_ITEMS" "t"
      ORDER BY "t"."CREATED_AT", "t"."ID"
      OFFSET :p_p ROWS FETCH NEXT :p_p1 ROWS ONLY
```

`ORDER BY "t"."CREATED_AT", "t"."ID"` 是 `OrderBy().ThenBy()` 的結果。排序一定要有，而且要有一個能唯一決定順序的欄位當最後的決勝：分頁靠 `OFFSET` 跳過前面幾列，如果排序欄位有重複值，同一筆資料可能在第 1 頁和第 2 頁各出現一次，或兩頁都漏掉，所以用 `CREATED_AT` 加 `ID`。`OFFSET ... FETCH NEXT` 是 Oracle 12c 以後的分頁語法，EF Core 的 Oracle provider 自動產生。

`AsNoTracking()` 是這一節的重點。EF Core 預設會追蹤每個查出來的 entity：存一份載入當下的快照，`SaveChanges` 時逐一比對，找出被改過的屬性來產生 UPDATE。追蹤要花記憶體與 CPU。列表與單筆查詢這類「讀完轉成 DTO 回傳」的路徑不會把物件改完再存回，追蹤純粹是浪費。判準只有一個：查出來的物件會不會被修改並存回？不會就加 `AsNoTracking()`。機制見 [[07-efcore-internals]]。

單筆查詢也是同樣的道理：

```csharp
public async Task<TaskResponse> GetByIdAsync(Guid id, CancellationToken ct)
{
    var task = await _db.TaskItems.AsNoTracking().FirstOrDefaultAsync(t => t.Id == id, ct)
        ?? throw new NotFoundException("Task", id);
    return task.ToResponse();
}
```

`FirstOrDefaultAsync` 找不到時回傳 `null`，這裡接著丟 `NotFoundException`，由 [[basics-08-middleware-and-exception-handling]] 做好的 `DomainExceptionHandler` 轉成 404 的 ProblemDetails。Service 不認識 HTTP，只負責說「找不到」。對應的 SQL 結尾是 `FETCH FIRST 1 ROWS ONLY`，這是 Oracle 版的 `LIMIT 1`。

`WHERE "t"."ID" = :p_id` 裡的 id 是以參數傳給資料庫，不是拼進 SQL 字串。這是 EF Core 預設防 SQL injection 的原因，也讓 Oracle 能重用執行計畫。

### 7.4 寫入：Add、修改屬性、SaveChanges

新增：

```csharp
public async Task<TaskResponse> CreateAsync(CreateTaskRequest request, CancellationToken ct)
{
    var title = request.Title.Trim();
    await EnsureTitleIsUniqueAsync(title, exceptId: null, ct);
    var task = new TaskItem
    {
        Id = Guid.NewGuid(),
        Title = title,
        Status = TaskItemStatus.Todo,
        CreatedAt = _timeProvider.GetUtcNow()
    };
    _db.TaskItems.Add(task);
    await SaveChangesAsync(title, ct);
    return task.ToResponse();
}
```

`_db.TaskItems.Add(task)` 沒有碰資料庫，它只是告訴 Change Tracker：「這個物件是新的，下次存檔時要 INSERT」。真正的 INSERT 在 `SaveChangesAsync` 才送出。這是 EF Core 的工作單元（unit of work）模式：你在記憶體裡累積一批變更，最後一次寫入。

更新的寫法看起來更不像資料庫操作：

```csharp
public async Task<TaskResponse> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct)
{
    var task = await _db.TaskItems.FirstOrDefaultAsync(t => t.Id == id, ct)
        ?? throw new NotFoundException("Task", id);
    var title = request.Title.Trim();
    await EnsureTitleIsUniqueAsync(title, exceptId: id, ct);
    task.Title = title;
    task.Status = request.Status!.Value;
    await SaveChangesAsync(title, ct);
    return task.ToResponse();
}
```

這裡查詢沒有 `AsNoTracking()`，因為要改它。程式只改屬性，沒有任何「更新」呼叫；`SaveChangesAsync` 時 Change Tracker 拿現在的值和載入當下的快照比對，有變才產生 UPDATE。實測把一筆任務的 `status` 從 `todo` 改成 `done`、標題不變，送出的 SQL 是：

```text
Executed DbCommand (7ms) [Parameters=[:ocnt0='?' (Direction = Output) (DbType = Int32), :pu0_0='?', :pc0_0='?' (DbType = Binary)], CommandType='Text', CommandTimeout='0']
BEGIN
  UPDATE "TASK_ITEMS" SET "STATUS" = :pu0_0
  WHERE "ID" = :pc0_0;
  :ocnt0 := SQL%ROWCOUNT;
END;
```

`SET` 裡只有 `STATUS`，因為標題沒變。這是 Change Tracker 的工作，也是更新路徑不能加 `AsNoTracking()` 的原因：沒有快照可比，改了屬性也不會有 UPDATE。

刪除則換了一種做法：

```csharp
public async Task DeleteAsync(Guid id, CancellationToken ct)
{
    var deleted = await _db.TaskItems.Where(t => t.Id == id).ExecuteDeleteAsync(ct);
    if (deleted == 0)
    {
        throw new NotFoundException("Task", id);
    }
}
```

`ExecuteDeleteAsync`（EF Core 7 起）不載入 entity、不經過 Change Tracker，直接送一條 `DELETE ... WHERE` 並回傳受影響的列數。刪一筆沒必要先查再刪；回傳 0 代表 id 不存在，直接對應 404。實測重複刪除同一個 id，第一次 `204 No Content`，第二次 `404 Not Found`。

換成資料庫版本之後，對外行為應該一模一樣。啟動 API 後用 `curl.exe` 建立一筆任務：

```powershell
'{"title":"Write chapter 10"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 201 Created
Location: http://localhost:5080/api/tasks/a8f845e2-dbc6-41ca-a47c-d3e6bb1e0848

{"id":"a8f845e2-dbc6-41ca-a47c-d3e6bb1e0848","title":"Write chapter 10","status":"todo","createdAt":"2026-10-30T14:36:26.6763444+00:00"}
```

回應與記憶體版的格式完全相同。再建兩筆之後，用 `curl.exe "http://localhost:5080/api/tasks?page=2&pageSize=2"` 查第 2 頁、每頁 2 筆：回應的 `items` 只有一筆，`page` 是 2，`totalCount` 是 3：三筆資料、每頁兩筆，第二頁剩一筆。到這一步，重啟 API 之後資料還在，因為它們在 Oracle 裡，不在行程裡。

## 八、標題重複：ORA-00001 如何變成 409

TaskTracker 的規格說同一個標題不能出現兩次，違反時回 409 Conflict。記憶體版只需要在集合裡找；資料庫版需要想得更仔細，因為有兩個人可能同時送出相同的標題。

第一道防線在 Service：寫入之前先查一次標題有沒有重複。

```csharp
private async Task EnsureTitleIsUniqueAsync(string title, Guid? exceptId, CancellationToken ct)
{
    var sameTitle = _db.TaskItems.Where(t => t.Title == title);
    if (exceptId is { } id)
    {
        sameTitle = sameTitle.Where(t => t.Id != id);
    }

    if (await sameTitle.AnyAsync(ct))
    {
        throw new ConflictException($"A task titled '{title}' already exists.");
    }
}
```

對應的 SQL 只問「存不存在」，不撈資料：

```text
SELECT CASE
    WHEN EXISTS (
        SELECT 1
        FROM "TASK_ITEMS" "t"
        WHERE "t"."TITLE" = :p_title) THEN True
    ELSE False
END FROM DUAL
```

重複時，使用者拿到清楚的訊息：

```text
HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.10","title":"Conflict","status":409,"detail":"A task titled 'Write chapter 10' already exists.","traceId":"00-bbce35d53484bb8d48d24cad1780be82-55a27cdb5189618d-00"}
```

這個檢查擋得住絕大多數重複，但擋不住並發：兩個標題相同的請求同時進來，兩邊都先查到「不存在」，兩邊都通過，然後都 INSERT。「先查再寫」在並行時不是原子操作，能保證唯一的只有資料庫，這就是第三節建唯一索引 `UX_TASK_ITEMS_TITLE` 的原因。繞過 Service 直接塞一筆重複標題會看到：

```text
insert into task_items (id, title, status, created_at) values (sys_guid(), 'Learn Oracle quoting rules', 'Todo', systimestamp)
*
ERROR at line 1:
ORA-00001: unique constraint (TASKTRACKER.UX_TASK_ITEMS_TITLE) violated on table TASKTRACKER.TASK_ITEMS columns (TITLE)
```

ORA-00001 是「違反唯一約束」的錯誤碼。在並發的空隙裡，輸的請求會在 `SaveChangesAsync` 拿到它；不處理的話它以 `DbUpdateException` 變成 500，但這是使用者資料的衝突，不是伺服器壞了，應該同樣是 409。所以 `SaveChangesAsync` 被包成私有方法：

```csharp
private async Task SaveChangesAsync(string title, CancellationToken ct)
{
    try
    {
        await _db.SaveChangesAsync(ct);
    }
    catch (DbUpdateException exception) when (exception.IsUniqueConstraintViolation())
    {
        throw new ConflictException($"A task titled '{title}' already exists.");
    }
}
```

判斷「是不是唯一約束違反」放在一個擴充方法，不在 Service 裡散落各處：

```csharp
public static class DbUpdateExceptionExtensions
{
    private const int OraUniqueConstraintViolated = 1;

    public static bool IsUniqueConstraintViolation(this DbUpdateException exception)
    {
        return exception.InnerException is OracleException { Number: OraUniqueConstraintViolated };
    }
}
```

真正的原因在 `DbUpdateException` 的 `InnerException`，是驅動丟出的 `OracleException`，用 `Number` 比對錯誤碼 1。用錯誤碼不用訊息文字，因為訊息會隨資料庫語言與版本變化。`when` 子句讓其他的 `DbUpdateException`（例如別的約束、連線中斷）不被吞掉。

兩道防線各有分工：預先檢查給大多數情況一個便宜、訊息清楚的答案，唯一索引加 `catch` 則保證並發下結果也正確。只留預先檢查，並發時會寫入重複資料；只留索引，單一使用者輸入重複標題也要吃一次失敗的 INSERT 與例外成本。

順帶一提，同樣的實測還看到 Oracle 的另一個行為：空字串等於 NULL。對 `NOT NULL` 的 `TITLE` 欄位塞空字串，會得到：

```text
ORA-01400: cannot insert NULL into ("TASKTRACKER"."TASK_ITEMS"."TITLE")
```

這意味著 API 層的必填驗證（[[basics-05-model-binding-and-validation]]）不能省，否則空白標題會變成一個難懂的 500。細節見 [[10-oracle-specifics]] 的空字串一節。

## 九、資料庫連不上的時候

到目前為止都假設資料庫活著。實際營運中，資料庫會重啟、網路會斷、密碼會被改。先看最基本的情況：把 Oracle 容器停掉，再打 API。

```powershell
docker stop tasktracker-oracle
curl.exe -s -i http://localhost:5080/api/tasks
```

```text
HTTP/1.1 500 Internal Server Error
Content-Type: application/problem+json; charset=utf-8

{"type":"https://tools.ietf.org/html/rfc9110#section-15.6.1","title":"An error occurred while processing your request.","status":500,"traceId":"00-e9853b619de5e2cc01478754341545de-3b9ce19ff6df6293-00"}
```

使用者看到的是 500 與通用訊息，沒有資料庫細節，這是對的：連線位址與錯誤碼對呼叫端沒有幫助，卻可能洩漏內部架構。`TaskService` 也不需要額外程式：連線失敗不是 `DbUpdateException`，而是驅動直接丟出的 `OracleException`，沒有 handler 認得它，就落到 `UseExceptionHandler` 的預設路徑，變成 500 的 ProblemDetails。根因在伺服器的 console：

```text
fail: Microsoft.EntityFrameworkCore.Database.Connection[20004]
      An error occurred using the connection to database '' on server 'localhost:1521/FREEPDB1'.
       ---> OracleInternal.Network.NetworkException (0x80004005): ORA-50201: Oracle Communication: Failed to connect to server or failed to parse connect string
       ---> OracleInternal.Network.NetworkException (0x80004005): ORA-12541: Cannot connect. No listener at  host 127.0.0.1 port 1521.
```

最外層的 ORA-50201 是驅動的籠統說法，真正原因在最內層的 ORA-12541：那個位址的 1521 埠沒有 listener。ORA-01017 是帳號密碼錯，ORA-12514 是服務名稱（這裡的 `FREEPDB1`）不對。用回應裡的 `traceId` 去 log 找對應那次請求，是 [[basics-08-middleware-and-exception-handling]] 建立的習慣。

改以 Production 環境重做同樣的測試，回應一樣是通用的 500，只有 `traceId` 不同。

503 Service Unavailable 更貼近「依賴的後端暫時不可用」，但要做到需要區分暫時性連線錯誤與程式 bug，還要設計重試與熔斷，那是 [[18-resilience-and-performance]] 的主題。入門的底線是不吞例外、不把驅動的錯誤訊息回給使用者、確保有 log 可查；服務是否還活著，交給健康檢查端點（[[basics-16-deployment-and-go-live]]）。

## 十、交易：EF Core 預設已經做了什麼

交易（transaction）是一組操作全部成功或全部不生效。很多人習慣在每個方法外面包 `BeginTransaction`，通常多餘：`SaveChanges` 本身就是一個交易，一次呼叫內所有的 INSERT、UPDATE、DELETE 一起提交或回滾，`CreateAsync` 不需要再包。細節見 [[09-transactions-and-concurrency]] 與 [[07-efcore-internals]]。

需要明確交易的情況，是一個業務動作要跨過「不止一次」資料庫寫入。典型的例子是兩次 `SaveChanges`，或是 `ExecuteDeleteAsync` 這類批次操作加上 `SaveChanges`，它們各自是獨立的交易。假設 TaskTracker 新增一個「封存已完成任務」功能：刪掉所有 `done` 的任務，並新增一筆紀錄寫明刪了幾筆。這兩步必須同生同死：

```csharp
public async Task<int> ArchiveDoneAsync(CancellationToken ct)
{
    await using var transaction = await _db.Database.BeginTransactionAsync(ct);
    var removed = await _db.TaskItems.Where(t => t.Status == TaskItemStatus.Done).ExecuteDeleteAsync(ct);
    _db.TaskItems.Add(new TaskItem
    {
        Id = Guid.NewGuid(),
        Title = $"Archived {removed} done tasks",
        Status = TaskItemStatus.Done,
        CreatedAt = _timeProvider.GetUtcNow()
    });
    await _db.SaveChangesAsync(ct);
    await transaction.CommitAsync(ct);
    return removed;
}
```

（這個封存功能只是說明交易寫法的假設範例，TaskTracker 專案並沒有它。）沒有明確交易時，刪除成功而新增失敗，已完成的任務就消失且沒有紀錄。`await using` 是關鍵：離開範圍時若還沒呼叫 `CommitAsync`，交易自動回滾，中途丟例外不需要自己寫 `Rollback`。隔離級別、樂觀並發與重試屬於 [[09-transactions-and-concurrency]]，入門只記一條：單次 `SaveChanges` 不用包；跨多次寫入才包，並且 `await using`。

## 十一、兩個常見的反例

最後是兩種幾乎每個初學者都會寫的程式。它們都能通過測試，都能回傳正確結果，問題在資料量增大以後才出現。

### 反例一：先 `ToList()`，再過濾

```csharp
// 反例
var all = await _db.TaskItems.ToListAsync(ct);
return all.Where(t => t.Status == status).ToList();
```

`ToListAsync` 一執行，EF Core 就送出 `SELECT` 把整張表撈進記憶體，後面的 `Where` 是 C# 在記憶體裡過濾。50 筆看不出差別，50 萬筆時每個請求都把 50 萬列從 Oracle 搬進 API，只為了留下幾筆。正確的順序是把條件加在 `ToListAsync` 之前：

```csharp
return await _db.TaskItems.AsNoTracking().Where(t => t.Status == status).ToListAsync(ct);
```

過濾因此變成 SQL 的 `WHERE`，只有符合的列離開資料庫。判斷法則：LINQ 鏈上出現在 `ToList`、`ToArray`、`AsEnumerable` 之前的運算子會被翻譯成 SQL，之後的在記憶體執行。要確認送出了什麼 SQL，看第六節開啟的 `Database.Command` log。翻譯失敗的處理見 [[08-efcore-query]]。

### 反例二：在迴圈裡查詢

```csharp
// 反例
var result = new List<TaskItem?>();
foreach (var id in ids)
{
    result.Add(await _db.TaskItems.FirstOrDefaultAsync(t => t.Id == id, ct));
}
```

每次迴圈一次資料庫往返，100 個 id 就是 100 條循序執行的 SQL；一次往返 5 毫秒的話，光等待就半秒。這和 N+1 同一類：往返次數隨資料量成長。修正方向是把多次查詢合併成一次：

```csharp
return await _db.TaskItems.AsNoTracking().Where(t => ids.Contains(t.Id)).ToListAsync(ct);
```

`ids.Contains(...)` 會被翻譯成 SQL 的 `IN`，一次往返取回全部。（Oracle 的 `IN` 清單有 1000 個元素的上限，見 [[10-oracle-specifics]]。）關聯資料的 N+1 與 `Include`、投影的解法見 [[08-efcore-query]]。

## 常見誤解

**「`DbContext` 可以註冊成 Singleton，反正只有一個資料庫。」** `DbContext` 不是執行緒安全的，而且 Change Tracker 會持續累積載入過的 entity。一個長壽命的 `DbContext` 會同時碰到並發錯誤與記憶體增長。`AddDbContext` 預設是 Scoped，一個請求一個，依賴它的服務也要至少是 Scoped。

**「所有查詢都該加 `AsNoTracking()`。」** 只有「查出來不會再存回去」的路徑才加。更新路徑需要追蹤，沒有追蹤就沒有快照可比，修改屬性後 `SaveChanges` 不會產生任何 UPDATE，而且沒有錯誤訊息。

**「`Add` 呼叫之後資料就進資料庫了。」** `Add` 只通知 Change Tracker，要等 `SaveChangesAsync` 才 INSERT；忘了它，程式會回 201，資料卻沒寫。

**「Service 先查過標題了，就不需要唯一索引。」** 「先查再寫」在並發時會被兩個同時進來的請求同時通過。唯一性只有資料庫的約束能保證，預先檢查只是讓常見情況的訊息更好看。

**「Oracle 的表名大小寫隨便，反正 EF Core 會處理。」** EF Core 自己查不會出錯，因為它每次都加引號；出問題的是寫不加引號 SQL 的 DBA 與報表工具，遇到 `"LabTaskItems"` 會得到 ORA-00942。

## 同事會來問你的問題

**Q：我 clone 專案之後，`dotnet ef` 說找不到指令，要裝全域的嗎？**
不用。repo 裡有 tool manifest（`dotnet-tools.json`），執行 `dotnet tool restore` 就會裝好和專案一致的版本。裝成全域工具會讓每個人的版本不同，產生的 migration 可能有無關的差異。

**Q：`dotnet run` 起來就報連線字串是必填，但我明明有 `appsettings.json`。**
連線字串刻意不在 `appsettings.json` 裡，因為它包含密碼。開發機用 `dotnet user-secrets set "ConnectionStrings:Default" ...`，部署環境用環境變數 `ConnectionStrings__Default`。`ValidateOnStart` 讓這個錯誤在啟動時就出現，而不是等到第一個請求。

**Q：我能不能在測試環境或正式環境也開 `MigrateOnStartup`？**
技術上可以，但不建議。多副本同時啟動會搶著改 schema，Oracle 的 DDL 隱含提交，中途失敗無法整段回滾。正式環境用 `dotnet ef migrations script --idempotent` 產生 SQL 交給 DBA，或在部署流程裡用獨立的 job 執行。

**Q：我改了 entity 加一個欄位，API 一啟動就 500，說欄位不存在。**
Model 改了，資料庫沒跟上。執行 `dotnet ef migrations add <名稱>` 產生新 migration；開發環境重啟後 `MigrateAsync` 會套用，其他環境把產生的 SQL 交給對應流程。

## 這章的位置

讀完這一章，你能在本機用 Compose 起 Oracle，用 local tool 的 `dotnet ef` 建立並審查 migration，知道 `SaveChanges` 做了什麼，能把記憶體版 Service 改成資料庫版，並處理標題重複與資料庫斷線。TaskTracker 有了持久化，但誰都可以呼叫它，這是下一章的主題。機制請讀 [[07-efcore-internals]]（Change Tracker）、[[08-efcore-query]]（LINQ 變 SQL、N+1）、[[09-transactions-and-concurrency]]（隔離與樂觀並發）、[[10-oracle-specifics]]（型別、主鍵、migration 實務）。

---

## 連結

- 上一章：[[basics-09-configuration-and-environments]]
- 下一章：[[basics-11-auth-concepts-and-pipeline]]
- 對應深度章：[[07-efcore-internals]]、[[08-efcore-query]]、[[09-transactions-and-concurrency]]、[[10-oracle-specifics]]
- 總目錄：[[dotnet-web-api]]
