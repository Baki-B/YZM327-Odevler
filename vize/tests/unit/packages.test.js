// Hazır paketler (src/workflows/packages.js): her paket iş akışı motoruyla çalışır ve
// her "Eşleşme → Bulgu" kutusunun bulgu sayısı (1) pakette yazan beklenen sayıya,
// (2) motordan bağımsız olarak CodeScan / ExactMatch ile hesaplanan sayıya eşittir.
// Komut satırıyla karşılaştırma: node scripts/paketler.js
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { createCatalog, parsePatternList } from '../../src/workflows/catalog.js';
import { deserializeWorkflow, runWorkflow, validateWorkflow, explainWorkflow } from '../../src/workflows/engine.js';
import { PACKAGES } from '../../src/workflows/packages.js';
import { PRESETS } from '../../src/workflows/presets.js';
import { loadSampleNode } from '../../src/workflows/samplesNode.js';
import { CodeScan } from '../../src/workflows/CodeScan.js';
import { ExactMatch } from '../../src/molecules/ExactMatch.js';
import { parseFasta } from '../../src/fasta.js';

const catalog = createCatalog();

/** Bir Bulgu kutusuna giden yolu geriye doğru izleyip aynı işi motor olmadan yapar. */
async function independentCount(wf, bulguId) {
  const byId = Object.fromEntries(wf.nodes.map((n) => [n.id, n]));
  const parents = (id, port) => wf.edges.filter((e) => e.to.node === id && (!port || e.to.port === port)).map((e) => byId[e.from.node]);
  const searcher = parents(bulguId)[0];
  const sets = parents(searcher.id, 'patterns').map((n) => (n.type === 'desen.ozel'
    ? { patterns: parsePatternList(n.params.patterns), ignoreCase: n.params.ignoreCase }
    : PRESETS[n.type.slice('desen.'.length)]));
  const patterns = sets.flatMap((s) => s.patterns);
  const ignoreCase = sets.some((s) => s.ignoreCase);
  const adapter = parents(searcher.id, 'entries')[0];
  const files = (await Promise.all(parents(adapter.id).map((s) => loadSampleNode(s.params.sample)))).flat();
  const strategy = searcher.type === 'molekul.ExactMatch' ? 'auto' : searcher.type.slice('atom.'.length);
  if (adapter.type === 'uyarlayici.kaynak') return [...new CodeScan({ patterns, ignoreCase, strategy }).run(files)].length;
  const entries = files.flatMap((f) => parseFasta(f.text));
  return [...new ExactMatch({ patterns, ignoreCase, strategy }).run(entries)].length;
}

describe('hazır paketler', () => {
  test('en az 6 paket, kimlikler benzersiz, her birinin açıklaması ve komut satırı karşılığı var', () => {
    assert.ok(PACKAGES.length >= 6);
    assert.equal(new Set(PACKAGES.map((p) => p.id)).size, PACKAGES.length);
    for (const p of PACKAGES) {
      assert.ok(p.summary.length > 20 && p.cli.length >= 1, p.id);
      assert.deepEqual(validateWorkflow(deserializeWorkflow(p.build(), catalog), catalog), [], p.id);
      assert.ok(explainWorkflow(deserializeWorkflow(p.build(), catalog), catalog).length > 50);
    }
  });

  for (const p of PACKAGES) {
    test(`${p.id}: beklenen bulgu sayısı ve bağımsız hesapla aynı`, async () => {
      const wf = deserializeWorkflow(p.build(), catalog);
      const res = await runWorkflow(wf, catalog, { loadSample: loadSampleNode, yieldEvery: 0 });
      assert.equal(res.ok, true, JSON.stringify(Object.entries(res.nodes).filter(([, r]) => r.status !== 'bitti')));
      const bulgu = wf.nodes.filter((n) => n.type === 'uyarlayici.bulgu');
      assert.deepEqual(Object.keys(p.expected).sort(), bulgu.map((n) => n.id).sort());
      for (const n of bulgu) {
        const got = res.nodes[n.id].outputs.findings.findings.length;
        assert.equal(got, p.expected[n.id], `${n.id}`);
        assert.equal(got, await independentCount(wf, n.id), `${n.id} bağımsız`);
      }
      for (const g of wf.nodes.filter((n) => n.type === 'cikti.kapi')) assert.equal(res.nodes[g.id].info.gate, 'kaldı');
    });
  }

  test('tek desen paketinde iki dal farklı atom seçer', async () => {
    const wf = deserializeWorkflow(PACKAGES.find((p) => p.id === 'tek-desen').build(), catalog);
    const res = await runWorkflow(wf, catalog, { loadSample: loadSampleNode, yieldEvery: 0 });
    assert.notEqual(res.nodes.tek_molekul.info.record.selected, res.nodes.cok_molekul.info.record.selected);
  });
});
