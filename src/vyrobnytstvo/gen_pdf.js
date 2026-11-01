// node src/vyrobnytstvo/gen_pdf.js vyrobnytstvo — генерує pdf/<бланк>--tsekh-<оператор>.pdf для телефонів
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
const dir=path.resolve(process.argv[2]||'vyrobnytstvo');fs.mkdirSync(dir+'/pdf',{recursive:true});
const html=fs.readFileSync(dir+'/index.html','utf8');
const FORMS=[...html.matchAll(/\{ id: '([a-z-]+)', title:/g)].map(m=>m[1]);
const OPS=['ТОВ «ФІШ МАКСИМУМ ТРЕЙД»','ФОП Каменецький Олексій Леонідович'];
(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.emulateMedia({media:'print'});
const url='file://'+dir+'/index.html';let c=0;
for(let i=0;i<OPS.length;i++){await p.goto(url);
 await p.evaluate(([op])=>{localStorage.clear();localStorage.setItem('vyr-shop','tsekh');localStorage.setItem('vyr-op-tsekh',op);},[OPS[i]]);
 await p.goto(url+'#blanky');await p.reload();await p.evaluate(()=>{window.print=()=>{}});
 for(const f of FORMS){await p.evaluate(f=>window.__dovForm(f),f);await p.waitForTimeout(80);
  await p.pdf({path:dir+'/pdf/'+f+'--tsekh-'+i+'.pdf',preferCSSPageSize:true});c++;}}
console.log('pdf',c,FORMS.join(' '));await b.close();})();
