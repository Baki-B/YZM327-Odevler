// Veri şekli (shape): molekülün karar verirken baktığı sayılar.
//   n        metin uzunluğu (ilk kaydın)
//   sigma    metindeki farklı karakter sayısı (σ)
//   sigmaEff etkin alfabe büyüklüğü 1/Σp² (harfler eşit sıklıkta değilse σ'dan küçüktür)
//   k        desen sayısı
//   mMin, mMax, mMean  desen uzunlukları
// 16 384 karakterden uzun metinde σ ve σe, metne eşit aralıklarla yayılmış 64 parçadan
// (her biri 256 karakter, toplam 16 K karakter) sayılır; bu deterministiktir.
// (v3'e kadar parçalar 4096 karakterdi ve 262 144 karaktere kadar metin tam sayılıyordu.
// Teslim öncesi denetimde bu sayımın küçük ve tek desenli girdide aramanın kendisi kadar
// sürdüğü görüldü: 200 000 karakterlik proteinde ~0,9 ms. v4'te sayım en fazla 16 384
// karakterdir. Bkz. rapor bölüm 6–7, KARARLAR.md.)

import { foldAsciiUnit } from './functions/alphabet.js';

const COUNTS = new Uint32Array(0x10000);
const TOUCHED = new Uint16Array(0x10000);
const SAMPLE_BLOCKS = 64;
const BLOCK = 256;
/** Tam sayılan en uzun metin; daha uzununda örneklenir. */
export const SAMPLE_LIMIT = SAMPLE_BLOCKS * BLOCK;

export function computeShape(entry, params) {
  const { patterns, ignoreCase = false } = params;
  const seq = entry.seq;
  const n = seq.length;
  // Sayaç dizisi her çağrıda yeniden ayrılmaz: yalnızca dokunulan hücreler sonunda sıfırlanır.
  // (İlk sürüm her kararda 256 KB ayırıp 65 536 hücreyi tarıyordu; küçük girdide bu,
  // aramanın kendisi kadar sürüyordu.)
  const counts = COUNTS;
  const touched = TOUCHED;
  let distinct = 0;
  let counted = 0;
  const countRange = (from, to) => {
    if (ignoreCase) {
      for (let i = from; i < to; i++) {
        const c = foldAsciiUnit(seq.charCodeAt(i));
        if (counts[c]++ === 0) touched[distinct++] = c;
      }
    } else {
      for (let i = from; i < to; i++) {
        const c = seq.charCodeAt(i);
        if (counts[c]++ === 0) touched[distinct++] = c;
      }
    }
    counted += to - from;
  };
  const sampled = n > SAMPLE_LIMIT;
  if (!sampled) countRange(0, n);
  else {
    const step = Math.floor((n - BLOCK) / (SAMPLE_BLOCKS - 1));
    for (let b = 0; b < SAMPLE_BLOCKS; b++) countRange(b * step, b * step + BLOCK);
  }
  const sigma = distinct;
  let sumSq = 0;
  for (let j = 0; j < distinct; j++) {
    const c = touched[j];
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
