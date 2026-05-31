---
tags: [devops, docker, kubernetes, volume, storage]
---

> 關聯：[[docker]] [[kubernetes]]

# Volume 教學：從「資料消失」感受它的價值

學 volume 最快的方式不是看文件，而是先讓資料消失一次。

---

## 第一關：親眼看到資料消失（無 volume）

```bash
# 啟動一個容器，寫入資料，然後刪掉它
docker run -it --name demo alpine sh
# 在容器裡執行：
echo "hello" > /data/memo.txt
exit

# 刪掉容器
docker rm demo

# 重新跑同一個 image
docker run -it --name demo alpine sh
# 在容器裡執行：
cat /data/memo.txt
# → cat: can't open '/data/memo.txt': No such file or directory
```

**結論**：容器的 writable layer 跟容器生命週期綁死。容器刪了，資料跟著消失。

---

## 第二關：用 Volume 讓資料活過去

```bash
# 建立 named volume
docker volume create mydata

# 掛載並寫入
docker run -it --name demo -v mydata:/data alpine sh
# 在容器裡執行：
echo "hello" > /data/memo.txt
exit

# 刪掉容器
docker rm demo

# 換一個全新容器，掛同一個 volume
docker run -it --name demo2 -v mydata:/data alpine sh
# 在容器裡執行：
cat /data/memo.txt
# → hello ✓
```

**結論**：volume 存活於容器生命週期之外，容器刪了，volume 的資料還在。

---

## Volume 三種形式比較

| 形式 | 語法 | 資料存在哪 | 適用情境 |
|---|---|---|---|
| Named Volume | `-v mydata:/data` | Docker 管理的路徑 | DB、cache，不需要直接存取 |
| Bind Mount | `-v /host/path:/data` | Host 指定路徑 | 本機開發，即時同步程式碼 |
| tmpfs | `--tmpfs /data` | 記憶體，重啟就消失 | session、暫存，不需持久 |

---

## 第三關：Bind Mount — 開發時的即時同步

這是開發環境最常感受到 volume 好處的場景。

```bash
# 假設 host 的 ./src 有你的程式碼
docker run -it --rm \
  -v "$(pwd)/src:/app/src" \
  -p 3000:3000 \
  node:20 node /app/src/index.js

# 現在直接修改 host 的 ./src/index.js
# → 容器內 /app/src/index.js 同步更新，不需要重 build image
```

**效益**：不需要每次改程式碼就重新 `docker build`，縮短開發循環。

---

## 第四關：K8s 的 Volume — 為什麼更複雜？

Docker volume 只解決單機問題。K8s Pod 可能跑在任意 Node 上，需要跨節點的儲存抽象。

```
Pod A (Node 1) ─┐
                ├── PVC ──→ PV ──→ 實際儲存（NFS / cloud disk / hostPath）
Pod B (Node 2) ─┘
```

K8s 把「使用者要什麼」（PVC）和「實際怎麼提供」（PV）分開，讓 Pod 不需要知道底層儲存細節。

---

## PV / PVC / StorageClass 三者關係

```
StorageClass（規格型號，像是「SSD 等級」）
    ↓ 動態 Provision
PV（實際磁碟，管理員或系統建立）
    ↑ Bind（一對一）
PVC（使用者的申請單，Pod 掛這個）
    ↑ 掛載
Pod
```

| 資源 | 由誰建立 | 描述 |
|---|---|---|
| PV | 管理員 / StorageClass 動態建立 | 實際儲存資源 |
| PVC | 開發者 | 申請「我需要 1Gi 的 ReadWriteOnce 儲存」 |
| StorageClass | 管理員 | 定義動態建立 PV 的規則 |

---

## 第五關：minikube 上的實作（感受 Pod 重啟資料不消失）

### 步驟一：建立 PVC

```yaml
# pvc-demo.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: demo-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 256Mi
  storageClassName: standard  # minikube 預設的 StorageClass
```

```bash
kubectl apply -f pvc-demo.yaml
kubectl get pvc demo-pvc
# STATUS 要變成 Bound 才能用
```

### 步驟二：掛 PVC 到 Pod，寫入資料

```yaml
# pod-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: writer
spec:
  containers:
    - name: app
      image: alpine
      command: ["sh", "-c", "echo 'hello from pod' > /data/memo.txt && sleep 3600"]
      volumeMounts:
        - name: storage
          mountPath: /data
  volumes:
    - name: storage
      persistentVolumeClaim:
        claimName: demo-pvc
```

```bash
kubectl apply -f pod-demo.yaml
kubectl exec writer -- cat /data/memo.txt
# → hello from pod
```

### 步驟三：刪掉 Pod，換一個新 Pod 讀資料

```bash
kubectl delete pod writer

# 換一個 reader Pod 掛同一個 PVC
kubectl run reader --image=alpine --overrides='{
  "spec": {
    "containers": [{
      "name": "reader",
      "image": "alpine",
      "command": ["cat", "/data/memo.txt"],
      "volumeMounts": [{"name": "s", "mountPath": "/data"}]
    }],
    "volumes": [{"name": "s", "persistentVolumeClaim": {"claimName": "demo-pvc"}}],
    "restartPolicy": "Never"
  }
}' --restart=Never

kubectl logs reader
# → hello from pod ✓
```

**結論**：Pod 被刪、重啟、甚至換到另一個 Node 重跑，只要掛同一個 PVC，資料就在。

---

## Access Modes 說明

| Mode | 縮寫 | 說明 |
|---|---|---|
| ReadWriteOnce | RWO | 只能一個 Node 掛載讀寫（最常用） |
| ReadOnlyMany | ROX | 多個 Node 唯讀 |
| ReadWriteMany | RWX | 多個 Node 讀寫（需要 NFS / CephFS 等） |

minikube 的 `standard` StorageClass 只支援 RWO。

---

## Volume 在實際架構中的位置

```
資料庫（PostgreSQL）
  └── PVC（RWO）→ PV → hostPath（minikube）/ cloud disk（prod）

Config / Secret
  └── ConfigMap / Secret 掛 Volume（不用 PVC，K8s 直接管）

應用程式 log
  └── 通常不用 volume，用 sidecar 或 log aggregator 收
```

---

## 常見問題排查

**PVC 一直是 Pending**

```bash
kubectl describe pvc <name>
# 看 Events 欄位
```

- 原因：沒有匹配的 PV 或 StorageClass 不存在
- 解法：確認 `storageClassName` 跟 `kubectl get storageclass` 列出的一致；minikube 用 `standard`

**Pod 無法掛載 volume，卡在 ContainerCreating**

```bash
kubectl describe pod <name>
# 看 Events → FailedMount
```

- 原因：PVC 還沒 Bound，或 PV 被其他 Pod 獨佔（RWO 限制）
- 解法：確認 `kubectl get pvc` 狀態為 `Bound`；RWO 不能兩個 Pod 同時掛

**刪 PVC 後資料不見了**

- 原因：PV 的 `reclaimPolicy` 預設是 `Delete`，PVC 刪掉 PV 也跟著刪
- 解法：生產環境把 PV 或 StorageClass 的 reclaimPolicy 設為 `Retain`
