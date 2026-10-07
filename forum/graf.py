"""Üyeler grafı.

Düğümler üyelerdir. Kenarlar:
  DEVIR     veren → alan         (oy devri)
  YANIT     yanıtlayan → yazar   (tartışma etkileşimi)
  TAKIP     takipçi → takip edilen
  BENZERLIK iki üyenin sonuçlanmış oylamalarda aynı yönde oy verme oranı (yönsüz). YALNIZCA İÇ HESAPTA kullanılır:
            ikili benzerlik dışarı verilirse kendi oyunu bilen biri komşusunun gizli oyunu çıkarabilir (T4 gizli oy).
            Dışarıya yalnızca en az GRUP_EN_AZ kişilik görüş grupları gösterilir (k-anonimlik).

Graf üzerinde hesaplananlar:
  * Etki puanı (PageRank)
  * Oy gücü dağılımı ve Gini katsayısı (güç yoğunlaşması uyarısı)
  * Görüş grupları (oy benzerliği grafında etiket yayılımı)
"""
from collections import defaultdict

from . import ayarlar, bildirimler, yonetmelik, zaman
from .hatalar import KuralHatasi

# Görüş grupları da paletten renk alır: yeşilin ve grinin birbirinden kolay ayrılan tonları
GRUP_RENKLERI = [ayarlar.YESIL[600], ayarlar.GRI[500], ayarlar.YESIL[300], ayarlar.YESIL[800],
                 ayarlar.GRI[300], ayarlar.YESIL[400], ayarlar.YESIL[200], ayarlar.GRI[700]]
GRUPSUZ_RENK = ayarlar.TAS_BEYAZI[50]
KENAR_AGIRLIKLARI = {"DEVIR": 2.0, "YANIT": 1.0, "TAKIP": 0.5}
GRUP_EN_AZ = 3        # bundan küçük görüş grubu gösterilmez: iki kişilik grup, iki kişinin aynı oyu verdiğini ele verir


# --- Takip (sosyal kenar) ---

def takip_et(db, kullanici, hedef_id):
    if hedef_id == kullanici["id"]:
        raise KuralHatasi("Kendini takip edemezsin.")
    hedef = db.execute("SELECT * FROM kullanicilar WHERE id = ?", (hedef_id,)).fetchone()
    if not hedef:
        raise KuralHatasi("Kullanıcı bulunamadı.")
    if takip_ediyor_mu(db, kullanici["id"], hedef_id):
        db.execute("DELETE FROM takipler WHERE takip_eden_id = ? AND takip_edilen_id = ?", (kullanici["id"], hedef_id))
        return False
    db.execute("INSERT INTO takipler (takip_eden_id, takip_edilen_id, olusturma) VALUES (?, ?, ?)",
               (kullanici["id"], hedef_id, zaman.simdi_metin()))
    bildirimler.gonder(db, hedef_id, f"@{kullanici['takma_ad']} seni takip etmeye başladı.",
                       f"/kullanici/{kullanici['takma_ad']}")
    return True


def takip_ediyor_mu(db, eden_id, edilen_id):
    return bool(db.execute("SELECT 1 FROM takipler WHERE takip_eden_id = ? AND takip_edilen_id = ?",
                           (eden_id, edilen_id)).fetchone())


def takip_sayilari(db, kullanici_id):
    takipci = db.execute("SELECT COUNT(*) FROM takipler WHERE takip_edilen_id = ?", (kullanici_id,)).fetchone()[0]
    takip = db.execute("SELECT COUNT(*) FROM takipler WHERE takip_eden_id = ?", (kullanici_id,)).fetchone()[0]
    return takipci, takip


# --- Kenarlar ---

def kenarlar(db):
    """[(kaynak, hedef, tür, ağırlık)] — yönlü kenarlar (benzerlik hariç)."""
    liste = []
    for r in db.execute("SELECT veren_id, alan_id, COUNT(*) n FROM devirler GROUP BY veren_id, alan_id"):
        liste.append((r["veren_id"], r["alan_id"], "DEVIR", r["n"]))
    for r in db.execute("""SELECT y.yazar_id k, u.yazar_id h, COUNT(*) n FROM mesajlar y
                           JOIN mesajlar u ON u.id = y.ust_mesaj_id
                           WHERE y.yazar_id IS NOT NULL AND u.yazar_id IS NOT NULL AND y.yazar_id != u.yazar_id
                           GROUP BY y.yazar_id, u.yazar_id"""):
        liste.append((r["k"], r["h"], "YANIT", r["n"]))
    for r in db.execute("SELECT takip_eden_id, takip_edilen_id FROM takipler"):
        liste.append((r["takip_eden_id"], r["takip_edilen_id"], "TAKIP", 1))
    return liste


def cekismeli_oylamalar(db, tavan=0.8):
    """Görüş ayrılığını gösteren oylamalar: en az 3 oy, önde giden seçenek oyların %80'inden azı.
    Neredeyse oybirliğiyle geçen oylamalar kimin kiminle aynı düşündüğünü göstermez."""
    dagilim = defaultdict(lambda: defaultdict(int))
    for r in db.execute("""SELECT o.teklif_id, o.secim FROM oylar o JOIN teklifler t ON t.id = o.teklif_id
                           WHERE t.durum != 'ACIK' AND o.secim != 'CEKIMSER'"""):
        dagilim[r["teklif_id"]][r["secim"]] += 1
    return {t for t, d in dagilim.items() if sum(d.values()) >= 3 and max(d.values()) / sum(d.values()) < tavan}


def oy_benzerlikleri(db, en_az_ortak=2, esik=0.6):
    """{(a, b): benzerlik} — çekişmeli oylamalarda aynı yönde oy verme oranı (çekimserler hariç)."""
    cekismeli = cekismeli_oylamalar(db)
    oylar = defaultdict(dict)
    for r in db.execute("""SELECT o.kullanici_id, o.teklif_id, o.secim FROM oylar o
                           JOIN teklifler t ON t.id = o.teklif_id
                           WHERE t.durum != 'ACIK' AND o.secim != 'CEKIMSER'"""):
        if r["teklif_id"] in cekismeli:
            oylar[r["kullanici_id"]][r["teklif_id"]] = r["secim"]
    kisiler = sorted(oylar)
    sonuc = {}
    for i, a in enumerate(kisiler):
        for b in kisiler[i + 1:]:
            ortak = oylar[a].keys() & oylar[b].keys()
            if len(ortak) < en_az_ortak:
                continue
            oran = sum(1 for t in ortak if oylar[a][t] == oylar[b][t]) / len(ortak)
            if oran >= esik:
                sonuc[(a, b)] = oran
    return sonuc


# --- Görüş grupları ---

def gorus_gruplari(db):
    """Oy benzerliği grafında etiket yayılımıyla bulunan gruplar (en az GRUP_EN_AZ üyeli)."""
    if "gruplar" in db.onbellek:
        return db.onbellek["gruplar"]
    benzerlik = oy_benzerlikleri(db)
    komsular = defaultdict(dict)
    for (a, b), w in benzerlik.items():
        komsular[a][b] = w
        komsular[b][a] = w
    etiket = {k: k for k in komsular}
    for _ in range(20):
        degisti = False
        for k in sorted(komsular):
            puanlar = defaultdict(float)
            for n, w in komsular[k].items():
                puanlar[etiket[n]] += w
            en_iyi = min(puanlar, key=lambda e: (-puanlar[e], e))
            if puanlar[en_iyi] > puanlar.get(etiket[k], 0) and en_iyi != etiket[k]:
                etiket[k] = en_iyi
                degisti = True
        if not degisti:
            break
    kumeler = defaultdict(list)
    for k, e in etiket.items():
        kumeler[e].append(k)
    gruplar = sorted((sorted(u) for u in kumeler.values() if len(u) >= GRUP_EN_AZ), key=lambda u: (-len(u), u[0]))
    sonuc = [{"no": i, "ad": f"Grup {chr(65 + i)}", "renk": GRUP_RENKLERI[i % len(GRUP_RENKLERI)], "uyeler": u}
             for i, u in enumerate(gruplar)]
    db.onbellek["gruplar"] = sonuc
    return sonuc


# --- Etki (PageRank) ---

def etki_puanlari(db, adim=30, sonum=0.85):
    kisiler = [r["id"] for r in db.execute("SELECT id FROM kullanicilar")]
    if not kisiler:
        return {}
    cikis = defaultdict(list)
    for k, h, tur, n in kenarlar(db):
        cikis[k].append((h, KENAR_AGIRLIKLARI[tur] * n))
    n = len(kisiler)
    puan = {k: 1 / n for k in kisiler}
    for _ in range(adim):
        yeni = {k: (1 - sonum) / n for k in kisiler}
        sarkan = sum(puan[k] for k in kisiler if not cikis[k])
        for k in kisiler:
            toplam = sum(w for _, w in cikis[k])
            for h, w in cikis[k]:
                yeni[h] += sonum * puan[k] * w / toplam
        for k in kisiler:
            yeni[k] += sonum * sarkan / n
        puan = yeni
    en = max(puan.values())
    return {k: round(100 * v / en) for k, v in puan.items()}


# --- Oy gücü ve yoğunlaşma ---

def oy_gucleri(db):
    """Genel kapsamlı devirlere göre, devretmeyenler oy verdiğinde her üyenin taşıdığı oy sayısı.
    Oyunu devreden 0 taşır; zincirin sonundaki kişi kendi oyu + devredilenleri (tavanlı) taşır."""
    alan = {r["veren_id"]: r["alan_id"] for r in
            db.execute("SELECT veren_id, alan_id FROM devirler WHERE kapsam = 'GENEL'")}
    guc = {r["id"]: 1 for r in db.execute("SELECT id FROM kullanicilar")}
    tasinan = defaultdict(int)
    for veren in alan:
        guc[veren] = 0
        gorulen, x = {veren}, alan[veren]
        while x in alan and x not in gorulen:
            gorulen.add(x)
            x = alan[x]
        if x not in gorulen and x in guc:      # döngüye giren devir kaybolur
            tasinan[x] += 1
    tavan = yonetmelik.deger(db, "MAX_DEVIR")
    for x, n in tasinan.items():
        guc[x] += min(n, tavan)
    return guc


def gini(degerler):
    degerler = sorted(v for v in degerler if v >= 0)
    n, toplam = len(degerler), sum(degerler)
    if n == 0 or toplam == 0:
        return 0.0
    kumulatif = sum((i + 1) * v for i, v in enumerate(degerler))
    return (2 * kumulatif) / (n * toplam) - (n + 1) / n


# --- Görselleştirme verisi ---

def graf_verisi(db):
    etki = etki_puanlari(db)
    gruplar = gorus_gruplari(db)
    grup_of = {u: g for g in gruplar for u in g["uyeler"]}
    uzmanlar = {r["kullanici_id"] for r in db.execute("SELECT kullanici_id FROM uzmanliklar WHERE bitis > ?",
                                                      (zaman.simdi_metin(),))}
    dugumler = [{"id": r["id"], "ad": r["takma_ad"], "yz": bool(r["yz_mi"]), "uzman": r["id"] in uzmanlar,
                 "etki": etki.get(r["id"], 0), "grup": grup_of[r["id"]]["ad"] if r["id"] in grup_of else None,
                 "renk": grup_of[r["id"]]["renk"] if r["id"] in grup_of else GRUPSUZ_RENK}
                for r in db.execute("SELECT id, takma_ad, yz_mi FROM kullanicilar ORDER BY id")]
    kenar_listesi = [{"kaynak": k, "hedef": h, "tur": t, "agirlik": n} for k, h, t, n in kenarlar(db)]
    return {"dugumler": dugumler, "kenarlar": kenar_listesi}   # ikili oy benzerliği gizli oy nedeniyle verilmez


def ozet(db):
    guc = oy_gucleri(db)
    etki = etki_puanlari(db)
    adlar = {r["id"]: r["takma_ad"] for r in db.execute("SELECT id, takma_ad FROM kullanicilar")}
    g = gini(list(guc.values()))
    return {
        "gini": g,
        "yogunlasma": "düşük" if g < 0.2 else ("orta" if g < 0.4 else "yüksek"),
        "en_guclu": sorted(((adlar[k], v) for k, v in guc.items() if v > 1), key=lambda x: -x[1])[:5],
        "en_etkili": sorted(((adlar[k], v) for k, v in etki.items()), key=lambda x: -x[1])[:8],
        "gruplar": [{"ad": gr["ad"], "renk": gr["renk"], "uyeler": [adlar[u] for u in gr["uyeler"]]}
                    for gr in gorus_gruplari(db)],
    }
