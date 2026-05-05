# Minikube 介紹

Minikube 是一個 **Kubernetes cluster** 的工具，能讓你在本機電腦上跑起一個**單Node** 
目的：讓開發者不需要真實的雲端環境，就能學習和測試 Kubernetes

### 主要用途

- 學習 `kubectl` 指令
- 測試自己寫的 Deployment、Service、Ingress
- 驗證 YAML 設定是否正確
- 在推上正式環境前先在本地確認行為

### 架構概念

電腦 (Host)
└── Minikube VM / Container
└── 單節點 Kubernetes Cluster
├── Control Plane (API Server, Scheduler, etcd...)
└── Worker (同一個節點)

| Driver | 說明 |
| --- | --- |
| `docker` | 用 Docker container 模擬節點，最常用 |
| `hyperkit` | macOS 原生 VM |
| `hyper-v` | Windows 原生 VM |
| `virtualbox` | 跨平台 VM |