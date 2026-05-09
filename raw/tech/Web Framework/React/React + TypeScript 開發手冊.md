# React + TypeScript 開發手冊

> 適用對象：有 JavaScript / React 基礎，正在轉型 TypeScript 的開發者。
後端搭配：ASP.NET Core Web API
> 

---

## 目錄

1. [TypeScript 核心語法速查](about:blank#1-typescript-%E6%A0%B8%E5%BF%83%E8%AA%9E%E6%B3%95%E9%80%9F%E6%9F%A5)
2. [TypeScript 在 React 中的型別應用](about:blank#2-typescript-%E5%9C%A8-react-%E4%B8%AD%E7%9A%84%E5%9E%8B%E5%88%A5%E6%87%89%E7%94%A8)
3. [React 核心概念與 Hooks](about:blank#3-react-%E6%A0%B8%E5%BF%83%E6%A6%82%E5%BF%B5%E8%88%87-hooks)
4. [狀態管理 (Zustand)](about:blank#4-%E7%8B%80%E6%85%8B%E7%AE%A1%E7%90%86-zustand)
5. [API 串接與 ASP.NET Core 後端整合](about:blank#5-api-%E4%B8%B2%E6%8E%A5%E8%88%87-aspnet-core-%E5%BE%8C%E7%AB%AF%E6%95%B4%E5%90%88)
6. [專案結構建議](about:blank#6-%E5%B0%88%E6%A1%88%E7%B5%90%E6%A7%8B%E5%BB%BA%E8%AD%B0)
7. [常見錯誤與對策](about:blank#7-%E5%B8%B8%E8%A6%8B%E9%8C%AF%E8%AA%A4%E8%88%87%E5%B0%8D%E7%AD%96)

---

## 1. TypeScript 核心語法速查

### 1.1 基本型別與函式

**基本型態**

```tsx
// 原始型別
const name: string = "Alice";
const age: number = 30;
const isActive: boolean = true;
const nothing: null = null;
const undef: undefined = undefined;

// 陣列
const ids: number[] = [1, 2, 3];
const names: Array<string> = ["Alice", "Bob"];

// Tuple (固定長度 + 型別的陣列)
const point: [number, number] = [10, 20];
```

 **Function 定義方式**

```tsx
// 基本函式定義
function add(a, b) {
  return a + b;
}

// 物件格式定義函式
const add = function (a, b) {
  return a + b;
};

// 箭頭函式定義
const add = (a, b) => a + b;

// IIFE（立即執行函式）
(function () {
  console.log("run immediately");
})();
```

**函式參數定義方式**

```tsx
type SquareProps = {
  value: string;
};

// 以下方法效果相同
function Square(props: SquareProps) {}
function Square({ value }: SquareProps) {}
const Square = ({ value }: SquareProps) => {}

<Square value="1" />
```

### 1.2 物件型別與 Interface vs Type

```tsx
// Interface: 適合描述物件結構，可以被 extends
interface User {
  id: number;
  name: string;
  email?: string; // ? 表示 nullable
}

// Type Alias: 更彈性，可以描述 Union、Intersection
type Status = "active" | "inactive" | "pending"; // Union Type

// 用 "&" 合併兩個型別
type AdminUser = User & { role: string }; // Intersection Type

// AdminUser 長得就像這樣
type AdminUser = {
  id: number;
  name: string;
  email: string;
  role: string;  // 多了這個
}
```

<aside>
💡

實務建議：物件結構用 Interface，Union / 組合型別用 Type

</aside>

### 1.3 函式型別

```tsx
// 一般函式
function add(a: number, b: number): number {
  return a + b;
}

// Arrow Function
const multiply = (a: number, b: number): number => a * b;

// 選填參數與預設值
function greet(name: string, greeting: string = "Hello"): string {
  return `${greeting},${name}`;
}

// 回傳 void (不回傳值)
const logMessage = (msg: string): void => {
  console.log(msg);
};
```

### 1.4 泛型 (Generics)

```tsx
// 最常用的概念：讓函式或型別可以適用多種型別，又保有型別安全
function identity<T>(value: T): T {
  return value;
}

identity<string>("hello"); // 回傳 string
identity<number>(42);       // 回傳 number

// 泛型 Interface
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message: string;
}

// 用法
type UserResponse = ApiResponse<User>;
type UserListResponse = ApiResponse<User[]>;
```

### 1.5 型別縮窄 (Type Narrowing)

```tsx
// TypeScript 會根據條件判斷縮小型別範圍
function printId(id: string | number) {
  if (typeof id === "string") {
    console.log(id.toUpperCase()); // 這裡 TypeScript 知道是 string
  } else {
    console.log(id.toFixed(2));   // 這裡 TypeScript 知道是 number
  }
}
```

### 1.6 Utility Types (常用內建工具型別)

```tsx
interface User {
  id: number;
  name: string;
  email: string;
  password: string;
}

// Partial: 所有欄位變成可選
type UpdateUserDto = Partial<User>;

// Pick: 只取部分欄位
type UserProfile = Pick<User, "id" | "name" | "email">;

// Omit: 排除某些欄位
type PublicUser = Omit<User, "password">;

// Required: 所有欄位變成必填
type StrictUser = Required<Partial<User>>;

// Readonly: 所有欄位變成唯讀
type ImmutableUser = Readonly<User>;
```

### 1.7 Spread / Rest 運算子

> 打散（Spread）用在「放進去」的地方
收集（Rest）：用在「接收」的地方
> 

| 情境 | 語法 | 作用 |
| --- | --- | --- |
| 合併陣列 | `[...a, ...b]` | Spread 打散再合併 |
| 複製物件 | `{ ...obj }` | **Spread 淺複製** |
| 更新物件欄位 | `{ ...obj, key: val }` | Spread + 覆蓋 |
| 不定數量參數 | `fn(...args: T[])` | Rest 收集 |
| 解構剩餘欄位 | `const { a, ...rest }` | Rest 收集剩餘 |
| 傳入 props | `<Comp {...props} />` | Spread 打散傳入 |

**一、Spread 打散陣列**

```tsx
const a = [1, 2, 3];
const b = [4, 5, 6];

// 合併陣列
const combined = [...a, ...b];
// 結果：[1, 2, 3, 4, 5, 6]

// 複製陣列（建立新陣列，不影響原本的）
const copy = [...a];
// 結果：[1, 2, 3]，但是全新的陣列

// 在特定位置插入
const inserted = [...a, 99, ...b];
// 結果：[1, 2, 3, 99, 4, 5, 6]
```

<aside>
💡

因為 React 要求你不能直接修改 state，必須給它一個**新的陣列**：

```tsx
const [users, setUsers] = useState<User[]>([]);

// 新增一個 user
setUsers(prev => [...prev, newUser]); // 建立新陣列，最後加入 newUser

// 刪除一個 user（過濾掉 id = 3 的）
setUsers(prev => prev.filter(u => u.id !== 3));
```

</aside>

**二、Spread 打散物件**

```tsx
const user = { id: 1, name: "Alice", email: "a@a.com" };

// 複製物件
const copy = { ...user };

// 複製並覆蓋某個欄位
const updated = { ...user, name: "Bob" };
// 結果：{ id: 1, name: "Bob", email: "a@a.com" }
// 後面的 name 會蓋掉前面的 name

// 合併兩個物件
const extra = { role: "admin", age: 30 };
const merged = { ...user, ...extra };
// 結果：{ id: 1, name: "Alice", email: "a@a.com", role: "admin", age: 30 }
```

這就是 `AdminUser = User & { role: string }` 在執行時的樣子：

```tsx
// 型別定義（告訴 TypeScript 結構長什麼樣）
type AdminUser = User & { role: string };

// 實際建立物件（執行時合併資料）
const adminUser: AdminUser = { ...user, role: "admin" };
```

在 React state 更新物件時也很常用：

```tsx
const [user, setUser] = useState<User>({ id: 1, name: "Alice", email: "a@a.com" });

// 只更新 name，保留其他欄位
setUser(prev => ({ ...prev, name: "Bob" }));
//              ↑ 注意：箭頭函式回傳物件要用 () 包起來，否則 {} 會被誤認為函式 body
```

**三、Rest 收集函式參數**

> **Rest**  方向相反，把「多個參數」收集成一個**陣列**
(概念類似 C# 函式最後可以放 param)
> 

```tsx
// 不知道會傳幾個數字進來，全部收集成陣列
function sum(...numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}

sum(1, 2, 3);       // 6
sum(1, 2, 3, 4, 5); // 15

// 前面的參數正常接，剩下的用 rest 收集
function log(level: string, ...messages: string[]): void {
  console.log(`[${level}]`, messages.join(" "));
}

log("INFO", "User", "logged", "in");
// 印出：[INFO] User logged in
```

**四、Rest 解構賦值（最常搞混的地方）**

```tsx
// 陣列解構 + Rest
const [first, second, ...rest] = [1, 2, 3, 4, 5];
// first = 1, second = 2, rest = [3, 4, 5]

// 物件解構 + Rest（React Component 很常用）
const { id, name, ...otherProps } = user;
// id = 1, name = "Alice"
// otherProps = { email: "a@a.com" }
```

在 React Component 裡的實際場景：

```tsx
interface ButtonProps {
  label: string;
  variant?: "primary" | "danger";
  onClick: () => void;
  disabled?: boolean;
}

const Button = ({ label, variant = "primary", ...rest }: ButtonProps) => {
  // label 和 variant 單獨拿出來用
  // onClick、disabled 等其他 props 用 rest 收集
  return (
    <button className={`btn-${variant}`} {...rest}>
      {label}
    </button>
    // ↑ 這裡又用 Spread 把 rest 打散，傳給原生 button
  );
};
```

這個模式特別重要，Component 先「Rest 收集」剩餘的 props，再「Spread 打散」傳給底層元素，是封裝 UI 元件的常見技巧。

### 1.8 淺複製 vs. 深複製

```tsx
const user = {
  id: 1,
  name: "Alice",
  address: {
    city: "台北",
    zip: "100"
  }
};

const copy = { ...user };

// 修改 copy 的 city
copy.address.city = "台中";

// 請問：user.address.city 現在是什麼？
console.log(user.address.city); // "台北" 還是 "台中"？(A:台中)
```

```tsx
const copy = { ...user };

```
Spread 做的事是：**把每個抽屜的內容**連同位置**複製一份**。
```
user.id      → 1          copy.id      → 1         (複製數字，獨立的)
user.name    → "Alice"    copy.name    → "Alice"    (複製字串，獨立的)
user.address → "0x001"    copy.address → "0x001"    (複製位址，指向同一個地方！)
```

所以 `user.address` 和 `copy.address` 指向**同一個物件**，
指向**同一個物件**代表著只要改其中一個，另一個也跟著變。

---

## 深複製解決什麼問題

深複製會把整個結構**完整複製一份**，包含裡面的物件：
```
user.address → "0x001"    copy.address → "0x002"    (不同位址，完全獨立)
                ↓                          ↓
        { city: "台北" }          { city: "台北" }   (兩份獨立的資料)
```

實際寫法比較

```tsx
const user = {
  id: 1,
  name: "Alice",
  address: {
    city: "台北",
    zip: "100"
  }
};

// 淺複製，address 還是共用的
const shallowCopy = { ...user };

// 深複製方式 1：手動展開每一層（簡單情境用這個）
const deepCopy1 = {
  ...user,
  address: { ...user.address }  // 把 address 也展開一層
};

// 深複製方式 2：JSON 轉換（簡單但有限制）
const deepCopy2 = JSON.parse(JSON.stringify(user));
// 限制：無法複製 function、Date 物件、undefined 等特殊值

// 深複製方式 3：structuredClone（現代瀏覽器推薦）
const deepCopy3 = structuredClone(user);
```

|  | 淺複製 | 深複製 |
| --- | --- | --- |
| 第一層 | 獨立 | 獨立 |
| 巢狀物件 | 共用（同一個參考） | 獨立（完整複製） |
| 寫法 | `{ ...obj }` | `structuredClone(obj)` |
| React 使用 | 大多數情況夠用，巢狀要手動展開 | 資料結構很深時才需要 |

---

## 2. TypeScript 在 React 中的型別應用

### 2.1 Component Props 型別

```tsx
// 使用 Interface 定義 Props (推薦)
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}

const Button = ({ label, onClick, variant = "primary", disabled = false }: ButtonProps) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {label}
    </button>
  );
};

// 使用方式
<Button label="送出" onClick={() => console.log("clicked")} />
<Button label="刪除" onClick={handleDelete} variant="danger" />
```

### 2.2 包含 children 的 Component

```tsx
import { ReactNode } from "react";

interface CardProps {
  title: string;
  children: ReactNode; // 接受任何 JSX 內容
}

const Card = ({ title, children }: CardProps) => {
  return (
    <div className="card">
      <h2>{title}</h2>
      <div className="card-body">{children}</div>
    </div>
  );
};

// 使用方式
<Card title="用戶資訊">
  <p>這裡可以放任何內容</p>
</Card>
```

### 2.3 Event Handler 型別

```tsx
import { ChangeEvent, FormEvent, MouseEvent } from "react";

const Form = () => {
  // input 的 onChange
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    console.log(e.target.value);
  };

  // textarea 的 onChange
  const handleTextareaChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    console.log(e.target.value);
  };

  // select 的 onChange
  const handleSelectChange = (e: ChangeEvent<HTMLSelectElement>) => {
    console.log(e.target.value);
  };

  // form submit
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // 處理送出
  };

  // button click
  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    console.log("clicked");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input onChange={handleInputChange} />
      <button onClick={handleClick} type="submit">送出</button>
    </form>
  );
};
```

---

## 3. React 核心概念與 Hooks

### 3.1 useState

> `useState` 是跨 render 存活，且改變會影響畫面的資料
> 

```tsx
const [count, setCount] = useState(0);
```

- state 不是變數，是 React 管理的記憶槽，
- 用 setState 指派會觸發 re-render
- state 更新是非同步、批次的

<aside>
💡

資料改變後，畫面需不需要跟著變

- 需要 → `useState`
- 不需要 → `const`
</aside>

- 每次 render 都會重新計算 `const`
- 改變 `const`  **不會觸發 re-render**
- render 結束後`const` 就消失

```tsx
import { useState } from "react";

interface User {
  id: number;
  name: string;
}

const UserComponent = () => {
  // 基本型別，TypeScript 會自動推斷
  const [count, setCount] = useState(0);
  const [name, setName] = useState("");

  // 物件型別，明確標注
  const [user, setUser] = useState<User | null>(null);

  // 陣列型別
  const [users, setUsers] = useState<User[]>([]);

  // 更新物件 (記得展開舊的 state)
  const updateUserName = (newName: string) => {
    setUser(prev => prev ? { ...prev, name: newName } : null);
  };

  return <div>{user?.name}</div>;
};
```

### 3.2 useEffect

> state 改變 →render（計算 JSX、useMemo、變數）→畫面更新（DOM commit）→ useEffect
> 

```tsx
useEffect(() => { ... }, []);
// 只有在 mount (初始化) 時跑一次，以後都不跑

useEffect(() => { ... }, [x]);
// x 改變後跑

useEffect(() => { ... });
// 每次 render 後都跑

// 依賴陣列(Dependent Array)
// []	只在 mount / unmount (第一次render)
// [a,b]	a"或"b 改變才重跑
// 不寫	每次 render 都跑
```

<aside>
💡

**精神：**Dependent Array (要偵測的東西)改變的時候才跑

</aside>

```tsx
import { useState, useEffect } from "react";

const DataFetcher = ({ userId }: { userId: number }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 每次 userId 變化就重新執行
    const fetchUser = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/users/${userId}`);
        if (!res.ok) throw new Error("載入失敗");
        const data: User = await res.json();
        setUser(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "未知錯誤");
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]); // 依賴陣列：userId 變化時重跑

  if (loading) return <p>載入中...</p>;
  if (error) return <p>錯誤：{error}</p>;
  return <p>{user?.name}</p>;
};
```

**useEffect 的 Cleanup (清理)**

```tsx
useEffect(() => {
  const timer = setInterval(() => {
    console.log("tick");
  }, 1000);

  // 回傳 cleanup function，在 component 卸載或下次 effect 執行前呼叫
  return () => clearInterval(timer);
}, []);
```

### 3.3 useCallback 與 useMemo

> **useMemo**
避免物件 / 陣列每次 render 都變新 reference
精神：每次Render時，先判斷偵測的東西改變的時候才跑
> 

```tsx
const value = useMemo(() => heavyCalc(x), [x]);
// render 時先檢查 x 有沒有變，有變才重新計算heavyCalc(x)，沒變用舊的結果

// 錯誤用法
useMemo(() => 1 + 1, []); // 沒意義
```

> 
> 
> 
> **useCallback**
> 用來在 render 階段「記住一個函式 reference」，避免在不必要的 render 中產生新函式。
> 
> 防止 child component 因 function reference 改變而 re-render
> 

```tsx
useCallback = useMemo(() => fn)
```

```tsx
const handleSelect = useCallback((value: string) => {
  setSelected(value);
}, []);
// render 時，如果 dependencies 沒變，沿用同一個 handleSelect 函式 reference

const handleAdd = useCallback(() => {
  setCount(count + 1);
}, [count]);
// 當 count 改變時，重新建立 handleAdd 函式，確保使用最新的 count
```

- 搭配 `memo`

```tsx
const Child = React.memo(({ onClick }: { onClick: () => void }) => {
  return <button onClick={onClick}>Click</button>;
});

const onClick = useCallback(() => {
  console.log("clicked");
}, []);
// 確保 onClick 不因父元件 render 而變成新函式
```

範例

```tsx
import { useState, useCallback, useMemo } from "react";

const ExpensiveComponent = () => {
  const [count, setCount] = useState(0);
  const [name, setName] = useState("");

  // useMemo: 快取計算結果，只在 count 變化時重新計算
  const expensiveValue = useMemo(() => {
    console.log("重新計算");
    return count * 1000; // 假設這是很耗時的計算
  }, [count]);

  // useCallback: 快取函式，避免每次 render 產生新的函式參考
  // 適合用在傳給子 component 的 callback，避免子 component 不必要的 re-render
  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []); // 沒有依賴，函式永遠不會改變

  return (
    <div>
      <p>計算結果: {expensiveValue}</p>
      <ChildComponent onClick={handleClick} />
    </div>
  );
};
```

### 3.4 useRef

> `useRef` 是 React 的 Hook，它回傳一個可變的 ref 物件，這個物件有一個 `.current` 屬性。它有兩個主要用途：
> 
> - **存取 DOM 元素**
> - **儲存不需要觸發重新渲染的值**

```tsx
// 操作 DOM
const canvasRef = useRef<HTMLCanvasElement | null>(null);

//存「不影響 UI 的狀態」
const viewRef = useRef({
  offsetX: 0,
  offsetY: 0,
  scale: 1,
});

viewRef.current.scale++;
```

<aside>
💡

**關鍵特性：**修改 `.current` 不會觸發元件重新渲染。

</aside>

**用途一：存取 DOM 元素**

最常見的用法，直接操作 DOM，例如讓輸入框自動聚焦。

```tsx
import { useRef, useEffect } from 'react';

function LoginForm() {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
	  // 使用前要檢查 null
    inputRef.current?.focus(); // 頁面載入後自動聚焦
  }, []);

  return <input ref={inputRef} type="text" placeholder="請輸入帳號" />;
}
```

**流程說明：**

1. `useRef(null)` 建立 ref，初始值為 `null`
2. **將 `ref={inputRef}` 綁定到 DOM 元素**
3. React 渲染後，`inputRef.current` 就會指向那個真實的 DOM 節點

**用途二：儲存不觸發渲染的值**

> 當你需要記住某個值，但不希望它改變時畫面重新渲染，就用 useRef。
> 

```tsx
import { useRef, useState } from 'react';

function Timer() {
  const [count, setCount] = useState(0);
  const intervalRef = useRef<HTMLInputElement|null>(null); // 儲存 timer ID

  const start = () => {
    intervalRef.current = setInterval(() => {
      setCount(prev => prev + 1);
    }, 1000);
  };

  const stop = () => {
    clearInterval(intervalRef.current); // 用 ref 取得 timer ID 來清除
  };

  return (
    <div>
      <p>計數：{count}</p>
      <button onClick={start}>開始</button>
      <button onClick={stop}>停止</button>
    </div>
  );
}
```

**為什麼不用 `useState` 存 timer ID？**

因為 `setIntervalId(id)` 會觸發重新渲染，而我們只是要記住這個 ID，根本不需要渲染，用 `useRef` 更合適。

## `useRef` vs `useState` 比較

| 特性 | `useRef` | `useState` |
| --- | --- | --- |
| 修改後觸發渲染 | 不會 | 會 |
| 適合存畫面資料 | 不適合 | 適合 |
| 適合存內部狀態/計時器 | 適合 | 不適合 |
| 跨渲染保留值 | 會保留 | 會保留 |

## 常見錯誤提醒

**錯誤 1：在渲染期間讀取 `ref.current`**

```tsx
// 錯誤做法
function Bad() {
  const ref = useRef(0);
  ref.current = ref.current + 1; // 直接在渲染中修改，行為不可預期
  return <p>{ref.current}</p>;
}
```

`ref.current` 的修改應該放在 `useEffect` 或事件處理函式內，不要在渲染邏輯中直接讀寫。

**錯誤 2：把需要顯示的資料存在 `useRef`**

```tsx
// 錯誤做法，畫面不會更新
const nameRef = useRef('');
nameRef.current = '新名字'; // 畫面不會重新渲染，使用者看不到變化
```

需要顯示在畫面上的資料，一定要用 `useState`。

---

## 總結

`useRef` 的核心思維是：**「我需要記住這個東西，但它的變化不需要更新畫面。」**

掌握這個判斷原則，你就能在 `useRef` 和 `useState` 之間做出正確選擇。

### 3.5 useReducer (複雜狀態邏輯)

```tsx
import { useReducer } from "react";

// 定義狀態型別
interface CartState {
  items: CartItem[];
  total: number;
}

interface CartItem {
  id: number;
  name: string;
  quantity: number;
  price: number;
}

// 定義 Action 型別 (Union Type 是關鍵)
type CartAction =
  | { type: "ADD_ITEM"; payload: CartItem }
  | { type: "REMOVE_ITEM"; payload: { id: number } }
  | { type: "CLEAR_CART" };

// Reducer 函式
const cartReducer = (state: CartState, action: CartAction): CartState => {
  switch (action.type) {
    case "ADD_ITEM":
      return {
        ...state,
        items: [...state.items, action.payload],
        total: state.total + action.payload.price * action.payload.quantity,
      };
    case "REMOVE_ITEM":
      const item = state.items.find(i => i.id === action.payload.id);
      return {
        ...state,
        items: state.items.filter(i => i.id !== action.payload.id),
        total: state.total - (item ? item.price * item.quantity : 0),
      };
    case "CLEAR_CART":
      return { items: [], total: 0 };
    default:
      return state;
  }
};

const Cart = () => {
  const [cart, dispatch] = useReducer(cartReducer, { items: [], total: 0 });

  return (
    <div>
      <p>總計: {cart.total}</p>
      <button onClick={() => dispatch({ type: "CLEAR_CART" })}>清空購物車</button>
    </div>
  );
};
```

### 3.6 useContext (跨層傳遞資料)

```tsx
import { createContext, useContext, useState, ReactNode } from "react";

// 1. 定義 Context 型別
interface AuthContextType {
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
}

// 2. 建立 Context (給一個預設值或 undefined)
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 3. 建立 Provider Component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = (user: User) => setUser(user);
  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// 4. 建立自訂 Hook 安全存取 Context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth 必須在 AuthProvider 內使用");
  }
  return context;
};

// 5. 在任何子 Component 使用
const Header = () => {
  const { user, logout } = useAuth();
  return (
    <header>
      <span>{user?.name}</span>
      <button onClick={logout}>登出</button>
    </header>
  );
};
```

### 3.7 自訂 Hook

自訂 Hook 是提取可重用邏輯的最佳方式，命名規則是 `use` 開頭。

```tsx
import { useState, useCallback } from "react";

// 通用資料載入 Hook
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP Error:${res.status}`);
      const json: T = await res.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  }, [url]);

  return { data, loading, error, fetchData };
}

// 使用自訂 Hook
const UserList = () => {
  const { data: users, loading, error, fetchData } = useFetch<User[]>("/api/users");

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <p>載入中...</p>;
  if (error) return <p>錯誤：{error}</p>;
  return <ul>{users?.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
};
```

---

## 4. 狀態管理 (Zustand)

Zustand 是輕量的全域狀態管理工具，比 Redux 簡潔很多，適合中小型專案。

### 4.1 安裝

```bash
npm install zustand
```

### 4.2 建立 Store

```tsx
// stores/useUserStore.ts
import { create } from "zustand";

interface User {
  id: number;
  name: string;
  email: string;
}

interface UserState {
  // 狀態
  currentUser: User | null;
  users: User[];
  isLoading: boolean;

  // Actions (操作方法)
  setCurrentUser: (user: User | null) => void;
  setUsers: (users: User[]) => void;
  addUser: (user: User) => void;
  removeUser: (id: number) => void;
  setLoading: (loading: boolean) => void;
}

export const useUserStore = create<UserState>((set) => ({
  // 初始狀態
  currentUser: null,
  users: [],
  isLoading: false,

  // Actions
  setCurrentUser: (user) => set({ currentUser: user }),
  setUsers: (users) => set({ users }),
  addUser: (user) => set((state) => ({ users: [...state.users, user] })),
  removeUser: (id) =>
    set((state) => ({ users: state.users.filter((u) => u.id !== id) })),
  setLoading: (isLoading) => set({ isLoading }),
}));
```

### 4.3 在 Component 中使用

```tsx
// components/UserList.tsx
import { useUserStore } from "../stores/useUserStore";

const UserList = () => {
  // 只取需要的狀態 (效能最佳化：只在 users 變化時 re-render)
  const users = useUserStore((state) => state.users);
  const removeUser = useUserStore((state) => state.removeUser);

  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>
          {user.name}
          <button onClick={() => removeUser(user.id)}>刪除</button>
        </li>
      ))}
    </ul>
  );
};
```

### 4.4 搭配 API 的非同步操作 (進階)

```tsx
// stores/useUserStore.ts (加入非同步 action)
import { create } from "zustand";
import { userApi } from "../api/userApi";

interface UserState {
  users: User[];
  isLoading: boolean;
  error: string | null;
  fetchUsers: () => Promise<void>;
}

export const useUserStore = create<UserState>((set) => ({
  users: [],
  isLoading: false,
  error: null,

  fetchUsers: async () => {
    set({ isLoading: true, error: null });
    try {
      const users = await userApi.getAll();
      set({ users, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "載入失敗",
        isLoading: false,
      });
    }
  },
}));
```

---

## 5. API 串接與 ASP.NET Core 後端整合

### 5.1 建立 API 型別定義

```tsx
// types/api.ts

// 對應後端 Response 的統一格式 (建議與後端團隊約定)
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message: string;
  errors?: string[];
}

// 分頁回應
interface PagedResponse<T> {
  items: T[];
  totalCount: number;
  pageNumber: number;
  pageSize: number;
  totalPages: number;
}

// 對應後端 DTO
interface CreateUserDto {
  name: string;
  email: string;
  password: string;
}

interface UpdateUserDto {
  name?: string;
  email?: string;
}
```

### 5.2 建立 API Client (封裝 fetch)

```tsx
// lib/apiClient.ts

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://localhost:7001/api";

// 取得 JWT Token (從 localStorage 或 Store)
const getAuthToken = (): string | null => {
  return localStorage.getItem("token");
};

// 通用 fetch 封裝
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();

  const config: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const res = await fetch(`${BASE_URL}${endpoint}`, config);

  if (!res.ok) {
    // 處理 HTTP 錯誤
    if (res.status === 401) {
      // Token 過期，清除並跳回登入
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.message || `HTTP${res.status}`);
  }

  // 204 No Content 不需要解析
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

// 匯出便利方法
export const apiClient = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, body: unknown) =>
    request<T>(url, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(url: string, body: unknown) =>
    request<T>(url, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(url: string, body: unknown) =>
    request<T>(url, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(url: string) => request<T>(url, { method: "DELETE" }),
};
```

### 5.3 建立 API 模組

```tsx
// api/userApi.ts
import { apiClient } from "../lib/apiClient";
import { User, CreateUserDto, UpdateUserDto } from "../types";

export const userApi = {
  getAll: () => apiClient.get<User[]>("/users"),

  getById: (id: number) => apiClient.get<User>(`/users/${id}`),

  create: (dto: CreateUserDto) => apiClient.post<User>("/users", dto),

  update: (id: number, dto: UpdateUserDto) =>
    apiClient.put<User>(`/users/${id}`, dto),

  delete: (id: number) => apiClient.delete<void>(`/users/${id}`),
};
```

### 5.4 Auth API 與 JWT 處理

```tsx
// api/authApi.ts
import { apiClient } from "../lib/apiClient";

interface LoginDto {
  email: string;
  password: string;
}

interface AuthResponse {
  token: string;
  refreshToken: string;
  expiresAt: string;
  user: User;
}

export const authApi = {
  login: (dto: LoginDto) => apiClient.post<AuthResponse>("/auth/login", dto),
  logout: () => apiClient.post<void>("/auth/logout", {}),
  refreshToken: (refreshToken: string) =>
    apiClient.post<AuthResponse>("/auth/refresh", { refreshToken }),
};

// stores/useAuthStore.ts
import { create } from "zustand";
import { authApi } from "../api/authApi";

interface AuthState {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  user: null,

  login: async (email, password) => {
    const res = await authApi.login({ email, password });
    localStorage.setItem("token", res.token);
    set({ token: res.token, user: res.user });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ token: null, user: null });
  },
}));
```

### 5.5 CORS 設定提醒 (ASP.NET Core 後端)

前端開發時，後端需要開放 CORS，確認 `Program.cs` 有以下設定：

```csharp
// Program.cs (ASP.NET Core)
builder.Services.AddCors(options =>
{
    options.AddPolicy("ReactApp", policy =>
    {
        policy.WithOrigins("http://localhost:5173") // Vite 預設 port
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

app.UseCors("ReactApp");
```

### 5.6 環境變數設定

```bash
# .env.development
VITE_API_BASE_URL=https://localhost:7001/api

# .env.production
VITE_API_BASE_URL=https://your-production-domain.com/api
```

```tsx
// 使用方式
const BASE_URL = import.meta.env.VITE_API_BASE_URL;
// 注意：Vite 的環境變數必須以 VITE_ 開頭才能在前端存取
```

---

## 6. 專案結構建議

- 收合架構
    
    ```
    src/
    ├── api/                  # API 呼叫模組
    │   ├── authApi.ts
    │   └── userApi.ts
    ├── components/           # 可重用 UI 元件
    │   ├── ui/               # 基礎元件 (Button, Input, Modal...)
    │   └── shared/           # 共用業務元件
    ├── features/             # 以功能模組切分 (大型專案)
    │   └── users/
    │       ├── components/
    │       ├── hooks/
    │       └── types.ts
    ├── hooks/                # 自訂 Hook
    │   └── useFetch.ts
    ├── lib/                  # 工具函式、API Client 等
    │   └── apiClient.ts
    ├── pages/                # 頁面元件 (對應路由)
    │   ├── LoginPage.tsx
    │   └── DashboardPage.tsx
    ├── stores/               # Zustand Store
    │   ├── useAuthStore.ts
    │   └── useUserStore.ts
    ├── types/                # 全域型別定義
    │   ├── api.ts
    │   └── index.ts
    └── App.tsx
    ```
    

---

## 7. 常見錯誤與對策

### 7.1 型別是 `any`，失去保護

```tsx
// 錯誤：any 讓 TypeScript 無法幫你檢查
const handleData = (data: any) => {
  console.log(data.name.toUpperCase()); // 執行時可能爆炸
};

// 正確：明確定義型別
const handleData = (data: User) => {
  console.log(data.name.toUpperCase()); // TypeScript 會確保 name 存在
};
```

### 7.2 沒有處理 `null` / `undefined`

```tsx
// 錯誤：user 可能是 null
const name = user.name; // TypeScript 會報錯

// 正確方式 1：Optional Chaining
const name = user?.name;

// 正確方式 2：Nullish Coalescing
const name = user?.name ?? "訪客";

// 正確方式 3：型別縮窄
if (user) {
  const name = user.name; // 這裡確定不是 null
}
```

### 7.3 useEffect 依賴陣列不完整

```tsx
// 錯誤：用到 userId 但沒放進依賴陣列 (ESLint 會警告)
useEffect(() => {
  fetchUser(userId);
}, []); // userId 變化時不會重跑，資料會過期

// 正確
useEffect(() => {
  fetchUser(userId);
}, [userId]);
```

### 7.4 直接修改 State

```tsx
// 錯誤：直接修改 state，React 不會偵測到變化
const [users, setUsers] = useState<User[]>([]);
users.push(newUser); // 不要這樣做

// 正確：建立新陣列
setUsers(prev => [...prev, newUser]);
```

### 7.5 fetch 忘記處理 non-2xx 回應

```tsx
// 錯誤：HTTP 404 / 500 時，fetch 不會自動 throw Error
const res = await fetch("/api/users");
const data = await res.json(); // 404 時這裡可能拿到錯誤格式的 JSON

// 正確：檢查 res.ok
const res = await fetch("/api/users");
if (!res.ok) {
  throw new Error(`伺服器錯誤:${res.status}`);
}
const data: User[] = await res.json();
```

---