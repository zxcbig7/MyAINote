# Wiki Index

> 本檔列出 `wiki/` 內所有頁面。回答問題時**先查此檔找線索**。
> 每次 ingest / synthesis 後即時更新。

## Tech / MOC（主題入口）

- [[devops-moc]] — Docker / K8s / Helm / Argo / Vault / CI-CD
- [[web-frontend-moc]] — React / TypeScript / CSS / UI/UX
- [[web-backend-moc]] — .NET Web API / C# / Auth
- [[database-moc]] — Oracle / SQL / PL-SQL
- [[languages-moc]] — C# / TypeScript / Python / VBA
- [[tools-system-moc]] — Git / Linux / Networking / 開發工具
- [[modeling-moc]] — 數學規劃建模方法論（García Sánchez + Williams）+ 29 個經典案例庫

## Tech / Entities

- [[argocd]] — GitOps 部署控制器，監控 git repo 並 sync 到 K8s 叢集
- [[raw/devops/Docker/Docker]] — 容器化平台，Image / Container / Repository 核心概念 + Compose
- [[kubernetes]] — 容器編排平台，Pod/Node/Cluster 四元件 + YAML 架構
- [[istio]] — Service mesh，Sidecar 注入、流量攔截、xDS、啟動 race condition 與偵錯
- [[minikube]] — 本機單節點 K8s 開發環境
- [[helm]] — K8s 應用部署打包工具，Chart / Release / values.yaml
- [[kubectl]] — K8s CLI 工具，get/apply/describe/logs/exec 常用指令速查
- [[raw/devops/Vault]] — HashiCorp Secret 管理，K8s 整合、Unseal 流程
- [[raw/Web Framework/TypeScript]] — 型別系統、Interface vs Type、泛型、Utility Types
- [[wiki/tech/entities/react]] — React Hooks 完整說明（useState/useEffect/useCallback/useRef/useContext）+ Zustand
- [[dotnet-web-api]] — 全書目錄《ASP.NET Core Web API：從入門到專家》：入門篇 17 章、深度篇 22 章＋2 附錄、專家篇 9 章，附速查與舊筆記修正表
- [[aspnetcore-webapi-complete]] — ASP.NET Core Minimal API 完整教學：路由、參數綁定、Middleware、DI、Health Check、快取等 18 章
- [[csharp]] — C# 語法重點、OOP、LINQ、async/await
- [[msbuild]] — MSBuild 與 .csproj：兩大積木（PropertyGroup/ItemGroup）、三動詞、CopyToOutputDirectory、Target、Directory.Build.props
- [[git]] — Git 四種物件、常用指令、日常開發 SOP、Branch 策略
- [[oracle]] — Oracle SQL 基本指令、CMD 操作、C# 連接方式
- [[linux]] — Linux 目錄結構、權限、常用指令、Ubuntu 設定
- [[claude-code-skills]] — Claude Code 自訂 slash command，Skills 定義方式、檔案格式與適用時機
- [[python]] — **給 C# 開發者的 Python**：五個會壞掉的直覺、四大容器對照、生成式 vs LINQ、EAFP、型別提示與工具鏈
- [[python-fast-api]] — FastAPI：ASGI、型別驅動驗證、`Depends`、Pydantic v2 + 教材總目錄

### FastAPI 教材（詳見 [[python-fast-api]]）

寫給「已經會 ASP.NET Core、第一次碰 Python 後端」的讀者，全 14 章 + 3 附錄 + 1 實戰，假設環境為 K8s + JWT + 前後端分離。**全數完成並通過驗收**。

- [[00-why-fastapi-and-setup]] — WSGI 為何撐不住、ASGI 的三個差異、型別提示如何在執行期生效（`__annotations__`）、`@app.get` 是當場執行不是中繼資料、venv/uvicorn/`/docs` 建置
- [[01-routing-and-path-operations]] — 參數來源六條推導規則、`str | None` 不等於選填、`list[str]` 少了 `Query()` 會變 body、路由是 list 由上往下匹配（`/users/me` 陷阱）、尾斜線 307 重導、`APIRouter` 分模組
- [[02-pydantic-and-validation]] — 解析而非檢查（`"35.5"` 會變 float）、422 的 `loc` 怎麼讀、`field_validator` 只能丟 `ValueError`、Create/Update/Out 三分（over-posting 與 `password_hash` 外洩）、`from_attributes`、v1→v2 對照表
- [[03-dependency-injection]] — 與 .NET DI 的三個根本差異、依賴快取即 Scoped、`yield` 收尾在回應送出**前**（背景任務拿到已關閉 session）、`lru_cache` 與 `lifespan` 兩種 Singleton、`dependency_overrides` 是測試接縫
- [[04-async-and-concurrency]] — event loop 單執行緒的完整後果、`async def` 包同步程式碼比 `def` 危險、threadpool 40 條上限與兩種卡法的診斷差異、GIL 讓 CPU 密集必須離開程序、`gather` vs `TaskGroup`、逾時是必要不是可選
- [[05-database-sqlalchemy]] — 連線池 15 對 threadpool 40 的算術矛盾、三條池子計算規則、同步 ORM 才是預設選擇、交易邊界三種寫法取捨、`expire_on_commit=False`、`DetachedInstanceError` 的根因與紀律、autogenerate 改名會刪資料、Oracle 四坑
- [[06-error-handling]] — 例外處理器三層位置（**middleware 裡 `raise` 會變 500**）、狀態碼決策表（401/403/404 的資安分界、500 vs 503）、RFC 9457 統一格式完整實作、領域例外與 HTTP 解耦、`IntegrityError` → 409 且先查擋不住競態、記錄層級對照表
- [[07-auth-and-jwt]] — **`OAuth2PasswordBearer` 不是認證**（只取字串，`Bearer abc` 照樣過）、FastAPI 沒有 authentication 系統、`algorithms` 白名單防演算法混淆、`aud` 少驗等於任何人能登入任何帳號、資源層級授權要寫進查詢、登出四方案與 refresh 輪替＋重用偵測、pwdlib/PyJWT 取代已停更的 passlib/jose
- [[08-middleware-and-cross-cutting]] — **註冊順序與執行順序相反**（與 .NET 相反，最後加的最外層）、假 CORS 錯誤的完整診斷表、middleware vs dependency 決策（看得到路由嗎）、`contextvars` 讓每行 log 自動帶 request_id、JSON log 要一起接管 uvicorn logger、`--proxy-headers` 與 redirect_uri 變 http
- [[09-configuration]] — **打錯字 + 預設值 = 靜默寫進容器內 SQLite**、必填不給預設讓 CrashLoop 擋住滾動更新、`model_validator` 把上線檢查清單變成程式碼、env vs volume（`secrets_dir` 直讀掛載）、list 要 JSON 不能逗號、密鑰外洩先輪替再清歷史、禁用 `if env == "production"` 分岔
- [[10-testing]] — **SQLite 測試綠燈證明不了任何事**（五項行為差異表）、`TestClient` 不啟動 server 所以整合測試該多寫、`raise_server_exceptions=False` 才測得到 500、覆寫 `get_current_user` 三行切身分、交易回滾 fixture、mock 邊界（別 mock Session）、時間要注入不要 patch、每支 endpoint 四種必測
- [[11-deployment]] — 部署掉 502 的真因（SIGTERM 與 Endpoints 更新**並行**，五行 preStop 解決）、K8s 上一容器一 worker 的四個理由、worker 數反推公式與「DB 連線才是天花板」、Python 不能用 Alpine、記憶體設 limit CPU 不設、liveness 碰 DB 會放大成自我攻擊、expand-contract、**收束用「本機好好的上叢集就掛」14 列對照表 + 上線前檢查清單**
- [[12-cheatsheet]] — 附錄 A：緊急排錯十連發、可直接貼的 `main.py`/`deps.py`/`conftest.py`/Dockerfile 骨架、參數規則與 v1→v2 對照、**數字速查表**（散落各章的預設值與硬性上限集中）、Oracle 錯誤碼對應 HTTP、20 條紅色警戒清單
- [[13-aspnet-mapping]] — 附錄 B：三個世界觀差異（型別何時生效／註冊 vs 宣告／誰吸收阻塞）、十二組逐項對照表、四段程式碼並排、**「看起來一樣其實不一樣」14 列**（照 .NET 直覺寫會出事的地方）、遷移順序與不該照搬的 .NET 慣例、雙方各自缺什麼
- [[14-self-assessment]] — 附錄 C：58 題三級自我檢測，答案用 `<details>` 摺疊強制先自己講；**L3 十六題全是「給症狀反推根因」**（連 `/health` 都超時、QueuePool timeout、部署掉 502、log 沒例外卻重啟…），附題號→章節對照與過關標準
- [[15-practice-deploy-to-k8s]] — **實戰（差異章）**：K8s 側概念一律指回 k8s-mastery，只講「應用換成 FastAPI 後哪十件事要改」——alpine 建置爆炸、venv 取代 publish 產物、缺 `PYTHONUNBUFFERED` 看不到死因、`secrets_dir` 直讀掛載、Alembic PreSync Job、**副本數與連線池五步實算**、CI 用 ruff+mypy 補編譯器的缺、slim 映像沒有 curl
- [[16-background-work]] — 補充篇：三副本讓對帳跑三次、四種做法邊界表、**`create_task` 的例外會靜默吞掉**、Redis 鎖的 TTL 與 Lua 比對釋放、arq vs Celery、**冪等鍵才是唯一防線**（佇列是 at-least-once）、outbox 保證 DB 與訊息原子、「排程沒跑」要靠時間戳告警
- [[17-resilience]] — 補充篇：**下游變慢比掛掉危險**（40 條 threadpool ÷ 2 秒 = 20 req/s）、httpx 四維度逾時會疊加、重試三紀律（冪等／暫時性／抖動）與重試預算、斷路器要包在重試外面、快取雪崩三解法、限流優先放 Ingress、**訊號量隔艙是最便宜的解**、量測優先於猜測

### ASP.NET Core Web API：從入門到專家（詳見 [[dotnet-web-api]]）

一本書三篇，假設部署環境為 K8s + Oracle + JWT/Google OAuth。入門篇以 .NET 10 用 TaskTracker 從零做到上線，程式碼與輸出全部實跑過（14 個階段建置成功、77 個測試通過）；深度篇以 .NET 8 為基準，回答「為什麼」；專家篇處理設計取捨、安全、效能與分散式。

#### 入門篇

- [[basics-01-http-and-web-api]] — 連結預覽和爬蟲會替你按 GET，所以 `GET /delete` 真的會刪資料；冪等性決定重試元件敢不敢重送；實測 `Content-Type`、無狀態、HTTP/1.1 到 3 的差別
- [[basics-02-rest-api-design]] — 整支 API 只用 POST 回 200，`res.ok` 永遠是 `true`、監控看不到錯誤率；用一串問題三題內選出狀態碼，並交出 TaskTracker 的 API 規格表
- [[basics-03-first-project]] — 清掉一行 `Program.cs` 換來空 body 的 404 且 console 沒有任何錯誤；兩階段（先註冊、後排 middleware）、.NET 10 範本不附 Swagger UI、`launchSettings` 部署後不生效
- [[basics-04-controllers-and-routing]] — 兩個 404 長得不一樣（路由沒命中與資源不存在）；改成 `GetByIdAsync` 會讓 `CreatedAtAction` 找不到 action；記憶體 `static List` 不是 thread-safe
- [[basics-05-model-binding-and-validation]] — 漏帶 `status` 的 `PUT` 會把已完成任務默默改回 `todo`；沒標 `[ApiController]` 就沒有自動 400；nullable 造成隱含必填，並實測 415
- [[basics-06-dto-design]] — 回傳 entity 與直接收 entity 各在不同時間點出事（洩漏欄位、over-posting）；Request 與 Response 要分開，手動 mapping 先於 AutoMapper，DTO 讓版本能演進
- [[basics-07-dependency-injection-and-services]] — 自己 `new` 的三個痛點；`TaskService` 先是 Singleton 因為它持有集合，換 DbContext 後必須改 Scoped；`ValidateOnBuild` 只在 Development 預設開，Production 會靜默出事
- [[basics-08-middleware-and-exception-handling]] — 順序就是行為：請求記錄放最外層才看得到 404 與 409；.NET 10 起被處理的例外預設不再留 log；Response 已開始後丟例外，狀態碼改不回來
- [[basics-09-configuration-and-environments]] — 伺服器回 200 而瀏覽器說被擋，是 CORS 在瀏覽器端判定；設定來源後者蓋前者；`ValidateOnStart` 讓壞設定起不來；CORS 白名單多打一個斜線就失效
- [[basics-10-efcore-and-oracle]] — 表名 `TASK_ITEMS` 來自 Oracle 的引號規則；空字串等於 NULL，空白標題變成難懂的 500；唯一性只有資料庫能保證，ORA-00001 轉成 409；更新路徑不能加 `AsNoTracking`
- [[basics-11-auth-concepts-and-pipeline]] — 沒帶任何身分的 `DELETE` 竟回 204；`[Authorize]` 是掛在 endpoint 上的 metadata 而非 Controller 裡的 if；省略 `UseAuthentication` 的症狀、401 與 403 的分界
- [[basics-12-jwt-login]] — 16 bytes 的金鑰啟動不出錯，到第一次簽 token 才丟誤導性的 IDX10720；Base64 不是加密；`MapInboundClaims` 讓 Role 檢查悄悄失效；Viewer、Editor、Admin 的後端落地
- [[basics-13-permissions-with-frontend]] — 藏起來的按鈕擋不住一行 `curl`，403 才是門鎖；permission claim 是簽發當下的快照；三種角色打整張權限矩陣的實測，以及 token 放 localStorage 還是 cookie
- [[basics-14-openapi-and-versioning]] — 實測 `MapOpenApi` 是 endpoint，放在 pipeline 哪裡都不影響；`ProducesResponseType` 不寫 200 的陷阱；悄悄改名就是破壞性變更；第二個版本出現時 DTO 要分版本
- [[basics-15-testing]] — 30 個單元測試全過，Editor 卻能刪除任務：屬性只有在 pipeline 裡才被讀；20 個矩陣案例中只有 1 個變紅；沒有 Docker 時整合測試整批跳過卻仍是綠燈
- [[basics-16-deployment-and-go-live]] — 純 http 端點只有 HTTP/1.1，強制 HTTP/2 會得到 `HTTP_1_1_REQUIRED`；live 與 ready 是兩個問題；資料庫暫時連不上改回 503；非 root 映像與上線清單
- [[basics-17-attribute-reference]] — 附錄：Attribute 本身什麼都不做，是路由、Binding、驗證、授權四種讀者在讀它；從加了 `[Authorize]` 卻放行的 action 出發，查表並對照常見誤解

#### 深度篇

- [[00-hosting-and-startup]] — Generic Host 四職責、`CreateBuilder` 載入什麼、`Build()` 凍結什麼、Kestrel 與反向代理分工、graceful shutdown 與 K8s 502 真相
- [[01-request-pipeline]] — `RequestDelegate` 型別簽章決定洋蔥、由後往前組裝、短路、三種寫法的 DI 陷阱、順序的完整推導、`OnStarting` 與 `HasStarted`
- [[02-dependency-injection]] — scope 是誰開的、captive dependency 四種症狀、`IDisposable` 由誰釋放、keyed services、Service Locator 反模式、lifetime 決策表
- [[03-routing-and-endpoints]] — Endpoint metadata 為何要兩階段、route template 語法、constraint 是消歧義不是驗證、優先序規則、Minimal API 與 Controller 底層差異、`CreatedAtAction` 的 Async 後綴坑
- [[04-model-binding-and-validation]] — 參數是 null 的六種成因、`[ApiController]` 推斷規則、record/init-only 與 nullable 造成的意外 400、DTO 是安全邊界（over-posting）、DataAnnotations vs FluentValidation
- [[05-filters-and-mvc-internals]] — MVC 執行 action 的 11 步、五種 Filter 位置與短路、ServiceFilter/TypeFilter 的 DI 差異、Exception Filter 的四項限制、內容協商、Minimal API endpoint filter
- [[06-async-and-threading]] — async 省的是執行緒不是時間、ThreadPool 飢餓的完整因果與診斷、`async void` 三宗罪、CancellationToken 傳遞、`ValueTask` 取捨、`IAsyncEnumerable` 串流
- [[07-efcore-internals]] — change tracker 快照比對（為何不用 `Update`）、identity map 三推論、`AsNoTracking` 判準、`SaveChanges` 五步驟、斷開情境與 `Update()` 造成的資料損毀、pooling 的前提
- [[08-efcore-query]] — `IQueryable` 延遲執行與具體化那條線、翻譯失敗的處理、N+1 四種解法與笛卡兒爆炸、深分頁改 keyset、Oracle `IN` 1000 上限、`ExecuteUpdate`、原生 SQL 的注入風險
- [[09-transactions-and-concurrency]] — 遺失更新為何加交易也擋不住、隔離級別（Oracle 只有兩級）、樂觀併發三種 token、悲觀鎖三紀律、冪等鍵、outbox 模式、長交易與連線池
- [[10-oracle-specifics]] — 識別碼引號與大小寫、30/128 字元上限、型別對應與值轉換器、空字串即 NULL、CLOB 效能、序列跳號、綁定變數與 shared pool、DDL 隱含提交、何時該換 Dapper
- [[11-authentication]] — 401/403 分界、scheme = 名字+handler+設定、四種動作（Challenge 為何回 302）、Claims 三層與 inbound 映射陷阱、Cookie vs Bearer 取捨、自訂 handler
- [[12-jwt-deep-dive]] — Base64 不是加密、HS256 vs RS256/JWKS、`alg:none` 與演算法混淆、`ClockSkew` 預設 5 分鐘、金鑰輪替、撤銷四方案、refresh token 輪替與重用偵測、前端存放位置
- [[13-oauth-oidc]] — OAuth 授權 vs OIDC 認證、授權碼流程六步、PKCE、三種 token 別搞混、前後端分離的驗證實作（`aud` 檢查是資安關鍵）、反向代理 scheme 與 `Correlation failed`
- [[14-authorization]] — Policy 是統一抽象、Requirement/Handler 的 OR/AND 語意、resource-based（attribute 表達不了的需求）、`FallbackPolicy` 讓漏寫不再是漏洞、權限模型設計、多租戶查詢篩選器
- [[15-error-handling]] — 三層分工、`ProblemDetails` 標準、`IExceptionHandler`（.NET 8）、400 vs 422 與 4xx vs 5xx、例外不該做控制流程、Result pattern、記錄層級對照表
- [[16-logging-and-observability]] — 結構化 logging（`$` 換逗號的價值）、scope 與 W3C TraceId、容器只寫 stdout、`IncludeScopes` 陷阱、metrics 高基數殺手、liveness 不可檢查資料庫
- [[17-configuration-and-secrets]] — provider 疊層與陣列覆蓋反直覺、三個 Options 介面差異、`ValidateOnStart` 讓壞設定進不了叢集、ConfigMap env vs volume 決定能否熱重載、Secret 分層與洩漏處置
- [[18-resilience-and-performance]] — 級聯故障（預設逾時 100 秒）、`HttpClient` 三陷阱、重試三紀律與斷路器、快取三層與 stampede、四種限流演算法、量測優先於猜測
- [[19-background-work]] — 多副本重複執行、`PeriodicTimer` vs `Task.Delay`、例外會停掉整個 Host、K8s CronJob/分散式鎖/Hangfire 選擇、`Channel<T>` 背壓、outbox 投遞
- [[20-testing]] — 測試金字塔在 API 的樣貌、mock 邊界（別 mock DbContext）、InMemory provider 為何不可靠、`WebApplicationFactory` + TestAuthHandler、Testcontainers、`TimeProvider`
- [[21-deployment]] — Dockerfile layer 快取與非 root、Server GC 與容器記憶體、CPU limit 影響 ThreadPool、migration 由 Job 執行、schema 向前相容、API 版本、上線前檢查清單
- [[22-self-assessment]] — 附錄 A：65 題三級難度自我檢測（含 L3 症狀反推根因）＋ 25 條紅色警戒清單
- [[23-cheatsheet]] — 附錄 B：緊急排錯十連發、`Program.cs` 骨架、middleware 順序、DI 決策表、EF Core/Oracle 速查、Dockerfile 與 Deployment 骨架

### React + TypeScript 教材（詳見 [[wiki/tech/entities/react/React|react]]）

把 `raw/Web Framework/React/` 的 17 份筆記重寫成一本書，以 React 19.3、TS 7、Vite 8 為基準，用 Task Tracker 專案貫穿，範例都實際編譯測試過。**撰寫中**，完整目錄與進度見 hub 頁。

- [[react-06-components-and-jsx]] — JSX 是函式呼叫不是模板：`class`、`if`、大小寫規則都能從編譯結果推出來、React element 只是便條、`&&` 為什麼會畫出一個 0、與 Razor 的方向差異、Task Tracker 第一個靜態畫面
- [[react-07-props]] — 單向資料流與 props 唯讀的理由、children 與 slot、Layout Component、用 ComponentProps 與 extends 接 HTML 屬性、事件型別、`React.FC` 為何退場
- [[react-08-state]] — setter 之後為什麼讀到舊值：state 是這次 render 的 `const` 快照（`await` 也救不了）、updater 與 queue 手算、batching 的真正邊界、stale closure 造成的資料蓋回、`Object.is` 是不可變更新的根本理由、受控 input 的迴圈、哪些東西不該是 state
- [[react-09-rendering]] — render、commit、paint 分別做什麼、子 component 為何連帶 render、state 綁在樹的位置上、`key` 的真正角色與 index 當 key 的 bug、StrictMode 雙重 render 的目的、component 為什麼必須是 pure
- [[react-10-tic-tac-toe]] — state 放最近共同父層，勝負與輪次一律推導；存 winner 晚一步、留 isXNext 回放錯方、原地改盤面毀掉歷史、key={currentMove} 掉焦點
- [[react-11-effects]] — Effect 是同步不是生命週期、四條判斷規則、依賴陣列與 exhaustive-deps、cleanup、競態與 AbortController、你可能不需要 Effect 的情境、`useEffectEvent`、`useLayoutEffect`、StrictMode 下的雙跑
- [[react-12-refs]] — ref 是不觸發 render 的記憶、render 中讀寫 ref 為何違規、DOM ref、React 19 的 ref prop 取代 forwardRef、useImperativeHandle 只開放必要操作、ref callback 與 cleanup
- [[react-13-reducer-and-context]] — reducer 把更新規則收在一處、action 描述事件、discriminated union 型別；Context 解 prop drilling、null 預設加拋錯的 hook、重 render 成本與拆分、Context 不是狀態管理
- [[react-14-memoization]] — 參考相等是一切的根源、三者分工、useCallback 只在接收方會比較時才有用、React Compiler 改變了什麼、何時不要加 memo
- [[react-15-custom-hooks]] — 邏輯重用不是 state 共享、何時值得抽 hook、tuple 與 object 回傳的取捨、useDebounce、用 useSyncExternalStore 寫對 useIsMobile、useId、useDebugValue、use API 預告
- [[react-19-routing]] — SPA fallback 讓所有路徑回 200，少 /api 守門則打錯 API 拿到 HTML；同路由換參數 state 殘留要 key；篩選進 URL，setSearchParams 物件覆蓋、連呼叫不累積；Data lazy 留舊頁。
- [[react-20-api-layer]] — fetch 只對網路失敗 reject，請求有六種結局；axios 泛型不驗證，Zod 才是查核；ProblemDetails 轉 ApiError；VITE_ 全公開且字串 false 為真；CORS 是瀏覽器規則，能同源就同源。

## Tech / Concepts

- [[cicd-pipeline]] — GitLab/Azure DevOps + Harbor + Helm + ArgoCD 完整 CI/CD 流程
- [[csharp-syntactic-sugar]] — C# 語法糖：定義與判斷標準、lowering 流程、expression-bodied member（不是 lambda、`=>` vs `=` 陷阱）、null/宣告/流程/字串/呼叫類糖的展開對照、重度糖（閉包/yield/async/record）、非糖功能與舊 runtime 可用性、SharpLab/ILSpy 觀察法、九個常見陷阱
- [[domain-networking]] — DNS 概念、Record 類型、Cloudflare、TLS Binding
- [[dom]] — DOM 是什麼：HTML vs DOM、節點種類與繼承鏈、渲染流程（CSSOM/Layout/Paint）、原生操作 API 與 EventListener、Layout Thrashing、事件傳遞（三階段、target/currentTarget、stopPropagation 陷阱、委派、不冒泡事件）、React Virtual DOM 與 useRef、七個常見錯誤排查
- [[runtime-data-directory-flow]] — 原始碼樹 vs 輸出目錄兩份資料的雙向流：程式回寫產物、PreserveNewest 造成的永久分岔、產物指紋辨識與回收 SOP
- [[unit-testing-sop]] — 新手向 xUnit 單元測試 SOP：建專案四步、寫測試五步、12 種情境對照表（Fact/Theory/不變式/不爆炸/例外/集合/樹/golden/假物件/async/private）、斷言速查、六個常踩的坑

### K8s Mastery 教材（詳見 [[k8s-mastery]]）

涵蓋 Docker → K8s → Helm/ArgoCD → Prometheus/ELK 完整交付鏈的**入門篇 6 章 + 實戰篇 6 章 + 正文 16 章 + 59 附錄**，約 540,000 字、97 張圖。**全數完成並通過驗收**。

- [[k8s-mastery]] — 總目錄、進度表與七天學習路徑
- [[intro-0-start-here]] — **入門篇總覽**：零基礎的六章台階，正文之前先讀這個
- [[intro-1-server-and-process]] — 入門 1：程式 vs 程序、伺服器是角色不是硬體、port 是房號、部署其實是四件事
- [[intro-2-linux-and-terminal]] — 入門 2：終端機求生，PowerShell↔Linux 指令對照、管線與重導向、權限 rwx、環境變數、vi 逃生門
- [[intro-3-network-basics]] — 入門 3：一次請求的完整旅程（DNS→TCP→TLS→HTTP）、私有 IP、狀態碼分類、反向代理，附 K8s 概念對照表
- [[intro-4-yaml-syntax]] — 入門 4：YAML 三種結構、縮排三規則、五種要加引號的情況（含 Norway problem）、多行字串、錯誤訊息解讀
- [[intro-5-first-container-and-pod]] — 入門 5：手把手 docker run → Dockerfile → minikube → Pod → Deployment 自我修復 →Service，含 docker/kubectl 指令對照
- [[intro-6-error-messages]] — 入門 6：40+ 條錯誤訊息白話翻譯（Docker/連線/YAML/Pod/網路五組）+ 排錯決策樹 + 求助時該附什麼
- [[practice-1-containerize-your-app]] — **實戰 1**：把自己的 ASP.NET Core + React 容器化，應用要先改的四件事、多階段建置與層快取順序、非 root、`.dockerignore`、前端環境變數兩難
- [[practice-2-deploy-real-app]] — 實戰 2：一組真實服務的七個物件完整 manifest，三種 probe 分工、preStop 與優雅關閉、由內而外的驗證順序、Kustomize 多環境
- [[practice-3-gitops-pipeline]] — 實戰 3：app repo/manifest repo 分離、tag 觸發 CI、ArgoCD selfHeal 與 prune、Sync×Health 四種組合判讀、HPA 與 GitOps 打架的解法
- [[practice-4-write-yaml-from-scratch]] — **實戰 4**：不靠複製貼上寫 YAML —— `kubectl create --dry-run` 產骨架、從需求推導欄位的五問法、兩個完整推導示範、反向讀 YAML 練習、四步驗證鏈（kubeconform/kube-linter）
- [[practice-5-database-and-state]] — 實戰 5：資料庫該不該進叢集的決策表、ExternalName 三種接法、**連線數是 Pod 數 × 連線池的乘法**、migration 抽成 Job、expand-contract 零停機改 schema、K8s 沒有 depends_on 的正解、StatefulSet 與 fsGroup/PGDATA 細節
- [[practice-6-observability]] — 實戰 6：metrics/logs/traces 分工、OpenTelemetry 接上 ServiceMonitor 與抓不到的三個原因、四個黃金訊號 PromQL（含最易漏的 **CPU throttle**）、高基數殺手、結構化日誌 + trace ID、六條實用告警 PrometheusRule、**沒測過的監控等於沒有監控**
- [[00-docker-foundations]] — 容器三大 Linux 基石（namespace/cgroup/OverlayFS）、image layer、Dockerfile 逐指令、多階段建置、dockershim 真相
- [[01-why-kubernetes]] — 部署的痛從哪來、K8s 解決什麼問題與它的取捨
- [[02-cluster-internals]] — Control Plane/Node 元件、`kubectl apply` 完整旅程、Reconciliation Loop 與 pull-based 心智模型
- [[03-api-and-yaml]] — GVK/GVR、apiVersion 棄用規則、labels vs annotations、selector、server-side apply 與 field manager
- [[04-workloads]] — Pod 剖析與多容器模式、三種 Probe 誤設災難、優雅關閉與 preStop、Deployment 滾動更新推演、StatefulSet 三保證、Job/CronJob
- [[05-networking]] — 網路四鐵律、Service 選擇鏈與 kube-proxy、DNS 與 ndots 陷阱、Ingress/TLS、NetworkPolicy、完整封包路徑
- [[06-config-and-storage]] — ConfigMap env vs volume 更新差異、Secret 非加密真相、PV/PVC/StorageClass 三層、Vault + ESO
- [[07-scheduling-and-resources]] — Scheduler 決策、requests/limits 真義、CPU throttle vs Memory OOMKill、QoS 與驅逐、Taint/Affinity、三種 Autoscaler
- [[08-security-and-rbac]] — Authentication/Authorization/Admission 三道關卡、RBAC 四物件配對與純白名單本質、ServiceAccount token 演進、Pod Security Admission、Vault 信任鏈、ArgoCD AppProject 權限邊界
- [[09-extending-kubernetes]] — Admission webhook（為什麼 YAML 被改了）、CRD/Operator、Finalizer（namespace 卡 Terminating）、OwnerReference 與 GC
- [[10-helm]] — Chart 結構、`include` vs `template`、`nindent`、values 覆蓋優先序、Hooks、除錯三件套
- [[11-argocd]] — GitOps pull 模型、Application 解剖、Sync 與 Health 獨立性、Sync Waves、OutOfSync 診斷、ApplicationSet、AppProject 邊界
- [[12-cluster-operations]] — etcd 備份還原、憑證輪替、版本升級順序、Node 維護與 Velero
- [[13-troubleshooting]] — 分層定位方法論、Pod 狀態機、網路排查流程、19 個真實踩坑案例庫
- [[14-prometheus-grafana]] — pull 模型、四種 metric type、PromQL 深入（rate/irate/histogram_quantile）、Alertmanager、USE/RED、Grafana
- [[15-elk-elastic]] — 容器日誌收集路徑、倒排索引、shard/mapping、`text` vs `keyword`、KQL 與 Query DSL、Logstash/Filebeat、ILM、ELK vs Loki
- [[16-self-assessment]] — 附錄 A：144 題自我檢測題庫，三級難度＋18 條紅色警戒清單
- [[17-cheatsheet]] — 附錄 B：速查表，緊急排錯十連發、17 種 YAML 骨架、kubectl/Helm/ArgoCD/PromQL/KQL 速查
- [[18-yaml-fields-pod]] — 附錄 C-1：metadata / PodSpec / Container 逐欄位百科，含預設值、版本門檻與 `kubectl explain` 自查法（v1.33）
- [[19-yaml-fields-workloads]] — 附錄 C-2：Deployment/STS/DS/Job/CronJob 全欄位 + HPA `behavior`、PDB、PriorityClass、Quota/LimitRange
- [[20-yaml-fields-network-storage]] — 附錄 C-3：Service/EndpointSlice/Ingress/NetworkPolicy 全欄位 + PV/PVC/StorageClass、ConfigMap/Secret
- [[21-yaml-fields-cluster-security]] — 附錄 C-4：Namespace/PSA labels、ServiceAccount、RBAC 四物件、Node/Taint、CRD、Admission Webhook + 上線前檢查清單
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：生態系 CRD 全欄位，ArgoCD Application/AppProject/ApplicationSet、Helm Chart.yaml、ServiceMonitor/PrometheusRule、cert-manager、External Secrets、VPA、Gateway API、kustomization.yaml
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：冷門內建資源（CSI 家族、Event/Lease、CSR、APF、DRA）+ 元件設定檔（kubelet/kube-proxy/scheduler/kubeadm/加密/稽核/kubeconfig）
- [[24-yaml-fields-istio]] — 附錄 C-7：Istio 全欄位，Gateway/VirtualService/DestinationRule/ServiceEntry/Sidecar + mTLS、JWT 驗證與 AuthorizationPolicy 三條判定規則
- [[25-yaml-fields-pipeline]] — 附錄 C-8：交付鏈上的非 K8s YAML，GitHub Actions workflow 全欄位（含 tag 觸發部署範例）、cloudflared config、Docker Compose 與 K8s 欄位對照
- [[26-lab-drills]] — 附錄 D：20 個破壞—診斷—修復實驗，在 minikube 上親手製造 OOMKill/throttle/probe 誤殺/DNS 斷線/PSA 擋 Pod 等故障並自己查出根因
- [[27-upgrades-and-deprecations]] — 附錄 E：version skew 規則、1.22→1.33 已移除 API 完整對照表、四種棄用掃描手段（`apiserver_requested_deprecated_apis`/pluto/kubent/convert）、升級前後檢查清單
- [[28-ingress-nginx-annotations]] — 附錄 F：ingress-nginx annotation 百科分十組（重寫/逾時/大小/TLS/認證/限流/黏著/canary/CORS/其他）+ 全域 ConfigMap + 外部 OAuth 認證範例
- [[29-status-and-conditions]] — 附錄 G：Pod 三層狀態、所有 waiting/terminated reason、exit code 對照、Node/Deployment/Job/PVC/HPA/CRD/Namespace conditions、ArgoCD 雙維度，症狀→欄位一頁式
- [[30-production-readiness]] — 附錄 H：新叢集上線清單、服務 runbook 模板、容量規劃三數字、每日/週/月/年維運節奏、12 條必備告警、事故分級與第一小時流程
- [[31-glossary]] — 附錄 I：約 140 條 K8s 術語百科（A–Z），每條兩三句定義加章節連結，全書導航層
- [[32-istio-ingress-gateway]] — 附錄 J：Istio Ingress Gateway（IGW），與 ingress-nginx 的七項對照與選型、Gateway/VirtualService 三條綁定規則、15xxx port 對照、**503 的四種 Envoy 旗標（NR/UH/UF/NC）判讀**、憑證三坑
- [[33-cost-optimization]] — 附錄 K：排程飽和度 vs 真實飽和度、**記憶體用 P99／CPU 用 P90 的理由**、找出過度配置的 PromQL、VPA 當免費建議引擎、CPU limit 該不該設的判準表、節點碎片化與規格取捨、autoscaler 縮不掉節點的四個原因、七條孤兒資源盤點指令、成本歸屬標籤
- [[34-multicluster-and-dr]] — 附錄 L：RTO/RPO 決定架構、要保護的四層（**第 4 層叢集外依賴最常被遺忘**）、etcd 快照必須連 `/etc/kubernetes/pki` 一起備、Velero pre hook 與資料庫一致性、**三種還原演練腳本（誤刪 namespace／PV 損毀／整座重建）含驗收標準與計時**、四種多叢集拓撲選型、10 個誤區
- [[35-cloud-networking]] — 附錄 M：VPC 五件套與 **IGW/NAT 的差別**（public subnet 是路由的推論結果不是開關）、SG vs NACL、**Pod IP 兩種模型與 EKS 的 IP 額度耗盡**（節點資源夠卻排不進去）、LoadBalancer `<pending>` 三查、NLB+ingress-nginx 收斂、IRSA 信任鏈、EBS 綁 AZ 與 WaitForFirstConsumer、跨 AZ/NAT 處理費等雲端成本陷阱
- [[36-ebpf-and-cilium]] — 附錄 N：kube-proxy 的結構性極限（規則數與 Service 數成正比）、eBPF 與 verifier 白話原理、Cilium 的 **identity-based 安全模型**（政策規則數與 Pod 數脫鉤）、L7 與 `toFQDNs` 政策、Hubble 回答「為什麼被丟掉」、Egress Gateway 固定出口 IP、**該不該換的誠實判準表**與遷移八步
- [[37-platform-engineering]] — 附錄 O：從「我管叢集」到「我提供平台」——責任邊界表、**golden path 是最好走的路不是唯一的路**、內部 chart 承載安全基線、namespace 自助化完整 YAML（quota+LimitRange 必須成對、給 `edit` 不給 `admin`）、隔離七維度與何時該拆叢集、政策 audit→warn→enforce、三次法則、DORA 與採用率、10 種失敗模式（含**抽象漏水**）
- [[38-security-incident-response]] — 附錄 P：供應鏈（distroless、digest 釘選、掃描三位置與豁免到期日、SBOM 回答「我們有沒有用到」、cosign 簽章）、機密外洩**先輪替再清理**與各類憑證輪替表、**叢集被入侵的隔離→蒐證→評估→清理**（不要 delete 可疑 Pod；改標籤讓 controller 補新的）、容器逃逸六條路徑與盤點指令、audit log 五種調查查詢
- [[39-performance-troubleshooting]] — 附錄 Q：「服務變慢了」專章——延遲六段分解與各段量測、**先問四個問題**（全部/部分、持續/尖峰、何時開始、P50/P99）、逐層排查 L0–L5、**CPU 用量低仍被大量 throttle 的 CFS 週期原理**、尾端延遲六因（含重試放大）、三個完整推演、10 個誤區
- [[40-operators-and-stateful]] — 附錄 R：**該不該寫 Operator 的決策階梯**與成熟度五級（L1/L2 用 Helm 就夠，價值從 L3 開始）、選用既有 Operator 的逃生門檢查、reconcile 六原則（冪等、level-triggered、status/spec 分離、重試節奏、finalizer 釋放路徑、ownerReference 優先）、StatefulSet 運維手冊（partition 金絲雀、`--cascade=orphan` 改不可變欄位、擴儲存要逐個 PVC）
- [[41-advanced-scheduling]] — 附錄 S：線上 vs 批次的排程差異、**PriorityClass 七層分配建議**與優先級通膨的兩種防護、**PDB 對搶佔只是偏好不是硬保證**、gang scheduling 死鎖與 Kueue 用 `suspend` 的解法、GPU 三條硬規則與 time-slicing/MIG、spot 跑批次的五個配套（`podFailurePolicy` 排除搶佔失敗）、**`matchLabelKeys: [pod-template-hash]` 為何在滾動更新時必要**、`FailedScheduling` 訊息七種關鍵字對照
- [[42-helm-chart-design]] — 附錄 T：**chart 是 API、values.yaml 是介面**——最小可用五行、命名對齊社群、**逃生門（extraEnv/extraObjects）決定採用率**、`values.schema.json`、`labels` 與 `selectorLabels` 必須分開、checksum annotation、**`lookup` 在 ArgoCD 下靜默回空造成每次產生新密碼**、library chart vs subchart 三陷阱、破壞性變更三步（並存→公告→`fail`）、Helm×ArgoCD 四個坑、CI 測試五道
- [[43-migration-to-k8s]] — 附錄 U：既有系統遷移專案——**先問該不該搬**（六類該留在原地的系統，「不搬」是合法結論）、容器化難度七維度評分找試點、**隱性依賴要用觀察而非詢問**、三波節奏（試點要選最容易的不是最重要的）、應用要改的五件事、雙跑期與影子流量副作用、回滾點設計、Windows 應用三條路、10 種失敗模式
- [[44-knowledge-transfer]] — 附錄 V：**「只有我會」是負債不是資產**——bus factor 三題自測、四種角色的知識分層（開發者不必懂 etcd）、**用本教材設計的四條培訓路徑含時數與驗收**、文件四分法（教學/指南/參考/說明，本教材即實踐）、不該寫進文件的四類、五種讓知識流動的機制（輪值 shadow 期、配對排錯、事故當教材）、**用可執行的東西取代文件**、你自己該改的四件事
- [[45-microservices-and-communication]] — 附錄 W：**該不該拆**（六個營運面的好理由 vs 四個壞理由、模組化≠分散式）、**資料所有權才是真正的邊界**（共用資料庫＝分散式單體）、Strangler 漸進拆、四種通訊模式對照與同步呼叫的可用性相乘、分散式五堂必修課（逾時/重試三條件/斷路器/冪等鍵/追蹤）、**mesh 解決不了的五件事**與「加 mesh 不會讓爛的拆分變好」、何時該合併服務
- [[46-advanced-self-assessment]] — 附錄 X：**75 題進階自我檢測**，涵蓋附錄 A 沒考到的實戰篇與附錄 E–W；43 題標為紅色警戒（答錯會在正式環境造成實際損害），收尾附 30 條紅色警戒濃縮清單
- [[47-api-versioning]] — 附錄 Y：**什麼算破壞性變更**（含最陰險的「改語意」——schema diff 與契約測試都抓不到）、向後相容 vs **向前相容**與 Tolerant Reader、版本化三策略與「多數變更根本不需要新版本」、K8s 上多版本並存三做法與共用 DB 的 expand-contract、**棄用四步（監控要先於公告）**與各對象的時程、OpenAPI diff 擋 PR、10 個誤區
- [[48-testing-in-k8s]] — 附錄 Z：**先分清楚測試在驗證什麼**（應用邏輯／部署設定／叢集行為，前兩類不需要叢集）、Testcontainers 取代共用測試庫、CI 五道靜態驗證（**要驗渲染後的結果**）、kind 跑的四種叢集行為測試（**`auth can-i` 當斷言**、NetworkPolicy 實打驗證）、ApplicationSet pullRequest 預覽環境與成本控制、**能消除的環境差異必須消除**與「測不到的六件事」、部署後 smoke test 與金絲雀、混沌五階段
- [[49-messaging-and-events]] — 附錄 AA：**要不要用訊息系統**（為了重試而引入是錯的）、Kafka vs RabbitMQ 的根本差異（能不能重播）、**consumer 不是 HTTP 服務**所以 CPU 指標的 HPA 沒用 → KEDA 依佇列深度擴縮、**Kafka partition 數是並行硬上限**、優雅關閉與「處理到一半被砍」、at-least-once 逼出冪等、順序保證只在 partition 內、DLQ 不是垃圾桶是待辦清單、**告警要對 lag 持續成長而非絕對值**
- [[50-caching]] — 附錄 AB：**先量測再加快取**與命中率估算、**多副本下本機快取的四個陷阱**（重新整理看到不同結果、清除只清到一個副本、擴容時新副本是冷的）、Redis 該不該進叢集（純快取可重建所以可以）、**`maxmemory` 沒設會 OOMKilled 讓快取瞬間全空**、寫入後要刪除不要更新、**TTL 加抖動**與單飛解雪崩、「加了快取反而更慢」五成因、Redis 掛掉要降級不是一起掛
- [[51-background-jobs]] — 附錄 AC：四種形式的決策樹（**CronJob 是預設**）、**應用內 Timer 在三副本下每小時跑三次**與三種解法（抽 CronJob／leader election／分散式鎖，「只跑一副本」不是解法）、CronJob 四陷阱（時區、**錯過 100 次會永久停止排程**、`Forbid` 卡住會靜默跳過、Job 也會被驅逐）、分批 + checkpoint 的長任務設計、**「沒跑」是安靜的**要用 dead man's switch + Pushgateway 偵測、10 個批次反模式
- [[52-file-and-object-storage]] — 附錄 AD：**使用者檔案不該放 PVC 的五個理由**與 PVC 仍然適用的場景、物件儲存三個心智模型調整（扁平 key、不能 append、multipart）、**預簽名 URL 讓檔案不經過應用**（記憶體/worker/Ingress 限制/雙倍流量四個代價一次解決）與直傳的五條安全設計、CORS 是直傳第一個障礙、檔案處理要非同步且 worker 獨立、**孤兒檔案對帳**與版本控制的成本
- [[53-configuration-management]] — 附錄 AE：**設定變更的事故比程式碼變更多**（沒型別、沒測試、生效快）——依變更頻率×敏感度分四類、**不要用 git 分支管環境**且要能 diff 兩環境、四道防護（**`ValidateOnStart` 讓壞設定變成部署失敗而非執行期故障**）、熱重載三種行為與「預設該用滾動更新」的理由、feature flag 與 ConfigMap 的分工及 flag 債務、**必填設定不給預設值**（打錯字靜默用預設是最陰險的事故）
- [[54-developer-experience]] — 附錄 AF：**inner loop 一天五十次×三分鐘=兩個半小時**且會讓人寫出更大的改動、四種策略對照（完全本機／本機 K8s+Skaffold sync／遠端同步／**流量攔截 = 本機速度+叢集真實度**）、**高估真實度需求是最常見的錯誤**與真實度可分階段、避免本機與叢集設定漂移三原則（**不要在程式碼裡加 `if (isLocal)`**）、共用開發叢集的 per-developer namespace 與流量攔截的搶流量風險、開發叢集成本、`kubectl debug` 是 distroless 的唯一排查手段
- [[55-logging-strategy]] — 附錄 AG：**日誌三種用途要分開**（除錯／趨勢／稽核，保留期差十倍）、**不要用日誌做監控**（數量趨勢是 metric 的工作）、該記與不該記（決策點最有價值、完整 body 風險最高）、`Error` 的定義是「需要人採取行動」、**成本算術**（43GB/天 × 30 天 × 索引副本 ≈ 4TB／單一服務）與四個減量手段、ILM 分層是投報率最高的單一動作、Loki 只索引 label 的取捨、DaemonSet vs sidecar、**kubelet 日誌輪替沒設會撐爆節點磁碟**
- [[56-frontend-deployment]] — 附錄 AH：前端與後端的**三個根本差異**（產物是靜態檔、執行在瀏覽器、**版本切換不是原子的**）、四種部署形態與「純 SPA 其實不需要 K8s」、**「舊 JS 檔案 404」的完整推演與四個解法**（滾動更新反而讓它更嚴重）、快取策略（`index.html` 必須 no-cache、帶 hash 的資源永久快取）、環境變數三解法與「前端設定全部公開不能放機密」、SSR 是 Node 服務（`--max-old-space-size` 要小於 limit）、RUM
- [[57-database-connections]] — 附錄 AI：**`Min Pool Size` 也要 × Pod 數**、連線池中介三種 pooling 模式與transaction pooling 會壞掉的東西、**sidecar 形態的中介收斂效果差**、讀寫分離「預設讀主庫」的保守起點、**K8s 上連線更容易「看起來還在但已死」**（NAT/防火牆單方面丟棄）與三道防護、**故障轉移時 liveness 查 DB 會讓所有 Pod 同時重啟**、重連要有抖動（沒抖動只是把衝擊延後）、「等待連線的時間」是分辨應用慢 vs DB 慢的關鍵指標
- [[58-api-gateway-and-edge]] — 附錄 AJ：**邊界層該做什麼的判準**（這件事對所有服務都一樣嗎／這規則改了要重新部署邊界嗎）、**認證在邊界、授權在應用**且應用仍要驗（不假設請求一定經過邊界）、**`RequestAuthentication` 不擋沒帶 token 的請求**、限流兩層與「ingress 限流是每副本各自計數」、429 要帶 `Retry-After`、API key 輪替要新舊並存、對外對內用不同 Ingress、WAF 先偵測模式再阻擋、**邊界層是單點**要專屬資源與更高優先級
- [[59-adoption-roadmap]] — **附錄 AK：導入路線圖**——把全書 72 份重排成時間軸：Phase 0 決策（先定工作負載再建叢集）／1 個月能跑起來（**附錄 D 實驗是最高投報率的一天**）／1 季能安全重複（部署全走 git + 還原演練）／半年能交給別人（**另一團隊自己上線是唯一驗收標準**）／1 年能承擔變化（升級、DR、成本、**你休過假沒被找**）；每階段都列「明確不要做的」、安全/成本/知識三條橫向線、**六個常見順序錯誤**（太早上 mesh、監控留最後、太早平台化）、各階段「還沒準備好」的訊號
- [[60-advanced-cheatsheet]] — 附錄 AL：**進階速查表**——附錄 B 寫於 16 章時代，這份補上後來引入的 16 種工具（trivy/cosign/istioctl/hubble/cilium/velero/kubeconform/kube-linter/conftest/pluto/kubent/etcdutl/KEDA/Kueue/kind/skaffold），按**「你想做什麼」**組織，收尾附一頁式對照表
- [[61-compliance-and-audit]] — 附錄 AM：**合規與稽核**——安全問「有沒有做」，合規問**「能不能證明做了」**；控制項對應表、GitOps 天然滿足職務分離、audit log 的五種稽核查詢、個資盤點最常漏掉**日誌與備份**、**把蒐證自動化**讓稽核季不用停下工作，附十個常見提問與該拿出什麼
- [[62-stateful-workloads-decision]] — 附錄 AN：**有狀態服務要不要進叢集**——你當上管理員一定會被問到的問題；StatefulSet **沒有**給的五件事（備份／選主／一致性／資料遷移／重分布）、operator 補的是哪一段、**「資料掉了能不能重建」是最好用的單一判準**、缺一就出事的八項底線、六種災難模式，以及「應用進叢集、資料庫留外面」為何是務實終點
- [[63-ci-in-cluster]] — 附錄 AO：**在叢集裡跑 CI 與建置**——「runner 可以搬進來嗎」的完整答案；掛 Docker socket **等於交出整台節點且 RBAC 擋不住**、三層建置快取與「清空重跑結果要不變」的判準、runner 用完即丟、**CI 只推映像不碰叢集**、專用節點池與低優先級，以及為何混合方案最務實
- [[64-slo-and-alerting]] — 附錄 AP：**SLO、錯誤預算與告警設計**——實戰 6 只說「從 SLO 導出告警」，這份補上怎麼做；`CPU > 80%` 為何同時造成誤報與漏報、**99.9% ＝ 每月 43 分鐘**（99.99% 已是人為介入來不及的架構要求）、延遲 SLI 要寫成比例而非 P95、**多視窗燃燒率四組門檻**與可直接抄的 PromQL、快燒叫人慢燒開工單、每季刪告警
- [[65-inheriting-a-cluster]] — 附錄 AQ：**接手一座既有叢集**——附錄 AK 是從零導入，這份是「叢集在跑、建它的人要走、下週起是你的」；心法是**「最大的風險不是你不會的，是你不知道它存在的」**；第一週只看不動的盤點指令（含最易埋伏的失效 webhook）、六個要證據不要口頭保證的問題、**「有多少在 git 裡」決定你三個月的工作**、P0–P3 風險排序、交接該問前任的十題
- [[66-ingress-to-gateway-api]] — 附錄 AR：**從 Ingress 遷移到 Gateway API**——附錄 F 那份 annotation 百科的存在本身就是問題的證據；核心不是新語法而是**角色分離**（平台管 Gateway、應用管 HTTPRoute）、annotation 對照表**右半邊「對不上的那些」才是重點**、並行而非切換日、`ResolvedRefs: false` 會**靜默失敗**，以及「新服務用新的、舊的不動」這個中間立場
- [[67-scaling-limits]] — 附錄 AS：**規模瓶頸與 API Server 保護**——會先撞到的不是 Pod 數而是 **etcd 容量與 API Server 記憶體**；**etcd 滿了整個叢集唯讀（連刪東西都不行）**、一次 `list` 吃掉數 GB 且**復原時所有 controller 同時重連會重現當初的負載**、Job 不設 TTL 的累積、APF 是唯一能單方面部署的防線、**etcd 寫入延遲是最早的領先指標**
- [[68-registry-operations]] — 附錄 AT：**映像 registry 的營運**——教材前面都從 Pod 這端看，這份從另一端：registry 是**掛了就起不了新 Pod 的單點依賴**，而它掛掉時**你的監控是綠的**；`imagePullPolicy` 依 tag 決定預設值造成的「同版本不同節點行為不同」、`latest` 讓 git 不再是真相來源、**清理映像前必須先掃叢集在用的**，以及速率限制型 ImagePullBackOff 與 `exec format error`
- [[69-third-self-assessment]] — 附錄 AU：**第三份自我檢測**——附錄 X 之後教材又長出 **22 份、13 萬字沒被考過**；**70 題**針對「答錯會造成實際損失」的判斷，附 10 題紅色警戒清單（冪等、CronJob 重疊、連線數乘法、掛 Docker socket、registry 掛掉監控是綠的、etcd 唯讀）
- [[70-node-lifecycle-and-ha]] — 附錄 AV：**節點生命週期與控制平面高可用**——SSH 上去修的代價是**新節點不會有你的修改**；節點失聯到 Pod 重排預設約**五分半鐘空窗**（想更快要靠多副本而非調短參數）、**兩台 etcd 比一台更糟**（容錯都是 0 但故障機率加倍）、自動修復沒速率限制會陷入全叢集重建迴圈、沙箱執行時多數人不需要（先用專用節點池）
- [[71-schema-migration]] — 附錄 AW：**資料庫 schema 變更與部署的交界**——核心洞見：**滾動更新讓每一次部署都變成新舊版本並存**，所以 expand-contract 不是進階技巧而是基本功；加 `NOT NULL` 欄位會讓舊程式碼**寫入全失敗但讀取正常所以監控是綠的**、**migration 放在應用啟動或 initContainer 會每個副本各跑一次**、`PreSync` + `backoffLimit: 0` 讓它 fail closed、**down script 能還原結構但還不回資料**
- [[72-cascading-failure]] — 附錄 AX：**級聯失敗與韌性模式**——為何一個「非關鍵」下游變慢會讓整站掛掉；**慢比掛更危險**（掛是快速失敗，慢會綁住資源）、**三層各重試 3 次 = 27 倍**且發生在對方最脆弱時、**內層超時比外層長等於永遠不會生效**、readinessProbe 不該檢查下游（否則所有副本同時消失）、**下游是瓶頸時 HPA 是加油不是滅火**
- [[73-long-lived-connections]] — 附錄 AY：**長連線（gRPC／WebSocket）在 K8s 上的行為**——附錄 W 那兩行的展開；四個看似無關的症狀（HPA 擴了沒用、部分 Pod 滿載其他閒置、部署後斷線、WebSocket 每 60 秒斷）**根源同一個：K8s 預設網路模型是為短連線設計的**；**「重啟客戶端就好了」是最強指紋**、限制連線壽命是被低估的純伺服器端解、金絲雀權重只影響新連線
- [[74-distributed-tracing]] — 附錄 AZ：**分散式追蹤**——教材到處推薦「導入分散式追蹤」卻從沒說怎麼做，這份補上第三支柱；**它的價值是把「哪裡慢」從推理變成觀察**、context propagation 斷一處後面全是孤兒（**佇列是最常見斷點**）、**head-based 取樣 1% = 丟掉 99% 的錯誤 trace**、不可用取樣後的 trace 算 metrics，以及「告警→metrics→trace→logs」這條動線才是可觀測性的真正產出

### 建模與最佳化 Modeling（詳見 [[modeling-moc]]）

- [[mp-model-fundamentals]] — 建模為什麼需要方法論而非經驗、古典四元件如何擴充為五元件、決策活動與計算的判準差異
- [[system-elements]] — 如何從系統描述中識別出元素、判斷資料的 own/shared 與 primary element、individual 對 collective 的量化性質判斷
- [[decision-activities]] — 決策活動如何從系統動詞與參與元素中系統化推導出來，以及為何「有計算值的動作」不該被誤定義成決策變數
- [[system-calculations]] — 三種計算變數（auxiliary/logical/bound）怎麼定義，以及為何決策變數與計算變數的角色必須徹底分開
- [[specification-types]] — 規格(specification)為何不等於限制式(constraint)，五種語意分類加上如何揪出隱含規格
- [[logical-specifications-guide]] — 用 big-M 開關技巧把 NOT/OR/AND/IF-THEN/IFF 等邏輯運算子轉成線性限制式
- [[quantitative-nature-of-elements]] — 元素的「數量性質」是建模者的選擇而非題目給定，教你判斷何時該拆開、何時該合併
- [[gs-worked-examples]] — 六個由淺入深的完整案例，把前七章方法論一次串起來實戰演練
- [[mathematical-programming-overview]] — 模型是什麼、為什麼要建模、LP/NLP/IP/stochastic programming 模型分類
- [[building-lp-models]] — 線性為什麼讓 LP 好解、目標函數五種類型與限制式十一種類型完整分類、好模型三要素
- [[structured-lp-models]] — 大型 LP 如何由多工廠/多產品/多期小模型組合出 block angular 結構，以及 Dantzig-Wolfe decomposition
- [[lp-applications-and-networks]] — LP 在各產業的應用地圖、input-output 經濟模型，以及七種網路模型
- [[interpreting-lp-solutions]] — dual model、shadow price、reduced cost 的經濟意義，以及 alternative optima/degeneracy 陷阱
- [[nonlinear-and-separable-programming]] — convex/non-convex 決定局部解是否等於全域解，separable programming 分段線性近似
- [[integer-programming-fundamentals]] — IP 何時該用、四類求解法概觀，指示變數、命題邏輯轉限制式、SOS1/SOS2 建模工具箱
- [[special-integer-programming-structures]] — set covering/packing/partitioning、knapsack、TSP、VRP、QAP、column generation
- [[integer-programming-refinement]] — IP formulation 好壞對比（symmetry、big-M、bounds tightening）、facet 化簡
- [[mp-implementation-in-practice]] — MP 模型從算出答案到被組織採用要跨過哪些坎：決策者參與、集中化 vs 去中心化、資料維護
- [[case-food-manufacture-1]] — 六個月原油調配存貨問題，示範單期 LP 擴充成多期模型，正確線性化品質區間限制
- [[case-food-manufacture-2]] — 延續案例1，加入三條邏輯規則，示範 0-1 指示變數與 semi-continuous variable
- [[case-factory-planning-1]] — 七產品四製程多期生產排程，示範 product mix 問題與 shadow price 在擴產決策的應用
- [[case-factory-planning-2]] — 把維修時程從已知變成模型決策，示範整數變數如何避免對稱解爆炸
- [[case-manpower-planning]] — 三種技能人力逐年演變，示範「最小化資遣」vs「最小化成本」兩種目標函數的代價差異
- [[case-refinery-optimisation]] — 蒸餾/重組/裂解/調和四道工序串成一張 LP，示範 structured multi-stage 製程模型
- [[case-mining]] — 五年四礦選三運作，示範用兩組 0-1 變數分別表達「當期運作」與「永久關閉」
- [[case-farm-planning]] — 牛群依年齡拆世代鏈、作物多期存量流動，示範貸款年金折現避免模型過度舉債
- [[case-economic-planning]] — 動態 Leontief 三產業經濟模型，三種目標函數導出三種成長路徑
- [[case-decentralisation]] — 二次指派問題(QAP)真實案例，示範 0-1 乘積變數線性化二次目標函數
- [[case-curve-fitting]] — 用 LP 做曲線擬合，示範 goal programming 偏差變數與 minimax 轉線性目標
- [[case-logical-design]] — 用最少 NOR 邏輯閘組出指定真值表，示範命題邏輯真值表轉 0-1 限制式
- [[case-market-sharing]] — 23 家零售商依七指標分配市場，示範 goal programming 在 0-1 指派問題求解異常困難的教訓
- [[case-opencast-mining]] — 露天採礦區塊前置關係約束，約束矩陣全單模，LP relaxation 自動得整數解
- [[case-tariff-rates]] — 電力機組排程 MIP，示範整數解沒有真正 shadow price 時如何折衷估算邊際電價
- [[case-hydro-power]] — 在火力機組排程骨架上疊加水庫水位變數，示範跨時段庫存平衡取代動態規劃
- [[case-3d-noughts-and-crosses]] — 3×3×3 立體井字遊戲組合最小化，示範單向邏輯+目標函數方向讓求解器自己補完限制式
- [[case-optimising-a-constraint]] — 把一條 0-1 限制式本身當成待簡化對象，用邏輯等價找出最乾淨寫法
- [[case-distribution-1]] — 工廠+轉運站+客戶配送網路，示範 transhipment 建模與同骨架換目標函數處理多目標
- [[case-depot-location]] — 在配送網路上疊加 0-1 選址開關，示範 fixed charge 問題在網路節點層級的應用
- [[case-agricultural-pricing]] — 政府牛奶/奶油/起司定價，價格彈性線性化到 separable programming 全流程
- [[case-efficiency-analysis]] — 28 間展示中心 DEA 效率評估，把比率型目標轉成可解 LP
- [[case-milk-collection]] — 兩天路線容量限制 TSP/VRP，示範子巡迴消除按需追加求解
- [[case-yield-management]] — 三期航空票價多階段隨機規劃，情境樹取代連續需求曲線
- [[case-car-rental-1]] — 四城市租車調度，把車隊流動建模成循環網路流，示範「現實整數」不代表「模型必須整數」
- [[case-car-rental-2]] — 從既有 LP 敏感度分析長出投資決策，示範 precedence 與 cardinality 邏輯限制式疊加在網路流上
- [[case-lost-baggage-distribution]] — TSP 改造成不繞回原點的 Hamiltonian path，示範子迴路消去延遲生成
- [[case-protein-folding]] — 蛋白質摺疊翻譯成配對+恰好一次轉折的 0-1 邏輯限制式
- [[case-protein-comparison]] — contact map 最大公共子圖比對，最優值本身就是相似度的答案

## Tech / Summaries

- [[argocd-tutorial-summary]] — 既有 ArgoCD 教學筆記摘要

## Personal / Entities

（尚無頁面）

## Personal / Concepts

### 資產配置與投資教材（詳見 [[資產配置與投資]]）

寫給「科技業工程師、投資完全新手」的 **15 章正文 + 1 補充篇 + 4 附錄 + 5 張圖解**，從人力資本集中風險講到台灣實務落地（複委託／稅／RSU）。頁面實體放在 `wiki/personal/concepts/資產配置與投資/`。**全數完成並通過驗收**（跨章數字重算一致、wikilink 無斷鏈、mermaid 語法自查通過）。只有一個晚上的話讀 [[00-why-asset-allocation]]、[[07-choose-your-allocation]]、[[14-action-checklist]] 三章。

- [[資產配置與投資]] — 總目錄、全書地圖與進度表
- [[00-why-asset-allocation]] — **你已經重倉科技業了**：人力資本是金融資產的十倍且完全未分散、失業與股災同時發生的相關性、資產配置 = 類別與比例（不是選標的）、Brinson 90% 的正確讀法、工程師的過度最佳化陷阱
- [[01-money-map]] — 財務盤點與地基四件事：資產負債表（未歸屬 RSU 不算資產）、**儲蓄率在前十年勝過報酬率**的兩組試算、還債利率分界表、緊急預備金科技業建議 6~12 個月、保障與投資要分開（投資型保單）、勞退自提的節稅與流動性取捨、執行順序決策圖
- [[02-return-and-compounding]] — 報酬三來源拆解（股息＋盈餘成長＋估值變化，第三項長期趨近零）用來過濾騙局、**實質報酬才是真的**（定存 30 年購買力剩八成）、複利大部分成果在後期所以早 10 年 > 多存 20 年、**費用也在複利**（1.5% 吃掉 680 萬）、三個數字誤用：波動拖累／年化 7% 不是每年 7%／別用最近十年外推
- [[03-what-risk-really-means]] — 風險至少五種意思、標準差的三個侷限、**最大回撤與回本不對稱（跌 50% 要漲 100%）**、風險承受度三維度取最小（能力客觀／意願主觀／需求倒推）、把百分比換成金額的誠實測試、**順序報酬風險**（累積期早跌有利、提領期早跌致命）、時間分散是迷思（縮小年化離散、放大終值離散）
- [[04-asset-classes]] — 每個資產先問「**它在組合裡做什麼工作**」（成長引擎／穩定器／流動性／保險）、本國偏誤與台股雙重集中（全球市值 2% + 單一成分股過半 + 與人力資本重疊）、**高收益債是假穩定器**（股災時跟著崩）、duration 決定利率敏感度（2022 長債 −30%）、穩定器用台幣定存避免匯率反效果、黃金是沒有現金流的保險、加密貨幣報酬 100% 來自估值變化、三條紅線
- [[05-etf-and-indexing]] — **Sharpe 的算術**（主動整體扣費用後必然落後，是恆等式不是統計）、市值加權自動再平衡但會集中、**費用率是唯一 100% 可控的變數**（1.5% 吃掉獲利約三分之一）、看 ETF 的七個欄位（經理費≠總費用率）、**高股息不是額外的錢**（除息機制＋稅與摩擦，累積期不利）、**槓桿 ETF 每日重設造成波動衰減**、主題型 ETF 在最熱時發行
- [[06-correlation-and-rebalancing]] — **報酬線性相加、風險不是**（組合變異數公式與 ρ 從 +1 到 −0.5 的實算：同樣 5.4% 報酬、波動 13.2%→9.8%）、分散只消得掉非系統性風險 → **市場只為不可分散的風險付錢**、三個陷阱（危機時相關性趨近 1、2022 股債同跌是低通膨假設失效、相關矩陣是後照鏡）、再平衡確定做到的是控風險不是加報酬、**累積期最好的再平衡工具是新資金**
- [[07-choose-your-allocation]] — 決定重要性排序（股債比 >> 內部切分 >> 選哪檔）、**用最壞情況反推**（回撤 ≈ 股票比例 × 50%，代入實際金額）、用配置追報酬缺口效率極差（80→100% 只多 0.8% 卻多 10 個百分點回撤）、**分桶提供崩盤時的正確敘事**、五個經典模型的假設與失效條件（60/40 在 2022、全天候對累積期太保守）、台股佔股票部位 10~40% 的決策框架、過度設計四警訊
- [[08-taiwan-implementation]] — 三條管道（台灣 ETF／複委託／海外券商）**最大差別是稅不是手續費**、台灣不課證所稅所以低周轉最有利、海外所得走最低稅負制且只在賣出時實現、**ETF 註冊地決定股息預扣（美 30% vs 愛爾蘭 15%）**、**美國遺產稅非居民免稅額只有 6 萬美元**（複委託是否適用見解不一）、複委託低消陷阱、穩定器留台幣、按資產規模選路徑
- [[09-rsu-and-concentration]] — 公司股票是**雙重曝險的單點故障**（薪水/年終/工作/持股同時出事）、**核心反問「給我等值現金我會買自家股票嗎」**（持有＝買進）、稟賦效應與三個心理障礙、集中度上限建議 10%、**歸屬即賣**與「按高價課稅按低價持有」的泡沫教訓、ESPP 的參加與持有是兩個決定、未上市股票當成 0、賣出後別再買同產業
- [[10-execution-plan]] — 計畫死於執行而非設計、一次投入期望值較高但**分批是心理保險**（>30% 資產分 6~12 個月且機械執行）、別把分批偷換成「等跌再進場」、投入頻率判準是固定成本佔比 <0.5%、**「先付給自己」把意志力移出流程**、年度檢視 30 分鐘且多數年份結論是什麼都不做、嚴格區分再平衡與改目標、**查看頻率與投資期限成反比**（短視損失趨避）
- [[11-behavioral-traps]] — **行為差距每年一到三個百分點是被自己拿走的**、直覺系統為草原演化所以每條本能都指向錯誤方向、十個陷阱（損失趨避／近因／從眾／過度自信／確認／錨定／心理帳戶／稟賦／後見之明／行動偏誤）、三個高風險情境的預案（**7 天冷靜期**）、**知道偏誤不會免疫 → 改架構而非更努力**、五道結構性防禦、工程師特有三陷阱（過度最佳化／寫程式打敗市場／技術理解≠投資優勢）
- [[12-tax-and-safety-net]] — **確定的報酬值得更多注意力**、邊際稅率是所有節稅決策的基準、台灣不課證所稅的三個推論、節稅順序（勞退自提 ≥20% 才划算／扣除額擇優／申報方式／控制課稅時點）但**別讓稅務尾巴搖狗**、工程師最大破洞是**失能保障**、投資型保單的費用拆解與「繼續繳 vs 解約 vs 減額繳清」算法、退休三層與**勞保保守當 0**、**4% 法則的五個限制 → 保守用 3~3.5%**、缺口四槓桿裡提高報酬率效果最小
- [[13-compute-it-yourself]] — 八段可直接跑的 numpy 程式（複利反推／組合報酬波動／ρ 對波動的曲線／效率前緣／蒙地卡羅／順序報酬／費用）；**核心實驗：期望報酬假設動 1 個百分點，最佳股票權重從 14% 跳到 40%** → 均值-變異數最佳化是**誤差最大化器**，追求穩健而非最佳；蒙地卡羅要看分布不看平均（P5 才是你的下限）；把提領金額設 0 可證明順序只在有現金流時才重要
- [[14-action-checklist]] — **30 天啟動計畫**（盤點→補地基→紙上決定配置→執行，前三週不投資）、**完整 IPS 模板**（含「允許/不允許修改的情況」兩份清單與寫給崩盤時自己的話）、月/季/年檢查清單、**20 條紅色警戒**（結構性／成本稅務／配置／行為四類）、一頁式決策樹、收尾四件事：存夠多、買夠廣夠便宜、別亂動、等夠久
- [[15-real-estate]] — **補充篇**：正確的比較是「持有成本 vs 房租」（**頭期款的機會成本**最常被漏）、**房價租金比 > 30 則租房較划算**而台灣雙北收益率僅 1.5~2.5%（買房報酬高度依賴續漲）、**房貸是多數人一生最高的槓桿**（頭期款兩成＝4 倍，房價跌 25% 頭期款歸零）、台灣多為機動利率要做升息 1.5pp 壓力測試、**寬限期沒它就買不起＝買太貴**、買房讓配置一天內作廢（不動產可能瞬間佔八成）、集中風險三重變四重、**買房後金融資產要大幅偏向海外**、工程師特有的地理流動性代價
- [[appendix-a-glossary]] — 附錄 A：約 90 條術語 A–Z，每條「一句定義 + 為什麼你該在意 + 章節連結」，另收中文專有名詞（二代健保補充保費、最低稅負制、勞退自提、證所稅、除息）
- [[appendix-b-numbers]] — 附錄 B：**散落各章的數字全部集中**——規劃用假設值、各資產報酬/波動量級、**回本不對稱表**、配置對應的最壞回撤與預期報酬、費用率三十年帳、72 法則、儲蓄率 vs 報酬率對照、台灣與美國稅制數字、緊急預備金與債務利率分界、配置與再平衡規則值、退休試算、**十一條常用公式**、20 條紅色警戒濃縮版
- [[appendix-c-faq]] — 附錄 C：45 題 FAQ 分八組，含**「我朋友說……」系列**（買 0050 就好／高股息 8%／美股年化 10%／年輕就該 100% 股票／定存最安全／終身險划算／勞保會倒／買房才是最好的投資）、標的比較（VT/VTI/VOO 重疊、台幣定存 vs 債券 ETF）、台灣稅務實務、RSU 五題、崩盤與停扣的處置、人生階段（結婚/失業/加薪/退休前/小孩）、**「我怎麼知道自己做對了」的五題判準**（全部是可控項目）
- [[appendix-d-self-assessment]] — 附錄 D：**60 題三級自我檢測**，答案用 `<details>` 摺疊強制先自己講；L3 十八題全是「給症狀反推根因」（照著書做卻輸給指數／2022 股債同跌就說分散沒用／年化 15% 的回測該問什麼／組合裡 0050+006208+半導體 ETF+公司股票）；**12 題標紅色警戒**（答錯會造成實際財務損害），附題號→章節對照與過關標準

## Personal / Summaries

（尚無頁面）

## Tech / Synthesis

- [[react-frontend-development-roadmap]] — 從 TypeScript 基礎到可維護 React SPA 的開發路線
- [[javascript-typescript-react-foundations]] — 從 JavaScript 執行模型到 React Hook 的單一基礎教材

## Synthesis

- [[uiux-design-cheat-book]] — 28 章、284 條「當…就應該…」UI/UX 情境規則，28 張章節對照圖，含元件選擇矩陣、6 種頁型配方與來源邊界

---

## Raw Sources（速查）

✓ = 已 ingested 並建立 wiki 頁

### Tech / DevOps

- `raw/tech/devops/Docker/Docker/Docker.md` ✓ → [[raw/devops/Docker/Docker]]
- `raw/tech/devops/Docker/Docker Compose/Docker Compose.md` ✓ → [[raw/devops/Docker/Docker]]
- `raw/tech/devops/Docker/Docker 部屬範例/Docker 部屬範例.md` ✓ → [[raw/devops/Docker/Docker]]
- ~~`raw/tech/devops/Docker/Docker Compose yaml 架構.md`~~ → 已整合
- ~~`raw/tech/devops/Docker/Docker Compose 重開.md`~~ → 已整合
- `raw/tech/devops/Kubernetes (K8s)/Kubernetes (K8s).md` ✓ → [[kubernetes]]
- `raw/tech/devops/K8s YAML 概念與架構/K8s YAML 概念與架構.md` ✓ → [[kubernetes]]
- `raw/tech/devops/Minikube 介紹/Minikube 介紹.md` ✓ → [[minikube]]
- `raw/tech/devops/Helm Chart/Helm Chart.md` ✓ → [[helm]]
- `raw/tech/devops/kubectl 指令/kubectl 指令.md` ✓ → [[kubectl]]
- `raw/tech/devops/Vault/Vault.md` ✓ → [[raw/devops/Vault]]
- `raw/tech/devops/Azure Pipeline/Azure Pipeline.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/部署筆記/部署筆記.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/部屬後端/部屬後端.md` ✓ → [[cicd-pipeline]]
- `raw/tech/devops/argocd-tutorial/argocd-tutorial.md` ✓ → [[argocd]]
- `raw/tech/devops/azure-pipelines/azure-pipelines.md`
- `raw/tech/devops/complete-tutorial/complete-tutorial.md`
- `raw/tech/devops/harbor-tutorial/harbor-tutorial.md`
- `raw/tech/devops/helm-tutorial/helm-tutorial.md`
- `raw/tech/devops/k8s-rbac/k8s-rbac.md`
- `raw/tech/devops/kubectl-api-version/kubectl-api-version.md`
- `raw/tech/devops/minikube-tutorial/minikube-tutorial.md`
- `raw/tech/devops/postgresql-k8s/postgresql-k8s.md`
- `raw/tech/devops/vault-tutorial/vault-tutorial.md`
- `raw/tech/devops/troubleshooting/troubleshooting.md`

### Tech / Web Dev

- `raw/tech/web-dev/TypeScript/TypeScript.md` ✓ → [[raw/Web Framework/TypeScript]]
- `raw/tech/web-dev/React/React.md` ✓ → [[wiki/tech/entities/react]]
- `raw/tech/web-dev/React/React + TypeScript 開發手冊.md` ✓ → [[wiki/tech/entities/react]], [[raw/Web Framework/TypeScript]]
- `raw/Web Framework/NET Web API/`（25 份筆記，含 Chapter 1～10 與補充篇）✓ → [[dotnet-web-api]]
- `raw/tech/web-dev/HTML/HTML.md`
- `raw/tech/web-dev/CSS/CSS.md`
- `raw/tech/web-dev/react-hooks-gotchas/react-hooks-gotchas.md`
- `raw/tech/web-dev/uiux-notes/uiux-notes.md`

### Tech / Languages

- `raw/Languages/languages/Typescript/typescript-web-research.md` ✓ → [[raw/Web Framework/TypeScript]]（由淺至深完整語法，含進階型別操作）
- `raw/Languages/languages/C#/C#.md` ✓ → [[csharp]]
- `raw/Languages/languages/csharp-debug-test/csharp-debug-test.md`

### Tech / Database

- `raw/tech/database/SQL 資料庫基本指令/SQL 資料庫基本指令.md` ✓ → [[oracle]]
- `raw/tech/database/Oracle CMD 指令筆記/Oracle CMD 指令筆記.md` ✓ → [[oracle]]
- `raw/tech/database/Oracle To C#/Oracle To C#.md` ✓ → [[oracle]]
- `raw/tech/database/SQL 建立資料表/SQL 建立資料表.md`
- `raw/tech/database/SQL Basic Functions/SQL Basic Functions.md`
- `raw/tech/database/SQL 指令語法速查/SQL 指令語法速查.md`
- `raw/tech/database/Oracle Server操作/Oracle Server操作.md`
- `raw/tech/database/PL SQL/PL SQL.md`
- `raw/tech/database/Procedure & Function/Procedure & Function.md`

### Tech / Git

- `raw/tech/git/Git 指令筆記/Git 指令筆記.md` ✓ → [[git]]
- `raw/tech/git/Git 每日開發 SOP/Git 每日開發 SOP.md` ✓ → [[git]]
- `raw/tech/git/Github 心得/Github 心得.md` ✓ → [[git]]
- `raw/tech/git/SourseTree(Local) 筆記/SourseTree(Local) 筆記.md`
- `raw/tech/git/git-tutorial/git-tutorial.md`

### Tech / System

- `raw/tech/system/Linux 觀念/Linux 觀念.md` ✓ → [[linux]]
- `raw/tech/system/Ubuntu 筆記/Ubuntu 筆記.md` ✓ → [[linux]]
- `raw/tech/system/xrdp 設定/xrdp 設定.md`
- `raw/tech/system/網路設定/網路設定.md`

### Tech / Networking

- `raw/tech/networking/網域小知識/網域小知識.md` ✓ → [[domain-networking]]
- `raw/tech/networking/google-oauth-tutorial/google-oauth-tutorial.md`

### Tech / Tools

- `raw/tech/tools/Visual Studio Code/Visual Studio Code.md`
- `raw/tech/tools/LaTex/LaTex.md`
- `raw/tech/tools/VBA/VBA.md`
- `raw/tech/tools/markdown哲學/markdown哲學.md`

### Tech / Simulation

- `raw/tech/simulation/NetLogo/NetLogo.md`
- `raw/tech/simulation/Flexsim/Flexsim.md`
- `raw/tech/simulation/Game Notes (Godot)/Game Notes (Godot).md`

### Tech / Optimization

- `raw/tech/optimization/GLPK/GLPK.md`
- `raw/tech/optimization/AMPL/AMPL.md`

### Tech / Modeling

- `raw/Modeling/(Book)Modelling in Mathematical Programming.pdf` ✓ → [[modeling-moc]]（書1，García Sánchez 方法論全書 8 章）
- `raw/Modeling/WileyModelBuildinginMathematicalProgramming5th2013.sharethefiles.com.pdf` ✓ → [[modeling-moc]]（書2，Williams Part I 方法論 11 章 + Part II/III/IV 全部 29 個經典案例）
