# 倉庫（Repository）

倉庫（Repository）是集中存放映像檔的地方。

一個容易混淆的概念是註冊伺服器（Registry）。實際上註冊伺服器是管理倉庫的具體伺服器，每個伺服器上可以有多個倉庫，而每個倉庫下面有多個映像檔。從這方面來說，倉庫可以被認為是一個具體的專案或目錄。例如對於倉庫位址 `dl.dockerpool.com/ubuntu` 來說，`dl.dockerpool.com` 是註冊伺服器位址，`ubuntu` 是倉庫名。

大部分時候，並不需要嚴格區分這兩者的概念。

# **Docker Hub**

目前 Docker 官方維護了一個公共倉庫 [Docker Hub](https://hub.docker.com/)，其中已經包括了超過 15,000 的映像檔。大部分需求都可以透過在 Docker Hub 中直接下載映像檔來實作。

## **登錄**

- 可以透過執行 `docker login` 命令來輸入使用者名稱、密碼和電子信箱來完成註冊和登錄。
- 註冊成功後，本地使用者目錄的 `.dockercfg` 中將保存使用者的認證訊息。

## **基本操作**

使用者無需登錄即可透過 `docker search` 命令來查詢官方倉庫中的映像檔，並利用 `docker pull` 命令來將它下載到本地。 例如以 centos 為關鍵字進行搜尋：

```
$ sudo docker search centos
NAME                                            DESCRIPTION                                     STARS     OFFICIAL   AUTOMATED
centos                                          The official build of CentOS.                   465       [OK]
tianon/centos                                   CentOS 5 and 6, created using rinse instea...   28
blalor/centos                                   Bare-bones base CentOS 6.5 image                6                    [OK]
saltstack/centos-6-minimal                                                                      6                    [OK]
tutum/centos-6.4                                DEPRECATED. Use tutum/centos:6.4 instead. ...   5                    [OK]
...
```

可以看到顯示了很多包含關鍵字的映像檔，其中包括映像檔名字、描述、星級（表示該映像檔的受歡迎程度）、是否官方建立、是否自動建立。 官方的映像檔說明是官方專案組建立和維護的，automated 資源允許使用者驗證映像檔的來源和內容。

根據是否是官方提供，可將映像檔資源分為兩類。 一種是類似 centos 這樣的基礎映像檔，被稱為基礎或根映像檔。這些基礎映像檔是由 Docker 公司建立、驗證、支援、提供。這樣的映像檔往往使用單個單詞作為名字。 還有一種類型，比如 `tianon/centos` 映像檔，它是由 Docker 的使用者建立並維護的，往往帶有使用者名稱前綴。可以透過前綴 `user_name/` 來指定使用某個使用者提供的映像檔，比如 tianon 使用者。

另外，在查詢的時候透過 `-s N` 參數可以指定僅顯示評價為 `N` 星以上的映像檔。

下載官方 centos 映像檔到本地。

```
$ sudo docker pull centos
Pulling repository centos
0b443ba03958: Download complete
539c0211cd76: Download complete
511136ea3c5a: Download complete
7064731afe90: Download complete
```

使用者也可以在登錄後透過 `docker push` 命令來將映像檔推送到 Docker Hub。

# **私有倉庫**

有時候使用 Docker Hub 這樣的公共倉庫可能不方便，使用者可以建立一個本地倉庫供私人使用。本節介紹如何使用本地倉庫。 `docker-registry` 是官方提供的工具，可以用於建立私有的映像檔倉庫。

## **安裝執行 docker-registry**

### **容器執行**

在安裝了 Docker 後，可以透過取得官方 registry 映像檔來執行。

```
$ sudo docker run -d -p 5000:5000 registry
```

這將使用官方的 registry 映像檔來啟動本地的私有倉庫。使用者可以透過指定參數來設定私有倉庫位置，例如設定映像檔儲存到 Amazon S3 服務。

```
$ sudo docker run \
         -e SETTINGS_FLAVOR=s3 \
         -e AWS_BUCKET=acme-docker \
         -e STORAGE_PATH=/registry \
         -e AWS_KEY=AKIAHSHB43HS3J92MXZ \
         -e AWS_SECRET=xdDowwlK7TJajV1Y7EoOZrmuPEJlHYcNP2k4j49T \
         -e SEARCH_BACKEND=sqlalchemy \
         -p 5000:5000 \
         registry
```

此外，還可以指定本地路徑（如 `/home/user/registry-conf` ）下的設定檔案。

```
$ sudo docker run -d -p 5000:5000 -v /home/user/registry-conf:/registry-conf -e DOCKER_REGISTRY_CONFIG=/registry-conf/config.yml registry
```

預設情況下，倉庫會被建立在容器的 `/tmp/registry` 下。可以透過 `-v` 參數來將映像檔檔案存放在本地的指定路徑。 例以下面的例子將上傳的映像檔放到 `/opt/data/registry` 目錄。

```
$ sudo docker run -d -p 5000:5000 -v /opt/data/registry:/tmp/registry registry
```

### **本地安裝**

對於 Ubuntu 或 CentOS 等發行版，可以直接透過套件庫安裝。

- Ubuntu
    
    ```
    $ sudo apt-get install -y build-essential python-dev libevent-dev python-pip liblzma-dev swig
    $ sudo pip install docker-registry
    ```
    

也可以從 [docker-registry](https://github.com/docker/docker-registry) 專案下載原始碼進行安裝。

```
$ sudo apt-get install build-essential python-dev libevent-dev python-pip libssl-dev liblzma-dev libffi-dev
$ git clone https://github.com/docker/docker-registry.git
$ cd docker-registry
$ sudo python setup.py install
```

然後修改設定檔案，主要修改 dev 模板段的 `storage_path` 到本地的儲存倉庫的路徑。

```
$ cp config/config_sample.yml config/config.yml
```

之後啟動 Web 服務。

```
$ sudo gunicorn -c contrib/gunicorn.py docker_registry.wsgi:application
```

或者

```
$ sudo gunicorn --access-logfile - --error-logfile - -k gevent -b 0.0.0.0:5000 -w 4 --max-requests 100 docker_registry.wsgi:application
```

此時使用連結本地的 5000 連接埠，看到輸出 docker-registry 的版本訊息說明執行成功。

- 註：`config/config_sample.yml` 檔案是範例設定檔案。

## **在私有倉庫上傳、下載、搜尋映像檔**

1. 建立好私有倉庫之後，就可以使用 `docker tag` 來標記一個映像檔，然後推送它到倉庫，別的機器上就可以下載下來了。例如私有倉庫位址為 `192.168.7.26:5000`。
2. 先在本機查看已有的映像檔。

```
$ sudo docker images
REPOSITORY                        TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
ubuntu                            latest              ba5877dc9bec        6 weeks ago         192.7 MB
ubuntu                            14.04               ba5877dc9bec        6 weeks ago         192.7 MB
```

1. 使用`docker tag` 將 `ba58` 這個映像檔標記為 `192.168.7.26:5000/test`（格式為 `docker tag IMAGE[:TAG] [REGISTRYHOST/][USERNAME/]NAME[:TAG]`）。

```
$ sudo docker tag ba58 192.168.7.26:5000/test
root ~ # docker images
REPOSITORY                        TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
ubuntu                            14.04               ba5877dc9bec        6 weeks ago         192.7 MB
ubuntu                            latest              ba5877dc9bec        6 weeks ago         192.7 MB
192.168.7.26:5000/test            latest              ba5877dc9bec        6 weeks ago         192.7 MB
```

1. 使用 `docker push` 上傳標記的映像檔。
    
    ```
    $ sudo docker push 192.168.7.26:5000/test
    The push refers to a repository [192.168.7.26:5000/test] (len: 1)
    Sending image list
    Pushing repository 192.168.7.26:5000/test (1 tags)
    Image 511136ea3c5a already pushed, skipping
    Image 9bad880da3d2 already pushed, skipping
    Image 25f11f5fb0cb already pushed, skipping
    Image ebc34468f71d already pushed, skipping
    Image 2318d26665ef already pushed, skipping
    Image ba5877dc9bec already pushed, skipping
    Pushing tag for rev [ba5877dc9bec] on {http://192.168.7.26:5000/v1/repositories/test/tags/latest}
    ```
    
2. 用 curl 查看倉庫中的映像檔。
    
    ```
    $ curl http://192.168.7.26:5000/v1/search
    {"num_results": 7, "query": "", "results": [{"description": "", "name": "library/miaxis_j2ee"}, {"description": "", "name": "library/tomcat"}, {"description": "", "name": "library/ubuntu"}, {"description": "", "name": "library/ubuntu_office"}, {"description": "", "name": "library/desktop_ubu"}, {"description": "", "name": "dockerfile/ubuntu"}, {"description": "", "name": "library/test"}]}
    ```
    
    這裡可以看到 `{"description": "", "name": "library/test"}`，表明映像檔已經被成功上傳了。
    
3. 現在可以到另外一臺機器去下載這個映像檔。
    
    ```
    $ sudo docker pull 192.168.7.26:5000/test
    Pulling repository 192.168.7.26:5000/test
    ba5877dc9bec: Download complete
    511136ea3c5a: Download complete
    9bad880da3d2: Download complete
    25f11f5fb0cb: Download complete
    ebc34468f71d: Download complete
    2318d26665ef: Download complete
    $ sudo docker images
    REPOSITORY                         TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
    192.168.7.26:5000/test             latest              ba5877dc9bec        6 weeks ago         192.7 MB
    ```
    
4. 可以使用 [這個腳本](https://github.com/yeasy/docker_practice/raw/master/_local/push_images.sh) 批次上傳本地的映像檔到註冊伺服器中，預設為本地註冊伺服器 `127.0.0.1:5000`。例如：
    
    ```
    $ wget https://github.com/yeasy/docker_practice/raw/master/_local/push_images.sh; sudo chmod a+x push_images.sh
    $ ./push_images.sh ubuntu:latest centos:centos7
    The registry server is 127.0.0.1
    Uploading ubuntu:latest...
    The push refers to a repository [127.0.0.1:5000/ubuntu] (len: 1)
    Sending image list
    Pushing repository 127.0.0.1:5000/ubuntu (1 tags)
    Image 511136ea3c5a already pushed, skipping
    Image bfb8b5a2ad34 already pushed, skipping
    Image c1f3bdbd8355 already pushed, skipping
    Image 897578f527ae already pushed, skipping
    Image 9387bcc9826e already pushed, skipping
    Image 809ed259f845 already pushed, skipping
    Image 96864a7d2df3 already pushed, skipping
    Pushing tag for rev [96864a7d2df3] on {http://127.0.0.1:5000/v1/repositories/ubuntu/tags/latest}
    Untagged: 127.0.0.1:5000/ubuntu:latest
    Done
    Uploading centos:centos7...
    The push refers to a repository [127.0.0.1:5000/centos] (len: 1)
    Sending image list
    Pushing repository 127.0.0.1:5000/centos (1 tags)
    Image 511136ea3c5a already pushed, skipping
    34e94e67e63a: Image successfully pushed
    70214e5d0a90: Image successfully pushed
    Pushing tag for rev [70214e5d0a90] on {http://127.0.0.1:5000/v1/repositories/centos/tags/centos7}
    Untagged: 127.0.0.1:5000/centos:centos7
    Done
    ```
    
    # **設定檔案**
    
    Docker 的 Registry 利用設定檔案提供了一些倉庫的模組（flavor），使用者可以直接使用它們來進行開發或生產部署。
    
    ## **模組**
    
    在 `config_sample.yml` 檔案中，可以看到一些現成的模組段：
    
    - `common`：基礎設定
    - `local`：儲存資料到本地檔案系統
    - `s3`：儲存資料到 AWS S3 中
    - `dev`：使用 `local` 模組的基本設定
    - `test`：單元測試使用
    - `prod`：生產環境設定（基本上跟s3設定類似）
    - `gcs`：儲存資料到 Google 的雲端
    - `swift`：儲存資料到 OpenStack Swift 服務
    - `glance`：儲存資料到 OpenStack Glance 服務，本地檔案系統為後備
    - `glance-swift`：儲存資料到 OpenStack Glance 服務，Swift 為後備
    - `elliptics`：儲存資料到 Elliptics key/value 儲存
    
    使用者也可以新增自訂的模版段。
    
    預設情況下使用的模組是 `dev`，要使用某個模組作為預設值，可以新增 `SETTINGS_FLAVOR` 到環境變數中，例如
    
    ```
    export SETTINGS_FLAVOR=dev
    ```
    
    另外，設定檔案中支援從環境變數中載入值，語法格式為 `_env:VARIABLENAME[:DEFAULT]`。
    
    ## **範例設定**
    
    ```
    common:
        loglevel: info
        search_backend: "_env:SEARCH_BACKEND:"
        sqlalchemy_index_database:
            "_env:SQLALCHEMY_INDEX_DATABASE:sqlite:////tmp/docker-registry.db"
    
    prod:
        loglevel: warn
        storage: s3
        s3_access_key: _env:AWS_S3_ACCESS_KEY
        s3_secret_key: _env:AWS_S3_SECRET_KEY
        s3_bucket: _env:AWS_S3_BUCKET
        boto_bucket: _env:AWS_S3_BUCKET
        storage_path: /srv/docker
        smtp_host: localhost
        from_addr: docker@myself.com
        to_addr: my@myself.com
    
    dev:
        loglevel: debug
        storage: local
        storage_path: /home/myself/docker
    
    test:
        storage: local
        storage_path: /tmp/tmpdockertmp
    ```
    
    ## **選項**