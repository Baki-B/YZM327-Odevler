"""Demo verisi: son iki haftada yaşanmış gibi görünen, dolu bir forum.

Veriler doğrudan iş mantığı fonksiyonlarıyla, geçmiş zamanlara ayarlanmış bir saatle ve zaman sırasıyla oluşturulur;
yani yönetmelik denetimi, tur tur eleme, ezici üstünlük, çekimser, kategori önerileri, şikayet tabanı ve defter
kayıtları gerçekten çalışır; trendler, kategori nabzı ve etkinlik grafikleri de gerçek zamanlarla dolar.
Bütün demo hesaplarının şifresi: forum1234
"""
from datetime import date, timedelta

from . import (devir, graf, kategoriler, konular, kullanicilar, oylama, sikayetler, uzmanlik, veritabani, yonetmelik,
               yz, zaman)

SIFRE = "forum1234"


def _dogum(yas):
    return date(zaman.simdi().year - yas, 1, 1).isoformat()


def _konum(db, il, ilce=None):
    il_id = db.execute("SELECT id FROM konumlar WHERE ad = ? AND tur = 'IL'", (il,)).fetchone()["id"]
    if not ilce:
        return il_id
    return db.execute("SELECT id FROM konumlar WHERE ad = ? AND ust_id = ?", (ilce, il_id)).fetchone()["id"]


def _kategori(db, alan, alt=None):
    ust = db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id IS NULL", (alan,)).fetchone()["id"]
    if not alt:
        return ust
    return db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id = ?", (alt, ust)).fetchone()["id"]


def gerekirse_yukle(yol):
    db = veritabani.baglan(yol)
    try:
        if db.execute("SELECT COUNT(*) FROM kullanicilar").fetchone()[0]:
            return False
        yukle(db)
        db.commit()
        return True
    finally:
        db.close()


KISILER = [
    ("yonetici", "Forum Yöneticisi", 36, "İstanbul", "Şişli"),
    ("ayse", "Ayşe Yılmaz", 21, "İstanbul", "Kadıköy"),
    ("mehmet", "Mehmet Kaya", 23, "İstanbul", "Beşiktaş"),
    ("elif", "Elif Demir", 17, "İstanbul", "Kadıköy"),
    ("zeynep", "Zeynep Arslan", 20, "Ankara", "Çankaya"),
    ("can", "Can Öztürk", 19, "İzmir", "Bornova"),
    ("selin", "Selin Koç", 22, "İzmir", "Karşıyaka"),
    ("burak", "Burak Şen", 24, "İstanbul", "Kartal"),
    ("dr.deniz", "Deniz Aydın", 41, "Ankara", "Çankaya"),
    ("kaan.hoca", "Kaan Şahin", 46, "İstanbul", "Üsküdar"),
    ("ece", "Ece Güneş", 20, "İzmir", "Konak"),
    ("onur", "Onur Çelik", 27, "Ankara", "Keçiören"),
    ("defne", "Defne Aksoy", 22, "İstanbul", "Beşiktaş"),
    ("mert", "Mert Yıldız", 25, "Bursa", None),
]


def yukle(db):
    gercek = zaman.simdi
    try:
        _senaryo(db, gercek)
    finally:
        zaman.simdi = gercek


def _senaryo(db, gercek):  # noqa: C901 — tek parça, zaman sırasıyla okunan bir senaryo
    simdi = gercek()

    def saat(h):
        """Saati h saat öncesine ayarlar; sonraki bütün kayıtlar o zamanda yapılmış olur."""
        an = simdi - timedelta(hours=h)
        zaman.simdi = lambda: an

    def u(takma):
        return kullanicilar.takma_ad_ile(db, takma)

    def konu(h, sahip, baslik, aciklama, kategori, ust=None, itiraz=None, **ek):
        saat(h)
        return konular.konu_ac(db, u(sahip), dict(baslik=baslik, aciklama=aciklama, kategori_id=kategori, **ek), ust, itiraz)

    def fikir(h, kim, konu_id, metin):
        saat(h)
        return konular.fikir_yaz(db, u(kim), konu_id, metin)

    def yaz(h, kim, konu_id, tip, metin, ust=None):
        saat(h)
        return konular.mesaj_yaz(db, u(kim), konu_id, tip, metin, ust)

    def tartisma(konu_id, satirlar):
        """satirlar: [(saat, kim, tip, metin, yanıtlanan mesaj ya da None)] → mesaj id'leri"""
        return [yaz(h, kim, konu_id, tip, metin, ust) for h, kim, tip, metin, ust in satirlar]

    def oy(h, teklif_id, kim, secim, gerekce=""):
        saat(h)
        t = oylama.teklif_getir(db, teklif_id)
        if not gerekce and oylama.oy_durumu(db, t, u(kim))["agirlik"] > 1:
            gerekce = "Alanımdaki bilgi ve tartışmadaki argümanlar doğrultusunda bu yönde oy veriyorum."
        oylama.oy_ver(db, teklif_id, u(kim), str(secim), gerekce)

    def tur(h, konu_id, dagilim):
        """Süren turda oy verdirir; oylar h saatten başlayarak birkaç dakika arayla verilir."""
        t = oylama.acik_teklif(db, "KARAR", konu_id=konu_id)
        i = 0
        for hedef, kimler in dagilim.items():
            secim = hedef if hedef == oylama.CEKIMSER else db.execute(
                "SELECT id FROM secenekler WHERE teklif_id = ? AND mesaj_id = ?", (t["id"], hedef)).fetchone()["id"]
            for kim in kimler:
                oy(h - 0.4 * i, t["id"], kim, secim)
                i += 1
        return t["id"]

    def evet_hayir(h, teklif_id, evet=(), hayir=(), cekimser=()):
        i = 0
        for secim, kimler in (("EVET", evet), ("HAYIR", hayir), ("CEKIMSER", cekimser)):
            for kim in kimler:
                oy(h - 0.5 * i, teklif_id, kim, secim)
                i += 1

    def baslat(h, konu_id):
        saat(h)
        konular.oylamayi_baslat(db, konu_id)

    def bitir(h, teklif_id=None, konu_id=None):
        saat(h)
        t = teklif_id or oylama.acik_teklif(db, "KARAR", konu_id=konu_id)["id"]
        oylama.sonuclandir(db, t)

    # ================= 12,5 gün önce: üyeler, uzmanlar, takip ve devir =================
    saat(300)
    for i, (takma, ad, yas, il, ilce) in enumerate(KISILER):
        saat(300 - i * 3)
        kullanicilar.kayit(db, ad, takma, SIFRE, SIFRE, _dogum(yas), _konum(db, il, ilce))
    db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE takma_ad = 'yonetici'")
    saat(258)
    kullanicilar.yz_ekle(db, u("yonetici"), "Bilge")
    # Demo başlangıcı: iki uzman hazır gelir (normalde ön şart + kontenjan + alan oylamasıyla olunur).
    uzmanlik.uzmanlik_ver(db, u("dr.deniz")["id"], _kategori(db, "Sağlık"))
    uzmanlik.uzmanlik_ver(db, u("kaan.hoca")["id"], _kategori(db, "Teknoloji", "Yazılım"))
    for eden, edilen in [("ayse", "kaan.hoca"), ("zeynep", "dr.deniz"), ("mehmet", "ayse"), ("can", "mehmet"),
                         ("burak", "ayse"), ("selin", "zeynep"), ("elif", "ayse"), ("dr.deniz", "kaan.hoca"),
                         ("ece", "selin"), ("onur", "dr.deniz"), ("defne", "mehmet"), ("mert", "can"), ("ece", "ayse")]:
        graf.takip_et(db, u(eden), u(edilen)["id"])
    devir.devir_ekle(db, u("elif"), "mehmet", "KATEGORI", _kategori(db, "Siyaset"))
    devir.devir_ekle(db, u("zeynep"), "kaan.hoca", "KATEGORI", _kategori(db, "Teknoloji"))
    devir.devir_ekle(db, u("burak"), "ayse", "GENEL")

    # ================= 1) Final projesi: beş turun hepsi (18+) =================
    k1 = konu(250, "kaan.hoca", "Yazılım Mühendisliğine Giriş final projesi hangi dille yapılsın?",
              "Dönem sonu projesinde bütün grupların aynı programlama dilini mi kullanması, yoksa serbest mi olması "
              "daha iyi? Herkes bir fikir yazsın; gerekçelerinizi argüman olarak ekleyin.",
              _kategori(db, "Teknoloji", "Yazılım"), min_yas=18)
    py = fikir(249.8, "kaan.hoca", k1, "Python (Flask) ile web uygulaması")
    java = fikir(249.5, "can", k1, "Java (Spring Boot) ile web uygulaması")
    serbest = fikir(249, "zeynep", k1, "Serbest olsun, her grup kendi dilini seçsin")
    c_dili = fikir(248, "burak", k1, "Herkes C ile konsol uygulaması yazsın")
    tartisma(k1, [
        (247, "ayse", "ARGUMAN", "Python'un sözdizimi yeni başlayanlar için çok okunabilir; derste kavramlara odaklanırız.", py),
        (246, "can", "KARSI_ARGUMAN", "Python'da tip hataları ancak çalışırken ortaya çıkıyor, büyük projede sorun olabilir.", py),
        (244, "yonetici", "ARGUMAN", "Java sektörde çok yaygın; staj bulmak için avantajlı.", java),
        (243, "mehmet", "KARSI_ARGUMAN", "Spring Boot kurulumu bir dönemlik giriş dersi için ağır kalır.", java),
        (241, "mehmet", "ARGUMAN", "Farklı diller kullanılırsa gruplar birbirinden öğrenir; akran öğrenmesi zenginleşir.", serbest),
        (240, "kaan.hoca", "KARSI_ARGUMAN", "Ortak altyapı olmazsa geri bildirim vermek ve değerlendirmek zorlaşır.", serbest),
        (238, "selin", "KARSI_ARGUMAN", "Konsol uygulaması web projesi hedefiyle örtüşmüyor.", c_dili),
        (236, "zeynep", "SORU", "Teslimde sadece kod mu olacak, yoksa rapor ve UML diyagramları da istenecek mi?", None),
        (235, "kaan.hoca", "KAYNAK", "Ders izlencesine göre teslimde kod, kullanım durumu ve sınıf diyagramları birlikte isteniyor.", None),
        (233, "ece", "ARGUMAN", "Serbest seçim, grupların güçlü olduğu dili kullanmasını sağlar; motivasyon artar.", serbest),
    ])
    baslat(226, k1)
    pycular, serbestciler = ["kaan.hoca", "ayse", "yonetici", "selin", "onur"], ["mehmet", "zeynep", "dr.deniz", "ece", "defne"]
    tur(222, k1, {py: pycular, serbest: serbestciler, java: ["can", "mert"], c_dili: ["burak"]})   # C, uzman ağırlığı yüzünden %5 altında

    # ================= 2) Kütüphane: 2. turda ezici üstünlük =================
    k12 = konu(200, "selin", "Kampüs kütüphanesinde gece açık okuma salonu olsun",
               "Sınav dönemlerinde kütüphane 22.00'de kapanıyor. Kitaplarla ve sessiz bir ortamda gece de çalışabileceğimiz "
               "bir okuma salonu istiyoruz. Edebiyat kulübü de akşam okuma buluşmalarını orada yapabilir.",
               _kategori(db, "Kültür ve Sanat", "Edebiyat"))
    ka = fikir(199.5, "selin", k12, "Kütüphanenin bir salonu 24 saat açık okuma salonu olsun.")
    kb = fikir(199, "ece", k12, "Kütüphane yalnızca sınav haftalarında gece 02.00'ye kadar açık kalsın.")
    kc = fikir(198, "onur", k12, "Gece salonu yerine yurtlarda sessiz çalışma odaları açılsın.")
    tartisma(k12, [
        (197, "ayse", "ARGUMAN", "Yurtta çalışmak zor; oda arkadaşları uyurken ışık açamıyoruz.", ka),
        (195, "kaan.hoca", "KARSI_ARGUMAN", "24 saat açık salonun güvenlik ve temizlik maliyeti yüksek olur.", ka),
        (194, "mehmet", "ARGUMAN", "Sadece sınav haftaları açık kalırsa maliyet makul olur.", kb),
        (192, "defne", "ARGUMAN", "Okuma buluşmaları için de akşam saatleri gerekiyor; bu yalnızca sınavla ilgili değil.", ka),
        (190, "zeynep", "SORU", "Diğer üniversitelerde gece açık kütüphane uygulaması var mı?", None),
        (188, "ece", "KAYNAK", "Birçok büyük kampüste sınav dönemlerinde 24 saat açık çalışma salonu uygulaması bulunuyor.", None),
    ])
    bitir(178, konu_id=k1)                                                   # 1. tur bitti: C elendi
    baslat(176, k12)
    tur(172, k1, {py: pycular, serbest: serbestciler + ["burak"], java: ["can", "mert"]})

    # ================= 3) Finaller: yeter sayı yok, sonuçsuz =================
    k5 = konu(170, "can", "Final sınavları tamamen kaldırılsın",
              "Dönem boyunca proje ve ödevlerle değerlendirme yapılsın; final sınavı stresi öğrenmeyi engelliyor.",
              _kategori(db, "Eğitim", "Üniversite"))
    k5f = fikir(169, "can", k5, "Finaller kalksın, not proje ve ödevlerden oluşsun.")
    yaz(165, "kaan.hoca", k5, "KARSI_ARGUMAN", "Final, dönemin bütününü ölçen tek araç; tamamen kaldırmak yerine ağırlığı azaltılabilir.", k5f)
    tur_k12 = [("selin", "ece", "ayse", "defne", "elif", "can", "zeynep"), ("kaan.hoca", "mehmet", "burak", "mert", "yonetici"),
               ("onur", "dr.deniz")]
    tur(160, k12, {ka: list(tur_k12[0]), kb: list(tur_k12[1]), kc: list(tur_k12[2])})
    bitir(154, konu_id=k1)                                                   # 2. tur bitti: herkes kaldı
    tur(150, k1, {py: pycular, serbest: serbestciler + ["burak"], java: ["can", "mert"]})
    baslat(146, k5)
    tur(140, k5, {k5f: ["can"]})

    # ================= 4) Kulüp toplantıları: ilk turda ezici üstünlük =================
    k2 = konu(140, "selin", "Kulüp toplantıları hafta sonu yapılsın mı?",
              "Hafta içi dersler yüzünden kulüp etkinliklerine katılım düşük. Toplantı gününü birlikte seçelim.",
              _kategori(db, "Eğitim", "Kampüs Yaşamı"))
    cmt = fikir(139.5, "selin", k2, "Kulüp toplantıları cumartesi öğleden sonra yapılsın.")
    hafta = fikir(139, "burak", k2, "Toplantılar hafta içi akşam 18.00'de yapılsın.")
    tartisma(k2, [
        (138, "ayse", "ARGUMAN", "Cumartesi herkes boş; etkinlik uzun sürebilir.", cmt),
        (136, "can", "ARGUMAN", "Hafta sonu kampüs sakin olduğu için salon bulmak kolay.", cmt),
        (134, "mehmet", "KARSI_ARGUMAN", "Şehir dışından gelen ve hafta sonu çalışan öğrenciler dışlanır.", cmt),
        (131, "zeynep", "ARGUMAN", "Akşam 18.00 dersten hemen sonra; kampüsteyken katılmak kolay.", hafta),
        (132, "defne", "SORU", "Kulüp başkanlarıyla bir anket yapıldı mı?", None),
    ])
    bitir(130, konu_id=k1)                                                   # 3. tur bitti: Java %10 altında elendi
    bitir(128, konu_id=k12)
    tur(126, k1, {py: pycular + ["can", "mert"], serbest: serbestciler + ["burak"]})
    tur(125, k12, {ka: list(tur_k12[0]) + ["kaan.hoca", "mehmet", "onur", "dr.deniz"], kb: ["burak", "mert", "yonetici"]})

    # ================= Kategori önerileri =================
    saat(120)
    t_tiyatro = kategoriler.oner(db, u("defne"), "Tiyatro", _kategori(db, "Kültür ve Sanat"),
                                 "tiyatro, oyun, sahne, prova, oyuncu",
                                 "Kampüste üç tiyatro topluluğu var ama konuları Edebiyat ya da Müzik altında kayboluyor.")
    evet_hayir(118, t_tiyatro, evet=["defne", "selin", "ece", "ayse", "elif", "can", "onur", "zeynep", "mehmet"],
               hayir=["mert"], cekimser=["burak"])
    baslat(116, k2)
    tur(110, k2, {cmt: ["selin", "ayse", "can", "yonetici", "elif", "dr.deniz", "kaan.hoca", "zeynep", "ece", "defne", "onur"],
                  hafta: ["burak", "mehmet", "mert"]})
    bitir(106, konu_id=k1)                                                   # 4. tur bitti: ikisi de %20 üstünde
    bitir(104, konu_id=k12)                                                  # 2. turda %79: ezici üstünlük
    tur(102, k1, {py: pycular + ["can", "mert"], serbest: serbestciler + ["burak"]})
    saat(100)
    t_magazin = kategoriler.oner(db, u("mert"), "Magazin", None, "unlu, dizi, magazin",
                                 "Ünlüler ve diziler hakkında konuşabileceğimiz ayrı bir yer olsun, Genel çok karışıyor.")
    evet_hayir(99, t_magazin, evet=["mert", "burak"], hayir=["ayse", "kaan.hoca", "zeynep", "selin", "mehmet", "onur", "dr.deniz"])
    bitir(98, konu_id=k5)                                                    # yeter sayı yok: sonuçsuz
    bitir(82, konu_id=k1)                                                    # 5. tur: Python kazandı

    # ================= 5) Yemekhane: 2. tur sürüyor; çekimser, uzman oyu, şikayet =================
    k3 = konu(80, "ayse", "Yemekhanede haftada 2 gün etsiz menü olsun mu?",
              "Sağlık, maliyet ve farklı beslenme tercihleri açısından yemekhane menüsünü tartışalım. Haftada iki gün "
              "ana yemeğin etsiz olmasını öneriyorum.", _kategori(db, "Sağlık", "Beslenme"))
    f1 = fikir(79.5, "ayse", k3, "Pazartesi ve perşembe ana yemek etsiz olsun; yanında baklagil ve yoğurt verilsin.")
    f2 = fikir(79, "mehmet", k3, "Her gün etli ve etsiz iki ana yemek seçeneği sunulsun; kimse zorlanmasın.")
    fikir(78, "burak", k3, "Menü değişmesin, yalnızca porsiyonlar küçültülsün.")
    tartisma(k3, [
        (77, "dr.deniz", "ARGUMAN", "Baklagil ve tahıl birlikte tüketildiğinde tam protein sağlar. Haftada iki gün etsiz menü "
                                    "sağlık açısından olumludur.", f1),
        (76, "can", "KARSI_ARGUMAN", "Sporcu öğrencilerin protein ihtiyacı yüksek; iki gün az gelebilir.", f1),
        (74, "zeynep", "ARGUMAN", "Seçenek sunmak farklı beslenme tercihlerine saygı gösterir.", f2),
        (73, "kaan.hoca", "SORU", "Her gün iki ana yemek çıkarmanın yemekhane bütçesine maliyeti ne olur?", None),
        (72.6, "mehmet", "KAYNAK", "Dünya Sağlık Örgütü'nün sağlıklı beslenme önerileri, haftalık menüde baklagil ve sebzenin "
                                 "payının artırılmasını tavsiye ediyor.", None),
        (72.3, "ece", "ARGUMAN", "Vegan ve vejetaryen arkadaşlar şu an çoğu gün sadece pilav yiyebiliyor.", f2),
    ])
    bitir(72, t_tiyatro)                                                     # kabul: Kültür ve Sanat › Tiyatro eklendi
    bitir(68, konu_id=k2)
    spam = yaz(66, "can", k3, "ARGUMAN", "Arkadaşlar satılık bisikletim var, isteyen bana ulaşsın.")
    for i, kim in enumerate(["ayse", "zeynep", "mehmet"]):                   # 3. şikayetle taban doldu → yöneticiye düşer
        saat(65 - i)
        sikayetler.sikayet_et(db, u(kim), "MESAJ", spam, "Konu dışı")

    # ================= 6) Burslar: 1. tur sürüyor =================
    k10 = konu(60, "onur", "Öğrenci bursları enflasyona göre her dönem güncellensin",
               "Burs miktarı yılda bir belirleniyor ama kira, yemek ve ulaşım fiyatları dönem içinde birkaç kez artıyor. "
               "Bursların alım gücü korunmalı.", _kategori(db, "Ekonomi", "Kişisel Finans"))
    b1 = fikir(59.5, "onur", k10, "Burslar her dönem başında enflasyon oranında otomatik artırılsın.")
    b2 = fikir(58, "ayse", k10, "Nakit artış yerine yemek ve ulaşım kartına ek destek verilsin.")
    b3 = fikir(56.5, "defne", k10, "Burs miktarı her yıl öğrenci temsilcileriyle birlikte belirlensin.")
    tartisma(k10, [
        (57, "mert", "ARGUMAN", "Kira artışları özellikle ikinci dönemde bursun yarısını eritiyor.", b1),
        (55, "kaan.hoca", "KARSI_ARGUMAN", "Otomatik artış bütçeyi öngörülemez yapar; burs verilen kişi sayısı azalabilir.", b1),
        (53, "selin", "ARGUMAN", "Kart desteği doğrudan temel ihtiyaca gider; kötüye kullanım da azalır.", b2),
        (50, "can", "SORU", "Burs kaynağı üniversite mi, vakıf mı? Kararı kim uygulayacak?", None),
        (47, "defne", "ARGUMAN", "Temsilci katılımı olursa hangi harcamanın arttığı daha iyi anlaşılır.", b3),
        (44, "onur", "KAYNAK", "Son iki yılda öğrenci evlerinin kiraları ortalama iki kattan fazla arttı.", None),
    ])

    # ================= 7) Yemekhane oylaması, reddedilen kategori, plastik bardak =================
    baslat(56, k3)
    bitir(52, t_magazin)                                                     # ret: çoğunluk ayrı kategori istemedi
    tur(50, k3, {f1: ["dr.deniz", "ayse", "elif", "selin", "ece"], f2: ["mehmet", "zeynep", "kaan.hoca", "can", "onur", "defne"],
                 oylama.CEKIMSER: ["burak"]})
    k8 = konu(40, "ece", "Kampüste tek kullanımlık plastik bardak kalksın",
              "Kantinlerde ve kahve noktalarında her gün yüzlerce tek kullanımlık bardak çöpe gidiyor. İklim ve çevre için "
              "kampüste plastik atığı azaltalım.", _kategori(db, "Bilim", "Çevre ve İklim"))
    p1 = fikir(39.5, "ece", k8, "Depozitolu kupa sistemi gelsin; kupayı iade edene ücret geri ödensin.")
    p2 = fikir(39, "can", k8, "Kendi bardağını getirene kahvede indirim yapılsın.")
    p3 = fikir(37, "mert", k8, "Plastik tamamen yasaklansın, yalnızca kağıt bardak kalsın.")
    tartisma(k8, [
        (38, "dr.deniz", "ARGUMAN", "Depozito sistemleri birçok festivalde atığı ciddi biçimde azalttı.", p1),
        (36, "zeynep", "KARSI_ARGUMAN", "Kupaların yıkanması için ek personel ve su gerekir.", p1),
        (34, "selin", "ARGUMAN", "İndirim hem ucuz hem hemen uygulanabilir; alışkanlık yavaş yavaş değişir.", p2),
        (31, "kaan.hoca", "KARSI_ARGUMAN", "Kağıt bardakların çoğu da plastik kaplıdır, geri dönüşümü zordur.", p3),
        (27, "onur", "KAYNAK", "Kağıt bardağın iç yüzeyindeki kaplama yüzünden çoğu tesis onları geri dönüştüremiyor.", p3),
        (24, "ayse", "ARGUMAN", "Kampüs kulüpleri kupa tasarım yarışması yapabilir, kupa sahiplenmeyi artırır.", p1),
        (21, "mehmet", "SORU", "Depozito ücreti ne kadar olmalı ki kimse kupayı atmasın?", p1),
    ])
    baslat(36, k10)
    tur(34, k10, {b1: ["onur", "mert", "can", "zeynep"], b2: ["ayse", "selin", "elif"], b3: ["defne", "mehmet", "ece"]})

    # ================= Yönetmelik değişikliği =================
    saat(30)
    t_ym = yonetmelik.degisiklik_teklif_et(db, u("mehmet"), {"tur": "PARAMETRE", "kod": "YETER_SAYI_ORANI", "yeni": "0.3"},
                                           "Kararların meşruiyeti için daha geniş katılım gerekli; oy hakkı olanların "
                                           "en az üçte biri oy vermeli.")
    evet_hayir(29, t_ym, evet=["ayse", "defne", "onur"], hayir=["zeynep", "can"])
    tur(26, k10, {b1: ["kaan.hoca"], b2: ["burak"]})

    # ================= 8) Gençlik meclisi: günün en çok konuşulan konusu =================
    k9 = konu(22, "defne", "Mahallelere gençlik meclisi kurulsun",
              "Belediyelerin gençlerle ilgili kararlarında gençlerin sesi yok. Her mahallede seçimle gelen, belediye "
              "meclisine önerge verebilen bir gençlik meclisi kurulmasını tartışalım.", _kategori(db, "Siyaset", "Yerel Yönetim"))
    g1 = fikir(21.5, "defne", k9, "Her mahallede 15–25 yaş arası gençlerin seçtiği bir gençlik meclisi kurulsun.")
    g2 = fikir(21, "zeynep", k9, "Meclis yerine belediyede çevrimiçi bir gençlik öneri platformu açılsın.")
    g3 = fikir(19.5, "onur", k9, "Gençlik meclisi olsun ama bütçesi ve kararları herkese açık yayımlansın.")
    tartisma(k9, [
        (21.2, "mehmet", "ARGUMAN", "Seçimle gelen temsilciler belediye meclisinde daha çok ciddiye alınır.", g1),
        (20.5, "kaan.hoca", "SORU", "Gençlik meclisinin kararları bağlayıcı mı olacak, yoksa tavsiye niteliğinde mi?", g1),
        (20, "can", "KARSI_ARGUMAN", "Seçim süreci uzun sürer; çevrimiçi platformla hemen başlanabilir.", g1),
        (18.5, "ece", "ARGUMAN", "Çevrimiçi platform daha çok genç ulaşır, özellikle çalışan gençler için.", g2),
        (17.5, "dr.deniz", "KARSI_ARGUMAN", "Çevrimiçi öneriler çoğu zaman cevapsız kalıyor; bir muhatap gerekir.", g2),
        (16, "selin", "ARGUMAN", "Açık bütçe olmazsa meclis göstermelik kalır; şeffaflık şart.", g3),
        (14.5, "burak", "SORU", "Seçimlere kaç yaşından itibaren katılınabilecek?", g1),
        (13, "defne", "KAYNAK", "Birçok Avrupa şehrinde gençlik meclisleri belediye bütçesinin küçük bir kısmını yönetiyor.", None),
        (11, "mert", "ARGUMAN", "Mahalle yerine ilçe düzeyinde olursa katılım daha yüksek olur.", g1),
        (8, "ayse", "ARGUMAN", "İkisi birlikte olabilir: meclis seçilir, öneriler çevrimiçi toplanır.", g3),
        (5, "zeynep", "KARSI_ARGUMAN", "Ne kadar yapı kurulursa o kadar bürokrasi; basit başlamalıyız.", g3),
        (2.5, "onur", "ARGUMAN", "Bütçenin herkese açık olması güveni artırır, katılımı da büyütür.", g3),
    ])

    # ================= 9) İtiraz konusu: final projesi kararına =================
    k1i = konu(20, "zeynep", "Final projesinde farklı teknoloji deneyen gruplara ek puan verilsin",
               "Tek dil kararı pratik ama grupların farklı teknolojileri denemesi akran öğrenmesinin en güçlü yanıydı. "
               "Kararı yeniden tartışalım: en azından ek bir teknoloji deneyen gruplar ödüllendirilsin.",
               _kategori(db, "Teknoloji", "Yazılım"), itiraz=k1, min_yas=18)
    ek = fikir(19.8, "zeynep", k1i, "Ek bir dil ya da çatı kullanan gruplara %10 ek puan verilsin.")
    tartisma(k1i, [
        (19, "mehmet", "ARGUMAN", "Ek puan, ortak dil kararını bozmadan çeşitliliği teşvik eder.", ek),
        (15, "kaan.hoca", "KARSI_ARGUMAN", "Ek puan, dersin temel hedefinden sapan grupları ödüllendirebilir.", ek),
        (9, "ece", "SORU", "Ek teknoloji raporda ayrıca anlatılırsa değerlendirme kolaylaşmaz mı?", None),
    ])

    # ================= 10) İstanbul gece hatları: tartışmada; alt konular, gizleme oylaması =================
    k4 = konu(18, "mehmet", "İstanbul'da öğrenci indirimi gece hatlarında da geçerli olsun",
              "Gece 00.00'dan sonra çalışan otobüs ve vapur hatlarında öğrenci indirimi uygulanmıyor. Bu konuya sadece "
              "İstanbul'da oturanlar katılabilir; diğerleri gözlemci.", _kategori(db, "Siyaset", "Ulaşım"),
              konum_id=_konum(db, "İstanbul"))
    h1 = fikir(17.8, "mehmet", k4, "Öğrenci indirimi 24 saat geçerli olsun.")
    h2 = fikir(17, "ayse", k4, "Gece hatlarında öğrencilere ücretsiz aktarma hakkı verilsin.")
    tartisma(k4, [
        (16.5, "elif", "ARGUMAN", "Gece çalışan öğrenciler en çok bu saatlerde ulaşıma ihtiyaç duyuyor.", h1),
        (15.5, "kaan.hoca", "KARSI_ARGUMAN", "Gece hatlarının işletme maliyeti yüksek; tam gün indirim bütçeyi zorlar.", h1),
        (14, "yonetici", "ARGUMAN", "Aktarma hakkı daha düşük maliyetle aynı ihtiyacı karşılar.", h2),
        (12.5, "mehmet", "KAYNAK", "Belediyenin yolcu sayımına göre gece hatlarını en çok 18–25 yaş arası kullanıyor.", None),
        (10, "mehmet", "KARSI_ARGUMAN", "Aktarma hakkı tek hatla giden öğrencinin işine yaramaz.", h2),
        (7.5, "defne", "ARGUMAN", "Vapur seferleri gece de olsa indirim olmadıkça öğrenciler taksiye mecbur kalıyor.", h1),
    ])
    konu_disi = yaz(6.5, "burak", k4, "ARGUMAN", "Bu arada hafta sonu halı saha maçı var, gelmek isteyen yazsın.")

    # ================= 11) Plastik bardak oylaması, tiyatro konusu, Genel =================
    baslat(16, k8)
    tur(15, k8, {p1: ["ece", "dr.deniz", "ayse", "selin", "defne"], p2: ["can", "burak", "zeynep"], p3: ["mert"]})
    k14 = konu(16, "defne", "Bahar şenliğinde öğrenci tiyatrosu sahnelensin",
               "Tiyatro toplulukları yıl boyu prova yapıyor ama sahne bulamıyor. Bahar şenliğinin ikinci günü açık hava "
               "sahnesinde öğrenci oyunlarına yer ayrılsın.", _kategori(db, "Kültür ve Sanat", "Tiyatro"))
    s1 = fikir(15.5, "defne", k14, "Şenliğin ikinci günü akşam saatleri öğrenci tiyatrosuna ayrılsın.")
    tartisma(k14, [
        (14, "selin", "ARGUMAN", "Kısa oyunlar arka arkaya sahnelenirse birden fazla topluluk yer bulur.", s1),
        (9.5, "ece", "SORU", "Ses ve ışık düzeni için bütçe var mı?", s1),
        (6, "can", "ARGUMAN", "Müzik kulübü de oyunların arasında kısa performanslarla destek olabilir.", s1),
    ])
    k13 = konu(14, "mert", "Foruma Spor ve Oyun diye yeni bir ana kategori eklensin mi?",
               "Halı saha, turnuva, satranç ve espor konuları şu an Genel'de ya da Sağlık › Spor'da kayboluyor. "
               "Ayrı bir ana kategori açılsın mı, yoksa mevcut yapı yeterli mi?", _kategori(db, "Genel"))
    tartisma(k13, [
        (13.5, "burak", "ARGUMAN", "Turnuva duyuruları için ayrı bir yer iyi olur; sağlıkla ilgisi yok.", None),
        (12.5, "dr.deniz", "KARSI_ARGUMAN", "Spor zaten Sağlık altında var; ayrı kategori konuları bölebilir.", None),
        (11, "ayse", "SORU", "Espor da bu kategoriye girer mi, yoksa Teknoloji altında mı olmalı?", None),
        (7, "mert", "ARGUMAN", "Öneriyi Kategoriler sayfasından oylamaya sundum; herkes oy verebilir.", None),
    ])
    saat(13)
    t_spor = kategoriler.oner(db, u("mert"), "Spor ve Oyun", None, "futbol, turnuva, espor, satranc, mac, oyun",
                              "Spor ve oyun konuları Genel'de kayboluyor; turnuva ve takım duyuruları için ayrı bir yer gerekiyor.")
    evet_hayir(12.8, t_spor, evet=["mert", "burak", "can", "elif", "onur", "ece"], hayir=["dr.deniz"])

    # ================= 12) Yapay zeka kuralı, alt konular =================
    k11 = konu(12, "kaan.hoca", "Ödevlerde yapay zeka kullanımı için ortak bir kural olsun",
               "Bazı dersler yapay zeka araçlarını tamamen yasaklıyor, bazıları serbest bırakıyor. Öğrenciler ne zaman "
               "neyin serbest olduğunu bilmiyor. Bölüm genelinde ortak ve açık bir kural belirleyelim.",
               _kategori(db, "Teknoloji", "Yapay Zeka"))
    y1 = fikir(11.8, "kaan.hoca", k11, "Yapay zeka kullanılabilir ama ödevde nerede ve nasıl kullanıldığı açıkça yazılsın.")
    y2 = fikir(11, "zeynep", k11, "Sınav ve proje dışındaki alıştırmalarda serbest, notlu ödevlerde yasak olsun.")
    y3 = fikir(8.5, "can", k11, "Her ders kendi kuralını izlencede ilk hafta ilan etsin.")
    tartisma(k11, [
        (11.5, "ece", "ARGUMAN", "Açıkça yazmak dürüstlüğü ödüllendirir; yasak olunca herkes gizli kullanıyor.", y1),
        (10.5, "dr.deniz", "SORU", "Yapay zekanın ürettiği metnin kaynak gösterilmesi yeterli mi?", y1),
        (9, "mehmet", "KARSI_ARGUMAN", "Notlu ödevde yasak koymak denetlenemez; kural uygulanamaz olur.", y2),
        (7, "selin", "ARGUMAN", "Ders bazında kural, farklı derslerin farklı amaçlarına uyar.", y3),
        (4.5, "onur", "KARSI_ARGUMAN", "Her ders farklı kural koyarsa öğrenciler yine karışıklık yaşar.", y3),
        (3, "ayse", "ARGUMAN", "Ortak bir çerçeve ve ders bazında küçük eklemeler en dengelisi olur.", y1),
        (1.5, "kaan.hoca", "KAYNAK", "Birçok üniversite 'kullanım beyanı' şablonu yayımladı; ödevin sonuna eklenen kısa bir bölüm.", None),
    ])
    alt = konu(12, "mehmet", "Beşiktaş gece otobüs hatları",
               "Beşiktaş'tan geçen gece otobüs hatlarının sıklığı ve güzergâhları. Sadece Beşiktaş sakinleri katılır.",
               _kategori(db, "Siyaset", "Ulaşım"), ust=k4, konum_id=_konum(db, "İstanbul", "Beşiktaş"))
    fikir(11.5, "mehmet", alt, "Gece hatları 30 dakikada bir kalksın.")
    yaz(10.5, "mehmet", alt, "ARGUMAN", "Şu an bir saatte bir sefer var; durakta beklemek güvenli değil.")
    yaz(9.5, "defne", alt, "ARGUMAN", "Sahil yolu güzergâhı da gece hattına eklensin.")
    konu(8, "ayse", "Kadıköy iskelesinden gece vapur seferleri",
         "Kadıköy'den karşıya gece vapuru olmaması öğrencileri pahalı taksiye mecbur bırakıyor. Gece seferleri konulmalı.",
         _kategori(db, "Siyaset", "Ulaşım"), ust=k4, konum_id=_konum(db, "İstanbul", "Kadıköy"))

    # ================= 13) Son saatler =================
    bitir(8, konu_id=k3)                                                     # oy alamayan fikir elendi, 2. tur başladı
    k16 = konu(9, "onur", "Kampüste aylık gökyüzü gözlem gecesi düzenlensin",
               "Fizik bölümünün teleskopları yılın çoğunda kullanılmıyor. Ayda bir akşam herkese açık gökyüzü gözlemi "
               "yapılsın; astronomi kulübü de rehberlik edebilir.", _kategori(db, "Bilim", "Fizik"))
    fikir(8.8, "onur", k16, "Her ayın ilk cuma akşamı futbol sahasında gözlem gecesi yapılsın.")
    yaz(7.8, "dr.deniz", k16, "ARGUMAN", "Işık kirliliği az olan saha kenarı gözlem için en uygun yer.")
    yaz(6.2, "elif", k16, "SORU", "Lise öğrencileri de katılabilir mi?")
    tur(7, k3, {f1: ["ayse", "selin", "dr.deniz"], f2: ["mehmet"]})
    tur(6, k10, {b3: ["yonetici"]})
    k6 = konu(6, "burak", "Kampüste enerji içeceği satışı yasaklansın",
              "Sınav haftalarında aşırı enerji içeceği tüketimi sağlık sorunlarına yol açıyor. Kantin ve otomatlarda "
              "satışı yasaklansın.", _kategori(db, "Sağlık", "Beslenme"))
    fikir(5.8, "burak", k6, "Kantin ve otomatlarda enerji içeceği satılmasın.")
    e2 = fikir(5.2, "dr.deniz", k6, "Yasak yerine kafein miktarı etikette büyük yazılsın ve bilgilendirme yapılsın.")
    yaz(4.8, "ayse", k6, "ARGUMAN", "Bilgilendirme yasaktan daha kalıcı bir alışkanlık değişikliği sağlar.", e2)
    saat(5)
    t_gizle = konular.mesaj_silme_teklifi(db, u("ayse"), konu_disi, "Konu dışı", "Tartışmayla ilgisi yok.")
    evet_hayir(4.9, t_gizle, evet=["ayse", "mehmet", "defne"])
    tur(4.5, k8, {p1: ["mehmet", "onur"], p2: ["kaan.hoca"]})
    k15 = konu(4, "elif", "Forumda haftalık soru-cevap saati olsun",
               "Her pazar akşamı bir uzman ya da hoca bir saat boyunca forumda soruları yanıtlasın. Yeni gelenler için de "
               "forumu tanımanın iyi bir yolu olur.", _kategori(db, "Genel"))
    tartisma(k15, [
        (3.5, "kaan.hoca", "ARGUMAN", "İlk soru-cevap saatini ben yapabilirim; yazılım ve yapay zeka üzerine.", None),
        (2.8, "selin", "SORU", "Sorular önceden toplanırsa daha verimli olur mu?", None),
    ])
    evet_hayir(3.2, t_spor, evet=["defne", "zeynep"], hayir=["kaan.hoca"])
    saat(3)
    t_uzman = uzmanlik.basvur(db, u("mehmet"), _kategori(db, "Siyaset", "Ulaşım"),
                              "Şehir ve bölge planlama 4. sınıf öğrencisiyim; belediyede ulaşım planlaması stajı yaptım.")
    evet_hayir(2.6, t_uzman, evet=["ayse", "defne"])
    konu(2, "zeynep", "Ankara'da kampüs ring servisleri gece 23.00'e kadar çalışsın",
         "Kütüphaneden geç çıkan öğrenciler için ring servislerinin son saati uzatılsın; güvenli ulaşım sağlanır.",
         _kategori(db, "Siyaset", "Ulaşım"))
    saat(1)
    yz.tartisma_ozeti(db, k9)                                                # bir katılımcı özet istedi
    return {"k1": k1, "k1i": k1i, "k2": k2, "k3": k3, "k4": k4, "k5": k5, "k8": k8, "k9": k9, "k10": k10, "k12": k12,
            "k13": k13, "k14": k14}
