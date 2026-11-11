// Testlerde ortak yardımcılar.
import { readFileSync } from 'node:fs';
import { parseFasta } from '../../src/fasta.js';
import { registry } from '../../src/registry.js';
import { NaiveSearch } from '../../src/atomic/NaiveSearch.js';

/** NaiveSearch dışındaki bütün kayıtlı atomlar (sınanan algoritmalar). */
export const ATOMS = registry.names().filter((n) => n !== 'NaiveSearch').map((n) => registry.get(n));
/** Referans dahil bütün atomlar (sözleşme testleri için). */
export const ALL_ATOMS = registry.names().map((n) => registry.get(n));

export function collect(Atom, params, entries) {
  const atom = new Atom(params);
  const out = [];
  for (const e of entries) for (const m of atom.process(e)) out.push(m);
  return out;
}

export function oracle(params, entries) {
  return collect(NaiveSearch, params, entries);
}

export function loadFasta(name) {
  return parseFasta(readFileSync(new URL(`../data/${name}`, import.meta.url), 'utf8'));
}

/** İki eşleşme listesinin ilk farkını okunur biçimde verir (hata iletisi için). */
export function firstDiff(a, b) {
  const n = Math.max(a.length, b.length);
  for (let i = 0; i < n; i++) {
    if (JSON.stringify(a[i]) !== JSON.stringify(b[i])) {
      return `sıra ${i}: beklenen ${JSON.stringify(b[i])}, gelen ${JSON.stringify(a[i])} (uzunluk ${a.length} / ${b.length})`;
    }
  }
  return null;
}

/**
 * Büyük listeler için eşitlik denetimi. Başarısızlıkta yalnızca ilk farkı yazar;
 * assert.deepEqual'ın büyük dizilerde ürettiği dev fark metni hem çok yavaş hem
 * bellek açısından pahalıdır (mutasyon denetiminde süreçleri bellek sınırına itiyordu).
 */
export function assertSameMatches(got, want, label = '') {
  const d = firstDiff(got, want);
  if (d !== null) throw new Error(`${label ? label + ': ' : ''}${d}`);
}
