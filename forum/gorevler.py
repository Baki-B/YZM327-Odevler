"""Zamanlanmış işler: tartışma süresi dolan konularda oylamayı başlatır, süresi dolan oylamaları sonuçlandırır.

`tick` her web isteğinde çağrılır; ayrıca `arka_plan_baslat` ile her 30 saniyede bir arka planda çalışır,
böylece kimse siteye girmese bile süreler işler. Durum geçişleri atomik olduğu için ikisi çakışmaz.
"""
import logging
import threading
import time

from . import konular, oylama, veritabani, zaman

log = logging.getLogger(__name__)


def tick(db):
    simdi = zaman.simdi_metin()
    for k in db.execute("SELECT id FROM konular WHERE durum = 'TARTISMA' AND silindi = 0 AND tartisma_bitis <= ?",
                        (simdi,)).fetchall():
        konular.oylamayi_baslat(db, k["id"])
    for t in db.execute("SELECT id FROM teklifler WHERE durum = 'ACIK' AND bitis <= ? ORDER BY id",
                        (simdi,)).fetchall():
        oylama.sonuclandir(db, t["id"])


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
