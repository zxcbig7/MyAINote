# React 生態系資源

# 1. UI 元件庫

## 1.1 [Ant Design](https://ant.design/)

> 企業級 React UI 設計系統， Ant Design適合快速打造後台管理系統與 B 端產品。
> 

```bash
npm install antd
```

```tsx
import React from 'react';
import { Button, Space } from 'antd';

const App: React.FC = () => (
  <Space>
    <Button type="primary">主要按鈕</Button>
    <Button>預設按鈕</Button>
    <Button type="dashed">虛線按鈕</Button>
  </Space>
);

export default App;
```

<aside>
💡

**備註：** v5 以後採用 CSS-in-JS，不需額外引入 CSS 檔案；內建 TypeScript 型別定義，無需安裝

</aside>

## 1.2 [shadcn/ui](https://ui.shadcn.com/)

> 基於 Radix UI + Tailwind CSS 的可複製元件集合， MarkaicodeShadcn適合需要完全掌控元件原始碼的專案。
> 

```bash
# 初始化（專案需先配好 Tailwind CSS）
npx shadcn@latest init

# 新增個別元件
npx shadcn@latest add button
```

```tsx
import React from 'react';
import { Button } from '@/components/ui/button';

const App: React.FC = () => (
  <div className="flex gap-4">
    <Button variant="default">預設</Button>
    <Button variant="outline">外框</Button>
    <Button variant="destructive">危險</Button>
  </div>
);

export default App;
```

<aside>
💡

**備註：** shadcn/ui **不是傳統 npm 套件**，而是透過 CLI 將元件原始碼複製到你的專案中（ [shadcn/ui](https://ui.shadcn.com/docs)預設放在 `src/components/ui/`）。你擁有完整的程式碼控制權，可以自由修改。 [Shadcn](https://www.shadcn.io/ui/installation-guide)

</aside>

## 1.3 [MUI (Material UI)](https://mui.com/material-ui/)

> Google Material Design 的 React 實現，適合追求一致設計語言與豐富元件的大型應用。
> 

```bash
npm install @mui/material @emotion/react @emotion/styled
```

```tsx
import React from 'react';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';

const App: React.FC = () => (
  <Stack direction="row" spacing={2}>
    <Button variant="contained">Contained</Button>
    <Button variant="outlined">Outlined</Button>
    <Button variant="text">Text</Button>
  </Stack>
);

export default App;
```

<aside>
💡

**備註：** 必須安裝 @emotion/react 與 @emotion/styled 作為樣式引擎。若需要 Material Icons，另外安裝 @mui/icons-material。 MUImui

</aside>

## 1.4 [Mantine](https://mantine.dev/)

> 功能全面的現代 React 元件庫， mantine適合追求開發效率與美觀預設樣式的全端專案。
> 

```bash
npm install @mantine/core @mantine/hooks
```

```tsx
import React from 'react';
import { MantineProvider, Button, Group } from '@mantine/core';
import '@mantine/core/styles.css';

const App: React.FC = () => (
  <MantineProvider>
    <Group>
      <Button variant="filled">填滿</Button>
      <Button variant="light">淺色</Button>
      <Button variant="outline">外框</Button>
    </Group>
  </MantineProvider>
);

export default App;
```

<aside>
💡

**備註：** 必須在根元件引入 @mantine/core/styles.css 並用 <MantineProvider> 包裹應用。Mantine 另提供 @mantine/dates、@mantine/form、@mantine/notifications 等擴充套件。 

</aside>

# 2. 圖示庫

## 2.1 [react-icons](https://react-icons.github.io/react-icons/)

> 聚合 30+ 套圖示庫（Font Awesome、Material Design、Bootstrap 等）的一站式方案，適合需要混用多種風格圖示的專案。
> 

```bash
npm install react-icons
```

```tsx
import React from 'react';
import { FaReact, FaGithub } from 'react-icons/fa';
import { MdDashboard } from 'react-icons/md';
import { BsLightningChargeFill } from 'react-icons/bs';

const IconDemo: React.FC = () => (
  <div style={{ display: 'flex', gap: '16px', fontSize: '2rem' }}>
    <FaReact color="#61DAFB" />
    <FaGithub />
    <MdDashboard color="#4CAF50" />
    <BsLightningChargeFill color="gold" />
  </div>
);

export default IconDemo;
```

<aside>
💡

**備註：** 各圖示集有獨立子路徑（`react-icons/fa`、`react-icons/md` 等），支援 tree-shaking，只打包用到的圖示。 

</aside>

## 2.2 [Lucide React](https://lucide.dev/)

> Feather Icons 的社群分支，提供 1500+ 精緻線性圖示，適合追求一致視覺風格與設計品質的專案（ GitHubshadcn/ui 預設使用 Lucide）。
> 

```bash
npm install lucide-react
```

```tsx
import React from 'react';
import { Camera, Heart, Home, Settings, Search } from 'lucide-react';

const IconDemo: React.FC = () => (
  <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
    <Camera size={32} color="red" />
    <Heart size={32} fill="pink" stroke="red" />
    <Home size={32} color="#4CAF50" />
    <Settings size={32} strokeWidth={1.5} />
    <Search size={32} />
  </div>
);

export default IconDemo;
```

<aside>
💡

**備註：** 每個圖示支援 `size`（預設 24）、`color`、`strokeWidth`（預設 2）等 props，也接受所有標準 SVG 屬性。 

</aside>

# 3. 表單處理與驗證

## 3.1 [React Hook Form](https://react-hook-form.com/)

> 高效能表單管理，基於非受控元件策略最大限度減少重新渲染， Medium適合表單複雜度高、效能要求嚴格的場景。
> 

```bash
npm install react-hook-form
```

```tsx
import { useForm, SubmitHandler } from 'react-hook-form';

type FormData = {
  name: string;
  email: string;
  age: number;
};

function MyForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>();

  const onSubmit: SubmitHandler<FormData> = (data) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name', { required: '請輸入名稱' })} />
      {errors.name && <p>{errors.name.message}</p>}

      <input {...register('email', { required: '請輸入 Email' })} />
      {errors.email && <p>{errors.email.message}</p>}

      <input
        type="number"
        {...register('age', { valueAsNumber: true, min: 1 })}
      />
      {errors.age && <p>請輸入有效年齡</p>}

      <button type="submit">送出</button>
    </form>
  );
}

export default MyForm;
```

## 3.2 [Zod](https://zod.dev/)

> TypeScript-first 的 schema 驗證庫， npm可用 z.infer 自動推導型別， GitHub適合在前後端共用驗證邏輯與消除重複型別定義。
> 

```bash
npm install zod
```

```tsx
import { z } from 'zod';

// 定義 schema
const UserSchema = z.object({
  name: z.string().min(1, '名稱必填'),
  email: z.string().email('Email 格式不正確'),
  age: z.number().int().min(0).max(120),
});

// 從 schema 自動推導 TypeScript 型別
type User = z.infer<typeof UserSchema>;

// 解析資料（不合格會拋出錯誤）
const user = UserSchema.parse({
  name: 'Alice',
  email: 'alice@example.com',
  age: 30,
});

// 安全解析（不拋錯誤，回傳 result 物件）
const result = UserSchema.safeParse({ name: '', email: 'bad', age: -1 });
if (!result.success) {
  console.log(result.error.issues);
}
```

## 3.3 [**Resolvers](https://github.com/react-hook-form/resolvers) (**React Hook Form + Zod 整合)

> 最佳實踐組合：用 Zod 定義驗證 schema，再透過 zodResolver 橋接到 React Hook Form， freeCodeCamp達成「定義一次 schema，同時獲得型別推導 + 表單驗證」。
> 

```bash
npm install react-hook-form zod @hookform/resolvers
```

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// 1️⃣ 用 Zod 定義 schema
const schema = z.object({
  name: z.string().min(1, { message: '名稱必填' }),
  email: z.string().email({ message: 'Email 格式不正確' }),
  age: z
    .number({ invalid_type_error: '年齡必須為數字' })
    .min(18, '必須年滿 18 歲'),
});

// 2️⃣ 從 schema 推導型別（不用再手寫 interface）
type FormData = z.infer<typeof schema>;

function RegistrationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema), // 3️⃣ 用 zodResolver 橋接
    defaultValues: { name: '', email: '', age: undefined },
  });

  const onSubmit = (data: FormData) => {
    console.log('驗證通過：', data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} placeholder="名稱" />
      {errors.name && <p>{errors.name.message}</p>}

      <input {...register('email')} placeholder="Email" />
      {errors.email && <p>{errors.email.message}</p>}

      <input
        type="number"
        {...register('age', { valueAsNumber: true })}
        placeholder="年齡"
      />
      {errors.age && <p>{errors.age.message}</p>}

      <button type="submit">註冊</button>
    </form>
  );
}

export default RegistrationForm;
```

<aside>
💡

**關鍵整合點：** zodResolver(schema) 傳入 useForm 的 resolver 選項； Tecktolz.infer<typeof schema> 自動產生 TypeScript 型別，完全不需要手動維護重複的 interface。 Contentfulnpm

</aside>

# 4. 路由

## 4.1 [React Router](https://reactrouter.com/)

> React 生態系最主流的路由方案，適合所有需要**頁面導航**的 SPA 應用。
v7 起所有 import 統一來自 react-router，不再需要 react-router-dom。
> 

```bash
npm install react-router
```

**入口 main.tsx：**

```tsx
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
```

**App.tsx：**

```tsx
import { Routes, Route, Link, Outlet } from 'react-router';

function Layout() {
  return (
    <div>
      <nav>
        <Link to="/">首頁</Link> | <Link to="/about">關於</Link>
      </nav>
      <hr />
      <Outlet />
    </div>
  );
}

const Home = () => <h2>首頁</h2>;
const About = () => <h2>關於頁面</h2>;
const NotFound = () => <h2>404 - 頁面不存在</h2>;

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default App;
```

<aside>
💡

**備註：** React Router v7 也支援類似 Remix 的 Framework Mode（檔案式路由）和使用 createBrowserRouter + RouterProvider 的 Data Mode。上方範例為最基本的宣告式用法。

</aside>

# 5. 日期時間

## 5.1 [Day.js](https://day.js.org/)

> 僅 2kB 的輕量日期庫，API 與 Moment.js 相容，適合任何需要日期格式化、計算或比較的場景（Moment.js 的最佳替代品）
> 

```bash
npm install dayjs
```

```tsx
import React from 'react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const DateDemo: React.FC = () => {
  const now = dayjs();

  return (
    <div>
      {/* 格式化 */}
      <p>短日期：{now.format('YYYY-MM-DD')}</p>
      <p>完整格式：{now.format('YYYY/MM/DD HH:mm:ss')}</p>

      {/* 日期運算（immutable，回傳新物件） */}
      <p>7 天後：{now.add(7, 'day').format('YYYY-MM-DD')}</p>
      <p>上個月：{now.subtract(1, 'month').format('YYYY-MM-DD')}</p>

      {/* 相對時間（需 relativeTime 插件） */}
      <p>距今：{dayjs('2025-01-01').fromNow()}</p>

      {/* 日期比較 */}
      <p>
        差距：{dayjs('2026-12-31').diff(now, 'day')} 天
      </p>
    </div>
  );
};

export default DateDemo;
```

<aside>
💡

**備註：** Day.js 核心極輕量，進階功能透過插件擴充，常用插件包括 `relativeTime`、`utc`、`timezone`、`customParseFormat`、`isBetween`、`duration`。

</aside>

# 6. 表格

## 6.1 [TanStack Table](https://tanstack.com/table/latest)

> Headless 表格邏輯引擎，只提供排序、篩選、分頁等核心邏輯，UI 完全自訂， GitHubDEV Community適合需要高度客製化表格的資料密集型應用。
> 

```bash
npm install @tanstack/react-table
```

```tsx
import React, { useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table';

// 定義資料型別
type User = {
  name: string;
  email: string;
  role: string;
};

// 範例資料
const defaultData: User[] = [
  { name: 'Alice', email: 'alice@example.com', role: 'Admin' },
  { name: 'Bob', email: 'bob@example.com', role: 'Editor' },
  { name: 'Charlie', email: 'charlie@example.com', role: 'Viewer' },
];

// 用 columnHelper 定義型別安全的欄位
const columnHelper = createColumnHelper<User>();

const columns = [
  columnHelper.accessor('name', { header: '姓名' }),
  columnHelper.accessor('email', { header: 'Email' }),
  columnHelper.accessor('role', { header: '角色' }),
];

function UserTable() {
  const [data] = useState<User[]>(defaultData);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <table>
      <thead>
        {table.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <th key={header.id}>
                {flexRender(
                  header.column.columnDef.header,
                  header.getContext()
                )}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row) => (
          <tr key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default UserTable;
```

<aside>
💡

**備註：** TanStack Table 是 headless 設計，不提供任何內建樣式。 
TanStackMonsterlessons-academy可搭配排序（getSortedRowModel）、篩選（getFilteredRowModel）、分頁（getPaginationRowModel）等功能模組自由組合。

</aside>