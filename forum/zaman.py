"""Zaman tek bir yerden okunur. Testler ve demo verisi `simdi` fonksiyonunu değiştirerek zamanı ileri sarabilir."""
from datetime import datetime


def simdi():
    return datetime.now().replace(microsecond=0)


def metin(an):
    return an.isoformat(sep=" ")


def simdi_metin():
    return metin(simdi())


def coz(deger):
    return datetime.fromisoformat(deger)
