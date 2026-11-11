// Horspool atomu: yalnızca kötü karakter kayması (Horspool 1980).
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareHorspool, searchHorspool } from '../functions/horspool.js';
import { horspoolShift } from '../functions/expect.js';
import { common, tablePrep } from './features.js';

export class HorspoolSearch extends ExactSearchAtom {
  static manifest = {
    name: 'HorspoolSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (Horspool)', references: ['Horspool 1980'],
  };
  static selection = {
    features(shape) {
      const steps = shape.k * shape.n / horspoolShift(shape.mMean, shape.sigmaEff);
      return { ...common(shape), scan: steps, verify: steps / Math.max(shape.sigmaEff, 1), prep: tablePrep(shape) };
    },
    defaults: { fixed: 2e-6, perPattern: 1e-7, base: 2e-9, out: 5e-8, scan: 4e-9, verify: 4e-9, prep: 5e-9 },
  };

  prepare() {
    this.prep = this.unique.map((p) => prepareHorspool(p, this.sigma));
  }

  scanText(text, n, hits) {
    for (let u = 0; u < this.prep.length; u++) searchHorspool(this.prep[u], u, text, n, hits);
  }
}
