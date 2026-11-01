---
type: concept
domain: tech
tags: [react, useref, ref, dom-ref, ref-callback, useimperativehandle, typescript]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
  - raw/Web Framework/React/DOM 節點觀念.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 12 章：Ref — 要記住，但不該觸發 render 的東西

## 游標跳到別的看板，提示提早消失

有人開始拿 Task Tracker 連續建任務，回報兩個小問題：按下「新增」之後，游標沒有回到輸入框，每打一筆都要再點一次；「已新增」的提示掛在畫面上不會消失。需求很小，你各寫了幾行。

游標的部分，`TaskForm` 送出後找到輸入框再 focus：

```tsx
onAdd(title);
setDraft('');
document.querySelector<HTMLInputElement>('form input')?.focus();
```

單一看板時完全正常。後來同一頁放了兩個看板，在右邊新增，游標跳到左邊的輸入框，因為 `querySelector` 回傳的是整份文件裡第一個符合的節點。

提示的部分，顯示後設一個 3 秒的計時器，再次新增時取消舊的、重新計時：

```tsx
const [notice, setNotice] = useState<string | null>(null);
let noticeTimer: ReturnType<typeof setTimeout> | undefined;

const showNotice = (title: string): void => {
  clearTimeout(noticeTimer);
  setNotice(`已新增「${title}」`);
  noticeTimer = setTimeout(() => {
    setNotice(null);
  }, 3000);
};
```

第 0 秒新增 A，第 2 秒新增 B，B 的提示只停留 1 秒就消失了。`clearTimeout` 明明寫在那裡，第一個計時器卻照樣觸發。

這兩個問題要的東西其實一樣：這個 component 實例的輸入框節點、這個 component 實例上次的計時器 id。它們都要跨 render 記住，改變時畫面都不用動。本章回答：這種值該放哪裡，以及為什麼 React 對它設下那麼多限制。

## 現有的選項各缺一塊

第 08 章列過 state 的三個條件：活得比單次函式呼叫久、改了會讓 React 重算畫面、每個實例各有一份。這裡的需求只要第一和第三條，第二條反而是多餘的。用這個標準看手上的工具，開場的 bug 就有了解釋。

區域變數活不過一次呼叫。按下 A 時，執行的是第 1 次 render 建立的 `showNotice`，id 存進第 1 次 render 的 `noticeTimer`。`setNotice` 引發第 2 次 render，`let` 又跑一次，產生一個全新的、值為 `undefined` 的變數，新的 `showNotice` 抓住的是它。按下 B 時 `clearTimeout(undefined)` 什麼也沒做，A 的計時器還活著。

搬到模組層級，值活下來了，但所有實例共用同一個變數。左邊看板顯示提示後，右邊看板新增，會把左邊的計時器取消掉，左邊的提示從此再也不會消失。

放進 `useState` 的話，單次點擊會正常，代價有兩個。id 不在畫面上，存它卻要排一次 render；如果同一個事件裡剛好有別的 setState，第 08 章的 batching 會把它們合併，否則就是純粹多一次。更麻煩的是 state 是快照：批次匯入時同一個 handler 連呼叫三次 `showNotice`，三次讀到的都是同一個舊 id，於是三個計時器全部活著，而 state 只記得最後一個。計時器 id 需要的是「寫進去，下一行就讀得到」，快照語意在這裡幫倒忙。

## useRef 給你一個 React 保管的盒子

`useRef` 回傳一個只有 `current` 屬性的物件：

```tsx
const noticeTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

const showNotice = (title: string): void => {
  clearTimeout(noticeTimerRef.current);
  setNotice(`已新增「${title}」`);
  noticeTimerRef.current = setTimeout(() => {
    setNotice(null);
  }, 3000);
};
```

它的合約有三條。同一個 component 實例的每一次 render，拿到的都是同一個物件。改 `current` 不會排 render。每個實例各有一個盒子，remount 之後是新盒子。官方文件給的直覺很好記：可以把它想成 `useState({ current: initialValue })` 只取第一個值、永遠不呼叫 setter，然後自己去改物件的屬性。第 08 章禁止直接改 state 物件，因為 React 靠參考比較判斷是否要更新；ref 正好反過來利用這點，參考永遠不變，所以永遠不會引發 render。

現在每次 render 建立的 `showNotice` 雖然是不同的函式，closure 裡抓到的卻是同一個盒子。第 1 次 render 的 handler 寫進去，第 2 次 render 的 handler 讀得到；批次匯入連呼叫三次，第二次就讀到第一次剛寫的 id，最後只留下一個計時器。

寫過 C# 的話，ref 很像類別上的 private field：`private CancellationTokenSource? _cts;` 跨方法呼叫保留，改了沒有人會收到通知。舊式 class component 也確實用 instance field 做這件事（第 42 章）。類比破在建構的時機：C# 方法體可以放心改 field，component 函式本體卻可能被 React 重跑或丟棄，所以本章後面有一條 field 沒有的限制。

型別上有兩點要留意。計時器 id 寫 `ReturnType<typeof setTimeout>`，因為專案載入 Node 型別時它是 `NodeJS.Timeout`，只有 DOM 型別時是 `number`，這樣寫兩邊都成立。`clearTimeout(undefined)` 是合法的空操作，起始值用 `undefined` 就不必多寫一層判斷。另外 React 19 的 `useRef` 一定要給參數，`useRef<number>()` 會編譯失敗。

該用哪一個，問的問題和第 08 章相同：

| 問題 | `useState` | `useRef` |
| --- | --- | --- |
| 改了要重算畫面嗎 | 會重算 | 不會 |
| 跨 render 保留嗎 | 會 | 會 |
| 寫完同一個 handler 內讀得到新值嗎 | 讀不到，要等下次 render | 讀得到 |
| 典型內容 | 任務清單、輸入值、篩選條件 | 計時器 id、DOM 節點、第三方物件、拖曳起點 |

拖曳是個好例子：`pointerdown` 記下起點，`pointermove` 每次事件都要讀它，`pointerup` 清掉。起點本身不顯示，用 `dragRef.current = { isDragging: true, startX }` 就夠了。第 32 章的 Canvas 也會把平移與縮放的 `viewRef` 放在 ref 裡，因為畫布不走 React 的 render。

### 需要最新值時，ref 也是逃出快照的門

第 08 章說過舊 closure 裡的 state 永遠是舊的，而這多半正是你要的。偶爾需求相反：按下「稍後儲存」，一秒後要存的是當下輸入框的內容，不是按下時的內容。

```tsx
export const DraftSaveLater = ({ saveDraft }: { saveDraft: (draft: string) => void }): React.JSX.Element => {
  const [draft, setDraft] = useState('');
  const latestDraftRef = useRef(draft);

  useEffect(() => {
    latestDraftRef.current = draft;
  }, [draft]);

  const handleSaveLater = (): void => {
    setTimeout(() => {
      saveDraft(latestDraftRef.current);
    }, 1000);
  };

  return (
    <>
      <input aria-label="草稿" value={draft} onChange={(event) => setDraft(event.target.value)} />
      <button onClick={handleSaveLater}>稍後儲存</button>
    </>
  );
};
```

打「補」、按按鈕、接著打成「補測試」，一秒後存到的是「補測試」；如果 `setTimeout` 裡直接讀 `draft`，存到的會是「補」。同步 ref 的動作放在 Effect，下一節會說明為什麼不能直接寫在函式本體。如果讀最新值的地方在 Effect 裡，先用第 11 章的 `useEffectEvent`，它就是為那個情境設計的。

## 計時器不一定要進 ref

上一章結尾問計時器 id 該放哪，答案要看計時器從哪裡開始。不少舊筆記和範例會這樣寫自動儲存：

```tsx
const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

useEffect(() => {
  clearTimeout(timerRef.current);
  timerRef.current = setTimeout(() => {
    saveToServer(content);
  }, 1000);
}, [content, saveToServer]);
```

內容變動時的 debounce 是對的，但沒有 cleanup。使用者打完字馬上離開頁面，component 已經卸載，一秒後 `saveToServer` 還是會送出去。ref 在這裡也是多餘的，因為 Effect 的 cleanup closure 本來就抓得到同一次 setup 建立的 id：

```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    saveToServer(content);
  }, 1000);
  return () => {
    clearTimeout(timer);
  };
}, [content, saveToServer]);
```

內容一變，舊計時器由 cleanup 取消；卸載時同樣取消。第 11 章的 `AutoRefreshBadge` 也屬於這一類，它的 interval id 留在 Effect 內就好，不需要 ref。

判斷方式：計時器的建立與取消都在同一個 Effect，用 closure 變數。建立在 handler、取消在另一次 handler 呼叫，兩者之間隔著 render，才需要 ref。開場的提示屬於後者。你也許會想把它改成 Effect 依賴 `lastAddedTitle`，可是連續新增兩筆同名任務時值沒有變，Effect 不會重跑，計時也不會重來，第二則提示只剩下第一則的剩餘時間。

## render 期間不要碰 current

有了一個能跨 render 保存、改了又不引發更新的盒子，很自然會想拿它來數 render 次數：

```tsx
export const RenderCounter = (): React.JSX.Element => {
  const renderCountRef = useRef(0);
  renderCountRef.current += 1;
  return <p>第 {renderCountRef.current} 次 render</p>;
};
```

放在 `<StrictMode>` 底下，第一次出現在畫面上就寫著「第 2 次 render」，拿掉 StrictMode 才是「第 1 次」。第 09 章說過 component 必須是 pure，StrictMode 重跑一次 render 就是在抓這種事：同樣的 props 和 state 算出了不同的畫面。問題不在這個計數器不準，而是 render 的結果依賴了一個 React 不追蹤的輸入。

這會造成兩種實際症狀。第一種是畫面和資料脫節：

```tsx
export const SelectedCountInRef = (): React.JSX.Element => {
  const selectedCountRef = useRef(0);
  const [filter, setFilter] = useState('all');

  return (
    <>
      <button
        onClick={() => {
          selectedCountRef.current += 1;
        }}
      >
        選取
      </button>
      <button onClick={() => setFilter('done')}>只看已完成</button>
      <p>
        {filter}：已選 {selectedCountRef.current} 筆
      </p>
    </>
  );
};
```

按兩次「選取」，畫面維持 `all：已選 0 筆`，看起來像按鈕壞了。按一下毫不相關的「只看已完成」，數字突然跳成 `done：已選 2 筆`。這種 bug 很難查，因為現象出現在無關的操作之後。要顯示的值放 state；如果內部確實需要 ref 來計數，就在 handler 裡另外呼叫 setter 把結果送上畫面。

第二種症狀要到第 30 章才會完整看到：並行渲染下 React 可以中途放棄一次 render，放棄的 render 寫進 ref 的值卻不會還原。React Compiler（第 14 章）也假設 render 是 pure 才敢做快取。所以 `eslint-plugin-react-hooks` 的 recommended 設定裡有 `react-hooks/refs` 規則，上面的 `RenderCounter` 會得到 `Cannot access refs during render`。讀和寫都算，讀的問題是它讓 render 結果依賴可變的值；要讀寫就放在 handler 或 Effect。這也解釋了上一節的 `latestDraftRef` 為什麼在 Effect 裡同步。

規則有一個正式的例外，初始化代價高的物件：

```tsx
const indexRef = useRef<Map<string, Task> | null>(null);
if (indexRef.current === null) {
  indexRef.current = createTaskIndex();
}
```

`useRef(createTaskIndex())` 看起來只建一次，其實參數在每次 render 都會求值，只是結果除了第一次之外都被丟掉，索引有多貴就白算多少次。上面的寫法只在第一次建立，重跑也得到等價結果，所以不破壞 purity，lint 規則認得這個形式，不會報錯。

## DOM ref：拿到這個實例的節點

把 ref 物件交給 JSX 元素的 `ref` 屬性，React 會在 commit 時把真實節點放進 `current`，節點移除時放回 `null`。這正好解決開場的第一個問題，`querySelector` 查的是整份文件，ref 拿到的是這個實例自己 render 出來的節點：

```tsx
const inputRef = useRef<HTMLInputElement>(null);
// ...
<input ref={inputRef} value={draft} onChange={(event) => setDraft(event.target.value)} />
```

`current` 的型別是 `HTMLInputElement | null`，所以呼叫時要寫 `inputRef.current?.focus()`。`null` 不是型別上的囉嗦，它描述的是真實的時間軸：

```text
render         current 是 null，節點還不存在
commit         React 更新 DOM，把節點放進 current
layout Effect  讀得到節點，瀏覽器尚未繪製
paint
Effect         讀得到節點
---- 卸載 ----
Effect cleanup current 已經是 null
```

這條時間軸幾乎能解釋所有「ref 怎麼是 null」的問題。父層 Effect 讀子層的節點沒問題，整棵樹的 ref 在 Effect 之前都放好了。卸載時 Effect cleanup 讀 `current` 已經是 `null`，要用節點就在 setup 時先存進區域變數，下面的 `DueDatePicker` 就是這樣做。

最容易踩的是點擊後才出現的節點。行內編輯：點標題切換成輸入框，並把游標放進去：

```tsx
export const TitleEditFocusTooEarly = ({ title }: { title: string }): React.JSX.Element => {
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const startEditing = (): void => {
    setIsEditing(true);
    inputRef.current?.focus();
  };

  return isEditing ? (
    <input ref={inputRef} defaultValue={title} aria-label="標題" />
  ) : (
    <button onClick={startEditing}>{title}</button>
  );
};
```

輸入框出現了，游標卻不在裡面，也沒有任何錯誤。`setIsEditing(true)` 只是排了一次 render（第 08 章），下一行執行時輸入框還不存在，`current` 是 `null`，而 `?.` 安靜地跳過了呼叫。`?.` 通過了型別檢查，同時也把時機錯誤藏起來。單純想在 mount 時 focus，`<input autoFocus />` 就夠了。需要多做一點，例如 focus 之外還要全選文字，下一節的 ref callback 是對的工具。

### 只動 React 不管的東西

有了節點，很容易順手把別的事也做了。適合用 DOM ref 的是 React 沒有宣告式說法的操作：`focus()`、`select()`、`scrollIntoView()`、量尺寸、`video.play()`，以及把節點交給第三方函式庫。寫入 React 正在管理的東西則會出事：

```tsx
const clearDraft = (): void => {
  if (inputRef.current !== null) {
    inputRef.current.value = '';
  }
};
```

如果這個 input 是受控的（`value={draft}`），輸入框看起來清空了，但 `draft` 還是原來的內容。使用者按送出，送出去的是他以為已經清掉的文字。第 08 章說過受控 input 的真實資料在 state，清空就該呼叫 `setDraft('')`。

第三方函式庫則是把一塊 DOM 整個交出去，React 只負責提供一個空節點，setup 掛上，cleanup 拆掉：

```tsx
export const DueDatePicker = ({
  mountDatePicker,
}: {
  mountDatePicker: (node: HTMLElement) => DatePickerWidget;
}): React.JSX.Element => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = containerRef.current;
    if (node === null) return;
    const picker = mountDatePicker(node);
    return () => {
      picker.destroy();
    };
  }, [mountDatePicker]);

  return <div ref={containerRef} />;
};
```

`mountDatePicker` 代表函式庫的進入點，`DatePickerWidget` 是只有 `destroy()` 的介面。這個 `<div>` 不放任何 React children，裡面的節點歸函式庫管，兩邊才不會互相覆寫。

## ref callback：節點出現與消失的那一刻

`ref` 屬性也可以接函式。React 在節點 attach 時呼叫它，傳入節點。行內編輯的 focus 問題這樣解最乾淨，不必等 render 也不必多一個 Effect：

```tsx
const focusAndSelect = (node: HTMLInputElement | null): void => {
  node?.focus();
  node?.select();
};

// JSX 裡
<input ref={focusAndSelect} defaultValue={title} aria-label="標題" />
```

`focusAndSelect` 定義在 component 外面是刻意的。React 用參考比較 `ref` 屬性，函式變了就先拆舊的、再接新的。寫成 inline，每次 render 都是新函式，attach 每次都重跑：

```tsx
<input
  ref={(node) => {
    node?.focus();
  }}
  defaultValue={title}
  aria-label="標題"
/>
```

症狀是搶 focus。使用者已經 Tab 到旁邊的「儲存」按鈕，這時任何原因引發一次 render，例如背景更新清單，游標就被拉回輸入框。只有副作用可以安全重跑時才適合 inline。

React 19 讓 ref callback 可以回傳 cleanup。回傳 cleanup 時，卸載呼叫的是 cleanup，不會再用 `null` 呼叫一次；沒回傳時維持舊行為，卸載時傳入 `null`。所以 inline callback 在一次重新 render 時的順序是舊 cleanup、新 attach。StrictMode 的開發環境 mount 會多跑一輪：attach、cleanup、attach，道理和第 11 章的 Effect 雙重執行相同。

這裡有個型別陷阱：`ref={(el) => (captured = el)}` 會得到 TS2322，因為箭頭函式隱式回傳了節點，而 callback 只能回傳 `void` 或 cleanup。改成區塊 `{ captured = el; }` 就好。舊專案升級時常見這個錯，React 19 有對應的 codemod（第 42 章）。

ref callback 真正不可取代的場合是數量不固定的節點。新增任務後要捲到那一筆，每個 `<li>` 都需要 ref，但第 11 章的 Hook 規則不允許在迴圈裡呼叫 `useRef`。解法是一個 ref 裝一個 `Map`，由 callback 維護：

```tsx
export const ScrollingTaskList = (): React.JSX.Element => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const itemNodesRef = useRef(new Map<string, HTMLLIElement>());

  const handleAdd = (): void => {
    const task = createTask(`任務 ${tasks.length + 1}`);
    flushSync(() => {
      setTasks((prev) => [...prev, task]);
    });
    itemNodesRef.current.get(task.id)?.scrollIntoView();
  };

  return (
    <>
      <button onClick={handleAdd}>新增</button>
      <ul>
        {tasks.map((task) => (
          <li
            key={task.id}
            ref={(node) => {
              if (node === null) return;
              itemNodesRef.current.set(task.id, node);
              return () => {
                itemNodesRef.current.delete(task.id);
              };
            }}
          >
            {task.title}
          </li>
        ))}
      </ul>
    </>
  );
};
```

這裡 inline callback 重跑無害，只是刪掉再放回同一筆。`new Map()` 每次 render 都會求值，但它幾乎沒有成本，不值得用前面的 lazy 寫法。

`flushSync`（來自 `react-dom`）對應前一節的時機問題：拿掉它，下一行的 `get` 回傳 `undefined`，節點還沒 commit。它強制 React 在 callback 結束前同步更新 DOM，所以只留給「下一行就要讀到新 DOM」的場合，到處用等於關掉 batching。

## 把 ref 傳進自己寫的 component

`TaskForm` 自己持有 input，所以上面都很順。一旦父層需要子 component 裡的節點，就要把 ref 傳下去。React 19 起 `ref` 就是一般 prop：

```tsx
interface TextInputProps {
  label: string;
  ref?: Ref<HTMLInputElement>;
}

export const TextInput = ({ label, ref }: TextInputProps): React.JSX.Element => (
  <label>
    {label}
    <input ref={ref} />
  </label>
);
```

`Ref<T>` 用 `import type { Ref } from 'react'` 取得，同時涵蓋 ref 物件和 callback，所以呼叫端兩種都能傳。`<TextInput ref={...} />` 傳給沒宣告 `ref` 的 component，TypeScript 會擋下來；若繞過型別，React 只把它當成沒人讀的 prop，父層的 `current` 一直是 `null`。包裝原生元素時，用 `ComponentPropsWithRef<'input'>`（第 07 章 `ComponentProps` 的含 ref 版本）繼承全部屬性，`{...rest}` 會把 `ref` 一起帶過去。

既有專案裡你會看到另一種寫法。React 18 以前 `ref` 和 `key` 一樣是保留字，不會出現在 props，要穿透就得包一層：

```tsx
// React 18 以前的寫法，新程式碼不要用
const TextInputLegacy = forwardRef<HTMLInputElement, { label: string }>(({ label }, ref) => (
  <input ref={ref} aria-label={label} />
));
```

注意泛型順序是 ref 在前、props 在後，參數也分成兩個。`forwardRef` 在 19 仍可使用，舊碼不會壞，遷移放在第 42 章。

## useImperativeHandle：只交出該交的操作

Task Tracker 的空狀態要放一顆「建立第一筆任務」按鈕，按下去讓表單的輸入框取得 focus。按鈕在 `TasksPage`，輸入框在 `TaskForm`。最直接的做法是 `TaskForm` 把 input 的 ref 交出去，但這樣父層拿到的是整個 DOM 節點，它可以呼叫 `focus()`，也可以寫 `value`，而前面才看過寫 `value` 會讓 `draft` 和畫面分家。

先看另一個直覺方案，用 prop 表達：

```tsx
export const FocusFlagInput = ({ shouldFocus }: { shouldFocus: boolean }): React.JSX.Element => {
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (shouldFocus) {
      inputRef.current?.focus();
    }
  }, [shouldFocus]);
  return <input ref={inputRef} aria-label="新任務" />;
};
```

第一次有效。使用者點走之後再按一次按鈕，`shouldFocus` 還是 `true`，依賴沒變，Effect 不跑，什麼事也沒發生。要修就得在 focus 後通知父層把旗標設回 `false`，多一個 prop、多一次 render，只為了描述一個動作。問題出在 focus 是事件，prop 描述的卻是狀態。反過來，對話框開著或關著是持續的狀態，就該用 `isOpen` prop，不該做成 `open()` 方法。判斷方式是：這件事能不能用「現在長什麼樣」來描述？能就用 props。

`useImperativeHandle` 處理剩下的少數情況，它讓 component 決定父層的 ref 拿到什麼：

```tsx
import { useImperativeHandle, useRef, useState } from 'react';
import type { Ref } from 'react';

export interface TaskFormHandle {
  focus: () => void;
  clear: () => void;
}

interface TaskFormProps {
  onAdd: (title: string) => void;
  ref?: Ref<TaskFormHandle>;
}

export const TaskForm = ({ onAdd, ref }: TaskFormProps): React.JSX.Element => {
  const [draft, setDraft] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const title = draft.trim();

  useImperativeHandle(
    ref,
    () => ({
      focus: () => {
        inputRef.current?.focus();
      },
      clear: () => {
        setDraft('');
      },
    }),
    [],
  );

  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (title === '') return;
    onAdd(title);
    setDraft('');
    inputRef.current?.focus();
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        新任務
        <input ref={inputRef} value={draft} onChange={(event) => setDraft(event.target.value)} />
      </label>
      <button type="submit" disabled={title === ''}>
        新增
      </button>
    </form>
  );
};
```

父層的 `formRef.current` 是一個只有 `focus` 和 `clear` 的物件，碰不到 DOM。`clear` 走 `setDraft`，state 和畫面維持一致。後端讀者可以把 `TaskFormHandle` 想成控制器依賴的 interface：呼叫端只看得到合約，實作藏在後面，之後把 `<input>` 換成 antd 的元件也不影響父層。類比破在保證的強度，DI 容器解析失敗會在啟動或請求時報錯，這裡的 `current` 在子層未 mount 或已卸載時是 `null`，呼叫端要自己用 `?.` 面對。

第三個參數是依賴陣列，和 Effect 同一套邏輯。這裡 `inputRef` 和 `setDraft` 都穩定，所以可以寫 `[]`。若 handle 用到會變的值就得列出來：

```tsx
useImperativeHandle(ref, () => ({ getDraft: () => draft }), [draft]);
```

把 `[draft]` 寫成 `[]`，`getDraft()` 會永遠回傳第一次 render 的空字串，又是一次 stale closure。

## Task Tracker：兩個需求落地

`TaskForm` 已在上一節完整列出，它做了兩個決定：`handleSubmit` 最後把 focus 放回 input，這次 input 一直存在，不必等 commit；對外只開 `focus` 和 `clear`。`TasksPage` 只動了下面幾處，資料載入的 Effect 維持第 11 章的樣子。

提示的計時器由事件啟動，而且同名任務也要重新計時，所以依前面的判斷放 ref。卸載時另外用一個 Effect 收尾，否則使用者換頁後計時器還掛著：

```tsx
const noticeTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
const formRef = useRef<TaskFormHandle>(null);

useEffect(() => {
  return () => {
    clearTimeout(noticeTimerRef.current);
  };
}, []);

const handleAdd = (title: string): void => {
  const task = createTask(title);
  updateTasks((prev) => addTask(prev, task));
  setLastAddedTitle(title);
  clearTimeout(noticeTimerRef.current);
  noticeTimerRef.current = setTimeout(() => {
    setLastAddedTitle(null);
  }, NOTICE_MS);
};
```

`NOTICE_MS` 是定義在模組頂端的 `3000`。父層的兩個新按鈕透過 handle 操作表單。「重設畫面」要清掉的草稿歸 `TaskForm` 所有，把 `draft` 提升上來只為了這一顆按鈕並不划算：

```tsx
const handleReset = (): void => {
  setQuery('');
  setFilter('all');
  formRef.current?.clear();
};

// JSX 裡的新增與異動部分
<>
  <TaskForm ref={formRef} onAdd={handleAdd} />
  <button type="button" onClick={handleReset}>
    重設畫面
  </button>
  {remote.status === 'success' && tasks.length === 0 && (
    <button type="button" onClick={() => formRef.current?.focus()}>
      建立第一筆任務
    </button>
  )}
</>
```

兩個看板並排時，各自的 `formRef`、`noticeTimerRef` 互不干擾，開場的兩個症狀都消失了。

## 常見誤解

**「把 `ref.current` 放進依賴陣列，值變了 Effect 就會跑。」** 依賴只在 render 時比較，而改 `current` 不會引發 render，所以改完什麼事都不會發生。等某個無關的 render 來了，React 才發現值不同而重跑 Effect，時機完全不可預期。想在值改變時做事，要嘛它該是 state，要嘛把那件事寫在改值的 handler 裡。反過來，`useRef` 回傳的 ref 物件本身是穩定的，不需要列入依賴。

**「改用 ref 可以減少 render，所以比較快。」** 這只在值確實不影響畫面時才成立。受控 input 換成 ref，打字時的 render 是少了，但送出按鈕的 disabled、字數提示就都要另外想辦法同步。React Hook Form 確實靠非受控 input 減少 render，那是整套機制（第 17 章），單獨把 state 換成 ref 只是把 bug 換個地方。慢不慢先量（第 28 章）。

**「專案升到 React 19 就要把 `forwardRef` 全改掉。」** 不用，它還能跑，也不會改變行為。新寫的 component 用 ref prop，舊的等碰到再改或跑 codemod，不必為此開一支大 PR。

## 同事會來問你的問題

**「我的 ref 是 null，要從哪裡查？」** 照時間軸問四件事。讀的時機是否在 commit 之前，例如 render 中，或 setState 的下一行？節點此刻是否存在，例如被條件渲染隱藏？傳給的是自己寫的 component 嗎？它有沒有把 `ref` 接到內層節點上？讀的地方是不是 Effect cleanup？卸載時那裡已經是 `null`。多數情況問到第二題就有答案。如果呼叫寫成 `?.`，先暫時印出 `current`，否則連「有沒有執行到」都看不出來。

**「lint 說 render 不能讀 ref，那我要依元素高度決定版面怎麼辦？」** 把量到的結果變成 state。第 11 章的 `DueDateHint` 就是這樣做：`useLayoutEffect` 讀節點高度、setState、同步重新 render，繪製前就修正好。畫面依賴的是 state，ref 只負責取得節點。

**「`clear` 為什麼不用 `key` 重置表單？」** 第 09 章的 `key` 也做得到，而且不需要 handle，父層多一個遞增的 `formKey` 就好。差別是 `key` 會把整個 `TaskForm` 連同 DOM 節點一起換掉，所有內部 state 全部重來，適合「徹底換一份資料」。只想清一個欄位時，handle 比較精準。兩者都比把 `draft` 提升到頁面合理，後者會讓 `TasksPage` 每打一個字就 render 一次。

**「舊程式裡有個 prop 叫 `inputRef`，這是什麼？」** React 18 以前 `ref` 不能當一般 prop，有些人不想用 `forwardRef`，就改個名字傳 ref 物件。它一直都能跑，只是呼叫端寫法和原生元素不一致。React 19 之後直接叫 `ref` 即可。

## 本章小結

ref 是 React 替每個 component 實例保管的盒子，跨 render 保留、寫完立刻讀得到、改了不引發 render，畫面要用的值因此不該放在裡面，render 期間也不該碰它。DOM 節點要到 commit 才進 `current`，時間軸能解釋大部分的 `null`，節點出現的那一刻要做事就用 ref callback。對外交 ref 時，能用 props 描述的就用 props，真正屬於動作的才用 `useImperativeHandle` 縮成窄介面。`TasksPage` 現在的 state 和 handler 越來越多，下一章處理事件邏輯該怎麼收攏，以及資料要穿透很多層時怎麼辦。

## 連結

- [[react-11-effects]] — 上一章：Effect、cleanup、依賴陣列
- [[react-13-reducer-and-context]] — 下一章：`useReducer` 與 Context
- [[react-08-state]] — 快照、batching、受控 input
- [[react-09-rendering]] — render 與 commit、component 必須 pure、`key`
- [[react-14-memoization]] — React Compiler 與參考相等
- [[react-17-forms]] — React Hook Form 與非受控 input
- [[react-27-accessibility]] — 鍵盤操作與 focus 管理
- [[react-30-concurrent-react]] — 可中斷的 render
- [[react-32-canvas-foundations]] — 用 ref 接 Canvas
- [[react-42-legacy-and-migration]] — `forwardRef` 遷移與 codemod
- [[dom]] — DOM 節點與瀏覽器 API
