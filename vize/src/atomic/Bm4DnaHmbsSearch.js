// bm4DNAHMbs atomu (Allmer 2016; Wu & Manber 1994): q-gram özetleri üzerinden kayma; uzun desenler için.
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareBm4DnaHmbs, searchBm4DnaHmbs, createTable, chooseQ } from '../functions/bm4dnaHmbs.js';
import { qgramShift } from '../functions/expect.js';
import { common, patternSigma } from './features.js';

export class Bm4DnaHmbsSearch extends ExactSearchAtom {
  static manifest = {
    name: 'Bm4DnaHmbsSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (bm4DNAHMbs)', references: ['Allmer 2016', 'Wu & Manber 1994'],
  };
  static selection = {
    features(shape) {
      const q = chooseQ(patternSigma(shape) + 1, Math.round(shape.mMean));
      const windows = shape.k * shape.n / qgramShift(shape.mMean, q, shape.sigmaEff);
      return { ...common(shape), scan: windows * q, windows, prep: shape.k * shape.mMean };
    },
    defaults: { base: 2e-9, out: 5e-8, scan: 2e-9, windows: 3e-9, prep: 2e-8 },
  };

  prepare() {
    this.prep = this.unique.map((p) => prepareBm4DnaHmbs(p, this.sigma));
    this.table = createTable();
  }

  scanText(text, n, hits) {
    for (let u = 0; u < this.prep.length; u++) searchBm4DnaHmbs(this.prep[u], u, text, n, hits, this.table);
  }
}
