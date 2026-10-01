"""Yapay zeka üye (ör. Bilge): yalnızca kısa özetler yazar.

Oy kullanmaz, fikir yazmaz, kararlara karışmaz. İki işi vardır:
  * Tartışma özeti: oylama başlarken (ve bir katılımcı isteyince) tartışmayı ve fikirleri kısaca özetler.
  * Tur özeti: her tur bitince kimin ne kadar oy aldığını ve ne olduğunu kısaca yazar.
Özetler kural tabanlıdır: sayılara dayanır, yorum katmaz.
"""
from . import konular


def asistan(db):
    return db.execute("SELECT * FROM kullanicilar WHERE yz_mi = 1 ORDER BY id LIMIT 1").fetchone()


def _yuzde(x):
    return f"%{round(x * 100)}"


def tartisma_ozeti(db, konu_id):
    """Döner: özet yazıldıysa True (yapay zeka hesabı yoksa False)."""
    ai = asistan(db)
    if not ai:
        return False
    mesajlar = db.execute("""SELECT m.*, k.takma_ad FROM mesajlar m LEFT JOIN kullanicilar k ON k.id = m.yazar_id
                             WHERE m.konu_id = ? AND m.gizli = 0 AND m.tip NOT IN ('SISTEM', 'YZ')""", (konu_id,)).fetchall()
    fikirler = [m for m in mesajlar if m["tip"] == "FIKIR"]
    yazanlar = {m["yazar_id"] for m in mesajlar}
    satirlar = [f"Özet: {len(yazanlar)} kişi {len(mesajlar)} mesaj yazdı; {len(fikirler)} fikir var."]
    for f in fikirler:
        yanitlar = [m for m in mesajlar if m["ust_mesaj_id"] == f["id"]]
        destek = sum(1 for m in yanitlar if m["tip"] == "ARGUMAN")
        karsi = sum(1 for m in yanitlar if m["tip"] == "KARSI_ARGUMAN")
        satirlar.append(f"• @{f['takma_ad']}: “{konular._kisalt(f['icerik'], 90)}” ({destek} argüman, {karsi} karşı argüman)")
    if not fikirler:
        satirlar.append("Henüz fikir yazılmadı. Her katılımcı 1. tur bitene kadar bir fikir yazabilir.")
    konular.yz_mesaji(db, konu_id, ai, "\n".join(satirlar))
    return True


def tur_ozeti(db, konu_id, tur_no, s, sonuc, kalanlar):
    """sonuc: KABUL / DEVAM / SONUCSUZ (sonuclar.tur_karari). kalanlar: kabul edilen ya da sonraki tura kalan fikirler."""
    ai = asistan(db)
    if not ai or not s["secenekler"]:
        return
    kalan_anahtarlar = {f["anahtar"] for f in kalanlar}
    satirlar = [f"{tur_no}. tur özeti: {s['katilan']} kişi oy verdi"
                + (f", {s['cekimser']['kisi']} çekimser" if s["cekimser"]["kisi"] else "") + "."]
    for f in s["secenekler"]:
        durum = ("kabul edildi" if sonuc == "KABUL" else "sonraki tura kaldı") if f["anahtar"] in kalan_anahtarlar \
            else ("elendi" if sonuc != "SONUCSUZ" else "")
        satirlar.append(f"• {_yuzde(f['oran'])} “{konular._kisalt(f['metin'], 80)}”" + (f" → {durum}" if durum else ""))
    konular.yz_mesaji(db, konu_id, ai, "\n".join(satirlar))
