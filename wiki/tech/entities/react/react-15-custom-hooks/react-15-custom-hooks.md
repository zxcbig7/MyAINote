---
type: concept
domain: tech
tags: [react, custom-hook, usedebounce, useismobile, usesyncexternalstore, usedebugvalue, useid, use, typescript]
sources:
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
  - raw/Web Framework/React/AuthProvider & Route 概念.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 15 章：Custom Hooks — 邏輯可以重用，state 為什麼不會跟著共用

## 徽章的數字不會動

`TasksPage` 長到一百多行，載入、競態處理、reducer 全擠在同一個函式裡。同事開了 PR，把這些搬進 `useTasks`，它收一個搜尋字串，回傳遠端資料與一組操作函式，完整內容本章後面會寫出來。隔天 PM 要頁首顯示任務總數，既然邏輯已經抽出來了，徽章直接再呼叫一次：

```tsx
export const TaskCountBadge = (): React.JSX.Element => {
  const { remote } = useTasks('');
  return <span aria-label="任務數">{remote.status === 'success' ? remote.data.length : '-'}</span>;
};

export const TaskPanel = (): React.JSX.Element => {
  const { remote, addTask } = useTasks('');
  return (
    <section>
      <button type="button" onClick={() => addTask('補測試')}>
        新增
      </button>
      <p>清單 {remote.status === 'success' ? remote.data.length : '-'} 筆</p>
    </section>
  );
};
```

`remote` 是第 05 章的 `RemoteData<Task[]>`。畫面一開始兩邊都是 2。按下「新增」，清單變成 3 筆，徽章還是 2。打開 Network，`/api/tasks` 被打了兩次。

同事的困惑很合理：兩邊呼叫的是同一個 `useTasks`，資料怎麼會不一樣？本章要回答的問題是：custom hook 重用的到底是什麼？答案會決定什麼時候該抽 hook、該怎麼設計它的輸入輸出，也會解釋為什麼 `useIsMobile` 用 `useEffect` 寫是錯的。

## Custom hook 是普通函式，state 住在呼叫它的 component 裡

React 不知道 custom hook 的存在。對 React 來說，`TaskCountBadge` render 時依序呼叫了一個 `useReducer` 和一個 `useEffect`，至於這兩個呼叫是直接寫在 component 裡，還是隔著一層函式，它分不出來。所以呼叫 `useTasks('')` 等於把函式本體就地展開：

```tsx
const TaskCountBadge = (): React.JSX.Element => {
  const [state, dispatch] = useReducer(tasksReducer, initialTasksState);
  useEffect(() => {
    // 載入任務，結果 dispatch 進這個 state
  }, []);
  // ...
};
```

第 08 章說過，state 綁在 component 實例上。`TaskPanel` 展開後也有自己的一份 `useReducer` 和 `useEffect`。兩個實例、兩份 state、兩個 Effect，所以有兩個請求；`addTask` 只 dispatch 到自己那份 reducer，徽章當然不動。

後端的直覺可以這樣接：custom hook 像註冊成 Transient 的服務，每個注入者拿到自己的新實例，共用的是類別定義，不是資料。第 13 章把 Context 比成 Scoped，這裡剛好補上另一端。類比破在生命週期：Transient 物件是你手上的參考，hook 沒有物件可以傳來傳去，它的 state 跟著 component 在樹上的位置活著，靠呼叫順序認領。

要讓兩處看到同一份資料，有三條路，差別在資料住哪裡。徽章和清單的共同祖先不遠時，在祖先呼叫一次，把結果用 props 傳下去，這是第 08 章的 lifting state：

```tsx
const { remote, addTask } = useTasks(debouncedQuery);
// <TaskCountBadge count={tasks.length} />、<TaskList tasks={visibleTasks} ... />
```

距離太遠就在祖先呼叫，再用第 13 章的 Context 往下送。第三條路是讓資料住在 React 外面，每個 hook 只是去訂閱它。第 21 章的 TanStack Query 正是如此，兩個 component 呼叫同一個 `useQuery` 會共用快取、只發一個請求，第 23 章的 Zustand 也一樣。它們看起來打破了本節的規則，其實 hook 裡的 state 依然各自一份，共用的是外面那個 store。本章後面的 `useIsMobile` 會親手做一次最小版本。

## `use` 開頭是給工具看的合約

函式名稱不影響執行，`getTaskFilter` 裡呼叫 `useState` 一樣跑得起來。命名的作用在靜態檢查：第 11 章的兩條 Hook 規則要靠 `eslint-plugin-react-hooks` 執行，而它只能從名字判斷一個函式是不是 hook。

```tsx
export const getTaskFilter = () => {
  const [filter] = useState('all');
  return filter;
};
```

這段會得到 `React Hook "useState" is called in function "getTaskFilter" that is neither a React function component nor a custom React Hook function`。如果它真能過關，問題會在呼叫端爆發：有人寫 `if (isVisible) getTaskFilter()`，看起來只是呼叫普通函式，實際上改變了 Hook 的呼叫順序。名字改成 `useTaskFilter` 之後，同一行就會被標出 `is called conditionally`。

反過來，沒有呼叫任何 Hook 的函式不該取 `use` 開頭。`useFormatDate = (iso) => iso.slice(0, 10)` 不會報錯，但呼叫者從此不能在條件式或迴圈裡用它，換來的是什麼都沒有。它就是 `formatDate`。

另外分清楚來歷：`useFetch`、`useLocalStorage`、`useToggle` 這些名字到處都有，但都不是 React 內建，通常是專案自己或第三方寫的；`useQuery`、`useForm`、`useNavigate` 則屬於各自的套件。

還有一個被 `use` 名字藏起來的成本。hook 內的 state 就是呼叫者的 state，所以 hook 裡 `setState`，整個呼叫者都會 re-render。頁面上一行 `useSomething()` 可能帶著計時器或訂閱。訂閱類的 hook 要盡量放在真正用到它的葉節點，本章的 `TaskFilterBar` 會自己呼叫 `useIsMobile`，不讓 `TasksPage` 代勞。

## 該抽的是一個目的，不是一段生命週期

抽 hook 的門檻不是「重複出現兩次」。只用一次也值得抽，如果它能把「怎麼做」藏在一個說得出目的的名字後面。第 11 章那個同步分頁標題的 Effect 就是例子：

```ts
export const useDocumentTitle = (title: string): void => {
  useEffect(() => {
    document.title = title;
  }, [title]);
};
```

`TasksPage` 從此讀起來是 `useDocumentTitle(...)`，讀的人不必再解析依賴陣列。相反地，只包一個 `useState` 的 hook 什麼都沒藏，只多一層跳轉。

最常見的壞抽法是把生命週期包起來，這通常來自 class component 或其他框架的習慣：

```tsx
export const useMount = (callback) => {
  useEffect(() => {
    callback();
  }, []);
};

export const Page = ({ query }) => {
  const [, setResult] = useState(null);
  useMount(() => {
    setResult(query);
  });
  return null;
};
```

`useMount` 內部會收到 `missing dependency: 'callback'` 警告，有人會把它關掉。更糟的是呼叫端：`Page` 用到了 `query`，lint 卻安靜無聲，因為檢查器不知道 `useMount` 的參數是個 Effect。`query` 改變時任務不會重新載入，症狀和第 11 章的漏列依賴一樣，而且連警告都沒有了。Effect 描述的是「跟什麼同步」，`useMount` 把這個資訊刪掉了。

來源筆記裡有兩個流傳很廣的通用 hook，值得看看它們壞在哪裡。第一個是 `useFetch<T>(url)`，它的 `loading` 初值是 `false`，Effect 又在 commit 之後才跑，所以第一幀會畫出空清單；它沒有取消機制，第 11 章的競態原封不動；`const json: T = await res.json()` 只是告訴編譯器相信我，第 20 章才會用 Zod 守住。把這些全補上，你就在重寫 TanStack Query，那是第 21 章要做的選擇。

第二個是帶 `mountedRef` 的 `useAsync`，省略錯誤處理後的骨架是這樣：

```tsx
export const useAsyncWithMountedRef = <T,>(fn: () => Promise<T>): { execute: () => Promise<void>; isLoading: boolean; data: T | null } => {
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const mountedRef = useRef(true);
  useEffect(
    () => () => {
      mountedRef.current = false;
    },
    [],
  );

  const execute = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    const result = await fn();
    if (mountedRef.current) {
      setData(result);
      setIsLoading(false);
    }
  }, [fn]);

  return { execute, isLoading, data };
};
```

跟著 StrictMode 走一遍（第 09、11 章）：掛載後 React 先跑 cleanup，`mountedRef` 變 `false`，再重新跑 Effect。這個 Effect 的 setup 什麼都沒做，沒有人把它改回 `true`。於是開發環境裡 `execute` 永遠走不進 `if`，`isLoading` 卡在 `true`，`data` 永遠是 `null`，正式環境卻正常。

這個防護本來也不必要。筆記說它防止「unmount 後 setState 造成記憶體洩漏」，那是 React 18 以前的警告，現在卸載後呼叫 setter 不會有任何訊息，React 直接忽略。該處理的是別讓卸載後的工作繼續跑，也就是第 11 章的 `AbortController`。這個 hook 還有一個坑：`useAsync(() => getUsers())` 傳行內函式時，`execute` 每次 render 都換新，放進 `useEffect` 依賴就成了無限迴圈。

## `useDebounce`：延後的是值，不是 setter

第 11 章留下的問題是搜尋框每打一個字就發一個請求。第 08 章也說過 setter 不能延後，受控 input 需要同步更新，否則打不進字。所以要延後的是下游拿來查詢的那個值：輸入框用即時的 `query`，查詢用晚一點才變的版本。

```ts
export const useDebounce = <T>(value: T, delayMs = 300): T => {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
};
```

裡面沒有新東西，全是第 08、11 章的零件，機制在它們的組合。每次呼叫者 render，都把最新的 `value` 傳進來；`value` 一變，Effect 重跑，cleanup 先取消上一個計時器。使用者在 200ms 內接連打字時是這樣：

```text
時間    value     Effect 動作                 回傳值
0ms     ''        初次 render 直接用初值       ''
100ms   '報'      排 timer A（400ms 到期）     ''
300ms   '報表'    取消 A，排 timer B（600ms）  ''
600ms   '報表'    B 到期，setDebounced         '報表'
```

中途的 `'報'` 從未出現在回傳值裡，因為它的計時器在到期前就被 cleanup 取消了。component 卸載時同一個 cleanup 也會執行，不會留下計時器。

這個版本有三個邊界要清楚。第一，`T` 是函式時 `useState(value)` 會把它當 lazy initializer 呼叫（第 08 章），回傳的是它的執行結果。Debounce 函式很少見，真要做就寫成 `useState(() => value)` 和 `setDebounced(() => value)`。第二，瀏覽器計時器不是精準時鐘，主執行緒忙碌時會更晚觸發，300ms 是下限。第三，它只減少請求數，不處理競態。查詢 `'報表'` 的請求還沒回來，使用者又停頓送出 `'報表匯出'`，兩個請求依然會同時在路上，第 11 章的 `AbortController` 不能拿掉。第 30 章的 `useDeferredValue` 長得很像，但它沒有固定延遲，依 React 的 render 排程走，也不適合用來省請求。

## 接上 `useTasks`：搜尋卡在「載入中」

現在把 debounce 接進去。第 13 章的 reducer 裡有 `query`，`queryChanged` 會順便把 `remote` 設成 `loading`。最順手的接法是留著 reducer 不動，只把 Effect 的依賴換掉：

```tsx
const [state, dispatch] = useReducer(naiveReducer, { query: '', remote: { status: 'loading' } });
const debouncedQuery = useDebounce(state.query, 300);

useEffect(() => {
  const controller = new AbortController();
  void fetchTasks({ q: debouncedQuery }, controller.signal).then((tasks) => {
    if (!controller.signal.aborted) dispatch({ type: 'loadSucceeded', tasks });
  });
  return () => controller.abort();
}, [debouncedQuery]);
```

正常打字都沒問題。直到有人打了一個字，馬上按倒退鍵刪掉，畫面就停在「載入中」，再也不會結束，Network 裡也沒有新請求。

順著事件推理。打 `'a'`，`queryChanged` 把 `remote` 設成 `loading`。100ms 後刪回 `''`，又一次 `queryChanged`，`remote` 還是 `loading`。計時器到期時，`debounced` 的新值是 `''`，和舊值相同，React 不 re-render，Effect 的依賴沒變，不會發請求。沒有請求就沒有 `loadSucceeded`，也就沒有任何事件能把 `loading` 收掉。

根本原因是 `remote: loading` 這個 state 假設「query 變了就一定會有請求」，加上 debounce 後這個假設不再成立。第 08 章的原則在這裡又出現了：能算出來的東西不要存。「結果是否屬於目前的查詢」可以比對出來，第 11 章也用過同一招。所以 reducer 拿掉 `query` 和 `queryChanged`，改記這份結果對應哪個查詢：

```ts
export interface TasksState {
  loadedQuery: string | null;
  remote: RemoteData<Task[]>;
  past: Task[][];
}

// tasksReducer 的 load 兩個 case，其餘 case 不變
case 'loadSucceeded':
  return { loadedQuery: action.query, remote: { status: 'success', data: action.tasks }, past: [] };
case 'loadFailed':
  return { loadedQuery: action.query, remote: { status: 'error', message: action.message }, past: [] };
```

`query` 改由呼叫者傳進來，hook 不必知道它有沒有被 debounce 過。這是抽 hook 時最值得花時間想的一點：`useTasks` 只負責「給我一個查詢字串，我給你對應的任務」，延遲與否是另一個 hook 的事，兩者在 `TasksPage` 組合。

```ts
export interface UseTasksResult {
  remote: RemoteData<Task[]>;
  canUndo: boolean;
  addTask: (title: string) => void;
  toggleTask: (id: string) => void;
  removeTask: (id: string) => void;
  undo: () => void;
}

const LOADING: RemoteData<Task[]> = { status: 'loading' };

const describeRemote = (remote: RemoteData<Task[]>): string =>
  remote.status === 'success' ? `${remote.data.length} 筆` : remote.status;

export const useTasks = (query: string): UseTasksResult => {
  const [state, dispatch] = useReducer(tasksReducer, initialTasksState);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    const load = async (): Promise<void> => {
      try {
        const tasks = await fetchTasks({ q: query }, signal);
        if (!signal.aborted) {
          dispatch({ type: 'loadSucceeded', query, tasks });
        }
      } catch (error: unknown) {
        if (!signal.aborted) {
          const message = error instanceof Error ? error.message : '發生未知錯誤';
          dispatch({ type: 'loadFailed', query, message });
        }
      }
    };

    void load();

    return () => {
      controller.abort();
    };
  }, [query]);

  const remote = state.loadedQuery === query ? state.remote : LOADING;
  useDebugValue(remote, describeRemote);

  const addTask = useCallback((title: string): void => {
    dispatch({ type: 'taskAdded', task: createTask(title) });
  }, []);
  const toggleTask = useCallback((id: string): void => {
    dispatch({ type: 'taskToggled', id });
  }, []);
  const removeTask = useCallback((id: string): void => {
    dispatch({ type: 'taskRemoved', id });
  }, []);
  const undo = useCallback((): void => {
    dispatch({ type: 'undoRequested' });
  }, []);

  return { remote, canUndo: state.past.length > 0, addTask, toggleTask, removeTask, undo };
};
```

重走一次剛才的情境：打 `'a'` 再刪掉，傳給 `useTasks` 的 `query` 始終是 `''`，`loadedQuery` 也是 `''`，`remote` 一直是 success，既沒有多餘請求也不會卡住。還多得一個好處：等待 debounce 的 300ms 內舊清單留在畫面上，不會每打一個字就閃一次載入中。連打「報、報表、報表匯」只會多發一個請求，帶的是最後那個字串。

`TasksPage` 的邏輯段縮成組合：

```tsx
const [query, setQuery] = useState('');
const [filter, setFilter] = useState<TaskFilter>('all');
const debouncedQuery = useDebounce(query, SEARCH_DEBOUNCE_MS);
const { remote, canUndo, addTask, toggleTask, removeTask, undo } = useTasks(debouncedQuery);
const formRef = useRef<TaskFormHandle>(null);
const showToast = useShowToast();

const tasks = remote.status === 'success' ? remote.data : [];
const visibleTasks = filter === 'all' ? tasks : tasks.filter((task) => task.status === filter);
const todoCount = tasks.filter((task) => task.status !== 'done').length;

useDocumentTitle(`(${todoCount}) Task Tracker`);
```

Toast 留在頁面，沒進 hook：`useTasks` 管資料，要不要提示使用者是這個畫面的決定。搜尋框改綁 `query` 與 `setQuery`，`handleReset` 也改呼叫 `setQuery('')`。`useDebounce`、`useDocumentTitle` 放在 `hooks/`，`useTasks` 放在頁面旁邊，因為它只屬於這個功能。第 21 章會用 `useTasksQuery` 取代它，到時你會看到這個 hook 的介面幾乎不必改，呼叫端也就不用大動。

## 回傳 tuple 還是 object，看呼叫者要不要改名

`useState` 回傳 tuple，因為它只有兩個值，而且一個 component 裡會呼叫好幾次，每次都要取不同的名字。`useTasks` 有六個欄位，用 tuple 的話呼叫者要背位置，要跳過前三個還得寫 `[, , , toggleTask]`，所以用 object。判準是：一兩個值且常要改名用 tuple，其餘用 object。

自己寫 tuple 時會碰到一個 TypeScript 的坑。`return [isOn, toggle]` 預設被推論成陣列 `(boolean | (() => void))[]`，呼叫 `result[1]()` 會編譯失敗，因為第二個位置也可能是 boolean。要明確告訴編譯器這是固定長度：

```ts
export const useToggle = (initial = false): readonly [boolean, () => void] => {
  const [isOn, setIsOn] = useState(initial);
  const toggle = useCallback(() => setIsOn((current) => !current), []);
  return [isOn, toggle] as const;
};
```

回傳的函式要不要穩定，第 14 章的判準在這裡也適用，只是答案常常偏向要。寫 component 內部的 handler 時，你看得到它被誰用；hook 的函式會交給你看不到的呼叫者，他可能放進 `useEffect` 依賴或傳給 `memo` 過的子元件。`useTasks` 的 `dispatch` 本身穩定，所以 `useCallback` 依賴是空陣列，`undo` 跨 render 都是同一個參考。外層的回傳物件每次 render 都是新的，這沒關係，呼叫者會解構，不會把整包放進依賴。反方向也要留意：hook 接收 callback 參數時，別把它放進內部 Effect 的依賴，否則呼叫者傳行內函式就會反覆重新同步，那是第 11 章 `useEffectEvent` 的場合。

## `useIsMobile`：Effect 版的兩條縫

有些版面差異 CSS 做不到，例如手機上把篩選按鈕列換成 `<select>`，兩者是不同的元素，也有不同的鍵盤行為。來源筆記的寫法是：

```tsx
export const useIsMobileWithEffect = (breakpoint = 768): boolean => {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < breakpoint);

  useEffect(() => {
    const query = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handleChange = (event: MediaQueryListEvent): void => setIsMobile(event.matches);
    query.addEventListener('change', handleChange);
    return () => query.removeEventListener('change', handleChange);
  }, [breakpoint]);

  return isMobile;
};
```

它有值得學的部分：lazy initializer 只在初次讀 `window`；`matchMedia` 的 `change` 只在跨越斷點時觸發，比監聽每一像素都觸發的 `resize` 省事；cleanup 也有寫。但它把瀏覽器的值複製一份到 React state，這份副本有兩條和本尊對不上的縫。

第一條縫在初值之後、訂閱之前。state 在 render 時讀取，訂閱在 commit 之後才建立，中間若跨過斷點（裝置旋轉、其他 layout Effect 改了版面），`change` 事件沒人聽，`isMobile` 就一直錯下去，直到下次跨越斷點。第二條縫在 `breakpoint` 改變時：寬 800 的視窗，`breakpoint` 從 768 改成 1024，Effect 重新訂閱了新的查詢，state 卻不會重算，仍然回傳 `false`。

這類問題都有同一個結構：資料的真正主人在 React 外面。第 11 章的四條規則把這種情況分給了 `useSyncExternalStore`，它讓你不必維護副本，只要回答兩個問題：怎麼知道它變了、現在的值是什麼。

```ts
// 和 Tailwind 的 md 斷點同一條線，JS 和 CSS 對版面的判斷才不會打架
const MOBILE_QUERY = '(width < 48rem)';

const subscribe = (onChange: () => void): (() => void) => {
  const query = window.matchMedia(MOBILE_QUERY);
  query.addEventListener('change', onChange);
  return () => query.removeEventListener('change', onChange);
};

const getSnapshot = (): boolean => window.matchMedia(MOBILE_QUERY).matches;

const getServerSnapshot = (): boolean => false;

export const useIsMobile = (): boolean => useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
```

`subscribe` 建立訂閱並回傳取消函式，來源變動時呼叫 React 給的 `onChange`。`getSnapshot` 回傳目前的值，React 在 render 時讀它，訂閱建立後再比對一次，所以第一條縫補上了：commit 期間跨過斷點，畫面會更新成正確的值。沒有 state 副本，第二條縫也不存在。Tailwind 的 `md` 第 16 章會講，斷點固定成常數也是這個理由。若真要參數化，`subscribe` 得隨參數變動，要用 `useCallback` 包起來。

熟悉 ASP.NET Core 的話，它很像 `IOptionsMonitor<T>`：`CurrentValue` 對應 `getSnapshot`，`OnChange` 對應 `subscribe`，都回傳可取消的訂閱。類比破在讀取頻率：`getSnapshot` 會被 React 反覆呼叫，再用 `Object.is` 比較前後結果，結果不同就更新，於是有第一條合約：資料沒變時必須回傳相同的值。

```tsx
useSyncExternalStore(
  () => () => undefined,
  () => ({ isMobile: false }),
);
```

每次都回傳新物件，比較永遠不同。console 會出現 `The result of getSnapshot should be cached to avoid an infinite loop`，接著 React 丟出 `Maximum update depth exceeded`。回傳 primitive 就沒這問題；要回傳物件得自己快取，第 23 章 Zustand 的 selector 踩的是同一個雷。第二條合約是 `subscribe` 要定義在 component 外面。寫成行內函式時參考每次都變，每次 render 都會取消再重新訂閱，雖然不會出錯，但完全是白工。

第三個參數 `getServerSnapshot` 只在 server render 與 hydration 時用，因為那裡沒有 `window`。server render 時少了它，React 會丟 `Missing getServerSnapshot`；有的話就用它，兩端的初值必須一致。Task Tracker 是純 SPA 用不到，參考實作仍然寫了，第 31 章會回頭談。它也順便點出來源寫法的另一個問題：`window.innerWidth` 在 server 上直接是 `ReferenceError`。

把連線狀態訂閱起來也是同一個模式，`online`、`offline` 兩個事件共用一個 `subscribe`：

```ts
const subscribeNetwork = (onChange: () => void): (() => void) => {
  window.addEventListener('online', onChange);
  window.addEventListener('offline', onChange);
  return () => {
    window.removeEventListener('online', onChange);
    window.removeEventListener('offline', onChange);
  };
};

const getIsOnline = (): boolean => navigator.onLine;

const getIsOnlineOnServer = (): boolean => true;

export const useIsOnline = (): boolean => useSyncExternalStore(subscribeNetwork, getIsOnline, getIsOnlineOnServer);
```

它回報的是瀏覽器的判斷，不保證你的 API 連得上，顯示「離線」橫幅可以，拿來決定要不要發請求不行。

回到開場的問題。`useIsMobile` 不管被幾個 component 呼叫，大家都看到同一個值，因為值住在 `window` 上，這就是前面說的第三條路。Task Tracker 把它放進 `TaskFilterBar`，寬度跨越斷點時只有這個葉節點 re-render：

```tsx
export const TaskFilterBar = ({ filter, onFilterChange }: TaskFilterBarProps): React.JSX.Element => {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <select
        aria-label="篩選"
        value={filter}
        onChange={(event) => {
          if (isTaskFilter(event.target.value)) onFilterChange(event.target.value);
        }}
      >
        {FILTER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    );
  }

  return (
    <div>
      {FILTER_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === filter}
          onClick={() => onFilterChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
};
```

`isTaskFilter` 是第 05 章式的 type guard，檢查字串是否在 `FILTER_OPTIONS` 裡。只是間距或欄數不同就用 CSS media query，別動用這個 hook，JS 判斷的代價是多一次 render，而 CSS 不必。

## 寫 hook 時會碰到的三個內建工具

**`useDebugValue` 替 hook 在 DevTools 加標籤。** 一個頁面用了好幾個 hook，React DevTools 只會列出一堆 state 值。`useTasks` 那行 `useDebugValue(remote, describeRemote)` 讓面板直接顯示 `12 筆` 或 `loading`。它不影響畫面，也不是 `console.log`。第二個參數是格式化函式，只在 DevTools 檢查時才執行，一般 render 不會呼叫，摘要算起來貴也不要緊。官方建議只加在共用函式庫或結構複雜的 hook 上，`useToggle` 這種一眼看穿的不必加。

**`useId` 替可重用的欄位產生不衝突的 id。** `label` 的 `htmlFor`、`aria-describedby` 都要靠 id 關聯（第 27 章會細談）。寫死 id，同一個欄位放兩次，第二個 `label` 就指到第一個輸入框。模組計數器或 `Math.random()` 則破壞第 09 章 render 必須 pure 的要求，SSR 時兩端產生的值也對不上。`useId` 綁在 component 實例上，同一實例跨 render 不變：

```tsx
const useFieldIds = (): { inputId: string; hintId: string } => {
  const inputId = useId();
  return { inputId, hintId: `${inputId}-hint` };
};

export const TitleField = (): React.JSX.Element => {
  const { inputId, hintId } = useFieldIds();
  return (
    <div>
      <label htmlFor={inputId}>標題</label>
      <input id={inputId} aria-describedby={hintId} />
      <p id={hintId}>最多 100 個字</p>
    </div>
  );
};
```

一個 component 要多個 id 時，用同一個前綴衍生，呼叫一次就好。輸出長得像 `_r_1_`，別解析它。它不能當列表 `key`：`key` 必須在父層 `map` 時就決定，而 Hook 不能在迴圈裡呼叫，況且 `key` 要跟著資料走（第 09 章），用 `task.id`。資料庫主鍵和快取鍵同理。

**`use` 名字像 Hook，官方歸類為 API。** 它讀取 Context 或 Promise，和所有 Hook 最大的差別是可以放在條件式與迴圈裡，提前 return 之後也能呼叫：

```tsx
export const TaskMeta = ({ task, isExpanded }: TaskMetaProps): React.JSX.Element | null => {
  if (!isExpanded) return null;
  const density = use(DensityContext);
  return <p data-density={density}>{task.dueDate ?? '未設定'}</p>;
};
```

`useContext` 寫在這個位置會違反 Hook 規則。傳入 Promise 時，`const task = use(taskPromise)` 在等待期間讓最近的 Suspense 顯示 fallback，失敗交給最近的 Error Boundary，所以不要用 `try/catch` 包它。陷阱是 Promise 必須跨 render 重用，在 render 裡現場 `fetch` 再傳進去，每次都是新的 Promise，永遠等不完。Task Tracker 目前不需要它。完整用法留給第 30 章，Suspense 與 Error Boundary 在第 25 章。

## Custom hook 出事時怎麼推理

症狀對到問題，比記規則快：

- 兩個 component 資料不同步：是不是各呼叫一次？state 各一份，往上提或放到 React 外。
- 請求數是 component 數的倍數：同上，每個呼叫都有自己的 Effect。
- 開發環境異常、正式環境正常：看 hook 有沒有在 cleanup 改東西，setup 卻沒還原。
- 卡在 loading、沒有新請求：哪個事件該結束 loading？那個事件在這條路徑上真的會發生嗎？
- 依賴的函式造成迴圈：hook 回傳或接收的函式是否每次 render 都換新。
- 副本和瀏覽器的值對不上：資料的主人在外面，改用 `useSyncExternalStore`。

## 常見誤解

**「useTasks 抽出來，測試就可以脫離 component 了。」** hook 離不開 render，因為 `useState` 要有 fiber 才能運作。測試時 `renderHook` 其實替你建了一個隱形的 component，第 26 章會用到它。真正能脫離 React 測的是 `tasksReducer` 和 `taskOps` 這類純函式，這也是邏輯該盡量往純函式放、hook 只做接線的原因。

**「custom hook 裡的 Effect 會在 hook 被呼叫時跑一次。」** 呼叫 hook 只是登記，Effect 依然在呼叫者 commit 之後才跑，依賴比對也跟每一次 render 走。同一個 render 裡的多個 hook，Effect 按呼叫順序執行，所以 `useTasks` 和 `useDocumentTitle` 交換位置，執行順序也會交換。

**「hook 回傳的值是即時的。」** hook 的回傳值和 state 一樣是這次 render 的快照（第 08 章）。handler 裡呼叫 `addTask` 之後立刻讀 `remote`，讀到的還是舊的。`useTasks` 不會因為多一層函式就逃過這個語意。

**「有 useDebounce，就不必再處理競態了。」** 它只拉開請求的間距。只要回應時間可能超過 debounce 間隔，舊回應就可能晚到，`useTasks` 裡的 abort 和 `signal.aborted` 檢查都要留著。

## 同事會來問你的問題

**「為什麼不把 useTasks 寫成 module 層的 singleton，大家共用就好？」** 那就是自己做 store，第 12、13 章講過模組變數不會通知 React，你得補上訂閱，再用 `useSyncExternalStore` 接，這樣已經是 Zustand 的雛形。還要自己處理快取失效、重試、登出時清資料。要共享 server 資料就等第 21 章，那裡都做好了。

**「這個 hook 回傳十幾個欄位，要拆嗎？」** 看呼叫者是不是都用到。如果每個呼叫者只用其中幾個，又看得出兩三組不相干的責任，那就拆。但 state 彼此有關聯時（`remote` 和 `past` 由同一個 reducer 維護），拆開反而要在 hook 之間同步。hook 也可以呼叫 hook，拆完讓外層組合即可。

**「useDebounce 用來防按鈕連點可以嗎？」** 不適合。它延後的是值，連點防護要處理的是事件，而且通常要第一下立刻生效。送出按鈕的正解是 pending 時 disable（第 17 章）。如果真要 debounce 一個 callback，計時器放 ref 裡，自己寫 event handler，不要透過 state 轉一圈。

**「hook 可以回傳 JSX 嗎？」** 語法上可以，但別這樣做。回傳的元件若在 hook 裡定義，每次 render 都是新的 component 型別，第 09 章講過這會讓 React 卸載重建子樹、丟掉 state。要共用的東西含有畫面，就做成 component，第 35 章會談組合的做法。

## 本章小結

Custom hook 重用的是邏輯，每次呼叫都展開成呼叫者自己的 state 與 Effect，要共用資料就得往上提，或放到 React 外面用 `useSyncExternalStore` 訂閱。`use` 開頭的名字讓工具能檢查規則，好的 hook 以目的命名、不隱藏依賴，也只負責一件事，再由 component 組合。Task Tracker 現在有 `useDebounce`、`useIsMobile`、`useTasks`，邏輯都有了家，但畫面依然是沒有樣式的 HTML，下一章用 Tailwind 把它變得能看。

## 連結

- [[react-14-memoization]] — 上一章：`useCallback` 與參考相等
- [[react-16-tailwind]] — 下一章：`md` 斷點、`cn()`、`Button`
- [[react-08-state]] — 快照、lifting state、衍生值不存 state
- [[react-09-rendering]] — StrictMode、render 必須 pure、`key`
- [[react-11-effects]] — Hook 規則、cleanup、競態、`useEffectEvent`
- [[react-13-reducer-and-context]] — `tasksReducer` 與 Context
- [[react-21-server-state]] — `useTasksQuery` 取代 `useTasks`
- [[react-23-client-state]] — Zustand 與 `useSyncExternalStore`
- [[react-26-testing]] — 用 `renderHook` 測 hook
- [[react-27-accessibility]] — `useId` 與表單標籤
- [[react-30-concurrent-react]] — `use`、`useDeferredValue`
