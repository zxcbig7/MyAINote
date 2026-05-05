# LLM Wiki — 第二大腦架構規則

> **此檔案是本 wiki 的憲法。每次與本 vault 互動前先讀本檔，並嚴格遵循其中規則。**
> 你（LLM）負責所有寫入、整理、cross-link、bookkeeping。使用者只負責找來源、提問、決策方向。

---

## 三層架構

| 層 | 路徑 | 誰寫 | 性質 |
| --- | --- | --- | --- |
| Raw | `raw/` | 使用者 | 原始來源，**永不修改** |
| Wiki | `wiki/` | LLM | 合成知識，持續演化 |
| Schema | `CLAUDE.md`（本檔） | 雙方協作 | 規則、慣例、workflow |

外加兩個導航檔：

- `index.md` — 內容目錄（content-oriented）
- `log.md` — 時序日誌（append-only）

---

## 資料夾結構

```text
Notes/
├── CLAUDE.md              # 本檔（schema）
├── index.md               # 內容目錄
├── log.md                 # 時序日誌
├── raw/
│   ├── tech/              # 技術類來源
│   │   └── legacy-notes/  # 既有 17 篇筆記（已視為 ingested source）
│   ├── personal/          # 個人成長類來源
│   └── assets/            # 圖片、附件
└── wiki/
    ├── tech/
    │   ├── entities/      # 工具、框架、服務（kubernetes、argocd、react）
    │   ├── concepts/      # 抽象概念與模式（gitops、rbac、ssr）
    │   └── summaries/     # 每篇 source 對應的摘要頁
    ├── personal/
    │   ├── entities/      # 人物、專案、習慣
    │   ├── concepts/      # 思維框架、原則
    │   └── summaries/
    └── synthesis/         # 跨領域分析、比較、思考
```

不要動 `.obsidian/`（Obsidian vault 設定）。

---

## 命名規範

- 檔名一律 **kebab-case**：`argocd.md`、`gitops-workflow.md`
- 工具/技術概念優先用英文；個人主題（情緒、習慣）可用中文檔名
- entity 頁 = **名詞單數**（`kubernetes.md` 而非 `kubernetes-stuff.md`）
- summary 頁命名：`<source-basename>-summary.md`
- synthesis 頁用描述性短句：`gitops-vs-traditional-cicd.md`

---

## Frontmatter 規範

每個 wiki 頁面開頭必加：

```yaml
---
type: entity | concept | summary | synthesis
domain: tech | personal | cross
tags: [標籤陣列]
sources: [raw/tech/legacy-notes/argocd-tutorial.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

`sources` 列出本頁知識的來源檔（相對 vault root 路徑）。每次更新時 append 新 source。

---

## 內部連結

一律使用 Obsidian wikilinks：

- 簡單連結：`[[argocd]]`
- 別名連結：`[[gitops-workflow|GitOps 流程]]`
- 跨資料夾連結：Obsidian 自動解析，**不要寫完整路徑**

頁面結尾固定加一個 `## 連結` 區塊列出相關頁。

---

## 三大 Operation

### 1. Ingest — 匯入新 source

**觸發詞**：「ingest 這個」「讀這篇」「處理這個」「幫我消化」

步驟：

1. **讀取** raw/ 內的 source（必要時讀引用的圖檔）
2. **討論** 與使用者交流關鍵 takeaway，問清楚他想強調什麼
3. **寫 summary 頁** → `wiki/<domain>/summaries/<basename>-summary.md`
4. **更新或新建 entity / concept 頁**：
   - 該 source 提到的每個重要工具、概念都需要對應頁面
   - 既有頁面 → 補充新資訊，於 `sources:` 加入本 source
   - 新頁面 → 從零建立，含完整 frontmatter
5. **建立 cross-link**：新舊頁面雙向連結
6. **標註矛盾**：若新 source 與既有頁面衝突，於頁中以
   `> ⚠️ 矛盾：[[old-claim]] 主張 X，[[new-source-summary]] 主張 Y` 標註，並等待使用者裁決
7. **更新 `index.md`**：在對應分類加入新頁
8. **追加 `log.md`**：`## [YYYY-MM-DD] ingest | <source title>` + 1-3 行說明

### 2. Query — 提問

當使用者問問題：

1. 先讀 `index.md` 找線索
2. 讀相關 wiki 頁面（**不直接讀 raw**，除非需要查證原文）
3. 合成答案，引用 `[[wiki-page]]`
4. **若答案有保存價值** → 主動建議：「這個分析要不要存成 synthesis 頁？」
   - 同意 → 寫到 `wiki/synthesis/`，更新 index + log

### 3. Lint — 健檢

**觸發詞**：「lint」「健檢 wiki」「檢查」「整理」

檢查項目：

- 矛盾偵測：跨頁面主張衝突
- 過時主張：新 source 已推翻舊主張
- 孤兒頁面：無 inbound link 的頁
- 缺漏概念：被多次提及但無自己的頁面
- 缺漏 cross-link：應該連結卻沒連
- 提出值得追問的問題與可補的 source

輸出為一份 lint 報告，由使用者裁決逐項修復。

---

## index.md 維護規則

- 結構：依 `wiki/` 子分類列出每頁
- 每行格式：`- [[page-name]] — 一行 hook`
- 每次 ingest / synthesis 寫入後**立刻**更新

## log.md 維護規則

- **Append-only**，永不刪改舊條目
- 每筆開頭：`## [YYYY-MM-DD] <action> | <subject>`
- action 類型：`bootstrap`、`ingest`、`query`、`synthesis`、`lint`、`refactor`
- 一筆 1-3 行，記錄 what + why

---

## 語言規範

- wiki 內容用 **繁體中文** 為主
- Technical terms 保留英文（namespace、middleware、component、controller）
- 標題、frontmatter key、檔名用英文
- 引用原文（quote block）保留原語言

---

## 互動原則

1. **使用者只做**：找來源、提問、決策方向
2. **LLM 全包**：閱讀、摘要、合成、cross-link、bookkeeping
3. **每次對話開始**：先讀本檔 + `index.md`
4. **每次對話結束**：適度更新 wiki + `log.md`
5. **檔案從不靜默修改**：每次寫入後告訴使用者動了哪些檔
6. **不確定就問**：分類模糊、頁面是否合併、衝突如何裁決 → 一律先問
