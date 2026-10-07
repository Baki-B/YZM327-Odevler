import json

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from .. import kararlar, konular, kullanicilar, oylama, sonuclar, uygunluk
from ..metin import yuzde
from . import db_al, giris_gerekli, sayfa_no
from .yardimcilar import sayfala

bp = Blueprint("oylamalar", __name__)


@bp.get("/gundem")
def gundem():
    db = db_al()
    benim = oylama.kullanici_teklifleri(db, g.kullanici) if g.kullanici else []
    benim_idler = {x["teklif"]["id"] for x in benim}
    diger = [x for x in oylama.acik_teklifler(db, 100) if x["teklif"]["id"] not in benim_idler]
    kapananlar = db.execute("SELECT * FROM teklifler WHERE durum NOT IN ('ACIK', 'IPTAL') "
                            "ORDER BY kapanis DESC LIMIT 15").fetchall()
    return render_template("gundem.html", benim=benim, diger=diger,
                           kapananlar=[{"teklif": t, "baslik": oylama.teklif_basligi(db, t)} for t in kapananlar])


def _tur_bilgisi(db, t, karar=None):
    """Fikir oylaması turunun kuralı: bu turda hangi oranın altı elenir? Kapanmış turda, kapanış anındaki kurallar."""
    if not oylama.turu(t).fikir_oylamasi:
        return None
    ezici, eleme = (karar.ezici, karar.eleme) if karar else sonuclar.tur_kurallari(db, t["tur_no"])
    return {"no": t["tur_no"], "son": eleme is None, "ezici": yuzde(ezici), "eleme": None if eleme is None else yuzde(eleme)}


@bp.get("/oylama/<int:teklif_id>")
def teklif(teklif_id):
    db = db_al()
    t = oylama.teklif_getir(db, teklif_id)
    tur_ = oylama.turu(t)
    konu = konular.konu_getir(db, t["konu_id"]) if t["konu_id"] else None
    makbuz = session.pop("son_makbuz", None)
    if makbuz and makbuz.get("teklif") != teklif_id:
        makbuz = None
    sonuc = oylama.sonuc(t)
    tur_sonucu = karar = None
    if tur_.fikir_oylamasi and sonuc and t["durum"] in ("BITTI", "YETERSIZ"):
        karar = sonuclar.tur_sonucu(db, t, sonuc)
        tur_sonucu = {"karar": karar.sonuc, "kalanlar": set(karar.kalanlar), "aciklama": karar.aciklama}
    return render_template(
        "teklif.html", t=t, veri=json.loads(t["veri"] or "{}"), konu=konu, baslik=tur_.baslik(db, t),
        fikir_oylamasi=tur_.fikir_oylamasi, acan=kullanicilar.getir(db, t["acan_id"]) if t["acan_id"] else None,
        secenekler=oylama.secenekler(db, teklif_id), durum=oylama.oy_durumu(db, t, g.kullanici),
        sonuc=sonuc, tur_sonucu=tur_sonucu, tur_bilgisi=_tur_bilgisi(db, t, karar),
        oy_sayisi=oylama.oy_sayisi(db, teklif_id),
        hak_sahibi=len(uygunluk.oy_hakki_olanlar(db, oylama.teklif_baglami(db, t))), makbuz=makbuz,
        **tur_.sayfa_verisi(db, t),           # türe özgü bölümün verisi (teklif/_<tür>.html)
    )


@bp.post("/oylama/<int:teklif_id>/oy")
@giris_gerekli
def oy_ver(teklif_id):
    db = db_al()
    makbuz = oylama.oy_ver(db, teklif_id, g.kullanici, request.form.get("secim", ""), request.form.get("gerekce"))
    db.commit()
    session["son_makbuz"] = {"teklif": teklif_id, "kod": makbuz}
    if oylama.teklif_getir(db, teklif_id)["durum"] != "ACIK":
        flash("Oyun kaydedildi. Oy hakkı olan herkes oy verdiği için oylama sonuçlandı.", "basari")
    else:
        flash("Oyun kaydedildi. Oylama bitene kadar değiştirebilirsin.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


@bp.get("/kararlar")
def kararlar_arsivi():
    db = db_al()
    parca, sayfalama = sayfala(kararlar.tum_kararlar(db), sayfa_no(), 10)
    return render_template("kararlar.html", liste=parca, sayfalama=sayfalama,
                           itirazlar={kr["konu_no"]: konular.itirazlar(db, kr["konu_no"]) for kr in parca})
