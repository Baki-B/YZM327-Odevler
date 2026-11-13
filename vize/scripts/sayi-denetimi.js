// Sayı denetimi: belgelerde geçen her sayı bir kaynak dosyada bulunmalı.
// Kaynaklar: bench/results/*.md ve *.json (ölçümler), docs/mutasyon.md (mutasyon denetimi),
// hazır paketlerin beklenen sayıları (src/workflows/packages.js) ve bu betiğin çalıştırdığı
// `node --test` sayıları. Bunlarda bulunmayan sayılar yalnızca aşağıdaki SABİTLER listesinde
// gerekçesiyle yazılıysa kabul edilir (ödev metnindeki sabitler, yıllar, kod sabitleri...).
// Bir sayı, kaynaktaki bir değerin aynı ondalık basamağa yuvarlanmış hâliyle (ya da yüzde
// olarak 100 katıyla) eşleşirse "bulundu" sayılır.
// Kullanım (vize/ klasöründen): node scripts/sayi-denetimi.js   (bulunmayan varsa çıkış kodu 1)
import { readFileSync, readdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { PACKAGES } from '../src/workflows/packages.js';

const VIZE = new URL('../', import.meta.url);
const read = (p) => readFileSync(new URL(p, VIZE), 'utf8');

// ------------------------------------------------------------------ kaynak değerler
const values = new Set();
const add = (x) => {
  if (!Number.isFinite(x)) return;
  for (let d = 0; d <= 3; d++) {
    values.add(x.toFixed(d));
    values.add((x * 100).toFixed(d));
  }
};
const walk = (v) => {
  if (typeof v === 'number') add(v);
  else if (Array.isArray(v)) v.forEach(walk);
  else if (v && typeof v === 'object') Object.values(v).forEach(walk);
};
const NUM = /(?<![\w.])\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?/g;
const norm = (t) => t.replace(/[   ]/g, '').replace(',', '.');
const fromText = (text) => { for (const m of text.match(NUM) ?? []) add(Number(norm(m))); };

for (const f of readdirSync(new URL('bench/results/', VIZE))) {
  const text = read(`bench/results/${f}`);
  if (f.endsWith('.json')) walk(JSON.parse(text));
  fromText(text);
}
fromText(read('docs/mutasyon.md'));
for (const p of PACKAGES) walk(p.expected), walk(Object.values(p.expected).reduce((a, b) => a + b, 0));
const testCounts = {};
for (const f of readdirSync(new URL('tests/unit/', VIZE)).filter((x) => x.endsWith('.test.js'))) {
  const out = execSync(`node --test tests/unit/${f}`, { cwd: VIZE, encoding: 'utf8' });
  testCounts[f] = Number(out.match(/^# pass (\d+)/m)[1]);
}
const total = Object.values(testCounts).reduce((a, b) => a + b, 0);
walk(Object.values(testCounts));
add(total);
add(testCounts['contract.test.js'] + testCounts['atoms.test.js']);
add(testCounts['forbidden.test.js'] + testCounts['cli.test.js'] + testCounts['core.test.js']);

// ------------------------------------------------------------------ gerekçeli sabitler
const SABITLER = {
  // ödev metni ve sözleşme
  '2016': 'Allmer 2016', '1977': 'kaynak yılı', '1980': 'kaynak yılı', '1991': 'kaynak yılı', '1992': 'kaynak yılı', '1994': 'kaynak yılı', '1975': 'kaynak yılı', '1974': 'kaynak yılı', '1962': 'kaynak yılı', '2026': 'tarih',
  '6': 'ödev: en fazla 6 sayfa', '50': 'Allmer kuralı: m < 50', '32': 'Shift-Or kelime sınırı (m ≤ 32)',
  '22': 'Node 22+', '300': 'ödev: en az 300 rastgele vaka', '100': 'ödev: en az 100 doğrulama vakası / m üst sınırı 100',
  '10': '%10 içinde (ödev ölçütü) / 10⁴', '0.1': 'ödev SSS: 0,1 ms altı yorumlanmaz',
  // kod sabitleri
  '64': 'örneklem: 64 parça / ızgara m = 64', '256': 'örneklem: 256 karakter', '16384': '64 × 256', '262144': 'v3 örneklem sınırı 64 × 4096', '4096': 'v3 parça boyu',
  '16': 'q-gram özeti 16 bit / 16 özel durum / 16 Python anahtar sözcüğü', '2': 'Allmer kuralı ve genel', '3': 'genel', '5': 'tekrar sayısı', '7': 'yedi yeni atom', '8': 'sekiz atom', '9': 'molekül testi: 9 strateji',
  '12': 'mutasyon sayısı', '18': 'Kahn / bileşen', '120': 'vaka sayısı', '180': 'kalibrasyon vakası', '360': 'rastgele vaka',
  '8327': 'yerel sunucu bağlantı noktası', '390': 'telefon genişliği (px)', '1280': 'masaüstü genişliği (px)', '1060': 'site genişliği',
  '48502': 'lambda genomu uzunluğu (NCBI kaydı)', '126': 'E. coli protein sayısı', '34004': 'E. coli proteinlerinin toplam uzunluğu', '001416': 'NC_001416.1', '001416.1': 'NC_001416.1',
  '415': 'lambda: ilk GATC konumu (ios run çıktısı)', '881771': 'kod.txt uzunluğu (atölye karar kaydı)', '19.661': 'kod.txt σe (atölye karar kaydı)', '111': 'kod.txt σ', '880': 'kod.txt ~880 KB', '8597': '882 + 7715',
  '114': 'agora.json dosya sayısı (scripts/ornekler.js çıktısı)', '29': 'arayüz denetimi: 29 denetim', '2.10': 'işlemci 2,10 GHz', '2.30': 'işlemci 2,30 GHz', '23.4': 'Node v22.23.4', '6.18': 'Linux 6.18',
  '0.775': 'lambda explain tahmini (bm4DNADS)', '0.799': 'lambda explain tahmini (Horspool)', '0.812': 'lambda explain tahmini (Boyer-Moore)', '3.994': 'lambda explain σe',
  '233.9': 'kalibrasyon ızgarası süresi (calibrate çıktısı)', '3.31': 'ortak eşleşme maliyeti 3,31·10⁻⁷', '1440': '180 × 8',
  '12000': 'doğrulama n alt sınırı', '900000': 'doğrulama n üst sınırı', '30': 'karışık uzunluk oranı %30', '0.951': 'D molekül yükü medyanı',
  '83333': 'E. coli K-12 taksonomi kimliği (OX)', '200': 'tek ölçümlük', '4': 'genel', '1': 'genel', '0': 'genel', '20': 'genel', '13': 'genel', '15': 'genel',
};

// ------------------------------------------------------------------ denetlenen belgeler
const strip = (html) => html.replace(/<style[\s\S]*?<\/style>/g, '').replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ').replace(/&[a-z]+;/g, ' ');
const DOCS = [
  ['docs/rapor/rapor.html', true], ['README.md', false], ['docs/sunum.md', false], ['docs/kontrol.md', false], ['docs/anlatim.md', false], ['KARARLAR.md', false],
  ['docs/sunum/index.html', true], ...readdirSync(new URL('site/', VIZE)).filter((f) => f.endsWith('.html')).map((f) => [`site/${f}`, true]),
];
let bad = 0;
let checked = 0;
for (const [file, html] of DOCS) {
  let text = read(file);
  if (html) text = strip(text);
  // kod blokları, dosya adları, tohumlar ve komutlar sayı sayılmaz
  text = text.replace(/```[\s\S]*?```/g, ' ').replace(/`[^`]*`/g, ' ').replace(/[\w./-]*\.(?:js|json|md|html|svg|png|pdf|fa|fasta|tsv|puml|txt|log)\b/g, ' ')
    .replace(/https?:\S+/g, ' ').replace(/\b[vV]\d\b/g, ' ').replace(/\b(?:Ek|Şekil|Bölüm|bölüm|sayfa|Sıralı diyagram|Sınıf diyagramı)\s+\d+/g, ' ')
    .replace(/\b(?:İG|İOG|H|D|S|W)\d\b/g, ' ').replace(/(\d)\/(\d)/g, '$1 ; $2');
  const misses = [];
  for (const m of text.matchAll(NUM)) {
    const tok = norm(m[0]);
    checked++;
    if (values.has(tok) || values.has(String(Number(tok))) || SABITLER[tok] || SABITLER[String(Number(tok))]) continue;
    misses.push(`${m[0]}  …${text.slice(Math.max(0, m.index - 40), m.index + 30).replace(/\s+/g, ' ')}…`);
  }
  if (misses.length) {
    bad += misses.length;
    console.log(`\n${file}: ${misses.length} kaynaksız sayı`);
    for (const x of misses) console.log('  ' + x);
  }
}
// ------------------------------------------------------------------ hedefli iddialar
// Küçük tamsayılar pek çok dosyada geçtiği için varlık denetimi onları ayırt edemez; en önemli
// iddialar burada doğrudan hesaplanan değerle karşılaştırılır.
{
  const { evaluate, E2E } = await import('../tests/benchmarks/metrics.js');
  const mut = read('docs/mutasyon.md');
  const mutRows = mut.split('\n').filter((l) => /^\| \d+ \|/.test(l));
  const caught = mutRows.filter((l) => l.includes('| evet |')).length;
  const failCount = (n) => Number(mutRows.find((l) => l.startsWith(`| ${n} |`)).match(/(\d+) test başarısız/)?.[1]);
  const D = evaluate(JSON.parse(read('bench/results/validation-d.json')).cases);
  const E = evaluate(JSON.parse(read('bench/results/validation-e.json')).cases);
  const tr = (x, d) => x.toFixed(d).replace('.', ',');
  const rapor = strip(read('docs/rapor/rapor.html'));
  const readme = read('README.md');
  const claims = [
    ['rapor: bm4DNAHMbs mutasyonunda düşen test', rapor, `Mutasyonla sınandı: ${failCount(4)} test başarısız`],
    ['rapor: yakalanan mutasyon', rapor, `${caught}'si de yakalandı`],
    ['rapor: npm test toplamı', rapor, `${total}/${total} geçiyor`],
    ['README: test toplamı', readme, `${total} birim testi`],
    ['rapor: D seçilen geo. ort.', rapor, `geometrik ortalaması <b>${tr(D['ExactMatch (auto)'].geomeanSlowdown, 3)}</b>`.replace(/<\/?b>/g, '')],
    ['rapor: D uçtan uca geo. ort.', rapor, `geo. ort. ${tr(D[E2E].geomeanSlowdown, 3)}`],
    ['rapor: E seçilen geo. ort.', rapor, `seçilen atomla ${tr(E['ExactMatch (auto)'].geomeanSlowdown, 3)}`],
    ['rapor: E uçtan uca', rapor, `uçtan uca ${tr(E[E2E].geomeanSlowdown, 3)}`],
    ['README: D seçilen', readme, `**${tr(D['ExactMatch (auto)'].geomeanSlowdown, 3)}**`],
    ['README: D en hızlı oranı', readme, `%${tr(D['ExactMatch (auto)'].fastestRate * 100, 1)} en hızlı`],
  ];
  for (const [name, text, needle] of claims) {
    const norm2 = (t) => t.replace(/\s+/g, ' ');
    const ok = norm2(text).includes(norm2(needle));
    if (!ok) bad++;
    console.log(`${ok ? 'tutarlı ' : 'TUTARSIZ'} ${name}: "${needle}"`);
  }
}
console.log(`\nTest sayıları: ${JSON.stringify(testCounts)} (toplam ${total})`);
console.log(`${checked} sayı denetlendi; ${bad} tanesi kaynakta ya da gerekçeli sabitlerde bulunamadı.`);
process.exitCode = bad ? 1 : 0;
