# Github 心得

01~09堂線上講義：

[https://hexschool.tw/n1C7O](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqa3VHWHE5bHNwUWVjMTBKTGc0UFV4Y0FYcTFmZ3xBQ3Jtc0tsWmVDLW9mangwSGwtY3ZDallCLXlJOFdmRGpyNlB5ZXQtd2lJZV9VOXRZMXVqY1JJb3ZMRDQ3SmUtQkxwRkRuYVJ4a1V5UHpWd0ViXzcxUWI0ZXBtUXpZZG9xOUlnZFo5cGFQYWRCRlBtcW9xR3c0SQ&q=https%3A%2F%2Fhexschool.tw%2Fn1C7O&v=PNEM7CH3ZAg)

10~18堂線上講義：

[https://hexschool.tw/PDcLZ](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqbkhzcDR1UXgtY0ZFRVRGUFJHcEJFYjBQemFKQXxBQ3Jtc0tuOERnUER6aUpnMmtWZW1VYjlyRGxhQ1lsSk5RLXNXSUpuQWN3TzAyLVZ5M0ZzZ3NxNWNxaGFCbnlYbUxVWFJFODRCTk15NTZ0R0tKMGRmdWRiTUFYXzBxSllIWi12cVQ5eWVoYm0yQXF4UFctMGpQbw&q=https%3A%2F%2Fhexschool.tw%2FPDcLZ&v=PNEM7CH3ZAg)

19~25堂線上講義：

[https://hexschool.tw/qCPbw](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqbFRzUnBfS3hQTGZzbnlvT1B2WDQtRHBOY1ppUXxBQ3Jtc0trZkpqVWJRVTNSelFnVGRRTGxzQjVaUzNuMGZibFZ2YkRnNEhwRE5vZF8ySl9EOWxmSDl0WUhiNGtiVUU2UWlDcnVHZ2VwdmFaczdVckhvaHNTMEhfY0wzUkNyYUJ2VzgxRENvUVBhb05pWWpTdFFLbw&q=https%3A%2F%2Fhexschool.tw%2FqCPbw&v=PNEM7CH3ZAg)

26~32堂線上講義：

[https://hexschool.tw/v9bxz](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqbGE1bGZ5SWotSVgycnc4UjBWMF9EZjU3RThJUXxBQ3Jtc0tram9QQ0thU1V3R2hRaktzSXZNZ1NqZDg1b3pCU1NrT2RJVzg4Yl8yaE1RQkx0bHMtdkF6dnJMVEpROWtzMkc2RVpyQ0xWV0VuSDFwRmVmN1UydzR6SDJOT0VhODlZMzc3LVBKbm5rMWFYSzZJcHNnNA&q=https%3A%2F%2Fhexschool.tw%2Fv9bxz&v=PNEM7CH3ZAg)

33~36堂線上講義：

[https://hexschool.tw/jjq1M](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqbFlzZ19rZG5yN0xrTjRRSnNsemowQkFMTUlTd3xBQ3Jtc0ttQS1saUxSVnhLazlzdWdIalRxY0lUenRSR3ZGOEVrT09uenlfZGZrYWRwRHhYYXd0OThDZlh2OEQ5YkZ5U3lpcVh0RTJrdXNhcEFsWTdBS2JmZEVKUnpSbjJheUJfRU11VEh6azRzVUp5WWQ2QVFCOA&q=https%3A%2F%2Fhexschool.tw%2Fjjq1M&v=PNEM7CH3ZAg)

分支練習:

[https://learngitbranching.js.org/?locale=zh_TW](https://learngitbranching.js.org/?locale=zh_TW)

連猴子都懂得Git入門指南

[用Git版本控制【Git的基本介紹】 | 連猴子都能懂的Git入門指南  | 貝格樂（Backlog）](https://backlog.com/git-tutorial/tw/intro/intro1_1.html)

| 指令 | 功能 |
| --- | --- |
| git commit | 創建節點 |
| **git commit -m "添加add的說明"** |  |
| git branch | 創建分支 |
| git checkout <分支名稱> | 指到該分支最新位置 |
| git checkout <分支名稱>^ | 指到該分支最新節點的上一個 |
| git checkout [Commit] | 分出一個HEAD標籤，指到該節點位置 |
| git checkout -b <branch> | 在 checkout 命令給定 -b 參數執行，可以同時建立分支和切換至該節點。 |
| git merge [分支名稱] | 把該分支合併到當前分支(保留分支) |
| git rebase [分支名稱] | 把當前分支合併至該分支(直接移動) |
| git rebase -i HEAD~<數量> | 有介面的rebase |
| git branch -f <分支名稱1> <分支名稱2> | （強制）移動 <分支名稱1> 至 <節點名稱2> |
| git reset HEAD^ | 退回，至少需要一個^ |
| git revert HEAD |  發出一個退回的狀態(所以反而會多一個commit) |
| git cherry-pick <Commit1> <Commit2> <...> |  |

### 下指令指定某資料夾有git更新追蹤功能(常用功能)

1. 打開git bash
2. 輸入`cd "空格"`
3. 把該資料夾拉到git bash裡面(快速輸入路徑)
4. 輸入`git init`

### 確認版本指令

1. 打開git bash
2. 輸入`git bash`

### 更改個人資訊

- 輸入姓名：`git config --global user.name "雙引號內改ID"`
- 輸入個人的 email：`git config --global user.email "雙引號內改電子信箱"`
- 查詢 git 設定內容：`git config --list`

### 常用cmd指令

| **Windows** | **說明** |
| --- | --- |
| cd [路徑] | 前往資料夾路徑 |
| cd | 取得目前所在的位置 |
| dir | 顯示資料夾裡的檔案 |
| mkdir | 新增資料夾 |
| 無指令 | 開新檔案 |
| copy | 複製檔案 |
| move | 移動檔案 |
| del | 刪除檔案 |
| cls | 清除畫面上的內容 |

### 常用git指令

![Untitled](Github%20心得/Untitled.png)

| **Windows** | **說明** |
| --- | --- |
| `git init` | 初始化數據庫 |
| `git status` | 查詢當前狀態 |
| `git add` (.) | 將檔案加入到索引，用 ” . ”可以找所有檔案 |
| `git commit -m "新增網頁環境"` | 將索引檔案變成一個更新(commit) |
| `git log` | 觀察 commit 歷史紀錄 |
| `git clone 數據庫網址` | 下載遠端數據庫 |
| `git push origin master` | 更新遠端數據庫 |

### 打開 VSC 拉檔案進去

他自己會讀取git

### **Sourcetree軟體教學**

新增有.git資料夾的專案至軟體中

![Untitled](Github%20心得/Untitled%201.png)

### 本地Git綁定GitHub

1. 在github新建數據庫
2. 執行三行指令
    
    ```csharp
    git remote add origin https://github.com/zxcbig7/GitHubTest0215.git
    git branch -M main
    git push -u origin main
    ```
    

### 看.git中的config有無連結

![Untitled](Github%20心得/Untitled%202.png)

### Git 縮寫指令設定

```agda
$ git config --global alias.co checkout
$ git config --global alias.br branch
$ git config --global alias.st status
$ git config --global alias.ci commit
```

- 觀看所有 config 的設定：
    - Mac：`~/.gitconfig`
    - Win：`C:\Users\$USER`

### 甚麼是origin，master

如果要把同一個本地檔案上傳至兩個不同的數據庫，例如區分成正式主機與測試主機時。

本地Git綁定GitHub時，指令中的origin 是數據庫名稱，可以自己取，同樣的本地資料不可以有相同origin名稱。(下面範例是origin改git2)

```csharp
git remote add **git2** https://github.com/zxcbig7/GitHubTest0215.git
git branch -M main
git push -u **git2** main
```

### Git 與 Github 是什麼？

- Git 是一個分散式版本控制軟體，可藉由它產生一個**儲存庫( git Repository)**。
- Github：支援 git 程式碼存取和**遠端托管儲存庫**的平台服務
- 關係像是本地端有一個 index.html，但可以放到 dropbox、Google Drive 進行雲端託管

## 遠端儲存庫(Repository)操作

- 註冊遠端儲存庫：`git remote add origin 遠端儲存庫網址`
- 更新資料到遠端 master 分支：`git push -u origin master`
- -u 是指他預設會推到哪個遠端數據庫服務
- origin 可以改它的遠端數據庫名稱，例如 **git push -u github master**

## Git 版本細節

- branch ：分支，預設分支叫做 master
- HEAD：指標(正在看的版本)
    
    ```csharp
    git log
    ```
    
- origin：預設遠端儲存庫名稱
- 回頭觀看版本內容：`git checkout 編號`
- 返回最新的版本：`git checkout master(分支名稱)`

![Untitled](Github%20心得/Untitled%203.png)

### 新增檔案時，檔案還沒加追蹤時，清空工作目錄

- 顯示此次清除的檔案：`git clean -n`
- 強制清除檔案：`git clean -f`

**檔案已加入追蹤，清空工作目錄**

- 還原工作目錄上已更改的檔案 ：`git checkout -- <file>`

**檔案加入到索引，退到工作目錄**

- 加入索引的檔案還原到工作目錄：`git reset HEAD`

# 分支(Branch)

## 開分支流程

開發情境：我有一個正式主機 master 分支，有一個開發分支叫做 develop

| 指令 | 功能 | 補充 |
| --- | --- | --- |
| git branch 分支名稱 | 新增分支 |  |
| git branch | 查看全部分支 |  |
| git checkout 分支名稱 | 切換分支 |  |
| git branch -d 分支名稱 | 刪除分支 | -D 是強制刪除 |

## 合併分支 && 快轉機制

| 指令 | 功能 | 補充 |
| --- | --- | --- |
| git merge 分支名稱 | 快轉合併分支 | 不同base的時候用，會不知道何時合併 |
| git merge 分支名稱 --no-ff | 取消快轉合併 | 繼承該分支的資料，保留該分支的節點，同一個base的時候才用的到 |
| git log —oneline -graph | 觀看線圖 |  |
| git reset —hard ORIG_HEAD | 還原合併前狀態 |  |

## checkout 與 reset 差異

- checkout 是移動 HEAD
- reset 是移動 branch

## 還原技巧

- 回頭觀看版本內容：`git checkout 編號`
- 返回最新的版本：`git checkout master(分支名稱)`
- 還原工作目錄上已更改的檔案 ：`git checkout -- <file>`
- 索引檔案>還原到工作目錄：`git reset HEAD`
- 還原前兩個版本：`git reset HEAD^^`
- 還原前兩個版本，所有更新檔案都**放棄**：`git reset HEAD^^ --hard`
- 觀看詳細歷史紀錄：`git reflog`
    - 之後可以再用git reset “代碼” —hard 更變紀錄
    

### 從數據庫抓資料下來到本端

- git clone [直接輸入github的clone連結]

## commit 衝突

兩個 commit 在合併時，檔案裡的某一行有重複修改到時，就會觸發

## 本地衝突

- 1.洧杰跟 Ray 一起在同個 repo 開發，只有一條 master 線
- 2.洧杰先部署了一個 commit 到 master
- 3.Ray 更新了第六行程式碼，並在下班前立馬 push
- 4.洧杰也改了第六行，但他效率比較差，下班後 push 時才發現，Ray 這個ㄐ歪人先 push 了！
- 5.洧杰只好先 pull 下來，結果竟然跟自己的 commit 衝突
- 6.洧杰只好邊罵髒話，邊解決衝突，整理好後再 push

### Merge 和 rebase 都是合併歷史記錄，但是結果不同。

- **Merge**修改內容的歷史記錄會維持原狀，但是合併後的歷史紀錄會變得更複雜。
- **Rebase**修改內容的歷史記錄會接在要合併的分支後面，合併後的歷史記錄會比較清楚簡單，但是，會比使用 merge 更容易發生衝突。