---
type: entity
domain: tech
tags: [typescript, javascript, frontend, type-system]
sources:
  - raw/tech/web-dev/TypeScript.md
  - raw/tech/web-dev/React/React + TypeScript 開發手冊.md
created: 2026-05-03
updated: 2026-05-03
---

# TypeScript

TypeScript 是 JavaScript 的超集，加入靜態型別系統。負責**型別檢查與轉譯（compile to JS）**，執行時的 hoisting、TDZ 等行為仍是 JavaScript runtime 的規則。

## 基本型別

```typescript
const name: string = "Alice";
const age: number = 30;
const isActive: boolean = true;
const nothing: null = null;
const undef: undefined = undefined;

// 型別推論（TS 自動從初始值推斷）
const pi = 3.14;  // number

// Union 聯合型別
let id: string | number = "A-001";
id = 1001;

// unknown / any（盡量避免 any）
let data: unknown;
```

## Interface vs Type

```typescript
// Interface：描述物件結構，可被 extends（推薦用於物件）
interface User {
  id: number;
  name: string;
  email?: string;   // ? = 選填
}

// Type Alias：更彈性，可描述 Union、Intersection（推薦用於組合型別）
type Status = "active" | "inactive" | "pending";   // Union
type AdminUser = User & { role: string };           // Intersection
```

**實務建議：物件結構用 Interface，Union / 組合型別用 Type**

## 泛型 Generics

```typescript
// 讓函式適用多種型別，又保有型別安全
function identity<T>(value: T): T {
  return value;
}

// 泛型 Interface（API 回應常用模式）
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message: string;
}

type UserResponse = ApiResponse<User>;
type UserListResponse = ApiResponse<User[]>;
```

## Utility Types（常用內建工具型別）

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  password: string;
}

type UpdateUserDto = Partial<User>;          // 所有欄位變成可選
type UserProfile = Pick<User, "id" | "name">;  // 只取部分欄位
type PublicUser = Omit<User, "password">;    // 排除欄位
type StrictUser = Required<Partial<User>>;  // 所有欄位變必填
type ImmutableUser = Readonly<User>;         // 所有欄位唯讀
```

## 型別縮窄 Narrowing

```typescript
function printId(id: string | number) {
  if (typeof id === "string") {
    console.log(id.toUpperCase());  // TS 確認是 string
  } else {
    console.log(id.toFixed(2));    // TS 確認是 number
  }
}
```

## Spread / Rest

```typescript
// Spread：打散陣列或物件
const combined = [...arr1, ...arr2];
const updated = { ...user, name: "Bob" };  // 後面覆蓋前面

// Rest：收集剩餘參數
function sum(...numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}

// React Component 常用模式：Rest 收集 + Spread 傳遞
const Button = ({ label, variant = "primary", ...rest }: ButtonProps) => (
  <button className={`btn-${variant}`} {...rest}>{label}</button>
);
```

## 淺複製 vs 深複製

```typescript
// 淺複製：Spread 只複製第一層
const copy = { ...user };          // user.address 和 copy.address 指向同一物件

// 深複製方式
const deepCopy1 = { ...user, address: { ...user.address } };  // 手動展開
const deepCopy2 = JSON.parse(JSON.stringify(user));           // JSON 轉換（限制多）
const deepCopy3 = structuredClone(user);                      // 現代瀏覽器推薦
```

## 非同步

```typescript
// async/await
async function fetchUsers(): Promise<User[]> {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error("Request failed");
  return (await res.json()) as User[];
}

// Promise.all 並行
const [u1, u2] = await Promise.all([fetchUser(1), fetchUser(2)]);
```

## 錯誤處理

```typescript
try {
  divide(10, 0);
} catch (e) {
  if (e instanceof Error) {
    console.log(e.message);  // strict 模式 e 是 unknown，需收窄
  }
}
```

## 實用語法速查

```typescript
// Optional chaining
const city = user.address?.city;
const upper = input?.toUpperCase();

// Nullish coalescing（只在 null/undefined 時取右側，不同於 || 的 falsy）
const value = input ?? "預設值";

// 型別斷言
const el = document.querySelector("#name") as HTMLInputElement | null;

// Nullish coalescing vs OR
const url1 = env.VITE_API ?? "";   // 只有 null/undefined 才用 ""
const url2 = env.VITE_API || "";   // 0、""、false 也會用 ""
```

## 常見錯誤

```typescript
// 不要用 any
const handleData = (data: any) => data.name; // 失去型別保護

// 處理 null/undefined
const name = user?.name ?? "訪客";

// useEffect 依賴陣列要完整
useEffect(() => { fetchUser(userId); }, [userId]);  // 不要漏掉依賴

// 不直接修改 state
setUsers(prev => [...prev, newUser]);  // 建立新陣列
```

## 連結

- [[react]] — TypeScript 在 React 中的應用
- [[dotnet-web-api]] — 後端 API 定義對應前端型別
