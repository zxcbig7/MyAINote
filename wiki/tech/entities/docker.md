---
type: entity
domain: tech
tags: [docker, container, devops, image]
sources:
  - raw/tech/devops/Docker 觀念.md
  - raw/tech/devops/Docker.md
  - raw/tech/devops/Docker Compose yaml 架構.md
  - raw/tech/devops/Docker 部屬範例.md
created: 2026-05-03
updated: 2026-05-03
---

# Docker

Docker 是一個開源容器化平台，將應用程式與相依套件打包成標準化的 Container，可在任何環境一致運行。核心優勢是環境隔離與可移植性：開發者用同一份 Image 建立開發環境，維運人員直接用該 Container 部署。

## 三大核心概念

### Image（映像檔）
- **唯讀模板**，包含運行應用程式所需的所有內容。類比 OOP 的 Class。
- **分層儲存**：建構時一層層疊加，前一層是後一層的基礎。每層建構後不再改變，後層的「刪除」只是標記，檔案仍存在映像中。
- 常用指令：

| 指令 | 說明 |
| --- | --- |
| `docker images` | 列出本機 Image（`-q` 只顯示 ID） |
| `docker pull <image>` | 從 Registry 下載 Image |
| `docker build -t <name> .` | 從 Dockerfile 建立 Image |
| `docker push <image>` | 上傳 Image 到 Registry |
| `docker rmi <image>` | 刪除本機 Image |
| `docker tag <src> <dst>` | 替 Image 加標籤 |
| `docker save / load` | 匯出 / 匯入 Image 檔案 |

### Container（容器）
- Image 的**執行實例**。可被啟動、停止、刪除，彼此相互隔離。
- 可視為一個輕量 Linux 環境，Container 啟動時在最上層建立一層**可寫層**。

| 指令 | 說明 |
| --- | --- |
| `docker run <image>` | 建立並啟動 Container |
| `docker run -d -p 8080:8080 --name <name> <image>` | 背景執行並對外開放 port |
| `docker ps` | 列出執行中 Container（`-a` 含停止的） |
| `docker stop <name>` | 停止 Container |
| `docker rm <name>` | 刪除 Container |
| `docker logs <name>` | 查看 Container log |
| `docker exec -it <name> /bin/bash` | 進入 Container shell |

### Repository（倉庫）
- 集中存放 Image 的地方。最大公開倉庫為 [Docker Hub](https://hub.docker.com/)。
- 概念類似 Git 的 remote repository。公司或個人可自建私有倉庫（如 Harbor）。
- `docker login` → `docker push` → 另一台機器 `docker pull`。

## Dockerfile 基本結構

```dockerfile
# 以官方 runtime 映像為基礎
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app

# 複製已發佈的應用程式
COPY . .

# 容器啟動指令
ENTRYPOINT ["dotnet", "MyApp.dll"]
```

## Docker Compose

用 `docker-compose.yaml` 定義多服務應用，統一管理 Container、網路、Volume。

### 核心區塊

**services**：每個 key 定義一個服務，同時是 Docker 內部 DNS hostname。

```yaml
services:
  backend:
    build:
      context: ./Backend
      dockerfile: Dockerfile
    container_name: my-backend
    environment:
      ASPNETCORE_ENVIRONMENT: Production
    ports:
      - "8080:8080"   # 對外開放
    expose:
      - "8080"        # 只在 Docker 網路內可用
    depends_on:
      - db
    volumes:
      - backend-logs:/app/logs
    networks:
      - app-net
```

**networks**：容器間的虛擬網路層。同一 network 內可用 service name 當 hostname（Docker 自動 DNS 解析）。

```yaml
networks:
  app-net:
    driver: bridge
```

**volumes**：獨立於 Container 生命週期的持久化儲存，Container 刪除後資料不消失。

```yaml
volumes:
  backend-logs:
```

- `ports`：對外（主機可連）；`expose`：只在 Docker 網路內可用
- `depends_on`：控制啟動順序，**不保證服務 ready**

## 完整部署流程（ACR 為例）

```bash
# 1. Build Image
docker build -t myapp:1.0.0 .

# 2. Tag（準備推到 ACR）
docker tag myapp:1.0.0 myregistry.azurecr.io/myapp:1.0.0

# 3. Login & Push
az acr login --name myregistry
docker push myregistry.azurecr.io/myapp:1.0.0
```

## 連結

- [[kubernetes]] — Docker Container 的編排管理平台
- [[minikube]] — 本機 K8s 開發環境
- [[helm]] — K8s 應用部署打包工具
- [[cicd-pipeline]] — CI/CD 流程中 Docker 的角色
