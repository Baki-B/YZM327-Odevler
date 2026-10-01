"""Anlık bildirim (push): her site bildirimi, bildirimleri açmış cihazlara da gönderilir.

İki kanal var, ikisi de isteğe bağlıdır:
  * WEB: tarayıcı ve ana ekrana eklenen web uygulaması (Web Push, VAPID). `pip install pywebpush` gerekir;
    anahtarlar ilk kullanımda instance/vapid_ozel.pem dosyasına üretilir. Tarayıcılar bunu yalnızca HTTPS adreslerde
    (ya da bilgisayarın kendisindeki localhost'ta) izin verir.
  * FCM: mobil/ klasöründeki Android uygulaması (Firebase Cloud Messaging). instance/firebase.json dosyasına Firebase
    hizmet hesabı anahtarı konunca açılır (adımlar mobil/BENIOKU.md'de).
Gönderim, veritabanı işlemi kaydedildikten sonra arka planda yapılır; istek beklemez. Geçersizleşen abonelikler silinir.
"""
import base64
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from . import ayarlar, zaman
from .hatalar import KuralHatasi

log = logging.getLogger(__name__)
_kilit = threading.Lock()
_fcm_erisim = {"anahtar": None, "bitis": 0}


def _instance(db):
    return os.path.dirname(os.path.abspath(db.yol))


def _b64(veri):
    return base64.urlsafe_b64encode(veri).rstrip(b"=").decode()


# --- Kanalların durumu ---

def web_etkin():
    import importlib.util
    return importlib.util.find_spec("pywebpush") is not None


def _vapid_yolu(db):
    return os.path.join(_instance(db), "vapid_ozel.pem")


def vapid_acik_anahtar(db):
    """Tarayıcının abone olurken istediği sunucu anahtarı (applicationServerKey). Gerekirse anahtar çiftini üretir."""
    if not web_etkin():
        return None
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    yol = _vapid_yolu(db)
    with _kilit:
        if not os.path.exists(yol):
            ozel = ec.generate_private_key(ec.SECP256R1())
            with open(yol, "wb") as f:
                f.write(ozel.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
        with open(yol, "rb") as f:
            ozel = serialization.load_pem_private_key(f.read(), password=None)
    return _b64(ozel.public_key().public_bytes(serialization.Encoding.X962,
                                               serialization.PublicFormat.UncompressedPoint))


def _fcm_hesabi(db):
    yol = os.path.join(_instance(db), "firebase.json")
    if not os.path.exists(yol):
        return None
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def fcm_etkin(db):
    return _fcm_hesabi(db) is not None and web_etkin()   # imza için cryptography gerekir (pywebpush ile gelir)


def durum(db):
    return {"web": web_etkin(), "fcm": fcm_etkin(db)}


# --- Abonelikler ---

def abone_ol(db, kullanici, tur, veri, cihaz=""):
    if tur == "WEB":
        adres = (veri or {}).get("endpoint", "")
        anahtarlar = (veri or {}).get("keys") or {}
        if not adres.startswith("https://") or not anahtarlar.get("p256dh") or not anahtarlar.get("auth"):
            raise KuralHatasi("Geçersiz tarayıcı aboneliği.")
        anahtar_json = json.dumps({"p256dh": anahtarlar["p256dh"], "auth": anahtarlar["auth"]})
    elif tur == "FCM":
        adres, anahtar_json = str((veri or {}).get("token", "")), None
        if not 20 <= len(adres) <= 4096:
            raise KuralHatasi("Geçersiz cihaz anahtarı.")
    else:
        raise KuralHatasi("Geçersiz bildirim kanalı.")
    db.execute(
        """INSERT INTO anlik_abonelikler (kullanici_id, tur, adres, anahtarlar, cihaz, olusturma) VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(adres) DO UPDATE SET kullanici_id = excluded.kullanici_id, anahtarlar = excluded.anahtarlar,
           cihaz = excluded.cihaz""",
        (kullanici["id"], tur, adres, anahtar_json, (cihaz or "")[:80], zaman.simdi_metin()))


def abonelikten_cik(db, kullanici, adres):
    db.execute("DELETE FROM anlik_abonelikler WHERE kullanici_id = ? AND adres = ?", (kullanici["id"], adres or ""))


def abonelikler(db, kullanici_id):
    return db.execute("SELECT * FROM anlik_abonelikler WHERE kullanici_id = ? ORDER BY id DESC",
                      (kullanici_id,)).fetchall()


# --- Gönderim ---

def kuyruga_ekle(db, kullanici_id, metin, baglanti):
    """bildirimler.gonder çağırır. İşlem kaydedilince (commit) arka planda gönderilir; geri alınırsa gönderilmez."""
    if not hasattr(db, "commit_sonrasi"):
        return
    hedefler = [dict(r) for r in db.execute("SELECT * FROM anlik_abonelikler WHERE kullanici_id = ?", (kullanici_id,))]
    if not hedefler:
        return
    kuyruk = getattr(db, "anlik_kuyrugu", None)
    if kuyruk is None:
        kuyruk = db.anlik_kuyrugu = []
        yol = db.yol

        def gonder_hepsi():
            isler, db.anlik_kuyrugu = db.anlik_kuyrugu, None
            threading.Thread(target=_gonder, args=(yol, isler), daemon=True).start()
        db.commit_sonrasi.append(gonder_hepsi)
    yuk = json.dumps({"baslik": ayarlar.SITE_ADI, "metin": metin[:240], "url": baglanti or "/bildirimler"},
                     ensure_ascii=False)
    kuyruk.extend((h, yuk) for h in hedefler)


def _gonder(yol, isler):
    from . import veritabani
    db = veritabani.baglan(yol)
    try:
        silinecek = []
        for abonelik, yuk in isler:
            try:
                gecerli = (_web_gonder(db, abonelik, yuk) if abonelik["tur"] == "WEB"
                           else _fcm_gonder(db, abonelik, yuk))
            except Exception:                       # ağ hatası: abonelik kalır, bir sonraki bildirimde tekrar denenir
                log.exception("Anlık bildirim gönderilemedi")
                continue
            if not gecerli:
                silinecek.append(abonelik["id"])
        for i in silinecek:
            db.execute("DELETE FROM anlik_abonelikler WHERE id = ?", (i,))
        db.commit()
    finally:
        db.close()


def _web_gonder(db, abonelik, yuk):
    """Döner: abonelik hâlâ geçerli mi."""
    from pywebpush import WebPushException, webpush
    try:
        webpush({"endpoint": abonelik["adres"], "keys": json.loads(abonelik["anahtarlar"])}, data=yuk,
                vapid_private_key=_vapid_yolu(db), timeout=10, ttl=86400,
                vapid_claims={"sub": os.environ.get("FORUM_ANLIK_ILETISIM", "mailto:agora@example.com")})
        return True
    except WebPushException as e:
        if e.response is not None and e.response.status_code in (404, 410):
            return False
        raise


def _fcm_erisim_anahtari(hesap):
    """Hizmet hesabıyla imzalanmış JWT karşılığında kısa ömürlü OAuth erişim anahtarı alır (saatlik önbellek)."""
    with _kilit:
        if _fcm_erisim["anahtar"] and _fcm_erisim["bitis"] > time.time() + 60:
            return _fcm_erisim["anahtar"]
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    an = int(time.time())
    govde = {"iss": hesap["client_email"], "scope": "https://www.googleapis.com/auth/firebase.messaging",
             "aud": hesap.get("token_uri", "https://oauth2.googleapis.com/token"), "iat": an, "exp": an + 3600}
    imzalanacak = (_b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()) + "." +
                   _b64(json.dumps(govde).encode()))
    anahtar = serialization.load_pem_private_key(hesap["private_key"].encode(), password=None)
    jwt = imzalanacak + "." + _b64(anahtar.sign(imzalanacak.encode(), padding.PKCS1v15(), hashes.SHA256()))
    istek = urllib.request.Request(govde["aud"], data=urllib.parse.urlencode(
        {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt}).encode())
    with urllib.request.urlopen(istek, timeout=10) as y:
        cevap = json.load(y)
    with _kilit:
        _fcm_erisim.update(anahtar=cevap["access_token"], bitis=time.time() + int(cevap.get("expires_in", 3600)))
    return cevap["access_token"]


def _fcm_gonder(db, abonelik, yuk):
    hesap = _fcm_hesabi(db)
    if not hesap:
        return True
    v = json.loads(yuk)
    mesaj = {"message": {"token": abonelik["adres"], "notification": {"title": v["baslik"], "body": v["metin"]},
                         "data": {"url": v["url"]}, "android": {"priority": "high"}}}
    istek = urllib.request.Request(
        f"https://fcm.googleapis.com/v1/projects/{hesap['project_id']}/messages:send",
        data=json.dumps(mesaj).encode(), headers={"Authorization": f"Bearer {_fcm_erisim_anahtari(hesap)}",
                                                  "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=10):
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404 or (e.code == 400 and b"UNREGISTERED" in e.read()):
            return False                            # uygulama silinmiş ya da anahtar yenilenmiş
        raise
