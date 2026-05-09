# Tailwind CSS 開發

# 資源

## 查 Tailwind CSS 的最佳資源

**第一個，官方文件** [https://tailwindcss.com/docs](https://tailwindcss.com/docs)

這是你最應該先去的地方。左側欄位就是所有分類，每個分類進去就能看到所有可用的 class 字串，還有對應的 CSS 是什麼。

---

**第二個，Tailwind CSS Cheat Sheet** 

- [https://tailwindcomponents.com/cheatsheet](https://tailwindcomponents.com/cheatsheet)
- [https://flowbite.com/tools/tailwind-cheat-sheet/](https://flowbite.com/tools/tailwind-cheat-sheet/)

---

**(必須)第三個，直接在 VS Code 裡查** 

安裝這個 extension：Tailwind CSS IntelliSense

打 class 的時候會自動補全，還會顯示這個 class 對應的實際 CSS，不用離開編輯器就能查到所有東西。這個在實際開發時是最快的。

---

**第四個，Tailwind Play (官方 Playground)** [https://play.tailwindcss.com](https://play.tailwindcss.com/)

可以直接在線上測試 class，看效果，適合不確定某個 class 長什麼樣子的時候快速驗證。

# 安裝與建置

> **Tailwind CSS** 負責樣式，**clsx** 負責處理動態 class，**tailwind-merge** 負責解決 class 衝突。
> 

```bash
npm install tailwindcss clsx tailwind-merge
```

然後把 `clsx` 和 `tailwind-merge` 包成一個 `cn` 工具函式，幾乎所有專案都會這樣做：

```tsx
// lib/utils.js
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
```

之後在元件裡直接用 `cn` 來管理樣式：

```tsx
import { cn } from '@/lib/utils';

function Button({ variant = 'primary', disabled, className }) {
  return (
    <button
      className={cn(
        'px-4 py-2 rounded font-medium transition',
        variant === 'primary' && 'bg-blue-500 text-white hover:bg-blue-600',
        variant === 'secondary' && 'bg-gray-200 text-black hover:bg-gray-300',
        disabled && 'opacity-50 cursor-not-allowed',
        className  // 允許外部覆寫樣式
      )}
    >
      Click
    </button>
  );
}
```

# 設計哲學：Utility First

> Tailwind 提供大量小型 class，每個 class 只做一件事。
不需要寫任何 CSS 檔案，直接在 HTML 上組合這些 class 來完成樣式。
> 

> **優點：**開發速度非常快，不需要在 JSX 和 CSS 檔案之間切換，打包後 CSS 體積小（只打包用到的 class），也容易維持整個專案的設計一致性。
**缺點：** class 名稱很長，初期需要記憶 class 對應的 CSS，對不熟悉的人閱讀性較差。
> 

```tsx
function Card() {
  return (
    <div className="p-6 bg-white rounded-xl shadow-md flex gap-4">
      <img className="w-12 h-12 rounded-full" src="/avatar.png" />
      <div>
        <h2 className="text-lg font-semibold text-gray-800">John Doe</h2>
        <p className="text-gray-500 text-sm">Software Engineer</p>
      </div>
    </div>
  );
}
```

上方範例中的 `p-6`, `bg-white`, `rounded-xl` 都是 Tailwind 的 utility class，對應到固定的 CSS 值。

### 響應式與狀態

Tailwind 用前綴來處理，不需要另外寫 media query。

```tsx
<div className="
  w-full          
  md:w-1/2        
  lg:w-1/3        
  hover:bg-blue-600
  focus:ring-2    
  dark:bg-gray-800
">
```

`md:` 代表在 medium 螢幕以上套用，`hover:` 代表滑鼠移上去時套用，語意直覺。

### 用 `cn` 處理動態樣式

當樣式需要依條件改變，搭配 `clsx` 或 `tailwind-merge` 來管理。

```tsx
import { clsx } from 'clsx';

function Button({ variant = 'primary', disabled }) {
  return (
    <button
      className={clsx(
        'px-4 py-2 rounded font-medium transition',
        variant === 'primary' && 'bg-blue-500 text-white hover:bg-blue-600',
        variant === 'secondary' && 'bg-gray-200 text-black hover:bg-gray-300',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
      disabled={disabled}
    >
      Click
    </button>
  );
}
```

# Tailwind CSS Class 值 Cheat note

以下按功能分類，列出所有常用的 class 字串。

---

## 排版 (Typography)

**字體大小 `text-{size}**text-xs` / `text-sm` / `text-base` / `text-lg` / `text-xl` / `text-2xl` / `text-3xl` / `text-4xl` / `text-5xl` / `text-6xl` / `text-7xl` / `text-8xl` / `text-9xl`

**字重 `font-{weight}**font-thin` / `font-extralight` / `font-light` / `font-normal` / `font-medium` / `font-semibold` / `font-bold` / `font-extrabold` / `font-black`

**字型 `font-{family}**font-sans` / `font-serif` / `font-mono`

**行高 `leading-{size}**leading-none` / `leading-tight` / `leading-snug` / `leading-normal` / `leading-relaxed` / `leading-loose` / `leading-3` ~ `leading-10`

**字距 `tracking-{size}**tracking-tighter` / `tracking-tight` / `tracking-normal` / `tracking-wide` / `tracking-wider` / `tracking-widest`

**文字對齊 `text-{align}**text-left` / `text-center` / `text-right` / `text-justify` / `text-start` / `text-end`

**文字裝飾**`underline` / `overline` / `line-through` / `no-underline`

**文字變換**`uppercase` / `lowercase` / `capitalize` / `normal-case`

**文字溢位**`truncate` / `text-ellipsis` / `text-clip` / `overflow-ellipsis`

---

## 顏色 (Colors)

**文字顏色 `text-{color}-{shade}`**
顏色：`slate` / `gray` / `zinc` / `neutral` / `stone` / `red` / `orange` / `amber` / `yellow` / `lime` / `green` / `emerald` / `teal` / `cyan` / `sky` / `blue` / `indigo` / `violet` / `purple` / `fuchsia` / `pink` / `rose`
色階：`50` / `100` / `200` / `300` / `400` / `500` / `600` / `700` / `800` / `900` / `950`

例：`text-blue-500` / `text-red-700` / `text-white` / `text-black`

**背景顏色 `bg-{color}-{shade}`**，**邊框顏色 `border-{color}-{shade}`** 用法相同。

---

## 間距 (Spacing)

**Padding `p-{size}` / `px-` / `py-` / `pt-` / `pr-` / `pb-` / `pl-`Margin `m-{size}` / `mx-` / `my-` / `mt-` / `mr-` / `mb-` / `ml-`**

尺寸值：
`0` / `px` / `0.5` / `1` / `1.5` / `2` / `2.5` / `3` / `3.5` / `4` / `5` / `6` / `7` / `8` / `9` / `10` / `11` / `12` / `14` / `16` / `20` / `24` / `28` / `32` / `36` / `40` / `44` / `48` / `52` / `56` / `60` / `64` / `72` / `80` / `96`

特殊值：`auto` / `full` / `screen` (只有部分屬性支援)

負值用 `-mt-4` / `-mb-2` 這樣加 `-` 前綴。

---

## 尺寸 (Sizing)

**寬度 `w-{size}`**
數值同上，加上：`1/2` / `1/3` / `2/3` / `1/4` / `3/4` / `1/5` / `2/5` / `3/5` / `4/5` / `full` / `screen` / `svw` / `lvw` / `dvw` / `min` / `max` / `fit` / `auto`

**高度 `h-{size}**h-full` / `h-screen` / `h-svh` / `h-lvh` / `h-dvh` / `h-min` / `h-max` / `h-fit` / `h-auto` + 數值同上

**最大寬度 `max-w-{size}**max-w-none` / `max-w-xs` / `max-w-sm` / `max-w-md` / `max-w-lg` / `max-w-xl` / `max-w-2xl` / `max-w-3xl` / `max-w-4xl` / `max-w-5xl` / `max-w-6xl` / `max-w-7xl` / `max-w-full` / `max-w-min` / `max-w-max` / `max-w-fit` / `max-w-prose` / `max-w-screen-sm` / `max-w-screen-md` / `max-w-screen-lg` / `max-w-screen-xl` / `max-w-screen-2xl`

---

## Display & 排版模式

`block` / `inline-block` / `inline` / `flex` / `inline-flex` / `grid` / `inline-grid` / `table` / `hidden` / `contents` / `flow-root` / `list-item`

---

## Flexbox

**方向**`flex-row` / `flex-row-reverse` / `flex-col` / `flex-col-reverse`

**換行**`flex-wrap` / `flex-wrap-reverse` / `flex-nowrap`

**主軸對齊 `justify-{value}**justify-start` / `justify-end` / `justify-center` / `justify-between` / `justify-around` / `justify-evenly` / `justify-stretch`

**交叉軸對齊 `items-{value}**items-start` / `items-end` / `items-center` / `items-baseline` / `items-stretch`

**自身對齊 `self-{value}**self-auto` / `self-start` / `self-end` / `self-center` / `self-stretch` / `self-baseline`

**Flex 屬性**`flex-1` / `flex-auto` / `flex-initial` / `flex-nonegrow` / `grow-0` / `shrink` / `shrink-0order-first` / `order-last` / `order-none` / `order-1` ~ `order-12`

---

## Grid

**欄數 `grid-cols-{n}**grid-cols-1` ~ `grid-cols-12` / `grid-cols-none` / `grid-cols-subgrid`

**列數 `grid-rows-{n}**grid-rows-1` ~ `grid-rows-6` / `grid-rows-none` / `grid-rows-subgrid`

**跨欄 `col-span-{n}**col-span-1` ~ `col-span-12` / `col-span-full`

**跨列 `row-span-{n}**row-span-1` ~ `row-span-6` / `row-span-full`

**Gap `gap-{size}`** / `gap-x-{size}` / `gap-y-{size}`
數值同 spacing。

---

## 定位 (Position)

**定位方式**`static` / `relative` / `absolute` / `fixed` / `sticky`

**位置值 `top-` / `right-` / `bottom-` / `left-` / `inset-`**
數值同 spacing，加上 `auto` / `full` / `1/2` / `1/3` / `1/4`

---

## 邊框 (Border)

**寬度 `border-{size}**border` / `border-0` / `border-2` / `border-4` / `border-8`
方向：`border-t-` / `border-r-` / `border-b-` / `border-l-` / `border-x-` / `border-y-`

**樣式**`border-solid` / `border-dashed` / `border-dotted` / `border-double` / `border-hidden` / `border-none`

**圓角 `rounded-{size}**rounded-none` / `rounded-sm` / `rounded` / `rounded-md` / `rounded-lg` / `rounded-xl` / `rounded-2xl` / `rounded-3xl` / `rounded-full`
方向：`rounded-t-` / `rounded-r-` / `rounded-b-` / `rounded-l-` / `rounded-tl-` / `rounded-tr-` / `rounded-br-` / `rounded-bl-`

---

## 陰影 (Shadow)

**Box Shadow `shadow-{size}**shadow-sm` / `shadow` / `shadow-md` / `shadow-lg` / `shadow-xl` / `shadow-2xl` / `shadow-inner` / `shadow-none`

**Ring `ring-{size}**ring-0` / `ring-1` / `ring-2` / `ring` / `ring-4` / `ring-8` / `ring-inset`

---

## 背景 (Background)

**大小**`bg-auto` / `bg-cover` / `bg-contain`

**位置**`bg-center` / `bg-top` / `bg-right` / `bg-bottom` / `bg-left` / `bg-left-top` / `bg-right-top` / `bg-left-bottom` / `bg-right-bottom`

**重複**`bg-repeat` / `bg-no-repeat` / `bg-repeat-x` / `bg-repeat-y`

**漸層**`bg-gradient-to-t` / `bg-gradient-to-tr` / `bg-gradient-to-r` / `bg-gradient-to-br` / `bg-gradient-to-b` / `bg-gradient-to-bl` / `bg-gradient-to-l` / `bg-gradient-to-tlfrom-{color}` / `via-{color}` / `to-{color}`

---

## 效果 (Effects)

**透明度 `opacity-{value}**opacity-0` / `opacity-5` / `opacity-10` / `opacity-20` / `opacity-25` / `opacity-30` / `opacity-40` / `opacity-50` / `opacity-60` / `opacity-70` / `opacity-75` / `opacity-80` / `opacity-90` / `opacity-95` / `opacity-100`

**混合模式 `mix-blend-{mode}**mix-blend-normal` / `mix-blend-multiply` / `mix-blend-screen` / `mix-blend-overlay` / `mix-blend-darken` / `mix-blend-lighten` 等

---

## 濾鏡 (Filter)

**模糊 `blur-{size}**blur-none` / `blur-sm` / `blur` / `blur-md` / `blur-lg` / `blur-xl` / `blur-2xl` / `blur-3xl`

**亮度 `brightness-{value}**brightness-0` / `brightness-50` / `brightness-75` / `brightness-90` / `brightness-95` / `brightness-100` / `brightness-105` / `brightness-110` / `brightness-125` / `brightness-150` / `brightness-200`

**對比 `contrast-{value}**contrast-0` / `contrast-50` / `contrast-75` / `contrast-100` / `contrast-125` / `contrast-150` / `contrast-200`

---

## 變形 (Transform)

**縮放 `scale-{value}**scale-0` / `scale-50` / `scale-75` / `scale-90` / `scale-95` / `scale-100` / `scale-105` / `scale-110` / `scale-125` / `scale-150scale-x-` / `scale-y-` 也支援

**旋轉 `rotate-{value}**rotate-0` / `rotate-1` / `rotate-2` / `rotate-3` / `rotate-6` / `rotate-12` / `rotate-45` / `rotate-90` / `rotate-180`
負值：`-rotate-6` 等

**位移 `translate-x-{size}` / `translate-y-{size}`**
數值同 spacing，加上 `1/2` / `1/3` / `1/4` / `full`

**傾斜 `skew-x-{value}` / `skew-y-{value}**skew-x-0` / `skew-x-1` / `skew-x-2` / `skew-x-3` / `skew-x-6` / `skew-x-12`

---

## 過渡與動畫

**過渡 `transition-{property}**transition-none` / `transition-all` / `transition` / `transition-colors` / `transition-opacity` / `transition-shadow` / `transition-transform`

**時長 `duration-{ms}**duration-0` / `duration-75` / `duration-100` / `duration-150` / `duration-200` / `duration-300` / `duration-500` / `duration-700` / `duration-1000`

**緩動 `ease-{type}**ease-linear` / `ease-in` / `ease-out` / `ease-in-out`

**延遲 `delay-{ms}**delay-0` / `delay-75` / `delay-100` / `delay-150` / `delay-200` / `delay-300` / `delay-500` / `delay-700` / `delay-1000`

**動畫 `animate-{name}**animate-none` / `animate-spin` / `animate-ping` / `animate-pulse` / `animate-bounce`

---

## 互動 (Interactivity)

**游標 `cursor-{type}**cursor-auto` / `cursor-default` / `cursor-pointer` / `cursor-wait` / `cursor-text` / `cursor-move` / `cursor-help` / `cursor-not-allowed` / `cursor-none` / `cursor-grab` / `cursor-grabbing`

**使用者選取 `select-{type}**select-none` / `select-text` / `select-all` / `select-auto`

**Pointer Events**`pointer-events-none` / `pointer-events-auto`

**輪廓 `outline-{type}**outline-none` / `outline` / `outline-dashed` / `outline-dotted` / `outline-double`

---

## 可見性 & 溢位

**可見性**`visible` / `invisible` / `collapse`

**溢位 `overflow-{value}**overflow-auto` / `overflow-hidden` / `overflow-visible` / `overflow-scroll` / `overflow-clipoverflow-x-` / `overflow-y-` 也支援

**Z-index `z-{value}**z-0` / `z-10` / `z-20` / `z-30` / `z-40` / `z-50` / `z-auto`

---

## 響應式前綴

所有 class 都可以加斷點前綴：
`sm:` / `md:` / `lg:` / `xl:` / `2xl:`

例：`md:flex` / `lg:text-xl` / `sm:hidden`

---

## 狀態前綴

`hover:` / `focus:` / `active:` / `disabled:` / `checked:` / `placeholder:` / `first:` / `last:` / `odd:` / `even:` / `group-hover:` / `peer-hover:` / `dark:` / `focus-within:` / `focus-visible:` / `required:` / `valid:` / `invalid:`