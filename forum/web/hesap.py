from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .. import kullanicilar, ontoloji
from ..hatalar import KuralHatasi
from ..metin import site_ici_yol_mu
from . import db_al

bp = Blueprint("hesap", __name__)


def _konum_verisi(db):
    return {"iller": ontoloji.il_listesi(db), "ilceler": ontoloji.ilce_haritasi(db)}


def _guvenli_adres(adres):
    """Girişten sonra dönülecek adres. `sonra` uygulama içi yoldur ("/konu/3"); uygulama bir alt yolda çalışıyorsa
    (GitHub Pages: /YZM327-Odevler/app) önek eklenir."""
    return request.script_root + adres if site_ici_yol_mu(adres) else url_for("konular.ana_sayfa")


def _oturum_ac(kullanici):
    """Oturum, hesabın oturum sürümünü de taşır: şifre değişince sürüm artar ve eski çerezler geçersiz olur."""
    session.clear()
    session.permanent = True
    session["kullanici_id"], session["surum"] = kullanici["id"], kullanici["oturum_surumu"]


@bp.route("/kayit", methods=["GET", "POST"])
def kayit():
    db = db_al()
    if request.method == "POST":
        f = request.form
        try:
            kullanici_id, kod = kullanicilar.kayit(db, f.get("ad_soyad"), f.get("takma_ad"), f.get("sifre"),
                                                   f.get("sifre_tekrar"), f.get("dogum_tarihi"),
                                                   f.get("ilce_id") or f.get("il_id"), istemci=request.remote_addr or "")
        except KuralHatasi as e:
            db.rollback()
            flash(str(e), "hata")
            return render_template("kayit.html", form=f, **_konum_verisi(db))
        db.commit()
        _oturum_ac(kullanicilar.getir(db, kullanici_id))
        session["yeni_kurtarma"] = kod
        return redirect(url_for("hesap.kurtarma_kodu"))
    return render_template("kayit.html", form={}, **_konum_verisi(db))


@bp.get("/kurtarma-kodu")
def kurtarma_kodu():
    kod = session.pop("yeni_kurtarma", None)
    if not kod:
        return redirect(url_for("konular.ana_sayfa"))
    return render_template("kurtarma_kodu.html", kod=kod)


@bp.route("/giris", methods=["GET", "POST"])
def giris():
    sonra = request.values.get("sonra")
    if request.method == "POST":
        db = db_al()
        try:
            k = kullanicilar.giris(db, request.form.get("takma_ad"), request.form.get("sifre"), request.remote_addr or "")
        except KuralHatasi as e:
            flash(str(e), "hata")
            return render_template("giris.html", sonra=sonra, takma_ad=request.form.get("takma_ad", ""))
        db.commit()
        _oturum_ac(k)
        flash(f"Hoş geldin, @{k['takma_ad']}.", "basari")
        return redirect(_guvenli_adres(sonra))
    return render_template("giris.html", sonra=sonra, takma_ad="")


@bp.post("/cikis")
def cikis():
    session.clear()
    flash("Çıkış yaptın.", "bilgi")
    return redirect(url_for("konular.ana_sayfa"))


@bp.route("/sifremi-unuttum", methods=["GET", "POST"])
def sifremi_unuttum():
    if request.method == "POST":
        db = db_al()
        f = request.form
        try:
            k, kod = kullanicilar.sifre_sifirla(db, f.get("takma_ad"), f.get("kurtarma_kodu"), f.get("yeni"),
                                                f.get("yeni_tekrar"), request.remote_addr or "")
        except KuralHatasi as e:
            db.rollback()
            flash(str(e), "hata")
            return render_template("sifremi_unuttum.html", takma_ad=f.get("takma_ad", ""))
        db.commit()
        _oturum_ac(kullanicilar.getir(db, k["id"]))
        session["yeni_kurtarma"] = kod
        flash("Şifren değişti. Eski kurtarma kodun artık geçersiz; yenisini sakla.", "basari")
        return redirect(url_for("hesap.kurtarma_kodu"))
    return render_template("sifremi_unuttum.html", takma_ad="")
