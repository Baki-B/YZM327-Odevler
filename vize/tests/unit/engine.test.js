// İş akışı motoru (src/workflows/engine.js) ve atölye kataloğu (src/workflows/catalog.js).
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import {
  createWorkflow, addNode, connect, canConnect, removeNode, removeEdge, topologicalOrder, validateWorkflow,
  runWorkflow, serializeWorkflow, deserializeWorkflow, explainWorkflow, FORMAT,
} from '../../src/workflows/engine.js';
import { createCatalog, parsePatternList, matchesToFindings } from '../../src/workflows/catalog.js';
import { raceAtoms } from '../../src/workflows/race.js';
import { CodeScan } from '../../src/workflows/CodeScan.js';
import { registry } from '../../src/registry.js';
import { ExactSearchAtom, TASK } from '../../src/atomic/ExactSearchAtom.js';

const catalog = createCatalog();
const CODE = 'def f():\n    # TODO: düzelt\n    x = eval(s)  # FIXME\n    return x\n// TODO son\n';

/** Kod → Kaynak→Entry → ExactMatch ← özel desen → Bulgu → tablo/özet/jsonl/kapı */
function codeFlow(text = CODE, patterns = 'TODO\nFIXME') {
  const wf = createWorkflow({ name: 'deneme', target: 'TODO avı' });
  addNode(wf, catalog, 'kaynak.kod', { id: 'src', params: { path: 'a.py', text } });
  addNode(wf, catalog, 'uyarlayici.kaynak', { id: 'ad' });
  addNode(wf, catalog, 'desen.ozel', { id: 'pat', params: { patterns } });
  addNode(wf, catalog, 'molekul.ExactMatch', { id: 'em' });
  addNode(wf, catalog, 'uyarlayici.bulgu', { id: 'bul' });
  addNode(wf, catalog, 'cikti.tablo', { id: 'tab' });
  addNode(wf, catalog, 'cikti.ozet', { id: 'oz' });
  addNode(wf, catalog, 'cikti.jsonl', { id: 'js' });
  addNode(wf, catalog, 'cikti.kapi', { id: 'gate' });
  connect(wf, catalog, { node: 'src', port: 'files' }, { node: 'ad', port: 'files' });
  connect(wf, catalog, { node: 'ad', port: 'entries' }, { node: 'em', port: 'entries' });
  connect(wf, catalog, { node: 'pat', port: 'patterns' }, { node: 'em', port: 'patterns' });
  connect(wf, catalog, { node: 'em', port: 'matches' }, { node: 'bul', port: 'matches' });
  for (const id of ['tab', 'oz', 'js', 'gate']) connect(wf, catalog, { node: 'bul', port: 'findings' }, { node: id, port: 'findings' });
  return wf;
}

describe('iş akışı motoru: yapı', () => {
  test('addNode varsayılan ayarları doldurur, kimlikler benzersiz', () => {
    const wf = createWorkflow();
    const a = addNode(wf, catalog, 'desen.ozel');
    const b = addNode(wf, catalog, 'desen.ozel');
    assert.notEqual(a.id, b.id);
    assert.equal(a.params.patterns, 'TODO');
    assert.equal(a.params.ignoreCase, false);
    assert.throws(() => addNode(wf, catalog, 'desen.ozel', { id: a.id }), /zaten var/);
    assert.throws(() => addNode(wf, catalog, 'yok.boyle'), /Bilinmeyen bileşen/);
  });

  test('uyumsuz tür bağlantısı reddedilir ve nedeni söylenir', () => {
    const wf = createWorkflow();
    addNode(wf, catalog, 'kaynak.kod', { id: 's' });
    addNode(wf, catalog, 'molekul.ExactMatch', { id: 'm' });
    const r = canConnect(wf, catalog, { node: 's', port: 'files' }, { node: 'm', port: 'entries' });
    assert.equal(r.ok, false);
    assert.match(r.reason, /Tür uyuşmuyor: "Kod yapıştır" Source\.File üretiyor/);
    assert.match(r.reason, /FASTA\.Entry bekliyor/);
    assert.match(r.reason, /uyarlayıcı/); // ipucu
    assert.throws(() => connect(wf, catalog, { node: 's', port: 'files' }, { node: 'm', port: 'entries' }), (e) => e.code === 'BAGLANTI_REDDEDILDI');
    assert.equal(wf.edges.length, 0);
  });

  test('tek girişli uç ikinci bağlantıyı reddeder, çok girişli uç kabul eder', () => {
    const wf = createWorkflow();
    addNode(wf, catalog, 'kaynak.kod', { id: 's1' });
    addNode(wf, catalog, 'kaynak.kod', { id: 's2' });
    addNode(wf, catalog, 'uyarlayici.kaynak', { id: 'a1' });
    addNode(wf, catalog, 'uyarlayici.kaynak', { id: 'a2' });
    addNode(wf, catalog, 'molekul.ExactMatch', { id: 'm' });
    connect(wf, catalog, { node: 's1', port: 'files' }, { node: 'a1', port: 'files' });
    connect(wf, catalog, { node: 's2', port: 'files' }, { node: 'a1', port: 'files' }); // multi
    connect(wf, catalog, { node: 'a1', port: 'entries' }, { node: 'm', port: 'entries' });
    const r = canConnect(wf, catalog, { node: 'a2', port: 'entries' }, { node: 'm', port: 'entries' });
    assert.equal(r.ok, false);
    assert.match(r.reason, /yalnızca bir bağlantı alır/);
    assert.equal(canConnect(wf, catalog, { node: 's1', port: 'files' }, { node: 'a1', port: 'files' }).ok, false); // aynı bağlantı
  });

  test('döngü ve kendine bağlantı reddedilir', () => {
    const wf = createWorkflow();
    addNode(wf, catalog, 'uyarlayici.kaynak', { id: 'a' });
    assert.match(canConnect(wf, catalog, { node: 'a', port: 'entries' }, { node: 'a', port: 'files' }).reason, /kendine/);
    // Gerçek bir döngüyü yapay bir katalogla dene: X → Y → X
    const cat = new Map([
      ['x', { type: 'x', title: 'X', inputs: [{ name: 'i', type: 'T', optional: true }], outputs: [{ name: 'o', type: 'T' }], run: () => ({ o: 1 }) }],
    ]);
    const w2 = createWorkflow();
    addNode(w2, cat, 'x', { id: 'X' });
    addNode(w2, cat, 'x', { id: 'Y' });
    connect(w2, cat, { node: 'X', port: 'o' }, { node: 'Y', port: 'i' });
    const r = canConnect(w2, cat, { node: 'Y', port: 'o' }, { node: 'X', port: 'i' });
    assert.equal(r.ok, false);
    assert.match(r.reason, /döngü/);
    // Elle eklenen döngü topolojik sırada yakalanır
    w2.edges.push({ from: { node: 'Y', port: 'o' }, to: { node: 'X', port: 'i' } });
    assert.throws(() => topologicalOrder(w2), /döngü/);
    assert.ok(validateWorkflow(w2, cat).some((p) => /döngü/.test(p.message)));
  });

  test('topolojik sıra: her düğüm girdilerinden sonra, eşitlikte liste sırası', () => {
    const wf = codeFlow();
    const order = topologicalOrder(wf).map((n) => n.id);
    const pos = Object.fromEntries(order.map((id, i) => [id, i]));
    for (const e of wf.edges) assert.ok(pos[e.from.node] < pos[e.to.node], `${e.from.node} → ${e.to.node}`);
    assert.deepEqual(order, ['src', 'ad', 'pat', 'em', 'bul', 'tab', 'oz', 'js', 'gate']);
    assert.deepEqual(topologicalOrder(wf).map((n) => n.id), order); // deterministik
  });

  test('eksik zorunlu giriş denetimde bildirilir; düğüm silinince bağlantıları da gider', () => {
    const wf = codeFlow();
    removeNode(wf, 'pat');
    assert.ok(!wf.edges.some((e) => e.from.node === 'pat'));
    const problems = validateWorkflow(wf, catalog);
    assert.equal(problems.length, 1);
    assert.match(problems[0].message, /"ExactMatch": "desenler" girişi \(Pattern\.Set\) bağlı değil/);
    removeEdge(wf, { from: { node: 'bul', port: 'findings' }, to: { node: 'tab', port: 'findings' } });
    assert.equal(validateWorkflow(wf, catalog).length, 2);
  });
});

describe('iş akışı motoru: çalıştırma', () => {
  test('kod taraması CodeScan ile aynı bulguları verir', async () => {
    const res = await runWorkflow(codeFlow(), catalog);
    assert.equal(res.ok, true);
    const got = res.nodes.tab.info.findings.map(({ file, line, column, pattern, position }) => ({ file, line, column, pattern, position }));
    const want = [...new CodeScan({ patterns: ['TODO', 'FIXME'] }).run([{ path: 'a.py', text: CODE }])];
    assert.deepEqual(got, want);
    assert.equal(got.length, 3);
    assert.equal(res.nodes.oz.info.total, 3);
    assert.deepEqual(res.nodes.oz.info.byPattern, [['TODO', 2], ['FIXME', 1]]);
    assert.equal(res.nodes.gate.info.gate, 'kaldı');
    assert.equal(res.nodes.em.info.record.requested, 'auto');
    assert.ok(registry.has(res.nodes.em.info.record.selected));
    // JSONL: ios scan --json ile aynı biçim
    assert.equal(res.nodes.js.info.jsonl, want.map((f) => JSON.stringify(f)).join('\n') + '\n');
    // Önizleme eşleşen kısmı ayırır
    const p = res.nodes.tab.info.findings[0].preview;
    assert.equal(p.hit, 'TODO');
    assert.match(p.before, /# $/);
  });

  test('bulgu yoksa kapı geçer', async () => {
    const res = await runWorkflow(codeFlow('print(1)\n', 'TODO'), catalog);
    assert.equal(res.nodes.gate.info.gate, 'geçti');
    assert.equal(res.nodes.js.info.jsonl, '');
  });

  test('hata veren kutudan sonrakiler atlanır, ilgisizler çalışır', async () => {
    const wf = codeFlow();
    wf.nodes.find((n) => n.id === 'pat').params.patterns = '\n\n';
    const res = await runWorkflow(wf, catalog);
    assert.equal(res.ok, false);
    assert.equal(res.nodes.pat.status, 'hata');
    assert.match(res.nodes.pat.error, /En az bir desen/);
    assert.equal(res.nodes.em.status, 'atlandı');
    assert.equal(res.nodes.gate.status, 'atlandı');
    assert.equal(res.nodes.ad.status, 'bitti');
  });

  test('çalıştırılamayan iş akışı sorun listesiyle döner', async () => {
    const wf = codeFlow();
    removeNode(wf, 'src');
    const res = await runWorkflow(wf, catalog);
    assert.equal(res.ok, false);
    assert.ok(res.problems.length >= 1);
  });

  test('çok girişli desen ucu kümeleri birleştirir (ios scan --preset + --patterns gibi)', async () => {
    const wf = codeFlow(CODE, 'eval(');
    addNode(wf, catalog, 'desen.todo', { id: 'todo' });
    connect(wf, catalog, { node: 'todo', port: 'patterns' }, { node: 'em', port: 'patterns' });
    const res = await runWorkflow(wf, catalog);
    const want = [...new CodeScan({ patterns: ['eval(', 'TODO', 'FIXME', 'HACK', 'XXX'] }).run([{ path: 'a.py', text: CODE }])];
    assert.equal(res.nodes.oz.info.total, want.length);
    assert.equal(want.length, 4);
  });

  test('FASTA okuyucu + atom kutusu: NaiveSearch ile aynı eşleşmeler', async () => {
    const wf = createWorkflow();
    addNode(wf, catalog, 'kaynak.fasta', { id: 'f', params: { text: '>a\nGATCGATC\nGGATCC\n>b\nAAGATC\n' } });
    addNode(wf, catalog, 'uyarlayici.fasta', { id: 'r' });
    addNode(wf, catalog, 'desen.ozel', { id: 'p', params: { patterns: 'GATC\nGGATCC' } });
    addNode(wf, catalog, 'atom.HorspoolSearch', { id: 'h' });
    addNode(wf, catalog, 'atom.NaiveSearch', { id: 'n' });
    connect(wf, catalog, { node: 'f', port: 'files' }, { node: 'r', port: 'files' });
    for (const a of ['h', 'n']) {
      connect(wf, catalog, { node: 'r', port: 'entries' }, { node: a, port: 'entries' });
      connect(wf, catalog, { node: 'p', port: 'patterns' }, { node: a, port: 'patterns' });
    }
    const res = await runWorkflow(wf, catalog);
    assert.equal(res.ok, true);
    assert.deepEqual(res.nodes.h.outputs.matches.matches, res.nodes.n.outputs.matches.matches);
    assert.equal(res.nodes.h.info.count, 5); // a: GATC@0,4, GGATCC@8 → GATC@9; b: GATC@2
  });

  test('örnek veri yükleyicisi ctx üzerinden verilir', async () => {
    const wf = createWorkflow();
    addNode(wf, catalog, 'kaynak.ornek', { id: 'o', params: { sample: 'lambda' } });
    const ok = await runWorkflow(wf, catalog, { loadSample: async (name) => [{ path: name, text: '>x\nA\n' }] });
    assert.equal(ok.nodes.o.status, 'bitti');
    assert.deepEqual(ok.nodes.o.outputs.files, [{ path: 'lambda', text: '>x\nA\n' }]);
    const bad = await runWorkflow(wf, catalog);
    assert.equal(bad.nodes.o.status, 'hata');
  });
});

describe('iş akışı motoru: dışa/içe aktarma ve açıklama', () => {
  test('JSON gidiş-dönüş aynı iş akışını verir', async () => {
    const wf = codeFlow();
    wf.nodes[0].x = 12.6;
    const json = JSON.parse(JSON.stringify(serializeWorkflow(wf)));
    assert.equal(json.format, FORMAT);
    const back = deserializeWorkflow(json, catalog);
    assert.deepEqual(serializeWorkflow(back), json);
    assert.equal(back.nodes[0].x, 13);
    const a = await runWorkflow(wf, catalog);
    const b = await runWorkflow(back, catalog);
    assert.deepEqual(b.nodes.tab.info.findings, a.nodes.tab.info.findings);
  });

  test('yabancı ya da bozuk dosya reddedilir', () => {
    assert.throws(() => deserializeWorkflow({ format: 'baska' }, catalog), /atölye iş akışı değil/);
    assert.throws(() => deserializeWorkflow(null, catalog), /JSON nesnesi/);
    const json = serializeWorkflow(codeFlow());
    json.edges.push({ from: { node: 'src', port: 'files' }, to: { node: 'em', port: 'entries' } });
    assert.throws(() => deserializeWorkflow(json, catalog), /Tür uyuşmuyor/);
    const j2 = serializeWorkflow(codeFlow());
    j2.version = 99;
    assert.throws(() => deserializeWorkflow(j2, catalog), /sürüm/);
  });

  test('açıklama kurala dayalı, sıralı ve deterministik', async () => {
    const wf = codeFlow();
    const text = explainWorkflow(wf, catalog);
    assert.equal(text, explainWorkflow(wf, catalog));
    const lines = text.split('\n');
    assert.match(lines[0], /"deneme" iş akışında 9 kutu ve 8 bağlantı var/);
    assert.match(lines[1], /Hedef: TODO avı/);
    assert.match(text, /^4\. "ExactMatch" "Kaynak → FASTA\.Entry" ve "Özel desen listesi" kutusundan gelen veriyle: ilk kaydın şekline/m);
    const run = await runWorkflow(wf, catalog);
    assert.match(explainWorkflow(wf, catalog, run), /Sonuç: 3 eşleşme; seçilen atom/);
    removeNode(wf, 'pat');
    assert.match(explainWorkflow(wf, catalog), /düzeltilmesi gereken 1 sorun/);
  });
});

describe('atölye kataloğu', () => {
  test('her kayıtlı atom bir kutu, molekülün strateji listesi kayıt defterinden', () => {
    for (const name of registry.names()) assert.ok(catalog.get(`atom.${name}`), name);
    const strat = catalog.get('molekul.ExactMatch').params[0].options.map((o) => o.value);
    assert.deepEqual(strat, ['auto', ...registry.names()]);
    for (const c of catalog.values()) assert.ok(catalog.categories.includes(c.category), c.type);
  });

  test('kayıt defterine eklenen sahte atom katalogda ve molekülde görünür (katalog kodu değişmeden)', async () => {
    class FakeSearch extends ExactSearchAtom {
      static manifest = { name: 'FakeSearch', version: '0.0.1', kind: 'atom', task: TASK, title: 'Exact match (fake)', references: ['test'] };
      static selection = { features: () => ({ fixed: 1 }), defaults: { fixed: 1e-12 } };
      *process(entry) {
        yield* registry.get('NaiveSearch').prototype.process.call(this, entry);
      }
    }
    const reg = registry.clone();
    reg.register(FakeSearch);
    const cat = createCatalog(reg);
    assert.ok(cat.get('atom.FakeSearch'));
    const wf = codeFlow();
    const res = await runWorkflow(deserializeWorkflow(serializeWorkflow(wf), cat), cat);
    assert.equal(res.nodes.em.info.record.selected, 'FakeSearch');
    assert.equal(res.nodes.oz.info.total, 3);
  });

  test('özel desen listesi: satır başına bir desen, boş satırlar atılır', () => {
    assert.deepEqual(parsePatternList('a,b\n\nc d\r\n'), ['a,b', 'c d']);
  });

  test('FASTA kaydında bulgu satırı 1, sütun konum + 1', () => {
    const v = matchesToFindings({ matches: [{ header: '>x', pattern: 'AC', position: 4, length: 2 }], entries: [{ header: '>x', seq: 'GGGGACGG' }] });
    assert.deepEqual({ ...v.findings[0], preview: undefined }, { file: 'x', line: 1, column: 5, pattern: 'AC', position: 4, length: 2, preview: undefined });
  });
});

describe('atomları yarıştır', () => {
  test('her aday atom ölçülür, eşleşme sayıları aynı, tahminler molekülden', () => {
    const entries = [{ header: '>x', seq: 'ACGT'.repeat(2000) + 'GATC' }];
    let t = 0;
    const r = raceAtoms(entries, { patterns: ['GATC', 'CGTA'], ignoreCase: false }, { reps: 3, warmup: 1, now: () => (t += 1) });
    assert.deepEqual(r.rows.map((x) => x.name).sort(), registry.candidates().map((A) => A.manifest.name).sort());
    assert.ok(r.rows.every((x) => x.hits === r.rows[0].hits));
    assert.ok(r.rows.every((x) => x.ms > 0 && Number.isFinite(x.estimatedMs)));
    assert.ok(registry.has(r.selected));
    assert.equal(r.fastest, r.rows.reduce((a, b) => (b.ms < a.ms ? b : a)).name);
  });
});
