// rapor.html → Agora_Proje_Raporu.pdf  (A4; kapak + en fazla 4 içerik sayfası)
// Kullanım:  npm i playwright-core  &&  node docs/rapor/pdf_uret.mjs  [chrome-yolu]
// Chrome yolu verilmezse Playwright'ın kendi Chromium'u kullanılır. Elle: rapor.html'i Chrome'da açıp "PDF olarak kaydet".
// Yazı tipi: Inter ve Inter Display kurulu olmalı; yoksa tarayıcı başka bir yazı tipine düşer ve sayfa sayısı değişebilir.
// Yazar ve konu bilgisi, varsa Python'daki pypdf ile eklenir (yoksa bu adım atlanır, PDF yine üretilir).
import { chromium } from "playwright-core";
import { spawnSync } from "child_process";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const klasor = path.dirname(fileURLToPath(import.meta.url));
const cikti = path.join(klasor, "Agora_Proje_Raporu.pdf");
const tarayici = await chromium.launch(process.argv[2] ? { executablePath: process.argv[2] } : {});
const sayfa = await tarayici.newPage();
await sayfa.goto(pathToFileURL(path.join(klasor, "rapor.html")).href, { waitUntil: "networkidle" });
await sayfa.pdf({ path: cikti, format: "A4", printBackground: true, preferCSSPageSize: true, outline: true, tagged: true });
await tarayici.close();

const meta = spawnSync("python3", ["-c", `
import sys
from pypdf import PdfReader, PdfWriter
yol = sys.argv[1]
w = PdfWriter(clone_from=PdfReader(yol))
w.add_metadata({"/Author": "Abdülbaki Bayır (24290050)", "/Subject": "YZM327 1. Hafta Ödevi: Agora proje raporu"})
w.write(yol)
`, cikti], { encoding: "utf8" });
console.log(meta.status === 0 ? "Yazıldı: docs/rapor/Agora_Proje_Raporu.pdf (yazar bilgisiyle)"
                              : "Yazıldı: docs/rapor/Agora_Proje_Raporu.pdf (pypdf yok, yazar bilgisi eklenmedi)");
