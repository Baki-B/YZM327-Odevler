"""Oylama motoru. Forumdaki her karar bir "teklif" (oylama) olarak buradan geçer.

Bu modül bütün oylamaların ortak İSKELETİDİR (GoF Template Method): aç → oy ver → say → sonuçlandır.
Türe göre değişen adımlar (kimler oy verir, seçenekler, kabul ölçütü, sonuçta ne olur, başlık...) türün kendi
sınıfından istenir: teklif_turleri.tur(t["tip"]) (Strategy + Registry). Bu yüzden burada tür adı geçen dal yoktur;
yeni bir oylama türü bu dosyayı değiştirmeden eklenir.
  * Fikir oylaması (KARAR): bir konunun fikirleri turlar hâlinde yarışır. Seçim bir fikir ya da çekimserdir.
  * Evet/Hayır oylaması: mesaj gizleme, konu kaldırma, uzmanlık başvurusu, yönetmelik değişikliği, yeni kategori.

Ortak kurallar:
  * ORAN iki ayrı hesaplanır: ağırlıklı oylarda (uzman oyu ağır sayılır) ve oy veren kişi sayısında.
    İkisinden küçük olan geçerlidir; yani bir sonucun çıkması için iki ölçüde de yeterli destek gerekir.
  * Çekimser oylar toplamda sayılır: oranı düşürür, yeter sayıya katkı yapar.
  * Yeter sayı sağlanmalıdır.
  * Her oy kayıt defterine taahhüt (hash) olarak yazılır; seçmen makbuz koduyla oyunu doğrulayabilir.
"""
import json
import math
import secrets
from datetime import timedelta

from . import ayarlar, bildirimler, defter, denetim, devir, gunluk, teklif_turleri, uygunluk, yonetmelik, zaman
from .hatalar import BulunamadiHatasi, KuralHatasi
from .oy_kurallari import CEKIMSER, GIZLENEN_FIKIR, esik_saglandi

# Oylama motorunun dışarıya açtığı adlar (bazıları oy_kurallari'ndan gelir; çağıranlar oylama.X diye kullanır).
__all__ = ["CEKIMSER", "GIZLENEN_FIKIR", "esik_saglandi", "turu", "teklif_baglami", "teklif_getir", "acik_teklif",
           "teklif_ac", "secenek_ekle", "secenekler", "secim_anahtarlari", "oy_durumu", "oy_ver", "gerekli_katilim",
           "sayim", "sonuclandir", "sonuc", "teklif_basligi", "oy_sayisi", "konu_teklifleri", "kullanici_teklifleri",
           "bekleyen_oy_sayisi", "acik_teklifler"]


def turu(t):
    return teklif_turleri.tur(t["tip"])


def teklif_baglami(db, t):
    """Bu oylamada kimler, hangi ağırlıkla oy verir (türe göre)."""
    return turu(t).baglam(db, t)


def teklif_getir(db, teklif_id):
    t = db.execute("SELECT * FROM teklifler WHERE id = ?", (teklif_id,)).fetchone()
    if not t:
        raise BulunamadiHatasi("Oylama bulunamadı.")
    return t


def acik_teklif(db, tip, konu_id=None, hedef_id=None):
    sorgu, parametreler = "SELECT * FROM teklifler WHERE tip = ? AND durum = 'ACIK'", [tip]
    if konu_id is not None:
        sorgu += " AND konu_id = ?"
        parametreler.append(konu_id)
    if hedef_id is not None:
        sorgu += " AND hedef_id = ?"
        parametreler.append(hedef_id)
    return db.execute(sorgu, parametreler).fetchone()


def teklif_ac(db, tip, acan_id, konu_id=None, hedef_id=None, gerekce="", veri=None, esik=None, tur_no=1,
              secenekler=None):
    tur_ = teklif_turleri.tur(tip)
    esik = tur_.esik(db, esik)
    an = zaman.simdi()
    bitis = an + timedelta(hours=yonetmelik.deger(db, tur_.sure_parametresi(tur_no)))
    teklif_id = db.execute(
        """INSERT INTO teklifler (tip, konu_id, hedef_id, acan_id, gerekce, veri, esik, tur_no, baslangic, bitis)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (tip, konu_id, hedef_id, acan_id, gerekce, json.dumps(veri or {}, ensure_ascii=False), esik, tur_no,
         zaman.metin(an), zaman.metin(bitis)),
    ).lastrowid
    for metin, mesaj_id in secenekler or []:
        secenek_ekle(db, teklif_id, metin, mesaj_id)
    t = teklif_getir(db, teklif_id)
    gunluk.kaydet(db, acan_id, "TEKLIF", f"#{teklif_id} {tur_.ad} açıldı" + (f" ({tur_no}. tur)" if tur_.fikir_oylamasi else ""))
    defter.ekle(db, "TEKLIF", {"teklif": teklif_id, "tip": tip, "konu": konu_id, "esik": esik, "tur": tur_no})
    bildirimler.coklu_gonder(db, tur_.acilis_alicilari(db, t), f"Yeni oylama: {tur_.baslik(db, t)}",
                             f"/oylama/{teklif_id}", haric=acan_id)
    return teklif_id


def secenek_ekle(db, teklif_id, metin, mesaj_id):
    db.execute("INSERT INTO secenekler (teklif_id, mesaj_id, metin) VALUES (?, ?, ?)", (teklif_id, mesaj_id, metin))


def secenekler(db, teklif_id):
    """Fikir oylamasının seçenekleri (gizlenen fikir `gizli` işaretli ve metinsiz)."""
    return teklif_turleri.tur("KARAR").fikirler(db, {"id": teklif_id})


def secim_anahtarlari(db, teklif):
    return turu(teklif).secim_anahtarlari(db, teklif)


# --- Oy verme ---

def oy_durumu(db, teklif, kullanici):
    baglam = teklif_baglami(db, teklif)
    agirlik, aciklama = uygunluk.oy_agirligi(db, kullanici, baglam)
    durum = {"verebilir": agirlik > 0 and teklif["durum"] == "ACIK", "agirlik": agirlik,
             "aciklama": aciklama, "oy": None, "devir": None}
    if kullanici is None:
        return durum
    durum["oy"] = db.execute("SELECT * FROM oylar WHERE teklif_id = ? AND kullanici_id = ?",
                             (teklif["id"], kullanici["id"])).fetchone()
    alan_id, kapsam = devir.gecerli_devir(db, kullanici["id"], baglam)
    if alan_id:
        alan = db.execute("SELECT takma_ad FROM kullanicilar WHERE id = ?", (alan_id,)).fetchone()
        durum["devir"] = {"takma_ad": alan["takma_ad"], "kapsam": devir.KAPSAMLAR[kapsam]}
    return durum


def oy_ver(db, teklif_id, kullanici, secim, gerekce=""):
    """Oyu kaydeder ve seçmene özel makbuz kodunu döndürür. Oylama bitene kadar oy değiştirilebilir."""
    t = teklif_getir(db, teklif_id)
    if t["durum"] != "ACIK" or t["bitis"] <= zaman.simdi_metin():
        raise KuralHatasi("Bu oylama kapandı.")
    baglam = teklif_baglami(db, t)
    agirlik, aciklama = uygunluk.oy_agirligi(db, kullanici, baglam)
    if agirlik == 0:
        raise KuralHatasi(aciklama)
    turu(t).secim_dogrula(db, t, secim)
    gerekce = (gerekce or "").strip()
    if agirlik > 1 and len(gerekce) < 10:
        raise KuralHatasi(f"Uzman olarak oyun {agirlik} sayıldığı için gerekçe yazmalısın (en az 10 karakter). "
                          "Uzman oyları herkese açıktır.")
    if gerekce:
        denetim.mesaj_denetle(db, gerekce)

    makbuz = "-".join(secrets.token_hex(2).upper() for _ in range(4))
    taahhut = defter.taahhut(teklif_id, secim, makbuz)
    an = zaman.simdi_metin()
    # Koşullu yazma: kontrol ile kayıt arasında oylama başka bir bağlantıda kapandıysa oy kaydedilmez ve makbuz verilmez.
    if db.execute(
        """INSERT INTO oylar (teklif_id, kullanici_id, secim, agirlik, aciklama, gerekce, taahhut, zaman)
           SELECT ?, ?, ?, ?, ?, ?, ?, ? WHERE EXISTS
             (SELECT 1 FROM teklifler WHERE id = ? AND durum = 'ACIK' AND bitis > ?)
           ON CONFLICT (teklif_id, kullanici_id) DO UPDATE SET secim = excluded.secim, agirlik = excluded.agirlik,
             aciklama = excluded.aciklama, gerekce = excluded.gerekce, taahhut = excluded.taahhut,
             zaman = excluded.zaman""",
        (teklif_id, kullanici["id"], secim, agirlik, aciklama, gerekce, taahhut, an, teklif_id, an),
    ).rowcount == 0:
        raise KuralHatasi("Bu oylama kapandı.")
    defter.ekle(db, "OY", {"teklif": teklif_id, "yurttas": kullanici["takma_ad"], "taahhut": taahhut,
                           "agirlik": agirlik})
    # Evet/Hayır oylamaları herkes oy verince erken biter; fikir turları süresini doldurur.
    if turu(t).erken_biter and _herkes_oy_verdi(db, t, baglam):
        sonuclandir(db, teklif_id)
    return makbuz


def _herkes_oy_verdi(db, teklif, baglam):
    hakli = {k["id"] for k in uygunluk.oy_hakki_olanlar(db, baglam)}
    verenler = {r["kullanici_id"] for r in db.execute("SELECT kullanici_id FROM oylar WHERE teklif_id = ?",
                                                      (teklif["id"],))}
    return bool(hakli) and hakli <= verenler


# --- Sayım ---

def gerekli_katilim(db, hak_sahibi):
    oran = yonetmelik.deger(db, "YETER_SAYI_ORANI")
    return min(hak_sahibi, max(yonetmelik.deger(db, "MIN_KATILIM"), math.ceil(hak_sahibi * oran - 1e-9)))


def _oran(agirlik, kisi, toplam_agirlik, toplam_kisi):
    """Çift oran: ağırlıklı pay ile kişi payının küçüğü."""
    if not toplam_agirlik or not toplam_kisi:
        return 0.0
    return min(agirlik / toplam_agirlik, kisi / toplam_kisi)


def sayim(db, teklif):
    baglam = teklif_baglami(db, teklif)
    hakli = {k["id"] for k in uygunluk.oy_hakki_olanlar(db, baglam)}
    oylar = db.execute("""SELECT o.*, k.takma_ad, k.yz_mi FROM oylar o JOIN kullanicilar k ON k.id = o.kullanici_id
                          WHERE o.teklif_id = ?""", (teklif["id"],)).fetchall()
    dogrudan = {o["kullanici_id"]: o for o in oylar}
    tasinan, dusen = devir.devirleri_coz(db, baglam, set(dogrudan), hakli)

    tur_ = turu(teklif)
    tablo = tur_.bos_tablo(db, teklif)

    devredilen = 0
    for uid, o in dogrudan.items():
        ek = tasinan.get(uid, [])
        devredilen += len(ek)
        tablo[o["secim"]]["agirlik"] += o["agirlik"] + len(ek)
        tablo[o["secim"]]["kisi"] += 1 + len(ek)

    toplam_agirlik = sum(s["agirlik"] for s in tablo.values())
    toplam_kisi = katilan = sum(s["kisi"] for s in tablo.values())
    for s in tablo.values():
        s["agirlik_oran"] = s["agirlik"] / toplam_agirlik if toplam_agirlik else 0
        s["kisi_oran"] = s["kisi"] / toplam_kisi if toplam_kisi else 0
        s["oran"] = _oran(s["agirlik"], s["kisi"], toplam_agirlik, toplam_kisi)
    hak_sahibi = len(hakli | set(dogrudan))
    gerekli = tur_.gerekli_katilim(db, gerekli_katilim(db, hak_sahibi))
    yeter = katilan >= gerekli and katilan > 0

    cekimser = tablo[CEKIMSER]
    d = tur_.degerlendir(teklif, tablo, toplam_agirlik, toplam_kisi, yeter)
    sirali, onde = d["sirali"], d["onde"]
    dusen_sayilari = {}
    for _, neden in dusen:
        dusen_sayilari[neden] = dusen_sayilari.get(neden, 0) + 1

    return {
        "secenekler": sirali, "cekimser": cekimser, "toplam_agirlik": toplam_agirlik, "toplam_kisi": toplam_kisi,
        "katilan": katilan, "hak_sahibi": hak_sahibi, "gerekli": gerekli, "yeter": yeter, "esik": teklif["esik"],
        "onde": onde["anahtar"] if onde else None,
        "agirlik_oran": onde["agirlik_oran"] if onde else 0, "kisi_oran": onde["kisi_oran"] if onde else 0,
        "oran": onde["oran"] if onde else 0,
        "agirlik_ok": d["agirlik_ok"], "kisi_ok": d["kisi_ok"], "kabul": d["kabul"],
        "acik_oylar": [{"takma_ad": o["takma_ad"], "yz_mi": o["yz_mi"], "secim": o["secim"],
                        "secim_metni": tablo[o["secim"]]["metin"], "agirlik": o["agirlik"],
                        "aciklama": o["aciklama"], "gerekce": o["gerekce"]} for o in oylar if o["agirlik"] > 1],
        "devredilen": devredilen, "dusen": dusen_sayilari, "dogrudan": len(dogrudan),
    }


# --- Sonuçlandırma ---

def sonuclandir(db, teklif_id):
    if not db.in_transaction:
        db.execute("BEGIN IMMEDIATE")      # sayım ile kapanış arasında başka bir bağlantı oy yazamasın
    t = teklif_getir(db, teklif_id)
    if t["durum"] != "ACIK":
        return
    tur_ = turu(t)
    s = sayim(db, t)
    durum = tur_.sonuc_durumu(s)
    tur_.sonucu_tamamla(db, t, s)
    sonuc_json = json.dumps(s, ensure_ascii=False)
    # Atomik geçiş: aynı anda iki iş parçacığı sonuçlandırmaya çalışırsa sadece biri başarır.
    if db.execute("UPDATE teklifler SET durum = ?, sonuc = ?, kapanis = ? WHERE id = ? AND durum = 'ACIK'",
                  (durum, sonuc_json, zaman.simdi_metin(), teklif_id)).rowcount == 0:
        return
    db.onbellek.pop("gruplar", None)   # görüş grupları yeni sonuçla yeniden hesaplanmalı
    gunluk.kaydet(db, None, "SONUC",
                  f"#{teklif_id} {teklif_basligi(db, t)}: {ayarlar.TEKLIF_DURUMLARI[durum].lower()} "
                  f"(katılım {s['katilan']}/{s['hak_sahibi']})")
    defter.ekle(db, "SONUC", {"teklif": teklif_id, "durum": durum, "ozet": defter.ozet(sonuc_json),
                              "katilan": s["katilan"]})
    tur_.sonuc_bildirimi(db, t, s, durum)
    tur_.uygula(db, teklif_getir(db, teklif_id), s, durum)


def sonuc(teklif):
    return json.loads(teklif["sonuc"]) if teklif["sonuc"] else None


# --- Listeleme ---

def teklif_basligi(db, t):
    if t["tip"] not in teklif_turleri.TURLER:      # eski sürümden kalmış, artık tanımlı olmayan tür
        return "Eski oylama"
    return turu(t).baslik(db, t)


def oy_sayisi(db, teklif_id):
    return db.execute("SELECT COUNT(*) FROM oylar WHERE teklif_id = ?", (teklif_id,)).fetchone()[0]


def konu_teklifleri(db, konu_id):
    return db.execute("SELECT * FROM teklifler WHERE konu_id = ? ORDER BY id DESC", (konu_id,)).fetchall()


def kullanici_teklifleri(db, kullanici):
    liste = []
    for t in db.execute("SELECT * FROM teklifler WHERE durum = 'ACIK' ORDER BY bitis").fetchall():
        durum = oy_durumu(db, t, kullanici)
        if durum["agirlik"] > 0:
            liste.append({"teklif": t, "baslik": teklif_basligi(db, t), "durum": durum})
    return liste


def bekleyen_oy_sayisi(db, kullanici):
    return sum(1 for x in kullanici_teklifleri(db, kullanici) if x["durum"]["oy"] is None)


def acik_teklifler(db, limit=10):
    return [{"teklif": t, "baslik": teklif_basligi(db, t)} for t in
            db.execute("SELECT * FROM teklifler WHERE durum = 'ACIK' ORDER BY bitis LIMIT ?", (limit,))]
