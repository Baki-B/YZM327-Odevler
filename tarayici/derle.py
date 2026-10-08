"""Agora'nın tarayıcı sürümünü (GitHub Pages sitesi) üretir.

    python tarayici/derle.py                 # _site/ klasörüne
    python tarayici/derle.py --cikti site --pyodide-arsivi pyodide-core-0.29.4.tar.bz2 --paket-klasoru paketler/

Ortaya çıkan klasör yalnızca statik dosyalardan oluşur; herhangi bir statik sunucudan (GitHub Pages, `python -m http.server`)
sunulabilir. İçinde:
  index.html, kabuk.js, isci.js, sw.js, kopru.py   kabuk sayfası, Python işçisi, service worker, Flask köprüsü
  pyodide/        WebAssembly Python (Pyodide) ve gereken üç paketi (sqlite3, hashlib, markupsafe): siteyle birlikte sunulur,
                  çalışma anında başka bir CDN'e bağımlılık yoktur
  tekerlekler.zip Flask ve bağımlılıkları (saf Python)
  forum.zip       uygulamanın kendisi (forum/ paketi; şablonlar ve şema dahil)
  app/static/     CSS, JS, simgeler (uygulamanın sayfaları bunları bu adresten ister)
  surum.json      sürüm (önbellek yenileme)

Tedarik zinciri: indirilen her dosyanın SHA-256 özeti doğrulanır (Pyodide arşivi burada sabit; paketler arşivdeki
pyodide-lock.json'dan; Python paketleri tarayici/gereksinimler.txt'den). Biri uymazsa derleme durur.
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KAYNAK = KOK / "tarayici"
PYODIDE_SURUMU = "0.29.4"
PYODIDE_ARSIVI = f"https://github.com/pyodide/pyodide/releases/download/{PYODIDE_SURUMU}/pyodide-core-{PYODIDE_SURUMU}.tar.bz2"
PYODIDE_ARSIV_OZETI = "5304510cb0e4b5cfce57b410451c3fd2fba96177e3d0b8a31da9ad7a0620bff6"
PYODIDE_PAKETLERI = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_SURUMU}/full/"
CEKIRDEK_DOSYALARI = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")
GEREKEN_PAKETLER = ("sqlite3", "hashlib", "markupsafe")     # bağımlılıkları (libopenssl) kilit dosyasından eklenir
KABUK_DOSYALARI = ("index.html", "kabuk.js", "isci.js", "sw.js", "kopru.py", "manifest.webmanifest")


def ozet(veri):
    return hashlib.sha256(veri).hexdigest()


def indir(adres):
    print(f"  indiriliyor: {adres}")
    with urllib.request.urlopen(adres, timeout=120) as y:
        return y.read()


def dogrula(ad, veri, beklenen):
    if ozet(veri) != beklenen:
        raise SystemExit(f"HATA: {ad} özeti uyuşmuyor (beklenen {beklenen}, gelen {ozet(veri)}). Derleme durduruldu.")


def pyodide_kur(hedef, arsiv_yolu, paket_klasoru):
    arsiv = Path(arsiv_yolu).read_bytes() if arsiv_yolu else indir(PYODIDE_ARSIVI)
    dogrula("Pyodide arşivi", arsiv, PYODIDE_ARSIV_OZETI)
    hedef.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(arsiv), mode="r:bz2") as tar:
        for ad in CEKIRDEK_DOSYALARI:
            (hedef / ad).write_bytes(tar.extractfile(f"pyodide/{ad}").read())
    kilit = json.loads((hedef / "pyodide-lock.json").read_text(encoding="utf-8"))["packages"]
    gerekenler, bekleyen = set(), list(GEREKEN_PAKETLER)
    while bekleyen:
        ad = bekleyen.pop()
        if ad not in gerekenler:
            gerekenler.add(ad)
            bekleyen.extend(kilit[ad].get("depends", []))
    for ad in sorted(gerekenler):
        dosya, beklenen = kilit[ad]["file_name"], kilit[ad]["sha256"]
        yerel = Path(paket_klasoru) / dosya if paket_klasoru else None
        veri = yerel.read_bytes() if yerel and yerel.exists() else indir(PYODIDE_PAKETLERI + dosya)
        dogrula(dosya, veri, beklenen)
        (hedef / dosya).write_bytes(veri)


def tekerlekler_zip(hedef, tekerlek_klasoru):
    """Flask ve bağımlılıklarının tekerlek (wheel) dosyalarını tek bir zip'te birleştirir: işçi bunu site-packages'a açar."""
    with tempfile.TemporaryDirectory() as gecici:
        if tekerlek_klasoru:
            kaynak = Path(tekerlek_klasoru)
        else:
            kaynak = Path(gecici)
            subprocess.run([sys.executable, "-m", "pip", "download", "--quiet", "--only-binary=:all:", "--no-deps",
                            "--require-hashes", "-r", str(KAYNAK / "gereksinimler.txt"), "-d", str(kaynak)], check=True)
        beklenen = {}
        for satir in (KAYNAK / "gereksinimler.txt").read_text(encoding="utf-8").splitlines():
            if satir.strip() and not satir.startswith("#"):
                paket, ozet_ = satir.split()[0], satir.split("--hash=sha256:")[1].strip()
                beklenen[paket.split("==")[0].lower() + "-" + paket.split("==")[1]] = ozet_
        with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as cikis:
            for anahtar, ozet_ in sorted(beklenen.items()):
                dosya = next(kaynak.glob(f"{anahtar}-*.whl"), None)
                if dosya is None:
                    raise SystemExit(f"HATA: {anahtar} tekerleği bulunamadı.")
                veri = dosya.read_bytes()
                dogrula(dosya.name, veri, ozet_)
                with zipfile.ZipFile(io.BytesIO(veri)) as tekerlek:
                    for bilgi in tekerlek.infolist():
                        cikis.writestr(bilgi.filename, tekerlek.read(bilgi))


def forum_zip(hedef):
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as cikis:
        for yol in sorted((KOK / "forum").rglob("*")):
            goreli = yol.relative_to(KOK)
            if yol.is_dir() or "__pycache__" in goreli.parts or goreli.parts[1] == "static":
                continue
            cikis.write(yol, goreli.as_posix())


def surum_bilgisi():
    surum = os.environ.get("GITHUB_SHA", "")[:12]
    if not surum:
        try:
            surum = subprocess.run(["git", "-C", str(KOK), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                                   text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            surum = "yerel"
    return surum + "-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")


def main():
    ayr = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ayr.add_argument("--cikti", default=str(KOK / "_site"))
    ayr.add_argument("--pyodide-arsivi", help="önceden indirilmiş pyodide-core arşivi (yoksa GitHub'dan indirilir)")
    ayr.add_argument("--paket-klasoru", help="Pyodide paketlerinin bulunduğu klasör (yoksa Pyodide CDN'inden indirilir)")
    ayr.add_argument("--tekerlek-klasoru", help="Flask tekerleklerinin bulunduğu klasör (yoksa pip ile indirilir)")
    a = ayr.parse_args()

    cikti = Path(a.cikti).resolve()
    if cikti.exists():
        shutil.rmtree(cikti)
    cikti.mkdir(parents=True)
    surum = surum_bilgisi()
    print(f"Agora tarayıcı sürümü derleniyor → {cikti}  (sürüm {surum})")

    for ad in KABUK_DOSYALARI:
        icerik = (KAYNAK / ad).read_text(encoding="utf-8")
        (cikti / ad).write_text(icerik.replace("__SURUM__", surum), encoding="utf-8")
    shutil.copytree(KOK / "forum" / "static", cikti / "app" / "static")
    print("  Pyodide hazırlanıyor")
    pyodide_kur(cikti / "pyodide", a.pyodide_arsivi, a.paket_klasoru)
    print("  Python paketleri hazırlanıyor")
    tekerlekler_zip(cikti / "tekerlekler.zip", a.tekerlek_klasoru)
    forum_zip(cikti / "forum.zip")
    (cikti / "surum.json").write_text(json.dumps({"surum": surum, "pyodide": PYODIDE_SURUMU}), encoding="utf-8")
    (cikti / ".nojekyll").write_text("", encoding="utf-8")       # GitHub Pages dosyaları Jekyll'den geçirmesin
    boyut = sum(p.stat().st_size for p in cikti.rglob("*") if p.is_file())
    print(f"Tamam: {sum(1 for p in cikti.rglob('*') if p.is_file())} dosya, {boyut / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
