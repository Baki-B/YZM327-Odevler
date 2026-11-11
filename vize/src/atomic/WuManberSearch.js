// Wu-Manber atomu: çok desen, blok kayması (Wu & Manber 1994).
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareWuManber, searchWuManber, chooseBlock } from '../functions/wuManber.js';
import { horspoolShift } from '../functions/expect.js';
import { common, patternSigma } from './features.js';

export class WuManberSearch extends ExactSearchAtom {
  static manifest = {
    name: 'WuManberSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (Wu-Manber)', references: ['Wu & Manber 1994'],
  };
  static selection = {
    features(shape) {
      const B = chooseBlock(patternSigma(shape), shape.k, shape.mMin);
      const blocks = Math.pow(Math.max(shape.sigmaEff, 1), B);
      // k desenin blokları tabloyu doldurdukça kayma kısalır: blok alfabesi blocks/k gibi davranır.
      const shift = horspoolShift(shape.mMin - B + 1, Math.max(1, blocks / shape.k));
      const windows = shape.n / shift;
      const candidates = windows * Math.min(1, shape.k / blocks) * (1 + shape.k / blocks);
      return { ...common(shape), scan: windows * B, verify: candidates, prep: shape.k * shape.mMin };
    },
    defaults: { base: 2e-9, out: 5e-8, scan: 4e-9, verify: 1e-8, prep: 5e-9 },
  };

  prepare() {
    const B = chooseBlock(this.sigma - 1, this.unique.length, this.minLen);
    this.prep = prepareWuManber(this.unique, this.sigma, B);
  }

  scanText(text, n, hits) {
    searchWuManber(this.prep, text, n, hits);
  }
}
