# CSS

需要在`<head>`裡面加入`<style>`

```html
<style>
    h1 {
        font-size: 16px;
				color: brown;
    }
</style>
```

# 選擇器

範例中的選擇器指定更改所有h1，

- 可以指定**`id`**或者`class`屬性
- 用 {} 框起來
- 用 : 分隔`屬性`與`值`
- 用 ; 分隔多個`屬性`

# 建立並匯入CSS檔案

1. 建立css資料夾
2. 建立一個副檔名為.css的檔案
3. 把`<style>`的內容放進該.css檔案
4. 在`<head>`中加入`<link rel="stylesheet" href="路徑">`

# 各種CSS屬性

- **/*註解內容*/**
- **文字大小 `font-size`**
    - px: 預設16px
    - em: 以父元素的文字大小為基礎的相對值。(假設父元素大小為16px，2em=2*16px = 32px)
- **文字顏色 `color`**
    - 直接輸入顏色
    - 色碼
        1. 10進位RGB ⇒ color: rgb(34, 140, 77)
        2. 16進位必須加# ⇒ color: #228c4d
- **指定文字對齊方式`text-align`**
    - center : 中間
    - left : 靠左(預設)
    - right : 靠右
    - justify : 左右對齊
- **邊框`border`**
    - 邊框設定
        1. border-style ⇒ 上下左右
        2. border-top-style ⇒ 上
        3. border-bottom-style ⇒ 下
        4. border-left-style ⇒ 左
        5. border-right-style ⇒ 右
    - 線條種類`border-style`
        1. solid ⇒ 實心
        2. double ⇒ 雙線條
        3. dotted ⇒ 點線
        4. dashed ⇒ 間隔
        5. groove ⇒ 立體1
        6. ridge ⇒ 立體2
        7. inset ⇒ 立體3
        8. outset ⇒ 立體4
    - 寬度`border-width`
        - 無法單獨使用
        - 設定為數值，例如16px
        - 與`border-style`並用
        1. border-width⇒ 上下左右
        2. border-top-width ⇒ 上
        3. border-bottom-width ⇒ 下
        4. border-left-width ⇒ 左
        5. border-right-width ⇒ 右
    - 顏色 `border-color`
        - 無法單獨使用
        - 與`border-style`並用
        1. border-color⇒ 上下左右
        2. border-top-width ⇒ 上
        3. border-bottom-color ⇒ 下
        4. border-left-color ⇒ 左
        5. border-right-color⇒ 右
        
    - 簡寫範例
        
        選擇器{border: [種類] [粗細] [顏色];}
        
        ```css
        h3{
        	border-left: solid 6px #6b3008;
        }
        ```
        
- **設定背景 `background-color`**
    - 使用色碼指定(rgb或者#)
    

# 以 *class* 與 *id* 指定CSS的方法

### class選擇器

1. 在原本HTML的元素裡面加class=""
2. 在.css檔案裡用「.」+「class屬性值」建立class選擇器

### id選擇器

1. 在原本HTML的元素裡面加id=""
2. 在.css檔案裡用「#」+「id屬性值」建立id選擇器

### class 與 id 的差別

- id可以設定書籤連結或者在JavaScript中指定特定元素
- class可以在單一HTML網頁內**設定多個相同的值**，但id屬性**只能在單一網頁內使用一次**

<aside>
💡 如果要大量CSS裝飾，用class比較好

</aside>

# 盒子模組

邊距 : padding屬性

邊框 : border屬性

邊界 : margin屬性

### padding 與 margin

---

- 可在元素的上下左右增加留白
- 指定樣式
    - padding
        1. padding
        2. padding-top
        3. padding-bottom
        4. padding-left
        5. padding-right
    - margin
        1. margin
        2. margin-top
        3. margin-bottom
        4. marginmargin-left
        5. padding-right
- 指定大小(以padding為例，margin也一樣)
    - padding
        1. padding: 10px ⇒ 上下左右
        2. padding: 10px 5px ⇒ 上下|左右
        3. padding: 10px 5px 20px  ⇒ 上|左右|下
        4. padding: 10px 5px 20px 15px ⇒ 上|下|左|右
        

- 補充
    1. 下面的選擇器會覆蓋上面的選擇器設定
    2. 上下邊界如果重複設定，取設定較大者
    3. 左右邊界如果重複設定，直接相加

# table設定

---

**border-collapse屬性**

- separate 分離邊框模組(預設)
- collapse 結合邊框模組

**width 屬性**

- 數值px
- 比例
- 預設width:auto

# 更變清單符號

- list-style-type
    1. none ⇒ 無符號
    2. disc ⇒ 圓   (ul預設)
    3. circle ⇒ 空心圓
    4. square ⇒ 黑色矩形
    5. lower-roman ⇒ 小寫羅馬數字
    6. upper-roman ⇒ 大寫羅馬數字
    7. dicimal ⇒ 數字  (ol預設)
    8. dicimal-leading-zero ⇒ 開頭0的數字
    9. lower-alpha ⇒ 小寫英文字母
    10. upper-alpha ⇒ 大寫英文字母
    11. hiragana ⇒ 平假名
    12. katakana ⇒ 片假名

# 更變連結樣式

在選擇器後面加上:hover，能夠指定滑鼠游標停懸在連結上的裝飾

```css
.navigation ul li a:hover{
    color: #62D5e8;
}
```

![](raw/Languages/CSS/Untitled.png))

![](raw/Languages/CSS/Untitled%201.png))

**虛擬類別(在選擇器的地方使用)**

a ⇒ 所有連結

a:link ⇒ 尚未瀏覽的連結

a:hover ⇒ 滑鼠游標移入連結時

a:active ⇒ 連結被點選時

a:visited ⇒ 已瀏覽的連結

a:focus ⇒ 焦點移至連結時(以`tab`鍵移動時)

**連結底線**

test-decoration: none;  ⇒ 刪除底線

test-decoration: underline; ⇒ 底線

test-decoration: overline; ⇒ 上線

test-decoration: line-through; ⇒ 刪除線

區塊層級元素與行內層級元素

border: solid 1px red;

其中參數可以放 線條樣式、線條粗細、線條顏色

區塊層級元素: p、h1~h6、ul、ol、li、section、article

行內層級元素:img、a

display: [樣式];

其中參數可以放 inline(排列)