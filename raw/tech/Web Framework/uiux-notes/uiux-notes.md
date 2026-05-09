---
tags: [web-dev, uiux, frontend, design]
---

> 關聯：[[react]]

# UI/UX 設計筆記

## 圓角的正確關係：外圓角 = 內圓角 + Padding

### 核心概念

當一個元素包在另一個元素裡面，兩者的圓角**不應該相同**。

```
外圓角（r_outer）= 內圓角（r_inner）+ Padding
```

### 為什麼？

圓角是從元素邊緣算起的弧度半徑。如果內外圓角相同，視覺上內層的弧度會比外層「更彎」，兩者曲線不平行，看起來不協調。

```
❌ 錯誤：外圓角 = 內圓角 = 12px
┌────────────────────┐
│  ┌──────────────┐  │  ← 內外弧度不平行，視覺不自然
│  │              │  │
│  └──────────────┘  │
└────────────────────┘

✅ 正確：外圓角 16px，Padding 4px，內圓角 12px
╭────────────────────╮
│  ╭──────────────╮  │  ← 兩條弧線平行，看起來剛好「貼合」
│  │              │  │
│  ╰──────────────╯  │
╰────────────────────╯
```

### 實際計算範例

| Padding | 內圓角 | 外圓角 |
| ------- | ------ | ------ |
| 4px     | 8px    | 12px   |
| 8px     | 8px    | 16px   |
| 16px    | 12px   | 28px   |
| 4px     | 0px    | 4px    |

### 程式碼示例

```css
/* 外層容器 */
.card {
  border-radius: 16px;
  padding: 4px;
}

/* 內層元素：外圓角 - padding = 12px */
.card-inner {
  border-radius: 12px;
}
```

```typescript
// 動態計算
const padding = 8;
const innerRadius = 12;
const outerRadius = innerRadius + padding; // 20px
```

### 適用時機

- 卡片內有按鈕、圖片、tag 等帶圓角的子元素
- Input field 帶 icon 或 prefix/suffix
- Badge 疊在容器上
- Nested card（卡片裡有卡片）

### 特例：內圓角為 0

內層完全無圓角時，外層圓角只需等於 padding 即可讓視覺感覺貼合：

```
外圓角 = padding（內圓角 0 的情況）
```

---
