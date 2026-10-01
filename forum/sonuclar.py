"""Bir oylama sonuçlandığında ne olacağı.

Fikir oylamasında (KARAR) tur bitince eleme kuralları uygulanır:
  1. Yeter sayı yoksa ya da hiç fikir yoksa konu sonuçsuz kapanır.
  2. Bir fikir ezici üstünlük oranına (varsayılan %75) ulaştıysa hemen kabul edilir.
  3. Son turda (5.) en yüksek oranlı fikir kabul edilir; eşitlik varsa konu sonuçsuz kapanır.
  4. Diğer turlarda oranı eleme eşiğinin altında kalan fikirler elenir (1. ve 2. tur %5, 3. tur %10, 4. tur %20).
     Geriye tek fikir kalırsa o kabul edilir; hiç kalmazsa konu sonuçsuz kapanır; birden fazla kalırsa sonraki tur açılır.
Oran = ağırlıklı pay ile kişi payının küçüğü (çekimserler toplamda sayılır); bkz. oylama.sayim.
"""
import json

from . import ayarlar, bildirimler, kararlar, kategoriler, konular, uzmanlik, yonetmelik, yz, zaman

_HASSASIYET = 1e-9


def _yuzde(x):
    return f"%{round(x * 100)}"


def ozet(s):
    return (f"ağırlıklı {_yuzde(s['agirlik_oran'])}, kişi {_yuzde(s['kisi_oran'])}, "
            f"katılım {s['katilan']}/{s['hak_sahibi']}")


def _durum_metni(durum):
    return {"KABUL": "kabul edildi", "RET": "reddedildi", "YETERSIZ": "yeter sayıya ulaşılamadı"}[durum]


def uygula(db, teklif, s, durum):
    {"KARAR": _tur, "MESAJ_SILME": _mesaj_silme, "KONU_SILME": _konu_silme, "UZMANLIK": _uzmanlik,
     "YONETMELIK": _yonetmelik, "KATEGORI": _kategori}[teklif["tip"]](db, teklif, s, durum)


# --- Fikir oylaması turu ---

def tur_karari(db, tur_no, s):
    """Turun sonucunu hesaplar (veritabanına dokunmaz). Döner: (sonuç, fikirler, açıklama)
    sonuç: "KABUL" (fikirler[0] kazandı), "DEVAM" (fikirler sonraki tura kaldı) ya da "SONUCSUZ"."""
    if not s["yeter"]:
        return "SONUCSUZ", [], f"yeter sayıya ulaşılamadı (katılım {s['katilan']}, gereken {s['gerekli']})"
    fikirler = [f for f in s["secenekler"] if f["kisi"] > 0]      # orana göre büyükten küçüğe sıralı
    if not s["secenekler"]:
        return "SONUCSUZ", [], "hiç fikir yazılmadı"
    if not fikirler:
        return "SONUCSUZ", [], "hiçbir fikir oy alamadı"
    ezici = yonetmelik.deger(db, "ESIK_EZICI")
    if fikirler[0]["oran"] + _HASSASIYET >= ezici:
        return "KABUL", fikirler[:1], f"ezici üstünlük ({_yuzde(fikirler[0]['oran'])})"
    if tur_no >= ayarlar.TUR_SAYISI:
        if len(fikirler) > 1 and abs(fikirler[0]["oran"] - fikirler[1]["oran"]) < _HASSASIYET:
            return "SONUCSUZ", [], "son turda eşitlik çıktı"
        return "KABUL", fikirler[:1], f"son turda en çok oyu aldı ({_yuzde(fikirler[0]['oran'])})"
    esik = yonetmelik.deger(db, ayarlar.ELEME_PARAMETRELERI[tur_no])
    kalanlar = [f for f in fikirler if f["oran"] + _HASSASIYET >= esik]
    if not kalanlar:
        return "SONUCSUZ", [], f"hiçbir fikir {_yuzde(esik)} eşiğini geçemedi"
    if len(kalanlar) == 1:
        return "KABUL", kalanlar, f"eşiği geçen tek fikir ({_yuzde(kalanlar[0]['oran'])})"
    elenen = len(s["secenekler"]) - len(kalanlar)
    return "DEVAM", kalanlar, (f"{_yuzde(esik)} altında kalan {elenen} fikir elendi" if elenen else
                               f"bütün fikirler {_yuzde(esik)} eşiğini geçti, elenen olmadı")


def _tur(db, t, s, durum):
    konu_id, tur_no = t["konu_id"], t["tur_no"]
    konu = konular.konu_getir(db, konu_id)
    if konu["silindi"] or konu["durum"] != "OYLAMA":
        return
    sonuc, fikirler, aciklama = tur_karari(db, tur_no, s)
    katilim = f"katılım {s['katilan']}/{s['hak_sahibi']}"
    alicilar = bildirimler.konu_katilimcilari(db, konu_id) | {
        r["kullanici_id"] for r in db.execute("SELECT kullanici_id FROM oylar WHERE teklif_id = ?", (t["id"],))}
    baglanti = f"/konu/{konu_id}"
    if sonuc == "KABUL":
        kazanan = fikirler[0]
        kararlar.olustur(db, konu_id, t["id"], int(kazanan["anahtar"]), kazanan["metin"])
        konular.kapat(db, konu_id, "KARARA_BAGLANDI")
        konular.sistem_mesaji(db, konu_id, f"Karar: “{kazanan['metin']}”. {tur_no}. turda {aciklama}; {katilim}. "
                                           "Konu kapandı. Karara katılmayanlar itiraz konusu açabilir.")
        bildirimler.coklu_gonder(db, alicilar, f"Karar çıktı: “{kazanan['metin']}”", baglanti)
    elif sonuc == "DEVAM":
        konular.sonraki_tur(db, konu_id, tur_no + 1, [(f["metin"], f["mesaj_id"]) for f in fikirler])
        konular.sistem_mesaji(db, konu_id, f"{tur_no}. tur bitti: {aciklama}; {katilim}. {len(fikirler)} fikirle "
                                           f"{tur_no + 1}. tur başladı.")
    else:
        konular.kapat(db, konu_id, "SONUCSUZ")
        konular.sistem_mesaji(db, konu_id, f"Konu sonuçsuz kapandı: {tur_no}. turda {aciklama}. "
                                           "İsteyen yeni bir konu açabilir.")
        bildirimler.coklu_gonder(db, alicilar, f"Konu sonuçsuz kapandı: {konu['baslik']}", baglanti)
    yz.tur_ozeti(db, konu_id, tur_no, s, sonuc, fikirler)


# --- Evet/Hayır oylamaları ---

def _mesaj_listesi(idler):
    if len(idler) == 1:
        return f"#{idler[0]} numaralı mesajın"
    return ", ".join(f"#{i}" for i in idler) + " numaralı mesajların"


def _mesaj_silme(db, t, s, durum):
    idler = json.loads(t["veri"] or "{}").get("mesajlar", [t["hedef_id"]])
    if durum == "KABUL":
        for mesaj_id in idler:
            konular.mesaji_gizle(db, mesaj_id, f"Bu mesaj {zaman.simdi():%d.%m.%Y} tarihinde oylamayla "
                                               f"gizlendi ({ozet(s)}). Gerekçe: {t['gerekce']}", t["id"])
    konular.sistem_mesaji(db, t["konu_id"], f"{_mesaj_listesi(idler)} gizleme oylaması: "
                                            f"{_durum_metni(durum)} ({ozet(s)}).")


def _konu_silme(db, t, s, durum):
    if durum == "KABUL":
        konular.konuyu_kaldir(db, t["konu_id"], f"Bu konu {zaman.simdi():%d.%m.%Y} tarihinde oylamayla "
                                                f"kaldırıldı ({ozet(s)}). Gerekçe: {t['gerekce']}")
    else:
        konular.sistem_mesaji(db, t["konu_id"], f"Konu kaldırma oylaması: {_durum_metni(durum)} ({ozet(s)}).")


def _uzmanlik(db, t, s, durum):
    if durum == "KABUL":
        uzmanlik.uzmanlik_ver(db, t["hedef_id"], json.loads(t["veri"])["kategori_id"])


def _yonetmelik(db, t, s, durum):
    if durum == "KABUL":
        yonetmelik.degisikligi_uygula(db, json.loads(t["veri"]))


def _kategori(db, t, s, durum):
    if durum == "KABUL":
        kategoriler.ekle(db, t)
