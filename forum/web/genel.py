from flask import (Blueprint, current_app, flash, g, redirect, render_template, request, send_from_directory, url_for)

from .. import arama, ayarlar, defter, graf, gunluk, oylama, yonetmelik
from ..hatalar import KuralHatasi
from . import db_al, giris_gerekli, sayfa_no
from .yardimcilar import sayfa_bilgisi, sayfala

bp = Blueprint("genel", __name__)


# --- Yönetmelik ---

@bp.get("/yonetmelik")
def yonetmelik_sayfasi():
    db = db_al()
    maddeler = yonetmelik.maddeler(db)
    acik = [t for t in db.execute("SELECT * FROM teklifler WHERE tip = 'YONETMELIK' ORDER BY id DESC LIMIT 20")]
    return render_template("yonetmelik.html",
                           gruplar=[(tur, ad, [m for m in maddeler if m["tur"] == tur])
                                    for tur, ad in yonetmelik.MADDE_TURLERI.items()],
                           parametreler=yonetmelik.parametre_listesi(db), teklifler=acik,
                           basliklar={t["id"]: oylama.teklif_basligi(db, t) for t in acik},
                           denetim_maddeleri=[m for m in maddeler if m["tur"] == "DENETIM"],
                           ciddiyetler=yonetmelik.CIDDIYETLER, tipler=ayarlar.TEKLIF_TIPLERI)


@bp.post("/yonetmelik/teklif")
@giris_gerekli
def yonetmelik_teklif():
    db = db_al()
    f = request.form
    tur = f.get("tur")
    if tur == "PARAMETRE":
        veri = {"tur": tur, "kod": f.get("kod"), "yeni": f.get("yeni")}
    elif tur == "DENETIM":
        veri = {"tur": tur, "kod": f.get("madde"), "yeni": f.get("ciddiyet")}
    else:
        veri = {"tur": "BEYAN", "baslik": f.get("baslik"), "metin": f.get("metin")}
    teklif_id = yonetmelik.degisiklik_teklif_et(db, g.kullanici, veri, f.get("gerekce"))
    db.commit()
    flash("Yönetmelik değişikliği oylamaya açıldı.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


# --- Dağıtık defter ---

@bp.get("/defter")
def defter_sayfasi():
    db = db_al()
    tur = request.args.get("tur") or None
    sayfa = sayfa_no()
    bloklar, toplam = defter.bloklar(db.defter_klasoru, sayfa, 20, tur)
    aranan = request.args.get("blok", "").strip()
    return render_template("defter.html", durum=defter.durum(db.defter_klasoru), bloklar=bloklar,
                           sayfalama=sayfa_bilgisi(toplam, sayfa, 20), tur=tur,
                           turler=["KONU", "KONU_DUZENLEME", "KONU_DURUM", "MESAJ", "MESAJ_DUZENLEME", "GIZLEME", "TEKLIF",
                                   "OY", "SONUC", "KARAR", "DEVIR", "UYE", "UZMANLIK", "YONETIM"],
                           aranan=aranan, bulunan=defter.blok_bul(db.defter_klasoru, aranan) if aranan else None,
                           tutarlilik=defter.tutarlilik(db) if request.args.get("denetle") else None)


@bp.post("/defter/makbuz")
def makbuz_dogrula():
    db = db_al()
    teklif_id = request.form.get("teklif", type=int)
    makbuz = (request.form.get("makbuz") or "").strip().upper()
    try:
        t = oylama.teklif_getir(db, teklif_id)
    except KuralHatasi:
        flash("Oylama bulunamadı.", "hata")
        return redirect(url_for("genel.defter_sayfasi"))
    bulunan = defter.makbuz_dogrula(db.defter_klasoru, teklif_id, makbuz, oylama.secim_anahtarlari(db, t))
    if bulunan:
        blok, secim = bulunan
        flash(f"Oyun defterde kayıtlı: blok #{blok['no']} ({blok['hash'][:16]}…). Seçimin: "
              f"“{_secim_metni(db, t, secim)}”. Bu bilgiyi sadece makbuz sahibi görebilir.", "basari")
    else:
        flash("Bu makbuzla eşleşen bir oy bulunamadı (oyunu sonradan değiştirdiysen yeni makbuzu kullan).", "hata")
    return redirect(url_for("genel.defter_sayfasi"))


def _secim_metni(db, t, secim):
    if t["tip"] == "KARAR" and secim != oylama.CEKIMSER:
        r = db.execute("SELECT metin FROM secenekler WHERE id = ?", (int(secim),)).fetchone()
        return r["metin"] if r else secim
    return ayarlar.SECIM_ADLARI.get(secim, secim)


# --- Graf, arama, günlük ---

@bp.get("/graf")
def graf_sayfasi():
    return render_template("graf.html", ozet=graf.ozet(db_al()))


@bp.get("/ara")
def ara():
    q = request.args.get("q", "").strip()
    return render_template("arama.html", q=q, sonuclar=arama.ara(db_al(), q) if q else [])


@bp.get("/gunluk")
def gunluk_sayfasi():
    kayitlar, sayfalama = sayfala(gunluk.son_kayitlar(db_al(), 1000), sayfa_no(), 40)
    return render_template("gunluk.html", kayitlar=kayitlar, sayfalama=sayfalama)


# --- Bilgi sayfaları ve uygulama (PWA) ---

@bp.get("/hakkinda")
def hakkinda():
    db = db_al()
    return render_template("hakkinda.html", tipler=ayarlar.TEKLIF_TIPLERI, parametreler=yonetmelik.parametre_listesi(db))


@bp.get("/api-belgeleri")
def api_belgeleri():
    return render_template("api_belgeleri.html")


@bp.get("/cevrimdisi")
def cevrimdisi():
    return render_template("cevrimdisi.html")


@bp.get("/manifest.webmanifest")
def manifest():
    return send_from_directory(current_app.static_folder, "manifest.webmanifest",
                               mimetype="application/manifest+json")


@bp.get("/sw.js")
def service_worker():
    yanit = send_from_directory(current_app.static_folder, "sw.js", mimetype="application/javascript")
    yanit.headers["Service-Worker-Allowed"] = "/"
    yanit.headers["Cache-Control"] = "no-cache"
    return yanit
