"""Kategoriler: forumun zamanla büyüyen konu ağacı.

7 temel alan ve Genel kategori hazır gelir (ontoloji.KATEGORILER). Her üye yeni bir ana kategori ya da bir ana
kategorinin altına alt kategori önerebilir. Öneri bütün üyelerin oyuna sunulur (herkes 1 oy, ESIK_KATEGORI);
kabul edilirse kategori eklenir ve önerirken yazılan kavramlar kategori denetiminde (D3) kullanılır.
"""
import json
from datetime import timedelta

from . import ayarlar, bildirimler, defter, gunluk, ontoloji, oylama, yonetmelik, zaman
from .hatalar import KuralHatasi

MAX_KAVRAM = 15
SIRALAMALAR = {"populer": "En çok konu", "etkin": "Son etkinlik", "ad": "Ada göre", "yeni": "En yeni"}
SUZGECLER = {"": "Tümü", "ana": "Ana kategoriler", "alt": "Alt kategoriler", "topluluk": "Topluluğun ekledikleri",
             "dolu": "Konusu olanlar"}


def kategori_adi(ad):
    ad = " ".join((ad or "").split())
    if not 2 <= len(ad) <= 40:
        raise KuralHatasi("Kategori adı 2–40 karakter olmalı.")
    return ad


def _kardes_var_mi(db, ad, ust_id):
    return db.execute("SELECT 1 FROM kategoriler WHERE ad = ? COLLATE NOCASE AND ust_id IS ?", (ad, ust_id)).fetchone()


def _ust_kategori(db, ust_id):
    if not ust_id:
        return None
    try:
        ust = ontoloji.dugum(db, "kategoriler", int(ust_id))
    except (TypeError, ValueError):
        ust = None
    if not ust or ust["ust_id"] is not None:
        raise KuralHatasi("Alt kategori yalnızca bir ana kategorinin altına eklenebilir.")
    if ust["ad"] == ayarlar.GENEL_KATEGORI:
        raise KuralHatasi("Genel kategorinin alt kategorisi olmaz; yeni bir ana kategori öner.")
    return ust


def _kavramlar(metin):
    terimler = []
    for t in (metin or "").split(","):
        t = ontoloji.katla(" ".join(t.split()))
        if not t:
            continue
        if not 2 <= len(t) <= 30:
            raise KuralHatasi("Her kavram 2–30 karakter olmalı.")
        if t not in terimler:
            terimler.append(t)
    if len(terimler) > MAX_KAVRAM:
        raise KuralHatasi(f"En fazla {MAX_KAVRAM} kavram yazılabilir.")
    return terimler


def oner(db, kullanici, ad, ust_id, kavramlar, gerekce):
    """Yeni kategori önerisini oylamaya sunar. Döner: oylamanın id'si."""
    if kullanici["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları kategori öneremez.")
    ad = kategori_adi(ad)
    ust = _ust_kategori(db, ust_id)
    ust_id = ust["id"] if ust else None
    if _kardes_var_mi(db, ad, ust_id):
        raise KuralHatasi(f"“{ad}” adında bir kategori zaten var.")
    for t in oylama_suren_oneriler(db):
        veri = json.loads(t["veri"])
        if ontoloji.katla(veri["ad"]) == ontoloji.katla(ad) and veri.get("ust_id") == ust_id:
            raise KuralHatasi("Bu kategori için zaten süren bir oylama var.")
        if t["acan_id"] == kullanici["id"]:
            raise KuralHatasi("Oylamada bekleyen bir kategori önerin var; o sonuçlanınca yenisini önerebilirsin.")
    terimler = _kavramlar(kavramlar)
    gerekce = (gerekce or "").strip()
    if len(gerekce) < 20:
        raise KuralHatasi("Bu kategoriye neden ihtiyaç olduğunu yaz (en az 20 karakter).")
    yonetmelik.mesaj_denetle(db, f"{ad} {gerekce} {' '.join(terimler)}")
    return oylama.teklif_ac(db, "KATEGORI", kullanici["id"], gerekce=gerekce,
                            veri={"ad": ad, "ust_id": ust_id, "kavramlar": terimler})


def oylama_suren_oneriler(db):
    return db.execute("SELECT * FROM teklifler WHERE tip = 'KATEGORI' AND durum = 'ACIK' ORDER BY bitis").fetchall()


def son_oneriler(db, limit=8):
    return db.execute("SELECT * FROM teklifler WHERE tip = 'KATEGORI' AND durum != 'ACIK' ORDER BY id DESC LIMIT ?",
                      (limit,)).fetchall()


def oneri_basligi(db, veri):
    ust = f"{ontoloji.ad(db, 'kategoriler', veri['ust_id'])} › " if veri.get("ust_id") else ""
    return f"{ust}{veri['ad']}"


def ekle(db, teklif):
    """Kabul edilen öneriyi kategori olarak ekler (o arada aynı adda kategori açıldıysa eklemez)."""
    veri = json.loads(teklif["veri"])
    ust_id = veri.get("ust_id")
    if _kardes_var_mi(db, veri["ad"], ust_id) or (ust_id and not ontoloji.dugum(db, "kategoriler", ust_id)):
        return None
    yeni = db.execute("INSERT INTO kategoriler (ad, ust_id, kaynak, kavramlar, olusturma) VALUES (?, ?, 'TOPLULUK', ?, ?)",
                      (veri["ad"], ust_id, ",".join(veri.get("kavramlar") or []) or None, zaman.simdi_metin())).lastrowid
    db.onbellek.clear()
    yol = ontoloji.yol_metni(db, "kategoriler", yeni)
    gunluk.kaydet(db, teklif["acan_id"], "YENI_KATEGORI", f"Oylamayla yeni kategori eklendi: {yol}")
    defter.ekle(db, "KATEGORI", {"kategori": yol, "teklif": teklif["id"]})
    bildirimler.gonder(db, teklif["acan_id"], f"Önerdiğin “{yol}” kategorisi kabul edildi ve eklendi.",
                       f"/konular?kategori={yeni}")
    return yeni


# --- Kategoriler sayfası ---

def liste(db, siralama="populer", aranan="", suzgec=""):
    """Her kategori için sayılar; arama, süzme ve sıralama uygulanmış olarak."""
    tum = db.execute("SELECT * FROM kategoriler").fetchall()
    konu = {r["kategori_id"]: r for r in db.execute(
        """SELECT kategori_id, COUNT(*) AS n, SUM(durum IN ('TARTISMA', 'OYLAMA')) AS acik FROM konular
           WHERE silindi = 0 GROUP BY kategori_id""")}
    son = {r["kategori_id"]: r["son"] for r in db.execute(
        """SELECT k.kategori_id, MAX(m.olusturma) AS son FROM mesajlar m JOIN konular k ON k.id = m.konu_id
           WHERE k.silindi = 0 GROUP BY k.kategori_id""")}
    hafta = zaman.metin(zaman.simdi() - timedelta(days=7))
    haftalik = {r["kategori_id"]: r["n"] for r in db.execute(
        """SELECT k.kategori_id, COUNT(*) AS n FROM mesajlar m JOIN konular k ON k.id = m.konu_id
           WHERE k.silindi = 0 AND m.yazar_id IS NOT NULL AND m.olusturma >= ? GROUP BY k.kategori_id""", (hafta,))}
    simdi = zaman.simdi_metin()
    uzman = {}
    for r in db.execute("SELECT kategori_id, COUNT(DISTINCT kullanici_id) AS n FROM uzmanliklar "
                        "WHERE baslangic <= ? AND bitis > ? GROUP BY kategori_id", (simdi, simdi)):
        uzman[r["kategori_id"]] = r["n"]

    def topla(kid, sozluk, alan=None):
        ids = ontoloji.alt_agac(db, "kategoriler", kid)
        return sum(((sozluk[i][alan] or 0) if alan else sozluk[i]) for i in ids if i in sozluk)

    satirlar = []
    for k in tum:
        ids = ontoloji.alt_agac(db, "kategoriler", k["id"])
        satirlar.append({
            "id": k["id"], "ad": k["ad"], "ust_id": k["ust_id"], "yol": ontoloji.yol_metni(db, "kategoriler", k["id"]),
            "renk": ontoloji.kategori_rengi(db, k["id"]), "kaynak": k["kaynak"], "olusturma": k["olusturma"] or "",
            "konu": topla(k["id"], konu, "n"), "acik": topla(k["id"], konu, "acik"), "hafta": topla(k["id"], haftalik),
            "uzman": topla(k["id"], uzman), "son": max([son[i] for i in ids if i in son] or [""]),
            "genel": k["ad"] == ayarlar.GENEL_KATEGORI and k["ust_id"] is None,
            "altlar": [], "kavramlar": ontoloji.kavramlar(dict(k))[:8],
        })
    harita = {s["id"]: s for s in satirlar}
    for s in satirlar:
        if s["ust_id"] in harita:
            harita[s["ust_id"]]["altlar"].append(s)

    aranan = ontoloji.katla((aranan or "").strip())
    if aranan:
        satirlar = [s for s in satirlar if aranan in ontoloji.katla(s["yol"]) or any(aranan in t for t in s["kavramlar"])]
    satirlar = [s for s in satirlar if {"ana": s["ust_id"] is None, "alt": s["ust_id"] is not None,
                                          "topluluk": s["kaynak"] == "TOPLULUK", "dolu": s["konu"] > 0}.get(suzgec, True)]
    anahtar = {"ad": lambda s: ontoloji.tr_sirala(s["yol"]),
               "yeni": lambda s: s["olusturma"],
               "etkin": lambda s: s["son"],
               "populer": lambda s: (s["konu"], s["hafta"])}.get(siralama) or (lambda s: (s["konu"], s["hafta"]))
    satirlar.sort(key=anahtar, reverse=siralama != "ad")
    for s in satirlar:
        s["altlar"].sort(key=lambda a: -a["konu"])
    return satirlar


def ana_kategoriler(db):
    """Öneri formundaki "hangi ana kategorinin altına?" seçenekleri (Genel hariç)."""
    return [(k["id"], k["ad"]) for k in sorted(
        db.execute("SELECT id, ad FROM kategoriler WHERE ust_id IS NULL").fetchall(), key=lambda k: ontoloji.tr_sirala(k["ad"]))
        if k["ad"] != ayarlar.GENEL_KATEGORI]
