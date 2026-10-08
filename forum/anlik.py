"""Anlık bildirim (push): her site bildirimi, bildirimleri açmış cihazlara da gönderilir.

İki kanal var, ikisi de isteğe bağlıdır:
  * WEB: tarayıcı ve ana ekrana eklenen web uygulaması (Web Push, VAPID). `pip install pywebpush==2.5.0` gerekir;
    anahtarlar ilk kullanımda instance/vapid_ozel.pem dosyasına üretilir. Tarayıcılar bunu yalnızca HTTPS adreslerde
    (ya da bilgisayarın kendisindeki localhost'ta) izin verir.
  * FCM: mobil/ klasöründeki Android uygulaması (Firebase Cloud Messaging). instance/firebase.json dosyasına Firebase
    hizmet hesabı anahtarı konunca açılır (adımlar mobil/BENIOKU.md'de).
Gönderim, veritabanı işlemi kaydedildikten sonra arka planda yapılır; istek beklemez. Geçersizleşen abonelikler silinir.

Tasarım — GoF **Adapter**: iki kanalın dış API'leri birbirine hiç benzemez (pywebpush'ın webpush() fonksiyonu ile
Firebase'in JWT + HTTP v1 uç noktası). Her biri AnlikKanal hedef arayüzüne uyarlanır; forumun geri kalanı yalnızca
`etkin / abonelik_coz / gonder` bilir. Kanallar KANALLAR sözlüğünde durur (Strategy): üçüncü bir kanal (ör. iOS)
yeni bir sınıf demektir; testler bu sözlüğe sahte bir kanal koyar (bağımlılığı tersine çevirme).
"""
import base64
import importlib.util
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod

from . import ayarlar, zaman
from .hatalar import KuralHatasi

log = logging.getLogger(__name__)
_kilit = threading.Lock()
# Tarayıcıların Web Push servisleri. Abonelik adresi yalnızca bunlardan biri olabilir: sunucu bu adrese istek
# attığı için, serbest bir adres kabul etmek iç ağa istek attırmaya (SSRF) kapı açardı.
PUSH_SERVISLERI = ("fcm.googleapis.com", "android.googleapis.com", "push.services.mozilla.com",
                   "notify.windows.com", "push.apple.com")


def push_adresi_gecerli_mi(adres):
    parca = urllib.parse.urlsplit(adres or "")
    ad = (parca.hostname or "").lower()
    return parca.scheme == "https" and parca.port in (None, 443) and \
        any(ad == s or ad.endswith("." + s) for s in PUSH_SERVISLERI)


def _instance(db):
    return os.path.dirname(os.path.abspath(db.yol))


def _b64(veri):
    return base64.urlsafe_b64encode(veri).rstrip(b"=").decode()


def _cryptography_var():
    return importlib.util.find_spec("cryptography") is not None


# --- Hedef arayüz ---

class AnlikKanal(ABC):
    """Bir anlık bildirim kanalı. `klasor`: sunucunun instance klasörü (anahtar dosyaları burada)."""
    kod = ""

    @abstractmethod
    def etkin(self, klasor):
        """Kanal bu sunucuda kullanılabilir mi (kütüphane ve anahtarlar hazır mı)?"""

    @abstractmethod
    def abonelik_coz(self, veri):
        """İstemcinin gönderdiği abonelik verisini doğrular. Döner: (adres, anahtarlar_json ya da None)."""

    @abstractmethod
    def gonder(self, klasor, abonelik, yuk):
        """Bildirimi gönderir. Döner: abonelik hâlâ geçerli mi (False ise silinir). Ağ hatasında istisna fırlatır."""


class WebPushKanali(AnlikKanal):
    """pywebpush kütüphanesini AnlikKanal arayüzüne uyarlar."""
    kod = "WEB"

    def etkin(self, klasor):
        return importlib.util.find_spec("pywebpush") is not None

    def vapid_yolu(self, klasor):
        return os.path.join(klasor, "vapid_ozel.pem")

    def acik_anahtar(self, klasor):
        """Tarayıcının abone olurken istediği sunucu anahtarı (applicationServerKey). Gerekirse anahtar çiftini üretir."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        yol = self.vapid_yolu(klasor)
        with _kilit:
            if not os.path.exists(yol):
                ozel = ec.generate_private_key(ec.SECP256R1())
                with os.fdopen(os.open(yol, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as f:
                    f.write(ozel.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
            with open(yol, "rb") as f:
                ozel = serialization.load_pem_private_key(f.read(), password=None)
        return _b64(ozel.public_key().public_bytes(serialization.Encoding.X962,
                                                   serialization.PublicFormat.UncompressedPoint))

    def abonelik_coz(self, veri):
        adres = (veri or {}).get("endpoint", "")
        anahtarlar = (veri or {}).get("keys") or {}
        if not push_adresi_gecerli_mi(adres) or not anahtarlar.get("p256dh") or not anahtarlar.get("auth"):
            raise KuralHatasi("Geçersiz tarayıcı aboneliği.")
        return adres, json.dumps({"p256dh": anahtarlar["p256dh"], "auth": anahtarlar["auth"]})

    def gonder(self, klasor, abonelik, yuk):
        from pywebpush import WebPushException, webpush
        try:
            webpush({"endpoint": abonelik["adres"], "keys": json.loads(abonelik["anahtarlar"])}, data=yuk,
                    vapid_private_key=self.vapid_yolu(klasor), timeout=10, ttl=86400,
                    vapid_claims={"sub": os.environ.get("FORUM_ANLIK_ILETISIM", "mailto:agora@example.com")})
            return True
        except WebPushException as e:
            if e.response is not None and e.response.status_code in (404, 410):
                return False
            raise


class FcmKanali(AnlikKanal):
    """Firebase Cloud Messaging HTTP v1 uç noktasını (hizmet hesabıyla imzalı JWT → OAuth) arayüze uyarlar."""
    kod = "FCM"

    def __init__(self):
        self._erisim = {"anahtar": None, "bitis": 0}          # kısa ömürlü OAuth anahtarının önbelleği

    def hesap(self, klasor):
        yol = os.path.join(klasor, "firebase.json")
        if not os.path.exists(yol):
            return None
        with open(yol, encoding="utf-8") as f:
            return json.load(f)

    def etkin(self, klasor):
        return self.hesap(klasor) is not None and _cryptography_var()     # JWT imzası için cryptography gerekir

    def abonelik_coz(self, veri):
        adres = str((veri or {}).get("token", ""))
        if not 20 <= len(adres) <= 4096:
            raise KuralHatasi("Geçersiz cihaz anahtarı.")
        return adres, None

    def _erisim_anahtari(self, hesap):
        """Hizmet hesabıyla imzalanmış JWT karşılığında kısa ömürlü OAuth erişim anahtarı alır (saatlik önbellek)."""
        with _kilit:
            if self._erisim["anahtar"] and self._erisim["bitis"] > time.time() + 60:
                return self._erisim["anahtar"]
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
            self._erisim.update(anahtar=cevap["access_token"], bitis=time.time() + int(cevap.get("expires_in", 3600)))
        return cevap["access_token"]

    def gonder(self, klasor, abonelik, yuk):
        hesap = self.hesap(klasor)
        v = json.loads(yuk)
        mesaj = {"message": {"token": abonelik["adres"], "notification": {"title": v["baslik"], "body": v["metin"]},
                             "data": {"url": v["url"]}, "android": {"priority": "high"}}}
        istek = urllib.request.Request(
            f"https://fcm.googleapis.com/v1/projects/{hesap['project_id']}/messages:send",
            data=json.dumps(mesaj).encode(), headers={"Authorization": f"Bearer {self._erisim_anahtari(hesap)}",
                                                      "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(istek, timeout=10):
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404 or (e.code == 400 and b"UNREGISTERED" in e.read()):
                return False                        # uygulama silinmiş ya da anahtar yenilenmiş
            raise


KANALLAR = {k.kod: k for k in (WebPushKanali(), FcmKanali())}


def _kanal(tur):
    kanal = KANALLAR.get(tur)
    if kanal is None:
        raise KuralHatasi("Geçersiz bildirim kanalı.")
    return kanal


# --- Kanalların durumu ---

def vapid_acik_anahtar(db):
    kanal = KANALLAR["WEB"]
    return kanal.acik_anahtar(_instance(db)) if kanal.etkin(_instance(db)) else None


def durum(db):
    return {kod.lower(): kanal.etkin(_instance(db)) for kod, kanal in KANALLAR.items()}


# --- Abonelikler ---

def abone_ol(db, kullanici, tur, veri, cihaz=""):
    kanal = _kanal(tur)
    if not kanal.etkin(_instance(db)):
        # Kapalı kanala abonelik alınırsa her bildirimde gönderim hatası günlüğe düşer, abonelik hiç işe yaramaz.
        raise KuralHatasi("Bu bildirim kanalı sunucuda kurulu değil.")
    adres, anahtar_json = kanal.abonelik_coz(veri)
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
    hedefler = [dict(r) for r in db.execute("SELECT * FROM anlik_abonelikler WHERE kullanici_id = ?", (kullanici_id,))]
    if not hedefler:
        return
    if db.anlik_kuyrugu is None:
        db.anlik_kuyrugu = []
        yol = db.yol

        def gonder_hepsi():
            isler, db.anlik_kuyrugu = db.anlik_kuyrugu, None
            threading.Thread(target=_gonder, args=(yol, isler), daemon=True).start()
        db.commit_sonrasi.append(gonder_hepsi)
    yuk = json.dumps({"baslik": ayarlar.SITE_ADI, "metin": metin[:240], "url": baglanti or "/bildirimler"},
                     ensure_ascii=False)
    db.anlik_kuyrugu.extend((h, yuk) for h in hedefler)


def _gonder(yol, isler):
    from . import veritabani
    db = veritabani.baglan(yol)
    klasor = _instance(db)
    try:
        silinecek = []
        for abonelik, yuk in isler:
            kanal = KANALLAR.get(abonelik["tur"])
            if kanal is None or not kanal.etkin(klasor):
                continue                            # kanal sonradan kapatıldı: abonelik kalır, gönderim denenmez
            try:
                gecerli = kanal.gonder(klasor, abonelik, yuk)
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
