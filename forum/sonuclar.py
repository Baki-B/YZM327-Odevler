"""Fikir oylaması turunun sonucu: eleme kuralları ve turun sonuçları.

(Evet/Hayır oylamalarının sonucu kendi tür sınıflarındadır: teklif_turleri.py.)
Fikir oylamasında (KARAR) tur bitince eleme kuralları uygulanır:
  1. Yeter sayı yoksa ya da hiç fikir yoksa konu sonuçsuz kapanır.
  2. Bir fikir ezici üstünlük oranına (varsayılan %75) ulaştıysa hemen kabul edilir.
  3. Son turda (5.) en yüksek oranlı fikir kabul edilir; eşitlik varsa konu sonuçsuz kapanır.
  4. Diğer turlarda oranı eleme eşiğinin altında kalan fikirler elenir (1. ve 2. tur %5, 3. tur %10, 4. tur %20).
     Geriye tek fikir kalırsa o kabul edilir; hiç kalmazsa konu sonuçsuz kapanır; birden fazla kalırsa sonraki tur açılır.
Oran = ağırlıklı pay ile kişi payının küçüğü (çekimserler toplamda sayılır); bkz. oylama.sayim.
"""
from dataclasses import dataclass

from . import ayarlar, bildirimler, kararlar, konular, yonetmelik, yz
from .konu_durumlari import durumu
from .metin import yuzde

_HASSASIYET = 1e-9


def ozet(s):
    return (f"ağırlıklı {yuzde(s['agirlik_oran'])}, kişi {yuzde(s['kisi_oran'])}, "
            f"katılım {s['katilan']}/{s['hak_sahibi']}")


# --- Fikir oylaması turu ---

@dataclass(frozen=True)
class TurKarari:
    """Bir turun sonucu ve o an geçerli olan kurallar. Oylama kapanırken sonucun içine yazılır (anlık görüntü):
    yönetmelik sonradan oylamayla değişse de geçmiş tur, kendi kurallarıyla anlatılır."""
    sonuc: str                 # "KABUL" (kalanlar[0] kazandı), "DEVAM" (kalanlar sonraki tura geçti), "SONUCSUZ"
    kalanlar: tuple            # seçenek anahtarları
    elenenler: tuple           # eleme eşiğinin altında kaldığı için elenenler
    aciklama: str
    ezici: float
    eleme: object = None       # bu turun eleme eşiği (son turda None)

    def sozluk(self):
        return {"sonuc": self.sonuc, "kalanlar": list(self.kalanlar), "elenenler": list(self.elenenler),
                "aciklama": self.aciklama, "ezici": self.ezici, "eleme": self.eleme}

    @classmethod
    def sozlukten(cls, d):
        return cls(d["sonuc"], tuple(d["kalanlar"]), tuple(d["elenenler"]), d["aciklama"], d["ezici"], d["eleme"])


def tur_kurallari(db, tur_no):
    """(ezici üstünlük oranı, eleme eşiği) — son turda eleme yoktur."""
    eleme = None if tur_no >= ayarlar.TUR_SAYISI else yonetmelik.deger(db, ayarlar.ELEME_PARAMETRELERI[tur_no])
    return yonetmelik.deger(db, "ESIK_EZICI"), eleme


def tur_karari(tur_no, s, ezici, eleme):
    """Turun sonucunu hesaplayan SAF fonksiyon: yalnızca sayımı (s) ve iki kuralı alır, veritabanına dokunmaz."""
    def karar(sonuc, kalanlar=(), elenenler=(), aciklama=""):
        return TurKarari(sonuc, tuple(f["anahtar"] for f in kalanlar), tuple(f["anahtar"] for f in elenenler),
                         aciklama, ezici, eleme)

    if not s["yeter"]:
        return karar("SONUCSUZ", aciklama=f"yeter sayıya ulaşılamadı (katılım {s['katilan']}, gereken {s['gerekli']})")
    # orana göre büyükten küçüğe sıralı; oylamayla gizlenen fikir yarışmaz (oyları toplamda sayılmaya devam eder)
    fikirler = [f for f in s["secenekler"] if f["kisi"] > 0 and not f.get("gizli")]
    if not s["secenekler"]:
        return karar("SONUCSUZ", aciklama="hiç fikir yazılmadı")
    if not fikirler:
        return karar("SONUCSUZ", aciklama="hiçbir fikir oy alamadı")
    if fikirler[0]["oran"] + _HASSASIYET >= ezici:
        return karar("KABUL", fikirler[:1], aciklama=f"ezici üstünlük ({yuzde(fikirler[0]['oran'])})")
    if eleme is None:                                   # son tur: en çok oy alan kazanır
        if len(fikirler) > 1 and abs(fikirler[0]["oran"] - fikirler[1]["oran"]) < _HASSASIYET:
            return karar("SONUCSUZ", aciklama="son turda eşitlik çıktı")
        return karar("KABUL", fikirler[:1], aciklama=f"son turda en çok oyu aldı ({yuzde(fikirler[0]['oran'])})")
    kalanlar = [f for f in fikirler if f["oran"] + _HASSASIYET >= eleme]
    elenenler = [f for f in s["secenekler"] if f not in kalanlar and not f.get("gizli")]
    if not kalanlar:
        return karar("SONUCSUZ", elenenler=elenenler, aciklama=f"hiçbir fikir {yuzde(eleme)} eşiğini geçemedi")
    if len(kalanlar) == 1:
        return karar("KABUL", kalanlar, elenenler, f"eşiği geçen tek fikir ({yuzde(kalanlar[0]['oran'])})")
    return karar("DEVAM", kalanlar, elenenler,
                 f"{yuzde(eleme)} altında kalan {len(elenenler)} fikir elendi" if elenenler else
                 f"bütün fikirler {yuzde(eleme)} eşiğini geçti, elenen olmadı")


def tur_sonucu(db, t, s):
    """Kapanan turun kararı: kapanışta yazılmış anlık görüntü; yoksa (eski kayıt) bugünkü kurallarla hesaplanır."""
    if s.get("tur"):
        return TurKarari.sozlukten(s["tur"])
    return tur_karari(t["tur_no"], s, *tur_kurallari(db, t["tur_no"]))


def tur_uygula(db, t, s):
    """Tur bitince: karar (konu kapanır), sonraki tur ya da sonuçsuz kapanış; sonra yapay zeka tur özeti."""
    konu_id, tur_no = t["konu_id"], t["tur_no"]
    konu = konular.konu_getir(db, konu_id)
    if durumu(konu).kod != "OYLAMA":
        return
    k = tur_sonucu(db, t, s)
    secenek = {f["anahtar"]: f for f in s["secenekler"]}
    fikirler = [secenek[a] for a in k.kalanlar]
    katilim = f"katılım {s['katilan']}/{s['hak_sahibi']}"
    alicilar = bildirimler.konu_katilimcilari(db, konu_id) | {
        r["kullanici_id"] for r in db.execute("SELECT kullanici_id FROM oylar WHERE teklif_id = ?", (t["id"],))}
    baglanti = f"/konu/{konu_id}"
    if k.sonuc == "KABUL":
        kazanan = fikirler[0]
        kararlar.olustur(db, konu_id, t["id"], int(kazanan["anahtar"]), kazanan["metin"])
        konular.kapat(db, konu_id, "KARARA_BAGLANDI")
        konular.sistem_mesaji(db, konu_id, f"Karar: “{kazanan['metin']}”. {tur_no}. turda {k.aciklama}; {katilim}. "
                                           "Konu kapandı. Karara katılmayanlar itiraz konusu açabilir.")
        bildirimler.coklu_gonder(db, alicilar, f"Karar çıktı: “{kazanan['metin']}”", baglanti)
    elif k.sonuc == "DEVAM":
        konular.sonraki_tur(db, konu_id, tur_no + 1, [(f["metin"], f["mesaj_id"]) for f in fikirler])
        konular.sistem_mesaji(db, konu_id, f"{tur_no}. tur bitti: {k.aciklama}; {katilim}. {len(fikirler)} fikirle "
                                           f"{tur_no + 1}. tur başladı.")
    else:
        konular.kapat(db, konu_id, "SONUCSUZ")
        konular.sistem_mesaji(db, konu_id, f"Konu sonuçsuz kapandı: {tur_no}. turda {k.aciklama}. "
                                           "İsteyen yeni bir konu açabilir.")
        bildirimler.coklu_gonder(db, alicilar, f"Konu sonuçsuz kapandı: {konu['baslik']}", baglanti)
    yz.tur_ozeti(db, konu_id, tur_no, s, k)
