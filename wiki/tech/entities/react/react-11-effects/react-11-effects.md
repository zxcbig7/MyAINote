---
type: concept
domain: tech
tags: [react, useeffect, side-effect, cleanup, race-condition, abortcontroller, useeffectevent, uselayouteffect, strictmode, typescript]
sources:
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
  - raw/Web Framework/React/react-hooks-gotchas/react-hooks-gotchas.md
created: 2026-10-30
updated: 2026-10-30
---

# 第 11 章：Effect — useEffect 什麼時候該用、什麼時候不該用

## 輸入框寫「登入」，清單卻是報表的結果

第 08 章的任務資料還寫死在 `INITIAL_TASKS`。現在要接後端，順便加搜尋框。第 03 章寫過的 `fetchTasks` 多收一個 `q` 參數，完整內容在本章最後。你照著網路上的範例寫：

```tsx
const [query, setQuery] = useState('');
const [tasks, setTasks] = useState<Task[]>([]);

useEffect(() => {
  void fetchTasks({ q: query }).then(setTasks);
}, [query]);
```

（`void` 明確表示這個 Promise 的結果沒有人要接。）開發機上一切正常，部署到測試環境後 QA 回報：搜尋框裡寫著「登入」，清單列的卻是報表相關的任務。你重試五次都正常，第六次又出現。同一天你打開 DevTools 的 Network，發現頁面一載入就有兩筆 `GET /api/tasks`，第一個念頭是有 bug，想加個旗標擋掉。接著同事想把篩選條件包成物件，改成 `const filters = { q: query }` 再把 `filters` 放進依賴陣列，Network 面板的請求從此停不下來。

你把 `[query]` 改成 `[]` 試試，請求不再狂發，但搜尋失效了。這是「試到好」的路：每次改動都在賭，因為你不知道依賴陣列到底在說什麼。本章要回答的問題是：Effect 到底是什麼，什麼時候該用，什麼時候根本不該用？答案會一次解釋這三個症狀。

## 在 render 裡發請求會發生什麼

先從最直覺的寫法開始：既然 component 就是函式，何不直接在函式裡抓資料？

```tsx
const TaskListFetchInRender = (): React.JSX.Element => {
  const [tasks, setTasks] = useState<Task[]>([]);

  void fetchTasks({ q: '' }).then(setTasks);

  return <p>{tasks.length} 筆</p>;
};
```

這段程式會一直打 API。render 發出請求，回應呼叫 `setTasks` 並傳入一個新陣列，第 08 章說過 React 用 `Object.is` 比對，新陣列就是新值，於是再 render 一次，又發出一個請求。第一個回應回來後就開始循環，收到幾個回應就多發幾個請求。

這類「影響函式外部世界」的操作叫 side effect：呼叫 API、改 DOM、設定計時器、訂閱事件、寫 `localStorage`。第 09 章說 component 必須是 pure，相同的 props 與 state 要算出相同的畫面，而且不碰外面的東西。理由也在那裡：React 可能多跑一次 render（StrictMode），也可能跑完就丟棄結果（第 30 章的並行 render）。所以「component 函式執行了」不等於「這個畫面真的上屏了」，更不能當成「某個外部動作只發生一次」的保證。

可是應用程式沒有 side effect 就什麼都做不了。問題於是變成：這些動作該放在哪裡。

## Side effect 該放哪裡：四條規則

| 這個動作的起因 | 放哪裡 |
| --- | --- |
| 任何情況都不放在 | render 期間 |
| 使用者做了某個動作（點擊、送出） | event handler |
| component 出現在畫面上，就要和外部系統保持一致 | `useEffect` |
| 同上，但必須趕在瀏覽器繪製前完成 | `useLayoutEffect` |
| 訂閱外部 store 的值來 render | `useSyncExternalStore`（第 15 章） |

前兩條的分界最常被搞混，判斷方式是問「這段程式碼**為什麼**要跑」。「使用者按了新增，所以送 `POST /api/tasks`」的起因是一次具體的互動，那次互動只發生一次，放 event handler。「任務頁正顯示在畫面上，所以分頁標題要反映未完成數」沒有單一的觸發動作，不管未完成數是因為載入、切換或別人的操作而變，標題都要跟上，這是 Effect 的工作。

搜尋框是個有趣的例子。使用者打字是事件，但「清單要顯示符合 `query` 的任務」是一個同步關係：`query` 可能來自打字，將來也可能來自網址（第 19 章），不論來源，清單都該跟上。所以查詢放 Effect 合理，開場那段程式的位置沒錯，錯在細節。

## useEffect 在 commit 之後才跑，看到的是那次 render 的值

`useEffect` 收兩個參數：一個 setup 函式，和一個依賴陣列。最小的真實例子就是分頁標題：

```tsx
useEffect(() => {
  document.title = `(${todoCount}) Task Tracker`;
}, [todoCount]);
```

setup 不會在 render 當下執行。React 只是把它記下來，等這次 render 的結果 commit 到 DOM 之後才跑，所以 Effect 裡讀得到更新後的 DOM。這正是它存在的理由：把 side effect 移出 render 流程，render 依然 pure。一般情況下瀏覽器會先繪製再跑 Effect，但 React 文件明講，由互動（例如點擊）引起的 Effect 可能在繪製前就跑，所以不要依賴「一定畫完了」這個假設。Effect 也不會在伺服器端渲染時執行，這點第 31 章會用到。

setup 是 render 當中建立的函式，第 08 章的快照規則同樣適用：每次 render 都有自己的一份 `todoCount`，也有自己的一個 setup，閉包抓住的是那次 render 的值。從這個角度看，「Effect 重跑」其實是 React 跑了另一次 render 建立的另一個函式。

setup 的回傳值有規定：只能是 `undefined` 或一個 cleanup 函式。這就是為什麼不能寫 `useEffect(async () => { ... })`：async 函式回傳 Promise。TypeScript 會當場報錯；硬跑的話 React 會在 console 警告 `useEffect must not return anything besides a function`，等 component 卸載時再把那個 Promise 當 cleanup 呼叫，丟出 `destroy is not a function`。需要 `await` 時，在 setup 裡面宣告一個 async 函式再呼叫它，後面的競態處理會看到完整寫法。

## Hook 為什麼只能寫在頂層

有了第二個 Hook 之後，第 08 章預告的規則該講完整了。規則只有兩條：Hook 只能在 function component 或 custom hook（第 15 章）裡呼叫；而且要在頂層呼叫，不放進 `if`、迴圈、event handler，也不放在提前 `return` 之後。最常見的違規長得很無辜：

```tsx
const Page = ({ isLoading }: { isLoading: boolean }): React.JSX.Element => {
  const [title] = useState('任務');
  if (isLoading) {
    return <p>載入中</p>;
  }
  useEffect(() => {
    document.title = title;
  }, [title]);
  return <h1>{title}</h1>;
};
```

`isLoading` 從 `true` 變 `false` 的那次 render，React 丟出 `Rendered more hooks than during the previous render`，整個畫面崩掉。反方向則是 `Rendered fewer hooks than expected`（前面還有其他 Hook 時才偵測得到）。原因是 React 不看 Hook 的名字，只靠呼叫順序把這次的第 N 個 Hook 對上上次存的第 N 筆資料，順序或數量一變就對不上。資料結構的細節在第 36 章，寫 code 時只要記得結論。

修法是讓 Hook 無條件呼叫，把條件搬進 Effect 裡面：

```tsx
useEffect(() => {
  if (!isLoading) {
    document.title = title;
  }
}, [isLoading, title]);

if (isLoading) {
  return <p>載入中</p>;
}
```

這條規則不必靠記憶。`eslint-plugin-react-hooks` 的 `rules-of-hooks` 會報 `React Hook "useEffect" is called conditionally`。第 15 章會介紹的 `use` API 是唯一的例外，它可以寫在條件裡。

## 依賴陣列在描述 Effect 用到什麼

現在來拆開場的第三個症狀。依賴陣列有三種寫法：

| 寫法 | 什麼時候跑 setup |
| --- | --- |
| 不傳 | 每次 commit 後 |
| `[]` | commit 一次（mount）後，之後沒有值會讓它重跑 |
| `[a, b]` | mount 後，以及 `a` 或 `b` 改變的 commit 後 |

React 的比對很單純：把這次的陣列和上次的陣列逐項用 `Object.is` 比，只要有一項不同就重跑。沒有深層比較。

大部分人把這個陣列理解成「我想在這些東西變的時候觸發」，這正是試到好的根源。正確的讀法是：陣列在宣告 **setup 用到了哪些會變的值**。props、state、以及 component 裡由它們算出來的東西都算；`useState` 的 setter 不算，它的參考固定，所以開場的 `setTasks` 不用列。Effect 該不該重跑是由這份宣告推導出來的結果，不該反過來用它控制次數。

如果為了「只想跑一次」把 `query` 拿掉：

```tsx
useEffect(() => {
  void fetchTasks({ q: query }).then(setTasks);
}, []);
```

使用者打再多字都不會發新請求，清單永遠停在 `q` 是空字串的結果，因為這個 Effect 從頭到尾只用第一次 render 的 `query`。計時器也會出同樣的事：

```tsx
useEffect(() => {
  const timerId = window.setInterval(() => {
    setRefreshCount(refreshCount + 1);
  }, 1000);
  return () => {
    window.clearInterval(timerId);
  };
}, []);
```

畫面顯示 1 就不再動。計時器確實每秒都在跑，但每次讀到的 `refreshCount` 都是第一次 render 的 0，每次都算出 1。這裡不想讓計時器隨 `refreshCount` 重建，正解是第 08 章的 updater：`setRefreshCount((prev) => prev + 1)`，讓 Effect 根本不必讀這個值。漏列依賴時先問：這個 Effect 真的需要讀它嗎？`exhaustive-deps` 規則會抓這類問題，訊息是 `React Hook useEffect has a missing dependency`。Vite 模板預設的 Oxlint 也有同名規則。

### 物件和函式為什麼讓 Effect 停不下來

再看同事的改動：

```tsx
const filters = { q: query };

useEffect(() => {
  void fetchTasks(filters).then(setTasks);
}, [filters]);
```

依賴陣列沒有說謊，`filters` 確實被用到了。但 component 每次 render 都會建立一個新物件，`Object.is` 比參考，內容一樣也算不同。走一遍流程：Effect 發請求，回應呼叫 `setTasks`，觸發 render，產生新的 `filters`，Effect 重跑，又發一個請求。這個循環不會丟任何錯誤，只有 Network 面板和後端的 log 看得出來，因為每一輪都隔了一段網路等待。如果 setter 是同步呼叫（Effect 裡直接 `setX`，不等請求），才會在 console 看到 `Maximum update depth exceeded` 的警告，而且它只是警告，迴圈不會自己停。

修法是讓依賴回到原始值，把物件搬進 Effect：

```tsx
useEffect(() => {
  const filters = { q: query };
  void fetchTasks(filters).then(setTasks);
}, [query]);
```

函式是同樣的問題，因為 component 內宣告的函式每次 render 都是新的。lint 訊息會直接告訴你：`The 'load' function makes the dependencies of useEffect Hook change on every render`。依序考慮三個解法：

- 函式完全不讀 props 或 state：搬到 component 外面，它就不再是會變的值。
- 函式只有這個 Effect 在用：搬進 Effect 裡面，這是多數情況的答案。
- 其他地方也要用，而且讀了 props 或 state：用 `useCallback` 固定參考（第 14 章），再把它放進依賴。

```tsx
const loadTasks = useCallback(() => fetchTasks({ q: query }), [query]);

useEffect(() => {
  void loadTasks().then(setTasks);
}, [loadTasks]);
```

`// eslint-disable-line react-hooks/exhaustive-deps` 不在清單上。它只把症狀藏起來，留下一個讀舊值的 Effect，而且之後這個 Effect 新增的依賴也不會再有人提醒。

### 函式宣告在 Effect 之後

把 handler 寫在 Effect 下面，新版外掛會報一個讓人困惑的錯：

```text
react-hooks/immutability: `handleSync` is accessed before it is declared
```

第 02 章講過 hoisting：`function` 宣告會整個提升，`const` 箭頭函式在宣告前是暫時性死區，直接呼叫會丟 `ReferenceError`。但 Effect 的情況有點不同。setup 要等 render 跑完才執行，那時 `const` 早就初始化了，所以下面這段在 runtime 完全正常，用 `function` 或 `const` 都會被同一條規則擋下：

```tsx
useEffect(() => {
  handleSync();
}, []);
const handleSync = (): void => {
  void fetchTasks({ q: '' });
};
```

規則在意的不是會不會當掉，而是閱讀順序和依賴分析：規則訊息說明，提前讀取會讓前面的存取無法隨值變化而更新。修法很簡單：函式放到 Effect 之前，或者更好的做法是把邏輯直接寫進 Effect。

## Effect 是同步，不是生命週期

依賴陣列講完，Effect 的另一半是回傳值。從 class component 時代留下的說法是「`useEffect` 就是 `componentDidMount` 加 `componentDidUnmount`」，這個模型會一直誤導你，因為它讓人以為 cleanup 只在卸載時跑。看一個會變動設定的計時器：

```tsx
interface AutoRefreshBadgeProps {
  intervalMs: number;
}

export const AutoRefreshBadge = ({ intervalMs }: AutoRefreshBadgeProps): React.JSX.Element => {
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    const timerId = window.setInterval(() => {
      setRefreshCount((prev) => prev + 1);
    }, intervalMs);

    return () => {
      window.clearInterval(timerId);
    };
  }, [intervalMs]);

  return <p>已自動刷新 {refreshCount} 次</p>;
};
```

`intervalMs` 從 1000 改成 500 時，React 先跑舊的 cleanup，再跑新的 setup，任何時刻都只有一個計時器。完整順序是：

```text
render(1000) → commit → setup(1000)
render(500) → commit → cleanup(1000) → setup(500)
卸載 → cleanup(500)
```

注意 `cleanup(1000)` 用的是舊值：cleanup 也是那次 render 的閉包，它要清掉的正是當初自己建立的東西。

所以該用的模型是：一個 Effect 描述「當這些值是這樣時，外部世界要處於某個狀態」，setup 建立，cleanup 撤銷，值一變就撤銷重建。你只需要寫好一對可逆的操作，不用管現在是第一次還是第五次，也不用管是 mount 還是更新。

後端讀者可以把 setup 和 cleanup 想成 `using` 的取得與 `Dispose`：資源的範圍有明確的開始與結束。類比破在範圍由誰決定：`using` 的範圍是你的程式碼區塊，Effect 的範圍由 React 依依賴變化決定，可能開關很多次，所以 setup 不能假設自己只跑一次。

少了 cleanup 的症狀通常很晚才被發現。假設按 Escape 要清除目前的篩選：

```tsx
useEffect(() => {
  const handleKeyDown = (event: KeyboardEvent): void => {
    if (event.key === 'Escape') {
      onEscape(filter);
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => {
    window.removeEventListener('keydown', handleKeyDown);
  };
}, [filter, onEscape]);
```

拿掉 `return` 那段，`filter` 依序變成 `all`、`todo`、`done` 之後，按一次 Escape，`onEscape` 被呼叫三次，分別帶著三個不同的舊 `filter`；連 component 卸載了，這些 listener 還在 `window` 上繼續觸發。使用者看到的是「篩選偶爾跳回之前的值」，很難從畫面追回這段程式碼。

## 開發環境為什麼每個請求都發兩次

這就是開場的第二個症狀。用 `<StrictMode>` 包住的 component，在 development 模式下 mount 時，Effect 的順序是：

```text
setup → cleanup → setup
```

React 刻意假裝卸載再重新掛載一次，production 不會這樣做。第 09 章講過 StrictMode 的雙重 render 是在檢查 purity；這裡的雙重 Effect 在檢查另一件事：你的 cleanup 寫對了沒。因為真實世界裡同一個 component 確實可能重新掛載，例如 `key` 改變（第 09 章）或 `<Activity>` 隱藏再顯示（第 30 章）。如果一輪 setup → cleanup → setup 之後的結果和只跑一次不同，那就是個遲早會在 production 出現的 bug，前一節的 listener 累積就是例子。

所以看到兩筆請求，正確反應是確認 cleanup 有把第一筆處理掉，然後放著不管。常見的錯誤反應是用 ref 擋：

```tsx
const hasStarted = useRef(false);

useEffect(() => {
  if (hasStarted.current) return;
  hasStarted.current = true;
  const controller = new AbortController();
  void loadFirstPage(controller.signal);
  return () => {
    controller.abort();
  };
}, []);
```

`useRef` 第 12 章才細講，這裡只要知道它的值跨 render 保留，也撐得過 StrictMode 這次假卸載。這段程式在開發環境會讓畫面永遠停在載入中：第一次 setup 發請求，cleanup 把它 abort，第二次 setup 被 guard 擋下，唯一的請求已經取消，再也沒有人發新的。guard 把 StrictMode 想幫你抓的問題變成了真正的 bug。它也擋不住真正的 remount，新的實例會拿到新的 ref，動作照樣再跑一次。

那真的只能執行一次的動作呢？例如 Google 登入導回後，用網址上的 authorization code 換 token，這個 code 只能用一次。這種情況有兩層防護。前端用**模組層級**的旗標，它活得比 component 實例久，真正的 remount 也擋得住：

```tsx
let didExchangeCode = false;

const AuthCallback = (): React.JSX.Element => {
  useEffect(() => {
    if (didExchangeCode) return;
    didExchangeCode = true;
    void exchangeCode();
  }, []);

  return <p>登入中</p>;
};
```

後端則要把重複的請求當成必然會發生的事來設計，也就是 API 要有冪等性。前端的旗標管不到重新整理頁面、網路重送或另一個分頁。完整流程在第 22 章。

## 輸入框和清單對不上：競態

終於回到開場的第一個症狀。把事情排成時間線：

```text
t0 輸入「報表」，送出 R1
t1 改成「登入」，送出 R2
t2 R2 回來：setTasks(登入的結果)，畫面正確
t3 R1 才回來：setTasks(報表的結果)，畫面被蓋掉
```

網路不保證回應順序。R1 可能剛好查到慢的 Oracle 執行計畫，R2 走了快取。「重試五次都正常」也因此說得通：只有回應順序顛倒時才會出現，開發機上 API 延遲都差不多，所以很少碰到。

機制上的修法前面都鋪好了。`query` 改變時，React 會先跑上一個 Effect 的 cleanup，所以 cleanup 正好是告訴舊請求「你已經過期」的地方：

```tsx
useEffect(() => {
  let isStale = false;

  void fetchTasks({ q: query }).then((data) => {
    if (!isStale) {
      setTasks(data);
    }
  });

  return () => {
    isStale = true;
  };
}, [query]);
```

每次 Effect 都有自己的 `isStale`，舊 Effect 的回應回來時，它閉包裡的 `isStale` 已經被自己的 cleanup 改成 `true`，於是結果被丟掉。這樣畫面就對了，但舊請求還在跑，白白占著連線和伺服器資源。第 03 章的 `AbortController` 能把它真正取消，而它的 `signal` 同時可以取代 `isStale` 旗標：

```tsx
useEffect(() => {
  const controller = new AbortController();
  const { signal } = controller;

  const load = async (): Promise<void> => {
    try {
      const data = await fetchTasks({ q: query }, signal);
      if (!signal.aborted) {
        setLoaded({ query, result: { status: 'success', data } });
      }
    } catch (error: unknown) {
      if (!signal.aborted) {
        const message = error instanceof Error ? error.message : '發生未知錯誤';
        setLoaded({ query, result: { status: 'error', message } });
      }
    }
  };

  void load();

  return () => {
    controller.abort();
  };
}, [query]);
```

有兩個細節要慢慢看。第一，`abort()` 讓進行中的 `fetch` 以 `AbortError` reject，這是我們自己取消的，不算失敗，所以 `catch` 要先看 `signal.aborted`，否則每次改搜尋，畫面都會閃一下錯誤訊息。第二，`try` 裡的 `signal.aborted` 檢查看起來多餘，既然取消了不就會進 `catch`？但 `abort()` 只能打斷還在進行中的工作。如果底層函式沒有把 `signal` 傳下去（例如換成某個不支援取消的 SDK），或者資料已經拿到、後續的 Promise 還沒輪到執行，就不會 reject。這行檢查不依賴底層函式的配合，所以兩條路都留著。

開場提到的第二個症狀現在也有了完整解釋：StrictMode 下第一筆請求被第一次 cleanup abort，Network 面板會看到一筆 canceled，第二筆正常回來，畫面只更新一次，而且 production 只會有一筆。

後端讀者會立刻想到 `CancellationToken`，對應確實很直接：`AbortSignal` 是 token，`AbortController` 是 `CancellationTokenSource`。這個類比破在跨網路的那段。前端 abort 只是關閉這一方的請求，ASP.NET Core 要把 `HttpContext.RequestAborted` 一路傳給 Oracle 的查詢才會真的停下來；就算傳了，伺服器也可能早已處理完。所以取消是前端的生命週期管理，不代表後端的動作沒發生。`POST` 被 abort 之後，資料可能已經寫進去了。

### loading 不用另外存

來源筆記和網路範例常見的寫法，是在 Effect 開頭 `setIsLoading(true)`。新版外掛的 `set-state-in-effect` 會把它標成錯誤（Effect 內同步呼叫 setState），訊息是 `Calling setState synchronously within an effect can trigger cascading renders`。問題不只是多 render 一次。因為 Effect 在 commit 之後才跑，`query` 剛改變的第一次 commit 裡 `isLoading` 還是 `false`，那一幀畫面會是新的搜尋字配舊的結果。

上面的程式碼把結果和它對應的 `query` 存在一起，loading 就可以從 render 算出來：

```tsx
const remote: RemoteData<Task[]> = loaded?.query === query ? loaded.result : { status: 'loading' };
```

存的結果不屬於目前的 `query`，就是還在載入。`query` 一變，同一次 render 就顯示載入中，舊結果不會多留一幀。`RemoteData` 是第 05 章的 discriminated union，`loaded` 的型別在本章最後。外掛只抓 setup 本體內的同步呼叫，`await` 或 `.then` 之後再 setState 不會被標記，因為那時確實是外部系統回應了。

每打一個字都發請求是另一個問題，取消只是讓它不出錯，第 15 章的 `useDebounce` 才會減少請求量。

## 很多 Effect 根本不該存在

學會 Effect 之後最常見的毛病是到處用它。判斷準則還是那句話：有沒有外部系統？如果沒有，通常不需要 Effect。以下四種情況都是 Task Tracker 裡會自然寫出來的。

**衍生資料。** 第 08 章用過 `tasks.filter(...)` 在 render 計算 `visibleTasks`，有人會改成 state 加 Effect：

```tsx
const [visibleTasks, setVisibleTasks] = useState<Task[]>([]);

useEffect(() => {
  setVisibleTasks(filter === 'all' ? tasks : tasks.filter((task) => task.status === filter));
}, [tasks, filter]);
```

切換篩選時，component 先用新的 `filter` 和舊的 `visibleTasks` render 並 commit，Effect 跑完才再 render 一次。多了一次 render，還多了一個新舊不一致的中間畫面。直接在 render 裡算就沒有這些問題；算得慢才考慮第 14 章的 `useMemo`。

**prop 改變時重置 state。** 第 08 章留了個問題：行內編輯切到另一筆任務時，草稿要重來。用 Effect 寫是這樣：

```tsx
const [draft, setDraft] = useState(task.title);

useEffect(() => {
  setDraft(task.title);
}, [task]);
```

從任務 A 切到 B，第一次 render 拿到的是任務 B 配上 A 的草稿，等 Effect 跑完才修正。如果這個 component 在這段空檔做了任何事（例如存檔），就會把 A 的標題寫到 B 身上。而且 `[task]` 比對的是物件參考，後端刷新資料帶來新物件時，使用者打到一半的草稿也會被蓋掉。正解是第 09 章的 `key`：`<TaskTitleEditor key={task.id} task={task} />`，換任務就是換實例，state 從新的初始值開始，只 render 一次，也沒有中間狀態。

**事件邏輯。** 第 08 章提到不要用 Effect 監看 `tasks` 來顯示提示：

```tsx
useEffect(() => {
  if (tasks.length > 0) {
    setNotice(`已新增，目前共 ${tasks.length} 筆任務`);
  }
}, [tasks]);
```

現在任務從 API 載入，問題變得明顯：頁面一打開提示就跳出來，使用者勾選完成也跳「已新增」。Effect 只知道 `tasks` 變了，不知道為什麼變。「使用者按了新增」這個資訊只存在於 handler，所以邏輯要留在那裡。同樣的道理，把 `POST` 寫成「`isSubmitted` 變 `true` 時發送」的 Effect，等於把一個事件拆成兩段，還要處理 StrictMode 重跑和重設旗標的問題。

**通知 parent 或串接多個 state。** 用 Effect 在 state 改變後呼叫 `onChange`，parent 收到時 child 已經 commit 過一次，多一輪 render；在 handler 裡同時呼叫 `setX` 和 `onChange`，第 08 章的 batching 會把它們併成一次。把 A 變了設 B、B 變了設 C 串成 Effect 鏈也一樣，每一環都多一次 commit，用 handler 或衍生值就能在一次 render 內算完。

這些情況大多會被 `set-state-in-effect` 抓到，它不用安裝 React Compiler 就能用，這也是第 43 章建議開啟的理由之一。

**資料抓取呢？** 這是真正的外部系統，Effect 放得合理，本章的寫法也能正確運作。但它只解決了「同步」，沒有快取，切回頁面要重抓；兩個 component 要同一份資料就發兩個請求；也沒有重試與背景更新。第 21 章的 TanStack Query 會接手這些，內部同樣要處理本章的取消與過期問題。

## Effect 裡有一段不想被依賴牽著走：useEffectEvent

還有一種情況是前面的工具都解不了的。看板要連上後端的通知 channel（第 38 章會換成真正的 SignalR），收到訊息就顯示；使用者可以切換靜音。先把連線抽象成兩個方法：

```ts
export interface BoardChannel {
  onMessage: (listener: (message: string) => void) => void;
  close: () => void;
}
```

`connect` 從 props 傳入，它接收 `boardId` 回傳一個 `BoardChannel`。第一版照規則列依賴：

```tsx
useEffect(() => {
  const channel = connect(boardId);
  channel.onMessage((message) => {
    if (!isMuted) {
      setLatest(message);
    }
  });
  return () => {
    channel.close();
  };
}, [boardId, isMuted, connect]);
```

行為正確，但切換靜音就會斷線重連一次，重連的空檔可能漏掉訊息。靜音只是使用者偏好，和連到哪個看板無關。於是有人把 `isMuted` 從依賴拿掉，連線是穩了，但 listener 閉包抓住第一次 render 的 `isMuted`，開了靜音訊息照樣顯示。

矛盾的來源是這個 Effect 裡混了兩種邏輯。「連到哪個看板」是同步，應該隨 `boardId` 重跑。「收到訊息時怎麼處理」是一個事件，它從 Effect 裡被觸發，需要讀最新的值，但讀到的值不該讓連線重建。React 19.2 起穩定的 `useEffectEvent` 就是把後者拆出來：

```tsx
const onMessage = useEffectEvent((message: string): void => {
  if (!isMuted) {
    setLatest(message);
  }
});

useEffect(() => {
  const channel = connect(boardId);
  channel.onMessage(onMessage);
  return () => {
    channel.close();
  };
}, [boardId, connect]);
```

切換靜音不會重連，訊息進來時讀到的是最新的 `isMuted`；換 `boardId` 才會重連。這也是第 08 章留下的問題的答案之一：在長壽的 Effect 閉包裡讀到最新值。

它的限制來自這個定位：只能從同一個 component 或 Hook 內的 Effect（或其他 Effect Event）呼叫，不能當 `onClick` 也不能傳給 child，lint 會直接報錯；不放進依賴陣列，放了 lint 也會提醒移除。最重要的一條在 lint 抓不到的地方：不要用它消除依賴警告。如果 `boardId` 被包進 Effect Event 裡，切換看板時連線不會跟著換，這就是把該同步的東西藏起來了。判斷方式回到老問題：這個值變了，連線這個外部狀態應該跟著變嗎？應該就列依賴，不應該才放進 Effect Event。

## 必須搶在繪製前：useLayoutEffect 與 useInsertionEffect

到期日提示要顯示在任務上方，空間不夠就翻到下方。可是提示的高度要等 DOM 出來才量得到。用 `useEffect` 的話，使用者可能先看到提示畫在上方（被裁掉），下一幀才跳到下方，這就是閃爍。`useLayoutEffect` 的寫法完全相同，時機在 DOM 更新後、瀏覽器繪製前，裡面的 setState 也會同步處理：

```tsx
interface DueDateHintProps {
  dueDate: string;
  anchorTop: number;
}

export const DueDateHint = ({ dueDate, anchorTop }: DueDateHintProps): React.JSX.Element => {
  const hintRef = useRef<HTMLDivElement>(null);
  const [placement, setPlacement] = useState<'above' | 'below'>('above');

  useLayoutEffect(() => {
    const hint = hintRef.current;
    if (hint !== null) {
      const { height } = hint.getBoundingClientRect();
      setPlacement(anchorTop < height ? 'below' : 'above');
    }
  }, [anchorTop, dueDate]);

  return (
    <div ref={hintRef} data-placement={placement}>
      到期：{dueDate}
    </div>
  );
};
```

`hintRef` 拿到的是 DOM 節點，第 12 章會細講。流程是：React 更新 DOM，跑 layout Effect 讀到高度，設定 `placement`，同步重新 render，然後瀏覽器才繪製修正後的結果，使用者從頭到尾只看到正確的位置。這裡的 setState 不會被 `set-state-in-effect` 標記，因為值來自 DOM 量測，這是這條規則承認的合法用途。

代價是它和裡面排程的更新會擋住瀏覽器繪製，寫得慢就直接造成卡頓，所以只在「不這樣做就會閃」時才用，其他一律 `useEffect`。伺服器端沒有 layout 可以量，這類量測只能發生在 client。這個範例也只在 `anchorTop` 或 `dueDate` 改變時重新量，視窗縮放造成的尺寸變化要另外訂閱。

`useInsertionEffect` 更早，在 layout Effect 之前跑，存在的目的只有一個：讓 CSS-in-JS 函式庫趕在任何 layout Effect 量測 DOM 之前把樣式插入。你大概不會親手寫它，但在函式庫原始碼裡看到時，形狀是這樣：

```tsx
export const useInjectedColor = (className: string, color: string): void => {
  useInsertionEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = `.${className} { color: ${color}; }`;
    document.head.appendChild(styleElement);

    return () => {
      styleElement.remove();
    };
  }, [className, color]);
};
```

這時 ref 還沒掛上，裡面呼叫 setState 會得到 `useInsertionEffect must not schedule updates` 的警告。一般產品要換顏色，用 class 或 `style` prop 就好。三者並列如下，順序指同一次 commit：

| Hook | 時機 | 讀得到 ref | 可否 setState | 給誰用 |
| --- | --- | --- | --- | --- |
| `useInsertionEffect` | 最早，layout Effect 之前 | 否 | 否 | CSS-in-JS 函式庫 |
| `useLayoutEffect` | DOM 更新後，繪製前，同步 | 是 | 可，同步重 render | 量測 DOM、避免閃爍 |
| `useEffect` | 通常繪製後 | 是 | 可 | 其他所有同步需求 |

有個細節：layout Effect 裡 setState 時，React 會先把這次 commit 尚未執行的 `useEffect` 跑完，再重新 render。所以 `useEffect` 可能先看到量測前的值，再隨新的 commit 重跑一次。

## 把 Task Tracker 接上 API

這一章 Task Tracker 只動兩個檔。`fetchTasks` 把第 03 章的版本加上 `q`。非 2xx 轉成 throw 是必要的（`fetch` 本身不會 reject，第 20 章會細談），回傳值暫時直接相信後端，第 20 章再用 Zod 守邊界：

```ts
import type { Task } from './types';

export interface TaskQuery {
  q: string;
}

export const fetchTasks = async ({ q }: TaskQuery, signal?: AbortSignal): Promise<Task[]> => {
  const response = await fetch(`/api/tasks?q=${encodeURIComponent(q)}`, { signal });
  if (!response.ok) {
    throw new Error(`載入任務失敗，HTTP ${response.status}`);
  }
  const data: Task[] = await response.json();
  return data;
};
```

`TasksPage` 有三個決定。伺服器端查詢（`query`）進 Effect，狀態篩選（`filter`）依然是 render 裡的衍生值，因為資料已經在手上，不需要再問後端。其次，`tasks` 不再是獨立的 state，改從 `loaded` 算出，也就是前一節的設計，所以新增與切換要透過 `updateTasks` 改 `loaded` 裡的資料。第三，分頁標題是一個獨立的 Effect，一個 Effect 只同步一件事，它和查詢沒有共同的依賴，放在一起只會讓標題改變時多發請求。搜尋的 Effect 內容就是競態那節的版本，以下省略不重貼：

```tsx
interface LoadedTasks {
  query: string;
  result: RemoteData<Task[]>;
}

export const TasksPage = (): React.JSX.Element => {
  const [query, setQuery] = useState('');
  const [loaded, setLoaded] = useState<LoadedTasks | null>(null);
  const [filter, setFilter] = useState<TaskFilter>('all');
  const [lastAddedTitle, setLastAddedTitle] = useState<string | null>(null);

  // 這裡是競態那節的搜尋 Effect

  const remote: RemoteData<Task[]> = loaded?.query === query ? loaded.result : { status: 'loading' };
  const tasks = remote.status === 'success' ? remote.data : [];
  const visibleTasks = filter === 'all' ? tasks : tasks.filter((task) => task.status === filter);
  const todoCount = tasks.filter((task) => task.status !== 'done').length;

  useEffect(() => {
    document.title = `(${todoCount}) Task Tracker`;
  }, [todoCount]);

  const updateTasks = (update: (prev: Task[]) => Task[]): void => {
    setLoaded((prev) =>
      prev?.result.status === 'success'
        ? { ...prev, result: { status: 'success', data: update(prev.result.data) } }
        : prev,
    );
  };

  const handleAdd = (title: string): void => {
    const task = createTask(title);
    updateTasks((prev) => addTask(prev, task));
    setLastAddedTitle(title);
  };

  const handleToggle = (id: string): void => {
    updateTasks((prev) => toggleTask(prev, id));
  };

  return (
    <TaskBoard title="任務">
      <TaskForm onAdd={handleAdd} />
      <label>
        搜尋
        <input value={query} onChange={(event) => setQuery(event.target.value)} />
      </label>
      <TaskFilterBar filter={filter} onFilterChange={setFilter} />
      {lastAddedTitle !== null && <p role="status">已新增「{lastAddedTitle}」</p>}
      {remote.status === 'loading' && <p>載入中</p>}
      {remote.status === 'error' && <p role="alert">{remote.message}</p>}
      {remote.status === 'success' && <TaskList tasks={visibleTasks} onToggle={handleToggle} />}
    </TaskBoard>
  );
};
```

這個版本有兩個刻意留著的缺口。新增與切換還只改前端記憶體，換個搜尋字串重新查詢就消失，要等第 20 章的寫入 API。載入期間 `tasks` 是空陣列，分頁標題會短暫顯示 `(0)`。把伺服器資料放進 `useState` 的彆扭感，例如 `updateTasks` 這種手工維護，正是第 21 章要解決的。

## Effect 出事時怎麼推理

遇到問題先別動依賴陣列，從症狀找原因：

| 症狀 | 先問 | 通常的根因與修法 |
| --- | --- | --- |
| 請求或 render 停不下來 | 依賴裡有沒有 render 中新建的物件或函式？Effect 是否設定了自己依賴的 state？ | 搬進 Effect 或改用原始值；衍生值不存 state |
| Effect 裡的值一直是舊的 | 依賴是否漏列？ | 補依賴；寫 state 改 updater；只是要讀最新值用 `useEffectEvent` |
| 開發環境兩次、production 一次 | cleanup 是否完整？ | StrictMode 的正常行為，補 cleanup，不要加 guard |
| 畫面偶爾是舊查詢的結果 | 有沒有 cleanup 讓舊回應失效？ | `AbortController` 加 `signal.aborted` 檢查 |
| 動作觸發次數愈來愈多 | 每個訂閱有沒有對應的取消？ | cleanup 移除 listener、計時器、連線 |
| 切換時閃過錯的內容 | 是不是用 Effect 同步 state？ | 改衍生值或 `key` |
| 版面閃一下才到位 | 是否在 `useEffect` 量測 DOM？ | 換 `useLayoutEffect` |
| `Rendered more hooks` | Hook 有沒有放在提前 return 之後？ | Hook 移到頂層，條件搬進 Effect |

## 常見誤解

**「Effect 裡完全不能呼叫 setState。」** `set-state-in-effect` 的名字讓人這樣以為，但它抓的是 setup 本體內的同步呼叫。訂閱或請求的回呼裡呼叫 setter，是外部系統把變化告訴 React，正是 Effect 的正常用法；前面的 `useLayoutEffect` 也示範了依 DOM 量測結果設定 state 是被允許的。

**「只要 production 沒有雙跑，cleanup 寫不好也沒關係。」** StrictMode 只是把問題提早暴露。production 一樣會有依賴改變造成的重新同步、`key` 造成的 remount，`<Activity>` 隱藏時也會執行 cleanup，顯示時再跑 setup。不完整的 cleanup 在這些時刻都會出事，而且不像開發環境那樣每次都能重現。

**「`useEffectEvent` 就是不用寫依賴的 `useCallback`。」** 兩者解的是不同問題。`useCallback` 回傳的函式可以傳給 child，參考在依賴不變時固定；Effect Event 不能傳給 child，也不該假設它的參考固定，所以它只能活在 Effect 旁邊。需要穩定 callback 給 `memo` child 時，第 14 章的工具才對。

**「`useLayoutEffect` 比較早跑，全換掉比較保險。」** 早跑的代價是擋住繪製。把資料請求或大量計算放進去，使用者看到畫面的時間就直接被拖慢。`useEffect` 是預設值，`useLayoutEffect` 是有閃爍問題才換的例外。

**「取消了請求，後端就沒做這件事。」** 前面講過 `AbortController` 管的是前端這一側。這個誤解最危險的地方在寫入操作：使用者按了取消上傳，資料庫裡可能已經有這筆資料，UI 要告訴使用者的是「不確定」，並由 API 的冪等設計收尾。

## 同事會來問你的問題

**「Network 裡同一個 API 打兩次，是不是要加 flag 擋？」** 先確認這是 development 且有 `<StrictMode>`，那是 React 刻意跑 setup → cleanup → setup 來檢查 cleanup。正確處理後第一筆會顯示 canceled，production 只有一筆。加 ref 擋的話，搭配 abort 的 cleanup 會把唯一的請求取消，畫面卡在載入中。production 也出現兩筆才是真的 bug，通常是兩個 component 各抓一次，或依賴在 mount 後又變了。

**「lint 叫我把這個函式加進依賴，加了就無限迴圈，怎麼辦？」** 函式每次 render 都是新參考，加進去 Effect 就每次重跑，如果它又設了 state 就形成循環。lint 指出的問題是對的，只是修法不是把它關掉。函式只有這個 Effect 用就搬進去，不讀 props 或 state 就搬到 component 外，都不行才用 `useCallback`。

**「cleanup 裡讀到的 state 為什麼是舊的，是不是 bug？」** 不是。cleanup 是舊 render 建立的閉包，它讀到那次 render 的值，這正是它能正確撤銷自己當初設定的原因：`roomId` 從 A 換到 B 時，cleanup 需要斷開的是 A。如果需要最新值，那件事可能本來就該放在下一次 setup。

**「送出表單要不要放 Effect，這樣寫 loading 比較方便？」** 不要。送出的起因是一次使用者動作，放 handler。放 Effect 就要多一個 `isSubmitted` 旗標當觸發器，還得處理重設、StrictMode 重跑以及重複送出，一個 `POST` 被送兩次可是真實的資料問題。第 17 章有表單送出中狀態的完整做法。

**「那大家為什麼說不要用 useEffect 抓資料？」** 這句話指的是別自己維護整套機制，用 Effect 抓資料本身沒有錯，也是理解下一層工具的基礎。本章處理了同步與競態，但快取、去重、重試、背景更新都還沒有，把它們一一補上就等於自己寫一個資料函式庫。第 21 章的 TanStack Query 已經做好了，一般專案用它。

## 本章小結

Effect 用來讓 component 和外部系統保持同步，setup 建立、cleanup 撤銷，值一變就撤銷重建，所以依賴陣列要誠實列出用到的值，而不是用來控制執行次數。開場的三個症狀都有了解釋：競態靠 cleanup 讓舊請求失效，兩筆請求是 StrictMode 在檢查 cleanup，停不下來的請求是物件參考每次都變。沒有外部系統就不需要 Effect，衍生值在 render 算，事件邏輯留在 handler，重置 state 用 `key`。不過 `AutoRefreshBadge` 這類需求還留著一個問題：計時器 id、DOM 節點這種東西要跨 render 記住，改了卻不該觸發 render，該放哪裡？第 12 章的 ref 回答這件事。

## 連結

- [[react-10-tic-tac-toe]] — 上一章：把核心模型組起來的實作
- [[react-12-refs]] — 下一章：跨 render 記住但不觸發 render 的值
- [[react-03-async-javascript]] — Promise、async/await 與 `AbortController`
- [[react-02-javascript-for-react]] — closure 與 hoisting
- [[react-08-state]] — 快照、updater、衍生值不存 state
- [[react-09-rendering]] — render 與 commit、`key`、StrictMode 雙重 render
- [[react-14-memoization]] — `useCallback`、`useMemo` 何時值得加
- [[react-15-custom-hooks]] — `useDebounce`、`useSyncExternalStore`
- [[react-21-server-state]] — 用 TanStack Query 接手資料抓取
- [[react-22-authentication]] — 一次性的 authorization code 交換
- [[react-36-react-internals]] — Hook 順序規則的資料結構由來
- [[01-request-pipeline]] — ASP.NET Core 的 request pipeline
