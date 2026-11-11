// bm4DNADS (Allmer 2016): kısa desenler için Boyer-Moore çeşidi.
// İki hızlandırma (Hume & Sunday 1991'deki "ayarlı Boyer-Moore" ile aynı fikir):
//
// 1) Sentinel (bekçi): Desenin bir kopyası metnin sonuna eklenir. Böylece atlama
//    döngüsü "metnin sonuna geldim mi?" diye her adımda sormak zorunda kalmaz;
//    döngü en geç bu kopyada durur.
// 2) Üç kez açılmış atlama döngüsü: Desenin son karakteri için kayma 0 yapılır.
//    Döngü, kayma 0 olana kadar (yani pencerenin sonu desenin son karakterine
//    denk gelene kadar) art arda üç adım atar; dal sayısı azalır.
//
// Pencere sonu desenin son karakterine denk gelince desen tam doğrulanır ve
// Horspool kayması (shift2) kadar ilerlenir.
// Karmaşıklık: ön işleme O(m + σ), arama tipik O(n/m), en kötü O(n·m).
//
// Makaleden sapmalar (gerekçeler docs/sapmalar.md içinde):
//  - Metnin sonu: döngü sentinel'de durduğunda j ≥ n kontrolü yapılır; sentinel
//    içindeki sahte eşleşmeler raporlanmaz.
//  - shift2, son karakterin desenin İLK m−1 karakterindeki en sağ yerinden
//    hesaplanır (yoksa m). Son karakterin kendisi sayılırsa kayma 0 olur ve
//    döngü sonsuza kadar döner.

export function prepareBm4DnaDs(p, sigma) {
  const m = p.length;
  const skip = new Int32Array(sigma).fill(m);
  for (let i = 0; i < m - 1; i++) skip[p[i]] = m - 1 - i;
  const shift2 = skip[p[m - 1]]; // son karakter için gerçek Horspool kayması (≥ 1)
  skip[p[m - 1]] = 0;
  return { p, skip, shift2 };
}

/**
 * text dizisinin uzunluğu en az n + m olmalı (sentinel yeri).
 * Sentinel her desen için yeniden yazılır; dizinin n'den sonraki kısmı serbesttir.
 */
export function searchBm4DnaDs(prep, u, text, n, hits) {
  const { p, skip, shift2 } = prep;
  const m = p.length;
  if (m > n) return;
  for (let i = 0; i < m; i++) text[n + i] = p[i]; // sentinel

  const last = m - 1;
  let j = last; // pencerenin son karakterinin metindeki yeri
  for (;;) {
    let k = skip[text[j]];
    while (k !== 0) {
      j += k; k = skip[text[j]];
      j += k; k = skip[text[j]];
      j += k; k = skip[text[j]];
    }
    if (j >= n) return; // sentinel'e ulaşıldı
    const start = j - last;
    let i = 0;
    while (i < last && p[i] === text[start + i]) i++;
    if (i === last) hits.add(u, start);
    j += shift2;
  }
}
