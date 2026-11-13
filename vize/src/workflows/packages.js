// Hazır paketler: tek tıkla açılan örnek iş akışları (atölye, web/).
// Her paket: hazır bağlanmış kutular + örnek veri (kaynak.ornek ile depodaki gerçek
// dosyalardan) + bir cümlelik açıklama + beklenen sonuç + aynı işi yapan komut satırı.
// Beklenen sayılar `node scripts/paketler.js` çıktısından alındı ve
// tests/unit/packages.test.js ile her `npm test`te yeniden denetlenir.

import { FORMAT, FORMAT_VERSION } from './engine.js';

const COL = [20, 245, 470, 695, 920]; // kutu genişliği 190 px

function node(id, type, x, y, params = {}) {
  return { id, type, x, y, params };
}
function edge(from, fromPort, to, toPort) {
  return { from: { node: from, port: fromPort }, to: { node: to, port: toPort } };
}
function wf(name, target, nodes, edges) {
  return { format: FORMAT, version: FORMAT_VERSION, name, target, nodes, edges };
}

/** Kaynak → uyarlayıcı → ExactMatch ← desen(ler) → Bulgu → çıktılar (en sık kullanılan iskelet). */
function scanSkeleton({ sample, patternNodes, outputs, adapter = 'uyarlayici.kaynak', strategy = 'auto', prefix = '' , y0 = 40 }) {
  const p = (s) => prefix + s;
  const nodes = [
    node(p('kaynak'), 'kaynak.ornek', COL[0], y0, { sample }),
    node(p('uyarlayici'), adapter, COL[1], y0),
    ...patternNodes.map((pn, i) => node(p(`desen${i + 1}`), pn.type, COL[1], y0 + 120 + i * 110, pn.params ?? {})),
    node(p('molekul'), 'molekul.ExactMatch', COL[2], y0 + 50, { strategy }),
    node(p('bulgu'), 'uyarlayici.bulgu', COL[3], y0 + 50),
    ...outputs.map((o, i) => node(p(`cikti${i + 1}`), o.type, COL[4], y0 + i * 105, o.params ?? {})),
  ];
  const edges = [
    edge(p('kaynak'), 'files', p('uyarlayici'), 'files'),
    edge(p('uyarlayici'), 'entries', p('molekul'), 'entries'),
    ...patternNodes.map((_, i) => edge(p(`desen${i + 1}`), 'patterns', p('molekul'), 'patterns')),
    edge(p('molekul'), 'matches', p('bulgu'), 'matches'),
    ...outputs.map((_, i) => edge(p('bulgu'), 'findings', p(`cikti${i + 1}`), 'findings')),
  ];
  return { nodes, edges };
}

const TABLE = { type: 'cikti.tablo' };
const SUMMARY = { type: 'cikti.ozet' };
const JSONL = { type: 'cikti.jsonl' };
const GATE = { type: 'cikti.kapi' };

function teknikBorc() {
  const s = scanSkeleton({ sample: 'agora', patternNodes: [{ type: 'desen.todo' }], outputs: [TABLE, SUMMARY, JSONL] });
  return wf('Teknik borç avı', 'Agora kodunda TODO / FIXME / HACK / XXX notlarını bul', s.nodes, s.edges);
}

function gizliBilgi() {
  const s = scanSkeleton({ sample: 'gizli', patternNodes: [{ type: 'desen.secrets' }], outputs: [TABLE, GATE, SUMMARY] });
  return wf('Gizli bilgi sızıntısı', 'Depoya girmiş parola, API anahtarı ve özel anahtar izlerini yakala; varsa derlemeyi durdur', s.nodes, s.edges);
}

function yasakliApi() {
  const s = scanSkeleton({ sample: 'agora', patternNodes: [{ type: 'desen.banned-api' }], outputs: [TABLE, SUMMARY, GATE] });
  return wf('Yasaklı / riskli API', 'Agora kodunda eval(, exec(, innerHTML, pickle.loads, os.system( gibi riskli çağrıları bul', s.nodes, s.edges);
}

function logIncelemesi() {
  const s = scanSkeleton({
    sample: 'log',
    patternNodes: [{ type: 'desen.errors' }, { type: 'desen.ozel', params: { patterns: 'timeout', ignoreCase: false } }],
    outputs: [TABLE, SUMMARY, JSONL],
  });
  return wf('Log incelemesi', 'Uygulama logunda ERROR / Exception / Traceback / timeout satırlarını topla', s.nodes, s.edges);
}

export const KEYWORDS = ['def', 'class', 'return', 'import', 'self', 'lambda', 'yield', 'await', 'async', 'raise', 'except', 'finally', 'while', 'elif', 'assert', 'global'];

function tekDesen() {
  // Aynı büyük dosya, iki dal: tek desen ve 16 desen. Molekül iki dalda farklı atom seçer.
  const a = scanSkeleton({ sample: 'korpus', patternNodes: [{ type: 'desen.ozel', params: { patterns: 'return', ignoreCase: false } }], outputs: [SUMMARY], prefix: 'tek_', y0: 30 });
  const b = scanSkeleton({ sample: 'korpus', patternNodes: [{ type: 'desen.ozel', params: { patterns: KEYWORDS.join('\n'), ignoreCase: false } }], outputs: [SUMMARY], prefix: 'cok_', y0: 330 });
  return wf('Tek desen, büyük dosya', 'Aynı 880 KB dosyada tek desen ile 16 desen: molekül neden farklı atom seçiyor?', [...a.nodes, ...b.nodes], [...a.edges, ...b.edges]);
}

function biyoloji() {
  // Lambda genomu: molekül ve tek bir atom aynı girdide aynı eşleşmeleri verir.
  const nodes = [
    node('kaynak', 'kaynak.ornek', COL[0], 60, { sample: 'lambda' }),
    node('okuyucu', 'uyarlayici.fasta', COL[1], 60),
    node('desen1', 'desen.ozel', COL[1], 200, { patterns: 'GATC\nGGATCC', ignoreCase: false }),
    node('molekul', 'molekul.ExactMatch', COL[2], 40, { strategy: 'auto' }),
    node('atom', 'atom.Bm4DnaDsSearch', COL[2], 250),
    node('bulgu', 'uyarlayici.bulgu', COL[3], 40),
    node('cikti1', 'cikti.tablo', COL[4], 0),
    node('cikti2', 'cikti.ozet', COL[4], 110),
    node('bulgu_atom', 'uyarlayici.bulgu', COL[3], 250),
    node('cikti3', 'cikti.ozet', COL[4], 250),
  ];
  const edges = [
    edge('kaynak', 'files', 'okuyucu', 'files'),
    edge('okuyucu', 'entries', 'molekul', 'entries'),
    edge('desen1', 'patterns', 'molekul', 'patterns'),
    edge('okuyucu', 'entries', 'atom', 'entries'),
    edge('desen1', 'patterns', 'atom', 'patterns'),
    edge('molekul', 'matches', 'bulgu', 'matches'),
    edge('bulgu', 'findings', 'cikti1', 'findings'),
    edge('bulgu', 'findings', 'cikti2', 'findings'),
    edge('atom', 'matches', 'bulgu_atom', 'matches'),
    edge('bulgu_atom', 'findings', 'cikti3', 'findings'),
  ];
  return wf('Biyoloji köprüsü', 'Lambda faj genomunda GATC (DpnI/MboI) ve GGATCC (BamHI) kesim bölgeleri: kod taramasıyla aynı atomlar', nodes, edges);
}

/**
 * Paket listesi. `cli`: aynı sonucu veren komut(lar) (vize/ klasöründen); `expected`:
 * beklenen bulgu sayısı her "Eşleşme → Bulgu" kutusu için.
 */
export const PACKAGES = [
  {
    id: 'teknik-borc', channel: 'teknik-borç-avı', build: teknikBorc,
    summary: 'Agora projesinin forum/ klasöründe bırakılmış TODO, FIXME, HACK ve XXX notlarını dosya:satır:sütun olarak listeler.',
    cli: ['node bin/ios.js scan --preset todo ../forum'],
    expected: { bulgu: 18 },
  },
  {
    id: 'gizli-bilgi', channel: 'gizli-bilgi-sızıntısı', build: gizliBilgi,
    summary: 'Sahte örnek dosyalarda parola, API anahtarı, AKIA… erişim anahtarı ve özel anahtar başlıklarını bulur; bulgu varsa kapı "kaldı" der (CI\'da çıkış kodu 1).',
    cli: ['node bin/ios.js scan --preset secrets --fail web/data/gizli'],
    expected: { bulgu: 7 },
  },
  {
    id: 'yasakli-api', channel: 'yasaklı-api', build: yasakliApi,
    summary: 'Agora kodunda eval(, exec(, innerHTML, pickle.loads, os.system( gibi güvenlik açısından riskli çağrıları bulur.',
    cli: ['node bin/ios.js scan --preset banned-api ../forum'],
    expected: { bulgu: 3 },
  },
  {
    id: 'log', channel: 'log-incelemesi', build: logIncelemesi,
    summary: 'Örnek uygulama logunda ERROR, Exception, Traceback ve timeout geçen yerleri toplar; iki desen kümesi tek moleküle bağlanır.',
    cli: ['node bin/ios.js scan --preset errors --patterns timeout web/data/ornek.log'],
    expected: { bulgu: 117 },
  },
  {
    id: 'tek-desen', channel: 'tek-desen-büyük-dosya', build: tekDesen,
    summary: 'Aynı 880 KB kaynak kod dosyasında tek desen ("return") ve 16 Python anahtar sözcüğü: molekül tek desende Horspool ailesinden bir atom, çok desende tek geçişli bir otomat seçer. ExactMatch kutusunu seçip karar kaydını okuyun, "Atomları yarıştır" ile ölçün.',
    cli: ['node bin/ios.js scan --patterns return bench/corpus/kod.txt', `node bin/ios.js scan --patterns ${KEYWORDS.join(',')} bench/corpus/kod.txt`],
    expected: { tek_bulgu: 882, cok_bulgu: 7715 },
  },
  {
    id: 'biyoloji', channel: 'biyoloji-köprüsü', build: biyoloji,
    summary: 'Lambda faj genomunda GATC ve GGATCC kesim bölgelerini arar; molekül ve tek başına bir atom aynı 121 eşleşmeyi verir. Kod taramasındaki atomların aynısı.',
    cli: ['node bin/ios.js run ExactMatch --patterns GATC,GGATCC < tests/data/lambda_NC_001416.fa', 'node bin/ios.js run Bm4DnaDsSearch --patterns GATC,GGATCC < tests/data/lambda_NC_001416.fa'],
    expected: { bulgu: 121, bulgu_atom: 121 },
  },
];

export function packageById(id) {
  return PACKAGES.find((p) => p.id === id) ?? null;
}
