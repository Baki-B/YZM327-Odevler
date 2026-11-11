// docs/rapor/rapor.html → docs/rapor/Rapor.pdf
// Ortamda kurulu Playwright + Chromium kullanılır (yalnızca bu betik için; npm test'in bağımlılığı değildir).
// Ana metnin sayfa sayısı ayrıca ölçülür (ekler gizlenerek): ödev sınırı 6 sayfa.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  console.error('Playwright bulunamadı. Kurulum: npm i -g playwright && npx playwright install chromium');
  process.exit(1);
}

const html = fileURLToPath(new URL('../docs/rapor/rapor.html', import.meta.url));
const pdf = fileURLToPath(new URL('../docs/rapor/Rapor.pdf', import.meta.url));
const options = { format: 'A4', printBackground: true, margin: { top: '14mm', bottom: '16mm', left: '15mm', right: '15mm' },
  displayHeaderFooter: true, headerTemplate: '<span></span>',
  footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#777"><span class="pageNumber"></span> / <span class="totalPages"></span></div>' };

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto('file://' + html, { waitUntil: 'networkidle' });
await page.emulateMedia({ media: 'print' });
await page.pdf({ ...options, path: pdf });
const full = await page.pdf(options);
await page.addStyleTag({ content: '.ekler { display: none !important; }' });
const main = await page.pdf(options);
await browser.close();
const pages = (buf) => (buf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) ?? []).length;
console.log(`Rapor.pdf yazıldı: toplam ${pages(full)} sayfa, ana metin ${pages(main)} sayfa (sınır 6)`);
