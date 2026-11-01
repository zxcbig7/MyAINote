---
type: concept
domain: tech
tags: [react, usereducer, usecontext, reducer, context, prop-drilling, discriminated-union, typescript]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 13 章：Reducer 與 Context — 規則變多、資料要穿透很多層時

## 按一次復原，兩件事一起倒退

Task Tracker 要加「復原」。第 10 章的 time travel 給了現成的想法：每次編輯前，把目前的任務清單存進 `past`，復原時取最後一份回來。你在 `TasksPage` 動手，切換先做，刪除是另一位同事當天下午補的：

```tsx
const [tasks, setTasks] = useState<Task[]>(initialTasks);
const [past, setPast] = useState<Task[][]>([]);

const handleToggle = (id: string): void => {
  setPast([...past, tasks]);
  setTasks(toggleTask(tasks, id));
};

const handleRemove = (id: string): void => {
  setTasks(removeTask(tasks, id));
};

const handleUndo = (): void => {
  const previous = past.at(-1);
  if (previous === undefined) return;
  setTasks(previous);
  setPast(past.slice(0, -1));
};
```

測試回報：勾選「補文件」，刪除「寫測試」，按一次復原，「寫測試」回來了，「補文件」的勾也不見了。沒有 error，型別全過，每個 handler 單獨看都對。問題在 `handleRemove` 少了一行，於是歷史裡最新的一份還是切換之前的清單。

同一週還有第二件煩心事。任務列要加「複製標題」按鈕，複製完跳一則 toast。按鈕在 `TaskItem` 裡面，toast 的 state 在最外層，於是 `showToast` 這個 prop 要經過 `TasksPage`、`TaskList`、`TaskItem`，這些 component 自己都用不到它。

兩個症狀對應兩個問題：更新規則散在各處時，怎麼保證規則不被漏掉？資料要穿過很多層時，怎麼不讓中間層當傳話人？第一題的答案是 reducer，第二題是 Context。兩者彼此獨立。

## 規則散在 handler 裡，就只能靠每個人記得

開場的 bug 不是筆誤那麼簡單。這份 state 有一條不變條件：**清單的每次編輯都要留下一筆歷史**。用 `useState` 時，這條規則沒有地方可以寫下來，它只存在於每個 handler 的慣例裡。第四個 handler 的作者只要沒讀過前三個，規則就破了。

後端開發者遇過同樣的事：每個 controller 都要自己記得寫 audit log，總有一個會漏，所以你把寫入收進一個 service。前端也一樣：把「怎麼更新」從 handler 搬出來，集中到一個函式。

這個函式叫 reducer，名字來自第 02 章的 `Array.prototype.reduce`：拿著累積值和下一個元素，算出新的累積值。把累積值換成 state，把元素換成「發生了什麼事」，簽章就出來了：

```ts
const nextState = reducer(currentState, action);
```

handler 不再說「把 `past` 設成這樣、把 `tasks` 設成那樣」，只回報發生的事。比較兩個版本的呼叫端：

```tsx
// useState：handler 是一串指令，規則寫在這裡
setPast([...past, tasks]);
setTasks(removeTask(tasks, id));

// useReducer：handler 只回報事件，規則在 reducer 裡
dispatch({ type: 'taskRemoved', id });
```

新 handler 的作者不可能忘記留歷史，因為那已經不是他的工作了。`useReducer` 把這個函式接上 React：

```tsx
const [state, dispatch] = useReducer(tasksReducer, initialTasksState);
```

流程是單向的：

```text
使用者點「刪除」
  → handler 呼叫 dispatch({ type: 'taskRemoved', id })
  → React 排一次 render
  → render 時 React 呼叫 tasksReducer(目前 state, action)，得到新 state
  → useReducer 交出新 state，component 算出新畫面
```

## dispatch 和 setter 一樣遵守快照，但沒有 stale closure

第 08 章的 state 規則在這裡全部照舊。`dispatch` 之後，這次 render 的 `state` 不會變；同一個事件裡的多次 `dispatch` 會批次處理成一次 render。差別在 reducer 拿到的 `state` 參數永遠是佇列算到當下的最新值，效果等同第 08 章的 functional update。回想那裡的批次匯入，同樣的迴圈換成 reducer：

```tsx
const handleImport = (lines: string[]): void => {
  lines.forEach((line) => dispatch({ type: 'taskAdded', task: createTask(line) }));
  console.log(tasks.length);
};
```

原本有 0 筆，匯入三行，console 印出 `0`（這次 render 的快照），畫面出現 3 筆。

`await` 之後也安全。第 08 章提過 `tasks` 這個舊快照放在 `await` 後面會蓋掉別人的更新，而 action 裡沒有帶整份清單，只有一筆新任務，等待期間別處新增的任務不會被蓋掉。一筆新增在 `await` 之後才 dispatch，等待期間另一筆先進來，最後兩筆都在，先進來的排前面。

還有兩個 `dispatch` 的性質之後會用到。第一，它的 identity 跨 render 穩定，放進依賴陣列或傳下去都不會變。第二，reducer 回傳與傳入**同一個參考**時，React 判定沒有變化，child 不會 render（官方文件提醒 React 可能還是會呼叫該 component 一次才放棄，不要依賴次數）。所以 reducer 判斷「這個事件不需要改任何東西」時，直接 `return state`，不要 `return { ...state }`。

## 用 discriminated union 寫 action，讓編譯器幫你守

Action 的型別是第 05 章 discriminated union 最典型的用途。`type` 是判別欄位，每種事件帶自己需要的資料。Task Tracker 的版本如下（`src/tasksReducer.ts`，`addTask` 等函式來自第 02 章的 `taskOps.ts`，`RemoteData` 來自第 05 章）：

```ts
import { addTask, removeTask, toggleTask } from './taskOps';
import type { RemoteData, Task } from './types';

export interface TasksState {
  query: string;
  remote: RemoteData<Task[]>;
  past: Task[][];
}

export type TasksAction =
  | { type: 'queryChanged'; query: string }
  | { type: 'loadSucceeded'; tasks: Task[] }
  | { type: 'loadFailed'; message: string }
  | { type: 'taskAdded'; task: Task }
  | { type: 'taskToggled'; id: string }
  | { type: 'taskRemoved'; id: string }
  | { type: 'undoRequested' };

export const initialTasksState: TasksState = {
  query: '',
  remote: { status: 'loading' },
  past: [],
};

const applyEdit = (state: TasksState, edit: (tasks: Task[]) => Task[]): TasksState => {
  if (state.remote.status !== 'success') return state;
  const current = state.remote.data;
  return {
    ...state,
    remote: { status: 'success', data: edit(current) },
    past: [...state.past, current],
  };
};

export const tasksReducer = (state: TasksState, action: TasksAction): TasksState => {
  switch (action.type) {
    case 'queryChanged':
      if (action.query === state.query) return state;
      return { query: action.query, remote: { status: 'loading' }, past: [] };
    case 'loadSucceeded':
      return { ...state, remote: { status: 'success', data: action.tasks }, past: [] };
    case 'loadFailed':
      return { ...state, remote: { status: 'error', message: action.message }, past: [] };
    case 'taskAdded':
      return applyEdit(state, (tasks) => addTask(tasks, action.task));
    case 'taskToggled':
      return applyEdit(state, (tasks) => toggleTask(tasks, action.id));
    case 'taskRemoved':
      return applyEdit(state, (tasks) => removeTask(tasks, action.id));
    case 'undoRequested': {
      const previous = state.past.at(-1);
      if (previous === undefined) return state;
      return {
        ...state,
        remote: { status: 'success', data: previous },
        past: state.past.slice(0, -1),
      };
    }
  }
};
```

開場那條不變條件現在落在 `applyEdit` 一個地方：三種編輯都得經過它，就都會留歷史。其他規則也集中了：載入中不能編輯、換搜尋字要同時進入 loading 並清空歷史（否則復原會把上一個搜尋的結果叫回來）。

這裡有三個型別上的決定。第一，`switch` 沒有 `default`。函式宣告了回傳 `TasksState`，所以新增一種 action 卻忘了處理時，TypeScript 會報 TS2366（函式缺少結尾的 return）。很多舊範例寫 `default: return state`，壞處就在這：漏掉的事件會安靜地什麼都不做，症狀是「按了沒反應」，要等使用者回報才發現。第二，`'undoRequested'` 的 case 加了大括號，因為 `switch` 所有 case 共用一個區塊範圍，裡面宣告 `const` 會和其他 case 互相干擾。第三，每個 case 裡的 `action` 都被 narrow 了，在 `taskAdded` 裡讀 `action.id` 是編譯錯誤。

呼叫 `useReducer` 不必寫泛型參數，從 reducer 的簽章推論就夠了。在 `@types/react` 19 裡它的型別參數是 `<S, A extends AnyActionArg>`，其中 `A` 是參數 tuple，舊專案裡的 `useReducer<State, Action>(...)` 或 `useReducer<Reducer<S, A>>(...)` 在這裡會編譯失敗。需要把 `dispatch` 當 prop 傳時，型別寫 `Dispatch<TasksAction>`。

初始 state 要經過計算時有第三個參數，`useReducer(tasksReducer, urlQuery, createTasksState)` 只在初次 render 呼叫 `createTasksState(urlQuery)`，和 `useState` 的 lazy initializer 同一個理由：不要每次 render 都重算。第 19 章把搜尋字放進 URL 時會需要這個形狀。

比較 `{ type: 'setPast', past }` 和 `{ type: 'taskRemoved', id }`：前者只是把 setter 換個拼法，規則還是留在呼叫端，開場的 bug 一樣會發生，還多寫一層 switch。一個實用的檢查是把 action 名稱念成過去式事件：「任務被刪除了」能念，「設定歷史」念不通，後者多半是你在用 reducer 模仿 setter。你也可能在舊範例看到 `payload` 欄位（`{ type: 'ADD_ITEM', payload: item }`），那是 Redux 社群的慣例，`useReducer` 沒有這個要求。

state 裡也不要存算得出來的值。來源筆記常見的購物車範例把 `total` 和 `items` 一起存，每個 case 都要手動同步 `total`，同步錯一次就是第 08 章說的矛盾 state。總價在 render 時從 `items` 算就好，`todoCount` 也是這樣處理。

## Reducer 必須是 pure，StrictMode 會替你抓

Reducer 在 render 期間執行，所以第 09 章對 component 的要求同樣適用於它：相同輸入得到相同輸出，不改動既有的東西。StrictMode 在開發期會把 reducer 呼叫兩次來揭露違規，下面是兩種真人會犯的錯。

第一種是直接改 state，通常是覺得 `past` 反正是自己的陣列（片段省略了 `status` 的檢查）：

```ts
case 'taskToggled':
  state.past.push(state.remote.data);
  return { ...state, remote: { status: 'success', data: toggleTask(state.remote.data, action.id) } };
```

切換一次，`past` 裡多了 **2** 筆。兩次呼叫拿到同一個 `state`，各 push 一次到同一個陣列。症狀是開發時要按兩次復原才會有反應，拿掉 `StrictMode` 就「好了」。請把這當成 bug 的警報，而不是 StrictMode 的問題。

第二種是把副作用放進 reducer，因為「刪除成功要跳 toast」看起來是規則的一部分：

```ts
case 'taskRemoved':
  showToast(`已刪除 ${action.id}`);
  return applyEdit(state, (tasks) => removeTask(tasks, action.id));
```

如果 `showToast` 背後是另一個 component 的 setter，結果是畫面跳出 2 則 toast，console 還有 `Cannot update a component while rendering a different component` 的錯誤，因為這行程式碼是在 render 期間跑的。API 呼叫、計時器、寫 `localStorage` 都屬於這一類。

判斷的原則是：**不純的東西在 handler 做完，結果放進 action**。這也是 `taskAdded` 帶整個 `task` 而不是 `title` 的原因。`createTask` 會呼叫 `crypto.randomUUID()` 和 `new Date()`，放進 reducer 就會每次呼叫產生不同 id，所以它留在 handler：

```tsx
const handleAdd = (title: string): void => {
  dispatch({ type: 'taskAdded', task: createTask(title) });
  showToast(`已新增「${title}」`);
};
```

純函式的回報是測試。不需要 render、不需要假的 DOM，把開場的 bug 寫成一個 Vitest 案例（工具細節在第 26 章）：

```ts
it('復原只退回最後一步', () => {
  const docs = createTask('補文件');
  const tests = createTask('寫測試');
  let state = tasksReducer(initialTasksState, { type: 'loadSucceeded', tasks: [docs, tests] });
  state = tasksReducer(state, { type: 'taskToggled', id: docs.id });
  state = tasksReducer(state, { type: 'taskRemoved', id: tests.id });
  state = tasksReducer(state, { type: 'undoRequested' });
  expect(state.remote).toEqual({
    status: 'success',
    data: [{ ...docs, status: 'done' }, tests],
  });
});
```

## Task Tracker 換上 reducer，filter 留在外面

`TasksPage` 的變化集中在三處，`TaskBoard`、`TaskFilterBar`、`TaskForm` 都沒動。

第一個決定是 `query` 搬進 reducer。第 11 章為了不在 Effect 裡同步 setState，用 `LoadedTasks` 記下「這份結果屬於哪個 query」，再比對導出 loading。現在換搜尋字本身就是事件，`queryChanged` 在同一次更新裡換 query、進入 loading、清空歷史，不再需要比對。Effect 只負責抓資料並回報結果，AbortController 的競態處理照舊：

```tsx
const [state, dispatch] = useReducer(tasksReducer, initialTasksState);
const [filter, setFilter] = useState<TaskFilter>('all');
const formRef = useRef<TaskFormHandle>(null);
const showToast = useShowToast(); // 本章後面定義
const { query, remote, past } = state;

// Effect 的結構和第 12 章相同，load 裡的 setLoaded 換成：
const tasks = await fetchTasks({ q: query }, signal);
if (!signal.aborted) {
  dispatch({ type: 'loadSucceeded', tasks });
}
```

依賴陣列沒有 `dispatch`：它是穩定的，`react-hooks/exhaustive-deps` 認得 `useReducer` 回傳的 `dispatch`，不會要求列入。

第二個決定是 `filter` 留在 `useState`。它不影響 `past`，也不被任何事件連帶改動，放進 reducer 只會多一個 case，換不到任何保證。判斷標準和欄位數量無關，要看更新之間有沒有牽連：

| 情況 | 選擇 | 理由 |
| --- | --- | --- |
| 值獨立變動，例如 `filter`、`isOpen` | `useState` | 沒有規則需要集中 |
| 一個事件要同時改好幾個欄位 | `useReducer` | 一次更新裡維持一致 |
| 欄位之間有不變條件，例如編輯留歷史 | `useReducer` | 規則只寫一次 |
| 下一個值的算法複雜，想單獨測 | `useReducer` | 純函式好測 |

第三，`noticeTimerRef` 和 `lastAddedTitle` 拿掉了，交給下面要寫的 toast。

Reducer 不會讓 state 共用，要跨層需要另一個機制。

## 中間層不用的 prop，是在替別人揹耦合

現在回到第二個症狀。Toast 整個 app 都會用，state 要放在最上層；要用的 component 卻在很深的地方：

```text
App（持有 toasts、showToast）
└── TasksPage       自己要用
    └── TaskList    只是轉交
        └── TaskItem    只是轉交
            └── CopyTitleButton    真正要用
```

這就是 prop drilling。傳兩層的成本是多打幾個字，真正的問題在於：`TaskList` 的 interface 現在宣告依賴一個它從不呼叫的東西，測它要多給一個假函式，搬動 `CopyTitleButton` 要改沿路所有 component。

動用 Context 之前先確認 composition 解不解得了。第 07 章的 `TaskBoard` 用 `children`，所以 `TasksPage` 能直接把 `TaskForm` 放進去，不必經過 `TaskBoard` 的 props，這條路徑上本來就沒有 drilling。很多看起來的 drilling 其實是 layout component 沒開 slot。另外，`onToggle` 從 `TasksPage` 傳到 `TaskList` 再到 `TaskItem` 只有兩層，資料流一眼看得到，就該繼續用 props。Context 是在犧牲這份明確性：看 `CopyTitleButton` 的呼叫端，已經看不出它依賴什麼。官方文件的建議也是先考慮傳 props 或 composition，兩者都不合適才用 Context。

Toast 符合 Context 的條件：很多不同位置、不同層級都要用，未來 `UsersPage`、登入頁也要。主題、語系、使用者偏好、登入狀態都是同類的資料。

## Context 怎麼運作：建立、提供、讀取

Context 有三步。`createContext` 建立一個可被搜尋的「頻道」，並指定預設值；渲染 `<SomeContext value={...}>` 提供值；`useContext(SomeContext)` 讀取。下面用一個最小例子，`Density` 是列表的疏密設定：

```tsx
type Density = 'comfortable' | 'compact';
const DensityContext = createContext<Density>('comfortable');

const DensityLabel = (): React.JSX.Element => {
  const density = useContext(DensityContext);
  return <span>{density}</span>;
};
```

`useContext` 往上找**最近的** Provider，所以可以巢狀覆寫：外層給 `compact`，內層再給 `comfortable`，裡面的 `DensityLabel` 讀到 `comfortable`。完全找不到 Provider 時才用預設值。

一個 component 同時渲染 Provider 又呼叫 `useContext`，讀到的是**外層**的值，因為搜尋從自己的上方開始，自己渲染的 Provider 只影響 children。

```tsx
const DensityShell = (): React.JSX.Element => {
  const density = useContext(DensityContext); // 'comfortable'，不是下面的 'compact'
  return (
    <DensityContext value="compact">
      <span>{density}</span>
      <DensityLabel />
    </DensityContext>
  );
};
```

React 19 起 `<SomeContext value>` 就是 Provider。你會在舊專案和許多範例看到 `<SomeContext.Provider value>`，官方文件稱它為舊寫法，仍能運作。`use(SomeContext)` 也能讀 Context，而且可以放在條件式裡，`use` 的完整介紹在第 15 與第 30 章；一般情況用 `useContext` 就好。

## 預設值用 null，讓忘記包 Provider 立刻炸

很多 Context 沒有合理的預設值。`showToast` 的預設值該是什麼？給一個空函式 `() => {}` 的話，忘記包 Provider 時程式照常執行，toast 就是不出現，你會花一個下午查 CSS。Task Tracker 的做法是預設 `null`，再用一個 hook 統一檢查（`src/toastContext.ts`）：

```ts
import { createContext, useContext } from 'react';

export type ShowToast = (message: string) => void;

export const ToastContext = createContext<ShowToast | null>(null);

export const useShowToast = (): ShowToast => {
  const showToast = useContext(ToastContext);
  if (showToast === null) {
    throw new Error('useShowToast 必須在 <ToastProvider> 裡面使用');
  }
  return showToast;
};
```

呼叫端拿到的型別不含 `null`，不必每處寫 `?.`；少包 Provider 的錯誤從安靜失效變成第一次 render 就拋出。

這裡的判斷條件要小心。不少範例這樣寫：

```tsx
const useCurrentUser = (): User => {
  const user = useContext(CurrentUserContext);
  if (!user) throw new Error('useCurrentUser 必須在 CurrentUserProvider 裡面使用');
  return user;
};
```

如果 Provider 的 `user` 在未登入時是 `null`，這個 hook 會在**包了 Provider** 的情況下拋出「必須在 Provider 裡面使用」，訊息完全誤導：`null` 同時代表「沒有 Provider」和「沒登入」兩件事。修法是讓 Context 的值永遠不是 `null`，把可能為空的資料包進物件：

```tsx
interface CurrentUserValue {
  user: User | null;
}

const CurrentUserContext = createContext<CurrentUserValue | null>(null);

export const useCurrentUser = (): User | null => {
  const value = useContext(CurrentUserContext);
  if (value === null) {
    throw new Error('useCurrentUser 必須在 CurrentUserProvider 裡面使用');
  }
  return value.user;
};
```

同理，值可能是 `0` 或 `''` 時，`!value` 也會誤判，所以一律寫 `=== null`。第 22 章的 `AuthProvider` 會用同樣的形狀，把 `status` 建模成 `loading`、`anonymous`、`authenticated`。

## Context 的重 render 成本從哪裡來

第 09 章說過 render 的來源是 state 更新，並預告 Context 會多一條路：Provider 的 `value` 用 `Object.is` 比較後變了，React 會重新 render **所有**讀這個 Context 的 component，不管中間隔幾層。這裡有三個常被誤判的細節，下面的例子都用這棵樹，`Sidebar` 和 `ThemeBadge` 都包了第 09 章提過的 `memo`，只有 `ThemeBadge` 透過 `useTheme` 讀 Context，`useTheme` 是上一節那種 `null` 加拋錯的 hook，值為 `{ theme, toggleTheme }`：

```tsx
const ThemeBadge = memo((): React.JSX.Element => {
  const { theme } = useTheme();
  return <span>{theme}</span>;
});

const Sidebar = memo((): React.JSX.Element => <ThemeBadge />);
```

**`memo` 擋不住 Context。** 切換主題時，`Sidebar` 沒有 render，`ThemeBadge` 照樣 render。`memo` 比較的是 props，Context 的更新不走 props。它能做的是擋住中間層，讓更新不必沿著樹一路走下來。

**每次 render 建立的物件字面值，等於永遠在變。** 來源筆記的範例幾乎都這樣寫：

```tsx
const ThemeShell = (): React.JSX.Element => {
  const [theme, setTheme] = useState<Theme>('light');
  const [unread, setUnread] = useState(0);
  const toggleTheme = (): void => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  return (
    <ThemeContext value={{ theme, toggleTheme }}>
      <button onClick={() => setUnread(unread + 1)}>未讀 {unread}</button>
      <Sidebar />
    </ThemeContext>
  );
};
```

點「未讀」和主題毫無關係，`ThemeBadge` 卻 render 了。`ThemeShell` 重算時 `{ theme, toggleTheme }` 是新物件，`Object.is` 判定改變。如果 `ThemeShell` 很少更新，這沒什麼影響，不必處理。如果它常更新，把 value 用 `useMemo` 包起來（第 14 章的主題），依賴 `[theme]`，點「未讀」時 `ThemeBadge` 就不再 render。

**只用其中一個欄位，也算讀了整個 Context。** 沒有 selector。這直接影響 toast 的設計。直覺寫法是把清單和函式放一起：

```tsx
return <ToastContext value={{ toasts, showToast }}>{children}</ToastContext>;
```

`CopyTitleButton` 只要 `showToast`，但任何一則 toast 出現或消失，`value` 都變，每個任務列的按鈕全部 render。

治法是**拆分**：按「誰讀」和「多常變」把一個 Context 切成幾個。把 user 和 theme 放在同一個 `AppContext`，改主題時所有只讀 user 的 component 都要重算；各開一個就互不影響。變動頻率差很多的值尤其該分開。函式和資料也常分開，因為函式通常穩定，資料才會變。

Provider 自己的 state 更新時，那些不讀 Context 的 child 為什麼沒跟著 render？因為 `children` 是外層傳進來的 prop，Provider 重算時拿到的是同一批 element，React 看到參考沒變就跳過。這就是為什麼 Provider 要包成獨立 component、接 `children`，把 state 和 Provider 直接寫在有一堆子孫的 `App` 裡，每次更新都會連帶整棵樹。

## Toast context 的完整寫法

把上面的判斷放在一起（`src/ToastProvider.tsx`）。Context 的值只有 `showToast`，toast 清單不需要對外，由 Provider 直接畫出來，所以沒有 consumer 要為清單變動付出代價。清單用 reducer 管，因為 `dispatch` 穩定，可以省掉不少依賴問題；這麼小的 state 用 `useState` 也可以。

```tsx
import { useCallback, useEffect, useReducer } from 'react';
import type { Dispatch, ReactNode } from 'react';
import { ToastContext } from './toastContext';

const TOAST_MS = 3000;

interface Toast {
  id: string;
  message: string;
}

type ToastAction =
  | { type: 'toastShown'; toast: Toast }
  | { type: 'toastExpired'; id: string };

const toastsReducer = (toasts: Toast[], action: ToastAction): Toast[] => {
  switch (action.type) {
    case 'toastShown':
      return [...toasts, action.toast];
    case 'toastExpired':
      return toasts.filter((toast) => toast.id !== action.id);
  }
};

interface ToastItemProps {
  toast: Toast;
  dispatch: Dispatch<ToastAction>;
}

const ToastItem = ({ toast, dispatch }: ToastItemProps): React.JSX.Element => {
  useEffect(() => {
    const timer = setTimeout(() => {
      dispatch({ type: 'toastExpired', id: toast.id });
    }, TOAST_MS);
    return () => {
      clearTimeout(timer);
    };
  }, [toast.id, dispatch]);

  return <li>{toast.message}</li>;
};

interface ToastProviderProps {
  children: ReactNode;
}

export const ToastProvider = ({ children }: ToastProviderProps): React.JSX.Element => {
  const [toasts, dispatch] = useReducer(toastsReducer, []);

  const showToast = useCallback((message: string): void => {
    dispatch({ type: 'toastShown', toast: { id: crypto.randomUUID(), message } });
  }, []);

  return (
    <ToastContext value={showToast}>
      {children}
      <ul role="status" aria-label="通知">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} dispatch={dispatch} />
        ))}
      </ul>
    </ToastContext>
  );
};
```

`useCallback` 讓 `showToast` 跨 render 維持同一個參考（第 14 章細講），於是新增 toast 時 `value` 沒變，呼叫 `showToast` 的 component 都不 render。計時器放在每個 `ToastItem` 的 Effect 裡，因為這是和 `setTimeout` 這個外部系統同步，一則 toast 掛上就開始倒數，卸載就清除，兩則 toast 各算各的：第一則出現 2 秒後再跳第二則，第一則會在第 3 秒消失，第二則在第 5 秒。

`toastContext.ts` 和 `ToastProvider.tsx` 分開，是因為 Vite 的 Fast Refresh 希望一個檔案只匯出 component；hook 和 component 混在同一檔，存檔時容易退回整頁更新。

接線只要在最外層包一次（`src/App.tsx`），`TaskList.tsx` 新增的按鈕不必經過任何 prop：

```tsx
export const App = (): React.JSX.Element => (
  <ToastProvider>
    <TasksPage />
  </ToastProvider>
);
```

```tsx
const CopyTitleButton = ({ title }: CopyTitleButtonProps): React.JSX.Element => {
  const showToast = useShowToast();

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(title);
      showToast(`已複製「${title}」`);
    } catch {
      showToast('無法存取剪貼簿');
    }
  };

  return (
    <button type="button" onClick={() => void handleCopy()}>
      複製標題
    </button>
  );
};
```

`TaskItem` 同時多了 `onRemove`，走一般的 props，交由 `TasksPage` 發出 `taskRemoved` 和 toast。

## Reducer 加 Context 的組合，以及為什麼這裡不用

兩者是獨立的軸，可以自由組合：

| | 留在一個 component | 跨層共用 |
| --- | --- | --- |
| 規則簡單 | `useState` | `useState` + Context |
| 規則多 | `useReducer` | `useReducer` + Context |

右下角是官方文件也介紹的模式：state 和 dispatch 各放一個 Context。

```tsx
export const TasksProvider = ({ children }: { children: ReactNode }): React.JSX.Element => {
  const [state, dispatch] = useReducer(tasksReducer, initialTasksState);
  return (
    <TasksStateContext value={state}>
      <TasksDispatchContext value={dispatch}>{children}</TasksDispatchContext>
    </TasksStateContext>
  );
};
```

因為 `dispatch` 穩定，只發事件、不讀 state 的 component 只用 `TasksDispatchContext`，state 變動時不會 render。Task Tracker 目前沒有採用，任務清單只有 `TasksPage` 底下兩層在用，props 夠清楚；第 21 章任務清單還會搬進 TanStack Query，到時這層 Context 也得拆掉。

## Context 不是狀態管理，也不是 DI 容器

這個組合常被叫做「React 內建的狀態管理」，容易讓人誤會。Context 只負責**傳遞**：值的擁有者仍是上層的 `useState` 或 `useReducer`，更新規則也在那裡。它不提供 selector，消費者不能只訂閱一個欄位；它不提供快取、重新抓取或跨分頁同步。所以它適合變動不頻繁、讀的人很多的值。伺服器資料該交給第 21 章的 server state 工具，高頻或大範圍共享且需要細粒度訂閱的 client state，第 23 章會比較 Zustand。

Context 和 ASP.NET Core 的 DI 確實對得上：Provider 像在某個 scope 註冊服務，`useShowToast`（下面會寫）像建構式注入，內層 Provider 覆寫像子 scope 替換實作，`=== null` 拋錯則是手寫的 `GetRequiredService`，只是要到 render 才會發現。

類比破在兩處。第一，DI 解析出來的是一個物件，服務內部狀態變了，沒有人會通知注入它的 controller；Context 是反應式的，值一變，所有消費者都會重算。把 Context 當服務容器放一個大物件，就是上一節的 render 爆炸。第二，scope 的生命週期是一次 HTTP request；Provider 的 state 綁在樹的位置上（第 09 章），Provider 卸載或 `key` 改變，state 就重置。把 `ToastProvider` 放在會切換的頁面裡面，換頁時 toast 就全消失。

## 常見誤解

**「用了 useReducer，state 就全域了。」** 這個誤解通常來自 Redux 的印象。`useReducer` 是區域 hook，同一個 component 渲染兩次就有兩份獨立的 state，兩個 component 呼叫同一個 reducer 函式也只是共用規則。要共享，得靠 Context 傳下去，或搬到外部 store。

**「Reducer 比 useState 進階，專案大了應該全部換掉。」** Reducer 的成本是多一層間接：讀程式碼的人要從 handler 跳到 switch。它值回票價的前提是有規則需要集中，沒有規則時它就只是冗長的 setter。

**「Context 能取代所有 props。」** 把 `task`、`onToggle` 都放進 Context，每個 `TaskItem` 就只能活在 Provider 底下，無法在測試或別的頁面獨立使用，資料從哪來也看不出來。而且 `TaskItem` 需要的是「這一筆」，同一個 Context 值服務不了清單的每一列。

**「Context 值沒變，消費者就不會 render。」** 只對 Context 這條路成立。父層 render 時，沒包 `memo` 的 child 照樣連帶 render（第 09 章），和 Context 無關。

**「把所有 Provider 都放到 App 最外層比較整齊。」** Provider 放得越高，值的更新影響範圍就可能越大，生命週期也越長。只有任務頁用的東西包在任務頁就好，切走時 state 自然清掉，這通常正是你要的。

## 同事會來問你的問題

**「`dispatch` 之後我馬上讀 `state`，為什麼還是舊的？」** 和 setter 同一個原因。`state` 是這次 render 的 `const`，`dispatch` 只是把 action 排進佇列，reducer 在下次 render 才算出新值。需要立刻用結果，就在 handler 裡用同一個純函式自己算：`const next = tasksReducer(state, action)`，但多半代表那段邏輯該搬進 reducer。

**「我的 reducer 在開發環境跑了兩次，是不是有 bug？」** 不是，StrictMode 刻意呼叫兩次，production 不會。如果兩次造成不同結果（歷史翻倍、toast 跳兩則），那才是真正的 bug，這個機制剛好抓到它。

**「API 呼叫該放在 reducer 裡嗎？」** 不該。Reducer 在 render 期間執行、可能被多呼叫，必須 pure。事件觸發的請求放 handler，同步型的放 Effect，然後把結果 dispatch 進去，就像 `TasksPage` 的 `loadSucceeded`。

## 本章小結

規則散在 handler 裡就只能靠人記得，reducer 把「發生什麼事」和「state 怎麼變」分開，讓不變條件只寫一次，代價是一層間接與 pure 的紀律。Context 解決的是傳遞問題，用 `null` 預設加拋錯的 hook 讓漏包 Provider 立刻現形，並透過拆分和穩定的 `value` 控制重 render 範圍；它不負責管理 state。Task Tracker 現在有了 `tasksReducer` 和 toast，復原也不再倒退兩步。本章有好幾處提到「穩定的參考」，`useMemo` 和 `useCallback` 被順手用了卻沒細說，下一章就來回答它們和 `React.memo` 到底該不該加。

## 連結

- [[react-12-refs]] — 上一章：要記住但不觸發 render 的值
- [[react-14-memoization]] — 下一章：參考相等與 memo 的取捨
- [[react-08-state]] — 快照、functional update、衍生值不存 state
- [[react-09-rendering]] — StrictMode 雙重呼叫、child 連帶 render、state 綁在樹的位置
- [[react-22-authentication]] — `AuthProvider` 的完整實作
- [[react-23-client-state]] — Context 不夠用時的 Zustand
- [[dotnet-web-api]] — ASP.NET Core 的 DI scope
