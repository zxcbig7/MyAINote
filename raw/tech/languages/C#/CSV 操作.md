# CSV 操作

[112年6月.csv](112%E5%B9%B46%E6%9C%88.csv)

[CSV 控制.zip](CSV_%E6%8E%A7%E5%88%B6.zip)

[https://www.jb51.net/article/193012.htm](https://www.jb51.net/article/193012.htm)

[https://dotblogs.com.tw/shinyo.her/2010/10/05/18107](https://dotblogs.com.tw/shinyo.her/2010/10/05/18107)

TryParse

### **開啟資料**

這是使用FILESTREAM開啟文件夾的典型範例 ，重要的是要始終關閉stream。如果你不關閉它可能會需要一分鐘之後才能再次開啟文件（它將等待garbage collector釋放FileStream，並關閉該文件）。

```csharp
using System.IO;

FileStream fileStream = new FileStream(@"c:\test1.txt", FileMode.Open);
try
{
  // read from file or write to file
}
finally
{
  fileStream.Close();
}
```

1. 開起來讀
    
    ```csharp
    FileStream fileStream = new FileStream(@"c:\test1.txt", FileMode.Open, FileAccess.Read);
    ```
    
2. 開起來寫
    
    ```csharp
    FileStream fileStream = new FileStream(@"c:\test1.txt", Filode.Open, FileAccess.Write);
    ```
    
3. 創建資料
    
    ```csharp
    FileStream fileStream = new FileStream(@"c:\test1.txt", FileMode.Create);
    ```
    

### **從目錄讀取資料**

```csharp
string[] filePaths = Directory.GetFiles(@"c:\SHINYO\");
```

再來是關鍵字的方法，可以用*.jpg搜尋以其為副檔名之資料，也可以用a*搜尋以A為檔名開頭之資料

```csharp
string[] filePaths = Directory.GetFiles(@"c:\SHINYO\", "*.bmp");
```

### 刪除資料

```csharp
using System.IO;

string[] filePaths = Directory.GetFiles(@"c:\SHINYO\");
foreach (string filePath in filePaths)
File.Delete(filePath);
```

### **獲得資料時間**

得知資料的特定時間資訊如:最後修改時間(GetLastWri­teTime)...等，之類的方法。

```csharp
// local  
DateTime creationTime = File.GetCreationTime(@"c:\AA.txt");
DateTime lastWriteTime = File.GetLastWriteTime(@"c:\AA.txt");
DateTime lastAccessTime = File.GetLastAccessTime(@"c:\AA.txt");

// UTC  
DateTime creationTimeUtc = File.GetCreationTimeUtc(@"c:\AA.txt");
DateTime lastWriteTimeUtc = File.GetLastWriteTimeUtc(@"c:\AA.txt");
DateTime lastAccessTimeUtc = File.GetLastAccessTimeUtc(@"c:\AA.txt");

// write time ( Local / UTC)
Console.WriteLine(lastWriteTime);      
Console.WriteLine(lastWriteTimeUtc);
```

為了精簡程式，可以使用[FileInfo Class](http://msdn.microsoft.com/zh-tw/library/system.io.fileinfo_members.aspx)來達成簡化的目的:

```csharp
FileInfo fileInfo = new FileInfo(@"c:\AA.txt");

// local  
DateTime creationTime = fileInfo.CreationTime;
DateTime lastWriteTime = fileInfo.LastWriteTime;
DateTime lastAccessTime = fileInfo.LastAccessTime;

// UTC  
DateTime creationTimeUtc = fileInfo.CreationTimeUtc;
DateTime lastWriteTimeUtc = fileInfo.LastWriteTimeUtc;
DateTime lastAccessTimeUtc = fileInfo.LastAccessTimeUtc;

// write  time ( Local / UTC)
Console.WriteLine(lastWriteTime);      
Console.WriteLine(lastWriteTimeUtc);
```

### **StreamReader示例：**讀取一行

> 假設e:\myoutput.txt文件的內容如下 -
> 
> 
> This is line 1
> This is line 2
> This is line 3
> This is line 4
> 

```csharp
using System;
using System.IO;
public class StreamReaderExample
{
    public static void Main(string[] args)
    {
        FileStream fs = new FileStream("e:\\myoutput.txt", FileMode.OpenOrCreate);
        StreamReader s = new StreamReader(fs);

        string line = s.ReadLine();
        Console.WriteLine(line);
        string line2 = s.ReadLine();
        Console.WriteLine(line2);
        s.Close();
        fs.Close();
    }
}
```

> 執行上面示例代碼，得到以下輸出結果 -
> 
> 
> This is line 1
> This is line 2
> 

### **StreamReader示例：讀取所有行**

```csharp
using System;
using System.IO;
public class StreamReaderExample
{
    public static void Main(string[] args)
    {
        FileStream f = new FileStream("e:\\myoutput.txt", FileMode.OpenOrCreate);
        StreamReader s = new StreamReader(f);

        string line = "";
        while ((line = s.ReadLine()) != null)
        {
            Console.WriteLine(line);
        }
        s.Close();
        f.Close();
    }
}

```

> 執行上面示例代碼，得到以下輸出結果 -
> 
> 
> This is line 1
> This is line 2
> This is line 3
> This is line 4
>