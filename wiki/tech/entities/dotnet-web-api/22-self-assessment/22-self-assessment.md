---
type: concept
domain: tech
tags: [dotnet, aspnet, self-assessment, quiz, interview, review]
sources:
  - raw/tech/web-dev/NET Web API.md
created: 2026-08-15
updated: 2026-08-15
---

# 附錄 A：自我檢測 — 講得出來才算會

## 怎麼用這份題庫

**先蓋住答案自己講一遍。** 心裡覺得「我知道」和真的講得出來是兩件事——後者才是被同事追問時能用的。答案區塊是摺疊的，點開之前先自己說完。

題目分三級：

- **L1 基礎**：讀過該章就該答得出來
- **L2 應用**：需要把兩三個概念串起來
- **L3 診斷**：給症狀反推根因，實務上真正會遇到的形態

L3 答不出來不代表沒學會，但那正是「會用」與「問不倒」的分界。

---

## 一、執行模型（第 00–06 章）

### L1

**1.** Generic Host 負責哪四件事？

<details><summary>答案</summary>

設定（Configuration）、依賴注入、Logging、生命週期管理（啟動與停止 `IHostedService`、處理關機訊號）。Web 應用只是在這之上多掛一個啟動 `IServer` 的 hosted service。

</details>

**2.** `builder.Build()` 之後為什麼不能再 `AddXxx`？

<details><summary>答案</summary>

服務清單被封裝成 `ServiceProvider` 並凍結。容器在建立時預先編譯了每個型別的建構表達式（把反射工作在啟動時做完），允許後期修改就得放棄這層最佳化，並引入執行緒安全問題。

</details>

**3.** 三種 service lifetime 的實例分別存放在哪裡？

<details><summary>答案</summary>

Singleton 在 root provider；Scoped 在當前 scope；Transient 不快取每次新建，但若實作 `IDisposable` 會被解析它的 scope 追蹤到 scope 結束。

</details>

**4.** `app.Use` 和 `app.Run` 的差別？

<details><summary>答案</summary>

`Use` 註冊的 middleware 有 `next` 參數可以往下傳；`Run` 註冊 terminal middleware，簽章沒有 `next`，永遠不往下傳。`app.Run()` 後面註冊的 middleware 是死程式碼。

（注意無參數的 `app.Run()` 是啟動應用程式，與 `app.Run(RequestDelegate)` 同名但完全不同。）

</details>

**5.** `[ApiController]` 帶來哪些行為？

<details><summary>答案</summary>

`ModelState` 無效時自動回 400 + `ValidationProblemDetails`；推斷 binding source（複雜型別視為 `[FromBody]`）；要求使用 attribute routing；錯誤回應統一為 `ProblemDetails`。

</details>

**6.** 為什麼一個 action 只能有一個 `[FromBody]` 參數？

<details><summary>答案</summary>

Request body 是只能讀一次的前向串流，反序列化會整個消耗掉。需要傳多個物件就包成一個 DTO。

</details>

### L2

**7.** 推導 `UseRouting`、`UseCors`、`UseAuthentication`、`UseAuthorization` 的正確順序，並說明每一步的理由。

<details><summary>答案</summary>

`UseRouting` → `UseCors` → `UseAuthentication` → `UseAuthorization`。

`UseRouting` 選出 endpoint 並放進 `HttpContext`；`UseCors` 需要 endpoint metadata 才知道該套用哪個 CORS policy，且必須在 `UseAuthorization` 之前（否則授權短路時回應沒有 CORS header）；`UseAuthentication` 填 `HttpContext.User`；`UseAuthorization` 需要 endpoint metadata（`[Authorize]`）與已填好的 `User`。

</details>

**8.** 為什麼 convention-based middleware 的建構子不能注入 Scoped 服務？正確做法是什麼？

<details><summary>答案</summary>

pipeline 在啟動時組裝一次，middleware 實例是 Singleton。建構子注入 Scoped 服務會把它俘虜成 Singleton（captive dependency）。正確做法是宣告在 `InvokeAsync` 的參數上——框架會用當前 request 的 scope 解析；或改實作 `IMiddleware` 並註冊為 Scoped。

</details>

**9.** `{id}` 和 `{name}` 兩個路由為什麼會衝突？`{id:int}` 為什麼能解決？

<details><summary>答案</summary>

優先序規則是「字面字串 > 有 constraint 的參數 > 無 constraint 的參數 > catch-all」。兩個無 constraint 參數同級且都匹配，拋 `AmbiguousMatchException`。加上 `:int` 讓其中一個升級到較高等級，就分出勝負了。

</details>

**10.** 專案開了 nullable reference types 之後，為什麼沒寫 `[Required]` 的欄位也變成必填？

<details><summary>答案</summary>

驗證系統會把不可為 null 的參考型別自動視為 `[Required]`。這通常是好的預設，但 PATCH 式的部分更新 DTO 必須把欄位宣告成 `string?`，否則使用者不送該欄位就會收到 400。

</details>

**11.** Middleware 和 Filter 該怎麼選？

<details><summary>答案</summary>

問它需不需要 MVC 的上下文——綁定後的參數、是哪個 action、`ModelState`、回傳的 `IActionResult`。需要就用 filter；需要涵蓋所有請求（含靜態檔案、健康檢查）就用 middleware。

</details>

**12.** Exception Filter 接不到哪些例外？

<details><summary>答案</summary>

model binding 階段的、result 執行階段的（JSON 序列化失敗）、middleware 層的，以及所有不走 MVC 的端點。所以它不能當唯一的全域錯誤處理，最後防線必須是 `UseExceptionHandler`。

</details>

**13.** async 讓程式變快了嗎？

<details><summary>答案</summary>

沒有。單一請求甚至因為狀態機開銷略慢。它提升的是吞吐量——I/O 等待期間執行緒被歸還給 ThreadPool 去服務其他請求，同樣的執行緒數能處理數十倍的並行請求。

</details>

### L3

**14.** Pod 反覆重啟，`kubectl logs` 沒有任何錯誤。從哪裡開始查？

<details><summary>答案</summary>

先看 `kubectl describe pod` 的事件，確認是 probe 失敗還是 OOMKilled。若是 startup probe 逾時，常見成因是某個 `IHostedService` 的 `StartAsync` / `ExecuteAsync` 在第一個真正的 await 之前有同步阻塞，卡住整個 Host 的啟動流程——這種情況 log 裡什麼都沒有。

</details>

**15.** CPU 使用率只有 20%，但所有請求都在逾時，重啟後恢復，過幾天再犯。診斷路徑？

<details><summary>答案</summary>

ThreadPool 飢餓。程式碼裡有 `.Result`、`.Wait()` 或 `GetAwaiter().GetResult()` 同步等待非同步操作，佔住執行緒。並行量超過池的最小執行緒數之後，新執行緒每 500 毫秒才增加一個，形成正回饋。CPU 低是因為執行緒是**阻塞**而非忙碌。

用 `dotnet-counters` 看 `ThreadPool Queue Length` 確認，治本是把 async 一路貫穿到底。

</details>

**16.** 前端說「登入過期時會出現 CORS 錯誤」，後端 log 顯示是正常的 401。怎麼回事？

<details><summary>答案</summary>

`UseCors` 排在 `UseAuthorization` 之後（更內層）。授權失敗時 `UseAuthorization` 直接短路返回，`UseCors` 從來沒有執行過，回應因此沒有 `Access-Control-Allow-Origin`。瀏覽器擋掉這個跨域回應，前端看到的就是 CORS 錯誤。

</details>

**17.** 服務在啟動時要跑一次資料初始化，`app.Services.GetRequiredService<AppDbContext>()` 卻拋例外。為什麼？怎麼改？

<details><summary>答案</summary>

`app.Services` 是 root provider，而 DbContext 是 Scoped。從 root 解析 Scoped 會被擋下（避免它被俘虜成事實上的 Singleton）。改成 `using var scope = app.Services.CreateScope();` 再從 `scope.ServiceProvider` 解析。

</details>

**18.** 記憶體每天緩慢上升，重啟就好，壓測卻測不出來。可能的原因？

<details><summary>答案</summary>

需要時間累積的洩漏，兩個典型來源：從 root provider 解析 `IDisposable` 的 Transient 服務（容器會永久持有參考以便日後 dispose）；以及 `CreateScope()` 沒有 `using`（scope 內的所有服務與資料庫連線都不會被回收）。

</details>

**19.** 匯出十萬筆資料時記憶體爆掉，怎麼改？

<details><summary>答案</summary>

不要 `ToListAsync()` 之後再回傳。改回傳 `IAsyncEnumerable<T>` 讓框架邊查邊寫 JSON，記憶體用量從整份資料降到單筆。記得加 `[EnumeratorCancellation]`，並且 DbContext 要在整個串流期間存活。

</details>

---

## 二、資料層（第 07–10 章）

### L1

**20.** 為什麼改了實體的屬性、沒呼叫 `Update()` 也會存進資料庫？

<details><summary>答案</summary>

查詢出來的實體被 change tracker 追蹤，並拍了一份快照。`SaveChanges` 時逐屬性與快照比對，發現差異就標為 `Modified` 並產生只更新變動欄位的 UPDATE。

</details>

**21.** `FindAsync` 與 `FirstOrDefaultAsync` 的差別？

<details><summary>答案</summary>

`FindAsync` 先查 identity map，命中就直接回傳、一條 SQL 都不發，且只能用主鍵查。`FirstOrDefaultAsync` 一定查資料庫，但若查到的主鍵已在追蹤中，回傳的仍是既有物件實例。

</details>

**22.** `AsNoTracking()` 什麼時候該加？

<details><summary>答案</summary>

查出來的資料不會被修改後存回去時。純查詢的 GET、報表、匯出都該加。投影成 DTO 時不需要——投影結果本來就不被追蹤。

</details>

**23.** Oracle 裡空字串等於什麼？

<details><summary>答案</summary>

`NULL`。存進 `""` 讀出來是 null，`WHERE X = ''` 永遠不匹配。要在應用層統一正規化，且不要設計依賴「空字串 ≠ null」的邏輯。

</details>

### L2

**24.** 為什麼 `DbContext` 必須是 Scoped？從 EF Core 這一側說三個理由。

<details><summary>答案</summary>

非執行緒安全（change tracker 是普通字典，並行會拋 `A second operation was started`）；change tracker 只增不減，長壽會變成記憶體洩漏；identity map 讓它讀到的資料越活越久越可能過期。

</details>

**25.** `_db.Update(entity)` 有什麼風險？

<details><summary>答案</summary>

它把**所有**屬性標為 Modified。DTO 沒帶到的欄位會被寫成 CLR 預設值——`CreatedAt` 變 `0001-01-01`、`PasswordHash` 變 null。這是實務上常見的資料損毀來源。改成先查出實體再逐欄位賦值。

</details>

**26.** `Include` 兩個集合導覽為什麼會出問題？怎麼解？

<details><summary>答案</summary>

JOIN 造成笛卡兒爆炸——1 筆訂單 × 10 品項 × 5 付款 = 50 列，每列都重複訂單本身的所有欄位。用 `AsSplitQuery()` 拆成多條查詢（代價是失去單一快照的一致性），或更好的是改用投影只取需要的欄位。

</details>

**27.** 為什麼分頁一定要有 `OrderBy`？

<details><summary>答案</summary>

沒有 `ORDER BY` 時關聯式資料庫不保證回傳順序，翻頁會出現重複或遺漏的資料。而且排序鍵必須唯一——只用 `CreatedAt` 排序時同一秒的多筆順序仍不確定，要加主鍵當決勝鍵。

</details>

**28.** 交易已經包住了，為什麼還會發生「兩個人同時買到最後一張票」？

<details><summary>答案</summary>

交易保證原子性與一致性，不保證「我讀到的值在寫回去之前沒被改過」。在 Read Committed 下兩個交易都讀到 1、都通過檢查、都寫入 0——遺失更新。要靠並發 token、單條原子 UPDATE 或悲觀鎖解決。

</details>

**29.** Oracle 上怎麼做樂觀併發？為什麼不能用 `[Timestamp]`？

<details><summary>答案</summary>

`[Timestamp]` 依賴 SQL Server 的 rowversion，Oracle 沒有。做法是自己加一個整數 `Version` 欄位標記 `[ConcurrencyCheck]`，在 `SaveChanges` 覆寫或攔截器裡統一遞增。`ORA_ROWSCN` 預設是區塊粒度會大量誤判，除非建表時指定 `ROWDEPENDENCIES`。

</details>

### L3

**30.** 列表 API 三秒才回應，但資料庫的慢查詢紀錄是空的。

<details><summary>答案</summary>

N+1——大量的小查詢，每條都很快但總數上千。打開 SQL 記錄看查詢**條數**而非單條耗時。解法優先序：改用投影 `Select`；需要完整實體時用 `Include`；多個集合導覽時加 `AsSplitQuery()`。

</details>

**31.** SQL*Plus 執行 `SELECT * FROM USERS` 說表不存在，但 API 正常運作。

<details><summary>答案</summary>

EF Core 的 Oracle provider 為識別碼加引號，建出的是混合大小寫的 `"Users"`。加引號的識別碼在 Oracle 是大小寫敏感的。解法是在 `OnModelCreating` 用慣例把表名與欄位名統一轉成全大寫。

</details>

**32.** 有 CLOB 欄位的表，列表查詢特別慢，但手動執行同樣條件的 SQL 很快。

<details><summary>答案</summary>

EF Core 查完整實體會 SELECT 所有欄位含 CLOB，而 CLOB 存在獨立區段、讀取需要額外往返。手動查的 SQL 只選了幾個欄位。改用投影只取需要的欄位。

</details>

**33.** 「連線池已滿」的錯誤，第一個該查什麼？

<details><summary>答案</summary>

長交易。交易裡有沒有外部 HTTP 呼叫、迴圈寄信、或忘記 `using` 的 `CreateScope()`。連線池大小是最後才調的參數，不是第一個。

</details>

**34.** 開了 `EnableRetryOnFailure` 之後 `BeginTransactionAsync` 開始報錯。

<details><summary>答案</summary>

執行策略需要重播整個操作，但無法重播使用者手寫的交易區塊。把整段包進 `Database.CreateExecutionStrategy().ExecuteAsync(...)`。

</details>

---

## 三、認證授權（第 11–14 章）

### L1

**35.** 401 和 403 的差別？

<details><summary>答案</summary>

401 = 未認證（沒表明身分或身分無效），前端該觸發重新登入；403 = 已認證但權限不足，前端該顯示權限不足訊息。混淆會造成登入迴圈。

</details>

**36.** `UseAuthentication()` 會拒絕沒帶 token 的請求嗎？

<details><summary>答案</summary>

不會。它只負責呼叫 handler 並填 `HttpContext.User`，沒帶 token 就填一個匿名身分，請求繼續往下走。拒絕是 `UseAuthorization` 加 `[Authorize]` 的事。

</details>

**37.** JWT 的 payload 是加密的嗎？

<details><summary>答案</summary>

不是。它只是 Base64URL 編碼，任何人都能解開讀取。簽章保護的是不可竄改，不是不可讀取。所以絕不能放敏感資料。

</details>

**38.** `ClockSkew` 的預設值是多少？有什麼影響？

<details><summary>答案</summary>

5 分鐘。標示 10 分鐘過期的 token 實際上最多可用 15 分鐘。用短期 access token 策略時不調小它等於策略失效。

</details>

### L2

**39.** 為什麼 API 專案會回 302 導向登入頁？

<details><summary>答案</summary>

預設的 challenge scheme 是 Cookie，而 Cookie handler 的 challenge 行為就是導向登入頁。把 `AddAuthentication` 的預設 scheme 設成 Bearer，或明確設定 `DefaultChallengeScheme`。

</details>

**40.** `[Authorize(Roles = "Admin")]` 一直失敗，token 裡明明有 role claim。

<details><summary>答案</summary>

`RoleClaimType` 與 token 裡的 claim 名稱不一致。框架看的是 `TokenValidationParameters.RoleClaimType` 指定的那個 claim。關閉 inbound claim 映射（`MapInboundClaims = false`）時特別容易出這個問題。

</details>

**41.** 使用者被停權了，為什麼還能繼續呼叫 API？

<details><summary>答案</summary>

JWT 無狀態，簽發時的資訊是快照，伺服器不保存 session 也無法撤銷已簽發的 token。解法是短期 access token（5–15 分鐘）+ 可撤銷的 refresh token，或加黑名單 / SecurityStamp 檢查（代價是失去無狀態的效能優勢）。

</details>

**42.** 驗證 Google ID token 時，除了簽章還必須檢查什麼？

<details><summary>答案</summary>

`aud` 必須等於自己的 client ID——否則別的網站簽發給它自己的 Google token 也能登入你的系統（簽章一樣是真的）。還要檢查 `email_verified`，並用 `sub` 而非 email 當唯一鍵。

</details>

**43.** 「使用者只能刪除自己的訂單」為什麼不能用 attribute 表達？

<details><summary>答案</summary>

授權 filter 跑在 model binding 與資料查詢之前，拿不到「是哪一筆訂單」。要用 resource-based authorization——在 action 裡載入資源後呼叫 `IAuthorizationService.AuthorizeAsync(User, resource, requirement)`。

</details>

### L3

**44.** OAuth 登入成功後陷入無限重導向。

<details><summary>答案</summary>

反向代理後面的 scheme 問題。應用程式看到的是 HTTP，於是產生 http 的 redirect URI 與非 Secure 的 cookie，瀏覽器丟棄後又判定未登入。加 `app.UseForwardedHeaders()`（放在所有 middleware 最前面）並設定信任 `XForwardedProto`。

</details>

**45.** `Correlation failed` 是什麼原因？

<details><summary>答案</summary>

存放 OAuth `state` 的 correlation cookie 沒有被送回來。三個常見原因：cookie 的 `SameSite`/`Secure` 設定與當前協定不符（本機用 http 測試最常見）、反向代理的 scheme 問題、使用者在登入頁停留太久導致 cookie 過期。

</details>

**46.** 怎麼確保沒有 endpoint 忘記加授權？

<details><summary>答案</summary>

設定 `AuthorizationOptions.FallbackPolicy` 要求已認證使用者——沒有任何授權 metadata 的 endpoint 會套用它，預設從「開放」變成「關閉」。公開端點明確標 `[AllowAnonymous]`，記得健康檢查端點也要開放，否則 K8s probe 拿到 401 會導致 Pod 反覆重啟。

</details>

**47.** 多租戶系統怎麼確保不會查到別的租戶的資料？

<details><summary>答案</summary>

用 EF Core 的 `HasQueryFilter` 全域篩選 `TenantId`，讓「忘記加條件」不再可能。三個注意事項：`IgnoreQueryFilters()` 能繞過它、寫入端不受保護要另外處理、以及這個 DbContext 不能用 pooling（租戶上下文會跨請求殘留）。

</details>

---

## 四、工程實務（第 15–21 章）

### L1

**48.** 為什麼不該把所有回應都包成 200？

<details><summary>答案</summary>

HTTP 語意消失：監控看不到錯誤率、快取會快取錯誤回應、前端必須解析 body 才知道結果、重試邏輯無從判斷。

</details>

**49.** 4xx 和 5xx 的分界為什麼重要？

<details><summary>答案</summary>

4xx 是客戶端的問題，不該觸發告警；5xx 是伺服器的問題，該告警。把 404 回成 500 會讓錯誤率失真並造成告警疲勞；把真實故障回成 400 會讓事故被埋沒。

</details>

**50.** 結構化 logging 的訊息模板寫法為什麼重要？

<details><summary>答案</summary>

`_logger.LogInformation("使用者 {UserId} 下單", userId)` 會把參數保留成獨立欄位，在 Kibana 可以精確查詢與聚合；字串插值產生的只是一整串不可查詢的文字。成本是零，收益很大。

</details>

**51.** 三個 Options 介面的差別？

<details><summary>答案</summary>

`IOptions<T>` 是 Singleton，啟動時讀一次永不更新；`IOptionsSnapshot<T>` 是 Scoped，每個 request 重新計算（不能注入 Singleton 服務）；`IOptionsMonitor<T>` 是 Singleton 但有 `CurrentValue` 與變更通知，背景服務要用它。

</details>

**52.** `HttpClient` 為什麼不能用 `using` 包？

<details><summary>答案</summary>

dispose 後底層 TCP 連線進入 TIME_WAIT 約四分鐘才釋放，高頻呼叫會耗盡 socket。但改用 static 單例又會讓連線永不重建、DNS 變更不被感知。正解是 `IHttpClientFactory`——它池化 handler 且 handler 有生命週期會輪替。

</details>

### L2

**53.** 為什麼 liveness probe 不能檢查資料庫？

<details><summary>答案</summary>

liveness 失敗會**重啟 Pod**。資料庫短暫抖動會讓所有 Pod 同時失敗、同時重啟，服務完全中斷，而重啟並不能解決資料庫的問題，於是進入無限重啟。依賴檢查放 readiness——失敗只是被移出負載平衡，恢復後自動回來。

</details>

**54.** 改了 ConfigMap 為什麼沒生效？

<details><summary>答案</summary>

用環境變數注入的話不可能生效——環境變數在程序啟動時就固定了，這是作業系統層級的事實。要熱重載必須用 volume 掛載，並搭配 `IOptionsSnapshot` 或 `IOptionsMonitor`。

</details>

**55.** 重試機制有哪三條紀律？

<details><summary>答案</summary>

只重試冪等操作（否則可能扣兩次款）；只重試暫時性錯誤（對 4xx 重試沒有意義）；必須有指數退避與 jitter（否則所有客戶端同時重試，把正在恢復的下游再次打垮）。

</details>

**56.** 斷路器的核心價值是什麼？

<details><summary>答案</summary>

Open 狀態下的**快速失敗**——請求在毫秒內得到「服務不可用」，而不是等滿 10 秒逾時。這讓你的 API 在下游故障時仍保持回應能力，只有那個特定功能降級，避免級聯故障。

</details>

**57.** 為什麼 metrics 的標籤不能放 user_id？

<details><summary>答案</summary>

每個唯一的標籤組合產生一條獨立時間序列。一百萬使用者就是一百萬條序列，會炸掉 Prometheus 的記憶體。「是誰」用 log 查，metrics 的標籤只放有限且穩定的維度。

</details>

**58.** 為什麼不該用 InMemory provider 測資料存取？

<details><summary>答案</summary>

它不做真實的 LINQ 翻譯（任何查詢都能在記憶體執行，包含真實資料庫會拋 `could not be translated` 的）、不檢查唯一與外鍵約束、交易幾乎是空操作。測試通過不代表能在真實資料庫跑。用 Testcontainers。

</details>

**59.** 為什麼「刪除欄位」要拆成兩次部署？

<details><summary>答案</summary>

滾動更新期間新舊版本同時運行。一次做完的話，還在跑的舊 Pod 會因為欄位不見而全部報錯。先部署「程式碼停止使用該欄位」，下一次部署才真的刪除。

</details>

### L3

**60.** 擴容之後每個客戶收到三封相同的通知信。

<details><summary>答案</summary>

`BackgroundService` 在每個 Pod 都跑一份。排程工作應該用 K8s CronJob（K8s 保證只跑一次），或用 Hangfire（共用資料庫佇列），或自己用資料庫唯一索引做分散式鎖——注意要靠唯一約束而非「先查再插」，後者有競爭視窗。

</details>

**61.** 加了快取之後，尖峰時段資料庫負載反而更高。

<details><summary>答案</summary>

Cache stampede——快取同時過期，大量請求同時回源。加鎖（含雙重檢查）確保只有一個請求去載入，並在 TTL 上加隨機抖動避免大量項目集體過期。

</details>

**62.** Pod 一直 OOMKilled，本機測記憶體明明夠用。

<details><summary>答案</summary>

三個方向：Server GC 在容器裡記憶體用量較大（確認 limits 有設好讓容器感知生效，必要時測 `DOTNET_gcServer=0`）；長壽 DbContext 的 change tracker 累積；沒有設 `SizeLimit` 的 `IMemoryCache`。

</details>

**63.** CPU limit 從 `1000m` 調到 `500m` 之後，偶發逾時明顯變多。

<details><summary>答案</summary>

CPU limit 影響 `Environment.ProcessorCount`，進而決定 ThreadPool 的最小執行緒數。半個核心讓池子起始很小，ThreadPool 飢餓更容易被觸發。要嘛放寬 limit，要嘛徹底消除程式碼裡的同步阻塞。

</details>

**64.** 使用者截圖回報「出現錯誤」，怎麼在幾分鐘內定位?

<details><summary>答案</summary>

前提是事先做好三件事：錯誤回應的 `ProblemDetails` 帶 `traceId`（來自 `Activity.Current`）、log 用結構化格式輸出到 stdout、`IncludeScopes` 有開啟。有了這些，在 Kibana 用 traceId 搜尋就能撈出整條請求鏈的所有 log，含跨服務的部分。

</details>

**65.** 改一行程式碼，Docker build 要跑五分鐘。

<details><summary>答案</summary>

`COPY . .` 放在 `dotnet restore` 之前，導致 layer 快取每次都失效、重新下載所有套件。先只複製 `.csproj` 做 restore，再複製其餘原始碼。

</details>

---

## 紅色警戒清單

以下每一項在生產環境都造成過真實事故。看到就該停下來。

1. **`.Result` / `.Wait()` / `GetAwaiter().GetResult()`** —— ThreadPool 飢餓（第 06 章）
2. **`async void`** —— 例外無法捕捉，直接讓程序當掉（第 06 章）
3. **Singleton 服務持有 `DbContext` 或任何 request 狀態** —— 資料錯亂與跨使用者洩漏（第 02 章）
4. **`CreateScope()` 沒有 `using`** —— 連線與資源永不釋放（第 02 章）
5. **用 Entity 當 API 的輸入型別** —— over-posting，`IsAdmin` 可被客戶端設定（第 04 章）
6. **直接回傳 Entity** —— `PasswordHash` 與內部欄位被序列化出去（第 04 章）
7. **`_db.Update(entity)` 配部分欄位的 DTO** —— 未帶到的欄位被寫成預設值（第 07 章）
8. **生產環境開 `EnableSensitiveDataLogging`** —— 參數值（含密碼）進 log（第 08 章）
9. **`FromSqlRaw` + 字串串接** —— SQL injection（第 08 章）
10. **交易裡呼叫外部 HTTP 服務** —— 連線被長時間佔用，且無法原子化（第 09 章）
11. **`ValidateIssuerSigningKey = false`** —— 任何人都能偽造 token（第 12 章）
12. **JWT payload 放敏感資料** —— Base64 任何人都能解開（第 12 章）
13. **Refresh token 明文存資料庫** —— 資料庫外洩等於所有帳號被接管（第 12 章）
14. **驗證 Google ID token 不檢查 `aud`** —— 別站的 token 也能登入（第 13 章）
15. **忘記 `[Authorize]` 且沒設 `FallbackPolicy`** —— endpoint 對全世界開放（第 14 章）
16. **健康檢查端點沒有 `AllowAnonymous`** —— probe 拿到 401，Pod 反覆重啟（第 14 章）
17. **把例外訊息直接回給客戶端** —— 洩漏連線字串、內部路徑、SQL（第 15 章）
18. **liveness probe 檢查資料庫** —— 資料庫抖動導致全體 Pod 同時重啟（第 16 章）
19. **機密進版控** —— git 歷史永久留存，唯一有效的補救是輪替憑證（第 17 章）
20. **`HttpClient.Timeout` 保持預設 100 秒** —— 下游變慢時級聯故障（第 18 章）
21. **Output caching 用在含個人化資料的回應** —— A 使用者的資料被回給 B（第 18 章）
22. **`Channel.CreateUnbounded`** —— 消費跟不上時無限成長直到 OOM（第 19 章）
23. **Hangfire dashboard 未加授權** —— 任何人可觸發任意工作（第 19 章）
24. **測試用的 authentication handler 出現在生產環境** —— 任何人都能自稱管理員（第 20 章）
25. **schema 變更不向前相容** —— 滾動更新期間舊版 Pod 全部報錯（第 21 章）

---

## 連結

- [[dotnet-web-api]] — 教材總目錄與速查
- [[21-deployment]] — 上一章
- [[23-cheatsheet]] — 附錄 B：速查表
