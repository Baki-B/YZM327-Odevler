"""Agora — herkesin fikir yazdığı, fikirlerin tur tur oylandığı tartışma forumu.

Konu açılır, tartışılır, her katılımcı bir fikir yazar; fikirler en fazla beş turda elenerek tek karara iner.
Oran çift hesaplanır (ağırlıklı pay ve kişi payı), mesajlar silinmez ve her olay dağıtık deftere yazılır.
"""
import logging
import os
import secrets
from logging.handlers import RotatingFileHandler

from flask import Flask


def create_app(ayar=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        VERITABANI=os.environ.get("FORUM_VERITABANI", os.path.join(app.instance_path, "forum.db")),
        SECRET_KEY=os.environ.get("FORUM_GIZLI_ANAHTAR") or (ayar or {}).get("SECRET_KEY")
        or _gizli_anahtar(app.instance_path),
        CSRF=True,
        ZAMANLAYICI=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("FORUM_HTTPS") == "1",   # HTTPS arkasında yayınlanınca açılır
        MAX_CONTENT_LENGTH=1024 * 1024,
        JSON_AS_ASCII=False,
    )
    if ayar:
        app.config.update(ayar)
    if not app.config.get("TESTING") and not app.config.get("TARAYICI"):
        _gunluk_dosyasi(app)

    from . import ontoloji, veritabani, yonetmelik
    db = veritabani.hazirla(app.config["VERITABANI"])
    ontoloji.yukle(db)
    yonetmelik.yukle(db)
    db.commit()
    db.close()

    from .web import kur
    kur(app)

    if app.config["ZAMANLAYICI"]:
        from . import gorevler
        gorevler.arka_plan_baslat(app.config["VERITABANI"])
    return app


def _gizli_anahtar(klasor):
    """Oturum çerezlerini imzalayan anahtar; ilk çalıştırmada üretilir ve saklanır."""
    yol = os.path.join(klasor, "gizli_anahtar.txt")
    if not os.path.exists(yol):
        with os.fdopen(os.open(yol, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(32))     # yalnızca sunucuyu çalıştıran kullanıcı okuyabilir
    with open(yol, encoding="utf-8") as f:
        return f.read().strip()


def _gunluk_dosyasi(app):
    isleyici = RotatingFileHandler(os.path.join(app.instance_path, "forum.log"), maxBytes=1_000_000, backupCount=3,
                                   encoding="utf-8")
    isleyici.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    isleyici.setLevel(logging.INFO)
    kok = logging.getLogger("forum")
    kok.setLevel(logging.INFO)
    if not any(isinstance(h, RotatingFileHandler) for h in kok.handlers):
        kok.addHandler(isleyici)
