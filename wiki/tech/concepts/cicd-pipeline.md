---
type: concept
domain: tech
tags: [cicd, devops, gitlab, github-actions, argocd, harbor, helm, pipeline]
sources:
  - raw/tech/devops/部署筆記.md
  - raw/tech/devops/Azure Pipeline.md
  - raw/tech/devops/部屬後端.md
created: 2026-05-03
updated: 2026-05-03
---

# CI/CD Pipeline

CI/CD（持續整合 / 持續部署）是現代 DevOps 的核心實踐，將程式碼從提交到部署的流程自動化。

## 工具角色分工

| 工具 | 角色 |
| --- | --- |
| **GitLab / GitHub** | 程式碼版本庫，觸發 CI Pipeline |
| **Azure DevOps** | 可替代 GitLab CI 的 Pipeline 執行引擎 |
| **Docker** | 容器化建置環境，打包 Image |
| **Harbor** | 私有 Container Registry（企業內部） |
| **Helm** | K8s 應用部署打包工具 |
| **ArgoCD** | GitOps CD 控制器，監控 Git 並 sync 到 K8s |

## GitLab CI + ArgoCD 完整流程

```
開發者 push code
    ↓
GitLab CI 觸發 Pipeline
    ├── 1. 自動測試（unit test）
    ├── 2. docker build → docker push 到 Harbor（含 commit SHA tag）
    └── 3. 更新 Helm values.yaml 的 image.tag → git commit → git push

Git Repo 變更
    ↓
ArgoCD 偵測到更新
    ↓
ArgoCD 用 Helm 渲染 YAML → kubectl apply 到 K8s
    ↓
K8s 完成 Rolling Update
```

## GitLab CI 設定（`.gitlab-ci.yml`）

### Pipeline 階段劃分

```yaml
# 測試階段
test:
  stage: test
  script:
    - npm install
    - npm run test

# 建置階段（Docker-in-Docker）
build:
  stage: build
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  variables:
    DOCKER_DRIVER: overlay2
  script:
    - echo "$HARBOR_PASSWORD" | docker login -u "$HARBOR_USERNAME" \
        --password-stdin harbor.example.com
    - docker build -t harbor.example.com/myproj/myapp:${CI_COMMIT_SHA} .
    - docker push harbor.example.com/myproj/myapp:${CI_COMMIT_SHA}

# 部署階段（GitOps：更新設定 repo）
deploy:
  stage: deploy
  image: alpine:3.18
  before_script:
    - apk add --no-cache git yq
  script:
    - git clone git@gitlab.com:myteam/myapp-manifest.git
    - cd myapp-manifest
    - yq -i '.image.tag = "${CI_COMMIT_SHA}"' helm/values-dev.yaml
    - git commit -am "Update image tag to ${CI_COMMIT_SHA} [skip ci]"
    - git push
```

## Azure Pipelines 設定（`azure-pipelines.yml`）

### Pipeline 術語結構

```
Pipeline
└── Stage（build / dev / prod）
    └── Job（一台 agent 上執行的工作單元）
        └── Step（單一指令或 task）
```

### 完整 CI/CD 範例（.NET + Docker）

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
          - task: UseDotNet@2
            inputs:
              version: '9.x'

          - script: dotnet test --no-build --logger trx
            displayName: 'Run tests'

          - task: Docker@2
            displayName: 'Build & Push'
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
        environment: production          # Environments 頁面設定 approval gates
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
                        --name my-api \
                        --resource-group MyRG \
                        --image myregistry.azurecr.io/backend:$(imageTag)
```

### 常用內建變數

| 變數 | 值 |
| --- | --- |
| `Build.BuildId` | 每次 build 的唯一編號 |
| `Build.SourceBranchName` | 分支名稱（main、feature-xxx） |
| `System.DefaultWorkingDirectory` | agent 上的 repo 路徑 |

## Helm Chart 多環境組織

```
myapp/
├── src/...
├── Dockerfile
├── helm/
│   ├── Chart.yaml
│   ├── values.yaml           # 共用預設值
│   ├── values-dev.yaml       # dev 環境覆寫
│   ├── values-stg.yaml
│   └── values-prod.yaml
└── .gitlab-ci.yml
```

## ArgoCD Application 宣告式管理

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: git@gitlab.com:myteam/myapp-manifest.git
    targetRevision: main
    path: helm
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## MyDevWeb CI/CD 架構（GitHub Actions + tag-based）

```
push tag V.X.X.X.X.X
    ↓
GitHub Actions workflow 觸發
    ├── build image
    ├── push to Docker Hub（zxcbig7/mydevweb-frontend:<tag>）
    └── 更新 values-prod.yaml 的 image tag

ArgoCD 偵測 values-prod.yaml 變更 → sync → K8s 更新
```

## 前置作業 Checklist

- [ ] Container Registry 帳號（Harbor / ACR / Docker Hub）
- [ ] K8s Namespace（dev / stg / prod）已建立
- [ ] ImagePullSecret 在各 Namespace 建立
- [ ] CI/CD 敏感變數設為 Protected/Masked
- [ ] ArgoCD 連接 Git repo（SSH 金鑰或 token）
- [ ] Helm Chart 結構清楚（values 覆寫機制設計好）

## 連結

- [[docker]] — 打包 Image
- [[helm]] — K8s 部署打包
- [[argocd]] — GitOps CD 工具
- [[kubernetes]] — 部署目標平台
- [[git]] — 版本控制，CI/CD 觸發來源
