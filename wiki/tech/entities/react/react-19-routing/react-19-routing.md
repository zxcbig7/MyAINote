---
type: concept
domain: tech
tags: [react, react-router, routing, history-api, spa-fallback, nested-routes, search-params, lazy, typescript]
sources:
  - raw/Web Framework/React/AuthProvider & Route 概念.md
  - raw/Web Framework/React/React 生態系資源.md
created: 2026-10-30
updated: 2026-11-01
---

# 第 19 章：路由 — 只有一個 HTML，網址怎麼會變

## 本機好好的，貼給同事就 404

第 18 章做完 `UsersPage` 之後，Task Tracker 有了兩個畫面。你用最省事的方法切換：

```tsx
const [page, setPage] = useState<'tasks' | 'users'>('tasks');
```

很快就有人回報：在使用者頁按重新整理，會跳回任務頁；按瀏覽器的上一頁，直接離開整個網站；篩選出已完成的任務想傳給同事看，傳過去的網址打開是全部任務。

你裝了 React Router，上述問題在本機全部消失。部署之後，你把 `https://tracker.example.com/tasks/42` 貼到團隊頻道，同事點開看到的是 nginx 的 404。奇怪的是，從首頁一路點進同一筆任務完全正常，網址列顯示的字串也一模一樣。

同一個網址，點進去可以，直接開不行。本章要回答：只有一個 HTML，網址怎麼會變？答案會帶出伺服器為什麼要 fallback、巢狀路由如何保住 layout，以及哪些 state 應該搬進網址。

## 網址替使用者做了三件事

先回想你熟悉的傳統網站，例如 ASP.NET Core MVC 的 Razor 頁面。點一個連結，瀏覽器對新網址發出請求，伺服器回傳一份新的 HTML，瀏覽器丟掉舊頁面的 DOM 和 JavaScript 狀態，從頭建立新頁面。

SPA 把這條路砍掉了。整個應用只有一份 `index.html` 和幾個 JavaScript 檔，畫面都由 React 在瀏覽器裡產生。這帶來流暢的換頁，也帶走了網址原本免費提供的三個功能：重新整理後回到同一個地方、上一頁下一頁可以走、把位置傳給別人。開場的 `useState<'tasks' | 'users'>` 三個都做不到，因為 state 只活在這個分頁的記憶體裡，瀏覽器的網址和歷史紀錄完全不知道它存在。

我們要的是：改變網址和歷史紀錄，但不讓瀏覽器真的載入新頁面。

## History API：改網址而不發請求

瀏覽器提供的就是 `history.pushState`。它在分頁的歷史紀錄疊上一筆新項目，並把網址列改掉，不發任何網路請求，也不觸發換頁。

```ts
window.history.pushState(null, '', '/tasks/42');
window.location.pathname; // '/tasks/42'
```

它只能改同一個 origin 底下的網址，否則瀏覽器會丟 `SecurityError`；不然任何網頁都能把網址列改成銀行的網域。

搭配的另一半是 `popstate` 事件：使用者按上一頁或下一頁時，瀏覽器改回舊網址並觸發它。這裡有個不對稱的地方要記住，`pushState` 本身不會觸發 `popstate`。也就是說，瀏覽器只會在使用者動歷史紀錄時通知你，你自己改的網址要自己通知畫面。

有了這兩個零件，一個能動的 router 不到 50 行。第 15 章的 `useSyncExternalStore` 正好適合這裡，因為網址就是 React 外部的 store：

```tsx
import { useSyncExternalStore } from 'react';

const subscribe = (onChange: () => void): (() => void) => {
  window.addEventListener('popstate', onChange);
  return () => window.removeEventListener('popstate', onChange);
};

export const usePathname = (): string => useSyncExternalStore(subscribe, () => window.location.pathname);

export const navigateTo = (to: string): void => {
  window.history.pushState(null, '', to);
  // pushState 不會觸發 popstate，訂閱者要自己通知。
  window.dispatchEvent(new PopStateEvent('popstate'));
};

interface MiniLinkProps {
  to: string;
  children: React.ReactNode;
}

export const MiniLink = ({ to, children }: MiniLinkProps): React.JSX.Element => (
  <a
    href={to}
    onClick={(event) => {
      if (event.ctrlKey || event.metaKey || event.shiftKey) return;
      event.preventDefault();
      navigateTo(to);
    }}
  >
    {children}
  </a>
);

export const MiniApp = (): React.JSX.Element => {
  const pathname = usePathname();
  return (
    <>
      <nav>
        <MiniLink to="/tasks">任務</MiniLink>
        <MiniLink to="/users">使用者</MiniLink>
      </nav>
      {pathname === '/tasks' && <h1>任務清單</h1>}
      {pathname === '/users' && <h1>使用者清單</h1>}
    </>
  );
};
```

點「使用者」時，`preventDefault` 擋下瀏覽器的換頁，`pushState` 改網址，手動發出的事件讓 `usePathname` 讀到新值，React 重新 render。按上一頁時，瀏覽器自己發出 `popstate`，走同一條訂閱路徑。

留意 `MiniLink` 回傳的是真正的 `<a href>`，而且按住 Ctrl 時直接放行。改用 `<button onClick>` 的話，新分頁開啟、右鍵複製連結、螢幕閱讀器的連結清單全都消失。React Router 的 `Link` 也是這樣做的：它 render 出帶 `href` 的 `<a>`，一般點擊才攔下，Ctrl 點擊交還給瀏覽器。

## 為什麼伺服器要 fallback

現在可以解開開場的謎題了。同一個網址其實有兩條完全不同的進入路徑：

```text
從首頁點進去
  瀏覽器已經載入 index.html 和 JS
  點擊 → pushState('/tasks/42') → React 換畫面
  伺服器從頭到尾沒收到 /tasks/42 這個請求

直接開網址（貼連結、重新整理）
  瀏覽器 GET /tasks/42
  伺服器找 /tasks/42 這個檔案 → 沒有 → 404
  index.html 根本沒載入，React 沒有機會開始
```

只有 JavaScript 載入之後，`/tasks/42` 才有意義，而第二條路徑卡在 JavaScript 載入之前。修法是讓伺服器對「找不到檔案的路徑」一律回 `index.html`，React 啟動後讀 `window.location` 自己決定要顯示什麼。這就是 SPA fallback。

本機沒出事，是因為 Vite dev server 預設的 `appType: 'spa'` 內建這個行為。把它改成 `'mpa'`，同一個 `/tasks/42` 就回 404，正好重現上線的狀況。

nginx 的寫法是一行 `try_files $uri /index.html;`，完整設定在第 29 章。

如果由 ASP.NET Core 直接託管前端，對應的是 `MapFallbackToFile`，這裡有一個後端讀者特別容易踩的坑：

```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.UseStaticFiles();
app.MapGet("/api/tasks/{id:guid}", (Guid id) => Results.Ok("by-guid"));
app.MapGet("/api/tasks/export", () => Results.Ok("export"));
// 少了這行，打錯的 API 路徑會拿到 200 與 index.html。
app.MapFallback("/api/{**rest}", () => Results.NotFound());
app.MapFallbackToFile("index.html");
app.Run();
```

拿掉中間那行 `MapFallback` 再打幾個路徑，結果如下：

| 請求 | 只有 MapFallbackToFile | 加上 /api 的 fallback |
| --- | --- | --- |
| `/tasks/42` | 200，HTML | 200，HTML |
| `/api/nope` | 200，HTML | 404 |
| `/api/tasks/abc`（不符合 guid 限制） | 200，HTML | 404 |
| `/assets/missing.js` | 404 | 404 |

第二列是壞在哪裡：前端打錯 API 路徑時，收到的是 200 和一份 HTML，`response.ok` 是 true，接著 `response.json()` 丟出 `Unexpected token '<'`，你會去懷疑後端序列化，而真正的問題是路徑打錯。最後一列則是預設行為幫你守住的：`MapFallbackToFile` 不比對帶副檔名的路徑，少一個 JS 檔會得到誠實的 404。

fallback 也帶來一個要接受的代價：對伺服器而言所有前端路徑都存在，所以你稍後看到的「找不到頁面」畫面，HTTP 狀態碼是 200。外部監控要檢查前端頁面是否存在，不能只看狀態碼。

## React Router 替你多做了什麼

迷你 router 證明了原理，也暴露了不足：`pathname === '/tasks'` 寫不出 `/tasks/:taskId`，沒有巢狀 layout，查詢字串要自己解析。React Router 8 就是把這些做完整的版本。安裝只要一個套件：

```powershell
npm install react-router
```

既有專案常看到的 `react-router-dom` 在 v8 已經移除，所有東西改從 `react-router` import，只有 Data Router 的 `RouterProvider` 例外，要從 `react-router/dom` import。最簡單的用法叫 Declarative mode，用 JSX 描述網址和 component 的對應：

```tsx
const DeclarativeApp = (): React.JSX.Element => (
  <BrowserRouter>
    <Routes>
      <Route path="/tasks" element={<TasksPage />} />
      <Route path="/users" element={<UsersPage />} />
    </Routes>
  </BrowserRouter>
);
```

`BrowserRouter` 負責剛才那段 History API 訂閱，`Routes` 拿目前網址比對底下的 `Route`，只 render 比中的那個 `element`。Task Tracker 最後會用另一種寫法，但巢狀與比對的規則相同。

## 巢狀路由：layout 為什麼不會重新掛載

每個頁面都要有同一條導覽列。把 `<AppNav />` 貼進每個頁面可以動，但切換頁面時，舊頁面的 `AppNav` 和新頁面的 `AppNav` 位在不同的 component 底下，第 09 章說過 state 綁在樹的位置上，導覽列裡的任何 state 都會跟著重置。我們要的是外殼留著，只換中間的內容。

巢狀路由把這件事寫在路由結構裡。子路由的 `element` 不會直接出現在畫面上，而是 render 到父路由 `element` 裡 `<Outlet />` 的位置：

```tsx
const Layout = (): React.JSX.Element => (
  <div>
    <nav>
      <Link to="/tasks">任務</Link>
      <Link to="/users">使用者</Link>
    </nav>
    <Outlet />
  </div>
);

const AppRoutes = (): React.JSX.Element => (
  <Routes>
    <Route path="/" element={<Layout />}>
      <Route index element={<Navigate to="tasks" replace />} />
      <Route path="tasks" element={<TasksPage />} />
      <Route path="users" element={<UsersPage />} />
    </Route>
  </Routes>
);
```

`Outlet` 可以想成由路由決定內容的 `children`。網址從 `/tasks` 換到 `/users` 時，`Layout` 這一層比對結果沒變，React 看到同一個位置還是同一個 component，所以它不會重新掛載，在 layout 裡的輸入框打的字也還在，只有 `Outlet` 的內容被替換。

忘記放 `<Outlet />` 是新手最常見的錯誤，而且完全安靜：網址正確、console 沒有任何訊息、layout 正常顯示，子頁面就是不出現。

`index` 路由回答的是「網址剛好停在父層時，`Outlet` 要放什麼」。使用者打開 `/`，沒有子路徑可以比，`index` 就接手。這裡放 `<Navigate>`，意思是一 render 就導走。`to="tasks"` 不帶斜線，相對於父路由，結果是 `/tasks`；寫 `to="/tasks"` 在這個位置結果一樣，差別在哪天父路由整組搬到 `/app` 底下時，相對路徑會跟著走，絕對路徑不會。

`replace` 決定導向要新增還是覆蓋歷史紀錄，少了它的症狀很具體。假設歷史是 `/about`，使用者點連結到 `/`，被導到 `/tasks`：

```text
有 replace：[/about, /tasks]      按上一頁 → /about
沒 replace：[/about, /, /tasks]   按上一頁 → / → 又被導向 /tasks
```

沒有 `replace` 時，使用者按上一頁會回到轉址那一格，立刻又被彈回 `/tasks`。原則是：只要這一格「不是一個值得回去的地方」，就用 `replace`。第 22 章的登入守衛是同一個道理。

## 比對規則：順序不重要，具體的贏

你對 ASP.NET Core endpoint routing 的直覺在這裡大多能用：選的是最具體的那條，和註冊順序無關。React Router 也是打分排序，所以 `/tasks/new` 這種靜態路徑永遠贏過 `/tasks/:taskId`，就算你把後者寫在前面。`*` 的分數最低，只接其他路由都不要的網址。「`*` 一定要放最後」是過時的說法，放第一個也能正常運作，放最後只是好讀。

| | ASP.NET Core endpoint routing | React Router |
| --- | --- | --- |
| 比對發生在 | 伺服器，每個請求一次 | 瀏覽器，每次網址變動 |
| 動態參數 | `{id}`，可加 `{id:guid}` 限制 | `:taskId`，沒有型別限制 |
| 萬用 | `{**rest}` | `*` |
| 比不中 | 404 狀態碼 | 你自己 render 的畫面，HTTP 仍是 200 |

類比破在兩個地方。第一，endpoint routing 是安全邊界的一部分，`RequireAuthorization` 掛在路由上真的能擋請求；前端路由只決定畫面，整包 JavaScript 都已經在使用者手上（第 22 章會講到底）。第二，`:taskId` 沒有 `{id:guid}` 那種限制，`/tasks/abc` 一樣會進到頁面，驗證要自己做。

`*` 放在哪一層決定了 404 長什麼樣子。放在 `Layout` 底下，404 畫面會出現在 `Outlet` 裡，導覽列還在；放在最外層，就是一個沒有導覽列的獨立頁面。Task Tracker 選後者，第 22 章加上登入守衛之後，這個位置也讓未登入的人打錯網址時看到 404，不會先被導去登入。

## 動態參數：網址變了，component 沒有換

`/tasks/:taskId` 裡的 `:taskId` 是佔位符，`useParams` 把它取出來，並且已經做過 URL 解碼（`/tasks/a%20b` 拿到 `a b`）：

```tsx
const { taskId } = useParams<'taskId'>();
```

`taskId` 的型別是 `string | undefined`。泛型只決定有哪些 key，React Router 在 Data 與 Declarative mode 沒辦法從路由表推導這個 component 一定掛在有 `:taskId` 的路由底下，所以你要自己處理 `undefined`。

真正會咬人的是另一件事。任務詳情頁放一個備註輸入框，再放一個「下一筆」連結，從 `/tasks/1` 走到 `/tasks/2`：

```tsx
const TaskNotePanel = (): React.JSX.Element => {
  const { taskId } = useParams<'taskId'>();
  const [note, setNote] = useState('');
  return (
    <>
      <h1>任務 {taskId}</h1>
      <input aria-label="備註" value={note} onChange={(event) => setNote(event.target.value)} />
      <Link to="/tasks/2">下一筆</Link>
    </>
  );
};
```

標題變成「任務 2」，輸入框裡卻還留著給任務 1 寫的備註。使用者如果接著按儲存，備註就寫到錯的任務上。原因和 layout 不重新掛載完全相同：兩個網址比中同一條路由，同一個位置是同一個 component，React 沒有理由丟掉它的 state。從清單點進去都正常，所以很容易漏測。

修法是第 09 章的工具：`key` 變了就是另一個實例。Task Tracker 的詳情頁把「讀參數」和「顯示內容」拆成兩層，外層拿 `taskId` 當 `key`：

```tsx
export const TaskDetailPage = (): React.JSX.Element => {
  const { taskId } = useParams<'taskId'>();

  return (
    <section>
      <Link to="/tasks">回任務清單</Link>
      {taskId === undefined ? <TaskNotFound /> : <TaskDetail key={taskId} taskId={taskId} />}
    </section>
  );
};
```

內層的 `TaskDetail` 收 `taskId` prop，用 `RemoteData<Task | null>` 記載入結果，Effect 依賴 `[taskId]`，寫法和第 15 章的 `useTasks` 一樣用 AbortController 處理競態。有了 `key`，換任務時 `remote` 自動回到 `loading`，不會短暫顯示上一筆的內容。`fetchTask` 在 404 時回傳 `null`，交給 `TaskNotFound` 顯示。這段載入邏輯到第 21 章會換成 TanStack Query。

## Link、NavLink、useNavigate 各管什麼

使用者會「點」的導覽一律用 `Link`，理由在 History API 那節講過。`NavLink` 多知道一件事：自己是否對應目前的網址。比中時它會加上 `aria-current="page"`，`className` 也可以傳函式來換樣式，Task Tracker 的導覽列就是這樣用的。它預設連子路徑也算比中，所以在 `/tasks/1` 時「任務」仍然亮著，通常正是你要的；要限定完全相同的路徑，加 `end`。

`useNavigate` 給的是另一種情境：導覽發生在某件事之後，例如刪除成功後回清單。

呼叫時寫 `void navigate('/tasks', { replace: true })`：前面的 `void` 告訴 linter 這裡刻意不等它回傳的 Promise，`replace` 的理由和前面相同，已刪除任務的網址不值得回去。

`navigate` 有個陷阱：不能在 render 時呼叫。下面這段看起來合理，實際上什麼都不會發生，只在 console 留一則警告，要你改到 `useEffect` 裡呼叫：

```tsx
const Guard = (): React.JSX.Element => {
  const navigate = useNavigate();
  void navigate('/login'); // 被忽略，網址不會變
  return <p>請先登入</p>;
};
```

第 09 章說過 render 必須是 pure，改網址是副作用，所以 React Router 擋下它。要在 render 階段決定導走，用 `<Navigate to="/login" replace />`，它會回傳畫面描述，導向在 commit 之後才發生。

另一個容易誤判的是 `..`。你在 `/tasks/:taskId` 頁面寫 `<Link to="..">回上層</Link>`，直覺是 `/tasks`。如果路由表把 `tasks` 和 `tasks/:taskId` 寫成同層的兄弟，它連到的卻是 `/`，因為 `..` 預設是往上一層「路由」，而這條路由的父層就是 `/`。要照網址路徑往上，寫 `<Link to=".." relative="path">`。Task Tracker 的路由是扁平的，所以乾脆用絕對路徑。

如果側邊欄用的是第 18 章的 antd `Menu`，它沒有 `Link` 可用，item 的 `key` 直接放路徑，用 `useNavigate` 和 `useLocation` 接上：

```tsx
const handleMenuClick: MenuProps['onClick'] = (event) => {
  void navigate(event.key);
};

const activeKey = pathname.startsWith('/users') ? '/users' : '/tasks';

return <Menu mode="inline" items={items} selectedKeys={[activeKey]} onClick={handleMenuClick} />;
```

`MenuProps['onClick']` 是 indexed access type，直接從套件取出 handler 的型別，套件升級也會跟著變。`activeKey` 不能直接用 `pathname`，否則在 `/tasks/1` 沒有任何項目比中。這些項目不是連結，Ctrl 點擊開新分頁會消失，所以 Task Tracker 的導覽列選 `NavLink`。

## 網址也是 state：篩選該住在哪裡

回到開場的抱怨：篩選結果傳不出去。第 08 章把 `filter` 放在 `useState`，當時是對的選擇，現在需求變了。判斷的問題是：**使用者會希望這個值在重新整理、上一頁、貼給別人之後還在嗎？** 篩選條件和搜尋字會，所以進網址；對話框開關、輸入中的草稿不會，留在 state。

`useSearchParams` 是它的讀寫介面，用法很像 `useState`，但有三個差異都會造成 bug。

第一，物件形式的 setter 是整組覆蓋。目前網址 `/tasks?q=report`，呼叫 `setSearchParams({ status: 'done' })` 之後是 `/tasks?status=done`，搜尋字不見了。要保留其他參數，用函式形式 `(previous) => next`。

第二，函式形式的 `previous` 沒有 `useState` 那種排隊語意。同一個 handler 連呼叫兩次：

```tsx
setSearchParams((previous) => {
  previous.set('status', 'done');
  return previous;
});
setSearchParams((previous) => {
  previous.set('q', 'report');
  return previous;
});
```

結果是 `?q=report`，`status` 沒了。兩次拿到的 `previous` 都來自同一個 render 的網址，第 08 章的 functional update 直覺在這裡不適用。要同時改兩個值，就在一次呼叫裡改完。

第三，網址裡的一切都是字串，而且誰都能亂打。`?status=bogus` 一定會出現，別讓它把頁面弄壞。自己手動拼查詢字串也會出事：``navigate(`/tasks?q=${keyword}`)`` 在 `keyword` 是 `R&D` 時，頁面讀到的 `q` 只有 `R`，後面的 `D` 被當成另一個參數。走 `URLSearchParams` 就會正確編碼成 `q=R%26D`。

Task Tracker 把這些規則收進一個 hook，page 不必知道篩選存在哪裡。邊界用第 17 章的 Zod 守住，schema 只有兩個欄位：`status: z.enum(['all', ...taskStatusSchema.options]).catch('all')` 和 `q: z.string().catch('')`，`.catch` 讓壞值退回預設，不會丟錯。

`useTaskFilters` 做了兩個決定。預設值不寫進網址，`/tasks` 比 `/tasks?status=all&q=` 乾淨，也讓分享出去的連結只帶有意義的條件。每次更新都用 `replace`，因為每改一次篩選都不是一個值得按上一頁回去的地方；如果用 push，打完幾次篩選之後，使用者要按好幾次上一頁才能離開這個頁面。

```ts
import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';
import { taskFiltersSchema } from './schema';
import type { TaskFilterValues } from './schema';

interface UseTaskFiltersResult {
  filters: TaskFilterValues;
  setFilters: (next: Partial<TaskFilterValues>) => void;
}

// 預設值不寫進網址。逐 key 比對，因為搜尋 "all" 這個字是真的搜尋。
const writeParam = (params: URLSearchParams, key: string, value: string, defaultValue: string): void => {
  if (value === defaultValue) params.delete(key);
  else params.set(key, value);
};

export const useTaskFilters = (): UseTaskFiltersResult => {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(
    () => taskFiltersSchema.parse({ status: searchParams.get('status') ?? undefined, q: searchParams.get('q') ?? undefined }),
    [searchParams],
  );

  const setFilters = useCallback(
    (next: Partial<TaskFilterValues>): void => {
      setSearchParams(
        (previous) => {
          const params = new URLSearchParams(previous);
          if (next.status !== undefined) writeParam(params, 'status', next.status, 'all');
          if (next.q !== undefined) writeParam(params, 'q', next.q, '');
          return params;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  return { filters, setFilters };
};
```

狀態按鈕可以直接接上。搜尋框不行，這是本章最細的一個坑，要慢慢看。

直覺寫法是 `value={filters.q}`，`onChange` 呼叫 `setFilters`。問題出在受控 input 的合約：React 要求事件結束前 state 就更新好，否則它會把 DOM 還原成舊的 `value`。而 React Router 預設把路由狀態更新包在 `React.startTransition` 裡（第 30 章會講），這個更新不屬於 input 事件當下的同步 render。於是每打一個字，輸入框先被還原成舊值，transition 完成後又跳成新值，游標跑到最後，中文輸入法的組字也被打斷。這類行為要在真瀏覽器才看得到，參考實作在 chromium 上碰過。

解法是讓輸入框有自己的草稿 state，只在使用者「領先網址」的時候存在：

```tsx
import { useEffect, useEffectEvent, useState } from 'react';
import { useDebounce } from '../react-15-custom-hooks/hooks/useDebounce';

const SEARCH_DEBOUNCE_MS = 300;

interface SearchBoxProps {
  value: string;
  onCommit: (value: string) => void;
}

export const SearchBox = ({ value, onCommit }: SearchBoxProps): React.JSX.Element => {
  const [draft, setDraft] = useState<string | null>(null);
  const debouncedDraft = useDebounce(draft, SEARCH_DEBOUNCE_MS);

  if (draft !== null && draft === value) setDraft(null);

  const commit = useEffectEvent((next: string): void => {
    if (next !== value) onCommit(next);
  });

  useEffect(() => {
    if (debouncedDraft !== null) commit(debouncedDraft);
  }, [debouncedDraft]);

  return (
    <input
      type="search"
      aria-label="搜尋任務標題"
      value={draft ?? value}
      onChange={(event) => setDraft(event.target.value)}
    />
  );
};
```

`draft` 平常是 `null`，輸入框顯示網址的 `value`。打下「報告」，`draft` 變成這個字串，input 走普通的同步 state，不受路由影響。300 毫秒後 `useDebounce`（第 15 章）的值跟上，`commit` 把它寫進網址。網址更新之後 `draft === value`，`draft` 退回 `null`，顯示權交還網址。如果此時使用者點導覽列的「任務」連到乾淨的 `/tasks`，`value` 變成空字串，因為 `draft` 已經是 `null`，輸入框也跟著清空。單一來源仍然是網址，草稿只是打字期間的暫存。

`TasksPage` 的改動因此很小。下面只列有動的部分，`TaskForm`、復原、Toast 維持原樣，「重設畫面」按鈕改成 `setFilters({ status: 'all', q: '' })`。第 15 章的 `TaskFilterBar` 只透過 props 收值，一行都不用改。

```tsx
const { filters, setFilters } = useTaskFilters();
const { remote } = useTasks(filters.q);

const tasks = remote.status === 'success' ? remote.data : [];
const visibleTasks = filters.status === 'all' ? tasks : tasks.filter((task) => task.status === filters.status);
```

JSX 裡換掉原本的搜尋框，`TaskFilterBar` 改接 URL：

```tsx
<>
  <SearchBox value={filters.q} onCommit={(q) => setFilters({ q })} />
  <TaskFilterBar filter={filters.status} onFilterChange={(status) => setFilters({ status })} />
</>
```

搜尋的 debounce 已經搬進 `SearchBox`，`TasksPage` 原本的 `useDebounce` 和 `query` state 可以刪掉。任務標題改成連到 `/tasks/${task.id}` 的 `Link`，清單到詳情就接通了。

## 宣告式還是 Data Router

React Router 8 有三種模式，能力一層包一層：Declarative 是 `<BrowserRouter>` 加 `<Routes>`；Data 改用 `createBrowserRouter` 加 `<RouterProvider>`，多了 `loader`、`action`、`lazy`、`useNavigation` 和路由層級的 `ErrorBoundary`；Framework 再加上 Vite 外掛、型別生成和 SSR。Task Tracker 的後端是 ASP.NET Core，部署是靜態檔加 nginx，用不到 Framework，選擇只剩前兩個。

真正讓兩者分開的情境是 lazy。每個頁面拆成獨立的 chunk、要用時才下載（理由在第 28 章），而兩種模式等待 chunk 時的畫面行為不同：

```tsx
const UsersPage = lazy(() => import('./UsersPage').then((m) => ({ default: m.UsersPage })));

const usersRouteElement = (
  <Suspense fallback={<PageSpinner />}>
    <UsersPage />
  </Suspense>
);
```

上面是 Declarative：`React.lazy` 需要 `default` export，所以用 `then` 轉接具名 export，再把 `usersRouteElement` 當成 `<Route>` 的 `element`。Data Router 的 `lazy` 則是路由物件本身的欄位，寫法在下面的 `router.tsx`。

| 點下連結之後，chunk 還在下載時 | Declarative + `React.lazy` | Data Router `lazy` |
| --- | --- | --- |
| 網址 | 立刻變成 `/users` | 還是 `/tasks`，下載完才變 |
| 畫面 | 舊頁面消失，顯示 fallback | 舊頁面留著可以操作 |
| chunk 下載失敗 | 要自己包 Error Boundary | 進最近的路由 `ErrorBoundary` |

右欄的體驗比較接近傳統網站：點了連結，舊頁面留著，上方出現進度條，好了才換。部署之後舊的 chunk 被清掉是真實會發生的失敗，路由層級能直接接住。Task Tracker 因此選 Data Router。

但 Data Router 的招牌功能 `loader` 我們不用。`loader` 在導覽前先抓資料，頁面用 `useLoaderData` 拿結果。Task Tracker 的資料要有快取、背景更新和樂觀更新，這些是第 21 章 TanStack Query 的工作，再讓 `loader` 管一份會出現兩個資料擁有者。所以路由只管「網址對應哪個頁面」，資料由 query 層管。沒有這些需求的專案，`loader` 是合理的起點。

路由表放在 `router.tsx`。第 24 章重整成 feature 結構前，檔案先都放在 `src/` 底下：

```tsx
import { createBrowserRouter, Navigate } from 'react-router';
import type { RouteObject } from 'react-router';
import { AppLayout } from './AppLayout';
import { NotFoundPage, RouteErrorPage } from './errorPages';
import { PageSpinner } from './PageSpinner';

export const routes: RouteObject[] = [
  {
    ErrorBoundary: RouteErrorPage,
    HydrateFallback: PageSpinner,
    children: [
      { path: '/login', lazy: { Component: async () => (await import('./LoginPage')).LoginPage } },
      {
        Component: AppLayout,
        children: [
          {
            ErrorBoundary: RouteErrorPage,
            children: [
              { path: '/', element: <Navigate to="/tasks" replace /> },
              { path: '/tasks', lazy: { Component: async () => (await import('./TasksPage')).TasksPage } },
              { path: '/tasks/:taskId', lazy: { Component: async () => (await import('./TaskDetailPage')).TaskDetailPage } },
              { path: '/users', lazy: { Component: async () => (await import('./UsersPage')).UsersPage } },
            ],
          },
        ],
      },
      { path: '*', Component: NotFoundPage },
    ],
  },
];

export const router = createBrowserRouter(routes);
```

這張表每一層都有理由。沒有 `path` 的路由叫 pathless route，它不吃網址，只提供畫面外殼或邊界；`AppLayout` 用這種方式包住需要導覽列的頁面，`/login` 與 `*` 不在它底下，所以沒有導覽列。在 pathless layout 底下，`path: '/'` 和前面學的 `index: true` 效果相同，這裡為了和其他絕對路徑一致而採用前者。第 22 章會把 `ProtectedRoute` 插在 `AppLayout` 外面一層，這張表的其他部分不用動。

`ErrorBoundary` 有兩層。內層讓某一頁壞掉時導覽列還在，使用者能走去別的頁；外層接住 `/login` 和 layout 本身的錯誤。完整的錯誤處理是第 25 章的事。`HydrateFallback` 處理第一次載入：貼連結直接開 `/users` 時，還沒有舊頁面可以留著，chunk 下載期間就顯示它。

`createBrowserRouter` 放在模組頂層，整個應用只建一次，官方文件也明確要求放在 React 樹之外。router 實例持有導覽狀態與已載入的 lazy 結果，寫在 component 裡就會每次 render 都重來一份。入口只要 `<RouterProvider router={router} />`，注意 import 來源是 `react-router/dom`，它替你帶入 `flushSync`；第 13 章的 `ToastProvider` 仍包在外面。

`AppLayout` 是前面零件的組合：`NavLink` 的 `className` 傳 `({ isActive }) => cn(...)`（第 16 章），內容區放 `<Outlet />`，再用 `navigation.state === 'loading'` 顯示表格右欄說的進度條。換頁時把焦點移到主要內容，是第 27 章要加的。`RouteErrorPage` 用 `useRouteError` 取得錯誤，型別是 `unknown`，先用 `isRouteErrorResponse` 與 `instanceof Error` 判斷才能讀；

## 常見誤解

**「路由表沒列出來的頁面，使用者就進不去，所以算保護。」** 拿掉路由只是讓畫面沒有入口，程式碼和 API 都還在。真正的權限檢查永遠在後端。開發工具頁也一樣：`{<Route path="sudoku" element={<SudokuSolver />} />}` 外層的大括號只是 JSX 表達式，不做任何判斷，production 照樣掛載。寫成 `{import.meta.env.DEV && <Route ... />}` 才是條件，`Routes` 會略過值為 `false` 的 child；Vite 在 build 時把 `import.meta.env.DEV` 換成常數，這條分支才有機會被移除。Data Router 的陣列則寫成 `...(import.meta.env.DEV ? [devRoute] : [])`。

**「`useParams<{ taskId: string }>()` 保證了參數存在。」** 泛型沒有任何 runtime 檢查，取出來仍是 `string | undefined`，內容也只保證是字串。第 20 章的 Zod 邊界上線後，詳情頁會先用 `z.uuid()` 擋掉明顯錯誤的 ID。

**「路由設定是純資料，同一份 `routes` 陣列可以給很多個 router。」** 含 `lazy` 物件的路由不行。第一個 router 載入後，第二個 router 用同一份物件走到那條路由，會直接進 `ErrorBoundary`，錯誤是 404 `No route matches URL`，網址明明正確。正式環境只有一個 router 碰不到，每個測試各建一個 memory router 時就會踩到，第 26 章會用到這個結論。

## 同事會來問你的問題

**「部署後重新整理變 404，怎麼查？」** 先分清楚這個 404 是誰給的。打開 DevTools 的 Network，看第一筆 document 請求。回應是 nginx 或 Kestrel 的 404，代表 fallback 沒設，用 `curl.exe -i https://tracker.example.com/tasks/42` 可以不開瀏覽器重現。回應是 200 而畫面顯示「找不到頁面」，那是 React Router 的 `*`，要檢查路由表。如果 document 正常、JS 請求卻回了 HTML，console 會出現 `Unexpected token '<'` 或 MIME type 錯誤：資源路徑是相對的，`/tasks/42` 底下去抓 `/tasks/assets/x.js`，被 fallback 回了 `index.html`。Vite 預設 `base: '/'` 不會這樣，有人改過 `base` 時才要懷疑，細節在第 29 章。

**「『回上一頁』按鈕直接 `navigate(-1)` 不就好了？」** 從清單點進來時沒問題，還保留了篩選。但如果使用者是開別人貼的連結進來，歷史紀錄的上一格可能是別的網站，甚至沒有上一格。要兼顧，可以進詳情頁時在 `Link` 加上 `state={location.search}` 把清單的查詢字串帶過去，返回連結用它組回 `/tasks?status=done`，沒有 state 時退回 `/tasks`。`location.state` 存在這個分頁的歷史紀錄裡，不在網址上，貼給別人就沒了，讀取時也要當成 `unknown` 檢查。Task Tracker 選最簡單的固定連到 `/tasks`，代價是篩選會重置。

**「`/tasks?status=done` 和 `/tasks/done` 哪個好？」** 問這個值移除之後資源還成不成立。任務詳情的 ID 拿掉就不是同一個東西，放 path。篩選和排序是對同一份清單的檢視，而且可以多個並存、順序不重要，放 search params。這個判斷和你設計 `GET /api/tasks?status=done` 時完全相同。

## 本章小結

網址能在 SPA 裡變化，靠的是 History API 改網址不發請求，也因此直接開網址時需要伺服器 fallback 把 `index.html` 交出來。React Router 在這之上提供比對、巢狀 layout 和參數，同一條路由下 component 不會重新掛載，這帶來穩定的 layout，也帶來參數改變時殘留 state 的 bug。使用者想保留或分享的值應該住在 URL，並用 Zod 把它當成不可信的外部輸入。Task Tracker 有了完整的頁面骨架，但資料請求還零散地寫著 `fetch`，下一章要回答 API 呼叫到底該寫在哪裡。

## 連結

- 上一章：[[react-18-component-libraries]]
- 下一章：[[react-20-api-layer]]
- [[react-09-rendering]] — state 綁在樹的位置、`key` 重置
- [[react-15-custom-hooks]] — `useSyncExternalStore`、`useDebounce`
- [[react-21-server-state]] — TanStack Query 取代詳情頁的 Effect
- [[react-22-authentication]] — `ProtectedRoute` 插進路由表
- [[react-25-error-and-loading]] — Error Boundary 的完整行為
- [[react-29-build-and-deploy]] — nginx 與 `base`
- [[56-frontend-deployment]] — 前端部署
