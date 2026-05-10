---
tags: [database, oracle, sql]
---

> 關聯：[[oracle]]

# Oracle CMD 指令筆記

SQL教學：[http://faculty.stust.edu.tw/~jehuang/oracle/ch1/1-1.htm](http://faculty.stust.edu.tw/~jehuang/oracle/ch1/1-1.htm)

### 伺服器開關

[https://ithelp.ithome.com.tw/articles/10156813](https://ithelp.ithome.com.tw/articles/10156813)

oracle 資料庫可分成四個狀態：shutdown, nomonut, monut, open。

**nomonut：**

1.查詢SPFILE<SID>.ora -> SPFILE.ora ->INIT<SID>.ora (儲存資料庫啟動時相關參數)

2.allcating the SGA

3.啟動背景作業

4.開啟alert<SID>.log，並且開始記錄

**mount****：**

1.在指定的參數檔案中，定義與開啟control file

2.從control file 中取得data file與redo log的狀態與名稱(並檢查是否存在)

在這個階段可以執行以下作業:

1.renaming data file

2.可以調整redo log 是否開啟achiveing mode相關選項

3.進行完逞的資料庫備份與還原作業

**open：**

顧名思義就是讓使用者可以連線到資料庫進行作業，包含開啟線上的data file 與redo log

若在data file 與online redo log不存在的時候開啟資料庫，oracle會告知錯誤訊息(若有必要，系統會進行環原)

**shutdown：**

分成四種模式：normal, transactional, immediate, abort 差別在于

normal:等待session斷線

transactional:等待transaction完成

immediate:不等待，所有未commit的transaction都會被roll back

abort:立即關閉，但在下次啟動前需要修復資料庫。

### CMD 語法

---

sqlplus

show parameter sga; --显示内存分配情况

alter system set sga_max_size=200m scope=spfile; --修改占用内存的大小

exit 登出

### 登入指令

sqlplus account/password@host/dbSid，

sqlplus account/password@host/dbSid as sysdba

sqlplus sys/shengichen@140.113.59.168/xe as sysdba

sqlplus sys/shengichen@140.113.59.168/umc as sysdba

> account: 帳號
> 
> 
> password: 密碼
> 
> host: 資料庫主機位置
> 
> dbSID: 資料庫 SID
> 
> 第一個"/":帳號與密碼分隔
> 
> 第二個"/":位置與SID分隔
> 
> "@":密碼與主機位置分隔
> 

sqlplus alter session set "_ORACLE_SCRIPT"=true;

CREATE USER AUO IDENTIFIED BY oracle;

### 啟動兩個Oracle服務，一個是 Listener，一個是 Servcie

[https://ithelp.ithome.com.tw/articles/10156813](https://ithelp.ithome.com.tw/articles/10156813)

```
cmd-->sqlplus /nolog
cmd-->set ORALCE_SID=HRKF
sql-->connect / as sysdba
sql-->startup

```

參考：

[https://dotblogs.com.tw/kinanson/2017/05/06/090718](https://dotblogs.com.tw/kinanson/2017/05/06/090718)

[https://kknews.cc/zh-tw/code/ro2y6rn.html](https://kknews.cc/zh-tw/code/ro2y6rn.html)

[http://shaurong.blogspot.com/2022/11/oracle-database-21c-213-standard-win2022.html](http://shaurong.blogspot.com/2022/11/oracle-database-21c-213-standard-win2022.html)

[http://www.wellife.com.tw/blog/2015/07/28/dlp-安裝與建置-01-安裝和建立-oracle-資料庫/](http://www.wellife.com.tw/blog/2015/07/28/dlp-%E5%AE%89%E8%A3%9D%E8%88%87%E5%BB%BA%E7%BD%AE-01-%E5%AE%89%E8%A3%9D%E5%92%8C%E5%BB%BA%E7%AB%8B-oracle-%E8%B3%87%E6%96%99%E5%BA%AB/)

[https://blog.hungwin.com.tw/oracle-11gr2-install/](https://blog.hungwin.com.tw/oracle-11gr2-install/)

最重要的：

[https://www.123yun.com/article/672.html](https://www.123yun.com/article/672.html)

[http://bradctchen.blogspot.com/2019/07/oracle-tnstnsnamesora.html](http://bradctchen.blogspot.com/2019/07/oracle-tnstnsnamesora.html)[https://medium.com/@neil_tsai/ora-12154-tns-無法解析指定的連線-id-ff5cdbb144ab](https://medium.com/@neil_tsai/ora-12154-tns-%E7%84%A1%E6%B3%95%E8%A7%A3%E6%9E%90%E6%8C%87%E5%AE%9A%E7%9A%84%E9%80%A3%E7%B7%9A-id-ff5cdbb144ab)

權限：

[http://www.aspphp.online/shujuku/oraclesjk/oraclezs/201701/230000.html](http://www.aspphp.online/shujuku/oraclesjk/oraclezs/201701/230000.html)

[http://taichitech.blogspot.com/2013/08/oracle.html](http://taichitech.blogspot.com/2013/08/oracle.html)

### 監聽器 cmd指令

---

| cmd 指令 | 功能 |
| --- | --- |
| lsnrctl status |  看狀態 |
| lsnrctl stop |  關 |
| lsnrctl start |  開 |

### 資料庫操作

---

alter user `User名稱` identified by `User名稱` account unlock;

alter user ESCP_GUI identified by ESCP_GUI  account unlock;

[https://DESKTOP-AOMHV0K:5500/em](https://desktop-aomhv0k:5500/em)

### client 端設定

---

oracle卸了安裝，報 [INS-32025] 所選安裝與指定 Oracle 主目錄中已安裝的軟體衝突” 的問題 這個錯誤

解決方案：當我再次重裝的時候，選擇之前安裝的目錄（已經刪除乾淨了），就出現了 “[INS-32025] 所選安裝與指定 Oracle 主目錄中已安裝的軟體衝突” 的問題。

解決辦法：刪除C:\Program Files (x86)\Oracle\Inventory\ContentsXML目錄下的inventory.xml 檔案即可。（附帶改檔案內容，該目錄位址在這裡被佔用了，所以會報錯） 我是直接把oracle下面的檔案都刪了