"""Metin yardımcıları (yüzde, kısaltma, site içi adres). Saf fonksiyonlar; veritabanı ya da Flask bilmez."""
import math
from urllib.parse import urlsplit


def yuzde(oran):
    """Oranı Türkçe yüzde olarak yazar: 0.75 → "%75", 0.0455 → "%4,5", 0.745 → "%74,5".

    Ondalık kısım YUVARLANMAZ, kesilir. Böylece eşiğin altında kalan bir oran ekranda eşiğe eşit görünmez
    (%4,55 "%5" yazılıp "elendi" denirse okuyan kural yanlış uygulandı sanır)."""
    onda = math.floor((oran or 0) * 1000 + 1e-6) / 10
    return "%" + (f"{onda:.0f}" if onda == int(onda) else f"{onda:.1f}".replace(".", ","))


def kisalt(metin, n):
    """Boşlukları sadeleştirir; n karakterden uzunsa üç noktayla kısaltır."""
    metin = " ".join(metin.split())
    return metin if len(metin) <= n else metin[: n - 1] + "…"


def site_ici_yol_mu(adres):
    """Adres bu sitenin içinde bir yol mu? Yönlendirmeden ve bildirim bağlantısından önce sorulur (açık yönlendirme).

    "/konu/3" evet; "//kotu.com", "/\t/kotu.com" (tarayıcı sekmeyi atar → //kotu.com), "/\\kotu.com",
    "https://kotu.com" hayır."""
    if not isinstance(adres, str) or not adres.startswith("/") or adres.startswith("//"):
        return False
    if "\\" in adres or any(ord(c) < 32 or ord(c) == 127 for c in adres):
        return False
    parca = urlsplit(adres)
    return not parca.scheme and not parca.netloc
