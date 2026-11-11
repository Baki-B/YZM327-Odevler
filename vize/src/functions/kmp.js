// Knuth-Morris-Pratt (Knuth, Morris & Pratt 1977).
// Metinde hiç geri dönülmez. Uyuşmazlıkta desenin "kendi içindeki tekrarına"
// (önek = sonek) bakılarak desende geri gidilir. Bu yüzden akış dostudur ve en
// kötü durumda bile doğrusaldır.
// Karmaşıklık: ön işleme O(m), arama O(n).

/** fail[i] = p[0..i] dizgisinin hem öneki hem soneki olan en uzun özel parçanın uzunluğu. */
export function failureFunction(p) {
  const m = p.length;
  const fail = new Int32Array(m);
  let k = 0;
  for (let i = 1; i < m; i++) {
    while (k > 0 && p[i] !== p[k]) k = fail[k - 1];
    if (p[i] === p[k]) k++;
    fail[i] = k;
  }
  return fail;
}

export function prepareKmp(p) {
  return { p, fail: failureFunction(p) };
}

export function searchKmp(prep, u, text, n, hits) {
  const { p, fail } = prep;
  const m = p.length;
  let q = 0;
  for (let i = 0; i < n; i++) {
    const c = text[i];
    while (q > 0 && p[q] !== c) q = fail[q - 1];
    if (p[q] === c) q++;
    if (q === m) {
      hits.add(u, i - m + 1);
      q = fail[q - 1];
    }
  }
}
