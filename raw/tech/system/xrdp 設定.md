# xrdp 設定

# 網路連線資訊查詢

### 查ip

```bash
ip addr show
```

### 查詢Port

```bash
sudo ss -tuln
```

# 改Port

1. 使用超級用戶權限（或  root 權限）打開文件編輯器，例如 nano：
    
    ```bash
    sudo nano /etc/xrdp/xrdp.ini
    ```
    
2. 在 `[xrdp1]` 部分中找到 `port` 一行，預設情況下它應該是 `3389`：
    
    ```bash
    port=3389 #修改成欲改變的端口
    ```
    
3. 修改完成後，保存並關閉文件。
4. 重新啟動 xrdp 服務以應用新的設置
    
    ```bash
    sudo systemctl restart xrdp
    ```