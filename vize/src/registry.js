// Kayıt defteri (registry): molekülün tanıdığı atomların listesi.
//
// Açık/Kapalı ilkesi: Yeni bir atom eklemek için ExactMatch'e dokunulmaz.
// Atom dosyası yazılır ve ya aşağıdaki BUILTIN listesine eklenir ya da çalışma
// anında registry.register(YeniAtom) çağrılır. Molekül atomları adlarıyla
// yalnızca buradan tanır.

import { TASK } from './atomic/ExactSearchAtom.js';
import { NaiveSearch } from './atomic/NaiveSearch.js';
import { BoyerMooreSearch } from './atomic/BoyerMooreSearch.js';
import { HorspoolSearch } from './atomic/HorspoolSearch.js';
import { ShiftOrSearch } from './atomic/ShiftOrSearch.js';
import { KmpSearch } from './atomic/KmpSearch.js';
import { AhoCorasickSearch } from './atomic/AhoCorasickSearch.js';
import { WuManberSearch } from './atomic/WuManberSearch.js';
import { Bm4DnaDsSearch } from './atomic/Bm4DnaDsSearch.js';
import { Bm4DnaHmbsSearch } from './atomic/Bm4DnaHmbsSearch.js';

export const BUILTIN = [
  NaiveSearch, BoyerMooreSearch, HorspoolSearch, ShiftOrSearch, KmpSearch,
  AhoCorasickSearch, WuManberSearch, Bm4DnaDsSearch, Bm4DnaHmbsSearch,
];

export class Registry {
  #atoms = new Map();

  /** Bir atom sınıfını ekler. Sözleşmeye uymayan sınıf reddedilir. */
  register(Atom) {
    const m = Atom?.manifest;
    if (!m || typeof m.name !== 'string' || m.name === '') throw new TypeError('Atomun manifest.name alanı olmalı');
    if (m.kind !== 'atom') throw new TypeError(`${m.name}: manifest.kind "atom" olmalı`);
    if (m.task !== TASK) throw new TypeError(`${m.name}: manifest.task "${TASK}" olmalı`);
    if (typeof Atom.prototype?.process !== 'function') throw new TypeError(`${m.name}: process() yöntemi yok`);
    const s = Atom.selection;
    if (s !== null && s !== undefined) {
      if (typeof s.features !== 'function') throw new TypeError(`${m.name}: selection.features bir işlev olmalı`);
      if (!s.defaults || typeof s.defaults !== 'object') throw new TypeError(`${m.name}: selection.defaults bir nesne olmalı`);
    }
    if (this.#atoms.has(m.name)) throw new Error(`${m.name} zaten kayıtlı`);
    this.#atoms.set(m.name, Atom);
    return this;
  }

  unregister(name) {
    return this.#atoms.delete(name);
  }

  has(name) {
    return this.#atoms.has(name);
  }

  get(name) {
    return this.#atoms.get(name);
  }

  /** Kayıtlı bütün atom adları, kayıt sırasıyla. */
  names() {
    return [...this.#atoms.keys()];
  }

  /** "auto" kipinde aday olan atomlar: selection alanı olanlar. */
  candidates() {
    return [...this.#atoms.values()].filter((A) => A.selection);
  }

  /** Aynı atomlarla yeni bir kayıt defteri (testlerde güvenle değiştirmek için). */
  clone() {
    const r = new Registry();
    for (const A of this.#atoms.values()) r.register(A);
    return r;
  }
}

export function createDefaultRegistry() {
  const r = new Registry();
  for (const A of BUILTIN) r.register(A);
  return r;
}

/** Varsayılan, paylaşılan kayıt defteri. */
export const registry = createDefaultRegistry();
