# React Hooks 用途筆記與 TypeScript 範例

核對日期：2026-10-17（台灣時間）  
依據：React 官方文件，查閱時的最新穩定版為 **React 19.3**。

這份筆記涵蓋 **18 個 `react` 內建 Hook、1 個 `react-dom` Hook**，另外補充 `use` API、自訂 Hook 與 API 查詢實例。第三方套件及自訂 Hook 沒有固定的「全部清單」，不計入這 19 個。

## 先看這一頁

Hook 是讓函式元件使用狀態、生命週期相關同步、Context 等 React 功能的函式。你不需要每個元件都使用所有 Hook；先判斷問題，再選需要的工具。

| 類別 | Hook | 主要用途 | 筆記中的例子 | 開始提供的穩定版本 |
| --- | --- | --- | --- | --- |
| 狀態 | useState | 保存會影響畫面的狀態 | 計數器 | 16.8 |
| 狀態 | useReducer | 用 action 集中處理狀態更新規則 | 商品數量與單價 | 16.8 |
| 共用資料 | useContext | 讀取並訂閱上層提供的 Context | 切換主題 | 16.8 |
| 參照 | useRef | 保存 DOM 或不觸發重新渲染的可變值 | 聚焦輸入框 | 16.8 |
| 外部同步 | useEffect | 與計時器、事件、網路等外部系統同步 | 可調整間隔的計時器 | 16.8 |
| 計算快取 | useMemo | 快取純計算的結果 | 商品篩選 | 16.8 |
| 函式快取 | useCallback | 在依賴不變時重用函式參照 | 傳 callback 給 memo 子元件 | 16.8 |
| 畫面測量 | useLayoutEffect | 在瀏覽器繪製前讀取布局並修正畫面 | 測量區塊高度 | 16.8 |
| 元件介面 | useImperativeHandle | 自訂父元件透過 ref 可呼叫的方法 | focus 與 clear | 16.8 |
| 除錯 | useDebugValue | 在 React DevTools 標示自訂 Hook 的值 | 計數 Hook 的標籤 | 16.8 |
| 識別碼 | useId | 產生無障礙屬性使用的 ID | label 與 input 關聯 | 18 |
| 更新優先順序 | useTransition | 將更新標為可中斷的非緊急更新 | 輸入框搭配大量清單 | 18 |
| 更新優先順序 | useDeferredValue | 讓部分 UI 使用稍後追上的值 | 延後更新搜尋結果 | 18 |
| 外部狀態 | useSyncExternalStore | 訂閱 React 以外的資料來源 | 瀏覽器連線狀態 | 18 |
| 樣式注入 | useInsertionEffect | 在 layout Effects 前注入動態樣式 | CSS-in-JS 教學示意 | 18 |
| 非同步動作 | useActionState | 保存 Action 結果與 pending 狀態 | 儲存暱稱表單 | 19 |
| 樂觀更新 | useOptimistic | Action 執行中先顯示預期結果 | 先顯示按讚結果 | 19 |
| 表單狀態 | useFormStatus | 讀取所在上層表單的提交狀態 | 共用送出按鈕 | 19，來自 react-dom |
| Effect 事件 | useEffectEvent | 在 Effect 事件中讀取最新值，不因這些值改變而重建訂閱 | 定時記錄最新計數 | 19.2 |

**建議閱讀順序：** useState → useEffect → useRef → useContext → useReducer，再依實際需求學其他 Hook。useMemo / useCallback 的概念值得理解，但不必預先套用到所有程式碼。

**範例怎麼使用：**

1. 各節的主要 TSX 程式碼都是獨立範例，包含 import 與預設匯出的元件，可逐一放進既有 React + TypeScript 專案的 `App.tsx`。
2. 不要把所有範例直接貼在同一個檔案；它們刻意使用相同的 `App` 名稱。
3. 全部範例以 React 19.3 環境為基準；表格的版本是 Hook 首次進入穩定版的版本，不代表範例內所有寫法都支援那個舊版本。
4. 使用 React Server Components 的框架時，這些互動範例要放在適當的 Client Component 邊界；一般瀏覽器端 React 專案不需要額外加上 `'use client'`。
5. 範例的模擬 API 都會明確標示。它們只用來展示 Hook 行為，不會真的寫入資料庫。

官方範圍與版本：[React 版本](https://react.dev/versions)、[React Hooks](https://react.dev/reference/react/hooks)、[useOptimistic](https://react.dev/reference/react/useOptimistic)、[React DOM Hooks](https://react.dev/reference/react-dom/hooks)。

## 0. 使用 Hook 前要理解的規則

### Hook 的呼叫位置

一般 Hook 必須在函式元件或自訂 Hook 的最上層呼叫。不要放進 `if`、迴圈、事件處理函式或條件式提前 return 之後。

~~~tsx
import { useState } from "react";

type Props = { visible?: boolean };

export default function App({ visible = true }: Props) {
  // 每次渲染都以相同順序呼叫 Hook。
  const [count, setCount] = useState(0);

  if (!visible) {
    return null;
  }

  return (
    <button onClick={() => setCount((previous) => previous + 1)}>
      {count}
    </button>
  );
}
~~~

需要條件執行 Effect 時，把條件放在 Effect 的 callback 裡面。後面介紹的 `use` API 是特殊情況，允許在條件及迴圈內呼叫，但仍必須在元件或 Hook 內使用。

### Render、commit 與 Effect

- **Render：** React 執行元件，計算畫面應該長什麼樣。這段程式應保持純粹；不要在這裡送出請求、建立訂閱或修改 DOM。
- **Commit：** React 將這次渲染結果套用到 DOM。
- **Effect：** 讓這個已提交的元件與外部系統保持同步。每種 Effect 的執行時機不同。

React 可能重新執行或放棄一次 render，因此不要把「元件函式執行」視為「某個外部動作保證只會發生一次」。

### 依賴陣列

Effect、useMemo、useCallback 等 Hook 使用 `Object.is` 逐項比較依賴值；它不是深層物件比較。元件內每次建立的新物件或新函式通常會有不同參照。

依賴陣列是在描述 callback 使用了哪些會改變的值。不要為了控制執行次數而刻意漏掉依賴；遇到重複執行，應檢查資料與函式的結構。

官方文件：[Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)。

## 1. useState：管理會影響畫面的狀態

**用途：** 保存計數、輸入內容、是否開啟視窗、目前選取項目等資料。

**語法：** `const [state, setState] = useState(initialState)`

~~~tsx
import { useState } from "react";

export default function App() {
  const [count, setCount] = useState(0);

  function increaseThreeTimes() {
    setCount((previous) => previous + 1);
    setCount((previous) => previous + 1);
    setCount((previous) => previous + 1);
  }

  return (
    <div>
      <p>目前數量：{count}</p>
      <button onClick={() => setCount((previous) => previous + 1)}>
        加 1
      </button>
      <button onClick={increaseThreeTimes}>加 3</button>
      <button onClick={() => setCount(0)}>歸零</button>
    </div>
  );
}
~~~

**執行方式：** 點「加 3」會排入三次函式型更新，每次使用前一次的結果，因此總共加三。

**常見錯誤：**

- `setCount` 不會改變當下這次 render 已經取得的 `count`。在同一個事件裡連續寫三次 `setCount(count + 1)`，通常只會增加一。
- 更新物件或陣列時，要建立新值，避免直接修改舊物件後把相同參照交回去。
- 若新值與舊值經 `Object.is` 比較相同，React 通常會略過這次更新。
- 初始值計算很昂貴時，可以傳初始化函式，例如 `useState(() => buildInitialData())`；初始化函式必須純粹。

官方文件：[useState](https://react.dev/reference/react/useState)。

## 2. useReducer：集中管理狀態更新規則

**用途：** 多個欄位會一起變動，或狀態更新有多種明確操作時，集中在 reducer 處理。

**語法：** `const [state, dispatch] = useReducer(reducer, initialState)`

~~~tsx
import { useReducer } from "react";

type State = {
  quantity: number;
  unitPrice: number;
};

type Action =
  | { type: "increase" }
  | { type: "decrease" }
  | { type: "setPrice"; price: number }
  | { type: "reset" };

const initialState: State = { quantity: 1, unitPrice: 100 };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "increase":
      return { ...state, quantity: state.quantity + 1 };
    case "decrease":
      return { ...state, quantity: Math.max(1, state.quantity - 1) };
    case "setPrice":
      return { ...state, unitPrice: Math.max(0, action.price) };
    case "reset":
      return initialState;
  }
}

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const total = state.quantity * state.unitPrice;

  return (
    <div>
      <p>數量：{state.quantity}，總價：{total}</p>
      <button onClick={() => dispatch({ type: "decrease" })}>減少</button>
      <button onClick={() => dispatch({ type: "increase" })}>增加</button>
      <label>
        單價：
        <input
          type="number"
          min={0}
          value={state.unitPrice}
          onChange={(event) =>
            dispatch({
              type: "setPrice",
              price: Number(event.target.value),
            })
          }
        />
      </label>
      <button onClick={() => dispatch({ type: "reset" })}>重設</button>
    </div>
  );
}
~~~

**執行方式：** UI 發送 action → reducer 根據舊 state 與 action 回傳新 state → React 更新畫面。

**選擇原則：** 簡單獨立狀態先用 useState；更新規則變多、欄位彼此牽動時再考慮 useReducer。它本身不會讓狀態變成全域共用。

**注意：** reducer 必須是純函式；不要在 reducer 裡呼叫 API、啟動計時器或修改原本的 state。總價可以由數量與單價直接算出，不需要額外存一份 state。

官方文件：[useReducer](https://react.dev/reference/react/useReducer)。

## 3. useContext：讀取上層提供的共用資料

**用途：** 主題、登入資訊、語系等資料，需要供多層子元件使用時，避免每一層都轉傳 props。

**語法：** `const value = useContext(SomeContext)`

~~~tsx
import { createContext, useContext, useState } from "react";

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);

  if (value === null) {
    throw new Error("useTheme 必須在 ThemeContext.Provider 內使用");
  }

  return value;
}

function ThemeButton() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button onClick={toggleTheme}>
      目前是 {theme === "light" ? "淺色" : "深色"}，點我切換
    </button>
  );
}

function Toolbar() {
  return <ThemeButton />;
}

export default function App() {
  const [theme, setTheme] = useState<Theme>("light");

  function toggleTheme() {
    setTheme((previous) => (previous === "light" ? "dark" : "light"));
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <Toolbar />
    </ThemeContext.Provider>
  );
}
~~~

**執行方式：** App 提供資料；ThemeButton 直接讀取；中間的 Toolbar 不需要接收或轉傳 theme。

**注意：**

- useContext 會讀取元件上方最近的相同 Context Provider。
- Context 的狀態仍由上層的 useState / useReducer 等來源管理。
- Provider 的 value 改變時，使用該 Context 的元件會收到更新；不能單靠 `memo` 阻止這種更新。
- 範例的 value 每次 render 都會建立新物件。若上層頻繁發生不相關更新，可拆分 Context，或在確認需要時穩定化 value。
- React 19 也支援 `<ThemeContext value={...}>` 的 Provider 寫法；此處使用較熟悉的 `.Provider`。

官方文件：[useContext](https://react.dev/reference/react/useContext)。

## 4. useRef：保存 DOM 或不觸發重新渲染的值

**用途：** 存 DOM 節點、計時器 ID、第三方物件等。修改 `ref.current` 不會排程重新渲染。

**語法：** `const ref = useRef(initialValue)`

~~~tsx
import { useRef, useState } from "react";

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const focusCountRef = useRef(0);
  const [message, setMessage] = useState("尚未聚焦");

  function focusInput() {
    inputRef.current?.focus();
    focusCountRef.current += 1;
    // ref 值本身不驅動畫面；這裡用 state 顯示結果。
    setMessage("已聚焦 " + focusCountRef.current + " 次");
  }

  return (
    <div>
      <label>
        姓名：
        <input ref={inputRef} />
      </label>
      <button onClick={focusInput}>聚焦輸入框</button>
      <p>{message}</p>
    </div>
  );
}
~~~

**選擇原則：** 資料改變後需要顯示新畫面，使用 state；資料只是供事件或外部系統使用，可以考慮 ref。

**注意：** 一般不要在 render 過程讀寫 `ref.current`；優先放在事件或 Effect。不要用 ref 代替本來應該影響畫面的 state。DOM ref 在節點尚未掛載或已卸載時可能是 null。

官方文件：[useRef](https://react.dev/reference/react/useRef)。

## 5. useEffect：與外部系統保持同步

**用途：** 訂閱事件、計時器、WebSocket、外部圖表、資料查詢等。

**語法：** `useEffect(setup, dependencies?)`

~~~tsx
import { useEffect, useState } from "react";

export default function App() {
  const [ticks, setTicks] = useState(0);
  const [intervalMs, setIntervalMs] = useState(1000);

  useEffect(() => {
    const timerId = window.setInterval(() => {
      setTicks((previous) => previous + 1);
    }, intervalMs);

    return () => {
      window.clearInterval(timerId);
    };
  }, [intervalMs]);

  return (
    <div>
      <p>已觸發 {ticks} 次</p>
      <label>
        間隔：
        <select
          value={intervalMs}
          onChange={(event) => setIntervalMs(Number(event.target.value))}
        >
          <option value={1000}>1 秒</option>
          <option value={500}>0.5 秒</option>
        </select>
      </label>
    </div>
  );
}
~~~

**執行方式：**

1. 元件提交後建立計時器。
2. intervalMs 改變時，先用舊設定執行 cleanup，清掉舊計時器，再建立新計時器。
3. 元件卸載時再次清理。

| 依賴寫法 | 一般行為 |
| --- | --- |
| 不傳第二個參數 | 每次元件 commit 後執行 |
| `[]` | 掛載後執行；沒有依賴改變引發的重新同步 |
| `[a, b]` | 掛載後執行；後續 a 或 b 改變時重新同步 |

**重要觀念：**

- cleanup 不只在卸載時執行，也會在依賴改變後、下一次 setup 前執行。
- 開發環境的 Strict Mode 可能額外執行 setup → cleanup → setup，協助找出不完整的清理；不要把 `[]` 理解成「永遠保證只執行一次」。
- 通常先讓瀏覽器繪製再執行一般 Effect，但互動引起的 Effect 可能在繪製前執行；不要依賴它「一定在 paint 後」。
- Effect 不在伺服器端渲染時執行。
- 不要直接寫 `useEffect(async () => ...)`，因為 setup 應回傳 cleanup 或 undefined。需要非同步時，在內部宣告並呼叫 async 函式。
- 可以直接從 props / state 計算出的資料，通常在 render 計算即可，不需要用 Effect 再存另一份 state。

實際 API 查詢的取消與舊回應處理，見附錄 A。

官方文件：[useEffect](https://react.dev/reference/react/useEffect)、[You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)。

## 6. useMemo：快取計算結果

**用途：** 某段純計算較昂貴，且常因不相關的狀態改變而重做時，重用之前的結果。

**語法：** `const result = useMemo(calculateValue, dependencies)`

~~~tsx
import { useMemo, useState } from "react";

type Product = { id: number; name: string; price: number };

const products: Product[] = [
  { id: 1, name: "鍵盤", price: 1200 },
  { id: 2, name: "滑鼠", price: 800 },
  { id: 3, name: "螢幕", price: 6000 },
  { id: 4, name: "筆電", price: 30000 },
];

export default function App() {
  const [maxPrice, setMaxPrice] = useState(10000);
  const [dark, setDark] = useState(false);

  const affordableProducts = useMemo(
    () => products.filter((product) => product.price <= maxPrice),
    [maxPrice],
  );

  return (
    <div
      style={{
        padding: 16,
        background: dark ? "#222" : "#fff",
        color: dark ? "#fff" : "#222",
      }}
    >
      <button onClick={() => setDark((previous) => !previous)}>
        切換背景
      </button>
      <label>
        預算上限：
        <input
          type="number"
          value={maxPrice}
          onChange={(event) => setMaxPrice(Number(event.target.value))}
        />
      </label>
      <ul>
        {affordableProducts.map((product) => (
          <li key={product.id}>
            {product.name}：{product.price}
          </li>
        ))}
      </ul>
    </div>
  );
}
~~~

**執行方式：** 切換背景時，maxPrice 沒變，可重用篩選結果；改預算時重新篩選。products 在元件外宣告，且範例不會修改它，因此不是元件內的反應式依賴。

**注意：**

- 這只有四筆資料，實務上直接 filter 就很足夠；保留 useMemo 是為了清楚展示其行為。
- callback 在 render 時執行，應保持純粹；不要在裡面呼叫 API 或 setState。
- useMemo 不會讓計算變成非同步或移到另一條執行緒，也不會阻止這個元件重新渲染。
- 它是效能最佳化，React 可能丟棄快取；功能正確性不應依賴快取永遠存在。
- 使用並正確設定 React Compiler 時，編譯器可以自動處理許多記憶化工作，降低手寫 useMemo 的需求。

官方文件：[useMemo](https://react.dev/reference/react/useMemo)。

## 7. useCallback：快取函式參照

**用途：** 將 callback 傳給經過 memo 最佳化的子元件，或需要穩定函式參照的自訂 Hook 時使用。

**語法：** `const handler = useCallback(callback, dependencies)`

~~~tsx
import { memo, useCallback, useState } from "react";

type AddButtonProps = {
  onAdd: () => void;
};

const AddButton = memo(function AddButton({ onAdd }: AddButtonProps) {
  return <button onClick={onAdd}>增加數量</button>;
});

export default function App() {
  const [count, setCount] = useState(0);
  const [note, setNote] = useState("");

  const handleAdd = useCallback(() => {
    setCount((previous) => previous + 1);
  }, []);

  return (
    <div>
      <p>數量：{count}</p>
      <label>
        備註：
        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </label>
      <AddButton onAdd={handleAdd} />
    </div>
  );
}
~~~

**執行方式：** App 因備註改變而重新渲染時，handleAdd 的參照通常維持不變；AddButton 的 props 沒變，memo 可以略過不必要的重新渲染。

**注意：**

- useCallback 回傳函式，並不執行它，也不快取「呼叫函式後的結果」。
- 這裡使用函式型更新，因此 callback 不需要讀取 count，依賴可以是空陣列。
- 如果 callback 使用可變的 props 或 state，就需要列入依賴。
- 子元件沒有相應的最佳化，或其他 props 每次都改變時，單加 useCallback 不一定有幫助。
- React Compiler 也能降低手動 useCallback 的需求；先確認實際效能問題。

**與 useMemo 對照：** useMemo 保留「算出來的值」；useCallback 保留「供之後呼叫的函式參照」。

官方文件：[useCallback](https://react.dev/reference/react/useCallback)。

## 8. useLayoutEffect：在畫面繪製前測量與調整布局

**用途：** Tooltip 位置、彈出視窗定位、必須在使用者看到畫面前完成的 DOM 尺寸測量。

**語法：** `useLayoutEffect(setup, dependencies?)`

~~~tsx
import { useLayoutEffect, useRef, useState } from "react";

export default function App() {
  const boxRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [height, setHeight] = useState(0);

  useLayoutEffect(() => {
    const element = boxRef.current;

    if (element !== null) {
      setHeight(element.getBoundingClientRect().height);
    }
  }, [expanded]);

  return (
    <div>
      <button onClick={() => setExpanded((previous) => !previous)}>
        {expanded ? "收合" : "展開"}
      </button>
      <div
        ref={boxRef}
        style={{ width: 240, padding: 12, border: "1px solid #999" }}
      >
        <p>這是一段會改變高度的內容。</p>
        {expanded && (
          <p>展開後增加文字，React 會在繪製前重新測量區塊高度。</p>
        )}
      </div>
      <p>區塊高度：{Math.round(height)} px</p>
    </div>
  );
}
~~~

**執行方式：** React 更新 DOM → 讀取新高度 → 更新 height → 瀏覽器顯示修正後的結果。

**注意：** 它及其同步排程的更新會阻擋瀏覽器繪製，不適合拿來取代所有 useEffect。這個範例只測量掛載及 expanded 改變的情況；若尺寸會因視窗或其他外部因素改變，需要另行觀察尺寸變動。

伺服器端沒有可測量的瀏覽器布局；這類測量應在客戶端進行。

官方文件：[useLayoutEffect](https://react.dev/reference/react/useLayoutEffect)。

## 9. useImperativeHandle：決定父元件可以透過 ref 操作什麼

**用途：** 封裝輸入元件、播放器或編輯器，讓父元件只取得特定操作。

**語法：** `useImperativeHandle(ref, createHandle, dependencies?)`

以下使用 **React 19 的 ref prop 寫法**。

~~~tsx
import { useImperativeHandle, useRef, useState } from "react";
import type { Ref } from "react";

type InputHandle = {
  focus: () => void;
  clear: () => void;
};

type SmartInputProps = {
  ref?: Ref<InputHandle>;
};

function SmartInput({ ref }: SmartInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [text, setText] = useState("");

  useImperativeHandle(
    ref,
    () => ({
      focus() {
        inputRef.current?.focus();
      },
      clear() {
        setText("");
      },
    }),
    [],
  );

  return (
    <label>
      內容：
      <input
        ref={inputRef}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
    </label>
  );
}

export default function App() {
  const smartInputRef = useRef<InputHandle>(null);

  return (
    <div>
      <SmartInput ref={smartInputRef} />
      <button onClick={() => smartInputRef.current?.focus()}>聚焦</button>
      <button onClick={() => smartInputRef.current?.clear()}>清空</button>
    </div>
  );
}
~~~

**執行方式：** 父元件取得的 ref 包含 focus、clear，而不是整個 DOM input。子元件仍自行管理內部狀態。

**注意：**

- React 18 及以前需要用 forwardRef 接收父層 ref；上面範例的 ref prop 寫法需要 React 19。
- 可以用 props 表達的行為通常優先使用 props；例如視窗是否開啟，通常由 `isOpen` 控制即可。
- createHandle 若使用會變動的值，必須列入依賴。這裡只使用穩定的 ref 物件與 state setter，因此可使用空陣列。

官方文件：[useImperativeHandle](https://react.dev/reference/react/useImperativeHandle)。

## 10. useDebugValue：替自訂 Hook 加上除錯標籤

**用途：** 在 React DevTools 檢查元件時，看見自訂 Hook 的摘要，方便辨識複雜狀態。

**語法：** `useDebugValue(value, format?)`

~~~tsx
import { useDebugValue, useState } from "react";

function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);

  useDebugValue(count, (value) => "目前計數：" + value);

  function increase() {
    setCount((previous) => previous + 1);
  }

  return { count, increase };
}

export default function App() {
  const { count, increase } = useCounter();

  return <button onClick={increase}>已點擊 {count} 次</button>;
}
~~~

**執行方式：** 畫面照常顯示計數；在 React DevTools 檢查這個自訂 Hook 時，可以看到格式化的標籤。

**注意：** 不會在網頁上新增文字，也不是 console.log。格式化 callback 可延後到檢查時才執行，適合有較昂貴摘要計算的情況。

官方文件：[useDebugValue](https://react.dev/reference/react/useDebugValue)。

## 11. useId：產生無障礙屬性使用的 ID

**用途：** 建立 label、input、說明文字之間的關聯，避免多個相同元件發生 ID 衝突。

**語法：** `const id = useId()`

~~~tsx
import { useId } from "react";

function EmailField() {
  const inputId = useId();
  const hintId = inputId + "-hint";

  return (
    <div>
      <label htmlFor={inputId}>電子郵件</label>
      <input id={inputId} type="email" aria-describedby={hintId} />
      <p id={hintId}>請輸入可接收通知的電子郵件。</p>
    </div>
  );
}

export default function App() {
  return (
    <div>
      <EmailField />
      <EmailField />
    </div>
  );
}
~~~

**執行方式：** 兩個 EmailField 有各自的 ID，label 不會指到另一個輸入框。

**注意：** 列表的 key 應使用資料本身的穩定識別碼；不要用 useId 產生列表 key、資料庫主鍵或 Promise 的快取鍵。伺服器渲染與客戶端 hydration 的元件樹仍須一致。

官方文件：[useId](https://react.dev/reference/react/useId)。

## 12. useTransition：讓非緊急的畫面更新可以被中斷

**用途：** 使用者正在輸入時，先更新輸入框，再處理較重的結果清單或圖表。

**語法：** `const [isPending, startTransition] = useTransition()`

~~~tsx
import { memo, useState, useTransition } from "react";

const itemNames = Array.from(
  { length: 3000 },
  (_, index) => "設備 " + String(index + 1).padStart(4, "0"),
);

const Results = memo(function Results({ query }: { query: string }) {
  const matches = itemNames.filter((name) => name.includes(query));

  return (
    <ul>
      {matches.map((name) => (
        <li key={name}>{name}</li>
      ))}
    </ul>
  );
});

export default function App() {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [isPending, startTransition] = useTransition();

  function handleChange(nextValue: string) {
    // 輸入框需要立即反映打字。
    setInput(nextValue);

    // 搜尋結果可稍後完成，並可被下一次打字中斷。
    startTransition(() => {
      setQuery(nextValue);
    });
  }

  return (
    <div>
      <label>
        搜尋設備：
        <input
          value={input}
          onChange={(event) => handleChange(event.target.value)}
        />
      </label>
      <p aria-live="polite">{isPending ? "正在更新結果…" : "結果已更新"}</p>
      <Results query={query} />
    </div>
  );
}
~~~

**執行方式：** input 先更新，Results 使用的 query 以 Transition 排程；若使用者又輸入，React 可以優先處理新的緊急更新。

**注意：**

- 不能把控制文字輸入框的 state 更新當作 Transition；輸入框應保持即時。
- startTransition 的 callback 會立即執行。把昂貴的同步計算直接塞進 callback，不會讓那段計算自動變成背景執行。
- React 能在渲染工作之間調度，但不能中途切斷你正在執行的一個巨大同步迴圈；大量 CPU 工作可能仍需拆分或 Web Worker。
- memo 在範例中讓 Results 的 query 沒變時有機會略過渲染。
- React 19 支援 async Action；依目前文件，await 後若要把 setState 標成 Transition，仍需再包一層 startTransition。
- 它不保證一般非同步請求按發送順序完成；資料更新的競爭條件仍需處理。

官方文件：[useTransition](https://react.dev/reference/react/useTransition)。

## 13. useDeferredValue：讓某個值的畫面呈現稍後追上

**用途：** 已經有一個值，例如 props 或輸入 state，想讓較重的子元件稍後接收新值。

**語法：** `const deferredValue = useDeferredValue(value, initialValue?)`

~~~tsx
import { memo, useDeferredValue, useState } from "react";

const records = Array.from(
  { length: 3000 },
  (_, index) => ({ id: index + 1, title: "工單 " + (index + 1) }),
);

const RecordList = memo(function RecordList({ query }: { query: string }) {
  const matches = records.filter((record) => record.title.includes(query));

  return (
    <ul>
      {matches.map((record) => (
        <li key={record.id}>{record.title}</li>
      ))}
    </ul>
  );
});

export default function App() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <div>
      <label>
        搜尋工單：
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      <p aria-live="polite">{isStale ? "結果更新中…" : "結果已更新"}</p>
      <div style={{ opacity: isStale ? 0.5 : 1 }}>
        <RecordList query={deferredQuery} />
      </div>
    </div>
  );
}
~~~

**執行方式：** query 先更新；結果清單暫時沿用舊的 deferredQuery，稍後再追上。

**與 useTransition 比較：**

| 問題 | 比較適合 |
| --- | --- |
| 我能控制這一次 setState，要把它標為非緊急 | useTransition |
| 我收到一個值，希望它的部分呈現可以稍後追上 | useDeferredValue |

**注意：**

- useDeferredValue 沒有固定延遲時間，並非「等 300ms 再更新」。
- 它不會自行減少網路請求。想等停止打字後才查 API，可以採用防抖；附錄的 useDebounce 示範固定時間延後。
- 它也不會直接讓單一巨大同步計算變成可中斷；這點與 useTransition 相同。
- optional initialValue 可讓首次渲染先使用指定初值，再排程背景更新；範例省略它。

官方文件：[useDeferredValue](https://react.dev/reference/react/useDeferredValue)。

## 14. useSyncExternalStore：訂閱 React 外部的狀態來源

**用途：** 外部 store、既有 JavaScript 狀態管理、瀏覽器狀態等，需要在來源變動時通知 React。

**語法：** `const value = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot?)`

~~~tsx
import { useSyncExternalStore } from "react";

function subscribeNetwork(notify: () => void): () => void {
  const events = ["online", "offline"] as const;

  for (const eventName of events) {
    window.addEventListener(eventName, notify);
  }

  return () => {
    for (const eventName of events) {
      window.removeEventListener(eventName, notify);
    }
  };
}

function readNetworkStatus(): boolean {
  return navigator.onLine;
}

function readServerStatus(): boolean {
  // 伺服器與 hydration 階段採用相同初值。
  return true;
}

export default function App() {
  const isOnline = useSyncExternalStore(
    subscribeNetwork,
    readNetworkStatus,
    readServerStatus,
  );

  return <p>瀏覽器連線狀態：{isOnline ? "線上" : "離線"}</p>;
}
~~~

**三個參數的責任：**

1. subscribe：建立訂閱，在外部值改變時呼叫 notify，並回傳取消訂閱函式。
2. getSnapshot：回傳目前可供畫面使用的資料快照。
3. getServerSnapshot：供伺服器渲染及初次 hydration 使用，兩邊必須一致。

**注意：** 資料沒變時，getSnapshot 應回傳相同值或相同參照。每次都回傳新物件，可能造成重複更新。subscribe 放在元件外，可避免因函式參照改變而反覆重新訂閱。

範例顯示的是瀏覽器判定的連線狀態，不能用來保證某個後端 API 一定可連通。

官方文件：[useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore)。

## 15. useInsertionEffect：供樣式函式庫注入動態 CSS

**用途：** 主要供 CSS-in-JS 函式庫作者使用，讓樣式在 layout Effects 測量前就緒。

**語法：** `useInsertionEffect(setup, dependencies?)`

~~~tsx
import { useId, useInsertionEffect, useState } from "react";

function useDemoColor(color: "teal" | "purple"): string {
  const id = useId();
  const className = "hook-demo-" + id.replace(/[^a-zA-Z0-9_-]/g, "");

  useInsertionEffect(() => {
    const styleElement = document.createElement("style");
    styleElement.textContent = "." + className + " { color: " + color + "; }";
    document.head.appendChild(styleElement);

    return () => {
      styleElement.remove();
    };
  }, [className, color]);

  return className;
}

export default function App() {
  const [color, setColor] = useState<"teal" | "purple">("teal");
  const className = useDemoColor(color);

  return (
    <div>
      <p className={className}>這段文字使用動態注入的 CSS。</p>
      <button
        onClick={() =>
          setColor((previous) => (previous === "teal" ? "purple" : "teal"))
        }
      >
        切換顏色
      </button>
    </div>
  );
}
~~~

**注意：**

- 這是瀏覽器端教學示意，沒有完整函式庫的 SSR 樣式擷取、去重或快取機制。
- 一般產品程式只要變更顏色，使用 CSS class 或 style prop 即可，不需要自己注入 style。
- 不能在 useInsertionEffect 內更新 state；也不能假設 ref 已掛上。
- 不要依賴它與 DOM 更新的固定先後關係。可靠的重點是它適合在 layout Effects 前準備樣式。
- 同樣不在伺服器端執行。

官方文件：[useInsertionEffect](https://react.dev/reference/react/useInsertionEffect)。

## 16. useActionState：保存 Action 的結果與執行狀態

**用途：** 提交表單或執行非同步操作時，集中取得結果、錯誤訊息與 pending 狀態。

**語法：** `const [state, dispatchAction, isPending] = useActionState(action, initialState, permalink?)`

Action 接收「前一次 state」和「這次 payload」，回傳下一個 state。與 useReducer 不同，這裡的 Action 可以是 async，也可以執行外部操作。

~~~tsx
import { useActionState } from "react";

type FormState = {
  name: string;
  message: string;
  status: "idle" | "success" | "error";
};

const initialState: FormState = {
  name: "",
  message: "",
  status: "idle",
};

// 模擬 API；輸入 error 可觀察失敗情況。
async function mockSaveName(name: string): Promise<string> {
  await new Promise<void>((resolve) => window.setTimeout(resolve, 700));

  if (name.toLowerCase() === "error") {
    throw new Error("伺服器暫時無法儲存");
  }

  return name;
}

async function saveNameAction(
  previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  const name = String(formData.get("name") ?? "").trim();

  if (name.length < 2) {
    return {
      ...previousState,
      status: "error",
      message: "暱稱至少需要 2 個字元",
    };
  }

  try {
    const savedName = await mockSaveName(name);
    return {
      name: savedName,
      status: "success",
      message: "已儲存：" + savedName,
    };
  } catch (error: unknown) {
    return {
      ...previousState,
      status: "error",
      message: error instanceof Error ? error.message : "儲存失敗",
    };
  }
}

export default function App() {
  const [state, formAction, isPending] = useActionState(
    saveNameAction,
    initialState,
  );

  return (
    <form action={formAction}>
      <label>
        暱稱：
        <input name="name" required minLength={2} disabled={isPending} />
      </label>
      <button type="submit" disabled={isPending}>
        {isPending ? "儲存中…" : "儲存"}
      </button>
      <p role={state.status === "error" ? "alert" : "status"}>
        {state.message}
      </p>
      <p>上次成功儲存的暱稱：{state.name || "尚無資料"}</p>
    </form>
  );
}
~~~

**執行方式：** 表單送出 → formAction 接到 FormData → 執行 saveNameAction → isPending 表示進行中 → Action 回傳結果成為新的 state。

**注意：**

- 從 `react` 匯入 useActionState。
- Action 的第一個參數是 previousState，FormData 是第二個參數；這是常見接錯位置的原因。
- 範例的 form action 自動建立 Action 執行環境。若從一般按鈕手動呼叫 dispatchAction，應放在 startTransition 內。
- 同一個 Hook 的多次 dispatch 會排隊處理；前一次回傳值會提供給下一次 Action。
- 可預期的錯誤可轉成 state 顯示；未處理的拋出錯誤需由 Error Boundary 接住。
- 非受控表單欄位在 Action 正常完成後會自動重設。回傳「錯誤 state」仍屬正常回傳；需要保留欄位內容時，應另外設計受控欄位或回填機制。
- 它能在一般前端 Action 中呼叫 HTTP API，不要求一定使用 Server Functions。
- permalink 是配合特定伺服器表單漸進增強情境的選用參數，這份入門範例不需要。

官方文件：[useActionState](https://react.dev/reference/react/useActionState)。

## 17. useOptimistic：先顯示預期成功的結果

**用途：** 按讚、收藏、新增留言等，先給立即的畫面回饋，再等待真正結果。

**語法：** `const [optimisticState, updateOptimistic] = useOptimistic(baseValue, reducer?)`

~~~tsx
import { useOptimistic, useState, useTransition } from "react";

// 模擬 API，沒有真正寫入後端。
async function mockAddLike(
  currentLikes: number,
  shouldFail: boolean,
): Promise<number> {
  await new Promise<void>((resolve) => window.setTimeout(resolve, 900));

  if (shouldFail) {
    throw new Error("新增按讚失敗，請再試一次");
  }

  return currentLikes + 1;
}

export default function App() {
  const [likes, setLikes] = useState(0);
  const [shouldFail, setShouldFail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    likes,
    (current: number, amount: number) => current + amount,
  );

  function handleLike() {
    setError(null);

    startTransition(async () => {
      addOptimisticLike(1);

      try {
        const confirmedLikes = await mockAddLike(likes, shouldFail);

        // await 後的正式狀態更新再標記為 Transition。
        startTransition(() => {
          setLikes(confirmedLikes);
        });
      } catch (cause: unknown) {
        setError(cause instanceof Error ? cause.message : "操作失敗");
      }
    });
  }

  return (
    <div>
      <p>畫面顯示：{optimisticLikes} 個讚</p>
      <p>已確認：{likes} 個讚</p>
      <label>
        <input
          type="checkbox"
          checked={shouldFail}
          disabled={isPending}
          onChange={(event) => setShouldFail(event.target.checked)}
        />
        模擬失敗
      </label>
      <button onClick={handleLike} disabled={isPending}>
        {isPending ? "確認中…" : "按讚"}
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </div>
  );
}
~~~

**成功路徑：** 立即顯示 +1 → API 回傳 → 更新正式 likes → 暫時值與正式值一致。

**失敗路徑：** 立即顯示 +1 → API 失敗 → Action 結束 → 回到目前的正式 likes，並顯示錯誤。

**注意：**

- 樂觀 setter 應在 Action / Transition 裡呼叫。
- 成功後必須更新正式資料來源；如果只更新樂觀值，Action 結束後仍會回到原本的 baseValue。
- 它管理暫時 UI，不負責送出請求、永久保存資料或撤銷後端交易。
- 回復的是「目前的正式資料」，不一定是操作開始時的資料；其他更新可能同時改變正式資料。
- 範例刻意在請求中停用按鈕，讓單次提交行為清楚；需要允許同時多筆操作時，要進一步處理識別碼、順序與伺服器回應。

官方文件：[useOptimistic](https://react.dev/reference/react/useOptimistic)。

## 18. useFormStatus：讓表單內的子元件取得提交狀態

**用途：** 做可重複使用的送出按鈕，不需要每一層傳遞 pending。

**語法：** `const { pending, data, method, action } = useFormStatus()`

**匯入來源是 `react-dom`。**

~~~tsx
import { useState } from "react";
import { useFormStatus } from "react-dom";

function SubmitButton() {
  const { pending, data } = useFormStatus();
  const submittedName = String(data?.get("name") ?? "");

  return (
    <button type="submit" disabled={pending}>
      {pending ? "正在送出 " + submittedName + "…" : "送出"}
    </button>
  );
}

export default function App() {
  const [message, setMessage] = useState("");

  async function submitAction(formData: FormData): Promise<void> {
    const name = String(formData.get("name") ?? "").trim();
    // 模擬等待，沒有真正呼叫後端。
    await new Promise<void>((resolve) => window.setTimeout(resolve, 800));
    setMessage("已收到：" + name);
  }

  return (
    <form action={submitAction}>
      <label>
        姓名：
        <input name="name" required />
      </label>
      <SubmitButton />
      <p role="status">{message}</p>
    </form>
  );
}
~~~

**執行方式：** SubmitButton 是 form 裡的子元件，因此可以讀到這個表單的 pending 與正在提交的 data。

**最常見的錯誤：** 在 App 最上層呼叫 useFormStatus，然後才在 App 的 return 裡產生 form。Hook 只能讀取「元件上方的表單」，不能讀取同一元件自己產生的表單。

| 回傳屬性 | 意義 |
| --- | --- |
| pending | 所在上層表單是否正在提交 |
| data | 目前提交的 FormData；無進行中的提交時為 null |
| method | 表單的提交方法資訊 |
| action | 函式型 action 的參照；不適用時為 null |

**與 useActionState 比較：** useActionState 管理 Action 的結果與狀態；useFormStatus 讓表單內元件讀取表單提交狀態。兩者可以一起使用。

一般 `onSubmit` 中自行呼叫的任意 Promise，不會只因為放在 form 裡就自動被追蹤；這份範例使用 React 的函式型 action 機制。

官方文件：[useFormStatus](https://react.dev/reference/react-dom/hooks/useFormStatus)。

## 19. useEffectEvent：Effect 事件讀最新值，但不因此重新訂閱

**用途：** 計時器或訂閱收到事件時，需要讀取最新 state / props；但那些值變動不應讓計時器或連線重新建立。

**語法：** `const onEvent = useEffectEvent(callback)`  
**版本：React 19.2 起。**

~~~tsx
import { useEffect, useEffectEvent, useState } from "react";

export default function App() {
  const [count, setCount] = useState(0);
  const [intervalMs, setIntervalMs] = useState(2000);
  const [lastRecord, setLastRecord] = useState("尚未記錄");

  const recordLatestCount = useEffectEvent(() => {
    setLastRecord("計時器讀到的最新 count：" + count);
  });

  useEffect(() => {
    const timerId = window.setInterval(() => {
      recordLatestCount();
    }, intervalMs);

    return () => {
      window.clearInterval(timerId);
    };
  }, [intervalMs]);

  return (
    <div>
      <p>目前 count：{count}</p>
      <button onClick={() => setCount((previous) => previous + 1)}>
        加 1
      </button>
      <label>
        記錄間隔：
        <select
          value={intervalMs}
          onChange={(event) => setIntervalMs(Number(event.target.value))}
        >
          <option value={2000}>2 秒</option>
          <option value={1000}>1 秒</option>
        </select>
      </label>
      <p>{lastRecord}</p>
    </div>
  );
}
~~~

**執行方式：** 增加 count 不會重設計時器；計時器觸發時仍讀得到最新已提交的 count。改 intervalMs 則應重新建立計時器，所以它仍放在依賴陣列。

**注意：**

- Effect Event 要用在 Effect 或由 Effect 建立的事件 callback 中，也可由同元件的其他 Effect Event 呼叫。
- 不要把它當成一般 onClick handler，不要傳給子元件或其他 Hook。
- Effect Event 不放入 Effect 的依賴陣列。
- 不要用它藏掉原本應該讓 Effect 重新同步的依賴。
- 不應依賴它的函式參照固定不變；它與 useCallback 的用途不同。
- 專案的 React 與 Hooks lint 工具需支援這個 API。

官方文件：[useEffectEvent](https://react.dev/reference/react/useEffectEvent)、[React 19.2](https://react.dev/blog/2025/10/01/react-19-2)。

## 補充 1. use：讀取資源的 API，不列入 Hook 數量

React 官方把 `use` 歸類為 API。常見用途是讀取 Context 或 Promise；使用 React 19.3 時，也能配合 react-dom 的 browser API 標記僅在瀏覽器渲染的元件。

**Promise 的基本行為：**

- 還沒完成：最近的 Suspense 顯示 fallback。
- 成功完成：取得解析後的值並渲染。
- 失敗：交給最近的 Error Boundary。

~~~tsx
import { Component, Suspense, use, useState } from "react";
import type { ReactNode } from "react";

type BoundaryProps = { children: ReactNode };
type BoundaryState = { message: string | null };

class MessageBoundary extends Component<BoundaryProps, BoundaryState> {
  override state: BoundaryState = { message: null };

  static getDerivedStateFromError(error: unknown): BoundaryState {
    return {
      message: error instanceof Error ? error.message : "讀取失敗",
    };
  }

  override render() {
    if (this.state.message !== null) {
      return <p role="alert">{this.state.message}</p>;
    }

    return this.props.children;
  }
}

// 模擬非同步資料來源，從事件處理函式呼叫。
async function loadMessage(shouldFail: boolean): Promise<string> {
  await new Promise<void>((resolve) => window.setTimeout(resolve, 800));

  if (shouldFail) {
    throw new Error("訊息載入失敗，請重新讀取");
  }

  return "資料已載入完成";
}

function Message({ promise }: { promise: Promise<string> }) {
  const message = use(promise);
  return <p>{message}</p>;
}

export default function App() {
  const [messagePromise, setMessagePromise] = useState<Promise<string> | null>(
    null,
  );
  const [attempt, setAttempt] = useState(0);

  function beginLoad(shouldFail: boolean) {
    // 在事件中建立 Promise，並保留同一個實例供 render 使用。
    setMessagePromise(loadMessage(shouldFail));
    setAttempt((previous) => previous + 1);
  }

  return (
    <div>
      <button onClick={() => beginLoad(false)}>讀取成功範例</button>
      <button onClick={() => beginLoad(true)}>讀取失敗範例</button>
      <MessageBoundary key={attempt}>
        <Suspense fallback={<p>載入中…</p>}>
          {messagePromise !== null && <Message promise={messagePromise} />}
        </Suspense>
      </MessageBoundary>
    </div>
  );
}
~~~

**注意：**

- Promise 必須能在重新渲染時重用。不要在 Client Component 每次 render 都直接建立新的 fetch Promise 再交給 use。
- 範例在按鈕事件中建立 Promise，並放進 state，避免每次 render 都重建。
- use 可以放在 if 或迴圈內，但仍須在元件或 Hook 內呼叫。
- 不要用 try/catch 包住 use 的 Promise 讀取；用 Error Boundary 處理失敗。
- Context 的用法是 `const value = use(SomeContext)`，讀取最近的上層 Provider；Server Component 不支援讀取 Context。
- React 19.3 的 `use(browser())` 會讓伺服器渲染採用最近的 Suspense fallback，而在瀏覽器正常渲染。它是特殊的瀏覽器環境需求，不是所有 Client Component 都必須加的設定。

官方文件：[use](https://react.dev/reference/react/use)、[React 19.3](https://react.dev/blog/2026/09/09/react-19-3)。

## 補充 2. 自訂 Hook：重用狀態邏輯

自訂 Hook 是以 `use` 開頭，組合其他 Hook 的函式。它共享的是邏輯；不同元件呼叫同一個自訂 Hook，不會因此自動共用同一份 state。

下面製作固定延遲的 **useDebounce**，與 useDeferredValue 的排程行為作比較。

~~~tsx
import { useEffect, useState } from "react";

function useDebounce<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(() => value);

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      setDebouncedValue(() => value);
    }, delayMs);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [value, delayMs]);

  return debouncedValue;
}

export default function App() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 400);

  return (
    <div>
      <label>
        關鍵字：
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      <p>即時值：{query}</p>
      <p>停止變更約 400ms 後的值：{debouncedQuery}</p>
    </div>
  );
}
~~~

**執行方式：** 每次 query 改變都清除上一個 timeout，再等待 400ms；連續輸入時只留下最後一次等待。初次回傳值直接等於傳入的初始值。

**注意：** 瀏覽器計時器不是精準時鐘，主執行緒忙碌時可能更晚觸發。這個 Hook 只延後更新值，若已經送出 API 請求，還需要另外處理取消與回應順序。

`useFetch`、`useLocalStorage`、`useToggle` 等名稱通常是自己或第三方定義，並非 React 內建 Hook。第三方的 `useQuery`、`useForm`、`useNavigate` 等也屬於各自套件的 API。

官方文件：[Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)。

## 附錄 A. useEffect 查詢 API：取消舊請求與防止回應覆蓋

**適用情境：** 依使用者選取的 ID 查詢資料。

**API 合約：** 需要你自己的同源後端提供 `GET /api/users/{id}`，成功回傳 `{ "id": 1, "name": "使用者一" }`。這段不是模擬 API；沒有該端點會顯示錯誤。若後端使用其他欄位大小寫或網域，請調整 URL 與資料解析。

~~~tsx
import { useEffect, useState } from "react";

type User = {
  id: number;
  name: string;
};

type RequestState =
  | { status: "loading"; userId: number }
  | { status: "success"; userId: number; user: User }
  | { status: "error"; userId: number; message: string };

function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "number" &&
    "name" in value &&
    typeof value.name === "string"
  );
}

export default function App() {
  const [userId, setUserId] = useState(1);
  const [request, setRequest] = useState<RequestState>({
    status: "loading",
    userId: 1,
  });

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;

    setRequest({ status: "loading", userId });

    async function loadUser(): Promise<void> {
      try {
        const response = await fetch("/api/users/" + userId, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("查詢失敗，HTTP " + response.status);
        }

        const data: unknown = await response.json();

        if (!isUser(data)) {
          throw new Error("API 回傳格式不符合預期");
        }

        if (!disposed) {
          setRequest({ status: "success", userId, user: data });
        }
      } catch (error: unknown) {
        if (disposed || controller.signal.aborted) {
          return;
        }

        setRequest({
          status: "error",
          userId,
          message: error instanceof Error ? error.message : "發生未知錯誤",
        });
      }
    }

    void loadUser();

    return () => {
      disposed = true;
      controller.abort();
    };
  }, [userId]);

  // ID 已切換，但下一個 Effect 尚未開始時，也不顯示前一位使用者。
  const isLoading =
    request.userId !== userId || request.status === "loading";

  return (
    <div>
      <label>
        使用者：
        <select
          value={userId}
          onChange={(event) => setUserId(Number(event.target.value))}
        >
          <option value={1}>使用者 1</option>
          <option value={2}>使用者 2</option>
          <option value={3}>使用者 3</option>
        </select>
      </label>

      {isLoading ? (
        <p role="status">載入中…</p>
      ) : request.status === "error" ? (
        <p role="alert">{request.message}</p>
      ) : request.status === "success" ? (
        <p>姓名：{request.user.name}</p>
      ) : null}
    </div>
  );
}
~~~

**為什麼需要 cleanup？**

假設先查 ID 1，接著立刻查 ID 2。如果 ID 1 比較慢，較晚回來的 ID 1 可能覆蓋 ID 2。上面用兩道處理：

- AbortController：通知 fetch 取消舊請求或回應讀取。
- disposed：舊 Effect 已失效時，不再把結果寫入 state。

取消前端請求不等於伺服器一定停止處理；這裡處理的是前端生命週期與過期回應。

**查詢與使用者動作要區分：** 隨選取 ID 變動而同步查詢，可以放 Effect。由「送出」或「刪除」按鈕直接觸發的操作，通常放事件處理函式或 Action，不要為了執行操作而繞一層 Effect。

這份範例用來理解底層流程；實際應用若需要快取、重試、請求去重、SSR 載入與重新驗證，可評估框架資料載入機制或合適的查詢工具。

官方文件：[useEffect：Fetching data with Effects](https://react.dev/reference/react/useEffect#fetching-data-with-effects)。

## 附錄 B. 常見選擇比較

### useState、useRef、useMemo

| 問題 | 選擇 | 原因 |
| --- | --- | --- |
| 值變了，畫面要跟著變 | useState / useReducer | 更新 state 會要求 React 處理新的畫面 |
| 跨 render 保存可變資料，但本身不驅動畫面 | useRef | ref.current 可變，不會因此排程 render |
| 純計算昂貴，想在依賴不變時重用結果 | useMemo | 依賴沒變時重用計算快取 |

一般函式內的普通區域變數會隨元件函式再次執行而重新建立，不能代替 state 或 ref。

### 三種 Effect

| Hook | 主要目的 | 時機重點 |
| --- | --- | --- |
| useEffect | 與外部系統同步 | commit 後執行；不保證一律在 paint 後 |
| useLayoutEffect | 測量布局、避免可見的錯位 | 瀏覽器繪製前執行；會阻擋繪製 |
| useInsertionEffect | CSS-in-JS 樣式注入 | 在 layout Effects 前準備樣式；不依賴固定 DOM 更新時點 |

### 非同步與表單

| 需求 | 優先考慮 |
| --- | --- |
| 讓較重的 state 更新不影響輸入操作 | useTransition |
| 已有一個值，讓較重的子畫面稍後追上 | useDeferredValue |
| 記錄 Action 完成後的結果、錯誤與 pending | useActionState |
| 讓 form 內子元件知道是否送出中 | useFormStatus |
| 伺服器回覆前先顯示預期結果 | useOptimistic |
| 讀取可重用的 Promise 並整合 Suspense | use API |

### 常見誤解

| 誤解 | 正確理解 |
| --- | --- |
| 所有資料變化都要用 useEffect 接起來 | 可從既有資料算出的值，通常直接在 render 計算 |
| useEffect 的空依賴保證只執行一次 | 還要考慮重新掛載、Strict Mode 等情況 |
| useCallback 讓函式內的工作不會重做 | 它保留函式參照；實際呼叫時仍會執行 |
| useMemo 會阻止元件重新渲染 | 它只協助重用特定計算結果 |
| useDeferredValue 等於防抖 | 它依 React 排程延後呈現，沒有固定等待時間 |
| Context 的所有子元件一定一起重繪 | 使用該 Context 的消費者會收到更新；其他子元件另受一般渲染規則影響 |
| useOptimistic 已經幫我存入資料庫 | 它只管理暫時呈現，正式資料仍須更新 |
| useEffectEvent 可以拿來移除任何依賴 | 只適合真正由 Effect 觸發、無須因讀取值改變而重新同步的事件邏輯 |

## 延伸閱讀與範圍註記

- [React Hooks 官方清單](https://react.dev/reference/react/hooks)
- [React DOM Hooks 官方清單](https://react.dev/reference/react-dom/hooks)
- [React 版本](https://react.dev/versions)
- [React 19 新增 API](https://react.dev/blog/2024/12/05/react-19)
- [React 19.2：useEffectEvent](https://react.dev/blog/2025/10/01/react-19-2)
- [React 19.3](https://react.dev/blog/2026/09/09/react-19-3)
- [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)
- [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)

舊教學可能使用 `useFormState`：它是 Canary 時期的舊名稱，後來改為 `useActionState` 並棄用舊名稱，不另外算成現代 Hook。

這份筆記以官方公開穩定 API 為範圍，不把 experimental 前綴 API、第三方 Hook、自訂 Hook，或 `memo`、`createContext`、`forwardRef`、`startTransition`、Suspense 等其他 API / 元件誤列為內建 Hook。

檢查紀錄：已核對官方 API 文件、19 個 Hook 章節與 23 段完整 TSX 程式區塊。範例經逐段檢視；本環境未安裝 TypeScript 編譯器及 React 型別套件，未進行專案編譯或瀏覽器執行驗證。

