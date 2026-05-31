---
type: concept
domain: tech
tags: [cron, scheduling, kubernetes, github-actions, linux, devops]
created: 2026-05-31
updated: 2026-05-31
---

# Cron Expression

Cron 表達式用來描述「何時執行某個排程任務」，廣泛應用於 Linux crontab、Kubernetes CronJob、GitHub Actions 等系統。

## 格式：5 欄 vs 6 欄

| 格式 | 欄位順序 | 使用場景 |
| --- | --- | --- |
| **5 欄**（標準） | 分 時 日 月 週 | Linux crontab、GitHub Actions |
| **6 欄**（擴充） | 秒 分 時 日 月 週 | Spring / Quartz / AWS EventBridge |

```
# 5 欄標準格式
┌───────── 分鐘 (0–59)
│ ┌─────── 小時 (0–23)
│ │ ┌───── 日期 (1–31)
│ │ │ ┌─── 月份 (1–12)
│ │ │ │ ┌─ 星期 (0–7，0 和 7 都是週日)
│ │ │ │ │
* * * * *
```

## 各欄位合法值

| 欄位 | 範圍 | 說明 |
| --- | --- | --- |
| 秒（6 欄限定） | 0–59 | |
| 分鐘 | 0–59 | |
| 小時 | 0–23 | |
| 日期 | 1–31 | |
| 月份 | 1–12 或 JAN–DEC | |
| 星期 | 0–7 或 SUN–SAT | 0 與 7 皆為週日 |

## 特殊字元

| 字元 | 意義 | 範例 |
| --- | --- | --- |
| `*` | 任意值 | `* * * * *`：每分鐘 |
| `/` | 步進（每隔 N） | `*/15 * * * *`：每 15 分鐘 |
| `-` | 範圍 | `0 9-17 * * *`：9 點到 17 點整點 |
| `,` | 列舉 | `0 8,12,18 * * *`：8、12、18 點 |
| `?` | 不指定（日或週二擇一） | `0 0 15 * ?`：每月 15 日（不限週幾） |
| `L` | 最後一天（日欄：當月末；週欄：最後一個該週幾） | `0 0 L * *`：每月最後一天 |
| `W` | 最近的工作日 | `0 9 15W * *`：15 日最近的工作日 9 點 |
| `#` | 第 N 個週幾 | `0 10 * * 1#2`：每月第 2 個週一 |

> `?` 與 `L`、`W`、`#` 通常只有 Quartz 等 6 欄格式才支援，標準 crontab 不支援。

## 常用範例

```
# 每分鐘
* * * * *

# 每小時整點
0 * * * *

# 每天早上 8 點
0 8 * * *

# 每週一早上 9 點
0 9 * * 1

# 每月 1 日 0 點
0 0 1 * *

# 每 15 分鐘
*/15 * * * *

# 週一到週五（工作日）早上 8 點
0 8 * * 1-5

# 每天 8 點、12 點、18 點
0 8,12,18 * * *

# 每小時的第 0、15、30、45 分
0,15,30,45 * * * *
```

## Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: my-cronjob
  namespace: default
spec:
  schedule: "0 2 * * *"          # 每天凌晨 2 點（UTC）
  concurrencyPolicy: Forbid       # 上一個 Job 未完成時不新增
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: worker
              image: my-image:latest
              command: ["./run.sh"]
```

### concurrencyPolicy 選項

| 值 | 行為 |
| --- | --- |
| `Allow`（預設） | 允許並發執行 |
| `Forbid` | 跳過本次（上次未結束） |
| `Replace` | 刪除上次、執行本次 |

> K8s CronJob 時區預設為 **UTC**。1.27+ 支援 `spec.timeZone: "Asia/Taipei"` 指定時區。

## GitHub Actions Schedule

```yaml
on:
  schedule:
    - cron: "0 2 * * 1-5"    # UTC 週一到週五 02:00
```

注意事項：
- 時區固定為 **UTC**，台北時間需換算（UTC+8，`0 2 * * *` = 台北時間 10:00）
- GitHub 在高負載時可能延遲數分鐘觸發
- fork 的 repo 預設停用 schedule，需手動啟用

## 時區換算（UTC → Asia/Taipei）

台北時間 = UTC + 8

| 想要台北時間 | 填入 UTC cron |
| --- | --- |
| 08:00 | `0 0 * * *` |
| 12:00 | `0 4 * * *` |
| 18:00 | `0 10 * * *` |
| 23:00 | `0 15 * * *` |

## 推薦工具

- **crontab.guru** — 線上即時預覽 cron 表達式的下次觸發時間，支援自然語言說明

## 連結

- [[kubernetes]] — K8s CronJob 部署平台
- [[cicd-pipeline]] — GitHub Actions schedule 觸發 CI/CD
- [[linux]] — Linux crontab 原生排程
