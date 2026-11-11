# Kalibrasyon uydurma kalitesi

Makine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 çekirdek, Node v22.23.4, 2026-11-11T13:34:05.049Z

| Atom | Vaka | Medyan göreli hata | %90 göreli hata | Katsayılar |
|---|---:|---:|---:|---|
| BoyerMooreSearch | 180 | 17.4 % | 35.9 % | fixed=1.85e-5, base=3.05e-9, perPattern=7.17e-6, out=4.17e-7, scan=6.97e-9, prep=0.00e+0 |
| HorspoolSearch | 180 | 9.8 % | 28.2 % | fixed=1.58e-5, base=2.37e-9, perPattern=3.81e-6, out=8.39e-8, scan=4.61e-9, verify=1.80e-8, prep=0.00e+0 |
| ShiftOrSearch | 144 | 14.5 % | 34.9 % | fixed=3.01e-5, base=5.07e-9, perPattern=6.49e-6, out=8.58e-8, scan=2.22e-9, prep=8.98e-8 |
| KmpSearch | 180 | 19.0 % | 41.5 % | fixed=9.39e-6, base=3.65e-9, perPattern=4.66e-6, out=8.65e-7, scan=3.52e-9, prep=0.00e+0 |
| AhoCorasickSearch | 180 | 15.2 % | 34.5 % | fixed=5.92e-5, base=8.86e-9, perPattern=8.21e-7, out=1.12e-7, scan=0.00e+0, big=2.37e-10, prep=2.19e-9 |
| WuManberSearch | 180 | 16.2 % | 38.2 % | fixed=3.03e-5, base=2.26e-9, perPattern=1.68e-6, out=0.00e+0, scan=5.83e-9, verify=1.08e-7, prep=0.00e+0, table=4.46e-10 |
| Bm4DnaDsSearch | 180 | 10.9 % | 33.5 % | fixed=1.64e-5, base=2.40e-9, perPattern=4.08e-6, out=8.60e-8, scan=4.69e-9, verify=1.49e-8, prep=0.00e+0 |
| Bm4DnaHmbsSearch | 180 | 19.5 % | 53.1 % | fixed=3.20e-5, base=3.22e-9, perPattern=1.54e-5, out=0.00e+0, scan=4.61e-10, windows=6.64e-9, prep=0.00e+0, table=5.93e-10 |

Kalibrasyon kümesinin kendisinde seçim (görülmüş veri, yalnızca tanı): en hızlıyı seçme %73.3, yavaşlama geometrik ortalaması 1.032, en kötü 1.42×
