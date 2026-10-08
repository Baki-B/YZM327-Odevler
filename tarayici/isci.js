// Web Worker: Pyodide ile tarayıcıda çalışan Python'u ve içindeki Flask uygulamasını çalıştırır. Kabuk sayfası (kabuk.js)
// istekleri buraya iletir. Python tek iş parçacıklıdır; istekler sırayla işlenir. Ana sayfa donmasın diye ayrı bir işçide
// çalışır.
"use strict";

const SITE = new URL("./", self.location).href;
let surum = "";
let py = null;
let istekIsle = null;
const bekleyenler = [];          // Python hazır olmadan gelen istekler
let kayitZamanlayici = null;

function durum(mesaj) { postMessage({ tur: "durum", mesaj }); }

async function al(ad) {
  const y = await fetch(SITE + ad + "?v=" + surum);
  if (!y.ok) throw new Error(ad + " indirilemedi (" + y.status + ")");
  return new Uint8Array(await y.arrayBuffer());
}

// /veri klasörü tarayıcının IndexedDB'sine bağlıdır. doldur=true: IndexedDB → bellek; false: bellek → IndexedDB.
function senkron(doldur) {
  return new Promise((tamam, hata) => py.FS.syncfs(doldur, (e) => (e ? hata(e) : tamam())));
}

// Her istekten sonra (yazma olmasa da: oturum, zamanlayıcı) kısa bir gecikmeyle diske yazılır.
function kaydetPlanla() {
  clearTimeout(kayitZamanlayici);
  kayitZamanlayici = setTimeout(() => senkron(false).catch((e) => console.error("Kayıt hatası", e)), 300);
}

async function baslat() {
  surum = (await (await fetch(SITE + "surum.json", { cache: "no-store" })).json()).surum;
  durum("Python yükleniyor…");
  importScripts(SITE + "pyodide/pyodide.js");
  py = await loadPyodide({ indexURL: SITE + "pyodide/" });
  durum("Paketler yükleniyor…");
  await py.loadPackage(["sqlite3", "hashlib", "markupsafe"]);
  const [tekerlekler, uygulama, kopru] = await Promise.all([al("tekerlekler.zip"), al("forum.zip"),
    fetch(SITE + "kopru.py?v=" + surum).then((y) => y.text())]);
  const site = py.runPython("import site; site.getsitepackages()[0]");
  py.unpackArchive(tekerlekler, "zip", { extractDir: site });
  py.FS.mkdirTree("/uygulama");
  py.unpackArchive(uygulama, "zip", { extractDir: "/uygulama" });
  py.FS.mkdirTree("/veri");
  py.FS.mount(py.FS.filesystems.IDBFS, {}, "/veri");
  await senkron(true);
  durum("Forum hazırlanıyor…");
  await py.runPythonAsync(kopru);
  istekIsle = py.globals.get("istek");
  const yeni = py.globals.get("YENI");
  await senkron(false);
  postMessage({ tur: "hazir", yeni });
  while (bekleyenler.length) isle(...bekleyenler.shift());
}

function isle(veri, port) {
  let sonuc = null;
  try {
    sonuc = istekIsle(veri.yontem, veri.kok, veri.yol, py.toPy(veri.basliklar),
      veri.govde ? py.toPy(veri.govde) : null);
    const [durumKodu, basliklar, govde] = sonuc.toJs({ create_proxies: false });
    const govdeDizi = new Uint8Array(govde);
    port.postMessage({ durum: durumKodu, basliklar, govde: govdeDizi }, [govdeDizi.buffer]);
  } catch (e) {
    console.error(e);
    const metin = new TextEncoder().encode("Uygulama hatası: " + e);
    port.postMessage({ durum: 500, basliklar: [["Content-Type", "text/plain; charset=utf-8"]], govde: metin },
      [metin.buffer]);
  } finally {
    if (sonuc) sonuc.destroy();
    kaydetPlanla();
  }
}

async function sifirla() {
  clearTimeout(kayitZamanlayici);
  for (const ad of py.FS.readdir("/veri")) {
    if (ad === "." || ad === "..") continue;
    sil("/veri/" + ad);
  }
  await senkron(false);
  postMessage({ tur: "sifirlandi" });
}

function sil(yol) {
  const bilgi = py.FS.stat(yol);
  if (py.FS.isDir(bilgi.mode)) {
    for (const ad of py.FS.readdir(yol)) if (ad !== "." && ad !== "..") sil(yol + "/" + ad);
    py.FS.rmdir(yol);
  } else {
    py.FS.unlink(yol);
  }
}

onmessage = (e) => {
  const veri = e.data || {};
  if (veri.tur === "istek") {
    if (istekIsle) isle(veri, e.ports[0]);
    else bekleyenler.push([veri, e.ports[0]]);
  } else if (veri.tur === "sifirla") {
    sifirla().catch((h) => postMessage({ tur: "hata", mesaj: String(h) }));
  }
};

baslat().catch((h) => {
  console.error(h);
  postMessage({ tur: "hata", mesaj: String(h && h.message ? h.message : h) });
});
