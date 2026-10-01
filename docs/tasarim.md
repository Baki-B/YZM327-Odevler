# Agora — Tasarım Belgesi

Bu belgedeki diyagramlar Mermaid ile yazılmıştır (GitHub'da ve VS Code'da Mermaid eklentisiyle çizilir).

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
  KARARA_BAGLANDI --> [*]
  SONUCSUZ --> [*]
  note right of KARARA_BAGLANDI: Katılmayan, itiraz konusu açar (yeni bir TARTISMA)
```

Eleme eşikleri: 1. tur %5, 2. tur %5, 3. tur %10, 4. tur %20. Oran = ağırlıklı pay ile kişi payının küçüğü.

## 3. Oy verme ve sonuçlandırma (sıralı diyagram)

```mermaid
sequenceDiagram
  actor Y as Üye
  participant W as Web katmanı
  participant O as oylama.py
  participant U as uygunluk.py
  participant V as Veritabanı
  participant D as Kayıt defteri (3 düğüm)
  Y->>W: POST /oylama/12/oy (seçim, CSRF)
  W->>O: oy_ver()
  O->>U: oy_agirligi() — gözlemci mi, uzman mı?
  U-->>O: ağırlık (1 / 10) + açıklama
  O->>O: makbuz üret, taahhüt = SHA256(teklif|seçim|makbuz)
  O->>V: INSERT oylar (seçim, ağırlık, taahhüt)
  O->>V: (tur süresi dolunca) sayım → çift oran → eleme kuralları
  W->>V: COMMIT
  V->>D: kuyruktaki bloklar (OY, SONUC…) düğümlere yazılır
  W-->>Y: makbuz kodu (bir kez gösterilir)
  Y->>W: POST /defter/makbuz (teklif, makbuz)
  W->>D: taahhüdü ara
  D-->>Y: "Oyun blok #N'de kayıtlı, seçimin: …"
```

## 4. Varlık–ilişki (veri modeli)

```mermaid
erDiagram
  KULLANICILAR ||--o{ KONULAR : "açar"
  KULLANICILAR ||--o{ MESAJLAR : yazar
  KULLANICILAR ||--o{ OYLAR : verir
  KULLANICILAR ||--o{ DEVIRLER : "devreder / devralır"
  KULLANICILAR ||--o{ TAKIPLER : "takip eder"
  KULLANICILAR ||--o{ UZMANLIKLAR : "uzmandır"
  KATEGORILER ||--o{ KONULAR : alan
  KATEGORILER ||--o{ UZMANLIKLAR : alan
  KONUMLAR ||--o{ KULLANICILAR : oturur
  KONUMLAR ||--o{ KONULAR : "katılım kuralı"
  KONULAR ||--o{ KONULAR : "alt konu / itiraz"
  KONULAR ||--o{ MESAJLAR : içerir
  KONULAR ||--o{ TEKLIFLER : "oylanır"
  KULLANICILAR ||--o{ SIKAYETLER : "şikayet eder"
  MESAJLAR ||--o{ MESAJLAR : yanıt
  MESAJLAR ||--o{ MESAJ_SURUMLERI : "eski sürümler"
  TEKLIFLER ||--o{ SECENEKLER : içerir
  TEKLIFLER ||--o{ OYLAR : toplar
  TEKLIFLER ||--o| KARARLAR : "kabul edilen fikir"
  PARAMETRELER }o--|| YONETMELIK_MADDELERI : "metinde kullanılır"
```

## 5. Katmanlar

```mermaid
flowchart TB
  subgraph İstemciler
    Tarayici[Tarayıcı / PWA] ---|oturum + CSRF| Web
    Mobil[Mobil uygulama] ---|Bearer anahtar| API
  end
  Web[web/*.py — sayfalar] --> Is
  API[web/api.py — REST] --> Is
  Is[İş mantığı: konular, oylama, sonuclar, devir, uzmanlik, yönetmelik, graf, yz] --> VT[(SQLite)]
  VT -->|commit sonrası| Defter[(Düğüm A · B · C)]
  Zamanlayici[gorevler.tick — 30 sn] --> Is
```

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
