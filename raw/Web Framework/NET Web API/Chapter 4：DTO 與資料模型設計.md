---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Chapter 4：DTO 與資料模型設計

## 4.1 為什麼 Web API 一定需要 DTO

### 問題背景

在 Web API 中，資料會在多個邊界之間流動：

- Client ↔ API
- API ↔ Domain / Application Layer
- Application ↔ Database

如果沒有明確的資料邊界，會導致：

- 安全風險（敏感欄位外洩）
- API 破壞性變更
- 前後端高度耦合

### DTO（Data Transfer Object）的角色

- 定義 **API 對外的資料契約**
- 隔離內部資料結構
- 控制可讀寫欄位

**核心原則**

- Entity 是內部模型
- DTO 是對外模型
- 兩者不應直接共用

---

## 4.2 常見錯誤做法（務必避免）

### 錯誤示範

```csharp
[HttpGet("{id}")]
public UserGetUser(int id)
{
	return _db.Users.Find(id);
}
```

### 問題點

- Entity 結構一旦改動，API 行為即改變
- 可能暴露：
    - 密碼雜湊
    - 內部狀態欄位
- 無法控管輸入資料範圍

---

## 4.3 DTO 的分類方式

### Request DTO

- 用於接收 Client 傳入資料
- 定義「允許被寫入」的欄位

### Response DTO

- 用於回傳資料給 Client
- 定義「允許被讀取」的欄位

### 原則

- Request 與 Response DTO **分開定義**
- 不要因為「欄位一樣」而合併

---

## 4.4 DTO 命名與結構規範

### 命名建議

- `{Resource}CreateRequest`
- `{Resource}UpdateRequest`
- `{Resource}Response`
- `{Resource}SummaryResponse`

### 範例

```csharp
public class UserCreateRequest
{
	public string Name {get;set;}
	public string Email {get;set;}
}
```

```csharp
public class UserResponse
{
	public int Id {get;set;}
	public string Name {get;set;}
}
```

---

## 4.5 DTO 與 Model Validation

### 為什麼 Validation 應放在 DTO

- 驗證的是「輸入資料是否合法」
- 不應污染 Domain Model

### 常用 Data Annotation

```csharp
public class UserCreateRequest
{
    [Required]
    [MaxLength(50)]
    public string Name { get; set; }

    [Required]
    [EmailAddress]
    public string Email { get; set; }
}
```

### 搭配 ApiController 行為

- 驗證失敗自動回傳 400
- Controller 不需手動檢查 ModelState

---

## 4.6 DTO 與 Controller 的標準搭配方式

### 範例：新增使用者

```csharp
[HttpPost]
public ActionResult<UserResponse> CreateUser(
    [FromBody] UserCreateRequest request)
{
    var user = new UserResponse
    {
        Id = 1,
        Name = request.Name
    };

    return CreatedAtAction(
        nameof(GetUser),
        new { id = user.Id },
        user);
}
```

---

## 4.7 DTO 映射策略（先手動，後工具）

### 初期建議

- 使用手動 mapping
- 明確可讀
- 易於 Debug

```csharp
var response = new UserResponse
{
    Id = entity.Id,
    Name = entity.Name
};
```

### AutoMapper 的使用時機

- DTO 與 Entity 數量龐大
- Mapping 規則穩定
- 團隊熟悉工具行為

---

## 4.8 DTO 與版本演進策略

### 為什麼 DTO 有助於版本控管

- 可同時存在多版本 DTO
- 舊 Client 不受影響

### 範例

- `UserResponseV1`
- `UserResponseV2`

---

## Chapter 4 設計準則（定稿）

- Entity 不直接暴露給 Client
- 所有 API I/O 一律使用 DTO
- Request / Response DTO 分離
- 驗證邏輯放在 DTO
- DTO 是 API 的長期契約

---

## Chapter 4 小結

- DTO 是 API 設計的邊界防線
- 正確的 DTO 設計能避免 80% 的未來重構
- DTO 不是多餘，而是必要抽象