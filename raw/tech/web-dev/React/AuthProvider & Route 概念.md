# AuthProvider & Route 概念

---

## 目錄

1. [整體架構概覽](about:blank#%E6%95%B4%E9%AB%94%E6%9E%B6%E6%A7%8B%E6%A6%82%E8%A6%BD)
2. [App.tsx — 路由層](about:blank#apptsx--%E8%B7%AF%E7%94%B1%E5%B1%A4)
    - [AuthProvider：Context 注入](about:blank#1-authprovider--context-%E6%B3%A8%E5%85%A5)
    - [公開路由 vs 受保護路由](about:blank#2-%E5%85%AC%E9%96%8B%E8%B7%AF%E7%94%B1-vs-%E5%8F%97%E4%BF%9D%E8%AD%B7%E8%B7%AF%E7%94%B1)
    - [ProtectedRoute：路由守衛](about:blank#3-protectedroute--%E8%B7%AF%E7%94%B1%E5%AE%88%E8%A1%9B)
    - [巢狀路由與 Outlet](about:blank#4-%E5%B7%A2%E7%8B%80%E8%B7%AF%E7%94%B1%E8%88%87-outlet)
    - [index route + Navigate 重導向](about:blank#5-index-route--navigate-%E9%87%8D%E5%B0%8E%E5%90%91)
    - [動態路由參數 :slug](about:blank#6-%E5%8B%95%E6%85%8B%E8%B7%AF%E7%94%B1%E5%8F%83%E6%95%B8-slug)
    - [萬用路由 * 做 404](about:blank#7-%E8%90%AC%E7%94%A8%E8%B7%AF%E7%94%B1--%E5%81%9A-404)
    - [DEV 環境路由（待修正）](about:blank#8-dev-%E7%92%B0%E5%A2%83%E8%B7%AF%E7%94%B1%E5%BE%85%E4%BF%AE%E6%AD%A3)
3. [HomePage.tsx — Layout 元件層](about:blank#homepagetsx--layout-%E5%85%83%E4%BB%B6%E5%B1%A4)
    - [useIsMobile：自訂響應式 Hook](about:blank#1-useismobile--%E8%87%AA%E8%A8%82%E9%9F%BF%E6%87%89%E5%BC%8F-hook)
    - [useMemo：快取計算結果](about:blank#2-usememo--%E5%BF%AB%E5%8F%96%E8%A8%88%E7%AE%97%E7%B5%90%E6%9E%9C)
    - [useNavigate：程式化導航](about:blank#3-usenavigate--%E7%A8%8B%E5%BC%8F%E5%8C%96%E5%B0%8E%E8%88%AA)
    - [條件渲染：isMobile 控制三區塊](about:blank#4-%E6%A2%9D%E4%BB%B6%E6%B8%B2%E6%9F%93--ismobile-%E6%8E%A7%E5%88%B6%E4%B8%89%E5%8D%80%E5%A1%8A)
    - [環境變數控制選單可見性](about:blank#5-%E7%92%B0%E5%A2%83%E8%AE%8A%E6%95%B8%E6%8E%A7%E5%88%B6%E9%81%B8%E5%96%AE%E5%8F%AF%E8%A6%8B%E6%80%A7)

---

## 整體架構概覽

```
App.tsx
└── AuthProvider                    ← Context，提供全域登入狀態
    └── Routes
        ├── /login → AuthPage       ← 公開，不需登入
        └── / → ProtectedRoute      ← 守衛，未登入踢回 /login
              └── HomePage          ← Layout 元件，含 <Outlet />
                    ├── index       → Navigate /homepage
                    ├── homepage    → Homepage
                    ├── notes       → NotesList
                    ├── notes/:slug → NoteArticle
                    ├── ruleviewer  → RuleViewer
                    └── *           → ErrorPage 404
```

---

## App.tsx — 路由層

### 1. AuthProvider：Context 注入

```tsx
<AuthProvider>
  <Routes>...</Routes>
</AuthProvider>
```

**概念：React Context**

- `AuthProvider` 包在最外層，讓整棵元件樹都能透過 `useAuth()` 取得登入狀態
- Provider 必須在「使用 context 的元件」之上，否則 `useContext` 讀到的是預設值
- `ProtectedRoute` 內部呼叫 `useAuth()`，所以它必須在 `AuthProvider` 裡面

```tsx
// AuthContext.tsx 大致結構
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("**useAuth 必須在 AuthProvider 內使用**");
  return ctx;
};
```

---

### 2. 公開路由 vs 受保護路由

```tsx
{/* 不需登入 */}
<Route path="/login" element={<AuthPage />} />

{/* 需要登入 */}
<Route
  path="/"
  element={
    <ProtectedRoute>
      <HomePage />
    </ProtectedRoute>
  }
>
```

**概念：平行 Route、單一入口保護**

- `/login` 和 `/` 是同層的兄弟路由，互不干涉
- 所有需要保護的頁面都掛在 `/` 底下，只需在父層做一次保護，不需要每個頁面重複寫驗證邏輯
- `/login` 完全繞過 `ProtectedRoute`，未登入使用者一定能進到登入頁

---

### 3. ProtectedRoute：路由守衛

```tsx
const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
```

**概念：條件渲染 + Navigate**

- 這不是 react-router-dom 的內建元件，是自己寫的
- 有登入 → 渲染 `children`（也就是 `<HomePage />`）
- 沒登入 → 用 `<Navigate>` 跳轉到 `/login`

**`replace` vs 不加 `replace` 的差異：**

|  | 行為 |
| --- | --- |
| `replace` | 不留歷史紀錄，按上一頁不會卡住 |
| 不加（預設 push） | 留下歷史紀錄，按上一頁會回到被擋的頁面，再被踢一次 |

> 登入守衛一律用 `replace`，避免無限循環的使用者體驗問題。
> 

---

### 4. 巢狀路由與 Outlet

```tsx
<Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>}>
  <Route path="homepage" element={<Homepage />} />
  <Route path="notes" element={<NotesList />} />
  {/* ... */}
</Route>
```

**概念：Nested Routes + Outlet**

- 子路由的 `element` 不會直接出現在畫面上，而是渲染進父路由 element 裡的 `<Outlet />` 位置
- `HomePage.tsx` 必須在適當的位置放 `<Outlet />`，否則子頁面永遠不會顯示

```tsx
// HomePage.tsx 的關鍵部分
const HomePage = () => {
  return (
    <Layout>
      <Sider>...</Sider>
      <Content>
        <Outlet />  {/* ← Homepage、NotesList 等渲染在這裡 */}
      </Content>
    </Layout>
  );
};
```

**為什麼這樣設計：**
- Sidebar、TopBar、TabBar 等 Layout 只需要寫一次
- 切換頁面時 Layout 不會重新掛載，只有 `<Outlet />` 的內容替換

---

### 5. index route + Navigate 重導向

```tsx
<Route index element={<Navigate to="homepage" replace />} />
```

**概念：index route**

- `index` 代表「父路由精確匹配時的預設子路由」
- 進入 `/` 時，index route 觸發，`<Navigate>` 立刻導向 `/homepage`
- `to="homepage"` 是相對路徑（不帶斜線），相對於父路由 `/`，等同於 `/homepage`

**完整對比：**

| 寫法 | 結果 |
| --- | --- |
| `to="homepage"` | 相對路徑 → `/homepage` |
| `to="/homepage"` | 絕對路徑 → `/homepage`（一樣） |
| `to="/other/homepage"` | 絕對路徑 → `/other/homepage`（不同） |

---

### 6. 動態路由參數 :slug

```tsx
<Route path="notes/:slug" element={<NoteArticle />} />
```

**概念：Dynamic Segments**

- `:slug` 是佔位符，可以匹配任意字串
- `/notes/react-intro`、`/notes/hooks-guide` 都會匹配
- 在元件裡用 `useParams()` 取出，加 TypeScript 泛型保持型別安全

```tsx
import { useParams } from "react-router-dom";

const NoteArticle = () => {
  const { slug } = useParams<{ slug: string }>();
  // /notes/react-intro → slug = "react-intro"
};
```

---

### 7. 萬用路由 * 做 404

```tsx
<Route path="*" element={<ErrorPage statusCode={404} />} />
```

**概念：Catch-all Route**

- 比對所有沒被前面路由抓到的路徑
- 必須放在同層子路由的最後，確保精確路由先嘗試
- 這個  只接 `/` 底下的 404，放在 `/` 的子路由裡，`/login` 以外的頂層未知路徑不受影響

---

### 8. DEV 環境路由（待修正）

```tsx
// 現在：不論環境都掛載
{<Route path="sudoku" element={<SudokuSolver />} />}

// 正確：只在 DEV 才掛載
{import.meta.env.DEV && <Route path="sudoku" element={<SudokuSolver />} />}
{import.meta.env.DEV && <Route path="tailwind" element={<TailwindCheatsheet />} />}
```

**為什麼現在的寫法有問題：**

- 外層大括號只是把 JSX 放進 JS 表達式，不做任何條件判斷
- Production build 一樣會掛載這些路由，使用者猜到 URL 就能進入
- 加上 `import.meta.env.DEV &&` 才能讓 production build 完全移除這些路由

> Vite 環境變數規則：只有 `VITE_` 開頭的變數才能在前端讀取。`import.meta.env.DEV` 是 Vite 內建的布林值，不需要自訂。
> 

---

## HomePage.tsx — Layout 元件層

### 1. useIsMobile：自訂響應式 Hook

```tsx
function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(
    () => window.innerWidth < breakpoint  // lazy initializer
  );

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);  // cleanup
  }, [breakpoint]);

  return isMobile;
}
```

**三個技巧同時出現：**

**① useState Lazy Initializer**

```tsx
// 錯誤：每次 render 都執行 window.innerWidth
const [isMobile, setIsMobile] = useState(window.innerWidth < breakpoint);

// 正確：傳函式，只在初始化時執行一次
const [isMobile, setIsMobile] = useState(() => window.innerWidth < breakpoint);
```

**② MediaQueryList 監聽視窗變化**

- `window.matchMedia(...)` 比監聽 `resize` 事件更精準，只在跨越 breakpoint 時觸發
- `e.matches` 是布林值，直接對應 `isMobile` 的型態

**③ useEffect Cleanup**

```tsx
return () => mq.removeEventListener("change", handler);
```

- 元件卸載時自動移除 listener，防止記憶體洩漏
- 如果沒有 cleanup，元件消失後 handler 還在跑，可能對已卸載的元件 setState 引發警告

---

### 2. useMemo：快取計算結果

```tsx
const selectedKeys = useMemo(
  () => [location.pathname],
  [location.pathname]
);

const currentPageLabel = useMemo(() => {
  const flat = items.flatMap((item: any) =>
    item?.children ? [item, ...item.children] : [item]
  );
  const found = flat.find((item: any) => item?.key === location.pathname);
  return typeof found?.label === "string" ? found.label : "Menu";
}, [location.pathname]);
```

**為什麼要用 useMemo：**

- `selectedKeys`：每次 render 都 `[location.pathname]` 會產生新的陣列參考，傳給 Ant Design `<Menu>` 會觸發不必要的子元件重新渲染。`useMemo` 讓陣列參考穩定。
- `currentPageLabel`：`flatMap` + `find` 要遍歷整個選單陣列，快取起來只在路徑改變時重算。

**使用時機：**

| 情況 | 要不要用 useMemo |
| --- | --- |
| 計算結果會傳給子元件 props | 要（參考穩定性） |
| 計算本身耗時（大量資料處理） | 要 |
| 簡單的字串拼接、加減法 | 不需要，反而增加複雜度 |

---

### 3. useNavigate：程式化導航

```tsx
const handleMenuClick: MenuProps["onClick"] = (e) => {
  const key = String(e.key);
  if (key.startsWith("/")) {
    navigate(key);
    setDrawerOpen(false);
  }
};
```

**概念：useNavigate + TypeScript 索引型別**

- `useNavigate()` 回傳一個函式，呼叫它就等於點了 `<Link>`
- 型別寫 `MenuProps["onClick"]` 是 TypeScript 的**索引型別（Indexed Access Type）**，直接從 Ant Design 的型別定義中取出 onClick 的型別，不需要自己猜

```tsx
// 自己寫型別（容易猜錯）
const handleMenuClick = (e: { key: string }) => {...}

// 從現有型別取出（正確且自動跟隨套件更新）
const handleMenuClick: MenuProps["onClick"] = (e) => {...}
```

- `key.startsWith("/")` 過濾掉分組 key（例如「專案開發」），只對路徑字串做導航

---

### 4. 條件渲染：isMobile 控制三區塊

```tsx
{/* 桌面 Sider */}
{!isMobile && <Sider>...</Sider>}

{/* 手機 Top Bar */}
{isMobile && <div>...</div>}

{/* 手機底部 Tab Bar（IIFE 寫法） */}
{isMobile && (() => {
  const tabs = [...];
  return <div>...</div>;
})()}
```

**IIFE in JSX 是什麼：**

`(() => { ... })()` 是立即執行函式（IIFE，Immediately Invoked Function Expression）。

在 JSX 裡用它的目的是建立一個局部作用域，在裡面宣告 `tabs` 陣列，避免把它提升到元件頂層污染作用域，或是把 JSX 拆成另一個函式。

```tsx
// 等價的寫法（用獨立函式）
const TabBar = () => {
  const tabs = [...];
  return <div>...</div>;
};

// ...
{isMobile && <TabBar />}
```

兩種寫法都正確，IIFE 寫法適合這個邏輯很短、不需要重用的情況。

---

### 5. 環境變數控制選單可見性

```tsx
const SHOW_PRIVATE = import.meta.env.VITE_SHOW_PRIVATE === "true";

function privateLabel(label: string) {
  if (SHOW_PRIVATE) return label;
  return (
    <span className="flex items-center justify-between gap-1 w-full opacity-50">
      {label}
      <LockOutlined style={{ fontSize: 11 }} />
    </span>
  );
}

// 選單項目
{
  label: privateLabel("專案開發"),
  disabled: !SHOW_PRIVATE,
}
```

**重要細節：字串比較 `=== "true"`**

```tsx
// 錯誤：字串 "false" 是 truthy，結果永遠是 true
const SHOW_PRIVATE = import.meta.env.VITE_SHOW_PRIVATE;

// 正確：明確比較字串值
const SHOW_PRIVATE = import.meta.env.VITE_SHOW_PRIVATE === "true";
```

環境變數永遠是字串型態。即使 `.env` 裡寫 `VITE_SHOW_PRIVATE=false`，讀到的也是字串 `"false"`，直接用在 if 條件會是 `true`。

**`.env` 設定：**

```bash
# .env.development
VITE_SHOW_PRIVATE=true

# .env.production
VITE_SHOW_PRIVATE=false
```

---

## 快速對照表

| 概念 | 用在哪 | 關鍵 API |
| --- | --- | --- |
| React Context | AuthProvider 全域登入狀態 | `createContext` `useContext` |
| 路由守衛 | ProtectedRoute 把關 `/` 底下所有頁面 | `Navigate replace` |
| 巢狀路由 | HomePage 作為 Layout，子頁面填入 Outlet | `Outlet` |
| index route | 進入 `/` 自動導向 `/homepage` | `Route index` |
| 動態路由 | 筆記文章頁 `/notes/:slug` | `useParams` |
| 萬用路由 | 404 頁面 | `path="*"` |
| Lazy Initializer | useIsMobile 初始值只算一次 | `useState(() => ...)` |
| useMemo | selectedKeys 參考穩定、currentPageLabel 計算快取 | `useMemo` |
| 索引型別 | handleMenuClick 從 MenuProps 取出正確型別 | `Type["key"]` |
| IIFE in JSX | Tab Bar 局部作用域 | `(() => {...})()` |
| 環境變數 | SHOW_PRIVATE 控制選單鎖定 | `import.meta.env.VITE_*` |

---

> 最後更新：2026 年 3 月
對應 commit：App.tsx + HomePage.tsx 初版架構
>