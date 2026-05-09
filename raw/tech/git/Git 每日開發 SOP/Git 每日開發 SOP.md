# Git 每日開發 SOP

## 一、建議 SOP

### 🔒 Branch Policy（最重要）

| 分支 | 用途 | 規則 |
| --- | --- | --- |
| `main` | 穩定、可發佈版本 | **不直接開發** |
| `dev` | 日常整合分支 | 日常工作基準 |
| `feature/*` | 功能開發 | 一個功能一支 |

## 二、每天開發的標準流程

### 0️⃣ 開始前（每天一次）

```bash
git checkout dev
git pull origin dev
```

目的： 保證是從 **最新 dev** 開始工作

---

### 1️⃣ 開新功能（一定要做）

```bash
git checkout -b feature/inspector-ui
```

規則：

- 一個功能一支 branch
- 名字有語意（不要 `test1`）

---

### 2️⃣ 開發中（小步 commit）

```bash
git status
git add .
git commit -m "feat: inspector UI drag & resize"
```

建議：

- commit 小且可回滾
- 不要一次塞一堆功能

---

### 3️⃣ 功能完成 → 回 dev

```bash
git checkout dev
git pull origin dev# 確保 dev 是最新
git merge feature/inspector-ui
```

- 若有衝突 → 解在這裡
- merge 完才 push

---

### 4️⃣ 推到遠端

```bash
git push origin dev
```

⚠️ **這裡不應該再出現 force**

---

### 5️⃣ 清理 feature

```bash
git branch -d feature/inspector-ui
git push origin --delete feature/inspector-ui
```