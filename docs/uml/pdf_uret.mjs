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
  "1_k": ["Kullanım durumu diyagramı", "Ziyaretçi okur ve kayıt olur. Üye, ziyaretçinin yapabildiklerine ek olarak konu açar, yazar, oy verir ve şikayet eder. Konu açmak her zaman yönetmelik denetimini içerir. Yönetici siteyi yönetir; zamanlayıcı süresi dolan turları sonuçlandırır."],
  "2_s": ["Sınıf diyagramı", "Bir kullanıcı konu açar ve mesaj yazar. Her konunun bir kategorisi ve oylamaları vardır. Oylamanın seçenekleri (fikirler) ve oyları olur. Konu karara bağlanırsa kazanan seçenek karar olarak kaydedilir."],
  "3a_": ["Sıralı diyagram: konu açma", "Konu kaydedilmeden önce yönetmelik denetiminden geçer; kurala aykırıysa açılmaz."],
  "3b_": ["Sıralı diyagram: oy verme", "Oy kaydedilir, kayıt defterine oyun kendisi değil bir taahhüdü yazılır; üye oyunu sonradan makbuz koduyla doğrulayabilir."],
  "3c_": ["Sıralı diyagram: tur sonu", "Süre dolunca oylar sayılır. Bir fikir %75'e ulaştıysa ya da tek fikir kaldıysa konu karara bağlanır; yoksa sonraki tur başlar."],
};

const svgKlasoru = path.join(klasor, "svg");
const dosyalar = fs.readdirSync(svgKlasoru).filter((f) => f.endsWith(".svg")).sort();
function svgOku(f) {
  return fs.readFileSync(path.join(svgKlasoru, f), "utf8").replace(/<\?xml[^>]*>/, "")
    .replace(/preserveAspectRatio="none"/, 'preserveAspectRatio="xMidYMin meet"');   // oranı bozmadan sığdır
}
// Her diyagram kendi sayfasında, sayfa genişliğine sığdırılarak.
const sayfalar = dosyalar.map((f) => {
  const [baslik, metin] = ACIKLAMALAR[f.slice(0, 3)] || [f, ""];
  return `<section class="dikey"><h2>${baslik}</h2><p>${metin}</p><div class="cizim">${svgOku(f)}</div></section>`;
});

const html = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>
  @page { size: A4 portrait; margin: 14mm; }
  body { font-family: Inter, sans-serif; color: #2c2a27; margin: 0; }
  section { break-after: page; display: flex; flex-direction: column; }
  section.dikey { height: 268mm; }
  h1 { font-size: 22px; margin: 0 0 6px; } h2 { font-size: 15px; margin: 0 0 4px; color: #3a5234; }
  p { font-size: 11px; line-height: 1.45; margin: 0 0 8px; }
  .cizim { flex: 1; min-height: 0; display: flex; align-items: flex-start; justify-content: center; }
  .cizim svg { width: 100% !important; height: auto !important; max-height: 100%; }
  .kapak { justify-content: flex-start; }
  .kapak ul { font-size: 12px; line-height: 1.7; }
</style></head><body>
<section class="dikey kapak">
  <p style="font-size:12px;color:#57534c">Abdülbaki Bayır · 24290050 · YZM327</p>
  <h1>Agora — UML diyagramları</h1>
  <p>Kullanım durumu, sınıf ve sıralı diyagramların sade hâlleri. Kaynak dosyalar <code>docs/uml/*.puml</code> (PlantUML).
     Ayrıntılı hâlleri (tasarım desenleri, yedi akış) <code>docs/uml/ayrintili/</code> klasöründedir.</p>
  <ul>${dosyalar.map((f) => `<li>${(ACIKLAMALAR[f.slice(0, 3)] || [f])[0]}</li>`).join("")}</ul>
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
