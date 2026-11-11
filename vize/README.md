# Akıllı Tam Desen Eşleştirme (IoS: `sequence.pattern-match.exact`)

Vize projesi. Bir metin (genom, protein, kaynak kod, log) içinde bir ya da daha çok desenin geçtiği bütün yerleri bulan **yedi yeni atom** ve girdinin şekline bakıp bunlardan en hızlısını seçen **ExactMatch molekülü** içerir. Seçim, ölçümle kalibre edilmiş bir maliyet modeliyle yapılır. Modelin işe yaradığı, kalibrasyonda görülmemiş 120 vakada gösterildi.

Hocanın "yazılım mühendisliğine uygulayın" isteği için aynı molekül kaynak kod ve log dosyalarında da çalışır: `ios scan --preset todo src/`.

| Belge | İçinde |
|---|---|
| [docs/rapor/Rapor.pdf](docs/rapor/Rapor.pdf) | Rapor (IoS bileşen yayını biçiminde, 8 bölüm + ekler) |
| [bench/results/validation.md](bench/results/validation.md) | Doğrulama tablosu (120 görülmemiş vaka) |
| [bench/results/calibration-fit.md](bench/results/calibration-fit.md) | Kalibrasyon katsayıları ve uydurma kalitesi |
| [docs/sapmalar.md](docs/sapmalar.md) | Allmer 2016'dan ve klasik tariflerden sapmalar, gerekçeleriyle |
| [docs/mutasyon.md](docs/mutasyon.md) | Mutasyon denetimi: testler bilerek konan hataları yakalıyor mu? |
| [docs/anlatim.md](docs/anlatim.md) | Her dosyanın ve algoritmanın sade anlatımı (sunum hazırlığı için) |
| [docs/sunum.md](docs/sunum.md) | 5 dakikalık sunum akışı ve olası sorular |
| [KARARLAR.md](KARARLAR.md) | Ödev metninin açık bıraktığı noktalarda verilen kararlar |

## Kurulum

Node.js 22 ya da üstü yeterlidir. Hiçbir npm paketi kullanılmaz; `npm install` gerekmez.

```bash
node --version
```

## Komutlar

| Komut | Ne yapar | Süre (bu makinede) |
|---|---|---|
| `npm test` | 328 birim testi: sözleşme, özel durumlar, oracle karşılaştırması (gerçek + sentetik + 360 rastgele vaka), molekül, komut satırı, yasaklı işlev taraması | ~3 sn |
| `npm run calibrate` | Kalibrasyon ızgarasını ölçer (180 vaka × 8 atom), katsayıları `src/molecules/coefficients.json` dosyasına yazar | ~3 dk |
| `npm run bench` | Doğrulama: 120 görülmemiş vaka, politikaların karşılaştırması → `bench/results/validation.md` | ~10 dk |
| `npm run figures` | Rapor şekillerini ölçüm dosyalarından üretir (`docs/rapor/*.svg`) | 1 sn |
| `npm run mutation` | Mutasyon denetimi → `docs/mutasyon.md` | ~1 dk |
| `npm run report` | `docs/rapor/rapor.html` → `docs/rapor/Rapor.pdf` (Playwright + Chromium gerekir; yalnızca bu komut için) | 5 sn |

Ölçüm yaparken makinede başka ağır iş çalışmamalı. Sonuçlar makineye bağlıdır: teslimden önce `npm run calibrate` ve ardından `npm run bench` kendi bilgisayarınızda yeniden çalıştırılmalıdır.

## Komut satırı

```bash
node bin/ios.js run ExactMatch --patterns GATC,GGATCC --strategy auto < tests/data/lambda_NC_001416.fa > cikti.jsonl
```

```bash
node bin/ios.js explain --patterns GATC,GGATCC < tests/data/lambda_NC_001416.fa
```

```bash
node bin/ios.js run HorspoolSearch --patterns acgt --ignoreCase < girdi.fasta
```

```bash
node bin/ios.js scan --preset todo ../forum
```

- `run`: stdout'a satır başına bir `Sequence.Match` (JSONL) yazar; karar özeti stderr'e gider. Bileşen adı `ExactMatch` ya da bir atomun adı olabilir.
- `explain`: yalnızca molekülün kararını (`record`) JSON olarak yazar.
- `scan`: dosya ya da klasörlerde arar; çıktı `dosya:satır:sütun: desen`. Hazır kümeler: `todo`, `secrets`, `banned-api`, `errors`. Diğer seçenekler: `--json` (JSONL çıktı), `--fail` (bulgu varsa çıkış kodu 1, sürekli entegrasyonda kullanmak için).
- `list`: kayıtlı atomları listeler.

Kod içinden kullanım:

```js
import { ExactMatch } from './src/molecules/ExactMatch.js';
const em = new ExactMatch({ patterns: ['ACGT', 'GGCC'], ignoreCase: false, strategy: 'auto' });
for (const match of em.run(entries)) console.log(match);
console.log(em.record); // { requested, selected, shape, estimates, why }
```

## Depo yapısı

```
src/functions/   algoritma çekirdekleri (saf; yalnızca sayı dizileri üzerinde çalışır)
src/atomic/      atom sınıfları: manifest + selection + process (ExactSearchAtom ortak sınıf)
src/molecules/   ExactMatch.js (molekül), costModel.js (tahmin + NNLS), coefficients.json
src/registry.js  kayıt defteri: yeni atom eklemek molekülü değiştirmez
src/shape.js     veri şekli: n, σ, σe, k, mMin, mMax, mMean
src/adapters/    kaynak dosya → FASTA.Entry uyarlayıcısı
src/workflows/   CodeScan (kaynak kod / log tarama) ve hazır desen kümeleri
bin/ios.js       komut satırı
bench/           veri üretici (data.js), zaman ölçümü (timing.js), kod korpusu, sonuçlar (results/)
tests/unit/      birim testleri (npm test)
tests/benchmarks/ kalibrasyon, doğrulama ve şekil betikleri
tests/data/      gerçek veri: lambda faj genomu, 126 E. coli K-12 proteini
docs/            rapor, sapmalar, mutasyon, anlatım, sunum
scripts/         korpus üretimi, mutasyon denetimi, PDF üretimi
```

## Yeni bir atom eklemek

1. Çekirdeği `src/functions/` altına yazın.
2. `ExactSearchAtom`'dan türeyen sınıfı `src/atomic/` altına yazın. Sınıf `manifest`, `selection.features`, `selection.defaults` ve gerekirse `selection.applicable` alanlarını, ayrıca `prepare()` ve `scanText()` yöntemlerini içerir.
3. `src/registry.js` içindeki `BUILTIN` listesine ekleyin ya da çalışma anında `registry.register(YeniAtom)` çağırın.
4. `npm run calibrate` çalıştırın.

`ExactMatch.js` değişmez. Bunu `tests/unit/molecule.test.js` içindeki sahte atom testi gösterir.

## Veri kaynakları

- **Lambda faj genomu:** NC_001416.1, 48 502 baz. `tests/data/lambda_NC_001416.fa` (bowtie2 deposundaki örnek dosya, NCBI kaydının kopyası).
- **E. coli K-12 proteinleri:** 126 UniProtKB/Swiss-Prot kaydı (OX=83333), erişim numarasına göre ilk 126. `tests/data/ecoli_k12_126_proteins.fasta`; her kaydın kaynağı yanındaki `.kaynak.tsv` dosyasında.
- **Kaynak kod korpusu:** bu deponun kendi Agora projesi (`forum/`, `testler/`, `tarayici/`, `olcum/`, `laboratuvar/`). `bench/corpus/kod.txt`, `scripts/korpus.js` ile üretilir.

## Katkılar

| Kişi | Katkı |
|---|---|
| Baki | Proje sahibi; kararların onayı, ölçümlerin kendi makinesinde yenilenmesi, sunum |

**Yapay zekâ kullanımı:** Kod, testler, ölçüm betikleri, rapor ve belgeler bir yapay zekâ kodlama aracıyla (Claude Code) üretildi. Ders politikası (izinli / kısıtlı / yasak) henüz belli değil; öğrenilince bu bölüm ve raporun ilgili kısmı güncellenmeli. Sunumda her bölümün anlatılabilmesi için [docs/anlatim.md](docs/anlatim.md) hazırlandı.
