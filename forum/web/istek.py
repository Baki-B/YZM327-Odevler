"""Her isteğin önünden ve arkasından geçtiği adımlar.

İstek öncesi adımlar ayrı fonksiyonlardır ve kayıt sırasıyla çalışır; biri yanıt döndürürse sonrakiler çalışmaz.
Bu, web çatılarındaki ara katman (middleware) zinciridir — GoF Chain of Responsibility'nin Flask'taki karşılığı.
  1. kimlik       oturum çerezi ya da (yalnızca /api/ altında) Bearer API anahtarı
  2. aski         askıdaki üyenin yazma isteklerini durdurur
  3. csrf         çerezle gelen POST'larda güvenlik anahtarını doğrular
  4. zamanlayici  süresi dolan tartışmaları ve oylama turlarını işler
  5. yazma_kilidi POST isteklerinde baştan yazma kilidini alır
Önceden bunların hepsi (ve hata sayfaları, şablon filtreleri...) 150 satırlık tek bir kur() fonksiyonundaydı.
"""
import hmac

from flask import abort, current_app, flash, g, jsonify, redirect, request, session, url_for

from .. import gorevler, guvenlik, kullanicilar, uygunluk, zaman
from . import db_al

CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
       "connect-src 'self'; manifest-src 'self'; worker-src 'self'; frame-ancestors 'none'; form-action 'self'; "
       "base-uri 'self'; object-src 'none'")


def _statik():
    return request.endpoint == "static"


def kimlik():
    if _statik():
        return None
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
    return None


def aski():
    """Askıdaki üye okuyabilir, çıkış yapabilir; yazamaz, oy veremez, konu açamaz."""
    if _statik() or g.kullanici is None or request.method != "POST" or not uygunluk.askida_mi(g.kullanici) \
            or request.endpoint in ("hesap.cikis", "api.giris"):
        return None
    metin = f"Hesabın {zaman.coz(g.kullanici['askida_bitis']):%d.%m.%Y %H:%M} tarihine kadar askıda; bu işlemi yapamazsın."
    if g.api:
        return jsonify(hata=metin), 403
    flash(metin, "hata")
    return redirect(geldigi_sayfa())


def csrf():
    if _statik() or request.method != "POST" or not current_app.config["CSRF"] or g.token:
        return None
    if "kullanici_id" not in session and g.api:          # çerezsiz API isteği: CSRF riski yok (kimlik Bearer ile)
        return None
    gelen = request.form.get("csrf") or request.headers.get("X-CSRF-Token") or ""
    if not session.get("csrf") or not hmac.compare_digest(gelen, session["csrf"]):
        if g.api:
            return jsonify(hata="Güvenlik anahtarı (CSRF) geçersiz."), 400
        abort(400, "Güvenlik anahtarı geçersiz; sayfayı yenileyip tekrar dene.")
    return None


def zamanlayici():
    if _statik():
        return None
    db = db_al()
    gorevler.tick(db)   # süresi dolan tartışmalar ve oylama turları
    db.commit()
    return None


def yazma_kilidi():
    # Yazma isteği baştan yazma kilidini alır: "zaten fikrin var mı?" gibi kontrol ile kayıt arasında başka bir istek
    # araya giremez (eşzamanlı isteklerle kişi başı tek fikir kuralı aşılabiliyordu).
    if not _statik() and request.method == "POST":
        db_al().execute("BEGIN IMMEDIATE")
    return None


def guvenlik_basliklari(yanit):
    # Tarayıcı sürümünde (GitHub Pages, tarayici/) uygulama aynı sitedeki kabuk sayfasının çerçevesinde açılır; yalnızca
    # aynı kökenden çerçeveye izin verilir. Sunucu sürümünde hiçbir site çerçeveye alamaz.
    cerceve = "'self'" if current_app.config.get("TARAYICI") else "'none'"
    yanit.headers.setdefault("X-Content-Type-Options", "nosniff")
    yanit.headers.setdefault("X-Frame-Options", "SAMEORIGIN" if current_app.config.get("TARAYICI") else "DENY")
    yanit.headers.setdefault("Referrer-Policy", "same-origin")
    yanit.headers.setdefault("Content-Security-Policy", CSP.replace("frame-ancestors 'none'", f"frame-ancestors {cerceve}"))
    if getattr(g, "kullanici", None) is not None:
        yanit.headers.setdefault("Cache-Control", "no-store")   # kişisel sayfalar tarayıcı önbelleğinde kalmasın
    return yanit


def baglantiyi_kapat(_hata):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def geldigi_sayfa():
    """Formun gönderildiği sayfa (aynı siteden geldiyse), yoksa konu akışı."""
    hedef = request.referrer if request.referrer and request.referrer.startswith(request.host_url) else None
    return hedef or url_for("konular.ana_sayfa")


def kur(app):
    for adim in (kimlik, aski, csrf, zamanlayici, yazma_kilidi):      # sıra önemlidir
        app.before_request(adim)
    app.after_request(guvenlik_basliklari)
    app.teardown_appcontext(baglantiyi_kapat)
