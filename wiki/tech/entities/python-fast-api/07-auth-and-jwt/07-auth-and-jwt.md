---
type: concept
domain: tech
tags: [python, fastapi, authentication, authorization, jwt, oauth, oidc, security, password-hashing]
sources: []
created: 2026-08-16
updated: 2026-08-16
---

# 第 07 章：認證與授權 — `OAuth2PasswordBearer` 其實沒有在保護你

## 一個假的門鎖

某個專案的管理端點寫成這樣：

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, token: str = Depends(oauth2_scheme)):
    repo.delete(user_id)
    return {"deleted": user_id}
```

看起來很有安全感：有 `OAuth2`、有 `Bearer`、有 `Depends`，`/docs` 上還出現了一個 Authorize 按鈕。所有人都以為這支 endpoint 需要登入才能呼叫。

但這行指令會成功：

```powershell
curl.exe -X DELETE https://api.example.com/admin/users/1 -H "Authorization: Bearer abc"
```

因為 `OAuth2PasswordBearer` **只做兩件事**：從 `Authorization` header 讀出 `Bearer ` 後面那串字，以及讓 `/docs` 產生一個授權介面。它不驗證簽章、不檢查過期、不知道使用者是誰。header 有東西它就放行，內容是 `abc` 也一樣。

這是從 ASP.NET Core 過來最危險的一個認知落差。那邊 `[Authorize]` 加上 `AddJwtBearer()` 就真的完成了驗證——scheme、handler、middleware 都是框架寫好的。**FastAPI 沒有 authentication 系統，一行都沒有。** 你看到的所有東西都是自己用 dependency 拼出來的。

這一章要把整套拼起來：密碼怎麼存、token 怎麼簽、怎麼驗、授權寫在哪一層、以及登出為什麼比想像中難。

---

## 一、三個詞先分清楚

| 詞 | 問的問題 | 失敗時的狀態碼 |
| --- | --- | --- |
| Authentication（認證） | 你是誰？ | 401 |
| Authorization（授權） | 你可以做這件事嗎？ | 403 |
| OAuth 2.0 | 一個**委任授權**的協定，讓 A 服務代表使用者存取 B 服務 | — |

第三個最常被誤用。「用 Google 登入」嚴格說不是 OAuth 而是 **OIDC**（OpenID Connect），它是建在 OAuth 2.0 上的認證層。FastAPI 那些 `OAuth2*` 類別的名字來自 OAuth 規範定義的幾種流程格式，**不代表你在做 OAuth**——用帳號密碼換自家的 JWT，那只是借用了 OAuth 的密碼流程（password flow）格式而已。

這個區分在第八節接 Google 登入時會變得重要。

---

## 二、FastAPI 給了什麼、沒給什麼

| ASP.NET Core | FastAPI |
| --- | --- |
| `AddAuthentication().AddJwtBearer(...)` | **沒有對應**，自己寫 |
| Authentication middleware | **沒有**，用 dependency |
| `[Authorize]` | `dependencies=[Depends(get_current_user)]` |
| `[Authorize(Roles = "Admin")]` | 自訂的 `RequireRole("admin")` dependency |
| `ClaimsPrincipal` / `User.Identity` | 自己回傳的 `User` 物件 |
| `AddAuthorization(policy => ...)` | 自訂 dependency |

`fastapi.security` 裡的那些類別（`OAuth2PasswordBearer`、`HTTPBearer`、`APIKeyHeader`）全部都只是**取值器加上 OpenAPI 的中繼資料**。它們負責從請求的正確位置把憑證字串拿出來，並讓 `/docs` 知道這支 endpoint 需要授權。驗證是你的事。

這個設計有好有壞。好處是完全透明——沒有隱藏的 handler、沒有「為什麼我的 policy 沒生效」這種問題，整條驗證鏈都在你自己寫的三十行程式碼裡。壞處是**漏寫就是漏洞**，而且漏寫不會有任何警告。

所以有一條紀律比什麼都重要：

> **驗證掛在 router 或 app 層級，不要一支一支掛。**

```python
# ✓ 整個 router 都受保護，新增 endpoint 自動繼承
admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(require_admin)],
)

# 需要公開的用另一個 router
public_router = APIRouter(prefix="/public")
```

這對應 .NET 那邊設 `FallbackPolicy` 的理由：讓「忘記加」的預設結果是拒絕而不是放行。

---

## 三、密碼儲存

```python
# app/core/security.py
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()      # 目前是 Argon2

def hash_password(plain: str) -> str:
    return password_hash.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)
```

幾個要點：

**函式庫的選擇。** `passlib` 是十幾年來的標準，但已經長期沒有維護，而且和新版 `bcrypt` 套件有相容性問題（會噴 `module 'bcrypt' has no attribute '__about__'` 這種莫名其妙的錯）。新專案建議用 `pwdlib`（FastAPI 官方文件已改用它）或直接用 `bcrypt` 套件。舊專案沿用 `passlib` 沒問題，但要把 `bcrypt` 版本釘住。

**演算法只有兩個選項：Argon2 或 bcrypt。** 它們刻意設計成計算緩慢，讓暴力破解昂貴。`hashlib.sha256(password)` **不算雜湊密碼**——SHA 是為了快而設計的，現代 GPU 一秒可以試上億次。MD5 更不用說。

**bcrypt 有 72 位元組上限。** 超過的部分會被**靜默截斷**，所以「超長密碼比較安全」在 bcrypt 下不成立。Argon2 沒有這個限制。

**登入失敗的訊息要一致。** 這是常被忽略的一點：

```python
# ✗ 洩漏帳號是否存在
if user is None:
    raise HTTPException(401, "使用者不存在")
if not verify_password(form.password, user.password_hash):
    raise HTTPException(401, "密碼錯誤")

# ✓
if user is None or not verify_password(form.password, user.password_hash):
    raise HTTPException(401, "帳號或密碼錯誤")
```

第一種寫法讓攻擊者可以用登入頁列舉出所有存在的帳號。更講究的話，帳號不存在時也要跑一次假的雜湊比對，避免用回應時間差判斷——因為「查無此人」會比「比對密碼」快很多。

---

## 四、簽發 JWT

用 **PyJWT**（`pip install pyjwt`）。另一個常見的 `python-jose` 也已停止維護，FastAPI 官方文件同樣改用 PyJWT 了。

```python
# app/core/security.py
from datetime import datetime, timedelta, timezone
import uuid
import jwt

def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),                            # 主體，一定要是字串
        "iss": settings.jwt_issuer,                     # 誰簽的
        "aud": settings.jwt_audience,                   # 給誰用的
        "iat": now,                                     # 簽發時間
        "exp": now + timedelta(minutes=15),             # 過期時間
        "jti": str(uuid.uuid4()),                       # 唯一識別，撤銷時會用到
        "roles": user.roles,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
```

登入端點：

```python
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/token")
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = db.scalar(select(User).where(User.email == form.username))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
    }
```

`OAuth2PasswordRequestForm` 收的是 **form data 不是 JSON**，欄位名固定是 `username` 和 `password`（就算你的帳號其實是 email 也叫 `username`）。這是 OAuth 密碼流程的規範，也是讓 `/docs` 的 Authorize 按鈕能運作的條件。不需要相容 `/docs` 的話，用自己的 Pydantic model 收 JSON 也完全可以。

### 四件關於 JWT 本身要知道的事

**一、payload 沒有加密。** JWT 是 `header.payload.signature`，前兩段只是 Base64URL 編碼，任何人貼到 jwt.io 就看得到全部內容。簽章保證的是**沒被竄改**，不是**看不到**。所以 payload 裡絕對不能放密碼、身分證號、完整地址這類資料。

**二、`sub` 要是字串。** JWT 規範要求 `sub` 是字串，PyJWT 較新的版本會對非字串的 `sub` 報錯。`str(user.id)` 別忘了。

**三、放進 token 的資料會過期。** `roles` 寫進 token 之後，管理員把使用者降權，那個人手上的 token 在過期之前仍然帶著舊角色。這是 JWT 無狀態的必然代價，也是**存取 token 的效期要短**（15 分鐘左右）的主要理由。

**四、HS256 還是 RS256。** HS256 是對稱的，簽發與驗證用同一把密鑰——單一服務自己簽自己驗，用它就好。RS256 是非對稱的，私鑰簽、公鑰驗，適合「多個服務都要驗證同一組 token」的情況（那些服務只需要拿到公鑰，拿不到偽造 token 的能力）。

---

## 五、驗證：真正的那道門

```python
# app/api/deps.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

CREDENTIALS_ERROR = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "無法驗證憑證",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],              # ← 必須明確指定，見下方
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            leeway=30,                         # 容忍 30 秒時鐘偏移
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "憑證已過期",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except jwt.InvalidTokenError:
        raise CREDENTIALS_ERROR

    user_id = payload.get("sub")
    if user_id is None:
        raise CREDENTIALS_ERROR

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
```

這三十行才是真正的門鎖。裡面有五個安全關鍵：

**`algorithms=["HS256"]` 是白名單，不能省。** 如果讓函式庫從 token 的 header 自己讀演算法，攻擊者可以把 header 改成 `{"alg": "none"}` 送一個沒有簽章的 token。更陰險的是**演算法混淆**：伺服器用 RS256（公鑰是公開的），攻擊者把 header 改成 HS256 並用**那把公開的公鑰**當 HMAC 密鑰簽一個 token——如果驗證端沒鎖定演算法，它會拿同一把公鑰去驗 HMAC，然後通過。PyJWT 強制要求傳 `algorithms` 參數就是為了防這個。

**`audience` 與 `issuer` 一定要驗。** 沒驗 `aud` 的後果是：另一個服務（甚至 Google）簽發的、格式合法的 token 也能通過你的驗證。第八節會看到這在 Google 登入場景是致命的。

**`leeway` 處理時鐘偏移。** 簽發與驗證在不同機器上時，幾秒的差距就會讓剛簽好的 token 被判定「還沒生效」或「已過期」。ASP.NET Core 預設給 5 分鐘的 `ClockSkew`（其實太寬鬆），PyJWT 預設 0（太嚴格）。30 秒是合理值。

**過期與其他錯誤分開處理。** 前端需要知道「過期了，去 refresh」和「token 根本是壞的，回登入頁」的差別。訊息可以模糊，但至少要能區分。

**最後查一次資料庫。** 這一步讓「停用帳號」立刻生效，代價是每個請求多一次查詢（通常會走主鍵快取，很便宜）。不想查的話就得接受停用要等 token 過期。這是效能與即時性的取捨，多數系統選擇查。

---

## 六、授權：三個層次

### 層次一：需要登入

```python
router = APIRouter(dependencies=[Depends(get_current_user)])
```

### 層次二：角色或權限

```python
class RequireRole:
    def __init__(self, *roles: str):
        self.roles = set(roles)

    def __call__(self, user: CurrentUser) -> User:
        if not self.roles & set(user.roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "權限不足")
        return user

admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(RequireRole("admin", "superuser"))],
)
```

這對應 `[Authorize(Roles = "Admin")]`。想做得更細一點就把 `roles` 換成 `permissions`（`order:write`、`user:delete`），角色只是權限的集合——這個模型在權限開始變複雜時比較撐得住。

### 層次三：資源層級

「這張訂單是不是你的」這種問題，**dependency 回答不了**，因為它需要先把資源查出來：

```python
@router.delete("/orders/{order_id}", status_code=204)
def cancel_order(order_id: int, user: CurrentUser, db: DbSession):
    order = db.get(Order, order_id)
    if order is None or order.owner_id != user.id:
        raise HTTPException(404)          # 注意是 404 不是 403
    order_service.cancel(db, order)
```

兩個要點。一是**回 404 不是 403**——回 403 等於告訴對方「這張訂單存在」，那本身就是洩漏（第 06 章的決策表）。二是多租戶系統應該讓這件事**結構性地不可能出錯**：把租戶條件寫進查詢本身，而不是查出來再比對。

```python
def get_owned_order(order_id: int, user: CurrentUser, db: DbSession) -> Order:
    stmt = select(Order).where(Order.id == order_id, Order.owner_id == user.id)
    order = db.scalars(stmt).first()
    if order is None:
        raise HTTPException(404)
    return order

OwnedOrder = Annotated[Order, Depends(get_owned_order)]
```

現在它可以當 dependency 用了，而且**忘記加租戶條件變成不可能**——因為根本沒有另一條路徑可以拿到 `Order`。這比「記得每次都要檢查」可靠得多。

---

## 七、登出，以及為什麼它比想像中難

JWT 是無狀態的：伺服器不記得自己簽過哪些 token，驗證完全靠簽章與 `exp`。這帶來一個直接後果：

> **伺服器沒有辦法「取消」一個已經簽出去的 JWT。**

前端把 token 從 localStorage 刪掉叫做「本地登出」，但那串字如果被複製走了，在過期之前仍然完全有效。四個處理方向：

| 方案 | 做法 | 代價 |
| --- | --- | --- |
| **短效期 + refresh token** | access token 15 分鐘，refresh token 存資料庫可撤銷 | 多一套流程；**這是標準答案** |
| 黑名單 | 登出時把 `jti` 寫進 Redis，驗證時查一次 | 每個請求多一次 Redis 查詢；失去部分無狀態優勢 |
| token 版本號 | 使用者資料表加 `token_version`，寫進 payload，改密碼時 +1 | 只能全域登出，不能單裝置；反正已經在查資料庫了，成本低 |
| 改用 session | 不用 JWT，用伺服器端 session | 需要共享儲存；但登出、撤銷、變更權限全部立即生效 |

最後一列值得認真考慮。**如果你的系統只有一個後端、前後端同源，session + httpOnly cookie 往往是更簡單且更安全的選擇。** JWT 的優勢在跨服務、跨網域、無狀態擴展；如果沒有這些需求，你付了複雜度卻沒拿到好處。

### refresh token 的兩條紀律

```python
@router.post("/refresh")
def refresh(payload: RefreshIn, db: DbSession):
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token == payload.refresh_token))
    if stored is None or stored.revoked or stored.expires_at < now():
        raise HTTPException(401, "refresh token 無效")

    if stored.used_at is not None:                      # 重用偵測
        revoke_all_for_user(db, stored.user_id)         # 整條鏈作廢
        raise HTTPException(401, "偵測到憑證重用，已登出所有裝置")

    stored.used_at = now()
    new_refresh = issue_refresh_token(db, stored.user_id)   # 輪替
    db.commit()
    return {"access_token": create_access_token(stored.user), "refresh_token": new_refresh}
```

**輪替**：每次使用就換一個新的，舊的作廢。**重用偵測**：如果一個已經用過的 refresh token 又被拿來用，代表它被複製了——這時把該使用者的所有 refresh token 全部作廢，強制重新登入。

這兩條是 OAuth 2.1 對公開客戶端（瀏覽器、行動 App）的建議做法，實作成本不高但擋掉的攻擊面很大。

---

## 八、Google 登入（OIDC）

前後端分離下的流程比想像中單純，因為授權碼那一段由 Google 的前端 SDK 處理掉了：

```text
1. 前端用 Google SDK 完成登入，拿到一個 id_token（那是一個 JWT）
2. 前端把 id_token POST 給你的後端
3. 後端驗證這個 id_token（下面這段）
4. 後端簽發自己的 access token 回去
5. 之後的所有 API 呼叫都用你自己的 token，Google 不再參與
```

第 3 步是唯一有資安風險的地方：

```python
import jwt

GOOGLE_JWKS = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs", cache_keys=True)

def verify_google_id_token(id_token: str) -> dict:
    signing_key = GOOGLE_JWKS.get_signing_key_from_jwt(id_token)
    claims = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.google_client_id,          # ← 資安關鍵
        issuer=["https://accounts.google.com", "accounts.google.com"],
    )
    if not claims.get("email_verified"):
        raise HTTPException(401, "Google 帳號的 email 未驗證")
    return claims
```

**`audience` 這一行是整段最重要的。** 沒有它的話：任何人都可以去申請自己的 Google 應用程式、拿一個由 Google 正確簽發的 `id_token`（簽章完全合法、`iss` 也是 Google）、送到你的後端——然後就登入了任何人的帳號。`aud` 是唯一能證明「這個 token 是發給**我這個應用**」的欄位。

其他三個細節：`PyJWKClient` 會快取 Google 的公鑰，不要每次請求都去抓；Google 的 `iss` 有兩種寫法都合法，要都接受；`email_verified` 要檢查，否則有人可以用未驗證的 email 冒充別人的帳號。

拿到 claims 之後，用 `sub`（Google 的使用者唯一 id，不是 email——email 是可以變的）去對應或建立你自己的使用者記錄。

---

## 九、前端該把 token 放哪

這個問題會被問到，先講結論：**沒有完美解，只有取捨。**

| 位置 | 怕什麼 | 說明 |
| --- | --- | --- |
| `localStorage` | **XSS** | 任何注入的腳本都讀得到 |
| 記憶體（JS 變數） | 重新整理就消失 | 配合 refresh token 可以接受 |
| httpOnly cookie | **CSRF** | JS 讀不到（防 XSS 竊取），但瀏覽器會自動附帶 |

httpOnly cookie 加上 `SameSite=Lax`（或 `Strict`）已經能擋掉絕大多數 CSRF，同時免疫於 XSS 竊取 token，所以**同源部署的情況下它通常是比較好的選擇**。跨網域（前端在 CDN、後端在另一個網域）的話 cookie 會複雜很多，那時 `localStorage` 加上嚴格的 CSP 是務實的折衷。

無論選哪個，**存取 token 的效期短**都是最有效的一道防線。

---

## 十、常見誤解

**「加了 `Depends(oauth2_scheme)` 就有認證了。」**
沒有。它只從 header 取出字串並產生 `/docs` 的授權介面，內容是 `abc` 也照樣放行。真正的驗證是你自己寫的那個 `get_current_user`。

**「JWT 是加密的，放個人資料沒關係。」**
payload 只是 Base64 編碼，貼到 jwt.io 就看得到。簽章保證的是完整性不是機密性。

**「登出 API 呼叫成功，token 就失效了。」**
不會。JWT 無狀態，伺服器記不得簽過什麼。要真的失效需要黑名單、token 版本號，或改用 session。前端刪掉 token 只是本地登出。

**「`decode` 的時候 `algorithms` 可以不傳，函式庫會自己看 header。」**
那正是 `alg:none` 與演算法混淆攻擊的入口。PyJWT 強制要求這個參數就是為了防它。**永遠明確指定白名單。**

**「驗了簽章和過期就夠了。」**
還要驗 `aud` 和 `iss`。少了 `aud`，別的應用（甚至 Google）簽發的合法 token 也能通過你的驗證——在 Google 登入場景這等於任何人都能登入任何帳號。

**「`[Authorize]` 在 FastAPI 的對應是什麼？我找不到。」**
沒有對應，要自己拼。所以把驗證掛在 router 或 app 層級（`dependencies=[...]`），讓「忘記加」的預設結果是拒絕而不是放行。

**「用 `hashlib.sha256` 存密碼，有雜湊就安全了。」**
SHA 是為了快而設計的，GPU 一秒可試上億次。密碼要用刻意緩慢的 Argon2 或 bcrypt。另外 bcrypt 有 72 位元組上限，超過會被靜默截斷。

---

## 十一、同事會來問你的問題

**「FastAPI 的認證怎麼做？」**
自己寫。`fastapi.security` 那些類別只負責從請求裡取出憑證字串加上產生 `/docs` 的介面，驗證是一個你自己寫的 dependency：解碼 JWT（鎖定演算法、驗 `aud`/`iss`、給 leeway）、查資料庫確認使用者還存在且啟用、回傳 `User`。然後把它掛在 router 層級而不是一支一支掛。

**「HS256 還是 RS256？」**
單一服務自簽自驗用 HS256，簡單。多個服務都要驗同一組 token 用 RS256——它們只需要公鑰，拿不到偽造能力。用 RS256 時特別要鎖定 `algorithms=["RS256"]`，否則有演算法混淆的風險（用公開的公鑰當 HMAC 密鑰偽造）。

**「怎麼做登出？」**
JWT 本身做不到。標準答案是存取 token 效期做短（15 分鐘）＋ refresh token 存資料庫可撤銷，並實作輪替與重用偵測。如果系統只有一個後端且前後端同源，認真考慮直接用 session + httpOnly cookie——登出、撤銷、改權限全部立即生效，複雜度反而更低。

**「權限檢查要寫在哪一層？」**
分三層。要不要登入、有沒有某個角色，用 dependency 掛在 router 上。「這筆資料是不是你的」不行——那需要先查資源。這種情況把租戶條件寫進查詢本身並包成 dependency，讓「忘記檢查」在結構上不可能發生，而不是靠人記得。

**「Google 登入怎麼接？」**
前端拿 `id_token` 給後端，後端用 `PyJWKClient` 抓 Google 公鑰驗簽，**`audience` 必須設成你自己的 client_id**（少了這一行，任何人用自己的 Google 應用簽的合法 token 都能登入任何帳號），`iss` 兩種寫法都要接受，`email_verified` 要檢查。驗過之後簽發你自己的 token，後續 Google 不再參與。用 `sub` 對應使用者，不要用 email。

**「token 該存哪？」**
同源部署用 httpOnly cookie + `SameSite=Lax`，它免疫於 XSS 竊取且擋掉多數 CSRF。跨網域的話 `localStorage` 加嚴格 CSP 是務實折衷。不管選哪個，短效期的存取 token 都是最有效的一層防護。

---

## 連結

- [[python-fast-api]] — 教材總目錄
- [[06-error-handling]] — 上一章：401/403 的狀態碼決策
- [[08-middleware-and-cross-cutting]] — 下一章：CORS 與 cookie 的跨網域設定
- [[09-configuration]] — jwt_secret 該怎麼注入
- [[11-authentication]] — ASP.NET Core 的對應章節（scheme 與 handler）
- [[12-jwt-deep-dive]] — .NET 那邊的 JWT 專章，同一組攻擊面
- [[13-oauth-oidc]] — .NET 那邊的 Google 登入流程
