"""Oylama (teklif) türleri — GoF **Strategy** + **Registry**; oylama.py ile birlikte **Template Method**.

Forumdaki her oylama aynı iskeletten geçer (oylama.py): aç → oy topla → say → sonuçlandır. Bu iskeletin türe göre
değişen adımları ("kancalar") burada, her tür için ayrı bir sınıfta durur:

    TeklifTuru (soyut)
    ├── FikirTuru            KARAR        seçenekler fikirler; sonucu eleme kuralları belirler (sonuclar.py)
    └── EvetHayirTuru (soyut)             seçenekler Evet / Hayır / Çekimser; sonucu eşik belirler
        ├── MesajGizlemeTuru  MESAJ_SILME
        ├── KonuKaldirmaTuru  KONU_SILME
        ├── UzmanlikTuru      UZMANLIK
        ├── YonetmelikTuru    YONETMELIK
        └── KategoriTuru      KATEGORI

Önceden bu farklar `if t["tip"] == "KARAR": ... elif ...` dallarıyla oylama.py, uygunluk.py, sonuclar.py ve web
katmanında 30'dan fazla yere dağılmıştı; yeni bir tür eklemek altı dosyaya dokunmayı gerektiriyordu ve unutulan bir
dal (ör. uygunluk.teklif_baglami'nın "geri kalan her şey uzmanlıktır" varsayımı) sessizce yanlış çalışıyordu.
Şimdi yeni bir oylama türü eklemek = bu dosyaya @kaydet ile bir sınıf eklemek (Açık/Kapalı ilkesi). Her alt sınıf
üst sınıfın sözleşmesine uyar; oylama.py hangi türle çalıştığını bilmez (Liskov).

Türlerin adı, eşik ve süre parametreleri veri olarak ayarlar.TEKLIF_TIPLERI'nde durur (şablonlar da oradan okur).
"""
import json
from abc import ABC, abstractmethod

from . import ayarlar, bildirimler, kategoriler, konular, ontoloji, sonuclar, uygunluk, uzmanlik, yonetmelik, zaman
from .hatalar import KuralHatasi
from .oy_kurallari import CEKIMSER, EVET_HAYIR, GIZLENEN_FIKIR, esik_saglandi

TURLER = {}


def kaydet(sinif):
    """Sınıf dekoratörü: türün tek örneğini kayıt defterine ekler. Aynı kod iki kez kaydedilemez."""
    if sinif.kod in TURLER:
        raise KeyError(f"{sinif.kod} oylama türü zaten kayıtlı")
    if sinif.kod not in ayarlar.TEKLIF_TIPLERI:
        raise KeyError(f"{sinif.kod} için ayarlar.TEKLIF_TIPLERI'nde ad/eşik/süre tanımı yok")
    TURLER[sinif.kod] = sinif()
    return sinif


def tur(kod):
    try:
        return TURLER[kod]
    except KeyError:
        raise KuralHatasi(f"Bilinmeyen oylama türü: {kod}") from None


def _veri(t):
    return json.loads(t["veri"] or "{}")


def _hucre(anahtar, metin, **ek):
    return dict(anahtar=anahtar, metin=metin, agirlik=0, kisi=0, **ek)


class TeklifTuru(ABC):
    """Bir oylama türünün iskelete taktığı kancalar. Varsayılanlar "bir konuya bağlı oylama" içindir."""
    kod = ""
    fikir_oylamasi = False       # seçenekler fikirler mi (yoksa Evet/Hayır)?
    erken_biter = True           # oy hakkı olan herkes oy verince süre dolmadan sonuçlanır mı?

    @property
    def ad(self):
        return ayarlar.TEKLIF_TIPLERI[self.kod]["ad"]

    # --- açılış ---
    def sure_parametresi(self, tur_no):
        return ayarlar.TEKLIF_TIPLERI[self.kod]["sure"]

    def esik(self, db, verilen=None):
        """Teklife yazılacak eşik kodu (ör. "UCTE_IKI"). Verilen eşik (korunan madde) önceliklidir."""
        return verilen or yonetmelik.deger(db, ayarlar.TEKLIF_TIPLERI[self.kod]["esik"])

    def acilis_alicilari(self, db, t):
        return bildirimler.konu_katilimcilari(db, t["konu_id"])

    # --- kimler, hangi ağırlıkla oy verir ---
    def baglam(self, db, t):
        konu = db.execute("SELECT * FROM konular WHERE id = ?", (t["konu_id"],)).fetchone()
        return uygunluk.konu_baglami(konu)

    # --- seçenekler ve sayım ---
    @abstractmethod
    def secenekler(self, db, t):
        """[(anahtar, metin, ek_alanlar)] — oy verilebilecek seçenekler (çekimser dahil)."""

    def secim_anahtarlari(self, db, t):
        return [a for a, _, _ in self.secenekler(db, t)]

    def secim_dogrula(self, db, t, secim):
        if secim not in self.secim_anahtarlari(db, t):
            raise KuralHatasi("Geçersiz seçim.")

    def secim_metni(self, db, t, secim):
        return next((m for a, m, _ in self.secenekler(db, t) if a == secim), secim)

    def bos_tablo(self, db, t):
        return {a: _hucre(a, m, **ek) for a, m, ek in self.secenekler(db, t)}

    def gerekli_katilim(self, db, gerekli):
        return gerekli

    @abstractmethod
    def degerlendir(self, t, tablo, toplam_agirlik, toplam_kisi, yeter):
        """Döner: {"sirali", "onde", "agirlik_ok", "kisi_ok", "kabul"}."""

    # --- sonuçlandırma ---
    @abstractmethod
    def sonuc_durumu(self, s):
        """Teklifin kapanış durumu (ayarlar.TEKLIF_DURUMLARI anahtarlarından biri)."""

    def sonucu_tamamla(self, db, t, s):
        """Sonuç JSON'a yazılmadan önce türe özgü alanlar eklenir (kapanış anının anlık görüntüsü)."""

    def sonuc_bildirimi(self, db, t, s, durum):
        oy_verenler = [r["kullanici_id"] for r in db.execute("SELECT kullanici_id FROM oylar WHERE teklif_id = ?",
                                                             (t["id"],))]
        bildirimler.coklu_gonder(db, oy_verenler + ([t["acan_id"]] if t["acan_id"] else []),
                                 f"Oylama sonuçlandı ({ayarlar.TEKLIF_DURUMLARI[durum].lower()}): {self.baslik(db, t)}",
                                 f"/oylama/{t['id']}")

    @abstractmethod
    def uygula(self, db, t, s, durum):
        """Sonuç çıkınca ne olacağı (kabul edilen mesajı gizle, uzmanlığı ver...)."""

    # --- gösterim ---
    def baslik(self, db, t):
        konu = db.execute("SELECT baslik FROM konular WHERE id = ?", (t["konu_id"],)).fetchone()
        return f"{self.ad}: {konu['baslik'] if konu else ''}"

    def sayfa_verisi(self, db, t):
        """Oylama sayfasının bu türe özgü bölümü için veri."""
        return {}


# --- Fikir oylaması ---

@kaydet
class FikirTuru(TeklifTuru):
    kod = "KARAR"
    fikir_oylamasi = True
    erken_biter = False          # tur süresini doldurur: tartışma sürer, oy değiştirilebilir, 1. turda fikir eklenir
    ESIK = "TUR"                 # eşik yerine eleme kuralları (sonuclar.tur_karari)

    def sure_parametresi(self, tur_no):
        return "SURE_TUR1_SAAT" if tur_no == 1 else "SURE_TUR_SAAT"

    def esik(self, db, verilen=None):
        return self.ESIK

    def fikirler(self, db, t):
        """Seçenekler. `gizli`: fikir oylamayla gizlendi; yarışmaz, metni gösterilmez (oyları toplamda kalır)."""
        return [dict(s, metin=GIZLENEN_FIKIR if s["gizli"] else s["metin"]) for s in db.execute(
            """SELECT s.*, COALESCE(m.gizli, 0) AS gizli FROM secenekler s LEFT JOIN mesajlar m ON m.id = s.mesaj_id
               WHERE s.teklif_id = ? ORDER BY s.id""", (t["id"],))]

    def secenekler(self, db, t):
        return [(str(s["id"]), s["metin"], {"mesaj_id": s["mesaj_id"], "gizli": bool(s["gizli"])})
                for s in self.fikirler(db, t)] + [(CEKIMSER, "Çekimser", {"mesaj_id": None, "gizli": False})]

    def secim_dogrula(self, db, t, secim):
        super().secim_dogrula(db, t, secim)
        if any(str(s["id"]) == secim and s["gizli"] for s in self.fikirler(db, t)):
            raise KuralHatasi("Bu fikir oylamayla gizlendi; başka bir seçenek seç.")

    def degerlendir(self, t, tablo, toplam_agirlik, toplam_kisi, yeter):
        sirali = sorted((s for s in tablo.values() if s["anahtar"] != CEKIMSER),
                        key=lambda s: (s["gizli"], -s["oran"], -s["agirlik"], int(s["anahtar"])))
        onde = sirali[0] if sirali and sirali[0]["kisi"] > 0 and not sirali[0]["gizli"] else None
        # sonucu eleme kuralları belirler (sonuclar.tur_karari); eşik alanları anlamsız olduğu için False
        return {"sirali": sirali, "onde": onde, "agirlik_ok": False, "kisi_ok": False, "kabul": False}

    def sonuc_durumu(self, s):
        return "BITTI" if s["yeter"] else "YETERSIZ"

    def sonucu_tamamla(self, db, t, s):
        s["tur"] = sonuclar.tur_karari(t["tur_no"], s, *sonuclar.tur_kurallari(db, t["tur_no"])).sozluk()

    def sonuc_bildirimi(self, db, t, s, durum):
        pass                     # bildirimi turun sonucuna göre (karar / yeni tur / sonuçsuz) sonuclar.tur_uygula gönderir

    def uygula(self, db, t, s, durum):
        sonuclar.tur_uygula(db, t, s)

    def baslik(self, db, t):
        konu = db.execute("SELECT baslik FROM konular WHERE id = ?", (t["konu_id"],)).fetchone()
        return f"{t['tur_no']}. tur: {konu['baslik'] if konu else ''}"


# --- Evet/Hayır oylamaları ---

class EvetHayirTuru(TeklifTuru):
    def secenekler(self, db, t):
        return [(s, ayarlar.SECIM_ADLARI[s], {}) for s in EVET_HAYIR]

    def degerlendir(self, t, tablo, toplam_agirlik, toplam_kisi, yeter):
        evet = tablo["EVET"]
        agirlik_ok = esik_saglandi(evet["agirlik"], toplam_agirlik, t["esik"])
        kisi_ok = esik_saglandi(evet["kisi"], toplam_kisi, t["esik"])
        return {"sirali": list(tablo.values()), "onde": evet, "agirlik_ok": agirlik_ok, "kisi_ok": kisi_ok,
                "kabul": yeter and agirlik_ok and kisi_ok}

    def sonuc_durumu(self, s):
        return "KABUL" if s["kabul"] else ("YETERSIZ" if not s["yeter"] else "RET")


def _durum_metni(durum):
    return {"KABUL": "kabul edildi", "RET": "reddedildi", "YETERSIZ": "yeter sayıya ulaşılamadı"}[durum]


def _mesaj_listesi(idler):
    if len(idler) == 1:
        return f"#{idler[0]} numaralı mesajın"
    return ", ".join(f"#{i}" for i in idler) + " numaralı mesajların"


@kaydet
class MesajGizlemeTuru(EvetHayirTuru):
    kod = "MESAJ_SILME"

    def idler(self, t):
        return _veri(t).get("mesajlar", [t["hedef_id"]])

    def uygula(self, db, t, s, durum):
        idler = self.idler(t)
        if durum == "KABUL":
            for mesaj_id in idler:
                konular.mesaji_gizle(db, mesaj_id, f"Bu mesaj {zaman.simdi():%d.%m.%Y} tarihinde oylamayla "
                                                   f"gizlendi ({sonuclar.ozet(s)}). Gerekçe: {t['gerekce']}", t["id"])
        konular.sistem_mesaji(db, t["konu_id"], f"{_mesaj_listesi(idler)} gizleme oylaması: "
                                                f"{_durum_metni(durum)} ({sonuclar.ozet(s)}).")

    def baslik(self, db, t):
        idler = self.idler(t)
        return f"{self.ad}: " + ", ".join(f"#{i}" for i in idler) + \
            (" numaralı mesaj" if len(idler) == 1 else " numaralı mesajlar")

    def sayfa_verisi(self, db, t):
        konu = db.execute("SELECT silindi FROM konular WHERE id = ?", (t["konu_id"],)).fetchone()
        if konu and konu["silindi"]:
            return {"hedef_mesajlar": []}           # kaldırılmış konunun mesajları burada da gösterilmez
        idler = self.idler(t)
        return {"hedef_mesajlar": db.execute(
            f"""SELECT m.*, k.takma_ad, k.yz_mi FROM mesajlar m LEFT JOIN kullanicilar k ON k.id = m.yazar_id
                WHERE m.id IN ({','.join('?' * len(idler))}) ORDER BY m.id""", idler).fetchall()}


@kaydet
class KonuKaldirmaTuru(EvetHayirTuru):
    kod = "KONU_SILME"

    def uygula(self, db, t, s, durum):
        if durum == "KABUL":
            konular.konuyu_kaldir(db, t["konu_id"], f"Bu konu {zaman.simdi():%d.%m.%Y} tarihinde oylamayla "
                                                    f"kaldırıldı ({sonuclar.ozet(s)}). Gerekçe: {t['gerekce']}")
        else:
            konular.sistem_mesaji(db, t["konu_id"], f"Konu kaldırma oylaması: {_durum_metni(durum)} "
                                                    f"({sonuclar.ozet(s)}).")


@kaydet
class UzmanlikTuru(EvetHayirTuru):
    """Başvuruyu o alanın "niş kitlesi" oylar; herkesin oyu 1, aday oy kullanamaz."""
    kod = "UZMANLIK"

    def baglam(self, db, t):
        kategori_id = _veri(t)["kategori_id"]
        return uygunluk.Baglam(None, kategori_id, 1, {t["hedef_id"]}, esit_agirlik=True,
                               secmenler=uygunluk.alanda_yazanlar(db, kategori_id))

    def acilis_alicilari(self, db, t):
        return uygunluk.alanda_yazanlar(db, _veri(t)["kategori_id"])

    def gerekli_katilim(self, db, gerekli):
        return max(gerekli, yonetmelik.deger(db, "MIN_KATILIM"))   # tek kişilik bir kitle kimseyi uzman yapamaz

    def uygula(self, db, t, s, durum):
        if durum == "KABUL":
            uzmanlik.uzmanlik_ver(db, t["hedef_id"], _veri(t)["kategori_id"])

    def baslik(self, db, t):
        k = db.execute("SELECT takma_ad FROM kullanicilar WHERE id = ?", (t["hedef_id"],)).fetchone()
        return f"{self.ad}: @{k['takma_ad']} → {ontoloji.yol_metni(db, 'kategoriler', _veri(t)['kategori_id'])}"

    def sayfa_verisi(self, db, t):
        k = db.execute("SELECT * FROM kullanicilar WHERE id = ?", (t["hedef_id"],)).fetchone()
        kategori_id = _veri(t)["kategori_id"]
        return {"aday": {"k": k, "sart": uzmanlik.on_sartlar(db, k["id"], kategori_id),
                         "kontenjan": uzmanlik.kontenjan(db, kategori_id)}}


class ForumGeneliTuru(EvetHayirTuru):
    """Forumun kurallarını ya da yapısını değiştiren oylamalar: bütün üyeler oylar, herkesin oyu 1 (eşitlik)."""

    def baglam(self, db, t):
        return uygunluk.Baglam(None, None, 1, esit_agirlik=True)

    def acilis_alicilari(self, db, t):
        return [r["id"] for r in db.execute("SELECT id FROM kullanicilar WHERE yz_mi = 0")]


@kaydet
class YonetmelikTuru(ForumGeneliTuru):
    kod = "YONETMELIK"

    def uygula(self, db, t, s, durum):
        if durum == "KABUL":
            yonetmelik.degisikligi_uygula(db, _veri(t))

    def baslik(self, db, t):
        return f"{self.ad}: {_veri(t).get('aciklama', '')}"


@kaydet
class KategoriTuru(ForumGeneliTuru):
    kod = "KATEGORI"

    def uygula(self, db, t, s, durum):
        if durum == "KABUL":
            kategoriler.ekle(db, t)

    def baslik(self, db, t):
        return f"{self.ad}: {kategoriler.oneri_basligi(db, _veri(t))}"

    def sayfa_verisi(self, db, t):
        veri = _veri(t)
        eklenen = db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id IS ?",
                             (veri["ad"], veri.get("ust_id"))).fetchone() if t["durum"] == "KABUL" else None
        return {"kategori_onerisi": {"yol": kategoriler.oneri_basligi(db, veri), "ust": veri.get("ust_id"),
                                     "kavramlar": veri.get("kavramlar", []), "eklenen": eklenen}}

