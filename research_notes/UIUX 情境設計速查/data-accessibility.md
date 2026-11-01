# Data, Mobile, Accessibility and AI Research

查證日期：2026-10-30。以下是速查書的研究素材，非市占排名。所有「推論」都是依據任務需求整理的綜合設計建議，例子為原創；並非所列設計系統逐字提出的規定。正式書稿應保留標準、平台建議、情境建議的區別。

## Data Tables and Dashboards

### Takeaway

資料密集介面應以「找到、比較、處理資料」為核心；一般 table 與 spreadsheet 型 grid 的鍵盤模型不可混用。

### Cited Findings

- 【事實】Carbon 的 data table 提供 sorting、expandable rows、batch actions 與 toolbar；定位不是完整 spreadsheet。查證頁最後更新 2026-09-30。[Carbon Data table](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines)
- 【事實】APG 建議能用原生 HTML table 時優先使用；table 本身不是互動 widget，內部 link/button 各自進入 Tab 順序。[APG Table](https://www.w3.org/WAI/ARIA/apg/patterns/table/)
- 【事實】grid 是 composite widget，通常只有一個內部元素進入頁面 Tab 順序，作者必須實作內部方向鍵移動與 focus 管理。[APG Grid](https://www.w3.org/WAI/ARIA/apg/patterns/grid/)
- 【事實】Carbon 建議 bar/area 等以大小或部分整體比較的圖表從零起算；line/scatter 為揭露變化可使用非零起點。缺資料與軸標籤都應明示。[Carbon Axes and labels](https://www.carbondesignsystem.com/building-blocks/data-visualization/axes-and-labels)

### Inferences

以下 D01–D25 為【推論／綜合建議】，不是 WCAG 硬性規定。D01–D10 參照上述 Carbon table 與 APG；D11–D25 為資料分析任務的原創情境推導。

| ID | 當……時，就應該…… | 好例子／壞例子 | 邊界 |
|---|---|---|---|
| D01 | 當使用者需要逐欄比較相同屬性時，就應該優先用 table。 | 好：訂單、金額、狀態各一欄；壞：每張訂單卡片資訊順序不同。 | 圖像探索為主時可用卡片。 |
| D02 | 當只是讀資料並偶爾開詳情時，就應該先用原生 table 加真實 link/button。 | 好：訂單編號是 link；壞：每個 td 都加 tabindex。 | spreadsheet 式編輯另選完整 grid。 |
| D03 | 當必須做 cell 編輯與方向鍵巡覽時，就應該採完整 grid 模型。 | 好：方向鍵換格、明確進出編輯；壞：只加 role=grid 卻沒有鍵盤行為。 | grid 成本高，不為樣式使用。 |
| D04 | 當整列可點擊開詳情時，就應該仍提供可用鍵盤操作的明確入口。 | 好：名稱 link，點空白處也可開啟；壞：tr 只有 onclick。 | 列內 checkbox/menu 不得誤觸導航。 |
| D05 | 當欄位可排序時，就應該顯示目前排序方向並讓控制項可操作。 | 好：「金額，降冪」；壞：表頭只有滑鼠 hover 才出現箭頭。 | 多欄排序需另顯示優先序。 |
| D06 | 當使用者選多列時，就應該切換成清楚的批次操作上下文。 | 好：「已選 6 筆，封存」；壞：同時保留易混淆的單列刪除。 | 禁止操作應解釋限制。 |
| D07 | 當有跨頁全選時，就應該明寫選取範圍。 | 好：「本頁 20 筆」與「全部符合條件 843 筆」分開；壞：「全選」不知道選了多少。 | 資料變動時需重新確認範圍。 |
| D08 | 當批次操作部分失敗時，就應該分列成功、失敗與可重試項。 | 好：「8 筆成功，2 筆權限不足」；壞：只顯示失敗並讓人重做全部。 | 重試需避免重複副作用。 |
| D09 | 當欄位太多時，就應該先保留任務必需欄位並提供次要資訊入口。 | 好：狀態與金額常駐、備註展開；壞：為塞全部把字縮成 10px。 | 對照分析可保留橫向捲動。 |
| D10 | 當某列可展開時，就應該用獨立展開控制並說明狀態。 | 好：展開明細按鈕；壞：點任何格都忽然展開。 | 展開內容太長時改詳情頁。 |
| D11 | 當使用者要返回剛才的位置時，就應該保留 filter、sort、page 與 scroll。 | 好：開詳情後返回同一列；壞：每次回到第 1 頁。 | 新工作階段可依需求重置。 |
| D12 | 當工作需要可定位與可分享時，就應該優先分頁並保存查詢狀態。 | 好：同事打開同一查詢條件；壞：只能一路無限下滑找第 300 筆。 | 探索 feed 可使用 infinite scroll。 |
| D13 | 當要用 infinite scroll 時，就應該設計返回位置與可抵達的頁尾。 | 好：載入更多與返回位置；壞：頁尾永遠被新資料推走。 | 不必為少量固定資料使用。 |
| D14 | 當金額或數量要跨列比較時，就應該對齊數字、統一精度並顯示單位。 | 好：「NT$」欄名與一致小數位；壞：100、100.0、1百混在同欄。 | ID 不是數量，不作數值格式化。 |
| D15 | 當資料是缺值時，就應該區分缺值、零與不適用。 | 好：「未提供」「0」「不適用」；壞：全部填 0。 | 短橫線要有圖例。 |
| D16 | 當資料持續更新時，就應該顯示更新時間與刷新狀態。 | 好：「10:32 更新，刷新中」；壞：過期資料看起來像即時。 | 高頻 feed 可聚合時間提示。 |
| D17 | 當更新可能打斷選取或閱讀時，就應該暫存新資料並讓使用者套用。 | 好：「有 12 筆新結果」；壞：滑鼠快點到某列時突然重排。 | 緊急監控可明確定義自動刷新。 |
| D18 | 當 dashboard 服務特定角色時，就應該先顯示他能採取行動的指標。 | 好：客服看待處理與逾時；壞：所有人都看營收大字。 | 管理摘要與作業介面可分開。 |
| D19 | 當指標顯示成長率時，就應該標明比較基期與時間範圍。 | 好：「本週比上週 +8%」；壞：只有綠色 +8%。 | 缺同期資料不得假算。 |
| D20 | 當圖表需要比較類別大小時，就應該優先採容易比較長度的位置編碼。 | 好：橫向 bar 顯示各店銷量；壞：十幾塊 3D pie。 | 真正部分整體且類別少可用 pie。 |
| D21 | 當要呈現時間趨勢時，就應該用連續時間軸並明示缺口。 | 好：沒回報的日期留 gap；壞：把無資料當成零。 | 插值必須標明。 |
| D22 | 當 bar 長度代表數值大小時，就應該從零起算。 | 好：92 與 95 差距不誇大；壞：y 軸從 90 起看似成長數倍。 | line chart 可非零，但標清刻度。 |
| D23 | 當圖表必須讀精確數字時，就應該同時提供可讀的資料表或數值摘要。 | 好：圖下有資料表切換；壞：只能 hover 小點讀值。 | 摘要可依任務聚合，不一定列全部原始點。 |
| D24 | 當系列太多難以辨識時，就應該允許篩選或拆成 small multiples。 | 好：分店分圖同尺度；壞：二十條相近色折線。 | 不同尺度要醒目標示。 |
| D25 | 當某圖表能進一步查原因時，就應該保留 drill-down 的上下文。 | 好：點週異常後看該週明細；壞：跳到沒 filter 的總表。 | drill-down 入口應可鍵盤操作。 |

### Gaps

- 【未查到】未尋得可證明「全產業主流市占」的公開資料，因此不能將上述模式描述為統計排名。
- 【未查到】不存在已查證的「超過 N 列一律 pagination」通用閾值；應以任務、效能與返回需求決定。

## Accessibility and Mobile

### Takeaway

WCAG 2.2 的 A/AA/AAA 是不同門檻；Apple pt、Android dp 與 Web CSS px 是不同語境的單位，不應混成一個像素規則。

### Cited Findings

- 【事實】SC 2.5.8 AA：pointer target 至少 24×24 CSS px，或符合 spacing、equivalent、inline、user-agent、essential 例外。spacing 是以小 target 中心的直徑 24 CSS px 圓檢查不與其他 target／小 target 的同類圓相交，並非「間距固定 24px」。[Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- 【事實】SC 2.5.5 AAA：44×44 CSS px；有 equivalent、inline、user-agent、essential 例外，並無前項相同的 spacing 例外。[Target Size Enhanced](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html)
- 【事實】Apple buttons 建議一般 hit region 至少 44×44 pt，visionOS 為 60×60 pt；Android 建議至少 48×48 dp。這些是平台建議，不是 Web AA 的直接換算。[Apple Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons?changes=latest_1)；[Android Accessibility](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views?hl=en)
- 【事實】SC 1.4.3 AA：一般文字至少 4.5:1，大字至少 3:1；大字門檻為 18pt regular 或 14pt bold（或等效），不是任意標題。inactive、純裝飾、logotype 等有例外。[Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- 【事實】SC 1.4.11 AA：辨識控制項及狀態所需的視覺資訊、理解圖像所需部分，對相鄰色至少 3:1；有 inactive／未修改 UA 外觀／essential 例外，不是每條裝飾線都要 3:1。[Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- 【事實】SC 1.4.10 AA：縱向內容在 320 CSS px 等效寬度、橫向內容在 256 CSS px 等效高度，不應需要雙向捲動；需二維布局才能使用／理解的局部內容有例外。[Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
- 【事實】SC 2.1.1 A 要求鍵盤操作，底層功能依賴運動路徑的例外不等於「所有 drag 都例外」。[Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html)
- 【事實】SC 2.4.7 AA 要求可見鍵盤 focus；SC 2.4.11 AA 要求 focus 元件不被作者內容完全遮住，完全不遮住屬更高要求。[Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)；[Focus Not Obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)
- 【事實】SC 2.5.7 AA 的 drag 功能需單 pointer 不拖曳替代，除 essential／未修改 UA 功能；只提供鍵盤替代不足以滿足此條。[Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
- 【事實】SC 2.5.1 A 要求非必要的 multipoint／path-based gesture 有單 pointer、非路徑式替代。[Pointer Gestures](https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures.html)
- 【事實】SC 1.3.4 AA 不得強制單一螢幕方向，除方向對功能必要。[Orientation](https://www.w3.org/WAI/WCAG22/Understanding/orientation.html)
- 【事實】SC 2.3.3 AAA：互動引發的非必要 motion animation 可關閉；不要誤寫成全部動畫均屬 AA。[Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
- 【事實】SC 1.4.1 A 不以顏色作唯一視覺資訊；SC 4.1.3 AA 的 status messages 要能由輔助科技在不取得 focus 下辨識。[Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)；[Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
- 【事實】SC 3.3.8 AA 的認證過程不應強制認知測驗，除提供替代／協助機制／物件辨識／個人內容例外；password manager 與 copy/paste 是協助機制例。[Accessible Authentication](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html)

### Inferences

以下 A01–A35 的動作是【推論／原創落地建議】，其標準依據對照上方同名來源。數字是標準時明寫層級；超出門檻的建議不可宣稱為規範全文。

| ID | 當……時，就應該…… | 好例子／壞例子 | 邊界 |
|---|---|---|---|
| A01 | 當 Web 以 WCAG 2.2 AA 為目標時，就應該依 24×24 CSS px 與完整例外檢查 target。 | 好：檢查實際可點範圍；壞：只量 icon 圖片尺寸。 | 不代表 24px 就是最佳觸控尺寸。 |
| A02 | 當主要操作會用手指進行時，就應該採較寬裕 target 並按平台單位設計。 | 好：iOS 44pt、Android 48dp 的平台設計；壞：跨平台寫「全部 44 實體像素」。 | Web 可自訂較高目標，不假稱 AA 強制。 |
| A03 | 當 icon 視覺上需小巧時，就應該擴大 hit region 而非只放大圖案。 | 好：小叉號置於大按鈕；壞：兩個隱形 hit region 重疊。 | 擴大後需檢查相鄰操作。 |
| A04 | 當 target 小於門檻而採 spacing 例外時，就應該檢查幾何條件。 | 好：依中心圓檢查相鄰 target；壞：一律加 4px 就說合規。 | AAA 44px 沒有相同 spacing 例外。 |
| A05 | 當正文使用淺灰色時，就應該量測文字與實際底色對比。 | 好：一般字達 4.5:1；壞：只憑螢幕看起來清楚。 | inactive/裝飾例外不應拿來包裝重要資訊。 |
| A06 | 當用大字 3:1 門檻時，就應該核對字級與字重。 | 好：24 CSS px regular 作等效參考；壞：16px bold 就當大字。 | 字體等效與非拉丁字需保守判斷。 |
| A07 | 當邊框是辨識輸入框的唯一線索時，就應該確保必要線索對比足夠。 | 好：必要邊框對相鄰底色達 3:1；壞：所有框只剩近白細線。 | 若其他可見線索已充分辨識，不必每條裝飾線都量。 |
| A08 | 當狀態以顏色顯示時，就應該再加文字、形狀或 icon。 | 好：「失敗」加警示符號；壞：紅點與綠點沒有說明。 | 裝飾性色彩不必硬加標籤。 |
| A09 | 當圖表靠色彩分系列時，就應該加直接標籤或可辨線型。 | 好：實線／虛線配系列名稱；壞：只說「看紅線」。 | 太多線型時改篩選或分圖。 |
| A10 | 當使用者只用鍵盤時，就應該能完成同一核心任務。 | 好：Tab 到操作、Enter 執行；壞：只有 hover 才出現入口。 | 自由手繪路徑屬特殊情境。 |
| A11 | 當客製按鈕樣式時，就應該保留清楚且持續的 focus indicator。 | 好：focus-visible 外框；壞：outline:none 無替代。 | 不必強迫所有滑鼠點擊都同樣呈現。 |
| A12 | 當有 sticky header/footer 時，就應該讓 focus 元件可被看見。 | 好：聚焦時滾到工具列之外；壞：按鈕整個藏在底部 banner 下。 | AA 最低為不完全遮擋，設計上宜完全可見。 |
| A13 | 當畫面重排到小寬度時，就應該仍能讀取及操作。 | 好：320 CSS px 寬單欄表單；壞：整頁固定 1200px。 | 表格／地圖等必要二維區塊可局部橫捲。 |
| A14 | 當表格需要橫捲時，就應該把橫捲限制在表格容器。 | 好：頁面正文重排，表格獨立捲；壞：整頁連標題一起超寬。 | 仍需讓容器可鍵盤使用及可發現。 |
| A15 | 當使用者放大文字時，就應該允許換行與高度增長。 | 好：兩行按鈕文字不裁切；壞：固定高度把下半字切掉。 | icon-only 仍要可理解名稱。 |
| A16 | 當有拖曳排序時，就應該另外提供點選式移動。 | 好：「移到上一位／指定位置」；壞：只給鍵盤快捷鍵而無 pointer 替代。 | 拖曳本質必要者另評估例外。 |
| A17 | 當用 pinch 或 swipe 操作時，就應該也有單點控制。 | 好：地圖加減縮放；壞：只能雙指縮放。 | OS 自身手勢與頁面自訂手勢分開。 |
| A18 | 當手機橫放時，就應該保持服務可用。 | 好：內容重排；壞：蓋上「請轉直」阻擋頁。 | 方向對功能本質必要才例外。 |
| A19 | 當非必要動畫可能造成不適時，就應該尊重 reduced motion。 | 好：滑動改為淡入或直接切換；壞：設定減少動態仍強制 parallax。 | 保留必要狀態回饋，非一律消除全部變化。 |
| A20 | 當資料更新但不需要轉移注意力時，就應該提供可讀的 status announcement。 | 好：結果數以 polite status 更新；壞：每次搜尋把 focus 搶到頁頂。 | 真正要處理的錯誤可採不同焦點策略。 |
| A21 | 當訊息更新很頻繁時，就應該合併公告。 | 好：一次告知「已載入 20 筆」；壞：每列新增都朗讀。 | 緊急警報不能因合併而漏掉。 |
| A22 | 當使用 icon-only button 時，就應該有與動作一致的 accessible name。 | 好：「刪除訂單 A102」；壞：「垃圾桶」。 | 可見文字與名稱應一致包含關鍵詞。 |
| A23 | 當列表重複出現相同操作時，就應該讓輔助科技能分辨作用對象。 | 好：「編輯 王小明」；壞：一連串無上下文的「編輯」。 | 避免把整列所有文字都塞入名稱。 |
| A24 | 當圖片只做裝飾時，就應該避免重複朗讀。 | 好：裝飾圖從可及性樹排除；壞：每個裝飾箭頭都讀一遍。 | 傳達資料的圖不能當裝飾。 |
| A25 | 當使用者登入時，就應該允許 password manager 與貼上。 | 好：自動填入與貼上 OTP；壞：禁止 paste 逼人記住驗證碼。 | 安全需求應靠適當認證流程處理。 |
| A26 | 當 OTP 分成多格時，就應該支援整串貼上並維持可預期 focus。 | 好：貼上六碼自動分配；壞：每格都阻止貼上或跳焦。 | 單欄輸入通常較簡單。 |
| A27 | 當手機鍵盤展開時，就應該仍看得到正在編輯的欄位與錯誤。 | 好：表單可捲到當前欄；壞：固定底部 CTA 蓋住輸入。 | 以實機測試各鍵盤類型。 |
| A28 | 當文字很長或翻譯後變長時，就應該讓布局容納內容。 | 好：標籤換行；壞：把「刪除帳號」截成「刪除…」。 | 技術識別碼可提供完整查看／複製。 |
| A29 | 當行動版把側欄收進 drawer 時，就應該保留目前位置與關閉入口。 | 好：當前頁高亮、可返回內容；壞：開了選單找不到退出。 | 是否 modal 決定 focus 管理，不只看外觀。 |
| A30 | 當重要操作只放 hover 時，就應該增加可點或常駐替代。 | 好：更多選單常駐；壞：touch 使用者永遠看不到刪除。 | 桌面可額外提供 hover 捷徑。 |
| A31 | 當手機有瀏海或底部手勢區時，就應該留出安全區域。 | 好：底部操作在 safe area 之上；壞：確認鍵與 home gesture 重疊。 | 背景可延伸，互動內容需可達。 |
| A32 | 當功能含 swipe-to-delete 時，就應該提供可發現的操作入口與復原。 | 好：更多選單也有刪除；壞：只有隱藏手勢。 | 不可復原時先確認後果。 |
| A33 | 當資料密集畫面縮到手機時，就應該重新決定資訊優先序。 | 好：主要欄位＋詳情展開；壞：把桌面十欄直接縮小。 | 比較任務可保留局部 table。 |
| A34 | 當互動被動畫或背景遮擋時，就應該先保障可操作與可辨識。 | 好：內容層有穩定底色；壞：玻璃透明層隨背景變得讀不到。 | 視覺效果可用在非關鍵區。 |
| A35 | 當需要確認 accessibility 是否通過時，就應該實測完整任務。 | 好：鍵盤完成建立、修改、錯誤恢復；壞：只截圖看顏色。 | 還需按目標標準完整評估，幾項檢查不等於合規。 |

### Gaps

- 【未查到】未主張完成完整 WCAG conformance 稽核；本筆記只涵蓋最常見設計決策。
- Apple 無 query 的頁面需 JS；本次 44pt／60pt 文字取自工具可讀的同官方頁 query 版本。不要把 visionOS 60pt 擴大為所有 Apple 平台。

## AI, Design Systems and Validation

### Takeaway

AI 介面需讓使用者知道現在在生成什麼、能否相信、是否已執行、如何更正；design system 則需要把這些行為和狀態一起固定，而非只固定顏色。

### Cited Findings

- 【事實】Microsoft 2019 Human-AI Guidelines 強調能力與可靠度預期、讓使用者容易呼叫／忽略／更正、遇到不確定時縮限服務、提供控制與回饋。[Microsoft Human-AI Guidelines](https://www.microsoft.com/en-us/research/articles/guidelines-for-human-ai-interaction-eighteen-best-practices-for-human-centered-ai-design/)
- 【事實】Fluent Responsible AI 包括標示 AI、說明能力與資料範圍、驗證來源、避免過度依賴、保持使用者控制與蒐集回饋。[Fluent Responsible AI](https://fluent2.microsoft.design/responsible-AI)
- 【事實】Carbon color tokens 依角色與元件使用方式分組，提供不同 theme 下的值。查證頁最後更新 2026-09-25。[Carbon Color Tokens](https://www.carbondesignsystem.com/building-blocks/foundations/color/tokens)
- 【事實】WAI 建議開發早期與全程評估；沒有單一工具能獨自判定網站是否符合 accessibility 標準，需要人工評估。[WAI Evaluation](https://www.w3.org/WAI/test-evaluate/)

### Inferences

以下 X01–X30 全部為【推論／綜合建議】。X01–X15 以 AI guidelines 原則推導產品情境，並非逐項直接引述；X16–X30 是可測試的工作方法與誠實介面建議。

| ID | 當……時，就應該…… | 好例子／壞例子 | 邊界 |
|---|---|---|---|
| X01 | 當內容由 AI 生成時，就應該在相關位置標示來源性質。 | 好：「AI 草稿」；壞：裝成人類專家已審核。 | 不必每個字都貼標籤。 |
| X02 | 當 AI 能做的任務有限時，就應該用具體例子說明範圍。 | 好：「摘要此文件」；壞：「問任何事都能準確回答」。 | 能力隨方案不同需同步更新。 |
| X03 | 當 AI 回答依賴來源時，就應該讓人打開對應來源核對。 | 好：主張旁有支援段落入口；壞：列一堆不支援結論的連結。 | 沒查到來源要明說。 |
| X04 | 當模型信心未經校準時，就應該用限制與證據說明不確定性。 | 好：「缺少本季資料」；壞：隨意顯示「可信度 97%」。 | 只有經驗證的量化指標才顯示。 |
| X05 | 當內容正在 streaming 時，就應該區分生成中與完成。 | 好：「生成中」並提供停止；壞：游標停止就當完成但其實失敗。 | 停止不代表撤銷已執行外部動作。 |
| X06 | 當 streaming 被中斷時，就應該保留已產生內容並提供重試。 | 好：「連線中斷，保留草稿」；壞：整段消失。 | 不可把半段結果標成已完成。 |
| X07 | 當新內容持續流入時，就應該尊重使用者正在閱讀的位置。 | 好：使用者捲上去後顯示「跳到最新」；壞：每個 token 強制捲到底。 | 使用者停留底部可自動跟隨。 |
| X08 | 當 AI 要修改文件時，就應該提供修改範圍與可審查結果。 | 好：顯示差異、接受或復原；壞：無提示覆蓋原文。 | 小型可逆修正可依已授權範圍直接完成。 |
| X09 | 當 AI 要做有外部副作用的動作時，就應該在執行前顯示對象與後果。 | 好：寄出前列收件人、內容、附件；壞：「我處理好了」才揭露已寄信。 | 已有明確持續授權時避免重複確認。 |
| X10 | 當 AI 只產生建議而未執行時，就應該用狀態文案清楚區隔。 | 好：「草稿已準備，尚未送出」；壞：「完成」讓人以為已生效。 | 完成標籤需與產品實際狀態一致。 |
| X11 | 當 AI 理解錯誤時，就應該讓人局部更正。 | 好：改日期後重算；壞：要求使用者整段重講。 | 高風險上下文變更需重檢結果。 |
| X12 | 當 AI 讀取多個資料來源時，就應該讓資料範圍可見且可調整。 | 好：「本專案 3 份文件」；壞：看不出用了個人或公司資料。 | 不揭露使用者無權看到的資料。 |
| X13 | 當 AI 回饋用於改善服務時，就應該讓回饋對象具體。 | 好：標記某段「來源不符」；壞：只有整篇 thumbs-down 不知道原因。 | 不應強制寫長回饋才能繼續。 |
| X14 | 當 AI 不能完成任務時，就應該給出可採取的下一步。 | 好：「缺附件，加入後可重試」；壞：只有「出了點問題」。 | 不洩漏內部敏感錯誤細節。 |
| X15 | 當 AI 建議常打斷工作時，就應該提供暫停或關閉控制。 | 好：此頁停用建議；壞：每次關閉下一秒又彈出。 | 關閉功能不應難於啟用。 |
| X16 | 當多個頁面出現同類語意顏色時，就應該使用 semantic token。 | 好：text-danger／surface-selected；壞：每頁硬編不同紅色。 | 色票名稱可留底層，元件用角色。 |
| X17 | 當支援 light/dark theme 時，就應該按語意角色重新映射。 | 好：error 文字各 theme 都測對比；壞：所有顏色直接反相。 | 圖片與圖表也需要檢查。 |
| X18 | 當建立 component 規格時，就應該一起定義所有狀態。 | 好：default、focus、loading、error、disabled；壞：只給一張正常畫面。 | 狀態依元件用途選擇，不必機械套全部。 |
| X19 | 當兩個 component 名稱相同時，就應該維持核心行為一致。 | 好：同類 menu 都相同鍵盤模型；壞：外觀相同卻一個 Enter 開、一個 hover 開。 | 平台差異需明確記錄。 |
| X20 | 當新需求看似要新 component 時，就應該先檢查現有元件能否組合。 | 好：既有 field 加 hint；壞：每個產品各做一套 input。 | 真正新語意不強塞舊元件。 |
| X21 | 當規格有例外時，就應該記錄觸發條件。 | 好：「資料表可 compact」；壞：只寫「這頁比較特別」。 | 例外過多時回頭修正基礎模式。 |
| X22 | 當交付設計時，就應該附可測試情境而不只畫面。 | 好：空資料、慢網路、權限不足、超長姓名；壞：全是假資料正常狀態。 | 優先覆蓋實際產品高風險路徑。 |
| X23 | 當自動 accessibility 掃描全綠時，就應該再做人工作業測試。 | 好：鍵盤與 screen reader 實走；壞：把工具分數當合規證書。 | 人工測試也需有明確範圍。 |
| X24 | 當做 usability test 時，就應該給任務並觀察完成過程。 | 好：「找上月逾期訂單」；壞：「你覺得好看嗎」。 | 視覺偏好可另做測試。 |
| X25 | 當優化某個 conversion 指標時，就應該同看失誤與反悔成本。 | 好：完成率、退訂率、求助量一起看；壞：誤點造成的轉換也算成功。 | 指標應對準使用者成功。 |
| X26 | 當提供同意或拒絕選擇時，就應該讓文字與後果清楚。 | 好：「接受」「拒絕」可理解；壞：「不了，我不重視隱私」。 | 此為設計倫理建議，不宣稱特定法規結論。 |
| X27 | 當收費在後續才發生時，就應該在承諾前說明總價與週期。 | 好：「每月 NT$300，某日起扣款」；壞：把費用藏到完成後。 | 稅費未知則說明計算時點。 |
| X28 | 當使用者想取消服務時，就應該提供可找到且可完成的退出流程。 | 好：帳務頁能取消並確認結果；壞：加入一鍵、退出必須迷宮導航。 | 必要身分確認應與風險相稱。 |
| X29 | 當顯示名額或倒數時，就應該反映真實狀態。 | 好：真實活動截止；壞：重整就重設的假倒數。 | 沒有可靠資料時不要顯示精確剩餘量。 |
| X30 | 當要決定是否採用視覺新潮流時，就應該先檢查任務收益與可讀性。 | 好：品牌頁適量效果；壞：後台工具為流行而犧牲密度與操作。 | 不把單一品牌風格稱為全產業標準。 |

### Gaps

- 【未查到】沒有可支持「AI UI 已有單一全球統一最佳模式」的證據；此處是成熟原則加可驗證的落地推論。
- 【未查到】沒有採用任何「2026 最流行十大風格」排行或未證實百分比；Carbon 更新日期只能支持該頁當時更新，不能推出全產業採用率。
