---
tags: [devops, docker, container]
---

> 關聯：[[docker]]

# Docker Compose

Docker Compose 用 `docker-compose.yaml` 定義並管理多容器應用，統一處理 Container、網路、Volume 的生命週期。

---

## YAML 結構

### services（核心）

`services` 代表系統中有哪些邏輯服務，每個 key 同時是：
1. Compose 內部服務識別名稱
2. Docker network 內的 DNS hostname
3. `depends_on`、`proxy_pass`、內部連線使用的名字

```yaml
services:
  frontend:
    # ...
  backend:
    # ...
  nginx:
    # ...
```

#### build — 由本地 Dockerfile 建 Image

```yaml
backend:
  build:
    context: ./MyBackend
    dockerfile: Dockerfile
```

#### image — 直接使用已存在的 Image

```yaml
backend:
  image: myregistry.azurecr.io/myapp:1.0.0
```

#### container_name — 識別名稱

```yaml
backend:
  container_name: myapp-backend
```

- `docker ps`、`docker logs` 時好辨識
- 不影響 DNS，不影響 `depends_on`

#### environment — 執行環境變數

```yaml
backend:
  environment:
    ASPNETCORE_ENVIRONMENT: Production
    ASPNETCORE_URLS: http://0.0.0.0:8080
    DB_CONNECTION: "Host=db;Database=mydb"
```

#### ports vs expose

```yaml
backend:
  ports:
    - "8080:8080"   # 主機:容器，對外開放（主機可連）
  expose:
    - "8080"        # 只在 Docker 內部網路可用，不對外
```

#### volumes — 掛載資料

```yaml
backend:
  volumes:
    - backend-logs:/app/logs          # named volume
    - ./nginx.conf:/etc/nginx/nginx.conf:ro  # bind mount（唯讀）
```

#### depends_on — 啟動順序

```yaml
frontend:
  depends_on:
    - backend
    - db
```

> ⚠️ 只控制 **container 啟動順序**，不保證服務已 ready。需要真正等待服務就緒，要自行加 healthcheck 或 wait-for-it 腳本。

#### networks — 加入網路

```yaml
backend:
  networks:
    - app-net
```

---

### networks

Docker network 是容器之間的虛擬網路層。同一 network 內：
- 容器可以互相通訊
- 可以用 service name 當 hostname（Docker 自動 DNS 解析）

```yaml
networks:
  app-net:
    driver: bridge
```

**範例：** nginx 可以直接用 service name 連到 backend

```nginx
proxy_pass http://backend:8080;
```

不用管 IP，container 重啟也不怕位址變動。

---

### volumes

Volume 是獨立於 container 生命週期的資料空間，container 刪除後資料不消失。

```yaml
volumes:
  backend-logs:
  db-data:
  letsencrypt:
```

---

## 完整範例

```yaml
services:
  backend:
    build:
      context: ./Backend
      dockerfile: Dockerfile
    container_name: myapp-backend
    environment:
      ASPNETCORE_ENVIRONMENT: Production
      ASPNETCORE_URLS: http://0.0.0.0:8080
    ports:
      - "8080:8080"
    volumes:
      - backend-logs:/app/logs
    depends_on:
      - db
    networks:
      - app-net

  db:
    image: postgres:16
    container_name: myapp-db
    environment:
      POSTGRES_DB: mydb
      POSTGRES_PASSWORD: secret
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - app-net

  nginx:
    image: nginx:alpine
    container_name: myapp-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    networks:
      - app-net

networks:
  app-net:
    driver: bridge

volumes:
  backend-logs:
  db-data:
```

---

## 重開策略

三種等級，從快到完整：

### 一、最快速重開（服務卡住，設定未改）

```bash
docker compose restart
```

- Container 還在，只是重啟服務
- 不重 build、不重建 Image

### 二、標準重開（推薦日常使用）

```bash
docker compose down
docker compose up -d
```

- `down`：停止並移除 container
- `up -d`：用**現有 Image** 重新啟動（不重 build，速度快）

### 三、完全重開（有改 Dockerfile / 設定檔 / 程式碼）

```bash
docker compose down
docker compose up --build -d
```

- `--build`：強制重新執行 Dockerfile，不使用 cache
- 適用：Dockerfile 有改、nginx.conf 有改、.NET / 前端 build 有變動

---

## 常用指令

```bash
docker compose up -d              # 背景啟動所有服務
docker compose up --build -d      # 重 build 後啟動
docker compose down               # 停止並移除 container
docker compose down -v            # 同時刪除 volumes
docker compose restart            # 重啟（不重 build）
docker compose ps                 # 查看服務狀態
docker compose logs <service>     # 查看 log
docker compose logs -f <service>  # 即時追蹤 log
docker compose exec <service> sh  # 進入容器
docker compose build              # 只 build 不啟動
```

---

## 重開後確認清單

```bash
# 1. 確認所有服務 Up
docker compose ps

# 2. 確認 nginx proxy 正常
docker compose logs nginx

# 3. 確認 backend 無錯誤
docker compose logs backend
```
