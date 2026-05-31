---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Chapter 3：Controller、Routing 與 Action 設計

## 3.1 Controller 的角色定位

### Controller 在系統中的責任

- Web API 的 **HTTP 入口層**
- 負責：
    - 接收 HTTP Request
    - 解析輸入資料
    - 呼叫應用層服務
    - 組裝 HTTP Response

### Controller 不應負責的事情

- 商業邏輯
- 資料庫存取
- 複雜流程控制

**設計原則**

- Controller 應保持「薄（Thin Controller）」
- 所有邏輯應下沉至 Service Layer

## 3.2 Controller 的基本結構

```csharp
[ApiController]
[Route("api/[controller]")]
publicclassUsersController :ControllerBase
{
    [HttpGet]
		public IActionResultGetUsers()
    {
				return Ok();
    }
}
```

### ApiController

- 啟用 API 專用行為：
    - 自動 Model Validation
    - 更嚴謹的 Model Binding
    - 預設回傳 400（Bad Request）

### ControllerBase

- 專為 Web API 設計的基底類別
- 不包含 View 相關功能
- 適合 REST API 使用

## 3.3 Routing 設計原則

### Attribute Routing

- ASP.NET Core Web API 預設使用 Attribute Routing
- Route 直接宣告在 Controller 與 Action 上

```csharp
[Route("api/users")]
```

### 常見 Route Pattern

```
/api/resources
/api/resources/{id}
/api/resources/{id}/sub-resources
```

### [controller] Token

- `[controller]` 會自動替換為 Controller 類名（去除 Controller）
- `UsersController` → `users`

**建議**

- 使用小寫 URL
- 使用複數名詞表示集合

## 3.4 HTTP Method 與 Action 對應

### Method Attribute

| Attribute | HTTP Method |
| --- | --- |
| `[HttpGet]` | GET |
| `[HttpPost]` | POST |
| `[HttpPut]` | PUT |
| `[HttpPatch]` | PATCH |
| `[HttpDelete]` | DELETE |

### 搭配 Route 參數

```csharp
[HttpGet("{id}")] // 用 {} 讓 url 的值當作 function 參數
public IActionResultGetUser(int id) // 對應url的 id
{
		return Ok();
}
```

## 3.5 Model Binding（資料來源對應）

ASP.NET Core 會依照 **Model Binding 規則與優先順序**，自動將 HTTP Request 中的資料對應到 Action 參數或 DTO 屬性 (DTO)。

[ASP.NET](http://asp.net/) Core 在呼叫你的 Controller Action 之前，先把 HTTP Request 拆解，然後一格一格把值塞進你宣告的參數或 DTO 屬性裡。

## 一、實際時間軸：Request 到 Action 發生了什麼

你寫的程式碼是這個：

```csharp
[HttpGet("{id}")]
public IActionResultGetUser(
    [FromRoute]int id,
    [FromQuery]bool includeProfile
)
{
	return Ok();
}
```

使用者送出這個 Request：

```
GET /api/users/42?includeProfile=true
```

---

### Step 1：HTTP Request 抵達 ASP.NET Core

伺服器收到的是純文字協定資料，大致是：

- Method: GET
- Path: /api/users/42
- Query String: includeProfile=true
- Headers: …
- Body: （空）

此時 **沒有 id，也沒有 includeProfile 變數**。

---

### Step 2：Routing 先執行（還不是 Model Binding）

Routing 做一件事：

> 這個 Request 應該交給哪一個 Controller / Action？
> 

```csharp
[HttpGet("{id}")]
```

Routing 發現 `{id}` 對應到 `42`，於是得到：

```
RouteValues["id"] ="42"
```

⚠️ 注意：**此時還沒有 int id，只是字串 "42" 被放進 RouteValues。**

---

### Step 3：Model Binding 開始（重點來了）

現在 Framework 已經知道要呼叫這個方法：

```csharp
GetUser(int id,bool includeProfile)
```

Model Binder 開始「逐一處理參數」。

---

### 參數 1：`int id`

1. 看到你標註 `[FromRoute]`
2. 於是去 RouteValues 找 `id`
3. 找到 `"42"`（string）
4. 嘗試轉型成 `int`
5. 成功 → `id = 42`

---

### 參數 2：`bool includeProfile`

1. 看到 `[FromQuery]`
2. 去 Query String 找 `includeProfile`
3. 找到 `"true"`
4. 嘗試轉成 `bool`
5. 成功 → `includeProfile = true`

---

### Step 4：Action 被真正呼叫

到這一刻，Framework 等同於幫你執行了：

```csharp
GetUser(42,true);
```

然後才進到你的程式碼：

```csharp
return Ok();
```

## 二、DTO 為什麼「看起來像自動魔法」

你寫：

```csharp
public IActionResultCreateUser(CreateUserDto dto)
```

Request：

```
POST /api/users
Content-Type: application/json

{
  "name": "Vic",
  "age": 30
}
```

---

### Model Binding 對 DTO 做了什麼

1. 偵測到 `Content-Type: application/json`
2. 讀取 Body 原始文字
3. 使用 JSON Formatter 反序列化
4. 嘗試建立 `CreateUserDto`
5. 逐一對應屬性名稱：
    - `name` → `dto.Name`
    - `age` → `dto.Age`

結果等同於：

```csharp
var dto = new CreateUserDto
{
    Name ="Vic",
    Age =30
};
```

然後才呼叫：

```csharp
CreateUser(dto);
```

---

## 三、為什麼叫「Binding」

因為它做的是**「資料來源 → 參數」的綁定**：只宣告「我需要什麼」，Framework 幫你把資料接上。

| Request 裡的資料 | 綁定到 |
| --- | --- |
| RouteValues | Action 參數 |
| Query String | Action 參數 |
| Header | Action 參數 |
| Body(JSON) | DTO 屬性 |

---

## 四、如果 Binding 失敗，會發生什麼事

例如：

```
GET /api/users/abc
```

```csharp
public IActionResultGetUser([FromRoute] int id)
```

流程會是：

1. 找到 `"abc"`
2. 嘗試轉成 `int`
3. 失敗
4. ModelState 標記錯誤
5. 若有 `[ApiController]` → 直接回傳 400

你甚至 **不會進到 Action**。

---

## 五、你可以用一句「腦內模型」記住

> Controller Action 不是直接接 HTTP Request **而是接收「已經被 Framework 填好值的參數」**
> 

Model Binding 就是「填值」這件事。

---

## 六、如果你想再更底層一點（可選）

內部實際元件包含：

- ModelBinder
- Value Provider（Route / Query / Header）
- Input Formatter（JSON / XML）

但**理解到「逐一參數嘗試取值與轉型」就夠了**，寫 API 已經完全足夠。

隱式 Model Binding（未標註 Attribute）

若未明確標註 `[FromXxx]`，Framework 會依型別與 HTTP Method 推斷來源：

| 參數型別 | 預設來源 |
| --- | --- |
| 基本型別（int, string, bool…） | Route → Query |
| 複合型別（class / record） | Body（POST / PUT / PATCH） |

```csharp
[HttpPost]
public IActionResult CreateUser(CreateUserDto dto)
{
    // dto 預設來自 Body
    return Ok();
}
```

**設計建議**

- 公開 API 建議「明確標註來源」，避免日後誤判
- 尤其在複雜查詢條件時，不要依賴隱式規則

### 二、[ApiController] 對 Model Binding 的影響（非常重要）

當 Controller 標註 `[ApiController]` 時：

1. **自動推斷 FromBody / FromQuery**
2. **自動 Model Validation（400 Bad Request）**
3. **禁止多個 `[FromBody]` 參數**

```csharp
[ApiController]
[Route("api/users")]
public class UsersController : ControllerBase
{
}
```

```csharp
public IActionResult Create(
	[FromBody] CreateUserDto dto
)
{
    // 若 ModelState Invalid，Controller 不會進來
}
```

**設計建議**

- API 專案一定要使用 `[ApiController]`
- 不要手動檢查 `ModelState.IsValid`

### 三、FromQuery 與查詢 DTO（實務常用）

複雜查詢條件應封裝為 DTO，而非多個參數：

```csharp
public class UserQueryDto
{
    public string? Keyword { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
}
```

```csharp
[HttpGet]
public IActionResult GetUsers([FromQuery] UserQueryDto query)
{
    return Ok();
}
```

```csharp
GET /api/users?keyword=vic&page=2&pageSize=50
```

**設計建議**

- Query DTO 命名建議：`XxxQueryDto`
- 預設值應直接在 DTO 中定義

### Model Binding 發生的事情

| Query String | 對應屬性 |
| --- | --- |
| keyword=vic | query.Keyword = "vic" |
| page=2 | query.Page = 2 |
| pageSize=50 | query.PageSize = 50 |

沒給的值：

- `keyword` → `null`
- `page` → 使用 DTO 預設值 `1`
- `pageSize` → 使用 DTO 預設值 `20`

## 二、只給部分條件（非常常見）

### URL

```
GET /api/users?keyword=admin
```

結果：

```csharp
query.Keyword// "admin"
query.Page// 1
query.PageSize// 20
```

**不用寫任何防呆程式碼**，預設值自然生效。

## 三、只有分頁，沒有關鍵字

```
GET /api/users?page=3
```

結果：

```csharp
query.Keyword// null
query.Page// 3
query.PageSize// 20
```

---

### 四、FromHeader 使用情境（不是拿來傳業務資料）

```csharp
public IActionResult Get(
    [FromHeader(Name = "X-Request-Id")] string requestId
)
{
    return Ok();
}
```

**適合放在 Header 的資料**

- Correlation Id / Request Id
- 語系（Accept-Language）
- Feature Flag
- Client Version

**不建議**

- 業務資料（例如 userId、orderId）

---

### 五、FromForm（檔案與表單資料）

```csharp
[HttpPost("upload")]
public IActionResult Upload(
    [FromForm] IFormFile file,
    [FromForm] string description
)
{
    return Ok();
}
```

**設計建議**

- 檔案上傳一律使用 `multipart/form-data`
- 不要混用 `FromBody` 與 `FromForm`

---

### 六、Route 與 Query 命名一致性

```csharp
[HttpGet("{userId}")]
public IActionResult Get(
    [FromRoute(Name = "userId")] int id
)
{
    return Ok();
}
```

**設計建議**

- Route 參數名稱與方法參數名稱一致
- 若不同，務必明確指定 `Name`

---

### 七、常見錯誤與陷阱

| 問題 | 說明 |
| --- | --- |
| GET 使用 Body | 大多數 Proxy / Cache 不支援 |
| 多個 FromBody | 直接丟 Exception |
| DTO 屬性無 setter | 無法綁定 |
| nullable 設計錯誤 | 容易造成 400 |

---

### 八、總結建議（可直接當結尾）

- 明確標註資料來源，提高可讀性與可維護性
- 查詢條件使用 Query DTO，寫法一致
- 業務資料放 Body，控制資訊放 Header
- 所有 API Controller 啟用 `[ApiController]`

### 常見來源

| Attribute | 資料來源 |
| --- | --- |
| [FromRoute] | URL Path |
| [FromQuery] | Query String |
| [FromBody] | Request Body |
| [FromHeader] | HTTP Header |

```csharp
[HttpGet("{id}")]
public IActionResultGetUser(
    [FromRoute]int id,
    [FromQuery]bool includeProfile)
{
		return Ok();
}
```

**設計建議**

- GET 不使用 Body
- 複雜輸入一律使用 DTO + FromBody

## 3.6 Action 回傳策略（ActionResult）

### 為什麼不直接回傳資料

- HTTP Response 需要狀態碼
- 錯誤與成功需明確區分

### 常用回傳方式

```csharp
return Ok(data);// 200
return CreatedAtAction(...);// 201
return BadRequest();// 400
return NotFound();// 404
return Unauthorized();// 401
```

### ActionResult vs IActionResult

- `IActionResult`：彈性高
- `ActionResult<T>`：型別安全、Swagger 友善

**建議**

- 對外 API 優先使用 `ActionResult<T>`

## 3.7 一個完整 Controller 範例

```csharp
[ApiController]
[Route("api/users")]
public class UsersController : ControllerBase
{
    [HttpGet("{id}")]
    public ActionResult<UserDto> GetUser(int id)
    {
        if (id <= 0)
            return BadRequest();

        var user = new UserDto
        {
            Id = id,
            Name = "Demo User"
        };

        return Ok(user);
    }
}
```

## 3.8 Controller 設計準則（定稿）

- 一個 Controller 對應一個 Resource
- Method 與 Route 語意需一致
- 不在 Controller 寫商業邏輯
- 回傳正確的 HTTP Status Code
- 使用 DTO 隔離內部模型