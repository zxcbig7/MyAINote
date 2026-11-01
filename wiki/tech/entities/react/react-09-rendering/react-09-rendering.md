---
type: concept
domain: tech
tags: [react, rendering, reconciliation, virtual-dom, key, strict-mode, purity, typescript]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/DOM 節點觀念.md
  - raw/Web Framework/React/react-hooks-gotchas/react-hooks-gotchas.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 09 章：Rendering — React 怎麼決定要更新什麼

## 按下排序，草稿跑到別筆任務上

上一章的 Task Tracker 能新增、切換、篩選。這週多了兩個需求：任務標題要能行內編輯，清單要能依到期日排序。`TaskItem` 因此多了自己的 state：`isEditing` 和草稿 `draft`。同事在同一個 PR 裡改了 `TaskList` 的 `map`：

```tsx
{visibleTasks.map((task, index) => (
  <TaskItem key={index} task={task} onToggle={onToggle} onRename={onRename} />
))}
```

PR 描述寫「index 一定唯一，也不會有 key 警告」。點起來一切正常，review 也過了。

清單有三筆：「寫 API 規格」（11/20 到期）、「接上登入流程」（11/10 到期）、「補測試」（沒有到期日）。你按第一筆的「編輯」，把標題改成「寫 API 規格 v2」，還沒儲存，想先看看到期順序，於是按下「依到期日排序」。「接上登入流程」排到了最上面，但輸入框留在第一列，裡面還是「寫 API 規格 v2」。你按下「儲存」：

```text
排序前                    排序後按下儲存
[寫 API 規格 v2] 儲存     寫 API 規格 v2    這一列原本是「接上登入流程」
接上登入流程              寫 API 規格
補測試                    補測試
```

被改名的是「接上登入流程」，「寫 API 規格」原封不動。沒有錯誤，沒有警告，資料就這樣錯了。等第 20 章接上 API，這會是一個帶著錯誤 id 的 `PATCH`。

`draft` 和 `task` 都寫在同一個 `TaskItem` 裡，看起來應該綁在一起，React 憑什麼把這筆的草稿配上那筆的資料？要回答這個問題，得先打開上一章一直當黑盒子的那句話：「React 重新 render」。這一章回答的是：state 改變之後，React 呼叫了誰、改了哪些 DOM、又靠什麼判斷哪份 state 屬於誰。

## 從 setter 到畫面改變，中間有三步

上一章說 setter 會「排一次 render」，容易讓人以為 render 就是更新畫面。這兩件事其實分開，中間隔著 React 的比對，React 的文件把整個過程拆成三步，再加上瀏覽器自己的一步：

```text
Trigger  有事情要求更新：初次掛載，或某個 component 的 state 改了
   |
Render   React 呼叫 component 函式，拿到新的畫面描述，和上一次比對，算出差異
   |
Commit   React 把算好的差異套用到 DOM
   |
Paint    瀏覽器把更新後的 DOM 畫到螢幕上（第 01 章的 layout 與 paint）
```

Trigger 只有兩種來源。第一種是初次 render，也就是 `main.tsx` 裡的 `createRoot(...).render(<App />)`。第二種是 state 更新，自己的或祖先的都算（第 13 章的 Context 會再多一條路）。同一個事件裡呼叫好幾個 setter 只會排一次 render，這是第 08 章的 batching。

在 React 的術語裡，render 指的就是**呼叫你的函式**。這一步只做計算，DOM 一個字都還沒動。用這個小 component 看三步各做了什麼：

```tsx
const TaskProgress = (): React.JSX.Element => {
  const [doneCount, setDoneCount] = useState(1);
  return (
    <section>
      <h2>本週進度</h2>
      <p>已完成 {doneCount} 筆</p>
      <input aria-label="備註" />
      <button onClick={() => setDoneCount(doneCount + 1)}>完成一筆</button>
    </section>
  );
};
```

在備註欄打「等設計稿」，再按「完成一筆」。`setDoneCount(2)` 是 trigger。React 重新呼叫 `TaskProgress` 是 render，整個函式從頭跑一遍，回傳一份新的描述，裡面包含 `<h2>`、`<input>`、`<button>`，一個都沒少。Commit 時，React 只把 `<p>` 裡的文字節點從 `1` 改成 `2`。`<input>` 還是原來那個 DOM 節點，你打的「等設計稿」還在，雖然這個 input 沒有綁任何 state。

假如 React 每次都重建整棵 DOM，備註的文字和游標位置都會消失，手動重組 `innerHTML` 時就是這個結果。所以「重新 render」和「重建畫面」是兩回事。如果 render 的結果和上次完全相同，React 就不會碰 DOM。

## Virtual DOM 就是你回傳的那堆物件

那 React 怎麼知道差異在哪？第 06 章說過 JSX 會編譯成函式呼叫，那個呼叫的回傳值就是答案：

```tsx
const title = '任務';
const element = (
  <div className="card">
    <h1>{title}</h1>
  </div>
);
```

把 `element` 簡化後大概長這樣：

```text
{
  type: 'div',
  props: {
    className: 'card',
    children: { type: 'h1', props: { children: '任務' } },
  },
}
```

這是一個普通的 JavaScript 物件，React 叫它 element。一次 render 產生的整棵 element 樹，就是大家口中的 Virtual DOM。`type` 是 DOM 標籤時存字串；是 component 時存函式本身，`<TaskRow title="補測試" />` 的 `type` 就是 `TaskRow` 這個函式。注意這時 `TaskRow` 還沒被呼叫。寫 JSX 只是填一張單子，什麼時候照單子呼叫、要不要呼叫，由 React 決定。這個區別在後面解釋 `children` 時會派上用場。

有了前後兩棵樹，React 就能一層層比對，這個過程叫 reconciliation。回到上面的例子，把 `title` 從「任務」改成「本週任務」：根節點兩邊都是 `div`，`className` 相同，不動；子節點兩邊都是 `h1`，不動；文字不同，記下一筆「改這個文字節點」。比對在 render 階段就算好了，但 React 這時還不會動手，要等到 commit 才一次套用。

後端讀者可以拿 EF Core 的 change tracking 來理解。你改了 entity 的一個屬性，呼叫 `SaveChanges` 時 EF Core 比對快照和目前的值，只產生那個欄位的 `UPDATE`，不會把整列重寫。React 的 commit 也只送出差異。這個類比有兩個地方不適用。第一，你不是在原物件上改值，每次 render 都產生一整棵新的樹。第二，也是本章的重點：EF Core 靠主鍵認出「這是同一筆資料」，而 React 預設沒有主鍵，它只能靠**位置**來認。後面的 `key` 就是在補這個缺口。

常有人說 Virtual DOM 比直接操作 DOM 快。這句話要看和什麼比。如果你清楚知道只有一個文字節點要改，`node.textContent = '2'` 一定比「重新計算一整棵樹、比對、再改同一個節點」快，因為後者多做了前面所有的工作。Virtual DOM 省掉的是你的工作：第 01 章要為每一種狀態轉換手寫 DOM 操作，現在你只需描述任何時刻的畫面長什麼樣（第 00 章的 `v = fn(s)`），轉換交給 React 算。它用一些執行成本換來可維護性，同時保證 DOM 的改動量接近必要的最小值，多數應用的效能因此夠用。

## 一次 state 更新會呼叫哪些 component

比對之前要先有新的樹，所以 React 需要重新呼叫 component。問題是呼叫哪些。看這一頁：

```tsx
const PageHeader = (): React.JSX.Element => {
  console.log('render PageHeader');
  return <h1>任務</h1>;
};

const DraftInput = (): React.JSX.Element => {
  const [draft, setDraft] = useState('');
  console.log('render DraftInput');
  return <input aria-label="新任務" value={draft} onChange={(event) => setDraft(event.target.value)} />;
};

const TaskRow = ({ title }: { title: string }): React.JSX.Element => {
  console.log('render TaskRow', title);
  return <li>{title}</li>;
};

const CascadePage = (): React.JSX.Element => {
  const [notice, setNotice] = useState('');
  console.log('render CascadePage');
  return (
    <>
      <PageHeader />
      <DraftInput />
      <button onClick={() => setNotice('已同步')}>同步</button>
      <p>{notice}</p>
      <ul>
        <TaskRow title="寫 API 規格" />
        <TaskRow title="補測試" />
      </ul>
    </>
  );
};
```

按下「同步」，`CascadePage` 的 state 變了，console 印出（如果你的專案開著 StrictMode，每行會出現兩次，原因本章後面會講）：

```text
render CascadePage
render PageHeader
render DraftInput
render TaskRow 寫 API 規格
render TaskRow 補測試
```

`PageHeader` 沒有任何 props，`TaskRow` 的 `title` 是寫死的字串，它們還是全部被呼叫了。規則是：**state 改變的那個 component，以及它底下所有的子孫，預設都會 render，和 props 有沒有變無關。** 在輸入框打一個字時，`DraftInput` 的 state 變了，console 只有一行 `render DraftInput`。更新只往下傳，不往上也不往旁邊，`CascadePage` 和兩個 `TaskRow` 都沒有動。上一章說不要把 `draft` 提到 `TasksPage`，理由就在這裡：提上去之後，每打一個字，整頁都要跟著重算。

為什麼 React 不聰明一點，只呼叫 props 變了的 child？因為它無法確定 props 沒變就代表結果沒變。Component 可能讀了 Context，也可能（雖然不該）讀了外部變數。寧可多算一次、比對後發現沒差異，也不要漏算造成畫面過期。這個取捨通常划算，因為前一節說過，多算不等於多改 DOM。上面那次「同步」，五個函式都跑了，DOM 只動了 `<p>`。

底下這些 component 的順序是由上而下印出來的，但不要讓程式依賴它。官方文件明確要求 component 不要假設彼此的 render 順序。

### `children` 為什麼有時候逃得掉

上面的規則有一個容易被誤解的例外。第 07 章的 layout component 用 `children` 接內容，假設看板自己有一個「緊湊模式」的 state：

```tsx
interface BoardProps {
  title: string;
  children: ReactNode;
}

const CompactBoard = ({ title, children }: BoardProps): React.JSX.Element => {
  const [isCompact, setIsCompact] = useState(false);
  console.log('render CompactBoard');
  return (
    <section className={isCompact ? 'compact' : undefined}>
      <button onClick={() => setIsCompact(!isCompact)}>{title}</button>
      {children}
    </section>
  );
};

const BoardPage = (): React.JSX.Element => {
  console.log('render BoardPage');
  return (
    <CompactBoard title="任務">
      <TaskRow title="寫 API 規格" />
    </CompactBoard>
  );
};
```

按下看板標題，console 只有 `render CompactBoard`，`TaskRow` 沒有被呼叫。回想剛才那張單子：`<TaskRow />` 這個 element 是 `BoardPage` render 時填好的，`BoardPage` 這次沒有 render，所以 `CompactBoard` 拿到的 `children` 還是同一個物件。React 看到這個位置的 element 和上次是同一個參考，就知道底下不需要重算。

所以「子孫都會 render」更精確的說法是：這次 render 新產生的 element 才會被處理。這也提供了一個不用任何 memo 的優化手法：把會頻繁變動的 state 放進 layout component，把昂貴的內容從外面用 `children` 傳進去。

### `React.memo` 先知道它存在就好

如果確定某個 component 又貴又常被連帶呼叫，可以用 `react` 匯出的 `memo` 明確選擇退出預設行為：

```tsx
const MemoRow = memo(TaskRow);
```

`memo` 會逐一用 `Object.is` 比對 props，全部相同就跳過這次 render。上面的 `title` 是字串，比對成立。但只要 parent 在 JSX 裡寫 `onOpen={() => setNotice('開啟')}`，每次 render 都是新函式，`memo` 就白包了，child 照樣 render。什麼時候值得加、要搭配什麼，是第 14 章的主題，量測方法在第 28 章。

## React 自己決定呼叫時機，所以 component 必須是 pure

既然 React 可以多呼叫、跳過呼叫，你的函式就不能對呼叫次數有任何意見。這個要求有個名字叫 pure，它有兩個條件：相同的輸入（props、state、Context）得到相同的輸出；執行時不改動呼叫之前就存在的東西。

後端讀者可以把 render 想成 HTTP 的 GET：它是安全的，client、proxy 重試幾次都不該改變資料，所以你不會在 GET handler 裡寫 `counter++`。這個類比破在 GET 可以每次讀到資料庫的最新狀態，render 卻只該依賴傳進來的輸入，第 08 章的快照正是為此而存在。

不 pure 的程式通常看起來沒什麼問題。例如想幫清單加上列編號：

```tsx
let rowNumber = 0;

const NumberedRow = ({ title }: { title: string }): React.JSX.Element => {
  rowNumber += 1;
  return (
    <li>
      {rowNumber}. {title}
    </li>
  );
};
```

沒有 StrictMode 時，第一次畫面是 `1. 寫 API 規格`、`2. 補測試`，完全正確。任何一次父層更新之後變成 `3. 寫 API 規格`、`4. 補測試`，編號繼續累加。壞在 `rowNumber` 活得比 render 久，而每次呼叫都改動它，輸出因此取決於「被呼叫過幾次」，這正是 React 不保證的東西。正解是讓編號變成輸入：`tasks.map((task, index) => <NumberedRow key={task.id} number={index + 1} title={task.title} />)`。

第二個例子更常見，因為它不像在改東西。`Array.prototype.sort` 會就地修改陣列，而不是回傳新的。`compareByDueDate` 是比較兩筆任務到期日的函式，本章最後會寫出來：

```tsx
interface SortableListProps {
  tasks: Task[];
  isSortedByDueDate: boolean;
}

const SortableList = ({ tasks, isSortedByDueDate }: SortableListProps): React.JSX.Element => {
  const ordered = isSortedByDueDate ? tasks.sort(compareByDueDate) : tasks;
  return (
    <ul>
      {ordered.map((task) => (
        <li key={task.id}>{task.title}</li>
      ))}
    </ul>
  );
};
```

打開排序時看起來完全正確。關掉排序，清單卻回不去原本的順序，因為 `tasks` 這個陣列本身，也就是 parent 的 state，已經被永久改掉了。這段程式沒有呼叫任何 setter，卻在 render 裡改了 state，第 08 章講的「不可變」在這裡同樣適用。修法是用回傳新陣列的 `toSorted`。型別也幫得上忙：把 prop 宣告成 `tasks: readonly Task[]`，`tasks.sort` 就會變成編譯錯誤，`toSorted` 則不受影響。

要注意 pure 只限制「呼叫之前就存在的東西」。在 render 裡建立一個新陣列再 `push` 進去完全沒問題，這叫 local mutation，外面看不到。反過來，什麼都沒改也可能不 pure：在 render 裡讀 `new Date()` 或 `Math.random()` 也違反第一個條件，相同輸入會得到不同輸出，所以「是否逾期」要用的目前時間，最好從外面傳進來。

那真正要產生副作用的程式放哪裡？優先放 event handler，它們不在 render 期間執行，不需要 pure。沒有對應事件的（例如和外部系統同步）才考慮第 11 章的 Effect。

React 這麼堅持，是因為它要靠這個保證做事：pure 的 component 才能在輸入沒變時安全跳過（第 14 章的 `memo`），才能在 render 到一半時被打斷重來（第 30 章的 transition），才能在伺服器上執行（第 31 章）。如果你用 ESLint，`eslint-plugin-react-hooks` 7 的 recommended 設定裡有 `purity`、`immutability` 這類規則，針對的就是這類問題（第 43 章會細談 lint 設定）。

## StrictMode 為什麼要把你的函式跑兩次

上面的編號 bug 要等父層更新才現形，只點一次、看一眼的手動測試抓不到。StrictMode 就是為了提早抓到它而存在。Vite 模板的 `main.tsx` 預設把整個 App 包在裡面：

```tsx
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

開發模式下，它會把**應該是 pure 的函式**多呼叫一次。理由很直接：pure 函式呼叫兩次和一次沒有差別，如果有差別，你的程式就有 bug。同樣的 `NumberedRow` 放進 StrictMode，第一個畫面就是 `2. 寫 API 規格`、`4. 補測試`，不用等任何更新。

| 函式 | StrictMode 下的呼叫 |
| --- | --- |
| component 函式本體 | 每次 render 2 次 |
| `useState` 的 initializer、`useMemo` 的 factory | 2 次 |
| setter 的 updater、`useReducer` 的 reducer | 2 次 |
| event handler | 1 次（本來就不需要 pure） |
| Effect | mount 時依序 setup、cleanup、setup |
| ref callback | mount 時依序 setup、cleanup、setup |

這些檢查只在開發模式執行，production build 完全沒有這個行為，所以不用擔心效能。如果你裝了 React DevTools，第二次 render 裡的 `console.log` 會顯示成淡色，看到兩行 log 時可以這樣分辨。

Effect 和 ref callback 那兩列檢查的不是 pure，而是 cleanup 有沒有寫對：component 應該能承受「掛上、拆掉、再掛上」，第 11、12 章會各自細談。這裡先處理你最可能碰到的症狀：開發時 API 被打了兩次、OAuth 流程走了兩次。常見的反應是加一個 ref 當門閂（`fetchTasks` 是第 03 章寫的載入函式，`useRef` 和 `useEffect` 第 11、12 章才正式介紹，這裡看懂意圖就好）：

```tsx
const called = useRef(false);

useEffect(() => {
  if (called.current) return;
  called.current = true;
  fetchTasks();
}, []);
```

StrictMode 下這確實只會呼叫一次，因為模擬的重新掛載會保留 ref。但 component 真的被拆掉再掛回來時（切走再切回來），ref 是新的，`fetchTasks` 還是會再跑一次。所以門閂只遮住了開發模式的症狀，沒有解決「重複請求要安全」這件事，寫入型 API 的冪等設計依然要做。正確的做法是第 11 章的 cleanup 與第 21 章的 server state 工具。

StrictMode 也不是萬能。上一節的 `tasks.sort` 排序兩次和一次結果一樣，所以它抓不到，只有切回原順序才現形。它能抓的是「多跑一次結果就不同」的那一類。把 StrictMode 拿掉，則只是讓 bug 不再被提早發現，bug 本身還在。

## state 住在樹的位置上

現在可以回答第 08 章留下的問題：state 怎麼認出自己屬於哪個實例？看一段任務詳情的編輯器，它就是第 08 章那個「換了 prop，輸入框內容沒變」的 bug：

```tsx
const TaskEditor = ({ task }: { task: Task }): React.JSX.Element => {
  const [draft, setDraft] = useState(task.title);
  return <input aria-label="標題" value={draft} onChange={(event) => setDraft(event.target.value)} />;
};

// parent 裡
<TaskEditor task={selected} />
```

`selected` 是目前選中的任務。從第一筆切到第二筆，輸入框還是「寫 API 規格」。`task` 明明變了，`useState` 卻沒有重新初始化。原因是 state 既不存在你的函式裡（函式每次跑完就結束了），也不存在 element 裡（element 每次都是新的）。React 內部維護著一棵樹，state 掛在這棵樹的節點上。每次 render 之後，React 按位置走訪新的 element，問一個問題：這個位置上的東西，和上次是同一個嗎？

| 這個位置，新舊比較 | React 的動作 | state |
| --- | --- | --- |
| 相同 `type`、相同 `key` | 保留實例，只更新 props | 留著 |
| `type` 或 `key` 不同 | 拆掉舊的，建立新的 | 整棵子樹清空 |
| 這個位置沒有東西了 | 拆掉 | 整棵子樹清空 |

`TaskEditor` 的位置和 `type` 都沒變，對 React 來說它就是同一個實例拿到新 props，`useState` 交出既有的值，初始值當然不會再看一眼。React 判斷時只看這張表，不看你的意圖，也不看 prop 裡的 id。以下四個例子都是這張表的直接結果。

**三元運算式的兩邊，可能是同一個實例。** `{isCompact ? <DraftInput /> : <DraftInput />}` 讀起來像兩個 component，切換時草稿卻留著，因為同一個位置上 `type` 都是 `DraftInput`。

**提早 return 會讓位置移動。** 同樣是多顯示一行提示，這兩種寫法結果不同：

```tsx
// 草稿留著
<div>
  <button onClick={() => setShowHint(!showHint)}>切換</button>
  {showHint && <p>提示</p>}
  <DraftInput />
</div>
```

```tsx
// 草稿消失
if (showHint) {
  return (
    <div>
      <button onClick={() => setShowHint(false)}>切換</button>
      <p>提示</p>
      <DraftInput />
    </div>
  );
}
return (
  <div>
    <button onClick={() => setShowHint(true)}>切換</button>
    <DraftInput />
  </div>
);
```

第一種寫法裡，`showHint` 是 `false` 時那個 `false` 會佔住第二個位置，`DraftInput` 永遠在第三個。第二種寫法裡，`DraftInput` 原本在第二個位置，打開提示後第二個位置變成 `<p>`，`type` 不同，舊的拆掉，第三個位置建立一個全新的 `DraftInput`。使用者看到的是：打開一行提示，剛打的字沒了。

**外層換標籤，裡面全部重來。** `isCompact` 切換時外層從 `<div>` 變成 `<section>`，就算裡面的 `<DraftInput />` 一模一樣，它也會被清空，因為拆掉是連整棵子樹一起拆的。兩個 function body 完全相同的 component 也一樣算不同 `type`，React 比的是函式的參考，不看內容。

**不要在 component 裡定義 component。** 這是最難查的一個，因為程式看起來只是整理得比較乾淨：

```tsx
const TaskSearch = (): React.JSX.Element => {
  const [keyword, setKeyword] = useState('');

  const SearchBox = (): React.JSX.Element => (
    <input aria-label="搜尋" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
  );

  return <SearchBox />;
};
```

症狀是每打一個字輸入框就失去焦點。依序打 `abc`，輸入框只有 `a`，後面兩個鍵按到不知道哪裡去了。推理一遍：打 `a` 觸發 `setKeyword`，`TaskSearch` 重新呼叫，這次呼叫建立了一個**新的** `SearchBox` 函式。React 比對這個位置，新舊 `type` 是兩個不同的函式，於是拆掉舊的，連同它的 `<input>` DOM 節點一起丟棄，再建立新的。`keyword` 住在外面的 `TaskSearch`，所以 `a` 留著，但焦點跟著舊節點消失了。修法是把 `SearchBox` 搬到檔案頂層，用 props 傳 `keyword` 和 `onChange`。`eslint-plugin-react-hooks` 7 的 `static-components` 規則就是針對這種寫法。

## key 是你告訴 React「這是誰」的方式

位置規則對固定結構的 UI 很好用，遇到列表就力不從心了。清單重排時，React 只看位置的話，分不出「這幾筆換了順序」和「每筆的內容都改了」。`key` 是你給的識別：同一層的兄弟裡，React 改用 key 而不是順序來配對新舊節點。這就是前面 EF Core 類比裡缺的那個主鍵。

現在可以逐步解開開場的 bug。排序前後，`key={index}` 的配對是這樣：

```text
key={index}
排序前                               排序後
key 0  task=寫 API 規格  draft=...v2  key 0  task=接上登入流程  draft=...v2
key 1  task=接上登入流程              key 1  task=寫 API 規格
key 2  task=補測試                    key 2  task=補測試
```

新的清單裡還是有 `key 0`，`type` 也還是 `TaskItem`，查前面的表：保留實例，只更新 props。所以 `draft` 和 `isEditing` 留在第一列，`task` 卻換成了另一筆。你按「儲存」時執行的是這次 render 建立的 `handleSave`，它的 closure 抓到的 `task.id` 是 `t2`，於是 `onRename('t2', '寫 API 規格 v2')`。React 完全照規則做事，規則的輸入錯了：你告訴它「第 0 列就是同一個東西」。

換成 `key={task.id}`：

```text
key={task.id}
排序前                                排序後
key t1  task=寫 API 規格  draft=...v2  key t2  task=接上登入流程
key t2  task=接上登入流程              key t1  task=寫 API 規格  draft=...v2
key t3  task=補測試                    key t3  task=補測試
```

`t1` 還在，只是換了位置，所以 React 保留那個實例，連同 `draft` 一起移到第二列，對應的 `<li>` 也是把原本的 DOM 節點搬過去，不會重建。草稿跟著任務走，儲存也改對了人。

### index 當 key 為什麼常常沒事

這個 bug 能通過 review，是因為多數情況下真的看不出問題。如果每一列都沒有自己的 state，顯示內容全部來自 props，用 index 當 key 重排後畫面完全正確：React 保留第 0 列的節點，把文字從「寫 API 規格」改成「接上登入流程」，只是做了比必要更多的 DOM 更新。React 也不會警告，因為 index 確實是唯一的。

症狀只在列上有「不從 props 來的東西」時才出現：`useState`、沒綁 state 的 input、焦點、捲動位置。而且不只排序會觸發。刪掉第一筆時也一樣，原本 `key 1` 的任務變成 `key 0`，繼承了被刪那筆的草稿，這時按儲存，標題就寫到了下一筆身上。任何讓項目相對位置改變的操作都算，包括插入到最前面和拖曳。

所以 index 只在這些條件同時成立時才安全：列表不會重排、不會在中間插入或刪除，列上也沒有本地 state。今天成立不代表下個月還成立，開場的 `TaskItem` 就是後來才加上 state。有資料庫 id 就用 id，這是最省事的判斷。

完全不寫 key 的話，React 會印出 `Each child in a list should have a unique "key" prop` 的警告，然後退回用 index，行為和開場一樣。寫 `key={index}` 只是把警告關掉，問題還在。

### 亂數 key 比 index 更糟

有人為了消除警告，或是資料沒有 id，會這樣寫：

```tsx
{visibleTasks.map((task) => (
  <TaskItem key={crypto.randomUUID()} task={task} onToggle={onToggle} onRename={onRename} />
))}
```

每次 render 都產生新 key，查表得到「`key` 不同，拆掉重建」。結果是 parent 任何一次更新，所有列都被拆掉重建：正在編輯的列直接退出編輯模式，草稿消失，DOM 全部重做。資料沒有 id 時，應該在**建立資料的時候**產生，就像 `createTask` 那樣，存進資料裡一起走，不要在 render 時才算。

另外兩個細節。key 只需要在同一層兄弟之間唯一，兩個不同的 `<ul>` 可以各有一個 `t1`；同一層重複則會得到 `Encountered two children with the same key` 警告。key 也不會傳給 component，`props.key` 讀到的是 `undefined`，需要 id 就另外傳一個 prop，如 `<TaskItem key={task.id} task={task} />`。

### 換 key 可以重置 state

理解了 key 代表身份，第 08 章的 `TaskEditor` 就有解了。「切到另一筆任務」在語意上就是另一個編輯器，把這件事告訴 React：

```tsx
<TaskEditor key={selected.id} task={selected} />
```

`selected.id` 一變，表上的結果是拆掉重建，`useState(task.title)` 重新初始化，輸入框顯示新任務的標題。這裡完全不需要 Effect，也沒有列表。第 11 章會解釋為什麼用 Effect 同步這類 state 是更糟的做法。

這個工具有代價：整棵子樹的 state 都會清空、DOM 重建、焦點消失，第 11 章的 Effect 也會全部重跑。所以它適合「這真的是另一個東西」的情境，例如切換任務、切換使用者。如果只想重置其中一個欄位，直接在事件處理裡呼叫 setter 比較合適。

## 把 Task Tracker 修好

現在把這些判斷落到專案上。資料操作先多三個函式，`renameTask` 延續第 02 章的不可變寫法；排序用 `toSorted`，因為它要在 render 中呼叫，不能動到傳入的陣列，參數宣告成 `readonly` 讓編譯器幫忙看著：

```ts
// taskOps.ts，新增
export const renameTask = (tasks: Task[], id: string, title: string): Task[] =>
  tasks.map((task) => (task.id === id ? { ...task, title } : task));

export const compareByDueDate = (a: Task, b: Task): number => {
  if (a.dueDate === b.dueDate) return 0;
  if (a.dueDate === null) return 1;
  if (b.dueDate === null) return -1;
  return a.dueDate < b.dueDate ? -1 : 1;
};

export const sortByDueDate = (tasks: readonly Task[]): Task[] => tasks.toSorted(compareByDueDate);
```

`TaskItem` 的 `isEditing` 和 `draft` 只有它自己需要，依第 08 章的原則留在這一層。有個細節：`draft` 在按下「編輯」時才從 `task.title` 複製，不放在 `useState` 的初始值裡。因為有了穩定的 key，這個實例會活很久，改名之後 `task.title` 變了，初始值早就過期，再次編輯時會看到舊標題。`TaskList` 則把 key 改回 `task.id`：

```tsx
// TaskList.tsx
import { useState } from 'react';
import type { Task } from './types';

interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export const TaskItem = ({ task, onToggle, onRename }: TaskItemProps): React.JSX.Element => {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState('');

  const handleStartEdit = (): void => {
    setDraft(task.title);
    setIsEditing(true);
  };

  const handleSave = (): void => {
    const title = draft.trim();
    if (title !== '') onRename(task.id, title);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <li>
        <input aria-label="任務標題" value={draft} onChange={(event) => setDraft(event.target.value)} />
        <button type="button" onClick={handleSave}>
          儲存
        </button>
      </li>
    );
  }

  return (
    <li>
      <label>
        <input
          type="checkbox"
          checked={task.status === 'done'}
          onChange={() => onToggle(task.id)}
        />
        {task.title}
      </label>
      <button type="button" onClick={handleStartEdit}>
        編輯
      </button>
    </li>
  );
};

interface TaskListProps {
  tasks: Task[];
  onToggle: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export const TaskList = ({ tasks, onToggle, onRename }: TaskListProps): React.JSX.Element => (
  <ul>
    {tasks.map((task) => (
      <TaskItem key={task.id} task={task} onToggle={onToggle} onRename={onRename} />
    ))}
  </ul>
);
```

`TasksPage` 只多一個 Boolean state。排序後的清單是衍生值，依第 08 章的原則不存 state，每次 render 算一次就好，放在 render 裡也合乎 pure，因為 `sortByDueDate` 不動輸入。`INITIAL_TASKS` 同時補上第三筆任務和開場用到的到期日：

```tsx
// TasksPage.tsx，改動的部分
const [isSortedByDueDate, setIsSortedByDueDate] = useState(false);

const filteredTasks = filter === 'all' ? tasks : tasks.filter((task) => task.status === filter);
const visibleTasks = isSortedByDueDate ? sortByDueDate(filteredTasks) : filteredTasks;

const handleRename = (id: string, title: string): void => {
  setTasks((prev) => renameTask(prev, id, title));
};
```

重跑開場的步驟：草稿跟著「寫 API 規格」移到第二列，儲存後改的是對的那一筆。

還有一個刻意留下的行為。編輯「接上登入流程」到一半時切到「已完成」篩選，這一列不在清單裡了，查表：這個位置沒有東西，拆掉。切回「全部」，它回來了，但草稿已經消失。如果篩選切換後這一列還在（例如切到「待辦」），草稿就會留著。要不要保留，是產品決定，技術上有三條路：把各列的草稿提到 `TasksPage` 用任務 id 存起來（列被拆掉也不影響，最常用）；不拆掉，用 CSS 隱藏（清單大時會拖慢）；存到 `localStorage`，連重新整理都不會丟。第 30 章的 `<Activity>` 也是這個方向。Task Tracker 目前選擇接受：行內編輯的草稿短命，不值得多一份 state。

## 畫面不對時怎麼推理

看到 render 相關的症狀時，先把它放進三步裡，問「是函式被呼叫的問題、state 歸屬的問題，還是 DOM 沒被更新的問題」，再對照這張表：

| 症狀 | 多半是 | 怎麼確認 |
| --- | --- | --- |
| 草稿、勾選跑到別列 | 用 index 當 key，或 key 不穩定 | 看 `map` 裡的 key |
| 換了 prop，本地 state 沒變 | 同位置同 `type`，實例被保留 | 要重置就加 `key`，或不要存 state |
| 打開提示、切版面後 state 消失 | 位置移動或外層 `type` 改變 | 比對兩種情況的 JSX 結構 |
| 每打一個字就失去焦點 | component 定義在 component 裡，或亂數 key | 把定義搬到頂層 |
| 開發時 log、請求都兩次 | StrictMode | production build 看是否消失，同時檢查 cleanup |
| 數字越點越大、順序回不去 | render 裡改了外部變數或 props | 找 `+=`、`sort`、`push`、`reverse` |
| 一個小改動，一堆 component 都 render | 預設連帶行為 | 先看有沒有真的變慢，第 28 章量測 |

要觀察「誰 render 了」，最快是在函式裡加 `console.log`，或打開 React DevTools 設定裡的 Highlight updates when components render。如果 log 有印、畫面沒變，通常是 render 結果和上次相同；如果 log 沒印，代表 trigger 根本沒發生，回頭查第 08 章的 `Object.is` 和不可變更新。

## 常見誤解

**「Virtual DOM 是瀏覽器裡的另一份 DOM。」** 瀏覽器完全不知道它的存在。Element 是你的函式回傳的 JavaScript 物件，每次 render 都產生新的，用完就丟。長期存在、掛著 state 的是 React 內部另一棵樹，叫 Fiber，它的結構與 hooks 規則的由來在第 36 章。這也是為什麼把 element 存進變數重複使用是安全的：它只是描述，本身不持有 state。

**「log 印很多次就是效能問題。」** Render 次數本身不是問題，函式跑得快就沒人感覺得到，而且多數 render 最後不會改 DOM。為了減少次數到處加 `memo`，常常只是換來更多要維護的比對，第 14 章會算這筆帳。判斷效能要用量測（第 28 章），不要用 log 的行數。

**「把 `key` 加在 component 最外層的元素上就能重置它。」** 這個寫法看起來很合理：

```tsx
const ProfileForm = ({ userId }: { userId: string }): React.JSX.Element => {
  const [name, setName] = useState('');
  return (
    <form key={userId}>
      <input aria-label="姓名" value={name} onChange={(event) => setName(event.target.value)} />
    </form>
  );
};
```

換 `userId` 時，`<form>` 和 `<input>` 的 DOM 確實都重建了，但輸入框的值還在。`name` 這個 state 掛在 `ProfileForm` 上，而 `ProfileForm` 自己的位置和 key 都沒變。Key 只會重置**它所在節點以下**的東西，所以要放在 state 擁有者的外面，由 parent 來寫：`<ProfileForm key={userId} userId={userId} />`。

**「production 不會跑兩次，所以 StrictMode 抓到的東西不用修。」** 雙重呼叫只是把問題提早暴露的手段，bug 本身在 production 也存在。前面的列編號在沒有 StrictMode 時，只要父層更新一次就錯了，到了第 30 章的 transition，render 被打斷重來時還會出現更多次呼叫。

## 同事會來問你的問題

**「我只改一個欄位，為什麼整頁 component 都 render 了？」** 因為 state 放在頁面這一層，更新會連帶呼叫它底下的所有子孫，這是預設行為，不是 bug。React 保守地重算，比對後只改有差異的 DOM，所以通常不用處理。真的慢了，依序考慮：把 state 往下搬到真正需要的 component；把昂貴的內容從外面當 `children` 傳進來；最後才用 `memo`。前兩個不增加任何比對成本，所以優先。

**「console.log 印兩次，是不是我的 Effect 或 component 寫錯了？」** 通常是 StrictMode 在開發模式多呼叫一次，用來檢查函式是否 pure，production 不會發生。裝了 React DevTools 的話，第二次的 log 是淡色的。但不要因此直接無視：如果兩次的結果不一樣（資料重複、編號跳號），那才是它要抓的 bug。

**「新任務還沒存到後端，沒有 id，key 用什麼？」** 在建立物件時由前端產生，`createTask` 就是用 `crypto.randomUUID()`。如果之後要換成後端發的 id，要知道換 key 等於換身份，那一列的 state 會被清掉、DOM 會重建。正在編輯這一列的使用者會因此丟掉草稿。最省事的做法是讓前端產生的 id 就是正式 id，由後端接受；第 21 章的樂觀更新會再碰到這個選擇。

**「該用 `key` 重置，還是在事件裡一個個 `setXxx('')`？」** 看你要重置的範圍。整個 component 語意上變成另一個東西（換了任務、換了使用者），用 key，它不會漏掉新增的欄位，也不會漏掉子孫的 state。只清其中幾個欄位、其他要留著（例如新增後清空標題但保留指派人），在 handler 裡呼叫 setter。送出後清空表單這種情況兩者都行，但 key 會讓輸入框失去焦點，要留焦點就用 setter。

## 本章小結

State 更新會觸發 render，也就是重新呼叫該 component 與它的子孫；React 比對前後兩棵 element 樹，只在 commit 時把差異寫進 DOM。因為呼叫時機由 React 決定，component 必須 pure，StrictMode 用多呼叫一次來檢查這件事。State 掛在樹的位置上，同位置同 `type` 就保留，`key` 則讓你明確告訴 React 誰是誰，這就是開場草稿跑錯列的原因和解法。第 06 到 09 章的零件到這裡都齊了，第 10 章用一個井字遊戲把它們組起來走一遍，並看到 `key` 在歷史回放裡的用法。

## 連結

- [[react-08-state]] — 上一章：state 快照、不可變更新、lifting state
- [[react-10-tic-tac-toe]] — 下一章：把前四章組成一個完整的小遊戲
- [[react-00-why-react]] — `v = fn(s)` 與 mutation 的痛點
- [[react-01-browser-and-dom]] — 瀏覽器的 layout 與 paint
- [[react-06-components-and-jsx]] — JSX 編譯結果與 `key` 初探
- [[react-11-effects]] — StrictMode 下 Effect 的 cleanup、為什麼不用 Effect 同步 state
- [[react-12-refs]] — ref callback 與跨 render 的值
- [[react-14-memoization]] — `React.memo` 的完整取捨
- [[react-28-performance]] — 量測 render 成本、把 state 往下搬
- [[react-30-concurrent-react]] — render 被打斷時 purity 的重要性、`<Activity>`
- [[react-36-react-internals]] — Fiber 樹與 reconciler 的假設
- [[dom]] — 真實 DOM 的深入內容
