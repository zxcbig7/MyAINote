---
type: concept
domain: tech
tags: [kubernetes, k8s, beginner, yaml, syntax, indentation]
sources: []
created: 2026-08-14
updated: 2026-08-14
---

# 入門第四章：YAML 不是程式語言

到目前為止你都在下指令。從這一章開始，你要學會用**檔案描述你想要的狀態**——而 K8s 用的描述格式是 YAML。

很多人在這裡受挫，因為 YAML 看起來很簡單（就是縮排嘛），但寫起來一直出錯，而且錯誤訊息常常指向一個看起來沒問題的行號。這一章把規則講清楚，之後你寫 YAML 出錯的機率會降低九成。

## YAML 在做什麼

先建立正確的期待：**YAML 是一種資料格式，不是程式語言。** 它沒有變數、沒有邏輯、沒有迴圈，只能表達「資料長什麼樣」。

它跟 JSON 是等價的（任何 YAML 都能轉成 JSON），只是寫起來對人友善——不用寫一堆大括號和引號，還可以加註解。

YAML 只有三種東西，任何複雜的檔案都是這三種的組合：

| 結構 | 長什麼樣 | 對應的程式概念 |
| --- | --- | --- |
| **純量（scalar）** | `name: nginx` | 單一的值：字串、數字、布林 |
| **對映（map）** | 一組 `key: value` | 字典 / 物件 |
| **序列（list）** | 一串 `-` 開頭的項目 | 陣列 / 清單 |

```yaml
# 這是一個 map，有三個 key
name: my-app # 純量：字串
replicas: 3 # 純量：數字
enabled: true # 純量：布林

# 巢狀 map：labels 的值又是一個 map
labels:
  app: my-app
  tier: backend

# list：三個字串
ports:
  - 80
  - 443
  - 8080

# list of map：最常用也最容易寫錯的組合
containers:
  - name: web
    image: nginx:1.25
  - name: sidecar
    image: filebeat:8.13
```

最後那個 `containers` 值得多看兩眼，因為 K8s 的 YAML 到處都是它。它的意思是：`containers` 是一個清單，清單裡每一項都是一個 map。`-` 開頭那一行的 `name` 與下一行的 `image` 屬於同一個項目，因為它們縮排對齊。

## 縮排：三條規則

YAML 用縮排表達從屬關係，這是它最強大也最容易出錯的地方。三條規則記熟就不會錯：

**規則一：只能用空格，絕對不能用 Tab。** 這是 YAML 規格明文禁止的。麻煩的是編輯器裡 Tab 和空格看起來一樣，所以錯誤訊息會很莫名其妙。**解法是在編輯器裡設定「Tab 自動轉成空格」，一勞永逸。**

**規則二：同一層的項目必須對齊在同一欄。** 差一個空格就是不同層。

**規則三：縮排幾格不重要，重要的是一致。** 慣例用 2 格。

看一個典型的錯誤：

```yaml
# 錯：image 比 name 多縮排，YAML 會困惑
containers:
  - name: web
     image: nginx
```

```yaml
# 對：同一項目內的 key 對齊
containers:
  - name: web
    image: nginx
```

還有一個新手常見的困惑——list 底下的 `-` 要不要縮排？兩種寫法都合法，但**不要混用**：

```yaml
# 寫法 A（推薦，視覺上比較清楚）
ports:
  - 80
  - 443

# 寫法 B（也合法）
ports:
- 80
- 443
```

## 字串什麼時候要加引號

大部分時候不用，但有五種情況必須加，否則會被誤解成別的東西。

**情況一：值裡有冒號加空格。** `: ` 是 YAML 的分隔符號。

```yaml
message: "錯誤: 找不到檔案" # 必須加引號
```

**情況二：值以特殊字元開頭。** `-`、`?`、`:`、`,`、`[`、`]`、`{`、`}`、`#`、`&`、`*`、`!`、`|`、`>`、`%`、`@` 開頭都要小心。

**情況三：你要的是字串，但它長得像數字。** 這一條在 K8s 裡天天遇到：

```yaml
version: 1.10 # 這是數字，YAML 會存成 1.1，你的版本號被吃掉了
version: "1.10" # 這才是字串

phone: 0912345678 # 前導零可能被當成八進位
phone: "0912345678"

id: 12345678901234567890 # 太大的數字可能精度出錯
id: "12345678901234567890"
```

**情況四：你要的是字串，但它長得像布林。** 這是 YAML 最惡名昭彰的陷阱。在 YAML 1.1（多數工具仍相容）裡，下面這些**未加引號時全部會變成布林值**：

```
true  True  TRUE  yes  Yes  YES  on  On  ON
false False FALSE  no  No  NO   off Off OFF
```

這造成一個著名的笑話：挪威的國碼是 `NO`，所以

```yaml
country: NO # 變成 false！
country: "NO" # 才是挪威
```

**情況五：空字串。** 直接寫 `key:` 是 null，不是空字串，要空字串得寫 `key: ""`。

### 單引號還是雙引號

| 引號 | 行為 |
| --- | --- |
| `'單引號'` | 完全照字面，裡面什麼都不解析（要表達單引號本身就打兩個 `''`） |
| `"雙引號"` | 會解析跳脫字元：`\n` 換行、`\t` tab、`\\` 反斜線 |

不確定的時候用**雙引號**比較符合直覺，但如果字串裡有反斜線（例如 Windows 路徑或正則表達式），用單引號才不會被跳脫規則搞亂。

## 多行字串：四個符號

設定檔內容、腳本、憑證這些多行內容，要用專門的語法。

```yaml
# | 保留換行（最常用）
script: |
  #!/bin/sh
  echo "line 1"
  echo "line 2"

# > 摺疊成一行（換行變空格）
description: >
  這段很長的文字
  會被合併成一行
  
# |- 保留換行，但去掉最後的換行
config: |-
  key=value

# >- 摺疊，且去掉最後的換行
note: >-
  合併成一行且不留尾巴
```

判斷法很簡單：**內容的換行有意義（腳本、設定檔）用 `|`；只是為了排版好看而換行（說明文字）用 `>`**。

要注意的是，`|` 底下的內容以**第一行的縮排**為基準，多出來的縮排會被保留。這就是為什麼把 YAML 塞進 YAML（例如 Helm 模板產生設定檔）時縮排特別容易出事。

## null、註解與多文件

```yaml
# 這四種都是 null
a:
b: null
c: ~
d: Null

# 註解用 # 開頭，可以在行尾
name: nginx # 這是註解

# 一個檔案放多個文件，用 --- 分隔
apiVersion: v1
kind: Service
# ...
---
apiVersion: apps/v1
kind: Deployment
# ...
```

多文件分隔在 K8s 特別實用：一個服務相關的 Deployment、Service、ConfigMap 可以放在同一個檔案，`kubectl apply -f` 一次全部套用。

## 共用片段：anchor 與別名

當同樣的內容要重複好幾次，YAML 有內建的共用機制：

```yaml
# & 定義錨點，* 引用
defaults: &defaults
  restart: always
  memory: 512Mi

service-a:
  <<: *defaults # << 是合併
  image: app-a

service-b:
  <<: *defaults
  image: app-b
  memory: 1Gi # 覆蓋掉合併進來的值
```

K8s 的 manifest 很少用它（因為有 Helm 和 Kustomize），但 Docker Compose 與 CI 設定檔常見，看到要認得。

## 錯誤訊息怎麼讀

| 訊息 | 意思 | 通常的原因 |
| --- | --- | --- |
| `found character '\t' that cannot start any token` | 用了 Tab | 換成空格 |
| `mapping values are not allowed in this context` | 冒號出現在不該出現的地方 | 值裡有 `: ` 沒加引號 |
| `could not find expected ':'` | 缺少冒號或縮排錯 | 檢查上一行 |
| `did not find expected key` | 縮排不一致 | 同層對齊 |
| `expected <block end>, but found ...` | 結構斷掉 | 通常錯在**報錯行的上面幾行** |
| `duplicate key` | 同一層有重複的 key | 檢查有沒有貼重複 |

**最重要的一條經驗：YAML 的錯誤行號常常不是真正出錯的地方。** 解析器是在後面某一行才發現「結構對不上」，但問題往往在前面。看到行號先往上找兩三行。

## 怎麼驗證

不要靠肉眼。三種驗證方式，由淺到深：

```powershell
# 1. 純語法檢查（Python 有裝的話）
python -c "import yaml,sys; yaml.safe_load(open('app.yaml',encoding='utf-8')); print('OK')"

# 2. K8s 結構檢查（不會真的部署）
kubectl apply -f app.yaml --dry-run=client

# 3. 送到 API Server 走完驗證與預設值填充（同樣不會真的部署）
kubectl apply -f app.yaml --dry-run=server -o yaml
```

第三種特別值得養成習慣：它會回傳「這份 YAML 實際會變成什麼樣子」，包含 K8s 自動補上的所有預設值。你寫 10 行、它回你 60 行，多出來的那 50 行就是預設值——這是理解 K8s 行為最快的方式之一。

另外，**在編輯器裝一個 YAML 外掛**（VS Code 的 YAML extension）會即時標紅、自動補完 K8s 欄位名，能省掉大量低級錯誤。

## K8s YAML 的固定骨架

最後預告一下你接下來會看到的東西。**所有** K8s 的 YAML 都是同一個骨架：

```yaml
apiVersion: apps/v1 # 用哪個版本的 API
kind: Deployment # 這是什麼類型的東西
metadata: # 它叫什麼、屬於哪個群組
  name: my-app
  namespace: default
  labels:
    app: my-app
spec: # 你想要它變成什麼樣子
  replicas: 3
  # ...（每種 kind 的 spec 內容不同）
status: # 它現在實際上是什麼樣子（K8s 自己填，你不用寫）
```

五個部分裡，你只需要寫前四個。核心的心智模型是：**`spec` 是你的願望，`status` 是現實，K8s 的工作就是不斷讓現實靠近願望。** 這句話是整個 K8s 的精神，之後每一章都會回到它。

## 動手練習

把下面這段錯誤的 YAML 修好（有四個錯誤），然後用 `--dry-run=client` 驗證：

```yaml
apiVersion: v1
kind: Pod
metadata:
	name: test-pod
  labels:
    version: 1.10
    enabled: yes
spec:
  containers:
  - name: web
     image: nginx:1.25
```

<details>
<summary>答案</summary>

1. `name: test-pod` 前面用了 **Tab**，要換成空格
2. `version: 1.10` 會被解析成數字 `1.1`，label 的值必須是字串 → `version: "1.10"`
3. `enabled: yes` 會變成布林 `true`，label 值必須是字串 → `enabled: "yes"`
4. `image` 比 `name` 多縮排一格，要對齊

修好之後：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  labels:
    version: "1.10"
    enabled: "yes"
spec:
  containers:
    - name: web
      image: nginx:1.25
```

順帶一提，第 2、3 點是 K8s 特有的規則：**label 的值必須是字串**，寫成數字或布林會被 API Server 拒絕。這是「明明照抄範例卻被拒絕」的常見原因。

</details>

## 本章回顧

- YAML 是資料格式不是程式語言，只有純量、map、list 三種結構
- 縮排只能用空格、同層要對齊、幾格不重要但要一致
- 五種情況要加引號：含 `: `、特殊字元開頭、像數字的字串、像布林的字串（`yes`/`no`/`on`/`off`）、空字串
- `|` 保留換行、`>` 摺疊成一行
- 錯誤行號常常不是真正出錯的地方，往上找
- 用 `--dry-run=server` 看 K8s 補了哪些預設值
- K8s YAML 骨架固定：`apiVersion` / `kind` / `metadata` / `spec`（+ K8s 自己填的 `status`）

## 自我檢查

1. 為什麼 `version: 1.10` 是個問題？
2. `country: NO` 會被解析成什麼？
3. `|` 跟 `>` 差在哪？各自什麼時候用？
4. YAML 報錯說第 20 行有問題，你第一件事做什麼？
5. `spec` 和 `status` 分別代表什麼？

下一章開始動手——你會跑起第一個容器，然後用 K8s 做同一件事。

## 連結

- [[intro-3-network-basics]] — 上一章：網路基礎
- [[intro-5-first-container-and-pod]] — 下一章：第一個容器與第一個 Pod
- [[03-api-and-yaml]] — 正文：K8s API 機制與 YAML 進階陷阱
- [[18-yaml-fields-pod]] — 附錄 C-1：所有欄位的完整參考（之後查用）
- [[k8s-mastery]] — 教材總目錄（含各階段的閱讀路徑）
