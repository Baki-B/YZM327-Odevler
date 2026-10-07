import json

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .. import (ayarlar, devir, gundem, kararlar, kategoriler, konular, kullanicilar, ontoloji, oylama, sikayetler,
                uygunluk, yonetmelik, yz)
from ..hatalar import KuralHatasi
from . import db_al, giris_gerekli, sayfa_no
from .yardimcilar import sayfala

bp = Blueprint("konular", __name__)

FILTRELER = [("tumu", "Tümü"), ("katilabildiklerim", "Katılabildiğim"), ("gozlemci", "Gözlemci olduğum"),
             ("TARTISMA", "Tartışmada"), ("OYLAMA", "Oylamada"), ("KARARA_BAGLANDI", "Karara bağlananlar"),
             ("SONUCSUZ", "Sonuçsuz kapananlar")]


@bp.route("/")
def acilis():
    """Giriş katmanı: ziyaretçiye tanıtım sayfası, giriş yapmış üyeye doğrudan konu akışı."""
    if g.kullanici:
        return ana_sayfa()
    db = db_al()
    gundemdekiler = sorted((k for k in konular.konu_listesi(db) if k["durum"] in ayarlar.AKTIF_DURUMLAR),
                           key=lambda k: k["son_etkinlik"], reverse=True)[:3]
    return render_template("acilis.html", istatistik=konular.istatistikler(db), gundemdekiler=gundemdekiler)


@bp.route("/konular")
def ana_sayfa():
    db = db_al()
    filtre = request.args.get("filtre", "tumu")
    kategori = request.args.get("kategori", type=int)
    satirlar = []
    for k in konular.konu_listesi(db):
        u = uygunluk.uygunluk(db, g.kullanici, k)
        if filtre == "katilabildiklerim" and not u.katilimci:
            continue
        if filtre == "gozlemci" and u.katilimci:
            continue
        if filtre in ayarlar.KONU_DURUMLARI and k["durum"] != filtre:
            continue
        if kategori and not ontoloji.altinda_mi(db, "kategoriler", k["kategori_id"], kategori):
            continue
        satirlar.append({"konu": k, "uygunluk": u, "kural": uygunluk.kural_metni(db, k)})
    satirlar.sort(key=lambda s: s["konu"]["son_etkinlik"], reverse=True)
    parca, sayfalama = sayfala(satirlar, sayfa_no(), ayarlar.SAYFA_BOYU)
    yan = gundem.yan_panel(db)
    son_karar = gundem.son_kararlar(db, 1)
    return render_template("konular.html", satirlar=parca, sayfalama=sayfalama, filtre=filtre, filtreler=FILTRELER,
                           kategori=kategori, istatistik=konular.istatistikler(db), yan=yan,
                           gundemdekiler={t["id"] for t in yan["trend"][:3]}, son_karar=son_karar[0] if son_karar else None,
                           alt_kategoriler=[a for a in ontoloji.kategori_listesi(db) if kategori and
                                            ontoloji.dugum(db, "kategoriler", a[0])["ust_id"] == kategori],
                           kok_kategori=ontoloji.atalar(db, "kategoriler", kategori)[0] if kategori else None)


@bp.route("/kesfet")
def kesfet():
    return render_template("kesfet.html", g_=gundem.kesfet(db_al()))


@bp.route("/kategoriler")
def kategori_sayfasi():
    db = db_al()
    q, sirala, suz = request.args.get("q", "").strip(), request.args.get("sirala", "populer"), request.args.get("suz", "")
    duz = bool(q) or suz in ("alt", "topluluk")
    satirlar = kategoriler.liste(db, sirala, q, suz)
    if not duz:
        satirlar = [s for s in satirlar if s["ust_id"] is None]
    return render_template("kategoriler.html", satirlar=satirlar, duz=duz, q=q, sirala=sirala, suz=suz,
                           siralamalar=kategoriler.SIRALAMALAR, suzgecler=kategoriler.SUZGECLER,
                           oneriler=[{"t": t, "baslik": oylama.teklif_basligi(db, t), "veri": json.loads(t["veri"]),
                                      "oy": oylama.oy_sayisi(db, t["id"])}
                                     for t in kategoriler.oylama_suren_oneriler(db)],
                           sonuclananlar=[{"t": t, "baslik": oylama.teklif_basligi(db, t)} for t in kategoriler.son_oneriler(db, 6)],
                           ana_kategoriler=kategoriler.ana_kategoriler(db), toplam=len(db.execute("SELECT id FROM kategoriler").fetchall()),
                           form=request.args)


@bp.post("/kategori/oner")
@giris_gerekli
def kategori_oner():
    db = db_al()
    f = request.form
    teklif_id = kategoriler.oner(db, g.kullanici, f.get("ad"), f.get("ust_id"), f.get("kavramlar"), f.get("gerekce"))
    db.commit()
    flash("Kategori önerin oylamaya sunuldu. Bütün üyelere haber verildi.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


# --- Konu açma ve düzenleme ---

def _form_sayfasi(db, form, ust=None, itiraz=None):
    return render_template("konu_form.html", form=form, ust=ust, itiraz=itiraz,
                           kategoriler=ontoloji.kategori_listesi(db), konum_agaci=ontoloji.konum_agaci(db),
                           ust_kural=uygunluk.kural_metni(db, ust) if ust else None)


@bp.route("/konu/yeni", methods=["GET", "POST"])
@giris_gerekli
def konu_yeni():
    db = db_al()
    ust_id, itiraz_id = request.values.get("ust", type=int), request.values.get("itiraz", type=int)
    ust = konular.konu_getir(db, ust_id) if ust_id else None
    itiraz = konular.konu_getir(db, itiraz_id) if itiraz_id else None
    if request.method == "POST":
        try:
            konu_id = konular.konu_ac(db, g.kullanici, request.form, ust_id, itiraz_id)
        except KuralHatasi as e:
            db.rollback()
            flash(str(e), "hata")
            return _form_sayfasi(db, request.form, ust, itiraz)
        db.commit()
        flash(f"Konun açıldı. {yonetmelik.deger(db, 'SURE_TARTISMA_SAAT')} saat tartışıldıktan sonra fikir oylaması başlar.",
              "basari")
        return redirect(url_for("konular.konu", konu_id=konu_id))
    kaynak = ust or itiraz
    form = {"kategori_id": kaynak["kategori_id"] if kaynak else None}
    if itiraz:
        form.update(baslik=f"İtiraz: {itiraz['baslik']}"[:150], konum_id=itiraz["konum_id"], min_yas=itiraz["min_yas"],
                    max_yas=itiraz["max_yas"])
    return _form_sayfasi(db, form, ust, itiraz)


@bp.route("/konu/<int:konu_id>/duzenle", methods=["GET", "POST"])
@giris_gerekli
def konu_duzenle(konu_id):
    db = db_al()
    k = konular.konu_duzenleme_izni(db, g.kullanici, konu_id)
    if request.method == "POST":
        konular.konu_duzenle(db, g.kullanici, konu_id, request.form)
        db.commit()
        flash("Konu düzenlendi. Eski hâli konu geçmişinde duruyor.", "basari")
        return redirect(url_for("konular.konu", konu_id=konu_id))
    return render_template("konu_duzenle.html", konu=k)


# --- Konu sayfası ---

@bp.route("/konu/<int:konu_id>")
def konu(konu_id):
    db = db_al()
    k = konular.konu_getir(db, konu_id)
    zincir = uygunluk.konu_zinciri(db, k)
    if k["silindi"]:
        return render_template("konu_silindi.html", konu=k, zincir=zincir)
    ben = g.kullanici
    u = uygunluk.uygunluk(db, ben, k)
    baglam = uygunluk.konu_baglami(k)
    teklifler = oylama.konu_teklifleri(db, konu_id)
    tur = next((t for t in teklifler if t["tip"] == "KARAR" and t["durum"] == "ACIK"), None)

    # Fikirler ayrı listelenir; her fikrin altındaki yanıtlar onunla birlikte gösterilir.
    agac = konular.mesaj_agaci(db, konu_id)
    yarisanlar = {s["mesaj_id"] for s in oylama.secenekler(db, tur["id"])} if tur else set()
    karar = kararlar.konu_karari(db, konu_id)
    kazanan_mesaj = None
    if karar:
        r = db.execute("SELECT mesaj_id FROM secenekler WHERE id = ?", (karar["kazanan_secenek_id"],)).fetchone()
        kazanan_mesaj = r["mesaj_id"] if r else None
    fikirler = []
    for m in agac:
        if m["tip"] != "FIKIR":
            continue
        if kazanan_mesaj == m["id"]:
            m["fikir_durumu"] = "KAZANDI"
        elif k["durum"] == "OYLAMA" and k["tur"] > 1 and m["id"] not in yarisanlar and not m["gizli"]:
            m["fikir_durumu"] = "ELENDI"
        else:
            m["fikir_durumu"] = ""
        fikirler.append(m)

    benim_devrim = None
    if ben:
        alan_id, kapsam = devir.gecerli_devir(db, ben["id"], baglam)
        if alan_id:
            benim_devrim = {"takma_ad": kullanicilar.getir(db, alan_id)["takma_ad"], "kapsam": devir.KAPSAMLAR[kapsam]}
    katilimci = bool(ben) and u.katilimci
    return render_template(
        "konu.html", konu=k, zincir=zincir, uygunluk=u, kural=uygunluk.kural_metni(db, k),
        katilimci=katilimci, aktif=k["durum"] in ayarlar.AKTIF_DURUMLAR,
        sahibi=bool(ben) and ben["id"] == k["sahip_id"],
        agirlik=uygunluk.oy_agirligi(db, ben, baglam) if ben else (0, ""),
        sahip=kullanicilar.getir(db, k["sahip_id"]),
        alt_konular=konular.konu_listesi(db, konu_id),
        tur=tur, tur_durumu=oylama.oy_durumu(db, tur, ben) if tur else None,
        diger_acik=[t for t in teklifler if t["durum"] == "ACIK" and t["tip"] != "KARAR"],
        kapali_teklifler=[t for t in teklifler if t["durum"] != "ACIK"][:8],
        basliklar={t["id"]: oylama.teklif_basligi(db, t) for t in teklifler},
        karar=karar, karar_sonucu=oylama.sonuc(oylama.teklif_getir(db, karar["teklif_id"])) if karar else None,
        fikirler=fikirler, mesajlar=[m for m in agac if m["tip"] != "FIKIR"],
        fikir_yazilabilir=katilimci and konular.fikir_yazilabilir_mi(k)
        and not konular.kullanicinin_fikri(db, konu_id, ben["id"]),
        benim_fikrim=konular.kullanicinin_fikri(db, konu_id, ben["id"]) if ben else None,
        denetim=json.loads(k["denetim"]) if k["denetim"] else None,
        itiraz_edilen=konular.konu_getir(db, k["itiraz_id"]) if k["itiraz_id"] else None,
        itirazlar=konular.itirazlar(db, konu_id),
        surum_sayisi=len(konular.konu_surumleri(db, konu_id)), benim_devrim=benim_devrim,
        yz_var=bool(yz.asistan(db)),
    )


@bp.post("/konu/<int:konu_id>/kaldir")
@giris_gerekli
def kaldir(konu_id):
    db = db_al()
    teklif_id = konular.kaldirma_teklifi(db, g.kullanici, konu_id, request.form.get("gerekce"))
    db.commit()
    flash(f"Kaldırma önerin oylamaya açıldı ({yonetmelik.parametre_metni(db, 'ESIK_KONU_SILME')} gerekiyor).", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


@bp.get("/konu/<int:konu_id>/gecmis")
def konu_gecmisi(konu_id):
    db = db_al()
    return render_template("konu_gecmis.html", konu=konular.okunur_konu(db, konu_id),
                           surumler=konular.konu_surumleri(db, konu_id))


@bp.post("/konu/<int:konu_id>/ozet")
@giris_gerekli
def ozet_iste(konu_id):
    db = db_al()
    yz.ozet_iste(db, g.kullanici, konu_id)
    db.commit()
    return redirect(url_for("konular.konu", konu_id=konu_id, _anchor="mesajlar"))


# --- Fikirler ve mesajlar ---

@bp.post("/konu/<int:konu_id>/fikir")
@giris_gerekli
def fikir_yaz(konu_id):
    db = db_al()
    mesaj_id = konular.fikir_yaz(db, g.kullanici, konu_id, request.form.get("icerik"))
    db.commit()
    flash("Fikrin eklendi. Oylamada seçenek olarak yer alacak.", "basari")
    return redirect(url_for("konular.konu", konu_id=konu_id, _anchor=f"m{mesaj_id}"))


@bp.post("/konu/<int:konu_id>/mesaj")
@giris_gerekli
def mesaj_yaz(konu_id):
    db = db_al()
    f = request.form
    mesaj_id = konular.mesaj_yaz(db, g.kullanici, konu_id, f.get("tip"), f.get("icerik"), f.get("ust_mesaj_id"))
    db.commit()
    return redirect(url_for("konular.konu", konu_id=konu_id, _anchor=f"m{mesaj_id}"))


@bp.route("/mesaj/<int:mesaj_id>/duzenle", methods=["GET", "POST"])
@giris_gerekli
def mesaj_duzenle(mesaj_id):
    db = db_al()
    m = konular.mesaj_duzenleme_izni(db, g.kullanici, mesaj_id)
    if request.method == "POST":
        konular.mesaj_duzenle(db, g.kullanici, mesaj_id, request.form.get("icerik"))
        db.commit()
        flash("Mesaj düzenlendi. Eski hâli mesaj geçmişinde herkese görünür.", "basari")
        return redirect(url_for("konular.konu", konu_id=m["konu_id"], _anchor=f"m{mesaj_id}"))
    return render_template("mesaj_duzenle.html", mesaj=m)


@bp.get("/mesaj/<int:mesaj_id>/gecmis")
def mesaj_gecmisi(mesaj_id):
    db = db_al()
    m = konular.okunur_mesaj(db, mesaj_id)
    return render_template("mesaj_gecmis.html", mesaj=m, surumler=konular.mesaj_surumleri(db, mesaj_id))


@bp.post("/konu/<int:konu_id>/gizle")
@giris_gerekli
def toplu_gizle(konu_id):
    """Tartışmanın bir kısmını (birden fazla mesajı) tek oylamayla gizleme teklifi."""
    db = db_al()
    teklif_id = konular.mesaj_silme_teklifi(db, g.kullanici, request.form.getlist("mesaj"), request.form.get("neden"),
                                            request.form.get("aciklama"))
    db.commit()
    flash("Seçtiğin mesajlar için gizleme oylaması açıldı.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


@bp.post("/mesaj/<int:mesaj_id>/gizle")
@giris_gerekli
def mesaj_gizle(mesaj_id):
    db = db_al()
    teklif_id = konular.mesaj_silme_teklifi(db, g.kullanici, mesaj_id, request.form.get("neden"),
                                            request.form.get("aciklama"))
    db.commit()
    flash("Gizleme oylaması açıldı. Mesaj silinmez; kabul edilirse gizlenir.", "basari")
    return redirect(url_for("oylamalar.teklif", teklif_id=teklif_id))


# --- Şikayet ---

def _sikayet_mesaji(kalan):
    if kalan:
        return f"Şikayetin kaydedildi. {kalan} üye daha şikayet ederse yöneticilere ulaşır."
    return "Şikayetin kaydedildi ve yöneticilere ulaştı. Sonuçlanınca bildirim alacaksın."


@bp.post("/mesaj/<int:mesaj_id>/sikayet")
@giris_gerekli
def mesaj_sikayet(mesaj_id):
    db = db_al()
    m = konular.mesaj_getir(db, mesaj_id)
    _, kalan = sikayetler.sikayet_et(db, g.kullanici, "MESAJ", mesaj_id, request.form.get("neden"),
                                     request.form.get("aciklama"))
    db.commit()
    flash(_sikayet_mesaji(kalan), "basari")
    return redirect(url_for("konular.konu", konu_id=m["konu_id"], _anchor=f"m{mesaj_id}"))


@bp.post("/konu/<int:konu_id>/sikayet")
@giris_gerekli
def konu_sikayet(konu_id):
    db = db_al()
    _, kalan = sikayetler.sikayet_et(db, g.kullanici, "KONU", konu_id, request.form.get("neden"),
                                     request.form.get("aciklama"))
    db.commit()
    flash(_sikayet_mesaji(kalan), "basari")
    return redirect(url_for("konular.konu", konu_id=konu_id))
