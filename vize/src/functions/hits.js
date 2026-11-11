// Sonuç toplayıcı (hit collector).
//
// Algoritmalar eşleşmeleri kendi sıralarında bildirir (ör. Aho-Corasick bitiş
// konumuna göre). Toplayıcı her eşleşmeyi tek bir sayıya paketler:
//     anahtar = konum × k + desenin listedeki sırası
// ve sonunda bu sayıları sıralar. Böylece sözleşmedeki sıra (önce konum, eşitse
// desenin listedeki sırası) tek bir sayısal sıralamayla elde edilir.
// Aynı desen listede birden çok kez varsa (groups), her kopya ayrı raporlanır.

export class HitCollector {
  /**
   * @param {number[][]} groups groups[u] = benzersiz desen u'nun listedeki bütün sıraları
   * @param {number} k desen listesinin uzunluğu
   */
  constructor(groups, k) {
    this.groups = groups;
    this.k = k;
    this.keys = new Float64Array(64);
    this.count = 0;
  }

  /** Benzersiz desen u, metnin `pos` konumunda eşleşti. */
  add(u, pos) {
    const g = this.groups[u];
    if (this.count + g.length > this.keys.length) {
      const bigger = new Float64Array(Math.max(this.keys.length * 2, this.count + g.length));
      bigger.set(this.keys.subarray(0, this.count));
      this.keys = bigger;
    }
    const base = pos * this.k;
    for (let j = 0; j < g.length; j++) this.keys[this.count++] = base + g[j];
  }

  /** Sözleşme sırasında Sequence.Match nesneleri üretir. */
  *matches(header, patterns) {
    const keys = this.keys.subarray(0, this.count).sort();
    const k = this.k;
    for (let i = 0; i < keys.length; i++) {
      const key = keys[i];
      const idx = key % k;
      const position = (key - idx) / k;
      const pattern = patterns[idx];
      yield { header, pattern, position, length: pattern.length };
    }
  }
}
