---
tags: [devops, docker, container]
---

> 關聯：[[docker]]

# Dockerfile 基本結構

Dockerfile 由一行行命令語句組成，並且支援以 `#` 開頭的註解行。一般而言，Dockerfile 分為四部分：基底映像檔資訊、維護者資訊、映像檔操作指令和容器啟動時執行指令。例如：

```
# This dockerfile uses the ubuntu image
# VERSION 2 - EDITION 1
# Author: docker_user
# Command format: Instruction [arguments / command] ..

# 基本映像檔，必須是第一個指令
FROM ubuntu

# 維護者： docker_user <docker_user at email.com> (@docker_user)
MAINTAINER docker_user docker_user@email.com

# 更新映像檔的指令
RUN echo "deb http://archive.ubuntu.com/ubuntu/ raring main universe" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y nginx
RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf

# 建立新容器時要執行的指令
CMD /usr/sbin/nginx
```

其中，一開始必須指明作為基底的映像檔名稱，接下來說明維護者資訊（建議）。接著則是映像檔操作指令，例如 `RUN` 指令，`RUN` 指令將對映像檔執行相對應的命令。每運行一條 `RUN` 指令，映像檔就會新增一層。最後是 `CMD` 指令，指定執行容器時的操作命令。下面來看一個更複雜的例子：

```
# Nginx
#
# VERSION               0.0.1

FROM      ubuntu
MAINTAINER Victor Vieux <victor@docker.com>

RUN apt-get update && apt-get install -y inotify-tools nginx apache2 openssh-server

# Firefox over VNC
#
# VERSION               0.3

FROM ubuntu

# Install vnc, xvfb in order to create a 'fake' display and firefox
RUN apt-get update && apt-get install -y x11vnc xvfb firefox
RUN mkdir /.vnc
# Setup a password
RUN x11vnc -storepasswd 1234 ~/.vnc/passwd
# Autostart firefox (might not be the best way, but it does the trick)
RUN bash -c 'echo "firefox" >> /.bashrc'

EXPOSE 5900
CMD    ["x11vnc", "-forever", "-usepw", "-create"]

# Multiple images example
#
# VERSION               0.1

FROM ubuntu
RUN echo foo > bar
# Will output something like ===> 907ad6c2736f

FROM ubuntu
RUN echo moo > oink
# Will output something like ===> 695d7793cbe4

# You᾿ll now have two images, 907ad6c2736f with /bar, and 695d7793cbe4 with
# /oink.
```

# **指令**

指令的一般格式為 `INSTRUCTION arguments`，指令包括 `FROM`、`MAINTAINER`、`RUN` 等。

## **FROM**

- 格式：
    
    ```
    FROM <image>
    FROM <image>:<tag>
    ```
    
- 說明：第一條指令必須為 `FROM` 指令。並且，如果在同一個 Dockerfile 中建立多個映像檔時，可以使用多個 `FROM` 指令（每個映像檔一次）。

## **MAINTAINER**

- 格式：
    
    ```
    MAINTAINER <name>
    ```
    
- 說明：指定維護者訊息。

## **RUN**

- 格式：
    
    ```
    RUN <command>
    RUN ["executable", "<param1>", "<param2>"]
    ```
    
- 說明：
    - 前者將在 shell 終端中運行命令，即 `/bin/sh -c`；後者則使用 `exec` 執行。
    - 指定使用其它終端可以透過第二種方式實作，例如：`RUN ["/bin/bash", "-c", "echo hello"]`。
    - 每條 `RUN` 指令將在當前映像檔基底上執行指定命令，並產生新的映像檔。當命令較長時可以使用 `\` 來換行。

## **CMD**

- 格式：
    - `CMD ["executable","<param1>","<param2>"]` （使用 `exec` 執行，推薦使用)
    - `CMD <command> <param1> <param2>` 在 `/bin/sh` 中執行，使用在給需要互動的指令；
    - `CMD ["<param1>","<param2>"]` 提供給 `ENTRYPOINT` 的預設參數；
- 說明：
    - 指定啟動容器時執行的命令，每個 Dockerfile 只能有一條 `CMD` 命令。如果指定了多條命令，只有最後一條會被執行。
    - 如果使用者啟動容器時候指定了運行的命令，則會覆蓋掉 `CMD` 指定的命令。

## **EXPOSE**

- 格式：
    
    ```
    EXPOSE <port> [<port>...]
    ```
    
- 說明：
    - 設定 Docker 伺服器容器對外的埠號，供外界使用。
    - 在啟動容器時需要透過 `P`，Docker 會自動分配一個埠號轉發到指定的埠號。

## **ENV**

- 格式：
    
    ```
    ENV <key> <value>
    ```
    
- 說明：指定一個環境變數，會被後續 `RUN` 指令使用，並在容器運行時保持。
- 例如：
    
    ```
    ENV PG_MAJOR 9.3
    ENV PG_VERSION 9.3.4
    RUN curl -SL http://example.com/postgres-$PG_VERSION.tar.xz | tar -xJC /usr/src/postgress && …
    ENV PATH /usr/local/postgres-$PG_MAJOR/bin:$PATH
    ```
    

## **ADD**

- 格式：
    
    ```
    ADD <src> <dest>
    ```
    
- 說明：
    - 該命令將複製指定的 `<src>` 到容器中的 `<dest>`。
    - 其中 `<src>` 可以是 Dockerfile 所在目錄的相對路徑；也可以是一個 URL；還可以是一個 tar 檔案（其複製後會自動解壓縮）。

## **COPY**

- 格式：
    
    ```
    COPY <src> <dest>
    ```
    
- 說明：
    - 複製本地端的 `<src>`（為 Dockerfile 所在目錄的相對路徑）到容器中的 `<dest>`。
    - 當使用本地目錄為根目錄時，推薦使用 `COPY`。

## **ENTRYPOINT**

- 格式：
    
    ```
    ENTRYPOINT ["executable", "<param1>", "<param2>"]
    ENTRYPOINT <command> <param1> <param2>`
    ```
    
- 說明：
    - 指定容器啟動後執行的命令，並且不會被 `docker run` 提供的參數覆蓋。
    - 每個 Dockerfile 中只能有一個 `ENTRYPOINT`，當指定多個時，只有最後一個會生效。
    - 第二條指令要在 shell 中執行。

## **VOLUME**

- 格式：
    
    ```
    VOLUME ["/data"]
    ```
    
- 說明：建立一個可以從本地端或其他容器掛載的掛載點，一般用來存放資料庫和需要保存的資料等。

## **USER**

- 格式：
    
    ```
    USER daemon
    ```
    
- 說明：
    - 指定運行容器時的使用者名稱或 UID，後續的 `RUN` 也會使用指定使用者。
    - 當服務不需要管理員權限時，可以透過該命令指定運行使用者。並且可以在之前建立所需要的使用者，例如：`RUN groupadd -r postgres && useradd -r -g postgres postgres`。
    - 要臨時取得管理員權限可以使用 `gosu`，而不推薦 `sudo`。

## **WORKDIR**

- 格式：
    
    ```
    WORKDIR </path/to/workdir>
    ```
    
- 說明：
    - 為後續的 `RUN`、`CMD`、`ENTRYPOINT` 指令指定工作目錄。
    - 可以使用多個 `WORKDIR` 指令，後續命令如果參數是相對路徑，則會基於之前命令指定的路徑。例如：
        
        ```
        WORKDIR /a
        WORKDIR b
        WORKDIR c
        RUN pwd
        ```
        
        則最終路徑為 `/a/b/c`。
        

## **ONBUILD**

- 格式：
    
    Copy
    
    ```
    ONBUILD [instruction]
    ```
    
- 說明：
    - 指定當建立的映像檔作為其它新建立映像檔的基底映像檔時，所執行的操作指令。例如，Dockerfile 使用以下的內容建立了映像檔 `image-A`。
        
        ```
        [...]
        ONBUILD ADD . /app/src
        ONBUILD RUN /usr/local/bin/python-build --dir /app/src
        [...]
        ```
        
    - 如果基於 image-A 建立新的映像檔時，新的 Dockerfile 中使用 `FROM image-A`指定基底映像檔時，會自動執行 `ONBUILD` 指令內容，等於在後面新增了兩條指令。
        
        ```
        FROM image-A
        
        #Automatically run the following
        ADD . /app/src
        RUN /usr/local/bin/python-build --dir /app/src
        ```
        
    - 使用 `ONBUILD` 指令的映像檔，推薦在標籤中註明，例如 `ruby:1.9-onbuild`。
    
    # **建立映像檔**
    
    編輯完成 Dockerfile 之後，可以透過 `docker build` 命令建立映像檔。
    
    基本的格式為 `docekr build [選項] 路徑`，該命令將讀取指定路徑下（包括子目錄）的 Dockerfile，並將該路徑下所有內容發送給 Docker 伺服端，由伺服端來建立映像檔。因此一般會建議放置 Dockerfile 的目錄為空目錄。也可以透過 `.dockerignore` 檔案（每一行新增一條排除模式：exclusion patterns）來讓 Docker 忽略路徑下的目錄和檔案。
    
    要指定映像檔的標籤資訊，可以透過 `-t` 選項，例如：
    
    ```
    $ sudo docker build -t myrepo/myapp /tmp/test1/
    ```