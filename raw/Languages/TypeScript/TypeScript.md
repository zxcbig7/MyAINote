---
tags: [typescript, programming]
---

> 關聯：[[typescript]]

# TypeScript

## 註解

```tsx
// 單行註解

/* 多行註解
   可以換行
*/

/* 不能巢狀註解： /* nested */ 會造成語法錯誤 */
```

## 變數與型別（TypeScript 觀點）

### 變數宣告（let / const）

> TypeScript 建議優先使用 `const`，需要重新賦值時才用 `let`。
> 

```tsx
// 具型別註記（type annotation）
let name: string = "小明";
let age: number = 25;

// 型別推論（type inference）：TS 會從初始值推論型別
const pi = 3.14159; // number
const email = "example@email.com"; // string

// 也可以宣告 union（聯合型別）
let id: string | number = "A-001";
id = 1001;
```

### 基本型別（Primitive types）

```tsx
// string
const text: string = "Hello World";
const text2 = 'TypeScript';
const text3 = `範本字串：${name}`;

// number
const integer: number = 42;
const decimal: number = 3.14;
const negative = -10;

// boolean
const isTrue: boolean = true;
const isFalse = false;

// null / undefined
let empty: null = null;
let notDefined: undefined = undefined;

// unknown / any（盡量避免 any）
let data: unknown;
let loose: any = 123;
loose = "anything";
```

### 陣列與元組（Array / Tuple）

```tsx
// 陣列
const colors: string[] = ["紅", "綠", "藍"];
const numbers: Array<number> = [1, 2, 3, 4, 5];

// union array
const mixed: (string | number)[] = ["A", 1, "B", 2];

// 元組（固定長度與順序）
const point: [number, number] = [25.033, 121.565];
```

### 物件與介面（Object / Interface）

```tsx
// 用 interface 描述物件結構
interface Person {
	name: string;
	age: number;
	city?: string; // optional property
}

const person: Person = {
	name: "小華",
	age: 30,
	city: "台北",
};

// 型別別名（type alias）也很常用
type UserId = string | number;
const userId: UserId = "u_001";
```

### undefined 與 null（更貼近 TS 的行為）

> 多數專案會開啟 `strictNullChecks`，此時 `null`/`undefined` 需要明確寫進型別中。
> 

```tsx
// 變數可能不存在，就用 union 表示
let input: string | undefined;

if (input === undefined) {
	console.log("input 尚未賦值");
}

// 取用前先縮窄（narrowing）
if (input) {
	console.log(input.toUpperCase());
}

// 也可以用 optional chaining
const upper = input?.toUpperCase();
```

### 變數作用域（Scope）

```tsx
if (true) {
	var x = 5;
}
console.log(x); // 5（var 為 function-scoped）

if (true) {
	let y = 5;
}
console.log(y); // TS/JS 都會報錯：y is not defined
```

### 變數提升（Hoisting）

```tsx
console.log(x === undefined); // true
var x = 3;

// let/const 也會「提升」，但在 TDZ（暫時性死區）中不可使用
// console.log(z); // ReferenceError
let z = 10;
```

<aside>
💡

TypeScript 只負責型別檢查與轉譯（compile to JS）。

提升（hoisting）、TDZ 等行為仍然是 JavaScript 執行時（runtime）的規則。

</aside>

### 函式提升（Function hoisting）

```tsx
// Function declaration：可在宣告前呼叫
foo();
function foo(): void {
	console.log("bar");
}

// Function expression：不可在賦值前呼叫
// baz(); // TS 會警告，執行時也會出錯
const baz = (): void => {
	console.log("bar2");
};
```

### 字串轉數字

```tsx
const n1 = Number("1.1");
const n2 = parseInt("42", 10);
const n3 = parseFloat("3.14");

// unary plus
const n4 = +"2.5";

// NaN 檢查
const maybe = Number("abc");
if (Number.isNaN(maybe)) {
	console.log("不是有效數字");
}
```

---

## 運算子（Operators）

### 算術運算子

```tsx
const a = 10;
const b = 3;

const sum = a + b;
const diff = a - b;
const product = a * b;
const quotient = a / b;
const remainder = a % b;
const power = a ** b;
```

### 比較運算子（建議使用嚴格比較）

```tsx
const x = 5;
const y = "5";

// x == y;  // 不建議（型別轉換）
// x != y;

x === Number(y); // ✅
x !== Number(y);
```

### 邏輯運算子與 Falsy

```tsx
const age = 20;
const hasID = true;

const ok = age >= 18 && hasID;
const canEnter = age >= 18 || hasID;
const deny = !hasID;
```

Falsy 值：

- `false`
- `undefined`
- `null`
- `0`
- `NaN`
- 空字串（`""`）

## 變數預設值 ?? vs. ||

```tsx
// ?? vs ||（Nullish Coalescing vs OR）
// ?? 只在左側是 null / undefined 時取右側
// || 在左側是任何 falsy（"", 0, false）時都取右側
const url = import.meta.env.VITE_API_BASE ?? "";  
const url2 = import.meta.env.VITE_API_BASE || "";
```

---

## 條件判斷（Control flow）

### if...else

```tsx
const score = 85;

if (score >= 90) {
	console.log("優秀");
} else if (score >= 60) {
	console.log("及格");
} else {
	console.log("不及格");
}
```

### switch

```tsx
const day: "星期一" | "星期六" | "星期日" | "其他" = "星期一";

switch (day) {
	case "星期一":
		console.log("工作日");
		break;
	case "星期六":
	case "星期日":
		console.log("週末");
		break;
	default:
		console.log("未知");
}
```

### 三元運算子

```tsx
const age2 = 20;
const status = age2 >= 18 ? "成年" : "未成年";
```

---

## 迴圈（Loops）

### for

```tsx
for (let i = 0; i < 5; i++) {
	console.log(i);
}
```

### for...of（遍歷可迭代）

```tsx
const fruits = ["蘋果", "香蕉", "橘子"];
for (const f of fruits) {
	console.log(f);
}
```

### for...in（遍歷物件 key）

```tsx
const p = { name: "小明", age: 25, city: "台北" };
for (const key in p) {
	// key 的型別是 string，要安全取值需縮窄或斷言
	const value = p[key as keyof typeof p];
	console.log(key, value);
}
```

---

## 函式（Functions）

### 函式宣告 + 參數/回傳型別

```tsx
function greet(name: string): string {
	return `你好，${name}`;
}

const message = greet("小華");
```

### 函式表達式 / 箭頭函數

```tsx
const add = (a: number, b: number): number => a + b;
const multiply = (a: number, b: number): number => a * b;
const square = (x: number): number => x * x;
```

### 預設參數

```tsx
function welcome(name: string = "訪客"): string {
	return `歡迎，${name}`;
}
```

### Never / throw（例外）

```tsx
function fail(message: string): never {
	throw new Error(message);
}
```

---

## 陣列操作（Array methods）

```tsx
const numbers = [1, 2, 3, 4, 5];

numbers.push(6);
numbers.pop();
numbers.unshift(0);
numbers.shift();

const subset = numbers.slice(1, 3);
numbers.splice(2, 0, 99);

numbers.forEach((num) => console.log(num));
const doubled = numbers.map((num) => num * 2);
const evens = numbers.filter((num) => num % 2 === 0);
const found = numbers.find((num) => num > 3);
const sum2 = numbers.reduce((acc, num) => acc + num, 0);
```

---

## 物件操作（Object）

### 物件字面值（Object literal）

```tsx
type SalesBrand = "Toyota" | "Honda" | "Saturn";

const sales: SalesBrand = "Toyota";

function carTypes(name: string): string {
	if (name === "Honda") return name;
	return `Sorry, we don't sell ${name}.`;
}

const car = {
	myCar: "Saturn",
	getCar: carTypes("Honda"),
	special: sales,
};

console.log(car.myCar);
console.log(car.getCar);
console.log(car.special);
```

### 建立與存取（搭配 interface）

```tsx
interface Student {
	name: string;
	age: number;
	grades: number[];
	study: () => void;
	email?: string;
}

const student: Student = {
	name: "小明",
	age: 20,
	grades: [85, 90, 78],
	study() {
		console.log(`${this.name} 正在學習`);
	},
};

student.email = "ming@example.com";
student.study();
```

---

## 字串操作（String）

```tsx
const text = "TypeScript 教學";

text.length;
text.toUpperCase();
text.toLowerCase();
text.indexOf("教學");
text.includes("Type");
text.startsWith("Type");
text.endsWith("學");
text.slice(0, 10);
text.split(" ");
["Hello", "World"].join(" ");
text.replace("教學", "入門");
"  hello  ".trim();
```

---

## DOM 操作（TypeScript + DOM 型別）

> 在 TS 中，DOM API 會有型別。常見做法是先判斷是否為 `null`。
> 

### 選取元素

```tsx
const el = document.getElementById("myId");
if (el) {
	el.textContent = "新文字";
}

const button = document.querySelector<HTMLButtonElement>("#myButton");
button?.addEventListener("click", () => {
	console.log("按鈕被點擊了");
});
```

### 修改內容與樣式

```tsx
const element = document.querySelector<HTMLElement>(".myClass");
if (element) {
	element.textContent = "新文字";
	element.style.color = "red";
	element.classList.add("active");
	element.setAttribute("data-id", "123");
}
```

---

## 非同步程式設計（Async）

### Promise

```tsx
function delay(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

delay(300).then(() => console.log("done"));
```

### async/await

```tsx
type ApiUser = { id: number; name: string };

async function fetchUsers(): Promise<ApiUser[]> {
	const res = await fetch("https://api.example.com/users");
	if (!res.ok) throw new Error("Request failed");
	return (await res.json()) as ApiUser[];
}

fetchUsers().then((users) => console.log(users));
```

### Promise.all（並行）

```tsx
async function parallel() {
	const [u1, u2] = await Promise.all([fetchUsers(), fetchUsers()]);
	console.log(u1.length + u2.length);
}
```

---

## 錯誤處理（Error handling）

```tsx
function divide(a: number, b: number): number {
	if (b === 0) throw new Error("除數不能為零");
	return a / b;
}

try {
	divide(10, 0);
} catch (e) {
	// e 在 strict 模式通常是 unknown
	if (e instanceof Error) {
		console.log(e.message);
	}
}
```

---

## 模組化（ESM + TypeScript）

### 匯出（export）

```tsx
// math.ts
export const PI = 3.14159;

export function add(a: number, b: number): number {
	return a + b;
}

export default function subtract(a: number, b: number): number {
	return a - b;
}
```

### 匯入（import）

```tsx
// main.ts
import subtract, { PI, add } from "./math";

console.log(PI);
console.log(add(5, 3));
console.log(subtract(10, 4));
```

---

## 實用技巧（TS 常用語法）

### 展開運算子（Spread）

```tsx
const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];
const combined = [...arr1, ...arr2];

const p1 = { name: "小明", age: 25 };
const employee = { ...p1, company: "ABC" };
```

### 可選鏈（Optional chaining）

```tsx
type User = { name: string; address?: { city: string; zip?: string } };

const user: User = { name: "小明", address: { city: "台北" } };

const city = user.address?.city;
const zip = user.address?.zip;
```

### 空值合併運算子（Nullish coalescing）

```tsx
const value: string | null = null;
const result = value ?? "預設值";

const count = 0;
const result2 = count ?? 10; // 0
```

### 型別斷言（Type assertion）

```tsx
const inputEl = document.querySelector("#name") as HTMLInputElement | null;
const v = inputEl?.value;
```