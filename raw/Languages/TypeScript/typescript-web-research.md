---
tags: [typescript, programming]
---

> 關聯：[[typescript]]

# TypeScript 由淺至深語法教學 — Web Research

來源 URL：
- https://www.typescriptlang.org/docs/handbook/intro.html
- https://www.typescriptlang.org/docs/handbook/2/generics.html
- https://www.typescriptlang.org/docs/handbook/utility-types.html
- https://www.typescriptlang.org/docs/handbook/2/conditional-types.html
- https://www.typescriptlang.org/docs/handbook/2/types-from-types.html
- https://www.freecodecamp.org/news/learn-typescript-beginners-guide/

---

## 1. 基礎：原始型別與型別推論

TypeScript 是 JavaScript 的靜態型別超集，在 compile 時檢查型別錯誤。

```typescript
// 明確標注型別
let id: number = 5;
let name: string = "Danny";
let isActive: boolean = true;
let nothing: null = null;
let undef: undefined = undefined;

// 型別推論（TS 自動推斷，省略標注）
let pi = 3.14;        // 推斷為 number
let greeting = "Hi"; // 推斷為 string

// any 與 unknown
let data: any;        // 跳過型別檢查（盡量避免）
let safe: unknown;    // 必須先 narrowing 才能使用
```

---

## 2. Union 聯合型別 / Literal 字面量型別

```typescript
// Union：接受多種型別
let id: string | number;
id = "A-001";
id = 1001;

// Literal：限定在特定值
let direction: "left" | "right" | "up" | "down";
direction = "left"; // OK
direction = "back"; // Error

// Tuple：固定長度、固定順序
let point: [number, number] = [10, 20];
let record: [string, number, boolean] = ["Alice", 30, true];
```

---

## 3. 陣列型別

```typescript
let ids: number[] = [1, 2, 3];
let names: string[] = ["Alice", "Bob"];

// 泛型語法（效果相同）
let scores: Array<number> = [95, 87, 100];

// 混合型別陣列
let mixed: (string | number)[] = ["Alice", 1, "Bob", 2];
```

---

## 4. Interface：物件型別契約

```typescript
interface User {
  id: number;
  name: string;
  email?: string;   // ? 代表選填
}

// Interface 可以 extends（繼承）
interface AdminUser extends User {
  role: string;
  permissions: string[];
}

// Interface 可以定義函式簽名
interface Speech {
  sayHi(name: string): string;
  sayBye: (name: string) => string;
}

// 實作
let user: User = { id: 1, name: "Alice" };
```

---

## 5. Type Alias：彈性型別別名

```typescript
// 基本別名
type ID = string | number;
type Status = "active" | "inactive" | "pending";

// 物件型別（與 Interface 類似，但不能 extends，只能 &）
type Point = {
  x: number;
  y: number;
};

// Intersection（交集型別）
type AdminUser = User & { role: string };

// 實務建議：
// - 物件結構（可能被繼承/擴充）→ Interface
// - Union / Intersection / 複雜組合 → Type
```

---

## 6. 函式型別

```typescript
// 參數與回傳值標注
function add(a: number, b: number): number {
  return a + b;
}

// Arrow function
const multiply = (a: number, b: number): number => a * b;

// Optional 參數（? 必須放在必填後面）
const greet = (name: string, greeting?: string): string => {
  return `${greeting ?? "Hello"}, ${name}!`;
};

// Default 參數
const createUser = (name: string, role: string = "user") => ({
  name,
  role,
});

// Rest 參數
function sum(...numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}

// Void 回傳型別
const logMessage = (msg: string): void => {
  console.log(msg);
};

// 函式型別宣告
type MathFn = (a: number, b: number) => number;
let divide: MathFn = (a, b) => a / b;
```

---

## 7. Class 類別

```typescript
class Person {
  // 存取修飾子
  readonly id: number;      // 唯讀
  private _age: number;     // 只在 class 內使用
  protected email: string;  // class 與子 class 可用
  public name: string;      // 任何地方（預設）

  constructor(id: number, name: string, age: number, email: string) {
    this.id = id;
    this.name = name;
    this._age = age;
    this.email = email;
  }

  // Getter / Setter
  get age(): number {
    return this._age;
  }

  set age(value: number) {
    if (value < 0) throw new Error("Age cannot be negative");
    this._age = value;
  }

  greet(): string {
    return `Hi, I'm ${this.name}`;
  }
}

// 建構子簡寫（直接在參數加修飾子）
class Programmer extends Person {
  constructor(
    id: number,
    name: string,
    age: number,
    email: string,
    public languages: string[]
  ) {
    super(id, name, age, email);
  }
}

// 實作 Interface
interface Formatter {
  format(): string;
}

class User implements Formatter {
  constructor(public username: string) {}

  format(): string {
    return this.username.toLowerCase();
  }
}
```

---

## 8. Enum 列舉

```typescript
// Numeric Enum（預設從 0 開始）
enum Direction {
  Up,     // 0
  Down,   // 1
  Left,   // 2
  Right,  // 3
}

// 自訂起始值
enum StatusCode {
  OK = 200,
  NotFound = 404,
  ServerError = 500,
}

// String Enum（推薦，更易讀懂）
enum Role {
  Admin = "ADMIN",
  User = "USER",
  Guest = "GUEST",
}

// 使用
let userRole: Role = Role.Admin;
console.log(Role.NotFound); // 404（numeric enum 可反查）
```

---

## 9. 型別縮窄 Narrowing

```typescript
// typeof guard
function printValue(val: string | number) {
  if (typeof val === "string") {
    console.log(val.toUpperCase()); // 確定是 string
  } else {
    console.log(val.toFixed(2));    // 確定是 number
  }
}

// instanceof guard
function getArea(shape: Circle | Square) {
  if (shape instanceof Circle) {
    return Math.PI * shape.radius ** 2;
  }
  return shape.side ** 2;
}

// Discriminated Union（識別聯合）
interface Circle { kind: "circle"; radius: number; }
interface Square { kind: "square"; side: number; }

function getShapeArea(shape: Circle | Square) {
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

## 10. 泛型 Generics

### 基本用法

```typescript
// 泛型函式：保留型別資訊
function identity<T>(value: T): T {
  return value;
}

let str = identity<string>("hello");  // 明確指定
let num = identity(42);              // 型別推斷

// 多個型別參數
function pair<K, V>(key: K, value: V): [K, V] {
  return [key, value];
}
```

### Generic Constraint（泛型約束）

```typescript
// 限制 T 必須有 length 屬性
interface Lengthwise {
  length: number;
}

function logLength<T extends Lengthwise>(arg: T): T {
  console.log(arg.length);
  return arg;
}

logLength("hello");        // OK: string 有 length
logLength([1, 2, 3]);      // OK: array 有 length
logLength(42);             // Error: number 無 length

// keyof 約束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 30 };
getProperty(user, "name");  // OK
getProperty(user, "email"); // Error: "email" 不在 user 的 keys
```

### Generic Interface & Class

```typescript
// Generic Interface
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message: string;
}

type UserResponse = ApiResponse<User>;
type UserListResponse = ApiResponse<User[]>;

// Generic Class
class Stack<T> {
  private items: T[] = [];

  push(item: T): void {
    this.items.push(item);
  }

  pop(): T | undefined {
    return this.items.pop();
  }

  peek(): T | undefined {
    return this.items[this.items.length - 1];
  }
}

const numStack = new Stack<number>();
numStack.push(1);
numStack.push(2);
```

### Generic Parameter Defaults

```typescript
// 提供預設型別參數
interface Container<T = string> {
  value: T;
}

const c1: Container = { value: "hello" };    // T = string（預設）
const c2: Container<number> = { value: 42 }; // T = number（指定）
```

---

## 11. Utility Types 內建工具型別

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  password: string;
  createdAt: Date;
}

// Partial<T>：所有欄位變 optional
type UpdateUserDto = Partial<User>;

// Required<T>：所有欄位變必填（反 Partial）
type StrictUser = Required<Partial<User>>;

// Readonly<T>：所有欄位唯讀
type ImmutableUser = Readonly<User>;

// Pick<T, K>：只取指定欄位
type UserProfile = Pick<User, "id" | "name">;

// Omit<T, K>：排除指定欄位
type PublicUser = Omit<User, "password">;

// Record<K, V>：以 K 為 key、V 為 value 的物件
type RolePermissions = Record<Role, string[]>;

// Exclude<T, U>：從 Union 排除特定型別
type StringOrNumber = string | number | boolean;
type OnlyPrimitives = Exclude<StringOrNumber, boolean>; // string | number

// Extract<T, U>：只留下符合的型別
type OnlyBoolean = Extract<StringOrNumber, boolean>; // boolean

// NonNullable<T>：排除 null 和 undefined
type SafeString = NonNullable<string | null | undefined>; // string

// ReturnType<T>：取得函式回傳型別
type FetchResult = ReturnType<typeof fetchUser>; // Promise<User>

// Parameters<T>：取得函式參數型別（tuple）
type FetchParams = Parameters<typeof fetchUser>; // [id: number]

// Awaited<T>：遞迴解包 Promise（TS 4.5+）
type ResolvedUser = Awaited<Promise<Promise<User>>>; // User
```

---

## 12. 進階型別操作

### Conditional Types 條件型別

```typescript
// 語法：T extends U ? TrueType : FalseType
type IsString<T> = T extends string ? true : false;

type A = IsString<string>;  // true
type B = IsString<number>;  // false

// 實際應用：依型別決定 label 型別
type IdLabel = { id: number };
type NameLabel = { name: string };

type LabelFor<T extends number | string> =
  T extends number ? IdLabel : NameLabel;

// infer：在 conditional type 中推斷型別
type UnpackPromise<T> = T extends Promise<infer U> ? U : T;

type Value = UnpackPromise<Promise<string>>;  // string
type Other = UnpackPromise<number>;           // number

// 提取函式回傳型別（ReturnType 的原始實作）
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
```

### Mapped Types 映射型別

```typescript
// 基本語法：遍歷現有型別的所有 key
type Optional<T> = {
  [K in keyof T]?: T[K];
};

// 添加 readonly
type Immutable<T> = {
  readonly [K in keyof T]: T[K];
};

// 移除 readonly 和 optional（使用 - 修飾符）
type Mutable<T> = {
  -readonly [K in keyof T]-?: T[K];
};

// 型別轉換
type Stringify<T> = {
  [K in keyof T]: string;
};
```

### Template Literal Types 模板字面量型別

```typescript
type EventName = "click" | "focus" | "blur";

// 組合產生新型別
type EventHandler = `on${Capitalize<EventName>}`;
// "onClick" | "onFocus" | "onBlur"

// 與 keyof 組合
type Getter<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface User {
  name: string;
  age: number;
}

type UserGetters = Getter<User>;
// { getName: () => string; getAge: () => number }
```

### keyof / typeof 運算子

```typescript
// keyof：取得所有 key 的 Union
type UserKeys = keyof User; // "id" | "name" | "email" | ...

// typeof：取得變數/值的型別
const config = {
  host: "localhost",
  port: 3000,
  debug: true,
};

type Config = typeof config;
// { host: string; port: number; debug: boolean }

// 組合使用
function getConfigValue<K extends keyof typeof config>(key: K) {
  return config[key];
}
```

### Indexed Access Types 索引存取型別

```typescript
type UserName = User["name"];      // string
type UserId = User["id"];          // number

// 用陣列索引取元素型別
type Colors = ["red", "green", "blue"];
type FirstColor = Colors[0];       // "red"
type AnyColor = Colors[number];    // "red" | "green" | "blue"
```

---

## 13. 實用語法速查

```typescript
// Optional Chaining
const city = user?.address?.city;

// Nullish Coalescing（只在 null/undefined 時取右側）
const name = user.name ?? "訪客";

// Non-null Assertion（斷言不為 null）
const el = document.getElementById("app")!;

// 型別斷言
const input = document.querySelector("input") as HTMLInputElement;

// Satisfies（確保滿足型別但保留推斷，TS 4.9+）
const config = {
  host: "localhost",
  port: 3000,
} satisfies Partial<ServerConfig>;
```

---

## 14. tsconfig.json 重要選項

```json
{
  "compilerOptions": {
    "target": "ES2020",           // 轉譯目標
    "module": "ESNext",
    "strict": true,               // 啟用所有嚴格檢查
    "noImplicitAny": true,        // 禁止隱性 any
    "strictNullChecks": true,     // null/undefined 須明確處理
    "exactOptionalPropertyTypes": true, // 嚴格 optional 處理
    "noUncheckedIndexedAccess": true,   // 陣列存取包含 undefined
    "rootDir": "./src",
    "outDir": "./dist",
    "sourceMap": true,
    "declaration": true           // 產生 .d.ts 型別宣告檔
  }
}
```

---

## 圖片

（本次研究未下載圖片，官方文件為文字為主）
