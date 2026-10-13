// Oyun testi: cihazın göndereceği a-s-d tuşlarının AYNISINI ekransız (headless)
// Chromium'a bastırır ve oyunun skorunun yükseldiğini doğrular. Yani "otomatik
// klavyeye basan cihaz, oyunu gerçekten oynuyor mu?" sorusunu donanım olmadan
// yanıtlar.
//
// Çalıştır:  node oyun/test_oyun.mjs
import { fileURLToPath } from "url";
import path from "path";
import { createRequire } from "module";

// Playwright çoğunlukla genel (global) kurulu olduğundan, ESM yerine CommonJS
// çözümleyicisiyle bul (genel modül yollarını tarar). Yerelde kuruluysa da bulur.
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const buDizin = path.dirname(fileURLToPath(import.meta.url));
const oyunYolu = "file://" + path.join(buDizin, "index.html");
const ekranYolu = path.join(buDizin, "ekran_goruntusu.png");

// Cihazın makro ayarıyla aynı: haritada WASD ile gezilir (glor.io/dynast.io tarzı).
const TUSLAR = ["w", "a", "s", "d"];
const TUR = 40;                 // 40 tur × 4 tuş = 160 hamle
const ARALIK_MS = 25;           // testte hızlı; cihazda 200 ms

function kontrol(kosul, mesaj) {
  if (!kosul) { console.error("  [KALDI] " + mesaj); process.exitCode = 1; }
  else console.log("  [GECTI] " + mesaj);
}

const tarayici = await chromium.launch({ headless: true });
try {
  const sayfa = await tarayici.newPage({ viewport: { width: 480, height: 760 } });
  await sayfa.goto(oyunYolu);

  const basla = await sayfa.evaluate(() => window.durum.toplam);
  console.log("Baslangic toplam kaynak:", basla);

  // Makronun yaptığı şey: her tur, sırayla tuşlara bas, aralık kadar bekle.
  for (let t = 0; t < TUR; t++) {
    for (const tus of TUSLAR) {
      await sayfa.keyboard.press(tus);
      await sayfa.waitForTimeout(ARALIK_MS);
    }
  }

  const son = await sayfa.evaluate(() => window.durum);
  console.log("Sonuc:", JSON.stringify(son));

  await sayfa.screenshot({ path: ekranYolu });
  console.log("Ekran goruntusu:", ekranYolu);

  console.log("\n=== Dogrulamalar ===");
  kontrol(son.hamle === TUR * TUSLAR.length, `hamle sayisi ${TUR * TUSLAR.length} olmali (oldu: ${son.hamle})`);
  kontrol(son.toplam > 0, `en az bir kaynak farmlanmali (oldu: ${son.toplam})`);
  kontrol(son.odun > 0 && son.tas > 0, `hem odun hem tas farmlanmali (odun: ${son.odun}, tas: ${son.tas})`);
  kontrol(son.seviye > 1, `seviye atlanmali (oldu: ${son.seviye})`);
  kontrol(son.toplam > basla, "toplam kaynak baslangictan yuksek olmali");
} finally {
  await tarayici.close();
}

console.log(process.exitCode ? "\nTEST BASARISIZ" : "\nTEST GECTI: otomatik tuslar oyunu oynatti.");
