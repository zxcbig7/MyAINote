---
tags: [devops, docker, container]
---

> 關聯：[[docker]]

# Docker

Docker 是一個開源容器化平台，將應用程式與相依套件打包成標準化的 Container，可在任何環境一致運行。核心價值：**環境隔離**與**可移植性**——開發者用同一份 Image 建立開發環境，維運人員直接部署。

參考：[Docker 從入門到實踐](https://philipzheng.gitbook.io/docker_practice)

---

## 核心概念

### Image（映像檔）

- 唯讀模板，包含執行應用所需的所有內容。類比 OOP 的 Class。
- **分層儲存**：建構時一層層疊加，每層建構後不再改變。後層的「刪除」只是標記，原始資料仍存在映像中。建構時每層應只含該層所需內容，多餘檔案應在該層結束前清理乾淨。
- 建構完成後可上傳分享，其他人用 `docker pull` 取用。

### Container（容器）

- Image 的執行實例，可被啟動、停止、刪除，彼此相互隔離。
- 類似一個輕量 Linux 環境（root 權限、程式空間、網路空間）。
- 啟動時在 Image 最上層建立一層**可寫層**，Image 本身不變。Container 刪除後可寫層也消失。

### Repository（倉庫）

- 集中存放 Image 的地方，概念類似 Git remote repository。
- Registry（伺服器）上存放多個 Repository，每個 Repository 含多個 tag。
- 公開倉庫：[Docker Hub](https://hub.docker.com/)
- 私有倉庫：Harbor（企業自架）、ACR、ECR 等

---

## 安裝（Linux/Ubuntu）

```bash
# 更新套件列表並安裝依賴
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release

# 安裝 Docker Engine
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 啟動並設定開機自動啟動
sudo systemctl start docker
sudo systemctl enable docker

# 確認安裝正常
sudo systemctl status docker
sudo docker run hello-world
```

---

## Image 常用指令

| 指令 | 說明 |
| --- | --- |
| `docker images [-a]` | 列出本機 Image（`-a` 含中間層，`-q` 只顯示 ID） |
| `docker pull <image>[:tag]` | 從 Registry 下載 |
| `docker push <image>` | 上傳到 Registry |
| `docker build -t <name>:<tag> .` | 從 Dockerfile 建立 Image |
| `docker rmi <image>` | 刪除本機 Image |
| `docker rmi $(docker images -q)` | 刪除所有 Image |
| `docker tag <src> <dst>` | 加標籤（為 push 到私有 Registry 用） |
| `docker save -o out.tar <image>` | 匯出 Image 為檔案（含完整層歷史） |
| `docker load -i out.tar` | 從檔案匯入 Image |

---

## Container 常用指令

```bash
# 新建並啟動（互動模式）
docker run -it ubuntu:22.04 /bin/bash

# 背景執行並對外開放 port
docker run -d -p 8080:8080 --name myapp myimage

# 查看容器
docker ps           # 執行中
docker ps -a        # 全部（含停止）

# 停止 / 啟動 / 重啟 / 刪除
docker stop <name>
docker start <name>
docker restart <name>
docker rm <name>
docker rm -f <name>               # 強制刪除執行中的

# 批次操作
docker stop $(docker ps -a -q)    # 停止所有
docker rm $(docker ps -a -q)      # 刪除所有已停止

# 進入執行中的 Container（推薦方式）
docker exec -it <name> /bin/bash

# 查看 log
docker logs <name>
docker logs -f <name>             # 即時追蹤

# 檢查容器詳細狀態（網路、Volume、環境變數等）
docker inspect <name>
```

### attach vs exec

| | `attach` | `exec` |
| --- | --- | --- |
| 用途 | 附加到主程序的 stdin/stdout | 在容器內另開新程序 |
| 退出不中斷容器 | `ctrl+P` → `ctrl+Q` | `exit` 即可 |
| 推薦場景 | 特殊除錯 | **日常除錯首選** |

> `attach` 的限制：多個視窗同時 attach 時，所有視窗同步顯示，一個阻塞其餘也無法操作。

---

## Container 匯出 / 匯入

```bash
# 匯出快照（不含層歷史，只保留當前狀態）
docker export <container_id> > snapshot.tar

# 從快照匯入為 Image
cat snapshot.tar | docker import - myrepo:v1.0

# 也可透過 URL 匯入
docker import http://example.com/image.tgz myrepo:v1.0
```

> `export/import`（容器快照）vs `save/load`（Image 完整層）：快照較小但無歷史；完整層可回溯。

---

## Volume 資料管理

Container 刪除後，可寫層的資料一同消失。持久化資料需使用 Volume 或 bind mount。

```bash
# Named Volume（推薦，Docker 管理）
docker run -d -v mydata:/app/data myimage

# Bind Mount（掛載主機目錄，開發常用）
docker run -d -v /host/path:/container/path myimage

# 唯讀掛載
docker run -d -v /host/path:/container/path:ro myimage

# Volume 管理
docker volume ls
docker volume inspect mydata
docker volume rm mydata
```

**多容器共享 Volume：**

```bash
# 建立資料容器
docker run -d -v /dbdata --name dbdata postgres

# 其他容器從資料容器掛載
docker run -d --volumes-from dbdata --name db1 postgres
docker run -d --volumes-from dbdata --name db2 postgres
```

**Volume 備份與還原：**

```bash
# 備份
docker run --volumes-from dbdata -v $(pwd):/backup ubuntu \
  tar cvf /backup/backup.tar /dbdata

# 還原
docker run -v /dbdata --name dbdata2 ubuntu /bin/bash
docker run --volumes-from dbdata2 -v $(pwd):/backup busybox \
  tar xvf /backup/backup.tar
```

---

## Dockerfile 指令

Dockerfile 定義如何從基底 Image 建構新 Image，格式為 `INSTRUCTION arguments`，以 `#` 開頭為註解。

```dockerfile
# 基底 Image（必須是第一條指令）
FROM ubuntu:22.04

# 維護者資訊（建議加）
MAINTAINER name <email>

# 執行命令（每條 RUN 新增一層，善用 && 合併減少層數）
RUN apt-get update && apt-get install -y nginx && \
    echo "daemon off;" >> /etc/nginx/nginx.conf

# 環境變數（容器執行時保持，後續 RUN 也可使用）
ENV APP_ENV=production \
    APP_PORT=8080

# 設定工作目錄（後續 RUN/CMD/ENTRYPOINT 相對此路徑）
WORKDIR /app

# 複製本地檔案（只能複製 build context 內的檔案，推薦）
COPY ./publish .

# 複製檔案，支援 URL 下載與自動解壓 .tar.gz
ADD archive.tar.gz /app/assets/

# 宣告對外 port（只是文件用，需 docker run -p 才真正開啟）
EXPOSE 8080

# 掛載點（資料持久化）
VOLUME ["/data"]

# 執行身份
USER appuser

# Container 啟動時執行（不被 docker run 參數覆蓋）
ENTRYPOINT ["dotnet", "MyApp.dll"]

# 預設參數（可被 docker run 後面的命令覆蓋）
CMD ["--environment", "Production"]
```

### 關鍵指令對比

| | `COPY` | `ADD` |
| --- | --- | --- |
| 本地檔案 | ✓ | ✓ |
| URL 下載 | ✗ | ✓ |
| 自動解壓 tar | ✗ | ✓ |
| 推薦 | **優先** | 只在需要解壓或 URL 時用 |

| | `CMD` | `ENTRYPOINT` |
| --- | --- | --- |
| 作用 | 預設執行命令 | 固定主程序 |
| 可被 `docker run` 覆蓋 | ✓ | ✗ |
| 常見用法 | 提供預設參數給 ENTRYPOINT | 固定應用入口 |

**ONBUILD**（進階）：當此 Image 被用作其他 Dockerfile 的 FROM 基底時，才觸發執行。

```dockerfile
ONBUILD COPY . /app/src
ONBUILD RUN npm install
```

**建立 Image：**

```bash
docker build -t myapp:1.0.0 .
docker build -t myapp:1.0.0 -f ./docker/Dockerfile .

# .dockerignore 排除不需要複製的檔案
echo "node_modules\n.git\n*.log" > .dockerignore
```

---

## Repository / Registry 操作

```bash
docker login                                   # 登入 Docker Hub
docker login myregistry.azurecr.io            # 登入私有 Registry
docker logout

docker tag myapp:1.0.0 myuser/myapp:1.0.0     # 標記準備 push
docker push myuser/myapp:1.0.0                # 上傳
docker pull myuser/myapp:1.0.0                # 下載

docker commit <container> myimage:tag         # 從容器建立 Image
```
