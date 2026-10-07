"""Ontoloji: kavramlar ve aralarındaki ilişkiler.

Konum:    Türkiye › Bölge › İl › İlçe  (Kadıköy'de oturan, "İstanbul" konusuna uygundur)
Kategori: Alan › Alt alan             ("Sağlık" uzmanı, "Sağlık › Beslenme" konularında da uzmandır)
Kavramlar: her kategorinin terimleri   (yönetmelik denetimi bir metnin hangi kategoriye ait olduğunu bununla ölçer)
"""
import re

BOLGELER = {
    "Marmara": ["Balıkesir", "Bilecik", "Bursa", "Çanakkale", "Edirne", "İstanbul",
                "Kırklareli", "Kocaeli", "Sakarya", "Tekirdağ", "Yalova"],
    "Ege": ["Afyonkarahisar", "Aydın", "Denizli", "İzmir", "Kütahya", "Manisa", "Muğla", "Uşak"],
    "Akdeniz": ["Adana", "Antalya", "Burdur", "Hatay", "Isparta", "Kahramanmaraş", "Mersin", "Osmaniye"],
    "İç Anadolu": ["Aksaray", "Ankara", "Çankırı", "Eskişehir", "Karaman", "Kayseri", "Kırıkkale",
                   "Kırşehir", "Konya", "Nevşehir", "Niğde", "Sivas", "Yozgat"],
    "Karadeniz": ["Amasya", "Artvin", "Bartın", "Bayburt", "Bolu", "Çorum", "Düzce", "Giresun",
                  "Gümüşhane", "Karabük", "Kastamonu", "Ordu", "Rize", "Samsun", "Sinop", "Tokat",
                  "Trabzon", "Zonguldak"],
    "Doğu Anadolu": ["Ağrı", "Ardahan", "Bingöl", "Bitlis", "Elazığ", "Erzincan", "Erzurum", "Hakkari",
                     "Iğdır", "Kars", "Malatya", "Muş", "Tunceli", "Van"],
    "Güneydoğu Anadolu": ["Adıyaman", "Batman", "Diyarbakır", "Gaziantep", "Kilis", "Mardin", "Siirt",
                          "Şanlıurfa", "Şırnak"],
}

ILCELER = {
    "İstanbul": ["Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy",
                 "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu",
                 "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt", "Eyüpsultan", "Fatih",
                 "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", "Kartal", "Küçükçekmece",
                 "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Silivri", "Sultanbeyli", "Sultangazi",
                 "Şile", "Şişli", "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu"],
    "Ankara": ["Akyurt", "Altındağ", "Ayaş", "Bala", "Beypazarı", "Çamlıdere", "Çankaya", "Çubuk",
               "Elmadağ", "Etimesgut", "Evren", "Gölbaşı", "Güdül", "Haymana", "Kahramankazan",
               "Kalecik", "Keçiören", "Kızılcahamam", "Mamak", "Nallıhan", "Polatlı", "Pursaklar",
               "Sincan", "Şereflikoçhisar", "Yenimahalle"],
    "İzmir": ["Aliağa", "Balçova", "Bayındır", "Bayraklı", "Bergama", "Beydağ", "Bornova", "Buca",
              "Çeşme", "Çiğli", "Dikili", "Foça", "Gaziemir", "Güzelbahçe", "Karabağlar", "Karaburun",
              "Karşıyaka", "Kemalpaşa", "Kınık", "Kiraz", "Konak", "Menderes", "Menemen", "Narlıdere",
              "Ödemiş", "Seferihisar", "Selçuk", "Tire", "Torbalı", "Urla"],
}

# 7 temel alan + Genel. Kullanıcılar oylamayla yeni ana ya da alt kategori ekleyebilir (kategoriler.py).
KATEGORILER = {
    "Bilim": ["Fizik", "Biyoloji", "Çevre ve İklim"],
    "Sağlık": ["Beslenme", "Spor", "Ruh Sağlığı"],
    "Siyaset": ["Yerel Yönetim", "Ulaşım", "Kamu Politikası"],
    "Eğitim": ["Üniversite", "Lise", "Akran Öğrenmesi", "Kampüs Yaşamı"],
    "Teknoloji": ["Yazılım", "Yapay Zeka", "Donanım"],
    "Ekonomi": ["Kişisel Finans", "İş ve Kariyer", "Girişimcilik"],
    "Kültür ve Sanat": ["Edebiyat", "Müzik", "Sinema"],
    "Genel": [],
}
KATEGORI_SURUMU = "2"   # site_ayarlari'nda tutulur; eski kurulumların kategori ağacı bir kez yeniye taşınır

# Eski ağaçtan (Şehir, Kampüs Yaşamı) yeniye: (eski ana, eski alt) → (yeni ana, yeni alt). Konular, uzmanlıklar ve
# devirler yeni kategoriye bağlanır; hiçbir konu kaybolmaz.
ESKI_KATEGORILER = {
    ("Şehir", None): ("Siyaset", "Yerel Yönetim"),
    ("Şehir", "Ulaşım"): ("Siyaset", "Ulaşım"),
    ("Şehir", "Çevre"): ("Bilim", "Çevre ve İklim"),
    ("Şehir", "Kentsel Dönüşüm"): ("Siyaset", "Yerel Yönetim"),
    ("Kampüs Yaşamı", None): ("Eğitim", "Kampüs Yaşamı"),
    ("Kampüs Yaşamı", "Yemekhane"): ("Eğitim", "Kampüs Yaşamı"),
    ("Kampüs Yaşamı", "Kulüpler"): ("Eğitim", "Kampüs Yaşamı"),
    ("Kampüs Yaşamı", "Yurtlar"): ("Eğitim", "Kampüs Yaşamı"),
}

# Kavram terimleri (Türkçe karakterleri katlanmış kök biçimleri). 3 harf ve altı terimler tam kelime eşleşir.
# Topluluğun eklediği kategorilerin terimleri veritabanında (kategoriler.kavramlar) durur.
KAVRAMLAR = {
    "Bilim": ["bilim", "arastirma", "deney", "bilimsel", "makale", "teori", "kesif", "laboratuvar", "bilim insan"],
    "Fizik": ["fizik", "enerji", "kuantum", "uzay", "astronomi", "gezegen", "teleskop", "gokyuzu", "yildiz"],
    "Biyoloji": ["biyoloji", "hucre", "genetik", "dna", "evrim", "canli", "hayvan", "bitki", "tur"],
    "Çevre ve İklim": ["cevre", "iklim", "geri donusum", "atik", "yesil", "karbon", "kirlilik", "agac", "plastik",
                       "surdurulebilir", "tek kullanimlik"],
    "Sağlık": ["saglik", "hastane", "doktor", "hekim", "tedavi", "hastalik", "ilac", "saglikli"],
    "Beslenme": ["beslen", "yemek", "menu", "diyet", "protein", "vitamin", "etsiz", "etli", "vegan",
                 "vejetaryen", "kalori", "gida", "sebze", "baklagil", "icecek", "kafein"],
    "Spor": ["spor", "egzersiz", "antrenman", "futbol", "basketbol", "kosu", "fitness", "sporcu", "mac"],
    "Ruh Sağlığı": ["ruh sagligi", "psikolo", "stres", "kaygi", "terapi", "depresyon", "danisma"],
    "Siyaset": ["siyaset", "politika", "secim", "meclis", "yasa", "kanun", "hukuk", "demokrasi", "parti", "temsil"],
    "Yerel Yönetim": ["belediye", "mahalle", "sehir", "kent", "muhtar", "park", "kentsel donusum", "deprem", "konut",
                      "genclik meclisi"],
    "Ulaşım": ["ulasim", "otobus", "metro", "vapur", "tramvay", "trafik", "bisiklet", "durak", "hat",
               "hatlar", "indirim", "toplu tasima", "sefer", "iskele", "aktarma", "ring", "servis"],
    "Kamu Politikası": ["kamu", "vergi", "sosyal", "destek", "duzenleme", "politika", "yonetmelik"],
    "Eğitim": ["egitim", "ders", "ogrenci", "ogretmen", "okul", "sinav", "mufredat", "ogren", "hoca", "odev"],
    "Üniversite": ["universite", "fakulte", "kampus", "bolum", "donem", "final", "vize", "akademik",
                   "kutuphane", "rektor"],
    "Lise": ["lise", "sinif", "yks", "lgs", "mezun"],
    "Akran Öğrenmesi": ["akran", "calisma grubu", "mentor", "birlikte ogren", "ogretme"],
    "Kampüs Yaşamı": ["kampus", "yemekhane", "kafeterya", "ogun", "kulup", "etkinlik", "topluluk", "toplanti", "yurt",
                      "barinma", "senlik"],
    "Teknoloji": ["teknoloji", "bilgisayar", "internet", "dijital", "uygulama"],
    "Yazılım": ["yazilim", "kod", "program", "python", "java", "flask", "spring", "algoritma",
                "veritabani", "git", "framework", "web"],
    "Yapay Zeka": ["yapay zeka", "yz", "makine ogren", "model", "llm", "sinir agi", "sohbet botu"],
    "Donanım": ["donanim", "islemci", "cihaz", "elektronik", "devre"],
    "Ekonomi": ["ekonomi", "fiyat", "enflasyon", "para", "maas", "butce", "piyasa", "ucret", "zam", "pahali"],
    "Kişisel Finans": ["birikim", "harcama", "kredi", "burs", "kira", "tasarruf", "yatirim", "borc"],
    "İş ve Kariyer": ["kariyer", "staj", "mulakat", "calisan", "isveren", "meslek", "is ilani", "ozgecmis"],
    "Girişimcilik": ["girisim", "startup", "yatirimci", "sirket", "isletme"],
    "Kültür ve Sanat": ["kultur", "sanat", "sergi", "festival", "sahne"],
    "Edebiyat": ["edebiyat", "kitap", "roman", "siir", "yazar", "okuma"],
    "Müzik": ["muzik", "konser", "sarki", "enstruman", "koro"],
    "Sinema": ["sinema", "film", "yonetmen", "gosterim"],
}

# Metinde yer adı ararken yanlış eşleşmeye açık olan (günlük kelime de olan) adlar.
_BELIRSIZ_YER_ADLARI = {"bala", "evren", "kiraz", "tire", "konak", "van", "kars", "ordu", "mus", "batman", "urla"}

_TABLOLAR = {"konumlar", "kategoriler"}
_ALFABE = "abcçdefgğhıijklmnoöprsştuüvyz"
_KATLAMA = str.maketrans("çğıöşüâîû", "cgiosuaiu")
DURAK_KELIMELER = set("ve ile bir bu su o da de mi mu icin olsun olarak gibi daha en ne ya ki her cok ama veya "
                      "hem bunu sey nasil neden hangi mi olmali olur ise kadar".split())


# --- Metin yardımcıları ---

def tr_kucuk(metin):
    return metin.replace("I", "ı").replace("İ", "i").lower()


def katla(metin):
    """Türkçe karakterleri katlanmış küçük harf metin: 'İstanbul'da Öğrenci' → 'istanbul'da ogrenci'."""
    return tr_kucuk(metin).translate(_KATLAMA)


def kelimeler(metin):
    return re.findall(r"[a-z0-9]+", katla(metin))


def anlamli_kelimeler(metin):
    return {k for k in kelimeler(metin) if len(k) > 2 and k not in DURAK_KELIMELER}


def tr_sirala(metin):
    """Türk alfabesine göre sıralama anahtarı."""
    return [_ALFABE.index(h) if h in _ALFABE else 100 + ord(h) for h in tr_kucuk(metin)]


def benzerlik_orani(a, b):
    """İki metnin anlamlı kelime kümelerinin Jaccard benzerliği (0–1)."""
    ka, kb = anlamli_kelimeler(a), anlamli_kelimeler(b)
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


# --- Tablolar ---

def yukle(db):
    if not db.execute("SELECT COUNT(*) FROM konumlar").fetchone()[0]:
        ekle = "INSERT INTO konumlar (ad, tur, ust_id) VALUES (?, ?, ?)"
        turkiye = db.execute(ekle, ("Türkiye", "ULKE", None)).lastrowid
        for bolge, iller in BOLGELER.items():
            bolge_id = db.execute(ekle, (bolge, "BOLGE", turkiye)).lastrowid
            for il in iller:
                il_id = db.execute(ekle, (il, "IL", bolge_id)).lastrowid
                for ilce in ILCELER.get(il, []):
                    db.execute(ekle, (ilce, "ILCE", il_id))
    surum = db.execute("SELECT deger FROM site_ayarlari WHERE anahtar = 'kategori_surumu'").fetchone()
    if not surum or surum[0] != KATEGORI_SURUMU:
        _kategori_agacini_kur(db)
        db.execute("INSERT INTO site_ayarlari (anahtar, deger) VALUES ('kategori_surumu', ?) "
                   "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger", (KATEGORI_SURUMU,))
    db.onbellek.clear()


def _kategori_bul(db, ad_, ust_id):
    r = db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id IS ?", (ad_, ust_id)).fetchone()
    return r[0] if r else None


def _kategori_agacini_kur(db):
    """Temel ağacı kurar (eksikleri ekler) ve eski ağaçtan kalan kategorileri yenilerine bağlar. Bir kez çalışır;
    yöneticinin ya da topluluğun eklediği kategorilere dokunmaz."""
    from . import zaman
    an = zaman.simdi_metin()
    for alan, alt_alanlar in KATEGORILER.items():
        alan_id = _kategori_bul(db, alan, None) or db.execute(
            "INSERT INTO kategoriler (ad, ust_id, kaynak, olusturma) VALUES (?, NULL, 'SISTEM', ?)", (alan, an)).lastrowid
        for alt in alt_alanlar:
            if not _kategori_bul(db, alt, alan_id):
                db.execute("INSERT INTO kategoriler (ad, ust_id, kaynak, olusturma) VALUES (?, ?, 'SISTEM', ?)",
                           (alt, alan_id, an))
    for (eski_ana, eski_alt), (yeni_ana, yeni_alt) in ESKI_KATEGORILER.items():
        eski_ana_id = _kategori_bul(db, eski_ana, None)
        if eski_ana_id is None or eski_alt is None:
            continue
        eski_id = _kategori_bul(db, eski_alt, eski_ana_id)
        yeni_id = _kategori_bul(db, yeni_alt, _kategori_bul(db, yeni_ana, None))
        if eski_id and yeni_id:
            _kategoriyi_birlestir(db, eski_id, yeni_id)
    for eski_ana in {a for a, _ in ESKI_KATEGORILER}:
        eski_ana_id = _kategori_bul(db, eski_ana, None)
        if eski_ana_id is None:
            continue
        hedef_ana, hedef_alt = ESKI_KATEGORILER[(eski_ana, None)]
        hedef_ana_id = _kategori_bul(db, hedef_ana, None)
        # Yöneticinin sonradan eklediği alt kategoriler silinmez, yeni ana kategorinin altına taşınır.
        db.execute("UPDATE kategoriler SET ust_id = ? WHERE ust_id = ?", (hedef_ana_id, eski_ana_id))
        _kategoriyi_birlestir(db, eski_ana_id, _kategori_bul(db, hedef_alt, hedef_ana_id))


def _kategoriyi_birlestir(db, eski_id, yeni_id):
    """eski kategoriye bağlı her şeyi yenisine taşır ve eskisini siler."""
    import json
    if eski_id == yeni_id:
        return
    db.execute("UPDATE konular SET kategori_id = ? WHERE kategori_id = ?", (yeni_id, eski_id))
    db.execute("UPDATE uzmanliklar SET kategori_id = ? WHERE kategori_id = ?", (yeni_id, eski_id))
    db.execute("DELETE FROM devirler WHERE kapsam = 'KATEGORI' AND kapsam_id = ? AND EXISTS (SELECT 1 FROM devirler d "
               "WHERE d.veren_id = devirler.veren_id AND d.kapsam = 'KATEGORI' AND d.kapsam_id = ?)", (eski_id, yeni_id))
    db.execute("UPDATE devirler SET kapsam_id = ? WHERE kapsam = 'KATEGORI' AND kapsam_id = ?", (yeni_id, eski_id))
    for t in db.execute("SELECT id, veri FROM teklifler WHERE veri LIKE '%kategori_id%'").fetchall():
        veri = json.loads(t["veri"] or "{}")
        if veri.get("kategori_id") == eski_id:
            veri["kategori_id"] = yeni_id
            db.execute("UPDATE teklifler SET veri = ? WHERE id = ?", (json.dumps(veri, ensure_ascii=False), t["id"]))
    db.execute("DELETE FROM kategoriler WHERE id = ?", (eski_id,))


def _harita(db, tablo):
    assert tablo in _TABLOLAR
    if tablo not in db.onbellek:
        db.onbellek[tablo] = {r["id"]: dict(r) for r in db.execute(f"SELECT * FROM {tablo}")}
    return db.onbellek[tablo]


def dugum(db, tablo, dugum_id):
    return _harita(db, tablo).get(dugum_id)


def atalar(db, tablo, dugum_id):
    """Kökten düğüme kadar olan id listesi (düğümün kendisi dahil)."""
    harita = _harita(db, tablo)
    yol = []
    while dugum_id is not None:
        yol.append(dugum_id)
        dugum_id = harita[dugum_id]["ust_id"]
    return list(reversed(yol))


def altinda_mi(db, tablo, alt_id, ust_id):
    return ust_id in atalar(db, tablo, alt_id)


def alt_agac(db, tablo, dugum_id):
    return [i for i in _harita(db, tablo) if altinda_mi(db, tablo, i, dugum_id)]


def yol_metni(db, tablo, dugum_id):
    harita = _harita(db, tablo)
    adlar = [harita[i]["ad"] for i in atalar(db, tablo, dugum_id)]
    if tablo == "konumlar" and len(adlar) > 1:
        adlar = adlar[1:]
    return " › ".join(adlar)


def kategori_rengi(db, kategori_id):
    """Alt kategoriler, ana kategorinin rengini alır. Yönetim panelinde seçilen renk önceliklidir."""
    from .ayarlar import KATEGORI_RENKLERI, VARSAYILAN_KATEGORI_RENGI
    kok = _harita(db, "kategoriler")[atalar(db, "kategoriler", kategori_id)[0]]
    return kok.get("renk") or KATEGORI_RENKLERI.get(kok["ad"], VARSAYILAN_KATEGORI_RENGI)


def ad(db, tablo, dugum_id):
    return _harita(db, tablo)[dugum_id]["ad"]


def benzerlik(db, tablo, kullanici_dugum, hedef_dugum):
    """Ontoloji tabanlı uygunluk: ortak en yakın atanın derinliği / hedefin derinliği.
    Hedef Kadıköy iken: Kadıköy 1.0, Beşiktaş 0.67 (aynı il), Bursa 0.33 (aynı bölge), Ankara 0."""
    kullanici_yolu = atalar(db, tablo, kullanici_dugum)
    hedef_yolu = atalar(db, tablo, hedef_dugum)
    ortak = 0
    for a, b in zip(kullanici_yolu, hedef_yolu):
        if a != b:
            break
        ortak += 1
    hedef_derinlik = len(hedef_yolu) - 1
    if hedef_derinlik == 0:
        return 1.0
    return max(0, ortak - 1) / hedef_derinlik


# --- Kavram eşleştirme (yönetmelik denetimi için) ---

def _terim_var_mi(terim, kelime_listesi, katli_metin):
    if " " in terim:
        return terim in katli_metin
    if len(terim) <= 3:
        return terim in kelime_listesi
    return any(k.startswith(terim) for k in kelime_listesi)


def kategori_eslesmeleri(db, metin):
    """{kategori_id: [eşleşen terimler]} — metnin ontolojideki kavramlarla ilişkisi."""
    katli = katla(metin)
    liste = kelimeler(metin)
    sonuc = {}
    for kid, d in _harita(db, "kategoriler").items():
        terimler = [t for t in kavramlar(d) if _terim_var_mi(t, liste, katli)]
        if terimler:
            sonuc[kid] = terimler
    return sonuc


def kavramlar(kategori):
    """Bir kategorinin terimleri: koddaki liste + topluluğun önerirken yazdıkları."""
    ek = [t.strip() for t in (kategori.get("kavramlar") or "").split(",") if t.strip()]
    return KAVRAMLAR.get(kategori["ad"], []) + ek


def genel_mi(db, kategori_id):
    from .ayarlar import GENEL_KATEGORI
    return ad(db, "kategoriler", atalar(db, "kategoriler", kategori_id)[0]) == GENEL_KATEGORI


def kategori_iliskisi(db, metin, kategori_id):
    """Metnin seçilen kategoriyle ilişkisi: kategori, üst ve alt kategorilerin terimleri sayılır."""
    eslesme = kategori_eslesmeleri(db, metin)
    ilgili = set(atalar(db, "kategoriler", kategori_id)) | set(alt_agac(db, "kategoriler", kategori_id))
    terimler = sorted({t for kid in ilgili for t in eslesme.get(kid, [])})
    return terimler, eslesme


def alan_puanlari(db, eslesme):
    """{ana alan id: (eşleşen farklı kavram sayısı, bunlardan alt kategori düzeyinde olanların sayısı)}.
    Aynı kavram iki alt kategoride geçse de (ör. "kampus": Üniversite ve Kampüs Yaşamı) bir kez sayılır."""
    alanlar = {}
    for kid, terimler in eslesme.items():
        yol = atalar(db, "kategoriler", kid)
        tum, alt = alanlar.setdefault(yol[0], (set(), set()))
        tum.update(terimler)
        if len(yol) > 1:
            alt.update(terimler)
    return {kok: (len(tum), len(alt)) for kok, (tum, alt) in alanlar.items()}


def en_uygun_kategori(db, metin):
    """Metne en uygun kategori. Önce ana alan seçilir: alt kategorileriyle birlikte en çok farklı kavramı eşleşen alan;
    eşitlikte alt kategori düzeyinde (daha belirgin) eşleşmesi çok olan. Sonra o alanın içinde en çok eşleşen, eşitlikte
    en derindeki kategori döner.
    Önceden her kategori tek başına yarışıyordu: "belediye meclis toplantıları canlı yayınlansın" metninde Siyaset (meclis)
    ve Yerel Yönetim (belediye) birer eşleşmeyle Biyoloji'ye (canlı) eşit kalıyor, kazananı sözlük sırası belirliyordu.
    Tam eşitlikte (aynı iki puan) kazananı hâlâ kategori sırası belirler; D3 yalnızca uyarı verdiği için kabul edildi."""
    eslesme = kategori_eslesmeleri(db, metin)
    if not eslesme:
        return None, []
    puanlar = alan_puanlari(db, eslesme)
    kok = max(puanlar, key=puanlar.get)
    kid = max((k for k in eslesme if atalar(db, "kategoriler", k)[0] == kok),
              key=lambda k: (len(eslesme[k]), len(atalar(db, "kategoriler", k))))
    return kid, eslesme[kid]


def metindeki_yerler(db, metin):
    """Metinde geçen il ve ilçe adları → konum id listesi."""
    liste = set(kelimeler(metin))
    bulunan = []
    for kid, d in _harita(db, "konumlar").items():
        if d["tur"] not in ("IL", "ILCE"):
            continue
        adi = katla(d["ad"])
        if adi in _BELIRSIZ_YER_ADLARI:
            continue
        if (" " in adi and adi in katla(metin)) or adi in liste:
            bulunan.append(kid)
    return bulunan


# --- Formlar için seçenek listeleri ---

def il_listesi(db):
    iller = [d for d in _harita(db, "konumlar").values() if d["tur"] == "IL"]
    return sorted(iller, key=lambda d: tr_sirala(d["ad"]))


def ilce_haritasi(db):
    sonuc = {}
    for d in _harita(db, "konumlar").values():
        if d["tur"] == "ILCE":
            sonuc.setdefault(d["ust_id"], []).append({"id": d["id"], "ad": d["ad"]})
    for liste in sonuc.values():
        liste.sort(key=lambda d: tr_sirala(d["ad"]))
    return sonuc


def konum_agaci(db):
    harita = _harita(db, "konumlar")
    cocuklar = {}
    for d in harita.values():
        cocuklar.setdefault(d["ust_id"], []).append(d)
    for liste in cocuklar.values():
        liste.sort(key=lambda d: tr_sirala(d["ad"]))
    kok = cocuklar[None][0]
    return [(bolge, [(il, cocuklar.get(il["id"], [])) for il in cocuklar.get(bolge["id"], [])])
            for bolge in cocuklar.get(kok["id"], [])]


def kategori_listesi(db):
    """Formlardaki seçim listesi: ana kategoriler Türk alfabesine göre, Genel en sonda."""
    from .ayarlar import GENEL_KATEGORI
    liste = [(i, yol_metni(db, "kategoriler", i)) for i in _harita(db, "kategoriler")]
    return sorted(liste, key=lambda x: (x[1].split(" › ")[0] == GENEL_KATEGORI, tr_sirala(x[1])))
