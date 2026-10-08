# Agora

Herkesin konu açıp fikir yazabildiği, fikirlerin tur tur oylanarak tek bir karara indiği bir forum. Konu açıldıktan sonra 24 saat tartışılır; ardından en fazla beş turluk oylamada az oy alan fikirler elenir ve beşinci turda en çok oy alan fikir kabul edilir (%75'i bulan fikir hemen kabul edilir). Mesajlar silinmez; her olay kayıt defterine yazılır.

Yazılım Mühendisliğine Giriş dersi ödevi.

**Hemen dene (kurulum gerekmez):** <https://baki-b.github.io/YZM327-Odevler/>. Uygulamanın tamamı tarayıcıda çalışır. Telefonda açmanın yolları aşağıda, [Telefonda aç](#telefonda-aç) bölümünde.

| Belge | İçinde |
|---|---|
| [docs/rapor/Agora_Proje_Raporu.pdf](docs/rapor/Agora_Proje_Raporu.pdf) | **Proje raporu** (PDF, kapak + 4 sayfa): teknik ayrıntılar, SOLID ve GoF desenleri, problem çerçeveleme, ölçümler, dağıtım. Kaynağı `docs/rapor/rapor.html` |
| [docs/analiz.md](docs/analiz.md) | **Problem çerçeveleme ve gereksinim analizi:** YZ gerekli mi?, tek sayfalık kanvas, iş/ürün/koruyucu metrikler, ölçülmüş temel çizgi ve hata analizi, kısıtlar, paydaşlar, ön-otopsi, ölçülmüş gecikme ve ölçeklenme |
| [docs/tasarim.md](docs/tasarim.md) | UML diyagramları; **SOLID ilkeleri ve GoF tasarım desenleri** (State, Strategy, Template Method, Chain of Responsibility, Adapter, Memento, Observer, Repository, Facade) dosya dosya, sınırları ve sınıf diyagramlarıyla |
| [docs/rehber.md](docs/rehber.md) | Uygulamanın bütün ayrıntıları ve kullanılan mimariler, sade bir dille |
| [laboratuvar/](laboratuvar/README.md) | **S02-50 mini laboratuvarı:** Türkçe/İngilizce token oranı (tiktoken), nedensel maskeli dikkat ısı haritası (NumPy), sıcaklık deneyi, YZ kodlama aracının önerdiği import'ların doğrulanması; **S01-49 soru 6:** YZ'nin yazdığı testlerin doğruluğu ve mutasyon testi |
| [docs/tartisma_sorulari.md](docs/tartisma_sorulari.md) | Ders sunumlarındaki tartışma sorularına kısa yanıtlar (S01, S02; TD-59'unkiler `docs/tasarim.md` 8.7–8.8'de) |

## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt
python calistir.py
```

Ya da klasördeki **`baslat.bat`** dosyasına çift tıkla. Tarayıcı **http://127.0.0.1:5000** adresinde açılır (port doluysa sıradaki boş port kullanılır ve ekrana yazılır). Sunucu penceresini kapatma.

| Komut | Ne yapar |
|---|---|
| `python calistir.py --sifirla` | Veritabanını ve kayıt defterini silip demo verisini baştan yükler |
| `python calistir.py --ag` | Aynı Wi-Fi'daki telefondan erişim (ekrana yazılan adres) |
| `python calistir.py --yonetici Baki` | Bir üyeyi yönetici yapar (ilk yönetici için; sonrası yönetim panelinden) |
| `python calistir.py --demo` | Sunum kipi: yönetim panelinde "Süreyi ilerlet" düğmesi açılır (24/48 saat beklememek için) |
| `python calistir.py --demo-verisiz` | Boş veritabanına demo verisini (ve şifresi herkesçe bilinen demo hesaplarını) yüklemez |
| `python -m unittest discover testler` | 204 otomatik test (~12 sn) |
| `python -m pytest` ya da `uv run pytest` | Aynı testler pytest ile (ayarlar `pyproject.toml`'da) |
| `python olcum/denetim_olcumu.py` | Denetim kurallarının kesinlik/duyarlılık ölçümü (temel çizgilerle karşılaştırmalı; geliştirme, test ve görülmemiş son küme) |
| `python olcum/gecikme_olcumu.py` | Sayfaların p50/p95 yanıt süresi (`--defter-blok 50000` ile büyük defterde) |
| `python olcum/urun_metrikleri.py` | İş, ürün ve koruyucu metrikler |

**Ortam değişkenleri:** `FORUM_VERITABANI`, `FORUM_GIZLI_ANAHTAR` (oturum anahtarı; verilmezse üretilip yalnızca sahibinin okuyabildiği dosyada saklanır), `FORUM_HTTPS=1` (HTTPS arkasında güvenli çerez), `FORUM_ANLIK_ILETISIM`, `FORUM_SIFRE_YONTEMI`.

**Site adı:** `forum/ayarlar.py` içindeki `SITE_ADI` değiştirilerek tek yerden değiştirilir.

**İsteğe bağlı anlık bildirim:** `pip install pywebpush==2.5.0`.

### Tarayıcı sürümü (GitHub Pages, sunucusuz)

GitHub Pages yalnızca dosya sunar, Python çalıştırmaz. Bu yüzden Agora'nın aynı kodu ziyaretçinin tarayıcısında, WebAssembly üzerinde çalışan Python (Pyodide) ile çalışır. Her ziyaretçi kendi demo kopyasını açar; veriler yalnızca o tarayıcıda (IndexedDB) saklanır. Ayrıntı: `docs/tasarim.md` 9. bölüm.

| Komut / adım | Ne yapar |
|---|---|
| `python tarayici/derle.py` | Siteyi `_site/` klasörüne üretir (Pyodide ve paketleri indirip SHA-256 özetlerini doğrular) |
| `python -m http.server -d _site 8000` | Yerelde dener: <http://localhost:8000/> |
| GitHub'da bir kez: **Settings › Pages › Source: GitHub Actions** | Sonra `main` dalına her gönderimde `.github/workflows/sayfalar.yml` testleri çalıştırır, siteyi derler ve yayınlar (Actions sekmesinden elle de başlatılabilir) |

İlk açılışta yaklaşık 15 MB indirilir (sonra önbellekten); site bir kez açıldıktan sonra internetsiz de çalışır. Sunum kipi açıktır ("Süreyi ilerlet"). Kabuktaki **Sıfırla** düğmesi bu tarayıcıdaki verileri silip demoyu baştan yükler.

### Telefonda aç

<img src="docs/agora_qr.png" alt="Agora sitesinin QR kodu" width="120" align="right">

| Yol | Nasıl |
|---|---|
| **Android uygulaması** | [Agora.apk](https://github.com/Baki-B/YZM327-Odevler/releases/latest/download/Agora.apk) dosyasını telefonda indirip kur. Uygulama siteyi tam ekran açar. APK her `main` gönderiminde GitHub Actions ile yeniden derlenir. |
| **Ana ekrana ekle** (Android ve iPhone) | QR kodu okut ya da siteyi aç; Chrome'da ⋮ menüsünden, Safari'de paylaş düğmesinden "Ana ekrana ekle". Uygulama gibi açılır, internetsiz de çalışır. |
| **Expo Go** | `mobil-expo/` klasörü. Expo Go'da **"Sunucusuz demoyu aç"** düğmesi siteyi açar; kendi sunucuna bağlanmak da mümkün. Adımlar `mobil-expo/BENIOKU.md` dosyasında. |

Android uygulamasının kaynağı `mobil/` klasöründedir (Capacitor); kendi sunucuna bağlamak ve elle derlemek için `mobil/BENIOKU.md`.

### Demo hesapları (şifre hepsinde `forum1234`)

| Takma ad | Özellik |
|---|---|
| `yonetici` | Yönetici: sayfa altındaki **Yönetici girişi**'nden yönetim paneline girer (yetki verir, askıya alır, şikayetlere bakar) |
| `ayse`, `elif` (17 yaş) | İstanbul › Kadıköy |
| `mehmet` · `burak` | İstanbul › Beşiktaş · İstanbul › Kartal |
| `zeynep` | Ankara (İstanbul konularında gözlemci) |
| `can`, `selin` | İzmir |
| `ece` · `onur` · `defne` · `mert` | İzmir › Konak · Ankara › Keçiören · İstanbul › Beşiktaş · Bursa |
| `dr.deniz` | **Uzman: Sağlık** |
| `kaan.hoca` | **Uzman: Teknoloji › Yazılım** |
| `Bilge` | **Yapay zeka üye** (giriş yapamaz) |

### Sunum senaryosu

Sunumda beklememek için `python calistir.py --demo` ile başlat; yönetim panelinde "Süreyi ilerlet" düğmesi açılır.

1. **Konular:** Üstte kategori çipleri ve durum filtresi; listede her aşamada bir konu var (tartışmada, oylamada, karara bağlanmış, sonuçsuz).
2. **"Final projesi":** Beş turun tamamı. Oylamalar sayfasından turlara tek tek bak: 1. turda %5 altında kalan fikir (%4,5), 3. turda %10 altındaki fikir (%9) elendi; 5. turda Python kazandı. Uzman oyu açık ve gerekçeli.
3. **"Farklı teknoloji deneyen gruplara ek puan":** Yukarıdaki karara açılmış **itiraz konusu**.
4. **"Kulüp toplantıları":** İlk turda %78,5 → **ezici üstünlük** (eşik %75), hemen karar.
5. **"Yemekhane":** 2. tur sürüyor. `burak` ile gir, oy ver, makbuzu al. Elenen fikir üstü çizili duruyor; Bilge'nin özetleri tartışmanın içinde.
6. **"Final sınavları":** Yeter sayı olmadığı için **sonuçsuz**.
7. `zeynep` ile gir → İstanbul konusunda **gözlemci**; `ayse` ile gir → birkaç mesajı işaretle → **toplu gizleme oylaması** (3/4).
8. `mehmet` ile **Panelim › Uzmanlık:** ön şart, kontenjan ve sürmekte olan başvuru.
9. Sayfa altındaki **Yönetici girişi** → `yonetici` ile **Yönetim paneli:** tabanı dolmuş şikayet; "Süreyi ilerlet" ile bir konuyu tartışmadan oylamaya geçir.
10. **Kayıt defteri:** Yönetim paneli › Sistem › "Bozmayı dene" → kayıt defteri sayfasında düğüm bozuk görünür → "Onar". Makbuz kodunu kayıt defteri sayfasında doğrula.

## Ödev maddeleri

Tam karşılık tablosu sitede **Nasıl işler? → Ödev gereksinimleri** bölümündedir (`/hakkinda#gereksinimler`).

| Madde | Karşılığı |
|---|---|
| Herkes konu açar, düzenler, silme teklif eder | Konu hemen açılır; sahibi tartışma sürerken düzenler (eski hâli görünür); kaldırma 3/4 oylamayla |
| Çoğunluk kararı | Fikir oylaması: en fazla 5 tur, eleme eşikleri, ezici üstünlük |
| Alt konular | Her konunun altına alt konu açılır; üst konunun kurallarını sadece daraltabilir |
| Konu sonunda fikir uzlaşması | Turlar sonunda tek fikir kalır ve karar olur |
| Giriş ekranı; ad soyad, adres, doğum tarihi, şifre, takma ad | Kayıt/giriş; bilgiler gizli, görünen takma ad; kurtarma kodu |
| Bilgiler kısıt (İstanbul konusuna İstanbullular, diğerleri gözlemci) | Konum hiyerarşisi + yaş kuralı; gözlemci modu; uygunluk puanı |
| Her birey eşit / bazıları daha eşit | Kurallar herkese eşit, herkes bir fikir yazar; uzman oyu 10 sayılır, çift oranla dengelenir |
| Kurallar ve uygunluk ölçümü (ontoloji); yönetmelik denetlesin | Yönetmelik maddeleri D1–D7 ontolojiyle denetler; yönetmelik oylamayla değişir. Kişisel veri engellenir; hakaret varsayılan olarak uyarılır (ölçüm sonucu, `docs/analiz.md` 6.5), topluluk "Engeller"e çekebilir |
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

### Fikir oylaması

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

### Diğer oy eşikleri

| İşlem | Eşik |
|---|---|
| Mesaj gizleme, konu kaldırma | 3/4 |
| Uzmanlık başvurusu (alanın üyeleri oylar) | 2/3 |
| Yeni kategori (bütün üyeler oylar) | Salt çoğunluk |
| Yönetmelik değişikliği | 2/3 |
| Temel hak değişikliği | 3/4 |

### Öteki özellikler

- **Kategoriler:** 7 temel alan (Bilim, Sağlık, Siyaset, Eğitim, Teknoloji, Ekonomi, Kültür ve Sanat) ve her konuya açık **Genel**. Her üye yeni kategori önerebilir; bütün üyeler oylar (salt çoğunluk). Kategoriler sayfasında arama, süzme ve sıralama vardır.
- **Gündem ve trendler:** Konu akışında vitrin, trend konular ve öne çıkan kelimeler; **Keşfet** sayfasında son 24 saatin sayıları ve canlı akış.
- **Giriş katmanı:** Ziyaretçi `/` adresinde tanıtım sayfasını görür; giriş yapmış üye doğrudan konu akışına (`/konular`) düşer.
- **Panelim (`/profil`):** oyunu bekleyen oylamalar, açtığın konular, bildirimler, hesap bilgileri, oy devri, uzmanlık, güvenlik (şifre, kurtarma kodu), uygulama ve API anahtarları.
- **Yönetim paneli (`/yonetim`, yalnızca yöneticiler):** üye arayüzünden ayrıdır; kendi giriş sayfası (`/yonetim/giris`, her sayfanın altındaki "Yönetici girişi") ve üye oturumundan bağımsız oturumu vardır. Bölümleri: pano, üyeler (yönetici yapma, askıya alma), şikayetler, konular ve oylamalar (yalnızca izleme), kategoriler, sistem (site duyurusu, yedek) ve günlük. **Yönetici yalnızca siteyi yönetir:** içerik silemez, uzman atayamaz, oylamaların süresine ve sonucuna dokunamaz (tek istisna: sunum kipindeki "Süreyi ilerlet", yalnızca beklemeyi kısaltır). Her işlem şeffaflık günlüğüne yazılır.
- **Şikayet kutusu:** Aynı içeriği en az 3 farklı üye şikayet ederse yöneticilere ulaşır. Yönetici şikayeti gizleme/kaldırma oylamasına alır ya da yersiz bulup kapatır; karar yine oylamayla verilir (3/4).
- **Toplu ve anlık bildirim:** Yönetici bütün üyelere, bir il/ilçeye, bir alanın uzmanlarına ya da yöneticilere bildirim gönderir. Anlık bildirim, bildirimleri açmış cihazlara da gider (Panelim › Bildirimler › Bu cihazda aç). Android uygulaması için Firebase ayarı `mobil/BENIOKU.md`'de.
- **Karanlık tema:** Cihaz koyu moddaysa kendiliğinden açılır; hesap menüsündeki Görünüm'den Otomatik / Açık / Koyu seçilir.
- **Yapay zeka üye (`Bilge`):** yalnızca kısa özet yazar (tartışma özeti, tur özeti). Oy kullanmaz; dış servis gerektirmez. Özetler kural tabanlıdır: her sayı veritabanından gelir (gerekçe: [analiz.md](docs/analiz.md) 3. bölüm).
- **Renkler:** taş beyazı `#ebe7df` ve kaktüs yeşili `#4a6642`. Değerler `forum/ayarlar.py` ile `forum/static/style.css` (`:root`) içindedir.

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
olcum/               ölçüm betikleri ve etiketli örnekler (gelistirme.csv, test.csv, son_test.csv)
laboratuvar/         S02-50 mini laboratuvarı (4 görev; sonuçlar laboratuvar/README.md)
mobil-expo/          Expo Go uygulaması (Expo SDK 57, WebView)
mobil/               Android uygulaması (Capacitor): capacitor.config.json, android/ projesi, BENIOKU.md
testler/             204 test: iş kuralları, web, hata düzeltmeleri, desenler, ölçüm
docs/                analiz.md (problem çerçeveleme), tasarim.md (UML + desenler), rehber.md (ayrıntılar)
```

Tarayıcı sürümünde aynı kod, şu zincirle çalışır:

```
Tarayıcı ──► index.html (kabuk) ──► Web Worker: Pyodide + Flask (forum/ paketi) ──► SQLite ve defter düğümleri (IndexedDB)
                 ▲                              ▲
                 └── sw.js (service worker): app/ altındaki her sayfa ve API isteğini yakalayıp işçiye iletir
```

## Güvenlik

- Şifreler hash'lenir; şifre politikası uygulanır; 5 hatalı girişte 10 dakika kilit.
- Şifre kurtarma kodu da yalnızca hash olarak saklanır.
- Her formda CSRF koruması var.
- İçerik güvenlik politikası (CSP) ve diğer güvenlik başlıkları gönderilir.
- SQL sorguları parametrelidir; şablonlar otomatik kaçış kullanır.
- API'de kişisel veri döndürülmez.
- Şifre değişince eski oturumlar ve API anahtarları geçersiz olur; girişten sonra yalnızca site içi adrese dönülür; anlık bildirim adresleri yalnızca bilinen bildirim servislerine gidebilir. Ayrıntılar: `docs/rehber.md` 24. bölüm.

## YZ kullanım beyanı

Ders sunumlarındaki çerçeveye göre (S01-46, 47; H2-59):

- **Araç:** Claude Code (Anthropic). Forumun ilk sürümü benim commit'imdir (`eae7510`, 1 Ekim 2026); sonraki commit'ler bu araçla yapıldı (git geçmişinde yazar "Claude").
- **Aracın yaptığı:** analiz ve tasarım belgeleri, SOLID ve GoF düzenlemeleri, hata düzeltmeleri ve testleri, ölçüm betikleri ve ölçüm örnekleri (`olcum/*.csv`), tarayıcı sürümü, mini laboratuvar, rapor taslağı.
- **Benim rolüm:** ürün fikri ve ilk sürüm; hedeflerin ve ders kaynaklarının verilmesi; kapsam kararları (rapor biçimi, GitHub Pages, mobil); sonuçların gözden geçirilmesi ve teslim kararı.
- **Doğrulama:** Testleri de YZ yazdığı için (S01-46):
  1. Düzeltme testleri düzeltmeden önceki koda karşı çalıştırılıp başarısız oldukları görüldü (`de73de8` 9/9, `0a01434` 7/7).
  2. Yayın ölçütleri sonuçlardan önce yazıldı; görülmemiş ölçüm kümesi ölçülmeden önce commit edildi (`dfa996e`). Sonuç ölçütü karşılamayınca hedef değiştirilmedi, D1 "Uyarır" düzeyine çekildi.
  3. Her gönderimde CI testleri, statik denetimi (pyflakes) ve ölçümü çalıştırır.
  4. Her inceleme bulgusu kodla ya da komut çıktısıyla doğrulandıktan sonra uygulandı.
- **Sınır:** Ölçüm örnekleri ve kurallar aynı araçla yazıldığı için başarım sayıları iyimser olabilir (`docs/analiz.md` 6.2). Hedefler ve maliyet birimleri varsayımdır.
