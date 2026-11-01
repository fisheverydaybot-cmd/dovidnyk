import json, os, sys
d=os.path.dirname(os.path.abspath(__file__))
out=sys.argv[1] if len(sys.argv)>1 else os.path.join(d,'dist')
os.makedirs(out,exist_ok=True)
t=open(f'{d}/template.html').read()
md=open(f'{d}/content.md').read()
qr=open(f'{d}/package/qrcode.js').read()
app=open(f'{d}/app.js').read()
for x in (md,qr,app): assert '</script' not in x.lower()
html=t.replace('__CONTENT__',md).replace('__QRLIB__',qr).replace('__APP__',app)
open(f'{out}/index.html','w').write(html)
open(f'{out}/manifest.webmanifest','w').write(json.dumps({"name":"Довідник НАССР · Риба Щодня","short_name":"НАССР","start_url":".","display":"standalone","background_color":"#f6f8f9","theme_color":"#0b5d7a","lang":"uk","icons":[{"src":"icon.svg","sizes":"any","type":"image/svg+xml"},{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png"}]},ensure_ascii=False,indent=1))
open(f'{out}/icon.svg','w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0b5d7a"/><text x="32" y="44" font-size="34" text-anchor="middle">🐟</text></svg>')
open(f'{out}/sw.js','w').write("""const C='dovidnyk-v6';const F=['./','index.html','manifest.webmanifest','icon.svg','icon-192.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('index.html'))))});
""")
print('ok',len(html))
