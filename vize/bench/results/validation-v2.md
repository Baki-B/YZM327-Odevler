# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v378, 2026-11-11T13:41:16.324Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

120 vaka (tohum 20261111); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 75.8 % | 79.2 % | 1.078 | 2.27× | 1.271 |
| Allmer 2016 kuralı | 120 | 5.0 % | 9.2 % | 2.754 | 40.94× | 3.266 |
| her zaman BoyerMooreSearch | 120 | 0.0 % | 0.0 % | 3.302 | 33.97× | 3.436 |
| her zaman HorspoolSearch | 120 | 6.7 % | 12.5 % | 2.854 | 44.23× | 3.948 |
| her zaman ShiftOrSearch | 120 | 0.8 % | 0.8 % | 5.839 | 57.84× | 4.136 |
| her zaman KmpSearch | 120 | 0.0 % | 0.0 % | 8.092 | 119.09× | 7.776 |
| her zaman AhoCorasickSearch | 120 | 35.0 % | 39.2 % | 1.642 | 5.22× | 1.136 |
| her zaman WuManberSearch | 120 | 51.7 % | 54.2 % | 1.228 | 3.45× | 1.264 |
| her zaman Bm4DnaDsSearch | 120 | 5.8 % | 10.0 % | 2.801 | 40.94× | 3.640 |
| her zaman Bm4DnaHmbsSearch | 120 | 0.0 % | 0.0 % | 3.467 | 32.07× | 3.428 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 60 | 80.0 % | 81.7 % | 1.073 | 2.27× | 1.280 |
| Allmer 2016 kuralı | 60 | 3.3 % | 3.3 % | 3.193 | 40.94× | 3.232 |
| her zaman BoyerMooreSearch | 60 | 0.0 % | 0.0 % | 3.710 | 29.18× | 3.391 |
| her zaman HorspoolSearch | 60 | 0.0 % | 3.3 % | 3.504 | 44.23× | 3.921 |
| her zaman ShiftOrSearch | 60 | 0.0 % | 0.0 % | 5.632 | 57.84× | 3.971 |
| her zaman KmpSearch | 60 | 0.0 % | 0.0 % | 9.475 | 119.09× | 7.563 |
| her zaman AhoCorasickSearch | 60 | 51.7 % | 58.3 % | 1.281 | 3.53× | 1.087 |
| her zaman WuManberSearch | 60 | 45.0 % | 48.3 % | 1.267 | 3.45× | 1.264 |
| her zaman Bm4DnaDsSearch | 60 | 3.3 % | 3.3 % | 3.372 | 40.94× | 3.608 |
| her zaman Bm4DnaHmbsSearch | 60 | 0.0 % | 0.0 % | 3.778 | 32.07× | 3.413 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 83.3 % | 83.3 % | 1.045 | 1.55× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 6.7 % | 8.3 % | 2.712 | 35.42× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 68.3 % | 75.0 % | 1.112 | 2.27× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 3.3 % | 10.0 % | 2.796 | 40.94× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 1.133, %90'lık dilim 1.747. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 40 | binary | 112250 | 15 | 6/3/14 | Bm4DnaHmbsSearch | 20.313 | AhoCorasickSearch | 8.933 | 2.27× |
| 52 | binary | 206551 | 3 | 3 | Bm4DnaHmbsSearch | 17.607 | AhoCorasickSearch | 8.018 | 2.20× |
| 82 | binary | 263449 | 33 | 3/3/7 | Bm4DnaHmbsSearch | 110.886 | AhoCorasickSearch | 57.868 | 1.92× |
| 23 | text | 21724 | 3 | 27/11/62 | WuManberSearch | 0.193 | HorspoolSearch | 0.110 | 1.76× |
| 9 | log | 825804 | 52 | 18/7/41 | WuManberSearch | 12.109 | AhoCorasickSearch | 6.999 | 1.73× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 0 | 0 |
| HorspoolSearch | 8 | 1 |
| ShiftOrSearch | 1 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 42 | 38 |
| WuManberSearch | 62 | 75 |
| Bm4DnaDsSearch | 7 | 2 |
| Bm4DnaHmbsSearch | 0 | 4 |
