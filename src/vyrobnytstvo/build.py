# Збирає довідник для виробництва: python3 src/vyrobnytstvo/build.py vyrobnytstvo
# Рушій (app.js, template.html) спільний з довідником магазинів; тут лише дані і тексти.
import json, os, re, shutil, sys
d = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(d)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(d, 'dist')
os.makedirs(out, exist_ok=True)

t = open(f'{src}/template.html').read()
md = open(f'{d}/content.md').read()
qr = open(f'{src}/package/qrcode.js').read()
app = open(f'{src}/app.js').read()
data = open(f'{d}/data.js').read()

# 1) дані магазинів -> дані цеху
cut = app.index('// ---------- Утиліти')
app = data + '\n' + app[cut:]

# 2) окремі ключі localStorage, щоб не змішувати з довідником магазинів
app = app.replace("localStorage.getItem(k)", "localStorage.getItem('vyr-' + k)").replace("localStorage.setItem(k, v)", "localStorage.setItem('vyr-' + k, v)")

def rep(old, new, count=1):
    global app
    assert app.count(old) >= 1, old
    app = app.replace(old, new) if count == 0 else app.replace(old, new, count)

# один цех: обирається автоматично
rep("  return s || null;", "  return s || (SHOPS.length === 1 ? SHOPS[0] : null);")
rep("<label>Магазин<select", "<label>Цех<select")
rep("Оберіть магазин — його адреса й оператор будуть у шапці бланка.", "Оберіть оператора (ТОВ або ФОП) — він буде в шапці бланка.")
rep("<div>Магазин «Риба Щодня», ", "<div>Рибопереробний цех «Риба Щодня», ")
rep("Відкрийте посилання з групи магазину.", "Відкрийте посилання з групи цеху.")
rep("Для старшого продавця:", "Для начальника дільниці:")
rep("Наклейте їх на морозильник, вітрину, біля рукомийника", "Наклейте їх на посолочні ємності, коптильну камеру, камеру вʼялення, камери зберігання, біля рукомийника")
rep("'https://fisheverydaybot-cmd.github.io/dovidnyk/'", "'https://fisheverydaybot-cmd.github.io/dovidnyk/vyrobnytstvo/'")
rep("Не знайшли відповіді? Зателефонуйте старшому продавцю або технологу.", "Не знайшли відповіді або показник поза нормою? Зупиніть процес і зателефонуйте технологу або начальнику дільниці.")
rep('<div class="p-s">Риба Щодня</div>', '<div class="p-s">Риба Щодня · виробництво</div>')
rep("<li>що робити, якщо щось пішло не так</li><li>температури, строки, прибирання, гігієна</li><li>бланки і журнали для друку</li>",
    "<li>посол, тузлук, копчення, вʼялення: режими</li><li>ККТ, температури, строки, миття, відходи</li><li>журнали і чек-листи для друку</li>")
rep("Наведіть камеру телефону · Риба Щодня", "Наведіть камеру телефону · Риба Щодня, цех")
app = re.sub(r"var ICONS = \{[^}]*\};", "var ICONS = { '1': '📦', '2': '❄️', '3': '🧂', '4': '🔥', '5': '🌬️', '6': '📋', '7': '🏷️', '8': '🚚', '9': '🧽', '10': '🧼', '11': '🗑️', '12': '🐀', '13': '⚠️', '14': '📚' };", app)
# пошук: різні апострофи -> ʼ
if "var t = term.toLowerCase().trim();" in app:
    rep("var t = term.toLowerCase().trim();", "var t = term.toLowerCase().trim().replace(/['’`]/g, 'ʼ');")
# картинки в тексті: ![підпис](img/файл.png)
rep("    if (/^(Бланк|Документ):/.test(l)) {",
    "    var im = /^!\\[(.*)\\]\\((.+)\\)$/.exec(l);\n    if (im) { out.push('<figure class=\"pic\"><a href=\"' + esc(im[2]) + '\" target=\"_blank\"><img src=\"' + esc(im[2]) + '\" alt=\"' + esc(im[1]) + '\" loading=\"lazy\"></a><figcaption>' + inline(im[1]) + '</figcaption></figure>'); i++; continue; }\n    if (/^(Бланк|Документ):/.test(l)) {")

t = t.replace('<title>Довідник НАССР · Риба Щодня</title>', '<title>Довідник НАССР · Виробництво · Риба Щодня</title>')
t = t.replace('<a href="#" id="home">🐟 Довідник НАССР</a><small>Риба Щодня · чернетка</small>', '<a href="#" id="home">🐟 НАССР · Цех</a><small>Риба Щодня · виробництво · чернетка</small>')
t = t.replace('placeholder="Пошук: морожена, дезрозчин, скарга…"', 'placeholder="Пошук: тузлук, скумбрія, копчення, відходи…"')
t = t.replace('</style>\n</head>', '.pic{margin:12px 0}.pic img{width:100%;height:auto;border:1px solid var(--line);border-radius:10px;background:#fff}.pic figcaption{font-size:13px;color:var(--q)}\n</style>\n</head>')
# світліша зелена гама, щоб цех відрізнявся від магазинів (синя)
for a, b in [('#0b5d7a', '#2e8b57'), ('#e8f3f7', '#e9f6ee'), ('#9cc7d6', '#a8d8b9'), ('#c6e0ea', '#cfe9d8'), ('#f6f8f9', '#f5faf7')]:
    assert a in t, a
    t = t.replace(a, b)
assert 'НАССР · Цех' in t and '.pic{' in t

for x in (md, qr, app): assert '</script' not in x.lower()
html = t.replace('__CONTENT__', md).replace('__QRLIB__', qr).replace('__APP__', app)
open(f'{out}/index.html', 'w').write(html)
open(f'{out}/manifest.webmanifest', 'w').write(json.dumps({"name": "НАССР · Цех · Риба Щодня", "short_name": "НАССР цех", "start_url": ".", "display": "standalone", "background_color": "#f5faf7", "theme_color": "#2e8b57", "lang": "uk", "icons": [{"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"}]}, ensure_ascii=False, indent=1))
open(f'{out}/icon.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#2e8b57"/><text x="32" y="44" font-size="34" text-anchor="middle">🐟</text></svg>')
open(f'{out}/sw.js', 'w').write("""const C='vyrobnytstvo-v2';const F=['./','index.html','manifest.webmanifest','icon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x.startsWith('vyrobnytstvo-')&&x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('index.html'))))});
""")
if os.path.isdir(f'{d}/img'):
    shutil.copytree(f'{d}/img', f'{out}/img', dirs_exist_ok=True)
print('ok', len(html))
