"""Tarayıcı köprüsü: Agora'yı Pyodide (WebAssembly üzerinde çalışan Python) içinde çalıştırır.

GitHub Pages yalnızca statik dosya sunar; Python sunucusu yoktur. Bu yüzden Flask uygulamasının kendisi ziyaretçinin
tarayıcısında, bir Web Worker içinde çalışır (isci.js). Sitenin service worker'ı (sw.js) uygulama adreslerine giden
istekleri yakalar, buraya iletir; `istek()` isteği Flask'a verir ve yanıtı geri döndürür. Veritabanı ve kayıt defteri
düğümleri /veri klasöründedir; bu klasör tarayıcının IndexedDB'sine bağlıdır, sayfa kapanınca kaybolmaz.

Kod sunucu sürümüyle aynıdır; farklar yalnızca yapılandırmadadır (TARAYICI=True):
  * Sayfalar aynı sitedeki kabuk sayfasının çerçevesinde (iframe) açılabilir.
  * Uygulamanın kendi service worker'ı kaydedilmez (kabuğunkini ezerdi).
  * Sunum kipi açıktır: herkes kendi tarayıcısındaki kopyada "Süreyi ilerlet" ile turları hızlandırabilir.
"""
import json
import os
import secrets
import sys
from http.cookies import SimpleCookie

VERI = os.environ.get("AGORA_VERI", "/veri")     # tarayıcıda IndexedDB'ye bağlı klasör; testlerde geçici klasör
sys.path.insert(0, "/uygulama")
os.makedirs(VERI, exist_ok=True)

from forum import create_app, guvenlik, ornek_veri  # noqa: E402

# WebAssembly'de şifre özeti yerel koda göre birkaç kat yavaştır. Veriler yalnızca bu cihazda durduğu ve demo
# hesaplarının şifresi zaten herkesçe bilindiği için daha az yinelemeli PBKDF2 yeterlidir (sunucuda scrypt kullanılır).
guvenlik.SIFRE_YONTEMI = "pbkdf2:sha256:20000"


def _gizli_anahtar():
    """Oturum çerezlerini imzalayan anahtar; ilk açılışta üretilir ve /veri ile birlikte saklanır."""
    yol = os.path.join(VERI, "gizli_anahtar.txt")
    if not os.path.exists(yol):
        with open(yol, "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(32))
    with open(yol, encoding="utf-8") as f:
        return f.read().strip()


app = create_app({"VERITABANI": os.path.join(VERI, "forum.db"), "SECRET_KEY": _gizli_anahtar(),
                  "DEMO": True, "TARAYICI": True})
YENI = ornek_veri.gerekirse_yukle(app.config["VERITABANI"])     # ilk açılışta demo verisi
_istemci = app.test_client(use_cookies=False)

# Çerezler (oturum) burada tutulur: service worker tarayıcının çerezlerini okuyamaz, yapay yanıtla çerez de kuramaz.
# /veri altında saklandıkları için sayfa yenilenince oturum açık kalır. Süre denetimi Flask'ın kendi imzalı oturumundadır.
_CEREZ_DOSYASI = os.path.join(VERI, "cerezler.json")


def _cerezleri_oku():
    try:
        with open(_CEREZ_DOSYASI, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


_cerezler = _cerezleri_oku()


def _cerezleri_guncelle(yanit):
    degisti = False
    for satir in yanit.headers.getlist("Set-Cookie"):
        cerez = SimpleCookie()
        cerez.load(satir)
        for ad, morsel in cerez.items():
            silinecek = morsel["max-age"] == "0" or "1970" in morsel["expires"] or not morsel.value
            if silinecek:
                degisti |= _cerezler.pop(ad, None) is not None
            elif _cerezler.get(ad) != morsel.value:
                _cerezler[ad] = morsel.value
                degisti = True
    if degisti:
        with open(_CEREZ_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(_cerezler, f)


def istek(yontem, kok, yol, basliklar, govde):
    """kok: uygulamanın tam adresi (ör. https://baki-b.github.io/YZM327-Odevler/app); yol: kökten sonrası (/konular?s=2).
    Döner: (durum kodu, [(başlık, değer)...], gövde bayt dizisi)."""
    basliklar = dict(basliklar.to_py()) if hasattr(basliklar, "to_py") else dict(basliklar or {})
    govde = bytes(govde.to_py()) if hasattr(govde, "to_py") else bytes(govde or b"")
    for ad in ("cookie", "host", "content-length"):
        basliklar.pop(ad, None)
    if _cerezler:
        basliklar["Cookie"] = "; ".join(f"{ad}={deger}" for ad, deger in _cerezler.items())
    yanit = _istemci.open(yol, method=yontem, base_url=kok, headers=basliklar, data=govde or None,
                          follow_redirects=False)
    _cerezleri_guncelle(yanit)
    cikis = [(ad, deger) for ad, deger in yanit.headers.items() if ad.lower() not in ("set-cookie", "content-length")]
    return yanit.status_code, cikis, yanit.get_data()
