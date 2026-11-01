---
type: concept
domain: tech
tags: [react, state, usestate, snapshot, stale-closure, batching, immutability, lifting-state, controlled-input, typescript]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 08 章：State — 為什麼 setter 之後讀到的還是舊值

## 清單顯示 3 筆，提示卻寫 2 筆

上一章結束時，Task Tracker 的 `TaskList` 和 `TaskItem` 接好了 props，畫面卻不會動。你動手加第一個功能：按下「新增」，清單多一筆，並在上方顯示一行提示。`createTask` 是建立一筆新任務的函式，本章最後會寫出來。程式碼看起來沒什麼好出錯的：

```tsx
const handleAdd = (): void => {
  setTasks([...tasks, createTask('新任務')]);
  setNotice(`已新增，目前共 ${tasks.length} 筆任務`);
};
```

原本有 2 筆任務。按下去，清單變成 3 筆，提示卻寫「目前共 2 筆任務」。

你猜是 state 更新需要時間，於是在 `setTasks` 後面等一下，再把變數裡的筆數和 DOM 裡的筆數都印出來比對：

```tsx
const handleAdd = async (): Promise<void> => {
  setTasks([...tasks, createTask('新任務')]);
  await new Promise((resolve) => setTimeout(resolve, 50));
  console.log('變數', tasks.length, 'DOM', document.querySelectorAll('li').length);
};
```

console 印出 `變數 2 DOM 3`。五十毫秒後畫面上明明已經有 3 個 `<li>`，同一個函式裡的 `tasks.length` 還是 2。等待沒有用，再等多久都一樣。

過幾天你做批次匯入，迴圈跑三次，每次 `setTasks([...tasks, createTask(line)])`，匯入 A、B、C 三行，清單上只出現 C。

這三個症狀來自同一件事，而「state 更新是非同步的」這個常見說法解釋不了第二個症狀：非同步的東西等一下就該好了，這裡卻永遠等不到。本章要回答的問題是：setter 被呼叫的那一刻，到底發生了什麼？答案會順便告訴你為什麼 React 要求不可變更新、state 該放在哪個 component、哪些值根本不該是 state。讀完這章，Task Tracker 可以新增、切換、篩選，而且你說得出每個值為什麼放在那裡。

## 區域變數為什麼記不住畫面上的東西

先退一步，假裝 `useState` 不存在。篩選器要記住目前選了哪個狀態，最直覺的寫法是一個區域變數：

```tsx
const FilterBarWithLocalVar = (): React.JSX.Element => {
  let filter = 'all';
  return (
    <>
      <button
        onClick={() => {
          filter = 'done';
          console.log(filter);
        }}
      >
        已完成
      </button>
      <p role="status">{filter}</p>
    </>
  );
};
```

點下按鈕，console 印出 `done`，畫面上卻還是 `all`。這裡有兩個獨立的問題。第一，改變數這個動作 React 看不到。第 06 章說過 component 是回傳畫面描述的函式，它已經回傳過了，React 手上那份描述是舊的，沒有人通知它該重算。第二，就算有別的原因讓 React 再次呼叫這個函式（例如父層更新），第一行 `let filter = 'all'` 也會再跑一次，你改過的值隨著上次呼叫結束而消失。

那把變數搬到函式外面呢？模組層級的變數確實能跨呼叫存活，第二個問題解決了，第一個還在，並多了第三個：同一個模組變數被這個 component 的所有實例共用。Task Tracker 同時開兩個看板時，點左邊那個把模組變數改成 `left`，右邊那個下次 render 時也顯示 `left`，一個看板的篩選跑到了另一個身上。

所以我們需要一個同時做到三件事的東西：值活得比單次函式呼叫久、改它會讓 React 重算畫面、每個 component 實例各有一份。這就是 `useState` 的合約：

```tsx
const [filter, setFilter] = useState<TaskFilter>('all');
```

`TaskFilter` 是 `'all'` 加上三種任務狀態的 union，本章最後定義。`useState` 回傳一個長度為 2 的 tuple：這次 render 的值，以及用來要求更新的 setter。回傳 tuple 而不是物件，是為了讓你用陣列解構自由命名，一個 component 裡有好幾個 state 時不用寫 `{ value: filter, set: setFilter }` 這種改名。命名慣例是 `[xxx, setXxx]`，Boolean 用 `[isOpen, setIsOpen]`。

值實際存在 React 裡，綁在這個 component 實例上。函式每次被呼叫時，`useState` 去把目前的值拿給你。因為 React 靠呼叫順序認出哪個 `useState` 對應哪個值，它必須寫在 component 頂層，不能放進 `if` 或迴圈；完整規則在第 11 章，由來在第 36 章。至於實例怎麼被認出來、什麼時候值會被清掉，是第 09 章的主題。

什麼時候該用 state？問一個問題就夠：這個值變了，畫面要跟著變嗎？要變，才考慮 state。不用變、但要跨 render 記住的（計時器 id、前一次的捲動位置）是第 12 章 `useRef` 的工作。可以從現有資料算出來的，則連 state 都不需要，這點本章後面會細談。

## setter 沒有改變數：state 是這次 render 的快照

現在可以回答開場的問題了。關鍵在這行的 `const`：

```tsx
const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
```

`tasks` 是 `const`，是這次函式呼叫的區域常數，沒有任何程式碼能把它改掉，React 也不能。呼叫 `setTasks` 時，React 記下「下次 render 要用這個新值」，然後排一次 render；當下這個 `tasks` 完全不受影響。等 React 再次呼叫 component，`useState` 交出新值，它被放進**另一次函式呼叫的另一個 `const`**，也叫 `tasks`，但和上一個毫無關係。

handler 是 render 當中建立的函式，第 02 章講過 closure：函式會抓住建立時所在範圍的變數。被抓住的是一個永遠不會變的 `const`，而且它專屬於那一次 render。把開場的流程攤開來是這樣：

```text
第 1 次 render，tasks 是 [A, B]
  建立 handleAdd，closure 抓住這個 tasks
  回傳畫面：2 筆
      |
      | 使用者點擊，執行第 1 次 render 建立的 handleAdd
      |   setTasks(...)：記下新值，排一次 render，tasks 沒動
      |   tasks.length：仍然是 2
      |
第 2 次 render，tasks 是 [A, B, 新任務]
  這是另一次函式呼叫、另一個 tasks
  建立新的 handleAdd，closure 抓住新的 tasks
  回傳畫面：3 筆
```

這就解釋了 `await` 為什麼沒用。五十毫秒後第 2 次 render 早就完成，DOM 已經是 3 筆，但 `await` 之後繼續執行的還是第 1 次 render 建立的那個 `handleAdd`，它看到的永遠是第 1 次的 `tasks`。這也是為什麼「state 更新是非同步的」這句話會誤導人：它暗示等一下變數就會變，實際上這個變數從頭到尾沒有機會變。

熟悉 Oracle 的話，可以用 read consistency 來想：一個查詢看到的是語句開始那一刻的一致資料，別人中途 commit 也不會影響它。一次 render 裡的所有 props、state 和 handler 也是這樣，全部來自同一個時間點，不會讀到一半變掉。類比破在這裡：Oracle 的查詢結束後你可以再查一次拿到新資料，而舊 render 的 handler 沒有任何「再查一次」的方式，`tasks` 這個名字在它的範圍裡永遠指向舊值。需要在舊 closure 裡讀到最新值，得靠第 11 章的 `useEffectEvent` 或第 12 章的 ref。

這個語意多數時候正是你要的。想像新增任務後延遲顯示一則訊息，同時立刻清空輸入框：

```tsx
const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>): void => {
  event.preventDefault();
  setDraft('');
  setTimeout(() => {
    console.log(`已建立「${draft}」`);
  }, 10);
};
```

輸入「補測試」後送出，console 印出 `已建立「補測試」`，雖然這時輸入框已經清空了。如果 `draft` 是一個隨時會變的即時值，這則訊息會變成 `已建立「」`，或者變成使用者接著打的下一筆內容。一次 render 建立的 handler，看到的就是使用者按下按鈕時畫面上那份資料。

回到開場的提示訊息，正確修法有兩種，選哪個看你需要什麼。如果提示只是這次新增的結果，先把下一個值算出來放進變數，兩個 setter 都用它：

```tsx
const handleAdd = (): void => {
  const nextTasks = addTask(tasks, createTask('新任務'));
  setTasks(nextTasks);
  setNotice(`已新增，目前共 ${nextTasks.length} 筆任務`);
};
```

更好的做法是問：提示裡的筆數需要存嗎？筆數已經在 `tasks` 裡了。真正的新資訊只有「剛才新增了哪一筆」，存這個就夠，文字在 render 時組出來。這樣提示永遠不會和清單對不上，即使任務之後被刪除，筆數也跟著對：

```tsx
const NoticeDerived = (): React.JSX.Element => {
  const [tasks, setTasks] = useState<Task[]>(() => [createTask('A'), createTask('B')]);
  const [lastAddedTitle, setLastAddedTitle] = useState<string | null>(null);

  const handleAdd = (title: string): void => {
    const task = createTask(title);
    setTasks((prev) => addTask(prev, task));
    setLastAddedTitle(title);
  };

  return (
    <>
      <button onClick={() => handleAdd('新任務')}>新增</button>
      {lastAddedTitle !== null && (
        <p role="status">
          已新增「{lastAddedTitle}」，目前共 {tasks.length} 筆任務
        </p>
      )}
    </>
  );
};
```

`setTasks((prev) => ...)` 這種傳函式的寫法下一節會解釋，`useState` 收到函式的意思則在「初始值只用一次」那節。不要用的第三種修法是加一個 `useEffect` 監看 `tasks` 再 `setNotice`：它多了一次 render，而且把「使用者按了新增」這個事件的邏輯拆到別處。第 11 章會專門談為什麼這類 Effect 不該存在。

## 連續呼叫 setter 為什麼會丟資料

理解快照之後，批次匯入的 bug 就能一步步算出來。這是出錯的版本：

```tsx
const BulkImportBug = (): React.JSX.Element => {
  const [tasks, setTasks] = useState<Task[]>([]);

  const handleImport = (lines: string[]): void => {
    for (const line of lines) {
      setTasks([...tasks, createTask(line)]);
    }
  };

  return (
    <>
      <button onClick={() => handleImport(['A', 'B', 'C'])}>匯入</button>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>{task.title}</li>
        ))}
      </ul>
    </>
  );
};
```

迴圈跑三次，`tasks` 三次都是這次 render 的空陣列，所以三次分別算出 `[A]`、`[B]`、`[C]`。React 不會每呼叫一次 setter 就立刻處理，而是先把它們收起來（原因見下一節），等處理時依序走過：把 state 換成 `[A]`，換成 `[B]`，換成 `[C]`。三個都是完整的新值，後面的覆蓋前面的，最後只剩 C。寫 SQL 的人對這個情況很熟，這就是 lost update：先 `SELECT` 讀出 2，算出 3，再 `UPDATE ... SET total = 3`，好幾個人照做，結果還是 3。修法也一樣，把語句改成 `SET total = total + 1`，讓資料庫用**當下的值**計算。

setter 也有這種寫法。傳給它一個函式，意思就從「把 state 換成這個值」變成「用目前的值算出下一個值」：

```tsx
const handleImport = (lines: string[]): void => {
  for (const line of lines) {
    const task = createTask(line);
    setTasks((prev) => addTask(prev, task));
  }
};
```

這個函式叫 **updater**（或 functional update）。匯入 A、B、C，三筆全部都在。你可以把 setter 想成把東西放進一條 queue，React 處理時從頭走一遍：拿目前的 state 當起點，遇到值就直接取代，遇到函式就把目前結果傳進去，算出下一個結果。`prev` 就是走到這一項時的結果。下面這段把兩種混在一起，每一步都可以手算。起點是 state 為 `[A]`，`b`、`c` 是兩筆已經建立好的任務（標題分別是 B、C）：

```tsx
const handleClick = (): void => {
  setTasks((prev) => addTask(prev, b));
  setTasks([]);
  setTasks((prev) => addTask(prev, c));
};
```

| queue 裡的項目 | 進來的 state | 算出的 state |
| --- | --- | --- |
| `(prev) => addTask(prev, b)` | `[A]` | `[A, B]` |
| `[]` | `[A, B]` | `[]` |
| `(prev) => addTask(prev, c)` | `[]` | `[C]` |

點擊前畫面是 `[A]`。點擊後 React 一次把三項算完，畫面直接變成 `[C]`，`[A, B]` 和 `[]` 從來沒被畫出來。

SQL 的類比破在一個地方：`SET total = total + 1` 要靠資料庫的鎖處理多個連線同時寫入，React 的 updater 跟併發寫入無關。瀏覽器的 JavaScript 跑在單一執行緒上，沒有兩個 setter 同時執行這回事。updater 解決的只有「我手上這個值已經不是最新的」。

什麼時候用 updater？下一個值是從前一個值算出來的，就用它，例如新增、切換、刪除；下一個值與前一個值無關，直接傳值，例如 `setFilter('done')`、`setDraft('')`。有人會問「那我確定事件只觸發一次時，`setTasks(addTask(tasks, task))` 也對吧？」對，開場的第一種修法就這樣寫，官方文件也不要求一律改成 updater。本書的 Task Tracker 對 `tasks` 一律用 updater，理由很實際：`tasks` 是會被多條路徑更新的清單，現在是單次事件，下週就可能被放進 `setTimeout` 或 `await` 後面，「舊 render 的函式還活著」那節的 stale closure 就會發生。

updater 有一個硬性要求：必須是 pure function，不能改 `prev`，也不能做其他副作用。這不是風格問題，因為它會被多跑一次。Vite 模板預設在 `main.tsx` 把整個 App 包在 `<StrictMode>` 裡，這是開發模式專用的檢查，會故意把 updater 跑兩次，讓不 pure 的寫法現形（細節在第 09 章）。看這個寫錯的版本：

```tsx
const handleAdd = (title: string): void => {
  const task = createTask(title);
  setTasks((prev) => {
    prev.push(task);
    return [...prev];
  });
};
```

兩次執行都把 `task` push 進同一個 `prev`，所以任務重複。連續新增 `t1`、`t2`、`t3`，畫面依序是 `t1`、`t1,t2,t2`、`t1,t2,t2,t3,t3`：第一次看起來正常，連點才現形。所以只點一次的手動測試抓不到它，把 StrictMode 拿掉也只是把症狀藏起來。修法是不去動 `prev`：`setTasks((prev) => [...prev, task])`。

同樣因為執行時機不由你決定，updater 裡不要讀事件物件。這種寫法在表單裡很自然：

```tsx
<input
  value={form.title}
  onChange={(event) => setForm((prev) => ({ ...prev, title: event.currentTarget.value }))}
/>
```

輸入第一個字沒事，第二個字就丟 `TypeError`：讀不到 `null` 的 `value`。React 只在呼叫你的 handler 期間把 `currentTarget` 指向元素，handler 一回傳就設回 `null`，而 updater 多半在這之後才執行；第一個字沒事，只是因為 React 有時會在 setter 呼叫當下先算一次。舊文章會說這是 event pooling，那個機制 React 17 起已經移除，這裡是另一回事。`event.target` 不會被設回 `null`，但它讀的是 DOM 此刻的值，事件當下的快照它給不了：把上面的 updater 放進 `setTimeout`，受控 input 早就被還原，讀到的是空字串。所以一律先把值讀出來，closure 抓住的就是當下的字串：

```tsx
<input
  value={form.title}
  onChange={(event) => {
    const { value } = event.target;
    setForm((prev) => ({ ...prev, title: value }));
  }}
/>
```

## 呼叫幾次 setter，就 render 幾次嗎

前面說 React 會把 setter 收起來再處理，現在來看為什麼。後端開發者看到一個 handler 裡有兩三個 setter，第一個反應常常是：這不就 render 好幾次？會想把它們併成一個物件來省效能。不會。React 會等當下這段程式碼跑完，才把累積的更新一次處理掉，這叫 **batching**。你可以自己看到它：

```tsx
const FilterAndPage = (): React.JSX.Element => {
  const [filter, setFilter] = useState<TaskFilter>('all');
  const [page, setPage] = useState(3);
  console.log('render', filter, page);

  const handleShowDone = (): void => {
    setFilter('done');
    setPage(1);
  };

  return <button onClick={handleShowDone}>只看已完成</button>;
};
```

按一下按鈕，console 只出現 `render done 1`，不會有 `render done 3` 這種篩選改了、頁碼還沒改的中間狀態，畫面也就不會閃過它。在 StrictMode 下這一行會印兩次，那是同一次 render 被執行兩遍，和前面 updater 跑兩次同理，內容是相同的。

歷史上 React 17 以前只在 React 事件處理器裡做 batching，`setTimeout` 和 Promise callback 裡的每個 setter 都各 render 一次；舊文章說「非同步裡要自己包 `unstable_batchedUpdates`」指的就是那個時代。React 18 起所有來源都自動 batching（官方 React 18 公告），`setTimeout` 和 Promise callback 裡連續呼叫兩個 setter，也都只 render 一次。

batching 的邊界不是 handler 函式的大括號，是 React 下一次把累積的更新處理掉（flush）的時機。在點擊這類事件的 handler 裡，React 排在 microtask（第 03 章）做這件事，所以第一個 `await` 之前的 setter 自成一批，`await` 之後的是另一批：

```tsx
const handleClick = async (): Promise<void> => {
  setFilter('done');
  await new Promise((resolve) => setTimeout(resolve, 5));
  setPage(2);
};
```

這段會 render 兩次，中間那次畫面的狀態是 `done` 配舊頁碼。`await Promise.resolve()` 也一樣切成兩次。但 `await` 並不是一律切開：同樣的三行放在 `setTimeout` 的 callback 裡，React 的 flush 排得比較晚，`await Promise.resolve()` 前後的 setter 會併成一次 render。不必背這些組合，你要記住的是做法：`setIsLoading(true)`、`await fetch(...)`、`setTasks(...)` 本來就該分兩次畫，而必須一起生效的幾個 setter，要放在同一段同步程式碼裡，中間不要隔 `await`。

兩次分開的點擊也是兩批。真人的兩次點擊之間，React 一定已經把第一批 render 並 commit 完，第二次點擊的 handler 是新 render 建立的，看到的是新值。所以連點兩次，`setSelected([...selected, id])` 這種直接傳值的寫法結果是對的。也因此開場的 bug 只會出現在同一批之內，手動點按鈕時你看不出來，要等到有人寫迴圈才爆。這個保證只限於真實的事件：程式碼在同一段同步流程裡連續呼叫兩次 `button.click()`，中間沒有 flush 的機會，兩次 handler 用的是同一份舊 closure。

還有一個容易忽略的情況：setter 傳入的值與目前的 state 相同，React 會用 `Object.is` 比較後跳過這次更新，子 component 不會 render。component 本身則不一定：剛 mount、還沒更新過時是 0 次；state 改過之後，第一次同值 setter 可能讓 component 本身再被呼叫一次，之後才是 0 次。官方文件也提醒「有些情況 React 可能會先呼叫 component 一次才決定放棄」，所以不要把「一定是 0 次」寫進邏輯裡。

少數情況你需要 DOM 立刻更新。例如新增任務後馬上捲到最後一筆，而 `scrollIntoView` 要的元素這時還沒畫出來。`listRef` 是指向 `<ul>` 的 ref（第 12 章會講），`react-dom` 的 `flushSync` 則要求 React 在 callback 結束前就把裡面的更新處理完並寫進 DOM：

```tsx
const handleAdd = (title: string): void => {
  const task = createTask(title);
  flushSync(() => {
    setTasks((prev) => addTask(prev, task));
  });
  listRef.current?.lastElementChild?.scrollIntoView();
};
```

拿掉 `flushSync`，`lastElementChild` 抓到的是舊的最後一筆，因為這行執行時新的 `<li>` 還不存在。它貴在兩處：同步 render 會卡住當下的執行，而且它切開了 batch，同一個 handler 裡後面的 setter 會多一次 render。官方文件提醒它可能明顯傷害效能，只留給「下一行就要讀 DOM」的情境。

## 舊 render 的函式還活著，會怎樣

快照的語意在同步程式碼裡很好懂，出事通常是在**時間拉長之後**。stale closure 是你之後在 Effect、timer、WebSocket 裡反覆會碰到的問題，只是換了場景。

Task Tracker 要做「刪除可以反悔」：按下刪除後等 3 秒才真的從清單移除。

```tsx
const handleRemoveLater = (id: string): void => {
  setTimeout(() => {
    setTasks(removeTask(tasks, id));
  }, 3000);
};
```

單獨試這個功能完全正常。現在照這個順序操作，清單一開始是 A、B：

1. 第 0 秒：使用者刪除 A。第 1 次 render 建立的 `handleRemoveLater` 啟動計時器，計時器的 callback 抓住第 1 次 render 的 `tasks`，也就是 `[A, B]`。
2. 第 1 秒：使用者新增 C。state 變成 `[A, B, C]`，第 2 次 render 完成，畫面顯示三筆。計時器 callback 的 closure 沒有任何變化，因為那是第 1 次 render 的東西。
3. 第 3 秒：計時器觸發。`removeTask(tasks, id)` 用的是 `[A, B]`，算出 `[B]`，然後把 state **整個換成** `[B]`。

最後畫面只剩 B，使用者剛新增的 C 消失了，沒有任何錯誤訊息。這就是 **stale closure**：一個舊 render 建立的函式活得比那次 render 久，用它手上過期的快照去做決定。它和快照是同一件事，差別只在於同步時快照還是最新的，時間拉長後就過期了。

症狀的特徵是資料「偶爾」被蓋回去，而且要在等待期間有其他操作才會發生。這也是它難查的原因，開發時一個人慢慢點，幾乎不會碰到。

這個案例用 updater 就能修好，因為它要的是「根據目前的清單算下一份」，不需要看快照：

```tsx
setTasks((prev) => removeTask(prev, id));
```

第 3 秒時 React 拿當下的 `[A, B, C]` 當 `prev`，結果是 `[B, C]`。

updater 解得掉的只有「寫」。如果舊 closure 是要**讀**最新值去做別的事，它幫不上忙：

```tsx
<button
  onClick={() => {
    setTimeout(() => console.log(tasks.length), 3000);
  }}
>
  回報
</button>
```

原本 2 筆，按下回報後立刻新增一筆，3 秒後印出來的還是 2。這種情況要先判斷你要的到底是什麼。「使用者按下按鈕那一刻有幾筆」就是快照的正確語意，這段程式碼沒有錯。如果真的要「3 秒後當下的筆數」，就需要一個存活在 render 之外的東西，第 12 章的 ref 是答案；放在 Effect 裡的版本則是第 11 章的 `useEffectEvent`。

## 為什麼不能直接改物件和陣列

第 02 章的 `taskOps.ts` 寫成回傳新陣列的純函式，當時只說這樣比較安全，現在可以講清楚理由了：React 判斷 state 有沒有變，用的是 `Object.is`，對物件和陣列來說就是比**參考**。

```tsx
const handleAdd = (): void => {
  tasks.push(newTask);
  setTasks(tasks);
};
```

`push` 改的是同一個陣列，`setTasks(tasks)` 交回去的還是同一個參考，`Object.is` 判定相同，React 跳過更新，畫面停在原本的筆數。React 為什麼不做深度比較？因為那要走遍整棵資料，每個 setter 的成本就和資料大小綁在一起；比參考只要一步，代價是由你保證「內容變了，參考也要變」。

比「畫面沒動」更麻煩的是它會潛伏。資料已經被改了，只是還沒畫出來，只要有任何別的原因讓 component 重新 render，它就會突然冒出來：

```tsx
<>
  <button
    onClick={() => {
      tasks.push(createTask('二'));
      setTasks(tasks);
    }}
  >
    新增
  </button>
  <button onClick={() => setFilter('done')}>篩選</button>
</>
```

清單原本 1 筆。點「新增」後筆數還是 1，再點和任務清單完全無關的「篩選」，筆數跳成 2。bug 報告會寫成「切換篩選時會多出任務」，而你會往篩選邏輯裡查半天。

`Array.prototype.sort` 是最常見的不小心。它原地排序，回傳的就是原陣列，所以 `setTasks(tasks.sort(compare))` 同樣不會觸發 render，但資料已經被排過了。JavaScript 從 ES2023 起提供回傳新陣列的 `toSorted`，這時候用它就好。

還有一個更隱蔽的代價：舊快照被污染。React 的設計假設舊 render 的值不會再變，第 10 章做歷史回放時會直接依賴這個假設，把每一步的陣列存起來，想看第幾步就拿第幾份。如果中途有人 `task.status = 'done'` 原地改物件，所有持有這個物件的舊陣列都一起變了，歷史也就不存在了。用 `map` 產生新陣列也救不了這種寫法，新陣列的元素和舊陣列的是同一個物件。

正確的 `toggleTask` 複製了「從被改的地方到根」這一路上的每一層：

```ts
export const toggleTask = (tasks: Task[], id: string): Task[] =>
  tasks.map((task) =>
    task.id === id ? { ...task, status: task.status === 'done' ? 'todo' : 'done' } : task,
  );
```

新陣列是新的、被切換的那筆是新的，**其他沒動到的任務仍然是同一個物件**，新舊陣列裡的參考相同。這叫 structural sharing，所以不可變更新不等於每次把整份資料深複製一遍，也不必為此搬出 `structuredClone`。第 14 章的 `React.memo` 就是靠「沒變的東西參考不變」來跳過 render。

陣列常用操作的對照放在這裡，寫 code 時可以直接查：

| 要做的事 | 不要用（改原陣列） | 用這個（回傳新陣列） |
| --- | --- | --- |
| 新增 | `push`、`unshift` | `[...prev, item]`、`[item, ...prev]` |
| 刪除 | `splice`、`pop`、`shift` | `prev.filter((t) => t.id !== id)` |
| 修改某筆 | `prev[i].title = ...` | `prev.map((t) => (t.id === id ? { ...t, title } : t))` |
| 插入到位置 i | `splice(i, 0, item)` | `prev.toSpliced(i, 0, item)` |
| 取代位置 i | `prev[i] = item` | `prev.with(i, item)` |
| 排序 | `sort` | `prev.toSorted(compare)` |
| 反轉 | `reverse` | `prev.toReversed()` |

物件 state 有一點和你從別的框架聽來的不一樣：setter 是**整個取代**，不會幫你合併。`{ title, dueDate }` 這個 state 呼叫 `setDraft({ title: '改標題' })` 後，`dueDate` 就不見了（`dueDate` 是 optional，所以 TypeScript 不會攔）。要保留其他欄位就自己展開：

```tsx
setDraft((prev) => ({ ...prev, title: '改標題' }));
```

state 可能是 `null` 時，展開之前要先處理這個分支。例如「目前正在編輯的任務」型別是 `Task | null`，沒有編輯中的任務時就維持 `null`：

```tsx
const [editing, setEditing] = useState<Task | null>(null);

const handleRename = (title: string): void => {
  setEditing((prev) => (prev === null ? null : { ...prev, title }));
};
```

每個更新都要多這一層判斷，而且 `editing` 還是清單裡那筆任務的副本。下一節之後你會看到更簡單的選擇：只存 `editingId`，要用時再從 `tasks` 查。

展開只複製一層，巢狀物件要逐層複製。下面的 `BoardView` 是為了示範巢狀才這樣設計的檢視設定，`status` 是任務狀態，Task Tracker 實際的篩選只用一個 `TaskFilter` 字串。第一段是第 02 章提過的淺複製陷阱在 state 上的版本：

```ts
interface BoardView {
  filter: { status: TaskStatus; assigneeId: string | null };
  page: number;
}

const view: BoardView = { filter: { status: 'todo', assigneeId: null }, page: 1 };
const copiedView: BoardView = { ...view };
copiedView.filter.status = 'done';
```

`copiedView` 和 `view` 共用同一個 `filter` 物件，所以 `view.filter.status` 也跟著變成 `'done'`，舊資料被改了。逐層複製才不會互相影響，`savedView` 維持 `'todo'`：

```ts
const savedView: BoardView = { filter: { status: 'todo', assigneeId: null }, page: 1 };
const nextView: BoardView = { ...savedView, filter: { ...savedView.filter, status: 'done' } };
```

巢狀超過兩層時，這種寫法會開始難讀。這通常是 state 結構本身有問題的訊號，「哪些東西不該是 state」那一節會回來處理。

## 初始值只用一次，型別要自己說清楚

`useState` 的引數只在 component 第一次 render 時有用，之後每次 render 它都被忽略。這條規則簡單，違反它卻是常見 bug。任務編輯器要編輯某筆任務，於是這樣寫：

```tsx
const TitleEditor = ({ task }: { task: Task }): React.JSX.Element => {
  const [title, setTitle] = useState(task.title);
  return <input aria-label="標題" value={title} onChange={(event) => setTitle(event.target.value)} />;
};
```

一開始顯示第一筆的標題，正常。使用者切到第二筆，parent 傳入新的 `task`，輸入框卻還是第一筆的標題。state 是在初始化時複製了一份 prop，之後兩者就沒有關係了。修法取決於需求：如果這個輸入框根本不需要自己的草稿，不要 state，直接讀 prop；如果需要草稿，但切到另一筆時要重來，正確工具是第 09 章的 `key`。不要用 Effect 去同步 prop 和 state，第 11 章會解釋那條路為什麼更糟。

初始值的運算式在每次 render 都會被求值，只是結果被丟掉而已。如果它很花時間就是白工。假設任務草稿存在 localStorage，一開始要讀回來：

```tsx
const readDraftTasks = (): Task[] => {
  const raw = localStorage.getItem('task-drafts');
  return raw === null ? [] : (JSON.parse(raw) as Task[]);
};

// 第一種：先呼叫 readDraftTasks()，再把結果傳進去
const [tasks, setTasks] = useState<Task[]>(readDraftTasks());
// 第二種：把 readDraftTasks 這個函式本身傳進去
const [tasks, setTasks] = useState<Task[]>(readDraftTasks);
```

第一種每次 render 都同步讀一次 localStorage 再 `JSON.parse`，每按一個鍵都要重來，結果卻用不上。第二種由 React 只在初始化時呼叫，這叫 lazy initializer，render 3 次也只讀 1 次。lazy initializer 和 updater 一樣必須 pure，StrictMode 下會被呼叫 2 次。差別只有一對括號，初始值很便宜時（`''`、`[]`、常數）不需要包函式。上面的 `as Task[]` 是沒有驗證的斷言，第 20 章的 Zod 才是這類外部資料的正解。

這條規則有個副作用：既然 `useState` 和 setter 看到函式都會去呼叫它，想把函式本身存進 state 就要多包一層。`useState<string>(format)` 存到的是 `format()` 的結果，`useState<() => string>(() => format)` 存到的才是函式。這種情況不多見，但錯誤訊息會很困惑人，知道就好。

型別方面，第 04 章的推斷在 `useState('')` 這類初始值上運作得很好，推斷為 `string` 之後，`setDraft(1)` 就會被擋下。有三種初始值要自己給泛型。第一種是 `null`，它沒有足夠資訊，TypeScript 只能依字面推斷：

```tsx
const [selected, setSelected] = useState(null);
// 錯誤：推斷為 null，之後什麼都放不進去
setSelected(task);

const [selectedTask, setSelectedTask] = useState<Task | null>(null);
setSelectedTask(task);
```

第二種是空陣列，理由相同：

```tsx
const [emptyList, setEmptyList] = useState([]);
// 錯誤：推斷為 never[]
setEmptyList([task]);

const [tasks, setTasks] = useState<Task[]>([]);
setTasks([task]);
```

第三種最容易被漏掉，因為它不會報錯：

```tsx
const [looseFilter, setLooseFilter] = useState('all');
setLooseFilter('not-a-filter');

const [filter, setFilter] = useState<TaskFilter>('all');
// 錯誤：不是 union 的成員
setFilter('not-a-filter');
```

`useState('all')` 的型別會放寬成 `string`，和 `let filter = 'all'` 得到 `string` 是同一個理由：這個值之後可能被改成別的字串，TypeScript 不會替你猜只有 `'all'` 合法。於是拼錯的字也能過。第 05 章花力氣建的 union，要在這裡寫出來才有保護力。不給引數的 `useState<string>()` 型別是 `string | undefined`，這個 `undefined` 接下來會在受控 input 那裡製造問題。

## 輸入框的值，誰說了算

寫到這裡，Task Tracker 還差一個輸入框。HTML 的 `<input>` 自己有狀態，它把使用者打的字存在 DOM 節點裡。第 01 章的原生版本要取值，就得回 DOM 去讀。這和我們一路建立的模型衝突：畫面應該是 state 的函式，現在卻有一塊資料活在 DOM 裡，React 不知道它的存在，你也沒辦法從外面把它清空或檢查內容。

**受控 input** 把真相搬回 state。`value` 決定輸入框顯示什麼，`onChange` 回報使用者想改成什麼：

```tsx
const [draft, setDraft] = useState('');
return (
  <input aria-label="新任務" value={draft} onChange={(event) => setDraft(event.target.value)} />
);
```

React 的 `onChange` 對應原生的 `input` 事件，每次輸入都觸發，和原生 `change` 事件（失焦才觸發）不同。使用者按下 `a`，瀏覽器先把 DOM 裡的值改成 `a` 並觸發事件，React 呼叫 `onChange`，`setDraft('a')` 排更新，render 出 `value="a"`，DOM 也是 `a`，兩邊一致。如果 handler 沒有呼叫 setter 呢？事件結束時 React 看到 DOM 的值和 `value` 對不上，會把 DOM 改回去，使用者看到的就是打字沒反應。只有 `value` 沒有 `onChange` 時輸入框動不了，console 還會警告：

```text
You provided a `value` prop to a form field without an `onChange` handler
```

理解這個迴圈之後，有兩件事就不用背了。第一，**setter 不能延後**。如果把 `setDraft` 放進 `setTimeout` 或 `await` 後面，事件結束時 state 還沒變，React 把 DOM 改回舊值，打 `abc` 最後只留下一個字元。第二，`onChange` 裡可以對值加工，但它每個按鍵都會跑。`setDraft(event.target.value.trim())` 打 `修 bug` 會變成 `修bug`，因為空白一打出來就被修掉了，後面的 `bug` 接了上來。所以 Task Tracker 的 `TaskForm` 把使用者打的原文存在 `draft`，要用的時候才算 `draft.trim()`。

這個迴圈帶來的好處，是 state 成為唯一的真相：送出後 `setDraft('')` 就能清空輸入框，按鈕的 `disabled` 可以從 `draft` 算出來，這些都不必碰 DOM。checkbox 的對應屬性是 `checked`，讀值用 `event.target.checked`，其餘都一樣。

`event.target.value` 永遠是字串，`type="number"` 的欄位也一樣。直覺寫法是把 state 存成 number，`onChange` 裡 `setPageSize(Number(event.target.value))`，但 `Number('')` 是 `0`：使用者清空欄位想重打，框裡立刻跳出 0，清都清不掉。比較順手的做法是 state 存字串、用到時才轉成數字。完整的欄位轉型與驗證留給第 17 章。

受控 input 還有一個常見警告。值從 `undefined` 變成字串時，React 會判定它從非受控變成受控：

```text
changing an uncontrolled input to be controlled
```

原因在於 `value={undefined}` 等於沒給 `value`，React 把它當非受控；之後有值了又變成受控，兩種模式誰管 DOM 的答案不同。`useState<string | undefined>()` 接到 `value` 上就會出現。修法是給 `''` 當初始值。`value={null}` 也不行，TypeScript 會擋，繞過去的話 runtime 會警告 `should not be null`。`Task.dueDate` 是 `string | null`，接到輸入框時要寫 `value={task.dueDate ?? ''}`。

欄位多起來時，每按一鍵都 render 整個表單，驗證也要自己寫，這時非受控加 React Hook Form 是另一條路，第 17 章會比較。兩三個欄位的表單，受控就是最簡單的選擇。

## 兩個 component 要同一份資料時，state 放哪裡

到目前為止，state 都放在用它的 component 裡。Task Tracker 現在有一個需求打破了這個做法：`TaskList` 要顯示任務、`TaskForm` 要新增任務，頁面頂端還要一行「已完成 1 / 2」。如果 `tasks` 放在 `TaskList` 裡，`TaskForm` 碰不到；第 07 章講過 props 只能往下流，兄弟 component 之間沒有路。

解法是把 state 移到它們**最近的共同 parent**，再用 props 分下去，這叫 lifting state up：

```text
TasksPage（tasks、filter 在這裡）
├─ TaskForm 收到 onAdd，往上回報事件
├─ TaskFilterBar 收到 filter、onFilterChange
├─ 計數列 收到（算好的）doneCount
└─ TaskList 收到 visibleTasks、onToggle
```

資料往下流，事件往上傳。child 不改資料，它只回報「使用者想新增這個標題」；parent 擁有資料，所以由 parent 決定怎麼處理。`onAdd` 什麼都不回傳，child 要等 parent 下一次 render，才會從 props 看到新資料。在第 21 章把資料交給 server state 之前，`TasksPage` 就是這份資料的擁有者。

往上提有成本，所以不要提過頭。`TaskForm` 的 `draft` 是個好例子：除了 `TaskForm`，沒有人需要知道使用者打字打到哪。如果把 `draft` 也提到 `TasksPage`，每按一個鍵，整頁連同整份清單都要重算（第 09 章會解釋為什麼），而且 `TasksPage` 多了一個與它無關的欄位。判斷方式很簡單：找出所有讀這個 state 的 component，放在它們最近的共同 parent，不要更高。放對位置還有個好處：打字打到一半切換篩選，草稿還在，因為它和篩選住在不同的 component 裡。

往下傳的時候，傳語意不要傳 setter。下面是很多人第一次提升 state 時會寫的 `TaskForm`，`Dispatch<SetStateAction<Task[]>>` 就是 `useState` 回傳的 setter 型別：

```tsx
import type { Dispatch, SetStateAction } from 'react';

interface TaskFormProps {
  tasks: Task[];
  setTasks: Dispatch<SetStateAction<Task[]>>;
}

const TaskFormWithSetter = ({ tasks, setTasks }: TaskFormProps): React.JSX.Element => {
  const handleSubmit = async (): Promise<void> => {
    await saveDraft();
    setTasks([...tasks, createTask('補測試')]);
  };
  return <button onClick={() => void handleSubmit()}>送出</button>;
};
```

它現在能動，壞處要等需求變動才出現。`tasks` 是這個 child 手上的 prop 快照，放在 `await` 後面就是前面那節的 stale closure：等待期間別處新增的任務會被這行蓋掉。業務規則也散掉了：PM 要求「標題重複不能新增」，所有拿到 setter 的 child 都得各補一份判斷，漏一個就是漏洞。將來 `tasks` 改成第 13 章的 reducer，這些 child 也要全部改寫。把 prop 換成 `onAdd: (title: string) => void`，child 只能回報這一件事，規則和更新方式都收在 parent。

後面 `TasksPage` 會寫 `onFilterChange={setFilter}`，看起來也傳了 setter，差別在 child 這一側。`TaskFilterBar` 的 prop 型別宣告的是窄合約 `(filter: TaskFilter) => void`，它只能傳一個合法的篩選值，不知道也不依賴 parent 怎麼實作；`setFilter` 只是剛好符合這個簽章。

如果一路往下要穿過好幾層不需要這份資料的 component，那是 prop drilling，第 13 章的 Context 會處理。

## 哪些東西不該是 state

state 越多，能出錯的組合就越多。設計 state 時要做的主要是刪減，目標是留下最小但足夠的一組。有五個原則，每一個都對應一種會實際出事的情況。

**能算出來的就不要存。** 這條最重要，也最常被違反。假設已完成數存成 state，切換時順手維護它：

```tsx
const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
const [doneCount, setDoneCount] = useState(0);

const handleToggle = (task: Task): void => {
  setTasks((prev) => toggleTask(prev, task.id));
  if (task.status === 'todo') {
    setDoneCount((prev) => prev + 1);
  }
};
```

寫的人只想到「勾選」，沒想到「取消勾選」也走這裡。勾選再取消，清單裡已完成是 0 筆，`doneCount` 卻是 1。隨著新增、刪除、批次操作這些路徑變多，你要在每個地方都記得同步，而沒有任何東西會替你檢查。正確的寫法是一行計算，每次 render 重算：

```tsx
const doneCount = tasks.filter((task) => task.status === 'done').length;
```

擔心效能的話，經驗上幾千筆以內的 `filter` 不太會是瓶頸；真的慢要先量測，再考慮第 14 章的 `useMemo`，而不是存成 state。篩選結果 `visibleTasks`、草稿去空白後的 `title` 都是同一種。

**不要存同一份資料的兩個副本。** 使用者點選一筆任務看明細，直覺是把任務物件存起來：

```tsx
const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
const [selectedTask, setSelectedTask] = useState<Task | null>(null);
```

選取後把那筆切換成 `done`，清單顯示 `done`，明細還是 `todo`。`selectedTask` 是選取當下的副本，`tasks` 之後怎麼更新都和它無關。只存 id，要用的時候查：

```tsx
const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
const [selectedId, setSelectedId] = useState<string | null>(null);
const selectedTask = tasks.find((task) => task.id === selectedId) ?? null;
```

這和資料庫正規化是同一件事：同一個事實只存一處，用 key 參照。類比破在 React 沒有外鍵：任務被刪除後 `selectedId` 就懸空了，沒有東西替你擋，所以上面才要 `?? null`，並且畫面要處理查不到的情況。

**不要讓 state 能表達矛盾。** 送出狀態用兩個 Boolean，四種組合裡有一種沒有意義：

```tsx
const [isSubmitting, setIsSubmitting] = useState(false);
const [hasError, setHasError] = useState(false);
```

上次失敗後重試，只呼叫了 `setIsSubmitting(true)` 沒有清掉 `hasError`，就得到 `true/true`，畫面同時顯示 spinner 和錯誤訊息。第 05 章的 discriminated union 就是為這個準備的，不合法的組合根本寫不出來，錯誤訊息也只在 `error` 分支才存在：

```ts
type SubmitState =
  | { status: 'idle' }
  | { status: 'submitting' }
  | { status: 'error'; message: string };
```

**一定一起變的值放在一起。** 排序欄位和方向分開存時，batching 保證兩個 setter 會一起生效，卻不保證你兩個都有呼叫：

```tsx
const [sortField, setSortField] = useState<'dueDate' | 'createdAt'>('createdAt');
const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

const handleResetSort = (): void => {
  setSortField('createdAt');
};
```

預設是建立時間新到舊。使用者先切成「依期限、舊到新」，再按「恢復預設」，得到的是 `createdAt asc`：按鈕說恢復了，清單卻從最舊的排起。如果這組值還要拿去組 API 查詢，錯誤組合也會一路送到後端。存成一個物件，每次都得給完整的一組，就不會只改一半：

```tsx
interface TaskSort {
  field: 'dueDate' | 'createdAt';
  direction: 'asc' | 'desc';
}

const DEFAULT_SORT: TaskSort = { field: 'createdAt', direction: 'desc' };
const [sort, setSort] = useState<TaskSort>(DEFAULT_SORT);
```

反過來，彼此無關的值不要為了省幾行併成一個大物件，因為 setter 不合併，每次都要展開，還容易漏。

**結構盡量扁平。** 這是前面「為什麼不能直接改物件和陣列」那節巢狀更新問題的根治方式。領域型別 `Task` 用 `assigneeId` 而不是內嵌整個 `User`，是刻意的。假設內嵌了，使用者改名字時要走遍每一筆任務，對符合的逐層複製：

```ts
interface TaskWithAssignee extends Omit<Task, 'assigneeId'> {
  assignee: User | null;
}

const renameInTasks = (prev: TaskWithAssignee[], userId: string, name: string): TaskWithAssignee[] =>
  prev.map((task) =>
    task.assignee?.id === userId ? { ...task, assignee: { ...task.assignee, name } } : task,
  );
```

同一個使用者可能負責幾十筆任務，人員清單如果也有一份，這兩邊還得記得一起改。分開存、用 id 參照，改名字就只碰一層，所有顯示這個名字的地方下次 render 時自己查到新值：

```ts
const renameUser = (prev: User[], userId: string, name: string): User[] =>
  prev.map((user) => (user.id === userId ? { ...user, name } : user));
```

## 把 Task Tracker 組起來

把本章所有決定放回專案。前幾章寫好的部分大多不動：`types.ts` 的 `Task` 和 `TaskStatus`、`taskOps.ts` 的 `addTask`、`toggleTask`、`removeTask`、layout 用的 `TaskBoard` 都原樣沿用。`TaskList` 和 `TaskItem` 也一樣，只是第 07 章接好的 `onToggle` 現在真的有人接了；checkbox 的 `checked` 由 `task.status === 'done'` 算出來，它也是受控的。

新增的東西有四樣。第一樣是型別，`TaskFilter` 是 `TaskStatus` 加上 `'all'`，只屬於 UI，所以不併入領域型別：

```ts
// types.ts
export type TaskFilter = 'all' | TaskStatus;
```

第二樣是 `taskOps.ts` 多了建立新任務的函式：

```ts
// taskOps.ts
export const createTask = (title: string): Task => ({
  id: crypto.randomUUID(),
  title,
  status: 'todo',
  assigneeId: null,
  dueDate: null,
  createdAt: new Date().toISOString(),
});
```

第三樣是 `TaskForm`，它自己擁有 `draft`，往上只回報去空白後的標題。`handleSubmit` 的事件型別是 `React.SubmitEvent`；舊專案常見的 `React.FormEvent` 在 `@types/react` 19.3 已標為 deprecated。`disabled` 是操作提示，`if (title === '') return;` 才是規則本身，兩者都從衍生值 `title` 來：

```tsx
// TaskForm.tsx
import { useState } from 'react';

interface TaskFormProps {
  onAdd: (title: string) => void;
}

export const TaskForm = ({ onAdd }: TaskFormProps): React.JSX.Element => {
  const [draft, setDraft] = useState('');
  const title = draft.trim();

  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (title === '') return;
    onAdd(title);
    setDraft('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        新任務
        <input value={draft} onChange={(event) => setDraft(event.target.value)} />
      </label>
      <button type="submit" disabled={title === ''}>
        新增
      </button>
    </form>
  );
};
```

第四樣是 `TaskFilterBar`，它完全沒有 state，是受控的：目前值從 props 來，變更往上回報。這和受控 input 是同一個模式，只是這次由你寫的 component 擔任 `<input>` 的角色。`aria-pressed` 告訴輔助工具這是切換鈕的目前狀態，第 27 章會講。選項裡刻意沒放 `doing`：`toggleTask` 把 `done` 切成 `todo`，其餘（包含 `doing`）切成 `done`，目前沒有任何操作能讓任務進入 `doing`，放一顆「進行中」只會是永遠選不到東西的按鈕。等能改任務狀態時，在這裡加回一行就好，`TaskFilter` 型別已經備好了。

```tsx
// TaskFilterBar.tsx
import type { TaskFilter } from './types';

const FILTER_OPTIONS: { value: TaskFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'todo', label: '待辦' },
  { value: 'done', label: '已完成' },
];

interface TaskFilterBarProps {
  filter: TaskFilter;
  onFilterChange: (filter: TaskFilter) => void;
}

export const TaskFilterBar = ({ filter, onFilterChange }: TaskFilterBarProps): React.JSX.Element => (
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
```

最後是 `TasksPage`，本章所有判斷都集中在這裡。開場那行提示也回來了，用的是「只存剛才新增了哪一筆」的修法，所以這裡存三個 state：`tasks`、`filter`、`lastAddedTitle`。`visibleTasks` 和 `doneCount` 是算出來的，切換任務時兩者同時正確，不需要任何同步程式碼。你在「待辦」篩選下勾選一筆，它會從清單消失、計數同時加一，而我們沒有為這個情境寫一行程式。計數用 `tasks`、清單用 `visibleTasks`，也不會因為篩選就數錯。批次匯入要等匯入畫面出現才會進專案，但 `handleAdd` 已經用 updater，到時候在迴圈裡呼叫也不會丟資料。

```tsx
// TasksPage.tsx
import { useState } from 'react';
import { TaskBoard } from './TaskBoard';
import { TaskFilterBar } from './TaskFilterBar';
import { TaskForm } from './TaskForm';
import { TaskList } from './TaskList';
import { addTask, createTask, toggleTask } from './taskOps';
import type { Task, TaskFilter } from './types';

const INITIAL_TASKS: Task[] = [
  {
    id: 't1',
    title: '寫 API 規格',
    status: 'done',
    assigneeId: null,
    dueDate: null,
    createdAt: '2026-10-01T09:00:00Z',
  },
  {
    id: 't2',
    title: '接上登入流程',
    status: 'todo',
    assigneeId: null,
    dueDate: null,
    createdAt: '2026-10-02T09:00:00Z',
  },
];

export const TasksPage = (): React.JSX.Element => {
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
  const [filter, setFilter] = useState<TaskFilter>('all');
  const [lastAddedTitle, setLastAddedTitle] = useState<string | null>(null);

  const visibleTasks = filter === 'all' ? tasks : tasks.filter((task) => task.status === filter);
  const doneCount = tasks.filter((task) => task.status === 'done').length;

  const handleAdd = (title: string): void => {
    const task = createTask(title);
    setTasks((prev) => addTask(prev, task));
    setLastAddedTitle(title);
  };

  const handleToggle = (id: string): void => {
    setTasks((prev) => toggleTask(prev, id));
  };

  return (
    <TaskBoard title="任務">
      <TaskForm onAdd={handleAdd} />
      <TaskFilterBar filter={filter} onFilterChange={setFilter} />
      <p>
        已完成 {doneCount} / {tasks.length}
      </p>
      {lastAddedTitle !== null && (
        <p role="status">
          已新增「{lastAddedTitle}」，目前共 {tasks.length} 筆任務
        </p>
      )}
      <TaskList tasks={visibleTasks} onToggle={handleToggle} />
    </TaskBoard>
  );
};
```

注意 `createTask(title)` 放在 updater **外面**。它會產生隨機 id 和當下時間，不是 pure 的，放進 updater 的話 StrictMode 跑兩次會得到不同的 id。任務資料目前寫死在 `INITIAL_TASKS`，第 11 章會從 API 載入。

## 畫面不對時怎麼推理

本章的機制可以濃縮成一張反查表。遇到症狀時，先對到機制，再回對應的小節。

| 症狀 | 多半是 | 修法 |
| --- | --- | --- |
| setter 下一行讀到舊值 | snapshot，這是正常行為 | 先算出 `next` 再用，或改成從 state 衍生 |
| 迴圈連續 set，只有最後一筆 | 每次都用同一份 snapshot 算完整新值 | 改用 updater |
| 等待期間的操作結果被蓋掉 | stale closure 寫回舊 snapshot | 改用 updater |
| timer 裡讀到的永遠是舊值 | stale closure | 判斷語意，要最新值用 ref（第 12 章） |
| 資料改了畫面沒動 | 原地修改，參考沒變 | 回傳新物件或新陣列 |
| 做別的操作時才冒出舊變更 | 同上，搭了別的 render 便車 | 同上 |
| 開發模式下資料重複 | updater 不 pure，被 StrictMode 跑了兩次 | 不動 `prev`，隨機值放到外面 |
| 換了 prop，輸入框內容沒變 | 初始值只用一次 | 直接讀 prop，或用 `key`（第 09 章） |
| 輸入框打不進字 | 有 `value` 沒 `onChange`，或 setter 被延後 | 補 `onChange`，同步呼叫 setter |
| uncontrolled to controlled 警告 | `value` 從 `undefined` 變字串 | 初始值給 `''`，用 `?? ''` |
| 兩個數字對不上 | 衍生值或副本存成了 state | 刪掉那個 state，用算的 |

還有一個錯誤訊息是 `Too many re-renders`，通常來自少寫一層函式：

```tsx
return <button onClick={setFilter('done')}>{filter}</button>;
```

這裡沒有把 setter 交給 `onClick`，而是**在 render 當下呼叫它**：render 呼叫 setter、setter 要求 render，無限循環，React 偵測到後直接丟錯。TypeScript 也會擋住這行，因為 setter 回傳 `void`，不是事件處理器。修法是 `onClick={() => setFilter('done')}`。

## 常見誤解

**「用了 updater，`tasks` 就會是最新的。」** updater 只有 `prev` 這個參數是當下的值，只活在那個函式裡。外面的 `tasks` 還是快照，`setTasks((prev) => ...)` 的下一行讀 `tasks` 還是舊值。要拿下一個值去做別的事，就先算出 `next`。

**「先 `push` 再 `setTasks([...tasks])`，參考變了就沒問題。」** 這樣畫面確實會更新，也因此不容易被發現。問題是舊陣列已經被改了，它是舊 render 的快照，也可能是別的 state 或歷史紀錄持有的同一個物件。把這段放進 updater 裡，StrictMode 下還會重複新增。先複製再改，改的永遠是副本。

**「打字太頻繁，把 `setDraft` 包一層 debounce 就好。」** 這會讓受控 input 打不進字。事件結束時 state 還沒變，React 把 DOM 改回舊值，下一次 debounce 觸發時拿到的也不是完整內容。該延後的是下游的工作，例如拿輸入值去查詢：setter 維持同步，查詢用的值另外延後，這就是第 15 章的 `useDebounce`。

**「`Set` 和 `Map` 是容器，往裡面加東西應該算有更新。」** `selectedIds.add(id)` 之後 `setSelectedIds(selectedIds)` 交回去的是同一個參考，`Object.is` 判定相同，畫面不動，和陣列 `push` 同一個原因，`Date` 的 `setDate` 也一樣。它們沒有展開語法這條順手的路，所以特別容易被漏掉。要產生新的一份：`setSelectedIds((prev) => new Set(prev).add(id))`。

另外幾個常聽到的說法，本章各節已經處理過：「`await` 之後就拿得到新值」錯在變數是 `const` 快照，見「setter 沒有改變數」；「`useState(props.value)` 會隨 prop 更新」錯在初始值只用一次，見「初始值只用一次」；「三個 setter 會 render 三次」錯在 batching，見「呼叫幾次 setter」；「state 放越高越安全」錯在每個讀者之外的 component 都要跟著重算，見「state 放哪裡」。

## 同事會來問你的問題

**「`useState`、`useRef`、`useMemo` 到底怎麼選？」**
問這個值變了之後畫面要不要跟著變。要變，用 `useState`（邏輯複雜時用第 13 章的 `useReducer`），因為更新它會讓 React 排一次 render。不用變但要跨 render 記住，用第 12 章的 `useRef`，它的 `current` 可以改，也不會觸發 render。如果它可以從其他值算出來，就直接算；算起來真的貴才用第 14 章的 `useMemo`，它只是快取，真正的資料仍在算它的來源。一般區域變數活不過單次 render，不能代替其中任何一個。

**「不是說不要傳 setter 給 child 嗎？`TasksPage` 怎麼把 `setFilter` 傳下去了？」**
看 child 宣告的合約。`TaskFilterBar` 只認得 `(filter: TaskFilter) => void`，日後要加 log 或重設頁碼，parent 把 `setFilter` 換成自己的函式就好，child 一行都不用動。要避免的是把 prop 型別寫成 `Dispatch<SetStateAction<Task[]>>`，這會讓 child 能傳任意陣列，甚至 updater，也把 parent 綁死在 `useState` 上。

**「為什麼 React 不讓 `tasks` 永遠是最新的，這樣不是少很多 bug？」**
那樣換來的是另一類 bug。一次 render 的畫面和 handler 是配套的：使用者看到什麼、按下去就處理什麼。如果值會在 handler 執行中途變掉，`setTimeout` 裡的訊息可能指向使用者根本沒送出的內容，同一個函式裡前後兩行讀到的也可能不一致。快照讓這類問題不存在，代價是你要主動處理「我真的要最新值」的少數場景，而這些場景有明確工具：updater 處理寫，ref 處理讀。

**「StrictMode 下 updater 和 component 都跑兩次，production 也這樣嗎？」**
不會。這是開發模式專屬的行為（官方文件），目的是把不 pure 的程式碼逼出原形。如果你的程式會因為跑兩次而壞掉，它在 production 也不是安全的，只是沒那麼容易看到，例如第 30 章的並行 render 就可能重跑或捨棄 render。正確的反應是修成 pure，把 StrictMode 拿掉解決不了問題。第 09 章會再談這個機制。

**「表單有十幾個欄位，要寫十幾個 `useState` 嗎？」**
這些欄位通常會一起被送出、一起被重設，可以合併成一個物件，先 `const { value } = event.target;`，再 `setForm((prev) => ({ ...prev, title: value }))` 更新。直接在 updater 裡讀 `event.target` 只有在 updater 於同一個事件內執行時才拿得到打的字，先讀出來就不必想這件事。但欄位到這個規模，通常還需要驗證、錯誤訊息、dirty 狀態，自己維護不划算，第 17 章的 React Hook Form 就是為此而生。兩三個欄位用 `useState` 就夠了。

## 本章小結

每次 render 都是一次函式呼叫，有自己專屬的 `const` 快照，所以 setter 的下一行和 `await` 之後讀到的都是舊值；要從前一個值算下一個值，就交給 updater。React 用 `Object.is` 比參考來判斷 state 有沒有變，這是不可變更新的根本理由。state 放在所有讀者最近的共同 parent，只存最小必要的資料，input 的值也交給它管。Task Tracker 現在能新增、切換、篩選，但我們一直把「React 重新 render」當成黑盒子：它重新呼叫了哪些 component？怎麼知道該改哪個 DOM 節點？state 又是怎麼認出自己屬於哪個實例的？第 09 章打開這個黑盒子。

## 連結

- [[react-07-props]] — 上一章：props、單向資料流與 layout component
- [[react-09-rendering]] — 下一章：render、commit、reconciliation 與 `key`
- [[react-02-javascript-for-react]] — 值與參考、closure、不可變更新
- [[react-05-typescript-modeling]] — 用 discriminated union 排除矛盾狀態
- [[react-10-tic-tac-toe]] — 不可變更新帶來的歷史回放
- [[react-11-effects]] — 為什麼不該用 Effect 同步 state、`useEffectEvent`
- [[react-12-refs]] — 跨 render 記住但不觸發 render 的值
- [[react-13-reducer-and-context]] — 更新邏輯變複雜、state 要穿透很多層時
- [[react-14-memoization]] — 參考相等與 render 成本的取捨
- [[react-15-custom-hooks]] — `useDebounce`：把下游的工作延後，而不是 setter
- [[react-17-forms]] — 受控與非受控的完整比較、React Hook Form
- [[react-23-client-state]] — state 該放哪裡的完整決策樹
- [[javascript-typescript-react-foundations]] — 基礎知識的綜合整理
