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
h1{font-size:26px;line-height:1.25;margin:4px 0 2px}.lat{color:#5b6873;font-style:italic;margin:0 0 14px}
.card{background:#fff;border:1px solid #d7dee3;border-radius:14px;padding:4px 16px;margin-bottom:12px}
.row{padding:12px 0;border-bottom:1px solid #edf1f3}.row:last-child{border-bottom:0}
.k{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#0b5d7a;font-weight:700;margin-bottom:2px}
table{border-collapse:collapse;width:100%}td{padding:6px 0;border-bottom:1px solid #edf1f3}td:last-child{text-align:right;font-weight:600}
.note{font-size:13px;color:#5b6873}.alg{background:#fff4dc;border-radius:10px;padding:10px 12px}
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

def row(k, v): return f'<div class="row"><div class="k">{e(k)}</div>{v}</div>'

os.makedirs(f'{out}/p/qr', exist_ok=True)
for p in P:
    b, f, c, kcal = p['nutr']
    kj = round(kcal * 4.184)
    nut = (f'<table><tr><td>Енергетична цінність</td><td>{kcal} ккал / {kj} кДж</td></tr><tr><td>Білки</td><td>{str(b).replace('.',',')} г</td></tr>'
           f'<tr><td>Жири</td><td>{str(f).replace('.',',')} г</td></tr><tr><td>Вуглеводи</td><td>{c} г</td></tr></table>'
           '<p class="note">На 100 г продукту. Орієнтовні дані за довідковими таблицями.</p>')
    body = (f'<h1>{e(p["name"])}</h1><p class="lat">{e(p["fish"])} · {e(p["latin"])}</p><div class="card">' +
            row('Де водиться', f'<div>{e(p["habitat"])}</div>') +
            row('Категорія', f'<div>{e(p["category"])}</div>') +
            row('Як виготовлено', f'<div>{e(p["method"])}</div>') +
            row('Склад', f'<div>{e(p["composition"])}</div>') +
            row('Харчова цінність', nut) +
            row('Алергени', '<div class="alg">Містить <b>рибу</b>.</div>') +
            row('Як подавати', f'<div>{e(p["serve"])}</div>') +
            '</div><p class="note">Виробник, дата виготовлення, номер партії, умови і строк зберігання вказані на етикетці товару.</p>')
    os.makedirs(f'{out}/p/{p["id"]}', exist_ok=True)
    open(f'{out}/p/{p["id"]}/index.html', 'w').write(page(p['name'], body))
    q = segno.make(BASE + p['id'] + '/', error='m')
    q.save(f'{out}/p/qr/{p["id"]}.svg', scale=4, border=2)
    q.save(f'{out}/p/qr/{p["id"]}.png', scale=12, border=2)

lst = '<h1>Наша продукція</h1><ul class="list">' + ''.join(
    f'<li><a href="{p["id"]}/">{e(p["name"])}<small>{e(p["category"])}</small></a></li>' for p in P) + '</ul>'
open(f'{out}/p/index.html', 'w').write(page('Наша продукція', lst, back=False))

sheet = ('<div class="noprint"><h1>QR-коди для етикеток</h1><p class="note">Для персоналу. Кожен код веде на картку товару. '
         'Окремий файл коду (PNG/SVG) — натисніть на назву.</p><p><button class="btn" onclick="print()">Друкувати аркуш</button></p></div><div class="sheet">' +
         ''.join(f'<div class="lbl"><img src="qr/{p["id"]}.svg" alt=""><div>{e(p["name"])}</div><small class="noprint"><a href="qr/{p["id"]}.png" download>PNG</a> · <a href="qr/{p["id"]}.svg" download>SVG</a></small></div>' for p in P) + '</div>')
open(f'{out}/p/qr.html', 'w').write(page('QR-коди для етикеток', sheet, back=False).replace('href="./">🐟', 'href="./">🐟'))
print('products', len(P))
