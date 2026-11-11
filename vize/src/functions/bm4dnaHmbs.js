// bm4DNAHMbs (Allmer 2016; Wu & Manber 1994): uzun desenler için q-gram kayması.
// Pencerenin son karakteri yerine son q karakterine (q-gram) bakılır. q-gram,
// karakter kimlikleri bit kaydırmayla ("bs": bit shift) birleştirilerek tek bir
// sayıya (özet) çevrilir ve kaydırma tablosunda aranır. Uzun desende bir q-gramın
// desende geçme olasılığı tek bir karakterinkinden çok daha düşüktür; bu yüzden
// kaymalar m − q + 1'e yaklaşır.
//
// Kaydırma kuralı:
//   - q-gram desende (son konum hariç) e konumunda bitiyorsa kayma m − 1 − e (en küçüğü),
//   - desende hiç geçmiyorsa kayma m − q + 1. (Makalenin ipucu sorusu: m DEĞİL.
//     m kadar kaymak, son q−1 karakterle başlayan bir eşleşmeyi atlayabilir.)
//   - desenin son q-gramı için kayma 0 → tam doğrulama, sonra shift2 kadar ilerle.
// Karmaşıklık: ön işleme O(m + 2^(q·b)), arama tipik O(n·q/(m−q+1)).

import { bitsFor } from './expect.js';

export const TABLE_BITS = 16;

/** q: tablo 2^16 elemanı aşmayacak kadar büyük, m'den büyük olmayan blok uzunluğu. */
export function chooseQ(sigma, m) {
  const bits = bitsFor(sigma - 1);
  return Math.max(1, Math.min(m, Math.floor(TABLE_BITS / bits)));
}

export function prepareBm4DnaHmbs(p, sigma) {
  const m = p.length;
  const bits = bitsFor(sigma - 1);
  const q = chooseQ(sigma, m);
  const hashAt = (arr, end) => {
    let h = 0;
    for (let j = end - q + 1; j <= end; j++) h = (h << bits) | arr[j];
    return h;
  };
  // Tablo seyrek tutulur: yalnızca desende geçen q-gramların kaymaları saklanır.
  const entries = new Map();
  for (let e = q - 1; e < m - 1; e++) entries.set(hashAt(p, e), m - 1 - e); // e büyüdükçe kayma küçülür
  const lastHash = hashAt(p, m - 1);
  const dflt = m - q + 1;
  const shift2 = entries.has(lastHash) ? entries.get(lastHash) : dflt;
  entries.set(lastHash, 0);
  return { p, q, bits, dflt, shift2, keys: Int32Array.from(entries.keys()), vals: Int32Array.from(entries.values()) };
}

/** Bütün desenlerin paylaştığı tablo: değer = kayma + 1, 0 = "bu q-gram desende yok". */
export function createTable() {
  return new Int32Array(1 << TABLE_BITS);
}

export function searchBm4DnaHmbs(prep, u, text, n, hits, table) {
  const { p, q, bits, dflt, shift2, keys, vals } = prep;
  const m = p.length;
  if (m > n) return;
  for (let i = 0; i < keys.length; i++) table[keys[i]] = vals[i] + 1;

  let j = m - 1;
  while (j < n) {
    let h = 0;
    for (let t = j - q + 1; t <= j; t++) h = (h << bits) | text[t];
    const v = table[h];
    if (v === 1) { // kayma 0: tam doğrula
      const start = j - m + 1;
      let i = 0;
      while (i < m && p[i] === text[start + i]) i++;
      if (i === m) hits.add(u, start);
      j += shift2;
    } else {
      j += v === 0 ? dflt : v - 1;
    }
  }
  for (let i = 0; i < keys.length; i++) table[keys[i]] = 0; // tabloyu bir sonraki desen için temizle
}
