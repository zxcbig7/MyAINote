---
type: concept
domain: tech
tags: [dotnet, aspnet, web-api, authorization, permission, policy, claims, react, typescript, jwt-decode, token-storage, taskTracker]
sources:
  - raw/Web Framework/NET Web API/chapter 7.3 後端各種權限管理的寫法，搭配前端操作的實務範例.md
  - raw/Web Framework/NET Web API/NET 6 Web API JWT 驗證與授權完整設定與實作指南.md
created: 2026-10-31
updated: 2026-10-31
---

# 入門第 13 章：權限與前端 — 按鈕只是禮貌，403 才是門鎖

## 藏起來的按鈕，擋不住一行 curl

前端同事做完權限功能，很得意地展示：用 Viewer 帳號登入，畫面上「新增任務」按鈕不見了；換成 Editor 帳號，按鈕出現。需求完成。同一天下午，另一位同事打開 PowerShell，拿著 Viewer 的 token，不經過任何畫面直接呼叫 API：

```powershell
'{"title":"Nope"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -H "Authorization: Bearer $viewerToken" -d '@-'
```

```text
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json; charset=utf-8
Date: Sat, 31 Oct 2026 06:21:27 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.4","title":"Forbidden","status":403,"traceId":"00-2f805acbf75e62e75db331c878af7451-56bff6f345b67749-00"}
```

這次被擋下來，是因為後端有檢查。如果後端只寫了 `[Authorize]`（登入就放行），這個請求會直接建立一筆資料：前端藏按鈕，只改變了「誠實的使用者看到什麼」，沒有改變「伺服器肯做什麼」。瀏覽器的 DevTools、`curl.exe`、Postman 都能繞過前端，任何跑在使用者機器上的程式碼，使用者都能改。

所以「前端依權限顯示按鈕」這件事，要同時回答兩個問題：安全由誰負責（後端，而且只有後端），以及前端怎麼知道該顯示哪些按鈕才不會和後端打架。後者如果處理得不好，會出現兩種煩人的症狀：按鈕顯示了但按下去 403，或是明明有權限卻看不到按鈕。[[basics-12-jwt-login]] 讓 TaskTracker 能簽發 token，也讓 `[Authorize(Roles = ...)]` 能運作；本章接手之後的事：把角色升級成權限、讓前端拿到同一份權限清單、統一處理 401 與 403，最後用三種角色實測整張權限矩陣。

---

## 一、三層模型：誰建立身分、誰守門、誰負責體驗

這章的案例來自作者自己做過的 RuleViewer 系統，需求只有三句話：所有人都可以查看規則，只有 Editor 與 Admin 可以編輯，只有 Admin 可以刪除。需求簡單，卻足以暴露一個事實：權限從來不是單點設計，而是一條責任鏈，鏈上有三個環節，每個環節只該做自己的事。

```text
Authentication（你是誰）
        ↓
Authorization（你能不能做）
        ↓
Frontend UI / UX（你看到什麼、能操作什麼）
```

第一個環節是 Authentication，負責建立身分。[[basics-12-jwt-login]] 已經做完這件事：登入成功後簽發 JWT，之後每個請求由 JwtBearer 驗證簽章與有效期，把 token 裡的 claim 變成 `HttpContext.User`。這一層只回答「你是誰」，不擋請求，也不判斷你能不能做某件事。

第二個環節是 Authorization，也就是後端的授權層，負責回答「這個人能不能對這支 API 做這個動作」。它是整條鏈上唯一可信的安全邊界，因為它跑在使用者碰不到的伺服器上。[[basics-11-auth-concepts-and-pipeline]] 講過的 `[Authorize]` 和 `UseAuthorization()` 就屬於這一層。

第三個環節是 Frontend，負責體驗：Viewer 不需要看到一顆按了只會得到 403 的刪除按鈕，唯讀的頁面直接顯示「唯讀模式」比滿畫面錯誤訊息友善得多。這一層只是體驗優化，不負責安全，因為它的任何判斷都可以被繞過。

三層之間靠 JWT 串起來，這也是這章最重要的三句話：JWT 是三層共同使用的語言，後端永遠是最終裁判，前端的所有限制都假設「可能被繞過」。違反其中任何一句，系統就開始失控。第一句被違反，會出現前端看到的權限和後端認定的權限不一致；第二句被違反，就是開頭那個藏按鈕卻沒鎖門的故事；第三句被違反，會有人在前端寫出「反正有隱藏就不用驗」的假設，之後有人加了一支新的 API 卻只靠畫面保護。

接下來的做法就依這個順序：先把後端的授權做紮實，再決定前端用什麼方式拿到同一份權限，最後驗證三層真的對齊。

---

## 二、Role 為什麼不夠：把「能做什麼」變成獨立的詞彙

[[basics-12-jwt-login]] 結束時，TaskTracker 的授權寫法是直接在 action 上標角色：

```csharp
[Authorize(Roles = "Editor,Admin")]
[HttpPost]
public async Task<ActionResult<TaskResponse>> CreateAsync(...)
```

這個寫法對小專案夠用，問題出在系統長大之後。第一個問題是權限被綁在角色名稱上：某天業務說「Viewer 也要能新增任務，但只限新增」，你得到處找哪些 action 標了 `Editor,Admin`，一個個改，而且沒有任何地方能一眼看出「Viewer 現在能做什麼」。第二個問題發生在前端：前端要決定要不要顯示按鈕，只能寫 `role === "Admin"` 這樣的判斷，等於把後端的權限表複製了一份到 React 裡。後端改了規則，前端要同步改，漏改一處就是 bug。

解法是在角色和 action 之間加一層詞彙：permission。角色是「人的分類」（Viewer、Editor、Admin），permission 是「能做的事」（讀任務、寫任務、刪任務）。action 只問「你有沒有這個 permission」，完全不知道角色存在；角色和 permission 的對應關係集中在一個地方。這樣業務改規則時只動那一個對應表，action 和前端都不用跟著改。深度篇 [[14-authorization]] 第五節會把這個模型擴展到資料庫儲存的權限和多租戶，這裡先做到最小可用的版本。

依 RuleViewer 的需求，TaskTracker 的矩陣是：

| 角色   | tasks:read | tasks:write | tasks:delete |
| ------ | ---------- | ----------- | ------------ |
| Viewer | 有         | 無          | 無           |
| Editor | 有         | 有          | 無           |
| Admin  | 有         | 有          | 有           |

permission 字串用 `資源:動作` 的格式（`tasks:read`），好處是前後端都能一眼看懂，也可以按資源分組。格式沒有規定，重點是前後端共用的穩定字串，不要用顯示文字或中文。

---

## 三、後端落地：permission claim 與具名 policy

這一節要改五個地方：定義 permission 常數、集中角色對應、登入時把 permission 寫進 token、註冊 policy、把 Controller 改成檢查 policy。每一步都對應 TaskTracker 專案裡的實際檔案。

第一步，新增 `Authorization/Permissions.cs`，把所有 permission 字串集中成常數。`ClaimType` 是 token 裡 claim 的名字，`All` 在註冊 policy 時會用到：

```csharp
namespace TaskTracker.Api.Authorization;

public static class Permissions
{
    public const string ClaimType = "permission";
    public const string TasksRead = "tasks:read";
    public const string TasksWrite = "tasks:write";
    public const string TasksDelete = "tasks:delete";

    public static IReadOnlyList<string> All { get; } = [TasksRead, TasksWrite, TasksDelete];
}
```

第二步，新增 `Authorization/RolePermissions.cs`，這就是上一節說的「集中的那個地方」。業務要調整某個角色的權限，只改這個 switch：

```csharp
using TaskTracker.Api.Entities;

namespace TaskTracker.Api.Authorization;

public static class RolePermissions
{
    public static IReadOnlyList<string> For(UserRole role)
    {
        return role switch
        {
            UserRole.Viewer => [Permissions.TasksRead],
            UserRole.Editor => [Permissions.TasksRead, Permissions.TasksWrite],
            UserRole.Admin => [Permissions.TasksRead, Permissions.TasksWrite, Permissions.TasksDelete],
            _ => []
        };
    }
}
```

先前的 `RoleNames.cs`（`Viewer`、`Editor`、`Admin`、`EditorOrAdmin` 四個字串常數）已經沒人用，刪除它。`UserRole` enum 仍然保留，因為使用者資料表還是記錄角色。

第三步，修改 `Services/TokenService.cs` 簽發 token 的地方。原本的 claim 是 `sub`、`email`、`jti`、`role` 四個；現在改成先組一個 `List<Claim>`，再把該角色的每個 permission 各加一筆 `permission` claim：

```csharp
var claims = new List<Claim>
{
    new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
    new(JwtRegisteredClaimNames.Email, user.Email),
    new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
    new("role", user.Role.ToString())
};
claims.AddRange(RolePermissions.For(user.Role).Select(permission => new Claim(Permissions.ClaimType, permission)));
var descriptor = new SecurityTokenDescriptor
{
    Subject = new ClaimsIdentity(claims),
    // Issuer、Audience、IssuedAt、Expires、SigningCredentials 與上一章相同
};
```

為什麼 permission 要放進 token，而不是每個請求都查資料庫？因為 JWT 的設計就是自包含：驗證只靠簽章與有效期，不用往返資料庫。代價在第四節會詳細討論，這裡先記住：token 裡的權限是簽發當下的快照。

第四步，註冊 policy。`Extensions/ServiceCollectionExtensions.cs` 裡原本是 `services.AddAuthorization();`，改成：

```csharp
var authorization = services.AddAuthorizationBuilder();
foreach (var permission in Permissions.All)
{
    authorization.AddPolicy(permission, policy => policy.RequireClaim(Permissions.ClaimType, permission));
}
```

這段會為每個 permission 註冊一個名字等於 permission 字串的 policy，內容是「token 裡要有一筆 `permission` claim，值等於這個字串」。`AddAuthorizationBuilder()` 是 .NET 7 加入的流暢寫法。用迴圈註冊的好處是新增 permission 時只要加進 `Permissions.All`，不會漏註冊。

第五步，把 `Controllers/TasksController.cs` 的 attribute 全部換成 policy：

```csharp
[ApiController]
[Authorize(Policy = Permissions.TasksRead)]
[Route("api/tasks")]
public class TasksController : ControllerBase
{
    // GetAllAsync、GetByIdAsync 沿用 class 層級的 tasks:read

    [Authorize(Policy = Permissions.TasksWrite)]
    [HttpPost]
    public async Task<ActionResult<TaskResponse>> CreateAsync(CreateTaskRequest request, CancellationToken ct) { /* 同前 */ }

    [Authorize(Policy = Permissions.TasksWrite)]
    [HttpPut("{id:guid}")]
    public async Task<ActionResult<TaskResponse>> UpdateAsync(Guid id, UpdateTaskRequest request, CancellationToken ct) { /* 同前 */ }

    [Authorize(Policy = Permissions.TasksDelete)]
    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> DeleteAsync(Guid id, CancellationToken ct) { /* 同前 */ }
}
```

這裡有兩個值得停下來想的地方。第一，class 層級和 action 層級的 `[Authorize]` 是累加的（AND）：要新增任務，必須同時有 `tasks:read` 和 `tasks:write`。對 TaskTracker 沒有影響，因為每個有寫入權的角色一定也有讀取權；但設計 permission 時要記得這個語意，否則「只能寫不能讀」的角色會被 class 層級的 policy 擋掉。（逗號分隔的 `Roles = "Editor,Admin"` 則是 OR，疊多個 attribute 才是 AND，深度篇 [[14-authorization]] 有實測。）第二，action 上寫的是常數 `Permissions.TasksWrite`，不是字串字面值，拼錯會在編譯期就發現，而不是等到有人呼叫才爆。

RuleViewer 的原始需求有一句觀念這裡完全成立：權限寫在 API 上，不要藏在程式邏輯裡，Controller 本身就是「權限規格書」。讀一遍 `TasksController` 的 attribute，就知道每支 API 需要什麼權限，不用翻 service 的程式碼。

### 看看簽出來的 token

改完之後重新啟動 API、重新登入（舊 token 沒有 `permission` claim，這就是快照的第一個實例）。以 Admin 登入，解開 JWT 的 payload：

```text
{"aud":"tasktracker-web","iss":"tasktracker-api","exp":1793429476,"iat":1793427676,"nbf":1793427676,"sub":"04c14f22-78da-4b99-b756-470a52851d2d","email":"admin@example.com","jti":"acabeb37-b677-4e62-b982-200e43610e99","role":"Admin","permission":["tasks:read","tasks:write","tasks:delete"]}
```

Viewer 的 payload：

```text
{"aud":"tasktracker-web","iss":"tasktracker-api","exp":1793429473,"iat":1793427673,"nbf":1793427673,"sub":"eff2cf7b-ddb1-4b0f-a6d4-a65c5fd48695","email":"viewer@example.com","jti":"9fa99546-1d54-49a7-9a54-5e5b004274f5","role":"Viewer","permission":"tasks:read"}
```

仔細比較兩者的 `permission`：Admin 是陣列，Viewer 是單純的字串。同樣型別的 claim 只有一筆時，簽發端會序列化成純量，有多筆時才變成陣列。後端不受影響，`FindAll("permission")` 不管哪種形狀都回傳所有值；但如果前端自己解開 token，直接寫 `payload.permission.includes(...)`，Viewer 登入時會變成對字串做子字串比對（`"tasks:read".includes("tasks:r")` 為 `true`），出現難以察覺的誤判。這是下一節 `/auth/me` 存在的理由之一。

---

## 四、`GET /api/auth/me`：不要讓前端自己解讀 token

前端需要知道目前使用者有哪些權限。最直覺的做法是前端自己解 JWT，因為 payload 只是 Base64URL 編碼，任何人都讀得到。許多教學範例用的就是這個做法，這也可行，但有幾個地方要先講清楚。

先看怎麼解。前端常用的套件是 `jwt-decode`，v4 之後只有具名匯出，沒有 default export。舊版教學裡常見的 `import jwtDecode from "jwt-decode"` 在 v4 會直接編譯失敗：

```text
old.ts(1,8): error TS2613: Module '".../jwt-decode/build/esm/index"' has no default export. Did you mean to use 'import { jwtDecode } from "...index"' instead?
```

正確寫法是具名匯出，並且要處理上一節看到的「單值是字串、多值是陣列」：

```ts
import { jwtDecode } from 'jwt-decode';

interface TokenPayload {
  sub: string;
  role: string;
  permission?: string | string[];
}

export function permissionsFromToken(token: string): string[] {
  const payload = jwtDecode<TokenPayload>(token);
  const value = payload.permission;
  if (value === undefined) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}
```

用 Viewer 與 Editor 的 payload 形狀實際跑（`jwt-decode` 4.0.0，Node 24）：

```text
tasks:read
[ 'tasks:read', 'tasks:write' ]
[ 'tasks:read' ]
[ 'tasks:read', 'tasks:write' ]
```

前兩行是 `jwtDecode(...).permission` 的原始值，字串與陣列確實都會出現；後兩行是經過 `permissionsFromToken` 正規化後的結果。

這個做法能用，但有三個結構性的缺點。第一，前端要知道 token 的內部格式：claim 叫什麼名字、單值還是陣列、哪天改成 `scope` 就要跟著改。第二，`jwtDecode` 只解碼不驗證，前端無法知道這個 token 的簽章是否有效、是否被伺服器視為過期；使用者若在 DevTools 改掉前端拿來判斷的 payload 或程式變數，前端會很開心地顯示刪除按鈕；真把改過的 token 送出去，後端驗簽失敗會回 401，不是 403，但畫面已經說謊了。第三，如果將來為了安全把 token 改放 `HttpOnly` cookie，JavaScript 根本讀不到 token，這條路就整個斷了。

因此 TaskTracker 加了一支專門回答「伺服器怎麼看待這個 token 的持有者」的端點。新增 `Dtos/MeResponse.cs`：

```csharp
namespace TaskTracker.Api.Dtos;

public sealed record MeResponse(Guid Id, string Email, string Role, IReadOnlyList<string> Permissions);
```

新增 `Extensions/ClaimsPrincipalExtensions.cs`，把 `ClaimsPrincipal` 轉成 DTO。`MapInboundClaims = false`（[[basics-12-jwt-login]] 已設定）讓 claim 保持 token 裡的名字，所以這裡讀 `sub`、`email`、`role` 就是原名：

```csharp
using System.Security.Claims;
using Microsoft.IdentityModel.JsonWebTokens;
using TaskTracker.Api.Authorization;
using TaskTracker.Api.Dtos;

namespace TaskTracker.Api.Extensions;

public static class ClaimsPrincipalExtensions
{
    public static MeResponse ToMeResponse(this ClaimsPrincipal principal)
    {
        return new MeResponse(
            Guid.Parse(principal.FindFirstValue(JwtRegisteredClaimNames.Sub)!),
            principal.FindFirstValue(JwtRegisteredClaimNames.Email)!,
            principal.FindFirstValue("role")!,
            principal.FindAll(Permissions.ClaimType).Select(claim => claim.Value).ToList());
    }
}
```

最後在 `Controllers/AuthController.cs` 加上端點：

```csharp
[Authorize]
[HttpGet("me")]
public ActionResult<MeResponse> Me()
{
    return Ok(User.ToMeResponse());
}
```

沒帶 token 時回 401，三種角色各自回自己的身分與權限（不論 token 裡是字串還是陣列，這裡一律是陣列）：

```powershell
curl.exe -s -i http://localhost:5080/api/auth/me
```

```text
HTTP/1.1 401 Unauthorized
Content-Type: application/problem+json; charset=utf-8
Date: Sat, 31 Oct 2026 06:21:19 GMT
Server: Kestrel
Transfer-Encoding: chunked
WWW-Authenticate: Bearer

{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.2","title":"Unauthorized","status":401,"traceId":"00-f97e9a74eea18fa99693984ba4ef1758-71b3eb26eef4b430-00"}
```

```powershell
curl.exe -s -i http://localhost:5080/api/auth/me -H "Authorization: Bearer $viewerToken"
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 06:21:19 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"id":"eff2cf7b-ddb1-4b0f-a6d4-a65c5fd48695","email":"viewer@example.com","role":"Viewer","permissions":["tasks:read"]}
```

Editor 與 Admin 的回應同樣格式：

```text
{"id":"34f87a5b-b03a-42d5-ad8a-c8ec7aa76f4d","email":"editor@example.com","role":"Editor","permissions":["tasks:read","tasks:write"]}
{"id":"04c14f22-78da-4b99-b756-470a52851d2d","email":"admin@example.com","role":"Admin","permissions":["tasks:read","tasks:write","tasks:delete"]}
```

### 解 token 和問伺服器，差別在哪裡

兩條路的差別可以整理成三點。解 token 不需要網路往返，但資訊來自前端自己的解讀，沒有人替它驗證過簽章與有效期；問 `/auth/me` 要多一次請求，但回來的資料是伺服器驗證通過之後給的，格式也由後端 DTO 固定，前端不必理解 JWT。至於「新鮮度」，要誠實說：TaskTracker 的 `/auth/me` 是從已驗證 token 的 claim 讀出來的，沒有查資料庫，所以它和解 token 看到的是同一份快照，只是由伺服器背書。

快照問題是這個設計繞不開的限制。管理員把某個 Editor 降成 Viewer，資料庫立刻更新；但那位使用者手上的 token 還寫著 `tasks:write`，直到 token 過期（TaskTracker 預設 30 分鐘，登入回應裡的 `expiresIn` 是 `1799` 秒）或重新登入。這段時間內後端仍然依 token 放行。反過來，剛被加權限的使用者要重新取得 token 才看得到新按鈕。

怎麼處理，取決於你能接受多長的時間差。常見做法有三種：縮短 access token 的有效期並搭配 refresh token，每次刷新時重新讀取最新權限；在敏感操作（刪除、金流）的 handler 裡額外查一次資料庫確認；或者接受「最多慢 30 分鐘生效」並在需求文件寫清楚。深度篇 [[12-jwt-deep-dive]] 第六節整理了撤銷的四種策略與取捨，需要即時生效時請從那裡選。不論選哪種，前端都要處理一個必然的情況：畫面依舊的快照顯示了按鈕，但伺服器已經不認，這時會收到 403，而不是壞掉的畫面，這是下面第六節要統一處理的。

結論很短：UI 判斷用 `/auth/me`，不要自己解 token；登入後 token 只要原封不動送給後端，由前端程式碼保管，而不是解讀。

---

## 五、前端：型別、Context 與 `Can` 元件

有了 `/auth/me`，前端的工作變成三件事：用型別描述權限、把目前使用者放進 React 的 Context、提供一個元件讓畫面用宣告的方式表達「有這個權限才顯示」。這一節的程式碼放在 TaskTracker 旁邊的 `frontend-snippets` 資料夾，只做型別檢查，不需要啟動 React。設定如下，`package.json`：

```json
{
  "name": "tasktracker-frontend-snippets",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@types/react": "19.3.0",
    "typescript": "7.0.2"
  }
}
```

`tsconfig.json`：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "noUncheckedIndexedAccess": true
  },
  "include": ["src"]
}
```

放好這兩個檔後執行 `npm install`，之後用 `npm run typecheck` 檢查。`src` 底下放下面五個檔案。前面的 `permissionsFromToken` 不在這份專案裡，要試的話另外 `npm install jwt-decode@4.0.0`。第一個是 `types.ts`，把後端的 API 形狀用 TypeScript 描述。關鍵是 `Permission` 型別，它列出後端所有合法的 permission 字串：

```ts
export type Permission = 'tasks:read' | 'tasks:write' | 'tasks:delete';

export type Role = 'Viewer' | 'Editor' | 'Admin';

export interface Me {
  id: string;
  email: string;
  role: Role;
  permissions: Permission[];
}

export interface Task {
  id: string;
  title: string;
  status: 'todo' | 'done';
  createdAt: string;
}

export interface Paged<T> {
  items: T[];
  page: number;
  pageSize: number;
  totalCount: number;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
}

export interface ProblemDetails {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  errors?: Record<string, string[]>;
  traceId?: string;
}
```

第二個是 `auth.tsx`。常見的 `Can` 元件範例讀的是一個全域的 `permissions` 變數、沒有型別，`children` 也沒宣告。這樣寫的問題是：全域變數變了，React 不知道要重新渲染（登出再用別的帳號登入，畫面可能還停在上一個人的按鈕）；拼錯字串也沒人提醒。改用 Context 之後，permissions 是狀態的一部分，登入登出時 `AuthProvider` 的 `me` 一換，所有 `Can` 自動重新判斷：

```tsx
import { createContext, useContext, type ReactNode } from 'react';
import type { Me, Permission } from './types';

const AuthContext = createContext<Me | null>(null);

export function AuthProvider({ me, children }: { me: Me | null; children: ReactNode }) {
  return <AuthContext.Provider value={me}>{children}</AuthContext.Provider>;
}

export function useCan(permission: Permission): boolean {
  const me = useContext(AuthContext);
  return me?.permissions.includes(permission) ?? false;
}

interface CanProps {
  permission: Permission;
  children: ReactNode;
  fallback?: ReactNode;
}

export function Can({ permission, children, fallback = null }: CanProps) {
  return useCan(permission) ? <>{children}</> : <>{fallback}</>;
}
```

幾個設計選擇值得說明。`useCan` 在「還沒登入」（`me` 為 `null`）時回 `false`，預設拒絕比預設允許安全，也避免登入前閃現不該出現的按鈕。`useCan` 另外匯出，是因為有些地方不是顯示或隱藏元件，而是要決定 `disabled` 或改變行為，這時直接用 hook 比包元件自然；`Can` 本身只是 `useCan` 的薄包裝。`fallback` 讓「無權限時顯示替代內容」不必再寫第二個條件。最後，`Permission` 是 union 型別，所以拼錯字串在編譯期就被擋住：

```tsx
export const Bad = () => <Can permission="tasks:admin">x</Can>;
```

```text
src/_bad.tsx(3,31): error TS2322: Type '"tasks:admin"' is not assignable to type 'Permission'.
```

正常的檔案執行 `npx tsc --noEmit` 沒有任何輸出，結束碼為 0。要小心的是，這個 union 是前端手寫的，和後端的 `Permissions` 常數是兩份獨立的清單。後端新增 permission 卻忘了更新前端型別，編譯不會報錯，只是新權限在前端永遠被當成沒有。這個缺口可以靠 [[basics-14-openapi-and-versioning]] 的 OpenAPI 文件產生型別來補，目前先靠第九節的檢查清單約束。

第三個檔案是 `example.tsx` 的使用示範。刪除按鈕只有 `tasks:delete` 的人看得到，新增按鈕沒有權限時顯示「唯讀模式」：

```tsx
export function TaskRow({ task, onDelete }: { task: Task; onDelete: (id: string) => void }) {
  return (
    <li>
      {task.title}
      <Can permission="tasks:delete">
        <button onClick={() => onDelete(task.id)}>刪除</button>
      </Can>
    </li>
  );
}

export function App({ me }: { me: Me | null }) {
  return (
    <AuthProvider me={me}>
      <Can permission="tasks:write" fallback={<p>唯讀模式</p>}>
        <button>新增任務</button>
      </Can>
    </AuthProvider>
  );
}
```

這種寫法的價值在於，畫面只出現 permission，不出現角色。比較壞的寫法是 `{me.role === 'Admin' && <button>刪除</button>}`：它把「Admin 才能刪除」這個後端規則複製進了畫面。當後端決定 Editor 也可以刪自己建立的任務時，所有寫了 `role === 'Admin'` 的地方都要找出來改；用 `Can permission="tasks:delete"` 的地方，只要後端的 `RolePermissions` 改了，前端自動跟著變。

---

## 六、統一處理 401 與 403：fetch 包裝層

畫面上的按鈕對齊之後，還要處理執行時的錯誤。許多教學對這件事只有一句「統一處理 401 / 403」。這一句背後的重點是：401 和 403 的處理方式完全不同，把它們混在一起會製造出難以診斷的迴圈。

401 表示後端不認得你是誰：token 缺少、過期、簽章不對。補救方式是重新取得身分，也就是導向登入頁。403 表示後端認得你，只是你沒有這個權限。這時再導去登入頁，使用者登入後仍然沒有權限，再被擋一次，再導去登入頁，永遠繞不出來。403 該做的是顯示「沒有權限」的訊息，保持登入狀態。

在 `src` 放下面的 `api-client.ts`。它把每個請求都經過同一個 `request` 函式，統一加上 `Authorization` 標頭，並依狀態碼分流：

```ts
import type { ProblemDetails } from './types';

export class ApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetails | null;

  constructor(status: number, problem: ProblemDetails | null) {
    super(problem?.detail ?? problem?.title ?? `HTTP ${status}`);
    this.status = status;
    this.problem = problem;
  }
}

export interface ApiClientOptions {
  baseUrl: string;
  getToken: () => string | null;
  onUnauthorized: () => void;
  onForbidden?: (problem: ProblemDetails | null) => void;
}

export function createApiClient(options: ApiClientOptions) {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    const token = options.getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    if (init.body !== undefined && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${options.baseUrl}${path}`, { ...init, headers });
    if (response.ok) {
      return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
    }

    const problem = (await response.json().catch(() => null)) as ProblemDetails | null;
    if (response.status === 401) {
      options.onUnauthorized();
    } else if (response.status === 403) {
      options.onForbidden?.(problem);
    }
    throw new ApiError(response.status, problem);
  }

  return {
    get: <T>(path: string) => request<T>(path),
    post: <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: (path: string) => request<void>(path, { method: 'DELETE' })
  };
}
```

有幾個細節決定了這個包裝層好不好用。錯誤回應被解析成 `ProblemDetails`，這是 [[basics-08-middleware-and-exception-handling]] 設定的統一錯誤格式（前面 403 的回應就是 `application/problem+json`），裡面的 `traceId` 讓使用者回報問題時能附上，後端查 log 時可以直接對上。`ApiError` 保留 `status` 與 `problem`，呼叫端可以在 `catch` 裡針對 400 的欄位錯誤做表單提示，而 401、403 已經由攔截層處理過。`204 No Content`（刪除成功）沒有 body，要特別跳過 `response.json()`，否則會丟出解析錯誤。

401 的處理有兩個陷阱。第一，登入失敗也是 401（TaskTracker 的帳密錯誤回 401），所以 `onUnauthorized` 會在登入頁被呼叫；它不能無條件導向登入頁，否則登入頁會一直重新載入。第二，畫面一次載入多個資源時，多個請求同時 401，`onUnauthorized` 會被呼叫多次；它必須是冪等的，例如只清除 token 並設定一次「需要登入」的狀態，而不是每次都執行導頁。

把它接起來的方式在 `example.tsx`。`token-store.ts` 是一個模組內的變數，等一下會說明為什麼不放 `localStorage`：

```ts
let accessToken: string | null = null;

export const tokenStore = {
  get: (): string | null => accessToken,
  set: (token: string | null): void => {
    accessToken = token;
  }
};
```

```ts
export const api = createApiClient({
  baseUrl: 'http://localhost:5080/api',
  getToken: tokenStore.get,
  onUnauthorized: () => {
    tokenStore.set(null);
  },
  onForbidden: problem => {
    console.warn('沒有權限', problem?.traceId);
  }
});

export async function login(email: string, password: string): Promise<Me> {
  const { accessToken } = await api.post<LoginResponse>('/auth/login', { email, password });
  tokenStore.set(accessToken);
  return api.get<Me>('/auth/me');
}

export function loadTasks(): Promise<Paged<Task>> {
  return api.get<Paged<Task>>('/tasks?page=1&pageSize=20');
}
```

`login` 的流程把前面各節串在一起：先 POST 登入拿到 token，存進 `tokenStore`，再立刻呼叫 `/auth/me` 取得這位使用者的權限，把回傳的 `Me` 交給 `AuthProvider`。真實專案裡，`console.warn` 要換成 toast 或提示頁，`onUnauthorized` 除了清 token 還要把應用程式狀態切到「未登入」。

如果有 refresh token 機制，401 的處理會多一步：先嘗試用 refresh token 換新的 access token，成功就重送原本的請求，失敗才導向登入。TaskTracker 目前沒有實作 refresh，完整的流程與撤銷取捨請看 [[12-jwt-deep-dive]]。

這一層寫完之後，所有「未登入」和「沒權限」的處理都集中在一處，畫面元件不用各自 `try/catch` 去判斷狀態碼，也就不會有人漏掉。

---

## 七、實測：三種角色打整張權限矩陣

三層都寫好了，現在驗證後端真的守住了門。做法是登入三個種子帳號（[[basics-12-jwt-login]] 建立的 `viewer@example.com`、`editor@example.com`、`admin@example.com`），拿到各自的 token，加上不帶 token 的匿名身分，一共四種身分，對任務的五個操作（列出、讀取單筆、新增、更新、刪除）各打一次，與預期對照。

先登入取得 token。`$password` 是種子帳號的密碼，來自 [[basics-12-jwt-login]] 設定的 User Secrets：

```powershell
@{ email = 'viewer@example.com'; password = $password } | ConvertTo-Json -Compress | curl.exe -s -i -X POST http://localhost:5080/api/auth/login -H "Content-Type: application/json" -d '@-'
```

回應是 `200 OK` 加上 `accessToken`（內容見前面第三節的 payload 解碼）。把三個帳號的 token 分別存進 `$viewerToken`、`$editorToken`、`$adminToken`，再用 Admin 先建立一筆測試用任務，把它的 id 存進 `$newId`：

```powershell
'{"title":"Matrix fixture"}' | curl.exe -s -i -X POST http://localhost:5080/api/tasks -H "Content-Type: application/json" -H "Authorization: Bearer $adminToken" -d '@-'
```

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 06:21:22 GMT
Server: Kestrel
Location: http://localhost:5080/api/tasks/41fd5603-4e52-4045-a931-8fa074aed4b4
Transfer-Encoding: chunked

{"id":"41fd5603-4e52-4045-a931-8fa074aed4b4","title":"Matrix fixture","status":"todo","createdAt":"2026-10-31T06:21:22.4854894+00:00"}
```

接著用一段 PowerShell 逐格比對。`Get-Status` 只回傳 HTTP 狀態碼；`$matrix` 是事先寫下的預期（這份預期才是「規格」，不是依實際結果倒推）；每一格印出 `actual`、`expected` 與是否相符：

```powershell
function Get-Status([string]$method, [string]$path, [string]$token, [string]$body) {
    $arguments = @('-s', '-o', 'NUL', '-w', '%{http_code}', '-X', $method, "http://localhost:5080$path")
    if ($token) { $arguments += @('-H', "Authorization: Bearer $token") }
    if ($body) {
        $arguments += @('-H', 'Content-Type: application/json', '-d', '@-')
        $body | curl.exe @arguments
    } else {
        curl.exe @arguments
    }
}
$tokens = @{ anonymous = ''; viewer = $viewerToken; editor = $editorToken; admin = $adminToken }
$matrix = @(
    @{ Role = 'anonymous'; List = 401; Get = 401; Create = 401; Update = 401; Delete = 401 },
    @{ Role = 'viewer'; List = 200; Get = 200; Create = 403; Update = 403; Delete = 403 },
    @{ Role = 'editor'; List = 200; Get = 200; Create = 201; Update = 200; Delete = 403 },
    @{ Role = 'admin'; List = 200; Get = 200; Create = 201; Update = 200; Delete = 204 }
)
$mismatches = 0
foreach ($row in $matrix) {
    $token = $tokens[$row.Role]
    $actual = [ordered]@{
        List = Get-Status 'GET' '/api/tasks' $token $null
        Get = Get-Status 'GET' "/api/tasks/$newId" $token $null
        Create = Get-Status 'POST' '/api/tasks' $token ('{"title":"matrix-' + $row.Role + '"}')
        Update = Get-Status 'PUT' "/api/tasks/$newId" $token ('{"title":"matrix-update-' + $row.Role + '","status":"done"}')
        Delete = Get-Status 'DELETE' "/api/tasks/$newId" $token $null
    }
    foreach ($operation in $actual.Keys) {
        $expected = $row[$operation]
        $verdict = 'OK'
        if ([int]$actual[$operation] -ne $expected) { $verdict = 'MISMATCH'; $mismatches++ }
        "$($row.Role) $operation actual=$($actual[$operation]) expected=$expected $verdict"
    }
}
"不符的格數：$mismatches"
```

實測輸出：

```text
anonymous List actual=401 expected=401 OK
anonymous Get actual=401 expected=401 OK
anonymous Create actual=401 expected=401 OK
anonymous Update actual=401 expected=401 OK
anonymous Delete actual=401 expected=401 OK
viewer List actual=200 expected=200 OK
viewer Get actual=200 expected=200 OK
viewer Create actual=403 expected=403 OK
viewer Update actual=403 expected=403 OK
viewer Delete actual=403 expected=403 OK
editor List actual=200 expected=200 OK
editor Get actual=200 expected=200 OK
editor Create actual=201 expected=201 OK
editor Update actual=200 expected=200 OK
editor Delete actual=403 expected=403 OK
admin List actual=200 expected=200 OK
admin Get actual=200 expected=200 OK
admin Create actual=201 expected=201 OK
admin Update actual=200 expected=200 OK
admin Delete actual=204 expected=204 OK
不符的格數：0
```

二十格全部符合。這張表有幾個值得細看的地方。匿名的五格全是 401，Viewer 的寫入類操作全是 403：同樣是「被拒絕」，狀態碼不同，因為一個是不知道你是誰，一個是知道你是誰但不允許。這正是上一節攔截層要分開處理的原因，後端早就把兩種情況分得清清楚楚。Editor 的 Delete 是 403，Admin 的 Delete 是 204，剛好對應 RuleViewer 的需求「只有 Admin 可以刪除」。

驗證的最後一步，確認矩陣只留下合理的副作用，也就是被允許的建立動作確實留下了資料，被擋下的沒有：

```powershell
curl.exe -s -i http://localhost:5080/api/tasks -H "Authorization: Bearer $adminToken"
```

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Sat, 31 Oct 2026 06:21:28 GMT
Server: Kestrel
Transfer-Encoding: chunked

{"items":[{"id":"703193d4-7d39-46f4-b4ac-f1afbab1830b","title":"matrix-editor","status":"todo","createdAt":"2026-10-31T06:21:26.0073573+00:00"},{"id":"68eaeaf4-cb0d-4328-b32c-a4367ca0d0db","title":"matrix-admin","status":"todo","createdAt":"2026-10-31T06:21:27.0483709+00:00"}],"page":1,"pageSize":20,"totalCount":2}
```

清單裡只有 `matrix-editor` 和 `matrix-admin`：Editor 與 Admin 的新增成功、Viewer 的新增被擋下沒有留下 `matrix-viewer`，而最初的 `Matrix fixture` 已被 Admin 刪掉。「只看狀態碼」不夠，要確認被拒絕的請求真的沒有改動資料，這才是授權的目的。

這份矩陣腳本值得留下來。每次新增 API 或調整 `RolePermissions` 就重跑一遍，是最便宜的授權回歸測試。[[basics-15-testing]] 會把它改寫成自動化的整合測試。

---

## 八、Token 放在哪裡：localStorage 還是 cookie

`tokenStore` 為什麼只是一個模組變數，而不是常見教學裡的 `localStorage.setItem("access_token", ...)`？因為這是一個有明確風險取捨的決定。

先看威脅。JavaScript 能讀的地方，被注入的惡意 JavaScript 也能讀。這種攻擊叫 XSS（Cross-Site Scripting）：網站某處沒有妥善處理使用者輸入，或某個第三方套件被植入惡意程式，攻擊者的腳本就在你的網頁裡執行，`localStorage.getItem(...)` 一行就把 token 讀走送到自己的伺服器。token 一旦外洩，攻擊者可以在別的機器上冒用，直到它過期。

`HttpOnly` cookie 是另一條路：瀏覽器保存、自動附加在請求上，JavaScript 完全讀不到，XSS 偷不走。但 cookie 會被瀏覽器自動帶出去，換來另一種威脅：CSRF（Cross-Site Request Forgery）。攻擊者的網站讓使用者的瀏覽器對你的 API 發請求，cookie 也會跟著送出。要靠 `SameSite` 屬性和 anti-forgery token 防護。而用 `Authorization` 標頭手動附加 token（TaskTracker 的做法）不會被其他網站觸發，所以對 CSRF 免疫。

四種存放位置的差異，深度篇 [[12-jwt-deep-dive]] 第七節有完整表格。這裡直接給判準：

- 如果 token 是長效憑證（有效期數小時以上，或可以換新 token），不要放在 `localStorage` 或 `sessionStorage`。XSS 只要發生一次，攻擊者就拿到有效期這麼長的通行證。
- 如果 access token 的有效期在 15 到 30 分鐘內，放在 JavaScript 記憶體（TaskTracker 的做法）是最低成本的折衷：重新整理頁面後 token 消失，需要重新取得；XSS 無法把 token 帶走留作日後使用，但在頁面還活著的期間，惡意腳本仍然可以用使用者的身分發請求，所以記憶體保存是縮小損害範圍，不是消除 XSS。
- 需要「重新整理頁面不用重新登入」，就加 refresh token，放在 `HttpOnly`、`Secure`、`SameSite=Strict`（或 `Lax`）的 cookie，前端載入頁面時呼叫 refresh 端點換回 access token。這個 refresh 端點需要 CSRF 防護，而且前端與 API 必須是同站（same-site），跨站的 cookie 會被 `SameSite` 擋掉。跨站與第三方 cookie 的細節見 [[13-oauth-oidc]] 的 `SameSite` 段落。
- 只有在內部工具、使用者可信、token 有效期很短、而且團隊明確接受 XSS 風險並寫進文件時，`localStorage` 才說得過去。「我們沒有 XSS」不構成理由，因為這是無法證明的聲明，npm 套件的供應鏈就是常見入口。

TaskTracker 現階段選擇「access token 放記憶體」。它已經足以示範三層對齊，而且不引入 refresh 的複雜度。真正要上線的專案，建議的目標形態是 refresh token 放 `HttpOnly` cookie、access token 放記憶體。

---

## 九、新增一項權限時，要動哪些地方

三層對齊最容易崩壞的時刻是「加新功能」。假設要新增「匯出任務」功能，需要 `tasks:export` 這個權限，只有 Admin 可用。依序做這幾件事：

1. 在 `Permissions.cs` 加常數 `TasksExport`，並放進 `All`（policy 因此自動註冊）。
2. 在 `RolePermissions.cs` 把它加到 Admin 的清單。
3. 新的 action 標上 `[Authorize(Policy = Permissions.TasksExport)]`。
4. 在前端 `types.ts` 的 `Permission` union 加上 `'tasks:export'`。
5. 畫面用 `<Can permission="tasks:export">` 包住匯出按鈕。
6. 權限矩陣腳本加一欄 Export，預期 Viewer、Editor 是 403，Admin 是 200。

第 1 到 3 步是後端，第 4 到 5 步是前端，第 6 步是驗收。做對了，後端一定擋得住；漏了第 4 步，按鈕不會出現（安全的方向出錯）；漏了第 3 步才是危險的，action 上沒有權限檢查，只剩前端按鈕保護，這時第 6 步的矩陣腳本會把它抓出來。

---

## 常見誤解

**「前端已經隱藏按鈕了，所以這個操作很安全。」** 隱藏按鈕改變的是畫面，伺服器收到的仍然是任何人能構造的 HTTP 請求。安全的檢查只能在後端：每支需要權限的 API 都要有 `[Authorize]` 或 policy，前端的 `Can` 只負責不讓使用者看到注定失敗的選項。

**「解開 JWT 就能知道使用者有什麼權限，所以前端不需要呼叫 `/auth/me`。」** 解 token 可以拿到簽發當下寫進去的內容，但前端沒有驗證簽章，單值 claim 與多值 claim 的 JSON 形狀還不一樣（字串與陣列）。用 `/auth/me` 取得由後端整理過的結果，前端不依賴 token 的內部格式，將來 token 改成 `HttpOnly` cookie 也不會壞。

**「403 和 401 都是沒權限，統一導去登入頁就好。」** 401 是不知道你是誰，重新登入有機會解決；403 是知道你是誰但不允許，重新登入不會改變結果，還會造成登入、被擋、再導向登入的迴圈。要分開處理。

**「改了使用者的角色，他下一個請求就會生效。」** 權限寫在 token 裡，是簽發當下的快照。已簽發的 token 在過期前仍然帶著舊權限，TaskTracker 的預設有效期是 30 分鐘。需要更即時的生效，要縮短有效期、搭配 refresh，或在敏感操作多查一次資料庫。

**「`import jwtDecode from 'jwt-decode'` 是標準寫法。」** 那是 v3 時代的寫法。v4 只有具名匯出，要寫 `import { jwtDecode } from 'jwt-decode'`，否則 TypeScript 會報 TS2613。

---

## 同事會來問你的問題

**Q：為什麼 permission 要放進 token，而不是每次請求都查資料庫？**
放進 token 是 JWT 的核心取捨：驗證只靠簽章，不需要每個請求都連資料庫，換來水平擴展容易、延遲低。代價是權限變更有延遲。如果你的系統無法接受這個延遲（例如停權必須立即生效），再考慮每次查詢、短效 token 加 refresh，或黑名單，細節在 [[12-jwt-deep-dive]]。

**Q：Role 還需要嗎？既然改用 permission 了。**
需要。Role 仍是「人的分類」，用來決定誰預設擁有哪些 permission、在管理畫面顯示使用者身分、做報表。只是程式碼檢查授權時問的是 permission，不問 role。TaskTracker 的 token 同時帶 `role` 與 `permission`，前者給人看，後者給程式判斷。

**Q：前端的 `Permission` 型別和後端的常數是兩份，不會不同步嗎？**
會有這個風險，所以後端是唯一的來源，前端的 union 要跟著後端改，並用權限矩陣腳本驗收。比較進階的做法是讓後端的 OpenAPI 文件包含 permission 清單，前端從文件產生型別，這在 [[basics-14-openapi-and-versioning]] 之後可以接上。

**Q：我可以在 `Can` 裡直接呼叫 API 確認權限嗎？**
不建議。`Can` 會在每次渲染時執行，頻繁呼叫 API 會拖慢畫面。權限在登入後取得一次，放進 Context，`Can` 只讀 Context。真正要確認的時候（例如按下刪除），後端本來就會檢查，不需要前端再問一遍。

**Q：token 放記憶體，重新整理頁面就登出了，使用者會抱怨怎麼辦？**
這是「安全」與「便利」之間的取捨。要保留登入狀態，就實作 refresh token（放 `HttpOnly` cookie），讓頁面載入時自動換回 access token。不要用「改放 `localStorage`」解決，那等於放棄對 XSS 的防線。

---

## 這章的位置

學完這一章，你能把一份權限需求拆成三層，各做各的事：後端用 permission claim 與 policy 守門，前端用 `/auth/me`、`Can` 與統一的 401／403 處理提供一致的體驗，並且能用一張矩陣實測證明三層對齊。同時你也能說出為什麼 token 放記憶體而不是 `localStorage`，以及權限異動為什麼不會立刻生效。想看機制：授權模型（Requirement、Handler、資源式授權）見 [[14-authorization]]，JWT 的撤銷與前端存放的完整取捨見 [[12-jwt-deep-dive]]，用 Google 等外部身分提供者登入的流程見 [[13-oauth-oidc]]。

接下來 [[basics-14-openapi-and-versioning]] 處理另一個前後端對齊問題：前端同事怎麼知道這支 API 怎麼呼叫，API 改版時又如何不弄壞他們的程式。

---

## 連結

- 上一章：[[basics-12-jwt-login]]
- 下一章：[[basics-14-openapi-and-versioning]]
- 對應深度章：[[14-authorization]]、[[12-jwt-deep-dive]]、[[13-oauth-oidc]]
- 本章用到的先修內容：[[basics-11-auth-concepts-and-pipeline]]、[[basics-08-middleware-and-exception-handling]]
- 總目錄：[[dotnet-web-api]]
