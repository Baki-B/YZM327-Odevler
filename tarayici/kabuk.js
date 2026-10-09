// Kabuk sayfası: service worker'ı kaydeder, Python işçisini başlatır, service worker'dan gelen istekleri işçiye iletir
// ve uygulamayı tam ekran bir çerçevede (iframe) gösterir.
"use strict";

const perde = document.getElementById("perde");
const adim = document.getElementById("adim");
const cerceve = document.getElementById("uygulama");
const parametreler = new URLSearchParams(location.search);
let isci = null;

function yaz(metin, hata) {
  adim.textContent = metin;
  perde.classList.toggle("hatali", Boolean(hata));
}

function uygulamayiAc() {
  const yol = parametreler.get("yol") || "/";
  cerceve.src = "app" + (yol.startsWith("/") ? yol : "/" + yol);
  perde.classList.add("gizli");
}

// Çentik ve sistem çubuğu boşlukları çerçevenin içinden görünmez (env() çerçevede 0 olur; Expo uygulaması değişkenleri
// yalnızca ana sayfaya verir). Kabuk ölçtüğü boşlukları çerçeveye aktarır: üstü kabuğun şeridi karşılar, altı ve yanları
// uygulamanın alt sekme çubuğu kullanır.
function bosluklariAktar() {
  try {
    const olcu = getComputedStyle(document.getElementById("olcu"));
    const s = cerceve.contentDocument.documentElement.style;
    s.setProperty("--safe-area-inset-top", "0px");
    s.setProperty("--safe-area-inset-bottom", olcu.paddingBottom);
    s.setProperty("--safe-area-inset-left", olcu.paddingLeft);
    s.setProperty("--safe-area-inset-right", olcu.paddingRight);
  } catch (e) { /* çerçeve henüz yüklenmedi */ }
}
window.addEventListener("resize", bosluklariAktar);

// Geri tuşu (Android ve Expo uygulaması): sayfalar çerçevede açıldığı için uygulamanın kendi geçmişi boş görünür. Kabuk,
// çerçevede kaç sayfa ilerlendiğini sayar; geri tuşu çerçevede bir sayfa geri gider, en baştaysa uygulama kapanır.
let derinlik = -1;                 // ilk sayfa açılınca 0 olur
let geriGidiyor = false;

function geri() {
  if (derinlik <= 0) return false;
  derinlik--;
  geriGidiyor = true;
  setTimeout(() => { geriGidiyor = false; }, 1500);   // sayfa yeniden yüklenmeden dönülürse (#bağlantı) sayaç kaymasın
  cerceve.contentWindow.history.back();
  return true;
}
window.agoraGeri = geri;           // Expo uygulaması geri tuşunda bunu çağırır

const cap = window.Capacitor;
if (cap && cap.isNativePlatform && cap.isNativePlatform() && cap.Plugins && cap.Plugins.App) {
  cap.Plugins.App.addListener("backButton", () => { if (!geri()) cap.Plugins.App.exitApp(); });
}

// Çerçevedeki sayfanın başlığını ve adresini kabuğa yansıt: yenileyince aynı sayfa açılır.
cerceve.addEventListener("load", () => {
  if (geriGidiyor) geriGidiyor = false; else derinlik++;
  bosluklariAktar();
  try {
    const belge = cerceve.contentDocument;
    if (belge && belge.title) document.title = belge.title;
    const yol = cerceve.contentWindow.location.pathname.split("/app").slice(1).join("/app") || "/";
    const adres = new URL(location.href);
    adres.searchParams.set("yol", yol + cerceve.contentWindow.location.search);
    history.replaceState(null, "", adres);
  } catch (e) { /* farklı kökenli sayfa: dokunma */ }
});

// İlk ziyarette sayfa, service worker etkinleşip clients.claim() çalışana kadar denetimsizdir. Python işçisi o arada
// başlarsa indirdiği Pyodide ve uygulama dosyaları service worker'dan geçmez, önbelleğe girmez ve site çevrimdışı açılmaz.
// Bu yüzden işçi, sayfa denetime girene kadar (en çok birkaç saniye) bekletilir. Zorla yenilemede (Shift+F5) sayfa hiç
// denetime girmez; o zaman beklemeden devam edilir, dosyalar önceki ziyaretlerden zaten önbellektedir.
async function denetimiBekle(ms) {
  await navigator.serviceWorker.ready;
  if (navigator.serviceWorker.controller) return;
  await Promise.race([
    new Promise((tamam) => navigator.serviceWorker.addEventListener("controllerchange", tamam, { once: true })),
    new Promise((tamam) => setTimeout(tamam, ms)),
  ]);
}

async function baslat() {
  if (!("serviceWorker" in navigator) || !window.Worker || !window.WebAssembly) {
    yaz("Bu tarayıcı Agora'yı çalıştıramıyor. " +
      "Güncel Chrome, Edge, Firefox ya da Safari ile tekrar deneyin.", true);
    return;
  }
  // Aynı anda tek bir kabuk çalışır: iki sekme aynı veritabanının iki ayrı kopyasına yazıp birbirini ezmesin.
  if (navigator.locks) {
    const kilit = await new Promise((tamam) => {
      navigator.locks.request("agora-kabuk", { ifAvailable: true }, (k) => {
        tamam(k);
        return k ? new Promise(() => {}) : undefined;     // sekme açık kaldıkça kilit tutulur
      });
    });
    if (!kilit) {
      yaz("Agora zaten başka bir sekmede açık. Veriler karışmasın diye o sekmeyi kullanın ya da kapatıp bu sayfayı yenileyin.", true);
      return;
    }
  }
  const kayit = await navigator.serviceWorker.register("sw.js", { scope: "./" });
  navigator.serviceWorker.addEventListener("message", (e) => {
    if (e.data && e.data.tur === "istek" && isci) isci.postMessage(e.data, [e.ports[0]]);
  });
  await denetimiBekle(3000);
  isci = new Worker("isci.js");
  isci.onmessage = (e) => {
    const m = e.data;
    if (m.tur === "durum") yaz(m.mesaj);
    else if (m.tur === "hazir") navigator.serviceWorker.ready.then(uygulamayiAc);
    else if (m.tur === "sifirlandi") location.replace(location.pathname);
    else if (m.tur === "hata") yaz("Başlatılamadı: " + m.mesaj, true);
  };
  isci.onerror = (e) => yaz("Başlatılamadı: " + (e.message || "bilinmeyen hata"), true);
  await kayit.update().catch(() => {});
}

document.getElementById("sifirla").addEventListener("click", () => {
  if (!isci) return;
  if (!confirm("Bu cihazdaki bütün Agora verileri (hesaplar, konular, oylar) silinecek ve örnek veriler yeniden yüklenecek. Emin misin?")) return;
  perde.classList.remove("gizli");
  yaz("Veriler siliniyor…");
  isci.postMessage({ tur: "sifirla" });
});

const bilgi = document.getElementById("bilgi");
document.getElementById("bilgi-ac").addEventListener("click", () => bilgi.showModal());
document.getElementById("bilgi-kapat").addEventListener("click", () => bilgi.close());

baslat().catch((h) => yaz("Başlatılamadı: " + h, true));
