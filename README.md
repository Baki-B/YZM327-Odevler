# Agora

Herkesin konu açtığı, herkesin bir fikir yazdığı ve fikirlerin tur tur oylanarak tek bir karara indiği bir forum.
Konu açılınca 24 saat tartışılır; sonra en fazla beş turluk fikir oylaması başlar: her turda az oy alan fikirler elenir
(%5, %5, %10, %20), beşinci turda en çok oy alan kazanır. Bir fikir %75'i bulursa ya da tek başına kalırsa hemen kabul edilir.
Mesajlar silinmez, karara katılmayan itiraz konusu açar ve her olay kayıt defterine yazılır.

Yazılım Mühendisliğine Giriş dersi ödevi.

Uygulamanın bütün ayrıntıları ve kullanılan mimariler sade bir dille [docs/rehber.md](docs/rehber.md) dosyasında.

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
| `python -m unittest discover testler` | 94 otomatik test |

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
oylamaların süresine ve sonucuna dokunamaz; oyu herkes gibi 1'dir. Her işlemi şeffaflık günlüğüne, yetki ve askı işlemleri
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
**Yapay zeka üye:** yalnızca kısa özet yazar (tartışma özeti, tur özeti). Oy kullanmaz; dış servis gerektirmez.

### Demo hesapları (şifre hepsinde `forum1234`)

| Takma ad | Özellik |
|---|---|
| `yonetici` | Yönetici: yönetim paneline girer (yetki verir, askıya alır, şikayetlere bakar) |
| `ayse`, `elif` (17 yaş) | İstanbul › Kadıköy |
| `mehmet` · `burak` | İstanbul › Beşiktaş · İstanbul › Kartal |
| `zeynep` | Ankara (İstanbul konularında gözlemci) |
| `can`, `selin` | İzmir |
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
| İnsanları grafta tut | Üye ağı: devir, yanıt, takip, oy benzerliği; PageRank, Gini, görüş grupları |

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
2. **"Final projesi":** Beş turun tamamı. Oylamalar sayfasından turlara tek tek bak: 2. turda oy alamayan fikir, 3. turda %10 altındaki fikir elendi; 5. turda Python kazandı. Uzman oyu açık ve gerekçeli.
3. **"Farklı teknoloji deneyen gruplara ek puan":** Yukarıdaki karara açılmış **itiraz konusu**.
4. **"Kulüp toplantıları":** İlk turda %80 → **ezici üstünlük**, hemen karar.
5. **"Yemekhane":** 2. tur sürüyor. `burak` ile gir, oy ver, makbuzu al. Elenen fikir üstü çizili duruyor; Bilge'nin özetleri tartışmanın içinde.
6. **"Final sınavları":** Yeter sayı olmadığı için **sonuçsuz**.
7. `zeynep` ile gir → İstanbul konusunda **gözlemci**; `ayse` ile gir → birkaç mesajı işaretle → **toplu gizleme oylaması** (3/4).
8. `mehmet` ile **Panelim › Uzmanlık:** ön şart, kontenjan ve süren başvuru.
9. `yonetici` ile **Yönetim paneli:** tabanı dolmuş şikayet; "Süreyi ilerlet" ile bir konuyu tartışmadan oylamaya geçir.
10. **Kayıt defteri:** Yönetim paneli › Sistem › "Bozmayı dene" → kayıt defteri sayfasında düğüm bozuk görünür → "Onar". Makbuz kodunu kayıt defteri sayfasında doğrula.

## Mimari

```
forum/
  ayarlar.py      site adı, sabitler, yönetmeliğin varsayılan parametreleri
  yonetmelik.py   maddeler, oylamayla değişen parametreler, ontoloji tabanlı denetim motoru
  ontoloji.py     konum ve kategori hiyerarşileri, kavram terimleri, benzerlik ölçümü
  uygunluk.py     kim katılımcı, kim gözlemci; oyu kaç sayılır
  konular.py      konu açma/düzenleme, fikirler, turların açılması, alt konu, itiraz, mesajlar, toplu gizleme
  oylama.py       teklif, oy + makbuz, sayım (çift oran, çekimser, yeter sayı), sonuçlandırma
  sonuclar.py     oylama sonuçlanınca ne olur (teklif türüne göre); eleme kuralları
  kararlar.py     kabul edilen fikirlerin kaydı
  devir.py        oy devri          uzmanlik.py   ön şart, kontenjan, başvuru
  graf.py         üye ağı: takip, PageRank, Gini, görüş grupları
  defter.py       dağıtık kayıt defteri: hash zinciri, 3 düğüm, uzlaşma, onarım, tutarlılık
  yz.py           yapay zeka üyenin özetleri
  yonetim.py      yönetim paneli: pano sayıları, yetki, askı, kategoriler, site ayarları, toplu bildirim, yedek
  sikayetler.py   şikayet kutusu        anlik.py  anlık bildirim (Web Push ve Firebase)
  kategoriler.py  kategori önerisi ve kategoriler sayfası      gundem.py  trendler, öne çıkan kelimeler, kategori nabzı
  kullanicilar.py, guvenlik.py, bildirimler.py, arama.py, gorevler.py, veritabani.py
  web/            HTTP katmanı (Flask blueprint'leri + REST API; yonetim_sayfalari.py = /yonetim)
  templates/      sayfalar; panel/ = Panelim, yonetim/ = yönetim paneli     static/  CSS, JS, ağ çizimi, PWA dosyaları
mobil-expo/       Expo Go uygulaması (Expo SDK 57, WebView)
mobil/            Android uygulaması (Capacitor): capacitor.config.json, android/ projesi, BENIOKU.md
testler/          94 test
docs/tasarim.md   UML diyagramları (kullanım durumu, durum, sıralı, varlık-ilişki, katmanlar)
```

**Güvenlik:**
- Şifreler hash'lenir; şifre politikası uygulanır; 5 hatalı girişte 10 dakika kilit.
- Şifre kurtarma kodu da sadece hash olarak saklanır.
- Her formda CSRF koruması var.
- İçerik güvenlik politikası (CSP) ve diğer güvenlik başlıkları gönderilir.
- SQL sorguları parametrelidir; şablonlar otomatik kaçış kullanır.
- API'de kişisel veri döndürülmez.
