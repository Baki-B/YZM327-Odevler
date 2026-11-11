// Wu-Manber (Wu & Manber 1994): çok desenli blok kayması.
// Bütün desenler en kısa desenin uzunluğuna (mMin) kırpılmış gibi düşünülür.
// Pencerenin son B karakterlik bloğuna bakılır:
//   SHIFT[blok] > 0 ise pencere o kadar kayar (hiçbir desen burada bitemez);
//   SHIFT[blok] = 0 ise bu blokla biten desenler (HASH kovası) tam olarak doğrulanır.
// Hiçbir desende geçmeyen bir blok için güvenli kayma mMin − B + 1'dir.
// Karmaşıklık: ön işleme O(Σ mMin + tablo), arama tipik O(n·B / kayma).

import { bitsFor } from './expect.js';

const MAX_TABLE_BITS = 18;

/** Tablo boyu (bit): olası blok sayısı küçükse birebir, değilse desenlerdeki blok sayısının ~8 katı. */
export function tableBitsFor(sigma, B, k, mMin) {
  const bits = bitsFor(sigma - 1);
  const wanted = Math.min(MAX_TABLE_BITS, Math.max(8, Math.ceil(Math.log2(k * (mMin - B + 1) * 8))));
  return bits * B <= wanted ? bits * B : wanted;
}

/** Blok uzunluğu B: tabloyu yeterince seyrek tutacak kadar uzun, mMin'den kısa. */
export function chooseBlock(sigmaEff, k, mMin) {
  const s = Math.max(2, sigmaEff);
  const b = Math.ceil(Math.log(2 * k * mMin) / Math.log(s));
  return Math.max(1, Math.min(mMin, b, 8));
}

export function prepareWuManber(patterns, sigma, block) {
  let mMin = Infinity;
  for (const p of patterns) if (p.length < mMin) mMin = p.length;
  const B = Math.max(1, Math.min(block, mMin));

  // Blok → tablo indisi. Olası blok sayısı küçükse birebir (çakışmasız), değilse karma (hash).
  // Tablo boyu desenlerdeki blok sayısının ~8 katıyla sınırlanır: küçük girdide
  // 2^18 elemanlık tabloyu sıfırlamak aramanın kendisinden uzun sürer.
  const bits = bitsFor(sigma - 1);
  const tableBits = tableBitsFor(sigma, B, patterns.length, mMin);
  const exact = tableBits === bits * B;
  const size = 1 << tableBits;
  const mask = size - 1;

  const dflt = mMin - B + 1;
  const shift = new Int32Array(size).fill(dflt);
  const head = new Int32Array(size).fill(-1); // HASH kovası: bağlı liste başı
  const next = new Int32Array(patterns.length).fill(-1);

  const hashAt = (arr, end) => {
    let h = 0;
    if (exact) {
      for (let j = end - B + 1; j <= end; j++) h = (h << bits) | arr[j];
      return h;
    }
    for (let j = end - B + 1; j <= end; j++) h = (Math.imul(h, 0x9e3779b1) + arr[j]) | 0;
    return (h ^ (h >>> 15)) & mask;
  };

  for (let u = 0; u < patterns.length; u++) {
    const p = patterns[u];
    for (let e = B - 1; e < mMin; e++) {
      const h = hashAt(p, e);
      const sft = mMin - 1 - e;
      if (sft < shift[h]) shift[h] = sft; // çakışmada en küçük kayma (güvenli olan) kalır
    }
    const h = hashAt(p, mMin - 1);
    next[u] = head[h];
    head[h] = u;
  }
  return { patterns, mMin, B, shift, head, next, hashAt };
}

export function searchWuManber(prep, text, n, hits) {
  const { patterns, mMin, shift, head, next, hashAt } = prep;
  let i = mMin - 1; // pencerenin (kırpılmış) son karakteri
  while (i < n) {
    const h = hashAt(text, i);
    const s = shift[h];
    if (s > 0) {
      i += s;
      continue;
    }
    const pos = i - mMin + 1;
    for (let u = head[h]; u !== -1; u = next[u]) {
      const p = patterns[u];
      const m = p.length;
      if (pos + m > n) continue;
      let j = 0;
      while (j < m && p[j] === text[pos + j]) j++;
      if (j === m) hits.add(u, pos);
    }
    i += 1;
  }
}
