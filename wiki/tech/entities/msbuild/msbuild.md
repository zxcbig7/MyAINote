---
type: entity
domain: tech
tags: [msbuild, csproj, dotnet, build]
sources: []
created: 2026-07-17
updated: 2026-07-17
---

# MSBuild 與 .csproj

## 這篇要回答的問題

大部分人第一次認真打開 `.csproj`，是因為某個檔案「build 之後找不到」、或是想加個引用卻不知道該寫哪一段。`.csproj` 看起來是一坨 XML，但它其實只有兩種積木、五個關鍵字，理解了骨架之後，任何一段陌生的 csproj 都能一眼看懂在做什麼。

這篇從「csproj 到底是什麼」開始，一路講到 build 生命週期的自訂步驟，讓你之後看到別人的專案檔不再只是照抄，而是知道每一行在對建置流程說什麼。

## 一、.csproj 是描述，MSBuild 是引擎

先分清楚兩個東西。`.csproj` 是一份**宣告式的建置描述**：它不是程式，不會「執行」，而是列出「這個專案由哪些檔組成、引用了什麼、編出來要長什麼樣」。真正讀這份描述、把它變成實際動作（呼叫編譯器、複製檔案、產生 dll）的，是 MSBuild —— .NET 的建置引擎。你每次跑 `dotnet build`、`dotnet run`、`dotnet publish`，背後都是 MSBuild 在讀你的 csproj 並執行。

現代的 csproj 是所謂的 **SDK-style**，開頭一行 `<Project Sdk="Microsoft.NET.Sdk">`。這個 SDK 幫你預設了一大堆行為，其中最關鍵的一條是：**它會自動把專案資料夾下的 `.cs` 檔收進來編譯、把其他檔收成附帶項目**。這就是為什麼一個新專案的 csproj 短短十幾行卻能正常編譯 —— 大部分規則 SDK 已經內建，csproj 只寫「跟預設不一樣的地方」。記住這件事，後面很多寫法才會講得通。

## 二、只有兩種積木：PropertyGroup 與 ItemGroup

整份 csproj，拆到最底層，只有兩類容器：

| 積木 | 裝什麼 | 心智模型 |
| --- | --- | --- |
| `PropertyGroup` | 單一鍵值的設定、開關 | 像變數：一個名字對一個值 |
| `ItemGroup` | 檔案、引用的清單 | 像陣列：一個名字對一組項目 |

幾乎所有你會在 csproj 看到的東西，不是設定（PropertyGroup），就是清單（ItemGroup）。先建立這個二分法，剩下的都是它們的變化。

## 三、PropertyGroup：設定與開關

PropertyGroup 裡每個子元素就是一個 property，用 `<名稱>值</名稱>` 表達。它們控制「這個專案怎麼編、編成什麼」。常見的幾類：

| 類別 | Property | 作用 |
| --- | --- | --- |
| 建置目標 | `TargetFramework` / `TargetFrameworks` | 編給哪個 .NET 版本；複數版可一次編多個（`net8.0;net48`） |
| 專案類型 | `OutputType` | `Exe`（可執行）或 `Library`（dll） |
| 語言 | `LangVersion` / `Nullable` / `ImplicitUsings` | C# 版本、可空參考型別開關、隱式 using |
| 輸出 | `AssemblyName` / `RootNamespace` / `OutputPath` | 改 dll 名、預設命名空間、輸出路徑 |
| 警告 | `TreatWarningsAsErrors` / `NoWarn` | 把警告當錯誤中斷 build；靜音特定警告編號 |
| 文件 | `GenerateDocumentationFile` | 把 `///` XML 註解輸出成 XML doc 檔 |
| 發布 | `RuntimeIdentifier` / `SelfContained` / `PublishSingleFile` | 指定平台、內含 runtime、打包成單一執行檔 |

這裡有個常被忽略、但很好用的能力：**property 名字可以自訂**。你寫一個 SDK 不認得的 property，它不會報錯，而是變成一個你可以在別處引用的變數：

```xml
<PropertyGroup>
  <MyToolDir Condition="'$(MyToolDir)' == ''">C:\Tools\Default</MyToolDir>
</PropertyGroup>
```

之後任何地方用 `$(MyToolDir)` 就能取出這個值。這讓你把「會變動的路徑、版本號」集中成一個變數，而不是散落各處。上面那個 `Condition` 的意思是「只有當它還沒被設定時才給預設值」，允許從外部（命令列 `-p:MyToolDir=...`）覆寫 —— 條件的用法第七節細講。

## 四、ItemGroup 與三個動詞：Include / Remove / Update

ItemGroup 裝的是清單，每個項目叫一個 **item**。而操作 item 有三個動詞，這是理解 SDK-style csproj 的關鍵：

| 動詞 | 語意 | 何時用 |
| --- | --- | --- |
| `Include` | 新增項目到清單 | 這個檔／引用原本不在清單裡 |
| `Remove` | 從清單移除 | 排除 SDK 預設收進來的東西 |
| `Update` | 修改既有項目的 metadata | 項目已在清單裡（多半是 SDK 自動收的），只想改它的屬性 |

`Include` 和 `Update` 的差別是最容易踩雷的地方。回到第一節那句話：**SDK 會自動把資料夾下的檔 glob 進清單**。所以當你想對一個「SDK 已經自動收進來」的檔做設定時，如果又用 `Include`，等於把同一個檔加了兩次。

### 問題排查：NETSDK1022

**錯誤訊息**：
```text
NETSDK1022: Duplicate 'None' items were included. The .NET SDK includes
'None' items from your project directory by default...
```

**原因**：SDK-style 專案預設已把某類檔（例如非 `.cs` 的雜項檔，歸類為 `None`）自動 `Include` 進清單。你又寫了一次 `<None Include="...">`，造成同一項目重複。

**解法**：把 `Include` 改成 `Update`。`Update` 不新增項目，只針對「已存在的項目」修改它的 metadata，因此不會重複。

```xml
<ItemGroup>
  <None Update="Data\*.csv" CopyToOutputDirectory="PreserveNewest" />
</ItemGroup>
```

這行的意思是：「那些 SDK 已經幫我收好的 `Data\*.csv`，我不要新增它們，只要幫它們補一個『隨 build 複製到輸出目錄』的屬性。」動詞選 `Update` 而非 `Include`，正是為了繞開 NETSDK1022。

## 五、常用的 item 型別

item 依「型別」分類，型別名決定 MSBuild 怎麼對待它。以下是最常遇到的：

| Item 型別 | 用途 |
| --- | --- |
| `Compile` | 要送進編譯器的原始碼；用 `Remove` 可排除某些 `.cs`（例如產生出來、不該重複編譯的檔） |
| `None` | 不參與編譯的雜項檔；搭配 metadata 決定要不要複製到輸出 |
| `Content` | 與 `None` 類似，但語意上是「應用程式的內容檔」（web 專案常用） |
| `Reference` | 引用一個裸 dll（不透過 NuGet），需搭 `HintPath` 指出 dll 位置 |
| `Analyzer` | 掛載 source generator 或程式碼分析器（build 時執行、可產碼／報警告） |
| `PackageReference` | 引用 NuGet 套件（最常見的相依方式） |
| `ProjectReference` | 引用同 solution 裡的另一個專案 |
| `EmbeddedResource` | 把檔案嵌入 dll 內部，runtime 不需外部檔也能讀到 |
| `Using` | 在專案層級宣告 global using（省去每個檔重複 using） |

`Reference` + `HintPath` 的組合值得單獨記，因為它是「引用非 NuGet 的本地 dll」的標準寫法：

```xml
<Reference Include="SomeLibrary">
  <HintPath>..\libs\SomeLibrary.dll</HintPath>
</Reference>
```

## 六、item metadata 與 CopyToOutputDirectory

每個 item 除了「是哪個檔」之外，還能掛一組 **metadata**（附加屬性）。前一節的 `HintPath` 就是一個 metadata。而日常最常用、也最容易搞混的一個，是 `CopyToOutputDirectory`。

要理解它，得先接受一個 .NET 的基本事實：**程式執行時的工作基準目錄是「輸出目錄」（`bin/<Configuration>/<TargetFramework>/`，也就是執行檔所在處），不是你的原始碼目錄。** 你在原始碼樹裡放的資料檔、設定檔，runtime 預設是看不到的 —— 除非它們被複製到輸出目錄。

這正是 `CopyToOutputDirectory` 的職責。它有三個值：

| 值 | 行為 |
| --- | --- |
| `Never`（預設） | 不複製 |
| `PreserveNewest` | 只有當原始檔比輸出的那份新時才複製（增量、省時） |
| `Always` | 每次 build 都複製一次 |

實務上絕大多數情況用 `PreserveNewest`：改了才搬，沒改就跳過。你熟悉的 `appsettings.json` 之所以在執行時讀得到，就是 SDK 預設幫它設了這個。

### 這個機制的完整資料流

```text
原始碼樹的資料檔（你編輯的地方）
   │  dotnet build / dotnet run
   ▼  MSBuild 依 CopyToOutputDirectory 複製
輸出目錄的資料檔（bin/.../）  ← 程式實際讀取的是這一份
```

心智模型要對：**原始碼樹是你維護資料的家，輸出目錄是 build 產物，程式讀的是產物那一份。** 這跟「`.cs` 寫在原始碼、編譯到 bin」是完全同一套邏輯 —— 你不會把原始碼直接寫進 bin，資料檔也一樣。

### 問題排查：改了資料檔卻沒生效

**現象**：修改了原始碼樹裡的資料檔，程式行為卻沒變。

**原因**（三種常見）：
1. 沒有重新 build，輸出目錄那份還是舊的。
2. 該檔的 `CopyToOutputDirectory` 是預設的 `Never`，根本沒被複製。
3. 你手動改的是**輸出目錄**那份，下次 build 又被原始碼較新版覆蓋掉（`PreserveNewest` 的正常行為）。

**解法**：資料一律改原始碼樹那份，確認該檔有設 `PreserveNewest`，重新 build。永遠不要把輸出目錄當成維護資料的地方 —— 那是可拋棄、且會被 `dotnet clean` 清空、通常也被 git 忽略的產物目錄。

### 問題排查：runtime 找不到資料檔（FileNotFound）

**現象**：程式啟動後讀取資料檔時丟 `FileNotFoundException`。

**原因**：該檔沒有被複製到輸出目錄（沒設 `CopyToOutputDirectory`，或誤設 `Never`），而程式又是以輸出目錄為基準去找它。

**解法**：為該檔補上 `CopyToOutputDirectory="PreserveNewest"`。反過來說，如果你的目的是「讓程式不要再依賴這個複製」，那就不能只是拿掉這行 —— 還得改程式讀檔的基準路徑，否則移除複製只會讓它讀不到檔。

## 七、Condition：條件分支

`Condition` 是 csproj 裡最通用的功能性關鍵字：它幾乎可以掛在**任何元素**上（PropertyGroup、ItemGroup、單一 item、甚至 Target），讓那段內容只在條件成立時生效。這使得同一份 csproj 能依組態（Debug/Release）、環境、平台走不同分支。

```xml
<PropertyGroup Condition="'$(Configuration)' == 'Debug'">
  <DefineConstants>DEBUG;TRACE</DefineConstants>
</PropertyGroup>

<None Update="Data\dev-only.csv"
      Condition="'$(Configuration)' == 'Debug'"
      CopyToOutputDirectory="PreserveNewest" />
```

慣用的寫法是把兩邊都用單引號包起來（`'$(X)' == 'value'`），這樣即使變數是空字串也不會讓語法崩掉。這個小細節能避開一整類「變數未定義時條件解析出錯」的問題。

## 八、Target：build 生命週期的自訂步驟

前面講的都是宣告式的「描述」。但有時你需要 build 過程中**真的執行一個動作** —— 跑一段命令、複製一批檔、動態產生檔案。這就是 `Target` 的領域，也是 csproj 功能性最強的部分。

Target 透過 `BeforeTargets` / `AfterTargets` 掛進 build 的某個階段，裡面用內建的 task 做事：

```xml
<Target Name="StampGitHash" BeforeTargets="Build">
  <Exec Command="git rev-parse --short HEAD" ConsoleToMSBuild="true">
    <Output TaskParameter="ConsoleOutput" PropertyName="GitHash" />
  </Exec>
  <Message Text="Building from commit $(GitHash)" Importance="high" />
</Target>
```

常用的內建 task：

| Task | 作用 |
| --- | --- |
| `Exec` | 執行任意命令列指令 |
| `Copy` / `Delete` / `MakeDir` | 檔案／資料夾操作 |
| `Message` | 在 build log 印訊息 |
| `Error` | 條件不符時主動中斷 build（做前置檢查用） |

要抓一個原則：**能用 metadata 宣告解決的，就不要動用 Target。** 像「把資料檔複製到輸出」這種需求，`CopyToOutputDirectory` 一個 metadata 就夠了，寫成 Target 反而把簡單的事複雜化。Target 的價值在於「宣告式表達不了的動作」—— 跑外部工具、依當下狀態動態產檔這類。

## 九、變數與引用語法：$() @() %()

csproj 裡有三種引用符號，各對應前面講過的一種東西：

| 語法 | 引用對象 | 例子 |
| --- | --- | --- |
| `$(名稱)` | property（單一值） | `$(Configuration)`、`$(OutputPath)`、`$(TargetFramework)` |
| `@(名稱)` | item（整個清單） | `@(Compile)`、`@(None)` |
| `%(名稱)` | item 的 metadata（做批次展開） | `%(CopyToOutputDirectory)` |

MSBuild 內建了大量 property 可直接取用，例如 `$(MSBuildProjectDirectory)`（專案檔所在目錄）、`$(OutDir)`（輸出目錄）、`$(Configuration)`（目前組態）。這些在寫 Target 或 Condition 時非常好用，不必自己重新定義。

## 十、Directory.Build.props：跨專案共用

當多個專案要套同一組設定時，一份份 csproj 複製貼上既囉嗦又容易漂移。MSBuild 的解法是 `Directory.Build.props`：把它放在某個上層資料夾，**該資料夾底下所有專案在 build 時會自動繼承它的內容** —— 不需要任何專案手動引用。

```xml
<!-- 放在解決方案根目錄的 Directory.Build.props -->
<Project>
  <PropertyGroup>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <None Update="Data\*.csv" CopyToOutputDirectory="PreserveNewest" />
  </ItemGroup>
</Project>
```

判斷準則很簡單：**同一段設定在兩個以上專案重複出現，就該考慮抽到 `Directory.Build.props`。** 反過來，若某段設定只有單一專案需要，留在該專案自己的 csproj 反而更清楚。這是「共用」與「就近」之間的權衡。

## 收尾：五個關鍵字的心智模型

整份 csproj 的知識，可以壓縮成五個詞：

- **PropertyGroup** = 設定值
- **ItemGroup** = 檔案清單（動詞 Include / Remove / Update，SDK 已自動 Include 時用 Update）
- **Condition** = 分支
- **Target** = 動作
- **Directory.Build.props** = 跨專案共用

看任何一份陌生的 csproj，先問「這段是設定還是清單」，再看它有沒有掛條件、有沒有自訂動作。骨架抓住了，細節查表即可。

## 連結

- [[dotnet-web-api]] — ASP.NET Core Web API，csproj 是每個 .NET 專案的入口
- [[csharp]] — C# 語言，`LangVersion` / `Nullable` 等 property 直接影響它的行為
