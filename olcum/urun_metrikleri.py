"""İş, ürün ve koruyucu metrikler: herhangi bir Agora veritabanından hesaplanır.

Çalıştırmak için:  python olcum/urun_metrikleri.py [veritabanı yolu]
(Yol verilmezse geçici bir klasöre demo verisi yüklenip onun üzerinde hesaplanır. Demo verisi elle kurulmuş bir
senaryodur; çıkan sayılar ölçümün çalıştığını gösterir, forumun gerçek başarımını değil.)

Metriklerin tanımı ve hedefleri docs/analiz.md'nin 5. kutusundadır. Ders slaytı (Hafta 2): iş metriği, ürün metriği ve
koruyucu (guardrail) metrik birbirine bağlanmalı; tek bir ölçüt hedef yapılırsa bozulur (Goodhart).
"""
import json
import os
import statistics
import sys
import tempfile

KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(KLASOR))

from forum import defter, graf, guvenlik, ontoloji, ornek_veri, veritabani, yonetmelik, zaman  # noqa: E402

YANIT_TURLERI = ("ARGUMAN", "KARSI_ARGUMAN", "SORU", "KAYNAK")


def _oran(pay, payda):
    return pay / payda if payda else None


def metrikler(db):
    kapali = db.execute("""SELECT durum, COUNT(*) FROM konular WHERE silindi = 0
                           AND durum IN ('KARARA_BAGLANDI', 'SONUCSUZ') GROUP BY durum""").fetchall()
    kapali = {r[0]: r[1] for r in kapali}
    karar = kapali.get("KARARA_BAGLANDI", 0)
    itiraz_edilen = db.execute("""SELECT COUNT(DISTINCT itiraz_id) FROM konular WHERE itiraz_id IS NOT NULL
                                  AND silindi = 0""").fetchone()[0]
    sureler = [(zaman.coz(r["kabul_tarihi"]) - zaman.coz(r["olusturma"])).total_seconds() / 3600 for r in db.execute(
        "SELECT olusturma, kabul_tarihi FROM konular WHERE durum = 'KARARA_BAGLANDI' AND kabul_tarihi IS NOT NULL")]
    sonuclar = [json.loads(r["sonuc"]) for r in db.execute(
        "SELECT sonuc FROM teklifler WHERE tip = 'KARAR' AND durum != 'ACIK' AND sonuc IS NOT NULL")]
    sonuclar = [s for s in sonuclar if s.get("hak_sahibi")]
    fikir = db.execute("SELECT COUNT(*) FROM mesajlar WHERE tip = 'FIKIR' AND gizli = 0").fetchone()[0]
    yanit = db.execute(f"""SELECT COUNT(*) FROM mesajlar WHERE gizli = 0
                           AND tip IN ({','.join('?' * len(YANIT_TURLERI))})""", YANIT_TURLERI).fetchone()[0]
    mesaj = db.execute("SELECT COUNT(*) FROM mesajlar WHERE tip != 'SISTEM'").fetchone()[0]
    yz_mesaj = db.execute("SELECT COUNT(*) FROM mesajlar WHERE tip = 'YZ'").fetchone()[0]
    gizli = db.execute("SELECT COUNT(*) FROM mesajlar WHERE gizli = 1").fetchone()[0]
    g = graf.ozet(db)
    guc = graf.oy_gucleri(db)
    tutarlilik = defter.tutarlilik(db)
    return {
        "is": {
            "Karara bağlanma oranı (kapanan konular)": _oran(karar, karar + kapali.get("SONUCSUZ", 0)),
            "İtiraz konusu açılan kararların oranı": _oran(itiraz_edilen, karar),
        },
        "urun": {
            "Açılıştan karara medyan süre (saat)": statistics.median(sureler) if sureler else None,
            "Fikir oylamalarında ortalama katılım (katılan / hak sahibi)":
                statistics.mean(s["katilan"] / s["hak_sahibi"] for s in sonuclar) if sonuclar else None,
            "Yeter sayıya ulaşamayan tur oranı": _oran(sum(not s.get("yeter") for s in sonuclar), len(sonuclar)),
            "Fikir başına yanıt (argüman, karşı argüman, soru, kaynak)": _oran(yanit, fikir),
        },
        "koruyucu": {
            "Oy gücü Gini katsayısı (0 = eşit)": g["gini"],
            "En güçlü üyenin oy gücü payı": _oran(max(guc.values(), default=0), sum(guc.values())),
            "Defter–veritabanı tutarsızlığı (adet)": len(tutarlilik["sorunlar"]),
            "Yapay zeka mesajlarının payı": _oran(yz_mesaj, mesaj),
            "Gizlenen mesaj oranı": _oran(gizli, mesaj),
        },
    }


def _bicim(deger):
    if deger is None:
        return "—"
    if isinstance(deger, int):
        return str(deger)
    return f"{deger:.2f}".replace(".", ",")


def rapor(db):
    satirlar = ["| Katman | Metrik | Değer |", "|---|---|---|"]
    m = metrikler(db)
    for katman, ad in (("is", "İş"), ("urun", "Ürün"), ("koruyucu", "Koruyucu")):
        for metrik, deger in m[katman].items():
            satirlar.append(f"| {ad} | {metrik} | {_bicim(deger)} |")
    return "\n".join(satirlar)


def _demo_veritabani(klasor):
    yol = os.path.join(klasor, "demo.db")
    guvenlik.SIFRE_YONTEMI = "pbkdf2:sha256:1"
    db = veritabani.hazirla(yol)
    ontoloji.yukle(db)
    yonetmelik.yukle(db)
    db.commit()
    db.close()
    ornek_veri.gerekirse_yukle(yol)
    return yol


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as gecici:
        yol = sys.argv[1] if len(sys.argv) > 1 else _demo_veritabani(gecici)
        db = veritabani.baglan(yol)
        try:
            print(rapor(db))
        finally:
            db.close()
