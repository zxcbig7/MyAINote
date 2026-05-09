---
type: entity
domain: tech
tags: [typescript, javascript, frontend, type-system, generics, utility-types]
sources:
  - raw/tech/web-dev/TypeScript.md
  - raw/tech/web-dev/React/React + TypeScript 開發手冊.md
  - raw/Languages/languages/Typescript/typescript-web-research.md
created: 2026-05-03
updated: 2026-05-09
---

# TypeScript

TypeScript 是 JavaScript 的靜態型別超集，加入編譯時型別檢查。TypeScript 檔案 `.ts` 需 compile 成 `.js` 才能執行；執行時的行為（hoisting、TDZ、prototype chain）仍是 JavaScript runtime 規則。

---

## 基礎：原始型別與型別推論

```typescript
let id: number = 5;
let name: string = "Alice";
let isActive: boolean = true;
let nothing: null = null;
let undef: undefined = undefined;

// 型別推論（TS 自動從初始值推斷，可省略標注）
const pi = 3.14;  // number

// any vs unknown
let data: any;     // 跳過型別檢查（避免使用）
let safe: unknown; // 需先 narrowing 才能操作
```

---

## Union 聯合型別 / Literal 字面量型別

```typescript
// Union：接受多種型別
let id: string | number;
id = "A-001";
id = 1001;

// Literal：限定在特定值
let direction: "left" | "right" | "up" | "down";
direction = "back"; // Error

// Tuple：固定長度、固定型別順序
let point: [number, number] = [10, 20];
let record: [string, number, boolean] = ["Alice", 30, true];
```

---

## 陣列型別

```typescript
let ids: number[] = [1, 2, 3];
let names: Array<string> = ["Alice", "Bob"]; // 泛型語法，效果相同

let mixed: (string | number)[] = ["Alice", 1];
```

---

## Interface vs Type

```typescript
// Interface：描述物件結構，可 extends（推薦用於物件）
interface User {
  id: number;
  name: string;
  email?: string;  // ? = 選填
}

interface AdminUser extends User {
  role: string;
}

// Type Alias：更彈性，可描述 Union / Intersection（推薦用於組合型別）
type Status = "active" | "inactive" | "pending";
type AdminUser = User & { role: string };  // Intersection

// 實務建議：物件結構 → Interface；Union / 組合 → Type
```

---

## 函式型別

```typescript
// 基本標注
function add(a: number, b: number): number {
  return a + b;
}

// Arrow function
const multiply = (a: number, b: number): number => a * b;

// Optional / Default / Rest 參數
const greet = (name: string, greeting = "Hello"): string =>
  `${greeting}, ${name}!`;

function sum(...numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}

// void 回傳（不回傳值）
const log = (msg: string): void => console.log(msg);

// 函式型別別名
type MathFn = (a: number, b: number) => number;
```

---

## Class 類別

```typescript
class Person {
  readonly id: number;      // 唯讀
  private _age: number;     // 只在 class 內部
  protected email: string;  // class 與子 class
  public name: string;      // 任何地方（預設）

  constructor(id: number, name: string, age: number, email: string) {
    this.id = id;
    this.name = name;
    this._age = age;
    this.email = email;
  }

  get age(): number { return this._age; }
  set age(value: number) {
    if (value < 0) throw new Error("Age cannot be negative");
    this._age = value;
  }
}

// 建構子簡寫（參數直接加修飾子）
class Programmer extends Person {
  constructor(
    id: number, name: string, age: number, email: string,
    public languages: string[]
  ) {
    super(id, name, age, email);
  }
}

// 實作 Interface
interface Formatter { format(): string; }

class User implements Formatter {
  constructor(public username: string) {}
  format() { return this.username.toLowerCase(); }
}
```

---

## Enum 列舉

```typescript
// Numeric Enum
enum Direction { Up, Down, Left, Right }  // 0, 1, 2, 3

// String Enum（推薦，易讀）
enum Role {
  Admin = "ADMIN",
  User = "USER",
  Guest = "GUEST",
}

let r: Role = Role.Admin;
```

---

## 型別縮窄 Narrowing

```typescript
// typeof guard
function printId(id: string | number) {
  if (typeof id === "string") {
    console.log(id.toUpperCase());
  } else {
    console.log(id.toFixed(2));
  }
}

// Discriminated Union（識別聯合）
interface Circle { kind: "circle"; radius: number; }
interface Square { kind: "square"; side: number; }

function getArea(shape: Circle | Square) {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "square": return shape.side ** 2;
  }
}

// Type Predicate（自訂型別守衛）
function isString(val: unknown): val is string {
  return typeof val === "string";
}
```

---

## 泛型 Generics

```typescript
// 基本：保留型別資訊
function identity<T>(value: T): T { return value; }

// 多型別參數
function pair<K, V>(key: K, value: V): [K, V] { return [key, value]; }

// Generic Constraint（約束 T 必須有 length）
interface Lengthwise { length: number; }

function logLength<T extends Lengthwise>(arg: T): T {
  console.log(arg.length);
  return arg;
}

// keyof 約束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Generic Interface（API 常用）
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message: string;
}
type UserResponse = ApiResponse<User>;

// Generic Class
class Stack<T> {
  private items: T[] = [];
  push(item: T): void { this.items.push(item); }
  pop(): T | undefined { return this.items.pop(); }
}

// 預設型別參數（TS 2.3+）
interface Container<T = string> { value: T; }
```

---

## Utility Types 內建工具型別

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  password: string;
}

type UpdateUserDto   = Partial<User>;                 // 所有欄位 optional
type StrictUser      = Required<Partial<User>>;        // 所有欄位必填
type ImmutableUser   = Readonly<User>;                 // 所有欄位 readonly
type UserProfile     = Pick<User, "id" | "name">;      // 只取部分欄位
type PublicUser      = Omit<User, "password">;         // 排除欄位

// Record<K, V>：以 K 為 key、V 為 value
type RoleMap = Record<"admin" | "user" | "guest", string[]>;

// Exclude / Extract（操作 Union）
type T1 = Exclude<string | number | boolean, boolean>; // string | number
type T2 = Extract<string | number | boolean, boolean>; // boolean

// NonNullable：排除 null/undefined
type SafeStr = NonNullable<string | null | undefined>;  // string

// ReturnType / Parameters
type FetchResult = ReturnType<typeof fetchUser>;   // Promise<User>
type FetchParams  = Parameters<typeof fetchUser>;  // [id: number]

// Awaited（遞迴解包 Promise，TS 4.5+）
type Resolved = Awaited<Promise<Promise<User>>>;   // User
```

---

## 進階型別操作

### Conditional Types 條件型別

```typescript
// 語法：T extends U ? TrueType : FalseType
type IsArray<T> = T extends any[] ? true : false;
type A = IsArray<string[]>; // true
type B = IsArray<number>;   // false

// infer：在條件型別中推斷
type UnpackPromise<T> = T extends Promise<infer U> ? U : T;
type Value = UnpackPromise<Promise<string>>; // string

// 自製 ReturnType
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// Distributive（Union 分配）
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]

// 防止分配（用 [] 包住）
type NonDist<T> = [T] extends [any] ? T[] : never;
```

### Mapped Types 映射型別

```typescript
// 遍歷所有 key
type Optional<T> = { [K in keyof T]?: T[K] };
type Immutable<T> = { readonly [K in keyof T]: T[K] };

// - 修飾符（移除 readonly / ?）
type Mutable<T> = { -readonly [K in keyof T]-?: T[K] };

// 搭配 as 重命名 key（TS 4.1+）
type Getter<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
// { getName: () => string; getAge: () => number; }
```

### Template Literal Types 模板字面量型別

```typescript
type EventName = "click" | "focus" | "blur";

// 組合產生新型別
type Handler = `on${Capitalize<EventName>}`;
// "onClick" | "onFocus" | "onBlur"
```

### keyof / typeof / Indexed Access

```typescript
// keyof：取得所有 key 的 Union
type UserKeys = keyof User; // "id" | "name" | "email" | "password"

// typeof：取得值的型別
const config = { host: "localhost", port: 3000 };
type Config = typeof config; // { host: string; port: number }

// 組合
function get<K extends keyof typeof config>(key: K) {
  return config[key];
}

// Indexed Access：用 key 存取型別
type NameType = User["name"];            // string
type AnyColor = ["red","green","blue"][number]; // "red" | "green" | "blue"
```

---

## 實用語法速查

```typescript
// Optional Chaining
const city = user?.address?.city;

// Nullish Coalescing（只在 null/undefined 時取右側）
const name = user.name ?? "訪客";

// Non-null Assertion（斷言非 null，小心使用）
const el = document.getElementById("app")!;

// 型別斷言
const input = document.querySelector("input") as HTMLInputElement;

// Satisfies（保留推斷型別同時確保符合型別，TS 4.9+）
const palette = {
  red: [255, 0, 0],
  green: "#00ff00",
} satisfies Record<string, string | number[]>;
```

---

## Spread / Rest

```typescript
// Spread：打散陣列或物件
const merged = [...arr1, ...arr2];
const updated = { ...user, name: "Bob" };  // 後覆前

// Rest：收集剩餘參數
function sum(...numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}
```

---

## 淺複製 vs 深複製

```typescript
// 淺複製：Spread 只複製第一層
const copy = { ...user }; // user.address 與 copy.address 指向同一物件

// 深複製
const deep1 = { ...user, address: { ...user.address } }; // 手動展開
const deep2 = JSON.parse(JSON.stringify(user));           // JSON（限制多）
const deep3 = structuredClone(user);                      // 現代瀏覽器推薦
```

---

## 非同步

```typescript
async function fetchUsers(): Promise<User[]> {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error("Request failed");
  return (await res.json()) as User[];
}

// Promise.all 並行
const [u1, u2] = await Promise.all([fetchUser(1), fetchUser(2)]);
```

---

## tsconfig.json 重要選項

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": true,
    "rootDir": "./src",
    "outDir": "./dist",
    "sourceMap": true,
    "declaration": true
  }
}
```

| 選項 | 說明 |
| ---- | ---- |
| `strict` | 啟用所有嚴格檢查 |
| `noImplicitAny` | 禁止隱性 any |
| `strictNullChecks` | null/undefined 須明確處理 |
| `noUncheckedIndexedAccess` | 陣列存取包含 `undefined` |
| `exactOptionalPropertyTypes` | `?` 屬性不允許主動設為 `undefined` |

---

## 常見錯誤

```typescript
// 不要用 any
const handleData = (data: any) => data.name; // 失去型別保護

// 處理 null/undefined
const name = user?.name ?? "訪客";

// 不直接修改 state（React）
setUsers(prev => [...prev, newUser]);

// useEffect 依賴陣列要完整
useEffect(() => { fetchUser(userId); }, [userId]);
```

---

## 連結

- [[react]] — TypeScript 在 React 中的應用（FC、useState、useRef 型別）
- [[dotnet-web-api]] — 後端 API 定義對應前端型別
- [[csharp]] — C# 型別系統與 TypeScript 的異同
