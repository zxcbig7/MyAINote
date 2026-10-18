---
type: reference
domain: tech
tags: [kubernetes, k8s, yaml, reference, github-actions, cloudflare-tunnel, docker-compose, cicd]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 C-8：交付鏈上的非 K8s YAML

一個 commit 要變成線上跑著的 Pod，中間經過的 YAML 不只有 K8s 的。它先被 GitHub Actions 的 workflow 檔決定怎麼建置、被 Compose 檔決定本機怎麼跑、最後被 cloudflared 的設定檔決定外面的人怎麼連進來。這三種檔案不歸 K8s API 管，`kubectl explain` 查不到，但寫錯的代價一樣真實——而且因為它們散在不同工具，出事時最難定位。

這一份把它們收在同一個地方，並且刻意對照 K8s 的對應概念，讓你在兩邊切換時不用重新建立心智模型。

---

## GitHub Actions Workflow

檔案放在 `.github/workflows/*.yml`。

### 觸發器：`on`

```yaml
name: Build and Deploy
run-name: "Deploy ${{ github.ref_name }} by @${{ github.actor }}"

on:
  push:
    branches: [main, "release/**"]
    branches-ignore: []
    tags: ["V.*.*.*.*.*"] # 你的版本格式；點是字面字元，* 不跨層級
    paths: ["src/**", "Dockerfile"]
    paths-ignore: ["**.md"]
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  schedule:
    - cron: "0 2 * * *" # 一律 UTC，沒有 timeZone 欄位可設
  workflow_dispatch: # 手動觸發，可帶輸入
    inputs:
      environment:
        description: "部署環境"
        required: true
        default: staging
        type: choice
        options: [staging, prod]
      dry_run:
        type: boolean
        default: false
  workflow_call: # 讓別的 workflow 呼叫（可重用 workflow）
    inputs:
      image_tag:
        required: true
        type: string
    secrets:
      REGISTRY_PASSWORD:
        required: true
    outputs:
      digest:
        value: ${{ jobs.build.outputs.digest }}
  workflow_run:
    workflows: ["CI"]
    types: [completed]
  release:
    types: [published]
  repository_dispatch:
    types: [deploy-request]
```

> `schedule` 的 cron **只有 UTC**，而且在 GitHub 負載高時可能延遲數十分鐘——不要拿它做有精確時間要求的事。這點與 K8s CronJob 有 `timeZone` 欄位不同（附錄 C-2）。

### 全域區塊

```yaml
permissions: # 預設權限，建議全域收緊、單一 job 再放寬
  contents: read
  packages: write
  id-token: write # OIDC 換雲端憑證時必要
  pull-requests: write

concurrency:
  group: "deploy-${{ github.ref }}"
  cancel-in-progress: true # 同一分支新的 push 取消舊的執行

env:
  REGISTRY: harbor.example.com
  IMAGE_NAME: team-a/my-app

defaults:
  run:
    shell: bash
    working-directory: ./src
```

`concurrency` 對部署類 workflow 是必要的：沒有它，連續兩次 push 會有兩個部署同時跑，後推的版本可能先完成，導致線上實際跑的是舊版。要注意部署 job 通常該設 `cancel-in-progress: false`（部署中途被砍更危險），只在建置階段開啟取消。

### `jobs` 全欄位

```yaml
jobs:
  build:
    runs-on: ubuntu-latest # 或 [self-hosted, linux, x64]
    timeout-minutes: 30
    if: github.event_name != 'pull_request'
    permissions:
      contents: read
      id-token: write
    environment: # 綁 GitHub Environment，可要求人工核准
      name: production
      url: https://example.com
    outputs:
      image_tag: ${{ steps.meta.outputs.tag }}
    strategy:
      fail-fast: false
      max-parallel: 3
      matrix:
        node: [18, 20, 22]
        os: [ubuntu-latest, windows-latest]
        include:
          - node: 22
            experimental: true
        exclude:
          - node: 18
            os: windows-latest
    container: # 整個 job 跑在容器裡
      image: node:22-alpine
      credentials:
        username: ${{ secrets.REGISTRY_USER }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
      options: --cpus 2
    services: # 附屬服務，等同測試用的 sidecar
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: meta
        name: 解析版本號
        run: echo "tag=${GITHUB_REF_NAME#V.}" >> "$GITHUB_OUTPUT"
      - name: 只在失敗時執行
        if: failure()
        run: ./scripts/notify.sh
        continue-on-error: true

  deploy:
    needs: [build] # 依賴，形成 DAG
    if: needs.build.result == 'success'
    runs-on: ubuntu-latest
    steps:
      - run: echo "部署 ${{ needs.build.outputs.image_tag }}"
```

| 欄位 | 說明 |
| --- | --- |
| `needs` | job 之間的依賴。沒寫的 job 全部平行跑 |
| `if` | 表達式不需要 `${{ }}` 包住（寫了也可以） |
| `strategy.matrix` | 展開成多個平行 job；`include` 追加組合、`exclude` 移除組合 |
| `strategy.fail-fast` | 預設 `true`，一個失敗就取消其他。跨版本測試通常要設 `false` |
| `environment` | 對應 repo 設定裡的 Environment，可設必須人工核准才能繼續 |
| `outputs` | 傳給下游 job，值來自 step 的 `$GITHUB_OUTPUT` |
| `services` | 由 Actions 起的附屬容器，概念等同 Pod 裡的 sidecar |

### 運算式與 context

| context | 常用欄位 |
| --- | --- |
| `github` | `ref`、`ref_name`、`sha`、`actor`、`event_name`、`repository`、`run_id`、`event.*` |
| `env` / `vars` / `secrets` | 環境變數、repo 變數、機密 |
| `needs.<job>` | `.result`、`.outputs.*` |
| `matrix` / `steps.<id>.outputs` / `job.status` / `runner.os` / `inputs` | 各自作用域 |

常用函式：`contains()`、`startsWith()`、`endsWith()`、`format()`、`join()`、`toJSON()`、`fromJSON()`、`hashFiles()`，以及狀態函式 `success()`、`failure()`、`always()`、`cancelled()`。

> `always()` 與 `if: failure()` 的差別：前者連 workflow 被取消都會跑，後者只在前面步驟失敗時跑。清理類步驟用 `always()`，通知類用 `failure()`。

### 完整範例：tag 觸發 → Harbor → GitOps

這是與你目前架構對應的骨架（tag 格式 `V.X.X.X.X.X`，推 Harbor 後更新 manifest repo 讓 ArgoCD 拉）。

```yaml
name: Release
on:
  push:
    tags: ["V.*.*.*.*.*"]

permissions:
  contents: read

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build-push:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.ver.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - id: ver
        run: echo "version=${GITHUB_REF_NAME#V.}" >> "$GITHUB_OUTPUT"

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: harbor.example.com
          username: ${{ secrets.HARBOR_USERNAME }} # robot 名稱含 $ 時務必走 secret
          password: ${{ secrets.HARBOR_PASSWORD }}

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: harbor.example.com/team-a/my-app:${{ steps.ver.outputs.version }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: false # Harbor 舊版對 attestation manifest 支援不佳

  bump-manifest:
    needs: [build-push]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: org/k8s-manifests
          token: ${{ secrets.MANIFEST_REPO_TOKEN }}

      - name: 只改這個服務的 tag
        env:
          VERSION: ${{ needs.build-push.outputs.version }}
        run: |
          yq -i '.image.tag = strenv(VERSION)' apps/my-app/values.yaml

      - run: |
          git config user.name "ci-bot"
          git config user.email "ci@example.com"
          git commit -am "chore: my-app -> ${{ needs.build-push.outputs.version }}"
          git push
```

兩個刻意的寫法，都對應第 13 章的真實踩坑：**用 `yq` 精準改單一欄位而不是 `sed` 全域替換**（全域 `sed` 會把其他服務的 tag 一起改掉，造成多服務互蓋），以及 **Harbor robot 帳號一律走 secret**（robot 名稱裡的 `$` 在 shell 展開會變成空字串，導致認證莫名失敗）。

### 常見誤設

| # | 誤設 | 症狀 | 正解 |
| --- | --- | --- | --- |
| 1 | `on.push.tags` 用了正則語法 | workflow 完全不觸發 | 是 glob 不是 regex，`*` 不跨 `/` |
| 2 | 部署 job 開 `cancel-in-progress: true` | 部署中途被砍，叢集停在半套狀態 | 建置可取消，部署不可 |
| 3 | `permissions` 沿用預設的寬鬆權限 | token 外洩即可改 repo | 全域 `contents: read`，個別 job 再放寬 |
| 4 | 用 `sed` 全域改 image tag | 其他服務的 tag 被一起改掉 | 用 `yq` 指定路徑 |
| 5 | secret 直接寫在 `run` 的字串裡 | 出現在 log（GitHub 只遮蔽已註冊的 secret） | 透過 `env:` 傳入 |
| 6 | 期望 `schedule` 準時 | 尖峰時可能延遲數十分鐘 | 有精確需求改用 K8s CronJob |
| 7 | matrix 沒關 `fail-fast` | 一個版本失敗看不到其他版本結果 | 測試矩陣設 `false` |

---

## Cloudflare Tunnel（cloudflared）

把叢集服務暴露到公網而不開任何入站 port。設定檔通常掛成 ConfigMap，憑證放 Secret。

```yaml
tunnel: my-cluster-tunnel # tunnel 名稱或 UUID
credentials-file: /etc/cloudflared/creds/credentials.json
metrics: 0.0.0.0:2000 # 健康檢查與 Prometheus 抓取端點
no-autoupdate: true # 容器環境一律關閉自動更新
loglevel: info
protocol: quic # auto | quic | http2；受限網路改 http2

originRequest: # 全域預設，可被單條 ingress 覆蓋
  connectTimeout: 30s
  tlsTimeout: 10s
  keepAliveConnections: 100
  keepAliveTimeout: 90s
  noTLSVerify: false
  originServerName: internal.example.com
  httpHostHeader: app.internal
  disableChunkedEncoding: false

ingress:
  - hostname: app.example.com
    path: /api/*
    service: http://api-svc.prod.svc.cluster.local:80
    originRequest:
      connectTimeout: 10s
  - hostname: app.example.com
    service: http://frontend-svc.prod.svc.cluster.local:80
  - hostname: ssh.example.com
    service: ssh://10.0.0.5:22
  - service: http_status:404 # 必須是最後一條，且不能有 hostname
```

三條規則：**`ingress` 由上而下比對，第一個命中即決定**（與 Istio VirtualService 相同）；**最後一條必須是沒有 `hostname` 的 catch-all**，否則 cloudflared 啟動就會失敗；`service` 可以是 `http://`、`https://`、`tcp://`、`ssh://`、`rdp://` 或 `http_status:<code>`。

在 K8s 裡的部署形式：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudflared
spec:
  replicas: 2 # 多副本＝多條連線，Cloudflare 端自動負載
  template:
    spec:
      containers:
        - name: cloudflared
          image: cloudflare/cloudflared:latest
          args: ["tunnel", "--config", "/etc/cloudflared/config/config.yaml", "run"]
          livenessProbe:
            httpGet:
              path: /ready
              port: 2000
            initialDelaySeconds: 10
          volumeMounts:
            - name: config
              mountPath: /etc/cloudflared/config
              readOnly: true
            - name: creds
              mountPath: /etc/cloudflared/creds
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: cloudflared-config
        - name: creds
          secret:
            secretName: tunnel-credentials
```

兩個已知限制值得寫在牆上（第 13 章有完整案例）：**免費方案的請求主體上限約 100 MB**，超過會失敗而症狀看起來像應用問題；**錯誤 1016（Origin DNS error）** 幾乎都是 `service` 指的叢集內 DNS 名稱解析不到——先確認 cloudflared Pod 與目標 Service 在同一叢集且 NetworkPolicy 有放行。

---

## Docker Compose（Compose Spec）

本機開發與 K8s 之間的橋。同一份服務定義，在 compose 與 K8s 的欄位對照如下：

| Compose | K8s | 差異 |
| --- | --- | --- |
| `image` / `build` | `containers[].image` | K8s 不會幫你 build |
| `ports: "8080:80"` | Service + `containerPort` | compose 直接綁主機 port |
| `environment` / `env_file` | `env` / `envFrom` | 對應直接 |
| `volumes` | `volumes` + `volumeMounts` | compose 的具名 volume ≈ PVC |
| `depends_on.condition` | initContainer 或重試 | **K8s 沒有啟動順序保證** |
| `restart: always` | `restartPolicy: Always` | 語意接近 |
| `deploy.resources` | `resources` | compose 只在 swarm 生效 |
| `healthcheck` | `livenessProbe` / `readinessProbe` | K8s 分成三種 probe |

```yaml
services:
  api:
    image: harbor.example.com/team-a/api:1.4.0
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
      args:
        BUILD_ENV: production
      cache_from: ["harbor.example.com/team-a/api:cache"]
    command: ["./app", "--port=8080"]
    entrypoint: ["/bin/sh", "-c"]
    environment:
      LOG_LEVEL: info
      DB_HOST: db
    env_file: [".env"]
    ports:
      - "8080:8080" # 短語法
      - target: 9090 # 長語法
        published: "9090"
        protocol: tcp
        mode: host
    expose: ["8080"]
    volumes:
      - ./src:/app/src:ro # bind mount
      - app-data:/var/lib/app # 具名 volume
      - type: tmpfs
        target: /tmp
    depends_on:
      db:
        condition: service_healthy # compose 有、K8s 沒有的能力
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 30s
    restart: unless-stopped # no | always | on-failure | unless-stopped
    user: "10001:10001"
    working_dir: /app
    init: true # 用 tini 當 PID 1，正確轉發訊號
    stop_grace_period: 30s
    cap_drop: ["ALL"]
    security_opt: ["no-new-privileges:true"]
    read_only: true
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks: [backend]
    profiles: [dev] # 只有指定 profile 時才啟動
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1.0"
          memory: 512M

volumes:
  app-data:

networks:
  backend:
    driver: bridge
```

`depends_on.condition: service_healthy` 是 compose 有而 K8s 沒有的能力——這正是為什麼從 compose 搬到 K8s 時，「等資料庫就緒再啟動」必須改寫成 init container 或應用自己重試（第 4 章）。把這個差異當成搬遷檢查清單的第一項，可以省掉很多「本機好好的，上叢集就壞」的困惑。

頂層還可用 `include`（引入其他 compose 檔）、`configs`、`secrets`，以及 YAML anchor 做共用片段：

```yaml
x-common: &common
  restart: unless-stopped
  logging:
    driver: json-file
    options:
      max-size: "10m"

services:
  api:
    <<: *common
    image: api:1.0
  worker:
    <<: *common
    image: worker:1.0
```

---

## 連結

- [[63-ci-in-cluster]] — 附錄 AO：把這些 workflow 跑在自己叢集裡的風險與做法
- [[24-yaml-fields-istio]] — 附錄 C-7：Istio 全欄位
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：ArgoCD/Helm/Prometheus 等生態系 CRD
- [[23-yaml-fields-rare-builtins]] — 附錄 C-6：冷門內建資源與元件設定檔
- [[cicd-pipeline]] — CI/CD 完整流程（Harbor + Helm + ArgoCD）
- [[domain-networking]] — DNS、Cloudflare 與 TLS
- [[00-docker-foundations]] — Dockerfile 逐指令與多階段建置
- [[13-troubleshooting]] — Harbor robot `$`、Cloudflare 1016、CI `sed` 互蓋等實際案例
- [[k8s-mastery]] — 教材總目錄
