"""REST API (v1) — mobil uygulama ve dış istemciler için.

Kimlik doğrulama: POST /api/v1/giris ile alınan anahtar `Authorization: Bearer <anahtar>` başlığıyla gönderilir.
Tarayıcıdan (oturum çereziyle) yapılan POST isteklerinde `X-CSRF-Token` başlığı gerekir.
Kişisel veriler (ad, doğum tarihi, adres) API'de hiçbir zaman döndürülmez.
"""
import json

from flask import Blueprint, g, jsonify, request

from .. import (anlik, arama, ayarlar, bildirimler, gundem, kategoriler, defter, graf, guvenlik, kararlar, konular, kullanicilar,
                ontoloji, oylama, uygunluk, yonetmelik)
from ..hatalar import KuralHatasi
from . import db_al, giris_gerekli

bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _veri():
    return request.get_json(silent=True) or request.form.to_dict()


def _yurttas(k):
    if not k:
        return None
    return {"takma_ad": k["takma_ad"], "yz": bool(k["yz_mi"]), "yonetici": bool(k["yonetici_mi"])}


def _konu(db, k, detay=False):
    d = {"id": k["id"], "ust_id": k["ust_id"], "baslik": k["baslik"], "durum": k["durum"],
         "durum_adi": ayarlar.KONU_DURUMLARI[k["durum"]], "kategori": ontoloji.yol_metni(db, "kategoriler", k["kategori_id"]),
         "katilim_kurali": uygunluk.kural_metni(db, k), "tur": k["tur"], "tartisma_bitis": k["tartisma_bitis"],
         "itiraz_id": k["itiraz_id"], "uzman_agirlik": k["bilirkisi_agirlik"], "olusturma": k["olusturma"]}
    if detay:
        u = uygunluk.uygunluk(db, g.kullanici, k)
        d.update(aciklama=k["aciklama"], denetim=json.loads(k["denetim"]) if k["denetim"] else None,
                 rolum="KATILIMCI" if u.katilimci else "GOZLEMCI", uygunluk_puani=round(u.puan, 2))
    return d


def _teklif(db, t):
    d = {"id": t["id"], "tip": t["tip"], "baslik": oylama.teklif_basligi(db, t), "durum": t["durum"], "esik": t["esik"],
         "konu_id": t["konu_id"], "tur": t["tur_no"], "baslangic": t["baslangic"], "bitis": t["bitis"]}
    if t["tip"] == "KARAR":
        d["secenekler"] = [{"id": str(s["id"]), "metin": s["metin"]} for s in oylama.secenekler(db, t["id"])]
        d["secenekler"].append({"id": oylama.CEKIMSER, "metin": ayarlar.SECIM_ADLARI[oylama.CEKIMSER]})
    else:
        d["secenekler"] = [{"id": s, "metin": ayarlar.SECIM_ADLARI[s]} for s in oylama.EVET_HAYIR]
    if t["durum"] != "ACIK" and t["sonuc"]:
        s = json.loads(t["sonuc"])
        d["sonuc"] = {k: s.get(k) for k in ("secenekler", "cekimser", "agirlik_oran", "kisi_oran", "yeter", "katilan",
                                            "hak_sahibi", "acik_oylar")}
    if g.kullanici:
        durum = oylama.oy_durumu(db, t, g.kullanici)
        d["benim"] = {"verebilir": durum["verebilir"], "agirlik": durum["agirlik"], "aciklama": durum["aciklama"],
                      "oy_verdim": durum["oy"] is not None}
    return d


@bp.get("")
def bilgi():
    return jsonify(ad=ayarlar.SITE_ADI + " API", surum=1, belgeler="/api-belgeleri")


@bp.post("/giris")
def giris():
    db = db_al()
    v = _veri()
    k = kullanicilar.giris(db, v.get("takma_ad"), v.get("sifre"), request.remote_addr or "")
    anahtar = guvenlik.api_anahtari_olustur(db, k["id"], v.get("cihaz") or "Mobil uygulama")
    db.commit()
    return jsonify(anahtar=anahtar, yurttas=_yurttas(k)), 201


# --- Anlık bildirim aboneliği (tarayıcı ve Android uygulaması) ---

@bp.get("/anlik")
def anlik_bilgi():
    db = db_al()
    d = anlik.durum(db)
    return jsonify(web=d["web"], fcm=d["fcm"], vapid=anlik.vapid_acik_anahtar(db) if d["web"] else None)


@bp.post("/anlik/abone")
@giris_gerekli
def anlik_abone():
    db = db_al()
    v = _veri()
    anlik.abone_ol(db, g.kullanici, v.get("tur"), v.get("abonelik") or {"token": v.get("token")}, v.get("cihaz"))
    db.commit()
    return jsonify(tamam=True), 201


@bp.post("/anlik/ayril")
@giris_gerekli
def anlik_ayril():
    db = db_al()
    anlik.abonelikten_cik(db, g.kullanici, _veri().get("adres"))
    db.commit()
    return jsonify(tamam=True)


@bp.get("/ben")
@giris_gerekli
def ben():
    db = db_al()
    return jsonify(yurttas=_yurttas(g.kullanici), bekleyen_oy=oylama.bekleyen_oy_sayisi(db, g.kullanici),
                   okunmamis_bildirim=bildirimler.okunmamis_sayisi(db, g.kullanici["id"]))


@bp.get("/konular")
def konu_listesi():
    db = db_al()
    durum = request.args.get("durum")
    liste = konular.konu_listesi(db, durumlar=[durum] if durum else None)
    return jsonify(konular=[_konu(db, k) for k in liste])


@bp.get("/konular/<int:konu_id>")
def konu_detay(konu_id):
    db = db_al()
    k = konular.konu_getir(db, konu_id)
    if k["silindi"]:
        return jsonify(hata="Konu kaldırıldı.", notu=k["silinme_notu"]), 410
    mesajlar = db.execute("""SELECT m.*, u.takma_ad FROM mesajlar m LEFT JOIN kullanicilar u ON u.id = m.yazar_id
                             WHERE m.konu_id = ? ORDER BY m.id""", (konu_id,)).fetchall()
    return jsonify(
        konu=_konu(db, k, detay=True),
        alt_konular=[_konu(db, a) for a in konular.konu_listesi(db, konu_id)],
        mesajlar=[{"id": m["id"], "ust_id": m["ust_mesaj_id"], "tip": m["tip"], "yazar": m["takma_ad"],
                   "icerik": None if m["gizli"] else m["icerik"], "gizli": bool(m["gizli"]),
                   "not": m["gizlenme_notu"], "zaman": m["olusturma"]} for m in mesajlar],
        fikirler=[{"id": f["id"], "yazar": f["takma_ad"], "metin": f["icerik"]} for f in konular.fikirler(db, konu_id)],
        oylamalar=[_teklif(db, t) for t in oylama.konu_teklifleri(db, konu_id)])


@bp.post("/konular")
@giris_gerekli
def konu_ac():
    db = db_al()
    v = _veri()
    konu_id = konular.konu_ac(db, g.kullanici, v, v.get("ust_id"), v.get("itiraz_id"))
    db.commit()
    return jsonify(id=konu_id, konu=_konu(db, konular.konu_getir(db, konu_id), detay=True)), 201


@bp.post("/denetim")
@giris_gerekli
def denetim():
    """Konuyu açmadan yönetmelik denetimini çalıştırır (formdaki "Denetle" düğmesi bunu kullanır)."""
    db = db_al()
    v = _veri()
    ust_id = v.get("ust_id") or v.get("ust")
    rapor = konular.denetim_onizleme(db, v, int(ust_id) if ust_id else None)
    return jsonify(rapor)


@bp.post("/konular/<int:konu_id>/mesajlar")
@giris_gerekli
def mesaj_yaz(konu_id):
    db = db_al()
    v = _veri()
    mesaj_id = konular.mesaj_yaz(db, g.kullanici, konu_id, v.get("tip", "ARGUMAN"), v.get("icerik"),
                                 v.get("ust_mesaj_id"))
    db.commit()
    return jsonify(id=mesaj_id), 201


@bp.post("/konular/<int:konu_id>/fikir")
@giris_gerekli
def fikir_yaz(konu_id):
    """Kişi başı bir fikir: tartışma ve 1. tur boyunca yazılabilir."""
    db = db_al()
    mesaj_id = konular.fikir_yaz(db, g.kullanici, konu_id, _veri().get("icerik"))
    db.commit()
    return jsonify(id=mesaj_id), 201


@bp.get("/oylamalar")
def oylama_listesi():
    db = db_al()
    return jsonify(oylamalar=[_teklif(db, x["teklif"]) for x in oylama.acik_teklifler(db, 100)])


@bp.get("/oylamalar/<int:teklif_id>")
def oylama_detay(teklif_id):
    db = db_al()
    return jsonify(_teklif(db, oylama.teklif_getir(db, teklif_id)))


@bp.post("/oylamalar/<int:teklif_id>/oy")
@giris_gerekli
def oy_ver(teklif_id):
    db = db_al()
    v = _veri()
    makbuz = oylama.oy_ver(db, teklif_id, g.kullanici, str(v.get("secim", "")), v.get("gerekce"))
    db.commit()
    return jsonify(makbuz=makbuz, mesaj="Oyun kaydedildi. Makbuzla oyunun deftere yazıldığını doğrulayabilirsin."), 201


@bp.get("/kararlar")
def karar_listesi():
    db = db_al()
    return jsonify(kararlar=[{"id": k["id"], "konu_id": k["konu_id"], "konu": k["baslik"], "metin": k["metin"],
                              "durum": k["durum"], "tarih": k["olusturma"]}
                             for k in kararlar.tum_kararlar(db)])


@bp.get("/gundem")
def gundem_verisi():
    """Trend konular, öne çıkan kelimeler, kategori nabzı ve yakında bitenler."""
    db = db_al()
    trend, saat = gundem.trend_konular(db, 10)
    return jsonify(pencere_saat=saat, trend=[{k: t[k] for k in ("id", "baslik", "durum", "mesaj", "fikir", "oy", "kisi")}
                                             for t in trend],
                   kelimeler=gundem.anahtar_kelimeler(db), son_24_saat=gundem.son_24_saat(db),
                   nabiz=[{k: n[k] for k in ("id", "ad", "bu", "gecen", "degisim", "seri", "acik")}
                          for n in gundem.kategori_nabzi(db)],
                   yakinda=gundem.yakinda_bitenler(db, 6))


@bp.get("/kategoriler")
def kategori_listesi():
    db = db_al()
    return jsonify(kategoriler=[{k: s[k] for k in ("id", "ad", "ust_id", "yol", "kaynak", "konu", "acik", "hafta", "uzman")}
                                for s in kategoriler.liste(db, request.args.get("sirala", "populer"),
                                                           request.args.get("q", ""), request.args.get("suz", ""))])


@bp.post("/kategoriler")
@giris_gerekli
def kategori_oner():
    db = db_al()
    v = _veri()
    teklif_id = kategoriler.oner(db, g.kullanici, v.get("ad"), v.get("ust_id"), v.get("kavramlar"), v.get("gerekce"))
    db.commit()
    return jsonify(oylama_id=teklif_id), 201


@bp.get("/bildirimler")
@giris_gerekli
def bildirim_listesi():
    db = db_al()
    satirlar, _ = bildirimler.liste(db, g.kullanici["id"], 1, 50)
    return jsonify(bildirimler=[dict(b) for b in satirlar])


@bp.get("/defter")
def defter_durumu():
    db = db_al()
    bloklar, toplam = defter.bloklar(db.defter_klasoru, 1, 20)
    return jsonify(durum=defter.durum(db.defter_klasoru), toplam=toplam,
                   son_bloklar=[{k: b[k] for k in ("no", "zaman", "tur", "hash", "onceki", "veri_json")}
                                for b in bloklar])


@bp.get("/graf")
def graf_verisi():
    return jsonify(graf.graf_verisi(db_al()))


@bp.get("/yonetmelik")
def yonetmelik_verisi():
    db = db_al()
    return jsonify(maddeler=[{k: m[k] for k in ("kod", "tur", "baslik", "metin_goster", "ciddiyet", "korunan")}
                             for m in yonetmelik.maddeler(db)],
                   parametreler=[dict(p) for p in yonetmelik.parametre_listesi(db)])


@bp.get("/ara")
def ara():
    db = db_al()
    return jsonify(sonuclar=[{"tur": s["tur"], "konu_id": s["konu"]["id"], "konu": s["konu"]["baslik"],
                              "baglanti": s["baglanti"], "alinti": s["alinti"]}
                             for s in arama.ara(db, request.args.get("q", ""))])


@bp.errorhandler(KuralHatasi)
def kural_hatasi(e):
    db_al().rollback()
    return jsonify(hata=str(e)), 422
