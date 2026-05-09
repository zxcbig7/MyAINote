---
type: concept
domain: tech
tags: [dns, domain, networking, cloudflare, tls, https]
sources:
  - raw/tech/networking/網域小知識.md
  - raw/tech/devops/部屬後端.md
created: 2026-05-03
updated: 2026-05-03
---

# Domain / Networking

DNS（Domain Name System）是網際網路的電話簿，把 domain name 對應到 IP 或其他目標。

## 核心概念

| 術語 | 說明 |
| --- | --- |
| **Domain** | 名字（如 `viclai.idv.tw`） |
| **IP** | 地址（如 `93.184.216.34`） |
| **Name Server (NS)** | 指定誰來管這個 domain 的 DNS。例：在中華電信買的 domain，NS 預設是 `ns1.hinet.net` |

## DNS Record 類型

| Record | 一句話 |
| --- | --- |
| **A** | 名字 → IPv4 |
| **AAAA** | 名字 → IPv6 |
| **CNAME** | 名字 → 另一個名字（轉址標籤） |
| **MX** | 收信送到哪台伺服器 |
| **TXT** | 放任意文字（驗證身份用） |
| **NS** | 這個 domain 由哪台 DNS 管理 |
| **PTR** | IP → 名字（反查） |
| **CAA** | 哪家 CA 可以核發憑證 |

## CNAME vs A Record

```
A Record：直接給答案（名字 → IP）
example.com  A  93.184.216.34

CNAME：去找別人（名字 → 另一個名字）
www  CNAME  my-app.azurecontainerapps.io
```

**CNAME 限制**：同一 hostname 有 CNAME 就不能再加任何其他 record（如 A、MX）

## TXT Record 用途

TXT 是「備註欄」，放文字讓第三方服務讀取，使用者和瀏覽器看不到。

常見用途：
- **Azure 驗證**：確認你擁有這個 domain
  ```
  Azure 給你一串暗號 → 你填進 DNS TXT
  → Azure 去查 DNS 看到暗號 → 確認你是 domain 擁有者
  ```
- **SSL/TLS 驗證**：Let's Encrypt ACME challenge
- **SPF/DMARC**：Email 防偽設定

TXT 可以一對多（同一 hostname 可掛多筆 TXT）。

## TLS/SSL Binding

TLS Binding 是把憑證和域名綁在一起，告訴伺服器「當有人連到 `www.viclai.idv.tw`，用這張憑證加密」。

```
有 Binding：
使用者連到 https://www.viclai.idv.tw
→ 伺服器找到對應憑證
→ 建立加密連線
→ 瀏覽器顯示鎖頭

沒有 Binding：
→ 伺服器不知道用哪張憑證
→ 瀏覽器顯示「不安全」
```

## MyDevWeb 網域設定範例（viclai.idv.tw）

| Record 類型 | 名稱 | 值 | 用途 |
| --- | --- | --- | --- |
| CNAME | `www` | Azure Container Apps endpoint | 前端流量 |
| CNAME | `api` | Azure Container Apps endpoint | 後端 API 流量 |
| TXT | `asuid.www` | Azure 給的驗證碼 | Azure 確認擁有 www 子域名 |
| TXT | `asuid.api` | Azure 給的驗證碼 | Azure 確認擁有 api 子域名 |

## Azure Container Apps 自訂網域流程

```bash
# 1. 在 DNS 加 TXT 和 CNAME
#    TXT: asuid.api → <Azure 驗證碼>
#    CNAME: api → my-app.greenrock-e5ac13da.westus2.azurecontainerapps.io

# 2. Azure 新增自訂網域
az containerapp hostname add \
  --name my-api \
  --resource-group MyRG \
  --hostname api.viclai.idv.tw

# 3. 驗證並綁定 SSL
az containerapp hostname bind \
  --name my-api \
  --resource-group MyRG \
  --hostname api.viclai.idv.tw \
  --environment managedEnvironment-xxx \
  --validation-method CNAME

# 4. 驗證 DNS 設定
nslookup -type=TXT asuid.api.viclai.idv.tw
```

## Cloudflare Tunnel

Cloudflare Tunnel 可以不開放 server 的 port，就讓外部流量到達本機服務。在 MyDevWeb 用於讓 `viclai.idv.tw` 流量穿透到 minikube ingress。

```
使用者 → Cloudflare → cloudflared daemon（本機）
→ minikube tunnel → ingress-nginx → Service → Pod
```

**NS 切換到 Cloudflare**：把中華電信的 NS 改成 Cloudflare DNS，之後只需在 Cloudflare Dashboard 管理所有 DNS record。

## 常見 DNS 傳播

```bash
# 查詢 DNS 記錄
nslookup www.viclai.idv.tw
nslookup -type=TXT asuid.api.viclai.idv.tw
dig www.viclai.idv.tw CNAME

# DNS 傳播通常需要幾分鐘到幾小時（TTL 決定）
```

## 連結

- [[kubernetes]] — ingress 需要 domain 設定
- [[cicd-pipeline]] — 部署後的 domain 綁定
- [[argocd]] — GitOps 部署到 K8s 後的對外流量
