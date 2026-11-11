# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v378, 2026-11-11T13:45:12.105Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

120 vaka (tohum 20261111); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 81.7 % | 88.3 % | 1.038 | 1.83× | 1.007 |
| Allmer 2016 kuralı | 120 | 8.3 % | 11.7 % | 2.764 | 35.15× | 3.294 |
| her zaman BoyerMooreSearch | 120 | 0.0 % | 0.8 % | 3.328 | 32.54× | 3.372 |
| her zaman HorspoolSearch | 120 | 5.0 % | 14.2 % | 2.883 | 42.09× | 3.969 |
| her zaman ShiftOrSearch | 120 | 0.0 % | 0.0 % | 5.901 | 66.82× | 4.193 |
| her zaman KmpSearch | 120 | 0.0 % | 0.0 % | 8.218 | 120.48× | 7.826 |
| her zaman AhoCorasickSearch | 120 | 36.7 % | 39.2 % | 1.593 | 4.87× | 1.119 |
| her zaman WuManberSearch | 120 | 50.0 % | 58.3 % | 1.210 | 2.95× | 1.259 |
| her zaman Bm4DnaDsSearch | 120 | 8.3 % | 14.2 % | 2.826 | 35.61× | 3.664 |
| her zaman Bm4DnaHmbsSearch | 120 | 0.0 % | 0.0 % | 3.476 | 30.57× | 3.401 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 56 | 92.9 % | 96.4 % | 1.007 | 1.24× | 1.004 |
| Allmer 2016 kuralı | 56 | 3.6 % | 5.4 % | 3.126 | 35.15× | 3.214 |
| her zaman BoyerMooreSearch | 56 | 0.0 % | 1.8 % | 3.636 | 28.86× | 3.295 |
| her zaman HorspoolSearch | 56 | 0.0 % | 3.6 % | 3.474 | 42.09× | 3.899 |
| her zaman ShiftOrSearch | 56 | 0.0 % | 0.0 % | 5.401 | 66.82× | 3.998 |
| her zaman KmpSearch | 56 | 0.0 % | 0.0 % | 9.239 | 120.48× | 7.520 |
| her zaman AhoCorasickSearch | 56 | 53.6 % | 57.1 % | 1.265 | 3.59× | 1.076 |
| her zaman WuManberSearch | 56 | 42.9 % | 50.0 % | 1.257 | 2.95× | 1.260 |
| her zaman Bm4DnaDsSearch | 56 | 3.6 % | 5.4 % | 3.294 | 35.61× | 3.587 |
| her zaman Bm4DnaHmbsSearch | 56 | 0.0 % | 0.0 % | 3.731 | 26.53× | 3.345 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 85.0 % | 90.0 % | 1.031 | 1.83× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 6.7 % | 10.0 % | 2.675 | 34.28× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 78.3 % | 86.7 % | 1.044 | 1.71× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 10.0 % | 13.3 % | 2.856 | 35.15× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 1.182, %90'lık dilim 1.762. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 74 | code | 28122 | 3 | 6 | WuManberSearch | 0.344 | Bm4DnaDsSearch | 0.188 | 1.83× |
| 22 | binary | 12470 | 13 | 21 | WuManberSearch | 0.277 | AhoCorasickSearch | 0.162 | 1.71× |
| 39 | log | 26159 | 32 | 9/5/21 | WuManberSearch | 0.849 | AhoCorasickSearch | 0.530 | 1.60× |
| 30 | dna | 28766 | 3 | 11/5/25 | BoyerMooreSearch | 0.591 | HorspoolSearch | 0.385 | 1.53× |
| 23 | text | 21724 | 3 | 27/11/62 | WuManberSearch | 0.149 | Bm4DnaDsSearch | 0.099 | 1.51× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 0 | 1 |
| HorspoolSearch | 6 | 1 |
| ShiftOrSearch | 0 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 44 | 41 |
| WuManberSearch | 60 | 76 |
| Bm4DnaDsSearch | 10 | 1 |
| Bm4DnaHmbsSearch | 0 | 0 |
