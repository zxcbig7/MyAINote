---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, controller, routing, attribute-routing, actionresult, createdat-action, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 3：Controller、Routing 與 Action 設計.md
  - raw/Web Framework/NET Web API/aspnet-web-api-web-research/aspnet-web-api-web-research.md
  - raw/Web Framework/NET Web API/ASP NET Core Web API 常用 Attribute 整理.md
created: 2026-10-31
updated: 2026-10-31
---

# 入門第 04 章：Controller 與 Routing — 把 API 規格變成可以呼叫的端點

## 兩個 404，長得不一樣

前端同事在串 TaskTracker 的「讀取單一任務」。他先打一個不存在的 id，再打一個亂寫的 id：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks/99999999-9999-9999-9999-999999999999
```

```text
HTTP/1.1 404 Not Found
Content-Type: application/problem+json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:26 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.5","title":"Not Found","status":404,"traceId":"00-1400a43d0f90abdb630ac91e008b0b84-66b45c1bb9693e8e-00"}
```

```powershell
curl.exe -s -i http://localhost:5080/api/tasks/abc
```

```text
HTTP/1.1 404 Not Found
Content-Length: 0
Date: Fri, 30 Oct 2026 14:19:27 GMT
Server: Kestrel
```

兩個都是 404，一個帶著 `application/problem+json` 的 body 和 `traceId`，另一個 body 是空的，連 `Content-Type` 都沒有。他的錯誤處理程式碼如果依賴 body 來顯示訊息，第二種情況會直接壞掉。更麻煩的是，後端開發者自己也答不出為什麼會有兩種：程式裡明明只寫了一種 `NotFound()`。

答案分成兩半。第一個 404 是 Controller 裡的程式碼主動回的，所以框架有機會把它包成標準的錯誤格式；第二個 404 連 Controller 都沒進去，請求在「找哪個 endpoint 處理」這一步就落空了，沒有任何程式碼可以幫它加 body。這個差異串起本章的三件事：請求怎麼被路由到某個 action，action 用什麼型別、什麼方法把結果交還給框架，以及 `[ApiController]` 在背後替我們多做了什麼。

[[basics-02-rest-api-design]] 交出了 TaskTracker 的規格，[[basics-03-first-project]] 讓一個只有 `GET /api/ping` 的專案跑起來。本章把規格裡的五支任務端點寫出來，並用 `curl.exe` 逐一打過。章末還會看到：這一章的資料暫時放在記憶體裡，這是刻意的過渡，也會說明它在哪些情況下一定會出錯。

---

## 一、Controller 該做什麼，不該做什麼

動手寫 `TasksController` 之前，先決定它的邊界。Controller 在整個系統裡是 HTTP 的入口：請求從這裡進來，回應從這裡出去。它的工作可以用四個動詞說完：接收請求、取出輸入、把工作交給別人、組出 HTTP 回應。

「把工作交給別人」是這四件事裡最容易被忽略的一件。Controller 不該自己做商業邏輯、不該自己存取資料庫、也不該自己控制複雜的流程。理由很實際：Controller 只能透過 HTTP 呼叫。如果「標題不可重複」的規則寫在 `Create` 這個 action 裡，之後要做批次匯入、背景工作、另一支內部 API 時，這條規則要嘛被複製一份，要嘛根本漏掉。測試也跟著受害，要驗證一條規則得先組出整個 HTTP 請求。

看一個反例。下面這個 action 把驗證、重複檢查、建立物件、寫入資料全部擠在一起：

```csharp
// 反例：規則和資料存取都寫在 action 裡
[HttpPost]
public ActionResult<TaskItem> Create(TaskItem input)
{
    var title = input.Title.Trim();
    if (title.Length is 0 or > 100)
    {
        return BadRequest("title must be 1 to 100 characters");
    }

    if (Tasks.Any(t => t.Title.Equals(title, StringComparison.OrdinalIgnoreCase)))
    {
        return Conflict("duplicate title");
    }

    var task = new TaskItem
    {
        Id = Guid.NewGuid(),
        Title = title,
        Status = TaskItemStatus.Todo,
        CreatedAt = DateTimeOffset.UtcNow
    };
    Tasks.Add(task);
    return Created($"/api/tasks/{task.Id}", task);
}
```

這段程式能編譯，也能跑，問題在於它混合了三種不同層級的事：長度與空白的規則（輸入檢查）、重複標題（商業規則）、`Tasks.Add`（資料存取）。其中只有最後一行 `Created(...)` 真的屬於 HTTP。Controller 理想的樣子是反過來：

```csharp
// 目標形狀（第 7 章會完成）：只剩 HTTP 的部分
[HttpPost]
public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct)
{
    var task = await _taskService.CreateAsync(request, ct);
    return CreatedAtAction(nameof(GetByIdAsync), new { id = task.Id }, task);
}
```

規則在 Service 裡，action 只負責「收到請求、呼叫 Service、決定回哪個狀態碼」。這個分工叫做 Thin Controller，Service 層怎麼切、怎麼註冊，在 [[basics-07-dependency-injection-and-services]] 處理。

這裡有一個要先坦白的地方：本章的 `TasksController` 自己持有資料，也自己查詢和修改，違反了剛剛講的分工。這是刻意的。要先確定「請求能不能走到 action、結果能不能正確回去」，才有意義談資料放在哪。第六節會說明這個過渡版本的限制，並指出它在哪一章被取代。

---

## 二、建立 TasksController

### 2.1 從第 3 章的狀態開始

本章從 [[basics-03-first-project]] 結束時的 TaskTracker 出發：專案裡有 `PingController.cs`、`TaskTracker.Api.http`，`Program.cs` 已經包含 `AddControllers()` 與 `MapControllers()`。`/api/ping` 只是驗證管線用的，現在不再需要，先刪掉：

```powershell
Remove-Item src\TaskTracker.Api\Controllers\PingController.cs
Remove-Item src\TaskTracker.Api\TaskTracker.Api.http
```

`.http` 檔裡的請求打的是 `/api/ping`，本書統一用 `curl.exe`，所以一併刪除。`Program.cs` 這一章不需要改，裡面第一階段的 `AddControllers()` 登記了 Controller 相關服務，第二階段的 `MapControllers()` 把所有 Controller 的 action 登記成 endpoint，兩者就是本章需要的全部。

接著新增資料型別。規格把 Task 定義為四個欄位：`id`、`title`、`status`、`createdAt`。在 `src\TaskTracker.Api` 底下建立 `Entities` 資料夾，放兩個檔案：

```csharp
// Entities/TaskItemStatus.cs
using System.Text.Json.Serialization;

namespace TaskTracker.Api.Entities;

[JsonConverter(typeof(JsonStringEnumConverter<TaskItemStatus>))]
public enum TaskItemStatus
{
    [JsonStringEnumMemberName("todo")]
    Todo,

    [JsonStringEnumMemberName("done")]
    Done
}
```

```csharp
// Entities/TaskItem.cs
namespace TaskTracker.Api.Entities;

public class TaskItem
{
    public Guid Id { get; set; }

    public string Title { get; set; } = string.Empty;

    public TaskItemStatus Status { get; set; }

    public DateTimeOffset CreatedAt { get; set; }
}
```

規格要求 `status` 在 JSON 裡是小寫字串 `"todo"` 或 `"done"`，而 C# 慣例的 enum 成員是 PascalCase。`JsonStringEnumConverter<T>` 讓 enum 以字串而非數字出現在 JSON 裡，`JsonStringEnumMemberName` 指定每個成員對外的字串（這個 attribute 需要 .NET 9 以上）。JSON 的外觀由這兩個 attribute 決定，C# 內部的命名不受影響。

名稱叫 `TaskItem` 而不是 `Task`，是為了避開 `System.Threading.Tasks.Task`；同一個檔案裡出現 `Task` 會讓讀者和編譯器都得花力氣分辨。`TaskItem` 同時扮演資料模型、請求內容和回應內容三個角色，這在下一章之後就會拆開，現在先承受這個簡化。

### 2.2 Controller 骨架

在 `Controllers` 資料夾新增 `TasksController.cs`。先看類別宣告和資料來源：

```csharp
using Microsoft.AspNetCore.Mvc;
using TaskTracker.Api.Entities;

namespace TaskTracker.Api.Controllers;

[ApiController]
[Route("api/tasks")]
public class TasksController : ControllerBase
{
    // 暫時的資料來源：static List 不是 thread-safe，第 7 章移進 Service，第 10 章換成資料庫
    private static readonly List<TaskItem> Tasks =
    [
        new() { Id = Guid.Parse("11111111-1111-1111-1111-111111111111"), Title = "Read chapter 4", Status = TaskItemStatus.Done, CreatedAt = new DateTimeOffset(2026, 10, 1, 9, 0, 0, TimeSpan.Zero) },
        new() { Id = Guid.Parse("22222222-2222-2222-2222-222222222222"), Title = "Write the first controller", Status = TaskItemStatus.Todo, CreatedAt = new DateTimeOffset(2026, 10, 2, 9, 0, 0, TimeSpan.Zero) },
        new() { Id = Guid.Parse("33333333-3333-3333-3333-333333333333"), Title = "Try the PUT endpoint", Status = TaskItemStatus.Todo, CreatedAt = new DateTimeOffset(2026, 10, 3, 9, 0, 0, TimeSpan.Zero) }
    ];
```

這個類別宣告帶了三個值得停下來看的東西：`ControllerBase`、`[ApiController]`、`[Route]`。前兩個在這一節講，`[Route]` 留給下一節。

`ControllerBase` 是所有 Web API Controller 的基底類別。它提供三類東西：和當前請求有關的屬性（`Request`、`Response`、`HttpContext`、`User`、`ModelState`），產生結果物件的 helper 方法（`Ok()`、`NotFound()`、`CreatedAtAction()`、`NoContent()` 等），以及用 route 資訊產生 URL 的工具（`Url`）。MVC 另有一個叫 `Controller` 的類別，繼承自 `ControllerBase` 再加上 View 的支援，用在回傳 HTML 頁面的網站。Web API 沒有 View，繼承 `ControllerBase` 就夠，也避免帶進用不到的功能。

框架如何找到這些類別：`MapControllers()` 所依賴的探索機制會掃描專案，把類別名稱以 `Controller` 結尾的類別視為 Controller，把裡面的 public 方法登記成 endpoint。所以類別名稱的 `Controller` 結尾是約定，沒有這個結尾（也沒有 `[Controller]` attribute）的類別不會被當成 Controller。

`[ApiController]` 比看起來做得多。它啟用一組只對 API 有意義的行為：

- 要求使用 attribute routing。有這個 attribute 的 Controller 不能再依賴傳統的集中式路由設定，路徑必須寫在 `[Route]` 與 `[HttpGet]` 這類 attribute 上。
- 模型驗證失敗時自動回 400，body 是 `ValidationProblemDetails`，不需要在每個 action 開頭寫 `if (!ModelState.IsValid)`。
- 依參數型別自動推斷資料來源：複雜型別（像 `TaskItem`）預設從請求 body 讀 JSON，簡單型別（像 `Guid id`）從路由或查詢字串讀。
- 把沒有 body 的 4xx 結果（像 `NotFound()`）轉成 `ProblemDetails` 格式。

最後一項就是開場那兩個 404 的差別。`NotFound()` 本身只代表「狀態碼 404」，是 `[ApiController]` 把它補成 `application/problem+json`。請求若在路由階段就落空，沒有 action 被執行，這個轉換就不會發生。

自動 400 與來源推斷的細節、各種失敗的樣子，是 [[basics-05-model-binding-and-validation]] 的主題。本章的程式碼只在兩個地方依賴它：POST 和 PUT 的 `TaskItem input` 參數會被推斷成 `[FromBody]`，以及錯誤回應會是 ProblemDetails。

---

## 三、Attribute Routing：路徑寫在 action 旁邊

### 3.1 兩層 attribute 組成一條路徑

`TasksController` 的類別上有 `[Route("api/tasks")]`，每個 action 再用 `[HttpGet]`、`[HttpPost]` 等 attribute 宣告自己的 HTTP method 和路徑片段。兩者會串接起來：

```csharp
    [HttpGet]
    public ActionResult<IEnumerable<TaskItem>> GetAll() => Ok(Tasks);

    [HttpGet("{id:guid}")]
    public ActionResult<TaskItem> GetById(Guid id)
    {
        var task = Tasks.FirstOrDefault(t => t.Id == id);
        return task is null ? NotFound() : Ok(task);
    }
```

`GetAll` 的 `[HttpGet]` 沒有帶片段，完整路徑就是 `api/tasks`；`GetById` 的片段 `{id:guid}` 接在後面，完整路徑是 `api/tasks/{id:guid}`。花括號包起來的是路由參數，請求的對應片段會被取出來，依名稱交給同名的 action 參數，所以 `Guid id` 拿到的是網址裡 `tasks/` 後面那一段。

到這裡，[[basics-02-rest-api-design]] 規格表的五支端點可以逐一對應到 attribute：

| 規格 | Attribute | Action |
| --- | --- | --- |
| `GET /api/tasks` | `[HttpGet]` | `GetAll` |
| `GET /api/tasks/{id}` | `[HttpGet("{id:guid}")]` | `GetById` |
| `POST /api/tasks` | `[HttpPost]` | `Create` |
| `PUT /api/tasks/{id}` | `[HttpPut("{id:guid}")]` | `Update` |
| `DELETE /api/tasks/{id}` | `[HttpDelete("{id:guid}")]` | `Delete` |

規格是設計文件，attribute 是它的程式碼版本。以後規格改了，改的就是這些 attribute；反過來說，只要 attribute 是對的，路徑和 method 就是規格要求的那一組。方法名稱（`GetAll`、`Create`）在 attribute routing 下不影響網址，取名的重點是讓閱讀者看得懂。

### 3.2 `[controller]` token：方便，但把類別名稱綁進了網址

`[Route("api/tasks")]` 是把路徑寫死的版本。另一種常見寫法是用 token：

```csharp
[Route("api/[controller]")]
```

框架會把 `[controller]` 換成類別名稱去掉 `Controller` 後綴的部分。不少教學文章會寫成換成小寫的 `tasks`，實測不是這樣。把 TaskTracker 的 `[Route]` 改成 `api/[controller]` 後新增一筆任務，回應是：

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 13:52:05 GMT
Server: Kestrel
Location: http://localhost:5080/api/Tasks/59ccc09b-3088-4e67-be53-d7ed650011ed
Transfer-Encoding: chunked

{"id":"59ccc09b-3088-4e67-be53-d7ed650011ed","title":"Fixed","status":"todo","createdAt":"2026-10-31T13:52:06.428425+00:00"}
```

`Location` 裡是 `/api/Tasks/...`，大寫 T。token 展開的結果保留類別名稱的原樣大小寫，也就是 PascalCase。

那是不是代表打 `/api/tasks`（小寫）會 404？也不會。同一個程式用小寫和全大寫都打得通：

```powershell
curl.exe -s -o NUL -w "%{http_code}\n" http://localhost:5080/API/TASKS
```

```text
200
```

路由比對不分大小寫，大小寫只影響「框架自己產生的網址」：`Location` 標頭、OpenAPI 文件裡的 path。前端若拿 `Location` 的值去比對字串，才會踩到大小寫的差異。ASP.NET Core 提供 `RouteOptions.LowercaseUrls = true` 讓產生的網址一律小寫（它不改變比對行為，也不會在 `OrderItems` 之間插入連字號，得到的是 `orderitems`）。要產生 `order-items` 這種連字號形式，需要自訂 token transformer，而且它會真的改掉路由模式，原本的 `/api/OrderItems` 就變成 404，是一次 breaking change。

這引出 token 最大的問題：它把類別名稱和對外網址綁在一起。某天有人覺得 `TasksController` 取得不夠精確，重構成 `TaskItemsController`，網址就悄悄跟著變，所有呼叫端一起壞，編譯器和單元測試都不會抗議。對外契約應該由規格決定，不該由重構決定。所以 TaskTracker 全部用字面值：`[Route("api/tasks")]`。改類別名稱不會影響網址，網址變更必須動到這行 attribute，在 code review 裡一眼看得見。

網址用小寫、集合用複數名詞，是 [[basics-02-rest-api-design]] 的設計原則，字面值寫法剛好滿足。路由的優先序、`Order` 屬性與 URL 產生的其他細節，見 [[03-routing-and-endpoints]]。

### 3.3 `{id:guid}`：constraint 是用來選路由，不是用來驗證

`{id:guid}` 冒號後面的 `guid` 是 route constraint（路由限制）。它的作用是：請求的這一段如果不是合法的 GUID 格式，這個 endpoint 視為「不匹配」。第一個例子裡的 `/api/tasks/abc` 就是這樣：`abc` 不是 GUID，`GetById` 這條路由不成立；框架接著看有沒有別的 endpoint 能處理，沒有，回 404，而且沒有任何程式碼被執行，所以沒有 body。

這是「constraint 不是驗證」的核心。驗證的意思是「請求收到了，內容有問題，告訴呼叫端哪裡錯」，所以應該回 400 加上錯誤說明。constraint 的意思是「這條路由適不適用於這個網址」，不適用就當它不存在。規格表第 6.3 節把 `{id}` 不是 GUID 訂為 404，也就是在說：TaskTracker 刻意把這種請求視為「根本沒有這個資源」。

那為什麼還需要 constraint？因為它在兩條路由競爭同一個網址時有決定性的用途。假設以後加一條 `GET /api/tasks/search`，而 `{id}` 沒有限制：`/api/tasks/search` 同時符合字面路由和 `{id}`，雖然框架有優先序規則（字面值勝過參數），但路徑一多就難以推理。有了 `{id:guid}`，`search` 因為不是 GUID 直接排除在外，兩條路由不可能衝突。這是 constraint 的本業：消歧義。

如果團隊希望格式錯誤回 400 並說明原因，做法是把 constraint 拿掉，讓參數用字串（或 `Guid`，由 model binding 解析）進來，在 [[basics-05-model-binding-and-validation]] 的流程裡產生 400。這是設計選擇，取捨在於前端看到 404 會以為資源不存在，看到 400 才知道是自己傳錯格式。TaskTracker 選前者，因為 GUID 本來就不是人手打的，幾乎只會是程式拼接出錯。

其他常用的 constraint 有 `:int`、`:bool`、`:minlength(4)`、`:regex(...)`，數值範圍可寫成 `{id:int:min(1)}`。常見的範例會在 action 裡手寫 `if (id <= 0) return BadRequest();`，這種檢查要嘛改成 `min(1)`（同樣產生 404），要嘛交給驗證機制（產生 400），不要和路由設計混在 action 裡。

### 3.4 路徑對、method 錯：405，而且會告訴你可以用什麼

路徑存在但 method 不支援，框架回 405 而不是 404。對只有 GET、PUT、DELETE 的 `/api/tasks/{id}` 送 PATCH：

```powershell
curl.exe -s -i -X PATCH http://localhost:5080/api/tasks/11111111-1111-1111-1111-111111111111
```

```text
HTTP/1.1 405 Method Not Allowed
Content-Length: 0
Date: Sat, 31 Oct 2026 13:51:44 GMT
Server: Kestrel
Allow: DELETE, GET, PUT
```

`Allow` 標頭列出這個路徑支援的 method，是 HTTP 規範要求 405 必須附帶的資訊。所以前端遇到 405，不用猜：看 `Allow` 就知道該用哪個 method。這個回應和 `abc` 的 404 一樣，是路由階段決定的，沒有 body。

順帶一提，結尾多一條斜線的網址（`/api/tasks/`）在這個專案實測也回 200，與 `/api/tasks` 是同一個 endpoint，不需要特別處理。

---

## 四、Action 的回傳型別

### 4.1 為什麼不直接回傳資料

最直覺的 action 寫法是直接回傳要給呼叫端的資料：`public TaskItem GetById(Guid id)`。它能動，缺點在於 HTTP 回應不只有 body：還有狀態碼。「找不到」要回 404，「建立成功」要回 201 並附 `Location`，「刪除成功」要回 204 沒有 body。如果回傳型別只能是 `TaskItem`，找不到的時候只能丟例外或回 `null`（框架會把 `null` 變成 204，與「刪除成功」混在一起），規格表裡的狀態碼就無法表達。

所以 action 回傳的應該是「結果」，一個描述「回什麼狀態碼、帶什麼內容」的物件。這個物件的介面是 `IActionResult`，`Ok(task)`、`NotFound()`、`NoContent()` 這些 `ControllerBase` 的 helper 方法，都是在建立它的實作類別。

### 4.2 `IActionResult` 與 `ActionResult<T>`

TaskTracker 的 action 用了兩種回傳型別：

```csharp
public ActionResult<TaskItem> GetById(Guid id) // 讀取、新增、更新
public IActionResult Delete(Guid id) // 刪除
```

兩者的差別在於是否宣告「成功時 body 是什麼型別」。`Delete` 成功時 204 沒有 body，不需要型別，用 `IActionResult` 即可。其他四支端點成功時都回 `TaskItem`（或其集合），用 `ActionResult<T>` 把這件事寫進方法簽章。

`ActionResult<T>` 比 `IActionResult` 好的地方有三個：

第一，簽章本身就是文件。讀程式的人看到 `ActionResult<TaskItem>` 就知道成功路徑回什麼，不必讀完 action 內容。

第二，工具讀得到這個型別。把 TaskTracker 的 OpenAPI 文件（`/openapi/v1.json`）打開來看：`GET /api/tasks/{id}` 的 200 回應 schema 指向 `TaskItem`，`GET /api/tasks` 是 `TaskItem` 的陣列；而 `DELETE` 這支用 `IActionResult`，200 回應沒有任何 body 型別。前端產生 client 程式碼、或同事查文件時，差別立刻看得出來。

第三，成功路徑可以直接回傳資料本身。`ActionResult<T>` 允許兩種寫法：`return task;`（隱含 200）和 `return NotFound();`（任何 `ActionResult`）。前者在編譯期確認型別是 `T`；後者保留了回傳其他狀態碼的彈性。如果用 `T` 當回傳型別，只有第一種寫法；用 `IActionResult`，兩種都可以但編譯器不檢查 body 型別。

需要修正一個常見的說法：「ActionResult<T> 讓編譯器擋住回錯型別的 body」只對 `return task;` 這種直接回傳成立。`return Ok(whatever)` 仍然能編譯，因為 `OkObjectResult` 是 `ActionResult` 的一種，body 是 `object`，編譯器不檢查。所以 `ActionResult<T>` 的價值主要在於文件與工具，不是嚴格的型別安全。

同一份 OpenAPI 也顯示一個限制：文件裡 `POST` 的回應是 200、`DELETE` 也是 200，與實際的 201、204 不符，404 完全沒出現。回傳型別只能推斷出 body 的形狀，沒辦法知道 action 內部有哪些 `return` 分支。要讓文件準確，需要用 `[ProducesResponseType]` 明確宣告，這在 [[basics-14-openapi-and-versioning]] 補上。

### 4.3 helper 方法對回規格表

`ControllerBase` 的 helper 方法和 [[basics-02-rest-api-design]] 的狀態碼是一對一的：

| 規格的回應 | 呼叫 | 用在 |
| --- | --- | --- |
| `200`，帶 body | `Ok(task)` | 讀取、更新成功 |
| `201`，帶 body 與 `Location` | `CreatedAtAction(...)` | 新增成功 |
| `204`，無 body | `NoContent()` | 刪除成功 |
| `404` | `NotFound()` | 讀取、更新、刪除時 id 不存在 |

你不需要背 helper 的名字：IDE 裡輸入 `return ` 觸發自動完成，`ControllerBase` 提供的所有結果方法都會列出來，名稱就是狀態碼的英文名稱。

### 4.4 `CreatedAtAction`：告訴呼叫端新資源在哪裡

這四個 helper 中，`CreatedAtAction` 的參數最多，也最容易用錯。看 `Create` 這個 action：

```csharp
    [HttpPost]
    public ActionResult<TaskItem> Create(TaskItem input)
    {
        var task = new TaskItem
        {
            Id = Guid.NewGuid(),
            Title = input.Title,
            Status = TaskItemStatus.Todo,
            CreatedAt = DateTimeOffset.UtcNow
        };
        Tasks.Add(task);
        return CreatedAtAction(nameof(GetById), new { id = task.Id }, task);
    }
```

action 內容先建立一個新的 `TaskItem`：`Id`、`Status`、`CreatedAt` 由伺服器決定（規格表 6.1 的「誰決定」欄），只有 `Title` 取自請求。這也是為什麼不能直接把請求物件加進列表。`CreatedAtAction` 的三個參數各有分工：

- 第一個參數是「查詢這個資源要呼叫哪個 action」。這裡指向 `GetById`。
- 第二個參數 `new { id = task.Id }` 是填進那個 action 路由模板裡的值。`GetById` 的模板是 `api/tasks/{id:guid}`，`id` 填入後得到完整網址。
- 第三個參數是回應 body，也就是剛建立的任務。

框架用前兩個參數反推出 URL，放進 `Location` 標頭，狀態碼設為 201。好處是 URL 不是手動拼的字串：以後 `GetById` 的路徑變了，`Location` 自動跟著變。用 `nameof(GetById)` 而不是 `"GetById"`，則讓 IDE 的重新命名能連動這裡。

對照 [[basics-02-rest-api-design]] 的 POST 規格：`201`，Task，`Location` 指向新任務。三個條件都由這一行滿足。

### 4.5 陷阱：方法名稱加 Async 後綴，`CreatedAtAction` 就會 500

`nameof(GetById)` 的寫法有一個很容易在下一階段踩到的陷阱。團隊規範通常要求 I/O 方法一律加 `Async` 後綴（本書從 [[basics-07-dependency-injection-and-services]] 起也這樣做）。假設在改成非同步時把 `GetById` 改名為 `GetByIdAsync`，同時 `nameof(GetById)` 也被 IDE 一起改成 `nameof(GetByIdAsync)`。編譯沒問題，一切看起來合理。

在 TaskTracker 上實際試一次。把 `GetById` 改名為 `GetByIdAsync`（方法本體不動，回傳型別也維持同步，後面會說明為什麼不影響結論），然後 POST（送 JSON 的寫法為什麼要這樣包，5.2 節會說明）：

```powershell
'{"title":"Async suffix"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 500 Internal Server Error
Content-Type: text/plain; charset=utf-8
Date: Sat, 31 Oct 2026 13:51:44 GMT
Server: Kestrel
Transfer-Encoding: chunked

System.InvalidOperationException: No route matches the supplied values.
   at Microsoft.AspNetCore.Mvc.CreatedAtActionResult.OnFormatting(ActionContext context)
   at Microsoft.AspNetCore.Mvc.Infrastructure.ObjectResultExecutor.ExecuteAsyncCore(ActionContext context, ObjectResult result, Type objectType, Object value)
   ...
```

500，錯誤訊息是「沒有路由符合提供的值」。更糟的是接著看資料：

```powershell
curl.exe -s http://localhost:5080/api/tasks
```

```text
[{"id":"11111111-...","title":"Read chapter 4",...},{"id":"22222222-...",...},{"id":"33333333-...",...},{"id":"8dede8d2-1491-484e-bb8b-ea6330b5e6ba","title":"Async suffix","status":"todo","createdAt":"2026-10-31T13:51:44.9671125+00:00"}]
```

（`...` 為省略。）新任務在列表裡。失敗發生在 action 已經執行完、資料已經寫入之後的「組出回應」階段，呼叫端看到 500，不知道資源已經建立，很自然會重試，結果建出一筆重複的資料。接上資料庫之後，這代表資料庫裡多了一筆呼叫端不知情的資料。

原因是框架在登記 action 時，預設會把名稱結尾的 `Async` 拿掉，登記的名稱是 `GetById`。`nameof(GetByIdAsync)` 產生字串 `"GetByIdAsync"`，在登記表裡找不到，於是丟出例外。這個移除只看名稱，不看方法是否真的非同步，所以上面刻意保持同步的方法也會中招。這個行為由 `MvcOptions.SuppressAsyncSuffixInActionNames` 控制，預設 `true`，目的是讓 `Async` 這個實作細節不出現在 action 的名稱裡。

有三種解法，各有取捨：

1. 全域關掉後綴移除。這是 TaskTracker 採用的做法（第 7 章加入）：

   ```csharp
   builder.Services.AddControllers(options =>
   {
       options.SuppressAsyncSuffixInActionNames = false;
   });
   ```

   登記名稱保留 `GetByIdAsync`，`nameof(GetByIdAsync)` 對得上，仍然受重新命名保護。把上面失敗的實驗加上這個設定，同一個 POST 就成功：

   ```text
   HTTP/1.1 201 Created
   Content-Type: application/json; charset=utf-8
   Date: Sat, 31 Oct 2026 13:52:05 GMT
   Server: Kestrel
   Location: http://localhost:5080/api/Tasks/59ccc09b-3088-4e67-be53-d7ed650011ed
   Transfer-Encoding: chunked
   ```

   代價是方向相反的失敗：之後如果有人在別處寫字串 `"GetById"`，反而找不到。換設定時要整批檢查字串寫法的呼叫。（上面的 `Location` 是 `/api/Tasks/...`，因為該實驗同時把路由換成了 `[controller]` token，與第 3.2 節同一次執行。）

2. 改用路由名稱。在 GET 上指定 `Name`，用 `CreatedAtRoute` 取代 `CreatedAtAction`：

   ```csharp
   [HttpGet("{id:guid}", Name = "GetTaskById")]
   public ActionResult<TaskItem> GetByIdAsync(Guid id) { /* ... */ }

   return CreatedAtRoute("GetTaskById", new { id = task.Id }, task);
   ```

   路由名稱不受後綴開關影響。缺點是名稱要全域唯一；日後做 API 版本時，不同版本的 Controller 不能共用同一個名稱。

3. 不用 `nameof`，直接寫 `"GetById"` 字串。預設設定下能動，但失去重構保護，改名時不會有人提醒你。

TaskTracker 選第一種：寫程式的人不需要記住任何特殊規則，`nameof` 的保護也保留。無論選哪一種，重點是專案裡只能有一種，團隊在 code review 時才有明確的依據。本章的 action 都是同步的，沒有 `Async` 後綴，所以最終版的 `Program.cs` 暫時不需要這個設定。

---

## 五、完整的 Controller，以及每支端點的實際回應

### 5.1 其餘三個 action

前面看了 `GetAll`、`GetById`、`Create`。`Update` 與 `Delete` 的寫法有同樣的結構：先找資源，找不到回 404，找到就動手並回成功結果。

```csharp
    [HttpPut("{id:guid}")]
    public ActionResult<TaskItem> Update(Guid id, TaskItem input)
    {
        var task = Tasks.FirstOrDefault(t => t.Id == id);
        if (task is null)
        {
            return NotFound();
        }

        task.Title = input.Title;
        task.Status = input.Status;
        return Ok(task);
    }

    [HttpDelete("{id:guid}")]
    public IActionResult Delete(Guid id)
    {
        var task = Tasks.FirstOrDefault(t => t.Id == id);
        if (task is null)
        {
            return NotFound();
        }

        Tasks.Remove(task);
        return NoContent();
    }
}
```

`Update` 有兩個參數：`Guid id` 從路由的 `{id}` 來，`TaskItem input` 因為 `[ApiController]` 的推斷從 body 來。`Update` 只改 `Title` 和 `Status`，`Id` 與 `CreatedAt` 維持原樣，這符合規格裡「建立後不變」的欄位。`Delete` 沒有 body，用 `IActionResult`。

### 5.2 啟動並逐一測試

從 solution 根目錄啟動：

```powershell
dotnet build
dotnet run --project src/TaskTracker.Api --launch-profile http
```

另開一個 PowerShell 視窗打 API。以下輸出都是在 Windows PowerShell 5.1 以 `curl.exe` 實際執行的結果（時間與 GUID 每次不同）。

讀取全部任務：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:25 GMT
Server: Kestrel
Transfer-Encoding: chunked

[{"id":"11111111-1111-1111-1111-111111111111","title":"Read chapter 4","status":"done","createdAt":"2026-10-01T09:00:00+00:00"},{"id":"22222222-2222-2222-2222-222222222222","title":"Write the first controller","status":"todo","createdAt":"2026-10-02T09:00:00+00:00"},{"id":"33333333-3333-3333-3333-333333333333","title":"Try the PUT endpoint","status":"todo","createdAt":"2026-10-03T09:00:00+00:00"}]
```

欄位名稱是小寫開頭的 camelCase，`status` 是小寫字串，都符合規格。這是 ASP.NET Core 預設的 JSON 命名，加上前面 enum 的設定，不需要在 Controller 裡處理。注意這裡回的是陣列；規格裡 `GET /api/tasks` 要回的是附帶 `page`、`totalCount` 的物件，那需要查詢參數與分頁，在下一章加入。

讀取單一任務，id 存在：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks/11111111-1111-1111-1111-111111111111
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:25 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"id":"11111111-1111-1111-1111-111111111111","title":"Read chapter 4","status":"done","createdAt":"2026-10-01T09:00:00+00:00"}
```

id 不存在，以及 id 不是 GUID 的兩種 404，在本章開頭已經看過。

新增任務。Windows PowerShell 5.1 把含雙引號的字串傳給外部程式時會吃掉引號，直接 `-d '{"title":"x"}'` 會送出壞掉的 JSON。穩當的做法是用管線把 JSON 送進 stdin，再用 `-d '@-'` 讓 curl 從 stdin 讀。這個寫法在 PowerShell 7 也能用：

```powershell
'{"title":"Write chapter 4"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:27 GMT
Server: Kestrel
Location: http://localhost:5080/api/tasks/431cf864-f2ba-4241-9b6c-e3ef97df77c1
Transfer-Encoding: chunked

{"id":"431cf864-f2ba-4241-9b6c-e3ef97df77c1","title":"Write chapter 4","status":"todo","createdAt":"2026-10-30T14:19:28.2956432+00:00"}
```

201、`Location`、完整的新任務，規格要求的三件事都到位。把 `id` 存進變數，用 `Location` 指向的網址讀回來，確認它真的能被找到（以下 `$newId` 請換成你自己拿到的 id）：

```powershell
$newId = "431cf864-f2ba-4241-9b6c-e3ef97df77c1"
curl.exe -s -i "http://localhost:5080/api/tasks/$newId"
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:28 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"id":"431cf864-f2ba-4241-9b6c-e3ef97df77c1","title":"Write chapter 4","status":"todo","createdAt":"2026-10-30T14:19:28.2956432+00:00"}
```

整筆更新：

```powershell
'{"title":"Write chapter 4 (done)","status":"done"}' | curl.exe -s -i -X PUT "http://localhost:5080/api/tasks/$newId" -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:34 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"id":"431cf864-f2ba-4241-9b6c-e3ef97df77c1","title":"Write chapter 4 (done)","status":"done","createdAt":"2026-10-30T14:19:28.2956432+00:00"}
```

`id` 和 `createdAt` 沒變，`title` 與 `status` 更新了。對不存在的 id 做同樣的 PUT 會得到 404（同樣是 `application/problem+json`）。

刪除，然後再刪一次：

```powershell
curl.exe -s -i -X DELETE "http://localhost:5080/api/tasks/$newId"
```

```text
HTTP/1.1 204 No Content
Date: Fri, 30 Oct 2026 14:19:34 GMT
Server: Kestrel
```

```powershell
curl.exe -s -i -X DELETE "http://localhost:5080/api/tasks/$newId"
```

```text
HTTP/1.1 404 Not Found
Content-Type: application/problem+json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:35 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.5","title":"Not Found","status":404,"traceId":"00-f3146ffad0ba6f3b1ed74bc5f1cb5a5e-7262a98843b6b255-00"}
```

第一次 204 沒有 body，第二次因為資源已經不在，回 404。這是規格表 6.3 的行為：刪除一個不存在的任務是 404，而不是假裝成功。（DELETE 在 HTTP 語意上是冪等的，意思是「做一次和做很多次，伺服器狀態相同」，不代表每次都要回同一個狀態碼。）

### 5.3 `[ApiController]` 已經替我們擋掉的壞請求

有幾種壞請求，Controller 的程式一行都沒寫，卻已經有合理的回應。送一個壞掉的 JSON：

```powershell
'{"title":' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:31 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.1","title":"One or more validation errors occurred.","status":400,"errors":{"input":["The input field is required."],"$.title":["Expected depth to be zero at the end of the JSON payload. There is an open JSON object or array that should be closed. Path: $.title | LineNumber: 0 | BytePositionInLine: 9."]},"traceId":"00-4369aba7a5f8de524207668fbeaeb3f7-a3afa009cc1ea746-00"}
```

400，`errors` 欄位指出問題在 `$.title`。把 `status` 傳成不合法的列舉值也是 400：

```powershell
'{"title":"x","status":"archived"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:32 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.1","title":"One or more validation errors occurred.","status":400,"errors":{"input":["The input field is required."],"$.status":["The JSON value could not be converted to TaskTracker.Api.Entities.TaskItemStatus. Path: $.status | LineNumber: 0 | BytePositionInLine: 32."]},"traceId":"00-5d476230bdca816cfe6299f0c0817ea4-c2e176d8b1662b2b-00"}
```

Content-Type 不是 JSON，則是 415：

```powershell
curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: text/plain" -d 'title=hello'
```

```text
HTTP/1.1 415 Unsupported Media Type
Content-Type: application/problem+json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:33 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.16","title":"Unsupported Media Type","status":415,"traceId":"00-6074f552ac6eb0d3978c926af69ac8ed-338a874076c2423b-00"}
```

這三種都對應規格表 6.3：格式錯誤的 JSON 或型別不符是 400，Content-Type 不對是 415。這些是 body 還沒進入 action 前就被擋下的情況，所以不需要寫任何驗證程式。

### 5.4 還沒擋住的

同樣有幾種請求，現在會被默默接受。夾帶不該由呼叫端決定的欄位：

```powershell
'{"id":"00000000-0000-0000-0000-000000000001","title":"Over-posted","status":"done","createdAt":"1999-01-01T00:00:00Z"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:29 GMT
Server: Kestrel
Location: http://localhost:5080/api/tasks/64464d4d-854c-4cb0-9a23-1c3ad6936413
Transfer-Encoding: chunked

{"id":"64464d4d-854c-4cb0-9a23-1c3ad6936413","title":"Over-posted","status":"todo","createdAt":"2026-10-30T14:19:29.8640092+00:00"}
```

呼叫端傳了 `id`、`status`、`createdAt`，回應裡全被伺服器自己的值取代。這靠 `Create` 裡手動指定每個欄位才擋得住，只要有人哪天偷懶寫成 `Tasks.Add(input)`，呼叫端就能決定自己的 `id`、`createdAt`。這個問題叫 over-posting（過度提交），根本的解法是讓請求使用另一個只含 `title` 的型別，在 [[basics-06-dto-design]] 處理。

送一個空物件：

```powershell
'{}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Fri, 30 Oct 2026 14:19:30 GMT
Server: Kestrel
Location: http://localhost:5080/api/tasks/6f91f7a8-b0cf-4e2a-8eaa-b1aea1148587
Transfer-Encoding: chunked

{"id":"6f91f7a8-b0cf-4e2a-8eaa-b1aea1148587","title":"","status":"todo","createdAt":"2026-10-30T14:19:30.5136237+00:00"}
```

標題是空字串的任務被建立了，違反規格「必填，1 到 100 字元」。原因是 `Title` 預設值是 `string.Empty`，缺少欄位時不會觸發任何錯誤。同理，PUT 若漏掉 `status`，`Status` 會變成 enum 的預設值，也就是第一個成員 `Todo`，一個已完成的任務就這樣被默默改回 `todo`。這兩個問題都屬於輸入驗證，由 [[basics-05-model-binding-and-validation]] 解決。

這一節的目的是讓你知道目前的邊界在哪：路由與格式層面，框架幫你守住了；「內容合不合理」仍然是空的。

---

## 六、記憶體資料庫：過渡版本的限制

整個 `TasksController` 的資料放在 `private static readonly List<TaskItem> Tasks`。選它純粹是為了讓本章專注在 Controller 和 routing，沒有任何需要安裝或設定的東西。但它只是過渡，在真實環境裡會在三個地方出錯。

第一，重啟就消失。`static` 欄位存在於處理程序（process）的記憶體裡，程序結束，資料跟著消失。實測：新增一筆任務後列表有 4 筆；停掉再重新啟動，回到只剩 3 筆初始資料。部署一個新版本、容器被重啟、機器重開機，都會讓使用者的任務憑空消失。

第二，多副本會各說各話。正式環境為了可用性，通常會同時跑多個副本（例如 K8s 裡的多個 Pod），負載平衡器把請求輪流分給它們。每個副本有自己的 `Tasks`。使用者對副本 A 發出 `POST` 建立任務，接著對副本 B 發 `GET` 讀取，B 的記憶體裡沒有這筆資料，回 404。症狀是時好時壞，取決於這次請求被分到哪個副本，這類 bug 在單機開發時永遠重現不了。

第三，並行存取會出錯。Kestrel 同時在多個執行緒上處理請求，`List<T>` 不是 thread-safe：兩個請求同時 `Add`，內部陣列可能被覆蓋或擴充到一半，結果是資料遺失，甚至丟出例外。本章的程式碼在一個人手動依序測試時不會出事，並行才會。換成加鎖可以解決這一點，但前兩個問題還在，而且鎖只在單一程序內有效，所以治標不治本。

資料必須放進獨立於 API 程序之外的儲存體，才能在重啟、多副本、並行下都正確。路線是：[[basics-07-dependency-injection-and-services]] 先把資料從 Controller 搬進 Service（Controller 才真的變薄），[[basics-10-efcore-and-oracle]] 再把 Service 背後換成 Oracle 資料庫。到那時 Controller 的 action 不需要因為儲存體換了而改動，這也是現在就先把「Controller 負責 HTTP」想清楚的原因。

---

## 常見誤解

**「`[Route("api/[controller]")]` 會展開成小寫的 `api/users`，打錯大小寫會 404。」** 實測展開的結果保留類別名稱的大小寫（`api/Users`），而路由比對不分大小寫，`/api/users`、`/API/USERS` 都能打通。大小寫只影響框架產生的網址，如 `Location` 標頭與 OpenAPI 的 path。

**「`{id:guid}` 這類 constraint 會驗證輸入，格式錯誤會回 400。」** Constraint 的作用是決定這條路由適不適用。格式不符視為路由不匹配，結果通常是 404，而且 action 不會被執行，所以沒有 ProblemDetails body。需要 400 與錯誤說明，要靠 model binding 與驗證，不是 constraint。

**「`ActionResult<T>` 讓編譯器檢查所有回傳的型別。」** 只有直接 `return value;` 這種寫法會被檢查。`return Ok(任何物件)` 照樣編譯。它的價值是讓簽章說清楚成功時回什麼，並且讓 OpenAPI 等工具讀得到 body 型別；狀態碼仍需要另外用 `[ProducesResponseType]` 宣告。

**「方法加了 `Async` 後綴，`CreatedAtAction(nameof(...))` 自動就對得上。」** 預設設定下框架登記 action 時會移除 `Async` 後綴，`nameof(GetByIdAsync)` 找不到目標，回 500，而且資源已經建立。要設定 `SuppressAsyncSuffixInActionNames = false`，或改用路由名稱，或寫字串。

**「資料先放 `static List`，之後再換，反正功能一樣。」** 記憶體資料在重啟後消失、多副本互不相通、並行寫入不安全。功能看起來一樣，是因為開發時只有一個程序、一個人在測。

## 同事會來問你的問題

**Q：我的 action 只回傳資料，沒有狀態碼，為什麼還是能運作？**

如果 action 回傳的是一般物件，框架會把它當作 200 加上序列化後的 body；回傳 `null` 則是 204。所以簡單的查詢可以這樣寫，但只要需要區分 404、201 這類狀態，就必須回傳 `ActionResult<T>` 或 `IActionResult`。專案內統一用這兩種，比一部分直接回物件、一部分回結果物件，閱讀時不需要切換心智模型。

**Q：id 格式錯誤，應該回 400 還是 404？**

規格決定。TaskTracker 的規格選 404，因為 id 是程式產生的 GUID，格式不符可以視為路徑不存在，實作上用 `{id:guid}` 一行搞定。如果前端會讓使用者手動輸入 id，回 400 並說明「id 必須是 GUID」對使用者更友善，這時改用 model binding 驗證，不用 constraint。無論選哪一種，都要寫進規格，不要讓兩支端點各自不同。

**Q：路徑為什麼不用 `[controller]` token，不是比較少打字嗎？**

少打字的代價是類別名稱變成對外契約的一部分。重構時改類別名稱，網址會悄悄改變，呼叫端壞掉。字面值多打幾個字，換到的是「改網址必須動到這行 attribute」的保護。

**Q：`DELETE` 為什麼用 `IActionResult`，不是 `ActionResult<T>`？**

`ActionResult<T>` 的 `T` 代表成功時的 body 型別。DELETE 成功是 204，沒有 body，沒有型別可以填，所以用 `IActionResult`。

**Q：既然 `CreatedAtAction` 這麼容易踩坑，為什麼不直接手動寫 `Created("/api/tasks/" + id, task)`？**

可以，但字串拼出來的網址需要自己維護：路徑一改，所有手寫的地方都要跟著改，漏掉的不會有編譯錯誤。`CreatedAtAction` 讓網址由路由模板產生，路徑只有一個來源。本章第一節的反例用了手寫字串，那是反例的一部分。

## 這章的位置

讀完這章，你能把規格表的每一列對應到 attribute 與 action，說出 `ControllerBase` 與 `[ApiController]` 各提供什麼，解釋 route constraint 為什麼是 404 而不是 400，用 `ActionResult<T>` 與 `Ok`、`NotFound`、`CreatedAtAction`、`NoContent` 回出規格要求的狀態碼，並能在 `CreatedAtAction(nameof(...))` 回 500 時想到 `Async` 後綴。TaskTracker 現在有五支能用 `curl.exe` 呼叫的端點，只是資料在記憶體、輸入沒有驗證。

下一章 [[basics-05-model-binding-and-validation]] 處理輸入：請求裡的字串怎麼變成 C# 參數，不合法的輸入誰來擋。想看 routing 的比對優先序、URL 產生的細節，請讀深度篇 [[03-routing-and-endpoints]]；action 被選中之後 MVC 內部的 filter 流程，在 [[05-filters-and-mvc-internals]]。

---

## 連結

- 上一章：[[basics-03-first-project]]
- 下一章：[[basics-05-model-binding-and-validation]]
- 對應深度章：[[03-routing-and-endpoints]]、[[05-filters-and-mvc-internals]]
- 全書目錄：[[dotnet-web-api]]
