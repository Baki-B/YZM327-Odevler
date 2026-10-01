import json

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from .. import ayarlar, kararlar, konular, kullanicilar, oylama, sonuclar, uygunluk, uzmanlik, yonetmelik
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


def _tur_bilgisi(db, t):
    """Fikir oylaması turunun kuralı: bu turda hangi oranın altı elenir?"""
    if t["tip"] != "KARAR":
        return None
    son = t["tur_no"] >= ayarlar.TUR_SAYISI
    return {"no": t["tur_no"], "son": son, "ezici": yonetmelik.parametre_metni(db, "ESIK_EZICI"),
            "eleme": None if son else yonetmelik.parametre_metni(db, ayarlar.ELEME_PARAMETRELERI[t["tur_no"]])}


@bp.get("/oylama/<int:teklif_id>")
def teklif(teklif_id):
    db = db_al()
    t = oylama.teklif_getir(db, teklif_id)
    veri = json.loads(t["veri"] or "{}")
    konu = konular.konu_getir(db, t["konu_id"]) if t["konu_id"] else None
    hedef_mesajlar, aday = [], None
    kategori_onerisi = None
    if t["tip"] == "KATEGORI":
        from .. import kategoriler as _k
        kategori_onerisi = {"yol": _k.oneri_basligi(db, veri), "ust": veri.get("ust_id"), "kavramlar": veri.get("kavramlar", []),
                            "eklenen": db.execute("SELECT id FROM kategoriler WHERE ad = ? AND ust_id IS ?",
                                                  (veri["ad"], veri.get("ust_id"))).fetchone() if t["durum"] == "KABUL" else None}
    if t["tip"] == "MESAJ_SILME":
        idler = veri.get("mesajlar", [t["hedef_id"]])
        hedef_mesajlar = db.execute(
            f"""SELECT m.*, k.takma_ad, k.yz_mi FROM mesajlar m LEFT JOIN kullanicilar k ON k.id = m.yazar_id
                WHERE m.id IN ({','.join('?' * len(idler))}) ORDER BY m.id""", idler).fetchall()
    if t["tip"] == "UZMANLIK":
        k = kullanicilar.getir(db, t["hedef_id"])
        aday = {"k": k, "sart": uzmanlik.on_sartlar(db, k["id"], veri["kategori_id"]),
                "kontenjan": uzmanlik.kontenjan(db, veri["kategori_id"])}
    makbuz = session.pop("son_makbuz", None)
    if makbuz and makbuz.get("teklif") != teklif_id:
        makbuz = None
    sonuc = oylama.sonuc(t)
    tur_sonucu = None
    if t["tip"] == "KARAR" and sonuc and t["durum"] in ("BITTI", "YETERSIZ"):
        karar, kalanlar, aciklama = sonuclar.tur_karari(db, t["tur_no"], sonuc)
        tur_sonucu = {"karar": karar, "kalanlar": {f["anahtar"] for f in kalanlar}, "aciklama": aciklama}
    return render_template(
        "teklif.html", t=t, veri=veri, konu=konu, baslik=oylama.teklif_basligi(db, t),
        acan=kullanicilar.getir(db, t["acan_id"]) if t["acan_id"] else None,
        secenekler=oylama.secenekler(db, teklif_id), durum=oylama.oy_durumu(db, t, g.kullanici),
        sonuc=sonuc, tur_sonucu=tur_sonucu, tur_bilgisi=_tur_bilgisi(db, t), hedef_mesajlar=hedef_mesajlar, aday=aday,
        kategori_onerisi=kategori_onerisi,
        oy_sayisi=db.execute("SELECT COUNT(*) FROM oylar WHERE teklif_id = ?", (teklif_id,)).fetchone()[0],
        hak_sahibi=len(uygunluk.oy_hakki_olanlar(db, uygunluk.teklif_baglami(db, t))), makbuz=makbuz,
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
