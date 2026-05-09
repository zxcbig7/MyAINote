---
type: entity
domain: tech
tags: [linux, ubuntu, cli, sysadmin]
sources:
  - raw/tech/system/Linux 觀念.md
  - raw/tech/system/Ubuntu 筆記.md
created: 2026-05-03
updated: 2026-05-03
---

# Linux

Linux 是開源的 Unix-like 作業系統核心。Ubuntu 是最常用的 Linux 發行版，適合伺服器與開發環境。

## 目錄樹結構（FHS）

- 所有資料以**檔案**形態呈現
- 根目錄 `/` 是起點，所有路徑從此出發
- 目錄是一把**鑰匙（x 權限）**，沒有就無法進入

| 目錄 | 用途 |
| --- | --- |
| `/` | 根目錄，與開機系統有關 |
| `/home` | 使用者家目錄 |
| `/etc` | 系統設定檔（不可分享，不變） |
| `/usr` | 軟體安裝位置 |
| `/var` | 可變動資料（log、mail） |
| `/tmp` | 暫存檔 |
| `/boot` | 開機核心相關檔案 |

**掛載（mount）**：把磁碟分割槽連結到目錄樹的某個目錄（掛載點）。`/etc/fstab` 記錄開機自動掛載設定。

## 檔案權限

```
drwxr-xr--. 1 root users 4096 Jun 25 .ssh
│└─┬─┘└─┬─┘└─┬─┘
│  │    │    └── others 權限
│  │    └─────── group 權限
│  └──────────── owner 權限
└────────────── 類型（d=目錄 -=檔案 l=連結）

r=4（讀）  w=2（寫）  x=1（執行）
chmod 755 file   # owner=rwx(7), group=rx(5), others=rx(5)
chmod u+x file   # 加入 owner 執行權限
chown user:group file
chgrp group file
```

## 常用指令

### 目錄與檔案

```bash
pwd                    # 查看當前目錄
ls -la                 # 列出所有檔案（含隱藏，詳細資訊）
cd /path               # 切換目錄
mkdir -p /a/b/c        # 建立多層目錄
rm -rf dir             # 刪除目錄（遞迴，強制）
cp -r src dst          # 複製目錄
mv src dst             # 移動 / 重命名
cat file               # 顯示檔案內容
grep "keyword" file    # 搜尋字串（-n 顯示行號，-r 遞迴）
find . -name "*.log"   # 搜尋檔案
```

### 使用者管理

```bash
sudo adduser username          # 新增使用者
sudo deluser username          # 刪除使用者
sudo passwd username           # 設定密碼
su - username                  # 切換使用者
sudo passwd root               # 設定 root 密碼
groups username                # 查看使用者所屬群組
sudo usermod -aG sudo username # 加入 sudo 群組
```

### 程序管理

```bash
ps -ef                         # 顯示所有程序
ps -ef | grep python           # 篩選特定程序
kill -9 <PID>                  # 強制殺死程序
top                            # 即時查看 CPU/Memory
nohup ./script.sh &            # 背景執行且不受終端關閉影響
```

### 系統服務

```bash
systemctl start nginx          # 啟動服務
systemctl stop nginx           # 停止服務
systemctl restart nginx        # 重啟服務
systemctl status nginx         # 查看狀態
systemctl enable nginx         # 設定開機自啟
```

### 網路

```bash
ip addr                        # 查看網路介面 IP
ping 192.168.1.1               # 測試連線
netstat -anp | grep 80         # 查看 port 使用狀況
ss -tlnp                       # 查看監聽 port（新版 netstat）
ssh user@192.168.1.12          # 遠端連線
scp file user@host:/path       # 複製檔案到遠端
wget <url>                     # 下載檔案
```

### 防火牆（ufw）

```bash
ufw enable                     # 啟用防火牆
ufw status                     # 查看狀態
ufw allow 22/tcp               # 開放 SSH port
ufw allow http                 # 開放 HTTP（80）
ufw delete allow http          # 刪除規則
```

## vi / vim 快速參考

```
# 模式切換
i / a / o   進入插入模式
Esc         回命令模式
:           進入底行模式

# 命令模式常用
dd          刪除一行
yy          複製一行
p           貼上
u           撤銷
/keyword    向下搜尋（n 繼續，N 反向）

# 底行模式
:wq         存檔並退出
:q!         不存檔強制退出
:set nu     顯示行號
:1,$s/old/new/g  全文替換
```

## 套件管理（apt）

```bash
apt update                     # 更新套件清單
apt install <package>          # 安裝套件
apt remove <package>           # 移除套件
apt list --installed           # 列出已安裝套件
```

## 關機 / 重啟

```bash
shutdown -h now                # 立即關機
shutdown -r +10 "10 mins"     # 10 分鐘後重啟並廣播訊息
reboot                         # 立即重啟
poweroff                       # 立即關機
sync; sync; sync; reboot       # 確保寫入後重啟
```

## 重定向與管道

```bash
command > file         # stdout 重定向到檔案（覆蓋）
command >> file        # stdout 追加
command 2> err.log     # stderr 重定向
command &> both.log    # stdout + stderr 重定向

# 管道：將前一個指令的 stdout 作為後一個的 stdin
ps -ef | grep python | grep -v grep
```

## 連結

- [[docker]] — Docker 容器基於 Linux kernel
- [[kubernetes]] — K8s 節點運行在 Linux 上
