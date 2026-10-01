"""Güvenlik: giriş denemesi sınırı, şifre kurtarma kodu, API anahtarları."""
import hashlib
import secrets
from datetime import timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from . import ayarlar, zaman
from .hatalar import KuralHatasi


# --- Kaba kuvvet saldırısına karşı giriş sınırı ---

def giris_kilitli_mi(db, anahtar):
    r = db.execute("SELECT * FROM giris_denemeleri WHERE anahtar = ?", (anahtar,)).fetchone()
    if r and r["kilit_bitis"] and r["kilit_bitis"] > zaman.simdi_metin():
        kalan = zaman.coz(r["kilit_bitis"]) - zaman.simdi()
        raise KuralHatasi(f"Çok fazla hatalı giriş denemesi. {max(1, kalan.seconds // 60)} dakika sonra tekrar dene.")


def hatali_giris(db, anahtar):
    r = db.execute("SELECT * FROM giris_denemeleri WHERE anahtar = ?", (anahtar,)).fetchone()
    sayi = (r["sayi"] if r and not r["kilit_bitis"] else 0) + 1
    kilit = None
    if sayi >= ayarlar.GIRIS_DENEME_SINIRI:
        kilit = zaman.metin(zaman.simdi() + timedelta(minutes=ayarlar.GIRIS_KILIT_DAKIKA))
        sayi = 0
    db.execute("INSERT INTO giris_denemeleri (anahtar, sayi, kilit_bitis) VALUES (?, ?, ?) "
               "ON CONFLICT (anahtar) DO UPDATE SET sayi = excluded.sayi, kilit_bitis = excluded.kilit_bitis",
               (anahtar, sayi, kilit))
    db.commit()


def basarili_giris(db, anahtar):
    db.execute("DELETE FROM giris_denemeleri WHERE anahtar = ?", (anahtar,))


# --- Şifre ---

def sifre_kontrol(sifre, tekrar):
    if len(sifre or "") < ayarlar.SIFRE_MIN:
        raise KuralHatasi(f"Şifre en az {ayarlar.SIFRE_MIN} karakter olmalı.")
    if not any(c.isdigit() for c in sifre) or not any(c.isalpha() for c in sifre):
        raise KuralHatasi("Şifre en az bir harf ve bir rakam içermeli.")
    if sifre != tekrar:
        raise KuralHatasi("Şifreler aynı değil.")


def sifre_hash(sifre):
    return generate_password_hash(sifre)


def sifre_dogru_mu(hash_, sifre):
    return bool(hash_) and check_password_hash(hash_, sifre or "")


# --- Kurtarma kodu (e-posta olmadan şifre sıfırlama) ---

def kurtarma_kodu_uret():
    parcalar = [secrets.token_hex(2).upper() for _ in range(4)]
    return "AGORA-" + "-".join(parcalar)


def kurtarma_hash(kod):
    return generate_password_hash(kod.strip().upper())


def kurtarma_dogru_mu(hash_, kod):
    return bool(hash_) and check_password_hash(hash_, (kod or "").strip().upper())


# --- API anahtarları (mobil uygulama / dış istemciler) ---

def _anahtar_ozeti(anahtar):
    return hashlib.sha256(anahtar.encode()).hexdigest()


def api_anahtari_olustur(db, kullanici_id, ad):
    ad = (ad or "").strip() or "Uygulama"
    if db.execute("SELECT COUNT(*) FROM api_anahtarlari WHERE kullanici_id = ?", (kullanici_id,)).fetchone()[0] >= 5:
        raise KuralHatasi("En fazla 5 API anahtarın olabilir; önce birini sil.")
    anahtar = "agr_" + secrets.token_urlsafe(32)
    db.execute("INSERT INTO api_anahtarlari (kullanici_id, ad, anahtar_hash, olusturma) VALUES (?, ?, ?, ?)",
               (kullanici_id, ad[:40], _anahtar_ozeti(anahtar), zaman.simdi_metin()))
    return anahtar


def api_anahtari_kullanici(db, anahtar):
    r = db.execute("SELECT * FROM api_anahtarlari WHERE anahtar_hash = ?", (_anahtar_ozeti(anahtar),)).fetchone()
    if not r:
        return None
    db.execute("UPDATE api_anahtarlari SET son_kullanim = ? WHERE id = ?", (zaman.simdi_metin(), r["id"]))
    return db.execute("SELECT * FROM kullanicilar WHERE id = ?", (r["kullanici_id"],)).fetchone()


def api_anahtarlari(db, kullanici_id):
    return db.execute("SELECT id, ad, olusturma, son_kullanim FROM api_anahtarlari WHERE kullanici_id = ? "
                      "ORDER BY id DESC", (kullanici_id,)).fetchall()


def api_anahtari_sil(db, kullanici_id, anahtar_id):
    db.execute("DELETE FROM api_anahtarlari WHERE id = ? AND kullanici_id = ?", (anahtar_id, kullanici_id))
