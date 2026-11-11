// bm4DNADS atomu (Allmer 2016): sentinel + üç kez açılmış atlama döngüsü; kısa desenler için.
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareBm4DnaDs, searchBm4DnaDs } from '../functions/bm4dnaDs.js';
import { horspoolShift } from '../functions/expect.js';
import { common, tablePrep } from './features.js';

export class Bm4DnaDsSearch extends ExactSearchAtom {
  static manifest = {
    name: 'Bm4DnaDsSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (bm4DNADS)', references: ['Allmer 2016', 'Hume & Sunday 1991'],
  };
  static selection = {
    features(shape) {
      const steps = shape.k * shape.n / horspoolShift(shape.mMean, shape.sigmaEff);
      return { ...common(shape), scan: steps, verify: steps / Math.max(shape.sigmaEff, 1), prep: tablePrep(shape) };
    },
    defaults: { base: 2e-9, out: 5e-8, scan: 3e-9, verify: 4e-9, prep: 5e-9 },
  };

  prepare() {
    this.prep = this.unique.map((p) => prepareBm4DnaDs(p, this.sigma));
  }

  padding() {
    return this.maxLen; // sentinel için yer
  }

  scanText(text, n, hits) {
    for (let u = 0; u < this.prep.length; u++) searchBm4DnaDs(this.prep[u], u, text, n, hits);
  }
}
