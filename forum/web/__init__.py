"""Web katmanı: iş mantığı modüllerini (forum/*.py) HTTP'ye bağlar.

Kimlik doğrulama iki yoldan olur:
  * Tarayıcı: imzalı oturum çerezi + her POST'ta CSRF anahtarı.
  * Uygulama (API): `Authorization: Bearer <anahtar>` başlığı (CSRF gerekmez, çerez kullanılmaz).
"""
import hmac
import logging
import secrets
from functools import wraps

from flask import (abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for)

from .. import (ayarlar, bildirimler, gorevler, guvenlik, konular, kullanicilar, ontoloji, oylama, sikayetler,
                veritabani, yonetim, yonetmelik, zaman)
from ..hatalar import KuralHatasi
from ..metin import yuzde
from . import ikonlar, yardimcilar

log = logging.getLogger(__name__)


def db_al():
    if "db" not in g:
        g.db = veritabani.baglan(current_app.config["VERITABANI"])
    return g.db


def giris_gerekli(f):
    @wraps(f)
    def sarici(*args, **kwargs):
        if g.kullanici is None:
            if g.get("api"):
                return jsonify(hata="Kimlik doğrulaması gerekli."), 401
            flash("Bu işlem için giriş yapmalısın.", "hata")
            # Girişten sonra yalnızca bir sayfaya (GET) dönülür; POST adresine dönmek 405 verirdi.
            return redirect(url_for("hesap.giris", sonra=request.path if request.method == "GET" else None))
        return f(*args, **kwargs)
    return sarici


def yonetici_gerekli(f):
    @wraps(f)
    def sarici(*args, **kwargs):
        if g.kullanici is None or not g.kullanici["yonetici_mi"]:
            abort(403)
        return f(*args, **kwargs)
    return sarici


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def sayfa_no():
    return request.args.get("sayfa", 1, type=int)


def kur(app):
    @app.before_request
    def istek_oncesi():
        if request.endpoint == "static":
            return
        g.api = request.path.startswith("/api/")
        g.kullanici, g.token = None, False
        db = db_al()
        yetki = request.headers.get("Authorization", "")
        if yetki.startswith("Bearer ") and g.api:           # API anahtarı yalnızca /api/ altında geçerli (en az yetki)
            g.kullanici = guvenlik.api_anahtari_kullanici(db, yetki[7:].strip())
            g.token = True
            if g.kullanici is None:
                return jsonify(hata="Geçersiz API anahtarı."), 401
        elif "kullanici_id" in session:
            k = kullanicilar.getir(db, session["kullanici_id"])
            if k is None or session.get("surum", 0) != k["oturum_surumu"]:   # silinmiş hesap ya da şifre değişti
                session.clear()
            else:
                g.kullanici = kullanicilar.bekleyen_adresi_uygula(db, k)

        # Askıdaki üye okuyabilir, çıkış yapabilir; yazamaz, oy veremez, konu açamaz.
        if (g.kullanici is not None and request.method == "POST" and yonetim.askida_mi(g.kullanici)
                and request.endpoint not in ("hesap.cikis", "api.giris")):
            metin = f"Hesabın {zaman.coz(g.kullanici['askida_bitis']):%d.%m.%Y %H:%M} tarihine kadar askıda; bu işlemi yapamazsın."
            if g.api:
                return jsonify(hata=metin), 403
            flash(metin, "hata")
            hedef = request.referrer if request.referrer and request.referrer.startswith(request.host_url) else None
            return redirect(hedef or url_for("konular.ana_sayfa"))

        if request.method == "POST" and app.config["CSRF"] and not g.token:
            cerezli = "kullanici_id" in session
            if cerezli or not g.api:
                gelen = request.form.get("csrf") or request.headers.get("X-CSRF-Token") or ""
                if not session.get("csrf") or not hmac.compare_digest(gelen, session["csrf"]):
                    if g.api:
                        return jsonify(hata="Güvenlik anahtarı (CSRF) geçersiz."), 400
                    abort(400, "Güvenlik anahtarı geçersiz; sayfayı yenileyip tekrar dene.")
        gorevler.tick(db)   # süresi dolan tartışmalar ve oylama turları
        db.commit()
        if request.method == "POST":
            # Yazma isteği baştan yazma kilidini alır: "zaten fikrin var mı?" gibi kontrol ile kayıt arasında başka
            # bir istek araya giremez (eşzamanlı isteklerle kişi başı tek fikir kuralı aşılabiliyordu).
            db.execute("BEGIN IMMEDIATE")

    @app.after_request
    def guvenlik_basliklari(yanit):
        yanit.headers.setdefault("X-Content-Type-Options", "nosniff")
        yanit.headers.setdefault("X-Frame-Options", "DENY")
        yanit.headers.setdefault("Referrer-Policy", "same-origin")
        yanit.headers.setdefault("Content-Security-Policy",
                                 "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                                 "script-src 'self'; connect-src 'self'; manifest-src 'self'; worker-src 'self'; "
                                 "frame-ancestors 'none'; form-action 'self'; base-uri 'self'; object-src 'none'")
        if getattr(g, "kullanici", None) is not None:
            yanit.headers.setdefault("Cache-Control", "no-store")   # kişisel sayfalar tarayıcı önbelleğinde kalmasın
        return yanit

    @app.teardown_appcontext
    def kapat(_hata):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(KuralHatasi)
    def kural_hatasi(e):
        db_al().rollback()
        if g.get("api"):
            return jsonify(hata=str(e)), 422
        if request.method == "GET":
            return render_template("hata.html", baslik="İşlem yapılamadı", mesaj=str(e)), 400
        flash(str(e), "hata")
        hedef = request.referrer if request.referrer and request.referrer.startswith(request.host_url) else None
        return redirect(hedef or url_for("konular.ana_sayfa"))

    def _hata(kod, baslik, mesaj):
        if g.get("api"):
            return jsonify(hata=mesaj), kod
        return render_template("hata.html", baslik=baslik, mesaj=mesaj), kod

    app.register_error_handler(400, lambda e: _hata(400, "Geçersiz istek", e.description))
    app.register_error_handler(403, lambda e: _hata(403, "Yetkin yok", "Bu sayfa sadece yöneticiler içindir."))
    app.register_error_handler(404, lambda e: _hata(404, "Sayfa bulunamadı", "Aradığın sayfa yok."))
    app.register_error_handler(413, lambda e: _hata(413, "Çok büyük", "Gönderdiğin veri çok büyük."))

    @app.errorhandler(500)
    def hata_500(e):
        log.exception("Sunucu hatası")
        return _hata(500, "Beklenmeyen hata", "Beklenmeyen bir hata oluştu ve kaydedildi. Sayfayı yenileyip tekrar dene.")

    app.jinja_env.globals.update(ayarlar=ayarlar, csrf_token=csrf_token, avatar=yardimcilar.avatar, ikon=ikonlar.ikon,
                                 parametre=lambda kod: yonetmelik.parametre_metni(db_al(), kod))

    @app.context_processor
    def sablon_degiskenleri():
        k = getattr(g, "kullanici", None)
        ortak = {"yan_kategoriler": konular.kategori_ozeti(db_al()), "site_duyurusu": yonetim.site_ayari(db_al(), "duyuru"),
                 "mobil_uygulama": ayarlar.MOBIL_UA in request.headers.get("User-Agent", "")}
        if not k:
            return dict(ortak, kullanici=None, bekleyen_oy=0, okunmamis=0, askida=False, acik_sikayet=0)
        return dict(ortak, kullanici=k, bekleyen_oy=oylama.bekleyen_oy_sayisi(db_al(), k),
                    okunmamis=bildirimler.okunmamis_sayisi(db_al(), k["id"]), askida=yonetim.askida_mi(k),
                    acik_sikayet=sikayetler.acik_sayisi(db_al()) if k["yonetici_mi"] else 0)

    @app.template_filter("tarih")
    def tarih(deger):
        return zaman.coz(deger).strftime("%d.%m.%Y %H:%M") if deger else ""

    @app.template_filter("gun")
    def gun(deger):
        return zaman.coz(deger).strftime("%d.%m.%Y") if deger else ""

    @app.template_filter("kalan")
    def kalan(deger):
        fark = zaman.coz(deger) - zaman.simdi()
        if fark.total_seconds() <= 0:
            return "süresi doldu"
        saat, dakika = fark.seconds // 3600, (fark.seconds % 3600) // 60
        if fark.days:
            return f"{fark.days} gün {saat} saat kaldı"
        return f"{saat} saat {dakika} dk kaldı" if saat else f"{dakika} dk kaldı"

    @app.template_filter("once")
    def once(deger):
        """Göreli zaman: "az önce", "5 dk önce", "3 saat önce", "2 gün önce"."""
        if not deger:
            return ""
        saniye = (zaman.simdi() - zaman.coz(deger)).total_seconds()
        if saniye < 60:
            return "az önce"
        if saniye < 3600:
            return f"{int(saniye // 60)} dk önce"
        if saniye < 86400:
            return f"{int(saniye // 3600)} saat önce"
        if saniye < 30 * 86400:
            return f"{int(saniye // 86400)} gün önce"
        return zaman.coz(deger).strftime("%d.%m.%Y")

    @app.template_filter("kategori_rengi")
    def kategori_rengi(kategori_id):
        return ontoloji.kategori_rengi(db_al(), kategori_id) if kategori_id else ayarlar.VARSAYILAN_KATEGORI_RENGI

    app.template_filter("yuzde")(yuzde)

    @app.template_filter("konum")
    def konum(konum_id):
        return ontoloji.yol_metni(db_al(), "konumlar", konum_id) if konum_id else "—"

    @app.template_filter("kategori")
    def kategori(kategori_id):
        return ontoloji.yol_metni(db_al(), "kategoriler", kategori_id) if kategori_id else "—"

    app.template_filter("bicimle")(yardimcilar.bicimle)

    from . import api, genel, hesap, konu_sayfalari, oylama_sayfalari, profil, yonetim_sayfalari
    for modul in (hesap, konu_sayfalari, oylama_sayfalari, profil, genel, yonetim_sayfalari, api):
        app.register_blueprint(modul.bp)
