# Kalibrasyon uydurma kalitesi

Makine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 çekirdek, Node v22.23.4, 2026-11-13T07:39:15.201Z

| Atom | Vaka | Medyan göreli hata | %90 göreli hata | Katsayılar |
|---|---:|---:|---:|---|
| BoyerMooreSearch | 180 | 21.3 % | 44.1 % | fixed=1.53e-5, base=6.37e-9, perPattern=1.79e-5, scan=1.01e-8, prep=0.00e+0, out=3.31e-7 |
| HorspoolSearch | 180 | 15.5 % | 34.7 % | fixed=1.21e-5, base=4.79e-9, perPattern=7.81e-6, scan=6.19e-9, verify=2.62e-8, prep=0.00e+0, out=3.31e-7 |
| ShiftOrSearch | 144 | 18.5 % | 45.4 % | fixed=5.96e-5, base=9.20e-9, perPattern=5.73e-6, scan=3.42e-9, prep=1.68e-7, out=3.31e-7 |
| KmpSearch | 180 | 19.4 % | 40.9 % | fixed=0.00e+0, base=6.85e-9, perPattern=1.34e-5, scan=6.13e-9, prep=0.00e+0, out=3.31e-7 |
| AhoCorasickSearch | 180 | 17.2 % | 42.2 % | fixed=1.37e-4, base=1.52e-8, perPattern=0.00e+0, scan=0.00e+0, big=5.53e-10, prep=4.24e-9, out=3.31e-7 |
| WuManberSearch | 180 | 19.4 % | 47.2 % | fixed=3.54e-5, base=4.76e-9, perPattern=2.31e-6, scan=7.54e-9, verify=1.86e-7, prep=1.99e-8, table=0.00e+0, out=3.31e-7 |
| Bm4DnaDsSearch | 180 | 18.2 % | 37.9 % | fixed=1.49e-5, base=4.78e-9, perPattern=9.44e-6, scan=6.46e-9, verify=2.15e-8, prep=0.00e+0, out=3.31e-7 |
| Bm4DnaHmbsSearch | 180 | 23.6 % | 60.1 % | fixed=3.46e-5, base=6.62e-9, perPattern=3.32e-5, scan=5.94e-10, windows=9.74e-9, prep=0.00e+0, table=3.36e-10, out=3.31e-7 |

Ortak eşleşme başına maliyet (out): 3.31e-7 s. Atom başına serbest uydurmada bulunan değerler: BoyerMoore 6.8e-7, Horspool 3.0e-7, ShiftOr 1.5e-7, Kmp 1.1e-6, AhoCorasick 2.1e-7, WuManber 2.1e-8, Bm4DnaDs 3.6e-7, Bm4DnaHmbs 3.8e-7.

Kalibrasyon kümesinin kendisinde seçim (görülmüş veri, yalnızca tanı): en hızlıyı seçme %75.0, yavaşlama geometrik ortalaması 1.037, en kötü 1.78×
