# python3 src/gen_etyketky.py <outDir>
# Етикетки цеху для Zebra LP 2824 Plus (203 dpi, 57,3×41 мм) з QR на картку продукції.
# Створює: <outDir>/pdf/<назва>.pdf (кожна етикетка), <outDir>/vsi-etyketky.pdf (усі, по одній на сторінку),
#          <outDir>/zrazky-A4.pdf (огляд на аркушах A4), <outDir>/zpl/<назва>.zpl (друк напряму на Zebra),
#          <outDir>/png/<назва>.png (картинка 1:1 у точках принтера).
# Потрібні пакети: pillow, reportlab, segno.
import os, sys, html, shutil, importlib.util
import segno
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

d = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('etyketky', os.path.join(d, 'etyketky.py'))
E = importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
BASE = 'https://fisheverydaybot-cmd.github.io/dovidnyk/p/'

DPI = 203
W, H = 458, 328          # точки принтера: 57,3 × 41 мм (розмір з файлів ZebraDesigner)
SIZES = {False: (458, 328), True: (448, 406)}   # True — фасовка 200 г: 56 × 50,75 мм (як у файлах .prn фасовки)


def set_size(l):
    global W, H
    W, H = SIZES[bool(l.get('pack'))]
M = 9                    # поле
QM = 3                   # розмір модуля QR у точках (0,375 мм)
LIFT = 12  # 1,5 мм вгору від низу (8 точок = 1 мм)
FONTS = {False: '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf',
         True: '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'}
_fc = {}


# народні і російські назви для пошуку на сторінці етикеток
SYN = {'пласт': 'метелик бабочка', 'оселед': 'сельдь селедка', 'товстолоб': 'толстолоб', 'лящ': 'лещ', 'ікр': 'икра',
       'кілька': 'килька', 'тюлька': 'тюлька', 'вʼял': 'вяленая', 'гарячого копчення': 'г/к гк горячего', 'холодного копчення': 'х/к хк холодного',
       'солон': 'соленая', 'мойва': 'мойва', 'камбала': 'камбала', 'окунь червоний': 'окунь морской', 'сом ': 'сом', 'щука': 'щука',
       'ставрида': 'ставрида', 'хребт': 'хребты', 'черевц': 'брюшки', 'фасовка': 'фасованая', 'нерозібран': 'неразделанная', 'патран': 'потрошеная'}


def search_q(title):
    t = title.lower()
    return ' '.join([t] + [v for k, v in SYN.items() if k in t])


def font(size, bold=False):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONTS[bold], size)
    return _fc[k]


def tw(segs, size):
    return sum(font(size, b).getlength(s) for s, b in segs)


def wrap(segs, size, width):
    """segs: [(текст, жирний)] → рядки, кожен — список сегментів. Пробіл ставиться лише там, де він був у тексті."""
    words = []          # [слово, жирний, чи був пробіл перед ним]
    gap = False
    for s, b in segs:
        for i, w in enumerate(s.split(' ')):
            if i > 0:
                gap = True
            if w:
                words.append((w, b, gap and bool(words)))
                gap = False
    lines, cur = [], []
    for w, b, sp in words:
        cand = cur + ([(' ', False)] if cur and sp else []) + [(w, b)]
        if cur and sp and tw(cand, size) > width:
            lines.append(cur); cur = [(w, b)]
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def deg(t):
    return ('+' if t > 0 else '') + str(t).replace('-', '−')


def layout(l, body=17):
    """Повертає список операцій малювання в точках (y — базова лінія) або None, якщо не влазить."""
    ops = []
    y = M
    full = W - 2 * M
    # назва
    ts = 25
    titles = l['title']
    while max(tw([(t, True)], ts) for t in titles) > full and ts > 18:
        ts -= 1
    if max(tw([(t, True)], ts) for t in titles) > full:
        ts = 22
        titles = [''.join(x for x, _ in ln) for ln in wrap([(' '.join(l['title']), True)], ts, full)]
        while len(titles) > 2 and ts > 18:
            ts -= 1
            titles = [''.join(x for x, _ in ln) for ln in wrap([(' '.join(l['title']), True)], ts, full)]
    for t in titles:
        y += ts - 3
        ops.append(('text', (W - tw([(t, True)], ts)) / 2, y, ts, [(t, True)]))
    y += 3
    # стандарт
    if l['std']:
        y += body
        ops.append(('text', (W - tw([(l['std'], False)], body)) / 2, y, body, [(l['std'], False)]))
    lh = body + 1
    if l.get('paras') is not None:      # етикетка іншого виробника — текст як є
        for ptxt in l['paras']:
            for ln in wrap([(ptxt, False)], body, full):
                y += lh
                ops.append(('text', M, y, body, ln))
        return bottom_block(l, ops, y, body)
    fish, rest = l['comp'].split(',', 1) if ',' in l['comp'] else (l['comp'], '')
    comp = [('Склад: ', False), (fish, True)]
    if rest:
        # алергени в складі (крім риби) теж жирним
        for i, part in enumerate((',' + rest).split('гірчиця')):
            if i:
                comp.append(('гірчиця', True))
            comp.append((part, False))
    comp.append(('.', False))
    merged = []
    for t, b in comp:
        if merged and merged[-1][1] == b:
            merged[-1] = (merged[-1][0] + t, b)
        else:
            merged.append((t, b))
    paras = [merged]
    if l['salt']:
        paras.append([('Ступінь солоності: ' + l['salt'] + '.', False)])
    if isinstance(l['t'], str):      # складні умови зберігання — готовим текстом
        paras.append([(l['t'].rstrip('.') + '.', False)])
    else:
        lo, hi = l['t']
        paras.append([(f'Зберігати при t від {deg(lo)} до {deg(hi)} °C. Термін придатності {l["term"].rstrip(".")}.', False)])
    b = str(l['b']).replace('.', ',')
    paras.append([(f'Поживна цінність 100 г: білки {b} г, жири {str(l["f"]).replace('.', ',')} г.', False)])
    paras.append([(f'Енергетична цінність 100 г: {l["kcal"]} ккал / {round(l["kcal"] * 4.184)} кДж.', False)])
    for p in paras:
        for ln in wrap(p, body, full):
            y += lh
            ops.append(('text', M, y, body, ln))
    return bottom_block(l, ops, y, body)


def bottom_block(l, ops, y, body):
    # нижній блок: ліворуч поля і виробник, праворуч QR
    fs = body - 1
    fl = fs + 1
    if l.get('qr') is False:
        left = W - M
        bottom = []
        if l.get('mass'):
            bottom.append(('text', [('Маса нетто: ' + l['mass'], False)]))
        else:
            bottom.append(('field', 'Маса нетто', 'кг', 'mass'))
        bottom.append(('field', 'Дата виробництва', '', 'date'))
        for ln in wrap([(l['op'], True)], fs, left - M):
            bottom.append(('text', ln))
        for ln in wrap([(l['addr'], False)], fs, left - M):
            bottom.append(('text', ln))
        if l.get('gmo'):
            bottom.append(('text', [('без ГМО', False)]))
        by = H - M - LIFT - len(bottom) * fl + fs - 2
        if by - fs < y + 2:
            return None
        return draw_bottom(ops, bottom, by, fs, fl, left)
    q = segno.make(BASE + l['id'] + '/', error='m')
    mat = [list(r) for r in q.matrix_iter(border=0)]
    qs = len(mat) * QM
    qx, qy = W - M - qs, H - M - LIFT - qs + 2
    ops.append(('qr', qx, qy, mat))
    cap = l.get('cap', 'Про рибу')
    ops.append(('text', qx + (qs - tw([(cap, True)], 14)) / 2, qy - 4, 14, [(cap, True)]))
    left = qx - M - 10
    if l.get('pack'):
        # nomass: вагу друкують ваги CAS — рядка ваги на етикетці немає
        top = ([] if l.get('nomass') else [('text', [('Вага нетто 200 г ± 5 %', False)])]) + [('field', 'Дата пакування', '', 'date'), ('field', 'Вжити до', '', 'until')]
    else:
        top = [('field', 'Маса нетто', 'кг', 'mass'), ('field', 'Дата виготовлення', '', 'date')]
    bottom = top + [
        ('field', 'Партія №', '', 'batch'),
        ('text', [('Виробник: ', False), (l.get('op', E.OPERATOR), True)]),
        ('text', [(l.get('addr', E.ADDRESS), False)]),
        ('text', [('тел. ' + l.get('phone', E.PHONE) + '      без ГМО', False)]),
    ]
    by = H - M - LIFT - len(bottom) * fl + fs - 2
    if by - fs < y + 2 or qy - 18 < y:
        return None
    return draw_bottom(ops, bottom, by, fs, fl, left)


def draw_bottom(ops, bottom, by, fs, fl, left):
    for it in bottom:
        if it[0] == 'field':
            _, lab, unit, key = it
            ops.append(('text', M, by, fs, [(lab, False)]))
            x1 = M + tw([(lab, False)], fs) + 4
            x2 = left - (tw([(unit, False)], fs) + 4 if unit else 0)
            if unit:
                ops.append(('text', x2 + 4, by, fs, [(unit, False)]))
            ops.append(('rule', x1, x2, by + 1))
            # місце для змінного значення (дата, партія, маса), яке вписує сторінка друку
            ops.append(('slot', key, round(x1), round(x2), round(by), fs))
        else:
            segs = it[1]
            s = fs
            while tw(segs, s) > left - M and s > 12:
                s -= 1
            ops.append(('text', M, by, s, segs))
        by += fl
    return ops


def fit(l):
    for body in (20, 19, 18, 17, 16, 15, 14, 13, 12, 11):
        ops = layout(l, body)
        if ops:
            return ops
    raise SystemExit('не влазить: ' + l['file'])


def render_png(ops, k=1):
    """k=1 — 1:1 у точках принтера (чорно-біле, для друку); k>1 — чітка картинка для перегляду на екрані."""
    # Малюємо зі згладжуванням і потім переводимо в чорно-біле: так усі слова стоять на одній лінії
    # (у режимі '1' Pillow піднімав на 1 точку слова, що починаються з «б», напр. «білки»).
    hd = k > 1
    im = Image.new('L', (W * k, H * k), 255)
    dr = ImageDraw.Draw(im)
    for op in ops:
        if op[0] == 'text':
            _, x, y, s, segs = op
            for t, b in segs:
                dr.text((x * k, y * k), t, font=font(s * k, b), fill=0, anchor='ls')
                x += font(s, b).getlength(t)
        elif op[0] == 'rule':
            _, x1, x2, y = op
            dr.line([(x1 * k, y * k), (x2 * k, y * k)], fill=0, width=k)
        elif op[0] == 'qr':
            _, x, y, mat = op
            x, y = round(x), round(y)
            for r, row in enumerate(mat):
                for c, v in enumerate(row):
                    if v:
                        dr.rectangle([(x + c * QM) * k, (y + r * QM) * k, (x + c * QM + QM) * k - 1, (y + r * QM + QM) * k - 1], fill=0)
    if hd:
        return im.quantize(4)
    return im.point(lambda v: 0 if v < 128 else 255).convert('1', dither=Image.Dither.NONE)


def zpl(im):
    bpr = (W + 7) // 8
    data = bytearray()
    px = im.load()
    for yy in range(H):
        for bx in range(bpr):
            v = 0
            for k in range(8):
                xx = bx * 8 + k
                v = (v << 1) | (1 if xx < W and px[xx, yy] == 0 else 0)
            data.append(v)
    hexs = data.hex().upper()
    rows = '\n'.join(hexs[i:i + bpr * 2] for i in range(0, len(hexs), bpr * 2))
    return (f'^XA\n^PW{W}\n^LL{H}\n^LH0,0\n^FO0,0^GFA,{len(data)},{len(data)},{bpr},\n{rows}\n^FS\n^PQ1\n^XZ\n')


pdfmetrics.registerFont(TTFont('Carl', FONTS[False]))
pdfmetrics.registerFont(TTFont('CarlB', FONTS[True]))
PT = 72 / DPI


def draw_pdf(c, ops, ox=0, oy=0):
    """ox, oy — зсув у pt від лівого нижнього кута сторінки."""
    def Y(y): return oy + (H - y) * PT
    for op in ops:
        if op[0] == 'text':
            _, x, y, s, segs = op
            for t, b in segs:
                c.setFont('CarlB' if b else 'Carl', s * PT)
                c.drawString(ox + x * PT, Y(y), t)
                x += font(s, b).getlength(t)
        elif op[0] == 'rule':
            _, x1, x2, y = op
            c.setLineWidth(0.3)
            c.line(ox + x1 * PT, Y(y), ox + x2 * PT, Y(y))
        elif op[0] == 'qr':
            _, x, y, mat = op
            x, y = round(x), round(y)
            for r, row in enumerate(mat):
                for cc, v in enumerate(row):
                    if v:
                        c.rect(ox + (x + cc * QM) * PT, Y(y + r * QM + QM), QM * PT, QM * PT, stroke=0, fill=1)


HDK = 3  # збільшення картинки для перегляду на екрані


def main(out):
    for sub in ('pdf', 'zpl', 'png', 'png-hd'):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    allc = canvas.Canvas(os.path.join(out, 'vsi-etyketky.pdf'), pagesize=(W * PT, H * PT))
    allc.setTitle('Етикетки ТОВ «ФІШ-МАКСИМУМ ТРЕЙД»')
    a4 = canvas.Canvas(os.path.join(out, 'zrazky-A4.pdf'), pagesize=(210 * mm, 297 * mm))
    a4.setTitle('Етикетки — огляд на A4')
    cols, rows_ = 3, 5
    CW, CH = 458, 406
    gx, gy = (210 * mm - cols * CW * PT) / (cols + 1), (297 * mm - rows_ * CH * PT) / (rows_ + 1)
    for i, l in enumerate(E.LABELS):
        set_size(l)
        ops = fit(l)
        l['_slots'] = {o[1]: list(o[2:]) for o in ops if o[0] == 'slot'}
        name = l['file'].strip().replace('  ', ' ')
        im = render_png(ops)
        im.save(os.path.join(out, 'png', name + '.png'))
        render_png(ops, HDK).save(os.path.join(out, 'png-hd', name + '.png'), optimize=True)
        open(os.path.join(out, 'zpl', name + '.zpl'), 'w', encoding='ascii').write(zpl(im))
        c = canvas.Canvas(os.path.join(out, 'pdf', name + '.pdf'), pagesize=(W * PT, H * PT))
        c.setTitle(name); draw_pdf(c, ops); c.showPage(); c.save()
        allc.setPageSize((W * PT, H * PT)); draw_pdf(allc, ops); allc.showPage()
        k = i % (cols * rows_)
        if i and k == 0:
            a4.showPage()
        cx = gx + (k % cols) * (CW * PT + gx)
        cy = 297 * mm - (k // cols + 1) * (CH * PT + gy) + (CH - H) * PT
        a4.setLineWidth(0.3); a4.setStrokeGray(0.6)
        a4.roundRect(cx, cy, W * PT, H * PT, 2 * mm, stroke=1, fill=0)
        a4.setStrokeGray(0)
        draw_pdf(a4, ops, cx, cy)
    allc.save(); a4.showPage(); a4.save()
    print('етикеток:', len(E.LABELS))


SITE_CSS = """*{box-sizing:border-box}body{margin:0;font:17px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#1d2730;background:#f5faf7}
header{background:#2e8b57;color:#fff;padding:14px 16px}header a{color:#fff;text-decoration:none;font-weight:700;font-size:19px}header small{display:block;opacity:.85;font-size:13px}
main{max-width:760px;margin:0 auto;padding:16px 14px 50px}h1{font-size:24px;margin:4px 0 8px}
.how{background:#fff;border:1px solid #cfe9d8;border-radius:12px;padding:10px 16px;font-size:15px}
input{width:100%;font:inherit;padding:11px 13px;border:1px solid #a8d8b9;border-radius:10px;margin:12px 0}
.it[hidden],.grp[hidden],#none[hidden]{display:none!important}
.it{display:flex;gap:12px;align-items:center;background:#fff;border:1px solid #cfe9d8;border-radius:12px;padding:10px;margin-bottom:8px}
.it img{width:150px;height:auto;border:1px solid #ddd;border-radius:4px;image-rendering:pixelated;flex:none}
.it b{display:block;line-height:1.3}.it small{color:#5b6873}
.it a{display:inline-block;margin:6px 6px 0 0;padding:7px 12px;border-radius:9px;background:#2e8b57;color:#fff;text-decoration:none;font-weight:600;font-size:15px}
.it a.z{background:#e9f6ee;color:#1d5c3a}
.vars{background:#fff;border:2px solid #2e8b57;border-radius:12px;padding:10px 14px;margin-bottom:12px}
.row3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.vars label{font-size:14px;font-weight:600;color:#1d5c3a}
.vars input{margin:4px 0 0}.vars .chk{display:flex;gap:8px;align-items:center;font-weight:400;color:#1d2730}.vars .chk input{width:auto;margin:0}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 0}.tab{font:inherit;font-size:15px;font-weight:600;padding:8px 12px;border-radius:20px;border:1px solid #a8d8b9;background:#fff;color:#1d5c3a;cursor:pointer}
.tab span{font-weight:400;opacity:.7}.tab.on{background:#2e8b57;color:#fff;border-color:#2e8b57}
.grp h2{font-size:16px;text-transform:uppercase;letter-spacing:.04em;color:#1d5c3a;margin:18px 0 8px}
.tip{font-size:13px;color:#5b6873;margin:6px 0 0}
@media(max-width:520px){.row3{grid-template-columns:1fr}}
@media(max-width:520px){.it{flex-direction:column;align-items:flex-start}.it img{width:100%}}"""


# Групи на сторінці друку. Порядок = порядок вкладок. Етикетці можна задати групу вручну: поле 'cat' у src/etyketky.py.
CATS = [('sol', 'Солона'), ('pryan', 'Пряного і спецпосолу'), ('mar', 'Мариновані, в олії, в соусі'),
        ('hk', 'Гарячого копчення'), ('khk', 'Холодного копчення'), ('vyal', 'Вʼялена'), ('rulet', 'Рулети, ковбаси, шинки'),
        ('fas', 'Фасовка'), ('sylno', 'Сильносолена морожена (напівфабрикат)'), ('mm', 'Морська морожена (напівфабрикат)'),
        ('mr', 'Річкова морожена (напівфабрикат)'), ('moroz', 'Морожена'), ('inshi', 'Інші виробники')]


def cat(l):
    if l.get('cat'):
        return l['cat']
    t = ' '.join(l['title']).lower().replace("'", 'ʼ').replace('’', 'ʼ')
    if 'гарячого копч' in t:
        return 'hk'
    if 'копч' in t:
        return 'khk'
    if 'вʼял' in t or 'сушен' in t:
        return 'vyal'
    if 'морож' in t:
        return 'moroz'
    if any(w in t for w in ('маринов', 'олії', 'заливц', 'соус')):
        return 'mar'
    if 'пряного' in t or 'спеціального посолу' in t:
        return 'pryan'
    return 'sol'


def site(sitedir, labels):
    """Сторінка «Етикетки» в довіднику цеху: пошук, змінні дата/партія/маса, друк на Zebra, PDF, ZPL."""
    import json
    e = html.escape
    for sub in ('pdf', 'zpl', 'png', 'png-hd'):
        os.makedirs(os.path.join(sitedir, sub), exist_ok=True)
    items = []
    for i, (l, src) in enumerate(labels):
        set_size(l)
        slug = f'{i + 1:02d}-{l["id"] or "inshi"}'
        for sub, ext in (('pdf', 'pdf'), ('zpl', 'zpl'), ('png', 'png'), ('png-hd', 'png')):
            shutil.copy(os.path.join(src, sub, l['_name'] + '.' + ext), os.path.join(sitedir, sub, slug + '.' + ext))
        title = ' '.join(l['title'])
        items.append((cat(l), f'<div class="it" data-c="{cat(l)}" data-q="{e(search_q(title))}" data-s="{slug}" data-w="{W}" data-h="{H}" data-f=\'{json.dumps(l["_slots"])}\'>'
                     f'<img src="png/{slug}.png" alt="" loading="lazy"><div><b>{e(title)}</b>'
                     f'<small>{e(l["std"])}{" · " + e(l["term"]) if l.get("term") else ""}{" · " + e(l["op"]) if l.get("op") else ""}</small><br>'
                     f'<a href="#" data-act="print">🖨 Друкувати на Zebra</a>'
                     f'<a class="z" href="#" data-act="zpl">ZPL з датою</a>'
                     f'<a class="z" href="pdf/{slug}.pdf" target="_blank">PDF без дати</a></div></div>'))
    groups, tabs = [], ['<button class="tab on" data-t="">Усі <span>' + str(len(items)) + '</span></button>']
    for k, name in CATS:
        g = [h for c, h in items if c == k]
        if not g:
            continue
        tabs.append(f'<button class="tab" data-t="{k}">{e(name)} <span>{len(g)}</span></button>')
        groups.append(f'<section class="grp" data-g="{k}"><h2>{e(name)}</h2>' + ''.join(g) + '</section>')
    page = f"""<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Етикетки · Цех · Риба Щодня</title><meta name="theme-color" content="#2e8b57"><style>{SITE_CSS}</style></head><body>
<header><a href="../">🐟 НАССР · Цех</a><small>Етикетки для принтера Zebra</small></header><main>
<h1>Етикетки</h1>
<div class="vars"><div class="row3">
<label>Дата виготовлення<input id="vDate" type="date"></label>
<label>Партія №<input id="vBatch" type="text" maxlength="14" placeholder="напр. 245"></label>
<label>Маса нетто, кг<input id="vMass" type="text" inputmode="decimal" maxlength="7" placeholder="можна порожньо"></label>
</div><div class="row3" style="margin-top:8px">
<label>Час пакування (фасовка)<input id="vTime" type="time"></label>
<label>Вжити до (фасовка)<input id="vUntil" type="text" maxlength="18"></label>
<span class="tip" style="align-self:end">Рахується саме: дата і час пакування + 72 год. Якщо строк партії закінчується раніше — виправте вручну.</span>
</div><label class="chk"><input id="vBlank" type="checkbox"> Друкувати без дати (порожні рядки, вписати ручкою)</label>
<p class="tip">Дата, партія і маса друкуються прямо на етикетці. Перевірте їх перед друком — вони однакові для всіх етикеток, які друкуєте зараз.</p></div>
<div class="how"><p><b>Як надрукувати:</b> заповніть дату (і партію), знайдіть товар і натисніть «🖨 Друкувати на Zebra». У вікні друку виберіть принтер
<b>ZDesigner…</b>, поля — «Немає», масштаб — <b>100 %</b>, і вкажіть кількість копій.
Фасовка 200 г друкується на етикетці 56 × 51 мм — перед друком вставте в принтер цей рулон.</p>
<p>«ZPL з датою» — файл з уже вписаною датою, для друку напряму через Zebra Setup Utilities («Send file»).</p></div>
<div class="tabs" id="tabs">{''.join(tabs)}</div>
<input id="q" type="search" placeholder="Пошук: оселедець, скумбрія, товстолоб…" autocomplete="off">
<div id="list">{''.join(groups)}</div><div id="res" hidden></div><p id="none" hidden>Нічого не знайдено. Спробуйте інше слово, наприклад лише назву риби.</p>
<p class="note" style="font-size:13px;color:#5b6873">Етикеток: {len(labels)}. Виробник — ТОВ «ФІШ-МАКСИМУМ ТРЕЙД»; морожена і сильносолена — ФОП Каменецький О. Л.; вкладка «Інші виробники» — етикетки постачальників без змін. Щоб змінити текст етикетки — напишіть, хто веде довідник (дані в src/etyketky.py).</p>
</main><script>
function $(i){{return document.getElementById(i)}}
(function(){{var d=new Date();d=new Date(d-d.getTimezoneOffset()*6e4);$('vDate').value=d.toISOString().slice(0,10);
try{{var b=localStorage.getItem('etk-batch');if(b)$('vBatch').value=b}}catch(e){{}}
var t0=new Date();$('vTime').value=('0'+t0.getHours()).slice(-2)+':'+('0'+t0.getMinutes()).slice(-2);
function calcUntil(){{var v=$('vDate').value,t=$('vTime').value||'00:00';if(!v){{$('vUntil').value='';return}}var p=v.split('-'),q=t.split(':');
var d=new Date(+p[0],+p[1]-1,+p[2],+q[0],+q[1]);d=new Date(d.getTime()+72*3600e3);
$('vUntil').value=('0'+d.getDate()).slice(-2)+'.'+('0'+(d.getMonth()+1)).slice(-2)+'.'+d.getFullYear()+' '+('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2)}}
$('vDate').addEventListener('change',calcUntil);$('vTime').addEventListener('change',calcUntil);calcUntil();
$('vBatch').addEventListener('change',function(){{try{{localStorage.setItem('etk-batch',this.value)}}catch(e){{}}}});}})();
function vals(){{if($('vBlank').checked)return {{}};var v=$('vDate').value,o={{}};
if(v){{var p=v.split('-');o.date=p[2]+'.'+p[1]+'.'+p[0]}}
var u=$('vUntil').value.trim();if(u)o.until=u;var b=$('vBatch').value.trim();if(b)o.batch=b;var m=$('vMass').value.trim().replace('.',',');if(m)o.mass=m;return o}}
function check(o){{if($('vBlank').checked)return true;if(!o.date){{alert('Вкажіть дату виготовлення');$('vDate').focus();return false}}return true}}
function loadImg(src){{return new Promise(function(ok,no){{var i=new Image();i.onload=function(){{ok(i)}};i.onerror=no;i.src=src}})}}
// hd=true — чітка картинка (у 3 рази більша) лише для перегляду на екрані; на принтер іде звичайна 1:1
function render(it,o,hd){{var K=hd?3:1;return loadImg((hd?'png-hd/':'png/')+it.dataset.s+'.png').then(function(im){{
var W=im.naturalWidth,H=im.naturalHeight;var c=document.createElement('canvas');c.width=W;c.height=H;var x=c.getContext('2d');x.drawImage(im,0,0);
var f=JSON.parse(it.dataset.f);x.fillStyle='#000';x.textBaseline='alphabetic';
Object.keys(o).forEach(function(k){{var s=f[k];if(!s)return;var x1=s[0],x2=s[1],y=s[2],fs=s[3]+2,t=o[k];
x1*=K;x2*=K;y*=K;var sz=fs*K;do{{x.font='bold '+sz+'px Arial, sans-serif';sz--}}while(x.measureText(t).width>x2-x1-6*K&&sz>10*K);
x.fillText(t,x1+4*K,y-K)}});
if(hd)return c;var d=x.getImageData(0,0,W,H),a=d.data;for(var i=0;i<a.length;i+=4){{var v=(a[i]+a[i+1]+a[i+2])/3<150?0:255;a[i]=a[i+1]=a[i+2]=v;a[i+3]=255}}
x.putImageData(d,0,0);return c}})}}
function preview(h,c){{var o=$('pv');if(o)o.remove();o=document.createElement('div');o.id='pv';o.style.cssText='position:fixed;inset:0;z-index:99;background:rgba(0,0,0,.75);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;box-sizing:border-box';var im=new Image();im.src=h.toDataURL('image/png');im.alt='Етикетка';im.style.cssText='background:#fff;width:min(70vw,calc(70vh*'+(h.width/h.height).toFixed(3)+'));height:auto;box-shadow:0 4px 24px rgba(0,0,0,.5)';var bar=document.createElement('div');bar.style.cssText='display:flex;gap:16px;margin-top:16px';var bs='font-size:24px;font-weight:bold;padding:14px 28px;border:0;border-radius:10px;cursor:pointer';var p=document.createElement('button');p.textContent='🖨 Друкувати';p.style.cssText=bs+';background:#2e8b57;color:#fff';var x=document.createElement('button');x.textContent='✕ Скасувати';x.style.cssText=bs+';background:#eee;color:#222';function close(){{o.remove();document.removeEventListener('keydown',kd)}}function kd(e){{if(e.key==='Escape')close();if(e.key==='Enter'){{close();printCanvas(c)}}}}p.onclick=function(){{close();printCanvas(c)}};x.onclick=close;o.onclick=function(e){{if(e.target===o)close()}};document.addEventListener('keydown',kd);bar.appendChild(p);bar.appendChild(x);o.appendChild(im);o.appendChild(bar);document.body.appendChild(o);p.focus()}}
function printCanvas(c){{var u=c.toDataURL('image/png'),mw=(c.width*25.4/203).toFixed(1)+'mm',mh=(c.height*25.4/203).toFixed(1)+'mm';var f=$('pf');if(f)f.remove();f=document.createElement('iframe');f.id='pf';
f.style.cssText='position:fixed;width:0;height:0;border:0;right:0;bottom:0';document.body.appendChild(f);
var d=f.contentWindow.document;d.open();d.write('<!DOCTYPE html><html><head><style>@page{{size:'+mw+' '+mh+';margin:0}}html,body{{margin:0;padding:0}}'+
'img{{display:block;width:'+mw+';height:'+mh+';image-rendering:pixelated}}</style></head><body><img src="'+u+'"></body></html>');d.close();
var im=d.querySelector('img');var go=function(){{f.contentWindow.focus();f.contentWindow.print()}};if(im.complete)go();else im.onload=go}}
function zpl(c,name){{var W=c.width,H=c.height,d=c.getContext('2d').getImageData(0,0,W,H).data,bpr=Math.ceil(W/8),h='',r,b,k,v,xx;
for(r=0;r<H;r++){{for(b=0;b<bpr;b++){{v=0;for(k=0;k<8;k++){{xx=b*8+k;v=(v<<1)|(xx<W&&d[(r*W+xx)*4]<128?1:0)}}h+=(v<16?'0':'')+v.toString(16).toUpperCase()}}h+='\\n'}}
var n=bpr*H,z='^XA\\n^PW'+W+'\\n^LL'+H+'\\n^LH0,0\\n^FO0,0^GFA,'+n+','+n+','+bpr+',\\n'+h+'^FS\\n^PQ1\\n^XZ\\n';
var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([z],{{type:'text/plain'}}));a.download=name+'.zpl';document.body.appendChild(a);a.click();a.remove()}}
document.querySelector('main').addEventListener('click',function(ev){{var a=ev.target.closest('.it [data-act]');if(!a)return;ev.preventDefault();
var it=a.closest('.it'),o=vals();if(!check(o))return;
render(it,o).then(function(c){{if(a.dataset.act==='print')printCanvas(c);else zpl(c,it.dataset.s+(o.date?'-'+o.date:''))}})}});
var TAB='',ITS=[].slice.call(document.querySelectorAll('.it')),GRS=[].slice.call(document.querySelectorAll('.grp'));
// пошук не розрізняє укр./рос. літери: і ї и ы → и, є е э ё → е, ґ → г; апострофи ігноруються
function nz(s){{return s.toLowerCase().replace(/[ʼ’'`"«»ъ]/g,'').replace(/[іїиы]/g,'и').replace(/[єеэё]/g,'е').replace(/ґ/g,'г')}}
ITS.forEach(function(d){{d._q=nz(d.dataset.q);d._t=nz(d.querySelector('b').textContent);d._g=d.parentNode}});
// слово з пошуку має збігатися з ПОЧАТКОМ слова в назві: «л» → лосось, лящ…, а не все, де є літера «л»
function pre(q,w){{var i=q.indexOf(w);while(i>=0){{if(i===0||' («-/'.indexOf(q.charAt(i-1))>=0)return true;i=q.indexOf(w,i+1)}}return false}}
var SR=false;
// у вкладці «Усі» шукаємо по всіх товарах, в інших вкладках — лише в цій групі; результат одним списком за алфавітом (спершу назви, що починаються з введеного); без тексту — вибрана вкладка
function filt(){{var raw=$('q').value.trim(),v=raw?nz(raw).split(/\s+/):[],n=0,hit=[];
if(!v.length&&SR){{ITS.forEach(function(d){{d._g.appendChild(d)}});SR=false}}
ITS.forEach(function(d){{var ok=(!TAB||d.dataset.c===TAB)&&v.every(function(w){{return pre(d._q,w)}});if(ok){{n++;hit.push(d)}}if(d.hidden===ok)d.hidden=!ok}});
if(v.length){{var f=v[0];hit.sort(function(a,b){{var x=a._t.indexOf(f)===0?0:1,y=b._t.indexOf(f)===0?0:1;return x-y||a._t.localeCompare(b._t,'uk')}});
hit.forEach(function(d){{$('res').appendChild(d)}});SR=true}}
$('list').hidden=!!v.length;$('res').hidden=!v.length;
GRS.forEach(function(g){{var ok=!!g.querySelector('.it:not([hidden])');if(g.hidden===ok)g.hidden=!ok}});
$('none').hidden=n>0}}
var tm;$('q').addEventListener('input',function(){{clearTimeout(tm);tm=setTimeout(filt,200)}});
$('tabs').addEventListener('click',function(ev){{var b=ev.target.closest('.tab');if(!b)return;TAB=b.dataset.t;
[].forEach.call(this.children,function(x){{x.classList.toggle('on',x===b)}});try{{localStorage.setItem('etk-tab',TAB)}}catch(e){{}}filt()}});
try{{var st=localStorage.getItem('etk-tab');if(st){{var bb=document.querySelector('.tab[data-t="'+st+'"]');if(bb)bb.click()}}}}catch(e){{}}
</script></body></html>"""
    open(os.path.join(sitedir, 'index.html'), 'w').write(page)


if __name__ == '__main__':
    # python3 src/gen_etyketky.py <outDir> [--site vyrobnytstvo/etyketky]
    a = sys.argv[1:]
    sitedir = None
    if '--site' in a:
        k = a.index('--site'); sitedir = a[k + 1]; del a[k:k + 2]
    out = os.path.abspath(a[0] if a else 'etyketky')
    main(out)
    if sitedir:
        for l in E.LABELS:
            l['_name'] = l['file'].strip().replace('  ', ' ')
        site(sitedir, [(l, out) for l in E.LABELS])
