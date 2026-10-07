"""Dağıtık defter (distributed ledger).

Forumda olan her önemli olay (tasarı, mesaj özeti, oy taahhüdü, sonuç, karar...) bir blok olarak
hash zincirine eklenir. Zincir birden fazla düğümde (A, B, C düğümleri) ayrı dosyalarda tutulur:

  * Her blok bir öncekinin hash'ini içerir: bir blok değiştirilirse sonraki bütün bağlar kopar.
  * Düğümler çoğunlukla uzlaşır: 3 düğümden 2'si aynı zincirdeyse o zincir geçerlidir.
  * Bozulan bir düğüm tespit edilir ve sağlam düğümlerden onarılır.
  * Veritabanı defterle karşılaştırılır: silinen ya da gizlice değiştirilen mesaj/oy yakalanır.

Kişisel veri deftere yazılmaz: mesajların sadece SHA-256 özeti, oyların sadece taahhüdü yazılır.

Tasarım desenleri:
  * **Repository** — bir düğümün blokları nerede saklanırsa saklansın `DugumDeposu` arayüzünün arkasındadır.
    Uzlaşma, onarım ve doğrulama mantığı yalnızca bu arayüzü bilir. Üretimde `SqliteDugumDeposu` (her düğüm ayrı
    dosya), birim testlerinde `BellekDugumDeposu` kullanılır; mantık disk olmadan test edilir.
  * **Observer** — veritabanı bağlantısı defteri tanımaz. Defter, bağlantının "işlem kaydedildi" olayına abone olur
    (`veritabani.commit_aboneligi`) ve kuyruktaki blokları o an düğümlere yazar. Böylece altyapı katmanı (veritabanı)
    üst katmana (defter) bağımlı olmaz (DIP).

Defter işlevlerinin `kaynak` parametresi bir klasör yolu (üretim) ya da `DugumDeposu` listesidir (test).
"""
import hashlib
import json
import logging
import os
import random
import sqlite3
import threading
from abc import ABC, abstractmethod
from collections import Counter

from . import ayarlar, veritabani, zaman

_KILIT = threading.Lock()
log = logging.getLogger(__name__)
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


@veritabani.commit_aboneligi
def _islem_kaydedildi(db):
    """Observer: işlem kaydedilince kuyruktaki blokları düğümlere yazar. Geri alınan işlemin kuyruğu bağlantı
    tarafından zaten boşaltılmıştır (rollback), deftere girmez."""
    if not (db.defter_kuyrugu and db.defter_klasoru):
        return
    kuyruk, db.defter_kuyrugu = db.defter_kuyrugu, []
    try:
        dugumlere_yaz(db.defter_klasoru, kuyruk)
    except Exception:
        # Veri artık kalıcı; istek hata vermez (kullanıcı tekrar denerse çift kayıt oluşurdu). Eksik bloğu
        # tutarlılık denetimi gösterir.
        log.exception("Kayıt defterine %d blok yazılamadı", len(kuyruk))


# --- Düğüm depoları (Repository) ---

def baslangic_blogu():
    """Bütün düğümlerde birebir aynı olan 0 numaralı blok (zamanı sabittir)."""
    veri = json.dumps({"ad": ayarlar.SITE_ADI + " dağıtık defteri", "dugumler": ayarlar.DEFTER_DUGUMLERI},
                      ensure_ascii=False)
    return {"no": 0, "zaman": BASLANGIC_ZAMANI, "tur": "BASLANGIC", "veri": veri, "onceki": BASLANGIC_HASH,
            "hash": blok_hash(0, BASLANGIC_ZAMANI, "BASLANGIC", veri, BASLANGIC_HASH)}


class DugumDeposu(ABC):
    """Bir düğümün blok deposu. Boş bir depo ilk okunduğunda başlangıç bloğuyla açılır."""

    def __init__(self, ad):
        self.ad = ad

    @abstractmethod
    def bloklar(self):
        """Bütün bloklar, numara sırasıyla (sözlük listesi)."""

    @abstractmethod
    def ekle(self, yeni):
        """Blokları zincirin sonuna ekler."""

    @abstractmethod
    def yeniden_kur(self, zincir):
        """Depodaki zinciri verilen zincirle değiştirir (onarım)."""

    @abstractmethod
    def veri_degistir(self, no, veri):
        """Bir bloğun verisini hash'ine dokunmadan değiştirir. SADECE kurcalama gösterimi (boz_demo) içindir."""


_EKLE = "INSERT INTO bloklar VALUES (:no, :zaman, :tur, :veri, :onceki, :hash)"


class SqliteDugumDeposu(DugumDeposu):
    """Üretim deposu: her düğüm klasörde ayrı bir SQLite dosyasıdır (A.db, B.db, C.db)."""

    def __init__(self, klasor, ad):
        super().__init__(ad)
        self.yol = os.path.join(klasor, f"{ad}.db")

    def _baglan(self):
        os.makedirs(os.path.dirname(self.yol), exist_ok=True)
        c = sqlite3.connect(self.yol, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute("""CREATE TABLE IF NOT EXISTS bloklar (
                       no INTEGER PRIMARY KEY, zaman TEXT NOT NULL, tur TEXT NOT NULL,
                       veri TEXT NOT NULL, onceki TEXT NOT NULL, hash TEXT NOT NULL)""")
        if c.execute("SELECT COUNT(*) FROM bloklar").fetchone()[0] == 0:
            c.execute(_EKLE, baslangic_blogu())
            c.commit()
        return c

    def _yaz(self, sql_ler):
        c = self._baglan()
        try:
            for sql, parametre in sql_ler:
                (c.executemany if isinstance(parametre, list) else c.execute)(sql, parametre)
            c.commit()
        finally:
            c.close()

    def bloklar(self):
        c = self._baglan()
        try:
            return [dict(r) for r in c.execute("SELECT * FROM bloklar ORDER BY no")]
        finally:
            c.close()

    def ekle(self, yeni):
        self._yaz([(_EKLE, list(yeni))])

    def yeniden_kur(self, zincir):
        self._yaz([("DELETE FROM bloklar", ()), (_EKLE, list(zincir))])

    def veri_degistir(self, no, veri):
        self._yaz([("UPDATE bloklar SET veri = ? WHERE no = ?", (veri, no))])


class BellekDugumDeposu(DugumDeposu):
    """Test deposu (sahte depo): bloklar bellekte bir listede durur; disk ya da SQLite gerekmez."""

    def __init__(self, ad):
        super().__init__(ad)
        self._bloklar = []

    def bloklar(self):
        if not self._bloklar:
            self._bloklar.append(baslangic_blogu())
        return [dict(b) for b in self._bloklar]

    def ekle(self, yeni):
        self.bloklar()
        self._bloklar.extend(dict(b) for b in yeni)

    def yeniden_kur(self, zincir):
        self._bloklar = [dict(b) for b in zincir]

    def veri_degistir(self, no, veri):
        self.bloklar()
        self._bloklar[no]["veri"] = veri


def bellek_depolari():
    """Her düğüm için boş bir bellek deposu (testler için)."""
    return [BellekDugumDeposu(ad) for ad in ayarlar.DEFTER_DUGUMLERI]


def _depolar(kaynak):
    """kaynak: klasör yolu → SQLite depoları; DugumDeposu listesi ya da {ad: depo} → olduğu gibi. Döner: {ad: depo}."""
    if isinstance(kaynak, (str, os.PathLike)):
        return {ad: SqliteDugumDeposu(kaynak, ad) for ad in ayarlar.DEFTER_DUGUMLERI}
    if isinstance(kaynak, dict):
        return kaynak
    return {d.ad: d for d in kaynak}


def zinciri_dogrula(bloklar):
    """(geçerli_mi, ilk bozuk blok no)."""
    onceki = BASLANGIC_HASH
    for i, b in enumerate(bloklar):
        if b["no"] != i or b["onceki"] != onceki or b["hash"] != blok_hash(b["no"], b["zaman"], b["tur"],
                                                                         b["veri"], b["onceki"]):
            return False, b["no"]
        onceki = b["hash"]
    return True, None


def _uzlasma(kaynak):
    """Geçerli zincirlerin baş hash'lerine göre çoğunluk zinciri: (baş hash, zincir, düğüm durumları)."""
    depolar = _depolar(kaynak)
    zincirler, durumlar = {}, []
    for ad, depo in depolar.items():
        z = depo.bloklar()
        gecerli, bozuk = zinciri_dogrula(z)
        zincirler[ad] = z
        durumlar.append({"ad": ad, "uzunluk": len(z), "bas": z[-1]["hash"] if z else None,
                         "gecerli": gecerli, "bozuk_blok": bozuk})
    sayac = Counter(d["bas"] for d in durumlar if d["gecerli"])
    if not sayac:
        for d in durumlar:
            d["durum"] = "BOZUK"
        return None, [], durumlar
    bas, oy = sayac.most_common(1)[0]
    cogunluk = oy > len(depolar) // 2
    kaynak = next(d["ad"] for d in durumlar if d["gecerli"] and d["bas"] == bas)
    for d in durumlar:
        if not d["gecerli"]:
            d["durum"] = "BOZUK"
        elif d["bas"] == bas:
            d["durum"] = "UYUMLU" if cogunluk else "AZINLIKTA"
        else:
            d["durum"] = "AYRISMIS"
    return (bas if cogunluk else None), zincirler[kaynak], durumlar


def dugumlere_yaz(kaynak, kuyruk):
    """kuyruk: (tür, veri_json, zaman) üçlüleri. Bloklar çoğunluk zincirinin sonuna eklenir ve o zincirdeki
    bütün düğümlere yazılır."""
    with _KILIT:
        depolar = _depolar(kaynak)
        bas, zincir, durumlar = _uzlasma(depolar)
        if not zincir:
            log.error("Kayıt defterinde sağlam düğüm yok; %d blok yazılamadı", len(kuyruk))
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
            depolar[d["ad"]].ekle(yeni)


def durum(kaynak):
    bas, zincir, durumlar = _uzlasma(kaynak)
    return {"bas": bas, "uzunluk": len(zincir), "dugumler": durumlar,
            "saglikli": all(d.get("durum") == "UYUMLU" for d in durumlar)}


def onar(kaynak, ad):
    """Bozuk/ayrışmış düğümü çoğunluk zincirinden yeniden kurar."""
    with _KILIT:
        depolar = _depolar(kaynak)
        bas, zincir, _ = _uzlasma(depolar)
        if bas is None:
            raise ValueError("Çoğunluk sağlanamıyor; onarım için en az iki sağlam düğüm gerekli.")
        depolar[ad].yeniden_kur(zincir)


def boz_demo(kaynak, ad):
    """SADECE DEMO: bir düğümdeki rastgele bir bloğun verisini hash'i güncellemeden değiştirir.
    Döner: bozulan bloğun numarası (başlangıç bloğundan başka blok yoksa None)."""
    with _KILIT:
        depo = _depolar(kaynak)[ad]
        adaylar = [b for b in depo.bloklar() if b["no"] > 0]
        if not adaylar:
            return None
        blok = random.choice(adaylar)
        veri = json.loads(blok["veri"])
        veri["kurcalandi"] = 1
        depo.veri_degistir(blok["no"], json.dumps(veri, ensure_ascii=False, sort_keys=True))
        return blok["no"]


# --- Okuma ---

def bloklar(kaynak, sayfa=1, boy=25, tur=None):
    _, zincir, _ = _uzlasma(kaynak)
    liste = [b for b in reversed(zincir) if tur is None or b["tur"] == tur]
    toplam = len(liste)
    secilen = liste[(sayfa - 1) * boy: sayfa * boy]
    for b in secilen:
        b["veri_json"] = json.loads(b["veri"])
    return secilen, toplam


def blok_bul(kaynak, anahtar):
    _, zincir, _ = _uzlasma(kaynak)
    for b in zincir:
        if b["hash"].startswith(anahtar) or str(b["no"]) == anahtar:
            b["veri_json"] = json.loads(b["veri"])
            return b
    return None


def taahhut(teklif_id, secim, makbuz):
    return ozet(f"{teklif_id}|{secim}|{makbuz}")


def makbuz_dogrula(kaynak, teklif_id, makbuz, secenekler):
    """Makbuz koduyla, oyun deftere hangi seçimle yazıldığını bulur (seçim sadece makbuz sahibince bilinir).
    Döner: None ya da (blok, seçim, güncel_mi). Oy sonradan değiştirildiyse eski makbuzun bloğu güncel değildir."""
    olasi = {taahhut(teklif_id, s, makbuz.strip()): s for s in secenekler}
    _, zincir, _ = _uzlasma(kaynak)
    bulunan, son_oy = None, {}
    for b in zincir:
        if b["tur"] != "OY":
            continue
        v = json.loads(b["veri"])
        if v.get("teklif") != teklif_id:
            continue
        son_oy[v.get("yurttas")] = b["no"]
        if v.get("taahhut") in olasi:
            bulunan = (b, olasi[v["taahhut"]], v.get("yurttas"))
    if not bulunan:
        return None
    blok, secim, yurttas = bulunan
    return blok, secim, son_oy[yurttas] == blok["no"]


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
