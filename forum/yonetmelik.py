"""Yönetmelik: forumun anayasası.

* Parametreler (eşikler, süreler, yeter sayı...) veritabanında durur ve oylamayla değişir.
* Maddeler dört türdür: TEMEL_HAK (korunan), USUL, DENETIM (otomatik uygulanır), BEYAN (topluluk normu).
* Denetim maddeleri ontolojiyi kullanarak konuları ve mesajları denetler (ENGEL / UYARI / KAPALI); denetim motoru
  denetim.py'dedir (Chain of Responsibility). Bu modül maddelerin metnini, parametre deposunu ve değişiklik akışını taşır.
"""
import json
import re

from . import ayarlar, denetim, gunluk, zaman
from .hatalar import KuralHatasi
from .metin import yuzde

# (kod, tür, başlık, metin şablonu, ciddiyet, korunan). {PARAMETRE} yerine parametrenin güncel değeri yazılır.
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
     "Konular 7 temel alanda ve Genel kategoride açılır. Genel kategori her konuya açıktır. Her üye yeni bir ana ya da alt "
     "kategori önerebilir; öneri bütün üyelerin oyuna sunulur ve {ESIK_KATEGORI} ile kabul edilirse kategori eklenir. "
     "Bu oylamada herkesin oyu 1 sayılır.", None, False),
    # D1 varsayılan olarak yalnızca uyarır; kesinlik yayın ölçütünün altında kaldığı için (docs/analiz.md 6.5 ve 11).
    # Topluluk yönetmelik oylamasıyla ENGEL'e çekebilir.
    ("D1", "DENETIM", "Saygılı dil", "Konular ve mesajlar hakaret içeremez.", "UYARI", False),
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
    ("D7", "DENETIM", "Açıklık", "Konunun açıklaması derdini anlaşılır biçimde anlatmalıdır (en az 40 karakter).",
     "UYARI", False),
    ("B1", "BEYAN", "Tartışma kültürü", "Kişilere değil fikirlere karşı çıkılır.", None, False),
]

MADDE_TURLERI = {"TEMEL_HAK": "Temel haklar", "USUL": "Usul", "DENETIM": "Denetim", "BEYAN": "Beyan"}
CIDDIYETLER = {"ENGEL": "Engeller", "UYARI": "Uyarır", "KAPALI": "Kapalı"}


def yukle(db):
    """İlk kurulumda parametreleri ve maddeleri yükler. Kurulu veritabanını koddaki tanımlarla eşitler: eksik
    parametre ve madde eklenir, artık kullanılmayan parametre silinir, açıklama ve madde metinleri güncellenir.
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
        d["metin_goster"] = re.sub(r"\{([A-Z][A-Z0-9_]*)\}", lambda e: parametre_metni(db, e.group(1)), m["metin"])
        liste.append(d)
    return liste


def ciddiyet(db, kod):
    if "ciddiyet" not in db.onbellek:
        db.onbellek["ciddiyet"] = {r["kod"]: r["ciddiyet"] for r in
                                   db.execute("SELECT kod, ciddiyet FROM yonetmelik_maddeleri WHERE tur = 'DENETIM'")}
    return db.onbellek["ciddiyet"].get(kod, "KAPALI")


def madde_basligi(db, kod):
    r = db.execute("SELECT baslik FROM yonetmelik_maddeleri WHERE kod = ?", (kod,)).fetchone()
    return r["baslik"] if r else kod


# --- Yönetmelik değişikliği ---

def _aralik_dogrula(db, p, yeni):
    """Sayı ve oran parametreleri: türü, anlamlı aralığı ve parametreler arası tutarlılık."""
    alt, ust = ayarlar.PARAMETRE_ARALIKLARI[p["kod"]]
    try:
        deger_ = float(yeni) if p["tur"] == "oran" else int(yeni)
    except ValueError:
        raise KuralHatasi("Oran ondalık sayı olmalı (ör. 0.25)." if p["tur"] == "oran" else "Geçerli bir tam sayı gir.")
    if not alt <= deger_ <= ust:
        raise KuralHatasi(f"{p['aciklama']}: değer {deger_metni(p['tur'], alt)} ile {deger_metni(p['tur'], ust)} "
                          "arasında olmalı.")
    # Eleme eşiği ezici üstünlükten küçük olmalı; yoksa eleme turundan geçen her fikir zaten kazanmış olurdu.
    elemeler = [deger(db, k) for k in ayarlar.ELEME_PARAMETRELERI.values() if k != p["kod"]]
    if p["kod"] in ayarlar.ELEME_PARAMETRELERI.values() and deger_ >= deger(db, "ESIK_EZICI"):
        raise KuralHatasi("Eleme eşiği ezici üstünlük oranından küçük olmalı.")
    if p["kod"] == "ESIK_EZICI" and any(e >= deger_ for e in elemeler):
        raise KuralHatasi("Ezici üstünlük oranı bütün eleme eşiklerinden büyük olmalı.")


def degisiklik_dogrula(db, veri):
    """Değişiklik önerisini doğrular; (açıklama, korunan_mu) döndürür."""
    tur = veri.get("tur")
    if tur == "PARAMETRE":
        p = _parametreler(db).get(veri.get("kod"))
        if not p:
            raise KuralHatasi("Parametre bulunamadı.")
        yeni = str(veri.get("yeni", "")).strip()
        if p["tur"] == "esik":
            if yeni not in ayarlar.ESIKLER:
                raise KuralHatasi("Geçersiz eşik.")
        else:
            _aralik_dogrula(db, p, yeni)
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
        kaba = denetim.kaba_ifadeler(f"{baslik} {metin}")
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
    denetim.mesaj_denetle(db, gerekce)
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
