"""Yapay zeka üye (ör. Bilge): yalnızca kısa özetler yazar.

Oy kullanmaz, fikir yazmaz, kararlara karışmaz. İki işi vardır:
  * Tartışma özeti: oylama başlarken (ve bir katılımcı isteyince) tartışmayı ve fikirleri kısaca özetler.
  * Tur özeti: her tur bitince kimin ne kadar oy aldığını ve ne olduğunu kısaca yazar.
Özetler KURAL TABANLIDIR: her sayı veritabanından gelir, yorum katmaz. Bu bilinçli bir seçimdir; gerekçesi
docs/analiz.md'deki "YZ gerekli mi?" bölümündedir (dil modeli uydurma sayı üretebilir, kararı etkileyebilir).
"""
from . import konular, uygunluk
from .hatalar import KuralHatasi
from .konu_durumlari import yazilabilir_olmali
from .metin import kisalt, yuzde

YANIT_TURLERI = ("ARGUMAN", "KARSI_ARGUMAN", "SORU", "KAYNAK")


def asistan(db):
    return db.execute("SELECT * FROM kullanicilar WHERE yz_mi = 1 ORDER BY id LIMIT 1").fetchone()


def _alt_yanitlar(mesajlar, kok_id):
    """Bir mesajın altındaki bütün yanıtlar (yanıtların yanıtları dahil)."""
    cocuklar = {}
    for m in mesajlar:
        cocuklar.setdefault(m["ust_mesaj_id"], []).append(m)
    sonuc, bekleyen = [], list(cocuklar.get(kok_id, []))
    while bekleyen:
        m = bekleyen.pop()
        sonuc.append(m)
        bekleyen.extend(cocuklar.get(m["id"], []))
    return sonuc


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
        yanitlar = _alt_yanitlar(mesajlar, f["id"])
        sayilar = [(sum(1 for m in yanitlar if m["tip"] == tip), ad) for tip, ad in
                   (("ARGUMAN", "argüman"), ("KARSI_ARGUMAN", "karşı argüman"), ("SORU", "soru"), ("KAYNAK", "kaynak"))]
        dokum = ", ".join(f"{n} {ad}" for n, ad in sayilar if n) or "henüz yanıt yok"
        satirlar.append(f"• @{f['takma_ad']}: “{kisalt(f['icerik'], 90)}” ({dokum})")
    if not fikirler:
        satirlar.append("Henüz fikir yazılmadı. Her katılımcı 1. tur bitene kadar bir fikir yazabilir.")
    konular.yz_mesaji(db, konu_id, ai, "\n".join(satirlar))
    return True


def ozet_iste(db, kullanici, konu_id):
    """Bir katılımcının istediği tartışma özeti. Son özetten beri yeni mesaj yoksa yeni özet yazılmaz
    (aynı özetin tekrar tekrar yazılıp tartışmayı doldurması ve deftere boş blok eklenmesi önlenir)."""
    konu = konular.konu_getir(db, konu_id)
    yazilabilir_olmali(konu)
    if not uygunluk.uygunluk(db, kullanici, konu).katilimci:
        raise KuralHatasi("Özet, süren bir konuda katılımcılar tarafından istenebilir.")
    son_ozet = db.execute("SELECT MAX(id) FROM mesajlar WHERE konu_id = ? AND tip = 'YZ'", (konu_id,)).fetchone()[0]
    if son_ozet and not db.execute("SELECT 1 FROM mesajlar WHERE konu_id = ? AND id > ? AND tip NOT IN ('SISTEM', 'YZ')",
                                   (konu_id, son_ozet)).fetchone():
        raise KuralHatasi("Son özetten beri yeni mesaj yazılmadı; özet zaten güncel.")
    if not tartisma_ozeti(db, konu_id):
        raise KuralHatasi("Forumda özet yazacak bir yapay zeka hesabı yok.")


def tur_ozeti(db, konu_id, tur_no, s, karar):
    """karar: sonuclar.TurKarari. Her fikrin durumu kararın kendisinden okunur; oranlar kesilerek yazılır
    (%74,5 "%75" diye yazılıp ezici üstünlük sanılmasın)."""
    ai = asistan(db)
    if not ai or not s["secenekler"]:
        return
    satirlar = [f"{tur_no}. tur özeti: {s['katilan']} kişi oy verdi"
                + (f", {s['cekimser']['kisi']} çekimser" if s["cekimser"]["kisi"] else "") + "."]
    for f in s["secenekler"]:
        if f.get("gizli"):
            durum = "oylamayla gizlendi"
        elif f["anahtar"] in karar.kalanlar:
            durum = "kabul edildi" if karar.sonuc == "KABUL" else "sonraki tura kaldı"
        elif f["anahtar"] in karar.elenenler:
            durum = f"{yuzde(karar.eleme)} eşiğinin altında kaldı, elendi"
        else:
            durum = "kabul edilmedi" if karar.sonuc == "KABUL" else ""
        satirlar.append(f"• {yuzde(f['oran'])} “{kisalt(f['metin'], 80)}”" + (f" → {durum}" if durum else ""))
    konular.yz_mesaji(db, konu_id, ai, "\n".join(satirlar))
