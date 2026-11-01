# python3 src/gen_etyketky.py <outDir>
# Етикетки цеху для Zebra LP 2824 Plus (203 dpi, 57,3×41 мм) з QR на картку продукції.
# Створює: <outDir>/pdf/<назва>.pdf (кожна етикетка), <outDir>/vsi-etyketky.pdf (усі, по одній на сторінку),
#          <outDir>/zrazky-A4.pdf (огляд на аркушах A4), <outDir>/zpl/<назва>.zpl (друк напряму на Zebra),
#          <outDir>/png/<назва>.png (картинка 1:1 у точках принтера).
# Потрібні пакети: pillow, reportlab, segno.
import os, sys, importlib.util
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
M = 9                    # поле
QM = 3                   # розмір модуля QR у точках (0,375 мм)
FONTS = {False: '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf',
         True: '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'}
_fc = {}


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
    while max(tw([(t, True)], ts) for t in l['title']) > full and ts > 18:
        ts -= 1
    for t in l['title']:
        y += ts - 3
        ops.append(('text', (W - tw([(t, True)], ts)) / 2, y, ts, [(t, True)]))
    y += 3
    # стандарт
    y += body
    ops.append(('text', (W - tw([(l['std'], False)], body)) / 2, y, body, [(l['std'], False)]))
    lh = body + 1
    fish, rest = l['comp'].split(',', 1) if ',' in l['comp'] else (l['comp'], '')
    paras = [[('Склад: ', False), (fish, True), (',' + rest + '.' if rest else '.', False)]]
    if l['salt']:
        paras.append([('Ступінь солоності: ' + l['salt'] + '.', False)])
    lo, hi = l['t']
    paras.append([(f'Зберігати при t від {deg(lo)} до {deg(hi)} °C. Термін придатності {l["term"].rstrip(".")}.', False)])
    b = str(l['b']).replace('.', ',')
    paras.append([(f'Поживна цінність 100 г: білки {b} г, жири {l["f"]} г.', False)])
    paras.append([(f'Енергетична цінність 100 г: {l["kcal"]} ккал / {round(l["kcal"] * 4.184)} кДж.', False)])
    for p in paras:
        for ln in wrap(p, body, full):
            y += lh
            ops.append(('text', M, y, body, ln))
    # нижній блок: ліворуч поля і виробник, праворуч QR
    q = segno.make(BASE + l['id'] + '/', error='m')
    mat = [list(r) for r in q.matrix_iter(border=0)]
    qs = len(mat) * QM
    qx, qy = W - M - qs, H - M - qs + 2
    ops.append(('qr', qx, qy, mat))
    cap = 'Про рибу'
    ops.append(('text', qx + (qs - tw([(cap, True)], 14)) / 2, qy - 4, 14, [(cap, True)]))
    left = qx - M - 10
    fs = body - 1
    fl = fs + 1
    bottom = [
        ('field', 'Маса нетто', 'кг'),
        ('field', 'Дата виготовлення', ''),
        ('field', 'Партія №', ''),
        ('text', [('Виробник: ', False), (E.OPERATOR, True)]),
        ('text', [(E.ADDRESS, False)]),
        ('text', [('тел. ' + E.PHONE + '      без ГМО', False)]),
    ]
    by = H - M - len(bottom) * fl + fs - 2
    if by - fs < y + 2 or qy - 18 < y:
        return None
    for it in bottom:
        if it[0] == 'field':
            _, lab, unit = it
            ops.append(('text', M, by, fs, [(lab, False)]))
            x1 = M + tw([(lab, False)], fs) + 4
            x2 = left - (tw([(unit, False)], fs) + 4 if unit else 0)
            if unit:
                ops.append(('text', x2 + 4, by, fs, [(unit, False)]))
            ops.append(('rule', x1, x2, by + 1))
        else:
            segs = it[1]
            s = fs
            while tw(segs, s) > left - M and s > 12:
                s -= 1
            ops.append(('text', M, by, s, segs))
        by += fl
    return ops


def fit(l):
    for body in (20, 19, 18, 17, 16, 15, 14, 13):
        ops = layout(l, body)
        if ops:
            return ops
    raise SystemExit('не влазить: ' + l['file'])


def render_png(ops):
    im = Image.new('1', (W, H), 1)
    dr = ImageDraw.Draw(im)
    dr.fontmode = '1'
    for op in ops:
        if op[0] == 'text':
            _, x, y, s, segs = op
            for t, b in segs:
                dr.text((x, y), t, font=font(s, b), fill=0, anchor='ls')
                x += font(s, b).getlength(t)
        elif op[0] == 'rule':
            _, x1, x2, y = op
            dr.line([(x1, y), (x2, y)], fill=0, width=1)
        elif op[0] == 'qr':
            _, x, y, mat = op
            x, y = round(x), round(y)
            for r, row in enumerate(mat):
                for c, v in enumerate(row):
                    if v:
                        dr.rectangle([x + c * QM, y + r * QM, x + c * QM + QM - 1, y + r * QM + QM - 1], fill=0)
    return im


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


def main(out):
    for sub in ('pdf', 'zpl', 'png'):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    allc = canvas.Canvas(os.path.join(out, 'vsi-etyketky.pdf'), pagesize=(W * PT, H * PT))
    allc.setTitle('Етикетки ТОВ «ФІШ-МАКСИМУМ ТРЕЙД»')
    a4 = canvas.Canvas(os.path.join(out, 'zrazky-A4.pdf'), pagesize=(210 * mm, 297 * mm))
    a4.setTitle('Етикетки — огляд на A4')
    cols, rows_ = 3, 6
    gx, gy = (210 * mm - cols * W * PT) / (cols + 1), (297 * mm - rows_ * H * PT) / (rows_ + 1)
    for i, l in enumerate(E.LABELS):
        ops = fit(l)
        name = l['file'].strip().replace('  ', ' ')
        im = render_png(ops)
        im.save(os.path.join(out, 'png', name + '.png'))
        open(os.path.join(out, 'zpl', name + '.zpl'), 'w', encoding='ascii').write(zpl(im))
        c = canvas.Canvas(os.path.join(out, 'pdf', name + '.pdf'), pagesize=(W * PT, H * PT))
        c.setTitle(name); draw_pdf(c, ops); c.showPage(); c.save()
        draw_pdf(allc, ops); allc.showPage()
        k = i % (cols * rows_)
        if i and k == 0:
            a4.showPage()
        cx = gx + (k % cols) * (W * PT + gx)
        cy = 297 * mm - (k // cols + 1) * (H * PT + gy)
        a4.setLineWidth(0.3); a4.setStrokeGray(0.6)
        a4.roundRect(cx, cy, W * PT, H * PT, 2 * mm, stroke=1, fill=0)
        a4.setStrokeGray(0)
        draw_pdf(a4, ops, cx, cy)
    allc.save(); a4.showPage(); a4.save()
    print('етикеток:', len(E.LABELS))


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'etyketky'))
