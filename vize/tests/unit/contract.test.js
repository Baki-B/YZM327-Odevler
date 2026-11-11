// Sözleşme testleri (ödev bölüm 4): her atom bunları geçmelidir.
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { ALL_ATOMS, collect } from './helpers.js';
import { TASK } from '../../src/atomic/ExactSearchAtom.js';

const H = '>chr1 açıklama';
const E = (seq, header = H) => ({ header, seq });

for (const Atom of ALL_ATOMS) {
  const name = Atom.manifest.name;
  const run = (patterns, seqs, ignoreCase = false) =>
    collect(Atom, { patterns, ignoreCase }, seqs.map((s, i) => (typeof s === 'string' ? E(s, `>r${i}`) : s)));

  describe(`sözleşme: ${name}`, () => {
    test('manifest alanları', () => {
      const m = Atom.manifest;
      assert.equal(m.name, name);
      assert.equal(m.kind, 'atom');
      assert.equal(m.task, TASK);
      assert.equal(typeof m.version, 'string');
      assert.equal(typeof m.title, 'string');
      assert.ok(Array.isArray(m.references));
    });

    test('selection alanı (auto adayıysa) özellik ve varsayılan katsayı verir', () => {
      if (Atom.selection === null) return; // yalnızca NaiveSearch
      const shape = { n: 1000, sigma: 4, sigmaEff: 4, k: 2, mMin: 4, mMax: 8, mMean: 6 };
      const f = Atom.selection.features(shape);
      assert.ok(Object.keys(f).length > 0);
      for (const [key, v] of Object.entries(f)) {
        assert.ok(Number.isFinite(v) && v >= 0, `${key}=${v}`);
        assert.ok(key in Atom.selection.defaults, `${key} için varsayılan katsayı yok`);
      }
    });

    test('çıktı alanları ve 0 tabanlı konum', () => {
      const out = collect(Atom, { patterns: ['ACGT'] }, [E('TTACGTT')]);
      assert.deepEqual(out, [{ header: H, pattern: 'ACGT', position: 2, length: 4 }]);
      assert.deepEqual(Object.keys(out[0]), ['header', 'pattern', 'position', 'length']);
    });

    test('örtüşen eşleşmeler: "AAAAA" içinde "AA" → 0,1,2,3', () => {
      assert.deepEqual(run(['AA'], ['AAAAA']).map((m) => m.position), [0, 1, 2, 3]);
    });

    test('sıra: kayıt, sonra konum, eşitse desen listesindeki sıra', () => {
      const out = run(['CG', 'ACG', 'A'], ['ACGACG', 'CGA']);
      assert.deepEqual(out.map((m) => [m.header, m.position, m.pattern]), [
        ['>r0', 0, 'ACG'], ['>r0', 0, 'A'], ['>r0', 1, 'CG'],
        ['>r0', 3, 'ACG'], ['>r0', 3, 'A'], ['>r0', 4, 'CG'],
        ['>r1', 0, 'CG'], ['>r1', 2, 'A'],
      ]);
    });

    test('aynı desen iki kez verilirse ikisi de ayrı raporlanır', () => {
      const out = run(['GG', 'T', 'GG'], ['GGTGG']);
      assert.deepEqual(out.map((m) => [m.position, m.pattern]), [[0, 'GG'], [0, 'GG'], [2, 'T'], [3, 'GG'], [3, 'GG']]);
    });

    test('ignoreCase yalnızca ASCII harfleri eşitler; pattern verildiği gibi yazılır', () => {
      const out = run(['acGT', 'ACGT'], ['xACGTacgt'], true);
      assert.deepEqual(out.map((m) => [m.position, m.pattern]), [[1, 'acGT'], [1, 'ACGT'], [5, 'acGT'], [5, 'ACGT']]);
      assert.deepEqual(run(['i'], ['İıIi'], true).map((m) => m.position), [2, 3]); // Türkçe İ/ı ASCII değil
      assert.deepEqual(run(['é'], ['ÉéE'], true).map((m) => m.position), [1]);
      assert.deepEqual(run(['acgt'], ['ACGT'], false), []);
    });

    test('konumlar UTF-16 kod birimi cinsinden', () => {
      const out = run(['b', '😀'], ['a😀b']);
      assert.deepEqual(out.map((m) => [m.position, m.pattern, m.length]), [[1, '😀', 2], [3, 'b', 1]]);
    });

    test('desen metinden uzunsa ya da metin boşsa sonuç boş, hata yok', () => {
      assert.deepEqual(run(['ACGTACGT'], ['ACG']), []);
      assert.deepEqual(run(['A'], ['']), []);
      assert.deepEqual(run(['ACGT', 'A'], ['', 'C']), []);
    });

    test('boş desen listesi ya da boş desen hata verir', () => {
      assert.throws(() => new Atom({ patterns: [] }), TypeError);
      assert.throws(() => new Atom({ patterns: [''] }), TypeError);
      assert.throws(() => new Atom({ patterns: ['A', ''] }), TypeError);
      assert.throws(() => new Atom({}), TypeError);
      assert.throws(() => new Atom({ patterns: 'ACGT' }), TypeError);
      assert.throws(() => new Atom({ patterns: [42] }), TypeError);
    });

    test('process bir üreteçtir ve FASTA.Entry dışını reddeder', () => {
      const atom = new Atom({ patterns: ['A'] });
      const it = atom.process(E('AA'));
      assert.equal(typeof it.next, 'function');
      assert.throws(() => [...atom.process({ header: '>x' })], TypeError);
      assert.throws(() => [...atom.process(null)], TypeError);
    });

    test('deterministik: aynı girdi, aynı çıktı; atom yeniden kullanılabilir', () => {
      const atom = new Atom({ patterns: ['AT', 'TA', 'ATA'] });
      const a = [...atom.process(E('ATATATAT'))];
      const b = [...atom.process(E('GGGG'))];
      const c = [...atom.process(E('ATATATAT'))];
      assert.deepEqual(a, c);
      assert.deepEqual(b, []);
    });

    test('desen listesi dışarıda değiştirilse de atom etkilenmez', () => {
      const pats = ['AC'];
      const atom = new Atom({ patterns: pats });
      pats[0] = 'GG';
      assert.deepEqual([...atom.process(E('ACGG'))].map((m) => m.pattern), ['AC']);
    });
  });
}
