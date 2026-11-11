// Boyer-Moore (Boyer & Moore 1977): kötü karakter + iyi sonek kaymaları.
// Pencere sağdan sola karşılaştırılır; uyuşmazlıkta iki kuraldan büyük olanı kadar kayılır.
// Karmaşıklık: ön işleme O(m + σ), arama en kötü O(n·m), tipik olarak alt doğrusal.

/** İyi sonek tablosu (Charras & Lecroq'taki klasik kuruluş). shift[j+1]: j'de uyuşmazlıkta kayma; shift[0]: tam eşleşmede kayma. */
export function goodSuffixShifts(p) {
  const m = p.length;
  const shift = new Int32Array(m + 1);
  const border = new Int32Array(m + 1);
  let i = m;
  let j = m + 1;
  border[i] = j;
  while (i > 0) {
    while (j <= m && p[i - 1] !== p[j - 1]) {
      if (shift[j] === 0) shift[j] = j - i;
      j = border[j];
    }
    i--;
    j--;
    border[i] = j;
  }
  j = border[0];
  for (i = 0; i <= m; i++) {
    if (shift[i] === 0) shift[i] = j;
    if (i === j) j = border[j];
  }
  return shift;
}

export function prepareBoyerMoore(p, sigma) {
  const last = new Int32Array(sigma).fill(-1); // her karakterin desendeki en sağ yeri
  for (let i = 0; i < p.length; i++) last[p[i]] = i;
  return { p, last, good: goodSuffixShifts(p) };
}

export function searchBoyerMoore(prep, u, text, n, hits) {
  const { p, last, good } = prep;
  const m = p.length;
  let s = 0;
  while (s <= n - m) {
    let j = m - 1;
    while (j >= 0 && p[j] === text[s + j]) j--;
    if (j < 0) {
      hits.add(u, s);
      s += good[0];
    } else {
      const bad = j - last[text[s + j]];
      const gs = good[j + 1];
      s += gs > bad ? gs : bad;
    }
  }
}
