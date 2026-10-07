"""Gündem ve trendler: forumda şu an ne konuşuluyor?

Hepsi son etkinlikten hesaplanır (mesaj, fikir, oy); hiçbiri kararları etkilemez, yalnızca okuyana yol gösterir.
  * Trend konular: son 24 saatte (az etkinlik varsa son 3 günde) en çok mesaj, fikir ve oy alan konular.
  * Öne çıkan kelimeler: son 7 günün mesajlarında en çok konuda geçen kelimeler.
  * Kategori nabzı: her ana kategorinin bu haftaki ve geçen haftaki mesaj sayısı, günlük dağılımı.
  * Yakında bitenler, son kararlar, haftanın en etkin üyeleri, canlı akış.
"""
import re
from datetime import timedelta

from . import ayarlar, ontoloji, oylama, zaman

# Öne çıkan kelimelerde sayılmayan sık kelimeler (Türkçe karakterleri katlanmış)
DURAK = set("""
ama ancak artik aslinda ayni ayrica az bana bazi belki ben bence benim bile biraz birlikte bir biz bizim bu buna bunda
bundan bunlar bunu bunun burada butun cok cunku daha degil diger dolayi elbette en evet fakat gibi gore gercekten
hem hep her herkes hic icin iki ile ilgili ise iste iyi kadar karsi katiliyorum kendi kesinlikle ki kim kimse konu
konuda konunun konusu mi mu nasil ne neden nicin olan olarak olmali olmasi olsun olur olursa olabilir once onlar onu
oyle sadece sanki sen sey siz simdi sonra soyle su sunu tabii tam tum uzere var ve veya ya yani yapilsin yapmak yeni
yok zaten edilsin olsa gerek gerekir dusunuyorum fikir fikri fikrim fikrine oylama oylamada tur arkadaslar lutfen
hafta gun saat once sonra neler bizce onerim oneri oneriyorum boyle bunlarin bizler kisi insan olmayan olacak
yerine farkli aksam sabah birden fazla icinde uzerine buyuk kucuk cogu zaman yine ayri bircok hemen tamamen yuksek
dusuk onemli gerekli mumkun ozellikle yalnizca genelde kolay zor kotu ekstra herkese hepsi yapmak olmak etmek
tartisalim tartisma tartismak istiyoruz isteyen olursa oldugu olan yapilabilir aslinda gerci bazen sanirim
""".split())
_KELIME = re.compile(r"[a-zçğıöşüâîû0-9]+")
KISI_BASI_MESAJ = 3     # trend puanında bir kişinin en çok kaç mesajı sayılır


def _once(**sure):
    return zaman.metin(zaman.simdi() - timedelta(**sure))


# --- Trend konular ---

def trend_konular(db, limit=5):
    """Döner: (konular, pencere_saat). Son 24 saatte yeterli etkinlik yoksa pencere 72 saate genişler."""
    for saat in (24, 72, 24 * 14):
        liste = _trend(db, _once(hours=saat), limit)
        if len(liste) >= min(3, limit):
            return liste, saat
    return liste, saat


def _trend(db, esik, limit):
    satirlar = db.execute(
        """SELECT k.id, k.baslik, k.kategori_id, k.durum, k.tur, k.olusturma,
                  (SELECT COUNT(*) FROM mesajlar m WHERE m.konu_id = k.id AND m.yazar_id IS NOT NULL
                     AND m.tip NOT IN ('YZ', 'SISTEM') AND m.olusturma >= :e) AS mesaj,
                  (SELECT COUNT(*) FROM mesajlar m WHERE m.konu_id = k.id AND m.tip = 'FIKIR' AND m.olusturma >= :e) AS fikir,
                  (SELECT COUNT(*) FROM oylar o JOIN teklifler t ON t.id = o.teklif_id
                     WHERE t.konu_id = k.id AND o.zaman >= :e) AS oy,
                  (SELECT COUNT(DISTINCT m.yazar_id) FROM mesajlar m WHERE m.konu_id = k.id AND m.yazar_id IS NOT NULL
                     AND m.tip NOT IN ('YZ', 'SISTEM') AND m.olusturma >= :e) AS kisi
           FROM konular k WHERE k.silindi = 0""", {"e": esik}).fetchall()
    liste = []
    for r in satirlar:
        # Mesajlar kişi başı en çok KISI_BASI_MESAJ kadar sayılır: tek kişi art arda yazarak konuyu gündeme taşıyamasın
        # (ölçüt hedef olunca bozulur; çok kişinin katıldığı konu öne çıkmalı).
        puan = (min(r["mesaj"], KISI_BASI_MESAJ * r["kisi"]) + 2 * r["fikir"] + 0.5 * r["oy"]
                + (3 if r["olusturma"] >= esik else 0))
        if r["mesaj"] or r["oy"] or r["fikir"]:
            liste.append(dict(r, puan=puan))
    liste.sort(key=lambda r: (-r["puan"], -r["id"]))
    tepe = liste[0]["puan"] if liste else 1
    for r in liste:
        r["yuzde"] = round(100 * r["puan"] / tepe)
    return liste[:limit]


# --- Öne çıkan kelimeler ---

def anahtar_kelimeler(db, gun=7, limit=14):
    """[{kelime, konu, adet, boyut}] — en çok farklı konuda geçen kelimeler. boyut 1–4 (etiket bulutu için)."""
    esik = _once(days=gun)
    metinler = [(r["konu_id"], r["icerik"]) for r in db.execute(
        """SELECT m.konu_id, m.icerik FROM mesajlar m JOIN konular k ON k.id = m.konu_id
           WHERE m.gizli = 0 AND k.silindi = 0 AND m.tip NOT IN ('SISTEM', 'YZ') AND m.olusturma >= ?""", (esik,))]
    metinler += [(r["id"], f"{r['baslik']} {r['baslik']} {r['aciklama']}") for r in db.execute(
        "SELECT id, baslik, aciklama FROM konular WHERE silindi = 0 AND olusturma >= ?", (esik,))]
    konular, adet, yazim = {}, {}, {}
    for konu_id, metin in metinler:
        for kelime in _KELIME.findall(ontoloji.tr_kucuk(metin)):
            kok = ontoloji.katla(kelime)
            if len(kok) < 4 or kok in DURAK or kok.isdigit() or (len(kok) >= 6 and kok.endswith(("sin", "sun"))):
                continue
            konular.setdefault(kok, set()).add(konu_id)
            adet[kok] = adet.get(kok, 0) + 1
            yazim.setdefault(kok, {}).setdefault(kelime, 0)
            yazim[kok][kelime] += 1
    sirali = sorted(adet, key=lambda k: (-len(konular[k]), -adet[k], k))
    sirali = [k for k in sirali if len(konular[k]) >= 2 or adet[k] >= 3][:limit]
    if not sirali:
        return []
    tepe = max(len(konular[k]) * 2 + adet[k] for k in sirali)
    sonuc = [{"kelime": max(yazim[k], key=yazim[k].get), "konu": len(konular[k]), "adet": adet[k],
              "boyut": 1 + round(3 * (len(konular[k]) * 2 + adet[k]) / tepe) if tepe else 1} for k in sirali]
    return sorted(sonuc, key=lambda s: ontoloji.tr_sirala(s["kelime"]))


# --- Kategori nabzı ---

def kategori_nabzi(db, gun=7):
    """Her ana kategori için bu haftanın ve geçen haftanın mesaj sayısı ve son 7 günün günlük dağılımı."""
    an = zaman.simdi()
    gunler = [(an - timedelta(days=i)).date().isoformat() for i in range(gun - 1, -1, -1)]
    iki_hafta = _once(days=2 * gun)
    bu_hafta = _once(days=gun)
    koklar = {}
    for r in db.execute("""SELECT k.kategori_id, m.olusturma FROM mesajlar m JOIN konular k ON k.id = m.konu_id
                           WHERE k.silindi = 0 AND m.yazar_id IS NOT NULL AND m.tip NOT IN ('YZ', 'SISTEM')
                             AND m.olusturma >= ?""", (iki_hafta,)):
        kok = ontoloji.atalar(db, "kategoriler", r["kategori_id"])[0]
        d = koklar.setdefault(kok, {"bu": 0, "gecen": 0, "gunluk": {}})
        if r["olusturma"] >= bu_hafta:
            d["bu"] += 1
            d["gunluk"][r["olusturma"][:10]] = d["gunluk"].get(r["olusturma"][:10], 0) + 1
        else:
            d["gecen"] += 1
    acik = {}
    for r in db.execute("SELECT kategori_id FROM konular WHERE silindi = 0 AND durum IN ('TARTISMA', 'OYLAMA')"):
        kok = ontoloji.atalar(db, "kategoriler", r["kategori_id"])[0]
        acik[kok] = acik.get(kok, 0) + 1
    sonuc = []
    for k in db.execute("SELECT id, ad FROM kategoriler WHERE ust_id IS NULL").fetchall():
        d = koklar.get(k["id"], {"bu": 0, "gecen": 0, "gunluk": {}})
        seri = [d["gunluk"].get(g, 0) for g in gunler]
        degisim = None if not d["gecen"] else round(100 * (d["bu"] - d["gecen"]) / d["gecen"])
        sonuc.append({"id": k["id"], "ad": k["ad"], "renk": ontoloji.kategori_rengi(db, k["id"]), "bu": d["bu"],
                      "gecen": d["gecen"], "degisim": degisim, "yeni": not d["gecen"] and d["bu"] > 0,
                      "seri": seri, "acik": acik.get(k["id"], 0)})
    sonuc.sort(key=lambda s: (-s["bu"], -s["acik"], ontoloji.tr_sirala(s["ad"])))
    tepe = max([max(s["seri"]) for s in sonuc] + [1])
    for s in sonuc:
        s["cizgi"] = " ".join(f"{i * 10},{round(22 - 20 * v / tepe, 1)}" for i, v in enumerate(s["seri"]))
    return sonuc


# --- Yakında bitenler, kararlar, üyeler, akış ---

def yakinda_bitenler(db, limit=4):
    """Süresi en yakın dolacak oylamalar ve oylamaya geçecek tartışmalar."""
    liste = [{"tur": "OYLAMA", "baslik": oylama.teklif_basligi(db, t), "baglanti": f"/oylama/{t['id']}",
              "bitis": t["bitis"], "tip": t["tip"]}
             for t in db.execute("SELECT * FROM teklifler WHERE durum = 'ACIK' ORDER BY bitis LIMIT ?", (limit,))]
    liste += [{"tur": "TARTISMA", "baslik": k["baslik"], "baglanti": f"/konu/{k['id']}", "bitis": k["tartisma_bitis"],
               "tip": None}
              for k in db.execute("SELECT id, baslik, tartisma_bitis FROM konular WHERE durum = 'TARTISMA' AND silindi = 0 "
                                  "AND tartisma_bitis IS NOT NULL ORDER BY tartisma_bitis LIMIT ?", (limit,))]
    return sorted(liste, key=lambda x: x["bitis"])[:limit]


def son_kararlar(db, limit=3):
    return db.execute("""SELECT kr.*, k.baslik, k.kategori_id FROM kararlar kr JOIN konular k ON k.id = kr.konu_id
                         WHERE kr.durum = 'KESIN' AND k.silindi = 0 ORDER BY kr.id DESC LIMIT ?""", (limit,)).fetchall()


def etkin_uyeler(db, gun=7, limit=5):
    esik = _once(days=gun)
    return db.execute(
        """SELECT u.takma_ad,
                  (SELECT COUNT(*) FROM mesajlar m WHERE m.yazar_id = u.id AND m.tip != 'YZ' AND m.olusturma >= :e) AS mesaj,
                  (SELECT COUNT(*) FROM mesajlar m WHERE m.yazar_id = u.id AND m.tip = 'FIKIR' AND m.olusturma >= :e) AS fikir,
                  (SELECT COUNT(*) FROM oylar o WHERE o.kullanici_id = u.id AND o.zaman >= :e) AS oy
           FROM kullanicilar u WHERE u.yz_mi = 0 ORDER BY (mesaj + oy) DESC, u.takma_ad LIMIT :n""",
        {"e": esik, "n": limit}).fetchall()


AKIS_EYLEMLERI = ("KONU", "SONUC", "KARAR", "UZMANLIK", "YENI_KATEGORI", "TEKLIF", "KAYIT")


def canli_akis(db, limit=8):
    return db.execute(
        f"""SELECT g.*, k.takma_ad, k.yz_mi FROM gunluk g LEFT JOIN kullanicilar k ON k.id = g.kullanici_id
            WHERE g.eylem IN ({','.join('?' * len(AKIS_EYLEMLERI))}) ORDER BY g.zaman DESC, g.id DESC LIMIT ?""",
        AKIS_EYLEMLERI + (limit,)).fetchall()


def son_24_saat(db):
    esik = _once(hours=24)
    tek = lambda q: db.execute(q, (esik,)).fetchone()[0]  # noqa: E731
    return {
        "mesaj": tek("SELECT COUNT(*) FROM mesajlar WHERE yazar_id IS NOT NULL AND tip NOT IN ('YZ', 'SISTEM') "
                     "AND olusturma >= ?"),
        "fikir": tek("SELECT COUNT(*) FROM mesajlar WHERE tip = 'FIKIR' AND olusturma >= ?"),
        "oy": tek("SELECT COUNT(*) FROM oylar WHERE zaman >= ?"),
        "konu": tek("SELECT COUNT(*) FROM konular WHERE silindi = 0 AND olusturma >= ?"),
        "uye": tek("SELECT COUNT(DISTINCT yazar_id) FROM mesajlar WHERE tip NOT IN ('YZ', 'SISTEM') AND yazar_id IS NOT NULL "
                   "AND olusturma >= ?"),
    }


def yan_panel(db):
    """Konular sayfasının sağ sütunu."""
    trend, saat = trend_konular(db, 5)
    return {"trend": trend, "trend_saat": saat, "kelimeler": anahtar_kelimeler(db, limit=10),
            "yakinda": yakinda_bitenler(db, 3), "nabiz": kategori_nabzi(db)[:5]}


def kesfet(db):
    trend, saat = trend_konular(db, 8)
    return {"trend": trend, "trend_saat": saat, "kelimeler": anahtar_kelimeler(db, limit=20),
            "nabiz": kategori_nabzi(db), "yakinda": yakinda_bitenler(db, 6), "kararlar": son_kararlar(db, 4),
            "uyeler": etkin_uyeler(db), "akis": canli_akis(db, 10), "son24": son_24_saat(db),
            "genel_kategori": ayarlar.GENEL_KATEGORI,
            "acik_oylama": db.execute("SELECT COUNT(*) FROM teklifler WHERE durum = 'ACIK'").fetchone()[0]}
