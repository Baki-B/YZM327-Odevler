"""Konular, fikirler ve mesajlar.

Bir konunun yolculuğu:
  TARTISMA (24 saat) ──► OYLAMA: 1. tur (48 saat) ──► 2. … 5. tur (24'er saat) ──► KARARA_BAGLANDI
                              └── yeter sayı yok / hiçbir fikir eşiği geçemedi / eşitlik ──► SONUCSUZ
  * Konuyu her üye açar; onay beklemez. Yönetmelik denetimi (hakaret, kişisel veri...) açılırken çalışır.
  * Her katılımcı bir konuda en fazla BİR fikir yazar; fikirler tartışma boyunca ve 1. tur bitene kadar yazılabilir.
  * Oylama sürerken tartışma devam eder. Eleme kuralları sonuclar.py içindedir.
Mesajlar silinmez; düzenlenince eski hâli saklanır; gizleme oylamaya tabidir.
"""
import json
from datetime import timedelta

from . import (arama, ayarlar, bildirimler, defter, gunluk, oylama, ontoloji, uygunluk, yonetmelik, zaman)
from .hatalar import KuralHatasi, tamsayi

MAX_TOPLU_GIZLEME = 20
FIKIR_UZUNLUGU = (10, 600)


def konu_getir(db, konu_id):
    k = db.execute("SELECT * FROM konular WHERE id = ?", (konu_id,)).fetchone()
    if not k:
        raise KuralHatasi("Konu bulunamadı.")
    return k


def mesaj_getir(db, mesaj_id):
    m = db.execute("SELECT * FROM mesajlar WHERE id = ?", (mesaj_id,)).fetchone()
    if not m:
        raise KuralHatasi("Mesaj bulunamadı.")
    return m


def _katilimci_olmali(db, kullanici, konu):
    u = uygunluk.uygunluk(db, kullanici, konu)
    if not u.katilimci:
        raise KuralHatasi("Bu konuda gözlemcisin: " + "; ".join(m for g, m in u.satirlar if not g))


def _canli_olmali(konu):
    if konu["silindi"]:
        raise KuralHatasi("Bu konu kaldırıldı.")


def _aktif_olmali(konu):
    _canli_olmali(konu)
    if konu["durum"] not in ayarlar.AKTIF_DURUMLAR:
        raise KuralHatasi("Bu konu kapandı; artık yazılamaz. Karara katılmıyorsan itiraz konusu açabilirsin.")


def durum_degistir(db, konu_id, durum):
    db.execute("UPDATE konular SET durum = ? WHERE id = ?", (durum, konu_id))
    gunluk.kaydet(db, None, "KONU_DURUM", f"#{konu_id} durumu: {ayarlar.KONU_DURUMLARI[durum]}")
    defter.ekle(db, "KONU_DURUM", {"konu": konu_id, "durum": durum})


def _kisalt(metin, n):
    metin = " ".join(metin.split())
    return metin if len(metin) <= n else metin[: n - 1] + "…"


# --- Konu açma ve düzenleme ---

def _alanlari_dogrula(db, form, ust=None):
    baslik, aciklama = (form.get("baslik") or "").strip(), (form.get("aciklama") or "").strip()
    if not 5 <= len(baslik) <= 150:
        raise KuralHatasi("Başlık 5–150 karakter olmalı.")
    if not 10 <= len(aciklama) <= 5000:
        raise KuralHatasi("Açıklama 10–5000 karakter olmalı.")
    kategori_id, konum_id = tamsayi(form.get("kategori_id")), tamsayi(form.get("konum_id"))
    min_yas, max_yas = tamsayi(form.get("min_yas")), tamsayi(form.get("max_yas"))
    if not kategori_id or not ontoloji.dugum(db, "kategoriler", kategori_id):
        raise KuralHatasi("Geçerli bir kategori seç.")
    if konum_id and not ontoloji.dugum(db, "konumlar", konum_id):
        raise KuralHatasi("Geçersiz konum.")
    for y in (min_yas, max_yas):
        if y is not None and not 0 <= y <= 120:
            raise KuralHatasi("Yaş sınırı 0–120 arasında olmalı.")
    if min_yas is not None and max_yas is not None and min_yas > max_yas:
        raise KuralHatasi("En küçük yaş, en büyük yaştan büyük olamaz.")
    if ust is not None:
        ust_konum, ust_min, ust_max = uygunluk.etkin_kurallar(db, ust)
        if ust_konum and konum_id and not ontoloji.altinda_mi(db, "konumlar", konum_id, ust_konum):
            raise KuralHatasi("Alt konunun konumu, üst konunun konumu ("
                              f"{ontoloji.yol_metni(db, 'konumlar', ust_konum)}) içinde olmalı.")
        if ust_min is not None and min_yas is not None and min_yas < ust_min:
            raise KuralHatasi(f"Üst konu {ust_min}+ yaş için; alt konu bunu genişletemez.")
        if ust_max is not None and max_yas is not None and max_yas > ust_max:
            raise KuralHatasi(f"Üst konu en fazla {ust_max} yaş için; alt konu bunu genişletemez.")
    return dict(baslik=baslik, aciklama=aciklama, kategori_id=kategori_id, konum_id=konum_id, min_yas=min_yas,
                max_yas=max_yas)


def _sahibin_uygunlugu(db, sahip, alanlar, ust_id):
    u = uygunluk.uygunluk(db, sahip, dict(alanlar, id=None, ust_id=ust_id))
    if not u.katilimci:
        raise KuralHatasi("Kendi katılamayacağın bir konu açamazsın: " + "; ".join(m for g, m in u.satirlar if not g))


def denetim_onizleme(db, form, ust_id=None):
    """Konuyu göndermeden önce yönetmelik denetimini çalıştırır (formdaki "Denetle" düğmesi)."""
    ust_id = tamsayi(ust_id, "Geçersiz üst konu.")
    ust = konu_getir(db, ust_id) if ust_id else None
    alanlar = _alanlari_dogrula(db, form, ust)
    return yonetmelik.denetle(db, alanlar["baslik"], alanlar["aciklama"], alanlar["kategori_id"],
                              alanlar["konum_id"], ust)


def _denetle(db, alanlar, ust, haric_konu_id=None):
    rapor = yonetmelik.denetle(db, alanlar["baslik"], alanlar["aciklama"], alanlar["kategori_id"],
                               alanlar["konum_id"], ust, haric_konu_id=haric_konu_id)
    if rapor["engel"]:
        raise KuralHatasi("Yönetmelik denetimi engelledi: " +
                          " ".join(f"[{b['kod']}] {b['mesaj']}" for b in rapor["engel"]))
    return rapor


def konu_ac(db, sahip, form, ust_id=None, itiraz_id=None):
    """Konu hemen tartışmaya açılır. ust_id: alt konu. itiraz_id: karara bağlanmış bir konunun sonucuna itiraz."""
    if sahip["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları konu açamaz.")
    ust_id, itiraz_id = tamsayi(ust_id, "Geçersiz üst konu."), tamsayi(itiraz_id, "Geçersiz itiraz konusu.")
    ust = None
    if ust_id:
        ust = konu_getir(db, ust_id)
        _aktif_olmali(ust)
        _katilimci_olmali(db, sahip, ust)
    if itiraz_id:
        eski = konu_getir(db, itiraz_id)
        if eski["silindi"] or eski["durum"] not in ("KARARA_BAGLANDI", "SONUCSUZ"):
            raise KuralHatasi("İtiraz konusu yalnızca kapanmış bir konu için açılabilir.")
    alanlar = _alanlari_dogrula(db, form, ust)
    _sahibin_uygunlugu(db, sahip, alanlar, ust_id)
    rapor = _denetle(db, alanlar, ust)
    simdi = zaman.simdi()
    bitis = simdi + timedelta(hours=yonetmelik.deger(db, "SURE_TARTISMA_SAAT"))
    konu_id = db.execute(
        """INSERT INTO konular (ust_id, itiraz_id, sahip_id, kategori_id, baslik, aciklama, konum_id, min_yas, max_yas,
                                bilirkisi_agirlik, yz_agirlik, durum, tur, denetim, tartisma_bitis, olusturma)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'TARTISMA', 0, ?, ?, ?)""",
        (ust_id, itiraz_id, sahip["id"], alanlar["kategori_id"], alanlar["baslik"], alanlar["aciklama"],
         alanlar["konum_id"], alanlar["min_yas"], alanlar["max_yas"], yonetmelik.deger(db, "UZMAN_AGIRLIK"),
         json.dumps(rapor, ensure_ascii=False), zaman.metin(bitis), zaman.metin(simdi)),
    ).lastrowid
    arama.indeksle(db, "KONU", konu_id, konu_id, f"{alanlar['baslik']} {alanlar['aciklama']}")
    gunluk.kaydet(db, sahip["id"], "KONU", f"#{konu_id} “{alanlar['baslik']}” konusunu açtı"
                  + (f" (#{ust_id} altında)" if ust_id else "") + (f" (#{itiraz_id} kararına itiraz)" if itiraz_id else ""))
    defter.ekle(db, "KONU", {"konu": konu_id, "ust": ust_id, "itiraz": itiraz_id, "sahip": sahip["takma_ad"],
                             "ozet": defter.ozet(alanlar["baslik"] + alanlar["aciklama"])})
    saat = yonetmelik.deger(db, "SURE_TARTISMA_SAAT")
    sistem_mesaji(db, konu_id, f"Konu tartışmaya açıldı. {saat} saat sonra fikir oylaması başlar. Her katılımcı bir fikir yazabilir.")
    baglanti = f"/konu/{konu_id}"
    bildirimler.coklu_gonder(db, bildirimler.takipciler(db, sahip["id"]),
                             f"@{sahip['takma_ad']} yeni bir konu açtı: {alanlar['baslik']}", baglanti)
    if ust_id:
        bildirimler.coklu_gonder(db, bildirimler.konu_katilimcilari(db, ust_id),
                                 f"Katıldığın konuya alt konu açıldı: {alanlar['baslik']}", baglanti, haric=sahip["id"])
    if itiraz_id:
        sistem_mesaji(db, konu_id, f"Bu konu, #{itiraz_id} numaralı konunun sonucuna itiraz olarak açıldı.")
        bildirimler.coklu_gonder(db, bildirimler.konu_katilimcilari(db, itiraz_id),
                                 f"Katıldığın konunun sonucuna itiraz konusu açıldı: {alanlar['baslik']}", baglanti,
                                 haric=sahip["id"])
    return konu_id


def _surum_kaydet(db, konu, neden):
    db.execute("""INSERT INTO konu_surumleri (konu_id, baslik, aciklama, bilirkisi_agirlik, yz_agirlik, tarih, neden)
                  VALUES (?, ?, ?, ?, 0, ?, ?)""",
               (konu["id"], konu["baslik"], konu["aciklama"], konu["bilirkisi_agirlik"], zaman.simdi_metin(), neden))


def konu_duzenle(db, kullanici, konu_id, form):
    """Konuyu açan kişi tartışma aşamasında başlığı ve açıklamayı düzenleyebilir; eski hâli saklanır."""
    konu = konu_getir(db, konu_id)
    _canli_olmali(konu)
    if konu["durum"] != "TARTISMA" or konu["sahip_id"] != kullanici["id"]:
        raise KuralHatasi("Konuyu yalnızca açan kişi ve yalnızca oylama başlamadan önce düzenleyebilir.")
    ust = konu_getir(db, konu["ust_id"]) if konu["ust_id"] else None
    alanlar = _alanlari_dogrula(db, dict(form, kategori_id=konu["kategori_id"], konum_id=konu["konum_id"],
                                         min_yas=konu["min_yas"], max_yas=konu["max_yas"]), ust)
    if alanlar["baslik"] == konu["baslik"] and alanlar["aciklama"] == konu["aciklama"]:
        raise KuralHatasi("Hiçbir değişiklik yapmadın.")
    rapor = _denetle(db, alanlar, ust, haric_konu_id=konu_id)
    _surum_kaydet(db, konu, "Konuyu açan kişi düzenledi")
    db.execute("UPDATE konular SET baslik = ?, aciklama = ?, denetim = ?, duzenleme = ? WHERE id = ?",
               (alanlar["baslik"], alanlar["aciklama"], json.dumps(rapor, ensure_ascii=False), zaman.simdi_metin(),
                konu_id))
    arama.indeksle(db, "KONU", konu_id, konu_id, f"{alanlar['baslik']} {alanlar['aciklama']}")
    defter.ekle(db, "KONU_DUZENLEME", {"konu": konu_id, "ozet": defter.ozet(alanlar["baslik"] + alanlar["aciklama"])})
    gunluk.kaydet(db, kullanici["id"], "KONU_DUZENLEME", f"#{konu_id} konusunu düzenledi")


def konu_surumleri(db, konu_id):
    return db.execute("SELECT * FROM konu_surumleri WHERE konu_id = ? ORDER BY id", (konu_id,)).fetchall()


# --- Fikirler ---

def fikirler(db, konu_id):
    return db.execute("""SELECT m.*, k.takma_ad FROM mesajlar m JOIN kullanicilar k ON k.id = m.yazar_id
                         WHERE m.konu_id = ? AND m.tip = 'FIKIR' AND m.gizli = 0 ORDER BY m.id""", (konu_id,)).fetchall()


def fikir_yazilabilir_mi(konu):
    """Fikirler tartışma boyunca ve 1. tur bitene kadar yazılabilir."""
    return not konu["silindi"] and (konu["durum"] == "TARTISMA" or (konu["durum"] == "OYLAMA" and konu["tur"] == 1))


def kullanicinin_fikri(db, konu_id, kullanici_id):
    return db.execute("SELECT * FROM mesajlar WHERE konu_id = ? AND yazar_id = ? AND tip = 'FIKIR'",
                      (konu_id, kullanici_id)).fetchone()


def fikir_yaz(db, kullanici, konu_id, icerik):
    konu = konu_getir(db, konu_id)
    _aktif_olmali(konu)
    _katilimci_olmali(db, kullanici, konu)
    if not fikir_yazilabilir_mi(konu):
        raise KuralHatasi("1. tur bittiği için artık yeni fikir yazılamaz.")
    if kullanicinin_fikri(db, konu_id, kullanici["id"]):
        raise KuralHatasi("Bu konuda zaten bir fikrin var. Her katılımcı bir fikir yazabilir; istersen fikrini düzenleyebilirsin.")
    icerik = (icerik or "").strip()
    if not FIKIR_UZUNLUGU[0] <= len(icerik) <= FIKIR_UZUNLUGU[1]:
        raise KuralHatasi(f"Fikir {FIKIR_UZUNLUGU[0]}–{FIKIR_UZUNLUGU[1]} karakter olmalı.")
    yonetmelik.mesaj_denetle(db, icerik)
    mesaj_id = _mesaj_ekle(db, konu_id, kullanici, "FIKIR", icerik)
    gunluk.kaydet(db, kullanici["id"], "MESAJ", f"#{konu_id} konusuna fikir yazdı")
    tur = oylama.acik_teklif(db, "KARAR", konu_id=konu_id)
    if tur:                                 # 1. tur sürüyorsa fikir oylamaya da eklenir
        oylama.secenek_ekle(db, tur["id"], _kisalt(icerik, 200), mesaj_id)
    if konu["sahip_id"] != kullanici["id"]:
        bildirimler.gonder(db, konu["sahip_id"], f"Konuna yeni bir fikir yazıldı: {konu['baslik']}",
                           f"/konu/{konu_id}#m{mesaj_id}")
    return mesaj_id


# --- Oylama turları ---

def oylamayi_baslat(db, konu_id):
    """Tartışma süresi dolunca 1. turu açar. Döner: oylamanın id'si ya da None (zaten başlamışsa)."""
    # Atomik geçiş: arka plan zamanlayıcısı ile bir web isteği aynı anda çalışsa da tek oylama açılır.
    if db.execute("UPDATE konular SET durum = 'OYLAMA', tur = 1 WHERE id = ? AND durum = 'TARTISMA' AND silindi = 0",
                  (konu_id,)).rowcount == 0:
        return None
    defter.ekle(db, "KONU_DURUM", {"konu": konu_id, "durum": "OYLAMA", "tur": 1})
    liste = fikirler(db, konu_id)
    teklif_id = oylama.teklif_ac(db, "KARAR", None, konu_id=konu_id, tur_no=1,
                                 secenekler=[(_kisalt(m["icerik"], 200), m["id"]) for m in liste])
    saat = yonetmelik.deger(db, "SURE_TUR1_SAAT")
    sistem_mesaji(db, konu_id, f"Fikir oylaması başladı (1. tur, {saat} saat). Şu an {len(liste)} fikir var; tur bitene "
                               "kadar yeni fikir yazılabilir. Tartışma devam ediyor.")
    from . import yz
    yz.tartisma_ozeti(db, konu_id)
    return teklif_id


def sonraki_tur(db, konu_id, tur_no, kalanlar):
    """kalanlar: [(metin, mesaj_id), ...] — bir sonraki tura kalan fikirler."""
    db.execute("UPDATE konular SET tur = ? WHERE id = ?", (tur_no, konu_id))
    defter.ekle(db, "KONU_DURUM", {"konu": konu_id, "durum": "OYLAMA", "tur": tur_no})
    return oylama.teklif_ac(db, "KARAR", None, konu_id=konu_id, tur_no=tur_no, secenekler=kalanlar)


def kapat(db, konu_id, durum):
    durum_degistir(db, konu_id, durum)
    db.execute("UPDATE konular SET kabul_tarihi = ? WHERE id = ?", (zaman.simdi_metin(), konu_id))


def itirazlar(db, konu_id):
    return db.execute("SELECT id, baslik, durum FROM konular WHERE itiraz_id = ? AND silindi = 0 ORDER BY id",
                      (konu_id,)).fetchall()


# --- Konu kaldırma ---

def kaldirma_teklifi(db, kullanici, konu_id, gerekce, katilim_denetimi=True):
    """katilim_denetimi=False: yönetici bir şikayeti oylamaya alırken gözlemci olduğu konuda da oylama açabilir."""
    konu = konu_getir(db, konu_id)
    _canli_olmali(konu)
    if katilim_denetimi:
        _katilimci_olmali(db, kullanici, konu)
    gerekce = (gerekce or "").strip()
    if len(gerekce) < 10:
        raise KuralHatasi("Konunun neden kaldırılması gerektiğini en az 10 karakterle yaz.")
    yonetmelik.mesaj_denetle(db, gerekce)
    if oylama.acik_teklif(db, "KONU_SILME", konu_id=konu_id):
        raise KuralHatasi("Bu konu için zaten süren bir kaldırma oylaması var.")
    return oylama.teklif_ac(db, "KONU_SILME", kullanici["id"], konu_id=konu_id, gerekce=gerekce)


def alt_agac(db, konu_id):
    idler, bekleyen = [], [konu_id]
    while bekleyen:
        x = bekleyen.pop()
        idler.append(x)
        bekleyen.extend(r["id"] for r in db.execute("SELECT id FROM konular WHERE ust_id = ?", (x,)))
    return idler


def konuyu_kaldir(db, konu_id, not_metni):
    for i in alt_agac(db, konu_id):
        db.execute("UPDATE konular SET silindi = 1, silinme_notu = ? WHERE id = ?", (not_metni, i))
        db.execute("UPDATE teklifler SET durum = 'IPTAL', kapanis = ? WHERE konu_id = ? AND durum = 'ACIK'",
                   (zaman.simdi_metin(), i))
        db.execute("DELETE FROM arama WHERE konu_id = ?", (i,))
    gunluk.kaydet(db, None, "KONU_KALDIRMA", f"#{konu_id} kaldırıldı: {not_metni}")
    defter.ekle(db, "KONU_DURUM", {"konu": konu_id, "durum": "KALDIRILDI"})


# --- Mesajlar ---

def _mesaj_ekle(db, konu_id, yazar, tip, icerik, ust_mesaj_id=None):
    mesaj_id = db.execute(
        "INSERT INTO mesajlar (konu_id, yazar_id, ust_mesaj_id, tip, icerik, olusturma) VALUES (?, ?, ?, ?, ?, ?)",
        (konu_id, yazar["id"] if yazar else None, ust_mesaj_id, tip, icerik, zaman.simdi_metin()),
    ).lastrowid
    defter.ekle(db, "MESAJ", {"mesaj": mesaj_id, "konu": konu_id, "yazar": yazar["takma_ad"] if yazar else "Sistem",
                              "ozet": defter.ozet(icerik)})
    if tip != "SISTEM":
        arama.indeksle(db, "MESAJ", mesaj_id, konu_id, icerik)
    return mesaj_id


def sistem_mesaji(db, konu_id, icerik):
    return _mesaj_ekle(db, konu_id, None, "SISTEM", icerik)


def yz_mesaji(db, konu_id, yz_hesabi, icerik, ust_mesaj_id=None):
    return _mesaj_ekle(db, konu_id, yz_hesabi, "YZ", icerik, ust_mesaj_id)


def mesaj_yaz(db, kullanici, konu_id, tip, icerik, ust_mesaj_id=None):
    konu = konu_getir(db, konu_id)
    _aktif_olmali(konu)
    _katilimci_olmali(db, kullanici, konu)
    if tip not in ayarlar.KULLANICI_MESAJ_TIPLERI:
        raise KuralHatasi("Geçersiz mesaj türü.")
    icerik = (icerik or "").strip()
    if not 2 <= len(icerik) <= 5000:
        raise KuralHatasi("Mesaj 2–5000 karakter olmalı.")
    yonetmelik.mesaj_denetle(db, icerik)
    ust_mesaj_id = tamsayi(ust_mesaj_id)
    ust = None
    if ust_mesaj_id:
        ust = mesaj_getir(db, ust_mesaj_id)
        if ust["konu_id"] != konu_id:
            raise KuralHatasi("Yanıtlanan mesaj bu konuya ait değil.")
    mesaj_id = _mesaj_ekle(db, konu_id, kullanici, tip, icerik, ust_mesaj_id)
    gunluk.kaydet(db, kullanici["id"], "MESAJ", f"#{konu_id} konusuna {ayarlar.MESAJ_TIPLERI[tip].lower()} yazdı")
    baglanti = f"/konu/{konu_id}#m{mesaj_id}"
    if ust and ust["yazar_id"] and ust["yazar_id"] != kullanici["id"]:
        bildirimler.gonder(db, ust["yazar_id"], f"@{kullanici['takma_ad']} mesajını yanıtladı "
                                                f"({ayarlar.MESAJ_TIPLERI[tip].lower()}): {konu['baslik']}", baglanti)
    if konu["sahip_id"] != kullanici["id"] and not (ust and ust["yazar_id"] == konu["sahip_id"]):
        bildirimler.gonder(db, konu["sahip_id"], f"Konuna yeni {ayarlar.MESAJ_TIPLERI[tip].lower()}: {konu['baslik']}",
                           baglanti)
    return mesaj_id


def mesaj_duzenle(db, kullanici, mesaj_id, icerik):
    """Yazan kişi mesajını düzenleyebilir; eski hâli mesaj geçmişinde herkese görünür."""
    m = mesaj_getir(db, mesaj_id)
    if m["yazar_id"] != kullanici["id"] or m["tip"] in ("SISTEM", "YZ"):
        raise KuralHatasi("Sadece kendi mesajını düzenleyebilirsin.")
    if m["gizli"]:
        raise KuralHatasi("Gizlenmiş bir mesaj düzenlenemez.")
    konu = konu_getir(db, m["konu_id"])
    _aktif_olmali(konu)
    if m["tip"] == "FIKIR" and konu["durum"] != "TARTISMA":
        raise KuralHatasi("Oylama başladıktan sonra fikir değiştirilemez; oylanan metin aynı kalmalı.")
    icerik = (icerik or "").strip()
    alt, ust = FIKIR_UZUNLUGU if m["tip"] == "FIKIR" else (2, 5000)
    if not alt <= len(icerik) <= ust:
        raise KuralHatasi(f"Metin {alt}–{ust} karakter olmalı.")
    if icerik == m["icerik"]:
        raise KuralHatasi("Hiçbir değişiklik yapmadın.")
    yonetmelik.mesaj_denetle(db, icerik)
    db.execute("INSERT INTO mesaj_surumleri (mesaj_id, icerik, tarih) VALUES (?, ?, ?)",
               (mesaj_id, m["icerik"], zaman.simdi_metin()))
    db.execute("UPDATE mesajlar SET icerik = ?, duzenleme = ? WHERE id = ?", (icerik, zaman.simdi_metin(), mesaj_id))
    arama.indeksle(db, "MESAJ", mesaj_id, m["konu_id"], icerik)
    defter.ekle(db, "MESAJ_DUZENLEME", {"mesaj": mesaj_id, "ozet": defter.ozet(icerik)})


def mesaj_surumleri(db, mesaj_id):
    return db.execute("SELECT * FROM mesaj_surumleri WHERE mesaj_id = ? ORDER BY id", (mesaj_id,)).fetchall()


# --- Mesaj gizleme (oylamayla) ---

def gizleme_oylamasindaki_mesajlar(db, konu_id=None):
    """{mesaj_id: teklif_id} — süren gizleme oylamalarındaki mesajlar (tek ya da toplu)."""
    sorgu = "SELECT id, hedef_id, veri FROM teklifler WHERE tip = 'MESAJ_SILME' AND durum = 'ACIK'"
    parametreler = []
    if konu_id is not None:
        sorgu += " AND konu_id = ?"
        parametreler.append(konu_id)
    sonuc = {}
    for t in db.execute(sorgu, parametreler):
        for mid in json.loads(t["veri"] or "{}").get("mesajlar", [t["hedef_id"]]):
            sonuc[mid] = t["id"]
    return sonuc


def mesaj_silme_teklifi(db, kullanici, mesaj_idleri, neden, aciklama, katilim_denetimi=True):
    """Bir ya da birden fazla mesajın ("tartışmanın bir kısmı") gizlenmesini oylamaya sunar."""
    if isinstance(mesaj_idleri, (int, str)):
        mesaj_idleri = [mesaj_idleri]
    idler = sorted({tamsayi(x, "Geçersiz mesaj numarası.") for x in mesaj_idleri if str(x).strip()})
    if not idler:
        raise KuralHatasi("Gizlenmesini istediğin en az bir mesajı seç.")
    if len(idler) > MAX_TOPLU_GIZLEME:
        raise KuralHatasi(f"Tek oylamada en fazla {MAX_TOPLU_GIZLEME} mesaj seçilebilir.")
    mesajlar = [mesaj_getir(db, i) for i in idler]
    konu_id = mesajlar[0]["konu_id"]
    if any(m["konu_id"] != konu_id for m in mesajlar):
        raise KuralHatasi("Seçilen mesajlar aynı konuya ait olmalı.")
    if any(m["tip"] == "SISTEM" for m in mesajlar):
        raise KuralHatasi("Sistem mesajları gizlenemez.")
    if any(m["gizli"] for m in mesajlar):
        raise KuralHatasi("Seçilen mesajlardan biri zaten gizlenmiş.")
    konu = konu_getir(db, konu_id)
    _canli_olmali(konu)
    if katilim_denetimi:
        _katilimci_olmali(db, kullanici, konu)
    if neden not in ayarlar.SILME_NEDENLERI:
        raise KuralHatasi("Bir neden seç.")
    suren = gizleme_oylamasindaki_mesajlar(db, konu_id)
    if any(i in suren for i in idler):
        raise KuralHatasi("Seçilen mesajlardan biri için zaten süren bir gizleme oylaması var.")
    gerekce = neden + (f": {aciklama.strip()}" if (aciklama or "").strip() else "")
    yonetmelik.mesaj_denetle(db, gerekce)
    teklif_id = oylama.teklif_ac(db, "MESAJ_SILME", kullanici["id"], konu_id=konu_id, hedef_id=idler[0],
                                 gerekce=gerekce, veri={"neden": neden, "mesajlar": idler})
    for yazar_id in {m["yazar_id"] for m in mesajlar} - {kullanici["id"]}:
        bildirimler.gonder(db, yazar_id, "Mesajın için gizleme oylaması açıldı.", f"/oylama/{teklif_id}")
    return teklif_id


def mesaji_gizle(db, mesaj_id, not_metni, teklif_id):
    db.execute("UPDATE mesajlar SET gizli = 1, gizlenme_notu = ? WHERE id = ?", (not_metni, mesaj_id))
    arama.kaldir(db, "MESAJ", mesaj_id)
    defter.ekle(db, "GIZLEME", {"mesaj": mesaj_id, "teklif": teklif_id})


# --- Okuma ---

def mesaj_agaci(db, konu_id):
    """Mesajları yanıt ağacı olarak döndürür. Fikirler ayrı listelenir; buradaki ağaçta da kök olarak yer alırlar."""
    satirlar = db.execute(
        """SELECT m.*, k.takma_ad, k.yz_mi,
                  (SELECT COUNT(*) FROM mesaj_surumleri s WHERE s.mesaj_id = m.id) AS surum_sayisi
           FROM mesajlar m LEFT JOIN kullanicilar k ON k.id = m.yazar_id
           WHERE m.konu_id = ? ORDER BY m.id""", (konu_id,)).fetchall()
    suren = gizleme_oylamasindaki_mesajlar(db, konu_id)
    dugumler = {r["id"]: dict(r, cocuklar=[], silme_teklifi=suren.get(r["id"])) for r in satirlar}
    kokler = []
    for d in dugumler.values():
        (dugumler[d["ust_mesaj_id"]]["cocuklar"] if d["ust_mesaj_id"] in dugumler else kokler).append(d)
    return kokler


def konu_listesi(db, ust_id=None, durumlar=None):
    sorgu = """SELECT k.*, u.takma_ad AS sahip_ad,
                  (SELECT COUNT(*) FROM mesajlar m WHERE m.konu_id = k.id AND m.yazar_id IS NOT NULL
                     AND m.tip != 'YZ') AS mesaj_sayisi,
                  (SELECT COUNT(*) FROM mesajlar m WHERE m.konu_id = k.id AND m.tip = 'FIKIR' AND m.gizli = 0) AS fikir_sayisi,
                  (SELECT COUNT(*) FROM konular a WHERE a.ust_id = k.id AND a.silindi = 0) AS alt_sayisi,
                  (SELECT COUNT(*) FROM teklifler t WHERE t.konu_id = k.id AND t.durum = 'ACIK') AS acik_oylama,
                  COALESCE((SELECT MAX(m.olusturma) FROM mesajlar m WHERE m.konu_id = k.id), k.olusturma) AS son_etkinlik
               FROM konular k JOIN kullanicilar u ON u.id = k.sahip_id WHERE k.silindi = 0 """
    parametreler = []
    if ust_id is None:
        sorgu += "AND k.ust_id IS NULL "
    else:
        sorgu += "AND k.ust_id = ? "
        parametreler.append(ust_id)
    if durumlar:
        sorgu += f"AND k.durum IN ({','.join('?' * len(durumlar))}) "
        parametreler += list(durumlar)
    return db.execute(sorgu + "ORDER BY k.id DESC", parametreler).fetchall()


def kategori_ozeti(db):
    """Konu listesindeki kategori çipleri için: ana kategoriler, renkleri ve içlerindeki konu sayısı."""
    sayilar = {}
    for r in db.execute("SELECT kategori_id, COUNT(*) AS n FROM konular WHERE silindi = 0 GROUP BY kategori_id"):
        kok = ontoloji.atalar(db, "kategoriler", r["kategori_id"])[0]
        sayilar[kok] = sayilar.get(kok, 0) + r["n"]
    koklar = sorted(db.execute("SELECT id, ad FROM kategoriler WHERE ust_id IS NULL").fetchall(),
                    key=lambda d: (d["ad"] == ayarlar.GENEL_KATEGORI, ontoloji.tr_sirala(d["ad"])))
    return [{"id": d["id"], "ad": d["ad"], "renk": ontoloji.kategori_rengi(db, d["id"]), "sayi": sayilar.get(d["id"], 0)}
            for d in koklar]


def istatistikler(db):
    tek = lambda q, *p: db.execute(q, p).fetchone()[0]  # noqa: E731
    return {
        "uye": tek("SELECT COUNT(*) FROM kullanicilar WHERE yz_mi = 0"),
        "konu": tek("SELECT COUNT(*) FROM konular WHERE silindi = 0 AND durum IN ('TARTISMA', 'OYLAMA')"),
        "oylama": tek("SELECT COUNT(*) FROM teklifler WHERE durum = 'ACIK'"),
        "karar": tek("SELECT COUNT(*) FROM kararlar WHERE durum = 'KESIN'"),
        "mesaj": tek("SELECT COUNT(*) FROM mesajlar WHERE yazar_id IS NOT NULL"),
    }
