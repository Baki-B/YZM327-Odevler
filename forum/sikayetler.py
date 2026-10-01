"""Şikayet kutusu: üyeler bir mesajı ya da konuyu şikayet eder.

Tek bir şikayet yöneticilere gitmez: aynı içeriği en az SIKAYET_TABANI (varsayılan 3) farklı üye şikayet edince
yöneticilere ulaşır. Böylece tek kişinin keyfî şikayeti yöneticiyi meşgul etmez.

Yönetici şikayeti iki yoldan sonuçlandırır: gizleme/kaldırma oylaması açar (karar yine oylamayla verilir) ya da
yersiz bulup kapatır. Aynı içerik hakkındaki bütün açık şikayetler birlikte sonuçlanır ve şikayet edenlere bildirilir.
"""
from datetime import timedelta

from . import ayarlar, bildirimler, gunluk, konular, oylama, yonetmelik, zaman
from .hatalar import KuralHatasi

TURLER = {"MESAJ": "Mesaj", "KONU": "Konu"}
DURUMLAR = {"ACIK": "Bekliyor", "OYLAMADA": "Oylamaya alındı", "YERSIZ": "Yersiz bulundu"}
GUNLUK_SINIR = 10


def _hedef(db, tur, hedef_id):
    """Döner: (konu, mesaj ya da None). Şikayet edilebilir değilse hata verir."""
    if tur == "MESAJ":
        m = konular.mesaj_getir(db, hedef_id)
        if m["tip"] == "SISTEM" or m["yazar_id"] is None:
            raise KuralHatasi("Sistem mesajları şikayet edilemez.")
        if m["gizli"]:
            raise KuralHatasi("Bu mesaj zaten gizlenmiş.")
        konu = konular.konu_getir(db, m["konu_id"])
    elif tur == "KONU":
        m, konu = None, konular.konu_getir(db, hedef_id)
    else:
        raise KuralHatasi("Geçersiz şikayet türü.")
    if konu["silindi"]:
        raise KuralHatasi("Bu konu kaldırıldı.")
    return konu, m


def sikayet_et(db, kullanici, tur, hedef_id, neden, aciklama=""):
    try:
        hedef_id = int(hedef_id)
    except (TypeError, ValueError):
        raise KuralHatasi("Şikayet edilecek içerik bulunamadı.")
    if kullanici["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları şikayet gönderemez.")
    konu, m = _hedef(db, tur, hedef_id)
    sahip_id = m["yazar_id"] if m else konu["sahip_id"]
    if sahip_id == kullanici["id"]:
        raise KuralHatasi("Kendi mesajını şikayet edemezsin; gizletmek istersen gizleme oylaması açabilirsin." if m else
                          "Kendi konunu şikayet edemezsin.")
    if neden not in ayarlar.SILME_NEDENLERI:
        raise KuralHatasi("Bir neden seç.")
    aciklama = (aciklama or "").strip()
    if len(aciklama) > 500:
        raise KuralHatasi("Açıklama en fazla 500 karakter olabilir.")
    if aciklama:
        yonetmelik.mesaj_denetle(db, aciklama)
    if db.execute("SELECT 1 FROM sikayetler WHERE sikayetci_id = ? AND tur = ? AND hedef_id = ? AND durum = 'ACIK'",
                  (kullanici["id"], tur, hedef_id)).fetchone():
        raise KuralHatasi("Bu içerik için bekleyen bir şikayetin zaten var.")
    dun = zaman.metin(zaman.simdi() - timedelta(days=1))
    if db.execute("SELECT COUNT(*) FROM sikayetler WHERE sikayetci_id = ? AND olusturma >= ?",
                  (kullanici["id"], dun)).fetchone()[0] >= GUNLUK_SINIR:
        raise KuralHatasi(f"Bir günde en fazla {GUNLUK_SINIR} şikayet gönderebilirsin.")
    sikayet_id = db.execute(
        "INSERT INTO sikayetler (sikayetci_id, tur, hedef_id, konu_id, neden, aciklama, olusturma) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (kullanici["id"], tur, hedef_id, konu["id"], neden, aciklama or None, zaman.simdi_metin())).lastrowid
    sayi, taban = sikayetci_sayisi(db, tur, hedef_id), yonetmelik.deger(db, "SIKAYET_TABANI")
    if sayi == taban:                       # taban tam dolduğunda, bir kez
        ne = f"#{hedef_id} numaralı mesaj" if tur == "MESAJ" else f"“{konu['baslik']}” konusu"
        for (yonetici_id,) in db.execute("SELECT id FROM kullanicilar WHERE yonetici_mi = 1").fetchall():
            bildirimler.gonder(db, yonetici_id, f"{sayi} üye şikayet etti: {ne}.", "/yonetim/sikayetler")
    return sikayet_id, max(0, taban - sayi)


def sikayetci_sayisi(db, tur, hedef_id):
    return db.execute("SELECT COUNT(DISTINCT sikayetci_id) FROM sikayetler WHERE tur = ? AND hedef_id = ? "
                      "AND durum = 'ACIK'", (tur, hedef_id)).fetchone()[0]


def acik_sayisi(db):
    """Yöneticilere ulaşmış (tabanı geçmiş) farklı içerik sayısı."""
    taban = yonetmelik.deger(db, "SIKAYET_TABANI")
    return db.execute("""SELECT COUNT(*) FROM (SELECT 1 FROM sikayetler WHERE durum = 'ACIK' GROUP BY tur, hedef_id
                         HAVING COUNT(DISTINCT sikayetci_id) >= ?)""", (taban,)).fetchone()[0]


def liste(db, durum="ACIK"):
    """Şikayetleri içeriğe göre gruplar: her grup bir mesaj ya da konu, içinde o içerik hakkındaki şikayetler."""
    satirlar = db.execute(
        """SELECT s.*, k.takma_ad AS sikayetci, y.takma_ad AS yonetici FROM sikayetler s
           JOIN kullanicilar k ON k.id = s.sikayetci_id LEFT JOIN kullanicilar y ON y.id = s.yonetici_id
           WHERE s.durum = ? ORDER BY s.id DESC LIMIT 300""" if durum == "ACIK" else
        """SELECT s.*, k.takma_ad AS sikayetci, y.takma_ad AS yonetici FROM sikayetler s
           JOIN kullanicilar k ON k.id = s.sikayetci_id LEFT JOIN kullanicilar y ON y.id = s.yonetici_id
           WHERE s.durum != 'ACIK' ORDER BY s.kapanis DESC, s.id DESC LIMIT 100""", (durum,) if durum == "ACIK" else ()
    ).fetchall()
    gruplar = {}
    for s in satirlar:
        anahtar = (s["tur"], s["hedef_id"], s["durum"], s["teklif_id"])
        if anahtar not in gruplar:
            konu = db.execute("SELECT id, baslik, silindi FROM konular WHERE id = ?", (s["konu_id"],)).fetchone()
            mesaj = db.execute(
                "SELECT m.*, u.takma_ad FROM mesajlar m LEFT JOIN kullanicilar u ON u.id = m.yazar_id WHERE m.id = ?",
                (s["hedef_id"],)).fetchone() if s["tur"] == "MESAJ" else None
            suren = None
            if s["durum"] == "ACIK":
                suren = (konular.gizleme_oylamasindaki_mesajlar(db, konu["id"]).get(s["hedef_id"]) if mesaj else
                         (oylama.acik_teklif(db, "KONU_SILME", konu_id=konu["id"]) or {"id": None})["id"])
            gruplar[anahtar] = {"tur": s["tur"], "hedef_id": s["hedef_id"], "konu": konu, "mesaj": mesaj,
                                "durum": s["durum"], "teklif_id": s["teklif_id"], "suren_oylama": suren,
                                "sonuc_notu": s["sonuc_notu"], "yonetici": s["yonetici"], "kapanis": s["kapanis"],
                                "ilk_id": s["id"], "sikayetler": []}
        gruplar[anahtar]["sikayetler"].append(s)
    if durum == "ACIK":                     # tabanın altındaki şikayetler yöneticiye gösterilmez
        taban = yonetmelik.deger(db, "SIKAYET_TABANI")
        return [g for g in gruplar.values() if len({s["sikayetci_id"] for s in g["sikayetler"]}) >= taban]
    return list(gruplar.values())


def _gruptakiler(db, sikayet_id):
    s = db.execute("SELECT * FROM sikayetler WHERE id = ?", (sikayet_id,)).fetchone()
    if not s:
        raise KuralHatasi("Şikayet bulunamadı.")
    if s["durum"] != "ACIK":
        raise KuralHatasi("Bu şikayet zaten sonuçlandı.")
    if sikayetci_sayisi(db, s["tur"], s["hedef_id"]) < yonetmelik.deger(db, "SIKAYET_TABANI"):
        raise KuralHatasi("Bu içerik henüz yeterli sayıda üye tarafından şikayet edilmedi.")
    return s, db.execute("SELECT * FROM sikayetler WHERE tur = ? AND hedef_id = ? AND durum = 'ACIK'",
                         (s["tur"], s["hedef_id"])).fetchall()


def _kapat(db, yonetici, grup, durum, not_metni, teklif_id=None):
    an = zaman.simdi_metin()
    for s in grup:
        db.execute("UPDATE sikayetler SET durum = ?, sonuc_notu = ?, teklif_id = ?, yonetici_id = ?, kapanis = ? "
                   "WHERE id = ?", (durum, not_metni, teklif_id, yonetici["id"], an, s["id"]))


def oylamaya_al(db, yonetici, sikayet_id):
    """Şikayet edilen mesaj için gizleme, konu için kaldırma oylaması açar. Süren oylama varsa ona bağlar."""
    s, grup = _gruptakiler(db, sikayet_id)
    konu, m = _hedef(db, s["tur"], s["hedef_id"])
    aciklama = "; ".join(sorted({x["aciklama"] for x in grup if x["aciklama"]}))[:300]
    if m:
        teklif_id = konular.gizleme_oylamasindaki_mesajlar(db, konu["id"]).get(m["id"])
        if not teklif_id:
            teklif_id = konular.mesaj_silme_teklifi(db, yonetici, [m["id"]], s["neden"],
                                                    f"Şikayet üzerine. {aciklama}".strip(), katilim_denetimi=False)
        ne = f"#{m['id']} numaralı mesaj"
    else:
        t = oylama.acik_teklif(db, "KONU_SILME", konu_id=konu["id"])
        teklif_id = t["id"] if t else konular.kaldirma_teklifi(
            db, yonetici, konu["id"], f"Şikayet üzerine ({s['neden']}). {aciklama}".strip(), katilim_denetimi=False)
        ne = f"“{konu['baslik']}” konusu"
    _kapat(db, yonetici, grup, "OYLAMADA", "Oylamaya alındı", teklif_id)
    gunluk.kaydet(db, yonetici["id"], "SIKAYET", f"{ne} hakkındaki {len(grup)} şikayet oylamaya alındı (#{teklif_id})")
    for sikayetci_id in {x["sikayetci_id"] for x in grup}:
        bildirimler.gonder(db, sikayetci_id, f"Şikayetin üzerine {ne} için oylama açıldı.", f"/oylama/{teklif_id}")
    return teklif_id


def yersiz_bul(db, yonetici, sikayet_id, not_metni):
    s, grup = _gruptakiler(db, sikayet_id)
    not_metni = (not_metni or "").strip()
    if len(not_metni) < 5:
        raise KuralHatasi("Şikayet edene gösterilecek kısa bir not yaz (en az 5 karakter).")
    _kapat(db, yonetici, grup, "YERSIZ", not_metni[:300])
    ne = f"#{s['hedef_id']} numaralı mesaj" if s["tur"] == "MESAJ" else f"#{s['hedef_id']} numaralı konu"
    gunluk.kaydet(db, yonetici["id"], "SIKAYET", f"{ne} hakkındaki {len(grup)} şikayet yersiz bulundu")
    baglanti = f"/konu/{s['konu_id']}" + (f"#m{s['hedef_id']}" if s["tur"] == "MESAJ" else "")
    for sikayetci_id in {x["sikayetci_id"] for x in grup}:
        bildirimler.gonder(db, sikayetci_id, f"Şikayetin incelendi ve yersiz bulundu: {not_metni[:120]}", baglanti)


def kullanicinin_sikayetleri(db, kullanici_id, limit=20):
    return db.execute("SELECT s.*, k.baslik FROM sikayetler s JOIN konular k ON k.id = s.konu_id "
                      "WHERE s.sikayetci_id = ? ORDER BY s.id DESC LIMIT ?", (kullanici_id, limit)).fetchall()
