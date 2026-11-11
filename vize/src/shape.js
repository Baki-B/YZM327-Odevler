// Veri şekli (shape): molekülün karar verirken baktığı sayılar.
//   n        metin uzunluğu (ilk kaydın)
//   sigma    metindeki farklı karakter sayısı (σ)
//   sigmaEff etkin alfabe büyüklüğü 1/Σp² (harfler eşit sıklıkta değilse σ'dan küçüktür)
//   k        desen sayısı
//   mMin, mMax, mMean  desen uzunlukları
// Çok uzun metinde σ, metne eşit aralıklarla yayılmış 64 parçadan (toplam 256 K
// karakter) sayılır; bu deterministiktir ve 10^6 karakterde ~1 ms yerine ~0,3 ms sürer.

import { foldAsciiUnit } from './functions/alphabet.js';

const COUNTS = new Uint32Array(0x10000);
const SAMPLE_BLOCKS = 64;
const BLOCK = 4096;

export function computeShape(entry, params) {
  const { patterns, ignoreCase = false } = params;
  const seq = entry.seq;
  const n = seq.length;
  // Sayaç dizisi her çağrıda yeniden ayrılmaz: yalnızca dokunulan hücreler sonunda sıfırlanır.
  // (İlk sürüm her kararda 256 KB ayırıp 65 536 hücreyi tarıyordu; küçük girdide bu,
  // aramanın kendisi kadar sürüyordu.)
  const counts = COUNTS;
  const touched = [];
  let counted = 0;
  const countRange = (from, to) => {
    for (let i = from; i < to; i++) {
      let c = seq.charCodeAt(i);
      if (ignoreCase) c = foldAsciiUnit(c);
      if (counts[c]++ === 0) touched.push(c);
    }
    counted += to - from;
  };
  const sampled = n > SAMPLE_BLOCKS * BLOCK;
  if (!sampled) countRange(0, n);
  else {
    const step = Math.floor((n - BLOCK) / (SAMPLE_BLOCKS - 1));
    for (let b = 0; b < SAMPLE_BLOCKS; b++) countRange(b * step, b * step + BLOCK);
  }
  const sigma = touched.length;
  let sumSq = 0;
  for (const c of touched) {
    const p = counts[c] / counted;
    sumSq += p * p;
    counts[c] = 0;
  }
  let mMin = Infinity, mMax = 0, total = 0;
  for (const p of patterns) {
    if (p.length < mMin) mMin = p.length;
    if (p.length > mMax) mMax = p.length;
    total += p.length;
  }
  return {
    n,
    sigma,
    sigmaEff: sumSq > 0 ? round(1 / sumSq) : 0,
    k: patterns.length,
    mMin,
    mMax,
    mMean: round(total / patterns.length),
    sampled,
  };
}

function round(x) {
  return Math.round(x * 1000) / 1000;
}
