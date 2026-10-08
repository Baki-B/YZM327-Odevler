"""S01-49 uygulamalı soru 6: "Bir YZ kodlama aracına küçük bir fonksiyon ve testlerini ürettirin. Testlerden kaç tanesi
gerçekten doğruydu?"

    python laboratuvar/test_dogrulugu.py

yz_testleri/ klasöründe bir YZ kodlama aracının T.C. kimlik numarası denetimi için yazdığı fonksiyon ve 16 test, ilk öneri
olarak değiştirilmeden duruyor. Betik iki soruyu ayrı ayrı yanıtlar:

1. Doğruluk: her testin beklediği sonuç, tanıma göre doğru mu? Kâhin (oracle) olarak YZ'nin kodu değil, forumun kendi
   ve testli `denetim.tc_kimlik_gecerli_mi` işlevi kullanılır; istekteki ek kurallar (değer str olmalı, baştaki/sondaki
   boşluk kırpılır, yalnızca ASCII rakam) onun önüne eklenir. Testin YZ'nin kendi koduyla geçmesi doğruluğun kanıtı
   değildir: kod ve test aynı yanlışı paylaşabilir.
2. Güç: testler hatayı yakalar mı? YZ'nin fonksiyonuna tek tek küçük hatalar (mutant) sokulur; bir mutantı en az bir
   test kırmızıya çeviriyorsa "öldürülmüş" sayılır. Hayatta kalan mutant, testlerin göremediği bir hatadır.
"""
import ast
import os
import sys
import types
import unittest

KLASOR = os.path.dirname(os.path.abspath(__file__))
YZ = os.path.join(KLASOR, "yz_testleri")
sys.path[:0] = [os.path.dirname(KLASOR), YZ]

from forum.denetim import tc_kimlik_gecerli_mi  # noqa: E402

KAYNAK = open(os.path.join(YZ, "tc_kimlik.py"), encoding="utf-8").read()


def kahin(no):
    if not isinstance(no, str):
        return False
    no = no.strip()
    return all(c in "0123456789" for c in no) and tc_kimlik_gecerli_mi(no)


def testlerin_beklentileri():
    """Her test yönteminden (girdi, beklenen) çıkarır: self.assertTrue/False(tc_kimlik_gecerli(<sabit>))."""
    agac = ast.parse(open(os.path.join(YZ, "test_tc_kimlik.py"), encoding="utf-8").read())
    sonuc = {}
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name.startswith("test_"):
            cagri = d.body[0].value
            beklenen = cagri.func.attr == "assertTrue"
            sonuc[d.name] = (ast.literal_eval(cagri.args[0].args[0]), beklenen)
    return sonuc


# Her mutant, kaynağa tek bir küçük değişiklik yapar (gerçekçi hatalar).
MUTANTLAR = {
    "boşluk kırpılmıyor": ("no = no.strip()", "pass"),
    "ilk hane 0 denetimi yok": ('if no[0] == "0":', "if False:"),
    "10. hane denetimi yok": ("if (tek * 7 - cift) % 10 != d[9]:", "if False:"),
    "11. hane denetimi yok": ("if sum(d[:10]) % 10 != d[10]:", "if False:"),
    "çarpan 7 yerine 3": ("tek * 7", "tek * 3"),
    "11. hane için 9 hane toplanıyor": ("sum(d[:10])", "sum(d[:9])"),
    "tek ve çift haneler karışık": ("tek = d[0] + d[2] + d[4] + d[6] + d[8]", "tek = d[1] + d[3] + d[5] + d[7] + d[8]"),
    "Unicode rakam kabul ediliyor": ('if not all(c in "0123456789" for c in no):', "if not no.isdigit():"),
    "uzunluk denetimi gevşek (≥ 11)": ("if len(no) != 11:", "if len(no) < 11:"),
    "str olmayan değer denetimi yok": ("if not isinstance(no, str):", "if False:"),
}


def calistir(kaynak):
    """Testleri verilen kaynakla çalıştırır. Döner: {test adı: geçti mi}"""
    modul = types.ModuleType("tc_kimlik")
    exec(compile(kaynak, "tc_kimlik.py", "exec"), modul.__dict__)
    sys.modules["tc_kimlik"] = modul
    sys.modules.pop("test_tc_kimlik", None)
    import test_tc_kimlik
    sonuc = {}
    for ad in [a for a in dir(test_tc_kimlik.TcKimlikGecerliTest) if a.startswith("test_")]:
        r = unittest.TestResult()
        test_tc_kimlik.TcKimlikGecerliTest(ad).run(r)
        sonuc[ad] = r.wasSuccessful()
    return sonuc


def main():
    beklentiler = testlerin_beklentileri()
    kendi = calistir(KAYNAK)
    dogru = {ad: kahin(girdi) == beklenen for ad, (girdi, beklenen) in beklentiler.items()}
    print(f"1) {len(beklentiler)} test; YZ'nin kendi koduyla geçen: {sum(kendi.values())}; "
          f"beklentisi tanıma göre doğru olan: {sum(dogru.values())}")
    for ad, (girdi, beklenen) in sorted(beklentiler.items()):
        if not dogru[ad]:
            print(f"   YANLIŞ: {ad}: {girdi!r} için {beklenen} bekliyor, doğrusu {kahin(girdi)}")
    print("\n2) Mutasyon testi (hatalı sürümü yakalayan testler):")
    olen = 0
    for ad, (eski, yeni) in MUTANTLAR.items():
        assert KAYNAK.count(eski) == 1, ad
        sonuc = calistir(KAYNAK.replace(eski, yeni))
        yakalayan = sorted(t for t, gecti in sonuc.items() if not gecti)
        olen += bool(yakalayan)
        print(f"   {'öldü' if yakalayan else 'HAYATTA'}  {ad:<34} {len(yakalayan)} test" +
              (f" (ör. {yakalayan[0]})" if yakalayan else ""))
    print(f"   Toplam: {olen}/{len(MUTANTLAR)} mutant yakalandı")
    kullanilmayan = [t for t in beklentiler if not any(not calistir(KAYNAK.replace(*m))[t] for m in MUTANTLAR.values())]
    print(f"\n3) Hiçbir mutantı yakalamayan test: {len(kullanilmayan)} ({', '.join(sorted(kullanilmayan))})")


if __name__ == "__main__":
    main()
