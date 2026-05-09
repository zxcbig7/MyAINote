# Swagger 在 HTTP Pipeline 中的位置與設計理由

# 一、Swagger 在 HTTP Pipeline 中的位置與設計理由

這一節的目標只有一個：讓你「看到 Program.cs 就能立即判斷 Swagger 放得對不對」

## 二、Swagger 實際在 ASP.NET Core 中「是什麼」

Swagger 在 ASP.NET Core 裡 **不是單一功能**，而是兩個 Middleware：

| Middleware | 功能 |
| --- | --- |
| `UseSwagger()` | 提供 `/swagger/v1/swagger.json` |
| `UseSwaggerUI()` | 提供 `/swagger/index.html`（UI） |

## 三、Swagger 在 Pipeline 中的正確位置（結論先給）

### 標準且正確的放置方式

```csharp
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}
```

**位置：在所有「會影響請求流程的 Middleware 之前」**

```csharp
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseRouting();
app.UseCors("AllowFrontend");
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

## 四、為什麼 Swagger 一定要放這麼前面

### 關鍵原因 1：Swagger 自己就是一組 Endpoint

Swagger 會註冊：

- `/swagger/v1/swagger.json`
- `/swagger/index.html`

這代表：

- 它必須在 **Request 還沒被限制、驗證、攔截前就能被存取**
- 否則你會遇到：
    - Swagger UI 打不開
    - Swagger JSON 被 401 / 403 擋掉

---

### 關鍵原因 2：Swagger 不應被 Authorization 影響（預設情況）

如果你把 Swagger 放在這裡：

```csharp
app.UseAuthentication();
app.UseAuthorization();

app.UseSwagger();// ❌
app.UseSwaggerUI();// ❌

```

結果會是：

- Swagger UI 請求也要驗證身分
- Swagger JSON 被 `[Authorize]` 擋住
- UI 顯示空白或一直 loading

**這在 90% 專案中不是你要的行為**

## 五、Swagger 與 Routing 的實際關係

### 常見誤解

> Swagger 需要 UseRouting()
> 

**錯**

Swagger 使用的是：

- Endpoint Routing（內部註冊）
- 不依賴你自己寫的 Controller Routing

因此：

```csharp
app.UseSwagger();
app.UseSwaggerUI();
app.UseRouting();
```

是 **完全合法而且正常的**

## 六、為什麼幾乎所有專案都只在 Development 開 Swagger

### 原因不是「因為大家都這樣做」

而是三個非常實際的理由：

### 1. 資安風險

Swagger 會暴露：

- 所有 API 路徑
- 所有 DTO 結構
- 所有參數定義

在 Production 等同於：

> 把 API 規格書直接公開給外部
> 

### 2. Swagger UI 本身不是給使用者用的

Swagger 的受眾是：

- Backend Developer
- Frontend Developer
- QA

不是 End User。

---

### 3. Production 有更好的替代方案

實務上 Production 會用：

- 匯出 OpenAPI JSON
- 丟給 Postman / Stoplight / Redoc
- 或放在內部文件系統

## 七、常見錯誤放法與實際後果

### 錯誤 1：放在 `MapControllers()` 後面

```csharp
app.MapControllers();
app.UseSwagger();// ❌

```

後果：

- Swagger 永遠不會被執行
- Pipeline 已經結束

---

### 錯誤 2：放在 Authorization 後面

```csharp
app.UseAuthorization();
app.UseSwagger();// ❌

```

後果：

- Swagger 被授權機制攔截
- UI 無法正常使用

---

## 八、這一節你應該帶走的「判斷規則」

只記住這三句就夠了：

1. **Swagger 是 Middleware，不是工具**
2. **Swagger 要放在 Pipeline 很前面**
3. **預設只在 Development 開**