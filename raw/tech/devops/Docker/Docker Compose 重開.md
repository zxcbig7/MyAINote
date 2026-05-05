# Docker Compose 重開

以下是 **docker compose「重開」的三種等級**，從最快到最乾淨，請直接照需求用，不要混用。

---

## 一、最快速重開（設定沒改，只是卡住）

👉 **最常用**

```bash
docker compose restart
```

用途：

- container 還在
- 只是想重啟服務
- **不會重 build、不會重建 image**

---

## 二、標準重開（推薦你現在用）

```bash
docker compose down
docker compose up -d
```

說明：

- `down`：停掉並移除 container
- `up -d`：用「現有 image」重新啟動
- 不會重新 build（速度快）

---

## 三、完全重開（改了 Dockerfile / nginx.conf / 程式碼）

👉 **當你有改任何設定檔，一定要用這個**

```bash
docker compose down
docker compose up --build -d
```

用途：

- Dockerfile 有改
- nginx.conf 有改
- .NET / 前端 build 有變動
- 確保 **image 一定是最新的**

---

## 四、你現在可以照這個 SOP 走（建議）

因為你剛剛：

- 有改前端 API 呼叫
- 很可能要調 nginx proxy

👉 **請直接做這一組：**

```bash
docker compose down
docker compose up --build -d
```

### `--build`

👉 **強制重新 build image**

即使：

- image 已經存在
- Docker 覺得 cache 可以用

也會：

- 重新執行 Dockerfile
- 重新 `dotnet publish`
- 重新 `npm build`
- 重新產生 image

📌 **用在你「有改任何程式碼 / 設定檔」時**

### `d`（detached）

👉 **背景執行**

- terminal 不會卡住
- container 在背景跑
- 你要用 `logs` 看輸出

---

## 五、重開後「一定要檢查」的三件事

### 1️⃣ 看服務狀態

```bash
docker compose ps
```

你應該看到：

- backend：Up
- frontend：Up
- nginx：Up

---

### 2️⃣ 看 nginx log（確認 proxy）

```bash
docker compose logs nginx
```