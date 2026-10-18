---
type: concept
domain: tech
tags: [python, fastapi, configuration, pydantic-settings, environment-variables, secrets, kubernetes, configmap]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 09 章：設定與環境 — 讓壞掉的設定進不了叢集

## 一個少了一個字母的災難

某個服務上線後三天，客服回報「有些使用者的訂單不見了」。查下去的結果讓人背脊發涼：訂單**根本沒有進正式資料庫**。

程式碼是這樣寫的：

```python
DATABASE_URL = os.getenv("DATABSE_URL", "sqlite:///./app.db")
#                            ^^^^^^ 少了一個 A
```

環境變數名稱打錯了，`os.getenv` 找不到就安靜地回傳預設值，於是服務連上了容器內的一個 SQLite 檔案。**一切都正常運作**——啟動成功、健康檢查綠燈、寫入成功、查詢得到資料。直到 Pod 因為滾動更新被換掉，那個檔案連同裡面的訂單一起消失。

這個事故的每一個環節都很合理，合起來卻是災難。它暴露了設定管理最根本的問題：

> **設定錯誤最可怕的形式不是啟動失敗，而是靜默地用了錯的值繼續跑。**

這一章的核心目標只有一個：**讓錯誤的設定在程序啟動的那一秒就失敗，而不是在上線三天後**。

---

## 一、設定就是一個 Pydantic model

```powershell
pip install pydantic-settings
```

```python
# app/core/config.py
from functools import lru_cache
from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 沒有預設值 = 必填 = 少了就啟動失敗
    database_url: str
    jwt_secret: SecretStr
    jwt_issuer: str
    jwt_audience: str

    # 有預設值 = 選填
    environment: str = "development"
    log_level: str = "INFO"
    db_pool_size: int = Field(default=10, ge=1, le=100)
    access_token_minutes: int = Field(default=15, ge=1, le=120)
    cors_origins: list[str] = []

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

`BaseSettings` 的行為是：建立實例時，**自動從環境變數尋找同名（不分大小寫）的值**，找不到就往下一個來源找，最後才用預設值。整個過程走的是 Pydantic 的驗證管線——型別轉換、範圍檢查、自訂 validator 全部生效。

對照 ASP.NET Core，這是 `IOptions<T>` 加上 `ValidateOnStart()` 的組合，但更集中：一個類別同時是設定的定義、驗證規則、文件、和型別來源。

比起 `os.getenv` 的四個具體好處：

| | `os.getenv` | `BaseSettings` |
| --- | --- | --- |
| 型別 | 永遠是 `str`，要自己 `int()` | 自動轉換並驗證 |
| 打錯字 | 靜默用預設值（就是開頭那個事故） | 必填欄位缺了就啟動失敗 |
| 全部設定在哪 | 散落在整個專案 | 一個類別看完 |
| IDE 支援 | 沒有 | 補全與型別檢查 |

`SecretStr` 值得特別提：它的 `repr()` 是 `SecretStr('**********')`，所以**不小心把 settings 印進 log 或錯誤訊息時不會洩漏**。要讀實際值得明確呼叫 `.get_secret_value()`——這個小摩擦正是它的價值。

---

## 二、來源優先序

pydantic-settings 的預設查找順序（前面的蓋後面的）：

| 順序 | 來源 | 典型用途 |
| --- | --- | --- |
| 1 | 初始化參數 `Settings(database_url=...)` | 測試 |
| 2 | **環境變數** | K8s、Docker |
| 3 | `.env` 檔 | 本機開發 |
| 4 | secrets 目錄（掛載的檔案） | K8s Secret volume |
| 5 | 欄位預設值 | 合理的預設 |

這和 .NET 那邊 provider 疊層是同一個概念，順序也大致對應。

### 三個實際會踩的地方

**一、複雜型別要用 JSON。**

```python
cors_origins: list[str] = []
```

環境變數是純字串，pydantic-settings 對 `list`／`dict` 這類複雜型別會嘗試 `json.loads`：

```powershell
$env:CORS_ORIGINS='["https://app.example.com","https://admin.example.com"]'
```

寫成逗號分隔的 `https://a.com,https://b.com` 會直接解析失敗。這在 K8s 的 ConfigMap 裡特別容易寫錯，因為 YAML 裡塞一段 JSON 看起來很怪。

想支援逗號分隔就自己處理：

```python
from pydantic import field_validator

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v
```

**二、巢狀設定用雙底線。**

```python
class DatabaseSettings(BaseModel):
    url: str
    pool_size: int = 10

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")
    database: DatabaseSettings
```

對應的環境變數是 `DATABASE__URL`、`DATABASE__POOL_SIZE`。**兩個底線**，不是一個。

分組讓設定變整齊，但也讓環境變數名變長。設定項少於十幾個的話，扁平結構通常更好維護。

**三、`extra` 的預設值會咬人。**

pydantic-settings v2 對 `.env` 檔裡出現的、model 上沒有定義的變數會報錯（預設 `extra="forbid"`）。而 `.env` 檔常常會有一些給其他工具用的變數，於是啟動就失敗。設 `extra="ignore"` 放行。

（環境變數本身不受影響——它只會去找 model 上有的欄位，系統裡上百個無關的環境變數不會有事。）

---

## 三、Fail fast：讓壞設定進不了叢集

這一節是本章的重點。

### 規則一：必填就不要給預設值

回到開頭那個事故。用 `BaseSettings` 之後：

```python
database_url: str          # 沒有預設值
```

環境變數名打錯 → `Settings()` 建立失敗 → **程序啟動就崩潰** → K8s 的 Pod 進入 `CrashLoopBackOff` → 舊版本的 Pod 因為新版沒 ready 而不會被移除 → **滾動更新自動停住，正式環境毫髮無傷**。

這才是我們要的行為。一個永遠不會啟動的 Pod，比一個帶著錯誤設定安靜跑著的 Pod 好上一百倍。

推論是：**任何在不同環境必須不同的設定，都不該有預設值。** 資料庫連線字串、JWT 密鑰、外部服務位址——這些沒有「合理的預設」，給了預設就是給了一條靜默失敗的路。

### 規則二：危險的預設值要主動擋掉

有些設定為了本機方便會給預設，但那個值上正式環境就是漏洞：

```python
    @model_validator(mode="after")
    def check_production_safety(self):
        if self.environment == "production":
            secret = self.jwt_secret.get_secret_value()
            if secret in {"changeme", "dev-secret", ""} or len(secret) < 32:
                raise ValueError("正式環境的 jwt_secret 不可使用預設值或短於 32 字元")
            if "*" in self.cors_origins:
                raise ValueError("正式環境不可使用萬用字元 CORS")
            if self.debug:
                raise ValueError("正式環境不可開啟 debug")
        return self
```

這幾行做的是 .NET 那邊 `ValidateOnStart()` 的事，價值在於**把「上線前檢查清單」變成程式碼**。人會忘記檢查，`ValueError` 不會。

### 規則三：啟動時就建立實例

```python
# app/core/config.py 模組層級
settings = get_settings()
```

模組被 import 時就會建立並驗證。因為 `app/main.py` 一定會 import 它，所以驗證發生在 uvicorn 開始監聽 port **之前**。

如果只在 dependency 裡才第一次呼叫 `get_settings()`，驗證會延遲到第一個請求進來——那時候 Pod 已經 ready、流量已經切過來了，變成 500 而不是啟動失敗。差別很大。

---

## 四、K8s 注入：env 還是 volume

兩種注入方式，差別比想像中大。

### 環境變數

```yaml
envFrom:
  - configMapRef:
      name: myapi-config
  - secretRef:
      name: myapi-secrets
```

或逐項指定：

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: myapi-secrets
        key: database-url
```

**優點**：簡單、pydantic-settings 直接支援、沒有額外程式碼。

**缺點**：**不能熱重載**。環境變數在程序建立的那一刻就固定了，之後改 ConfigMap，K8s 不會（也沒辦法）通知已經在跑的程序。要生效必須重啟 Pod：

```powershell
kubectl rollout restart deployment/myapi
```

### Volume 掛載

```yaml
volumeMounts:
  - name: secrets
    mountPath: /run/secrets
    readOnly: true
volumes:
  - name: secrets
    secret:
      secretName: myapi-secrets
```

pydantic-settings 原生支援讀取這種掛載：

```python
model_config = SettingsConfigDict(secrets_dir="/run/secrets")
```

它會把目錄下的**每個檔案名當成欄位名、檔案內容當成值**。K8s Secret volume 掛出來剛好就是這個結構（每個 key 一個檔案），所以完全不用寫解析程式碼。

**優點**：檔案內容會被 kubelet 自動更新（有延遲，通常一分鐘內），所以**理論上可以熱重載**；而且 volume 掛載的 Secret 不會出現在 `kubectl describe pod` 或子程序的環境裡，洩漏面比較小。

**缺點**：多一層設定；而且「檔案更新了」不等於「應用重新讀了」——你得自己實作重讀邏輯（見第八節）。

### 一張決策表

| 設定類型 | 建議 | 理由 |
| --- | --- | --- |
| 一般設定（log level、pool size） | ConfigMap → env | 簡單，改了重啟即可 |
| 密鑰（DB 密碼、JWT secret） | Secret → **volume** | 不進環境變數，降低洩漏面 |
| 需要不重啟就生效的 | volume + 自行重讀 | 少見，先問是不是真的需要 |

第三列值得多說一句：**「不重啟就生效」在 K8s 環境下通常是偽需求**。滾動更新本來就是零停機的，改設定重啟一次是完全可以接受的成本，而且重啟讓「當前執行中的設定」是可預測的。追求熱重載常常換來的是「不確定這個 Pod 現在用的是哪一版設定」。

---

## 五、Secret 管理

### 基本紀律

**`.env` 永遠不進版控。**

```gitignore
.env
.env.*
!.env.example
```

**提供 `.env.example`** 列出所有需要的變數（值留空或填假值），讓新加入的人知道要設什麼。這份檔案該進版控，而且**每次新增設定項都要同步更新**——它是設定的文件。

**正式環境的密鑰不該有任何人的個人電腦碰得到。** 從 Vault 或 External Secrets Operator 進 K8s Secret，開發者只看得到測試環境的值。

### 密鑰洩漏之後

程式碼裡不小心提交了密鑰，`git rm` 加一個新 commit **完全沒有用**——歷史裡還在，而且如果推到過遠端，就必須假設已經外洩。正確流程：

1. **立刻輪替那把密鑰**（改掉它，讓洩漏的值失效）——這是唯一真正有效的一步
2. 檢查稽核記錄有沒有被使用過
3. 之後才處理 git 歷史（`git filter-repo` 或 BFG）

順序不能顛倒。先花兩小時清歷史再輪替，那兩小時裡密鑰是活的。

**預防**：在 CI 加上 `gitleaks` 或 `detect-secrets` 這類掃描，讓帶密鑰的 commit 根本推不上去。

---

## 六、多環境：同一份程式碼，不同的值

一個常見但有問題的寫法：

```python
# ✗
if settings.environment == "production":
    engine = create_engine(prod_url, pool_size=50)
else:
    engine = create_engine(dev_url, pool_size=5)
```

問題在於**正式環境走的那條路徑，在測試環境從來沒有被執行過**。你測的是另一段程式碼。

正確的做法是讓程式碼只有一條路徑，差異全部在設定值裡：

```python
# ✓
engine = create_engine(settings.database_url, pool_size=settings.db_pool_size)
```

```text
開發：DB_POOL_SIZE=5    正式：DB_POOL_SIZE=30
```

### 真正該依環境分岔的東西

只有少數幾項，而且都在「應用邊界」上：

```python
app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)
```

還有 CORS 來源清單、log 格式（本機用人看得懂的、正式用 JSON）、以及是否啟用 SQL echo。這些的共同特徵是：**它們不影響業務邏輯的執行路徑**。

判準很簡單：**如果分岔會讓「正式環境跑的程式碼」和「測試環境跑的程式碼」不同，那就不該分岔。**

---

## 七、什麼不該放進設定

設定檔容易膨脹成什麼都往裡塞。三類東西該擋在外面：

**一、頻繁變動的業務參數。** 「免運門檻 1000 元」放設定裡，改一次就要重新部署。這種東西該進資料庫或後台管理介面。判準：**改這個值需不需要工程師介入？** 需要就是設定，不需要就該進資料庫。

**二、大量的功能開關。** 少數幾個 boolean 可以，但超過五六個之後，「哪些組合被測過」會變成一個沒人答得出來的問題。需要真正的 feature flag 就用專門的服務。

**三、衍生值。** 能從別的設定算出來的，就用 `computed_field` 或 property 算，不要變成第二個設定項——否則遲早出現兩者不一致：

```python
from pydantic import computed_field

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
```

---

## 八、快取與熱重載

`@lru_cache` 讓 `get_settings()` 整個程序只執行一次（第 03 章）。這是刻意的：設定應該在程序生命週期內**不變**，這樣「這個 Pod 現在用什麼設定」才有確定的答案。

真的需要熱重載時（例如一個常常要調整的閾值），做法是把它從設定裡拿出來，改成一個定期重讀的物件：

```python
class ReloadableConfig:
    def __init__(self, path: Path, ttl: float = 30.0):
        self._path = path
        self._ttl = ttl
        self._value: dict = {}
        self._loaded_at = 0.0

    def get(self) -> dict:
        now = time.monotonic()
        if now - self._loaded_at > self._ttl:
            self._value = json.loads(self._path.read_text(encoding="utf-8"))
            self._loaded_at = now
        return self._value
```

但先問一句：**這個東西真的是設定，還是其實該進資料庫？** 需要隨時調整的值，多半屬於第七節說的第一類。

---

## 九、常見誤解

**「`os.getenv` 加預設值很方便。」**
那正是開頭那個事故的成因。變數名打錯、忘了設、K8s 沒掛上——三種情況都會靜默地用預設值繼續跑。必填設定不該有預設值，讓它在啟動時就失敗。

**「設定驗證失敗會讓服務掛掉，太危險了。」**
反過來想：Pod 起不來的話 K8s 不會把舊版本移除，滾動更新自動停住，正式環境毫髮無傷。而一個帶著錯誤設定安靜跑著的 Pod，會把錯誤資料寫進資料庫。啟動失敗是最安全的失敗方式。

**「改了 ConfigMap 應該就生效了。」**
用 env 注入的話不會。環境變數在程序建立時就固定，K8s 沒辦法改變已存在程序的環境。要重啟 Pod（`kubectl rollout restart`）。用 volume 掛載的話檔案會更新，但應用得自己重讀。

**「`CORS_ORIGINS=https://a.com,https://b.com` 這樣寫就好。」**
複雜型別（`list`、`dict`）從環境變數讀取時走 JSON 解析，要寫成 `["https://a.com","https://b.com"]`。想用逗號分隔得自己加一個 `mode="before"` 的 validator。

**「密鑰不小心進 git 了，改掉並 commit 就好。」**
歷史裡還在，推過遠端就要當作已外洩。**第一步永遠是輪替密鑰**，讓洩漏的值失效；清理 git 歷史是之後的事，順序不能顛倒。

**「用 `if environment == 'production'` 切換行為很直覺。」**
它讓正式環境執行一段從未在測試環境跑過的程式碼。差異應該全部在設定值裡，程式碼只有一條路徑。只有 `/docs` 這種不影響業務邏輯的邊界設定才適合分岔。

---

## 十、同事會來問你的問題

**「設定要怎麼寫才不會出事？」**
用 `BaseSettings` 定義成一個 Pydantic model，必填項不給預設值，模組層級就建立實例（讓驗證發生在監聽 port 之前）。再加一個 `model_validator` 檢查正式環境的危險組合（預設密鑰、萬用字元 CORS、debug 開著）。核心目標是讓錯誤的設定在啟動那一秒就失敗。

**「ConfigMap 用 env 還是 volume？」**
一般設定用 env 簡單；密鑰用 volume 掛載加 `secrets_dir`，因為它不會出現在環境變數、`kubectl describe pod` 或子程序裡，洩漏面比較小。差別最大的是 env 不能熱重載——改了要重啟 Pod，volume 的檔案會自動更新但應用要自己重讀。

**「為什麼我改了 ConfigMap 沒有生效？」**
環境變數在程序建立時就固定了，K8s 改不動已存在的程序。`kubectl rollout restart deployment/xxx`。這不是 bug，而且重啟其實是好事——它讓「這個 Pod 現在用什麼設定」有確定答案。

**「list 型別的設定怎麼從環境變數傳？」**
JSON 字串：`CORS_ORIGINS='["https://a.com","https://b.com"]'`。逗號分隔會解析失敗，要支援的話加一個 `field_validator(mode="before")` 自己 split。巢狀設定則用雙底線 `DATABASE__POOL_SIZE`。

**「密鑰不小心 commit 了怎麼辦？」**
立刻輪替那把密鑰——這是唯一真正有效的一步。然後查稽核記錄有沒有被用過。清 git 歷史排最後，因為推過遠端就要假設已外洩。之後在 CI 加 `gitleaks` 之類的掃描擋住下一次。

**「開發和正式的差異要怎麼處理？」**
全部放在設定值裡，程式碼只有一條路徑。`if environment == "production"` 會讓正式環境跑一段沒被測過的程式碼。唯一適合分岔的是 `/docs` 開關這種不影響業務邏輯的邊界設定。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[08-middleware-and-cross-cutting]] — 上一章：CORS 來源清單的使用端
- [[10-testing]] — 下一章：測試時怎麼覆寫設定
- [[03-dependency-injection]] — `lru_cache` 作為 Singleton 的機制
- [[11-deployment]] — Deployment manifest 的完整寫法
- [[17-configuration-and-secrets]] — ASP.NET Core 的對應章節（provider 疊層與 `ValidateOnStart`）
- [[vault]] — Secret 管理工具
