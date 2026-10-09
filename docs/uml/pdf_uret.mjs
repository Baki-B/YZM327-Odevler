// svg/ klasöründeki diyagramları tek PDF'te toplar: Agora_UML_Diyagramlari.pdf
// Kullanım:  npm i playwright-core  &&  node docs/uml/pdf_uret.mjs  [chrome-yolu]
// Diyagramları yeniden çizmek için:  java -jar plantuml.jar -charset UTF-8 -tsvg -o svg [123]*.puml
import { chromium } from "playwright-core";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const klasor = path.dirname(fileURLToPath(import.meta.url));
const ACIKLAMALAR = {
  "1_k": ["Kullanım durumu diyagramı", "Ziyaretçi kayıt olur ya da giriş yapar. Üye konu açar, mesaj yazar ve oy verir. Yönetici şikayetleri inceler."],
  "2_s": ["Sınıf diyagramı", "Bir kullanıcı konu açar ve oy verir. Bir konuda mesajlar ve oylamalar olur; her oylamanın fikirleri ve oyları vardır."],
  "3a_": ["Konu açma", ""],
  "3b_": ["Oy verme", ""],
  "3c_": ["Tur sonu", ""],
};

const svgKlasoru = path.join(klasor, "svg");
const dosyalar = fs.readdirSync(svgKlasoru).filter((f) => f.endsWith(".svg")).sort();
function svgOku(f) {
  return fs.readFileSync(path.join(svgKlasoru, f), "utf8").replace(/<\?xml[^>]*>/, "")
    .replace(/preserveAspectRatio="none"/, 'preserveAspectRatio="xMidYMid meet"');   // oranı bozmadan sığdır
}
// Kullanım durumu ve sınıf diyagramı birer sayfa; üç kısa sıralı diyagram tek sayfada.
const sayfalar = dosyalar.filter((f) => !f.startsWith("3")).map((f) => {
  const [baslik, metin] = ACIKLAMALAR[f.slice(0, 3)] || [f, ""];
  return `<section><h2>${baslik}</h2><p>${metin}</p><div class="cizim">${svgOku(f)}</div></section>`;
});
const sirali = dosyalar.filter((f) => f.startsWith("3"));
if (sirali.length) {
  sayfalar.push(`<section><h2>Sıralı diyagramlar</h2><p>Bir işlemde mesajların hangi sırayla gittiği.</p>${sirali
    .map((f) => `<div class="parca">${svgOku(f)}</div>`).join("")}</section>`);
}

const html = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>
  @page { size: A4 portrait; margin: 16mm; }
  body { font-family: Inter, sans-serif; color: #2c2a27; margin: 0; }
  section { break-after: page; height: 260mm; display: flex; flex-direction: column; }
  h1 { font-size: 22px; margin: 0 0 6px; } h2 { font-size: 16px; margin: 0 0 4px; color: #3a5234; }
  p { font-size: 12px; line-height: 1.5; margin: 0 0 10px; }
  .cizim, .parca { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }
  .cizim svg, .parca svg { width: 100% !important; height: 100% !important; }
  .kapak ul { font-size: 13px; line-height: 1.8; }
</style></head><body>
<section class="kapak">
  <p style="font-size:12px;color:#57534c">Abdülbaki Bayır · 24290050 · YZM327</p>
  <h1>Agora — UML diyagramları</h1>
  <p>Kullanım durumu, sınıf ve sıralı diyagramlar.</p>
  <ul><li>Kullanım durumu diyagramı</li><li>Sınıf diyagramı</li><li>Sıralı diyagramlar: konu açma, oy verme, tur sonu</li></ul>
</section>
${sayfalar.join("\n")}
</body></html>`;

const cikti = path.join(klasor, "Agora_UML_Diyagramlari.pdf");
const tarayici = await chromium.launch(process.argv[2] ? { executablePath: process.argv[2] } : {});
const sayfa = await tarayici.newPage();
await sayfa.setContent(html, { waitUntil: "load" });
await sayfa.pdf({ path: cikti, printBackground: true, preferCSSPageSize: true, outline: true, tagged: true });
await tarayici.close();
// Başlık ve yazar bilgisi, varsa Python'daki pypdf ile eklenir (yoksa bu adım atlanır).
spawnSync("python3", ["-c", `
import sys
from pypdf import PdfReader, PdfWriter
w = PdfWriter(clone_from=PdfReader(sys.argv[1]))
w.add_metadata({"/Title": "Agora — UML diyagramları", "/Author": "Abdülbaki Bayır (24290050)",
                "/Subject": "YZM327: kullanım durumu, sınıf ve sıralı diyagramlar"})
w.write(sys.argv[1])
`, cikti]);
console.log("Yazıldı: docs/uml/Agora_UML_Diyagramlari.pdf");
