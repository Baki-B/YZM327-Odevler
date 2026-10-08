"""Uzmanlık: bir alanda oyu ağır sayılan üyeler.

Uzman olmanın üç adımı vardır:
  1. ÖN ŞART: aday o alanda yeterince yazmış olmalı (en az UZMAN_MIN_MESAJ mesaj, en az UZMAN_MIN_KONU farklı konu).
  2. KONTENJAN: bir ana kategoride en fazla UZMAN_KONTENJAN uzman olabilir; yer yoksa başvuru açılamaz.
     Böylece küçük bir grup birbirini sırayla uzman yapamaz.
  3. OYLAMA: başvuruyu o alanın "niş kitlesi" (o ana kategorideki konulara yazmış üyeler) oylar.
     Herkesin oyu 1 sayılır, aday oy kullanamaz; kabul için ESIK_UZMANLIK gerekir.
Yönetici uzman atayamaz. Yapay zeka hesapları da aynı şartlarla, bir üyenin aday göstermesiyle uzman olabilir.
"""
from datetime import timedelta

from . import bildirimler, defter, denetim, gunluk, ontoloji, oylama, uygunluk, yonetmelik, zaman
from .hatalar import KuralHatasi


def uzmanliklar(db, kullanici_id, sadece_aktif=True):
    sorgu, parametreler = "SELECT * FROM uzmanliklar WHERE kullanici_id = ?", [kullanici_id]
    if sadece_aktif:
        sorgu += " AND baslangic <= ? AND bitis > ?"
        parametreler += [zaman.simdi_metin()] * 2
    return db.execute(sorgu + " ORDER BY id", parametreler).fetchall()


def _kok(db, kategori_id):
    return ontoloji.atalar(db, "kategoriler", kategori_id)[0]


def alan_uzmanlari(db, kategori_id):
    """Bir ana kategorideki (alt kategorileriyle) aktif uzmanların id'leri."""
    alan = set(ontoloji.alt_agac(db, "kategoriler", _kok(db, kategori_id)))
    simdi = zaman.simdi_metin()
    return {r["kullanici_id"] for r in db.execute(
        "SELECT kullanici_id, kategori_id FROM uzmanliklar WHERE baslangic <= ? AND bitis > ?", (simdi, simdi))
        if r["kategori_id"] in alan}


def kontenjan(db, kategori_id):
    dolu, toplam = len(alan_uzmanlari(db, kategori_id)), yonetmelik.deger(db, "UZMAN_KONTENJAN")
    return {"dolu": dolu, "toplam": toplam, "yer_var": dolu < toplam,
            "alan": ontoloji.ad(db, "kategoriler", _kok(db, kategori_id))}


def on_sartlar(db, kullanici_id, kategori_id):
    """Adayın o alandaki (seçilen kategori ve alt kategorileri) etkinliği ön şartları sağlıyor mu?"""
    alan = set(ontoloji.alt_agac(db, "kategoriler", kategori_id))
    mesaj, konular_ = 0, set()
    for r in db.execute("""SELECT m.konu_id, k.kategori_id FROM mesajlar m JOIN konular k ON k.id = m.konu_id
                           WHERE m.yazar_id = ? AND m.gizli = 0 AND k.silindi = 0""", (kullanici_id,)):
        if r["kategori_id"] in alan:
            mesaj += 1
            konular_.add(r["konu_id"])
    gereken_mesaj, gereken_konu = yonetmelik.deger(db, "UZMAN_MIN_MESAJ"), yonetmelik.deger(db, "UZMAN_MIN_KONU")
    return {"mesaj": mesaj, "konu": len(konular_), "gereken_mesaj": gereken_mesaj, "gereken_konu": gereken_konu,
            "tamam": mesaj >= gereken_mesaj and len(konular_) >= gereken_konu}


def basvur(db, basvuran, kategori_id, gerekce, aday_id=None):
    """Üye kendisi için başvurur; aday_id verilirse bir yapay zeka hesabını aday gösterir."""
    if basvuran["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları başvuru açamaz; bir üye aday gösterebilir.")
    aday = basvuran
    if aday_id and aday_id != basvuran["id"]:
        aday = db.execute("SELECT * FROM kullanicilar WHERE id = ?", (aday_id,)).fetchone()
        if not aday or not aday["yz_mi"]:
            raise KuralHatasi("Yalnızca yapay zeka hesapları aday gösterilebilir; üyeler kendileri başvurur.")
    try:
        kategori_id = int(kategori_id)
    except (TypeError, ValueError):
        raise KuralHatasi("Alan seç.")
    if not ontoloji.dugum(db, "kategoriler", kategori_id):
        raise KuralHatasi("Alan bulunamadı.")
    if uygunluk.aktif_uzmanlik(db, aday["id"], kategori_id):
        raise KuralHatasi("Bu alanda zaten uzmanlık var.")
    if oylama.acik_teklif(db, "UZMANLIK", hedef_id=aday["id"]):
        raise KuralHatasi("Zaten süren bir uzmanlık oylaması var.")
    sart = on_sartlar(db, aday["id"], kategori_id)
    if not sart["tamam"]:
        raise KuralHatasi(f"Ön şartlar sağlanmıyor: bu alanda en az {sart['gereken_mesaj']} mesaj ve "
                          f"{sart['gereken_konu']} farklı konu gerekir (şu an {sart['mesaj']} mesaj, {sart['konu']} konu).")
    yer = kontenjan(db, kategori_id)
    if not yer["yer_var"]:
        raise KuralHatasi(f"{yer['alan']} alanında uzman kontenjanı dolu ({yer['dolu']}/{yer['toplam']}). "
                          "Bir uzmanlığın süresi dolunca yer açılır.")
    gerekce = (gerekce or "").strip()
    if len(gerekce) < 20:
        raise KuralHatasi("Gerekçeye eğitimi, deneyimi ya da alandaki katkıyı yaz (en az 20 karakter).")
    denetim.mesaj_denetle(db, gerekce)
    return oylama.teklif_ac(db, "UZMANLIK", basvuran["id"], hedef_id=aday["id"], gerekce=gerekce,
                            veri={"kategori_id": kategori_id})


def uzmanlik_ver(db, kullanici_id, kategori_id):
    """Oylama kabul edince çağrılır. Kontenjan o arada dolduysa uzmanlık verilmez."""
    k = db.execute("SELECT * FROM kullanicilar WHERE id = ?", (kullanici_id,)).fetchone()
    alan = ontoloji.yol_metni(db, "kategoriler", kategori_id)
    if not k or uygunluk.aktif_uzmanlik(db, kullanici_id, kategori_id):
        return False
    if not kontenjan(db, kategori_id)["yer_var"]:
        bildirimler.gonder(db, kullanici_id, f"Başvurun kabul edildi ama {alan} alanında kontenjan doldu; "
                                             "uzmanlık verilemedi.", "/profil/uzmanlik")
        return False
    gun = yonetmelik.deger(db, "UZMAN_SURE_GUN")
    an = zaman.simdi()
    db.execute("INSERT INTO uzmanliklar (kullanici_id, kategori_id, baslangic, bitis, kaynak) VALUES (?, ?, ?, ?, 'TOPLULUK')",
               (kullanici_id, kategori_id, zaman.metin(an), zaman.metin(an + timedelta(days=gun))))
    gunluk.kaydet(db, kullanici_id, "UZMANLIK", f"@{k['takma_ad']} {alan} alanında uzman oldu ({gun} gün)")
    defter.ekle(db, "UZMANLIK", {"yurttas": k["takma_ad"], "alan": alan, "gun": gun})
    bildirimler.gonder(db, kullanici_id, f"{alan} alanında uzman oldun. Bu alandaki fikir oylamalarında oyun ağır "
                                         "sayılır ve gerekçe yazman gerekir.", f"/kullanici/{k['takma_ad']}")
    return True
