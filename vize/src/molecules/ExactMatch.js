// ExactMatch molekülü: aynı görevi yapan atomlar arasından girdiye göre seçim yapar.
//
// Kullanım:
//   const em = new ExactMatch({ patterns, ignoreCase, strategy: 'auto' });
//   for (const match of em.run(entries)) { ... }
//   em.record → { requested, selected, shape, estimates, why }
//
// "auto": ilk kaydın şekline bakılır, her aday atomun maliyeti tahmin edilir,
// en ucuzu seçilir ve bütün akış için o atom kullanılır.
// Bu dosyada hiçbir atom adı geçmez: atomlar kayıt defterinden (registry) gelir.

import { registry as defaultRegistry } from '../registry.js';
import { computeShape } from '../shape.js';
import { TASK, validateParams, validateEntry } from '../atomic/ExactSearchAtom.js';
import { estimateCost } from './costModel.js';
import calibrated from './coefficients.json' with { type: 'json' };

export class ExactMatch {
  static manifest = {
    name: 'ExactMatch', version: '0.1.0', kind: 'molecule', task: TASK,
    title: 'Exact match (auto-selecting molecule)', references: ['Allmer 2016'],
  };

  /**
   * @param {object} params { patterns, ignoreCase, strategy = 'auto' }
   * @param {object} [options] { registry, coefficients } — testlerde değiştirmek için
   */
  constructor(params, options = {}) {
    const { strategy = 'auto', ...rest } = params ?? {};
    const { patterns, ignoreCase } = validateParams(rest);
    this.registry = options.registry ?? defaultRegistry;
    this.coefficients = options.coefficients ?? calibrated;
    if (typeof strategy !== 'string' || (strategy !== 'auto' && !this.registry.has(strategy))) {
      throw new Error(
        `Bilinmeyen strateji "${strategy}". Geçerli seçenekler: auto, ${this.registry.names().join(', ')}`,
      );
    }
    this.params = { patterns, ignoreCase };
    this.strategy = strategy;
    this.atom = null;
    this.record = { requested: strategy, selected: null, shape: null, estimates: null, why: 'henüz karar verilmedi: hiç kayıt okunmadı' };
  }

  /** Kayıtları sırayla işler; ilk kayıtta karar verir. */
  *run(entries) {
    for (const entry of entries) {
      if (this.atom === null) this.decide(entry);
      yield* this.atom.process(entry);
    }
    if (this.atom === null) this.decide({ header: '', seq: '' }); // boş akışta da record dolu olsun
  }

  /** Verilen kayda bakarak atomu seçer, kurar ve record'u doldurur. */
  decide(entry) {
    validateEntry(entry);
    const shape = computeShape(entry, this.params);
    const estimates = {};
    const ranked = [];
    for (const Atom of this.registry.candidates()) {
      const name = Atom.manifest.name;
      const ok = Atom.selection.applicable ? Atom.selection.applicable(shape) : true;
      if (ok !== true) {
        estimates[name] = { applicable: false, reason: typeof ok === 'string' ? ok : 'uygulanamaz' };
        continue;
      }
      const est = estimateCost(Atom, shape, this.coefficients.atoms?.[name]);
      estimates[name] = { applicable: true, ms: round(est.seconds * 1e3), coefficients: est.coefficients, features: roundAll(est.features) };
      ranked.push({ name, seconds: est.seconds });
    }
    ranked.sort((a, b) => a.seconds - b.seconds);

    let selected;
    let why;
    if (this.strategy !== 'auto') {
      selected = this.strategy;
      why = `strateji adıyla istendi: ${selected}`;
      if (ranked.length && ranked[0].name !== selected) why += ` (model ${ranked[0].name} seçerdi)`;
    } else if (ranked.length === 0) {
      throw new Error('Bu girdi için uygulanabilir bir atom yok: ' + JSON.stringify(estimates));
    } else {
      selected = ranked[0].name;
      why = describe(ranked, estimates, shape);
    }
    const Atom = this.registry.get(selected);
    this.atom = new Atom(this.params);
    this.record = { requested: this.strategy, selected, shape, estimates, why };
    return this.record;
  }
}

function describe(ranked, estimates, shape) {
  const best = ranked[0];
  let s = `auto: n=${shape.n}, σ=${shape.sigma} (etkin ${shape.sigmaEff}), k=${shape.k}, m=${shape.mMin}..${shape.mMax}; `;
  s += `${best.name} en düşük tahmini süreye sahip (${fmt(best.seconds)})`;
  if (ranked.length > 1) {
    const second = ranked[1];
    const diff = (second.seconds / best.seconds - 1) * 100;
    const pct = diff < 10 ? diff.toFixed(1) : Math.round(diff);
    s += `; ikinci ${second.name} ${fmt(second.seconds)} (%${pct} daha yavaş)`;
  }
  const out = Object.entries(estimates).filter(([, e]) => !e.applicable);
  if (out.length) s += '; uygun değil: ' + out.map(([n, e]) => `${n} (${e.reason})`).join(', ');
  return s;
}

function fmt(seconds) {
  return seconds >= 1e-3 ? `${round(seconds * 1e3)} ms` : `${round(seconds * 1e6)} µs`;
}

function round(x) {
  if (x === 0 || !Number.isFinite(x)) return x;
  const d = Math.max(0, 3 - Math.floor(Math.log10(Math.abs(x))));
  return Number(x.toFixed(Math.min(d, 12)));
}

function roundAll(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj)) out[k] = round(v);
  return out;
}
