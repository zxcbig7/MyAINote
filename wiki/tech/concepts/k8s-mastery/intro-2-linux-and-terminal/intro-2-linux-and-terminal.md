---
type: concept
domain: tech
tags: [kubernetes, k8s, beginner, linux, terminal, powershell, bash, cli]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 入門第二章：終端機求生

上一章結尾說了，正式伺服器通常沒有螢幕鍵盤。這代表你跟它溝通的唯一方式，是打字。

很多人對終端機的抗拒來自一個誤解：以為要背幾百個指令。其實不是。**日常九成的工作只用得到十幾個指令**，而且它們的邏輯高度一致。這一章的目標是讓你在陌生的機器上不會手足無措——能找到檔案、看得到日誌、改得了設定、知道自己在哪。

## 為什麼非用不可

圖形介面直覺，但有三件事它做不到，而這三件事正好是維運的日常。

**第一，遠端。** 你的服務跑在雲端的某台 Linux 機器上，那台機器沒有桌面。你能連進去的只有一個文字介面。

**第二，可重複。** 「點開設定 → 選第三個分頁 → 勾那個選項」沒辦法寫進文件讓別人準確重做，也沒辦法自動化。但一行指令可以貼進文件、貼進腳本、貼進 CI。

**第三，可組合。** 終端機的指令可以像積木一樣串起來——「找出所有錯誤日誌 → 只留今天的 → 數一數有幾筆」是一行的事。圖形介面沒有這種能力。

## 先搞清楚你在用哪個殼

「終端機」是那個視窗，裡面跑的程式叫 **shell（殼）**。不同的 shell 語法不同，這是初學者最大的困惑來源之一。

在 Windows 上你至少會遇到三種：

| shell | 怎麼開 | 語法特徵 |
| --- | --- | --- |
| **PowerShell** | 開始選單搜尋 PowerShell | 指令長得像 `Get-Process`（動詞-名詞） |
| **cmd** | 搜尋 cmd | 老舊，`dir`、`copy`，能力有限 |
| **Git Bash / WSL** | 裝 Git 或 WSL 後 | Linux 語法，`ls`、`grep` |

本教材的指令**預設用 PowerShell**，因為那是你在自己 Windows 電腦上會用的。但要有心理準備：**當你連進伺服器、或進到容器裡面，那裡幾乎一定是 Linux 的 bash**，語法不一樣。所以下面的表格兩邊都給。

判斷自己在哪：PowerShell 的提示符通常是 `PS C:\Users\you>`，bash 是 `user@host:~$`。看到 `$` 結尾就是 Linux 系。

## 你在哪裡：路徑

終端機永遠有一個「當前所在的資料夾」，所有相對路徑都以它為基準。

```powershell
Get-Location        # 我在哪（Linux: pwd）
Set-Location C:\Projects   # 換位置（Linux: cd /projects）
cd ..               # 上一層（兩邊都通）
cd ~                # 回到家目錄
```

四個符號要認得：

| 符號 | 意思 |
| --- | --- |
| `.` | 現在這個資料夾 |
| `..` | 上一層 |
| `~` | 你的家目錄（Windows 是 `C:\Users\你`，Linux 是 `/home/你`） |
| `/` | Linux 的最頂層（Windows 對應的概念是 `C:\`） |

**絕對路徑**從最頂層寫起（`/etc/nginx/nginx.conf`、`C:\Projects\app`），不管你現在在哪都指同一個地方。**相對路徑**從當前位置算起（`./config/app.yaml`）。寫腳本或設定檔時盡量用絕對路徑——相對路徑會因為「執行時所在的目錄不同」而神秘失敗，這個坑非常常見。

Linux 的幾個重要目錄，看到時知道是什麼就好：

| 路徑 | 放什麼 |
| --- | --- |
| `/etc` | 設定檔 |
| `/var/log` | 日誌 |
| `/usr/bin`、`/usr/local/bin` | 可執行程式 |
| `/home/<user>` | 使用者的個人資料 |
| `/tmp` | 暫存，重開機會清掉 |
| `/opt` | 額外安裝的軟體 |

## 十五個指令走天下

左邊是 Linux（伺服器與容器裡用），右邊是 PowerShell（你自己電腦上用）。

| 做什麼 | Linux | PowerShell |
| --- | --- | --- |
| 列出檔案 | `ls -la` | `Get-ChildItem` (`ls`) |
| 換目錄 | `cd /path` | `cd C:\path` |
| 現在在哪 | `pwd` | `Get-Location` (`pwd`) |
| 看檔案全部 | `cat file` | `Get-Content file` (`cat`) |
| 看檔案開頭／結尾 | `head -20 f` / `tail -20 f` | `Get-Content f -Head 20` / `-Tail 20` |
| **持續追蹤日誌** | `tail -f app.log` | `Get-Content app.log -Wait -Tail 50` |
| 搜尋檔案內容 | `grep "error" file` | `Select-String "error" file` |
| 找檔案 | `find / -name "*.yaml"` | `Get-ChildItem -Recurse -Filter *.yaml` |
| 複製 | `cp a b` | `Copy-Item a b` |
| 移動／改名 | `mv a b` | `Move-Item a b` |
| 刪除 | `rm f` / `rm -rf dir` | `Remove-Item f` / `-Recurse -Force` |
| 建資料夾 | `mkdir -p a/b` | `New-Item -ItemType Directory a\b` |
| 看程序 | `ps aux` | `Get-Process` |
| 殺程序 | `kill <PID>` | `Stop-Process -Id <PID>` |
| 打 HTTP | `curl -s http://x` | `Invoke-RestMethod http://x` (`curl`) |

PowerShell 貼心地幫常見的 Linux 指令做了別名（`ls`、`cat`、`pwd` 都能用），所以剛開始不必兩套都背。但**別名只是名字像，參數完全不同**——`ls -la` 在 PowerShell 會報錯。這是初學者常見的挫折點，知道原因就不會慌。

其中 `tail -f` 特別值得記住，它是「即時看日誌」的標準做法：程式一寫新的日誌，畫面立刻跟著跑。排查問題時你會一直用到它。

## 把指令串起來

終端機真正的威力在這裡。`|`（管線）把左邊指令的輸出，餵給右邊當輸入。

```bash
# Linux：找出日誌裡有 error 的行，只看最後 20 筆
cat app.log | grep error | tail -20

# 數一數今天有幾筆錯誤
grep "2026-08-14" app.log | grep -c ERROR
```

```powershell
# PowerShell：概念一樣，串的是物件不是文字
Get-Process | Where-Object { $_.WorkingSet -gt 100MB } | Sort-Object WorkingSet -Descending | Select-Object -First 5
```

還有兩個符號要認得：`>` 把輸出寫進檔案（**會覆蓋原內容**），`>>` 是附加到結尾。

```bash
kubectl get pods > pods.txt      # 覆蓋
echo "note" >> notes.txt          # 附加
```

`>` 的覆蓋行為是新手意外刪掉檔案的常見原因。養成習慣：**寫進已存在的檔案時先想一秒，需要保留就用 `>>`。**

## Linux 的權限

在容器與伺服器裡工作，權限問題會反覆出現，值得花五分鐘理解。

```
-rw-r--r--  1 root root  1024 Aug 14 10:00 config.yaml
drwxr-xr-x  2 app  app   4096 Aug 14 10:00 data
```

開頭那串十個字元要這樣讀：

- 第 1 個字元：`-` 是檔案，`d` 是資料夾，`l` 是捷徑
- 接下來三個一組，共三組：**擁有者**、**群組**、**其他所有人**
- 每組是 `r`（讀）、`w`（寫）、`x`（執行），沒有的話是 `-`

所以 `-rw-r--r--` 的意思是：擁有者可讀可寫，群組只能讀，其他人只能讀。

數字寫法是把 rwx 當成三個位元：r=4、w=2、x=1，加起來就是那一組的數字。

| 數字 | 權限 | 常見用途 |
| --- | --- | --- |
| `755` | `rwxr-xr-x` | 可執行程式、資料夾 |
| `644` | `rw-r--r--` | 一般設定檔 |
| `600` | `rw-------` | **私鑰、密碼檔**（只有擁有者能讀） |
| `777` | `rwxrwxrwx` | **任何人都能改，正式環境幾乎永遠是錯的** |

```bash
chmod 600 private.key   # 改權限
chown app:app data      # 改擁有者
```

**root** 是 Linux 的最高權限使用者，可以做任何事。`sudo` 的意思是「用 root 的身份執行這一行」。看到 `Permission denied` 時的直覺反應常是加 `sudo`，但更好的習慣是先問「為什麼我需要這個權限」——之後在容器安全那章你會看到，用 root 跑容器是實際的風險來源。

## 環境變數

環境變數是「跟著程序走的設定」。程式啟動時會讀它們，這是傳遞設定（尤其是密碼）的標準方式。

```powershell
$env:MY_VAR = "hello"      # 設定（只在這個視窗有效）
$env:MY_VAR                # 讀取
Get-ChildItem Env:         # 列出全部
```

```bash
export MY_VAR=hello        # Linux 設定
echo $MY_VAR               # 讀取
env                        # 列出全部
```

**環境變數不會自動傳給別人。** 你在自己視窗設的，另一個視窗看不到；你在自己電腦設的，伺服器上沒有。「我明明設了為什麼程式讀不到」十次有九次是這個原因——設在錯的地方，或設完之後程式沒重新啟動。

這個概念直接對應到後面的 K8s：容器的環境變數要寫在 YAML 的 `env` 欄位裡，而且**改了必須重啟容器才會生效**（因為環境變數在程序啟動時就固定了）。

## 編輯檔案：vi 的最小求生包

伺服器和容器裡通常沒有圖形編輯器。如果有 `nano` 就用它（畫面下方會直接寫著操作提示，`Ctrl+O` 存檔、`Ctrl+X` 離開）。但很多精簡的容器裡連 nano 都沒有，只有 `vi`。

vi 讓新手崩潰的原因是它有「模式」——剛打開時你打的字不會被輸入，而是被當成指令。最小求生包只有五個動作：

| 動作 | 按鍵 |
| --- | --- |
| 開始輸入文字 | `i` |
| 停止輸入，回到指令模式 | `Esc` |
| 存檔並離開 | `Esc` 然後 `:wq` 再 Enter |
| **不存檔離開**（改壞了想反悔） | `Esc` 然後 `:q!` 再 Enter |
| 搜尋 | `Esc` 然後 `/關鍵字` 再 Enter |

記住 `:q!` 就好，它是你的逃生門。

## 六個省時間的習慣

1. **Tab 補全**：打一半按 Tab，自動補完檔名或指令。這不只省時間，還能避免打錯字
2. **上下鍵**：翻找剛才打過的指令
3. **`Ctrl+C`**：中止當前指令（跳不出 `tail -f` 的時候按這個）
4. **`Ctrl+L`** 或 `clear`：清畫面
5. **`Ctrl+R`**（bash）：搜尋歷史指令
6. **`指令 --help`**：不確定參數就問它，比 Google 快

## 三個新手最常撞的錯誤

| 錯誤訊息 | 意思 | 怎麼辦 |
| --- | --- | --- |
| `command not found` | 這個指令不存在，或不在搜尋路徑裡 | 確認拼字；確認裝了沒；容器裡常常是**真的沒裝**（精簡映像連 `curl` 都沒有） |
| `Permission denied` | 沒權限 | 看 `ls -l` 的權限；考慮是不是不該用這個身份做這件事 |
| `No such file or directory` | 路徑不對 | `pwd` 確認你在哪，`ls` 確認檔案真的在那 |

第一個特別值得展開：**容器裡沒有你習慣的工具是常態，不是故障**。正式環境的映像會刻意做得很小，可能連 shell 都沒有。之後你會學到用臨時容器（ephemeral container）來除錯，就是為了解決這個問題。

## 本章回顧

- shell 有很多種，語法不同；你電腦上是 PowerShell，伺服器與容器裡幾乎都是 bash
- 終端機永遠有「當前目錄」；絕對路徑比相對路徑安全
- 十五個指令覆蓋日常九成工作，其中 `tail -f` 與 `grep` 是排錯主力
- `|` 串接、`>` 覆蓋、`>>` 附加
- 權限三組 rwx，`600` 給私鑰、`777` 幾乎永遠是錯的
- 環境變數跟著程序走，**改了要重啟才生效**
- `:q!` 是 vi 的逃生門

## 自我檢查

1. 你怎麼知道自己現在在 PowerShell 還是 bash？
2. `tail -f` 跟 `cat` 差在哪？什麼時候用哪個？
3. `chmod 600` 是什麼意思？為什麼私鑰要用它？
4. 為什麼「我設了環境變數但程式讀不到」？
5. 在容器裡打 `curl` 說 command not found，最可能的原因是什麼？

下一章講網路——因為接下來你要讓別人連得到你的服務。

## 連結

- [[intro-1-server-and-process]] — 上一章：伺服器與程序
- [[intro-3-network-basics]] — 下一章：兩台電腦怎麼講話
- [[linux]] — Linux 目錄結構與指令的完整整理
- [[17-cheatsheet]] — 附錄 B：之後會用到的 kubectl 指令速查
- [[k8s-mastery]] — 教材總目錄（含各階段的閱讀路徑）
