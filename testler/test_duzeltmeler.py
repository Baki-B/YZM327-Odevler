"""Yazılım mühendisliği incelemesinde bulunan hataların düzeltmelerini koruyan testler.

Her test önce hatayı yeniden üretecek biçimde yazıldı (düzeltmeden önce başarısız oluyordu), sonra kod düzeltildi.
"""
import logging
import os
import sys
import threading
import unittest

_KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(_KLASOR), _KLASOR]

from forum import (anlik, ayarlar, defter, devir, gorevler, graf, gundem, guvenlik, kategoriler, konular,  # noqa: E402
                   kullanicilar, oylama, sonuclar, teklif_turleri, uygunluk, yonetim, yonetmelik, yz)
from forum.metin import site_ici_yol_mu  # noqa: E402
from forum.hatalar import KuralHatasi, tamsayi  # noqa: E402
from test_forum import Ortam  # noqa: E402


class GirdiAyristirma(Ortam):
    def test_tamsayi(self):
        self.assertEqual(tamsayi(" 12 "), 12)
        self.assertIsNone(tamsayi(""))
        self.assertIsNone(tamsayi(None))
        for bozuk in ("abc", "1.5", "²", "1e3"):
            with self.assertRaises(KuralHatasi, msg=bozuk):
                tamsayi(bozuk)

    def test_bozuk_sayilar_kural_hatasi_verir(self):
        """Eskiden ValueError → 500 hatası veriyordu."""
        ali, ayse = self.kisi("ali"), self.kisi("ayse")
        k = self.konu(ali)
        with self.assertRaises(KuralHatasi):
            devir.devir_ekle(self.db, ali, "ayse", "KATEGORI", "abc")
        with self.assertRaises(KuralHatasi):
            konular.mesaj_silme_teklifi(self.db, ayse, ["²"], "Spam", "")
        with self.assertRaises(KuralHatasi):
            konular.denetim_onizleme(self.db, {"baslik": "Deneme başlığı", "aciklama": "Yeterince uzun bir açıklama",
                                               "kategori_id": self.kategori("Sağlık")}, "abc")
        devir.devir_ekle(self.db, ali, "ayse", "KONU", str(k))          # formdan gelen dize de kabul edilir
        self.assertEqual(devir.verilen_devirler(self.db, ali["id"])[0]["kapsam_id"], k)


class KategoriKurallari(Ortam):
    def setUp(self):
        super().setUp()
        y = self.kisi("yonetici")
        self.db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE id = ?", (y["id"],))
        self.yonetici = kullanicilar.getir(self.db, y["id"])
        self.genel = self.kategori("Genel")

    def test_yonetici_de_genelin_altina_kategori_ekleyemez(self):
        """Topluluk önerisi bu kuralı uyguluyordu, yönetici yolu uygulamıyordu (kopya kod sapması)."""
        with self.assertRaises(KuralHatasi):
            yonetim.kategori_ekle(self.db, self.yonetici, "Alt Deneme", self.genel)
        with self.assertRaises(KuralHatasi):
            kategoriler.oner(self.db, self.yonetici, "Alt Deneme", self.genel, "a, b", "Gerekçe yeterince uzun olsun.")

    def test_yeniden_adlandirmada_kardes_ad_ve_genel_korunur(self):
        bilim = self.kategori("Bilim")
        with self.assertRaises(KuralHatasi):
            yonetim.kategori_duzenle(self.db, self.yonetici, bilim, "Sağlık")
        with self.assertRaises(KuralHatasi):
            yonetim.kategori_duzenle(self.db, self.yonetici, self.genel, "Diğer")
        yonetim.kategori_duzenle(self.db, self.yonetici, bilim, "Bilim")       # yalnız renk değişimi serbest


class YanEtkiDayanikliligi(Ortam):
    def test_defter_yazilamazsa_commit_hata_vermez(self):
        """Veri kalıcıyken isteğin 500 dönmesi kullanıcıyı işlemi tekrarlamaya iter (çift kayıt)."""
        gercek = defter.dugumlere_yaz
        defter.dugumlere_yaz = lambda klasor, kuyruk: (_ for _ in ()).throw(OSError("disk dolu"))
        try:
            with self.assertLogs("forum.veritabani", logging.ERROR):
                self.kisi("ali")
                self.db.commit()
        finally:
            defter.dugumlere_yaz = gercek
        self.assertIsNotNone(kullanicilar.takma_ad_ile(self.db, "ali"))

    def test_commit_sonrasi_bir_is_digerlerini_durdurmaz(self):
        calisan = []
        self.db.commit_sonrasi.append(lambda: 1 / 0)
        self.db.commit_sonrasi.append(lambda: calisan.append(1))
        with self.assertLogs("forum.veritabani", logging.ERROR):
            self.db.commit()
        self.assertEqual(calisan, [1])

    def test_with_blogu_kendi_commitimizden_gecer(self):
        calisan = []
        with self.db:
            self.db.commit_sonrasi.append(lambda: calisan.append(1))
        self.assertEqual(calisan, [1])

    def test_kayit_noktasi_yalnizca_bloku_geri_alir(self):
        """Memento: kayıt noktasına dönülünce bloğun deftere eklediği bloklar da kuyruktan silinir."""
        self.kisi("ali")
        once = len(self.db.defter_kuyrugu)
        with self.assertRaises(ZeroDivisionError):
            with self.db.kayit_noktasi():
                self.kisi("ayse")
                self.assertGreater(len(self.db.defter_kuyrugu), once)
                1 / 0
        self.assertEqual(len(self.db.defter_kuyrugu), once)
        self.assertIsNone(kullanicilar.takma_ad_ile(self.db, "ayse"))
        self.assertIsNotNone(kullanicilar.takma_ad_ile(self.db, "ali"))     # dış işlem sürüyor
        self.db.commit()
        self.assertIsNotNone(kullanicilar.takma_ad_ile(self.db, "ali"))


class ZamanlayiciYalitimi(Ortam):
    def test_bozuk_bir_is_digerlerini_engellemez(self):
        ali, ayse = self.kisi("ali"), self.kisi("ayse")
        k1, k2 = self.konu(ali), self.konu(ayse, baslik="Kütüphane saatleri uzatılsın")
        self.ileri_sar(hours=25)
        gercek = konular.oylamayi_baslat

        def bozuk(db, konu_id):
            if konu_id == k1:
                raise RuntimeError("beklenmeyen hata")
            return gercek(db, konu_id)
        konular.oylamayi_baslat = bozuk
        try:
            with self.assertLogs("forum.gorevler", logging.ERROR):
                gorevler.tick(self.db)                     # eskiden istisna yayılıyor, her sayfa 500 dönüyordu
        finally:
            konular.oylamayi_baslat = gercek
        self.assertEqual(self.durum(k1), "TARTISMA")
        self.assertEqual(self.durum(k2), "OYLAMA")
        self.db.commit()
        gorevler.tick(self.db)                             # hata giderilince bir sonraki tick'te işlenir
        self.assertEqual(self.durum(k1), "OYLAMA")
        self.assertEqual(len([t for t in oylama.konu_teklifleri(self.db, k1) if t["durum"] == "ACIK"]), 1)


class DefterTurleri(Ortam):
    def test_bilinmeyen_tur_reddedilir_ve_sayfa_hepsini_listeler(self):
        with self.assertRaises(ValueError):
            defter.ekle(self.db, "YAZIM_HATASI", {})
        for tur in ("DEVIR_GERI", "KATEGORI"):
            self.assertIn(tur, defter.BLOK_TURLERI)


class WebOrtam(Ortam):
    """Boş veritabanıyla çalışan Flask uygulaması; giriş, oturuma kullanıcı yazılarak yapılır."""

    def setUp(self):
        super().setUp()
        from forum import create_app
        self.app = create_app({"VERITABANI": self.yol, "TESTING": True})
        self.istemci = self.app.test_client()

    def giris(self, kisi):
        self.db.commit()
        with self.istemci.session_transaction() as s:
            s["kullanici_id"], s["csrf"] = kisi["id"], "anahtar"

    def post(self, adres, **veri):
        return self.istemci.post(adres, data=dict(veri, csrf="anahtar"))


class GizliIcerikSizmaz(WebOrtam):
    """Gizlenen mesajın ve kaldırılan konunun içeriği düzenleme formu ve geçmiş sayfalarından da okunamaz."""

    def setUp(self):
        super().setUp()
        self.ali, self.ayse = self.kisi("ali"), self.kisi("ayse")
        self.k = self.konu(self.ali)
        self.m = konular.mesaj_yaz(self.db, self.ali, self.k, "ARGUMAN", "GIZLI_METIN bu menü pahalı olur.")
        konular.mesaj_duzenle(self.db, self.ali, self.m, "GIZLI_METIN bu menü çok pahalı olur.")

    def test_gizlenen_mesaj(self):
        konular.mesaji_gizle(self.db, self.m, "Oylamayla gizlendi.", None)
        for kim in (self.ali, self.ayse):
            self.giris(kim)
            for adres in (f"/mesaj/{self.m}/duzenle", f"/mesaj/{self.m}/gecmis"):
                yanit = self.istemci.get(adres)
                self.assertNotIn("GIZLI_METIN", yanit.get_data(as_text=True), adres)
                self.assertNotEqual(yanit.status_code, 200, adres)

    def test_baskasinin_mesajinin_formu_acilmaz(self):
        self.giris(self.ayse)
        self.assertNotEqual(self.istemci.get(f"/mesaj/{self.m}/duzenle").status_code, 200)

    def test_kaldirilan_konu(self):
        konular.konu_duzenle(self.db, self.ali, self.k, {"baslik": "Yemekhane menüsü tartışması",
                                                          "aciklama": "KALDIRILAN_ACIKLAMA sebze ve baklagil olsun."})
        konular.konuyu_kaldir(self.db, self.k, "Oylamayla kaldırıldı.")
        self.db.commit()
        for adres in (f"/konu/{self.k}/gecmis", f"/mesaj/{self.m}/gecmis"):           # girişsiz ziyaretçi
            self.assertNotIn("sebze ve baklagil", self.istemci.get(adres).get_data(as_text=True), adres)
        self.giris(self.ali)
        yanit = self.istemci.get(f"/konu/{self.k}/duzenle")
        self.assertNotIn("KALDIRILAN_ACIKLAMA", yanit.get_data(as_text=True))


class GizlenenFikir(Ortam):
    """Oylamayla gizlenen fikir süren turda yarışmaz, kazanamaz ve metni oylama sayfasında görünmez."""

    def test_gizlenen_fikir_kazanamaz(self):
        kisiler = self.kisiler(8)
        k, (f1, f2, f3) = self.fikirli_konu(kisiler[:3])
        t = self.tur(k)["id"]
        self.oyla(k, [(f3, kisiler[2:7]), (f1, kisiler[:1]), (f2, kisiler[1:2])], bitir=False)
        konular.mesaji_gizle(self.db, f3, "Oylamayla gizlendi.", None)        # gizleme oylaması kabul edildi
        secenek = next(s for s in oylama.secenekler(self.db, t) if s["mesaj_id"] == f3)
        self.assertEqual(secenek["metin"], oylama.GIZLENEN_FIKIR)
        with self.assertRaises(KuralHatasi):
            oylama.oy_ver(self.db, t, kisiler[7], str(secenek["id"]))
        bildirim = self.db.execute("SELECT COUNT(*) FROM bildirimler WHERE kullanici_id = ? AND metin LIKE "
                                   "'Oy verdiğin fikir oylamayla gizlendi%'", (kisiler[3]["id"],)).fetchone()[0]
        self.assertEqual(bildirim, 1)                                         # ona oy verenler haberdar edilir
        oylama.sonuclandir(self.db, t)
        karar = sonuclar.tur_sonucu(self.db, oylama.teklif_getir(self.db, t), oylama.sonuc(oylama.teklif_getir(self.db, t)))
        self.assertNotIn(str(secenek["id"]), karar.kalanlar)
        self.assertNotIn("3 numaralı fikir", " ".join(r["metin"] for r in oylama.secenekler(self.db, self.tur(k)["id"])))

    def test_fikri_gizlenen_yeni_fikir_yazabilir(self):
        ali, ayse = self.kisi("ali"), self.kisi("ayse")
        k = self.konu(ali)
        f = konular.fikir_yaz(self.db, ayse, k, "İlk fikrim: menü böyle olsun")
        konular.mesaji_gizle(self.db, f, "Oylamayla gizlendi.", None)
        konular.fikir_yaz(self.db, ayse, k, "Yeni fikrim: menüde sebze olsun")
        with self.assertRaises(KuralHatasi):                                  # yarışan fikir yine tek
            konular.fikir_yaz(self.db, ayse, k, "Üçüncü fikir: menü değişsin")


class TurKarariAnlikGoruntusu(Ortam):
    def test_gecmis_tur_kendi_kurallariyla_anlatilir(self):
        kisiler = self.kisiler(10)
        k, (f1, f2, f3) = self.fikirli_konu(kisiler[:3])
        t = self.oyla(k, [(f1, kisiler[:5]), (f2, kisiler[5:9]), (f3, kisiler[9:])])   # %50, %40, %10
        teklif = oylama.teklif_getir(self.db, t)
        once = sonuclar.tur_sonucu(self.db, teklif, oylama.sonuc(teklif))
        self.assertEqual((once.sonuc, len(once.kalanlar)), ("DEVAM", 3))
        self.db.execute("UPDATE parametreler SET deger = '0.2' WHERE kod = 'ELEME_TUR1'")   # sonradan oylamayla değişti
        self.db.onbellek.clear()
        sonra = sonuclar.tur_sonucu(self.db, teklif, oylama.sonuc(teklif))
        self.assertEqual(sonra, once)


class YapayZekaOzetleri(Ortam):
    def test_tur_ozeti_esigi_yanlis_gostermez(self):
        """%4,55 oy alan fikir "%5 … elendi", ezici üstünlükte kaybedenler "elendi" diye yazılmaz."""
        self.yz()
        kisiler = self.kisiler(22)
        k, (f1, f2) = self.fikirli_konu(kisiler[:2])
        self.oyla(k, [(f1, kisiler[:21]), (f2, kisiler[21:])])                # 21/22 ve 1/22 (%4,54)
        ozet = self.db.execute("SELECT icerik FROM mesajlar WHERE konu_id = ? AND tip = 'YZ' ORDER BY id DESC",
                               (k,)).fetchone()["icerik"]
        self.assertIn("%95,4", ozet)
        self.assertIn("%4,5", ozet)
        self.assertNotIn("%5 ", ozet)
        self.assertIn("kabul edilmedi", ozet)                                 # ezici üstünlük: eleme olmadı
        self.assertNotIn("elendi", ozet)

    def test_tartisma_ozeti_alt_yanitlari_da_sayar(self):
        self.yz()
        ali, ayse, can = self.kisiler(3)
        k = self.konu(ali)
        f = konular.fikir_yaz(self.db, ali, k, "Menüde haftada iki gün sebze olsun")
        a = konular.mesaj_yaz(self.db, ayse, k, "ARGUMAN", "Sağlık için iyi olur.", f)
        konular.mesaj_yaz(self.db, can, k, "KARSI_ARGUMAN", "Maliyeti artırır.", a)
        konular.mesaj_yaz(self.db, can, k, "SORU", "Bütçe ne kadar?", f)
        yz.tartisma_ozeti(self.db, k)
        ozet = self.db.execute("SELECT icerik FROM mesajlar WHERE konu_id = ? AND tip = 'YZ'", (k,)).fetchone()["icerik"]
        self.assertIn("1 argüman, 1 karşı argüman, 1 soru", ozet)

    def test_ozet_istegi_kurallari(self):
        self.yz()
        ali, ayse = self.kisi("ali"), self.kisi("ayse")
        k = self.konu(ali)
        konular.mesaj_yaz(self.db, ayse, k, "ARGUMAN", "Sebze yemekleri artmalı.")
        yz.ozet_iste(self.db, ayse, k)
        with self.assertRaises(KuralHatasi):                                  # yeni mesaj yok: özet zaten güncel
            yz.ozet_iste(self.db, ayse, k)
        konular.mesaj_yaz(self.db, ali, k, "SORU", "Hangi gün olsun?")
        yz.ozet_iste(self.db, ayse, k)
        konular.konuyu_kaldir(self.db, k, "Oylamayla kaldırıldı.")
        konular.mesaj_yaz  # kaldırılmış konuya özet yazılmaz
        with self.assertRaises(KuralHatasi):
            yz.ozet_iste(self.db, ayse, k)


class AcikYonlendirme(WebOrtam):
    def test_site_ici_yol(self):
        for iyi in ("/", "/konu/3", "/konu/3?x=1#m2"):
            self.assertTrue(site_ici_yol_mu(iyi), iyi)
        for kotu in ("//kotu.com", "/\t/kotu.com", "/\\kotu.com", "https://kotu.com", "kotu.com", "", None,
                     "/\n/kotu.com"):
            self.assertFalse(site_ici_yol_mu(kotu), repr(kotu))

    def test_giristen_sonra_disari_yonlendirilmez(self):
        self.kisi("ali")
        self.db.commit()
        self.istemci.get("/giris")
        with self.istemci.session_transaction() as s:
            csrf = s["csrf"]
        yanit = self.istemci.post("/giris", data={"takma_ad": "ali", "sifre": "sifre1234", "csrf": csrf,
                                                  "sonra": "/\t/kotu.com"})
        self.assertEqual(yanit.status_code, 302)
        self.assertNotIn("kotu.com", yanit.headers["Location"])

    def test_postta_giris_istenince_geri_donus_adresi_yok(self):
        yanit = self.istemci.post("/konu/1/fikir", data={"csrf": "x"})
        self.assertNotIn("sonra=", yanit.headers.get("Location", ""))


class OturumVeAnahtarlar(WebOrtam):
    def setUp(self):
        super().setUp()
        self.ali = self.kisi("ali")

    def test_sifre_degisince_eski_oturum_ve_api_anahtarlari_gecersiz(self):
        anahtar = guvenlik.api_anahtari_olustur(self.db, self.ali["id"], "Telefon")
        self.giris(kullanicilar.getir(self.db, self.ali["id"]))
        eski = self.app.test_client()                                          # aynı çerezle ikinci cihaz
        with self.istemci.session_transaction() as s, eski.session_transaction() as e:
            e.update(s)
        self.assertEqual(eski.get("/profil").status_code, 200)
        self.assertEqual(self.post("/profil/sifre", eski="sifre1234", yeni="yeniSifre99",
                                   yeni_tekrar="yeniSifre99").status_code, 302)
        self.assertEqual(self.istemci.get("/profil").status_code, 200)         # şifreyi değiştiren oturum açık kalır
        self.assertEqual(eski.get("/profil").status_code, 302)                 # çalınmış eski çerez geçersiz
        self.assertEqual(self.istemci.get("/api/v1/bildirimler", headers={"Authorization": f"Bearer {anahtar}"}
                                          ).status_code, 401)

    def test_ayni_cihaz_anahtari_yenilenir(self):
        for _ in range(7):                                                     # eskiden 6. girişte kilitleniyordu
            guvenlik.api_anahtari_olustur(self.db, self.ali["id"], "Mobil uygulama")
        self.assertEqual(len(guvenlik.api_anahtarlari(self.db, self.ali["id"])), 1)

    def test_api_anahtari_yalnizca_api_altinda_gecerli(self):
        self.db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE id = ?", (self.ali["id"],))
        anahtar = guvenlik.api_anahtari_olustur(self.db, self.ali["id"], "Telefon")
        self.db.commit()
        basliklar = {"Authorization": f"Bearer {anahtar}"}
        self.assertEqual(self.istemci.get("/api/v1/bildirimler", headers=basliklar).status_code, 200)
        self.assertEqual(self.istemci.get("/yonetim/yedek", headers=basliklar).status_code, 403)

    def test_oturumda_sifre_tahmini_sinirli(self):
        for _ in range(5):
            with self.assertRaises(KuralHatasi):
                kullanicilar.sifre_degistir(self.db, self.ali, "yanlis1234", "yeniSifre99", "yeniSifre99")
        with self.assertRaises(KuralHatasi):                                   # doğru şifre de kilit sürerken geçmez
            kullanicilar.sifre_degistir(self.db, self.ali, "sifre1234", "yeniSifre99", "yeniSifre99")

    def test_api_govdesi_nesne_degilse_500_vermez(self):
        anahtar = guvenlik.api_anahtari_olustur(self.db, self.ali["id"], "Telefon")
        self.db.commit()
        basliklar = {"Authorization": f"Bearer {anahtar}"}
        for govde in ([1, 2], "metin", 5, {"baslik": 5, "aciklama": True}):
            yanit = self.istemci.post("/api/v1/konular", json=govde, headers=basliklar)
            self.assertLess(yanit.status_code, 500, govde)


class Kayit(Ortam):
    def test_turkce_benzer_takma_ad_alinamaz(self):
        self.kisi("Çağlar")
        for benzer in ("çağlar", "ÇAĞLAR", "Caglar"):
            with self.assertRaises(KuralHatasi, msg=benzer):
                self.kisi(benzer)

    def test_ayni_adresten_kayit_siniri(self):
        il = self.konum("İstanbul")
        sinir, _ = kullanicilar.KAYIT_SINIRI
        for i in range(sinir):
            kullanicilar.kayit(self.db, "Test Kişi", f"uye{i}", "sifre1234", "sifre1234", "2000-01-01", il,
                               istemci="10.0.0.9")
        with self.assertRaises(KuralHatasi):
            kullanicilar.kayit(self.db, "Test Kişi", "fazla", "sifre1234", "sifre1234", "2000-01-01", il,
                               istemci="10.0.0.9")
        kullanicilar.kayit(self.db, "Test Kişi", "baska", "sifre1234", "sifre1234", "2000-01-01", il,
                           istemci="10.0.0.10")


class OylamaYarislari(Ortam):
    def test_suresi_dolmus_oylamaya_oy_verilmez(self):
        kisiler = self.kisiler(3)
        k, (f1, f2) = self.fikirli_konu(kisiler[:2])
        t = self.tur(k)["id"]
        self.ileri_sar(hours=49)                                               # zamanlayıcı henüz çalışmadı
        with self.assertRaises(KuralHatasi):
            oylama.oy_ver(self.db, t, kisiler[2], self.secenek(t, f1))

    def test_askidaki_uye_hak_sahibi_sayilmaz(self):
        kisiler = self.kisiler(4)
        k, _ = self.fikirli_konu(kisiler[:2])
        t = self.tur(k)
        baglam = oylama.teklif_baglami(self.db, t)
        self.assertEqual(len(uygunluk.oy_hakki_olanlar(self.db, baglam)), 4)
        self.db.execute("UPDATE kullanicilar SET askida_bitis = '2999-01-01 00:00:00' WHERE id = ?", (kisiler[3]["id"],))
        self.assertEqual(len(uygunluk.oy_hakki_olanlar(self.db, baglam)), 3)

    def test_ayni_anda_gelen_fikirler(self):
        """Eşzamanlı istekler "zaten bir fikrin var" kontrolünü birlikte geçip birden fazla fikir yazabiliyordu."""
        from forum import create_app
        ali, ayse = self.kisi("ali"), self.kisi("ayse")
        k = self.konu(ali)
        self.db.commit()
        app = create_app({"VERITABANI": self.yol, "TESTING": True})
        engel = threading.Barrier(8)

        def gonder(i):
            istemci = app.test_client()
            with istemci.session_transaction() as s:
                s["kullanici_id"], s["csrf"] = ayse["id"], "a"
            engel.wait()
            istemci.post(f"/konu/{k}/fikir", data={"csrf": "a", "icerik": f"Eşzamanlı fikir numarası {i}"})
        isler = [threading.Thread(target=gonder, args=(i,)) for i in range(8)]
        for i in isler:
            i.start()
        for i in isler:
            i.join()
        sayi = self.db.execute("SELECT COUNT(*) FROM mesajlar WHERE konu_id = ? AND yazar_id = ? AND tip = 'FIKIR'",
                               (k, ayse["id"])).fetchone()[0]
        self.assertEqual(sayi, 1)


class AnlikAbonelikAdresi(Ortam):
    def test_yalnizca_push_servisleri(self):
        ali = self.kisi("ali")
        anahtarlar = {"p256dh": "x" * 20, "auth": "y" * 10}
        for kotu in ("https://10.0.0.5:8443/x", "https://localhost/x", "https://169.254.169.254/latest",
                     "https://fcm.googleapis.com.kotu.com/x", "http://fcm.googleapis.com/x"):
            with self.assertRaises(KuralHatasi, msg=kotu):
                anlik.abone_ol(self.db, ali, "WEB", {"endpoint": kotu, "keys": anahtarlar})
        anlik.abone_ol(self.db, ali, "WEB", {"endpoint": "https://updates.push.services.mozilla.com/wpush/v2/abc",
                                             "keys": anahtarlar})


class DefterKorumasi(WebOrtam):
    def test_bozma_denemesi_yalnizca_sunum_kipinde(self):
        y = self.kisi("yonetici")
        self.db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE id = ?", (y["id"],))
        self.giris(y)
        self.post("/yonetim/defter/A/boz")
        self.post("/yonetim/defter/B/boz")
        self.assertTrue(defter.durum(self.db.defter_klasoru)["saglikli"])

    def test_butun_dugumler_bozuksa_durum_yine_okunur(self):
        self.kisi("ali")
        self.db.commit()
        for ad in ("A", "B", "C"):
            defter.boz_demo(self.db.defter_klasoru, ad)
        d = defter.durum(self.db.defter_klasoru)
        self.assertEqual({x["durum"] for x in d["dugumler"]}, {"BOZUK"})


class GrafGizliOy(WebOrtam):
    def test_ikili_oy_benzerligi_disari_verilmez(self):
        """İki üyenin oy benzerliği verilirse, kendi oyunu bilen kişi komşusunun gizli oyunu çıkarabiliyordu (T4)."""
        kisiler = self.kisiler(6)
        for i in range(3):                                         # üç çekişmeli oylama: a,b aynı; c,d tersi
            k, (f1, f2) = self.fikirli_konu(kisiler[:2], baslik=f"Yemekhane menüsü tartışması {i}")
            self.oyla(k, [(f1, kisiler[0:2] + kisiler[4:5]), (f2, kisiler[2:4] + kisiler[5:6])])
        self.db.commit()
        veri = self.istemci.get("/api/v1/graf").get_json()
        self.assertNotIn("BENZERLIK", {k["tur"] for k in veri["kenarlar"]})
        for gr in graf.gorus_gruplari(self.db):
            self.assertGreaterEqual(len(gr["uyeler"]), graf.GRUP_EN_AZ)


class ParametreAraliklari(Ortam):
    def test_anlamsiz_degerler_onerilemez(self):
        ali = self.kisi("ali")
        for kod, deger in (("UZMAN_AGIRLIK", "0"), ("SIKAYET_TABANI", "0"), ("SURE_TUR_SAAT", "0"),
                           ("ELEME_TUR4", "1"), ("ESIK_EZICI", "0.01"), ("ELEME_TUR1", "0.8"), ("MIN_KATILIM", "abc")):
            with self.assertRaises(KuralHatasi, msg=kod):
                yonetmelik.degisiklik_teklif_et(self.db, ali, {"tur": "PARAMETRE", "kod": kod, "yeni": deger},
                                                "Bu değişiklik topluluk için gerekli bir düzenlemedir.")
        yonetmelik.degisiklik_teklif_et(self.db, ali, {"tur": "PARAMETRE", "kod": "UZMAN_AGIRLIK", "yeni": "5"},
                                        "Bu değişiklik topluluk için gerekli bir düzenlemedir.")

    def test_varsayilanlar_araliklarin_icinde(self):
        from forum import ayarlar
        for kod, deger, tur, _, _ in ayarlar.VARSAYILAN_PARAMETRELER:
            if tur != "esik":
                alt, ust = ayarlar.PARAMETRE_ARALIKLARI[kod]
                self.assertTrue(alt <= float(deger) <= ust, kod)


class YanitDerinligi(WebOrtam):
    def test_cok_derin_yanit_zinciri_sayfayi_bozmaz(self):
        ali, ayse = self.kisi("ali"), self.kisi("ayse")
        k = self.konu(ali)
        ust = None
        for i in range(300):                                       # eskiden ~250. kademede RecursionError → 500
            ust = konular.mesaj_yaz(self.db, ali if i % 2 else ayse, k, "ARGUMAN", f"Yanıt {i}", ust)
        self.db.commit()
        self.assertEqual(self.istemci.get(f"/konu/{k}").status_code, 200)

        def derinlik(dugum):
            return 1 + max((derinlik(c) for c in dugum["cocuklar"]), default=0)
        self.assertLessEqual(max(derinlik(d) for d in konular.mesaj_agaci(self.db, k)), konular.MAX_YANIT_DERINLIGI + 1)


class KisiselVeri(Ortam):
    def test_tc_kimlik_saglamasi(self):
        self.assertTrue(yonetmelik.tc_kimlik_gecerli_mi("10000000146"))
        self.assertFalse(yonetmelik.tc_kimlik_gecerli_mi("10000000147"))
        self.assertIn("T.C. kimlik numarası", yonetmelik.kisisel_veriler("Kimliğim 10000000146"))
        self.assertEqual(yonetmelik.kisisel_veriler("Sipariş numaram 12345678901, kargo gelmedi"), [])


class Makbuz(Ortam):
    def test_degistirilen_oyun_eski_makbuzu_guncel_degil(self):
        a, b = self.kisi("ali"), self.kisi("banu")
        k, (fa, fb) = self.fikirli_konu([a, b])
        t = self.tur(k)
        secimler = oylama.secim_anahtarlari(self.db, t)
        eski = oylama.oy_ver(self.db, t["id"], b, secimler[0])
        yeni = oylama.oy_ver(self.db, t["id"], b, secimler[1])
        self.db.commit()
        self.assertFalse(defter.makbuz_dogrula(self.db.defter_klasoru, t["id"], eski, secimler)[2])
        self.assertTrue(defter.makbuz_dogrula(self.db.defter_klasoru, t["id"], yeni, secimler)[2])


class Gundem(Ortam):
    def test_tek_kisi_mesaj_seliyle_gundeme_tasiyamaz(self):
        kisiler = self.kisiler(5)
        k1 = self.konu(kisiler[0], baslik="Tek kişinin konusu burada")
        k2 = self.konu(kisiler[1], baslik="Herkesin konusu burada")
        for i in range(12):
            konular.mesaj_yaz(self.db, kisiler[0], k1, "ARGUMAN", f"Yine ben yazıyorum {i}")
        for kim in kisiler[1:]:
            konular.mesaj_yaz(self.db, kim, k2, "ARGUMAN", "Ben de katılıyorum")
        trend, _ = gundem.trend_konular(self.db)
        self.assertEqual(trend[0]["id"], k2)



class TeklifTurleri(Ortam):
    """Strategy + Registry: oylama motoru tür adı bilmez; yeni tür, motora dokunmadan eklenir."""

    def test_kayit_defteri_tanimlarla_eslesir(self):
        self.assertEqual(set(teklif_turleri.TURLER), set(ayarlar.TEKLIF_TIPLERI))
        for kod, tur in teklif_turleri.TURLER.items():
            self.assertIsInstance(tur, teklif_turleri.TeklifTuru)
            self.assertEqual(tur.kod, kod)

    def test_yeni_tur_motor_degismeden_calisir(self):
        """Açık/Kapalı ilkesinin kanıtı: oylama.py'ye tek satır eklemeden yeni bir oylama türü uçtan uca çalışır."""
        uygulananlar = []

        class AnketTuru(teklif_turleri.EvetHayirTuru):
            kod = "ANKET"

            def baglam(self, db, t):
                return uygunluk.Baglam(None, None, 1, esit_agirlik=True)

            def uygula(self, db, t, s, durum):
                uygulananlar.append(durum)

        ayarlar.TEKLIF_TIPLERI["ANKET"] = {"ad": "Anket", "esik": "ESIK_KATEGORI", "sure": "SURE_USUL_SAAT"}
        self.addCleanup(ayarlar.TEKLIF_TIPLERI.pop, "ANKET")
        teklif_turleri.kaydet(AnketTuru)
        self.addCleanup(teklif_turleri.TURLER.pop, "ANKET")
        with self.assertRaises(KeyError):                        # aynı kod iki kez kaydedilemez
            teklif_turleri.kaydet(AnketTuru)

        kisiler = self.kisiler(3)
        t = oylama.teklif_ac(self.db, "ANKET", kisiler[0]["id"], gerekce="Kulüp tişörtü yeşil olsun mu?")
        self.assertEqual(oylama.teklif_basligi(self.db, oylama.teklif_getir(self.db, t)), "Anket: ")
        for kim in kisiler:                                      # herkes oy verince erken biter (EvetHayirTuru)
            oylama.oy_ver(self.db, t, kim, "EVET")
        self.assertEqual(uygulananlar, ["KABUL"])
        self.assertEqual(oylama.teklif_getir(self.db, t)["durum"], "KABUL")


if __name__ == "__main__":
    unittest.main()
