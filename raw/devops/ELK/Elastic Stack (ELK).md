# ELK 核心功能
* 提供中心化的日誌記錄，能將雲環境中的日誌集中至單一可搜尋索引（Single Searchable Index）
* 串連多個來源的日誌與資料事件（Data Events），並應用於資安監控、根本原因分析等多種場景

# ELK 整體概要
ELK 是取自三個開源產品的字首作為縮寫分別為：Elasticsearch 、Logstash  和 Kibana 。
> 運作流程： 日誌搜集、儲存＆搜尋、可視化
> 系統流程：原始資料 → Logstash → Elastic Search → Kibana
> 說明：
> Logstash 收集並處理資料，將處理好的資料送入 Elasticsearch 進行儲存和索引，Kibana 從 Elasticsearch 獲取資料，進行可視化和分析。

# 各別系統說明
## 資料處理：[[Logstash]] (以及 Beat)
![[assets/Elastic Stack (ELK)/file-20260531224510612.webp|420]]
* 通常會搭配 Beats 一起看
* ELK 會先利用 Beats 搜集日誌，再將搜集後的 Raw Data （原始資料）傳送至 Logstash 中進行轉換與資料的預處理。
* Input Data / Transform Data / Stash Data
* 輕量開源的伺服端資料處理 pipeline
* 用動態搜索以找到正確資料，並即時轉換、傳送到指定的儲存裝置
* 不受資料來源格式或者架構影響
* 可以理解成幫助不同平台傳送給Elasticsearch資料儲存的前處理
* 能夠從多個資料源擷取、轉換、再將其傳送至「存放區」
## 集中儲存 ＆ 快速搜尋：Elasticsearch (ES)
* 是 ELK 的核心，可以理解成資料庫
* ES 為分散式、RESTful 的搜尋及分析的搜尋引擎
* ES 能集中儲存資料以便於做快速搜尋，並做關聯性的微調，及能輕易擴展的分析功能。
* 用於 Log, metrics, Trace data
* 有整合向量資料庫搜尋，可以做AI語義搜尋
### 重要組成
* Node - Elasticsearch 運作的實體
* Document - 主要處理的資料結構，JSON 格式儲存的一筆資料 (No SQL)
* Index - 將 Document 寫入Index 或者讀取 Document
	* schema-free
* Primary Shard - 實際儲存資料的單位
* Replica Shard - Shard 的副本，內容與 Shard 完全相同
### Comparison with [[RDMS]]
* ES 的 Indexes  DB 就是 Schema
* ES 的 Patterns 或 Types 對應 DB 的 Table
* ES 的 Documents 對應 DB 的 Rows
* ES  的 Fields  對應 DB 的 Columns
## 可視化：[[Kibana]]
* 將來自 Elasticsearch 的資料進行可視化，並建立客製化儀表板。
* 用於管理 Elastic Search
* Web based UI Dashboard
* Widgets/Visualization

