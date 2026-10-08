"""Tarayıcı sürümünün köprüsü (tarayici/kopru.py) normal Python'da sınanır: Pyodide içinde de aynı kod çalışır.
Uçtan uca tarayıcı denemesi (service worker, IndexedDB) docs/rehber.md'de anlatılan adımlarla elle/otomatik yapılır."""
import importlib
import os
import re
import sys
import tempfile
import unittest

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _KOK)
sys.path.insert(0, os.path.join(_KOK, "tarayici"))

from forum import guvenlik  # noqa: E402

UYGULAMA = "https://baki-b.github.io/YZM327-Odevler/app"


class TarayiciKoprusu(unittest.TestCase):
    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["AGORA_VERI"] = self.klasor.name
        self.eski_yontem = guvenlik.SIFRE_YONTEMI
        sys.modules.pop("kopru", None)
        self.kopru = importlib.import_module("kopru")

    def tearDown(self):
        guvenlik.SIFRE_YONTEMI = self.eski_yontem
        os.environ.pop("AGORA_VERI", None)
        sys.modules.pop("kopru", None)
        self.klasor.cleanup()

    def iste(self, kopru, yontem, yol, govde=b"", tur=None):
        basliklar = {"content-type": tur} if tur else {}
        durum, basliklar, veri = kopru.istek(yontem, UYGULAMA, yol, basliklar, govde)
        return durum, dict(basliklar), veri.decode("utf-8", "replace")

    def test_demo_verisi_yuklenir_ve_adresler_alt_klasorle_uretilir(self):
        self.assertTrue(self.kopru.YENI)
        durum, basliklar, sayfa = self.iste(self.kopru, "GET", "/konular")
        self.assertEqual(durum, 200)
        self.assertIn('href="/YZM327-Odevler/app/konu/', sayfa)
        self.assertIn('data-sw="0"', sayfa)                                 # uygulamanın kendi service worker'ı kaydedilmez
        self.assertIn("frame-ancestors 'self'", basliklar["Content-Security-Policy"])
        self.assertEqual(basliklar["X-Frame-Options"], "SAMEORIGIN")
        self.assertNotIn("Set-Cookie", basliklar)                           # çerezler köprüde tutulur

    def test_oturum_ve_veri_sayfa_yenilenince_kalir(self):
        _, _, form = self.iste(self.kopru, "GET", "/giris")
        csrf = re.search(r'name="csrf" value="([^"]+)"', form).group(1)
        durum, basliklar, _ = self.iste(self.kopru, "POST", "/giris", f"csrf={csrf}&takma_ad=ayse&sifre=forum1234".encode(),
                                        "application/x-www-form-urlencoded")
        self.assertEqual(durum, 302)
        self.assertTrue(basliklar["Location"].startswith("/YZM327-Odevler/app/"))
        # sayfa yenilendi: işçi baştan başlar, köprü yeniden yüklenir; veriler ve oturum /veri'den okunur
        sys.modules.pop("kopru", None)
        yeni = importlib.import_module("kopru")
        self.assertFalse(yeni.YENI)                                         # demo verisi ikinci kez yüklenmez
        durum, _, sayfa = self.iste(yeni, "GET", "/profil")
        self.assertEqual(durum, 200)
        self.assertIn("@ayse", sayfa)

    def test_sunum_kipi_acik(self):
        self.assertTrue(self.kopru.app.config["DEMO"])
        self.assertTrue(self.kopru.app.config["TARAYICI"])


if __name__ == "__main__":
    unittest.main()
