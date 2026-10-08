// rapor.html → Agora_Proje_Raporu.pdf  (A4; kapak + en fazla 4 içerik sayfası)
// Kullanım:  npm i playwright-core  &&  node docs/rapor/pdf_uret.mjs  [chrome-yolu]
// Chrome yolu verilmezse Playwright'ın kendi Chromium'u kullanılır. Elle: rapor.html'i Chrome'da açıp "PDF olarak kaydet".
import { chromium } from "playwright-core";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const klasor = path.dirname(fileURLToPath(import.meta.url));
const tarayici = await chromium.launch(process.argv[2] ? { executablePath: process.argv[2] } : {});
const sayfa = await tarayici.newPage();
await sayfa.goto(pathToFileURL(path.join(klasor, "rapor.html")).href, { waitUntil: "networkidle" });
await sayfa.pdf({ path: path.join(klasor, "Agora_Proje_Raporu.pdf"), format: "A4", printBackground: true,
                  preferCSSPageSize: true });
await tarayici.close();
console.log("Yazıldı: docs/rapor/Agora_Proje_Raporu.pdf");
