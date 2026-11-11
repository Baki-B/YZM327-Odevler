// Kalibrasyon (Görev 4.1): ölçüm ızgarası + katsayı uydurma.
//   3 alfabe (DNA, protein, kaynak kod) × 3 metin uzunluğu (10^4, 10^5, 10^6)
//   × 5 desen uzunluğu (4, 8, 16, 32, 64) × 4 desen sayısı (1, 4, 16, 64) = 180 vaka.
// Her vakada bütün aday atomlar dönüşümlü ölçülür (ısınma + 5 tekrarın medyanı;
// tek ölçüm 10 ms'den kısaysa blok içinde tekrar edilip ortalaması alınır).
// Çıktılar:
//   bench/results/calibration.json   ham ölçümler + makine bilgisi
//   src/molecules/coefficients.json  her atomun katsayıları (NNLS, göreli hata)
//   bench/results/calibration-fit.md uydurma kalitesi
// Kullanım: npm run calibrate   (ya da: node --expose-gc tests/benchmarks/calibrate.js --quick)

import { writeFileSync, readFileSync } from 'node:fs';
import { computeShape } from '../../src/shape.js';
import { registry } from '../../src/registry.js';
import { makeText, makePatterns } from '../../bench/data.js';
import { machineInfo, now } from '../../bench/timing.js';
import { fitNonNegative } from '../../src/molecules/costModel.js';
import { measureCase, saveJson, saveText, progress } from './common.js';

const QUICK = process.argv.includes('--quick');
// --refit: ölçümleri yeniden yapmadan, kayıtlı calibration.json üzerinden katsayıları yeniden uydurur
// (atomlar değişmeden yalnızca özellik tanımları değiştiğinde kullanılır).
const REFIT = process.argv.includes('--refit');
const ALPHABETS = ['dna', 'protein', 'code'];
const NS = QUICK ? [1e4, 1e5] : [1e4, 1e5, 1e6];
const MS = [4, 8, 16, 32, 64];
const KS = [1, 4, 16, 64];
const REPS = 5;

const seedOf = (...xs) => xs.reduce((h, x) => (Math.imul(h ^ Math.round(x), 0x9e3779b1) >>> 0), 17);

function runGrid() {
  const cases = [];
  const total = ALPHABETS.length * NS.length * MS.length * KS.length;
  let i = 0;
  const t0 = now();
  for (const alphabet of ALPHABETS) {
    for (const n of NS) {
      const seq = makeText(alphabet, n, seedOf(1, ALPHABETS.indexOf(alphabet), n));
      const entries = [{ header: `>${alphabet}_${n}`, seq }];
      for (const m of MS) {
        for (const k of KS) {
          const seed = seedOf(2, ALPHABETS.indexOf(alphabet), n, m, k);
          const patterns = makePatterns(seq, k, [m], seed);
          progress(++i, total, `${alphabet} n=${n} m=${m} k=${k}`);
          const r = measureCase({ patterns, ignoreCase: false }, entries, { reps: REPS });
          cases.push({ alphabet, n, m, k, seed, ...r });
        }
      }
    }
  }
  process.stderr.write(`\nızgara bitti: ${((now() - t0) / 1000).toFixed(1)} s\n`);
  return cases;
}

/**
 * Katsayı uydurma, iki adımda:
 *  1. Her atom ayrı uydurulur; "out" (eşleşme sayısı) ölçülen gerçek sayıyla beslenir.
 *  2. Eşleşme başına iş (toplayıcıya ekleme + çıktı nesnesi üretme) koddaki aynı
 *     parçalarla yapıldığı için bütün atomlarda ortaktır. Adım 1'deki out katsayılarının
 *     medyanı ortak değer olarak sabitlenir, diğer katsayılar bu sabitle yeniden uydurulur.
 *     (Atom başına serbest out katsayısı 45 kat değişiyordu; eşleşmenin çok olduğu girdide
 *     yanlış atomu ucuz gösteriyordu. Bkz. rapor bölüm 6.)
 */
function fit(cases) {
  const prepared = {};
  const free = {};
  for (const Atom of registry.candidates()) {
    const name = Atom.manifest.name;
    const sel = Atom.selection;
    const used = cases.filter((c) => c.times[name]?.applicable);
    const keys = Object.keys(sel.features(used[0].shape));
    const feats = used.map((c) => {
      const f = { ...sel.features(c.shape) };
      if ('out' in f) f.out = c.hits;
      return f;
    });
    const targets = used.map((c) => c.times[name].ms / 1e3);
    prepared[name] = { keys, feats, targets };
    const coef = fitNonNegative(feats.map((f) => keys.map((k) => f[k])), targets);
    free[name] = Object.fromEntries(keys.map((k, j) => [k, coef[j]]));
  }
  const outs = Object.values(free).map((c) => c.out).filter((x) => x !== undefined).sort((a, b) => a - b);
  const sharedOut = outs.length % 2 ? outs[outs.length >> 1] : (outs[outs.length / 2 - 1] + outs[outs.length / 2]) / 2;

  const atoms = {};
  const quality = {};
  for (const [name, { keys, feats, targets }] of Object.entries(prepared)) {
    const rest = keys.filter((k) => k !== 'out');
    const offsets = feats.map((f) => ('out' in f ? sharedOut * f.out : 0));
    const coef = fitNonNegative(feats.map((f) => rest.map((k) => f[k])), targets, offsets);
    atoms[name] = Object.fromEntries(rest.map((k, j) => [k, coef[j]]));
    if (keys.includes('out')) atoms[name].out = sharedOut;
    const rel = feats
      .map((f, i) => Math.abs(keys.reduce((s, k) => s + f[k] * atoms[name][k], 0) / targets[i] - 1))
      .sort((a, b) => a - b);
    quality[name] = { cases: feats.length, medianRelError: rel[rel.length >> 1], p90RelError: rel[Math.floor(rel.length * 0.9)] };
  }
  return { atoms, quality, sharedOut, freeOuts: Object.fromEntries(Object.entries(free).map(([n, c]) => [n, c.out])) };
}

/** Kalibrasyon kümesinde (görülmüş veri) seçimin kalitesi: yalnızca tanı amaçlı. */
function inSample(cases, atoms) {
  let logSum = 0, best = 0, worst = 1;
  for (const c of cases) {
    let pick = null, pickCost = Infinity;
    for (const Atom of registry.candidates()) {
      const name = Atom.manifest.name;
      if (!c.times[name]?.applicable) continue;
      const f = Atom.selection.features(c.shape);
      const cost = Object.entries(f).reduce((s, [k, x]) => s + x * (atoms[name][k] ?? 0), 0);
      if (cost < pickCost) { pickCost = cost; pick = name; }
    }
    const fastestMs = Math.min(...Object.values(c.times).map((t) => t.ms));
    const slow = c.times[pick].ms / fastestMs;
    logSum += Math.log(slow);
    if (slow <= 1.0000001) best++;
    worst = Math.max(worst, slow);
  }
  return { cases: cases.length, bestRate: best / cases.length, geomeanSlowdown: Math.exp(logSum / cases.length), worstSlowdown: worst };
}

let machine;
let cases;
if (REFIT) {
  const old = JSON.parse(readFileSync(new URL('../../bench/results/calibration.json', import.meta.url), 'utf8'));
  machine = old.machine;
  // Şekil, güncel shape.js ile yeniden hesaplanır (metin aynı tohumdan yeniden üretilir).
  const texts = new Map();
  cases = old.cases.map((c) => {
    const key = `${c.alphabet}:${c.n}`;
    if (!texts.has(key)) texts.set(key, makeText(c.alphabet, c.n, seedOf(1, ALPHABETS.indexOf(c.alphabet), c.n)));
    const patterns = makePatterns(texts.get(key), c.k, [c.m], c.seed);
    return { ...c, shape: computeShape({ header: '', seq: texts.get(key) }, { patterns }) };
  });
  process.stderr.write(`kayıtlı ${cases.length} ölçümden yeniden uyduruluyor\n`);
} else {
  machine = machineInfo();
  cases = runGrid();
  saveJson(QUICK ? 'calibration-quick.json' : 'calibration.json', {
    description: 'Kalibrasyon ızgarası: ham ölçümler (ms, ısınma + medyan)', machine, reps: REPS,
    grid: { alphabets: ALPHABETS, n: NS, m: MS, k: KS }, cases,
  });
}
const { atoms, quality, sharedOut, freeOuts } = fit(cases);
if (!QUICK) {
  writeFileSync(new URL('../../src/molecules/coefficients.json', import.meta.url), JSON.stringify({
    source: 'bench/results/calibration.json', method: 'NNLS, göreli hata', machine: { cpu: machine.cpu, node: machine.node, date: machine.date },
    sharedOut, atoms,
  }, null, 1) + '\n');
}
let md = `# Kalibrasyon uydurma kalitesi\n\nMakine: ${machine.cpu}, ${machine.cores} çekirdek, Node ${machine.node}, ${machine.date}\n\n`;
md += '| Atom | Vaka | Medyan göreli hata | %90 göreli hata | Katsayılar |\n|---|---:|---:|---:|---|\n';
for (const [name, q] of Object.entries(quality)) {
  const c = Object.entries(atoms[name]).map(([k, v]) => `${k}=${v.toExponential(2)}`).join(', ');
  md += `| ${name} | ${q.cases} | ${(q.medianRelError * 100).toFixed(1)} % | ${(q.p90RelError * 100).toFixed(1)} % | ${c} |\n`;
}
md += `\nOrtak eşleşme başına maliyet (out): ${sharedOut.toExponential(2)} s. Atom başına serbest uydurmada bulunan değerler: ` +
  Object.entries(freeOuts).map(([n, v]) => `${n.replace('Search', '')} ${v.toExponential(1)}`).join(', ') + '.\n';
const ins = inSample(cases, atoms);
md += `\nKalibrasyon kümesinin kendisinde seçim (görülmüş veri, yalnızca tanı): en hızlıyı seçme %${(ins.bestRate * 100).toFixed(1)}, ` +
  `yavaşlama geometrik ortalaması ${ins.geomeanSlowdown.toFixed(3)}, en kötü ${ins.worstSlowdown.toFixed(2)}×\n`;
saveText(QUICK ? 'calibration-fit-quick.md' : 'calibration-fit.md', md);
process.stdout.write(md);
