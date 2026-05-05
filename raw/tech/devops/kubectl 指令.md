# kubectl 指令

# 查看資源

## **get**

列出資源（pods, services, deployments...），最常用的查看指令，支援 -o wide/yaml/json

## **describe**

顯示資源的詳細資訊，包含 Events，除錯的起點

## **explain**

查看資源欄位的說明文件，相當於內建 API spec 查閱器

## **api-resources**

列出叢集支援的所有資源類型與縮寫（po, svc, deploy...）

## **api-versions**

列出叢集支援的所有 API 版本群組（v1, apps/v1...）

## **version**

顯示 kubectl client 與 API Server 的版本資訊

# 建立/管理

## create

一次性建立資源，資源已存在會報錯，適合明確的新建場景

## apply

宣告式建立或更新資源，CI/CD 最常用，idempotent

## delete

刪除資源，可搭配 -f yaml 或直接指定名稱

## edit

在預設編輯器直接修改資源的 YAML，存檔即套用

## patch

用 JSON/YAML 片段更新資源的特定欄位，不用改整個 YAML

## replace

用檔案完整取代資源，相當於 delete + create

## scale

手動調整 Deployment/StatefulSet 的 replica 數量

## autoscale

建立 HPA，依 CPU 使用率自動調整 Pod 數量

## rollout

部署的 rollout：history、status、undo（回滾）、pause/resume

## set

更新資源的特定屬性，最常用於 set image 更新容器映像

## label

新增或修改資源的 label，影響 selector 和排程

## annotate

新增或修改資源的 annotation，通常儲存 metadata

## taint

替 Node 加上 taint，配合 toleration 控制 Pod 排程

## cordon

標記 Node 為不可排程，新 Pod 不會被排到這個節點

## uncordon

解除 cordon，讓 Node 重新可排程

## drain

驅逐 Node 上的所有 Pod，通常用在節點維護前

## run

快速建立一個 Pod 並執行指定映像，測試用途為主

## expose

將 Deployment/Pod 對外暴露，快速建立 Service

# 除錯

logs
取得 Pod 內容器的 log，-f 追蹤即時輸出，--previous 看崩潰前的 log

exec
在容器內執行指令，-it 可進入互動 shell

port-forward
將本機 port 轉發到 Pod/Service，本地測試神器

cp
在本機與容器之間複製檔案

top
顯示 Pod 或 Node 的即時 CPU/Memory 用量（需 metrics-server）

events
列出叢集事件，等同 describe 裡的 Events 區塊，快速排錯用

attach
附加到正在執行中容器的 stdin/stdout，類似 docker attach

debug
為 Pod 建立 debug 容器（ephemeral container），不重啟原 Pod

proxy
在本機啟動 API Server proxy，可直接呼叫 Kubernetes REST API

# Cluster 設定

config
管理 kubeconfig：切換 context、namespace，設定、使用者

cluster-info
顯示 API Server 和 CoreDNS 的位址

auth
驗證 RBAC 權限（can-i），確認目前身份是否能執行某操作

certificate
審核（approve/deny）TLS 憑證簽署請求（CSR）

# 進階

diff
預覽 apply 會做什麼變更，不實際執行，CI/CD 審查用

kustomize
執行 Kustomize 並輸出最終 YAML，等同 kustomize build

wait
等待資源到達指定狀態，再繼續下一步，腳本自動化用

completion
輸出 shell 自動補全腳本（bash/zsh/fish），強烈建議啟用

plugin
列出已安裝的 kubectl plugin（如 krew 安裝的 kubectx 等）

```bash

```

kubectl create -f kubernetes-demo.yaml

kubectl apply -f kubernetes-demo.yaml

ArgoCD 查密碼
`kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

---

## Troubleshooting：kubectl apply API 版本不符

執行 `kubectl apply -f <file.yaml>` 出現：

```text
error: resource mapping not found for name: "..."
no matches for kind "<Kind>" in version "<apiVersion>"
```

**原因**：yaml 中的 `apiVersion` 與 cluster 實際支援的版本不符（套件升版、文件過期、或 discovery cache 未更新）。

**診斷**：

```bash
kubectl api-resources | grep <keyword>   # 查該資源類型目前支援的版本
```

**解法**：將 yaml 的 `apiVersion` 改為查到的版本後重新 apply。若 cache 過期：

```bash
rm -rf ~/.kube/cache         # Linux / macOS
rmdir /s /q "%USERPROFILE%\.kube\cache"   # Windows
```

**annotation 超過 262KB**：改用 server-side apply

```bash
kubectl apply --server-side -f <file.yaml>
```

| | client-side apply | server-side apply |
| --- | --- | --- |
| 差異計算 | kubectl 本機 | K8s API server |
| annotation 大小限制 | 262KB | 無 |
| 適用場景 | 一般資源 | CRD 等大型 manifest |
