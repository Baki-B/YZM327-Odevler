// Tam bir örnek atom: Boyer-Moore (başlangıç paketindeki örnek atomun karşılığı).
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareBoyerMoore, searchBoyerMoore } from '../functions/boyerMoore.js';
import { horspoolShift } from '../functions/expect.js';
import { common, tablePrep, overLengths } from './features.js';

export class BoyerMooreSearch extends ExactSearchAtom {
  static manifest = {
    name: 'BoyerMooreSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (Boyer-Moore)', references: ['Boyer & Moore 1977'],
  };
  static selection = {
    features(shape) {
      const steps = overLengths(shape, (m) => shape.n / horspoolShift(m, shape.sigmaEff));
      return { ...common(shape), scan: steps, prep: tablePrep(shape) + shape.k * shape.mMean };
    },
    defaults: { fixed: 2e-6, perPattern: 1e-7, base: 2e-9, out: 5e-8, scan: 6e-9, prep: 5e-9 },
  };

  prepare() {
    this.prep = this.unique.map((p) => prepareBoyerMoore(p, this.sigma));
  }

  scanText(text, n, hits) {
    for (let u = 0; u < this.prep.length; u++) searchBoyerMoore(this.prep[u], u, text, n, hits);
  }
}
