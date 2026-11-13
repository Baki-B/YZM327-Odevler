# Ölçüm makineleri: v3 ve v4 kalibrasyonu

v3: Intel(R) Xeon(R) Processor @ 2.30GHz, Node v22.23.4, 2026-11-11T13:34:05.049Z

v4: Intel(R) Xeon(R) Processor @ 2.10GHz, Node v22.23.4, 2026-11-13T07:39:15.201Z

Aynı 180 vaka, aynı atomlar (1440 atom-vaka çifti). Atom kodu iki ölçüm arasında değişmedi.

| Ölçüt | Medyan | %10 | %90 |
|---|---:|---:|---:|
| v4 süresi / v3 süresi | 1.74 | 1.30 | 2.36 |
| tekrarlar arası en büyük / en küçük, v3 | 1.28 | 1.07 | 1.70 |
| tekrarlar arası en büyük / en küçük, v4 | 1.38 | 1.14 | 1.91 |

v4 makinesi aynı işi medyanda 1.74 kat uzun sürede yaptı ve tekrarlar arasında daha çok oynadı. Bu yüzden v3 (A, B, C) ile v4 (D, E) arasındaki farkın ne kadarının modelden, ne kadarının makineden geldiği ayrılamaz.
