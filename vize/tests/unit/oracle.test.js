// Doğruluk kanıtı (Görev 2): her atom ve molekül, bütün veri kümelerinde
// NaiveSearch ile eleman eleman aynı sonucu vermelidir.
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { ATOMS, collect, oracle, loadFasta, assertSameMatches } from './helpers.js';
import { ExactMatch } from '../../src/molecules/ExactMatch.js';
import { makeText, makePatterns, rng } from '../../bench/data.js';

const lambda = loadFasta('lambda_NC_001416.fa');
const ecoli = loadFasta('ecoli_k12_126_proteins.fasta');

/** Bir veri kümesini bütün atomlar + molekül ile oracle'a karşı sınar. */
function checkAll(params, entries) {
  const want = oracle(params, entries);
  for (const Atom of ATOMS) {
    const got = collect(Atom, params, entries);
    assertSameMatches(got, want, Atom.manifest.name);
  }
  const em = new ExactMatch({ ...params, strategy: 'auto' });
  const got = [...em.run(entries)];
  assertSameMatches(got, want, `ExactMatch(auto→${em.record.selected})`);
  return want.length;
}

function slices(seq, k, lengths, seed) {
  return makePatterns(seq, k, lengths, seed);
}

describe('gerçek veri: lambda faj genomu (NC_001416.1, 48 502 baz)', () => {
  const g = lambda[0].seq;
  test('veri yüklendi', () => {
    assert.equal(lambda.length, 1);
    assert.equal(g.length, 48502);
  });
  test('kısa desenler (1–8)', () => {
    const hits = checkAll({ patterns: ['GATC', 'GAATTC', 'A', 'TTTT', 'GGATCC', 'CGCG'] }, lambda);
    assert.ok(hits > 10000);
  });
  test('uzun desenler (40–300)', () => {
    checkAll({ patterns: slices(g, 6, [40, 64, 100, 300], 11) }, lambda);
  });
  test('çok sayıda desen (300 desen, 6–30 uzunluk)', () => {
    checkAll({ patterns: slices(g, 300, [6, 10, 16, 22, 30], 12) }, lambda);
  });
  test('ignoreCase: küçük harfli desenler', () => {
    const pats = slices(g, 20, [5, 12], 13).map((p) => p.toLowerCase());
    assert.ok(checkAll({ patterns: pats, ignoreCase: true }, lambda) > 0);
  });
  test('genom parçalara bölünmüş çok kayıtlı akış', () => {
    const parts = [];
    for (let i = 0; i < 10; i++) parts.push({ header: `>lambda_${i}`, seq: g.slice(i * 4850, (i + 1) * 4850) });
    checkAll({ patterns: ['GATC', 'GCGC', ...slices(g, 10, [8, 20], 14)] }, parts);
  });
});

describe('gerçek veri: 126 E. coli K-12 proteini', () => {
  test('veri yüklendi', () => {
    assert.equal(ecoli.length, 126);
  });
  test('kısa motifler', () => {
    assert.ok(checkAll({ patterns: ['M', 'KK', 'GG', 'HHH', 'CXXC', 'GXGXXG', 'LL'] }, ecoli) > 1000);
  });
  test('proteinlerden kesilmiş desenler (3–60)', () => {
    const all = ecoli.map((e) => e.seq).join('');
    checkAll({ patterns: slices(all, 120, [3, 5, 8, 15, 30, 60], 21) }, ecoli);
  });
  test('ignoreCase ve tekrar eden desen', () => {
    checkAll({ patterns: ['mkk', 'MKK', 'lla', 'mkk'], ignoreCase: true }, ecoli);
  });
});

describe('sentetik veri', () => {
  const cases = [
    ['DNA', 'dna', 20000], ['protein', 'protein', 20000], ['metin', 'text', 20000],
    ['ikili alfabe (ab)', 'binary', 20000], ['kaynak kod', 'code', 20000], ['log', 'log', 20000],
  ];
  for (const [title, alpha, n] of cases) {
    test(`${title}: kısa, uzun ve çok desen`, () => {
      const t = makeText(alpha, n, 101);
      const E = [{ header: `>${alpha}`, seq: t }];
      checkAll({ patterns: makePatterns(t, 3, [2, 4], 1) }, E);
      checkAll({ patterns: makePatterns(t, 4, [33, 64, 120], 2) }, E);
      checkAll({ patterns: makePatterns(t, 64, [4, 8, 16], 3) }, E);
      checkAll({ patterns: makePatterns(t, 8, [1, 5, 40], 4), ignoreCase: true }, E);
    });
  }
  test('çok tekrarlı metin: ATATAT…, AAAA…', () => {
    const at = 'AT'.repeat(5000);
    const aa = 'A'.repeat(10000);
    const E = [{ header: '>at', seq: at }, { header: '>aa', seq: aa }];
    checkAll({ patterns: ['AT', 'TA', 'ATA', 'ATAT'.repeat(10), 'A', 'AA', 'A'.repeat(50), 'AAAT'] }, E);
  });
  test('karışık uzunluk, aynı desen iki kez, çok kayıt, ignoreCase', () => {
    const t = makeText('text', 5000, 7);
    const E = [0, 1, 2, 3].map((i) => ({ header: `>p${i}`, seq: t.slice(i * 1000, i * 1000 + 1500) }));
    const pats = makePatterns(t, 10, [1, 3, 9, 27, 70], 8);
    checkAll({ patterns: [...pats, pats[2], pats[0]], ignoreCase: true }, E);
  });
});

describe('tohumlu rastgele testler', () => {
  test('360 rastgele vaka (tohum 2026)', () => {
    const r = rng(2026);
    const alphas = ['dna', 'protein', 'text', 'binary', 'code', 'log', 'repeat'];
    let total = 0;
    for (let c = 0; c < 360; c++) {
      const alpha = alphas[c % alphas.length];
      const n = Math.floor(r() * 600);
      const t = makeText(alpha, Math.max(n, 1), 1000 + c).slice(0, n);
      const k = 1 + Math.floor(r() * 8);
      const lens = [];
      for (let i = 0; i < k; i++) lens.push(1 + Math.floor(r() * (r() < 0.2 ? 80 : 10)));
      const pats = makePatterns(t.length ? t : 'ACGT', k, lens, 5000 + c);
      if (r() < 0.2) pats.push(pats[0]);
      const records = r() < 0.3 ? [{ header: '>a', seq: t }, { header: '>b', seq: t.slice(0, n >> 1) }, { header: '>c', seq: '' }] : [{ header: '>a', seq: t }];
      try {
        total += checkAll({ patterns: pats, ignoreCase: r() < 0.3 }, records);
      } catch (err) {
        err.message = `vaka ${c} (alfabe ${alpha}, n=${n}, desenler ${JSON.stringify(pats).slice(0, 200)}): ${err.message}`;
        throw err;
      }
    }
    assert.ok(total > 0);
  });
});
