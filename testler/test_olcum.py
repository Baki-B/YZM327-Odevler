"""Ölçüm düzeneğinin testleri: denetim kuralları "aptal" temel çizgileri açık farkla geçmeli ve yayın ölçütünün
altına düşmemeli (koruyucu metrik). Eşikler docs/analiz.md 11. bölümdedir. Metrik ve temel çizgi hesapları da sınanır
(H2-54: ölçüm kodu bozuksa her sayı yanlıştır)."""
import os
import sys
import unittest

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _KOK)
sys.path.insert(0, os.path.join(_KOK, "olcum"))

import denetim_olcumu as olcum  # noqa: E402
from forum import denetim, ontoloji  # noqa: E402
import gecikme_olcumu  # noqa: E402
import urun_metrikleri  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_forum import Ortam  # noqa: E402


class DenetimOlcumu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sonuc = {k: olcum.olc(k)[0] for k in olcum.KUMELER}

    def test_kural_temel_cizgileri_gecer(self):
        """Her kümede kural, iki temel çizgiyi de açık farkla geçer: D1/D2'de F1 en az +0,10, D3'te makro F1 3 kat."""
        for kume, s in self.sonuc.items():
            for madde in ("D1", "D2"):
                kural = s[madde]["Kural (anahtar kelime/desen)"]["F1"]
                for temel in ("Çoğunluk sınıfı (hep temiz)", "Rastgele (beklenen)"):
                    self.assertGreaterEqual(kural, s[madde][temel]["F1"] + 0.10, (kume, madde, temel))
            d3 = s["D3"]
            for temel in ("Çoğunluk sınıfı", "Rastgele (beklenen)"):
                self.assertGreater(d3["Kural (ontoloji kavramları)"]["makro_F1"], 3 * d3[temel]["makro_F1"], (kume, temel))

    def test_test_kumesinde_yayin_olcutu_korunur(self):
        """docs/analiz.md 11. bölüm: D1 kesinlik ve F1, D2 duyarlılık, D3 makro F1 (5.3'teki öncelikli metrikler)."""
        s = self.sonuc["test"]
        d1 = s["D1"]["Kural (anahtar kelime/desen)"]
        self.assertGreaterEqual(d1["kesinlik"], 0.80)
        self.assertGreaterEqual(d1["F1"], 0.80)
        self.assertGreaterEqual(s["D2"]["Kural (anahtar kelime/desen)"]["duyarlilik"], 0.80)
        self.assertGreaterEqual(s["D3"]["Kural (ontoloji kavramları)"]["makro_F1"], 0.85)

    def test_metrik_hesabi(self):
        m = olcum.ikili_metrikler(["VAR", "VAR", "YOK", "YOK"], ["VAR", "YOK", "VAR", "YOK"])
        self.assertEqual((m["DP"], m["YP"], m["YN"], m["DN"]), (1, 1, 1, 1))
        self.assertEqual((m["kesinlik"], m["duyarlilik"], m["F1"]), (0.5, 0.5, 0.5))
        self.assertEqual(olcum.ikili_metrikler(["VAR"], ["YOK"])["F1"], 0.0)       # sıfıra bölme yok

    def test_f_beta(self):
        """Kesinlik 1, duyarlılık 0,5: F0,5 kesinliğe yakın, F2 duyarlılığa yakın (H2-30)."""
        m = olcum.ikili_metrikler(["VAR", "VAR", "YOK"], ["VAR", "YOK", "YOK"])
        self.assertAlmostEqual(m["F1"], 2 / 3)
        self.assertAlmostEqual(m["F0,5"], 5 / 6)
        self.assertAlmostEqual(m["F2"], 5 / 9)

    def test_makro_f1_ve_karisiklik(self):
        gercek, tahmin = ["A", "A", "B", "B"], ["A", "B", "B", "B"]
        self.assertAlmostEqual(olcum.makro_f1(gercek, tahmin), (2 / 3 + 0.8) / 2)
        self.assertEqual(olcum.makro_f1(gercek, gercek), 1.0)
        m = olcum.karisiklik(gercek, tahmin)
        self.assertEqual((m["A"]["A"], m["A"]["B"], m["B"]["B"], m["B"]["A"]), (1, 1, 2, 0))

    def test_temel_cizgiler(self):
        """Çoğunluk sınıfı ("hep temiz") hiçbir şeyi yakalamaz; rastgelenin beklenen değeri dengeli ikili kümede ~0,5'tir
        ve tohumlar sabit olduğu için her çalıştırmada aynıdır."""
        gercek = ["VAR", "YOK"] * 10
        self.assertEqual(olcum.ikili_metrikler(gercek, ["YOK"] * 20)["F1"], 0.0)
        r = olcum.rastgele_beklenen(gercek, ("VAR", "YOK"), olcum.ikili_metrikler)
        self.assertAlmostEqual(r["duyarlilik"], 0.5, delta=0.03)
        self.assertAlmostEqual(r["dogruluk"], 0.5, delta=0.03)
        self.assertEqual(r, olcum.rastgele_beklenen(gercek, ("VAR", "YOK"), olcum.ikili_metrikler))
        siniflar = list("ABCDEFG")
        d = olcum.rastgele_beklenen(siniflar * 2, siniflar, olcum.cok_sinifli)
        self.assertAlmostEqual(d["dogruluk"], 1 / 7, delta=0.02)


class TurkceBuyukHarf(unittest.TestCase):
    """H2-41 "Türkçe tuzağı": str.lower() 'I'yı 'i', 'İ'yi 'i̇' yapar. Ölçüm kümelerinde büyük harfli örnek olmadığı için
    bu hata ölçümde görünmez; ayrı test gerekir."""

    def test_tr_kucuk(self):
        self.assertEqual(ontoloji.tr_kucuk("YARALI İSTANBUL"), "yaralı istanbul")

    def test_buyuk_harfli_kaba_ifade_yakalanir(self):
        for metin in ("BEYİNSİZ", "Sen GERİ ZEKALI mısın?", "ŞEREFSİZ", "HAYSİYETSİZLİK bu"):
            self.assertTrue(denetim.kaba_ifadeler(metin), metin)


class Yuzdelik(unittest.TestCase):
    def test_en_yakin_sira(self):
        for n, p, beklenen in ((60, 95, 57), (20, 95, 19), (100, 95, 95), (100, 50, 50), (1, 95, 1), (7, 50, 4)):
            self.assertEqual(gecikme_olcumu.yuzdelik(list(range(1, n + 1)), p), beklenen, (n, p))


class UrunMetrikleri(Ortam):
    def test_bos_forumda_tanimsiz_degerler_cokmez(self):
        m = urun_metrikleri.metrikler(self.db)
        self.assertIsNone(m["is"]["Karara bağlanma oranı (kapanan konular)"])
        self.assertEqual(m["koruyucu"]["Defter–veritabanı tutarsızlığı (adet)"], 0)
        self.assertIn("| Koruyucu |", urun_metrikleri.rapor(self.db))

    def test_karar_ve_katilim(self):
        kisiler = self.kisiler(4)
        k = self.konu(kisiler[0])
        self.db.execute("UPDATE konular SET durum = 'KARARA_BAGLANDI', kabul_tarihi = olusturma WHERE id = ?", (k,))
        self.db.execute("""INSERT INTO teklifler (tip, konu_id, esik, baslangic, bitis, durum, sonuc)
                           VALUES ('KARAR', ?, 'X', '', '', 'KABUL', ?)""",
                        (k, '{"katilan": 3, "hak_sahibi": 4, "yeter": true}'))
        m = urun_metrikleri.metrikler(self.db)
        self.assertEqual(m["is"]["Karara bağlanma oranı (kapanan konular)"], 1.0)
        self.assertEqual(m["urun"]["Fikir oylamalarında ortalama katılım (katılan / hak sahibi)"], 0.75)
        self.assertEqual(m["urun"]["Açılıştan karara medyan süre (saat)"], 0.0)


if __name__ == "__main__":
    unittest.main()
