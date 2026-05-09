---
tags: [devops, docker, container]
---

> 關聯：[[docker]]

# Docker 部屬範例

## Windows 開發

### Visual Studio

1. 專案點右鍵 → 發佈 → 新增發行設定案 → 目標選擇 **資料夾**
2. 確保發佈設定可在 Linux 系統上執行

> 💡 發佈完成後，目標位置中的 `linux-x64` 資料夾就是要生成 Image 的檔案位置

### Docker

#### Step 1. 建立環境

在打算生成 Image 的資料夾中，放置 CPLEX 的 `libcplex2211.so` 檔案。

> 💡 可點擊以下檔案下載：[libcplex2211.zip](libcplex2211.zip)
>
> **【補充】** 該檔案在 Ubuntu 安裝 Cplex 的安裝位置裡面

1. 在打算生成 Image 的資料夾中，撰寫 Dockerfile

   > ⚠️ 在你的目錄下建立一個名為 `Dockerfile` 的文件
   >
   > **重要：** Dockerfile 不是 .txt 檔案，需要特別把副檔名刪除
   >
   > 記得將 `你的應用程式.dll` 替換為你的應用程式的 DLL 名稱

   ```docker
   # 使用官方的 .NET 運行時 Image 作為基礎 Image
   FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
   WORKDIR /app

   # 複製發佈的應用程式文件到工作目錄
   COPY . .

   # 設置 Container 啟動時執行的指令
   ENTRYPOINT ["dotnet", "【這邊改你的應用程式】.dll"]
   ```

#### Step 2. 建立 Docker Image

1. 在要生成 Image 的資料夾開啟命令提示字元

   > ⚠️ 留意目錄位置在執行程式的資料夾裡面

2. 建立 Docker Image：

   ```bash
   docker build -t your-app-name .
   ```

   > ⚠️ `your-app-name` 要改為區分 Image 的名稱

3. 上傳 Docker Image 到 Docker Hub（要在不同機器上使用相同 Image）：

   ```bash
   docker push your-dockerhub-username/your-app-name
   ```

   > ⚠️ `your-dockerhub-username` 改為 Docker 使用者的名稱（需要註冊）
   > `your-app-name` 改為 Image 名稱（跟上一指令的名稱一樣）
   >
   > 需要確保 Windows 電腦有安裝 Docker Desktop 再上傳

## Docker 其他指令

1. 查詢主機有哪些 image

   ```bash
   docker image ls
   docker images -a
   ```

2. 刪除 image

   ```bash
   # 刪除特定 image
   docker rmi <your-image-id>

   # 刪除所有 image
   docker rmi $(docker images -q)
   ```

3. 列出 Container

   ```bash
   docker ps
   ```

   - `-a` 列出所有容器，包括停止運行的（預設只列出運行中的）
   - `-q` 列出容器的數字 ID，而不是所有資訊

4. 刪除 container

   ```bash
   # 強制停止 Container 運行
   docker rm -f

   # 停止所有 Container 運行
   docker stop $(docker ps -a -q)

   # 刪除所有停止運行的 Container
   docker rm $(docker ps -a -q)
   ```

## Ubuntu 執行

### 執行 Docker Container

```bash
sudo docker run --name your-container-name your-dockerhub-username/your-app-name
```

> ⚠️ `your-container-name` 要改為區分 Container 的名稱

### 重複執行同一個 Container

> ⚠️ 如果重複執行上方指令會出現錯誤告訴你已經有相同的 Container

需要執行以下操作刪除原本的 Container：

1. 查詢所有 Container（非必要，除非忘記 Container 名稱）

   ```bash
   sudo docker ps -a
   ```

2. 刪除原本的 Container

   ```bash
   docker rm your-container-name
   ```

   > ⚠️ 刪除好之後就可以回到執行 Docker Container 的指令
