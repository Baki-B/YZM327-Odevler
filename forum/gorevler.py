"""Zamanlanmış işler: tartışma süresi dolan konularda oylamayı başlatır, süresi dolan oylamaları sonuçlandırır.

`tick` her web isteğinde çağrılır; ayrıca `arka_plan_baslat` ile her 30 saniyede bir arka planda çalışır,
böylece kimse siteye girmese bile süreler işler. Durum geçişleri atomik olduğu için ikisi çakışmaz.
"""
import logging
import threading
import time

from . import konular, oylama, veritabani, zaman
from .hatalar import KuralHatasi
from .konu_durumlari import durumu

log = logging.getLogger(__name__)


def tick(db):
    """Süresi dolan işleri yürütür. Her iş kendi kayıt noktasında çalışır: biri hata verirse yalnızca o iş geri alınır
    ve günlüğe yazılır; diğerleri ve (tick her istekte çalıştığı için) sitenin geri kalanı etkilenmez."""
    simdi = zaman.simdi_metin()
    for k in db.execute("SELECT id FROM konular WHERE durum = 'TARTISMA' AND silindi = 0 AND tartisma_bitis <= ?",
                        (simdi,)).fetchall():
        _yalitilmis(db, f"#{k['id']} konusunun oylaması başlatılamadı", konular.oylamayi_baslat, k["id"])
    for t in db.execute("SELECT id FROM teklifler WHERE durum = 'ACIK' AND bitis <= ? ORDER BY id",
                        (simdi,)).fetchall():
        _yalitilmis(db, f"#{t['id']} numaralı oylama sonuçlandırılamadı", oylama.sonuclandir, t["id"])


def konuyu_ilerlet(db, konu_id):
    """Sunum kipi: konunun sıradaki zamanlanmış işini süresini beklemeden yürütür (tick'in tek konuluk hâli).
    Döner: konu."""
    konu = konular.konu_getir(db, konu_id)
    kod = durumu(konu).kod
    if kod == "TARTISMA":
        konular.oylamayi_baslat(db, konu_id)
    elif kod == "OYLAMA":
        t = oylama.acik_teklif(db, "KARAR", konu_id=konu_id)
        if t:
            oylama.sonuclandir(db, t["id"])
    else:
        raise KuralHatasi("Bu konu kapanmış.")
    return konu


def _yalitilmis(db, hata_metni, is_, *argumanlar):
    try:
        with db.kayit_noktasi("zamanlayici"):
            is_(db, *argumanlar)
    except Exception:
        log.exception(hata_metni)


def arka_plan_baslat(yol, aralik=30):
    def dongu():
        while True:
            db = veritabani.baglan(yol)
            try:
                tick(db)
                db.commit()
            except Exception:
                log.exception("Zamanlanmış iş başarısız")
                db.rollback()
            finally:
                db.close()
            time.sleep(aralik)

    threading.Thread(target=dongu, name="forum-zamanlayici", daemon=True).start()
