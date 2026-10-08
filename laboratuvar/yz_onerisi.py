"""S02-50 mini laboratuvar, 4. görev: bir YZ kodlama aracının 5 fonksiyon için İLK önerisi (değiştirilmeden kaydedildi). İmport'lar laboratuvar/import_dogrula.py ile denetlenir."""

import re
from datetime import datetime

import dateparser
import pandas as pd
import pdfplumber
import zeyrek
from schwifty import IBAN
from transformers import pipeline


def _turkce_kucuk(s: str) -> str:
    """Türkçe kurallarına uygun küçük harfe çevirme (I -> ı, İ -> i)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


# ---------------------------------------------------------------------------
# 1. Kök bulma
# ---------------------------------------------------------------------------
_analizci = None


# pip install zeyrek
def kokleri_bul(metin: str) -> list[str]:
    """Türkçe bir metindeki kelimeleri köklerine (gövdelerine) ayırır."""
    global _analizci
    if _analizci is None:
        _analizci = zeyrek.MorphAnalyzer()

    kokler = []
    # Kesme işaretinden sonrasını (Ankara'da -> Ankara) at, rakam ve noktalamayı yoksay.
    for kelime in re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", metin):
        kelime = re.split(r"['’]", kelime)[0]
        sonuc = _analizci.lemmatize(_turkce_kucuk(kelime))
        # sonuc biçimi: [(kelime, [kok1, kok2, ...])]
        if sonuc and sonuc[0][1]:
            kokler.append(sonuc[0][1][0])
        else:
            kokler.append(_turkce_kucuk(kelime))
    return kokler


# ---------------------------------------------------------------------------
# 2. PDF tabloları
# ---------------------------------------------------------------------------
# pip install pdfplumber pandas
def pdf_tablolari(yol: str) -> list:
    """Bir PDF dosyasındaki tabloları pandas DataFrame listesi olarak döndürür."""
    tablolar = []
    with pdfplumber.open(yol) as pdf:
        for sayfa in pdf.pages:
            for tablo in sayfa.extract_tables():
                if not tablo:
                    continue
                if len(tablo) > 1:
                    # İlk satırı sütun başlığı kabul et.
                    df = pd.DataFrame(tablo[1:], columns=tablo[0])
                else:
                    df = pd.DataFrame(tablo)
                tablolar.append(df)
    return tablolar


# ---------------------------------------------------------------------------
# 3. Türkçe tarih ifadeleri
# ---------------------------------------------------------------------------
_GUN_ADLARI = r"\b(pazartesi|salı|çarşamba|perşembe|cumartesi|cuma|pazar)\b"
_GUN_BOLUMU = r"\b(sabah|öğleden sonra|öğle|akşam|gece)\s+(\d{1,2})(?::(\d{2}))?\b"


# pip install dateparser
def turkce_tarih(ifade: str) -> datetime:
    """'3 Ekim 2026 Cumartesi' ya da 'dün akşam 8' gibi ifadeleri datetime'a çevirir."""
    simdi = datetime.now()
    ayarlar = {
        "PREFER_DATES_FROM": "past",
        "RELATIVE_BASE": simdi,
        "RETURN_AS_TIMEZONE_AWARE": False,
    }
    metin = _turkce_kucuk(ifade.strip())

    # "akşam 8", "sabah 7:30", "gece 11" gibi gün bölümü + saat ifadelerini ayır.
    saat = dakika = None
    m = re.search(_GUN_BOLUMU, metin)
    if m:
        bolum, saat, dakika = m.group(1), int(m.group(2)), int(m.group(3) or 0)
        if bolum in ("öğleden sonra", "öğle", "akşam") and saat < 12:
            saat += 12
        elif bolum == "gece" and 6 <= saat < 12:
            saat += 12
        elif bolum == "gece" and saat == 12:
            saat = 0
        metin = (metin[: m.start()] + " " + metin[m.end():]).strip()

    # Tam tarih (yıl) varsa gün adı gereksizdir; ayrıştırıcıyı şaşırtmasın.
    if re.search(r"\d{4}", metin):
        metin = re.sub(_GUN_ADLARI, " ", metin).strip()

    if metin:
        tarih = dateparser.parse(metin, languages=["tr"], settings=ayarlar)
    else:
        tarih = simdi

    if tarih is None:
        raise ValueError(f"Tarih ifadesi anlaşılamadı: {ifade!r}")

    if saat is not None:
        tarih = tarih.replace(hour=saat, minute=dakika, second=0, microsecond=0)
    return tarih


# ---------------------------------------------------------------------------
# 4. IBAN denetimi ve banka adı
# ---------------------------------------------------------------------------
# Türkiye IBAN'ında 5.-9. karakterler banka kodudur (kısmi liste).
_TR_BANKALARI = {
    "00010": "T.C. Ziraat Bankası",
    "00012": "Türkiye Halk Bankası",
    "00015": "Türkiye Vakıflar Bankası",
    "00032": "Türk Ekonomi Bankası (TEB)",
    "00046": "Akbank",
    "00062": "Garanti BBVA",
    "00064": "Türkiye İş Bankası",
    "00067": "Yapı ve Kredi Bankası",
    "00099": "ING Bank",
    "00103": "Fibabanka",
    "00111": "QNB Finansbank",
    "00123": "HSBC Bank",
    "00134": "Denizbank",
    "00203": "Albaraka Türk",
    "00205": "Kuveyt Türk",
    "00206": "Türkiye Finans Katılım Bankası",
}


# pip install schwifty
def iban_bilgisi(iban: str) -> dict:
    """Bir IBAN'ın geçerli olup olmadığını denetler ve banka adını döndürür."""
    sonuc = {
        "gecerli": False,
        "iban": None,
        "ulke": None,
        "banka": None,
        "bic": None,
        "hata": None,
    }
    temiz = re.sub(r"\s+", "", iban).upper()

    try:
        kayit = IBAN(temiz)  # sağlama basamaklarını ve uzunluğu denetler
    except ValueError as hata:
        sonuc["hata"] = str(hata)
        return sonuc

    sonuc["gecerli"] = True
    sonuc["iban"] = kayit.compact
    sonuc["ulke"] = kayit.country_code

    banka = kayit.bank
    if banka:
        sonuc["banka"] = banka.get("name")
        sonuc["bic"] = banka.get("bic")

    if sonuc["banka"] is None and kayit.country_code == "TR":
        sonuc["banka"] = _TR_BANKALARI.get(kayit.compact[4:9])

    return sonuc


# ---------------------------------------------------------------------------
# 5. Duygu sınıflandırma
# ---------------------------------------------------------------------------
_siniflandirici = None


# pip install transformers torch
def duygu(metin: str) -> str:
    """Türkçe bir metni 'olumlu' / 'olumsuz' / 'nötr' diye sınıflandırır."""
    global _siniflandirici
    if not metin or not metin.strip():
        return "nötr"
    if _siniflandirici is None:
        _siniflandirici = pipeline(
            "sentiment-analysis",
            model="savasy/bert-base-turkish-sentiment-cased",
        )

    sonuc = _siniflandirici(metin, truncation=True, max_length=512)[0]
    etiket = sonuc["label"].lower()
    skor = sonuc["score"]

    # Model ikili (positive/negative) çalışır; düşük güveni "nötr" say.
    if skor < 0.60:
        return "nötr"
    return "olumlu" if etiket.startswith("pos") else "olumsuz"
