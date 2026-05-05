# Table Library

# 參考資料

[https://www.dotblogs.com.tw/chjackiekimo/2014/04/03/144606#google_vignette](https://www.dotblogs.com.tw/chjackiekimo/2014/04/03/144606#google_vignette)

---

[程式範例.rar](%E7%A8%8B%E5%BC%8F%E7%AF%84%E4%BE%8B.rar)

# 程式範例

---

DataSet可以想像成由許多Table所組成的資料表集合，Table在C#裡就叫DataTable

DataTable是由三個東西組成的，欄位(DataColumn)、列(DataRow)以及存放的值

<aside>
📅 DataTable的物件是在System.Data參考裡，如果沒有請記得加入System.Data並Using System.Data

</aside>

![Untitled](Table%20Library/Untitled.png)

```csharp
// 建立Table物件
DataTable dt = new DataTable("StudentData");

dt.Columns.Add("StudentID", typeof(String));
dt.Columns.Add("StudentName", typeof(String));
dt.Columns.Add("Math", typeof(Double));
dt.Columns.Add("Eng", typeof(Double));

// ========== Column設定 ==========
//  只有String 才要設定長度
// StudentID
dt.Columns["StudentID"].MaxLength = 10;//長度
dt.Columns["StudentID"].AllowDBNull = false;//不能空值
dt.Columns["StudentID"].Unique = true;//建立唯一性
// StudnetName
dt.Columns["StudentName"].MaxLength = 10;
dt.Columns["StudentName"].AllowDBNull = false;

// 讓DataGridView的資料來源設定為dt
dataGridView1.DataSource = dt;
```

![Untitled](Table%20Library/Untitled%201.png)

```csharp
//第一種新增列的方法

//DataRow 沒有New
DataRow row;
//切記 !! DataTable 要產生Row時，必須使用NewRow這個方法
//可以把它想成為將dt產生一個新的列
row = dt.NewRow();

//隨機產生成績 (放全域)
Random rd = new Random();

//產生順序ID (放全域)
int G_studentID = 0;

row["StudentID"] = "S00" + (++G_studentID);
row["StudentName"] = G_studentID;
row["Math"] = Double.Parse( (rd.NextDouble() * 100.0).ToString("0.00"));
row["Eng"] = Double.Parse((rd.NextDouble() * 100.0).ToString("0.00"));

// 最後一步將DataRow新增到Table裡
dt.Rows.Add(row);
```

![Untitled](Table%20Library/Untitled%202.png)

```csharp
// 透過DataRow新增資料還有第二個方法，不過要確保欄位順序的問題。

DataRow row;
row = dt.NewRow();

dt.Rows.Add(new Object[] { "S00" + (++G_studentID), G_studentID, Double.Parse((rd.NextDouble() * 100.0).ToString("0.00")), Double.Parse((rd.NextDouble() * 100.0).ToString("0.00")) });
```