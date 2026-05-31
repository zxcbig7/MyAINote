---
tags: [web-dev, dotnet, csharp, web-api, backend]
---

> 關聯：[[dotnet-web-api]]、[[csharp]]

# Chapter 1：HTTP 與 Web API 的核心概念

## 1.1  Web API 與 HTTP

- Web API 的本質是 **[[HTTP Server]]的實作**
- ASP.NET Core 負責處理：
    - HTTP Request 解析
    - Routing
    - Response 組裝
- Controller、Attribute、Middleware 都是建立在 HTTP 模型之上的抽象

**設計原則**

- 所有 API 行為都應能映射回 HTTP 的語意
- 不理解 HTTP，API 設計必然混亂

> 不是在「寫 .NET API」，你是在「用 .NET 寫一個 HTTP Server」。
> 

## 1.2 HTTP 的基本互動模型

> HTTP 採用的是 Request / Response 模型。
> 

**關鍵原則**

- Request 表達「我想做什麼」
- Response 表達「結果如何」

### 1.2.1 Request（請求）

一個 HTTP Request 至少包含以下元素：

1. Method 表示「你要對這個資源做什麼事」
2. URL 表示「你要操作哪一個資源」
3. Headers 補充資訊（身份、格式、語言、授權）
4. Body（可選）傳送資料本體（通常是 JSON）

<aside>
💡

範例（語意說明）：我用 `GET` (Method) 去存取 `/api/users/123` (URL) 並且告訴伺服器我想要 `application/json` (Body)

</aside>

```tsx
// 無 body
fetch("/api/users/123", {
  method: "GET", // Method：要對資源做什麼
  headers: {
    "Accept": "application/json",          // Headers：期望回傳格式
    "Authorization": "Bearer <token>"      // Headers：身分與授權
  }
});
```

前端使用 React 透過 `fetch` 發送一個 `GET` Request 到 `/api/users/123`，在 Headers 中攜帶授權資訊並指定期望回傳 `application/json`，因為是讀取資料，所以沒有傳送 Body。

```tsx
// 有 body
fetch("/api/users", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer <token>"
  },
  body: JSON.stringify({
    name: "Vic",
    email: "vic@example.com"
  })
});
```

前端使用 React 發送 `POST` Request 建立使用者，在 Headers 中宣告資料格式與授權資訊，並在 Body 中傳送使用者資料。

### 1.2.2 Response（回應）

伺服器回傳的 Response 也有固定結構：

1. Status Code 告訴 Client「結果如何」
2. Headers 描述回傳內容、快取、授權等
3. Body（可選）實際資料內容

## 1.3 HTTP Method 的真正語意

### **1.3.1 為什麼要區分 Method**

HTTP Method 的存在，是為了讓 Client 與 Server 在不溝通實作細節的情況下，仍能理解彼此的意圖。這是 Web 能夠大規模擴展的關鍵。

### 1.3.2 常用 Method 的正確語意

**設計原則**

- Method 表達「行為語意」
- 不應濫用 POST 取代所有操作

### GET

- 用途：**讀取資源**
- 不應修改伺服器狀態
- 可快取
- 冪等（多次結果一致）

錯誤用法：

- 用 GET 來新增資料
- 用 GET 觸發業務流程

---

### POST

- 用途：**建立新資源或觸發行為**
- 特性：
    - 非冪等
    - 常用於新增、登入、流程啟動
    - 通常會產生新資料

常見場景：

- 新增資料
- 登入（因為會產生 token）

---

### PUT

- 用途：**完整取代資源**
- 特性：
    - 冪等
    - 必須提供完整資料
    - 你送什麼，資源就變成什麼

---

### PATCH

- 用途：**部分更新資源**
- 特性：
    - 非必須傳完整資料
    - 較符合現代 API 使用情境

---

### DELETE

- 用途：**刪除資源**
- 特性：
    - 冪等（刪第二次結果一樣）

## 1.4 Status Code 的設計哲學

> Status Code 不是給機器看的，是給「使用 API 的人」看的。
> 

### 常見且必要的幾個

- **200 OK** 請求成功，有回傳資料
- **201 Created** 成功建立新資源（通常搭配 POST）
- **400 Bad Request** Client 傳的資料有問題
- **401 Unauthorized** 沒有身份（未登入）
- **403 Forbidden** 有身份但沒權限
- **404 Not Found** 資源不存在
- **500 Internal Server Error** Server 端錯誤（不該頻繁出現）

<aside>
💡

**重要原則：**不要把所有錯誤都包成 200。

</aside>

## 1.5 REST 的核心概念：Resource（資源）

REST API 的關鍵不是 Method，而是 **Resource 的設計**。

### 1.5.1 Resource 定義

- Resource 表示系統中的「名詞型對象」
- URL 應描述資源，而非動作
- 使用複數表示集合
- 好的：
    - `/api/users`
    - `/api/orders/123`
    - `/api/users`
    - `/api/users/{id}`
    - `/api/orders/{orderId}/items`
- 不好的：
    - `/api/getUser`
    - `/api/createOrder`

Method 負責「動作」，URL 負責「對象」。