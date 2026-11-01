---
type: concept
domain: tech
tags: [react, memoization, memo, usememo, usecallback, react-compiler, reference-equality, performance]
sources:
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 14 章：Memoization — useMemo、useCallback、React.memo 該不該加

## PR 加了三種 memo，打字還是卡

Task Tracker 上線試用，有個團隊匯入了三千筆任務。回報很快就來了：在快速新增框打字，每按一個鍵畫面就頓一下。

頁面長這樣。`tasksReducer` 是第 13 章的 reducer，快速新增框的 `draft` 當初圖方便，就直接放在 `TasksPage`：

```tsx
const [tasks, dispatch] = useReducer(tasksReducer, initialTasks);
const [draft, setDraft] = useState('');

const visibleTasks = sortByDueDate(tasks);

const handleToggle = (id: string): void => {
  dispatch({ type: 'toggled', id });
};

const handleRename = (id: string, title: string): void => {
  dispatch({ type: 'renamed', id, title });
};
```

同事讀過第 09 章，知道 parent render 會連帶 render child，於是發了一個 PR：`TaskItem` 包 `memo`，排序包 `useMemo`，`handleToggle` 包 `useCallback`。

```tsx
const MemoTaskItem = memo(TaskItem);

const visibleTasks = useMemo(() => sortByDueDate(tasks), [tasks]);

const handleToggle = useCallback((id: string): void => {
  dispatch({ type: 'toggled', id });
}, []);
```

他在 `TaskItem` 第一行放了 `console.log`，打一個字，還是三千行 log。Reviewer 問他為什麼，他答不出來；有人留言說「反正都包起來比較保險」，也有人說「memo 開銷很大，全拿掉」。

只要再把 `handleRename` 也包上 `useCallback`，log 就消失了，一行都不剩。三千列的命運被一個漏掉的函式決定。這章要回答的問題是：這三個 API 各自擋住了什麼、需要什麼條件才擋得住？答案會告訴你，這個 PR 其實連最該做的那一步都沒做。

## 每次 render，物件和函式都是新的

第 02 章講過值與參考的差別，這裡它變成了效能問題。字串比的是內容，物件和函式比的是「是不是同一個東西」：

```ts
Object.is('todo', 'todo'); // true
Object.is({ status: 'todo' }, { status: 'todo' }); // false
Object.is(() => 1, () => 1); // false
```

`Object.is` 是 React 比較 props、Hook 依賴時用的函式，對這幾種值的行為和 `===` 相同。C# 的讀者可以把它想成 class 的 `ReferenceEquals`：兩個欄位全同的 `TaskDto` 實例並不相等。這個類比破在 C# 還有 `record` 和可覆寫的 `Equals` 能改成值相等，JavaScript 的物件沒有這種開關，也不能替 `Object.is` 客製規則。

再把第 08 章的事實接上來：component 是函式，每次 render 都從頭跑一遍。函式本體裡寫的 `const handleRename = () => ...` 每跑一次就建立一個新函式，`{ status: 'todo' }` 每跑一次就建立一個新物件，JSX 的 `<p>內容</p>` 每跑一次就建立一個新的 element 物件。內容一模一樣，參考全部不同。

平常這完全無害，新函式和舊函式做同一件事，沒有人在比它們。問題只出現在**有人開始比參考**的時候。React 裡會比參考的地方主要有兩個：`memo` 比 props，Hook 比依賴陣列（第 11 章的 `useEffect`，以及本章的 `useMemo`、`useCallback`）。本章的所有內容都從這一點長出來。

## `memo` 只問一件事：每個 prop 都是同一個參考嗎

第 09 章說過，parent render 預設會連帶 render 所有 child，不管 props 有沒有變。`memo` 讓你替某個 component 退出這個預設：

```tsx
const MemoTaskItem = memo(TaskItem);
```

`memo` 回傳一個新的 component。Parent render 到它時，React 拿這次的 props 和上次的逐一用 `Object.is` 比，全部相同就重用上次的結果，`TaskItem` 這個函式不會被呼叫。先宣告再包，DevTools 才有名字可以顯示。

把開場那列放進去走一遍。使用者打了一個字，`draft` 變了，`TasksPage` render，React 來到每一列的 `MemoTaskItem`：

```text
prop       上次                這次                Object.is
task       tasks[0]            tasks[0]            true   (useMemo 沒重算，陣列元素也沒動)
onToggle   useCallback 的函式  useCallback 的函式  true
onRename   第 N 次 render 的   第 N+1 次 render 的 false  --> 整列重新 render
```

只要有一個 false，比較就失敗。這就是「三千列的命運被一個函式決定」：`memo` 是全有或全無，少穩定一個 prop，前面的功夫全部白費，還多付了比較的成本。

順著這張表還能看出一件好事。第 08 章說不可變更新有 structural sharing：`toggleTask` 回傳新陣列，但沒被切換的任務還是原來的物件。所以等 handler 都穩定之後，切換一筆任務時只有那一筆的 `task` 參考變了，其他兩千九百九十九列都能跳過。不可變更新和 `memo` 是一套的。

### 為什麼這不是預設行為

既然這麼好，React 為什麼不替每個 component 自動做？`memo` 的跳過判斷依賴一個前提：資料變了，參考就一定變。React 不能假設你的程式碼都守住這條。假設有人把任務就地改掉：

```tsx
const handleMarkDone = (): void => {
  task.status = 'done';
  setTick(tick + 1);
};
```

`setTick` 是一個只用來觸發 render 的 state setter。`Row` 是沒包 `memo` 的普通 component，`MemoRow` 是 `memo(Row)`，兩者都收這個 `task`，只顯示 `task.status`。按下去之後，`Row` 顯示 `done`，`MemoRow` 還顯示 `todo`：`task` 參考沒變，比較通過，舊畫面留著。預設的「全部重跑」慢一點，但在這種程式碼面前依然畫出正確的畫面。React 選了預設正確、需要時再選擇變快。

所以 `memo` 把一個原本只會變慢的 mutation，變成了畫面錯誤。這也給了你一個判斷：如果拿掉 `memo` 之後功能會壞，或是加上 `memo` 之後功能會壞，問題都在別處，要先修那個問題。官方的定位是 `memo` 只是效能最佳化，不提供「一定不重跑」的保證。

### `memo` 擋不住的東西

`memo` 只管「parent 傳來的 props」。Component 自己的 state 變了，它照樣 render：任務列按「編輯」時 `isEditing` 改變，那一列會重跑，別列不受影響，這正是你要的。它用到的 Context 變了，它也照樣 render，第 13 章的 Toast context 如果被每一列讀取，發一則通知就是三千列一起動，`memo` 幫不上忙。

Context 還有一個連帶問題。Provider 的 `value` 若在 render 裡直接寫物件：

```tsx
<ToastContext value={{ show }}>{children}</ToastContext>
```

每次 provider 所在的 component render，`value` 都是新物件，所有 consumer 都要重跑，即使它們被 `memo` 包著，也即使 `show` 根本沒變。這是 `useMemo` 的標準用途之一，寫成 `const value = useMemo(() => ({ show }), [show]);`，consumer 就不會再被無關的 render 拖著走。

最後一個容易漏看的是 `children`：

```tsx
<MemoPanel>
  <p>內容</p>
</MemoPanel>
```

`children` 也是 prop，而 `<p>內容</p>` 每次都是新 element。Parent 一 render，`MemoPanel` 就跟著 render，字面上看不到任何物件或函式，但 `memo` 已經失效了。

## `useCallback` 的價值全看對方有沒有在比

`useCallback` 給你的是：依賴沒變時，回傳上次那個函式。

```tsx
const handleRename = useCallback((id: string, title: string): void => {
  dispatch({ type: 'renamed', id, title });
}, []);
```

有兩個常見的誤會要先拆掉。第一，它不會省下建立函式的工作：傳給 `useCallback` 的箭頭函式在每次 render 都照樣建立，React 只是決定要回傳新的還是舊的，所以它不可能單靠自己變快，只會多一次依賴比對。第二，它不會讓 child 不 render。把穩定的函式傳給沒包 `memo` 的 child，child 依然跟著 parent 一起 render，因為那條路徑根本沒有人比較 props。

它和 `useMemo` 其實是同一件事，`useCallback(fn, deps)` 等同於 `useMemo(() => fn, deps)`。差別只在保存的東西：`useMemo` 保存函式算出來的值，`useCallback` 保存函式本身，且不會呼叫它。

那什麼時候才有用？只有當這個函式的參考會被拿去比較：

- 傳給 `memo` 包過的 component，而且那個 component 的其他 props 也都穩定。
- 放進另一個 Hook 的依賴陣列。

兩條都不符合，加了不會變快。開場那個 PR 的 `handleToggle` 就符合第一條的前半，卻敗在「其他 props 也都穩定」。

### 依賴會把穩定性吃掉

假設 `tasks` 還是第 08 章的 `useState`。下面這個版本看起來守規矩，依賴都寫齊了，卻幾乎沒有效果：

```tsx
const handleToggle = useCallback((id: string): void => {
  setTasks(toggleTask(tasks, id));
}, [tasks]);
```

`tasks` 一變，`handleToggle` 就是新函式。切換一筆任務，`tasks` 變了，於是每一列的 `onToggle` 都變了，三千列全部 render。你的 `memo` 在最需要它的那個操作上失效。

把函式對 `tasks` 的依賴拿掉才是解法。第 08 章的 functional update 正好做得到：

```tsx
const handleToggle = useCallback((id: string): void => {
  setTasks((current) => toggleTask(current, id));
}, []);
```

依賴是空的，切換時只有被切換的那一列 render。第 13 章的 `dispatch` 也一樣，React 保證 `dispatch` 和 setter 的參考不變，reducer 又能拿到最新 state，所以它們不必列入依賴。把事件邏輯搬進 reducer 除了第 13 章說的好處，這裡又多了一個：handler 不再需要讀 state。

千萬別用「少寫依賴」來達到同樣的效果：

```tsx
const handleDone = useCallback((): void => {
  setDoneCount(doneCount + 1);
}, []);
```

這正是第 08 章的 stale closure。函式抓住的是第一次 render 的 `doneCount`，也就是 0，之後永遠回傳第一次的函式，所以按三次按鈕，畫面還是 1。沒有錯誤訊息，lint 的 `exhaustive-deps` 是唯一會提醒你的東西。

### map 裡的箭頭函式

另一個把 `useCallback` 抵銷的寫法長這樣：

```tsx
{tasks.map((task) => (
  <MemoTaskItem key={task.id} task={task} onToggle={() => handleToggle(task.id)} />
))}
```

`handleToggle` 再穩定也沒用，傳下去的是外面那層每次新建的箭頭函式，所有列都會重跑。這解釋了 `TaskItem` 的 `onToggle` 為什麼設計成 `(id: string) => void`：列自己知道自己的 `id`，parent 傳一個共用的穩定函式就夠。第 07 章定這個型別時還談不上效能，到這裡它多了一層理由。

### 當作 Effect 依賴

第二個用途你在第 11 章見過：其他地方也要用的函式，同時又是 Effect 的依賴。

```tsx
const loadTasks = useCallback(() => fetchTasks(status), [status]);

useEffect(() => {
  void loadTasks();
}, [loadTasks]);
```

`status` 改變才產生新的 `loadTasks`，Effect 才重跑；其他無關的 render 不會重新抓資料。如果沒包 `useCallback`，每次 render 都是新函式，Effect 每次都跑，而它若又 `setState`，就是第 11 章看過的無限迴圈。第 11 章的順序依然適用：函式能搬到 component 外或 Effect 裡就先搬，兩處都要用才輪到這個寫法。

## `useMemo` 有兩份工作

`useMemo` 把計算結果留下來，依賴沒變就直接回傳上次的值：

```tsx
const visibleTasks = useMemo(() => sortByDueDate(tasks), [tasks]);
```

它處理兩種不同的問題，要分開想。第一種是**省計算**：這段計算本身慢，且常因無關的 state 改變而被重跑。第二種是**穩定參考**：算出來的物件或陣列要傳給 `memo` 過的 component，或要放進某個 Hook 的依賴。第二種和計算快慢無關，例如要把任務 id 的 `Set` 傳給一個 `memo` 過的統計 component：

```tsx
const doneIds = useMemo(
  () => new Set(tasks.filter((task) => task.status === 'done').map((task) => task.id)),
  [tasks],
);
```

如果兩種都不是，就沒有理由包。`useMemo(() => 1 + 1, [])` 的成本比計算本身還高，連常數都可以直接搬到 component 外面：模組層級的值不會變，也不必列入依賴。

ASP.NET Core 的讀者可能會想到 `IMemoryCache`，依賴陣列像 cache key。這個直覺能幫你記住「key 變了才重算」，但破在三處：`useMemo` 只存最新一筆，key 一變舊值就被取代；它綁在這個 component 實例上，同一個 component 渲染兩次就各算各的；它也沒有 TTL 可以設。

### 它做不到的事

`useMemo` 常被賦予它沒有的能力，這些邊界值得逐一交代。

它不阻止 component render。依賴沒變時省下的只有傳進去那個函式，component 的其餘部分照跑。它也不會讓計算變成非同步或移到別的執行緒，主執行緒該卡還是卡。第一次 render 一定要計算，所以它不會讓首次載入變快，只會在更新時省事。

傳入的函式是在 render 中執行的，第 09 章對 component 的 pure 要求同樣適用：不能呼叫 API，也不能 `setState`。開 StrictMode 時，React 在開發環境會把這個函式呼叫兩次、丟掉其中一個結果，幫你抓出不 pure 的計算。如果你在裡面 `console.log` 看到兩行，那就是原因。

快取也可能被丟掉。官方列出的情況有：開發時編輯該檔案、component 在首次掛載時 suspend，未來也可能有其他功能這麼做。所以 `useMemo` 只能用來省工，不能用來保證語意。例如靠它確保 `createTask()` 只跑一次，產生的 `id` 哪天就會變；要保證只建立一次，用第 08 章的 `useState` 初始函式或第 12 章的 ref。

最後是依賴也適用參考相等：

```tsx
const query = { status: 'todo' };
const result = useMemo(() => searchTasks(query), [query]);
```

`query` 每次 render 都是新物件，這個 `useMemo` 每次都重算，白包了。把依賴改成原始值 `status`，物件搬進函式裡，它才開始有效。

### 多慢才算慢

官方的經驗法則是：除非在建立或走訪上千個物件，否則通常不算貴；要確定就量，累計時間大約到 1 毫秒以上再考慮 memoize。

```tsx
console.time('sort tasks');
const visibleTasks = sortByDueDate(tasks);
console.timeEnd('sort tasks');
```

量的時候要用接近正式環境的條件：production build 比開發版快，你的機器也可能比使用者的快很多。在開發者工具用 CPU throttling 模擬較慢的裝置，比較接近真實。完整的 Profiler 流程在第 28 章。

## 自訂比較函式是一條容易走歪的路

`memo` 接受第二個參數，讓你自己決定 props 算不算相等。handler 穩定不下來時，很多人會想到它。假設這一列收 `task` 和 `onOpen` 兩個 prop：

```tsx
const Row = memo(TaskRow, (previous, next) => previous.task === next.task);
```

log 立刻消失，看起來成功了。這段程式碼壞在忽略了函式：只要 `task` 沒變，`TaskRow` 手上的 `onOpen` 就一直是舊的。假設 parent 寫 `onOpen={() => console.log(filter)}`，把篩選切到 `todo` 再點這一列，console 印出的是 `all`。比較函式跳過了更新，連帶讓這一列留在舊 render 的 closure 裡，這種 bug 只有特定操作順序才看得到，很難追。

官方的要求是**每個 prop 都要比，包含函式**。另一條歪路是在這裡做深比較，例如 `JSON.stringify` 比兩份資料：比較成本隨資料大小增長，資料結構日後變大時可能比重新 render 更慢。先想辦法穩定 props，比寫比較函式可靠得多，第二個參數留給你量過、也確定每個 prop 都比到的少數情況。

## 把 Task Tracker 修好：先動 state，再談 memo

機制講完了，回到開場。打字會卡，真正的原因是 `draft` 放錯了地方：只有輸入框需要它，它卻住在 `TasksPage`，每打一個字就把整頁拖下水。第 08 章說 state 要放在需要它的最低共同祖先，這裡只有一個 component 需要，就放在那裡：

```tsx
import { useState } from 'react';

interface TaskFormProps {
  onAdd: (title: string) => void;
}

export const TaskForm = ({ onAdd }: TaskFormProps): React.JSX.Element => {
  const [draft, setDraft] = useState('');

  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const title = draft.trim();
    if (title === '') return;
    onAdd(title);
    setDraft('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input aria-label="新任務" value={draft} onChange={(event) => setDraft(event.target.value)} />
      <button type="submit">新增</button>
    </form>
  );
};
```

現在打字時 `TasksPage` 根本不 render，連 `memo` 都還沒加，任務列一行 log 都沒有。如果這就是唯一的回報，修到這裡就該停。這種搬動沒有依賴陣列要維護，也不會出現 stale closure，所以永遠排在 memo 之前。第 09 章把昂貴內容用 `children` 傳進 layout component，是同類的手法。

但切換任務呢？`tasks` 真的變了，`TasksPage` 必須 render，三千列也會跟著跑，而實際上只有一列改變。這是搬 state 解決不了的，正是 `memo` 的條件：經常帶著相同的 props 被連帶 render，且數量多到累積起來昂貴。這裡的判斷有明確理由，才把它加上去：

```tsx
import { memo } from 'react';
import { TaskItem } from './TaskItem';
import type { Task } from './types';

const MemoTaskItem = memo(TaskItem);

interface TaskListProps {
  tasks: Task[];
  onToggle: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export const TaskList = ({ tasks, onToggle, onRename }: TaskListProps): React.JSX.Element => (
  <ul>
    {tasks.map((task) => (
      <MemoTaskItem key={task.id} task={task} onToggle={onToggle} onRename={onRename} />
    ))}
  </ul>
);
```

`TaskItem` 本身一行沒動，只是從 `TaskList.tsx` 搬到自己的 `TaskItem.tsx`。`TasksPage` 要負責把 props 穩定下來，同時它也多了一個會引發無關 render 的統計面板。初始資料暫時用 prop 傳入，好讓這段專注在 memo，第 11 章的載入 Effect 不受影響。

```tsx
import { useCallback, useMemo, useReducer, useState } from 'react';
import { TaskForm } from './TaskForm';
import { TaskList } from './TaskList';
import { createTask, sortByDueDate } from './taskOps';
import { tasksReducer } from './tasksReducer';
import type { Task, TaskFilter } from './types';

interface TasksPageProps {
  initialTasks: Task[];
}

export const TasksPage = ({ initialTasks }: TasksPageProps): React.JSX.Element => {
  const [tasks, dispatch] = useReducer(tasksReducer, initialTasks);
  const [filter, setFilter] = useState<TaskFilter>('all');
  const [isStatsOpen, setIsStatsOpen] = useState(false);

  const visibleTasks = useMemo(() => {
    const matched = filter === 'all' ? tasks : tasks.filter((task) => task.status === filter);
    return sortByDueDate(matched);
  }, [tasks, filter]);

  const handleToggle = useCallback((id: string): void => {
    dispatch({ type: 'toggled', id });
  }, []);

  const handleRename = useCallback((id: string, title: string): void => {
    dispatch({ type: 'renamed', id, title });
  }, []);

  const handleAdd = (title: string): void => {
    dispatch({ type: 'added', task: createTask(title) });
  };

  const doneCount = tasks.filter((task) => task.status === 'done').length;

  return (
    <>
      <TaskForm onAdd={handleAdd} />
      <button type="button" onClick={() => setFilter(filter === 'all' ? 'todo' : 'all')}>
        {filter === 'all' ? '只看待辦' : '顯示全部'}
      </button>
      <button type="button" onClick={() => setIsStatsOpen((isOpen) => !isOpen)}>
        統計
      </button>
      {isStatsOpen && <p role="status">已完成 {doneCount} 筆</p>}
      <TaskList tasks={visibleTasks} onToggle={handleToggle} onRename={handleRename} />
    </>
  );
};
```

這裡每個包與不包都是決定，可以逐一說出理由。

`handleToggle`、`handleRename` 包 `useCallback`，因為它們要傳給三千個 `memo` 過的列。`handleAdd` 沒包，因為 `TaskForm` 沒有 `memo`，它只有一個輸入框，連帶 render 的成本可以忽略。`visibleTasks` 包 `useMemo`，是為了省下開關統計面板時的排序，它的參考穩定與否反而無關緊要：`TaskList` 沒包 `memo`，列比較的是個別的 `task`。`doneCount` 沒包，它只是走訪一次陣列，只有量出來有問題才值得多一個依賴陣列。

各種操作的結果如下，假設頁面上有 N 筆任務：

| 操作 | `TasksPage` | 任務列 render | 排序 |
| --- | --- | --- | --- |
| 在新增框打字 | 不 render | 0 | 不跑 |
| 開關統計面板 | render | 0 | 不跑 |
| 切換一筆任務 | render | 1 | 跑 1 次 |
| 按「只看待辦」 | render | 0（被濾掉的列 unmount） | 跑 1 次 |
| 按某列的「編輯」 | 不 render | 1（該列自己的 state） | 不跑 |

但三千筆的首次掛載、從篩選切回全部時重新掛載的列，`memo` 一點忙都幫不上，它只能跳過已經存在的列。那要靠第 28 章的 virtualization。

## React Compiler 改變了什麼

上面這些手寫的取捨，React 團隊的答案是交給工具。React Compiler 在 2025 年 10 月發布 1.0 穩定版，它在 build time 分析 component 和 Hook，自動插入快取。

把這段沒有任何 `memo`、`useCallback` 的 component 餵給它，`Row` 是收 `title` 和 `onOpen` 的普通 component：

```tsx
export const Board = ({ title }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <section>
      <button onClick={() => setIsOpen((value) => !value)}>統計</button>
      {isOpen && <p>統計已開啟</p>}
      <Row title={title} onOpen={() => console.log(title)} />
    </section>
  );
};
```

編譯輸出中和 `Row` 相關的片段如下（`$` 是 React 替這個實例保管的快取陣列）：

```js
let t3;
if ($[3] !== title) {
  t3 = () => console.log(title);
  $[3] = title;
  $[4] = t3;
} else {
  t3 = $[4];
}
let t4;
if ($[5] !== t3 || $[6] !== title) {
  t4 = <Row title={title} onOpen={t3} />;
  $[5] = t3;
  $[6] = title;
  $[7] = t4;
} else {
  t4 = $[7];
}
```

這段完全可以用本章的機制讀懂：行內箭頭函式被快取，參考穩定了；連 `<Row />` 這個 element 也被快取，只要 `title` 沒變，同一個物件就原封不動交回 React。第 09 章說過，React 看到同一個 element 參考就知道底下不用重算。所以開關統計面板時，沒包 `memo` 的 `Row` 也不會 render。編譯器用的是逐段的快取，比手寫的粒度更細，前面 map 裡那種行內箭頭函式也處理得了。

它還是要靠你守規矩。編譯器假設你遵守第 09 章的 pure 和第 12 章的 ref 規則，看到違規時的策略是放棄最佳化那個 component，保留原樣。在 render 裡寫 `renderCount.current += 1` 的 component，編譯輸出就和原始碼一樣，沒有快取，也沒有任何錯誤訊息。想查哪些 component 被跳過，`eslint-plugin-react-hooks` 的 `refs`、`purity`、`immutability` 等規則不必裝 compiler 就能先把這些違規標出來，recommended 設定已包含。需要手動排除某個 component 時，在函式開頭寫 `'use no memo';` 指令。

它也有範圍。官方明講快取不跨 component 共享，兩個 component 算同一個昂貴結果就算兩次；只有 component 和 Hook 內的程式碼會被處理，一般函式不會。第三方函式庫若違反 React 的假設，也會讓這個最佳化出問題，lint 有 `incompatible-library` 規則提示。它針對的是更新時的 render，一樣無法加速首次掛載。

**Vite 模板預設沒有開。** 模板 README 說明的理由是它對開發與建置效能的影響，所以你用第 00 章方式建的專案不會有 compiler，本章的手動機制還是實際在運作的東西。要新專案直接用模板：

```powershell
npm create vite@latest task-tracker -- --template react-compiler-ts
```

現有專案依 `@vitejs/plugin-react` 的說明安裝 `@rolldown/plugin-babel`、`@babel/core`、`babel-plugin-react-compiler`，並在 `vite.config.ts` 掛上 `babel({ presets: [reactCompilerPreset()] })`。

已有的手寫 memo 怎麼辦？官方建議保留，移除前要測試，因為拿掉可能改變編譯結果。新程式碼則先依賴 compiler，只有需要精準控制（例如確保某個值當 Effect 依賴時穩定）才手寫。無論開不開，參考相等都要懂：你還會讀別人的舊程式、遇到沒開 compiler 的專案，也要能判斷「這個 Effect 為什麼一直跑」。

## 不加的判斷比加的判斷重要

回頭看開場 reviewer 那兩句留言，「都包起來比較保險」和「全拿掉」都沒在回答問題。手寫 memo 的成本主要是維護上的：每個依賴陣列都是一個可能寫錯的地方，寫少了是 stale closure，寫多了白包，而且讀者要多花時間想為什麼這裡有它。遇到「感覺慢」時，建議依這個順序：

1. 量測，確認慢的是 render，且是哪個 component。bundle 和網路造成的慢，memo 無能為力（第 28 章）。
2. 檢查有沒有 Effect 造成的連鎖更新，把衍生值改回 render 裡直接算（第 11 章）。
3. 把 state 下放到真正需要它的地方，或把昂貴的內容改用 `children` 傳入（第 09 章）。
4. 確定 component 又貴又常帶著相同 props 被連帶 render，才加 `memo`，並把它收到的所有 props 穩定下來。
5. 計算本身量得出慢，才加 `useMemo`。

三者的分工可以這樣速查：

| API | 保存什麼 | 誰會受益 | 沒有這個就白包 |
| --- | --- | --- | --- |
| `memo` | 上次的 render 結果 | 被連帶 render 的昂貴 component | 所有 props 參考都穩定 |
| `useCallback` | 函式參考 | `memo` 過的 child、Hook 依賴 | 對方真的在比參考 |
| `useMemo` | 計算結果 | 慢計算、`memo` 過的 child、Hook 依賴 | 計算夠慢，或對方在比參考 |

## 常見誤解

**「useCallback 讓函式只建立一次，可以省記憶體。」** 這個說法把順序搞反了，箭頭函式在呼叫 `useCallback` 之前就已經建立了，每次 render 都一樣。它甚至會讓舊函式多活一陣子，連同它 closure 抓住的那次 render 的值都不能被回收。它賣的是參考穩定，省不到建立成本。

**「`setTasks` 或 `dispatch` 要列入依賴才安全。」** 列了不會錯，但沒有必要。React 保證它們的參考在 component 生命週期內不變，lint 也知道這一點。不過這只限於你直接拿到的那個變數；從 props 或 custom hook 傳進來的同名函式，lint 無從確認，仍會要求列入。

**「我用 Context 傳 handler，就不用處理 props 穩定的問題了。」** 這只是把比較從 `memo` 搬到 Context：provider 的 `value` 參考一變，所有讀它的 component 都要 render，而且連 `memo` 都救不了。你一樣得用 `useMemo` 穩定 `value`，要處理的問題沒有變少。

**「把 memo 全部加上去，至少沒有壞處。」** 官方確實說過，部分團隊選擇盡量 memoize，這對行為沒有害處。代價在可讀性，而且只要有一個值每次都是新的，整條鏈就失效，你以為有保護、其實沒有。想要全面覆蓋的話，評估開 compiler 比手寫划算。

**「用了 React Compiler，舊的 `useMemo` 就可以刪光。」** 官方的建議正好相反：保留，刪之前測試。如果某個 `useMemo` 的值用作 Effect 依賴，它是程式行為的一部分，編譯器的快取策略不一定等價。

## 同事會來問你的問題

**「為什麼我加了 `memo`，Profiler 還是說這列 render 了？」** 先看 props 裡有沒有哪個是 render 中新建的物件、函式或 element，包含 `style={{ ... }}` 和 `children`。全部穩定的話，再看它有沒有讀 Context、自己的 state 有沒有變。React DevTools 的 Profiler 能顯示每次 render 的原因，第 28 章會示範。

**「`useMemo` 和 `useCallback` 什麼時候用哪個？」** 看你要留下什麼。要留下函式本身給別人之後呼叫，用 `useCallback`；要留下計算出來的值，用 `useMemo`。`useMemo(() => handleClick, deps)` 也行得通，只是多包一層函式，所以才有 `useCallback` 這個簡寫。

**「`useEffect` 依賴一個物件 prop，每次都觸發，要在 parent 包 `useMemo` 嗎？」** 可以，但先看有沒有更簡單的修法。如果 Effect 只用到 `options.status`，把 `status` 取出來當依賴，parent 就完全不必動。Parent 的 `useMemo` 是把「這個物件要穩定」的隱性合約放到另一個檔案，換一個 caller 寫法不同就又壞了。

**「React Compiler 開了之後，還需要懂這些嗎？」** 需要懂機制，不必常手寫。Compiler 會默默略過違規的 component，所以你得看得出它為什麼沒被最佳化；你也會遇到手寫 memo 的舊程式碼和第三方 hook。本章前半的知識就是用來讀懂這些情況的。

**「三千筆資料全 `memo` 了還是卡，怎麼辦？」** `memo` 只省 render，比較和 reconciliation 仍要走過這三千個 element，首次掛載更是一列都省不到，而且 DOM 節點本身就是成本。到這個規模該考慮的是不要畫出三千列，第 28 章的 virtualization 只把看得到的部分放進 DOM。

## 本章小結

`memo`、`useCallback`、`useMemo` 都建立在參考相等上：只有當某處真的在比參考，保留舊參考才會省到東西，而 `memo` 要求全部 props 都通過才算數。Task Tracker 的打字卡頓靠把 `draft` 搬進 `TaskForm` 就解決了，切換任務的連帶 render 才輪到 `memo`、穩定的 handler 和不可變更新一起出力。React Compiler 能代勞大部分快取，但它預設沒開，也會略過違規的 component，所以機制仍然要懂。下一章把 `TasksPage` 裡越長越多的 Hook 邏輯抽成 custom hook，你會看到回傳的函式和物件要不要穩定，又成了 Hook 作者要替呼叫者想的問題。

## 連結

- 上一章：[[react-13-reducer-and-context]]
- 下一章：[[react-15-custom-hooks]]
- 相關章節：[[react-02-javascript-for-react]]、[[react-07-props]]、[[react-08-state]]、[[react-09-rendering]]、[[react-11-effects]]、[[react-12-refs]]、[[react-28-performance]]、[[react-30-concurrent-react]]
