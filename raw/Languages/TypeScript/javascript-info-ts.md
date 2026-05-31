---
tags: [typescript, javascript, tutorial]
source: https://zh.javascript.info/
---

> 關聯：[[typescript]]

# JavaScript.info — TypeScript 版筆記

基於 [現代 JavaScript 教程](https://zh.javascript.info/) 全站內容，所有程式碼範例改寫為 TypeScript。

---

## 變數宣告

```ts
// let：可重新賦值
let message: string = "Hello";
message = "World";

// const：不可重新賦值（物件內容仍可改）
const PI: number = 3.14159;

// 型別推論（type inference）：從初始值自動推導
const email = "example@email.com"; // TypeScript 推論為 string

// 常數命名慣例：UPPER_SNAKE_CASE
const COLOR_RED = "#F00";
const COLOR_GREEN = "#0F0";

// Union 型別
let id: string | number = "A-001";
id = 1001;
```

---

## 資料型別

### 原始型別（Primitive Types）

```ts
// number（整數與浮點數共用）
let n: number = 123;
n = 12.345;
const inf = Infinity;
const nan = NaN;

// bigint：超大整數，加 n 後綴
const bigInt: bigint = 1234567890123456789012345678901234567890n;

// string：三種引號
const str1: string = "Hello";
const str2: string = 'World';
const name = "John";
const phrase: string = `Hello, ${name}!`; // 樣板字串

// boolean
let isChecked: boolean = true;
let isGreater: boolean = 4 > 1;

// null 與 undefined
let age: number | null = null;
let notAssigned: undefined = undefined;

// symbol：唯一識別符
const id: symbol = Symbol("id");
```

### typeof 運算子

```ts
console.log(typeof undefined);  // "undefined"
console.log(typeof 0);          // "number"
console.log(typeof 10n);        // "bigint"
console.log(typeof true);       // "boolean"
console.log(typeof "foo");      // "string"
console.log(typeof Symbol("id")); // "symbol"
console.log(typeof null);       // "object"（歷史遺留 bug）
console.log(typeof alert);      // "function"
```

---

## 型別轉換

```ts
// 字串轉換
let value: boolean | string = true;
const strValue: string = String(value); // "true"

// 數字轉換
const str: string = "123";
const num: number = Number(str); // 123

// 數字轉換規則
Number("   123   "); // 123（去除空白）
Number("123z");      // NaN
Number(true);        // 1
Number(false);       // 0
Number(null);        // 0
Number(undefined);   // NaN

// 布林轉換：falsy 值為 false，其餘為 true
Boolean(1);          // true
Boolean(0);          // false
Boolean("hello");    // true
Boolean("");         // false
Boolean("0");        // true（非空字串！）
```

---

## 運算子

```ts
// 取餘
console.log(5 % 2);   // 1

// 求幂
console.log(2 ** 3);  // 8

// 字串連接（+）
console.log("1" + 2); // "12"
console.log(2 + 2 + "1"); // "41"（從左到右）

// 一元加號轉型別
console.log(+true);  // 1
console.log(+"");    // 0

// 自增（前置 vs 後置）
let counter: number = 1;
const newVal = ++counter; // 2（先加再回傳）
const oldVal = counter++; // 2（先回傳再加）

// 原地修改
let n: number = 2;
n += 5; // 7
n *= 2; // 14
```

---

## 值的比較

```ts
// 嚴格相等（不做型別轉換）— TypeScript 推薦使用
console.log(0 === false);          // false
console.log(null === undefined);   // false

// 寬鬆相等（會做型別轉換，TS 中應避免）
console.log("2" == 1);    // false（轉成 number 比較）
console.log(null == undefined);    // true（特殊規則）
console.log(null === undefined);   // false

// null 的特殊行為
console.log(null > 0);   // false
console.log(null >= 0);  // true（!）
console.log(null == 0);  // false
```

---

## 邏輯運算子

```ts
// OR（||）：回傳第一個「真值」
const firstName: string = "";
const lastName: string = "";
const nickName: string = "SuperCoder";
const displayName = firstName || lastName || nickName || "Anonymous";
// "SuperCoder"

// AND（&&）：回傳第一個「假值」，否則回傳最後一個值
console.log(1 && 0);     // 0
console.log(1 && 2 && 3); // 3

// NOT（!）
console.log(!true);           // false
console.log(!!"non-empty");   // true（雙重否定轉 boolean）

// 空值合併（??）：只處理 null/undefined，不處理 falsy
const height: number | null = 0;
console.log(height || 100);  // 100（因 0 是 falsy）
console.log(height ?? 100);  // 0（0 不是 null/undefined）

// 用法：提供預設值
let user: string | null = null;
console.log(user ?? "匿名"); // "匿名"
```

---

## 控制流程

### if / else / 三元運算子

```ts
const age: number = 20;

if (age >= 18) {
  console.log("成年");
} else if (age >= 12) {
  console.log("青少年");
} else {
  console.log("兒童");
}

// 三元運算子
const status: string = age >= 18 ? "成年" : "未成年";
```

### switch

```ts
const day: number = 3;

switch (day) {
  case 1:
  case 2:
  case 3:
  case 4:
  case 5:
    console.log("工作日");
    break;
  case 6:
  case 7:
    console.log("週末");
    break;
  default:
    console.log("無效");
}
```

### 迴圈

```ts
// while
let i: number = 0;
while (i < 3) {
  console.log(i);
  i++;
}

// do...while（至少執行一次）
do {
  console.log(i);
  i++;
} while (i < 3);

// for
for (let j: number = 0; j < 3; j++) {
  console.log(j);
}

// break / continue
outer: for (let x = 0; x < 3; x++) {
  for (let y = 0; y < 3; y++) {
    if (x + y === 3) break outer; // 跳出外層迴圈
  }
}
```

---

## 函式

### 函式宣告 vs 函式表達式

```ts
// 函式宣告（declaration）：可以在宣告前呼叫（hoisting）
function sum(a: number, b: number): number {
  return a + b;
}

// 函式表達式（expression）：執行到才建立
const greet = function(name: string): string {
  return `Hello, ${name}!`;
};

// 箭頭函式
const double = (n: number): number => n * 2;
const add = (a: number, b: number): number => a + b;

// 多行箭頭函式
const getFullName = (first: string, last: string): string => {
  const full = `${first} ${last}`;
  return full;
};
```

### 參數

```ts
// 預設參數
function showMessage(from: string, text: string = "no text given"): void {
  console.log(`${from}: ${text}`);
}
showMessage("Ann"); // "Ann: no text given"

// 可選參數（在 TS 中用 ? 表示）
function log(message: string, userId?: number): void {
  console.log(message, userId ?? "anonymous");
}

// Rest 參數（TypeScript 明確指定型別）
function sumAll(...args: number[]): number {
  return args.reduce((total, n) => total + n, 0);
}
sumAll(1, 2, 3); // 6

// 混合 rest
function showName(firstName: string, lastName: string, ...titles: string[]): void {
  console.log(`${firstName} ${lastName}`);
  console.log(titles); // string[]
}
```

### Spread 語法

```ts
const arr: number[] = [3, 5, 1];
console.log(Math.max(...arr)); // 5

const arr1: number[] = [1, -2, 3];
const arr2: number[] = [8, 3, -8];
console.log(Math.max(...arr1, ...arr2)); // 8

// 合併陣列
const merged: number[] = [0, ...arr1, 2, ...arr2];

// 複製陣列（淺拷貝）
const arrCopy: number[] = [...arr];

// 複製物件
interface Config { a: number; b: number }
const obj: Config = { a: 1, b: 2 };
const objCopy: Config = { ...obj };
```

---

## 物件基礎

### 建立與存取

```ts
interface User {
  name: string;
  age: number;
  "likes birds"?: boolean; // 多詞屬性
}

const user: User = {
  name: "John",
  age: 30,
};

// 點記法
console.log(user.name);

// 方括號記法（動態鍵名）
const key = "age";
console.log(user[key as keyof User]); // 30

// 計算屬性
const fruit = "apple";
const bag: Record<string, number> = { [fruit]: 5 };

// 屬性值簡寫（shorthand）
function makeUser(name: string, age: number): User {
  return { name, age };
}

// in 運算子
console.log("age" in user); // true

// for...in
for (const key in user) {
  console.log(key, user[key as keyof User]);
}

// 刪除屬性
delete (user as any)["likes birds"];
```

### 物件方法與 this

```ts
interface Counter {
  count: number;
  increment(): Counter;
  decrement(): Counter;
  show(): void;
}

const counter: Counter = {
  count: 0,
  increment() {
    this.count++;
    return this; // 鏈式呼叫
  },
  decrement() {
    this.count--;
    return this;
  },
  show() {
    console.log(this.count);
  },
};

counter.increment().increment().decrement().show(); // 1

// 箭頭函式不綁定 this（繼承外層）
class Timer {
  private seconds: number = 0;

  start(): void {
    setInterval(() => {
      this.seconds++; // this 正確指向 Timer 實例
    }, 1000);
  }
}
```

### 物件引用與複製

```ts
// 物件是傳引用（reference）
const a = { x: 1 };
const b = a;   // b 與 a 指向同一物件
b.x = 2;
console.log(a.x); // 2

// 淺拷貝
const clone1 = Object.assign({}, a);
const clone2 = { ...a };

// 深拷貝（簡單物件）
const deep = JSON.parse(JSON.stringify(a));
```

### 可選鏈（Optional Chaining）

```ts
interface Address { street?: string }
interface UserWithAddress { name: string; address?: Address }

const userObj: UserWithAddress = {};

// 安全存取
console.log(userObj?.address?.street); // undefined（不報錯）

// 可選方法呼叫
interface Admin { admin?(): void }
const admin: Admin = {};
admin.admin?.(); // 若 admin 方法不存在則靜默

// 可選方括號
const key2 = "name";
const val = (userObj as any)?.[key2]; // undefined
```

---

## Symbol

```ts
// Symbol 是唯一識別符
const id1: symbol = Symbol("id");
const id2: symbol = Symbol("id");
console.log(id1 === id2); // false

// 作為物件鍵（隱藏屬性，不出現在 for...in）
const SYM_ID = Symbol("id");
const obj2 = {
  [SYM_ID]: 123,
  name: "John",
};

for (const key in obj2) {
  console.log(key); // 只有 "name"
}

// 全域 Symbol（相同 key 回傳相同實例）
const globalId = Symbol.for("globalId");
const globalId2 = Symbol.for("globalId");
console.log(globalId === globalId2); // true
console.log(Symbol.keyFor(globalId)); // "globalId"
```

---

## 資料型別詳解

### Number

```ts
// 科學記數法
const billion: number = 1e9;
const micro: number = 1e-6;

// 不同進位
const hex: number = 0xff;    // 255
const bin: number = 0b11111111; // 255
const oct: number = 0o377;   // 255

// toString(base)
const num: number = 255;
console.log(num.toString(16)); // "ff"
console.log(num.toString(2));  // "11111111"

// 捨入
Math.floor(3.7);  // 3
Math.ceil(3.1);   // 4
Math.round(3.5);  // 4
Math.trunc(-1.7); // -1（移除小數部分）

// toFixed（回傳 string）
const pi: number = 3.14159;
console.log(pi.toFixed(2)); // "3.14"
console.log(+pi.toFixed(2)); // 3.14（轉 number）

// 精度問題
console.log(0.1 + 0.2 === 0.3); // false
console.log(+(0.1 + 0.2).toFixed(2) === 0.3); // true

// 特殊值
console.log(isNaN(NaN));      // true
console.log(isFinite(Infinity)); // false
console.log(Object.is(NaN, NaN)); // true
console.log(Object.is(0, -0));    // false

// parseInt / parseFloat（解析含非數字的字串）
parseInt("100px");     // 100
parseFloat("12.5em");  // 12.5
parseInt("ff", 16);    // 255

// Math 常用方法
Math.random();         // 0 到 1
Math.max(3, 5, -10);  // 5
Math.pow(2, 10);      // 1024

// 隨機整數工具
const randomInt = (min: number, max: number): number =>
  Math.floor(min + Math.random() * (max + 1 - min));
```

### String

```ts
const str: string = "stringify";

// 長度
console.log(`My\n`.length); // 3

// 存取字元
console.log(str[0]);          // "s"
console.log(str.charAt(0));   // "s"
console.log(str[str.length - 1]); // "y"

// 字串不可變：只能建立新字串
const hi: string = "Hi";
const modified = "h" + hi[1]; // "hi"

// 大小寫
"Interface".toUpperCase(); // "INTERFACE"
"Interface".toLowerCase(); // "interface"

// 搜尋
const text = "Widget with id";
text.indexOf("Widget");      // 0（找不到回傳 -1）
text.includes("Widget");     // true
text.startsWith("Widget");   // true
text.endsWith("id");         // true

// 擷取子字串（推薦用 slice）
str.slice(0, 5);    // "strin"（含頭不含尾）
str.slice(2);       // "ringify"
str.slice(-4, -1);  // "gif"（負值從尾端算）
str.substring(2, 6); // "ring"（不支援負值）

// 比較
"a" > "Z";  // true（小寫 code 較大）
"Österreich".localeCompare("Zealand"); // -1（本地語言規則）

// 常用工具
"  hello  ".trim();   // "hello"
"abc".repeat(3);      // "abcabcabc"

// 實用範例
const ucFirst = (s: string): string =>
  s ? s[0].toUpperCase() + s.slice(1) : s;

const truncate = (s: string, maxLen: number): string =>
  s.length > maxLen ? s.slice(0, maxLen - 1) + "…" : s;
```

### Array

```ts
// 建立
const arr: number[] = [1, 2, 3];
const mixed: (string | number)[] = ["hello", 1, true as any];

// 增刪
arr.push(4);           // 尾端加入，回傳新長度
arr.pop();             // 尾端移除並回傳
arr.unshift(0);        // 頭端加入
arr.shift();           // 頭端移除並回傳

// splice（原地修改）
arr.splice(1, 1);           // 從 index 1 刪除 1 個
arr.splice(1, 0, 10, 20);   // 插入而不刪除
arr.splice(0, 2, "a", "b"); // 替換

// slice（回傳新陣列）
arr.slice(1, 3); // index 1 到 2
arr.slice(-2);   // 最後兩個

// 搜尋
const users = [{ id: 1, name: "John" }, { id: 2, name: "Jane" }];
users.indexOf(users[0]);          // 0
users.includes(users[0]);         // true
users.find(u => u.id === 1);      // { id: 1, name: "John" }
users.findIndex(u => u.id === 2); // 1
users.filter(u => u.id > 0);      // 全部

// 轉換
const nums: number[] = [1, 2, 3];
nums.map(n => n * 2);              // [2, 4, 6]
nums.filter(n => n > 1);          // [2, 3]
nums.reduce((sum, n) => sum + n, 0); // 6
nums.sort((a, b) => a - b);       // 升冪排序

// forEach（副作用，無回傳值）
nums.forEach((n, i) => console.log(i, n));

// some / every
nums.some(n => n > 2);   // true
nums.every(n => n > 0);  // true

// flat / flatMap
const nested: number[][] = [[1, 2], [3, 4]];
nested.flat();            // [1, 2, 3, 4]

// 字串轉陣列
"a,b,c".split(",");       // ["a", "b", "c"]
["a", "b", "c"].join("-"); // "a-b-c"

// concat
const a2 = [1, 2];
const b2 = [3, 4];
a2.concat(b2); // [1, 2, 3, 4]
```

### Map 與 Set

```ts
// Map：任何型別都能當 key
const map = new Map<string | number | object, string>();
map.set("1", "str1");
map.set(1, "num1");
map.set(true as any, "bool1");
console.log(map.get(1));  // "num1"
console.log(map.size);    // 3

// 以物件為 key
interface Person { name: string }
const john: Person = { name: "John" };
const visits = new Map<Person, number>();
visits.set(john, 123);
console.log(visits.get(john)); // 123

// 迭代
const recipeMap = new Map([["cucumber", 500], ["tomatoes", 350]]);
for (const [veg, amount] of recipeMap) {
  console.log(veg, amount);
}
recipeMap.forEach((amount, veg) => console.log(veg, amount));

// Object <-> Map 互轉
const obj3 = { name: "John", age: 30 };
const mapFromObj = new Map(Object.entries(obj3));
const objFromMap = Object.fromEntries(mapFromObj);

// Set：不重複的集合
const set = new Set<string>(["a", "b", "c"]);
set.add("a"); // 重複，不變
console.log(set.size); // 3

// 去重
const unique = <T>(arr: T[]): T[] => Array.from(new Set(arr));

// WeakMap：key 必須是物件，key 被 GC 時自動移除
const cache = new WeakMap<object, string>();
let objRef = {};
cache.set(objRef, "cached");
objRef = null as any; // cache 中的條目自動清除

// WeakSet：物件集合，自動清除
const visited = new WeakSet<object>();
```

### Object.keys / values / entries

```ts
interface Prices { banana: number; orange: number; meat: number }
const prices: Prices = { banana: 1, orange: 2, meat: 4 };

Object.keys(prices);    // ["banana", "orange", "meat"]
Object.values(prices);  // [1, 2, 4]
Object.entries(prices); // [["banana", 1], ["orange", 2], ["meat", 4]]

// 翻倍價格
const doublePrices = Object.fromEntries(
  Object.entries(prices).map(([k, v]) => [k, v * 2])
);

// 薪資加總
const sumSalaries = (salaries: Record<string, number>): number =>
  Object.values(salaries).reduce((a, b) => a + b, 0);

// 屬性數量
const count = (obj: object): number => Object.keys(obj).length;
```

### 解構賦值

```ts
// 陣列解構
const [firstName, surname] = "John Smith".split(" ");
const [first, , title] = ["Julius", "Caesar", "Consul"];
const [x, y, ...rest] = [1, 2, 3, 4, 5]; // rest = [3, 4, 5]
const [a = "Guest", b = "Anonymous"] = ["Julius"]; // 預設值

// 變數交換
let p = "Pete";
let q = "John";
[p, q] = [q, p];

// 物件解構
interface Options {
  title: string;
  width?: number;
  height?: number;
  items?: string[];
}

const options: Options = { title: "Menu", width: 100, height: 200 };

const { title, width = 50, height = 50 } = options; // 重命名 + 預設值
const { width: w, height: h } = options; // 重命名

// Rest 屬性
const { title: t, ...rest2 } = options;

// 函式參數解構
function showMenu({
  title = "Untitled",
  width = 200,
  height = 100,
  items = [],
}: Options = {}): void {
  console.log(title, width, height, items);
}

// 巢狀解構
interface Config2 {
  size: { width: number; height: number };
  items: string[];
}
const { size: { width: sw, height: sh }, items: [item1, item2] } = 
  { size: { width: 100, height: 200 }, items: ["a", "b"] } as Config2;
```

### JSON

```ts
interface Student {
  name: string;
  age: number;
  isAdmin: boolean;
  courses: string[];
  spouse: null;
}

const student: Student = {
  name: "John",
  age: 30,
  isAdmin: false,
  courses: ["html", "css", "js"],
  spouse: null,
};

// 序列化
const json: string = JSON.stringify(student);

// 格式化輸出
const pretty: string = JSON.stringify(student, null, 2);

// replacer 函式（過濾循環引用）
const meetup = { title: "Conference", participants: [{ name: "John" }] };
const filtered = JSON.stringify(meetup, (key, value) =>
  key === "occupiedBy" ? undefined : value
);

// 自訂 toJSON
interface Room { number: number; toJSON(): number }
const room: Room = {
  number: 23,
  toJSON() { return this.number; },
};

// 反序列化
const str2 = '{"title":"Conference","date":"2017-11-30T12:00:00.000Z"}';
const parsed = JSON.parse(str2, (key, value) =>
  key === "date" ? new Date(value) : value
);
```

---

## 函式進階

### 閉包（Closure）

```ts
// 每個函式呼叫建立獨立的詞彙環境（Lexical Environment）
function makeCounter(): () => number {
  let count = 0;
  return () => count++; // 捕獲外層 count
}

const counter1 = makeCounter();
const counter2 = makeCounter();
console.log(counter1()); // 0
console.log(counter1()); // 1
console.log(counter2()); // 0（獨立的 count）

// 閉包的實際應用
function makeMultiplier(factor: number): (n: number) => number {
  return (n: number) => n * factor;
}
const double2 = makeMultiplier(2);
const triple = makeMultiplier(3);
```

### 遞迴

```ts
// 遞迴版本
function pow(x: number, n: number): number {
  return n === 1 ? x : x * pow(x, n - 1);
}

// 遞迴遍歷部門薪資
type Department = Employee[] | Record<string, Department>;
interface Employee { salary: number }

function sumSalariesRec(department: Department): number {
  if (Array.isArray(department)) {
    return department.reduce((prev, emp) => prev + emp.salary, 0);
  }
  return Object.values(department).reduce(
    (sum, sub) => sum + sumSalariesRec(sub), 0
  );
}

// 斐波那契（迭代版，效能佳）
function fib(n: number): number {
  let a = 1, b = 1;
  for (let i = 3; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
```

### 裝飾器 / call / apply

```ts
// 快取裝飾器
function cachingDecorator<T extends unknown[], R>(
  func: (...args: T) => R
): (...args: T) => R {
  const cache = new Map<string, R>();
  return function (...args: T): R {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key)!;
    const result = func(...args);
    cache.set(key, result);
    return result;
  };
}

// 間諜裝飾器
function spy<T extends unknown[], R>(
  func: (...args: T) => R
): ((...args: T) => R) & { calls: T[] } {
  const wrapper = function (...args: T): R {
    wrapper.calls.push(args);
    return func(...args);
  } as ((...args: T) => R) & { calls: T[] };
  wrapper.calls = [];
  return wrapper;
}

// 延遲裝飾器
function delay<T extends unknown[]>(
  f: (...args: T) => void,
  ms: number
): (...args: T) => void {
  return function (...args: T): void {
    setTimeout(() => f(...args), ms);
  };
}

// 防抖（debounce）
function debounce<T extends unknown[]>(
  func: (...args: T) => void,
  ms: number
): (...args: T) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return function (...args: T): void {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), ms);
  };
}

// 節流（throttle）
function throttle<T extends unknown[]>(
  func: (...args: T) => void,
  ms: number
): (...args: T) => void {
  let isThrottled = false;
  let savedArgs: T | null = null;

  function wrapper(...args: T): void {
    if (isThrottled) {
      savedArgs = args;
      return;
    }
    isThrottled = true;
    func(...args);
    setTimeout(() => {
      isThrottled = false;
      if (savedArgs) {
        wrapper(...savedArgs);
        savedArgs = null;
      }
    }, ms);
  }
  return wrapper;
}
```

### bind 與 Partial Application

```ts
// bind：硬綁定 this
interface User2 { firstName: string }
function sayHi(this: User2): void {
  console.log(`Hello, ${this.firstName}!`);
}
const user2: User2 = { firstName: "John" };
const boundSayHi = sayHi.bind(user2);
setTimeout(boundSayHi, 1000);

// Partial application
function mul(a: number, b: number): number { return a * b; }
const double3 = mul.bind(null, 2); // a 固定為 2
console.log(double3(3)); // 6

// 自訂 partial（不綁定 this）
function partial<T extends unknown[], R>(
  func: (...args: T) => R,
  ...argsBound: Partial<T>
): (...args: unknown[]) => R {
  return function (...args: unknown[]): R {
    return func(...([...argsBound, ...args] as T));
  };
}
```

### 柯里化（Currying）

```ts
function curry<T extends unknown[], R>(
  func: (...args: T) => R
): (...args: unknown[]) => unknown {
  return function curried(...args: unknown[]): unknown {
    if (args.length >= func.length) {
      return func(...(args as T));
    }
    return (...args2: unknown[]) => curried(...args, ...args2);
  };
}

// 應用：日誌函式
function log(date: Date, importance: string, message: string): void {
  console.log(`[${date.getHours()}:${date.getMinutes()}] [${importance}] ${message}`);
}
const curriedLog = curry(log);
const logNow = curriedLog(new Date()) as (i: string) => (m: string) => void;
const debugNow = logNow("DEBUG");
debugNow("message"); // [HH:mm] DEBUG message
```

### 可迭代物件（Iterable）

```ts
// 自訂可迭代物件
interface Range {
  from: number;
  to: number;
  [Symbol.iterator](): Iterator<number>;
}

const range: Range = {
  from: 1,
  to: 5,
  [Symbol.iterator]() {
    let current = this.from;
    const last = this.to;
    return {
      next(): IteratorResult<number> {
        return current <= last
          ? { done: false, value: current++ }
          : { done: true, value: undefined as never };
      },
    };
  },
};

for (const num of range) {
  console.log(num); // 1, 2, 3, 4, 5
}

// Array.from
const arr2 = Array.from(range); // [1, 2, 3, 4, 5]
const squares = Array.from(range, n => n ** 2); // [1, 4, 9, 16, 25]
```

---

## 物件屬性配置

### 屬性描述符

```ts
// 查詢描述符
const descriptor = Object.getOwnPropertyDescriptor(Math, "PI");
// { value: 3.14…, writable: false, enumerable: false, configurable: false }

// 設定只讀
const user3 = { name: "John" };
Object.defineProperty(user3, "name", { writable: false });

// 批次定義
Object.defineProperties(user3, {
  name: { value: "John", writable: false },
  // surname: { value: "Smith", writable: false },
});

// 深度複製（含所有描述符）
const clone = Object.defineProperties(
  {},
  Object.getOwnPropertyDescriptors(user3)
);

// 凍結物件
Object.freeze(user3);       // 不可修改
Object.seal(user3);         // 不可新增/刪除
Object.preventExtensions(user3); // 不可新增
```

### Getter / Setter

```ts
class User3 {
  private _name: string = "";

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    if (value.length < 4) {
      console.log("Name is too short");
      return;
    }
    this._name = value;
  }

  constructor(name: string) {
    this.name = name; // 透過 setter
  }
}

// 計算屬性（相容性用途）
class UserWithAge {
  name: string;
  birthday: Date;

  get age(): number {
    return new Date().getFullYear() - this.birthday.getFullYear();
  }

  constructor(name: string, birthday: Date) {
    this.name = name;
    this.birthday = birthday;
  }
}
```

---

## 原型與繼承

```ts
// TypeScript 中推薦用 class，直接操作 prototype 較少見
// 下方展示等效的原型概念

// 原型鏈示意
const animal = {
  eats: true,
  walk() { console.log("Animal walk"); },
};
const rabbit = Object.create(animal);
rabbit.jumps = true;
console.log(rabbit.eats); // true（從 animal 繼承）
rabbit.walk();             // "Animal walk"

// Object.create 是 TypeScript 中操作原型最安全的方式
// 實際開發中用 class extends 替代

// hasOwnProperty（過濾繼承屬性）
for (const key in rabbit) {
  if (Object.prototype.hasOwnProperty.call(rabbit, key)) {
    console.log(`自有: ${key}`);
  }
}

// 原生原型的擴充（不建議）
// 若必須，用 declare module 合併宣告
declare global {
  interface Array<T> {
    last(): T | undefined;
  }
}
Array.prototype.last = function () {
  return this[this.length - 1];
};
```

---

## 類別（Class）

### 基本語法

```ts
class User4 {
  name: string;

  constructor(name: string) {
    this.name = name;
  }

  sayHi(): void {
    console.log(this.name);
  }
}

const u = new User4("John");
u.sayHi();

// 類別字段（Class Fields）
class Button {
  value: string;
  // 箭頭函式作為 class field：this 永遠指向實例
  click = (): void => {
    console.log(this.value);
  };

  constructor(value: string) {
    this.value = value;
  }
}
setTimeout(new Button("hello").click, 1000); // 正常輸出
```

### 繼承

```ts
class Animal {
  speed: number = 0;
  name: string;

  constructor(name: string) {
    this.name = name;
  }

  run(speed: number): void {
    this.speed = speed;
    console.log(`${this.name} runs at ${this.speed}`);
  }

  stop(): void {
    this.speed = 0;
    console.log(`${this.name} stands still`);
  }
}

class Rabbit extends Animal {
  earLength: number;

  constructor(name: string, earLength: number) {
    super(name); // 必須在使用 this 之前呼叫
    this.earLength = earLength;
  }

  hide(): void {
    console.log(`${this.name} hides!`);
  }

  // 覆寫（override）
  stop(): void {
    super.stop();
    this.hide();
  }
}

const rabbit = new Rabbit("White Rabbit", 10);
rabbit.run(5);
rabbit.stop();
```

### 靜態屬性與方法

```ts
class Article {
  title: string;
  date: Date;
  static publisher: string = "Anthropic";

  constructor(title: string, date: Date) {
    this.title = title;
    this.date = date;
  }

  static compare(a: Article, b: Article): number {
    return a.date.getTime() - b.date.getTime();
  }

  static createToday(): Article {
    return new Article("Today's digest", new Date());
  }
}

const articles: Article[] = [
  new Article("HTML", new Date(2024, 0, 1)),
  new Article("CSS", new Date(2024, 1, 1)),
];
articles.sort(Article.compare);
console.log(Article.publisher); // "Anthropic"

// 靜態方法與繼承
class TechnicalArticle extends Article {}
console.log(TechnicalArticle.publisher); // "Anthropic"（繼承靜態）
```

### 私有與保護屬性

```ts
class CoffeeMachine {
  // 保護（慣例，無語言強制）
  protected _waterAmount: number = 0;
  private readonly _power: number;

  // TypeScript 私有（編譯期檢查）
  private _status: string = "idle";

  // JavaScript 私有（#，執行期隔離）
  #waterLimit: number = 200;

  constructor(power: number) {
    this._power = power;
  }

  get power(): number { return this._power; }

  get waterAmount(): number { return this._waterAmount; }
  set waterAmount(value: number) {
    this._waterAmount = Math.max(0, value);
  }

  #fixWaterAmount(value: number): number {
    return Math.min(Math.max(0, value), this.#waterLimit);
  }

  setWaterAmount(value: number): void {
    this._waterAmount = this.#fixWaterAmount(value);
  }
}

const machine = new CoffeeMachine(100);
machine.setWaterAmount(300); // 被限制在 200
// machine._power = 200;     // TS 錯誤：readonly
// machine.#waterLimit;      // 語法錯誤
```

### instanceof 與型別檢查

```ts
class Animal2 {}
class Rabbit2 extends Animal2 {}

const r = new Rabbit2();
console.log(r instanceof Rabbit2); // true
console.log(r instanceof Animal2); // true（繼承鏈）

const arr: number[] = [1, 2, 3];
console.log(arr instanceof Array);  // true
console.log(arr instanceof Object); // true

// Symbol.toStringTag
class User5 {
  static [Symbol.toStringTag] = "User";
}
console.log(Object.prototype.toString.call(new User5())); // "[object User]"
```

### Mixin 模式

```ts
type Constructor<T = {}> = new (...args: unknown[]) => T;

function Serializable<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    serialize(): string {
      return JSON.stringify(this);
    }
  };
}

function Validatable<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    validate(): boolean {
      return true;
    }
  };
}

class User6 {
  name: string;
  constructor(name: string) { this.name = name; }
}

const SerializableUser = Serializable(Validatable(User6));
const u2 = new SerializableUser("John");
console.log(u2.serialize()); // {"name":"John"}
```

---

## 錯誤處理

### try / catch / finally

```ts
// 基本結構
try {
  const user = JSON.parse('{ bad json }');
} catch (err) {
  if (err instanceof SyntaxError) {
    console.log("JSON 語法錯誤:", err.message);
  } else {
    throw err; // 再次拋出未預期錯誤
  }
} finally {
  console.log("清理工作，一定執行");
}

// 自訂 throw
function readUser(json: string): { name: string; age: number } {
  const user = JSON.parse(json) as { name?: string; age?: number };
  if (!user.name) throw new SyntaxError("缺少 name 欄位");
  if (!user.age) throw new SyntaxError("缺少 age 欄位");
  return user as { name: string; age: number };
}

// instanceof 判斷錯誤型別
try {
  readUser('{ "age": 25 }');
} catch (err) {
  if (err instanceof SyntaxError) {
    console.log("無效資料:", err.message);
  }
}
```

### 自訂錯誤類別

```ts
// 基礎自訂錯誤（自動設 name）
class AppError extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

class ValidationError extends AppError {}

class PropertyRequiredError extends ValidationError {
  property: string;
  constructor(property: string) {
    super(`No property: ${property}`);
    this.property = property;
  }
}

// 包裝異常（Wrapping Exceptions）
class ReadError extends AppError {
  cause: Error;
  constructor(message: string, cause: Error) {
    super(message);
    this.cause = cause;
  }
}

function readUser2(json: string): void {
  try {
    JSON.parse(json);
  } catch (err) {
    if (err instanceof SyntaxError) {
      throw new ReadError("Syntax Error", err as Error);
    }
    throw err;
  }
}

try {
  readUser2("{bad json}");
} catch (e) {
  if (e instanceof ReadError) {
    console.log(e.message);           // "Syntax Error"
    console.log("Original:", e.cause); // SyntaxError
  }
}
```

---

## Promise 與非同步

### Promise 基礎

```ts
// Promise 狀態：pending → fulfilled / rejected
const promise = new Promise<string>((resolve, reject) => {
  setTimeout(() => resolve("done!"), 1000);
});

promise
  .then(result => console.log(result))  // "done!"
  .catch(err => console.error(err))
  .finally(() => console.log("清理"));

// 工廠函式：回傳 Promise
function delay2(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function loadScript(src: string): Promise<HTMLScriptElement> {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.onload = () => resolve(script);
    script.onerror = () => reject(new Error(`Script load error: ${src}`));
    document.head.append(script);
  });
}
```

### Promise 鏈

```ts
new Promise<number>((resolve) => {
  setTimeout(() => resolve(1), 1000);
})
  .then(result => {
    console.log(result); // 1
    return result * 2;
  })
  .then(result => {
    console.log(result); // 2
    return new Promise<number>(resolve => setTimeout(() => resolve(result * 2), 1000));
  })
  .then(result => console.log(result)); // 4

// 實際應用：fetch 鏈
async function fetchGithubUser(url: string): Promise<void> {
  const response = await fetch(url);
  const user = await response.json() as { name: string; avatar_url: string };
  console.log(user.name);
}
```

### Promise API

```ts
// Promise.all：全部成功才 resolve，任一失敗立即 reject
const urls = ["url1", "url2", "url3"];
const results = await Promise.all(urls.map(url => fetch(url)));

// Promise.allSettled：等全部結束，不論成功失敗
const settled = await Promise.allSettled(urls.map(url => fetch(url)));
settled.forEach(result => {
  if (result.status === "fulfilled") {
    console.log(result.value.status);
  } else {
    console.log(result.reason);
  }
});

// Promise.race：取最快的結果（成功或失敗）
const fastest = await Promise.race([
  delay2(1000).then(() => "first"),
  delay2(2000).then(() => "second"),
]);

// Promise.any：取第一個成功的，全部失敗才 reject（AggregateError）
const first = await Promise.any([
  Promise.reject(new Error("fail1")),
  delay2(1000).then(() => "success"),
]);

// Promise.resolve / reject
const cached = Promise.resolve("cached value");
```

### async / await

```ts
async function fetchData(url: string): Promise<string> {
  const response = await fetch(url);
  const data = await response.json() as string;
  return data;
}

// 錯誤處理
async function safeLoad(url: string): Promise<string | null> {
  try {
    const response = await fetch(url);
    return await response.text();
  } catch (err) {
    console.error("載入失敗:", err);
    return null;
  }
}

// 平行執行（比循序快）
async function loadAll(urls: string[]): Promise<string[]> {
  const results = await Promise.all(urls.map(url => fetch(url).then(r => r.text())));
  return results;
}

// 類別中的 async 方法
class ApiClient {
  async getData(): Promise<number> {
    return await Promise.resolve(1);
  }
}

new ApiClient().getData().then(console.log);
```

---

## Generator

```ts
// Generator 函式用 function*
function* generateSequence(start: number, end: number): Generator<number> {
  for (let i = start; i <= end; i++) {
    yield i;
  }
}

const gen = generateSequence(1, 5);
console.log(gen.next()); // { value: 1, done: false }
console.log(gen.next()); // { value: 2, done: false }

for (const value of generateSequence(1, 3)) {
  console.log(value); // 1, 2, 3
}

// 展開 Generator
const arr3 = [...generateSequence(1, 5)]; // [1, 2, 3, 4, 5]

// yield* 組合 Generator
function* generatePasswordCodes(): Generator<number> {
  yield* generateSequence(48, 57);  // 0-9
  yield* generateSequence(65, 90);  // A-Z
  yield* generateSequence(97, 122); // a-z
}

// 雙向通訊
function* calculator(): Generator<string, void, number> {
  const x: number = yield "輸入第一個數字";
  const y: number = yield "輸入第二個數字";
  yield `結果：${x + y}`;
}

const calc = calculator();
calc.next();      // { value: "輸入第一個數字", done: false }
calc.next(3);     // { value: "輸入第二個數字", done: false }
calc.next(5);     // { value: "結果：8", done: false }

// 無限 Generator
function* pseudoRandom(seed: number): Generator<number, never> {
  let value = seed;
  while (true) {
    value = (value * 16807) % 2147483647;
    yield value;
  }
}
```

---

## 模組（Module）

```ts
// === say.ts ===
export const greeting: string = "Hello";

export function sayHi(user: string): void {
  console.log(`Hello, ${user}!`);
}

export function sayBye(user: string): void {
  console.log(`Bye, ${user}!`);
}

// 預設匯出（每個檔案只能一個）
export default class UserService {
  getUser(id: number): string { return `User ${id}`; }
}

// === main.ts ===
import UserService from "./user";           // 預設匯入
import { sayHi, sayBye } from "./say";     // 具名匯入
import { sayHi as hi } from "./say";       // 重命名匯入
import * as say from "./say";              // 整個模組

// 重新匯出
export { sayHi, sayBye } from "./say";
export { default as UserService } from "./user";

// 動態匯入
async function loadModule(): Promise<void> {
  const { sayHi: h } = await import("./say");
  h("John");
}
```

---

## Proxy 與 Reflect

```ts
// get 捕捉器：預設值
const numbers: number[] = [0, 1, 2];
const proxy = new Proxy(numbers, {
  get(target, prop: string | symbol): number {
    return prop in target ? target[prop as unknown as number] : 0;
  },
});
console.log(proxy[123]); // 0

// set 捕捉器：驗證型別
const typedArray = new Proxy([] as number[], {
  set(target, prop, val): boolean {
    if (typeof val !== "number") throw new TypeError("只能放數字");
    target[prop as unknown as number] = val;
    return true;
  },
});

// has 捕捉器：in 運算子
const range2 = new Proxy({ start: 1, end: 10 }, {
  has(target, prop): boolean {
    return Number(prop) >= target.start && Number(prop) <= target.end;
  },
});
console.log(5 in range2); // true

// Reflect：轉發操作（保持原生行為）
const observed = new Proxy({} as Record<string, unknown>, {
  set(target, prop, value, receiver): boolean {
    console.log(`SET ${String(prop)} = ${value}`);
    return Reflect.set(target, prop, value, receiver);
  },
});

// 可撤銷 Proxy
const { proxy: p2, revoke } = Proxy.revocable({ data: "sensitive" }, {});
console.log(p2.data);
revoke(); // 此後 p2 的所有操作都會報錯
```

---

## 正則表達式

```ts
// 建立正規表示式
const re1: RegExp = /pattern/flags;
const re2: RegExp = new RegExp("pattern", "flags");

// 修飾符（flags）
// g：全域搜尋   i：忽略大小寫   m：多行   s：. 匹配換行   u：Unicode   y：粘性

// 常用方法
const str3 = "Hello World";
str3.match(/\w+/g);         // ["Hello", "World"]
str3.search(/World/);       // 6
str3.replace(/World/, "JS"); // "Hello JS"
str3.replaceAll(/o/g, "0"); // "Hell0 W0rld"
str3.split(/\s/);           // ["Hello", "World"]
/World/.test(str3);         // true

// 字元類
/\d/.test("3");    // 數字
/\w/.test("a");    // 字母/數字/_
/\s/.test(" ");    // 空白
/\D/.test("a");    // 非數字

// 量詞
/\d{3}/.test("123");   // 恰好 3 個
/\d{2,4}/.test("12");  // 2 到 4 個
/\d+/.test("1");       // 1 個以上
/\d*/.test("");        // 0 個以上
/\d?/.test("");        // 0 或 1 個

// 錨點
/^\d/.test("1abc");  // true（開頭是數字）
/\d$/.test("abc1"); // true（結尾是數字）

// 捕獲群組
const dateStr = "2024-01-15";
const match = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/);
if (match) {
  const [full, year, month, day] = match;
}

// 具名群組
const namedMatch = dateStr.match(/(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})/);
const year = namedMatch?.groups?.year; // "2024"

// 前瞻 / 後顧
// (?=Y)：前瞻肯定    (?!Y)：前瞻否定
// (?<=Y)：後顧肯定   (?<!Y)：後顧否定
"1px".replace(/\d+(?=px)/, "5"); // "5px"（只替換 px 前面的數字）
```

---

## 瀏覽器 API（TypeScript 型別）

### DOM 操作

```ts
// 搜尋元素
const elem: HTMLElement | null = document.getElementById("main");
const elems: NodeListOf<Element> = document.querySelectorAll(".item");
const div: HTMLDivElement | null = document.querySelector<HTMLDivElement>(".box");

// 型別安全存取
if (elem) {
  console.log(elem.innerHTML);
  elem.style.color = "red";
}

// 建立元素
const newDiv: HTMLDivElement = document.createElement("div");
newDiv.className = "container";
newDiv.textContent = "Hello";
document.body.append(newDiv);

// 修改樣式
const box = document.querySelector<HTMLElement>(".box");
if (box) {
  box.style.width = "100px";
  box.classList.add("active");
  box.classList.remove("hidden");
  box.classList.toggle("visible");
}
```

### 事件

```ts
// 事件監聽器（型別安全）
const btn = document.querySelector<HTMLButtonElement>("#submit");
btn?.addEventListener("click", (e: MouseEvent) => {
  e.preventDefault();
  console.log(e.target);
});

// 事件委托
document.getElementById("list")?.addEventListener("click", (e: Event) => {
  const target = e.target as HTMLElement;
  if (target.matches("li")) {
    console.log("clicked:", target.textContent);
  }
});

// 自訂事件
const myEvent = new CustomEvent<{ detail: string }>("my-event", {
  bubbles: true,
  detail: { detail: "data" } as any,
});
document.dispatchEvent(myEvent);
```

### Fetch 與網路

```ts
// 基本 fetch
async function getUser(id: number): Promise<{ name: string; email: string }> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

// 帶選項的 fetch
async function postData(url: string, data: object): Promise<unknown> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

// FormData
const formData = new FormData();
formData.append("name", "John");
formData.append("age", "30");
await fetch("/submit", { method: "POST", body: formData });

// 中止請求（AbortController）
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);
try {
  const res = await fetch("/slow-api", { signal: controller.signal });
} catch (err) {
  if (err instanceof DOMException && err.name === "AbortError") {
    console.log("請求已中止");
  }
}

// WebSocket
const socket = new WebSocket("wss://example.com/ws");
socket.addEventListener("open", () => socket.send("hello"));
socket.addEventListener("message", (e: MessageEvent<string>) => {
  console.log("收到:", e.data);
});
socket.addEventListener("close", () => console.log("連線關閉"));
```

### 瀏覽器儲存

```ts
// localStorage（字串，持久）
localStorage.setItem("user", JSON.stringify({ name: "John" }));
const user4 = JSON.parse(localStorage.getItem("user") ?? "null") as { name: string } | null;
localStorage.removeItem("user");
localStorage.clear();

// sessionStorage（字串，會話）
sessionStorage.setItem("token", "abc123");

// Cookie
document.cookie = "name=John; max-age=86400; path=/";
```

---

## 進階特性

### BigInt

```ts
const big: bigint = 9007199254740991n;
const alsoNice: bigint = BigInt(9007199254740991);

// BigInt 與 number 不能混用
// big + 1;           // 錯誤
big + BigInt(1);      // 正確
Number(big);          // 轉回 number（精度可能損失）

// 比較可以混用
console.log(1n == 1);   // true（寬鬆）
console.log(1n === 1);  // false（嚴格，型別不同）
```

### 事件循環（Event Loop）概念

```ts
// 宏任務（Macro-task）：setTimeout, setInterval, I/O
// 微任務（Micro-task）：Promise.then, queueMicrotask

console.log("start");
setTimeout(() => console.log("timeout"), 0);
Promise.resolve().then(() => console.log("promise"));
console.log("end");
// 輸出順序：start → end → promise → timeout

// queueMicrotask
queueMicrotask(() => console.log("microtask"));

// MutationObserver（DOM 變動觀察）
const observer = new MutationObserver((mutations: MutationRecord[]) => {
  mutations.forEach(m => console.log(m.type));
});
observer.observe(document.body, { childList: true, subtree: true });
```

---

> 本筆記涵蓋 javascript.info 第一部分（JavaScript 語言）與部分第二、三部分。
> 所有程式碼已轉為 TypeScript，加入型別標注。
> 更新日期：2026-05-31
