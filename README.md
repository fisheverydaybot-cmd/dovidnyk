# Довідник НАССР · Риба Щодня

Довідник для працівників магазинів: питання-відповіді, бланки для друку, QR-наклейки.

Адреса: https://fisheverydaybot-cmd.github.io/dovidnyk/

- Текст довідника: `src/content.md` (з документа «Довідник НАССР для працівників магазинів»).
- Зібрати сайт: `python3 src/build.py .` (створює `index.html` у корені).
- Згенерувати PDF бланків (для друку з телефона): `node src/gen_pdf.js .` (потрібен Playwright; створює папку `pdf/`).
- QR-генератор: qrcode-generator (Kazuhiko Arase, MIT).
