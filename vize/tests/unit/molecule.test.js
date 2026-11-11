// Molekül testleri (Görev 3).
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { ExactMatch } from '../../src/molecules/ExactMatch.js';
import { registry, Registry, createDefaultRegistry } from '../../src/registry.js';
import { NaiveSearch } from '../../src/atomic/NaiveSearch.js';
import { TASK } from '../../src/atomic/ExactSearchAtom.js';
import { oracle, loadFasta } from './helpers.js';
import { makeText, makePatterns } from '../../bench/data.js';
import { readFileSync } from 'node:fs';

const lambda = loadFasta('lambda_NC_001416.fa');

/** Test için sahte atom: doğru sonuç verir (NaiveSearch'ten türer), maliyetini istediğimiz gibi bildirir. */
function fakeAtom(name, { cost = 1e-12, applicable } = {}) {
  return class extends NaiveSearch {
    static manifest = { name, version: '0.0.1', kind: 'atom', task: TASK, title: `Sahte ${name}`, references: [] };
    static selection = {
      features: (shape) => ({ scan: shape.n + 1 }),
      defaults: { scan: cost },
      ...(applicable ? { applicable } : {}),
    };
  };
}

describe('ExactMatch molekülü', () => {
  test('record doğru alanları içerir ve en ucuz tahmin seçilir', () => {
    const em = new ExactMatch({ patterns: ['GATC', 'GGATCC'], strategy: 'auto' });
    const out = [...em.run(lambda)];
    const r = em.record;
    assert.deepEqual(Object.keys(r), ['requested', 'selected', 'shape', 'estimates', 'why']);
    assert.equal(r.requested, 'auto');
    for (const key of ['n', 'sigma', 'sigmaEff', 'k', 'mMin', 'mMax', 'mMean']) assert.ok(key in r.shape, key);
    assert.equal(r.shape.n, 48502);
    assert.equal(r.shape.sigma, 4);
    assert.equal(r.shape.k, 2);
    assert.equal(r.shape.mMin, 4);
    assert.equal(r.shape.mMax, 6);
    assert.equal(r.shape.mMean, 5);
    const applicable = Object.entries(r.estimates).filter(([, e]) => e.applicable);
    assert.ok(applicable.length >= 7);
    const cheapest = applicable.reduce((a, b) => (b[1].ms < a[1].ms ? b : a));
    assert.equal(r.selected, cheapest[0]);
    assert.equal(typeof r.why, 'string');
    assert.ok(r.why.includes(r.selected));
    assert.deepEqual(out, oracle({ patterns: ['GATC', 'GGATCC'] }, lambda));
  });

  test('zorla seçilen her strateji aynı sonucu verir', () => {
    const t = makeText('protein', 30000, 3);
    const entries = [{ header: '>a', seq: t }, { header: '>b', seq: t.slice(5000, 9000) }];
    const patterns = makePatterns(t, 12, [3, 7, 20, 45], 4);
    const want = oracle({ patterns }, entries);
    for (const name of registry.names()) {
      const em = new ExactMatch({ patterns, strategy: name });
      assert.deepEqual([...em.run(entries)], want, name);
      assert.equal(em.record.selected, name);
      assert.equal(em.record.requested, name);
      assert.ok(em.record.why.includes('adıyla'));
    }
  });

  test('bilinmeyen strateji geçerli seçenekleri listeleyerek hata verir', () => {
    assert.throws(() => new ExactMatch({ patterns: ['A'], strategy: 'Hizli' }), (err) => {
      assert.match(err.message, /Hizli/);
      for (const n of ['auto', ...registry.names()]) assert.ok(err.message.includes(n), n);
      return true;
    });
  });

  test('kayıt defterine eklenen sahte atom, molekül kodu değişmeden seçilebilir', () => {
    const reg = createDefaultRegistry();
    const Fake = fakeAtom('FakeSearch');
    reg.register(Fake);
    const em = new ExactMatch({ patterns: ['GATC'] }, { registry: reg });
    const out = [...em.run(lambda)];
    assert.equal(em.record.selected, 'FakeSearch');
    assert.equal(em.record.estimates.FakeSearch.coefficients, 'defaults');
    assert.deepEqual(out, oracle({ patterns: ['GATC'] }, lambda));
    // adıyla da seçilebilir
    assert.equal(new ExactMatch({ patterns: ['A'], strategy: 'FakeSearch' }, { registry: reg }).strategy, 'FakeSearch');
    // varsayılan kayıt defteri etkilenmedi
    assert.equal(registry.has('FakeSearch'), false);
  });

  test('paylaşılan kayıt defterine çalışma anında eklenen atom da seçilir', () => {
    const Fake = fakeAtom('RuntimeFake');
    registry.register(Fake);
    try {
      const em = new ExactMatch({ patterns: ['ACGT'] });
      em.decide({ header: '>x', seq: 'ACGTACGT' });
      assert.equal(em.record.selected, 'RuntimeFake');
    } finally {
      registry.unregister('RuntimeFake');
    }
  });

  test('kendini uygulanamaz ilan eden atom hiç seçilmez', () => {
    const reg = new Registry();
    reg.register(fakeAtom('CheapButNo', { cost: 1e-15, applicable: () => 'test için uygun değil' }));
    reg.register(fakeAtom('Expensive', { cost: 1 }));
    for (const seq of ['', 'A', 'ACGT'.repeat(1000)]) {
      const em = new ExactMatch({ patterns: ['ACG', 'T'] }, { registry: reg });
      [...em.run([{ header: '>x', seq }])];
      assert.equal(em.record.selected, 'Expensive');
      assert.equal(em.record.estimates.CheapButNo.applicable, false);
      assert.equal(em.record.estimates.CheapButNo.reason, 'test için uygun değil');
      assert.ok(em.record.why.includes('CheapButNo'));
    }
  });

  test('Shift-Or 32 karakterden uzun desende auto kipinde seçilmez', () => {
    const em = new ExactMatch({ patterns: ['A'.repeat(33)] });
    em.decide({ header: '>x', seq: 'A'.repeat(100) });
    assert.equal(em.record.estimates.ShiftOrSearch.applicable, false);
    assert.notEqual(em.record.selected, 'ShiftOrSearch');
  });

  test('karar yalnızca ilk kayda göre verilir ve akış boyunca aynı atom kullanılır', () => {
    const reg = new Registry();
    reg.register(fakeAtom('SmallText', { applicable: (s) => (s.n < 100 ? true : 'metin uzun') }));
    reg.register(fakeAtom('BigText', { cost: 1, applicable: (s) => (s.n >= 100 ? true : 'metin kısa') }));
    const em = new ExactMatch({ patterns: ['A'] }, { registry: reg });
    const entries = [{ header: '>kisa', seq: 'AAA' }, { header: '>uzun', seq: 'A'.repeat(500) }];
    const out = [...em.run(entries)];
    assert.equal(em.record.selected, 'SmallText');
    assert.equal(em.record.shape.n, 3);
    assert.equal(out.length, 503);
  });

  test('uygulanabilir atom yoksa açıklayıcı hata', () => {
    const reg = new Registry();
    reg.register(fakeAtom('Never', { applicable: () => 'asla' }));
    const em = new ExactMatch({ patterns: ['A'] }, { registry: reg });
    assert.throws(() => [...em.run([{ header: '>x', seq: 'A' }])], /uygulanabilir/);
  });

  test('boş akışta sonuç boş, record yine dolu', () => {
    const em = new ExactMatch({ patterns: ['A'] });
    assert.deepEqual([...em.run([])], []);
    assert.equal(em.record.shape.n, 0);
    assert.ok(em.record.selected);
  });

  test('parametre hataları molekülde de geçerli', () => {
    assert.throws(() => new ExactMatch({ patterns: [] }), TypeError);
    assert.throws(() => new ExactMatch({ patterns: ['A', ''] }), TypeError);
  });

  test('kalibre katsayı verilirse kullanılır ve record bunu söyler', () => {
    const coefficients = { atoms: { KmpSearch: { base: 0, out: 0, scan: 1e-15, prep: 0 } } };
    const em = new ExactMatch({ patterns: ['ACGT'] }, { coefficients });
    em.decide({ header: '>x', seq: 'ACGT'.repeat(100) });
    assert.equal(em.record.selected, 'KmpSearch');
    assert.equal(em.record.estimates.KmpSearch.coefficients, 'calibrated');
  });

  test('ExactMatch.js içinde hiçbir atom adı geçmez (genişletilebilirlik)', () => {
    const src = readFileSync(new URL('../../src/molecules/ExactMatch.js', import.meta.url), 'utf8');
    for (const name of registry.names()) assert.ok(!src.includes(name), `${name} molekül kodunda geçiyor`);
  });
});

describe('kayıt defteri', () => {
  test('sözleşmeye uymayan atom reddedilir', () => {
    const reg = new Registry();
    assert.throws(() => reg.register(class {}), TypeError);
    assert.throws(() => reg.register(class extends NaiveSearch { static manifest = { ...NaiveSearch.manifest, task: 'baska.gorev' }; }), TypeError);
    assert.throws(() => reg.register(class extends NaiveSearch { static manifest = { ...NaiveSearch.manifest, name: 'X' }; static selection = { defaults: {} }; }), TypeError);
    reg.register(NaiveSearch);
    assert.throws(() => reg.register(NaiveSearch), /zaten/);
  });
  test('varsayılan kayıt defteri: 9 atom, NaiveSearch auto adayı değil', () => {
    assert.equal(registry.names().length, 9);
    assert.ok(!registry.candidates().includes(NaiveSearch));
    assert.equal(registry.candidates().length, 8);
    assert.deepEqual(registry.clone().names(), registry.names());
  });
});
