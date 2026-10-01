"""Oy devri (likit demokrasi).

Kurallar:
  * Kapsam: tüm forum (GENEL), bir kategori (KATEGORI) ya da tek konu (KONU).
    Bir oylamada en özel kapsam geçerlidir: KONU > KATEGORI > GENEL.
  * Zincirleme: A → B → C. Döngüler engellenir.
  * Doğrudan oy devri ezer: devretmiş olsan da kendin oy verirsen senin oyun sayılır.
  * Devralan kişinin o oylamada oy hakkı yoksa devir o oylamada geçmez.
  * Sadece temel oy (1) devredilir; uzmanlık ağırlığı kişiye özeldir.
  * Bir kişi en fazla MAX_DEVIR (yönetmelik parametresi) devredilmiş oy taşıyabilir.
  * Yapay zeka hesapları oy kullanmadığı için onlara oy devredilemez.
"""
from collections import defaultdict

from . import bildirimler, defter, gunluk, ontoloji, uygunluk, yonetmelik, zaman
from .hatalar import KuralHatasi

KAPSAMLAR = {"GENEL": "Tüm forum", "KATEGORI": "Kategori", "KONU": "Konu"}

DUSME_NEDENLERI = {
    "DONGU": "devir zinciri döngüye giriyor",
    "HAK_YOK": "devralan kişinin bu oylamada oy hakkı yok",
    "TAVAN": "devralan kişi devir tavanına ulaştı",
}


def devir_ekle(db, veren, alan_takma_ad, kapsam, kapsam_id=0):
    if kapsam not in KAPSAMLAR:
        raise KuralHatasi("Geçersiz devir kapsamı.")
    if veren["yz_mi"]:
        raise KuralHatasi("YZ hesapları oy devredemez.")
    if kapsam == "GENEL":
        kapsam_id = 0
    elif kapsam == "KATEGORI":
        if not ontoloji.dugum(db, "kategoriler", kapsam_id):
            raise KuralHatasi("Kategori bulunamadı.")
    else:
        if not db.execute("SELECT 1 FROM konular WHERE id = ? AND silindi = 0", (kapsam_id,)).fetchone():
            raise KuralHatasi("Konu bulunamadı.")

    alan = db.execute("SELECT * FROM kullanicilar WHERE takma_ad = ?", (alan_takma_ad.strip(),)).fetchone()
    if not alan:
        raise KuralHatasi(f"“{alan_takma_ad}” adında bir kullanıcı yok.")
    if alan["id"] == veren["id"]:
        raise KuralHatasi("Oyunu kendine devredemezsin.")
    if alan["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları oy kullanmaz; onlara oy devredilemez.")

    # Aynı kapsamda zinciri izle: veren'e geri dönüyorsa döngü var.
    x, gorulen = alan["id"], set()
    while x and x not in gorulen:
        if x == veren["id"]:
            raise KuralHatasi(f"Bu devir bir döngü oluşturur (@{alan['takma_ad']} zaten sana zincirle bağlı).")
        gorulen.add(x)
        r = db.execute("SELECT alan_id FROM devirler WHERE veren_id = ? AND kapsam = ? AND kapsam_id = ?",
                       (x, kapsam, kapsam_id)).fetchone()
        x = r["alan_id"] if r else None

    db.execute(
        """INSERT INTO devirler (veren_id, alan_id, kapsam, kapsam_id, olusturma) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT (veren_id, kapsam, kapsam_id)
           DO UPDATE SET alan_id = excluded.alan_id, olusturma = excluded.olusturma""",
        (veren["id"], alan["id"], kapsam, kapsam_id, zaman.simdi_metin()),
    )
    kapsam_yazi = kapsam_metni(db, kapsam, kapsam_id)
    gunluk.kaydet(db, veren["id"], "DEVIR", f"Oy devri → @{alan['takma_ad']} ({kapsam_yazi})")
    defter.ekle(db, "DEVIR", {"veren": veren["takma_ad"], "alan": alan["takma_ad"], "kapsam": kapsam_yazi})
    bildirimler.gonder(db, alan["id"], f"@{veren['takma_ad']} oy hakkını sana devretti ({kapsam_yazi}).",
                       f"/kullanici/{veren['takma_ad']}")


def devir_sil(db, veren, devir_id):
    d = db.execute("SELECT * FROM devirler WHERE id = ? AND veren_id = ?", (devir_id, veren["id"])).fetchone()
    if not d:
        raise KuralHatasi("Devir bulunamadı.")
    db.execute("DELETE FROM devirler WHERE id = ?", (devir_id,))
    kapsam_yazi = kapsam_metni(db, d["kapsam"], d["kapsam_id"])
    gunluk.kaydet(db, veren["id"], "DEVIR_GERI", f"Oy devri geri alındı ({kapsam_yazi})")
    defter.ekle(db, "DEVIR_GERI", {"veren": veren["takma_ad"], "kapsam": kapsam_yazi})


def kapsam_metni(db, kapsam, kapsam_id):
    if kapsam == "GENEL":
        return "tüm forum"
    if kapsam == "KATEGORI":
        return "kategori: " + ontoloji.yol_metni(db, "kategoriler", kapsam_id)
    r = db.execute("SELECT baslik FROM konular WHERE id = ?", (kapsam_id,)).fetchone()
    return "konu: " + (r["baslik"] if r else f"#{kapsam_id}")


def verilen_devirler(db, kullanici_id):
    return db.execute(
        """SELECT d.*, k.takma_ad AS alan_ad, k.yz_mi AS alan_yz FROM devirler d
           JOIN kullanicilar k ON k.id = d.alan_id WHERE d.veren_id = ? ORDER BY d.id""",
        (kullanici_id,),
    ).fetchall()


def alinan_devirler(db, kullanici_id):
    return db.execute(
        """SELECT d.*, k.takma_ad AS veren_ad FROM devirler d
           JOIN kullanicilar k ON k.id = d.veren_id WHERE d.alan_id = ? ORDER BY d.id""",
        (kullanici_id,),
    ).fetchall()


def gecerli_devir(db, kullanici_id, baglam):
    """Bu bağlamda kullanıcının oyunu kime devrettiği: en özel kapsam kazanır."""
    devirler = {(d["kapsam"], d["kapsam_id"]): d["alan_id"] for d in
                db.execute("SELECT * FROM devirler WHERE veren_id = ?", (kullanici_id,))}
    if not devirler:
        return None, None
    if baglam.konu is not None:
        for k in reversed(uygunluk.konu_zinciri(db, baglam.konu)):
            if ("KONU", k["id"]) in devirler:
                return devirler[("KONU", k["id"])], "KONU"
    kategoriler = ontoloji.atalar(db, "kategoriler", baglam.kategori_id) if baglam.kategori_id else []
    for kategori_id in reversed(kategoriler):
        if ("KATEGORI", kategori_id) in devirler:
            return devirler[("KATEGORI", kategori_id)], "KATEGORI"
    if ("GENEL", 0) in devirler:
        return devirler[("GENEL", 0)], "GENEL"
    return None, None


def _zinciri_izle(db, kullanici_id, baglam, dogrudan, hakli):
    """(oyun ulaştığı doğrudan oy veren, düşme nedeni)."""
    gorulen, x = {kullanici_id}, kullanici_id
    while True:
        alan, _ = gecerli_devir(db, x, baglam)
        if alan is None:
            return None, None          # zincir oy vermeyen birinde bitti: oy kullanılmadı
        if alan in gorulen:
            return None, "DONGU"
        if alan not in hakli:
            return None, "HAK_YOK"
        if alan in dogrudan:
            return alan, None
        gorulen.add(alan)
        x = alan


def devirleri_coz(db, baglam, dogrudan, hakli):
    """Doğrudan oy vermeyen hak sahiplerinin oylarını zincir boyunca taşır.

    dogrudan: doğrudan oy veren kullanıcı id'leri
    hakli:    bu oylamada oy hakkı olan kullanıcı id'leri
    Döner: ({oy_veren_id: [devreden_id, ...]}, [(kullanici_id, neden_kodu), ...])
    """
    tasinan, dusen = defaultdict(list), []
    for uid in sorted(hakli):
        if uid in dogrudan:
            continue
        hedef, neden = _zinciri_izle(db, uid, baglam, dogrudan, hakli)
        if hedef is not None:
            tasinan[hedef].append(uid)
        elif neden:
            dusen.append((uid, neden))
    tavan = yonetmelik.deger(db, "MAX_DEVIR")
    for hedef, liste in tasinan.items():
        if len(liste) > tavan:
            dusen.extend((uid, "TAVAN") for uid in liste[tavan:])
            tasinan[hedef] = liste[:tavan]
    return dict(tasinan), dusen
