"""Kim hangi konuda katılımcı, kim gözlemci; kimin oyu kaç sayılır?

Temel kural: önce uygunluk, sonra ağırlık.
  1. Konunun konum/yaş kurallarını sağlamayan kişi gözlemcidir (okur, yazamaz, oy veremez).
  2. Uygun olan kişinin oyu 1 sayılır; konunun alanındaki uzmanın oyu UZMAN_AGIRLIK (varsayılan 10) sayılır.
  3. Uzmanlık ve yönetmelik oylamalarında herkesin oyu 1'dir.
  Yapay zeka hesapları oy kullanmaz.
"""
from dataclasses import dataclass, field
from datetime import date

from . import ontoloji, zaman


@dataclass
class Uygunluk:
    katilimci: bool
    puan: float                                   # 0–1, ontoloji tabanlı uygunluk ölçümü
    satirlar: list = field(default_factory=list)  # [(gecti_mi, açıklama), ...]

    @property
    def rol(self):
        return "Katılımcı" if self.katilimci else "Gözlemci"


@dataclass
class Baglam:
    """Bir oylamanın geçtiği ortam: hangi konu, hangi alan, uzman oyu kaç sayılır, kimler oy verebilir?"""
    konu: object
    kategori_id: object
    uzman_agirlik: int
    haric: set = field(default_factory=set)       # oy kullanamayacaklar (ör. uzmanlık adayı)
    esit_agirlik: bool = False                    # uzmanlık ve yönetmelik oylaması: herkes 1
    secmenler: object = None                      # None: herkes; küme: yalnızca bu üyeler (uzmanlıkta alanda yazanlar)


def yas(dogum_tarihi, bugun=None):
    bugun = bugun or zaman.simdi().date()
    d = date.fromisoformat(dogum_tarihi)
    return bugun.year - d.year - ((bugun.month, bugun.day) < (d.month, d.day))


def etkin_konum_id(kullanici, an=None):
    """Adres değişikliği bekleme süresinin ardından geçerli olur; süre dolmadıysa eski adres kullanılır."""
    bekleyen = kullanici["bekleyen_konum_id"]
    if bekleyen and kullanici["konum_gecerlilik"] <= zaman.metin(an or zaman.simdi()):
        return bekleyen
    return kullanici["konum_id"]


def konu_zinciri(db, konu):
    """Kök konudan bu konuya kadar olan konular (alt konu, üst konunun kurallarını miras alır)."""
    zincir = [konu]
    ust_id = konu["ust_id"]
    while ust_id:
        ust = db.execute("SELECT * FROM konular WHERE id = ?", (ust_id,)).fetchone()
        zincir.append(ust)
        ust_id = ust["ust_id"]
    return list(reversed(zincir))


def etkin_kurallar(db, konu):
    """Zincirdeki bütün kuralların birleşimi (VE): en dar konum, en dar yaş aralığı."""
    konum_id, min_yas, max_yas = None, None, None
    for k in konu_zinciri(db, konu):
        if k["konum_id"]:
            konum_id = k["konum_id"]
        if k["min_yas"] is not None:
            min_yas = k["min_yas"] if min_yas is None else max(min_yas, k["min_yas"])
        if k["max_yas"] is not None:
            max_yas = k["max_yas"] if max_yas is None else min(max_yas, k["max_yas"])
    return konum_id, min_yas, max_yas


def yas_araligi_metni(min_yas, max_yas):
    if min_yas is not None and max_yas is not None:
        return f"{min_yas}–{max_yas} yaş"
    if min_yas is not None:
        return f"{min_yas}+ yaş"
    return f"{max_yas} yaş ve altı"


def kural_metni(db, konu):
    konum_id, min_yas, max_yas = etkin_kurallar(db, konu)
    parcalar = []
    if konum_id:
        parcalar.append(f"{ontoloji.yol_metni(db, 'konumlar', konum_id)} sakinleri")
    if min_yas is not None or max_yas is not None:
        parcalar.append(yas_araligi_metni(min_yas, max_yas))
    return " · ".join(parcalar) if parcalar else "Herkese açık"


def uygunluk(db, kullanici, konu, an=None):
    if kullanici is None:
        return Uygunluk(False, 0.0, [(False, "Katılmak için giriş yapmalısın.")])
    if kullanici["yz_mi"]:
        return Uygunluk(False, 0.0, [(False, "Yapay zeka hesapları yalnızca özet yazar; oy kullanmaz.")])

    konum_id, min_yas, max_yas = etkin_kurallar(db, konu)
    satirlar, puanlar = [], []
    if konum_id:
        kullanici_konum = etkin_konum_id(kullanici, an)
        puan = ontoloji.benzerlik(db, "konumlar", kullanici_konum, konum_id)
        puanlar.append(puan)
        satirlar.append((
            puan == 1.0,
            f"Konumun {ontoloji.yol_metni(db, 'konumlar', kullanici_konum)}; konu "
            f"{ontoloji.yol_metni(db, 'konumlar', konum_id)} sakinlerine açık (uyum %{round(puan * 100)})",
        ))
    if min_yas is not None or max_yas is not None:
        y = yas(kullanici["dogum_tarihi"], (an or zaman.simdi()).date())
        gecti = (min_yas is None or y >= min_yas) and (max_yas is None or y <= max_yas)
        puanlar.append(1.0 if gecti else 0.0)
        satirlar.append((gecti, f"Yaşın {y}; konu {yas_araligi_metni(min_yas, max_yas)} için açık"))

    if not puanlar:
        return Uygunluk(True, 1.0, [(True, "Bu konu herkese açık.")])
    return Uygunluk(all(g for g, _ in satirlar), sum(puanlar) / len(puanlar), satirlar)


# --- Oylama bağlamı ve ağırlık ---

def alanda_yazanlar(db, kategori_id):
    """Bir alanın "niş kitlesi": o ana kategorideki (alt kategorileriyle) konulara en az bir mesaj yazmış insan üyeler."""
    kok = ontoloji.atalar(db, "kategoriler", kategori_id)[0]
    alan = set(ontoloji.alt_agac(db, "kategoriler", kok))
    return {r["yazar_id"] for r in db.execute(
        """SELECT DISTINCT m.yazar_id, k.kategori_id FROM mesajlar m JOIN konular k ON k.id = m.konu_id
           JOIN kullanicilar u ON u.id = m.yazar_id WHERE u.yz_mi = 0 AND k.silindi = 0""")
        if r["kategori_id"] in alan}


def konu_baglami(konu):
    return Baglam(konu, konu["kategori_id"], konu["bilirkisi_agirlik"])


def askida_mi(kullanici, an=None):
    return bool(kullanici and kullanici["askida_bitis"] and kullanici["askida_bitis"] > zaman.metin(an or zaman.simdi()))


def katilabilir_mi(db, kullanici, baglam, an=None):
    if kullanici is None:
        return False, "Oy vermek için giriş yapmalısın."
    if kullanici["yz_mi"]:
        return False, "Yapay zeka hesapları oy kullanmaz."
    if askida_mi(kullanici, an):              # askıdaki üye yeter sayıyı da şişirmesin
        return False, "Hesabın askıda; askı bitene kadar oy kullanamazsın."
    if kullanici["id"] in baglam.haric:
        return False, "Kendi uzmanlık oylamanda oy kullanamazsın."
    if baglam.secmenler is not None and kullanici["id"] not in baglam.secmenler:
        return False, "Bu oylamaya yalnızca bu alandaki konulara yazmış üyeler katılabilir."
    if baglam.konu is None:
        return True, ""
    u = uygunluk(db, kullanici, baglam.konu, an)
    return u.katilimci, ("" if u.katilimci else "Bu konuda gözlemcisin; oy hakkın yok.")


def aktif_uzmanlik(db, kullanici_id, kategori_id, an=None):
    """Kullanıcı bu kategoride (ya da üst kategorisinde) aktif uzman mı?"""
    simdi = zaman.metin(an or zaman.simdi())
    for u in db.execute(
        "SELECT * FROM uzmanliklar WHERE kullanici_id = ? AND baslangic <= ? AND bitis > ?",
        (kullanici_id, simdi, simdi),
    ):
        if ontoloji.altinda_mi(db, "kategoriler", kategori_id, u["kategori_id"]):
            return u
    return None


def oy_agirligi(db, kullanici, baglam, an=None):
    """(ağırlık, açıklama). Oy hakkı yoksa ağırlık 0."""
    uygun, neden = katilabilir_mi(db, kullanici, baglam, an)
    if not uygun:
        return 0, neden
    if baglam.esit_agirlik:
        return 1, "Bu oylamada herkes eşit"
    uzmanlik = aktif_uzmanlik(db, kullanici["id"], baglam.kategori_id, an)
    if uzmanlik:
        alan = ontoloji.yol_metni(db, "kategoriler", uzmanlik["kategori_id"])
        return baglam.uzman_agirlik, f"Uzman ({alan})"
    return 1, "Üye"


def oy_hakki_olanlar(db, baglam, an=None):
    kullanicilar = db.execute("SELECT * FROM kullanicilar").fetchall()
    return [k for k in kullanicilar if katilabilir_mi(db, k, baglam, an)[0]]
