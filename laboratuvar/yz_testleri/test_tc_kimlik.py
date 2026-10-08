"""S01-49 uygulamalı soru 6: aynı aracın yazdığı testler (ilk öneri, değiştirilmeden kaydedildi)."""

import unittest

from tc_kimlik import tc_kimlik_gecerli


class TcKimlikGecerliTest(unittest.TestCase):
    def test_gecerli_numara_1(self):
        self.assertTrue(tc_kimlik_gecerli("10000000146"))

    def test_gecerli_numara_2(self):
        self.assertTrue(tc_kimlik_gecerli("12345678950"))

    def test_gecerli_numara_3(self):
        self.assertTrue(tc_kimlik_gecerli("11111111110"))

    def test_bastaki_sondaki_bosluk_kirpilir(self):
        self.assertTrue(tc_kimlik_gecerli("  10000000146  "))

    def test_ilk_hane_sifir_olamaz(self):
        self.assertFalse(tc_kimlik_gecerli("01234567890"))

    def test_tamami_sifir(self):
        self.assertFalse(tc_kimlik_gecerli("00000000000"))

    def test_10_hane_cok_kisa(self):
        self.assertFalse(tc_kimlik_gecerli("1000000014"))

    def test_12_hane_cok_uzun(self):
        self.assertFalse(tc_kimlik_gecerli("100000001461"))

    def test_bos_dize(self):
        self.assertFalse(tc_kimlik_gecerli(""))

    def test_yalnizca_bosluk(self):
        self.assertFalse(tc_kimlik_gecerli("           "))

    def test_harf_iceren(self):
        self.assertFalse(tc_kimlik_gecerli("1000000014a"))

    def test_ic_bosluk_iceren(self):
        self.assertFalse(tc_kimlik_gecerli("10000 00146"))

    def test_10_hane_sagLama_hatali(self):
        self.assertFalse(tc_kimlik_gecerli("10000000156"))

    def test_11_hane_sagLama_hatali(self):
        self.assertFalse(tc_kimlik_gecerli("10000000147"))

    def test_tam_genislikli_rakamlar(self):
        self.assertFalse(tc_kimlik_gecerli("１０００００００１４６"))

    def test_str_olmayan_deger(self):
        self.assertFalse(tc_kimlik_gecerli(10000000146))


if __name__ == "__main__":
    unittest.main()
