"""Yazılım mühendisliği incelemesinde bulunan hataların düzeltmelerini koruyan testler.

Her test önce hatayı yeniden üretecek biçimde yazıldı (düzeltmeden önce başarısız oluyordu), sonra kod düzeltildi.
"""
import logging
import os
import sys
import tempfile
import unittest

_KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(_KLASOR), _KLASOR]

from forum import (defter, devir, gorevler, kategoriler, konular, kullanicilar, oylama, sonuclar, veritabani,  # noqa: E402
                   yonetim, yonetmelik, yz)
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


if __name__ == "__main__":
    unittest.main()
