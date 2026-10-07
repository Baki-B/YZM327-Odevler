# Agora — Tasarım Belgesi

Bu belgedeki diyagramlar Mermaid ile yazılmıştır (GitHub'da ve VS Code'da Mermaid eklentisiyle çizilir).
Problem çerçeveleme, metrikler, ölçümler ve işlevsel olmayan gereksinimler [analiz.md](analiz.md) dosyasındadır.
SOLID ilkeleri ve tasarım desenlerinin projedeki karşılıkları 8. bölümde.

## 1. Kullanım durumu (use case)

```mermaid
flowchart LR
  Y([Üye]) --- T[Konu aç / düzenle / itiraz konusu aç]
  Y --- F[Fikir yaz: konu başına bir tane]
  Y --- M[Mesaj yaz, yanıtla, düzenle]
  Y --- O[Oy ver, makbuzla doğrula]
  Y --- D[Oy devret]
  Y --- G[Mesaj gizleme / konu kaldırma oylaması aç, şikayet et]
  Y --- U[Uzmanlığa başvur]
  Y --- R[Yönetmelik değişikliği öner]
  Gz([Gözlemci]) --- Ok[Oku, ara, defteri incele]
  Uz([Uzman]) --- O2[Alanında 10 sayılan, açık ve gerekçeli oy]
  YZ([Yapay zeka]) --- Oz[Tartışma ve tur özeti]
  Yn([Yönetici]) --- Bk[Yetki, askı, şikayet kutusu, kategori, duyuru, yedek]
  S([Zamanlayıcı]) --- Z[Tartışma ve tur sürelerini işlet]
```

## 2. Konunun yaşam döngüsü (durum diyagramı)

```mermaid
stateDiagram-v2
  [*] --> TARTISMA: konu açıldı (yönetmelik denetimi geçti)
  TARTISMA --> OYLAMA: 24 saat doldu → 1. tur
  OYLAMA --> OYLAMA: tur bitti, birden fazla fikir kaldı → sonraki tur (en fazla 5)
  OYLAMA --> KARARA_BAGLANDI: bir fikir %75 aldı / tek fikir kaldı / 5. turda en çok oyu aldı
  OYLAMA --> SONUCSUZ: yeter sayı yok / hiçbir fikir kalmadı / son turda eşitlik
  TARTISMA --> KALDIRILDI: kaldırma oylaması (3/4)
  OYLAMA --> KALDIRILDI: kaldırma oylaması (3/4)
  KARARA_BAGLANDI --> KALDIRILDI: kaldırma oylaması (3/4)
  SONUCSUZ --> KALDIRILDI: kaldırma oylaması (3/4)
  KARARA_BAGLANDI --> [*]
  SONUCSUZ --> [*]
  note right of KARARA_BAGLANDI: Katılmayan, itiraz konusu açar (yeni bir TARTISMA)
```

Eleme eşikleri: 1. tur %5, 2. tur %5, 3. tur %10, 4. tur %20. Oran = ağırlıklı pay ile kişi payının küçüğü.
Durumlar kodda **State** desenidir (`forum/konu_durumlari.py`, 8.2): her durum "bu durumda ne yapılabilir?" sorusunu kendisi
yanıtlar ve izin verilen geçişleri bilir. KALDIRILDI ayrı bir sütun değil, `silindi = 1` bayrağıdır; kaldırılan konunun içeriği
ve geçmişi gösterilmez.

## 3. Oy verme ve sonuçlandırma (sıralı diyagramlar)

**Oy verme.** Yazan her istek baştan yazma kilidini alır (`BEGIN IMMEDIATE`); oy, ancak tur hâlâ açıksa yazılır. Defter, veritabanının
"işlem kaydedildi" olayına abonedir (Observer): veritabanı defteri tanımaz.

```mermaid
sequenceDiagram
  actor Y as Üye
  participant W as Web katmanı (istek zinciri)
  participant O as oylama.py
  participant U as uygunluk.py
  participant V as Veritabanı (Baglanti)
  participant D as defter.py (abone)
  participant N as Düğüm A · B · C
  Y->>W: POST /oylama/12/oy (seçim, CSRF)
  W->>W: kimlik → askı → CSRF → zamanlayıcı → yazma kilidi (BEGIN IMMEDIATE)
  W->>O: oy_ver()
  O->>U: oy_agirligi() — gözlemci mi, uzman mı?
  U-->>O: ağırlık (1 / 10) + açıklama
  O->>O: makbuz üret, taahhüt = SHA256(teklif|seçim|makbuz)
  O->>V: INSERT oylar … WHERE tur hâlâ açık (koşullu)
  O->>V: defter kuyruğuna OY bloğu (henüz yazılmaz)
  W->>V: COMMIT
  V-->>D: commit olayı → _islem_kaydedildi()
  D->>N: çoğunluk zincirinin son bloğuna ekle (yalnızca sağlam düğümlere)
  W-->>Y: makbuz kodu (bir kez gösterilir)
  Y->>W: POST /defter/makbuz (teklif, makbuz)
  W->>D: makbuz_dogrula()
  D-->>Y: "Oyun blok #N'de kayıtlı, seçimin: …, güncel mi"
```

**Tur sonu.** Zamanlayıcı (her 30 sn ve her istekte) süresi dolan turları sonuçlandırır. Her oylama ayrı bir kayıt noktasında
(SAVEPOINT, Memento) işlenir: biri hata verirse yalnızca o geri alınır, diğerleri sürer. Sonuçlandırma bir Template Method'dur;
türe özgü adımlar Strategy nesnesinden (teklif türü) gelir.

```mermaid
sequenceDiagram
  participant Z as gorevler.tick
  participant V as Veritabanı
  participant O as oylama.sonuclandir (şablon)
  participant T as Teklif türü (strateji)
  participant S as sonuclar.py
  participant Y as yz.py
  Z->>V: kayit_noktasi() — SAVEPOINT + kuyruk hatırası
  Z->>O: sonuclandir(teklif)
  O->>O: sayim() — çift oran, çekimser, yeter sayı
  O->>T: sonuc_durumu(s), sonucu_tamamla(s)
  T->>S: tur_karari() — saf işlev: KABUL / DEVAM / SONUÇSUZ
  O->>T: sonuc_bildirimi(), uygula()
  T->>S: tur_uygula() — karar kaydı ya da sonraki tur
  T->>Y: tur_ozeti() — sayılar kararın kendisinden
  Z->>V: RELEASE (hata olursa ROLLBACK TO + kuyruklar hatıraya döner)
  Z->>V: COMMIT → defter aboneleri
```

## 4. Varlık–ilişki (veri modeli)

```mermaid
erDiagram
  KULLANICILAR ||--o{ KONULAR : "açar"
  KULLANICILAR ||--o{ MESAJLAR : "yazar"
  KULLANICILAR ||--o{ OYLAR : "verir"
  KULLANICILAR ||--o{ DEVIRLER : "devreder / devralır"
  KULLANICILAR ||--o{ TAKIPLER : "takip eder"
  KULLANICILAR ||--o{ UZMANLIKLAR : "uzmandır"
  KULLANICILAR ||--o{ BILDIRIMLER : "alır"
  KULLANICILAR ||--o{ API_ANAHTARLARI : "sahibidir"
  KULLANICILAR ||--o{ ANLIK_ABONELIKLER : "cihaz kaydeder"
  KULLANICILAR ||--o{ GUNLUK : "işlem yapar"
  KULLANICILAR ||--o{ SIKAYETLER : "şikayet eder / inceler"
  KATEGORILER ||--o{ KATEGORILER : "alt kategori"
  KATEGORILER ||--o{ KONULAR : "alan"
  KATEGORILER ||--o{ UZMANLIKLAR : "alan"
  KONUMLAR ||--o{ KONUMLAR : "il › ilçe"
  KONUMLAR ||--o{ KULLANICILAR : "oturur"
  KONUMLAR ||--o{ KONULAR : "katılım kuralı"
  KONULAR ||--o{ KONULAR : "alt konu / itiraz"
  KONULAR ||--o{ KONU_SURUMLERI : "eski sürümler"
  KONULAR ||--o{ MESAJLAR : "içerir"
  KONULAR ||--o{ TEKLIFLER : "oylanır"
  KONULAR ||--o{ SIKAYETLER : "şikayet edilir"
  MESAJLAR ||--o{ MESAJLAR : "yanıt"
  MESAJLAR ||--o{ MESAJ_SURUMLERI : "eski sürümler"
  MESAJLAR ||--o| SECENEKLER : "fikir seçeneği"
  TEKLIFLER ||--o{ SECENEKLER : "içerir"
  TEKLIFLER ||--o{ OYLAR : "toplar"
  TEKLIFLER ||--o| KARARLAR : "kabul edilen fikir"
  TEKLIFLER ||--o{ SIKAYETLER : "oylamaya alınır"
  SECENEKLER ||--o| KARARLAR : "kazanan"
  PARAMETRELER }o--|| YONETMELIK_MADDELERI : "metinde kullanılır"
```

İlişkisi olmayan tablolar: `giris_denemeleri` (hız sınırı ve giriş kilidi; anahtar = takma ad ya da adres), `site_ayarlari`
(duyuru, yeni üyelik açık mı, şema sürümü), `arama` (tam metin arama dizini, FTS). Kayıt defteri düğümleri (A.db, B.db, C.db)
veritabanının dışında, ayrı dosyalardadır.

## 5. Katmanlar

```mermaid
flowchart TB
  subgraph İstemciler
    Tarayici[Tarayıcı / PWA] ---|oturum + CSRF| Web
    Mobil[Mobil uygulama] ---|Bearer anahtar| API
  end
  subgraph Sunum["Sunum katmanı (forum/web)"]
    Zincir[istek.py — istek öncesi zincir] --> Web[sayfa rotaları]
    Zincir --> API[api.py — REST]
    Web --> Gorunum[gorunum.py — konu sayfası cephesi]
  end
  subgraph Is["İş kuralı katmanı (forum)"]
    Konular[konular · konu_durumlari] --- Oylama[oylama · teklif_turleri · sonuclar]
    Denetim[denetim — D1…D7 zinciri] --- Diger[devir · uzmanlik · yonetmelik · graf · gundem · yz]
  end
  Web --> Is
  API --> Is
  Gorunum --> Is
  Is --> VT[(SQLite — veritabani.Baglanti)]
  VT -.->|commit olayı - Observer| Defter[defter.py]
  Defter --> Depo[(DugumDeposu: A · B · C)]
  VT -.->|commit sonrası| Anlik[anlik.py — kanal adaptörleri]
  Zamanlayici[gorevler.tick — 30 sn] --> Is
  Ortak[metin · hatalar · zaman · ayarlar] -.- Is
```

Kesikli oklar: altyapı katmanı (veritabanı) üst katmanı **çağırmaz**; olay yayımlar, üst katman abone olur (DIP).

## 6. Görsel tasarım: "Sade akış" ve iki renk

**Bilgi mimarisi:** Eski kenar menüsündeki 9 bölüm, 6 kategori ve 2 alt bağlantı üç ana bölümde toplandı.

| Bölüm | İçinde |
|---|---|
| Konular | Konu akışı, kategori çipleri, durum filtresi (açılır menü), bekleyen oylar şeridi, arama |
| Oylamalar | Gündem (süren oylamalar), kararlar arşivi |
| Meclis | Nasıl işler?, yönetmelik, kayıt defteri, üye ağı, şeffaflık günlüğü, API, yönetim (yalnızca yönetici) |
| Avatar menüsü | Panelim, bildirimler, herkese açık profil, yönetim paneli (yöneticilere), çıkış |
| Panelim (`/profil`) | Solda bölüm menüsü: özet, bildirimler, hesap bilgileri, oy devri, uzmanlık, güvenlik, uygulama ve API |
| Yönetim paneli (`/yonetim`) | Solda bölüm menüsü: pano, üyeler, konular, oylamalar, kategoriler, sistem, günlük; kullanıcı sayfalarında yönetici düğmesi yok |
| Telefon / mobil uygulama | Üst çubukta logo, arama, bildirim ve avatar; ana bölümler alttaki sekme çubuğunda (ortada yeni konu düğmesi) |

**Giriş katmanı:** `/` adresi ziyaretçiye tanıtım sayfasını (tapınak çizimi, canlı sayılar, bir konunun 4 adımda karara
dönüşmesi, şu an mecliste olan konular, üyelik çağrısı) gösterir; giriş yapmış üye aynı adreste doğrudan konu akışını görür.
Konu akışı `/konular` adresindedir. Giriş, üye ol ve şifre sıfırlama sayfaları solda kaktüs yeşili bir tanıtım paneli,
sağda form olan iki sütunlu bir kabuk kullanır (`giris_kabugu` makrosu).

Konu sayfasının sağ sütunu da beş kutudan üçe indi (senin durumun + oy ağırlıkları, işlemler, bu konudaki oylamalar ve alt konular).

| Renk | Nerede |
|---|---|
| Taş beyazı `#ebe7df`, kartlarda `#f6f4ef` (ana renk) | Sayfa zemini, üst çubuk, kartlar, mesajlar, formlar |
| Kaktüs yeşili `#4a6642` ve tonları (yan renk) | Düğmeler, seçili sekme ve çip, rozetler, gündem şeridi, aşama noktaları, bağlantılar |

- Taş beyazı, güneş almış mermer tonunun (`#f6e9d9`) biraz silikleştirilip grileştirilmiş hâlidir. Yazılar koyu gridir
  (`#2c2a27`); başka renk yoktur.
- Kırmızı olmadığı için durumlar ikon ve dolgu biçimiyle ayrılır (oylamada = açık yeşil + nokta, sonuçlandı = koyu yeşil + ✓,
  olumsuz = kesikli çerçeve + ✕). Konu kartındaki yedi nokta (tartışma, beş tur, karar), konunun hangi aşamada olduğunu gösterir.
- Emojiler işletim sistemine göre renkli çizildiği için tek renkli çizgi ikonlarla (`web/ikonlar.py`) değiştirildi.
- Logo: kaktüs yeşili zemin üzerinde, yivli Dor sütunlu taş beyazı bir meclis binası.

## 7. Temel kararlar ve gerekçeleri

| Karar | Gerekçe |
|---|---|
| Konu hemen açılır, kabul oylaması yok | Herkesin derdini anlatabilmesi; çoğunluk konunun açılmasına değil sonucuna karar verir. |
| Kişi başı tek fikir | Herkes eşit söz alır; kimse onlarca seçenekle oylamayı boğamaz. |
| Tur tur eleme (%5, %5, %10, %20) | Çok sayıda fikir adım adım azalır; her turda oylar kalan fikirlerde yeniden toplanır. |
| Ezici üstünlük (%75) ve "tek kalan" kısa yolları | Belli olmuş bir sonucu beş tur beklemeye gerek yok. |
| Oran = ağırlıklı pay ile kişi payının küçüğü | Uzman ağırlığı kalabalığı tek başına yenemez; kalabalık da uzmanları yok sayamaz. |
| Çekimser paydada sayılır | Nötr oy da çoğunluğun sağlanıp sağlanmadığını etkiler. |
| Her oylama tek bir "teklif" mekanizmasından geçer | Fikir turları, gizleme, kaldırma, uzmanlık ve yönetmelik aynı sayım kurallarını paylaşır; kod tekrarı olmaz. |
| Uzmanlık: ön şart + kontenjan + alanın oylaması | Uzmanlık emekle ve alanın onayıyla kazanılır; kontenjan, bir kliğin birbirini uzman yapmasını önler. |
| Yönetici yalnızca yönetir | Karar yetkisi yalnızca oylamalardadır; yönetim panelinde kararı etkileyen işlem tanımlı değildir. |
| Şikayet tabanı (3 üye) | Tek kişinin şikayeti yöneticiyi meşgul etmez; taban dolunca da kararı yine oylama verir. |
| Eşikler veritabanında | Topluluk kendi kurallarını oylayabilir. Korunan maddeler 3/4 ister (anayasa gibi). |
| Defter yalnızca commit sonrası yazılır | Geri alınan işlemler deftere girmez; veritabanı ve defter tutarlı kalır. |
| Deftere kişisel veri yazılmaz | Mesajların özeti, oyların taahhüdü yazılır; gizli oy ve KVKK korunur. |
| Yapay zeka yalnızca özetler | Kararlar üyelere aittir; yapay zeka oy kullanmaz, özetleri sayılara dayanır. |

## 8. Tasarım ilkeleri (SOLID) ve tasarım desenleri

Atıflar *Yazılım Tasarım Desenleri* slaytlarına (TD-numara). Bir desen ancak kodda somut bir sorunu çözdüğü yerde kullanıldı
(TD-3: "desen bir amaç değil, araçtır"; TD-57: YAGNI ve KISS). Her satırdaki "önce" sütunu, desenin hangi sorunu çözdüğünü
gösterir; her desenin davranışı testle korunur (`testler/test_duzeltmeler.py` içindeki sınıf adları).

### 8.1 SOLID (TD-9…12)

| İlke | Önce (ihlal) | Şimdi | Nerede |
|---|---|---|---|
| **S** — Tek sorumluluk | `web/__init__.kur()` 150 satırda kimlik, CSRF, zamanlayıcı, hata sayfaları ve şablon filtrelerini birlikte yapıyordu. Yönetmelik modülü hem maddeleri hem denetim motorunu taşıyordu. Konu sayfası rotası iş kuralı içeriyordu. | Her biri kendi modülünde | `web/istek.py`, `web/hata_sayfalari.py`, `web/sablon.py`, `denetim.py`, `gorunum.py`, `metin.py`, `hatalar.py` |
| **O** — Açık/kapalı | Yeni oylama türü 5 dosyada `if tip == …` dalı demekti; yeni bildirim kanalı `if tur == 'WEB'` dalı | Yeni tür = yeni sınıf + `@kaydet`; yeni denetim maddesi = yeni halka; yeni kanal = yeni adaptör; yeni depo = yeni `DugumDeposu` | `teklif_turleri.py`, `denetim.py`, `anlik.py`, `defter.py` |
| **L** — Liskov | Web Push kanalı, `pywebpush` kurulu değilken abone kabul edip her bildirimde hata veriyordu (alt tür sözleşmeyi bozuyordu) | Kapalı kanal abone kabul etmez. Bütün teklif türleri şablon yöntemde aynı biçimde kullanılır. SQLite ve bellek depoları aynı sonucu verir | `AnlikAbonelikAdresi`, `TeklifTurleri`, `DefterOlceklenmesi.test_sorgu_islemleri_iki_depoda_ayni` |
| **I** — Arayüz ayrımı | — | Arayüzler küçük: `AnlikKanal` 3 yöntem, `DenetimKurali` 1 soyut yöntem (`kontrol`), `DugumDeposu` 5 soyut yöntem (sorgular varsayılanlı) | `anlik.py`, `denetim.py`, `defter.py` |
| **D** — Bağımlılığın tersine çevrilmesi | Veritabanı bağlantısı (altyapı) defter modülünü (üst katman) içe aktarıyordu. Şifre özeti yöntemi sabitti; zaman `datetime.now()` ile her yerden okunuyordu | Defter commit olayına abone (Observer); şifre yöntemi enjekte edilir (`FORUM_SIFRE_YONTEMI`); zaman tek kaynaktan (`zaman.simdi`); kanallar ve depolar dışarıdan verilir | `veritabani.commit_aboneligi`, `guvenlik.SIFRE_YONTEMI`, `zaman.py`, `anlik.KANALLAR`, `defter._depolar` |

### 8.2 Uygulanan desenler

| Desen | Önceki sorun | Agora'da | Test |
|---|---|---|---|
| **State** (TD-43) | `konu["durum"] == …` karşılaştırmaları modüllere, web katmanına ve şablonlara dağılmıştı; unutulan bir kontrol kaldırılmış konunun geçmişini okunur bırakıyordu | `konu_durumlari.py`: `KonuDurumu` + 5 durum sınıfı; izinler (`yazilabilir`, `okunabilir`, `fikir_yazilabilir`…) ve geçiş tablosu (`gecis_dogrula`) | `GizliIcerikSizmaz` |
| **Strategy** (TD-36) | Sonuç uygulama kuralları türe göre `if/elif` ve dağınık sözlüklerde | `teklif_turleri.py`: `TeklifTuru` ve 6 somut tür (`FikirTuru`, `MesajGizlemeTuru`, `KonuKaldirmaTuru`, `UzmanlikTuru`, `YonetmelikTuru`, `KategoriTuru`) | `TeklifTurleri` |
| **Template Method** (TD-41) | Her türün sonuçlandırması aynı iskeleti tekrar ediyordu | `oylama.sonuclandir`: sayım → `sonuc_durumu` → `sonucu_tamamla` → `sonuc_bildirimi` → `uygula`; adımlar stratejinin kancaları | `TeklifTurleri` |
| **Registry** (TD-49) | Tür listesi birkaç yerde elle tutuluyordu | `teklif_turleri.TURLER` + `@kaydet` (yinelenen kod ve ayarlarda olmayan tür reddedilir); `anlik.KANALLAR`; `web/sablon.FILTRELER` | `TeklifTurleri` |
| **Factory** (TD-16) | — | `teklif_turleri.tur(kod)` koddan strateji nesnesi; `denetim.zincir_kur(*siniflar)` halkaları bağlar; `defter._depolar(kaynak)` kaynağa göre depo seçer (yol → SQLite, liste → verilen) | — |
| **Chain of Responsibility** (TD-44) | D1–D7 tek 77 satırlık fonksiyondaydı; mesaj denetimi D1 ve D2'yi ayrıca yeniden yazıyordu | `denetim.py`: her madde bir halka (`SayginDil` … `Aciklik`); mesajlara uygulananlar `mesajlara_uygulanir`. Web'de `web/istek.py` istek öncesi zinciri (kimlik → askı → CSRF → zamanlayıcı → yazma kilidi) | `DenetimZinciri` |
| **Adapter** (TD-24) | `pywebpush` ve Firebase HTTP v1 farklı arayüzler; çağıran kod iki dalı da biliyordu | `anlik.py`: `AnlikKanal` ← `WebPushKanali`, `FcmKanali`; testlerde `SahteKanal` | `AnlikAbonelikAdresi` |
| **Memento** (TD-47) | Zamanlayıcıda bir konunun hatası bütün işi geri alıyordu; geri alınan bloğun defter/bildirim yan etkileri kuyrukta kalıyordu | `veritabani.KuyrukHatirasi` + `kayit_noktasi()` (SAVEPOINT); `sonuclar.TurKarari` (turun kararı anlık görüntü olarak saklanır; sonradan parametre değişse de geçmiş tur aynı gösterilir) | `ZamanlayiciYalitimi`, `TurKarariAnlikGoruntusu` |
| **Observer** (TD-38) | `Baglanti.commit` defteri doğrudan çağırıyordu | `veritabani.commit_aboneligi`; `defter._islem_kaydedildi` abone. Bağlantı başına `commit_sonrasi` kuyruğu (bildirim, arka plan işleri) | `CommitGozlemcisi` |
| **Repository** (TD-51) | Düğüm dosyalarına `sqlite3` erişimi uzlaşma ve onarım mantığına gömülüydü; test için disk gerekiyordu; ölçeklenme düzeltmesi yapılamıyordu | `defter.DugumDeposu` ← `SqliteDugumDeposu` (üretim), `BellekDugumDeposu` (sahte depo, test) | `DefterDeposu`, `DefterOlceklenmesi` |
| **Facade** (TD-28) | Konu sayfası rotası 9 alt sistemi tek tek çağırıyor, fikir rozeti kuralı rotadaydı | `gorunum.konu_sayfasi()`; kural saf işlev `gorunum.fikir_durumu` | `KonuSayfasiCephesi` |
| **Dependency Injection** (TD-52) | Testler gerçek scrypt şifre özetiyle çalıştığı için 94 test ~60 sn sürüyordu | `guvenlik.SIFRE_YONTEMI` (testte hızlı yöntem), `zaman.simdi` (testte ileri sarılır), `anlik.KANALLAR` (testte sahte kanal), defter işlevlerine depo listesi | 172 test ~7 sn |
| **Decorator** (TD-26, 27 — fonksiyon düzeyinde) | — | `giris_gerekli`, `yonetici_gerekli` rotayı sarar; `@kaydet`, `@commit_aboneligi` kayıt dekoratörleri | — |
| **Command** (TD-40, hafif) | — | `commit_sonrasi` ve defter kuyrukları: yapılacak iş nesne olarak kuyruğa alınır, commit'te çalışır, rollback'te silinir | `YanEtkiDayanikliligi` |

### 8.3 Sınıf diyagramları

**State — konu durumları**

```mermaid
classDiagram
  class KonuDurumu {
    +kod
    +yazilabilir
    +kapali
    +okunabilir
    +sonrakiler
    +fikir_yazilabilir(konu)
    +konu_duzenlenebilir()
    +fikir_duzenlenebilir()
    +gecis_dogrula(yeni)
  }
  KonuDurumu <|-- Tartisma
  KonuDurumu <|-- Oylama
  KonuDurumu <|-- KararaBaglandi
  KonuDurumu <|-- Sonucsuz
  KonuDurumu <|-- Kaldirildi
  class konular {
    <<modül>>
    durumu(konu) KonuDurumu
    yazilabilir_olmali(konu)
    okunabilir_olmali(konu)
  }
  konular ..> KonuDurumu : sorar
```

**Strategy + Template Method + Registry — oylama türleri**

```mermaid
classDiagram
  class oylama {
    <<modül>>
    sonuclandir(teklif) «şablon yöntem»
    sayim(teklif)
    turu(teklif) TeklifTuru
  }
  class TeklifTuru {
    <<abstract>>
    +kod
    +secenekler(db, t)*
    +degerlendir(t, tablo, ...)*
    +sonuc_durumu(s)*
    +uygula(db, t, s, durum)*
    +esik(db) «kanca»
    +sonucu_tamamla(db, t, s) «kanca»
    +sonuc_bildirimi(db, t, s, durum) «kanca»
  }
  class TURLER {
    <<Registry>>
    kaydet(sinif)
    tur(kod) TeklifTuru
  }
  TeklifTuru <|-- FikirTuru
  TeklifTuru <|-- EvetHayirTuru
  EvetHayirTuru <|-- MesajGizlemeTuru
  EvetHayirTuru <|-- KonuKaldirmaTuru
  EvetHayirTuru <|-- UzmanlikTuru
  EvetHayirTuru <|-- ForumGeneliTuru
  ForumGeneliTuru <|-- YonetmelikTuru
  ForumGeneliTuru <|-- KategoriTuru
  oylama ..> TURLER : tur(kod)
  oylama ..> TeklifTuru : adımları çağırır
  FikirTuru ..> sonuclar : tur_karari() saf işlev
```

**Chain of Responsibility — yönetmelik denetimi**

```mermaid
classDiagram
  class DenetimKurali {
    <<abstract>>
    +kod
    +mesajlara_uygulanir
    +sonraki DenetimKurali
    +isle(istek) bulgular
    +kontrol(istek)*
    +mesaj_sorunu(metin)
  }
  DenetimKurali o-- DenetimKurali : sonraki
  DenetimKurali <|-- SayginDil
  DenetimKurali <|-- KisiselVeri
  DenetimKurali <|-- KategoriyeUygunluk
  DenetimKurali <|-- KonumTutarliligi
  DenetimKurali <|-- BenzerKonu
  DenetimKurali <|-- AltKonuIliskisi
  DenetimKurali <|-- Aciklik
  class DenetimIstegi {
    db, baslik, aciklama, kategori_id, konum_id, ust
    onerilen_kategori
  }
  DenetimKurali ..> DenetimIstegi
```

**Adapter — anlık bildirim kanalları**

```mermaid
classDiagram
  class AnlikKanal {
    <<abstract>>
    +kod
    +etkin(klasor)*
    +abonelik_coz(veri)*
    +gonder(klasor, abonelik, yuk)*
  }
  AnlikKanal <|-- WebPushKanali
  AnlikKanal <|-- FcmKanali
  WebPushKanali ..> pywebpush : uyarlar
  FcmKanali ..> FirebaseHTTPv1 : uyarlar
  class KANALLAR
  <<Registry>> KANALLAR
  KANALLAR o-- AnlikKanal
```

**Repository + Observer — kayıt defteri**

```mermaid
classDiagram
  class Baglanti {
    <<veritabani.py>>
    +defter_kuyrugu
    +commit_sonrasi
    +commit()
    +rollback()
    +kayit_noktasi()
  }
  class commit_aboneligi
  <<Observer>> commit_aboneligi
  Baglanti ..> commit_aboneligi : commit'te aboneleri çağırır
  class defter {
    <<modül>>
    _islem_kaydedildi(db) «abone»
    dugumlere_yaz(kaynak, kuyruk)
    durum(kaynak)
    onar(kaynak, ad)
  }
  commit_aboneligi <.. defter : abone olur
  class DugumDeposu {
    <<abstract>>
    +bloklar()*
    +ekle(yeni)*
    +yeniden_kur(zincir)*
    +veri_degistir(no, veri)*
    +surum()*
    +son_blok()
    +sayfa(tur, atla, boy)
    +turdeki(turler)
    +bul(anahtar)
  }
  DugumDeposu <|-- SqliteDugumDeposu
  DugumDeposu <|-- BellekDugumDeposu
  defter ..> DugumDeposu : yalnızca arayüzü bilir
```

**Facade — konu sayfası**

```mermaid
classDiagram
  class konu_sayfalari {
    <<web rotası>>
    konu(konu_id)
  }
  class gorunum {
    <<Facade>>
    konu_sayfasi(db, ben, konu_id)
    fikir_durumu(fikir, konu, yarisanlar, kazanan)
  }
  konu_sayfalari ..> gorunum
  gorunum ..> konular
  gorunum ..> uygunluk
  gorunum ..> oylama
  gorunum ..> kararlar
  gorunum ..> devir
  gorunum ..> kullanicilar
  gorunum ..> yz
```

### 8.4 Ödev slaytındaki gereksinimlerin karşılığı (TD-59)

| Slayttaki madde | Agora'daki karşılığı |
|---|---|
| Seçim yapılandırmadan yapılsın (Registry + Factory) | Oylama türleri `ayarlar.TEKLIF_TIPLERI` yapılandırmasında; sınıflar `@kaydet` ile kaydolur, `tur(kod)` ile seçilir. Şifre yöntemi ve gizli anahtar ortam değişkeninden |
| Ön işleme ve model tek nesnede (Pipeline) | Oylama sonuçlandırma hattı: sayım → saf `tur_karari` → `tur_uygula`; web istek öncesi zinciri |
| Veri kaynağı değiştirilebilsin (Repository) | `DugumDeposu`: SQLite dosyası ya da bellek; PostgreSQL için yeni bir gerçekleme yeter |
| Olaylar birden çok bileşene haber versin (Observer) | `commit_aboneligi`: defter commit olayına abone; bağlantı başına `commit_sonrasi` (bildirimler) |
| Tek giriş noktası (Facade) | `gorunum.konu_sayfasi` |
| Her bileşen için birim testi (sahte depo ile) | `BellekDugumDeposu` (sahte depo), `SahteKanal` (sahte bildirim kanalı), sahte zaman; 172 test |

### 8.5 Bilerek kullanılmayan desenler (TD-57, TD-58)

| Desen | Neden kullanılmadı |
|---|---|
| Singleton | Python modülü zaten tekildir (`ayarlar`, `KANALLAR`). Ayrı bir Singleton sınıfı TD-57'deki "gizli global durum" anti-desenini getirirdi |
| Builder, Prototype, Abstract Factory | Çok parametreli, adım adım kurulan nesne ya da birden çok altyapı ailesi yok |
| Visitor | Tür hiyerarşisi üzerinde sık eklenen yeni işlem yok; stratejinin kancaları yetiyor |
| Mediator | Bileşenler birbirleriyle karmaşık biçimde konuşmuyor; katmanlı çağrı yeterli |
| Proxy | Tembel yükleme yalnızca `pywebpush` içe aktarımında gerekli; bunun için bir sınıf gereksiz |
| Composite | Kategori ve konum ağaçları veri olarak var ama ağacın düğümlerine ortak bir işlem arayüzü gerekmedi |
| Iterator | Python'da yerleşik (üreteçler: `DenetimKurali.halkalar()`) |

### 8.6 Giderilen anti-desenler (TD-57)

| Anti-desen | Neredeydi | Nasıl giderildi |
|---|---|---|
| God function | `web/__init__.kur()` (150 satır), `yonetmelik.denetle` (77 satır) | 3 modül; 7 halka |
| Uzun `if durum == …` zinciri (TD-58: State) | Konu durumu kontrolleri, sonuç türü dalları, kanal dalları | State, Strategy, Adapter |
| Kopya kod | Güvenli yönlendirme kontrolü 5 kopya (biri açık yönlendirme açığı içeriyordu), yüzde biçimi 4 kopya, mesaj denetimi D1/D2 iki kopya | `metin.site_ici_yol_mu`, `metin.yuzde`, tek zincir |
| Gizli global durum | Sabit şifre yöntemi, her yerde `datetime.now()` | Enjeksiyon, `zaman.simdi` |
| Yapılandırma borcu (doğrulanmamış ayar) | Oylamayla `UZMAN_AGIRLIK=0`, eleme eşiği > ezici eşik gibi anlamsız değerler kabul ediliyordu | `ayarlar.PARAMETRE_ARALIKLARI` |
| Ölü kod | `yz_agirlik`, `komisyon_bitis` sütunları ("kullanılmıyor") | **Bilerek duruyor**: eski veritabanlarının göçü için (analiz.md 12. bölüm) |
| Erken soyutlama | — | Her arayüzün en az iki gerçeklemesi var (`DugumDeposu` 2, `AnlikKanal` 2 + test, `TeklifTuru` 6, `DenetimKurali` 7) |

### 8.7 Tartışma sorusu (TD-59): Python'un dinamik doğası hangi desenleri gereksiz kılıyor?

- **Singleton:** modül zaten tek bir nesnedir.
- **Strategy:** tek yöntemli bir strateji için fonksiyon yeter (`zaman.simdi` testte bir fonksiyonla değiştirilir). `TeklifTuru` sınıf
  oldu çünkü 15 kancası ve ortak varsayılanları var.
- **Command:** kapanış (closure) ya da herhangi bir çağrılabilir nesne komuttur (`commit_sonrasi` listesi).
- **Observer:** ayrı bir gözlemci arayüzü yerine fonksiyon listesi yeter (`commit_aboneligi`).
- **Factory / Registry:** sınıflar birinci sınıf nesnedir; sözlükte saklanıp koddan seçilir (`TURLER`, `KANALLAR`).
- **Iterator ve Decorator:** dilin kendisinde (`yield`, `@`).
