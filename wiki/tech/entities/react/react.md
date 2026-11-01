---
type: entity
domain: tech
tags: [react, typescript, frontend, hooks, spa]
sources:
  - raw/Web Framework/React/React.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
created: 2026-05-03
updated: 2026-10-31
---

# React

React 是一個以 Component 為核心的 UI 函式庫。配合 TypeScript 使用時，Props、State、Event 全部都有型別保護。

這一頁有兩個身分。上半部是**教材總目錄**：一本從 `raw/Web Framework/React/` 那 17 份筆記重寫而成、可以從頭讀到尾的書，回答「為什麼」。下半部是舊有的**速查**，回答「怎麼寫」。

---

## 教材：React + TypeScript — 從會抄範例到說得出機制

React 的入門體驗讓人以為自己會了。照著範例能做出畫面，但 `useEffect` 無限迴圈時只能試到好，setter 下一行讀到舊值時只能加 `setTimeout`，code review 被問「為什麼這裡要 `useCallback`」答不出來。這本書要補的就是這個落差：讀者不缺語法清單，缺的是機制，以及出事時怎麼推理。

### 誰該讀

預設讀者寫過 ASP.NET Core Web API，HTML、CSS、JavaScript 看得懂但不穩，寫過一點 React，多半靠抄範例。書中會在有幫助的地方對照 ASP.NET Core 與 Oracle 的概念，並指出類比在哪裡失效。

讀完應該能從需求切出 component 與 state ownership、分清楚 event 與 Effect、用型別與 runtime validation 守住 API 邊界、把 SPA 接上 ASP.NET Core 並部署，也能定位 rendering、network、state 三類問題，在 review 時說得出理由。

全書以 **React 19.3、TypeScript 7、Vite 8、React Router 8、TanStack Query 5、Tailwind 4、Zod 4** 為基準，並用同一個 Task Tracker 專案貫穿：每章把它往前推一步，最後一章看到全貌。書中範例都在沙盒實際編譯並測試過。

### 進度總覽

**撰寫中。** 寫作順序是核心機制優先，所以章號會跳著完成。✅ 已完成，空白表示尚未撰寫。

| 篇 | 章節 | 核心問題 | 狀態 |
| --- | --- | --- | --- |
| **第一篇 地基** | [[react-00-why-react]] | 為什麼不用 jQuery 就好？React 到底解決什麼？ | |
| | [[react-01-browser-and-dom]] | React 底下的瀏覽器在做什麼？ | |
| | [[react-02-javascript-for-react]] | 寫 React 真正需要哪些 JavaScript？ | |
| | [[react-03-async-javascript]] | 為什麼網路資料不會立刻回來？ | |
| | [[react-04-typescript-foundations]] | TypeScript 保護了什麼、沒保護什麼？ | |
| | [[react-05-typescript-modeling]] | 怎麼用型別把不合法狀態排除掉？ | |
| **第二篇 核心模型** | [[react-06-components-and-jsx]] | JSX 到底是什麼？ | ✅ |
| | [[react-07-props]] | 資料怎麼在 component 之間流動？ | |
| | [[react-08-state]] | 為什麼 setter 之後讀到的還是舊值？ | ✅ |
| | [[react-09-rendering]] | React 怎麼決定要更新什麼？ | ✅ |
| | [[react-10-tic-tac-toe]] | 把前四章組起來長什麼樣？ | |
| **第三篇 Hooks** | [[react-11-effects]] | useEffect 什麼時候該用、什麼時候不該用？ | ✅ |
| | [[react-12-refs]] | 什麼東西要記住但不該觸發 render？ | |
| | [[react-13-reducer-and-context]] | 狀態邏輯變複雜、要穿透很多層時怎麼辦？ | |
| | [[react-14-memoization]] | useMemo/useCallback/React.memo 該不該加？ | |
| | [[react-15-custom-hooks]] | 邏輯怎麼重用？ | |
| **第四篇 畫面** | [[react-16-tailwind]] | 為什麼要把 class 寫得這麼長？ | |
| | [[react-17-forms]] | 表單為什麼是 React 裡最麻煩的東西？ | |
| | [[react-18-component-libraries]] | 元件庫怎麼選、怎麼不被綁死？ | |
| **第五篇 真實應用** | [[react-19-routing]] | 只有一個 HTML，網址怎麼會變？ | |
| | [[react-20-api-layer]] | API 呼叫該寫在哪裡？ | |
| | [[react-21-server-state]] | 後端資料為什麼不該放 useState？ | |
| | [[react-22-authentication]] | 前端的登入到底保護了什麼？ | |
| | [[react-23-client-state]] | 什麼時候才需要 Zustand？ | |
| **第六篇 工程化** | [[react-24-project-architecture]] | 專案長大後要怎麼不崩潰？ | |
| | [[react-25-error-and-loading]] | 出錯或等待時畫面該長怎樣？ | |
| | [[react-26-testing]] | 前端要測什麼才值得？ | |
| | [[react-27-accessibility]] | 為什麼 div 不能當按鈕？ | |
| | [[react-28-performance]] | 感覺慢的時候先看哪裡？ | |
| | [[react-29-build-and-deploy]] | `npm run build` 之後發生什麼？ | |
| **第七篇 進階** | [[react-30-concurrent-react]] | 為什麼打字會卡，又怎麼不卡？ | |
| | [[react-31-server-components]] | Server Component 不是 SSR？ | |
| | [[react-32-canvas-foundations]] | Canvas 和 React 怎麼相處？ | |
| | [[react-33-canvas-interactive]] | 怎麼做出會動、能互動的畫布？ | |
| **實戰** | [[react-34-practice-task-tracker]] | 從空專案到接上 ASP.NET Core 到部署 | |
| **附錄** | [[react-a1-hooks-reference]] | A：全部 Hook 對照 | |
| | [[react-a2-typescript-cheatsheet]] | B：React × TS 型別速查 | |
| | [[react-a3-tailwind-cheatsheet]] | C：Tailwind class 速查 | |
| | [[react-a4-ecosystem-resources]] | D：生態系與學習資源 | |
| | [[react-a5-troubleshooting]] | E：錯誤訊息與症狀對照 | |
| | [[react-a6-self-assessment]] | F：三級自我檢測 | |
| **補充篇** | [[react-35-component-patterns]] | 怎麼設計別人好用的 component？ | |
| | [[react-36-react-internals]] | Hook 為什麼不能放 if 裡？ | |
| | [[react-37-frontend-security]] | 前端能被怎麼打？ | |
| | [[react-38-realtime-signalr]] | 任務被別人改了，畫面怎麼即時更新？ | |
| | [[react-39-file-upload-download]] | 上傳下載為什麼都會踩坑？ | |
| | [[react-40-i18n-and-datetime]] | 多語系和時區怎麼不出錯？ | |
| | [[react-41-observability]] | 使用者說壞了，你怎麼知道發生什麼？ | |
| | [[react-42-legacy-and-migration]] | 接手舊專案該怎麼辦？ | |
| | [[react-43-code-review-checklist]] | React PR 要看什麼？ | |

---

## 速查

## Component Props 型別

```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}

const Button = ({ label, onClick, variant = "primary", disabled = false }: ButtonProps) => (
  <button onClick={onClick} disabled={disabled} className={`btn-${variant}`}>
    {label}
  </button>
);
```

## Event Handler 型別

```typescript
import { ChangeEvent, FormEvent, MouseEvent } from "react";

const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
  console.log(e.target.value);
};

const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();
};

const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
  console.log("clicked");
};
```

## Hooks

### useState

```typescript
// 資料改變後，畫面需不需要跟著變
// 需要 → useState；不需要 → const

const [count, setCount] = useState(0);
const [user, setUser] = useState<User | null>(null);
const [users, setUsers] = useState<User[]>([]);

// 更新物件（記得展開舊 state）
setUser(prev => prev ? { ...prev, name: "Bob" } : null);

// 更新陣列（建立新陣列，不直接修改）
setUsers(prev => [...prev, newUser]);
setUsers(prev => prev.filter(u => u.id !== 3));
```

### useEffect

```typescript
// 執行時機：state 改變 → render → DOM commit → useEffect

useEffect(() => { ... }, []);      // 只在 mount 時跑一次
useEffect(() => { ... }, [x]);     // x 改變後跑
useEffect(() => { ... });          // 每次 render 都跑

// 資料獲取範例
useEffect(() => {
  const fetchUser = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/users/${userId}`);
      if (!res.ok) throw new Error("載入失敗");
      setUser(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };
  fetchUser();
}, [userId]);  // userId 變化時重跑

// Cleanup（清理 side effect）
useEffect(() => {
  const timer = setInterval(() => console.log("tick"), 1000);
  return () => clearInterval(timer);  // unmount 或下次 effect 前呼叫
}, []);
```

### useMemo 與 useCallback

```typescript
// useMemo：快取計算結果，偵測的東西改變才重算
const expensiveValue = useMemo(() => count * 1000, [count]);

// useCallback：快取函式 reference，避免子 component 不必要 re-render
const handleClick = useCallback(() => {
  setCount(c => c + 1);
}, []);  // 沒有依賴，函式永遠不改變

// 搭配 React.memo
const Child = React.memo(({ onClick }: { onClick: () => void }) => (
  <button onClick={onClick}>Click</button>
));
```

### useRef

```typescript
// 用途一：操作 DOM
const inputRef = useRef<HTMLInputElement | null>(null);
useEffect(() => { inputRef.current?.focus(); }, []);
return <input ref={inputRef} />;

// 用途二：儲存不觸發 re-render 的值（如 timer ID）
const intervalRef = useRef<number | null>(null);
const start = () => {
  intervalRef.current = setInterval(() => setCount(c => c + 1), 1000);
};
const stop = () => clearInterval(intervalRef.current!);
```

**useRef vs useState**：修改 `.current` 不觸發 re-render；需要畫面更新用 `useState`，只需記住值用 `useRef`

### useContext

```typescript
interface AuthContextType {
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  return (
    <AuthContext.Provider value={{ user, login: setUser, logout: () => setUser(null) }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth 必須在 AuthProvider 內使用");
  return context;
};
```

### 自訂 Hook

```typescript
// 命名規則：use 開頭
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  }, [url]);

  return { data, loading, error, fetchData };
}
```

## 狀態管理：Zustand

輕量全域狀態管理，比 Redux 簡潔，適合中小型專案：

```typescript
import { create } from "zustand";

interface UserState {
  users: User[];
  isLoading: boolean;
  addUser: (user: User) => void;
  removeUser: (id: number) => void;
  fetchUsers: () => Promise<void>;
}

export const useUserStore = create<UserState>((set) => ({
  users: [],
  isLoading: false,
  addUser: (user) => set((state) => ({ users: [...state.users, user] })),
  removeUser: (id) => set((state) => ({ users: state.users.filter(u => u.id !== id) })),
  fetchUsers: async () => {
    set({ isLoading: true });
    const users = await userApi.getAll();
    set({ users, isLoading: false });
  },
}));

// 使用（只在 users 變化時 re-render）
const users = useUserStore((state) => state.users);
```

## API 串接模式

```typescript
// 封裝 fetch，統一處理 token 和錯誤
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token");
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}
```

## 專案結構建議

```
src/
├── api/           # API 呼叫模組（userApi.ts、authApi.ts）
├── components/    # 可重用 UI 元件
│   ├── ui/        # 基礎元件（Button、Input）
│   └── shared/    # 共用業務元件
├── hooks/         # 自訂 Hook
├── lib/           # 工具函式、API Client
├── pages/         # 頁面元件（對應路由）
├── stores/        # Zustand Store
├── types/         # 全域型別定義
└── App.tsx
```

## 連結

- [[dom]] — React 底下的真實 DOM、Virtual DOM 與 useRef 的界線
- [[typescript]] — React 搭配的型別系統
- [[dotnet-web-api]] — 後端 API 整合
