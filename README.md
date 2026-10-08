# Agora

Herkesin konu açtığı, herkesin bir fikir yazdığı ve fikirlerin tur tur oylanarak tek bir karara indiği bir forum.
Konu açılınca 24 saat tartışılır; sonra en fazla beş turluk fikir oylaması başlar: her turda az oy alan fikirler elenir
(%5, %5, %10, %20), beşinci turda en çok oy alan kazanır. Bir fikir %75'i bulursa ya da tek başına kalırsa hemen kabul edilir.
Mesajlar silinmez, karara katılmayan itiraz konusu açar ve her olay kayıt defterine yazılır.

Yazılım Mühendisliğine Giriş dersi ödevi.

**Hemen dene (kurulum gerekmez):** <https://baki-b.github.io/YZM327-Odevler/> — uygulamanın tamamı tarayıcıda çalışır
(aşağıda "Tarayıcı sürümü"). Telefonda aynı adresi açıp "Ana ekrana ekle" ile uygulama gibi kurulabilir.

| Belge | İçinde |
|---|---|
| [docs/rapor/Agora_Proje_Raporu.pdf](docs/rapor/Agora_Proje_Raporu.pdf) | **Proje raporu (PDF, kapak + 4 sayfa):** teknik ayrıntılar, SOLID ve GoF desenleri, problem çerçeveleme, ölçümler, dağıtım. Kaynağı `docs/rapor/rapor.html` |
| [docs/analiz.md](docs/analiz.md) | **Problem çerçeveleme ve gereksinim analizi:** YZ gerekli mi?, tek sayfalık kanvas, iş/ürün/koruyucu metrikler, ölçülmüş temel çizgi ve hata analizi, kısıtlar, paydaşlar, ön-otopsi, ölçülmüş gecikme ve ölçeklenme |
| [docs/tasarim.md](docs/tasarim.md) | UML diyagramları; **SOLID ilkeleri ve tasarım desenlerinin** (State, Strategy, Template Method, Registry, Chain of Responsibility, Adapter, Memento, Observer, Repository, Facade…) dosya dosya karşılığı ve sınıf diyagramları |
| [docs/rehber.md](docs/rehber.md) | Uygulamanın bütün ayrıntıları ve kullanılan mimariler, sade bir dille |

## Tarayıcı sürümü (GitHub Pages, sunucusuz)

GitHub Pages yalnızca dosya sunar, Python çalıştırmaz. Bu yüzden Agora'nın **aynı kodu** ziyaretçinin tarayıcısında,
WebAssembly üzerinde çalışan Python (Pyodide) ile çalıştırılır. Her ziyaretçi kendi tarayıcısında, demo verisiyle dolu, gerçek ve
çalışan bir kopya açar. Veriler yalnızca o tarayıcıda (IndexedDB) saklanır. Ayrıntılar: `docs/tasarim.md` 9. bölüm.

```
Tarayıcı ──► index.html (kabuk) ──► Web Worker: Pyodide + Flask (forum/ paketi) ──► SQLite ve defter düğümleri (IndexedDB)
                 ▲                              ▲
                 └── sw.js (service worker): app/ altındaki her sayfa ve API isteğini yakalayıp işçiye iletir
```

| Komut / adım | Ne yapar |
|---|---|
| `python tarayici/derle.py` | Siteyi `_site/` klasörüne üretir (Pyodide ve paketleri indirip SHA-256 özetlerini doğrular) |
| `python -m http.server -d _site 8000` | Yerelde dener: <http://localhost:8000/> |
| GitHub'da bir kez: **Settings › Pages › Source: GitHub Actions** | Sonra `main` dalına her gönderimde `.github/workflows/sayfalar.yml` testleri çalıştırır, siteyi derler ve yayınlar (Actions sekmesinden elle de başlatılabilir) |

İlk açılışta yaklaşık 15 MB indirilir (sonra önbellekten); site bir kez açıldıktan sonra internetsiz de çalışır. Sunum kipi
açıktır ("Süreyi ilerlet"). Kabuktaki **Sıfırla** düğmesi bu tarayıcıdaki verileri silip demoyu baştan yükler.

**Mobil:** Telefonda adresi açıp **Ana ekrana ekle** (Android: Chrome ⋮ menüsü, iPhone: Safari paylaş düğmesi) — tam ekran,
çevrimdışı çalışan bir uygulama olur. Expo Go uygulamasında (`mobil-expo/`) adres ekranındaki **"Sunucusuz demoyu aç"** düğmesi
aynı adresi açar (Android). Capacitor uygulaması da bu adrese yönlendirilebilir: `npm run adres -- https://baki-b.github.io/YZM327-Odevler`.

## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt
python calistir.py
```

Ya da klasördeki **`baslat.bat`** dosyasına çift tıkla. Tarayıcı kendiliğinden **http://127.0.0.1:5000** adresinde açılır
(port doluysa sıradaki boş port kullanılır ve ekrana yazılır). Sunucu penceresini kapatma.

| Komut | Ne yapar |
|---|---|
| `python calistir.py --sifirla` | Veritabanını ve kayıt defterini silip demo verisini baştan yükler |
| `python calistir.py --ag` | Aynı Wi-Fi'daki telefondan erişim (ekrana yazılan adres) |
| `python calistir.py --yonetici Baki` | Bir üyeyi yönetici yapar (ilk yönetici için; sonrası yönetim panelinden) |
| `python calistir.py --demo` | Sunum kipi: yönetim panelinde "Süreyi ilerlet" düğmesi açılır (24/48 saat beklememek için) |
| `python calistir.py --demo-verisiz` | Boş veritabanına demo verisini (ve şifresi herkesçe bilinen demo hesaplarını) yüklemez |
| `python -m unittest discover testler` | 181 otomatik test (~7 sn) |
| `python -m pytest` ya da `uv run pytest` | Aynı testler pytest ile (ayarlar `pyproject.toml`'da) |
| `python olcum/denetim_olcumu.py` | Denetim kurallarının kesinlik/duyarlılık ölçümü (temel çizgilerle karşılaştırmalı; geliştirme, test ve görülmemiş son küme) |
| `python olcum/gecikme_olcumu.py` | Sayfaların p50/p95 yanıt süresi (`--defter-blok 50000` ile büyük defterde) |
| `python olcum/urun_metrikleri.py` | İş, ürün ve koruyucu metrikler |

**Ortam değişkenleri:** `FORUM_VERITABANI`, `FORUM_GIZLI_ANAHTAR` (oturum anahtarı; verilmezse üretilip yalnızca sahibinin
okuyabildiği dosyada saklanır), `FORUM_HTTPS=1` (HTTPS arkasında güvenli çerez), `FORUM_ANLIK_ILETISIM`, `FORUM_SIFRE_YONTEMI`.

**Site adı:** `forum/ayarlar.py` içindeki `SITE_ADI` değiştirilerek tek yerden değiştirilir.
**Arayüz ("Sade akış"):** kenar menüsü yok; üç bölüm var: Konular (Akış, Keşfet, Kategoriler), Oylamalar (gündem, kararlar),
Meclis (nasıl işler, yönetmelik, kayıt defteri, üye ağı, şeffaflık günlüğü, API).
**Gündem ve trendler:** konu akışının üstünde vitrin (şu an gündemde, süresi dolanlar, son karar), yanında trend konular, öne çıkan
kelimeler, yakında bitenler ve kategorilerin nabzı; **Keşfet** sayfasında son 24 saatin sayıları, haftanın en etkin üyeleri ve canlı akış.
**Kategoriler:** 7 temel alan (Bilim, Sağlık, Siyaset, Eğitim, Teknoloji, Ekonomi, Kültür ve Sanat) + her konuya açık **Genel**.
Her üye yeni ana ya da alt kategori önerebilir; bütün üyeler oylar (salt çoğunluk), kabul edilirse kategori eklenir.
Kategoriler sayfasında arama (ad ve kavramlarda), süzme (ana, alt, topluluğun ekledikleri, dolu olanlar) ve sıralama (popüler,
son etkinlik, ad, en yeni) vardır.
**Giriş katmanı:** ziyaretçi `/` adresinde önce tanıtım sayfasını görür (nasıl işler, canlı sayılar, gündemdeki konular);
giriş yapmış üye doğrudan konu akışına (`/konular`) düşer. Giriş, üye ol ve şifre sıfırlama sayfaları iki sütunludur.
**Renkler (iki renk):** ana renk taş beyazı `#ebe7df` (kartlarda `#f6f4ef`), yan renk kaktüs yeşili `#4a6642` ve tonları.
Değerler `forum/ayarlar.py` (`TAS_BEYAZI`, `GRI`, `YESIL`) ve `forum/static/style.css` (`:root`) içindedir.
**Panelim (`/profil`):** üyenin kendi işleri tek yerde: özet (oyunu bekleyen oylamalar, açtığı konular, son mesajları),
bildirimler, hesap bilgileri ve adres, oy devri, uzmanlık, güvenlik (şifre, kurtarma kodu), uygulama ve API anahtarları.
**Yönetim paneli (`/yonetim`, yalnızca yöneticiler):** pano (sayılar, son 14 günün etkinliği, konu durumları, ilgilenilmesi
gerekenler), üyeler (arama, yönetici yapma, askıya alma), şikayetler, konular ve oylamalar (yalnızca izleme),
kategoriler (ekleme, ad ve renk değiştirme), sistem (site duyurusu, yeni üyeliği açma/kapama, yapay zeka hesapları, kayıt
defteri denemesi, veritabanı yedeği) ve süzülebilir günlük. **Yönetici yalnızca siteyi yönetir:** içerik silemez, uzman atayamaz,
oylamaların süresine ve sonucuna dokunamaz (tek istisna: sunum kipindeki "Süreyi ilerlet", yalnızca beklemeyi kısaltır); oyu herkes gibi 1'dir. Her işlemi şeffaflık günlüğüne, yetki ve askı işlemleri
kayıt defterine de yazılır.
**Expo Go uygulaması (`mobil-expo/`):** telefona Expo Go'yu kur, `python calistir.py --ag` ile forumu, `mobil-expo`
klasöründe `npx expo start` ile Expo'yu başlat, QR kodu okut (Expo SDK 57). Adımlar `mobil-expo/BENIOKU.md` dosyasında.
**Mobil uygulama (`mobil/`):** web sitesini açan bir Android uygulaması (Capacitor). Aynı sayfaları, aynı hesabı ve aynı
veritabanını kullanır; telefonda alt sekme çubuğu, geri tuşu ve çentik boşlukları uygulamaya göre ayarlıdır. APK oluşturma
adımları `mobil/BENIOKU.md` dosyasında.
**Şikayet kutusu:** üyeler bir mesajı ya da konuyu şikayet eder (neden + açıklama). Şikayet, aynı içeriği en az 3 farklı üye
şikayet edince yöneticilere ulaşır. Yönetici şikayeti gizleme/kaldırma oylamasına alır ya da yersiz bulup kapatır; karar yine
oylamayla verilir (3/4), şikayet edene sonuç bildirilir.
**Toplu bildirim:** yönetici bütün üyelere, bir il/ilçedeki üyelere, bir alanın uzmanlarına ya da yöneticilere bildirim gönderir.
**Anlık bildirim:** her bildirim, bildirimleri açmış cihazlara da gider (Panelim › Bildirimler › Bu cihazda aç). Tarayıcı için
`pip install pywebpush` yeter (HTTPS ya da localhost gerekir); Android uygulaması için Firebase ayarı `mobil/BENIOKU.md`'de.
**Karanlık tema:** cihaz koyu moddaysa kendiliğinden açılır; hesap menüsündeki Görünüm'den Otomatik / Açık / Koyu seçilir.
**Yapay zeka üye:** yalnızca kısa özet yazar (tartışma özeti, tur özeti). Oy kullanmaz; dış servis gerektirmez. Özetler bilinçli
olarak kural tabanlıdır: her sayı veritabanından gelir (gerekçe: [analiz.md](docs/analiz.md) 3. bölüm, "YZ gerekli mi?").

### Demo hesapları (şifre hepsinde `forum1234`)

| Takma ad | Özellik |
|---|---|
| `yonetici` | Yönetici: yönetim paneline girer (yetki verir, askıya alır, şikayetlere bakar) |
| `ayse`, `elif` (17 yaş) | İstanbul › Kadıköy |
| `mehmet` · `burak` | İstanbul › Beşiktaş · İstanbul › Kartal |
| `zeynep` | Ankara (İstanbul konularında gözlemci) |
| `can`, `selin` | İzmir |
| `ece` · `onur` · `defne` · `mert` | İzmir › Konak · Ankara › Keçiören · İstanbul › Beşiktaş · Bursa |
| `dr.deniz` | **Uzman: Sağlık** |
| `kaan.hoca` | **Uzman: Teknoloji › Yazılım** |
| `Bilge` | **Yapay zeka üye** (giriş yapamaz) |

## Ödevdeki maddeler

Tam karşılık tablosu sitede **Nasıl işler? → Ödev gereksinimleri** bölümündedir (`/hakkinda#gereksinimler`). Özet:

| Madde | Karşılığı |
|---|---|
| Herkes konu açar, düzenler, silme teklif eder | Konu hemen açılır; sahibi tartışma sürerken düzenler (eski hâli görünür); kaldırma 3/4 oylamayla |
| Çoğunluk kararı | Fikir oylaması: en fazla 5 tur, eleme eşikleri, ezici üstünlük |
| Alt konular | Her konunun altına alt konu açılır; üst konunun kurallarını sadece daraltabilir |
| Konu sonunda fikir uzlaşması | Turlar sonunda tek fikir kalır ve karar olur |
| Giriş ekranı; ad soyad, adres, doğum tarihi, şifre, takma ad | Kayıt/giriş; bilgiler gizli, görünen takma ad; kurtarma kodu |
| Bilgiler kısıt (İstanbul konusuna İstanbullular, diğerleri gözlemci) | Konum hiyerarşisi + yaş kuralı; gözlemci modu; uygunluk puanı |
| Her birey eşit / bazıları daha eşit | Kurallar herkese eşit, herkes bir fikir yazar; uzman oyu 10 sayılır, çift oranla dengelenir |
| Kurallar ve uygunluk ölçümü (ontoloji); yönetmelik denetlesin | Yönetmelik maddeleri D1–D7 ontolojiyle denetler; yönetmelik oylamayla değişir |
| Tartışmalar silinmez; (bir kısmı) silinmek istenirse oylama | Mesaj silinemez; düzenlenirse eski hâli görünür; tek ya da birden fazla mesaj tek oylamayla gizlenir (3/4), iz kalır |
| Oy hakkı havale | Oy devri: genel / kategori / konu; zincirleme; tavanlı |
| Azınlıkları koruma | Herkes fikir yazar, itiraz konusu, çift oran, çekimserin paydada sayılması, 3/4 eşikler, korunan haklar, devir tavanı, uzman kontenjanı, gizli oy |
| Uygulama + web sitesi | Expo Go ve Android uygulaması, telefona kurulabilen web uygulaması (PWA) ve REST API |
| Dağıtık defter | 3 düğümlü hash zinciri, uzlaşma, kurcalama tespiti ve onarım, oy makbuzu |
| Bilirkişi (uzman) entegrasyonu | Uzmanlık: ön şart + kontenjan + alanın üyelerinin oylaması; yönetici atayamaz |
| Yapay zeka entegrasyonu | YZ üye tartışmayı ve tur sonuçlarını kısaca özetler |
| İnsanları grafta tut | Üye ağı: devir, yanıt, takip; PageRank, Gini; oy benzerliğinden en az 3 kişilik görüş grupları (gizli oy korunur) |
| Problem çerçeveleme analizi (ders) | `docs/analiz.md`: YZ gerekli mi?, kanvas, metrikler, ölçülmüş temel çizgi, kısıtlar, paydaşlar, ön-otopsi |
| SOLID ve GoF desenleri (ders) | `docs/tasarim.md` 8. bölüm: her ilke ve desen, önceki sorunu, dosyası ve testiyle |

## Fikir oylaması

| Aşama | Süre | Kural |
|---|---|---|
| Tartışma | 24 saat | Mesajlar ve fikirler yazılır (kişi başı bir fikir) |
| 1. tur | 48 saat | %5 altı elenir; tur boyunca yeni fikir yazılabilir |
| 2. tur | 24 saat | %5 altı elenir |
| 3. tur | 24 saat | %10 altı elenir |
| 4. tur | 24 saat | %20 altı elenir |
| 5. tur | 24 saat | En çok oy alan fikir kabul edilir |

- **Ezici üstünlük:** her turda %75 ve üstü alan fikir hemen kabul edilir.
- **Tek kalan:** elemeden sonra tek fikir kaldıysa o kabul edilir (ör. yedi fikir %5 altında, sekizinci %65).
- **Oran:** ağırlıklı oylardaki pay ile kişi sayısındaki payın küçüğü; çekimserler paydada sayılır.
- **Sonuçsuz:** yeter sayı yoksa, hiçbir fikir eşiği geçemezse ya da son turda eşitlik olursa.

## Diğer oy eşikleri

| İşlem | Eşik |
|---|---|
| Mesaj gizleme, konu kaldırma | 3/4 |
| Uzmanlık başvurusu (alanın üyeleri oylar) | 2/3 |
| Yeni kategori (bütün üyeler oylar) | Salt çoğunluk |
| Yönetmelik değişikliği | 2/3 |
| Temel hak değişikliği | 3/4 |

## Demo senaryosu (sunum için)

Sunumda beklememek için forumu `python calistir.py --demo` ile başlat; yönetim panelinde "Süreyi ilerlet" düğmesi açılır.

1. **Konular:** Üstte kategori çipleri ve durum filtresi; listede her aşamada bir konu var (tartışmada, oylamada, karara bağlanmış, sonuçsuz).
2. **"Final projesi":** Beş turun tamamı. Oylamalar sayfasından turlara tek tek bak: 1. turda %5 altında kalan fikir (%4,5), 3. turda %10 altındaki fikir (%9) elendi; 5. turda Python kazandı. Uzman oyu açık ve gerekçeli.
3. **"Farklı teknoloji deneyen gruplara ek puan":** Yukarıdaki karara açılmış **itiraz konusu**.
4. **"Kulüp toplantıları":** İlk turda %78,5 → **ezici üstünlük** (eşik %75), hemen karar.
5. **"Yemekhane":** 2. tur sürüyor. `burak` ile gir, oy ver, makbuzu al. Elenen fikir üstü çizili duruyor; Bilge'nin özetleri tartışmanın içinde.
6. **"Final sınavları":** Yeter sayı olmadığı için **sonuçsuz**.
7. `zeynep` ile gir → İstanbul konusunda **gözlemci**; `ayse` ile gir → birkaç mesajı işaretle → **toplu gizleme oylaması** (3/4).
8. `mehmet` ile **Panelim › Uzmanlık:** ön şart, kontenjan ve süren başvuru.
9. `yonetici` ile **Yönetim paneli:** tabanı dolmuş şikayet; "Süreyi ilerlet" ile bir konuyu tartışmadan oylamaya geçir.
10. **Kayıt defteri:** Yönetim paneli › Sistem › "Bozmayı dene" → kayıt defteri sayfasında düğüm bozuk görünür → "Onar". Makbuz kodunu kayıt defteri sayfasında doğrula.

## Mimari

```
forum/
  ayarlar.py         site adı, sabitler, yönetmeliğin varsayılan parametreleri ve anlamlı aralıkları
  yonetmelik.py      maddeler, oylamayla değişen parametreler
  denetim.py         yönetmelik denetimi D1–D7: her madde zincirin bir halkası (Chain of Responsibility)
  ontoloji.py        konum ve kategori hiyerarşileri, kavram terimleri, benzerlik ölçümü
  uygunluk.py        kim katılımcı, kim gözlemci; oyu kaç sayılır
  konular.py         konu açma/düzenleme, fikirler, turların açılması, alt konu, itiraz, mesajlar, toplu gizleme
  konu_durumlari.py  konunun durumları ve her durumda izin verilenler (State)
  oylama.py          teklif, oy + makbuz, sayım (çift oran, çekimser, yeter sayı), sonuçlandırma iskeleti (Template Method)
  teklif_turleri.py  altı oylama türü (Strategy + Registry)
  sonuclar.py        fikir turunun eleme kuralları (saf işlev) ve turun kararı (anlık görüntü, Memento)
  kararlar.py        kabul edilen fikirlerin kaydı
  devir.py           oy devri            uzmanlik.py   ön şart, kontenjan, başvuru
  graf.py            üye ağı: takip, PageRank, Gini, görüş grupları (en az 3 kişilik)
  defter.py          dağıtık kayıt defteri: hash zinciri, 3 düğüm, uzlaşma, onarım, tutarlılık;
                     düğüm depoları (Repository), commit aboneliği (Observer), doğrulama önbelleği
  yz.py              yapay zeka üyenin kural tabanlı özetleri
  gorunum.py         konu sayfasının verisi (Facade)
  metin.py           yüzde biçimi, kısaltma, güvenli yönlendirme      hatalar.py  kural hatası, sayı ayrıştırma
  yonetim.py         yönetim paneli: pano sayıları, yetki, askı, kategoriler, site ayarları, toplu bildirim, yedek
  sikayetler.py      şikayet kutusu      anlik.py  anlık bildirim kanalları: Web Push ve Firebase (Adapter)
  kategoriler.py     kategori önerisi ve kategoriler sayfası      gundem.py  trendler, öne çıkan kelimeler, kategori nabzı
  kullanicilar.py, guvenlik.py, bildirimler.py, arama.py, gorevler.py, veritabani.py (kayıt noktası, Memento)
  web/               HTTP katmanı: istek.py (istek öncesi zincir), hata_sayfalari.py, sablon.py, Flask blueprint'leri, REST API
  templates/         sayfalar; panel/ = Panelim, yonetim/ = yönetim paneli     static/  CSS, JS, ağ çizimi, PWA dosyaları
olcum/               ölçüm betikleri ve etiketli örnekler (gelistirme.csv, test.csv)
mobil-expo/          Expo Go uygulaması (Expo SDK 57, WebView)
mobil/               Android uygulaması (Capacitor): capacitor.config.json, android/ projesi, BENIOKU.md
testler/             181 test: iş kuralları, web, hata düzeltmeleri, desenler, ölçüm
docs/                analiz.md (problem çerçeveleme), tasarim.md (UML + desenler), rehber.md (ayrıntılar)
```

**Güvenlik:**
- Şifreler hash'lenir; şifre politikası uygulanır; 5 hatalı girişte 10 dakika kilit.
- Şifre kurtarma kodu da sadece hash olarak saklanır.
- Her formda CSRF koruması var.
- İçerik güvenlik politikası (CSP) ve diğer güvenlik başlıkları gönderilir.
- SQL sorguları parametrelidir; şablonlar otomatik kaçış kullanır.
- API'de kişisel veri döndürülmez.
- Şifre değişince eski oturumlar ve API anahtarları geçersiz olur; girişten sonra yalnızca site içi adrese dönülür; anlık
  bildirim adresleri yalnızca bilinen bildirim servislerine gidebilir. Ayrıntılar: `docs/rehber.md` 24. bölüm.

## YZ kullanım beyanı

Bu ödevin yazılım mühendisliği revizyonunda (SOLID/GoF incelemesi, hata düzeltmeleri, desenlerin uygulanması, ölçüm betikleri ve
`docs/analiz.md`, `docs/tasarim.md` belgelerinin taslakları) bir YZ kodlama asistanı (Claude Code) kullanıldı. Asistanın
önerdiği her değişiklik otomatik testlerle doğrulandı; bulunan her hata için önce hatayı yeniden üreten bir test yazıldı.
Belgelerdeki sayılar `olcum/` betikleriyle ölçülmüştür.
