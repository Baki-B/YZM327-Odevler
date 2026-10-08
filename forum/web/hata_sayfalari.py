"""Hataların kullanıcıya gösterimi: tarayıcıya sayfa, API'ye JSON. İş katmanı yalnızca KuralHatasi fırlatır;
HTTP'ye çevirmek burada, tek yerde yapılır."""
import logging

from flask import flash, g, jsonify, redirect, render_template, request

from ..hatalar import BulunamadiHatasi, KuralHatasi
from . import db_al
from .istek import geldigi_sayfa

log = logging.getLogger("forum.web")


def kural_hatasi(e):
    db_al().rollback()
    yok = isinstance(e, BulunamadiHatasi)
    if g.get("api"):
        return jsonify(hata=str(e)), 404 if yok else 422
    if request.method == "GET":
        if yok:
            return render_template("hata.html", baslik="Bulunamadı", mesaj=str(e)), 404
        return render_template("hata.html", baslik="İşlem yapılamadı", mesaj=str(e)), 400
    flash(str(e), "hata")
    return redirect(geldigi_sayfa())


def _hata(kod, baslik, mesaj):
    if g.get("api"):
        return jsonify(hata=mesaj), kod
    return render_template("hata.html", baslik=baslik, mesaj=mesaj), kod


def sunucu_hatasi(e):
    log.exception("Sunucu hatası")
    return _hata(500, "Beklenmeyen hata", "Beklenmeyen bir hata oluştu ve kaydedildi. Sayfayı yenileyip tekrar dene.")


def kur(app):
    app.register_error_handler(KuralHatasi, kural_hatasi)
    app.register_error_handler(400, lambda e: _hata(400, "Geçersiz istek", e.description))
    app.register_error_handler(403, lambda e: _hata(403, "Yetkin yok", "Bu sayfa sadece yöneticiler içindir."))
    app.register_error_handler(404, lambda e: _hata(404, "Sayfa bulunamadı", "Aradığın sayfa yok."))
    app.register_error_handler(413, lambda e: _hata(413, "Çok büyük", "Gönderdiğin veri çok büyük."))
    app.register_error_handler(500, sunucu_hatasi)
