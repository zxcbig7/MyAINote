---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, dto, mapping, over-posting, record, automapper, taskTracker]
sources:
  - raw/Web Framework/NET Web API/Chapter 4：DTO 與資料模型設計.md
created: 2026-11-01
updated: 2026-11-01
---

# 入門第 06 章：DTO 設計 — 為什麼不能直接把 entity 回傳給前端

## 三個看起來都很省事的寫法，各自在不同時間點出事

[[basics-05-model-binding-and-validation]] 結束時，TaskTracker 的 controller 還在直接收發 `TaskItem`，也就是那個 entity。只有四個欄位的 entity 這樣做看不出問題，所以先換成一個比較接近真實專案的例子：一支使用者 API，entity 長這樣，action 直接收發它。

```csharp
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public bool IsAdmin { get; set; }
    public List<Project> Projects { get; set; } = [];
}

[HttpGet("{id}")]
public User Get(int id) => Users.First(x => x.Id == id);

[HttpPost]
public User Create(User user)
{
    user.Id = Users.Count + 1;
    Users.Add(user);
    return user;
}
```

第一個出事的時間點是讀取。前端要顯示使用者名稱，打 `GET /api/users/flat/1`（這是一個只複製純量欄位、不帶 `Projects` 的讀取端點）：

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"id":1,"name":"alice","email":"a@x.com","passwordHash":"$2a$11$abcdefghijklmnopqrstuv","isAdmin":false,"projects":[]}
```

`passwordHash` 出現在回應裡。沒有人寫程式要把它送出去；序列化器的規則是「公開屬性全部輸出」，entity 上有什麼，JSON 裡就有什麼。雜湊值不是明文，但它是離線暴力破解的原料，任何有權限看這個回應的人（或這個回應經過的 log、快取、瀏覽器擴充套件）都拿到了。

第二個時間點是關聯。`User` 有 `Projects`，`Project` 又有 `Owner` 指回 `User`。這在 EF Core 裡是正常的雙向導覽屬性，序列化時卻變成無窮迴圈：

```text
HTTP/1.1 500 Internal Server Error
Content-Type: text/plain; charset=utf-8
```

伺服器的 log 裡可以看到原因：

```text
System.Text.Json.JsonException: A possible object cycle was detected. This can either be due to a cycle or if the object depth is larger than the maximum allowed depth of 32. ... Path: $.Projects.Owner.Projects.Owner.Projects.Owner...
```

（省略了後面重複的 `Owner.Projects`。）這種錯誤最討厭的地方是它不會在開發初期出現：只有 `Projects` 裡真的有資料的使用者才會觸發，空清單的使用者一切正常。

第三個時間點是寫入。`POST /api/users` 的參數就是 `User`，一個想當管理員的人只要多送一個欄位：

```powershell
'{"name":"mallory","email":"m@x.com","isAdmin":true}' | curl.exe -s -i -X POST http://localhost:5080/api/users -H 'Content-Type: application/json' --data-binary '@-'
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"id":2,"name":"mallory","email":"m@x.com","passwordHash":"","isAdmin":true,"projects":[]}
```

`isAdmin` 變成 `true`。表單上本來就沒有這個欄位，所以前端程式、UI、驗證規則都沒有問題，但 HTTP 請求的內容由呼叫端決定，不由你的畫面決定。這類漏洞叫 over-posting（也稱 mass assignment）：model binding 看到 body 裡有屬性名稱對得上的欄位就填，不問這個欄位「該不該」由呼叫端設定。[[basics-05-model-binding-and-validation]] 的驗證屬性擋不住它，因為 `isAdmin: true` 是完全合法的布林值。

還有第四種出事方式，不會有任何錯誤訊息：資料庫同事把 `Title` 欄位改名為 `Name`，entity 跟著改，編譯通過，測試全綠，隔天前端發現所有任務標題都是空的，因為 JSON 裡的 `title` 消失了。

這四件事的共同原因是：API 的輸入輸出型別和資料庫模型是同一個型別，所以它們的命運綁在一起。本章要做的事，就是把兩者拆開，並讓 TaskTracker 完成這個拆分。

---

## 一、為什麼不能直接回傳 entity

資料在系統裡跨過好幾個邊界：瀏覽器到 API、API 內部的程式到資料庫。每個邊界兩側的需求不一樣。資料庫那一側關心的是怎麼存、怎麼查、怎麼維持一致性，所以 entity 會有密碼雜湊、軟刪除旗標、`RowVersion`、導覽屬性。呼叫端那一側關心的是這支 API 承諾了什麼：有哪些欄位、什麼名稱、什麼型別。承諾一旦發出去，前端程式碼、行動 App、第三方整合都會依賴它。

DTO（Data Transfer Object）就是這個承諾的 C# 形狀：一個只為了在邊界上搬運資料而存在、沒有行為的型別。它和 entity 的關係可以用一句話概括：entity 是內部模型，DTO 是對外契約，兩者不共用。把這句話拆成前面看到的四個問題：

- 洩漏：entity 的欄位預設全部對外。DTO 要明確寫出要給誰看的欄位，沒寫的就不存在於 JSON，連「忘了遮」的機會都沒有。這個方向是白名單，entity 直接回傳是黑名單（必須記得逐一遮掉），而黑名單遲早會漏一條。
- 迴圈與過量資料：導覽屬性是為了讓 EF Core 查詢方便，與 API 回應需要多深的物件圖無關。DTO 由你決定要帶哪些子資料、帶幾層。
- Over-posting：Request DTO 只宣告「這個端點允許呼叫端設定的欄位」。沒宣告的欄位物理上綁不進來。
- 耦合：欄位改名、拆表、改型別，改的是 entity 和 mapping 的那一行，API 契約不動。

有人會說這是大專案的做法，小專案直接回傳 entity 比較快。上面的例子沒有一個和專案大小有關：兩個欄位的 entity 也可能有 `PasswordHash`。更實際的理由是修正成本：API 一旦有人在用，改欄位就是 breaking change，而 entity 和 API 綁在一起的專案，每次資料庫異動都在冒險。

---

## 二、Request 與 Response 為什麼要分開

拆開 entity 與 DTO 之後，下一個問題是一個 DTO 夠不夠：既然 `TaskResponse` 有 `Id`、`Title`、`Status`、`CreatedAt`，用同一個型別收 `POST` 不就好了？

試著想一次。建立任務時，`Id` 與 `CreatedAt` 應該由伺服器決定，`Status` 固定是 `todo`，呼叫端只能提供 `Title`。若 Request 與 Response 共用型別，`Id`、`CreatedAt` 就成了「可以被呼叫端設定的欄位」，你得靠 controller 裡的程式碼記得忽略它們，這又回到黑名單思維。更新任務時呼叫端要送 `Title` 和 `Status`，不能送 `Id`（網址已經有了）和 `CreatedAt`（建立後不可變）。三個操作可寫入的欄位集合各不相同，卻都不等於可讀取的欄位集合。

所以 TaskTracker 的規則是一個操作一個 Request 型別，加上一個共用的 Response：

| 型別 | 用途 | 可由呼叫端設定的欄位 |
| --- | --- | --- |
| `CreateTaskRequest` | `POST /api/tasks` | `Title` |
| `UpdateTaskRequest` | `PUT /api/tasks/{id}` | `Title`、`Status` |
| `TaskResponse` | 所有回傳任務的端點 | 無（唯讀） |
| `PagedResponse<T>` | 清單端點的包裝 | 無（唯讀） |

有人會抱怨「Create 和 Update 的 `Title` 規則一樣，重複定義很煩」。重複是真的，但這兩份規則會分開演進的機率很高：更新時可能允許標題空白保留原值，建立時不行；某天加入 `Priority`，建立時選填、更新時必填。共用一個型別就得用一堆條件去區分情境。重複幾行屬性宣告的成本，比一個型別承擔兩種意圖的成本低得多。

### 命名

TaskTracker 的命名只有兩條：Request 以動詞開頭，`{動詞}{資源}Request`（`CreateTaskRequest`、`UpdateTaskRequest`）；Response 以資源開頭，`{資源}Response`（`TaskResponse`）。清單的包裝型別是 `PagedResponse<T>`，查詢字串的是 `TaskListQuery`。這個規則的目的是讓你只看型別名稱就知道方向和操作，所以不論採用哪一種慣例，重點是整個專案只用一種。常見的另一種慣例是 `{資源}CreateRequest`、`{資源}Response`（資源在前）。兩種都行，混用最糟，因為搜尋與自動完成的時候你不知道該用哪個前綴去找。

---

## 三、動手：把 TaskTracker 的 entity 拆出來

起點是 [[basics-05-model-binding-and-validation]] 結束時的 TaskTracker：`TasksController` 的 `Create` 與 `Update` 參數是 `TaskItem`，`GetAll` 回 `PagedResponse<TaskItem>`，`TaskItem` 上掛著 `[Required]` 與 `[StringLength(100)]`。這一節做五件事。

### 1. Request DTO

在 `src/TaskTracker.Api/Dtos/` 新增 `CreateTaskRequest.cs`：

```csharp
using System.ComponentModel.DataAnnotations;

namespace TaskTracker.Api.Dtos;

public sealed class CreateTaskRequest
{
    [Required]
    [StringLength(100)]
    public string Title { get; init; } = string.Empty;
}
```

同一個資料夾新增 `UpdateTaskRequest.cs`：

```csharp
using System.ComponentModel.DataAnnotations;
using TaskTracker.Api.Entities;

namespace TaskTracker.Api.Dtos;

public sealed class UpdateTaskRequest
{
    [Required]
    [StringLength(100)]
    public string Title { get; init; } = string.Empty;

    [Required]
    [EnumDataType(typeof(TaskItemStatus))]
    public TaskItemStatus? Status { get; init; }
}
```

兩個設計決定值得說明。`Status` 宣告成 `TaskItemStatus?`（可為 null）並加 `[Required]`，原因是 [[basics-05-model-binding-and-validation]] 末尾遺留的問題：不可為 null 的 enum 在請求沒帶這個欄位時會被填成預設值（第一個成員，也就是 `Todo`），驗證看不出「沒送」與「送了 todo」的差別，那筆已完成的任務就被悄悄改回待辦。改成可為 null 後，缺欄位得到 `null`，`[Required]` 就能擋下。`[EnumDataType]` 補的是另一個洞：JSON 裡寫數字 `7` 時，序列化器不會拒絕，而 `7` 不是任何一個成員，這個 attribute 讓它被驗證擋下。

屬性用 `init` 而非 `set`，是因為 Request 物件被 binding 填完之後不應該再被改動，`init` 讓這件事成為編譯期保證。類別加 `sealed` 只是表達「沒有人要繼承它」，不影響行為。

### 2. Response DTO

新增 `TaskResponse.cs`：

```csharp
using TaskTracker.Api.Entities;

namespace TaskTracker.Api.Dtos;

public sealed record TaskResponse(Guid Id, string Title, TaskItemStatus Status, DateTimeOffset CreatedAt);
```

Response 用 `record`，Request 用 `class`，這是刻意的分工，下一節說明。

### 3. 把驗證從 entity 拿掉

`TaskItem` 現在不再是外部輸入，它的驗證屬性已經沒有作用（binding 不會再碰它），留著只會讓人誤以為資料庫模型有這些規則。編輯 `Entities/TaskItem.cs`，刪掉 `using System.ComponentModel.DataAnnotations;`、`[Required]`、`[StringLength(100)]`：

```csharp
namespace TaskTracker.Api.Entities;

public class TaskItem
{
    public Guid Id { get; set; }

    public string Title { get; set; } = string.Empty;

    public TaskItemStatus Status { get; set; }

    public DateTimeOffset CreatedAt { get; set; }
}
```

這裡有個取捨要說清楚：驗證規則現在只存在於 Request DTO。如果之後有別的程式路徑（背景工作、資料匯入）也會建立 `TaskItem`，它們不會經過這些驗證。那種情境的規則要放在更內層（service 或 entity 自己的建構邏輯），這是 [[basics-07-dependency-injection-and-services]] 之後要處理的事。HTTP 邊界的輸入驗證放在 DTO 是對的，但它不是唯一一道防線。

### 4. 手動 mapping

新增資料夾 `src/TaskTracker.Api/Extensions/`，建立 `TaskItemExtensions.cs`：

```csharp
using TaskTracker.Api.Dtos;
using TaskTracker.Api.Entities;

namespace TaskTracker.Api.Extensions;

public static class TaskItemExtensions
{
    public static TaskResponse ToResponse(this TaskItem task) => new(task.Id, task.Title, task.Status, task.CreatedAt);
}
```

這個 extension method 是整本書 mapping 的樣板：一個方向（entity 轉 Response）、一個地方、一行。反方向（Request 轉 entity）不寫成 mapper，下一步直接在 controller 裡 new，因為它包含伺服器才知道的值（新 id、現在時間、初始狀態），這些值不屬於任何一個 DTO。

### 5. 改 controller

`TasksController` 的變動集中在簽章與回傳，標準是「進來的是 Request，出去的是 `TaskResponse`」。保留與 entity 有關的 `Tasks` 靜態清單不動（它在 [[basics-07-dependency-injection-and-services]] 會被移進 service）。

```csharp
using TaskTracker.Api.Extensions;
// 其餘 using 與 basics-05 相同

[HttpGet]
public ActionResult<PagedResponse<TaskResponse>> GetAll([FromQuery] TaskListQuery query)
{
    var filtered = query.Status is null ? Tasks : Tasks.Where(t => t.Status == query.Status);
    var ordered = filtered.OrderBy(t => t.CreatedAt).ToList();
    var items = ordered
        .Skip((query.Page - 1) * query.PageSize)
        .Take(query.PageSize)
        .Select(t => t.ToResponse())
        .ToList();
    return Ok(new PagedResponse<TaskResponse>(items, query.Page, query.PageSize, ordered.Count));
}

[HttpGet("{id:guid}")]
public ActionResult<TaskResponse> GetById(Guid id)
{
    var task = Tasks.FirstOrDefault(t => t.Id == id);
    return task is null ? NotFound() : Ok(task.ToResponse());
}

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

[HttpPut("{id:guid}")]
public ActionResult<TaskResponse> Update(Guid id, UpdateTaskRequest request)
{
    var task = Tasks.FirstOrDefault(t => t.Id == id);
    if (task is null)
    {
        return NotFound();
    }

    task.Title = request.Title;
    task.Status = request.Status!.Value;
    return Ok(task.ToResponse());
}
```

`Delete` 沒有變動。`request.Status!.Value` 的驚嘆號是「我保證不是 null」：因為 `[Required]` 保證驗證通過時 `Status` 一定有值，而驗證失敗的請求不會進到 action（見 [[basics-05-model-binding-and-validation]]）。這個斷言的依據是框架行為，所以如果日後有人拿掉 `[Required]`，這一行會在執行期丟 `InvalidOperationException`。

注意 `CreatedAtAction` 的第三個參數也是 `task.ToResponse()`：`201` 回應的 body 同樣是 Response DTO，不是 entity，沒有例外。

### 驗證結果

啟動專案（`dotnet run --project src/TaskTracker.Api`），先看清單：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"items":[{"id":"11111111-1111-1111-1111-111111111111","title":"Read chapter 4","status":"done","createdAt":"2026-10-01T09:00:00+00:00"},{"id":"22222222-2222-2222-2222-222222222222","title":"Write the first controller","status":"todo","createdAt":"2026-10-02T09:00:00+00:00"},{"id":"33333333-3333-3333-3333-333333333333","title":"Try the PUT endpoint","status":"todo","createdAt":"2026-10-03T09:00:00+00:00"}],"page":1,"pageSize":20,"totalCount":3}
```

（省略了 `Date`、`Server`、`Transfer-Encoding` 標頭。回應內容與拆分前相同，這正是 DTO 的目的：對外契約沒有變。）

接著送一個夾帶 `id`、`status`、`createdAt` 的建立請求，這是前面 over-posting 的同一種手法：

```powershell
'{"id":"00000000-0000-0000-0000-000000000001","title":"Over-posted","status":"done","createdAt":"1999-01-01T00:00:00Z"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" --data-binary '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Location: http://localhost:5080/api/tasks/a0cf32c4-d82d-49ff-870a-df174d7c2940

{"id":"a0cf32c4-d82d-49ff-870a-df174d7c2940","title":"Over-posted","status":"todo","createdAt":"2026-10-30T14:21:52.9727904+00:00"}
```

`id`、`status`、`createdAt` 全部被忽略，伺服器用自己的值。多餘欄位的預設行為是靜默忽略，不會回 400，呼叫端得不到任何提示，所以前端打錯欄位名稱（例如 `titel`）時，要靠 `Title` 的 `[Required]` 才會發現。

這個結果在 basics-05 的版本也一樣，因為當時的 `Create` 手動把 `Id`、`Status`、`CreatedAt` 蓋成伺服器的值。差別在安全的來源：以前靠 controller 的每一行都記得蓋，哪天有人在 entity 加了 `IsAdmin` 又忘了蓋，洞就開了；現在 `CreateTaskRequest` 根本沒有這些屬性，新增 entity 欄位不會自動變成可寫入。

再看 basics-05 遺留的 `PUT` 問題，少送 `status`：

```powershell
'{"title":"Only title"}' | curl.exe -s -i -X PUT "http://localhost:5080/api/tasks/$newId" -H "Content-Type: application/json" --data-binary '@-'
```

```text
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json; charset=utf-8

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.1","title":"One or more validation errors occurred.","status":400,"errors":{"Status":["The Status field is required."]},"traceId":"..."}
```

（`$newId` 是你先用 `POST` 建出來的任務 id；`traceId` 省略。）已完成的任務不會再被悄悄改回待辦。最後確認 enum 的兩種錯誤寫法都被擋下：

```powershell
'{"title":"x","status":"archived"}' | curl.exe -s -i -X PUT "http://localhost:5080/api/tasks/$newId" -H "Content-Type: application/json" --data-binary '@-'
```

```text
HTTP/1.1 400 Bad Request

{"...":"...","errors":{"request":["The request field is required."],"$.status":["The JSON value could not be converted to System.Nullable`1[TaskTracker.Api.Entities.TaskItemStatus]. Path: $.status | LineNumber: 0 | BytePositionInLine: 32."]},...}
```

（省略處以 `...` 表示，只留與主題有關的 `errors`。）字串 `archived` 不是任何成員的對外名稱，序列化器在反序列化階段就失敗了。這個錯誤訊息的 `request: The request field is required` 是 JSON 失敗後參數為 null 的附帶結果，不是第二個問題。數字 `7` 則走另一條路：

```powershell
'{"title":"x","status":7}' | curl.exe -s -i -X PUT "http://localhost:5080/api/tasks/$newId" -H "Content-Type: application/json" --data-binary '@-'
```

```text
HTTP/1.1 400 Bad Request

{"...":"...","errors":{"Status":["The field Status is invalid."]},...}
```

這是 `[EnumDataType]` 的功勞。到此 basics-05 留下的兩個問題都解決了。

---

## 四、record 與 class：各自用在哪

前面 Response 用 `record`、Request 用 `class`，這個分工的理由和語言特性有關，值得展開，因為這兩種寫法在網路上的文章混用得很亂。

`record` 的 positional 語法（`record TaskResponse(Guid Id, string Title, ...)`）一行定義出建構子、唯讀屬性、值相等比較和 `ToString`。Response 物件的生命週期很簡單：controller 建出來，序列化器輸出，用完丟掉。它不需要驗證、不需要預設值、不會被改動，這些條件正是 positional record 的最佳場景。簡潔的另一個好處是欄位和 `ToResponse()` 的參數一一對應，漏一個欄位會編譯失敗。

Request 的情境不同。它需要驗證屬性與預設值，而 `init` 屬性的 class 在這兩點上更直觀。positional record 也能加驗證屬性，直接標在建構子參數上，.NET 10 實測可用：

```csharp
public record CreateRec([Required][StringLength(10)] string Title);
```

送 `{}` 得到 `"Title":["The Title field is required."]`，送超長字串得到 `"The field Title must be a string with a maximum length of 10."`，送合法值回傳 `{"title":"ok"}`。所以選 class 不是因為 record 做不到，而是 Request 常常需要「選填欄位有預設值」、「同一個屬性疊三個 attribute」，這些在屬性宣告式的 class 裡每個欄位自成一區塊，修改時 diff 乾淨；positional record 的參數列會越拉越長。使用 record 當 Request 的專案也很多，只要全專案一致就好。深度篇對 record 與 JSON 建構子規則（多個建構子時的 `[JsonConstructor]`）有進一步說明，見 [[04-model-binding-and-validation]]。

兩者共通的規則是 DTO 裡不放行為。有人會想在 `TaskResponse` 加一個 `IsOverdue` 計算屬性，這會把商業規則藏進傳輸型別，之後測試和重用都變難；那類邏輯放在 service 或 entity。

### status 怎麼變成小寫字串

規格要求 JSON 裡的 `status` 是 `"todo"` 或 `"done"`，但 C# 的 enum 成員是 PascalCase。這件事在 [[basics-04-controllers-and-routing]] 已經設定好了，`TaskResponse` 直接沿用，值得回頭看它為何有效：

```csharp
[JsonConverter(typeof(JsonStringEnumConverter<TaskItemStatus>))]
public enum TaskItemStatus
{
    [JsonStringEnumMemberName("todo")]
    Todo,

    [JsonStringEnumMemberName("done")]
    Done
}
```

`JsonStringEnumConverter<T>` 讓 enum 以字串輸出，`JsonStringEnumMemberName` 指定每個成員的對外字串（需要 .NET 9 以上）。這兩個 attribute 寫在 enum 型別上，所以不論 enum 出現在 `TaskResponse`、`UpdateTaskRequest` 還是 `TaskListQuery`，JSON 的外觀都一致，不用每個 DTO 各設一次。注意這是 System.Text.Json 的規則：query string 綁定 enum 看的是 C# 成員名稱，`?status=todo` 是靠不分大小寫比對 `Todo`，與 `JsonStringEnumMemberName` 無關（見 [[basics-05-model-binding-and-validation]]）。

這裡有一個與 DTO 主題相關的觀察：enum 型別 `TaskItemStatus` 同時被 entity 和 DTO 使用。大多數專案這樣做沒問題，enum 是穩定的領域詞彙。但它也意味著「對外的狀態字串」和「內部的狀態列舉」綁在一起；如果某天資料庫存的是 `Archived`、對外要合併成 `done`，就需要在 DTO 層另設自己的 enum 或字串，並在 mapping 時轉換。現在不必為此預做準備，知道這個接縫在哪裡就夠。

---

## 五、為什麼先手動 mapping，AutoMapper 與其他選項怎麼取捨

`ToResponse()` 是一行手寫的 mapping。有經驗的 .NET 開發者看到會問：為什麼不用 AutoMapper？

先手動的理由有三個。第一，欄位數量少時，手寫比設定檔案更短；`new(task.Id, task.Title, task.Status, task.CreatedAt)` 比任何 profile 都直白。第二，欄位漏掉的時機不同：positional record 少給一個參數，編譯器立刻報錯；反射式 mapper 的設定錯誤要到執行期才爆（除非另外寫測試呼叫驗證方法）。第三，除錯時可以在 mapping 那一行下中斷點，看每個欄位的值是怎麼來的。

手動 mapping 的成本在欄位多、DTO 多的時候才出現：幾十個型別、每個二十個欄位，每次加欄位要改多處。這時才有理由考慮 mapping 工具。選項至少有三類，各自的取捨如下（授權資訊截至本章寫作時，從各專案官方頁面查證）：

| 工具 | 運作方式 | 授權狀況 |
| --- | --- | --- |
| AutoMapper | 執行期反射與表達式樹，用 profile 設定規則 | 15.0.0 起需要商業授權；較早版本維持原本的 Apache 2.0；有符合條件的免費 Community 方案 |
| Mapperly | build 時由 source generator 產生 mapping 程式碼 | Apache 2.0 |
| Mapster | 執行期表達式編譯，另有 build 時產生程式碼的工具 | MIT |

AutoMapper 的授權變動是選型時必須先確認的事。自 15.0.0 起，AutoMapper 由 Lucky Penny Software 維護並需要商業授權，更早的版本仍是原本的開源授權；另有免費的 Community 方案，但有資格條件，條件內容以其官方站（automapper.io）當時的說明為準。GitHub 上該組織的 `LICENSE.md` 寫明預設授權為 Reciprocal Public License 1.5，不想以該授權公開衍生原始碼者需另簽授權協議。這些條件可能再變，專案若考慮使用，應該在決定當下重新讀官方頁面，並請公司的法務或採購確認，而不是照本書的轉述。

Mapperly 的路線不同：mapping 方法的實作在編譯期產生成普通 C# 程式碼，執行期沒有反射，產生的程式碼也可以打開來看。它的 mapping 問題（例如目的端有屬性來源端沒有）在編譯期以診斷警告出現（可設成錯誤讓 build 失敗），這與「先手動」的第二個理由一致：錯誤越早出現越好。對於已經習慣手動 mapping、只是想省下重複勞動的團隊，這是最小的認知落差。

判準可以訂得具體一點：DTO 少於十來個，手動。多於這個數量，且 mapping 規則單純（欄位同名同型別），選用 source generator 類工具。需要大量條件式、跨多層物件的對映設定，才輪到執行期工具，而且先確認授權與維護狀況。無論選哪一個，有一條不變：mapping 工具只負責欄位搬運，不要把商業邏輯寫進 mapping 設定，否則除錯時行為藏在設定檔裡。

另一個常見的誤用是在 `Select` 之前先把整個 entity 載入再 mapping。使用 EF Core 時，可以在查詢階段就只選出需要的欄位（projection），讓資料庫少傳資料；這個技巧留給深度篇 [[08-efcore-query]]。目前 TaskTracker 還是記憶體清單，先不處理。

---

## 六、DTO 如何讓 API 能演進

回到本章開頭資料庫欄位改名的情境，現在 TaskTracker 的狀態是什麼：如果 `TaskItem.Title` 改叫 `Name`，編譯器會立刻指出 `ToResponse()` 和 `Create` 裡兩處要改；改完，JSON 的 `title` 還是 `title`，前端什麼都不會發現。這就是 DTO 的演進價值：資料庫模型可以隨內部需要自由調整，API 契約只在你決定改的時候才改。

新增欄位同樣受益。假設要加 `Priority`：先在 entity 加屬性，這時 API 完全沒變，因為 `TaskResponse` 沒有它；準備好要公開時，在 `TaskResponse` 加一個欄位並更新 `ToResponse()`。對舊的前端來說，多出一個沒用到的 JSON 欄位通常無害（會忽略不認識欄位的客戶端不受影響），這叫「向後相容的新增」。反過來，移除欄位、改名、改型別都是 breaking change，必須讓舊客戶端有時間遷移。

當真的需要 breaking change 時，DTO 讓兩個版本能並存：舊端點繼續回舊 DTO，新端點回新 DTO，兩者從同一個 entity 映射而來。命名上有兩種寫法，把版本放類別名稱後綴（`TaskResponseV1`、`TaskResponseV2`），或用 namespace 區隔（`V1.TaskResponse`、`V2.TaskResponse`）。前者簡單但型別數量一多就難以管理，後者讓同一個名字在不同版本資料夾裡出現，搭配版本化的 controller 比較整齊。版本號怎麼放進網址或標頭、OpenAPI 文件如何依版本分組，是 [[basics-14-openapi-and-versioning]] 的內容，到那一章再決定採用哪一種。這一章先留下一個習慣：DTO 放在獨立資料夾，不被 entity 引用，日後加版本只是多一個資料夾。

---

## 常見誤解

**「DTO 是為了解耦，小專案直接回傳 entity 比較快。」** 前面的例子裡沒有一個問題和專案大小有關。`PasswordHash` 外洩、導覽屬性造成序列化迴圈、`isAdmin` 被 over-posting，兩個欄位的 entity 也可能碰到其中之一。DTO 先是安全與契約的邊界，其次才談得上解耦。

**「Request 和 Response 欄位一樣就可以合併。」** 現在一樣不代表會一直一樣。更關鍵的是「可寫入」與「可讀取」本來就是兩個集合：`Id`、`CreatedAt` 可讀不可寫。合併後，可寫入集合被迫等於可讀取集合，over-posting 的洞就開了。

**「加了 `[Required]` 就能防止 over-posting。」** `[Required]` 只保證「有值」，不限制「多送別的」。多餘的欄位在預設行為下會被靜默忽略（前提是 Request DTO 沒有對應屬性），所以能防止 over-posting 的是 Request DTO 本身沒有那個屬性。如果用 entity 當 Request，驗證屬性擋不住 `isAdmin: true`，因為它是合法的布林值。

**「用了 AutoMapper 就不用擔心漏欄位。」** 反射式 mapper 在目的端有來源端找不到的屬性時，要執行期才發現（除非主動呼叫設定驗證）。這是它和手動 mapping、source generator 之間的差別：手動和 source generator 的錯誤在編譯期。

**「DTO 裡可以放商業邏輯，反正都是 C# 類別。」** DTO 的職責是傳輸資料。把計算屬性、狀態轉換放進去，邏輯會散在傳輸層，測試與重用都變困難。

## 同事會來問你的問題

**Q：entity 和 DTO 欄位一模一樣，還要寫 DTO 嗎？**

要。一模一樣是現在的狀態，它保護的是未來：資料庫欄位增加、改名時，API 契約不被牽動。如果真的永遠一樣，`ToResponse()` 只是幾行無害的程式；如果日後不一樣，你已經有地方放差異。

**Q：Create 和 Update 的規則幾乎相同，用一個 `TaskRequest` 不行嗎？**

可以硬做，但需要條件式驗證去區分情境，而 `Id`、`CreatedAt` 這類只讀欄位也要想辦法擋。兩個小型別的重複成本，低於一個需要「在這個情境下才必填」判斷的型別。

**Q：為什麼 `UpdateTaskRequest.Status` 是 `TaskItemStatus?` 而不是 `TaskItemStatus`？**

為了能區分「沒送」與「送了第一個成員的值」。不可為 null 的 enum 在缺欄位時會被填成預設值 `Todo`，驗證看不出差別。可為 null 加上 `[Required]` 之後，缺欄位得到 `null` 並被擋下。

**Q：mapping 要放在 controller、extension method 還是 service？**

單向、無依賴的 entity 轉 Response 放 extension method 最簡單。需要注入其他服務（例如查另一張表補欄位）的 mapping 就不適合放 extension，要放到 service。Request 轉 entity 通常含伺服器決定的值，直接在建立 entity 的地方寫。

**Q：我可以直接用 AutoMapper 嗎，公司有在用？**

看版本與公司的授權狀況。15.0.0 之後需要商業授權或符合條件的 Community 方案，較早的版本維持原授權。先問公司是否已有授權，再決定；如果沒有，Mapperly 這類 source generator 是授權單純的替代，或者維持手動。

## 這章的位置

讀完這章，你能解釋直接回傳 entity 會出的四種事（洩漏、序列化迴圈、over-posting、契約與資料庫耦合），能依操作切出 Request 與 Response DTO 並命名，能把 TaskTracker 的 entity 與 API 契約拆開，也知道手動 mapping 的做法與何時該換工具。TaskTracker 現在每個端點的輸入輸出都是 DTO，basics-05 遺留的「缺 `status` 被預設值蓋過」已經解決。

還沒解決的是 controller 裡直接操作靜態清單、`Create` 與 `Update` 裡有建立與修改 entity 的邏輯，隨著規則增加 controller 會變胖。[[basics-07-dependency-injection-and-services]] 處理這個問題：把邏輯移進 service，並解釋物件由誰建立。想看 binding 內部與 over-posting 更多細節，讀深度篇 [[04-model-binding-and-validation]]。

---

## 連結

- 上一章：[[basics-05-model-binding-and-validation]]
- 下一章：[[basics-07-dependency-injection-and-services]]
- 對應深度章：[[04-model-binding-and-validation]]
- 全書目錄：[[dotnet-web-api]]
