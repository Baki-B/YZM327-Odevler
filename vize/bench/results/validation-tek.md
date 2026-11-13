# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v378, 2026-11-11T15:47:45.902Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

120 vaka (tohum 27182818); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

"ExactMatch (uçtan uca, karar dahil)" satırı molekülün kendi uçtan uca süresini kullanır: molekülü kurmak, ilk kaydın şeklini hesaplamak, her atomun maliyetini tahmin etmek ve seçilen atomla aramak. Diğer satırlar ödevin tanımıyla yalnızca seçilen atomun süresidir.

**Bu kümede desen sayısı k = 1 olarak sabitlendi.** k = 1 kalibrasyon ızgarasının da bir değeridir; bu yüzden küme k bakımından "ızgara arası" değildir. n ve m ızgara noktalarının arasından seçildi; metin ve desen tohumları kalibrasyondakilerden farklıdır.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 51.7 % | 79.2 % | 1.073 | 2.10× | 1.095 |
| ExactMatch (uçtan uca, karar dahil) | 120 | 0.8 % | 0.8 % | 1.686 | 3.73× | 1.527 |
| Allmer 2016 kuralı | 120 | 26.7 % | 53.3 % | 1.276 | 3.89× | 1.239 |
| her zaman BoyerMooreSearch | 120 | 1.7 % | 5.8 % | 1.413 | 2.53× | 1.427 |
| her zaman HorspoolSearch | 120 | 32.5 % | 61.7 % | 1.272 | 4.61× | 1.259 |
| her zaman ShiftOrSearch | 120 | 4.2 % | 6.7 % | 2.234 | 6.00× | 2.121 |
| her zaman KmpSearch | 120 | 0.0 % | 0.8 % | 2.303 | 4.89× | 2.407 |
| her zaman AhoCorasickSearch | 120 | 0.0 % | 0.0 % | 3.158 | 6.23× | 2.844 |
| her zaman WuManberSearch | 120 | 30.8 % | 47.5 % | 1.224 | 3.27× | 1.276 |
| her zaman Bm4DnaDsSearch | 120 | 29.2 % | 59.2 % | 1.297 | 4.79× | 1.287 |
| her zaman Bm4DnaHmbsSearch | 120 | 1.7 % | 8.3 % | 1.858 | 7.11× | 1.849 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 40 | 42.5 % | 77.5 % | 1.078 | 1.59× | 1.088 |
| ExactMatch (uçtan uca, karar dahil) | 40 | 2.5 % | 2.5 % | 1.481 | 2.28× | 1.447 |
| Allmer 2016 kuralı | 40 | 25.0 % | 60.0 % | 1.152 | 2.61× | 1.180 |
| her zaman BoyerMooreSearch | 40 | 0.0 % | 0.0 % | 1.413 | 2.53× | 1.409 |
| her zaman HorspoolSearch | 40 | 42.5 % | 67.5 % | 1.183 | 2.69× | 1.210 |
| her zaman ShiftOrSearch | 40 | 2.5 % | 5.0 % | 2.140 | 4.72× | 2.040 |
| her zaman KmpSearch | 40 | 0.0 % | 0.0 % | 2.438 | 4.89× | 2.396 |
| her zaman AhoCorasickSearch | 40 | 0.0 % | 0.0 % | 2.848 | 4.67× | 2.685 |
| her zaman WuManberSearch | 40 | 25.0 % | 47.5 % | 1.200 | 2.03× | 1.267 |
| her zaman Bm4DnaDsSearch | 40 | 25.0 % | 62.5 % | 1.204 | 3.21× | 1.226 |
| her zaman Bm4DnaHmbsSearch | 40 | 5.0 % | 17.5 % | 1.539 | 6.12× | 1.665 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 51.7 % | 86.7 % | 1.047 | 1.38× |
| görülen (DNA, protein, kod) | ExactMatch (uçtan uca, karar dahil) | 60 | 1.7 % | 1.7 % | 1.675 | 3.73× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 33.3 % | 63.3 % | 1.132 | 2.04× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 51.7 % | 71.7 % | 1.100 | 2.10× |
| görülmeyen (log, ikili, metin) | ExactMatch (uçtan uca, karar dahil) | 60 | 0.0 % | 0.0 % | 1.697 | 2.73× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 20.0 % | 43.3 % | 1.438 | 3.89× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 1.593, %90'lık dilim 1.962. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 52 | binary | 167157 | 1 | 17 | Bm4DnaHmbsSearch | 2.007 | WuManberSearch | 0.957 | 2.10× |
| 64 | binary | 37854 | 1 | 12 | BoyerMooreSearch | 0.350 | ShiftOrSearch | 0.185 | 1.89× |
| 4 | binary | 200343 | 1 | 12 | Bm4DnaHmbsSearch | 1.604 | ShiftOrSearch | 0.857 | 1.87× |
| 106 | binary | 12613 | 1 | 31 | WuManberSearch | 0.153 | BoyerMooreSearch | 0.088 | 1.73× |
| 76 | binary | 314119 | 1 | 27 | Bm4DnaHmbsSearch | 1.673 | WuManberSearch | 1.054 | 1.59× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 2 | 2 |
| HorspoolSearch | 39 | 53 |
| ShiftOrSearch | 5 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 0 | 0 |
| WuManberSearch | 37 | 48 |
| Bm4DnaDsSearch | 35 | 12 |
| Bm4DnaHmbsSearch | 2 | 5 |
