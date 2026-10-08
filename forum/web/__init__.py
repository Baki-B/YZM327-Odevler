"""Web katmanı: iş mantığı modüllerini (forum/*.py) HTTP'ye bağlar.

Modüller: istek.py (istek öncesi zincir: kimlik, askı, CSRF, zamanlayıcı), hata_sayfalari.py, sablon.py (şablon
filtreleri ve bağlamı) ve alan başına blueprint'ler (hesap, konu_sayfalari, oylama_sayfalari, profil, genel,
yonetim_sayfalari, api). Bu dosyada yalnızca blueprint'lerin ortak kullandığı küçük yardımcılar vardır.

Kimlik doğrulama iki yoldan olur:
  * Tarayıcı: imzalı oturum çerezi + her POST'ta CSRF anahtarı.
  * Uygulama (API): `Authorization: Bearer <anahtar>` başlığı (CSRF gerekmez, çerez kullanılmaz).
"""
import secrets
from functools import wraps

from flask import abort, current_app, flash, g, jsonify, redirect, request, session, url_for

from .. import veritabani


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
            # Girişten sonra yalnızca GET sayfasına dönülür; POST adresi 405 verir.
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
    """Sayfa numarası 1 ile 100.000 arasında tutulur; çok büyük sayılar sorguda taşmaya (500) yol açar."""
    return min(max(request.args.get("sayfa", 1, type=int), 1), 100_000)


def kur(app):
    """Web katmanını uygulamaya bağlar. Her parça kendi modülündedir (tek sorumluluk)."""
    from . import api, genel, hata_sayfalari, hesap, istek, konu_sayfalari, oylama_sayfalari, profil, sablon, \
        yonetim_sayfalari
    istek.kur(app)              # istek öncesi zincir, güvenlik başlıkları, bağlantı kapatma
    hata_sayfalari.kur(app)     # KuralHatasi ve HTTP hataları → sayfa ya da JSON
    sablon.kur(app)             # şablon değişkenleri ve filtreleri
    for modul in (hesap, konu_sayfalari, oylama_sayfalari, profil, genel, yonetim_sayfalari, api):
        app.register_blueprint(modul.bp)
