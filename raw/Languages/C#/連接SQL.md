# 連接SQL

以下Code幾個步驟 :

1. 確認連接字串
2. 建立SqlConnection
3. 確認查詢字串
4. 建立SqlDataAdpater
5. 找容器來裝 ( EX : DataSet、DataTAble .... )

```csharp
try
{
    // step 1 . using System.Data.SqlClient;

    // step 2 . 宣告連接字串

    string Constr = @"Persist Security Info=False;Integrated Security=true;
         Initial Catalog=AdventureWorksDW;Server=.\SQLExpress";

    // step 3 . 建立SqlConnection
    SqlConnection conn = new SqlConnection(Constr);

    // step 4 . 宣告查詢字串
    string Sqlstr = "select * from DimCustomer";

    // step 5. 建立SqlDataAdapter
    SqlDataAdapter da = new SqlDataAdapter(Sqlstr, conn);

    // step 6. 建立DataSet來儲存Table
    DataSet ds = new DataSet();
  
    // step 7. 將DataAdapter查詢之後的結果，填充至DataSet
    da.Fill(ds);                

    // step 8 . 用DataGridView1 顯示出來
    this.dataGridView1.DataSource = ds.Tables[0].DefaultView;
   

}
catch (Exception ex)
{

    MessageBox.Show(ex.Message);
}
```

- SqlConnection 的使用基本上要習慣 Open及Close但是這裡用到 SqlDataAdapter，會自動開啟連線以及自動關閉連線。
- 它會開啟連線並直接執行Query(查詢字串)，以及結束後會自動關閉連線，因次就可不必使用SqlConnection.Open();  and SqlConnection.Close();

```csharp
SqlDataAdapter da = new SqlDataAdapter(Sqlstr, conn);

public SqlDataAdapter(
	string selectCommandText,
	SqlConnection selectConnection
)

//     使用 System.Data.SqlClient.SqlDataAdapter.SelectCommand 和 System.Data.SqlClient.SqlConnection
//     物件，初始化 System.Data.SqlClient.SqlDataAdapter 類別的新執行個體。
//
// 參數:
//   selectCommandText:
//     System.String，即要由 System.Data.SqlClient.SqlDataAdapter 的 System.Data.SqlClient.SqlDataAdapter.SelectCommand
//     屬性使用的 Transact-SQL SELECT 陳述式或預存程序。
//
//   selectConnection:
//     表示連接的 System.Data.SqlClient.SqlConnection。 如果您的連接字串不使用 Integrated Security
//     = true，您可以使用 System.Data.SqlClient.SqlCredential 傳遞使用者 ID 和密碼，比起在連接字串中將使用者
//     ID 和密碼指定為文字更安全。
```