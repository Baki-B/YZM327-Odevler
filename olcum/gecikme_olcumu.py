"""Sayfa gecikmesi ölçümü (p50 / p95 / en kötü), demo verisiyle.

Çalıştırmak için:  python olcum/gecikme_olcumu.py [istek_sayısı] [--defter-blok N] [--konu N]

--konu N: ölçümden önce demo konularının N kopyası eklenir (konu sayısı büyüdükçe konu akışının nasıl yavaşladığını görmek
için; kopyalar mesajsızdır, yalnızca başlık ve açıklamaları vardır).

--defter-blok N: ölçümden önce kayıt defterine N yapay blok eklenir (defter büyüdükçe gecikmenin nasıl değiştiğini
görmek için). Doğrulama önbelleğinden önce her yazma üç zinciri baştan doğruluyordu: 50.000 blokta oy verme p95 ≈ 645 ms,
kayıt defteri sayfası ≈ 1,1 sn idi. Sonuçlar docs/analiz.md'de.

Ders slaytı (S01, "gecikme"): ortalama yanıltır; p95 gibi yüzdelikler izlenir. Hedefler docs/analiz.md'de
(işlevsel olmayan gereksinimler). Ölçüm, geçici bir klasöre demo verisi yükler ve Flask'ın test istemcisiyle istek
atar: ağ ve tarayıcı süresi dahil değildir, yalnızca sunucunun isteği işleme süresi ölçülür. Tek iş parçacığıdır.
Oy verme isteği her seferinde veritabanına ve kayıt defterinin üç düğümüne yazar (commit + defter dahil).
"""
import os
import statistics
import sys
import tempfile
import time

KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(KLASOR))

from forum import create_app, defter, guvenlik, ornek_veri, oylama, veritabani  # noqa: E402

ISINMA = 3


def yuzdelik(degerler, p):
    """En yakın sıra yöntemiyle p. yüzdelik: sıralı listede ⌈p·N/100⌉. sıradaki değer (60 değerde p95 = 57. değer).
    Önceki round(x + 0,5) yazımı Python'un "çifte yuvarlama" kuralı yüzünden bazen bir sonraki sırayı veriyordu."""
    s = sorted(degerler)
    sira = -(-p * len(s) // 100)          # tam sayı tavanı
    return s[min(len(s), max(1, sira)) - 1]


def _defteri_buyut(yol, n):
    klasor = veritabani.defter_klasoru(yol)
    for bas in range(0, n, 5000):
        defter.dugumlere_yaz(klasor, [("MESAJ", '{"mesaj": %d, "ozet": "%s"}' % (i, "0" * 64), "2026-01-02 10:00:00")
                                      for i in range(bas, min(n, bas + 5000))])


def _konulari_cogalt(yol, n):
    db = veritabani.baglan(yol)
    try:
        sutunlar = [r[1] for r in db.execute("PRAGMA table_info(konular)") if r[1] != "id"]
        secim = ", ".join("baslik || ' (kopya ' || :i || ')'" if s == "baslik" else s for s in sutunlar)
        kaynaklar = [r[0] for r in db.execute("SELECT id FROM konular WHERE silindi = 0")]
        for i in range(n):
            db.execute(f"INSERT INTO konular ({', '.join(sutunlar)}) SELECT {secim} FROM konular WHERE id = :k",
                       {"i": i, "k": kaynaklar[i % len(kaynaklar)]})
        db.commit()
    finally:
        db.close()


def _hazirla(klasor, defter_blok=0, konu=0):
    yol = os.path.join(klasor, "olcum.db")
    guvenlik.SIFRE_YONTEMI = "pbkdf2:sha256:1"      # yalnızca demo verisinin yüklenmesini hızlandırır; ölçülmez
    app = create_app({"VERITABANI": yol, "TESTING": True, "SECRET_KEY": "olcum"})
    ornek_veri.gerekirse_yukle(yol)
    _defteri_buyut(yol, defter_blok)
    _konulari_cogalt(yol, konu)
    db = veritabani.baglan(yol)
    try:
        konu = db.execute("""SELECT konu_id FROM mesajlar GROUP BY konu_id ORDER BY COUNT(*) DESC LIMIT 1""").fetchone()[0]
        oy = db.execute("""SELECT o.teklif_id, o.kullanici_id, k.oturum_surumu FROM oylar o
                           JOIN teklifler t ON t.id = o.teklif_id JOIN kullanicilar k ON k.id = o.kullanici_id
                           WHERE t.tip = 'KARAR' AND t.durum = 'ACIK' AND k.yz_mi = 0 ORDER BY o.teklif_id LIMIT 1""").fetchone()
        secimler = oylama.secim_anahtarlari(db, oylama.teklif_getir(db, oy["teklif_id"]))
        mesaj_sayisi = db.execute("SELECT COUNT(*) FROM mesajlar WHERE konu_id = ?", (konu,)).fetchone()[0]
    finally:
        db.close()
    return app, konu, mesaj_sayisi, oy, secimler


def olc(n=60, defter_blok=0, sadece=None, ek_konu=0):
    """sadece: yalnızca adı bu sözcüklerden birini içeren istekler ölçülür."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as klasor:
        app, konu, mesaj_sayisi, oy, secimler = _hazirla(klasor, defter_blok, ek_konu)
        istemci = app.test_client()
        with istemci.session_transaction() as s:
            s["kullanici_id"], s["surum"], s["csrf"] = oy["kullanici_id"], oy["oturum_surumu"], "olcum"
        teklif = oy["teklif_id"]
        istekler = [
            ("Konu akışı", "GET", "/konular"),
            (f"Konu sayfası ({mesaj_sayisi} mesaj)", "GET", f"/konu/{konu}"),
            ("Oylama sayfası", "GET", f"/oylama/{teklif}"),
            ("Gündem", "GET", "/gundem"),
            ("Kayıt defteri", "GET", "/defter"),
            ("Üye ağı (graf)", "GET", "/graf"),
            ("API: konu listesi", "GET", "/api/v1/konular"),
            ("Oy verme (commit + 3 düğüm)", "POST", f"/oylama/{teklif}/oy"),
        ]
        sonuc = []
        for ad, yontem, adres in istekler:
            if sadece and not any(x in ad for x in sadece):
                continue
            sureler, hatalar = [], 0
            for i in range(ISINMA + n):
                bas = time.perf_counter()
                if yontem == "GET":
                    cevap = istemci.get(adres)
                else:
                    cevap = istemci.post(adres, data={"secim": secimler[i % len(secimler)], "csrf": "olcum"})
                sure = (time.perf_counter() - bas) * 1000
                hatalar += cevap.status_code >= 400
                if i >= ISINMA:
                    sureler.append(sure)
            sonuc.append({"ad": ad, "p50": statistics.median(sureler), "p95": yuzdelik(sureler, 95),
                          "en_kotu": max(sureler), "hata": hatalar})
        return sonuc


if __name__ == "__main__":
    argumanlar = sys.argv[1:]

    def secenek(ad):
        if ad not in argumanlar:
            return 0
        i = argumanlar.index(ad)
        deger = int(argumanlar[i + 1])
        del argumanlar[i:i + 2]
        return deger

    blok, ek_konu = secenek("--defter-blok"), secenek("--konu")
    n = int(argumanlar[0]) if argumanlar else 60
    print(f"Her istek {n} kez (önce {ISINMA} ısınma isteği), milisaniye" + (f"; defterde +{blok} blok" if blok else "")
          + (f"; +{ek_konu} konu" if ek_konu else "") + ":\n")
    print("| İstek | p50 | p95 | En kötü | Hatalı yanıt |\n|---|---|---|---|---|")
    for r in olc(n, blok, ek_konu=ek_konu):
        print(f"| {r['ad']} | {r['p50']:.1f} | {r['p95']:.1f} | {r['en_kotu']:.1f} | {r['hata']} |")
