---
tags:
  - k8s
source: https://www.youtube.com/watch?v=RUjcGn2YeVo
---
# 部屬會遇到的問題

傳統上，系統需要多少個節點我們就準備多少台電腦主機，再把相對應的應用程式給部署上去。
然而，其中的一大問題就是系統資源的分配不均與浪費，畢竟某些應用程式可能只需要少少的運算資源，卻獨佔了整台機器。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621125606161.png]]

同時，當某幾台機器掛點又或者使用量超過系統負荷時也都需要手動去進行檢查維護。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621125636352.png]]

這零零總總雜七雜八的瑣事如果只是幾台機器也就算了，然而當規模持續擴大，同時需要部署或管理成千上萬台機器和應用程式時就會變得很混亂，整天光處理這些瑣事就飽了，大概也不用做正事了。

為了解決這些問題，Google 提出一套名為 Kubernetes (K8s) 的部署管理系統，把部署與管理應用程式的問題給虛擬化、自動化，同時也兼具系統資源的分配管理。


今天帶你略懂這套強大的部署管理系統 Kubernetes 與 Helm 部屬文件寫法說明。

Kubernetes 是希臘文舵手的意思，意味著引導一個個的貨櫃容器 container，到他們應該去的地方去，由於 Kubernetes 字母太多、也常被簡稱為 K8s。

# K8s Concept
在 K8s 的**實體架構**當中，許多機器會被組織成一個 Cluster，其中的每一台機器都會被視為 Cluster 當中的一個 Node，少部分的 Node 負責調度和管理整個 cluster 的資源，我們稱這類型的 Node 為 Control Plane，其餘的 Node 則接收來自 Control Plane 的調度指令，用來實際運行應用程式。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621130257275.png]]


在 K8s 的**抽象概念**上，Cluster 就是一個虛擬的資料中心，這個資料中心有自己的內網串聯運行著應用程式的虛擬機器，透過虛擬的內網與虛擬的對外接口路由器，把外部流量導向相對應的虛擬機器去做處理，處理完再把結果回傳。
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621130355764.png]]

對於一個剛入門的新手來說，實體架構和抽象概念之間常會造成混淆，因此我們將以略為簡化的方式，同時搭**配實體架構**與**抽象概念**去做說明。

當我們想要在 cluster 當中部署應用程式，會先把應用程式包裝成容器 container，而這裡的容器通常會選用 Docker。接著把一到多個容器包裝成 Kubernetes 的最小執行單位 Pod，然後再透過 Control Plane，去把 Pod 部署到合適的 Node 上面去運行。在抽象概念上，Pod 可以被視為一台虛擬的電腦主機，所以當我們部署了一個 Pod，概念上就等同於在虛擬資料中心當中創建了一台虛擬主機，這個 Pod 的資訊會被記錄在 Control Plane 當中，而實際運行在 Node 裡面。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621130613244.png]]

我們可以單獨部署一個 Pod，也可以利用 Deployment 的機制一次部署多個相同內容的 Pod，讓系統可以做到動態**水平擴充**與**自我修復**的效果。同樣的，這個 Deployment 的資訊會被記錄在 Control Plane 當中，而實際的 Pod 則運行在 Node 裡面。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621130827432.png]]


一旦 Pod 能順利被運行起來，下一個需要解決的問題就是打通 Pod 與 Pod 之間的網路連線。

在 K8s 的世界當中，Cluster 內部有自己的內網並與外界隔絕，而當每個 Pod 被創建起來時都會被隨機分配到一個內網動態 IP。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621131322657.png]]


由於這個動態 IP 難以掌控，因此我們會需要有個內部的虛擬路由器來作為 Pod 的網路接口，為我們把內部流量導向對應的 Pod。這種在 Cluster 內網負責導流量到 Pod 的虛擬路由器元件，我們稱之為 **Service**。同樣的，這個 Service 的資訊會被記錄在 Control Plane 當中與對應的 Pod 或是 Deployment 匹配。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621131407394.png]]

一旦 Pod 之間能相互溝通，下一個需要解決的問題就是打通 Cluster 內部與外部的網路連線。

這時，我們就會需要有個對外的虛擬路由器來對接外部流量，**這種對外的虛擬路由器我們稱之為** **Ingress Controller**，在實體 Cluster 當中以 Pod 的形式存在 (IGW 是獨立的AP來處理同ns下的網路流量)。如此一來，我們只要定義好 Ingress 路由規則，由 Cluster 外部來的請求就能通過 Ingress 串接到 Service，最終進到 Pod 進行處理並將結果沿相反的路徑回覆給請求者。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621131512347.png]]


以上的架構大致就足以滿足基本的網路服務需求，而實務上我們經常會把一些應用程式的參數以環境變數的形式給抽離出來，這樣就不用為了要更改某幾個參數大費周章去全部重新打包部署。在 K8s 當中，也有提供這樣的抽離環境變數的元件可供利用，包含存放明碼的 ConfigMap 以及存放密碼的 Secret。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621131823222.png]]

此外，即便在同一個 Cluster 當中也有可能會同時運行多個不同的專案，為了讓專案之間能相互區隔。K8s 也提供 Namespace 元件，來對不同專案做比較明確的切割和管理。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621131931862.png]]


而基於 Pod 和 Service 元件都一定會隸屬於某個 Namespace 的前提下，Kubernetes 也會為每個 Service 和 Pod 建立各自的 DNS Record，讓 Cluster 內部的應用程式之間能透過這套簡單的 DNS 規則相互溝通。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132015403.png]]

藉由以上的說明我們就能大致理解在實體架構當中除了 Pod 的實體運行在 Node 之上，主要元件都記錄與管理在 Control Plane 這個 Kubernetes 的大腦當中。包含元件與元件之間的關聯與互動主要也是在 Control Plane 進行。

而抽象概念上，這些元件就像是存在於一個由 Control Plane 這個大腦所想像出來的虛擬資料中心當中各司其職地負責自己份內的工作，就像真的有許多主機和路由器在這個不同維度的空間當中運行一樣。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132141723.png]]

## K8s 實務

接下來，就讓我們來進行實際操作，更進一步深刻體會與理解每一個元件以及相對應指令動作的意義。
要創造一個 Kubernetes Cluster 最簡單的方式是使用 minikube，由於 minikube 是基於 Docker 運行的，所以在跑 minikube 之前要事先先裝好 Docker。
一切都就定位之後，執行 minikube start，一個本機端的 Kubernetes Cluster 就跑起來了。在安裝 minikube 的同時
Kubernetes 的命令列工具 kubectl或者有人會念做 kube-cuttle 或是 kube-control 也會一併被安裝起來。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132413075.png]]

在一般使用情境下 kubectl 後面通常會接一些參數，包含要執行什麼動作、要作用在什麼類型的元件上、針對的元件名稱以及一些額外的參數。透過 kubectl get nodes 我們知道這個剛創建起來的 Cluster 只有一個名為 minikube 的 Node，當下也只負責 Control Plane 的工作。
透過 kubectl get namespaces 我們知道系統預設創建了四個 Namespaces，如果不特別指定的話，kubectl 執行的範圍就會限定在 default Namespace。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132535661.png]]

透過 kubectl get pods，我們知道目前在 default Namespace 下沒有任何 Pod，而當我們加上 --all-namespaces 或是 -A 就會列出所有 Namespaces 下面的所有的 Pods 。這時我們就可以看出在 kube-system Namespace 下面其實跑了許多 Control Plane 的 Pods。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132650468.png]]

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132805815.png]]

而透過 kubectl get services -A 我們也可以看到一些系統建立的 Services，以此類推。
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132908621.png]]
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621132836041.png]]


大致熟悉 kubectl 的操作同時了解 Cluster 的初始狀態之後，就可以開始在這之上建構一個 demo 系統了。為了方便想像，後續都會從虛擬 Cluster 的角度來做說明。

首先，我們先把想像中的系統給勾勒出來。其中為求方便好懂，我們都簡單使用元件縮寫配合編號來命名。

在這個 demo 系統當中，我們預計在兩個 Namespaces 之下

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133355218.png]]

分別部署單獨的 Pod

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133427911.png]]

以及使用 Deployment 來部署一群 Pods

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133504032.png]]

並把各自的 Service 給接起來

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133605378.png]]

再以 Ingress 來打通各自 Cluster 外部的流量

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133629290.png]]

同時也把各自的環境變數給抽離出來，把明碼及密碼分別存放在 ConfigMap 及 Secret 中，以方便未來動態調整。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133659619.png]]

為了 demo 效果，我們先準備一個特殊的 Docker image，除了顯示當前的 Server 資訊，也顯示三個環境變數，包含一個寫死的環境變數、一個 ConfigMap以及一個 Secret 的值。同時，如果帶入名為 url 的 HTTP 參數的話則會從當前的容器對 url 指定的網址發送一個 HTTP request 並把 HTTP response 給印出來。如此一來，我們就能透過這個機制觀察和測試 Cluster 內部 Pod 與 Pod 之間的溝通機制。我們以 docker build 把它 build 起來，docker run 把它跑起來，以瀏覽器實際測試過沒問題之後再用 docker push 把它推到 Docker hub 上面去供後續部署使用。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621133803434.png]]



接下來就可以開始打造我們所規劃的 Kubernetes 環境了。

在部署之前，我們先用 kubectl create namespace 指令把 ns1 和 ns2 這兩個 Namespaces 創建起來。
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134038919.png]]

接著我們也先把 ConfigMap 和 Secret 準備好以供後續 Pod 和 Deployment 引用。Kubernetes 的元件都是以 YAML 格式來做為設定檔，ConfigMap 相對單純，基本格式直接到 Kubernetes 官網抄範例來改就好。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134111378.png]]

在此，我們把 USERNAME 這個變數給放進 YAML 設定檔中，以 kubectl apply 建立之後，再以 kubectl get 來確認。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134200001.png]]


Secret 也類似，一樣到 Kubernetes 官網抄 YAML 範例來改。唯一不同的是這裡的值需要先經過 bass64 encode，表面上看起來比較神秘一點，實際還是能透過 base64 decode 來還原。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134335701.png]]

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134411259.png]]

所以在此，我們把 PASSWORD 這個變數給放進 YAML 設定檔中，以 kubectl apply 建立之後，再以 kubectl get 來確認。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134451695.png]]

接下來就可以開始準備我們的應用程式了。要部署一個 Pod，設定檔一樣到 Kubernetes 官網抄寫範例來改就好。

首先，把剛才準備好的 Docker image 給指定上去並把三個環境變數分別填入相對應的值。由於之後我們預計會綁定一個 Service，所以這邊需要在 metadata 裡面指定 labels，用來讓 Service 利用 selector 去綁定。![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621134705772.png]]

接著，我們就可以利用 kubectl apply，來把這個 Pod 部署到 ns1 的 Namespace 上。
執行過後，我們可以用 kubectl get 來確認狀態。第一次部署通常會需要花點時間抓取 Docker image 下來執行，等到 Status 變為 Running 就代表 Pod 部署完成，正在運行當中。
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621135012854.png]]

這時我們可以進一步用 kubectl port-forward 指令把 po1 的 80 port 指向本機的 8080 port，以瀏覽器來測試看看沒問題就代表 po1 部署成功。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621135054664.png]]

接著就來建立 po1 的 Service，我們一樣到 Kubernetes 官網抄範例來改。如同前面所提到的，Service 主要會利用 selector 去綁定 Pod 的 label。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621135139241.png]]

YAML 設定檔準備好後，同樣使用 kubectl apply 來部署，使用 kubectl get 來確認，也同樣可以用 kubectl port-forward 打通本機以瀏覽器來做測試。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621164542861.png]]

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621164810668.png]]

相較於部署單一 Pod，Deployment 則可以一次部署多個相同內容的 Pod。YAML 設定檔一樣可以到 Kubernetes 官網抄範例來改，其中 template 欄位的部分基本上就是一個 Pod 的設定，我們就從先前的 Pod 設定檔複製過來小改就好。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621164428824.png]]

YAML 設定檔準備好後同樣使用 kubectl apply 來部署，使用 kubectl get 來確認。除了確認 Deployment 的狀態之外也可以藉由確認 Pod 的狀態，發現多了三個藉由 Deployment 部署出來的 Pod。最後也同樣可以用 kubectl port-forward 來測試。

``` bash
kubectl apply -f depoly1.yaml -n ns1
```

``` bash
kubectl get depolyments -n ns1
```

``` bash
kubectl get pods -n ns1
```

``` bash
kubectl port-forward depolymen/deploy1 8080:80 -n ns1
```

類似於 po1 的 Service，deploy1 的 Service 也是大同小異，我們就直接進行部署並且一樣用 kubectl get 來確認一下，再以 kubectl port-forward 來測試。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621165236815.png]]

``` bash
kubectl apply -f deploy1-svc.yaml -n ns1
```

``` bash
kubectl get services -n ns1
```

``` bash
kubectl port-forward service/deploy1-svc 8080:80 -n ns1
```


Pod 以及 Deployment 和相對應的 Service 都部署建立完成之後，Cluster 內網的相互溝通就沒問題了。然而當我們想打通 Cluster 內網與外部的連線，就需要再額外建立 Ingress 路由規則，在這之前如同前面概念所提到的，要建立 Ingress 之前我們需要先確定 Cluster 內部跑著 Ingress Controller 作為執行網路封包路由的實際角色。

在 minikube 當中，要部署一個 Ingress Controller 只要執行 minikube addons enable ingress 就可以了
``` Bash
minikube addons enable ingress 
```

啟動之後我們以 kubectl get 來查看 ingress-nginx Namespace 的 Pod，就會發現 Ingress Controller 已經順利跑起來，我們也就可以來建立 Ingress 路由規則了。

``` Bash
minikube get pods -n ingress-nginx
```

要準備 Ingress 的 YAML 設定檔，我們一樣到 Kubernetes 官網抄範例來改，分別把路徑 po1 導向 po1-svc，以及路徑 deploy1 導向 deploy1-svc，同樣地我們使用 kubectl apply 來部署、再使用 kubectl get 來確認。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621165807933.png]]

``` bash
kubectl apply -f ing1.yaml -n ns1
```

``` bash
kubectl get ingress -n ns1
```

``` bash
kubectl port-forward service/deploy1-svc 8080:80 -n ns1
```



而為了去模擬 foo.bar.com，這個假的 domain name 我們要到 /etc/hosts 去把這個 domain name 給加上去再來進行測試。
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170025889.png]]
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170000064.png]]


同時由於 minikube其實是以 Docker 的形式跑起來的，Cluster 本身仍然被隔絕在 Docker 容器內部，因此我們還需要使用 minikube tunnel 指令來將 minikube 本身的 IP 串連到本機的 localhost，如此一來我們就可以使用模擬的 domain name配合 Ingress 定義的路徑一路連向預期的 Pod。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170211936.png]]

同時我們也可以使用先前設計的 url 參數傳入相對應的 Service url來測試 Cluster 內部Pod 連向 Deployment以及 Deployment 連向 Pod 所得到的結果，到此為止 ns1 這個 Namespace 下面的元件都已經建立完成。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170343819.png]]

依樣畫葫蘆，我們也可以把 ns2 這個 Namespace下面相對應的元件YAML 設定檔準備好，以 kubectl apply 依序建立起來等兩個 Namespace 內的元件都建立完成之後，就可以執行 minikube tunnel 來進行跨 Namespace 的連線測試

這時我們就可以觀察到，在跨 Namespace 的情況下直接使用 Service name 是無法連線的，然而只要在 Service name 後面再加上 Namespace 或者遵循 Kubernetes 的 DNS 規則，使用整串完整的 domain name就能進行跨 Namespace 的連線。



以上我們大致把 Kubernetes 常用的元件以及操作方式透過建置一個假想的系統完整呈現出來，藉由這些基礎元件的組合，我們就能在 Kubernetes 上打造出符合自身需求的系統，同時享有 Kubernetes 所帶來的種種好處。
##  Helm

然而從以上的操作當中我們不難發現一個問題，光是要建立一套簡單的系統就需要牽扯許多的 Kubernetes 元件，而隨著系統越來越複雜所牽扯到的元件終將變得難以維護。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170731637.png]]

為此我們需要一個 package 管理系統進一步將一整組元件打包成 package，以整包 package 為單位進行部署或更新。如此一來要建立一套系統就不用去執行一大堆 kubectl apply 的指令，而是一個指令就全部搞定。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170741068.png]]

接下來要介紹的 Helm，就是這樣一套為 Kubernetes 而生的 package 管理系統，Helm 的英文是舵的意思意味著協助舵手 Kubernetes 所不可或缺的工具，

在 Helm 的世界裡，package 被稱為 Helm chart 也就是航海圖，意味著當我們把航海路線都事先定義好，舵手就只要無腦依照航海圖去執行，就會抵達我們預想的目的地。而有了 Helm chart一整組定義好的系統，就有辦法以 package 的形式被分享和重複使用，接下來我們就試著把剛才的 demo 打包成 Helm chart，體會一下 Helm 的威力。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621170932823.png]]

首先我們先安裝好 Helm，就可以使用 helm create 來建立一個 demo-chart。

``` bash
brew install helm
```

``` bash
helm version
```

``` bash
brew create demo-chart
```

在 demo-chart 當中，Chart.yaml 定義了這個 chart 的主要資訊。templates 目錄存放我們想打包的 Kubernetes 元件的 YAML 檔，其中如果有需要抽離出來的變數則集中放在 Values.yaml 當中，以方便未來依照需求動態調整，至於 charts 目錄則用來存放其他相依的 charts。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621171139914.png]]



接著我們把 templates 目錄清空，再把先前其中一個 Namespace 底下的所有元件放入 templates 目錄當中，把檔名當中的 id 數字拿掉(pod1.yaml -> pod.yaml)，同時也把所有元件當中的 id 數字以及 Deployment 的 replica 個數給抽離出來，統一定義在 Values.yaml 當中。如此一來我們就已經把剛才的系統打包成 Helm chart 了。
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621171423606.png]]

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621171505110.png]]

其中在某些情況下，我們需要把部分變數覆寫掉，就可以把要覆寫的變數和值做成一個獨立的檔案，這裡我們準備一個 values-ns2.yaml 來為 ns2 這個 Namespace 下面的元件覆寫 nsId 為 2。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621171624100.png]]

打包完成後我們可以使用 helm template 來確定一下，變數都有如預期的被安插進最終的 YAML 當中，同時可以使用 --values 參數來指定我們剛剛準備好為 ns2 覆寫變數的檔案。

```bash
 helm template . | more
```

```bash
 helm template . --values=values-ms2.yaml | more
```

或是如果我們要覆寫的變數很單純，其實也可以使用 --set 來直接指定。如此一來，有被覆寫的變數就會被覆寫過去，其餘變數還是會去讀 Values.yaml 的值作為預設值。

```bash
 helm template . --set nsId=2 | more
```

確定都沒問題之後就可以使用 helm install 來進行實際的部署了。

在部署之前我們先重建兩個 Namespaces，確保兩個 Namespaces 都處在一個乾淨的狀態，
```bash
kubectl delete namespace n1
kubectl delete namespace n2

kubectl create namespace n1
kubectl create namespace n2
```

然後我們以 helm install 來部署這個 demo-chart 到 ns1，我們把它命名為 chart1，這時就可以用 kubectl get all 來確認元件都有順利被建立起來，接著以覆寫變數的方式部署 demo-chart 到 ns2，我們把它命名為 chart2，也同樣可以用 kubectl get all 確定一下元件都有順利被建立起來。

```bash
helm install chart1 . -n ns1
kubectl get all -n ns1

helm install chart2 . -n ns2 --values=values-ns2.yaml
```

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621172658685.png]]

最後打通 minikube tunnel 實際測試一下功能，也都沒有問題

就這樣我們先前花了許多功夫才建立起來的系統，透過 Helm chart 輕輕鬆鬆就搞定，而除了打包成 Helm chart 一鍵安裝的概念之外，Helm 也有版本控制的機制，接下來我們就實際來體驗一下。

先前我們在 Values.yaml 給定的 replica 個數是 3，當我們把它改成 1 並以 helm upgrade 進行更新時就會發現，Deployment 的 Pod replica 數量確實變成 1 個。

```bash
helm upgrade chart1 . -n ns1
```

這時以 helm history 指令可以看到 chart1 這個 Helm chart 的歷史更動記錄，

```bash
helm history chart1 -n ns1
```
![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621173016999.png]]


如果想要還原到上一個版本可以使用 helm rollback 指令來進行還原。
```bash
helm rollback chart1 -n ns1
```


這時我們可以發現 Deployment 的 Pod 數量變回 3 個，同時 helm history 也可以看到這次 rollback 的還原記錄。而除了還原上一版本之外，helm rollback 也可以指定版本來進行還原.


例如我們指定還原到第 2 版也就是 Pod replica 數量是 1 的情況，Deployment 的 Pod 數量就又再次變回 1 個，而 helm history 也一樣會有這次 rollback 的還原記錄

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621173216518.png]]

最後我們再使用 helm delete 指令來移除先前安裝的 Helm chart

``` bash
helm delete chart1 -n ns1
helm delete chart2 -n ns2
```

並把 minikube 建立出來的 Cluster 給刪除結束這次 demo

```bash
minikube stop

minikube delete
```


以上所有原始碼的連結附在 [GitLab](https://gitlab.com/kubernetes-helm-demo)，供有需要的鄉民朋友們參考。

順帶一提，除了靠自己打包 Helm chart 之外，在公開的 Artifact Hub 上面也有許多鄉民們無私分享貢獻的實用 Helm chart 供大家直接套用，不妨可以多加利用

回顧整個近代科技發展史，從電晶體抽象到邏輯閘以至於更複雜的積體電路、從機器語言抽象到組合語言以至於高階程式語言、從傳統實體機器抽象到 VM 虛擬機器再抽象到容器化的 Docker，
，進而發展出大規模協作管理機器與部署容器的 Kubernetes 以及 Helm。

人們不斷透過一層一層的技術堆疊，試圖把複雜到不可控的東西給抽象化、模組化而變為可控，然而抽象並非毫無成本，除了額外的學習門檻之外，這些抽象化的解決方案往往是透過犧牲某些彈性與效率而換來的。

也因此在某些情況下抽象過後的解法不見得會是最好的解決方案，例如高階程式語言雖然帶來了更高的開發效率和可讀性，但執行效率上往往不如低階程式語言。所以對於要求高效率的情境，我們通常還是會選用較低階的程式語言去開發。

同理 Kubernetes 雖然使我們省去了管理機器與部署應用程式的煩惱，但我們卻也失去了一些對底層資源的控制權，以及部分為了維持抽象層所需的資源損耗，進而可能造成更高的營運成本，也因此在評估解決方案時還是得視情況而定。

![[assets/二十一分鐘略懂 Kubernetes (以及 Helm)/file-20260621173525350.png]]

面對複雜的問題，抽象化的解法使我們更好掌控全局，而面對不複雜的問題，低階的解法往往才是有效率的好解法。