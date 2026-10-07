"""Yönetmeliğin denetim maddeleri (D1–D7) — GoF **Chain of Responsibility**.

Her madde zincirin bir halkasıdır: kendi kontrolünü yapar, bulgusunu ekler ve isteği sıradaki halkaya iletir
(ders slaytı 44'teki `Dogrulayici(sonraki)` kalıbı). Zincir sonuna kadar yürür; hiçbir halka akışı kesmez, çünkü
rapor bütün maddelerin sonucunu gösterir. Bir maddenin ciddiyeti (ENGEL / UYARI / KAPALI) yönetmelikte veridir ve
oylamayla değişir; halka yalnızca "geçti mi, ne diyeceğim" sorusunu yanıtlar.

Önceden yedi kural 77 satırlık tek bir fonksiyonun içindeydi; mesaj denetimi D1 ve D2'yi ayrıca yeniden yazıyordu.
Şimdi yeni bir madde (ör. D8) = yonetmelik.MADDELER'e metni + burada bir halka sınıfı; mesajlara da uygulanacaksa
`mesajlara_uygulanir = True`. Halkalar tek tek test edilebilir.
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from . import ontoloji, yonetmelik, zaman
from .hatalar import KuralHatasi
from .metin import yuzde

KABA_IFADELER = ["aptal", "salak", "gerizekal", "geri zekal", "cahil", "ahmak", "beyinsiz", "serefsiz",
                 "haysiyetsiz", "mankafa", "dangalak", "embesil"]
_YUMUSAMA = {"k": "g", "p": "b", "t": "d", "c": "c"}


def _yumusamis(kok):
    """Türkçe ünsüz yumuşaması: ünlüyle başlayan ek alınca sondaki p, ç, t, k → b, c, d, ğ (ahmak → ahmağın).
    Katlanmış metinde ğ, g olur. Ölçümde (olcum/) "ahmağın", "salağa" biçimleri bu yüzden kaçıyordu."""
    return kok[:-1] + _YUMUSAMA[kok[-1]] if kok[-1] in _YUMUSAMA else kok


KABA_KOKLER = sorted(set(KABA_IFADELER) | {_yumusamis(k) for k in KABA_IFADELER})
# Kök kelimenin başında aranır (Türkçe sondan eklemeli): "asalak bitkiler" içindeki "salak" hakaret sayılmaz.
_KABA_DESENLER = {k: re.compile(r"(?<![a-z0-9])" + re.escape(k)) for k in KABA_KOKLER}
# Desenler rakam ya da kelime sınırında başlar. Sınırsız e-posta deseni, uzun bir metinde her konumdan yeniden
# denendiği için süre metin uzunluğunun karesiyle büyüyordu (40.000 karakterlik bir gerekçe ~7 sn); telefon deseni de
# 13 haneli bir barkodun içindeki 10 haneyi telefon sanıyordu.
KISISEL_VERI_DESENLERI = {
    "telefon numarası": re.compile(r"(?<!\d)(?:\+?90|0)?\s?\(?5\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"),
    "e-posta adresi": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+\.[\w.]+"),
    "IBAN": re.compile(r"(?<![a-z0-9])TR\s?\d{2}(?:[\s-]?\d{4}){5}[\s-]?\d{2}(?!\d)", re.IGNORECASE),
}
METIN_EN_UZUN = 5000    # serbest metinler (mesaj, fikir, gerekçe, açıklama) için üst sınır
_ON_BIR_HANE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")


def tc_kimlik_gecerli_mi(no):
    """T.C. kimlik numarasının resmi sağlaması: 11 hane, ilk hane 0 değil, 10. ve 11. haneler önceki hanelerden hesaplanır.
    Yalnızca biçime bakmak, 11 haneli her sipariş ya da fatura numarasını kişisel veri sanıp mesajı engelliyordu."""
    if len(no) != 11 or not no.isdigit() or no[0] == "0":
        return False
    h = [int(c) for c in no]
    return (sum(h[0:9:2]) * 7 - sum(h[1:8:2])) % 10 == h[9] and sum(h[:10]) % 10 == h[10]


def kaba_ifadeler(metin):
    katli = ontoloji.katla(metin)
    return [k for k, desen in _KABA_DESENLER.items() if desen.search(katli)]


def kisisel_veriler(metin):
    bulunan = [ad for ad, desen in KISISEL_VERI_DESENLERI.items() if desen.search(metin)]
    if any(tc_kimlik_gecerli_mi(no) for no in _ON_BIR_HANE.findall(metin)):
        bulunan.insert(1, "T.C. kimlik numarası")
    return bulunan


@dataclass
class DenetimIstegi:
    """Zincir boyunca taşınan istek: denetlenen konu taslağı."""
    db: object
    baslik: str
    aciklama: str
    kategori_id: int
    konum_id: object = None
    ust: object = None
    haric_konu_id: object = None
    onerilen_kategori: object = None       # D3 doldurur: metin başka bir kategoriye daha çok uyuyorsa

    @property
    def metin(self):
        return f"{self.baslik}\n{self.aciklama}"


class DenetimKurali(ABC):
    """Zincirin bir halkası."""
    kod = ""
    mesajlara_uygulanir = False            # True: mesaj, fikir ve gerekçelerde de uygulanır (yalnızca ENGEL ise)

    def __init__(self, sonraki=None):
        self.sonraki = sonraki

    def isle(self, istek):
        """Bu halkanın bulgusu + sonraki halkaların bulguları."""
        bulgular = []
        sonuc = self.kontrol(istek)
        if sonuc is not None:
            gecti, mesaj = sonuc
            bulgular.append({"kod": self.kod, "baslik": yonetmelik.madde_basligi(istek.db, self.kod),
                             "ciddiyet": yonetmelik.ciddiyet(istek.db, self.kod), "gecti": gecti, "mesaj": mesaj})
        if self.sonraki:
            bulgular += self.sonraki.isle(istek)
        return bulgular

    @abstractmethod
    def kontrol(self, istek):
        """Döner: (geçti_mi, açıklama) ya da None (madde bu istek için geçerli değil, ör. üst konu yokken D6)."""

    def mesaj_sorunu(self, metin):
        """Mesaja uygulanan maddeler için: sorun varsa kullanıcıya gösterilecek metin, yoksa None."""
        return None

    def halkalar(self):
        h = self
        while h:
            yield h
            h = h.sonraki


class SayginDil(DenetimKurali):
    kod = "D1"
    mesajlara_uygulanir = True

    def kontrol(self, istek):
        kaba = kaba_ifadeler(istek.metin)
        return (not kaba, "Kaba ifade bulunamadı." if not kaba
                else f"Kaba ifade var: {', '.join(kaba)}. Kişiye değil fikre yönelik yaz.")

    def mesaj_sorunu(self, metin):
        return "Mesajında kaba ifade var; kişiye değil fikre yönelik yaz." if kaba_ifadeler(metin) else None


class KisiselVeri(DenetimKurali):
    kod = "D2"
    mesajlara_uygulanir = True

    def kontrol(self, istek):
        kisisel = kisisel_veriler(istek.metin)
        return (not kisisel, "Kişisel veri bulunamadı." if not kisisel
                else f"Metinde {', '.join(kisisel)} var. Kişisel verileri kaldır.")

    def mesaj_sorunu(self, metin):
        kisisel = kisisel_veriler(metin)
        return f"Mesajında kişisel veri var ({', '.join(kisisel)}); kaldırıp tekrar gönder." if kisisel else None


class KategoriyeUygunluk(DenetimKurali):
    kod = "D3"

    def kontrol(self, istek):
        db, kategori_id = istek.db, istek.kategori_id
        kategori_adi = ontoloji.yol_metni(db, "kategoriler", kategori_id)
        if ontoloji.genel_mi(db, kategori_id):
            return True, f"“{kategori_adi}” her konuya açık."
        terimler, _ = ontoloji.kategori_iliskisi(db, istek.metin, kategori_id)
        if terimler:
            return True, f"“{kategori_adi}” kavramlarıyla ilişkili: {', '.join(terimler[:6])}."
        oneri_id, oneri_terimler = ontoloji.en_uygun_kategori(db, istek.metin)
        if oneri_id:
            istek.onerilen_kategori = oneri_id
            return False, (f"“{kategori_adi}” ile ilgili bir kavram yok. Metin daha çok "
                           f"“{ontoloji.yol_metni(db, 'kategoriler', oneri_id)}” kategorisine uyuyor "
                           f"({', '.join(oneri_terimler[:4])}).")
        return False, "Metin hiçbir kategoriyle eşleşmedi. Açıklamaya konunun alanıyla ilgili ayrıntı ekle."


class KonumTutarliligi(DenetimKurali):
    kod = "D4"

    def kontrol(self, istek):
        db, konum_id = istek.db, istek.konum_id
        yerler = ontoloji.metindeki_yerler(db, istek.metin)
        if not yerler:
            return True, "Metinde belirli bir yer adı geçmiyor."
        if konum_id is None:
            adlar = ", ".join(ontoloji.yol_metni(db, "konumlar", y) for y in yerler[:3])
            return False, (f"Metinde {adlar} geçiyor ama katılım herkese açık. Konu yalnızca orayı "
                           "ilgilendiriyorsa katılımı oranın sakinleriyle sınırlayabilirsin.")
        uyumsuz = [y for y in yerler if not (ontoloji.altinda_mi(db, "konumlar", y, konum_id)
                                            or ontoloji.altinda_mi(db, "konumlar", konum_id, y))]
        if not uyumsuz:
            return True, "Metindeki yer adları katılım kuralıyla uyumlu."
        return False, (f"Katılım {ontoloji.yol_metni(db, 'konumlar', konum_id)} sakinlerine açık ama metinde "
                       f"{', '.join(ontoloji.yol_metni(db, 'konumlar', y) for y in uyumsuz[:3])} geçiyor.")


class BenzerKonu(DenetimKurali):
    kod = "D5"
    ESIK = 0.5

    def kontrol(self, istek):
        benzer = None
        for k in istek.db.execute("SELECT id, baslik FROM konular WHERE silindi = 0 AND durum != 'SONUCSUZ' AND id != ?",
                                  (istek.haric_konu_id or 0,)):
            oran = ontoloji.benzerlik_orani(istek.baslik, k["baslik"])
            if oran >= self.ESIK and (benzer is None or oran > benzer[1]):
                benzer = (k, oran)
        if benzer is None:
            return True, "Benzer bir konu bulunamadı."
        return False, f"#{benzer[0]['id']} “{benzer[0]['baslik']}” ile {yuzde(benzer[1])} benzer."


class AltKonuIliskisi(DenetimKurali):
    kod = "D6"

    def kontrol(self, istek):
        ust = istek.ust
        if ust is None:
            return None
        db = istek.db
        if (ontoloji.altinda_mi(db, "kategoriler", istek.kategori_id, ust["kategori_id"])
                or ontoloji.altinda_mi(db, "kategoriler", ust["kategori_id"], istek.kategori_id)):
            return True, "Üst konuyla aynı alanda."
        ortak = ontoloji.anlamli_kelimeler(istek.metin) & ontoloji.anlamli_kelimeler(f"{ust['baslik']} {ust['aciklama']}")
        if ortak:
            return True, f"Üst konuyla ortak kavramlar: {', '.join(sorted(ortak)[:5])}."
        return False, "Üst konuyla alanı da kavramları da ortak değil."


class Aciklik(DenetimKurali):
    kod = "D7"
    EN_AZ = 40

    def kontrol(self, istek):
        if len(istek.aciklama.strip()) < self.EN_AZ:
            return False, "Açıklama çok kısa. Derdini ve nedenini anlat."
        return True, "Açıklama yeterli uzunlukta."


def zincir_kur(*siniflar):
    """Halkaları verilen sırayla birbirine bağlar; ilk halkayı döndürür."""
    ilk = None
    for sinif in reversed(siniflar):
        ilk = sinif(ilk)
    return ilk


ZINCIR = zincir_kur(SayginDil, KisiselVeri, KategoriyeUygunluk, KonumTutarliligi, BenzerKonu, AltKonuIliskisi, Aciklik)


def denetle(db, baslik, aciklama, kategori_id, konum_id=None, ust=None, haric_konu_id=None):
    """Bir konu taslağını zincirden geçirir ve bir rapor döndürür."""
    istek = DenetimIstegi(db, baslik, aciklama, kategori_id, konum_id, ust, haric_konu_id)
    bulgular = ZINCIR.isle(istek)
    etkin = [b for b in bulgular if b["ciddiyet"] != "KAPALI"]
    return {
        "bulgular": bulgular,
        "engel": [b for b in etkin if not b["gecti"] and b["ciddiyet"] == "ENGEL"],
        "uyarilar": [b for b in etkin if not b["gecti"] and b["ciddiyet"] == "UYARI"],
        "puan": round(100 * sum(1 for b in etkin if b["gecti"]) / len(etkin)) if etkin else 100,
        "onerilen_kategori": istek.onerilen_kategori,
        "zaman": zaman.simdi_metin(),
    }


def mesaj_denetle(db, icerik):
    """Mesajlar (ve fikir, gerekçe gibi serbest metinler) için zincirin yalnızca ENGEL durumundaki mesaj halkaları
    uygulanır (hakaret, kişisel veri). Gerekçe alanlarının kendi üst sınırı olmadığından uzunluk burada sınırlanır."""
    if len(icerik) > METIN_EN_UZUN:
        raise KuralHatasi(f"Metin en fazla {METIN_EN_UZUN} karakter olabilir.")
    sorunlar = [s for h in ZINCIR.halkalar() if h.mesajlara_uygulanir and yonetmelik.ciddiyet(db, h.kod) == "ENGEL"
                for s in [h.mesaj_sorunu(icerik)] if s]
    if sorunlar:
        raise KuralHatasi(" ".join(sorunlar))
