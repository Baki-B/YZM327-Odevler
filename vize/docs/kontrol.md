# Ödev kontrol listesi

Ödev metnindeki (bölüm 4, 6, 7, 9) her madde, hocanın netleştirmeleri ve karşılıkları.

## Teknik sözleşme (bölüm 4)

| Madde | Durum | Nerede |
|---|---|---|
| Node 22+, ES modülleri, npm paketi yok, `node:test` | yapıldı | `package.json` |
| Girdi/çıktı biçimi, 0 tabanlı UTF-16 konum, örtüşme, sıra, tekrar eden desen, pattern verildiği gibi | yapıldı | `src/atomic/ExactSearchAtom.js`, `src/functions/hits.js`; test: `tests/unit/contract.test.js` |
| ignoreCase yalnızca ASCII | yapıldı | `src/functions/alphabet.js`; test: contract "ignoreCase" |
| Desen metinden uzun / boş metin → boş; boş liste / boş desen → hata | yapıldı | `ExactSearchAtom.js` (`validateParams`) |
| Atom arayüzü: manifest, selection (features, defaults, applicable), constructor, `*process` | yapıldı | `src/atomic/*.js` |
| Atomda console, dosya, ağ, hazır arama işlevi yok; deterministik | yapıldı | test: `tests/unit/forbidden.test.js` |
| Molekül: `strategy` auto / atom adı, bilinmeyen ad → geçerli seçenekler, `record` | yapıldı | `src/molecules/ExactMatch.js`; test: `tests/unit/molecule.test.js` |
| Kayıt defteri, molekül değişmeden genişleme | yapıldı | `src/registry.js`; test: sahte atom |
| Komut satırı `run`, `explain` | yapıldı | `bin/ios.js`; test: `tests/unit/cli.test.js` |

## Görevler (bölüm 6)

| Görev | Durum | Nerede |
|---|---|---|
| 1. En az 4 yeni atom, A grubundan en az 2 | 7 atom (A: 4, B: 1, C: 2) | `src/functions/`, `src/atomic/` |
| 1. Makaleden sapmalar kodda ve raporda | yapıldı (makale PDF'ine erişilemedi, açıkça yazıldı) | `docs/sapmalar.md`, rapor bölüm 2 ve Ek A |
| 1. Atom başına en az 5 özel durum testi | 16 durum × 8 atom | `tests/unit/atoms.test.js` |
| 2. Lambda (kısa, uzun, çok desen) ve E. coli | yapıldı (gerçek veri) | `tests/data/`, `tests/unit/oracle.test.js` |
| 2. Sentetik: DNA, protein, metin, ikili, tekrarlı | yapıldı (+ kaynak kod, log) | `oracle.test.js` |
| 2. Karışık uzunluk, tekrar eden desen, çok kayıt, ignoreCase | yapıldı | `oracle.test.js` |
| 2. En az 300 tohumlu rastgele vaka | 360 | `oracle.test.js` |
| 3. Molekül, şekil (n, σ, k, mMin, mMax, mMean) | yapıldı (+ σe) | `src/shape.js` |
| 3. Seçim yöntemi gerekçeli | maliyet modeli | rapor bölüm 4 |
| 3. Molekül testleri (record, en ucuz, zorla seçilen, sahte atom, uygulanamaz) | yapıldı | `molecule.test.js` |
| 4.1 Kalibrasyon ≥ 3 alfabe × 3 n × 5 m × 4 k | 3 × 3 × 5 × 4 = 180 | `tests/benchmarks/calibrate.js`, `bench/results/calibration.json` |
| 4.2 Doğrulama ≥ 100 görülmemiş vaka, ara değerler, yeni alfabe | v4: 120 (taze D) + 120 (taze E, k = 1); v3: A, B, C (saklandı) | `tests/benchmarks/validate.js`, `bench/results/validation*.json` |
| 4.3 Karşılaştırma: her zaman X, Allmer kuralı (+ molekül uçtan uca) | yapıldı | `bench/results/validation-d.md`, `validation-e.md` |
| 4.4 Ölçütler (en hızlı oranı, %10, geo. ort., en kötü, toplam oran) | yapıldı | aynı dosya |
| Ölçüm kuralları: ısınma, ≥ 3 tekrar medyan, makine bilgisi | ısınma + 5 tekrar, dönüşümlü | `bench/timing.js`; makine bilgisi sonuç dosyalarında |
| 5. Rapor ≤ 6 sayfa + ekler, 8 bölüm, şekil (m × k haritası), yanlış seçim analizi | ana metin 5 sayfa + ekler (gereksinimler, SOLID, test stratejisi, 7 UML diyagramı) | `docs/rapor/Rapor.pdf` |

## Teslim edilecekler (bölüm 7)

| Kalem | Durum | Nerede |
|---|---|---|
| Kod deposu ve commit geçmişi | yapıldı | bu depo, `vize/` |
| README: kurulum, npm test, calibrate, bench, katkılar | yapıldı | `README.md` |
| Ham ölçümler (JSON) ve doğrulama tablosu | yapıldı | `bench/results/` |
| Rapor PDF | yapıldı | `docs/rapor/Rapor.pdf` |
| Sunum | 10 slayt + konuşma notları; canlı demo atölyede | `docs/sunum/index.html`, `docs/sunum.md`, `docs/anlatim.md` |
| Site | yapıldı (sayılar sonuç dosyalarından üretilir) | `site/`, `scripts/site-uret.js` |
| Arayüz (Kod Bilimi Atölyesi) | yapıldı; 29/29 tarayıcı denetimi | `web/`, `scripts/arayuz-denetimi.js` |
| UML diyagramları | 7 diyagram (kullanım durumu, 2 sınıf, 3 sıralı, paket) | `docs/uml/` |
| Depo yapısı (src/functions, src/atomic, src/molecules/ExactMatch.js, src/registry.js, src/shape.js, bin/ios.js, bench/, tests/unit/, tests/benchmarks/) | yapıldı | README "Depo yapısı" |
| `npm test` temiz kopyada, bağımlılıksız | 360/360 | temiz klonda denendi |

## Bonus (bölüm 9)

| Bonus | Durum |
|---|---|
| İleri atom (Wu-Manber), molekülde seçilebilir ve testli | yapıldı; doğrulamada en sık seçilen atom |
| Performans yarışması | gizli kümeye bağlı; ölçülemez |

## Hocanın netleştirmeleri

| Netleştirme | Karşılığı |
|---|---|
| Arayüz önemli; örnek IoS iş akışı düzenleyicisi | Kod Bilimi Atölyesi (`web/`): kategorili bileşen listesi, noktalı tuval, uçlu kutular, özellikler paneli, ad + hedef + çalıştır + durum rozeti + Açıkla |
| IoS fikri yazılım mühendisliğine uygulanacak | Ana konu kaynak kod ve log taraması (5 paket), biyoloji ikincil (1 paket) |
| Başlangıç paketi verilmeyecek | Paket verilmedi, karşılığı yazıldı; proje kendi başına çalışır |
| Yapay zekâ serbest | README ve rapor Ek F |
| Teslim: rapor, sunum, site, GitHub | `docs/rapor/Rapor.pdf`, `docs/sunum/index.html`, `site/`, bu depo |
| Grup çalışması | Katkı tablosu README, rapor, site ve slaytlarda; adlar köşeli parantezle boş |

## Kullanıcının yapması gerekenler

- Köşeli parantezli alanları doldurun: ders kodu ve adı, öğretim elemanı, üye adları, numaralar, katkılar (README, `docs/rapor/rapor.html`, `scripts/site-uret.js` içindeki ekip sayfası ve slaytlar; sonra `node scripts/site-uret.js` ve `npm run report`).
- GitHub Pages: `.github/workflows/sayfalar.yml` vize projesini yayınlar; dal `main`'e birleşince <https://baki-b.github.io/YZM327-Odevler/> güncellenir (README "GitHub Pages'te yayınlama").
- Teslim yapısı: README "Teslim yapısı" bölümündeki `git subtree split` önerisini uygulayıp uygulamamaya karar verin.

## Son denetim (11 Kasım 2026)

Teslim öncesi bütün iş yeniden denetlendi. Sonuçlar:

| Denetim | Sonuç |
|---|---|
| `npm test` | 328/328 geçti |
| Bağımsız rastgele karşılaştırma (projenin test yardımcıları ve NaiveSearch kullanılmadan, ayrı bir kaba kuvvet aramasıyla): 4 tohum, 39 000 vaka, 16 alfabe (Unicode, vekil çift, NUL, Türkçe harfler dahil), çok kayıt, ignoreCase, metinden uzun / tekrar eden desen, iç içe tüketilen üreteçler | ~795 000 karşılaştırma, **0 fark** |
| Büyük ve kötü huylu girdiler (2·10⁶ eşleşme, en kötü durum desenleri, k = 20 000, m = 5 000, 3·10⁶ karakter × 5 000 desen, 3 000 farklı CJK karakteri) | bütün atomlar NaiveSearch ile aynı |
| Komut satırı: `run`, `explain`, `scan` (4 hazır küme, `--json`, `--fail`), `list`, hata kodları; lambda'da sonuç Python ile ayrıca sayıldı (GATC 116 + GGATCC 5 = 121) | doğru |
| Doğrulama tabloları ham JSON'dan ayrı bir betikle yeniden hesaplandı | birebir aynı |
| Taze küme B'nin yalnızca bir kez ölçüldüğü (ölçüm günlükleri ve dosya tarihleri) | doğrulandı |
| Mutasyon denetimi yeniden çalıştırıldı | `docs/mutasyon.md` |
| Rapor: ana metin ≤ 6 sayfa | 6 + 2 ek sayfa |

Denetimde bulunan iki zayıflık rapora eklendi (bölüm 6–7). İkincisi v4'te uygulandı (aşağıda):

1. **Tek desende seçim zayıf.** B'de k en az 2'ydi. k = 1 için ek küme C ölçüldü: molekül %51,7 en hızlı, geo. ort. 1,073, en kötü 2,10×. Yine bütün politikalardan iyi (en iyi tek atom 1,224), ama fark küçük. En kötü vakaların hepsi ikili alfabede.
2. **Karar süresi tek desende ağır.** Molekül karar için metni bir kez sayıyor; tek desen araması metnin yalnızca bir kısmına baktığı için bu sayım aramayla aynı mertebede. Karar süresi dahil edilince B'de geo. ort. 1,187 olur, "her zaman Wu-Manber"in 1,139'undan kötü. Toplam süre oranında molekül yine iyi (1,169'a karşı 1,218). Çözüm önerisi (daha küçük örneklem) raporda; model doğrulamadan sonra değiştirilmedi.

### Bulgu 2'nin uygulanması (model v4, 13 Kasım 2026)

| Adım | Sonuç |
|---|---|
| `src/shape.js`: örneklem 64 parça × 256 karakter (16 384 karakterden uzun metinde) | şekil hesabı D'de medyanda 0,648 ms → 0,063 ms; σe hatası medyanda %0,15, en kötü %7,00 (`bench/results/karar-yuku-v4.md`) |
| Karar adımındaki diğer işler | profil: 8 atomun tahmini birlikte yaklaşık 0,02 ms; değiştirilmedi (KARARLAR 19) |
| Katsayılar | kalibrasyon bu makinede yeniden ölçüldü (233,9 s; makinede başka iş yokken) |
| Taze kümeler, birer kez | D (tohum 16180339, çok desen): seçilen atom 1,051 / en kötü 2,00×; uçtan uca 0,990 / 3,26×. E (tohum 14142135, k = 1): 1,081 / 2,06×; uçtan uca 1,300 |
| Dürüstlük | uçtan uca oranın 1'in altına düşmesi ölçüm sapması (D'de molekül / seçilen atom medyanı 0,951); karar süresi ayrıca ölçüldü: medyanda seçilen atom süresinin %4,1'i (D), %11,4'ü (E). Tek desende molekül uçtan uca hep Horspool (1,198) ve Allmer kuralının (1,192) gerisinde: olduğu gibi raporlandı |
| Eski sonuçlar | silinmedi; sürüm tablosunda v1–v4 (rapor bölüm 6, `site/sonuclar.html`) |
| İkili alfabede tek desen | düzeltilmedi; sınır olarak raporda |
