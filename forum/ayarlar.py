"""Sabit tanımlar ve yönetmeliğin VARSAYILAN parametreleri.

Oylamayla değişebilen sayılar (eşikler, süreler, yeter sayı...) veritabanındaki `parametreler`
tablosunda yaşar ve `yonetmelik.deger(db, KOD)` ile okunur. Buradaki değerler sadece ilk kurulumda
yüklenir.
"""

# --- Site kimliği (sitenin adını değiştirmek için sadece burayı düzenle) ---
SITE_ADI = "Agora"
# Mobil uygulama (mobil/ klasöründeki Capacitor kabuğu) tarayıcı kimliğinin sonuna bunu ekler.
MOBIL_UA = "AgoraMobil"

# --- Renk paleti: iki renk ---
# Ana renk taş beyazı: güneş almış mermer tonunda, biraz silikleştirilmiş kirli beyaz. Yan renk kaktüs yeşili (düğmelerde koyu tonu). Yazılar taşın gölgesindeki koyu gridir.
# Açık/koyu tonlar aynı rengin tonlarıdır; başka renk kullanılmaz. Aynı değerler static/style.css içindeki :root'ta da vardır.
TAS_BEYAZI = {50: "#f6f4ef", 100: "#ebe7df", 200: "#dfd9ce", 300: "#cfc8ba"}
GRI = {300: "#c9c5bd", 400: "#a9a49b", 500: "#8a857c", 700: "#57534c", 900: "#2c2a27"}
YESIL = {50: "#f1f5ef", 100: "#e3ebdf", 200: "#c5d6bd", 300: "#a3bd97", 400: "#799a6d",
         500: "#5f8054", 600: "#4a6642", 700: "#3a5234", 800: "#2a3c25", 900: "#1f2d1b"}

# Ana kategorilerin renkleri: yeşilin ve grinin birbirinden kolay ayrılan tonları
KATEGORI_RENKLERI = {
    "Bilim": YESIL[300], "Sağlık": YESIL[400], "Siyaset": GRI[700], "Eğitim": YESIL[200],
    "Teknoloji": YESIL[600], "Ekonomi": YESIL[800], "Kültür ve Sanat": GRI[300], "Genel": GRI[500],
}
# Her konuya açık kategori: kategori denetimi (D3) burada aranmaz; yeni kategori fikirleri de burada tartışılır.
GENEL_KATEGORI = "Genel"
VARSAYILAN_KATEGORI_RENGI = TAS_BEYAZI[300]

# --- Eşik türleri: (pay, payda, kesin_büyük_mü) ---
ESIKLER = {
    "SALT":      {"ad": "Salt çoğunluk",        "kisa": "yarıdan fazla", "pay": 1, "payda": 2, "kati": True},
    "BESTE_UC":  {"ad": "Beşte üç çoğunluk",    "kisa": "en az 3/5",     "pay": 3, "payda": 5, "kati": False},
    "UCTE_IKI":  {"ad": "Üçte iki çoğunluk",    "kisa": "en az 2/3",     "pay": 2, "payda": 3, "kati": False},
    "DORTTE_UC": {"ad": "Dörtte üç çoğunluk",   "kisa": "en az 3/4",     "pay": 3, "payda": 4, "kati": False},
}

# --- Oylama türleri ---
# esik/sure: yönetmelik parametresinin kodu. Davranışları teklif_turleri.py'deki sınıflardadır (Strategy + Registry).
# KARAR (fikir oylaması turu) eşik yerine eleme kurallarını kullanır; süresi tur numarasına göre seçilir.
TEKLIF_TIPLERI = {
    "KARAR":       {"ad": "Fikir oylaması", "esik": None, "sure": None},
    "MESAJ_SILME": {"ad": "Mesaj gizleme", "esik": "ESIK_MESAJ_SILME", "sure": "SURE_USUL_SAAT"},
    "KONU_SILME":  {"ad": "Konu kaldırma", "esik": "ESIK_KONU_SILME", "sure": "SURE_USUL_SAAT"},
    "UZMANLIK":    {"ad": "Uzmanlık başvurusu", "esik": "ESIK_UZMANLIK", "sure": "SURE_USUL_SAAT"},
    "YONETMELIK":  {"ad": "Yönetmelik değişikliği", "esik": "ESIK_YONETMELIK", "sure": "SURE_YONETMELIK_SAAT"},
    "KATEGORI":    {"ad": "Yeni kategori", "esik": "ESIK_KATEGORI", "sure": "SURE_USUL_SAAT"},
}

TEKLIF_DURUMLARI = {
    "ACIK": "Oylama sürüyor", "KABUL": "Kabul edildi", "RET": "Reddedildi",
    "YETERSIZ": "Yeter sayıya ulaşılamadı", "IPTAL": "İptal edildi", "BITTI": "Tur bitti",
}
SECIM_ADLARI = {"EVET": "Evet", "HAYIR": "Hayır", "CEKIMSER": "Çekimser"}

# --- Fikir oylaması: en fazla 5 tur ---
TUR_SAYISI = 5
# Tur bitince oranı bu parametrenin altında kalan fikirler elenir (son turda eleme yok, en çok oy alan kazanır).
ELEME_PARAMETRELERI = {1: "ELEME_TUR1", 2: "ELEME_TUR2", 3: "ELEME_TUR3", 4: "ELEME_TUR4"}

# --- Yönetmelik parametrelerinin varsayılanları ---
# (kod, değer, tür, açıklama, korunan_mu)
# Korunan (temel hak) parametreler ancak ESIK_TEMEL_HAK ile değiştirilebilir.
VARSAYILAN_PARAMETRELER = [
    ("SURE_TARTISMA_SAAT", "24", "sayi", "Tartışma süresi: fikir oylaması açılmadan önce (saat)", False),
    ("SURE_TUR1_SAAT", "48", "sayi", "1. tur oylama süresi (saat)", False),
    ("SURE_TUR_SAAT", "24", "sayi", "2–5. tur oylama süresi (saat)", False),
    ("ELEME_TUR1", "0.05", "oran", "1. turda kalmak için gereken en az oy oranı", False),
    ("ELEME_TUR2", "0.05", "oran", "2. turda kalmak için gereken en az oy oranı", False),
    ("ELEME_TUR3", "0.1", "oran", "3. turda kalmak için gereken en az oy oranı", False),
    ("ELEME_TUR4", "0.2", "oran", "4. turda kalmak için gereken en az oy oranı", False),
    ("ESIK_EZICI", "0.75", "oran", "Ezici üstünlük: bu oranı alan fikir hemen kabul edilir", True),
    ("YETER_SAYI_ORANI", "0.2", "oran", "Yeter sayı (oy hakkı olanların oranı)", False),
    ("MIN_KATILIM", "2", "sayi", "Her oylamada en az katılım", False),
    ("ESIK_MESAJ_SILME", "DORTTE_UC", "esik", "Mesaj gizleme", True),
    ("ESIK_KONU_SILME", "DORTTE_UC", "esik", "Konu kaldırma", False),
    ("ESIK_UZMANLIK", "UCTE_IKI", "esik", "Uzmanlık başvurusu", False),
    ("ESIK_YONETMELIK", "UCTE_IKI", "esik", "Yönetmelik değişikliği", True),
    ("ESIK_KATEGORI", "SALT", "esik", "Yeni kategori önerisi", False),
    ("ESIK_TEMEL_HAK", "DORTTE_UC", "esik", "Temel hak maddesi değişikliği", True),
    ("SURE_USUL_SAAT", "48", "sayi", "Gizleme, kaldırma, uzmanlık ve kategori oylamaları (saat)", False),
    ("SURE_YONETMELIK_SAAT", "96", "sayi", "Yönetmelik değişikliği oylaması (saat)", False),
    ("UZMAN_AGIRLIK", "10", "sayi", "Uzman oyunun kendi alanındaki ağırlığı", False),
    ("UZMAN_KONTENJAN", "3", "sayi", "Bir ana kategorideki en fazla uzman sayısı", True),
    ("UZMAN_MIN_MESAJ", "5", "sayi", "Uzmanlık ön şartı: alanda yazılmış en az mesaj", False),
    ("UZMAN_MIN_KONU", "2", "sayi", "Uzmanlık ön şartı: alanda katılınmış en az konu", False),
    ("UZMAN_SURE_GUN", "180", "sayi", "Uzmanlık süresi (gün)", False),
    ("MAX_DEVIR", "5", "sayi", "Bir kişinin taşıyabileceği en fazla devredilmiş oy", True),
    ("SIKAYET_TABANI", "3", "sayi", "Bir içeriğin yöneticilere ulaşması için gereken en az şikayetçi", False),
    ("ADRES_BEKLEME_GUN", "30", "sayi", "Yeni adresin geçerli olması için geçen süre (gün)", False),
]

# Oylamayla değişebilen sayıların anlamlı aralıkları (en az, en çok). Aralık dışı değer önerilemez: ör. UZMAN_AGIRLIK=0
# uzmanların hiç oy verememesine, SIKAYET_TABANI=0 şikayetlerin yöneticiye hiç ulaşmamasına, SURE_TUR_SAAT=0 turların
# anında bitmesine yol açardı. Eşik türündeki parametrelerin geçerli değerleri ESIKLER'dir.
PARAMETRE_ARALIKLARI = {
    "SURE_TARTISMA_SAAT": (1, 720), "SURE_TUR1_SAAT": (1, 720), "SURE_TUR_SAAT": (1, 720),
    "ELEME_TUR1": (0.01, 0.5), "ELEME_TUR2": (0.01, 0.5), "ELEME_TUR3": (0.01, 0.5), "ELEME_TUR4": (0.01, 0.5),
    "ESIK_EZICI": (0.51, 1), "YETER_SAYI_ORANI": (0.01, 1), "MIN_KATILIM": (1, 1000),
    "SURE_USUL_SAAT": (1, 720), "SURE_YONETMELIK_SAAT": (24, 720),
    "UZMAN_AGIRLIK": (1, 100), "UZMAN_KONTENJAN": (1, 50), "UZMAN_MIN_MESAJ": (0, 1000), "UZMAN_MIN_KONU": (0, 1000),
    "UZMAN_SURE_GUN": (1, 3650), "MAX_DEVIR": (0, 1000), "SIKAYET_TABANI": (1, 1000), "ADRES_BEKLEME_GUN": (0, 365),
}

# --- Değişmeyen tanımlar ---
KONU_DURUMLARI = {
    "TARTISMA": "Tartışmada",
    "OYLAMA": "Oylamada",
    "KARARA_BAGLANDI": "Karara bağlandı",
    "SONUCSUZ": "Sonuçsuz kapandı",
}

MESAJ_TIPLERI = {
    "ARGUMAN": "Argüman", "KARSI_ARGUMAN": "Karşı argüman", "SORU": "Soru", "KAYNAK": "Kaynak",
    "FIKIR": "Fikir", "YZ": "Özet", "SISTEM": "Sistem",
}
KULLANICI_MESAJ_TIPLERI = ["ARGUMAN", "KARSI_ARGUMAN", "SORU", "KAYNAK"]   # fikir ayrı yazılır: kişi başı bir tane
SILME_NEDENLERI = ["Hakaret", "Spam", "Konu dışı", "Kişisel veri", "Yanlış bilgi", "Diğer"]

DEFTER_DUGUMLERI = ["A", "B", "C"]

MAX_YZ_HESABI = 3
MIN_KAYIT_YASI = 13
SIFRE_MIN = 8
GIRIS_DENEME_SINIRI = 5          # bu kadar hatalı girişten sonra...
GIRIS_KILIT_DAKIKA = 10          # ...bu kadar dakika beklenir
SAYFA_BOYU = 15
