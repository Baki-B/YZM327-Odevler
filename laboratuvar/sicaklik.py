"""S02-50 mini laboratuvar, 3. görev: aynı istem T = 0, 0,7 ve 1,5 sıcaklıkla 10'ar kez çalıştırılır; kaç farklı yanıt
geldiği sayılır.

    python laboratuvar/sicaklik.py --api      # Anthropic API (ANTHROPIC_API_KEY ortam değişkeni gerekir; S01-17)
    python laboratuvar/sicaklik.py            # API anahtarı yoksa: aynı deney yerel, küçük bir dil modeliyle

Sıcaklık (S02-32): logitler softmax'tan önce T'ye bölünür. T → 0 en olası tokenı seçer (belirlenimci); T büyüdükçe
dağılım düzleşir ve yanıtlar çeşitlenir.

API notları (Anthropic belgeleri, 2026):
  * Opus 4.7 ve sonrası sıcaklık taşıyan her isteği 400 hatasıyla reddeder; Sonnet 5/5.5 ve
    Haiku 5.5 varsayılan dışı değerleri reddeder. Deney bu yüzden sıcaklığı hâlâ kabul eden bir modelle yapılır
    (varsayılan claude-sonnet-4-6). Slayttaki (S02-42) "temperature=0 ile sabitle" önlemi yeni modellerde yoktur.
  * Python SDK'sının 1.x sürümü temperature parametresini imzadan kaldırdı; değer extra_body ile gönderilir.
  * Anthropic API'sinde sıcaklık 0 ile 1 arasındadır; 1,5'in reddedilmesi beklenir. Betik reddi de sonuç olarak yazar.
Yerel model: projenin kullanım kılavuzundaki (docs/rehber.md, ~1.000 satır Türkçe) cümlelerden kurulan kelime ikilisi
(bigram) modeli. Bir sonraki kelimenin olasılığı sayımla orantılıdır; sıcaklık T için p ∝ sayı^(1/T) (logit = log sayı,
logit / T). Gerçek bir dil modeli değildir; yalnızca sıcaklığın çeşitliliğe etkisini gösterir.
"""
import argparse
import collections
import os
import random
import re

KLASOR = os.path.dirname(os.path.abspath(__file__))
SICAKLIKLAR = (0.0, 0.7, 1.5)
TEKRAR = 10
ISTEM = "Bir okul forumu için en fazla on kelimelik bir slogan yaz. Yalnızca sloganı yaz."
API_MODELI = "claude-sonnet-4-6"


# --- API ---

def api_deneyi(model):
    import anthropic

    istemci = anthropic.Anthropic()                       # anahtar ortamdan okunur; kodda anahtar yok
    sonuc = {}
    for t in SICAKLIKLAR:
        yanitlar = []
        for _ in range(TEKRAR):
            try:
                y = istemci.messages.create(model=model, max_tokens=100, extra_body={"temperature": t},
                                            messages=[{"role": "user", "content": ISTEM}])
            except anthropic.BadRequestError as hata:
                sonuc[t] = f"API reddetti (400): {hata.message}"
                break
            yanitlar.append("".join(b.text for b in y.content if b.type == "text").strip())
        else:
            sonuc[t] = yanitlar
    return sonuc


# --- Yerel kelime ikilisi modeli ---

SON = "</s>"


def kelime_ikilileri():
    sayim = collections.defaultdict(collections.Counter)
    with open(os.path.join(KLASOR, "..", "docs", "rehber.md"), encoding="utf-8") as f:
        for cumle in re.split(r"[.!?\n]+", f.read()):
            kelimeler = re.findall(r"[^\W\d_]+", cumle)
            if len(kelimeler) < 3:
                continue                                      # başlık, tablo hücresi, kod parçası
            kelimeler = [kelimeler[0].lower()] + kelimeler[1:] + [SON]
            for a, b in zip(kelimeler, kelimeler[1:]):
                sayim[a][b] += 1
    return sayim


def uret(sayim, baslangic, t, rastgele, en_uzun=6):
    kelimeler = [baslangic]
    while len(kelimeler) < en_uzun and kelimeler[-1] in sayim:
        adaylar = sorted(sayim[kelimeler[-1]].items())    # sıralı: T = 0'da eşitlik hep aynı biçimde bozulur
        if t == 0:
            sonraki = max(adaylar, key=lambda x: x[1])[0]
        else:
            sonraki = rastgele.choices([k for k, _ in adaylar], weights=[n ** (1 / t) for _, n in adaylar])[0]
        if sonraki == SON:
            break
        kelimeler.append(sonraki)
    return " ".join(kelimeler)


def yerel_deney(baslangic="konu", tekrar=TEKRAR):
    sayim = kelime_ikilileri()
    return {t: [uret(sayim, baslangic, t, random.Random(tohum)) for tohum in range(tekrar)] for t in SICAKLIKLAR}


def ilk_adim_dagilimi(baslangic="konu"):
    """Başlangıç kelimesinden sonraki ilk kelimenin olasılıkları, her sıcaklıkta (örneklemesiz, kesin hesap).
    Döner: {T: [(kelime, olasılık), ...]} (olasılığa göre azalan)."""
    adaylar = sorted(kelime_ikilileri()[baslangic].items())
    sonuc = {}
    for t in SICAKLIKLAR:
        if t == 0:
            en = max(adaylar, key=lambda x: x[1])[0]
            sonuc[t] = [(k, 1.0 if k == en else 0.0) for k, _ in adaylar]
        else:
            agirlik = [n ** (1 / t) for _, n in adaylar]
            sonuc[t] = [(k, a / sum(agirlik)) for (k, _), a in zip(adaylar, agirlik)]
        sonuc[t].sort(key=lambda x: -x[1])
    return sonuc


def rapor(sonuc):
    print("| T | Farklı yanıt (10 denemede) | Örnek |")
    print("|---|---|---|")
    for t, yanitlar in sonuc.items():
        if isinstance(yanitlar, str):
            print(f"| {t:g} | — | {yanitlar} |")
            continue
        sayac = collections.Counter(yanitlar)
        print(f"| {t:g} | {len(sayac)} | {sayac.most_common(1)[0][0]} |")
    for t, yanitlar in sonuc.items():
        if not isinstance(yanitlar, str):
            print(f"\nT = {t:g}:")
            for y, n in collections.Counter(yanitlar).most_common():
                print(f"  {n} × {y}")


def main():
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--api", action="store_true", help="Anthropic API ile çalıştır (ANTHROPIC_API_KEY gerekir)")
    a.add_argument("--model", default=API_MODELI)
    secim = a.parse_args()
    if secim.api:
        print(f"Model: {secim.model} · istem: {ISTEM}\n")
        rapor(api_deneyi(secim.model))
    else:
        print("Yerel kelime ikilisi modeli (docs/rehber.md) · başlangıç kelimesi: 'konu' · en fazla 6 kelime\n")
        rapor(yerel_deney())
        sayim = kelime_ikilileri()["konu"]
        print(f"\n'konu'dan sonraki ilk kelimenin olasılığı (kesin hesap; {len(sayim)} aday, en sık: "
              + ", ".join(f"{k} {n}" for k, n in sayim.most_common(3)) + "):")
        for t, dagilim in ilk_adim_dagilimi().items():
            print(f"  T = {t:g}: " + ", ".join(f"{k} {p:.2f}" for k, p in dagilim[:4]))


if __name__ == "__main__":
    main()
