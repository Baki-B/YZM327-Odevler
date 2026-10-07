"""Forumu başlatır ve tarayıcıda açar:  python calistir.py

Seçenekler:
  --sifirla        veritabanını ve dağıtık defteri silip demo verisini yeniden yükler
  --port 5050      farklı bir port kullanır (varsayılan 5000; doluysa sıradaki boş port seçilir)
  --ag             aynı Wi-Fi'daki telefonlardan erişim için ağa açar (0.0.0.0)
  --tarayici-acma  tarayıcıyı otomatik açmaz
  --yonetici AD    takma adı verilen üyeyi yönetici yapar (ilk yöneticiyi atamak için; sonrası yönetim panelinden)
  --demo           sunum kipi: yönetim panelinde "süreyi ilerlet" düğmeleri açılır (24/48 saat beklememek için).
                   Normalde yönetici sürelere ve oylamalara dokunamaz.
  --demo-verisiz   boş veritabanına demo verisini (ve şifresi herkesçe bilinen demo hesaplarını) yüklemez

Ortam değişkenleri: FORUM_VERITABANI (veritabanı yolu), FORUM_GIZLI_ANAHTAR (oturum anahtarı),
FORUM_HTTPS=1 (HTTPS arkasında yayınlanıyorsa güvenli çerez), FORUM_ANLIK_ILETISIM (Web Push iletişim adresi).
"""
import glob
import os
import shutil
import socket
import sys
import threading
import webbrowser

KLASOR = os.path.dirname(os.path.abspath(__file__))
INSTANCE = os.path.join(KLASOR, "instance")
VERITABANI = os.environ.get("FORUM_VERITABANI") or os.path.join(INSTANCE, "forum.db")


def _secenek(ad, varsayilan):
    if ad in sys.argv and sys.argv.index(ad) + 1 < len(sys.argv):
        return sys.argv[sys.argv.index(ad) + 1]
    return varsayilan


def _port_dolu_mu(port):
    """Windows aynı porta iki sunucunun bağlanmasına izin verebiliyor; önceden kontrol ediyoruz."""
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _bos_port(baslangic):
    for port in range(baslangic, baslangic + 20):
        if not _port_dolu_mu(port):
            return port
    raise SystemExit(f"{baslangic}–{baslangic + 19} arasında boş port bulunamadı.")


def _yerel_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "bilgisayarın-ip-adresi"


def _yonetici_yap(takma_ad):
    from forum import gunluk, kullanicilar, veritabani
    db = veritabani.baglan(app.config["VERITABANI"])
    k = kullanicilar.takma_ad_ile(db, takma_ad)
    if not k or k["yz_mi"]:
        raise SystemExit(f"@{takma_ad} adında bir üye bulunamadı.")
    db.execute("UPDATE kullanicilar SET yonetici_mi = 1 WHERE id = ?", (k["id"],))
    gunluk.kaydet(db, None, "YETKI", f"@{k['takma_ad']} sunucu komutuyla yönetici yapıldı")
    db.commit()
    db.close()
    print(f"@{k['takma_ad']} artık yönetici.")


if "--sifirla" in sys.argv:
    for yol in glob.glob(VERITABANI + "*"):          # FORUM_VERITABANI verilmişse o dosya ve onun defteri silinir
        os.remove(yol)
    shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(VERITABANI)), "defter"), ignore_errors=True)
    print("Veritabanı ve defter silindi; demo verisi yeniden yüklenecek.")

from forum import create_app, gorevler, ornek_veri  # noqa: E402

# Bir WSGI sunucusu bu modülü içe aktarırsa zamanlayıcı hemen başlar; doğrudan çalıştırılınca demo verisi
# yüklendikten SONRA başlar (yükleme sırasında saat geçici olarak geriye alınır, zamanlayıcı bunu görmemeli).
app = create_app({"ZAMANLAYICI": __name__ != "__main__", "DEMO": "--demo" in sys.argv,
                  "VERITABANI": VERITABANI})

if __name__ == "__main__":
    istenen = int(_secenek("--port", 5000))
    port = _bos_port(istenen)
    if port != istenen:
        print(f"UYARI: {istenen} portunu başka bir program kullanıyor; forum {port} portunda açılacak.")
    if "--demo-verisiz" not in sys.argv and ornek_veri.gerekirse_yukle(app.config["VERITABANI"]):
        print(f"Demo verisi yüklendi (bütün demo hesaplarının şifresi: {ornek_veri.SIFRE}).")
    if "--yonetici" in sys.argv:
        _yonetici_yap(_secenek("--yonetici", ""))
    gorevler.arka_plan_baslat(app.config["VERITABANI"])

    from forum import ayarlar
    ag = "--ag" in sys.argv
    if ag and ornek_veri.demo_hesabi_var_mi(app.config["VERITABANI"]):
        print("  UYARI: Demo hesaplarının şifresi herkesçe biliniyor ve forum ağa açık. Gerçek kullanımda önce "
              "'yonetici' hesabının şifresini değiştir ya da --sifirla --demo-verisiz ile boş başlat.")
    adres = f"http://127.0.0.1:{port}"
    print(f"\n  {ayarlar.SITE_ADI} çalışıyor:  {adres}")
    if ag:
        print(f"  Telefondan (aynı Wi-Fi):  http://{_yerel_ip()}:{port}")
    if app.config["DEMO"]:
        print("  Sunum kipi AÇIK: yönetim panelinde 'süreyi ilerlet' düğmeleri görünür.")
    print("  Tarayıcı açılmazsa adresi kopyalayıp tarayıcına yapıştır.")
    print("  Bu pencereyi KAPATMA; kapatırsan forum da kapanır. Durdurmak için Ctrl+C.\n")
    if "--tarayici-acma" not in sys.argv:
        threading.Timer(1.2, webbrowser.open, args=(adres,)).start()
    app.run(host="0.0.0.0" if ag else "127.0.0.1", port=port, debug=False, threaded=True)
