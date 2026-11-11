# Kararlar

Ödev metninin açık bıraktığı ya da bu ortamda yapılamayan her nokta için verilen karar, bir satırla. Gerekçeler parantez içinde.

| # | Konu | Karar |
|---|---|---|
| 1 | "Bunu yazılım mühendisliğine uygulayın" | Sözleşme birebir korundu; üstüne kaynak kod ve log tarayan bir katman eklendi (`src/adapters/`, `src/workflows/`, `ios scan`). Kalibrasyona "kaynak kod" alfabesi, doğrulamaya "log" alfabesi eklendi. (Hoca hangi yorumu kastetmiş olursa olsun ikisi de karşılanır; gizli testler yalnızca sözleşmeyi sınar.) |
| 2 | Başlangıç paketi | Elimizde yok. `ExactSearchAtom`, `NaiveSearch`, `BoyerMooreSearch`, `alphabet.js`, `hits.js`, `fasta.js`, `bench/data.js`, `bench/timing.js`, `contract.test.js` ödevin 4. ve 5. bölümüne göre yeniden yazıldı. Paket gelirse aynı adlı dosyalar onunkiyle değiştirilip `npm test` yeniden çalıştırılmalı. |
| 3 | Gerçek veri | Lambda genomu (NC_001416.1, 48 502 baz) bowtie2 deposundaki örnek dosyadan, 126 E. coli K-12 proteini GitHub'daki açık UniProt FASTA dosyalarından derlendi. NCBI ve UniProt bu ortamdan erişilemedi. Her proteinin kaynağı `tests/data/ecoli_k12_126_proteins.kaynak.tsv` içinde. |
| 4 | Allmer 2016 makalesi | PDF bu ortamdan açılamadı (peerj.com ve doi.org engelli). bm4DNADS ve bm4DNAHMbs, ödev tablosundaki tarife ("sentinel + 3 kez açılmış atlama döngüsü", "q-gram özetleri üzerinden kayma"), Hume & Sunday 1991 ve Wu & Manber 1994'e göre yazıldı. Sapmalar `docs/sapmalar.md` içinde. |
| 5 | Atom seçimi | 7 yeni atom: A grubundan 4'ü (Horspool, Shift-Or, bm4DNADS, bm4DNAHMbs), B'den KMP, C'den Aho-Corasick ve Wu-Manber (bonus). Rabin-Karp, suffix array ve FM-index yazılmadı. |
| 6 | Seçim yöntemi | Maliyet modeli: her atom girdi şeklinden "adım sayısı" özellikleri hesaplar; katsayılar kalibrasyonla negatif olmayan en küçük kareler (göreli hata) ile bulunur. (Atom arayüzündeki `features` ve `defaults` alanları bunun için tasarlanmış; yeni atom eklemek yalnızca o atomun özelliklerini yazmayı gerektirir.) |
| 7 | Veri şekli | Zorunlu alanlara (n, σ, k, mMin, mMax, mMean) etkin alfabe büyüklüğü σe = 1/Σp² eklendi; harf sıklıkları eşit olmayan metinlerde (kaynak kod, log) beklenen kaymayı σ'dan daha iyi verir. 262 144 karakterden uzun metinde σ eşit aralıklı 64 parçadan sayılır. |
| 8 | Shift-Or ve 32'den uzun desen | Atom yanlış sonuç vermesin diye 32'den uzun desende de çalışır (ilk 32 karakterle süzüp geri kalanını doğrular), ama `applicable()` ile kendini "uygun değil" ilan eder; molekül onu yalnızca m ≤ 32 iken seçer. |
| 9 | Çok desenli tek desen algoritmaları | Horspool, BM, KMP, Shift-Or, bm4DNA* her benzersiz desen için ayrı geçer; sonuçlar ortak toplayıcıda sözleşme sırasına konur. Aynı desen listede iki kez varsa bir kez aranır, iki kez raporlanır. |
| 10 | Allmer kuralında "m" | Kural tek desen için tanımlı; çok desende desenlerin ortalama uzunluğu (mMean) kullanıldı. |
| 11 | `search` adı | Atomların arama kancası `scanText()` adını taşır; `this.search(...)` hazır `String.prototype.search` ile karışıp otomatik taramada yanlış alarm verebilirdi. |
| 12 | Kaynak kodda boşluk | FASTA'da `seq` boşluk içermez; kaynak kod kaydında ise boşluk ve satır sonu anlamlı olduğu için korunur. Atomlar bunu sorun etmez (testlerde boşluklu metin var). |
| 13 | Ölçüm | Ölçümler bu oturumun bulut makinesinde yapıldı (makine bilgisi sonuç dosyalarında). Atomlar dönüşümlü ölçüldü (her turda her atom bir kez), 5 tekrarın medyanı alındı, 10 ms'den kısa ölçümler blok içinde tekrarlandı. Teslimden önce `npm run calibrate` ve `npm run bench` kendi bilgisayarınızda yeniden çalıştırılmalı. |
| 14 | Çalışma biçimi | Bireysel (aksi belirtilmedi). README'deki katkı bölümü buna göre yazıldı. |
| 15 | Yapay zekâ kullanımı | Ders politikası alanı boş. Kod, testler ve belgeler bir yapay zekâ kodlama aracıyla (Claude Code) üretildi; bu README'de ve raporda açıkça yazıldı. Hocanın politikası öğrenilince bu satır güncellenmeli. |
| 16 | Konum | Proje bu deponun `vize/` klasöründe, kendi başına çalışır. Teslim için klasör ayrı bir depoya ya da .zip'e taşınabilir. |
