---
type: concept
domain: tech
tags: [kubernetes, k8s, docker, dotnet, react, dockerfile, beginner, hands-on]
sources: []
created: 2026-08-15
updated: 2026-08-15
---

# 實戰第一章：把你自己的應用容器化

入門篇跑的都是官方的 nginx 映像——按下指令就能跑，因為別人已經幫你打包好了。但你真正要部署的是自己寫的東西：一個 ASP.NET Core Web API、一個 React 前端。這一章把它們變成映像。

這裡有個順序問題值得先講：**很多人以為容器化就是寫個 Dockerfile，其實不是。** 應用程式本身如果沒有為「跑在容器裡」做好準備，Dockerfile 寫得再漂亮也會出問題。所以我們從應用開始改。

## 第一步：讓應用適合跑在容器裡

有四件事必須先確認。這四件事在傳統部署可有可無，在容器裡是必要條件。

### 1. 監聽 `0.0.0.0`，不是 `localhost`

第三章講過這個坑：程式綁在 `127.0.0.1` 就只有自己連得到。在容器裡這代表**外面永遠連不進來**，而且症狀是 connection refused，看起來像服務沒起來。

ASP.NET Core 用環境變數控制：

```
ASPNETCORE_URLS=http://+:8080
```

`+` 的意思就是「所有網路介面」，等同 `0.0.0.0`。.NET 8 之後官方映像預設就是 8080（不是 80），因為非 root 使用者不能綁 1024 以下的 port——這是第二章講的 Linux 權限規則。

### 2. 設定從環境變數讀，不要寫死

容器映像應該是「同一份，到哪都能跑」，所以連線字串、API 位址這些**會因環境而異的東西不能烤進映像裡**。開發、測試、正式應該用同一個映像，只是餵不同的設定。

好消息是 ASP.NET Core 原生就支援：環境變數的優先序高於 `appsettings.json`，而巢狀設定用雙底線表示層級。

```
ConnectionStrings__DefaultConnection=User Id=app;Password=...;Data Source=oracle-svc:1521/XEPDB1
Logging__LogLevel__Default=Information
```

這會覆蓋掉 `appsettings.json` 裡的 `ConnectionStrings:DefaultConnection`。之後在 K8s 裡，這些值會來自 ConfigMap 與 Secret（下一章）。

**反例**：把連線字串寫在 `appsettings.Production.json` 裡再一起打包進映像。這樣做的下場是密碼進了映像層（而且如第 0 章所述，**映像層刪不掉東西**，就算你之後改掉，舊層裡的密碼還在），而且換環境就要重 build。

### 3. 日誌輸出到 stdout

傳統做法是寫進 `logs/app.log`。在容器裡這是錯的——第五章證明過**容器裡的檔案會隨容器消失**，而且外面的日誌收集系統看不到它。

正確做法是直接輸出到標準輸出（`Console.WriteLine` 或 ILogger 的 Console provider），讓容器 runtime 接走，K8s 的 `kubectl logs` 才看得到，ELK/Loki 也才收得到。ASP.NET Core 預設就這麼做，只要**不要**額外設定寫檔即可。

### 4. 提供健康檢查端點

K8s 需要知道「你活著嗎」和「你準備好了嗎」（正文第 4 章的三種 probe）。應用要提供對應的端點：

```csharp
builder.Services.AddHealthChecks()
    .AddOracle(connectionString, name: "oracle", tags: new[] { "ready" });

var app = builder.Build();

// 存活：只看自己，不查下游
app.MapHealthChecks("/healthz", new HealthCheckOptions
{
    Predicate = _ => false // 不跑任何檢查，能回應就代表 process 活著
});

// 就緒：可以包含下游依賴
app.MapHealthChecks("/readyz", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});
```

**兩個端點分開這件事很重要。** 存活檢查（liveness）如果去查資料庫，資料庫抖一下，你所有的 Pod 會同時被判定為死亡並重啟——這是正文第 4 章反覆強調的災難。就緒檢查（readiness）失敗只會讓流量繞開這個 Pod，不會重啟它，所以放下游依賴才是合理的。

## 第二步：ASP.NET Core 的 Dockerfile

先看完整版，再逐段解釋：

```dockerfile
# ---------- 建置階段 ----------
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# 先只複製專案檔並還原套件——這一層只有 csproj 變動時才會重建
COPY ["MyApi/MyApi.csproj", "MyApi/"]
RUN dotnet restore "MyApi/MyApi.csproj"

# 再複製其餘原始碼並發布
COPY . .
WORKDIR /src/MyApi
RUN dotnet publish "MyApi.csproj" -c Release -o /app/publish --no-restore

# ---------- 執行階段 ----------
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
USER $APP_UID

ENTRYPOINT ["dotnet", "MyApi.dll"]
```

### 為什麼要兩個階段

`FROM` 出現兩次，這叫**多階段建置（multi-stage build）**，是這份 Dockerfile 最重要的設計。

建置需要完整的 .NET SDK（編譯器、NuGet、建置工具），那個映像大約 800 MB。但**執行**只需要 runtime，大約 200 MB。多階段建置讓你在第一階段用 SDK 編譯，然後只把編譯產物（`/app/publish`）複製到乾淨的 runtime 映像裡。

差別不只是體積。SDK 映像裡有編譯器和你的完整原始碼——如果最終映像帶著它們上正式環境，等於把原始碼和一堆攻擊面一起送出去。多階段建置讓最終映像**只有跑起來需要的東西**。

### 為什麼先 COPY csproj 再 COPY 全部

這是利用**映像層快取**。Docker 建置時每個指令產生一層，如果某一層的輸入沒變，它會直接用快取。

`dotnet restore` 通常要花不少時間，但套件清單（csproj）很少變，而原始碼天天在改。所以順序是：先只複製 csproj → restore（這層被快取住）→ 再複製原始碼 → publish。這樣改一行 C# 程式碼重 build 時，restore 那層直接跳過。

**反過來寫的話**（先 `COPY . .` 再 restore），任何一個字元的改動都會讓快取失效，每次 build 都要重新下載所有套件。這個順序問題是 CI 速度慢的頭號原因。

### `USER $APP_UID`

.NET 8 之後的官方映像內建一個非 root 使用者，`$APP_UID` 是它的 UID（64198）。加這一行讓容器以非 root 身份執行。

為什麼重要：容器裡的 root **就是主機上的 root**（共用核心，第五章講過），一旦容器被入侵，攻擊者的起點就高得多。K8s 的 `restricted` 安全等級（正文第 8 章）也會直接拒絕以 root 執行的容器，所以現在做好，之後才不會被擋。

### `.dockerignore`

跟 Dockerfile 放同一層，內容是不要送進建置流程的東西：

```
**/bin/
**/obj/
**/node_modules/
**/.git/
**/.vs/
**/appsettings.Development.json
**/*.user
```

漏寫這個檔案有兩個實際後果：build 變慢（把幾百 MB 的 `node_modules` 和 `.git` 傳進去），以及**本機的建置產物覆蓋掉容器內的**（`bin/` 裡是你 Windows 上編的東西，複製進 Linux 容器會出現各種詭異錯誤）。

建置與測試：

```powershell
docker build -t my-api:1.0.0 .
docker run -d --name api -p 8080:8080 my-api:1.0.0
curl.exe http://localhost:8080/healthz
docker logs api
docker rm -f api
```

## 第三步：React 前端的 Dockerfile

前端的邏輯不太一樣。React 應用最終是一堆靜態檔案（HTML/CSS/JS），不需要 Node 執行環境——它需要的是一個能把檔案送出去的網頁伺服器。

```dockerfile
# ---------- 建置階段 ----------
FROM node:22-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------- 執行階段 ----------
FROM nginx:1.27-alpine AS final
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
```

同樣是多階段：Node 只在建置時需要（`node_modules` 動輒幾百 MB），最終映像只有 nginx 加上編譯出來的靜態檔，通常不到 50 MB。

`npm ci` 而不是 `npm install`：前者嚴格依照 `package-lock.json` 安裝，結果可重現；後者可能悄悄升級版本，讓「昨天 build 出來的和今天不一樣」。**在 CI 裡一律用 `npm ci`。**

搭配的 `nginx.conf` 有一個必要設定：

```nginx
server {
    listen 8080;
    root /usr/share/nginx/html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

`try_files ... /index.html` 是 SPA 必備：使用者直接輸入 `/users/123` 這種前端路由時，nginx 找不到對應的實體檔案，必須回退到 `index.html` 讓 React Router 接手。少了這一行，重新整理頁面就會 404——這是前端容器化最常見的問題。

### 前端環境變數的兩難

後端可以在啟動時讀環境變數，前端不行——**React 的環境變數在 build 時就被烤進 JS 檔案裡了**。這代表你如果把 API 位址設成 build 時的變數，開發、測試、正式就得各 build 一份映像，違背了「同一個映像到處跑」的原則。

兩個解法：

**解法一（推薦）：用相對路徑，讓 Ingress 處理。** 前端呼叫 `/api/users` 而不是 `https://api.example.com/users`，由 Ingress 依路徑把 `/api` 導到後端服務（下一章會設定）。這樣前端映像完全不需要知道後端在哪。

**解法二：runtime 注入設定檔。** 容器啟動時產生一個 `/config.json`，前端啟動時先去讀它：

```dockerfile
COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
```

```sh
#!/bin/sh
cat > /usr/share/nginx/html/config.json <<EOF
{ "apiBaseUrl": "${API_BASE_URL}" }
EOF
exec nginx -g "daemon off;"
```

需要跨網域呼叫後端時用這個方法。單一網域的話解法一乾淨得多。

## 第四步：本機串起來測

在丟上 K8s 之前，先用 Docker Compose 確認兩個容器能一起工作。這一步會省下很多在 K8s 上瞎猜的時間——**如果在 Compose 裡就不通，那跟 K8s 沒關係。**

```yaml
services:
  api:
    build: ./MyApi
    environment:
      ASPNETCORE_URLS: http://+:8080
      ConnectionStrings__DefaultConnection: "User Id=app;Password=dev;Data Source=oracle:1521/XEPDB1"
    ports:
      - "8080:8080"
    depends_on:
      oracle:
        condition: service_healthy

  web:
    build: ./frontend
    ports:
      - "3000:8080"
    depends_on:
      - api

  oracle:
    image: gvenzl/oracle-free:23-slim
    environment:
      ORACLE_PASSWORD: dev
    healthcheck:
      test: ["CMD", "healthcheck.sh"]
      interval: 10s
      retries: 20
```

```powershell
docker compose up --build
```

注意 `depends_on` 的 `condition: service_healthy`——附錄 C-8 提過，這是 Compose 有而 **K8s 沒有**的能力。在 K8s 裡沒有「等資料庫好了再啟動」這回事，你的應用必須自己能承受「啟動時資料庫還沒好」並重試。這是從 Compose 搬到 K8s 時最常被忽略的差異，值得現在就在應用裡處理好。

## 第五步：版本標籤策略

最後一件事：映像怎麼命名。

**永遠不要用 `latest`。** 原因是它沒有辨識度——出事時你無法知道線上跑的到底是哪一版程式碼，回滾也無從滾起。而且 K8s 對 `latest` 的預設拉取策略是「每次都重拉」，行為難以預測。

合理的做法是把版本號跟你的發版流程綁定：

| 標籤 | 何時用 |
| --- | --- |
| `my-api:1.4.0` | 對應 git tag 的正式版本 |
| `my-api:1.4.0-abc1234` | 加上 commit SHA，最精確 |
| `my-api:sha256:...`（digest） | 最嚴格，完全不可變 |

你的環境用 `V.X.X.X.X.X` 格式的 git tag 觸發部署，那就讓 CI 從 tag 解析出版本號當映像標籤（附錄 C-8 有完整的 workflow 範例，實戰第三章會串起來）。

## 檢查清單

容器化完成前，逐項確認：

- [ ] 應用監聽 `0.0.0.0`（.NET 用 `ASPNETCORE_URLS=http://+:8080`）
- [ ] 所有環境相關設定都能從環境變數覆蓋，沒有寫死在映像裡
- [ ] 沒有任何密碼、金鑰進入映像（包含 `appsettings.Production.json`）
- [ ] 日誌輸出到 stdout，沒有寫進容器內的檔案
- [ ] 有 `/healthz`（只看自己）與 `/readyz`（可含下游）兩個端點
- [ ] 使用多階段建置，最終映像不含 SDK 與原始碼
- [ ] 先 COPY 依賴清單再 COPY 原始碼，善用層快取
- [ ] 有 `.dockerignore`，排除 `bin/`、`obj/`、`node_modules/`、`.git/`
- [ ] `USER` 設為非 root
- [ ] 前端有 SPA 的 `try_files` 回退設定
- [ ] 映像標籤帶版本號，不是 `latest`
- [ ] 應用能承受「啟動時依賴還沒就緒」並自行重試

## 本章回顧

- 容器化的第一步不是寫 Dockerfile，是**讓應用適合跑在容器裡**：綁 `0.0.0.0`、設定外部化、日誌到 stdout、提供健康檢查
- **多階段建置**讓最終映像只含執行所需，體積小、攻擊面小、不帶原始碼
- **先複製依賴清單再複製原始碼**，讓套件還原那層能被快取
- `.dockerignore` 同時影響 build 速度與正確性
- 非 root 執行不只是好習慣，也是 K8s `restricted` 等級的硬要求
- 前端環境變數在 build 時就固定，用相對路徑 + Ingress 是最乾淨的解法
- 上 K8s 之前先用 Compose 驗證一次，但要記得 K8s 沒有 `depends_on` 的等待能力

## 自我檢查

1. 為什麼 Dockerfile 要先 COPY csproj 再 COPY 其他檔案？
2. 為什麼最終映像不該用 SDK 映像？
3. liveness 端點為什麼不該檢查資料庫？
4. 前端的 API 位址為什麼不能用一般的環境變數處理？
5. 為什麼 `latest` 標籤在正式環境是壞主意？

下一章把這兩個映像部署到 K8s，寫出完整的一組 manifest。

## 連結

- [[intro-5-first-container-and-pod]] — 入門 5：Docker 與 K8s 的第一次接觸
- [[practice-2-deploy-real-app]] — 下一章：完整部署一組真實應用
- [[00-docker-foundations]] — 正文：容器原理、image layer、多階段建置的深入說明
- [[25-yaml-fields-pipeline]] — 附錄 C-8：Docker Compose 全欄位與 GitHub Actions
- [[dotnet-web-api]] — ASP.NET Core 架構與設定系統
- [[k8s-mastery]] — 教材總目錄（含各階段的閱讀路徑）
