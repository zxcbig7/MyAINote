# kubectl apply — API 版本不符問題

## 問題描述

執行 `kubectl apply -f <file.yaml>` 時出現：

```
error: resource mapping not found for name: "..." namespace: "..."
no matches for kind "<Kind>" in version "<apiVersion>"
ensure CRDs are installed first
```

即使 CRD 已確認安裝，錯誤仍然存在。

---

## 原因

yaml 檔案中指定的 `apiVersion` 與 cluster 實際安裝的版本不符。常見情況：

- 套件升版後 API 版本從 `v1beta1` 升為 `v1`
- 文件或範例使用的版本已過期
- kubectl 的 API discovery cache 尚未更新

---

## 診斷方式

查詢該資源類型目前 cluster 支援的版本：

```bash
kubectl api-resources | grep <keyword>
```

輸出中 `APIVERSION` 欄位即為實際支援的版本。

---

## 解法

將 yaml 中的 `apiVersion` 改為 `kubectl api-resources` 查到的版本，再重新 apply。

若 kubectl cache 過期導致誤判，清除後重試：

```bash
# Windows
rmdir /s /q "%USERPROFILE%\.kube\cache"

# Linux / macOS
rm -rf ~/.kube/cache
```

---

## 注意事項

- CRD 安裝完成不代表立即可用，API server 需要一段時間完成 discovery 更新
- 官方文件與社群範例的 `apiVersion` 可能落後於最新版本，以 `kubectl api-resources` 為準
- 不同版本的套件（helm chart）可能對應不同 API 版本，升版時需一併確認 yaml

---

## 相關問題

若 `kubectl apply` 因 annotation 大小超過 262KB 上限而失敗，改用 server-side apply：

```bash
kubectl apply --server-side -f <file.yaml>
```

差異：
| | client-side apply | server-side apply |
|--|---|---|
| 差異計算 | kubectl 本機 | K8s API server |
| annotation 大小限制 | 262KB | 無 |
| 適用場景 | 一般資源 | CRD 等大型 manifest |
