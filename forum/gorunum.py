"""Konu sayfasının görünüm verisi — GoF **Facade**.

Bir konu sayfası yedi alt sistemden veri ister: konular, uygunluk, oylama, kararlar, devir, kullanıcılar ve
yapay zeka. Web rotası bu sayfa için yalnızca `konu_sayfasi()` işlevini bilir; alt sistemler değişirse rota
değişmez. İş kuralı (`fikir_durumu`) saf bir işlevdir ve Flask olmadan test edilir.
"""
import json

from . import devir, kararlar, konular, kullanicilar, oylama, uygunluk, yz
from .konu_durumlari import durumu

KAZANDI, ELENDI = "KAZANDI", "ELENDI"


def fikir_durumu(fikir, konu, yarisanlar, kazanan_mesaj_id):
    """Bir fikrin konu sayfasındaki rozeti: KAZANDI, ELENDI ya da "" (yarışıyor / henüz oylama yok).
    yarisanlar: açık turdaki seçeneklerin mesaj numaraları. 1. turda bütün fikirler yarışır; gizlenen fikir
    "elendi" diye gösterilmez (oylamayla gizlendiği ayrıca yazılır)."""
    if kazanan_mesaj_id == fikir["id"]:
        return KAZANDI
    if konu["durum"] == "OYLAMA" and konu["tur"] > 1 and fikir["id"] not in yarisanlar and not fikir["gizli"]:
        return ELENDI
    return ""


def _kazanan_mesaj(db, karar):
    if not karar:
        return None
    r = db.execute("SELECT mesaj_id FROM secenekler WHERE id = ?", (karar["kazanan_secenek_id"],)).fetchone()
    return r["mesaj_id"] if r else None


def _benim_devrim(db, ben, baglam):
    if not ben:
        return None
    alan_id, kapsam = devir.gecerli_devir(db, ben["id"], baglam)
    if not alan_id:
        return None
    return {"takma_ad": kullanicilar.getir(db, alan_id)["takma_ad"], "kapsam": devir.KAPSAMLAR[kapsam]}


def konu_sayfasi(db, ben, konu_id):
    """Döner: (şablon adı, şablon değişkenleri)."""
    k = konular.konu_getir(db, konu_id)
    zincir = uygunluk.konu_zinciri(db, k)
    if k["silindi"]:
        return "konu_silindi.html", {"konu": k, "zincir": zincir}

    u = uygunluk.uygunluk(db, ben, k)
    baglam = uygunluk.konu_baglami(k)
    teklifler = oylama.konu_teklifleri(db, konu_id)
    tur = next((t for t in teklifler if t["tip"] == "KARAR" and t["durum"] == "ACIK"), None)
    karar = kararlar.konu_karari(db, konu_id)

    # Fikirler ayrı listelenir; her fikrin altındaki yanıtlar onunla birlikte gösterilir.
    agac = konular.mesaj_agaci(db, konu_id)
    yarisanlar = {s["mesaj_id"] for s in oylama.secenekler(db, tur["id"])} if tur else set()
    kazanan = _kazanan_mesaj(db, karar)
    fikirler = [dict(m, fikir_durumu=fikir_durumu(m, k, yarisanlar, kazanan)) for m in agac if m["tip"] == "FIKIR"]

    katilimci = bool(ben) and u.katilimci
    benim_fikrim = konular.kullanicinin_fikri(db, konu_id, ben["id"]) if ben else None
    return "konu.html", {
        "konu": k, "zincir": zincir, "uygunluk": u, "kural": uygunluk.kural_metni(db, k),
        "katilimci": katilimci, "durum": durumu(k), "aktif": durumu(k).yazilabilir,
        "sahibi": bool(ben) and ben["id"] == k["sahip_id"],
        "agirlik": uygunluk.oy_agirligi(db, ben, baglam) if ben else (0, ""),
        "sahip": kullanicilar.getir(db, k["sahip_id"]),
        "alt_konular": konular.konu_listesi(db, konu_id),
        "tur": tur, "tur_durumu": oylama.oy_durumu(db, tur, ben) if tur else None,
        "diger_acik": [t for t in teklifler if t["durum"] == "ACIK" and t["tip"] != "KARAR"],
        "kapali_teklifler": [t for t in teklifler if t["durum"] != "ACIK"][:8],
        "basliklar": {t["id"]: oylama.teklif_basligi(db, t) for t in teklifler},
        "karar": karar,
        "karar_sonucu": oylama.sonuc(oylama.teklif_getir(db, karar["teklif_id"])) if karar else None,
        "fikirler": fikirler, "mesajlar": [m for m in agac if m["tip"] != "FIKIR"],
        "fikir_yazilabilir": katilimci and konular.fikir_yazilabilir_mi(k) and not benim_fikrim,
        "benim_fikrim": benim_fikrim,
        "denetim": json.loads(k["denetim"]) if k["denetim"] else None,
        "itiraz_edilen": konular.konu_getir(db, k["itiraz_id"]) if k["itiraz_id"] else None,
        "itirazlar": konular.itirazlar(db, konu_id),
        "surum_sayisi": len(konular.konu_surumleri(db, konu_id)),
        "benim_devrim": _benim_devrim(db, ben, baglam),
        "yz_var": bool(yz.asistan(db)),
    }
