// Aho-Corasick atomu: çok desen, tek geçiş (Aho & Corasick 1975).
import { ExactSearchAtom, TASK } from './ExactSearchAtom.js';
import { prepareAhoCorasick, searchAhoCorasick } from '../functions/ahoCorasick.js';
import { common, patternSigma } from './features.js';

const MAX_CELLS = 3e7; // otomat tablosu bundan büyükse bellek (≈120 MB) sorunu

export class AhoCorasickSearch extends ExactSearchAtom {
  static manifest = {
    name: 'AhoCorasickSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (Aho-Corasick)', references: ['Aho & Corasick 1975'],
  };
  static selection = {
    features(shape) {
      const cells = (shape.k * shape.mMean + 1) * (patternSigma(shape) + 1);
      // Tablo işlemci önbelleğine sığmadığında her adım pahalılaşır: "big" bunu yakalar.
      const big = shape.n * Math.max(0, Math.log2(cells / 4096));
      return { ...common(shape), scan: shape.n, big, prep: cells };
    },
    defaults: { base: 2e-9, out: 5e-8, scan: 3e-9, big: 3e-10, prep: 3e-9 },
    applicable(shape) {
      const cells = (shape.k * shape.mMean + 1) * (patternSigma(shape) + 1);
      return cells <= MAX_CELLS ? true : `otomat tablosu çok büyük (${Math.round(cells)} hücre)`;
    },
  };

  prepare() {
    this.prep = prepareAhoCorasick(this.unique, this.sigma);
  }

  scanText(text, n, hits) {
    searchAhoCorasick(this.prep, text, n, hits);
  }
}
