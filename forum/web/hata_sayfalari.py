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
            return render_template("hata.html", baslik="Bulamadık", mesaj=str(e)), 404
        return render_template("hata.html", baslik="Bir sorun oluştu", mesaj=str(e)), 400
    flash(str(e), "hata")
    return redirect(geldigi_sayfa())


def _hata(kod, baslik, mesaj):
    if g.get("api"):
        return jsonify(hata=mesaj), kod
    return render_template("hata.html", baslik=baslik, mesaj=mesaj), kod


def sunucu_hatasi(e):
    log.exception("Sunucu hatası")
    return _hata(500, "Bir şeyler ters gitti", "Bir hata oluştu ve kaydedildi. Sayfayı yenileyip tekrar deneyebilirsin.")


def kur(app):
    app.register_error_handler(KuralHatasi, kural_hatasi)
    app.register_error_handler(400, lambda e: _hata(400, "Bir sorun oluştu", e.description))
    app.register_error_handler(403, lambda e: _hata(403, "Erişimin yok", "Bu sayfaya yalnızca yöneticiler erişebilir."))
    app.register_error_handler(404, lambda e: _hata(404, "Sayfa bulunamadı", "Aradığın sayfayı bulamadık."))
    app.register_error_handler(413, lambda e: _hata(413, "Veri çok büyük", "Gönderdiğin veri çok büyük. Daha kısa gönderip tekrar dene."))
    app.register_error_handler(500, sunucu_hatasi)
