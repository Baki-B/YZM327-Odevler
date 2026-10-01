"""Şeffaflık günlüğü: forumda olan her önemli olay kayıt altına alınır."""
from . import zaman


def kaydet(db, kullanici_id, eylem, detay):
    db.execute(
        "INSERT INTO gunluk (kullanici_id, eylem, detay, zaman) VALUES (?, ?, ?, ?)",
        (kullanici_id, eylem, detay, zaman.simdi_metin()),
    )


def son_kayitlar(db, limit=300):
    return db.execute(
        """SELECT g.*, k.takma_ad, k.yz_mi FROM gunluk g
           LEFT JOIN kullanicilar k ON k.id = g.kullanici_id
           ORDER BY g.zaman DESC, g.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
