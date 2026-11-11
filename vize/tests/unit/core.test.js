// FASTA okuyucu, veri şekli, maliyet modeli ve kod tarama katmanı.
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { parseFasta, formatFasta } from '../../src/fasta.js';
import { computeShape } from '../../src/shape.js';
import { estimateCost, fitNonNegative } from '../../src/molecules/costModel.js';
import { HorspoolSearch } from '../../src/atomic/HorspoolSearch.js';
import { sourceToEntry, lineStarts, toLineColumn } from '../../src/adapters/sourceToEntry.js';
import { CodeScan } from '../../src/workflows/CodeScan.js';
import { PRESETS } from '../../src/workflows/presets.js';
import { rng, makeText } from '../../bench/data.js';

describe('FASTA', () => {
  test('başlık, çok satırlı dizi, boş satır, \\r\\n', () => {
    const e = parseFasta('>chr1 açıklama\r\nACGT\r\nAC GT\n\n>chr2\nGG\n');
    assert.deepEqual(e, [{ header: '>chr1 açıklama', seq: 'ACGTACGT' }, { header: '>chr2', seq: 'GG' }]);
  });
  test('başlıksız dizi hata verir; boş dosya boş liste', () => {
    assert.throws(() => parseFasta('ACGT\n'), SyntaxError);
    assert.deepEqual(parseFasta(''), []);
  });
  test('formatFasta ↔ parseFasta', () => {
    const e = [{ header: '>a', seq: 'A'.repeat(130) }, { header: '>b', seq: '' }];
    assert.deepEqual(parseFasta(formatFasta(e)), e);
  });
});

describe('veri şekli', () => {
  test('n, σ, σe, k, desen uzunlukları', () => {
    const s = computeShape({ header: '>x', seq: 'AACCGGTT' }, { patterns: ['AC', 'GGT', 'T'] });
    assert.deepEqual(s, { n: 8, sigma: 4, sigmaEff: 4, k: 3, mMin: 1, mMax: 3, mMean: 2, sampled: false });
  });
  test('ignoreCase açıkken a ile A tek karakter sayılır', () => {
    assert.equal(computeShape({ header: '>x', seq: 'aAbB' }, { patterns: ['A'], ignoreCase: true }).sigma, 2);
    assert.equal(computeShape({ header: '>x', seq: 'aAbB' }, { patterns: ['A'] }).sigma, 4);
  });
  test('uzun metinde örnekleme deterministik ve σ doğru', () => {
    const t = makeText('dna', 1_000_000, 5);
    const a = computeShape({ header: '>x', seq: t }, { patterns: ['A'] });
    const b = computeShape({ header: '>x', seq: t }, { patterns: ['A'] });
    assert.deepEqual(a, b);
    assert.equal(a.sampled, true);
    assert.equal(a.sigma, 4);
    assert.ok(Math.abs(a.sigmaEff - 4) < 0.05);
  });
  test('boş metin', () => {
    const s = computeShape({ header: '>x', seq: '' }, { patterns: ['AB'] });
    assert.equal(s.n, 0);
    assert.equal(s.sigma, 0);
  });
});

describe('maliyet modeli', () => {
  test('tahmin = Σ katsayı × özellik', () => {
    const shape = { n: 1000, sigma: 4, sigmaEff: 4, k: 1, mMin: 8, mMax: 8, mMean: 8 };
    const est = estimateCost(HorspoolSearch, shape);
    const f = HorspoolSearch.selection.features(shape);
    const d = HorspoolSearch.selection.defaults;
    const sum = Object.keys(f).reduce((s, key) => s + f[key] * d[key], 0);
    assert.ok(Math.abs(est.seconds - sum) < 1e-15);
    assert.equal(est.coefficients, 'defaults');
  });
  test('NNLS bilinen katsayıları geri bulur ve negatif katsayı vermez', () => {
    const r = rng(1);
    const rows = [];
    const t = [];
    for (let i = 0; i < 200; i++) {
      const x = [r() * 1e6, r() * 1e3, r() * 10];
      rows.push(x);
      t.push(2e-9 * x[0] + 5e-7 * x[1] + 0 * x[2] + 1e-6);
    }
    rows.forEach((x) => x.push(1));
    const c = fitNonNegative(rows, t);
    assert.ok(Math.abs(c[0] / 2e-9 - 1) < 0.02, String(c));
    assert.ok(Math.abs(c[1] / 5e-7 - 1) < 0.05, String(c));
    assert.ok(c.every((x) => x >= 0));
  });
});

describe('yazılım mühendisliği katmanı', () => {
  test('uyarlayıcı: dosya → FASTA.Entry', () => {
    assert.deepEqual(sourceToEntry({ path: 'a/b.py', text: 'x = 1\n' }), { header: '>a/b.py', seq: 'x = 1\n' });
    assert.throws(() => sourceToEntry({ path: 'x' }), TypeError);
  });
  test('satır/sütun hesabı', () => {
    const t = 'ab\ncd\n\nef';
    const s = lineStarts(t);
    assert.deepEqual(s, [0, 3, 6, 7]);
    assert.deepEqual(toLineColumn(s, 0), { line: 1, column: 1 });
    assert.deepEqual(toLineColumn(s, 4), { line: 2, column: 2 });
    assert.deepEqual(toLineColumn(s, 8), { line: 4, column: 2 });
  });
  test('CodeScan: TODO ve gizli bilgi bulur, satır ve sütunu doğru verir', () => {
    const files = [
      { path: 'app.py', text: 'def f():\n    # TODO: düzelt\n    password="1234"\n' },
      { path: 'web.js', text: 'el.innerHTML = x; // FIXME\n' },
    ];
    const todo = [...new CodeScan(PRESETS.todo).run(files)];
    assert.deepEqual(todo.map((f) => [f.file, f.line, f.column, f.pattern]), [['app.py', 2, 7, 'TODO'], ['web.js', 1, 22, 'FIXME']]);
    const sec = [...new CodeScan(PRESETS.secrets).run(files)];
    assert.deepEqual(sec.map((f) => [f.file, f.line, f.pattern]), [['app.py', 3, 'password=']]);
    const api = new CodeScan(PRESETS['banned-api']);
    assert.deepEqual([...api.run(files)].map((f) => f.pattern), ['innerHTML']);
    assert.ok(api.record.selected);
  });
  test('bütün hazır kümeler geçerli', () => {
    for (const [name, p] of Object.entries(PRESETS)) {
      assert.ok(p.patterns.length > 0, name);
      new CodeScan(p);
    }
  });
});
