---
type: entity
domain: tech
tags: [minikube, kubernetes, local-dev, devops]
sources:
  - raw/tech/devops/Minikube 介紹.md
created: 2026-05-03
updated: 2026-05-03
---

# Minikube

Minikube 是一個在本機電腦跑起**單節點 Kubernetes Cluster** 的工具，讓開發者不需要真實雲端環境就能學習和測試 K8s。

## 主要用途

- 學習 `kubectl` 指令
- 測試自己寫的 Deployment、Service、Ingress
- 驗證 YAML 設定是否正確
- 推上正式環境前先在本地確認行為

## 架構概念

```
電腦 (Host)
└── Minikube VM / Container
    └── 單節點 Kubernetes Cluster
        ├── Control Plane（API Server、Scheduler、etcd...）
        └── Worker（同一個節點）
```

## Driver 選擇

| Driver | 說明 |
| --- | --- |
| `docker` | 用 Docker container 模擬節點，最常用 |
| `hyperkit` | macOS 原生 VM |
| `hyper-v` | Windows 原生 VM |
| `virtualbox` | 跨平台 VM |

本機環境（Windows 11）使用 `docker` driver。

## 常用指令

```bash
# 啟動（指定 driver）
minikube start --driver=docker

# 停止
minikube stop

# 刪除 cluster
minikube delete

# 查看狀態
minikube status

# 取得 Cluster IP
minikube ip

# 開啟 Dashboard
minikube dashboard

# 啟用 addon（如 ingress）
minikube addons enable ingress

# SSH 進入 minikube VM
minikube ssh

# 建立 tunnel（讓 LoadBalancer 服務可從外部連線）
minikube tunnel
```

## 本機開發注意事項

- minikube 的 etcd 和資料存在 minikube VM 內部（不是 PVC）
- 使用 `minikube tunnel` 才能讓 ingress 對外暴露
- Windows 環境中 Docker driver 跑在 WSL2 的 ext4.vhdx 內
- 若需 port-forward：`kubectl port-forward svc/<name> <local>:<remote>`

## 連結

- [[kubernetes]] — K8s 核心概念
- [[kubectl]] — minikube 環境中的 CLI 工具
- [[argocd]] — GitOps 部署工具，可在 minikube 上運行
- [[helm]] — minikube 上部署應用的打包工具
