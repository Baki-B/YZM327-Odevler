"""Forumun iş kurallarını doğrulayan testler.   Çalıştırmak için:  python -m unittest discover testler"""
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forum import (anlik, arama, ayarlar, defter, devir, gorevler, graf, gundem, gunluk, guvenlik, kararlar,  # noqa: E402
                   kategoriler, konular, kullanicilar, ontoloji, oylama, sikayetler, sonuclar, uzmanlik, veritabani, yonetim,
                   yonetmelik, yz, zaman)
from forum.hatalar import KuralHatasi  # noqa: E402

SIFRE = "sifre1234"


class Ortam(unittest.TestCase):
    """Her test boş bir veritabanı ve boş bir dağıtık defterle başlar."""

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.yol = os.path.join(self.klasor.name, "test.db")
        self.db = veritabani.hazirla(self.yol)
        ontoloji.yukle(self.db)
        yonetmelik.yukle(self.db)
        self.db.commit()
        self._gercek_simdi = zaman.simdi

    def tearDown(self):
        zaman.simdi = self._gercek_simdi
        self.db.close()
        self.klasor.cleanup()

    # --- yardımcılar ---
    def konum(self, il, ilce=None):
        il_id = self.db.execute("SELECT id FROM konumlar WHERE ad = ? AND tur = 'IL'", (il,)).fetchone()["id"]
        if not ilce:
            return il_id
        return self.db.execute("SELECT id FROM konumlar WHERE ad = ? AND ust_id = ?", (ilce, il_id)).fetchone()["id"]

    def kategori(self, alan, alt=None):
        ust = self.db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id IS NULL", (alan,)).fetchone()["id"]
        if not alt:
            return ust
        return self.db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id = ?", (alt, ust)).fetchone()["id"]

    def kisi(self, takma, yas=25, il="İstanbul", ilce="Kadıköy"):
        dogum = date(zaman.simdi().year - yas, 1, 1).isoformat()
        kullanicilar.kayit(self.db, "Test Kişi", takma, SIFRE, SIFRE, dogum, self.konum(il, ilce))
        return kullanicilar.takma_ad_ile(self.db, takma)

    def kisiler(self, n, on_ek="kisi"):
        return [self.kisi(f"{on_ek}{i}") for i in range(n)]

    def yz(self, takma="Bilge"):
        self.db.execute("INSERT INTO kullanicilar (takma_ad, yz_mi, olusturma) VALUES (?, 1, ?)",
                        (takma, zaman.simdi_metin()))
        return kullanicilar.takma_ad_ile(self.db, takma)

    def konu(self, sahip, **ek):
        form = {"baslik": "Yemekhane menüsü tartışması", "kategori_id": self.kategori("Sağlık", "Beslenme"),
                "aciklama": "Yemekhanede sağlıklı beslenme için menüde daha fazla sebze ve baklagil olsun."}
        form.update(ek)
        return konular.konu_ac(self.db, sahip, form, ek.get("ust_id"), ek.get("itiraz_id"))

    def durum(self, konu_id):
        return konular.konu_getir(self.db, konu_id)["durum"]

    def fikirli_konu(self, yazarlar, **ek):
        """Her yazar bir fikir yazar ve 1. tur başlar. Döner: (konu, fikir mesajlarının id'leri)"""
        k = self.konu(yazarlar[0], **ek)
        fikirler = [konular.fikir_yaz(self.db, y, k, f"{i + 1} numaralı fikir: menü böyle olsun") for i, y in enumerate(yazarlar)]
        konular.oylamayi_baslat(self.db, k)
        return k, fikirler

    def tur(self, konu_id):
        return oylama.acik_teklif(self.db, "KARAR", konu_id=konu_id)

    def secenek(self, teklif_id, mesaj_id):
        return str(self.db.execute("SELECT id FROM secenekler WHERE teklif_id = ? AND mesaj_id = ?",
                                   (teklif_id, mesaj_id)).fetchone()["id"])

    def oyla(self, konu_id, dagilim, bitir=True):
        """Süren turda oy verdirir. dagilim: [(fikir mesajının id'si ya da "CEKIMSER", [oy verenler]), ...]"""
        t = self.tur(konu_id)["id"]
        for hedef, kimler in dagilim:
            secim = hedef if hedef == oylama.CEKIMSER else self.secenek(t, hedef)
            for kim in kimler:
                oylama.oy_ver(self.db, t, kim, secim, "Alanımdaki bilgiye dayanarak bu yönde oy veriyorum.")
        if bitir:
            oylama.sonuclandir(self.db, t)
        return t

    def uzman_yap(self, kisi, *kategori):
        uzmanlik.uzmanlik_ver(self.db, kisi["id"], self.kategori(*kategori))

    def ileri_sar(self, **sure):
        hedef = self._gercek_simdi() + timedelta(**sure)
        zaman.simdi = lambda: hedef


class OntolojiVeYonetmelik(Ortam):
    def test_konum_benzerligi(self):
        kadikoy = self.konum("İstanbul", "Kadıköy")
        b = lambda x: ontoloji.benzerlik(self.db, "konumlar", x, kadikoy)  # noqa: E731
        self.assertEqual(b(kadikoy), 1.0)
        self.assertAlmostEqual(b(self.konum("İstanbul", "Beşiktaş")), 2 / 3)
        self.assertAlmostEqual(b(self.konum("Bursa")), 1 / 3)
        self.assertEqual(b(self.konum("Ankara")), 0.0)

    def test_kavram_eslestirme_ve_yer_adlari(self):
        terimler, _ = ontoloji.kategori_iliskisi(self.db, "Yemekhane menüsünde protein az",
                                                 self.kategori("Sağlık", "Beslenme"))
        self.assertIn("protein", terimler)
        self.assertEqual(ontoloji.metindeki_yerler(self.db, "İstanbul'da gece vapuru"), [self.konum("İstanbul")])

    def test_hakaret_iceren_konu_engellenir(self):
        with self.assertRaises(KuralHatasi):
            self.konu(self.kisi("ali"), aciklama="Bu menüyü savunanlar cahil, yemekhane rezalet durumda.")

    def test_konum_uyarisi_ve_kategori_onerisi(self):
        rapor = yonetmelik.denetle(self.db, "Ankara'da otobüs seferleri artsın",
                                   "Ankara'da ring otobüsleri gece de çalışsın, ulaşım kolaylaşsın.",
                                   self.kategori("Kültür ve Sanat", "Sinema"))
        kodlar = {b["kod"] for b in rapor["uyarilar"]}
        self.assertIn("D4", kodlar)   # metinde Ankara geçiyor ama katılım herkese açık
        self.assertIn("D3", kodlar)   # sinemayla ilgisi yok
        self.assertEqual(rapor["onerilen_kategori"], self.kategori("Siyaset", "Ulaşım"))

    def test_mesajda_kisisel_veri_engellenir(self):
        with self.assertRaises(KuralHatasi):
            yonetmelik.mesaj_denetle(self.db, "Beni 0532 123 45 67 numarasından ara")

    def test_korunan_parametre_dortte_uc_ister(self):
        kisiler = self.kisiler(4, "uye")
        t = yonetmelik.degisiklik_teklif_et(self.db, kisiler[0], {"tur": "PARAMETRE", "kod": "MAX_DEVIR", "yeni": "3"},
                                            "Güç yoğunlaşmasını daha da azaltmak istiyoruz.")
        self.assertEqual(oylama.teklif_getir(self.db, t)["esik"], "DORTTE_UC")
        for k in kisiler:
            oylama.oy_ver(self.db, t, k, "EVET")
        self.assertEqual(yonetmelik.deger(self.db, "MAX_DEVIR"), 3)

    def test_denetim_maddesi_kapatilabilir(self):
        yonetmelik.degisikligi_uygula(self.db, {"tur": "DENETIM", "kod": "D1", "yeni": "KAPALI"})
        yonetmelik.mesaj_denetle(self.db, "Bu fikir cahilce.")   # artık engellemez

    def test_varsayilan_sureler_ve_esikler(self):
        d = lambda kod: yonetmelik.deger(self.db, kod)  # noqa: E731
        self.assertEqual((d("SURE_TARTISMA_SAAT"), d("SURE_TUR1_SAAT"), d("SURE_TUR_SAAT")), (24, 48, 24))
        self.assertEqual([d(f"ELEME_TUR{i}") for i in range(1, 5)], [0.05, 0.05, 0.10, 0.20])
        self.assertEqual((d("ESIK_EZICI"), d("ESIK_MESAJ_SILME")), (0.75, "DORTTE_UC"))


class KonuAkisi(Ortam):
    def test_konu_hemen_tartismaya_acilir(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        k = self.konu(a)
        self.assertEqual(self.durum(k), "TARTISMA")           # kabul oylaması yok
        konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "Katılıyorum")

    def test_sure_dolunca_oylama_baslar_ve_turlar_ilerler(self):
        a, b, c = self.kisiler(3)
        k = self.konu(a)
        fa = konular.fikir_yaz(self.db, a, k, "Haftada iki gün etsiz menü olsun.")
        fb = konular.fikir_yaz(self.db, b, k, "Her gün iki seçenek sunulsun.")
        self.ileri_sar(hours=23)
        gorevler.tick(self.db)
        self.assertEqual(self.durum(k), "TARTISMA")           # 24 saat dolmadı
        self.ileri_sar(hours=25)
        gorevler.tick(self.db)
        konu = konular.konu_getir(self.db, k)
        self.assertEqual((konu["durum"], konu["tur"]), ("OYLAMA", 1))
        self.oyla(k, [(fa, [a, c]), (fb, [b])], bitir=False)
        self.assertEqual(self.tur(k)["tur_no"], 1)            # herkes oy verse de tur süresini doldurur
        self.ileri_sar(hours=25 + 47)
        gorevler.tick(self.db)
        self.assertEqual(self.tur(k)["tur_no"], 1)            # 1. tur 48 saat
        self.ileri_sar(hours=25 + 49)
        gorevler.tick(self.db)
        self.assertEqual(self.tur(k)["tur_no"], 2)            # %67 ve %33: ikisi de kaldı
        self.ileri_sar(hours=25 + 49 + 25)                    # 2. tur 24 saat; kimse oy vermedi
        gorevler.tick(self.db)
        self.assertEqual(self.durum(k), "SONUCSUZ")

    def test_kisi_basi_tek_fikir(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        k = self.konu(a)
        konular.fikir_yaz(self.db, b, k, "Haftada iki gün etsiz menü olsun.")
        with self.assertRaises(KuralHatasi):
            konular.fikir_yaz(self.db, b, k, "Bir fikrim daha var, onu da yazayım.")
        with self.assertRaises(KuralHatasi):                   # fikir, normal mesaj türü olarak yazılamaz
            konular.mesaj_yaz(self.db, b, k, "FIKIR", "Arka kapıdan ikinci fikir.")
        self.assertEqual(len(konular.fikirler(self.db, k)), 1)

    def test_fikir_birinci_tur_bitene_kadar_yazilir(self):
        a, b, c, d = self.kisiler(4)
        k, (fa, fb) = self.fikirli_konu([a, b])
        fc = konular.fikir_yaz(self.db, c, k, "Tur sürerken eklenen üçüncü fikir.")
        self.assertEqual(len(oylama.secenekler(self.db, self.tur(k)["id"])), 3)   # oylamaya da eklendi
        self.oyla(k, [(fa, [a]), (fb, [b]), (fc, [c])])
        self.assertEqual(self.tur(k)["tur_no"], 2)
        with self.assertRaises(KuralHatasi):
            konular.fikir_yaz(self.db, d, k, "İkinci turda fikir yazmak istiyorum.")
        konular.mesaj_yaz(self.db, d, k, "ARGUMAN", "Ama tartışma oylama sırasında da sürer.")

    def test_mesaj_duzenlenir_eski_hali_gorunur_fikir_oylamada_kilitlenir(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        k = self.konu(a)
        m = konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "İlk yazdığım hâli.")
        f = konular.fikir_yaz(self.db, a, k, "Haftada iki gün etsiz menü olsun.")
        konular.mesaj_duzenle(self.db, b, m, "Düzelttiğim hâli.")
        self.assertEqual([s["icerik"] for s in konular.mesaj_surumleri(self.db, m)], ["İlk yazdığım hâli."])
        with self.assertRaises(KuralHatasi):                   # başkasının mesajı düzenlenemez
            konular.mesaj_duzenle(self.db, a, m, "Başkası değiştirmeye çalışıyor.")
        konular.fikir_yaz(self.db, b, k, "Her gün iki seçenek sunulsun.")
        konular.oylamayi_baslat(self.db, k)
        with self.assertRaises(KuralHatasi):                   # oylanan metin değişemez
            konular.mesaj_duzenle(self.db, a, f, "Haftada üç gün etsiz menü olsun.")
        self.assertFalse(hasattr(konular, "mesaj_sil"))        # silme diye bir işlem yok

    def test_konu_duzenleme_gecmisi(self):
        a = self.kisi("ali")
        k = self.konu(a)
        konular.konu_duzenle(self.db, a, k, {"baslik": "Yemekhane menüsü ve fiyat tartışması",
                                             "aciklama": "Yemekhanede menü ve fiyatlar birlikte ele alınsın, sebze artsın."})
        self.assertEqual(konular.konu_surumleri(self.db, k)[0]["baslik"], "Yemekhane menüsü tartışması")
        konular.oylamayi_baslat(self.db, k)
        with self.assertRaises(KuralHatasi):
            konular.konu_duzenle(self.db, a, k, {"baslik": "Oylama başladıktan sonra değişiklik",
                                                 "aciklama": "Oylama başladıktan sonra konu metni değiştirilemez."})

    def test_alt_konu_kurali_genisletemez(self):
        a = self.kisi("ali")
        k = self.konu(a, konum_id=self.konum("İstanbul"))
        with self.assertRaises(KuralHatasi):
            self.konu(a, ust_id=k, baslik="Ankara yemekhaneleri", konum_id=self.konum("Ankara"))
        alt = self.konu(a, ust_id=k, baslik="Kadıköy yemekhanesi menüsü", konum_id=self.konum("İstanbul", "Kadıköy"))
        self.assertEqual(self.durum(alt), "TARTISMA")

    def test_gozlemci_yazamaz_fikir_veremez(self):
        a, ankarali = self.kisi("ali"), self.kisi("ankarali", il="Ankara", ilce="Çankaya")
        k = self.konu(a, konum_id=self.konum("İstanbul"))
        with self.assertRaises(KuralHatasi):
            konular.mesaj_yaz(self.db, ankarali, k, "ARGUMAN", "Ben de yazmak istiyorum")
        with self.assertRaises(KuralHatasi):
            konular.fikir_yaz(self.db, ankarali, k, "Gözlemci olarak fikir vermek istiyorum.")

    def test_itiraz_konusu(self):
        a, b, c, d = self.kisiler(4)
        k, (fa, fb) = self.fikirli_konu([a, b])
        with self.assertRaises(KuralHatasi):                   # konu kapanmadan itiraz olmaz
            self.konu(b, itiraz_id=k, baslik="Menü kararına itiraz ediyoruz")
        self.oyla(k, [(fa, [a, c, d]), (fb, [b])])
        self.assertEqual(self.durum(k), "KARARA_BAGLANDI")
        with self.assertRaises(KuralHatasi):                   # kapanan konuya yazılmaz
            konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "Karardan sonra yazmak istiyorum.")
        itiraz = self.konu(b, itiraz_id=k, baslik="Menü kararına itiraz ediyoruz")
        self.assertEqual(self.durum(itiraz), "TARTISMA")
        self.assertEqual([i["id"] for i in konular.itirazlar(self.db, k)], [itiraz])


class FikirOylamasi(Ortam):
    def _karar(self, tur_no, oranlar, yeter=True):
        """Eleme kurallarını doğrudan dener. oranlar: fikirlerin oranları (büyükten küçüğe)."""
        s = {"yeter": yeter, "katilan": 10, "gerekli": 2,
             "secenekler": [{"anahtar": str(i), "oran": o, "kisi": 1 if o else 0, "metin": f"f{i}"}
                            for i, o in enumerate(oranlar)]}
        k = sonuclar.tur_karari(tur_no, s, *sonuclar.tur_kurallari(self.db, tur_no))   # saf fonksiyon: kurallar parametre
        return k.sonuc, len(k.kalanlar)

    def test_eleme_esikleri(self):
        self.assertEqual(self._karar(1, [.50, .30, .06, .049, .04]), ("DEVAM", 3))    # 1. tur: %5 altı elenir
        self.assertEqual(self._karar(2, [.50, .45, .05]), ("DEVAM", 3))               # tam %5 kalır
        self.assertEqual(self._karar(3, [.50, .41, .09]), ("DEVAM", 2))               # 3. tur: %10
        self.assertEqual(self._karar(4, [.45, .36, .19]), ("DEVAM", 2))               # 4. tur: %20
        self.assertEqual(self._karar(4, [.60, .19, .19]), ("KABUL", 1))               # geriye tek fikir kaldı

    def test_ezici_ustunluk_her_turda(self):
        for tur_no in range(1, 6):
            self.assertEqual(self._karar(tur_no, [.75, .25]), ("KABUL", 1), tur_no)
        self.assertEqual(self._karar(1, [.74, .26]), ("DEVAM", 2))

    def test_son_tur(self):
        self.assertEqual(self._karar(5, [.40, .35, .25]), ("KABUL", 1))               # en çok oy alan
        self.assertEqual(self._karar(5, [.40, .40, .20]), ("SONUCSUZ", 0))            # eşitlik

    def test_sonucsuz_durumlar(self):
        self.assertEqual(self._karar(1, [.60, .40], yeter=False), ("SONUCSUZ", 0))    # yeter sayı yok
        self.assertEqual(self._karar(1, []), ("SONUCSUZ", 0))                         # hiç fikir yok
        self.assertEqual(self._karar(4, [.15, .15, .15]), ("SONUCSUZ", 0))            # hiçbiri eşiği geçemedi

    def test_yedi_kucuk_fikir_ve_bir_buyuk(self):
        """Yedi fikir %5'in altında, sekizinci %68: ezici üstünlük yok ama tek kalan o, ilk turda kabul edilir."""
        kisiler = self.kisiler(22)
        k, fikirler = self.fikirli_konu(kisiler[:8])
        self.oyla(k, [(f, [kisiler[i]]) for i, f in enumerate(fikirler[:7])] + [(fikirler[7], kisiler[7:])])
        self.assertEqual(self.durum(k), "KARARA_BAGLANDI")
        self.assertEqual(kararlar.konu_karari(self.db, k)["metin"], "8 numaralı fikir: menü böyle olsun")

    def test_ezici_ustunlukle_ilk_turda_karar(self):
        a, b, c, d = self.kisiler(4)
        k, (fa, fb) = self.fikirli_konu([a, b])
        self.oyla(k, [(fa, [a, c, d]), (fb, [b])])             # 3/4 = %75
        karar = kararlar.konu_karari(self.db, k)
        self.assertEqual((self.durum(k), karar["durum"]), ("KARARA_BAGLANDI", "KESIN"))

    def test_bes_turun_tamami(self):
        kisiler = self.kisiler(10)
        k, (fa, fb, fc) = self.fikirli_konu(kisiler[:3])
        dagilim = [(fa, kisiler[:5]), (fb, kisiler[5:9]), (fc, kisiler[9:])]          # %50, %40, %10
        for beklenen_tur, secenek_sayisi in ((2, 3), (3, 3), (4, 3), (5, 2)):
            self.oyla(k, dagilim if beklenen_tur < 5 else dagilim)
            t = self.tur(k)
            self.assertEqual((t["tur_no"], len(oylama.secenekler(self.db, t["id"]))), (beklenen_tur, secenek_sayisi))
        self.oyla(k, [(fa, kisiler[:5]), (fb, kisiler[5:9]), (oylama.CEKIMSER, kisiler[9:])])
        self.assertEqual(self.durum(k), "KARARA_BAGLANDI")
        self.assertEqual(kararlar.konu_karari(self.db, k)["metin"], "1 numaralı fikir: menü böyle olsun")
        self.assertEqual(konular.konu_getir(self.db, k)["tur"], 5)

    def test_yeter_sayi_yoksa_sonucsuz(self):
        kisiler = self.kisiler(10)
        k, (fa,) = self.fikirli_konu(kisiler[:1])
        self.oyla(k, [(fa, kisiler[:1])])                      # 10 hak sahibinden 1'i: en az 2 gerekir
        self.assertEqual(self.durum(k), "SONUCSUZ")
        self.assertIsNone(kararlar.konu_karari(self.db, k))

    def test_cekimser_toplamda_sayilir(self):
        kisiler = self.kisiler(5)
        k, (fa, fb) = self.fikirli_konu(kisiler[:2])
        t = self.oyla(k, [(fa, kisiler[:3]), (oylama.CEKIMSER, kisiler[3:])], bitir=False)
        s = oylama.sayim(self.db, oylama.teklif_getir(self.db, t))
        self.assertAlmostEqual(s["oran"], 0.6)                 # çekimser olmasa %100 olurdu
        self.assertEqual((s["cekimser"]["kisi"], s["katilan"]), (2, 5))
        oylama.sonuclandir(self.db, t)
        self.assertEqual(self.durum(k), "KARARA_BAGLANDI")     # %75 yok ama oy alan tek fikir

    def test_cift_oran_uzman_tek_basina_kazanamaz(self):
        normaller, doktor = self.kisiler(3), self.kisi("doktor")
        self.uzman_yap(doktor, "Sağlık")
        k, (fd, fn) = self.fikirli_konu([doktor, normaller[0]])
        t = self.oyla(k, [(fd, [doktor]), (fn, normaller)], bitir=False)
        s = oylama.sayim(self.db, oylama.teklif_getir(self.db, t))
        oran = {x["mesaj_id"]: x for x in s["secenekler"]}
        self.assertEqual(oran[fd]["agirlik"], 10)              # uzman oyu 10 sayılır
        self.assertAlmostEqual(oran[fd]["oran"], 1 / 4)        # ağırlıkta 10/13 ama kişide 1/4: küçük olan
        self.assertAlmostEqual(oran[fn]["oran"], 3 / 13)       # kişide 3/4 ama ağırlıkta 3/13
        self.assertEqual(s["acik_oylar"][0]["takma_ad"], "doktor")   # uzman oyu açıktır

    def test_uzman_gerekcesiz_oy_veremez(self):
        a, doktor = self.kisi("ali"), self.kisi("doktor")
        self.uzman_yap(doktor, "Sağlık")
        k, (fa,) = self.fikirli_konu([a])
        with self.assertRaises(KuralHatasi):
            oylama.oy_ver(self.db, self.tur(k)["id"], doktor, self.secenek(self.tur(k)["id"], fa))

    def test_makbuz_ile_oy_dogrulanir(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        k, (fa,) = self.fikirli_konu([a])
        t = self.tur(k)
        secimler = oylama.secim_anahtarlari(self.db, t)
        makbuz = oylama.oy_ver(self.db, t["id"], b, secimler[0])
        self.db.commit()
        _, secim = defter.makbuz_dogrula(self.db.defter_klasoru, t["id"], makbuz, secimler)
        self.assertEqual(secim, secimler[0])
        self.assertIsNone(defter.makbuz_dogrula(self.db.defter_klasoru, t["id"], "YANLIS-KOD", secimler))

    def test_esikler(self):
        e = oylama.esik_saglandi
        self.assertFalse(e(2, 4, "SALT"))
        self.assertTrue(e(3, 5, "SALT"))
        self.assertTrue(e(2, 3, "UCTE_IKI"))
        self.assertFalse(e(2, 3, "DORTTE_UC"))
        self.assertTrue(e(3, 4, "DORTTE_UC"))


class Gizleme(Ortam):
    def _ortam(self, n):
        kisiler = self.kisiler(n)
        k = self.konu(kisiler[0])
        m = konular.mesaj_yaz(self.db, kisiler[1], k, "ARGUMAN", "Satılık bisikletim var, isteyen bana yazsın.")
        return kisiler, k, m

    def test_dortte_uc_ile_gizlenir_iz_kalir(self):
        kisiler, k, m = self._ortam(4)
        t = konular.mesaj_silme_teklifi(self.db, kisiler[0], m, "Konu dışı", "")
        self.assertEqual(oylama.teklif_getir(self.db, t)["esik"], "DORTTE_UC")
        for kim, secim in zip(kisiler, ("EVET", "HAYIR", "EVET", "EVET")):
            oylama.oy_ver(self.db, t, kim, secim)             # herkes oy verince oylama biter
        mesaj = konular.mesaj_getir(self.db, m)
        self.assertEqual(mesaj["gizli"], 1)
        self.assertIn("gizlendi", mesaj["gizlenme_notu"])
        self.assertIsNotNone(mesaj["icerik"])                  # veritabanından silinmedi

    def test_yuzde_yetmisbesin_alti_gizlemez(self):
        kisiler, k, m = self._ortam(5)
        t = konular.mesaj_silme_teklifi(self.db, kisiler[0], m, "Konu dışı", "")
        for kim, secim in zip(kisiler, ("EVET", "HAYIR", "EVET", "EVET", "HAYIR")):
            oylama.oy_ver(self.db, t, kim, secim)             # 3/5 = %60
        self.assertEqual(konular.mesaj_getir(self.db, m)["gizli"], 0)
        self.assertEqual(oylama.teklif_getir(self.db, t)["durum"], "RET")

    def test_cekimser_gizlemeyi_zorlastirir(self):
        kisiler, k, m = self._ortam(4)
        t = konular.mesaj_silme_teklifi(self.db, kisiler[0], m, "Konu dışı", "")
        for kim, secim in zip(kisiler, ("EVET", "CEKIMSER", "EVET", "EVET")):
            oylama.oy_ver(self.db, t, kim, secim)             # 3/4: çekimser paydada
        self.assertEqual(konular.mesaj_getir(self.db, m)["gizli"], 1)
        m2 = konular.mesaj_yaz(self.db, kisiler[1], k, "ARGUMAN", "Kiralık odam da var, haber verin.")
        t2 = konular.mesaj_silme_teklifi(self.db, kisiler[0], m2, "Konu dışı", "")
        for kim, secim in zip(kisiler, ("EVET", "CEKIMSER", "CEKIMSER", "EVET")):
            oylama.oy_ver(self.db, t2, kim, secim)            # 2/4: hiç Hayır yok ama çoğunluk sağlanmadı
        self.assertEqual(konular.mesaj_getir(self.db, m2)["gizli"], 0)

    def test_tartismanin_bir_kismi_tek_oylamayla_gizlenir(self):
        (a, b, c), k, m1 = self._ortam(3)
        m2 = konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "Kiralık odam da var, haber verin.")
        m3 = konular.mesaj_yaz(self.db, c, k, "ARGUMAN", "Sebze ağırlıklı menü sağlıklıdır.")
        t = konular.mesaj_silme_teklifi(self.db, a, [m1, m2], "Konu dışı", "")
        with self.assertRaises(KuralHatasi):   # aynı mesaj ikinci kez oylamaya çıkamaz
            konular.mesaj_silme_teklifi(self.db, c, [m2, m3], "Spam", "")
        for kim in (a, b, c):
            oylama.oy_ver(self.db, t, kim, "EVET")
        self.assertEqual([konular.mesaj_getir(self.db, m)["gizli"] for m in (m1, m2, m3)], [1, 1, 0])


class Uzmanlik(Ortam):
    GEREKCE = "Beslenme ve diyetetik mezunuyum, beş yıldır hastanede çalışıyorum."

    def setUp(self):
        super().setUp()
        self.alan = self.kategori("Sağlık", "Beslenme")
        self.aday, self.b, self.c, self.d = self.kisiler(4)
        self.k1 = self.konu(self.b)
        self.k2 = self.konu(self.c, baslik="Kantinde meyve satılsın",
                            aciklama="Kantinde abur cubur yerine taze meyve ve kuruyemiş satılsın, sağlıklı beslenelim.")

    def _on_sarti_sagla(self, kim):
        for i in range(3):
            konular.mesaj_yaz(self.db, kim, self.k1, "ARGUMAN", f"Beslenme üzerine {i + 1}. katkım.")
        for i in range(2):
            konular.mesaj_yaz(self.db, kim, self.k2, "ARGUMAN", f"Meyve üzerine {i + 1}. katkım.")

    def test_on_sart(self):
        konular.mesaj_yaz(self.db, self.aday, self.k1, "ARGUMAN", "Tek bir mesajım var.")
        with self.assertRaises(KuralHatasi):                   # 5 mesaj ve 2 konu gerekir
            uzmanlik.basvur(self.db, self.aday, self.alan, self.GEREKCE)
        self._on_sarti_sagla(self.aday)
        self.assertTrue(uzmanlik.on_sartlar(self.db, self.aday["id"], self.alan)["tamam"])
        uzmanlik.basvur(self.db, self.aday, self.alan, self.GEREKCE)

    def test_kontenjan_doluysa_basvuru_acilamaz(self):
        self._on_sarti_sagla(self.aday)
        for u in self.kisiler(3, "uzman"):
            self.uzman_yap(u, "Sağlık")
        self.assertFalse(uzmanlik.kontenjan(self.db, self.alan)["yer_var"])
        with self.assertRaises(KuralHatasi):
            uzmanlik.basvur(self.db, self.aday, self.alan, self.GEREKCE)
        fazla = self.kisi("fazla")
        self.assertFalse(uzmanlik.uzmanlik_ver(self.db, fazla["id"], self.alan))      # doğrudan da verilemez

    def test_alanin_katilimcilari_oylar(self):
        self._on_sarti_sagla(self.aday)
        konular.mesaj_yaz(self.db, self.d, self.k1, "SORU", "Bu menünün maliyeti ne olur?")
        disaridan = self.kisi("disaridan")                     # bu alanda hiç yazmadı
        t = uzmanlik.basvur(self.db, self.aday, self.alan, self.GEREKCE)
        self.assertEqual(oylama.teklif_getir(self.db, t)["esik"], "UCTE_IKI")
        for kim in (self.aday, disaridan):                     # aday ve alan dışındaki üye oy kullanamaz
            with self.assertRaises(KuralHatasi):
                oylama.oy_ver(self.db, t, kim, "EVET")
        oylama.oy_ver(self.db, t, self.d, "EVET")
        self.assertIsNone(self._uzman())
        # b ve c konuları açtı ama mesaj yazmadı: niş kitle yalnızca yazanlardır, d'nin oyuyla oylama biter
        self.assertEqual(oylama.teklif_getir(self.db, t)["durum"], "YETERSIZ")

    def _uzman(self):
        from forum import uygunluk
        return uygunluk.aktif_uzmanlik(self.db, self.aday["id"], self.alan)

    def test_kabul_edilince_oy_agirligi_artar_ve_sure_dolar(self):
        self._on_sarti_sagla(self.aday)
        for kim in (self.b, self.c, self.d):
            konular.mesaj_yaz(self.db, kim, self.k1, "ARGUMAN", "Ben de bu alanda yazıyorum.")
        t = uzmanlik.basvur(self.db, self.aday, self.alan, self.GEREKCE)
        for kim, secim in ((self.b, "EVET"), (self.c, "EVET"), (self.d, "HAYIR")):
            oylama.oy_ver(self.db, t, kim, secim)             # 2/3
        self.assertIsNotNone(self._uzman())
        tur = oylama.teklif_getir(self.db, konular.oylamayi_baslat(self.db, self.k1))
        self.assertEqual(oylama.oy_durumu(self.db, tur, self.aday)["agirlik"], 10)
        self.assertEqual(oylama.oy_durumu(self.db, tur, self.b)["agirlik"], 1)
        self.ileri_sar(days=181)
        self.assertIsNone(self._uzman())                       # 180 gün sonra kendiliğinden biter

    def test_yapay_zeka_ayni_sartlarla_aday_gosterilir(self):
        ai = self.yz()
        with self.assertRaises(KuralHatasi):                   # ön şart yapay zeka için de geçerli
            uzmanlik.basvur(self.db, self.b, self.alan, self.GEREKCE, aday_id=ai["id"])
        for konu_id, kac in ((self.k1, 3), (self.k2, 2)):
            for _ in range(kac):
                yz.tartisma_ozeti(self.db, konu_id)
        konular.mesaj_yaz(self.db, self.d, self.k1, "SORU", "Bu menünün maliyeti ne olur?")
        with self.assertRaises(KuralHatasi):                   # yapay zeka kendi başvuramaz
            uzmanlik.basvur(self.db, ai, self.alan, self.GEREKCE)
        with self.assertRaises(KuralHatasi):                   # bir üye başka bir üyeyi aday gösteremez
            uzmanlik.basvur(self.db, self.b, self.alan, self.GEREKCE, aday_id=self.c["id"])
        t = uzmanlik.basvur(self.db, self.b, self.alan, self.GEREKCE, aday_id=ai["id"])
        self.assertEqual(oylama.teklif_getir(self.db, t)["hedef_id"], ai["id"])

    def test_yonetici_uzman_atayamaz(self):
        from forum.web import yonetim_sayfalari
        self.assertFalse(hasattr(yonetim_sayfalari, "uzmanlik_ata"))
        self.assertFalse(hasattr(kullanicilar, "uzmanlik_ekle"))


class YapayZeka(Ortam):
    def test_yalnizca_ozet_yazar_oy_kullanmaz(self):
        a, b, c = self.kisiler(3)
        ai = self.yz()
        k, (fa, fb) = self.fikirli_konu([a, b])
        ozetler = self.db.execute("SELECT icerik FROM mesajlar WHERE konu_id = ? AND yazar_id = ?", (k, ai["id"])).fetchall()
        self.assertEqual(len(ozetler), 1)                      # oylama başlarken tartışma özeti
        self.assertIn("2 fikir", ozetler[0]["icerik"])
        t = self.tur(k)["id"]
        with self.assertRaises(KuralHatasi):
            oylama.oy_ver(self.db, t, ai, self.secenek(t, fa), "Yapay zeka olarak oy vermek istiyorum.")
        self.oyla(k, [(fa, [a, c]), (fb, [b])])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM oylar WHERE kullanici_id = ?", (ai["id"],)).fetchone()[0], 0)
        son = self.db.execute("SELECT icerik FROM mesajlar WHERE konu_id = ? AND yazar_id = ? ORDER BY id DESC",
                              (k, ai["id"])).fetchone()["icerik"]
        self.assertIn("1. tur özeti", son)                     # tur bitince tur özeti

    def test_yz_ye_oy_devredilemez_ve_konu_acamaz(self):
        a, ai = self.kisi("ali"), self.yz()
        with self.assertRaises(KuralHatasi):
            devir.devir_ekle(self.db, a, "Bilge", "GENEL")
        with self.assertRaises(KuralHatasi):
            self.konu(ai)
        t = yonetmelik.degisiklik_teklif_et(self.db, a, {"tur": "BEYAN", "baslik": "Kaynak göster",
                                                         "metin": "İddialar mümkünse kaynakla desteklenir."},
                                            "Tartışmanın kalitesini artırmak için gerekli.")
        with self.assertRaises(KuralHatasi):
            oylama.oy_ver(self.db, t, ai, "EVET", "YZ olarak katılmak istiyorum.")


class Devir(Ortam):
    def setUp(self):
        super().setUp()
        self.a, self.b, self.c = self.kisi("ali"), self.kisi("banu"), self.kisi("cem")
        self.k = self.konu(self.a)
        konular.fikir_yaz(self.db, self.a, self.k, "Bir fikir: menü değişsin.")

    def _oylama(self):
        return konular.oylamayi_baslat(self.db, self.k)

    def _sayim(self, t):
        return oylama.sayim(self.db, oylama.teklif_getir(self.db, t))

    def _secim(self, t, i=0):
        return oylama.secim_anahtarlari(self.db, oylama.teklif_getir(self.db, t))[i]

    def test_zincirleme_ve_dogrudan_oy(self):
        devir.devir_ekle(self.db, self.a, "banu", "GENEL")
        devir.devir_ekle(self.db, self.b, "cem", "GENEL")
        t = self._oylama()
        oylama.oy_ver(self.db, t, self.c, self._secim(t))
        self.assertEqual(self._sayim(t)["devredilen"], 2)
        oylama.oy_ver(self.db, t, self.a, self._secim(t, 1))
        self.assertEqual(self._sayim(t)["devredilen"], 1)   # ali kendi oy verdi, devri ezildi

    def test_dongu_engellenir(self):
        devir.devir_ekle(self.db, self.a, "banu", "GENEL")
        devir.devir_ekle(self.db, self.b, "cem", "GENEL")
        with self.assertRaises(KuralHatasi):
            devir.devir_ekle(self.db, self.c, "ali", "GENEL")

    def test_tavan_yonetmelikten_okunur(self):
        yonetmelik.degisikligi_uygula(self.db, {"tur": "PARAMETRE", "kod": "MAX_DEVIR", "yeni": "2"})
        vekil = self.kisi("vekil")
        for i in range(4):
            devir.devir_ekle(self.db, self.kisi(f"veren{i}"), "vekil", "GENEL")
        t = self._oylama()
        oylama.oy_ver(self.db, t, vekil, self._secim(t))
        s = self._sayim(t)
        self.assertEqual((s["devredilen"], s["dusen"].get("TAVAN")), (2, 2))


class EskiVeritabani(Ortam):
    def test_eski_akistaki_kayitlar_yeni_akisa_uyarlanir(self):
        a = self.kisi("baki")
        an = zaman.simdi_metin()
        kat = self.kategori("Sağlık", "Beslenme")
        idler = {}
        for durum in ("KOMISYON", "GENEL_KURUL", "TARTISMA", "KARAR_GECICI", "REDDEDILDI", "KARARA_BAGLANDI"):
            idler[durum] = self.db.execute(
                "INSERT INTO konular (sahip_id, kategori_id, baslik, aciklama, bilirkisi_agirlik, durum, olusturma) "
                "VALUES (?, ?, ?, 'Eski akıştan kalan konu açıklaması.', 10, ?, ?)", (a["id"], kat, f"Eski {durum}", durum, an)).lastrowid
        for tip, konu_id in (("KONU_KABUL", idler["GENEL_KURUL"]), ("BILIRKISI", None)):
            self.db.execute("INSERT INTO teklifler (tip, konu_id, hedef_id, acan_id, veri, esik, baslangic, bitis) "
                            "VALUES (?, ?, ?, ?, ?, 'SALT', ?, ?)",
                            (tip, konu_id, a["id"], a["id"], '{"kategori_id": %d}' % kat, an, an))
        m = konular.mesaj_yaz(self.db, a, idler["TARTISMA"], "ARGUMAN", "Eski bir mesaj; olduğu gibi kalmalı.")
        self.db.commit()
        self.db.close()
        self.db = veritabani.hazirla(self.yol)                 # sunucu yeni sürümle yeniden başlıyor
        yonetmelik.yukle(self.db)
        durumlar = {eski: konular.konu_getir(self.db, i) for eski, i in idler.items()}
        for eski in ("KOMISYON", "GENEL_KURUL", "TARTISMA"):
            self.assertEqual(durumlar[eski]["durum"], "TARTISMA", eski)
            self.assertIsNotNone(durumlar[eski]["tartisma_bitis"])
        self.assertEqual(durumlar["KARAR_GECICI"]["durum"], "KARARA_BAGLANDI")
        self.assertEqual(durumlar["REDDEDILDI"]["durum"], "SONUCSUZ")
        tipler = {t["tip"]: t["durum"] for t in self.db.execute("SELECT tip, durum FROM teklifler")}
        self.assertEqual(tipler, {"KONU_KABUL": "IPTAL", "UZMANLIK": "ACIK"})
        self.assertIsNotNone(kullanicilar.takma_ad_ile(self.db, "baki"))              # üyeler yerinde
        self.assertEqual(konular.mesaj_getir(self.db, m)["icerik"], "Eski bir mesaj; olduğu gibi kalmalı.")
        for t in self.db.execute("SELECT * FROM teklifler").fetchall():               # eski oylamalar da adlandırılabilir
            self.assertTrue(oylama.teklif_basligi(self.db, t))
        self.db.execute("UPDATE konular SET durum = 'OYLAMA', tur = 1 WHERE id = ?", (idler["TARTISMA"],))
        self.db.commit()
        self.db.close()
        self.db = veritabani.hazirla(self.yol)                 # ikinci açılışta yeni akıştaki konulara dokunulmaz
        self.assertEqual(self.durum(idler["TARTISMA"]), "OYLAMA")


class DagitikDefter(Ortam):
    def test_zincir_kurcalama_ve_onarim(self):
        self.konu(self.kisi("ali"))
        self.db.commit()
        self.assertTrue(defter.durum(self.db.defter_klasoru)["saglikli"])
        defter.boz_demo(self.db.defter_klasoru, "C")
        d = defter.durum(self.db.defter_klasoru)
        self.assertFalse(d["saglikli"])
        self.assertIsNotNone(d["bas"])   # 2/3 çoğunluk hâlâ uzlaşıyor
        self.assertEqual(next(x for x in d["dugumler"] if x["ad"] == "C")["durum"], "BOZUK")
        defter.onar(self.db.defter_klasoru, "C")
        self.assertTrue(defter.durum(self.db.defter_klasoru)["saglikli"])

    def test_silinen_ve_degistirilen_mesaj_yakalanir(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        k = self.konu(a)
        m1 = konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "Birinci mesaj")
        m2 = konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "İkinci mesaj")
        m3 = konular.mesaj_yaz(self.db, b, k, "ARGUMAN", "Üçüncü mesaj")
        konular.mesaj_duzenle(self.db, b, m3, "Üçüncü mesajın düzeltilmiş hâli")   # kurallı düzenleme sorun sayılmaz
        self.db.commit()
        self.assertEqual(defter.tutarlilik(self.db)["sorunlar"], [])
        self.db.execute("UPDATE mesajlar SET icerik = 'gizlice değişti' WHERE id = ?", (m1,))
        self.db.execute("DELETE FROM arama WHERE ref_id = ?", (m2,))
        self.db.execute("DELETE FROM mesajlar WHERE id = ?", (m2,))
        sorunlar = " ".join(defter.tutarlilik(self.db)["sorunlar"])
        self.assertIn(f"#{m1} numaralı mesaj defterdeki özetle uyuşmuyor", sorunlar)
        self.assertIn(f"#{m2} numaralı mesaj veritabanından SİLİNMİŞ", sorunlar)

    def test_geri_alinan_islem_deftere_yazilmaz(self):
        self.kisi("ali")
        self.db.commit()
        once = defter.durum(self.db.defter_klasoru)["uzunluk"]
        self.kisi("banu")
        self.db.rollback()
        self.db.commit()
        self.assertEqual(defter.durum(self.db.defter_klasoru)["uzunluk"], once)


class GrafVeGuvenlik(Ortam):
    def test_oy_gucu_ve_gini(self):
        a, b, c = self.kisi("ali"), self.kisi("banu"), self.kisi("cem")
        devir.devir_ekle(self.db, a, "banu", "GENEL")
        devir.devir_ekle(self.db, b, "cem", "GENEL")
        guc = graf.oy_gucleri(self.db)
        self.assertEqual((guc[a["id"]], guc[b["id"]], guc[c["id"]]), (0, 0, 3))
        self.assertAlmostEqual(graf.gini([1, 1, 1]), 0.0)
        self.assertGreater(graf.gini([0, 0, 3]), 0.6)

    def test_takip(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        self.assertTrue(graf.takip_et(self.db, a, b["id"]))
        self.assertEqual(graf.takip_sayilari(self.db, b["id"]), (1, 0))
        self.assertFalse(graf.takip_et(self.db, a, b["id"]))   # ikinci tıklama takibi bırakır

    def test_giris_kilidi(self):
        self.kisi("ali")
        for _ in range(ayarlar.GIRIS_DENEME_SINIRI):
            with self.assertRaises(KuralHatasi):
                kullanicilar.giris(self.db, "ali", "yanlis-sifre1", "1.2.3.4")
        with self.assertRaises(KuralHatasi):   # doğru şifreyle bile kilitli
            kullanicilar.giris(self.db, "ali", SIFRE, "1.2.3.4")

    def test_kurtarma_kodu(self):
        dogum = date(zaman.simdi().year - 20, 1, 1).isoformat()
        _, kod = kullanicilar.kayit(self.db, "Deneme Kişi", "deneme", SIFRE, SIFRE, dogum, self.konum("İzmir"))
        _, yeni_kod = kullanicilar.sifre_sifirla(self.db, "deneme", kod, "yenisifre99", "yenisifre99")
        kullanicilar.giris(self.db, "deneme", "yenisifre99")
        with self.assertRaises(KuralHatasi):   # eski kod artık geçersiz
            kullanicilar.sifre_sifirla(self.db, "deneme", kod, "baskasifre1", "baskasifre1")
        self.assertNotEqual(kod, yeni_kod)

    def test_zayif_sifre_reddedilir(self):
        with self.assertRaises(KuralHatasi):
            guvenlik.sifre_kontrol("sadeceharf", "sadeceharf")

    def test_turkce_karaktersiz_arama(self):
        self.konu(self.kisi("ali"), baslik="Öğrenci indirimi genişletilsin")
        self.assertEqual(len(arama.ara(self.db, "ogrenci")), 1)


class Web(unittest.TestCase):
    """Demo verisiyle (ornek_veri): konular başlıklarına göre bulunur."""

    @classmethod
    def setUpClass(cls):
        cls.klasor = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        from forum import create_app, ornek_veri
        cls.app = create_app({"VERITABANI": os.path.join(cls.klasor.name, "web.db"), "TESTING": True})
        ornek_veri.gerekirse_yukle(cls.app.config["VERITABANI"])

    @classmethod
    def tearDownClass(cls):
        cls.klasor.cleanup()

    def setUp(self):
        self.istemci = self.app.test_client()

    def _csrf(self):
        self.istemci.get("/giris")
        with self.istemci.session_transaction() as s:
            return s["csrf"]

    def giris(self, takma):
        return self.istemci.post("/giris", data={"takma_ad": takma, "sifre": "forum1234", "csrf": self._csrf()})

    def metin(self, adres):
        return self.istemci.get(adres).get_data(as_text=True)

    def vt(self):
        db = veritabani.baglan(self.app.config["VERITABANI"])
        self.addCleanup(db.close)
        return db

    def konu_no(self, parca):
        return self.vt().execute("SELECT id FROM konular WHERE baslik LIKE ?", (f"%{parca}%",)).fetchone()[0]

    def tur_no(self, parca):
        return self.vt().execute("SELECT id FROM teklifler WHERE tip = 'KARAR' AND durum = 'ACIK' AND konu_id = ?",
                                 (self.konu_no(parca),)).fetchone()[0]

    def test_sayfalar_acilir(self):
        ilk_tur = self.vt().execute("SELECT MIN(id) FROM teklifler WHERE konu_id = ?", (self.konu_no("final projesi hangi"),)).fetchone()[0]
        adresler = ["/", "/konular", "/konular?filtre=OYLAMA", "/kesfet", "/kategoriler", "/kategoriler?suz=alt&sirala=ad",
                    "/kategoriler?q=iklim", "/kategoriler?suz=topluluk&sirala=yeni", "/gundem", "/kararlar", "/yonetmelik",
                    "/defter", "/defter?denetle=1", "/graf", "/ara?q=menu", "/gunluk", "/hakkinda", "/api-belgeleri", "/sw.js",
                    f"/oylama/{ilk_tur}", f"/oylama/{self.tur_no('Yemekhane')}", "/kullanici/kaan.hoca", "/kullanici/Bilge",
                    "/api/v1/gundem", "/api/v1/kategoriler"]
        adresler += [f"/konu/{r[0]}" for r in self.vt().execute("SELECT id FROM konular")]
        adresler += [f"/oylama/{r[0]}" for r in self.vt().execute("SELECT id FROM teklifler")]
        for adres in adresler:
            self.assertEqual(self.istemci.get(adres).status_code, 200, adres)
        self.assertEqual(self.giris("yonetici").status_code, 302)
        for adres in adresler + ["/profil", "/bildirimler", "/konu/yeni", f"/konu/yeni?itiraz={self.konu_no('hangi dille')}", "/yonetim"]:
            self.assertEqual(self.istemci.get(adres).status_code, 200, adres)

    def test_demo_senaryosu(self):
        db = self.vt()
        durum = lambda parca: tuple(db.execute("SELECT durum, tur FROM konular WHERE baslik LIKE ?",  # noqa: E731
                                               (f"%{parca}%",)).fetchone())
        self.assertEqual(durum("hangi dille"), ("KARARA_BAGLANDI", 5))      # beş turun hepsi
        self.assertEqual(durum("Kulüp toplantıları"), ("KARARA_BAGLANDI", 1))  # ilk turda ezici üstünlük
        self.assertEqual(durum("okuma salonu"), ("KARARA_BAGLANDI", 2))     # 2. turda ezici üstünlük
        self.assertEqual(durum("Yemekhanede"), ("OYLAMA", 2))
        self.assertEqual(durum("Final sınavları")[0], "SONUCSUZ")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM teklifler WHERE durum = 'ACIK' AND bitis <= ?",
                                    (zaman.simdi_metin(),)).fetchone()[0], 0)  # hiçbir süre geçmişte kalmadı
        self.assertIn("Karara katılmıyor musun?", self.metin(f"/konu/{self.konu_no('hangi dille')}"))
        self.assertIn("itiraz olarak açıldı", self.metin(f"/konu/{self.konu_no('ek puan')}"))
        self.assertIn("2. tur oylaması sürüyor", self.metin(f"/konu/{self.konu_no('Yemekhanede')}"))
        self.assertIn("Python (Flask)", self.metin("/kararlar"))
        tiyatro = db.execute("SELECT * FROM kategoriler WHERE ad = 'Tiyatro'").fetchone()
        self.assertEqual(tiyatro["kaynak"], "TOPLULUK")                   # oylamayla eklenmiş kategori
        self.assertIsNone(db.execute("SELECT 1 FROM kategoriler WHERE ad = 'Magazin'").fetchone())

    def test_konular_sayfasinda_gundem(self):
        sayfa = self.metin("/konular")
        for parca in ("Şu an gündemde", "Trend konular", "Öne çıkan kelimeler", "Kategorilerin nabzı", "Gündemde",
                      "Mahallelere gençlik meclisi kurulsun", 'class="vitrin"', "Tüm kategoriler"):
            self.assertIn(parca, sayfa)
        kesfet = self.metin("/kesfet")
        for parca in ("Son 24 saatte mesaj", "Haftanın en etkin üyeleri", "Canlı akış", "Son kararlar"):
            self.assertIn(parca, kesfet)
        veri = self.istemci.get("/api/v1/gundem").get_json()
        self.assertEqual(veri["trend"][0]["baslik"], "Mahallelere gençlik meclisi kurulsun")
        self.assertEqual(len(veri["nabiz"]), 8)                              # 7 temel alan + Genel
        self.assertTrue(veri["kelimeler"])

    def test_kategoriler_sayfasi_arama_suzme_siralama(self):
        tum = self.metin("/kategoriler")
        for ad in ("Bilim", "Sağlık", "Siyaset", "Eğitim", "Teknoloji", "Ekonomi", "Kültür ve Sanat", "Genel"):
            self.assertIn(f"{ad}</a>", tum)
        self.assertIn("Spor ve Oyun", tum)                                   # oylamadaki öneri
        ara = self.metin("/kategoriler?q=iklim")
        self.assertIn("Çevre ve İklim", ara)
        self.assertNotIn("Kişisel Finans", ara)
        self.assertIn("Tiyatro", self.metin("/kategoriler?suz=topluluk"))
        self.assertNotIn("Fizik</a>", self.metin("/kategoriler?suz=topluluk"))
        ada_gore = [k["ad"] for k in self.istemci.get("/api/v1/kategoriler?sirala=ad&suz=ana").get_json()["kategoriler"]]
        self.assertEqual(ada_gore[:3], ["Bilim", "Eğitim", "Ekonomi"])
        populer = self.istemci.get("/api/v1/kategoriler?suz=ana").get_json()["kategoriler"]
        self.assertEqual(populer[0]["ad"], "Siyaset")

    def test_kategori_onerisi_web(self):
        self.giris("ece")
        y = self.istemci.post("/kategori/oner", data={"ad": "Gezi", "ust_id": "", "kavramlar": "gezi, tatil, kamp",
                                                      "gerekce": "Öğrenci gezileri ve kamp planları için bir yer olsun.",
                                                      "csrf": self._csrf()})
        self.assertEqual(y.status_code, 302)
        self.assertIn("/oylama/", y.headers["Location"])
        self.assertIn("Önerilen kategori", self.metin(y.headers["Location"]))
        self.assertIn("Gezi", self.metin("/kategoriler"))

    def test_giris_katmani(self):
        ziyaretci = self.metin("/")
        self.assertIn('class="acilis"', ziyaretci)            # ziyaretçi önce tanıtım sayfasını görür
        self.assertIn("Önce göz at", ziyaretci)
        self.assertIn('class="giris-kabugu"', self.metin("/giris"))
        self.giris("ayse")
        uye = self.metin("/")
        self.assertNotIn('class="acilis"', uye)                # üye doğrudan konu akışına düşer
        self.assertIn('class="cipler"', uye)

    def test_csrf_olmadan_post_reddedilir(self):
        self.giris("ayse")
        yanit = self.istemci.post(f"/konu/{self.konu_no('Yemekhanede')}/mesaj", data={"tip": "SORU", "icerik": "Deneme?"})
        self.assertEqual(yanit.status_code, 400)

    def test_gozlemci_uyarisi(self):
        self.giris("zeynep")
        self.assertIn("gözlemcisin", self.metin(f"/konu/{self.konu_no('gece hatlarında')}"))

    def test_fikir_formu_ve_tek_fikir(self):
        self.giris("selin")
        k = self.konu_no("enerji içeceği")
        self.assertIn("Fikrimi ekle", self.metin(f"/konu/{k}"))
        y = self.istemci.post(f"/konu/{k}/fikir", data={"icerik": "Satış serbest kalsın, günde bir kutu sınırı olsun.",
                                                       "csrf": self._csrf()})
        self.assertEqual(y.status_code, 302)
        sayfa = self.metin(f"/konu/{k}")
        self.assertNotIn("Fikrimi ekle", sayfa)                # ikinci fikir yazılamaz
        self.assertIn("günde bir kutu sınırı", sayfa)
        self.assertNotIn("Fikrimi ekle", self.metin(f"/konu/{self.konu_no('Yemekhanede')}"))   # 2. turda fikir yazılamaz
        self.assertNotIn("faydalı", sayfa.lower())             # faydalı işareti kaldırıldı

    def test_mesaj_duzenlenince_gecmisi_gorunur(self):
        self.giris("kaan.hoca")
        k = self.konu_no("Yemekhanede")
        m = self.vt().execute("SELECT id FROM mesajlar WHERE konu_id = ? AND tip = 'SORU'", (k,)).fetchone()["id"]
        y = self.istemci.post(f"/mesaj/{m}/duzenle", data={"icerik": "İki ana yemeğin bütçeye maliyeti hesaplandı mı?",
                                                          "csrf": self._csrf()})
        self.assertEqual(y.status_code, 302)
        self.assertIn(f"/mesaj/{m}/gecmis", self.metin(f"/konu/{k}"))
        self.assertIn("Her gün iki ana yemek çıkarmanın", self.metin(f"/mesaj/{m}/gecmis"))   # eski hâli

    def test_guvenlik_basliklari(self):
        yanit = self.istemci.get("/")
        self.assertIn("default-src 'self'", yanit.headers["Content-Security-Policy"])
        self.assertEqual(yanit.headers["X-Frame-Options"], "DENY")

    def test_api_ile_giris_ve_oy(self):
        y = self.istemci.post("/api/v1/giris", json={"takma_ad": "mert", "sifre": "forum1234", "cihaz": "Test"})
        self.assertEqual(y.status_code, 201)
        basliklar = {"Authorization": f"Bearer {y.get_json()['anahtar']}"}
        self.assertEqual(self.istemci.get("/api/v1/ben", headers=basliklar).get_json()["yurttas"]["takma_ad"], "mert")
        oylamalar = self.istemci.get("/api/v1/oylamalar", headers=basliklar).get_json()["oylamalar"]
        hedef = next(o for o in oylamalar if o["tip"] == "KARAR" and o["benim"]["verebilir"] and not o["benim"]["oy_verdim"])
        self.assertEqual(hedef["secenekler"][-1]["id"], "CEKIMSER")
        y = self.istemci.post(f"/api/v1/oylamalar/{hedef['id']}/oy", headers=basliklar,
                              json={"secim": hedef["secenekler"][0]["id"]})
        self.assertEqual(y.status_code, 201, y.get_json())
        self.assertIn("makbuz", y.get_json())
        k = self.konu_no("ring servisleri")
        y = self.istemci.post(f"/api/v1/konular/{k}/fikir", headers=basliklar, json={"icerik": "Ring servisleri gece yarısına kadar çalışsın."})
        self.assertEqual(y.status_code, 201, y.get_json())
        self.assertEqual(self.istemci.post(f"/api/v1/konular/{k}/fikir", headers=basliklar,
                                           json={"icerik": "İkinci bir fikir daha yazıyorum."}).status_code, 422)
        self.assertEqual(len(self.istemci.get(f"/api/v1/konular/{k}").get_json()["fikirler"]), 1)
        self.assertEqual(self.istemci.get("/api/v1/ben", headers={"Authorization": "Bearer yanlis"}).status_code, 401)

    def test_api_kisisel_veri_dondurmez(self):
        metin = self.metin(f"/api/v1/konular/{self.konu_no('Yemekhanede')}")
        for gizli in ("ad_soyad", "dogum_tarihi", "Ayşe Yılmaz"):
            self.assertNotIn(gizli, metin)

    def test_yonetim_paneli(self):
        self.giris("ayse")
        self.assertEqual(self.istemci.get("/yonetim").status_code, 403)      # üye paneli göremez
        self.assertEqual(self.istemci.get("/yonetim/uyeler").status_code, 403)
        self.istemci = self.app.test_client()
        self.giris("yonetici")
        for adres in ["/yonetim", "/yonetim/uyeler", "/yonetim/uyeler?filtre=uzman&q=a", "/yonetim/uye/2",
                      "/yonetim/konular", "/yonetim/konular?durum=TARTISMA", "/yonetim/konular?durum=SONUCSUZ",
                      "/yonetim/oylamalar", "/yonetim/kategoriler", "/yonetim/sistem", "/yonetim/sistem?denetle=1",
                      "/yonetim/gunluk", "/yonetim/gunluk?eylem=YONETIM"]:
            self.assertEqual(self.istemci.get(adres).status_code, 200, adres)
        yedek = self.istemci.get("/yonetim/yedek")
        self.assertTrue(yedek.data.startswith(b"SQLite format 3"))

    def test_yonetici_kararlari_etkileyemez(self):
        self.giris("yonetici")
        db = self.vt()
        tur = self.tur_no("Yemekhanede")
        ring = self.konu_no("ring servisleri")
        for adres in (f"/konu/{self.konu_no('gece hatlarında')}", f"/oylama/{tur}", "/yonetim/konular", "/yonetim/oylamalar",
                      "/yonetim/uye/2", "/yonetim"):
            sayfa = self.metin(adres)
            for iz in ("Süreyi ilerlet", "Sonuçlandır", "Uzman ata", "sona erdir"):
                self.assertNotIn(iz, sayfa, adres)
        self.assertNotIn("Bozmayı dene", self.metin("/defter"))
        self.assertIn("Yönetim paneli", self.metin("/profil"))
        csrf = self._csrf()
        self.assertEqual(self.istemci.post("/yonetim/uzmanlik", data={"kullanici_id": 2, "kategori_id": 1, "csrf": csrf}).status_code, 404)
        self.assertEqual(self.istemci.post(f"/yonetim/oylama/{tur}/sonuclandir", data={"csrf": csrf}).status_code, 404)
        self.istemci.post(f"/yonetim/konu/{ring}/ilerlet", data={"csrf": csrf})            # sunum kipi kapalı: işlemez
        self.istemci.post(f"/yonetim/oylama/{tur}/ilerlet", data={"csrf": csrf})
        self.assertEqual(db.execute("SELECT durum FROM konular WHERE id = ?", (ring,)).fetchone()[0], "TARTISMA")
        self.assertEqual(db.execute("SELECT durum FROM teklifler WHERE id = ?", (tur,)).fetchone()[0], "ACIK")

    def test_sunum_kipinde_sure_ilerletilir(self):
        self.giris("yonetici")
        db = self.vt()
        k = self.konu_no("gözlem gecesi")
        self.app.config["DEMO"] = True
        try:
            self.assertIn("Süreyi ilerlet", self.metin("/yonetim/konular"))
            self.istemci.post(f"/yonetim/konu/{k}/ilerlet", data={"csrf": self._csrf()})
        finally:
            self.app.config["DEMO"] = False
        self.assertEqual(db.execute("SELECT durum FROM konular WHERE id = ?", (k,)).fetchone()[0], "OYLAMA")
        self.assertTrue(db.execute("SELECT 1 FROM gunluk WHERE eylem = 'SURE' AND detay LIKE 'Sunum kipi%'").fetchone())

    def test_panel_sayfalari(self):
        self.giris("ayse")
        for adres in ["/profil", "/profil/hesap", "/profil/oy-devri", "/profil/uzmanlik", "/profil/guvenlik",
                      "/profil/uygulama", "/bildirimler"]:
            self.assertEqual(self.istemci.get(adres).status_code, 200, adres)
        self.assertNotIn("Yönetim paneli", self.metin("/profil"))
        self.assertIn("Kontenjan", self.metin("/profil/uzmanlik"))

    def test_askidaki_uye_yazamaz(self):
        self.giris("yonetici")
        db = self.vt()
        can_id = db.execute("SELECT id FROM kullanicilar WHERE takma_ad = 'can'").fetchone()[0]
        once = db.execute("SELECT COUNT(*) FROM mesajlar").fetchone()[0]
        y = self.istemci.post(f"/yonetim/uye/{can_id}/aski", data={"gun": "3", "neden": "Deneme amaçlı askıya alma",
                                                                   "csrf": self._csrf()})
        self.assertEqual(y.status_code, 302)
        self.istemci = self.app.test_client()
        self.giris("can")
        self.istemci.post(f"/konu/{self.konu_no('Yemekhanede')}/mesaj",
                          data={"tip": "SORU", "icerik": "Askıdayken yazılabilir mi?", "csrf": self._csrf()})
        self.assertEqual(db.execute("SELECT COUNT(*) FROM mesajlar").fetchone()[0], once)
        self.assertIn("askıda", self.metin("/konular"))
        self.istemci = self.app.test_client()
        self.giris("yonetici")
        self.istemci.post(f"/yonetim/uye/{can_id}/aski-kaldir", data={"csrf": self._csrf()})
        self.assertIsNone(db.execute("SELECT askida_bitis FROM kullanicilar WHERE id = ?", (can_id,)).fetchone()[0])

    def test_sikayetler_ve_anlik(self):
        self.giris("yonetici")
        for adres in ["/yonetim/sikayetler", "/yonetim/sikayetler?durum=kapali", "/yonetim/bildirim", "/static/tema.js"]:
            self.assertEqual(self.istemci.get(adres).status_code, 200, adres)
        self.assertIn("satılık bisikletim", self.metin("/yonetim/sikayetler"))       # 3 kişi şikayet etti: taban doldu
        self.assertIn("Şikayet et", self.metin(f"/konu/{self.konu_no('Yemekhanede')}"))
        self.assertIn('data-tema-sec="koyu"', self.metin("/konular"))
        self.assertIn("fcm", self.istemci.get("/api/v1/anlik").get_json())
        y = self.istemci.post("/yonetim/bildirim", data={"hedef": "YONETICI", "metin": "Deneme bildirimi", "csrf": self._csrf()})
        self.assertEqual(y.status_code, 302)

    def test_eski_akistan_iz_yok(self):
        for adres in ["/hakkinda", "/yonetmelik", "/", f"/konu/{self.konu_no('hangi dille')}",
                      f"/konu/{self.konu_no('Yemekhanede')}", "/gundem", "/giris", "/kesfet", "/kategoriler"]:
            metin = self.metin(adres).lower()
            for iz in ("abd", "kongre", "senato", "komisyon", "genel kurul", "bilirkişi", "şerh", "erteleme"):
                self.assertNotIn(iz, metin, f"{adres}: {iz}")


class Kategoriler(Ortam):
    GEREKCE = "Bu alandaki konular başka kategorilerde kayboluyor; ayrı bir yer gerekiyor."

    def test_yedi_temel_alan_ve_genel(self):
        koklar = [r[0] for r in self.db.execute("SELECT ad FROM kategoriler WHERE ust_id IS NULL")]
        self.assertEqual(sorted(koklar), sorted(["Bilim", "Sağlık", "Siyaset", "Eğitim", "Teknoloji", "Ekonomi",
                                                 "Kültür ve Sanat", "Genel"]))
        self.assertEqual(ontoloji.kategori_listesi(self.db)[-1][1], "Genel")         # Genel listenin sonunda

    def test_genel_kategoride_kategori_denetimi_aranmaz(self):
        rapor = yonetmelik.denetle(self.db, "Forumda haftalık soru cevap saati olsun",
                                   "Her pazar akşamı bir saat boyunca sorular yanıtlansın, yeni gelenler forumu tanısın.",
                                   self.kategori("Genel"))
        self.assertNotIn("D3", {b["kod"] for b in rapor["uyarilar"]})
        self.assertIsNone(rapor["onerilen_kategori"])

    def test_oneri_kabul_edilince_kategori_eklenir_ve_kavramlari_kullanilir(self):
        kisiler = self.kisiler(4)
        t = kategoriler.oner(self.db, kisiler[0], "Spor ve Oyun", None, "turnuva, espor, Satranç", self.GEREKCE)
        self.assertEqual(oylama.teklif_getir(self.db, t)["esik"], "SALT")
        self.assertEqual(oylama.teklif_basligi(self.db, oylama.teklif_getir(self.db, t)), "Yeni kategori: Spor ve Oyun")
        for kim, secim in zip(kisiler, ("EVET", "EVET", "EVET", "HAYIR")):
            oylama.oy_ver(self.db, t, kim, secim)                     # herkes oy verince biter
        k = self.db.execute("SELECT * FROM kategoriler WHERE ad = 'Spor ve Oyun' AND ust_id IS NULL").fetchone()
        self.assertEqual((k["kaynak"], k["kavramlar"]), ("TOPLULUK", "turnuva,espor,satranc"))
        rapor = yonetmelik.denetle(self.db, "Bahar turnuvası düzenlensin",
                                   "Kampüste satranç ve espor turnuvası düzenleyelim, ödüller de olsun.", k["id"])
        self.assertNotIn("D3", {b["kod"] for b in rapor["uyarilar"]})
        self.konu(kisiler[1], baslik="Bahar satranç turnuvası", kategori_id=k["id"],
                  aciklama="Kampüste satranç turnuvası düzenleyelim, herkes katılabilsin ve ödül verilsin.")

    def test_alt_kategori_onerisi_ve_ret(self):
        kisiler = self.kisiler(3)
        t = kategoriler.oner(self.db, kisiler[0], "Tiyatro", self.kategori("Kültür ve Sanat"), "", self.GEREKCE)
        self.assertEqual(oylama.teklif_basligi(self.db, oylama.teklif_getir(self.db, t)), "Yeni kategori: Kültür ve Sanat › Tiyatro")
        for kim in kisiler:
            oylama.oy_ver(self.db, t, kim, "HAYIR")
        self.assertIsNone(self.db.execute("SELECT 1 FROM kategoriler WHERE ad = 'Tiyatro'").fetchone())
        self.assertEqual(oylama.teklif_getir(self.db, t)["durum"], "RET")

    def test_oneri_kurallari(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        with self.assertRaises(KuralHatasi):                          # aynı adda kategori var
            kategoriler.oner(self.db, a, "bilim", None, "", self.GEREKCE)
        with self.assertRaises(KuralHatasi):                          # alt kategori yalnızca ana kategorinin altına
            kategoriler.oner(self.db, a, "Kuantum", self.kategori("Bilim", "Fizik"), "", self.GEREKCE)
        with self.assertRaises(KuralHatasi):                          # Genel'in alt kategorisi olmaz
            kategoriler.oner(self.db, a, "Sohbet", self.kategori("Genel"), "", self.GEREKCE)
        with self.assertRaises(KuralHatasi):                          # gerekçe zorunlu
            kategoriler.oner(self.db, a, "Gezi", None, "", "kısa")
        with self.assertRaises(KuralHatasi):                          # yapay zeka öneremez
            kategoriler.oner(self.db, self.yz(), "Gezi", None, "", self.GEREKCE)
        kategoriler.oner(self.db, a, "Gezi", None, "", self.GEREKCE)
        with self.assertRaises(KuralHatasi):                          # aynı öneri ikinci kez oylamaya çıkmaz
            kategoriler.oner(self.db, b, "gezi", None, "", self.GEREKCE)
        with self.assertRaises(KuralHatasi):                          # kişi başı bir bekleyen öneri
            kategoriler.oner(self.db, a, "Fotoğraf", None, "", self.GEREKCE)

    def test_liste_arama_suzme_siralama(self):
        a = self.kisi("ali")
        self.konu(a, kategori_id=self.kategori("Ekonomi", "Kişisel Finans"), baslik="Burslar güncellensin",
                  aciklama="Burs miktarı enflasyon karşısında eriyor, her dönem güncellenmesi gerekiyor.")
        liste = kategoriler.liste(self.db, "populer", "", "ana")
        self.assertEqual(liste[0]["ad"], "Ekonomi")
        self.assertEqual((liste[0]["konu"], liste[0]["acik"]), (1, 1))
        self.assertEqual([s["yol"] for s in kategoriler.liste(self.db, "ad", "burs", "")], ["Ekonomi › Kişisel Finans"])
        self.assertTrue(all(s["ust_id"] for s in kategoriler.liste(self.db, "ad", "", "alt")))
        self.assertEqual([s["ad"] for s in kategoriler.liste(self.db, "populer", "", "dolu")], ["Ekonomi", "Kişisel Finans"])

    def test_eski_kategori_agaci_tasinir(self):
        a = self.kisi("ali")
        sehir = self.db.execute("INSERT INTO kategoriler (ad, ust_id) VALUES ('Şehir', NULL)").lastrowid
        ulasim = self.db.execute("INSERT INTO kategoriler (ad, ust_id) VALUES ('Ulaşım', ?)", (sehir,)).lastrowid
        ozel = self.db.execute("INSERT INTO kategoriler (ad, ust_id) VALUES ('Bisiklet Yolları', ?)", (sehir,)).lastrowid
        kampus = self.db.execute("INSERT INTO kategoriler (ad, ust_id) VALUES ('Kampüs Yaşamı', NULL)").lastrowid
        kulup = self.db.execute("INSERT INTO kategoriler (ad, ust_id) VALUES ('Kulüpler', ?)", (kampus,)).lastrowid
        self.db.onbellek.clear()
        k1 = self.konu(a, kategori_id=ulasim, baslik="Gece otobüsleri", aciklama="Gece otobüs seferleri artırılsın, durakta beklemek zor.")
        k2 = self.konu(a, kategori_id=kulup, baslik="Kulüp günleri", aciklama="Kulüp toplantıları için ortak bir gün belirlensin.")
        uzmanlik.uzmanlik_ver(self.db, a["id"], ulasim)
        self.db.execute("UPDATE site_ayarlari SET deger = '1' WHERE anahtar = 'kategori_surumu'")
        ontoloji.yukle(self.db)                                       # sunucu yeni sürümle açılıyor
        yol = lambda k: ontoloji.yol_metni(self.db, "kategoriler", konular.konu_getir(self.db, k)["kategori_id"])  # noqa: E731
        self.assertEqual(yol(k1), "Siyaset › Ulaşım")
        self.assertEqual(yol(k2), "Eğitim › Kampüs Yaşamı")
        self.assertEqual(ontoloji.yol_metni(self.db, "kategoriler", ozel), "Siyaset › Bisiklet Yolları")   # silinmedi, taşındı
        self.assertIsNone(self.db.execute("SELECT 1 FROM kategoriler WHERE ad IN ('Şehir') OR (ad = 'Kampüs Yaşamı' "
                                          "AND ust_id IS NULL)").fetchone())
        self.assertEqual(ontoloji.yol_metni(self.db, "kategoriler", uzmanlik.uzmanliklar(self.db, a["id"])[0]["kategori_id"]),
                         "Siyaset › Ulaşım")


class Gundem(Ortam):
    def test_trend_kelimeler_ve_nabiz(self):
        a, b, c = self.kisiler(3)
        sakin = self.konu(a, baslik="Kütüphane saatleri uzasın", kategori_id=self.kategori("Eğitim", "Üniversite"),
                          aciklama="Kütüphane sınav haftalarında gece yarısına kadar açık kalsın, öğrenciler çalışabilsin.")
        self.ileri_sar(hours=30)
        canli = self.konu(b, baslik="Kampüste plastik bardak kalksın", kategori_id=self.kategori("Bilim", "Çevre ve İklim"),
                          aciklama="Plastik bardak yerine kupa kullanılsın, plastik atık azalsın, kampüs temiz kalsın.")
        for kim, metin in ((a, "Plastik kupa yerine cam kupa daha iyi."), (c, "Plastik atık gerçekten çok fazla."),
                           (b, "Kupa getirene indirim yapılabilir.")):
            konular.mesaj_yaz(self.db, kim, canli, "ARGUMAN", metin)
        trend, saat = gundem.trend_konular(self.db)
        self.assertEqual(trend[0]["id"], canli)
        self.assertEqual((trend[0]["mesaj"], trend[0]["kisi"]), (3, 3))
        self.assertNotIn(sakin, [t["id"] for t in trend[:1]])
        kelimeler = {k["kelime"] for k in gundem.anahtar_kelimeler(self.db)}
        self.assertIn("plastik", kelimeler)
        self.assertNotIn("yerine", kelimeler)                         # sık kelimeler sayılmaz
        nabiz = {n["ad"]: n for n in gundem.kategori_nabzi(self.db)}
        self.assertEqual(nabiz["Bilim"]["bu"], 3)
        self.assertEqual(gundem.kategori_nabzi(self.db)[0]["ad"], "Bilim")
        self.assertEqual(gundem.son_24_saat(self.db)["mesaj"], 3)
        self.assertEqual([y["tur"] for y in gundem.yakinda_bitenler(self.db)], ["TARTISMA", "TARTISMA"])


class Yonetim(Ortam):
    def setUp(self):
        super().setUp()
        self.yonetici = self.kisi("yonetici")
        self.db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE id = ?", (self.yonetici["id"],))
        self.yonetici = kullanicilar.getir(self.db, self.yonetici["id"])

    def test_yetki_verme(self):
        ali = self.kisi("ali")
        yonetim.yetki_ver(self.db, self.yonetici, ali["id"], True)
        self.assertEqual(kullanicilar.getir(self.db, ali["id"])["yonetici_mi"], 1)
        with self.assertRaises(KuralHatasi):          # kendi yetkisini değiştiremez
            yonetim.yetki_ver(self.db, self.yonetici, self.yonetici["id"], False)
        with self.assertRaises(KuralHatasi):          # yapay zeka yönetici olamaz
            yonetim.yetki_ver(self.db, self.yonetici, self.yz()["id"], True)
        yonetim.yetki_ver(self.db, kullanicilar.getir(self.db, ali["id"]), self.yonetici["id"], False)
        self.assertEqual(kullanicilar.getir(self.db, self.yonetici["id"])["yonetici_mi"], 0)

    def test_yoneticinin_oyu_da_bir_sayilir(self):
        ali = self.kisi("ali")
        k, (fa,) = self.fikirli_konu([ali])
        self.assertEqual(oylama.oy_durumu(self.db, self.tur(k), self.yonetici)["agirlik"], 1)

    def test_askiya_alma(self):
        ali = self.kisi("ali")
        with self.assertRaises(KuralHatasi):          # neden zorunlu
            yonetim.askiya_al(self.db, self.yonetici, ali["id"], 3, "kısa")
        yonetim.askiya_al(self.db, self.yonetici, ali["id"], 3, "Tekrarlanan kişisel saldırı")
        self.assertTrue(yonetim.askida_mi(kullanicilar.getir(self.db, ali["id"])))
        self.assertTrue(any("askıya alındı" in g["detay"] for g in gunluk.son_kayitlar(self.db)))
        zaman.simdi = lambda: self._gercek_simdi() + timedelta(days=4)   # süre dolunca kendiliğinden biter
        self.assertFalse(yonetim.askida_mi(kullanicilar.getir(self.db, ali["id"])))
        zaman.simdi = self._gercek_simdi
        with self.assertRaises(KuralHatasi):          # yönetici önce yetkisi alınmadan askıya alınamaz
            yonetim.yetki_ver(self.db, self.yonetici, ali["id"], True) or \
                yonetim.askiya_al(self.db, self.yonetici, ali["id"], 3, "Yönetici askıya alınamaz")

    def test_yeni_uyelik_kapatilabilir(self):
        yonetim.site_ayari_yaz(self.db, self.yonetici, "kayit_acik", "0")
        with self.assertRaises(KuralHatasi):
            self.kisi("yeni")
        yonetim.site_ayari_yaz(self.db, self.yonetici, "kayit_acik", "1")
        self.kisi("yeni")

    def test_kategori_ekleme_ve_renk(self):
        kok = yonetim.kategori_ekle(self.db, self.yonetici, "Spor", renk=ayarlar.YESIL[400])
        alt = yonetim.kategori_ekle(self.db, self.yonetici, "Futbol", kok)
        self.assertEqual(ontoloji.kategori_rengi(self.db, alt), ayarlar.YESIL[400])
        self.assertEqual(ontoloji.yol_metni(self.db, "kategoriler", alt), "Spor › Futbol")
        with self.assertRaises(KuralHatasi):
            yonetim.kategori_ekle(self.db, self.yonetici, "spor")
        with self.assertRaises(KuralHatasi):          # renk paletten olmalı
            yonetim.kategori_ekle(self.db, self.yonetici, "Oyun", renk="#ff0000")

    def test_pano_ve_yedek(self):
        self.konu(self.kisi("ali"))
        p = yonetim.pano(self.db)
        self.assertEqual((p["sayilar"]["acik_konu"], p["sayilar"]["tartisma"], p["sayilar"]["uzman"]), (1, 1, 0))
        self.assertTrue(yonetim.yedek_al(self.db).startswith(b"SQLite format 3"))


class SikayetVeBildirim(Ortam):
    def setUp(self):
        super().setUp()
        self.yonetici = self.kisi("yonetici", il="Ankara", ilce=None)   # İstanbul konusunda gözlemci
        self.db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE id = ?", (self.yonetici["id"],))
        self.yonetici = kullanicilar.getir(self.db, self.yonetici["id"])
        self.a, self.b, self.c, self.d = self.kisi("ali"), self.kisi("banu"), self.kisi("cem"), self.kisi("derya")
        self.k = self.konu(self.a, konum_id=self.konum("İstanbul"))
        self.m = konular.mesaj_yaz(self.db, self.b, self.k, "ARGUMAN", "Satılık bisikletim var, isteyen bana yazsın.")

    def bildirim_sayisi(self, kullanici):
        return self.db.execute("SELECT COUNT(*) FROM bildirimler WHERE kullanici_id = ?", (kullanici["id"],)).fetchone()[0]

    def test_taban_dolmadan_yoneticiye_gitmez(self):
        once = self.bildirim_sayisi(self.yonetici)
        s1, kalan = sikayetler.sikayet_et(self.db, self.a, "MESAJ", self.m, "Konu dışı", "Reklam")
        self.assertEqual(kalan, 2)
        sikayetler.sikayet_et(self.db, self.c, "MESAJ", self.m, "Spam")
        self.assertEqual(self.bildirim_sayisi(self.yonetici), once)          # iki kişi yetmez
        self.assertEqual((sikayetler.acik_sayisi(self.db), sikayetler.liste(self.db)), (0, []))
        with self.assertRaises(KuralHatasi):                                  # yönetici de işleme alamaz
            sikayetler.oylamaya_al(self.db, self.yonetici, s1)
        with self.assertRaises(KuralHatasi):                                  # aynı kişi ikinci kez şikayet edemez
            sikayetler.sikayet_et(self.db, self.a, "MESAJ", self.m, "Spam")
        with self.assertRaises(KuralHatasi):                                  # kendi mesajını şikayet edemez
            sikayetler.sikayet_et(self.db, self.b, "MESAJ", self.m, "Spam")
        _, kalan = sikayetler.sikayet_et(self.db, self.d, "MESAJ", self.m, "Spam")
        self.assertEqual(kalan, 0)
        self.assertEqual(self.bildirim_sayisi(self.yonetici), once + 1)      # üçüncü kişiyle taban doldu
        self.assertEqual(sikayetler.acik_sayisi(self.db), 1)                 # aynı mesaj bir sayılır
        # yönetici gözlemci olduğu konuda da şikayeti oylamaya alabilir; karar yine oylamayla verilir
        t = sikayetler.oylamaya_al(self.db, self.yonetici, s1)
        self.assertEqual(oylama.teklif_getir(self.db, t)["tip"], "MESAJ_SILME")
        self.assertEqual(sikayetler.acik_sayisi(self.db), 0)
        self.assertEqual(konular.mesaj_getir(self.db, self.m)["gizli"], 0)    # yönetici kendisi gizlemez
        with self.assertRaises(KuralHatasi):                                  # sonuçlanan şikayet tekrar işlenmez
            sikayetler.oylamaya_al(self.db, self.yonetici, s1)

    def test_yersiz_sikayet_kapanir(self):
        yonetmelik.degisikligi_uygula(self.db, {"tur": "PARAMETRE", "kod": "SIKAYET_TABANI", "yeni": "1"})
        s, _ = sikayetler.sikayet_et(self.db, self.c, "KONU", self.k, "Diğer")
        with self.assertRaises(KuralHatasi):
            sikayetler.yersiz_bul(self.db, self.yonetici, s, "")
        sikayetler.yersiz_bul(self.db, self.yonetici, s, "Konu kurallara uygun.")
        self.assertEqual(self.db.execute("SELECT durum FROM sikayetler WHERE id = ?", (s,)).fetchone()[0], "YERSIZ")
        self.assertIn("yersiz", self.db.execute("SELECT metin FROM bildirimler WHERE kullanici_id = ? ORDER BY id DESC",
                                                (self.c["id"],)).fetchone()[0])

    def test_toplu_bildirim(self):
        uzak = self.kisi("uzak", il="İzmir", ilce=None)
        once = self.bildirim_sayisi(uzak)
        sayi = yonetim.toplu_bildirim(self.db, self.yonetici, "KONUM", "İstanbul toplantısı cuma günü.", "/konular",
                                      konum_id=self.konum("İstanbul"))
        self.assertEqual(sayi, 4)                                             # ali, banu, cem, derya (Kadıköy)
        self.assertEqual(self.bildirim_sayisi(uzak), once)
        self.assertEqual(yonetim.toplu_bildirim(self.db, self.yonetici, "HEPSI", "Bakım duyurusu."), 6)
        self.uzman_yap(self.a, "Sağlık")
        self.assertEqual(yonetim.toplu_bildirim(self.db, self.yonetici, "UZMAN", "Uzmanlara duyuru.",
                                                kategori_id=self.kategori("Sağlık")), 1)
        with self.assertRaises(KuralHatasi):                                  # dış bağlantı olmaz
            yonetim.toplu_bildirim(self.db, self.yonetici, "HEPSI", "Tıkla kazan", "https://ornek.com")

    def test_anlik_bildirim_islem_kaydedilince_gider(self):
        gonderilen = []
        gercek = anlik._gonder
        anlik._gonder = lambda yol, isler: gonderilen.extend(isler)
        try:
            anlik.abone_ol(self.db, self.a, "WEB", {"endpoint": "https://push.ornek/abc",
                                                    "keys": {"p256dh": "x" * 20, "auth": "y" * 10}})
            self.db.commit()
            konular.mesaj_yaz(self.db, self.c, self.k, "SORU", "Ali bu konuyu neden açtın?", self.m)
            yonetim.toplu_bildirim(self.db, self.yonetici, "HEPSI", "Bakım duyurusu.")
            self.db.rollback()                                                  # geri alınan işlem gönderilmez
            self.assertEqual(gonderilen, [])
            yonetim.toplu_bildirim(self.db, self.yonetici, "HEPSI", "Bakım duyurusu.")
            self.db.commit()
            self.assertEqual(len(gonderilen), 1)
            self.assertIn("Bakım duyurusu.", gonderilen[0][1])
        finally:
            anlik._gonder = gercek
        with self.assertRaises(KuralHatasi):
            anlik.abone_ol(self.db, self.a, "WEB", {"endpoint": "http://guvensiz", "keys": {}})

    def test_gecersiz_abonelik_silinir(self):
        anlik.abone_ol(self.db, self.a, "FCM", {"token": "t" * 40})
        self.db.commit()
        gercek = anlik._fcm_gonder
        anlik._fcm_gonder = lambda db, abonelik, yuk: False                  # uygulama kaldırılmış
        try:
            anlik._gonder(self.yol, [(dict(anlik.abonelikler(self.db, self.a["id"])[0]), "{}")])
        finally:
            anlik._fcm_gonder = gercek
        self.assertEqual(anlik.abonelikler(self.db, self.a["id"]), [])


if __name__ == "__main__":
    unittest.main()
