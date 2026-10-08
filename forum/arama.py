"""Tam metin arama (SQLite FTS5). Türkçe karakterler katlanarak indekslenir: "öğrenci" = "ogrenci"."""
import re

from . import ontoloji


def indeksle(db, tur, ref_id, konu_id, metin):
    db.execute("DELETE FROM arama WHERE tur = ? AND ref_id = ?", (tur, ref_id))
    db.execute("INSERT INTO arama (tur, ref_id, konu_id, metin) VALUES (?, ?, ?, ?)",
               (tur, ref_id, konu_id, ontoloji.katla(metin)))


def kaldir(db, tur, ref_id):
    db.execute("DELETE FROM arama WHERE tur = ? AND ref_id = ?", (tur, ref_id))


def _alinti(metin, kelimeler, uzunluk=180):
    katli = ontoloji.katla(metin)
    konum = min((katli.find(k) for k in kelimeler if katli.find(k) >= 0), default=0)
    bas = max(0, konum - 50)
    parca = metin[bas: bas + uzunluk]
    return ("…" if bas else "") + parca + ("…" if bas + uzunluk < len(metin) else "")


def ara(db, sorgu, limit=40):
    kelimeler = [k for k in re.findall(r"[a-z0-9]+", ontoloji.katla(sorgu or "")) if len(k) >= 2][:8]
    if not kelimeler:
        return []
    ifade = " AND ".join(f"{k}*" for k in kelimeler)
    sonuclar = []
    for r in db.execute("SELECT tur, ref_id, konu_id FROM arama WHERE arama MATCH ? ORDER BY rank LIMIT ?",
                        (ifade, limit)):
        konu = db.execute("SELECT id, baslik, aciklama, durum, silindi FROM konular WHERE id = ?",
                          (r["konu_id"],)).fetchone()
        if not konu or konu["silindi"]:
            continue
        if r["tur"] == "KONU":
            sonuclar.append({"tur": "Konu", "konu": konu, "baglanti": f"/konu/{konu['id']}",
                             "alinti": _alinti(konu["aciklama"], kelimeler)})
        else:
            m = db.execute("SELECT m.*, k.takma_ad FROM mesajlar m LEFT JOIN kullanicilar k ON k.id = m.yazar_id "
                           "WHERE m.id = ?", (r["ref_id"],)).fetchone()
            if not m or m["gizli"]:
                continue
            sonuclar.append({"tur": "Mesaj", "konu": konu, "yazar": m["takma_ad"],
                             "baglanti": f"/konu/{konu['id']}#m{m['id']}", "alinti": _alinti(m["icerik"], kelimeler)})
    return sonuclar
