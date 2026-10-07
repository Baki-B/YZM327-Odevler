"""Yönetim paneli: pano sayıları, yetki verme, askıya alma, kategoriler ve site ayarları.

Yönetici yalnızca siteyi yönetir: içerik silemez, oylama sonucunu ya da süresini değiştiremez, uzman atayamaz.
Buradaki her işlem şeffaflık günlüğüne, yetki ve askı işlemleri ayrıca kayıt defterine yazılır.
"""
import os
import sqlite3
import tempfile
from datetime import timedelta

from . import ayarlar, bildirimler, defter, gunluk, kategoriler, ontoloji, sikayetler, zaman
from .hatalar import KuralHatasi, tamsayi

# Yönetim işlemlerinin günlükteki eylem adları (panodaki "son yönetim işlemleri" bunları süzer)
YONETIM_EYLEMLERI = ("YETKI", "ASKI", "ASKI_BITTI", "KATEGORI", "SITE_AYARI", "YZ", "SURE", "SIKAYET",
                     "TOPLU_BILDIRIM")

EYLEM_ADLARI = {
    "ADRES": "Adres", "ASKI": "Askı", "ASKI_BITTI": "Askı kalktı", "UZMANLIK": "Uzmanlık", "KONU": "Konu",
    "KONU_DURUM": "Konu durumu", "DEVIR": "Oy devri", "DEVIR_GERI": "Devir geri alındı",
    "ERTELEME": "Erteleme", "KARAR": "Karar", "KATEGORI": "Kategori", "YENI_KATEGORI": "Yeni kategori", "KAYIT": "Yeni üye",
    "KONU_DUZENLEME": "Konu düzenleme", "KONU_KALDIRMA": "Konu kaldırma", "MESAJ": "Mesaj", "RAPOR": "Rapor",
    "SERH": "Şerh", "SIFRE": "Şifre", "SIKAYET": "Şikayet", "TOPLU_BILDIRIM": "Toplu bildirim", "SITE_AYARI": "Site ayarı", "SONUC": "Sonuç", "SURE": "Süre",
    "TASARI": "Öneri", "TEKLIF": "Oylama", "YETKI": "Yetki", "YONETMELIK": "Yönetmelik", "YZ": "Yapay zeka",
}

SITE_AYARLARI = {
    "duyuru": "",          # boş değilse her sayfanın üstünde görünür
    "kayit_acik": "1",     # "0" ise yeni üyelik alınmaz
}
MAX_ASKI_GUN = 365


# --- Site ayarları ---

def site_ayari(db, anahtar):
    r = db.execute("SELECT deger FROM site_ayarlari WHERE anahtar = ?", (anahtar,)).fetchone()
    return r["deger"] if r else SITE_AYARLARI[anahtar]


def site_ayari_yaz(db, yonetici, anahtar, deger):
    if anahtar not in SITE_AYARLARI:
        raise KuralHatasi("Bilinmeyen ayar.")
    deger = (deger or "").strip()
    if anahtar == "duyuru" and len(deger) > 300:
        raise KuralHatasi("Duyuru en fazla 300 karakter olabilir.")
    if anahtar == "kayit_acik":
        deger = "1" if deger == "1" else "0"
    if deger == site_ayari(db, anahtar):
        return
    db.execute("INSERT INTO site_ayarlari (anahtar, deger) VALUES (?, ?) "
               "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger", (anahtar, deger))
    metin = {"duyuru": f"Site duyurusu {'güncellendi' if deger else 'kaldırıldı'}",
             "kayit_acik": f"Yeni üyelik {'açıldı' if deger == '1' else 'kapatıldı'}"}[anahtar]
    gunluk.kaydet(db, yonetici["id"], "SITE_AYARI", metin)


# --- Yetki ve askı ---

def askida_mi(kullanici):
    return bool(kullanici and kullanici["askida_bitis"] and kullanici["askida_bitis"] > zaman.simdi_metin())


def _hedef(db, kullanici_id):
    k = db.execute("SELECT * FROM kullanicilar WHERE id = ?", (kullanici_id,)).fetchone()
    if not k:
        raise KuralHatasi("Üye bulunamadı.")
    return k


def yetki_ver(db, yonetici, kullanici_id, yonetici_olsun):
    k = _hedef(db, kullanici_id)
    if k["id"] == yonetici["id"]:
        raise KuralHatasi("Kendi yetkini değiştiremezsin; başka bir yönetici değiştirebilir.")
    if yonetici_olsun and k["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları yönetici olamaz.")
    if yonetici_olsun and askida_mi(k):
        raise KuralHatasi("Askıdaki bir üye yönetici yapılamaz.")
    if bool(k["yonetici_mi"]) == bool(yonetici_olsun):
        return
    db.execute("UPDATE kullanicilar SET yonetici_mi = ? WHERE id = ?", (int(bool(yonetici_olsun)), k["id"]))
    metin = f"@{k['takma_ad']} {'yönetici yapıldı' if yonetici_olsun else 'yöneticilikten çıkarıldı'}"
    gunluk.kaydet(db, yonetici["id"], "YETKI", metin)
    defter.ekle(db, "YONETIM", {"islem": "YETKI", "yurttas": k["takma_ad"], "yonetici": bool(yonetici_olsun)})
    bildirimler.gonder(db, k["id"], "Artık yöneticisin. Yönetim paneline hesap menünden ulaşabilirsin."
                       if yonetici_olsun else "Yöneticilik yetkin kaldırıldı.", "/yonetim" if yonetici_olsun else "/profil")


def askiya_al(db, yonetici, kullanici_id, gun, neden):
    k = _hedef(db, kullanici_id)
    if k["id"] == yonetici["id"]:
        raise KuralHatasi("Kendini askıya alamazsın.")
    if k["yonetici_mi"]:
        raise KuralHatasi("Bir yöneticiyi askıya almadan önce yöneticilik yetkisini kaldırmalısın.")
    if k["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları askıya alınamaz.")
    try:
        gun = int(gun)
    except (TypeError, ValueError):
        raise KuralHatasi("Süreyi gün olarak gir.")
    if not 1 <= gun <= MAX_ASKI_GUN:
        raise KuralHatasi(f"Süre 1 ile {MAX_ASKI_GUN} gün arasında olmalı.")
    neden = (neden or "").strip()
    if len(neden) < 10:
        raise KuralHatasi("Askıya alma nedenini yaz (en az 10 karakter). Neden şeffaflık günlüğünde görünür.")
    bitis = zaman.simdi() + timedelta(days=gun)
    db.execute("UPDATE kullanicilar SET askida_bitis = ?, askida_neden = ? WHERE id = ?",
               (zaman.metin(bitis), neden, k["id"]))
    gunluk.kaydet(db, yonetici["id"], "ASKI", f"@{k['takma_ad']} {gun} gün askıya alındı: {neden}")
    defter.ekle(db, "YONETIM", {"islem": "ASKI", "yurttas": k["takma_ad"], "gun": gun})
    bildirimler.gonder(db, k["id"], f"Hesabın {bitis:%d.%m.%Y %H:%M} tarihine kadar askıya alındı. Neden: {neden}",
                       "/profil")
    return bitis


def askiyi_kaldir(db, yonetici, kullanici_id):
    k = _hedef(db, kullanici_id)
    if not askida_mi(k):
        raise KuralHatasi("Bu üye askıda değil.")
    db.execute("UPDATE kullanicilar SET askida_bitis = NULL, askida_neden = NULL WHERE id = ?", (k["id"],))
    gunluk.kaydet(db, yonetici["id"], "ASKI_BITTI", f"@{k['takma_ad']} için askı kaldırıldı")
    defter.ekle(db, "YONETIM", {"islem": "ASKI_BITTI", "yurttas": k["takma_ad"]})
    bildirimler.gonder(db, k["id"], "Hesabının askısı kaldırıldı.", "/profil")


# --- Üyeler ---

UYE_FILTRELERI = {"": "Tümü", "yonetici": "Yöneticiler", "uzman": "Uzmanlar", "yz": "Yapay zeka",
                  "askida": "Askıdakiler"}


def uyeler(db, aranan="", filtre=""):
    simdi = zaman.simdi_metin()
    sorgu = """SELECT k.*, (SELECT COUNT(*) FROM mesajlar m WHERE m.yazar_id = k.id) AS mesaj_sayisi,
                      (SELECT COUNT(*) FROM oylar o WHERE o.kullanici_id = k.id) AS oy_sayisi,
                      (SELECT COUNT(*) FROM uzmanliklar u WHERE u.kullanici_id = k.id
                         AND u.baslangic <= :simdi AND u.bitis > :simdi) AS uzmanlik
               FROM kullanicilar k WHERE 1 = 1 """
    p = {"simdi": simdi}
    if aranan:
        sorgu += "AND (k.takma_ad LIKE :q OR k.ad_soyad LIKE :q) "
        p["q"] = f"%{aranan}%"
    sorgu += {"yonetici": "AND k.yonetici_mi = 1 ", "yz": "AND k.yz_mi = 1 ",
              "askida": "AND k.askida_bitis > :simdi ",
              "uzman": "AND EXISTS (SELECT 1 FROM uzmanliklar u WHERE u.kullanici_id = k.id "
                           "AND u.baslangic <= :simdi AND u.bitis > :simdi) "}.get(filtre, "")
    return db.execute(sorgu + "ORDER BY k.yonetici_mi DESC, k.yz_mi, k.takma_ad COLLATE NOCASE", p).fetchall()


def uye_ozeti(db, kullanici_id):
    tek = lambda q: db.execute(q, (kullanici_id,)).fetchone()[0]  # noqa: E731
    return {
        "mesaj": tek("SELECT COUNT(*) FROM mesajlar WHERE yazar_id = ?"),
        "gizlenen": tek("SELECT COUNT(*) FROM mesajlar WHERE yazar_id = ? AND gizli = 1"),
        "oy": tek("SELECT COUNT(*) FROM oylar WHERE kullanici_id = ?"),
        "konu": tek("SELECT COUNT(*) FROM konular WHERE sahip_id = ?"),
        "fikir": tek("SELECT COUNT(*) FROM mesajlar WHERE yazar_id = ? AND tip = 'FIKIR'"),
    }


def uye_gunlugu(db, kullanici_id, limit=15):
    return db.execute("SELECT * FROM gunluk WHERE kullanici_id = ? ORDER BY id DESC LIMIT ?",
                      (kullanici_id, limit)).fetchall()


# --- Kategoriler ---

RENK_SECENEKLERI = [("", "Otomatik")] + [(ayarlar.YESIL[t], f"Yeşil {t}") for t in (200, 400, 600, 800)] + \
                   [(ayarlar.GRI[t], f"Gri {t}") for t in (300, 500, 700)]


def kategori_agaci(db):
    sayilar = {r["kategori_id"]: r["n"] for r in
               db.execute("SELECT kategori_id, COUNT(*) AS n FROM konular WHERE silindi = 0 GROUP BY kategori_id")}
    tum = db.execute("SELECT * FROM kategoriler ORDER BY id").fetchall()
    koklar = [dict(k) for k in tum if k["ust_id"] is None]
    for kok in koklar:
        kok["renk_goster"] = ontoloji.kategori_rengi(db, kok["id"])
        kok["altlar"] = [dict(a, sayi=sayilar.get(a["id"], 0)) for a in tum if a["ust_id"] == kok["id"]]
        kok["sayi"] = sayilar.get(kok["id"], 0) + sum(a["sayi"] for a in kok["altlar"])
    return koklar


def _renk(renk):
    renk = (renk or "").strip()
    if renk and renk not in {r for r, _ in RENK_SECENEKLERI}:
        raise KuralHatasi("Renk, sitenin paletinden seçilmeli.")
    return renk or None


def kategori_ekle(db, yonetici, ad, ust_id=None, renk=None):
    ad = kategoriler.kategori_adi(ad)
    ust = kategoriler.ust_kategori(db, ust_id)      # topluluk önerisiyle aynı kural (ör. Genel'in alt kategorisi olmaz)
    ust_id = ust["id"] if ust else None
    if kategoriler.kardes_var_mi(db, ad, ust_id):
        raise KuralHatasi("Bu adda bir kategori zaten var.")
    yeni = db.execute("INSERT INTO kategoriler (ad, ust_id, renk, kaynak, olusturma) VALUES (?, ?, ?, 'YONETICI', ?)",
                      (ad, ust_id, None if ust_id else _renk(renk), zaman.simdi_metin())).lastrowid
    db.onbellek.clear()
    gunluk.kaydet(db, yonetici["id"], "KATEGORI", f"Kategori eklendi: {ontoloji.yol_metni(db, 'kategoriler', yeni)}")
    return yeni


def kategori_duzenle(db, yonetici, kategori_id, ad, renk=None):
    d = ontoloji.dugum(db, "kategoriler", tamsayi(kategori_id, "Kategori bulunamadı."))
    if not d:
        raise KuralHatasi("Kategori bulunamadı.")
    ad = kategoriler.kategori_adi(ad)
    if d["ad"] == ayarlar.GENEL_KATEGORI and ad != d["ad"]:
        raise KuralHatasi("Genel kategorinin adı değiştirilemez; her konuya açık olması bu ada bağlıdır.")
    if kategoriler.kardes_var_mi(db, ad, d["ust_id"], haric_id=d["id"]):
        raise KuralHatasi("Bu adda bir kategori zaten var.")
    eski = ontoloji.yol_metni(db, "kategoriler", d["id"])
    db.execute("UPDATE kategoriler SET ad = ?, renk = ? WHERE id = ?",
               (ad, _renk(renk) if d["ust_id"] is None else None, d["id"]))
    db.onbellek.clear()
    yeni = ontoloji.yol_metni(db, "kategoriler", d["id"])
    if yeni != eski:
        gunluk.kaydet(db, yonetici["id"], "KATEGORI", f"Kategori adı değişti: {eski} → {yeni}")
    else:
        gunluk.kaydet(db, yonetici["id"], "KATEGORI", f"{yeni} kategorisinin rengi değişti")


# --- Pano ---

def pano(db):
    an = zaman.simdi()
    once = lambda gun: zaman.metin(an - timedelta(days=gun))  # noqa: E731
    tek = lambda q, *p: db.execute(q, p).fetchone()[0]  # noqa: E731
    simdi = zaman.metin(an)
    sayilar = {
        "uye": tek("SELECT COUNT(*) FROM kullanicilar WHERE yz_mi = 0"),
        "yeni_uye": tek("SELECT COUNT(*) FROM kullanicilar WHERE yz_mi = 0 AND olusturma >= ?", once(7)),
        "aktif_uye": tek("SELECT COUNT(*) FROM kullanicilar WHERE yz_mi = 0 AND son_giris >= ?", once(7)),
        "yonetici": tek("SELECT COUNT(*) FROM kullanicilar WHERE yonetici_mi = 1"),
        "askida": tek("SELECT COUNT(*) FROM kullanicilar WHERE askida_bitis > ?", simdi),
        "acik_konu": tek("SELECT COUNT(*) FROM konular WHERE silindi = 0 AND durum IN ('TARTISMA', 'OYLAMA')"),
        "tartisma": tek("SELECT COUNT(*) FROM konular WHERE silindi = 0 AND durum = 'TARTISMA'"),
        "acik_oylama": tek("SELECT COUNT(*) FROM teklifler WHERE durum = 'ACIK'"),
        "karar": tek("SELECT COUNT(*) FROM kararlar WHERE durum = 'KESIN'"),
        "mesaj_hafta": tek("SELECT COUNT(*) FROM mesajlar WHERE yazar_id IS NOT NULL AND olusturma >= ?", once(7)),
        "oy_hafta": tek("SELECT COUNT(*) FROM oylar WHERE zaman >= ?", once(7)),
        "uzman": tek("SELECT COUNT(DISTINCT kullanici_id) FROM uzmanliklar WHERE baslangic <= ? AND bitis > ?",
                     simdi, simdi),
    }

    # Son 14 günün etkinliği: gün başına mesaj ve oy
    gunler = [(an - timedelta(days=i)).date() for i in range(13, -1, -1)]
    say = lambda q: {r[0]: r[1] for r in db.execute(q, (gunler[0].isoformat(),))}  # noqa: E731
    mesaj = say("SELECT substr(olusturma, 1, 10), COUNT(*) FROM mesajlar WHERE yazar_id IS NOT NULL "
                "AND olusturma >= ? GROUP BY 1")
    oy = say("SELECT substr(zaman, 1, 10), COUNT(*) FROM oylar WHERE zaman >= ? GROUP BY 1")
    etkinlik = [{"gun": g, "mesaj": mesaj.get(g.isoformat(), 0), "oy": oy.get(g.isoformat(), 0)} for g in gunler]
    tepe = max([e["mesaj"] + e["oy"] for e in etkinlik] + [1])

    durumlar = [(ayarlar.KONU_DURUMLARI[d], n) for d, n in db.execute(
        "SELECT durum, COUNT(*) FROM konular WHERE silindi = 0 GROUP BY durum ORDER BY COUNT(*) DESC")]

    # İlgilenilmesi gerekenler
    yakinda = zaman.metin(an + timedelta(hours=24))
    dikkat = {
        "biten_oylamalar": db.execute("SELECT * FROM teklifler WHERE durum = 'ACIK' AND bitis <= ? ORDER BY bitis",
                                      (yakinda,)).fetchall(),
        "biten_tartismalar": db.execute("SELECT id, baslik, tartisma_bitis FROM konular WHERE durum = 'TARTISMA' "
                                        "AND silindi = 0 AND tartisma_bitis <= ? ORDER BY tartisma_bitis",
                                        (yakinda,)).fetchall(),
        "biten_uzmanlik": db.execute(
            """SELECT u.*, k.takma_ad FROM uzmanliklar u JOIN kullanicilar k ON k.id = u.kullanici_id
               WHERE u.bitis > ? AND u.bitis <= ? ORDER BY u.bitis""",
            (simdi, zaman.metin(an + timedelta(days=30)))).fetchall(),
        "defter": defter.durum(db.defter_klasoru),
        "sikayet": sikayetler.acik_sayisi(db),
    }
    son_islemler = db.execute(
        f"""SELECT g.*, k.takma_ad FROM gunluk g LEFT JOIN kullanicilar k ON k.id = g.kullanici_id
            WHERE g.eylem IN ({','.join('?' * len(YONETIM_EYLEMLERI))}) ORDER BY g.zaman DESC, g.id DESC LIMIT 8""",
        YONETIM_EYLEMLERI).fetchall()
    return {"sayilar": sayilar, "etkinlik": etkinlik, "tepe": tepe, "durumlar": durumlar,
            "durum_tepe": max([n for _, n in durumlar] + [1]), "dikkat": dikkat, "son_islemler": son_islemler}


# --- Toplu bildirim ---

BILDIRIM_HEDEFLERI = {"HEPSI": "Bütün üyeler", "KONUM": "Bir il ya da ilçedeki üyeler",
                      "UZMAN": "Bir alanın uzmanları", "YONETICI": "Yöneticiler"}


def toplu_bildirim_alicilari(db, hedef, konum_id=None, kategori_id=None):
    simdi = zaman.simdi_metin()
    insanlar = [dict(r) for r in db.execute("SELECT id, konum_id, yonetici_mi FROM kullanicilar WHERE yz_mi = 0")]
    if hedef == "HEPSI":
        return [k["id"] for k in insanlar]
    if hedef == "YONETICI":
        return [k["id"] for k in insanlar if k["yonetici_mi"]]
    if hedef == "KONUM":
        konum_id = tamsayi(konum_id, "İl ya da ilçe seç.")
        if not konum_id or not ontoloji.dugum(db, "konumlar", konum_id):
            raise KuralHatasi("İl ya da ilçe seç.")
        return [k["id"] for k in insanlar
                if k["konum_id"] and ontoloji.altinda_mi(db, "konumlar", k["konum_id"], konum_id)]
    if hedef == "UZMAN":
        kategori_id = tamsayi(kategori_id, "Alan seç.")
        if not kategori_id or not ontoloji.dugum(db, "kategoriler", kategori_id):
            raise KuralHatasi("Alan seç.")
        alanlar = ontoloji.alt_agac(db, "kategoriler", kategori_id)
        return sorted({r["kullanici_id"] for r in db.execute(
            "SELECT kullanici_id, kategori_id FROM uzmanliklar WHERE baslangic <= ? AND bitis > ?", (simdi, simdi))
            if r["kategori_id"] in alanlar})
    raise KuralHatasi("Kime gönderileceğini seç.")


def toplu_bildirim(db, yonetici, hedef, metin, baglanti="", konum_id=None, kategori_id=None):
    metin = " ".join((metin or "").split())
    if not 5 <= len(metin) <= 300:
        raise KuralHatasi("Bildirim metni 5–300 karakter olmalı.")
    baglanti = (baglanti or "").strip()
    if baglanti and (not baglanti.startswith("/") or baglanti.startswith("//")):
        raise KuralHatasi("Bağlantı sitenin içinden olmalı ve / ile başlamalı (ör. /konu/3).")
    alicilar = toplu_bildirim_alicilari(db, hedef, konum_id, kategori_id)
    if not alicilar:
        raise KuralHatasi("Seçtiğin grupta hiç üye yok.")
    for kid in alicilar:
        bildirimler.gonder(db, kid, metin, baglanti or "/bildirimler")
    kime = BILDIRIM_HEDEFLERI[hedef].lower()
    if hedef == "KONUM":
        kime = f"{ontoloji.yol_metni(db, 'konumlar', tamsayi(konum_id))} üyeleri"
    elif hedef == "UZMAN":
        kime = f"{ontoloji.yol_metni(db, 'kategoriler', tamsayi(kategori_id))} uzmanları"
    gunluk.kaydet(db, yonetici["id"], "TOPLU_BILDIRIM", f"{len(alicilar)} kişiye ({kime}) bildirim gönderildi: {metin[:80]}")
    return len(alicilar)


# --- Günlük ---

def gunluk_kayitlari(db, eylem="", takma_ad="", limit=1000):
    sorgu = ("SELECT g.*, k.takma_ad, k.yz_mi FROM gunluk g LEFT JOIN kullanicilar k ON k.id = g.kullanici_id "
             "WHERE 1 = 1 ")
    p = []
    if eylem == "YONETIM":
        sorgu += f"AND g.eylem IN ({','.join('?' * len(YONETIM_EYLEMLERI))}) "
        p += YONETIM_EYLEMLERI
    elif eylem:
        sorgu += "AND g.eylem = ? "
        p.append(eylem)
    if takma_ad:
        sorgu += "AND k.takma_ad = ? "
        p.append(takma_ad.lstrip("@"))
    return db.execute(sorgu + "ORDER BY g.zaman DESC, g.id DESC LIMIT ?", p + [limit]).fetchall()


def gunluk_eylemleri(db):
    return [r[0] for r in db.execute("SELECT DISTINCT eylem FROM gunluk ORDER BY eylem")]


# --- Yedek ---

def yedek_al(db):
    """Veritabanının kaydedilmiş hâlinin tutarlı bir kopyasını bayt olarak döndürür (sunucu çalışırken de güvenlidir).
    Açık işlemi olan bağlantıyı kilitlememek için kopya ayrı bir okuma bağlantısından alınır."""
    fd, yol = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        kaynak, hedef = sqlite3.connect(db.yol), sqlite3.connect(yol)
        try:
            kaynak.backup(hedef)
        finally:
            kaynak.close()
            hedef.close()
        with open(yol, "rb") as f:
            return f.read()
    finally:
        os.remove(yol)
