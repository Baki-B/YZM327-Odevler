// Doğrulama ölçütleri (Görev 4.4): validate.js, site üreticisi ve sayı denetimi aynı formülü kullanır.
import { registry } from '../../src/registry.js';

export const E2E = 'ExactMatch (uçtan uca, karar dahil)';

/** Allmer 2016 kuralı: m < 50 ise bm4DNADS, değilse bm4DNAHMbs (çok desende m = mMean). */
export function allmerRule(shape) {
  return shape.mMean < 50 ? 'Bm4DnaDsSearch' : 'Bm4DnaHmbsSearch';
}

export function metrics(slowdowns, chosenMs, bestMs) {
  const N = slowdowns.length;
  const geo = Math.exp(slowdowns.reduce((s, x) => s + Math.log(x), 0) / N);
  return {
    cases: N,
    fastestRate: slowdowns.filter((x) => x <= 1.0000001).length / N,
    within10Rate: slowdowns.filter((x) => x <= 1.1).length / N,
    geomeanSlowdown: geo,
    worstSlowdown: Math.max(...slowdowns),
    totalRatio: chosenMs.reduce((a, b) => a + b, 0) / bestMs.reduce((a, b) => a + b, 0),
  };
}

/** Her politika için ölçütler. Politika bir vakada "harcanan süreyi" (ms) verir. */
export function evaluate(results, filter = () => true) {
  const rows = results.filter(filter);
  const atomNames = registry.candidates().map((A) => A.manifest.name);
  const policies = {
    'ExactMatch (auto)': (c) => c.times[c.selected].ms,
    // Molekülün kendisi: kurulum + karar (şekil, tahminler) + seçilen atomun işi, aynı turlarda ölçüldü.
    [E2E]: (c) => c.moleculeMs,
    'Allmer 2016 kuralı': (c) => c.times[allmerRule(c.shape)].ms,
    ...Object.fromEntries(atomNames.map((n) => [`her zaman ${n}`, (c) => c.times[n].ms])),
  };
  const table = {};
  for (const [label, spent] of Object.entries(policies)) {
    const slow = [];
    const chosen = [];
    const best = [];
    for (const c of rows) {
      const ms = spent(c);
      slow.push(ms / c.bestMs);
      chosen.push(ms);
      best.push(c.bestMs);
    }
    table[label] = metrics(slow, chosen, best);
  }
  return table;
}
