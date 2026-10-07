"""Üyeler: kayıt, giriş, şifre kurtarma, adres ve yapay zeka hesapları."""
import re
from datetime import date, timedelta

from . import ayarlar, defter, gunluk, guvenlik, ontoloji, uygunluk, yonetmelik, zaman
from .hatalar import KuralHatasi

TAKMA_AD_DESENI = re.compile(r"^[A-Za-z0-9_.çğıöşüÇĞİÖŞÜ]{3,30}$")
KAYIT_SINIRI = (20, 60)          # bir IP adresinden 60 dakikada en fazla 20 yeni üyelik (sahte hesap seli)


def _benzer_takma_ad_var_mi(db, takma_ad):
    """Türkçe büyük/küçük harf ve şapkasız yazım farkı taklide izin vermesin: Çağlar = çağlar = CAGLAR = Caglar."""
    aranan = ontoloji.katla(takma_ad)
    return any(ontoloji.katla(r["takma_ad"]) == aranan for r in db.execute("SELECT takma_ad FROM kullanicilar"))


def getir(db, kullanici_id):
    return db.execute("SELECT * FROM kullanicilar WHERE id = ?", (kullanici_id,)).fetchone()


def takma_ad_ile(db, takma_ad):
    return db.execute("SELECT * FROM kullanicilar WHERE takma_ad = ?", ((takma_ad or "").strip(),)).fetchone()


def _konum_dogrula(db, konum_id):
    try:
        konum_id = int(konum_id)
    except (TypeError, ValueError):
        raise KuralHatasi("İl/ilçe seçmelisin.")
    d = ontoloji.dugum(db, "konumlar", konum_id)
    if not d or d["tur"] not in ("IL", "ILCE"):
        raise KuralHatasi("İl/ilçe seçmelisin.")
    return konum_id


def kayit(db, ad_soyad, takma_ad, sifre, sifre_tekrar, dogum_tarihi, konum_id, istemci=None):
    """Yeni üye. Döner: (id, kurtarma_kodu) — kurtarma kodu sadece bu an gösterilir.
    istemci: isteğin IP adresi (web); verilirse aynı adresten saatlik üyelik sınırı uygulanır."""
    from . import yonetim
    if yonetim.site_ayari(db, "kayit_acik") != "1":
        raise KuralHatasi("Yeni üyelik şu an kapalı.")
    ad_soyad, takma_ad = (ad_soyad or "").strip(), (takma_ad or "").strip()
    if not 3 <= len(ad_soyad) <= 100 or not any(c.isalpha() for c in ad_soyad):
        raise KuralHatasi("Ad soyad 3–100 karakter olmalı.")
    if not TAKMA_AD_DESENI.match(takma_ad):
        raise KuralHatasi("Takma ad 3–30 karakter olmalı; harf, rakam, nokta ve alt çizgi kullanılabilir.")
    if takma_ad_ile(db, takma_ad) or _benzer_takma_ad_var_mi(db, takma_ad):
        raise KuralHatasi("Bu takma ad (ya da yazılışı çok benzeri) alınmış.")
    if yonetmelik.kaba_ifadeler(takma_ad):
        raise KuralHatasi("Takma ad kaba ifade içeremez.")
    guvenlik.sifre_kontrol(sifre, sifre_tekrar)
    try:
        dogum = date.fromisoformat(dogum_tarihi or "")
    except ValueError:
        raise KuralHatasi("Doğum tarihini gir.")
    if dogum >= zaman.simdi().date():
        raise KuralHatasi("Doğum tarihi geçmişte olmalı.")
    if uygunluk.yas(dogum.isoformat()) < ayarlar.MIN_KAYIT_YASI:
        raise KuralHatasi(f"Kayıt için en az {ayarlar.MIN_KAYIT_YASI} yaşında olmalısın.")
    if uygunluk.yas(dogum.isoformat()) > 120:
        raise KuralHatasi("Geçerli bir doğum tarihi gir.")
    konum_id = _konum_dogrula(db, konum_id)
    kod = guvenlik.kurtarma_kodu_uret()
    kullanici_id = db.execute(
        """INSERT INTO kullanicilar (ad_soyad, takma_ad, sifre_hash, kurtarma_hash, dogum_tarihi, konum_id, olusturma)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ad_soyad, takma_ad, guvenlik.sifre_hash(sifre), guvenlik.kurtarma_hash(kod), dogum.isoformat(), konum_id,
         zaman.simdi_metin())).lastrowid
    if istemci is not None:
        guvenlik.hiz_siniri(db, f"kayit|{istemci}", *KAYIT_SINIRI,
                            "Bu bağlantıdan çok sayıda yeni üyelik açıldı; bir süre sonra tekrar dene.")
    gunluk.kaydet(db, kullanici_id, "KAYIT", f"@{takma_ad} foruma katıldı")
    defter.ekle(db, "UYE", {"takma_ad": takma_ad, "yz": False})
    return kullanici_id, kod


def giris(db, takma_ad, sifre, istemci=""):
    anahtar = f"{(takma_ad or '').strip().lower()}|{istemci}"
    guvenlik.giris_kilitli_mi(db, anahtar)
    k = takma_ad_ile(db, takma_ad)
    if not k or not guvenlik.sifre_dogru_mu(k["sifre_hash"], sifre):
        guvenlik.hatali_giris(db, anahtar)
        raise KuralHatasi("Takma ad ya da şifre hatalı.")
    guvenlik.basarili_giris(db, anahtar)
    db.execute("UPDATE kullanicilar SET son_giris = ? WHERE id = ?", (zaman.simdi_metin(), k["id"]))
    return k


def _sifre_sor(db, kullanici, sifre, hata):
    """Oturum açıkken şifre soran işlemler de giriş gibi deneme sınırına tabidir (çalınan oturumla tahmin edilemesin)."""
    anahtar = f"sifre|{kullanici['id']}"
    guvenlik.giris_kilitli_mi(db, anahtar)
    if not guvenlik.sifre_dogru_mu(kullanici["sifre_hash"], sifre):
        guvenlik.hatali_giris(db, anahtar)
        raise KuralHatasi(hata)
    guvenlik.basarili_giris(db, anahtar)


def sifre_degistir(db, kullanici, eski, yeni, yeni_tekrar):
    _sifre_sor(db, kullanici, eski, "Mevcut şifre hatalı.")
    guvenlik.sifre_kontrol(yeni, yeni_tekrar)
    db.execute("UPDATE kullanicilar SET sifre_hash = ? WHERE id = ?", (guvenlik.sifre_hash(yeni), kullanici["id"]))
    guvenlik.oturumlari_kapat(db, kullanici["id"])
    gunluk.kaydet(db, kullanici["id"], "SIFRE", "Şifresini değiştirdi")


def sifre_sifirla(db, takma_ad, kurtarma_kodu, yeni, yeni_tekrar, istemci=""):
    """Kurtarma koduyla şifre sıfırlar ve YENİ bir kurtarma kodu döndürür (eski kod geçersiz olur)."""
    anahtar = f"kurtarma|{(takma_ad or '').strip().lower()}|{istemci}"
    guvenlik.giris_kilitli_mi(db, anahtar)
    k = takma_ad_ile(db, takma_ad)
    if not k or not guvenlik.kurtarma_dogru_mu(k["kurtarma_hash"], kurtarma_kodu):
        guvenlik.hatali_giris(db, anahtar)
        raise KuralHatasi("Takma ad ya da kurtarma kodu hatalı.")
    guvenlik.sifre_kontrol(yeni, yeni_tekrar)
    kod = guvenlik.kurtarma_kodu_uret()
    db.execute("UPDATE kullanicilar SET sifre_hash = ?, kurtarma_hash = ? WHERE id = ?",
               (guvenlik.sifre_hash(yeni), guvenlik.kurtarma_hash(kod), k["id"]))
    guvenlik.oturumlari_kapat(db, k["id"])
    guvenlik.basarili_giris(db, anahtar)
    gunluk.kaydet(db, k["id"], "SIFRE", "Şifresini kurtarma koduyla sıfırladı")
    return k, kod


def kurtarma_kodu_yenile(db, kullanici, sifre):
    _sifre_sor(db, kullanici, sifre, "Şifre hatalı.")
    kod = guvenlik.kurtarma_kodu_uret()
    db.execute("UPDATE kullanicilar SET kurtarma_hash = ? WHERE id = ?", (guvenlik.kurtarma_hash(kod), kullanici["id"]))
    return kod


def bekleyen_adresi_uygula(db, kullanici):
    if kullanici and kullanici["bekleyen_konum_id"] and kullanici["konum_gecerlilik"] <= zaman.simdi_metin():
        db.execute("UPDATE kullanicilar SET konum_id = bekleyen_konum_id, bekleyen_konum_id = NULL, "
                   "konum_gecerlilik = NULL WHERE id = ?", (kullanici["id"],))
        db.commit()
        return getir(db, kullanici["id"])
    return kullanici


def adres_degistir(db, kullanici, konum_id):
    konum_id = _konum_dogrula(db, konum_id)
    if konum_id == kullanici["konum_id"]:
        raise KuralHatasi("Zaten bu adreste kayıtlısın.")
    gecerlilik = zaman.simdi() + timedelta(days=yonetmelik.deger(db, "ADRES_BEKLEME_GUN"))
    db.execute("UPDATE kullanicilar SET bekleyen_konum_id = ?, konum_gecerlilik = ? WHERE id = ?",
               (konum_id, zaman.metin(gecerlilik), kullanici["id"]))
    gunluk.kaydet(db, kullanici["id"], "ADRES", f"Adres değişikliği bildirdi; {gecerlilik:%d.%m.%Y} tarihinde geçerli olacak")
    return gecerlilik


def adres_degisikligini_iptal(db, kullanici):
    db.execute("UPDATE kullanicilar SET bekleyen_konum_id = NULL, konum_gecerlilik = NULL WHERE id = ?",
               (kullanici["id"],))


# --- YZ hesapları ---

def yz_ekle(db, yonetici, takma_ad):
    if not yonetici["yonetici_mi"]:
        raise KuralHatasi("Bu işlem için yönetici olmalısın.")
    if db.execute("SELECT COUNT(*) FROM kullanicilar WHERE yz_mi = 1").fetchone()[0] >= ayarlar.MAX_YZ_HESABI:
        raise KuralHatasi(f"En fazla {ayarlar.MAX_YZ_HESABI} yapay zeka hesabı açılabilir.")
    takma_ad = (takma_ad or "").strip()
    if not TAKMA_AD_DESENI.match(takma_ad) or takma_ad_ile(db, takma_ad) or _benzer_takma_ad_var_mi(db, takma_ad):
        raise KuralHatasi("Geçersiz ya da alınmış takma ad.")
    kullanici_id = db.execute("INSERT INTO kullanicilar (takma_ad, yz_mi, olusturma) VALUES (?, 1, ?)",
                              (takma_ad, zaman.simdi_metin())).lastrowid
    gunluk.kaydet(db, yonetici["id"], "YZ", f"YZ hesabı açıldı: @{takma_ad}")
    defter.ekle(db, "UYE", {"takma_ad": takma_ad, "yz": True})
    return kullanici_id


def tum_kullanicilar(db):
    return db.execute("SELECT * FROM kullanicilar ORDER BY yz_mi, takma_ad").fetchall()


def acik_oylari(db, kullanici_id):
    """Uzman oyları (ağırlıklı oylar), oylama bittikten sonra herkese açıktır."""
    return db.execute(
        """SELECT o.*, t.tip, t.konu_id, t.id AS teklif_no FROM oylar o JOIN teklifler t ON t.id = o.teklif_id
           WHERE o.kullanici_id = ? AND o.agirlik > 1 AND t.durum != 'ACIK' ORDER BY o.zaman DESC LIMIT 20""",
        (kullanici_id,)).fetchall()
