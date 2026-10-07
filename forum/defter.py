"""Dağıtık defter (distributed ledger).

Forumda olan her önemli olay (tasarı, mesaj özeti, oy taahhüdü, sonuç, karar...) bir blok olarak
hash zincirine eklenir. Zincir birden fazla düğümde (A, B, C düğümleri) ayrı dosyalarda tutulur:

  * Her blok bir öncekinin hash'ini içerir: bir blok değiştirilirse sonraki bütün bağlar kopar.
  * Düğümler çoğunlukla uzlaşır: 3 düğümden 2'si aynı zincirdeyse o zincir geçerlidir.
  * Bozulan bir düğüm tespit edilir ve sağlam düğümlerden onarılır.
  * Veritabanı defterle karşılaştırılır: silinen ya da gizlice değiştirilen mesaj/oy yakalanır.

Kişisel veri deftere yazılmaz: mesajların sadece SHA-256 özeti, oyların sadece taahhüdü yazılır.
"""
import hashlib
import json
import os
import random
import sqlite3
import threading
from collections import Counter

from . import ayarlar, zaman

_KILIT = threading.Lock()
BASLANGIC_HASH = "0" * 64
# Deftere yazılabilen blok türleri (tek doğruluk kaynağı: defter sayfasındaki süzgeç de buradan gelir).
BLOK_TURLERI = ("KONU", "KONU_DUZENLEME", "KONU_DURUM", "MESAJ", "MESAJ_DUZENLEME", "GIZLEME", "TEKLIF", "OY", "SONUC",
                "KARAR", "DEVIR", "DEVIR_GERI", "UYE", "UZMANLIK", "KATEGORI", "YONETIM")
BASLANGIC_ZAMANI = "2026-01-01 00:00:00"


def ozet(metin):
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def blok_hash(no, zaman_, tur, veri, onceki):
    return ozet(f"{no}|{zaman_}|{tur}|{veri}|{onceki}")


def ekle(db, tur, veri):
    """Kaydı işlem kuyruğuna ekler; veritabanı commit edilince düğümlere yazılır."""
    if tur not in BLOK_TURLERI:
        raise ValueError(f"Bilinmeyen defter bloğu türü: {tur}")
    if db.defter_klasoru:
        db.defter_kuyrugu.append((tur, json.dumps(veri, ensure_ascii=False, sort_keys=True), zaman.simdi_metin()))


# --- Düğümler ---

def _dugum_yolu(klasor, ad):
    return os.path.join(klasor, f"{ad}.db")


def _baglan(klasor, ad):
    os.makedirs(klasor, exist_ok=True)
    c = sqlite3.connect(_dugum_yolu(klasor, ad), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS bloklar (
                   no INTEGER PRIMARY KEY, zaman TEXT NOT NULL, tur TEXT NOT NULL,
                   veri TEXT NOT NULL, onceki TEXT NOT NULL, hash TEXT NOT NULL)""")
    if c.execute("SELECT COUNT(*) FROM bloklar").fetchone()[0] == 0:
        z = BASLANGIC_ZAMANI   # sabit: bütün düğümlerin başlangıç bloğu birebir aynı olmalı
        veri = json.dumps({"ad": ayarlar.SITE_ADI + " dağıtık defteri", "dugumler": ayarlar.DEFTER_DUGUMLERI}, ensure_ascii=False)
        c.execute("INSERT INTO bloklar VALUES (0, ?, 'BASLANGIC', ?, ?, ?)",
                  (z, veri, BASLANGIC_HASH, blok_hash(0, z, "BASLANGIC", veri, BASLANGIC_HASH)))
        c.commit()
    return c


def _zincir(klasor, ad):
    c = _baglan(klasor, ad)
    try:
        return [dict(r) for r in c.execute("SELECT * FROM bloklar ORDER BY no")]
    finally:
        c.close()


def zinciri_dogrula(bloklar):
    """(geçerli_mi, ilk bozuk blok no)."""
    onceki = BASLANGIC_HASH
    for i, b in enumerate(bloklar):
        if b["no"] != i or b["onceki"] != onceki or b["hash"] != blok_hash(b["no"], b["zaman"], b["tur"],
                                                                         b["veri"], b["onceki"]):
            return False, b["no"]
        onceki = b["hash"]
    return True, None


def _uzlasma(klasor):
    """Geçerli zincirlerin baş hash'lerine göre çoğunluk zinciri: (baş hash, zincir, düğüm durumları)."""
    zincirler, durumlar = {}, []
    for ad in ayarlar.DEFTER_DUGUMLERI:
        z = _zincir(klasor, ad)
        gecerli, bozuk = zinciri_dogrula(z)
        zincirler[ad] = z
        durumlar.append({"ad": ad, "uzunluk": len(z), "bas": z[-1]["hash"] if z else None,
                         "gecerli": gecerli, "bozuk_blok": bozuk})
    sayac = Counter(d["bas"] for d in durumlar if d["gecerli"])
    if not sayac:
        return None, [], durumlar
    bas, oy = sayac.most_common(1)[0]
    cogunluk = oy > len(ayarlar.DEFTER_DUGUMLERI) // 2
    kaynak = next(d["ad"] for d in durumlar if d["gecerli"] and d["bas"] == bas)
    for d in durumlar:
        if not d["gecerli"]:
            d["durum"] = "BOZUK"
        elif d["bas"] == bas:
            d["durum"] = "UYUMLU" if cogunluk else "AZINLIKTA"
        else:
            d["durum"] = "AYRISMIS"
    return (bas if cogunluk else None), zincirler[kaynak], durumlar


def dugumlere_yaz(klasor, kuyruk):
    with _KILIT:
        bas, zincir, durumlar = _uzlasma(klasor)
        if not zincir:
            return
        son = zincir[-1]
        yeni = []
        for tur, veri, z in kuyruk:
            no = son["no"] + 1
            h = blok_hash(no, z, tur, veri, son["hash"])
            son = {"no": no, "zaman": z, "tur": tur, "veri": veri, "onceki": son["hash"], "hash": h}
            yeni.append(son)
        for d in durumlar:
            if d["bas"] != zincir[-1]["hash"] or not d["gecerli"]:
                continue   # bozuk ya da ayrışmış düğüme yazılmaz; önce onarılmalı
            c = _baglan(klasor, d["ad"])
            c.executemany("INSERT INTO bloklar VALUES (:no, :zaman, :tur, :veri, :onceki, :hash)", yeni)
            c.commit()
            c.close()


def durum(klasor):
    bas, zincir, durumlar = _uzlasma(klasor)
    return {"bas": bas, "uzunluk": len(zincir), "dugumler": durumlar,
            "saglikli": all(d.get("durum") == "UYUMLU" for d in durumlar)}


def onar(klasor, ad):
    """Bozuk/ayrışmış düğümü çoğunluk zincirinden yeniden kurar."""
    with _KILIT:
        bas, zincir, _ = _uzlasma(klasor)
        if bas is None:
            raise ValueError("Çoğunluk sağlanamıyor; onarım için en az iki sağlam düğüm gerekli.")
        c = _baglan(klasor, ad)
        c.execute("DELETE FROM bloklar")
        c.executemany("INSERT INTO bloklar VALUES (:no, :zaman, :tur, :veri, :onceki, :hash)", zincir)
        c.commit()
        c.close()


def boz_demo(klasor, ad):
    """SADECE DEMO: bir düğümdeki rastgele bir bloğun verisini hash'i güncellemeden değiştirir."""
    with _KILIT:
        c = _baglan(klasor, ad)
        adaylar = [r["no"] for r in c.execute("SELECT no FROM bloklar WHERE no > 0")]
        if adaylar:
            no = random.choice(adaylar)
            c.execute("UPDATE bloklar SET veri = json_set(veri, '$.kurcalandi', 1) WHERE no = ?", (no,))
            c.commit()
        c.close()
        return adaylar and no


# --- Okuma ---

def bloklar(klasor, sayfa=1, boy=25, tur=None):
    _, zincir, _ = _uzlasma(klasor)
    liste = [b for b in reversed(zincir) if tur is None or b["tur"] == tur]
    toplam = len(liste)
    secilen = liste[(sayfa - 1) * boy: sayfa * boy]
    for b in secilen:
        b["veri_json"] = json.loads(b["veri"])
    return secilen, toplam


def blok_bul(klasor, anahtar):
    _, zincir, _ = _uzlasma(klasor)
    for b in zincir:
        if b["hash"].startswith(anahtar) or str(b["no"]) == anahtar:
            b["veri_json"] = json.loads(b["veri"])
            return b
    return None


def taahhut(teklif_id, secim, makbuz):
    return ozet(f"{teklif_id}|{secim}|{makbuz}")


def makbuz_dogrula(klasor, teklif_id, makbuz, secenekler):
    """Makbuz koduyla, oyun deftere hangi seçimle yazıldığını bulur (seçim sadece makbuz sahibince bilinir)."""
    olasi = {taahhut(teklif_id, s, makbuz.strip()): s for s in secenekler}
    _, zincir, _ = _uzlasma(klasor)
    bulunan = None
    for b in zincir:
        if b["tur"] != "OY":
            continue
        v = json.loads(b["veri"])
        if v.get("teklif") == teklif_id and v.get("taahhut") in olasi:
            bulunan = (b, olasi[v["taahhut"]])
    return bulunan


# --- Veritabanı ile tutarlılık denetimi ---

def tutarlilik(db):
    """Veritabanındaki mesajları, oyları ve sonuçları defterle karşılaştırır."""
    _, zincir, _ = _uzlasma(db.defter_klasoru)
    mesaj_ozetleri, oylar, sonuclar = {}, {}, {}
    for b in zincir:
        v = json.loads(b["veri"])
        if b["tur"] in ("MESAJ", "MESAJ_DUZENLEME"):
            mesaj_ozetleri[v["mesaj"]] = v["ozet"]
        elif b["tur"] == "OY":
            oylar.setdefault(v["teklif"], {})[v["yurttas"]] = v["taahhut"]
        elif b["tur"] == "SONUC":
            sonuclar[v["teklif"]] = v["ozet"]

    sorunlar = []
    db_mesajlar = {r["id"]: r["icerik"] for r in db.execute("SELECT id, icerik FROM mesajlar")}
    for mid, ozet_ in mesaj_ozetleri.items():
        if mid not in db_mesajlar:
            sorunlar.append(f"#{mid} numaralı mesaj veritabanından SİLİNMİŞ (defterde kaydı var).")
        elif ozet(db_mesajlar[mid]) != ozet_:
            sorunlar.append(f"#{mid} numaralı mesaj defterdeki özetle uyuşmuyor (gizlice değiştirilmiş).")
    for mid in db_mesajlar.keys() - mesaj_ozetleri.keys():
        sorunlar.append(f"#{mid} numaralı mesaj deftere hiç yazılmamış.")

    db_oylar = {}
    for r in db.execute("SELECT o.teklif_id, k.takma_ad, o.taahhut FROM oylar o "
                        "JOIN kullanicilar k ON k.id = o.kullanici_id"):
        db_oylar.setdefault(r["teklif_id"], {})[r["takma_ad"]] = r["taahhut"]
    for tid in set(oylar) | set(db_oylar):
        if oylar.get(tid, {}) != db_oylar.get(tid, {}):
            sorunlar.append(f"#{tid} numaralı oylamanın oyları defterle uyuşmuyor.")
    for r in db.execute("SELECT id, sonuc FROM teklifler WHERE sonuc IS NOT NULL"):
        if r["id"] in sonuclar and ozet(r["sonuc"]) != sonuclar[r["id"]]:
            sorunlar.append(f"#{r['id']} numaralı oylamanın sonucu defterdeki özetle uyuşmuyor.")

    return {"sorunlar": sorunlar, "mesaj": len(mesaj_ozetleri), "oylama": len(oylar), "sonuc": len(sonuclar)}
