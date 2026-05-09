# C# 偵錯與測試

## dotnet test 常用指令

```powershell
# 跑全部測試
dotnet test

# 詳細輸出（看每個 test 的 pass/fail）
dotnet test --logger "console;verbosity=detailed"

# 只跑特定 method
dotnet test --filter "FullyQualifiedName~MethodName"

# 只跑特定 class
dotnet test --filter "ClassName=UserServiceTests"

# 只跑特定 category（需在 test 加 [Trait("Category", "Unit")]）
dotnet test --filter "Category=Unit"

# 輸出結果到 TRX 報告（可用 VS 開啟）
dotnet test --logger trx

# Watch mode：存檔即自動重跑
dotnet watch test

# Watch mode + filter
dotnet watch test -- --filter "ClassName=UserServiceTests"
```

---

## --filter 語法

| 語法 | 說明 |
|------|------|
| `FullyQualifiedName~Keyword` | 名稱包含關鍵字（模糊） |
| `FullyQualifiedName=Namespace.Class.Method` | 完整名稱完全符合 |
| `ClassName=MyTests` | 指定 class |
| `Category=Unit` | 指定 Trait category |
| `A&B` | 同時符合 A 和 B |
| `A\|B` | 符合 A 或 B |

---

## VSCode launch.json：偵錯 ASP.NET Core

存放位置：`.vscode/launch.json`（專案根目錄下）

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch (Debug)",
      "type": "coreclr",
      "request": "launch",
      "preLaunchTask": "build",
      "program": "${workspaceFolder}/bin/Debug/net8.0/ProjectName.dll",
      "args": [],
      "cwd": "${workspaceFolder}",
      "env": {
        "ASPNETCORE_ENVIRONMENT": "Development"
      },
      "stopAtEntry": false,
      "console": "internalConsole"
    }
  ]
}
```

- `preLaunchTask: "build"` 需要搭配 `tasks.json`，按 F5 會先自動 build
- `program` 的路徑要符合 `.csproj` 的 target framework（net8.0、net9.0 等）
- `console` 可選 `"internalConsole"`（輸出在 Debug Console）或 `"integratedTerminal"`

---

## VSCode tasks.json：定義 build task

存放位置：`.vscode/tasks.json`

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "build",
      "command": "dotnet",
      "type": "process",
      "args": [
        "build",
        "${workspaceFolder}/ProjectName.csproj",
        "/property:GenerateFullPaths=true",
        "/consoleloggerparameters:NoSummary"
      ],
      "problemMatcher": "$msCompile"
    }
  ]
}
```

---

## VSCode launch.json：偵錯 xUnit / NUnit 測試

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Tests",
      "type": "coreclr",
      "request": "launch",
      "preLaunchTask": "build",
      "program": "dotnet",
      "args": [
        "test",
        "${workspaceFolder}/ProjectName.Tests.csproj",
        "--filter",
        "FullyQualifiedName~TargetTestName"
      ],
      "cwd": "${workspaceFolder}",
      "console": "internalConsole",
      "stopAtEntry": false
    }
  ]
}
```

> 通常不需要手寫 test 的 launch.json。裝 **C# Dev Kit** extension 後，Test Explorer 會自動出現，可直接在 UI 點按偵錯個別測試。

---

## 設定斷點與偵錯流程

1. 在程式碼左側點一下設定斷點（紅點）
2. 按 `F5` 啟動（會先 build）
3. 執行到斷點時自動暫停
4. 偵錯工具列操作：

| 快捷鍵 | 動作 |
|--------|------|
| `F5` | 繼續執行 |
| `F10` | 逐行（不進入函式） |
| `F11` | 進入函式 |
| `Shift+F11` | 跳出函式 |
| `F9` | 切換斷點 |

---

## 注意事項

- `launch.json` 的 `program` 路徑若填錯，按 F5 會出現「program does not exist」—— 先確認 `bin/Debug/net8.0/` 下有沒有 `.dll`
- Watch mode 不支援設定斷點，要偵錯單一測試請用 Test Explorer 的 Debug 按鈕
- `ASPNETCORE_ENVIRONMENT` 若不設，預設為 `Production`，會讀錯 config
