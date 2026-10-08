# Ders sunumlarındaki tartışma soruları

Ders sunumlarında "Tartışma sorusu" ya da "Tartışma ve çalışma soruları" diye sorulan sorulara kısa yanıtlar. Yanıtlar
mümkün olduğunca Agora'daki ölçülmüş sonuçlara bağlandı. Atıf biçimi: S01-24 = *YZ Mühendisliğine Giriş* 24. slayt.
Ödev olarak işaretli sorular (S02-50 mini laboratuvar ve S01-49 soru 6) ayrıca çalıştırıldı: `laboratuvar/README.md`.
TD-59'un iki tartışma sorusu `docs/tasarim.md` 8.7 ve 8.8'de.

## S01 — YZ Mühendisliğine Giriş

**S01-27. Hangi kullanım alanında YZ'nin hatası en pahalıdır; nerede insan denetimi zorunlu olmalı?**
Hatanın bedeli, çıktının bir *eyleme* ya da bir kişi hakkında *karara* dönüşüp dönüşmediğine bağlıdır. En pahalıları:
bilgi çıkarma ve belge işleme (yanlış okunan sözleşme ya da fatura doğrudan para ve hukuk demektir), iş akışı otomasyonu
(model bir işlemi kendisi yürütür; geri almak zordur) ve kurumsal soru-cevap (yanlış bilgi resmî yanıt gibi algılanır).
Kod üretiminin hatası testle yakalanabildiği, görüntü düzenlemenin hatası gözle görüldüğü için daha ucuzdur. İnsan
denetimi bir kişiyi etkileyen her kararda zorunlu olmalıdır. Agora bu ilkeyle kuruldu: YZ oy vermez, karar vermez, özetteki
sayıları kendisi üretmez; denetimde bile ölçülen güveni yetmeyen hakaret maddesi "engelle" yerine "uyar" düzeyine
çekildi (`docs/analiz.md` 6.5).

**S01-38. Öğrenci işleri asistanı hangi soruları asla kendi başına yanıtlamamalı?**
Bir öğrencinin haklarını ya da durumunu değiştiren her şey: not itirazı ve burs sonucu (slayttaki örnekler), disiplin
işlemleri, mezuniyet ve kayıt silme kararı, ders muafiyeti ve yönetmelikteki istisnalar (yönetmeliğin yorumu kişiye özel
sonuç doğurur), kişisel veri içeren sorgular (başkasının notu, adresi; KVKK) ve kriz belirtisi taşıyan mesajlar (sağlık,
psikolojik destek; bunlar hemen bir insana aktarılmalı). Asistan bu konularda bilgi verip ilgili birime yönlendirebilir
ama sonucu söyleyemez. Ölçüt: yanıt yanlışsa düzeltmesi kimin işi ve ne kadar zarar verir?

**S01-49 / 1. Öz-denetimli öğrenme neden dil modellerinin ölçeklenmesini mümkün kıldı?** Denetimli öğrenmede her örneği
bir insan etiketler; bu pahalı ve yavaştır (S01-11, ImageNet örneği). Öz-denetimde etiket verinin kendisidir: bir metinde
sonraki token, önceki tokenların etiketidir. Böylece internetteki bütün metin etiket maliyeti olmadan eğitim verisi olur;
veri miktarını sınırlayan şey insan emeği değil, hesaplama gücü olur.

**S01-49 / 2. Türkçe metinlerin daha çok token tüketmesinin maliyet ve gecikmeye etkisi nedir?** Ölçtük
(`laboratuvar/` 1. bölüm): aynı anlam Türkçede İngilizceden 1,36 (o200k) ile 1,69 (cl100k) kat daha çok token tutuyor.
API ücreti token başına alındığı için maliyet aynı oranda artar (S01-35: maliyet = istek × token × fiyat). Çıktı token
token üretildiği için yanıtın tamamlanma süresi de artar (TPOT × çıktı token sayısı, S01-34). Bağlam penceresine de daha az
Türkçe metin sığar. Bir dönemde 100.000 soru yanıtlayan bir öğrenci işleri botu için bu, faturanın %36–69 büyümesi demektir.

**S01-49 / 3. YZ mühendisliğini ML mühendisliğinden ayıran üç fark (S01-43).**
1. *Model yerine uyarlama:* ML mühendisi modeli kendi verisiyle eğitir; YZ mühendisi hazır bir temel modeli istem, bağlam
   ve ince ayarla uyarlar. Örnek: duygu analizi için sıfırdan sınıflandırıcı eğitmek yerine bir modele örnekli istem yazmak.
2. *Değerlendirme çok daha zor:* çıktı açık uçludur (özet, yanıt); tek doğru cevap yoktur. Örnek: Agora'nın kural tabanlı
   özetinde sayı sadakati bir testle denetlenebiliyor; serbest metin özetinde aynı denetim yapılamaz (`docs/analiz.md` 3).
3. *Çıkarım optimizasyonu ve sıra:* modeller büyük olduğu için gecikme ve maliyet ön plandadır; ve iş önce üründen başlar
   (demo → veri → model), geleneksel ML'deki veri → model → ürün sırasının tersine.

**S01-49 / 4. "Ortalama gecikme" neden yanıltıcıdır?** Ortalama birkaç uç değerle bozulur. Slayttaki örnekte (S01-24)
dokuz istek ~100 ms, biri 3.000 ms; ortalama 390 ms sistemi yavaş gösterir ama medyan 100 ms'dir. Tersine, ortalama iyi
görünürken yavaş kalan azınlık (çoğu zaman en çok verisi olan en değerli kullanıcılar) gizlenir. Bu yüzden Agora'da
p50, p95 ve en kötü değer ayrı raporlandı; yayın ölçütü p95 < 200 ms'dir (`docs/analiz.md` 8.2).

**S01-49 / 5. Üniversite için bir öğrenci işleri sohbet botu planı.**

| Soru | Karar |
|---|---|
| Gerekçe | Dönem başında çağrı merkezi tıkanıyor, basit soruların yanıtı günler sürüyor |
| YZ'nin rolü | Tamamlayıcı ve tepkisel: yönetmelik, takvim ve SSS'den kaynak göstererek yanıt verir (bilgi alma, RAG); karar vermez |
| İnsanın rolü | Kişiye özel sonuç doğuran her soru personele aktarılır (S01-38 listesi); emekle aşamasında her yanıtı personel onaylar |
| Emekle | Bot taslak yazar, personel onaylar. Ölçülen: taslağın değiştirilmeden onaylanma oranı |
| Yürü | Onay oranı 4 hafta boyunca ≥ %95 olan SSS kategorileri otomatik yanıtlanır; diğerleri onayda kalır |
| Koş | Öğrencilere açık, insan yalnızca aktarılan sorularda; yeni dönem takviminde onay aşamasına geri dönülür |
| İş metrikleri | Otomatik çözülen talep oranı, ilk yanıt süresi, çağrı merkezine düşen çağrı sayısı, öğrenci memnuniyeti |
| Kullanışlılık eşiği | Kaynağa dayalı doğru yanıt ≥ %95, yanlış tarih bilgisi %0 (koruyucu metrik), ilk tokena kadar süre < 2 sn |
| Riskler | Eski takvimden yanlış tarih, kişisel veri sızması, yönetmeliğin yanlış yorumu; her yanıt kaynağını gösterir |

**S01-49 / 6.** Uygulamalı soru; çalıştırıldı: `laboratuvar/README.md` 5. bölüm (16 testin 16'sı doğru, ama 10 hatadan biri
hiçbir testte yakalanmadı).

## S02 — Temel Modelleri Anlamak

**S02-28. Yazar HH-RLHF örneğinde "kaybeden" yanıtı daha çok beğeniyor. Bu, tercihleri tek bir formülle yakalamak hakkında
ne söyler?** İnsan tercihleri ortak değildir: etiketçiler arası uyum yalnızca ≈ %73. Tek bir ödül modeli bu anlaşmazlığı
ortalamaya indirger; azınlığın tercihi kaybolur ve "evrensel tercih" varsayımı gizlice bir grubun zevkini herkese uygular.
Agora'nın tasarımı aynı sorunun karar tarafıdır: toplu tercih tek bir formüle bırakılmadı; oylama kuralları açık,
azınlık itiraz konusu açabilir, korunan maddeler 3/4 ister, oy gücü tavanlı.

**S02-50 kavramsal sorular.**

1. *Seq2seq'in iki sorunu ve Transformer'ın çözümü (kitap benzetmesi):* (a) Darboğaz: kod çözücü bütün girdiyi tek bir son
   gizli durumdan görür; kitap hakkındaki soruyu yalnızca kitabın özetine bakarak yanıtlamak gibi. Dikkat mekanizması her
   adımda girdinin bütün tokenlarına bakar: istenen sayfayı açıp okumak gibi. (b) Sıralılık: RNN tokenları tek tek işler,
   paralelleşemez. Transformer'da bütün tokenlar tek bir matris çarpımıyla birlikte işlenir (S02-15, S02-13).
2. *Llama 2-13B bellek hesabı:* ağırlıklar 13 × 10⁹ × 2 bayt = 26 GB; ×1,2 kuralıyla çıkarım belleği ≈ **31,2 GB** (S02-20).
   Tek istek, 4.096 token için KV önbelleği = 2 × yığın × dizi × katman × model boyutu × bayt =
   2 × 1 × 4.096 × 40 × 5.120 × 2 = 3.355.443.200 bayt ≈ **3,4 GB** (S02-17'deki formül; aynı modelin 32'lik yığın ve
   2.048 tokenlık kitap örneği 54 GB).
3. *Mixtral 8x7B:* 8 uzman × 7B = 56B olurdu, ama dikkat katmanları ve gömmeler uzmanlar arasında paylaşıldığı için toplam
   46,7B'dir. Her token için katman başına yalnızca 2 uzman çalışır; token başına 12,9B parametre etkindir, bu yüzden hız ve
   maliyet 12,9B'lik bir modele yakındır. Bellekte ise 46,7B'nin tamamı durmalıdır (S02-21).
4. *Llama 3-8B neden ~100 kat fazla tokenla eğitildi?* Chinchilla yasası *eğitim* hesabını en iyi kullanan boyutu verir:
   parametre başına ≈ 20 token (8B için ≈ 160B token). Llama 3-8B ≈ 15T token gördü: parametre başına ≈ 1.900, yani ≈ 95 kat.
   Neden: model bir kez eğitilir ama milyonlarca kez çalıştırılır. Küçük modeli uzun eğitmek eğitimde israf görünür, ama
   çıkarım ucuzlar ve model tek GPU'ya sığar; toplam maliyet (eğitim + çıkarım) düşer (S02-24, Sardana vd.).
5. *Halüsinasyonun iki hipotezi (S02-43, 44):* Kendini aldatma: model kendi ürettiği yanlış bir başlangıcı olgu sayıp
   üzerine inşa eder (kartopu). Bilgi uyumsuzluğu: ince ayarda etiketçi modelin bilmediği bir bilgiyle yanıt yazınca modele
   "bilmediğini biliyormuş gibi söyle" öğretilir. RAG daha çok birincisini azaltır: model her adımda kendi tahminine değil,
   bağlama konmuş kaynağa dayanır (bilgi eksiğini de çıkarım anında kapatır). Daha iyi etiketleme ikincisini azaltır:
   etiketçi yalnızca modelin bildiğiyle yanıt yazar ve "bilmiyorum" yanıtını ödüllendirir.
