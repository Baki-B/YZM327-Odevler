# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v445, 2026-11-13T07:43:49.079Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

Model: v4 (katsayılar: 2026-11-13T07:39:15.201Z kalibrasyonu, Intel(R) Xeon(R) Processor @ 2.10GHz).

120 vaka (tohum 16180339); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

"ExactMatch (uçtan uca, karar dahil)" satırı molekülün kendi uçtan uca süresini kullanır: molekülü kurmak, ilk kaydın şeklini hesaplamak, her atomun maliyetini tahmin etmek ve seçilen atomla aramak. Diğer satırlar ödevin tanımıyla yalnızca seçilen atomun süresidir.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 76.7 % | 84.2 % | 1.051 | 2.00× | 1.033 |
| ExactMatch (uçtan uca, karar dahil) | 120 | 58.3 % | 70.0 % | 0.990 | 3.26× | 1.064 |
| Allmer 2016 kuralı | 120 | 2.5 % | 5.8 % | 2.543 | 18.71× | 2.658 |
| her zaman BoyerMooreSearch | 120 | 0.0 % | 0.8 % | 3.255 | 17.52× | 3.081 |
| her zaman HorspoolSearch | 120 | 4.2 % | 9.2 % | 2.793 | 33.44× | 3.086 |
| her zaman ShiftOrSearch | 120 | 0.0 % | 1.7 % | 6.196 | 24.44× | 5.640 |
| her zaman KmpSearch | 120 | 0.0 % | 0.0 % | 9.196 | 58.30× | 9.062 |
| her zaman AhoCorasickSearch | 120 | 33.3 % | 36.7 % | 1.632 | 5.02× | 1.291 |
| her zaman WuManberSearch | 120 | 58.3 % | 67.5 % | 1.131 | 2.78× | 1.198 |
| her zaman Bm4DnaDsSearch | 120 | 4.2 % | 7.5 % | 2.820 | 30.80× | 2.931 |
| her zaman Bm4DnaHmbsSearch | 120 | 0.0 % | 0.8 % | 3.227 | 23.14× | 3.255 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 92 | 78.3 % | 85.9 % | 1.042 | 2.00× | 1.031 |
| ExactMatch (uçtan uca, karar dahil) | 92 | 62.0 % | 75.0 % | 0.948 | 1.67× | 1.064 |
| Allmer 2016 kuralı | 92 | 2.2 % | 4.3 % | 2.570 | 18.71× | 2.651 |
| her zaman BoyerMooreSearch | 92 | 0.0 % | 1.1 % | 3.115 | 17.52× | 3.053 |
| her zaman HorspoolSearch | 92 | 3.3 % | 8.7 % | 2.774 | 33.44× | 3.069 |
| her zaman ShiftOrSearch | 92 | 0.0 % | 2.2 % | 6.015 | 24.44× | 5.597 |
| her zaman KmpSearch | 92 | 0.0 % | 0.0 % | 9.277 | 58.30× | 8.985 |
| her zaman AhoCorasickSearch | 92 | 40.2 % | 42.4 % | 1.477 | 4.92× | 1.269 |
| her zaman WuManberSearch | 92 | 53.3 % | 63.0 % | 1.153 | 2.78× | 1.201 |
| her zaman Bm4DnaDsSearch | 92 | 3.3 % | 5.4 % | 2.752 | 30.80× | 2.902 |
| her zaman Bm4DnaHmbsSearch | 92 | 0.0 % | 1.1 % | 3.115 | 23.14× | 3.234 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 80.0 % | 86.7 % | 1.040 | 1.49× |
| görülen (DNA, protein, kod) | ExactMatch (uçtan uca, karar dahil) | 60 | 53.3 % | 68.3 % | 1.001 | 1.64× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 1.7 % | 6.7 % | 2.680 | 18.71× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 73.3 % | 81.7 % | 1.061 | 2.00× |
| görülmeyen (log, ikili, metin) | ExactMatch (uçtan uca, karar dahil) | 60 | 63.3 % | 71.7 % | 0.978 | 3.26× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 3.3 % | 5.0 % | 2.413 | 17.71× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 0.951, %90'lık dilim 1.282. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 119 | text | 531186 | 24 | 92/37/150 | Bm4DnaHmbsSearch | 12.571 | WuManberSearch | 6.275 | 2.00× |
| 39 | log | 73759 | 39 | 9 | WuManberSearch | 3.332 | AhoCorasickSearch | 2.034 | 1.64× |
| 99 | log | 16091 | 3 | 20 | WuManberSearch | 0.235 | HorspoolSearch | 0.154 | 1.53× |
| 68 | code | 14926 | 117 | 11/5/25 | WuManberSearch | 1.360 | AhoCorasickSearch | 0.910 | 1.49× |
| 115 | protein | 46983 | 13 | 3/3/7 | AhoCorasickSearch | 2.498 | WuManberSearch | 1.673 | 1.49× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 0 | 0 |
| HorspoolSearch | 5 | 0 |
| ShiftOrSearch | 0 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 40 | 31 |
| WuManberSearch | 70 | 85 |
| Bm4DnaDsSearch | 5 | 2 |
| Bm4DnaHmbsSearch | 0 | 2 |
