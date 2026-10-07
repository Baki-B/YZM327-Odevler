"""Yönetmelik: forumun anayasası.

* Parametreler (eşikler, süreler, yeter sayı...) veritabanında durur ve oylamayla değişir.
* Maddeler dört türdür: TEMEL_HAK (korunan), USUL, DENETIM (otomatik uygulanır), BEYAN (topluluk normu).
* Denetim maddeleri ontolojiyi kullanarak konuları ve mesajları denetler (ENGEL / UYARI / KAPALI).
"""
import json
import re

from . import ayarlar, gunluk, ontoloji, zaman
from .hatalar import KuralHatasi
from .metin import yuzde

KABA_IFADELER = ["aptal", "salak", "gerizekal", "geri zekal", "cahil", "ahmak", "beyinsiz", "serefsiz",
                 "haysiyetsiz", "mankafa", "dangalak", "embesil"]
KISISEL_VERI_DESENLERI = {
    "telefon numarası": re.compile(r"(\+90|0)?\s?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}"),
    "T.C. kimlik numarası": re.compile(r"\b[1-9]\d{10}\b"),
    "e-posta adresi": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
}

# (kod, tür, başlık, metin şablonu, ciddiyet, korunan). {KOD} yerine parametrenin güncel değeri yazılır.
MADDELER = [
    ("T1", "TEMEL_HAK", "Kurallar karşısında eşitlik",
     "Kurallar her üyeye aynı uygulanır. Bir konunun katılım kuralını sağlayan her üye o konuda yazabilir, "
     "fikir verebilir ve oy kullanabilir. Yöneticiler yalnızca siteyi yönetir; kararlara karışamaz.", None, True),
    ("T2", "TEMEL_HAK", "Söz hakkı",
     "Mesajlar silinmez. Düzenlenen mesajın eski hâli görünür kalır. Bir mesaj ancak {ESIK_MESAJ_SILME} ile "
     "gizlenebilir; yerinde bir not kalır.", None, True),
    ("T3", "TEMEL_HAK", "Fikir verme ve itiraz hakkı",
     "Her katılımcı her konuda bir fikir yazabilir; fikirler aynı oylamada yarışır. Karara katılmayan her üye "
     "yeni bir itiraz konusu açabilir.", None, True),
    ("T4", "TEMEL_HAK", "Gizli oy",
     "Oylar gizlidir. Her oy kayıt defterine, sahibinin makbuzla doğrulayabileceği bir özet olarak yazılır. "
     "Uzman oyları açıktır ve gerekçe ister.", None, True),
    ("T5", "TEMEL_HAK", "Güç sınırı",
     "Kimse {MAX_DEVIR} oydan fazla devredilmiş oy taşıyamaz. Bir ana kategoride en fazla {UZMAN_KONTENJAN} uzman "
     "olabilir.", None, True),
    ("U1", "USUL", "Konu ve tartışma",
     "Her üye konu açabilir; alt konular da aynı yoldan geçer. Konu açılınca {SURE_TARTISMA_SAAT} saat tartışılır. "
     "Sonra fikir oylaması başlar; oylama sürerken tartışma devam eder.", None, False),
    ("U2", "USUL", "Fikirler",
     "Her katılımcı bir konuda en fazla bir fikir yazabilir. Fikirler tartışma süresince ve 1. tur bitene kadar "
     "yazılabilir.", None, False),
    ("U3", "USUL", "Eleme turları",
     "Fikir oylaması en fazla 5 turdur. 1. tur {SURE_TUR1_SAAT} saat, sonraki turlar {SURE_TUR_SAAT} saat sürer. "
     "Tur bitince oranı 1. turda {ELEME_TUR1}, 2. turda {ELEME_TUR2}, 3. turda {ELEME_TUR3}, 4. turda {ELEME_TUR4} "
     "altında kalan fikirler elenir. Geriye tek fikir kalırsa o kabul edilir. 5. turda en çok oy alan fikir kabul "
     "edilir. Herhangi bir turda {ESIK_EZICI} ya da daha fazla oy alan fikir hemen kabul edilir.", None, False),
    ("U4", "USUL", "Oy ağırlığı ve oran",
     "Normal oy 1, uzmanın kendi alanındaki oyu {UZMAN_AGIRLIK} sayılır. Bir fikrin oranı iki ayrı hesaplanır: "
     "ağırlıklı oylarda ve oy veren kişi sayısında. İkisinden küçük olan geçerlidir. Çekimser oylar toplamda "
     "sayılır.", None, False),
    ("U5", "USUL", "Yeter sayı",
     "Bir oylamanın geçerli olması için oy hakkı olanların en az {YETER_SAYI_ORANI} kadarı ve en az {MIN_KATILIM} "
     "kişi oy vermelidir. Yeter sayı sağlanmazsa konu sonuçsuz kapanır.", None, False),
    ("U6", "USUL", "Konu düzenleme ve kaldırma",
     "Konuyu açan kişi tartışma süresince metni düzenleyebilir; eski hâli görünür kalır. Konunun kaldırılması "
     "{ESIK_KONU_SILME} ister.", None, False),
    ("U7", "USUL", "Uzmanlık",
     "Uzmanlık bir alan için verilir ve {UZMAN_SURE_GUN} gün sürer. Aday önce ön şartları sağlamalıdır: o alanda en az "
     "{UZMAN_MIN_MESAJ} mesaj ve en az {UZMAN_MIN_KONU} farklı konuya katılım. Sonra o alanda yazmış üyeler oylar; "
     "kabul için {ESIK_UZMANLIK} gerekir. Bu oylamada herkesin oyu 1 sayılır. Yapay zeka hesapları da aynı şartlarla "
     "aday gösterilebilir.", None, False),
    ("U8", "USUL", "Yönetmelik değişikliği",
     "Yönetmelik {ESIK_YONETMELIK} ile değişir. Temel hak maddelerine ve korunan parametrelere dokunan "
     "değişiklikler {ESIK_TEMEL_HAK} ister. Bu oylamada herkesin oyu 1 sayılır.", None, False),
    ("U9", "USUL", "Adres değişikliği",
     "Yeni adres {ADRES_BEKLEME_GUN} gün sonra geçerli olur. Bu süre, sırf bir konuya katılmak için adres "
     "değiştirmeyi önler.", None, False),
    ("U10", "USUL", "Şikayet",
     "Üyeler bir mesajı ya da konuyu şikayet edebilir. Şikayet, en az {SIKAYET_TABANI} farklı üye aynı içeriği "
     "şikayet edince yöneticilere ulaşır. Yönetici içeriği kendisi gizleyemez; oylamaya sunar.", None, False),
    ("U11", "USUL", "Kategoriler",
     "Konular 7 temel alanda ve Genel kategoride açılır. Genel her konuya açıktır. Her üye yeni bir ana ya da alt "
     "kategori önerebilir; öneri bütün üyelerin oyuna sunulur ve {ESIK_KATEGORI} ile kabul edilirse kategori eklenir. "
     "Bu oylamada herkesin oyu 1 sayılır.", None, False),
    ("D1", "DENETIM", "Saygılı dil", "Konular ve mesajlar hakaret içeremez.", "ENGEL", False),
    ("D2", "DENETIM", "Kişisel veri",
     "Telefon numarası, T.C. kimlik numarası, e-posta adresi gibi kişisel veriler paylaşılamaz.", "ENGEL", False),
    ("D3", "DENETIM", "Kategoriye uygunluk",
     "Konunun metni seçilen kategoriyle ilgili kavramlar içermelidir.", "UYARI", False),
    ("D4", "DENETIM", "Konum tutarlılığı",
     "Metinde bir yer adı geçiyorsa katılım kuralı o yerle uyumlu olmalıdır.", "UYARI", False),
    ("D5", "DENETIM", "Benzer konu",
     "Aynı konuda açık bir konu varsa yenisi yerine o konu kullanılmalıdır.", "UYARI", False),
    ("D6", "DENETIM", "Alt konu ilişkisi",
     "Alt konu, üst konuyla aynı alanda olmalıdır.", "UYARI", False),
    ("D7", "DENETIM", "Açıklık", "Konunun açıklaması derdi anlaşılır biçimde anlatmalıdır (en az 40 karakter).",
     "UYARI", False),
    ("B1", "BEYAN", "Tartışma kültürü", "Kişilere değil fikirlere karşı çıkılır.", None, False),
]

MADDE_TURLERI = {"TEMEL_HAK": "Temel haklar", "USUL": "Usul", "DENETIM": "Denetim", "BEYAN": "Beyan"}
CIDDIYETLER = {"ENGEL": "Engeller", "UYARI": "Uyarır", "KAPALI": "Kapalı"}


def yukle(db):
    """İlk kurulumda parametreleri ve maddeleri yükler. Kurulu veritabanında koddaki tanımlarla eşitler:
    eksik parametre ve madde eklenir, kalkan parametre silinir, açıklama ve madde metinleri tazelenir.
    Oylamayla değişmiş değerlere, ciddiyetlere ve sonradan eklenen beyan maddelerine dokunulmaz."""
    mevcut = {r[0] for r in db.execute("SELECT kod FROM parametreler")}
    for kod, deger_, tur, aciklama, korunan in ayarlar.VARSAYILAN_PARAMETRELER:
        if kod in mevcut:
            db.execute("UPDATE parametreler SET aciklama = ?, korunan = ? WHERE kod = ?", (aciklama, int(korunan), kod))
        else:
            db.execute("INSERT INTO parametreler (kod, deger, tur, aciklama, korunan) VALUES (?, ?, ?, ?, ?)",
                       (kod, deger_, tur, aciklama, int(korunan)))
    gecerli = {p[0] for p in ayarlar.VARSAYILAN_PARAMETRELER}
    for kod in mevcut - gecerli:
        db.execute("DELETE FROM parametreler WHERE kod = ?", (kod,))

    mevcut = {r[0] for r in db.execute("SELECT kod FROM yonetmelik_maddeleri")}
    for kod, tur, baslik, metin, ciddiyet_, korunan in MADDELER:
        if kod in mevcut:
            db.execute("UPDATE yonetmelik_maddeleri SET baslik = ?, metin = ?, korunan = ? WHERE kod = ?",
                       (baslik, metin, int(korunan), kod))
        else:
            db.execute("INSERT INTO yonetmelik_maddeleri (kod, tur, baslik, metin, ciddiyet, korunan) "
                       "VALUES (?, ?, ?, ?, ?, ?)", (kod, tur, baslik, metin, ciddiyet_, int(korunan)))
    db.onbellek.pop("parametreler", None)
    db.onbellek.pop("ciddiyet", None)


# --- Parametreler ---

def _parametreler(db):
    if "parametreler" not in db.onbellek:
        db.onbellek["parametreler"] = {r["kod"]: dict(r) for r in db.execute("SELECT * FROM parametreler")}
    return db.onbellek["parametreler"]


def deger(db, kod):
    p = _parametreler(db)[kod]
    if p["tur"] == "sayi":
        return int(p["deger"])
    if p["tur"] == "oran":
        return float(p["deger"])
    return p["deger"]


def deger_metni(tur, deger_):
    if tur == "esik":
        return ayarlar.ESIKLER[deger_]["ad"].lower() + f" ({ayarlar.ESIKLER[deger_]['kisa']})"
    if tur == "oran":
        return yuzde(float(deger_))
    return str(deger_)


def parametre_metni(db, kod):
    p = _parametreler(db)[kod]
    return deger_metni(p["tur"], p["deger"])


def parametre_listesi(db):
    return list(_parametreler(db).values())


# --- Maddeler ---

def maddeler(db):
    liste = []
    for m in db.execute("SELECT * FROM yonetmelik_maddeleri ORDER BY CASE tur WHEN 'TEMEL_HAK' THEN 1 WHEN 'USUL' THEN 2 WHEN 'DENETIM' THEN 3 ELSE 4 END, CAST(substr(kod, 2) AS INTEGER)"):
        d = dict(m)
        d["metin_goster"] = re.sub(r"\{([A-Z_]+)\}", lambda e: parametre_metni(db, e.group(1)), m["metin"])
        liste.append(d)
    return liste


def ciddiyet(db, kod):
    if "ciddiyet" not in db.onbellek:
        db.onbellek["ciddiyet"] = {r["kod"]: r["ciddiyet"] for r in
                                   db.execute("SELECT kod, ciddiyet FROM yonetmelik_maddeleri WHERE tur = 'DENETIM'")}
    return db.onbellek["ciddiyet"].get(kod, "KAPALI")


def _madde_basligi(db, kod):
    r = db.execute("SELECT baslik FROM yonetmelik_maddeleri WHERE kod = ?", (kod,)).fetchone()
    return r["baslik"] if r else kod


# --- Denetim ---

def kaba_ifadeler(metin):
    katli = ontoloji.katla(metin)
    return [k for k in KABA_IFADELER if k in katli]


def kisisel_veriler(metin):
    return [ad for ad, desen in KISISEL_VERI_DESENLERI.items() if desen.search(metin)]


def _bulgu(db, kod, gecti, mesaj):
    return {"kod": kod, "baslik": _madde_basligi(db, kod), "ciddiyet": ciddiyet(db, kod), "gecti": gecti,
            "mesaj": mesaj}


def denetle(db, baslik, aciklama, kategori_id, konum_id=None, ust=None, haric_konu_id=None):
    """Bir konuyu yönetmeliğin denetim maddelerine göre denetler ve bir rapor döndürür."""
    metin = f"{baslik}\n{aciklama}"
    bulgular = []

    kaba = kaba_ifadeler(metin)
    bulgular.append(_bulgu(db, "D1", not kaba, "Kaba ifade bulunamadı." if not kaba
                           else f"Kaba ifade var: {', '.join(kaba)}. Kişiye değil fikre yönelik yaz."))
    kisisel = kisisel_veriler(metin)
    bulgular.append(_bulgu(db, "D2", not kisisel, "Kişisel veri bulunamadı." if not kisisel
                           else f"Metinde {', '.join(kisisel)} var. Kişisel verileri kaldır."))

    terimler, _ = ontoloji.kategori_iliskisi(db, metin, kategori_id)
    oneri_id, oneri_terimler = ontoloji.en_uygun_kategori(db, metin)
    kategori_adi = ontoloji.yol_metni(db, "kategoriler", kategori_id)
    genel = ontoloji.genel_mi(db, kategori_id)
    if genel:
        terimler, oneri_id = ["genel"], None
        mesaj = f"“{kategori_adi}” her konuya açık."
    elif terimler:
        mesaj = f"“{kategori_adi}” kavramlarıyla ilişkili: {', '.join(terimler[:6])}."
    elif oneri_id:
        mesaj = (f"“{kategori_adi}” ile ilgili bir kavram yok. Metin daha çok "
                 f"“{ontoloji.yol_metni(db, 'kategoriler', oneri_id)}” kategorisine uyuyor ({', '.join(oneri_terimler[:4])}).")
    else:
        mesaj = "Metin hiçbir kategoriyle eşleşmedi. Açıklamaya konunun alanıyla ilgili ayrıntı ekle."
    bulgular.append(_bulgu(db, "D3", bool(terimler), mesaj))
    if genel:
        terimler = []

    yerler = ontoloji.metindeki_yerler(db, metin)
    if not yerler:
        bulgulu, mesaj = True, "Metinde belirli bir yer adı geçmiyor."
    elif konum_id is None:
        adlar = ", ".join(ontoloji.yol_metni(db, "konumlar", y) for y in yerler[:3])
        bulgulu, mesaj = False, (f"Metinde {adlar} geçiyor ama katılım herkese açık. Konu yalnızca orayı "
                                 "ilgilendiriyorsa katılımı oranın sakinleriyle sınırlayabilirsin.")
    else:
        uyumsuz = [y for y in yerler if not (ontoloji.altinda_mi(db, "konumlar", y, konum_id)
                                            or ontoloji.altinda_mi(db, "konumlar", konum_id, y))]
        bulgulu = not uyumsuz
        mesaj = ("Metindeki yer adları katılım kuralıyla uyumlu." if bulgulu else
                 f"Katılım {ontoloji.yol_metni(db, 'konumlar', konum_id)} sakinlerine açık ama metinde "
                 f"{', '.join(ontoloji.yol_metni(db, 'konumlar', y) for y in uyumsuz[:3])} geçiyor.")
    bulgular.append(_bulgu(db, "D4", bulgulu, mesaj))

    benzer = None
    for k in db.execute("SELECT id, baslik FROM konular WHERE silindi = 0 AND durum != 'SONUCSUZ' AND id != ?",
                        (haric_konu_id or 0,)):
        oran = ontoloji.benzerlik_orani(baslik, k["baslik"])
        if oran >= 0.5 and (benzer is None or oran > benzer[1]):
            benzer = (k, oran)
    bulgular.append(_bulgu(db, "D5", benzer is None, "Benzer bir konu bulunamadı." if benzer is None else
                           f"#{benzer[0]['id']} “{benzer[0]['baslik']}” ile %{round(benzer[1] * 100)} benzer."))

    if ust is not None:
        ayni_alan = (ontoloji.altinda_mi(db, "kategoriler", kategori_id, ust["kategori_id"])
                     or ontoloji.altinda_mi(db, "kategoriler", ust["kategori_id"], kategori_id))
        ortak = ontoloji.anlamli_kelimeler(metin) & ontoloji.anlamli_kelimeler(f"{ust['baslik']} {ust['aciklama']}")
        gecti = ayni_alan or bool(ortak)
        bulgular.append(_bulgu(db, "D6", gecti, "Üst konuyla aynı alanda." if ayni_alan else
                               (f"Üst konuyla ortak kavramlar: {', '.join(sorted(ortak)[:5])}." if ortak else
                                "Üst konuyla alanı da kavramları da ortak değil.")))

    kisa = len(aciklama.strip()) < 40
    bulgular.append(_bulgu(db, "D7", not kisa, "Açıklama yeterli uzunlukta." if not kisa else
                           "Açıklama çok kısa. Derdini ve nedenini anlat."))

    etkin = [b for b in bulgular if b["ciddiyet"] != "KAPALI"]
    return {
        "bulgular": bulgular,
        "engel": [b for b in etkin if not b["gecti"] and b["ciddiyet"] == "ENGEL"],
        "uyarilar": [b for b in etkin if not b["gecti"] and b["ciddiyet"] == "UYARI"],
        "puan": round(100 * sum(1 for b in etkin if b["gecti"]) / len(etkin)) if etkin else 100,
        "onerilen_kategori": oneri_id if not terimler and not genel else None,
        "zaman": zaman.simdi_metin(),
    }


def mesaj_denetle(db, icerik):
    """Mesajlar için sadece ENGEL maddeleri uygulanır (hakaret, kişisel veri)."""
    sorunlar = []
    if ciddiyet(db, "D1") == "ENGEL" and kaba_ifadeler(icerik):
        sorunlar.append("Mesajında kaba ifade var; kişiye değil fikre yönelik yaz.")
    if ciddiyet(db, "D2") == "ENGEL" and kisisel_veriler(icerik):
        sorunlar.append("Mesajında kişisel veri var (" + ", ".join(kisisel_veriler(icerik)) + "); kaldırıp tekrar gönder.")
    if sorunlar:
        raise KuralHatasi(" ".join(sorunlar))


# --- Yönetmelik değişikliği ---

def degisiklik_dogrula(db, veri):
    """Değişiklik önerisini doğrular; (açıklama, korunan_mu) döndürür."""
    tur = veri.get("tur")
    if tur == "PARAMETRE":
        p = _parametreler(db).get(veri.get("kod"))
        if not p:
            raise KuralHatasi("Parametre bulunamadı.")
        yeni = str(veri.get("yeni", "")).strip()
        if p["tur"] == "esik" and yeni not in ayarlar.ESIKLER:
            raise KuralHatasi("Geçersiz eşik.")
        if p["tur"] == "oran":
            try:
                if not 0.01 <= float(yeni) <= 1:
                    raise ValueError
            except ValueError:
                raise KuralHatasi("Oran 0.01 ile 1 arasında olmalı (ör. 0.25).")
        if p["tur"] == "sayi":
            try:
                if not 0 <= int(yeni) <= 10000:
                    raise ValueError
            except ValueError:
                raise KuralHatasi("Geçerli bir sayı gir.")
        if yeni == p["deger"]:
            raise KuralHatasi("Yeni değer mevcut değerle aynı.")
        veri["yeni"] = yeni
        return (f"{p['aciklama']}: {deger_metni(p['tur'], p['deger'])} → {deger_metni(p['tur'], yeni)}",
                bool(p["korunan"]))
    if tur == "DENETIM":
        m = db.execute("SELECT * FROM yonetmelik_maddeleri WHERE kod = ? AND tur = 'DENETIM'",
                       (veri.get("kod"),)).fetchone()
        if not m or veri.get("yeni") not in CIDDIYETLER or veri["yeni"] == m["ciddiyet"]:
            raise KuralHatasi("Geçersiz denetim değişikliği.")
        return f"{m['kod']} {m['baslik']}: {CIDDIYETLER[m['ciddiyet']]} → {CIDDIYETLER[veri['yeni']]}", False
    if tur == "BEYAN":
        baslik, metin = (veri.get("baslik") or "").strip(), (veri.get("metin") or "").strip()
        if not 5 <= len(baslik) <= 80 or not 20 <= len(metin) <= 1000:
            raise KuralHatasi("Beyan maddesinin başlığı 5–80, metni 20–1000 karakter olmalı.")
        kaba = kaba_ifadeler(metin + baslik)
        if kaba:
            raise KuralHatasi("Beyan maddesi kaba ifade içeremez.")
        veri.update(baslik=baslik, metin=metin)
        return f"Yeni beyan maddesi: {baslik}", False
    raise KuralHatasi("Geçersiz değişiklik türü.")


def degisiklik_teklif_et(db, kullanici, veri, gerekce):
    """Yönetmelik değişikliğini oylamaya sunar. Korunan maddeye dokunuyorsa ESIK_TEMEL_HAK uygulanır."""
    from . import oylama
    if kullanici["yz_mi"]:
        raise KuralHatasi("Yapay zeka hesapları yönetmelik değişikliği öneremez.")
    gerekce = (gerekce or "").strip()
    if len(gerekce) < 20:
        raise KuralHatasi("Değişikliğin gerekçesini en az 20 karakterle yaz.")
    mesaj_denetle(db, gerekce)
    veri = dict(veri)
    aciklama, korunan = degisiklik_dogrula(db, veri)
    veri["aciklama"] = aciklama
    veri["korunan"] = korunan
    esik = deger(db, "ESIK_TEMEL_HAK" if korunan else "ESIK_YONETMELIK")
    return oylama.teklif_ac(db, "YONETMELIK", kullanici["id"], gerekce=gerekce, veri=veri, esik=esik)


def degisikligi_uygula(db, veri):
    simdi = zaman.simdi_metin()
    if veri["tur"] == "PARAMETRE":
        db.execute("UPDATE parametreler SET deger = ?, degisme = ? WHERE kod = ?", (veri["yeni"], simdi, veri["kod"]))
    elif veri["tur"] == "DENETIM":
        db.execute("UPDATE yonetmelik_maddeleri SET ciddiyet = ?, degisme = ? WHERE kod = ?",
                   (veri["yeni"], simdi, veri["kod"]))
    else:
        sira = db.execute("SELECT COUNT(*) FROM yonetmelik_maddeleri WHERE tur = 'BEYAN'").fetchone()[0] + 1
        db.execute("INSERT INTO yonetmelik_maddeleri (kod, tur, baslik, metin, degisme) VALUES (?, 'BEYAN', ?, ?, ?)",
                   (f"B{sira}", veri["baslik"], veri["metin"], simdi))
    db.onbellek.pop("parametreler", None)
    db.onbellek.pop("ciddiyet", None)
    gunluk.kaydet(db, None, "YONETMELIK", "Yönetmelik değişti: " + json.dumps(veri, ensure_ascii=False))
