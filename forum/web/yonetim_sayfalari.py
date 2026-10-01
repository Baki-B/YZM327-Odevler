"""Yönetim paneli (/yonetim). Yalnızca yöneticiler görür.

Yönetici yalnızca siteyi yönetir: yetki, askı, kategoriler, şikayet kutusu, duyurular, site ayarları, yedek.
Kararları etkileyemez: uzman atayamaz, oylama sonuçlandıramaz, süre değiştiremez. Tek istisna sunum içindir:
sunucu --demo ile başlatılırsa "süreyi ilerlet" düğmeleri görünür (her kullanımı günlüğe yazılır).
"""
from flask import Blueprint, Response, current_app, flash, g, redirect, render_template, request, url_for

from .. import (ayarlar, defter, gunluk, konular, kullanicilar, ontoloji, oylama, sikayetler, uzmanlik, yonetim,
               zaman)
from ..hatalar import KuralHatasi
from . import db_al, sayfa_no, yonetici_gerekli
from .yardimcilar import sayfala

bp = Blueprint("yonetim", __name__, url_prefix="/yonetim")


@bp.before_request
@yonetici_gerekli
def _yalniz_yonetici():
    return None


def _geri(varsayilan):
    hedef = request.form.get("geri") or ""
    return redirect(hedef if hedef.startswith("/yonetim") else varsayilan)


# --- Pano ---

@bp.get("")
def pano():
    db = db_al()
    return render_template("yonetim/pano.html", p=yonetim.pano(db),
                           basliklar=lambda t: oylama.teklif_basligi(db, t))


# --- Üyeler ---

@bp.get("/uyeler")
def uyeler():
    db = db_al()
    q, filtre = request.args.get("q", "").strip(), request.args.get("filtre", "")
    satirlar, sayfalama = sayfala(yonetim.uyeler(db, q, filtre), sayfa_no(), 30)
    return render_template("yonetim/uyeler.html", satirlar=satirlar, sayfalama=sayfalama, q=q, filtre=filtre,
                           filtreler=yonetim.UYE_FILTRELERI, simdi=zaman.simdi_metin())


@bp.get("/uye/<int:kullanici_id>")
def uye(kullanici_id):
    db = db_al()
    k = kullanicilar.getir(db, kullanici_id)
    if not k:
        raise KuralHatasi("Üye bulunamadı.")
    return render_template("yonetim/uye.html", k=k, ozet=yonetim.uye_ozeti(db, k["id"]),
                           askida=yonetim.askida_mi(k),
                           uzmanliklar=uzmanlik.uzmanliklar(db, k["id"], sadece_aktif=False),
                           aktif={u["id"] for u in uzmanlik.uzmanliklar(db, k["id"])},
                           gunluk=yonetim.uye_gunlugu(db, k["id"]),
                           max_aski=yonetim.MAX_ASKI_GUN)


@bp.post("/uye/<int:kullanici_id>/yetki")
def yetki(kullanici_id):
    db = db_al()
    yonetim.yetki_ver(db, g.kullanici, kullanici_id, request.form.get("yonetici") == "1")
    db.commit()
    flash("Yetki güncellendi.", "basari")
    return redirect(url_for("yonetim.uye", kullanici_id=kullanici_id))


@bp.post("/uye/<int:kullanici_id>/aski")
def aski(kullanici_id):
    db = db_al()
    bitis = yonetim.askiya_al(db, g.kullanici, kullanici_id, request.form.get("gun"), request.form.get("neden"))
    db.commit()
    flash(f"Üye {bitis:%d.%m.%Y %H:%M} tarihine kadar askıya alındı.", "basari")
    return redirect(url_for("yonetim.uye", kullanici_id=kullanici_id))


@bp.post("/uye/<int:kullanici_id>/aski-kaldir")
def aski_kaldir(kullanici_id):
    db = db_al()
    yonetim.askiyi_kaldir(db, g.kullanici, kullanici_id)
    db.commit()
    flash("Askı kaldırıldı.", "basari")
    return redirect(url_for("yonetim.uye", kullanici_id=kullanici_id))


# --- Konular ve oylamalar ---

KONU_FILTRELERI = [("", "Tümü")] + list(ayarlar.KONU_DURUMLARI.items()) + [("SILINDI", "Kaldırılanlar")]


def _demo_olmali():
    if not current_app.config.get("DEMO"):
        raise KuralHatasi("Süre yalnızca sunum kipinde (--demo) ilerletilebilir.")


@bp.get("/konular")
def konu_listesi():
    db = db_al()
    durum = request.args.get("durum", "")
    sorgu = """SELECT k.*, u.takma_ad AS sahip,
                      (SELECT COUNT(*) FROM mesajlar m WHERE m.konu_id = k.id AND m.yazar_id IS NOT NULL) AS mesaj_sayisi
               FROM konular k JOIN kullanicilar u ON u.id = k.sahip_id """
    if durum == "SILINDI":
        satirlar = db.execute(sorgu + "WHERE k.silindi = 1 ORDER BY k.id DESC").fetchall()
    elif durum:
        satirlar = db.execute(sorgu + "WHERE k.silindi = 0 AND k.durum = ? ORDER BY k.id DESC", (durum,)).fetchall()
    else:
        satirlar = db.execute(sorgu + "WHERE k.silindi = 0 ORDER BY k.id DESC").fetchall()
    parca, sayfalama = sayfala(satirlar, sayfa_no(), 30)
    return render_template("yonetim/konular.html", satirlar=parca, sayfalama=sayfalama, durum=durum,
                           filtreler=KONU_FILTRELERI)


@bp.post("/konu/<int:konu_id>/ilerlet")
def konu_ilerlet(konu_id):
    """Sunum kipi: tartışma süresini beklemeden oylamayı başlatır ya da açık turu sonuçlandırır."""
    _demo_olmali()
    db = db_al()
    k = konular.konu_getir(db, konu_id)
    if k["durum"] == "TARTISMA":
        konular.oylamayi_baslat(db, konu_id)
    elif k["durum"] == "OYLAMA":
        t = oylama.acik_teklif(db, "KARAR", konu_id=konu_id)
        if t:
            oylama.sonuclandir(db, t["id"])
    else:
        raise KuralHatasi("Bu konu kapanmış.")
    gunluk.kaydet(db, g.kullanici["id"], "SURE", f"Sunum kipi: #{konu_id} “{k['baslik']}” için süre ilerletildi")
    db.commit()
    flash("Süre ilerletildi.", "bilgi")
    return _geri(url_for("yonetim.konu_listesi"))


@bp.get("/oylamalar")
def oylamalar():
    db = db_al()
    acik = [{"t": t, "baslik": oylama.teklif_basligi(db, t),
             "oy": db.execute("SELECT COUNT(*) FROM oylar WHERE teklif_id = ?", (t["id"],)).fetchone()[0]}
            for t in db.execute("SELECT * FROM teklifler WHERE durum = 'ACIK' ORDER BY bitis")]
    biten = [{"t": t, "baslik": oylama.teklif_basligi(db, t)}
             for t in db.execute("SELECT * FROM teklifler WHERE durum != 'ACIK' ORDER BY id DESC LIMIT 20")]
    return render_template("yonetim/oylamalar.html", acik=acik, biten=biten)


@bp.post("/oylama/<int:teklif_id>/ilerlet")
def oylama_ilerlet(teklif_id):
    _demo_olmali()
    db = db_al()
    t = oylama.teklif_getir(db, teklif_id)
    if t["durum"] == "ACIK":
        oylama.sonuclandir(db, teklif_id)
        gunluk.kaydet(db, g.kullanici["id"], "SURE", f"Sunum kipi: #{teklif_id} numaralı oylamanın süresi ilerletildi")
    db.commit()
    flash("Oylama sonuçlandırıldı.", "bilgi")
    return _geri(url_for("yonetim.oylamalar"))


# --- Şikayetler ---

@bp.get("/sikayetler")
def sikayet_listesi():
    db = db_al()
    kapali = request.args.get("durum") == "kapali"
    return render_template("yonetim/sikayetler.html", gruplar=sikayetler.liste(db, "KAPALI" if kapali else "ACIK"),
                           kapali=kapali, durumlar=sikayetler.DURUMLAR)


@bp.post("/sikayet/<int:sikayet_id>/oylama")
def sikayet_oylama(sikayet_id):
    db = db_al()
    teklif_id = sikayetler.oylamaya_al(db, g.kullanici, sikayet_id)
    db.commit()
    flash("Şikayet oylamaya alındı; şikayet edenlere bildirildi.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


@bp.post("/sikayet/<int:sikayet_id>/yersiz")
def sikayet_yersiz(sikayet_id):
    db = db_al()
    sikayetler.yersiz_bul(db, g.kullanici, sikayet_id, request.form.get("not"))
    db.commit()
    flash("Şikayet kapatıldı; şikayet edenlere bildirildi.", "bilgi")
    return redirect(url_for("yonetim.sikayet_listesi"))


# --- Toplu bildirim ---

@bp.route("/bildirim", methods=["GET", "POST"])
def bildirim_gonder():
    db = db_al()
    f = request.form
    if request.method == "POST":
        sayi = yonetim.toplu_bildirim(db, g.kullanici, f.get("hedef"), f.get("metin"), f.get("baglanti"),
                                      f.get("ilce_id") or f.get("il_id"), f.get("kategori_id"))
        db.commit()
        flash(f"Bildirim {sayi} kişiye gönderildi.", "basari")
        return redirect(url_for("yonetim.bildirim_gonder"))
    return render_template("yonetim/bildirim.html", hedefler=yonetim.BILDIRIM_HEDEFLERI,
                           iller=ontoloji.il_listesi(db), ilceler=ontoloji.ilce_haritasi(db),
                           kategoriler=ontoloji.kategori_listesi(db),
                           gecmis=yonetim.gunluk_kayitlari(db, "TOPLU_BILDIRIM", limit=10))


# --- Kategoriler ---

@bp.get("/kategoriler")
def kategoriler():
    db = db_al()
    return render_template("yonetim/kategoriler.html", agac=yonetim.kategori_agaci(db), renkler=yonetim.RENK_SECENEKLERI)


@bp.post("/kategoriler")
def kategori_ekle():
    db = db_al()
    f = request.form
    yonetim.kategori_ekle(db, g.kullanici, f.get("ad"), f.get("ust_id") or None, f.get("renk"))
    db.commit()
    flash("Kategori eklendi.", "basari")
    return redirect(url_for("yonetim.kategoriler"))


@bp.post("/kategori/<int:kategori_id>")
def kategori_duzenle(kategori_id):
    db = db_al()
    yonetim.kategori_duzenle(db, g.kullanici, kategori_id, request.form.get("ad"), request.form.get("renk"))
    db.commit()
    flash("Kategori güncellendi.", "basari")
    return redirect(url_for("yonetim.kategoriler"))


# --- Sistem: site ayarları, yapay zeka, kayıt defteri, yedek ---

@bp.get("/sistem")
def sistem():
    db = db_al()
    return render_template(
        "yonetim/sistem.html", duyuru=yonetim.site_ayari(db, "duyuru"), kayit_acik=yonetim.site_ayari(db, "kayit_acik") == "1",
        yz_hesaplari=db.execute("SELECT * FROM kullanicilar WHERE yz_mi = 1 ORDER BY takma_ad").fetchall(),
        defter_durumu=defter.durum(db.defter_klasoru),
        tutarlilik=defter.tutarlilik(db) if request.args.get("denetle") else None)


@bp.post("/ayar")
def ayar():
    db = db_al()
    f = request.form
    for anahtar in yonetim.SITE_AYARLARI:
        if anahtar in f:
            yonetim.site_ayari_yaz(db, g.kullanici, anahtar, f.get(anahtar))
    db.commit()
    flash("Ayarlar kaydedildi.", "basari")
    return redirect(url_for("yonetim.sistem"))


@bp.post("/yz")
def yz_ekle():
    db = db_al()
    kullanicilar.yz_ekle(db, g.kullanici, request.form.get("takma_ad"))
    db.commit()
    flash("Yapay zeka hesabı açıldı.", "basari")
    return redirect(url_for("yonetim.sistem", _anchor="yz"))


@bp.post("/defter/<ad>/<islem>")
def defter_deneme(ad, islem):
    db = db_al()
    if ad not in ayarlar.DEFTER_DUGUMLERI or islem not in ("boz", "onar"):
        raise KuralHatasi("Geçersiz işlem.")
    if islem == "boz":
        no = defter.boz_demo(db.defter_klasoru, ad)
        flash(f"Deneme: {ad} düğümündeki #{no} numaralı blok bozuldu. Kayıt defteri sayfası bu bozulmayı göstermeli.", "hata")
    else:
        try:
            defter.onar(db.defter_klasoru, ad)
        except ValueError as e:
            raise KuralHatasi(str(e))
        flash(f"{ad} düğümü çoğunluk zincirinden onarıldı.", "basari")
    return redirect(url_for("yonetim.sistem", _anchor="defter"))


@bp.get("/yedek")
def yedek():
    db = db_al()
    veri = yonetim.yedek_al(db)
    gunluk.kaydet(db, g.kullanici["id"], "SITE_AYARI", "Veritabanı yedeği indirildi")
    db.commit()
    ad = f"agora-yedek-{zaman.simdi():%Y%m%d-%H%M}.db"
    return Response(veri, mimetype="application/vnd.sqlite3",
                    headers={"Content-Disposition": f'attachment; filename="{ad}"'})


# --- Günlük ---

@bp.get("/gunluk")
def gunluk_sayfasi():
    db = db_al()
    eylem, kim = request.args.get("eylem", ""), request.args.get("kim", "").strip()
    kayitlar, sayfalama = sayfala(yonetim.gunluk_kayitlari(db, eylem, kim), sayfa_no(), 50)
    return render_template("yonetim/gunluk.html", kayitlar=kayitlar, sayfalama=sayfalama, eylem=eylem, kim=kim,
                           eylemler=yonetim.gunluk_eylemleri(db), eylem_adlari=yonetim.EYLEM_ADLARI)
