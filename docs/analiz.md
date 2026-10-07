# Agora — Problem Çerçeveleme ve Gereksinim Analizi

Bu belge, Agora'yı ders slaytlarındaki yöntemle analiz eder: önce "hangi problemi çözüyoruz?", sonra "YZ gerekli mi?",
sonra metrikler, temel çizgi (baseline), kısıtlar, paydaşlar ve ön-otopsi. Atıflar:
**H2** = Hafta 2 *Problem Çerçeveleme* slaytları, **S01** = *YZ Mühendisliğine Giriş*, **S02** = *Temel Modelleri Anlamak*,
**TD** = *Yazılım Tasarım Desenleri* (numaralar slayt numarasıdır).

Belgedeki bütün sayılar `olcum/` klasöründeki betiklerle **ölçülmüştür**; tahmin değildir. Her tablonun altında hangi
komutla yeniden üretileceği yazar. Kendi bilgisayarında çalıştırıp sayıları güncelleyebilirsin.

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

**Bileşen düzeyinde çerçeveleme tablosu (H2-18, H2-23).** Her satır bir kararla başlıyor; karar sütunu boş olan bileşen yok.

| Bileşen | Karar | Görev türü | Girdi → çıktı | Kararı kim verir |
|---|---|---|---|---|
| Fikir oylaması (`oylama.py`, `sonuclar.py`) | Hangi fikir kazanır | ML değil: sayım kuralı | Oylar → kabul / sonraki tur / sonuçsuz | Üyeler |
| D1 Saygın dil (`denetim.py`) | Metin yayımlansın mı | İkili sınıflandırma | Metin → kaba ifade VAR/YOK | Kural engeller; yazan düzeltir; kaçanı topluluk gizler |
| D2 Kişisel veri | Metin yayımlansın mı | İkili sınıflandırma (desen tanıma) | Metin → kişisel veri VAR/YOK | Kural engeller |
| D3 Kategoriye uygunluk | Konu doğru alanda mı | Çok sınıflı sınıflandırma (7 ana alan) | Başlık + açıklama → kategori | Konu sahibi (yalnızca uyarı) |
| D5 Benzer konu | Aynı konu açık mı | Benzerlik / sıralama | Başlık → en benzer konu ve oranı | Konu sahibi (uyarı) |
| Yapay zeka özeti (`yz.py`) | Okumadan oy verene ne gösterilir | Üretim (generation) | Mesajlar + sayım → kısa metin | Okur; özet oy vermez |
| Görüş grupları (`graf.py`) | — (yalnızca görselleştirme) | Kümeleme (etiket yayılımı) | Etkileşim grafı → gruplar | Kimse; karar yok |

**YZ'nin üründeki rolü (S01-31):** *tamamlayıcı* (Agora YZ olmadan da çalışır: özet yoksa forum işler, denetim kapatılabilir),
*tepkisel* (denetim, yazana anında yanıt verir → gecikme önemli) ve *öngörülü* (tur özeti tur bitince kendiliğinden yazılır →
kalite çıtası yüksek, gereksiz özet tartışmayı kirletir; bu yüzden yeni mesaj yoksa yeni özet yazılmaz), *statik*
(kurallar herkese aynı; topluluk oylamayla değiştirir).

---

## 3. YZ gerekli mi? (H2-7, H2-8, H2-9)

H2-7'deki beş koşul ve H2-9'daki karar ağacı her bileşen için ayrı ayrı uygulandı. ✓ koşul sağlanıyor, ✗ sağlanmıyor.

| Bileşen | Öğrenilecek örüntü | Kural yazmak zor | Veri var | Hata ucuz | Örüntü değişiyor | Karar ağacının sonucu |
|---|---|---|---|---|---|---|
| Sayım ve eleme | ✗ (kural yönetmelikte) | ✗ | — | ✗ (kararı belirler) | ✗ | **Kural yazın.** H2-12'deki "harf notu" durumu: model, bilinen kuralın bozuk kopyası olur. Açıklama yasal/etik zorunluluk (H2-8). |
| D1 kaba ifade | ✓ | kısmen | ✗ (etiketli forum mesajı yok) | kısmen | ✓ (argo değişir) | **Önce veri toplayın** → bugün kural; topluluğun gizleme oylamaları ve şikayetler etiket olarak birikir (H2-13: insan kararı = yeni etiket). |
| D2 kişisel veri | kısmen | ✗ (biçimler belli: telefon, e-posta, kimlik no, IBAN) | ✗ | ✗ (KVKK) | ✗ | **Kural yazın.** Adres gibi serbest biçimler kuralla yakalanmıyor (6. bölüm); ileride ad-varlık tanıma (NER) modeli adayı. |
| D3 kategori | ✓ | kısmen | ✗ | ✓ (yalnızca uyarı) | ✓ (yeni kategoriler) | **Kural (ontoloji)**; yeni kategoriler topluluk tarafından *kavramlarıyla* eklendiği için kural kendiliğinden uyarlanır. |
| YZ özeti — sayılar | ✗ | ✗ | — | ✗ (oyu etkiler) | ✗ | **Kural yazın.** Kim kaç mesaj yazdı, fikir yüzde kaç aldı: veritabanında hazır. |
| YZ özeti — içerik | ✓ | ✓ | ✓ (mesajlar) | ✗ | ✓ | **İnsan onaylı ML** (H2-9 en sağ alt dal). Bugün uygulanmadı; aşağıda tasarımı var. |

**Neden büyük dil modeli (BDM / LLM) ile özet yazılmadı?** H2-10'daki yelpazenin solundan başlandı; sağa geçmeyi
gerektiren ölçülmüş bir eksik yok. Ayrıca dört somut engel var:

1. **Halüsinasyon (S02-43, 44):** BDM "%74,5" yerine "%75" yazabilir ya da bir fikri "elendi" diye özetleyebilir. Agora'da
   özet oy vermeden önce okunur; yanlış sayı kararı etkiler. Bu yüzden `yz.py`'deki her sayı veritabanından gelir, oranlar
   **yuvarlanmaz, kesilir** (`metin.yuzde`: %74,9 asla "%75" olmaz), her fikrin durumu turun kaydedilmiş kararından okunur
   (`sonuclar.TurKarari`). Testler: `YapayZekaOzetleri`, `TurKarariAnlikGoruntusu`.
2. **Veri dışarı çıkamaz (H2-45, KVKK):** Mesajları bir dış API'ye göndermek, kişisel verinin üçüncü tarafa aktarılması demek.
3. **Maliyet ve gecikme (S01-24, H2-10):** Çağrı başına ücret ve saniyeler süren yanıt; kural tabanlı özet milisaniyeler sürer, ücretsiz.
4. **Olasılıksal çıktı (S02-41, 42):** Aynı tartışma iki kez özetlenince farklı metin çıkabilir; denetlenebilirlik ilkesiyle çelişir.

**İleride BDM eklenecekse önerilen tasarım (insan döngüde, S01-32 "emekle–yürü–koş"):**
- *Emekle:* BDM yalnızca içerik özetinin **taslağını** yazar; sayılar kural tabanlı özetten gelir ve BDM'ye "bu sayıları aynen kullan"
  diye verilir. Çıktı yapılandırılmıştır (S02-38: JSON şema — fikir no, öne çıkan argümanlar), serbest metin değildir.
- Son işleme (S02-40): çıktıdaki her sayı veritabanındaki sayıyla karşılaştırılır; bir tanesi bile uymazsa özet atılır, kural
  tabanlı özet yazılır (**sayı sadakati** koruyucu metriği, 5. bölüm).
- Özet, katılımcılardan biri onaylamadan yayımlanmaz. Onaylanan/düzeltilen özetler etiketli veri olur (veri çarkı, S01-33).
- *Yürü*'ye geçiş ölçütü: 4 hafta boyunca onaylayanların taslağı değiştirmeden kabul oranı ≥ %95 (S01-32'deki ölçütün aynısı).

---

## 4. Tek sayfalık problem tanım kanvası (H2-48, H2-49)

| Kutu | Agora |
|---|---|
| **1. İş hedefi ve değer** | Topluluk kararlarının adil (azınlık korunur, tek kişi baskın olmaz), şeffaf (sayım ve kayıt herkesçe denetlenir) ve zamanında (en fazla 7 gün: 24 saat tartışma + 48 saatlik 1. tur + 4 × 24 saatlik tur) alınması. İş metriği: kapanan konuların karara bağlanma oranı. |
| **2. Karar ve eylem** | Kararı üyeler oyla verir. Sistem, kararı *hazırlar*: içerik denetimi yazana anında geri bildirim verir (günde mesaj sayısı kadar), özet her tur sonunda bir kez yazılır. |
| **3. ML görevi** | Çekirdekte yok. Destek görevleri: D1/D2 ikili sınıflandırma, D3 7 sınıflı sınıflandırma, D5 benzerlik, özet = üretim. Etiket tanımları: `olcum/gelistirme.csv` başlığı ve 6. bölüm. |
| **4. Veri** | Etiketli veri yok (yeni ürün). Ölçüm için elle etiketlenmiş 85 + 43 örnek. Gelecekte etiket kaynağı: topluluğun gizleme oylamaları, şikayetler, kategori değişiklikleri. Kişisel veri: ad soyad, doğum tarihi, adres yalnızca kayıtta; görünen takma ad; deftere yalnızca özet ve taahhüt. |
| **5. Metrikler** | Model: D1 kesinlik (yanlış engel pahalı), D2 duyarlılık (kaçan kişisel veri pahalı), D3 makro F1. Ürün: katılım oranı, karar süresi. Koruyucu: oy gücü Gini, defter tutarsızlığı = 0, YZ sayı sadakati = %100, p95 gecikme. (5. bölüm) |
| **6. Baseline** | Çoğunluk sınıfı ve rastgele (ölçüldü); bugünkü kural (ölçüldü); mevcut çözüm = insan (topluluğun gizleme oylaması, ölçülmedi). (6. bölüm) |
| **7. Kısıtlar** | Dönem ödevi süresi; sunucu bütçesi yok, GPU yok, dış API yok; tek bilgisayarda SQLite; p95 < 200 ms; KVKK; gizli oy; kararlar açıklanabilir olmalı. (7. bölüm) |
| **8. Riskler ve başarı** | Ön-otopsi: 9. bölüm. Yayın ölçütü: 11. bölüm. |

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

- **D1 (kaba ifade), ENGEL:** Yanlış pozitif (YP) meşru bir mesajı durdurur, yazan düzeltmek zorunda kalır; yanlış negatif (YN)
  hakaretin yayımlanması demek ama topluluk şikayet ve gizleme oylamasıyla düzeltebilir. **YP daha pahalı → kesinlik öncelikli** (F0,5).
- **D2 (kişisel veri), ENGEL:** YN kişisel verinin herkese açılması (KVKK); YP yalnızca bir yeniden yazma. **YN çok daha pahalı →
  duyarlılık öncelikli** (F2). Örnek maliyet (H2-31 yöntemi; birimler paydaşlarla belirlenmeli): YN = 50, YP = 1 alınırsa test
  kümesinde kural 50·1 + 1·1 = **51**, "hep temiz" temel çizgisi 50·5 = **250** birim.
- **D3 (kategori), UYARI:** Hata yalnızca bir uyarı; 7 sınıfın hepsi eşit önemde → **makro F1** (H2-30).

### 5.4 Çok boyutlu değerlendirme (H2-34)

| Boyut | Gereksinim | Durum |
|---|---|---|
| Gecikme | p95 < 200 ms (sunucu tarafı) | Ölçüldü: en yavaş sayfa p95 16 ms (demo), 1.000 konuda konu akışı en kötü 151 ms (8. bölüm) |
| Maliyet | İstek başına dış servis ücreti 0 | Dış API yok |
| Açıklanabilirlik | Her engel/uyarı nedenini söyler; her sayım tablosu herkese açık | Denetim raporu madde madde gerekçe yazar; oylama sayfası sayım tablosunu gösterir |
| Mahremiyet | Kişisel veri modele/dışarıya gitmez | Kural tabanlı, yerel; deftere yalnızca özet |
| Adalet | Azınlık korunur; konumdan bağımsız eşit kural | Çift oran, kişi başı bir fikir, devir tavanı, uzman kontenjanı; koruyucu Gini |

---

## 6. Temel çizgi (baseline) ve hata analizi

### 6.1 Merdiven (H2-38)

| Basamak | Agora'da | Durum |
|---|---|---|
| Rastgele | Sınıflardan birini eşit olasılıkla seç (tohum 42) | Ölçüldü |
| Çoğunluk sınıfı | D1/D2: "hep temiz" (hiçbir şeyi engelleme), D3: "hep en sık kategori" | Ölçüldü |
| Basit kural | Anahtar kelime (D1), düzenli ifade + T.C. kimlik sağlaması (D2), ontoloji kavramları (D3) | **Bugünkü sistem**, ölçüldü |
| Mevcut çözüm | İnsan: topluluğun şikayet ve gizleme oylaması | Ölçülmedi (gerçek kullanım verisi yok) |
| Basit ML | TF-IDF + lojistik regresyon | Yapılmadı: etiketli veri yok (H2-9 "önce veri toplayın") |
| Karmaşık model | İnce ayarlı BERT / BDM | Yapılmadı (3. bölüm) |

### 6.2 Ölçüm düzeneği

- Örnekler `olcum/gelistirme.csv` (D1: 28, D2: 22, D3: 35) ve `olcum/test.csv` (D1: 12, D2: 10, D3: 21). Etiketler kurallar
  çalıştırılmadan **önce** elle yazıldı. Örnekler gerçekçi ama küçük; sonuçlar kesin başarım değil, bir referans noktası.
- **Test kümesi kutsaldır (H2-55):** Hata analizi yalnızca geliştirme kümesinde yapıldı; test kümesi kurallar değiştirilmeden önce
  yazıldı ve iyileştirmeden önce ölçüldü. *Dürüstlük notu:* yeni D3 kodundaki bir hata (aynı kavramın iki alt kategoride iki kez
  sayılması) test kümesindeki bir örnekte fark edildi ve düzeltildi; test kümesindeki D3 sayısı bu yüzden bir miktar iyimserdir.
- Ölçüm koda bağlandı: `testler/test_olcum.py`, kuralların temel çizgileri geçtiğini ve test kümesindeki başarımın aşağıdaki
  değerlerin altına düşmediğini her test çalıştırmasında denetler (koruyucu).

### 6.3 Sonuçlar — test kümesi (`python olcum/denetim_olcumu.py`)

| Madde | Yöntem | Kesinlik | Duyarlılık | F1 | Doğruluk |
|---|---|---|---|---|---|
| D1 kaba ifade (12 örnek, 6 VAR) | Çoğunluk sınıfı | 0,00 | 0,00 | 0,00 | 0,50 |
| | Rastgele | 0,50 | 0,83 | 0,62 | 0,50 |
| | Kural — iyileştirmeden önce | 0,75 | 0,50 | 0,60 | 0,67 |
| | **Kural — şimdi** | **0,83** | **0,83** | **0,83** | **0,83** |
| D2 kişisel veri (10 örnek, 5 VAR) | Çoğunluk sınıfı | 0,00 | 0,00 | 0,00 | 0,50 |
| | Rastgele | 0,57 | 0,80 | 0,67 | 0,60 |
| | **Kural** (önce ve şimdi aynı) | **0,80** | **0,80** | **0,80** | **0,80** |

| Madde | Yöntem | Doğruluk | Makro F1 |
|---|---|---|---|
| D3 kategori (21 örnek, 7 sınıf) | Çoğunluk sınıfı | 0,14 | 0,04 |
| | Rastgele | 0,10 | 0,10 |
| | Kural — iyileştirmeden önce | 0,81 | 0,83 |
| | **Kural — şimdi** | **0,86** | **0,87** |

Geliştirme kümesinde (iyimser, çünkü iyileştirmeler bu kümeye bakılarak yapıldı): D1 F1 0,74 → 0,79; D2 F1 0,82 → 0,95;
D3 doğruluk 0,86 → 0,89.

**Yorum.** Küçük ve dengeli (yarısı VAR) örneklerde rastgele tahminin F1'i yüksek görünür, çünkü duyarlılığı yüksektir.
Gerçek forumda mesajların çok büyük kısmı temizdir (dengesiz sınıf, H2-27); orada rastgelenin kesinliği sınıfın oranına
(ör. %2) düşer ve "hep temiz" temel çizgisi %98 doğruluk alır ama tek hakareti yakalamaz. Bu yüzden doğruluk değil, kesinlik
ve duyarlılık raporlanır.

### 6.4 Hata analizi (H2-56) ve ondan çıkan iyileştirmeler

Kuralın yanıldığı örnekler tek tek okundu. Belirli cümleleri ezberleyen değil, **dil kuralına** dayanan düzeltmeler yapıldı:

| Örnek | Neden yanıldı | Düzeltme |
|---|---|---|
| "Sen ahmağın tekisin." → kaçtı | Türkçe **ünsüz yumuşaması**: *ahmak* ek alınca *ahmağ-* olur; kök listede yok | Her kökün yumuşamış biçimi de aranır (`denetim._yumusamis`). H2-41'deki "Türkçe tuzağı"nın (İ/I) kardeşi; İ/I zaten `ontoloji.tr_kucuk` ile çözülüydü. |
| "IBAN numaram TR33 0006 …" → kaçtı | IBAN deseni yoktu | IBAN deseni eklendi (KVKK kapsamında kişisel veri) |
| "Telefonum 0 (532) 123-45-67." → kaçtı | Parantezli yazım | Desen parantezi kabul ediyor |
| "Belediye meclis toplantıları internetten **canlı** yayınlansın." → Bilim | Her alt kategori tek başına yarışıyordu: Siyaset (meclis) ve Yerel Yönetim (belediye) birer eşleşmeyle Biyoloji'ye (canlı) eşit kaldı, kazananı sözlük sırası belirledi | Eşleşmeler önce **ana alan** düzeyinde toplanıyor (`ontoloji.alan_puanlari`) |

Bilerek düzeltilmeyen hatalar (kuralın sınırı; düzeltmek ezberlemek olurdu):

| Örnek | Neden | Ne yapılmalı |
|---|---|---|
| "Cahiliye dönemi şiiri…", "Aptallar Gemisi adlı kitap…", "Ahmak ıslatan yağmur" → yanlış engel | Kök, masum bir kelimenin ya da deyimin içinde | Ciddiyet UYARI'ya çekilebilir; uzun vadede bağlamı anlayan model (H2-9: veri toplandıkça) |
| "s.a.l.a.k", "öküz", "kafasız", "mal mısın" → kaçtı | Gizleme ve listede olmayan argo | Topluluğun gizleme oylamaları etiket olarak birikir; liste yönetmelik gibi güncellenebilir |
| "Ev adresim Bağdat Caddesi No: 12…" → kaçtı | Adres serbest biçimli | NER modeli adayı; bugün şikayet + gizleme |
| "Ürün kodu 11111111110" → yanlış engel | 11 haneli rastgele bir sayı %1 olasılıkla T.C. kimlik sağlamasını tutar | Kabul edilen bedel (YN çok daha pahalı) |
| "Öğrencilere burs başvurusu…" → Eğitim | "öğrenci" kelimesi Eğitim'in iki kavramına (ogren, ogrenci) birden uyuyor | Ontoloji verisinde kavram tekrarı temizlenmeli |

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
| Aynı anda gelen oylar ve tur kapanışı tutarlı | Yazan istekler `BEGIN IMMEDIATE` ile sıralanır; oy, tur hâlâ açıksa yazılır (koşullu INSERT); fikir tekliği kısmi tekil indeksle | 8 iş parçacığıyla eşzamanlı test (`OylamaYarislari`); düzeltmeden önce aynı test 7–8 fikir üretiyordu |
| Bir işin hatası diğerlerini durdurmaz | Zamanlayıcı her konuyu ayrı kayıt noktasında (SAVEPOINT, Memento) işler | `ZamanlayiciYalitimi` |
| Yan etki hatası isteği bozmaz | Commit sonrası defter yazımı/bildirim hatası günlüğe yazılır, kullanıcı işlemi tekrarlamaz | `YanEtkiDayanikliligi` |
| Kayıtların kurcalanmadığı | 3 düğüm, çoğunluk, onarım; veritabanı–defter tutarlılık denetimi | `DefterDeposu`, `DefterOlceklenmesi` (dışarıdan kurcalama önbelleğe rağmen yakalanır) |
| Sessiz model hatası | Denetim kuralları ölçülüyor ve ölçüm testte korunuyor | `test_olcum.py` |
| Yedek ve kurtarma | Yönetim panelinden tutarlı veritabanı yedeği (`yonetim.yedek_al`) | **RPO** = son alınan yedek (elle); **RTO** ≈ dakikalar (dosyayı geri koy). Sınır: defter düğümleri yedeğe dahil değil; yedek dosyası gizli oy ve kişisel veri içerir → şifreli saklanmalı (yapılmadı, 10. bölüm) |

### 8.2 Ölçeklenebilirlik (scalability) — ölçüldü

`python olcum/gecikme_olcumu.py 60` (demo verisi; 4 çekirdekli Linux, Python 3.13; Flask test istemcisi, yalnızca sunucu süresi, ms):

| İstek | p50 | p95 | En kötü |
|---|---|---|---|
| Konu akışı | 11,5 | 16,2 | 17,4 |
| Konu sayfası (27 mesaj) | 8,6 | 9,6 | 10,0 |
| Oylama sayfası | 3,9 | 4,2 | 4,5 |
| Kayıt defteri | 4,7 | 5,2 | 6,2 |
| Üye ağı | 4,8 | 5,0 | 5,8 |
| API: konu listesi | 2,3 | 2,5 | 2,6 |
| Oy verme (commit + 3 düğüme yazım) | 7,8 | 9,4 | 12,3 |

**Defter büyüyünce (bulundu ve düzeltildi).** `--defter-blok` ile defter yapay olarak büyütüldü. Önceden her yazma ve her defter
sayfası üç düğümün bütün zincirini baştan okuyup SHA-256 ile yeniden doğruluyordu (O(n)):

| Defterdeki blok | Oy verme p95 — önce | Oy verme p95 — şimdi | Defter sayfası p95 — önce | şimdi |
|---|---|---|---|---|
| ~600 (demo) | 18,6 | 9,4 | 14,1 | 5,2 |
| +10.000 | 148,3 | 8,1 | 272,1 | 5,8 |
| +50.000 | **645,2** | **11,4** | **1.145,5** | **8,5** |

Düzeltme (`defter.py`): düğüm başına tam doğrulamanın sonucu, düğümün **sürümüyle** (SQLite dosya başlığındaki değişiklik sayacı)
birlikte saklanır; sürüm değişmedikçe zincir yeniden doğrulanmaz, yazma yalnızca son bloğu okur. Dışarıdan yapılan her değişiklik
sürümü değiştirdiği için kurcalama yine yakalanır (testli). Repository deseni sayesinde değişiklik tek dosyada kaldı.

**Konu sayısı büyüyünce.** 1.019 konuda (1.000 kopya eklenerek, 10 istek): konu akışı p50 77 → **51 ms** (en kötü 151 ms).
Zamanın çoğu yan paneldeki "öne çıkan kelimeler" hesabındaydı; aynı kelimenin binlerce kez yeniden katlanması kaldırıldı.

**Bilinen sınırlar:**
- Öne çıkan kelimeler hâlâ son 7 günün bütün metnini her istekte işliyor (O(metin)). Sonraki adım: konu/mesaj yazılınca artımlı sayım.
- Sunucu yeniden başlayınca her düğüm bir kez tam doğrulanır (50.000 blokta yaklaşık yarım saniye, yalnızca ilk istekte).
- SQLite tek yazar: yazan istekler sıraya girer. Bir oy ~10 ms → saniyede ~100 yazma. Daha fazlası için PostgreSQL ve
  defterin ayrı bir hizmete taşınması gerekir (Repository arayüzü buna hazır).

### 8.3 Sürdürülebilirlik (maintainability)

- Tasarım desenleri ve SOLID eşlemesi: `docs/tasarim.md` 8. bölüm (her desen dosya adıyla).
- 172 otomatik test (~7 sn); ölçüm betikleri; her düzeltmenin önce hatayı üreten testi (`testler/test_duzeltmeler.py`).
- Bağımlılık sürümleri sabit; gizli anahtar kodda değil; ayarlar ortam değişkeniyle (README).

### 8.4 Uyarlanabilirlik (adaptability) — "hizmeti kesmeden uyum"

| Değişiklik | Kod değişikliği gerekir mi? |
|---|---|
| Eşik, süre, ağırlık, yeter sayı | Hayır: yönetmelik oylamasıyla (parametreler veritabanında, anlamlı aralıklarla sınırlı) |
| Denetim maddesinin sertliği (Engeller / Uyarır / Kapalı) | Hayır: oylamayla |
| Yeni kategori ve kavramları | Hayır: üyeler önerir, oylar; D3 yeni kavramları hemen kullanır |
| Yeni oylama türü | Bir sınıf (`teklif_turleri.py`'de `@kaydet`), mevcut kod değişmez (OCP) |
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
| Yönetici | Siteyi işletmek | Yönetim ↔ karar yetkisi | Yönetici yalnızca yönetir; kararı etkileyen işlem hiç tanımlı değil |
| Veri sahibi (KVKK) | Kişisel verinin korunması | Denetlenebilirlik ↔ mahremiyet | Deftere yalnızca özet/taahhüt; gizli oy; küçük görüş grupları gösterilmez (k-anonimlik ≥ 3) |
| Geliştirici / bakım | Değiştirilebilir kod | Özellik hızı ↔ kalite | Desenler, testler, ölçümler |
| Ders / değerlendirici | Analiz, desen, ölçüm | — | Bu belge ve `docs/tasarim.md` |

---

## 10. Ön-otopsi (pre-mortem, H2-47): "Altı ay sonra Agora başarısız oldu. Neden?"

O = olasılık, E = etki (Y yüksek, O orta, D düşük).

| # | Neden | O | E | Önlem | Durum |
|---|---|---|---|---|---|
| A | Bir grup oy devriyle gücü topladı | O | Y | Devir tavanı (MAX_DEVIR), döngü yasağı, koruyucu metrik Gini | Uygulandı, ölçülüyor |
| B | Sahte hesaplarla oylama ele geçirildi (Sybil) | O | Y | Bir adresten saatte en fazla 20 kayıt; yaş/konum kuralı | **Kısmi**: kimlik doğrulama yok. Gerçek kullanımda okul e-postası/e-Devlet doğrulaması gerekir |
| C | Kimse oy vermedi, turlar sonuçsuz kaldı | Y | Y | Bildirimler, oy devri, yeter sayı ayarı; metrik: yeter sayıya ulaşamayan tur oranı | Uygulandı, ölçülüyor |
| D | Denetim meşru mesajları engelledi, üyeler küstü | O | O | Ölçüm (6. bölüm), ciddiyet oylamayla UYARI'ya çekilebilir | Uygulandı; yanlış engel örnekleri belgelendi |
| E | YZ özeti yanlış sayı yazdı, karar etkilendi | D | Y | Kural tabanlı özet, sayılar veritabanından, kesme ile yuvarlama | Uygulandı, testli |
| F | Defter büyüdü, site yavaşladı | Y | O | Doğrulama önbelleği | **Bulundu ve düzeltildi** (8.2) |
| G | Yedek dosyası sızdı (gizli oylar + kişisel veri) | D | Y | Yedeği yalnızca yönetici indirir | **Açık risk**: yedek şifrelenmiyor |
| H | Tek fikir + çok çekimser oyla zayıf bir fikir "tek kalan" olarak karar oldu | O | O | Ödev şartnamesindeki kural; yeter sayı ve itiraz konusu dengeler | Bilerek korundu; izlenecek metrik: tek kalanla kabul edilen kararların oranı |
| I | Forum demo şifreleriyle yayına alındı | O | Y | Ağa açılırken uyarı; `--demo-verisiz` | Uygulandı |

---

## 11. Başarı tanımı ve yayın ölçütü (H2-43: "önceden yazılmalı")

Agora şu koşullarda yayına alınır; biri bozulursa yayın durur:

1. Bütün otomatik testler geçer (`python -m unittest discover testler`).
2. Denetim, test kümesinde: D1 F1 ≥ 0,80, D2 duyarlılık ≥ 0,80, D3 doğruluk ≥ 0,85 — ve her biri temel çizgileri geçer
   (`testler/test_olcum.py` bunu her çalıştırmada denetler).
3. Sunucu tarafı p95 < 200 ms: demo verisinde, 1.000 konuda ve 50.000 bloklu defterde.
4. Defter–veritabanı tutarsızlığı 0.

**Bir kuralı modelle değiştirme ölçütü:** model, *aynı test kümesinde* kuralı en az +0,10 F1 farkla geçmeli, p95 < 200 ms'yi
korumalı ve mesaj metnini dışarı göndermemeli. Aksi hâlde H2-37'deki "Senaryo B": birkaç puan için GPU, izleme ve yeniden eğitim
maliyeti değmez.

---

## 12. Bilerek yapılmayanlar (ödünleşimler)

| Konu | Neden yapılmadı | Ne zaman yapılmalı |
|---|---|---|
| BDM ile içerik özeti | 3. bölüm: halüsinasyon, KVKK, maliyet; ölçülmüş eksik yok | Etiketli onay verisi birikince, insan onaylı |
| ML tabanlı denetim | Etiketli veri yok | Gizleme oylaması/şikayet verisi birkaç yüz örneğe ulaşınca; bugünkü kural temel çizgi olur |
| Çok süreçli dağıtım | SQLite tek yazar; defter kilidi süreç içi | Saniyede ~100 yazmayı aşan kullanımda |
| Yedeğin şifrelenmesi | Kapsam | Gerçek kullanıma geçmeden önce |
| Kimlik doğrulama (Sybil'e karşı) | Ödev kapsamı dışı | Gerçek kullanıma geçmeden önce |
| Göç kodundaki eski sütunlar | Eski veritabanlarıyla uyum | Bütün kurulumlar yeni şemaya geçince |
