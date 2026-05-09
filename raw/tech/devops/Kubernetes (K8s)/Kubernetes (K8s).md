---
tags: [devops, kubernetes, k8s]
---

> 關聯：[[kubernetes]]

# Kubernetes (K8s)

# 參考資料

參考資料: https://chengweihu.com/kubernetes-tutorial-1-pod-node/#kubernetes-%E5%9B%9B%E5%85%83%E4%BB%B6

[https://github.com/seifrajhi/Kubernetes-practical-exercises-Hands-on](https://github.com/seifrajhi/Kubernetes-practical-exercises-Hands-on)

# K8s 基本概念

> K8S 提供一個平台，以較高層次的抽象化去自動化操作與管理容器們，以部署多個容器到多台機器上並監測管理這些容器的狀態
> 
- Deployment：部署多容器到多設備
- Scaling：容器隨服務 Loading 調整擴展
- Management：偵測並重啟故障容器

# **K8s基本四元件**

![圖： Cluster 簡易版 (只有一個Master)](Kubernetes%20(K8s)/image.png)

圖： Cluster 簡易版 (只有一個Master)

## Pod (應用環境)

- Pod 是運作的**最小單位**，對應一個 Application (例如: API Server)
- 每個 Pod 都有對應一個 `yaml` 檔，也就是屬於這個 Pod 的身分證
- 每個 Pod 通常只有一個 Container，但也可以有多個 Container
- 同個 Pod 中的 Containers 共享相同資源及網路，彼此透過 local port number 溝通

## **Worker Node (執行設備)**

- Node是運作的**最小硬體單位**，對應一台設備
    - 設備包含：電腦或是虛擬機
    - 如 AWS 上的一台 EC2 或 GCP 上的一台 Computer Engine
- 每個 Node 都有三個組件：`kubelet`、`kube-proxy`、`Container Runtime`

<aside>
💡

*小提醒：在 Worker Node 與 Master Node 的組件部分，因為 Kubernetes 本身其實都抽象的很好，所以在 Kubernetes 「基礎的」使用上如何不了解這些組建也不會有非常大的影響。*

</aside>

**kubelet(管理)**

- 負責管理該 Node 上的所有 Pods 的狀態並負責與 Master 溝通

**kube-proxy (傳訊)**

- 負責更新 Node 的 iptables，讓 Kubernetes 中不在該 Node 的其他物件可以得知該 Node 上所有 Pods 的最新狀態

**Container Runtime (執行)**

- 該 Node 真正負責容器執行的程式
- 以 Docker 容器為例，其對應的 Container Runtime 就是 Docker Engine

## **Master Node (**指揮中心**)**

- 可理解成一個特化的 Node 負責管理所有其他 Node。
- 一個 Master Node 中有四個組件：`kube-apiserver`、`etcd`、`kube-scheduler`、`kube-controller-manager`

**kube-apiserver (溝通的橋樑)**

- 管理整個 K8s 所需 API 的接口（Endpoint），例如從 Command Line 下 kubectl 指令就會把指令送到這裏
- 負責 Node 之間的溝通橋樑，每個 Node 彼此不能直接溝通，必須要透過 apiserver 轉介
- 負責 K8s 中的請求的身份認證與授權

**etcd (備份還原資料)**

- 用來存放 Kubernetes Cluster 的資料作為備份，當 Master 因為某些原因而故障時，可以透過 etcd 還原 Kubernetes 的狀態

**kube-controller-manager**

- 負責管理並運行 K8s controller 的組件，簡單來說 controller 就是 K8s  裡一個個負責監視 Cluster 狀態的 Process，
    - 例如：`Node Controller`、`Replication Controller`
- 這些 Process 會在 Cluster 與預期狀態（desire state）不符時嘗試更新現有狀態（current state）。例如：現在要多開一台機器以應付突然增加的流量，那我的預期狀態就會更新成 N+1，現有狀態為 N，這時相對應的 controller 就會想辦法多開一台機器
- controller-manager 的監視與嘗試更新也都需要透過訪問 kube-apiserver 達成

**kube-scheduler**

- 整個 Kubernetes 的 Pods 調度員，scheduler 會監視新建立但還沒有被指定要跑在哪個 Node 上的 Pod，並根據每個 Node 上面資源規定、硬體限制等條件去協調出一個最適合放置的 Node 讓該 Pod 跑

## **Cluster**

K8s 中多個 Node 與 Master 的集合。基本上可以想成在同一個環境裡所有 Node 集合在一起的單位。

- 通常一個 Cluster 中其實會有多個 Master 作為備援
- `Kubectl` 是 K8s 操作 Cluster 的 Command Line 工具

# **基本運作**

通常一個 Cluster 中其實會有多個 Master 作為備援，此處簡化一個Master 來說明。

要部署一個新的 Pod 到 Cluster 時，要先透過 User Command（kubectl）輸入建立 Pod 的對應指令，指令會經過一層確認使用者身份的認證後，傳遞到 Master Node 中的 API Server，API Server 會把指令備份到 etcd 。

接下來 controller-manager 會從 API Server 收到需要創建一個新的 Pod 的訊息，並檢查如果資源許可，就會建立一個新的 Pod。

最後 Scheduler 在定期訪問 API Server 時，會詢問 controller-manager 是否有建置新的 Pod，如果發現新建立的 Pod 時，Scheduler 就會負責把 Pod 配送到最適合的一個 Node 上面。

<aside>
💡

上面基本運作實際上在操作時只要輸入一行 kubectl 指令後， K8s 就會自動完成後續的動作。

</aside>

# **如何建立一個 Pod**

## 準備：建立程式 Image

1. 決定一個要在 Pod 中運行的 Image 程式
2. 把這個程式打包成 Image 後上傳到 DockerHub 上
    1. 可以試著自己透過 `docker build -t` 先建立好 docker image
    2. 再透過 `docker push` 上傳到 Dockerhub

## **撰寫 Pod 的身分證 (.yaml)**

```yaml
apiVersion: v1
	kind: Pod
	metadata:
		name: kubernetes-demo-pod
		labels:
			app: demoApp
	spec:
		containers:
		- name: kubernetes-demo-container
			 image: hcwxd/kubernetes-demo
			 ports:
			   - containerPort: 3000
```

**apiVersion (**元件版本號)

**kind (**元件屬性)

- 常見有 `Pod`、`Node`、`Service`、`Namespace`、 `ReplicationController` 等

**metadata**

- **name -** 指定該 Pod 的名稱
- **labels -** 指定該 Pod 的標籤，這裡暫時幫它上標籤為 `app: demoApp`

**spec**

- **containers.name** 指定運行出的 Container 的名稱
- **containers.image** 指定 Container 要使用哪個 Image，這裡會從 DockerHub 上搜尋
- **containers.ports** 指定該 Container 有哪些 port number 是允許外部資源存取

## **透過 kubectl 建立 Pod**

有了身份證後就可以透過 kubectl 指令來建立 Pod，看到 `pod/kubernetes-demo-pod created` 的字樣就代表成功建立第一個 Pod 了。

- `-f` : 全名 `--filename`

```bash
> kubectl create -f kubernetes-demo.yaml
pod/kubernetes-demo-pod created
```

可以再透過指令看到運行中的 Pod：

```bash
> kubectl get pods
NAME                  READY   STATUS    RESTARTS   AGE
kubernetes-demo-pod   1/1     Running   0          60s
```

## **連線到 Pod 的服務資源**

- 建立好Pod 之後，在 Pod 中所指定的 port，跟 Localhost 的 port 是不相通的。
- 必須還要透過 `kubectl port-forward`，把兩端的 port 做 mapping。

```bash
kubectl port-forward kubernetes-demo-pod 3000:3000
```

- 做好 mapping 後，再打開瀏覽器的`localhost:3000` ，就可正常運行

# **進階三元件**

> Service、Ingress、Deployment 是要建構可運行服務的基本元件
> 

## Service (管一群 Pod 如何連線)

- `port-forward` 是用來設定「單個 Pod 」如何被連線存取服務用的指令
- `Service` 是用來定義「一群 Pod 」如何被連線存取服務用的元件

```yaml
apiVersion: v1
 kind: Service
 metadata:
   name: my-service
 spec:
   selector:
     app: demoApp
   type: NodePort
   ports:
     - protocol: TCP
       port: 3001
       targetPort: 3000
       nodePort: 30390
```

**spec.selector**

- selector 用於決定 Service 的連線規則適用在哪一群 Pods，`app` 要寫 Pod 的 Label
- 在寫建立 Pod 的 ymal 時，會幫 Pod 上 `label`，這時就可以透過 `app:demoApp`，去找到所有 label 的 app 屬性是 `demoApp` 的 Pods

**spec.ports**

- targetPort 指定 Pod 上允許外部資源存取 Port Number
- port 指定 Pod 上的 targetPort 要 mapping 到 Service 中 ClusterIP 中的哪個 port
- - nodePort 指定 Pod 上的 targetPort 要 mapping 到 Node 上的哪個 port

接下來先重新建立 Pod

```yaml
kubectl create -f kubernetes-demo.yaml
```

透過 `service.yaml` 來建立 Service 元件

```yaml
kubectl create -f service.yaml
```

然後可以取得新建立 Service 的資料

```yaml
> kubectl get services
NAME       TYPE      CLUSTER-IP     EXTERNAL-IP PORT(S)          AGE
my-service NodePort  10.110.237.205 <none>      3001:30391/TCP   60s
```

有了建立好的 Service 後，可以透過兩種方式連線 Pod 的服務資源。首先，要從外部連線到 Pod 資源服務，必須要先有 Kubernetes Cluster（在這邊是 minikube）對外開放的 IP。

**方法一：瀏覽器查看連線**

開瀏覽器，輸入上面的 ip 加上在 `service.yaml` 檔指定的 `nodePort`，在這邊是 `192.168.99.100:30390`。

```bash
> minikube ip
192.168.99.100
```

**方法二：從 minikube 裡面連線**

直接從 minikube 裡面連線到 Pod 

```bash
# curl <CLUSTER-IP>:<port>
> minikube ssh
> curl 10.110.237.205:3001
```

<aside>
💡

`curl <CLUSTER-IP>:<port>
CLUSTER-IP` 是用 `kubectl get services` 得到 Service 的 IP
`port` 是在 `yaml` 檔指定的 `port`
在這邊合起來就是 `10.110.237.205:3001`

</aside>

## Deployment

- 把一個 Pod 做橫向擴展，複製多個相同的 Pod 在 Cluster 中同時提供服務
- 監控如果有 Pod 當機就要重新把它啟動

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: demoApp
    spec:
      containers:
        - name: kubernetes-demo-container
          image: hcwxd/kubernetes-demo
          ports:
            - containerPort: 3000
  selector:
    matchLabels:
      app: demoApp
```

spec

- replicas 指定要建立多少個相同的 Pod，在這邊給的數字是所謂的 Desire State，當 Cluster 運行時如果 Pod 數量低於此數字，Kubernetes 就會自動增加 pod，反之就會關掉 Pod
- template 指定這個 Deployment 建立的 Pod 們統一的設定，包括 metadata 以及這些 Pod 的 Containers，這邊就沿用之前建立 Pod 的設定
- selector 指定這個 Deployment 的規則要適用到哪些 Pod，在這邊就是指定在 template 中指定的 labels

接下來就可以透過指令 `kubectl create -f deployment.yaml`建立好 Deployment，這時可以查看 Deployment 有沒有被建立好 

```yaml
> kubectl get deploy
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
my-deployment   3/3     3            3           60s
```

接著再看 Pod 們有沒有乖乖按照 Deployment 建立

```yaml
> kubectl get pods
NAME                             READY   STATUS    RESTARTS   AGE
my-deployment-5454f687cd-bxjfz   1/1     Running   0          60s
my-deployment-5454f687cd-gszbr   1/1     Running   0          60s
my-deployment-5454f687cd-k6zfv   1/1     Running   0          60s
```

這邊可以看到三個 Pod 都被建立好了，就成功做到了 Pod 的橫向擴展。

而除了 Pod 的橫向擴展外，Deployment 的另外一個好處就是可以做到無停機的系統升級（Zero Downtime Rollout）。也就是說，當要更新Pod 時，Kubernetes 並不會直接砍掉所有的 Pod，而是會建立新的 Pod，等新的 Pod 開始正常運行後，再來取代舊的 Pod。

舉例來說，假設現在想要更新 Pod 對外的 Port，可以先透過指令

```yaml
kubectl edit deployments my-deployment
```

接著會看到 Yaml 檔

```yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "2"
  creationTimestamp: "2019-04-26T04:18:26Z"
  generation: 2
  labels:
    app: demoApp
  name: my-deployment
  namespace: default
  resourceVersion: "328692"
  selfLink: /apis/extensions/v1beta1/namespaces/default/deployments/my-deployment
  uid: 56608fb5-67da-11e9-933f-08002789461f
spec:
  progressDeadlineSeconds: 600
  replicas: 3
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: demoApp
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: demoApp
    spec:
      containers:
        - image: hcwxd/kubernetes-demo
          imagePullPolicy: Always
          name: kubernetes-demo-container
          ports:
            - containerPort: 3000
              protocol: TCP
          resources: {}
          terminationMessagePath: /dev/termination-log
          terminationMessagePolicy: File
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      terminationGracePeriodSeconds: 30
```

把其中 `containerPort: 3000` 改成 `3001` 後儲存，Kubernetes 就會開始進行更新。這時繼續用指令 `kubectl get pods` 就會看到

```yaml
NAME                          READY STATUS            RESTARTS   AGE
my-deployment-5454f687cd-bxjf 1/1   Running           0          60s
my-deployment-5454f687cd-gszb 1/1   Terminating       0          60s
my-deployment-5454f687cd-k6zf 1/1   Running           0          60s
my-deployment-78dc8dcb89-5927 0/1   ContainerCreating 0          1s
my-deployment-78dc8dcb89-dwtl 1/1   Running           0          5s
```

從上面可以看到，Kubernetes 會永遠保持有 3 個 Pods 在正常運作，如果有新的 Pod 還在 `ContainerCreating` 的階段時，他還不會關掉對應要被取代的 Pod。

而在過一段時間輸入同樣 `kubectl get pods` 指令可以看到

```yaml
NAME                            READY   STATUS        RESTARTS   AGE
my-deployment-5454f687cd-bxjf   1/1     Terminating   0          60s
my-deployment-5454f687cd-gszb   1/1     Terminating   0          60s
my-deployment-5454f687cd-k6zf   1/1     Terminating   0          60s
my-deployment-78dc8dcb89-5927   1/1     Running       0          11s
my-deployment-78dc8dcb89-7b7h   1/1     Running       0          7s
my-deployment-78dc8dcb89-dwtl   1/1     Running       0          15s
```

三個新的 Pod 都被成功部署上去用來取代舊的 Pod 了，靠著這樣的機制，就可以確保系統在更新的時候不會有服務暫時無法使用的狀況。

這時可以透過指令，看到目前更改過的版本

```bash
> kubectl rollout history deployment my-deployment
deployment.extensions/my-deployment
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

從上面可以看出來，目前有兩個版本，如果發現版本 2 的程式有問題，想要先讓服務先恢復成版本 1 的程式（Rollback）時，還可以透過指令

```yaml
kubectl rollout undo deploy my-deployment
```

讓 Pod 都恢復成版本 1。甚至之後如果版本變的較多後，也可以指定要 Rollback 到的版本

```yaml
kubectl rollout undo deploy my-deployment **--to-revision=2**
```

## **Ingress (Service 的管理)**

Service 用來定義「一群 Pod 要如何被連線及存取」的元件。但在 Service 中，將每個 Service 元件對外的 port number 跟 Node 上的 port number 做 mapping，這樣在 Service 變多時，port number 以及分流規則的管理變得相當困難。

![image.png](Kubernetes%20(K8s)/image%201.png)

而 Ingress 可以透過 HTTP/HTTPS，在眾多的 Service 前搭建一個 reverse-proxy。這樣 Ingress 可以幫助**統一對外的 port number**，並且根據 hostname 或是 pathname 決定封包要轉發到哪個 Service 上

![image.png](Kubernetes%20(K8s)/image%202.png)

Ingress 這項服務是由 `Ingress Resources`、`Ingress Server`、`Ingress Controller` 構成。

- Ingress Resources：定義 Ingress 的身分證 (YAML)
- Ingress Server ：實體化用來接收 HTTP/HTTPS 連線的網路伺服器。
    - 實際上 Ingress Server 有各式各樣的實作，就如同市面上的 Web Server 琳瑯滿目一樣。
- Ingress Controller：一個可以把定義好的 Ingress Resources 設定轉換成特定 Ingress Server 實作的角色
    - 舉例來說，Kubernetes 由官方維護的兩種 Ingress Controller 就有 [ingress-gce](https://github.com/kubernetes/ingress-gce/blob/master/README.md) 跟 [ingress-nginx](https://github.com/kubernetes/ingress-nginx/blob/master/README.md)，分別可以對應轉換成 GCE 與 Nginx。
    - 也有其他非官方在維護的 Controller，詳細的列表可見官網的 [additional-controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/#additional-controllers)。

接下來要來試著建立一個 Ingress 物件去根據 hostname 轉發封包到不同的 Pod 上面。

所以第一步，要用 Deployment 建立好幾個不同的 Pod。在這邊直接透過準備好的兩個 Image 來建立其中的 Container，blue-whale 這個 Image 裡的程式會監聽 3000 port 然後在瀏覽器上被存取時會吐出藍色的鯨魚，purple-whale 則會吐出紫色的鯨魚。

```yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: blue-nginx
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: blue-nginx
    spec:
      containers:
        - name: nginx
          image: hcwxd/blue-whale
          ports:
            - containerPort: 3000
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: purple-nginx
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: purple-nginx
    spec:
      containers:
        - name: nginx
          image: hcwxd/purple-whale
          ports:
            - containerPort: 3000
```

接著就可以透過 `kubectl create -f deployment.yaml` 建立好 Pod。

```bash
> kubectl create -f deployment.yaml
NAME                           READY   STATUS    RESTARTS  AGE
blue-nginx-6b68c797c7-28tkz    1/1     Running   0         60s
blue-nginx-6b68c797c7-8ww8l    1/1     Running   0         60s
purple-nginx-84854fd7c-8g4nl   1/1     Running   0         60s
purple-nginx-84854fd7c-tmrbs   1/1     Running   0         60s
```

建立好了 Pod 們後，接下來就要建立這些 Pod 對外的各自 Service，在這邊會把各至 Container 上的 3000 port 全部都轉到 80 port 上。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: blue-service
spec:
  type: NodePort
  selector:
    app: blue-nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: purple-service
spec:
  type: NodePort
  selector:
    app: purple-nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
```

透過 `kubectl create -f service.yaml` 建立好 Pod。

```yaml
NAME            TYPE      CLUSTER-IP      EXTERNAL-IP  PORT(S)
blue-service    NodePort  10.111.192.164  <none>       80:30492/TCP
purple-service  NodePort  0.107.21.77     <none>       80:32086/TCP
```

最後就可以來建立 Ingress 了！

在這邊 Ingress 只有很簡單的規則，他會把所有發送到 `blue.demo.com` 的封包交給 service `blue-service` 負責，而根據上面 `service.yaml` 的定義，他會再轉交給 `blue-nginx` 這個 Pod。而發送給 `purple.demo.com` 則會轉交給 `purple-nginx`。

在這邊，要先記得使用指令 `minikube addons enable ingress` 來啟用 minikube 的 ingress 功能。

接著，就來撰寫 ingress 的身分證。

```yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: web
spec:
  rules:
    - host: blue.demo.com
      http:
        paths:
          - backend:
              serviceName: blue-service
              servicePort: 80
    - host: purple.demo.com
      http:
        paths:
          - backend:
              serviceName: purple-service
              servicePort: 80
```

透過 `kubectl create -f ingress.yaml` 來建立 ingress 物件。並使用 `kubectl get ingress` 來查看 ingress 狀況：

```yaml
NAME   HOSTS                           ADDRESS     PORTS   AGE
web    blue.demo.com,purple.demo.com   10.0.2.15   80      60s
```

接下來要來測試 ingress 有沒有自動轉發。因為 Cluster 實際上對外的 ip 都是透過指令 `minikube ip` 會看到的 `192.168.99.100`，這樣要怎麼同時讓這個 ip 可以是設定規則中的 `blue.demo.com` 以及 `purple.demo.com` 呢？

因為知道在 DNS 解析網址時，會先查找本機上 `/etc/hosts` 後才會到其他 DNS Server 上尋找。所以可以透過一個小技巧，在本機上把 `blue.demo.com` 以及 `purple.demo.com` 都指向 `192.168.99.100`。透過指令或是透過 `sudo vim /etc/hosts` 手動加上這兩條規則，就成功搞定 DNS 可以來測試了。

```yaml
echo 192.168.99.100   blue.demo.com  >> /etc/hosts
echo 192.168.99.100   purple.demo.com >> /etc/hosts
```

接下來打開瀏覽器，輸入 `blue.demo.com` 就可以得到熟悉的藍色小鯨魚，然後輸入 `purple.demo.com` 就可以得到紫色小鯨魚囉！

# **Helm 介紹與建立 Chart**

假設有一個複雜的服務，裡面同時包含了很多種YAML設定檔時，如何同時做好版本控制、管理、更新這些設定檔就變得不太容易，且要快速部署這個含有多個設定檔的服務也變得困難。因此 Helm 就是一個用來解決上述問題的工具。

Helm 就是一個管理設定檔的工具，把 Kubernetes 一個服務中各種元件裡的 `yaml` 檔統一打包成一個叫做 `chart` 的集合，然後透過給參數的方式，去同時管理與設定這些 `yaml` 檔案。

## **Chart 的運作方式**

可以到 Wordpress chart 的 [Github](https://github.com/helm/charts/tree/master/stable/wordpress) 上觀察這個 Chart 的檔案結構，或是透過指令來建立一個最簡單的 Chart

```bash
> helm create helm-demo
```

```
.
├── Chart.yaml
├── charts
├── templates
│   ├── deployment.yaml
│   ├── ingress.yaml
│   └── service.yaml
└── values.yaml
```

`Chart.yaml`

- 定義了這個 Chart 的 Metadata，包括 Chart 的版本、名稱、敘述等

`charts`

- 在這個資料夾裡可以放其他的 Chart，這裡稱作 SubCharts

`templates`

- 定義這個 Chart 服務需要的 Kubernetes 元件。但並不會把各元件的參數寫死在裡面，而是會用參數的方式代入

`values.yaml`

- 定義這個 Chart 的所有參數，這些參數都會被代入在 templates 中的元件。
    - 定義 `nodePorts` 給 `service.yaml`
    - 定義 `replicaCount` 給 `deployment.yaml`
    - 定義 `hosts` 給 `ingress.yaml` 等等

<aside>
💡

從上面的檔案結構可以看到，透過編輯 `values.yaml`，就可以對所有的 `yaml` 設定檔做到版本控制與管理。並透過 install / delete 的方式一鍵部署 / 刪除。

</aside>

## **如何建立自己的 Chart**

目標是要透過 `deployment`、`service`、`ingress` 來讓使用者在輸入 `blue.demo.com` 時可以得到一隻小鯨魚。而首先，我們一樣輸入指令，之後就看一下在 `ingress` 章節有使用過的 `yaml` 檔們。

```bash
> helm create helm-demo
```

```yaml
apiVersion: extensions/v1beta1
 kind: Deployment
 metadata:
   name: blue-nginx
 spec:
   replicas: 2
   template:
     metadata:
       labels:
         app: blue-nginx
     spec:
       containers:
         - name: nginx
           image: hcwxd/blue-whale
           ports:
             - containerPort: 3000
```

```yaml
apiVersion: v1
 kind: Service
 metadata:
   name: blue-service
 spec:
   type: NodePort
   selector:
     app: blue-nginx
   ports:
     - protocol: TCP
       port: 80
       targetPort: 3000
```

```yaml
apiVersion: extensions/v1beta1
 kind: Ingress
 metadata:
   name: web
 spec:
   rules:
     - host: blue.demo.com
       http:
         paths:
           - backend:
               serviceName: blue-service
               servicePort: 80
```

然後就可以嘗試來把上述 `yaml` 檔中可以作為參數的部分抽取出來，在這邊為了降低複雜度，只簡單挑幾個參數出來，然後我們就可以把這些參數寫到 `values.yaml` 中。

```yaml
replicaCount: 2
 
 image:
   repository: hcwxd/blue-whale
 
 service:
   type: NodePort
   port: 80
 
 ingress:
   enabled: true
 
   hosts:
     - host: blue.demo.com
       paths: [/]
```

把參數提取出來後，就來依樣畫葫蘆地把 `template` 中其他三個 `yaml` 檔寫成可以接受參數的方式：

```yaml
apiVersion: apps/v1
 kind: Deployment
 metadata:
   name: {{ include "value-helm-demo.fullname" . }}
 spec:
   replicas: {{ .Values.replicaCount }}
   selector:
     matchLabels:
       app: {{ include "value-helm-demo.fullname" . }}
   template:
     metadata:
       labels:
         app: {{ include "value-helm-demo.fullname" . }}
     spec:
       containers:
         - name: {{ .Chart.Name }}
           image: '{{ .Values.image.repository }}'
           ports:
             - containerPort: 3000
```

```yaml
apiVersion: v1
 kind: Service
 metadata:
   name: {{ include "value-helm-demo.fullname" . }}
 spec:
   type: {{ .Values.service.type }}
   ports:
     - port: {{ .Values.service.port }}
       targetPort: 3000
       protocol: TCP
   selector:
     app: {{ include "value-helm-demo.fullname" . }}
```

```yaml
{{- if .Values.ingress.enabled -}}
 {{- $fullName := include "value-helm-demo.fullname" . -}}
 apiVersion: extensions/v1beta1
 kind: Ingress
 metadata:
   name: {{ $fullName }}
 spec:
   rules:
   {{- range .Values.ingress.hosts }}
     - host: {{ .host | quote }}
       http:
         paths:
         {{- range .paths }}
           - backend:
               serviceName: {{ $fullName }}
               servicePort: 80
         {{- end }}
   {{- end }}
 {{- end }}
```

寫好後，我們就可以來一鍵部署我們的這三份檔案囉。我們可以直接在 `/helm-demo` 資料夾下輸入指令

```yaml
helm install .

NAME:   gilded-peacock
LAST DEPLOYED: Mon May  6 16:31:27 2019
NAMESPACE: default
STATUS: DEPLOYED

RESOURCES:
==> v1/Deployment
NAME                      READY  UP-TO-DATE  AVAILABLE  AGE
gilded-peacock-helm-demo  0/2    2           0          0s

==> v1/Pod(related)
NAME                                READY STATUS          RESTARTS
gilded-peacock-helm-demo-5fc5964759 0/1   ContainerCreating  0
gilded-peacock-helm-demo-5fc5964759 0/1   ContainerCreating  0

==> v1/Service
NAME                      TYPE      CLUSTER-IP     EXTERNAL-IP  PORT(S)
gilded-peacock-helm-demo  NodePort  10.106.164.53  <none>       80:30333/TCP

==> v1beta1/Ingress
NAME                      HOSTS          ADDRESS  PORTS
gilded-peacock-helm-demo  blue.demo.com  80       0s

NOTES:
1. Get the application URL by running these commands:
  http://blue.demo.com/
```

部署成功後顯示的 `NAME: gilded-peacock` 就是這個 Chart 部署後的名稱囉（在 Helm 中稱部署出去的這個實體為 `release`）。我們可以再透過指令列出目前所有的 `releases`。接下來可以用 `kubectl get all` 來看到目前的 kubernetes 狀況，這邊就可以看到所指定的資源都有按照 chart 的配置建立起來囉，所以打開 `blue.demo.com` 就可以看到一隻我們透過 Helm 實際部署出的小鯨魚。

```yaml
> helm list
NAME                                    READY STATUS  RESTARTS
pod/gilded-peacock-helm-demo-5fc5964759 1/1   Running 0
pod/gilded-peacock-helm-demo-5fc5964759 1/1   Running 0

NAME                               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/gilded-peacock-helm-demo   NodePort    10.106.164.53   <none>        80:30333/TCP

NAME                                     READY UP-TO-DATE AVAILABLE
deployment.apps/gilded-peacock-helm-demo 2/2   2          2

NAME                                                DESIRED CURRENT
replicaset.apps/gilded-peacock-helm-demo-5fc5964759 2       2
```

以上，我們就完成 Helm 的實際部署囉！

而其他常用的 Helm 指令還有：

```yaml
helm delete --purge RELEASE_NAME
```

刪除一個 release（`--purge` 這個 flag 可以把該 `RELEASE_NAME` 釋放出來供之後重複使用）。

```yaml
helm upgrade RELEASE_NAME CHART_PATH
```

如果有更新 Chart 的檔案時，可以透過 upgrade 去更新對應的 Release。

```yaml
helm lint CHART_PATH
```

檢查你的 Chart 檔案有沒有錯誤的語法。

```yaml
helm package CHART_PATH
```

打包並壓縮整個 Chart 資料夾的檔案。

# **kubectl 額外補充**

## **簡寫**

覺得每次下指令都要打 `kubectl` 很花時間的話，可以透過 alias 來節省時間，例如設定 `alias kbs=kubectl` 。

kubectl 中的各項資源的名稱其實也都有內建的簡寫，可以透過指令 `kubectl api-resources`

去看到各個資源的簡寫，例如 deployments 可以簡寫成 `deploy`、services 簡寫成 `svc` 等。

## **auto-complete**

覺得 kubectl 的指令沒有 auto-complete 很痛苦的話可以參考[官網](https://kubernetes.io/docs/reference/kubectl/cheatsheet/#kubectl-autocomplete)的教學。

像是如果使用 zsh 的話，就可以透過指令

`echo "if [ $commands[kubectl] ]; then source <(kubectl completion zsh); fi" >> ~/.zshrc`

來啟用 kubectl 的 auto-complete

## **create vs apply**

在之前提到透過 `yaml` 建立資源時，我們都用了 `kubectl create -f`。但其實也可以使用 `kubectl apply -f` 達成建立與更新資源，雖然在單純建立的使用情景上沒有差別，但其它用法上的差別可見 [kubectl apply vs kubectl create](https://stackoverflow.com/questions/47369351/kubectl-apply-vs-kubectl-create)。

一般 `kubectl apply` 會把整個設定存在 annotation 裡（叫 `last-applied-configuration`），之後用來比對差異。

## **server-side**

整句意思：**用 server-side 模式，把 ArgoCD 的官方安裝 yaml 套用到 argocd namespace**。

```bash
kubectl apply --server-side -n argocd -f [https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml](https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml)
```

server-side 與 client-side 是 `kubectl apply` 的模式。

**一般 apply（client-side）**：

- kubectl 在本機計算「哪些東西變了」
- 把整份設定存成 annotation 當紀錄
- 再送給 K8s

**`--server-side` apply**：

- kubectl 直接把設定送給 K8s API server
- 由 API server 自己計算哪些東西變了
- 不需要存 annotation，所以沒有大小限制

## ArgoCD 的安全設計。

**Project** 是 ArgoCD 的隔離單位，用於控制：

- 哪些 Git repo 可以當來源
- 哪些 K8s namespace 可以部署到
- 哪些 namespace 可以建立 Application 資源

**預設行為**：Application 只能建在 `argocd` namespace 裡。

**你的情況**：vault-app.yaml、harbor-app.yaml 的 metadata 是 `namespace: infra`，也就是 Application 資源放在 `infra` namespace，ArgoCD 看到就說「不認識這個 namespace 來的 app，拒絕」。

之前在 start.bat 加的 `application.namespaces: infra` 是告訴 ArgoCD「去監控 infra namespace」，但 default project 還需要另外說「允許來自 infra 的 app 使用我」，兩個設定要同時有才行。

整句意思：**讓 ArgoCD default project 接受 `infra` namespace 裡建立的 Application**。

```bash
kubectl patch appproject default -n argocd --type merge -p "{\"spec\":{\"sourceNamespaces\":[\"infra\"]}}"
```

| `kubectl patch` | 更新現有資源的部分欄位 |
| --- | --- |
| `appproject default` | 目標是名為 `default` 的 AppProject 資源 |
| `-n argocd` | 在 `argocd` namespace 裡 |
| `--type merge` | 用 merge patch 方式（只更新指定欄位，不覆蓋整個資源） |
| `-p "..."` | patch 內容（JSON 格式） |
| `spec.sourceNamespaces` | 允許哪些 namespace 裡的 Application 使用這個 project |
| `["infra"]` | 加入 `infra` namespace |

# 其他

**etcd**
K8s 的資料庫，儲存所有 cluster 狀態（deployments、services、secrets、configmaps 等）。minikube 把 etcd 跑在 control plane 裡，資料存在 minikube 的虛擬機內部，不是 PVC。

**PVC（PersistentVolumeClaim）**
應用程式申請的持久化儲存空間。你的架構裡：

- `data-vault-0` → Vault 的資料
- `data-harbor-database-0` → Harbor 的資料庫
- `harbor-registry` → Harbor 儲存的 images

兩者的差別：

|  | etcd | PVC |
| --- | --- | --- |
| 存什麼 | K8s 資源設定 | 應用程式資料 |
| 誰用 | K8s 系統 | Pod（Vault、Harbor 等） |
| 存在哪 | minikube VM 內部 | Docker WSL2 的 ext4.vhdx |