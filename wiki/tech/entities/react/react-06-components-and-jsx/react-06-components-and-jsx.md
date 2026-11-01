---
type: concept
domain: tech
tags: [react, jsx, component, composition, fragment, conditional-rendering, key, typescript]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
created: 2026-10-31
updated: 2026-10-31
---

# 第 06 章：Component 與 JSX — 長得像 HTML 的函式呼叫

## 貼上設計稿之後，畫面左上角多了一個 0

Task Tracker 目前有第 04、05 章的型別，有第 02 章的 `taskOps.ts`，畫面上卻只有第 00 章留下的標題。設計師給了任務清單的 HTML 稿，你心想這不就是貼進 component 嗎：

```tsx
export const TaskList = (): React.JSX.Element => (
  <div class="task-panel" style="margin-top: 8px">
    <ul>
      <li class="task-item"><input type="checkbox" checked> 設定 CI<br><small>到期 2026-11-03</small></li>
    </ul>
  </div>
);
```

編譯器的第一句話是 `JSX element 'input' has no corresponding closing tag`。瀏覽器明明吃這份 HTML，你把 `<input>` 和 `<br>` 補成自閉合，再編譯一次，這回變成 `Type '{ class: string; ... }' is not assignable to type ...`，連 `class` 都不行。改成 `className`，接著 `style` 又報 `Type 'string' has no properties in common with type 'Properties<...>'`。

好不容易過了，你想在清單是空的時候不要顯示 `<ul>`。寫過 Razor 的手很自然地想寫 `@if`，換成這裡的大括號：

```tsx
<div>{if (tasks.length > 0) { <ul>{rows}</ul> }}</div>
```

編譯器回 `Expression expected`。你上網查到大家都用 `&&`，改成這樣就過了：

```tsx
<div>{tasks.length && <ul>{rows}</ul>}</div>
```

測試資料有三筆時一切正常。後端回空陣列那天，QA 貼來一張截圖：清單區塊什麼都沒有，只有一個孤零零的 `0`。

這幾個錯誤看起來各不相干，其實都從同一件事來。本章要回答的問題是：JSX 到底是什麼？答案確定之後，`class` 為什麼不行、`if` 為什麼不能放進大括號、那個 `0` 從哪裡來，都可以直接推出來，不用背。讀完這章，Task Tracker 會有第一個由 `TaskList` 和 `TaskItem` 組成的靜態畫面。

## JSX 會被編譯成函式呼叫

瀏覽器不認識 JSX。專案在開發和打包時，Vite 用 Oxc 把 `.tsx` 轉成一般 JavaScript，`tsc` 依 `tsconfig` 的 `"jsx": "react-jsx"` 設定做型別檢查，兩邊用的都是 automatic runtime 這種轉換。轉譯結果整理後長這樣：

```tsx
// 你寫的
<h1 className="title">Hello</h1>

// 編譯器產出的
import { jsx } from 'react/jsx-runtime';
jsx('h1', { className: 'title', children: 'Hello' });
```

標籤名變成第一個參數，屬性和內容一起變成第二個參數的物件，內容放在 `children` 這個 key。整個 JSX 語法就是這個轉換的糖衣，執行時程式裡已經沒有任何標籤了。

所以 JSX 可以出現在任何能放函式呼叫的地方：指派給變數、放進陣列、當函式回傳值、當另一個函式的引數。大括號的規則也跟著確定了。`<p>{title}</p>` 編譯成 `jsx('p', { children: title })`，大括號裡的東西要放進物件的值，而物件的值只能是**運算式**（expression），也就是會算出一個值的東西。`if` 是陳述式（statement），`{ children: if (x) { ... } }` 在 JavaScript 裡本來就不合法，開場的 `Expression expected` 說的就是這件事。三元運算子、`&&`、函式呼叫、`map` 都是運算式，因此都能放。

寫過 Razor 的人會想拿 `.cshtml` 來對照，這個類比在一點上有幫助：兩者都把資料嵌進標記。它破在方向相反。Razor 是模板語言，以 HTML 為主體，用 `@` 跳進 C#，引擎自己定義了 `@if`、`@foreach` 這些控制結構，輸出的是字串。JSX 以 JavaScript 為主體，標籤只是函式呼叫的另一種寫法，它沒有自己的控制結構，條件和迴圈都用語言本來就有的東西，輸出的是物件。

這也是 React 不提供 `v-if`、`*ngFor` 這類指令的原因。第一次看會覺得缺東西，好處是不用學第二套語言：`filter`、`map`、解構、型別收窄全部照常運作，TypeScript 也能檢查到每個屬性。

### 舊教材的 `React.createElement` 和 `import React`

你在舊專案或舊教材會看到另一種編譯結果：

```tsx
import React from 'react';
React.createElement('h1', { className: 'title' }, 'Hello');
```

這是 React 17 之前的 classic runtime。JSX 會被編譯成對 `React` 這個變數的呼叫，所以每個檔案即使沒用到 `React` 也得 import 它，少了就會在執行時出錯。React 17 引入的 automatic runtime 改由編譯器自己 import `react/jsx-runtime`，這行 import 就不用寫了。`createElement` 仍然是公開 API，產出的 element 有相同的 `type` 和 `props`，只是平常不必手寫。

## JSX 算出來的是一個物件，畫面還沒出現

`jsx()` 回傳什麼？把結果印出來就知道：

```tsx
const heading = <h1 className="title">Hello</h1>;
console.log(heading.type); // 'h1'
console.log(heading.key); // null
console.log(heading.props); // { className: 'title', children: 'Hello' }
```

這個物件叫 **React element**。它沒有對應任何 DOM 節點，也沒有動到畫面，只是一張記著「這裡要有一個 `h1`，屬性是這些」的便條。第 01 章用原生 DOM 寫清單時，`document.createElement('li')` 當場就造出真的節點；React element 只是描述，造起來幾乎沒有成本，用完就丟也無所謂。第 00 章的 `v = fn(s)`，那個 `v` 指的就是它。

`type` 不一定是字串。component 的情況更值得看：

```tsx
const element = <TaskItem key={task.id} task={task} />;
console.log(element.type === TaskItem); // true
console.log(element.key); // 't-1'
console.log(Object.keys(element.props)); // ['task']
```

這裡有兩件事。第一，`type` 存的是 `TaskItem` 這個函式本身。編譯結果是 `jsx(TaskItem, { task }, task.id)`，寫下 `<TaskItem />` 的當下，`TaskItem` **沒有被呼叫**，它只是被記在 element 上。什麼時候呼叫、呼叫幾次，由 React 決定。第二，`key` 被編譯成獨立的第三個參數，不進 `props`，`TaskItem` 裡讀不到 `props.key`。本章後面談列表時會用到這點。

```text
TaskList.tsx 裡的 JSX
    |  編譯時：Oxc 轉成函式呼叫
    v
jsx(TaskItem, { task }, task.id)
    |  執行時：TaskList 被呼叫才跑到這行
    v
element：{ type: TaskItem, key: 't-1', props: { task } }
    |  React 讀 element
    |    type 是函式 → 呼叫它，拿回下一層 element，繼續往下
    |    type 是字串 → 對應一個 DOM 節點
    v
DOM（怎麼比對、何時更新，第 09 章）
```

這張圖解釋了大小寫規則。編譯器看第一個字母決定 `type` 是什麼：`<taskItem />` 編譯成 `jsx('taskItem', {})`，傳的是**字串**；`<TaskItem />` 編譯成 `jsx(TaskItem, {})`，傳的是**變數**。所以 component 名稱必須大寫開頭。寫錯時 TypeScript 會報 `Property 'taskItem' does not exist on type 'JSX.IntrinsicElements'`。沒有型別檢查的話，React 會真的在 DOM 裡造一個 `<taskitem>` 標籤，並在 console 警告大小寫不對，你的函式則從頭到尾沒被呼叫。

## JSX 和 HTML 的每條差異都有來由

知道 JSX 是函式呼叫加物件之後，那些跟 HTML 不一樣的規則就不必死背。屬性會變成物件的 key，而且這些 key 大多對應 DOM property，下面這張表的前四列都來自這一點：

| HTML | JSX | 來由 |
| --- | --- | --- |
| `class="a"` | `className="a"` | `class` 是 JS 保留字，`const { class } = props` 不合法；DOM property 本來也叫 `element.className` |
| `for="x"` | `htmlFor="x"` | `for` 同樣是保留字，DOM property 叫 `htmlFor` |
| `onclick`、`tabindex` | `onClick`、`tabIndex` | 物件 key 採 camelCase |
| `style="margin-top: 8px"` | `style={{ marginTop: 8 }}` | `style` 收物件，TypeScript 可以逐項檢查 |
| `<br>`、`<input>` | `<br />`、`<input />` | JSX 解析器不帶 HTML 的 void element 清單，每個標籤都要明確結束 |
| `<!-- 註解 -->` | `{/* 註解 */}` | 大括號裡是 JavaScript，註解用 JavaScript 的 |

`data-*` 和 `aria-*` 是例外，它們保留連字號，寫 `data-task-id="t-1"`、`aria-label="卡片"`。JSX 語法允許屬性名有連字號，編譯出來就是帶引號的 key。

`style` 的 `{{ }}` 常被當成特殊語法，其實是兩件事疊在一起：外層大括號表示「這裡是 JavaScript」，內層是物件字面值。數字值會自動補 `px`，所以 `marginTop: 8` 得到 `8px`；`lineHeight: 1.5` 這類本來就沒有單位的屬性維持 `1.5`。

布林屬性也照 JavaScript 的值走。`<button disabled>` 等於 `disabled={true}`；`disabled={false}` 時 DOM 上不會有這個屬性。這比 HTML 好懂，HTML 裡寫 `disabled="false"` 反而是停用，只要屬性存在就算。

### 換行不等於空白

有一個差異不會有任何編譯錯誤，只會讓版面悄悄變樣。HTML 把換行當成空白，JSX 不是：

```tsx
<p>
  負責人
  <strong>阿明</strong>
</p>
```

畫面文字是「負責人阿明」，中間沒有空白。JSX 會把含換行的空白整段丟掉，好讓你可以自由縮排而不會在 DOM 裡多出文字。要空白就明寫 `負責人{' '}`。同一行內的空白會保留，所以 `<time>到期 {task.dueDate}</time>` 不需要特別處理。

### 插入的字串會被當成文字

大括號塞字串進去時，React 把它設成 text，而非解析成 HTML：

```tsx
const title = '<img src=x onerror="alert(1)">';
return <span>{title}</span>;
```

畫面上就是這串字元本身，DOM 裡沒有 `<img>`。任務標題是使用者輸入的，這個預設替你擋掉最常見的 XSS。它的邊界在屬性值和 `dangerouslySetInnerHTML`，第 37 章會處理。

## 只能回傳一個根，以及為什麼不要多包一層 div

編譯一下兩個並列標籤就知道問題在哪：`return <h2>標題</h2><p>內容</p>;` 等於 `return jsx('h2', ...) jsx('p', ...);`，一個 `return` 後面接兩個值，JavaScript 沒有這種語法。TypeScript 報 `JSX expressions must have one parent element`。

最順手的解法是外面包 `<div>`，多數時候也沒事，但有些父子關係容不下多出來的節點。假設你想把任務表格的兩個欄位抽成 component：

```tsx
const TaskCells = (): React.JSX.Element => (
  <div>
    <td>設定 CI</td>
    <td>已完成</td>
  </div>
);
```

把它放進 `<tr>`，DOM 就真的變成 `tr > div > td`，表格欄位全亂，console 也會印 `In HTML, <div> cannot be a child of <tr>`。CSS 也一樣，父層是 `display: grid` 或 `flex` 時，多一層 `div` 會讓子項目不再是直接的 grid/flex item，排版跟著跑掉。

**Fragment** 解決這個需求：它在 element 這層把東西包成一個值，DOM 這層什麼都不留。

```tsx
const TaskCells = (): React.JSX.Element => (
  <>
    <td>設定 CI</td>
    <td>已完成</td>
  </>
);
```

這次 `<tr>` 的兩個子節點都是 `<td>`。`<>...</>` 是 `<Fragment>` 的縮寫，編譯成 `jsx(Fragment, { children: ... })`。縮寫有一個限制，它沒有地方寫屬性，所以需要 `key` 時要寫完整的 `<Fragment key={...}>`，列表那節會看到。

多行 JSX 外面習慣加小括號，這也有實際理由。JavaScript 的自動補分號會讓 `return` 後面直接換行的程式碼變成 `return;`，後面的 JSX 成了執行不到的死碼。宣告了回傳型別時 TypeScript 會報 `Type 'undefined' is not assignable to type 'Element'`，沒宣告的話 component 就靜悄悄地什麼都不畫。React 允許 component 回傳 `undefined`，這種情況不會有警告。這是本書要求完整範例寫 explicit return type 的理由之一。

## Component 是回傳 element 的函式

有了 element，component 的定義就很短：一個函式，收一個物件參數，回傳 React 能畫的東西。

```tsx
interface TaskTitleProps {
  title: string;
}

const TaskTitle = ({ title }: TaskTitleProps): React.JSX.Element => <h2>{title}</h2>;
```

`<TaskTitle title="設定 CI" />` 上的屬性就是這個函式收到的物件，也就是 **props**。本章只用到「屬性會變成參數」這一點，唯讀規則、預設值、`children` 和型別技巧都在第 07 章。

函式能回傳的不只 JSX。字串、數字、`null`、陣列和 Fragment 都可以，這些值的總稱是 `ReactNode` 型別。回傳 `null` 表示這個 component 這次什麼都不畫。

因為 component 是函式，建立和組合函式的直覺可以直接帶過來：小函式組成大函式，輸入決定輸出。函式裡可以先算好再回傳，也可以在回傳前用 `if`，因為那裡還是普通的 JavaScript，只有 JSX 的大括號裡面才限定運算式。你的 `if` 不是不能寫，只是位置要放對。

## 關注點分離換了一條切法

寫 ASP.NET Core MVC 或傳統網頁時，慣例是 View 放 `.cshtml`、樣式放 `.css`、行為放 `.js`，三種檔案各放一個資料夾。這是按**技術類型**分離。React 讓第一次看的人不舒服的地方，就是把標記和邏輯寫在一起，看起來像在開倒車。

判斷切法好不好，可以看改一個需求時要動幾個地方。假設任務要新增 `blocked` 狀態，按技術類型分離的話，模板要多一個分支，`.js` 的顯示文字對照要改，`.css` 要加一個 class，這三處之間的關聯沒有任何東西在維護：改名 `task-item-done` 時 CSS 和模板要各改一次，少改一處沒有編譯錯誤，只有畫面默默壞掉。而同一個資料夾裡，`.cshtml` 和 `.js` 之間的距離可能比 `TaskItem` 和 `UserTable` 之間還遠，它們實際上互不相干。

React 的主張是按**功能**分離：和「一筆任務長什麼樣」有關的結構、顯示文字、條件判斷都放在 `TaskItem`。新增狀態時，TypeScript 會因為第 04 章的 `Record<TaskStatus, string>` 缺 key 而報錯，直接把你帶到要改的地方。

這不代表什麼都往 component 塞。放進同一個 component 的標準是「它們會一起改」。第 02 章的 `toggleTask` 不依賴畫面，留在 `taskOps.ts` 才好測試，也才能讓別的畫面重用。第 20 章的 API client 更不該出現在 `TaskItem`，否則一個顯示用的 component 就綁死了網路，測試要 mock HTTP，換個地方用就會多打一次 API。

## 怎麼把畫面切成 component

Composition 是 React 重用程式碼的主要手段：大 component 由小 component 組成，就像函式呼叫函式。從設計稿往下切時，判斷依據是這幾個問題：

- 這塊有自己的名字嗎？`TaskItem` 有，「清單裡第二層那個 div」沒有。
- 這塊會重複嗎？一筆任務會出現很多次，每次只有資料不同。
- 這塊的改動理由和旁邊不一樣嗎？調整到期日顯示的人不必讀整個清單。

切過頭也有症狀。下面這個 component 沒有增加任何資訊，讀者為了知道畫面長怎樣，要多跳一個檔案：

```tsx
const TaskTitleText = ({ title }: TaskTitleProps): React.JSX.Element => <span>{title}</span>;
```

更多抽取時機的判斷，第 10 章做 Tic-Tac-Toe 時會在實作中再走一遍。現在回到任務清單，它有兩層明顯的東西：一筆任務，以及把任務排起來的清單。先看單筆。

## 從 `&&` 的那個 0 看懂條件渲染

單筆任務有「有到期日才顯示」的需求，於是回到開場的問題。要知道 `0` 從哪來，得先知道 React 看到各種 child 值時怎麼處理：

| child 的值 | 畫面 |
| --- | --- |
| `false`、`true`、`null`、`undefined` | 什麼都不畫 |
| 空字串 `''` | 什麼都不畫 |
| 非空字串 | 文字 |
| 數字，包含 `0` 和 `NaN` | 文字 `0`、`NaN` |
| 陣列 | 逐項處理，`['甲', 1, null, '乙']` 畫出「甲1乙」 |
| element | 繼續往下畫 |
| 一般物件、`Date` | 丟錯：`Objects are not valid as a React child` |

再加上第 02 章的短路求值：`a && b` 在 `a` 是 falsy 時回傳 **`a` 本身**，不是 `false`。兩件事合起來：

```tsx
<div>{tasks.length && <ul>{rows}</ul>}</div>
```

`tasks.length` 是 `0` 時，整個運算式的值是 `0`，等於寫了 `<div>{0}</div>`。數字要畫，於是 `0` 就出現在畫面上。布林值不畫，`&&` 這個慣用法才行得通，所以要讓左邊確實算出布林值：

```tsx
<div>{tasks.length > 0 && <ul>{rows}</ul>}</div>
```

同樣的事也會發生在 `NaN`：`{Number(input) && <Result />}` 遇到無法解析的輸入，畫面會出現 `NaN`。字串則不會出事，`task.dueDate` 是 `null` 或 `''` 都什麼也不畫。但本書一律把條件寫成明確的比較，例如 `task.dueDate !== null`，讀的人不用先想型別才知道安不安全。

條件渲染的其他寫法各有適合的形狀。只有兩種畫面時用三元運算子，它是運算式，可以留在 JSX 裡：

```tsx
<span>{isDone ? '已完成' : '進行中'}</span>
```

三種以上就不要再疊了。第 05 章的 `RemoteData<Task[]>` 有三個狀態，寫成巢狀三元會變成這樣：

```tsx
{state.status === 'loading' ? <p>載入中…</p> : state.status === 'error' ? <p>載入失敗</p> : <TaskList tasks={state.data} />}
```

型別上沒有錯，但多一個狀態就要在一行裡找插入點，review 時看不出哪個分支對應哪個條件。整個 component 的輸出都由狀態決定時，提前 return（guard clause）好讀得多，每個分支獨立，TypeScript 的 narrowing 也會一路生效，走到最後一行時 `state` 已經收窄成成功的那一種：

```tsx
import { TaskList } from './TaskList';
import type { RemoteData, Task } from './types';

interface TaskListPanelProps {
  state: RemoteData<Task[]>;
}

export const TaskListPanel = ({ state }: TaskListPanelProps): React.JSX.Element => {
  if (state.status === 'loading') {
    return <p role="status">載入中…</p>;
  }

  if (state.status === 'error') {
    return <p role="alert">{state.message}</p>;
  }

  return <TaskList tasks={state.data} />;
};
```

現在還沒有網路請求，這個 `state` 第 11 章才會真的變動，但形狀已經可以先定下來。

條件樣式是同一回事的另一面，`className={isDone ? 'task-item task-item-done' : 'task-item'}` 就是一個三元。條件一多這種字串很快失控，第 16 章的 `cn()` 會處理，寫法是 `cn('task-item', isDone && 'task-item-done')`，利用的同樣是 `&&` 短路，只是 falsy 值由 `cn` 濾掉。

最後要記住，條件渲染是把東西從樹上拿掉。`{isOpen && <TaskForm />}` 變成 `false` 時，`TaskForm` 連同它記著的內容一起消失，再次出現是全新的一個。第 09 章會解釋為什麼，這也是它和用 CSS 隱藏的差別。

## 列表是一個 element 陣列，React 要你替每項取名

child 可以是陣列，`map` 回傳陣列，於是列表不需要任何新語法：

```tsx
<ul>
  {tasks.map((task) => (
    <li>{task.title}</li>
  ))}
</ul>
```

畫面正確，console 卻出現 `Each child in a list should have a unique "key" prop`。手寫兩個 `<li>` 從來不會有這個警告，差別在編譯結果。手寫多個 children 時編譯器用的是 `jsxs`，那個結尾的 s 代表 static：

```tsx
jsxs('ul', { children: [jsx('li', { children: '甲' }), jsx('li', { children: '乙' })] });
```

手寫的 children 位置固定，第一個永遠是第一個。`map` 的結果放在大括號裡，編譯器只看到一個運算式，用的是 `jsx`，React 知道這個陣列是執行時才算出來的，可能下次多一項、少一項、換順序。下次 render 時它得知道「這個 `li` 是上次的哪一個」，光看位置猜不出來，所以要你用 `key` 替每一項取一個名字。

詳細的比對過程和用錯 key 造成的 bug 是第 09 章的主題，這裡先把寫對的規則立好，完整的理由留到那一章：

- `key` 的值用資料本身的 ID：`task.id`。陣列 index 和 `Math.random()` 雖然能讓警告消失，但都有問題，第 09 章會實際演出後果。
- `key` 只要在同一個陣列內唯一。兩個不同的清單都用 `task.id` 沒有問題；同一個陣列內重複時，console 會印 `Encountered two children with the same key`。
- `key` 寫在 **`map` 直接回傳的那個 element** 上。

最後這條是抽 component 後最常踩的。下面的寫法把 key 放在 `TaskItem` 內部的 `<li>`：

```tsx
const TaskItem = ({ task }: TaskItemProps): React.JSX.Element => <li key={task.id}>{task.title}</li>;

<ul>
  {tasks.map((task) => (
    <TaskItem task={task} />
  ))}
</ul>
```

警告照樣出現。React 比對的是 `ul` 底下那個陣列的項目，每項都是沒有 key 的 `TaskItem` element；裡面那個 `<li>` 的 key 在另一層，幫不上忙。正解是把 key 寫在 `<TaskItem key={task.id} task={task} />`。

如果每一項要產出多個節點，就輪到 Fragment 的完整寫法，縮寫 `<>` 放不了 key：

```tsx
<dl>
  {tasks.map((task) => (
    <Fragment key={task.id}>
      <dt>{task.title}</dt>
      <dd>{task.status}</dd>
    </Fragment>
  ))}
</dl>
```

`Fragment` 從 `react` import。

還有一個 `map` 的常見失誤與 JSX 無關，症狀卻是畫面一片空白：箭頭函式用大括號時要自己寫 `return`。

```tsx
{tasks.map((task) => {
  <TaskItem key={task.id} task={task} />;
})}
```

這個回呼函式回傳 `undefined`，陣列裡全是 `undefined`，React 什麼也不畫，也不會有 runtime 警告。TypeScript 會擋下來，訊息是 `Type 'void[]' is not assignable to type 'ReactNode'`。用小括號的隱式回傳就沒有這個問題。

## Task Tracker 的第一個靜態畫面

規則齊了，可以把開場的 HTML 稿做對。現在所有檔案都平放在 `src/` 下，第 24 章才會重整結構。沒有 state，沒有 API，資料是一份寫死的陣列。這是刻意的順序：先確定畫面怎麼從資料算出來，再處理資料怎麼改變。

`src/sampleTasks.ts` 放三筆假資料，涵蓋三種狀態，也涵蓋有無到期日，這樣條件分支都看得到：

```ts
import type { Task } from './types';

export const SAMPLE_TASKS: Task[] = [
  {
    id: 't-1',
    title: '設定 CI',
    status: 'done',
    assigneeId: 'u-1',
    dueDate: '2026-11-03',
    createdAt: '2026-10-28T09:00:00Z',
  },
  {
    id: 't-2',
    title: '補登入頁測試',
    status: 'doing',
    assigneeId: null,
    dueDate: null,
    createdAt: '2026-10-29T02:30:00Z',
  },
  {
    id: 't-3',
    title: '整理 API 錯誤格式',
    status: 'todo',
    assigneeId: 'u-2',
    dueDate: '2026-11-10',
    createdAt: '2026-10-30T07:15:00Z',
  },
];
```

`src/TaskItem.tsx` 負責一筆任務。`STATUS_LABELS` 放在同一個檔案，因為它只為這個畫面存在；用 `Record<TaskStatus, string>` 的好處就是前面說的，少一個狀態會編譯失敗。`className` 目前只是掛鉤，樣式到第 16 章才上。

```tsx
import type { Task, TaskStatus } from './types';

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: '待處理',
  doing: '進行中',
  done: '已完成',
};

interface TaskItemProps {
  task: Task;
}

export const TaskItem = ({ task }: TaskItemProps): React.JSX.Element => {
  const isDone = task.status === 'done';

  return (
    <li className={isDone ? 'task-item task-item-done' : 'task-item'}>
      <input
        type="checkbox"
        aria-label={`完成 ${task.title}`}
        checked={isDone}
        readOnly
      />
      <span>{task.title}</span>
      <span>{STATUS_LABELS[task.status]}</span>
      {task.dueDate !== null && <time dateTime={task.dueDate}>到期 {task.dueDate}</time>}
    </li>
  );
};
```

那個 `readOnly` 要解釋一下。少了它，console 會警告 `You provided a checked prop to a form field without an onChange handler`。React 的 `checked` 把勾選狀態交由資料決定，沒有 `onChange` 就表示使用者怎麼點都改不了，這多半是忘了接事件，所以它提醒你。靜態畫面確實還不打算接，`readOnly` 就是明確告訴 React 這是故意的。第 07 章接上 `onToggle` 時就會換掉它。

`src/TaskList.tsx` 把任務排起來，順便解決開場的 `0`。這裡選提前 return，因為空清單和有資料是兩種完全不同的畫面，沒有共用的外層。key 放在 `map` 直接回傳的 `TaskItem` 上：

```tsx
import { TaskItem } from './TaskItem';
import type { Task } from './types';

interface TaskListProps {
  tasks: Task[];
}

export const TaskList = ({ tasks }: TaskListProps): React.JSX.Element => {
  if (tasks.length === 0) {
    return <p className="task-list-empty">目前沒有任務。</p>;
  }

  return (
    <ul className="task-list">
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} />
      ))}
    </ul>
  );
};
```

`src/App.tsx` 把第 00 章的標題和清單組起來。Vite 模板的 `main.tsx` 是 default import（`import App from './App.tsx'`），這裡改成 named export 後要同步改成 `import { App } from './App.tsx'`。本書偏好 named export，檔案改名或重新匯入時名字不會各叫各的，IDE 的重新命名也能追到所有使用處。

```tsx
import { SAMPLE_TASKS } from './sampleTasks';
import { TaskList } from './TaskList';

export const App = (): React.JSX.Element => (
  <main>
    <h1>Task Tracker</h1>
    <TaskList tasks={SAMPLE_TASKS} />
  </main>
);
```

`npm run dev` 打開，畫面上有標題和三筆任務，第一筆勾選，第二筆沒有到期日，console 乾淨。把 `SAMPLE_TASKS` 暫時換成 `[]`，畫面顯示「目前沒有任務。」，沒有 `0`。這個畫面還不會動，點 checkbox 也沒反應，這是接下來兩章的事。

和第 01 章的原生版對照一下：那裡你要建節點、塞文字、掛到父層，資料變了還要自己找到對應的節點去改。這裡每個函式只回答「給我這份資料，畫面應該長怎樣」，一行 DOM 操作都沒寫。

## 常見誤解

**「`onClick={removeTask(task.id)}` 是點擊時才執行。」** 大括號裡的運算式在建立 element 時就會計算，這是函式呼叫的引數，和 `Math.max(f())` 裡的 `f()` 一樣當場執行。這行的意思是每次 render 都刪一次任務，再把回傳值 `undefined` 當成事件處理函式。TypeScript 會擋下來（`void` 不能當 event handler），正解是傳一個函式：`onClick={() => removeTask(task.id)}`。事件的完整寫法在第 07、08 章。

**「`TaskItem({ task })` 和 `<TaskItem task={task} />` 一樣，反正都是函式。」** 兩者在這章的靜態畫面可能畫出一樣的東西，時機和身分卻不同。直接呼叫是在父層的函式裡當場執行，React 只看到結果的 `<li>`，樹上沒有 `TaskItem` 這一層，它內部的 hook（第 08 章起會用到）也會被算成父層的。React 官方文件明文要求不要直接呼叫 component 函式。這件事的後果要等第 09 章和第 11 章才看得完整，現在先養成習慣。

**「想把物件印到畫面，寫 `{task}` 就好。」** 一般物件和 `Date` 會丟 `Objects are not valid as a React child`，整個 component 炸掉，錯誤訊息會列出物件的 key。React 不知道你要哪個欄位，也不會替物件挑一種文字格式。除錯時要看整個物件，用 `<pre>{JSON.stringify(task, null, 2)}</pre>`。`dueDate` 在本書的型別裡是字串所以可以直接放，等它被轉成 `Date` 才會踩到這個錯，第 40 章會處理日期顯示。

**「修掉 console 裡的 key 警告，就代表全部都修好了。」** 這個警告不是每處都印。在目前的 React 19 開發版，同一種父層只會警告一次：頁面上第一個漏 key 的 `<ul>` 印過之後，第二個漏 key 的 `<ul>` 就不再出聲。修完一個重新整理，下一個才會冒出來，所以看到一則要順手搜尋同類的 `map`。

## 同事會來問你的問題

**「為什麼不用 Razor 或 Vue 那種模板？JSX 把標記和程式混在一起不是很亂嗎？」** 混的是語法，不是職責。模板語言要另外發明條件、迴圈和作用域規則，編輯器和型別檢查也要特別支援才看得懂。JSX 編譯後就是函式呼叫，語言本身的 `map`、`if`、變數和型別都能用，TypeScript 也能把每個屬性和 props 檢查到。代價是你得搞懂那些和 HTML 的差異，也就是本章在處理的事。至於職責是否混亂，取決於你把什麼放進 component，資料存取和業務規則本來就不該放進去。

**「`{count && <Badge />}` 這行 review 為什麼被打回來？字串的時候不是沒事嗎？」** `&&` 回傳的是左邊的值本身，React 又會把數字 `0` 和 `NaN` 當文字畫出來，所以只要左邊可能是數字，就有機會在畫面上多出一個 `0`。字串確實沒事，因為空字串什麼也不畫。但變數的型別日後可能改變，而且 reviewer 要追到型別才能判斷安全與否。寫成 `count > 0 &&` 不必追。

**「component 的回傳型別要寫 `React.JSX.Element` 還是 `ReactNode`？」** 預設寫 `React.JSX.Element`，它最窄，能擋下 `return;` 和回傳忘記的錯誤。會回傳 `null` 時用 `React.JSX.Element | null`。真的會回傳字串或陣列時才用 `React.ReactNode`，目前的 TypeScript 和 `@types/react` 接受這種 component 放在 JSX 裡。舊程式碼常見的 `JSX.Element` 在 `@types/react` 19 會報 `Cannot find namespace 'JSX'`，因為全域的 `JSX` namespace 已經移除；`React.JSX.Element` 這樣寫也不用 import React，它在型別位置可以直接使用。

**「key 的警告又不影響畫面，可以先不管嗎？」** 靜態資料當下確實看不出問題。一旦清單會重排或刪除，React 就只能照位置比對，輸入框內容和 focus 這類留在 DOM 或 component 裡的東西會跟錯人。出事時的症狀是「刪了第二筆，第三筆的編輯內容跑到第二筆上」，離這個警告很遠，很難聯想回來。第 09 章會實際重現這個 bug。補一個 `key={task.id}` 的成本只有一行，沒有理由留著。

**「這個 400 行的 component 要不要拆？拆了會不會比較慢？」** 先看它是不是有多塊能各自命名、各自因不同理由改動的東西，是就拆，這是可讀性的決定。效能不是這一步要擔心的事，多一層 component 就是多一次函式呼叫。真正影響效能的是哪些 component 重新 render，那要到第 09 章和第 14 章才有判斷工具，而且第 28 章會教你先量再改。

## 本章小結

JSX 是函式呼叫的語法糖，算出來的是描述畫面的 element 物件，`type` 是字串時對應 DOM 節點，是函式時由 React 決定何時呼叫。`className`、自閉合、單一根和大括號只收運算式，都是這個編譯結果的直接後果。條件渲染和列表沒有專屬語法，靠的是 React 對各種 child 值的處理規則，這也解釋了 `&&` 留下的 `0` 和陣列為什麼需要 `key`。現在 `TaskList` 和 `TaskItem` 畫得出靜態清單，但 `task` 這個屬性我們只是拿來用，還沒問過資料在 component 之間到底怎麼流動、能不能改、checkbox 的事件要怎麼傳回去，這是第 07 章要回答的問題。

## 連結

- 上一章：[[react-05-typescript-modeling]]
- 下一章：[[react-07-props]]
- 相關章節：[[react-01-browser-and-dom]]、[[react-02-javascript-for-react]]、[[react-09-rendering]]、[[react-16-tailwind]]、[[react-37-frontend-security]]
- 相關頁面：[[dom]]、[[typescript]]、[[javascript-typescript-react-foundations]]
