"""Yönetmelik denetiminin (D1 kaba ifade, D2 kişisel veri, D3 kategoriye uygunluk) etiketli örneklerle ölçümü.

Çalıştırmak için:  python olcum/denetim_olcumu.py

Ders slaytı (Hafta 2, "Temel çizgi"): bir sayı, en basit makul çözümle karşılaştırılmadan iyi ya da kötü değildir.
Bu betik kural tabanlı denetimi iki "aptal" temel çizgiyle aynı örnekler üzerinde karşılaştırır:
  * çoğunluk sınıfı: D1/D2 için "hep temiz" (hiçbir şeyi engelleme), D3 için "hep en sık kategori"
  * rastgele: sınıflardan birini eşit olasılıkla seç. Tek bir çekim 10–20 örnekte çok oynak olduğu için
    RASTGELE_TOHUM tohumun ortalaması verilir (beklenen değer; tohumlar sabit, sonuç tekrarlanabilir)
Üç örnek kümesi vardır. Örnekler ve etiketler, kurallar çalıştırılmadan önce yazıldı
(docs/analiz.md 6.2):
  * gelistirme.csv — hata analizi bu kümede yapılır; kurallar bu kümedeki hatalara bakılarak iyileştirilir.
  * test.csv — kurallar değiştirilmeden ÖNCE yazıldı ve kurallar ona bakılarak ayarlanmaz ("test seti kutsaldır").
    Bir iyileştirmenin gerçek etkisi bu kümedeki değişimdir; geliştirme kümesindeki artış iyimserdir.
  * son_test.csv — kurallar dondurulduktan sonra, ölçülmeden önce yazıldı; bir kez ölçüldü
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
RASTGELE_TOHUM = 1000


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
    return {"DP": dp, "YP": yp, "YN": yn, "DN": dn, "kesinlik": p, "duyarlilik": r, "F1": f_beta(p, r, 1),
            "F0,5": f_beta(p, r, 0.5), "F2": f_beta(p, r, 2), "dogruluk": (dp + dn) / len(gercek)}


def f_beta(p, r, beta):
    """beta < 1 kesinliğe, beta > 1 duyarlılığa ağırlık verir (H2-30): D1 için F0,5, D2 için F2."""
    b2 = beta * beta
    return (1 + b2) * p * r / (b2 * p + r) if p + r else 0.0


def ortalama(sozlukler):
    return {k: sum(s[k] for s in sozlukler) / len(sozlukler) for k in sozlukler[0]}


def rastgele_beklenen(gercek, siniflar, olcu):
    """Rastgele temel çizginin RASTGELE_TOHUM tohumdaki ortalaması (tek çekim yerine beklenen değer)."""
    return ortalama([olcu(gercek, [r.choice(siniflar) for _ in gercek])
                     for r in (random.Random(t) for t in range(RASTGELE_TOHUM))])


def makro_f1(gercek, tahmin):
    siniflar = sorted(set(gercek))
    return sum(ikili_metrikler(gercek, tahmin, s)["F1"] for s in siniflar) / len(siniflar)


def cok_sinifli(gercek, tahmin):
    return {"dogruluk": sum(g == t for g, t in zip(gercek, tahmin)) / len(gercek), "makro_F1": makro_f1(gercek, tahmin)}


def karisiklik(gercek, tahmin):
    """Karışıklık matrisi: {gerçek sınıf: Counter(tahmin)}."""
    m = {g: Counter() for g in sorted(set(gercek))}
    for g, t in zip(gercek, tahmin):
        m[g][t] += 1
    return m


def _ana_kategori(db, kategori_id):
    return ontoloji.ad(db, "kategoriler", ontoloji.atalar(db, "kategoriler", kategori_id)[0])


def d3_tahmini(db, metin):
    kid, _ = ontoloji.en_uygun_kategori(db, metin)
    return _ana_kategori(db, kid) if kid else HICBIRI


def olc(kume="gelistirme", ayrinti=False):
    """Döner: {madde: {yöntem: metrikler}} ve hata örnekleri; ayrinti=True ise D3'ün gerçek/tahmin listeleri de."""
    sonuc, hatalar = {}, {}
    kurallar = {"D1": lambda m: VAR if denetim.kaba_ifadeler(m) else YOK,
                "D2": lambda m: VAR if denetim.kisisel_veriler(m) else YOK}
    for madde, kural in kurallar.items():
        satirlar = ornekler(madde, kume)
        gercek = [r["etiket"] for r in satirlar]
        tahmin = [kural(r["metin"]) for r in satirlar]
        sonuc[madde] = {
            "Çoğunluk sınıfı (hep temiz)": ikili_metrikler(gercek, [YOK] * len(gercek)),
            "Rastgele (beklenen)": rastgele_beklenen(gercek, (VAR, YOK), ikili_metrikler),
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
    sonuc["D3"] = {"Çoğunluk sınıfı": cok_sinifli(gercek, [en_sik] * len(gercek)),
                   "Rastgele (beklenen)": rastgele_beklenen(gercek, siniflar, cok_sinifli),
                   "Kural (ontoloji kavramları)": cok_sinifli(gercek, tahmin)}
    hatalar["D3"] = [(r["metin"], g, t) for r, g, t in zip(satirlar, gercek, tahmin) if g != t]
    if ayrinti:
        return sonuc, hatalar, (gercek, tahmin)
    return sonuc, hatalar


def _yuzde(x):
    return f"{x:.2f}".replace(".", ",")


def _adet(x):
    return str(x) if isinstance(x, int) else f"{x:.1f}".replace(".", ",")


def veri_ozeti(kume):
    satirlar = ["| Madde | Örnek | Sınıf dağılımı | Metin uzunluğu (karakter, medyan / en kısa–en uzun) |", "|---|---|---|---|"]
    for madde in ("D1", "D2", "D3"):
        liste = ornekler(madde, kume)
        boylar = sorted(len(r["metin"]) for r in liste)
        dagilim = ", ".join(f"{s} {n}" for s, n in sorted(Counter(r["etiket"] for r in liste).items()))
        satirlar.append(f"| {madde} | {len(liste)} | {dagilim} | {boylar[len(boylar) // 2]} / {boylar[0]}–{boylar[-1]} |")
    return satirlar


def d3_ayrinti(gercek, tahmin):
    """Sınıf bazlı kesinlik/duyarlılık/F1/destek ve karışıklık matrisi (satır gerçek, sütun tahmin)."""
    siniflar = sorted(set(gercek))
    satirlar = ["| Sınıf | Kesinlik | Duyarlılık | F1 | Destek |", "|---|---|---|---|---|"]
    for s in siniflar:
        m = ikili_metrikler(gercek, tahmin, s)
        satirlar.append(f"| {s} | {_yuzde(m['kesinlik'])} | {_yuzde(m['duyarlilik'])} | {_yuzde(m['F1'])} | {m['DP'] + m['YN']} |")
    sutunlar = siniflar + ([HICBIRI] if HICBIRI in tahmin else [])
    matris = karisiklik(gercek, tahmin)
    satirlar += ["", "| Gerçek ↓ / Tahmin → | " + " | ".join(sutunlar) + " |", "|---" * (len(sutunlar) + 1) + "|"]
    for g in siniflar:
        satirlar.append(f"| {g} | " + " | ".join(str(matris[g][t]) if matris[g][t] else "·" for t in sutunlar) + " |")
    return satirlar


def rapor(kume):
    sonuc, hatalar, (d3_gercek, d3_tahmin) = olc(kume, ayrinti=True)
    satirlar = [f"## {kume}.csv", ""] + veri_ozeti(kume)
    for madde, baslik in (("D1", "D1 Saygılı dil (kaba ifade)"), ("D2", "D2 Kişisel veri")):
        liste = ornekler(madde, kume)
        satirlar += [f"\n{baslik} — {len(liste)} örnek, {sum(r['etiket'] == VAR for r in liste)} tanesi VAR", "",
                     "| Yöntem | DP | YP | YN | DN | Kesinlik | Duyarlılık | F1 | F0,5 | F2 | Doğruluk |",
                     "|---|---|---|---|---|---|---|---|---|---|---|"]
        for ad, m in sonuc[madde].items():
            satirlar.append(f"| {ad} | {_adet(m['DP'])} | {_adet(m['YP'])} | {_adet(m['YN'])} | {_adet(m['DN'])} | "
                            f"{_yuzde(m['kesinlik'])} | {_yuzde(m['duyarlilik'])} | {_yuzde(m['F1'])} | "
                            f"{_yuzde(m['F0,5'])} | {_yuzde(m['F2'])} | {_yuzde(m['dogruluk'])} |")
    satirlar += [f"\nD3 Kategoriye uygunluk — {len(ornekler('D3', kume))} örnek, 7 ana kategori", "",
                 "| Yöntem | Doğruluk | Makro F1 |", "|---|---|---|"]
    for ad, m in sonuc["D3"].items():
        satirlar.append(f"| {ad} | {_yuzde(m['dogruluk'])} | {_yuzde(m['makro_F1'])} |")
    satirlar += ["", "D3 kuralı, sınıf bazında:", ""] + d3_ayrinti(d3_gercek, d3_tahmin)
    satirlar.append("\nHata analizi (kuralın yanıldığı örnekler):")
    for madde, liste in hatalar.items():
        for metin, gercek, tahmin in liste:
            satirlar.append(f"  {madde}  beklenen={gercek:<16} kural={tahmin:<16} {metin}")
    return "\n".join(satirlar)


if __name__ == "__main__":
    print("\n\n".join(rapor(k) for k in KUMELER))
