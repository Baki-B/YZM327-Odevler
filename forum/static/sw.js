// Service worker: uygulama kabuğunu önbellekler, bağlantı yoksa çevrimdışı sayfası gösterir, anlık bildirimleri gösterir.
// Sayfalar her zaman ağdan gelir (oylar ve kararlar bayat gösterilmemeli).
var SURUM = "agora-v17";
var KABUK = ["/cevrimdisi", "/static/style.css", "/static/app.js", "/static/tema.js", "/static/ikon.svg", "/static/ikon-192.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(SURUM).then(function (c) { return c.addAll(KABUK); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (anahtarlar) {
    return Promise.all(anahtarlar.filter(function (a) { return a !== SURUM; }).map(function (a) { return caches.delete(a); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var istek = e.request;
  if (istek.method !== "GET") return;
  var url = new URL(istek.url);
  if (url.origin !== location.origin) return;
  if (istek.mode === "navigate") {
    e.respondWith(fetch(istek).catch(function () { return caches.match("/cevrimdisi"); }));
    return;
  }
  if (url.pathname.indexOf("/static/") === 0) {
    // Önce ağ (güncellemeler hemen görünsün), bağlantı yoksa önbellek.
    e.respondWith(fetch(istek).then(function (yanit) {
      var kopya = yanit.clone();
      caches.open(SURUM).then(function (c) { c.put(istek, kopya); });
      return yanit;
    }).catch(function () { return caches.match(istek); }));
  }
});

// Anlık bildirim (Web Push): sunucu {baslik, metin, url} gönderir
self.addEventListener("push", function (e) {
  var v = {};
  try { v = e.data ? e.data.json() : {}; } catch (_) { v = { metin: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(v.baslik || "Agora", {
    body: v.metin || "Yeni bildirimin var.", icon: "/static/ikon-192.png", badge: "/static/ikon-192.png",
    data: { url: v.url || "/bildirimler" }, lang: "tr"
  }));
});

// Bildirime dokununca: site açıksa o sekmeye geç, değilse yeni pencerede aç
self.addEventListener("notificationclick", function (e) {
  e.notification.close();
  var hedef = new URL((e.notification.data && e.notification.data.url) || "/bildirimler", location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (pencereler) {
    for (var i = 0; i < pencereler.length; i++) {
      if (new URL(pencereler[i].url).origin === location.origin && "navigate" in pencereler[i]) {
        return pencereler[i].focus().then(function (p) { return p.navigate(hedef); });
      }
    }
    return self.clients.openWindow(hedef);
  }));
});
