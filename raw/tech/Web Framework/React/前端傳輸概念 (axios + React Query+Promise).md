# 前端傳輸概念 (axios + React Query+Promise)

## axios + React Query

### 先理解各自的職責

> **兩者的關係用一句話說**
React Query 負責「管理資料的生命週期」，axios 負責「實際去打 API」。
React Query 自己不打 API，它需要你告訴它「用什麼方法去拿資料」，而你就把 axios 塞進去。
> 

**`axios` ：**發送「 HTTP 請求」

**`React Query` ：**管理「這筆資料的狀態」，包含 loading、error、快取、自動更新

```tsx
// axios 只做這件事，打 API 拿資料
const response = await axios.get('/users');
```

### 只用 axios 會遇到的問題

每次打 API，你都要自己寫這些：

```tsx
const [users, setUsers] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

useEffect(() => {
  setLoading(true);
  axios.get('/users')
    .then(res => {
      setUsers(res.data);
      setLoading(false);
    })
    .catch(err => {
      setError(err);
      setLoading(false);
    });
}, []);
```

每一支 API 都要重複寫 `loading`、`error`、`useState`、`useEffect`，非常累。

而且還有更多問題沒解決：

- 使用者切換頁面又回來，要不要重新打 API？
- 同一支 API 在兩個元件都需要，會發送兩次請求嗎？
- 資料更新後，其他地方的資料怎麼同步？

---

### 加上 React Query 之後

React Query 把上面那一大段，變成這樣：

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['users'],       // 這筆資料的名字 (key)
  queryFn: () => axios.get('/users').then(res => res.data)  // 怎麼拿資料
});
```

三行解決，而且自動幫你處理：

| 問題 | React Query 怎麼處理 |
| --- | --- |
| loading 狀態 | `isLoading` 自動給你 |
| error 狀態 | `error` 自動給你 |
| 重複請求 | 同一個 key，只發一次 |
| 快取 | 資料暫存，切頁面回來不重打 |
| 背景自動更新 | 視窗重新 focus 自動刷新 |

---

---

### 一個完整的實際範例

```tsx
// 1. 建立 axios instance (統一設定)
const api = axios.create({
  baseURL: 'https://your-api.com',
  headers: { 'Content-Type': 'application/json' }
});

// 2. 用 React Query 呼叫
function UserList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then(res => res.data)
  });

  if (isLoading) return <p>載入中...</p>;
  if (error) return <p>發生錯誤</p>;

  return (
    <ul>
      {data.map(user => <li key={user.id}>{user.name}</li>)}
    </ul>
  );
}
```

你會發現元件裡完全沒有 `useState`、`useEffect`，程式碼乾淨很多。

### 總結

單純用 `axios` 可以運作，但你要自己管理所有狀態。加上 `React Query` 之後，axios 繼續做它最擅長的事 (發請求)，React Query 接管所有狀態管理的工作，兩者分工明確，這就是這個組合的意義。

---

# Promise 概念

> 
> 
> 
> JavaScript 是單執行緒的，一次只能做一件事。但有些操作很慢，例如打 API、讀檔案，如果等它完成才繼續，畫面就會卡住。
> 所以 JS 用 Promise 的非同步方式處理，意思是「你先去做，做完再告訴我」的機制。
> 

## Promise 是什麼

> Promise 是一個「未來會完成的工作」的容器，它代表一個現在還不知道結果，但未來會有結果的操作。
> 

Promise 有三種狀態，狀態只會從 Pending 變成其中一種，而且**不可逆**。

```
- Pending (等待中) →  還在執行
- Fulfilled (成功) →  拿到結果
- Rejected  (失敗) →  發生錯誤
```

## 最基本的 Promise 寫法

```tsx
const myPromise = new Promise<string>((resolve, reject) => {
  const success = true;

  if (success) {
    resolve('拿到資料了');   // 成功，進入 Fulfilled
  } else {
    reject('發生錯誤');      // 失敗，進入 Rejected
  }
});
```

## 三種使用 Promise 的寫法

### 寫法 1，`.then().catch()` 鏈式寫法 (舊式)

```tsx
axios.get('/users')
  .then(response => {
    console.log(response.data);   // 成功
  })
  .catch(error => {
    console.log(error);           // 失敗
  })
  .finally(() => {
    console.log('不管成功失敗都會執行');
  });
```

### 寫法 2，`async/await` (現代主流，最推薦)

```tsx
async function getUsers() {
  try {
    const response = await axios.get('/users');
    console.log(response.data);
  } catch (error) {
    console.log(error);
  } finally {
    console.log('不管成功失敗都會執行');
  }
}
```

`await` 的意思是「等這個 Promise 完成，再繼續往下跑」，讓非同步程式碼看起來像同步，更容易閱讀。

### 寫法 3，兩種混用 (常見於 React Query)

```tsx
// queryFn 裡用 axios 回傳 Promise，React Query 幫你處理狀態
const { data } = useQuery({
  queryKey: ['users'],
  queryFn: () => axios.get('/users').then(res => res.data)
});
```

---

## 重要概念，await 只能在 async 函式裡用

```tsx
// 錯誤寫法，await 不能在一般函式裡用
function getUsers() {
  const data = await axios.get('/users');  // 報錯
}

// 正確寫法
async function getUsers() {
  const data = await axios.get('/users');  // 正確
}

// React 元件裡，useEffect 內部建立 async 函式
useEffect(() => {
  async function fetchData() {
    const response = await axios.get('/users');
    setUsers(response.data);
  }

  fetchData();
}, []);
```

---

## 同時發送多個請求

有時候你需要同時打好幾支 API，不必一個等一個。

```tsx
// 錯誤做法，一個等一個，總共等 3 秒
const users    = await axios.get('/users');    // 等 1 秒
const products = await axios.get('/products'); // 等 1 秒
const orders   = await axios.get('/orders');   // 等 1 秒

// 正確做法，同時發送，只等最慢的那個，總共等 1 秒
const [users, products, orders] = await Promise.all([
  axios.get('/users'),
  axios.get('/products'),
  axios.get('/orders')
]);
```

`Promise.all` 是「全部成功才算成功，任何一個失敗就整體失敗」。

---

## Promise 的常用工具方法

```tsx
// Promise.all，全部成功才繼續，任一失敗就 catch
await Promise.all([p1, p2, p3]);

// Promise.allSettled，全部跑完，不管成功失敗，都給你結果
const results = await Promise.allSettled([p1, p2, p3]);
results.forEach(result => {
  if (result.status === 'fulfilled') console.log(result.value);
  if (result.status === 'rejected')  console.log(result.reason);
});

// Promise.race，哪個最快完成就用哪個
const fastest = await Promise.race([p1, p2, p3]);
```

---

## 在 React + TypeScript 的實際應用

```tsx
// 定義回傳型別
interface User {
  id: number;
  name: string;
}

// async 函式加上回傳型別
async function fetchUser(id: number): Promise<User> {
  const response = await axios.get<User>(`/users/${id}`);
  return response.data;
}

// 元件裡使用
function UserProfile({ id }: { id: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['user', id],
    queryFn: () => fetchUser(id)
  });

  if (isLoading) return <p>載入中</p>;
  return <p>{data?.name}</p>;
}
```

## 總結

```
同步  →  一行一行等，跑完才繼續
非同步 →  丟出去先跑，完成後再回來處理結果
Promise →  管理這個「完成後回來」的機制
async/await →  讓非同步寫起來像同步，更好讀
```