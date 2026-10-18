---
type: concept
domain: tech
tags: [python, fastapi, self-assessment, quiz, review, troubleshooting]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 C：自我檢測 — 蓋住答案，先自己講一遍

## 怎麼用這一份

**規則只有一條：看到問題先把答案蓋住，出聲講一遍，講得出來才算會。**

在心裡「覺得知道」和真的能對同事解釋，中間差了一整個理解的層次。這份的設計就是逼出那個差距——每一題都寫成「同事會這樣問你」的形式，答案摺疊在 `<details>` 裡。

三個難度：

| 級別 | 問什麼 | 答不出來代表 |
| --- | --- | --- |
| **L1** | 事實與定義 | 該回去重讀那一章 |
| **L2** | 給情境，要你做決策並說理由 | 知道 what 不知道 why |
| **L3** | 給症狀，反推根因 | 還沒有排錯能力——這一級才是分水嶺 |

L3 是真正拉開差距的地方。前兩級答得出來代表你讀過，L3 答得出來代表你**上線之後撐得住**。

---

## L1 基礎（22 題）

### 起步與路由

**1. Python 的型別提示執行期會被忽略，FastAPI 的驗證是怎麼生效的？**

<details><summary>答案</summary>

型別提示被存在函式物件的 `__annotations__` 字典裡。FastAPI 在**路由註冊時**（也就是 decorator 執行的當下）用 `inspect.signature()` 讀出簽章與型別，替每個參數建出 Pydantic 驗證器。請求進來時是那些驗證器在跑，不是直譯器。

推論：驗證只發生在 FastAPI 管轄的邊界上，你自己寫的一般函式標了型別仍然不受任何檢查。 → [[00-why-fastapi-and-setup]]
</details>

**2. WSGI 為什麼撐不住現代的 API 需求？**

<details><summary>答案</summary>

它的介面是同步的——函式回傳就代表請求結束，在那之前執行緒完全被佔住，所以一個 worker 同時只能服務一個請求。而且它的模型裡連線只有「進來、處理、出去」三個狀態，放不下 WebSocket 這種長連線。ASGI 把介面改成 `async def app(scope, receive, send)`，回應可分多次送出，連線類型寫進 `scope`。 → [[00-why-fastapi-and-setup]]
</details>

**3. `@app.get("/x")` 和 C# 的 `[HttpGet("/x")]` 機制上差在哪？**

<details><summary>答案</summary>

attribute 是編譯進組件的**中繼資料**，框架靠反射掃描；decorator 是一個函式，在模組載入時**立刻執行**——`@app.get("/x")` 的實際效果是當場把路由 append 進 router 的清單。

所以路由的宣告順序就是匹配的嘗試順序，而 .NET 那邊有一套獨立的優先序演算法。 → [[00-why-fastapi-and-setup]]、[[01-routing-and-path-operations]]
</details>

**4. 一個參數會被從 path、query 還是 body 取出，判斷順序是什麼？**

<details><summary>答案</summary>

1. 名稱出現在路徑模板中 → path
2. 有 `Query()`/`Path()`/`Body()`/`Header()`/`Cookie()`/`Form()` 標注 → 依標注
3. 型別是 `Request`/`Response`/`BackgroundTasks` → 框架注入
4. 值是 `Depends(...)` → 依賴
5. 型別是 Pydantic model → body
6. 其餘單純型別 → query

必填/選填**只看有沒有預設值**。 → [[01-routing-and-path-operations]]
</details>

**5. `q: str | None` 沒給預設值，是選填還是必填？**

<details><summary>答案</summary>

**必填**——但允許傳 null。選填只取決於有沒有預設值，要寫成 `q: str | None = None`。這是最常見的誤會之一。 → [[01-routing-and-path-operations]]
</details>

**6. `/items` 和 `/items/` 有差嗎？**

<details><summary>答案</summary>

有。Starlette 預設開 `redirect_slashes`，兩者之間會 307 重導（method 和 body 會保留，所以多半「看起來能動」）。但在反向代理後面，重導的 `Location` 可能指向內部位址；CORS 預檢後的重導在部分瀏覽器組合下也會失敗。團隊統一一種寫法，別依賴重導。 → [[01-routing-and-path-operations]]
</details>

### Pydantic

**7. Pydantic 是型別檢查器嗎？**

<details><summary>答案</summary>

不是，它是**解析器**。`Item(price="35.5")` 會得到 `35.5` 這個 float，不是錯誤。它的模型是「接收未知輸入，嘗試解析成保證合規的物件，解析不成就丟例外」——所以物件建立成功這件事本身，就是資料已通過驗證的證明。要拒絕轉換得開 `strict=True`。 → [[02-pydantic-and-validation]]
</details>

**8. 驗證失敗回幾？和 ASP.NET Core 一樣嗎？**

<details><summary>答案</summary>

FastAPI 回 **422**（語法正確、語意不通過），ASP.NET Core 的 `[ApiController]` 回 400。前端如果同時對接兩種後端要先講好。 → [[02-pydantic-and-validation]]
</details>

**9. 422 回應裡的 `loc` 是什麼？**

<details><summary>答案</summary>

從根到出錯位置的路徑。**第一個元素是來源**（`body`/`query`/`path`/`header`/`cookie`），後面依序是欄位名與陣列索引。`["body", "items", 0, "quantity"]` 就是 body 裡 items 陣列第一個元素的 quantity。

第一個元素和你的預期不符時，問題出在函式簽章而不是客戶端——這是診斷「參數收不到」的主要工具。 → [[02-pydantic-and-validation]]
</details>

**10. validator 裡可以丟 `HTTPException` 嗎？**

<details><summary>答案</summary>

不行。Pydantic 只認得 `ValueError`（與 `AssertionError`），會把它收集成標準的 422 條目。丟 `HTTPException` 會穿過驗證流程變成未處理例外，最後是 500。 → [[02-pydantic-and-validation]]
</details>

**11. `model_config = ConfigDict(from_attributes=True)` 是做什麼的？**

<details><summary>答案</summary>

讓 Pydantic 可以從**任意物件的屬性**讀值，而不只是 dict——SQLAlchemy 的 ORM 實例就是這樣被轉成回應 model 的。沒有這一行，`response_model` 遇到 ORM 物件會失敗。

v1 時代這個設定叫 `orm_mode`，網路上舊文章很多。 → [[02-pydantic-and-validation]]
</details>

### 依賴與並發

**12. FastAPI 的 DI 和 .NET 的 DI，三個根本差異是什麼？**

<details><summary>答案</summary>

1. **沒有集中註冊表**——`Depends` 直接指向函式
2. **沒有介面到實作的對應**——要替換得用 `dependency_overrides`
3. **解析在每個 request 現場進行**而非啟動時建圖——漏掉的依賴不會在啟動時被抓到

第三點的實務意義最大：測試覆蓋率因此比 .NET 更重要。 → [[03-dependency-injection]]
</details>

**13. Scoped 在 FastAPI 怎麼實作的？**

<details><summary>答案</summary>

就是一般的 `Depends`。**同一個 request 內，同一個依賴只會被呼叫一次，結果快取起來共用**——這就是 Scoped 的語意。沒有這個快取，一個 request 會開出好幾個資料庫連線且各在不同交易裡。

需要收尾（關 session）就用 `yield` 版本。 → [[03-dependency-injection]]
</details>

**14. `yield` dependency 的收尾在什麼時候執行？**

<details><summary>答案</summary>

在**回應送出之前**（0.106 版之後）。舊版是反過來的，所以「在背景任務裡用 yield 出來的 session」這種寫法現在會拿到已關閉的資源。 → [[03-dependency-injection]]
</details>

**15. `def` 和 `async def` 的 endpoint，FastAPI 分別怎麼處理？**

<details><summary>答案</summary>

`async def` 直接在 event loop 上 `await`；`def` 會被 `run_in_threadpool` 包起來丟到 threadpool（預設上限 40 條）執行。

**所以寫 `def` 的時候，FastAPI 幫你把阻塞隔離掉了。** → [[04-async-and-concurrency]]
</details>

**16. 為什麼說「`async def` 包同步程式碼比 `def` 危險」？**

<details><summary>答案</summary>

event loop 是單執行緒的協作式並發，任務必須自己在 `await` 讓出控制權。`async def` 裡的同步阻塞不會讓出，整個程序在那段時間**不處理任何請求**，包含 `/health`。寫成 `def` 則被隔離在 threadpool 裡，event loop 完全不受影響。 → [[04-async-and-concurrency]]
</details>

### 資料與錯誤

**17. `Engine` 和 `Session` 各自的生命週期是什麼？**

<details><summary>答案</summary>

`Engine` 持有連線池，建立成本高，**必須是程序層級單例**。`Session` 對應 EF Core 的 `DbContext`，不是執行緒安全的，**一個 request 一個**。

兩者不能搞反：模組層級的 `Session` 會累積 identity map、讓不同請求看到彼此未提交的資料。 → [[05-database-sqlalchemy]]
</details>

**18. `selectinload` 和 `joinedload` 怎麼選？**

<details><summary>答案</summary>

一對多用 `selectinload`（主查詢 + 一次 `WHERE id IN (...)`），一對一/多對一用 `joinedload`（單一 LEFT OUTER JOIN）。

一對多用 `joinedload` 會產生笛卡兒式的列數膨脹——10 筆訂單各 20 個品項就是 200 列。 → [[05-database-sqlalchemy]]
</details>

**19. 401 和 403 的分界是什麼？**

<details><summary>答案</summary>

**身分**，不是「有沒有登入」。token 過期是 401（身分無法確認），一般使用者想刪別人的訂單是 403（身分確認了，權限不夠）。

另外：不該讓對方知道資源存在時，回 **404** 而不是 403。 → [[06-error-handling]]
</details>

**20. 例外處理器該註冊在 `fastapi.HTTPException` 還是 `StarletteHTTPException`？**

<details><summary>答案</summary>

**`StarletteHTTPException`**（父類別）。FastAPI 的 `HTTPException` 繼承自它，但**框架內部產生的 404（路由不存在）、405（method 不允許）丟的是 Starlette 那個**。註冊在父類別才能一網打盡。 → [[06-error-handling]]
</details>

### 認證與部署

**21. `OAuth2PasswordBearer` 做了什麼？**

<details><summary>答案</summary>

**兩件事**：從 `Authorization` header 讀出 `Bearer ` 後面那串字，以及讓 `/docs` 產生授權介面。

它**不驗證簽章、不檢查過期、不知道使用者是誰**。header 有東西就放行，內容是 `abc` 也一樣。 → [[07-auth-and-jwt]]
</details>

**22. middleware 的註冊順序和執行順序是什麼關係？**

<details><summary>答案</summary>

**相反**。Starlette 的 `add_middleware` 是 `insert(0, ...)`，所以最後註冊的包在最外層。這和 ASP.NET Core 的 `app.UseX()`（註冊序即執行序）相反，而且不會有任何錯誤提示。

推論：`CORSMiddleware` 要**最後**註冊。 → [[08-middleware-and-cross-cutting]]
</details>

---

## L2 應用（20 題）

**23. 一支 endpoint 要查 Oracle（用同步 SQLAlchemy）然後呼叫一個外部 API，該寫 `def` 還是 `async def`？**

<details><summary>答案</summary>

寫 `def`。只要有**任何一個**同步阻塞呼叫，整支函式就該是 `def`，讓 FastAPI 把它隔離到 threadpool。

如果外部呼叫要用 `httpx.AsyncClient`，那就是 `async def` + 把同步的 DB 查詢包進 `asyncio.to_thread(...)`。但更務實的做法是統一用同步版本的 client，整支寫 `def`。 → [[04-async-and-concurrency]]
</details>

**24. 專案要接 Oracle，該用同步還是 async SQLAlchemy？**

<details><summary>答案</summary>

**同步 + `def`**，除非有明確理由。async 的四項代價：整條鏈不能有任何同步呼叫、lazy load 直接不合法（`MissingGreenlet`）、驅動選擇變少、stack trace 穿過 greenlet 難讀。

真正需要 async 的訊號是「單一請求要並行發多個獨立查詢」或「已經大量使用 async」，不是「因為 FastAPI 是 async 框架」。 → [[05-database-sqlalchemy]]
</details>

**25. 給你這組數字：4 個 Pod 副本、每個 1 個 worker、`pool_size=20`、`max_overflow=10`、PostgreSQL `max_connections=100`。這樣可以嗎？**

<details><summary>答案</summary>

不行。`4 × (20 + 10) = 120`，超過 `100 × 0.8 = 80`。

三個方向：降 `pool_size`（例如降到 15 → `4 × 20 = 80`，剛好踩線，再保守一點更好）、減少副本數、或加一層連線池代理（PgBouncer / Oracle DRCP）。 → [[05-database-sqlalchemy]]、[[11-deployment]]
</details>

**26. 交易的 commit 該寫在哪？三種寫法各有什麼取捨？**

<details><summary>答案</summary>

- **依賴只負責開關 + rollback，endpoint 明確 commit**：交易邊界顯性，可做多個獨立交易；但要記得寫。**小專案選這個。**
- **依賴代管 commit**：不會忘記；但邊界隱性，而且**非資料庫的副作用（寄信、外部 API）不會跟著回滾**，容易誤以為有原子性。有外部副作用的專案別用。
- **service 層 commit**：專案長大後的自然歸宿。**中大型專案選這個。** → [[05-database-sqlalchemy]]
</details>

**27. 要新增一種業務錯誤「訂單已退款不能取消」，該怎麼做？**

<details><summary>答案</summary>

在 `core/exceptions.py` 定義一個 `ConflictError` 的子類別（`code = "order_already_refunded"`），service 層 `raise` 它。**API 層不需要改任何東西**——那支 `DomainError` 的 handler 會自動轉成 409 並帶上 `code`。

前端拿到的是可以直接 switch 的機器可讀識別，而不是一個要靠訊息字串猜的 409。 → [[06-error-handling]]
</details>

**28. 「email 已被註冊」的檢查該寫在哪？**

<details><summary>答案</summary>

service 層，而且**唯一索引 + `try/except IntegrityError` 才是真正的保證**。

不能寫在 Pydantic validator 裡（它是同步的、不該依賴外部資源，而且這個語意是 409 不是 422）。也不能只用「先查再寫」——兩個並行請求會同時通過檢查。先查只是為了給出更友善的訊息。 → [[02-pydantic-and-validation]]、[[06-error-handling]]
</details>

**29. 你要在 middleware 裡檢查 API key，失敗時回 401。怎麼寫？**

<details><summary>答案</summary>

`return JSONResponse(status_code=401, content={...})`，**不能 `raise HTTPException(401)`**——`ExceptionMiddleware` 在使用者 middleware 的內側，接不到，會變成 500。

但更好的做法是**改用 dependency**：它在內側，`raise` 正常運作，還能用 DI、能只掛在需要的 router 上。 → [[06-error-handling]]、[[08-middleware-and-cross-cutting]]
</details>

**30. `jwt.decode` 至少要傳哪些參數才算安全？**

<details><summary>答案</summary>

`algorithms=["HS256"]`（白名單，防 `alg:none` 與演算法混淆）、`audience`（防別的應用簽的合法 token 通過）、`issuer`、`leeway=30`（時鐘偏移，PyJWT 預設 0 太嚴格）。

之後還要查一次資料庫確認使用者存在且啟用，讓「停用帳號」立刻生效。 → [[07-auth-and-jwt]]
</details>

**31. 什麼是演算法混淆攻擊？**

<details><summary>答案</summary>

伺服器用 RS256（公鑰是公開的），攻擊者把 token header 改成 `HS256`，並用**那把公開的公鑰**當 HMAC 密鑰簽一個 token。如果驗證端沒鎖定演算法，它會拿同一把公鑰去驗 HMAC，然後通過。

防法就是 `algorithms=[...]` 明確指定白名單。PyJWT 強制要求這個參數就是為此。 → [[07-auth-and-jwt]]
</details>

**32. 「這張訂單是不是你的」這種授權檢查，能寫成 dependency 嗎？**

<details><summary>答案</summary>

能，而且**應該**——但關鍵是把租戶條件寫進**查詢本身**：

```python
stmt = select(Order).where(Order.id == order_id, Order.owner_id == user.id)
```

包成 `OwnedOrder = Annotated[Order, Depends(get_owned_order)]` 之後，「忘記檢查」在結構上變成不可能，因為沒有另一條路徑可以拿到 `Order`。這比靠人記得可靠得多。找不到時回 404 不是 403。 → [[07-auth-and-jwt]]
</details>

**33. 系統只有一個後端、前後端同源。JWT 還是 session？**

<details><summary>答案</summary>

**認真考慮 session + httpOnly cookie。** JWT 的優勢在跨服務、跨網域、無狀態擴展；沒有這些需求就是付了複雜度卻沒拿到好處——登出、撤銷、改權限全部要另外想辦法。

session 那邊這三件事全部立即生效。 → [[07-auth-and-jwt]]
</details>

**34. 前端說讀不到你回傳的 `X-Request-ID`，但 Network 分頁明明看得到。**

<details><summary>答案</summary>

跨來源的回應，JS 預設只讀得到六個基本 header。要在 `CORSMiddleware` 的 `expose_headers=["X-Request-ID"]` 列出來。

而且不會有任何錯誤訊息——`response.headers.get(...)` 就只是回 `null`。 → [[08-middleware-and-cross-cutting]]
</details>

**35. 怎麼讓每一行 log 自動帶上 request id，不用每次傳參數？**

<details><summary>答案</summary>

用 **`contextvars`**（不能用 thread-local，因為並發請求共用執行緒會互相污染）。middleware 進入時 `set`、離開時 `reset`，再加一個 `logging.Filter` 把它塞進每筆 record。

id 要**優先沿用上游的** `X-Request-ID` 或 `traceparent`，才能跨服務貫串。 → [[08-middleware-and-cross-cutting]]
</details>

**36. 這行有什麼問題：`DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")`**

<details><summary>答案</summary>

必填設定給了預設值。變數名打錯、忘了設、K8s 沒掛上——三種情況都會**靜默地用預設值繼續跑**，服務一切正常但資料寫進容器內的 SQLite，Pod 一換就消失。

改用 `BaseSettings` 且**不給預設值**，讓它在啟動時就失敗。 → [[09-configuration]]
</details>

**37. 為什麼「Pod 起不來」反而是好事？**

<details><summary>答案</summary>

CrashLoopBackOff 會讓新版 Pod 一直不 ready，**滾動更新自動停住、舊版 Pod 不被移除**，正式環境毫髮無傷。

相比之下，一個帶著錯誤設定安靜跑著的 Pod 會把錯誤資料寫進資料庫。啟動失敗是最安全的失敗方式。 → [[09-configuration]]
</details>

**38. 密鑰用 ConfigMap env 還是 Secret volume？**

<details><summary>答案</summary>

**volume + `secrets_dir`**。pydantic-settings 會把「檔名=欄位名、內容=值」直接讀進來，和 K8s Secret volume 掛出來的結構天然吻合。

而且 volume 掛載的密鑰不會出現在環境變數、`kubectl describe pod` 或子程序裡，洩漏面小很多。 → [[09-configuration]]
</details>

**39. 測試資料庫可以用 SQLite 嗎（正式是 Oracle）？**

<details><summary>答案</summary>

不行。SQLite 預設**不檢查外鍵**、**不強制 `VARCHAR` 長度**、型別是動態的；Oracle 三者都嚴格，還多一條「空字串等於 NULL」。用 SQLite 測出來的綠燈證明不了任何關於正式環境的事。

用 Testcontainers 起一個真的（`scope="session"` 共用），每支測試用交易回滾隔離。 → [[10-testing]]
</details>

**40. 什麼該 mock、什麼不該？**

<details><summary>答案</summary>

**該**：外部 HTTP（`respx`）、寄信、金流、時間、隨機數。
**不該**：自己的資料庫、service 層、ORM。

mock 掉 `Session` 的測試永遠會過，因為它不執行任何 SQL——欄位長度、外鍵、NULL 約束、N+1、交易問題全部測不到。 → [[10-testing]]
</details>

**41. K8s 上該用 `--workers 4` 還是 `replicas: 4`？**

<details><summary>答案</summary>

`replicas: 4`。四個理由：K8s 本來就是程序管理器（疊兩層讓排查變複雜）、HPA 的擴展顆粒度會變成四倍、一個 worker 洩漏會拖垮同 Pod 的其他三個、log 四份交錯難查。

不在 K8s 上（單一 VM、Compose）時 `--workers` 才合理。 → [[11-deployment]]
</details>

**42. CPU limit 和記憶體 limit 各該怎麼設？**

<details><summary>答案</summary>

**記憶體設 limit，CPU 只設 request。**

CPU 是可壓縮資源，超用只會變慢；設了 limit 反而在尖峰被 throttle，延遲出現階梯。而且 Python 的 event loop 是單執行緒，給再多核心也用不到——這和 .NET 不同，那邊 CPU limit 會影響 ThreadPool 大小計算。

記憶體不可壓縮，不設 limit 的話一個洩漏的 Pod 能拖垮整個節點。 → [[11-deployment]]
</details>

---

## L3 診斷（16 題）

**這一級的形式是：給你症狀，說出根因與修法。** 這是上線之後真正會遇到的形態。

**43. 某支報表 API 被呼叫時，連 `/health` 都超時。資料庫沒有壓力，CPU 15%。**

<details><summary>答案</summary>

**根因**：那支 endpoint 是 `async def` 但裡面有同步阻塞呼叫（同步 ORM 查詢、`requests`、`time.sleep`）。event loop 是單執行緒的，被卡住期間整個程序不處理任何請求。

**修法**：改成 `def`（讓 FastAPI 丟去 threadpool 隔離），或把阻塞呼叫換成非同步版本。

**辨識訊號**：**全部**端點一起停，包含純 async 的 `/health`——一個請求就足以造成，不需要高併發。 → [[04-async-and-concurrency]]
</details>

**44. 尖峰時出現 `QueuePool limit of size 5 overflow 10 reached, timed out`。資料庫本身沒壓力。**

<details><summary>答案</summary>

**根因**：連線池（預設 5+10=15）小於 threadpool 併發數（預設 40）。40 條執行緒同時醒著，只有 15 條拿得到連線，其餘堵著等 30 秒後丟例外。

**修法**：把兩個數字對齊。通常把 threadpool 縮到接近連線池比較好——執行緒不夠是排隊（可預期），連線不夠是等 30 秒後 500。順便把 `pool_timeout` 從預設 30 調到 10。 → [[05-database-sqlalchemy]]
</details>

**45. 前端傳了 `?tag=a&tag=b`，後端收到的是空清單，但沒有任何錯誤。**

<details><summary>答案</summary>

**根因**：簽章寫成 `tag: list[str] = []`，少了 `Query()`。`list[str]` 不是「單純型別」，被規則第 5/6 條判成 body，所以 query 傳什麼都收不到。

**修法**：`tag: Annotated[list[str], Query()] = []`。

**診斷法**：看 422 回應的 `loc[0]`——它會說 `"body"`，那就是 FastAPI 認為該從 body 拿。 → [[01-routing-and-path-operations]]
</details>

**46. `/users/me` 一直回「找不到使用者 me」。**

<details><summary>答案</summary>

**根因**：`/users/{user_id}` 宣告在前面先攔截了。FastAPI 的路由是一個 list，由上往下找第一個匹配，沒有優先序演算法。

**修法**：把具體路徑移到參數路徑前面。

**不要**靠 `user_id: int` 的轉換失敗來繞——那回的是 422（訊息很難懂），而且 id 型別一改成字串就破功。 → [[01-routing-and-path-operations]]
</details>

**47. 回應序列化時爆 `Parent instance <Order> is not bound to a Session`。**

<details><summary>答案</summary>

**根因**：`response_model` 上有 `items` 這種關聯欄位，但查詢時沒有 eager load，序列化時才要去 lazy load——這時 session 已經關了。

**修法**：查詢時 `options(selectinload(Order.items))`。

**紀律**：`response_model` 上有什麼關聯，查詢的 `options()` 就要有對應的 loader。這條可以寫進 code review 清單。 → [[05-database-sqlalchemy]]
</details>

**48. 前端「偶爾」收到 CORS 錯誤，但大部分請求正常，而且 CORS 設定看起來沒問題。**

<details><summary>答案</summary>

**根因**：那些請求其實是失敗的（401、500），而錯誤回應在 `CORSMiddleware` 的**外層**產生，所以沒帶 `Access-Control-Allow-Origin`。瀏覽器看到缺 header 就報成 CORS 錯誤，把真正的狀態碼掩蓋掉。

**修法**：把 `CORSMiddleware` 移到**最後一個** `add_middleware`（註冊順序是反的，最後加的在最外層）。 → [[08-middleware-and-cross-cutting]]
</details>

**49. 你在 middleware 裡 `raise HTTPException(401)`，前端收到的是 500。**

<details><summary>答案</summary>

**根因**：`ExceptionMiddleware`（查 handler 對照表的那層）在使用者 middleware 的**內側**，接不到外側丟出的例外，於是一路穿到 `ServerErrorMiddleware` 變成 500。

**修法**：`return JSONResponse(...)`，或改用 dependency（它在內側，`raise` 正常運作）。 → [[06-error-handling]]
</details>

**50. 背景任務裡爆 `This Connection is closed`，但 endpoint 本身完全正常。**

<details><summary>答案</summary>

**根因**：把 `yield` dependency 給的 session 傳進了 `BackgroundTasks`。0.106 版之後，`yield` 之後的收尾在**回應送出前**執行，所以背景任務啟動時 session 早就 close。

**修法**：背景任務自己開 session（`with SessionLocal() as db:`）。

**附帶**：`BackgroundTasks` 是程序內執行的，程序被砍任務就沒了——重要工作要進佇列。 → [[03-dependency-injection]]
</details>

**51. 服務跑了三天，客服說「有些訂單不見了」。查資料庫，那些訂單根本不存在。**

<details><summary>答案</summary>

**根因**：環境變數名打錯（或沒掛上），而程式用 `os.getenv("X", "預設值")` 靜默 fallback 到容器內的 SQLite。服務一切正常，Pod 一換資料就沒了。

**修法**：改用 `BaseSettings`，必填項**不給預設值**，讓程序在啟動時就崩潰。

**這一題是整套教材最貴的一個事故。** → [[09-configuration]]
</details>

**52. 每次部署後三十秒內固定出現一批 502，之後恢復正常。**

<details><summary>答案</summary>

**根因**：K8s 送 SIGTERM 和把 Pod 移出 Endpoints 是**並行**的，後者慢幾百毫秒到幾秒。應用已經開始關閉，流量還在往它身上送。

**修法**：加 `preStop: ["sh","-c","sleep 5"]`（在 SIGTERM **之前**執行，等傳播完成），並確認 `terminationGracePeriodSeconds` > preStop + graceful timeout。 → [[11-deployment]]
</details>

**53. 資料庫閃斷三十秒，結果所有 Pod 一起重啟，資料庫恢復後又被打爆。**

<details><summary>答案</summary>

**根因**：livenessProbe 打的端點會查資料庫。DB 掛掉 → 全部 Pod liveness 同時失敗 → 同時重啟 → 恢復時被一批同時啟動的 Pod 打爆 → 再次失敗。

**修法**：liveness **只檢查程序自己**，依賴檢查放 readiness（失敗只把 Pod 移出 Service，不重啟，恢復後自動回來）。

**這是用一次可自癒的小故障，換一場自我攻擊。** → [[11-deployment]]
</details>

**54. Pod 突然重啟，但 log 裡完全沒有例外或錯誤。**

<details><summary>答案</summary>

**根因**：多半是 `OOMKilled`——kernel 直接砍掉程序，Python 層**完全沒有機會記錄任何東西**。

**診斷**：`kubectl describe pod <name>` 看 `Last State: Terminated, Reason: OOMKilled`。

**修法**：調高 `limits.memory`（抓「尖峰後的高原」而非平均值），同時檢查是不是有 endpoint 一次載入太多資料——那種要改成串流或分批。 → [[11-deployment]]
</details>

**55. 部署時偶爾撞到資料庫連線數上限，平常都正常。**

<details><summary>答案</summary>

**根因**：滾動更新期間新舊 Pod 並存，連線數短暫翻倍；而且 lifespan 沒有 `engine.dispose()`，舊 Pod 的連線會停留在資料庫端直到逾時。

**修法**：lifespan 的關閉段加 `engine.dispose()`，並在算連線總數時把 `maxSurge` 納入考量。 → [[11-deployment]]
</details>

**56. 某支測試單獨跑會過，整批跑會失敗，而且失敗與否跟檔案順序有關。**

<details><summary>答案</summary>

**根因**：測試污染。兩個常見來源——`app.dependency_overrides` 沒清（它是掛在 app 物件上的**全域字典**，活到整個 session 結束），或資料庫沒隔離。

**修法**：加一個 `autouse=True` 的 fixture 自動 `clear()`；資料庫用交易回滾的 fixture。 → [[10-testing]]
</details>

**57. 改了 ConfigMap，`kubectl get configmap` 顯示新值，但服務行為沒變。**

<details><summary>答案</summary>

**根因**：用 env 注入的設定在**程序建立的那一刻就固定了**，K8s 沒辦法改變已存在程序的環境。

**修法**：`kubectl rollout restart deployment/xxx`。

這不是 bug——重啟反而讓「這個 Pod 現在用什麼設定」有確定答案。真的要熱重載得用 volume 掛載 + 自行重讀。 → [[09-configuration]]
</details>

**58. 上了 K8s 之後，Google OAuth 的 redirect_uri 變成 `http://` 而且是內部 IP。**

<details><summary>答案</summary>

**根因**：uvicorn 沒開 `--proxy-headers`，所以不信任 Ingress 送來的 `X-Forwarded-Proto` 和 `X-Forwarded-For`，`request.url` 拿到的是內部的原始值。

**修法**：`--proxy-headers --forwarded-allow-ips="*"`。後者只在確定外部流量無法直接到達這個 port 時才能填星號（K8s 裡通常成立），否則任何人都能偽造來源 IP。 → [[08-middleware-and-cross-cutting]]
</details>

---

## 一頁自評

答不出來的題號 → 該回去重讀的章：

| 題號 | 章節 |
| --- | --- |
| 1–3、43 | [[00-why-fastapi-and-setup]] |
| 4–6、45–46 | [[01-routing-and-path-operations]] |
| 7–11、28 | [[02-pydantic-and-validation]] |
| 12–14、50 | [[03-dependency-injection]] |
| 15–16、23、43 | [[04-async-and-concurrency]] |
| 17–18、24–26、44、47 | [[05-database-sqlalchemy]] |
| 19–20、27–29、49 | [[06-error-handling]] |
| 21、30–33 | [[07-auth-and-jwt]] |
| 22、34–35、48–49、58 | [[08-middleware-and-cross-cutting]] |
| 36–38、51、57 | [[09-configuration]] |
| 39–40、56 | [[10-testing]] |
| 41–42、52–55 | [[11-deployment]] |

### 過關標準

- **L1 答對 18/22 以下** → 還在照範例寫的階段，重讀對應章
- **L2 答對 14/20 以下** → 知道 what 不知道 why，重點讀每章的「常見誤解」
- **L3 答對 10/16 以下** → 上線之後會撐得很辛苦，把 [[12-cheatsheet]] 的十連發和紅色警戒清單背下來

L3 全對的話，你已經比大多數寫過 FastAPI 的人更知道它會在哪裡壞掉。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[12-cheatsheet]] — 附錄 A：速查與紅色警戒清單
- [[13-aspnet-mapping]] — 附錄 B：ASP.NET Core 對照
- [[22-self-assessment]] — .NET 那邊的對應附錄（65 題）
