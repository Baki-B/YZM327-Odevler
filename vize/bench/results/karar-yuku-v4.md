# Karar süresi (doğrudan ölçüm) ve örneklem doğruluğu, v4

Makine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 çekirdek, Node v22.23.4, 2026-11-13T07:49:26.256Z.

Her vakada D ve E kümesinin girdisi yeniden üretildi (aynı tohumlar). Süreler ms; her biri ısınma + 9 bloğun medyanı, blok ≥ 2 ms. "Karar" = molekülü kurup decide() çağırmak − seçilen atomu tek başına kurmak (atom kurulumu her durumda yapılır). Karar / atom oranının paydası, D ve E ölçümlerindeki seçilen atom süresidir (aynı makinede, ayrı çalıştırma).

| Küme | Vaka | Şekil v3 (medyan) | Şekil v4 (medyan) | Şekil v3 en büyük | Şekil v4 en büyük | Karar v4 (medyan) | Karar / atom (medyan) | Karar / atom (%90) | Karar / atom (en büyük) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D | 120 | 0.648 | 0.063 | 2.013 | 0.099 | 0.116 | 0.041 | 0.229 | 0.718 |
| E | 120 | 0.515 | 0.065 | 1.642 | 0.102 | 0.116 | 0.114 | 0.608 | 1.241 |

## v4 örnekleminin doğruluğu (tam sayıma göre)

| Küme | Vaka | Örneklenen (n > 16 384) | σe göreli hata (medyan) | σe göreli hata (en büyük) | σ eksik sayılan vaka | σ en büyük eksik oran |
|---|---:|---:|---:|---:|---:|---:|
| D | 120 | 112 | 0.15 % | 7.00 % | 29 | 23.5 % |
| E | 120 | 109 | 0.18 % | 11.13 % | 27 | 25.0 % |
