---
type: concept
domain: tech
tags: [kubernetes, k8s, docker, argocd, helm, prometheus, elk, mastery, curriculum, devops]
sources:
  - raw/devops/Docker/01-基礎概念/Docker/Docker.md
  - raw/devops/Kubernetes (K8s)/Kubernetes (K8s).md
  - raw/devops/Kubernetes (K8s)/K8s YAML 概念與架構/K8s YAML 概念與架構.md
  - raw/devops/Helm Chart/helm-tutorial/helm-tutorial.md
  - raw/devops/argocd-tutorial/argocd-tutorial.md
  - raw/devops/ELK/Kibana Query Language (KQL).md
  - raw/devops/troubleshooting/troubleshooting.md
created: 2026-07-31
updated: 2026-08-01
---

# 雲原生部署體系 — 從會用到問不倒

這不是一份速查手冊。速查手冊回答「怎麼做」，而這套教材要回答的是「為什麼」。

兩者的差別在被追問的第二層就會現形。知道 `kubectl apply` 怎麼下的人很多，能說清楚這個指令送出去之後，請求經過哪些關卡、誰決定 Pod 該去哪台機器、為什麼 API 回了 200 但 Pod 還沒跑起來的人很少。前者遇到沒見過的錯誤只能貼上 Google，後者能從症狀反推根因。這套教材的目標是把讀者送到後者那一側。

涵蓋範圍是一條完整的交付鏈：**容器（Docker）→ 編排（Kubernetes）→ 打包與交付（Helm、ArgoCD）→ 可觀測性（Prometheus/Grafana、ELK）**。這幾樣東西在實務上從來不是分開學的，一個部署問題可能起因於 Dockerfile 的一行 `COPY`，表現成 ArgoCD 的 OutOfSync，最後在 Kibana 的日誌裡才找到真相。

## 誰該讀這套教材

預設讀者會用 Docker、看過 K8s 的 YAML，也許已經照著教學把服務部署起來過，但心裡清楚自己是在照抄範例——不確定每個欄位為什麼要那樣寫，也不確定出事的時候該從哪裡查起。

讀完之後，應該能夠獨立設計 YAML 而不是拼湊、審查別人的部署設定並指出問題、從一個模糊的「服務怪怪的」推理到具體根因，以及在被同事追問「為什麼」的時候，答得出機制而不只是現象。

## 進度總覽

**全書 16 章 + 2 附錄完成**，約 **143,600 字**、**60 張圖解**。

| 篇 | 章節 | 核心問題 | 狀態 |
| --- | --- | --- | --- |
| **容器篇** | [[00-docker-foundations]] | 容器在 kernel 層到底是什麼？image layer 為什麼刪不掉東西？ | ✅ |
| **基礎篇** | [[01-why-kubernetes]] | 部署的痛從哪來，K8s 的取捨是什麼 | ✅ |
| | [[02-cluster-internals]] | `kubectl apply` 的完整旅程、為什麼是 pull-based | ✅ |
| | [[03-api-and-yaml]] | GVK、apiVersion 棄用、labels/selector、server-side apply | ✅ |
| **資源篇** | [[04-workloads]] | 三種 Probe 差在哪？滾動更新為什麼還是掉請求？ | ✅ |
| | [[05-networking]] | ClusterIP 為什麼 ping 不通？封包從外部到容器的完整路徑 | ✅ |
| | [[06-config-and-storage]] | 改了 ConfigMap 為什麼沒生效？PVC 為什麼一直 Pending？ | ✅ |
| **治理篇** | [[07-scheduling-and-resources]] | requests/limits 真義、CPU throttle vs Memory OOMKill、QoS | ✅ |
| | [[08-security-and-rbac]] | 認證授權三道關卡、RBAC 四物件配對、Pod Security | ✅ |
| | [[09-extending-kubernetes]] | 為什麼 YAML 被改了？namespace 為何卡 Terminating？ | ✅ |
| **交付篇** | [[10-helm]] | `include` vs `template`、`nindent`、values 覆蓋優先序 | ✅ |
| | [[11-argocd]] | Sync 與 Health 為何獨立？OutOfSync 但看起來一樣怎麼辦？ | ✅ |
| **維運篇** | [[12-cluster-operations]] | etcd 備份還原、憑證輪替、版本升級、Velero | ✅ |
| | [[13-troubleshooting]] | 分層定位方法論、Pod 狀態機、19 個真實案例庫 | ✅ |
| **可觀測性篇** | [[14-prometheus-grafana]] | PromQL、`rate` vs `irate`、histogram 算 P95、USE/RED | ✅ |
| | [[15-elk-elastic]] | 倒排索引、`text` vs `keyword`、KQL、ILM、ELK vs Loki | ✅ |
| **附錄** | [[16-self-assessment]] | 144 題自我檢測，蓋住答案自己講一遍才算會 | ✅ |
| | [[17-cheatsheet]] | 緊急排錯十連發、17 種 YAML 骨架、PromQL/KQL 速查 | ✅ |

## 學習路徑

每天的份量抓在兩到三小時，重點是**邊讀邊在 minikube 上動手驗證**。教材裡的 YAML 範例都應該實際套下去看結果，尤其是那些「如果不這樣寫會出什麼事」的反例——親手把它弄壞一次，比讀十遍都有效。

| 天 | 章節 | 這天結束後你能回答 |
| --- | --- | --- |
| Day 1 | 00 | 容器和虛擬機到底差在哪？為什麼 Dockerfile 的順序會影響 build 速度？ |
| Day 2 | 01–03 | K8s 解決了什麼問題？`kubectl apply` 之後發生了什麼事？ |
| Day 3 | 04 | Deployment 滾動更新時，舊 Pod 什麼時候才真的被砍掉？ |
| Day 4 | 05–06 | 為什麼 Service 連得到但 Ingress 連不到？ConfigMap 改了為什麼沒生效？ |
| Day 5 | 07–09 | 為什麼這個 Pod 排不進去？為什麼我送出去的 YAML 被改了？ |
| Day 6 | 10–11 | ArgoCD 顯示 OutOfSync 但兩邊看起來一樣，怎麼回事？ |
| Day 7 | 12–15 | 同事說「服務掛了」，你的第一個指令下什麼？P95 延遲怎麼從 Prometheus 撈？ |

## 怎麼用這套教材

**第一遍求通不求精。** 遇到卡住的段落先標記起來繼續往下，很多概念要看過後面才回頭理解得了——例如 Finalizer 為什麼存在，要先知道 controller 怎麼運作。

**第二遍動手拆。** 回到標記處，在 minikube 上實際把每個機制跑一次。特別是治理篇與可觀測性篇的內容，光讀不做幾乎留不住。

**第三遍反過來考自己。** 教材裡的「常見誤解」與「同事會來問你的問題」小段落，蓋住答案先自己講一遍。講得出來才算會。

## 這套教材的獨特之處

第 13 章的案例庫收錄了 **19 個來自實際環境的踩坑紀錄**——Harbor robot account 名稱含 `$` 被 shell 展開、Cloudflare Tunnel 的 1016 錯誤與 100MB 上傳上限、WSL2 記憶體吃滿、CI 用全域 `sed` 改 tag 導致多服務互蓋、ArgoCD hard refresh 的時機。這些不是教科書上找得到的東西，而是真的在這套環境上出過事、查過、修好的紀錄，並且散布在各章對應的機制說明裡。

## 連結

- [[kubernetes]] — K8s entity 頁，速查用
- [[docker]] — Docker entity 頁
- [[kubectl]] — CLI 指令速查
- [[helm]] — Helm 打包工具
- [[argocd]] — GitOps 部署控制器
- [[minikube]] — 本機練習環境
- [[cicd-pipeline]] — CI/CD 完整流程
- [[devops-moc]] — DevOps 主題入口
