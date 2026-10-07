# Agora: uygulamanın bütün ayrıntıları

Bu belge Agora'nın nasıl çalıştığını baştan sona, sade bir dille anlatır. Sırayla okunacak şekilde yazıldı:
önce fikir, sonra kişiler, sonra bir konunun yolculuğu, sonra oylamanın içi, en sonda mimari ve teknik yapı.

Parantez içindeki sayılar **varsayılan** değerlerdir. Çoğu sayı yönetmelikte durur ve üyelerin oylamasıyla değişebilir
(bu yüzden sitede gördüğün değer farklı olabilir; güncel hâli her zaman **Meclis › Yönetmelik** sayfasındadır).

---

## 1. Tek cümlede Agora

Agora, herkesin konu açtığı, herkesin bir fikir yazdığı ve fikirlerin tur tur oylanarak tek bir karara indiği bir tartışma forumudur.

Dört ana fikir her şeyin temelidir:

1. **Kimse tek başına karar vermez.** Karar, mesaj gizleme, konu kaldırma, uzmanlık, kural değişikliği: hepsi oylamayla olur. Yönetici de karar veremez.
2. **Hiçbir şey silinmez.** Mesajlar düzenlenebilir ama eski hâli görünür; gizlenebilir ama yerinde iz kalır; her olay kayıt defterine yazılır.
3. **Herkes fikir verebilir.** Her katılımcı her konuda bir fikir yazar; bütün fikirler aynı oylamada yarışır.
4. **Sonuca itiraz edilebilir.** Karara katılmayan, yeni bir itiraz konusu açıp meseleyi yeniden tartışmaya açar.

---

## 2. Kimler var?

| Kim | Ne yapabilir |
|---|---|
| **Ziyaretçi** (giriş yapmamış) | Her şeyi okur. Yazamaz, oy veremez. |
| **Üye** | Konu açar, mesaj yazar, fikir verir, oy verir, oyunu devreder, şikayet eder. |
| **Katılımcı / gözlemci** | Aynı üye, bir konuda *katılımcı*, başka bir konuda *gözlemci* olabilir. Konunun katılım kuralını (il/ilçe, yaş) sağlıyorsa katılımcıdır; sağlamıyorsa o konuyu yalnızca okur. |
| **Uzman** | Belli bir alanda (ör. Sağlık) uzmanlığı oylamayla kabul edilmiş üye. O alandaki fikir oylamalarında oyu 10 sayılır. |
| **Yapay zeka üye** | Sistemin açtığı özel hesap (ör. `Bilge`). Yalnızca kısa özet yazar. Oy kullanmaz, giriş yapamaz. |
| **Yönetici** | Yalnızca siteyi yönetir (askı, şikayet kutusu, kategoriler, duyurular). Kararları etkileyemez; oyu herkes gibi 1'dir. |
| **Askıdaki üye** | Yöneticinin belli bir süre için askıya aldığı üye. Okur ama yazamaz, oy veremez. |

---

## 3. Kayıt ve giriş

**Kayıtta istenenler:** ad soyad, takma ad, doğum tarihi, il/ilçe, şifre.

- Forumda **yalnızca takma ad** görünür. Ad soyad, doğum tarihi ve adres gizlidir; sadece katılım kuralını kontrol etmek için kullanılır (bir de yöneticiler görebilir).
- En az **13 yaş** gerekir.
- Takma ad 3–30 karakter; harf, rakam, nokta, alt çizgi. Kaba ifade içeremez.
- Şifre en az **8 karakter**, en az bir harf ve bir rakam.

**Kurtarma kodu:** Kayıt olunca bir kez `AGORA-XXXX-XXXX-XXXX-XXXX` biçiminde bir kod gösterilir. E-posta yoktur;
şifre unutulursa bu kodla yeni şifre alınır. Kod kullanılınca yenisi verilir, eskisi geçersiz olur. Panelim › Güvenlik'ten de yenilenebilir.

**Giriş kilidi:** 5 hatalı denemeden sonra 10 dakika beklenir.

**Adres değişikliği:** Yeni adres hemen değil **30 gün** sonra geçerli olur. Neden: kimse sırf bir oylamaya katılmak için adresini değiştiremesin.

---

## 4. Bir konunun yolculuğu

```
KONU AÇILIR → TARTIŞMA (24 saat) → 1. TUR (48 saat) → 2. TUR (24 s) → 3. TUR (24 s) → 4. TUR (24 s) → 5. TUR (24 s) → KARAR
                                    %5 altı elenir     %5 altı        %10 altı        %20 altı        en çok oy alan

Her turda:  bir fikir %75 ya da fazlasını aldıysa  → hemen KARAR
            elemeden sonra tek fikir kaldıysa       → hemen KARAR
            yeter sayı yoksa / hiçbir fikir kalmadıysa → SONUÇSUZ
```

### 4.1 Konu açılır
Her üye konu açabilir. Derdi ne olursa olsun: bir fikir, bir öneri, bir şikayet. Formda: başlık (5–150 karakter),
açıklama (10–5000), kategori, katılım kuralı (isteğe bağlı il/ilçe ve yaş aralığı).

Konu **hemen açılır**; kabul oylaması ya da ön inceleme yoktur. Gönderirken yalnızca **yönetmelik denetimi** çalışır
(ayrıntı 12. bölümde): hakaret ya da kişisel veri varsa konu açılamaz, diğer sorunlar yalnızca uyarıdır.

Konuyu açan kişi, tartışma sürerken başlığı ve açıklamayı **düzenleyebilir**; eski hâli "düzenlendi, eski hâlini gör" bağlantısında herkese görünür.

### 4.2 Tartışma (24 saat)
Katılımcılar dört türde mesaj yazar: **Argüman, Karşı argüman, Soru, Kaynak.** Mesajlar birbirine yanıt olarak yazılabilir.

**Fikir** ayrı bir şeydir: "bu konuda ne yapılmalı?" sorusunun cevabıdır ve oylamada yarışacak olan odur.
- Her katılımcı bir konuda **en fazla bir fikir** yazabilir. Yazmak zorunda değildir.
- Fikir 10–600 karakterdir. Yazarı, oylama başlayana kadar fikrini düzenleyebilir.
- Fikirlerin altında da tartışılır (argüman, karşı argüman).

Bu aşamada ayrıca **alt konu** açılabilir (üst konunun katılım kuralını yalnızca daraltabilir: İstanbul konusunun alt konusu
Kadıköy olabilir, Ankara olamaz) ve **konu kaldırma** oylaması istenebilir (3/4 ister).

### 4.3 Birinci tur (48 saat)
24 saat dolunca oylama **kendiliğinden** açılır. Yapay zeka üye o ana kadarki tartışmayı kısaca özetler.
- Herkes **tek bir fikre** oy verir ya da **çekimser** kalır.
- Bu tur boyunca **hâlâ yeni fikir yazılabilir** (kişi başı bir tane sınırı sürer); yeni fikir oylamaya da eklenir.
- **Tartışma devam eder**; oy, tur bitene kadar değiştirilebilir.
- Tur bitince oranı **%5'in altında** kalan fikirler **elenir**.

### 4.4 İkinci–beşinci turlar (her biri 24 saat)
Kalan fikirler yeniden oylanır. Artık yeni fikir yazılamaz ama tartışma sürer.

| Tur | Süre | Bu oranın altındaki fikir elenir |
|---|---|---|
| 1 | 48 saat | %5 |
| 2 | 24 saat | %5 |
| 3 | 24 saat | %10 |
| 4 | 24 saat | %20 |
| 5 | 24 saat | eleme yok: **en çok oy alan fikir kabul edilir** |

### 4.5 Kısa yollar ve sonuçsuz kapanma
- **Ezici üstünlük:** Hangi turda olursa olsun bir fikir **%75 ya da daha fazla** aldıysa hemen kabul edilir, konu kapanır.
- **Tek kalan:** Bir turun sonunda elenmeyen tek fikir kaldıysa o kabul edilir. Örnek: ilk turda sekiz fikir var; yedisi %5'in altında,
  sekizincisi %65. Ezici üstünlük yok ama geriye tek fikir kaldığı için sekizinci kabul edilir.
- **Sonuçsuz:** Şu üç durumda konu karar çıkmadan kapanır: yeter sayıya ulaşılamadı; hiçbir fikir eşiği geçemedi (ya da hiç fikir yok);
  son turda ilk iki fikir tam eşit.

### 4.6 Karar ve itiraz
Kabul edilen fikir **karardır** ve hemen kesindir; konu kapanır (artık mesaj yazılamaz). Kararlar **Oylamalar › Kararlar** arşivinde durur.

Karara katılmayan (ya da sonuçsuz kapanan konuyu yeniden denemek isteyen) herkes **"İtiraz konusu aç"** düğmesiyle yeni bir konu açar.
İtiraz konusu eski konuya bağlı görünür ve **aynı yoldan** geçer: tartışma, turlar, karar. Azınlığın sesi böyle korunur.

### Durumların listesi
| Durum | Anlamı |
|---|---|
| Tartışmada | İlk 24 saat; mesaj ve fikir yazılır |
| Oylamada | Turlar sürüyor (konu kartında kaçıncı tur olduğu yazar); mesaj yazılır |
| Karara bağlandı | Bir fikir kabul edildi |
| Sonuçsuz kapandı | Karar çıkmadı |

Konu sayfasındaki **yedi adımlı çizgi** (Tartışma, 1.–5. tur, Karar) ve konu kartlarındaki yedi nokta, konunun nerede olduğunu gösterir.

### Süreler kendiliğinden işler
Kimse siteye girmese bile arka planda her 30 saniyede bir kontrol yapılır: tartışma süresi dolan konuda oylama açılır, süresi dolan tur
sonuçlanır. Fikir turları **süresini doldurur** (herkes oy verse bile erken bitmez, çünkü tartışma sürer ve oy değişebilir).
Evet/Hayır oylamaları ise oy hakkı olan herkes oy verince erken biter.

---

## 5. Katılım kuralı: kim katılımcı, kim gözlemci?

Konu açılırken iki kural konabilir:
- **Konum:** "İstanbul sakinleri" ya da "Kadıköy sakinleri" gibi.
- **Yaş:** "18+", "13–25" gibi.

Kuralı sağlayan **katılımcıdır** (yazar, oy verir). Sağlamayan **gözlemcidir** (okur). Kural koyulmazsa konu herkese açıktır.

**Uygunluk puanı:** Konum, bir ağaç üzerinde ölçülür (Türkiye › Bölge › İl › İlçe). Konu Kadıköy'e açıksa:
Kadıköy'de oturan %100, Beşiktaş'ta oturan (aynı il) %67, Bursa'da oturan (aynı bölge) %33, Ankara'da oturan %0 uyumludur.
Katılımcı olmak için %100 gerekir; puan, kişinin kurala ne kadar yakın olduğunu göstermek içindir.

Yapay zeka hesapları hiçbir konuda katılımcı değildir; yalnızca özet yazar.

---

## 6. Mesajlar

- **Silinemez.** Ne yazarı ne yönetici bir mesajı silebilir.
- **Düzenlenebilir, ama neyden düzenlendiği görünür.** Yazarı mesajını düzenleyebilir; eski hâli saklanır ve mesajın yanındaki
  "düzenlendi" bağlantısından herkes görür. (Fikirler yalnızca oylama başlamadan önce düzenlenebilir; oylanan metin değişemez.)
- **Gizleme:** Bir mesaj ancak **oylamayla** ve **dörtte üç (%75)** ile gizlenir.
  Birden fazla mesaj seçilip **tek oylamayla** gizletilebilir (en fazla 20 mesaj).
  Gizlenen mesajın yerinde "Bu mesaj ... tarihinde oylamayla gizlendi" notu kalır; metin veritabanında durur.
- **Şikayet:** Üye bir mesajı ya da konuyu şikayet edebilir; yeterli sayıda üye şikayet ederse yöneticilere ulaşır (18. bölüm).
- **Sistem mesajları** (gri, "Sistem" yazanlar) süreçteki olayları duyurur: "Fikir oylaması başladı", "2. tur bitti", "Karar: ..." gibi.
- **Özet mesajları** yapay zeka üyenin yazdığı kısa özetlerdir (11. bölüm).

---

## 7. Oylama nasıl sayılır?

### 7.1 Oylama türleri
| Oylama | Seçenekler | Kural | Süre |
|---|---|---|---|
| Fikir oylaması (turlar) | Fikirlerden biri ya da Çekimser | Eleme kuralları (4. bölüm) | 1. tur 48 saat, sonrakiler 24 saat |
| Mesaj gizleme | Evet / Hayır / Çekimser | 3/4 | 48 saat |
| Konu kaldırma | Evet / Hayır / Çekimser | 3/4 | 48 saat |
| Uzmanlık başvurusu | Evet / Hayır / Çekimser | 2/3 | 48 saat |
| Yönetmelik değişikliği | Evet / Hayır / Çekimser | 2/3 (temel hak maddeleri için 3/4) | 96 saat |
| Yeni kategori | Evet / Hayır / Çekimser | Salt çoğunluk (herkes 1 oy) | 48 saat |

Eşikler "en az" demektir: 3/4 = %75 ve üstü.

### 7.2 Oy ağırlığı
- Normal üye: **1**
- Konunun alanındaki uzman: **10**
- Yönetici: **1** (yöneticilik oy ağırlığı vermez)
- Yapay zeka: **oy kullanmaz**
- Uzmanlık ve yönetmelik oylamalarında herkes **1** (uzman da).

Uzman oy verirken **gerekçe yazmak zorundadır** ve oyu sonuçta **herkese açıktır**.

### 7.3 Çift çoğunluk: oran nasıl hesaplanır?
Her fikrin iki ayrı payı hesaplanır:
1. **Ağırlıklı pay:** fikrin aldığı ağırlıklı oy ÷ bütün ağırlıklı oylar (uzman oyu 10 sayılarak)
2. **Kişi payı:** fikre oy veren kişi sayısı ÷ oy veren bütün kişiler (herkes 1)

Fikrin **oranı, bu ikisinden küçük olanıdır.** Eleme eşikleri (%5, %10, %20), ezici üstünlük (%75) ve son turdaki sıralama hep bu orana bakar.

Örnek: 1 uzman A fikrine (10), 3 üye B fikrine (3) oy verdi.
- A: ağırlıklı 10/13 = %77, kişi 1/4 = %25 → **oran %25**
- B: ağırlıklı 3/13 = %23, kişi 3/4 = %75 → **oran %23**

Böylece ne birkaç uzman kalabalığı ezebilir, ne de kalabalık uzmanları tamamen yok sayabilir: bir fikrin güçlü sayılması için
**hem** uzmanlığın ağırlığında **hem** kişi sayısında karşılık bulması gerekir.

Evet/Hayır oylamalarında aynı fikir geçerlidir: Evet'in eşiği **iki payda da** sağlaması gerekir.

### 7.4 Yeter sayı
Oylamanın geçerli olması için oy hakkı olanların en az **%20**'si ve en az **2 kişi** oy vermeli.
Fikir oylamasında yeter sayı sağlanmazsa konu **sonuçsuz** kapanır; Evet/Hayır oylamasında sonuç "Yeter sayıya ulaşılamadı" olur (kabul sayılmaz).

### 7.5 Çekimser
Çekimser oy nötrdür ama **etkisizdir demek değildir**: toplamda sayılır.
- Yeter sayıya katkı yapar.
- Paydaya girer; yani bütün fikirlerin (ya da Evet'in) oranını düşürür. 3 kişi A'ya, 2 kişi çekimser oy verdiyse A'nın oranı %100 değil **%60**'tır.
- Sonuç: çoğunluğun sağlanıp sağlanmadığını çekimserler de etkiler. "Hiçbir fikri beğenmiyorum" demenin yolu budur.

### 7.6 Gizli oy ve makbuz
- Normal oylar gizlidir. Oylama bitene kadar ara sonuç gösterilmez.
- Oy verince sana bir **makbuz kodu** verilir (`XXXX-XXXX-XXXX-XXXX`).
- Kayıt defterine oyun kendisi değil, bir **özeti** yazılır: `SHA-256(oylama no | seçim | makbuz)`.
- Makbuzla **Meclis › Kayıt defteri › Oyumu doğrula** kısmından oyunun deftere yazıldığını ve ne oy verdiğini görebilirsin.
  Makbuz sadece sende olduğu için bunu başkası yapamaz.
- Oylama bitene kadar oyunu değiştirebilirsin; her değişiklikte yeni makbuz alırsın.

---

## 8. Azınlık nasıl korunur?

Temel koruma basittir: **herkes fikir verebilir** ve **sonuca katılmayan yeni bir tartışma açabilir.**

| Koruma | Nasıl çalışır |
|---|---|
| Fikir hakkı | Her katılımcı her konuda bir fikir yazar; küçük bir grubun fikri de aynı oylamada yarışır |
| İtiraz konusu | Karara katılmayan, "önceki konunun sonucuna katılmıyoruz" diyerek yeni bir konu açar; o da aynı yoldan geçer |
| Çift çoğunluk | Oran, ağırlıklı pay ile kişi payının küçüğüdür (7.3) |
| Çekimser | Çekimser oylar paydada sayılır; kimse sessiz kalanları yok sayarak çoğunluk olamaz (7.5) |
| Yüksek eşikler | Mesaj gizlemek ve konu kaldırmak 3/4 ister |
| Korunan maddeler | Temel haklar ve bazı parametreler ancak 3/4 ile değişir |
| Güç sınırı | Kimse 5'ten fazla devredilmiş oy taşıyamaz; bir alanda en fazla 3 uzman olur; yönetici kararlara karışamaz |
| Gizli oy | Kimse kimin ne oy verdiğini göremez (uzman oyları hariç) |

---

## 9. Oy devri

Oy hakkını güvendiğin birine bırakabilirsin (Panelim › Oy devri).

- **Kapsam:** tüm forum, bir kategori ya da tek bir konu.
- **Öncelik:** birden fazla devrin varsa en dar olan geçerlidir: önce konu, sonra kategori, sonra tüm forum.
- **Zincir olabilir:** A → B → C ise, C oy verince üçünün oyu sayılır.
- **Döngü olamaz:** A → B → A kurulmaz.
- **Kendin oy verirsen** o oylamada devir geçersiz olur, senin oyun sayılır.
- Devralan kişinin o oylamada oy hakkı yoksa devir o oylamada işlemez.
- Yalnızca **kendi oyun (1)** devredilir; uzmanlık ağırlığı devredilmez.
- Bir kişi en fazla **5** devredilmiş oy taşıyabilir; fazlası düşer.
- Yapay zekaya oy devredilemez (oy kullanmadığı için); yapay zeka hesapları da oy devredemez.

---

## 10. Uzmanlık

Uzman, bir **alanda** oyu ağır sayılan üyedir (ör. Sağlık › Beslenme). Alt alanlar da kapsanır: "Sağlık" uzmanı "Beslenme" konularında da uzmandır.

Uzman olmanın **üç adımı** vardır; üçü de sağlanmalıdır:

1. **Ön şart.** Aday o alanda yeterince katkı yapmış olmalı: en az **5 mesaj** ve en az **2 farklı konu**. Sağlamıyorsa başvuru açılamaz.
2. **Kontenjan.** Bir ana kategoride (ör. Sağlık'ın tamamı) aynı anda en fazla **3 uzman** olabilir. Yer yoksa başvuru açılamaz;
   bir uzmanlığın süresi dolunca yer açılır. Bu sınır, küçük bir grubun (klik) sırayla birbirini uzman yapmasını engeller.
3. **Alanın oylaması.** Başvuruyu herkes değil, o alanın **niş kitlesi** oylar: o ana kategorideki konulara en az bir mesaj yazmış üyeler.
   Herkesin oyu **1** sayılır (mevcut uzmanların da), **aday oy kullanamaz**, kabul için **2/3** gerekir ve en az 2 kişi oy vermelidir.

Diğer kurallar:
- Uzmanlık **180 gün** sürer, sonra kendiliğinden biter. Yeniden uzman olmak için yeniden başvurmak gerekir.
- **Yönetici uzman atayamaz**, uzmanlığı geri de alamaz.
- **Yapay zeka hesapları da uzman olabilir**, ama aynı şartlarla: aynı ön şartı sağlamalı, kontenjanda yer olmalı ve alanın üyeleri oylamalı.
  Yapay zeka kendi başvuramaz; bir üye onu **aday gösterir** (yapay zekanın profil sayfasından).
- Uzman ne kazanır: kendi alanındaki **fikir oylamalarında** oyu 10 sayılır. Karşılığında gerekçe yazmak zorundadır ve oyu herkese açıktır.
- Başvuru: **Panelim › Uzmanlık**. Sayfa, seçilen alan için ön şartların ve kontenjanın durumunu gösterir.

---

## 11. Yapay zeka üye

Forumda en fazla **3** yapay zeka hesabı olabilir (demoda `Bilge`). Hesabı yönetici açar.

Yapay zeka üyenin tek işi **kısaca özetlemektir**:

| Ne zaman | Ne yazar |
|---|---|
| Oylama başlarken | Tartışma özeti: kaç kişi kaç mesaj yazdı, hangi fikirler var, her fikre kaç argüman ve karşı argüman geldi |
| Her tur bitince | Tur özeti: kaç kişi oy verdi, her fikir yüzde kaç aldı, hangisi kaldı, hangisi elendi |
| Bir katılımcı isteyince | Konu sayfasındaki "Tartışmanın özetini iste" düğmesiyle güncel tartışma özeti |

Özetler sayılara dayanır, yorum katmaz; internet ya da dış servis gerekmez. Oranlar yuvarlanmaz, **kesilir**: %74,9 hiçbir zaman
"%75" yazılmaz, yoksa okuyan ezici üstünlük sağlandı sanır. Her fikrin "kaldı / elendi / kabul edildi" durumu, turun kaydedilmiş
kararından okunur.

**Neden büyük dil modeli (ChatGPT benzeri) kullanılmıyor?** Özet oy vermeden önce okunur; modelin uydurduğu tek bir sayı kararı
etkiler (halüsinasyon). Ayrıca mesajlar dış servise gönderilirse kişisel veri dışarı çıkar, her özet ücretli ve yavaş olur.
Gerekçe ve ileride insan onaylı bir modelin nasıl ekleneceği [analiz.md](analiz.md) 3. bölümde.

**Yapamadıkları:** oy kullanamaz, fikir yazamaz, konu açamaz, giriş yapamaz, oy devredemez, kendisine oy devredilemez, şikayet gönderemez,
yönetici olamaz. (Uzmanlık için aday gösterilebilir; 10. bölüm. Bu kısım şimdilik göstermeliktir.)

---

## 12. Yönetmelik

Forumun kurallarıdır. **Meclis › Yönetmelik** sayfasında görülür. İki parçası var: **maddeler** ve **parametreler**.

### 12.1 Madde türleri
- **Temel hak (T):** Korunur; değişmesi 3/4 ister.
- **Usul (U):** Sürecin nasıl işlediği.
- **Denetim (D):** Konuları ve mesajları **otomatik** denetleyen kurallar. Her birinin ciddiyeti vardır: **Engeller**, **Uyarır** ya da **Kapalı**.
- **Beyan (B):** Topluluk normu; oylamayla yenisi eklenebilir.

### 12.2 Maddeler
**Temel haklar**
- **T1 Kurallar karşısında eşitlik:** Kurallar herkese aynı uygulanır; yöneticiler kararlara karışamaz.
- **T2 Söz hakkı:** Mesajlar silinmez; düzenlenenin eski hâli görünür; ancak 3/4 ile gizlenir, yerinde not kalır.
- **T3 Fikir verme ve itiraz hakkı:** Her katılımcı bir fikir yazabilir; karara katılmayan itiraz konusu açabilir.
- **T4 Gizli oy:** Normal oylar gizli, uzman oyları açık ve gerekçeli.
- **T5 Güç sınırı:** En fazla 5 devredilmiş oy; bir ana kategoride en fazla 3 uzman.

**Usul**
- **U1 Konu ve tartışma**, **U2 Fikirler**, **U3 Eleme turları**, **U4 Oy ağırlığı ve oran**, **U5 Yeter sayı**,
  **U6 Konu düzenleme ve kaldırma**, **U7 Uzmanlık**, **U8 Yönetmelik değişikliği**, **U9 Adres değişikliği**, **U10 Şikayet**, **U11 Kategoriler**
  (bunların içeriği yukarıdaki bölümlerde anlatıldı).

**Denetim** (konu açılırken ve mesaj yazılırken çalışır)
| Madde | Ne kontrol eder | Varsayılan |
|---|---|---|
| D1 Saygılı dil | Hakaret listesindeki kelimeler | Engeller |
| D2 Kişisel veri | Telefon numarası, T.C. kimlik no, e-posta | Engeller |
| D3 Kategoriye uygunluk | Metin seçilen kategorinin kavramlarını içeriyor mu? İçermiyorsa daha uygun kategori önerir | Uyarır |
| D4 Konum tutarlılığı | Metinde "Ankara" geçiyor ama katılım herkese açıksa uyarır | Uyarır |
| D5 Benzer konu | Aynı konuda açık bir konu var mı? (kelime benzerliği) | Uyarır |
| D6 Alt konu ilişkisi | Alt konu, üst konuyla aynı alanda mı? | Uyarır |
| D7 Açıklık | Açıklama en az 40 karakter mi? | Uyarır |

Denetim bir **puan** (%) üretir. Engel varsa konu açılamaz; uyarılar engellemez ama konu sayfasında görünür.
"Yönetmelik denetimini önizle" düğmesiyle göndermeden önce sonuç görülebilir.

**Beyan**
- **B1 Tartışma kültürü:** Kişilere değil fikirlere karşı çıkılır.

### 12.3 Parametreler (varsayılanlar)
| Parametre | Değer |
|---|---|
| Tartışma süresi | 24 saat |
| 1. tur / sonraki turlar | 48 saat / 24 saat |
| Eleme eşikleri (1., 2., 3., 4. tur) | %5, %5, %10, %20 |
| Ezici üstünlük | %75 (korunan) |
| Yeter sayı | %20, en az 2 kişi |
| Mesaj gizleme | 3/4 (korunan) |
| Konu kaldırma | 3/4 |
| Uzmanlık başvurusu | 2/3 |
| Yönetmelik değişikliği | 2/3 (korunan) |
| Temel hak değişikliği | 3/4 (korunan) |
| Uzman oy ağırlığı | 10 |
| Uzman kontenjanı (ana kategori başına) | 3 (korunan) |
| Uzmanlık ön şartı | alanda 5 mesaj, 2 konu |
| Uzmanlık süresi | 180 gün |
| En fazla devredilmiş oy | 5 (korunan) |
| Şikayet tabanı | 3 farklı üye |
| Yeni kategori | Salt çoğunluk |
| Gizleme, kaldırma, uzmanlık oylamalarının süresi | 48 saat |
| Yönetmelik oylamasının süresi | 96 saat |
| Adres bekleme | 30 gün |

### 12.4 Yönetmelik nasıl değişir?
Yönetmelik sayfasının altından üç tür değişiklik önerilir:
1. **Parametre değiştir** (ör. yeter sayıyı %30 yap)
2. **Denetim maddesinin ciddiyetini değiştir** (ör. D5'i Kapalı yap)
3. **Yeni beyan maddesi ekle**

Oylamada herkesin oyu 1'dir (uzmanın da). Kabul için 2/3; korunan parametreler ve temel haklar için 3/4.

---

## 13. Ontoloji (kavram ağaçları)

"Ontoloji" burada kavramların ağaç biçiminde düzenlenmesi demek. İki ağaç var:

**Konum ağacı:** Türkiye › 7 bölge › 81 il › 94 ilçe. Katılım kuralı ve uygunluk puanı bu ağaçla hesaplanır.

**Kategori ağacı:** 7 temel alan + **Genel**, her temel alanın 3–4 alt kategorisi:
| Ana kategori | Alt kategoriler |
|---|---|
| Bilim | Fizik, Biyoloji, Çevre ve İklim |
| Sağlık | Beslenme, Spor, Ruh Sağlığı |
| Siyaset | Yerel Yönetim, Ulaşım, Kamu Politikası |
| Eğitim | Üniversite, Lise, Akran Öğrenmesi, Kampüs Yaşamı |
| Teknoloji | Yazılım, Yapay Zeka, Donanım |
| Ekonomi | Kişisel Finans, İş ve Kariyer, Girişimcilik |
| Kültür ve Sanat | Edebiyat, Müzik, Sinema |
| Genel | (alt kategorisi yok) her konuya açık |

Her kategorinin **kavram listesi** vardır (ör. Beslenme: yemek, menü, diyet, protein, etsiz, vegan...). D3 denetimi metindeki
kelimeleri bu listelerle karşılaştırır. **Genel** kategoride D3 aranmaz; her konu açılabilir.
Türkçe karakterler "katlanır" (ö → o, ş → s), böylece "ogrenci" araması "öğrenci"yi bulur.

### 13.1 Kategoriler üyelerle büyür
Forum zamanla genişler: **her üye yeni bir kategori önerebilir** (Konular › Kategoriler sayfasının altındaki form).
1. Ad, yeri (yeni ana kategori ya da bir ana kategorinin altına alt kategori), isteğe bağlı **kavramlar** ve gerekçe yazılır.
2. Öneri **bütün üyelerin** oyuna sunulur: 48 saat, herkesin oyu 1, kabul için **salt çoğunluk** (yeter sayı da gerekir).
3. Kabul edilirse kategori hemen eklenir, **Topluluk** rozetiyle görünür; önerirken yazılan kavramlar D3 denetiminde kullanılır.

Kurallar: aynı adda kategori olamaz; alt kategori yalnızca bir ana kategorinin altına açılır (Genel'in altına açılmaz);
aynı öneri iki kez oylamaya çıkmaz; bir üyenin aynı anda tek bekleyen önerisi olabilir; yapay zeka öneremez.
Önerilerden önce **Genel** kategoride tartışılması beklenir ("Spor ve Oyun gelsin mi?" gibi).

Yöneticiler de kategori ekleyebilir ve ad/renk değiştirebilir; kategori **silinmez**, çünkü konular ona bağlıdır.

### 13.2 Kategoriler sayfası
**Konular › Kategoriler** (`/kategoriler`): bütün kategoriler kart olarak; her kartta konu sayısı, açık konu, bu haftaki mesaj,
uzman sayısı, son etkinlik ve alt kategoriler.
- **Arama:** kategori adında ya da kavramlarında arar ("iklim" → Bilim › Çevre ve İklim).
- **Süzgeç:** Tümü, Ana kategoriler, Alt kategoriler, Topluluğun ekledikleri, Konusu olanlar.
- **Sıralama:** En çok konu, Son etkinlik, Ada göre, En yeni.
- Üstte **oylamadaki öneriler** (oy verme bağlantısıyla), altta öneri formu ve sonuçlanan öneriler.

Eski kurulumlardan gelen "Şehir" ve "Kampüs Yaşamı" ana kategorileri ilk açılışta yenilerine taşınır
(Şehir › Ulaşım → Siyaset › Ulaşım, Kampüs Yaşamı → Eğitim › Kampüs Yaşamı); konular, uzmanlıklar ve devirler kaybolmaz.

---

## 14. Kayıt defteri (dağıtık defter)

Forumdaki her önemli olay bir **zincire blok** olarak eklenir: konu, konu düzenleme, durum değişikliği (tur geçişleri), mesaj,
mesaj düzenleme, gizleme, oylama açılışı, oy, sonuç, karar, devir, yeni üye, uzmanlık, yönetim işlemi.

**Nasıl kurcalanamaz hâle gelir:**
- Her blok, bir önceki bloğun **SHA-256 özetini** taşır. Eski bir blok değiştirilirse ondan sonraki bütün bağlar kopar.
- Zincirin **üç kopyası** üç ayrı "düğümde" (A, B, C dosyaları) tutulur.
- **Çoğunluk kuralı:** 3 düğümden en az 2'si aynı zincirdeyse o zincir geçerlidir.
- Bozulan düğüm hemen görünür; **onarım** sağlam çoğunluktan kopyalanarak yapılır. Bozuk düğüme yeni blok yazılmaz.
- **Tutarlılık denetimi:** Veritabanındaki mesajlar, oylar ve sonuçlar defterle karşılaştırılır; biri gizlice silinmiş ya da değiştirilmişse yakalanır.
- Yalnızca başarıyla kaydedilen işlemler deftere yazılır; yarıda kalan işlem yazılmaz.

**Kişisel veri deftere yazılmaz:** mesajların yalnızca özeti, oyların yalnızca taahhüdü (makbuzlu özet) yazılır.

Sunumda göstermek için: Yönetim paneli › Sistem › "Bozmayı dene" → kayıt defteri sayfasında düğüm bozuk görünür → "Onar".
("Bozmayı dene" yalnızca `--demo` sunum kipinde açıktır; gerçek defter geri dönüşsüz bozulmasın.)

**Hız:** Bir düğümün zinciri bir kez baştan doğrulandıktan sonra sonuç, düğümün **sürümüyle** birlikte saklanır. Düğüm
değişmedikçe zincir yeniden hesaplanmaz; yeni blok eklerken yalnızca son blok okunur. Düğüm dosyasını dışarıdan biri değiştirirse
sürüm değişir ve bir sonraki okumada tam doğrulama yapılır, kurcalama yine yakalanır. Ölçüm: 50.000 blokluk defterde oy vermek
bu değişiklikten önce ~645 ms, sonra ~11 ms sürüyor ([analiz.md](analiz.md) 8.2).

---

## 15. Üye ağı (graf)

Üyeler bir **ağın düğümleridir**. Aralarındaki bağlar (kenarlar):
| Bağ | Anlamı |
|---|---|
| Devir | A oyunu B'ye devretti |
| Yanıt | A, B'ye yanıt yazdı |
| Takip | A, B'yi takip ediyor |
| Oy benzerliği (yalnızca sunucuda) | A ile B çekişmeli oylamalarda %60+ aynı yönde oy verdi (en az 2 ortak oylama). **Hiçbir yerde gösterilmez:** iki kişinin aynı oyu verdiğini göstermek gizli oyu bozardı |

**Ağ üzerinde hesaplananlar:**
- **Etki puanı (PageRank):** Kimin mesajları ve görüşü ağda daha çok karşılık buluyor (0–100).
- **Görüş grupları:** Oy benzerliği bağları üzerinde "etiket yayılımı" ile benzer oy verenler gruplanır (Grup A, Grup B...).
  Yalnızca **en az 3 kişilik** gruplar gösterilir (k-anonimlik): iki kişilik bir grup, o iki kişinin aynı oyu verdiğini ele verirdi.
- **Oy gücü ve Gini katsayısı:** Devirlerden sonra kimin kaç oy taşıdığı ve gücün ne kadar yoğunlaştığı (0 = eşit, 1 = tek kişide).

Ağ **yalnızca bilgi içindir**; oylamaların sonucunu etkilemez.
**Meclis › Üye ağı** sayfasında ağ çizilir (◆ uzman, ■ yapay zeka); noktalar sürüklenebilir, tıklanınca profile gidilir.

---

## 16. Şeffaflık günlüğü

Kayıt defterinin okunabilir hâlidir: "@ayse foruma katıldı", "#12 oylama sonuçlandı", "@can 3 gün askıya alındı: ..." gibi.
Herkese açıktır, yalnızca takma adlar görünür. Yönetimin yaptığı her işlem de buraya düşer.

---

## 17. Bildirimler

**Site içi bildirim** (zil simgesi): oylama açıldı, tur bitti, karar çıktı, mesajına yanıt geldi, konuna fikir yazıldı, uzman oldun,
şikayetin sonuçlandı, yönetici duyurusu gibi.

**Anlık bildirim** (telefona, site kapalıyken de): Panelim › Bildirimler › "Bu cihazda aç". Her cihaz için ayrı açılır.
- Tarayıcıda: sunucuda `pywebpush` kurulu olmalı ve site **HTTPS** (ya da bilgisayarın kendisinde `127.0.0.1`) üzerinden açılmalı.
- Android uygulamasında (Capacitor): Firebase ayarı gerekir (`mobil/BENIOKU.md`).
- Expo Go'da anlık bildirim yoktur (Expo Go desteklemiyor).
- Bildirim yalnızca işlem başarıyla kaydedilince gönderilir; geçersizleşen cihaz kayıtları kendiliğinden silinir.

**Toplu bildirim:** Yönetici; bütün üyelere, bir il/ilçedeki üyelere, bir alanın uzmanlarına ya da yöneticilere bildirim gönderir.

---

## 18. Şikayet kutusu

1. Üye bir mesajın altındaki **"Şikayet et"** ya da konu sayfasındaki **"Konuyu şikayet et"** ile neden seçer (Hakaret, Spam, Konu dışı, Kişisel veri, Yanlış bilgi, Diğer) ve isterse açıklama yazar.
2. **Alt taban:** Şikayet hemen yöneticilere gitmez. Aynı içeriği en az **3 farklı üye** şikayet edince yöneticilere ulaşır ve bildirim düşer.
   Tek kişinin şikayeti yöneticileri meşgul etmez; tabanın altındaki şikayetler yönetim panelinde görünmez. Şikayet edene "yöneticilere ulaşması için
   kaç şikayet daha gerektiği" söylenir.
3. Taban dolunca yönetici iki şeyden birini yapar:
   - **Oylamaya al:** Mesaj için gizleme, konu için kaldırma oylaması açılır. **Kararı yine üyeler verir** (3/4).
   - **Yersiz bul:** Kısa bir notla kapatır.
4. Şikayet edenlere sonuç bildirilir; Panelim › Özet'te şikayetlerinin durumu görünür.

Kurallar: kendi içeriğini şikayet edemezsin, aynı içerik için iki bekleyen şikayetin olamaz, günde en fazla 10 şikayet.
Aynı içerik hakkındaki bütün şikayetler tek kartta toplanır ve birlikte sonuçlanır.

Şikayet beklemeden de yol vardır: her katılımcı konu sayfasından doğrudan **gizleme oylaması** açabilir.

---

## 19. Panelim (üyenin kendi paneli)

Hesap menüsünden (sağ üstteki avatar) ya da telefonda alttaki **Panelim** sekmesinden açılır.

| Bölüm | İçinde ne var |
|---|---|
| Özet | Oyunu bekleyen oylamalar, açtığın konular, son mesajların, şikayetlerin, sayılar |
| Bildirimler | Bildirim listesi ve "Bu cihazda anlık bildirim" düğmesi |
| Hesap bilgileri | Ad, doğum tarihi, adres (yalnızca sen görürsün); adres değiştirme |
| Oy devri | Verdiğin ve aldığın devirler, yeni devir |
| Uzmanlık | Uzmanlıkların; seçtiğin alan için ön şart ve kontenjan durumu; başvuru formu |
| Güvenlik | Şifre değiştirme, yeni kurtarma kodu |
| Uygulama ve API | Telefona kurma yolları, API anahtarları |

Yöneticilerde menünün altında **Yönetim paneli** bağlantısı da vardır.

---

## 20. Yönetim paneli

Yalnızca yöneticiler görür (`/yonetim`). **Bütün yöneticiler eşittir**; ayrı bir süper yönetici yoktur.

Yönetici **yalnızca siteyi yönetir**. Kararları etkileyecek hiçbir düğmesi yoktur.

| Bölüm | Ne yapılır |
|---|---|
| Pano | Üye, aktif üye, açık konu, süren oylama, haftalık mesaj/oy sayıları; son 14 günün grafiği; konu durumları; bilgi amaçlı listeler (yakında biten oylamalar, oylamaya geçecek konular, biten uzmanlıklar), bekleyen şikayetler, defter sorunları; son yönetim işlemleri |
| Üyeler | Arama ve süzme; her üye için: **yönetici yap / çıkar**, **askıya al / askıyı kaldır**, uzmanlıkları (yalnızca görür), kişisel bilgiler, son etkinlik |
| Şikayetler | Tabanı geçmiş bekleyen şikayetler ve sonuçlananlar |
| Konular | Tüm konular ve durumları (yalnızca izleme) |
| Oylamalar | Süren ve biten oylamalar (yalnızca izleme) |
| Toplu bildirim | Hedef grup seçip bildirim gönderme |
| Kategoriler | Kategori ekleme, ad ve renk değiştirme (silme yok, eski konular bağlı) |
| Sistem | Site duyurusu, yeni üyeliği açma/kapama, yapay zeka hesabı açma, kayıt defteri deneme ve onarım, veritabanı yedeği indirme |
| Günlük | Bütün olaylar; türe ve kişiye göre süzme |

**Yöneticinin yapamadıkları:**
- içerik silmek ya da gizlemek (yalnızca oylamaya sunabilir),
- **uzman atamak** ya da uzmanlığı geri almak,
- bir oylamayı **erken bitirmek**, süresini ya da sonucunu değiştirmek,
- bir konuyu bir sonraki aşamaya geçirmek ya da yeniden açmak,
- oy ağırlığı kazanmak (oyu 1'dir),
- kendi yetkisini değiştirmek, kendini askıya almak, bir yöneticiyi yetkisi alınmadan askıya almak.

**Askıya alma:** 1–365 gün arası, en az 10 karakterlik neden zorunlu. Neden şeffaflık günlüğünde herkese görünür.
Askıdaki üye okur ama yazamaz, oy veremez, konu açamaz; eski oyları ve mesajları olduğu gibi kalır. Süre bitince kendiliğinden kalkar.

**İlk yöneticiyi atamak:** `python calistir.py --yonetici TAKMA_AD`. Sonrası panelden.

**Sunum kipi (`--demo`):** Sunumda 24–48 saat beklenemeyeceği için sunucu `python calistir.py --demo` ile başlatılırsa Konular ve Oylamalar
sayfalarında **"Süreyi ilerlet"** düğmesi çıkar. Bu düğme yalnızca beklemeyi kısaltır: o ana kadarki oylarla, aynı kurallarla sayım yapılır;
her kullanımı günlüğe yazılır. Normal çalıştırmada bu düğme yoktur ve adresi de çalışmaz.

---

## 21. Arayüz

**Üç ana bölüm** (üst çubuk):
- **Konular:** Akış, Keşfet ve Kategoriler sekmeleri. Akışta kategori çipleri, durum süzgeci (Tümü, Katılabildiğim, Gözlemci olduğum, Tartışmada, Oylamada...) ve gündem sütunu.
- **Oylamalar:** Gündem (süren oylamalar) ve Kararlar arşivi.
- **Meclis:** Nasıl işler?, Yönetmelik, Kayıt defteri, Üye ağı, Şeffaflık günlüğü, API.

**Konular bölümünün üç sekmesi:** **Akış** (konu listesi), **Keşfet** (gündem ve trendler), **Kategoriler** (13.2).

**Akış sayfası:**
- Üstte **vitrin**: şu an en çok konuşulan konu, süresi en yakın dolacak oylama ya da tartışma, son karar.
- Kategori çipleri (konu sayısıyla) ve "Tüm kategoriler" bağlantısı; bir ana kategori seçilince alt kategorileri de çıkar.
- Konu kartlarında en çok konuşulan üç konuya **Gündemde** rozeti.
- Sağ sütunda (telefonda listenin altında): **Trend konular**, **Öne çıkan kelimeler**, **Yakında bitenler**, **Kategorilerin nabzı**.

**Keşfet sayfası** (`/kesfet`): son 24 saatin sayıları (mesaj, fikir, oy, yeni konu, süren oylama), trend konular,
öne çıkan kelimeler, yakında bitenler, bütün kategorilerin nabzı, son kararlar, haftanın en etkin üyeleri ve canlı akış.

Nasıl hesaplanır (`gundem.py`):
| Gösterge | Hesap |
|---|---|
| Trend konular | Son 24 saatte (az etkinlik varsa son 3 gün) puan = mesaj + 2 × fikir + 0,5 × oy (yeni açılan konuya +3) |
| Öne çıkan kelimeler | Son 7 günün mesajlarında **en çok farklı konuda** geçen kelimeler; sık kelimeler (ve, ama, olsun...) sayılmaz. Tıklayınca arar |
| Kategorilerin nabzı | Her ana kategoride bu haftaki mesaj sayısı, son 7 günün çizgisi ve geçen haftaya göre değişim (↑/↓ %) |
| Yakında bitenler | Bitişi en yakın oylamalar ve oylamaya geçecek tartışmalar |
| Canlı akış | Şeffaflık günlüğündeki konu, sonuç, karar, uzmanlık ve yeni kategori olayları |

Bunların hiçbiri oylamaları etkilemez; yalnızca okuyana "şu an ne konuşuluyor?" sorusunun cevabını verir.

**Sağ üst:** arama, bildirim zili, "Yeni konu", avatar menüsü (Panelim, Bildirimler, Herkese açık profil, Yönetim paneli, Görünüm, Çıkış).

**Giriş katmanı:** Giriş yapmamış biri `/` adresinde önce tanıtım sayfasını görür; giriş yapmış üye doğrudan konulara gider.

**Telefonda:** Ana bölümler **alttaki sekme çubuğuna** geçer: Konular, Oylamalar, ortada yuvarlak **+** (yeni konu), Meclis, Panelim.

**Renkler (iki renk):** Ana renk **taş beyazı** (`#ebe7df`, kartlarda `#f6f4ef`), yan renk **kaktüs yeşili** (`#4a6642`).
Kırmızı yoktur; durumlar ikon ve dolgu biçimiyle ayrılır (sürüyor = yeşil nokta, sonuçlandı = ✓, olumsuz = kesikli çerçeve ve ✕).

**Karanlık tema:** Cihaz koyu moddaysa kendiliğinden açılır. Avatar menüsündeki **Görünüm**'den Otomatik / Açık / Koyu seçilir; seçim o cihazda saklanır.

---

## 22. Mobil

Üç yol var; hepsi **aynı siteyi** açar, yani aynı hesap ve aynı veri.

| Yol | Nasıl | Not |
|---|---|---|
| **Expo Go** (`mobil-expo/`) | `baslat_mobil.bat`'a çift tıkla, çıkan QR kodu Expo Go ile okut | Expo SDK 57. En hızlı deneme yolu. Anlık bildirim yok |
| **Android uygulaması** (`mobil/`) | Android Studio ile APK derlenir | Capacitor. Firebase ayarlanırsa anlık bildirim var |
| **Ana ekrana ekle** | Telefon tarayıcısında siteyi açıp menüden seç | Web uygulaması (PWA); çevrimdışıyken "bağlantı yok" sayfası |

Uygulamalarda ek olarak: geri tuşu, çentik boşlukları, sunucuya ulaşılamazsa hata ekranı, site dışı bağlantıların tarayıcıda açılması.
Site, uygulamada açıldığını tarayıcı kimliğindeki `AgoraMobil` ekinden anlar.

**Telefonla bilgisayar aynı Wi-Fi'da olmalı** ve forum `--ag` ile başlatılmalı.

---

## 23. API

Başka programların forumu kullanması için JSON arayüzü: `/api/v1`. Belgeleri sitede **Meclis › API**.

- Giriş: `POST /api/v1/giris` → anahtar döner. Sonraki isteklerde `Authorization: Bearer <anahtar>`.
- Panelim › Uygulama ve API'den de anahtar oluşturulur/silinir.
- Başlıca uç noktalar: `ben`, `konular` (listele, getir, aç), `konular/<id>/mesajlar`, `konular/<id>/fikir`, `denetim`, `oylamalar` (listele, getir, oy ver),
  `gundem` (trendler), `kategoriler` (listele, öner), `kararlar`, `bildirimler`, `defter`, `graf`, `yonetmelik`, `ara`, `anlik` (anlık bildirim aboneliği).
- API **hiçbir zaman** ad soyad, doğum tarihi, adres döndürmez.

---

## 24. Güvenlik

- Şifreler ve kurtarma kodları **hash**'lenerek saklanır; düz hâlleri hiçbir yerde durmaz.
- 5 hatalı girişte 10 dakika kilit.
- Her formda **CSRF** anahtarı (başka siteden sahte form gönderilemez).
- **İçerik güvenlik politikası (CSP)** ve diğer güvenlik başlıkları: yalnızca sitenin kendi betikleri çalışır, site başka sitenin çerçevesine gömülemez.
- Veritabanı sorguları parametrelidir (SQL enjeksiyonu yok); şablonlar metni otomatik kaçışlar (XSS yok).
- API anahtarları da hash olarak saklanır.
- Kişisel veri: forumda görünmez, API'de dönmez, deftere yazılmaz; mesajlarda telefon/e-posta/kimlik no engellenir.
- Oturum çerezi JavaScript'ten okunamaz (HttpOnly).
- Anlık bildirim anahtarı `instance/vapid_ozel.pem` ve Firebase anahtarı `instance/firebase.json` gizlidir.
- Oturum anahtarı kodda yazılı değildir: ortam değişkeninden okunur ya da ilk açılışta üretilip yalnızca sunucuyu çalıştıran
  kullanıcının okuyabildiği bir dosyaya yazılır.
- Şifre değişince ya da sıfırlanınca **bütün eski oturumlar ve API anahtarları** geçersiz olur (çalınmış bir çerez işe yaramaz).
- Şifre değiştirme ve kurtarma kodu yenileme de giriş gibi hatalı deneme kilidine tabidir.
- Bir adresten saatte en fazla 20 yeni üyelik açılabilir (sahte hesap seli).
- Türkçe büyük/küçük harf ya da Türkçe karakter farkıyla benzer takma ad alınamaz (`Çağlar` varken `çağlar` ya da `Caglar` olmaz).
- Girişten sonra yalnızca **site içi** bir adrese dönülür (`//kotu.site` ya da `/\t/kotu.site` gibi hilelerle dışarı yönlendirme olmaz).
- Anlık bildirim abonelik adresleri yalnızca bilinen bildirim servislerine (Google, Mozilla, Apple, Microsoft) gidebilir; sunucu,
  kullanıcının verdiği keyfi bir adrese istek atmaz (SSRF).
- Kimlik numarası denetimi resmi sağlama algoritmasıyla yapılır; 11 haneli her sipariş ya da fatura numarası engellenmez.
- Bağımlılıkların sürümleri `requirements.txt`'de sabittir.

---

## 25. Kullanılan mimariler

Burada "mimari", programın parçalarının nasıl bölündüğü ve birbirleriyle nasıl konuştuğu demek. Agora'da birden fazla
mimari fikir birlikte kullanılıyor; her birinin **ne olduğu**, **Agora'da nerede olduğu** ve **neden seçildiği** aşağıda.

### 25.1 İstemci–sunucu
Bütün veri ve kurallar **sunucuda** (Flask uygulaması) durur. Tarayıcı, Expo Go uygulaması, Android uygulaması ve API
kullanan programlar **istemcidir**; sadece ister ve gösterir.
- **Neden:** Oylama, sayım, eşik gibi kuralların tek bir yerde çalışması gerekir. İstemcide kural olsaydı biri değiştirip hile yapabilirdi.

### 25.2 Katmanlı mimari (3 katman)
```
┌─────────────────────────────────────────────┐
│ Sunum katmanı      web/ + templates/ + static/  │  HTTP, oturum, CSRF, yetki, sayfa çizimi
├─────────────────────────────────────────────┤
│ İş kuralı katmanı  forum/*.py                   │  oylama, sayım, yönetmelik, devir, defter...
├─────────────────────────────────────────────┤
│ Veri katmanı       SQLite + defter düğümleri    │  kalıcı kayıt
└─────────────────────────────────────────────┘
```
- Her katman **yalnızca altındakini** çağırır. Web katmanı kural içermez; "oy ver" düğmesine basılınca sadece `oylama.oy_ver(...)` fonksiyonunu çağırır.
- Kurallar hata durumunda `KuralHatasi` fırlatır; web katmanı bunu kullanıcıya uyarı olarak, API ise JSON hata olarak gösterir.
- **Neden:** Aynı kurallar hem web sitesinde hem API'de hem testlerde **aynen** kullanılır. Testler tarayıcı açmadan doğrudan iş kuralı katmanını dener.

### 25.3 MVC'ye benzer düzen
- **Model:** `forum/*.py` modülleri ve veritabanı tabloları
- **View (görünüm):** Jinja2 şablonları (`templates/`)
- **Controller (denetleyici):** Flask rotaları (`web/*.py`): isteği alır, modeli çağırır, şablonu seçer.

### 25.4 Sunucu tarafında sayfa üretimi (çok sayfalı uygulama)
Sayfalar sunucuda HTML olarak hazırlanır ve tarayıcıya hazır gelir (React gibi bir tek sayfa uygulaması değildir).
JavaScript yalnızca küçük kolaylıklar için kullanılır (kopyala düğmesi, il seçince ilçelerin gelmesi, tema, anlık bildirim).
- **Aşamalı iyileştirme:** JavaScript kapalı olsa da formlar çalışır; JavaScript sadece deneyimi güzelleştirir.
- **Neden:** Basit, hızlı, arama motoru ve eski telefon dostu; mobil uygulamalar aynı sayfaları gösterebilir.

### 25.5 Modüler yapı (Flask blueprint'leri)
Sunum katmanı konulara göre ayrı modüllere bölünmüştür:
| Blueprint | Adresler |
|---|---|
| `hesap` | Kayıt, giriş, çıkış, şifre kurtarma |
| `konular` | Konu akışı, konu sayfası, konu açma, fikir, mesaj, şikayet |
| `oylamalar` | Gündem, oylama sayfası, kararlar |
| `profil` | Panelim, herkese açık profil, bildirimler |
| `genel` | Yönetmelik, kayıt defteri, üye ağı, günlük, nasıl işler |
| `yonetim` | Yönetim paneli (`/yonetim`) |
| `api` | REST API (`/api/v1`) |

Yönetim blueprint'i girişte tek bir kontrol yapar: yönetici değilsen hiçbir sayfası açılmaz (403).

### 25.6 REST API
`/api/v1` altında JSON konuşan bir arayüz. Kimlik doğrulama **Bearer anahtarıyla** yapılır (çerez gerekmez).
Aynı iş kuralı katmanını kullanır; yani API'den verilen oy da aynı kurallarla sayılır.

### 25.7 Durum makinesi (state machine) — State deseni
Konunun yaşam döngüsü bir **durum makinesidir**: TARTISMA → OYLAMA (tur 1…5) → KARARA_BAGLANDI ya da SONUCSUZ; herhangi bir
durumdan oylamayla KALDIRILDI.
Her durumda yalnızca belli işlemler yapılabilir (ör. mesaj yalnızca TARTISMA ve OYLAMA'da, fikir yalnızca TARTISMA'da ve 1. turda yazılır).
Her durum `konu_durumlari.py`'de bir **sınıftır** ve "bu durumda ne yapılabilir?" sorusunu kendisi yanıtlar. Önceden bu sorular
`if durum == ...` biçiminde onlarca yere dağılmıştı; bir yerde unutulan kontrol, kaldırılmış bir konunun geçmişinin hâlâ
okunabilmesine yol açıyordu.
- **Atomik geçiş:** Durum değişikliği `UPDATE ... WHERE durum = 'eski durum'` biçiminde yapılır. Aynı anda iki istek aynı geçişi denerse yalnızca biri başarır; böylece örneğin aynı konu için iki tane 1. tur açılamaz.

### 25.8 Tek teklif mekanizması — Strategy + Template Method + Registry
Altı oylama türü (fikir turu, gizleme, kaldırma, uzmanlık, yönetmelik, yeni kategori) **aynı iskeleti** kullanır:
aç → oy topla → say → sonuçlandır. İskelet `oylama.sonuclandir`'dadır (**Template Method**); türden türe değişen adımlar
(seçenekler neler, eşik ne, sonuç çıkınca ne olacak, kime haber verilecek) her türün kendi sınıfındadır (**Strategy**,
`teklif_turleri.py`). Sınıflar `@kaydet` ile bir kayıt defterine (**Registry**) eklenir; kod, türü adından bulur:
```
KARAR (FikirTuru)            → eleme kurallarını uygula: karar / sonraki tur / sonuçsuz
MESAJ_SILME (MesajGizleme)   → mesajları gizle
KONU_SILME (KonuKaldirma)    → konuyu kaldır
UZMANLIK (Uzmanlik)          → uzmanlığı ver (kontenjan hâlâ uygunsa)
YONETMELIK (Yonetmelik)      → değişikliği uygula
KATEGORI (Kategori)          → kategoriyi ekle
```
- **Neden:** Oran hesabı, yeter sayı, çekimser, devir, gizli oy, makbuz kuralları **bir kez** yazılır ve bütün oylamalarda aynen geçerlidir.
  Yeni bir oylama türü eklemek, **yeni bir sınıf yazmak** demektir; mevcut koda dokunulmaz (açık/kapalı ilkesi). Önceden aynı iş
  beş dosyada `if tip == ...` dalı demekti.
- Eleme kararı (`sonuclar.tur_karari`) veritabanına dokunmayan **saf bir fonksiyondur**: sayım sonucunu alır, "kabul / devam / sonuçsuz" döndürür. Bu yüzden kolayca test edilir.

### 25.9 Kuralların veri olarak tutulması (yapılandırılabilir kural motoru)
Eşikler, süreler, oranlar kodda sabit değil, veritabanındaki `parametreler` tablosunda durur. Kod bir sayıya ihtiyaç duyunca
`yonetmelik.deger(db, "ELEME_TUR3")` diye sorar. Denetim maddelerinin ciddiyeti (Engeller/Uyarır/Kapalı) de veridir.
- **Neden:** Kurallar **üyelerin oylamasıyla** değişebilsin, kod değiştirmeye gerek kalmasın.

### 25.10 Ekleme-yalnız kayıt ve hash zinciri (blokzincir benzeri)
Kayıt defteri **yalnızca eklenir**, hiçbir blok güncellenmez ya da silinmez. Her blok bir öncekinin özetini taşır.
- **Çoğaltma (replikasyon):** Zincir üç düğümde tutulur.
- **Çoğunluk uzlaşması (quorum):** 3 düğümden 2'si aynıysa o zincir doğrudur.
- **Kendini onarma:** Bozuk düğüm çoğunluktan yeniden yazılır.
- Not: Bu, gerçek bir blokzincirin (madencilik, ağ üzerinde düğümler) basitleştirilmiş, tek sunucuda çalışan bir modelidir.

### 25.11 "Kaydedilince yap" düzeni (commit'e bağlı yan etkiler) — Observer ve Memento
Bir işlem sırasında hem veritabanına yazılıyor hem de dışarıya etki ediliyorsa (deftere blok, telefona bildirim),
dış etkiler hemen yapılmaz; bir **kuyruğa** eklenir. Veritabanı işlemi başarıyla kaydedilince (commit) kuyruk çalışır;
işlem geri alınırsa (rollback) kuyruk boşaltılır.
- Veritabanı bağlantısı defteri **tanımaz**: defter, "işlem kaydedildi" olayına abone olur (**Observer**). Böylece alt katman
  (veritabanı) üst katmana (defter) bağımlı olmaz.
- Bir işin içinde yalnızca bir parçayı geri almak gerekirse (ör. zamanlayıcıda tek bir konu hata verdi) **kayıt noktası** (SAVEPOINT)
  kullanılır; kuyrukların o anki boyu saklanır ve geri dönülünce kuyruklar da o boya kısaltılır (**Memento**).
- Yan etki başarısız olursa (ör. disk dolu) istek hata vermez; veri zaten kaydedilmiştir, kullanıcı işlemi tekrarlarsa çift kayıt
  oluşurdu. Hata günlüğe yazılır, eksik defter kaydını tutarlılık denetimi gösterir.
- **Neden:** Yarıda kalan bir işlem deftere yazılmasın, olmayan bir oylama için telefona bildirim gitmesin.
  Bu, yazılımda "transactional outbox" denen düzene benzer.

### 25.12 Arka plan işleri ve zamanlayıcı
- Süresi dolan tartışmalar ve oylama turları iki yoldan işlenir: **her web isteğinde** kısa bir kontrol ve **her 30 saniyede bir** çalışan arka plan iş parçacığı.
- İkisi aynı anda çalışsa bile sorun olmaz, çünkü geçişler atomiktir (25.7).
- Anlık bildirim gönderimi **ayrı iş parçacığında** çalışır; kullanıcı beklemez.

### 25.13 Zarif gerileme (graceful degradation)
İsteğe bağlı parçalar yoksa uygulama bozulmaz, daha basit yoldan devam eder:
- `pywebpush` yoksa → anlık bildirim kapalı, site içi bildirimler çalışır.
- Firebase ayarı yoksa → Android uygulamasında anlık bildirim düğmesi durumu açıklar.
- İnternet yoksa → PWA "bağlantı yok" sayfasını gösterir.

### 25.14 Ağaç ve graf veri yapıları
- **Ağaç (hiyerarşi):** Konum (ülke › bölge › il › ilçe) ve kategori ağaçları. Uygunluk, iki düğümün **ortak atasının derinliğiyle** ölçülür.
- **Graf (ağ):** Üyeler düğüm, etkileşimler kenar. Üzerinde **PageRank** (etki), **etiket yayılımı** (görüş grupları) ve **Gini** (güç yoğunlaşması) hesaplanır.
- Oy devri zinciri de bir graftır: döngü kurulamaz, zincir izlenerek oy son kişiye taşınır.
- Alt konular da bir ağaçtır: alt konu, üst konunun kurallarını miras alır ve yalnızca daraltabilir.

### 25.15 İnce istemci mobil mimari (hibrit uygulama)
Mobil uygulamalar sitenin kopyası değil, siteyi gösteren bir **kabuktur** (WebView).
```
Expo Go / Android uygulaması  ──(WebView)──►  Agora sunucusu  ◄──  Tarayıcı
```
- Kabuk yalnızca telefona özgü işleri yapar: sunucu adresi, geri tuşu, çentik boşlukları, hata ekranı, anlık bildirim kaydı.
- **Neden:** Tek bir kod tabanı. Sitede yapılan her değişiklik uygulamaya **anında** yansır, uyumluluk sorunu çıkmaz.
- **PWA:** Service worker, uygulama kabuğunu (CSS, JS, simgeler) önbellekler; sayfaları her zaman ağdan ister ("önce ağ"), çünkü oylar bayat gösterilmemeli.

### 25.16 Rol tabanlı yetki
Yetki üç düzeyde kontrol edilir: giriş gerekli mi (`giris_gerekli`), yönetici mi (`yonetici_gerekli`), bu konuda katılımcı mı
(uygunluk). Askıdaki üyenin yazma istekleri en başta, tek bir noktada durdurulur.
- **Yetkilerin ayrılması:** Yönetici rolü yalnızca *yönetim* yetkisi taşır; *karar* yetkisi yalnızca oylamalardadır. Yönetim panelinde
  kararları etkileyen bir işlem **hiç tanımlı değildir** (gizlenmiş değil, yoktur).

### 25.17 Katmanlı güvenlik (derinlemesine savunma)
Tek bir önleme güvenilmez; her katmanda ayrı önlem vardır: şifre hash'i, giriş kilidi, CSRF, CSP başlıkları, parametreli SQL,
otomatik HTML kaçışlama, kişisel veri denetimi, API'de kişisel veri döndürmeme, deftere kişisel veri yazmama.

### 25.18 Tasarım belirteçleri (design tokens)
Renkler CSS'te doğrudan yazılmaz; `:root` içinde değişken olarak tanımlanır (`--t50`, `--y600`...) ve bileşenler bunları kullanır.
Karanlık tema yalnızca bu değişkenleri yeniden tanımlar; hiçbir bileşene dokunmaz.

### 25.19 Test mimarisi
- Her test **boş, geçici bir veritabanıyla** başlar; testler birbirini etkilemez.
- **Zaman enjeksiyonu:** Kodun tamamı saati `zaman.simdi()` üzerinden okur. Testler bu fonksiyonu değiştirip zamanı ileri sarar ("48 saat geçti") ve süre kurallarını saniyeler içinde dener.
- Web testleri Flask'ın test istemcisiyle gerçek istekler atar (giriş, CSRF, yetki, sayfalar).
- Eleme kuralları saf fonksiyon olduğu için (25.8) sınır değerleri (%4,9 – %5 – %75) doğrudan denenir.
- **Sahte nesneler:** kayıt defteri testleri disk yerine bellekte çalışan sahte depoyla (`BellekDugumDeposu`), anlık bildirim
  testleri gerçek servis yerine sahte kanalla (`SahteKanal`) çalışır. Testlerde şifre özeti hızlı bir yöntemle yapılır
  (`guvenlik.SIFRE_YONTEMI`); 172 test yaklaşık 7 saniye sürer.
- **Hata önce test:** yazılım mühendisliği incelemesinde bulunan her hata için önce hatayı yeniden üreten bir test yazıldı, sonra
  düzeltildi (`testler/test_duzeltmeler.py`).
- **Ölçüm testleri:** denetim kurallarının etiketli örneklerdeki başarımı ve temel çizgileri geçtiği her çalıştırmada denetlenir
  (`testler/test_olcum.py`).

### 25.20 Yerinde veritabanı güncellemesi (migration)
Uygulama açılırken şema kontrol edilir: eksik tablo ve sütunlar **veri silinmeden** eklenir, kaldırılan sütunlar düşürülür.
Yönetmelik metinleri koddan tazelenir ama oylamayla değişmiş değerlere dokunulmaz.
Eski akıştan kalan kayıtlar bir kez yeni akışa uyarlanır: açık konular tartışmaya döner (süreleri baştan başlar), yarım kalan eski oylamalar
iptal edilir; üyeler, mesajlar ve geçmiş oylamalar olduğu gibi kalır.

### 25.21 Diğer tasarım desenleri
Yukarıdakilere ek olarak yönetmelik denetimi bir **Chain of Responsibility** (her madde zincirin bir halkası, `denetim.py`),
anlık bildirim kanalları **Adapter** (Web Push ve Firebase aynı arayüzün arkasında, `anlik.py`), kayıt defterinin düğümleri
**Repository** (SQLite dosyası ya da test için bellek, `defter.py`), konu sayfası **Facade** (`gorunum.py`) desenidir.
Her desenin hangi sorunu çözdüğü, sınıf diyagramları ve SOLID ilkeleriyle eşlemesi [tasarim.md](tasarim.md) 8. bölümde.

### 25.22 Ölçüm
Hiçbir başarım iddiası tahmine dayanmaz; `olcum/` klasöründeki betiklerle ölçülür: denetim kurallarının kesinlik ve duyarlılığı
(aptal temel çizgilerle karşılaştırmalı), sayfaların p95 yanıt süresi, iş/ürün/koruyucu metrikler. Sonuçlar ve yorumları
[analiz.md](analiz.md) dosyasında.

---

## 26. Teknik yapı

**Kullanılanlar:** Python 3.11 ve üstü, Flask, SQLite, Jinja2 şablonları, düz CSS ve JavaScript (çerçeve yok).
Mobil: Expo (React Native WebView) ve Capacitor.

Katmanların ve diğer mimari kararların açıklaması 25. bölümde.

**Dosyalar:**
| Dosya | Görevi |
|---|---|
| `ayarlar.py` | Site adı, renkler, sabitler, yönetmeliğin varsayılan parametreleri |
| `yonetmelik.py` | Maddeler, parametreler (anlamlı aralıklarıyla), yönetmelik değişikliği |
| `denetim.py` | Denetim maddeleri D1–D7 (Chain of Responsibility); mesaj denetimi |
| `konu_durumlari.py` | Konunun durumları ve her durumda izin verilen işlemler (State) |
| `teklif_turleri.py` | Oylama türleri (Strategy + Registry) |
| `gorunum.py` | Konu sayfasının verisi (Facade) |
| `metin.py`, `hatalar.py` | Yüzde biçimi, kısaltma, güvenli yönlendirme denetimi; kural hatası ve sayı ayrıştırma |
| `ontoloji.py` | Konum ve kategori ağaçları, kavramlar, benzerlik |
| `uygunluk.py` | Kim katılımcı, kim gözlemci; oy ağırlığı |
| `konular.py` | Konu açma ve düzenleme, fikirler, turların açılması, alt konu, itiraz, mesajlar, gizleme |
| `oylama.py` | Oylama açma, oy, makbuz, sayım (çift oran, çekimser, yeter sayı), sonuçlandırma iskeleti (Template Method) |
| `sonuclar.py` | Fikir turunun **eleme kuralları** (saf işlev) ve turun kararının anlık görüntüsü (`TurKarari`) |
| `kararlar.py` | Kabul edilen fikirlerin (kararların) kaydı |
| `devir.py` | Oy devri |
| `uzmanlik.py` | Ön şart, kontenjan, başvuru, uzmanlığın verilmesi |
| `kategoriler.py` | Kategori önerisi, kabul edilince ekleme; kategoriler sayfasının arama, süzme, sıralama listesi |
| `gundem.py` | Trend konular, öne çıkan kelimeler, kategori nabzı, yakında bitenler, canlı akış |
| `yz.py` | Yapay zeka üyenin özetleri |
| `defter.py` | Kayıt defteri; düğüm depoları (Repository), commit aboneliği (Observer), doğrulama önbelleği |
| `graf.py` | Üye ağı, PageRank, görüş grupları, Gini |
| `yonetim.py` | Yönetim paneli işleri |
| `sikayetler.py` | Şikayet kutusu |
| `anlik.py` | Anlık bildirim kanalları (Adapter) |
| `kullanicilar.py`, `guvenlik.py`, `bildirimler.py`, `arama.py`, `gunluk.py`, `gorevler.py`, `veritabani.py` | Üyeler, güvenlik, bildirim, arama, günlük, zamanlayıcı, bağlantı |
| `web/` | Sayfa rotaları ve API; `istek.py` (istek öncesi zincir: kimlik, askı, CSRF, zamanlayıcı, yazma kilidi), `hata_sayfalari.py`, `sablon.py` (şablon filtreleri) |
| `templates/` | Sayfalar (`panel/` = Panelim, `yonetim/` = yönetim paneli) |
| `static/` | CSS, JS, simgeler, service worker |
| `testler/` | 172 otomatik test |
| `olcum/` | Ölçüm betikleri ve etiketli örnekler ([analiz.md](analiz.md)) |

**Tek teklif mekanizması:** Bütün oylamalar (fikir turları, gizleme, kaldırma, uzmanlık, yönetmelik) aynı "teklif" yapısından geçer;
sayım ve eşik kuralları tek yerde yazılıdır. Oylama türü değişince sadece "bitince ne olacak" kısmı değişir.

**Veritabanı güncellemesi:** Yeni sütunlar/tablolar mevcut veritabanına veri silinmeden eklenir; yönetmelik metinleri her açılışta koddan tazelenir (değerlere dokunulmaz).

---

## 27. Çalıştırma

| Komut | Ne yapar |
|---|---|
| `python calistir.py` (ya da `baslat.bat`) | Forumu başlatır, tarayıcıyı açar (`http://127.0.0.1:5000`) |
| `python calistir.py --ag` | Aynı Wi-Fi'daki telefonlardan erişim; telefon adresini ekrana yazar |
| `baslat_mobil.bat` | Forumu ve Expo'yu iki pencerede birlikte açar |
| `python calistir.py --sifirla` | Veritabanını ve defteri silip demo verisini baştan yükler (**dikkat: kendi hesapların da gider**) |
| `python calistir.py --yonetici AD` | Bir üyeyi yönetici yapar |
| `python calistir.py --demo` | Sunum kipi: yönetim panelinde "Süreyi ilerlet" düğmesi açılır (20. bölüm) |
| `python calistir.py --demo-verisiz` | Boş veritabanına demo verisini (ve şifresi herkesçe bilinen demo hesaplarını) yüklemez |
| `python -m unittest discover testler` | Testleri çalıştırır |
| `python olcum/denetim_olcumu.py` | Denetim kurallarını etiketli örneklerle ölçer |
| `python olcum/gecikme_olcumu.py` | Sayfaların yanıt süresini (p50, p95) ölçer; `--defter-blok 50000` ile büyük defterde |
| `python olcum/urun_metrikleri.py [veritabanı]` | İş, ürün ve koruyucu metrikleri hesaplar |

**Ortam değişkenleri:** `FORUM_VERITABANI` (veritabanı yolu), `FORUM_GIZLI_ANAHTAR` (oturum anahtarı; verilmezse ilk açılışta
üretilip yalnızca sunucuyu çalıştıran kullanıcının okuyabildiği bir dosyada saklanır), `FORUM_HTTPS=1` (HTTPS arkasında yayınlanıyorsa
güvenli çerez), `FORUM_ANLIK_ILETISIM` (Web Push iletişim adresi), `FORUM_SIFRE_YONTEMI` (şifre özeti yöntemi; varsayılan scrypt).

**İsteğe bağlı:** `pip install pywebpush` → anlık bildirim.

**Demo hesapları** (hepsinin şifresi `forum1234`):
| Takma ad | Özelliği |
|---|---|
| `yonetici` | Yönetici |
| `ayse`, `elif` (17 yaş) | İstanbul › Kadıköy |
| `mehmet`, `burak` | İstanbul › Beşiktaş, İstanbul › Kartal |
| `zeynep` | Ankara (İstanbul konularında gözlemci) |
| `can`, `selin` | İzmir |
| `ece` · `onur` · `defne` · `mert` | İzmir › Konak · Ankara › Keçiören · İstanbul › Beşiktaş · Bursa |
| `dr.deniz` | Uzman: Sağlık |
| `kaan.hoca` | Uzman: Teknoloji › Yazılım |
| `Bilge` | Yapay zeka üye (giriş yapamaz) |

**Demo verisi:** son 12 günde yaşanmış gibi oluşturulur (14 üye, 19 konu, yaklaşık 120 mesaj ve 190 oy), böylece trendler,
kategori nabzı ve etkinlik grafikleri dolu görünür. Bir konunun yolculuğunun her hâli hazır gelir:
| Konu | Ne gösterir |
|---|---|
| Final projesi hangi dille yapılsın? | Beş turun tamamı: uzman ağırlığı yüzünden 1. turda elenen fikir, 3. turda %10 altı, 5. turda karar |
| Farklı teknoloji deneyen gruplara ek puan | Yukarıdaki karara açılmış **itiraz konusu** |
| Kütüphanede gece açık okuma salonu | 2. turda **ezici üstünlük** (%79) |
| Kulüp toplantıları hafta sonu yapılsın mı? | İlk turda **ezici üstünlük** (%79) |
| Yemekhanede etsiz menü | **2. tur sürüyor**; çekimser oy, elenen fikir, tabanı dolmuş şikayet |
| Öğrenci bursları · Plastik bardak | **1. tur sürüyor** |
| Mahallelere gençlik meclisi | Günün en çok konuşulan konusu (trendlerde 1.) |
| İstanbul'da gece hatlarında öğrenci indirimi | Tartışmada; konum kuralı, alt konular, gizleme oylaması |
| Spor ve Oyun kategorisi (Genel) | Genel'de tartışılan ve **oylamada** olan kategori önerisi |
| Kültür ve Sanat › Tiyatro | Oylamayla **eklenmiş** kategori ve içindeki konu; reddedilen "Magazin" önerisi |
| Final sınavları kaldırılsın | Yeter sayı olmadığı için **sonuçsuz** |

---

## 28. Ödev gereksinimleri nerede karşılanıyor?

| Gereksinim | Karşılığı |
|---|---|
| Herkes konu açar, düzenler, siler | Konu açma ve düzenleme (4.1), kaldırma oylaması (4.2) |
| Çoğunluk kararı | Fikir oylaması: turlar, eleme, ezici üstünlük (4.3–4.5) |
| Alt konular | Alt konu (4.2) |
| Tartışma fikir birliğiyle biter | En fazla beş turda tek fikir kalır ve karar olur (4.4–4.6) |
| Giriş: ad soyad, adres, doğum tarihi, şifre, takma ad | Kayıt (3) |
| Bilgiler katılım kuralı olur | Katılımcı / gözlemci (5) |
| Herkes eşit, bazıları daha eşit | Kurallar herkese aynı, herkes bir fikir yazar; uzman oyu 10, çift oranla dengeli (7) |
| Kurallar ve uygunluk ontolojiyle ölçülür | Yönetmelik denetimi D1–D7, konum/kategori ağaçları (12, 13) |
| Tartışmalar silinmez; kısmen silmek oylamayla | Düzenleme geçmişi, 3/4 ile gizleme, toplu gizleme, iz kalır (6) |
| Oy hakkı devredilir | Oy devri (9) |
| Bazı üyeler yapay zeka | Yapay zeka üye: özetler (11) |
| Azınlık korunur | 8. bölüm |
| Bilirkişi (uzman) | Uzmanlık: ön şart, kontenjan, alanın oylaması (10) |
| Uygulama ve web sitesi | Expo Go, Android, PWA, API (22, 23) |
| Dağıtık defter | Kayıt defteri (14) |
| Kişiler grafta tutulur | Üye ağı (15) |
| Akran öğrenmesi | Argüman / karşı argüman / soru / kaynak mesajları, fikirlerin altında tartışma, özetler (4.2, 11) |

Not: Eski sürümdeki "konu, çoğunluk kabul ederse açılır" adımı kaldırıldı. Artık konu hemen açılır; çoğunluk, konunun **sonucuna** karar verir.

---

## 29. Karıştırılabilecek noktalar

- **Fikir ≠ mesaj.** Mesaj tartışmadır (argüman, soru...), sınırsız yazılır. Fikir oylanacak öneridir, kişi başı bir tanedir.
- **Tartışma bitince mesaj bitmez.** "Tartışma" ilk 24 saatin adıdır; oylama turları sürerken de mesaj yazılır. Mesaj yalnızca konu kapanınca biter.
- **Oran ≠ oy yüzdesi.** Oran, ağırlıklı pay ile kişi payının **küçüğüdür** ve paydasında çekimserler de vardır.
- **Ezici üstünlük ≠ tek kalan.** %75 alan hemen kazanır. %75'i alamayan ama elemeden sonra tek kalan fikir de kazanır (ör. %65 ve yedi tane %5 altı fikir).
- **Elenmek ≠ gizlenmek.** Elenen fikir sayfada üstü çizili durur ve altında tartışılmaya devam edilir; yalnızca sonraki turda oylanmaz.
- **Gizlemek ≠ silmek.** Gizlenen mesaj veritabanında durur, yerinde not kalır, defterdeki özeti değişmez. Silme diye bir işlem yoktur.
- **Sonuçsuz ≠ kaldırılmış.** Sonuçsuz konu karar çıkmadan kapanmıştır, okunabilir. Kaldırılan konu 3/4 oyla gizlenmiştir; yerinde iz kalır.
- **İtiraz konusu ≠ kararın iptali.** İtiraz konusu yeni bir tartışmadır; eski karar arşivde durur. İtirazdan yeni bir karar çıkarsa ikisi de görünür.
- **Yönetici ≠ uzman.** Yönetici siteyi yönetir ama oyu 1'dir ve kararlara karışamaz. Uzmanın oyu kendi alanında 10'dur ama paneli göremez. Yönetici uzman atayamaz.
- **Yeter sayı ≠ eşik.** Yeter sayı "yeterince kişi oy verdi mi?", eşik "verilenlerin yeterince çoğu bunu mu istedi?" sorusudur. İkisi de sağlanmalı.
- **Çekimser** yeter sayıya katkı yapar **ve** oranları düşürür.
- **Şikayet ≠ gizleme oylaması.** Şikayet, 3 kişi olunca yöneticiye gider; gizleme oylaması doğrudan üyelere. Yönetici şikayeti oylamaya alabilir, ama kendisi gizleyemez.
- **Günlük ≠ defter.** Günlük okunabilir liste; defter kurcalanamaz zincir. Aynı olayları farklı amaçla tutarlar.
- **Sunum kipi ≠ yönetici yetkisi.** `--demo` sunucuyu başlatan kişinin açtığı bir kolaylıktır; normal çalışmada yönetici süreye dokunamaz.
