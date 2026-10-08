-- Agora veritabanı şeması (sürüm 2). Dağıtık defter ayrı dosyalarda tutulur (instance/defter/*.db).

-- ===== Ontoloji =====
CREATE TABLE IF NOT EXISTS konumlar (
    id      INTEGER PRIMARY KEY,
    ad      TEXT NOT NULL,
    tur     TEXT NOT NULL,                 -- ULKE, BOLGE, IL, ILCE
    ust_id  INTEGER REFERENCES konumlar(id)
);
CREATE TABLE IF NOT EXISTS kategoriler (
    id      INTEGER PRIMARY KEY,
    ad      TEXT NOT NULL,
    ust_id  INTEGER REFERENCES kategoriler(id),
    renk    TEXT,                               -- boşsa ayarlar.KATEGORI_RENKLERI'nden
    kaynak     TEXT NOT NULL DEFAULT 'SISTEM',   -- SISTEM, YONETICI, TOPLULUK (oylamayla eklendi)
    kavramlar  TEXT,                             -- virgülle ayrılmış ek terimler (kategori denetimi için)
    olusturma  TEXT
);

-- ===== Yurttaşlar ve graf =====
CREATE TABLE IF NOT EXISTS kullanicilar (
    id                 INTEGER PRIMARY KEY,
    ad_soyad           TEXT,                          -- gizli
    takma_ad           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    sifre_hash         TEXT,                          -- YZ hesaplarında NULL
    kurtarma_hash      TEXT,                          -- şifre kurtarma kodu (hash)
    dogum_tarihi       TEXT,
    konum_id           INTEGER REFERENCES konumlar(id),
    bekleyen_konum_id  INTEGER REFERENCES konumlar(id),
    konum_gecerlilik   TEXT,
    yz_mi              INTEGER NOT NULL DEFAULT 0,
    yonetici_mi        INTEGER NOT NULL DEFAULT 0,
    askida_bitis       TEXT,                          -- yönetici askıya aldıysa bitiş zamanı
    askida_neden       TEXT,
    oturum_surumu      INTEGER NOT NULL DEFAULT 0,   -- şifre değişince artar; eski oturum çerezleri geçersiz olur
    olusturma          TEXT NOT NULL,
    son_giris          TEXT
);
CREATE TABLE IF NOT EXISTS uzmanliklar (
    id           INTEGER PRIMARY KEY,
    kullanici_id INTEGER NOT NULL REFERENCES kullanicilar(id),
    kategori_id  INTEGER NOT NULL REFERENCES kategoriler(id),
    baslangic    TEXT NOT NULL,
    bitis        TEXT NOT NULL,
    kaynak       TEXT NOT NULL,                       -- TOPLULUK (oylamayla)
    belge        TEXT
);
-- Sosyal graf kenarı: takip. (Diğer kenarlar: devirler, yanıtlar; oy benzerliği yalnızca sunucuda hesaplanır, gösterilmez.)
CREATE TABLE IF NOT EXISTS takipler (
    takip_eden_id    INTEGER NOT NULL REFERENCES kullanicilar(id),
    takip_edilen_id  INTEGER NOT NULL REFERENCES kullanicilar(id),
    olusturma        TEXT NOT NULL,
    PRIMARY KEY (takip_eden_id, takip_edilen_id)
);
CREATE TABLE IF NOT EXISTS devirler (
    id         INTEGER PRIMARY KEY,
    veren_id   INTEGER NOT NULL REFERENCES kullanicilar(id),
    alan_id    INTEGER NOT NULL REFERENCES kullanicilar(id),
    kapsam     TEXT NOT NULL,                         -- GENEL, KATEGORI, KONU
    kapsam_id  INTEGER NOT NULL DEFAULT 0,
    olusturma  TEXT NOT NULL,
    UNIQUE (veren_id, kapsam, kapsam_id)
);

-- ===== Konular =====
CREATE TABLE IF NOT EXISTS konular (
    id                  INTEGER PRIMARY KEY,
    ust_id              INTEGER REFERENCES konular(id),    -- alt konuysa üst konusu
    itiraz_id           INTEGER REFERENCES konular(id),    -- bir konunun sonucuna itirazsa o konu
    sahip_id            INTEGER NOT NULL REFERENCES kullanicilar(id),
    kategori_id         INTEGER NOT NULL REFERENCES kategoriler(id),
    baslik              TEXT NOT NULL,
    aciklama            TEXT NOT NULL,
    konum_id            INTEGER REFERENCES konumlar(id),
    min_yas             INTEGER,
    max_yas             INTEGER,
    bilirkisi_agirlik   INTEGER NOT NULL,              -- uzman oyunun bu konudaki ağırlığı
    yz_agirlik          INTEGER NOT NULL DEFAULT 0,    -- kullanılmıyor
    durum               TEXT NOT NULL DEFAULT 'TARTISMA',  -- TARTISMA, OYLAMA, KARARA_BAGLANDI, SONUCSUZ
    tur                 INTEGER NOT NULL DEFAULT 0,    -- süren fikir oylaması turu (1-5)
    tartisma_bitis      TEXT,                          -- fikir oylamasının başlayacağı an
    denetim             TEXT,                          -- JSON: yönetmelik denetim raporu
    komisyon_bitis      TEXT,                          -- kullanılmıyor
    kabul_tarihi        TEXT,                          -- konunun kapandığı an
    silindi             INTEGER NOT NULL DEFAULT 0,
    silinme_notu        TEXT,
    erteleme_kullanildi INTEGER NOT NULL DEFAULT 0,
    olusturma           TEXT NOT NULL,
    duzenleme           TEXT
);
CREATE TABLE IF NOT EXISTS konu_surumleri (
    id                 INTEGER PRIMARY KEY,
    konu_id            INTEGER NOT NULL REFERENCES konular(id),
    baslik             TEXT NOT NULL,
    aciklama           TEXT NOT NULL,
    bilirkisi_agirlik  INTEGER NOT NULL,
    yz_agirlik         INTEGER NOT NULL,
    tarih              TEXT NOT NULL,
    neden              TEXT NOT NULL
);
-- ===== Mesajlar (silinmez) =====
CREATE TABLE IF NOT EXISTS mesajlar (
    id             INTEGER PRIMARY KEY,
    konu_id        INTEGER NOT NULL REFERENCES konular(id),
    yazar_id       INTEGER REFERENCES kullanicilar(id),
    ust_mesaj_id   INTEGER REFERENCES mesajlar(id),
    tip            TEXT NOT NULL,
    icerik         TEXT NOT NULL,
    gizli          INTEGER NOT NULL DEFAULT 0,
    gizlenme_notu  TEXT,
    olusturma      TEXT NOT NULL,
    duzenleme      TEXT
);
CREATE TABLE IF NOT EXISTS mesaj_surumleri (
    id        INTEGER PRIMARY KEY,
    mesaj_id  INTEGER NOT NULL REFERENCES mesajlar(id),
    icerik    TEXT NOT NULL,
    tarih     TEXT NOT NULL
);

-- ===== Oylama =====
CREATE TABLE IF NOT EXISTS teklifler (
    id         INTEGER PRIMARY KEY,
    tip        TEXT NOT NULL,
    konu_id    INTEGER REFERENCES konular(id),
    hedef_id   INTEGER,
    acan_id    INTEGER REFERENCES kullanicilar(id),
    gerekce    TEXT,
    veri       TEXT,
    esik       TEXT NOT NULL,
    tur_no     INTEGER NOT NULL DEFAULT 1,
    baslangic  TEXT NOT NULL,
    bitis      TEXT NOT NULL,
    durum      TEXT NOT NULL DEFAULT 'ACIK',
    sonuc      TEXT,
    kapanis    TEXT
);
CREATE TABLE IF NOT EXISTS secenekler (
    id         INTEGER PRIMARY KEY,
    teklif_id  INTEGER NOT NULL REFERENCES teklifler(id),
    mesaj_id   INTEGER REFERENCES mesajlar(id),
    metin      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS oylar (
    teklif_id     INTEGER NOT NULL REFERENCES teklifler(id),
    kullanici_id  INTEGER NOT NULL REFERENCES kullanicilar(id),
    secim         TEXT NOT NULL,
    agirlik       INTEGER NOT NULL,
    aciklama      TEXT NOT NULL,
    gerekce       TEXT,
    taahhut       TEXT NOT NULL,                     -- sha256(teklif|seçim|makbuz): deftere yazılan
    zaman         TEXT NOT NULL,
    PRIMARY KEY (teklif_id, kullanici_id)
);
CREATE TABLE IF NOT EXISTS kararlar (
    id                  INTEGER PRIMARY KEY,
    konu_id             INTEGER NOT NULL REFERENCES konular(id),
    teklif_id           INTEGER NOT NULL REFERENCES teklifler(id),
    kazanan_secenek_id  INTEGER NOT NULL REFERENCES secenekler(id),
    metin               TEXT NOT NULL,
    durum               TEXT NOT NULL DEFAULT 'KESIN',
    erteleme_bitis      TEXT NOT NULL,                 -- kullanılmıyor
    kesinlesme          TEXT,
    olusturma           TEXT NOT NULL
);

-- ===== Yönetmelik =====
CREATE TABLE IF NOT EXISTS parametreler (
    kod        TEXT PRIMARY KEY,
    deger      TEXT NOT NULL,
    tur        TEXT NOT NULL,                        -- esik, oran, sayi
    aciklama   TEXT NOT NULL,
    korunan    INTEGER NOT NULL DEFAULT 0,
    degisme    TEXT
);
CREATE TABLE IF NOT EXISTS yonetmelik_maddeleri (
    id         INTEGER PRIMARY KEY,
    kod        TEXT NOT NULL UNIQUE,                 -- T1.., U1.., D1.., B1..
    tur        TEXT NOT NULL,                        -- TEMEL_HAK, USUL, DENETIM, BEYAN
    baslik     TEXT NOT NULL,
    metin      TEXT NOT NULL,
    ciddiyet   TEXT,                                 -- DENETIM için: ENGEL, UYARI, KAPALI
    korunan    INTEGER NOT NULL DEFAULT 0,
    degisme    TEXT
);

-- ===== Site işlevleri =====
CREATE TABLE IF NOT EXISTS bildirimler (
    id            INTEGER PRIMARY KEY,
    kullanici_id  INTEGER NOT NULL REFERENCES kullanicilar(id),
    metin         TEXT NOT NULL,
    baglanti      TEXT NOT NULL,
    okundu        INTEGER NOT NULL DEFAULT 0,
    olusturma     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS giris_denemeleri (
    anahtar      TEXT PRIMARY KEY,
    sayi         INTEGER NOT NULL,
    kilit_bitis  TEXT
);
CREATE TABLE IF NOT EXISTS api_anahtarlari (
    id            INTEGER PRIMARY KEY,
    kullanici_id  INTEGER NOT NULL REFERENCES kullanicilar(id),
    ad            TEXT NOT NULL,
    anahtar_hash  TEXT NOT NULL UNIQUE,
    olusturma     TEXT NOT NULL,
    son_kullanim  TEXT
);
CREATE TABLE IF NOT EXISTS gunluk (
    id            INTEGER PRIMARY KEY,
    kullanici_id  INTEGER REFERENCES kullanicilar(id),
    eylem         TEXT NOT NULL,
    detay         TEXT NOT NULL,
    zaman         TEXT NOT NULL
);
-- Tam metin arama (Türkçe karakterler katlanmış halde saklanır)
CREATE VIRTUAL TABLE IF NOT EXISTS arama USING fts5(
    tur UNINDEXED, ref_id UNINDEXED, konu_id UNINDEXED, metin, tokenize = 'unicode61'
);

CREATE INDEX IF NOT EXISTS ix_mesaj_konu ON mesajlar(konu_id);
CREATE INDEX IF NOT EXISTS ix_teklif_konu ON teklifler(konu_id, durum);
CREATE INDEX IF NOT EXISTS ix_konu_ust ON konular(ust_id);
CREATE INDEX IF NOT EXISTS ix_bildirim ON bildirimler(kullanici_id, okundu);
CREATE INDEX IF NOT EXISTS ix_oy_kullanici ON oylar(kullanici_id);

PRAGMA user_version = 2;

-- ===== Site ayarları (yönetim panelinden değişir) =====
CREATE TABLE IF NOT EXISTS site_ayarlari (
    anahtar  TEXT PRIMARY KEY,
    deger    TEXT NOT NULL
);

-- ===== Şikayetler: üyeler mesajı ya da konuyu yöneticilere bildirir =====
CREATE TABLE IF NOT EXISTS sikayetler (
    id            INTEGER PRIMARY KEY,
    sikayetci_id  INTEGER NOT NULL REFERENCES kullanicilar(id),
    tur           TEXT NOT NULL,                     -- MESAJ, KONU
    hedef_id      INTEGER NOT NULL,                  -- mesaj ya da konu id
    konu_id       INTEGER NOT NULL REFERENCES konular(id),
    neden         TEXT NOT NULL,
    aciklama      TEXT,
    durum         TEXT NOT NULL DEFAULT 'ACIK',      -- ACIK, OYLAMADA, YERSIZ
    teklif_id     INTEGER REFERENCES teklifler(id),
    yonetici_id   INTEGER REFERENCES kullanicilar(id),
    sonuc_notu    TEXT,
    olusturma     TEXT NOT NULL,
    kapanis       TEXT
);
CREATE INDEX IF NOT EXISTS ix_sikayet_durum ON sikayetler(durum, tur, hedef_id);

-- ===== Anlık bildirim abonelikleri (tarayıcı: Web Push, Android uygulaması: FCM) =====
CREATE TABLE IF NOT EXISTS anlik_abonelikler (
    id            INTEGER PRIMARY KEY,
    kullanici_id  INTEGER NOT NULL REFERENCES kullanicilar(id),
    tur           TEXT NOT NULL,                     -- WEB, FCM
    adres         TEXT NOT NULL UNIQUE,              -- tarayıcı uç noktası ya da FCM cihaz anahtarı
    anahtarlar    TEXT,                              -- WEB: p256dh ve auth (JSON)
    cihaz         TEXT,
    olusturma     TEXT NOT NULL
);
