---
tags: [devops, helm, kubernetes]
---

> 關聯：[[helm]]、[[kubernetes]]

# Helm Chart

- Helm = Chart + Release + Repository
- Chart 用於描述 K8s 資源配置

```bash
my-chart/
├── **Chart.yaml**            # 套件元資料與依賴宣告（必要）
├── Chart.lock            # 依賴版本鎖定檔（自動產生，應納入版控）
├── **values.yaml**           # 預設參數值
├── values.schema.json    # 參數的 JSON Schema 驗證（選用）
├── **templates/**            # Go template 模板目錄
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── serviceaccount.yaml
│   ├── _helpers.tpl      # 共用具名模板（不會產生輸出）
│   ├── NOTES.txt         # 安裝後顯示的提示訊息
│   └── tests/
│       └── test-connection.yaml
├── charts/               # 下載的依賴套件（.tgz）
├── crds/                 # CRD 定義（在 templates 之前套用）
└── README.md
```

- Release 是 Chart 安裝到 Cluster 後的運行實例。
- 一個 Chart 可以多次安裝