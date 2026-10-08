"""Oylamaların ortak sabitleri ve eşik karşılaştırması.

Yaprak modül: yalnızca ayarlar'a bağlıdır. Oylamaların ortak sabitlerini ve eşik karşılaştırmasını tutar; böylece
teklif_turleri ile oylama arasında içe aktarma döngüsü oluşmaz.
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
