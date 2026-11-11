// Knuth-Morris-Pratt atomu (Knuth, Morris & Pratt 1977).
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareKmp, searchKmp } from '../functions/kmp.js';
import { common } from './features.js';

export class KmpSearch extends ExactSearchAtom {
  static manifest = {
    name: 'KmpSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (Knuth-Morris-Pratt)', references: ['Knuth, Morris & Pratt 1977'],
  };
  static selection = {
    features(shape) {
      return { ...common(shape), scan: shape.k * shape.n, prep: shape.k * shape.mMean };
    },
    defaults: { base: 2e-9, out: 5e-8, scan: 3e-9, prep: 5e-9 },
  };

  prepare() {
    this.prep = this.unique.map((p) => prepareKmp(p));
  }

  scanText(text, n, hits) {
    for (let u = 0; u < this.prep.length; u++) searchKmp(this.prep[u], u, text, n, hits);
  }
}
