"""S02-50 mini laboratuvar, 4. görev: bir YZ kodlama aracının önerdiği her import'un gerçekten var olup olmadığını doğrular.

    python laboratuvar/import_dogrula.py [dosya.py] [--pypi]

Ders slaytı (S02-47): kodlama asistanları var olmayan paket adları uydurabilir ("slopsquatting"); saldırgan o adla zararlı
bir paket yayımlarsa `pip install` onu kurar. Bu yüzden önerilen her import üç düzeyde denetlenir:
  1. Paket: `# pip install X` yorumundaki X, PyPI'da var mı (--pypi; https://pypi.org/pypi/X/json)?
  2. Modül: import edilen modül kurulu mu ve hangi dağıtım (distribution) onu sağlıyor? Önerilen paket adıyla aynı mı?
  3. Ad: `from M import A` ve kodda kullanılan `M.A` gerçekten var mı (hasattr)?
2 ve 3 için önerilen paketlerin kurulu olması gerekir (ayrı bir sanal ortam önerilir). Denetim kodu çalıştırmaz,
yalnızca modülleri yükler; tanımadığınız bir paketi kurmadan önce 1. adımın çıktısına (sürüm, tarih) bakın.
"""
import ast
import importlib
import importlib.metadata
import importlib.util
import json
import os
import re
import sys
import urllib.request

VARSAYILAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yz_onerisi.py")


def importlar(kaynak):
    """Döner: [(satır, modül, ad ya da None, takma ad)]"""
    sonuc = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if isinstance(dugum, ast.Import):
            sonuc += [(dugum.lineno, a.name, None, a.asname or a.name.split(".")[0]) for a in dugum.names]
        elif isinstance(dugum, ast.ImportFrom) and dugum.level == 0:
            sonuc += [(dugum.lineno, dugum.module, a.name, a.asname or a.name) for a in dugum.names]
    return sorted(sonuc)


def kullanilan_oznitelikler(kaynak, takma_adlar):
    """Kodda `takma_ad.oznitelik` biçiminde kullanılan adlar: {takma_ad: {oznitelik}}"""
    sonuc = {}
    for dugum in ast.walk(ast.parse(kaynak)):
        if isinstance(dugum, ast.Attribute) and isinstance(dugum.value, ast.Name) and dugum.value.id in takma_adlar:
            sonuc.setdefault(dugum.value.id, set()).add(dugum.attr)
    return sonuc


def pip_onerileri(kaynak):
    return sorted({p for satir in re.findall(r"#\s*pip install ([^\n]+)", kaynak) for p in satir.split()})


def pypi(paket):
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{paket}/json", timeout=20) as y:
            veri = json.load(y)
    except urllib.error.HTTPError as hata:
        return None if hata.code == 404 else f"denetlenemedi ({hata.code})"
    except OSError as hata:
        return f"denetlenemedi ({hata.__class__.__name__})"
    surum = veri["info"]["version"]
    dosyalar = veri["releases"].get(surum) or [{}]
    return f"var (son sürüm {surum}, {dosyalar[0].get('upload_time', '?')[:10]})"


def modul_denetimi(modul, adlar):
    """Döner: (durum, sağlayan dağıtımlar, eksik adlar)"""
    kok = modul.split(".")[0]
    if kok in sys.stdlib_module_names:
        durum = "standart kütüphane"
    elif importlib.util.find_spec(kok) is None:
        return "KURULU DEĞİL", [], sorted(adlar)
    else:
        durum = "kurulu"
    try:
        nesne = importlib.import_module(modul)
    except Exception as hata:                              # noqa: BLE001 — her yükleme hatası rapora yazılır
        return f"yüklenemedi: {hata.__class__.__name__}: {hata}", [], sorted(adlar)
    eksik = sorted(a for a in adlar if not hasattr(nesne, a))
    saglayan = importlib.metadata.packages_distributions().get(kok, [])
    return durum, saglayan, eksik


def main():
    argumanlar = [a for a in sys.argv[1:] if not a.startswith("--")]
    yol = argumanlar[0] if argumanlar else VARSAYILAN
    kaynak = open(yol, encoding="utf-8").read()
    liste = importlar(kaynak)
    oznitelik = kullanilan_oznitelikler(kaynak, {takma for _, _, ad, takma in liste if ad is None})
    oneriler = pip_onerileri(kaynak)

    print(f"Dosya: {os.path.relpath(yol)}\n")
    if "--pypi" in sys.argv:
        print("1) Önerilen paketler PyPI'da:")
        for p in oneriler:
            print(f"   {p:<14} {pypi(p) or 'YOK — uydurma paket adı!'}")
        print()
    print("2-3) İmport'lar:")
    print("| Satır | İmport | Durum | Sağlayan dağıtım | Önerilen pip adıyla aynı mı | Bulunamayan ad |")
    print("|---|---|---|---|---|---|")
    for satir, modul, ad, takma in liste:
        adlar = {ad} if ad else oznitelik.get(takma, set())
        durum, saglayan, eksik = modul_denetimi(modul, adlar)
        yazilis = f"from {modul} import {ad}" if ad else f"import {modul}" + (f" as {takma}" if takma != modul else "")
        if durum == "standart kütüphane":
            uyum = "—"
        elif saglayan:
            uyum = "evet" if {s.lower() for s in saglayan} & {o.lower() for o in oneriler} else "HAYIR"
        else:
            uyum = "?"
        print(f"| {satir} | `{yazilis}` | {durum} | {', '.join(saglayan) or '—'} | {uyum} | "
              f"{', '.join(eksik) or 'yok'} |")


if __name__ == "__main__":
    main()
