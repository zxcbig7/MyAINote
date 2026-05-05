# K8s 常見問題與指令紀錄

## 1. Docker Image Build 失敗 — TypeScript 未使用變數

**錯誤訊息**
```
error TS6133: 'IS_DEV' is declared but its value is never read.
```

**原因**  
TypeScript `noUnusedLocals` 設定開啟，宣告了但被注解掉的變數會報錯。

**解法**  
刪除或移除未使用的變數宣告。`_` 前綴只在 ESLint 有效，TypeScript 不認。

---

## 2. Pod 無法啟動 — TLS Secret 找不到

**錯誤訊息**
```
MountVolume.SetUp failed for volume "tls-volume": secret "web-app-tls" not found
```

**原因**  
Deployment 無條件掛載 TLS volume，但 DEV 環境沒有 TLS secret。

**解法**  
在 Helm template 加條件判斷：
```yaml
{{- if .Values.ingress.tls.enabled }}
- name: tls-volume
  ...
{{- end }}
```
並在 `values.yaml` 加預設值：
```yaml
ingress:
  tls:
    enabled: false
```

---

## 3. Helm Template 渲染失敗 — nil pointer

**錯誤訊息**
```
nil pointer evaluating interface {}.enabled
```

**原因**
`values.yaml` 沒有定義 `ingress.tls` 區塊，Helm 存取 `.Values.ingress.tls.enabled` 時拿到 nil。

**解法**
`values.yaml` 必須定義所有 template 會存取的欄位，即使是 `false`：
```yaml
ingress:
  enabled: false
  tls:
    enabled: false
```

---

## 4. nginx 容器 CrashLoop — 找不到 TLS 憑證

**錯誤訊息**
```
cannot load certificate "/etc/nginx/certs/tls.crt": No such file or directory
```

**原因**  
nginx ConfigMap 的設定硬寫了 SSL 憑證路徑，DEV 環境沒有憑證。

**解法**  
ConfigMap 也要加條件：
```yaml
{{- if .Values.ingress.tls.enabled }}
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/tls.crt;
    ...
}
{{- else }}
server {
    listen 80;
    ...
}
{{- end }}
```

---

## 5. CPU 不足 — Pod 排程失敗

**錯誤訊息**
```
0/1 nodes are available: 1 Insufficient cpu
```

**原因**  
所有 Pod 的 CPU requests 加總超過 node 上限（minikube 預設 2 CPU）。

**診斷指令**
```bash
kubectl describe nodes minikube | grep -A 10 "Allocated resources"
kubectl get pods -A
```

**解法**
- 降低 CPU requests（`25m` 而非 `100m`）
- 降低 replicas
- 關閉不必要的功能（Vault injection、CronJob）

---

## 6. Ingress 衝突 — 孤兒資源

**錯誤訊息**
```
admission webhook "validate.nginx.ingress.kubernetes.io" denied the request:
host "<host>" and path "/" is already defined in ingress <namespace>/<name>
```

**原因**  
舊的 ArgoCD Application 被刪除時，底下建立的 K8s 資源沒有一起清除（孤兒資源），導致新的 Ingress 與舊的衝突。

**常見發生時機**  
- Helm chart 資料夾重新命名
- 刪除 ArgoCD Application 但沒有 cascade 清除資源

**解法**  
手動刪除殘留的 Ingress 資源：
```bash
kubectl delete ingress <ingress-name> -n <namespace>
kubectl get all -n <namespace>   # 確認是否還有其他殘留
```

---

## 7. ArgoCD Sync 失敗 — 卡在舊 Commit

**症狀**  
ArgoCD 顯示的 Revision 不是最新的 commit。

**解法**  
強制 hard refresh：
```bash
kubectl annotate application <app-name> -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

---

## 8. ArgoCD port-forward 斷線

**錯誤訊息**
```
error creating forwarding stream for port 8080 -> 8080: Timeout occurred
```

**解法**  
重新執行 port-forward（Windows PowerShell）：
```powershell
# 找佔用 port 的程序
netstat -ano | findstr :8080

# 關掉程序
taskkill /PID <PID> /F

# 重新 port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

開啟：`https://localhost:8080`

---

## 9. WSL2 記憶體過高（VmmemWSL 吃超多）

**原因**  
WSL2 預設最多使用系統記憶體的 80%。

**解法**  
建立 `C:\Users\<user>\.wslconfig`：
```ini
[wsl2]
memory=2GB
processors=2
swap=512MB
```

套用：
```bash
wsl --shutdown
```

---

## 手機 / 外網連不到（Cloudflare Error 1016）

**症狀**  
手機打開 `https://viclai.idv.tw` 顯示 Cloudflare Error 1016。

**原因**  
`minikube tunnel` 沒有在跑，導致 `127.0.0.1:80` 無人接聽。cloudflared 雖然連到 Cloudflare，但流量打到本機時無法轉進 K8s ingress。

**確認方式**

```bash
# 確認 cloudflared 有在跑
tasklist | findstr cloudflared

# 嘗試啟動 minikube tunnel（若已有另一個在跑會提示錯誤，表示正常）
minikube tunnel
```

**解法**  
執行 `start.bat`，或在新終端機單獨跑：

```bash
minikube tunnel
```

> 重開電腦後兩個 tunnel 都需要重啟：`minikube tunnel` 和 `cloudflared tunnel run k8s-tunnel`。
> 最簡單的方式是直接執行 `start.bat`。

---

## 10. CI sed 覆蓋所有 tag — 多服務 image tag 互蓋

**症狀**  
某個服務的 pod 出現 `ImagePullBackOff`，image tag 是另一個服務的版本。

**原因**  
CI 使用全域 `sed` 替換 values 檔案中的 `tag:` 欄位：
```bash
sed -i "s|tag: .*|tag: \"$SHA\"|" values-prod.yaml
```
當多個服務共用同一個 values 檔案時，這條指令會把**所有** `tag:` 行都替換。

**解法**  
使用 sed address range 限定只替換特定 section：
```bash
# 只替換 sectionA 到 sectionB 之間的 tag
sed -i "/^sectionA:/,/^sectionB:/ s|tag: .*|tag: \"$TAG\"|" values.yaml

# 只替換 sectionB 到檔案結尾的 tag
sed -i "/^sectionB:/,$ s|tag: .*|tag: \"$TAG\"|" values.yaml
```

---

## 11. ImagePullBackOff — registry 找不到 image tag

**錯誤訊息**
```
manifest for <image>:<tag> not found: manifest unknown
```

**原因**  
CI 在 build/push image 之前就更新了 deployment repo 的 tag，或 CI job 失敗導致 image 未成功 push，但 deployment repo 已被更新。

**診斷**  
確認對應 commit 的 CI job 是否成功執行到 build & push image 步驟。

**解法**  
將 values 檔案的 tag 改回上一個成功的版本，commit + push，再觸發 ArgoCD sync。

---

## 12. Pod 無法啟動 — Secret 不存在

**錯誤訊息**
```
Error: secret "<secret-name>" not found
```

**原因**  
Helm template 用 `secretRef` 載入環境變數，但 K8s Secret 尚未建立。Secret 不屬於 Helm chart 管理範圍，不會自動建立。

**解法**  
手動建立 Secret（每個需要的 namespace 各需一份）：
```bash
kubectl create secret generic <secret-name> -n <namespace> \
  --from-literal=<KEY>="<value>"
```

---

## 13. 記憶體不足 — Pod 排程失敗（多環境同時跑）

**錯誤訊息**
```
0/1 nodes are available: 1 Insufficient memory
```

**原因**  
dev、stg、prod 三個環境同時跑，超過 minikube 記憶體上限。

**解法**  
暫時關掉不需要的環境：
```bash
kubectl scale deployment --all -n dev --replicas=0
kubectl scale deployment --all -n stg --replicas=0
```

---

## 14. 查詢 ArgoCD 初始密碼

**PowerShell**
```powershell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

帳號：`admin`

---

## 15. Harbor 憑證錯誤 — ERR_CERT_AUTHORITY_INVALID + HSTS

**錯誤訊息**

```text
net::ERR_CERT_AUTHORITY_INVALID
目前無法造訪，因為這個網站使用 HSTS
```

**原因**
Harbor 的 `externalURL` 設為 `https://`，但 `expose.tls.enabled: false`，造成 Harbor 回應中帶有 HSTS header。瀏覽器快取 HSTS 後，若 hosts 檔將 domain 指向本機 IP（繞過 Cloudflare），瀏覽器直連 Harbor 取得自簽憑證，觸發 HSTS 強制拒絕。

**解法（短期）**：清除 Chrome HSTS 快取：

1. 前往 `chrome://net-internals/#hsts`
2. 在 Delete domain security policies 輸入 domain → Delete
3. 前往 `chrome://net-internals/#dns` → Clear host cache

**解法（根本）**：移除 hosts 檔中的覆蓋條目，讓流量正常走 Cloudflare，或設定 cert-manager 取得有效憑證。

---

## 16. Docker Push 失敗 — Cloudflare 100MB 上限

**錯誤訊息**

```text
error parsing HTTP 413 response body
```

**原因**
Cloudflare 免費方案對 Proxied 的 HTTP 請求有 100MB request body 上限。Docker image layer 超過此大小時，push 被 Cloudflare edge 擋下。

**適用場景**：Docker registry（Harbor 等）透過 Cloudflare Proxy 對外時。

**解法**：

1. 將 Cloudflare DNS 該 record 改為 **DNS only（灰色雲朵）**
2. 設定 cert-manager + Let's Encrypt 取得有效 TLS 憑證
3. 路由器開 port 443 forwarding 到本機

這樣 Docker push 直連本機，不經過 Cloudflare proxy，不受大小限制。

---

## 17. Self-hosted Runner 在 Windows 使用 WSL bash 而非 Git Bash

**錯誤訊息**

```text
shell: C:\Windows\system32\bash.EXE --noprofile --norc -e -o pipefail {0}
<3>WSL (xxxxx) ERROR: CreateProcessEntryCommon:505: execvpe /bin/bash failed 2
```

**原因**
`shell: bash` 在 Windows runner 上會優先找 `C:\Windows\System32\bash.exe`（WSL bash）。若預設 WSL distro 沒有 bash（例如 `docker-desktop` 只有 `sh`），執行失敗。

**解法**
在 workflow 第一個 bash step 之前加一個 PowerShell step，把 Git Bash 路徑塞到 PATH 最前面：

```yaml
- name: Use Git Bash (not WSL bash)
  shell: powershell
  run: |
    $gitBin = "C:\Program Files\Git\bin"
    $gitUsr = "C:\Program Files\Git\usr\bin"
    "$gitBin`n$gitUsr" | Out-File -FilePath $env:GITHUB_PATH -Encoding utf8 -Append
    "PATH=$gitBin;$gitUsr;$($env:PATH)" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
```

需要執行 `wsl.exe` 的 step 單獨指定 `shell: powershell`，避免受到影響。

---

## 18. Docker Desktop daemon 解析到 Cloudflare Tunnel 內部 IPv6

**錯誤訊息**

```text
Error response from daemon: Get "https://<registry>/v2/": dial tcp [fd10:aec2:5dae::]:443: connect: network is unreachable
```

**原因**
Docker Desktop daemon 在獨立的 mount/network namespace 跑，其 DNS（`/proc/<pid>/root/etc/resolv.conf`）由 Docker Desktop 內部 resolver 提供。當 hostname 是 Cloudflare Tunnel domain 時，resolver 回傳私有 IPv6（`fd10::/16`），但 daemon namespace 沒有該 IPv6 路由，導致連線失敗。

修改 docker-desktop WSL2 主 namespace 的 `/etc/hosts` 對 daemon 無效，因為 daemon 在不同 mount namespace，看不到外面的 `/etc/hosts`。

**診斷方式**

```bash
# 查看 dockerd 的 PID
wsl -d docker-desktop -- ps | grep dockerd

# 查看 daemon 實際讀取的 hosts
wsl -d docker-desktop -- cat /proc/<pid>/root/etc/hosts

# 查看 daemon 實際讀取的 DNS
wsl -d docker-desktop -- cat /proc/<pid>/root/etc/resolv.conf
```

**解法**
用 `nsenter` 進入 daemon 的 mount namespace 修改 `/etc/hosts`：

```bash
wsl -d docker-desktop -- nsenter --target <dockerd-pid> --mount --uts -- sh -c \
  "grep -q '<hostname>' /etc/hosts || echo '104.x.x.x <hostname>' >> /etc/hosts"
```

寫入 Cloudflare 的公開 IPv4（用 `1.1.1.1` 查 A record 取得），而非 `127.0.0.1`，因為 daemon namespace 的 `127.0.0.1` 是 daemon 自己的 loopback，不是 Windows 主機的 loopback。

此修改在 Docker Desktop 重啟後會消失，需加進啟動腳本。

在 workflow 中自動修復：

```yaml
- name: Fix Docker DNS
  shell: powershell
  run: |
    wsl -d docker-desktop -- nsenter --target 172 --mount --uts -- sh -c `
      "grep -q '<hostname>' /etc/hosts || echo '104.x.x.x <hostname>' >> /etc/hosts"
```

---

## 19. PowerShell 字串展開導致 Docker login 帳號錯誤

**症狀**
`docker login` 回 `unauthorized`，即使帳密正確。

**原因**
Harbor robot account 名稱包含 `$`，例如 `robot$project+name`。在 PowerShell 雙引號字串中，`$project` 會被當成變數展開成空字串，實際送出 `robot+name`。

在 bash 中同理，`"robot$project+name"` 的 `$project` 也會被展開。

**解法**

```powershell
# PowerShell 用單引號
echo "token" | docker login registry -u 'robot$project+name' --password-stdin
```

```bash
# bash 中透過環境變數傳遞，避免展開
env:
  HARBOR_USERNAME: ${{ secrets.HARBOR_USERNAME }}
run: |
  echo "$HARBOR_PASSWORD" | docker login $HARBOR_URL -u "$HARBOR_USERNAME" --password-stdin
```

---

## 常用診斷指令

```bash
# 查看所有 namespace 的 Pod
kubectl get pods -A

# 查看 Pod 錯誤日誌
kubectl logs -n <namespace> deployment/<name> --previous

# 查看 node 資源使用量
kubectl describe nodes minikube | grep -A 10 "Allocated resources"

# 即時監控 Pod 資源（需要 metrics-server）
kubectl top pods -A

# 查看 ArgoCD Application 狀態
kubectl get application -n argocd
kubectl describe application <name> -n argocd

# 強制重啟 Deployment
kubectl rollout restart deployment <name> -n <namespace>

# 清除孤兒資源
kubectl get all -n <namespace>
kubectl delete <resource> <name> -n <namespace>
```
