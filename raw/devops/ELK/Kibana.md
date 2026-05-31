# 特色
* 透過Kibana介面管理elasticsearch
* 可以透過 [[Kibana Query Language (KQL)|KQL]] 語法做類似 SQL 的搜尋

# 常用功能
## **Dev Tools**

![[assets/Kibana/file-20260531215826878.png]]
Dev Tools 可以使用 Elasticsearch API，不論是要管理Cluster、Index，還是資料的查詢或API測試
以下圖為例，在左方區域輸入API，並點擊 ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAH3SURBVDhPrZRNTBNBFIC/7Q8IlCL/rVjEWEwQxLQGDNHEBD2ZeJYDF+PFgycuHvXq1bPe9GBMjPGGBhMjCWmEWCymKdFSbCgVUykgadntj7MwIna1rdAvmezkzew3781mnxIMx/NUEJOiQCWHECpiUrlhkpnuks5keBsN8ywU4MNKDDWblSvloYQiX/+4w3exLzz++J5wMoG7sZkLruMMODtx2Q/LHcUxZOgXWc19WyaUWGE8HOKB38eToB/f0iKb6halvqBBuCVKzuRy23P9+Xk1waPADPenJ3m1ME8k+b3oNRiEfyOV0ZhZjnJ38iUPZ30ERAXJdIqsPHgvZQl19FJTmsbT4CxjEy94Pj/H0o81tIJsyxbuJb6xzr2p19x5M44vtkgu/zvTfQl1cvk80/EoE5FPLCRXZfQAQh1N3GGVxUyt1SojBxAesli53NXNRdcJmmpqZXSfwp6Wdm6cGeR6/yCn25xUmy1y5T+EehdprqnjanevEA0wcsqDx9FBfVW13LFDSaFoINjES17HUa71erjpHeKKu4e2OttOqyrAILSazJjlRr2UTnsjl465RYnnuHX2vPi/W7b3/AuDsKO+gSNiOGx2+tudjPZ5uT00zHCXe/egYhi6zaaqMiUawbqapq/VwcmmVrlSHgahzq9A6XwKgZ/D7qjGqrAwaAAAAABJRU5ErkJggg==) 執行，即可在右方區域看到執行結果![[assets/Kibana/file-20260531215906463.png]]

以下列出幾個常用的API
* cluster狀態：GET cluster/health       
* Node 狀態：GET cat/nodes?v 
* Index 狀態：GET cat/indices?v 
* Node 分配狀態：GET cat/allocation?v
* 重新分配未分配的分片：POST cluster/reroute?retry_failed  
## **Stack Management**
![[assets/Kibana/file-20260531220213177.png]]
* ***Indices** 頁面可以管理所有的 Index( Index 可以理解成DB 的 Tables)
* 可以查看狀態、進行關閉、刪除等動作
![[assets/Kibana/file-20260531220307718.png]]
* *Index Template* 的功能是新的Index建立時，會套用符合條件的模板設定
* 包含了**Index Setting**、**Mapping**、**Alias**等等
* 下圖的 Pattern 可以理解成 DB Table 的 Columns
![[assets/Kibana/file-20260531220424453.png]]
下圖示範如何建立一個簡易版的 template
設定完**Name**及**index patterns**即可跳到第三步Index settings的部分
![[assets/Kibana/file-20260531220555363.png|697]]
下圖為三個常用到的基本設定
* "number_of_shards": 主分片的數量(在index產生後就不能修改了)
	* shards: 
* "number_of_replicas": 副分片數量
	* replicas
* "index.lifecycle.name": 要套用的ILM名稱(後續會說明ILM的部分)
![[assets/Kibana/file-20260531220702477.png]]
![[assets/Kibana/file-20260531220749803.png]]

## Index Lifecycle Policies
* 用於設定Index的生命週期
* 需要搭配上面的Index Template來自動帶入新建立的index
![[assets/Kibana/file-20260531220848598.png]]
下圖示範如何建立policy
1. 設定policy名稱（即為之前Index Template設定時的index.lifecycle.name）
2. 把Advenced settings展開，並關閉推薦設定
	 ![[assets/Kibana/file-20260531220939688.png]]
3. 接著把右邊的rollover也關閉
	 ![[assets/Kibana/file-20260531220955366.png|188]]
4. 然後點擊右邊的垃圾桶開啟資料刪除階層
	 ![[assets/Kibana/file-20260531221001663.png|235]]
5. 最後設定index建立多久後刪除資料
	![[assets/Kibana/file-20260531221011928.png]]
6. 建立完之後在列表中看到Linded index templates即為有使用該policy的Index Template
	![[assets/Kibana/file-20260531221022008.png]]

## Users
* 此為使用著的管理介面，不能編輯的是本身預設的使用者，只能進行密碼變更
	 ![[assets/Kibana/file-20260531221157704.png]]

## Lens
Kibana Lens 是一個易於使用且直觀的 UI（使用者介面），它的拖曳功能簡化了資料可視化過程。
![[assets/Kibana/file-20260531224805890.webp]]
