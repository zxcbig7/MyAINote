# Docker 部屬範例

# Windows 開發

## Visual Studio

1.  專案點右鍵 → 發佈 → 新增發行設定案 → 目標選擇**資料夾**
    
    ![Untitled](raw/Languages/CSS/Untitled.png)
    
    ![Untitled](raw/Languages/CSS/Untitled%201.png)
    
2. 確保發佈設定如下，才能在Linux系統上執行
    
    ![Untitled](raw/tech/git/Github%20心得/Untitled%202.png)
    
    <aside>
    💡 發佈完成後，在目標位置中的linux-x64那個資料夾就是要生成 Image 的檔案位置
    
    ![Untitled](raw/tech/git/Github%20心得/Untitled%203.png)
    
    </aside>
    

## Docker

### Step 1. 建立環境

在打算生成 Image 的資料夾中，放置 CPLEX 的`libcplex2211.so`檔案

![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%204.png)

<aside>
💡 可點擊以下檔案下載

[libcplex2211.zip](libcplex2211.zip)

**【補充】**

該檔案在Ubuntu 安裝Cplex的安裝位置裡面

![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%205.png)

</aside>

1. 在打算生成 Image 的資料夾中，撰寫 Dockerfile
    
    <aside>
    ⚠️ 在你的目錄下建立一個名為`Dockerfile`的文件
    
    </aside>
    
    ![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%206.png)
    
    <aside>
    ⚠️ **重要：**Dockerfile 不是 .txt 檔案，需要特別把副檔名刪除
    
    </aside>
    
    ![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%207.png)
    
    <aside>
    ⚠️ 記得將`你的應用程式.dll`替換為你的應用程式的DLL名稱。
    
    </aside>
    
    ```docker
    # 使用官方的 .NET 運行時Image作為基礎Image
    FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
    WORKDIR /app
    
    # 複製發佈的應用程式文件到工作目錄
    COPY . .
    
    # 設置Container啟動時執行的指令
    ENTRYPOINT ["dotnet", "【**這邊改你的應用程式**】.dll"]
    ```
    

### Step2. **建立Docker Image**

1. **在要生成 Image 的資料夾開啟命令提示字元（如圖右所示）**
    
    ![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%208.png)
    
    <aside>
    ⚠️ 留意目錄位置在執行程式的資料夾裡面
    
    </aside>
    
2. **建立 Docker Image：**
執行以下命令來構建Docker Image。
    
    ```
    docker build -t **your-app-name** .
    ```
    
    <aside>
    ⚠️ **your-app-name** 要改為區分Image的名稱
    
    </aside>
    
3. **上傳 Docker Image 到 Docker Hub：**
打算在不同的機器上使用相同的 Docker Image，須將其上傳到Docker Hub。
    
    ```
    docker push your-dockerhub-username/your-app-name
    ```
    
    <aside>
    ⚠️ **your-dockerhub-username** 改為Docker 使用者的名稱(需要註冊)
    **your-app-name** 改為Image名稱(跟上一指令的名稱一樣)
    
    </aside>
    
    <aside>
    ⚠️ 需要確保Windows電腦有安裝 Docker Desktop再上傳
    
    ![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%209.png)
    
    </aside>
    

## Docker 其他指令

1. 查詢主機有哪些 image
    
    ```docker
    docker image ls
    docker images -a
    ```
    
2. 刪除 image
    - 刪除特定 image
    
    ```csharp
    docker rmi <your-image-id>
    ```
    
    - 刪除所有 image
    
    ```csharp
    docker rmi $(docker images -q)。
    ```
    
3. 列出 Container
    
    ```csharp
    docker ps 
    ```
    
    - `-a` 这个选项用于列出所有容器，包括停止运行的。如果没有这个选项，则默认只列出在运行的容器。
    - `-q` 这个选项列出容器的数字 ID，而不是容器的所有信息。
4. 刪除 container
    - 強制停止 Container 運行 (force bridge)
        
        ```csharp
        docker rm -f
        ```
        
    - 停止所有 Container 運行
        
        ```csharp
        docker stop $(docker ps -a -q)
        ```
        
    - 刪除所有停止運行的 Container
        
        ```csharp
        docker rm $(docker ps -a -q)
        ```
        

# Ubuntu 執行

## 執行 Docker Container

```
sudo docker run --name **your-container-name** **your-dockerhub-username**/**your-app-name**
```

<aside>
⚠️ **your-container-name** 要改為區分Container的名稱

</aside>

## 重複執行同一個 Container

<aside>
⚠️ 如果重複執行上方指令會出現錯誤告訴你已經有相同的Container

![Untitled](raw/tech/git/SourseTree(Local)%20筆記/Untitled%2010.png)

</aside>

**所以需要執行以下操作刪除原本的Container**

1. 查詢所有Container(非必要，除非忘記Container名稱)
    
    ```docker
    sudo docker ps -a
    ```
    
    ![Untitled](Untitled%2011.png)
    
2. 刪除原本的Container
    
    ```docker
    docker rm **your-container-name**
    ```
    
    <aside>
    ⚠️ 刪除好之後就可以回到執行 Docker Container 的指令
    
    </aside>
    

---

# 結果

![messageImage_1719354795704.jpg](messageImage_1719354795704.jpg)