---
type: reference
domain: tech
tags: [kubernetes, k8s, ingress, ingress-nginx, annotations, reference, canary, oauth]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 附錄 F：ingress-nginx annotation 百科

附錄 C-3 講 Ingress 的時候留了一句話：「規格本身只定義了很少的東西，真正的能力全在 annotation 裡。」這一份把那句話展開。

Ingress 的 API 規格只有 host、path、backend、TLS 四件事。你在正式環境真正需要的——路徑重寫、限流、逾時、上傳大小、金絲雀分流、外部認證——一項都不在規格裡，全部是 controller 自訂的 annotation。這造成一個尷尬的局面：這些設定既是必需品，又完全不可攜，而且 `kubectl explain` 查不到、YAML schema 驗證也擋不住打錯的 key（打錯只會靜默失效）。

這份百科收錄 ingress-nginx 最常用的那批 annotation，按用途分組。所有 annotation 都以 `nginx.ingress.kubernetes.io/` 為前綴，表格中省略。

> **先講安全**：snippet 類 annotation（`configuration-snippet`、`server-snippet`）自 controller v1.9 起**預設停用**，因為它們等於讓任何能建立 Ingress 的人往 nginx 設定檔注入任意內容。2025 年的 IngressNightmare 系列漏洞（CVE-2025-1974 等）正是這條路徑的 RCE。新版另有 `annotations-risk-level` 機制，預設會擋掉高風險 annotation。**不要為了方便就把這些開關打開**——先確認有沒有非 snippet 的作法。

---

## 一、路由與重寫

| annotation | 值 | 說明 |
| --- | --- | --- |
| `rewrite-target` | 路徑（可含 `$1`） | 轉發給後端前改寫路徑 |
| `use-regex` | `"true"` | 讓 `path` 以正則解讀，`rewrite-target` 才能用捕獲群組 |
| `app-root` | `/app` | 存取 `/` 時 302 到指定路徑 |
| `permanent-redirect` | URL | 301 永久轉址 |
| `permanent-redirect-code` | `301`/`308` | 轉址狀態碼 |
| `temporal-redirect` | URL | 302 暫時轉址 |
| `server-alias` | `alt.example.com` | 同一條規則額外接受的 host |
| `x-forwarded-prefix` | `/api` | 告訴後端它被掛在哪個前綴下 |

`rewrite-target` 是全表最常寫錯的一個，因為它有兩種完全不同的用法：

```yaml
# 用法一：固定改寫。/api/users → /users
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - http:
        paths:
          - path: /api
            pathType: Prefix

# 用法二：捕獲群組。/api/users/1 → /users/1（保留後段）
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  rules:
    - http:
        paths:
          - path: /api(/|$)(.*)
            pathType: ImplementationSpecific
```

用法一會把 `/api` 底下**所有**路徑都改寫成 `/`，於是 `/api/users` 與 `/api/orders` 都變成 `/`——這通常不是你要的，但它是最常被複製貼上的寫法。需要保留後段就必須用捕獲群組，而且 `pathType` 要用 `ImplementationSpecific`（`Prefix` 不允許正則）。

---

## 二、後端協定與逾時

| annotation | 預設 | 說明 |
| --- | --- | --- |
| `backend-protocol` | `HTTP` | `HTTP`｜`HTTPS`｜`GRPC`｜`GRPCS`｜`FCGI`｜`AJP` |
| `proxy-connect-timeout` | `5`（秒） | 與後端建立連線的逾時 |
| `proxy-read-timeout` | `60` | 等後端回應的逾時 |
| `proxy-send-timeout` | `60` | 送資料給後端的逾時 |
| `proxy-next-upstream` | `error timeout` | 什麼情況換下一個後端 |
| `proxy-next-upstream-tries` | `3` | 最多換幾次 |
| `proxy-buffering` | `off` | 開啟後 nginx 會先緩衝完整回應才回給客戶端 |
| `proxy-request-buffering` | `on` | 關掉可支援串流上傳 |
| `service-upstream` | `"false"` | `"true"` 時走 Service ClusterIP 而非直接連 Pod IP |

`proxy-read-timeout` 預設 60 秒這件事，是「長查詢／報表下載跑到一半斷掉」的標準原因。SSE 或 WebSocket 這類長連線更要調大（常設 `3600`），並且要關掉 `proxy-buffering`，否則事件會被緩衝住不即時送出。

`backend-protocol: GRPC` 是 gRPC 服務能不能通的關鍵——沒設的話 nginx 會用 HTTP/1.1 跟後端說話，gRPC 直接失敗。

---

## 三、大小限制

| annotation | 預設 | 說明 |
| --- | --- | --- |
| `proxy-body-size` | `1m` | **請求主體上限**，設 `0` 為不限制 |
| `client-body-buffer-size` | `8k` | 超過就寫暫存檔 |
| `proxy-buffer-size` | `4k` | 回應標頭緩衝，後端回大量 header（例如長 JWT）時要調大 |

`proxy-body-size: 1m` 是預設值，也是「檔案上傳失敗但應用日誌什麼都沒有」的頭號原因——請求根本沒到應用就被 nginx 以 413 擋掉。設定時記得**這條鏈上每一層都有自己的上限**：Cloudflare（免費方案約 100 MB）、ingress-nginx、應用框架本身。任何一層漏改，症狀都一樣。

---

## 四、TLS 與憑證

| annotation | 說明 |
| --- | --- |
| `ssl-redirect` | 有 TLS 設定時預設 `true`，自動把 HTTP 導向 HTTPS |
| `force-ssl-redirect` | 即使該 host 沒設 TLS 也強制導向 |
| `ssl-passthrough` | 不解密，直接把 TLS 流量丟給後端（**controller 必須啟用此功能**，且會失去所有 L7 能力） |
| `proxy-ssl-secret` | 連後端時使用的客戶端憑證（namespace/name） |
| `proxy-ssl-verify` | 是否驗證後端憑證 |
| `auth-tls-secret` | mTLS：驗證客戶端憑證用的 CA |
| `auth-tls-verify-client` | `on`｜`off`｜`optional` |
| `auth-tls-verify-depth` | 憑證鏈深度 |
| `auth-tls-pass-certificate-to-upstream` | 把客戶端憑證轉給後端 |

`ssl-passthrough` 要特別小心：一旦開啟，這條 Ingress 上所有 L7 功能（路徑路由、header 改寫、重寫）全部失效，因為 nginx 根本看不到明文。只有在後端必須自己終結 TLS（例如某些資料庫代理）時才用。

---

## 五、存取控制與認證

| annotation | 說明 |
| --- | --- |
| `whitelist-source-range` | CIDR 白名單，逗號分隔 |
| `denylist-source-range` | CIDR 黑名單 |
| `auth-type` | `basic`｜`digest` |
| `auth-secret` | htpasswd 格式的 Secret |
| `auth-secret-type` | `auth-file`｜`auth-map` |
| `auth-realm` | 提示文字 |
| `auth-url` | **外部認證服務**的 URL |
| `auth-signin` | 認證失敗時導向的登入頁 |
| `auth-signin-redirect-param` | 回跳參數名，預設 `rd` |
| `auth-response-headers` | 把外部認證服務回傳的 header 轉給後端 |
| `auth-cache-key` / `auth-cache-duration` | 認證結果快取，減少對認證服務的壓力 |

外部認證（`auth-url`）是把 Google OAuth 這類登入流程加在既有服務前面而**完全不改應用程式**的標準做法。配合 oauth2-proxy 的典型組合：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: internal-dashboard
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "https://auth.example.com/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://auth.example.com/oauth2/start?rd=$escaped_request_uri"
    nginx.ingress.kubernetes.io/auth-response-headers: "x-auth-request-user, x-auth-request-email"
    nginx.ingress.kubernetes.io/auth-cache-key: "$remote_user$http_authorization"
    nginx.ingress.kubernetes.io/auth-cache-duration: "200 202 5m"
spec:
  ingressClassName: nginx
  rules:
    - host: dashboard.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: dashboard
                port:
                  number: 80
```

運作方式是：nginx 收到請求後先打 `auth-url`，回 2xx 就放行、回 401 就導去 `auth-signin`。後端服務透過 `auth-response-headers` 帶進來的 header 知道使用者是誰，自己完全不需要實作 OAuth。

> 注意 `auth-url` 對每個請求都會多一次內部呼叫。沒設 `auth-cache-duration` 的話，認證服務會成為所有流量的瓶頸與單點。

---

## 六、流量控制

| annotation | 說明 |
| --- | --- |
| `limit-rps` | 每秒請求數上限（單一來源 IP） |
| `limit-rpm` | 每分鐘請求數上限 |
| `limit-connections` | 單一 IP 併發連線上限 |
| `limit-burst-multiplier` | 允許的突發倍數，預設 5 |
| `limit-rate` / `limit-rate-after` | 回應傳輸速率限制（bytes/s） |
| `limit-whitelist` | 不受限流的 CIDR |

限流是在 nginx 層做的，**每個 controller 副本各自計數**。三個副本設 `limit-rps: 10`，實際上限接近 30。要精確限流得靠應用層或 API Gateway。

---

## 七、負載平衡與工作階段黏著

| annotation | 說明 |
| --- | --- |
| `upstream-hash-by` | 一致性雜湊的鍵，如 `$request_uri`、`$remote_addr` |
| `affinity` | `cookie`（唯一支援值） |
| `affinity-mode` | `balanced`（預設，後端變動時重新分配）｜`persistent`（盡量不變） |
| `session-cookie-name` | 預設 `INGRESSCOOKIE` |
| `session-cookie-expires` / `session-cookie-max-age` | 有效期 |
| `session-cookie-path` | 搭配 `rewrite-target` 時通常要明確指定 |
| `session-cookie-samesite` | `Lax`｜`Strict`｜`None` |
| `session-cookie-conditional-samesite-none` | 對不支援的瀏覽器自動省略 |

`affinity-mode: balanced` 的意思是「後端數量變動時允許重新分配」——也就是**滾動更新時黏著會斷**。需要在部署期間也維持黏著的服務要用 `persistent`，但代價是後端不均。

更根本的建議：黏著是狀態外部化沒做好的補丁。能把 session 放進 Redis 就不要靠 cookie 黏著。

---

## 八、金絲雀發布

Canary 的做法是**另建一條 Ingress**，host 與 path 與正式版相同，加上 canary annotation：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
spec:
  ingressClassName: nginx
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app-canary
                port:
                  number: 80
```

| annotation | 說明 |
| --- | --- |
| `canary` | `"true"` 標記這是金絲雀 Ingress |
| `canary-weight` | 導流百分比（相對 `canary-weight-total`） |
| `canary-weight-total` | 預設 `100`，設 `1000` 可做到 0.1% 精度 |
| `canary-by-header` | 指定 header 存在且值為 `always` 時強制走 canary |
| `canary-by-header-value` | 自訂觸發值 |
| `canary-by-header-pattern` | 用正則比對 header 值 |
| `canary-by-cookie` | 依 cookie 決定，值為 `always` / `never` |

**優先序是固定的**：`canary-by-header` > `canary-by-cookie` > `canary-weight`。這個順序讓你可以同時做「10% 隨機流量 + 內部人員帶 header 一定走新版」的組合，測試與灰度互不干擾。

限制：一個 host + path 只能有**一條** canary Ingress，而且 canary Ingress 上除了 canary 系列之外的 annotation 大多會被忽略（它繼承正式版那條的設定）。

---

## 九、CORS

| annotation | 預設 |
| --- | --- |
| `enable-cors` | `"false"` |
| `cors-allow-origin` | `*`（可逗號分隔多個） |
| `cors-allow-methods` | `GET, PUT, POST, DELETE, PATCH, OPTIONS` |
| `cors-allow-headers` | 一長串常見 header |
| `cors-allow-credentials` | `"true"` |
| `cors-expose-headers` | — |
| `cors-max-age` | `1728000` |

在 ingress 層開 CORS 的前提是**應用自己不要也回一份**——兩邊都送 `Access-Control-Allow-Origin` 會讓瀏覽器因為重複 header 而拒絕。決定一個地方做就好。

---

## 十、其他

| annotation | 說明 |
| --- | --- |
| `default-backend` | 這條 Ingress 專屬的錯誤／預設後端 |
| `custom-http-errors` | 哪些狀態碼交給 default-backend 產生自訂錯誤頁 |
| `mirror-target` | 把流量複製一份到另一個 URL（回應丟棄） |
| `mirror-request-body` | 是否連 body 一起鏡像 |
| `enable-modsecurity` / `enable-owasp-core-rules` | WAF |
| `enable-access-log` | 關閉高流量路徑的存取日誌 |
| `load-balance` | 覆蓋全域演算法（`round_robin`／`ewma`） |
| `configuration-snippet` | location 區塊注入（**預設停用**） |
| `server-snippet` | server 區塊注入（**預設停用**） |

`mirror-target` 是上線新版本前的最佳驗證手段：把正式流量複製一份到新版，觀察它的錯誤率與延遲，但回應完全不影響使用者。

---

## 全域設定：controller 的 ConfigMap

annotation 是逐條 Ingress 的設定，全域預設值在 controller 的 ConfigMap 裡。改這裡等於改所有 Ingress 的預設。

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  proxy-body-size: "50m"
  proxy-read-timeout: "120"
  use-gzip: "true"
  gzip-types: "application/json application/javascript text/css"
  use-forwarded-headers: "true" # 前面有 LB/CDN 時必開，否則拿不到真實來源 IP
  compute-full-forwarded-for: "true"
  enable-real-ip: "true"
  proxy-real-ip-cidr: "173.245.48.0/20" # 只信任你的 CDN 網段
  hsts: "true"
  hsts-max-age: "31536000"
  ssl-protocols: "TLSv1.2 TLSv1.3"
  keep-alive: "75"
  worker-processes: "auto"
  max-worker-connections: "16384"
  allow-snippet-annotations: "false" # 保持關閉
  annotations-risk-level: "High"
  log-format-upstream: '$remote_addr - $request_id [$time_local] "$request" $status $body_bytes_sent $request_time $upstream_response_time'
```

兩個值得特別設的：`use-forwarded-headers` 在前面有 Cloudflare 或雲端 LB 時必開，否則所有存取日誌與限流看到的都是 LB 的 IP；`log-format-upstream` 加上 `$request_id` 與 `$upstream_response_time`，可以把 ingress 的延遲與後端的延遲分開看——排查「到底是誰慢」時這兩個欄位省下大量時間。

---

## 常見誤設十連

| # | 誤設 | 症狀 | 正解 |
| --- | --- | --- | --- |
| 1 | annotation key 打錯字 | **完全靜默失效**，沒有任何錯誤 | `kubectl exec` 進 controller 跑 `cat /etc/nginx/nginx.conf` 確認實際生效 |
| 2 | `rewrite-target: /` 配 Prefix path | 所有子路徑都被改寫成 `/` | 要保留後段就用捕獲群組 + `use-regex` |
| 3 | 沒調 `proxy-body-size` | 上傳大檔 413，應用日誌無紀錄 | 整條鏈（CDN → ingress → 應用）都要調 |
| 4 | 長輪詢／SSE 沒調 `proxy-read-timeout` | 60 秒準時斷線 | 調大並關閉 `proxy-buffering` |
| 5 | gRPC 沒設 `backend-protocol: GRPC` | 連線失敗或協定錯誤 | 明確指定 |
| 6 | TLS Secret 與 Ingress 不同 namespace | 退回預設自簽憑證，瀏覽器警告 | 必須同 namespace |
| 7 | 前面有 CDN 卻沒開 `use-forwarded-headers` | 日誌與限流全看到 CDN 的 IP | 開啟並設 `proxy-real-ip-cidr` |
| 8 | canary Ingress 上加了其他 annotation | 被忽略，行為與預期不符 | canary Ingress 只認 canary 系列 |
| 9 | 為了方便打開 snippet annotation | 開了一條 RCE 路徑 | 保持 `allow-snippet-annotations: "false"` |
| 10 | 以為限流是全叢集的 | 實際上限 = 設定值 × 副本數 | 精確限流要在應用層做 |

第一條值得展開：**annotation 打錯字不會有任何回饋**。API Server 不驗證 annotation 內容，controller 認不得的 key 就直接忽略。所以每次加了新 annotation，唯一可靠的驗證方式是進 controller Pod 看產生的 `nginx.conf` 裡有沒有對應的設定，或用 `kubectl describe ing` 看 controller 的 event。

---

## 什麼時候該離開 Ingress

annotation 用到十幾條、或是開始需要 snippet 才能達成需求時，代表你已經超出 Ingress 的設計範圍了。此時該評估的是 Gateway API（附錄 C-5）——header 改寫、權重分流、流量鏡像這些在 Gateway API 是**規格內的欄位**，有 schema 驗證、打錯會被拒絕、換 controller 也不用重寫。

一個實用的判準：如果你的 Ingress annotation 超過五條，或其中任何一條是 snippet，就值得排一次評估。

---

## 連結

- [[73-long-lived-connections]] — 附錄 AY：「WebSocket 每 60 秒斷一次」對應的就是讀取逾時
- [[66-ingress-to-gateway-api]] — 附錄 AR：**這份百科的存在本身就是 Ingress 的問題**——哪些 annotation 在 Gateway API 有對應、哪些沒有
- [[20-yaml-fields-network-storage]] — 附錄 C-3：Ingress 規格本體與 Gateway API
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：Gateway API 完整欄位、cert-manager
- [[24-yaml-fields-istio]] — 附錄 C-7：Istio 的等價能力對照
- [[25-yaml-fields-pipeline]] — 附錄 C-8：Cloudflare Tunnel 與上傳大小限制
- [[27-upgrades-and-deprecations]] — 附錄 E：controller 升級與 API 相容性
- [[05-networking]] — Ingress 在封包路徑中的位置
- [[k8s-mastery]] — 教材總目錄
