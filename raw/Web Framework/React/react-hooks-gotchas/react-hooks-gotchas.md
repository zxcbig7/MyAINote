---
tags: [web-dev, react, frontend, typescript]
---

> 關聯：[[react]]

# React Hooks 常見陷阱

## useEffect 內呼叫函式的宣告順序

### 錯誤訊息

```
react-hooks/immutability: `handleXxx` is accessed before it is declared
```

### 原因

`function` 宣告雖然有 hoisting，但 React ESLint plugin（`react-hooks/immutability`）額外規定：**useEffect 內呼叫的函式必須在呼叫點之前定義**，確保每次 render 取到的是相同的 reference。

### 解法

把函式宣告移到 `useEffect` 之前：

```typescript
// ❌ 報錯：handleXxx 在 useEffect 之後定義
useEffect(() => { handleXxx(); }, []);
async function handleXxx() { ... }

// ✅ 正確：handleXxx 在 useEffect 之前定義
async function handleXxx() { ... }
useEffect(() => { handleXxx(); }, []);

// ✅ 更簡潔：邏輯直接內嵌，不需要獨立函式
useEffect(() => {
  // 邏輯寫在這裡
}, []);
```

---

## useEffect dependency array 的 exhaustive-deps 警告

### 錯誤訊息

```
React Hook useEffect has a missing dependency: 'handleXxx'.
Either include it or remove the dependency array.
```

### 原因

`useEffect` 內使用了外部函式，但 dependency array 沒有列入，ESLint 無法確保這個函式在每次 render 後是否有更新。

### 解法

| 情境 | 解法 |
|------|------|
| 邏輯只需跑一次（如 OAuth callback） | 把邏輯內嵌到 useEffect，或加 `// eslint-disable-line react-hooks/exhaustive-deps` |
| 函式會因 props/state 改變 | 用 `useCallback` 包住函式，再加入 dependency array |
| 函式完全不依賴外部狀態 | 移到 component 外部定義 |

```typescript
// 一次性邏輯：直接 inline
useEffect(() => {
  if (called.current) return;
  called.current = true;
  // ... OAuth callback 邏輯
}, []);  // eslint-disable-line react-hooks/exhaustive-deps

// 依賴外部狀態：useCallback
const handleXxx = useCallback(() => {
  doSomethingWith(externalValue);
}, [externalValue]);

useEffect(() => { handleXxx(); }, [handleXxx]);
```

---

## JavaScript Hoisting：function 宣告 vs const/let

React 的 ESLint 規則背後是 JavaScript 的 hoisting 概念：

| 宣告方式 | Hoisting 行為 |
|----------|--------------|
| `function foo() {}` | 整個函式提升，可在宣告前呼叫 |
| `const foo = () => {}` | 名稱提升但未初始化，宣告前呼叫會拋 ReferenceError |
| `const foo = async () => {}` | 同上 |

```typescript
// function 宣告：JS 本身允許（但 ESLint hooks 規則不允許在 useEffect 前）
foo();
function foo() { console.log("ok"); }

// const arrow：JS 本身不允許
bar();  // ReferenceError: Cannot access 'bar' before initialization
const bar = () => { console.log("ok"); };
```

---

## StrictMode 雙重觸發問題

React 18 StrictMode 在開發環境下會將 `useEffect` 執行兩次，用來偵測副作用。

### 現象

API 請求被打兩次、OAuth 流程被走兩次。

### 解法

用 `useRef` 作為 guard：

```typescript
const called = useRef(false);

useEffect(() => {
  if (called.current) return;
  called.current = true;
  // 只會執行一次的邏輯
}, []);
```

注意：這個 guard 只在 StrictMode 雙重觸發時有效，不能取代 API 的冪等設計。
