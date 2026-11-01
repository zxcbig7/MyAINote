from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'wiki/synthesis/uiux-design-cheat-book/assets'
OUT.mkdir(parents=True, exist_ok=True)
BG = '#f6f7fb'
INK = '#172b4d'
MUTED = '#526174'
TEAL = '#087f8c'
RED = '#b42318'
LINE = '#d5dde7'
WHITE = '#ffffff'
FONT = 'C:/Windows/Fonts/msjh.ttc'
BOLD = 'C:/Windows/Fonts/msjhbd.ttc'

PLAN = [
    (15, 'dates-and-time', 'Dates and Time', '時間範圍：讓跨日與時區直接可見', ['UX125', 'UX127'], '左側只有23:00到01:00，右側分別標明開始與結束日期、台北時區及兩小時長度。', '當時間跨日或跨時區時，就應該在確認點顯示日期、時區與完整範圍。'),
    (16, 'multi-step-work', 'Multi-step Work', '草稿、已送出與已核准，是不同狀態', ['UX135', 'UX136', 'UX138'], '左側儲存草稿後顯示模糊的完成；右側有確認摘要、可編輯入口及尚未送審的草稿狀態。', '當流程有多個完成階段時，就應該明示目前狀態及下一個動作。'),
    (17, 'identity-and-onboarding', 'Identity and Onboarding', '登入完成後，回到使用者原本的任務', ['UX144', 'UX149'], '左側登入後跳到首頁而失去原任務；右側顯示工作空間並返回訂單A102的編輯畫面。', '當登入中斷任務時，就應該保留目的地，並清楚展示當前工作空間。'),
    (18, 'overlays', 'Overlays', '需要比對清單時，保留操作上下文', ['UX151', 'UX153'], '左側modal遮蔽清單，無法比對其他任務；右側非modal側欄保留可操作清單與選中項目。', '當使用者需要邊看清單邊改細節時，就應該考慮非modal側欄並保留上下文。'),
    (19, 'feedback-and-waiting', 'Feedback and Waiting', '處理中：顯示真實進度，也提供離開後的出口', ['UX166', 'UX167', 'UX168'], '左側匯出只有不明spinner且要求等待；右側顯示已處理240／500筆的48%進度與下載中心及停止按鈕。', '當能量測進度且工作較久時，就應該顯示真實進度與後續追蹤入口。'),
    (20, 'empty-and-destructive', 'Empty and Destructive States', '清單是空的，但原因與下一步不一樣', ['UX171', 'UX172', 'UX173'], '左側把首次無資料、篩選無結果和讀取失敗都顯示為沒有資料；右側三種狀態各有建立、清除篩選與重試動作。', '當清單沒有內容時，就應該依原因提供相符的下一步。'),
    (21, 'files-and-persistence', 'Files and Persistence', '多檔上傳：把失敗留在對應檔案旁', ['UX182'], '左側總訊息只說上傳失敗並要求全部重傳；右側逐檔標示成功與失敗，只有失敗檔提供重試。', '當多個檔案只有部分失敗時，就應該逐檔顯示狀態並只重試失敗項目。'),
    (22, 'tables-and-bulk-actions', 'Tables and Bulk Actions', '批次操作前，讓選取數量與作用範圍可見', ['UX197', 'UX198', 'UX202'], '左側全選與封存沒有說明範圍，金額格式混雜；右側明示已選本頁3筆、可選全部12筆，金額同精度靠右對齊。', '當資料表提供批次操作時，就應該明示數量與範圍，並讓可比較數字格式一致。'),
    (23, 'pagination-and-live-data', 'Pagination and Live Data', '新資料到達時，不要把正在看的列推走', ['UX206', 'UX209', 'UX210'], '左側新資料直接插入且排序重排，原本選中位置移動；右側保留第3頁及原列，使用有2筆新結果按鈕由使用者套用。', '當刷新可能打斷選取或閱讀時，就應該保留位置，讓使用者決定何時套用新資料。'),
    (24, 'dashboards-and-charts', 'Dashboards and Charts', '長條代表大小時，零基準不能省略', ['UX219', 'UX220'], '同樣92與95筆資料，左側縱軸從90起造成兩根長條看似相差數倍；右側從0起畫出正確比例，並保留精確數字。', '當長條長度代表數量時，就應該從零起算並讓精確數值可讀。'),
    (25, 'touch-and-motion', 'Touch and Motion', '拖曳排序之外，提供可點選的移動入口', ['UX229', 'UX231'], '左側項目只能拖曳把手排序；右側同一項目保留把手並提供上移和下移按鈕，圖示周圍有較大且不重疊的點擊區。', '當提供拖曳排序時，就應該另有單pointer點選替代，不能只依靠拖曳。'),
    (26, 'accessible-interaction', 'Accessible Interaction', '鍵盤操作時，焦點在哪裡必須看得見', ['UX240', 'UX241', 'UX242'], '左側沒有焦點外框且送出鈕藏在底部固定工具列下；右側送出鈕完整可見並有清晰焦點框，旁註Tab及Enter操作。', '當使用者以鍵盤操作時，就應該保留可見焦點，並避免固定工具列遮住目標。'),
    (27, 'ai-interaction', 'AI Interaction', 'AI 準備好草稿，不等於已執行外部動作', ['UX252', 'UX260', 'UX261'], '左側只寫完成，無法知道通知是否寄出；右側明示AI草稿尚未寄出，列收件人與主旨並提供預覽及寄出按鈕。', '當AI準備有外部副作用的工作時，就應該分清草稿與執行狀態，並展示對象與後果。'),
    (28, 'systems-and-validation', 'Systems and Validation', '交付元件時，把操作狀態一起畫出來', ['UX270', 'UX274'], '左側元件規格只有預設按鈕，右側同一儲存動作列出預設、焦點、儲存中、失敗與重試的介面狀態。', '當交付component規格時，就應該定義任務需要的狀態，而非只有一張正常畫面。'),
]

def font(size=28, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

class Canvas:
    def __init__(self, plan):
        self.plan = plan
        self.im = Image.new('RGB', (1400, 960), BG)
        self.d = ImageDraw.Draw(self.im)
        self.text(50, 28, f'{plan[0]:02d}  {plan[2]}', 40, bold=True)
        self.text(50, 86, plan[3], 30, MUTED)
        for i, x in enumerate((50, 725)):
            self.box(x, 154, 625, 665, WHITE, LINE, 18)
            self.text(x+28, 176, '容易出錯' if i == 0 else '建議做法', 30, RED if i == 0 else TEAL, True)
            self.d.line((x+28, 227, x+597, 227), fill=LINE, width=2)
        self.text(50, 854, ' / '.join(plan[4]), 26, TEAL, True)
        self.text(50, 900, '原創介面示意 • 請搭配正文情境與例外閱讀', 24, MUTED)

    def text(self, x, y, s, size=28, color=INK, bold=False, anchor=None):
        self.d.text((x, y), s, font=font(size, bold), fill=color, anchor=anchor)

    def wrap(self, x, y, s, width, size=28, color=INK, bold=False, step=42):
        line = ''
        for ch in s:
            if ch == '\n' or self.d.textlength(line+ch, font=font(size, bold)) > width:
                self.text(x, y, line, size, color, bold)
                y += step
                line = '' if ch == '\n' else ch
            else:
                line += ch
        if line:
            self.text(x, y, line, size, color, bold)
        return y+step

    def box(self, x, y, w, h, fill=WHITE, outline=LINE, radius=10, thickness=2):
        self.d.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=fill, outline=outline, width=thickness)

    def button(self, x, y, label, w=180, fill=TEAL, color=WHITE, focus=False):
        if focus:
            self.box(x-7, y-7, w+14, 70, WHITE, '#174ea6', 15, 4)
        self.box(x, y, w, 56, fill, fill if fill != WHITE else LINE)
        self.text(x+w/2, y+28, label, 26, color, True, 'mm')

    def field(self, x, y, label, value, w=515):
        self.text(x, y, label, 26, MUTED)
        self.box(x, y+42, w, 60)
        self.text(x+15, y+54, value, 28)

    def note(self, side, s):
        x = (50, 725)[side]
        self.wrap(x+28, 720, s, 565, 26, RED if side == 0 else TEAL, step=38)

    def arrow(self, x1, y1, x2, y2, color=MUTED):
        self.d.line((x1, y1, x2, y2), fill=color, width=4)
        self.d.polygon(((x2, y2), (x2-10, y2-16), (x2+10, y2-16)), fill=color)

def draw_dates(c):
    for i, x in enumerate((82, 757)):
        c.text(x, 255, '預約設備維護', 30, bold=True)
    c.field(82, 320, '時間', '23:00  —  01:00')
    c.button(82, 510, '確認預約', 230)
    c.note(0, '哪一天結束？用哪個時區？')
    c.field(757, 315, '開始 · 台北時間 UTC+8', '2026/11/06  23:00')
    c.field(757, 440, '結束 · 台北時間 UTC+8', '2026/11/07  01:00')
    c.text(757, 558, '跨至隔日 · 共 2 小時', 28, TEAL, True)
    c.button(757, 620, '確認預約', 230)
    c.note(1, '在承諾前顯示完整時間範圍。')

def draw_steps(c):
    for x in (82, 757):
        c.text(x, 255, '設備申請', 30, bold=True)
    c.box(82, 330, 515, 190, '#e8f4ef', '#e8f4ef')
    c.text(110, 365, '完成！', 40, TEAL, True)
    c.text(110, 432, '資料已儲存', 28)
    c.button(82, 580, '離開', 170)
    c.note(0, '只存了草稿，卻讓人以為已送審。')
    c.text(757, 310, '1 資料  →  2 確認  →  3 送出', 26, TEAL)
    c.box(757, 365, 515, 220)
    c.text(780, 390, '申請人  王小明', 28)
    c.text(780, 442, '項目      顯示器', 28)
    c.text(780, 497, '編輯資料', 26, TEAL, True)
    c.text(757, 600, '草稿已儲存 · 尚未送審', 28, TEAL, True)
    c.button(757, 650, '確認並送審', 240)
    c.note(1, '保存、提交、核准分別說明。')

def draw_identity(c):
    for x in (82, 757):
        c.box(x, 265, 515, 100)
        c.text(x+20, 285, '編輯訂單 A102', 30, bold=True)
        c.text(x+20, 330, '工作階段已過期，請登入', 24, MUTED)
        c.arrow(x+255, 380, x+255, 430)
        c.box(x+115, 438, 280, 70, '#e9eff6', '#e9eff6')
        c.text(x+255, 473, '登入成功', 28, INK, True, 'mm')
        c.arrow(x+255, 520, x+255, 568)
    c.box(82, 575, 515, 118)
    c.text(105, 598, '首頁', 32, bold=True)
    c.text(105, 646, '重新尋找剛才的訂單…', 26, MUTED)
    c.note(0, '驗證通過了，任務卻斷掉。')
    c.box(757, 575, 515, 118, '#edf8f8', TEAL)
    c.text(780, 591, 'A 公司 / 編輯訂單 A102', 28, bold=True)
    c.text(780, 643, '繼續剛才的編輯', 26, TEAL)
    c.note(1, '返回原任務，也讓工作範圍可見。')

def draw_overlays(c):
    for x in (82, 757):
        c.box(x, 270, 550, 410, '#f0f3f7', LINE)
        c.text(x+15, 285, '任務清單', 28, bold=True)
        for j, label in enumerate(('網站改版', '更新文案', '上線檢查')):
            c.box(x+12, 340+j*83, 235, 64, WHITE, TEAL if j == 1 else LINE)
            c.text(x+24, 355+j*83, label, 26)
    c.box(110, 310, 490, 300, '#e5e8ee', '#9ba6b7')
    c.box(150, 352, 420, 215)
    c.text(175, 376, '編輯：更新文案', 28, bold=True)
    c.field(175, 422, '負責人', '王小明', 365)
    c.note(0, '本情境要比對其他列，modal 卻遮住它們。')
    c.box(1018, 270, 289, 410, WHITE, TEAL)
    c.text(1036, 290, '更新文案', 28, bold=True)
    c.text(1036, 350, '負責人', 24, MUTED)
    c.box(1036, 390, 250, 60)
    c.text(1050, 405, '王小明', 26)
    c.button(1036, 515, '儲存', 250)
    c.text(1036, 596, '非 modal 側欄', 24, TEAL)
    c.note(1, '同時保留清單與可編輯細節。')

def draw_waiting(c):
    for x in (82, 757):
        c.text(x, 260, '匯出訂單', 30, bold=True)
    c.d.arc((270, 350, 410, 490), 30, 300, fill=MUTED, width=12)
    c.text(170, 540, '處理中，請勿離開', 30)
    c.note(0, '沒有真實進度，也不知道離開的後果。')
    c.text(757, 335, '已處理 240 / 500 筆', 32, bold=True)
    c.box(757, 405, 515, 28, '#e3e8ef', '#e3e8ef', 12)
    c.box(757, 405, 247, 28, TEAL, TEAL, 12)
    c.text(1245, 451, '48%', 28, TEAL, True, 'rt')
    c.text(757, 518, '可離開，背景會繼續處理。', 28)
    c.text(757, 566, '完成後可在下載中心取得。', 28)
    c.button(757, 636, '下載中心', 220)
    c.button(1000, 636, '停止匯出', 220, WHITE, RED)
    c.note(1, '進度可信，追蹤與停止也可理解。')

def draw_empty(c):
    rows = [('首次使用', '尚無專案', '建立專案'), ('有篩選條件', '沒有符合項目', '清除篩選'), ('讀取失敗', '無法讀取資料', '重試')]
    for j, (context, msg, action) in enumerate(rows):
        y = 258+j*145
        for x in (82, 757):
            c.box(x, y, 550, 127)
            c.text(x+18, y+13, context, 24, MUTED)
        c.text(104, y+63, '沒有資料', 30)
        c.text(777, y+61, msg, 28, bold=True)
        c.button(1110, y+55, action, 175)
    c.note(0, '相同訊息掩蓋了三種不同原因。')
    c.note(1, '說明原因，給真正有效的下一步。')

def draw_files(c):
    for x in (82, 757):
        c.text(x, 258, '上傳附件', 30, bold=True)
        c.text(x, 310, '共 3 個檔案', 26, MUTED)
    for j, name in enumerate(('需求.pdf', '報價.pdf', '照片.png')):
        y = 370+j*92
        c.box(82, y, 550, 72)
        c.text(102, y+20, name, 28)
        c.box(757, y, 550, 72, '#fff4f1' if j == 1 else WHITE, LINE)
        c.text(777, y+20, name, 28)
        c.text(960, y+20, '失敗' if j == 1 else '已完成', 26, RED if j == 1 else TEAL)
        if j == 1:
            c.button(1120, y+8, '重試', 165)
    c.text(82, 660, '上傳失敗 · 請全部重傳', 28, RED, True)
    c.text(757, 660, '2 個完成，1 個等待重試', 28, TEAL, True)
    c.note(0, '不知道哪一份失敗，容易重複上傳。')
    c.note(1, '把狀態與恢復動作留在檔案旁。')

def draw_table(c):
    for i, x in enumerate((82, 757)):
        c.text(x, 255, '訂單', 30, bold=True)
        c.box(x, 315, 550, 72, '#eaf3f4', '#eaf3f4')
        c.text(x+14, 334, '全選' if i == 0 else '已選本頁 3 筆', 27, bold=True)
        c.button(x+365, 323, '封存', 165)
        c.text(x+15, 412, '訂單', 26, MUTED, True)
        c.text(x+530, 412, '金額（NT$）', 26, MUTED, True, 'ra')
        for j, (name, amount) in enumerate((('A102', '100.00'), ('A103', '2,500.00'), ('A104', '80.00'))):
            y = 468+j*66
            c.d.line((x, y-6, x+550, y-6), fill=LINE, width=2)
            c.box(x+10, y+6, 24, 24, TEAL, TEAL, 4)
            c.d.line((x+15, y+18, x+20, y+24, x+29, y+12), fill=WHITE, width=3)
            c.text(x+47, y, name, 28, TEAL)
            if i == 1:
                c.text(x+530, y, amount, 28, INK, anchor='ra')
            else:
                c.text(x+260, y, ('100', '2,500.0', '八十')[j], 28)
        if i == 1:
            c.text(x, 680, '改選全部符合條件 12 筆', 26, TEAL, True)
    c.note(0, '「全選」作用範圍不明，數字難比較。')
    c.note(1, '明寫選取範圍，數字統一精度並靠右。')

def draw_live(c):
    for i, x in enumerate((82, 757)):
        c.text(x, 258, '待處理訂單 · 第 3 頁', 29, bold=True)
        c.text(x, 309, '更新於 10:32', 25, MUTED)
        if i:
            c.button(x, 360, '有 2 筆新結果 · 套用', 550)
        else:
            c.box(x, 360, 550, 56, '#fff4f1', '#fff4f1')
            c.text(x+15, 372, '自動插入，清單立即重排', 27, RED)
        ids = ['A207（新增）', 'A206（新增）', 'A205', 'A204'] if i == 0 else ['A205', 'A204', 'A203', 'A202']
        for j, name in enumerate(ids):
            y = 447+j*57
            c.box(x, y, 550, 48, '#e5f5f4' if name == 'A204' else WHITE, LINE, 6)
            c.text(x+16, y+7, name, 27)
        c.text(x+500, 630 if i == 0 else 516, '←', 38, RED if i == 0 else TEAL)
    c.note(0, '準備點的資料被新結果擠到別處。')
    c.note(1, '保留閱讀位置，等使用者套用刷新。')

def draw_chart(c):
    for i, x in enumerate((82, 757)):
        c.text(x, 255, '每月完成件數', 30, bold=True)
        c.text(x, 307, '同一組資料：92 與 95 件', 26, MUTED)
        left, top, bottom = x+75, 380, 665
        minv, maxv = (90, 96) if i == 0 else (0, 100)
        for tick in ([90, 92, 94, 96] if i == 0 else [0, 25, 50, 75, 100]):
            y = bottom-(tick-minv)/(maxv-minv)*(bottom-top)
            c.d.line((left, y, x+530, y), fill=LINE, width=2)
            c.text(left-15, y, str(tick), 24, MUTED, anchor='rm')
        for j, v in enumerate((92, 95)):
            bx = left+70+j*175
            by = bottom-(v-minv)/(maxv-minv)*(bottom-top)
            c.d.rectangle((bx, by, bx+90, bottom), fill=RED if i == 0 else TEAL)
            c.text(bx+45, by-12, str(v), 28, INK, True, 'mb')
            c.text(bx+45, bottom+13, ('9月', '10月')[j], 26, INK, anchor='mt')
    c.note(0, '縱軸從 90 起，長度放大了差距。')
    c.note(1, '零基準呈現比例，數字保留精確差異。')

def draw_touch(c):
    for i, x in enumerate((82, 757)):
        c.text(x, 260, '調整任務順序', 30, bold=True)
        for j, label in enumerate(('規劃', '設計', '開發')):
            y = 345+j*100
            c.box(x, y, 550, 82, '#eaf6f6' if j == 1 else WHITE, LINE)
            c.text(x+20, y+20, '≡', 30, MUTED)
            c.text(x+73, y+23, label, 28, bold=True)
            if i == 1 and j == 1:
                c.button(x+270, y+13, '上移', 115, WHITE, TEAL)
                c.button(x+402, y+13, '下移', 115, WHITE, TEAL)
        c.text(x, 660, '只能拖曳把手' if i == 0 else '也能以單次點選改變順序', 28, RED if i == 0 else TEAL)
    c.note(0, '小把手難操作，也缺少不拖曳的替代。')
    c.note(1, '拖曳與點選並存；圖中尺寸為示意。')

def draw_focus(c):
    for i, x in enumerate((82, 757)):
        c.text(x, 255, '聯絡資料', 30, bold=True)
        c.field(x, 320, '姓名', '王小明', 550)
        c.field(x, 440, 'Email', 'ming@example.com', 550)
        c.button(x+300, 630 if i == 0 else 575, '送出', 230, focus=bool(i))
        c.box(x, 655, 550, 48, '#dce3ed', '#dce3ed', 0)
        c.text(x+15, 662, '固定在底部的工具列', 25, MUTED)
    c.note(0, '焦點看不見，送出鈕也被遮住。')
    c.note(1, 'Tab 可定位，Enter 可操作，目標可見。')

def draw_ai(c):
    for x in (82, 757):
        c.text(x, 255, '協助寄出會議通知', 30, bold=True)
    c.box(82, 330, 550, 245, '#edf3fa', '#edf3fa')
    c.text(108, 365, '完成！', 40, bold=True)
    c.wrap(108, 435, '已準備好會議通知。', 490, 30)
    c.text(82, 625, '到底有沒有寄出？寄給誰？', 28, RED, True)
    c.note(0, '一句「完成」混淆草稿與執行結果。')
    c.box(757, 330, 550, 310, '#edf8f8', '#c5e4e5')
    c.text(780, 350, 'AI 草稿 · 尚未寄出', 30, TEAL, True)
    c.text(780, 412, '收件人  專案成員 3 位', 28)
    c.text(780, 465, '主旨      週五設計討論', 28)
    c.text(780, 526, '寄出後會通知以上成員。', 27, MUTED)
    c.button(780, 575, '預覽內容', 220, WHITE, TEAL)
    c.button(1022, 575, '確認寄出', 250)
    c.note(1, '顯示對象、狀態與執行前的審查入口。')

def draw_systems(c):
    c.text(82, 255, '儲存按鈕規格', 30, bold=True)
    c.text(82, 320, '預設狀態', 28, MUTED)
    c.button(82, 385, '儲存', 250)
    c.text(82, 520, '其他狀態呢？', 32, RED, True)
    c.note(0, '只有正常畫面，失敗時行為由各頁猜。')
    c.text(757, 255, '同一個儲存動作', 30, bold=True)
    rows = [('預設', '儲存', TEAL), ('焦點', '儲存', TEAL), ('等待', '儲存中…', '#526174'), ('失敗', '重試儲存', RED)]
    for j, (label, action, col) in enumerate(rows):
        y = 335+j*85
        c.text(757, y+13, label, 28)
        c.button(900, y, action, 360, col, focus=j == 1)
    c.text(757, 682, '失敗：草稿保留，請重試。', 26, RED)
    c.note(1, '狀態、文案與恢復動作一起交付。')

DRAW = [draw_dates, draw_steps, draw_identity, draw_overlays, draw_waiting, draw_empty, draw_files, draw_table, draw_live, draw_chart, draw_touch, draw_focus, draw_ai, draw_systems]

manifest = []
for plan, draw in zip(PLAN, DRAW):
    filename = f'ch{plan[0]:02d}-{plan[1]}.png'
    c = Canvas(plan)
    draw(c)
    c.im.save(OUT / filename, optimize=True)
    manifest.append({'chapter': f'{plan[0]:02d}', 'filename': filename, 'alt': plan[5], 'caption': plan[6]+' 對照：'+ '、'.join(plan[4])+'。', 'rules': plan[4]})
    print(filename)
Path(__file__).with_suffix('.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
sheet = Image.new('RGB', (1400, 960), BG)
for n, item in enumerate(manifest):
    im = Image.open(OUT / item['filename'])
    im.thumbnail((350, 240))
    sheet.paste(im, ((n % 4)*350, (n // 4)*240))
sheet.save(Path(__file__).with_name('contact-second.png'))
print(f'Wrote {len(manifest)} images and manifest')
