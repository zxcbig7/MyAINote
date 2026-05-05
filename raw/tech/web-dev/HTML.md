# HTML

# 基本架構

```html
<!DOCTYPE html>
<html>
	<head lang="zh-Hant-TW">
		<meta charset="utf-8">
	</head>

	<body>
		<ul>
			<li> 清單 </li>
		</ul>
	  <h1> 標題 </h1>
		<p> 內容1<br> </p>
		<p> 內容2 </p>
	</body>

</html>

	<!--
		註解
	-->
```

## 大架構

---

- `<!DOCTYPE html>` 的部分稱為 [doctype 宣告]，宣告文件以HTML5製成的標記，HTML5較為常見
- `html` 標籤框住的內容代表HTML文件本身
- `head` 包含不會再瀏覽器畫面顯示的頁面資訊
- `body` 包含所有會顯示在瀏覽器畫面的資訊

## 元素

---

- `<br>` 換行
- 特殊字元`&(and符號);`
- 縮小文字 `<small>`
- 屬性
    1. `lang` : 代表html元素的語言是繁體中文，如果是英文網站可以用"en"
    2. `meta` : 通常為一組，指定文件相關資訊。因為是設定用標籤，所以沒有結束標籤
        1. `charset` : 設定[字元編碼](https://zh.wikipedia.org/zh-tw/%E5%AD%97%E7%AC%A6%E7%BC%96%E7%A0%81)。
        2. `name` : 指定屬性為description後輸入content值，內容為簡單扼要的網站說明內容
        - 標題與概要 將決定搜尋關鍵字的順位

## 

# 標籤

## 文件結構

---

- **清單**
    - `<ul>` 與 `<li>` : ul為清單範圍，li為清單項目，會顯示**．**
    - `<ol>` 與 `<li>` : ol為清單範圍，li為清單項目，會顯示順序
- **標格`<table>`**
    - `<tr>` : 表格標題，縱向
    - `<th>`與`<td>` : 表格文字，橫向
- **章節(增加HTML的易讀性)**
    - `<article>` : 獨立完整的內容區塊，通常用在整篇文章
    - `<aside>` : 與前後的內容有關聯，但與主題不同的區塊。通常是補充資訊或者廣告
    - `<nav>` : 網站的主要導覽列
    - `<section>` : 不屬於上述任一種的內容區塊，通常代表一部分內容
- **頁首 與 頁尾**
    - header : 章節的標題與引言部分、網頁LOGO標誌、標題、目錄、搜尋表單等
    - footer：撰寫內容的人的連結、著作聲明等
- **主要內容`<main>`**
    - 標記最主要內容
    - 一個HTML裡面只能有一個main
- **圖片`<img src="" alt="" width="" height="">`**
    - src : 路徑
    - alt : 圖片無法顯示的替代文字
    - width : 寬度
    - height : 高度
- **連結`<a href="路徑">內容</a>`**
    - 相對路徑:<a href="相對路徑">內容</a>
    - 絕對路徑:<a href="[https://www.google.com/](https://www.google.com/)" target="_blank">內容</a>
        
        <aside>
        💡 target 設定開啟方式，_blank是開新視窗
        
        </aside>
        
    - 路徑用[../]，表示相對上一頁
- **書籤連結`<a href="#書籤名稱">內容</a>`**
    - 其中書籤名稱是**章節標籤**的id係數
    - 要加#
    - #top預設為回到頂部，但如果有id取top則優先使用該路徑

## 注意事項

---

1. **如果檔案名稱為index.html為主頁，打網址時可以省略，以下兩個範例相同**
    - http://example.com/index.html
    - http://example.com/
2. **只能打半型字元**
3. 注意巢狀結構，善用縮排功能