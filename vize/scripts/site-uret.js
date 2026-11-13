// Proje sitesini (site/) ve sunum slaytlarını (docs/sunum/index.html) ölçüm dosyalarından üretir: bütün sayılar bench/results/*.json'dan
// okunur, elle yazılmaz. Sayfalar statik ve bağımlılıksızdır; göreli yollarla çalışır.
//   site/index.html, bilesenler.html, bilesen/<Ad>.html, sonuclar.html, rapor.html, ekip.html
// Kullanım (vize/ klasöründen): node scripts/site-uret.js
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { registry } from '../src/registry.js';
import { ExactMatch } from '../src/molecules/ExactMatch.js';
import coefficients from '../src/molecules/coefficients.js';
import { evaluate, E2E } from '../tests/benchmarks/metrics.js';
import { PACKAGES } from '../src/workflows/packages.js';

const VIZE = new URL('../', import.meta.url);
const RES = new URL('bench/results/', VIZE);
const SITE = new URL('site/', VIZE);
mkdirSync(new URL('bilesen/', SITE), { recursive: true });
const load = (name) => JSON.parse(readFileSync(new URL(`${name}.json`, RES), 'utf8'));

// ------------------------------------------------------------------ biçim
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const dec = (x, d) => x.toFixed(d).replace('.', ',');
const pct = (x) => `%${dec(x * 100, 1)}`;
const f3 = (x) => dec(x, 3);
const wx = (x) => `${dec(x, 2)}×`;
const int = (x) => String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const ms = (x) => (x < 1 ? dec(x, 3) : dec(x, 2));

const LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#fff" opacity=".16"/><path d="M9 11h6M9 16h10M9 21h6" stroke="#f2c14e" stroke-width="3" stroke-linecap="round"/><circle cx="23" cy="21" r="3" fill="#36c2b4"/></svg>';
const NAV = [['index.html', 'Ana sayfa'], ['../web/index.html', 'Atölye'], ['bilesenler.html', 'Bileşenler'], ['sonuclar.html', 'Sonuçlar'], ['rapor.html', 'Rapor'], ['ekip.html', 'Ekip']];

function page(file, title, body, { depth = 0, description = '' } = {}) {
  const up = '../'.repeat(depth);
  const nav = NAV.map(([href, label]) => `<a href="${href.startsWith('../') ? up + href : up + href}"${href === file ? ' aria-current="page"' : ''}>${label}</a>`).join('');
  return `<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description || 'Akıllı tam desen eşleştirme: IoS atomları, seçici molekül ve yazılım mühendisliği için Kod Bilimi Atölyesi.')}">
<link rel="stylesheet" href="${up}site.css">
</head>
<body>
<header class="top"><div class="in"><a class="brand" href="${up}index.html">${LOGO}<span>Kod Bilimi Atölyesi</span></a><nav aria-label="Site">${nav}</nav></div></header>
<main>
${body}
</main>
<footer class="foot"><div class="in"><span>IoS atom/molekül sözleşmesine uygun bileşenler · <code>sequence.pattern-match.exact</code></span><span>Sayılar <code>bench/results/</code> dosyalarından üretildi (<code>node scripts/site-uret.js</code>).</span></div></footer>
</body>
</html>
`;
}

function table(headers, rows, { cls = () => '' } = {}) {
  const th = headers.map((h) => `<th${h.n ? ' class="n"' : ''}>${h.t ?? h}</th>`).join('');
  const tr = rows.map((r, i) => `<tr${cls(r, i) ? ` class="${cls(r, i)}"` : ''}>${r.cells.map((c, j) => `<td${headers[j].n ? ' class="n"' : ''}>${c}</td>`).join('')}</tr>`).join('\n');
  return `<div class="table-wrap"><table><thead><tr>${th}</tr></thead><tbody>\n${tr}\n</tbody></table></div>`;
}

// ------------------------------------------------------------------ veri
const SETS = {
  A1: { file: 'validation-v1', label: 'A', model: 'v1' },
  A2: { file: 'validation-v2', label: 'A', model: 'v2' },
  A3: { file: 'validation', label: 'A', model: 'v3' },
  B: { file: 'validation-taze', label: 'B (taze)', model: 'v3' },
  C: { file: 'validation-tek', label: 'C (k = 1)', model: 'v3' },
  D: { file: 'validation-d', label: 'D (taze)', model: 'v4' },
  E: { file: 'validation-e', label: 'E (taze, k = 1)', model: 'v4' },
};
for (const s of Object.values(SETS)) {
  s.data = load(s.file);
  s.m = evaluate(s.data.cases);
}
const D = SETS.D.m, E = SETS.E.m;
const AUTO = 'ExactMatch (auto)';
const karar = load('karar-yuku-v4');
const calib = load('calibration');
const q = (xs, p) => [...xs].sort((a, b) => a - b)[Math.min(xs.length - 1, Math.floor(xs.length * p))];
const kararStats = (rows) => ({
  shapeV3: q(rows.map((r) => r.shapeV3Ms), 0.5), shapeV4: q(rows.map((r) => r.shapeV4Ms), 0.5),
  decision: q(rows.map((r) => r.decisionMs), 0.5), ratio: q(rows.map((r) => r.decisionMs / r.atomMs), 0.5), ratio90: q(rows.map((r) => r.decisionMs / r.atomMs), 0.9),
});
const KD = kararStats(karar.sets.D), KE = kararStats(karar.sets.E);
const overheadD = SETS.D.data.moleculeOverhead.median;

function bestSingle(m) {
  return Object.entries(m).filter(([k]) => k.startsWith('her zaman')).sort((a, b) => a[1].geomeanSlowdown - b[1].geomeanSlowdown)[0];
}
const bestD = bestSingle(D), bestE = bestSingle(E);
const shortName = (s) => s.replace('her zaman ', 'hep ').replace('Search', '');

function policyTable(m) {
  const rows = Object.entries(m).sort((a, b) => a[1].geomeanSlowdown - b[1].geomeanSlowdown)
    .map(([label, x]) => ({ label, cells: [esc(label.replace('Search', '')), pct(x.fastestRate), pct(x.within10Rate), f3(x.geomeanSlowdown), wx(x.worstSlowdown), f3(x.totalRatio)] }));
  return table(['Politika', { t: 'En hızlıyı seçme', n: 1 }, { t: '%10 içinde', n: 1 }, { t: 'Yavaşlama (geo. ort.)', n: 1 }, { t: 'En kötü', n: 1 }, { t: 'Toplam / en iyi', n: 1 }], rows,
    { cls: (r) => (r.label === AUTO ? 'hl' : r.label === E2E ? 'e2e' : '') });
}

// Atomların kazandığı / seçildiği vaka sayıları
function counts(data) {
  const best = {}, picked = {};
  for (const c of data.cases) {
    best[c.best] = (best[c.best] ?? 0) + 1;
    picked[c.selected] = (picked[c.selected] ?? 0) + 1;
  }
  return { best, picked };
}
const cD = counts(SETS.D.data), cE = counts(SETS.E.data);
const calWins = {};
for (const c of calib.cases) {
  const w = Object.entries(c.times).reduce((a, b) => (b[1].ms < a[1].ms ? b : a))[0];
  calWins[w] = (calWins[w] ?? 0) + 1;
}

// ------------------------------------------------------------------ bileşen bilgileri (yayın biçimi)
const INFO = {
  HorspoolSearch: { group: 'A', idea: 'Pencerenin son karakterine bakar; bu karakter desenin ilk m−1 karakterinde en sağda nerede geçiyorsa pencereyi o hizaya kaydırır, hiç geçmiyorsa m kadar.', cx: 'Ön işleme O(m + σ); arama tipik O(n/m), en kötü O(n·m).', dev: 'Sapma yok; çok desende her benzersiz desen için ayrı geçer.', good: 'Tek desen, büyük alfabe (protein, kaynak kod).', limit: 'Küçük alfabede (DNA, ikili) kayma kısa kalır.' },
  BoyerMooreSearch: { group: 'hazır örnek', idea: 'Kötü karakter ve iyi sonek kurallarından büyük olanı kadar kayar.', cx: 'Ön işleme O(m + σ); arama tipik alt doğrusal, en kötü O(n·m).', dev: 'Başlangıç paketinin karşılığı olarak yeniden yazıldı (paket verilmedi).', good: 'Periyodik desenlerde Horspool\'dan güvenli.', limit: 'Tablo kurmak pahalı; bu uygulamada doğrulamada hiç en hızlı olmadı.' },
  ShiftOrSearch: { group: 'A', idea: 'Bit paralel: 32 bitlik bir sayının her biti desenin bir konumunu izler; her karakterde D = (D << 1) | maske[c].', cx: 'Ön işleme O(m + σ); arama O(n), m ≤ 32.', dev: 'm > 32 iken ilk 32 karakterle süzüp kalanını doğrular; applicable() "uygun değil" der, molekül seçmez.', good: 'Kısa desen, küçük alfabe (ikili alfabe).', limit: 'Her karakteri okur; atlama yapmaz.' },
  KmpSearch: { group: 'B', idea: 'Başarısızlık işleviyle metinde hiç geri dönmeden ilerler.', cx: 'Ön işleme O(m); arama O(n) (en kötü durumda da).', dev: 'Sapma yok.', good: 'Akış dostu, en kötü durum garantili.', limit: 'Ortalamada Horspool ailesinden yavaş; doğrulamada hiç en hızlı olmadı.' },
  AhoCorasickSearch: { group: 'C', idea: 'Bütün desenlerden tam bir otomat kurar; metni tek geçişte okur, sözlük bağlarıyla iç içe desenleri de bulur.', cx: 'Ön işleme O(Σm · σ); arama O(n + z).', dev: 'Tam otomat (DFA). Tablo 3·10⁷ hücreyi aşarsa applicable() "uygun değil" der.', good: 'Çok desen, kısa desenler.', limit: 'Tablo büyüdükçe önbellek dışına taşar; bellek modelde yok.' },
  WuManberSearch: { group: 'C', idea: 'Çok desenli Horspool: pencerenin son B karakterlik bloğuna göre kayar; kayma 0 ise kovadaki desenleri doğrular.', cx: 'Ön işleme O(Σm + tablo); arama tipik O(n·B / kayma).', dev: 'Tablo boyu desen bloklarının ~8 katı (2⁸–2¹⁸); çakışmada en küçük kayma tutulur.', good: 'Çok desen, desenler çok kısa değilse.', limit: 'En kısa desen 3–5 karakterken blok kayması küçülür.' },
  Bm4DnaDsSearch: { group: 'A', idea: 'Horspool + metnin sonuna desen kopyası (sentinel) + üç kez açılmış atlama döngüsü; son karakterin kayması 0.', cx: 'Ön işleme O(m + σ); arama tipik O(n/m).', dev: 'Sentinel\'de durunca j ≥ n denetimi; shift2 ilk m−1 karakterden (Allmer 2016 PDF\'ine erişilemedi, docs/sapmalar.md).', good: 'Tek desen, kısa-orta desen.', limit: 'Çok desende her desen için ayrı geçer.' },
  Bm4DnaHmbsSearch: { group: 'A', idea: 'Son q karakterin bit kaydırmalı özetiyle (q-gram) kayar; DNA\'da tek karakterden çok daha uzun kayar.', cx: 'Ön işleme O(m); arama tipik O(n·q / (m − q + 1)).', dev: 'Desende geçmeyen q-gram için güvenli kayma m − q + 1 (m değil); DNA için 3 bit, q = 5.', good: 'Uzun desen, küçük alfabe.', limit: 'JavaScript\'te her pencere için q okuma; doğrulamada Wu-Manber çoğunlukla daha ucuz.' },
};

function componentPage(Atom) {
  const m = Atom.manifest;
  const info = INFO[m.name];
  const feats = Object.keys(Atom.selection.features({ n: 1e5, sigma: 4, sigmaEff: 4, k: 4, mMin: 8, mMax: 8, mMean: 8 }));
  const coef = coefficients.atoms[m.name] ?? {};
  const body = `
<p class="small"><a href="../bilesenler.html">← Bileşenler</a></p>
<h1>${esc(m.title)}</h1>
<p><span class="badge">${m.name}</span><span class="badge">kind: ${m.kind}</span><span class="badge">task: ${m.task}</span><span class="badge">v${m.version}</span><span class="badge">grup ${info.group}</span></p>
<h2>1. Ne yapar ve neden</h2>
<p>${esc(info.idea)} İyi olduğu yer: ${esc(info.good)}</p>
<h2>2. Algoritma</h2>
<p>${esc(info.cx)}</p><p><b>Sapmalar:</b> ${esc(info.dev)}</p><p>Kaynak: ${esc(m.references.join('; '))}. Kod: <code>src/functions/</code> (çekirdek), <code>src/atomic/${m.name}.js</code> (atom).</p>
<h2>3. Girdi ve çıktılar</h2>
<p>Girdi <code>FASTA.Entry</code> akışı <code>{ header, seq }</code>; parametreler <code>{ patterns, ignoreCase }</code>; çıktı her eşleşme için <code>Sequence.Match</code> <code>{ header, pattern, position, length }</code>. Konumlar 0 tabanlı UTF-16; örtüşen eşleşmeler raporlanır; sıra konum, sonra desenin listedeki sırası.</p>
<h2>4. Seçim özellikleri</h2>
<p>Molekül bu atomun süresini şu özelliklerin kalibre edilmiş katsayılarla ağırlıklı toplamıyla tahmin eder (model ${esc(coefficients.model ?? 'v3')}, <code>src/molecules/coefficients.json</code>):</p>
<dl class="kv">${feats.map((f) => `<dt>${f}</dt><dd>${coef[f] !== undefined ? coef[f].toExponential(2).replace('.', ',') + ' s' : '—'}</dd>`).join('')}</dl>
${Atom.selection.applicable ? '<p>Atom ayrıca <code>applicable(shape)</code> ile kendini uygun değil ilan edebilir; molekül o durumda seçmez ve nedeni karar kaydına yazar.</p>' : ''}
<h2>5. Nasıl test edildi</h2>
<p>Sözleşme testleri, 16 özel durum (her biri ignoreCase açık ve kapalı), NaiveSearch ile eleman eleman karşılaştırma: lambda genomu, 126 E. coli proteini, 6 sentetik alfabe, 360 tohumlu rastgele vaka (<code>tests/unit/</code>). Yasaklı işlev taraması ve mutasyon denetimi (<code>docs/mutasyon.md</code>).</p>
<h2>6. Sonuçlar</h2>
${table(['Küme', { t: 'En hızlı olduğu vaka', n: 1 }, { t: 'Molekülün seçtiği vaka', n: 1 }], [
    { cells: [`kalibrasyon ızgarası (${calib.cases.length} vaka)`, String(calWins[m.name] ?? 0), '—'] },
    { cells: [`D, çok desen (${SETS.D.data.cases.length} vaka, v4)`, String(cD.best[m.name] ?? 0), String(cD.picked[m.name] ?? 0)] },
    { cells: [`E, tek desen (${SETS.E.data.cases.length} vaka, v4)`, String(cE.best[m.name] ?? 0), String(cE.picked[m.name] ?? 0)] },
  ])}
<p>Hep bu atomu kullanmak (D): yavaşlama geo. ort. ${f3(D[`her zaman ${m.name}`].geomeanSlowdown)}, en kötü ${wx(D[`her zaman ${m.name}`].worstSlowdown)}. E: ${f3(E[`her zaman ${m.name}`].geomeanSlowdown)}, en kötü ${wx(E[`her zaman ${m.name}`].worstSlowdown)}.</p>
<h2>7. Sınırlar</h2>
<p>${esc(info.limit)}</p>
<h2>8. Nasıl kullanılır</h2>
<pre>node bin/ios.js run ${m.name} --patterns GATC,GGATCC &lt; tests/data/lambda_NC_001416.fa</pre>
<p>Atölyede: <a href="../../web/index.html">sol panel → ATOMLAR → ${m.name}</a>.</p>`;
  return page(`bilesen/${m.name}.html`, `${m.name} · Kod Bilimi Atölyesi`, body, { depth: 1, description: m.title });
}

function moleculePage() {
  const m = ExactMatch.manifest;
  const body = `
<p class="small"><a href="../bilesenler.html">← Bileşenler</a></p>
<h1>${esc(m.title)}</h1>
<p><span class="badge">${m.name}</span><span class="badge">kind: ${m.kind}</span><span class="badge">task: ${m.task}</span><span class="badge">model ${esc(coefficients.model)}</span></p>
<h2>1. Ne yapar ve neden</h2>
<p>Hiçbir arama algoritması her durumda en hızlı değil. Molekül ilk kaydın şekline (n, σ, σe, k, mMin, mMax, mMean) bakar, kayıt defterindeki her atomun süresini kalibre edilmiş bir maliyet modeliyle tahmin eder ve en ucuzunu seçer. Bütün akış aynı atomla işlenir.</p>
<h2>2. Yöntem</h2>
<p>Tahmini süre = Σ katsayı × özellik. Özellikleri her atom kendisi verir (<code>selection.features</code>); katsayılar ${calib.cases.length} vakalık kalibrasyon ızgarasında negatif olmayan en küçük kareler (göreli hata) ile bulunur. Yeni atom eklemek molekülü değiştirmez (<code>src/registry.js</code>).</p>
<p>v4 değişikliği: 16 384 karakterden uzun metinde σ ve σe, eşit aralıklı 64 parça × 256 karakterden sayılır (v3'te 64 × 4096, 262 144 karaktere kadar tam sayım). Şekil hesabı D kümesinde medyanda ${ms(KD.shapeV3)} ms'den ${ms(KD.shapeV4)} ms'ye indi.</p>
<h2>3. Girdi, çıktı, parametreler</h2>
<p>Atomlarla aynı; ek olarak <code>strategy</code>: <code>"auto"</code> ya da bir atomun adı (bilinmeyen ad geçerli seçenekleri listeleyen bir hata verir). <code>record = { requested, selected, shape, estimates, why }</code>.</p>
<h2>4–6. Doğrulama (v4)</h2>
${policyTable(D)}
<p class="small">D: ${SETS.D.data.cases.length} vaka, tohum ${SETS.D.data.seed}. Tam tablolar <a href="../sonuclar.html">Sonuçlar</a> sayfasında.</p>
<h2>7. Sınırlar</h2>
<p>Karar ilk kayda göre verilir; özellikler tekdüze rastgele metin varsayar; tek desende ve ikili alfabede seçim zayıf (E: geo. ort. ${f3(E[AUTO].geomeanSlowdown)}, en kötü ${wx(E[AUTO].worstSlowdown)}).</p>
<h2>8. Nasıl kullanılır</h2>
<pre>node bin/ios.js explain --patterns GATC,GGATCC &lt; tests/data/lambda_NC_001416.fa</pre>`;
  return page('bilesen/ExactMatch.html', `ExactMatch · Kod Bilimi Atölyesi`, body, { depth: 1, description: m.title });
}

// ------------------------------------------------------------------ sayfalar
const atoms = registry.candidates();
for (const A of atoms) writeFileSync(new URL(`bilesen/${A.manifest.name}.html`, SITE), componentPage(A));
writeFileSync(new URL('bilesen/ExactMatch.html', SITE), moleculePage());

const kpi = (v, label) => `<div class="kpi"><b>${v}</b><span>${label}</span></div>`;
const index = `
<h1>Kaynak kodda, logda ve genomda: doğru aramayı kendisi seçen bir molekül</h1>
<p class="lead">Bir metinde bir ya da çok desenin geçtiği bütün yerleri bulan sekiz atom ve girdinin şekline bakıp aralarından en hızlısını seçen bir molekül. Internet of Science (IoS) fikrini biyolojiden yazılım mühendisliğine taşıdık: aynı bileşenler kaynak kodda teknik borç, gizli bilgi ve riskli API arar, logda hata satırlarını toplar.</p>
<div class="cta"><a class="btn primary" href="../web/index.html">Atölyeyi aç</a><a class="btn" href="../docs/rapor/Rapor.pdf">Rapor (PDF)</a><a class="btn" href="../docs/sunum/index.html">Sunum</a><a class="btn" href="sonuclar.html">Sonuçlar</a></div>
<figure><img src="../docs/ekran/atolye-masaustu.png" alt="Kod Bilimi Atölyesi: solda bileşenler ve hazır paketler, ortada bağlanmış kutular, sağda molekülün karar kaydı" width="2560" height="1600"><figcaption>Kod Bilimi Atölyesi: aynı 880 KB dosyada tek desen ve 16 desen. Sağda molekülün karar kaydı: veri şekli, her atomun tahmini süresi, seçilen atom.</figcaption></figure>
<h2>Problem</h2>
<p>Desen aramanın onlarca algoritması var ve hiçbiri her durumda en hızlı değil: kısa desende iyi olan uzun desende, tek desende iyi olan çok desende geri kalır. Kaynak kodda doğru seçim DNA'dakinden farklıdır, çünkü kodda 100'den fazla farklı karakter olsa da boşluk ve sık harfler yüzünden "etkin" alfabe küçüktür.</p>
<h2>Ne yaptık</h2>
<div class="grid">
<a class="card" href="bilesenler.html"><h3>8 atom + 1 molekül</h3><p>Horspool, Shift-Or, bm4DNADS, bm4DNAHMbs, KMP, Aho-Corasick, Wu-Manber ve Boyer-Moore; ExactMatch molekülü kalibre edilmiş maliyet modeliyle seçer.</p></a>
<a class="card" href="../web/index.html"><h3>Kod Bilimi Atölyesi</h3><p>Tarayıcıda çalışan iş akışı düzenleyicisi: kutuları sürükle, türlü uçları bağla, çalıştır. ${PACKAGES.length} hazır paket: teknik borç, gizli bilgi, riskli API, log, büyük dosya, biyoloji köprüsü.</p></a>
<a class="card" href="sonuclar.html"><h3>Ölçülmüş kanıt</h3><p>${calib.cases.length} vakalık kalibrasyon; hiçbir karar için kullanılmamış taze kümelerde doğrulama; atölye ile komut satırı aynı sonucu verir.</p></a>
</div>
<h2>Ana sonuç (model v4, taze kümeler)</h2>
<div class="result">
<p><b>Çok desen (D, ${SETS.D.data.cases.length} vaka).</b> En hızlı atomu seçme oranı ${pct(D[AUTO].fastestRate)}; seçilen atomla yavaşlamanın geometrik ortalaması ${f3(D[AUTO].geomeanSlowdown)}, en kötü ${wx(D[AUTO].worstSlowdown)}. Karar süresi dahil uçtan uca: ${f3(D[E2E].geomeanSlowdown)}, en kötü ${wx(D[E2E].worstSlowdown)}. En iyi tek atom (${shortName(bestD[0])}) ${f3(bestD[1].geomeanSlowdown)} ve ${wx(bestD[1].worstSlowdown)}; Allmer 2016 kuralı ${f3(D['Allmer 2016 kuralı'].geomeanSlowdown)} ve ${wx(D['Allmer 2016 kuralı'].worstSlowdown)}.</p>
<p><b>Tek desen (E, ${SETS.E.data.cases.length} vaka).</b> Seçilen atomla geo. ort. ${f3(E[AUTO].geomeanSlowdown)}, en kötü ${wx(E[AUTO].worstSlowdown)}; Allmer kuralı ${f3(E['Allmer 2016 kuralı'].geomeanSlowdown)}, en iyi tek atom (${shortName(bestE[0])}) ${f3(bestE[1].geomeanSlowdown)}. Uçtan uca ${f3(E[E2E].geomeanSlowdown)}: tek desende karar yükü hâlâ görünür ve molekül uçtan uca bu iki politikanın gerisinde kalıyor.</p>
</div>
<div class="kpis">${kpi(pct(D[AUTO].fastestRate), 'D: en hızlıyı seçme')}${kpi(f3(D[AUTO].geomeanSlowdown), 'D: yavaşlama (seçilen atom)')}${kpi(f3(D[E2E].geomeanSlowdown), 'D: yavaşlama (uçtan uca)')}${kpi(`${ms(KD.shapeV3)} → ${ms(KD.shapeV4)} ms`, 'şekil hesabı, medyan (v3 → v4)')}</div>
<p class="small">Uçtan uca oran D'de 1'in altına düştü: molekül, seçtiği atomun tek başına süresinden medyanda kısa ölçüldü (oran ${f3(overheadD)}). Bu fiziksel olarak mümkün değil; ölçüm düzeneğinin sapmasıdır. Karar süresi ayrıca doğrudan ölçüldü: karar süresi / seçilen atomun süresi medyanda ${pct(KD.ratio)} (D) ve ${pct(KE.ratio)} (E). Ayrıntı: <a href="sonuclar.html">Sonuçlar</a>.</p>`;
writeFileSync(new URL('index.html', SITE), page('index.html', 'Kod Bilimi Atölyesi · Akıllı tam desen eşleştirme', index));

const bilesenler = `
<h1>Bileşenler</h1>
<p class="lead">Her atom IoS atom sözleşmesine uyar: aynı girdi (<code>FASTA.Entry</code>), aynı çıktı (<code>Sequence.Match</code>), <code>manifest</code> ve <code>selection</code> alanları. Her biri için bileşen yayını biçiminde kısa bir sayfa var.</p>
<h2>Molekül</h2>
<div class="grid"><a class="card" href="bilesen/ExactMatch.html"><h3>ExactMatch</h3><p>Girdinin şekline bakıp en ucuz atomu seçer. <span class="badge">kind: molecule</span></p></a></div>
<h2>Atomlar</h2>
<div class="grid">${atoms.map((A) => `<a class="card" href="bilesen/${A.manifest.name}.html"><h3>${A.manifest.name}</h3><p>${esc(INFO[A.manifest.name].idea.split(';')[0])}.</p><p><span class="badge">${esc(A.manifest.references.join('; '))}</span><span class="badge">grup ${INFO[A.manifest.name].group}</span></p></a>`).join('\n')}</div>
<h2>Atölye bileşen türleri</h2>
<p>Atölyede kutular türlü uçlarla bağlanır; yalnızca aynı türdeki uçlar bağlanabilir (<code>src/workflows/catalog.js</code>).</p>
${table(['Tür', 'Anlamı', 'Üreten', 'Kullanan'], [
    { cells: ['<code>Source.File</code>', 'kaynak dosya: yol + metin', 'Kod/Log/FASTA yapıştır, Dosya yükle, Örnek veri', 'Kaynak → FASTA.Entry, FASTA okuyucu'] },
    { cells: ['<code>FASTA.Entry</code>', '<code>{ header, seq }</code>', 'uyarlayıcılar', 'atomlar, ExactMatch'] },
    { cells: ['<code>Pattern.Set</code>', 'desenler + ignoreCase', 'todo, secrets, banned-api, errors, özel liste', 'atomlar, ExactMatch (birden çok küme birleşir)'] },
    { cells: ['<code>Sequence.Match</code>', '<code>{ header, pattern, position, length }</code>', 'atomlar, ExactMatch', 'Eşleşme → Bulgu'] },
    { cells: ['<code>Finding</code>', 'dosya:satır:sütun + desen + satır önizlemesi', 'Eşleşme → Bulgu', 'Bulgu tablosu, Özet, JSONL indir, "Bulgu varsa başarısız" kapısı'] },
  ])}`;
writeFileSync(new URL('bilesenler.html', SITE), page('bilesenler.html', 'Bileşenler · Kod Bilimi Atölyesi', bilesenler));

const versionRows = Object.values(SETS).map((s) => ({
  cells: [s.model, s.label, String(s.data.cases.length), String(s.data.seed), pct(s.m[AUTO].fastestRate), f3(s.m[AUTO].geomeanSlowdown), wx(s.m[AUTO].worstSlowdown), f3(s.m[E2E].geomeanSlowdown), f3(s.m[AUTO].totalRatio), s.data.machine.cpu.replace('Intel(R) Xeon(R) Processor @ ', 'Xeon ')],
}));
const worstD = [...SETS.D.data.cases].sort((a, b) => b.times[b.selected].ms / b.bestMs - a.times[a.selected].ms / a.bestMs).slice(0, 5);
const sonuclar = `
<h1>Sonuçlar</h1>
<p class="lead">Bütün sayılar <code>bench/results/</code> altındaki ham ölçümlerden bu sayfa üretilirken hesaplandı. "Yavaşlama" = politikanın harcadığı süre / o vakadaki en hızlı atomun süresi. Satır "${esc(E2E)}" molekülün kendi uçtan uca süresidir (kurulum + şekil + tahmin + arama); diğer satırlar ödevin tanımıyla yalnızca seçilen atomun süresidir.</p>
<h2>D: çok desenli taze küme (model v4)</h2>
<p class="small">${SETS.D.data.cases.length} vaka, tohum ${SETS.D.data.seed}, k 2–120, n 12 000–900 000, m 3–100 (ızgara değerleri hariç), log / ikili / metin alfabeleri kalibrasyonda yok. Bir kez ölçüldü; sonuca bakılarak model değiştirilmedi. Ham: <a href="../bench/results/validation-d.json">validation-d.json</a>, tablo: <a href="../bench/results/validation-d.md">validation-d.md</a>.</p>
${policyTable(D)}
<figure><img src="../docs/rapor/sekil2_politikalar.svg" alt="D kümesinde politikaların yavaşlama geometrik ortalaması ve en kötü vakası"><figcaption>D kümesinde politikalar (log ölçek). Açık mavi: molekül uçtan uca.</figcaption></figure>
<h2>E: tek desenli taze küme (model v4, k = 1)</h2>
<p class="small">${SETS.E.data.cases.length} vaka, tohum ${SETS.E.data.seed}. Ham: <a href="../bench/results/validation-e.json">validation-e.json</a>.</p>
${policyTable(E)}
<h2>Karar süresi (doğrudan ölçüm)</h2>
<p>Doğrulamadaki uçtan uca ölçüm iki gürültülü sürenin farkına dayanır; D'de molekül, seçtiği atomdan medyanda kısa ölçüldü (oran ${f3(overheadD)}), yani bu düzenek küçük karar süresini ayıramıyor. Bu yüzden karar adımı ayrıca, tek başına ve çok kez tekrarlanarak ölçüldü (<a href="../bench/results/karar-yuku-v4.md">karar-yuku-v4.md</a>).</p>
${table(['Küme', { t: 'Şekil v3 (medyan, ms)', n: 1 }, { t: 'Şekil v4 (medyan, ms)', n: 1 }, { t: 'Karar v4 (medyan, ms)', n: 1 }, { t: 'Karar / seçilen atom (medyan)', n: 1 }, { t: '(%90)', n: 1 }], [
    { cells: ['D', ms(KD.shapeV3), ms(KD.shapeV4), ms(KD.decision), pct(KD.ratio), pct(KD.ratio90)] },
    { cells: ['E', ms(KE.shapeV3), ms(KE.shapeV4), ms(KE.decision), pct(KE.ratio), pct(KE.ratio90)] },
  ])}
<h2>Sürüm tablosu</h2>
<p>Model her değiştiğinde yeni bir taze kümede ölçüldü; eski sonuç dosyaları silinmedi. A, v1 ve v2'nin hataları bulunurken görüldüğü için "görülmemiş" sayılmaz. v3 ve v4 farklı makinelerde ölçüldü (son sütun); bu yüzden v3 → v4 farkının ne kadarının modelden, ne kadarının makineden geldiği ayrılamaz.</p>
${table(['Model', 'Küme', { t: 'Vaka', n: 1 }, { t: 'Tohum', n: 1 }, { t: 'En hızlı', n: 1 }, { t: 'Geo. ort.', n: 1 }, { t: 'En kötü', n: 1 }, { t: 'Uçtan uca geo. ort.', n: 1 }, { t: 'Toplam / en iyi', n: 1 }, 'Makine'], versionRows, { cls: (r) => (r.cells[0] === 'v4' ? 'hl' : '') })}
<h2>D'de en kötü 5 seçim</h2>
${table(['Vaka', 'Alfabe', { t: 'n', n: 1 }, { t: 'k', n: 1 }, 'm', 'Seçilen', { t: 'ms', n: 1 }, 'En hızlı', { t: 'ms', n: 1 }, { t: 'Yavaşlama', n: 1 }], worstD.map((c) => ({
    cells: [String(c.id), c.alphabet, int(c.n), String(c.k), c.lengths.join('/'), c.selected.replace('Search', ''), ms(c.times[c.selected].ms), c.best.replace('Search', ''), ms(c.bestMs), wx(c.times[c.selected].ms / c.bestMs)],
  })))}
<h2>Kalibrasyon ızgarası</h2>
<figure><img src="../docs/rapor/sekil1_kazanan.svg" alt="Kalibrasyon ızgarasında her hücrede en hızlı atom"><figcaption>${calib.cases.length} vakada en hızlı atom (3 alfabe × 3 n × 5 m × 4 k). Ham: <a href="../bench/results/calibration.json">calibration.json</a>.</figcaption></figure>
<figure><img src="../docs/rapor/sekil3_dagilim.svg" alt="D kümesinde yavaşlamanın birikimli dağılımı"><figcaption>D kümesinde yavaşlamanın birikimli dağılımı.</figcaption></figure>`;
writeFileSync(new URL('sonuclar.html', SITE), page('sonuclar.html', 'Sonuçlar · Kod Bilimi Atölyesi', sonuclar));

const rapor = `
<h1>Rapor</h1>
<p class="lead">IoS bileşen yayını biçiminde rapor: 8 bölüm (ana metin en fazla 6 sayfa) ve ekler.</p>
<div class="cta"><a class="btn primary" href="../docs/rapor/Rapor.pdf">Rapor.pdf'i aç</a><a class="btn" href="../docs/rapor/rapor.html">HTML sürümü</a><a class="btn" href="../docs/sunum/index.html">Sunum</a></div>
<object class="pdf" data="../docs/rapor/Rapor.pdf" type="application/pdf" aria-label="Rapor PDF"><p>Tarayıcınız PDF'i burada gösteremiyor: <a href="../docs/rapor/Rapor.pdf">Rapor.pdf</a>.</p></object>
<h2>Diğer belgeler</h2>
<ul>
<li><a href="../docs/sapmalar.md">Makaleden ve klasik tariflerden sapmalar</a></li>
<li><a href="../docs/mutasyon.md">Mutasyon denetimi</a></li>
<li><a href="../docs/anlatim.md">Her dosyanın sade anlatımı</a></li>
<li><a href="../docs/kontrol.md">Ödev kontrol listesi</a></li>
<li><a href="../KARARLAR.md">Kararlar</a></li>
</ul>`;
writeFileSync(new URL('rapor.html', SITE), page('rapor.html', 'Rapor · Kod Bilimi Atölyesi', rapor));

const ekip = `
<h1>Ekip</h1>
<p class="lead">Grup çalışması. Ders: <span class="ph">[ders kodu ve adı]</span> · Öğretim elemanı: <span class="ph">[ad soyad]</span></p>
${table(['Üye', 'Numara', 'Katkı'], [
    { cells: ['Baki <span class="ph">[soyad]</span>', '<span class="ph">[numara]</span>', '<span class="ph">[...]</span>'] },
    { cells: ['<span class="ph">[Üye 2 ad soyad]</span>', '<span class="ph">[numara]</span>', '<span class="ph">[...]</span>'] },
  ])}
<p class="small">Köşeli parantezli alanlar grup tarafından doldurulacak; bilgiler uydurulmadı.</p>
<h2>Yapay zekâ kullanımı</h2>
<p>Ders politikası yapay zekâ kullanımını serbest bırakıyor. Kod, testler, ölçüm betikleri, atölye, site, sunum ve rapor bir yapay zekâ kodlama aracıyla (Claude Code) üretildi; bütün sayılar çalıştırılan komutların çıktısından alındı. Sunumda her bölümün anlatılabilmesi için <a href="../docs/anlatim.md">docs/anlatim.md</a> hazırlandı.</p>`;
writeFileSync(new URL('ekip.html', SITE), page('ekip.html', 'Ekip · Kod Bilimi Atölyesi', ekip));

console.log(`site/: ${6 + atoms.length} sayfa yazıldı (model ${coefficients.model}; D ${SETS.D.data.cases.length} vaka, E ${SETS.E.data.cases.length} vaka)`);

// ------------------------------------------------------------------ sunum (docs/sunum/index.html)
// Slaytlar da aynı ölçüm dosyalarından üretilir; ok tuşlarıyla ilerler, PDF'ye yazdırılabilir.
{
  const w = SETS.D.data.cases.find((c) => c.id === worstD[0].id);
  const est = (n) => w.estimates[n].ms;
  const tm = (n) => w.times[n].ms;
  const mini = (m, rows) => table(['Politika', { t: 'En hızlı', n: 1 }, { t: '%10 içinde', n: 1 }, { t: 'Geo. ort.', n: 1 }, { t: 'En kötü', n: 1 }, { t: 'Toplam / en iyi', n: 1 }],
    rows.map((label) => ({ label, cells: [esc(label.replace('Search', '').replace('her zaman', 'hep')), pct(m[label].fastestRate), pct(m[label].within10Rate), f3(m[label].geomeanSlowdown), wx(m[label].worstSlowdown), f3(m[label].totalRatio)] })),
    { cls: (r) => (r.label === AUTO ? 'hl' : r.label === E2E ? 'e2e' : '') });
  const slides = [
    `<h1>Kod Bilimi Atölyesi</h1><p class="big">Akıllı tam desen eşleştirme: IoS atomları, seçici bir molekül ve yazılım mühendisliği için tarayıcıda bir iş akışı düzenleyicisi</p><p class="muted"><span class="ph">[ders kodu ve adı]</span> · <span class="ph">[öğretim elemanı]</span><br>Baki <span class="ph">[soyad]</span> · <span class="ph">[Üye 2 ad soyad]</span></p>`,
    `<h2>Problem</h2><ul><li>Bir metinde bir ya da çok desenin geçtiği <b>bütün</b> yerleri bulmak: genomda kesim bölgesi, kodda <code>TODO</code>, logda <code>ERROR</code>.</li><li>Onlarca algoritma var, <b>hiçbiri her durumda en hızlı değil</b>: kısa desende iyi olan uzun desende, tek desende iyi olan çok desende geri kalır.</li><li>Soru: girdiye bakıp doğru algoritmayı <b>kendisi</b> seçen bir bileşen yazılabilir mi, ve seçimi doğru mu?</li></ul>`,
    `<h2>IoS fikri → yazılım mühendisliği</h2><div class="two"><div><h3>IoS (biyoloji)</h3><ul><li><b>Atom</b>: tek dönüşüm, sözleşmesi sabit</li><li><b>Molekül</b>: aynı görevi yapan atomlardan seçer</li><li><b>İş akışı</b>: bileşenleri bağlar</li></ul></div><div><h3>Bizim aktarımımız</h3><ul><li>Kaynak dosya → <code>FASTA.Entry</code> uyarlayıcısı: atomlara dokunmadan kod ve log</li><li>Hazır desen kümeleri: todo, secrets, banned-api, errors</li><li><b>Atölye</b>: türlü uçlarla iş akışı, CI kapısı ("bulgu varsa başarısız")</li></ul></div></div><p class="muted">Kodda 100'den fazla farklı karakter var ama etkin alfabe küçük (σe = 1/Σp²): kazanan atom DNA'dakinden farklı.</p>`,
    `<h2>Atomlar</h2>${table(['Atom', 'Fikir', 'Grup'], atoms.map((A) => ({ cells: [A.manifest.name.replace('Search', ''), esc(INFO[A.manifest.name].idea.split(';')[0].split(':')[0]), INFO[A.manifest.name].group] })))}<p class="muted">Hepsi aynı girdi/çıktı; NaiveSearch ile eleman eleman aynı sonuç (360 rastgele vaka, gerçek veri).</p>`,
    `<h2>Molekül ve maliyet modeli</h2><ul><li>İlk kaydın şekli: n, σ, σe, k, mMin, mMax, mMean</li><li>Her atom kendi özelliklerini verir (ör. Horspool: <i>pencere sayısı</i> = Σ n / E[kayma])</li><li>Tahmin = Σ katsayı × özellik; katsayılar ${calib.cases.length} vakalık ızgarada <b>negatif olmayan en küçük kareler</b> ile</li><li>En ucuz atom seçilir; <code>record</code> = şekil, tahminler, seçim, neden</li><li><b>v4:</b> şekil 64 × 256 karakterlik örneklemden → şekil hesabı medyanda ${ms(KD.shapeV3)} ms'den ${ms(KD.shapeV4)} ms'ye (D)</li></ul>`,
    `<h2>CANLI: atölye</h2><div class="two"><img src="../ekran/atolye-masaustu.png" alt="Atölye ekran görüntüsü"><ol><li><code>npm run web</code> → <code>/web/</code></li><li>Sol panel: <b># tek-desen-büyük-dosya</b></li><li><b>Tarayıcıda çalıştır</b> → rozet: bulgu sayısı ve süre</li><li>ExactMatch kutusu → karar kaydı: tek desende Horspool ailesi (bm4DNADS), 16 desende Aho-Corasick</li><li><b>Açıkla</b> → iş akışı düz Türkçe</li><li>Yedek: <b># gizli-bilgi-sızıntısı</b> (kapı kaldı)</li></ol></div>`,
    `<h2>Doğrulama (taze D, v4, ${SETS.D.data.cases.length} vaka)</h2>${mini(D, [AUTO, E2E, bestD[0], 'her zaman AhoCorasickSearch', 'Allmer 2016 kuralı'])}<p class="muted">Tek desen (E): seçilen ${f3(E[AUTO].geomeanSlowdown)}, uçtan uca ${f3(E[E2E].geomeanSlowdown)}; Allmer ${f3(E['Allmer 2016 kuralı'].geomeanSlowdown)}, hep Horspool ${f3(E['her zaman HorspoolSearch'].geomeanSlowdown)}.</p>`,
    `<h2>Bir yanlış seçim: D, vaka ${w.id}</h2><p>${w.alphabet === 'text' ? 'İngilizce benzeri metin (kalibrasyonda yok)' : w.alphabet}, n = ${int(w.n)}, k = ${w.k}, m = ${w.lengths.join('/')}</p>${table(['Atom', { t: 'Tahmin (ms)', n: 1 }, { t: 'Ölçülen (ms)', n: 1 }], [w.selected, w.best].map((n) => ({ cells: [n.replace('Search', '') + (n === w.selected ? ' (seçilen)' : ' (en hızlı)'), ms(est(n)), ms(tm(n))] })))}<ul><li>Yavaşlama ${wx(tm(w.selected) / w.bestMs)}: iki tahmin <b>ters yönde</b> yanıldı (${dec(tm(w.selected) / est(w.selected), 2)}× az, ${dec(est(w.best) / tm(w.best), 2)}× fazla).</li><li>Model metni tekdüze rastgele sayar. Olası neden: kelimelerden oluşan metinde sık q-gramlar desende de geçer, q-gram kayması öngörülenden kısa kalır; Wu-Manber'in blok tablosu ise bu metinde öngörülenden seyrek doğrulama yapar. (Doğrulamadan sonra model değiştirilmedi.)</li></ul>`,
    `<h2>Sınırlar</h2><ul><li><b>Tek desen</b>: seçim zayıf; uçtan uca molekül hep Horspool / Allmer kuralının gerisinde (E)</li><li><b>İkili alfabe</b>: E'nin en kötü 5 vakasının 5'i</li><li><b>Karar ilk kayda göre</b> (sözleşme): ilk dosya küçükse seçim kötü olabilir</li><li><b>Ölçüm</b>: D'de uçtan uca oran 1'in altına düştü (medyan ${f3(overheadD)}) → düzenek küçük farkı ayıramıyor; karar süresi ayrıca ölçüldü (medyan ${pct(KD.ratio)})</li><li>v3 ve v4 farklı makinelerde ölçüldü; fark ayrıştırılamaz</li></ul>`,
    `<h2>Ekip ve katkılar</h2>${table(['Üye', 'Katkı'], [{ cells: ['Baki <span class="ph">[soyad, numara]</span>', '<span class="ph">[...]</span>'] }, { cells: ['<span class="ph">[Üye 2 ad soyad, numara]</span>', '<span class="ph">[...]</span>'] }])}<p class="muted">Yapay zekâ kullanımı ders politikasında serbest; kod, testler, atölye, site, rapor ve bu slaytlar Claude Code ile üretildi, sayılar çalıştırılan komutlardan. Sorular: <code>docs/sunum.md</code>.</p>`,
  ];
  const html = `<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kod Bilimi Atölyesi · Sunum</title>
<style>
  :root { --ink: #1d1c1f; --ink2: #55535a; --line: #e4e1e6; --soft: #f6f5f8; --accent: #127c86; --accent-soft: #e2f3f4; --head: #3b1239; --warn-soft: #fff5dd; --warn: #8a5a00; }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: #26092a; font-family: "Inter", "Segoe UI", system-ui, Arial, sans-serif; color: var(--ink); }
  .deck { height: 100%; display: grid; place-items: center; }
  section { display: none; width: min(100vw, calc(100vh * 16 / 9)); aspect-ratio: 16 / 9; background: #fff; padding: 3.6% 5.5%; position: relative; overflow: hidden; font-size: min(2.2vw, 3.9vh); line-height: 1.4; }
  section.on { display: block; }
  section::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 1.1%; background: var(--head); }
  h1 { font-size: 2.5em; margin: 18% 0 .3em; letter-spacing: -.02em; color: var(--head); }
  h2 { font-size: 1.55em; margin: 0 0 .6em; color: var(--head); letter-spacing: -.01em; }
  h3 { font-size: 1em; margin: .2em 0; color: var(--accent); }
  .big { font-size: 1.15em; max-width: 85%; }
  .muted { color: var(--ink2); font-size: .8em; }
  ul, ol { margin: .2em 0; padding-left: 1.2em; } li { margin: .25em 0; }
  code { font-family: "JetBrains Mono", Consolas, monospace; font-size: .85em; background: var(--soft); padding: 0 .2em; border-radius: 3px; }
  .two { display: grid; grid-template-columns: 1.25fr 1fr; gap: 4%; align-items: start; }
  .two ol, .two ul { font-size: .9em; }
  .two img { width: 100%; border: 1px solid var(--line); border-radius: 8px; }
  .table-wrap { margin: .3em 0 .5em; }
  table { border-collapse: collapse; width: 100%; font-size: .78em; }
  th, td { text-align: left; padding: .28em .5em; border-bottom: 1px solid var(--line); }
  th { color: var(--ink2); font-weight: 600; } td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  tr.hl td { background: var(--accent-soft); font-weight: 700; } tr.e2e td { background: var(--soft); }
  .ph { background: var(--warn-soft); color: var(--warn); padding: 0 .2em; border-radius: 3px; }
  .num { position: absolute; right: 2.5%; bottom: 3%; font-size: .6em; color: var(--ink2); }
  .help { position: fixed; left: 10px; bottom: 8px; color: #d9c6d8; font-size: 12px; }
  @media print {
    @page { size: 297mm 167mm; margin: 0; }
    html, body { background: #fff; height: auto; } .deck { display: block; } .help { display: none; }
    section { display: block !important; width: 297mm; height: 167mm; aspect-ratio: auto; font-size: 15pt; page-break-after: always; break-after: page; }
  }
</style>
</head>
<body>
<div class="deck">
${slides.map((s, i) => `<section aria-label="Slayt ${i + 1}"${i === 0 ? ' class="on"' : ''}>${s}<span class="num">${i + 1} / ${slides.length}</span></section>`).join('\n')}
</div>
<p class="help">← → ya da boşluk: ilerle · Home/End · P: yazdır (PDF)</p>
<script>
  // Ok tuşları, boşluk, Page Up/Down, Home/End; slayt numarası adres çubuğunda (#3).
  const s = [...document.querySelectorAll('section')];
  let i = Math.min(s.length - 1, Math.max(0, (parseInt(location.hash.slice(1), 10) || 1) - 1));
  const show = (j) => { i = Math.min(s.length - 1, Math.max(0, j)); s.forEach((x, k) => x.classList.toggle('on', k === i)); history.replaceState(null, '', '#' + (i + 1)); };
  show(i);
  addEventListener('keydown', (e) => {
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) { e.preventDefault(); show(i + 1); }
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) { e.preventDefault(); show(i - 1); }
    else if (e.key === 'Home') show(0); else if (e.key === 'End') show(s.length - 1);
    else if (e.key === 'p' || e.key === 'P') print();
  });
  addEventListener('click', (e) => { if (!e.target.closest('a')) show(e.clientX > innerWidth / 3 ? i + 1 : i - 1); });
</script>
</body>
</html>
`;
  mkdirSync(new URL('docs/sunum/', VIZE), { recursive: true });
  writeFileSync(new URL('docs/sunum/index.html', VIZE), html);
  console.log(`docs/sunum/index.html: ${slides.length} slayt`);
}
