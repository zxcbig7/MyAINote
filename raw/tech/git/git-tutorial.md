# Git 操作筆記

## Merge Conflict 概念

Merge conflict 發生在兩個 branch 對同一個檔案做了不同的修改，git 無法自動決定保留哪個版本。

### Conflict 類型

| 類型 | 說明 |
|------|------|
| modify/modify | 兩邊都修改了同一個檔案 |
| rename/delete | 一邊 rename，另一邊 delete |
| rename/rename | 兩邊把同一個檔案 rename 成不同名稱 |
| modify/delete | 一邊修改，另一邊 delete |

`modify/modify` 會在檔案內出現 `<<<<<<<` 標記，其他類型不會。

---

## 解決 Conflict

### 查看衝突清單

```bash
git diff --name-only --diff-filter=U
```

### 術語

| 術語 | 說明 |
|------|------|
| Current / ours / HEAD | 你目前所在 branch 的版本 |
| Incoming / theirs / MERGE_HEAD | 合併進來的 branch 版本 |

### 選擇版本

```bash
# 採用 current branch（HEAD）的版本
git checkout HEAD -- <file>

# 採用 incoming branch 的版本
git checkout MERGE_HEAD -- <file>
```

### 刪除不再需要的檔案

```bash
git rm <file>
```

### 標記解決並 commit

```bash
git add .
git commit -m "merge: ..."
```

### 放棄整個 merge

```bash
git merge --abort
```

---

## 修改 Git 歷史

### 修改最後一個 commit

```bash
git commit --amend --no-edit   # 保留 commit message
git commit --amend -m "新訊息" # 改 commit message
```

`--amend` 不是修改舊 commit，而是用新 commit 取代它，hash 會改變。

### 從歷史移除特定檔案

```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <file>" \
  --prune-empty --tag-name-filter cat -- --all
```

移除後需 force push：
```bash
git push origin <branch> --force
```

---

## 移除敏感資料

若 secret 已 commit 進歷史，GitHub push protection 會擋下。

**解法：**
1. staged 刪除該檔案後執行 `git commit --amend`，新 commit 不含 secret
2. 使用 `git filter-branch` 從所有 commit 移除
3. Force push 覆蓋遠端歷史

> 即使移除，已洩漏的 secret 仍應視為不安全，應立即輪換。

---

## 常用指令

```bash
# 查看最近 commit
git log --oneline

# 查看 staged + unstaged 差異
git diff HEAD

# 確認某個 commit 包含哪些檔案
git show <commit-hash> --name-only

# 查看某個 commit 裡特定檔案的內容
git show <commit-hash>:<file-path>
```
