// Oyun testi: cihazın göndereceği fare tıklarının (sol/sağ) AYNISINI ekransız
// (headless) Chromium'da oyuna bastırır ve kaynakların farmlandığını doğrular.
// Yani "otomatik tıklayan cihaz, oyunu gerçekten farmlar mı?" sorusunu donanım
// olmadan yanıtlar. Oyuncu kaynakların yanında (oyun başlangıcı), oto-hedef en
// yakın kaynağa kilitli; makro sadece tıklar.
//
// Çalıştır:  node oyun/test_oyun.mjs
import { fileURLToPath } from "url";
import path from "path";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const buDizin = path.dirname(fileURLToPath(import.meta.url));
const oyunYolu = "file://" + path.join(buDizin, "index.html");
const ekranYolu = path.join(buDizin, "ekran_goruntusu.png");

// Cihazın makro ayarıyla aynı: fare düğmeleri sol ve sağ, aralıklı tıklanır.
const DUGMELER = ["left", "right"];
const TUR = 40;                 // 40 tur × 2 düğme = 80 tık
const ARALIK_MS = 25;           // testte hızlı; cihazda ~150 ms

function kontrol(kosul, mesaj) {
  if (!kosul) { console.error("  [KALDI] " + mesaj); process.exitCode = 1; }
  else console.log("  [GECTI] " + mesaj);
}

const tarayici = await chromium.launch({ headless: true });
try {
  const sayfa = await tarayici.newPage({ viewport: { width: 480, height: 760 } });
  await sayfa.goto(oyunYolu);

  const kutu = await sayfa.locator("#harita").boundingBox();
  const mx = kutu.x + kutu.width / 2, my = kutu.y + kutu.height / 2;

  const basla = await sayfa.evaluate(() => window.durum.toplam);
  console.log("Baslangic toplam kaynak:", basla);

  // Makronun yaptığı şey: her tur, sol ve sağ tık, aralık kadar bekle.
  for (let t = 0; t < TUR; t++) {
    for (const dugme of DUGMELER) {
      await sayfa.mouse.click(mx, my, { button: dugme });
      await sayfa.waitForTimeout(ARALIK_MS);
    }
  }

  const son = await sayfa.evaluate(() => window.durum);
  console.log("Sonuc:", JSON.stringify(son));

  await sayfa.screenshot({ path: ekranYolu });
  console.log("Ekran goruntusu:", ekranYolu);

  console.log("\n=== Dogrulamalar ===");
  kontrol(son.tik === TUR * DUGMELER.length, `tik sayisi ${TUR * DUGMELER.length} olmali (oldu: ${son.tik})`);
  kontrol(son.toplam > 0, `en az bir kaynak farmlanmali (oldu: ${son.toplam})`);
  kontrol(son.odun > 0 && son.tas > 0, `hem odun hem tas farmlanmali (odun: ${son.odun}, tas: ${son.tas})`);
  kontrol(son.seviye > 1, `seviye atlanmali (oldu: ${son.seviye})`);
  kontrol(son.toplam > basla, "toplam kaynak baslangictan yuksek olmali");
} finally {
  await tarayici.close();
}

console.log(process.exitCode ? "\nTEST BASARISIZ" : "\nTEST GECTI: otomatik fare tiklari oyunu farmladi.");
