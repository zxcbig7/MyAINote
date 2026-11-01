---
type: concept
domain: tech
tags: [dotnet, aspnet, middleware, pipeline, requestdelegate, cors, http]
sources:
  - raw/Web Framework/NET Web API/NET Web API.md
created: 2026-08-14
updated: 2026-11-01
---

# 第 01 章：Request Pipeline — 洋蔥不是比喻，是實作

## 三個順序引起的災難

先看三段幾乎一樣的程式碼，差別只在順序。

```csharp
// A
app.UseAuthentication();
app.UseAuthorization();
app.UseCors("ReactApp");
```

```csharp
// B
app.UseAuthorization();
app.UseAuthentication();
app.UseCors("ReactApp");
```

```csharp
// C
app.UseCors("ReactApp");
app.UseAuthentication();
app.UseAuthorization();
```

三段都能編譯、都能啟動、都不會有任何警告。但行為完全不同：

- **A** 的後果是 401 回應**沒有 CORS header**。瀏覽器看到跨網域回應缺少 `Access-Control-Allow-Origin` 就直接擋掉，前端拿到的是 CORS 錯誤而不是 401。前端工程師會來問你「為什麼登入過期會出現 CORS 錯誤」，而你在後端 log 裡看到的是一個正常的 401。
- **B** 的後果更嚴重：`UseAuthorization` 執行時，`HttpContext.User` 還沒被 `UseAuthentication` 填好，是一個匿名的空身分。授權檢查會全部失敗——如果你只有 `[Authorize]` 就只是全部 401；但如果有 `[Authorize(Roles = "Admin")]` 搭配某些自訂 fallback policy，可能出現更難預料的結果。
- **C** 是正確的（雖然還少了 `UseRouting`，後面會補）。

順序不是風格問題，是語意問題。要能夠自己推導出正確順序而不是背誦官方文件的清單，就必須知道 pipeline 到底是怎麼組出來的。這一章要拆的就是這件事。

---

## 一、`RequestDelegate`：整個 pipeline 只是一個函式

ASP.NET Core 處理 HTTP 請求的核心抽象只有一個型別：

```csharp
public delegate Task RequestDelegate(HttpContext context);
```

「吃一個 `HttpContext`，回傳一個 `Task`。」就這樣。

Kestrel 收到一個請求時做的事是：建立 `HttpContext`（把 socket 上的位元組解析成 `Request.Path`、`Request.Headers` 等物件）、呼叫這個委派、等它回來、把 `Response` 寫回 socket。

那 middleware 是什麼？**middleware 是一個「吃 `RequestDelegate`、吐 `RequestDelegate`」的函式**：

```csharp
public delegate RequestDelegate Middleware(RequestDelegate next);
```

它拿到「後面所有東西合起來的那個函式」（`next`），回傳一個新的函式——這個新函式做自己的事，並且在中間某處呼叫 `next`。

這個型別簽章本身就解釋了洋蔥。既然每個 middleware 都把 `next` 包在自己裡面，那麼把 N 個 middleware 串起來的結果，必然是一層包一層的結構。**洋蔥不是教學用的比喻，它是這個型別簽章的必然結果。**

---

## 二、組裝：為什麼是由後往前

`app.Use(...)` 並沒有立刻執行任何東西，它只是把 middleware 加進一個 `List`：

```csharp
private readonly List<Func<RequestDelegate, RequestDelegate>> _components = new();

public IApplicationBuilder Use(Func<RequestDelegate, RequestDelegate> middleware)
{
    _components.Add(middleware);
    return this;
}
```

真正的組裝發生在 `Build()`（由 `app.Run()` 內部呼叫）：

```csharp
public RequestDelegate Build()
{
    // 最內層：什麼都沒匹配到就回 404
    RequestDelegate app = context =>
    {
        context.Response.StatusCode = StatusCodes.Status404NotFound;
        return Task.CompletedTask;
    };

    // 由後往前包
    for (var c = _components.Count - 1; c >= 0; c--)
    {
        app = _components[c](app);
    }

    return app;
}
```

這十幾行是整個 ASP.NET Core 請求模型的心臟。值得逐句理解：

**先建立最內層。** 那是一個直接回 404 的委派。這解釋了一件事——為什麼一個什麼都沒 map 的 ASP.NET Core 應用會回 404 而不是掛掉。404 是 pipeline 的地板，不是誰特別實作的錯誤處理。

**然後由後往前，一層層往外包。** 迴圈從清單尾端開始，每次把「目前已組好的那一坨」當作 `next` 傳給前一個 middleware，得到一個更大的委派。

**最後拿到的 `app` 是第一個 middleware 產生的委派。** 執行它，就會像剝洋蔥一樣一層層往內走。

用實際的程式碼看這個過程。假設寫了三個：

```csharp
app.Use(async (ctx, next) => { Console.WriteLine("A 進"); await next(); Console.WriteLine("A 出"); });
app.Use(async (ctx, next) => { Console.WriteLine("B 進"); await next(); Console.WriteLine("B 出"); });
app.Run(async ctx => { Console.WriteLine("C 終點"); await ctx.Response.WriteAsync("done"); });
```

輸出是：

```text
A 進
B 進
C 終點
B 出
A 出
```

這個順序有一個非常實用的推論：**`await next()` 之前的程式碼按註冊順序執行，之後的程式碼按反向順序執行。** 需要「最早介入」就往前放，需要「最後收尾、看到最終結果」就利用 `next()` 之後的位置。

例如計時 middleware 必須放在最前面，因為它要在 `next()` 前後夾住所有東西：

```csharp
app.Use(async (ctx, next) =>
{
    var sw = Stopwatch.StartNew();
    await next();
    sw.Stop();
    logger.LogInformation("{Method} {Path} → {Status} 耗時 {Ms}ms",
        ctx.Request.Method, ctx.Request.Path, ctx.Response.StatusCode, sw.ElapsedMilliseconds);
});
```

放在最前面，量到的是完整耗時；放在 `UseAuthentication` 後面，量到的就漏掉了認證的成本。

---

## 三、短路：不呼叫 `next()` 會怎樣

middleware 有權決定**不**呼叫 `next()`。這叫短路（short-circuit），是 pipeline 設計裡最重要的能力。

```csharp
app.Use(async (ctx, next) =>
{
    if (!ctx.Request.Headers.ContainsKey("X-Api-Key"))
    {
        ctx.Response.StatusCode = 401;
        await ctx.Response.WriteAsync("Missing API key");
        return;                      // 不呼叫 next()，內層完全不會執行
    }
    await next();
});
```

框架自己大量使用這個機制：`UseAuthorization` 檢查失敗時短路回 401/403、`UseCors` 遇到 preflight 的 `OPTIONS` 請求時短路回應而不往下走、`UseStaticFiles` 匹配到檔案就直接回檔案內容不進 MVC。

`app.Run()` 是短路的極端形式——它註冊一個**terminal middleware**，簽章裡根本沒有 `next` 參數，永遠不會往下傳。所以 `app.Run()` 後面再註冊的 middleware 都是死程式碼：

```csharp
app.Run(async ctx => await ctx.Response.WriteAsync("Hello"));
app.UseAuthorization();   // ⚠️ 永遠不會被執行到
```

（注意這個 `app.Run(RequestDelegate)` 和第 00 章的 `app.Run()`（無參數，啟動應用程式）是兩個完全不同的方法，只是同名。這是 ASP.NET Core 命名上的一個歷史包袱。）

---

## 四、三種寫 middleware 的方式，以及 DI 的陷阱

### 4.1 Inline lambda

適合三五行的簡單邏輯。缺點是塞在 `Program.cs` 裡，多了就雜亂，也不好測試。

```csharp
app.Use(async (ctx, next) =>
{
    ctx.Response.Headers["X-Trace-Id"] = Activity.Current?.Id ?? ctx.TraceIdentifier;
    await next();
});
```

### 4.2 Convention-based 類別（最常見）

沒有介面要實作，靠**約定**：建構子第一個參數是 `RequestDelegate`，並且有一個名為 `InvokeAsync`（或 `Invoke`）的方法，第一個參數是 `HttpContext`。

```csharp
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context, IUserService userService)
    {
        _logger.LogInformation("進入 {Path}", context.Request.Path);
        await _next(context);
    }
}

app.UseMiddleware<RequestLoggingMiddleware>();
```

這裡有本章第二個關鍵陷阱，而且它非常容易誤踩。

**Convention-based middleware 的實例是 Singleton。** 它在應用程式啟動時被建立一次，之後所有 request 共用同一個實例。原因回到第二節的組裝機制：pipeline 在 `Build()` 時組裝一次，每個 middleware 的委派被固定下來，之後不再重建。

於是：

```csharp
// ❌ 建構子注入 Scoped 服務
public RequestLoggingMiddleware(RequestDelegate next, IUserService userService)
```

`IUserService` 是 Scoped，但這個 middleware 只建立一次。這個 Scoped 服務會被俘虜成 Singleton——如果它裡面包著 DbContext，就是災難：所有 request 共用一個非執行緒安全的 DbContext，在低流量測試環境可能完全不出事，上線後開始出現 `A second operation was started on this context` 或者更詭異的資料交錯。

好消息是框架會擋：從 root provider 解析 Scoped 服務會拋 `InvalidOperationException`。但**這個檢查只在 scope validation 開啟時生效**——也就是預設只在 Development。這正是第 00 章建議把 `ValidateScopes` 明確打開的理由之一。

正解是把 Scoped 依賴宣告在 **`InvokeAsync` 的參數**上：

```csharp
// ✅ InvokeAsync 的額外參數會從「當前 request 的 scope」解析
public async Task InvokeAsync(HttpContext context, IUserService userService)
```

框架每次呼叫 `InvokeAsync` 時，會用當前 request 的 scope 來解析這些參數。這叫 method injection，是 middleware 專屬的一個特例機制。

判斷規則很簡單：**Singleton 依賴放建構子（省下每次解析的成本），Scoped/Transient 依賴放 `InvokeAsync` 參數。** `ILogger<T>` 是 Singleton，放建構子沒問題。

### 4.3 IMiddleware（工廠模式）

實作 `IMiddleware` 介面，並且把自己註冊進 DI：

```csharp
public class ApiKeyMiddleware : IMiddleware
{
    private readonly IUserService _userService;   // Scoped 依賴可以放建構子

    public ApiKeyMiddleware(IUserService userService)
    {
        _userService = userService;
    }

    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        // ...
        await next(context);
    }
}

builder.Services.AddScoped<ApiKeyMiddleware>();   // 必須註冊
app.UseMiddleware<ApiKeyMiddleware>();
```

差別在於這個版本**每個 request 都從 DI 解析一次實例**（由 `IMiddlewareFactory` 負責）。因此建構子可以安全地注入 Scoped 服務，而且它是強型別的——打錯 `InvokeAsync` 的拼字會在編譯期被抓到，不像 convention-based 要到執行期才炸。

代價是每個 request 多一次物件建立與 DI 解析。

| | Convention-based | IMiddleware |
| --- | --- | --- |
| 實例數量 | 一個（Singleton） | 每 request 一個 |
| Scoped 依賴放哪 | `InvokeAsync` 參數 | 建構子或參數皆可 |
| 型別安全 | 靠約定，錯了執行期才知道 | 編譯期檢查 |
| 需要註冊到 DI | 否 | **是**（忘了會執行期報錯） |
| 效能 | 略優 | 每 request 多一次解析 |

實務建議：預設用 convention-based，並把 Scoped 依賴放 `InvokeAsync`。當 middleware 邏輯複雜、依賴多、需要單元測試時改用 `IMiddleware`。

---

## 五、順序的完整推導

現在有了機制，可以自己推導順序而不是背清單。原則只有一條：**每個 middleware 需要的前置條件，必須由排在它前面的 middleware 準備好。**

逐個問「它需要什麼、它產出什麼」：

| Middleware | 需要什麼 | 產出什麼 |
| --- | --- | --- |
| `UseExceptionHandler` | 無 | 捕捉內層所有例外 |
| `UseHsts` / `UseHttpsRedirection` | 無 | 可能短路（重導向） |
| `UseStaticFiles` | 無 | 匹配到就短路回檔案 |
| `UseRouting` | 無 | **在 `HttpContext` 上設定「選中的 Endpoint」** |
| `UseCors` | 選中的 Endpoint（才知道該 endpoint 的 CORS policy） | 加上 CORS header，preflight 短路 |
| `UseAuthentication` | 無 | **填好 `HttpContext.User`** |
| `UseAuthorization` | Endpoint（才知道有沒有 `[Authorize]`）+ `User` | 檢查失敗則短路 401/403 |
| `MapControllers` | 無 | 只登記 endpoint；真正執行它的是 pipeline 最後的 endpoint middleware |

推導結果：

```csharp
app.UseExceptionHandler();      // 最外層才能包住所有例外
app.UseHttpsRedirection();
app.UseStaticFiles();           // 靜態檔不需要走後面的認證授權，早點短路省成本
app.UseRouting();               // 必須在 CORS / Authorization 之前
app.UseCors();                  // 必須在 Authorization 之前（否則 401 沒有 CORS header）
app.UseAuthentication();        // 必須在 Authorization 之前（先有身分才能查權限）
app.UseAuthorization();
app.MapControllers();           // 登記 endpoint；執行由最後的 endpoint middleware 負責
```

現在回頭看開頭三段程式碼，答案是自明的：

- **A 錯**在 `UseCors` 排在 `UseAuthorization` 後面。授權失敗時 `UseAuthorization` 直接短路，控制權從內層往外返回，根本走不到 `UseCors`——但等等，`UseCors` 在它後面（更內層），所以是**根本沒進去過**。回應因此缺少 CORS header。
- **B 錯**在 `UseAuthorization` 排在 `UseAuthentication` 前面。授權執行時 `HttpContext.User` 還是空的。
- **C 對**（補上 `UseRouting` 後更完整）。

### 5.1 `UseRouting` 為什麼是分水嶺

`UseRouting` 做的事是：拿 `Request.Path` 去比對所有註冊的 endpoint，**選出**要執行的那一個，把它放進 `HttpContext.Features` 裡。注意它只是「選出」，並不執行。真正的執行在 pipeline 最後的 endpoint middleware 那一層。在 `WebApplication` 的寫法下，`MapControllers` 這類 `Map*` 只負責登記 endpoint，執行的 middleware 由框架自動放在最後，所以實測把其他 `Use*` 放在 `MapControllers` 前面或後面，行為相同；只有舊式 `app.UseEndpoints(...)` 明確出現時，排在它後面的 middleware 才會變成「只在沒命中 endpoint 時執行」。

為什麼要把「選擇」和「執行」拆成兩段、中間留一大塊空間？**因為那塊空間裡的 middleware 需要知道『這個請求最終會跑到哪個 endpoint』才能決定行為。**

`UseAuthorization` 是最好的例子。它必須知道目標 action 上有沒有 `[Authorize]`、有的話是哪個 policy。這個資訊是 endpoint 的 metadata，只有在 `UseRouting` 完成後才拿得到。同理 `UseCors` 要看 endpoint 上的 `[EnableCors]`，rate limiting 要看 endpoint 上的限流策略。

自己寫的 middleware 也能用這個資訊：

```csharp
app.Use(async (ctx, next) =>
{
    var endpoint = ctx.GetEndpoint();               // UseRouting 之後才有值
    var requiresAuth = endpoint?.Metadata.GetMetadata<IAuthorizeData>() is not null;
    // ...
    await next();
});
```

放在 `UseRouting` 之前，`GetEndpoint()` 永遠回 null。這是很多「為什麼我的 middleware 拿不到 endpoint」問題的答案。

.NET 6 之後，如果沒有明確呼叫 `UseRouting`，框架會在 pipeline 最前面自動插入一個。這個貼心設計有副作用：**你以為省了一行，實際上 `UseRouting` 被放到了最前面**——大多數情況沒差，但如果有 middleware 想在 routing 之前改寫 `Request.Path`（URL rewrite），就會發現改了沒用，因為路由早就選完了。需要精確控制時，明確寫出 `app.UseRouting()`。

`UseAuthentication` 與 `UseAuthorization` 也有類似的自動補法（.NET 7 起，在 `WebApplication` 下，且服務必須已註冊）。陷阱在於「只寫了一個」：實測只呼叫 `UseAuthentication()` 時，框架補的授權 middleware 會排在它前面，結果已登入的請求也一律 401，而且沒有任何例外或 log，症狀和順序寫反完全相同。所以仍然建議兩個都明確寫出，順序固定為認證在前、授權在後。

---

## 六、Response 已開始就回不了頭

pipeline 的返回路徑（`next()` 之後）有一個硬限制，是實務上第二常見的 middleware 錯誤來源：

```csharp
app.Use(async (ctx, next) =>
{
    await next();
    ctx.Response.Headers["X-Total-Time"] = sw.ElapsedMilliseconds.ToString();   // ❌ 可能炸
});
```

錯誤訊息：`Headers are read-only, response has already started.`

原因是 HTTP 的協定結構：header 走在 body 前面。一旦有任何一個位元組的 body 被寫進 socket，header 就已經送出去了，物理上不可能再改。內層 middleware 或 controller 只要開始寫回應（`WriteAsync`、序列化 JSON），header 就鎖死了。

`HttpResponse.HasStarted` 可以檢查狀態：

```csharp
await next();
if (!ctx.Response.HasStarted)
{
    ctx.Response.Headers["X-Total-Time"] = sw.ElapsedMilliseconds.ToString();
}
```

但這只是防止拋例外，header 該加的還是沒加上。要在 response 開始前的最後一刻做事，正確工具是 `OnStarting` 回呼：

```csharp
app.Use(async (ctx, next) =>
{
    var sw = Stopwatch.StartNew();

    ctx.Response.OnStarting(() =>
    {
        ctx.Response.Headers["X-Total-Time"] = sw.ElapsedMilliseconds.ToString();
        return Task.CompletedTask;
    });

    await next();
});
```

`OnStarting` 註冊的回呼會在「第一個位元組即將寫出」的那一刻執行——那時 header 還可以改。對應的還有 `OnCompleted`，在回應完全送出後執行，適合做記錄與清理（但不能再碰 response）。

同樣的道理解釋了為什麼「全域例外處理 middleware」在某些情況下無效：如果 controller 已經寫出了部分 response 才拋例外，外層的例外處理 middleware 接到例外時 response 已經開始，它沒辦法把狀態碼改成 500，只能讓連線以截斷的形式結束。這是 [[15-error-handling]] 的主題。

---

## 七、分支：`Map`、`MapWhen`、`UseWhen`

三個看起來很像的方法，差別在「分支之後會不會回到主線」以及「會不會動 Path」。

```csharp
// Map：依路徑前綴分支，分支結束後不回主線
app.Map("/admin", adminApp =>
{
    adminApp.UseMiddleware<AdminAuditMiddleware>();
    adminApp.Run(async ctx => await ctx.Response.WriteAsync("admin area"));
});

// MapWhen：依任意條件分支，一樣不回主線
app.MapWhen(ctx => ctx.Request.Query.ContainsKey("debug"), debugApp =>
{
    debugApp.Run(async ctx => await ctx.Response.WriteAsync("debug mode"));
});

// UseWhen：條件成立時「插入」額外 middleware，之後回到主線
app.UseWhen(ctx => ctx.Request.Path.StartsWithSegments("/api"), apiApp =>
{
    apiApp.UseMiddleware<ApiKeyMiddleware>();
});
```

`Map` 有一個容易忽略的副作用：**它會把匹配到的前綴從 `Request.Path` 移到 `Request.PathBase`。** 上面例子裡，請求 `/admin/users` 進到分支後，`Request.Path` 變成 `/users`，`PathBase` 變成 `/admin`。如果分支裡有路由或產生連結的邏輯，就得意識到這件事，否則會出現「路由怎麼都對不上」的困惑。

`UseWhen` 則是實務上更常用的那個——它的語意是「符合條件的請求多走幾道手續」，而不是「岔出去自成一個世界」。例如只對 `/api` 開頭的請求做 API key 檢查，其他路徑照常。

---

## 八、成本意識

每個 middleware 對**每一個**請求都有成本。以下是實務上值得注意的幾點。

**短路要放早。** 靜態檔案、健康檢查這類不需要認證的端點，如果排在認證授權後面，等於每次探測都白跑一遍 JWT 驗簽。K8s 的 liveness probe 每 10 秒一次、三個 Pod，一天就是兩萬六千次無謂的簽章驗證。

**別在 middleware 裡做同步 I/O。** middleware 對所有請求生效，一個同步的檔案讀取或 HTTP 呼叫會把 ThreadPool 執行緒卡住，在高併發下引發連鎖反應（[[06-async-and-threading]] 詳述）。

**讀 request body 要小心。** `Request.Body` 預設是**只能讀一次的前向串流**。middleware 讀完之後，controller 的 model binding 就讀不到了，現象是「參數莫名其妙是 null」。要讀就得先啟用緩衝：

```csharp
app.Use(async (ctx, next) =>
{
    ctx.Request.EnableBuffering();          // 允許重複讀取

    using var reader = new StreamReader(ctx.Request.Body, leaveOpen: true);
    var body = await reader.ReadToEndAsync();
    ctx.Request.Body.Position = 0;          // ⚠️ 一定要倒回開頭

    await next();
});
```

`EnableBuffering()` 會把 body 緩衝到記憶體（超過門檻則落到磁碟暫存檔）。這對大檔上傳是明顯的成本，所以「記錄所有 request body」這種需求要謹慎——它同時是效能問題和資安問題（密碼會進 log）。

**Middleware vs Filter 的選擇。** 兩者都能做橫切關注點，但層級不同：middleware 在 MVC 之外，看得到所有請求（包含靜態檔案、健康檢查），但看不到 model binding 的結果、不知道是哪個 action、也拿不到 `ModelState`。Filter 在 MVC 內部，反之。判斷法則是：**需要 MVC 的上下文（action 參數、ModelState、ActionResult）就用 Filter，需要涵蓋所有請求就用 middleware。** 完整比較在 [[05-filters-and-mvc-internals]]。

---

## 九、常見誤解

**「middleware 的順序照官方文件抄就好。」**
官方順序是一組預設情境下的正確解。一旦加入自訂 middleware、限流、回應快取、URL rewrite，就需要自己推導。推導的依據是「這個 middleware 需要誰先準備好什麼」，不是記憶。

**「`app.Use` 註冊的東西每個 request 都會重新建立。」**
不會。pipeline 在啟動時組裝一次，委派被重複使用。convention-based middleware 的實例是 Singleton，這正是 Scoped 依賴要放 `InvokeAsync` 參數的原因。

**「middleware 裡可以隨意注入任何服務。」**
建構子只能注入 Singleton。Scoped 服務要放 `InvokeAsync` 參數，或改用 `IMiddleware` 模式。

**「在 `next()` 之後改 response header 是安全的。」**
只有在內層完全沒開始寫 response 時才安全。要可靠地在回應前加 header，用 `Response.OnStarting`。

**「`UseRouting` 可以省略，反正框架會自動加。」**
自動加的位置在 pipeline 最前面。如果有 middleware 需要在路由選擇之前介入（URL rewrite、多租戶路徑改寫），就必須明確控制位置。

**「middleware 拿得到 `ModelState`。」**
拿不到。model binding 發生在 MVC 內部，middleware 執行時還沒發生（進去時）或已經結束（回來時）。需要它就用 Filter。

---

## 十、同事會來問你的問題

**Q：為什麼 401 回應在瀏覽器變成 CORS 錯誤？**
`UseCors` 排在 `UseAuthorization` 後面（更內層）。授權失敗時直接短路返回，`UseCors` 從來沒有執行過，回應因此沒有 `Access-Control-Allow-Origin`。瀏覽器擋掉這個沒有 CORS header 的跨域回應，前端看到的就是 CORS 錯誤而非 401。把 `UseCors` 移到 `UseAuthentication` 之前。

**Q：我在 middleware 裡讀了 request body，controller 的參數就變成 null 了。**
`Request.Body` 預設只能讀一次。讀之前呼叫 `Request.EnableBuffering()`，讀完把 `Body.Position` 設回 0。

**Q：middleware 建構子注入 `IUserService` 為什麼會爆 `Cannot resolve scoped service from root provider`？**
convention-based middleware 是 Singleton，建構子只能拿到 Singleton 服務。把 `IUserService` 移到 `InvokeAsync` 的參數，或改實作 `IMiddleware` 並註冊為 Scoped。

**Q：`ctx.GetEndpoint()` 一直是 null。**
這個 middleware 排在 `UseRouting` 之前。endpoint 是 `UseRouting` 選出來放進 context 的，之前拿不到。

**Q：Middleware 和 Filter 差在哪，什麼時候用哪個？**
Middleware 在 MVC 外層，涵蓋所有請求但看不到 action 資訊；Filter 在 MVC 內層，拿得到 action 參數、`ModelState`、`ActionResult`，但只作用於走進 MVC 的請求。需要 MVC 上下文用 Filter，需要全面覆蓋用 middleware。

**Q：想加一個「記錄每個請求耗時」的 header，但一直說 header 是唯讀的。**
內層已經開始寫 response 了。改用 `Response.OnStarting` 註冊回呼，它在第一個位元組送出前執行，那時 header 還可以改。

**Q：`Map` 和 `UseWhen` 該用哪個？**
要「岔出去自成一個 pipeline、不回主線」用 `Map`（注意它會改寫 `Path` 和 `PathBase`）；要「符合條件的請求多走幾道手續，之後回到主線」用 `UseWhen`。實務上後者更常用。

---

## 連結

- [[basics-03-first-project]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[basics-08-middleware-and-exception-handling]] — 入門篇對應章：先學怎麼做，本章講為什麼
- [[dotnet-web-api]] — 教材總目錄與速查
- [[00-hosting-and-startup]] — 上一章：pipeline 是在哪一刻被組裝的
- [[02-dependency-injection]] — 下一章：scope 與 captive dependency
- [[03-routing-and-endpoints]] — `UseRouting` 選 endpoint 的細節
- [[05-filters-and-mvc-internals]] — Filter 與 middleware 的分工
- [[15-error-handling]] — 例外處理 middleware 的位置與限制
