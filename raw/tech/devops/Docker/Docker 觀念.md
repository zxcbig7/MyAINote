# Docker 觀念

## 學習資源

- Docker 官方文檔: [https://docs.docker.com](https://docs.docker.com)
- Docker Hub: [https://hub.docker.com](https://hub.docker.com)
- 參考資料：[**Docker — 从入门到实践**](https://yeasy.gitbook.io/docker_practice)
- 參考資料：[https://philipzheng.gitbook.io/docker_practice](https://philipzheng.gitbook.io/docker_practice)

# Docker 核心概念

Docker 是一個開源的容器化平台,讓開發者可以將應用程式及其相依套件打包成標準化的容器,在任何環境中都能一致地運行。

- **Image:** 唯讀的模板,包含了運行應用程式所需的所有內容
- **Container:** 映像檔的執行實例,是一個輕量級、可攜帶的執行環境
- **Dockerfile:** 用來建立映像檔的腳本文件
- **Docker Hub:** Docker 官方的映像檔倉庫,可以分享和下載映像檔
- 開發者可以使用一個標準的 Image 來建立一套開發 Container
- 開發完成之後，維運人員可以直接使用這個Container來部署程式碼。

# **Image**

- 可理解成物件導向的 Class，用於定義程式執行的環境。
- 例如：一個Image可以包含一個完整的 ubuntu 作業系統環境，裡面僅安裝了 Apache 或使用者需要的其它應用程式。
- Docker 提供了一個很簡單的機制來建立Image或者更新現有的Image，使用者甚至可以直接從其他人那裡下載一個已經做好的Image來直接使用。
- 分層儲存
    
    **Image** 建構時會一層層建立，前一層是後一層的基礎。每一層建構完成後就不會再改變，後一層的任何變更只會發生在自己這一層。例如，刪除前一層檔案的操作，實際上並非真的刪除前一層的檔案，而是僅在當前層標記該檔案已刪除。容器最終運行時，雖然看不到這個檔案，但實際上該檔案會一直存在於映像檔中。因此，建構映像檔時需要特別注意：每一層應只包含該層需要新增的內容，任何多餘的檔案都應在該層建構結束前清理乾淨。分層儲存的特性讓映像檔的重用和客製化變得更容易。
    
    <aside>
    💡
    
    可以使用先前建構好的映像檔作為基礎層，然後進一步添加新的層來客製化所需內容，建構新的映像檔。
    
    </aside>
    

# **Container**

- Image可以用來建立 Docker Container。
- Docker 利用Container來執行應用。
- Container是從Image建立的執行實例。它可以被啟動、開始、停止、刪除。每個Container都是相互隔離的、保證安全的平台。
- 可以把Container看做是一個簡易版的 Linux 環境（包括 root 使用者權限、程式空間、使用者空間和網路空間等）和在其中執行的應用程式。
- 註：Image是唯讀的，Container在啟動的時候建立一層可寫層作為最上層。

# Repository

- 是集中存放 Image 檔案的地方
- 有時候會把Repository和Repository註冊伺服器（Registry）混為一談，並不嚴格區分。實際上，Repository 註冊伺服器上往往存放著多個Repository，每個 Repository 中又包含了多個Image，每個 Image 有不同的標籤（tag）。
- 庫分為公開Repository（Public）和私有Repository（Private）兩種形式。最大的公開Repository是 [Docker Hub](https://hub.docker.com/)，存放了數量龐大的Image供使用者下載。 大陸的公開Repository包括 [Docker Pool](http://www.dockerpool.com/) 等，可以提供大陸使用者更穩定快速的存取。
- 當然，使用者也可以在本地網路內建立一個私有Repository。當使用者建立了自己的Image之後就可以使用 `push` 命令將它上傳到公有或者私有Repository，這樣下次在另外一台機器上使用這個Image時候，只需要從Repository上 `pull` 下來就可以了。
- 註：Docker Repository的概念跟 [Git](http://git-scm.com/) 類似，註冊伺服器可以理解為 GitHub 這樣的託管服務。

---

# **Image說明**

[映像檔說明](映像檔說明%203158fda15f6f81c889c6e23a0e8809a9.md)

# **Container說明**

[**容器**](容器%203158fda15f6f8167b661ebd2f23fb5ca.md)

# Repository說明

[倉庫（Repository）](倉庫（Repository）%203158fda15f6f81898812de0da2ec4d6a.md)

# **資料管理**

[**資料管理**](資料管理%203158fda15f6f811ca9d1c884cde95b40.md)

# Container互連

[**容器互連**](容器互連%203158fda15f6f81faa067ee1ff28ea2a3.md)

# 實例說明

[實例說明](實例說明%203158fda15f6f8111b5e4c17f306051b2.md)

# Dockerfile 基本結構

[Dockerfile 基本結構](Dockerfile%20基本結構%203158fda15f6f818cb6c0e3511fd47b5d.md)

# 底層實作

[**底層實作**](底層實作%203158fda15f6f810bac3bc6b30d90d89e.md)

# **命令查詢**

[**命令查詢**](命令查詢%203158fda15f6f81438095f3c2733af35a.md)

# 基本常用指令

1. 更新 apt 資源列表
    
    ```bash
    sudo apt-get update
    sudo apt-get install \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    ```
    
2. 安裝 Docker 套件
    
    ```bash
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```
    
3. 啟動 Docker 服務
    
    ```bash
    sudo systemctl start docker
    ```
    
4. 確認 Docker 是否正常運作
    
    ```bash
    sudo systemctl status docker
    ```
    
5. 設定 Docker 自動啟動
    - 如果您希望 Docker 在每次開機時自動啟動
    
    ```bash
    sudo systemctl enable docker
    ```
    
6. 如果要測試是否能成功執行 Docker 可以執行以下指令
    
    ```bash
    sudo docker run hello-world
    ```
    

# **Image（Image）常用指令**

| 指令 | 動作 | 說明 |
| --- | --- | --- |
| docker images | 列出本機的Image | – a為列出完整Image層次資訊；-q為只列出ImageID；-tree代表列出Image不同層次間的樹狀關係。 |
| docker save/load | 將Image存入、匯出 |  |
| docker pull | 下載Image | 如果沒有加入registry位置，則預設從官方下載 |
| docker rmi | 刪除Image | 只能刪除本機中存放的Image |
| docker tag | 替本機Image加標籤 |  |
| docker build | 建立Image | 可從現有的Image為基礎，建立全新的Image |
| docker run | 執行Image |  |
| docker push | 上傳Image |  |

# **Container（Container）常用指令**

| 指令 | 動作 | 說明 |
| --- | --- | --- |
| create | 建立並執行Container |  |
| run | 新建或啟動 | 以image為基礎建立Container |
| kill | 刪除Container | 刪除正在執行中的Container，但Container依舊存在 |
| rm | 刪除Container | 刪除執行中或停止的Container，讓Container從此消失 |
| pause | 停止運作 | 停止正在運作中的Container，服務持續 |
| unpause | 再次啟動 | 讓停止運作的Container恢復運作 |
| stop | 停止運作 | 停止正在運作中的Container，服務中斷 |
| start | 啟動 | 啟動停止中的Container |
| inspect | 查看 | 檢查Container的狀態 |

# **Repository（Repository）常用指令**

| 指令 | 動作 | 說明 |
| --- | --- | --- |
| pull | 下載 |  |
| push | 上傳 |  |
| login | 登入 |  |
| tag | 標籤 |  |
| export | 匯出 |  |
| import | 匯入 |  |
| commit | Container存檔 |  |