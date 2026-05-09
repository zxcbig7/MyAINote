# Azure Pipelines 完整教學

> 資料來源：[Microsoft Learn — Azure Pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/?view=azure-devops)

---

# 目錄

1. [什麼是 Azure Pipelines](#什麼是-azure-pipelines)
2. [帳號與專案建立](#帳號與專案建立)
3. [建立第一個 Pipeline](#建立第一個-pipeline)
4. [Pipeline 層級結構](#pipeline-層級結構)
5. [trigger — 觸發條件](#trigger--觸發條件)
6. [pool — 執行環境（Agent）](#pool--執行環境agent)
7. [variables — 變數](#variables--變數)
8. [steps — 步驟](#steps--步驟)
9. [jobs — 工作](#jobs--工作)
10. [stages — 階段](#stages--階段)
11. [templates — 模板](#templates--模板)
12. [本專案實作](#本專案實作)
13. [與 GitHub Actions 對照](#與-github-actions-對照)
14. [常見問題](#常見問題)

---

# 什麼是 Azure Pipelines

Azure Pipelines 是 Azure DevOps 中負責 CI/CD 的服務，自動完成：
- **Continuous Integration（CI）**：每次 push 自動 build + test
- **Continuous Delivery（CD）**：自動部署到目標環境

**支援語言與平台：**
Node.js、Python、Java、PHP、Ruby、C#、C++、Go、.NET、Android、iOS，可在 Linux、macOS、Windows 上執行。

**費用（Cloud 版）：**

| 方案 | 費用 |
|------|------|
| Public repo | 免費，無限分鐘 |
| Private repo | 1 個 parallel job，1800 分鐘/月 |
| 超過後 | $0.008 USD/分鐘 |
| Self-hosted agent | 完全免費 |

> 新帳號的 private repo 預設可能沒有免費額度，需到 [Azure DevOps Parallelism Request](https://aka.ms/azpipelines-parallelism-request) 申請，需等幾個工作天。

---

# 帳號與專案建立

## Step 1：註冊

前往 [dev.azure.com](https://dev.azure.com) → 用 Microsoft 或 GitHub 帳號登入。

## Step 2：建立 Organization

```
Organization name: zxcbig7（自訂）
Region: East Asia（選最近的）
```

## Step 3：建立 Project

```
Project name: MyDevWeb
Visibility: Private
Version control: Git
Work item process: Basic
```

---

# 建立第一個 Pipeline

## Step 1：進入 Pipelines

左側選單 → **Pipelines** → **New pipeline** 或 **Create pipeline**

## Step 2：選擇 Code 來源

```
Where is your code? → GitHub
```

授權 Azure DevOps 存取 GitHub，若出現 GitHub 登入頁面請輸入帳號密碼。

## Step 3：選擇 Repo

選擇你的 repo（如 `zxcbig7/RuleViewerFrontend`）。
若出現安裝 Azure Pipelines App 提示，選 **Approve & install**。

## Step 4：選擇 YAML 設定方式

- **Starter pipeline**：自動產生基本 yaml，從頭建立
- **Existing Azure Pipelines YAML file**：使用 repo 裡已有的 yaml 檔

## Step 5：儲存並執行

右上角 **Save and run** → 確認 commit 訊息 → **Save and run**

yaml 會被 commit 到 repo，Pipeline 立刻開始執行。

## 建議的檔案結構

```
.azure/
├── ci.yml       ← push to main 觸發（只跑 build/test）
└── release.yml  ← push tag 觸發（build image + 部署）
```

> Azure Pipelines yaml 可以放在任何路徑，建立 Pipeline 時指定位置即可。

## 查看執行結果

Pipeline → 點選最新一次 run → 可看到每個 stage / job / step 的詳細 log。

執行中可以點 **Cancel** 取消，完成後可點 **Run new** 重新執行。

---

# Pipeline 層級結構

官方定義的層級（由大到小）：

```
Pipeline
└── Stage（多個環境的大階段，可省略）
    └── Job（分配給同一個 agent 的工作單位，可省略）
        └── Step（具體執行的動作）
            ├── task   ← 使用內建或市集任務
            ├── script ← Shell 指令
            ├── bash
            └── powershell
```

**四種寫法（由簡到完整）：**

```yaml
# 1. 只有 steps（最簡單，單一 job）
steps:
  - script: echo Hello

# 2. 有 jobs（多個平行或依序的工作）
jobs:
  - job: Build
    steps:
      - script: dotnet build

# 3. 有 stages（多個環境，如 dev / stg / prod）
stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - script: dotnet build

# 4. extends（繼承共用模板，進階用法）
extends:
  template: templates/base.yml
  parameters:
    buildSteps: []
```

> 如果只有一個 stage，可以省略 `stages` 直接寫 `jobs`。
> 如果只有一個 job，可以進一步省略 `jobs` 直接寫 `steps`。

---

# trigger — 觸發條件

> 官方文件：[trigger definition](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/trigger?view=azure-pipelines)

## 寫法一：簡單 branch 列表

```yaml
trigger:
- main
- develop
```

## 寫法二：關閉觸發

```yaml
trigger: none
```

## 寫法三：完整語法

```yaml
trigger:
  batch: true          # true = 等上次跑完才開新的，避免同時多個 build
  branches:
    include:
      - main
      - 'feature/*'    # 萬用字元支援
    exclude:
      - 'feature/experimental/*'
  paths:
    include:
      - src/*          # 只有 src/ 有改動才觸發
    exclude:
      - docs/*
      - README.md
  tags:
    include:
      - 'V.*'          # 推 V. 開頭的 tag 才觸發
```

> `batch: true` 適合 commit 頻率高的情境，避免同時跑多個重複的 build。

## PR 觸發

```yaml
pr:
  branches:
    include: [main]
  paths:
    include:
      - src/*
```

## 排程觸發（Cron）

```yaml
schedules:
  - cron: '0 2 * * *'         # 每天 UTC 凌晨 2 點
    displayName: Nightly Build
    branches:
      include:
        - main
    always: true               # 即使沒有新 commit 也跑
```

---

# pool — 執行環境（Agent）

Agent 是實際執行 Pipeline 的機器。

## Microsoft-hosted Agent（雲端，最常用）

Microsoft 提供的乾淨虛擬機，每次執行都是全新環境：

```yaml
pool:
  vmImage: ubuntu-latest     # Ubuntu Linux（最常用、最快）
  # vmImage: windows-latest  # Windows Server
  # vmImage: macos-latest    # macOS
```

**優點：** 不需要維護，永遠是乾淨環境
**缺點：** 私有 repo 有分鐘限制，每次都需要重新安裝依賴

## Self-hosted Agent（自己的機器，免費）

安裝在自己電腦或 VM 上的 agent，完全免費：

```yaml
pool:
  name: MyAgentPool
```

**優點：** 免費無限制、可以保留 cache（npm、dotnet）、可存取內網資源
**缺點：** 需要自己維護機器，不是乾淨環境

## 安裝 Self-hosted Agent

1. Azure DevOps → **Project Settings** → **Agent pools** → **New agent**
2. 選擇 OS，下載 agent 套件
3. 依照指示設定並執行 agent

---

# variables — 變數

> 官方文件：[Define variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)

## 直接定義

```yaml
variables:
  buildConfig: Release
  imageTag: latest
```

## 引用 Variable Group（多條 Pipeline 共用）

```yaml
variables:
  - group: my-variable-group   # 在 Pipelines → Library 建立
  - name: buildConfig
    value: Release
```

## 引用語法

```yaml
- script: dotnet build --configuration $(buildConfig)
```

## Secret 變數

不能寫在 yaml 裡，要在 Pipeline UI 設定：
**Pipeline → Edit → Variables → New variable → 勾選 Keep this value secret**

Secret 在 log 中會顯示 `***`，不會洩漏。

```yaml
- script: echo $(DOCKERHUB_TOKEN)   # log 顯示 ***
```

## 系統內建變數

| 變數 | 說明 | 範例值 |
|------|------|--------|
| `$(Build.BuildId)` | Build 流水號 | `42` |
| `$(Build.SourceBranch)` | 完整 branch/tag | `refs/heads/main` |
| `$(Build.SourceBranchName)` | 簡短名稱 | `main` 或 `V.1.0.0.0.0` |
| `$(Build.SourceVersion)` | Commit SHA | `abc1234...` |
| `$(Build.Repository.Name)` | Repo 名稱 | `RuleViewerFrontend` |
| `$(System.DefaultWorkingDirectory)` | 工作目錄 | `/home/runner/...` |
| `$(Build.ArtifactStagingDirectory)` | 暫存輸出目錄 | `/home/runner/.../a` |
| `$(Agent.OS)` | 作業系統 | `Linux` / `Windows_NT` |

## 跨 stage 傳遞變數

```yaml
stages:
- stage: Build
  jobs:
  - job: BuildJob
    steps:
    - script: echo "##vso[task.setvariable variable=myVar;isOutput=true]hello"
      name: setVar

- stage: Deploy
  variables:
    myVar: $[ stageDependencies.Build.BuildJob.outputs['setVar.myVar'] ]
  jobs:
  - job: DeployJob
    steps:
    - script: echo $(myVar)
```

---

# steps — 步驟

## 各種步驟類型

```yaml
# script：跨平台（Linux/Mac 用 bash，Windows 用 cmd）
- script: dotnet build
  displayName: 'Build'
  workingDirectory: src/
  continueOnError: true    # 失敗後繼續（預設 false）

# bash：明確指定 bash
- bash: |
    TAG=$(Build.SourceBranchName)
    echo "Deploying tag: $TAG"

# powershell：需要 PowerShell 環境
- powershell: |
    Write-Host "Hello from PowerShell"

# checkout：拉取程式碼
- checkout: self    # 預設
- checkout: none    # 不拉取（節省時間）
```

## 常用 Task

### Node.js
```yaml
- task: NodeTool@0
  inputs:
    versionSpec: '20.x'
  displayName: 'Install Node.js'

- script: npm ci
- script: npm run lint
- script: npm run build
- script: npm test
```

### .NET
```yaml
- task: UseDotNet@2
  inputs:
    version: '8.0.x'

- task: DotNetCoreCLI@2
  displayName: 'Build'
  inputs:
    command: build
    arguments: '--configuration Release'

- task: DotNetCoreCLI@2
  displayName: 'Test'
  inputs:
    command: test
    arguments: '--configuration Release --no-build'

- task: DotNetCoreCLI@2
  displayName: 'Publish'
  inputs:
    command: publish
    arguments: '--configuration Release --output $(Build.ArtifactStagingDirectory)'
```

### Docker
```yaml
# 方法一：Docker task（需先在 Project Settings → Service connections 設定）
- task: Docker@2
  displayName: 'Build & Push'
  inputs:
    command: buildAndPush
    repository: zxcbig7/mydevweb-frontend
    tags: $(Build.SourceBranchName)
    containerRegistry: dockerhub-connection

# 方法二：直接 script（較靈活）
- script: |
    echo $(DOCKERHUB_TOKEN) | docker login -u $(DOCKERHUB_USERNAME) --password-stdin
    docker build -t zxcbig7/mydevweb-frontend:$(Build.SourceBranchName) .
    docker push zxcbig7/mydevweb-frontend:$(Build.SourceBranchName)
  displayName: 'Build & Push Docker Image'
```

### Artifact（跨 stage 傳遞 build 輸出）

Artifact 是 build 產生的輸出檔（`dist/`、`.dll`），讓後續 stage 可以直接使用，不需要重新 build。

```yaml
# 上傳
- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: $(Build.ArtifactStagingDirectory)
    artifactName: drop

# 下載（在另一個 stage 或 job）
- task: DownloadBuildArtifacts@0
  inputs:
    artifactName: drop
    downloadPath: $(System.DefaultWorkingDirectory)
```

---

# jobs — 工作

> 官方文件：[jobs.job definition](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-job?view=azure-devops)

## 完整屬性

```yaml
jobs:
  - job: MyJob
    displayName: 'My First Job'          # UI 顯示名稱
    dependsOn: Build                     # 等哪個 job 完成後才跑（可以是 list）
    condition: succeeded()               # 執行條件
    continueOnError: true                # 失敗後繼續（預設 false）
    timeoutInMinutes: 60                 # 逾時（預設 60 分鐘）
    cancelTimeoutInMinutes: 5            # 取消後強制終止的等待時間
    pool:
      vmImage: ubuntu-latest
    variables:
      jobVar: value                      # 這個 job 專用的變數
    workspace:
      clean: outputs                     # 清除上次 build 輸出（outputs / resources / all）
    steps:
      - script: echo Hello
```

## 平行執行

```yaml
jobs:
  - job: BuildFrontend
    steps:
      - script: npm run build

  - job: BuildBackend       # 與 BuildFrontend 同時跑（沒有 dependsOn）
    steps:
      - script: dotnet build
```

## 依序執行

```yaml
jobs:
  - job: Build
    steps:
      - script: dotnet build

  - job: Test
    dependsOn: Build        # 等 Build 完才跑
    steps:
      - script: dotnet test

  - job: Deploy
    dependsOn: Test         # 等 Test 完才跑
    steps:
      - script: echo Deploying
```

---

# stages — 階段

> 官方文件：[Stages in Azure Pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/stages?view=azure-devops)

Stage 是 Pipeline 中的大區塊，用來分隔 build、test、deploy 等不同環境。

## 基本用法

```yaml
stages:
  - stage: Build
    displayName: 'Build Stage'
    jobs:
      - job: BuildJob
        steps:
          - script: dotnet build

  - stage: Test
    displayName: 'Test Stage'
    jobs:
      - job: TestJob
        steps:
          - script: dotnet test

  - stage: Deploy
    displayName: 'Deploy Stage'
    jobs:
      - job: DeployJob
        steps:
          - script: echo Deploying
```

## 依賴關係（dependsOn）

```yaml
# 預設：按順序執行
stages:
  - stage: Build
  - stage: Test        # 等 Build 完
  - stage: Deploy      # 等 Test 完
```

```yaml
# 平行執行（dependsOn: []）
stages:
  - stage: FunctionalTest

  - stage: AcceptanceTest
    dependsOn: []      # 與 FunctionalTest 平行跑
```

```yaml
# Fan-out / Fan-in
stages:
  - stage: Test

  - stage: DeployUS
    dependsOn: Test    # Test 後跑

  - stage: DeployEU
    dependsOn: Test    # 與 DeployUS 平行跑

  - stage: Notify
    dependsOn:         # 等 DeployUS 和 DeployEU 都完成
      - DeployUS
      - DeployEU
```

## 條件執行（condition）

```yaml
stages:
  - stage: A

  # stage B：只在 A 失敗時跑
  - stage: B
    condition: failed()

  # stage C：只在 B 成功時跑
  - stage: C
    dependsOn:
      - A
      - B
    condition: succeeded('B')

  # 自訂條件：只在 main branch 跑
  - stage: Deploy
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
```

## 手動觸發 Stage

```yaml
stages:
  - stage: Development
    jobs:
      - job: Deploy
        steps:
          - script: echo Deploying to Dev

  - stage: Production
    trigger: manual    # 需要手動在 UI 點擊才會執行
    jobs:
      - job: Deploy
        steps:
          - script: echo Deploying to Prod
```

## 防止跳過（isSkippable）

```yaml
- stage: MalwareDetection
  displayName: 'Malware Detection'
  isSkippable: false   # 禁止使用者在 UI 跳過此 stage
  jobs:
    - job: Scan
      steps:
        - script: echo Scanning...
```

## 人工審核（Approval）

Approval 設定在 **Environment** 上，不是寫在 yaml 裡：

1. Azure DevOps → **Pipelines → Environments** → 建立或選擇環境（如 `production`）
2. 右上角 `...` → **Approvals and checks** → **Approvals**
3. 加入審核人員

```yaml
# yaml 裡指定 deployment job 使用 environment
jobs:
  - deployment: Deploy
    environment: production    # 部署前會觸發 production 環境的審核
    strategy:
      runOnce:
        deploy:
          steps:
            - script: echo Deploying
```

---

# templates — 模板

> 官方文件：[YAML templates](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)

Template 讓你把重複的 YAML 抽出來，多個 Pipeline 共用。

**兩種類型：**
- **includes template**：把內容插入 Pipeline（像 `#include`）
- **extends template**：定義 Pipeline 必須遵守的結構（像繼承）

**限制：**
- 最多 100 個 YAML 檔案（直接或間接 include）
- 最多 100 層 template 嵌套
- 記憶體最多 20MB

## Includes Template（插入內容）

```yaml
# templates/npm-steps.yml
steps:
  - script: npm ci
  - script: npm run build
  - script: npm test
```

```yaml
# azure-pipelines.yml
jobs:
  - job: Linux
    pool:
      vmImage: ubuntu-latest
    steps:
      - template: templates/npm-steps.yml   # 插入 template

  - job: Windows
    pool:
      vmImage: windows-latest
    steps:
      - script: echo Before template
      - template: templates/npm-steps.yml   # 同樣的 template
      - script: echo After template
```

## Template 帶參數

```yaml
# templates/build-with-params.yml
parameters:
  - name: vmImage
    type: string
    default: ubuntu-latest
  - name: runTests
    type: boolean
    default: true

jobs:
  - job: Build
    pool:
      vmImage: ${{ parameters.vmImage }}
    steps:
      - script: npm ci
      - script: npm run build
      - ${{ if eq(parameters.runTests, true) }}:
        - script: npm test
```

```yaml
# azure-pipelines.yml
jobs:
  - template: templates/build-with-params.yml
    parameters:
      vmImage: ubuntu-latest
      runTests: true

  - template: templates/build-with-params.yml
    parameters:
      vmImage: windows-latest
      runTests: false
```

## Extends Template（定義結構）

用於強制所有 Pipeline 遵守特定結構（例如必須有安全掃描）：

```yaml
# templates/base.yml
parameters:
  - name: buildSteps
    type: stepList
    default: []

stages:
  - stage: Build
    jobs:
      - job: Build
        steps:
          - script: echo Pre-build security check
          - ${{ each step in parameters.buildSteps }}:
            - ${{ step }}
          - script: echo Post-build signing
```

```yaml
# azure-pipelines.yml
extends:
  template: templates/base.yml
  parameters:
    buildSteps:
      - script: npm run build
      - script: npm test
```

## 跨 Repo 使用 Template

```yaml
# azure-pipelines.yml
resources:
  repositories:
    - repository: templates           # 給 repo 取個別名
      type: github
      name: zxcbig7/pipeline-templates
      ref: refs/tags/v1.0             # 釘住版本（建議）

jobs:
  - template: common.yml@templates   # 用 @別名 引用
    parameters:
      vmImage: ubuntu-latest
```

---

# 本專案實作

## 前端 CI（push to main）

`.azure/ci.yml`（RuleViewerFrontend）：

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: ubuntu-latest

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '20.x'
    displayName: 'Install Node.js'

  - script: npm ci
    displayName: 'Install dependencies'

  - script: npm run lint
    displayName: 'Lint'

  - script: npm run build
    displayName: 'Build'
```

## 前端 Release（push tag V.*）

`.azure/release.yml`（RuleViewerFrontend）：

```yaml
trigger:
  tags:
    include:
      - 'V.*'

pool:
  vmImage: ubuntu-latest

variables:
  IMAGE: zxcbig7/mydevweb-frontend

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '20.x'
    displayName: 'Install Node.js'

  - script: npm ci
    displayName: 'Install dependencies'

  - script: npm run build
    env:
      VITE_API_BASE: $(VITE_API_BASE)
      VITE_AUTH_BASE: $(VITE_AUTH_BASE)
      VITE_GOOGLE_CLIENT_ID: $(VITE_GOOGLE_CLIENT_ID)
      VITE_APP_ENV: PROD
      VITE_SHOW_PRIVATE: 'false'
    displayName: 'Build'

  - script: |
      echo $(DOCKERHUB_TOKEN) | docker login -u $(DOCKERHUB_USERNAME) --password-stdin
      docker build \
        --build-arg VITE_API_BASE=$(VITE_API_BASE) \
        --build-arg VITE_AUTH_BASE=$(VITE_AUTH_BASE) \
        --build-arg VITE_GOOGLE_CLIENT_ID=$(VITE_GOOGLE_CLIENT_ID) \
        --build-arg VITE_APP_ENV=PROD \
        --build-arg VITE_SHOW_PRIVATE=false \
        -t $(IMAGE):$(Build.SourceBranchName) .
      docker push $(IMAGE):$(Build.SourceBranchName)
    displayName: 'Build & Push Docker Image'

  - script: |
      TAG=$(Build.SourceBranchName)
      git clone https://zxcbig7:$(DEPLOY_REPO_TOKEN)@github.com/zxcbig7/Deployment-Apps.git deploy
      cd deploy
      sed -i "/^frontend:/,/^backend:/ s|tag: .*|tag: \"$TAG\"|" web-app/values-prod.yaml
      git config user.email "ci@azure.com"
      git config user.name "Azure Pipelines"
      git commit -am "ci: update frontend image to $TAG"
      git push
    displayName: 'Update Deployment Repo'
```

## 後端 CI（push to main）

`.azure/ci.yml`（RuleViewerBackend）：

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: ubuntu-latest

steps:
  - task: UseDotNet@2
    inputs:
      version: '8.0.x'
    displayName: 'Install .NET'

  - task: DotNetCoreCLI@2
    inputs:
      command: build
      arguments: '--configuration Release'
    displayName: 'Build'

  - task: DotNetCoreCLI@2
    inputs:
      command: test
      arguments: '--configuration Release --no-build'
    displayName: 'Test'
```

## 後端 Release（push tag V.*）

`.azure/release.yml`（RuleViewerBackend）：

```yaml
trigger:
  tags:
    include:
      - 'V.*'

pool:
  vmImage: ubuntu-latest

variables:
  IMAGE: zxcbig7/mydevweb-backend

steps:
  - task: UseDotNet@2
    inputs:
      version: '8.0.x'
    displayName: 'Install .NET'

  - task: DotNetCoreCLI@2
    inputs:
      command: build
      arguments: '--configuration Release'
    displayName: 'Build'

  - task: DotNetCoreCLI@2
    inputs:
      command: test
      arguments: '--configuration Release --no-build'
    displayName: 'Test'

  - script: |
      echo $(DOCKERHUB_TOKEN) | docker login -u $(DOCKERHUB_USERNAME) --password-stdin
      docker build -t $(IMAGE):$(Build.SourceBranchName) .
      docker push $(IMAGE):$(Build.SourceBranchName)
    displayName: 'Build & Push Docker Image'

  - script: |
      TAG=$(Build.SourceBranchName)
      git clone https://zxcbig7:$(DEPLOY_REPO_TOKEN)@github.com/zxcbig7/Deployment-Apps.git deploy
      cd deploy
      sed -i "/^backend:/,$ s|tag: .*|tag: \"$TAG\"|" web-app/values-prod.yaml
      git config user.email "ci@azure.com"
      git config user.name "Azure Pipelines"
      git commit -am "ci: update backend image to $TAG"
      git push
    displayName: 'Update Deployment Repo'
```

---

# 與 GitHub Actions 對照

| | GitHub Actions | Azure Pipelines |
|---|---|---|
| yaml 位置 | `.github/workflows/` | `.azure/`（慣例，可自訂） |
| 觸發 branch | `on: push: branches:` | `trigger: branches:` |
| 觸發 tag | `on: push: tags:` | `trigger: tags:` |
| 排程觸發 | `on: schedule: cron:` | `schedules: cron:` |
| PR 觸發 | `on: pull_request:` | `pr:` |
| 執行環境 | `runs-on: ubuntu-latest` | `pool: vmImage: ubuntu-latest` |
| 步驟指令 | `run:` | `script:` |
| 內建任務 | `uses: actions/xxx` | `task: XxxTask@2` |
| Tag 名稱 | `${{ github.ref_name }}` | `$(Build.SourceBranchName)` |
| Commit SHA | `${{ github.sha }}` | `$(Build.SourceVersion)` |
| Secret 引用 | `${{ secrets.XXX }}` | `$(XXX)` |
| 多階段 | 無原生支援 | `stages:` |
| 條件 | `if:` | `condition:` |
| 等待其他 job | `needs:` | `dependsOn:` |
| 模板 | reusable workflows | `templates:` |
| 人工審核 | Environment protection rules | Environment Approvals |
| 私有 repo 免費額度 | 2000 分鐘/月 | 1800 分鐘/月 |

---

# 常見問題

## Pipeline 沒有被觸發

確認 yaml `trigger` 格式正確，縮排錯誤會導致 trigger 失效。
到 Pipeline → **Edit** → **Triggers** 可以查看目前生效的設定。

## Docker login 失敗

使用 Docker Hub **Access Token**，不是密碼：
Docker Hub → Account Settings → Security → **New Access Token**

## git push 403

`DEPLOY_REPO_TOKEN` 需要 `repo` 完整權限：
GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → **New token**

## Tag 名稱取錯

`$(Build.SourceBranch)` 是完整路徑（`refs/tags/V.1.0.0.0.0`）
`$(Build.SourceBranchName)` 才是簡短名稱（`V.1.0.0.0.0`）

## 私有 repo 跑不了，提示沒有 parallel job

新帳號預設可能沒有免費額度，需申請：[Azure DevOps Parallelism Request](https://aka.ms/azpipelines-parallelism-request)，需等幾個工作天。

## 如何限制只有特定人員能觸發 Release

在 **Environments** 設定 **Approvals**，部署前強制等待審核人員核准。
