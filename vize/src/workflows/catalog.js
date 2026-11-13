// Atölyenin bileşen kataloğu: iş akışı motorunun (engine.js) çalıştırdığı kutu türleri.
// DOM'suz ve G/Ç'siz: örnek veri ctx.loadSample(ad) ile dışarıdan (tarayıcıda fetch,
// Node'da dosya okuma) verilir. Algoritmalar kopyalanmaz; atomlar kayıt defterinden,
// molekül ExactMatch'ten, uyarlayıcılar src/adapters ve src/fasta.js'ten gelir.
//
// Uç türleri ve değerleri:
//   Source.File     [{ path, text }]                       kaynak dosyalar (kod, log, FASTA metni)
//   FASTA.Entry     [{ header, seq }]                      atomların girdisi
//   Pattern.Set     { patterns: [...], ignoreCase, label }  desen kümesi
//   Sequence.Match  { matches: [...], entries: [...] }      atomların çıktısı + hangi kayıtlarda bulunduğu
//   Finding         { findings: [{ file, line, column, pattern, position, length, preview }], files }

import { registry as defaultRegistry } from '../registry.js';
import { ExactMatch } from '../molecules/ExactMatch.js';
import { parseFasta } from '../fasta.js';
import { sourceToEntry, lineStarts, toLineColumn } from '../adapters/sourceToEntry.js';
import { PRESETS } from './presets.js';

export const TYPES = {
  'Source.File': 'Kaynak dosya(lar): yol + metin',
  'FASTA.Entry': 'FASTA kaydı: { header, seq }',
  'Pattern.Set': 'Desen kümesi: desenler + ignoreCase',
  'Sequence.Match': 'Eşleşmeler: { header, pattern, position, length }',
  Finding: 'Bulgu: dosya:satır:sütun + desen',
};

/** Örnek veriler. url'ler vize/ klasörüne göre göreli; "bundle" bir dosya listesi (JSON) demektir. */
export const SAMPLES = {
  agora: { title: 'Agora kodu (forum/)', kind: 'bundle', url: 'web/data/agora.json', note: 'Bu deponun Agora projesindeki forum/ klasörü (Python, JS, HTML)' },
  log: { title: 'Örnek uygulama logu', kind: 'file', url: 'web/data/ornek.log', path: 'ornek.log', note: 'bench/data.js log üreticisi (doğrulamadaki "log" alfabesi) + 3 örnek Traceback bloğu' },
  gizli: { title: 'Sahte gizli bilgi örneği', kind: 'bundle', url: 'web/data/gizli.json', note: 'Açıkça SAHTE değerler; gerçek anahtar içermez' },
  lambda: { title: 'Lambda faj genomu', kind: 'file', url: 'tests/data/lambda_NC_001416.fa', path: 'lambda_NC_001416.fa', note: 'NC_001416.1, 48 502 baz' },
  ecoli: { title: 'E. coli K-12 proteinleri', kind: 'file', url: 'tests/data/ecoli_k12_126_proteins.fasta', path: 'ecoli_k12_126_proteins.fasta', note: '126 UniProt kaydı' },
  korpus: { title: 'Kod korpusu (büyük tek dosya)', kind: 'file', url: 'bench/corpus/kod.txt', path: 'kod.txt', note: 'bench/corpus/kod.txt: Agora kaynaklarının birleşimi, ~880 KB' },
};

const files = (name = 'files', label = 'dosyalar') => ({ name, type: 'Source.File', label });

function mergePatternSets(sets) {
  const patterns = [];
  let ignoreCase = false;
  const labels = [];
  for (const s of sets) {
    patterns.push(...s.patterns);
    ignoreCase = ignoreCase || s.ignoreCase;
    labels.push(s.label);
  }
  if (patterns.length === 0) throw new Error('Desen kümesi boş.');
  return { patterns, ignoreCase, label: labels.join(' + ') };
}

function parsePatternList(text) {
  return String(text ?? '')
    .split('\n')
    .map((s) => s.replace(/\r$/, ''))
    .filter((s) => s !== '');
}

function countBy(items, key) {
  const m = new Map();
  for (const it of items) m.set(it[key], (m.get(it[key]) ?? 0) + 1);
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

/** Bir eşleşmeyi taşıyan satırın kısa önizlemesi (en fazla 160 karakter). */
function previewOf(text, starts, line, position, length) {
  const from = starts[line - 1];
  let to = line < starts.length ? starts[line] - 1 : text.length;
  if (to - from > 4000) to = from + 4000; // FASTA gibi tek satırlık dev kayıtlarda tümünü alma
  let a = from;
  let b = to;
  if (b - a > 160) {
    a = Math.max(from, position - 70);
    b = Math.min(to, position + length + 70);
  }
  const before = text.slice(a, position);
  const hit = text.slice(position, position + length);
  const after = text.slice(position + length, b);
  return { before: (a > from ? '…' : '') + before.replace(/^\s+/, a > from ? '' : ''), hit, after: after.replace(/\r$/, '') + (b < to ? '…' : '') };
}

function matchesToFindings(value) {
  const index = new Map();
  for (const e of value.entries) {
    if (!index.has(e.header)) index.set(e.header, { text: e.seq, starts: null, file: e.header.replace(/^>/, '') });
  }
  const findings = [];
  for (const m of value.matches) {
    const f = index.get(m.header);
    if (f.starts === null) f.starts = lineStarts(f.text);
    const { line, column } = toLineColumn(f.starts, m.position);
    findings.push({ file: f.file, line, column, pattern: m.pattern, position: m.position, length: m.length, preview: previewOf(f.text, f.starts, line, m.position, m.length) });
  }
  return { findings, files: index.size };
}

function atomComponent(Atom) {
  const m = Atom.manifest;
  return {
    type: `atom.${m.name}`,
    category: 'ATOMLAR',
    title: m.name,
    subtitle: m.title,
    icon: '◆',
    badge: m.references.length ? m.references.join('; ') : 'test referansı',
    manifest: m,
    auto: Boolean(Atom.selection),
    help: Atom.selection
      ? `IoS atomu (${m.task}). Molekül bu atomu "auto" kipinde aday sayar.`
      : `Test referansı (oracle): hazır indexOf kullanır, molekül "auto" kipinde seçmez.`,
    inputs: [{ name: 'entries', type: 'FASTA.Entry', label: 'kayıtlar' }, { name: 'patterns', type: 'Pattern.Set', label: 'desenler', multi: true }],
    outputs: [{ name: 'matches', type: 'Sequence.Match', label: 'eşleşmeler' }],
    params: [],
    describe: () => `${m.name} atomuyla (${m.title}) her kayıtta bütün desenleri arar.`,
    run(inputs, _params, ctx) {
      const set = mergePatternSets(inputs.patterns);
      const atom = new Atom({ patterns: set.patterns, ignoreCase: set.ignoreCase });
      const matches = [];
      for (const e of inputs.entries) for (const x of atom.process(e)) matches.push(x);
      ctx.info.summary = `${matches.length} eşleşme.`;
      ctx.info.count = matches.length;
      return { matches: { matches, entries: inputs.entries } };
    },
  };
}

/**
 * Kataloğu kurar. registry verilirse (ör. testte sahte bir atom eklenmiş kayıt defteri)
 * atom kutuları ve molekülün strateji listesi ondan gelir.
 */
export function createCatalog(registry = defaultRegistry) {
  const list = [];
  const add = (c) => list.push(c);

  // ---------------------------------------------------------------- KAYNAKLAR
  add({
    type: 'kaynak.kod', category: 'KAYNAKLAR', title: 'Kod yapıştır', icon: '⌨',
    help: 'Bir kaynak kod parçasını yapıştırın; dosya yolu bulgu tablosunda görünür.',
    inputs: [], outputs: [files()],
    params: [
      { key: 'path', label: 'Dosya yolu', kind: 'text', default: 'yapistirilan.js' },
      { key: 'text', label: 'Kod', kind: 'textarea', default: '' },
    ],
    describe: (p) => `"${p.path}" adlı ${String(p.text ?? '').length} karakterlik yapıştırılmış kodu kaynak dosya olarak verir.`,
    run(_i, p, ctx) {
      ctx.info.summary = `1 dosya, ${p.text.length} karakter.`;
      return { files: [{ path: p.path || 'yapistirilan.txt', text: String(p.text ?? '') }] };
    },
  });
  add({
    type: 'kaynak.dosyalar', category: 'KAYNAKLAR', title: 'Dosya yükle', icon: '⇪',
    help: 'Bilgisayarınızdan bir ya da birkaç metin dosyası seçin. Dosyalar tarayıcıdan çıkmaz.',
    inputs: [], outputs: [files()],
    params: [{ key: 'files', label: 'Dosyalar', kind: 'files', default: [] }],
    describe: (p) => `yüklenen ${(p.files ?? []).length} dosyayı kaynak olarak verir.`,
    run(_i, p, ctx) {
      const list = (p.files ?? []).map((f) => ({ path: String(f.path), text: String(f.text) }));
      if (list.length === 0) throw new Error('Henüz dosya yüklenmedi.');
      ctx.info.summary = `${list.length} dosya.`;
      return { files: list };
    },
  });
  add({
    type: 'kaynak.log', category: 'KAYNAKLAR', title: 'Log yapıştır', icon: '≣',
    help: 'Uygulama ya da sunucu logunu yapıştırın.',
    inputs: [], outputs: [files()],
    params: [
      { key: 'path', label: 'Dosya adı', kind: 'text', default: 'yapistirilan.log' },
      { key: 'text', label: 'Log', kind: 'textarea', default: '' },
    ],
    describe: (p) => `"${p.path}" adlı ${String(p.text ?? '').length} karakterlik logu kaynak dosya olarak verir.`,
    run(_i, p, ctx) {
      ctx.info.summary = `1 dosya, ${p.text.length} karakter.`;
      return { files: [{ path: p.path || 'yapistirilan.log', text: String(p.text ?? '') }] };
    },
  });
  add({
    type: 'kaynak.fasta', category: 'KAYNAKLAR', title: 'FASTA yapıştır / yükle', icon: '≋',
    help: 'FASTA metni (">" ile başlayan başlık satırları). Ardından "FASTA okuyucu" ile kayıtlara çevrilir.',
    inputs: [], outputs: [files()],
    params: [
      { key: 'path', label: 'Dosya adı', kind: 'text', default: 'girdi.fasta' },
      { key: 'text', label: 'FASTA', kind: 'textarea', default: '>ornek\nACGTACGTGATC\n', upload: true },
    ],
    describe: (p) => `"${p.path}" adlı FASTA metnini kaynak dosya olarak verir.`,
    run(_i, p, ctx) {
      ctx.info.summary = `1 dosya, ${p.text.length} karakter.`;
      return { files: [{ path: p.path || 'girdi.fasta', text: String(p.text ?? '') }] };
    },
  });
  add({
    type: 'kaynak.ornek', category: 'KAYNAKLAR', title: 'Örnek veri', icon: '★',
    help: 'Depodaki gerçek dosyalardan hazırlanmış örnekler.',
    inputs: [], outputs: [files()],
    params: [{ key: 'sample', label: 'Örnek', kind: 'select', default: 'agora', options: Object.entries(SAMPLES).map(([value, s]) => ({ value, label: s.title })) }],
    describe: (p) => `örnek veri olarak "${SAMPLES[p.sample]?.title ?? p.sample}" dosyalarını verir (${SAMPLES[p.sample]?.note ?? ''}).`,
    async run(_i, p, ctx) {
      if (!SAMPLES[p.sample]) throw new Error(`Bilinmeyen örnek: ${p.sample}`);
      if (typeof ctx.loadSample !== 'function') throw new Error('Örnek veri yükleyicisi verilmedi.');
      const list = await ctx.loadSample(p.sample);
      const chars = list.reduce((s, f) => s + f.text.length, 0);
      ctx.info.summary = `${list.length} dosya, ${chars} karakter.`;
      return { files: list };
    },
  });

  // ---------------------------------------------------------------- UYARLAYICILAR
  add({
    type: 'uyarlayici.kaynak', category: 'UYARLAYICILAR', title: 'Kaynak → FASTA.Entry', icon: '⇄',
    badge: 'sourceToEntry', help: 'Her dosyayı { header: ">yol", seq: içerik } kaydına çevirir (Adapter deseni). Boşluk ve satır sonları korunur.',
    inputs: [{ ...files(), multi: true }], outputs: [{ name: 'entries', type: 'FASTA.Entry', label: 'kayıtlar' }],
    params: [],
    describe: () => 'her dosyayı bir FASTA kaydına çevirir (başlık = dosya yolu, dizi = dosyanın tamamı).',
    run(inputs, _p, ctx) {
      const entries = inputs.files.flat().map(sourceToEntry);
      ctx.info.summary = `${entries.length} kayıt.`;
      return { entries };
    },
  });
  add({
    type: 'uyarlayici.fasta', category: 'UYARLAYICILAR', title: 'FASTA okuyucu', icon: '⇄',
    badge: 'parseFasta', help: 'FASTA metnini kayıtlara ayırır; dizideki boşluklar atılır.',
    inputs: [{ ...files(), multi: true }], outputs: [{ name: 'entries', type: 'FASTA.Entry', label: 'kayıtlar' }],
    params: [],
    describe: () => 'FASTA metnini başlık satırlarından kayıtlara ayırır.',
    run(inputs, _p, ctx) {
      const entries = inputs.files.flat().flatMap((f) => parseFasta(f.text));
      const total = entries.reduce((s, e) => s + e.seq.length, 0);
      ctx.info.summary = `${entries.length} kayıt, ${total} karakter.`;
      return { entries };
    },
  });
  add({
    type: 'uyarlayici.bulgu', category: 'UYARLAYICILAR', title: 'Eşleşme → Bulgu', icon: '⇄',
    badge: 'CodeScan', help: 'Konumu satır ve sütuna çevirir (satır başları ikili aramayla bulunur).',
    inputs: [{ name: 'matches', type: 'Sequence.Match', label: 'eşleşmeler' }], outputs: [{ name: 'findings', type: 'Finding', label: 'bulgular' }],
    params: [],
    describe: () => 'her eşleşmenin konumunu dosya:satır:sütun biçimine çevirir.',
    run(inputs, _p, ctx) {
      const value = matchesToFindings(inputs.matches);
      ctx.info.count = value.findings.length;
      ctx.info.summary = `${value.findings.length} bulgu.`;
      return { findings: value };
    },
  });

  // ---------------------------------------------------------------- DESEN KÜMELERİ
  const presetHelp = {
    todo: 'Kodda bırakılmış iş notları (teknik borç).',
    secrets: 'Koda gömülmüş gizli bilgi belirtileri; büyük/küçük harf duyarsız.',
    'banned-api': 'Güvenlik açısından riskli API çağrıları.',
    errors: 'Log dosyalarındaki hata satırları.',
  };
  for (const [name, preset] of Object.entries(PRESETS)) {
    add({
      type: `desen.${name}`, category: 'DESEN KÜMELERİ', title: name, icon: '#',
      badge: `${preset.patterns.length} desen${preset.ignoreCase ? ', ignoreCase' : ''}`,
      help: presetHelp[name] ?? '', inputs: [], outputs: [{ name: 'patterns', type: 'Pattern.Set', label: 'desenler' }],
      params: [], presetName: name,
      describe: () => `"${name}" hazır kümesini verir: ${preset.patterns.map((x) => `"${x}"`).join(', ')}${preset.ignoreCase ? ' (büyük/küçük harf duyarsız)' : ''}.`,
      run(_i, _p, ctx) {
        ctx.info.summary = `${preset.patterns.length} desen.`;
        return { patterns: { patterns: [...preset.patterns], ignoreCase: preset.ignoreCase, label: name } };
      },
    });
  }
  add({
    type: 'desen.ozel', category: 'DESEN KÜMELERİ', title: 'Özel desen listesi', icon: '#',
    help: 'Her satıra bir desen. Desenler olduğu gibi aranır (düzenli ifade değildir).',
    inputs: [], outputs: [{ name: 'patterns', type: 'Pattern.Set', label: 'desenler' }],
    params: [
      { key: 'patterns', label: 'Desenler (her satıra bir tane)', kind: 'textarea', default: 'TODO' },
      { key: 'ignoreCase', label: 'Büyük/küçük harf duyarsız (yalnızca ASCII)', kind: 'bool', default: false },
    ],
    describe: (p) => {
      const list = parsePatternList(p.patterns);
      return `${list.length} özel desen verir: ${list.slice(0, 6).map((x) => `"${x}"`).join(', ')}${list.length > 6 ? ', …' : ''}${p.ignoreCase ? ' (büyük/küçük harf duyarsız)' : ''}.`;
    },
    run(_i, p, ctx) {
      const list = parsePatternList(p.patterns);
      if (list.length === 0) throw new Error('En az bir desen yazın.');
      ctx.info.summary = `${list.length} desen.`;
      return { patterns: { patterns: list, ignoreCase: Boolean(p.ignoreCase), label: 'özel' } };
    },
  });

  // ---------------------------------------------------------------- ATOMLAR
  const atomNames = registry.names();
  for (const name of atomNames) add(atomComponent(registry.get(name)));

  // ---------------------------------------------------------------- MOLEKÜL
  add({
    type: 'molekul.ExactMatch', category: 'MOLEKÜL', title: 'ExactMatch', subtitle: 'Exact match (auto-selecting molecule)', icon: '⬢',
    badge: 'maliyet modeli', manifest: ExactMatch.manifest,
    help: 'İlk kaydın şekline bakar, her atomun süresini kalibre edilmiş maliyet modeliyle tahmin eder ve en ucuzunu seçer.',
    inputs: [{ name: 'entries', type: 'FASTA.Entry', label: 'kayıtlar' }, { name: 'patterns', type: 'Pattern.Set', label: 'desenler', multi: true }],
    outputs: [{ name: 'matches', type: 'Sequence.Match', label: 'eşleşmeler' }],
    params: [{ key: 'strategy', label: 'Strateji', kind: 'select', default: 'auto', options: [{ value: 'auto', label: 'auto (molekül seçer)' }, ...atomNames.map((n) => ({ value: n, label: n }))] }],
    describe: (p) => p.strategy === 'auto'
      ? 'ilk kaydın şekline (n, σ, k, desen uzunlukları) bakıp en ucuz atomu seçer ve bütün kayıtlarda onunla arar.'
      : `molekülü "${p.strategy}" stratejisine zorlar; yine de modelin ne seçeceği karar kaydına yazılır.`,
    run(inputs, p, ctx) {
      const set = mergePatternSets(inputs.patterns);
      const em = new ExactMatch({ patterns: set.patterns, ignoreCase: set.ignoreCase, strategy: p.strategy ?? 'auto' }, { registry });
      const t0 = ctx.now ? ctx.now() : 0;
      const matches = [];
      for (const x of em.run(inputs.entries)) matches.push(x);
      ctx.info.record = em.record;
      ctx.info.count = matches.length;
      ctx.info.searchMs = ctx.now ? ctx.now() - t0 : null;
      ctx.info.summary = `${matches.length} eşleşme; seçilen atom ${em.record.selected}.`;
      return { matches: { matches, entries: inputs.entries } };
    },
  });

  // ---------------------------------------------------------------- ÇIKTILAR
  const findingIn = [{ name: 'findings', type: 'Finding', label: 'bulgular' }];
  add({
    type: 'cikti.tablo', category: 'ÇIKTILAR', title: 'Bulgu tablosu', icon: '▤',
    help: 'dosya:satır:sütun, desen ve satır önizlemesi (eşleşen kısım vurgulu).',
    inputs: findingIn, outputs: [], params: [],
    describe: () => 'bulguları dosya:satır:sütun ve satır önizlemesiyle tablo olarak gösterir.',
    run(inputs, _p, ctx) {
      ctx.info.findings = inputs.findings.findings;
      ctx.info.summary = `${inputs.findings.findings.length} satır.`;
      return {};
    },
  });
  add({
    type: 'cikti.ozet', category: 'ÇIKTILAR', title: 'Özet sayaçlar', icon: 'Σ',
    help: 'Toplam bulgu, desene ve dosyaya göre sayılar.',
    inputs: findingIn, outputs: [], params: [],
    describe: () => 'toplam bulguyu, desene ve dosyaya göre sayıları çıkarır.',
    run(inputs, _p, ctx) {
      const list = inputs.findings.findings;
      ctx.info.total = list.length;
      ctx.info.files = inputs.findings.files;
      ctx.info.byPattern = countBy(list, 'pattern');
      ctx.info.byFile = countBy(list, 'file').slice(0, 20);
      ctx.info.summary = `${list.length} bulgu, ${new Set(list.map((f) => f.file)).size} dosyada.`;
      return {};
    },
  });
  add({
    type: 'cikti.jsonl', category: 'ÇIKTILAR', title: 'JSONL indir', icon: '⤓',
    help: 'Satır başına bir bulgu; biçim `ios scan --json` ile aynı.',
    inputs: findingIn, outputs: [], params: [{ key: 'filename', label: 'Dosya adı', kind: 'text', default: 'bulgular.jsonl' }],
    describe: (p) => `bulguları "${p.filename}" adlı JSONL dosyası olarak indirmeye hazırlar (ios scan --json biçimi).`,
    run(inputs, p, ctx) {
      const lines = inputs.findings.findings.map((f) => JSON.stringify({ file: f.file, line: f.line, column: f.column, pattern: f.pattern, position: f.position }));
      ctx.info.jsonl = lines.length ? lines.join('\n') + '\n' : '';
      ctx.info.filename = p.filename || 'bulgular.jsonl';
      ctx.info.summary = `${lines.length} satır hazır.`;
      return {};
    },
  });
  add({
    type: 'cikti.kapi', category: 'ÇIKTILAR', title: 'Bulgu varsa başarısız', icon: '⛔',
    badge: 'CI kapısı',
    help: 'Sürekli entegrasyon (CI) mantığı: en az bir bulgu varsa iş akışı "kaldı" sayılır (ios scan --fail → çıkış kodu 1).',
    inputs: findingIn, outputs: [], params: [],
    describe: () => 'bulgu varsa kapıyı kapatır: sürekli entegrasyonda derleme durur (ios scan --fail ile aynı kural).',
    run(inputs, _p, ctx) {
      const count = inputs.findings.findings.length;
      ctx.info.gate = count > 0 ? 'kaldı' : 'geçti';
      ctx.info.count = count;
      ctx.info.summary = count > 0 ? `KALDI: ${count} bulgu (çıkış kodu 1).` : 'GEÇTİ: bulgu yok (çıkış kodu 0).';
      return {};
    },
  });

  const map = new Map(list.map((c) => [c.type, c]));
  map.categories = ['KAYNAKLAR', 'UYARLAYICILAR', 'DESEN KÜMELERİ', 'ATOMLAR', 'MOLEKÜL', 'ÇIKTILAR'];
  return map;
}

export { mergePatternSets, parsePatternList, matchesToFindings };
