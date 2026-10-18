---
type: concept
domain: tech
tags: [kubernetes, k8s, beginner, docker, container, minikube, pod, deployment, hands-on]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 入門第五章：第一個容器，與第一個 Pod

前面四章都在鋪路。這一章你要親手把東西跑起來——先用 Docker 跑一個容器，再用 Kubernetes 做同一件事，然後看出兩者的差別在哪。

**這一章請務必邊讀邊打。** 每個指令都設計成可以直接複製執行，而且會告訴你「你應該看到什麼」。看到的跟寫的不一樣，就是學習發生的地方。

## 容器是什麼

第一章講過那個問題：「在我電腦上跑得好好的」，換台機器就爆炸，因為環境不一樣。

容器的解法很直接：**把程式跟它需要的整個環境（函式庫、設定、甚至一個精簡的作業系統檔案）打包成一個檔案，到哪裡都跑同一份。**

常見的比喻是貨櫃：貨櫃裡裝什麼、怎麼擺，是貨主的事；港口只負責搬運標準尺寸的箱子。同理，容器裡是哪個語言、哪個版本，主機不用管，它只負責「執行容器」這件標準化的事。

比喻到此為止，因為容器有一個關鍵特性比喻表達不出來：**它不是虛擬機。** 虛擬機是模擬一整台電腦，裡面跑完整的作業系統，所以肥（動輒幾 GB）、慢（開機要一分鐘）。容器則是**共用主機的作業系統核心**，只是把檔案系統與可見範圍隔離開來——所以它小（幾十 MB）、快（啟動不到一秒）。

這個「共用核心」的設計是容器所有優缺點的根源，正文第 0 章會詳細講。現在你只要記住結論：**容器很輕，所以你可以在一台機器上跑幾十個；而且啟動快，所以「掛掉就重開一個」是可行的策略。** 這個特性直接決定了 K8s 的設計。

還有兩個名詞要分清楚，它跟第一章「程式 vs 程序」是同一個概念：

| 名詞 | 是什麼 | 類比 |
| --- | --- | --- |
| **映像（image）** | 打包好的唯讀檔案 | 食譜 / 程式檔案 |
| **容器（container）** | 由映像啟動起來、正在跑的實例 | 那鍋菜 / 程序 |

一個映像可以啟動很多個容器，就像一份食譜可以煮很多鍋。

## 準備環境

Windows 上裝 **Docker Desktop**（官網下載安裝，過程中會提示啟用 WSL2，照著做）。裝完之後打開 PowerShell 驗證：

```powershell
docker version
```

看到 Client 與 Server 兩段版本資訊就成功了。只看到 Client、Server 那段報錯，代表 Docker Desktop 沒啟動——去工作列打開它，等鯨魚圖示不再轉動。

## 跑起第一個容器

```powershell
docker run -d --name web -p 8080:80 nginx:1.25
```

打開瀏覽器輸入 `http://localhost:8080`，你應該看到 nginx 的歡迎頁。

**先別急著往下，把這行指令拆開看**，每個部分都對應到你前四章學的東西：

| 部分 | 意思 |
| --- | --- |
| `docker run` | 啟動一個容器 |
| `-d` | detached，背景執行（不加的話會佔住你的終端機） |
| `--name web` | 給它一個好記的名字 |
| `-p 8080:80` | **port 對應**：主機的 8080 → 容器裡的 80 |
| `nginx:1.25` | 用哪個映像，`:1.25` 是版本標籤 |

`-p 8080:80` 是第一章 port 概念的直接應用：容器裡的 nginx 聽 80，但那是容器自己的「房號」，外面看不到。這個參數在主機的 8080 開一扇門，轉進容器的 80。**這就是為什麼你連的是 8080 卻看到 nginx。**

順帶注意：你剛剛沒有安裝 nginx。Docker 自動去下載了打包好的 nginx 映像——**這就是容器解決的問題**：不必在自己機器上裝任何東西，也不會弄髒環境。

## 四個日常指令

```powershell
docker ps                    # 有哪些容器在跑
docker logs web              # 看它的輸出（重新整理網頁再看一次，會多幾行）
docker logs -f web           # 持續追蹤（Ctrl+C 離開）——第二章的 tail -f
docker exec -it web sh       # 進到容器裡面
```

最後一個特別值得玩。進去之後你會發現**這裡面是一個小小的 Linux**，第二章學的東西全部派上用場：

```sh
ls /                          # 看起來就是一個 Linux 根目錄
cat /etc/os-release           # 這是 Debian
ps aux                        # 只有 nginx，沒有你主機上那幾百個程序
cat /usr/share/nginx/html/index.html   # 剛剛看到的網頁
exit                          # 離開
```

`ps aux` 只看到 nginx 這件事很重要：**容器裡的程序看不到主機上其他程序**。這就是「隔離」的實際體感。

## 一堂重要的課：容器是可拋棄的

現在做一個實驗。進去改掉那個網頁：

```powershell
docker exec -it web sh
```

```sh
echo "<h1>Hello from inside</h1>" > /usr/share/nginx/html/index.html
exit
```

重新整理瀏覽器，看到你改的字了。接著把容器砍掉重來：

```powershell
docker rm -f web
docker run -d --name web -p 8080:80 nginx:1.25
```

重新整理——**你的修改不見了，又變回原本的歡迎頁**。

這不是 bug，這是容器最重要的性質：**容器是可拋棄的（ephemeral），寫在裡面的東西隨著容器消失。** 映像是唯讀的，容器只是在它上面加一層暫時的可寫層，容器一死，那層就沒了。

這條性質決定了後面所有設計：

- 要**保留**的資料必須放在容器外面（這就是之後的 Volume 與 PVC）
- **設定**不該寫死在映像裡，要從外面注入（這就是之後的 ConfigMap 與 Secret）
- 日誌不該寫進容器裡的檔案，要輸出到標準輸出讓外面收走
- 因為容器可拋棄，所以「有問題就砍掉重建」變成合理的修復手段——K8s 大量使用這個策略

## 做一個自己的映像

用別人的映像很方便，但你的程式需要自己打包。這靠一個叫 `Dockerfile` 的檔案。

建一個資料夾，裡面放兩個檔案：

`index.html`

```html
<h1>My First Container</h1>
<p>Built by me.</p>
```

`Dockerfile`（沒有副檔名）

```dockerfile
FROM nginx:1.25
COPY index.html /usr/share/nginx/html/index.html
```

兩行的意思是：**以官方 nginx 映像為基礎，把我的 index.html 蓋上去。**

```powershell
docker build -t my-web:1.0 .
docker run -d --name mine -p 8081:80 my-web:1.0
```

打開 `http://localhost:8081` 就會看到你的網頁。**你剛剛做出了一個可以送到任何機器上、行為完全一致的成品。**

注意最後那個 `.`——它是「建置上下文」，代表「用當前目錄的檔案來建」。忘記加它是新手第一天最常見的錯誤。

清場：

```powershell
docker rm -f web mine
```

## Kubernetes 出場

現在問題來了：你會跑容器了，為什麼還需要 K8s？

回到第一章那四件事。Docker 解決了「打包」與「跑起來」，但下面這些它都不管：

- 這個容器掛了，誰負責重開？
- 我要三份一起跑分擔流量，誰負責維持數量？
- 三份分別在不同機器上，使用者要連哪一個？
- 我要更新版本，怎麼做到不中斷服務？
- 一台機器不夠了，怎麼加機器並自動用上？

K8s 就是負責這些的。**它的核心心智模型只有一句話：你描述「你想要的狀態」，它負責讓現實變成那樣，並且持續維持。**

## 裝 minikube 並啟動

minikube 是在自己電腦上跑一個單機 K8s 的工具。

```powershell
winget install Kubernetes.minikube
winget install Kubernetes.kubectl
```

（裝完要關掉再重開 PowerShell，讓 PATH 生效。）

```powershell
minikube start --cpus=4 --memory=6g
kubectl get nodes
```

看到一個 `Ready` 的節點就成功了。這台「節點」其實是跑在你電腦上的一個容器或虛擬機——**你現在有一座（只有一台機器的）K8s 叢集了**。

## 第一個 Pod

**Pod** 是 K8s 裡的最小單位，你可以先簡單理解成「一個或多個容器的包裝」。實務上一個 Pod 通常就是一個容器。

建立 `pod.yaml`：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-first-pod
  labels:
    app: web
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
```

對照第四章學的骨架逐行看：`apiVersion` 說用哪版 API、`kind` 說這是 Pod、`metadata` 給它名字和標籤、`spec` 描述你要的內容——一個叫 nginx 的容器，用 `nginx:1.25` 映像，聽 80 port。

```powershell
kubectl apply -f pod.yaml
kubectl get pods
```

`kubectl apply` 的意思是「把這個願望送給 K8s」。過幾秒再 `get pods` 一次，`STATUS` 會從 `ContainerCreating` 變成 `Running`。

看看它：

```powershell
kubectl describe pod my-first-pod      # 詳細狀態與事件（排錯主力）
kubectl logs my-first-pod              # 容器輸出
kubectl exec -it my-first-pod -- sh    # 進去看看（跟 docker exec 一樣）
```

要用瀏覽器看到它：

```powershell
kubectl port-forward pod/my-first-pod 8080:80
```

打開 `http://localhost:8080`，nginx 頁面出現。（`port-forward` 是把本機的 port 暫時接到 Pod 上，只適合測試用。Ctrl+C 結束。）

## 「啊哈」時刻：Pod 自己不會復活

現在做一個關鍵實驗。開另一個 PowerShell 視窗，把 Pod 刪掉：

```powershell
kubectl delete pod my-first-pod
kubectl get pods
```

**它就這樣沒了，沒有任何東西把它救回來。**

這說明了一件重要的事：**Pod 本身沒有自我修復能力。** 直接寫 Pod 等於把容器交給命運。所以實務上幾乎不會直接寫 Pod——你需要一個「盯著它」的角色。

## 改用 Deployment

建立 `deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3 # 我要三份
  selector:
    matchLabels:
      app: web # 我管的是有這個標籤的 Pod
  template: # 每一份長這樣（就是上面那份 Pod 的內容）
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
```

```powershell
kubectl apply -f deployment.yaml
kubectl get pods
```

你會看到**三個** Pod，名字是 `web-xxxxx-yyyyy` 這種自動生成的形式。

現在再殺一個：

```powershell
kubectl delete pod <其中一個 Pod 的名字>
kubectl get pods
```

**幾秒之內，一個新的 Pod 自動長出來，數量回到三個。**

這就是 K8s 的核心：你說「我要三份」，它就持續維持三份。你殺掉一個、機器當掉、程式崩潰——它都會補回來。這個「持續比對願望與現實並修正」的迴圈叫做 **reconciliation loop（調和迴圈）**，是整個 K8s 的運作原理。

順便試試擴縮容與更新：

```powershell
kubectl scale deployment web --replicas=5     # 變五份
kubectl set image deployment/web nginx=nginx:1.26   # 換版本（滾動更新，不中斷）
kubectl rollout status deployment/web         # 看更新進度
kubectl rollout undo deployment/web           # 反悔，回上一版
```

**這四行指令背後的複雜度非常高**——要決定先開新的還是先關舊的、要確認新的健康了才關舊的、要能回退。但對你來說就是四行。這就是 K8s 的價值。

## 加上 Service：讓別人找得到

現在有三個 Pod，每個都有自己的 IP，而且**每次重建 IP 都會變**。使用者怎麼連？

答案是 **Service**——第三章那個「負載平衡 + 內部 DNS」的組合，在 K8s 裡的名字。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  selector:
    app: web # 找有這個標籤的 Pod
  ports:
    - port: 80 # Service 對外的 port
      targetPort: 80 # 容器實際聽的 port
```

```powershell
kubectl apply -f service.yaml
kubectl get svc
kubectl get endpointslice     # 它找到哪幾個 Pod
```

`endpointslice` 那行會列出三個 Pod 的 IP——**Service 靠標籤找到它們**。這是 K8s 內部最重要的連結機制：不是靠名字或 IP 綁定，而是靠標籤動態配對。Pod 換了、IP 變了都不影響，只要標籤還在。

驗證它能負載平衡：

```powershell
kubectl port-forward service/web-svc 8080:80
```

叢集內部的其他 Pod 則可以直接用 `http://web-svc` 連到它——第三章講的 DNS，在叢集裡由 CoreDNS 提供。

## Docker 與 kubectl 指令對照

你剛學的 kubectl 指令，幾乎都能在 docker 找到對應：

| 做什麼 | Docker | kubectl |
| --- | --- | --- |
| 看有什麼在跑 | `docker ps` | `kubectl get pods` |
| 看詳細狀態 | `docker inspect` | `kubectl describe pod <name>` |
| 看日誌 | `docker logs -f x` | `kubectl logs -f <pod>` |
| 進去裡面 | `docker exec -it x sh` | `kubectl exec -it <pod> -- sh` |
| 啟動 | `docker run` | `kubectl apply -f x.yaml` |
| 停掉 | `docker rm -f x` | `kubectl delete -f x.yaml` |
| 開 port 到本機 | `-p 8080:80` | `kubectl port-forward` |

最大的差別在**啟動**那一行：docker 是「命令式」（你叫它做一件事），kubectl apply 是「宣告式」（你描述想要的結果）。這個差異看起來只是寫法不同，實際上是 K8s 一切能力的來源——因為 K8s 隨時知道「你想要的樣子」，所以它能在現實偏離時自動修正。

## 清場

```powershell
kubectl delete -f deployment.yaml -f service.yaml
minikube stop        # 停掉叢集（保留資料，下次 minikube start 繼續）
# minikube delete    # 徹底刪掉，想從零開始時用
```

## 本章回顧

- 映像是唯讀的打包成品，容器是它跑起來的實例
- 容器不是虛擬機——共用主機核心，所以又小又快
- **容器是可拋棄的**：寫在裡面的東西會消失，所以資料要放外面、設定要從外面注入
- `Dockerfile` 兩三行就能做出自己的映像
- Pod 是 K8s 的最小單位，但**它自己不會復活**
- Deployment 維持你要的副本數，殺掉會自動補回來——這就是 reconciliation loop
- Service 用**標籤**動態找到 Pod，提供穩定的入口與負載平衡
- docker 是命令式、kubectl apply 是宣告式，這是 K8s 能自我修復的根本原因

## 自我檢查

1. `-p 8080:80` 兩個數字分別代表什麼？
2. 你改了容器裡的檔案，重建容器後不見了，為什麼？這帶來哪三個設計上的結論？
3. 直接 `kubectl apply` 一個 Pod，跟用 Deployment 包起來，差在哪？
4. Service 是怎麼知道要把流量送給哪些 Pod 的？
5. 「宣告式」跟「命令式」差在哪？為什麼這個差異重要？

最後一章講錯誤訊息——因為接下來你一定會遇到，而看得懂就不會慌。

## 連結

- [[intro-4-yaml-syntax]] — 上一章：YAML 語法
- [[intro-6-error-messages]] — 下一章：錯誤訊息白話翻譯
- [[00-docker-foundations]] — 正文：容器在 kernel 層到底是什麼
- [[04-workloads]] — 正文：Pod、Deployment 與其他工作負載的完整說明
- [[26-lab-drills]] — 附錄 D：讀完正文後的動手實驗
- [[k8s-mastery]] — 教材總目錄（含各階段的閱讀路徑）
