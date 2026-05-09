---
tags: [python, tkinter, gui]
---

> 關聯：[[python]]

# GUI套件-tkinter

- 基本
    - 導入套件
        
        ```python
        from tkinter import *
        ```
        
    - 建立一個叫做window的新視窗
        
        ```python
        window = Tk()
        ```
        
    - 開視窗
        
        ```python
        	window.mainloop() 
        ```
        
        <aside>
        💡  mainloop，是一個要電腦在使用者關閉視窗之前持續偵測視窗並處理事件的語法。
        
        </aside>
        
- 窗格設定
    1. 標題
        
        ```python
        window.title(“你的標題”)
        ```
        
    2. 長,寬
        
        ```python
        window.maxsize(長,寬)
        #int
        ```
        
        ```python
        window.geometry('長x寬')
        #string
        ```
        
    3. 不可以更改大⼩
        
        ```python
        window.resizable(0,0) #不可以更改大⼩
        ```
        
- 宣告GUI元件
    
    元件類別(父類別, 選擇性參數1 = 值1, ...)
    
    ```python
    #範例
    btn1 = Button(window, text = "確定", bg = "yellow")
    ```
    
    <aside>
    💡 父類別是填 window，所以Button 出現在 window 的視窗中
    
    </aside>
    
    可以⽤文字索引或 `.config()` 的⽅式來更動參數。
    
    ```python
    btn1["text"] = "離開"
    btn1["fg"] = "red"   #改字顏色
    btn1.config(bg = "blue")　　　#改背景顏色
    ```
    
- 設置位置的方
    1. `pack(side = TOP)` ：根據某個方向排列
        - side ：排列方向，預設是 TOP，可以選擇 BOTTOM, LEFT, RIGHT
        - Pack 的呈現方式。會按照程式碼的順序堆疊。
        
        範例：
        
        ```python
        window = Tk()
        label1 = Label(window, text='1')
        label2 = Label(window, text='2')
        label3 = Label(window, text='3')
        label4 = Label(window, text='4')
        label1.pack(side = TOP)
        label2.pack(side = TOP)
        label3.pack(side = RIGHT)
        label4.pack(side = LEFT)
        window.mainloop() #開視窗
        ```
        
        效果：
        
      ![](raw/Languages/Python/GUI套件-tkinter/Untitled.png)))
        
    2. `grid(row, column)` ：類似格子
        - 將區域分割成最大的 row 列與最大的 column 行
        - 在這個格子狀的區域內，將 GUI 元件分配到某一格內
        - Column 的呈現方式。會將 GUI 元件填入格子中。
        
        範例：
        
        ```python
        window = Tk()
        label1 = Label(window, text=‘1’)
        label2 = Label(window, text=‘2’)
        label3 = Label(window, text=‘3’)
        label4 = Label(window, text=‘4’)
        label1.grid(row = 0, column = 0)
        label2.grid(row = 1, column = 0)
        label3.grid(row = 1, column = 1)
        label4.grid(row = 2, column = 2)
        ```
        
        效果：
        
      ![](raw/Languages/Python/GUI套件-tkinter/Untitled%201.png)))
        
    3. `place(x, y)` ：絕對的像素位置
        
        範例：
        
        ```python
        label1 = Label(window, text=‘1’)
        label2 = Label(window, text=‘2’)
        label1.place(x = 0, y = 50)
        label2.place(x = 33, y = 33)
        ```
        

[常見GUI介面](常見GUI介面%202c98fda15f6f81429d59f10b30fdb914.md)