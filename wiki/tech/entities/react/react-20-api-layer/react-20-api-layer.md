---
type: concept
domain: tech
tags: [react, typescript, api-client, axios, fetch, problem-details, zod, vite-env, cors, aspnet-core]
sources:
  - raw/Web Framework/React/API 設計.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/前端傳輸概念 (axios + React Query+Promise).md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/AuthProvider & Route 概念.md
created: 2026-10-30
updated: 2026-11-01
---

# 第 20 章：API 層 — API 呼叫該寫在哪裡，壞掉時誰負責

## 三個 bug，三種壞法

第 19 章結束時，Task Tracker 有了路由，資料請求卻還零散地寫著 `fetch`：`fetchTasks` 一份，`fetchTask` 一份，每份各自決定怎麼處理錯誤。接上真的 ASP.NET Core API 的第一個星期，你收到三張單。

第一張：後端部署時炸了一次，使用者看到白畫面，console 寫著 `TypeError: tasks.map is not a function`。那段程式是這樣的：

```ts
const response = await fetch('/api/tasks');
const tasks: Task[] = await response.json();
```

第二張：後端同事把 `assigneeId` 改名成 `assigneeUserId`，負責人欄從此全部空白。`tsc` 全過，沒有錯誤訊息，兩天後才有人發現。

第三張：同事想直接打 `http://localhost:5033` 測試，console 一片紅字，axios 只說 `Network Error`。他用 curl 打同一個網址卻完全正常，於是來問你是不是後端壞了。

三個 bug 都和 React 無關，都發生在瀏覽器與伺服器之間那條縫。本章要回答的是：這條縫該由誰來守？API 呼叫該寫在哪一層，錯誤該在哪裡轉換，回應該在哪裡驗證，一個變數進了 bundle 會怎樣，瀏覽器又為什麼擋下 curl 不擋的請求。

## 一個請求有幾種壞法

第一張單的根因是對 `fetch` 的誤解。它回傳的 Promise（第 03 章）只對「沒拿到 HTTP 回應」這件事 reject：DNS 失敗、連線中斷、被取消。伺服器回了 500，對 `fetch` 而言任務圓滿成功，你拿到一個 `ok` 為 `false` 的 `Response`。

所以 500 的 ProblemDetails 被 `response.json()` 順利解析成物件，一個物件被標註成 `Task[]` 放進 state，直到 `.map` 才爆。錯誤發生在網路層，症狀卻出現在 render，stack trace 指著無辜的 `TaskList`。第 11 章先用一行 `if (!response.ok) throw` 擋住，但那只處理了一種壞法。把一個請求可能的結局全部列出來，才知道 API 層要接住什麼：

| 結局 | `fetch` 的行為 | 誰會造成 |
| --- | --- | --- |
| 網路失敗 | reject `TypeError` | 斷線、DNS、CORS 擋下 |
| 非 2xx，body 是 JSON | resolve，`ok` 為 `false` | API 回 ProblemDetails |
| 非 2xx，body 是 HTML | resolve，`.json()` 丟 `SyntaxError` | Ingress 或 proxy 的 502 頁面 |
| 2xx，body 是 HTML | resolve，`.json()` 丟 `SyntaxError` | nginx 把 `/api` 也 fallback 到 `index.html`（第 19 章） |
| 204，沒有 body | resolve，`.json()` 丟 `SyntaxError` | `DELETE /api/tasks/{id}` |
| 2xx，JSON 形狀不對 | 全部正常，沒人發現 | 後端改了合約 |

六種結局裡，`fetch` 自己會 reject 的只有第一種。如果每個呼叫點都要處理其餘五種，程式碼會重複，而且一定有人漏掉。這就是把呼叫集中起來的第一個理由。

## 五種模式，是同一段邏輯搬了四次家

「API 呼叫該寫在哪裡」的答案是演進出來的。每一次搬家都是因為上一個位置撐不住某個問題，順著走一遍，你就知道每層在解決什麼。

**模式 1：直接寫在 component 的 Effect 裡。** 這是多數人的起點：

```tsx
useEffect(() => {
  setIsLoading(true);
  fetch('/api/tasks')
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json() as Promise<Task[]>;
    })
    .then(setTasks)
    .catch((e: Error) => setError(e.message))
    .finally(() => setIsLoading(false));
}, []);
```

原型夠用，但每個畫面都要抄一次 URL、錯誤判斷、loading 與 error state，改一次 base URL 要動幾十個檔。`isLoading` 初值是 `false`，第一次 render 畫出的是空清單，第 15 章看過這個問題。沒有 cleanup 則留著第 11 章的競態。

**模式 2：封裝層。** 把「怎麼打這個 API」搬出 component，每個 resource 一個模組，它只知道 HTTP，不知道畫面：

```ts
export const deleteTask = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/tasks/${id}`);
};
```

base URL、timeout、token、錯誤轉換都有了唯一的家，測試也不必 render 畫面。缺口是 component 還要自己寫 loading 與 error。

**模式 3：custom hook。** 第 15 章的 `useTasks` 就在這一層，把 state 與 Effect 也搬走，component 只管畫面。重新載入也只要在依賴陣列放一個計數器，遞增就重跑 Effect。它共用的是邏輯，state 不共用：兩個 component 各呼叫一次 `useTasks`，就發兩個請求、存兩份資料，其中一份改了另一份不知道。切換頁面再回來要不要重打？資料更新後其他畫面怎麼同步？這一層都答不出來。

**模式 4：server state 函式庫。** 這正是上一個缺口的答案。TanStack Query 把資料放進 component 外的快取，以 key 辨識，同一個 key 共用一份，並管理過期與背景更新：

```ts
const { data, isPending, error } = useQuery({
  queryKey: ['tasks', filters],
  queryFn: ({ signal }) => fetchTasks(filters, signal),
});
```

注意 `queryFn` 呼叫的仍是模式 2 的 `fetchTasks`。TanStack Query 不發請求，它管資料的生命週期，「怎麼打 API」還是你的封裝層負責。所以這五種模式不是五選一，模式 2 是模式 3、4 的地基，完整內容在第 21 章。

**模式 5：GraphQL。** 前四種都假設後端是 REST，一個端點回固定形狀；GraphQL 把形狀的決定權交給前端，由一個端點接受查詢：

```graphql
query GetTasks {
  tasks {
    id
    title
    assignee {
      name
    }
  }
}
```

它的型別可從後端 schema 由 codegen 自動產生，Apollo Client 這類 client 還附帶正規化快取。代價是後端要整套換：schema、resolver、N+1 查詢防護、授權要做到欄位層級，HTTP 快取也不再能照 URL 運作。Task Tracker 的畫面與資源幾乎一對一，後端又是現成的 Web API，沒有理由付這個代價。多個前端各要不同形狀的資料、後端團隊也願意維護 schema 時才值得考慮。

| 模式 | 快取 | 型別安全 | 重用 | 設定成本 | 適合 |
| --- | --- | --- | --- | --- | --- |
| 1. 直接呼叫 | 無 | 手動斷言 | 低 | 極低 | 原型、demo |
| 2. 封裝層 | 無 | 搭 Zod 可靠 | 中 | 低 | 任何 REST 專案的地基 |
| 3. Custom hook | 無 | 同上 | 高 | 低 | 不想加相依的小型共用邏輯 |
| 4. TanStack Query / SWR | 有 | 同上 | 高 | 中 | 主流 REST 專案 |
| 5. GraphQL | 有 | codegen | 高 | 高 | 查詢形狀多變且後端願意配合 |

本章把模式 2 蓋好，下一章在上面加模式 4。

## fetch 還是 axios

蓋封裝層前要選底層工具。`fetch` 是瀏覽器內建的零相依選項，要它處理上面那張表，至少得包這麼一層：

```ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export const fetchJson = async (path: string, init: RequestInit = {}): Promise<unknown> => {
  const headers = new Headers(init.headers);
  if (init.body !== undefined) headers.set('Content-Type', 'application/json');

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const text = await response.text();
  return text === '' ? undefined : JSON.parse(text);
};
```

先讀 text 再判斷空字串，204 才不會炸。`new Headers` 則避開一個常見失誤：寫成 `{ headers: { ... }, ...options }` 時，呼叫端一傳 `headers`，整組預設值連同 `Content-Type` 就被蓋掉。即使如此，這層還沒有 timeout、query string 序列化，也沒有第 22 章 refresh 要用的攔截點，這些都要自己補。

axios 內建了這些：

| 需求 | `fetch` | axios |
| --- | --- | --- |
| 非 2xx | resolve，自己查 `ok` | reject `AxiosError`，`error.response` 帶回應 |
| 解析 JSON | 自己呼叫，204 或 HTML 會丟錯 | 自動；HTML 維持字串，204 不丟錯 |
| Timeout | 自己組 `AbortSignal` | `timeout` 選項，逾時的 `code` 是 `ECONNABORTED` |
| Query string | 自己組，要處理 `undefined` | `params`，值為 `undefined` 的 key 不送 |
| 攔截 | 自己包函式 | `interceptors` |
| 取消 | `signal` | `signal`，用 `axios.isCancel` 判斷 |
| 成本 | 零相依 | 多一個相依 |

Task Tracker 選 axios，決定性的理由是第 22 章「401 → refresh → 重試原請求」要有攔截點。如果專案沒有 refresh、又在意相依數量，`fetchJson` 也完全站得住。下一節之後的 `ApiError` 與 Zod 兩種都適用，換的只有最底下一層。

使用者框架規範有一條「NEVER 在 component 內 `axios.create()`」，理由藏在 interceptor 的歸屬裡：interceptor 掛在 instance 上，每次 `axios.create()` 都是一個什麼都沒掛的新 instance。在 component 裡 create，請求照樣送出，卻沒有錯誤轉換，第 22 章之後也不會有 token，錯誤格式和全站不同，而且不會有任何報錯提醒你。

## 集中的 client：一個 instance 守住所有出口

`lib/api/client.ts` 是全站唯一的 axios instance：

```ts
import axios from 'axios';
import { toApiError } from './problem';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 15_000,
  // 同源請求不受影響；只有 VITE_API_BASE_URL 指向別的 origin 才需要。
  withCredentials: true,
});

apiClient.interceptors.response.use(undefined, (error: unknown) => {
  if (!axios.isAxiosError(error) || axios.isCancel(error)) throw error;
  throw toApiError(error);
});
```

interceptor 是掛在請求前後的函式。熟悉 .NET 的話，最接近的是 `HttpClient` 的 `DelegatingHandler`：同樣包住每個 outgoing 請求，同樣掛在特定 client 上。類比破在註冊順序：`DelegatingHandler` 先加的在最外層，axios 則是後加的在最外層，所以 request interceptor 後加的先跑，response interceptor 先加的先跑。從 .NET 帶來的直覺在這裡會把順序想反。

`response.use` 的第一個參數是成功時的處理，這裡傳 `undefined` 表示不動；第二個才處理失敗。取消要原樣放行，因為使用者換了篩選條件造成的 abort 不是錯誤，不該顯示紅字。到第 22 章，這個檔會多一個注入 token 的 request interceptor，和 401 時 refresh 的邏輯，呼叫端一行都不用改。這就是集中的回報。

## 把 ProblemDetails 轉成前端看得懂的錯誤

API 的錯誤一律是 RFC 9457 的 `application/problem+json`，形狀來自 `AddProblemDetails`（[[15-error-handling]]）：

```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.1",
  "title": "One or more validation errors occurred.",
  "status": 400,
  "traceId": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "errors": { "title": ["The Title field is required."], "$.dueDate": ["Invalid date."] }
}
```

如果讓 `AxiosError` 一路傳到 component，每個畫面都要寫 `error.response?.data?.title`，而 `data` 的型別是未知的，整個專案就和 axios 綁死。所以在邊界轉成自己的型別：

```ts
export class ApiError extends Error {
  // 0 means the request never got a response: network failure or timeout.
  readonly status: number;
  readonly title: string;
  readonly detail: string | undefined;
  readonly traceId: string | undefined;
  readonly errors: Record<string, string[]>;

  constructor({ status, title, detail, traceId, errors }: ApiErrorInit) {
    super(detail ?? title);
    this.name = 'ApiError';
    this.status = status;
    this.title = title;
    this.detail = detail;
    this.traceId = traceId;
    this.errors = errors ?? {};
  }
}
```

這裡用 class 是因為需要 `instanceof`：catch 拿到的是 `unknown`，`error instanceof ApiError` 一次完成 narrowing。欄位逐一宣告而不用 constructor parameter property，是模板開了 `erasableSyntaxOnly`。

`ApiErrorInit` 只是這五個欄位組成的 interface。轉換函式處理的是前面那張表的前三列，錯誤 body 用寬鬆的 schema 驗，`z.looseObject` 容許 ProblemDetails 帶擴充欄位：

```ts
const problemDetailsSchema = z.looseObject({
  type: z.string().optional(),
  title: z.string().optional(),
  status: z.number().optional(),
  detail: z.string().nullish(),
  traceId: z.string().optional(),
  errors: z.record(z.string(), z.array(z.string())).optional(),
});

export const toApiError = (error: AxiosError): ApiError => {
  if (!error.response) {
    return new ApiError({ status: 0, title: '無法連線到伺服器' });
  }

  const { status, data } = error.response;
  const parsed = problemDetailsSchema.safeParse(data);
  if (!parsed.success) {
    // A proxy or load balancer can answer with HTML before the request ever reaches the API.
    return new ApiError({ status, title: `伺服器回應錯誤（HTTP ${status}）` });
  }

  return new ApiError({
    status,
    title: parsed.data.title ?? `伺服器回應錯誤（HTTP ${status}）`,
    detail: parsed.data.detail ?? undefined,
    traceId: parsed.data.traceId,
    errors: parsed.data.errors,
  });
};
```

沒有 `response` 時，斷線、逾時、CORS 擋下全部併成 `status: 0`。逾時其實有 `code` 可分辨，Task Tracker 選擇不分；斷線和 CORS 則連 JavaScript 都分不出。錯誤 body 不能假設是 JSON，因為 Ingress 的 502 會回 HTML；來源筆記常見的 `err.response?.data?.message` 在這裡拿到的是 `undefined`，ProblemDetails 也根本沒有 `message` 欄位。

`title` 與 `detail` 是英文、寫給開發者看的，不該直接給使用者，所以畫面一律透過 `describeError` 取訊息：

```ts
const STATUS_MESSAGES: Partial<Record<number, string>> = {
  401: '登入資訊無效或已過期',
  403: '你沒有權限執行這個操作',
  404: '找不到這筆資料',
};

export const describeError = (error: unknown): string => {
  if (error instanceof ApiError) {
    if (error.status >= 500) return '伺服器發生錯誤，請稍後再試';
    return STATUS_MESSAGES[error.status] ?? error.message;
  }
  if (error instanceof z.ZodError) return '伺服器回應的格式和預期不符';
  return '發生未預期的錯誤';
};
```

500 以上不透露細節，避免洩漏內部資訊。`traceId` 留著給回報用，第 41 章會把它接上觀測工具。

驗證錯誤多一道手續。`errors` 的 key 有三種形狀：`title` 來自 DataAnnotations，`$.dueDate` 來自 JSON 轉型失敗，`$` 或空字串表示整個 body 讀不了、對應不到任何欄位。`splitValidationErrors`（`lib/api/problem.ts`）把它們分成兩堆：

```ts
export const splitValidationErrors = (errors: Record<string, string[]>): ValidationErrors => {
  const result: ValidationErrors = { fieldErrors: {}, formErrors: [] };
  for (const [key, messages] of Object.entries(errors)) {
    const field = key.startsWith('$.') ? key.slice(2) : key;
    if (field === '' || field === '$') {
      result.formErrors.push(...messages);
    } else if (messages[0] !== undefined) {
      result.fieldErrors[field] = messages[0];
    }
  }
  return result;
};
```

輸入 `{ title: [...], '$.status': [...], $: [...] }`，`fieldErrors` 得到 `title` 與去掉前綴的 `status`，`formErrors` 得到 `$` 的訊息。第 17 章的 `TaskForm` 用前者呼叫 React Hook Form 的 `setError` 掛回欄位，後者顯示在表單頂端。

你也許在舊專案看過另一種約定：所有回應都包成 `{ data, success, message, errors }` 信封。HTTP 已經有狀態碼，信封讓 200 也可能代表失敗，每個呼叫都要多拆一層，所以 Task Tracker 不用；框架規範的 `useApi<T>` 有拆信封的做法，第 21 章對照。分頁回應（`items`、`totalCount`）則是資料本身的形狀，該有就有，schema 照常寫。

## 型別是承諾，Zod 才是查核

現在處理第二張單。這是多數教學會寫的版本：

```ts
const response = await apiClient.get<Task[]>('/api/tasks');
```

`get<Task[]>` 看起來像在檢查，實際上那個泛型只是換個寫法的 `as`：第 04 章說過型別在編譯後全部消失。後端把欄位改名後，這行照常通過，`response.data[0].assigneeId` 在 runtime 是 `undefined`，型別卻宣稱它是 `string | null`。負責人欄空白，沒有錯誤，也沒人知道。

修法是誠實地把回應標成 `unknown`，再用第 17 章認識的 Zod 查核：

```ts
export const taskSchema = z.object({
  id: z.uuid(),
  title: z.string(),
  status: taskStatusSchema,
  assigneeId: z.uuid().nullable(),
  dueDate: z.iso.datetime().nullable(),
  createdAt: z.iso.datetime(),
});

export type Task = z.infer<typeof taskSchema>;

export const tasksResponseSchema = z.array(taskSchema);
```

```ts
export const fetchTasks = async ({ status, q }: TaskFilterValues, signal?: AbortSignal): Promise<Task[]> => {
  const response = await apiClient.get<unknown>('/api/tasks', {
    params: { status: status === 'all' ? undefined : status, q: q === '' ? undefined : q },
    signal,
  });
  return tasksResponseSchema.parse(response.data);
};
```

`Task` 型別改由 schema 推導，型別與檢查不會漂移。同樣的改名現在會丟 `ZodError`，`issues[0].path` 是 `[0, 'assigneeId']`，指出第幾筆的哪個欄位。第二張單兩天才發現的問題，變成第一次請求就看得到的錯誤。表裡剩下的「2xx 卻是 HTML」也在這裡被接住：axios 把 HTML 留成字串，字串過不了 `z.array`。

`parse` 放在 API 函式而不是 interceptor，因為只有 `fetchTasks` 知道該用哪個 schema。它和後端的 DTO 驗證很像，都是守邊界，類比破在失敗時誰能修：後端驗證失敗回 400，使用者改一下輸入就好；前端的 `ZodError` 表示兩邊的合約破了，使用者無能為力，該做的是顯示通用訊息並讓開發者知道。`describeError` 因此對 `ZodError` 回「伺服器回應的格式和預期不符」。

驗證的嚴格程度是取捨，要知道它會在哪裡擋你：

- 多出的欄位會被 `z.object` 剝掉，不會失敗。後端加欄位是安全的，但想讀新欄位要先改 schema。
- enum 新值會失敗。後端加一個 `blocked` 狀態，舊版前端的 `parse` 直接拒絕。
- 一筆壞，整個清單都失敗。一千筆裡有一筆 `blocked`，使用者一筆都看不到。這對內部系統通常是對的（馬上就會被發現並修好）；要容錯就逐筆 `safeParse`、略過並回報，但你換來的是一份悄悄少了資料的清單。

對接 ASP.NET Core 還有一個專屬陷阱。`z.iso.datetime()` 預設只接受結尾是 `Z` 的 UTC 字串，`2026-10-30T12:00:00.1234567Z` 這種七位小數沒問題，但 `+00:00` 與沒有時區的 `2026-10-30T12:00:00` 都會被拒絕。而 `DateTimeOffset` 序列化 UTC 時寫的正是 `+00:00`，Oracle `TIMESTAMP` 對應的 Kind 為 Unspecified 的 `DateTime` 則沒有時區字尾。所以你可能在第一次接真 API 時就看到整片 `ZodError`。Task Tracker 的解法在後端：DTO 用 `Kind=Utc` 的 `DateTime`，輸出固定為 `Z`。後端改不動時，用 `z.iso.datetime({ offset: true })` 或 `{ local: true }` 放寬。

## 寫入：undefined 與 null 不一樣，復原也不再是換陣列

有了 client，第 11 章留下的缺口可以補了：新增、切換、刪除終於寫到伺服器。`tasksApi.ts` 補齊其餘函式：

```ts
export type NewTask = Pick<Task, 'title' | 'status' | 'assigneeId' | 'dueDate'>;
export type TaskPatch = Partial<NewTask>;

export const updateTask = async (id: string, patch: TaskPatch): Promise<Task> => {
  const response = await apiClient.patch<unknown>(`/api/tasks/${id}`, patch);
  return taskSchema.parse(response.data);
};
```

`PATCH` 的語意是「只改出現的欄位」，`assigneeId` 傳 `null` 代表清空。JSON 沒有 `undefined`，序列化時那個 key 直接消失：`updateTask(id, { assigneeId: null, dueDate: undefined })` 送出的 body 是 `{"assigneeId":null}`，`dueDate` 維持原值。如果你想清空日期卻傳了 `undefined`，API 回 200，日期卻沒變，看起來就像後端的 bug。

`addTask` 也要變。第 08 章的 `taskOps.createTask` 在前端產生 id，現在 id 由伺服器決定，hook 要等回應：

```ts
const addTask = useCallback(async (title: string): Promise<void> => {
  const task = await createTask({ title, status: 'todo', assigneeId: null, dueDate: null });
  dispatch({ type: 'taskAdded', task });
}, []);
```

第 13 章的 undo 這時會暴露假設上的破口。`past` 存的是舊陣列，把陣列換回去只改了前端記憶體，伺服器上的資料沒有動，重新整理就全部回來。一旦資料住在伺服器，復原就是另一次 API 呼叫：切換狀態的復原是把舊值再 `PATCH` 回去；刪除的復原是重新 `POST`，而且會拿到新 id，原本的 `createdAt` 也回不來。第 09 章警告過的錯位 key 在這裡也變貴了：帶著錯誤 id 的 `PATCH` 改的是伺服器上別筆任務的資料。第 21 章的樂觀更新會處理 cache 回滾與請求順序，這裡先記住，前端狀態的時光機管不到伺服器。

讀取這邊只動兩行：`useTasks` 裡的 `fetchTasks({ q: query }, signal)` 改傳第 19 章 `useTaskFilters` 解出的 `{ status, q }`，catch 裡的訊息改用 `describeError(error)`。

詳情頁也兌現第 19 章的約定。網址是使用者能亂打的，先用 `z.uuid()` 擋掉，連請求都不必發：

```tsx
export const TaskDetailPage = (): React.JSX.Element => {
  const { taskId } = useParams<'taskId'>();
  const isValidId = z.uuid().safeParse(taskId).success;

  return (
    <section>
      <Link to="/tasks">回任務清單</Link>
      {taskId !== undefined && isValidId ? <TaskDetail key={taskId} taskId={taskId} /> : <TaskNotFound />}
    </section>
  );
};
```

`fetchTask` 不再用 `null` 表示 404，錯誤統一走 `ApiError`，由畫面決定 404 算不算一種狀態。第 19 章的 `RemoteData<Task | null>` 因此換成多一個成員的 union，不存在與載入失敗從此分得清楚：

```ts
type TaskDetailState =
  | { status: 'loading' }
  | { status: 'success'; data: Task }
  | { status: 'not-found' }
  | { status: 'error'; message: string };
```

```ts
if (signal.aborted) return;
if (error instanceof ApiError && error.status === 404) {
  setState({ status: 'not-found' });
} else {
  setState({ status: 'error', message: describeError(error) });
}
```

如果後端用的不是 RFC 版本位元的 GUID（自訂產生或資料庫轉出），`z.uuid()` 會拒絕，要改用只驗格式的 `z.guid()`。Task Tracker 的 id 是 v7 UUID，沒有這個問題。

## 環境變數：寫在 build 裡的公開字串

client 的 `baseURL` 來自 `import.meta.env.VITE_API_BASE_URL`。後端的直覺會以為這和 `appsettings.json` 一樣是執行期讀的設定，其實它在 `vite build` 時就被替換成字面值，寫死在 JavaScript 裡。兩個推論都很重要。

第一，它是公開的。只有 `VITE_` 開頭的變數會進前端程式碼，這個前綴是防呆，不是加密：進了 bundle，任何人打開 DevTools 都讀得到。`VITE_API_SECRET` 是自相矛盾的名字。沒有前綴的 `SECRET_TOKEN` 在前端讀到是 `undefined`，字串也不會出現在 bundle。需要金鑰的呼叫要走後端。

第二，改值要重新 build，同一份映像檔換不了環境。這個兩難與解法在第 29 章。Task Tracker 的策略是讓問題變小：正式環境前後端同源，`VITE_API_BASE_URL` 不設，請求走相對路徑 `/api/...`。

檔案依 mode 載入：`.env`、`.env.local`、`.env.[mode]`、`.env.[mode].local`，mode 專屬的優先，`vite build` 的 mode 預設是 `production`。程式裡要判斷環境用內建的 `import.meta.env.MODE`、`DEV`、`PROD`，前者是字串、後兩者是真正的 boolean。`.env` 在 Vite 啟動時讀取，改完要重啟 dev server，這也是「我改了 .env 卻沒生效」的常見原因。

值永遠是字串，這造成最常見的陷阱：

```ts
// .env.production 寫 VITE_SHOW_BURNDOWN=false
const isBurndownVisible = Boolean(import.meta.env.VITE_SHOW_BURNDOWN); // true，'false' 是非空字串
const isBurndownVisibleFixed = import.meta.env.VITE_SHOW_BURNDOWN === 'true'; // false
```

預設值也要選對運算子。`VITE_API_BASE_URL=` 設成空字串是有意義的（同源），`??` 會保留它，`||` 卻會把它換成後面的備援值。client 因此寫 `?? ''`。

型別方面，沒宣告的 `VITE_*` 是 `any`，typo 不會報錯，所以在 `src/vite-env.d.ts` 宣告。這個檔不能有 `import` 或 `export`，否則 augmentation 失效：

```ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_GOOGLE_CLIENT_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

宣告成 `'DEV' | 'PROD'` 這類 union 也只是承諾，Vite 不會檢查 `.env` 的實際內容。用環境變數隱藏選單項目則只是 UI 開關，功能本身的保護要靠後端授權。

## CORS：瀏覽器在保護誰

回到第三張單。curl 成功而瀏覽器失敗，因為 CORS 根本不是伺服器的防火牆，執行者是瀏覽器。

要理解它得先看同源政策。想像你登入公司內部的 Task Tracker 後，開了另一個分頁逛惡意網站。如果瀏覽器讓那個網站的 JavaScript 自由讀取任意網址的回應，它就能帶著你的登入 cookie 打內網 API，把結果讀走。所以瀏覽器規定：頁面的 JavaScript 只能讀同源的回應。Origin 是 scheme、host、port 三者的組合，`http://localhost:5173` 與 `http://localhost:5033` 只差 port，就是不同 origin。curl 沒有你的 cookie，也沒有「頁面」要保護，自然不受這條規則管。

但前後端分離確實需要跨 origin，CORS 就是伺服器宣告「我允許這些 origin 讀我」的機制。`PATCH` 這類方法，或帶 `Authorization`、`Content-Type: application/json` 的請求，瀏覽器會先問一聲：

```text
瀏覽器（頁面在 http://localhost:5173）          API（localhost:5033）
  OPTIONS /api/tasks/1 ------------------------->  Origin、要用的方法與 header
  <------------------------- 204 + Allow-Origin、Allow-Methods、Allow-Headers
  對照通過才送真正的請求
  PATCH /api/tasks/1 --------------------------->  執行
  <------------------------- 200 + Allow-Origin
  標頭相符才把回應交給 JavaScript
```

沒有通過預檢的 `PATCH` 不會送出。不觸發預檢的簡單請求則不同：它會送到伺服器並被執行，瀏覽器只是不讓 JavaScript 讀回應。所以 CORS 不能當存取控制，也不能防 CSRF（第 22、37 章）。而 JavaScript 拿不到失敗原因，只有 console 有，axios 只能說 `Network Error`，於是變成 `ApiError` 的 `status: 0`。看到 status 0 又是跨 origin，先開 console。

ASP.NET Core 端的設定：

```csharp
services.AddCors();

services
    .AddOptions<CorsOptions>()
    .Configure<IOptions<CorsSettings>>((options, settings) =>
    {
        options.AddPolicy(SpaCorsPolicy, policy => policy
            .WithOrigins(settings.Value.AllowedOrigins)
            .WithMethods(HttpMethods.Get, HttpMethods.Post, HttpMethods.Patch, HttpMethods.Delete)
            .WithHeaders("Authorization", "Content-Type")
            .AllowCredentials());
    });
```

`Program.cs` 的順序是 `UseCors` 在 `UseAuthentication` 之前：預檢的 `OPTIONS` 不帶 token，要在驗證前就被回應。順序的完整道理在 [[01-request-pipeline]]。參考實作的整合測試鎖住了三件事：允許的 origin 不帶 token 預檢得到 204，其他 origin 拿不到 CORS 標頭，401 回應也帶 CORS 標頭，前端才讀得到錯誤內容。

常見的偷懶是 `AllowAnyOrigin()` 配 `AllowCredentials()`。這等於放棄同源政策的保護，官方文件把它列為不安全的設定，CORS 規範也不允許萬用字元搭配憑證，瀏覽器不會接受這種回應。需要帶 cookie 時，前端的 `withCredentials: true` 和伺服器的明確 origin 要成對出現。

那 Task Tracker 為什麼平常沒遇到？開發時走 Vite proxy：

```ts
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    tsconfigPaths: true,
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET ?? 'http://localhost:5033',
      },
    },
  },
});
```

瀏覽器只看到同源的 `5173`，轉發是伺服器對伺服器，沒有 CORS 的事。正式環境由 Ingress 把前端與 `/api` 掛在同一個網域，也是同源，`AllowedOrigins` 留空即可。CORS 設定只服務真的跨 origin 的情境，例如同事直打 `5033`、或前後端不同網域。選得了同源就選同源，少一次預檢，也少一整類問題。

## 常見誤解

**「axios 比 fetch 安全，不會有非 2xx 的問題。」** axios 確實會 reject，但錯誤處理只是從 `if` 搬到 `catch`。沒有 `toApiError`，每個 catch 還是要猜 `error.response.data` 的形狀，也擋不住 200 配上形狀不對的 body。

**「在 interceptor 裡統一跳出錯誤 toast 最省事。」** 全站一致很誘人，但 client 不知道畫面脈絡：表單的 400 該掛到欄位上，詳情頁的 404 該顯示「找不到」，背景刷新失敗可能根本不該打擾使用者。client 只負責轉換型別，呈現留給呼叫端。

**「Zod 驗回應太慢了。」** 這句話要量過才能說。Task Tracker 的清單是幾十到幾千筆的小物件，相較於網路往返通常不是瓶頸，這是經驗法則。真的要處理巨量回應時，該先問後端為什麼一次回這麼多，第 28 章教怎麼量。

**「CORS 錯誤是前端的 bug，前端要修。」** 決定權在伺服器的回應標頭，前端唯一能做的是改走同源（proxy）。網路上「關掉瀏覽器安全性」的做法只是讓你自己的機器看不到問題。

## 同事會來問你的問題

**「後端明明回了 500，為什麼 Network 分頁看得到 body，程式卻只拿到 Network Error？」** 多半是 500 的回應沒帶 CORS 標頭，瀏覽器不把內容交給 JavaScript。DevTools 顯示的是瀏覽器看到的，JavaScript 看到的是另一回事。先看 console 有沒有 CORS 訊息，再查例外處理路徑上的回應是否帶了標頭。

**「`status` 是 0 是什麼意思？HTTP 沒有 0 啊。」** 那是 `ApiError` 自己的約定，表示沒拿到回應：斷線、逾時、CORS。它讓畫面只需判斷一個數字，不必知道 axios 的 `error.response` 這個細節。

**「Vite 的 env 能不能放 Google Client ID？」** 可以，它本來就是公開識別碼，所以 `VITE_GOOGLE_CLIENT_ID` 存在。Client Secret 不行，它只能留在後端。判斷標準是：這個值被看見會不會出事，因為它一定會被看見。

**「共用的 `Task` 型別要不要從後端 C# 自動產生？」** 有 OpenAPI 時，codegen 可以省掉手寫 schema 並提早發現合約漂移，值得評估，但產出的型別一樣是編譯期承諾，runtime 仍要靠 Zod 或從 OpenAPI 產生的 schema。本書用手寫 schema，機制才看得清楚。

## 本章小結

`fetch` 只對網路失敗 reject，一個請求卻有六種結局，所以呼叫要集中到 `apiClient`，由 interceptor 把各種失敗轉成 `ApiError`，再由 API 函式用 Zod 查核成功的回應。環境變數在 build 時寫死且完全公開，CORS 則是瀏覽器替使用者執行的規則，能同源就同源。但 `useTasks` 仍是每個畫面各存一份資料、各自決定何時重抓，這是封裝層解不了的問題，下一章的 TanStack Query 就從這裡接手。

## 連結

- 上一章：[[react-19-routing]]
- 下一章：[[react-21-server-state]]
- 前置：[[react-03-async-javascript]]、[[react-04-typescript-foundations]]、[[react-11-effects]]、[[react-15-custom-hooks]]、[[react-17-forms]]
- 後續：[[react-22-authentication]]（token 與 refresh interceptor）、[[react-29-build-and-deploy]]（build-time 環境變數的兩難）、[[react-37-frontend-security]]
- 後端對照：[[01-request-pipeline]]（CORS 與 middleware 順序）、[[15-error-handling]]（ProblemDetails）、[[dotnet-web-api]]
