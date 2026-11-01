---
type: synthesis
domain: tech
tags: [javascript, typescript, react, frontend, foundations]
sources:
  - raw/Web Framework/React/DOM 節點觀念.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/type vs interface.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/前端傳輸概念 (axios + React Query+Promise).md
created: 2026-10-17
updated: 2026-10-17
---

# JavaScript → TypeScript → React：前端基礎一本通

這是一份給 JavaScript 還不穩、但想學 React 的開發者的單一入口教材。它不要求你先把 JavaScript 的所有角落背完；相反地，它把真正會在 React 中遇到的 JavaScript 知識先抽出來，再用 TypeScript 建立資料護欄，最後讓 React 將資料變成可以操作的畫面。

全書使用同一個 Task Tracker 貫穿。它一開始只是陣列資料，接著成為可處理非同步資料的 TypeScript 程式，最後變成 React 畫面。讀完後，你應能理解一個 React feature 裡每一段程式分別屬於 JavaScript、TypeScript 或 React，而不是只會複製 Hook 範本。

## 全書地圖

| 章節 | 要回答的問題 | 完成後能做什麼 |
| --- | --- | --- |
| 1 | 瀏覽器中的 JavaScript 是誰在執行？ | 理解 DOM、event、module 與 HTTP 的位置 |
| 2 | 資料與函式如何組成程式？ | 使用 object、array、function、scope 與 closure |
| 3 | UI 資料怎麼安全地變化？ | 用 `map`、`filter`、spread 寫 immutable update |
| 4 | 為何網路資料不會立刻回來？ | 正確使用 Promise、`async` / `await` 與錯誤處理 |
| 5 | TypeScript 保護了什麼？ | 用 `strict`、型別與 `null` 檢查降低錯誤 |
| 6 | 不可信資料怎麼進入系統？ | 用 union、`unknown`、narrowing 與 type guard 處理 API |
| 7 | React 怎麼把資料變成 UI？ | 寫 Component、JSX、Props、事件與列表 |
| 8 | 一次互動為何會更新畫面？ | 管理 State、controlled input、derived data 與 state ownership |
| 9 | React 何時要碰外部世界？ | 正確使用 `useEffect`、`useRef` 與資料載入狀態 |

## 先建立正確地圖：三者不是競爭關係

JavaScript 是實際在瀏覽器執行的語言。它能建立 object、呼叫函式、等待網路請求、接收 click event，也能直接操作 DOM。TypeScript 是 JavaScript 的開發期檢查器：它在程式執行前檢查你宣告的資料形狀是否自洽，最後仍會被轉成 JavaScript。React 則建立在兩者之上，替你管理「資料改變後，哪裡該重新渲染」這件事。

```text
使用者點擊按鈕
        ↓
JavaScript event handler 執行
        ↓
React 更新 State 並重新 render UI
        ↓
需要後端資料時，JavaScript fetch 發出 HTTP request
        ↓
TypeScript 在開發期檢查資料如何被使用
```

最常見的誤解是以為 TypeScript 會修好 JavaScript 的所有問題。它不會讓 API 自動回傳正確資料，也不會讓 `await` 消失，更不會替你決定 state 應放在哪裡。它只是及早指出「依你目前的宣告，這段程式可能不安全」。因此學習順序必須是：先懂 JavaScript 的行為，再用 TypeScript 描述它，最後用 React 組織 UI。

## 第一章：JavaScript 發生在瀏覽器裡

網頁載入後，瀏覽器會建立 DOM。DOM 是文件的樹狀結構，也是按鈕、輸入框與文字在 JavaScript 眼中的物件。使用者點擊按鈕時，瀏覽器建立 event，event 會沿著 DOM 樹傳遞；程式註冊的 handler 才會被呼叫。React 沒有改變這個事實，它只是用 JSX 與 event props 讓你以 Component 方式描述它。

Module 則是把程式拆成可組合的單位。`export` 讓檔案公開功能，`import` 讓另一個檔案使用它。不要把所有邏輯放進 Component；例如 Task 資料的轉換規則可以是一般 JavaScript function，React Component 只負責呈現與接收互動。

```ts
// task.ts
export function normalizeTitle(title: string): string {
  return title.trim();
}

// app.ts
import { normalizeTitle } from "./task";

console.log(normalizeTitle("  學 React  "));
```

這段程式還沒有 React，但它已經是 React 專案的一部分。先養成把「資料規則」與「畫面」分開的習慣，後面 Component 才不會變成難以維護的大函式。

## 第二章：資料、函式與作用域

前端多數資料都能以 primitive、object 和 array 表達。Task Tracker 的單筆任務是 object，全部任務是 array；函式則把可重用行為包起來。`const` 代表變數不能重新指向別的值，不代表 object 或 array 內部不會改變，這是初學 React 時非常容易踩到的差異。

```ts
const task = { title: "學 JavaScript", done: false };
task.done = true; // 合法：task 仍指向同一個 object
// task = { title: "學 TypeScript", done: false }; // 不合法：重新指派
```

函式的另一個關鍵是 scope。函式可以讀到建立它時外層 scope 的變數，這稱為 closure。React 每次 render 都會重新呼叫 Component，因此 event handler 讀到的是該次 render 的 state snapshot；這就是為什麼之後會需要 functional update，而不是把它當成神祕規則。

```ts
function makeGreeting(name: string): () => string {
  return () => `你好，${name}`;
}

const greetVic = makeGreeting("Vic");
console.log(greetVic());
```

在這個例子中，內層函式仍可讀到 `name`。你不用先鑽研所有 closure 細節，但要知道函式不是只在宣告那一行存在；它會帶著建立當下可存取的資料。

## 第三章：用陣列與物件描述 UI 資料

UI 的列表、篩選結果與狀態更新，幾乎都依賴 array method。`map` 是「把每筆資料轉成另一筆資料」，`filter` 是「留下符合條件的資料」，`find` 是「找到一筆資料」。先把這些操作寫成純 function，再放進 React，會比一開始就混著 JSX 思考容易得多。

```ts
type TaskStatus = "todo" | "done";

interface Task {
  id: string;
  title: string;
  status: TaskStatus;
}

function toggleTask(tasks: Task[], id: string): Task[] {
  return tasks.map((task) => {
    if (task.id !== id) {
      return task;
    }

    return {
      ...task,
      status: task.status === "todo" ? "done" : "todo",
    };
  });
}

function onlyOpenTasks(tasks: Task[]): Task[] {
  return tasks.filter((task) => task.status === "todo");
}
```

上例沒有修改原本的 `tasks` 或任務 object，而是回傳新陣列與新 object。這就是 immutable update。React 用 reference 判斷資料是否改變；若直接 `push`、`splice` 或修改舊 object，畫面可能暫時看似正確，但 state 的來源會失去可預測性。

spread (`...`) 只是淺複製。若 `task` 內還有巢狀 `metadata`，要更新 `metadata.priority` 時，`metadata` 那一層也必須重新複製。不要把 `{ ...task }` 誤解為 deep copy。

## 第四章：非同步——資料不會立刻回來

`fetch` 發出 request 後，不會馬上得到 JSON；它立刻回傳一個 Promise，代表「未來才會完成的結果」。`async` function 也一定回傳 Promise，`await` 則在該 function 內等待結果完成。理解這個模型，才能知道 loading、error 與資料為何是三個不同狀態。

```ts
async function requestTaskData(): Promise<unknown> {
  const response = await fetch("/api/tasks");

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

async function showTaskCount(): Promise<void> {
  try {
    const data = await requestTaskData();
    console.log(data);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error(message);
  }
}
```

錯誤示範是把 `fetch()` 或 async function 的回傳值當成已完成的資料。另一個常見錯誤是只寫 `await fetch(...)`，卻沒檢查 `response.ok`；HTTP 404 或 500 仍可得到一個 Response，並不會自動進入 `catch`。當多個彼此獨立的請求可以同時進行時，再使用 `Promise.all`，不要無故把可並行的工作串成等待隊伍。

## 第五章：TypeScript——在執行前描述允許的資料

現在 Task Tracker 已能運作，但錯誤的資料形狀仍可能悄悄流進來。TypeScript 的任務是讓你在寫程式時清楚表達資料契約，例如 Task 一定有字串 `id`，`status` 只能是兩個指定字面值之一。這讓自動完成、重構與錯誤訊息都有共同的依據。

```ts
interface CreateTaskInput {
  title: string;
}

function createTask(input: CreateTaskInput): Task {
  return {
    id: crypto.randomUUID(),
    title: input.title.trim(),
    status: "todo",
  };
}
```

請從 `strict: true` 開始，而不是先把錯誤壓掉。尤其是 `null` 與 `undefined`：它們迫使你面對「資料可能尚未載入」或「使用者沒有填值」的真實狀況。對 React 來說，這不只是型別細節，而是 loading、empty 與 error UI 是否完整的來源。

`type` 和 `interface` 都能描述資料。實務上可以用 `interface` 描述 Props、Task 這類 object 形狀；需要 union、intersection 或 utility type 時用 `type`。重點不是每一行都選到唯一正解，而是團隊內的資料意圖保持清楚。

## 第六章：不可信資料必須先驗證

TypeScript 不會在 runtime 檢查 API response。即使你寫下 `const tasks: Task[] = await response.json()`，後端仍可能回傳缺少 `title` 的資料。從網路、URL、`localStorage`、使用者輸入進來的資料，都應先視為 `unknown`，驗證後再成為 domain data。

```ts
function isTask(value: unknown): value is Task {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return typeof candidate.id === "string"
    && typeof candidate.title === "string"
    && (candidate.status === "todo" || candidate.status === "done");
}

function isTaskList(value: unknown): value is Task[] {
  return Array.isArray(value) && value.every(isTask);
}

async function loadTasks(signal: AbortSignal): Promise<Task[]> {
  const response = await fetch("/api/tasks", { signal });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const data: unknown = await response.json();
  if (!isTaskList(data)) {
    throw new Error("Task API returned an invalid shape");
  }

  return data;
}
```

這種 type guard 是入門版 runtime validation。表單或 API 契約變複雜後，可改用 Zod 集中 schema 與錯誤訊息；核心原則不變：`unknown` 先縮窄，絕不以 `any` 假裝資料正確。

Generic 是第六章唯一需要的進階語法。它讓同一個結構可保留資料型別，例如 `ApiResponse<T>` 中的 `T` 代表不同 endpoint 的 payload。先能讀懂並使用一層 generic 即可；conditional type、mapped type、`infer` 和自行重寫 utility type 都可延後。

## 第七章：React——UI 是 State 的函式

React 的核心公式是 `UI = f(state)`。Component 是一個根據 Props 與 State 回傳 JSX 的 function；當 state 改變，React 再呼叫 Component，取得下一張 UI 描述並更新 DOM。這讓你不必在每次資料改變時手動尋找 DOM 節點再修改文字。

Props 是父層交給子層的唯讀輸入。子元件不能直接改 `props.task.status`；它應透過 callback 告訴父層「使用者想切換這個任務」，由擁有 state 的父層完成更新。這就是單向資料流。

```tsx
import { type ReactElement } from "react";

interface TaskListProps {
  tasks: Task[];
  onToggle: (id: string) => void;
}

export function TaskList({ tasks, onToggle }: TaskListProps): ReactElement {
  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.id}>
          <button type="button" onClick={() => onToggle(task.id)}>
            {task.status === "done" ? "完成" : "待辦"}
          </button>
          {task.title}
        </li>
      ))}
    </ul>
  );
}
```

`key` 不是為了讓 warning 消失，而是給 React 辨識列表項目身分。可重排的列表使用資料庫 ID 或其他穩定 ID，不能使用 array index。JSX 也不是 HTML 的複製貼上版本：class 要寫成 `className`，事件接收的是 function，花括號內才是 JavaScript expression。

## 第八章：State——互動如何成為下一張畫面

State 是 Component 在不同 render 間保留的記憶。使用者輸入文字、點擊完成按鈕，都是 event handler 呼叫 setter；React 排定下一次 render，新的 state 產生新的 UI。setter 不會在同一行立即改變目前 closure 內的值，所以依舊值計算下一值時要使用 functional update。

```tsx
import { type FormEvent, type ReactElement, useState } from "react";

export function TaskApp(): ReactElement {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();

    const normalizedTitle = title.trim();
    if (!normalizedTitle) {
      return;
    }

    const newTask = createTask({ title: normalizedTitle });
    setTasks((previousTasks) => [...previousTasks, newTask]);
    setTitle("");
  }

  function handleToggle(id: string): void {
    setTasks((previousTasks) => toggleTask(previousTasks, id));
  }

  return (
    <main>
      <form onSubmit={handleSubmit}>
        <label htmlFor="task-title">新任務</label>
        <input
          id="task-title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <button type="submit">新增</button>
      </form>
      <TaskList tasks={tasks} onToggle={handleToggle} />
    </main>
  );
}
```

`title` 是 controlled input：畫面上的輸入值由 state 控制，`onChange` 再把使用者輸入送回 state。這有一個明確的真實來源，日後才能做 validation、reset 與送出。

決定 state 放哪裡時，問「哪個 Component 最需要知道並改變這筆資料？」若多個子元件要協作，就把 state 提升到它們最近的共同父層。相反地，`visibleTasks = tasks.filter(...)` 能由現有 state 推導，應在 render 時計算，不要再存一份 `visibleTasks` state 讓 Effect 同步。

## 第九章：Effect、Ref 與外部世界

event handler 處理使用者的明確動作；`useEffect` 用來讓 React 和外部系統同步，例如網路請求、timer、DOM API 或 subscription。這個區分很重要：點擊「儲存」就呼叫 API，應留在 `handleSubmit`；畫面需要在顯示後載入初始任務，才是 Effect。

```tsx
import { type ReactElement, useEffect, useState } from "react";

export function RemoteTaskApp(): ReactElement {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  function handleToggle(id: string): void {
    setTasks((previousTasks) => toggleTask(previousTasks, id));
  }

  useEffect(() => {
    const controller = new AbortController();
    let isActive = true;

    async function load(): Promise<void> {
      try {
        const loadedTasks = await loadTasks(controller.signal);
        if (isActive) {
          setTasks(loadedTasks);
        }
      } catch (caught: unknown) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        if (isActive) {
          setError(caught instanceof Error ? caught.message : "Unknown error");
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void load();
    return () => {
      isActive = false;
      controller.abort();
    };
  }, []);

  if (isLoading) {
    return <p>載入任務中…</p>;
  }

  if (error) {
    return <p role="alert">載入失敗：{error}</p>;
  }

  if (tasks.length === 0) {
    return <p>還沒有任務，先新增一個吧。</p>;
  }

  return <TaskList tasks={tasks} onToggle={handleToggle} />;
}
```

Effect 的 dependency array 表示 Effect 讀取的 React 值變動時，是否需要重新同步。空 array 並不代表「任何環境下絕對只跑一次」；它表達的是本次 mount 不依賴 React 值，而 development 的 StrictMode 可能額外執行 setup、cleanup、setup 來幫你發現不安全的 Effect。因此 Effect 必須能 cleanup，不能假設它永遠只會發生一次。

`useRef` 則保存不需要觸發 render 的值，例如 DOM 節點、timer ID 或取消控制器。改 `ref.current` 不會更新畫面，所以畫面上可見的資料仍應放在 state。新增任務成功後要把游標移回輸入框時，可用 ref 取得 DOM；任務列表本身不可放進 ref。

```tsx
import { type ReactElement, useRef } from "react";

function TaskTitleInput(): ReactElement {
  const titleInputRef = useRef<HTMLInputElement | null>(null);

  function focusTaskInput(): void {
    titleInputRef.current?.focus();
  }

  return (
    <div>
      <input ref={titleInputRef} id="task-title" />
      <button type="button" onClick={focusTaskInput}>聚焦輸入框</button>
    </div>
  );
}
```

## 把三層合在一起：最小專題路徑

先用純 JavaScript 寫 `Task[]` 的新增、切換、刪除與篩選函式，並用 console 驗證輸入與輸出。第二步接 DOM：從表單讀值、監聽 submit、用 `map` 產生列表。第三步轉為 TypeScript：定義 `Task`、`TaskStatus`、輸入型別與 API guard。最後才轉成 React：拆出 `TaskApp`、`TaskForm`、`TaskList`、`TaskItem`，以 `useState` 管理互動，以 `useEffect` 載入初始資料。

這個演進刻意不放 Router、Zustand、React Query 或 UI library。它們在專案變大後才有價值：Router 解決多頁導覽，React Query 解決 server state caching 與 invalidation，Zustand 解決跨 feature 的複雜 client state。若連 Task Tracker 的資料流都還看不清楚，過早加入它們只會讓除錯路徑變長。

## 現在必學，與以後再學

| 現在必學 | 遇到需求再學 |
| --- | --- |
| object、array、function、scope、event、module | prototype、複雜 `this` 綁定、class inheritance、generator |
| `map`、`filter`、spread、immutable update | 複雜的 deep clone 與資料結構最佳化 |
| Promise、`async` / `await`、`try` / `catch`、HTTP/JSON | event loop 細節、Web Worker、複雜並發控制 |
| TypeScript strict、union、`null`、`unknown`、narrowing、基本 generic | conditional / mapped / template-literal type、`infer` |
| Props、State、事件、key、Effect、Ref、custom hook | Zustand、React Query、Router/Auth、memoization、Canvas、Server Components、Monorepo |

當你能獨立完成 Task Tracker 的四個演進版本，你就有足夠的 JavaScript 底子繼續進入 [[react-frontend-development-roadmap]] 的路由、Auth、資料層與部署階段。卡關時不要只搜尋 React 答案；先辨識問題屬於資料轉換、非同步、型別還是 UI state，再回到對應章節補洞。

## 連結

- [[basics-02-rest-api-design]] — 這個 Task Tracker 的後端規格；真實後端的 `GET /api/tasks` 回 `{ items, page, pageSize, totalCount }`，不是陣列
- [[dom]]
- [[typescript]]
- [[react]]
- [[react-frontend-development-roadmap]]
- [[web-frontend-moc]]
