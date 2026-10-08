# Agora — Problem Çerçeveleme ve Gereksinim Analizi

Bu belge, Agora'yı ders slaytlarındaki yöntemle analiz eder: önce "hangi problemi çözüyoruz?", sonra "YZ gerekli mi?",
sonra metrikler, temel çizgi (baseline), kısıtlar, paydaşlar ve ön-otopsi. Atıflar:
**H2** = Hafta 2 *Problem Çerçeveleme* slaytları, **S01** = *YZ Mühendisliğine Giriş*, **S02** = *Temel Modelleri Anlamak*,
**TD** = *Yazılım Tasarım Desenleri* (numaralar slayt numarasıdır).

Belgedeki başarım sayıları (kesinlik, duyarlılık, gecikme, ürün metrikleri) `olcum/` klasöründeki betiklerle **ölçülmüştür**;
tahmin değildir. Sayıların nasıl yeniden üretileceği ilgili bölümlerde yazar. Hedef değerler ve hata maliyeti birimleri (5.3)
ise varsayımdır; paydaşlarla belirlenmelidir.

| Betik | Ne ölçer |
|---|---|
| `python olcum/denetim_olcumu.py` | Denetim kurallarının (D1, D2, D3) etiketli örneklerde kesinlik, duyarlılık, F1; aptal temel çizgilerle karşılaştırma |
| `python olcum/gecikme_olcumu.py [n] [--defter-blok N]` | Sayfaların p50 / p95 / en kötü yanıt süresi; defter büyüyünce ne olduğu |
| `python olcum/urun_metrikleri.py [veritabanı]` | İş, ürün ve koruyucu metrikler (5. bölüm) |

---

## 1. Isınma: "Bir forum yapın" cümlesinin arkasındaki problemler

H2-5'teki belediye örneğinde olduğu gibi, ödev cümlesi ("herkesin konu açtığı, çoğunlukla karar alınan bir forum")
birden fazla problemi saklıyor. İlk iş, hangisinin gerçekten problem olduğunu ve hangisinin YZ ile ilgili olduğunu ayırmak:

| Gözlenen dert | Asıl problem | Çözüm türü | Agora'daki karşılığı |
|---|---|---|---|
| Kararları hep aynı birkaç sesli kişi veriyor | Söz ve oy eşitsizliği | **Süreç / kural** (YZ değil) | Kişi başı bir fikir, çift oran (ağırlıklı pay ile kişi payının küçüğü), devir tavanı |
| Tartışmalar uzuyor, sonuç çıkmıyor | Karar sürecinin sonu yok | **Süreç** (YZ değil) | Süreli tartışma + en fazla 5 tur eleme; yeter sayı; "sonuçsuz" durumu |
| Çıkan karara güvenilmiyor ("sonradan değiştirildi") | Denetlenebilirlik yok | **Kayıt / kriptografi** (YZ değil) | Hash zinciri, 3 düğüm, oy makbuzu, tutarlılık denetimi |
| Uzun tartışmayı kimse okumadan oy veriyor | Bilgi yükü | **Özetleme** — YZ adayı | Yapay zeka üyenin tartışma ve tur özetleri |
| Hakaret, kişisel veri, yanlış kategoride konu | İçerik denetimi | **Metin sınıflandırma** — YZ adayı | Yönetmelik denetimi D1–D7 |
| Aynı konu tekrar tekrar açılıyor | Tekrar | **Benzerlik** — YZ adayı | D5 benzer konu uyarısı |

**Sonuç:** Altı dertten üçü YZ ile hiç ilgili değil ve ürünün çekirdeği (oylama, sayım, defter) tamamen kurala dayalı.
YZ yalnızca üç *destek* işinde aday. Bu ayrım bütün belgenin omurgası: **kararı model değil, insanlar verir** (H2-17).

---

## 2. Çerçeveleme hunisi ve çerçeveleme tablosu

**Ürün düzeyinde huni (H2-16):**

| Basamak | Agora |
|---|---|
| İş hedefi | Bir topluluğun (okul, mahalle, kulüp) ortak sorunlarına **adil, şeffaf ve zamanında** karar üretmesi |
| İş sorusu | Neden karar çıkmıyor ya da çıkan karara güvenilmiyor? → birkaç kişinin baskınlığı, süresiz tartışma, denetlenemeyen sayım |
| Karar | Bu konuda hangi fikir topluluğun kararı olacak? |
| Kim karar verir | **Üyeler, oyla.** Model yok; sayım kuralı yönetmelikte yazılı ve herkesçe okunabilir |
| YZ'nin yeri | Kararı *hazırlayan* adımlar: okunmamış tartışmayı özetlemek, uygunsuz içeriği önce yazana göstermek |
| Tahmin (destek işlerinde) | Bu metin bir kişiyi aşağılıyor mu (D1), kişisel veri içeriyor mu (D2), hangi alana ait (D3)? |
| ML görevi | D1, D2 ikili sınıflandırma; D3 7 sınıflı sınıflandırma. Bugün kural tabanlı ve ölçülüyor (6. bölüm) |
| Veri ve etiket | Etiketli forum verisi yok; ölçüm için yazılıp etiketlenmiş 166 örnek (6.2). Gelecekte etiket kaynağı: gizleme oylamaları, şikayetler |

**Bileşen düzeyinde çerçeveleme tablosu (H2-18, H2-23).** Her satır bir kararla başlıyor; karar sütunu boş olan bileşen yok.

| Bileşen | Karar | Görev türü | Girdi → çıktı | Kararı kim verir |
|---|---|---|---|---|
| Fikir oylaması (`oylama.py`, `sonuclar.py`) | Hangi fikir kazanır | ML değil: sayım kuralı | Oylar → kabul / sonraki tur / sonuçsuz | Üyeler |
| D1 Saygılı dil (`denetim.py`) | Metin yayımlansın mı | İkili sınıflandırma | Metin → kaba ifade VAR/YOK | Kural uyarır (6.5'ten beri); yazan karar verir; kaçanı topluluk gizler |
| D2 Kişisel veri | Metin yayımlansın mı | İkili sınıflandırma (desen tanıma) | Metin → kişisel veri VAR/YOK | Kural engeller |
| D3 Kategoriye uygunluk | Konu doğru alanda mı | Çok sınıflı sınıflandırma (7 ana alan) | Başlık + açıklama → kategori | Konu sahibi (yalnızca uyarı) |
| D5 Benzer konu | Aynı konu zaten açılmış mı (sonuçsuz kapananlar hariç) | Benzerlik / sıralama | Başlık → en benzer konu ve oranı | Konu sahibi (uyarı) |
| Yapay zeka özeti (`yz.py`) | Okumadan oy verene ne gösterilir | Üretim (generation) | Mesajlar + sayım → kısa metin | Okur; özet oy vermez |
| Görüş grupları (`graf.py`) | — (yalnızca görselleştirme) | Kümeleme (etiket yayılımı) | Etkileşim grafı → gruplar | Kimse; karar yok |

**YZ'nin üründeki rolü (S01-31):** *tamamlayıcı* (Agora YZ olmadan da çalışır: özet yoksa forum işler, denetim kapatılabilir),
*tepkisel* (denetim, yazana anında yanıt verir → gecikme önemli) ve *öngörülü* (tur özeti tur bitince kendiliğinden yazılır →
kalite çıtası yüksek, gereksiz özet tartışmayı kirletir; bu yüzden yeni mesaj yoksa yeni özet yazılmaz), *statik*
(kurallar herkese aynı; topluluk oylamayla değiştirir).

---

## 3. YZ gerekli mi? (H2-7, H2-8, H2-9)

H2-7'deki beş koşul (öğrenilecek örüntü, kural yazmanın zorluğu, mevcut veri, cevabın tahmin olarak ifade edilebilmesi,
gelecek verinin geçmişe benzemesi), aynı slayttaki "ML daha da parlar" ölçütlerinden ikisi (hatanın ucuz olması, örüntünün
değişmesi) ve H2-9'daki karar ağacı her bileşen için ayrı ayrı uygulandı. ✓ sağlanıyor, ✗ sağlanmıyor.

| Bileşen | Örüntü | Kural zor | Veri var | Tahmin olarak ifade | Yeni veri benzer | *Hata ucuz* | *Örüntü değişir* | Karar ağacının sonucu |
|---|---|---|---|---|---|---|---|---|
| Sayım ve eleme | ✗ (kural yönetmelikte) | ✗ | — | ✗ (sonuç hesaplanır, tahmin edilmez) | — | ✗ (kararı belirler) | ✗ | **Kural yazın.** H2-12'deki "harf notu" durumu: model, bilinen kuralın bozuk kopyası olur. Açıklama yasal/etik zorunluluk (H2-8). |
| D1 kaba ifade | ✓ | kısmen | ✗ (etiketli forum mesajı yok) | ✓ (VAR/YOK) | kısmen (argo değişir) | kısmen | ✓ | **Önce veri toplayın** → bugün kural; topluluğun gizleme oylamaları ve şikayetler etiket olarak birikir (H2-13: insan kararı = yeni etiket). |
| D2 kişisel veri | kısmen | ✗ (biçimler belli: telefon, e-posta, kimlik no, IBAN) | ✗ | ✓ | ✓ | ✗ (KVKK) | ✗ | **Kural yazın.** Adres gibi serbest biçimler kuralla yakalanmıyor (6. bölüm); ileride ad-varlık tanıma (NER) modeli adayı. |
| D3 kategori | ✓ | kısmen | ✗ | ✓ (7 sınıftan biri) | kısmen (yeni kategoriler) | ✓ (yalnızca uyarı) | ✓ | **Kural (ontoloji)**; yeni kategoriler topluluk tarafından *kavramlarıyla* eklendiği için kural kendiliğinden uyarlanır. |
| YZ özeti — sayılar | ✗ | ✗ | — | ✗ (sayılar hesaplanır) | — | ✗ (oyu etkiler) | ✗ | **Kural yazın.** Kim kaç mesaj yazdı, fikir yüzde kaç aldı: veritabanında hazır. |
| YZ özeti — içerik | ✓ | ✓ | ✓ (mesajlar) | üretim (H2-18 notu) | ✓ | ✗ | ✓ | **İnsan onaylı ML** (H2-9 en sağ alt dal). Bugün uygulanmadı; aşağıda tasarımı var. |

**Neden büyük dil modeli (BDM / LLM) ile özet yazılmadı?** H2-10'daki yelpazenin solundan başlandı; sağa geçmeyi
gerektiren ölçülmüş bir eksik yok. Ayrıca dört somut engel var:

1. **Halüsinasyon (S02-43, 44):** BDM "%74,5" yerine "%75" yazabilir ya da bir fikri "elendi" diye özetleyebilir. Agora'da
   özet oy vermeden önce okunur; yanlış sayı kararı etkiler. Bu yüzden `yz.py`'deki her sayı veritabanından gelir, oranlar
   **yuvarlanmaz, kesilir** (`metin.yuzde`: %74,9 asla "%75" olmaz), her fikrin durumu turun kaydedilmiş kararından okunur
   (`sonuclar.TurKarari`). Testler: `YapayZekaOzetleri`, `TurKarariAnlikGoruntusu`.
2. **Veri dışarı çıkamaz (H2-45, KVKK):** Mesajları bir dış API'ye göndermek, kişisel verinin üçüncü tarafa aktarılması demek.
3. **Maliyet ve gecikme (S01-34, 35; H2-10):** Çağrı başına ücret ve saniyeler süren yanıt; kural tabanlı özet milisaniyeler sürer, ücretsiz.
4. **Olasılıksal çıktı (S02-41, 42):** Aynı tartışma iki kez özetlenince farklı metin çıkabilir; denetlenebilirlik ilkesiyle çelişir.
   Güncel modellerde `temperature=0` ile sabitleme de artık mümkün değil: Anthropic'in yeni modelleri sıcaklık parametresini
   reddediyor (`laboratuvar/` 3. görev). Kural tabanlı özet ise belirlenimcidir (test: `Belirlenimcilik`).
5. **Türkçe daha pahalı (S02-4…6):** Aynı anlam Türkçede İngilizceden 1,36–1,69 kat daha çok token tutuyor (`laboratuvar/`
   1. görev); maliyet, gecikme ve bağlam kullanımı aynı oranda artar.

Bu karar S01-19'un ölçütüne de uyar: ML, öğrenilecek karmaşık bir örüntü olduğunda anlamlıdır. Sayılar ve sayım kuralı için
öğrenilecek bir şey yok, kural zaten biliniyor.

**İleride BDM eklenecekse önerilen tasarım (insan döngüde, S01-32 "emekle–yürü–koş"):**
- *Emekle:* BDM yalnızca içerik özetinin **taslağını** yazar; sayılar kural tabanlı özetten gelir ve BDM'ye "bu sayıları aynen kullan"
  diye verilir. Çıktı yapılandırılmıştır (S02-38: JSON şema — fikir no, öne çıkan argümanlar), serbest metin değildir.
- Son işleme (S02-40): çıktıdaki her sayı veritabanındaki sayıyla karşılaştırılır; bir tanesi bile uymazsa özet atılır, kural
  tabanlı özet yazılır (**sayı sadakati** koruyucu metriği, 5. bölüm).
- Özet, katılımcılardan biri onaylamadan yayımlanmaz. Onaylanan/düzeltilen özetler etiketli veri olur (veri çarkı, S01-33).
- *Yürü*'ye geçiş ölçütü: onaylayanların taslağı değiştirmeden kabul oranı ≥ %95 (eşik S01-32'den; ölçümün en az 4 hafta
  sürmesi bu belgenin eklemesi, mevsimsel konu farklarını görmek için).
- Aynı ilke bugün denetimde uygulandı: ölçülen güveni yetmeyen D1 "engelle" (koş) yerine "uyar" (emekle) düzeyine çekildi (6.5).

---

## 4. Tek sayfalık problem tanım kanvası (H2-48, H2-49)

**Tek cümlelik problem tanımı (H2-50: kullanıcı, karar, görev, metrik, temel çizgi).** Denetim için:

> Forumda konu ya da mesaj yazan üye, metninin bir kişiyi aşağılayıp aşağılamadığını (D1) ve kişisel veri içerip
> içermediğini (D2) göndermeden önce görüp düzeltsin diye her metin ikili sınıflandırılır; başarı, kurallar dondurulduktan
> sonra yazılmış, hiç görülmemiş bir kümede D1 kesinliği ve F1'inin ≥ 0,80, D2 duyarlılığının ≥ 0,80 olmasıdır; temel
> çizgiler "hep temiz" (F1 = 0) ve rastgele tahmindir (F1 ≈ 0,50); bir model ancak bugünkü kuralı (son küme D1 F1 0,71,
> D2 duyarlılık 0,83) aynı türden bir kümede en az +0,10 F1 farkla geçerse onun yerine geçer.

Aynı problemin kötü tanımı (H2-50'deki karşı örnek gibi) şu olurdu: "Yapay zekâ ile forumdaki uygunsuz içeriği yüksek
doğrulukla engelleyen bir sistem." Kim kullanacak, "uygunsuz" nasıl etiketlenecek, "yüksek doğruluk" kaç, belli değil;
üstelik çözüm (YZ) problemden önce seçilmiş.

| Kutu | Agora |
|---|---|
| **1. İş hedefi ve değer** | Topluluk kararlarının adil (azınlık korunur, tek kişi baskın olmaz), şeffaf (sayım ve kayıt herkesçe denetlenir) ve zamanında (en fazla 7 gün: 24 saat tartışma + 48 saatlik 1. tur + 4 × 24 saatlik tur) alınması. İş metriği: kapanan konuların karara bağlanma oranı. |
| **2. Karar ve eylem** | Kararı üyeler oyla verir. Sistem, kararı *hazırlar*: içerik denetimi yazana anında geri bildirim verir (günde mesaj sayısı kadar; kişisel veri engellenir, hakaret için uyarılır), özet her tur sonunda bir kez yazılır. |
| **3. ML görevi** | Çekirdekte yok. Destek görevleri: D1/D2 ikili sınıflandırma, D3 7 sınıflı sınıflandırma, D5 benzerlik, özet = üretim. Etiket tanımları: 6.2. |
| **4. Veri** | Etiketli veri yok (yeni ürün). Ölçüm için yazılıp etiketlenmiş 166 örnek (geliştirme 85, test 43, görülmemiş son küme 38); gerçek forum mesajı değildir (6.2). Gelecekte etiket kaynağı: topluluğun gizleme oylamaları, şikayetler, kategori değişiklikleri. Kişisel veri: ad soyad, doğum tarihi, adres yalnızca kayıtta; görünen takma ad; deftere yalnızca özet ve taahhüt. |
| **5. Metrikler** | Model: D1 kesinlik (yanlış engel pahalı), D2 duyarlılık (kaçan kişisel veri pahalı), D3 makro F1. Ürün: katılım oranı, karar süresi. Koruyucu: oy gücü Gini, defter tutarsızlığı = 0, YZ sayı sadakati = %100, p95 gecikme. (5. bölüm) |
| **6. Baseline** | Çoğunluk sınıfı: D1/D2 F1 0, D3 makro F1 0,04. Rastgele (beklenen): F1 ≈ 0,50, D3 makro F1 ≈ 0,13. Bugünkü kural, son kümede: D1 F1 0,71, D2 duyarlılık 0,83, D3 makro F1 0,49. Mevcut çözüm = insan (topluluğun gizleme oylaması): ölçülmedi. (6. bölüm) |
| **7. Kısıtlar** | Dönem ödevi süresi; sunucu bütçesi yok, GPU yok, dış API yok; tek bilgisayarda SQLite; p95 < 200 ms; KVKK; gizli oy; kararlar açıklanabilir olmalı. (7. bölüm) |
| **8. Riskler ve başarı** | En büyük risk "kimse oy vermez, turlar sonuçsuz kalır" (O × E = 9; ön-otopsi, 10. bölüm). Yayın ölçütü (11. bölüm): son kümede D2 sağlandı; D1 sağlanmadı, varsayılanı "Uyarır" yapıldı; D3 zaten yalnızca uyarır. |

---

## 5. Başarı metrikleri

### 5.1 Üç katman (H2-25)

`python olcum/urun_metrikleri.py` her metrik için bir sayı üretir. Aşağıdaki "demo" sütunu demo verisinden hesaplandı; demo
verisi elle kurulmuş bir senaryo olduğu için bu sütun **metriğin çalıştığını** gösterir, forumun başarısını değil.

| Katman | Metrik | Neden bu | Hedef | Demo |
|---|---|---|---|---|
| İş | Karara bağlanma oranı (kapanan konular) | Asıl amaç: tartışma karara dönüşüyor mu | ≥ 0,60 | 0,75 |
| İş | İtiraz konusu açılan kararların oranı | Karara güven / kabul (düşük iyi) | ≤ 0,20 | 0,33 |
| Ürün | Açılıştan karara medyan süre | "Zamanında" | ≤ 120 saat | 96 saat |
| Ürün | Fikir oylamalarında ortalama katılım (katılan / hak sahibi) | Karar kaç kişinin sesi | ≥ 0,40 | 0,89 |
| Ürün | Yeter sayıya ulaşamayan tur oranı | Sonuçsuz kalmanın en sık nedeni | ≤ 0,20 | 0,10 |
| Ürün | Fikir başına yanıt (argüman, karşı argüman, soru, kaynak) | Tartışmanın derinliği (akran öğrenmesi) | ≥ 2 | 2,58 |
| Koruyucu | Oy gücü Gini katsayısı (0 = eşit) | Devirle güç yoğunlaşması | < 0,40 | 0,12 |
| Koruyucu | En güçlü üyenin oy gücü payı | Tek kişinin baskınlığı | < 0,20 | 0,13 |
| Koruyucu | Defter–veritabanı tutarsızlığı | Kayıtların kurcalanmadığı | **0** | 0 |
| Koruyucu | Yapay zeka mesajlarının payı | YZ tartışmayı doldurmasın | < 0,15 | 0,13 |
| Koruyucu | Gizlenen mesaj oranı | Gizleme oylamasının sansür aracına dönmesi | < 0,05 | 0,00 |
| Koruyucu | YZ özetinde sayı sadakati | Özetteki her sayı veritabanındakiyle aynı | **%100** | test ile güvence |
| Koruyucu | p95 gecikme | Kullanılabilirlik | < 200 ms | 5. ve 8. bölüm |

**Kopukluk tehlikesi (H2-25):** Katılım oranı artarken karara bağlanma oranı düşüyorsa darboğaz katılım değil, fikir sayısıdır
(çok fikir → yeter sayıya ulaşsa da eşiği kimse geçemez). İki metrik birlikte izlenir.

**Model metriğinden iş metriğine (H2-25, S01-20).** D1'in kesinliği düşükse meşru mesajlar durdurulur → yazan vazgeçer →
fikir başına yanıt ve katılım düşer (ürün) → daha az konu karara bağlanır (iş). D2'nin duyarlılığı düşükse kişisel veri
yayımlanır → KVKK ihlali ve güven kaybı (koruyucu). Bu zincir bugün yalnızca mantıkla kuruldu; gerçek kullanımda A/B
deneyiyle ölçülmelidir (S01-20).

### 5.2 Goodhart yasası (H2-35): metriği hedef yapınca ne bozulur?

| Hedef yapılırsa | Nasıl bozulur | Agora'daki önlem |
|---|---|---|
| "Trend konu" puanı | Tek kişi art arda yazıp konusunu gündeme taşır | Puanda kişi başı en çok 3 mesaj sayılır (`gundem.KISI_BASI_MESAJ`) |
| Katılım oranı | Oy vermeyene ısrarlı bildirim → bildirim yorgunluğu | Bildirim yalnızca olay olunca; koruyucu: bildirim kapatma oranı (izlenecek) |
| Karara bağlanma oranı | Eşikleri düşürerek "karar" üretmek | Eşikler yönetmelikte, korunan maddeler 3/4 ister; parametre aralıkları sınırlı (`ayarlar.PARAMETRE_ARALIKLARI`) |
| Özet sayısı | YZ her mesajda özet yazar, tartışmayı doldurur | Son özetten beri yeni mesaj yoksa özet yazılmaz (`yz.ozet_iste`); koruyucu: YZ mesajı payı |

### 5.3 Model metrikleri ve hata maliyeti (H2-26…31)

Denetim kurallarının bir olasılık eşiği yok; ama **ciddiyet** (Engeller / Uyarır / Kapalı) aynı işi görür ve H2-29'daki
"eşik bir iş kararıdır" ilkesine uygun olarak **topluluk oylamasıyla** ayarlanır (yönetmelik değişikliği).

- **D1 (kaba ifade; başta ENGEL, 6.5'teki karardan sonra UYARI):** Engellerken yanlış pozitif (YP) meşru bir mesajı durdurur,
  yazan düzeltmek zorunda kalır; yanlış negatif (YN) hakaretin yayımlanması demek ama topluluk şikayet ve gizleme oylamasıyla
  düzeltebilir. **YP daha pahalı → kesinlik öncelikli** (F0,5; son kümede 0,71). Örnek maliyet (H2-31 yöntemi; birimler
  varsayım, paydaşlarla belirlenmeli): engelleyen kuralda YP = 5, YN = 1 alınırsa son kümede kural 5·2 + 1·2 = **12**,
  "hep temiz" 1·7 = **7** birim. Bu maliyetlerle engelleyen kural, hiç kural olmamasından pahalıdır. Uyarıda yanlış pozitifin
  bedeli çok küçüktür (yazan uyarıyı okuyup geçer); 6.5'teki karar bu hesapla da desteklenir.
- **D2 (kişisel veri), ENGEL:** YN kişisel verinin herkese açılması (KVKK); YP yalnızca bir yeniden yazma. **YN çok daha pahalı →
  duyarlılık öncelikli** (F2; son kümede 0,86). YN = 50, YP = 1 alınırsa test kümesinde kural 50·1 + 1·1 = **51**, "hep temiz"
  50·5 = **250**; son kümede kural 50·1 + 1·0 = **50**, "hep temiz" 50·6 = **300** birim.
- **D3 (kategori), UYARI:** Hata yalnızca bir uyarı; 7 sınıfın hepsi eşit önemde → **makro F1** (H2-30).

### 5.4 Çok boyutlu değerlendirme (H2-34)

| Boyut | Gereksinim | Durum |
|---|---|---|
| Gecikme | p95 < 200 ms (sunucu tarafı) | Ölçüldü: en yavaş sayfa p95 15,5 ms (demo), 1.000 konuda konu akışı p95 51,5 ms (8. bölüm) |
| Maliyet | İstek başına dış servis ücreti 0 | Dış API yok |
| Açıklanabilirlik | Her engel/uyarı nedenini söyler; her sayım tablosu herkese açık | Denetim raporu madde madde gerekçe yazar; oylama sayfası sayım tablosunu gösterir |
| Mahremiyet | Kişisel veri modele/dışarıya gitmez | Kural tabanlı, yerel; deftere yalnızca özet |
| Adalet | Azınlık korunur; konumdan bağımsız eşit kural | Çift oran, kişi başı bir fikir, devir tavanı, uzman kontenjanı; koruyucu Gini |

---

## 6. Temel çizgi (baseline) ve hata analizi

### 6.1 Merdiven (H2-38)

| Basamak | Agora'da | Durum |
|---|---|---|
| Rastgele | Sınıflardan birini eşit olasılıkla seç; 1000 tohumun ortalaması verilir (beklenen değer) | Ölçüldü |
| Çoğunluk sınıfı | D1/D2: "hep temiz" (hiçbir şeyi engelleme), D3: "hep en sık kategori" | Ölçüldü |
| Basit kural | Anahtar kelime (D1), düzenli ifade + T.C. kimlik sağlaması (D2), ontoloji kavramları (D3) | **Bugünkü sistem**, ölçüldü |
| Mevcut çözüm | İnsan: topluluğun şikayet ve gizleme oylaması | Ölçülmedi (gerçek kullanım verisi yok) |
| Basit ML | TF-IDF + lojistik regresyon | Yapılmadı: etiketli veri yok (H2-9 "önce veri toplayın") |
| Karmaşık model | İnce ayarlı BERT / BDM | Yapılmadı (3. bölüm) |

### 6.2 Ölçüm düzeneği

- **Veri özeti (H2-53).** Örnekler gerçek forum mesajı değildir. Üç kümeyi bir YZ kodlama asistanı yazıp
  etiketledi (YZ kullanım beyanı, README); etiketler kurallar çalıştırılmadan **önce** yazıldı. Kuralları ve örnekleri aynı
  yazar yazdığı için son küme bile yazarın dil alışkanlıklarını taşır; gerçek kullanıcı mesajlarındaki başarım
  daha düşük olabilir. Örnekler küçük; sonuçlar kesin başarım değil, bir referans noktasıdır.

  | Küme | D1 örnek (VAR / YOK) | D2 örnek (VAR / YOK) | D3 örnek (7 sınıfın her biri) | Medyan uzunluk D1 / D2 / D3 (karakter) |
  |---|---|---|---|---|
  | `gelistirme.csv` | 28 (14 / 14) | 22 (10 / 12) | 35 (5) | 38 / 42 / 56 |
  | `test.csv` | 12 (6 / 6) | 10 (5 / 5) | 21 (3) | 37 / 35 / 53 |
  | `son_test.csv` | 13 (7 / 6) | 11 (6 / 5) | 14 (2) | 39 / 38 / 57 |

  Kümeler dengelidir; gerçek bir forumda hakaret ve kişisel veri çok daha seyrektir (6.3, yorum).
- **Etiket tanımları:** D1 VAR = metin bir *kişiyi* aşağılayan ya da ona hakaret eden bir ifade içeriyor (fikre yönelik sert eleştiri
  VAR değildir). D2 VAR = metinde belirli bir kişiye ulaşmayı ya da onu tanımlamayı sağlayan bilgi var (telefon, e-posta, T.C. kimlik
  no, IBAN, açık adres); kurum santrali, ders kodu, sipariş/ürün numarası YOK'tur. D3 = metnin asıl konusu olan ana alan (7 ana kategoriden biri).
- **Test kümesi kutsaldır (H2-55):** Test kümesi kurallar değiştirilmeden önce yazıldı ve iyileştirmeden önce ölçüldü; kurallardaki
  düzeltmeler geliştirme kümesindeki hatalardan çıkarıldı. **Dürüstlük notu:** (1) iyileştirmeden önceki test ölçümünün hata listesi
  ekrana yazdırıldığı için test kümesindeki hatalar düzeltmeler yapılırken görülmüştü; ünsüz yumuşaması düzeltmesi geliştirme
  kümesindeki "ahmağın" örneğinden çıktı ama test kümesindeki "salağa", "dangalağın" örneklerini de düzeltiyor. (2) Yeni D3 kodundaki
  bir hata (aynı kavramın iki alt kategoride iki kez sayılması) test kümesindeki bir örnekte fark edilip düzeltildi. (3) Test kümesi
  ile düzeltmeler aynı commit'te olduğu için sıralama git geçmişinden doğrulanamaz. Bu yüzden test kümesindeki artış **iyimserdir**;
  dürüst bir sonraki adım, kurallar artık değişmeyecekken yeni ve hiç görülmemiş bir test kümesi yazıp bir kez ölçmektir
  (6.5'te yapıldı).
  6.4'teki "bilerek düzeltilmeyen" tablosunda test kümesinden gelen örnekler yalnızca belgelendi, kurallara yansıtılmadı.
- Ölçüm koda bağlandı: `testler/test_olcum.py`, kuralların temel çizgileri geçtiğini ve test kümesinde 11. bölümdeki yayın
  ölçütlerinin altına düşülmediğini her test çalıştırmasında denetler (koruyucu).

### 6.3 Sonuçlar — test kümesi (`python olcum/denetim_olcumu.py`)

DP / YP / YN / DN: doğru pozitif, yanlış pozitif, yanlış negatif, doğru negatif (ikili karışıklık matrisinin dört hücresi).
Rastgele satırının sayıları 1000 tohumun ortalaması olduğu için kesirlidir.

| Madde | Yöntem | DP | YP | YN | DN | Kesinlik | Duyarlılık | F1 | Doğruluk |
|---|---|---|---|---|---|---|---|---|---|
| D1 kaba ifade (12 örnek, 6 VAR) | Çoğunluk sınıfı | 0 | 0 | 6 | 6 | 0,00 | 0,00 | 0,00 | 0,50 |
| | Rastgele (beklenen) | 2,9 | 3,0 | 3,1 | 3,0 | 0,49 | 0,49 | 0,48 | 0,49 |
| | Kural — iyileştirmeden önce | 3 | 1 | 3 | 5 | 0,75 | 0,50 | 0,60 | 0,67 |
| | **Kural — şimdi** | 5 | 1 | 1 | 5 | **0,83** | **0,83** | **0,83** | **0,83** |
| D2 kişisel veri (10 örnek, 5 VAR) | Çoğunluk sınıfı | 0 | 0 | 5 | 5 | 0,00 | 0,00 | 0,00 | 0,50 |
| | Rastgele (beklenen) | 2,5 | 2,5 | 2,5 | 2,5 | 0,50 | 0,49 | 0,48 | 0,50 |
| | **Kural** (önce ve şimdi aynı) | 4 | 1 | 1 | 4 | **0,80** | **0,80** | **0,80** | **0,80** |

| Madde | Yöntem | Doğruluk | Makro F1 |
|---|---|---|---|
| D3 kategori (21 örnek, 7 sınıf) | Çoğunluk sınıfı | 0,14 | 0,04 |
| | Rastgele (beklenen) | 0,15 | 0,13 |
| | Kural — iyileştirmeden önce | 0,81 | 0,83 |
| | **Kural — şimdi** | **0,86** | **0,87** |

Geliştirme kümesinde (iyimser, çünkü iyileştirmeler bu kümeye bakılarak yapıldı): D1 F1 0,74 → 0,79; D2 F1 0,82 → 0,95;
D3 doğruluk 0,86 → 0,89.

**Yorum.** Dengeli (yarısı VAR) bir kümede rastgele tahminin beklenen kesinliği VAR oranına (~0,5), beklenen duyarlılığı 0,5'e
eşittir; F1'i ≈ 0,48–0,50. (Tek bir tohumla çekilen rastgele tahmin 10–20 örnekte
F1 0,62–0,73 verebilir; bu şanstır, beklenen değer değildir.) Gerçek forumda mesajların çok büyük kısmı temizdir (dengesiz sınıf,
H2-27): VAR oranı %2 ise rastgelenin kesinliği 0,02'ye, F1'i ≈ 0,04'e düşer; "hep temiz" temel çizgisi %98 doğruluk alır ama
tek hakareti yakalamaz. Bu yüzden doğruluk değil, kesinlik ve duyarlılık raporlanır. `testler/test_olcum.py`, kuralın her
kümede iki temel çizgiyi de en az +0,10 F1 farkla geçtiğini denetler.

### 6.4 Hata analizi (H2-56) ve ondan çıkan iyileştirmeler

Kuralın yanıldığı örnekler tek tek okundu. Belirli cümleleri ezberleyen değil, **dil kuralına** dayanan düzeltmeler yapıldı:

| Örnek | Neden yanıldı | Düzeltme |
|---|---|---|
| "Sen ahmağın tekisin." → kaçtı | Türkçe **ünsüz yumuşaması**: *ahmak* ek alınca *ahmağ-* olur; kök listede yok | Her kökün yumuşamış biçimi de aranır (`denetim._yumusamis`). H2-41'deki "Türkçe tuzağı"nın (İ/I) kardeşi; İ/I zaten `ontoloji.tr_kucuk` ile çözülüydü. |
| "IBAN numaram TR33 0006 …" → kaçtı | IBAN deseni yoktu | IBAN deseni eklendi (KVKK kapsamında kişisel veri) |
| "Telefonum 0 (532) 123-45-67." → kaçtı | Parantezli yazım | Desen parantezi kabul ediyor |
| "Belediye meclis toplantıları internetten **canlı** yayınlansın." → Bilim | Her alt kategori tek başına yarışıyordu: Siyaset (meclis) ve Yerel Yönetim (belediye) birer eşleşmeyle Biyoloji'ye (canlı) eşit kaldı, kazananı sözlük sırası belirledi | Eşleşmeler önce **ana alan** düzeyinde toplanıyor (`ontoloji.alan_puanlari`). Tam eşitlikte (aynı sayıda kavram, aynı sayıda alt kategori eşleşmesi) kazananı hâlâ kategori sırası belirler; D3 yalnızca uyarı olduğu için kabul edildi |

Sonradan bulunan ve düzeltilenler (ölçüm kümelerinde örneği yoktu; ölçüm sonucu değişmedi):

| Durum | Düzeltme |
|---|---|
| "**Asalak** bitkiler üzerine seminer" → yanlış engel ("salak" kelimenin içinde) | Kökler kelime başında aranıyor (Türkçe sondan eklemeli) |
| "Kitap barkodu 8695012345678" → telefon sanılıyordu | Telefon deseni rakam sınırında başlayıp bitiyor |
| 40.000 karakterlik bir gerekçe ~7 sn sürüyordu (e-posta deseni karesel) | Desen kelime sınırında başlıyor; serbest metinlere 5.000 karakter sınırı |

Bilerek düzeltilmeyen hatalar (kuralın sınırı; düzeltmek ezberlemek olurdu). Test kümesinden gelenler ("mal mısın", ürün kodu,
"Aptallık", "Öğrencilere ücretsiz terapi"…) yalnızca belgelendi:

| Örnek | Neden | Ne yapılmalı |
|---|---|---|
| "Cahiliye dönemi şiiri…", "Aptallar Gemisi adlı kitap…", "Ahmak ıslatan yağmur" → yanlış engel | Kök, masum bir kelimenin ya da deyimin içinde | Ciddiyet UYARI'ya çekilebilir; uzun vadede bağlamı anlayan model (H2-9: veri toplandıkça) |
| "s.a.l.a.k", "öküz", "kafasız", "mal mısın" → kaçtı | Gizleme ve listede olmayan argo | Topluluğun gizleme oylamaları etiket olarak birikir. Liste bugün kodda sabit (`denetim.KABA_IFADELER`); yönetmelik verisine taşınırsa oylamayla güncellenebilir (8.4) |
| "Ev adresim Bağdat Caddesi No: 12…" → kaçtı | Adres serbest biçimli | NER modeli adayı; bugün şikayet + gizleme |
| "Ürün kodu 11111111110" → yanlış engel | 11 haneli rastgele bir sayı %1 olasılıkla T.C. kimlik sağlamasını tutar | Kabul edilen bedel (YN çok daha pahalı) |
| "Öğrencilere burs başvurusu…" → Eğitim | "öğrenci" kelimesi Eğitim'in iki kavramına (ogren, ogrenci) birden uyuyor | Ontoloji verisinde kavram tekrarı temizlenmeli |
| "Satranç **kulübü** için oda ayrılsın" → kavram eşleşmez | Ünsüz yumuşaması (kulüp → kulübü) ontoloji eşleşmesinde de var; ama D1'deki gibi her kökü yumuşatmak "kent" → "kend" gibi sık kelimelerle (kendi) yanlış eşleşme üretir | Yumuşayan kavramlar ontolojide tek tek, yumuşamış biçimleriyle yazılmalı |

### 6.5 Son ölçüm: hiç görülmemiş küme (kurallar donduruldu)

6.2'deki dürüstlük notunun önerdiği adım uygulandı. Kurallar donduktan sonra `olcum/son_test.csv` (D1: 13, D2: 11, D3: 14
örnek) yazıldı ve **ölçülmeden önce commit edildi** (`dfa996e`). Sıralama git geçmişinden doğrulanabilir. Küme
bir kez ölçüldü (`python olcum/denetim_olcumu.py`):

| Madde | Örnek (VAR) | Öncelikli metrik | Test kümesi (iyimser) | **Son küme** | DP / YP / YN / DN (son küme) | Çoğunluk sınıfı | Rastgele (beklenen) | Yayın ölçütü (11. bölüm) |
|---|---|---|---|---|---|---|---|---|
| D1 kaba ifade | 13 (7) | kesinlik / F1 | 0,83 / 0,83 | **0,71 / 0,71** | 5 / 2 / 2 / 4 | 0 / 0 | 0,53 / 0,50 | ✗ sağlanmadı |
| D2 kişisel veri | 11 (6) | duyarlılık (kesinlik) | 0,80 (0,80) | **0,83 (1,00)** | 5 / 0 / 1 / 5 | 0 | 0,49 | ✓ |
| D3 kategori | 14 (7 × 2) | makro F1 (doğruluk) | 0,87 (0,86) | **0,49 (0,50)** | aşağıda | 0,04 (0,14) | 0,13 (0,14) | ✗ sağlanmadı |

D1'de 0,83'ten 0,71'e düşüş, 13 örnekte bir yanlış engel ve bir kaçak farkıdır; küçük kümede tek örnek sonucu belirgin
değiştirir. Bu yüzden ölçüt yalnızca tek bir sayıya değil, hata örneklerine de bakılarak yorumlandı.

**D3 sınıf bazında ve karışıklık matrisi (son küme; satır gerçek sınıf, sütun kuralın tahmini, · = 0).**

| Sınıf | Kesinlik | Duyarlılık | F1 | Bil | Eko | Eğt | Kül | Sağ | Siy | Tek | eşleşme yok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bilim | 0,00 | 0,00 | 0,00 | · | · | 1 | · | · | · | · | 1 |
| Ekonomi | 1,00 | 0,50 | 0,67 | · | 1 | 1 | · | · | · | · | · |
| Eğitim | 0,29 | 1,00 | 0,44 | · | · | 2 | · | · | · | · | · |
| Kültür ve Sanat | 1,00 | 0,50 | 0,67 | · | · | 1 | 1 | · | · | · | · |
| Sağlık | 1,00 | 0,50 | 0,67 | · | · | 1 | · | 1 | · | · | · |
| Siyaset | 1,00 | 1,00 | 1,00 | · | · | · | · | · | 2 | · | · |
| Teknoloji | 0,00 | 0,00 | 0,00 | 1 | · | 1 | · | · | · | · | · |

Eğitim sütunu yedi hatanın beşini topluyor: Eğitim'in kesinliği 0,29'a düşüyor, Bilim ve Teknoloji hiç doğru bulunamıyor.

**Hata örnekleri (H2-56).**

| Madde | Örnek | Beklenen → kural | Neden |
|---|---|---|---|
| D1 | "Aptal telefonlar dönemine dönmek ister misiniz?" | YOK → VAR (yanlış engel) | Kelime bir kişiyi değil bir nesneyi niteliyor; liste bağlamı bilmiyor |
| D1 | "Kafana taş mı düştü, ne biçim öneri bu?" | VAR → YOK (kaçtı) | Deyimsel hakaret; listede tek bir kelimesi yok |
| D2 | "Moda Caddesi No 15 Daire 7 Kadıköy'de oturuyorum." | VAR → YOK (kaçtı) | Adres serbest biçimli; desenle yakalanmıyor |
| D3 | "Yurtlarda grip aşısı kampanyası yapılsın." | Sağlık → Eğitim | Yalnızca "yurt" (Kampüs Yaşamı) eşleşti; "grip", "aşı" Sağlık kavramlarında yok |
| D3 | "Laboratuvar bilgisayarlarına Linux kurulsun." | Teknoloji → Bilim | "laboratuvar" (Bilim) ve "bilgisayar" (Teknoloji) birer kavramla berabere; eşitliği kategori sırası bozdu |

**Yorum.**
- **D3:** Önceki ölçümler, kuralları geliştiren ve ontolojiyi bilen yazarın, kurallara bakarak düzeltme yaptığı örneklerle
  yapılmıştı. Gerçek başarım belirgin biçimde daha düşük çıktı. Hata analizinde yedi hatanın beşi "Eğitim" yönünde: "kampüs", "öğrenci", "ders", "laboratuvar" gibi her konuda geçen
  kelimeler metni Eğitim'e çekiyor. "Gökbilim" gibi listede olmayan kelimeler hiç eşleşmiyor. Bu, H2-38'deki merdivenin beklenen
  sonucu: anahtar kelime kuralı çoğunluk sınıfını açık farkla geçiyor (0,49'a karşı 0,04), ama kendi başına yeterli değil.
- **D1:** Listede olmayan argo ("hödük") ve deyimsel hakaret ("kafana taş mı düştü") kaçıyor. Kavram anlamındaki kullanımlar
  ("cahillik bilgisizlik demektir", "aptal telefon") yanlış engelleniyor. Yanlış engel oranı %29.
- **D2:** Desenle tanımlanabilen veri türlerinde (telefon, e-posta, kimlik no, IBAN) sağlam. Serbest yazılmış adres yine kaçtı.

**Karar (ölçütler önceden yazıldığı için, H2-43).**
1. D3 yalnızca **uyarı** verir, konuyu engellemez; önerdiği kategori konu sahibine bir öneri olarak gösterilir. Düşük başarım
   kullanıcıyı durdurmaz, bu yüzden yayın engeli sayılmadı. Ama "otomatik kategori" gibi bir kullanıma açılmamalıdır.
2. D1 **engelliyordu**; %29 yanlış engel, 5.3'teki maliyet hesabına göre (yanlış engel pahalı; engelleyen kural "hep temiz"den
   pahalı çıkıyor) kabul edilemez. Ölçüt önceden yazıldığı için hedef kaydırılmadı, sonuç uygulandı: **yeni kurulumlarda D1'in
   varsayılan ciddiyeti "Uyarır" yapıldı** (commit `1bdb6da`). Hakaret içeren metin artık yayımlanır ama yazana uyarı gösterilir;
   kaçanı topluluk şikayet ve gizleme oylamasıyla düzeltir. Bu, S01-32'deki "emekle" aşamasıdır: sistem işaretler, karar insanın.
   Topluluk isterse yönetmelik oylamasıyla "Engeller"e geri çekebilir (H2-29: eşik bir iş kararıdır); kod değişmez. Kişisel veri
   (D2) engellemeye devam eder.
3. Her iki madde için de H2-9 karar ağacındaki sonraki adım aynıdır: **önce veri toplayın.** Topluluğun gizleme oylamaları ve
   şikayetleri etiket olarak birikir. Birkaç yüz örnekte basit bir model (TF-IDF + lojistik regresyon) bugünkü kurala karşı,
   ikisi de dondurulduktan sonra yazılmış yeni ve hiç görülmemiş bir kümede ölçülür (11. bölümdeki değiştirme ölçütü). Bu son
   küme artık bir kez görüldüğü için o karşılaştırmada kullanılmaz.

---

## 7. Kısıtlar (H2-45)

| Kısıt | Agora | Model / tasarım seçimine etkisi |
|---|---|---|
| Zaman | Dönem ödevi | Çekirdek (oylama, defter) önce; YZ destek işleri kural tabanlı |
| Bütçe | Sunucu ücreti yok, GPU yok, ücretli API yok | BDM ve derin öğrenme masadan kalkar (H2-45 "kısıtlar modeli sizin yerinize seçer") |
| Gecikme | Sunucu tarafında p95 < 200 ms | Denetim her konu ve mesajda çalışır → milisaniyelik kural |
| Gizlilik ve KVKK | Kişisel veri yalnızca kayıtta; görünen takma ad; API kişisel veri döndürmez; deftere yalnızca özet | Mesaj metni dış servise gönderilemez |
| Donanım / ortam | Tek bilgisayar (Windows dizüstü), SQLite, tek süreç; telefon WebView kabuğu | Yazmalar tek kilitte sıralanır (`BEGIN IMMEDIATE`); çok süreçli dağıtım kapsam dışı |
| Yasal ve etik | Gizli oy; sayım kuralı açıklanabilir olmalı; oy ve kararları etkileyen YZ yüksek risk sınıfına yakın (AB YZ Yasası) | YZ oy vermez, karar vermez, kararı etkileyen sayıyı kendisi üretmez |
| Güvenlik | Gizli anahtar kodda değil (S01-17) | Oturum anahtarı `FORUM_GIZLI_ANAHTAR` ya da yalnız sahibinin okuyabildiği dosya (0600); bağımlılık sürümleri sabit (`requirements.txt`; S02-47: uydurma paket adları) |

---

## 8. İşlevsel olmayan gereksinimler (S01-25 dört gereksinim + S01-24 gecikme)

### 8.1 Güvenilirlik (reliability) — "ML sistemleri sessizce hata yapar"

| Gereksinim | Nasıl sağlanıyor | Kanıt |
|---|---|---|
| Aynı anda gelen istekler tutarlı | Yazan istekler `BEGIN IMMEDIATE` ile sıralanır; oy yalnızca tur hâlâ açıksa yazılır (koşullu INSERT); fikir tekliği kısmi tekil indeksle | Kişi başı tek fikir kuralı 8 iş parçacığıyla eşzamanlı sınanır (`OylamaYarislari.test_ayni_anda_gelen_fikirler`; düzeltmeden önce aynı test 7–8 fikir üretiyordu). Kapanmış tura oy verilmemesi tek iş parçacığıyla sınanır (`test_suresi_dolmus_oylamaya_oy_verilmez`); oy ile kapanışın eşzamanlı yarışı için ayrı bir test yok |
| Bir işin hatası diğerlerini durdurmaz | Zamanlayıcı her konuyu ayrı kayıt noktasında (SAVEPOINT, Memento) işler | `ZamanlayiciYalitimi` |
| Yan etki hatası isteği bozmaz | Commit sonrası defter yazımı/bildirim hatası günlüğe yazılır, kullanıcı işlemi tekrarlamaz | `YanEtkiDayanikliligi` |
| Kayıtların kurcalanmadığı | 3 düğüm, çoğunluk, onarım; veritabanı–defter tutarlılık denetimi; birden çok süreç aynı anda yazsa da zincir bölünmez (süreçler arası kilit) | `DefterDeposu`, `DefterOlceklenmesi`, `DefterDayanikliligi` (SQLite ile ya da ham bayt olarak yapılan kurcalama önbelleğe rağmen yakalanır; 3 süreç × 15 yazma) |
| Sessiz model hatası | Denetim kuralları ölçülüyor ve ölçüm testte korunuyor | `test_olcum.py` |
| Yedek ve kurtarma | Yönetim panelinden tutarlı veritabanı yedeği (`yonetim.yedek_al`) | **RPO** = son alınan yedek (elle); **RTO** ≈ dakikalar (dosyayı geri koy). Sınır: defter düğümleri yedeğe dahil değil; yedek dosyası gizli oy ve kişisel veri içerir → şifreli saklanmalı (yapılmadı, 10. bölüm) |

### 8.2 Ölçeklenebilirlik (scalability) — ölçüldü

`python olcum/gecikme_olcumu.py 60` (demo verisi; 4 çekirdekli Linux, Python 3.13; Flask test istemcisi, yalnızca sunucu süresi, ms):

| İstek | p50 | p95 | En kötü |
|---|---|---|---|
| Konu akışı | 10,9 | 15,5 | 15,6 |
| Konu sayfası (27 mesaj) | 8,9 | 10,5 | 14,8 |
| Oylama sayfası | 3,8 | 4,3 | 5,0 |
| Gündem | 4,6 | 5,1 | 5,8 |
| Kayıt defteri | 4,6 | 5,7 | 6,0 |
| Üye ağı | 4,8 | 5,3 | 7,6 |
| API: konu listesi | 2,2 | 2,4 | 2,6 |
| Oy verme (commit + 3 düğüme yazım) | 7,4 | 10,1 | 10,3 |

**Defter büyüyünce.** `--defter-blok` ile defter yapay olarak büyütüldü. Önceden her yazma ve her defter
sayfası üç düğümün bütün zincirini baştan okuyup SHA-256 ile yeniden doğruluyordu (O(n)):

| Defterdeki blok | Oy verme p95 — önce | Oy verme p95 — şimdi | Defter sayfası p95 — önce | şimdi |
|---|---|---|---|---|
| ~600 (demo) | 18,6 | 10,1 | 14,1 | 5,7 |
| +10.000 | 148,3 | 9,3 | 272,1 | 5,7 |
| +50.000 | **645,2** | **9,5** | **1.145,5** | **11,7** |

"Önce" sütunları düzeltmeden önceki kodla (commit `a266e48`) aynı komutla ölçüldü; o sürümde p95 formülündeki bir yuvarlama hatası
(sonradan düzeltildi) değerleri bir sıra yukarıdan okuyordu, büyüklük sırası değişmez. "Şimdi" sütunları:
`python olcum/gecikme_olcumu.py 60` ve `python olcum/gecikme_olcumu.py 30 --defter-blok N`.

Düzeltme (`defter.py`): düğüm başına tam doğrulamanın sonucu, düğümün **sürümüyle** birlikte saklanır; sürüm değişmedikçe zincir
yeniden doğrulanmaz, yazma yalnızca son bloğu okur. Sürüm; SQLite dosya başlığındaki değişiklik sayacı, dosyanın kimliği, boyu,
değişiklik ve durum değişim zamanı (ctime) ile WAL dosyasından oluşur: dosyayı SQLite ile ya da ham bayt olarak değiştirmek
sürümü değiştirir (testli). Sürümün göremeyeceği değişikliklere (disk bozulması; Windows'ta zamanı geri alınmış ham bayt değişikliği)
karşı bir doğrulama sonucu en fazla 10 dakika kullanılır ve "denetle" istekleri ile onarım önbelleği hiç kullanmaz.
Repository deseni sayesinde değişiklik tek dosyada kaldı.

**Konu sayısı büyüyünce.** `python olcum/gecikme_olcumu.py 30 --konu 1000` (1.019 konu): konu akışı p50 **48,7 ms**, p95 **51,5 ms**.
Düzeltmeden önce aynı ölçüm (1.000 kopya, 10 istek) p50 77 ms, en kötü 176 ms veriyordu. Zamanın çoğu yan paneldeki
"öne çıkan kelimeler" hesabındaydı; aynı kelimenin binlerce kez yeniden katlanması kaldırıldı.

**Bilinen sınırlar:**
- Öne çıkan kelimeler hâlâ son 7 günün bütün metnini her istekte işliyor (O(metin)). Sonraki adım: konu/mesaj yazılınca artımlı sayım.
- Sunucu yeniden başlayınca her düğüm bir kez tam doğrulanır (50.000 blokta yaklaşık yarım saniye, yalnızca ilk istekte).
- SQLite tek yazar: yazan istekler sıraya girer. Bir oy ~10 ms → saniyede ~100 yazma. Daha fazlası için PostgreSQL ve
  defterin ayrı bir hizmete taşınması gerekir (Repository arayüzü buna hazır).
- Birden çok sunucu süreci (ör. birden çok WSGI işçisi) çalışırsa defter yazmaları süreçler arası kilitle doğru sıralanır; ama bir
  süreç ötekinin yazdığı düğümü yeniden doğrulamak zorunda kalır, önbelleğin hız kazancı azalır. Önerilen dağıtım tek süreç, çok iş parçacığıdır.

### 8.3 Sürdürülebilirlik (maintainability)

- Tasarım desenleri ve SOLID eşlemesi: `docs/tasarim.md` 8. bölüm (her desen dosya adıyla).
- 201 otomatik test (~12 sn); ölçüm betikleri; hata düzeltmelerinin testleri (`testler/test_duzeltmeler.py`; düzeltmeden önceki kodda kırmızı olduğu denetlendi, README YZ kullanım beyanı).
- Bağımlılık sürümleri sabit; gizli anahtar kodda değil; ayarlar ortam değişkeniyle (README).

### 8.4 Uyarlanabilirlik (adaptability) — "hizmeti kesmeden uyum"

| Değişiklik | Kod değişikliği gerekir mi? |
|---|---|
| Eşik, süre, ağırlık, yeter sayı | Hayır: yönetmelik oylamasıyla (parametreler veritabanında, anlamlı aralıklarla sınırlı) |
| Denetim maddesinin sertliği (Engeller / Uyarır / Kapalı) | Hayır: oylamayla |
| D1 hakaret kelime listesi | **Evet:** bugün kod sabiti (`denetim.KABA_IFADELER`). Yönetmelik verisine taşınırsa oylamayla güncellenebilir (önerilen sonraki adım) |
| Yeni kategori ve kavramları | Hayır: üyeler önerir, oylar; D3 yeni kavramları hemen kullanır |
| Yeni oylama türü | Bir sınıf (`teklif_turleri.py`'de `@kaydet`) + `ayarlar.TEKLIF_TIPLERI`'nde bir yapılandırma satırı (ad, eşik, süre); mevcut kod değişmez (OCP) |
| Yeni denetim maddesi | Bir halka sınıfı (`denetim.py`) + madde metni |
| Yeni bildirim kanalı | Bir Adapter sınıfı (`anlik.py`) |
| Defter deposu (ör. PostgreSQL) | Bir `DugumDeposu` gerçeklemesi |

---

## 9. Paydaşlar (H2-46)

| Paydaş | Ne ister | Çatışma | Yazılı karar |
|---|---|---|---|
| Katılımcı üye | Sesinin duyulması, hızlı karar | Hız ↔ azınlığın dinlenmesi | Süreli turlar ama eleme kademeli (%5 → %20); ezici üstünlük kısa yolu |
| Azınlık | Fikrinin elenmemesi, karara itiraz | Çoğunluk kararı ↔ azınlık koruması | Herkes bir fikir; itiraz konusu; korunan maddeler 3/4 |
| Gözlemci (kural dışı kalan) | Okumak, izlemek | Katılım kuralı ↔ şeffaflık | Gözlemci her şeyi okur, oy veremez |
| Uzman | Bilgisinin ağırlığı | Uzmanlık ↔ eşitlik | Oy 10 sayılır ama çift oran: kalabalığı tek başına yenemez; kontenjan |
| Yönetici | Siteyi işletmek | Yönetim ↔ karar yetkisi | Yönetici yalnızca yönetir; normal çalışmada kararı etkileyen işlem tanımlı değil. Tek istisna sunum kipi (`--demo`): "Süreyi ilerlet" beklemeyi kısaltır, sayım kurallarını değiştirmez, günlüğe yazılır |
| Veri sahibi (KVKK) | Kişisel verinin korunması | Denetlenebilirlik ↔ mahremiyet | Deftere yalnızca özet/taahhüt; gizli oy; küçük görüş grupları gösterilmez (k-anonimlik ≥ 3) |
| Geliştirici / bakım | Değiştirilebilir kod | Özellik hızı ↔ kalite | Desenler, testler, ölçümler |
| Ders / değerlendirici | Analiz, desen, ölçüm | — | Bu belge ve `docs/tasarim.md` |

---

## 10. Ön-otopsi (pre-mortem, H2-47): "Altı ay sonra Agora başarısız oldu. Neden?"

O = olasılık, E = etki (Y yüksek = 3, O orta = 2, D düşük = 1). Risk = O × E; tablo riske göre sıralı (H2-47: önce en büyük risk).

| # | Neden | O | E | Risk | Önlem | Durum |
|---|---|---|---|---|---|---|
| C | Kimse oy vermedi, turlar sonuçsuz kaldı | Y | Y | **9** | Bildirimler, oy devri, yeter sayı ayarı; metrik: yeter sayıya ulaşamayan tur oranı | Uygulandı, ölçülüyor |
| A | Bir grup oy devriyle gücü topladı | O | Y | 6 | Devir tavanı (MAX_DEVIR), döngü yasağı, koruyucu metrik Gini | Uygulandı, ölçülüyor |
| B | Sahte hesaplarla oylama ele geçirildi (Sybil) | O | Y | 6 | Bir adresten saatte en fazla 20 kayıt; yaş/konum kuralı | **Kısmi**: hesaplar şifreyle korunuyor ama kişinin gerçek kimliği teyit edilmiyor. Gerçek kullanımda okul e-postası ya da e-Devlet ile kimlik teyidi gerekir |
| F | Defter büyüdü, site yavaşladı | Y | O | 6 | Doğrulama önbelleği | **Düzeltildi** (8.2) |
| I | Forum demo şifreleriyle yayına alındı | O | Y | 6 | Ağa açılırken uyarı; `--demo-verisiz` | Uygulandı |
| D | Denetim meşru mesajları engelledi, üyeler küstü | O | O | 4 | Ölçüm (6. bölüm); ciddiyet oylamayla değiştirilebilir | **Gerçekleşti ve önlendi:** görülmemiş kümede D1'in yanlış engel oranı %29 çıktı; varsayılanı "Uyarır" yapıldı (6.5) |
| H | Tek fikir + çok çekimser oyla zayıf bir fikir "tek kalan" olarak karar oldu | O | O | 4 | Ödev şartnamesindeki kural; yeter sayı ve itiraz konusu dengeler | Bilerek korundu; izlenecek metrik: tek kalanla kabul edilen kararların oranı |
| J | Çok uzun bir gerekçeyle sunucu saniyelerce kilitlendi (hizmet reddi) | O | O | 4 | Desenler kelime/rakam sınırında başlar; serbest metinlere 5.000 karakter sınırı | **Düzeltildi** (sonradan) |
| E | YZ özeti yanlış sayı yazdı, karar etkilendi | D | Y | 3 | Kural tabanlı özet, sayılar veritabanından, kesme ile yuvarlama | Uygulandı, testli |
| G | Yedek dosyası sızdı (gizli oylar + kişisel veri) | D | Y | 3 | Yedeği yalnızca yönetici indirir | **Açık risk**: yedek şifrelenmiyor |

---

## 11. Başarı tanımı ve yayın ölçütü (H2-43: "önceden yazılmalı")

Agora şu koşullarda yayına alınır. Biri bozulursa yayın durur ya da ölçütü bozan özellik engelleyici olarak yayına alınmaz
(6.5'te D1 için yapıldığı gibi). Ders demosu ve GitHub Pages sürümü "yayın" değil, prototiptir; gerçek bir topluluğa açılmadan
önce ayrıca 10. bölümdeki açık riskler (B kimlik teyidi, G yedek şifreleme) kapatılmalıdır.

1. Bütün otomatik testler geçer (`python -m unittest discover testler`).
2. Denetim, test kümesinde (5.3'teki öncelikli metriklerle): D1 kesinlik ≥ 0,80 ve F1 ≥ 0,80, D2 duyarlılık ≥ 0,80,
   D3 makro F1 ≥ 0,85 — ve her biri temel çizgileri geçer (`testler/test_olcum.py` bu eşikleri her çalıştırmada denetler).
   **Durum:** test kümesinde sağlanıyor. Görülmemiş son kümede (6.5) yalnızca D2 sağlandı. Karar: D1'in varsayılanı "Uyarır"
   yapıldı (uygulandı); D3 zaten yalnızca uyarır ve otomatik kategori seçiminde kullanılmaz.
3. Sunucu tarafı p95 < 200 ms: demo verisinde (`gecikme_olcumu.py 60`), 1.000 konuda (`--konu 1000`) ve 50.000 bloklu defterde
   (`--defter-blok 50000`).
4. Defter–veritabanı tutarsızlığı 0.

**Bir kuralı modelle değiştirme ölçütü:** model ve kural, ikisi de dondurulduktan sonra yazılmış, *hiç görülmemiş aynı kümede*
ölçülür (6.5'teki yöntem); model kuralı en az +0,10 F1 farkla geçmeli, p95 < 200 ms'yi korumalı ve mesaj metnini dışarı
göndermemeli. Aksi hâlde H2-37'deki "Senaryo B": birkaç puan için GPU, izleme ve yeniden eğitim
maliyeti değmez.

---

## 12. Bilerek yapılmayanlar (ödünleşimler)

| Konu | Neden yapılmadı | Ne zaman yapılmalı |
|---|---|---|
| BDM ile içerik özeti | 3. bölüm: halüsinasyon, KVKK, maliyet; ölçülmüş eksik yok | Etiketli onay verisi birikince, insan onaylı |
| ML tabanlı denetim | Etiketli veri yok | Gizleme oylaması/şikayet verisi birkaç yüz örneğe ulaşınca; bugünkü kural temel çizgi olur |
| Çok süreçli dağıtım | SQLite tek yazar; defter yazmaları süreçler arası kilitle doğru ama önbellek kazancı azalır | Saniyede ~100 yazmayı aşan kullanımda |
| Yedeğin şifrelenmesi | Kapsam | Gerçek kullanıma geçmeden önce |
| Kimlik teyidi (Sybil'e karşı; okul e-postası ya da e-Devlet) | Ödev kapsamı dışı | Gerçek kullanıma geçmeden önce |
| Göç kodundaki eski sütunlar | Eski veritabanlarıyla uyum | Bütün kurulumlar yeni şemaya geçince |
