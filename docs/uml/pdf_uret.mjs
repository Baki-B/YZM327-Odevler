// svg/ klasöründeki diyagramları tek PDF'te toplar: Agora_UML_Diyagramlari.pdf (geniş diyagramlar yatay sayfada).
// Kullanım:  npm i playwright-core  &&  node docs/uml/pdf_uret.mjs  [chrome-yolu]
// Diyagramları yeniden çizmek için:  java -jar plantuml.jar -charset UTF-8 -tsvg -o svg 0*.puml
import { chromium } from "playwright-core";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const klasor = path.dirname(fileURLToPath(import.meta.url));
const ACIKLAMALAR = {
  "01a": ["Kullanım durumları (1/2)", "Ziyaretçi, üye ve uzmanın sistemle etkileşimi. Konu açma, mesaj ve fikir yazma yönetmelik denetimini içerir (include); alt konu ve itiraz konusu, konu açmanın uzantısıdır (extend). Uzman, üyenin özelleşmiş hâlidir: alanındaki oyu 10 sayılır ve gerekçe ister."],
  "01b": ["Kullanım durumları (2/2)", "Yönetici yalnızca ayrı yönetici girişiyle panele girer ve kararlara karışamaz. Zamanlayıcı tartışmayı oylamaya geçirir ve turları sonuçlandırır; yapay zeka üye yalnızca özet yazar."],
  "02a": ["Sınıf diyagramı: alan modeli", "Sistemin temel varlıkları, nitelikleri ve çokluklarıyla. Kişisel bilgiler (ad, doğum tarihi) gizli niteliklerdir; oy deftere seçim olarak değil, taahhüt (SHA-256) olarak yazılır."],
  "02b": ["Sınıf diyagramı: konu durumları ve oylama türleri", "State: konunun her durumu ne yapılabileceğini kendisi söyler. Strategy + Template Method: sonuçlandırmanın adım sırası sabittir, türe özgü adımlar altı oylama türünden gelir; türler bir kayıt (Registry) üzerinden bulunur."],
  "02c": ["Sınıf diyagramı: yönetmelik denetimi ve konu sayfası", "Chain of Responsibility: D1–D7 maddeleri zincirin halkalarıdır; her halka kendi kontrolünü yapar ve isteği sonrakine geçirir. Facade: konu sayfası 7 alt sistemi tek bir giriş noktasından toplar."],
  "02d": ["Sınıf diyagramı: kayıt defteri ve anlık bildirim", "Observer: veritabanı defteri tanımaz, defter commit olayına abone olur. Repository: düğüm depoları (SQLite ya da bellek) aynı arayüzü uygular; test diske dokunmaz. Adapter: Web Push ve Firebase tek bir kanal arayüzünün arkasında."],
  "03a": ["Sıralı diyagram 1: kayıt olma", "Kurallar sağlanmazsa form hata mesajıyla geri döner; sağlanırsa şifre ve kurtarma kodu özetlenerek saklanır, deftere yalnızca takma ad yazılır."],
  "03b": ["Sıralı diyagram 2: konu açma", "Konu, yönetmelik denetimi zincirinden geçer. Engelleyen madde varsa konu açılmaz; yoksa 24 saatlik tartışma başlar."],
  "03c": ["Sıralı diyagram 3: oy verme ve makbuz", "Oy ağırlığı uygunluktan gelir (gözlemci 0, üye 1, uzman 10). Oy yalnızca oylama hâlâ açıksa yazılır; deftere taahhüt yazılır ve üye makbuzla oyunu sonradan doğrulayabilir."],
  "03d": ["Sıralı diyagram 4: tur sonu", "Zamanlayıcı her oylamayı ayrı bir kayıt noktasında sonuçlandırır; bir oylamadaki hata yalnızca onu geri alır. Turun kararı saf bir işlevdir: kabul, sonraki tur ya da sonuçsuz."],
  "03e": ["Sıralı diyagram 5: şikayetten gizleme oylamasına", "Şikayet tabanı (3 kişi) dolunca yöneticiler bilgilendirilir. Yönetici içeriği silemez; yalnızca oylamaya alır, kararı 3/4 oylama verir."],
  "03f": ["Sıralı diyagram 6: yönetici girişi ve askıya alma", "Yönetim paneli üye oturumunu değil, ayrı yönetici oturumunu kullanır. Askıya alma gerekçesiyle şeffaflık günlüğüne ve deftere yazılır."],
  "03g": ["Sıralı diyagram 7: tarayıcı sürümünde bir istek", "GitHub Pages'te sunucu yoktur: service worker isteği yakalar, kabuk sayfası onu Pyodide'de çalışan Flask'a iletir; veriler tarayıcıda (IndexedDB) saklanır."],
};

const svgKlasoru = path.join(klasor, "svg");
const dosyalar = fs.readdirSync(svgKlasoru).filter((f) => f.endsWith(".svg")).sort();
const sayfalar = dosyalar.map((f) => {
  const svg = fs.readFileSync(path.join(svgKlasoru, f), "utf8").replace(/<\?xml[^>]*>/, "");
  const m = svg.match(/viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"/) || svg.match(/width="([\d.]+)px"[^>]*height="([\d.]+)px"/);
  const yatay = m && Number(m[1]) / Number(m[2]) > 1.25;
  const [baslik, metin] = ACIKLAMALAR[f.slice(0, 3)] || [f, ""];
  return `<section class="${yatay ? "yatay" : "dikey"}"><h2>${baslik}</h2><p>${metin}</p><div class="cizim">${svg}</div></section>`;
});

const html = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>
  @page { size: A4 portrait; margin: 14mm; }
  @page yatay { size: A4 landscape; margin: 12mm; }
  body { font-family: Inter, sans-serif; color: #2c2a27; margin: 0; }
  section { break-after: page; display: flex; flex-direction: column; }
  section.dikey { height: 268mm; }
  section.yatay { page: yatay; height: 185mm; }
  h1 { font-size: 22px; margin: 0 0 6px; } h2 { font-size: 15px; margin: 0 0 4px; color: #3a5234; }
  p { font-size: 11px; line-height: 1.45; margin: 0 0 8px; }
  .cizim { flex: 1; min-height: 0; display: flex; align-items: flex-start; justify-content: center; }
  .cizim svg { max-width: 100%; max-height: 100%; width: auto !important; height: auto !important; }
  .kapak { justify-content: flex-start; }
  .kapak ul { font-size: 12px; line-height: 1.7; }
</style></head><body>
<section class="dikey kapak">
  <p style="font-size:12px;color:#57534c">Abdülbaki Bayır · 24290050 · YZM327</p>
  <h1>Agora — UML diyagramları</h1>
  <p>Kullanım durumu, sınıf ve sıralı diyagramlar. Diyagramlar koddan çıkarıldı; sınıf ve işlev adları kaynak koddakilerle aynıdır.
     Kaynak dosyalar <code>docs/uml/*.puml</code> (PlantUML); durum diyagramı ve varlık–ilişki diyagramı <code>docs/tasarim.md</code>'dedir.</p>
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
