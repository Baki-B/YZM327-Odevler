"""Şablonların kullandığı genel değişkenler, bağlam ve filtreler.

Saf filtreler (tarih, gün, kalan süre, göreli zaman) modül düzeyinde fonksiyonlardır: Flask olmadan test edilebilir.
Filtreler FILTRELER sözlüğünden döngüyle kaydedilir (Registry)."""
from flask import g, request

from .. import ayarlar, bildirimler, konular, ontoloji, oylama, sikayetler, uygunluk, yonetim, yonetmelik, zaman
from ..konu_durumlari import durumu
from ..metin import yuzde
from . import csrf_token, db_al, ikonlar, yardimcilar


def tarih(deger):
    return zaman.coz(deger).strftime("%d.%m.%Y %H:%M") if deger else ""


def gun(deger):
    return zaman.coz(deger).strftime("%d.%m.%Y") if deger else ""


def kalan(deger):
    fark = zaman.coz(deger) - zaman.simdi()
    if fark.total_seconds() <= 0:
        return "süresi doldu"
    saat, dakika = fark.seconds // 3600, (fark.seconds % 3600) // 60
    if fark.days:
        return f"{fark.days} gün {saat} saat kaldı"
    return f"{saat} saat {dakika} dk kaldı" if saat else f"{dakika} dk kaldı"


def once(deger):
    """Göreli zaman: "az önce", "5 dk önce", "3 saat önce", "2 gün önce"."""
    if not deger:
        return ""
    saniye = (zaman.simdi() - zaman.coz(deger)).total_seconds()
    if saniye < 60:
        return "az önce"
    if saniye < 3600:
        return f"{int(saniye // 60)} dk önce"
    if saniye < 86400:
        return f"{int(saniye // 3600)} saat önce"
    if saniye < 30 * 86400:
        return f"{int(saniye // 86400)} gün önce"
    return zaman.coz(deger).strftime("%d.%m.%Y")


def kategori_rengi(kategori_id):
    return ontoloji.kategori_rengi(db_al(), kategori_id) if kategori_id else ayarlar.VARSAYILAN_KATEGORI_RENGI


def konum(konum_id):
    return ontoloji.yol_metni(db_al(), "konumlar", konum_id) if konum_id else "—"


def kategori(kategori_id):
    return ontoloji.yol_metni(db_al(), "kategoriler", kategori_id) if kategori_id else "—"


FILTRELER = {"tarih": tarih, "gun": gun, "kalan": kalan, "once": once, "kategori_rengi": kategori_rengi,
             "yuzde": yuzde, "konum": konum, "kategori": kategori, "bicimle": yardimcilar.bicimle}


def sablon_degiskenleri():
    k = getattr(g, "kullanici", None)
    db = db_al()
    ortak = {"yan_kategoriler": konular.kategori_ozeti(db), "site_duyurusu": yonetim.site_ayari(db, "duyuru"),
             "mobil_uygulama": ayarlar.MOBIL_UA in request.headers.get("User-Agent", "")}
    if not k:
        return dict(ortak, kullanici=None, bekleyen_oy=0, okunmamis=0, askida=False, acik_sikayet=0)
    return dict(ortak, kullanici=k, bekleyen_oy=oylama.bekleyen_oy_sayisi(db, k),
                okunmamis=bildirimler.okunmamis_sayisi(db, k["id"]), askida=uygunluk.askida_mi(k),
                acik_sikayet=sikayetler.acik_sayisi(db) if k["yonetici_mi"] else 0)


def kur(app):
    app.jinja_env.globals.update(ayarlar=ayarlar, csrf_token=csrf_token, avatar=yardimcilar.avatar, ikon=ikonlar.ikon,
                                 durum_nesnesi=durumu,
                                 parametre=lambda kod: yonetmelik.parametre_metni(db_al(), kod))
    app.context_processor(sablon_degiskenleri)
    for ad, filtre in FILTRELER.items():
        app.add_template_filter(filtre, ad)
