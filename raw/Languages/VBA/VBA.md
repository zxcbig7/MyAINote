---
tags: [vba, programming, office]
---

# VBA

```vbnet
Sub ForNext()
        
    Dim i, Sumtotal As Integer
    
    Range("a:d").Clear
    Range("A1").Value = "編號"
    Range("B1").Value = "成績"
    Range("C1").Value = "及格"
    Range("D1").Value = "等第"
    
    For i = 1 To 10
        Range("B" & i + 1).Value = "=RANDBETWEEN(0, 100)"
    Next
    
    Range("B2:B11").Select
    Application.CutCopyMode = False
    Selection.Copy
    Selection.PasteSpecial Paste:=xlPasteValues, Operation:=xlNone, SkipBlanks _
        :=False, Transpose:=False
    Application.CutCopyMode = False
    Range("A1").Select
    

    For i = 1 To 10 Step 1
        
        '賦值
        Range("A" & i + 1).Value = i
        Sumtotal = Sumtotal + Range("B" & i + 1).Value
        
        '判斷及格
        If Range("B" & i + 1).Value >= 60 Then
            Range("C" & i + 1).Value = "及格"
        Else
            Range("C" & i + 1).Value = "不及格"
        End If
        
        
        '判斷等第
        Select Case Range("B" & i + 1).Value
            Case Is < 0, Is > 100
                Range("D" & i + 1).Value = "輸入錯誤"
            Case Is >= 80
                Range("D" & i + 1).Value = "A"
            Case 70 To 79
                Range("D" & i + 1).Value = "B"
            Case 60 To 69
                Range("D" & i + 1).Value = "C"
            Case Else
                Range("D" & i + 1).Value = "D"
        End Select
    Next
    
    '統計數
    Range("A" & i + 1).Value = "總成績: " & Sumtotal
    Range("B" & i + 1).Value = "平均數: " & Sumtotal / (i - 1)

    
End Sub
```