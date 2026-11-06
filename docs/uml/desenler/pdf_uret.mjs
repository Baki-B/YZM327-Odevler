// svg/ klasöründeki üç diyagramı tek PDF'te toplar: Agora_Desenler_ve_SOLID.pdf
// Kullanım:  npm i playwright-core  &&  node docs/uml/desenler/pdf_uret.mjs  [chrome-yolu]
// Diyagramları yeniden çizmek için (bu klasörde):  java -jar plantuml.jar -charset UTF-8 -tsvg -o svg *.puml
import { chromium } from "playwright-core";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const klasor = path.dirname(fileURLToPath(import.meta.url));
const DIYAGRAMLAR = [
  ["1_oylama_ve_konu_durumlari.svg", "1. Oylama türleri ve konu durumları — Strategy, Template Method, State",
   "Bir oylamanın sonucunun nasıl uygulanacağı oylamanın türüne göre değişiyor (Strategy). Sonuçlandırmanın adım sırası ise " +
   "her türde aynı (Template Method). Konunun hangi durumda neye izin verdiğini de durum nesneleri biliyor (State)."],
  ["2_denetim_bildirim_konu_sayfasi.svg", "2. Denetim, bildirim ve konu sayfası — Chain of Responsibility, Adapter, Facade",
   "Yeni bir konu ya da mesaj, yönetmeliğin D1–D7 maddelerinden sırayla geçiyor (Chain of Responsibility). İki farklı " +
   "bildirim servisi tek bir arayüzün arkasında duruyor (Adapter). Konu sayfası yedi alt sistemi tek bir çağrıyla topluyor (Facade)."],
  ["3_kayit_defteri.svg", "3. Kayıt defteri — Observer, Memento, Repository",
   "Veritabanı bir işlem kaydedildiğinde abonelerine haber veriyor; defter bu olaya abone (Observer). Zamanlayıcı her " +
   "oylamayı ayrı bir kayıt noktasında işliyor; hata olursa kuyruklar hatıradan geri yükleniyor (Memento). Defter düğümlerine " +
   "erişim ise tek bir arayüzün arkasında (Repository)."],
];

function svgOku(f) {
  return fs.readFileSync(path.join(klasor, "svg", f), "utf8").replace(/<\?xml[^>]*>/, "")
    .replace(/preserveAspectRatio="none"/, 'preserveAspectRatio="xMidYMid meet"');   // oranı bozmadan sığdır
}
const sayfalar = DIYAGRAMLAR.map(([f, baslik, metin]) =>
  `<section><h2>${baslik}</h2><p>${metin}</p><div class="cizim">${svgOku(f)}</div></section>`);

const html = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>
  @page { size: A4 portrait; margin: 10mm 12mm; }
  body { font-family: Inter, sans-serif; color: #2c2a27; margin: 0; }
  section { break-after: page; height: 276mm; display: flex; flex-direction: column; }
  section:last-child { break-after: auto; }
  h1 { font-size: 24px; margin: 0 0 4px; color: #2a3c25; } h2 { font-size: 15px; margin: 0 0 4px; color: #3a5234; }
  h3 { font-size: 14px; margin: 18px 0 6px; color: #3a5234; }
  p { font-size: 12px; line-height: 1.5; margin: 0 0 8px; }
  .cizim { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }
  .cizim svg { width: 100% !important; height: 100% !important; }
  table { border-collapse: collapse; width: 100%; font-size: 12px; margin: 6px 0 4px; }
  th { background: #4a6642; color: #f6f4ef; text-align: left; padding: 6px 8px; }
  td { padding: 6px 8px; border-bottom: 1px solid #dfd9ce; vertical-align: top; }
  ul { font-size: 12px; line-height: 1.6; margin: 0; padding-left: 18px; }
  .yesil { background: #e3ebdf; border: 1px solid #a9a49b; padding: 0 6px; }
  .bej { background: #f4efe3; border: 1px solid #a9a49b; padding: 0 6px; }
</style></head><body>
<section>
  <p style="font-size:12px;color:#57534c">Abdülbaki Bayır · 24290050 · YZM327 Yazılım Mühendisliğine Giriş</p>
  <h1>Agora — Tasarım desenleri ve SOLID ilkeleri</h1>
  <p>Agora'da kullanılan dokuz tasarım deseni (sekizi GoF, biri Repository) ve beş SOLID ilkesi üç sınıf diyagramında gösteriliyor. Her diyagram birbiriyle
  çalışan birkaç deseni bir arada çiziyor; SOLID ilkeleri de uygulandıkları sınıfın yanına not olarak yazıldı. Sınıf ve
  yöntem adları koddakiyle aynı.</p>
  <table>
    <tr><th style="width:38%">Diyagram</th><th style="width:36%">Desenler</th><th>SOLID ilkeleri</th></tr>
    <tr><td>1. Oylama türleri ve konu durumları</td><td>Strategy, Template Method, State</td><td>S, O, L</td></tr>
    <tr><td>2. Denetim, bildirim ve konu sayfası</td><td>Chain of Responsibility, Adapter, Facade</td><td>S, O, L, I</td></tr>
    <tr><td>3. Kayıt defteri</td><td>Observer, Memento, Repository</td><td>S, L, I, D</td></tr>
  </table>
  <h3>SOLID ilkeleri</h3>
  <ul>
    <li><b>S — Tek sorumluluk:</b> Her sınıfın ya da modülün değişmek için tek bir nedeni olmalı.</li>
    <li><b>O — Açık/kapalı:</b> Yeni davranış, var olan kodu değiştirmeden yeni bir sınıf eklenerek kazandırılmalı.</li>
    <li><b>L — Liskov:</b> Alt tür, üst türün yerine kullanıldığında program doğru çalışmaya devam etmeli.</li>
    <li><b>I — Arayüz ayrımı:</b> Bir sınıf, kullanmadığı yöntemleri yazmaya zorlanmamalı; arayüzler küçük tutulmalı.</li>
    <li><b>D — Bağımlılığın tersine çevrilmesi:</b> Alt katman üst katmanı tanımamalı; ikisi de bir soyutlamaya bağlı olmalı.</li>
  </ul>
  <h3>Diyagramlar nasıl okunur?</h3>
  <ul>
    <li>Sınıf adının üstündeki <b>«Strategy», «Handler», «Adapter»</b> gibi etiketler, sınıfın desendeki rolünü gösteriyor.
    «modül» etiketi, sınıf değil bir Python modülü olduğunu belirtiyor.</li>
    <li><span class="yesil">Yeşil notlar</span> o yerde uygulanan SOLID ilkesini, <span class="bej">bej notlar</span>
    desenin nasıl işlediğini anlatıyor.</li>
    <li>İtalik yazılan sınıf ve yöntemler soyut: alt sınıfın doldurması gerekiyor.</li>
    <li>Oklar: içi boş üçgen kalıtım, kesikli üçgen bir arayüzü gerçekleme, kesikli ok "kullanır / çağırır", düz ok kalıcı
    ilişki, boş elmas ise "bir listede tutar" (toplama) anlamına geliyor.</li>
  </ul>
</section>
${sayfalar.join("\n")}
</body></html>`;

const cikti = path.join(klasor, "Agora_Desenler_ve_SOLID.pdf");
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
w.add_metadata({"/Title": "Agora — Tasarım desenleri ve SOLID ilkeleri", "/Author": "Abdülbaki Bayır (24290050)",
                "/Subject": "YZM327 Yazılım Mühendisliğine Giriş: tasarım desenleri ve SOLID sınıf diyagramları"})
w.write(sys.argv[1])
`, cikti]);
console.log("Yazıldı: docs/uml/desenler/Agora_Desenler_ve_SOLID.pdf");
