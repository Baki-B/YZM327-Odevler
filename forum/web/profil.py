from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from .. import (bildirimler, devir, graf, guvenlik, kullanicilar, ontoloji, oylama, sikayetler, uygunluk, uzmanlik,
                yonetim)
from ..metin import site_ici_yol_mu
from . import db_al, giris_gerekli, sayfa_no
from .yardimcilar import sayfa_bilgisi

bp = Blueprint("profil", __name__)


# --- Panelim: üyenin kendi hesabı. Bölümler ayrı sayfalardır; ortak iskelet templates/panel/_kabuk.html ---

@bp.get("/profil")
@giris_gerekli
def profil():
    db = db_al()
    ben = g.kullanici
    takipci, takip = graf.takip_sayilari(db, ben["id"])
    oylamalar = oylama.kullanici_teklifleri(db, ben)
    return render_template(
        "panel/ozet.html", ben=ben, takipci=takipci, takip=takip,
        bekleyen=[x for x in oylamalar if x["durum"]["oy"] is None],
        oy_verdigim=[x for x in oylamalar if x["durum"]["oy"] is not None],
        konularim=db.execute("SELECT * FROM konular WHERE sahip_id = ? AND silindi = 0 ORDER BY id DESC LIMIT 8",
                             (ben["id"],)).fetchall(),
        mesajlarim=db.execute(
            """SELECT m.*, ko.baslik FROM mesajlar m JOIN konular ko ON ko.id = m.konu_id
               WHERE m.yazar_id = ? AND ko.silindi = 0 ORDER BY m.id DESC LIMIT 5""", (ben["id"],)).fetchall(),
        sayilar={"mesaj": db.execute("SELECT COUNT(*) FROM mesajlar WHERE yazar_id = ?", (ben["id"],)).fetchone()[0],
                 "fikir": db.execute("SELECT COUNT(*) FROM mesajlar WHERE yazar_id = ? AND tip = 'FIKIR'",
                                     (ben["id"],)).fetchone()[0],
                 "oy": db.execute("SELECT COUNT(*) FROM oylar WHERE kullanici_id = ?", (ben["id"],)).fetchone()[0]},
        askida=yonetim.askida_mi(ben), sikayetlerim=sikayetler.kullanicinin_sikayetleri(db, ben["id"], 5),
        sikayet_durumlari=sikayetler.DURUMLAR,
    )


@bp.get("/profil/hesap")
@giris_gerekli
def hesap():
    db = db_al()
    ben = g.kullanici
    return render_template("panel/hesap.html", ben=ben,
                           yas=uygunluk.yas(ben["dogum_tarihi"]) if ben["dogum_tarihi"] else None,
                           iller=ontoloji.il_listesi(db), ilceler=ontoloji.ilce_haritasi(db))


@bp.get("/profil/oy-devri")
@giris_gerekli
def devir_sayfasi():
    db = db_al()
    ben = g.kullanici
    return render_template(
        "panel/devir.html", verilen=devir.verilen_devirler(db, ben["id"]), alinan=devir.alinan_devirler(db, ben["id"]),
        kapsam_metni=lambda d: devir.kapsam_metni(db, d["kapsam"], d["kapsam_id"]),
        kategoriler=ontoloji.kategori_listesi(db),
        konu_secenekleri=db.execute("SELECT id, baslik FROM konular WHERE silindi = 0 AND durum IN ('TARTISMA', 'OYLAMA') "
                                    "ORDER BY id DESC").fetchall())


@bp.get("/profil/uzmanlik")
@giris_gerekli
def uzmanlik_sayfasi():
    db = db_al()
    ben = g.kullanici
    kategoriler = ontoloji.kategori_listesi(db)
    secili = request.args.get("alan", type=int) or (kategoriler[0][0] if kategoriler else None)
    return render_template("panel/uzmanlik.html", ben=ben, kategoriler=kategoriler, secili=secili,
                           uzmanliklar=uzmanlik.uzmanliklar(db, ben["id"], sadece_aktif=False),
                           aktif_uzmanliklar={u["id"] for u in uzmanlik.uzmanliklar(db, ben["id"])},
                           basvuru=oylama.acik_teklif(db, "UZMANLIK", hedef_id=ben["id"]),
                           sart=uzmanlik.on_sartlar(db, ben["id"], secili) if secili else None,
                           kontenjan=uzmanlik.kontenjan(db, secili) if secili else None)


@bp.get("/profil/guvenlik")
@giris_gerekli
def guvenlik_sayfasi():
    return render_template("panel/guvenlik.html", ben=g.kullanici)


@bp.get("/profil/uygulama")
@giris_gerekli
def uygulama():
    db = db_al()
    return render_template("panel/uygulama.html", api_anahtarlari=guvenlik.api_anahtarlari(db, g.kullanici["id"]),
                           yeni_anahtar=session.pop("yeni_api_anahtari", None))


@bp.post("/profil/adres")
@giris_gerekli
def adres():
    db = db_al()
    gecerlilik = kullanicilar.adres_degistir(db, g.kullanici, request.form.get("ilce_id") or request.form.get("il_id"))
    db.commit()
    flash(f"Yeni adresin {gecerlilik:%d.%m.%Y} tarihinde geçerli olacak. O zamana kadar eski adresin geçerli.", "basari")
    return redirect(url_for("profil.hesap"))


@bp.post("/profil/adres-iptal")
@giris_gerekli
def adres_iptal():
    db = db_al()
    kullanicilar.adres_degisikligini_iptal(db, g.kullanici)
    db.commit()
    flash("Bekleyen adres değişikliği iptal edildi.", "bilgi")
    return redirect(url_for("profil.hesap"))


@bp.post("/profil/sifre")
@giris_gerekli
def sifre():
    db = db_al()
    f = request.form
    kullanicilar.sifre_degistir(db, g.kullanici, f.get("eski"), f.get("yeni"), f.get("yeni_tekrar"))
    db.commit()
    session["surum"] = kullanicilar.getir(db, g.kullanici["id"])["oturum_surumu"]    # bu oturum açık kalır
    flash("Şifren değişti. Diğer cihazlardaki oturumların ve API anahtarların kapatıldı.", "basari")
    return redirect(url_for("profil.guvenlik_sayfasi"))


@bp.post("/profil/kurtarma")
@giris_gerekli
def kurtarma():
    db = db_al()
    kod = kullanicilar.kurtarma_kodu_yenile(db, g.kullanici, request.form.get("sifre"))
    db.commit()
    session["yeni_kurtarma"] = kod
    return redirect(url_for("hesap.kurtarma_kodu"))


@bp.post("/profil/devir")
@giris_gerekli
def devir_ekle():
    db = db_al()
    f = request.form
    kapsam = f.get("kapsam")
    kapsam_id = {"KATEGORI": f.get("kategori_id"), "KONU": f.get("konu_id")}.get(kapsam, 0)
    devir.devir_ekle(db, g.kullanici, f.get("alan", ""), kapsam, kapsam_id)
    db.commit()
    flash("Oy devrin kaydedildi. Bir oylamada kendin oy verirsen o oylama için devir geçersiz olur.", "basari")
    return redirect(url_for("profil.devir_sayfasi"))


@bp.post("/profil/devir/<int:devir_id>/sil")
@giris_gerekli
def devir_sil(devir_id):
    db = db_al()
    devir.devir_sil(db, g.kullanici, devir_id)
    db.commit()
    flash("Oy devri geri alındı.", "bilgi")
    return redirect(url_for("profil.devir_sayfasi"))


@bp.post("/profil/uzmanlik")
@giris_gerekli
def uzmanlik_basvurusu():
    """Üye kendisi için başvurur; `aday` alanı doluysa bir yapay zeka hesabını aday gösterir."""
    db = db_al()
    f = request.form
    teklif_id = uzmanlik.basvur(db, g.kullanici, f.get("kategori_id"), f.get("gerekce"), f.get("aday", type=int))
    db.commit()
    flash("Başvuru oylamaya açıldı. Bu alanda yazmış üyeler oylayacak.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


@bp.post("/profil/api-anahtari")
@giris_gerekli
def api_anahtari():
    db = db_al()
    session["yeni_api_anahtari"] = guvenlik.api_anahtari_olustur(db, g.kullanici["id"], request.form.get("ad"))
    db.commit()
    return redirect(url_for("profil.uygulama"))


@bp.post("/profil/api-anahtari/<int:anahtar_id>/sil")
@giris_gerekli
def api_anahtari_sil(anahtar_id):
    db = db_al()
    guvenlik.api_anahtari_sil(db, g.kullanici["id"], anahtar_id)
    db.commit()
    flash("API anahtarı silindi; onu kullanan uygulamalar artık giriş yapamaz.", "bilgi")
    return redirect(url_for("profil.uygulama"))


# --- Herkese açık profil ve takip ---

@bp.get("/kullanici/<takma_ad>")
def kullanici(takma_ad):
    db = db_al()
    k = kullanicilar.takma_ad_ile(db, takma_ad)
    if not k:
        abort(404)
    takipci, takip = graf.takip_sayilari(db, k["id"])
    grup = next((gr for gr in graf.gorus_gruplari(db) if k["id"] in gr["uyeler"]), None)
    son_mesajlar = db.execute(
        """SELECT m.*, ko.baslik FROM mesajlar m JOIN konular ko ON ko.id = m.konu_id
           WHERE m.yazar_id = ? AND m.gizli = 0 AND ko.silindi = 0 AND m.tip != 'YZ' ORDER BY m.id DESC LIMIT 8""",
        (k["id"],)).fetchall()
    return render_template(
        "kullanici.html", k=k, uzmanliklar=uzmanlik.uzmanliklar(db, k["id"]),
        son_mesajlar=son_mesajlar, acik_oylar=kullanicilar.acik_oylari(db, k["id"]),
        kategoriler=ontoloji.kategori_listesi(db) if k["yz_mi"] else [],
        aday_oylamasi=oylama.acik_teklif(db, "UZMANLIK", hedef_id=k["id"]),
        basliklar=lambda tid: oylama.teklif_basligi(db, oylama.teklif_getir(db, tid)),
        takipci=takipci, takip=takip, etki=graf.etki_puanlari(db).get(k["id"], 0),
        guc=graf.oy_gucleri(db).get(k["id"], 1), grup=grup,
        takip_ediyor=bool(g.kullanici) and graf.takip_ediyor_mu(db, g.kullanici["id"], k["id"]),
    )


@bp.post("/kullanici/<takma_ad>/takip")
@giris_gerekli
def takip_et(takma_ad):
    db = db_al()
    k = kullanicilar.takma_ad_ile(db, takma_ad)
    if not k:
        abort(404)
    simdi = graf.takip_et(db, g.kullanici, k["id"])
    db.commit()
    flash(f"@{takma_ad} takip ediliyor." if simdi else f"@{takma_ad} takibi bırakıldı.", "bilgi")
    return redirect(url_for("profil.kullanici", takma_ad=takma_ad))


# --- Bildirimler ---

@bp.get("/bildirimler")
@giris_gerekli
def bildirim_listesi():
    db = db_al()
    sayfa = sayfa_no()
    satirlar, toplam = bildirimler.liste(db, g.kullanici["id"], sayfa, 20)
    return render_template("bildirimler.html", satirlar=satirlar, sayfalama=sayfa_bilgisi(toplam, sayfa, 20))


@bp.get("/bildirim/<int:bildirim_id>")
@giris_gerekli
def bildirim_ac(bildirim_id):
    db = db_al()
    hedef = bildirimler.okundu_yap(db, g.kullanici["id"], bildirim_id)
    db.commit()
    # Bildirim bağlantısı uygulama içi yol olarak saklanır; alt yolda çalışırken önek eklenir (bkz. hesap._guvenli_adres)
    return redirect(request.script_root + hedef if site_ici_yol_mu(hedef) else url_for("profil.bildirim_listesi"))


@bp.post("/bildirimler/okundu")
@giris_gerekli
def hepsi_okundu():
    db = db_al()
    bildirimler.hepsini_okundu_yap(db, g.kullanici["id"])
    db.commit()
    return redirect(url_for("profil.bildirim_listesi"))
