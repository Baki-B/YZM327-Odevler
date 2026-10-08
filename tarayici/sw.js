// Service worker: sitenin "sunucusu".
//   * app/ altındaki sayfa ve API istekleri (app/static/ hariç) tarayıcıda çalışan Flask'a gider: istek, açık kabuk
//     sayfasına (index.html) iletilir, kabuk onu Python işçisine (isci.js) verir, yanıt geri gelir.
//   * Diğer dosyalar (kabuk, Pyodide, CSS, JS, simgeler) önce ağdan, ağ yoksa önbellekten sunulur: site bir kez açıldıktan
//     sonra çevrimdışı da çalışır ve telefona uygulama gibi kurulabilir.
"use strict";

const SURUM = "__SURUM__";                     // derle.py yerleştirir; sürüm değişince eski önbellek silinir
const ONBELLEK = "agora-" + SURUM;
const SITE = new URL("./", self.location).href;
const UYGULAMA = SITE + "app/";
const UYGULAMA_YOLU = new URL(UYGULAMA).pathname;
const BEKLEME_MS = 60000;

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const ad of await caches.keys()) if (ad.startsWith("agora-") && ad !== ONBELLEK) await caches.delete(ad);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin || url.pathname.endsWith(".apk")) return;   // APK önbelleğe alınmaz
  if (url.href.startsWith(UYGULAMA) && !url.href.startsWith(UYGULAMA + "static/")) {
    e.respondWith(uygulamaya(e.request, url));
  } else if (e.request.method === "GET") {
    e.respondWith(agdanYaDaOnbellekten(e.request));
  }
});

async function agdanYaDaOnbellekten(istek) {
  const onbellek = await caches.open(ONBELLEK);
  try {
    const yanit = await fetch(istek);
    if (yanit.ok) onbellek.put(istek, yanit.clone());
    return yanit;
  } catch (hata) {
    const kayitli = await onbellek.match(istek, { ignoreSearch: true });
    if (kayitli) return kayitli;
    throw hata;
  }
}

// Python işçisini barındıran kabuk sekmesine sor. Birden çok sekme açıksa yalnızca etkin kabuk yanıt verir.
function sor(istemci, mesaj) {
  return new Promise((tamam) => {
    const kanal = new MessageChannel();
    kanal.port1.onmessage = (e) => tamam(e.data);
    istemci.postMessage(mesaj, [kanal.port2]);
  });
}

function zamanAsimi(ms) {
  return new Promise((_, red) => setTimeout(() => red(new Error("zaman aşımı")), ms));
}

async function uygulamaya(istek, url) {
  const yol = "/" + url.pathname.slice(UYGULAMA_YOLU.length) + url.search;
  // Uygulama adresi sekmenin kendisinde açıldı (yer imi, yeni sekme): önce kabuk açılır, kabuk aynı sayfayı çerçevede gösterir.
  if (istek.mode === "navigate" && istek.destination === "document") {
    return Response.redirect(SITE + "?yol=" + encodeURIComponent(yol), 302);
  }
  const kabuklar = (await self.clients.matchAll({ type: "window", includeUncontrolled: true }))
    .filter((c) => !c.url.startsWith(UYGULAMA));
  if (!kabuklar.length) return new Response("Agora kapalı: sayfayı yenileyin.", { status: 503 });
  const basliklar = {};
  istek.headers.forEach((deger, ad) => { basliklar[ad] = deger; });
  const govde = ["GET", "HEAD"].includes(istek.method) ? null : new Uint8Array(await istek.arrayBuffer());
  const mesaj = { tur: "istek", yontem: istek.method, kok: UYGULAMA.slice(0, -1), yol, basliklar, govde };
  let yanit;
  try {
    yanit = await Promise.race([Promise.any(kabuklar.map((k) => sor(k, mesaj))), zamanAsimi(BEKLEME_MS)]);
  } catch {
    return new Response("Agora yanıt vermedi; sayfayı yenileyin.", { status: 504 });
  }
  const konum = yanit.basliklar.find(([ad]) => ad.toLowerCase() === "location");
  if (yanit.durum >= 300 && yanit.durum < 400 && konum) {
    const kod = [301, 302, 303, 307, 308].includes(yanit.durum) ? yanit.durum : 302;
    return Response.redirect(new URL(konum[1], istek.url).href, kod);
  }
  const bos = [204, 304].includes(yanit.durum) || istek.method === "HEAD";
  return new Response(bos ? null : yanit.govde, { status: yanit.durum, headers: yanit.basliklar });
}
