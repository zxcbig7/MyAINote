# React + TypeScript 開發語法指南

---

## 目錄

1. [TypeScript 基礎型別](#1-typescript-基礎型別)
2. [型別定義：type vs interface](#2-型別定義type-vs-interface)
3. [泛型 Generic](#3-泛型-generic)
4. [useState](#4-usestate)
5. [useEffect](#5-useeffect)
6. [useRef](#6-useref)
7. [useMemo](#7-usememo)
8. [useCallback](#8-usecallback)
9. [useContext + createContext](#9-usecontext--createcontext)
10. [forwardRef + useImperativeHandle](#10-forwardref--useimperativehandle)
11. [自訂 Hook（Custom Hook）](#11-自訂-hookcustom-hook)
12. [Props 型別定義](#12-props-型別定義)
13. [事件處理型別](#13-事件處理型別)
14. [條件渲染](#14-條件渲染)
15. [環境變數（Vite）](#15-環境變數vite)
16. [常用 TypeScript 技巧](#16-常用-typescript-技巧)

---

## 1. TypeScript 基礎型別

```ts
// 基本型別
const name: string = "Alice";
const age: number = 30;
const active: boolean = true;

// 陣列
const names: string[] = ["A", "B"];
const ids: Array<number> = [1, 2, 3];

// Union（聯合型別）：值可以是多種型別之一
type Status = "idle" | "loading" | "success" | "error";
let s: Status = "loading";

// Nullable：允許 null 或 undefined
let user: string | null = null;

// Tuple：固定長度與型別的陣列
const pair: [string, number] = ["Alice", 30];

// Record：Key-Value 物件型別
const map: Record<string, number> = { a: 1, b: 2 };
```

---

## 2. 型別定義：type vs interface

```ts
// type：彈性高，可用 Union、交叉型別
type User = {
  id: string;
  name: string;
  email: string;
};

type AdminUser = User & { role: "admin" };  // 交叉型別（合併）

// interface：適合描述物件結構，可被 extends
interface Animal {
  name: string;
}
interface Dog extends Animal {
  breed: string;
}

// 實務上：React Props / 資料型別用 type，Class / 可擴充結構用 interface
```

> **選擇原則**：專案中統一用 `type` 即可，除非需要繼承或宣告合併。

---

## 3. 泛型 Generic

```ts
// 函式泛型：讓函式接受不特定型別，呼叫時再決定
function identity<T>(value: T): T {
  return value;
}
identity<string>("hello");  // 明確指定
identity(42);               // TypeScript 自動推斷為 number

// 泛型約束：限制 T 必須有某個屬性
function getLength<T extends { length: number }>(item: T): number {
  return item.length;
}

// 泛型在型別定義
type ApiResponse<T> = {
  data: T;
  status: number;
};

type UserResponse = ApiResponse<User>;
// 等同於 { data: User; status: number }
```

---

## 4. useState

```tsx
import { useState } from "react";

// 基本用法：TypeScript 自動推斷型別
const [count, setCount] = useState(0);          // number
const [name, setName]   = useState("Alice");    // string

// 明確指定型別（初始值為 null 時必須）
const [user, setUser] = useState<User | null>(null);

// 物件 state（更新時要展開原本的值）
const [form, setForm] = useState({ name: "", email: "" });
setForm((prev) => ({ ...prev, name: "Bob" }));  // 只更新 name

// 陣列 state
const [items, setItems] = useState<string[]>([]);
setItems((prev) => [...prev, "newItem"]);       // 新增
setItems((prev) => prev.filter((i) => i !== "target")); // 刪除

// functional update：新值依賴舊值時使用，避免 stale closure
const [count, setCount] = useState(0);
setCount((prev) => prev + 1);  // ✅ 正確
setCount(count + 1);           // ⚠️ 可能拿到過時的 count
```

---

## 5. useEffect

```tsx
import { useEffect } from "react";

// 依賴陣列（deps）決定執行時機
// ┌────────────────────────────────────────────────────┐
// │ deps 省略    │ 每次 render 後都執行               │
// │ deps = []   │ 只在 mount（第一次渲染）執行一次    │
// │ deps = [x]  │ x 改變時執行                        │
// └────────────────────────────────────────────────────┘

// mount 時執行（呼叫 API、初始化）
useEffect(() => {
  fetchData();
}, []);

// 某個值變更時執行
useEffect(() => {
  console.log("phase changed:", phase);
}, [phase]);

// cleanup：回傳函式，在下次執行前或 unmount 時呼叫
// 常用於移除事件監聽、取消訂閱
useEffect(() => {
  function handleKeyDown(e: KeyboardEvent) { ... }
  window.addEventListener("keydown", handleKeyDown);

  return () => {
    window.removeEventListener("keydown", handleKeyDown); // cleanup
  };
}, []);

// ⚠️ 常見錯誤：依賴陣列遺漏變數 → ESLint 的 exhaustive-deps 規則會提示
useEffect(() => {
  fetchData(phase); // phase 要加入 deps
}, [phase]);        // ✅
```

---

## 6. useRef

```tsx
import { useRef } from "react";

// 用途一：綁定 DOM 元素（不觸發 re-render）
const inputRef = useRef<HTMLInputElement>(null);
// 在 JSX 中：<input ref={inputRef} />
inputRef.current?.focus(); // 呼叫 DOM 方法

// 用途二：儲存不需要觸發 re-render 的值
// （類似 class component 的 instance variable）
const timerRef = useRef<number | null>(null);
timerRef.current = window.setTimeout(() => {}, 1000);

// 用途三：儲存 ref 物件讓跨 render 共享（不用 state）
const dragRef = useRef({ dragging: false, startX: 0 });
dragRef.current.dragging = true; // 直接修改，不觸發 re-render

// 與 useState 的差異
// useState → 改變會觸發 re-render，用於畫面顯示
// useRef   → 改變不觸發 re-render，用於內部追蹤
```

---

## 7. useMemo

```tsx
import { useMemo } from "react";

// 快取運算結果，只有在依賴值改變時才重新計算
// 適用於：昂貴的過濾、排序、轉換運算

const filteredList = useMemo(() => {
  return items.filter((item) => item.includes(keyword));
}, [items, keyword]); // items 或 keyword 改變才重算

// Set 也適合用 useMemo 包裝（避免每次 render 建立新物件）
const matchedIds = useMemo(
  () => new Set(matchedItems.map((m) => m.id)),
  [matchedItems]
);

// ⚠️ 不要過度使用：簡單計算直接寫即可，useMemo 本身也有開銷
// ✅ 適合：大量資料過濾、複雜轉換、傳給子元件的物件/陣列（搭配 React.memo）
```

---

## 8. useCallback

```tsx
import { useCallback } from "react";

// 快取函式參考，只有依賴值改變時才建立新函式
// 主要用途：避免子元件因父層 re-render 而不必要地重新渲染

const handleClick = useCallback(() => {
  doSomething(id);
}, [id]); // id 不變 → 函式參考不變 → 子元件不會重新渲染

// 與 useMemo 的關係
// useMemo(() => fn, deps)    ← 快取「fn 的回傳值」
// useCallback(fn, deps)      ← 快取「fn 本身」
// useCallback(fn, deps) 等同於 useMemo(() => fn, deps)

// 常見搭配：useEffect 的依賴中有函式時
const fetchData = useCallback(async () => {
  const data = await api.get(phase);
  setItems(data);
}, [phase]);

useEffect(() => {
  fetchData();
}, [fetchData]); // fetchData 是穩定參考，只有 phase 變時重跑
```

---

## 9. useContext + createContext

```tsx
import { createContext, useContext } from "react";

// Step 1：定義 Context 的型別
type ThemeState = {
  theme: "light" | "dark";
  toggle: () => void;
};

// Step 2：建立 Context（初始值通常給 null）
// 泛型 <ThemeState | null> 允許「還沒被 Provider 包住」的情況
const ThemeContext = createContext<ThemeState | null>(null);

// Step 3：建立 Provider 元件，管理 state 並注入
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const toggle = () => setTheme((t) => t === "light" ? "dark" : "light");

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Step 4：自訂 Hook，統一取用並做 null 檢查
export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  // null 代表使用者忘記包 <ThemeProvider>，在開發階段立刻報錯
  if (!ctx) throw new Error("useTheme must be used inside <ThemeProvider>");
  return ctx;
}

// Step 5：在元件中使用
function MyButton() {
  const { theme, toggle } = useTheme();
  return <button onClick={toggle}>{theme}</button>;
}

// Step 6：在 App 最外層包上 Provider
function App() {
  return (
    <ThemeProvider>
      <MyButton />
    </ThemeProvider>
  );
}
```

---

## 10. forwardRef + useImperativeHandle

```tsx
import { forwardRef, useImperativeHandle, useRef } from "react";

// 問題：父元件有時需要直接呼叫子元件的方法（如 focus、scroll）
// 解法：forwardRef 讓父層的 ref 傳入子元件；
//       useImperativeHandle 決定對外暴露哪些方法

// 定義對外暴露的 handle 型別
type InputHandle = {
  focus: () => void;
  clear: () => void;
};

// 用 forwardRef 包裝子元件
const FancyInput = forwardRef<InputHandle, { placeholder: string }>(
  function FancyInput({ placeholder }, ref) {
    const inputRef = useRef<HTMLInputElement>(null);

    // 決定父層透過 ref 能呼叫哪些方法
    useImperativeHandle(ref, () => ({
      focus: () => inputRef.current?.focus(),
      clear: () => { if (inputRef.current) inputRef.current.value = ""; },
    }));

    return <input ref={inputRef} placeholder={placeholder} />;
  }
);

// 父元件：拿到 handle 後呼叫子元件方法
function Parent() {
  const inputRef = useRef<InputHandle>(null);

  return (
    <>
      <FancyInput ref={inputRef} placeholder="輸入..." />
      <button onClick={() => inputRef.current?.focus()}>聚焦</button>
      <button onClick={() => inputRef.current?.clear()}>清空</button>
    </>
  );
}
```

---

## 11. 自訂 Hook（Custom Hook）

```tsx
// 命名規則：必須以 use 開頭，才能使用其他 Hook

// 範例：封裝非同步操作狀態
function useAsync<T, Args extends unknown[]>(
  fn: (...args: Args) => Promise<T>,
  onError?: (error: Error) => void,
) {
  const [loading, setLoading] = useState(false);
  const [data, setData]       = useState<T | null>(null);
  const [error, setError]     = useState<Error | null>(null);

  // mountedRef：防止 unmount 後仍呼叫 setState（記憶體洩漏）
  const mountedRef = useRef(true);
  useEffect(() => () => { mountedRef.current = false; }, []);

  const execute = useCallback(async (...args: Args) => {
    setLoading(true);
    try {
      const result = await fn(...args);
      if (mountedRef.current) setData(result);
      return result;
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      if (mountedRef.current) { setError(err); onError?.(err); }
      return null;
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [fn]);

  return { execute, loading, data, error };
}

// 使用
const { execute: fetchUsers, loading, data } = useAsync(getUsers);
```

---

## 12. Props 型別定義

```tsx
// 基本 Props
type ButtonProps = {
  label: string;
  onClick: () => void;
  disabled?: boolean;   // ? 代表可選
};

// children：接受 React 子元素
type CardProps = {
  title: string;
  children: React.ReactNode;  // 可以是任何 React 內容
};

// 事件 handler Props
type InputProps = {
  value: string;
  onChange: (value: string) => void;       // 自訂參數
  onKeyDown?: (e: React.KeyboardEvent) => void; // 原生事件
};

// 繼承原生 HTML 屬性（常用於封裝 HTML 元素）
type MyInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string; // 額外加上自訂屬性
};

// 在元件中解構使用
function Button({ label, onClick, disabled = false }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}
```

---

## 13. 事件處理型別

```tsx
// 常用事件型別
// React.MouseEvent<T>      滑鼠事件
// React.KeyboardEvent<T>   鍵盤事件
// React.ChangeEvent<T>     輸入變更事件
// React.FocusEvent<T>      聚焦事件
// React.FormEvent<T>       表單事件

function MyInput() {
  // ChangeEvent：取得 input 的值
  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    console.log(e.target.value);
  }

  // KeyboardEvent：判斷按鍵
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") { ... }
    if (e.key === "Escape") { ... }
    if (e.key === "ArrowDown") {
      e.preventDefault(); // 阻止預設行為（如頁面捲動）
    }
  }

  // MouseEvent：取得座標
  function handleMouseDown(e: React.MouseEvent<HTMLDivElement>) {
    const x = e.clientX;
    const y = e.clientY;
    e.preventDefault(); // 阻止 focus 離開當前元素（常用於自訂 dropdown）
  }

  return (
    <input
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      onMouseDown={handleMouseDown}
    />
  );
}
```

---

## 14. 條件渲染

```tsx
// 方式一：&& 短路（條件為 false 時不渲染）
{isLoggedIn && <Dashboard />}

// ⚠️ 陷阱：數字 0 會被渲染出來
{count && <Badge />}   // ❌ count=0 時畫面出現 "0"
{count > 0 && <Badge />} // ✅

// 方式二：三元運算子
{isLoading ? <Spinner /> : <Content />}

// 方式三：提前 return（Guard Clause）
function MyPage() {
  if (loading) return <div>載入中…</div>;
  if (!user)   return <Navigate to="/login" />;
  return <div>{user.name}</div>;
}

// 方式四：cn() 工具函式做條件樣式
// cn 通常是 clsx 或類似工具，合併 className 並過濾 falsy 值
import { cn } from "../utils/clsx";

<button
  className={cn(
    "px-4 py-2 rounded",           // 永遠套用
    isActive && "bg-blue-500",     // 條件套用
    disabled && "opacity-50 cursor-not-allowed"
  )}
>
  Click
</button>
```

---

## 15. 環境變數（Vite）

```ts
// Vite 使用 import.meta.env 讀取環境變數
// 只有 VITE_ 前綴的變數才會暴露給前端

// .env.development
// VITE_APP_ENV=DEV
// VITE_API_BASE=http://localhost:8080

// 讀取
const env    = import.meta.env.VITE_APP_ENV;   // string | undefined
const apiUrl = import.meta.env.VITE_API_BASE ?? ""; // ?? 給預設值

// ?? vs ||（Nullish Coalescing vs OR）
// ?? 只在左側是 null / undefined 時取右側
// || 在左側是任何 falsy（"", 0, false）時都取右側
const url = import.meta.env.VITE_API_BASE ?? "";  // ✅ 空字串不會被覆蓋
const url2 = import.meta.env.VITE_API_BASE || ""; // ⚠️ 空字串也會被覆蓋

// TypeScript 型別補強（vite-env.d.ts）
interface ImportMetaEnv {
  readonly VITE_APP_ENV: "DEV" | "STAGE" | "PROD";
  readonly VITE_API_BASE: string;
}
```

---

## 16. 常用 TypeScript 技巧

### Optional Chaining `?.`
```ts
// 安全地存取可能是 null/undefined 的屬性或方法
const city = user?.address?.city;     // user 或 address 為 null → undefined
const len  = arr?.length;             // arr 為 null → undefined
ref.current?.focus();                  // ref.current 為 null → 什麼都不做
```

### Non-null Assertion `!`
```ts
// 告訴 TypeScript「我確定這裡不是 null」（慎用）
const value = map.get(key)!;  // 確定 key 存在
canvas.getContext("2d")!;     // 確定環境支援
```

### Type Assertion `as`
```ts
// 強制轉型（確定型別時使用，不做實際轉換）
const input = e.target as HTMLInputElement;
const env = import.meta.env.VITE_APP_ENV as "DEV" | "STAGE" | "PROD";
```

### `typeof` / `keyof` / `as const`
```ts
// as const：讓物件/陣列變成唯讀的字面型別
const PHASES = ["DEV", "STAGE", "PROD"] as const;
type Phase = typeof PHASES[number]; // "DEV" | "STAGE" | "PROD"

// keyof：取得物件所有 key 的 Union 型別
type Config = { host: string; port: number };
type ConfigKey = keyof Config; // "host" | "port"
```

### Partial / Required / Pick / Omit
```ts
type User = { id: string; name: string; email: string };

type PartialUser  = Partial<User>;         // 全部屬性變可選
type RequiredUser = Required<PartialUser>; // 全部屬性變必填
type NameOnly     = Pick<User, "name">;    // 只取 name
type WithoutId    = Omit<User, "id">;      // 排除 id
```

### Type Guard（型別守衛）
```ts
// 用 is 關鍵字在 if 內縮小型別範圍
function isError(value: unknown): value is Error {
  return value instanceof Error;
}

try { ... } catch (e) {
  const err = e instanceof Error ? e : new Error(String(e));
  console.error(err.message);
}

// filter 搭配 type guard 去掉 null
const values = [1, null, 2, undefined, 3];
const numbers = values.filter((v): v is number => v !== null && v !== undefined);
// numbers 的型別是 number[]，不是 (number | null | undefined)[]
```

---

> 本文件依據專案實際使用的語法整理，範例均來自真實程式碼情境。
