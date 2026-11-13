# Sunum: 5 dakika demo + 3 dakika soru

Ödevin istediği üç parça: **canlı bir `explain` örneği** (artık atölyede, molekülün karar kaydı olarak), **doğrulama tablosu**, **bir yanlış seçimin analizi**. Slaytlar: [`docs/sunum/index.html`](sunum/index.html) (10 slayt, ← → ile ilerler, `P` ile PDF'ye yazdırılır). Slaytlardaki sayılar `node scripts/site-uret.js` ile `bench/results/` dosyalarından üretilir.

## Hazırlık (sunumdan önce, bir kez)

```bash
cd vize
```

```bash
npm test
```

```bash
npm run web
```

Tarayıcıda iki sekme açın: `http://localhost:8327/docs/sunum/` (slaytlar) ve `http://localhost:8327/web/#paket=tek-desen` (atölye). Atölyede bir kez "Tarayıcıda çalıştır"a basıp örnek verinin önbelleğe girmesini sağlayın. İnternet gerekmez.

Yedek: atölye açılmazsa aynı kararı terminalde gösterin (aşağıdaki "Yedek komutlar").

## Akış

| Süre | Slayt / ekran | Ne söylenir |
|---|---|---|
| 0:00–0:30 | 1–2 Problem | "Metinde desen aramanın onlarca algoritması var ve hiçbiri her durumda en hızlı değil. Sekiz atom ve girdiye bakıp aralarından seçen bir molekül yazdık." |
| 0:30–1:00 | 3 IoS → yazılım mühendisliği | "IoS biyoloji için atom ve molekül fikrini kuruyor. Biz aynı bileşenleri kaynak koda ve loga taşıdık: bir uyarlayıcı dosyayı FASTA kaydına çeviriyor, atomlara dokunmuyoruz." |
| 1:00–1:30 | 4–5 Atomlar, maliyet modeli | "Her atom kendi 'adım sayısı' özelliklerini veriyor; katsayıları 180 vakalık ızgarada ölçerek bulduk. Molekül en ucuz tahmini seçiyor ve nedenini kaydediyor." |
| 1:30–2:50 | 6 → **CANLI atölye** | Aşağıdaki "Canlı demo". |
| 2:50–3:40 | 7 Doğrulama (D) | "Hiç görmediği 120 vakada molekülün seçtiği atom %76,7 en hızlı; ortalama yavaşlama 1,051, en kötü 2,00×. Karar süresi dahil uçtan uca 0,990. Hep Wu-Manber 1,131 ve 2,78×, Allmer kuralı 2,543 ve 18,71×." |
| 3:40–4:20 | 8 Yanlış seçim | Aşağıdaki "Yanlış seçim". |
| 4:20–4:45 | 9 Sınırlar | "Tek desende seçim zayıf ve uçtan uca hep Horspool'un gerisindeyiz. Ölçüm düzeneğimiz küçük karar süresini ayıramadı; bunu ayrıca ölçtük." |
| 4:45–5:00 | 10 Ekip | Katkılar, yapay zekâ kullanımı. |

### Canlı demo (atölye, ~80 sn)

1. Sol panel → **# tek-desen-büyük-dosya**. "Aynı 880 KB kaynak kod dosyası, iki dal: üstte tek desen, altta 16 Python anahtar sözcüğü."
2. **Tarayıcıda çalıştır.** Rozet: "bitti: 8 597 bulgu" (882 + 7 715). "Arama tarayıcıda, Web Worker içinde; algoritmalar `src/` modüllerinin kendisi, kopya değil."
3. Alt daldaki **ExactMatch** kutusuna tıklayın. Sağ panel = `explain` çıktısı: "Şekil: n = 881 771, σ = 111 ama etkin alfabe 19,7; k = 16. Her atomun tahmini süresi burada. Seçilen Aho-Corasick; gerekçe 'neden' kutusunda." Üst daldaki molekül tek desende bm4DNADS seçti: "Girdi değişti, kod değişmedi, karar değişti."
4. **Atomları yarıştır.** "Aynı girdide sekiz atomu tarayıcıda ölçüyor, tahminle yan yana koyuyor. Bu ölçüm gösterim amaçlı; rapordaki sayılar Node ölçümleri."
5. (Zaman kalırsa) **# gizli-bilgi-sızıntısı** → çalıştır: rozet kırmızı "kapı kaldı". "Sürekli entegrasyonda derlemeyi durduran kural: `ios scan --fail`." **Açıkla** düğmesi iş akışını Türkçe cümlelerle anlatır.
6. Bir kutuyu yanlış yere bağlamayı deneyin (ör. "Örnek veri" çıkışı → ExactMatch "kayıtlar" girişi): "Tür uyuşmuyor; araya uyarlayıcı koyun" uyarısı.

### Yanlış seçim (anlatılacak örnek)

**D, vaka 119:** İngilizce benzeri metin (kalibrasyonda olmayan alfabe), n = 531 186, k = 24, desen uzunlukları 92/37/150. Model bm4DNAHMbs seçti: tahmin 7,23 ms, ölçülen 12,57 ms. En hızlı Wu-Manber: tahmin 11,17 ms, ölçülen 6,28 ms. Yavaşlama 2,00×.

- İki tahmin **ters yönde** yanıldı: seçilen atomunki 1,74 kat az, en hızlınınki 1,78 kat fazla.
- Olası neden: model metni tekdüze rastgele sayıyor. Kelimelerden oluşan metinde sık geçen q-gramlar desende de geçer; q-gram kayması öngörülenden kısa kalır.
- Dürüstlük: bu vakayı gördükten sonra modeli değiştirmedik. Değiştirseydik yeni bir taze kümede yeniden ölçmemiz gerekirdi.

Yedek örnek (eski, düzeltilmiş hata): v1'de karışık uzunlukta desenlerde maliyet ortalama uzunlukla hesaplanıyordu; A kümesinde 6,1× yavaşlama. v2'de en kısa / ortalama / en uzun desenin ortalaması kullanıldı.

## Yedek komutlar (atölye açılmazsa)

1. Lambda genomunda iki desen için karar:

```bash
node bin/ios.js explain --patterns GATC,GGATCC < tests/data/lambda_NC_001416.fa
```

2. Büyük dosyada tek desen ve 16 desen (seçilen atom stderr'de):

```bash
node bin/ios.js scan --patterns return bench/corpus/kod.txt > /dev/null
```

```bash
node bin/ios.js scan --patterns def,class,return,import,self,lambda,yield,await,async,raise,except,finally,while,elif,assert,global bench/corpus/kod.txt > /dev/null
```

3. Agora projesinde riskli API taraması:

```bash
node bin/ios.js scan --preset banned-api ../forum
```

## Olası sorular ve kısa yanıtlar

1. **Neden kural tabanlı değil de maliyet modeli?**
   Yeni atom eklendiğinde eşikleri elle yeniden düşünmek gerekmiyor. Atom kendi özelliklerini yazıyor, `npm run calibrate` katsayıları buluyor. Molekülün kodu değişmiyor.
2. **Doğrulama kümesine bakarak modeli düzelttiniz, bu hile değil mi?**
   Katsayıları hiç doğrulama verisiyle ayarlamadık. Model her değiştiğinde (v2, v3, v4) yeni bir taze kümede ölçtük ve o kümeyi yalnızca bir kez ölçtük. Son model v4'ün kümeleri D ve E; tablodaki sayılar oradan. Eski kümeler (A, B, C) ve sonuçları silinmedi, sürüm tablosunda duruyor.
3. **v4'te ne değişti?**
   Teslim öncesi denetimde molekülün karar için metni 262 144 karaktere kadar saydığını, küçük ve tek desenli girdide bunun aramanın kendisi kadar sürdüğünü bulduk. v4 en fazla 64 × 256 karakter sayıyor: şekil hesabı D'de medyanda 0,648 ms'den 0,063 ms'ye indi. Örneklemin σe hatası medyanda %0,15, en kötü %7,00 (D).
4. **Uçtan uca yavaşlama nasıl 1'in altında (0,990)?**
   Olamaz; ölçüm sapması. Molekül, seçtiği atomun tek başına süresinden medyanda kısa ölçüldü (oran 0,951). İki gürültülü sürenin farkı küçük karar süresini ayıramıyor. Bu yüzden karar adımını ayrıca, tek başına ölçtük: medyanda 0,116 ms, seçilen atomun süresinin %4,1'i kadar (D), tek desende %11,4 (E).
5. **Hep Wu-Manber kullansak daha mı iyi?**
   Çok desende hayır: D'de hep Wu-Manber 1,131 ve en kötü 2,78×; molekülün seçtiği atom 1,051 ve 2,00×, uçtan uca 0,990. Tek desende (E) ise dürüst cevap evet sayılır: molekül uçtan uca 1,300, hep Horspool 1,198, Allmer kuralı 1,192.
6. **v3'ten (B: 1,016) neden daha kötü (D: 1,051)?**
   Bilmiyoruz ve ayıramıyoruz: v4 farklı bir makinede ölçüldü (eski makine 2,30 GHz, yeni 2,10 GHz; yeni makinede aynı ölçümler medyanda 1,74 kat yavaş ve daha gürültülü). Sonucu düzeltmeye çalışmadık, olduğu gibi raporladık.
7. **bm4DNAHMbs'de desende olmayan q-gram için neden m − q + 1?**
   Desen pencerenin son q − 1 karakterinden başlıyor olabilir. Örnek: desen ACGTAC, q = 3. Pencere "TTTxAC" iken son q-gram "xAC" desende yok, ama pencerenin sonundaki "AC" desenin başı. 6 kaysak eşleşmeyi atlarız; güvenli kayma 4.
8. **Atomlarda hazır `indexOf` kullanmadığınızı nasıl biliyoruz?**
   `forbidden.test.js` kaynak dosyaları tarıyor: indexOf, includes, RegExp, `.test(`, console, Node modülü, saat, rastgelelik. Taramanın kötü örnekleri gerçekten yakaladığını da ayrı bir test gösteriyor.
9. **Testleriniz gerçekten hata yakalıyor mu?**
   Mutasyon denetimi: koda 12 küçük hata yerleştirdik (kaymayı bir artırmak, `<` yerine `<=` vb.). 12'si de yakalandı (`docs/mutasyon.md`).
10. **Atölye algoritmaları kopyalıyor mu?**
    Hayır. `web/` doğrudan `../src/` altındaki kayıt defterini, molekülü ve uyarlayıcıları içe aktarıyor. İş akışı motoru (`src/workflows/engine.js`) DOM'suz ve `node:test` ile test ediliyor. Altı hazır paketin her birinde atölyenin bulgu sayısı komut satırınınkiyle aynı (`npm run paketler`, `scripts/arayuz-denetimi.js`).
11. **Uyumsuz bağlantı nasıl engelleniyor?**
    Her ucun bir türü var (Source.File, FASTA.Entry, Pattern.Set, Sequence.Match, Finding). Motor yalnızca aynı türdeki uçları bağlıyor, döngüye ve tek girişli uca ikinci bağlantıya izin vermiyor; nedeni Türkçe cümleyle söylüyor.
12. **Karar neden yalnızca ilk kayda göre?**
    Sözleşme böyle istiyor; akış boyunca tek atom kullanılıyor. Kod taramasında ilk dosya küçükse seçim kötü olabilir; raporda sınır olarak yazılı.
13. **Yeni bir atomu nasıl eklersiniz?**
    `src/atomic/` altına `ExactSearchAtom`'dan türeyen bir sınıf yazılır ve `registry.js`'teki listeye eklenir, sonra `npm run calibrate`. Atölyede de kendiliğinden bir kutu olarak görünür; bunu `engine.test.js`'teki sahte atom testi gösteriyor.
