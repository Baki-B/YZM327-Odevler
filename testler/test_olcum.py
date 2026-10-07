"""Ölçüm düzeneğinin testleri: denetim kuralları "aptal" temel çizgileri açık farkla geçmeli ve yayın ölçütünün
altına düşmemeli (koruyucu metrik). Eşikler docs/analiz.md 11. bölümdedir."""
import os
import sys
import unittest

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _KOK)
sys.path.insert(0, os.path.join(_KOK, "olcum"))

import denetim_olcumu as olcum  # noqa: E402
import gecikme_olcumu  # noqa: E402
import urun_metrikleri  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_forum import Ortam  # noqa: E402


class DenetimOlcumu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sonuc = {k: olcum.olc(k)[0] for k in olcum.KUMELER}

    def test_kural_temel_cizgileri_gecer(self):
        for kume, s in self.sonuc.items():
            for madde in ("D1", "D2"):
                kural = s[madde]["Kural (anahtar kelime/desen)"]["F1"]
                self.assertGreater(kural, s[madde]["Çoğunluk sınıfı (hep temiz)"]["F1"], (kume, madde))
            d3 = s["D3"]
            self.assertGreater(d3["Kural (ontoloji kavramları)"]["makro_F1"], 3 * d3["Rastgele"]["makro_F1"], kume)

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
