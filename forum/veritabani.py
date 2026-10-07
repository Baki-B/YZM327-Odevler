"""Veritabanı bağlantısı.

Bağlantı nesnesi iki iş daha yapar:
  * Ontoloji tablolarını (konum, kategori) önbellekte tutar.
  * İşlemin (transaction) yan etkilerini (deftere yazılacak bloklar, anlık bildirimler, arka plan işleri) kuyrukta
    biriktirir. Yan etkiler SADECE işlem başarıyla kaydedilince (commit) gerçekleşir; geri alınan (rollback) işlemin
    kuyruğu silinir.

GoF **Observer**: "işlem kaydedildi" olayına abone olunur (`commit_aboneligi`). Bu modül, olayı dinleyen üst
katman modüllerini (ör. defter) tanımaz; onları içe aktarmaz (DIP). Abonelik, abone modül yüklenince yapılır.
"""
import logging
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from . import zaman

SEMA = Path(__file__).with_name("schema.sql")
SURUM = 2
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class KuyrukHatirasi:
    """Memento: bağlantının işlem sonrası kuyruklarının bir andaki boyu. Kayıt noktasına geri dönülünce
    kuyruklar bu boya kısaltılır; böylece geri alınan bloğun deftere ya da telefona gidecek yan etkileri de silinir."""
    defter: int
    commit_sonrasi: int
    anlik: object          # None (kuyruk yoktu) ya da boyu


_COMMIT_ABONELERI = []


def commit_aboneligi(abone):
    """Observer aboneliği (dekoratör olarak da kullanılır): abone(db), her başarılı commit'ten sonra çağrılır."""
    if abone not in _COMMIT_ABONELERI:
        _COMMIT_ABONELERI.append(abone)
    return abone


class Baglanti(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.onbellek = {}
        self.defter_kuyrugu = []
        self.defter_klasoru = None
        self.yol = None
        self.commit_sonrasi = []      # işlem kaydedilince çalışacak işler (ör. arka plan YZ görevleri)
        self.anlik_kuyrugu = None     # işlem kaydedilince gönderilecek anlık bildirimler (anlik.py)

    def commit(self):
        super().commit()
        # Veri artık kalıcı. Yan etkilerden biri başarısız olsa bile istek hata vermez (kullanıcı işlemini tekrar
        # denerse çift kayıt oluşurdu); hata günlüğe yazılır.
        for abone in list(_COMMIT_ABONELERI):
            try:
                abone(self)
            except Exception:
                log.exception("Commit abonesi başarısız: %s", getattr(abone, "__qualname__", abone))
        isler, self.commit_sonrasi = self.commit_sonrasi, []
        for is_ in isler:
            try:
                is_()
            except Exception:
                log.exception("İşlem sonrası iş başarısız")

    def rollback(self):
        super().rollback()
        self.defter_kuyrugu = []
        self.commit_sonrasi = []
        self.anlik_kuyrugu = None
        self.onbellek.clear()      # geri alınan işlemin önbelleğe aldığı değerler (ör. değişmiş parametre) kalmasın

    def __exit__(self, tur, deger, iz):
        """`with db:` da kendi commit/rollback'imizden geçsin (yoksa sqlite3 yan etki kuyruklarını atlardı)."""
        if tur is None:
            self.commit()
        else:
            self.rollback()
        return False

    # --- Kayıt noktası (SAVEPOINT) ---

    def hatira(self):
        return KuyrukHatirasi(len(self.defter_kuyrugu), len(self.commit_sonrasi),
                              None if self.anlik_kuyrugu is None else len(self.anlik_kuyrugu))

    def hatiraya_don(self, h):
        del self.defter_kuyrugu[h.defter:]
        del self.commit_sonrasi[h.commit_sonrasi:]
        if h.anlik is None:
            self.anlik_kuyrugu = None
        elif self.anlik_kuyrugu is not None:
            del self.anlik_kuyrugu[h.anlik:]
        self.onbellek.clear()      # geri alınan bloğun okuduğu/yazdığı önbellek değerleri de geçersiz

    @contextmanager
    def kayit_noktasi(self, ad="nokta"):
        """Blok hata verirse yalnızca o bloğun veritabanı değişiklikleri ve kuyruğa eklediği yan etkiler geri alınır;
        dış işlem (transaction) sürer. Zamanlayıcı her konuyu ve oylamayı ayrı bir kayıt noktasında işler."""
        if not self.in_transaction:
            self.execute("BEGIN IMMEDIATE")
        h = self.hatira()
        self.execute(f"SAVEPOINT {ad}")
        try:
            yield
        except BaseException:
            self.execute(f"ROLLBACK TO {ad}")
            self.execute(f"RELEASE {ad}")
            self.hatiraya_don(h)
            raise
        self.execute(f"RELEASE {ad}")


def defter_klasoru(yol):
    return os.path.join(os.path.dirname(os.path.abspath(yol)), "defter")


def baglan(yol):
    db = sqlite3.connect(yol, factory=Baglanti, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 10000")
    db.defter_klasoru = defter_klasoru(yol)
    db.yol = yol
    return db


def hazirla(yol):
    """Şemayı kurar. Eski sürüm bir veritabanı varsa yedekleyip yenisini oluşturur."""
    if os.path.exists(yol):
        db = sqlite3.connect(yol)
        surum = db.execute("PRAGMA user_version").fetchone()[0]
        db.close()
        if surum != SURUM:
            yedek = f"{yol}.eski-{zaman.simdi():%Y%m%d%H%M%S}"
            os.replace(yol, yedek)
            log.warning("Eski sürüm veritabanı %s olarak yedeklendi, yenisi oluşturuluyor.", yedek)
    db = baglan(yol)
    db.execute("PRAGMA journal_mode = WAL")
    db.executescript(SEMA.read_text(encoding="utf-8"))
    _sutunlari_esitle(db)
    return db


# Sürüm 2 içinde sonradan eklenen / kaldırılan sütunlar. Kurulu veritabanı silinmeden yerinde güncellenir.
EK_SUTUNLAR = [("kullanicilar", "askida_bitis", "TEXT"), ("kullanicilar", "askida_neden", "TEXT"),
               ("kategoriler", "renk", "TEXT"), ("konular", "itiraz_id", "INTEGER"),
               ("konular", "tur", "INTEGER NOT NULL DEFAULT 0"), ("konular", "tartisma_bitis", "TEXT"),
               ("kategoriler", "kaynak", "TEXT NOT NULL DEFAULT 'SISTEM'"), ("kategoriler", "kavramlar", "TEXT"),
               ("kategoriler", "olusturma", "TEXT"), ("kullanicilar", "oturum_surumu", "INTEGER NOT NULL DEFAULT 0")]
KALKAN_SUTUNLAR = [("parametreler", "abd")]


def _sutunlari_esitle(db):
    def sutunlar(tablo):
        return {r[1] for r in db.execute(f"PRAGMA table_info({tablo})")}
    for tablo, sutun, tur in EK_SUTUNLAR:
        if sutun not in sutunlar(tablo):
            db.execute(f"ALTER TABLE {tablo} ADD COLUMN {sutun} {tur}")
    for tablo, sutun in KALKAN_SUTUNLAR:
        if sutun in sutunlar(tablo):
            db.execute(f"ALTER TABLE {tablo} DROP COLUMN {sutun}")
    _yeni_akisa_gecir(db)
    try:   # kişi başı tek (yarışan) fikir kuralı veri katmanında da korunur; eski bir kopya varsa kurulum durmaz
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS tek_fikir ON mesajlar (konu_id, yazar_id) "
                   "WHERE tip = 'FIKIR' AND gizli = 0")
    except sqlite3.IntegrityError:
        log.warning("Aynı konuda birden fazla fikri olan üye var; tek_fikir dizini oluşturulamadı.")
    db.commit()


def _yeni_akisa_gecir(db):
    """Eski akıştan (komisyon → genel kurul → karar → erteleme) kalan kayıtları yeni akışa uyarlar. Bir kez çalışır;
    üyelere, mesajlara ve geçmiş oylamalara dokunmaz.
      * Süren eski oylamalar iptal edilir; açık konular tartışmaya döner ve süreleri baştan başlar.
      * Geçici kararlar kesinleşir; reddedilen ve uzlaşılamayan konular "sonuçsuz" olur.
      * Mesaj gizleme ve konu kaldırma eşiği dörtte üçe çıkar."""
    eski = "'KOMISYON', 'GENEL_KURUL', 'REDDEDILDI', 'KARAR_GECICI', 'KAPANIS', 'UZLASMA_YOK'"
    bilirkisi = db.execute("SELECT COUNT(*) FROM teklifler WHERE tip = 'BILIRKISI'").fetchone()[0]
    if not bilirkisi and not db.execute(f"SELECT COUNT(*) FROM konular WHERE durum IN ({eski})").fetchone()[0] \
            and not db.execute("SELECT COUNT(*) FROM konular WHERE durum IN ('TARTISMA', 'OYLAMA') "
                               "AND tartisma_bitis IS NULL").fetchone()[0]:
        return
    simdi = zaman.simdi()
    an, bitis = zaman.metin(simdi), zaman.metin(simdi + timedelta(hours=24))
    db.execute("UPDATE teklifler SET tip = 'UZMANLIK' WHERE tip = 'BILIRKISI'")
    db.execute("UPDATE teklifler SET durum = 'IPTAL', kapanis = ? WHERE durum = 'ACIK' AND (tip IN "
               "('KONU_KABUL', 'KAPANIS', 'KONU_DUZENLEME') OR (tip = 'KARAR' AND konu_id IN "
               "(SELECT id FROM konular WHERE tartisma_bitis IS NULL)))", (an,))
    db.execute("UPDATE kararlar SET durum = 'KESIN', kesinlesme = COALESCE(kesinlesme, ?) WHERE durum = 'GECICI'", (an,))
    db.execute("UPDATE konular SET durum = 'KARARA_BAGLANDI' WHERE durum IN ('KARAR_GECICI', 'KAPANIS')")
    db.execute("UPDATE konular SET durum = 'SONUCSUZ' WHERE durum = 'REDDEDILDI'")
    db.execute("UPDATE konular SET durum = 'TARTISMA', tur = 0, tartisma_bitis = ? WHERE durum IN "
               "('KOMISYON', 'GENEL_KURUL', 'UZLASMA_YOK') OR (durum IN ('TARTISMA', 'OYLAMA') AND tartisma_bitis IS NULL)",
               (bitis,))
    # Gizleme ve kaldırma artık dörtte üç ister (eski kurulumlarda üçte iki kalmış olabilir).
    db.execute("UPDATE parametreler SET deger = 'DORTTE_UC' WHERE kod IN ('ESIK_MESAJ_SILME', 'ESIK_KONU_SILME')")
    log.warning("Veritabanı yeni konu akışına uyarlandı.")
