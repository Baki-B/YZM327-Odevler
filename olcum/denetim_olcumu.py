"""Yönetmelik denetiminin (D1 kaba ifade, D2 kişisel veri, D3 kategoriye uygunluk) etiketli örneklerle ölçümü.

Çalıştırmak için:  python olcum/denetim_olcumu.py

Ders slaytı (Hafta 2, "Temel çizgi"): bir sayı, en basit makul çözümle karşılaştırılmadan iyi ya da kötü değildir.
Bu betik kural tabanlı denetimi iki "aptal" temel çizgiyle aynı örnekler üzerinde karşılaştırır:
  * çoğunluk sınıfı: D1/D2 için "hep temiz" (hiçbir şeyi engelleme), D3 için "hep en sık kategori"
  * rastgele: sınıflardan birini eşit olasılıkla seç (tohum sabit, sonuç tekrarlanabilir)
İki örnek kümesi vardır; etiketler kurallar çalıştırılmadan önce elle yazıldı:
  * gelistirme.csv — hata analizi bu kümede yapılır; kurallar bu kümedeki hatalara bakılarak iyileştirilir.
  * test.csv — kurallar değiştirilmeden ÖNCE yazıldı ve kurallar ona bakılarak ayarlanmaz ("test seti kutsaldır").
    Bir iyileştirmenin gerçek etkisi bu kümedeki değişimdir; geliştirme kümesindeki artış iyimserdir.
  * son_test.csv — kurallar dondurulduktan sonra yazıldı ve ölçülmeden önce commit edildi; bir kez ölçüldü
    (docs/analiz.md 6.5). Kurallar bu kümeye bakılarak hiç değiştirilmez.
Örnek sayıları küçüktür; sonuçlar kesin başarım değil, bir referans noktasıdır.
"""
import csv
import os
import random
import sys
import tempfile
from collections import Counter

KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(KLASOR))

from forum import denetim, ontoloji, veritabani  # noqa: E402

VAR, YOK, HICBIRI = "VAR", "YOK", "(eşleşme yok)"


KUMELER = ("gelistirme", "test", "son_test")


def ornekler(madde=None, kume="gelistirme"):
    with open(os.path.join(KLASOR, f"{kume}.csv"), encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if madde is None or r["madde"] == madde]


def ikili_metrikler(gercek, tahmin, pozitif=VAR):
    dp = sum(g == pozitif and t == pozitif for g, t in zip(gercek, tahmin))
    yp = sum(g != pozitif and t == pozitif for g, t in zip(gercek, tahmin))
    yn = sum(g == pozitif and t != pozitif for g, t in zip(gercek, tahmin))
    dn = len(gercek) - dp - yp - yn
    p = dp / (dp + yp) if dp + yp else 0.0
    r = dp / (dp + yn) if dp + yn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"DP": dp, "YP": yp, "YN": yn, "DN": dn, "kesinlik": p, "duyarlilik": r, "F1": f1,
            "dogruluk": (dp + dn) / len(gercek)}


def makro_f1(gercek, tahmin):
    siniflar = sorted(set(gercek))
    return sum(ikili_metrikler(gercek, tahmin, s)["F1"] for s in siniflar) / len(siniflar)


def _ana_kategori(db, kategori_id):
    return ontoloji.ad(db, "kategoriler", ontoloji.atalar(db, "kategoriler", kategori_id)[0])


def d3_tahmini(db, metin):
    kid, _ = ontoloji.en_uygun_kategori(db, metin)
    return _ana_kategori(db, kid) if kid else HICBIRI


def olc(kume="gelistirme"):
    """Döner: {madde: {yöntem: metrikler}} ve hata örnekleri."""
    rastgele = random.Random(42)
    sonuc, hatalar = {}, {}
    kurallar = {"D1": lambda m: VAR if denetim.kaba_ifadeler(m) else YOK,
                "D2": lambda m: VAR if denetim.kisisel_veriler(m) else YOK}
    for madde, kural in kurallar.items():
        satirlar = ornekler(madde, kume)
        gercek = [r["etiket"] for r in satirlar]
        tahmin = [kural(r["metin"]) for r in satirlar]
        sonuc[madde] = {
            "Çoğunluk sınıfı (hep temiz)": ikili_metrikler(gercek, [YOK] * len(gercek)),
            "Rastgele": ikili_metrikler(gercek, [rastgele.choice((VAR, YOK)) for _ in gercek]),
            "Kural (anahtar kelime/desen)": ikili_metrikler(gercek, tahmin),
        }
        hatalar[madde] = [(r["metin"], g, t) for r, g, t in zip(satirlar, gercek, tahmin) if g != t]

    with tempfile.TemporaryDirectory() as klasor:
        db = veritabani.hazirla(os.path.join(klasor, "olcum.db"))
        try:
            ontoloji.yukle(db)
            satirlar = ornekler("D3", kume)
            gercek = [r["etiket"] for r in satirlar]
            tahmin = [d3_tahmini(db, r["metin"]) for r in satirlar]
        finally:
            db.close()
    siniflar = sorted(set(gercek))
    en_sik = Counter(gercek).most_common(1)[0][0]
    sonuc["D3"] = {}
    for ad, t in (("Çoğunluk sınıfı", [en_sik] * len(gercek)),
                  ("Rastgele", [rastgele.choice(siniflar) for _ in gercek]),
                  ("Kural (ontoloji kavramları)", tahmin)):
        sonuc["D3"][ad] = {"dogruluk": sum(g == x for g, x in zip(gercek, t)) / len(gercek), "makro_F1": makro_f1(gercek, t)}
    hatalar["D3"] = [(r["metin"], g, t) for r, g, t in zip(satirlar, gercek, tahmin) if g != t]
    return sonuc, hatalar


def _yuzde(x):
    return f"{x:.2f}".replace(".", ",")


def rapor(kume):
    sonuc, hatalar = olc(kume)
    satirlar = [f"## {kume}.csv"]
    for madde, baslik in (("D1", "D1 Saygın dil (kaba ifade)"), ("D2", "D2 Kişisel veri")):
        liste = ornekler(madde, kume)
        satirlar += [f"\n{baslik} — {len(liste)} örnek, {sum(r['etiket'] == VAR for r in liste)} tanesi VAR", "",
                     "| Yöntem | DP | YP | YN | DN | Kesinlik | Duyarlılık | F1 | Doğruluk |",
                     "|---|---|---|---|---|---|---|---|---|"]
        for ad, m in sonuc[madde].items():
            satirlar.append(f"| {ad} | {m['DP']} | {m['YP']} | {m['YN']} | {m['DN']} | {_yuzde(m['kesinlik'])} | "
                            f"{_yuzde(m['duyarlilik'])} | {_yuzde(m['F1'])} | {_yuzde(m['dogruluk'])} |")
    satirlar += [f"\nD3 Kategoriye uygunluk — {len(ornekler('D3', kume))} örnek, 7 ana kategori", "",
                 "| Yöntem | Doğruluk | Makro F1 |", "|---|---|---|"]
    for ad, m in sonuc["D3"].items():
        satirlar.append(f"| {ad} | {_yuzde(m['dogruluk'])} | {_yuzde(m['makro_F1'])} |")
    satirlar.append("\nHata analizi (kuralın yanıldığı örnekler):")
    for madde, liste in hatalar.items():
        for metin, gercek, tahmin in liste:
            satirlar.append(f"  {madde}  beklenen={gercek:<16} kural={tahmin:<16} {metin}")
    return "\n".join(satirlar)


if __name__ == "__main__":
    print("\n\n".join(rapor(k) for k in KUMELER))
