# React TypeScript Canvas 手冊

> 適用：React 18+, TypeScript 5+
> 
> 
> 涵蓋：2D 繪圖、動畫、互動事件、影像處理、效能優化、進階技術
> 

---

## 目錄

1. [Canvas 基礎架構](about:blank#1-canvas-%E5%9F%BA%E7%A4%8E%E6%9E%B6%E6%A7%8B)
2. [TypeScript 型別定義](about:blank#2-typescript-%E5%9E%8B%E5%88%A5%E5%AE%9A%E7%BE%A9)
3. [useCanvas 自訂 Hook](about:blank#3-usecanvas-%E8%87%AA%E8%A8%82-hook)
4. [2D 繪圖 API 完整參考](about:blank#4-2d-%E7%B9%AA%E5%9C%96-api-%E5%AE%8C%E6%95%B4%E5%8F%83%E8%80%83)
5. [動畫迴圈 (Animation Loop)](about:blank#5-%E5%8B%95%E7%95%AB%E8%BF%B4%E5%9C%88-animation-loop)
6. [互動事件 (Mouse / Touch)](about:blank#6-%E4%BA%92%E5%8B%95%E4%BA%8B%E4%BB%B6-mouse--touch)
7. [影像處理與濾鏡](about:blank#7-%E5%BD%B1%E5%83%8F%E8%99%95%E7%90%86%E8%88%87%E6%BF%BE%E9%8F%A1)
8. [效能優化技巧](about:blank#8-%E6%95%88%E8%83%BD%E5%84%AA%E5%8C%96%E6%8A%80%E5%B7%A7)
9. [進階技術](about:blank#9-%E9%80%B2%E9%9A%8E%E6%8A%80%E8%A1%93)
10. [完整範例：互動式畫板](about:blank#10-%E5%AE%8C%E6%95%B4%E7%AF%84%E4%BE%8B%E4%BA%92%E5%8B%95%E5%BC%8F%E7%95%AB%E6%9D%BF)
11. [常見錯誤與解法](about:blank#11-%E5%B8%B8%E8%A6%8B%E9%8C%AF%E8%AA%A4%E8%88%87%E8%A7%A3%E6%B3%95)
12. [最佳實踐清單](about:blank#12-%E6%9C%80%E4%BD%B3%E5%AF%A6%E8%B8%90%E6%B8%85%E5%96%AE)

---

## 1. Canvas 基礎架構

### 1.1 最小可運作的 Canvas 元件

```tsx
// BasicCanvas.tsx
import React, { useRef, useEffect } from 'react';

const BasicCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // 取得 2D context，明確告訴 TypeScript 型別
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 設定畫布尺寸（重要：避免模糊問題）
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // 開始繪圖
    ctx.fillStyle = '#4CAF50';
    ctx.fillRect(50, 50, 200, 100);

    ctx.font = '24px Arial';
    ctx.fillStyle = 'white';
    ctx.fillText('Hello Canvas!', 70, 110);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '400px', border: '1px solid #ccc' }}
    />
  );
};

export default BasicCanvas;
```

### 1.2 HiDPI / Retina 螢幕支援

這是最常被忽略的問題，導致畫面模糊。

```tsx
// utils/setupHiDPI.ts
export function setupHiDPI(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('無法取得 2D context');

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  // 實際像素大小 = CSS 大小 × 裝置像素比
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;

  // CSS 尺寸保持不變
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  // 縮放 context 使座標系統與 CSS 對齊
  ctx.scale(dpr, dpr);

  return ctx;
}
```

```tsx
// 在元件中使用
useEffect(() => {
  const canvas = canvasRef.current;
  if (!canvas) return;
  const ctx = setupHiDPI(canvas);

  // 現在可以用 CSS 像素座標繪圖，不需考慮 dpr
  ctx.fillRect(10, 10, 100, 50); // 在 Retina 螢幕也會清晰
}, []);
```

---

## 2. TypeScript 型別定義

### 2.1 常用型別速查表

```tsx
// types/canvas.types.ts

// Canvas 元素本身
type CanvasElement = HTMLCanvasElement;

// 2D Context
type Ctx2D = CanvasRenderingContext2D;

// 座標點
interface Point {
  x: number;
  y: number;
}

// 矩形區域
interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

// 顏色（字串或 CanvasGradient 或 CanvasPattern）
type CanvasColor = string | CanvasGradient | CanvasPattern;

// 繪圖選項
interface DrawOptions {
  fillStyle?: CanvasColor;
  strokeStyle?: CanvasColor;
  lineWidth?: number;
  lineCap?: CanvasLineCap;   // "butt" | "round" | "square"
  lineJoin?: CanvasLineJoin; // "bevel" | "miter" | "round"
  globalAlpha?: number;
  shadowBlur?: number;
  shadowColor?: string;
  shadowOffsetX?: number;
  shadowOffsetY?: number;
}

// 文字選項
interface TextOptions extends DrawOptions {
  font?: string;
  textAlign?: CanvasTextAlign;   // "left" | "right" | "center" | "start" | "end"
  textBaseline?: CanvasTextBaseline; // "top" | "middle" | "bottom" | "alphabetic" ...
}

// 動畫狀態
interface AnimationState {
  isRunning: boolean;
  frameId: number | null;
  fps: number;
  lastTime: number;
}

// 事件座標（轉換後的 Canvas 座標）
interface CanvasPointerEvent {
  canvasX: number;
  canvasY: number;
  originalEvent: MouseEvent | TouchEvent;
}
```

### 2.2 型別守衛 (Type Guards)

```tsx
// 判斷是否為 TouchEvent
function isTouchEvent(e: MouseEvent | TouchEvent): e is TouchEvent {
  return 'touches' in e;
}

// 取得 canvas 座標（適用 Mouse 和 Touch）
function getCanvasCoords(
  e: MouseEvent | TouchEvent,
  canvas: HTMLCanvasElement
): Point {
  const rect = canvas.getBoundingClientRect();
  const clientX = isTouchEvent(e) ? e.touches[0].clientX : e.clientX;
  const clientY = isTouchEvent(e) ? e.touches[0].clientY : e.clientY;

  return {
    x: clientX - rect.left,
    y: clientY - rect.top,
  };
}
```

---

## 3. useCanvas 自訂 Hook

### 3.1 基礎版 useCanvas

```tsx
// hooks/useCanvas.ts
import { useRef, useEffect, useCallback } from 'react';
import { setupHiDPI } from '../utils/setupHiDPI';

type DrawFunction = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => void;

interface UseCanvasOptions {
  onDraw?: DrawFunction;
  autoResize?: boolean;
}

export function useCanvas(options: UseCanvasOptions = {}) {
  const { onDraw, autoResize = true } = options;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx || !onDraw) return;
    onDraw(ctx, canvas);
  }, [onDraw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    ctxRef.current = setupHiDPI(canvas);
    draw();

    if (!autoResize) return;

    const resizeObserver = new ResizeObserver(() => {
      if (canvas && ctxRef.current) {
        ctxRef.current = setupHiDPI(canvas);
        draw();
      }
    });

    resizeObserver.observe(canvas);
    return () => resizeObserver.disconnect();
  }, [draw, autoResize]);

  return { canvasRef, ctx: ctxRef.current };
}
```

```tsx
// 使用範例
const MyCanvas: React.FC = () => {
  const { canvasRef } = useCanvas({
    onDraw: (ctx, canvas) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      ctx.arc(150, 150, 80, 0, Math.PI * 2);
      ctx.fillStyle = 'cornflowerblue';
      ctx.fill();
    },
  });

  return <canvas ref={canvasRef} style={{ width: '100%', height: '300px' }} />;
};
```

### 3.2 動畫版 useAnimationCanvas

```tsx
// hooks/useAnimationCanvas.ts
import { useRef, useEffect, useCallback } from 'react';
import { setupHiDPI } from '../utils/setupHiDPI';

type AnimateFunction = (
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  deltaTime: number,  // 距上一幀的毫秒數
  elapsed: number     // 總經過毫秒數
) => void;

export function useAnimationCanvas(onAnimate: AnimateFunction) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameIdRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  const stop = useCallback(() => {
    if (frameIdRef.current !== null) {
      cancelAnimationFrame(frameIdRef.current);
      frameIdRef.current = null;
    }
  }, []);

  const start = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const loop = (timestamp: number) => {
      if (startTimeRef.current === 0) startTimeRef.current = timestamp;

      const deltaTime = timestamp - lastTimeRef.current;
      const elapsed = timestamp - startTimeRef.current;
      lastTimeRef.current = timestamp;

      onAnimate(ctx, canvas, deltaTime, elapsed);

      frameIdRef.current = requestAnimationFrame(loop);
    };

    frameIdRef.current = requestAnimationFrame(loop);
  }, [onAnimate]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    setupHiDPI(canvas);
    start();
    return () => stop();
  }, [start, stop]);

  return { canvasRef, start, stop };
}
```

```tsx
// 使用範例：旋轉的圓
const RotatingCircle: React.FC = () => {
  const { canvasRef } = useAnimationCanvas((ctx, canvas, deltaTime, elapsed) => {
    const { width, height } = canvas.getBoundingClientRect();
    ctx.clearRect(0, 0, width, height);

    const angle = elapsed * 0.002; // 每毫秒轉 0.002 弧度
    const cx = width / 2;
    const cy = height / 2;
    const r = 80;

    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;

    ctx.beginPath();
    ctx.arc(x, y, 20, 0, Math.PI * 2);
    ctx.fillStyle = `hsl(${elapsed * 0.1 % 360}, 70%, 60%)`;
    ctx.fill();
  });

  return <canvas ref={canvasRef} style={{ width: '400px', height: '400px' }} />;
};
```

---

## 4. 2D 繪圖 API 完整參考

### 4.1 矩形

```tsx
// 填色矩形
ctx.fillRect(x, y, width, height);

// 描邊矩形
ctx.strokeRect(x, y, width, height);

// 清除矩形區域（變透明）
ctx.clearRect(x, y, width, height);
```

### 4.2 路徑 (Path)

```tsx
// 路徑的基本流程
ctx.beginPath();        // 開始新路徑（必須）
ctx.moveTo(x, y);       // 移動起始點（不畫線）
ctx.lineTo(x, y);       // 直線到某點
ctx.arc(cx, cy, r, startAngle, endAngle, counterclockwise?); // 圓弧
ctx.arcTo(x1, y1, x2, y2, radius); // 切線圓弧
ctx.quadraticCurveTo(cpx, cpy, x, y); // 二次貝茲曲線
ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y); // 三次貝茲曲線
ctx.rect(x, y, w, h);   // 矩形路徑
ctx.ellipse(cx, cy, rx, ry, rotation, startAngle, endAngle); // 橢圓
ctx.closePath();        // 閉合路徑（連回起點）

// 執行繪製
ctx.fill();             // 填充
ctx.stroke();           // 描邊
ctx.clip();             // 設為裁切遮罩
```

### 4.3 樣式設定

```tsx
// 顏色
ctx.fillStyle = 'red';
ctx.fillStyle = '#FF5733';
ctx.fillStyle = 'rgba(255, 87, 51, 0.5)';
ctx.fillStyle = 'hsl(20, 100%, 60%)';

// 漸層
const linearGrad = ctx.createLinearGradient(x0, y0, x1, y1);
linearGrad.addColorStop(0, 'red');
linearGrad.addColorStop(0.5, 'yellow');
linearGrad.addColorStop(1, 'blue');
ctx.fillStyle = linearGrad;

const radialGrad = ctx.createRadialGradient(cx0, cy0, r0, cx1, cy1, r1);
radialGrad.addColorStop(0, 'white');
radialGrad.addColorStop(1, 'black');
ctx.fillStyle = radialGrad;

// 圖案填充
const img = new Image();
img.onload = () => {
  const pattern = ctx.createPattern(img, 'repeat'); // 'repeat' | 'no-repeat' | 'repeat-x' | 'repeat-y'
  if (pattern) ctx.fillStyle = pattern;
  ctx.fillRect(0, 0, 400, 400);
};
img.src = '/pattern.png';

// 線條樣式
ctx.lineWidth = 3;
ctx.lineCap = 'round';    // 'butt' | 'round' | 'square'
ctx.lineJoin = 'round';   // 'bevel' | 'round' | 'miter'
ctx.miterLimit = 10;
ctx.setLineDash([10, 5]); // 虛線：10px 實線 + 5px 空白
ctx.lineDashOffset = 0;   // 虛線起始偏移

// 透明度
ctx.globalAlpha = 0.5; // 0 (全透明) 到 1 (不透明)

// 混合模式
ctx.globalCompositeOperation = 'source-over'; // 預設
// 其他常用值：'multiply', 'screen', 'overlay', 'destination-out' (橡皮擦效果)
```

### 4.4 文字

```tsx
// 字型設定（與 CSS font 語法相同）
ctx.font = '600 24px "Noto Sans TC", sans-serif';
ctx.textAlign = 'center';       // 'left' | 'right' | 'center' | 'start' | 'end'
ctx.textBaseline = 'middle';    // 'top' | 'middle' | 'bottom' | 'alphabetic' | 'hanging'
ctx.direction = 'ltr';          // 'ltr' | 'rtl' | 'inherit'

// 繪製文字
ctx.fillText('你好世界', x, y);
ctx.fillText('最多50字元', x, y, 200); // 第4參數：最大寬度（自動縮小）

ctx.strokeText('空心字', x, y);

// 測量文字寬度
const metrics = ctx.measureText('測試文字');
console.log(metrics.width);             // 文字寬度
console.log(metrics.actualBoundingBoxAscent); // 基線以上高度
console.log(metrics.actualBoundingBoxDescent); // 基線以下高度
```

### 4.5 影像繪製

```tsx
// 繪製圖片的幾種方式
const img = new Image();
img.onload = () => {
  // 方式1：指定位置
  ctx.drawImage(img, dx, dy);

  // 方式2：指定位置和尺寸（縮放）
  ctx.drawImage(img, dx, dy, dWidth, dHeight);

  // 方式3：裁切 + 縮放（9個參數）
  // sx, sy = 來源裁切起點
  // sw, sh = 來源裁切大小
  // dx, dy = 目標起點
  // dw, dh = 目標大小
  ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dWidth, dHeight);
};
img.src = '/image.png';

// 也可以繪製 canvas 本身、video 元素
const video = document.querySelector('video') as HTMLVideoElement;
ctx.drawImage(video, 0, 0);
```

### 4.6 陰影

```tsx
ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
ctx.shadowBlur = 10;
ctx.shadowOffsetX = 5;
ctx.shadowOffsetY = 5;

ctx.fillRect(50, 50, 200, 100); // 會有陰影

// 關閉陰影
ctx.shadowColor = 'transparent';
ctx.shadowBlur = 0;
```

### 4.7 座標變換

```tsx
// 平移
ctx.translate(tx, ty);

// 旋轉（弧度）
ctx.rotate(Math.PI / 4); // 45 度

// 縮放
ctx.scale(sx, sy);

// 自訂變換矩陣（a, b, c, d, e, f）
ctx.transform(a, b, c, d, e, f);

// 重置為單位矩陣
ctx.setTransform(1, 0, 0, 1, 0, 0);

// 儲存與還原狀態（包含所有樣式和變換）
ctx.save();
  ctx.translate(100, 100);
  ctx.rotate(Math.PI / 6);
  ctx.fillStyle = 'red';
  ctx.fillRect(-25, -25, 50, 50);
ctx.restore(); // 恢復到 save() 前的狀態
```

---

## 5. 動畫迴圈 (Animation Loop)

### 5.1 requestAnimationFrame 基礎

```tsx
class AnimationLoop {
  private frameId: number | null = null;
  private lastTime = 0;
  private onFrame: (dt: number) => void;

  constructor(onFrame: (dt: number) => void) {
    this.onFrame = onFrame;
  }

  start() {
    const loop = (time: number) => {
      const dt = this.lastTime === 0 ? 0 : time - this.lastTime;
      this.lastTime = time;
      this.onFrame(dt);
      this.frameId = requestAnimationFrame(loop);
    };
    this.frameId = requestAnimationFrame(loop);
  }

  stop() {
    if (this.frameId !== null) {
      cancelAnimationFrame(this.frameId);
      this.frameId = null;
      this.lastTime = 0;
    }
  }
}
```

### 5.2 限制 FPS（省電模式）

```tsx
function useLimitedFPS(targetFPS: number, onFrame: (dt: number) => void) {
  const interval = 1000 / targetFPS;
  const lastTimeRef = useRef(0);
  const frameIdRef = useRef<number | null>(null);

  useEffect(() => {
    const loop = (time: number) => {
      frameIdRef.current = requestAnimationFrame(loop);
      const dt = time - lastTimeRef.current;
      if (dt < interval) return; // 還沒到下一幀
      lastTimeRef.current = time - (dt % interval); // 校正時間
      onFrame(dt);
    };

    frameIdRef.current = requestAnimationFrame(loop);
    return () => {
      if (frameIdRef.current) cancelAnimationFrame(frameIdRef.current);
    };
  }, [onFrame, interval]);
}
```

### 5.3 緩動函數 (Easing)

```tsx
// easing.ts
export const Easing = {
  linear: (t: number) => t,
  easeIn: (t: number) => t * t,
  easeOut: (t: number) => t * (2 - t),
  easeInOut: (t: number) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  easeInCubic: (t: number) => t * t * t,
  easeOutCubic: (t: number) => (--t) * t * t + 1,
  easeInOutCubic: (t: number) =>
    t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
  bounce: (t: number) => {
    if (t < 1 / 2.75) return 7.5625 * t * t;
    if (t < 2 / 2.75) return 7.5625 * (t -= 1.5 / 2.75) * t + 0.75;
    if (t < 2.5 / 2.75) return 7.5625 * (t -= 2.25 / 2.75) * t + 0.9375;
    return 7.5625 * (t -= 2.625 / 2.75) * t + 0.984375;
  },
};

// 使用：從 fromValue 到 toValue，duration 毫秒
function lerp(from: number, to: number, t: number): number {
  return from + (to - from) * t;
}

// 範例：動畫物件從 x=0 移動到 x=300，持續 1000ms
let startTime: number | null = null;
const duration = 1000;
const from = 0;
const to = 300;

function animate(time: number) {
  if (!startTime) startTime = time;
  const elapsed = time - startTime;
  const t = Math.min(elapsed / duration, 1); // 0 到 1
  const easedT = Easing.easeOutCubic(t);
  const x = lerp(from, to, easedT);

  ctx.clearRect(0, 0, 800, 600);
  ctx.fillRect(x, 200, 50, 50);

  if (t < 1) requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

---

## 6. 互動事件 (Mouse / Touch)

### 6.1 滑鼠事件完整處理

```tsx
// hooks/useCanvasEvents.ts
import { useEffect, useCallback } from 'react';

interface CanvasPoint {
  x: number;
  y: number;
}

interface CanvasEventHandlers {
  onMouseDown?: (point: CanvasPoint, e: MouseEvent) => void;
  onMouseMove?: (point: CanvasPoint, e: MouseEvent) => void;
  onMouseUp?: (point: CanvasPoint, e: MouseEvent) => void;
  onMouseLeave?: () => void;
  onClick?: (point: CanvasPoint, e: MouseEvent) => void;
  onWheel?: (delta: number, point: CanvasPoint, e: WheelEvent) => void;
}

function getPoint(e: MouseEvent, canvas: HTMLCanvasElement): CanvasPoint {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;

  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  };
}

export function useCanvasEvents(
  canvasRef: React.RefObject<HTMLCanvasElement>,
  handlers: CanvasEventHandlers
) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseDown = (e: MouseEvent) => {
      handlers.onMouseDown?.(getPoint(e, canvas), e);
    };
    const handleMouseMove = (e: MouseEvent) => {
      handlers.onMouseMove?.(getPoint(e, canvas), e);
    };
    const handleMouseUp = (e: MouseEvent) => {
      handlers.onMouseUp?.(getPoint(e, canvas), e);
    };
    const handleMouseLeave = () => {
      handlers.onMouseLeave?.();
    };
    const handleClick = (e: MouseEvent) => {
      handlers.onClick?.(getPoint(e, canvas), e);
    };
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      handlers.onWheel?.(e.deltaY, getPoint(e, canvas), e);
    };

    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseLeave);
    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      canvas.removeEventListener('click', handleClick);
      canvas.removeEventListener('wheel', handleWheel);
    };
  }, [canvasRef, handlers]);
}
```

### 6.2 Touch 事件（手機支援）

```tsx
// hooks/useTouchCanvas.ts

interface TouchPoint {
  x: number;
  y: number;
  id: number;  // touch identifier（多指觸控用）
}

function getTouchPoints(e: TouchEvent, canvas: HTMLCanvasElement): TouchPoint[] {
  const rect = canvas.getBoundingClientRect();
  return Array.from(e.touches).map(touch => ({
    id: touch.identifier,
    x: touch.clientX - rect.left,
    y: touch.clientY - rect.top,
  }));
}

export function useTouchCanvas(
  canvasRef: React.RefObject<HTMLCanvasElement>,
  handlers: {
    onTouchStart?: (points: TouchPoint[], e: TouchEvent) => void;
    onTouchMove?: (points: TouchPoint[], e: TouchEvent) => void;
    onTouchEnd?: (e: TouchEvent) => void;
  }
) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const onStart = (e: TouchEvent) => {
      e.preventDefault(); // 防止滾動
      handlers.onTouchStart?.(getTouchPoints(e, canvas), e);
    };
    const onMove = (e: TouchEvent) => {
      e.preventDefault();
      handlers.onTouchMove?.(getTouchPoints(e, canvas), e);
    };
    const onEnd = (e: TouchEvent) => {
      handlers.onTouchEnd?.(e);
    };

    canvas.addEventListener('touchstart', onStart, { passive: false });
    canvas.addEventListener('touchmove', onMove, { passive: false });
    canvas.addEventListener('touchend', onEnd);

    return () => {
      canvas.removeEventListener('touchstart', onStart);
      canvas.removeEventListener('touchmove', onMove);
      canvas.removeEventListener('touchend', onEnd);
    };
  }, [canvasRef, handlers]);
}
```

### 6.3 點選偵測 (Hit Testing)

```tsx
// 偵測點是否在某形狀內
function isPointInRect(point: Point, rect: Rect): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

function isPointInCircle(point: Point, cx: number, cy: number, r: number): boolean {
  const dx = point.x - cx;
  const dy = point.y - cy;
  return dx * dx + dy * dy <= r * r;
}

// 使用 isPointInPath 偵測複雜形狀
function isPointInComplexShape(ctx: Ctx2D, point: Point): boolean {
  ctx.beginPath();
  // 畫出形狀路徑（不需要實際 fill/stroke）
  ctx.moveTo(100, 50);
  ctx.lineTo(200, 150);
  ctx.lineTo(50, 150);
  ctx.closePath();
  return ctx.isPointInPath(point.x, point.y);
}
```

---

## 7. 影像處理與濾鏡

### 7.1 像素操作 (ImageData)

```tsx
// 取得像素資料
const imageData = ctx.getImageData(x, y, width, height);
const pixels = imageData.data; // Uint8ClampedArray，每4個值 = 1像素 (R, G, B, A)

// 像素陣列結構
// pixels[i]   = Red   (0-255)
// pixels[i+1] = Green (0-255)
// pixels[i+2] = Blue  (0-255)
// pixels[i+3] = Alpha (0-255)

// 取得特定像素的函式
function getPixel(pixels: Uint8ClampedArray, x: number, y: number, width: number) {
  const i = (y * width + x) * 4;
  return {
    r: pixels[i],
    g: pixels[i + 1],
    b: pixels[i + 2],
    a: pixels[i + 3],
  };
}

// 設定特定像素
function setPixel(
  pixels: Uint8ClampedArray,
  x: number,
  y: number,
  width: number,
  r: number, g: number, b: number, a: number
) {
  const i = (y * width + x) * 4;
  pixels[i] = r;
  pixels[i + 1] = g;
  pixels[i + 2] = b;
  pixels[i + 3] = a;
}

// 套用修改後放回 canvas
ctx.putImageData(imageData, x, y);
```

### 7.2 常用濾鏡實作

```tsx
// 灰階濾鏡
function applyGrayscale(ctx: Ctx2D, width: number, height: number) {
  const imageData = ctx.getImageData(0, 0, width, height);
  const pixels = imageData.data;

  for (let i = 0; i < pixels.length; i += 4) {
    // 人眼對綠色最敏感，這個係數是標準 luminance 公式
    const gray = pixels[i] * 0.299 + pixels[i + 1] * 0.587 + pixels[i + 2] * 0.114;
    pixels[i] = pixels[i + 1] = pixels[i + 2] = gray;
  }

  ctx.putImageData(imageData, 0, 0);
}

// 反色濾鏡
function applyInvert(ctx: Ctx2D, width: number, height: number) {
  const imageData = ctx.getImageData(0, 0, width, height);
  const pixels = imageData.data;

  for (let i = 0; i < pixels.length; i += 4) {
    pixels[i] = 255 - pixels[i];
    pixels[i + 1] = 255 - pixels[i + 1];
    pixels[i + 2] = 255 - pixels[i + 2];
    // Alpha 不改變
  }

  ctx.putImageData(imageData, 0, 0);
}

// 亮度和對比調整
function adjustBrightnessContrast(
  ctx: Ctx2D,
  width: number,
  height: number,
  brightness: number,  // -255 到 255
  contrast: number     // -255 到 255
) {
  const imageData = ctx.getImageData(0, 0, width, height);
  const pixels = imageData.data;
  const factor = (259 * (contrast + 255)) / (255 * (259 - contrast));

  for (let i = 0; i < pixels.length; i += 4) {
    pixels[i] = Math.min(255, Math.max(0, factor * (pixels[i] - 128) + 128 + brightness));
    pixels[i + 1] = Math.min(255, Math.max(0, factor * (pixels[i + 1] - 128) + 128 + brightness));
    pixels[i + 2] = Math.min(255, Math.max(0, factor * (pixels[i + 2] - 128) + 128 + brightness));
  }

  ctx.putImageData(imageData, 0, 0);
}

// 高斯模糊（使用 CSS filter 更快）
function applyBlurViaCSSFilter(ctx: Ctx2D, radius: number) {
  ctx.filter = `blur(${radius}px)`;
  // 之後的繪製都會套用模糊
  // 記得用完後恢復
}

function resetFilter(ctx: Ctx2D) {
  ctx.filter = 'none';
}
```

### 7.3 匯出與儲存

```tsx
// 匯出為 PNG（預設）
function downloadCanvas(canvas: HTMLCanvasElement, filename = 'canvas.png') {
  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

// 匯出為 JPEG（有壓縮，檔案較小）
function downloadCanvasJPEG(canvas: HTMLCanvasElement, quality = 0.9) {
  const link = document.createElement('a');
  link.download = 'canvas.jpg';
  link.href = canvas.toDataURL('image/jpeg', quality); // quality: 0 到 1
  link.click();
}

// 匯出為 Blob（上傳到伺服器用）
async function getCanvasBlob(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) resolve(blob);
        else reject(new Error('無法產生 Blob'));
      },
      'image/png'
    );
  });
}

// 上傳到伺服器
async function uploadCanvas(canvas: HTMLCanvasElement, uploadUrl: string) {
  const blob = await getCanvasBlob(canvas);
  const formData = new FormData();
  formData.append('image', blob, 'canvas.png');

  const response = await fetch(uploadUrl, {
    method: 'POST',
    body: formData,
  });

  return response.json();
}
```

---

## 8. 效能優化技巧

### 8.1 離屏 Canvas (OffscreenCanvas)

```tsx
// 將複雜但不常變的內容繪製到離屏 Canvas，再貼到主 Canvas
// 這樣每幀只需要 drawImage，不需要重新計算

function createOffscreenBackground(width: number, height: number): HTMLCanvasElement {
  const offscreen = document.createElement('canvas');
  offscreen.width = width;
  offscreen.height = height;
  const ctx = offscreen.getContext('2d')!;

  // 繪製複雜的靜態背景
  for (let i = 0; i < 1000; i++) {
    ctx.beginPath();
    ctx.arc(
      Math.random() * width,
      Math.random() * height,
      Math.random() * 5,
      0,
      Math.PI * 2
    );
    ctx.fillStyle = `hsl(${Math.random() * 360}, 70%, 60%)`;
    ctx.fill();
  }

  return offscreen;
}

// 每幀只做一次 drawImage
const bgCanvas = createOffscreenBackground(800, 600);
function render(ctx: Ctx2D) {
  ctx.drawImage(bgCanvas, 0, 0); // 非常快
  // 再繪製動態內容...
}
```

### 8.2 在 Web Worker 中使用 OffscreenCanvas

```tsx
// main.tsx
const canvasRef = useRef<HTMLCanvasElement>(null);

useEffect(() => {
  const canvas = canvasRef.current;
  if (!canvas) return;

  // 將 canvas 的控制權轉移給 Worker
  const offscreen = canvas.transferControlToOffscreen();
  const worker = new Worker(new URL('./canvas.worker.ts', import.meta.url));

  worker.postMessage({ canvas: offscreen }, [offscreen]);

  return () => worker.terminate();
}, []);
```

```tsx
// canvas.worker.ts
self.onmessage = (e: MessageEvent) => {
  const { canvas } = e.data as { canvas: OffscreenCanvas };
  const ctx = canvas.getContext('2d')!;

  // 動畫迴圈在 Worker 中執行，不佔用主執行緒
  function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // ... 繪圖邏輯
    // 注意：Worker 中沒有 requestAnimationFrame，需要 MessageChannel 或 setTimeout 替代
  }

  // 使用 MessageChannel 實現 Worker 中的 rAF
  const channel = new MessageChannel();
  channel.port2.onmessage = loop;
  channel.port1.postMessage(null);
};
```

### 8.3 其他優化技巧

```tsx
// 1. 避免不必要的狀態切換，批次設定
// 差（每次切換 fillStyle）
items.forEach(item => {
  ctx.fillStyle = item.color; // 觸發 GPU 狀態切換
  ctx.fillRect(item.x, item.y, item.w, item.h);
});

// 好（依顏色分組）
const groups = new Map<string, typeof items>();
items.forEach(item => {
  const group = groups.get(item.color) ?? [];
  group.push(item);
  groups.set(item.color, group);
});
groups.forEach((group, color) => {
  ctx.fillStyle = color;
  group.forEach(item => ctx.fillRect(item.x, item.y, item.w, item.h));
});

// 2. 使用整數座標（避免反鋸齒計算）
// 差
ctx.fillRect(10.5, 20.3, 100.7, 50.1);
// 好
ctx.fillRect(Math.round(10.5), Math.round(20.3), Math.round(100.7), Math.round(50.1));

// 3. 只重繪「髒」的區域
function renderDirty(ctx: Ctx2D, dirtyRect: Rect) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(dirtyRect.x, dirtyRect.y, dirtyRect.width, dirtyRect.height);
  ctx.clip();

  // 清除並重繪髒區域
  ctx.clearRect(dirtyRect.x, dirtyRect.y, dirtyRect.width, dirtyRect.height);
  // ... 只繪製髒區域內的物件

  ctx.restore();
}

// 4. will-change 提示瀏覽器優化
// 在 CSS 或 style 屬性加上
// style={{ willChange: 'transform' }}
```

---

## 9. 進階技術

### 9.1 多層 Canvas 架構

```tsx
// 靜態背景 + 動態前景，分層繪製提高效能
const MultiLayerCanvas: React.FC = () => {
  const bgRef = useRef<HTMLCanvasElement>(null);       // 靜態背景層
  const dynamicRef = useRef<HTMLCanvasElement>(null);  // 動態內容層
  const uiRef = useRef<HTMLCanvasElement>(null);       // UI 互動層

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    width: '800px',
    height: '600px',
  };

  const canvasStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
  };

  return (
    <div style={containerStyle}>
      <canvas ref={bgRef} style={{ ...canvasStyle, zIndex: 1 }} />
      <canvas ref={dynamicRef} style={{ ...canvasStyle, zIndex: 2 }} />
      <canvas ref={uiRef} style={{ ...canvasStyle, zIndex: 3 }} />
    </div>
  );
};
```

### 9.2 可撤銷的繪圖操作 (Undo / Redo)

```tsx
class CanvasHistory {
  private states: ImageData[] = [];
  private index = -1;
  private maxSteps: number;

  constructor(maxSteps = 50) {
    this.maxSteps = maxSteps;
  }

  // 儲存當前狀態
  save(ctx: Ctx2D, width: number, height: number) {
    // 刪除 index 之後的歷史（新操作覆蓋 redo 堆）
    this.states = this.states.slice(0, this.index + 1);

    const state = ctx.getImageData(0, 0, width, height);
    this.states.push(state);

    // 超過上限，移除最舊的
    if (this.states.length > this.maxSteps) {
      this.states.shift();
    }

    this.index = this.states.length - 1;
  }

  undo(ctx: Ctx2D): boolean {
    if (this.index <= 0) return false;
    this.index--;
    ctx.putImageData(this.states[this.index], 0, 0);
    return true;
  }

  redo(ctx: Ctx2D): boolean {
    if (this.index >= this.states.length - 1) return false;
    this.index++;
    ctx.putImageData(this.states[this.index], 0, 0);
    return true;
  }

  canUndo = () => this.index > 0;
  canRedo = () => this.index < this.states.length - 1;
}
```

### 9.3 縮放與平移 (Pan / Zoom)

```tsx
interface ViewTransform {
  scale: number;
  offsetX: number;
  offsetY: number;
}

function worldToScreen(point: Point, view: ViewTransform): Point {
  return {
    x: point.x * view.scale + view.offsetX,
    y: point.y * view.scale + view.offsetY,
  };
}

function screenToWorld(point: Point, view: ViewTransform): Point {
  return {
    x: (point.x - view.offsetX) / view.scale,
    y: (point.y - view.offsetY) / view.scale,
  };
}

// 以滑鼠位置為中心縮放
function zoomAtPoint(
  view: ViewTransform,
  point: Point, // 螢幕座標
  zoomFactor: number
): ViewTransform {
  const newScale = Math.min(Math.max(view.scale * zoomFactor, 0.1), 20);

  // 縮放前世界座標
  const worldX = (point.x - view.offsetX) / view.scale;
  const worldY = (point.y - view.offsetY) / view.scale;

  return {
    scale: newScale,
    offsetX: point.x - worldX * newScale,
    offsetY: point.y - worldY * newScale,
  };
}

// 在每幀渲染前套用變換
function applyViewTransform(ctx: Ctx2D, view: ViewTransform) {
  ctx.setTransform(view.scale, 0, 0, view.scale, view.offsetX, view.offsetY);
}
```

---

## 10. 完整範例：互動式畫板

```tsx
// DrawingBoard.tsx
import React, { useRef, useEffect, useCallback, useState } from 'react';

interface DrawingTool {
  type: 'pen' | 'eraser' | 'line' | 'rect' | 'circle';
  color: string;
  size: number;
}

const DrawingBoard: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const isDrawingRef = useRef(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const snapshotRef = useRef<ImageData | null>(null);

  const [tool, setTool] = useState<DrawingTool>({
    type: 'pen',
    color: '#000000',
    size: 4,
  });

  // 初始化 Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d')!;
    ctx.scale(dpr, dpr);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctxRef.current = ctx;

    // 白色背景
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, rect.width, rect.height);
  }, []);

  const getPoint = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }, []);

  const startDrawing = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const ctx = ctxRef.current;
    const canvas = canvasRef.current;
    if (!ctx || !canvas) return;

    isDrawingRef.current = true;
    lastPointRef.current = getPoint(e);

    // 儲存快照（用於 line、rect、circle 工具）
    const rect = canvas.getBoundingClientRect();
    snapshotRef.current = ctx.getImageData(0, 0, rect.width, rect.height);

    ctx.beginPath();
    ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
  }, [getPoint]);

  const draw = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current || !ctxRef.current || !lastPointRef.current) return;
    const ctx = ctxRef.current;
    const canvas = canvasRef.current!;
    const point = getPoint(e);
    const start = lastPointRef.current;

    ctx.lineWidth = tool.size;
    ctx.strokeStyle = tool.type === 'eraser' ? 'white' : tool.color;

    if (tool.type === 'pen' || tool.type === 'eraser') {
      ctx.lineTo(point.x, point.y);
      ctx.stroke();
      lastPointRef.current = point;
    } else {
      // 還原快照，再畫新的形狀預覽
      const rect = canvas.getBoundingClientRect();
      ctx.putImageData(snapshotRef.current!, 0, 0);
      ctx.beginPath();

      if (tool.type === 'line') {
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(point.x, point.y);
        ctx.stroke();
      } else if (tool.type === 'rect') {
        ctx.strokeRect(
          start.x,
          start.y,
          point.x - start.x,
          point.y - start.y
        );
      } else if (tool.type === 'circle') {
        const r = Math.sqrt(
          Math.pow(point.x - start.x, 2) + Math.pow(point.y - start.y, 2)
        );
        ctx.arc(start.x, start.y, r, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }, [tool, getPoint]);

  const stopDrawing = useCallback(() => {
    isDrawingRef.current = false;
    lastPointRef.current = null;
    ctxRef.current?.beginPath();
  }, []);

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;
    const rect = canvas.getBoundingClientRect();
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, rect.width, rect.height);
  }, []);

  const downloadCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = 'drawing.png';
    link.href = canvas.toDataURL();
    link.click();
  }, []);

  const tools: Array<DrawingTool['type']> = ['pen', 'eraser', 'line', 'rect', 'circle'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* 工具列 */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: 8, background: '#f5f5f5' }}>
        {tools.map(t => (
          <button
            key={t}
            onClick={() => setTool(prev => ({ ...prev, type: t }))}
            style={{
              padding: '4px 12px',
              background: tool.type === t ? '#4CAF50' : '#fff',
              color: tool.type === t ? 'white' : 'black',
              border: '1px solid #ccc',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            {t}
          </button>
        ))}
        <input
          type="color"
          value={tool.color}
          onChange={e => setTool(prev => ({ ...prev, color: e.target.value }))}
        />
        <input
          type="range"
          min={1}
          max={50}
          value={tool.size}
          onChange={e => setTool(prev => ({ ...prev, size: Number(e.target.value) }))}
        />
        <button onClick={clearCanvas}>清除</button>
        <button onClick={downloadCanvas}>下載</button>
      </div>

      {/* 畫布 */}
      <canvas
        ref={canvasRef}
        onMouseDown={startDrawing}
        onMouseMove={draw}
        onMouseUp={stopDrawing}
        onMouseLeave={stopDrawing}
        style={{
          width: '100%',
          height: '500px',
          cursor: tool.type === 'eraser' ? 'cell' : 'crosshair',
          border: '1px solid #ddd',
        }}
      />
    </div>
  );
};

export default DrawingBoard;
```

---

## 11. 常見錯誤與解法

| 問題 | 原因 | 解法 |
| --- | --- | --- |
| 畫面模糊 | 沒有處理 devicePixelRatio | 套用 HiDPI 設定，設定 canvas.width = offsetWidth × dpr |
| getContext 回傳 null | Canvas 尚未掛載 | 確認在 useEffect 內，且元素存在 |
| 動畫越來越慢 | 沒有 cancelAnimationFrame | 在 useEffect 的 cleanup 中呼叫 cancel |
| 記憶體洩漏 | event listener 沒有移除 | 在 cleanup 函式中移除所有 listener |
| 圖片無法繪製 | 圖片未載入完成 | 在 img.onload 回呼中呼叫 drawImage |
| Canvas 事件無法觸發 | z-index 被覆蓋 | 確認 pointer-events CSS 屬性 |
| toDataURL CORS 錯誤 | 跨來源圖片汙染 canvas | 圖片來源設定 `img.crossOrigin = 'anonymous'` |
| 行動裝置觸控滾動 | touch event 未阻止預設行為 | `e.preventDefault()` 並用 `{ passive: false }` |

---

## 12. 最佳實踐清單

**設置階段**
- 永遠在 `useEffect` 中初始化 Canvas，不要在渲染函式中直接操作
- 永遠處理 HiDPI，避免模糊問題
- 使用 `ResizeObserver` 監聽尺寸變化並重繪

**繪圖階段**
- 每次繪圖前用 `ctx.save()`，結束後用 `ctx.restore()`
- 批次設定相同樣式，減少狀態切換
- 優先使用 `fillRect`、`strokeRect` 代替手動路徑畫矩形（效能更好）
- 靜態內容使用離屏 Canvas 快取

**動畫階段**
- 只用 `requestAnimationFrame`，不用 `setInterval`
- 使用 `deltaTime` 讓動畫速度與幀率無關
- 在 `useEffect` cleanup 中一定要 `cancelAnimationFrame`

**事件處理**
- 在 `useEffect` cleanup 中移除所有 event listener
- 行動裝置觸控事件要加 `{ passive: false }` 才能 `preventDefault`
- 統一使用座標轉換函式，避免重複計算

**資源管理**
- 用 `canvas.toBlob()` 代替 `toDataURL()`，對大圖較省記憶體
- `createPattern`、`createLinearGradient` 盡量快取，不要每幀重建
- Worker + OffscreenCanvas 用於複雜計算，避免阻塞主執行緒

---

*手冊版本：2025年版 | 適用 React 18+, TypeScript 5+*