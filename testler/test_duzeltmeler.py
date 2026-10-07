"""Yazılım mühendisliği incelemesinde bulunan hataların düzeltmelerini koruyan testler.

Her test önce hatayı yeniden üretecek biçimde yazıldı (düzeltmeden önce başarısız oluyordu), sonra kod düzeltildi.
"""
import logging
import os
import sys
import unittest

_KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(_KLASOR), _KLASOR]

from forum import defter, devir, gorevler, kategoriler, konular, kullanicilar, oylama, veritabani, yonetim  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
