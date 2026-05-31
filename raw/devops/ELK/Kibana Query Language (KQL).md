## 特色
* KQL 是一個簡單文字基礎的搜尋語言，用於篩選資料
* 無法用於資料彙總、轉換或者排序
* KQL 可以基於某 Field 是否存在、符合特定值或者在特定範圍篩出 Document

## Semi-structured search
> 以純文字的 Field 搭配: 條件 做搜尋
```
<Field>:<Condition>
```

Exact phrase query  精確字詞查詢	
```
http.response.body.content.text:"quick brown fox"
```
Terms query  條款查詢	
```
http.response.status_code:400 401 404
```
Boolean query  布林查詢
```
response:200 or extension:php
```
Range query  範圍查詢	
```
account_number >= 100 and items_sold <= 200
```
Wildcard query  通配符查詢	
```
machine.os:win*
```

## 過濾出那些包含某個欄位的文件

* 使用 `*` 運算子篩選出在某個欄位中存在索引值的文件，包含空字串
* 例如，篩選出 `http.request.method` 欄位存在於文件中的文件
```
http.request.method: *
```

## 過濾出符合某個值的文件
* 可以根據特定的數字、文字、日期或布林值來過濾文件。
* 例如，若要過濾出 `http.request.method` 為 GET 的文件
```
http.request.method: GET
```
* Field 是 Optional 。如果未填入該值，系統會在所有Field中搜尋該值。
* 例如，若要在所有欄位中搜尋“Hello”，就會找整個Field 是否有Hello資料
```
Hello
```
* 在查詢關鍵字、數字、日期或布林值等類型的欄位時，其值必須完全一致，包括標點符號和大小寫。
* 會根據 Field 的 mapping Settings 搜尋文字欄位
* 例如，若要搜尋那些在 `http.request.body.content` 欄位中包含“null pointer”這個字串的文件
```
http.request.body.content: null pointer
```
* 由於 `http.request.body.content`  是一個 `text` 類型的 Field ，因此這些搜尋詞的順序並不重要，即使是包含“pointer null”的Document也會被返回。
* 若要在 `text` 類型的欄位中按指定的順序進行搜尋，請將相關值用引號括起來
```
http.request.body.content: "null pointer"
```
* 當要處理 `\():<>"*` 字符，必須用反斜線來轉義（除非該字元已經被引號包起來）
* 例如，若要搜尋包含 `http.request.referrer` 且其值為 `https://example.com` 的Document
```
http.request.referrer: "https://example.com" http.request.referrer: https\://example.com
```

## 過濾特定範圍內的文件
* 使用 KQL 的範圍運算子搜尋包含在特定範圍內的詞彙的文件
* 若要搜尋某個範圍內的資料，可以結合多個範圍條件 (and、or)。
* 例如，若要搜尋 `http.response.bytes` 大於 10000 但小於或等於 20000 的文件
```
http.response.bytes > 10000 and http.response.bytes <= 20000
```
> 注意: 當在多值欄位(multi-value fields)上使用包含多個條件的範圍查詢時，每個條件都會分別對陣列中的所有值進行判斷。
> 例如，查詢 `number > 300 AND number < 400` 會與包含 `"number": [500, 10]` 的文件相匹配，因為 500 滿足第一個條件，而 10 則滿足第二個條件。如果您要求所有條件都必須由相同的數值來滿足，建議使用 Query DSL。使用 Query DSL 的話，只有當至少有一個數值完全落在指定的範圍內時，該查詢才會匹配到相關的文件。

* 可以對字串值、IP 位址和時間戳記使用範圍運算語法。
* 例如，若要搜尋兩週之前的文件
* 相關語法可以參考 [[Date Math]]
```
@timestamp < now-2w
```

## 使用通配符來過濾文件
* 若要搜尋符合某種模式的文件，請使用通配符語法。
* 目前僅支援 `*` 。它可以用來匹配零個或更多個字符。
* 例如，若要找出以 4 開頭的、包含 `http.response.status_code` 的文件
```
http.response.status_code: 4*
```

## 排除查詢
* 若要排除某組文件，請使用 `not` 關鍵字（不區分大小寫）
* 例如，若要篩選出 `http.request.method` 為非 GET 的文件
```
NOT http.request.method: GET
```

## 結合多個查詢條件
* 若要合併多個查詢條件，請使用 `and` / `or` 這些關鍵字（不區分大小寫）。
* 例如，若要找出 `http.request.method` 為 GET 或 `http.response.status_code` 為 400 的文件
```
http.request.method: GET OR http.response.status_code: 400
```
若要找出那些 `http.request.method` 為 GET 且 `http.response.status_code` 為 400 的文件
```
http.request.method: GET AND http.response.status_code: 400
```
* 若要在同時執行多個查詢時指定其優先順序，請使用括號。
* 例如，若要找出那些 `http.request.method` 為 GET、 `http.response.status_code` 為 200 的文件，或者 `http.request.method` 為 POST、 `http.response.status_code` 為 400 的文件
```
(http.request.method: GET AND http.response.status_code: 200) OR (http.request.method: POST AND http.response.status_code: 400)
```
* 在查詢同一欄位的多個值時，也可以使用括號來簡化語法。
* 例如，若要找出 `http.request.method` 為 GET、POST 或 DELETE 的文件
```
http.request.method: (GET OR POST OR DELETE)
```

## 匹配多個欄位
* 通配符也可用於查詢多個 Field。
* 例如，若要搜尋 `datastream` 中的任何子欄位包含「logs」的文件
```
datastream.*: logs
```

## 查詢巢狀欄位
* 查詢巢狀欄位需要使用特殊語法。請參考以下文件，其中 `user` 即為嵌套欄位：
``` JSON
{ 
	"user" : [ 
		{ 
		"first" : "John", 
		"last" : "Smith" 
		}, 
		{ 
		"first" : "Alice", 
		"last" : "White" 
		} 
	] 
}
```
* 若要找出在 `user` 陣列中，某個元素的值包含「Alice」作為名字、以及「White」作為姓氏的 document
```
user:{ first: "Alice" and last: "White" }
```
* 由於巢狀欄位可以存在於其他巢狀欄位之中，因此您必須指定欲查詢的巢狀欄位的完整路徑。
* 例如，在以下文件中， `user` 和 `names` 都是嵌套欄位：
```JSON
{
  "user": [
    {
      "names": [
        {
          "first": "John",
          "last": "Smith"
        },
        {
          "first": "Alice",
          "last": "White"
        }
      ]
    }
  ]
}
```
* 若要找出在 `user.names` 陣列中，某個元素的值包含「Alice」作為名字、以及「White」作為姓氏的文件，請使用以下方式：
```
user.names:{ first: "Alice" and last: "White" }
```