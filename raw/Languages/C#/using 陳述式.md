---
tags: [csharp, programming]
---

> 關聯：[[csharp]]

# using 陳述式

使用 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 最主要的目的是為了讓物件建立的同時能確保該物件所佔用的資源一定會被完整釋放，如果沒有釋放這些**無法自動釋放**的資源，就很有可能讓 .NET 應用程式發生 **資源耗盡** (Resource Exhausted) 的狀況。

```csharp
using (System.IO.StreamReader sr = new System.IO.StreamReader(@"C:\test.txt"))
{
    string s = null;
    while((s = sr.ReadLine()) != null)
    {
        Console.WriteLine(s);
    }
}
```

使用 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 陳述式有一個最基本的條件，就是該物件必須有實做 [IDisposable](http://msdn.microsoft.com/zh-tw/library/system.idisposable.aspx?WT.mc_id=DT-MVP-4015686) 介面，才能確保在 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 的結尾數時自動執行 [Dispose() 方法](http://msdn.microsoft.com/zh-tw/library/system.idisposable.dispose.aspx?WT.mc_id=DT-MVP-4015686)。

使用 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 陳述式的另一個**強烈建議**的條件，就是該物件被建立的語法必須寫在 using 子句中，否則物件很有可能在被釋放後還有其他物件存取的情況，進而引發例外狀況！

有些人認為 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 陳述式會自動被翻譯成以下程式碼：（錯誤範例）

```csharp
{
    System.IO.StreamReader sr = new System.IO.StreamReader(@"C:\test.txt");
    try
    {
      string s = null;
      while((s = sr.ReadLine()) != null)
      {
          Console.WriteLine(s);
      }
    }
    catch
    {
    }
    finally
    {
      if (sr != null)
        ((IDisposable)sr).Dispose();
    }
}
```

但事實上，應該不包含 catch 的區段才是！**正確的語法**應該如下：

```csharp
{
	System.IO.StreamReader sr = new System.IO.StreamReader(@"C:\test.txt");
	try
	{
	  string s = null;
	  while((s = sr.ReadLine()) != null)
	  {
		  Console.WriteLine(s);
	  }
	}
	finally
	{
	  if (sr != null)
		((IDisposable)sr).Dispose();
	}
}
```

也就是在使用 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 陳述式時，雖然有 **try** 與 **finally**，但並不包含 **catch** 的成分！

換句話說，使用 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 陳述式並不會幫你捕捉**例外狀況**！！

所以就算你用 [using](http://msdn.microsoft.com/zh-tw/library/yh598w02.aspx?WT.mc_id=DT-MVP-4015686) 在程式中，若要處理 [try-catch](http://msdn.microsoft.com/zh-tw/library/0yd65esw.aspx?WT.mc_id=DT-MVP-4015686) 的狀況還是要自行撰寫，否則就會遇到非預期的例外狀況而導致應用程式掛掉，這點必須特別注意！