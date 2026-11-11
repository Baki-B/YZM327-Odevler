// Shift-Or (Baeza-Yates & Gonnet 1992): bit paralel arama.
// Desenin her konumu 32 bitlik bir sayının bir bitine karşılık gelir. Durum D'nin
// i. biti 0 ise "desenin ilk i+1 karakteri metnin şu an bittiği yerde eşleşiyor"
// demektir. Her metin karakterinde tek satır: D = (D << 1) | maske[c].
// Karmaşıklık: ön işleme O(m + σ), arama O(n) (m ≤ 32 için).
//
// Ödev tablosu "m ≤ 32 için" diyor. Yanlış sonuç vermemek için daha uzun desenler
// de desteklenir: ilk 32 karakter bit paralel aranır, aday konumda kalan karakterler
// tek tek doğrulanır (süzgeç + doğrulama). Bu durumda atom applicable() ile kendini
// "uygun değil" ilan eder; yani molekül onu seçmez, ama adıyla zorlanırsa doğru çalışır.

export const WORD = 32;

export function prepareShiftOr(p, sigma) {
  const m = p.length;
  const w = m < WORD ? m : WORD;
  const masks = new Int32Array(sigma).fill(-1); // bütün bitler 1
  for (let i = 0; i < w; i++) masks[p[i]] &= ~(1 << i);
  return { p, masks, w, hit: 1 << (w - 1) };
}

export function searchShiftOr(prep, u, text, n, hits) {
  const { p, masks, w, hit } = prep;
  const m = p.length;
  let d = -1;
  if (m === w) {
    for (let i = 0; i < n; i++) {
      d = (d << 1) | masks[text[i]];
      if ((d & hit) === 0) hits.add(u, i - m + 1);
    }
    return;
  }
  // m > 32: ilk 32 karakter süzgeç, kalanı doğrulama.
  const limit = n - m + w; // süzgecin bitebileceği son yer + 1
  for (let i = 0; i < limit; i++) {
    d = (d << 1) | masks[text[i]];
    if ((d & hit) === 0) {
      const start = i - w + 1;
      let j = w;
      while (j < m && p[j] === text[start + j]) j++;
      if (j === m) hits.add(u, start);
    }
  }
}
