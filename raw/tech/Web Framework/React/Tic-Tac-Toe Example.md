---
tags: [web-dev, react, frontend, typescript]
---

> 關聯：[[react]]

# Tic-Tac-Toe Example

**`index.js`**

> 在 `App.js` 檔案中建立的元件與網頁瀏覽器之間的橋樑。
> 

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

import App from './App';

const root = createRoot(document.getElementById("root"));
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- React 的函式庫，用來與網頁瀏覽器溝通（React DOM）
- 零件的 CSS Style
- `App.js` 中創建的元件

> 💡 檔案的其餘部分會將所有碎片整合起來，並將最終成果注入 `public` 資料夾中的 `index.html`。

**`App.js`**

![image.png](Tic-Tac-Toe%20Example/image.png)

```tsx
export default function Board() {
  return (
    <>
	    <div>
        <button className="square">1</button>
	      <button className="square">2</button>
	      <button className="square">3</button>
	    </div>
	    <div>        
        <button className="square">4</button>
	      <button className="square">5</button>
	      <button className="square">6</button>
        </div>
	    <div>        
        <button className="square">7</button>
	      <button className="square">8</button>
	      <button className="square">9</button>
        </div>

    </>
  );
}
```

- `export` 關鍵字使此函式可在此檔案外部存取。
- `default` 關鍵字告訴其他檔案這是您檔案中的主要函式。
- `return`  關鍵字表示後面的字會以值形式回傳給函式呼叫者。
- `<button>` 是 *JSX 元素* 。JSX 元素是 JavaScript 程式碼與 HTML 標籤的結合，用來描述你想顯示的內容。
- `className="square"` 是一個按鈕的屬性 **，告訴 CSS 如何樣式按鈕。`X` 是按鈕內顯示的文字，`</button>` 關閉 JSX 元素，表示後續內容不應放在按鈕內。
- 使用 *Fragments（*`<>` 和 `</>`）來包裝多個相鄰的 JSX 元素

**`styles.css`** 

- *CSS selectors* (`*` and `body`) define the style of large parts of your app.
- The `.square` selector defines the style of any component where the `className` property is set to `square`.

**`App.css`**

```tsx
* {
  box-sizing: border-box;
}

body {
  font-family: sans-serif;
  margin: 20px;
  padding: 0;
}

h1 {
  margin-top: 0;
  font-size: 22px;
}

h2 {
  margin-top: 0;
  font-size: 20px;
}

h3 {
  margin-top: 0;
  font-size: 18px;
}

h4 {
  margin-top: 0;
  font-size: 16px;
}

h5 {
  margin-top: 0;
  font-size: 14px;
}

h6 {
  margin-top: 0;
  font-size: 12px;
}

code {
  font-size: 1.2em;
}

ul {
  padding-inline-start: 20px;
}

* {
  box-sizing: border-box;
}

body {
  font-family: sans-serif;
  margin: 20px;
  padding: 0;
}

.square {
  background: #fff;
  border: 1px solid #999;
  float: left;
  font-size: 24px;
  font-weight: bold;
  line-height: 34px;
  height: 34px;
  margin-right: -1px;
  margin-top: -1px;
  padding: 0;
  text-align: center;
  width: 34px;
}

.boardRow:after {
  clear: both;
  content: '';
  display: table;
}

.status {
  margin-bottom: 10px;
}
.game {
  display: flex;
  flex-direction: row;
}

.gameInfo {
  margin-left: 20px;
}
```

### 互動 C**omponent (handle)**