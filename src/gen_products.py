# python gen_products.py <siteDir> — генерує картки продукції p/<id>/ , список p/ , QR-коди p/qr/
import os, sys, html, importlib.util
import segno

d = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('products', os.path.join(d, 'products.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
P = m.PRODUCTS
out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
BASE = 'https://fisheverydaybot-cmd.github.io/dovidnyk/p/'
e = html.escape

CSS = """*{box-sizing:border-box}body{margin:0;font:17px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#1d2730;background:#f4f7f8}
header{background:#0b5d7a;color:#fff;padding:14px 16px}header a{color:#fff;text-decoration:none;font-weight:700;font-size:19px}header small{display:block;opacity:.8;font-size:13px}
main{max-width:680px;margin:0 auto;padding:16px 14px 50px}
h1{font-size:26px;line-height:1.25;margin:4px 0 2px}h2{font-size:15px;text-transform:uppercase;letter-spacing:.04em;color:#5b6873;margin:18px 0 6px}.lat{color:#5b6873;font-style:italic;margin:0 0 14px}
.card{background:#fff;border:1px solid #d7dee3;border-radius:14px;padding:4px 16px;margin-bottom:12px}
.row{padding:12px 0;border-bottom:1px solid #edf1f3}.row:last-child{border-bottom:0}
.k{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#0b5d7a;font-weight:700;margin-bottom:2px}
table{border-collapse:collapse;width:100%}td{padding:6px 0;border-bottom:1px solid #edf1f3}td:last-child{text-align:right;font-weight:600}
.note{font-size:13px;color:#5b6873}.ph{margin:12px 0}.ph img{width:100%;height:auto;border-radius:14px;display:block;background:#dde5e9}.ph figcaption{font-size:13px;color:#5b6873;margin-top:4px}.alg{background:#fff4dc;border-radius:10px;padding:10px 12px}
ul.list{list-style:none;padding:0}ul.list a{display:block;background:#fff;border:1px solid #d7dee3;border-radius:12px;padding:13px 14px;margin-bottom:8px;color:#1d2730;text-decoration:none;font-weight:600}
ul.list small{display:block;font-weight:400;color:#5b6873}
.sheet{display:grid;grid-template-columns:repeat(4,1fr);gap:4mm}.lbl{border:1px dashed #999;border-radius:6px;padding:3mm;text-align:center;break-inside:avoid;background:#fff}
.lbl img{width:28mm;height:28mm}.lbl div{font-size:9pt;font-weight:700;line-height:1.2}.lbl small{font-size:7pt;color:#444}
.btn{background:#0b5d7a;color:#fff;border:0;border-radius:10px;padding:10px 16px;font:inherit;font-weight:600;cursor:pointer}
@media print{header,.noprint{display:none}body{background:#fff}main{max-width:none;padding:0}@page{size:A4;margin:10mm}}"""

def page(title, body, back=True):
    return f"""<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Риба Щодня</title><meta name="theme-color" content="#0b5d7a"><style>{CSS}</style></head><body>
<header><a href="{'../' if back else './'}">🐟 Риба Щодня</a><small>Про нашу продукцію</small></header><main>{body}</main></body></html>"""

SMOKE = {
 'hot': '<div><b>Гаряче копчення</b>: дим 80–140 °C, кілька годин. Білок зварюється, тому мʼясо мʼяке, соковите, легко відходить від кістки. Продукт швидкопсувний: зберігайте в холодильнику від −2 до +2 °C і зʼїжте якнайшвидше (строк — на етикетці).</div><p class="note">Для порівняння: холодне копчення — дим до 40 °C протягом кількох діб, мʼясо щільне й пружне, зберігається довше.</p>',
 'cold': '<div><b>Холодне копчення</b>: дим не вище 40 °C, кілька діб. Риба не вариться, а повільно просочується димом і підсушується, тому мʼясо щільне, пружне, ріжеться тонкими шматочками. Зберігається довше, ніж гаряче копчення (строк — на етикетці).</div><p class="note">Для порівняння: гаряче копчення — дим 80–140 °C кілька годин, мʼясо мʼяке, строк зберігання — лише кілька діб.</p>'}

def row(k, v): return f'<div class="row"><div class="k">{e(k)}</div>{v}</div>'

FISH = m.FISH
for p in P:
    fi = FISH[p['fk']]
    p.setdefault('fish', fi['name']); p.setdefault('latin', fi['latin'])

def nutr_table(p):
    b, f, c, kcal = p['nutr']
    num = lambda x: str(x).replace('.', ',')
    t = (f'<table><tr><td>Енергетична цінність</td><td>{kcal} ккал / {round(kcal * 4.184)} кДж</td></tr>'
         f'<tr><td>Білки</td><td>{num(b)} г</td></tr><tr><td>Жири</td><td>{num(f)} г</td></tr>')
    if c is not None:
        t += f'<tr><td>Вуглеводи</td><td>{num(c)} г</td></tr>'
    note = ('На 100 г продукту, як на етикетці виробника.' if c is None
            else 'На 100 г продукту. Орієнтовні дані за довідковими таблицями.')
    return t + f'</table><p class="note">{note}</p>'

def photo(fk):
    # фото сировини: покладіть p/img/<ключ риби>.jpg (ключі — FISH у products.py), підпис/автор — FISH[fk]['photo']
    for ext in ('jpg', 'jpeg', 'png', 'webp'):
        if os.path.exists(f'{out}/p/img/{fk}.{ext}'):
            cap = FISH[fk].get('photo', FISH[fk]['name'] + ' — сировина')
            return f'<figure class="ph"><img src="../img/{fk}.{ext}" alt="{e(FISH[fk]["name"])}" loading="lazy"><figcaption>{e(cap)}</figcaption></figure>'
    return ''

os.makedirs(f'{out}/p/qr', exist_ok=True)
for p in P:
    fi = FISH[p['fk']]
    same = [o for o in P if o['fk'] == p['fk'] and o is not p]
    more = ('<ul class="list">' + ''.join(f'<li><a href="../{o["id"]}/">{e(o["name"])}</a></li>' for o in same) + '</ul>') if same else ''
    # порядок: продукт → про рибу (опис) → фото сировини (фото внизу, щоб не плутали з готовим продуктом)
    body = (f'<h1>{e(p["name"])}</h1><p class="lat">{e(fi["name"])} · {e(fi["latin"])}</p>'
            '<h2>Про продукт</h2><div class="card">' +
            row('Що це', f'<div>{e(p["category"])}</div>') +
            row('Як виготовлено', f'<div>{e(p["method"])}</div>') +
            (row('Гаряче чи холодне копчення?', SMOKE[p['smoke']]) if p.get('smoke') else '') +
            row('Склад', f'<div>{e(p["composition"])}</div>') +
            row('Харчова цінність', nutr_table(p)) +
            row('Алергени', '<div class="alg">Містить <b>' + fi.get('allergen', 'рибу') + '</b>' + (' і <b>гірчицю</b>' if 'гірчиц' in p['composition'].lower() else '') + '.</div>') +
            row('Як подавати', f'<div>{e(p["serve"])}</div>') +
            f'</div><h2>{e(fi.get("about", "Про рибу"))}</h2><div class="card">' +
            row(fi.get('kind', 'Риба'), f'<div>{e(fi["name"])} <i>({e(fi["latin"])})</i></div>') +
            row('Родина', f'<div>{e(fi["family"])}</div>') +
            row('Де ловлять', f'<div>{e(fi["habitat"])}</div>') +
            row('Чим корисна', f'<div>{e(fi["value"])}</div>') +
            '</div>' + photo(p['fk']) + (f'<h2>Що ще ми робимо з цієї риби</h2>{more}' if more else '') +
            '<p class="note">Виробник, дата виготовлення, номер партії, умови і строк зберігання вказані на етикетці товару.</p>')
    os.makedirs(f'{out}/p/{p["id"]}', exist_ok=True)
    open(f'{out}/p/{p["id"]}/index.html', 'w').write(page(p['name'], body))
    q = segno.make(BASE + p['id'] + '/', error='m')
    q.save(f'{out}/p/qr/{p["id"]}.svg', scale=4, border=2)
    q.save(f'{out}/p/qr/{p["id"]}.png', scale=12, border=2)

groups = {}
for p in P:
    groups.setdefault(p['fk'], []).append(p)
lst = '<h1>Наша продукція</h1>' + ''.join(
    f'<h2>{e(FISH[k]["name"])}</h2><ul class="list">' + ''.join(
        f'<li><a href="{p["id"]}/">{e(p["name"])}<small>{e(p["category"])}</small></a></li>' for p in ps) + '</ul>'
    for k, ps in groups.items())
open(f'{out}/p/index.html', 'w').write(page('Наша продукція', lst, back=False))

sheet = ('<div class="noprint"><h1>QR-коди для етикеток</h1><p class="note">Для персоналу. Кожен код веде на картку товару. '
         'Окремий файл коду (PNG/SVG) — натисніть на назву.</p><p><button class="btn" onclick="print()">Друкувати аркуш</button></p></div><div class="sheet">' +
         ''.join(f'<div class="lbl"><img src="qr/{p["id"]}.svg" alt=""><div>{e(p["name"])}</div><small class="noprint"><a href="qr/{p["id"]}.png" download>PNG</a> · <a href="qr/{p["id"]}.svg" download>SVG</a></small></div>' for p in P) + '</div>')
open(f'{out}/p/qr.html', 'w').write(page('QR-коди для етикеток', sheet, back=False).replace('href="./">🐟', 'href="./">🐟'))
print('products', len(P))
