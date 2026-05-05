# Game Notes (Godot)

# 座標系統

以2D遊戲平面，左上角為(0,0)，右為 `x+`、左為 `x-`，下為 `y+`、上為 `y-`

# Sprite2D

用於顯示圖片

# Input Events

![image.png](Game%20Notes%20(Godot)/image.png)

| 狀況 | `Pressed` | `Echo` |
| --- | --- | --- |
| 第一次按下鍵「A」 | `true` | `false` |
| 長按後系統重複輸入「A」 | `true` | `true` |
| 放開鍵「A」 | `false` | `false` |

| 屬性 | 意義 | 使用時機 |
| --- | --- | --- |
| `Pressed` | 是否按下（true）或放開（false） | 用來偵測「按下／放開」行為 |
| `Echo` | 是否為「重複觸發」的長按事件 | 用來避免重複處理長按時的多次觸發 |
|  |  |  |

偵測「第一次按下」某個鍵（不重複反應），可以加上判斷：這樣可以防止長按重複觸發的情況（特別常用在遊戲控制中，例如跳躍鍵）。

```csharp
if (keyEvent.Pressed && !keyEvent.Echo)
{
    GD.Print("Key just pressed once!");
}
```

# Handling Input

![image.png](Game%20Notes%20(Godot)/image%201.png)

# Transformation

![image.png](Game%20Notes%20(Godot)/image%202.png)

> Normalized 會把方向變成一個pixel
>