---
type: concept
domain: tech
tags: [react, props, children, one-way-data-flow, layout-component, typescript, events]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 07 章：Props — 資料怎麼在 component 之間流動

## 點了沒反應，打一個字卻自己勾上了

第 06 章的 `TaskItem` 留了一個 `readOnly`，checkbox 點不動。現在要讓它能勾。手上已經有 `task` 這個物件，最順手的做法就是直接改它：

```tsx
import type { Task } from './types';

interface TaskItemProps {
  task: Task;
}

export const TaskItem = ({ task }: TaskItemProps): React.JSX.Element => (
  <li>
    <input
      type="checkbox"
      aria-label={`完成 ${task.title}`}
      checked={task.status === 'done'}
      onChange={() => {
        task.status = task.status === 'done' ? 'todo' : 'done';
      }}
    />
    <span>{task.title}</span>
  </li>
);
```

TypeScript 沒有抱怨，console 也沒有警告。點下去，勾勾沒有出現。你在 handler 裡印 `task.status`，值確實變成 `done` 了。

接著怪事來了。同事在頁面上方加了一個搜尋框（它用 state，第 08 章才講，這裡只要知道每打一個字，上層和底下的 component 都會重新跑一次）。你在搜尋框打一個字，剛才那個 checkbox 自己勾上了。再試一次：點兩下 checkbox，打字，沒有變化；點三下，打字，又勾上了。

資料改了，畫面不動；不相干的操作，畫面才跳；跳不跳還看點擊次數的奇偶。這個 bug 的成因就是本章的主題：資料在 component 之間怎麼流動，誰可以改它，子層又該怎麼把「使用者點了」這件事傳回去。讀完這章，你能解釋上面每一個症狀，也會把 Task Tracker 的 component 用正確的方式接起來。

## Props 是函式參數，只是呼叫的人是 React

第 06 章說過，`<TaskItem task={task} />` 會編譯成 `jsx(TaskItem, { task })`，產生一個 element 物件，第二個引數就是 props。之後 React 決定要畫這個 component 時，才用這個物件去呼叫 `TaskItem`。所以 props 對 component 而言，就是引數對函式的關係，資料從呼叫端傳進來，函式根據它算出結果。

這個類比有三個差異要記住。第一，呼叫時機不歸你管，同一個 component 可能被呼叫很多次，每次都收到一份新的 props，開場那個搜尋框就是這樣讓 `TaskItem` 重跑的。第二，參數永遠只有一個物件，所以慣例上直接在參數位置解構。第三，有些屬性 React 會自己留著：寫 `<TaskItem key={task.id} task={task} />` 時，`key` 不會出現在 props 裡，因為它是給 React 比對用的，component 需要 id 就得另外傳。`ref` 在 React 19 則是一般的 prop，第 12 章會用到。

JSX 屬性的寫法都對應到這個物件的建立方式：

```tsx
<>
  <TaskItem task={task} onToggle={handleToggle} />
  <TextField label="標題" isInvalid />
  <TaskItem {...itemProps} />
</>
```

雙引號是字串，大括號是任意運算式。只寫名字等於 `isInvalid={true}`（`TextField` 本章後面會寫）。`itemProps` 假設是一個含 `task` 和 `onToggle` 的物件，`{...itemProps}` 把它的欄位攤開成多個屬性，和第 02 章的 spread 是同一回事。

## 資料只往下流

Props 只有一個方向：父層傳給子層。子層沒有任何語法可以把值「寫回」父層的變數。

這是刻意的限制。第 00 章提過的 AngularJS 有雙向綁定，input 改了 model 就跟著改，寫起來很省事。代價出現在專案長大以後：一個值可能被畫面上任何綁定它的地方改掉，某個欄位顯示錯了，你得查遍所有可能寫入它的路徑。

單向資料流把這個搜尋範圍縮小了。Task Tracker 的「設定 CI」顯示錯誤狀態時，推理路徑是固定的：`TaskItem` 的 `task` 從哪來？看誰 render 它，是 `TaskList`。`TaskList` 的 `tasks` 從哪來？再往上一層。沿著 component 樹往上走，走到真正擁有這份資料的地方，錯誤一定在這條路徑上的某一層。code review 時也一樣，看到一個 component 就知道它的輸入都寫在 props 型別裡。

但這個保證有前提：子層得真的不改收到的東西。開場的程式碼違反的就是這一點，而 React 只擋得住其中一部分。

## 唯讀的規則，React 只擋了最外層

「props 是唯讀的」聽起來像語言層級的保護，實際上各種改法的下場很不一樣：

| 寫法 | TypeScript | 開發版 runtime | 實際後果 |
| --- | --- | --- | --- |
| `props.title = '新標題'` | 不擋 | 丟 `TypeError` | render 當場失敗 |
| 解構後 `label = label.toUpperCase()` | 不擋 | 不擋 | 只改區域變數，外面不受影響 |
| `task.status = 'done'` | 不擋 | 不擋 | 改到父層持有的物件，畫面不更新 |
| `tasks.sort(byTitle)` | 不擋 | 不擋 | 就地重排父層的陣列 |

第一列會炸，是因為開發版的 `jsx()` 建立 element 時對 props 物件呼叫了 `Object.freeze`，對它賦值會得到 `Cannot assign to read only property 'title' of object`。production 版的 JSX runtime 沒有這個 freeze，所以這是開發階段的提醒，上線後不會替你把關。

第二列常被誤認為違規。`label` 解構出來後只是這次函式呼叫的區域變數，重新指派它不影響任何人，TypeScript 也不會報錯。只是讀程式的人會以為 prop 被改了，寫成 `const upperLabel = label.toUpperCase()` 比較清楚。

第三、四列才是真正的陷阱。`Object.freeze` 是淺層的，第 02 章講過物件是以參考傳遞的，`props.task` 這個欄位不能換，它指向的物件卻完全沒被凍結，和父層手上的是同一個。

現在可以把開場的症狀一個一個解開了：

1. 點 checkbox：handler 把物件的 `status` 改成 `done`，但改物件這個動作不會通知 React，沒有新的 render。`checked` 由資料決定，上一次 render 給的是 `false`，React 就把 DOM 的勾選狀態還原回去，所以勾勾沒有出現。
2. 在搜尋框打字：上層 render，連帶 `TaskItem` 重跑。這次讀到的 `task.status` 已經是 `done`，畫面終於對上被偷改的值。
3. 奇偶次：每次點擊都真的翻轉了物件，只是看不到。點兩下翻回原值，下次 render 就看不出變化。

同一個物件還被所有持有它的地方共用。只要另一個區塊也顯示這筆任務，它會在自己下次 render 時悄悄換成新狀態，兩個區塊可能一時顯示不同的結果。

後端讀者對這件事應該不陌生。C# 把 class 實例傳進方法，方法改它的屬性，呼叫端也看得到，因為傳的是參考。類比破在回到呼叫端之後：C# 的呼叫端接著讀欄位就拿到新值，React 的父層卻不會重新執行，畫面停在舊的計算結果上。

既然 runtime 擋不住，就讓型別來擋。把參數型別收緊，寫入和就地排序都會變成編譯錯誤：

```tsx
interface ReadonlyTaskItemProps {
  task: Readonly<Task>;
}

interface SortedTaskListProps {
  tasks: readonly Task[];
}

// 不會改到原陣列；readonly 陣列上根本沒有 sort
const sortedTasks = tasks.toSorted((a, b) => a.title.localeCompare(b.title));
```

一般的 `Task[]` 可以傳給 `readonly Task[]`，呼叫端不用改。本書其他範例為了簡短沒有全面加上，你的團隊若常被這類 bug 咬，把它寫進 props 的慣例很划算。

## 資料往下，事件往上

子層不能改資料，那使用者點了 checkbox 這件事怎麼讓擁有資料的人知道？用 props 本來就能傳函式這一點：父層把一個函式傳下去，子層在事件發生時呼叫它。

```tsx
interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
}

<input
  type="checkbox"
  checked={task.status === 'done'}
  onChange={() => onToggle(task.id)}
/>
```

`TaskItem` 只回報「這一筆被切換了」，不決定切換後是什麼狀態。第 02 章的 `toggleTask` 把 `done` 切成 `todo`、其餘切成 `done`，這個規則屬於擁有 `tasks` 的那一層，`TaskItem` 不必知道。資料和通知的方向畫出來是這樣：

```text
App（持有資料與 handleToggle）
  |  tasks、onToggle
  v
TaskList
  |  task、onToggle
  v
TaskItem --- 使用者點擊 ---> 呼叫 onToggle('t-2')
                             這個函式定義在 App，資料在那裡被更新
```

「事件往上」的往上不是什麼新機制，就是呼叫一個從上面傳下來的函式。命名慣例也跟著這個分工：prop 叫 `onToggle`，描述發生了什麼事；父層的實作叫 `handleToggle`，描述怎麼處理。

callback 的參數值得想一下。一種偷懶的寫法是把 DOM 事件原樣往上丟：

```tsx
interface LeakyTaskItemProps {
  task: Task;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}
```

這樣父層得知道 `TaskItem` 內部用的是 `<input>`，還要自己從事件裡找出是哪一筆。之後把 checkbox 換成按鈕，事件型別變了，所有呼叫端都要跟著改。`onToggle(id)` 傳的是領域語言，內部怎麼畫都不影響外面。

注意 `TaskList` 自己不用 `onToggle`，只是轉傳。一層這樣做很正常。如果一個 prop 要穿過很多不需要它的 component，就是第 13 章要處理的 prop drilling；在那之前，下面的 `children` 就能解決一部分。

## Props 可以是任何值

既然 props 就是一個 JavaScript 物件，欄位放什麼都可以：字串、數字、物件、陣列、函式，還有第 06 章看過的 element，它本身也只是物件。工具列按鈕用一個 interface 就能看到大部分種類：

```tsx
import type { CSSProperties, ReactNode } from 'react';

interface ToolbarButtonProps {
  label: string;
  onClick: () => void;
  icon?: ReactNode;
  style?: CSSProperties;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
}

export const ToolbarButton = ({
  label,
  onClick,
  icon,
  style,
  variant = 'secondary',
  disabled = false,
}: ToolbarButtonProps): React.JSX.Element => (
  <button
    type="button"
    className={`toolbar-button toolbar-button-${variant}`}
    style={style}
    disabled={disabled}
    onClick={onClick}
  >
    {icon}
    {label}
  </button>
);
```

`type="button"` 是因為 HTML 裡 `<button>` 的預設 type 是 `submit`，放進表單會意外送出。至於 `variant` 用 union，第 16 章會改寫成 `cva`。

`icon` 最容易寫錯，因為有兩種東西都叫「把 icon 傳進去」。`icon={<FlagIcon />}` 傳的是 element，已經描述好要畫什麼，`ToolbarButton` 直接放進 JSX 就好。`icon={FlagIcon}` 傳的是 component 函式本身，放進 JSX 的 `{icon}` 什麼也畫不出來，開發版會警告 `Functions are not valid as a React child`。幸好 `ReactNode` 不包含函式，TypeScript 會先擋下。

預設選 element，呼叫端可以自由決定大小和顏色。如果 `ToolbarButton` 必須自己控制 icon 的 props（例如統一尺寸），才改收 component，型別寫 `ComponentType<{ size: number }>`，解構時改成大寫開頭的名字再 render：`({ icon: Icon }) => <Icon size={16} />`。大寫是必要的，第 06 章講過 JSX 靠大小寫分辨 DOM 標籤與 component。

物件和函式 props 還有一個日後才會在意的性質：`style={{ color: 'red' }}` 每次 render 都是新物件。平常沒有影響，第 14 章談 `memo` 時它才變得重要。

## children：把內容的決定權留給使用者

Task Tracker 需要一個看板外框，有標題和固定的版面。第一版很容易長成這樣：

```tsx
<TaskBoard
  title="任務"
  tasks={tasks}
  onToggle={handleToggle}
  emptyText="目前沒有任務。"
  isFormVisible
  isFilterVisible
/>
```

外框本來只管排版，現在卻得 import `TaskList`、表單和篩選器，把一半的 props 原封不動轉傳下去。之後想在看板放一張統計卡，又得多一個 `isStatsVisible`。每個新需求都要改這個 component，而且它和裡面放的東西綁死了，沒辦法拿去裝別的內容。

換個想法：外框不必知道裡面是什麼，留個位置就好。

```tsx
import type { ReactNode } from 'react';

interface TaskBoardProps {
  title: string;
  children: ReactNode;
}

export const TaskBoard = ({ title, children }: TaskBoardProps): React.JSX.Element => (
  <section className="task-board">
    <h2>{title}</h2>
    {children}
  </section>
);
```

使用時，開始和結束標籤之間的內容就是 `children`：

```tsx
<TaskBoard title="任務">
  <TaskList tasks={SAMPLE_TASKS} onToggle={handleToggle} />
</TaskBoard>
```

`children` 沒有魔法，它就是 props 物件裡一個叫這個名字的欄位。上面那段編譯後等於 `jsx(TaskBoard, { title: '任務', children: jsx(TaskList, { ... }) })`。

注意 `handleToggle` 的路徑。它是在使用 `TaskBoard` 的那一層直接交給 `TaskList` 的，`TaskBoard` 全程沒碰過，也不需要宣告 `onToggle`。第一版要穿過外框的 props，現在都不用穿了。遇到「props 一路往下傳」的情況，先問中間那層能不能改成收 `children`，往往不必動用 Context。

### children 的形狀會變，所以型別寫 ReactNode

`children` 的實際值取決於標籤之間寫了什麼：沒寫是 `undefined`，一段文字是字串，一個 element 是物件，兩個以上是陣列，`共 {3} 筆` 這種文字夾運算式也是陣列（`['共 ', 3, ' 筆']`）。所以不要假設它有 `.map` 或 `.props`。真的需要檢視或重組 children 的進階模式留給第 35 章；絕大多數 component 只要把它放進 JSX。

能涵蓋這些形狀的型別是 `ReactNode`，它包含 element、字串、數字、布林、`null`、`undefined` 和它們組成的可迭代物件。把 `children` 寫成 `React.JSX.Element` 看似比較嚴格，實際上 `<TaskBoard title="任務">目前沒有任務</TaskBoard>` 和放兩個子元素都會變成編譯錯誤，等於限制了呼叫端。除非 component 真的只能接受單一 element，否則用 `ReactNode`。

必填與否也有意義：`children: ReactNode` 是必填，`<TaskBoard title="任務" />` 編譯不過。外框沒內容沒有意義時就該這樣寫，反之才加 `?`。

### 放進畫面才會執行

把 element 當 prop 傳下去，子 component 的函式不會因此執行。`<TaskList ... />` 在父層只是建立一個物件，要等這個物件出現在回傳的畫面裡，React 才呼叫 `TaskList`：

```tsx
interface CollapsiblePanelProps {
  isOpen: boolean;
  children: ReactNode;
}

export const CollapsiblePanel = ({ isOpen, children }: CollapsiblePanelProps): React.JSX.Element => (
  <section>{isOpen ? children : null}</section>
);
```

`isOpen` 是 `false` 時，傳進來的 component 一次都不會被呼叫。所以外框可以放心收一個很大的子樹，由它決定要不要顯示。`children` 和 render 之間還有另一層關係，第 09 章會講。

## Layout Component：一個位置不夠就開多個

`children` 最大的用途是 layout component：把排版和樣式封裝起來，內容交給使用者。頁面框架、側邊欄、對話框外殼都是這個形狀。只有一個插槽不夠時，再加幾個型別是 `ReactNode` 的 prop 就好，它們和 `children` 是同一種東西，只是有自己的名字：

```tsx
import type { ReactNode } from 'react';

interface PageLayoutProps {
  header: ReactNode;
  sidebar?: ReactNode;
  children: ReactNode;
}

export const PageLayout = ({ header, sidebar, children }: PageLayoutProps): React.JSX.Element => (
  <div className="page">
    <header className="page-header">{header}</header>
    {sidebar !== undefined && <aside className="page-sidebar">{sidebar}</aside>}
    <main className="page-content">{children}</main>
  </div>
);
```

```tsx
<PageLayout header={<h1>Task Tracker</h1>} sidebar={<nav>篩選</nav>}>
  <TaskBoard title="任務">
    <TaskList tasks={SAMPLE_TASKS} onToggle={handleToggle} />
  </TaskBoard>
</PageLayout>
```

寫過 Razor 的話，`children` 很像 `_Layout.cshtml` 的 `@RenderBody()`，具名的 prop 像 `@RenderSection()`。破口在於 Razor 的 section 是把一段模板交給 layout 輸出，而這裡傳的是普通 JavaScript 值：可以存進變數、用條件決定、在測試裡單獨傳假內容，layout 也能像 `sidebar !== undefined` 那樣判斷它有沒有被傳。

## Optional 與預設值：undefined 和 null 不是同一件事

`?` 讓 prop 可以不傳，預設值則寫在解構的位置，如前面的 `variant = 'secondary'`。這是 JavaScript 的解構預設值，React 沒有參與，所以它遵守 JavaScript 的規則：**只有值是 `undefined` 才補**。

Task Tracker 的 `dueDate` 型別是 `string | null`，API 用 `null` 表示沒有期限。這段程式因此出事：

```tsx
interface TaskDueProps {
  dueDate?: string | null;
}

export const BuggyTaskDue = ({ dueDate = '未排定' }: TaskDueProps): React.JSX.Element => (
  <span>{dueDate}</span>
);
```

`<BuggyTaskDue dueDate={task.dueDate} />` 遇到 `null` 時預設值不生效，`{null}` 什麼也不畫，畫面上留下一塊空白。測試若只測「沒傳」的情況還會過。要涵蓋 `null` 就用第 02 章的 `??`：

```tsx
export const TaskDue = ({ dueDate }: TaskDueProps): React.JSX.Element => (
  <span>{dueDate ?? '未排定'}</span>
);
```

型別上兩者也該分開想：`assigneeId: string | null` 表示欄位一定在，值可能是「沒有」；`icon?: ReactNode` 表示呼叫端可以不提。領域資料多半是前者，component 的設定選項多半是後者。

舊專案可能還看得到 `TaskItem.defaultProps = { ... }` 和 `propTypes`。React 19 對函式 component 已不理會這兩者，`defaultProps` 寫了也不會生效，升級時要改成解構預設值。

## 包原生元素：不要一個一個抄屬性

Task Tracker 需要一個帶標籤的輸入框。第一版列了 `value`、`onChange`、`placeholder`。隔天有人要 `maxLength`，再隔天要 `onBlur`、`autoFocus`、`aria-describedby`，每次都得回來改。`<input>` 有幾十個屬性，一個一個抄沒有盡頭。

解法是讓 props 型別直接繼承原生元素的全部屬性，自己只補多出來的部分，其餘用 rest 原樣交給 `<input>`：

```tsx
import type { ComponentProps } from 'react';

interface TextFieldProps extends ComponentProps<'input'> {
  label: string;
  isInvalid?: boolean;
}

export const TextField = ({
  label,
  isInvalid = false,
  className = '',
  ...rest
}: TextFieldProps): React.JSX.Element => (
  <label className="text-field">
    {label}
    <input
      type="text"
      {...rest}
      aria-invalid={isInvalid}
      className={`text-field-input ${className}`.trim()}
    />
  </label>
);
```

這幾行有三個決定。**自訂的 prop 要先解構出來。** 如果 `isInvalid` 留在 `rest` 裡被攤到 `<input>` 上，開發版會警告 `React does not recognize the isInvalid prop on a DOM element`。**spread 的順序就是覆蓋順序，後寫的贏。** `type="text"` 在 `{...rest}` 前面，所以它是呼叫端可以覆蓋的預設值，`<TextField type="email" />` 會得到 email；`aria-invalid` 寫在後面，就由這個 component 說了算。**className 要合併。** 若它留在 `rest` 裡，要嘛蓋掉內部樣式，要嘛被蓋掉，所以單獨取出來串接，第 16 章會換成 `cn()`。

`ComponentProps<'input'>` 也帶了 `ref`，`ref` 在 React 19 又是一般的 prop，所以它跟著 `rest` 一路到 `<input>`，`<TextField ref={inputRef} />` 不用多寫任何東西。既有程式常見的 `React.InputHTMLAttributes<HTMLInputElement>` 仍可用，但它只有 HTML 屬性，沒有 `ref`。

有時你想改掉某個原生屬性的簽章，例如 `onChange` 直接給字串。直接 `extends` 會因為型別衝突編譯失敗，要先用 `Omit` 拿掉：

```tsx
export interface SearchFieldProps extends Omit<ComponentProps<'input'>, 'onChange'> {
  onChange: (value: string) => void;
}

export const SearchField = ({ onChange, ...rest }: SearchFieldProps): React.JSX.Element => (
  <input {...rest} onChange={(event) => onChange(event.target.value)} />
);
```

`ComponentProps` 也接受 component：`ComponentProps<typeof TaskItem>` 可以取得一個沒有 export props 型別的 component 的 props，包第三方 component 時很好用。

## 事件的型別：讓 TypeScript 從位置推

事件 handler 寫在 JSX 裡時，什麼型別都不用標，TypeScript 從 `onChange` 這個位置就知道 `event` 是什麼：

```tsx
<input onChange={(event) => console.log(event.target.value)} />
```

把 handler 抽出來成獨立函式，這個線索就斷了，才需要自己寫。泛型參數是掛這個 handler 的元素：

```tsx
interface TaskQuickAddProps {
  onAdd: (title: string) => void;
}

export const TaskQuickAdd = ({ onAdd }: TaskQuickAddProps): React.JSX.Element => {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>): void => {
    if (event.key === 'Enter') {
      onAdd(event.currentTarget.value);
      event.currentTarget.value = '';
    }
    if (event.key === 'Escape') {
      event.currentTarget.value = '';
    }
  };

  return <input aria-label="快速新增任務" onKeyDown={handleKeyDown} />;
};
```

這個輸入框還沒有 state，內容留在 DOM 裡，所以直接讀寫 `currentTarget.value`；第 08 章會改成受控的做法。常用的型別不多，查這張表就夠：

| 事件 | 型別 | 常用的欄位與動作 |
| --- | --- | --- |
| `<input>`、`<textarea>`、`<select>` 的 `onChange` | `ChangeEvent<HTMLInputElement>`（另兩個換元素名） | `event.target.value` |
| `<form>` 的 `onSubmit` | `SubmitEvent<HTMLFormElement>` | `event.preventDefault()` |
| 點擊與滑鼠 | `MouseEvent<HTMLButtonElement>` | `event.clientX`、`event.clientY` |
| 鍵盤 | `KeyboardEvent<HTMLInputElement>` | `event.key` |
| 焦點 | `FocusEvent<HTMLInputElement>` | `event.relatedTarget` |

網路上和舊程式裡大量使用的 `FormEvent`，在目前的 `@types/react` 已標為 deprecated，表單送出請用 `SubmitEvent`。這些都是 React 包裝過的 synthetic event，介面和原生事件相近，機制留給第 36 章。

`preventDefault` 在這些事件裡各有用途。按 `ArrowDown` 時呼叫它，可以阻止瀏覽器預設的游標移動或頁面捲動，改由你自己移動選項。`onMouseDown` 上呼叫它，焦點不會離開目前的輸入框，自訂下拉選單靠這招才能讓使用者點選項時輸入框不失焦；同一個按鈕若沒有這行，焦點就被搶走了。

`target` 與 `currentTarget` 要分清楚。第 01 章講過事件會冒泡，`currentTarget` 是掛 handler 的元素，`target` 是實際被點的元素。卡片 `<div>` 上的 `onClick`，點到裡面的按鈕時，`currentTarget` 是 `div`，`target` 是 `button`。正因為 `target` 可能是任何子孫，`MouseEvent` 的 `event.target` 型別只是 `EventTarget`，上面沒有 `dataset`，要用 `instanceof` 收窄。`ChangeEvent` 是例外，它的 `target` 型別就是泛型參數指定的元素，這就是 `event.target.value` 能編譯的原因。

## React.FC 為什麼退場

舊專案和舊教學裡常見這種寫法：

```tsx
const TaskBoard: React.FC<TaskBoardProps> = ({ title, children }) => (
  <section>
    <h2>{title}</h2>
    {children}
  </section>
);
```

它在 `@types/react` 18 之前有一個實質問題：型別會偷偷加上 `children`，於是一個根本不渲染內容的 component，也能被寫成 `<Avatar>內容</Avatar>` 而不報錯，內容就這樣憑空消失。18 拿掉了這個隱含欄位，現在 `FC` 不寫 `children` 就讀不到（`Property 'children' does not exist`），這條理由已不成立，它並沒有錯，也沒有被標為 deprecated。

留下來的理由是它幫不上忙。`FC` 把型別綁在變數上，泛型參數沒有地方宣告，下面這種會隨選項推斷型別的 component 就寫不出來：

```tsx
interface ChoiceGroupProps<T extends string> {
  options: readonly T[];
  value: T;
  onChange: (next: T) => void;
}

export const ChoiceGroup = <T extends string>({
  options,
  value,
  onChange,
}: ChoiceGroupProps<T>): React.JSX.Element => (
  <div role="group">
    {options.map((option) => (
      <button
        key={option}
        type="button"
        aria-pressed={option === value}
        onClick={() => onChange(option)}
      >
        {option}
      </button>
    ))}
  </div>
);
```

傳 `options={STATUSES}`（`STATUSES` 是 `['todo', 'doing', 'done'] as const`）時，`T` 被推斷成 `TaskStatus` 的那三個值，`value="archived"` 會編譯失敗，`onChange` 收到的也是窄型別。此外 `FC` 的回傳型別是 `ReactNode | Promise<ReactNode>`，比第 06 章建議的 `React.JSX.Element` 寬，忘記寫 `return` 這類錯誤比較不容易被抓到。一般的箭頭函式加上參數型別就能表達全部需求，所以本書不用它。在既有專案看到不用急著改，新程式不要再寫。

## 把 Task Tracker 接起來

第 06 章的靜態畫面現在要長出兩件事：`TaskItem` 能回報切換，看板有外框。`types.ts` 和 `sampleTasks.ts` 不動。

先改最底層。拿掉 `readOnly`，因為 `checked` 這次有 `onChange` 了，React 不再需要那個「我是故意的」聲明。handler 也不碰 `task`，只回報 id：

```tsx
import type { Task, TaskStatus } from './types';

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: '待處理',
  doing: '進行中',
  done: '已完成',
};

interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
}

export const TaskItem = ({ task, onToggle }: TaskItemProps): React.JSX.Element => {
  const isDone = task.status === 'done';

  return (
    <li className={isDone ? 'task-item task-item-done' : 'task-item'}>
      <input
        type="checkbox"
        aria-label={`完成 ${task.title}`}
        checked={isDone}
        onChange={() => onToggle(task.id)}
      />
      <span>{task.title}</span>
      <span>{STATUS_LABELS[task.status]}</span>
      {task.dueDate !== null && <time dateTime={task.dueDate}>到期 {task.dueDate}</time>}
    </li>
  );
};
```

`onToggle` 是必填，所以存檔後 TypeScript 會立刻標出所有用到 `TaskItem` 的地方：`TaskList` 缺這個 prop。順著錯誤補，`TaskList` 也多一個 `onToggle` 並轉傳，接著第 06 章的 `TaskListPanel` 也被標出來，同樣補上。必填 prop 讓這次改動的影響範圍由編譯器列給你看，這是不把它寫成 `onToggle?` 的理由。

```tsx
import { TaskItem } from './TaskItem';
import type { Task } from './types';

interface TaskListProps {
  tasks: Task[];
  onToggle: (id: string) => void;
}

export const TaskList = ({ tasks, onToggle }: TaskListProps): React.JSX.Element => {
  if (tasks.length === 0) {
    return <p className="task-list-empty">目前沒有任務。</p>;
  }

  return (
    <ul className="task-list">
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} onToggle={onToggle} />
      ))}
    </ul>
  );
};
```

最後在 `App` 把前面寫好的 `TaskBoard` 套上去。`handleToggle` 目前只能印出 id，因為我們還沒有能讓畫面更新的工具：

```tsx
import { SAMPLE_TASKS } from './sampleTasks';
import { TaskBoard } from './TaskBoard';
import { TaskList } from './TaskList';

const handleToggle = (id: string): void => {
  console.log('toggle', id);
};

export const App = (): React.JSX.Element => (
  <main>
    <h1>Task Tracker</h1>
    <TaskBoard title="任務">
      <TaskList tasks={SAMPLE_TASKS} onToggle={handleToggle} />
    </TaskBoard>
  </main>
);
```

點「補登入頁測試」的 checkbox，console 印出 `toggle t-2`，勾勾沒有變，也沒有任何警告。這次的「不動」和開場不一樣：資料沒被偷改，也不會日後才跳，通知已經送到擁有者手上，只差擁有者真的去更新。

## 常見誤解

**「props 沒變，component 就不會重新執行。」** 開場的 `task` 參考從頭到尾沒變，`TaskItem` 還是跟著上層重跑了。預設情況下父層 render 就會連帶 render 子層，和 props 有沒有變無關。完整機制在第 09 章，能跳過的條件在第 14 章。

**「寫了 `Readonly<TaskItemProps>` 就安全了。」** `Readonly` 和 `Object.freeze` 一樣是淺層的。它讓 `props.task = other` 編譯失敗，`props.task.status = 'done'` 卻照樣通過，所以前面才把 `Readonly` 加在 `Task` 這一層。巢狀更深的資料型別，要逐層標註或另外定義唯讀版本。

**「`children` 是 JSX 的特殊語法。」** 它只是 prop，`<TaskBoard title="任務" children={<p>內容</p>} />` 也能動。兩種同時寫時，標籤之間的內容會蓋掉屬性，TypeScript 會用 `'children' are specified twice` 提醒。平常仍寫在標籤之間，比較好讀。

**「`{...props}` 全部往下傳最省事。」** 轉給 DOM 元素時已經看過未知屬性的警告。轉給另一個 component 也有問題：讀程式的人看不出它實際收到什麼，上層日後多一個同名 prop 也會悄悄改變它的行為。只有在「這層就是對某個元素的薄封裝」時，像 `TextField` 這樣先取走自己的欄位再轉傳才合理。

**「事件物件在 `await` 之後還能照常用。」** 舊文章會說事件物件會被回收、要呼叫 `event.persist()`，那是 React 17 之前的 event pooling，已經拿掉了。但有一件事現在還是會咬人：`async` handler 在 `await` 之後讀 `event.currentTarget` 會得到 `null`，因為事件派送結束後它就被清掉，`event.target` 則還在。要用就在 `await` 之前先存到區域變數。

## 同事會來問你的問題

**「`TaskItem` 要收整個 `task`，還是把 `title`、`status` 攤平成多個 prop？」** 看這個 component 知不知道領域。`TaskItem` 就是用來畫一筆任務的，收 `task` 最自然，之後多顯示一個欄位也不用改呼叫端。`ToolbarButton` 這種通用 component 不該認識 `Task`，它收 `label`、`onClick`，換到別的畫面才用得上。第 14 章談 `memo` 時，傳物件或傳基本值還會影響比較結果。

**「props 用 `interface` 還是 `type`？」** 本書用 `interface`，`extends` 原生屬性時若有欄位衝突，錯誤會直接標在宣告處，比交集型別在使用時才出事好查。需要 union 時只能用 `type`，例如「`mode` 是 `edit` 時才有 `onSave`」這種 discriminated union 的 props。判斷的完整理由在第 05 章。

**「Boolean prop 越來越多，`isPrimary`、`isDanger`、`isGhost`，怎麼辦？」** 這些旗標彼此互斥，型別卻允許 `isPrimary` 和 `isDanger` 同時為 `true`，這正是第 05 章說的不合法狀態。收斂成一個 `variant: 'primary' | 'danger' | 'ghost'`，互斥就由型別保證。如果旗標是在控制「裡面要不要出現某區塊」，那通常該改成 `children` 或插槽，第 35 章會整理這類 props 爆炸的治法。

**「為什麼 `ToolbarButton` 的 prop 叫 `disabled`，不照規範叫 `isDisabled`？」** `is` 前綴用在自己發明的 Boolean，例如 `isInvalid`。對應到原生 HTML 屬性的 prop 應該沿用原名，這樣繼承 `ComponentProps` 時才能直接轉傳，呼叫端也不用記兩套名字。

**「`onToggle` 傳了三層，算 prop drilling 嗎？要上 Context 嗎？」** 先看中間層是不是只在轉傳。兩三層、每層都和任務清單有關，寫清楚的 props 反而好追，錯了 TypeScript 會一路標出來。如果中間層只是版面，先改成 `children`，路徑就消失了。還是穿過一大片無關的 component 時才考慮 Context，第 13 章會談它的成本。

## 本章小結

Props 是 React 呼叫 component 時傳入的參數，資料沿著它往下流，事件透過傳下去的函式往上回報，所以畫面錯了可以沿著 component 樹往上追。React 只凍結 props 物件本身，裡面的物件和陣列要靠你和型別來保護，改了它們不但不會更新畫面，還會在之後某次 render 才冒出來。`children` 與具名插槽把內容的決定權留給使用者，也省掉一部分轉傳；包原生元素則用 `ComponentProps` 加 rest，留意 spread 的順序。現在 Task Tracker 的通知已經送到 `App`，資料卻還改不動，因為我們缺一種「值變了就讓 React 重算畫面」的東西，下一章的 state 就是它。

## 連結

- 上一章：[[react-06-components-and-jsx]]
- 下一章：[[react-08-state]]
- 相關章節：[[react-02-javascript-for-react]]、[[react-05-typescript-modeling]]、[[react-09-rendering]]、[[react-12-refs]]、[[react-13-reducer-and-context]]、[[react-14-memoization]]、[[react-16-tailwind]]、[[react-35-component-patterns]]、[[react-36-react-internals]]
- 相關頁面：[[typescript]]、[[dom]]、[[javascript-typescript-react-foundations]]
