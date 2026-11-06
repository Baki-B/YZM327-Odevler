// svg/ klasöründeki üç kısa diyagramı tek PDF'te toplar: Agora_Desenler_ve_SOLID_Kisa.pdf
// Kullanım:  npm i playwright-core  &&  node docs/uml/desenler/kisa/pdf_uret.mjs  [chrome-yolu]
// Diyagramları yeniden çizmek için (bu klasörde):  java -jar plantuml.jar -charset UTF-8 -tsvg -o svg *.puml
import { chromium } from "playwright-core";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const klasor = path.dirname(fileURLToPath(import.meta.url));
const DIYAGRAMLAR = [
  ["k1_oylama_ve_konu_durumlari.svg", "1. Oylama türleri ve konu durumları", "Strategy, Template Method, State · SOLID: S, O, L. EvetHayirTuru: gizleme, kaldırma, uzmanlık, yönetmelik ve kategori oylamaları."],
  ["k2_denetim_bildirim_konu_sayfasi.svg", "2. Denetim, bildirim ve konu sayfası", "Chain of Responsibility, Adapter, Facade · SOLID: S, O, L, I"],
  ["k3_kayit_defteri.svg", "3. Kayıt defteri", "Observer, Memento, Repository · SOLID: L, I, D"],
];
const svgOku = (f) => fs.readFileSync(path.join(klasor, "svg", f), "utf8").replace(/<\?xml[^>]*>/, "")
  .replace(/preserveAspectRatio="none"/, 'preserveAspectRatio="xMidYMid meet"');

const html = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>
  @page { size: A4 portrait; margin: 12mm; }
  body { font-family: Inter, sans-serif; color: #2c2a27; margin: 0; }
  section { break-after: page; height: 272mm; display: flex; flex-direction: column; }
  section:last-child { break-after: auto; }
  h1 { font-size: 20px; margin: 0 0 4px; color: #2a3c25; } h2 { font-size: 16px; margin: 0 0 2px; color: #3a5234; }
  p { font-size: 12px; line-height: 1.5; margin: 0 0 8px; }
  .cizim { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }
  .cizim svg { width: 100% !important; height: 100% !important; }
  .yesil { background: #e3ebdf; border: 1px solid #a9a49b; padding: 0 5px; }
</style></head><body>
${DIYAGRAMLAR.map(([f, baslik, alt], i) => `<section>${i === 0 ? `
  <p style="font-size:12px;color:#57534c;margin:0">Abdülbaki Bayır · 24290050 · YZM327 Yazılım Mühendisliğine Giriş</p>
  <h1>Agora — Tasarım desenleri ve SOLID (kısa sürüm)</h1>
  <p>«…» etiketi sınıfın desendeki rolünü, <span class="yesil">yeşil notlar</span> SOLID ilkesini gösteriyor
  (S tek sorumluluk, O açık/kapalı, L Liskov, I arayüz ayrımı, D bağımlılığın tersine çevrilmesi).</p>` : ""}
  <h2>${baslik}</h2><p>${alt}</p><div class="cizim">${svgOku(f)}</div></section>`).join("\n")}
</body></html>`;

const cikti = path.join(klasor, "Agora_Desenler_ve_SOLID_Kisa.pdf");
const tarayici = await chromium.launch(process.argv[2] ? { executablePath: process.argv[2] } : {});
const sayfa = await tarayici.newPage();
await sayfa.setContent(html, { waitUntil: "load" });
await sayfa.pdf({ path: cikti, printBackground: true, preferCSSPageSize: true, tagged: true });
await tarayici.close();
spawnSync("python3", ["-c", `
import sys
from pypdf import PdfReader, PdfWriter
w = PdfWriter(clone_from=PdfReader(sys.argv[1]))
w.add_metadata({"/Title": "Agora — Tasarım desenleri ve SOLID (kısa sürüm)", "/Author": "Abdülbaki Bayır (24290050)",
                "/Subject": "YZM327 Yazılım Mühendisliğine Giriş: tasarım desenleri ve SOLID, kısa sınıf diyagramları"})
w.write(sys.argv[1])
`, cikti]);
console.log("Yazıldı: docs/uml/desenler/kisa/Agora_Desenler_ve_SOLID_Kisa.pdf");
