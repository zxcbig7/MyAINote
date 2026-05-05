---
type: summary
domain: tech
tags: [argocd, gitops, kubernetes, tutorial]
sources: [raw/tech/devops/argocd-tutorial.md]
created: 2026-05-03
updated: 2026-05-03
---

# argocd-tutorial.md — Summary

> 來源：`raw/tech/devops/argocd-tutorial.md`
> 性質：個人實作教學筆記，從零安裝到日常運維 + ApplicationSet 與跨 namespace 進階

## 核心 Takeaway
1. **GitOps 心法**：Git push 取代 `kubectl apply`，ArgoCD 自動 reconcile（預設 3 分鐘 poll）
2. **selfHeal 是雙面刃**：手動改叢集會被覆蓋，臨時 debug 時要記得暫停 sync
3. **HTTPS > SSH**：ArgoCD 連 GitHub 用 HTTPS，SSH 需要額外 SSH agent 設定
4. **跨 namespace Application** 需要三段設定（`argocd-cmd-params-cm` + `appproject` + restart controllers），少一步就生不出 Application
5. **ApplicationSet** 是多環境部署的關鍵——一個模板 + list generator 即可生 dev/stg/prod

## 內容大綱
- 安裝 ArgoCD（kubectl apply 官方 manifests）
- Web UI 開啟（port-forward + 取得 admin 初始密碼）
- 建立 Application（手動 yaml + apply）
- syncPolicy：`automated.prune` / `automated.selfHeal`
- 私有 repo 認證（Secret + label）
- ApplicationSet 模板與多環境部署
- 跨 namespace 管理 Application 的設定

## 衍生問題（值得日後追問或補 source）
- `selfHeal` 在生產環境的最佳實踐？是否該關閉以保留 hotfix 空間？
- ApplicationSet 與 Argo Workflows 的協作方式？
- ArgoCD vs Flux 的選型差異？
- Sync wave / Sync hook 的實際應用場景？

## 連結
- 主要 entity：[[argocd]]
- 預期未來連結：[[gitops]]、[[helm]]、[[kubernetes]]
