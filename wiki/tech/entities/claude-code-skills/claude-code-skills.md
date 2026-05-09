---
type: entity
domain: tech
tags:
  - claude-code
  - ai-tools
  - slash-commands
  - automation
sources: []
created: 2026-05-09
updated: 2026-05-09
---

# Claude Code Skills

Claude Code Skills 是用 Markdown 定義的自訂 slash command，供 Claude Code CLI 呼叫。

## 來源位置

Skills 由 Anthropic 或使用者自行建立，存放路徑：

| 層級 | 路徑 | 說明 |
| --- | --- | --- |
| 使用者全域 | `~/.claude/skills/` | 適用所有專案 |
| 專案 | `.claude/skills/` | 僅限當前 repo |
| 內建 / 平台提供 | 由 Claude Code 系統注入 | 平台預裝，不在本機路徑 |

## Skill 檔案格式

每個 skill 是一個 `.md` 檔，以 frontmatter 宣告 metadata，其餘內容就是給 Claude 的執行指令：

```markdown
---
name: skill-name
description: 一句話說明（顯示在 /help 清單）
---

# Skill 名稱

這裡寫給 Claude 的指令與執行步驟...
```

## 呼叫方式

```text
/skill-name              # 無參數
/skill-name <args>       # 帶參數，args 以 <command-args> 注入至指令文字
```

Claude Code 會將 skill 的 Markdown 指令、`<command-args>` 內容，以及當前對話 context 一起送給 Claude 執行。

## Skills vs Memory vs Hooks

| 機制 | 用途 | 觸發方式 |
| --- | --- | --- |
| **Skills** | 封裝重複性任務流程 | 使用者手動 `/skill-name` |
| **Memory** | 跨對話持久化知識 | 自動讀取或 Claude 主動寫入 |
| **Hooks** | 工具事件的 shell 副作用 | 系統事件（工具呼叫前後） |

## 適用時機

- 有固定步驟需要每次重複執行（如 code review、寫筆記、設定環境）
- 想讓 Claude 遵循特定流程或格式而不必每次重新說明
- 需要在多個專案共用相同的任務模板

## 注意事項

- Skill 指令中如果有 `<command-args>` 佔位符，呼叫時帶的參數才會正確注入
- 未在 `~/.claude/skills/` 或 `.claude/skills/` 找到的 skill 名稱不能呼叫——Claude 不會憑記憶創造不存在的 skill
- 平台注入的 skills（如 `write-tutorial`）由 Claude Code 環境提供，使用者無需自行建檔

## 連結

- [[git]] — 類似 Git hook 概念（事件驅動的自動化）
- [[kubectl]] — CLI 工具設計參考
