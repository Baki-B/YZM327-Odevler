# Doğrulama sonuçları

Makine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 çekirdek, 16 GB, Node v22.23.4, linux 6.18.44-fc-v445, 2026-11-13T07:46:43.020Z. Çöp toplayıcı ölçümlerden önce çağrıldı: evet.

Model: v4 (katsayılar: 2026-11-13T07:39:15.201Z kalibrasyonu, Intel(R) Xeon(R) Processor @ 2.10GHz).

120 vaka (tohum 14142135); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. "Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.

"ExactMatch (uçtan uca, karar dahil)" satırı molekülün kendi uçtan uca süresini kullanır: molekülü kurmak, ilk kaydın şeklini hesaplamak, her atomun maliyetini tahmin etmek ve seçilen atomla aramak. Diğer satırlar ödevin tanımıyla yalnızca seçilen atomun süresidir.

**Bu kümede desen sayısı k = 1 olarak sabitlendi.** k = 1 kalibrasyon ızgarasının da bir değeridir; bu yüzden küme k bakımından "ızgara arası" değildir. n ve m ızgara noktalarının arasından seçildi; metin ve desen tohumları kalibrasyondakilerden farklıdır.

## Bütün vakalar

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 120 | 55.0 % | 70.8 % | 1.081 | 2.06× | 1.105 |
| ExactMatch (uçtan uca, karar dahil) | 120 | 20.0 % | 34.2 % | 1.300 | 3.10× | 1.088 |
| Allmer 2016 kuralı | 120 | 22.5 % | 50.8 % | 1.192 | 2.67× | 1.147 |
| her zaman BoyerMooreSearch | 120 | 5.0 % | 9.2 % | 1.422 | 2.50× | 1.350 |
| her zaman HorspoolSearch | 120 | 42.5 % | 64.2 % | 1.198 | 5.26× | 1.203 |
| her zaman ShiftOrSearch | 120 | 7.5 % | 10.0 % | 2.127 | 5.08× | 1.832 |
| her zaman KmpSearch | 120 | 0.0 % | 0.0 % | 2.189 | 3.95× | 2.016 |
| her zaman AhoCorasickSearch | 120 | 0.0 % | 1.7 % | 3.143 | 7.03× | 2.373 |
| her zaman WuManberSearch | 120 | 20.8 % | 26.7 % | 1.315 | 3.23× | 1.331 |
| her zaman Bm4DnaDsSearch | 120 | 22.5 % | 53.3 % | 1.257 | 6.55× | 1.216 |
| her zaman Bm4DnaHmbsSearch | 120 | 1.7 % | 9.2 % | 2.020 | 9.35× | 1.846 |

## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar

Çok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.

| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |
|---|---:|---:|---:|---:|---:|---:|
| ExactMatch (auto) | 58 | 44.8 % | 60.3 % | 1.109 | 2.06× | 1.108 |
| ExactMatch (uçtan uca, karar dahil) | 58 | 39.7 % | 63.8 % | 1.012 | 1.67× | 1.051 |
| Allmer 2016 kuralı | 58 | 31.0 % | 56.9 % | 1.176 | 2.67× | 1.142 |
| her zaman BoyerMooreSearch | 58 | 3.4 % | 5.2 % | 1.414 | 2.06× | 1.331 |
| her zaman HorspoolSearch | 58 | 31.0 % | 58.6 % | 1.218 | 3.85× | 1.193 |
| her zaman ShiftOrSearch | 58 | 8.6 % | 12.1 % | 1.923 | 3.93× | 1.769 |
| her zaman KmpSearch | 58 | 0.0 % | 0.0 % | 2.216 | 3.92× | 1.985 |
| her zaman AhoCorasickSearch | 58 | 0.0 % | 3.4 % | 2.600 | 4.46× | 2.222 |
| her zaman WuManberSearch | 58 | 22.4 % | 27.6 % | 1.289 | 2.35× | 1.324 |
| her zaman Bm4DnaDsSearch | 58 | 31.0 % | 55.2 % | 1.260 | 4.23× | 1.200 |
| her zaman Bm4DnaHmbsSearch | 58 | 3.4 % | 12.1 % | 1.773 | 6.83× | 1.746 |

## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)

| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |
|---|---|---:|---:|---:|---:|---:|
| görülen (DNA, protein, kod) | ExactMatch (auto) | 60 | 56.7 % | 73.3 % | 1.062 | 1.58× |
| görülen (DNA, protein, kod) | ExactMatch (uçtan uca, karar dahil) | 60 | 18.3 % | 30.0 % | 1.351 | 2.94× |
| görülen (DNA, protein, kod) | Allmer 2016 kuralı | 60 | 20.0 % | 50.0 % | 1.168 | 2.18× |
| görülmeyen (log, ikili, metin) | ExactMatch (auto) | 60 | 53.3 % | 68.3 % | 1.100 | 2.06× |
| görülmeyen (log, ikili, metin) | ExactMatch (uçtan uca, karar dahil) | 60 | 21.7 % | 38.3 % | 1.251 | 3.10× |
| görülmeyen (log, ikili, metin) | Allmer 2016 kuralı | 60 | 25.0 % | 51.7 % | 1.217 | 2.67× |

## Molekülün kendi yükü

Molekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan 1.141, %90'lık dilim 2.312. (Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)

## En kötü 5 seçim

| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |
|---:|---|---:|---:|---|---|---:|---|---:|---:|
| 34 | binary | 208307 | 1 | 9 | BoyerMooreSearch | 4.750 | ShiftOrSearch | 2.306 | 2.06× |
| 94 | binary | 284767 | 1 | 20 | Bm4DnaHmbsSearch | 4.399 | WuManberSearch | 2.511 | 1.75× |
| 118 | binary | 56995 | 1 | 17 | Bm4DnaHmbsSearch | 1.121 | ShiftOrSearch | 0.663 | 1.69× |
| 40 | binary | 62388 | 1 | 5 | BoyerMooreSearch | 2.825 | ShiftOrSearch | 1.703 | 1.66× |
| 28 | binary | 210796 | 1 | 23 | Bm4DnaHmbsSearch | 3.436 | WuManberSearch | 2.126 | 1.62× |

## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi

| Atom | En hızlı | Molekül seçti |
|---|---:|---:|
| BoyerMooreSearch | 6 | 8 |
| HorspoolSearch | 51 | 51 |
| ShiftOrSearch | 9 | 0 |
| KmpSearch | 0 | 0 |
| AhoCorasickSearch | 0 | 0 |
| WuManberSearch | 25 | 31 |
| Bm4DnaDsSearch | 27 | 25 |
| Bm4DnaHmbsSearch | 2 | 5 |
