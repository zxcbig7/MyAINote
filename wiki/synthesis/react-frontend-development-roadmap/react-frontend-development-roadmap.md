---
type: synthesis
domain: tech
tags: [react, typescript, frontend, roadmap, spa]
sources:
  - raw/Web Framework/React/React.md
  - raw/Web Framework/React/React Visualized — 一本書學 React.md
  - raw/Web Framework/React/React Visualized/React Visualized.md
  - raw/Web Framework/React/DOM 節點觀念.md
  - raw/Web Framework/React/React + TypeScript 開發手冊.md
  - raw/Web Framework/React/React_TypeScript_Guide.md
  - raw/Web Framework/React/type vs interface.md
  - raw/Web Framework/React/React-Hooks-用途筆記與TypeScript範例.md
  - raw/Web Framework/React/react-hooks-gotchas/react-hooks-gotchas.md
  - raw/Web Framework/React/AuthProvider & Route 概念.md
  - raw/Web Framework/React/API 設計.md
  - raw/Web Framework/React/前端傳輸概念 (axios + React Query+Promise).md
  - raw/Web Framework/React/Tailwind CSS 開發.md
  - raw/Web Framework/React/React 生態系資源.md
  - raw/Web Framework/React/Tic-Tac-Toe Example.md
  - raw/Web Framework/React/React TypeScript Canvas 手冊.md
  - raw/Web Framework/React/Monorepo 架構.md
created: 2026-10-17
updated: 2026-10-17
---

# React 前端開發 roadmap

這份路線的起點是假設你已能寫基本的 HTML、CSS 與 JavaScript，但還不能穩定地完成一個可維護的前端功能。終點則是能以 TypeScript 寫出有路由、登入、資料取得、表單驗證與部署設定的 React SPA，並知道哪些情況才需要效能優化、全域狀態或 Monorepo。

它不是要你依序蒐集 library。React 的難點通常不在 API 的數量，而在於先把「畫面是 state 的函式」這個模型建立好；否則後面的 `useEffect`、React Query 與 Context 都只會變成容易出錯的範本。

## 全局地圖

```text
Web 基礎與 TypeScript
        ↓
React 心智模型與 Component
        ↓
State、事件與渲染
        ↓
Effect、Ref 與 Custom Hook
        ↓
樣式、表單與可重用 UI
        ↓
路由、Auth 與 API / Server State
        ↓
專案架構、測試、效能與部署
        ↓
選修：Canvas、Concurrent React、Server Components、Monorepo
```

## 第 0 階段：不要跳過 Web 與 TypeScript

React 並不取代瀏覽器。JSX 最後仍會產生 DOM，事件仍會冒泡，網路請求仍是 Promise；不理解這些邊界，就會誤把每個問題都當成 React 問題。先能解釋 DOM 樹、事件冒泡、`async` / `await`、HTTP 狀態碼與環境變數的角色，再進入 Component。

TypeScript 是整條路線的護欄。先練熟基本型別、物件、陣列、函式、union、narrowing、generic、`type` 與 `interface`；接著再練 Props、事件、`useState<T>` 與 API response 型別。專案設定維持 `strict: true`，不以 `any` 略過不確定的資料。Props 優先用 `interface` 描述物件形狀，union 與 utility types 使用 `type`，但這是可讀性慣例，不是硬性語言限制。

**完成標準：** 能將一個未知 API 值先視為 `unknown`，驗證或縮窄後才使用；也能說明為何 immutable update 比直接修改 array 或 object 更適合 React state。

## 第一階段：建立 React 心智模型

從 `UI = f(state)` 開始，而不是從 Hook 清單開始。Component 是根據目前 Props 與 State 回傳 UI 的函式；React 依據資料變化重新計算畫面。先掌握 JSX、Component composition、Props、`children`、條件渲染、列表與穩定的 `key`，再做第一個互動元件。

這一階段要特別分清兩件事。Props 是由父層傳入的唯讀輸入；State 是 component 對時間的記憶。當兩個子元件需要同一份資料，就把 state 提升到它們共同的父層，而不是讓兩邊各自複製一份。

**練習：** 先完成 Tic-Tac-Toe 或待辦清單：可新增、切換、刪除與篩選。程式中不得直接修改 state，也不得用 array index 當會重排列表的 key。

**讀取順序：** `React Visualized — 一本書學 React` 第 1–5 章 → `DOM 節點觀念` → `Tic-Tac-Toe Example`。

## 第二階段：掌握 State、render 與事件

開始寫功能之前，要先理解 state 是每次 render 的快照，不是 setter 呼叫後立刻變動的變數。學習以事件處理器啟動使用者意圖，並在需要由前一狀態推導下一狀態時使用 functional update。這能避免 stale state，也讓程式更接近「輸入事件 → 狀態變更 → 新 UI」的單向資料流。

接著認識 render、commit 與 browser paint 的差別，並知道子 Component 通常會隨父層重新 render。此時不要急著加入 `memo`、`useMemo` 或 `useCallback`；先讓資料結構、Props 邊界與 state 位置正確，只有實測到昂貴計算或不必要 render 時才優化。

**練習：** 做可排序、可篩選的商品列表，拆成容器與展示元件。為每個 Props 與事件 handler 加上正確 TypeScript 型別。

## 第三階段：只在需要同步外部世界時使用 Effect

`useEffect` 最容易被濫用。它的職責不是「元件載入後要做的事」，而是讓 React 與外部系統同步，例如 API、timer、訂閱、瀏覽器 DOM 或第三方 widget。可在 render 直接算出的衍生資料，不應再存一份 state；由使用者點擊觸發的行為，通常應留在 event handler。

在這一階段依序學 `useEffect` 的 dependency、cleanup、取消過期請求、`useRef` 的 DOM 與非視覺值用途，以及 `useContext` 與 custom hook。每個 Effect 都應能回答：它同步哪一個外部系統？何時需要 cleanup？dependency 為何完整？這也是 `react-hooks/exhaustive-deps` 不應被關掉的原因。

**練習：** 製作可搜尋的使用者清單：query 改變時載入資料、顯示 loading/error/empty 狀態，並避免較慢的舊回應覆蓋新查詢結果。

**讀取順序：** `React-Hooks-用途筆記與TypeScript範例` 的規則、`useState`、`useRef`、`useEffect`、custom hook 與附錄 → `react-hooks-gotchas`。`useLayoutEffect`、`useImperativeHandle`、`useSyncExternalStore` 等留到遇到測量布局、封裝 imperative API 或外部 store 時再學。

## 第四階段：做出可用、可驗證的畫面

功能正確不代表介面可用。此時補齊 CSS layout、responsive design、focus 狀態與語意化表單，再用 Tailwind 將常見間距、Grid、Flexbox、breakpoint 與互動狀態快速落實。Tailwind 是樣式表達方式，不是設計系統本身；重複的色彩、間距與元件變體仍應收斂為 design tokens、`cn()` 與可重用 Component。

表單先由受控輸入與 validation 的需求出發。欄位一多、錯誤狀態與跨欄驗證一複雜，就採 React Hook Form 搭配 Zod；Zod 也適合放在 API 邊界，避免 TypeScript 型別只存在編譯期、實際 response 卻不可信的落差。

**練習：** 做一個 responsive 的「建立／編輯使用者」表單，具有即時錯誤訊息、送出中狀態、成功與失敗回饋。元件抽取要以重用與責任邊界為依據，不只因為檔案變長。

## 第五階段：建立一個真實 SPA 的骨架

這是由單一畫面跨入產品的分水嶺。先以 React Router 建立 layout、巢狀 route、動態參數、404 與導向，再以 Context 建構 AuthProvider 與 ProtectedRoute。登入狀態必須讓路由守衛、導覽列與 API client 使用同一個事實來源；不要把「是否登入」散落在每個 page。

資料層要區分 local state 與 server state。modal 開關、欄位輸入等短命資料留在 component；來自後端、需要 caching、loading、retry、invalidate 的資料交給 React Query。Axios 或 fetch client 集中設定 base URL、header、error mapping 與 timeout，Component 不直接建立 client。只有跨多個 feature 的 client state 真正變得複雜時，才引入 Zustand；Context 也不是所有 global state 的替代品。

與 ASP.NET Core API 整合時，先協議 request/response DTO、錯誤格式、CORS、token 或 cookie 策略，以及 dev/prod 的環境變數。前端路由保護只是在 UX 層隱藏畫面；後端仍必須自行驗證授權。

**練習：** 完成「登入後的帳號管理」小專案：登入、ProtectedRoute、使用者 CRUD、列表快取與 mutation 後更新、表單驗證、404 頁面，以及 `.env.development` / `.env.production`。

## 第六階段：讓專案可以長期演化

當功能超過幾個頁面，資料夾比單一檔案更重要。可將共用 UI 放在 `components/`、業務功能放在 `features/`、共用 Hook 放在 `hooks/`、API client 與 schema 放在 `lib/api/`、共享型別放在 `types/`，page 或 router 只負責組合。這樣能讓資料取得、商業規則與視覺呈現各自演化。

接著建立品質門檻：TypeScript strict mode、ESLint（尤其 Hooks rules）、Component / Hook / 資料層的測試、可存取性檢查，以及 production build。效能工作從測量開始：用 React DevTools 或瀏覽器工具確認瓶頸，再決定是否使用 `React.memo`、`useMemo`、`useCallback`、virtualization 或 code splitting。不要把 memoization 當作預設寫法。

部署前確認環境變數不含秘密、錯誤頁與 loading 狀態完整、API URL 與 CORS 符合環境、靜態資產路徑正確。這些檢查比再加入一個 state library 更常決定產品是否能穩定上線。

## 選修分支：依產品需求投資

完成前六階段後，再依你真正要做的產品選分支。需要繪圖、動畫或影像處理時，走 Canvas：從 `useRef`、HiDPI、`requestAnimationFrame`、pointer event 到 OffscreenCanvas / Worker；它是瀏覽器圖形程式設計，不是一般 CRUD React 的前置條件。需要大型共用套件與多個 app 時研究 Monorepo；在單一 app 還沒有清楚邊界前，Monorepo 只會增加工具成本。

想改善大型互動的體感時，再學 `useTransition`、`useDeferredValue` 與 React 19 Actions。若要採用 Next.js 或支援 Server Components，先理解 Client / Server Component 邊界、Suspense、Error Boundary 與 `use client`；這是另一種 runtime 與 rendering 架構，不能只當作「更進階的 Hook」。

## 建議的 10 週節奏

| 週次 | 焦點 | 產出 |
| --- | --- | --- |
| 1 | DOM、JavaScript 非同步、TypeScript 基礎 | typed utility 與小型 DOM 練習 |
| 2 | JSX、Component、Props、列表與事件 | Tic-Tac-Toe 或 Todo |
| 3 | State、lifting state、render | 可篩選／排序清單 |
| 4 | Effect、Ref、custom hook | 搜尋與取消舊請求 |
| 5 | Tailwind、responsive、表單 | 有驗證的表單頁 |
| 6 | React Router、layout、404 | 多頁 SPA 骨架 |
| 7 | AuthProvider、ProtectedRoute | 登入與受保護頁面 |
| 8 | API client、React Query、Zod | CRUD 與快取失效 |
| 9 | feature 架構、測試、a11y | 重構與測試補齊 |
| 10 | build、環境設定、部署檢查 | 可展示的完整專案 |

每週以可運作的垂直切片收尾，而非只讀文件。若一週沒有新增可被使用者操作的畫面、流程或品質保護，通常代表學習順序太偏向工具而不是產品。

## 來源限制與校正事項

現有素材對測試、accessibility、Error Boundary、Vite build、CI/CD 與部署的教學不足；完成第六階段前，應另補這些主題。素材中也混有不同版本的建議：React 18 的 `forwardRef` 慣例與 React 19 對 `ref` 的處理不同，Router 套件名稱也隨版本改變，因此實作時應先確認專案採用的 React 與 Router 版本。

此外，示範中的 localStorage Bearer token 只適合作為串接概念，不能取代 OAuth/OIDC、PKCE、refresh、XSS 與 CSRF 的安全設計。對使用者資料與權限的真正驗證必須留在後端。

## 何時算是具備 React 前端開發能力

你不需要背完所有 Hook。當你能從需求切出 Component 與 state ownership、正確區分 event 與 Effect、以型別與 runtime validation 保護 API 邊界、建立可導覽且可驗證的表單流程，並能定位 rendering / network / state 三類問題時，就已經能獨立處理一般的 React 前端功能。進階 Hook、Canvas、Server Components 與 Monorepo 應由產品需求拉動，而不是作為入門關卡。

## 連結

- [[dom]]
- [[react]]
- [[typescript]]
- [[web-frontend-moc]]
- [[dotnet-web-api]]
