# Kalibrasyon uydurma kalitesi

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, Node v22.23.4, 2026-11-11T13:34:05.049Z

| Atom | Vaka | Medyan göreli hata | %90 göreli hata | Katsayılar |
|---|---:|---:|---:|---|
| BoyerMooreSearch | 180 | 17.6 % | 34.9 % | fixed=1.85e-5, base=3.04e-9, perPattern=7.16e-6, scan=7.10e-9, prep=0.00e+0, out=1.19e-7 |
| HorspoolSearch | 180 | 9.2 % | 28.4 % | fixed=1.55e-5, base=2.38e-9, perPattern=3.82e-6, scan=4.54e-9, verify=1.81e-8, prep=0.00e+0, out=1.19e-7 |
| ShiftOrSearch | 144 | 14.4 % | 35.3 % | fixed=2.97e-5, base=5.08e-9, perPattern=6.57e-6, scan=2.21e-9, prep=8.72e-8, out=1.19e-7 |
| KmpSearch | 180 | 21.2 % | 42.2 % | fixed=8.98e-6, base=3.65e-9, perPattern=4.83e-6, scan=3.59e-9, prep=0.00e+0, out=1.19e-7 |
| AhoCorasickSearch | 180 | 13.6 % | 32.5 % | fixed=5.92e-5, base=8.85e-9, perPattern=7.02e-7, scan=0.00e+0, big=1.88e-10, prep=2.20e-9, out=1.19e-7 |
| WuManberSearch | 180 | 16.3 % | 37.3 % | fixed=2.97e-5, base=2.33e-9, perPattern=1.67e-6, scan=5.64e-9, verify=7.91e-8, prep=0.00e+0, table=4.27e-10, out=1.19e-7 |
| Bm4DnaDsSearch | 180 | 11.1 % | 32.3 % | fixed=1.61e-5, base=2.41e-9, perPattern=4.08e-6, scan=4.60e-9, verify=1.51e-8, prep=0.00e+0, out=1.19e-7 |
| Bm4DnaHmbsSearch | 180 | 19.6 % | 53.3 % | fixed=3.21e-5, base=3.24e-9, perPattern=1.54e-5, scan=4.69e-10, windows=6.48e-9, prep=0.00e+0, table=5.73e-10, out=1.19e-7 |

Ortak eşleşme başına maliyet (out): 1.19e-7 s. Atom başına serbest uydurmada bulunan değerler: BoyerMoore 4.1e-7, Horspool 1.7e-7, ShiftOr 1.1e-7, Kmp 7.2e-7, AhoCorasick 1.2e-7, WuManber 7.0e-8, Bm4DnaDs 1.2e-7, Bm4DnaHmbs 1.6e-8.

Kalibrasyon kümesinin kendisinde seçim (görülmüş veri, yalnızca tanı): en hızlıyı seçme %74.4, yavaşlama geometrik ortalaması 1.028, en kötü 1.42×
