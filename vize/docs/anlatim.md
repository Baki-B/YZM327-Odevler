# Projeyi anlatma rehberi

Bu belge sunumda "şu dosya ne yapıyor, neden böyle yazıldı?" sorusuna hazırlık içindir. Her bölüm üç soruyu yanıtlar: **ne yapar**, **neden böyle**, **hoca sorarsa nasıl anlatılır**. Yabancı terimler ilk geçtiği yerde Türkçe karşılığıyla verilir.

## 1. Büyük resim

Görev: bir metinde bir ya da birkaç desenin geçtiği **bütün** yerleri bulmak. Ctrl+F'in yaptığı iş, ama çok desenle ve hızlı.

Üç katman var (IoS'un dili):

| Katman | Bu projede | Benzetme |
|---|---|---|
| Fonksiyon (function) | `src/functions/horspool.js` gibi saf hesap | Motor |
| Atom | `src/atomic/HorspoolSearch.js`: motoru standart bir kasaya koyar | Araba |
| Molekül | `src/molecules/ExactMatch.js`: yola bakıp arabayı seçer | Şoför |

Bütün atomlar aynı girdiyi alır (`{ header, seq }`), aynı çıktıyı verir (`{ header, pattern, position, length }`). Bu yüzden molekül onları birbirinin yerine takabilir.

**Hoca sorarsa:** "Hiçbir algoritma her durumda en hızlı değil. Kısa desende biri, çok desende başkası kazanıyor. Molekül girdinin şekline bakıp her atomun ne kadar süreceğini tahmin ediyor ve en ucuzunu seçiyor. Tahmin formülünün katsayılarını ölçerek bulduk."

## 2. Ortak altyapı

### `src/functions/alphabet.js`: alfabe küçültme

- **Ne yapar:** Desenlerde geçen her farklı karaktere 1, 2, 3… diye numara verir. Desende olmayan her karakter 0 olur. Metin bu numaralara çevrilir.
- **Neden:** Kaydırma tabloları 65 536 elemanlı olmak yerine (UTF-16'daki bütün karakterler) σ + 1 elemanlı olur. DNA için 5 eleman. Küçük tablo işlemcinin önbelleğine sığar, hızlıdır.
- **Neden doğru:** Metindeki `N` ve `x` ikisi de 0 olur, ama 0 hiçbir desen karakterine eşit olmadığı için sonuç değişmez.
- **ignoreCase:** Yalnızca ASCII a–z, A–Z ile aynı numarayı alır. Türkçe `ı`/`İ` ya da `é` etkilenmez (sözleşme böyle istiyor).

### `src/functions/hits.js`: sonuç toplayıcı

- **Ne yapar:** Her eşleşmeyi tek bir sayıya paketler: `konum × k + desen sırası`. Sonunda bu sayıları sıralar.
- **Neden:** Sözleşme "önce konum, eşitse desenin listedeki sırası" diyor. Bu paketleme sayesinde tek bir sayısal sıralama yeterli oluyor. Aho-Corasick gibi eşleşmeleri karışık sırada bulan algoritmalar da doğru sırada çıktı veriyor.
- **Örnek:** k = 3 desen; desen 2, konum 5'te → 5·3 + 2 = 17. Desen 0, konum 5'te → 15. Sıralayınca 15 önce gelir.

### `src/atomic/ExactSearchAtom.js`: ortak atom sınıfı

- **Ne yapar:** Parametre denetimi, ignoreCase, alfabe küçültme, aynı desenin tekrarını tek desene indirme ve çıktı sıralaması. Alt sınıf yalnızca `prepare()` (ön işleme) ve `scanText()` (arama) yazar.
- **Tasarım deseni:** Template Method (şablon yöntem). İskelet üst sınıfta, değişen adımlar alt sınıfta.
- **Hoca sorarsa:** "Ortak kuralları tek yerde yazdık, böylece yedi atomun yedisinde ayrı ayrı hata yapma şansımız yok. Bir atom yalnızca algoritmasıyla ilgilenir."

### `src/atomic/NaiveSearch.js`: referans (oracle)

- **Ne yapar:** Kaba kuvvet. Her konumda her deseni dener. Hazır `indexOf` kullanır (yalnızca bu dosyada izinli).
- **Neden ayrı yazıldı:** Ortak alfabe kodlamasını bilerek kullanmaz. Ortak sınıfta bir hata olsa bile referans etkilenmez ve testler bu hatayı yakalar.

## 3. Algoritmalar (elle izlenebilen örneklerle)

Her algoritmada metin T, desen P, m = desen uzunluğu, n = metin uzunluğu.

### Horspool (`horspool.js`)

**Fikir:** Pencerenin son karakterine bak. Bu karakter desenin ilk m−1 karakterinde en sağda nerede geçiyorsa, pencereyi o hizaya getirecek kadar kaydır. Hiç geçmiyorsa m kadar kaydır.

**Örnek:** P = `GCAG` (m = 4). İlk m−1 karakter `G C A`: G 0. konumda, C 1.'de, A 2.'de. Kayma = m − 1 − konum, yani G → 3, C → 2, A → 1, desende olmayan her karakter → 4.
T = `TTTGCAG`: pencere `TTTG`, son karakter G, P'nin sonu da G: karşılaştır, `TTT` ≠ `GCA`, G kadar (3) kay. Yeni pencere `GCAG` → eşleşme (konum 3).

**Karmaşıklık:** Tipik O(n/m). Uzun desende ve büyük alfabede çok hızlı. En kötü O(n·m).

### Boyer-Moore (`boyerMoore.js`)

Horspool + "iyi sonek" kuralı: Eşleşmiş son parçanın desende başka nerede geçtiğine bakar. İki kuraldan büyük olanı kadar kayar. Periyodik desende Horspool'dan güvenlidir ama tablo kurmak daha pahalıdır.

### bm4DNADS (`bm4dnaDs.js`): sentinel + açılmış döngü

**Fikir 1, sentinel (bekçi):** Desenin bir kopyası metnin sonuna eklenir. Atlama döngüsü "metnin sonuna geldim mi?" diye her adımda sormaz, çünkü en geç bekçide durur.
**Fikir 2, açılmış döngü:** Son karakterin kayması 0 yapılır. Döngü `j += skip[T[j]]` adımını art arda üç kez atar. Kayma 0 olunca (pencere sonu desenin son harfine denk gelince) durur ve tam karşılaştırma yapar.

**Benzetme:** Market rafında bir ürünü ararken her adımda "raf bitti mi?" diye bakmak yerine rafın sonuna aynı üründen bir tane koyarsın. Mutlaka bir yerde durursun, durduğun yerin rafın sonu olup olmadığına yalnızca bir kez bakarsın.

**Makaleden sapma (sapmalar.md D2):** Bekçide durunca `j ≥ n` denetimi yapılır, bekçinin "eşleşmesi" raporlanmaz.

### bm4DNAHMbs (`bm4dnaHmbs.js`): q-gram kayması

**Fikir:** Tek karakter yerine pencerenin son **q karakterine** (q-gram) bakılır. DNA'da tek karakterin desende geçme olasılığı çok yüksektir (4 harf var), bu yüzden Horspool en fazla ~4 kayar. 5 harflik bir parçanın desende geçme olasılığı ise düşüktür, böylece kayma m − q + 1'e yaklaşır.

**"bs" (bit shift):** q karakterin numaraları bit kaydırmayla tek sayıya çevrilir: `h = (h << 3) | kod`. Bu sayı tabloda indeks olarak kullanılır.

**Ödevin ipucu sorusu: desende geçmeyen q-gram için kayma neden m − q + 1, m değil?**
Desen `ACGTAC`, q = 3, metin `TTTTxACGTAC`. Pencere `TTTxAC` (konum 1–6) iken son q-gram `xAC` desende yok. 6 kaydırırsak pencere 7'ye gider ve 5. konumdaki eşleşme kaçar. Çünkü pencerenin son iki karakteri `AC` desenin başıdır. Güvenli kayma 6 − 3 + 1 = 4: pencere 5'e gelir ve eşleşme bulunur.
(Bu hata `npm run mutation` içinde bilerek yerleştiriliyor ve testler yakalıyor.)

### Shift-Or (`shiftOr.js`): bit paralel

**Fikir:** 32 bitlik bir sayının her biti desenin bir konumunu temsil eder. Bit i = 0 demek "desenin ilk i+1 karakteri şu an metinde eşleşmiş durumda" demektir. Her metin karakterinde tek satır çalışır: `D = (D << 1) | maske[c]`.
**Örnek:** P = `AB`. maske[A] = …1110 (0. bit 0), maske[B] = …1101 (1. bit 0). T = `AB`: D = …1111 → A okununca (D<<1)|maske[A] = …1110 → B okununca (…11100)|…1101 = …1101: 1. bit 0 → eşleşme.
**Sınır:** 32 karakter. Daha uzun desende ilk 32 karakter süzgeç olur, kalanı tek tek doğrulanır, ama molekül bu atomu o durumda seçmez.

### KMP (`kmp.js`)

**Fikir:** Metinde asla geri dönülmez. Uyuşmazlıkta desenin "hem öneki hem soneki olan" en uzun parçasına geri gidilir.
**Örnek:** P = `ABAB`, başarısızlık tablosu [0, 0, 1, 2]. `ABAB` bulununca q = fail[3] = 2'ye dönülür. Böylece `ABABAB` içindeki ikinci (örtüşen) eşleşme de bulunur.
**Ne zaman iyi:** En kötü durumda bile doğrusal, akış dostu. Ama ortalamada atlama yapmadığı için Horspool ailesinden yavaş.

### Aho-Corasick (`ahoCorasick.js`)

**Fikir:** Bütün desenlerden bir harf ağacı (trie) kurulur ve "başarısızlık bağları" eklenir: Bu yol tıkanırsa en uzun hangi sonekle devam ederim? Sonra bu yapı tam bir otomata çevrilir: her (durum, harf) için bir sonraki durum tabloda hazırdır. Metin tek geçişte okunur; desen sayısı aramayı yavaşlatmaz.
**Örnek:** Desenler `he`, `she`, `his`, `hers`; metin `ushers`. `s-h-e` okununca hem `she` biter hem de (sözlük bağıyla) `he` biter.
**Ne zaman iyi:** Çok desen (k büyük), özellikle kısa desenlerle.

### Wu-Manber (`wuManber.js`)

**Fikir:** Çok desenli Horspool. Bütün desenler en kısa desenin uzunluğuna kırpılmış gibi düşünülür. Pencerenin son B karakterlik bloğuna bakılır. Hiçbir desende bu blok yoksa pencere mMin − B + 1 kadar kayar. Kayma 0 ise o blokla biten desenler (kova) tek tek doğrulanır.
**Ne zaman iyi:** Çok desen + desenler çok kısa değilse. Ölçümlerde en sık kazanan atom.

## 4. Molekül ve seçim

### `src/shape.js`: veri şekli

İlk kaydın uzunluğu n, farklı karakter sayısı σ, **etkin alfabe** σe = 1/Σp², desen sayısı k, desen uzunlukları.

**σe neden var?** Kaynak kodda 90 farklı karakter olabilir, ama boşluk ve `e` çok sık geçer. İki rastgele karakterin aynı çıkma olasılığı tekdüze 90 harflik alfabeden çok daha yüksektir. σe bunu ölçer: kod için ~25, DNA için ~4. Beklenen kayma σ'ya değil σe'ye bağlıdır.

### `src/molecules/costModel.js`: maliyet modeli

- Her atom girdi şeklinden **özellikler** hesaplar. Örnek, Horspool: `scan = k · n / E[kayma]`, yani yaklaşık pencere sayısı.
- Tahmini süre = Σ katsayı × özellik.
- Katsayılar kalibrasyonda **negatif olmayan en küçük kareler** (NNLS) ile bulunur. "Göreli hata" kullanılır: 0,05 ms'lik vaka ile 50 ms'lik vaka eşit ağırlıktadır.
- **Hoca sorarsa:** "Kural tabanlı eşikler yerine maliyet modeli seçtik. Yeni atom eklenince yalnızca onun özelliklerini yazıp kalibrasyonu yeniden çalıştırıyoruz; eşikleri elle yeniden düşünmek gerekmiyor."

### `src/molecules/ExactMatch.js`

1. İlk kaydı alır, şeklini hesaplar.
2. Kayıt defterindeki her aday atom için: `applicable` true değilse eler (nedeni `record`'a yazılır), değilse tahmini süreyi hesaplar.
3. En ucuzu seçer, bütün akışta onu kullanır.
4. `record` = istenen, seçilen, şekil, her atomun tahmini ve gerekçe.

**Genişletilebilirlik:** Dosyada hiçbir atom adı yok. Bunu bir test de denetliyor. Atomlar `registry.js`'ten gelir.

### `src/registry.js`: kayıt defteri

Açık/Kapalı ilkesi: sistem genişlemeye açık, değişikliğe kapalı. Yeni atom = yeni dosya + listeye bir satır (ya da çalışma anında `register`).

## 5. Yazılım mühendisliği katmanı

- `src/adapters/sourceToEntry.js`: Uyarlayıcı (Adapter) deseni. Bir kaynak dosyayı `{ header: '>yol', seq: içerik }` biçimine çevirir. Atomlara dokunmadan aynı altyapı kodda çalışır.
- `src/workflows/CodeScan.js`: Molekülü kullanır, konumları satır ve sütuna çevirir (satır başları ikili aramayla bulunur).
- `ios scan --preset secrets --fail src/` sürekli entegrasyonda (CI) kullanılabilir: kodda parola ya da API anahtarı izi varsa derleme kırılır.
- **Neden ilginç:** DNA'da 4 harf var. Kaynak kodda ~90 farklı karakter var ama etkin alfabe ~25. Bu yüzden kazanan atomlar farklı çıkıyor (rapor bölüm 6).

## 6. Testler

| Dosya | Ne sınıyor |
|---|---|
| `contract.test.js` | Sözleşme: alanlar, 0 tabanlı konum, örtüşme, sıra, tekrar eden desen, ignoreCase (yalnız ASCII), UTF-16, hatalar |
| `atoms.test.js` | Her atom için 16 özel durum (periyodik desen, tek harf, emoji, 31/32/33 sınırı…) + iç parçalar |
| `oracle.test.js` | Gerçek veri (lambda, E. coli), 6 sentetik alfabe, tekrarlı metin, 360 tohumlu rastgele vaka; her atom + molekül NaiveSearch ile birebir |
| `molecule.test.js` | record alanları, en ucuz seçim, zorla seçilen strateji, sahte atom, uygulanamaz atom, ilk kayda göre karar |
| `forbidden.test.js` | Atomlarda indexOf/RegExp/console/Node modülü/saat/rastgelelik yok (kaynak tarama + negatif kontrol) |
| `cli.test.js` | `bin/ios.js` alt süreç olarak: run, explain, scan, hatalar |
| `core.test.js` | FASTA, şekil, NNLS, uyarlayıcı, CodeScan |

**Oracle nedir?** Sonucu kesin doğru bilinen yavaş uygulama. Hızlı atomun sonucu onunkiyle eleman eleman aynı olmalı.

## 7. Ölçüm

- **Isınma (warm-up):** JavaScript motoru kodu ilk çalıştırmalarda derler. İlk ölçüm yavaş çıkar, bu yüzden atılır.
- **Medyan:** 5 tekrarın ortadaki değeri. Ortalamadan farkı, tek bir aşırı yavaş ölçümden etkilenmemesi.
- **Dönüşümlü ölçüm:** Her turda her atom bir kez çalışır. Makine bir an yavaşlarsa hepsini aynı biçimde etkiler.
- **Kalibrasyon / doğrulama ayrımı:** Katsayılar 180 vakada bulundu. Başarı ise hiç görülmemiş 120 vakada ölçüldü (farklı tohum, ızgara arası değerler, yeni alfabeler). Sınavda daha önce çözülmüş soruyu sormamak gibi.
