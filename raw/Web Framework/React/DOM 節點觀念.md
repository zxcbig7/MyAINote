# DOM 節點觀念

## 什麼是 DOM？

**DOM（Document Object Model）** 是瀏覽器把 HTML 文件解析後，在記憶體中建立的樹狀資料結構。

```
HTML 文件
    └─ <html>
         ├─ <head>
         │    └─ <title>我的網站</title>
         └─ <body>
              ├─ <h1>標題</h1>
              └─ <div>
                   └─ <p>段落</p>
```

每一個標籤、文字、甚至註解，都是一個 **節點（Node）**。

---

## 節點的種類

| 節點類型 | 說明 | 範例 |
|---|---|---|
| Element Node | HTML 標籤 | `<div>`、`<p>`、`<button>` |
| Text Node | 標籤內的文字 | `Hello` in `<p>Hello</p>` |
| Attribute Node | 標籤屬性（現代 DOM 不常直接操作） | `class="btn"` |
| Document Node | 整份文件的根 | `document` 物件 |

最常操作的是 **Element Node**。

---

## 瀏覽器怎麼建立 DOM？

```
HTML 字串
    → Parser 解析
    → DOM Tree（記憶體中的物件樹）
    → Render Tree（加上 CSS 樣式）
    → Layout（計算位置大小）
    → Paint（繪製到畫面）
```

改動 DOM → 瀏覽器重新走後面的步驟 → 有效能成本（這是 Virtual DOM 出現的原因）

---

## 用 JavaScript 操作 DOM（原生方式）

```js
// 選取節點
const el = document.getElementById('app')
const items = document.querySelectorAll('.item')

// 改內容
el.textContent = 'Hello'
el.innerHTML = '<span>Hello</span>'

// 改樣式
el.style.color = 'red'
el.classList.add('active')

// 新增節點
const btn = document.createElement('button')
btn.textContent = '點我'
el.appendChild(btn)

// 移除節點
el.removeChild(btn)
```

---

## Virtual DOM — React 的核心概念

直接操作 DOM 很慢，因為每次改動都可能觸發 Layout + Paint。

React 的解法：

```
你寫的 JSX
    → React 建立 Virtual DOM（純 JS 物件，速度快）
    → 狀態改變時，React 比較新舊 Virtual DOM（Diffing）
    → 只把「真正有差異」的部分更新到真實 DOM（Reconciliation）
```

### 舉例

```jsx
// 你寫的 JSX
<div className="card">
  <h1>{title}</h1>
  <p>{content}</p>
</div>

// React 內部看到的 Virtual DOM（簡化）
{
  type: 'div',
  props: { className: 'card' },
  children: [
    { type: 'h1', props: {}, children: [title] },
    { type: 'p',  props: {}, children: [content] }
  ]
}
```

title 改變 → React 只更新 `<h1>` 對應的那個真實 DOM 節點，其他不動。

---

## React 中直接存取 DOM：useRef

大多數情況讓 React 管理 DOM，但有些場景需要直接操作：

- 讓 input 自動 focus
- 整合第三方 library（例如圖表、地圖）
- 讀取 DOM 的尺寸 / 位置

```tsx
import { useRef, useEffect } from 'react'

function SearchBox() {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()  // 頁面載入後自動 focus
  }, [])

  return <input ref={inputRef} placeholder="搜尋..." />
}
```

`ref.current` 就是真實的 DOM Element，可以直接呼叫原生方法。

---

## 節點關係

```
parent
├─ child（firstChild）
├─ child           ← previousSibling / nextSibling
└─ child（lastChild）
```

```js
el.parentElement      // 父節點
el.children           // 所有子節點（HTMLCollection）
el.firstElementChild  // 第一個子節點
el.nextElementSibling // 下一個兄弟節點
```

---

## 事件冒泡（Event Bubbling）

點擊一個元素，事件會從該節點往上傳遞到 `document`。

```
點擊 <button>
    → button 的 click 事件觸發
    → div 的 click 事件觸發
    → body 的 click 事件觸發
    → document 的 click 事件觸發
```

```js
btn.addEventListener('click', (e) => {
  e.stopPropagation()  // 阻止繼續往上冒泡
})
```

React 的合成事件（Synthetic Event）也遵循同樣機制，所以 `onClick` 的 `e.stopPropagation()` 在 React 裡一樣有效。

---

## 重點整理

| 概念 | 一句話說明 |
|---|---|
| DOM | 瀏覽器把 HTML 變成記憶體中的物件樹 |
| Node | 樹上的每一個節點（標籤、文字…） |
| Virtual DOM | React 用純 JS 物件模擬 DOM，減少真實 DOM 操作 |
| Diffing | React 比較新舊 Virtual DOM 找出差異 |
| Reconciliation | 把差異同步到真實 DOM |
| useRef | 在 React 中直接拿到真實 DOM 節點的方式 |
| 事件冒泡 | 事件從觸發元素往上傳遞 |
