# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v378, 2026-11-11T13:47:43.715Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

120 vaka (tohum 31415926); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

"ExactMatch (uçtan uca, karar dahil)" satırı molekülün kendi uçtan uca süresini kullanır: molekülü kurmak, ilk kaydın şeklini hesaplamak, her atomun maliyetini tahmin etmek ve seçilen atomla aramak. Diğer satırlar ödevin tanımıyla yalnızca seçilen atomun süresidir.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 85.8 % | 92.5 % | 1.016 | 1.36× | 1.032 |
| ExactMatch (uçtan uca, karar dahil) | 120 | 25.8 % | 39.2 % | 1.187 | 2.61× | 1.169 |
| Allmer 2016 kuralı | 120 | 5.8 % | 7.5 % | 3.143 | 59.49× | 4.728 |
| her zaman BoyerMooreSearch | 120 | 0.0 % | 0.0 % | 3.771 | 33.13× | 4.804 |
| her zaman HorspoolSearch | 120 | 0.8 % | 8.3 % | 3.526 | 70.05× | 6.113 |
| her zaman ShiftOrSearch | 120 | 0.0 % | 0.8 % | 6.633 | 48.13× | 9.011 |
| her zaman KmpSearch | 120 | 0.0 % | 0.0 % | 10.688 | 136.56× | 17.077 |
| her zaman AhoCorasickSearch | 120 | 29.2 % | 33.3 % | 1.599 | 4.24× | 1.413 |
| her zaman WuManberSearch | 120 | 63.3 % | 66.7 % | 1.139 | 2.30× | 1.218 |
| her zaman Bm4DnaDsSearch | 120 | 6.7 % | 10.0 % | 3.500 | 59.49× | 5.668 |
| her zaman Bm4DnaHmbsSearch | 120 | 0.0 % | 0.0 % | 3.446 | 24.94× | 4.275 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 62 | 80.6 % | 90.3 % | 1.024 | 1.36× | 1.036 |
| ExactMatch (uçtan uca, karar dahil) | 62 | 22.6 % | 38.7 % | 1.139 | 1.95× | 1.164 |
| Allmer 2016 kuralı | 62 | 6.5 % | 6.5 % | 2.943 | 59.49× | 4.454 |
| her zaman BoyerMooreSearch | 62 | 0.0 % | 0.0 % | 3.710 | 33.13× | 4.637 |
| her zaman HorspoolSearch | 62 | 0.0 % | 1.6 % | 3.373 | 70.05× | 5.765 |
| her zaman ShiftOrSearch | 62 | 0.0 % | 1.6 % | 6.403 | 48.13× | 8.919 |
| her zaman KmpSearch | 62 | 0.0 % | 0.0 % | 11.196 | 136.56× | 16.637 |
| her zaman AhoCorasickSearch | 62 | 33.9 % | 41.9 % | 1.415 | 4.24× | 1.345 |
| her zaman WuManberSearch | 62 | 59.7 % | 66.1 % | 1.154 | 2.30× | 1.225 |
| her zaman Bm4DnaDsSearch | 62 | 6.5 % | 6.5 % | 3.239 | 59.49× | 5.307 |
| her zaman Bm4DnaHmbsSearch | 62 | 0.0 % | 0.0 % | 3.452 | 20.46× | 4.290 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 88.3 % | 95.0 % | 1.013 | 1.31× |
| görülen (DNA, protein, kod) | ExactMatch (uçtan uca, karar dahil) | 60 | 15.0 % | 28.3 % | 1.238 | 1.95× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 8.3 % | 10.0 % | 3.238 | 38.34× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 83.3 % | 90.0 % | 1.019 | 1.36× |
| görülmeyen (log, ikili, metin) | ExactMatch (uçtan uca, karar dahil) | 60 | 36.7 % | 50.0 % | 1.137 | 2.61× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 3.3 % | 5.0 % | 3.051 | 59.49× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 1.143, %90'lık dilim 1.683. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 81 | log | 289868 | 10 | 3 | WuManberSearch | 5.405 | AhoCorasickSearch | 3.983 | 1.36× |
| 104 | code | 193669 | 24 | 9/5/21 | WuManberSearch | 2.831 | AhoCorasickSearch | 2.166 | 1.31× |
| 92 | code | 267038 | 6 | 6/3/14 | AhoCorasickSearch | 3.165 | Bm4DnaDsSearch | 2.728 | 1.16× |
| 99 | log | 806754 | 116 | 7 | WuManberSearch | 18.008 | AhoCorasickSearch | 15.616 | 1.15× |
| 40 | binary | 15080 | 28 | 53 | WuManberSearch | 0.268 | AhoCorasickSearch | 0.233 | 1.15× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 0 | 0 |
| HorspoolSearch | 1 | 3 |
| ShiftOrSearch | 0 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 35 | 35 |
| WuManberSearch | 76 | 79 |
| Bm4DnaDsSearch | 8 | 3 |
| Bm4DnaHmbsSearch | 0 | 0 |
