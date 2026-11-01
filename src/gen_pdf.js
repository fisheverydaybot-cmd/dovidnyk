// node gen_pdf.js <siteDir> — генерує pdf/<бланк>[--<магазин>-<оператор>].pdf
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
const dir=path.resolve(process.argv[2]||'.');fs.mkdirSync(dir+'/pdf',{recursive:true});
const SH={'geroiv-oon':1,'zinkivska':1,'honchara':2,'mazepy':2,'kooperatyvna':2};
const FORMS=['chek-zminy','pryimannya','akt','prybyrannya','oznaiomlennya','vidkhylennya','medohlyady','vidviduvachi','obladnannya'];
const OPS={honchara:['ТОВ «ФІШ МАКСИМУМ ТРЕЙД»','ФОП Мирний Андрій Олександрович'],mazepy:['ТОВ «ФІШ МАКСИМУМ ТРЕЙД»','ФОП Коваленко Валентина Порфирівна'],kooperatyvna:['ТОВ «ФІШ МАКСИМУМ ТРЕЙД»','ФОП Анікеєва Наталя Миколаївна']};
(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.emulateMedia({media:'print'});
const url='file://'+dir+'/index.html';const variants=[[null,0]];
for(const [s,n] of Object.entries(SH))for(let i=0;i<n;i++)variants.push([s,i]);
let c=0;
for(const [s,i] of variants){await p.goto(url);
 await p.evaluate(([s,i,ops])=>{localStorage.clear();if(s){localStorage.setItem('shop',s);if(ops)localStorage.setItem('op-'+s,ops[i]);}window.print=()=>{};},[s,i,OPS[s]||null]);
 await p.goto(url+'#blanky');await p.reload();await p.evaluate(()=>{window.print=()=>{}});
 for(const f of FORMS){await p.evaluate(f=>window.__dovForm(f),f);await p.waitForTimeout(80);
  const name=f+(s?'--'+s+'-'+i:'')+'.pdf';await p.pdf({path:dir+'/pdf/'+name,preferCSSPageSize:true});c++;}}
console.log('pdf',c);await b.close();})();
