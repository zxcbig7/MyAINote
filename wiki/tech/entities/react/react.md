---
type: entity
domain: tech
tags: [react, typescript, frontend, hooks, spa]
sources:
  - raw/tech/web-dev/React.md
  - raw/tech/web-dev/React/React + TypeScript 開發手冊.md
created: 2026-05-03
updated: 2026-05-03
---

# React

React 是一個以 Component 為核心的 UI 框架。配合 TypeScript 使用時，Props、State、Event 全部都有型別保護。

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
