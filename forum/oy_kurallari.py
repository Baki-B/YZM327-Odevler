"""Oylamaların ortak sabitleri ve eşik karşılaştırması.

Yaprak modül: yalnızca ayarlar'a bağlıdır. Önceden teklif_turleri.py'deydi; oylama.py onları oradan aldığı için
`import forum.teklif_turleri` ilk içe aktarma olarak döngüye girip hata veriyordu (teklif_turleri → kategoriler →
oylama → teklif_turleri). Ortak parçalar buraya taşınınca döngü modül düzeyinde kırıldı.
"""
from . import ayarlar

CEKIMSER = "CEKIMSER"
EVET_HAYIR = ["EVET", "HAYIR", CEKIMSER]
GIZLENEN_FIKIR = "Bu fikir oylamayla gizlendi."


def esik_saglandi(pay, payda, esik):
    """Tam sayılarla kesin karşılaştırma (yuvarlama hatası yok)."""
    if payda <= 0:
        return False
    e = ayarlar.ESIKLER[esik]
    return pay * e["payda"] > e["pay"] * payda if e["kati"] else pay * e["payda"] >= e["pay"] * payda
