// Shift-Or atomu: bit paralel arama (Baeza-Yates & Gonnet 1992).
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareShiftOr, searchShiftOr, WORD } from '../functions/shiftOr.js';
import { common, tablePrep } from './features.js';

export class ShiftOrSearch extends ExactSearchAtom {
  static manifest = {
    name: 'ShiftOrSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (Shift-Or, bit parallel)', references: ['Baeza-Yates & Gonnet 1992'],
  };
  static selection = {
    features(shape) {
      return { ...common(shape), scan: shape.k * shape.n, prep: tablePrep(shape) };
    },
    defaults: { fixed: 2e-6, perPattern: 1e-7, base: 2e-9, out: 5e-8, scan: 1.5e-9, prep: 5e-9 },
    applicable(shape) {
      return shape.mMax <= WORD
        ? true
        : `en uzun desen ${shape.mMax} karakter; bit paralel yöntem ${WORD} karakterle sınırlı`;
    },
  };

  prepare() {
    this.prep = this.unique.map((p) => prepareShiftOr(p, this.sigma));
  }

  scanText(text, n, hits) {
    for (let u = 0; u < this.prep.length; u++) searchShiftOr(this.prep[u], u, text, n, hits);
  }
}
