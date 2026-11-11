# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v378, 2026-11-11T13:37:21.708Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

120 vaka (tohum 20261111); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 66.7 % | 78.3 % | 1.168 | 6.11× | 1.446 |
| Allmer 2016 kuralı | 120 | 7.5 % | 12.5 % | 2.742 | 36.78× | 3.241 |
| her zaman BoyerMooreSearch | 120 | 0.0 % | 0.0 % | 3.291 | 33.17× | 3.362 |
| her zaman HorspoolSearch | 120 | 6.7 % | 15.0 % | 2.828 | 44.68× | 3.964 |
| her zaman ShiftOrSearch | 120 | 0.0 % | 0.0 % | 5.806 | 69.05× | 4.116 |
| her zaman KmpSearch | 120 | 0.0 % | 0.0 % | 8.132 | 108.35× | 7.794 |
| her zaman AhoCorasickSearch | 120 | 37.5 % | 40.8 % | 1.597 | 4.97× | 1.124 |
| her zaman WuManberSearch | 120 | 48.3 % | 58.3 % | 1.219 | 3.00× | 1.260 |
| her zaman Bm4DnaDsSearch | 120 | 7.5 % | 15.0 % | 2.801 | 36.85× | 3.605 |
| her zaman Bm4DnaHmbsSearch | 120 | 0.0 % | 0.0 % | 3.477 | 32.26× | 3.387 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 63 | 71.4 % | 77.8 % | 1.171 | 5.07× | 1.449 |
| Allmer 2016 kuralı | 63 | 3.2 % | 4.8 % | 3.132 | 36.78× | 3.197 |
| her zaman BoyerMooreSearch | 63 | 0.0 % | 0.0 % | 3.645 | 28.45× | 3.306 |
| her zaman HorspoolSearch | 63 | 0.0 % | 1.6 % | 3.557 | 44.68× | 3.945 |
| her zaman ShiftOrSearch | 63 | 0.0 % | 0.0 % | 5.568 | 69.05× | 3.963 |
| her zaman KmpSearch | 63 | 0.0 % | 0.0 % | 9.564 | 108.35× | 7.600 |
| her zaman AhoCorasickSearch | 63 | 50.8 % | 55.6 % | 1.309 | 4.29× | 1.091 |
| her zaman WuManberSearch | 63 | 46.0 % | 54.0 % | 1.234 | 3.00× | 1.258 |
| her zaman Bm4DnaDsSearch | 63 | 3.2 % | 4.8 % | 3.400 | 36.85× | 3.574 |
| her zaman Bm4DnaHmbsSearch | 63 | 0.0 % | 0.0 % | 3.578 | 26.62× | 3.322 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 71.7 % | 86.7 % | 1.115 | 6.11× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 6.7 % | 11.7 % | 2.654 | 34.12× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 61.7 % | 70.0 % | 1.224 | 5.07× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 8.3 % | 13.3 % | 2.834 | 36.78× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 1.255, %90'lık dilim 2.247. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 90 | dna | 24457 | 9 | 7/3/17 | Bm4DnaHmbsSearch | 3.085 | AhoCorasickSearch | 0.505 | 6.11× |
| 10 | binary | 260737 | 38 | 14/6/33 | Bm4DnaHmbsSearch | 43.186 | AhoCorasickSearch | 8.520 | 5.07× |
| 58 | binary | 13873 | 7 | 10/5/23 | Bm4DnaHmbsSearch | 1.602 | AhoCorasickSearch | 0.337 | 4.75× |
| 16 | binary | 126679 | 26 | 9/5/21 | Bm4DnaHmbsSearch | 21.710 | AhoCorasickSearch | 4.819 | 4.51× |
| 106 | binary | 38563 | 5 | 20/9/46 | Bm4DnaHmbsSearch | 2.777 | AhoCorasickSearch | 0.642 | 4.33× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 0 | 0 |
| HorspoolSearch | 8 | 3 |
| ShiftOrSearch | 0 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 45 | 30 |
| WuManberSearch | 58 | 73 |
| Bm4DnaDsSearch | 9 | 1 |
| Bm4DnaHmbsSearch | 0 | 13 |
