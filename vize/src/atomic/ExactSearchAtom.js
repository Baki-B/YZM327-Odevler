// Bütün tam eşleştirme atomlarının ortak sınıfı (Template Method deseni).
//
// Ortak işler burada bir kez yapılır:
//   1. parametre kontrolü (boş liste / boş desen → hata),
//   2. ignoreCase (yalnızca ASCII harfler),
//   3. alfabe küçültme (karakterleri küçük sayılara çevirme),
//   4. aynı desenin tekrarlarını tek desene indirip sonuçta yeniden çoğaltma,
//   5. çıktının sözleşmedeki sıraya konması.
// Alt sınıf yalnızca iki "kanca" (hook) yazar:
//   prepare()                 → desenleri bir kez ön işler (kaydırma tablosu vb.)
//   scanText(text, n, hits)   → kimlik dizisine çevrilmiş metinde arar, hits.add(u, konum) çağırır.

import { buildAlphabet, encode, foldAscii } from '../functions/alphabet.js';
import { HitCollector } from '../functions/hits.js';

export const TASK = 'sequence.pattern-match.exact';

/** Parametreleri sözleşmeye göre denetler; kopyasını döndürür. */
export function validateParams(params) {
  if (params === null || typeof params !== 'object') {
    throw new TypeError('Parametreler bir nesne olmalı: { patterns, ignoreCase }');
  }
  const { patterns, ignoreCase = false } = params;
  if (!Array.isArray(patterns) || patterns.length === 0) {
    throw new TypeError('patterns boş olmayan bir dizi olmalı');
  }
  for (let i = 0; i < patterns.length; i++) {
    if (typeof patterns[i] !== 'string' || patterns[i].length === 0) {
      throw new TypeError(`patterns[${i}] boş olmayan bir dizgi olmalı`);
    }
  }
  if (typeof ignoreCase !== 'boolean') {
    throw new TypeError('ignoreCase true ya da false olmalı');
  }
  return { patterns: patterns.slice(), ignoreCase };
}

/** Bir FASTA.Entry nesnesini denetler. */
export function validateEntry(entry) {
  if (entry === null || typeof entry !== 'object' ||
      typeof entry.header !== 'string' || typeof entry.seq !== 'string') {
    throw new TypeError('Girdi bir FASTA.Entry olmalı: { header: string, seq: string }');
  }
}

export class ExactSearchAtom {
  static manifest = null;
  static selection = null;

  constructor(params) {
    const { patterns, ignoreCase } = validateParams(params);
    this.patterns = patterns;
    this.ignoreCase = ignoreCase;

    const alpha = buildAlphabet(patterns, ignoreCase);
    this.alphabet = alpha.map;
    this.sigma = alpha.size; // desen alfabesi + 1 (0 = "desende yok")

    // Aynı desen birden çok kez verilmişse bir kez aranır, sonuçta kopyalanır.
    const seen = new Map();
    this.unique = [];   // benzersiz desenler, kimlik dizisi (Uint16Array) olarak
    this.groups = [];   // groups[u] = listedeki sıraları
    for (let i = 0; i < patterns.length; i++) {
      const key = ignoreCase ? foldAscii(patterns[i]) : patterns[i];
      let u = seen.get(key);
      if (u === undefined) {
        u = this.unique.length;
        seen.set(key, u);
        this.unique.push(encode(patterns[i], this.alphabet));
        this.groups.push([]);
      }
      this.groups[u].push(i);
    }
    this.maxLen = 0;
    this.minLen = Infinity;
    for (const p of this.unique) {
      if (p.length > this.maxLen) this.maxLen = p.length;
      if (p.length < this.minLen) this.minLen = p.length;
    }
    this.prepare();
  }

  /** Alt sınıf: desenleri bir kez ön işler. */
  prepare() {}

  /** Alt sınıf: metnin sonuna kaç boş hücre eklenmesi gerektiği (sentinel için). */
  padding() {
    return 0;
  }

  /** Alt sınıf: text[0..n) içinde arar ve her eşleşme için hits.add(u, konum) çağırır. */
  scanText(_text, _n, _hits) {
    throw new Error(`${this.constructor.name}.scanText() yazılmamış`);
  }

  /** Bir FASTA.Entry için Sequence.Match nesneleri üretir. */
  *process(entry) {
    validateEntry(entry);
    const n = entry.seq.length;
    const hits = new HitCollector(this.groups, this.patterns.length);
    if (n > 0 && this.minLen <= n) {
      const text = encode(entry.seq, this.alphabet, this.padding());
      this.scanText(text, n, hits);
    }
    yield* hits.matches(entry.header, this.patterns);
  }
}
