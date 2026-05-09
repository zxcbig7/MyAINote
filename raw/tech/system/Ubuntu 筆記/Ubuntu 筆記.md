---
tags: [system, ubuntu, linux]
---

> 關聯：[[linux]]

# Ubuntu 筆記

# **目錄**

# 基本觀念

### 註銷（退出Linux系統）

在每次終端使用完後，一定要進行注銷（或者說退出），以防他人通過你的用戶進入系統。

在Linux提示符下，運行`exit`命令(或直接按組合鍵 `Ctrl+d` )，即可退出本次登錄。

### 關機與重啟

Linux主機的關機方法為：

用戶登錄後，輸入命令 `poweroff`表示立即關機。

Linux主機的重啟方法為：

用戶登錄後，輸入命令 `reboot`表示立即重啟電腦。

## 使用root 用戶登錄

root用戶是系統超級管理員，怎麽登錄呢？ 安裝時沒有設置root用戶密碼的地方呀。

Ubuntu 不想讓大家直接使用root用戶登錄， 因為權限太大，誤操作可能有很大危害。

很多命令必須以root用戶權限執行， 不用root用戶登錄會比較麻煩。

這時可以通過如下方法設置root用戶的密碼，並且切換到root用戶

- 使用安裝時創建的用戶登錄
- 執行命令 `sudo passwd root`

系統提示： `[sudo] password for byhy:` ， 是要你輸入 byhy這個用戶的密碼， 輸入後回車

接著提示： `New password:` ， 是要你輸入root用戶的密碼，輸入你要設置的密碼後回車

接著提示： `Retype new password:` ， 是要你再次輸入root用戶密碼確認，再次輸入後回車

如果出現 `passwd: password updated successfully` 表示設置root密碼成功， 後面就可以使用 root 用戶登錄了。

- 執行命令 `su - root`

表示要從當前用戶切換到root用戶登錄， 然後輸入剛設置的root用戶密碼，即可登錄。

<aside>
⚠️ 注意： Ubuntu 默認不允許root用戶直接遠程登錄的，只能本地登錄，或者先用其它用戶登錄後切換。

</aside>

# 文件編輯

操作Linux 往往是遠程操作，沒有圖形界面，要修改一個文本文件，最快捷的方式就是用 vi。

vi有個加強版本叫做vim，兩者常用的功能沒有什麽大的區別。

 vi 有 3 種使用模式。

## 命令模式

執行vi abc.txt 文件名 命令，就打開了vi去編輯文件abc.txt，默認進入的就是命令模式

### **移動光標**

- `h` － 光標左移一個字元
- `j` － 光標下移一個字元
- `k`－ 光標上移一個字元
- `l` － 光標右移一個字元
- `0` 或 `^` － 光標移動到所在行的行首
- `$` － 光標移動到所在行的行尾
- `gg` － 把光標移到文件開始位置
- `G` － 把光標移到文件末尾
- `Ctrl + f` － 往下翻一頁
- `Ctrl + b` － 往上翻一頁

### **刪除文字**

- `x` － 刪除光標所在字元
- `dd` － 刪除光標所在行
- `dw` － 刪除光標所在處到詞尾的內容
- `d$` － 刪除光標所在處到行尾的內容

### 選取、複製、貼上

- `yy` – 覆制光標所在的行
- `p` – 黏貼
- `v`，然後移動光標 – 可以選擇內容，再按y覆制選中的內容

### **撤銷、重複操作**

- `u` – 撤銷剛才所做的操作
- `Ctrl+r` – 重做被撤銷當前所做的操作
- `.` – 重覆剛才所做的操作

### 切換至插入模式

- `a`－將在光標所在位置之後插入文本（append）
- `i`－將在光標所在位置之前插入文本(insert)
- `o`－將在光標所在行之後插入一新行

## **插入模式**

插入模式是用來進行文件內容的輸入的。

在插入模式下，可以通過鍵盤方向鍵來移動光標。

編輯文件的過程中，經常需要切換回 命令模式，來刪除字元、刪除行，跳到上一頁，到最後一行等等。所以會非常頻繁的在插入模式 和 命令模式之間切換。

### 切換至命令模式

- `Esc` - 從插入模式切換到命令模式

## **底行模式**

底行模式就是在屏幕底部打開命令行，用來輸入命令。

底行模式 主要是 輸入命令 來 保存文件 或 退出vi程序、尋找字元串、列出行號等

<aside>
⚠️ **注意：**只能從命令模式進入底行模式。如果你現在是處於插入模式，必須先按Esc鍵進入命令模式後，再按冒號 `：` 或 `/` 進入底行模式。

</aside>

### 常用操作

- `:wq` 保存文件並退出
- `:q` 不保存文件，並退出，如果文件做了修改，但有不想保存，需要用:q!
- `:q!` 不保存文件，強制退出
- `:w` 只保存文件，但是不退出vi，可以切換到輸入模式下面繼續編輯文件
- `:set nu` 顯示行號
- `:set nonu` 取消顯示行號
- `/abc` 在文件中查找abc字元。按 `n` 不停的往下查找，按 `N` 往上查找
- `:1,$s/string/replace/g` 替換功能，把文件中的string,替換為replace 按Esc鍵，切換到命令模式

# **文件系统**

文本文件主要指磁碟上的文件。圖片文件都是存儲在磁碟上的文件系統里面的。

## **分區和文件系統**

在 Windows上， 可以為一塊磁碟 `分區` 。創建好分區後，還不能立即就在分區里面放文件，還要格式化分區。所謂格式化分區，也就是為分區安裝 `文件系統` 。

文件系統有好多種，Windows上 目前使用的文件系統 主要是 NTFS 。

Linux經常選用的文件系統有ext2，ext3，ext4 等

可以把文件系統理解為一種規範，規定了文件存放在磁碟上的方式。如果把 磁碟 比作 地球 的話， 磁碟分區好比是 地球上的各個國家地區， 而每個分區的格式化就像是為每個國家 選擇一種 管理制度。

在Windows上， 分好區，選擇文件系統格式化後，對每個文件系統的分區，需要給它們各自的盤符，比如 C盤或者D盤。

訪問Windows上的一個文件，需要給出這個文件的路徑。 文件的完整路徑，就是從盤符開始的：比如 `D:\\我的圖片\\a.jpg` 或者 `c:\\Windows\\write.exe`

- Windows文件系統里面都是磁碟文件或目錄
- Windows的文件路徑是從盤符開始的
- Windows上的文件的路徑是大小寫不區分的

## **掛接**

Linux文件系統里面不都是磁碟文件。

從Window過來學習Linux的人要糾正一個思維定式，就是看到路徑就一定要和磁碟上的存儲的目錄或文件對應起來。在Linux文件系統目錄里面除了磁碟文件，還有很多設備、甚至一些虛擬的對象，也在文件系統目錄里面訪問。

Linux在啟動過程中，就會[根據配置](https://stackoverflow.com/questions/10412135/where-are-all-mount-points-stored-in-linux/10412169)，創建一個虛擬的文件系統目錄結構（可以想象成，Linux系統創建在內存中的一個目錄結構），比如，下圖藍色部分所示

![Untitled](raw/tech/system/Ubuntu%20筆記/Untitled.png))

隨後的啟動過程，才會，將不同的分區 `掛接（mount）` 到文件系統不同的目錄中。

上圖就是把一個磁碟分區掛接到 /opt 下面。 /opt 這個路徑在這個動作中被稱為掛接點。

掛接後的文件系統目錄如下圖所示。

![Untitled](raw/tech/system/Ubuntu%20筆記/Untitled%201.png))

具體掛接到那個點，在安裝Linux操作系統的時候，就選擇好的。

<aside>
⚠️ **注意：**Linux啟動過程中，首先掛接的是 根節點 / 對應的磁碟分區文件系統，找到其中的 /etc/fstab文件，里面記載了其他文件系統的掛接點，再依次掛接其他的文件系統。

</aside>

- Linux目錄結構里面沒有文件系統的盤符
    
    從上面的示例可以看到，Linux 文件系統里面只有一個 `公共的根 /` ， 也叫根目錄。
    
    文件系統掛接到哪個掛接點，該文件系統下面的文件就從哪個掛接點算起。 比如上圖中磁碟分區掛接到 /opt 下面， 那麽原來該文件系統中的文件a1 的路徑就是 /opt/a1。如果直接掛接到根目錄 /下面，那麽原來該文件系統中的文件a1 的路徑就是 /a1
    
    一個文件的全路徑是 **從 根 到 該文件 這條路徑上 所有節點名** 順序連接，每個節點之間以 `/` 分開。
    
    比如，文件a3的全路徑就是：/opt/a3。
    

● Linux目錄結構是區分大小寫的 在Linux中 /root/abc 和 /root/abC 是兩個文件

# **目錄和文件操作**

## 當前目錄（工作目錄）

在命令行里執行命令的時候，我們所在的目錄。

當用戶剛登錄系統時，當前工作目錄是用戶的 `home目錄`。

root用戶的home目錄，是 `/root`

其他用戶home目錄，是在創建用戶的時候 指定產生的，一般是 `/home/用戶名`。比如你是用戶 byhy，home目錄通常就是 `/home/byhy`

當前目錄下面的所有文件都可以直接訪問， 假設當前目錄 下面有個文件 a.txt。 要用vi編輯它，就可以直接執行vi a.txt

- 使用命令 `pwd`  - 查看當前目錄，比如 `[root@izbqz ~]# pwd /root/package`
- 改變當前目錄用命令 `cd`
    
    改變當前目錄為package目錄（也稱進入到package目錄）， 就執行命令 `cd package`
    
    改變當前路徑到根目錄 就執行命令 `cd /`
    

## 絕對與相對路徑

![](https://cdn2.byhy.net/imgs/gh/36257654_57497214-51747f80-7309-11e9-862f-11d235f43e84.png)

- 絕對路徑：開始於根目錄，沿著目錄層級，一直到達所期望的目錄或文件。
    
    其中的 photos（假設它是個目錄） 的絕對路徑 就是 `/home/jono/photos`
    
    要進入到 photos 這個目錄，就執行命令 `cd /home/jono/photos`
    
- 相對路徑：
    
    相對的是 當前目錄。
    
    在使用相對路徑的過程中， 經常用到一對特殊符號 `.` (點) 和 `..` (兩個點)。
    
    符號 `.` 指的是當前目錄，`..` 指的是當前目錄的父目錄。
    
    根據上面的圖，假如當前目錄為 jono ，如果要用相對路徑切換到photos,就這樣寫 `cd ./photos` ，也可以直接寫 `cd photos` ，
    
    假如當前目錄為 cory ，如果要用相對路徑切換到 photos,就這樣寫 `cd ../jono/photos` 。其中 兩個點 `..` 表示上級目錄。當然也可以使用絕對路徑 `cd /home/jono/photos`
    

## **查看目錄和文件**

查看目錄內容 或者某個文件的屬性 使用命令 `ls`，就能看到 當前目錄下所包含的文件和子目錄列表。通過它可以知道目錄里面包含的內容，也可以知道 文件和目錄的 屬性。

Linux系統可以根據 的類型（文件還是目錄）和 副檔名 決定 列出 時的顏色。這些都是可以配置的。

目錄是藍色、文件都是白色、可執行文件是綠色

除了當前工作目錄以外，也可以指定要列出內容的目錄，例如 `ls /home/byhy/`

---

- 經常使用 ls 命令的“-l”選項，可以顯示出更多的信息：`ls -l`
    
    各個字段的含義如下：
    
    `rw-r--r--` 文件的訪問權限。第一個字元指明文件類型。在不同類型之間， 開頭的“－”說明是一個普通文件，“d”表明是一個目錄。其後三個字元是文件所有者的 訪問權限，再其後的三個字元是文件所屬組中成員的訪問權限，最後三個字元是其他人的訪問權限。這個字段的含義在後面用戶權限那一章會詳細講解。
    
    `1` 文件的硬鏈接數目。
    
    `byhy` 文件所有者的用戶名。
    
    `byhy` 文件所屬用戶組的名字。
    
    `13` 以字節數表示的文件大小。
    
    `May 10 10:36` 上次修改文件的時間和日期。
    
    `byhy.txt` 文件名。
    

## **查看文本文件內容**

對於比較短的文件， 可以直接用命令cat將文件的內容顯示到屏幕上。

```docker
[byhy@izbp16hara3tw8kbagjotqz ~]$ cat byhy.txt
byhy testing
```

說明byhy.txt 的文件內容就是 一行 `byhy testing`

## **創建目錄**

mkdir 命令是用來創建目錄的。

- `mkdir byhy1` - 會在當前目錄下，創建一個名為"byhy1"的目錄，而
- `mkdir byhy1 byhy2 byhy3` - 會創建三個目錄，名為 byhy1, byhy2, byhy3。

如果我們要創建好幾層的目錄，比如 /root/byhy/python/lesson1,

直接這樣寫命令 `mkdir /root/byhy/python/lesson1` shell 會報錯，因為系統中可能還 沒有 /root/byhy/python 這個目錄。

一種方法是：依次 創建 每一級目錄， 像這樣

- `mkdir /root/byhy`
- `mkdir /root/byhy/python`
- `mkdir /root/byhy/python/lesson1`

更簡單的方法是，使用參數 -p

- `mkdir -p /root/byhy/python/lesson1`

## **删除文件和目录**

- `rm` 命令後面 直接加上要刪除的文件。
    
    `rm file1 file2`
    

當我們要刪除目錄的時候 ，需要加上 `-r` 選項，否則會報錯，要這樣寫

`$ rm -r dir1`

- `r` 參數 也可以詳細的寫成 --recursive 。 它表示要 遞歸地刪除文件。 這意味著，如果要刪除一個目錄，而此目錄 又包含子目錄，那麽子目錄也會被刪除。
- `f` 參數 也可以詳細的寫成--force 。 它表示忽視不存在的文件，不顯示提示信息。
    
    通常 `-r` 和 `-f` 參數會一起使用。
    
    `rm -rf file1 dir1 file2 dir2`
    
    如果文件 file1，或目錄 dir1 不存在的話，rm 仍會繼續執行，不會報錯
    

<aside>
⚠️ 執行 rm 操作 要非常小心， rm 不像Windows里面有回收站，一旦用 rm 刪除了一些東西，想再恢覆是相當麻煩的。

</aside>

## **通配符**

Linux 提供了一組特殊字元來匹配 文件名中的各部分內容，這些特殊字元叫做 `通配符` 。

當前目錄下有這樣一些文件

> `byhy1.txt  file1.jpg  file2.jpg  file3.jpg file5.jpg  hy2.jpg hyby.jpg`
> 
- 可以寫 `rm -f file*.jpg` 要刪除 其中 所有 以file開頭， 副檔名為 .jpg 的文件

### **常用的通配符**

- `*` 匹配任意 `多個` 字元（包括零個或一個）
- `?` 匹配任意 `一個` 字元（不包括零個）
- `[abcd]` 匹配abcd中任意一個字元

### 一些示例用法

- `*` 表示 所有文件（或目錄）
- `by*` 表示 文件名以“by”開頭的文件（或目錄）
- `by*.py` 表示 以"by"開頭，中間有任意多個字元，並以".py"結尾的文件（或目錄）
- `byhy????` 表示 以“byhy”開頭，其後緊接著 `4個字元` 的文件（或目錄）
- `[byh]*` 表示 文件名以"b","y",或"h"開頭的文件（或目錄）
- `byhy[0-9][0-9]` 表示 以"byhy"開頭，並緊接著2個數字的文件（或目錄）

很多 Linux命令，只要它們使用的參數是文件名，都可以使用通配符， 比如 `ls、cp、rm、mv` 等等

<aside>
⚠️ **注意：**rm命令時，使用通配符特別要小心。 很多人 曾經 為此 流過 悔恨的淚水。

比如，你想刪除一個目錄中的所有 jpg 文件。你應該這樣寫 `rm *.jpg`

如果你不小心在 “*” 和 “.jpg” 之間多輸入了一個空格，就像這樣： `rm * .jpg`

這個 rm 命令會刪除目錄中的所有文件，還會提示沒有文件叫做 “.jpg”。

**建議：**只要使用 rm 命令里面有通配符， 一定要在執行之前 慎重的 思考 10秒鐘以上， 再敲回車鍵。

</aside>

## **覆制文件和目錄**

- `cp` 命令， 用來 覆制文件或者目錄。

> 假設 byhy1 是一個文件，可以輸入`cp byhy1 byhy2`
> 
> 
> > 如果 byhy2 不存在， 會創建一個新文件 byhy2 ，並把 byhy1內容 拷貝到byhy2中。
> > 
> 
> > 如果 byhy2 存在， 會把 byhy1內容 拷貝到byhy2中， 覆蓋byhy2 原來的內容。
> > 

如果要拷貝的是一個目錄， 則 需要加上 `-r` 選項

- 指定 `r` 或者 --recursive 會遞歸地覆制目錄及目錄中的內容。

> 輸入 `cp -r  frontend frontend2`
> 
> 
> > 如果 frontend 里面有好多級子目錄和文件，全部都會被拷貝過去。
> > 
- 可以拷貝 文件或者目錄到 另外一個目錄中，比如

> 輸入`cp -r file1 dir1 dir2`
> 
> 
> > 覆制文件 file1 和 目錄dir1 到目錄 dir2中。目錄 dir2 必須存在。
> > 

> 輸入 `cp dir1/* dir2`
> 
> 
> > 這里使用通配符，可以把目錄 dir1 中的所有文件都 覆制到目錄 dir2 中。
> dir2 必須已經存在。
> > 

## **移動文件目錄、重命名文件目錄**

mv 命令可以 `移動` 文件或者目錄， 也可以 `重命名` 文件或者目錄

mv 使用方法與 cp 很相像。

> 假設 byhy1 是一個文件，可以輸入 `mv byhy1 byhy2`
> 
> 
> > 如果 byhy2 不存在， 會把文件 byhy1 改名為 byhy2 ，並且把 byhy1內容 拷貝到byhy2中。
> > 
> 
> > 如果 byhy2 存在， 會把文件 byhy1 改名為 byhy2， 等於刪除了原來的 byhy2。
> > 

> 假設 dir1 是一個目錄，可以輸入 `mv dir1 dir2`
> 
> 
> > 如果目錄 dir2 不存在，就會把 dir1目錄 改名為 dir2。
> > 
> 
> > 如果目錄 dir2 存在，就會把 dir1（及它的內容）移動到目錄 dir2。
> > 

> 假設 byhy1 是一個文件，dir1 是一個目錄，可以輸入`mv byhy1 dir1 dir2`
> 
> 
> > 這樣寫的話， 如果目錄 dir2 存在，就會 移動文件 byhy1 和 目錄 dir1（及它的內容）到目錄 dir2。
> > 

## **在文件中查找字元串**

在 Linux 操作過程中，經常需要在一個文本文件中 查詢包含特定關鍵字的那些行的信息。

比如，需要在 日志文件 django.log 中查看所有包含了 Error 關鍵字的行。

除了可以使用vi打開這個文件，然後再底行模式輸入 `/Error` 查看。

> 更快捷的方式，就是 使用 `grep`命令
> 
> 
> > `$ grep Error django.log`
> 1130_15:57:28 Internal Server Error: /api/cust/pages
> raise ExpiredSignatureError('Signature has expired')
> jwt.exceptions.ExpiredSignatureError: Signature has expired
> 1130_16:00:20 Internal Server Error: /api/cust/pages
> raise ExpiredSignatureError('Signature has expired')
> jwt.exceptions.ExpiredSignatureError: Signature has expired
> 1130_16:08:38 Internal Server Error: /api/cust/pages
> raise ExpiredSignatureError('Signature has expired')
> jwt.exceptions.ExpiredSignatureError: Signature has expired
> > 

> 如果想同時顯示各行的行號，可以加上參數 `-n`
> 
> 
> > `$ grep Error django.log -n`
> 1:1130_15:57:28 Internal Server Error: /api/cust/pages
> 18:    raise ExpiredSignatureError('Signature has expired')
> 19:jwt.exceptions.ExpiredSignatureError: Signature has expired
> 20:1130_16:00:20 Internal Server Error: /api/cust/pages
> 37:    raise ExpiredSignatureError('Signature has expired')
> 38:jwt.exceptions.ExpiredSignatureError: Signature has expired
> 39:1130_16:08:38 Internal Server Error: /api/cust/pages
> 56:    raise ExpiredSignatureError('Signature has expired')
> 57:jwt.exceptions.ExpiredSignatureError: Signature has expired
> > 

> 如果你要查找的不僅僅是Error 這樣的 一個單詞，而是一段句子，比如 要找 `Internal Server Error`就需要使用雙引號，這樣寫
> 
> 
> > `$ grep "Internal Server Error" django.log -n`
> 1:1130_15:57:28 Internal Server Error: /api/cust/pages
> 20:1130_16:00:20 Internal Server Error: /api/cust/pages
> 39:1130_16:08:38 Internal Server Error: /api/cust/pages
> 58:1130_16:09:16 Internal Server Error: /api/cust/pages
> > 

> 如果你要查找上下兩行的句子，可以用參數 `-C`
> 
> 
> > `$ grep Error django.log -n -C 2`
> > 

> 如果你要查找上面兩行的句子，可以用參數 `-B`
> 
> 
> > `$ grep Error django.log -n -B 2`
> > 

> 如果你要查找下面兩行的句子，可以用參數 `-A`
> 
> 
> > `$ grep Error django.log -n -A 2`
> > 

# **用戶管理和文件權限**

## **用戶和用戶組**

Linux 系統有個特殊的用戶 `root` ， 通常是系統管理員使用該用戶。

- root 用戶
    
    具有系統中最高的權限，比如：可以創建其它用戶、停止其它用戶進程、修改一些Linux系統配置文件、訪問其它用戶文件。
    
    而其它用戶則是有權限限制的，上面說的root用戶的特權，其它用戶通常是沒有的。
    
    之所以要有這樣的權限區別，就是防止一些用戶不小心（或者故意）做出的破壞。
    
- 用戶 ID
    
    Linux系統中，每個用戶用戶 都對應一個`用戶 ID`。
    
    `用戶ID` 就是一個數字，因為計算機處理數字更加方便。
    
    用戶的 ID 與用戶的信息就存儲在文件 /etc/passwd 當中。
    
- GroupID
    
    每個用戶可以屬於一個或者多個 `用戶組` ，每個用戶組對應一個 `GroupID` 。
    
    `GroupID` 的信息存儲在文件 /etc/group 當中。
    
    系統管理員可以對某個用戶組中的所有用戶進行統一管理，比如分配權限等。
    

### **添加用户**

Linux系統中創建用戶，可以使用命令 `adduser` ，隨後輸入該用戶的密碼2次，並且一路按回車確認信息。

<aside>
⚠️ 該命令需要root權限，所以用root用戶登錄，

</aside>

> 使用命令 `cat /etc/passwd` 查看文件內容 ****
> 
> 
> > /etc/passwd文件每行對應一個用戶的信息。
> > 
> 
> > 一行中的字段用":"隔開。每個字段的含義分別是 
> `用戶名:密碼:ID:Group ID:描述信息:home目錄:預設shell`
> > 

> `adduser`同時也為該用戶創建了一個用戶組， 組名就叫 byhy2 ，如下所示
> 
> 
> > root@byhy-server:~# `groups byhy2`
> byhy2 : byhy2
> > 

> 創建用戶的時候，可以加入一個指定的組，而不是新建一個組，
> 
> 
> > `adduser --ingroup root byhy`
> > 
> 
> > 就在創建byby用戶的同時，把它加入到 root 這個用戶組里面了。
> > 

<aside>
⚠️ 另外`adduser`命令 還為該用戶創建了一個 home目錄（這里就是 /home/byhy2）， 該目錄作為byhy2用戶登錄後使用的 `主目錄` ，該目錄屬於byhy2用戶所有。
這里 `/home/byhy2` 就是 `byhy2` 這個用戶的 **用戶根目錄** ， 或者說 **用戶主目錄**

</aside>

### 設置密碼

使用命令`adduser`添加用戶時，就會設置密碼。

如果後面你想更新密碼了怎麽辦？ 使用命令 `passwd`

<aside>
⚠️ 只有root用戶才可以給其他用戶設置密碼，普通用戶只能修改自己的密碼。

</aside>

### 刪除用戶

如果要刪除用戶，使用命令 `deluser`

### 用戶間切換

切換用戶使用命令 `su` ， 英文意思 substitute user 或者 switch user 。

> 比如 su - byhy
> 
> 
> > 切換命令中使用 `-` 符號，表示要重新創建用戶環境，就像使用byhy用戶重新登陸一樣。
> > 
> 
> > 切換不使用符號 `-` ，比如 `su byhy` ，就會使用當前的用戶的環境（保留現有的環境變量），切換到新用戶byhy
> > 

<aside>
⚠️ 如果現有用戶不是root 用戶，切換到其他用戶用戶，需要輸入密碼。
如果是root用戶則不需要輸入密碼。

</aside>

### 登出用戶

如果要刪除用戶，使用命令 `exit`

<aside>
⚠️ 用戶登入具有層級關係。
例如用戶登入的順序是A→B→C→D
在用戶D的環境下使用`exit`指令會回到用戶C

</aside>

### **查看用户组**

使用命令 `groups` 查看自己属于哪个用户组。

> byhy@byhy-server:~$ `groups`
byhy adm cdrom sudo dip plugdev lxd
> 
> 
> > 其中第一个 byhy 是byhy用户的 `主用户组（primary group）` ，其它的是 `从用户组（secondary group）`
> > 

<aside>
⚠️ /etc/passwd 文件里面记录的是用户的主用户组

</aside>

要查看其它属于哪个用户组，使用命令 `groups <用户名>` 

> byhy@byhy-server:~$ `groups root`
root : root
byhy@byhy-server:~$ `groups byhy`
byhy : byhy adm cdrom sudo dip plugdev lxd
> 

要查看某个组里面有哪些用户可以直接看/etc/group 文件，

也可以使用指令`grep '^sudo' /etc/group`但是这样只能查看到从用户组为该组的用户。

据[这个帖子](https://serverfault.com/questions/605812/etc-passwd-shows-user-in-a-group-but-etc-group-does-not)的说明，/etc/group里面记录的从用户组用户。

也可以使用命令`groupmems -g groupname -l`

### 添加用戶組

增加一個新的用戶組使用 `addgroup` 命令。

> `addgroup byhyusers`
> 
> 
> > 此命令向系統中增加了一個新組byhyusers。
> > 

### 刪除用戶組

如果要刪除一個已有的用戶組，使用 `delgroup` 命令

> `delgroup byhyusers`
> 
> 
> > 此命令從系統中刪除組byhyusers。
> > 

### 改變用戶所屬組

 如果要將一個用戶從g1改到g2，需要root用戶使用 `usermod` 命令，其格式如下：

`usermod –g g1 byhy` 命令將用戶byhy的 主用戶組（primary group）設置為 g1 。

<aside>
⚠️ 注意：主用戶組只能有一個

</aside>

`usermod –G g2,g3 byhy` 命令將用戶byhy用戶的 從用戶組（secondary group）設置為：g2，g3

<aside>
⚠️ `從用戶組` 可以有多個。

</aside>

`usermod -a -G g1,g2 byhy` 命令給用戶byhy `再添加` 兩個從用戶組（secondary group） g2，g3 ，原來所屬的從用戶組仍然也在

<aside>
⚠️ 注意： 有 `-a` 參數是**添加**`從用戶組`， 沒有 `-a` 參數是**設置**從用戶組

</aside>

## **Linux 文件訪問權限**

訪問有三種權限： 讀（用字母r表示）、寫（用字母w表示）、執行（用字母x表示）

> 某個用戶 對於一個 文件 ：
> 
> 
> > 有讀權限，表示該用戶可以讀取文件的內容，
> > 
> 
> > 有寫權限，表示該用戶可以修改文件內容，
> > 
> 
> > 有執行權限, 表示該用戶可以運行該文件（當然該文件應該是可執行文件）
> > 

> 某個用戶 對於一個 目錄 ：
> 
> 
> > 有讀權限，表示該用戶可以查看該目錄里面的內容，
> > 
> 
> > 有寫權限，表示該用戶可以在該目錄里面 創建 和刪除 文件，
> > 
> 
> > 有執行權限, 表示該用戶可以使用 cd命令，進入該目錄
> > 

對某個文件或者目錄，Linux系統需要說明 `三種類型的用戶` ，分別具有怎樣的權限

- 文件的所有者，英文叫 owner ， 也就是該文件的創建者
- 文件歸屬的用戶組里面的用戶 ，英文叫 grouper
- 其他用戶 (非owner和非grouper)

<aside>
⚠️  Linux系統需要為每個文件和目錄，指定這個三種類型的用戶，具有什麽r、w、x里面的哪些權限

</aside>

文件存取權限的顯示 可以通過`ls -l`命令顯示，如：`$ ls -l file1`

顯示如下：

`$ ls -l mysql57-community.rpm 
-rwxr-xr--. 1 root root 9224 Sep 12  2016 mysql57-community.rpm`

其中：

- 第1字元”-”或”d”表示該檔案是文件或是資料夾
- 第2-4字元"rwx"表示此文件所有者root 對此文件的操作權限是為"可讀、可寫、可執行",
- 第5-7字元"r-x" 表示此文件所歸屬的root組內的用戶對此文件的操作權限是"可讀、不可寫、可執行"，
- 第8-10字元"r--" 表示其他用戶對此文件的操作權限是"可讀、不可寫、不可執行"

### 修改文件訪問權限

<aside>
⚠️ 文件的 **所有者** 或者 **root** 用戶可以修改文件的訪問權限

</aside>

用 `chmod` 命令修改文件的存取權限，格式如下**：**

`chmod [who][op][permission] file...`

**[who] 表示用戶類型，它的內容為以下一項或多項:**

- `u` 擁有者(user --- owner)
- `g` 與擁有者同一組的用戶(group)
- `o` 其他人(other)
- `a` 所有人(all)

**[op] 表示動作，，它的內容為以下一項：**

- `+`  表示要加上permission指定的權利
- `-`  表示要取消permission指定的權利

**[permission] 為存取權限，它的內容為以下一項或多項：**

- `r` 表示可讀
- `w` 表示可寫
- `x` 表示可執行

比如：

> `chmod u+w file1` ，該命令添加了 擁有者對file1文件的寫權限
> 

> `chmod u-x file1` ，該命令去掉了 擁有者對file1文件的執行權限
> 

> `chmod ug+rwx file1` ，該命令添加了 擁有者和同組用戶 對file1文件的 讀、寫、執行權限
> 

> `chmod a+rwx file1`，該命令添加了 所有人 對file1文件的 讀、寫、執行權限
> 

> `chmod o+rx /root` ， 該命令添加了 其它組 對 目錄 `/root` 的可讀可執行權限。 對於目錄來說 ，可執行權限意味著，用戶可以 `cd 進入` 到這個目錄。
> 

> `chmod -R o+rx /root` ， 參數 `-R` 表示遞歸的意思，該命令執行結果是：其它用戶可以對 `/root 目錄以及所有它的子目錄、子文件` 都有 可讀可執行權限 。
> 

### **改變文件所有者及文件所在組**

`chown` 將指定文件的擁有者改為指定的用戶或組。

該命令的參數中，用戶可以是用戶名或者用戶ID；組可以是組名或者組ID。

文件是以空格分開的要改變權限的文件列表，支持通配符。

系統管理員經常使用`chown`命令，在將文件拷貝到另一個用戶的名錄下之後，讓用戶擁有使用該文件的權限.

<aside>
⚠️ **注意：**必須是有root權限的用戶才能改變文件所有者。

</aside>

改變文件所有者的命令格式如下:

`chown [選項]... [所有者][:[組]] 文件...`

> `chown byhy test1` ，就把文件test1的所有者變更為用戶byhy
> 

> `chown byhy:byhy test1` ，就把文件test1的所有者變更為用戶byhy，所屬組變為byhy
> 

> `chown -R byhy dir1` ，就把**目錄dir1以及下面所有的子目錄和文件**的所有者變更為用戶byhy
> 

可以用命令`chgrp`改變文件所有者組，格式如下:

`chgrp [選項] [組] [文件]`

<aside>
⚠️ **注意：**必須是有root權限的用戶才能改變文件組別的歸屬

</aside>

> `chgrp byhy test1` ， 就把文件test1的用戶組變更為組byhy
> 

## **sudo：以root權限運行程序**

有的程序需要做一些特權操作，比如前面講的用戶賬號管理：adduser、deluser。

通常要執行這樣的程序必須以root用戶登錄去執行。

但是，有時卻希望給某幾個信任的用戶授予這樣的權限，允許他們某次可以申請以以root權限執行該程序。

Windows里面的 `以管理員權限` 運行某個程序，而Linux上就是使用命令 `sudo` 

例如：`sudo adduser byhy3`就是申請以root權限運行 `adduser byhy3` 這個命令。

<aside>
⚠️ 不是說申請運行就一定可以的，前提是當前登錄的賬號 要在系統設置里面 允許這樣做。

</aside>

這個設置是在 /etc/sudoers 里面配置的。 如下

> `vi /etc/sudoers`
…
root    ALL=(ALL:ALL) ALL
> 
> 
> > root    可以以任何帳號登入，可以以任何群組登入，可以使用所有命令
> > 
> 
> %admin         ALL=(ALL) ALL 
> %sudo          ALL=(ALL:ALL) ALL 
> 
> > `%` 代表直接給予某個用戶組特定權限
> > 
> 
> byhy2, byhy3   ALL = /sbin/shutdown, /sbin/reboot
> 
> > byhy2, byhy3 可以從任何帳號登入，僅能執行/sbin/shutdown, /sbin/reboot兩條命令
> > 

通過配置這個文件，可以設置

哪些用戶（或者哪些組里面的用戶） ，在什麽地方， 以 哪些賬號的權限 ， 運行哪些程序。

一般不建議直接修改這個文件， 防止語法寫錯，導入整個規則被破壞。

而是使用命令 `visudo` 命令修改， 這個命令可以對錯誤的修改做檢查，防止意外。

通常會給某個組設置規則， 然後只需要把某些用戶加入組中即可。

比如，Ubuntu上可以把某個用戶加入 sudo 這個組， 既可以擁有 任何地方、以任何賬號的權限、運行任何程序 的能力。

把用戶加入組的命令，就是使用 `usermod`， 上面已經講過。

<aside>
⚠️ 注意：通常修改組後，該賬號需要重新登錄(`exit`)，才有組的sudo 權限。

</aside>

# **進程管理**

## **進程的概念**

大家比較熟悉 Windows 下的可執行文件，就是那些副檔名為exe的文件。

程序運行起來後，我們把這個程序正在運行的 `實例` 稱之為 `進程` 。

操作系統對每個進程都分配一個數字標記，稱為 Process ID (PID)。

Windows進程的信息可以通過 任務管理器看到。如下所示

![](https://cdn2.byhy.net/imgs/gh/36462795_58363931-aeae2a80-7ede-11e9-9d34-8996e8a55a28.png)

上圖中，正在運行的計算器程序 Calculator.exe 的進程PID就是 3164

在Linux系統中進程也有PID。正在運行的交互式命令行程序 Shell， 它就是一個進程。

- 可以用命令 `ps` 查看進程信息的命令。
    
    > `$ ps
      PID TTY          TIME    CMD
     4786 pts/0    00:00:00   bash`
    > 

如上所示，當前bash shell的 進程 PID 為 4786

## 進程的創建與查看

Linux中，一個進程A里面可以創建出一個新的進程B，進程A就叫做進程B的 `父進程` (parent process)，進程B叫做進程A的子進程（child process）。

最典型的例子，在shell中運行的程序（命令），都是shell進程創建的，所以shell進程就是他們的父進程。

Linux中，主要是通過`ps`命令來查看進程信息的，我們運行命令`ps -f` ，結果如下所示

> [byhy@localhost ~]$ `ps -f`
UID          PID      PPID  C STIME    TTY       TIME         CMD
byhy        4786  1780   0  06:45     pts/0    00:00:00   -bash
byhy        1865  4786   0  06:55     pts/0    00:00:00   ps –f
> 

其中 PPID 這一列就是該進程的父進程的PID，可看出 `ps` 命令對應的進程的父進程PID為4786，正是 bash 進程的 PID 。

### 常用 `ps`命令 的例子：

- `ps` 顯示和當前終端有關的進程信息
- `ps -u byhy` 顯示byhy用戶所創建的進程信息
- `ps -f` 詳細顯示每個進程信息
- `ps -e` 顯示所有正在運行的進程信息
- `ps -ef` 顯示當前系統所有的進程
- `ps –ef | grep python` 查找python進程
    - `|` 用來儲存`ps –ef`的輸出結果當作`grep python`的Input

## **進程的前台、後台轉換**

Linux終端通過Shell程序來接收用戶輸入的命令，並且執行命令。

我們在Shell里正在執行的，和用戶進行人機交互的進程叫 `前台進程` (foreground process)

前台進程可以接收鍵盤輸入並將結果顯示在顯示器上。

用戶敲入什麽命令，shell就會啟動對應的程序，運行在 `前台` 。

比如，可以用vi 編寫一個 下面的Python程序到 Linux主機上，代碼文件名可以為t1.py

```python
while True:         
	info = input("please input something:")     
	print("you input:%s\\n\\n" % info)
```

然後使用命令 `python3 t1.py` 運行。

可以發現及時這個 python 程序變成了前台進程，接收用戶的輸入。

有些程序運行時，並不需要和用戶進行交互，也就是說，不需要用戶輸入什麽內容。 比如一個日志分析程序，一個定時清理磁盤文件的程序。

比如，下面這樣的一個Python程序 t2.py：

```python
import time 
while True:         
	print("execute a task ...")     
	time.sleep(2)     
	print("done, wait for an hour to proceed...")     
	time.sleep(3600)
```

可以執行命令 `python3 t2.py` 運行它

這樣的程序，運行期間，如果在前台執行，我們只能等待它結束，不然我們沒法執行下個程序。

但是既然不需要用戶輸入信息，在前台執行沒有太大意義，應該要讓它在 `後台` 執行。

要讓它在後台運行，啟動時只需在命令行的最後加上 `&` 符號。

比如 `python3 t2.py &`

後台運行的進程我們叫後台進程(background process)，或者後台任務 ，它不直接和用戶進行交互的進程。用戶一般是感覺不到後台進程程序的運行。

當在後台運行命令時，有時需要其輸出重定向輸出到一個文件中去，以便以後檢查。

比如 在後台運行find命令，在當前目錄及其子目路下查找文件名為 byhy 的文件。

> `$ find . -name byhy -print > log.txt & 
4762`
> 

重定向的概念後面會講。

## nohup

可以執行命令的時候，使用 `&` 結尾使進程在後台運行。

如果終端關閉，那麽程序也會被關閉，因為shell會發送SIGHUP信號給這些進程。進程接收的該信號，如果沒有特別的處理，默認就會**結束運行**。

為了避免這種情況，那麽我們就可以使用 `nohup` 這個命令。

比如我們有個 test.sh 需要在後台運行，並且希望在後台能夠一直運行，即使關閉了終端，也不退出。那麽就使用nohup：

`nohup /root/test.sh &`

## 進程**的终止**

進程一般有兩種終止方式。

- 自行終止
    
    有的進程執行完一段任務後，就自行退出了。
    
    比如上面的 `ps` 命令，它執行完查看進程信息的任務後，就會結束。
    
    也有的不是自動退出，而是用戶操作它，讓它退出。
    
    比如 我們在Shell進程中運行`exit`命令後，該Shell進程就會退出。
    
    也有的是異常退出，比如程序有個bug（比如代碼里面有除以0的指令），該程序無法執行下去，也會終止。
    
- 被強行殺死
    
    有的進程一直不結束，如果用戶覺得該進程應該被強行結束了，該怎麽辦呢？
    
    對於一個**前台進程**，要結束它，只要按組合鍵： `Ctrl + C` 。
    
    對於一個後台運行的進程 ，要強行結束它，可以使用 `kill -9`  命令強行殺死該進程。
    

比如上面的 python3 t2.py 命令運行的進程。 可以先用`ps`命令查出它的進程PID，

> `ps -f | grep t2.py | grep -v grep`
> 
> 
> 儲存`ps –f`的輸出結果當作`grep t2.py`的輸入，再把搜尋結果當作`grep -v grep` 的輸入
> 
> `-v` 是在搜索時去除包含grep的資料
> 

如上所示的python進程PID為2386，我們再執行命令 `kill -9 2386` 。 這樣就強行停止了該進程。

要注意的是， 上面所示的進程啟動它的用戶為byhy，那麽只能是用戶byhy或者root用戶才能殺死該進程

# **重定向和管道**

### 什麽是終端設備

人在操作電腦時，其實是和 運行著的程序（術語稱之為：進程） 在打交道（術語稱之為：交互）。

進程是在電腦CPU中執行的代碼指令。

所以，我們和進程交互的時候，必須有個設備才能通過它輸入信息給進程，並且顯示進程輸出信息。

<aside>
⚠️ **注意：**終端設備 只有 顯示器 和鍵盤 ， 是沒有 主機部分的。它和主機之間有根信號線，傳遞用戶通過鍵盤輸入的信息給程序，並顯示程序輸出的信息。

</aside>

Linux進程在啟動後，通常就會打開3個文件句柄，標準輸入文件（stdin），標準輸出文件（stdout）和 標準錯誤文件（stderr）。

Linux進程，要從用戶那里讀入輸入的信息，就是從stdin文件里面讀取信息，要 輸出 信息 給用戶看 都是 輸出到 stdout， 要 輸出 錯誤提示 給用戶看 都是 輸出到 stderr。

而默認情況下這三個文件stdin、stdout、stderr 都指向 —— 終端設備。

也就是說：

Linux進程從stdin里面讀取信息其實就是從終端設備（比如終端模擬程序Putty）讀取信息；

Linux進程寫入信息到stdout或者stderr，其實就是打印到終端設備上。

如下圖所示

![](https://cdn2.byhy.net/imgs/gh/36462795_57582487-ff458100-74f7-11e9-9fcc-0142ae49655b.png)

比如，運行下面的Python程序，要讀入信息，就是從終端讀入，因為stdin指向終端設備

```python
input("please input info:")
```

再比如：下面的命令echo輸出給用戶看的，就是輸入到終端上，因為stdout指向終端設備

> [root@bogon ~]# `echo "hello byhy"`
hello byhy
> 

## **Stdout、Stderr重定向**

如果在Shell中輸入命令的時候，使用 `>` 符號， 就可以將輸入信息輸出到其他文件（包括設備文件）中去。比如 `ps > out`

運行後，會發現out文件里面出現了ps的輸入信息，而Putty終端窗口里面則沒有任何內容打印出來了。

這個 `>` 就是 stdout 重定向符號， 它表示 stdout 不是指向 終端設備了，而是 重定向到 out 文件。 所以stdout 指向了 out 文件， 輸入的信息就到 out 文件了。 終端屏幕上就沒有信息了。

這時對應的示意圖如下

![](https://cdn2.byhy.net/imgs/gh/36462795_57582500-29973e80-74f8-11e9-819b-7adf5484ec05.png)

而 Stderr 的重定向符號 是 `2>` 。 注意 2 和 >之間不能有空格。

比如執行下面的命令，其中hhhh是個不存在的文件

`ps hhhh 2> err`

我們就會發現putty屏幕上沒有任何信息，而文件err里面則有。

如果要同時重定向stdout和stderr到同一個文件both中，命令寫法如下：

`command &> both`

如果要重定向stdout到out文件，並重定向stderr到err文件，命令寫法如下：

`command > out 2>err`

## stdin重定向

也可以在命令中，將標準輸入stdin 重定向，使用符號 `<`

用 vi 創建一個 Python 代碼文件 `add.py` ，其內容如下

```python
for i in xrange(3):     
	data=input()     
	print ('%s+1=%s' % (data,int(data)+1))
```

該程序從stdin 讀取一個數字後，顯示其加1後的結果。

再創建一個文件 add.dat內容如下(注意3後面有個空行)

> 1
2 
3
> 

執行如下命令

> [byhy@localhost ~]$ `python3 add.py < add.dat` 
1+1=2 
2+1=3 
3+1=4
> 

不需要我們從終端輸入數字，該程序直接從文件 add.dat中讀取數據並執行操作了。

這個 `<` 就是 stdin 重定向符號， 它表示 stdin 不是指向 終端設備了，而是 重定向到 add.dat 文件。 所以 stdin 指向了 add.dat 文件， 程序就從add.dat 文件讀入信息 了。

這時該進程對應示意圖如下：

![](https://cdn2.byhy.net/imgs/gh/36462795_57582718-a0353b80-74fa-11e9-9c25-7419d4a0184b.png)

## 管道

上面曾經學習過`grep`命令，這個命令可以從文件中過濾出 **包含指定字符串模式** 的行。

比如我們有個文件file1，里面有的行包含了mike 這個詞。如果我們想把所有包含mike的行都找出來。 可以執行命令 `grep mike file1` 。

當`grep`命令中沒有文件參數的時候比如`grep mike`, 它就會等待我們在標準輸入（一般是putty終端設備）中輸入一行行的內容，進行實時的過濾

在Linux操作過程中，我們經常需要 **將一個命令的輸出的內容，給另一個命令作為輸入的內容** 進行處理。

比如，我們想查出進程號是 6536 的進程的信息。

我們用`ps -ef` 可以顯示出所有的進程信息，但是這里面的內容太多了，想過濾出其中包含 6536 字符串的行。

當然可以 用重定向符號 `ps –ef > info.txt` , 然後再使用grep從 info.txt中過濾 `grep 6536 info.txt`

但是這樣比較麻煩，我們可以使用 `管道操作符` 。

我們看 這個命令 `ps –ef | grep 6536`

注意其中的 豎線 `|`， 這個就是管道操作符，它起的作用就是

● 將 前面的 `ps –ef` 命令的stdout（本來是輸出到終端設備的） 重定向到一個 臨時管道設備里面，

● 同時 將後一個命令 grep 6536 的stdin重定向到這個臨時的管道設備。

那麽這時會發生什麽事情呢？`ps –ef` 命令的結果直接被 命令 `grep 6536` 過濾出來了。

這個過程可以用如下示意圖表示

![](https://cdn2.byhy.net/imgs/gh/36462795_57582696-6f550680-74fa-11e9-9af7-99c62c847d13.png)

# **常用命令**

## apt安裝軟件包

在 Ubuntu上，安裝軟件通常使用 `apt` （全稱 Advanced Packaging Tool） 軟件包管理工具安裝。

apt 能夠從指定的 apt 來源伺服器自動下載安裝包並且安裝，可以自動處理依賴性關系，並且一次安裝所有依賴的軟件包，無須繁瑣地一次次下載、安裝。

如果安裝Ubuntu時，沒有更換源，現在想換，可以修改配置文件 /etc/apt/source.list， 把里面來源伺服器域名改掉。

### apt 命令用法

- 安裝軟件 `apt install package1`
    
    安裝指定的安裝包package1, 比如 `apt install net-tools`
    
- 列出所有安裝信息`apt list --installed`
    
    顯示所有已經安裝的程序包
    
- 列出指定軟件信息`apt list package1`
    
    顯示指定程序包package1的安裝情況
    
- 刪除軟件 `apt remove package1`
    
    刪除程序包package1
    

### 更改來源伺服器步驟(不要真的做這件事)

1. 以root賬號登錄，或者後續命令前面加 `sudo` 以root執行
2. 執行命令 `cd /etc/apt` 進入到目錄 `/etc/apt` 下
3. 執行命令 `cp sources.list sources.list.bak` 先創建備份文件，這樣萬一改錯，可以有備份文件恢覆
4. 執行 `vi sources.list` 打開文件， 準備把域名從從 `cn.archive.ubuntu.com` 替換為 `mirrors.163.com`
5. 按 冒號，進入底行模式，輸入命令 `1,$s/cn.archive.ubuntu.com/mirrors.163.com/g` 進行替換
6. 確認一下域名修改正確後，輸入 `:wq` 保存退出。
7. 執行命令 `apt update` ， 讓修改生效

## 啟動、重啟、關閉服務

Linux上有些軟件程序是以服務的形式安裝的，比如 SSH 服務、 MySQL服務、 nginx服務等。

這些 軟件 的啟動、重啟、關閉 要使用特殊的命令

在當前的 Ubuntu 系統上，使用命令 `systemctl` 來 啟動、重啟、關閉 服務。

- 要查看 服務 ssh 狀態， 執行命令 `systemctl status ssh`
- 要啟動 服務 ssh， 執行命令 `systemctl start ssh`
- 要重啟 服務 ssh， 執行命令 `systemctl restart ssh`
- 要關閉 服務 ssh， 執行命令 `systemctl stop ssh`

## **打包與壓縮**

### 打包

Linux下打包的最常用命令是 `tar`命令，可将多个文件、目录打包到一个文件中。

`-c` 生成壓縮檔案

`-v` 顯示詳細訊息

`-f`  顯示所有內容

`-t` 查看內容但不解壓縮

`-x` 解壓縮

`-r` 往壓縮檔案內添加檔案

`-z`  同時打包並壓縮

`-j`  透過.bz2同時解壓並解包

- tar 命令打包
    
    下面是使用tar命令打包的操作演示：
    
    在当前工作目录下面创建3个文件，使用下列命令：
    
    `touch 123.txt 456.txt 789.txt`
    
    将这3个文件放到一个文件包files.tar,使用下列命令：
    
    `tar cvf files.tar  123.txt 456.txt  789.txt`
    
    也可以使用通配符，如 *.txt，这样的格式代表以txt结尾的文件
    
    `tar  cvf  files1.tar *.txt`
    
    tar命令同样可以打包目录，假设 当前目录下 byhy是一个子目录，byhy.txt是一个文件
    
    `tar cvf byhy.tar ./byhy  byhy.txt`
    
    这个命令就把目录 byhy 和 文件 byhy.txt 都 打包到 文件 byhy.tar 中了。
    
- tar 命令解包
    
    要 将 上面创建的 files1.tar 解压到当前目录，使用下列命令：
    
    `tar  xvf   files.tar`
    
- 查看 tar 包内容
    
    如果只是想查看 上面创建的 files1.tar 内容，使用下列命令：
    
    `tar  tvf   files.tar`
    
- 往 tar 包中添加文件
    
    如果想 在 files1.tar中 添加 新文件 newfile，使用下列命令：
    
    `tar  rvf  files.tar  newfile`
    
    注意：tar命令只是把文件、目录打包到一个文件中。 并不会压缩文件
    

### 壓縮

- `gzip` 壓縮和解壓
    
    `gzip` 命令用於文件的壓縮與解壓縮，壓縮後的文件名後綴為“.gz”
    
- 要壓縮文件abc.txt ，執行命令 `gzip abc.txt`
    
    這樣就產生了一個名為 abc.txt.gz 的壓縮後的文件
    
- 要 解壓文件abc.txt.gz，執行命令 `gzip -d abc.txt.gz`

gzip和 tar 的聯合使用

`tar`工具與`gzip`工具聯合使用，實現打包並壓縮、解壓縮並解包功能

假設 在當前目錄有如下3個文件 touch 111.txt 222.txt 333.txt

- 要打包並壓縮這3個文件，放到壓縮包文件 byhy.tar.gz里面，
使用命令 `tar zcvf byhy.tar.gz *.txt`
- 解壓縮並解包，使用命令 `tar zxvf  byhy.tar.gz`
    - `-z`  同時打包並壓縮
- `bzip2`、`zip` 壓縮、解壓
    
    `bzip2` 和 `zip`也是常見的壓縮解壓工具， 使用方法和 `gzip` 類似
    
    > .bz2
    解壓1：`bzip2 -d FileName.bz2`
    解壓2：`bunzip2 FileName.bz2`
    壓縮： `bzip2 -z FileName`
    .tar.bz2
    解壓：`tar jxvf FileName.tar.bz2`
    壓縮：`tar jcvf FileName.tar.bz2 DirName`
    .zip
    解壓：`unzip FileName.zip`
    壓縮：`zip -r FileName.zip DirName`
    > 

## top 查看系統進程的動態運行情況

執行`top`命令可以查看 當前系統中，運行的進程的信息。

- CPU 整體負載
    
    在這行顯示了 CPU 整體負載
    
- 各個CPU 的負載（按鍵盤1，可以在整體cpu和所有cpu之間切換）
    - 進程的CPU占用
        
        預設情況下，進程列表里就是按CPU占用率來排序的。
        
        如果不是，可以按快捷鍵大寫的P要求top按照CPU占用率來排序。（按b，再按x可以顯示當前排序列）
        
    - 整體內存使用量
        
        <aside>
        ⚠️ **注意：**顯示 2507692 free，並非只有 2507692 的內存可用。
        
        </aside>
        
        因為 buffer 和 cache 部分的內存都是臨時緩存用了， 其實也是可用的內存
        
        實際可用的內存大概是 free + buffers + cached
        
    - 各個進程對內存的占用（RES）
        
        按快捷鍵大寫的 M 可以 對進程列表按照內存使用率來排序
        
- 輸入 `top -p [進程ID]` 可以看特定進程的狀況

## 查看系統內存使用情況

`free`命令可以顯示Linux系統中空閒的、已用的物理內存及swap內存,及被內核使用的buffer。

## 查看設置系統時間

`date`可以用來顯示或設定系統的日期與時間。

- 顯示當前日期和時間`date`
- 設定日期 `# date -s 20161109`
- 設定時間 `# date -s 21:05:50`

## **查看系統版本**

- 執行命令 `uname –a` 查看系統內核版本信息
- 執行命令 `lsb_release -a` 查看Ubuntu系統版本信息

# 網絡**管理**

## 查看網絡接口IP地址

- 查看所有網絡接口的IP地址，可以使用命令 `ip addr`
    
    > $`ip addr`
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
    valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
    valid_lft forever preferred_lft forever
    2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 08:00:27:e1:71:e8 brd ff:ff:ff:ff:ff:ff
    inet 192.168.50.64/24 brd 192.168.50.255 scope global dynamic enp0s3
    valid_lft 86125sec preferred_lft 86125sec
    inet6 fe80::a00:27ff:fee1:71e8/64 scope link
    valid_lft forever preferred_lft forever
    > 
    
    上面顯示了 兩個網絡接口 lo 和 enp0s3。
    
    其中 lo 是環回接口。
    
    我們應該關注的是 enp0s3 這個接口。
    
    上面命令的結果顯示：enp0s3 這個接口 的 IPv4 地址是 192.168.50.64
    

## 啟用、禁用網絡接口

啟用和禁用網絡接口，常用的是 `ifup` 和 `ifdown` ，要使用root用戶執行

Ubuntu 現在預設fㄝ是沒有這兩個命令的， 可以先運行 `apt install ifupdown` 安裝一下。

- 啟用網絡接口 `ifup enp0s3`
    
    使用命令 `ifup`，比如下面的命令就是啟用網絡接口 enp0s3
    
- 禁用網絡接口 `ifdown enp0s3`
    
    使用命令 `ifdown`，比如下面的命令就是禁用網絡接口 enp0s3
    

## **ping 檢測網絡連通性**

我們經常需要檢查是否可以從本機訪問某個遠程主機，這時應該使用 `ping` 命令

- 命令`ping [ip]` 可以查看網路連線狀況
    - `ping [localhost](<http://localhost>)` 可以看本機自己連自己的IP
- 可以按 `ctrl+C` 終止測試。

## netstat 查看網絡狀態

Ubuntu 現在預設安裝的查看網絡狀態的工具是 Socket Statistics， 命令名為 `ss` 。

但是 目前這個工具使用還不是特別廣泛，目前查看網絡狀態大多數人還是會使用著名的 `netstat` 。

`netstat` 這個命令通常用來 查看各種與網絡相關的狀態信息，包括：網絡的連接、狀態、接口的統計信息、路由表、端口的監聽情況。

但是 Ubuntu 預設沒有安裝這個netstat， 可以使用命令 `sudo apt install net-tools` 安裝 net-tools 工具包後，即可使用。

常用參數：

- `-a` (all)顯示所有選項，默認不顯示LISTEN相關
- `-t` (tcp)僅顯示tcp相關選項
- `-u` (udp)僅顯示udp相關選項
- `-n` 不顯示端口協議名，顯示端口數字
- `-l` 只顯示 Listen (監聽) 的狀態端口
- `-p` 顯示建立相關鏈接的進程PID
- `-r` 顯示路由信息，路由表

Netstat 最常用的地方就是查看網絡連接情況，比如查看22端口上的tcp網絡連接情況

使用命令 `netstat -anp | grep 22 | grep tcp`

> [root@localhost ~]# `netstat -anp |grep 22 |grep tcp`
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      977/sshd
tcp        0     52 192.168.10.199:22       192.168.10.92:63911     ESTABLISHED 2011/sshd: root@pts
tcp6       0      0 :::22                   :::*                    LISTEN      977/sshd
> 

## ssh（secure shell）登錄遠程機器

在Linux下，也可以遠程登錄其他Linux主機，只需要運行ssh命令即可。

命令的格式如下 `ssh  用戶名@IP地址或機器域名`

比如，要使用 user1 賬號 遠程登錄 192.168.1.12 這台Linux機器，執行下面的命令

`[byhy@localhost ~]$ ssh user1@192.168.1.12`

一般首次登錄某個主機的時候，會出現如下提示：

> The authenticity of host '192.168.1.12 (192.168.1.12)' can't be established.
RSA key fingerprint is cf:2c:22:d1:e8:4e:f3:16:43:09:9c:c6:fe:fc:9a:22.
Are you sure you want to continue connecting (yes/no)?
> 

這是因為該遠程機器沒有被認證過（可能會有‘中間人’攻擊的安全隱患），讓你確認一下。這里如果是局域網里面的機器，一般安全沒有什麽問題，輸入yes並回車即可。

接下來，會提示輸入對應用戶的密碼，你輸入正確的密碼即可登錄。

## scp 拷貝文件

在Linux上，可以直接使用`scp`命令 和遠程Linux主機 進行文件的拷貝。

`scp`是secure copy的縮寫，意為文件安全拷貝，它可以將遠程Linux系統上的文件拷貝到本地計算機，也可以將本地計算機上的文件拷貝到遠程Linux系統上。

比如：

我們已經登錄到主機A上面，要將 /home/byhy1 目錄下面的文件abc.txt，拷貝到主機B的/home/byhy2目錄下面，主機B的IP地址為：192.168.1.12

我們要拷貝到 B主機， 必須要有B主機的用戶賬號， 假如B主機的賬號是 byhy2，應該這樣寫

`scp /home/byhy1/abc.txt byhy2@192.168.1.12:/home/byhy2`

接下來，會提示用戶輸入用戶byhy2的密碼，輸入正確密碼後，進行拷貝操作。

如果，我們要 在主機A上面，將主機B上面的文件/home/byhy2/123.txt 拷貝到主機A的/tmp/下面：

`scp byhy2@192.168.1.12:/home/byhy2/123.txt /tmp/`

<aside>
⚠️ 在windows機器上，可以使用 WinSCP 工具和遠程Linux主機 進行文件的拷貝。
這個工具安裝好後，創建一個到遠程Linux主機的連接，隨後只要在界面拖動文件即可完成下載，上傳文件。

</aside>

## wget下載

Linux中，要從網絡下載文件，可以使用 `wget`。

wget就是一個下載文件的命令行工具。

`wget <https://mirrors.aliyun.com/centos/timestamp.txt>`

## 防火墻

通常網站服務之類的產品運行在Ubuntu上，我們會開啟防火墻。防止惡意的網絡訪問和攻擊。

Ubuntu目前使用命令 `ufw` (uncomplicated firewall) 管理防火墻功能。

- 預設 `ufw` 是未被激活的，執行`ufw enable`
    
    <aside>
    ⚠️ 注意：這個命令最好是在 虛擬機終端執行。
    
    </aside>
    
    如果是Putty遠程登錄，並且當前沒有允許SSH訪問的ufw規則，執行這個命令可能就會斷開連接。
    
    可以執行如下命令檢查 當前的 防火墻設置`ufw status`
    
    或者查看更詳細的信息`ufw status verbose`
    

● 開放端口

如果我們允許 外面從網絡訪問 本機的 SSH TCP 服務端口 22 ，應該這樣執行命令

`ufw allow 22/tcp 解釋`

如果你知道端口對應的服務名，也可以使用名字。

比如下面的命令可以允許外面從網絡訪問 本機的 ssh 服務

`sudo ufw allow ssh`

比如下面的命令可以允許外面從網絡訪問 本機的 HTTP 服務端口 80

`ufw allow http`

● 刪除規則

要刪除一個前面設定的規則，執行下面的命令

`ufw delete allow http`

# 參考資料

[https://www.byhy.net/etc/linux/ubuntu/01/](https://www.byhy.net/etc/linux/ubuntu/01/)

[https://www.bilibili.com/video/BV1ng411575g/?p=1](https://www.bilibili.com/video/BV1ng411575g/?p=1)