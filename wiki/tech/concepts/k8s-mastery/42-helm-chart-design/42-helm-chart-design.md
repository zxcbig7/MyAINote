---
type: reference
domain: tech
tags: [kubernetes, k8s, helm, chart-design, library-chart, argocd, values-schema]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 附錄 T：Chart 設計與內部共用

正文第 10 章講的是**使用** Helm：`include` 與 `template` 的差別、`nindent` 的縮排、values 覆蓋優先序、除錯三件套。那些是「拿到一份 chart 怎麼用」。

這一份講另一件事：**設計一份給別人用的 chart**。附錄 O 說 golden path 最實用的載體是一份內部 Helm chart——那份 chart 就是這一章的主題。它跟自用的 chart 有本質差異，因為**它是一個 API**：一旦有五個團隊在用，你的每個 values 欄位都變成一份承諾，改壞了會同時影響所有人。

---

## Part 1：chart 是 API，values.yaml 是它的介面

這個心智模型決定了後面所有設計決策。

| | 自用的 chart | 給別人用的 chart |
| --- | --- | --- |
| 改欄位名 | 改一下就好 | **破壞性變更**，要走過渡期 |
| 預設值 | 自己知道就好 | 決定了新使用者的第一印象 |
| 錯誤訊息 | 自己看得懂 | 要讓不懂 K8s 的人看得懂 |
| 沒想到的需求 | 直接改 chart | 要有逃生門，否則對方就 fork 走了 |
| 文件 | 可以沒有 | `values.yaml` 的註解就是文件 |

把它當 API 看之後，一個具體的判準浮現：**每加一個 values 欄位之前，先問「我準備好永遠支援它了嗎」**。移除一個欄位的成本遠高於當初不加。

---

## Part 2：values 介面設計

### 最小可用要夠小

好的 chart 讓使用者只填三五行就能跑起來。附錄 O 那份範例是這個原則的實踐：

```yaml
image:
  repository: harbor.example.com/team-a/my-api
  tag: "1.4.0"
healthPath: /healthz
```

其餘全部有合理預設。**如果你的 chart 要求使用者填三十行才能跑，多數人會複製別人的 values 檔然後不理解自己填了什麼**——安全基線也就跟著失效。

### 命名跟社群慣例對齊

不要發明自己的一套。使用者在別的 chart 學到的直覺，應該在你的 chart 也適用：

```yaml
# 慣例的名稱，照用
replicaCount: 3
image:
  repository: nginx
  tag: ""
  pullPolicy: IfNotPresent
imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""
serviceAccount:
  create: true
  name: ""
podAnnotations: {}
podSecurityContext: {}
securityContext: {}
resources: {}
nodeSelector: {}
tolerations: []
affinity: {}
```

`image.tag` 預設空字串、實際回退到 `appVersion` 是常見做法——這樣升級 chart 就自動換版，而使用者要釘版本時可以覆蓋。

### 一定要有逃生門

**這是內部 chart 最常被忽略、也最影響採用率的一項。** 你不可能預見所有需求，所以要留出口讓使用者自己補，否則他們只能 fork 你的 chart——那時候你的安全基線更新就再也推不到他們身上了。

至少提供這幾個：

```yaml
extraEnv: [] # 額外環境變數
extraEnvFrom: [] # 額外的 ConfigMap/Secret 整包注入
extraVolumes: [] # 額外的 volume
extraVolumeMounts: []
extraContainers: [] # sidecar
extraInitContainers: []
podAnnotations: {} # 例如 Istio 的注入控制
podLabels: {}
extraObjects: [] # 完全自訂的額外資源
```

模板裡這樣接：

```yaml
      env:
        - name: ASPNETCORE_URLS
          value: "http://+:8080"
        {{- with .Values.extraEnv }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
```

`extraObjects` 這一個特別有用——讓使用者把任意 YAML 塞進來，由你的 chart 一起部署：

```yaml
{{- range .Values.extraObjects }}
---
{{ tpl (toYaml .) $ }}
{{- end }}
```

**有了逃生門，「這個 chart 做不到我要的事」就不再是離開的理由。**

### 用 schema 驗證，而不是讓它默默壞掉

`values.schema.json` 讓 Helm 在渲染前就驗證輸入：

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image"],
  "properties": {
    "replicaCount": { "type": "integer", "minimum": 1 },
    "image": {
      "type": "object",
      "required": ["repository"],
      "properties": {
        "repository": { "type": "string" },
        "tag": { "type": "string" }
      }
    },
    "resources": {
      "type": "object",
      "required": ["requests"]
    }
  }
}
```

好處是**錯誤訊息指向具體欄位**，而不是渲染出一份壞掉的 YAML 再讓 API Server 拒絕。搭配 `required` 函式處理 schema 表達不了的：

```yaml
image: {{ required "必須指定 image.repository" .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}
```

**注意 `tag` 要加引號或用 `default`**——`1.10` 這種 tag 沒加引號會被 YAML 當成數字變成 `1.1`（入門第四章）。這是 chart 設計最常見的一個 bug。

---

## Part 3：模板實作

### helper 集中管理

`_helpers.tpl` 放共用片段。最重要的是標準 labels：

```
{{- define "mychart.labels" -}}
app.kubernetes.io/name: {{ include "mychart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "mychart.chart" . }}
{{- end }}

{{- define "mychart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mychart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

**`labels` 與 `selectorLabels` 必須分開，這是關鍵設計。** `selector` 建立後不可修改（附錄 C-2），所以它只能包含**永不改變**的標籤；而 `labels` 含有 version 與 chart 版本，每次升級都會變。兩者混用的結果是升級時被 API Server 拒絕，而且只能刪掉重建。

### 設定變更觸發滾動更新

ConfigMap 改了但 Pod 不會重啟（正文第 6 章）。標準解法是把設定的雜湊放進 Pod annotation：

```yaml
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
```

設定一變 → 雜湊變 → Pod template 變 → 觸發滾動更新。**這是內部 chart 該內建的能力**，讓使用者不必自己想這件事。

### `lookup` 是個陷阱

`lookup` 可以查詢叢集裡現有的資源，常被用來「如果 Secret 已存在就沿用，否則產生新密碼」：

```yaml
{{- $existing := lookup "v1" "Secret" .Release.Namespace "my-secret" }}
password: {{ if $existing }}{{ index $existing.data "password" }}{{ else }}{{ randAlphaNum 32 | b64enc }}{{ end }}
```

**這個寫法在 ArgoCD 底下會壞掉**，原因見 Part 6：ArgoCD 用 `helm template` 渲染，沒有叢集連線，`lookup` 一律回傳空值——於是每次同步都產生新密碼。

**結論：不要在 chart 裡產生機密。** 讓使用者自己提供，或用 External Secrets Operator 從 Vault 取（附錄 C-5）。這是設計上的取捨，不是技術限制。

---

## Part 4：Library chart 與 subchart

### Library chart：共用模板而不產生資源

多個 chart 需要共用同一套 helper 時，用 `type: library`：

```yaml
# common-lib/Chart.yaml
apiVersion: v2
name: common-lib
version: 1.2.0
type: library # 不會產生任何資源，只提供 define
```

其他 chart 依賴它：

```yaml
dependencies:
  - name: common-lib
    version: "1.2.x"
    repository: "https://charts.internal.example.com"
```

```yaml
{{ include "common-lib.securityContext" . }}
```

**這是內部平台維護多個 chart 時的正確結構**：安全基線寫在 library chart 一次，所有 chart 引用它。升級基線只要發一個新版 library。

### Subchart 的三個陷阱

Subchart（依賴其他完整 chart，例如你的 app chart 依賴 PostgreSQL chart）看起來方便，但有代價：

**陷阱一：values 的作用域。** 父 chart 覆蓋 subchart 的值要用 subchart 名稱包起來：

```yaml
# 父 chart 的 values.yaml
postgresql:
  auth:
    database: myapp
```

而 `global:` 底下的值才會被所有 subchart 看到。搞混這兩者是「我明明設了為什麼沒生效」的常見原因。

**陷阱二：依賴的生命週期綁在一起。** subchart 跟著父 chart 一起安裝、升級、刪除。你的應用要升級，PostgreSQL 也會被一起處理——**而資料庫通常不該跟應用同步升級**。

**陷阱三：條件啟用的複雜度。**

```yaml
dependencies:
  - name: postgresql
    version: "15.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

正式環境用外部資料庫、開發環境用內建的——聽起來合理，但**結果是兩個環境跑的是不同架構**，開發環境測不到正式環境的問題。

**判準**：subchart 適合「跟應用生命週期一致、且不含重要資料」的東西（例如一個純快取用的 Redis）。有狀態且重要的東西（實戰第五章的資料庫）應該分開部署，用 values 指向它。

---

## Part 5：版本與破壞性變更

### 兩個版本號的分工

| 欄位 | 意義 | 什麼時候要動 |
| --- | --- | --- |
| `version` | **chart 自己**的版本 | 只要 chart 內容有變就要動 |
| `appVersion` | 裡面那個應用的版本 | 應用升版時 |

改了 template 但應用沒變 → 只加 `version`；應用升版 → 兩個都動。**ArgoCD 是以 `version` 判斷要不要重新渲染的**，忘了加會導致改動不生效。

`version` 要遵守 SemVer，而且對 chart 的意義要定義清楚：

- **PATCH**：修 bug、改註解，使用者無感
- **MINOR**：新增 values 欄位（有預設值，向後相容）
- **MAJOR**：**移除或改名 values 欄位、改變預設行為**

### 破壞性變更的過渡期

要把 `healthPath` 改名成 `probes.livenessPath` 時，**不要直接改**。走三步：

```yaml
{{- $livenessPath := .Values.probes.livenessPath | default .Values.healthPath | default "/healthz" }}
{{- if .Values.healthPath }}
{{- fail "healthPath 已於 v2.0 移除，請改用 probes.livenessPath" }}
{{- end }}
```

1. **新舊並存**（MINOR 版）：新欄位優先，舊欄位仍可用，用 `printf` 或註解提示即將棄用
2. **公告期**：CHANGELOG 寫明、通知所有使用者、給明確的截止版本
3. **移除**（MAJOR 版）：舊欄位若被設定就用 `fail` 給出**明確的遷移訊息**

第 3 步的 `fail` 訊息很重要——**直接移除的話，使用者的設定會被靜默忽略**，服務用預設值跑起來但行為不對，這比報錯難查得多。

### 每個 chart 都要有 CHANGELOG

至少記錄：版本號、日期、新增/變更/移除的 values 欄位、是否需要使用者採取行動。**內部 chart 是所有服務的共同依賴，變更公告不是禮貌而是必要。**

---

## Part 6：Helm 與 ArgoCD 一起用

這一節是實務上踩坑最多的地方，因為兩者的模型不同。

### 根本差異：ArgoCD 不執行 `helm install`

**ArgoCD 預設是用 `helm template` 把 chart 渲染成純 YAML，再自己 apply。** 這帶來一連串後果：

| Helm 的東西 | 在 ArgoCD 底下 |
| --- | --- |
| Release 物件（`helm list` 看得到的） | **不存在** |
| `helm rollback` | 用不了，改用 git revert |
| `lookup` 函式 | **一律回傳空**（沒有叢集連線） |
| Helm hooks（`helm.sh/hook`） | 被 ArgoCD 轉譯，行為與原生不同 |
| `--set` 的三方 chart 覆蓋 | 改用 Application 的 `helm.parameters` |
| `.Release.IsUpgrade` / `IsInstall` | 語意不再準確 |

### 四個具體的坑

**坑一：每次同步都 OutOfSync。** chart 裡有 `randAlphaNum`、`uuidv4`、或 `now` 這類每次渲染都不同的函式，渲染結果永遠跟叢集裡的不一樣。**修法是不要在 chart 裡產生隨機值**（Part 3 說過）。

**坑二：`lookup` 靜默失效。** 不會報錯，只是回傳空值，然後你的「沿用既有 Secret」邏輯每次都走 else 分支產生新密碼。**這是無聲的資料破壞**，特別危險。

**坑三：Helm hook 的行為差異。** ArgoCD 會把 `helm.sh/hook: pre-install` 轉成自己的 `PreSync`，但對應關係不是完全等價（例如 `hook-weight` 與 `sync-wave` 的語意）。**內部 chart 若要同時支援兩種用法，最好明確寫成 ArgoCD 的 annotation**（實戰第三章）。

**坑四：CRD 管理。** Helm 的 `crds/` 目錄只會在安裝時建立，**升級時不會更新、卸載時不會刪除**。ArgoCD 則會照常同步。三方 chart 含 CRD 時，建議把 CRD 拆出來獨立管理（用一個單獨的 Application 加 sync-wave 排在前面）。

### 建議的配置

```yaml
source:
  repoURL: https://charts.internal.example.com
  chart: my-app
  targetRevision: "2.1.0" # 明確釘 chart 版本
  helm:
    releaseName: my-app
    valueFiles:
      - values-prod.yaml
    parameters:
      - name: image.tag
        value: "1.4.0"
        forceString: true # 防止 1.10 變成 1.1
```

`forceString: true` 就是入門第四章那個 YAML 型別陷阱的解法。

---

## Part 7：測試

給別人用的 chart 一定要有 CI 測試，否則你改壞了會同時影響所有使用者。

```powershell
# 1. 語法與慣例檢查
helm lint ./charts/my-app

# 2. 渲染出來看（用不同 values 各渲染一次）
helm template test ./charts/my-app -f ci/values-minimal.yaml
helm template test ./charts/my-app -f ci/values-full.yaml

# 3. 驗證渲染結果是合法的 K8s 資源
helm template test ./charts/my-app -f ci/values-full.yaml | kubeconform -strict -summary

# 4. 檢查最佳實踐
helm template test ./charts/my-app -f ci/values-full.yaml | kube-linter lint -

# 5. 單元測試（helm unittest 外掛）
helm unittest ./charts/my-app
```

`ci/` 目錄放幾組代表性的 values（最小、完整、各種開關組合），每次 PR 都全部渲染一次。**這能抓到最常見的一類 bug：某個組合下模板產生無效 YAML**。

`helm unittest` 適合斷言具體行為：

```yaml
suite: deployment
templates:
  - deployment.yaml
tests:
  - it: 預設應該以非 root 執行
    asserts:
      - equal:
          path: spec.template.spec.securityContext.runAsNonRoot
          value: true
  - it: 沒給 image.repository 應該失敗
    set:
      image.repository: null
    asserts:
      - failedTemplate:
          errorMessage: "必須指定 image.repository"
```

**第二個測試特別值得寫**——它驗證的是「錯誤訊息是不是清楚的」，那正是給別人用的 chart 的品質指標。

---

## 檢查清單

**介面設計**

- [ ] 最小可用的 values 在五行以內
- [ ] 命名跟社群慣例對齊
- [ ] 有 `extraEnv` / `extraVolumes` / `extraContainers` / `podAnnotations` 等逃生門
- [ ] 有 `values.schema.json`，必填欄位用 `required` 給明確訊息
- [ ] `values.yaml` 每個欄位都有註解（它就是文件）
- [ ] `image.tag` 有處理型別（`quote` 或 `forceString`）

**實作**

- [ ] `labels` 與 `selectorLabels` 分開，selector 只含不變的標籤
- [ ] 有 checksum annotation 觸發設定變更的滾動更新
- [ ] **沒有使用 `lookup` 或隨機值產生機密**
- [ ] 安全基線內建（非 root、drop ALL、readOnlyRootFilesystem）

**版本**

- [ ] `version` 遵守 SemVer，且對三種等級的意義有定義
- [ ] 有 CHANGELOG
- [ ] 破壞性變更走「並存 → 公告 → 用 `fail` 移除」三步

**ArgoCD 相容**

- [ ] 確認沒有依賴 Release 物件的邏輯
- [ ] 每次渲染結果穩定（不會永遠 OutOfSync）
- [ ] hook 用 ArgoCD 的 annotation 明確表達
- [ ] CRD 獨立管理

**測試**

- [ ] `ci/` 有多組代表性 values
- [ ] CI 跑 lint + template + kubeconform + kube-linter
- [ ] 有 `helm unittest`，含「錯誤訊息是否清楚」的測試

## 常見誤區

| # | 誤區 | 真相 |
| --- | --- | --- |
| 1 | values 欄位越多越彈性 | 每個欄位都是永久承諾；用逃生門取代窮舉 |
| 2 | 直接改 values 欄位名 | 對使用者是破壞性變更，要走過渡期 |
| 3 | 移除欄位就好，反正沒人用 | 設定會被**靜默忽略**，用 `fail` 給明確訊息 |
| 4 | 用 `lookup` 沿用既有 Secret | ArgoCD 底下一律回空，等於每次產生新密碼 |
| 5 | chart 裡產生隨機密碼很方便 | 永遠 OutOfSync，且無法重現 |
| 6 | `labels` 和 `selectorLabels` 可以共用 | selector 不可變，含 version 會讓升級失敗 |
| 7 | 資料庫用 subchart 比較簡單 | 生命週期綁在一起，升級應用會動到資料庫 |
| 8 | 只改 template 不用動 `version` | ArgoCD 靠 version 判斷是否重新渲染 |
| 9 | Helm hook 在 ArgoCD 下行為一樣 | 被轉譯，語意不完全等價 |
| 10 | chart 不需要測試 | 它是所有服務的共同依賴，改壞了全體受影響 |

## 連結

- [[10-helm]] — 正文：Helm 使用、`include` vs `template`、`nindent`、values 覆蓋優先序
- [[37-platform-engineering]] — 附錄 O：內部 chart 作為 golden path 的載體
- [[22-yaml-fields-ecosystem]] — 附錄 C-5：Chart.yaml 全欄位、ArgoCD Application 全欄位
- [[practice-3-gitops-pipeline]] — 實戰 3：ArgoCD 的 hook 與 sync 行為
- [[practice-2-deploy-real-app]] — 實戰 2：chart 該產生的完整 manifest
- [[intro-4-yaml-syntax]] — 入門 4：`1.10` 被當成數字的型別陷阱
- [[k8s-mastery]] — 教材總目錄
