# Akıllı Tam Desen Eşleştirme ve Kod Bilimi Atölyesi (IoS: `sequence.pattern-match.exact`)

> **Taşındı:** Bu proje <https://github.com/Baki-B/YZM327-Odev-3> deposuna (kök düzeniyle, bu klasörün geçmişiyle) taşındı ve orada sürdürülüyor; site: <https://baki-b.github.io/YZM327-Odev-3/>. Bu klasör arşivdir.

Vize projesi (grup çalışması). Bir metinde (genom, protein, kaynak kod, log) bir ya da daha çok desenin geçtiği bütün yerleri bulan **yedi yeni atom** (+ Boyer-Moore), girdinin şekline bakıp en hızlısını seçen **ExactMatch molekülü** ve bunları yazılım mühendisliğinde kullanan tarayıcı tabanlı bir iş akışı düzenleyicisi: **Kod Bilimi Atölyesi**. Seçim, ölçümle kalibre edilmiş bir maliyet modeliyle yapılır.

**Sonuç (model v4, kalibrasyonda ve hiçbir kararda kullanılmamış taze kümeler, birer kez ölçüldü):**

- **Çok desen (D, 120 vaka):** molekülün seçtiği atom %76,7 en hızlı, %84,2 en hızlının %10 yakınında; yavaşlamanın geometrik ortalaması **1,051**, en kötü **2,00×**. Karar süresi dahil **uçtan uca**: **0,990**, en kötü 3,26×. En iyi tek atom (hep Wu-Manber) 1,131 ve 2,78×; Allmer 2016 kuralı 2,543 ve 18,71×.
- **Tek desen (E, 120 vaka):** seçilen atomla 1,081, en kötü 2,06×; uçtan uca 1,300. Burada molekül uçtan uca hep Horspool (1,198) ve Allmer kuralının (1,192) gerisinde.
- **Karar yükü:** v3'te karar için metin 262 144 karaktere kadar sayılıyordu; v4 en fazla 64 × 256 karakter sayar. Şekil hesabı D'de medyanda 0,648 ms'den 0,063 ms'ye indi; karar süresi / seçilen atomun süresi medyanda %4,1 (D), %11,4 (E). Uçtan uca oranın 1'in altına düşmesi ölçüm sapmasıdır (molekül, kendi seçtiği atomdan medyanda kısa ölçüldü: 0,951); bu yüzden karar süresi ayrıca ölçüldü.
- v3 (A, B, C) ile v4 (D, E) farklı makinelerde ölçüldü; yeni makine aynı ölçümleri medyanda 1,74 kat yavaş yaptı. Ayrıntı: rapor bölüm 6–7, [bench/results/makine-karsilastirma.md](bench/results/makine-karsilastirma.md).

## Teslim parçaları

| Parça | Nerede |
|---|---|
| **Rapor** | [docs/rapor/Rapor.pdf](docs/rapor/Rapor.pdf): IoS bileşen yayını biçiminde 8 bölüm (ana metin 5 sayfa) + ekler (gereksinimler, SOLID, test stratejisi, UML) |
| **Sunum** | [docs/sunum/index.html](docs/sunum/index.html): 10 slayt, ← → ile ilerler, `P` ile PDF'ye yazdırılır; konuşma notları [docs/sunum.md](docs/sunum.md) |
| **Site** | [site/index.html](site/index.html): ana sayfa, atölye, bileşenler (her bileşen için yayın sayfası), sonuçlar, rapor, ekip |
| **Atölye** | [web/index.html](web/index.html): iş akışı düzenleyicisi (aşağıda nasıl açılacağı) |
| **UML** | [docs/uml/](docs/uml/README.md): kullanım durumu, 2 sınıf, 3 sıralı, paket diyagramı; tek dosyada [UML_Diyagramlari.pdf](docs/uml/UML_Diyagramlari.pdf) |
| **GitHub** | bu depo; commit geçmişi |

| Belge | İçinde |
|---|---|
| [bench/results/validation-d.md](bench/results/validation-d.md) | **Doğrulama tablosu**, v4, çok desen (D) |
| [bench/results/validation-e.md](bench/results/validation-e.md) | v4, tek desen (E) |
| [bench/results/karar-yuku-v4.md](bench/results/karar-yuku-v4.md) | Karar süresinin doğrudan ölçümü, örneklem doğruluğu |
| `validation-taze.md`, `validation-tek.md`, `validation.md`, `validation-v1.md`, `validation-v2.md` | Eski sürümlerin kümeleri (B, C, A); silinmedi |
| [bench/results/calibration-fit.md](bench/results/calibration-fit.md) | Kalibrasyon katsayıları (v4); v3: `calibration-fit-v3.md` |
| [docs/sapmalar.md](docs/sapmalar.md) | Allmer 2016'dan ve klasik tariflerden sapmalar |
| [docs/mutasyon.md](docs/mutasyon.md) | Mutasyon denetimi |
| [docs/anlatim.md](docs/anlatim.md) | Her dosyanın, atölyenin ve iş akışı motorunun sade anlatımı |
| [docs/kontrol.md](docs/kontrol.md) | Ödev kontrol listesi |
| [KARARLAR.md](KARARLAR.md) | Ödev metninin açık bıraktığı noktalarda verilen kararlar |

## Kurulum

Node.js 22 ya da üstü yeterlidir. Hiçbir npm paketi kullanılmaz; `npm install` gerekmez.

```bash
node --version
```

## Atölyeyi, siteyi ve sunumu yerelde açmak

Atölye ES modülleri ve Web Worker kullandığı için `file://` ile değil, bir sunucudan açılmalıdır. Depoda bağımlılıksız bir sunucu var (yalnızca Node'un kendi modülleri, yalnızca 127.0.0.1):

```bash
npm run web
```

Sonra tarayıcıda: atölye `http://localhost:8327/web/`, site `http://localhost:8327/site/`, sunum `http://localhost:8327/docs/sunum/`. Başka bir bağlantı noktası için: `node scripts/sunucu.js --port 9000`.

Atölyede: soldan bir hazır paket seçin (ya da bileşenleri tuvale sürükleyip uçlarını bağlayın) ve **Tarayıcıda çalıştır**'a basın. ExactMatch kutusunu seçince molekülün karar kaydı (`explain`) sağ panelde görünür; **Açıkla** iş akışını Türkçe cümlelerle anlatır; **Atomları yarıştır** aynı girdide bütün atomları tarayıcıda ölçer (gösterim amaçlı; rapordaki sayılar Node ölçümleridir). Kutu ekleme, taşıma ve bağlama klavyeyle de yapılır (Enter, ok tuşları, Delete, Esc; Ctrl+Enter çalıştırır).

Hazır paketler: teknik borç avı, gizli bilgi sızıntısı (+ CI kapısı), yasaklı / riskli API, log incelemesi, tek desen / büyük dosya, biyoloji köprüsü (lambda genomu). Her birinin bulgu sayısı komut satırıyla aynıdır (`npm run paketler`).

## Komutlar

| Komut | Ne yapar |
|---|---|
| `npm test` | 360 birim testi: sözleşme, özel durumlar, oracle karşılaştırması, molekül, iş akışı motoru, hazır paketler, komut satırı, yasaklı işlev taraması |
| `npm run calibrate` | Kalibrasyon ızgarasını ölçer (180 vaka × 8 atom), katsayıları `src/molecules/coefficients.json` ve `.js`'e yazar (bu makinede 233,9 s) |
| `npm run bench` | Doğrulama kümesi A. Taze kümeler: `node --expose-gc tests/benchmarks/validate.js --seed 16180339 --name validation-d` (D) ve `... --seed 14142135 --name validation-e --k 1` (E). `--retable` ölçüm yapmadan tabloları yeniden kurar |
| `npm run karar-yuku` | Karar süresinin doğrudan ölçümü ve örneklem doğruluğu → `bench/results/karar-yuku-v4.md` |
| `npm run figures` | Rapor şekilleri (`docs/rapor/*.svg`) |
| `npm run mutation` | Mutasyon denetimi (12 bilerek konmuş hata) → `docs/mutasyon.md` |
| `npm run web` | Bağımlılıksız yerel sunucu (atölye, site, sunum) |
| `npm run paketler` | Hazır paketleri iş akışı motoruyla çalıştırıp komut satırıyla karşılaştırır (`../forum` gerekir) |
| `npm run ornekler` | Atölyenin örnek verilerini depodaki gerçek dosyalardan üretir (`web/data/`) |
| `node scripts/site-uret.js` | Siteyi ve slaytları `bench/results/`'tan üretir (sayılar elle yazılmaz) |
| `node scripts/uml-ciz.js --pdf` | UML diyagramları (`docs/uml/`) |
| `node scripts/sayi-denetimi.js` | Rapor, README, sunum, site ve kontrol listesindeki her sayıyı kaynak dosyalara karşı denetler |
| `node scripts/arayuz-denetimi.js` | Atölyenin gerçek Chromium'da uçtan uca denetimi (Playwright gerekir), ekran görüntüleri `docs/ekran/` |
| `npm run report` | `docs/rapor/rapor.html` → `Rapor.pdf` (Playwright gerekir) |

Ölçüm yaparken makinede başka ağır iş çalışmamalı. Sonuçlar makineye bağlıdır: teslimden önce `npm run calibrate` ve ardından taze kümeler kendi bilgisayarınızda yeniden çalıştırılabilir (yeni tohumla; eski sonuçlar silinmeden).

## Komut satırı

```bash
node bin/ios.js run ExactMatch --patterns GATC,GGATCC --strategy auto < tests/data/lambda_NC_001416.fa > cikti.jsonl
```

```bash
node bin/ios.js explain --patterns GATC,GGATCC < tests/data/lambda_NC_001416.fa
```

```bash
node bin/ios.js scan --preset todo ../forum
```

- `run`: stdout'a satır başına bir `Sequence.Match` (JSONL) yazar; karar özeti stderr'e gider. Bileşen adı `ExactMatch` ya da bir atomun adı olabilir.
- `explain`: yalnızca molekülün kararını (`record`) JSON olarak yazar.
- `scan`: dosya ya da klasörlerde arar; çıktı `dosya:satır:sütun: desen`. Hazır kümeler: `todo`, `secrets`, `banned-api`, `errors`. `--json` (JSONL), `--fail` (bulgu varsa çıkış kodu 1; sürekli entegrasyon için).
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
src/molecules/   ExactMatch.js (molekül), costModel.js (tahmin + NNLS), coefficients.json/.js
src/registry.js  kayıt defteri: yeni atom eklemek molekülü değiştirmez
src/shape.js     veri şekli: n, σ, σe, k, mMin, mMax, mMean (64 × 256 karakterlik örneklem)
src/adapters/    kaynak dosya → FASTA.Entry uyarlayıcısı
src/workflows/   iş akışı motoru (engine), atölye kataloğu, hazır paketler, atom yarışı, CodeScan
bin/ios.js       komut satırı
web/             Kod Bilimi Atölyesi (saf HTML/CSS/JS; ../src modüllerini doğrudan içe aktarır)
site/            proje sitesi (scripts/site-uret.js ile üretilir)
bench/           veri üretici, zaman ölçümü, kod korpusu, sonuçlar (results/)
tests/unit/      birim testleri (npm test)
tests/benchmarks/ kalibrasyon, doğrulama, ölçütler, şekiller
tests/data/      gerçek veri: lambda faj genomu, 126 E. coli K-12 proteini
docs/            rapor, sunum, UML, sapmalar, mutasyon, anlatım, kontrol listesi, ekran görüntüleri
scripts/         sunucu, örnek veri, paket karşılaştırması, site/UML üretimi, denetimler, PDF
```

## Teslim yapısı (ödev depo kökünde `src/`, `bin/`, `package.json` bekliyor)

Proje bu deponun `vize/` klasöründe. Ödevin beklediği kök düzeni için önerilen yol: **yalnızca `vize/` geçmişini taşıyan ayrı bir dal**. Bu, mevcut dalları ve geçmişi değiştirmez; yeni bir dal oluşturur. Komutlar depo kökünden, `vize/` değişiklikleri commit edildikten sonra:

```bash
git subtree split --prefix=vize -b vize-teslim
```

```bash
git push -u origin vize-teslim
```

`vize-teslim` dalının kökünde doğrudan `src/`, `bin/`, `package.json`, `tests/` bulunur ve `vize/` klasörünü değiştiren her commit (yol önekleri atılmış hâliyle) geçmişte yer alır. Denetim: dalı ayrı bir klasöre alıp `npm test` çalıştırın (testler `vize/` dışındaki hiçbir dosyaya bağlı değil):

```bash
git worktree add ../teslim vize-teslim
```

```bash
cd ../teslim && npm test
```

Sınır: `npm run paketler` ve `scripts/arayuz-denetimi.js` Agora karşılaştırması için `../forum` klasörünü kullanır; teslim dalında bu iki betik yalnızca ana depoda çalışır (atölyenin örnek verisi `web/data/agora.json` dala dahildir). Teslim .zip olarak isteniyorsa: `git archive --format=zip -o vize-teslim.zip vize-teslim` (ödev `.git` klasörünü istiyorsa dal ayrı bir klasöre klonlanıp sıkıştırılmalı).

## GitHub Pages'te yayınlama

Yayın adresi: **<https://baki-b.github.io/YZM327-Odevler/>** (kök siteye yönlendirir; atölye `…/web/`, sunum `…/docs/sunum/`, rapor `…/docs/rapor/Rapor.pdf`).

Depodaki `.github/workflows/sayfalar.yml` artık Agora yerine bu projeyi yayınlıyor: `main` dalına her gönderimde Node 22 ile `npm test` çalıştırır (başarısızsa yayımlamaz), `vize/` klasörünü olduğu gibi siteye koyar ve yayınlar. Actions sekmesinden elle de başlatılabilir. Pages kaynağı zaten "GitHub Actions" olduğu için ayarlarda değişiklik gerekmez; dal `main`'e birleşmeden yayın güncellenmez.

Site, atölye, sunum ve rapor statik ve göreli yollarla çalışır; bu yüzden alt yol (`/YZM327-Odevler/`) altında da çalışır.

**Ayrı depo (isteğe bağlı):** `vize-teslim` dalını yeni bir depoya gönderirseniz: depo **Settings → Pages → Build and deployment → Source: "Deploy from a branch"**, **Branch: `main` (ya da `vize-teslim`), klasör `/ (root)`** → Save. Birkaç dakika sonra adres `https://<kullanıcı>.github.io/<depo>/` olur.

## Veri kaynakları

- **Lambda faj genomu:** NC_001416.1, 48 502 baz. `tests/data/lambda_NC_001416.fa` (bowtie2 deposundaki örnek dosya, NCBI kaydının kopyası).
- **E. coli K-12 proteinleri:** 126 UniProtKB/Swiss-Prot kaydı (OX=83333). `tests/data/ecoli_k12_126_proteins.fasta`; her kaydın kaynağı `.kaynak.tsv` dosyasında.
- **Kaynak kod korpusu:** bu deponun Agora projesi (`forum/`, `testler/`, `tarayici/`, `olcum/`, `laboratuvar/`) → `bench/corpus/kod.txt`.
- **Atölye örnekleri** (`web/data/`, `npm run ornekler`): Agora `forum/` klasörü (114 dosya), bench/data.js log üreticisinden örnek log (+ 3 elle yazılmış örnek Traceback bloğu), açıkça **sahte** gizli bilgi örnekleri (gerçek anahtar yok; AKIA ile başlayan değer AWS belgelerindeki resmî örnek anahtardır).

## Başlangıç paketi

Paket verilmedi; karşılığı ödevin 4. ve 5. bölümüne göre yazıldı (`ExactSearchAtom`, `NaiveSearch`, `BoyerMooreSearch`, `alphabet.js`, `hits.js`, `fasta.js`, `bench/data.js`, `bench/timing.js`, `contract.test.js`). Proje kendi başına çalışır.

## Katkılar

| Üye | Numara | Katkı |
|---|---|---|
| Baki [soyad] | [numara] | [...] |
| [Üye 2 ad soyad] | [numara] | [...] |

Ders: [ders kodu ve adı] · Öğretim elemanı: [ad soyad]

**Yapay zekâ kullanımı:** Ders politikası yapay zekâ kullanımını serbest bırakıyor. Kod, testler, ölçüm betikleri, iş akışı motoru ve atölye, site, slaytlar, UML diyagramları, rapor ve belgeler bir yapay zekâ kodlama aracıyla (Claude Code) üretildi. Bütün sayılar bu çalışmada çalıştırılan komutların çıktısından alındı ve `scripts/sayi-denetimi.js` ile denetlendi. Sunumda her bölümün anlatılabilmesi için [docs/anlatim.md](docs/anlatim.md) hazırlandı.
