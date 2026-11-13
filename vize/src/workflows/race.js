// "Atomları yarıştır": aynı girdide bütün aday atomları ölçer ve molekülün tahminiyle
// yan yana koyar. DOM'suz; saat dışarıdan verilir (tarayıcıda performance.now).
//
// Ölçüm kuralı bench/timing.js'teki dönüşümlü ölçümün sade bir kopyasıdır: ısınma turu,
// sonra her turda her atom bir kez (sıra kaydırılarak), tekrarların medyanı.
// Tarayıcıda yapılan ölçüm yalnızca gösterim amaçlıdır; rapordaki sayılar Node ölçümleridir.

import { registry as defaultRegistry } from '../registry.js';
import { ExactMatch } from '../molecules/ExactMatch.js';

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
}

/**
 * @param entries   FASTA.Entry dizisi
 * @param set       { patterns, ignoreCase }
 * @param options   { now, reps = 5, warmup = 1, registry, minBlockMs = 5 }
 * @returns {{ rows: [{ name, ms, estimatedMs, applicable, hits, samples }], selected, fastest, record }}
 */
export function raceAtoms(entries, set, { now, reps = 5, warmup = 1, registry = defaultRegistry, minBlockMs = 5 } = {}) {
  if (typeof now !== 'function') throw new Error('raceAtoms: now() saati verilmeli');
  const params = { patterns: set.patterns, ignoreCase: set.ignoreCase };
  const em = new ExactMatch({ ...params, strategy: 'auto' }, { registry });
  em.decide(entries[0] ?? { header: '', seq: '' });
  const record = em.record;
  const atoms = registry.candidates();
  const jobs = atoms.map((Atom) => {
    const job = () => {
      const a = new Atom(params);
      let c = 0;
      for (const e of entries) for (const _ of a.process(e)) c++;
      job.hits = c;
    };
    return job;
  });
  // Isınma ve blok büyüklüğü: tek çalıştırma çok kısaysa aynı iş blok içinde tekrarlanır.
  const inner = jobs.map((job) => {
    let first = 0;
    for (let w = 0; w < Math.max(1, warmup); w++) {
      const t0 = now();
      job();
      first = now() - t0;
    }
    return first >= minBlockMs ? 1 : Math.min(200, Math.ceil(minBlockMs / Math.max(first, 1e-3)));
  });
  const samples = jobs.map(() => []);
  for (let r = 0; r < reps; r++) {
    for (let j = 0; j < jobs.length; j++) {
      const i = (j + r) % jobs.length;
      const t0 = now();
      for (let x = 0; x < inner[i]; x++) jobs[i]();
      samples[i].push((now() - t0) / inner[i]);
    }
  }
  const rows = atoms.map((Atom, i) => {
    const name = Atom.manifest.name;
    const est = record.estimates[name];
    return { name, ms: median(samples[i]), samples: samples[i], hits: jobs[i].hits, applicable: est?.applicable !== false, estimatedMs: est?.applicable ? est.ms : null, reason: est?.reason ?? null };
  });
  const fastest = rows.reduce((a, b) => (b.ms < a.ms ? b : a)).name;
  return { rows, selected: record.selected, fastest, record };
}
