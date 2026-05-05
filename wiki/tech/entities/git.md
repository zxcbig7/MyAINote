---
type: entity
domain: tech
tags:
  - git
  - github
  - version-control
  - workflow
sources:
  - raw/tech/git/Git 指令筆記.md
  - raw/tech/git/Git 每日開發 SOP.md
  - raw/tech/git/Github 心得.md
created: 2026-05-03
updated: 2026-05-03
---

# Git

Git 是分散式版本控制系統。核心概念是維護一個完整的物件儲存庫（object store），追蹤所有變更歷史。

## 四種 Git 物件

| 物件 | 說明 |
| --- | --- |
| **blob** | 檔案的「內容」。`git add` 時立即寫入，只有內容、無檔名 |
| **tree** | 特定目錄的快照，包含檔名、對應 blob、子 tree |
| **commit** | 記錄哪些 tree 組成版本，含提交時間、訊息、parent commit |
| **tag** | 關聯特定 commit 的容器，通常用於版本標記 |

## 四種檔案狀態

- `untracked`：尚未加入 Git 追蹤
- `unmodified`：已追蹤，內容與 HEAD 一致
- `modified`：已編輯，與 HEAD 不一致
- `staged`：等待被 commit（在索引中）

## 每日開發 SOP

### Branch Policy

| 分支 | 用途 | 規則 |
| --- | --- | --- |
| `main` | 穩定、可發佈版本 | **不直接開發** |
| `dev` | 日常整合分支 | 日常工作基準 |
| `feature/*` | 功能開發 | 一個功能一支 |

### 標準流程

```bash
# 0. 開始前（每天一次）
git checkout dev
git pull origin dev

# 1. 開新功能
git checkout -b feature/my-feature

# 2. 開發中（小步 commit）
git add .
git commit -m "feat: add user login page"

# 3. 功能完成 → 回 dev
git checkout dev
git pull origin dev          # 確保最新
git merge feature/my-feature

# 4. 推到遠端
git push origin dev

# 5. 清理 feature 分支
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

## 常用指令

### 基本操作

```bash
git init                    # 初始化儲存庫
git status                  # 查看狀態
git add <file>              # 加入暫存區
git add .                   # 加入所有變更
git commit -m "message"     # 提交
git log --pretty=oneline    # 精簡查看歷史
git log --oneline --graph   # 圖形化分支歷史
git diff                    # 工作目錄 vs 索引
git diff HEAD               # 工作目錄 vs HEAD
git diff --cached           # 索引 vs HEAD
```

### 分支操作

```bash
git branch                  # 列出分支
git branch <name>           # 建立分支
git checkout <name>         # 切換分支
git checkout -b <name>      # 建立並切換
git merge <name>            # 合併（保留 merge commit 用 --no-ff）
git rebase <name>           # 將目前 commits 移到 name 後面（線性歷史）
git branch -d <name>        # 刪除已合併分支
git branch -D <name>        # 強制刪除
```

### 相對引用

```bash
HEAD^   # 上一個 commit（等同 HEAD~1）
HEAD~3  # 往上 3 個 commit
git checkout HEAD^          # 移動到上一個 commit
git branch -f main HEAD~3   # 強制移動 main 到指定位置
```

### 撤銷 / 還原

```bash
# reset（本地使用，改寫歷史）
git reset HEAD^             # 退回上一個 commit，保留工作目錄變更
git reset --hard HEAD^      # 退回並放棄所有變更

# revert（遠端安全，建立反向 commit）
git revert HEAD

# stash（臨時儲存未完成工作）
git stash                   # 儲存（包含已追蹤）
git stash -u                # 儲存（包含 untracked）
git stash pop               # 取回
```

### 遠端操作

```bash
git remote add origin <url>       # 設定遠端
git push origin main              # 推送
git push -u origin main           # 首次推送，設定追蹤
git pull origin main              # 拉取並合併（= fetch + merge）
git fetch origin                  # 只下載，不合併
git clone <url>                   # 複製遠端儲存庫
```

### Tag

```bash
git tag                     # 列出標籤
git tag v1.0.0              # 建立輕量標籤
git tag -a v1.0.0 -m "msg"  # 建立標示標籤（推薦）
git push origin v1.0.0      # 推送標籤
git push origin --tags      # 推送所有標籤
```

## 衝突處理

1. `git status` 看衝突的檔案
2. 衝突標記：`<<<<<<< HEAD`（你的）到 `=======`，`=======` 到 `>>>>>>> branch`（對方的）
3. 手動編輯解決後 `git add . && git commit`
4. 若要放棄：`git reset --hard ORIG_HEAD`

## Merge vs Rebase

| | Merge | Rebase |
| --- | --- | --- |
| 歷史 | 保留分支歷史，產生 merge commit | 線性歷史，更乾淨 |
| 衝突風險 | 較低 | 較高 |
| 適合場景 | 多人協作的主分支合併 | 整理個人 feature branch |

**重要**：`git reset` 只能用在本地，不能改寫已推送的遠端歷史。遠端撤銷用 `git revert`。

## Git Config 速查

```bash
git config --global user.name "Your Name"
git config --global user.email "email@example.com"
git config --global alias.co checkout
git config --global alias.st status
git config --list
```

## 連結

- [[cicd-pipeline]] — Git tag 觸發的 CI/CD 流程
- [[argocd]] — GitOps 以 Git 為單一事實來源
