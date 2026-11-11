# Ödev kontrol listesi

Ödev metnindeki (bölüm 4, 6, 7, 9) her madde ve karşılığı.

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
| 4.2 Doğrulama ≥ 100 görülmemiş vaka, ara değerler, yeni alfabe | 120 (A) + 120 (taze B) | `tests/benchmarks/validate.js`, `bench/results/validation*.json` |
| 4.3 Karşılaştırma: her zaman X, Allmer kuralı | yapıldı | `bench/results/validation-taze.md` |
| 4.4 Ölçütler (en hızlı oranı, %10, geo. ort., en kötü, toplam oran) | yapıldı | aynı dosya |
| Ölçüm kuralları: ısınma, ≥ 3 tekrar medyan, makine bilgisi | ısınma + 5 tekrar, dönüşümlü | `bench/timing.js`; makine bilgisi sonuç dosyalarında |
| 5. Rapor ≤ 6 sayfa + ekler, 8 bölüm, şekil (m × k haritası), yanlış seçim analizi | ana metin 6 sayfa + 2 sayfa ek | `docs/rapor/Rapor.pdf` |

## Teslim edilecekler (bölüm 7)

| Kalem | Durum | Nerede |
|---|---|---|
| Kod deposu ve commit geçmişi | yapıldı | bu depo, `vize/` |
| README: kurulum, npm test, calibrate, bench, katkılar | yapıldı | `README.md` |
| Ham ölçümler (JSON) ve doğrulama tablosu | yapıldı | `bench/results/` |
| Rapor PDF | yapıldı | `docs/rapor/Rapor.pdf` |
| Sunum hazırlığı | yapıldı | `docs/sunum.md`, `docs/anlatim.md` |
| Depo yapısı (src/functions, src/atomic, src/molecules/ExactMatch.js, src/registry.js, src/shape.js, bin/ios.js, bench/, tests/unit/, tests/benchmarks/) | yapıldı | README "Depo yapısı" |
| `npm test` temiz kopyada, bağımlılıksız | 328/328 | temiz klonda denendi |

## Bonus (bölüm 9)

| Bonus | Durum |
|---|---|
| İleri atom (Wu-Manber), molekülde seçilebilir ve testli | yapıldı; doğrulamada en sık seçilen atom |
| Performans yarışması | gizli kümeye bağlı; ölçülemez |

## Kullanıcının yapması gerekenler

- Hocadan başlangıç paketini isteyin. Gelirse aynı adlı dosyaları değiştirip `npm test` çalıştırın.
- Yapay zekâ politikasını öğrenip README ve rapor Ek F'yi güncelleyin.
- Teslimden önce kendi bilgisayarınızda `npm run calibrate`, `npm run bench`, taze küme komutunu ve ardından `npm run figures`, `npm run report` çalıştırın. Rapordaki sayıları yeni `bench/results/*.md` dosyalarına göre güncelleyin.
- Ders kodu, öğretim elemanı ve grup bilgilerini rapor başlığına ekleyin.
