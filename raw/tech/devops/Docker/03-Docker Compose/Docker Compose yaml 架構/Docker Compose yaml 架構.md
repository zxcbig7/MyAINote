---
tags: [devops, docker, container]
---

> 關聯：[[docker]]

# Docker Compose.yaml 架構

# version（可選）

# **services（核心）**

- `services` 代表系統中「有哪些邏輯服務」。
- `services` 下每一項目定義一個或多個 container

```yaml
services:
  frontend:
  backend:
  nginx:
  certbot: 
```

這個 `backend` 同時是：

1. Compose 內部的服務識別名稱
2. Docker network 內部的 DNS hostname
3. `depends_on`、`proxy_pass`、內部連線使用的名字

## build：由本地 Dockerfile 建 image

```yaml
backend:
	build:
		context: ./RuleViewerBackend
		dockerfile: Dockerfile
```

## image：直接使用已存在 image

```yaml
backend:
	image: my-backend:1.0.0
```

## container_name（識別container用）

```yaml
backend:
	container_name: ruleviewer-backend
```

- `docker ps`、`docker logs` 時好辨識
- 不影響 DNS、不影響 depends_on

## environment（執行環境變數）

```yaml
backend:
	environment:
	  ASPNETCORE_ENVIRONMENT: Production
	  ASPNETCORE_URLS: http://0.0.0.0:8080
```

- 告訴程式現在跑在什麼環境
- 控制 runtime 行為（log、port、feature flag）

## ports vs expose（對外或僅內部）

```yaml
backend:
	ports:
	  - "8080:8080"
	expose:
		- "8080"
```

- ports：對外開放（主機可以連）
- expose：只在 Docker 內部網路可用

```yaml
backend:
	volumes:
		- backend-logs:/app/logs
```

- container 重建後資料不消失

```yaml
backend:
	depends_on:
		- backend
```

- 控制 container 啟動順序
- **不保證服務 ready**

只管 container，不管服務狀態。

# networks（加入哪些網路）

Docker network 是：**容器之間的虛擬網路層**

在同一個 network 裡：

- 容器可以互相通訊
- 可以用 service name 當 hostname
- Docker 會自動做 DNS 解析

```yaml
networks:
  - ruleviewer-net
```

- 決定 service 能跟誰通
- 是否能用 service name 當 hostname

```yaml
networks:
  ruleviewer-net:
    driver: bridge
```

### Docker Compose 的 DNS 行為

在同一個 network 裡：

```
backend  →  某個 container IP
frontend →  某個 container IP
```

所以 nginx 可以：

```
proxy_pass http://backend:8080;
```

不用管 IP，也不怕 container 重啟。

# volumes（資料持久化）

- Volume ：**獨立於 container 生命週期之外的資料空間**
- container 可以刪，volume 不會消失。
- database、SSL 憑證 、使用者上傳檔案

```yaml
volumes:
  backend-logs:
  nginx-logs:
  letsencrypt: 
```

# configs / secrets（進階，用得少）

```bash

```