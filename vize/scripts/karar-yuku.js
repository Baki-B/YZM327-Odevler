// Tanı: molekülün karar süresini DOĞRUDAN ölçer (v3 ve v4 şekil hesabı yan yana) ve
// v4 örnekleminin σ / σe doğruluğunu tam sayımla karşılaştırır.
// Neden ayrı? Doğrulama betiğindeki "uçtan uca" ölçüm, molekülü ve atomları aynı turlarda
// ayrı ayrı ölçer; iki gürültülü sürenin farkı küçük karar süresini güvenilir veremez
// (D'de molekül, kendi seçtiği atomdan medyanda kısa ölçüldü). Burada karar adımı tek
// başına, çok kez tekrarlanarak ölçülür. Bu betik modeli değiştirmez ve D/E sonuçlarına
// dokunmaz; yalnızca D ve E vakalarının girdilerini yeniden üretir.
// Kullanım (vize/ klasöründen): node --expose-gc scripts/karar-yuku.js
// Çıktı: bench/results/karar-yuku-v4.json, bench/results/karar-yuku-v4.md

import { readFileSync } from 'node:fs';
import { makeText, makePatterns } from '../bench/data.js';
import { machineInfo, now, median } from '../bench/timing.js';
import { computeShape } from '../src/shape.js';
import { computeShape as computeShapeV3 } from '../bench/shape-v3.js';
import { ExactMatch } from '../src/molecules/ExactMatch.js';
import { registry } from '../src/registry.js';
import { saveJson, saveText, RESULTS, progress } from '../tests/benchmarks/common.js';

const SETS = [['D', 'validation-d'], ['E', 'validation-e']];

/** fn'in tek çağrı süresi (ms): ısınma + 9 bloğun medyanı; her blok ≥ 2 ms. */
function time(fn) {
  for (let i = 0; i < 3; i++) fn();
  const t0 = now();
  fn();
  const one = Math.max(now() - t0, 1e-4);
  const inner = Math.min(5000, Math.max(1, Math.ceil(2 / one)));
  const samples = [];
  for (let r = 0; r < 9; r++) {
    const s = now();
    for (let i = 0; i < inner; i++) fn();
    samples.push((now() - s) / inner);
  }
  return median(samples);
}

function exactSigma(seq) {
  const m = new Map();
  for (let i = 0; i < seq.length; i++) {
    const c = seq.charCodeAt(i);
    m.set(c, (m.get(c) ?? 0) + 1);
  }
  let sumSq = 0;
  for (const v of m.values()) sumSq += (v / seq.length) ** 2;
  return { sigma: m.size, sigmaEff: 1 / sumSq };
}

const q = (xs, p) => {
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor(s.length * p))];
};

const out = { description: 'Karar süresinin doğrudan ölçümü (ms) ve v4 örnekleminin doğruluğu', machine: machineInfo(), sets: {} };
for (const [label, file] of SETS) {
  const data = JSON.parse(readFileSync(new URL(`${file}.json`, RESULTS), 'utf8'));
  const rows = [];
  for (const c of data.cases) {
    progress(c.id + 1, data.cases.length, `${label} ${c.alphabet} n=${c.n} k=${c.k}`);
    const seq = makeText(c.alphabet, c.n, c.textSeed);
    const entry = { header: `>val_${c.id}`, seq };
    const patterns = makePatterns(seq, c.k, c.lengths, c.patternSeed);
    const params = { patterns, ignoreCase: false };
    const Selected = registry.get(c.selected);
    const shapeV3 = time(() => computeShapeV3(entry, params));
    const shapeV4 = time(() => computeShape(entry, params));
    const decide = time(() => new ExactMatch({ ...params, strategy: 'auto' }).decide(entry));
    const ctor = time(() => new Selected(params));
    const exact = exactSigma(seq);
    const s4 = computeShape(entry, params);
    rows.push({
      id: c.id, alphabet: c.alphabet, n: c.n, k: c.k, selected: c.selected, atomMs: c.times[c.selected].ms,
      shapeV3Ms: shapeV3, shapeV4Ms: shapeV4, decideMs: decide, ctorMs: ctor, decisionMs: Math.max(0, decide - ctor),
      sigmaExact: exact.sigma, sigmaV4: s4.sigma, sigmaEffExact: exact.sigmaEff, sigmaEffV4: s4.sigmaEff,
    });
  }
  out.sets[label] = rows;
}
process.stderr.write('\n');
saveJson('karar-yuku-v4.json', out);

const f3 = (x) => x.toFixed(3);
let md = `# Karar süresi (doğrudan ölçüm) ve örneklem doğruluğu, v4\n\n`;
md += `Makine: ${out.machine.cpu}, ${out.machine.cores} çekirdek, Node ${out.machine.node}, ${out.machine.date}.\n\n`;
md += `Her vakada D ve E kümesinin girdisi yeniden üretildi (aynı tohumlar). Süreler ms; her biri ısınma + 9 bloğun medyanı, blok ≥ 2 ms. `;
md += `"Karar" = molekülü kurup decide() çağırmak − seçilen atomu tek başına kurmak (atom kurulumu her durumda yapılır). `;
md += `Karar / atom oranının paydası, D ve E ölçümlerindeki seçilen atom süresidir (aynı makinede, ayrı çalıştırma).\n\n`;
md += `| Küme | Vaka | Şekil v3 (medyan) | Şekil v4 (medyan) | Şekil v3 en büyük | Şekil v4 en büyük | Karar v4 (medyan) | Karar / atom (medyan) | Karar / atom (%90) | Karar / atom (en büyük) |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n`;
for (const [label, rows] of Object.entries(out.sets)) {
  const ratio = rows.map((r) => r.decisionMs / r.atomMs);
  md += `| ${label} | ${rows.length} | ${f3(q(rows.map((r) => r.shapeV3Ms), 0.5))} | ${f3(q(rows.map((r) => r.shapeV4Ms), 0.5))} | ${f3(Math.max(...rows.map((r) => r.shapeV3Ms)))} | ${f3(Math.max(...rows.map((r) => r.shapeV4Ms)))} | ${f3(q(rows.map((r) => r.decisionMs), 0.5))} | ${f3(q(ratio, 0.5))} | ${f3(q(ratio, 0.9))} | ${f3(Math.max(...ratio))} |\n`;
}
md += `\n## v4 örnekleminin doğruluğu (tam sayıma göre)\n\n| Küme | Vaka | Örneklenen (n > 16 384) | σe göreli hata (medyan) | σe göreli hata (en büyük) | σ eksik sayılan vaka | σ en büyük eksik oran |\n|---|---:|---:|---:|---:|---:|---:|\n`;
for (const [label, rows] of Object.entries(out.sets)) {
  const sampled = rows.filter((r) => r.n > 16384);
  const err = sampled.map((r) => Math.abs(r.sigmaEffV4 / r.sigmaEffExact - 1));
  const miss = sampled.filter((r) => r.sigmaV4 < r.sigmaExact);
  const worstMiss = Math.max(0, ...sampled.map((r) => 1 - r.sigmaV4 / r.sigmaExact));
  md += `| ${label} | ${rows.length} | ${sampled.length} | ${(q(err, 0.5) * 100).toFixed(2)} % | ${(Math.max(...err) * 100).toFixed(2)} % | ${miss.length} | ${(worstMiss * 100).toFixed(1)} % |\n`;
}
saveText('karar-yuku-v4.md', md);
process.stdout.write(md);
