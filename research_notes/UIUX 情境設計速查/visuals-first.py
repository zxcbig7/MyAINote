from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'wiki/synthesis/uiux-design-cheat-book/assets'
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
BG = '#f6f7fb'
INK = '#172b4d'
TEAL = '#087f8c'
RED = '#b42318'
MUTED = '#526581'
LINE = '#ccd5e2'
SOFT = '#e8f4f3'
PINK = '#fff0ed'
FONT = 'C:/Windows/Fonts/msjh.ttc'
BOLD = 'C:/Windows/Fonts/msjhbd.ttc'

SPECS = [
    ('01', 'hierarchy', 'Hierarchy', '先看見任務，再看見補充資訊', ['UX001', 'UX002'], '左圖宣傳卡佔據工作台上半部；右圖先顯示待處理訂單與處理按鈕，宣傳降為次要入口。', '當使用者來完成工作時，就應該讓工作入口優先於宣傳資訊。'),
    ('02', 'spacing', 'Spacing', '用距離讓人看懂誰與誰是一組', ['UX007', 'UX008'], '左圖姓名與職稱使用相同段距而群組不清；右圖把同一人的姓名職稱靠近，人物之間留較大的距離。', '當資訊屬同一組時，就應該縮小組內距離、拉開組間距離。'),
    ('03', 'typography', 'Typography', '固定文字角色，讓資訊能被掃讀', ['UX015', 'UX016', 'UX017'], '左圖標題、資格與費用均以相同樣式連續堆放；右圖用頁標題、區塊標題與內文層級呈現同一申請說明。', '當內容需要掃讀時，就應該建立標題、區塊與內文的固定角色。'),
    ('04', 'color', 'Color', '狀態不能只剩下一個顏色', ['UX024', 'UX028', 'UX030'], '左圖訂單狀態只有紅綠圓點；右圖同樣三筆訂單加上完成、失敗與處理中文字和不同形狀。', '當顏色表示狀態時，就應該同時提供文字或形狀。'),
    ('05', 'nested-corners', 'Shape', '只有等距、同心的貼合輪廓才套公式', ['UX033', 'UX034', 'UX036'], '左圖內外圓角同為20，內輪廓看起來較彎；右圖外半徑20、邊界距離8、內半徑12形成同心等距輪廓，示意放大5倍。', '當內外輪廓需要等距同心時，就應該以實際邊界距離 d 推算內半徑。'),
    ('06', 'responsive', 'Responsive Layout', '窄螢幕要重排，不能丟掉核心任務', ['UX042', 'UX044'], '左圖手機沿用橫向資料列，金額被截斷；右圖把相同訂單的狀態、總額與動作重排為可閱讀的直向卡片。', '當容器變窄時，就應該重排核心資料與操作，而不是硬塞桌面版。'),
    ('07', 'navigation', 'Navigation', '頁標題、目前位置與導航一起說清楚', ['UX050', 'UX051', 'UX053'], '左圖只用抽象圖示導航且沒有頁面位置；右圖以可見導航名稱、選中狀態及麵包屑標示訂單明細。', '當使用者需要知道所在位置時，就應該保留頁標題與清楚的導航標示。'),
    ('08', 'tabs-comparison', 'Tabs and Disclosure', '需要同時比較的資訊，直接並列', ['UX056', 'UX061', 'UX062'], '左圖把兩個方案藏在不同tab內，只能一次看一個；右圖把同樣方案的月費、容量及使用者數並列比較。', '當任務是比較兩組資訊時，就應該讓它們同時可見。'),
    ('09', 'search-scope', 'Search', '搜尋框要說範圍，結果要說上下文', ['UX065', 'UX070'], '左圖搜尋欄位只寫搜尋，三筆同名結果無法區別；右圖明示搜尋專案檔案並在結果旁標示部門與季度。', '當搜尋範圍或同名結果可能混淆時，就應該把範圍與上下文放在畫面上。'),
    ('10', 'filter-state', 'Filters', '套用中的條件必須看得見、移得掉', ['UX073', 'UX075', 'UX077'], '左圖關閉篩選面板後只剩結果清單，無法知道有效條件；右圖在結果上方保留已套用的台北與本週條件及清除入口。', '當篩選面板關閉後，就應該仍讓使用者看見並移除生效條件。'),
    ('11', 'actions', 'Actions', '主次有差別，按鈕名稱說出結果', ['UX084', 'UX085'], '左圖用同樣醒目的確定與取消按鈕；右圖突出建立專案並將取消降為次要按鈕，名稱直接說明後果。', '當同一任務有主要與次要出口時，就應該突出主要動作並寫出結果。'),
    ('12', 'choice-controls', 'Choice Controls', '單選用單選，並就地列出代價', ['UX092', 'UX096'], '左圖配送方式用多選框，兩個互斥方式同時被勾選且費用藏在下一步；右圖用radio讓使用者單選，並在選項旁列運費。', '當答案只能擇一且費用不同時，就應該用單選元件並讓差異直接可見。'),
    ('13', 'field-labels', 'Fields', '填完後，仍然知道每一格是什麼', ['UX101', 'UX102', 'UX103'], '左圖填入資料後placeholder消失，只剩三串文字；右圖保留email、發票號碼與分機標籤，另有格式提示與選填標記。', '當使用者輸入資料後，就應該仍看見欄位名稱、格式提示與選填狀態。'),
    ('14', 'validation', 'Validation', '錯誤要告訴人怎麼修，資料不要清空', ['UX115', 'UX116', 'UX117'], '左圖只顯示資料不正確並清空原輸入；右圖保留姓名及email，頂端提供錯誤摘要並在email欄旁給可修正的提示。', '當提交驗證失敗時，就應該保留資料並把修正方式連到對應欄位。'),
]


def font(size=28, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def text(x, y, s, size=28, color=INK, bold=False, width=None):
    f = font(size, bold)
    if width is not None:
        assert D.textlength(s, font=f) <= width, (s, size, width)
    D.text((x, y), s, font=f, fill=color)


def box(x, y, w, h, fill='white', outline=LINE, radius=12, stroke=2):
    D.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline, width=stroke)


def button(x, y, w, label, primary=True, color=TEAL):
    box(x, y, w, 58, color if primary else 'white', color)
    f = font(28, True)
    tw = D.textlength(label, font=f)
    assert tw <= w - 20, label
    text(x + (w - tw) / 2, y + 9, label, 28, 'white' if primary else color, True)


def field(x, y, value, label=None, hint=None, error=False, w=545):
    if label:
        text(x, y, label, 28, INK, True, w)
        y += 42
    if hint:
        text(x, y, hint, 24, MUTED, width=w)
        y += 36
    box(x, y, w, 58, 'white', RED if error else '#91a0b4', 8)
    text(x + 15, y + 9, value, 28, width=w - 30)
    return y + 58


def note(x, y, lines, good=False):
    color = TEAL if good else RED
    for i, line in enumerate(lines):
        text(x, y + 38 * i, line, 26, color, width=545)


def ruleline(x, y, w=545):
    D.line((x, y, x + w, y), fill=LINE, width=2)


def start(spec):
    global I, D
    ch, slug, title, subtitle, ids, alt, caption = spec
    I = Image.new('RGB', (1400, 960), BG)
    D = ImageDraw.Draw(I)
    text(50, 30, f'{ch} / {title}', 40, bold=True, width=1300)
    text(50, 92, subtitle, 30, MUTED, width=1300)
    for x, good in ((50, False), (725, True)):
        box(x, 165, 625, 690, 'white', LINE, 22)
        text(x + 30, 188, '建議做法' if good else '容易出錯', 30, TEAL if good else RED, True)
        D.line((x + 30, 242, x + 595, 242), fill=LINE, width=2)
    text(50, 882, ' / '.join(ids), 26, TEAL, True)
    text(50, 920, '原創介面示意；情境與邊界請參照正文，畫面尺寸不是通用規範。', 24, MUTED)


def c01(x, good):
    text(x, 267, '訂單工作台', 34, bold=True)
    if good:
        box(x, 325, 545, 260, SOFT, '#b6dcd9')
        text(x + 25, 350, '待處理訂單', 30, bold=True)
        text(x + 25, 398, '12 筆待確認', 38, TEAL, True)
        button(x + 25, 484, 210, '處理訂單')
        ruleline(x, 626)
        text(x, 650, '新功能：自動產生報表', 28, MUTED)
        text(x, 695, '查看更新說明 →', 26, TEAL)
    else:
        box(x, 325, 545, 260, '#e5eafb', '#bcc8ef')
        text(x + 25, 350, '新功能登場', 38, '#3f4f86', True)
        text(x + 25, 410, '自動產生報表', 32, '#3f4f86')
        button(x + 25, 484, 210, '立即了解', color='#5364a4')
        text(x, 635, '待處理訂單：12 筆', 28)
        text(x, 682, '處理訂單 →', 26, TEAL)
    note(x, 785, ['先呈現當前任務' if good else '宣傳搶走主要工作區'], good)


def c02(x, good):
    text(x, 267, '專案聯絡人', 32, bold=True)
    people = [('王小文', '專案經理'), ('林小安', '產品設計師'), ('陳小宇', '前端工程師')]
    for idx, (name, role) in enumerate(people):
        y = 340 + idx * 140 if good else 330 + idx * 135
        if good:
            box(x, y - 12, 545, 108, '#f7f9fc', '#f7f9fc')
        text(x + 20, y, name, 30, bold=True)
        text(x + 20, y + (42 if good else 66), role, 28, MUTED)
    note(x, 785, ['組內靠近，組間留白' if good else '相同間距讓群組邊界不清'], good)


def c03(x, good):
    text(x, 270, '申請會員', 40 if good else 28, bold=good)
    if good:
        text(x, 340, '申請資格', 30, bold=True)
        text(x, 390, '完成公司 email 驗證即可申請。', 28, width=545)
        text(x, 475, '費用', 30, bold=True)
        text(x, 525, '基本方案免費；進階功能另計。', 28, width=545)
        text(x, 610, '申請前準備', 30, bold=True)
        text(x, 660, '公司名稱與可收信的 email。', 28)
    else:
        for y, s in zip(range(337, 690, 58), ['申請資格', '完成公司 email 驗證即可申請。', '費用', '基本方案免費；進階功能另計。', '申請前準備', '公司名稱與可收信的 email。']):
            text(x, y, s, 28, width=545)
    note(x, 785, ['標題與內文各有固定角色' if good else '讀者得逐行找出結構'], good)


def c04(x, good):
    text(x, 267, '訂單狀態', 32, bold=True)
    states = [('#A102', '完成', TEAL), ('#A103', '失敗', RED), ('#A104', '處理中', '#946200')]
    for j, (order, label, color) in enumerate(states):
        y = 350 + 120 * j
        text(x + 18, y, order, 30)
        if good:
            box(x + 260, y - 6, 235, 58, '#f7f9fc', LINE)
            if j == 0:
                D.line([(x + 280, y + 23), (x + 291, y + 34), (x + 309, y + 12)], fill=color, width=5)
            elif j == 1:
                D.polygon([(x + 295, y + 5), (x + 277, y + 37), (x + 313, y + 37)], outline=color, width=3)
            else:
                D.arc((x + 279, y + 7, x + 311, y + 39), 30, 300, fill=color, width=4)
            text(x + 330, y + 1, label, 28, color, True)
        else:
            D.ellipse((x + 390, y + 5, x + 425, y + 40), fill=color)
        ruleline(x, y + 75)
    note(x, 785, ['文字與形狀共同表示狀態' if good else '分不清顏色就分不清狀態'], good)


def c05(x, good):
    text(x, 267, '貼邊內容卡片・圓角放大示意', 28, bold=True, width=545)
    ox, oy, ow, oh = x + 40, 335, 465, 300
    box(ox, oy, ow, oh, INK, INK, 100, 1)
    box(ox + 10, oy + 10, ow - 20, oh - 20, '#e3eaf2', '#e3eaf2', 90, 1)
    box(ox + 40, oy + 40, ow - 80, oh - 80, '#a8d7d2', '#a8d7d2', 60 if good else 100, 1)
    text(ox + 103, oy + 120, '卡片內容', 32, TEAL, True)
    text(x, 666, '外半徑 20；border 2；padding 6', 25, width=545)
    text(x, 707, 'd = 8；內半徑 = 20 - 8 = 12' if good else '內外都設為 20 → 弧心不同', 26, TEAL if good else RED, True, 545)
    note(x, 786, ['示例放大 5 倍；d 是實際邊界距離'], good)


def c06(x, good):
    px, py = x + 87, 275
    box(px, py, 370, 470, '#f9fbfd', INK, 30, 3)
    text(px + 25, py + 32, '訂單 #A102', 30, bold=True)
    if good:
        text(px + 25, py + 105, '狀態', 24, MUTED)
        text(px + 25, py + 140, '待確認', 30, TEAL, True)
        text(px + 25, py + 218, '總額', 24, MUTED)
        text(px + 25, py + 253, 'TWD 3,200', 32, bold=True)
        button(px + 25, py + 355, 320, '確認訂單')
    else:
        for dx, s in ((25, '狀態'), (190, '總額')):
            text(px + dx, py + 110, s, 28, MUTED)
        text(px + 25, py + 165, '待確認', 28, TEAL)
        text(px + 190, py + 165, 'TWD 3,…', 28)
        ruleline(px + 25, py + 220, 320)
        button(px + 25, py + 355, 320, '確認訂單')
        D.line((px + 330, py + 150, px + 330, py + 216), fill=RED, width=3)
    note(x, 785, ['改為直向資訊，總額完整可讀' if good else '硬保留橫排，重要數字被截斷'], good)


def c07(x, good):
    if good:
        text(x, 270, '商品     訂單     報表', 28)
        D.line((x + 120, 316, x + 180, 316), fill=TEAL, width=5)
        text(x, 350, '訂單  >  #A102', 26, MUTED)
        text(x, 405, '訂單明細', 36, bold=True)
    else:
        D.line([(x + 10, 293), (x + 30, 275), (x + 50, 293)], fill=INK, width=3)
        D.line([(x + 16, 290), (x + 16, 315), (x + 44, 315), (x + 44, 290)], fill=INK, width=3)
        D.line([(x + 135, 315), (x + 135, 280), (x + 151, 280), (x + 158, 289), (x + 178, 289), (x + 178, 315), (x + 135, 315)], fill=INK, width=3)
        D.line([(x + 260, 275), (x + 260, 316), (x + 307, 316)], fill=INK, width=3)
        D.line([(x + 268, 303), (x + 280, 292), (x + 291, 298), (x + 305, 279)], fill=INK, width=3)
        text(x, 405, '#A102', 36, bold=True)
    box(x, 480, 545, 210, '#f7f9fc', LINE)
    text(x + 25, 508, '王小文', 30, bold=True)
    text(x + 25, 558, 'TWD 3,200', 30)
    text(x + 25, 610, '待確認', 28, TEAL)
    note(x, 785, ['名稱、選中狀態與標題互相呼應' if good else '圖示與編號不足以辨識位置'], good)


def c08(x, good):
    text(x, 267, '比較方案', 32, bold=True)
    if good:
        text(x + 195, 347, '基本', 28, bold=True)
        text(x + 365, 347, '專業', 28, bold=True)
        for y, label, a, b in [(422, '月費', '$300', '$900'), (512, '容量', '20 GB', '100 GB'), (602, '人數', '3 人', '10 人')]:
            ruleline(x, y - 20)
            text(x + 15, y, label, 28, MUTED)
            text(x + 190, y, a, 28)
            text(x + 355, y, b, 28)
    else:
        text(x + 25, 340, '基本', 30, TEAL, True)
        text(x + 230, 340, '專業', 30, MUTED)
        D.line((x + 20, 390, x + 150, 390), fill=TEAL, width=5)
        ruleline(x, 395)
        for y, s in [(435, '月費：$300'), (515, '容量：20 GB'), (595, '人數：3 人')]:
            text(x + 25, y, s, 30)
    note(x, 785, ['比較時讓兩份資料同時可見' if good else '切來切去，必須靠記憶比較'], good)


def c09(x, good):
    text(x, 267, '專案文件', 32, bold=True)
    field(x, 330, '季度報表', '搜尋此專案檔案' if good else '搜尋')
    for i, s in enumerate(['財務 · 2026 Q3', '行銷 · 2026 Q3', '財務 · 2026 Q2']):
        y = 470 + 92 * i
        text(x + 15, y, '季度報表', 29, TEAL, True)
        if good:
            text(x + 205, y + 2, s, 25, MUTED, width=330)
        ruleline(x, y + 64)
    note(x, 785, ['搜尋範圍與同名結果都可辨識' if good else '不知道在哪找，也分不清結果'], good)


def c10(x, good):
    text(x, 267, '訂單清單', 32, bold=True)
    button(x + 350, 265, 190, '篩選', False)
    if good:
        for dx, label, w in ((0, '台北 ×', 150), (170, '本週 ×', 150)):
            box(x + dx, 350, w, 52, SOFT, '#b6dcd9', 22)
            text(x + dx + 15, 359, label, 25, TEAL)
        text(x + 350, 362, '清除全部', 25, TEAL)
        text(x, 430, '已套用篩選 · 12 筆', 28, MUTED)
    else:
        text(x, 430, '12 筆訂單', 28, MUTED)
    for i, n in enumerate(['#A102', '#A106', '#A112']):
        y = 500 + i * 75
        text(x + 15, y, n, 28)
        text(x + 330, y, '待確認', 28, TEAL)
        ruleline(x, y + 53)
    note(x, 785, ['面板關閉後仍可確認生效條件' if good else '篩選仍有效，畫面卻沒有線索'], good)


def c11(x, good):
    text(x, 267, '建立專案', 34, bold=True)
    field(x, 350, '網站改版', '專案名稱')
    text(x, 510, '建立後可邀請成員加入。', 28, MUTED)
    if good:
        button(x, 620, 260, '建立專案')
        button(x + 295, 620, 220, '取消', False)
    else:
        button(x, 620, 260, '確定')
        button(x + 295, 620, 220, '取消')
    note(x, 785, ['主動作突出，而且說出後果' if good else '兩個出口同樣搶眼，文案含糊'], good)


def c12(x, good):
    text(x, 267, '配送方式', 34, bold=True)
    text(x, 322, '請選擇一種配送方式', 26, MUTED)
    for i, (label, price) in enumerate([('宅配', '$80'), ('門市自取', '免費')]):
        y = 410 + i * 145
        if good:
            D.ellipse((x + 15, y, x + 47, y + 32), outline=TEAL if i == 0 else MUTED, width=3)
            if i == 0:
                D.ellipse((x + 23, y + 8, x + 39, y + 24), fill=TEAL)
        else:
            box(x + 15, y, 32, 32, TEAL, TEAL, 4)
            D.line([(x + 21, y + 16), (x + 29, y + 24), (x + 42, y + 8)], fill='white', width=3)
        text(x + 75, y - 4, label, 30, bold=True)
        text(x + 75, y + 45, '運費：' + price if good else '運費將在下一步顯示', 26, MUTED)
    note(x, 785, ['單選明確，價格差異就地可見' if good else '互斥選項卻可複選，費用延後'], good)


def c13(x, good):
    text(x, 267, '聯絡資料', 34, bold=True)
    if good:
        field(x, 330, 'vic@example.com', 'Email')
        field(x, 462, 'AB12345678', '發票號碼', '格式：2 個英文字母＋8 位數字')
        field(x, 630, '123', '分機（選填）')
    else:
        field(x, 370, 'vic@example.com')
        field(x, 500, 'AB12345678')
        field(x, 630, '123')
    note(x, 794, ['標籤不消失，格式不用猜' if good else '填完只剩內容，看不出欄位用途'], good)


def c14(x, good):
    text(x, 265, '聯絡資料・提交後', 32, bold=True)
    if good:
        box(x, 325, 545, 108, PINK, RED, 10)
        text(x + 18, 338, '請修正 1 個問題', 28, RED, True)
        text(x + 18, 380, 'Email 不完整 → 跳至欄位', 26, RED)
        field(x, 460, '王小文', '姓名')
        field(x, 590, 'vic@', 'Email', error=True)
        text(x, 700, '請輸入完整 email，例如 a@b.com', 25, RED, width=545)
    else:
        box(x, 325, 545, 108, PINK, RED, 10)
        text(x + 18, 350, '資料不正確', 30, RED, True)
        field(x, 460, '', '姓名')
        field(x, 590, '', 'Email', error=True)
    note(x, 794, ['保留內容，指出欄位與修正方式' if good else '訊息含糊，正確資料也被清掉'], good)


manifest = []
for spec in SPECS:
    ch, slug, title, subtitle, ids, alt, caption = spec
    filename = f'ch{ch}-{slug}.png'
    manifest.append({'chapter': ch, 'filename': filename, 'alt': alt, 'caption': caption + ' 參照 ' + '、'.join(ids) + '。', 'rules': ids})
(HERE / 'visuals-first.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for spec, entry in zip(SPECS, manifest):
    start(spec)
    render = globals()['c' + spec[0]]
    render(90, False)
    render(765, True)
    I.save(OUT / entry['filename'])
    print(entry['filename'])

sheet = Image.new('RGB', (1400, 7 * 480), BG)
for i, entry in enumerate(manifest):
    thumb = Image.open(OUT / entry['filename']).resize((700, 480), Image.Resampling.LANCZOS)
    sheet.paste(thumb, ((i % 2) * 700, (i // 2) * 480))
sheet.save(HERE / 'contact-first.png')
