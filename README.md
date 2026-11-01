# Довідник НАССР · Риба Щодня

Довідник для працівників магазинів: питання-відповіді, бланки для друку, QR-наклейки.

Адреса: https://fisheverydaybot-cmd.github.io/dovidnyk/

- Текст довідника: `src/content.md` (з документа «Довідник НАССР для працівників магазинів»).
- Зібрати сайт: `python3 src/build.py .` (створює `index.html` у корені).
- Згенерувати PDF бланків (для друку з телефона): `node src/gen_pdf.js .` (потрібен Playwright; створює папку `pdf/`).
- Картки продукції для покупців (QR на етикетці): дані в `src/products.py`, зібрати `python3 src/gen_products.py .` (потрібен пакет segno). Створює `p/<id>/`, список `p/` і аркуш QR `p/qr.html`.
- QR-генератор: qrcode-generator (Kazuhiko Arase, MIT).

## Довідник для виробництва (цех)

Адреса: https://fisheverydaybot-cmd.github.io/dovidnyk/vyrobnytstvo/

- Текст: `src/vyrobnytstvo/content.md`, бланки і цех: `src/vyrobnytstvo/data.js`, блок-схеми: `src/vyrobnytstvo/img/`.
- Рушій спільний з довідником магазинів (`src/app.js`, `src/template.html`).
- Зібрати: `python3 src/vyrobnytstvo/build.py vyrobnytstvo`, PDF бланків: `node src/vyrobnytstvo/gen_pdf.js vyrobnytstvo`.
