import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NOTES = Path(__file__).resolve().parent
BOOK = ROOT / 'wiki/synthesis/uiux-design-cheat-book/uiux-design-cheat-book.md'
LOG = ROOT / 'log.md'
RAW = ROOT / 'raw/Web Framework/uiux-notes/uiux-notes.md'
BASELINE = NOTES / 'visuals-integration-baseline.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_text(path):
    return path.read_bytes().decode('utf-8').replace('\r\n', '\n')


def write_preserving_newlines(path, content):
    old = path.read_bytes()
    newline = '\r\n' if b'\r\n' in old else '\n'
    path.write_bytes(content.replace('\n', newline).encode('utf-8'))


def rules(text):
    return {
        key: digest(body.strip().encode('utf-8'))
        for key, body in re.findall(r'^### (UX\d{3})\n(.*?)(?=^#{1,3} |\Z)', text, re.M | re.S)
    }


def baseline():
    if BASELINE.exists():
        raise RuntimeError('Baseline already exists; preserve it.')
    data = {
        'book_sha256': digest(BOOK.read_bytes()),
        'rules': rules(read_text(BOOK)),
        'log_bytes': len(LOG.read_bytes()),
        'log_sha256': digest(LOG.read_bytes()),
        'raw_sha256': digest(RAW.read_bytes()),
    }
    assert len(data['rules']) == 284
    BASELINE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in data.items() if key != 'rules'}))
    print('Baseline: 284 rules.')


def manifests():
    entries = []
    for name in ['visuals-first.json', 'visuals-second.json']:
        loaded = json.loads((NOTES / name).read_text(encoding='utf-8'))
        if isinstance(loaded, dict):
            loaded = loaded.get('images', loaded.get('figures', loaded.get('entries')))
        assert isinstance(loaded, list), name
        entries.extend(loaded)
    assert sorted(int(item['chapter']) for item in entries) == list(range(1, 29))
    for item in entries:
        assert Path(item['filename']).name == item['filename']
        path = BOOK.parent / 'assets' / item['filename']
        with Image.open(path) as img:
            assert img.format == 'PNG'
            img.verify()
        assert item['alt'].strip() and item['caption'].strip() and item['rules']
    return sorted(entries, key=lambda item: int(item['chapter']))


def integrate():
    base = json.loads(BASELINE.read_text(encoding='utf-8'))
    assert digest(BOOK.read_bytes()) == base['book_sha256'], 'Book changed since baseline.'
    text = read_text(BOOK)
    entries = manifests()
    for item in entries:
        number = int(item['chapter'])
        pattern = rf'(^## {number:02d} [^\n]+\n\n[^\n]+\n\n)(?=### UX)'
        chapter = re.search(rf'^## {number:02d} [^\n]+\n(.*?)(?=^## |^# Part |\Z)', text, re.M | re.S)
        assert chapter, number
        for rule in item['rules']:
            assert f'### {rule}\n' in chapter.group(1), (number, rule)
        alt = item['alt'].replace('[', '（').replace(']', '）').replace('\n', ' ')
        caption = re.sub(r'(?<!#)\b(UX\d{3})\b', r'[[#\1]]', item['caption'].strip())
        for rule in item['rules']:
            if f'[[#{rule}]]' not in caption:
                caption += f' 參照 [[#{rule}]]。'
        insertion = f'![{alt}](assets/{item["filename"]})\n\n圖說：{caption}\n\n'
        text, count = re.subn(pattern, lambda match: match.group(1) + insertion, text, count=1, flags=re.M)
        assert count == 1, number
    origin = '本書每章附一張原創介面示意，呈現特定情境下的設計對照；案例數值不是通用門檻。圖下列出對應 UX 規則，可接著查閱適用條件與例外。\n\n'
    text = text.replace('## Situation Index\n', origin + '## Situation Index\n', 1)
    assert rules(text) == base['rules'], 'Rule text changed.'
    write_preserving_newlines(BOOK, text)
    index = ROOT / 'index.md'
    content = read_text(index)
    pattern = r'^(- \[\[uiux-design-cheat-book\]\] — .*?)(，含元件選擇矩陣.*)$'
    content, count = re.subn(pattern, r'\1，28 張章節對照圖\2', content, flags=re.M)
    assert count == 1
    write_preserving_newlines(index, content)
    entry = '\n## [2026-10-31] synthesis | UIUX visual examples\n\n為 UIUX Design Cheat Book 的 28 章加入原創介面對照圖、圖說與 UX 規則連結，方便讀者對照正反例；圖片存放於文章旁的 assets/，同步更新 index 入口。\n'
    old_log = LOG.read_bytes()
    assert digest(old_log[:base['log_bytes']]) == base['log_sha256'], 'Original log prefix changed.'
    newline = '\r\n' if b'\r\n' in old_log else '\n'
    with LOG.open('ab') as stream:
        stream.write(entry.replace('\n', newline).encode('utf-8'))
    verify()


def verify():
    base = json.loads(BASELINE.read_text(encoding='utf-8'))
    text = read_text(BOOK)
    assert rules(text) == base['rules']
    images = re.findall(r'!\[([^\]]+)\]\((assets/[^)]+)\)', text)
    assert len(images) == 28 and len({path for _, path in images}) == 28
    assert len(re.findall(r'^圖說：', text, re.M)) == 28
    for number in range(1, 29):
        chapter = re.search(rf'^## {number:02d} [^\n]+\n(.*?)(?=^## |^# Part |\Z)', text, re.M | re.S)
        assert chapter and len(re.findall(r'!\[', chapter.group(1))) == 1
        assert f'(assets/ch{number:02d}-' in chapter.group(1)
    for _, relative in images:
        assert (BOOK.parent / relative).is_file()
    headings = set(re.findall(r'^#{1,6} (.+)$', text, re.M))
    anchors = re.findall(r'\[\[#([^\]|]+)(?:\|[^\]]*)?\]\]', text)
    assert not set(anchors) - headings, sorted(set(anchors) - headings)
    assert digest(RAW.read_bytes()) == base['raw_sha256']
    assert digest(LOG.read_bytes()[:base['log_bytes']]) == base['log_sha256']
    for path in [BOOK, ROOT / 'index.md', LOG]:
        assert not path.read_bytes().startswith(b'\xef\xbb\xbf')
        path.read_bytes().decode('utf-8', errors='strict')
    assert '28 張章節對照圖' in read_text(ROOT / 'index.md')
    print('PASS: 28 chapter images/captions, 284 unchanged rules, valid assets/anchors, unchanged raw/log prefix, UTF-8 no BOM.')


if __name__ == '__main__':
    {'baseline': baseline, 'integrate': integrate, 'verify': verify}[sys.argv[1]]()
