// Doğrulama (Görev 4.2–4.4): kalibrasyonda kullanılmamış 120 vaka.
//   - farklı tohumlar (kalibrasyon tohumlarıyla çakışmaz),
//   - değerler ızgara noktalarının ARASINDAN (n, m, k hiçbir zaman 10^4/10^5/10^6, 4/8/16/32/64, 1/4/16/64 değil),
//   - kalibrasyonda olmayan alfabeler: log, ikili (ab), İngilizce benzeri metin,
//   - vakaların bir kısmında karışık desen uzunlukları.
// Karşılaştırılan politikalar: molekül (auto), "her zaman X" (her atom için), Allmer 2016 kuralı.
// Çıktılar: bench/results/validation.json (ham), bench/results/validation.md (tablolar).
// Kullanım: npm run bench   (ya da --quick ile 24 vakalık kısa deneme)
//   --seed <tohum> --name <dosya adı>   başka bir küme (taze küme B: --seed 31415926 --name validation-taze)
//   --k 1                               tek desenli ek küme (C: --seed 27182818 --name validation-tek --k 1)

import { registry } from '../../src/registry.js';
import { ExactMatch } from '../../src/molecules/ExactMatch.js';
import { makeText, makePatterns, rng } from '../../bench/data.js';
import { machineInfo, now } from '../../bench/timing.js';
import { measureCase, saveJson, saveText, progress } from './common.js';

const QUICK = process.argv.includes('--quick');
const CASES = QUICK ? 24 : 120;
const argValue = (flag, dflt) => {
  const i = process.argv.indexOf(flag);
  return i >= 0 ? process.argv[i + 1] : dflt;
};
// --seed: doğrulama kümesinin tohumu; --name: sonuç dosyalarının adı (bench/results/<name>.json/.md)
const SEED = Number(argValue('--seed', 20261111));
const NAME = argValue('--name', QUICK ? 'validation-quick' : 'validation');
// --k: desen sayısını sabitler (ör. --k 1: tek desenli ek küme). Verilmezse k, 2–120 arasından çekilir.
const FIXED_K = argValue('--k', null) === null ? null : Number(argValue('--k', null));
if (FIXED_K !== null && !(Number.isInteger(FIXED_K) && FIXED_K >= 1)) throw new Error('--k pozitif bir tamsayı olmalı');
const ALPHABETS = ['dna', 'protein', 'code', 'log', 'binary', 'text'];
const UNSEEN = new Set(['log', 'binary', 'text']);
const GRID_N = [1e4, 1e5, 1e6];
const GRID_M = new Set([4, 8, 16, 32, 64]);
const GRID_K = new Set([1, 4, 16, 64]);

/** log-tekdüze tamsayı, yasaklı değerlerden kaçınarak. */
function logUniformInt(r, lo, hi, banned) {
  for (;;) {
    const x = Math.round(Math.exp(Math.log(lo) + r() * (Math.log(hi) - Math.log(lo))));
    if (!banned(x)) return x;
  }
}

function makeCases() {
  const r = rng(SEED);
  const out = [];
  for (let i = 0; i < CASES; i++) {
    const alphabet = ALPHABETS[i % ALPHABETS.length];
    const n = logUniformInt(r, 12000, 900000, (x) => GRID_N.some((g) => Math.abs(x / g - 1) < 0.1));
    const kDrawn = logUniformInt(r, 2, 120, (x) => GRID_K.has(x)); // --k verilse de çekilir: rastgele sıra değişmesin
    const k = FIXED_K ?? kDrawn;
    const m = logUniformInt(r, 3, 100, (x) => GRID_M.has(x));
    const mixed = r() < 0.3;
    const lengths = mixed && k > 1
      ? [m, Math.max(3, Math.round(m / 2.5)), Math.min(150, Math.round(m * 2.3))].map((x) => (GRID_M.has(x) ? x + 1 : x))
      : [m];
    // Varsayılan küme (A) ilk sürümdeki tohumlarla birebir aynı kalır; başka tohumda veri tohumları da kayar.
    const base = SEED === 20261111 ? 0 : (SEED % 100000) + 1;
    out.push({ id: i, alphabet, unseenAlphabet: UNSEEN.has(alphabet), n, k, lengths, textSeed: 900000 + base * 1000 + i * 7, patternSeed: 500000 + base * 1000 + i * 13 });
  }
  return out;
}

function allmerRule(shape) {
  return shape.mMean < 50 ? 'Bm4DnaDsSearch' : 'Bm4DnaHmbsSearch';
}

function metrics(slowdowns, chosenMs, bestMs) {
  const N = slowdowns.length;
  const geo = Math.exp(slowdowns.reduce((s, x) => s + Math.log(x), 0) / N);
  return {
    cases: N,
    fastestRate: slowdowns.filter((x) => x <= 1.0000001).length / N,
    within10Rate: slowdowns.filter((x) => x <= 1.1).length / N,
    geomeanSlowdown: geo,
    worstSlowdown: Math.max(...slowdowns),
    totalRatio: chosenMs.reduce((a, b) => a + b, 0) / bestMs.reduce((a, b) => a + b, 0),
  };
}

function evaluate(results, filter = () => true) {
  const rows = results.filter(filter);
  const atomNames = registry.candidates().map((A) => A.manifest.name);
  const policies = {
    'ExactMatch (auto)': (c) => c.selected,
    'Allmer 2016 kuralı': (c) => allmerRule(c.shape),
    ...Object.fromEntries(atomNames.map((n) => [`her zaman ${n}`, () => n])),
  };
  const table = {};
  for (const [label, pick] of Object.entries(policies)) {
    const slow = [];
    const chosen = [];
    const best = [];
    for (const c of rows) {
      const name = pick(c);
      slow.push(c.times[name].ms / c.bestMs);
      chosen.push(c.times[name].ms);
      best.push(c.bestMs);
    }
    table[label] = metrics(slow, chosen, best);
  }
  return table;
}

const pct = (x) => `${(x * 100).toFixed(1)} %`;
const fx = (x) => x.toFixed(3);

function markdownTable(table) {
  let md = '| Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü yavaşlama | Toplam süre / en iyi |\n';
  md += '|---|---:|---:|---:|---:|---:|---:|\n';
  for (const [label, m] of Object.entries(table)) {
    md += `| ${label} | ${m.cases} | ${pct(m.fastestRate)} | ${pct(m.within10Rate)} | ${fx(m.geomeanSlowdown)} | ${m.worstSlowdown.toFixed(2)}× | ${fx(m.totalRatio)} |\n`;
  }
  return md;
}

// ------------------------------------------------------------------ çalıştır
const machine = machineInfo();
const cases = makeCases();
const results = [];
const t0 = now();
for (const c of cases) {
  progress(c.id + 1, cases.length, `${c.alphabet} n=${c.n} k=${c.k} m=${c.lengths.join('/')}`);
  const seq = makeText(c.alphabet, c.n, c.textSeed);
  const entries = [{ header: `>val_${c.id}`, seq }];
  const patterns = makePatterns(seq, c.k, c.lengths, c.patternSeed);
  const params = { patterns, ignoreCase: false };
  // Molekülün kararı (ölçümden bağımsız, bir kez)
  const em = new ExactMatch({ ...params, strategy: 'auto' });
  em.decide(entries[0]);
  const record = em.record;
  // Molekülün kendisi de aynı turlarda ölçülür (karar verme süresi dahil)
  const moleculeJob = () => {
    const m = new ExactMatch({ ...params, strategy: 'auto' });
    let x = 0;
    for (const _ of m.run(entries)) x++;
    moleculeJob.hits = x;
  };
  const r = measureCase(params, entries, { reps: 5 }, { ExactMatch: moleculeJob });
  const bestName = Object.entries(r.times).reduce((a, b) => (b[1].ms < a[1].ms ? b : a))[0];
  results.push({
    ...c, mMin: r.shape.mMin, mMax: r.shape.mMax, shape: r.shape, hits: r.hits, times: r.times,
    selected: record.selected, estimates: record.estimates, why: record.why,
    moleculeMs: r.extra.ExactMatch.ms, best: bestName, bestMs: r.times[bestName].ms,
  });
}
process.stderr.write(`\ndoğrulama bitti: ${((now() - t0) / 1000).toFixed(1)} s\n`);

const all = evaluate(results);
const big = evaluate(results, (c) => c.bestMs >= 1);
const unseen = evaluate(results, (c) => c.unseenAlphabet);
const seen = evaluate(results, (c) => !c.unseenAlphabet);
const overhead = results.map((c) => c.moleculeMs / c.times[c.selected].ms).sort((a, b) => a - b);
const worst = [...results].sort((a, b) => b.times[b.selected].ms / b.bestMs - a.times[a.selected].ms / a.bestMs).slice(0, 5);

saveJson(`${NAME}.json`, {
  description: 'Doğrulama kümesi: kalibrasyonda görülmemiş vakalar; süreler ms (ısınma + 5 tekrarın medyanı)',
  machine, seed: SEED, fixedK: FIXED_K, metrics: { all, bestAtLeast1ms: big, seenAlphabets: seen, unseenAlphabets: unseen },
  moleculeOverhead: { median: overhead[overhead.length >> 1], p90: overhead[Math.floor(overhead.length * 0.9)] },
  cases: results,
});

let md = `# Doğrulama sonuçları\n\n`;
md += `Makine: ${machine.cpu}, ${machine.cores} çekirdek, ${machine.memoryGB} GB, Node ${machine.node}, ${machine.platform}, ${machine.date}. `;
md += `Çöp toplayıcı ölçümlerden önce çağrıldı: ${machine.gcExposed ? 'evet' : 'hayır'}.\n\n`;
md += `${results.length} vaka (tohum ${SEED}); her vakada her atom dönüşümlü ölçüldü: ısınma + 5 tekrarın medyanı; tek ölçüm 10 ms'den kısaysa blok içinde tekrarlanıp ortalaması alındı. `;
md += `"Yavaşlama" = politikanın seçtiği atomun süresi / o vakadaki en hızlı atomun süresi.\n\n`;
if (FIXED_K !== null) {
  md += `**Bu kümede desen sayısı k = ${FIXED_K} olarak sabitlendi.** `;
  if (GRID_K.has(FIXED_K)) md += `k = ${FIXED_K} kalibrasyon ızgarasının da bir değeridir; bu yüzden küme k bakımından "ızgara arası" değildir. `;
  md += `n ve m ızgara noktalarının arasından seçildi; metin ve desen tohumları kalibrasyondakilerden farklıdır.\n\n`;
}
md += `## Bütün vakalar\n\n${markdownTable(all)}\n`;
md += `## Yalnızca en hızlı atomun 1 ms ve üstü sürdüğü vakalar\n\nÇok kısa sürelerde ölçüm gürültüsü farkları büyütür; bu alt küme daha güvenilirdir.\n\n${markdownTable(big)}\n`;
md += `## Kalibrasyonda görülen / görülmeyen alfabeler (molekül ve Allmer kuralı)\n\n`;
md += '| Alt küme | Politika | Vaka | En hızlıyı seçme | %10 içinde | Yavaşlama (geo. ort.) | En kötü |\n|---|---|---:|---:|---:|---:|---:|\n';
for (const [label, t] of [['görülen (DNA, protein, kod)', seen], ['görülmeyen (log, ikili, metin)', unseen]]) {
  for (const p of ['ExactMatch (auto)', 'Allmer 2016 kuralı']) {
    const m = t[p];
    md += `| ${label} | ${p} | ${m.cases} | ${pct(m.fastestRate)} | ${pct(m.within10Rate)} | ${fx(m.geomeanSlowdown)} | ${m.worstSlowdown.toFixed(2)}× |\n`;
  }
}
md += `\n## Molekülün kendi yükü\n\nMolekülün uçtan uca süresi / seçtiği atomun tek başına süresi: medyan ${fx(overhead[overhead.length >> 1])}, %90'lık dilim ${fx(overhead[Math.floor(overhead.length * 0.9)])}. `;
md += `(Karar için ilk kaydın şekli hesaplanır ve her atomun maliyeti tahmin edilir.)\n\n`;
md += `## En kötü 5 seçim\n\n| Vaka | Alfabe | n | k | m | Seçilen | Süresi (ms) | En hızlı | Süresi (ms) | Yavaşlama |\n|---:|---|---:|---:|---|---|---:|---|---:|---:|\n`;
for (const c of worst) {
  md += `| ${c.id} | ${c.alphabet} | ${c.n} | ${c.k} | ${c.lengths.join('/')} | ${c.selected} | ${c.times[c.selected].ms.toFixed(3)} | ${c.best} | ${c.bestMs.toFixed(3)} | ${(c.times[c.selected].ms / c.bestMs).toFixed(2)}× |\n`;
}
const wins = {};
for (const c of results) wins[c.best] = (wins[c.best] ?? 0) + 1;
const picks = {};
for (const c of results) picks[c.selected] = (picks[c.selected] ?? 0) + 1;
md += `\n## Hangi atom kaç vakada en hızlıydı / kaç vakada seçildi\n\n| Atom | En hızlı | Molekül seçti |\n|---|---:|---:|\n`;
for (const A of registry.candidates()) {
  const n = A.manifest.name;
  md += `| ${n} | ${wins[n] ?? 0} | ${picks[n] ?? 0} |\n`;
}
saveText(`${NAME}.md`, md);
process.stdout.write(md);
