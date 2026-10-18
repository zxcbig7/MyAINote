---
type: concept
domain: tech
tags: [python, fastapi, pydantic, validation, dto, response-model, schema]
sources: []
created: 2026-08-15
updated: 2026-08-15
---

# 第 02 章：Pydantic 與驗證 — 422 是誰產生的，`response_model` 又擋掉了什麼

## 一次不算漏洞的資料外洩

某個內部系統的使用者查詢 API，回傳長這樣：

```python
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()
```

能動、簡潔、看起來沒問題。直到某天前端工程師在瀏覽器 DevTools 裡截了一張圖問：「這個 `password_hash` 欄位是要給我用的嗎？」

回傳的是 ORM 物件，FastAPI 忠實地把它上面每一個欄位都序列化出去了——包含密碼雜湊、內部備註、軟刪除旗標、建立者 IP。沒有人「攻擊」任何東西，資料是後端主動送出去的。

這件事的修法只有一行——加上 `response_model=UserOut`——但要理解**為什麼這一行是安全機制而不是格式化選項**，得先弄懂 Pydantic 在 FastAPI 裡扮演的角色。

這一章講三件事：Pydantic 如何把型別宣告變成執行期的驗證、422 錯誤是誰產生的以及怎麼讀懂它、以及輸入與輸出為什麼必須是兩個不同的類別。

---

## 一、Pydantic 不是型別檢查器，是解析器

從 C# 過來很容易把 `BaseModel` 想成「有 DataAnnotations 的 DTO」。這個類比八成正確，但漏掉了關鍵的兩成。

DataAnnotations 的模型是：**先有一個物件，再檢查它合不合規**。`ModelState.IsValid` 是一次事後檢驗，物件本身早就建好了，欄位型別由 C# 保證。

Pydantic 的模型是：**接收未知的輸入，嘗試把它解析成一個保證合規的物件；解析不成就丟例外**。物件建立成功這件事本身，就是「資料已通過驗證」的證明。

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    in_stock: bool = True

item = Item(name="筆記本", price="35.5")   # 注意：字串
print(item.price, type(item.price))       # 35.5 <class 'float'>
```

`"35.5"` 被轉成了 `35.5`。這不是寬鬆，是刻意的：HTTP 傳來的東西全都是字串，如果不做型別強制轉換（coercion），每支 endpoint 都要自己 `int()` 一遍。

轉換不成功就是錯誤：

```python
Item(name="筆記本", price="免費")
# ValidationError: Input should be a valid number, unable to parse string as a number
```

這個「建構即驗證」的性質有個直接的實務結論：**一個 Pydantic 物件在你手上，就代表它的欄位型別是可信的**。不需要在業務邏輯裡再檢查一次 `if not isinstance(x, int)`。這正是型別驅動設計要的效果。

需要嚴格模式（不接受 `"35.5"` 這種轉換）時：

```python
from pydantic import ConfigDict

class Item(BaseModel):
    model_config = ConfigDict(strict=True)
    price: float
```

但對 HTTP API 來說預設的寬鬆模式通常才是你要的，別急著改。

---

## 二、定義一個 model

```python
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, EmailStr

class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"

class OrderItem(BaseModel):
    sku: str = Field(min_length=1, max_length=32)
    quantity: int = Field(gt=0, le=999)

class OrderCreate(BaseModel):
    customer_email: EmailStr
    items: list[OrderItem] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=200)
    status: OrderStatus = OrderStatus.pending
    total: Decimal = Field(gt=0, decimal_places=2)
    scheduled_at: datetime | None = None
```

幾個要點：

**必填 vs 選填，規則和上一章一樣**——有預設值就是選填。`Field(min_length=1)` 沒給 `default`，所以 `items` 仍是必填。

**巢狀 model 是遞迴驗證的。** `items` 裡的每個元素都會被當成 `OrderItem` 解析，任一個不合規整包就失敗，錯誤訊息會指出是第幾個元素的哪個欄位。

**`Enum` 繼承 `str` 是慣例。** 這樣它在 JSON 序列化時是 `"pending"` 而不是需要額外處理的列舉物件，比較字串也直接成立。

**`EmailStr` 需要額外套件**（`pip install "pydantic[email]"`），少了它啟動就會報錯。

**金額用 `Decimal` 不用 `float`。** 理由和 C# 用 `decimal` 不用 `double` 完全一樣——二進位浮點數表示不了 0.1。

### 常用約束

| 約束 | 適用型別 | 說明 |
| --- | --- | --- |
| `gt` / `ge` / `lt` / `le` | 數值 | 大於 / 大於等於 / 小於 / 小於等於 |
| `min_length` / `max_length` | 字串、list、dict | 長度 |
| `pattern` | 字串 | 正則（v1 叫 `regex`） |
| `decimal_places` / `max_digits` | Decimal | 小數位數 |
| `default_factory` | 全部 | 動態預設值，如 `default_factory=list` |

### 別名：處理 camelCase 前端

前端習慣 `customerEmail`，Python 慣例是 `customer_email`。用別名接起來：

```python
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

class OrderCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    customer_email: EmailStr
    scheduled_at: datetime | None = None
```

`populate_by_name=True` 表示兩種寫法都收（欄位名和別名）。這比在每個欄位上寫 `Field(alias=...)` 省事，而且產出的 OpenAPI 文件也會是 camelCase，前端看得懂。

---

## 三、422：誰產生的，怎麼讀

請求進來時，FastAPI 用你的簽章解析各個參數。任何一個解析失敗，Pydantic 丟出 `ValidationError`，FastAPI 把它包成 `RequestValidationError`，由內建的例外處理器轉成 **422 Unprocessable Entity**：

```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "items", 0, "quantity"],
      "msg": "Input should be greater than 0",
      "input": 0,
      "ctx": { "gt": 0 }
    },
    {
      "type": "missing",
      "loc": ["query", "limit"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**`loc` 是最有用的欄位**，它是一條從根到出錯位置的路徑。第一個元素告訴你 FastAPI 認為這個參數該從哪裡來——`"body"`、`"query"`、`"path"`、`"header"`、`"cookie"`。

所以上一章那句「參數明明帶了卻收不到」的診斷方法就是這個：如果你在 query 傳了 `tag`，回應卻說 `"loc": ["body", "tag"]`，代表 FastAPI 把它判成 body 了，問題出在你的型別宣告而不是前端。

**驗證是一次收集全部錯誤，不是遇到第一個就停。** 這對前端表單很有價值——一次回傳所有欄位的問題。

**422 vs 400。** ASP.NET Core 的 `[ApiController]` 驗證失敗回 400，FastAPI 回 422。語意上 422 更精確（語法正確、語意不通過），但如果前端已經對接了回 400 的後端，或公司規範統一 400，可以覆寫處理器改掉——做法在第 06 章。重點是**先講好**，不要讓前端猜。

---

## 四、自訂驗證

約束表達不了的規則，用 validator。

### 欄位層級：`field_validator`

```python
from pydantic import field_validator

class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_must_be_lower(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("使用者名稱只能包含英數字")
        return v.lower()       # 回傳值會取代原值
```

三個規則要記住：一定要加 `@classmethod`、一定要 `return` 值（忘了就變成 `None`）、丟 `ValueError` 而不是 `HTTPException`（Pydantic 會把它收集成標準的 422 條目；丟 `HTTPException` 會變成無法收集的 500）。

`mode="before"` 可以在型別轉換**之前**介入，用於清理輸入：

```python
    @field_validator("phone", mode="before")
    @classmethod
    def strip_dashes(cls, v):
        return v.replace("-", "") if isinstance(v, str) else v
```

### 模型層級：`model_validator`

跨欄位的規則要等所有欄位都解析完才能檢查：

```python
from pydantic import model_validator

class DateRange(BaseModel):
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def check_order(self):
        if self.start >= self.end:
            raise ValueError("start 必須早於 end")
        return self
```

`mode="after"` 的 validator 收到的是已建好的實例（所以有型別保證），回傳 `self`。

### 界線在哪

validator 適合**不需要外部資源的規則**：格式、範圍、欄位間關係。

**不該**放進 validator 的是需要查資料庫的規則（「這個 email 是否已註冊」）。理由有三：validator 是同步的，在 async 應用裡拿不到 async session；它會讓 model 依賴資料庫，變得無法單獨測試；而且這類規則的失敗語意是 **409 Conflict** 而不是 422。這種檢查屬於 service 層。

---

## 五、輸入與輸出必須分開

回到開頭的外洩事件。正確的做法是為同一個資源定義多個 model：

```python
class UserCreate(BaseModel):
    """客戶端送進來的（註冊）"""
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str

class UserUpdate(BaseModel):
    """客戶端送進來的（更新），全部選填"""
    display_name: str | None = None
    avatar_url: str | None = None

class UserOut(BaseModel):
    """回傳給客戶端的"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    display_name: str
    created_at: datetime
```

三個類別，三個理由：

**`UserOut` 沒有 `password_hash`。** 這是本章開頭那個問題的解法。只要回傳型別宣告成 `UserOut`，資料庫物件上多出來的欄位一律不會出現在回應裡。

**`UserCreate` 沒有 `id`、`created_at`、`is_admin`。** 這是防 over-posting：如果直接拿 ORM model 收 body，攻擊者送 `{"email": "...", "is_admin": true}` 就自己升級了。model 上沒有這個欄位，值就進不來。預設 Pydantic 對多餘欄位是**忽略**，要更嚴格可以：

```python
model_config = ConfigDict(extra="forbid")   # 多送欄位直接 422
```

`forbid` 對內部 API 很好用（打錯欄位名會立刻被告知，而不是靜默忽略），對外部 API 則要斟酌相容性。

**`UserUpdate` 全部選填。** PATCH 的語意是「只改我送的欄位」，配合 `model_dump(exclude_unset=True)` 就能區分「沒送這個欄位」和「明確送了 null」：

```python
@app.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: DbSession):
    user = get_or_404(db, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    return user
```

這整套和 [[dotnet-web-api]] 那邊 DTO 與 Entity 要分開的理由一模一樣，不同的只有語法。

### `from_attributes`：直接吃 ORM 物件

`model_config = ConfigDict(from_attributes=True)` 讓 Pydantic 可以從**任意物件的屬性**讀值，而不只是 dict。SQLAlchemy 的 ORM 實例就是這樣被轉成 `UserOut` 的。

沒有這一行，`response_model=UserOut` 遇到 ORM 物件會失敗。這是新手最常撞的錯誤之一（v1 時代這個設定叫 `orm_mode`，網路上舊文章很多）。

---

## 六、`response_model` 的完整行為

宣告 `response_model=UserOut` 之後，回傳值會經歷：

1. 用 `UserOut` 驗證（欄位缺漏或型別不符 → 丟 `ResponseValidationError`，客戶端收到 **500**）
2. 過濾掉 model 上沒有的欄位
3. 序列化成 JSON
4. 把 schema 寫進 OpenAPI 文件

第 1 點值得注意：**回應驗證失敗是 500 不是 422**，因為錯的是伺服器不是客戶端。看到 `ResponseValidationError` 就去對照回傳物件和 model 的差異，通常是某個欄位是 `None` 但 model 宣告成必填。

幾個調整選項：

| 參數 | 效果 | 典型用途 |
| --- | --- | --- |
| `response_model_exclude_none=True` | 值為 `None` 的欄位不出現 | 縮小回應體積 |
| `response_model_exclude_unset=True` | 沒被明確設定的欄位不出現 | PATCH 回應 |
| `response_model_exclude={"internal"}` | 排除指定欄位 | 單點微調 |

**謹慎使用 `exclude_none`。** 它會讓回應的形狀隨資料而變，前端要處理「欄位不存在」和「欄位是 null」兩種情況。除非有明確的體積考量，讓 schema 穩定通常更有價值。

### 繼承減少重複

```python
class UserBase(BaseModel):
    email: EmailStr
    display_name: str

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
```

適度就好。繼承鏈超過兩層之後，「這個 model 到底有哪些欄位」會變得要翻三個檔案才知道，那時候寧可重複。

---

## 七、Pydantic v1 與 v2

v2 在 2023 年發布，核心用 Rust 重寫（`pydantic-core`），效能大幅提升，但 API 有破壞性變更。網路上大量教學仍是 v1 寫法，混用會出現各種「照抄卻不能動」。

| v1 | v2 |
| --- | --- |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes=True` |
| `allow_population_by_field_name` | `populate_by_name` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `@validator` | `@field_validator`（要加 `@classmethod`） |
| `@root_validator` | `@model_validator` |
| `Field(regex=...)` | `Field(pattern=...)` |
| `Optional[str]` 隱含 `= None` | **必須明寫** `= None` |

最後一條是遷移時最常踩的：v1 裡 `Optional[str]` 自動變成選填，v2 不會。升級後大量欄位突然變必填，就是這個原因。

判斷手上專案是哪一版：`pip show pydantic`，或看程式碼裡有沒有 `class Config:`。

---

## 八、常見誤解

**「Pydantic 會做型別檢查，所以型別一定對。」**
Pydantic 做的是**解析與轉換**，`"35.5"` 會變成 `35.5`、`"1"` 會變成 `True`。要拒絕轉換得開 `strict=True`。而且它只在 model 的邊界上作用，你自己寫的普通函式標了型別仍然不受任何檢查。

**「`response_model` 是格式化用的。」**
它會實際過濾欄位，是防止內部資料外洩的機制。沒有它，回傳 ORM 物件等於把資料表整列送給客戶端。

**「直接用 ORM model 當 request body 比較省事。」**
省事的代價是 over-posting 漏洞（客戶端可以送 `is_admin`）、API 契約與資料表結構綁死（改欄位就是 breaking change）、以及回應可能夾帶敏感欄位。輸入、輸出、資料表是三種不同的形狀，該是三個類別。

**「validator 裡可以丟 `HTTPException`。」**
不要。Pydantic 只認得 `ValueError`（與 `AssertionError`），會把它收集成標準的 422 條目；丟 `HTTPException` 會穿過驗證流程變成未處理例外，最後是 500。

**「回應驗證失敗會回 422。」**
會回 **500**。請求驗證失敗才是 422。錯在伺服器，狀態碼就是 5xx。

---

## 九、同事會來問你的問題

**「為什麼要寫三個長得很像的 model？」**
因為它們是三種不同的契約：`Create` 是客戶端能送什麼（擋掉 `is_admin` 這種提權欄位）、`Out` 是客戶端能看到什麼（擋掉 `password_hash`）、ORM model 是資料庫的形狀（會隨 schema 演進）。合成一個就等於把這三件事綁死，任何一邊改動都會波及其他兩邊。

**「422 的 `loc` 怎麼讀？」**
它是從根到出錯欄位的路徑，第一個元素是來源（`body`/`query`/`path`/`header`），後面依序是欄位名與陣列索引。`["body", "items", 0, "quantity"]` 就是 body 裡 items 陣列第一個元素的 quantity。第一個元素和你的預期不符時，問題出在函式簽章而不是客戶端。

**「email 已存在的檢查要寫在 validator 裡嗎？」**
不要。validator 是同步的、不該依賴外部資源，而且這種衝突的正確語意是 409 而不是 422。放在 service 層，查完丟 `HTTPException(409)`。

**「PATCH 怎麼區分『沒送這個欄位』和『送了 null』？」**
把 update model 的欄位全設成選填，取值時用 `model_dump(exclude_unset=True)`——它只回傳客戶端明確送過的欄位。用 `exclude_none=True` 就分不出來了，因為明確送的 `null` 也會被濾掉。

**「這段程式碼有 `class Config:` 和 `.dict()`，是不是壞了？」**
那是 Pydantic v1 的寫法。v2 對應的是 `model_config = ConfigDict(...)` 和 `.model_dump()`。網路上大量文章還停在 v1，照抄會出現各種 deprecation 警告或直接報錯。先 `pip show pydantic` 確認版本再決定照哪個寫。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[01-routing-and-path-operations]] — 上一章：參數來源規則
- [[03-dependency-injection]] — 下一章：`Depends` 與資源生命週期
- [[06-error-handling]] — 改寫 422 格式、例外處理層次
- [[04-model-binding-and-validation]] — ASP.NET Core 的對應章節（DTO 與 over-posting）
