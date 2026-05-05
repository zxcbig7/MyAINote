# type vs. interface

# `type` vs `interface` 在 TypeScript 中的判斷

---

## 先看核心差異

### `interface`，描述「物件的形狀」

```tsx
interface User {
  id: number;
  name: string;
}
```

### `type`，描述「任何型別」

```tsx
type User = {
  id: number;
  name: string;
}

// type 還可以做 interface 做不到的事
type ID = string | number;           // 聯合型別
type Point = [number, number];       // Tuple
type Callback = () => void;          // 函式
```

---

## 最關鍵的差異點

### 差異 1：`interface` 可以被繼承與合併，`type` 不行

```tsx
// interface 可以 extends
interface Animal {
  name: string;
}

interface Dog extends Animal {
  breed: string;
}

// interface 同名可以自動合併 (Declaration Merging)
interface User {
  id: number;
}
interface User {
  name: string;
}
// 結果 User = { id: number; name: string }  自動合併`
```

```tsx
// type 同名會直接報錯
type User = { id: number; }
type User = { name: string; }  // 錯誤，不能重複宣告
```

### 差異 2：`type` 可以做聯合型別，`interface` 不行

```tsx
// 只有 type 能做這些
type Status = 'active' | 'inactive' | 'pending';
type ID = string | number;
type StringOrArray = string | string[];
```

### 差異 3：`type` 可以用 `&` 交叉合併

```tsx
type A = { id: number };
type B = { name: string };
type C = A & B;  // { id: number; name: string }
```

---

## 判斷原則，什麼時候用哪個

### 用 `interface` 的情況

**描述物件、class、API 回傳結構**

```tsx
// API 回傳的資料結構
interface UserResponse {
  id: number;
  name: string;
  email: string;
}

// React Props
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

// Class 實作
interface Repository<T> {
  findById(id: number): Promise<T>;
  save(entity: T): Promise<void>;
}

class UserRepository implements Repository<User> {
  // ...
}
```

### 用 `type` 的情況

**聯合型別、工具型別、非物件型別**

```tsx
// 聯合型別
type ButtonVariant = 'primary' | 'secondary' | 'danger';
type ID = string | number;

// 函式型別
type FetchUser = (id: number) => Promise<User>;

// 條件型別
type NonNullable<T> = T extends null | undefined ? never : T;

// 搭配 React Query 的資料狀態
type ApiState<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };
```

---

## 在 React + TypeScript 實務中的應用

```tsx
// Props 用 interface (物件形狀，可能被繼承)
interface CardProps {
  title: string;
  children: React.ReactNode;
}

interface LinkCardProps extends CardProps {
  href: string;
}

// 狀態、聯合、常數用 type
type Theme = 'light' | 'dark';
type Size = 'sm' | 'md' | 'lg';

// API DTO 用 interface
interface CreateUserRequest {
  name: string;
  email: string;
}

interface CreateUserResponse {
  id: number;
  name: string;
  createdAt: string;
}
```

---

## 一張判斷表

| 情境 | 用哪個 |
| --- | --- |
| 物件結構、Props、API DTO | `interface` |
| 聯合型別 `A | B` | `type` |
| 函式型別 | `type` |
| 需要 `extends` 繼承 | `interface` |
| 需要 `implements` | `interface` |
| 字串常數集合 | `type` |
| 工具型別、條件型別 | `type` |

---

## 最簡單的記憶方法

> 描述「一個東西長什麼樣子」，用 `interface`。
描述「這個東西是什麼種類」或「多種可能」，用 `type`。
> 

實務上兩者很多時候可以互換，團隊統一規範比糾結選擇更重要。但如果沒有規範，以上判斷表是最安全的做法。