// Horspool (Horspool 1980): yalnızca kötü karakter kayması.
// Pencerenin SON karakterine bakılır; bu karakter desenin ilk m−1 karakterinde
// en sağda nerede geçiyorsa pencere o kadar kaydırılır, hiç geçmiyorsa m kadar.
// Karmaşıklık: ön işleme O(m + σ); arama tipik O(n/m), en kötü O(n·m).

export function prepareHorspool(p, sigma) {
  const m = p.length;
  const shift = new Int32Array(sigma).fill(m);
  for (let i = 0; i < m - 1; i++) shift[p[i]] = m - 1 - i;
  return { p, shift };
}

export function searchHorspool(prep, u, text, n, hits) {
  const { p, shift } = prep;
  const m = p.length;
  const lastIdx = m - 1;
  const lastChar = p[lastIdx];
  let s = 0;
  while (s <= n - m) {
    const c = text[s + lastIdx];
    if (c === lastChar) {
      let j = 0;
      while (j < lastIdx && p[j] === text[s + j]) j++;
      if (j === lastIdx) hits.add(u, s);
    }
    s += shift[c];
  }
}
