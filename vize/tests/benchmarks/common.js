// Kalibrasyon ve doğrulamada ortak parçalar.
import { writeFileSync, mkdirSync } from 'node:fs';
import { registry } from '../../src/registry.js';
import { computeShape } from '../../src/shape.js';
import { measure, measureInterleaved } from '../../bench/timing.js';
import { NaiveSearch } from '../../src/atomic/NaiveSearch.js';

export const RESULTS = new URL('../../bench/results/', import.meta.url);

export function saveJson(name, data) {
  mkdirSync(RESULTS, { recursive: true });
  writeFileSync(new URL(name, RESULTS), JSON.stringify(data, null, 1) + '\n');
}

export function saveText(name, text) {
  mkdirSync(RESULTS, { recursive: true });
  writeFileSync(new URL(name, RESULTS), text);
}

/** Bir atomun ön işleme + arama + çıktı üretme süresini ölçer; eşleşme sayısını da döndürür. */
export function timeAtom(Atom, params, entries, opts) {
  let hits = 0;
  const run = () => {
    const atom = new Atom(params);
    let c = 0;
    for (const e of entries) for (const _ of atom.process(e)) c++;
    hits = c;
  };
  const t = measure(run, opts);
  return { ms: t.ms, samples: t.samples, inner: t.inner, hits };
}

/** Bir atomu ölçülebilir bir işe çevirir: kur + bütün kayıtları işle + çıktıyı tüket. */
export function atomJob(Atom, params, entries) {
  const job = () => {
    const atom = new Atom(params);
    let c = 0;
    for (const e of entries) for (const _ of atom.process(e)) c++;
    job.hits = c;
  };
  return job;
}

/**
 * Bir vakada bütün aday atomları dönüşümlü ölçer (her turda her atom bir kez);
 * sonuç sayılarının oracle ile aynı olduğunu da denetler.
 * extraJobs: aynı turlara katılacak ek işler (ör. molekülün kendisi).
 */
export function measureCase(params, entries, opts = {}, extraJobs = {}) {
  const shape = computeShape(entries[0], params);
  let expected = 0;
  {
    const ref = new NaiveSearch(params);
    for (const e of entries) for (const _ of ref.process(e)) expected++;
  }
  const jobs = {};
  for (const Atom of registry.candidates()) jobs[Atom.manifest.name] = atomJob(Atom, params, entries);
  Object.assign(jobs, extraJobs);
  const measured = measureInterleaved(jobs, opts);
  const times = {};
  for (const Atom of registry.candidates()) {
    const name = Atom.manifest.name;
    if (jobs[name].hits !== expected) throw new Error(`${name}: ${jobs[name].hits} eşleşme, beklenen ${expected}`);
    const ok = Atom.selection.applicable ? Atom.selection.applicable(shape) : true;
    times[name] = { ...measured[name], applicable: ok === true };
  }
  const extra = {};
  for (const name of Object.keys(extraJobs)) extra[name] = measured[name];
  return { shape, hits: expected, times, extra };
}

export function fastest(times, applicableOnly = false) {
  let best = null;
  for (const [name, t] of Object.entries(times)) {
    if (applicableOnly && !t.applicable) continue;
    if (best === null || t.ms < times[best].ms) best = name;
  }
  return best;
}

export function progress(i, total, label) {
  process.stderr.write(`\r[${String(i).padStart(3)}/${total}] ${label.padEnd(60).slice(0, 60)}`);
}
