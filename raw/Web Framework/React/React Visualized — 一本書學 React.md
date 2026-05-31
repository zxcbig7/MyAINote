---
tags: [web-dev, react, frontend, typescript, book]
---

> 關聯：[[React]]、[[React + TypeScript 開發手冊]]

# React Visualized — 一本書學 React

> 本書以 [react.gg/visualized](https://react.gg/visualized) 的視覺化課程為基礎撰寫，
> 目標是讓你從「會寫 React」進化到「真正理解 React 在做什麼」。

---

## 目錄

- [前言：Web 開發的演進](#前言web-開發的演進)
- [第一章：React 的核心理念 — v = fn(s)](#第一章react-的核心理念--vfns)
- [第二章：元件與 JSX — 重新定義關注點分離](#第二章元件與-jsx--重新定義關注點分離)
- [第三章：Props — 資料的單向河流](#第三章props--資料的單向河流)
- [第四章：State — 讓畫面活起來](#第四章state--讓畫面活起來)
- [第五章：渲染機制 — 快照、觸發與更新](#第五章渲染機制--快照觸發與更新)
- [第六章：Side Effects — 與外部世界的橋樑](#第六章side-effects--與外部世界的橋樑)
- [第七章：Refs — 不觸發渲染的記憶](#第七章refs--不觸發渲染的記憶)
- [第八章：Context — 跨越元件樹的傳送門](#第八章context--跨越元件樹的傳送門)
- [第九章：Concurrent React — 優先級與並行渲染](#第九章concurrent-react--優先級與並行渲染)
- [第十章：Server Components — 服務端的 React](#第十章server-components--服務端的-react)
- [附錄：React 版本演進對照表](#附錄react-版本演進對照表)

---

## 前言：Web 開發的演進

在理解 React 為何存在之前，我們得先回頭看看它試圖解決的問題。

### jQuery 時代：狀態藏在 DOM 裡

2006 年，jQuery 讓 JavaScript 操作 DOM 變得簡單。然而它有一個根本問題：**應用程式的狀態（state）散落在 DOM 節點之中**。

```javascript
// jQuery 時代
$('#counter').text(parseInt($('#counter').text()) + 1);
```

你要知道「現在的數字是幾」，必須去問 DOM。UI 本身就是唯一的真相來源（source of truth）。當應用程式複雜起來，這種模式讓追蹤狀態變成一場噩夢。

### Backbone.js：引入 Model

Backbone 把狀態從 DOM 解放出來，引入 Model-View-Controller 模式。Model 持有資料，View 負責渲染。這是一大進步，但 View 和 Model 的同步邏輯仍然是手動的。

```javascript
// Backbone 時代
var counter = new Backbone.Model({ count: 0 });
counter.on('change', function() {
  $('#counter').text(counter.get('count'));
});
```

### AngularJS：雙向綁定的誘惑與代價

AngularJS 帶來了雙向資料綁定（two-way data binding）。畫面改變 → Model 自動更新；Model 改變 → 畫面自動更新。聽起來很美好，但帶來一個新問題：**當 UI 複雜，你無法預測一個地方的改變會影響哪裡**。這種「神秘的遠距行動」讓大型應用程式的除錯變成一場惡夢。

### React 的答案：把 UI 變成純函式

2013 年，Facebook 開源了 React。它帶來的核心洞察極其簡單，卻顛覆了前端的思維模式：

> **UI 應該是狀態的確定性函式（deterministic function of state）。**

---

## 第一章：React 的核心理念 — v=fn(s)

### 1.1 那個改變一切的公式

```
v = fn(s)
```

- `v`（view）：畫面，你看到的 UI
- `fn`（function）：你的元件
- `s`（state）：狀態，資料

這個公式的意義是：**給定相同的狀態，永遠產生相同的畫面**。沒有隱藏的 DOM 操作，沒有神秘的副作用，UI 完全由狀態決定。

### 1.2 為什麼這個公式很重要

傳統做法讓你思考的問題是：「我要如何把按鈕的文字從『讚』改成『已讚』？」— 這是**命令式**（imperative）思維。

React 讓你思考的問題是：「當 `isLiked` 為 `true` 時，畫面長什麼樣子？」— 這是**宣告式**（declarative）思維。

```tsx
// 命令式：你告訴瀏覽器「怎麼做」
if (isLiked) {
  button.textContent = '已讚';
  button.classList.add('liked');
} else {
  button.textContent = '讚';
  button.classList.remove('liked');
}

// 宣告式：你描述「結果是什麼」
function LikeButton({ isLiked }: { isLiked: boolean }) {
  return (
    <button className={isLiked ? 'liked' : ''}>
      {isLiked ? '已讚' : '讚'}
    </button>
  );
}
```

### 1.3 元件就是函式

React 元件本質上就是一個 JavaScript 函式：
- **接收 props（輸入）**
- **回傳 JSX（輸出）**

```tsx
// 這就是一個 React 元件，普通的函式
function Greeting({ name }: { name: string }) {
  return <h1>Hello, {name}!</h1>;
}
```

這個設計讓 React 可以借用函式式程式設計的所有概念：組合、純函式、確定性……這不是意外，是刻意為之。

---

## 第二章：元件與 JSX — 重新定義關注點分離

### 2.1 JSX 不是 HTML

JSX 看起來像 HTML，但它其實是 JavaScript 的語法擴充。每一段 JSX 在編譯後都會變成 `React.createElement()` 的呼叫。

```tsx
// 你寫的 JSX
const element = <h1 className="title">Hello</h1>;

// 編譯後等同於
const element = React.createElement('h1', { className: 'title' }, 'Hello');
```

JSX 的幾個關鍵規則：

| 規則 | 原因 |
|------|------|
| `class` → `className` | `class` 是 JS 保留字 |
| 標籤必須關閉 | `<br />` 而非 `<br>` |
| 只能有一個根元素 | 函式只能有一個回傳值 |
| 使用 `{}` 插入 JS 運算式 | JSX 是 JS，不是模板語言 |

### 2.2 關注點分離的新定義

傳統觀念認為：HTML、CSS、JavaScript 應該分離在不同檔案。這是按**技術類型**分離。

React 提出的是：按**功能**分離。一個按鈕的 HTML 結構、樣式邏輯、互動行為，都屬於「按鈕」這個功能，放在同一個元件裡是合理的。

```tsx
// 關注點：「一個可點擊的計數按鈕」
function CounterButton() {
  const [count, setCount] = useState(0);

  return (
    <button
      onClick={() => setCount(c => c + 1)}
      style={{ padding: '8px 16px', cursor: 'pointer' }}
    >
      點了 {count} 次
    </button>
  );
}
```

### 2.3 元件的組合（Composition）

React 最強大的特性之一是**組合**。小元件組成大元件，就像樂高積木。

```tsx
function Avatar({ src, alt }: { src: string; alt: string }) {
  return <img src={src} alt={alt} className="avatar" />;
}

function UserCard({ user }: { user: User }) {
  return (
    <div className="card">
      <Avatar src={user.avatar} alt={user.name} />
      <h2>{user.name}</h2>
      <p>{user.bio}</p>
    </div>
  );
}

function UserList({ users }: { users: User[] }) {
  return (
    <div>
      {users.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
}
```

### 2.4 Fragment：隱形的容器

當你需要回傳多個根元素但不想增加額外的 DOM 節點：

```tsx
function TableRow() {
  return (
    <>
      <td>欄位 1</td>
      <td>欄位 2</td>
    </>
  );
}
```

`<>...</>` 是 `<React.Fragment>` 的縮寫，不會產生任何 DOM 節點。

---

## 第三章：Props — 資料的單向河流

### 3.1 Props 的本質

Props（Properties）是父元件傳給子元件的資料。它有一個鐵律：**Props 是唯讀的（read-only）**。

子元件不能修改收到的 props，這保證了資料流向是單向的——永遠從父到子。

```tsx
// 正確：接收並使用 props
function Badge({ label, color }: { label: string; color: string }) {
  return <span style={{ backgroundColor: color }}>{label}</span>;
}

// 錯誤：試圖修改 props（TypeScript 會報錯）
function Badge({ label }: { label: string }) {
  label = label.toUpperCase(); // 不要這樣做
  return <span>{label}</span>;
}
```

### 3.2 Props 可以是任何東西

Props 不只是字串或數字，可以是函式、物件、陣列，甚至是 React 元件。

```tsx
type ButtonProps = {
  label: string;
  onClick: () => void;        // 函式
  icon?: React.ReactNode;     // React 元素（可選）
  style?: React.CSSProperties; // CSS 物件
};

function Button({ label, onClick, icon, style }: ButtonProps) {
  return (
    <button onClick={onClick} style={style}>
      {icon && <span className="icon">{icon}</span>}
      {label}
    </button>
  );
}
```

### 3.3 children：元件的插槽模式

`children` 是一個特殊的 prop，代表「放在元件標籤之間的內容」。這讓你可以設計出具有容器功能的元件。

```tsx
type CardProps = {
  title: string;
  children: React.ReactNode;
};

function Card({ title, children }: CardProps) {
  return (
    <div className="card">
      <h2 className="card-title">{title}</h2>
      <div className="card-body">{children}</div>
    </div>
  );
}

// 使用方式
function App() {
  return (
    <Card title="使用者資訊">
      <p>名字：Vic</p>
      <p>職位：全端工程師</p>
    </Card>
  );
}
```

### 3.4 佈局元件（Layout Component）

`children` 的最大用途是建立佈局元件。你的頁面容器、側邊欄、模態框，都可以用這個模式設計：

```tsx
function PageLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="page">
      <header className="page-header">
        <nav>/* 導覽列 */</nav>
      </header>
      <main className="page-content">{children}</main>
      <footer>/* 頁尾 */</footer>
    </div>
  );
}

function DashboardPage() {
  return (
    <PageLayout>
      <h1>儀表板</h1>
      <DataTable />
    </PageLayout>
  );
}
```

---

## 第四章：State — 讓畫面活起來

### 4.1 為什麼需要 State

Props 是外部傳進來的，那元件自己需要「記住」什麼東西時怎麼辦？這就是 State 的用途。

State 是**元件私有的、可以隨時間改變的資料**。當 state 改變，React 會自動重新渲染元件，產生新的畫面。

```tsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0); // 初始值為 0

  return (
    <div>
      <p>目前數字：{count}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
      <button onClick={() => setCount(count - 1)}>-1</button>
    </div>
  );
}
```

### 4.2 useState 的解構賦值

`useState` 回傳一個長度為 2 的陣列：
1. **目前的狀態值**
2. **更新狀態的函式**

```tsx
const [state, setState] = useState(initialValue);
//    ↑ 當前值   ↑ setter    ↑ 初始值
```

命名慣例是 `[xxx, setXxx]`，例如 `[count, setCount]`、`[isOpen, setIsOpen]`。

### 4.3 State 是快照，不是即時值

這是初學者最容易犯的錯誤。**在同一次渲染中，state 的值是固定的**，即使你呼叫了 setter。

```tsx
function BuggyCounter() {
  const [count, setCount] = useState(0);

  function handleTripleClick() {
    setCount(count + 1); // count 是 0
    setCount(count + 1); // count 還是 0（！）
    setCount(count + 1); // count 還是 0（！）
    // 結果：count 變成 1，不是 3
  }
}
```

解決方法：使用 **updater function**（函式形式的 setter），接收最新的 state 作為參數：

```tsx
function CorrectCounter() {
  const [count, setCount] = useState(0);

  function handleTripleClick() {
    setCount(prev => prev + 1); // prev 是最新值
    setCount(prev => prev + 1); // prev 是上一步的結果
    setCount(prev => prev + 1); // prev 是上上一步的結果
    // 結果：count 正確變成 3
  }
}
```

### 4.4 State 提升（Lifting State Up）

當兩個元件需要共享同一份 state，答案是：**把 state 提升到它們共同的父元件**。

```tsx
// 問題：兩個子元件需要共享溫度
function TemperatureConverter() {
  const [celsius, setCelsius] = useState(0);
  // state 在父元件，透過 props 往下傳

  const fahrenheit = celsius * 9/5 + 32;

  return (
    <div>
      <CelsiusInput
        value={celsius}
        onChange={setCelsius}
      />
      <FahrenheitDisplay value={fahrenheit} />
    </div>
  );
}

function CelsiusInput({
  value,
  onChange
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <input
      type="number"
      value={value}
      onChange={e => onChange(Number(e.target.value))}
    />
  );
}
```

### 4.5 State 的資料結構設計原則

設計 state 時，越簡單越好：

```tsx
// 不好：重複計算，導致狀態不一致
const [items, setItems] = useState<string[]>([]);
const [itemCount, setItemCount] = useState(0); // 多餘，可以從 items.length 得到

// 好：只保留最小必要的狀態
const [items, setItems] = useState<string[]>([]);
const itemCount = items.length; // 派生值，不需要是 state
```

原則：**能從現有 state 或 props 計算出來的值，不要存成 state。**

---

## 第五章：渲染機制 — 快照、觸發與更新

### 5.1 渲染的三個階段

React 的渲染過程分為三個階段：

```
1. 觸發（Trigger）
   ↓ state 改變或父元件重新渲染
2. 渲染（Render）
   ↓ React 呼叫你的元件函式，取得新的 JSX
3. 提交（Commit）
   ↓ React 比對差異，只更新真正改變的 DOM 節點
```

這個過程叫做 **Reconciliation（調和）**。React 不會每次都重建整個 DOM，只更新有差異的部分。

### 5.2 快照（Snapshot）

每次渲染，React 都會呼叫你的元件函式一次，這次執行就像拍了一張「快照」。這個快照中的所有值（包括 state）在這次渲染期間是固定不變的。

```tsx
function MessageSender() {
  const [message, setMessage] = useState('');

  function handleSend() {
    // 這裡的 message 是「這次渲染的快照值」
    setTimeout(() => {
      // 3 秒後執行，但 message 還是快照時的值
      alert(`已送出：${message}`);
    }, 3000);
  }

  return (
    <>
      <input value={message} onChange={e => setMessage(e.target.value)} />
      <button onClick={handleSend}>送出</button>
    </>
  );
}
```

如果你在按下「送出」後，在 3 秒內修改輸入框，`alert` 顯示的還是你按下按鈕時的訊息，不是修改後的值。這就是「快照」的特性。

### 5.3 子元件會連帶重新渲染

**父元件重新渲染時，所有子元件都會跟著重新渲染**，無論 props 有沒有改變。這是預設行為。

```
App (re-renders)
├── Header (re-renders) ← 即使 Header 沒收到任何 props 變化
├── Main (re-renders)
│   ├── Sidebar (re-renders)
│   └── Content (re-renders)
└── Footer (re-renders)
```

### 5.4 React.memo：打破預設行為

`React.memo` 讓元件在 props 沒有改變時跳過重新渲染：

```tsx
// 沒有 memo：每次父元件渲染都會跟著渲染
function ExpensiveChart({ data }: { data: number[] }) {
  console.log('渲染了 Chart');
  return <div>/* 複雜圖表 */</div>;
}

// 有 memo：只有 data 改變才重新渲染
const ExpensiveChart = React.memo(function({ data }: { data: number[] }) {
  console.log('渲染了 Chart');
  return <div>/* 複雜圖表 */</div>;
});
```

> **注意**：不要過度使用 `React.memo`。它有比較 props 的開銷，只在確定有效能問題時才使用。

### 5.5 key：幫助 React 辨識元件身份

`key` 不只是「讓 React 不要警告」的東西，它告訴 React 某個元件的**身份（identity）**。

```tsx
// key 改變 → React 認為是不同的元件 → 會銷毀舊的，建立新的
function ProfileEditor({ userId }: { userId: string }) {
  const [name, setName] = useState('');

  return (
    // 當 userId 改變，整個表單重置（因為 key 改變）
    <form key={userId}>
      <input value={name} onChange={e => setName(e.target.value)} />
    </form>
  );
}
```

---

## 第六章：Side Effects — 與外部世界的橋樑

### 6.1 什麼是 Side Effect

Side Effect（副作用）是指任何**影響函式外部世界**的操作：
- 呼叫 API
- 操作 DOM
- 設定計時器
- 訂閱事件
- 寫入 localStorage

React 元件的渲染應該是純函式（相同輸入，相同輸出，無副作用）。Side effects 需要特殊處理。

### 6.2 四條黃金規則

| 情境 | 正確做法 |
|------|----------|
| 渲染期間 | **絕對禁止** |
| 使用者互動（點擊、輸入）引發的 | 放在**事件處理器**（event handler）|
| 元件需要與外部系統同步 | 放在 **`useEffect`** |
| 需要在瀏覽器繪製前執行 | 放在 **`useLayoutEffect`** |

### 6.3 useEffect 的基本語法

```tsx
useEffect(() => {
  // 副作用邏輯

  return () => {
    // 清除函式（cleanup）— 元件卸載時執行
  };
}, [/* 依賴陣列 */]);
```

**依賴陣列（dependency array）** 控制 effect 何時執行：

```tsx
// 每次渲染後都執行
useEffect(() => { ... });

// 只在第一次渲染後執行一次
useEffect(() => { ... }, []);

// 只在 userId 改變後執行
useEffect(() => { ... }, [userId]);
```

### 6.4 實際範例：API 資料獲取

```tsx
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isCancelled = false; // 防止 race condition

    setIsLoading(true);
    setError(null);

    fetchUser(userId)
      .then(data => {
        if (!isCancelled) {
          setUser(data);
          setIsLoading(false);
        }
      })
      .catch(err => {
        if (!isCancelled) {
          setError(err);
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true; // userId 改變時，取消上一個請求的影響
    };
  }, [userId]); // userId 改變就重新 fetch

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!user) return null;

  return <div>{user.name}</div>;
}
```

### 6.5 useLayoutEffect：在瀏覽器繪製前執行

`useLayoutEffect` 的語法和 `useEffect` 完全相同，但執行時機不同：

```
useEffect  →  渲染 → 提交 → 瀏覽器繪製 → 執行
useLayoutEffect → 渲染 → 提交 → 執行（阻塞繪製）→ 瀏覽器繪製
```

使用時機：需要在使用者看到畫面之前測量 DOM 或設定初始位置，避免閃爍。

```tsx
function Tooltip({ children, content }: TooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    // 在瀏覽器繪製前計算位置，避免 tooltip 閃爍
    const rect = tooltipRef.current?.getBoundingClientRect();
    // 調整 tooltip 位置...
  }, []);

  return (/* ... */);
}
```

---

## 第七章：Refs — 不觸發渲染的記憶

### 7.1 useRef 的兩大用途

`useRef` 建立一個在渲染之間持久存在的容器，**改變它的值不會觸發重新渲染**。

**用途一：持有跨渲染的值（如計時器 ID）**

```tsx
function AutoSave({ content }: { content: string }) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // 清除上一個計時器
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    // 設定新計時器
    timerRef.current = setTimeout(() => {
      saveToServer(content);
    }, 1000);
  }, [content]);

  return <p>自動儲存中...</p>;
}
```

**用途二：直接操作 DOM 節點**

```tsx
function VideoPlayer() {
  const videoRef = useRef<HTMLVideoElement>(null);

  function handlePlay() {
    videoRef.current?.play(); // 直接呼叫 DOM API
  }

  return (
    <>
      <video ref={videoRef} src="/video.mp4" />
      <button onClick={handlePlay}>播放</button>
    </>
  );
}
```

### 7.2 useRef vs useState：何時用哪個？

| 特性 | `useState` | `useRef` |
|------|-----------|---------|
| 改變是否觸發重新渲染 | 是 | 否 |
| 適合用途 | 影響畫面的資料 | 不需要呈現的資料 |
| 範例 | 計數器、輸入值 | 計時器 ID、DOM 節點 |

### 7.3 forwardRef：傳遞 ref 給子元件

預設情況下，你無法把 `ref` 傳給子元件。需要使用 `forwardRef`：

```tsx
// 自定義 Input，但允許父元件直接操作它的 DOM
const FancyInput = React.forwardRef<HTMLInputElement, { placeholder: string }>(
  function FancyInput({ placeholder }, ref) {
    return (
      <input
        ref={ref}
        placeholder={placeholder}
        className="fancy-input"
      />
    );
  }
);

function SearchPage() {
  const inputRef = useRef<HTMLInputElement>(null);

  function focusInput() {
    inputRef.current?.focus();
  }

  return (
    <>
      <FancyInput ref={inputRef} placeholder="搜尋..." />
      <button onClick={focusInput}>聚焦輸入框</button>
    </>
  );
}
```

---

## 第八章：Context — 跨越元件樹的傳送門

### 8.1 Props Drilling 的痛苦

假設你有這樣的元件樹，而底部的 `UserAvatar` 需要知道當前登入的使用者：

```
App (持有 currentUser)
└── Layout
    └── Sidebar
        └── Navigation
            └── UserAvatar ← 需要 currentUser
```

你得把 `currentUser` 從 `App` 一層層傳下去，中間的 `Layout`、`Sidebar`、`Navigation` 根本不需要它，卻要當傳話人。這叫做 **Props Drilling**。

### 8.2 Context 的解法：傳送門

Context 讓你可以在元件樹的任意位置直接取用資料，跳過中間的所有層級。

```tsx
// Step 1：建立 Context
const UserContext = React.createContext<User | null>(null);

// Step 2：提供資料（在上層元件包裹 Provider）
function App() {
  const [currentUser] = useState<User>({ id: '1', name: 'Vic' });

  return (
    <UserContext.Provider value={currentUser}>
      <Layout />
    </UserContext.Provider>
  );
}

// Step 3：在任意深度的子元件使用 useContext
function UserAvatar() {
  const user = useContext(UserContext);

  if (!user) return null;
  return <img src={`/avatars/${user.id}.jpg`} alt={user.name} />;
}
```

### 8.3 自定義 Context Hook

直接使用 `useContext` 需要每次 import Context。更好的做法是封裝成自定義 Hook：

```tsx
// context/UserContext.tsx
const UserContext = React.createContext<User | null>(null);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  return (
    <UserContext.Provider value={user}>
      {children}
    </UserContext.Provider>
  );
}

// 使用這個 hook，如果在 Provider 外使用會直接報錯
export function useUser(): User {
  const user = useContext(UserContext);
  if (!user) throw new Error('useUser 必須在 UserProvider 內使用');
  return user;
}
```

```tsx
// 使用方
function UserAvatar() {
  const user = useUser(); // 簡潔多了
  return <img src={`/avatars/${user.id}.jpg`} alt={user.name} />;
}
```

### 8.4 Context 的效能注意事項

Context 的 value 改變時，**所有使用這個 Context 的元件都會重新渲染**，不管它們用的是哪個欄位。

解決方法：拆分 Context，或搭配 `React.memo`。

```tsx
// 不好：user 和 theme 放在一起，改 theme 會讓所有 useUserContext 的元件重新渲染
const AppContext = createContext({ user, theme });

// 好：分開，互不影響
const UserContext = createContext(user);
const ThemeContext = createContext(theme);
```

---

## 第九章：Concurrent React — 優先級與並行渲染

### 9.1 React 17 的問題：全有或全無

在 React 17，一旦狀態更新開始渲染，就無法中斷。即使有更緊急的更新（例如使用者輸入），也要等當前渲染完成。

想像你在打字，每次按鍵都觸發一個過濾大型清單的昂貴渲染。鍵盤輸入（高優先級）和過濾結果（低優先級）都排在同一個隊列，使用者感覺到卡頓。

### 9.2 React 18：並行渲染（Concurrent Mode）

React 18 引入了 Concurrent Mode，核心思想是：**並非所有更新都同等重要**。

- **緊急更新（Urgent）**：使用者直接互動，如輸入、點擊 → 必須立即響應
- **非緊急更新（Transition）**：畫面切換、資料過濾 → 可以稍微延遲

### 9.3 startTransition：標記非緊急更新

```tsx
import { useState, startTransition } from 'react';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Item[]>([]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;

    // 緊急：立即更新輸入框顯示
    setQuery(value);

    // 非緊急：搜尋結果可以稍後更新
    startTransition(() => {
      setResults(filterItems(value));
    });
  }

  return (
    <>
      <input value={query} onChange={handleChange} />
      <ResultList items={results} />
    </>
  );
}
```

### 9.4 useTransition：帶有 loading 狀態的版本

`useTransition` 提供 `isPending` 旗標，讓你知道 transition 正在進行中：

```tsx
import { useState, useTransition } from 'react';

function TabsPanel() {
  const [activeTab, setActiveTab] = useState('home');
  const [isPending, startTransition] = useTransition();

  function handleTabChange(tab: string) {
    startTransition(() => {
      setActiveTab(tab);
    });
  }

  return (
    <div>
      <nav>
        {['home', 'profile', 'settings'].map(tab => (
          <button
            key={tab}
            onClick={() => handleTabChange(tab)}
            style={{ opacity: isPending ? 0.5 : 1 }} // 切換中顯示半透明
          >
            {tab}
          </button>
        ))}
      </nav>
      <TabContent tab={activeTab} />
    </div>
  );
}
```

### 9.5 useDeferredValue：延遲更新衍生值

當你無法控制觸發更新的來源（例如 props），使用 `useDeferredValue`：

```tsx
import { useDeferredValue } from 'react';

function ProductList({ searchQuery }: { searchQuery: string }) {
  // 延遲更新 searchQuery 的值
  const deferredQuery = useDeferredValue(searchQuery);

  // filteredProducts 使用延遲後的值計算
  // 使用者輸入時不會阻塞，先用舊資料顯示
  const filteredProducts = filterProducts(deferredQuery);

  return (
    <ul style={{ opacity: deferredQuery !== searchQuery ? 0.8 : 1 }}>
      {filteredProducts.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}
```

### 9.6 React 19：Actions

React 19 把 `transition` 的概念擴展到非同步操作（如 API 請求）。

```tsx
// React 19 Actions
function UpdateNameForm({ userId }: { userId: string }) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const name = new FormData(e.currentTarget).get('name') as string;

    startTransition(async () => {
      // 可以在 transition 中 await 非同步操作
      const result = await updateUserName(userId, name);
      if (!result.ok) {
        setError(result.error);
      }
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" />
      {error && <p className="error">{error}</p>}
      <button disabled={isPending}>
        {isPending ? '更新中...' : '更新名字'}
      </button>
    </form>
  );
}
```

---

## 第十章：Server Components — 服務端的 React

### 10.1 傳統 React 的限制

傳統的 React 元件（現在稱為 **Client Components**）完全在瀏覽器執行。這有幾個問題：
- 所有 JS bundle 都要傳到客戶端，Bundle Size 大
- 資料獲取在客戶端發起，有網路延遲
- 無法使用 Node.js 專屬 API（直接讀資料庫等）

### 10.2 Server Components 是什麼

Server Components 在**伺服器端渲染並轉換成輕量格式傳給客戶端**，客戶端不需要下載它們的 JavaScript。

```tsx
// app/page.tsx（Next.js App Router，預設是 Server Component）
// 可以直接 await！不需要 useEffect
async function ProductsPage() {
  // 在伺服器上直接查資料庫
  const products = await db.query('SELECT * FROM products');

  return (
    <div>
      <h1>商品清單</h1>
      {products.map(p => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}
```

### 10.3 Client Components vs Server Components

| 特性 | Server Component | Client Component |
|------|-----------------|-----------------|
| 執行環境 | 伺服器 | 瀏覽器 |
| 能使用 hooks | 否 | 是 |
| 能有互動性（onClick 等） | 否 | 是 |
| 能直接存取資料庫 | 是 | 否 |
| 加入 JS bundle | 否（節省流量）| 是 |
| 標記方式 | 預設（Next.js App Router）| 頂部加 `'use client'` |

### 10.4 'use client' 指令

`'use client'` 標記一個元件及其所有子元件為 Client Component：

```tsx
'use client'; // 這一行讓這個模組成為 Client Component

import { useState } from 'react';

// 因為有互動（useState），必須是 Client Component
export function AddToCartButton({ productId }: { productId: string }) {
  const [added, setAdded] = useState(false);

  return (
    <button onClick={() => setAdded(true)}>
      {added ? '已加入購物車' : '加入購物車'}
    </button>
  );
}
```

### 10.5 Slot Pattern：兩個世界的橋樑

最佳實踐是：**Server Component 作為容器，Client Component 作為互動島嶼**。

```tsx
// layout.tsx（Server Component）
// 伺服器產生骨架，把 children（slot）留給客戶端填充
async function ProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id); // 伺服器上取資料

  return (
    <div className="product-page">
      {/* 靜態資訊由伺服器渲染 */}
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <p>NT$ {product.price}</p>

      {/* 互動按鈕是 Client Component */}
      <AddToCartButton productId={product.id} />
    </div>
  );
}
```

### 10.6 Suspense 與 ErrorBoundary

Server Components 天然支援 `Suspense`，讓你在等待資料時顯示 loading 狀態：

```tsx
import { Suspense } from 'react';

function Page() {
  return (
    <div>
      <h1>我的頁面</h1>

      {/* 等待 SlowComponent 的資料時，顯示 Skeleton */}
      <Suspense fallback={<ProductSkeleton />}>
        <SlowProductList />
      </Suspense>
    </div>
  );
}
```

---

## 附錄：React 版本演進對照表

| 版本 | 重要特性 | 解決的問題 |
|------|---------|-----------|
| React 16.8 | Hooks（useState, useEffect 等）| 函式元件有狀態，告別 Class Component |
| React 17 | 無重大新功能，改善升級路徑 | 讓不同版本 React 可以共存 |
| React 18 | Concurrent Mode、Suspense 改善、useTransition、useDeferredValue | 優先級渲染，改善使用者互動體驗 |
| React 19 | Actions、use()、optimistic updates | 非同步操作一等公民，簡化資料變更流程 |

---

## 閱讀完本書後的下一步

1. **建立一個真實專案**：光看不練等於沒看。建議實作一個有認證、資料獲取、狀態管理的小應用。
2. **深入 Hooks**：`useReducer`、`useCallback`、`useMemo` 是本書未涵蓋的重要 Hooks。
3. **學習 Next.js App Router**：Server Components 的最佳實踐場域。
4. **研究狀態管理**：當 Context 不夠用時，Zustand 是輕量首選。

> 延伸閱讀：[[React + TypeScript 開發手冊]] | [[前端傳輸概念 (axios + React Query+Promise)]] | [[React 生態系資源]]
