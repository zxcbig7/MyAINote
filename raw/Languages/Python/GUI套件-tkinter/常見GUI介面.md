---
tags: [python, tkinter, gui]
---

> 關聯：[[python]]

# 常見GUI介面

![](https://miro.medium.com/max/374/1*Ox5Z_Mkw55uZ5lQJvZJwWg.png)

### Frame：視窗區域(整體)

上面的三行文字敘述同屬一個 Frame。

### LabelFrame：標籤式視窗(區域)

下方的兩個區塊皆為 Label Frame

### CheckButton：核取按鈕(右邊的 Use this option)

語法：

```
Checkbutton(父類別, 選擇性參數...)
```

參數：

- `textvariable` ：取得核取按鈕的文字
- `variable` ：取得或設定核取按鈕的狀態
- `command` ：當核取按鈕的狀態改變時，會呼叫這個參數的指定函式

```
from tkinter import *def ShowMsg():
    for i in checkvalue:
        if checkvalue[i].get() == True:
            print(item[i])window = Tk()
item= {0:’a’, 1:’b’. 2:’3’}
checkvalue = {}for i in range(len(item)):
    checkvalue[i] = BooleanVar()
    Checkbutton(window, variable = checkvalue[i], text=item[i])window.mainloop()
```

### RadioButton：選項按鈕(左邊的 Value)

RadioButton 與上面的 CheckButton 的差別在於 RadioButton 是單選，而 CheckButton 則可以多選。

語法：

```
Radiobutton(父類別, 選擇性參數...
```

參數：

- `textvariable` ：取得核取按鈕的文字
- `variable` ：取得或設定核取按鈕的狀態
- `value` ：選項按鈕的值，用來區分不同的選項按鈕
- `command` ：當選項按鈕的狀態改變時，會呼叫這個參數的指定函式

```
from tkinter import *def ShowMsg():
    i = radiovalue.get()
    print(item(i))window = Tk()
item= {0:’a’, 1:’b’. 2:’3’}
radiovalue = IntVar()
radiovalue.set(0)for i in range(len(item))
    Checkbutton(window, variable = radiovalue, text=item[i], value = i)window.mainloop()
```

---

### Label：文字標籤

![](https://miro.medium.com/max/247/1*jq8BBGOQR5eIaE9fBkRpRw.png)

語法：

```
Label(父類別, 選擇性參數...)
```

參數：

- `text` ：文字
- `width` ：寬度（自數）
- `height` ：高度（自行數）
- `bg / background` ：背景色彩（反白的時候的顏色）
- `fg / foreground` ：前景色彩
- `bd / borderwidth` ：邊框寬度
- `padx` ：水平間距
- `pady` ：垂直間距
- `justify` ：對齊方式，可以分為 LEFT, RIGHT, CENTER

---

![](https://miro.medium.com/max/432/1*4tefBZbpz--akulFO9OTZQ.png)

### Entry：文字方塊

「Enter Num 1:」旁的白框即為 Entry，可由使用者輸入內容。

語法：

```
Entry(父類別, 選擇性參數...)
```

參數：

- `width` ：寬度
- `state` ：輸入狀態，預設為 NORMAL，若是 DISABLE 則無法輸入
- `textvariable` ：用來取得或設定文字方塊的文字

```python
def printEntry():
    print(name.get())
window = Tk()
name = StringVar()
btn = Button(window, command= printEntry)
nameEntry = Entry(window, textvariable=name)
nameEntry.config(font=(“Arial”,30))
```

### Button：按鈕

最下方的 Quit 和 Show 即為 Button。

語法：

```
Button(父類別, 選擇性參數...)
```

參數：

- `image` ：按鈕上的圖形
- `textvariable` ：用來取得或設定按鈕的文字
- `command` ：當使用者點擊按鈕時，會呼叫這個參數指定的函式。

---

### Text：文字區域

視窗白底範圍內皆為 Text。

![](https://miro.medium.com/max/268/1*Jz6ZXLdzCM9ePq7HpiKhQQ.png)

語法：

```
Text(父類別, 選擇性參數...)
```

參數：

- `highlightbackground` ：反白背景顏色
- `highlightcolor` ：反白顏色
- `state` ：輸入狀態，NORMAL（預設）／DISABLE
- `wrap` ：換行，預設為 CHAR，斷掉單字／還有 WORD（不會斷掉單字）／NONE（不換行）
- `xscrollcommand` 、 `yscrollcommand` ：水平卷軸、垂直卷軸

```
TEXT.insert(位置參數, s)
```

- 位置參數：`a.b`，表示 line a, character b，第 a 行，第 b 個字元；END 表示文字區域的末端
- s：想輸入的字串

---

### Listbox：清單方塊

上方白底區塊即是 Listbox。

![](https://miro.medium.com/max/171/1*VfBq6KXXwHPEZUcznXQCIg.png)

---

### Scrollbar：卷軸

Scrollbar 是右邊的卷軸，可以在顯示面積不夠大時調整顯示範圍。

語法：

```
Scrollbar(父類別, 選擇性參數...)
```

參數：

- `highlightbackground` ：反白背景顏色
- `highlightcolor` ：反白顏色
- `activebackground` ：滑鼠移到卷軸時，卷軸與箭頭的顏色
- `orient` ：預設為 VERTICAL，HORIZONTAL 表示水平
- `command` ：當移動卷軸時，呼叫這個參數指定的函式

```python
text = '1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n'

window = Tk()
sbar1 = Scrollbar(window)
text1 = Text(window, width = 40, height = 4, wrap = WORD)
text1.insert(END, 'Text\n')
text1.insert(END, text)
sbar1.pack(side = RIGHT, fill = Y)
text1.pack(side = LEFT, fill = Y)
sbar1['command'] = text1.yview
text1['yscrollcommand'] = sbar1.set
window.mainloop()
```

---

### Menu：功能表

![](https://miro.medium.com/max/211/1*tDGt7FL-59Wr4llbh4Nh9Q.png)

上方的 File、Edit 和 Help 都是 Menu。

語法：

```
menu(父類別, 選擇性參數...)
```

參數：

- `activebackground` ：指標移到項目的反⽩顏⾊
- `tearoff` ：第⼀個項目上面的分割線
- `add_cascade` ：增加⼦項目表，label 指定子項⽬表的⽂字，memu 指定子功能報表與哪個 menu 元件產⽣關聯
- `add_command` ：增加項目，label 指定項目的⽂字，command 指定點擊項⽬時呼叫的函式
- `add_seperator()` ：加入分隔線

---

### MenuButton：功能表按鈕

![](https://miro.medium.com/max/257/1*tsdV2nW6IqyHKEeIrJyY_w.png)

---

### Scale：滑桿

![](https://miro.medium.com/max/369/1*aIL9_eUAt-uDaWGpr4VB4Q.png)

---

### Spinbox：調整紐

可以設置成無法調整的 Spinbox（如黃底的 1）。

![](https://miro.medium.com/max/404/1*jr9zUinf0DansRskV7rxog.png)

---

![](https://miro.medium.com/max/306/1*OXr309yth4gES6vWDma1vw.png)

### MessageBox：對話方塊

跳出 Hello World 的 messageBox。

語法：

```
messagebox.視窗選項(title, message, options)
```

參數：

- 視窗選項：`showerror` 、 `showinfo` 、 `showwarning` 、 `askokcancel` 、 `askquestion` 、 `askretrycancel` 、 `askyesno`
- `title` ：彈出視窗顯示的標題
- `message` ：對話方塊內的文字
- `default` ：預設的按鈕，可以設定為 CANCEL／IGNORE／OK／NO／ RETRY／YES
- `icon` ：對話方塊內的圖示，有 ERROR／INFO／QUESTION／WARNING 等
- `parent` ：對話方塊的父物件
- 部分視窗會回傳一些值，例如布林值

---

### PhotoImage：圖形

![](https://miro.medium.com/max/1177/1*aPWN09xtB9sfD0NMEzEz3g.png)

可以在視窗中顯示圖片。

```
PhotoImage(file = "GIF")
```

- `file` ：檔案名稱，副檔名與路徑