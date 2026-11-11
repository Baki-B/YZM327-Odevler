# Sunum: 5 dakika demo + 3 dakika soru

Ödevin istediği üç parça: **canlı bir `explain` örneği**, **doğrulama tablosu**, **bir yanlış seçimin analizi**.

## Hazırlık (sunumdan önce, bir kez)

```bash
cd vize
```

```bash
npm test
```

Terminal yazısını büyütün. `docs/rapor/Rapor.pdf` 4. ve 5. sayfaları (Şekil 1, doğrulama tablosu, Şekil 2) ayrı bir pencerede açık dursun.

## Akış

| Süre | Ne gösterilir | Ne söylenir |
|---|---|---|
| 0:00–0:40 | Raporun ilk sayfası | "Metinde desen aramanın onlarca algoritması var ve hiçbiri her durumda en hızlı değil. Yedi atom yazdık, bir de girdiye bakıp aralarından seçen bir molekül. Seçimi ölçümle kalibre edilmiş bir maliyet modeliyle yapıyoruz." |
| 0:40–1:40 | **Canlı explain** (komut 1, sonra 2) | Komut 1: "Lambda genomu, iki kısa desen. Şekil: n = 48 502, σ = 4, k = 2. Her atomun tahmini süresi burada; en ucuzu seçildi, gerekçesi `why` alanında." Komut 2: "Aynı molekül, ama şimdi 300 desen. Karar çok desenli bir atoma (Aho-Corasick ya da Wu-Manber) kayıyor. Molekülün koduna dokunmadık, girdi değişti." |
| 1:40–2:10 | **Şekil 1** (ızgara) | "180 vakada 8 atomu ölçtük. Çok desende Wu-Manber, kısa ve çok desende Aho-Corasick kazanıyor. Tek desende alfabe belirleyici: DNA'da blok kayması, kaynak kodda basit Horspool." |
| 2:10–3:10 | **Doğrulama tablosu** (rapor bölüm 6) | "Katsayıları hiç görmediği 120 vakada denedik: farklı tohum, ızgara arası değerler, log, ikili ve metin gibi yeni alfabeler. Molekül %85,8 en hızlıyı seçiyor; ortalama yavaşlama 1,016, en kötü 1,36×. En iyi tek atom 1,14 ve 2,3×, Allmer kuralı 3,14 ve 59×." |
| 3:10–4:20 | **Bir yanlış seçimin analizi** | Aşağıdaki "Yanlış seçim" kutusu. |
| 4:20–5:00 | Kod tarama (komut 3) + kapanış | "Hoca yazılım mühendisliğine uygulamamızı istedi: aynı molekül kaynak kodda TODO, gizli anahtar ve riskli API arıyor; `--fail` ile CI'da derlemeyi durdurabiliyor. 328 test, mutasyon denetiminde 12 hatanın 12'si yakalandı." |

### Komutlar

1. Lambda genomunda iki desen için karar:

```bash
node bin/ios.js explain --patterns GATC,GGATCC < tests/data/lambda_NC_001416.fa
```

2. Aynı genomda 300 desen için karar ve eşleşme sayısı:

```bash
node bin/ios.js run ExactMatch --patterns $(node -e "import('./bench/data.js').then(d=>{const fs=require('fs');const g=fs.readFileSync('tests/data/lambda_NC_001416.fa','utf8').split('\n').slice(1).join('');console.log(d.makePatterns(g,300,[6,10,16],12).join(','))})") < tests/data/lambda_NC_001416.fa | wc -l
```

3. Agora projesinde riskli API taraması:

```bash
node bin/ios.js scan --preset banned-api ../forum
```

### Yanlış seçim (anlatılacak örnek)

İki tane hazır. Zaman yetmezse yalnızca birincisini anlatın.

1. **v1'in hatası, düzeltildi:** DNA, 9 desen, uzunluklar 7/3/17. Model bm4DNAHMbs seçti (3,09 ms), en hızlı Aho-Corasick (0,51 ms), yani 6,1× yavaş. Neden: tek desenli algoritmaların maliyetini **ortalama** desen uzunluğuyla hesaplıyorduk. Ama toplam işi **en kısa** desen belirler: 3 harflik desende q-gram kayması ~1'e düşer. Çözüm: en kısa, ortalama ve en uzun uzunluğun ortalaması. Katsayılara dokunmadık; yalnızca özelliğin tanımı değişti.
2. **Hâlâ kalan hata:** Log dosyası, 10 desen, hepsi 3 karakter. Wu-Manber seçildi (5,4 ms), Aho-Corasick daha hızlıydı (4,0 ms), yani 1,36×. Neden: model metni tekdüze rastgele varsayıyor. Logda zaman damgası gibi tekrarlı parçalar var, Wu-Manber'in kova doğrulaması öngörülenden sık çalışıyor. Raporun 7. bölümünde sınır olarak yazılı.

## Olası sorular ve kısa yanıtlar

1. **Neden kural tabanlı değil de maliyet modeli?**
   Yeni atom eklendiğinde eşikleri elle yeniden düşünmek gerekmiyor. Atom kendi özelliklerini yazıyor, `npm run calibrate` katsayıları buluyor. Molekülün kodu değişmiyor.
2. **Doğrulama kümesine bakarak modeli düzelttiniz, bu hile değil mi?**
   Katsayıları hiç doğrulama verisiyle ayarlamadık; her seferinde yalnızca kalibrasyon ölçümlerinden uydurduk. Yine de iki özellik tanımını A kümesindeki hatalara bakarak düzelttik. Bu yüzden A'yı artık "görülmemiş" saymıyoruz. Son modeli hiçbir karar için kullanılmamış taze bir B kümesinde ayrıca ölçtük; tablodaki sayılar B'den.
3. **bm4DNAHMbs'de desende olmayan q-gram için neden m − q + 1?**
   Desen pencerenin son q − 1 karakterinden başlıyor olabilir. Örnek: desen ACGTAC, q = 3. Pencere "TTTxAC" iken son q-gram "xAC" desende yok, ama pencerenin sonundaki "AC" desenin başı. 6 kaysak eşleşmeyi atlarız; güvenli kayma 4.
4. **Atomlarda hazır `indexOf` kullanmadığınızı nasıl biliyoruz?**
   `forbidden.test.js` kaynak dosyaları tarıyor: indexOf, includes, RegExp, `.test(`, console, Node modülü, saat, rastgelelik. Taramanın kötü örnekleri gerçekten yakaladığını da ayrı bir test gösteriyor.
5. **Testleriniz gerçekten hata yakalıyor mu?**
   Mutasyon denetimi: koda 12 küçük hata yerleştirdik (kaymayı bir artırmak, `<` yerine `<=` vb.). 12'si de yakalandı (`docs/mutasyon.md`).
6. **Neden Boyer-Moore, Shift-Or, KMP hiç kazanmıyor?**
   Bu atomlar desen başına ayrı geçiyor. Çok desende Aho-Corasick ve Wu-Manber tek geçişte iş görüyor. Tek desende ise Horspool ailesinin atlaması daha ucuz. Shift-Or her karakteri okuyor; JavaScript'te bit işlemi ucuz ama atlamanın yerini tutmuyor.
7. **Allmer kuralı neden bu kadar kötü çıktı?**
   Kural tek desen ve DNA için tasarlanmış. Doğrulamada çok desen ve başka alfabeler var: bm4DNADS her desen için ayrı geçiyor. Ayrıca bu bizim JavaScript uygulamamız; C'deki özgün uygulama için genelleme yapmıyoruz.
8. **σe nedir, neden σ yetmiyor?**
   σe = 1/Σp², yani iki rastgele harfin aynı çıkma olasılığının tersi. Kaynak kodda 128 farklı karakter var, ama boşluk ve sık harfler yüzünden "etkin" alfabe 18. Beklenen kayma σe'ye bağlı.
9. **Karar neden yalnızca ilk kayda göre?**
   Sözleşme böyle istiyor; akış boyunca tek atom kullanılıyor. Sınırını raporda ve bir testte gösterdik: ilk kayıt kısa, sonrakiler uzunsa seçim kötü olabilir.
10. **Yeni bir atomu nasıl eklersiniz?**
    `src/atomic/` altına `ExactSearchAtom`'dan türeyen bir sınıf yazılır (manifest, selection, prepare, scanText) ve `registry.js`'teki listeye eklenir. Ardından `npm run calibrate` çalıştırılır. `molecule.test.js`, test içinde eklenen sahte bir atomun molekül değişmeden seçildiğini gösteriyor.
