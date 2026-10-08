"""Konunun yaşam döngüsü — GoF **State** deseni.

    TARTISMA ──► OYLAMA (1.–5. tur) ──► KARARA_BAGLANDI
                                   └──► SONUCSUZ
    (kaldırılmamış her durumdan oylamayla) ──► KALDIRILDI   (veritabanında `silindi = 1`)

Her durum bir sınıftır ve "bu durumda ne yapılabilir?" sorusunu kendisi yanıtlar. İzinler ve izin verilen geçişler
buradan okunur; geçişi yapan işlemler (konular.oylamayi_baslat, durum_degistir, konuyu_kaldir) geçiş tablosuna danışır.

Geçişin kendisi durum nesnesinde değil konular.py'de yapılır: geçiş veritabanı, kayıt defteri ve bildirim yazımı
gerektirir. Bunları durum sınıflarına taşımak modüller arasında döngüsel bağımlılık yaratır. Durum nesneleri
"ne yapılabilir ve nereye gidilebilir" bilgisinin tek kaynağıdır.

Durumlar iç durum taşımaz; her biri tek bir paylaşılan nesnedir. `durumu(konu)` bir veritabanı satırına karşılık
gelen durum nesnesini verir.
"""
from . import ayarlar
from .hatalar import KuralHatasi


class GecersizGecis(Exception):
    """Programlama hatası: durum makinesinde tanımlı olmayan bir geçiş istendi (ör. TARTISMA → KARARA_BAGLANDI)."""


class KonuDurumu:
    kod = ""
    yazilabilir = False          # mesaj yazma, yanıtlama, mesaj düzenleme, özet isteme
    kapali = False               # sonuçlanmış: itiraz konusu açılabilir
    okunabilir = True            # içerik ve geçmiş gösterilebilir
    zamanli = False              # süresi dolunca zamanlayıcı bir sonraki aşamaya geçirir (sunumda "Süreyi ilerlet")
    sonrakiler = frozenset()     # izin verilen geçişler

    @property
    def ad(self):
        return ayarlar.KONU_DURUMLARI.get(self.kod, "Kaldırıldı")

    def fikir_yazilabilir(self, konu):
        return False

    def konu_duzenlenebilir(self):
        return False

    def fikir_duzenlenebilir(self):
        return False

    def gecis_dogrula(self, yeni):
        if yeni not in self.sonrakiler:
            raise GecersizGecis(f"{self.kod} → {yeni} geçişi tanımlı değil")

    def __repr__(self):
        return f"<KonuDurumu {self.kod}>"


class Tartisma(KonuDurumu):
    kod = "TARTISMA"
    yazilabilir = True
    zamanli = True
    sonrakiler = frozenset({"OYLAMA", "KALDIRILDI"})

    def fikir_yazilabilir(self, konu):
        return True

    def konu_duzenlenebilir(self):
        return True

    def fikir_duzenlenebilir(self):
        return True


class Oylama(KonuDurumu):
    kod = "OYLAMA"
    yazilabilir = True                                   # oylama sürerken tartışma devam eder
    zamanli = True
    sonrakiler = frozenset({"KARARA_BAGLANDI", "SONUCSUZ", "KALDIRILDI"})

    def fikir_yazilabilir(self, konu):
        return konu["tur"] == 1                          # yeni fikir 1. tur bitene kadar yazılabilir


class KararaBaglandi(KonuDurumu):
    kod = "KARARA_BAGLANDI"
    kapali = True
    sonrakiler = frozenset({"KALDIRILDI"})


class Sonucsuz(KonuDurumu):
    kod = "SONUCSUZ"
    kapali = True
    sonrakiler = frozenset({"KALDIRILDI"})


class Kaldirildi(KonuDurumu):
    """Konu oylamayla kaldırıldı: hiçbir işlem yapılamaz, içerik ve geçmiş gösterilmez."""
    kod = "KALDIRILDI"
    okunabilir = False


DURUMLAR = {d.kod: d for d in (Tartisma(), Oylama(), KararaBaglandi(), Sonucsuz())}
KALDIRILDI = Kaldirildi()


def durumu(konu):
    return KALDIRILDI if konu["silindi"] else DURUMLAR[konu["durum"]]


def onceki_durumlar(yeni):
    """`yeni` duruma geçilebilen durumların kodları (atomik UPDATE'lerin WHERE koşulu bu tablodan kurulur)."""
    return sorted(kod for kod, d in DURUMLAR.items() if yeni in d.sonrakiler)


# --- Korumalar: kural ihlalinde kullanıcıya gösterilecek KuralHatasi ---

def okunabilir_olmali(konu):
    if not durumu(konu).okunabilir:
        raise KuralHatasi("Bu konu kaldırıldı.")


def yazilabilir_olmali(konu):
    d = durumu(konu)
    okunabilir_olmali(konu)
    if not d.yazilabilir:
        raise KuralHatasi("Bu konu kapandı; artık yazılamaz. Karara katılmıyorsan itiraz konusu açabilirsin.")
