"""Kararlar: fikir oylamasını kazanan fikir, konunun kararı olur ve konu kapanır.

Karar hemen kesindir. Karara katılmayan her üye yeni bir itiraz konusu açabilir (konular.konu_ac, itiraz_id);
itiraz konusu da aynı tartışma ve oylama yolundan geçer.
"""
import json

from . import defter, gunluk, zaman


def olustur(db, konu_id, teklif_id, secenek_id, metin):
    simdi = zaman.simdi_metin()
    karar_id = db.execute(
        """INSERT INTO kararlar (konu_id, teklif_id, kazanan_secenek_id, metin, durum, erteleme_bitis, kesinlesme, olusturma)
           VALUES (?, ?, ?, ?, 'KESIN', ?, ?, ?)""",
        (konu_id, teklif_id, secenek_id, metin, simdi, simdi, simdi)).lastrowid
    gunluk.kaydet(db, None, "KARAR", f"#{konu_id} konusunda karar: “{metin}”")
    defter.ekle(db, "KARAR", {"konu": konu_id, "karar": karar_id, "metin": metin})
    return karar_id


def konu_karari(db, konu_id):
    return db.execute("SELECT * FROM kararlar WHERE konu_id = ? AND durum = 'KESIN' ORDER BY id DESC LIMIT 1",
                      (konu_id,)).fetchone()


def tum_kararlar(db):
    satirlar = db.execute("""SELECT kr.*, k.baslik, k.id AS konu_no, k.kategori_id, t.sonuc, t.tur_no FROM kararlar kr
                             JOIN konular k ON k.id = kr.konu_id JOIN teklifler t ON t.id = kr.teklif_id
                             WHERE k.silindi = 0 AND kr.durum = 'KESIN' ORDER BY kr.id DESC""").fetchall()
    return [dict(r, sonuc_json=json.loads(r["sonuc"]) if r["sonuc"] else None) for r in satirlar]
