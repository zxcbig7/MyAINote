---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, dependency-injection, service-layer, lifetime, captive-dependency, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 5：Dependency Injection 與 Service 設計.md
created: 2026-10-31
updated: 2026-10-31
---

# 入門第 07 章：依賴注入與 Service — Controller 越來越胖，邏輯該放哪，物件誰來 new

## 三個一起來的需求

[[basics-06-dto-design]] 結束時，TaskTracker 的 `TasksController` 已經能列出、查詢、建立、更新、刪除任務，而且對外的形狀由 DTO 管著。但打開這個檔案，你會看到它同時做了好幾件事：把資料放在一個 `static List<TaskItem>`，用 LINQ 做狀態篩選與分頁，產生 `Guid` 與建立時間，最後才把結果包成 `Ok(...)`、`NotFound()`。Controller 該管的只有「HTTP 進來、HTTP 出去」，其餘全是任務本身的邏輯。

然後三個需求同一個星期出現：

1. 產品要求建立任務時的時間戳改由統一的時鐘提供，方便測試時固定時間。
2. 測試同事想驗證「查不到任務要回 404」，卻發現要驗證這件事必須先啟動一整個 Web 伺服器、再打 HTTP，因為 Controller 裡的資料取得寫死了，沒有地方可以換掉。
3. 資料很快要從記憶體搬到 Oracle（[[basics-10-efcore-and-oracle]]），那時整個 Controller 都得動。

三件事指向同一個根因：Controller 自己決定了「資料從哪來、邏輯在哪裡、誰來建立這些東西」。本章先把這些邏輯搬進 Service，再讓 ASP.NET Core 的依賴注入（Dependency Injection，下稱 DI）容器負責建立與交付物件。做完之後，上面三個需求都只需要改一個地方。

---

## 一、自己 new 的三個痛點

先看最直覺的寫法。假設已經有一個 `TaskService` 類別，Controller 最自然的用法是自己建立它：

```csharp
// 反例：Controller 自己 new 依賴
[ApiController]
[Route("api/tasks")]
public class TasksController : ControllerBase
{
    private readonly TaskService _service = new TaskService();
}
```

這行程式碼看起來無害，後果卻有三個，而且每一個都會在專案長大之後才變得痛。

第一個是換不掉。`new TaskService()` 把 Controller 綁死在這個具體類別上。第十章要把記憶體清單換成 Oracle 時，如果有三個 Controller 各自 new 了它，就得改三個地方；更糟的是，`TaskService` 的建構子一旦多了參數（例如要傳入時鐘或資料庫），所有 `new` 的地方都得跟著補齊。

第二個是測不了。測試 Controller 的目的，是確認「Service 回傳 null 時，Controller 要回 404」。但 Controller 內部的 Service 是它自己建立的，測試沒有辦法塞一個「永遠回傳 null 的假 Service」進去，只能連同真正的資料一起跑。

第三個是生命週期失控。誰來決定這個 Service 該活多久？Controller 每次請求都會被建立一個新實例，所以 `new TaskService()` 等於每次請求都建一份。如果 Service 裡放著記憶體資料，每次請求都看到一份全新的空資料；如果 Service 持有昂貴的資源（資料庫連線、`HttpClient`），就是每次請求都重建、而且沒人負責釋放。

這三個痛點共同指向一個解法：Controller 不負責建立依賴，只負責「宣告我需要什麼」。誰來提供、提供哪個實作、物件活多久，交給別人決定。這個「別人」就是 DI 容器。

---

## 二、把邏輯搬出 Controller

在談容器之前，先把邏輯搬出去，因為容器要有東西可以交付。

### 2.1 先定義介面

Service 的第一步是介面。`ITaskService` 把 Controller 需要的能力列成五個方法，每個都是 async 並接收 `CancellationToken`（I/O 一律 async，是從這裡開始每個 Service 都遵守的約定，也符合第十章換成資料庫時的形狀）：

```csharp
using TaskTracker.Api.Dtos;

namespace TaskTracker.Api.Services;

public interface ITaskService
{
    Task<PagedResponse<TaskResponse>> ListAsync(TaskListQuery query, CancellationToken ct);

    Task<TaskResponse?> GetByIdAsync(Guid id, CancellationToken ct);

    Task<TaskResponse> CreateAsync(CreateTaskRequest request, CancellationToken ct);

    Task<TaskResponse?> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct);

    Task<bool> DeleteAsync(Guid id, CancellationToken ct);
}
```

留意方法的形狀。輸入是 [[basics-06-dto-design]] 的 Request DTO，輸出是 Response DTO，Service 的邊界上沒有 `TaskItem` entity 外洩。「找不到」用 `null` 或 `false` 表達：Service 不知道也不該知道 HTTP，所以它不回 `NotFound()`，只回「沒有這筆」，由 Controller 決定這在 HTTP 世界裡叫 404。

或許有人會問：只有一個實作的介面，值得多寫一個檔案嗎？答案取決於是否有「縫」需要保留。對 TaskTracker 來說有兩條：測試要能換成假的 Service，第十章要能把實作換掉。這兩個需求都在介面這條縫上才能不動 Controller。如果一個類別既不需要替換、也不需要被假造，直接註冊具體類別（`AddScoped<ReportFormatter>()`）完全合法，沒有必要為每個類別都配一個介面。

### 2.2 實作 TaskService

`TaskService` 的內容幾乎是把原本 Controller 裡的邏輯整段搬過來，差別只在資料放進了實例欄位，時間改由注入的 `TimeProvider` 提供：

```csharp
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Entities;
using TaskTracker.Api.Extensions;

namespace TaskTracker.Api.Services;

// 資料放在執行個體裡，所以這個 Service 必須註冊成 Singleton；第十章換成 DbContext 後改為 Scoped
publicclass TaskService : ITaskService
{
    private readonly object _gate = new();
    private readonly TimeProvider _timeProvider;
    private readonly List<TaskItem> _tasks =
    [
        new() { Id = Guid.Parse("11111111-1111-1111-1111-111111111111"), Title = "Read chapter 7", Status = TaskItemStatus.Done, CreatedAt = new DateTimeOffset(2026, 10, 1, 9, 0, 0, TimeSpan.Zero) },
        new() { Id = Guid.Parse("22222222-2222-2222-2222-222222222222"), Title = "Extract a service", Status = TaskItemStatus.Todo, CreatedAt = new DateTimeOffset(2026, 10, 2, 9, 0, 0, TimeSpan.Zero) },
        new() { Id = Guid.Parse("33333333-3333-3333-3333-333333333333"), Title = "Register it in DI", Status = TaskItemStatus.Todo, CreatedAt = new DateTimeOffset(2026, 10, 3, 9, 0, 0, TimeSpan.Zero) }
    ];

    public TaskService(TimeProvider timeProvider)
    {
        _timeProvider = timeProvider;
    }

    public Task<PagedResponse<TaskResponse>> ListAsync(TaskListQuery query, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        lock (_gate)
        {
            var filtered = query.Status is null ? _tasks : _tasks.Where(t => t.Status == query.Status);
            var ordered = filtered.OrderBy(t => t.CreatedAt).ToList();
            var items = ordered
                .Skip((query.Page - 1) * query.PageSize)
                .Take(query.PageSize)
                .Select(t => t.ToResponse())
                .ToList();
            return Task.FromResult(new PagedResponse<TaskResponse>(items, query.Page, query.PageSize, ordered.Count));
        }
    }

    public Task<TaskResponse?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        lock (_gate)
        {
            return Task.FromResult(_tasks.FirstOrDefault(t => t.Id == id)?.ToResponse());
        }
    }

    public Task<TaskResponse> CreateAsync(CreateTaskRequest request, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        var task = new TaskItem
        {
            Id = Guid.NewGuid(),
            Title = request.Title,
            Status = TaskItemStatus.Todo,
            CreatedAt = _timeProvider.GetUtcNow()
        };
        lock (_gate)
        {
            _tasks.Add(task);
        }

        return Task.FromResult(task.ToResponse());
    }

    public Task<TaskResponse?> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        lock (_gate)
        {
            var task = _tasks.FirstOrDefault(t => t.Id == id);
            if (task is null)
            {
                return Task.FromResult<TaskResponse?>(null);
            }

            task.Title = request.Title;
            task.Status = request.Status!.Value;
            return Task.FromResult<TaskResponse?>(task.ToResponse());
        }
    }

    public Task<bool> DeleteAsync(Guid id, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        lock (_gate)
        {
            var task = _tasks.FirstOrDefault(t => t.Id == id);
            return Task.FromResult(task is not null && _tasks.Remove(task));
        }
    }
}
```

這份實作有幾個值得停下來看的地方。

`TaskService` 的建構子需要一個 `TimeProvider`，這是 .NET 8 加入的抽象類別，`TimeProvider.System` 回傳真實時間，測試時可以換成可手動撥動的假時鐘。以前常見的 `DateTimeOffset.UtcNow` 寫死在方法裡，測試無法固定結果；把時鐘變成「建構子要的依賴」，就是把 DI 的想法用在一個很小的地方。

資料是 `_tasks` 這個實例欄位，也就是說，這個 Service 本身持有狀態。這件事決定了它之後怎麼註冊（第五節會展開），也解釋了為什麼每個方法都包著 `lock (_gate)`：`List<T>` 不是 thread-safe，而 ASP.NET Core 會同時處理多個請求，兩個請求同時 `Add` 或一個 `Add` 一個列舉，都可能壞掉。[[basics-06-dto-design]] 時 Controller 用的 `static List` 有同樣的風險，當時只是暫時的資料來源；搬進 Service 之後順手補上了鎖。第十章換成資料庫，這些鎖會跟著 `_tasks` 一起消失，因為交給資料庫處理並行。

`ct.ThrowIfCancellationRequested()` 讓已經被客戶端放棄的請求不再繼續做事。對記憶體清單來說多此一舉，但它讓介面簽章與之後的真實 I/O 版本一致，Controller 完全不用跟著改。

### 2.3 Controller 變薄

Service 到位後，`TasksController` 只剩下 HTTP 的工作：

```csharp
using Microsoft.AspNetCore.Mvc;
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Services;

namespace TaskTracker.Api.Controllers;

[ApiController]
[Route("api/tasks")]
public class TasksController : ControllerBase
{
    private readonly ITaskService _taskService;

    public TasksController(ITaskService taskService)
    {
        _taskService = taskService;
    }

    [HttpGet]
    public async Task<ActionResult<PagedResponse<TaskResponse>>> GetAllAsync([FromQuery] TaskListQuery query, CancellationToken ct)
    {
        return Ok(await _taskService.ListAsync(query, ct));
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<TaskResponse>> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var task = await _taskService.GetByIdAsync(id, ct);
        return task is null ? NotFound() : Ok(task);
    }

    [HttpPost]
    public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct)
    {
        var task = await _taskService.CreateAsync(request, ct);
        return CreatedAtAction(nameof(GetByIdAsync), new { id = task.Id }, task);
    }

    [HttpPut("{id:guid}")]
    public async Task<ActionResult<TaskResponse>> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct)
    {
        var task = await _taskService.UpdateAsync(id, request, ct);
        return task is null ? NotFound() : Ok(task);
    }

    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> DeleteAsync(Guid id, CancellationToken ct)
    {
        return await _taskService.DeleteAsync(id, ct) ? NoContent() : NotFound();
    }
}
```

每個 action 現在都是兩三行：呼叫 Service、把結果翻譯成 HTTP。`CancellationToken ct` 是 ASP.NET Core 在 model binding 時自動提供的，連線中斷時它會被取消，Controller 把它往下傳給 Service，整條路徑才都能被中止。

留意 `private readonly ITaskService _taskService;` 這一行與建構子。Controller 現在只認識介面，沒有任何一處提到 `TaskService` 這個具體類別。

### 2.4 方法名稱加了 Async 之後，CreatedAtAction 會壞

方法改成 `GetByIdAsync` 這類名稱時，有一個很容易踩到的陷阱。先看不處理它的結果：Controller 已經改成上面的樣子，但 `Program.cs` 的 `AddControllers()` 沒有任何設定。建立任務：

```powershell
'{"title":"Write chapter 7"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Accept: application/json" -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 500 Internal Server Error
Content-Type: text/plain; charset=utf-8
Date: Fri, 30 Oct 2026 14:23:10 GMT
Server: Kestrel
Transfer-Encoding: chunked

System.InvalidOperationException: No route matches the supplied values.
   at Microsoft.AspNetCore.Mvc.CreatedAtActionResult.OnFormatting(ActionContext context)
   at Microsoft.AspNetCore.Mvc.Infrastructure.ObjectResultExecutor.ExecuteAsyncCore(ActionContext context, ObjectResult result, Type objectType, Object value)
   ...
```

（後面的 stack trace 省略。）編譯完全沒問題，建立請求卻回了 500。再看一眼資料有沒有建立：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:23:10 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"items":[{"id":"11111111-1111-1111-1111-111111111111","title":"Read chapter 7","status":"done","createdAt":"2026-10-01T09:00:00+00:00"},{"id":"22222222-2222-2222-2222-222222222222","title":"Extract a service","status":"todo","createdAt":"2026-10-02T09:00:00+00:00"},{"id":"33333333-3333-3333-3333-333333333333","title":"Register it in DI","status":"todo","createdAt":"2026-10-03T09:00:00+00:00"},{"id":"2ed4a764-ce69-452b-8289-ce82a98c357b","title":"Write chapter 7","status":"todo","createdAt":"2026-10-30T14:23:11.3537575+00:00"}],"page":1,"pageSize":20,"totalCount":4}
```

`totalCount` 變成 4：第四筆任務確實建立了。客戶端收到 500，以為失敗而重試，結果就是同一筆任務被建兩次。這是這個陷阱最危險的地方：錯誤發生在寫入已成功之後的「組裝回應」階段。

原因是 MVC 預設會在登記 action 時把名稱結尾的 `Async` 拿掉，也就是 `GetByIdAsync` 在路由系統裡叫 `GetById`。`nameof(GetByIdAsync)` 產生的字串是 `"GetByIdAsync"`，產生 `Location` 標頭時找不到叫這個名字的 action，於是丟出 `No route matches the supplied values.`。

解法有兩個：把 `nameof` 改成字串 `"GetById"`，或是關掉預設的剝除行為。本書選第二個，因為它讓 `nameof` 繼續受編譯器保護，改方法名時不會悄悄失效。`Program.cs` 在 `AddControllers` 加上設定：

```csharp
builder.Services.AddControllers(options =>
{
    // 預設會把 action 名稱的 Async 後綴拿掉，CreatedAtAction(nameof(GetByIdAsync)) 會因此找不到 action
    options.SuppressAsyncSuffixInActionNames = false;
});
```

這個坑的路由面向在 [[basics-04-controllers-and-routing]] 提過；現在是它第一次真的咬人，因為方法才第一次全部改成 `Async`。

---

## 三、建構子注入：宣告需要什麼，不管誰給

Controller 現在的建構子是：

```csharp
public TasksController(ITaskService taskService)
{
    _taskService = taskService;
}
```

這就是 constructor injection（建構子注入）。Controller 在建構子參數上宣告「我需要一個 `ITaskService`」，完全不知道、也不關心實際是哪個類別、何時建立、活多久。ASP.NET Core 每次要處理一個請求，就會建立一個 `TasksController` 實例，建立時檢視建構子參數，向 DI 容器要每一個依賴，再把拿到的物件傳進去。

容器要能回答「`ITaskService` 是誰」，就得有人事先告訴它。這個動作叫註冊（register），發生在 `Program.cs` 的第一階段（[[basics-03-first-project]] 說的「登記服務」那段）；而容器在請求進來時依照註冊的資料實際建立物件，叫解析（resolve）。兩件事分在兩個時間點，這個分開是 DI 好用的原因：寫 Controller 的人只要宣告需求，管理對應關係的人集中在一處。

註冊的基本形態是 `AddXxx<服務型別, 實作型別>()`：

```csharp
builder.Services.AddSingleton<ITaskService, TaskService>();
```

意思是「有人要 `ITaskService` 時，給他一個 `TaskService`」。左邊是對外的抽象，右邊是實際建立的類別。`Xxx` 的部分（`Singleton`、`Scoped`、`Transient`）決定這個物件活多久，下一節專門講。

如果完全忘了註冊會怎樣？啟動不會報錯，因為此時沒有任何人要這個服務；第一個打到 `TasksController` 的請求，在解析 Controller 時才發現找不到 `ITaskService`，回 500 並在 console 印出 `Unable to resolve service for type ... while attempting to activate ...`。看到 `Unable to resolve service` 就去檢查註冊，這是 DI 最常見的錯誤。

### 3.1 用 extension method 收納註冊

專案小的時候，把註冊直接寫在 `Program.cs` 沒問題。但服務會一個一個增加，`Program.cs` 很快變成一長串註冊與設定混在一起的清單。慣例是用 extension method 把相關的註冊收成一個群組。TaskTracker 新增 `Extensions/ServiceCollectionExtensions.cs`：

```csharp
using TaskTracker.Api.Services;

namespace TaskTracker.Api.Extensions;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddTaskTrackerServices(this IServiceCollection services)
    {
        services.AddSingleton(TimeProvider.System);
        services.AddSingleton<ITaskService, TaskService>();
        return services;
    }
}
```

`Program.cs` 於是只留下一行意圖明確的呼叫，並把 `using TaskTracker.Api.Extensions;` 放在檔案開頭：

```csharp
using TaskTracker.Api.Extensions;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers(options =>
{
    // 預設會把 action 名稱的 Async 後綴拿掉，CreatedAtAction(nameof(GetByIdAsync)) 會因此找不到 action
    options.SuppressAsyncSuffixInActionNames = false;
});
builder.Services.AddOpenApi();
builder.Services.AddTaskTrackerServices();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

framework 自己也是這個做法，`AddControllers()`、`AddOpenApi()` 都是 `IServiceCollection` 的 extension method，內部登記了數十個服務。TaskTracker 的版本同理：以後加了 `AddTaskTrackerAuth()`、`AddTaskTrackerPersistence()`，`Program.cs` 看起來還是清爽的幾行。這也是換實作的位置：第十章要把 `TaskService` 換掉，改的是 `AddTaskTrackerServices` 裡的一行。

### 3.2 此時照著做會得到什麼

到目前為止的檔案改動是：新增 `Services/ITaskService.cs`、`Services/TaskService.cs`、`Extensions/ServiceCollectionExtensions.cs`；改寫 `Controllers/TasksController.cs` 與 `Program.cs`。其餘的 DTO、entity、`ToResponse()` 擴充方法都不動。執行：

```powershell
dotnet build
dotnet run --project src/TaskTracker.Api --launch-profile http
```

另開一個 PowerShell 視窗，列出任務：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:23:36 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"items":[{"id":"11111111-1111-1111-1111-111111111111","title":"Read chapter 7","status":"done","createdAt":"2026-10-01T09:00:00+00:00"},{"id":"22222222-2222-2222-2222-222222222222","title":"Extract a service","status":"todo","createdAt":"2026-10-02T09:00:00+00:00"},{"id":"33333333-3333-3333-3333-333333333333","title":"Register it in DI","status":"todo","createdAt":"2026-10-03T09:00:00+00:00"}],"page":1,"pageSize":20,"totalCount":3}
```

（`Date` 標頭與建立時間每次會不同。）建立一筆任務並確認 `Location` 標頭正確：

```powershell
'{"title":"Write chapter 7"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:23:37 GMT
Server: Kestrel
Location: http://localhost:5080/api/tasks/33ca5ae9-7cde-44bb-b34e-a48c234ef132
Transfer-Encoding: chunked

{"id":"33ca5ae9-7cde-44bb-b34e-a48c234ef132","title":"Write chapter 7","status":"todo","createdAt":"2026-10-30T14:23:37.5604768+00:00"}
```

`id` 與時間每次都不一樣，這是正常的。用 `Location` 裡的網址查詢，會得到同一筆任務；再列一次清單，`totalCount` 會是 4。更新、刪除與驗證失敗的行為，與 [[basics-06-dto-design]] 結束時完全相同，因為外部契約一個字都沒動。這正是這次重構的標準：對外行為不變，內部結構改善。

---

## 四、三種 lifetime：物件活多久

註冊時那個 `AddSingleton` 的字眼值得認真對待，因為選錯 lifetime 是 DI 最常見也最難查的錯誤來源。容器提供三種：

- Transient：每次向容器要，就建立一個新實例。
- Scoped：在同一個 scope 內共用一個實例。在 ASP.NET Core 中，每個 HTTP 請求自成一個 scope。
- Singleton：整個應用程式只建立一個實例，所有請求共用。

這三句話裡最容易誤解的是 Transient。常見的說法是「Transient 每次請求都建立新的」，聽起來順理成章，卻是錯的：Transient 是每次「解析」都新建，同一個請求裡如果有兩個地方要它，就會建立兩個。

為了確認這件事，我做了一個最小的實驗：三個類別各自在建構時產生一個 `Guid`，分別註冊為 Transient、Scoped、Singleton。一個 Scoped 的 `Consumer` 在建構子裡同時要兩個 Transient、兩個 Scoped、一個 Singleton，之後端點再從 `HttpContext.RequestServices` 各取一次，用 `ReferenceEquals` 比較。連續發兩個請求，結果如下（Id 只列前 8 碼）：

```text
請求 1
  建構子注入的兩個 Transient：9222e014 / 88b0fbf6（同一個實例：False）
  建構子注入的兩個 Scoped：6230ecbe / 6230ecbe（同一個實例：True）
  再從 RequestServices 取 Scoped：6230ecbe（和建構子拿到的同一個：True）
  再從 RequestServices 取 Transient：e49f959a（和建構子拿到的同一個：False）
  Singleton：63e6aee9
請求 2
  建構子注入的兩個 Transient：88f56d6a / 817ddb6b（同一個實例：False）
  建構子注入的兩個 Scoped：5094c469 / 5094c469（同一個實例：True）
  再從 RequestServices 取 Scoped：5094c469（和建構子拿到的同一個：True）
  再從 RequestServices 取 Transient：ccda8bfe（和建構子拿到的同一個：False）
  Singleton：63e6aee9
```

請看這張結果的三個重點。同一個請求裡，建構子要兩次 Transient，得到兩個不同的實例，之後再向 `RequestServices` 要一次，又是第三個，所以 Transient 的「新」和 scope 無關，每次解析就一個。Scoped 在請求 1 裡四次取得都是 `6230ecbe`，到請求 2 就換成 `5094c469`，也就是同請求相同、跨請求不同。Singleton 兩個請求看到的都是 `63e6aee9`。

這個結果有實務後果。若把會累積狀態的物件（例如第十章的 `DbContext`）註冊成 Transient，同一個請求裡兩個 Service 各拿到各自的 `DbContext`，change tracker 不共用，也沒辦法在同一個交易裡工作。「一個請求一份」才是 Scoped 的用途。

三種 lifetime 的選擇可以歸納成判準：

| lifetime  | 適合                                                                      | 不適合                                     |
| --------- | ------------------------------------------------------------------------- | ------------------------------------------ |
| Transient | 無狀態、很輕、每個使用它的地方都要獨立一份的小物件                        | 會累積狀態的物件、建立昂貴的物件           |
| Scoped    | 與單一請求綁在一起的工作單位（`DbContext`、同一個請求內要共用的 Service） | 要跨請求保留資料的物件                     |
| Singleton | 無狀態且 thread-safe 的工具、快取、時鐘，或本來就要跨請求保留的資料       | 持有請求相關資料、或依賴 Scoped 物件的類別 |

不確定時預設選 Scoped，確定無狀態且 thread-safe 再升為 Singleton。Transient 要有明確的理由才用。機制層面（scope 是誰開的、誰負責 Dispose、容器怎麼解析）在 [[02-dependency-injection]]。

---

## 五、為什麼 TaskTracker 的 Service 是 Singleton

回頭看 `AddTaskTrackerServices` 裡的那一行：`AddSingleton<ITaskService, TaskService>()`。照剛才的建議，Web API 的 Service 通常預設選 Scoped，這裡為什麼反過來？

因為這一章的 `TaskService` 把資料放在自己的欄位 `_tasks` 裡。資料屬於 Service 這個實例，那麼這個實例活多久，資料就活多久。如果註冊成 Scoped，每個請求都會得到一個新的 `TaskService`，也就是一份全新的、只含三筆種子資料的 `_tasks`。

這不是推論，實測過。把 `AddSingleton<ITaskService, TaskService>()` 暫時改成 `AddScoped`，建立一筆任務：

```powershell
'{"title":"Write chapter 7"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:23:25 GMT
Server: Kestrel
Location: http://localhost:5080/api/tasks/bd21c192-5473-4b33-b1bf-b1ecdb1dca72
Transfer-Encoding: chunked

{"id":"bd21c192-5473-4b33-b1bf-b1ecdb1dca72","title":"Write chapter 7","status":"todo","createdAt":"2026-10-30T14:23:25.6129267+00:00"}
```

回應 `201 Created`，看起來完全成功。用 `Location` 的網址去查剛建立的任務：

把上一個回應裡的 `id` 存進 `$newId`，再查詢：

```powershell
curl.exe -s -i "http://localhost:5080/api/tasks/$newId"
```

```text
HTTP/1.1 404 Not Found
Content-Type: application/problem+json; charset=utf-8
Date: Fri, 30 Oct 2026 14:23:25 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.5","title":"Not Found","status":404,"traceId":"00-e7bb8c5a42c76431c6a980484b8f00b5-8deeb34be5388292-00"}
```

才剛回報建立成功的任務，下一個請求就找不到了；再列一次清單，`totalCount` 回到 3，剛才那筆從沒存在過。這是一個沒有任何錯誤訊息的 bug：建立請求的 Service 實例處理完就被丟掉，連同裡面那筆新任務。把註冊改回 `AddSingleton`，所有任務就在同一個 Service 實例裡累積：建立後可以查到，更新與刪除也都對得上。

所以這一章的結論有兩層。第一層，lifetime 要和「這個物件持有什麼」搭配：持有跨請求要保留的資料，只能是 Singleton。第二層，持有資料並不是 Service 的常態。正式的系統裡資料在資料庫，Service 不該有狀態。[[basics-10-efcore-and-oracle]] 把記憶體清單換成 `DbContext` 後，`TaskService` 只持有 `DbContext` 這個依賴（本身是 Scoped）。那時的註冊要改成 `AddScoped`，原因是下一節要講的：Singleton 不能依賴 Scoped。

這也是本章把註冊集中在 `AddTaskTrackerServices` 的好處：到時只要改那一行。

---

## 六、Captive dependency：Singleton 抓住 Scoped

上一節留下一個問題：如果第十章忘了把 `TaskService` 改成 Scoped，繼續維持 Singleton，但它的建構子現在要一個 Scoped 的 `DbContext`，會怎樣？

Singleton 在應用程式生命週期中只建立一次，建立時向容器要 `DbContext`，容器照辦，於是這個 `DbContext` 被存進 Singleton 的欄位，從此跟著 Singleton 活到應用程式結束。它的註冊明明寫 Scoped，實際壽命卻由持有者決定，這個現象叫 captive dependency（被俘虜的依賴）。「長生命週期不可依賴短生命週期」這句口訣就是這個規則的白話。

容器有沒有擋？答案是看環境，而且差異大到足以讓人在開發機上看不到任何症狀、上線後才出事。為此做了一組實驗：Singleton 的 `SingletonSvc` 建構子需要 Scoped 的 `IScopedDep`，在不同環境與驗證開關下啟動。`ValidateScopes` 與 `ValidateOnBuild` 是 DI 容器的兩個驗證開關，前者檢查生命週期是否違規，後者在 `Build()` 時就試著建構所有註冊的服務。結果（.NET 10）：

- Development、全部預設：`builder.Build()` 當場失敗，丟出 `AggregateException`，訊息包含 `Cannot consume scoped service 'Experiments.IScopedDep' from singleton 'Experiments.ISingletonSvc'.`。應用程式根本起不來，錯誤在啟動時就看得見。
- Development、`ValidateScopes = true`、`ValidateOnBuild = false`：`Build()` 成功，錯誤延後到第一個解析 `ISingletonSvc` 的請求，回 500，例外是同樣的 `Cannot consume scoped service ...`。
- Production、全部預設：`Build()` 成功，兩個請求都回 200，完全沒有任何錯誤。但看回應內容：

```text
GET /probe -> 200 OK | body: singleton 持有的 scoped Id = 00d534d7，這次請求的 scoped Id = 99e1a457
GET /probe -> 200 OK | body: singleton 持有的 scoped Id = 00d534d7，這次請求的 scoped Id = 819a5ed1
```

  Singleton 抓住的那個 Scoped 實例，兩次都是 `00d534d7`，而每個請求自己拿到的 Scoped 實例不同。Scoped 服務實質上變成了 Singleton，容器沒有發出任何訊號。
- Production、`ValidateScopes = true`：偵測到，請求回 500。
- Production、只開 `ValidateOnBuild = true`：沒有偵測到，兩個請求都回 200，Singleton 抓到的 Id 還是同一個（`cfa3600a`）。

最後一項最反直覺。名字聽起來「建置時驗證」應該能抓到生命週期不匹配，實測並不能：`ValidateOnBuild` 檢查的是服務能不能被建構（例如缺少依賴），不檢查生命週期。要在啟動時就抓到，兩個開關都要開，而 Development 預設就是這個組合，所以開發時一切正常、上線後靜默失敗。

後果有多嚴重？如果被俘虜的是 `DbContext`，所有請求會共用同一個，而 `DbContext` 不是 thread-safe，同時進來的請求可能撞出 `A second operation was started on this context`；它的 change tracker 會一直累積記憶體；也會讓不同請求之間看到彼此改過的狀態。症狀發生在流量上來之後、而且難以重現，完整的因果推導在 [[02-dependency-injection]] 的 captive dependency 一節。

對策是讓所有環境都有同樣的檢查，而不是靠 Development 自動開。在 `Program.cs` 加上：

```csharp
builder.Host.UseDefaultServiceProvider(options =>
{
    options.ValidateScopes = true;
    options.ValidateOnBuild = true;
});
```

代價是啟動時多一次走訪整張依賴圖，換來的是 Production 也在啟動時就失敗，部署管線能在流量打進來之前抓到。如果不想改 Production 的行為，至少讓 CI 的整合測試跑在 Development 環境，這個檢查也會在合併前觸發（[[basics-15-testing]]）。

版本備註：上面的結果是在 .NET 10 實測的。.NET 9 的 breaking change 清單寫到 Development 預設啟用 `ValidateOnBuild`；.NET 8 沒有實測，依清單推論是第一次解析時才失敗，不要拿它當事實。

Singleton 真的需要用到 Scoped 服務時（例如背景工作每隔一段時間查資料庫），解法是注入 `IServiceScopeFactory`，每次工作自己開一個 scope，用完釋放。做法在 [[02-dependency-injection]]。

---

## 七、Controller 與 Service 的分界

本章開頭說 Controller 越來越胖，邏輯該放哪。現在可以給具體的判準：Controller 管「HTTP 的進與出」，Service 管「任務本身要怎麼運作」。用 TaskTracker 的實際例子對照：

| 這件事                                                 | 放哪                         | 理由                               |
| ------------------------------------------------------ | ---------------------------- | ---------------------------------- |
| `[Route("api/tasks")]`、`[HttpGet("{id:guid}")]`       | Controller                   | 路徑與方法是 HTTP 的概念           |
| `[FromQuery] TaskListQuery`、body 綁定與驗證           | Controller（framework 代勞） | 屬於 request 的解讀                |
| 「查無資料就回 404」、`NoContent()`、`CreatedAtAction` | Controller                   | 狀態碼與標頭是 HTTP 的概念         |
| 狀態篩選、排序、分頁計算                               | Service                      | 與 HTTP 無關，換成別的呼叫端也一樣 |
| 產生 `Guid`、指定建立時間、新任務預設 `todo`           | Service                      | 任務的規則                         |
| 「已完成的任務不能再改標題」這類規則（若將來要加）     | Service                      | 業務規則，不能依賴誰在呼叫         |

判斷方式是問一個問題：這段程式碼會不會因為換了另一種呼叫端而改變？假設明天要加一個命令列工具，也要建立任務，它還是要產生 `Guid`、設定預設狀態，但完全用不到 `CreatedAtAction`。前者屬於 Service，後者只屬於 HTTP。

也可以從簽章看出界線：Service 的方法不接收 `HttpContext`、不回傳 `IActionResult`、不 `return NotFound()`，也不拋出 HTTP 的例外型別。一旦 Service 的 using 裡出現 `Microsoft.AspNetCore.Mvc`，通常就是分界跑偏了。

看看不好的做法長什麼樣，這是 Controller 變胖的典型：

```csharp
// 反例：Controller 兼任 Service
[HttpPost]
public ActionResult<TaskResponse> Create(CreateTaskRequest request)
{
    var task = new TaskItem
    {
        Id = Guid.NewGuid(),
        Title = request.Title,
        Status = TaskItemStatus.Todo,
        CreatedAt = DateTimeOffset.UtcNow
    };
    Tasks.Add(task);
    return CreatedAtAction(nameof(GetById), new { id = task.Id }, task.ToResponse());
}
```

這其實就是 [[basics-06-dto-design]] 的 Create：在 action 裡直接建立 entity、讀寫資料、寫死時間。它的問題不在於「行數太多」，而是要驗證任何一項行為，都得走完整個 HTTP 管線。對照搬進 Service 之後的樣子：

```csharp
[HttpPost]
public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct)
{
    var task = await _taskService.CreateAsync(request, ct);
    return CreatedAtAction(nameof(GetByIdAsync), new { id = task.Id }, task);
}
```

薄了之後最直接的好處是測試。因為 Controller 只認識 `ITaskService`，測試可以丟一個假的進去，不需要伺服器、不需要 HTTP。下面這段測試了「Service 查不到時 Controller 回 404」，專案已建置並執行過：

```csharp
using Microsoft.AspNetCore.Mvc;
using TaskTracker.Api.Controllers;
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Services;

var controller = new TasksController(new FakeTaskService());
var result = await controller.GetByIdAsync(Guid.NewGuid(), CancellationToken.None);
Console.WriteLine(result.Result is NotFoundResult ? "NotFound" : result.Result?.GetType().Name);

publicclass FakeTaskService : ITaskService
{
    public Task<PagedResponse<TaskResponse>> ListAsync(TaskListQuery query, CancellationToken ct) => throw new NotImplementedException();
    public Task<TaskResponse?> GetByIdAsync(Guid id, CancellationToken ct) => Task.FromResult<TaskResponse?>(null);
    public Task<TaskResponse> CreateAsync(CreateTaskRequest request, CancellationToken ct) => throw new NotImplementedException();
    public Task<TaskResponse?> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct) => throw new NotImplementedException();
    public Task<bool> DeleteAsync(Guid id, CancellationToken ct) => throw new NotImplementedException();
}
```

```text
NotFound
```

這是用一個主控台程式示範，真正的測試專案會用 xUnit 並搭配 mocking 套件省掉手寫假類別，[[basics-15-testing]] 會正式處理。這裡想展示的是：能這樣測，代表介面這條縫真的有用。

這一章刻意沒有加 Repository 層。常見的分層圖會畫成 Controller → Service → Repository → DbContext，但 TaskTracker 此刻的資料就在 Service 裡，多一層空殼沒有價值。第十章會直接在 Service 裡使用 `DbContext`；Repository 該不該存在是個有立場的爭論，見 [[expert-02-architecture]]。

---

## 八、反例：Service Locator

DI 有一個容易走偏的路徑：既然容器能提供任何服務，為什麼不直接拿容器本身？

```csharp
// 反例：Service Locator
public class TasksController : ControllerBase
{
    private readonly IServiceProvider _provider;

    public TasksController(IServiceProvider provider)
    {
        _provider = provider;
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<TaskResponse>> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var service = _provider.GetRequiredService<ITaskService>();
        var task = await service.GetByIdAsync(id, ct);
        return task is null ? NotFound() : Ok(task);
    }
}
```

這樣能跑，但問題出在建構子簽章：它只說「我需要整個容器」，沒說需要哪些服務。讀程式的人必須讀完每個方法才知道這個類別依賴什麼；測試時必須建立一個含所有服務的容器，不能只假造一個 `ITaskService`；如果漏了註冊，錯誤要等到那個方法被呼叫時才發生，而不是物件建立時。最麻煩的是這種依賴是隱形的：啟動時的檢查看不到它，因為建構子沒有宣告。Singleton 裡這樣寫，從根容器解析 Scoped 服務，只有 `ValidateScopes` 開著才會在「那一行真的執行時」丟出 `Cannot resolve scoped service ... from root provider`；`ValidateScopes` 沒開（Production 預設）就會靜默變成第六節的 captive dependency。無論 `ValidateOnBuild` 開不開，這種問題都不會在啟動時浮現。

好的做法是第二節那個版本：建構子參數就是依賴清單。偶爾確實需要 `IServiceProvider` 或 `IServiceScopeFactory`（例如背景工作自己開 scope、工廠型別要依執行期條件挑選實作），這種用法應當集中在少數基礎設施程式碼，不要出現在 Controller 與一般 Service。

---

## 常見誤解

**「Transient 是每個請求建立一個新的。」** 不少教材這樣寫，實測不成立：Transient 是每次「解析」建立一個，同一個請求裡兩個建構子參數都要它，就是兩個不同實例。每個請求一個的是 Scoped。

**「Singleton 注入 Scoped 一定會丟例外。」** 只有 scope 驗證開著才會。Development 預設開，所以開發時看得到；Production 預設不開，容器靜默接受，Scoped 物件變成 Singleton。只開 `ValidateOnBuild` 也偵測不到。

**「用了 DI，程式就分層良好。」** DI 只負責交付物件，不決定邏輯放哪。把所有邏輯留在 Controller、只是用 DI 注入一個 `DbContext`，Controller 還是胖的。分層是設計決定，DI 是實現它的工具。

**「每個類別都要配一個介面。」** 介面是為了保留一條縫：測試要換成假的，或實作將來要替換。沒有這種需求的類別（純粹的小工具、只有一個實作且不會被假造）直接註冊具體類別就好。

**「在 Controller 裡 new 一個 Service 比較簡單，反正都能跑。」** 能跑，但換不掉、測不了、生命週期失控；專案一長大，改一次建構子要改所有 new 的地方。簡單是一時的。

## 同事會來問你的問題

**Q：Service 為什麼不直接回傳 `NotFound()`？**

`NotFound()` 是 HTTP 的概念，而 Service 不該知道呼叫它的是 HTTP 請求還是背景工作或測試。Service 回傳 `null` 或 `false`，由 Controller 決定這叫 404 還是 409。這樣同一個 Service 可以被不同的呼叫端重複使用。

**Q：我的 Service 是 Scoped，要注入 Singleton 的快取，反過來可以嗎？**

Scoped 依賴 Singleton 沒問題，因為被依賴的壽命更長。反過來（Singleton 依賴 Scoped）才會出事。規則是：一個服務只能依賴壽命大於或等於自己的服務。

**Q：為什麼 TimeProvider 要註冊成 Singleton？**

`TimeProvider.System` 沒有狀態，所有人共用同一個實例沒有任何問題，Singleton 最省。測試時換成假的時鐘，是用 `Replace` 換掉這個註冊，Service 的程式碼不用改。

**Q：沒註冊就用，啟動會失敗嗎？**

不會。DI 在啟動時只登記，不檢查「誰需要誰」。第一個需要它的請求才會得到 `Unable to resolve service` 的 500。第六節的 `ValidateOnBuild` 能在啟動時抓到「已註冊的服務缺了它的依賴」，但 Controller 本身沒有註冊在容器裡，它建構子漏掉的依賴實測仍然要等到請求進來才會爆。所以新增 Controller 或依賴之後，至少要打一次對應的端點。

**Q：所有註冊都寫在 `AddTaskTrackerServices` 裡，會不會越寫越長？**

會，到時就依功能拆成多個 extension method（例如 `AddTaskTrackerPersistence`、`AddTaskTrackerAuth`），`Program.cs` 依序呼叫。拆分的依據是「一起變動的放一起」，而不是類別數量。

## 這章的位置

讀完這章，你能說明為什麼 Controller 不該自己 `new` 依賴，能把邏輯搬進 `ITaskService` / `TaskService`，用 constructor injection 與 extension method 完成註冊，能從 Transient、Scoped、Singleton 的實測行為選出正確的 lifetime，並解釋 TaskTracker 此刻的 Service 為什麼是 Singleton、第十章為什麼要改成 Scoped。你也知道 captive dependency 在 Production 為什麼靜默發生，以及怎麼讓所有環境都在啟動時就失敗。

下一章 [[basics-08-middleware-and-exception-handling]] 處理另一類「每支 API 都要做的事」：記錄、錯誤處理，它們不屬於任何一個 Service，而是橫跨所有請求。想看容器如何解析建構子、scope 的開關時機、誰負責 Dispose，請讀深度篇 [[02-dependency-injection]]。

---

## 連結

- 上一章：[[basics-06-dto-design]]
- 下一章：[[basics-08-middleware-and-exception-handling]]
- 對應深度章：[[02-dependency-injection]]
- 全書目錄：[[dotnet-web-api]]
