"""Bildirimler: üyeye kendisini ilgilendiren olayları haber verir."""
from . import zaman


def gonder(db, kullanici_id, metin, baglanti):
    if kullanici_id is None:
        return
    k = db.execute("SELECT yz_mi FROM kullanicilar WHERE id = ?", (kullanici_id,)).fetchone()
    if not k or k["yz_mi"]:
        return
    db.execute("INSERT INTO bildirimler (kullanici_id, metin, baglanti, olusturma) VALUES (?, ?, ?, ?)",
               (kullanici_id, metin, baglanti, zaman.simdi_metin()))
    from . import anlik
    anlik.kuyruga_ekle(db, kullanici_id, metin, baglanti)


def coklu_gonder(db, kullanici_idleri, metin, baglanti, haric=None):
    for kid in set(kullanici_idleri) - {haric}:
        gonder(db, kid, metin, baglanti)


def okunmamis_sayisi(db, kullanici_id):
    return db.execute("SELECT COUNT(*) FROM bildirimler WHERE kullanici_id = ? AND okundu = 0",
                      (kullanici_id,)).fetchone()[0]


def liste(db, kullanici_id, sayfa=1, boy=20):
    toplam = db.execute("SELECT COUNT(*) FROM bildirimler WHERE kullanici_id = ?", (kullanici_id,)).fetchone()[0]
    satirlar = db.execute("SELECT * FROM bildirimler WHERE kullanici_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                          (kullanici_id, boy, (sayfa - 1) * boy)).fetchall()
    return satirlar, toplam


def hepsini_okundu_yap(db, kullanici_id):
    db.execute("UPDATE bildirimler SET okundu = 1 WHERE kullanici_id = ? AND okundu = 0", (kullanici_id,))


def okundu_yap(db, kullanici_id, bildirim_id):
    r = db.execute("SELECT baglanti FROM bildirimler WHERE id = ? AND kullanici_id = ?",
                   (bildirim_id, kullanici_id)).fetchone()
    if r:
        db.execute("UPDATE bildirimler SET okundu = 1 WHERE id = ?", (bildirim_id,))
    return r["baglanti"] if r else None


def konu_katilimcilari(db, konu_id):
    """Konuya mesaj yazmış ya da konuyu açmış kişiler."""
    idler = {r["yazar_id"] for r in db.execute(
        "SELECT DISTINCT yazar_id FROM mesajlar WHERE konu_id = ? AND yazar_id IS NOT NULL", (konu_id,))}
    sahip = db.execute("SELECT sahip_id FROM konular WHERE id = ?", (konu_id,)).fetchone()
    if sahip:
        idler.add(sahip["sahip_id"])
    return idler


def takipciler(db, kullanici_id):
    return [r["takip_eden_id"] for r in
            db.execute("SELECT takip_eden_id FROM takipler WHERE takip_edilen_id = ?", (kullanici_id,))]
