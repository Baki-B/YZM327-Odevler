// Uygulamanın bağlanacağı sunucu adresini ayarlar:  npm run adres -- http://192.168.1.20:5000
// Adres değişince "npm run esitle" ile Android projesine aktarılır.
const fs = require("fs");
const path = require("path");

// Yol içeren adreslerde (GitHub Pages gibi) sondaki "/" korunur; yoksa sunucu bir yönlendirme daha yapar.
const ham = (process.argv[2] || "").replace(/\/+$/, "");
const adres = /^https?:\/\/[^/]+\/./.test(ham) ? ham + "/" : ham;
if (!/^https?:\/\/[^\s/]+(:\d+)?(\/[^\s]*)?$/.test(adres)) {
  console.error("Kullanım: npm run adres -- http://BILGISAYARIN-IP-ADRESI:5000");
  console.error("Emülatörde bilgisayarın kendisi: http://10.0.2.2:5000");
  console.error("Web sitesi (varsayılan): https://baki-b.github.io/YZM327-Odevler/");
  process.exit(1);
}
const yol = path.join(__dirname, "capacitor.config.json");
const ayar = JSON.parse(fs.readFileSync(yol, "utf8"));
ayar.server.url = adres;
ayar.server.cleartext = adres.startsWith("http://");
fs.writeFileSync(yol, JSON.stringify(ayar, null, 2) + "\n");
console.log(`Sunucu adresi: ${adres}`);
console.log("Şimdi çalıştır:  npm run esitle");
