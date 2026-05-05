# Azure Pipeline

# 核心概念與 YAML 基礎

**術語關係**

```tsx
Pipeline
└── Stage（部署環境：build / dev / prod）
    └── Job（一台 agent 上跑的工作單元）
        └── Step（單一指令或 task）
```

- **Agent**：執行 pipeline 的機器，分 Microsoft-hosted（微軟管理）和 Self-hosted（自己管）
- **YAML pipeline** vs **Classic pipeline**：現在都推 YAML，版本控制友好

**最小可跑的 YAML：**放在 repo 根目錄，推上 `main` 就會自動觸發。

```yaml
# azure-pipelines.yml
trigger:
  - main
pool:
  vmImage: ubuntu-latest
steps:
  - script: echo "Hello Azure Pipelines"
    displayName: 'Print hello'
```

# 觸發條件與變數管理

```yaml
trigger:
  branches:
    include:
      - main
      - release/*
  paths:
    include:
      - src/backend/**

pr:
  branches:
    include:
      - main

schedules:
  - cron: "0 2 * * *"    # 每天凌晨 2 點
    displayName: Nightly build
    branches:
      include:
        - main
```

### 變數三種層級

| 層級 | 方式 | 用途 |
| --- | --- | --- |
| YAML 內 | `variables:` | 公開的非敏感設定 |
| Variable Group | Library 頁面建立 | 跨 pipeline 共用 |
| Secret | Variable Group 裡勾 lock | API key、密碼 |

```yaml
variables:
  buildConfig: Release
  - group: my-variable-group   # 從 Library 載入

steps:
  - script: echo $(MY_SECRET)   # secret 不會印出真實值
```

## Build、Test 與 Artifact 發布

### 典型 .NET + Docker 的 Build job

```yaml
jobs:
  - job: Build
    pool:
      vmImage: ubuntu-latest
    steps:
      - task: UseDotNet@2
        inputs:
          version: '9.x'

      - script: dotnet build --configuration $(buildConfig)
        displayName: 'dotnet build'

      - script: dotnet test --no-build --logger trx
        displayName: 'dotnet test'

      - task: Docker@2
        displayName: 'Build & Push to ACR'
        inputs:
          containerRegistry: 'my-acr-service-connection'
          repository: 'my-backend'
          command: buildAndPush
          tags: |
            $(Build.BuildId)
            latest

      - task: PublishPipelineArtifact@1
        inputs:
          targetPath: '$(Build.ArtifactStagingDirectory)'
          artifact: 'drop'
```

### 常用內建變數

| 變數 | 值 |
| --- | --- |
| `Build.BuildId` | 每次 build 的唯一編號 |
| `Build.SourceBranchName` | `main` / `feature-xxx` |
| `System.DefaultWorkingDirectory` | agent 上的 repo 路徑 |

---

## 第四章　多 Stage 部署與 Environments

### Stage 分離 CI / CD

```yaml
stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - script: dotnet publish -o $(Build.ArtifactStagingDirectory)
          - task: PublishPipelineArtifact@1
            inputs:
              artifact: 'app'

  - stage: DeployDev
    dependsOn: Build
    jobs:
      - deployment: DeployToContainerApps
        environment: dev                    # 對應 Environments 頁面
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: app
                - task: AzureContainerApps@1
                  inputs:
                    ...
```

### Environments 核心功能

在 Azure DevOps Portal 的 **Environments** 頁面建立 `dev`、`staging`、`prod`，然後可以設定：

- **Approval gates**：部署前需要人工核准
- **Business hours check**：只在上班時間部署
- 每次部署有完整的部署歷史記錄

---

## 第五章　進階技巧

### Templates：共用邏輯

把常用的 steps 抽成獨立檔案，避免重複：

```yaml
# templates/build-steps.yml
parameters:
  - name: buildConfig
    default: Release

steps:
  - script: dotnet build -c ${{ parameters.buildConfig }}
  - script: dotnet test --no-build
```

```yaml
# azure-pipelines.yml
steps:
  - template: templates/build-steps.yml
    parameters:
      buildConfig: Release
```

### Matrix：平行測試多個版本

```yaml
jobs:
  - job: Test
    strategy:
      matrix:
        dotnet8:
          dotnetVersion: '8.x'
        dotnet9:
          dotnetVersion: '9.x'
    steps:
      - task: UseDotNet@2
        inputs:
          version: $(dotnetVersion)
      - script: dotnet test
```

### Conditions：條件執行

```yaml
 script: ./deployprod.sh
 condition: and(succeeded(), eq(variables['Build.SourceBranchName'], 'main'))
```

### OIDC（Workload Identity Federation）

比 Service Principal 密碼更安全，不需要儲存 secret：

```yaml
 task: AzureCLI@2
 inputs: azureSubscription: 'my-oidc-service-connection' scriptType: bash
 scriptLocation: inlineScript
 inlineScript: | az containerapp update --name my-app ...
```

## 第六章　真實專案整合（ACR + Container Apps）

這份是你現有架構的完整 CI/CD 範例：

```yaml
trigger:
  branches:
    include: [main]
  paths:
    include: [src/backend/**]

variables:
  - group: production-secrets
  imageTag: $(Build.BuildId)

stages:
  - stage: CI
    jobs:
      - job: BuildAndPush
        pool:
          vmImage: ubuntu-latest
        steps:
          - task: Docker@2
            inputs:
              containerRegistry: 'acr-service-connection'
              repository: 'mydevwebcontainerregistry/backend'
              command: buildAndPush
              dockerfile: src/backend/Dockerfile
              tags: |
                $(imageTag)
                latest

  - stage: CD
    dependsOn: CI
    jobs:
      - deployment: Deploy
        environment: production
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureCLI@2
                  inputs:
                    azureSubscription: 'azure-service-connection'
                    scriptType: bash
                    inlineScript: |
                      az containerapp update \
                        --name my-personal-website-api \
                        --resource-group MyRG \
                        --image mydevwebcontainerregistry.azurecr.io/backend:$(imageTag)
```