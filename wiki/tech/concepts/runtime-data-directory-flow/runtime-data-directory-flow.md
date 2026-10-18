---
type: concept
domain: tech
tags: [dotnet, msbuild, build-output, data-flow, csv, optimfoundation]
sources: []
created: 2026-08-07
updated: 2026-08-07
---

## 從一個困惑開始

打開一個 .NET 專案，你會在兩個地方看到同名的資料資料夾：一個在原始碼樹裡（`ProjectRoot/Data/`），一個在建置輸出目錄裡（`ProjectRoot/bin/Debug/<tfm>/Data/`）。它們裝的檔案同名同數量，看起來是同一份東西的兩個副本。

但真的去比對內容，往往會發現它們**不一樣** —— 檔案大小差幾個 byte、欄位名稱一個是 `Digit` 一個是 `DIGIT`、時間戳一個比另一個新。這時候第一個冒出來的問題是：哪一份才是真的？我該改哪一份？

多數教學只會回答一半。標準答案是「原始碼樹是家，輸出目錄是產物，build 時複製過去」，這在 [[msbuild]] 的 `CopyToOutputDirectory` 一節已經講完了。但那個答案只描述了**單向**的資料流。真正讓人困惑的情況，是資料還會**倒著流回來** —— 程式自己在執行時把檔案寫進輸出目錄。這一篇處理的就是這後半段。

## 兩條資料流

先把完整圖景畫出來。一個會讀寫檔案的應用程式，資料其實在兩條路上跑：

```text
                    ┌─────────────────────────┐
   你編輯 ────────► │  原始碼樹  ProjectRoot/Data/  │  ← 版控追蹤的那份
                    └────────────┬────────────┘
                                 │  ① build 時複製（MSBuild）
                                 ▼
                    ┌─────────────────────────┐
                    │  輸出目錄  bin/.../Data/  │  ← 程式實際讀寫的那份
                    └────────────┬────────────┘
                                 │  ② 程式執行時寫檔
                                 └──► 覆蓋輸出目錄的檔案（回不到原始碼樹）
```

**流向 ①（build → 產物）** 是大家熟悉的那條，由 MSBuild 的 `CopyToOutputDirectory` metadata 控制。

**流向 ②（程式 → 產物）** 才是分岔的來源。任何具備「前處理」「匯入」「資料轉檔」模式的程式都會有這條流：讀一份原始格式的檔，展開成程式自己的標準格式，再寫回檔案系統。問題是它寫出去的位置**必然落在輸出目錄**，而不是原始碼樹。

## 為什麼程式一定寫在輸出目錄

因為程式在執行時根本不知道原始碼樹在哪裡。

.NET 應用取得自身位置的標準方式是 `AppDomain.CurrentDomain.BaseDirectory`（或 `AppContext.BaseDirectory`），它回傳的是**執行檔所在目錄**。凡是把資料夾路徑掛在這個基準底下的設計，路徑就永遠指向 `bin/Debug/<tfm>/`：

```csharp
public static string ProjectPath => AppDomain.CurrentDomain.BaseDirectory;

public string GetPath() => Path.Combine(ProjectPath, _folderName);
```

這是正確的設計，不是 bug。程式發佈之後根本沒有原始碼樹可言 —— `dotnet publish` 出來的資料夾裡只有執行檔和它的資料檔。硬要把路徑指回 `../../../Data` 這種相對原始碼樹的位置，開發時或許能跑，一發佈就立刻壞掉。

**要記住的原則**：程式的世界觀裡只有輸出目錄。原始碼樹是給人和版控用的，執行期不存在。

反過來說，這也意味著程式**沒有任何辦法**自動把寫出去的檔案送回原始碼樹。那是人的責任。

## 兩條流相撞：分岔是怎麼形成的

現在把兩條流放進同一個專案，衝突就出現了。假設專案這樣宣告資料檔：

```xml
<ItemGroup>
  <None Update="Data\**\*.csv" CopyToOutputDirectory="PreserveNewest" />
</ItemGroup>
```

`PreserveNewest` 的仲裁規則只有一句話：**原始檔比輸出檔新才複製，否則跳過**。判斷依據是檔案的最後寫入時間。

於是這個序列會發生：

```text
10:00  你編輯原始碼樹的 Data/*.csv
10:05  dotnet build       → 原始檔較新，複製到 bin（兩份一致）
10:10  程式以匯入模式執行  → 覆寫 bin 的 Data/*.csv（兩份開始不同，bin 較新）
10:20  dotnet build       → 原始檔較舊，跳過複製（分岔保留下來）
10:30  dotnet build       → 一樣跳過
   ⋮   往後每次 build 都跳過，分岔永久存在
```

第 10:20 那一步是關鍵。多數人以為 build 會「同步」兩份，但 `PreserveNewest` 從來沒有同步的語意，它只做單向的「較新覆蓋較舊」。程式寫出來的檔天生就是最新的，所以**只要程式回寫過一次，原始碼樹那份就再也推不過去**，除非你重新編輯它、讓時間戳翻新。

這個行為經常被誤讀成 bug，其實它是刻意的：如果 build 每次都硬蓋，程式辛苦產生的資料每次 build 都會被抹掉，匯入流程就沒有意義了。`PreserveNewest` 等於是預設站在「保留執行期產物」那一邊。

## 分岔了要怎麼看出來

問題在於分岔很安靜。讀取端如果寫得夠寬容（例如 CSV 按欄名對位、大小寫不敏感、忽略多餘欄位），兩份內容不同也照樣跑得起來，不會有任何錯誤訊息。你可能幾個月都不知道自己讀的是哪一份。

好消息是，程式寫出來的檔通常帶有可辨識的**指紋**，因為框架的寫檔設定跟人手動編輯的習慣不同。常見的三個線索：

| 指紋 | 人手編輯 / 版控的檔 | 程式寫出來的檔 |
| --- | --- | --- |
| BOM | 通常無 BOM | 常有 UTF-8 BOM（`EF BB BF`），為了 Excel 相容而刻意加 |
| 換行 | 依 editor 與 git 設定，常見 LF | `StreamWriter.WriteLine` 在 Windows 產生 CRLF |
| 欄名大小寫 | 保持宣告時的原樣（`Digit`） | 常被正規化（`DIGIT`），與資料庫欄位慣例對齊 |

用十六進位直接看檔頭是最快的判別法：

```powershell
Format-Hex -Path .\Data\Set_Row.csv -Count 16
Format-Hex -Path .\bin\Debug\net8.0\Data\Set_Row.csv -Count 16
```

開頭有 `EF BB BF`、行尾是 `0D 0A`、表頭全大寫 —— 三個特徵同時出現，幾乎可以確定這份是程式寫的，不是複製過去的（MSBuild 的複製是 byte-for-byte，不會動編碼、換行或內容）。

要比對兩份是否真的相同，用雜湊最乾脆：

```powershell
Get-FileHash .\Data\*.csv, .\bin\Debug\net8.0\Data\*.csv | Format-Table Hash, Path
```

## 誰是 source？問版控就好

檔案內容可以偽裝，版控不會。判斷哪一份是原始碼樹的唯一權威作法是問 git：

```powershell
git ls-files "path/to/Data"                          # 有輸出 = 被追蹤 = source
git check-ignore -v "path/to/bin/.../Data/file.csv"  # 有輸出 = 被 ignore = 產物
```

被 `.gitignore` 擋掉的那份，定義上就是可拋棄的產物。這帶出一條實用的判準：

> **產物目錄必須是可隨時刪除的。** 如果刪掉 `bin/` 會讓你損失資料，那份資料就放錯地方了。

這條判準能直接回答「我可不可以 `dotnet clean`」這種問題 —— 在有反向資料流的專案裡，答案是「先確認回寫的資料已經回收到原始碼樹，否則不行」。

## 三種複製策略的取捨

理解了反向流之後，`CopyToOutputDirectory` 的三個值就不只是「要不要複製」的差別，而是「誰有最終話語權」的政策選擇：

| 值 | 話語權 | 適合的場景 |
| --- | --- | --- |
| `Never` | 程式獨佔 | 資料完全由執行期產生，原始碼樹不放種子資料 |
| `PreserveNewest` | 時間戳決定 | 有匯入 / 前處理流程，要保留執行期產物 |
| `Always` | 原始碼樹獨佔 | 資料是唯讀輸入，程式從不回寫 |

選擇的判準是一句話：**程式會不會寫這個資料夾？** 會寫就不能用 `Always`（每次 build 抹掉產物），不寫就該用 `Always`（省掉時間戳造成的一切困惑）。

`PreserveNewest` 是有反向流時的正確選擇，但它的代價就是前面說的分岔，而且這個代價**無法用設定消除**，只能用流程管理。

## 標準作法

把上面的機制收斂成三條可以直接照做的規則：

**一、要改輸入資料，改原始碼樹那份，然後重新 build。** 直接改輸出目錄那份不是不行，但它隨時可能被下一次 build 覆蓋（只要你之後又動了原始碼樹那份），而且改動不進版控。

**二、程式產生的資料要保留，就手動回收到原始碼樹。** 這一步沒有自動化的餘地，因為程式不知道原始碼樹在哪。回收之後那份的時間戳會變新，下次 build 反而會正確地把它推到輸出目錄，兩份重新一致：

```powershell
Copy-Item .\bin\Debug\net8.0\Data\*.csv .\Data\ -Force
```

**三、把回收動作綁進流程，不要靠記性。** 常見作法是在匯入指令的說明文件裡把「複製回原始碼樹」寫成第二步，或者在專案裡加一個 MSBuild Target 做這件事。若團隊經常忘記，另一個方向是讓程式的匯入模式接受輸出路徑參數，執行時直接指向原始碼樹 —— 但要注意這等於讓程式知道了它不該知道的位置，只適合開發用的工具模式。

## 問題排查

**現象**：修改原始碼樹的資料檔，重新 build，程式行為卻沒變。

**原因**：輸出目錄那份的時間戳比原始檔新（通常是程式先前回寫過），`PreserveNewest` 判定不需複製，靜默跳過。

**解法**：確認兩份的差異與時間戳，再決定要保留哪一份。要強制推送原始碼樹那份，最直接是刪掉輸出目錄的檔再 build，或用 `touch` 語意翻新原始檔時間戳：

```powershell
(Get-Item .\Data\Parameter_X.csv).LastWriteTime = Get-Date
```

---

**現象**：`dotnet clean` 或刪除 `bin/` 之後，程式讀不到資料或讀到過期的資料。

**原因**：匯入流程產生的資料只存在輸出目錄，從未回收到原始碼樹，隨產物一起被刪除。

**解法**：重新跑一次匯入流程重建資料；長期解法是把回收步驟納入流程（見標準作法第二、三條）。

---

**現象**：兩份資料的欄位名稱大小寫不同，程式卻沒報錯。

**原因**：讀取端按欄名對位且大小寫不敏感，這是刻意的容錯設計，讓框架自己輸出的檔可以直接被讀回（round-trip）。容錯的副作用就是分岔不會被偵測到。

**解法**：不要依賴程式報錯來發現分岔，用前面的雜湊比對或指紋檢查主動確認。

## 實作對照

以 OptimFoundation（CPLEX/Gurobi 的 .NET 建模框架）為例，上述機制對應到的具體元件如下，可作為在其他框架裡辨認同類設計的參照：

| 機制 | 實作位置 | 行為 |
| --- | --- | --- |
| 路徑基準 | `FolderDir.ProjFolder.ProjectPath` | `AppDomain.CurrentDomain.BaseDirectory`，所有資料夾掛在執行檔旁 |
| 資料夾配置 | `FolderDir` 的靜態屬性 | `Data/` 是唯一的讀取資料夾；`Solution/`、`Logs/`、`Models/` 等是輸出，不與輸入混放 |
| 讀取端 | `CsvDataSource` → `CsvCtrl.BuildParameter` | 表頭按 property 名對位、大小寫不敏感、多餘欄忽略 |
| 寫入端 | `CsvCtrl.WriteSet` / `WriteParam` | UTF-8 with BOM、欄名 `ToUpperInvariant()` —— 產物指紋的來源 |
| 反向流入口 | 匯入模式的建構子 + `Export()` | 讀 `Data/raw/` 的原始矩陣，展開後寫回 `Data/` 的標準格式 |

值得學的設計取捨有兩點。其一是**輸入與輸出資料夾分離**：解答寫進 `Solution/`、模型檔寫進 `Models/`，只有匯入流程會碰 `Data/`，所以反向流的影響面被限制在一個資料夾內。其二是**讀寫格式對稱**：寫出去的檔一定讀得回來，這讓匯入產物可以直接當成下一次執行的輸入，反向流才成立。

## 連結

- [[msbuild]] — `CopyToOutputDirectory` 的三個值、`Include` vs `Update`、item metadata 基礎
- [[csharp]] — `AppDomain` / `Path.Combine` / `StreamWriter` 編碼設定
- [[git]] — `.gitignore` 與 `git ls-files` / `git check-ignore` 判斷追蹤狀態
