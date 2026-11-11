// Rapor şekilleri: ölçüm dosyalarından SVG üretir (elle çizim yok).
//   docs/rapor/sekil1_kazanan.svg      kalibrasyon: m × k ızgarasında en hızlı atom (alfabe × n panelleri)
//   docs/rapor/sekil2_politikalar.svg  doğrulama: politikaların yavaşlama geometrik ortalaması
//   docs/rapor/sekil3_dagilim.svg      doğrulama: yavaşlamanın birikimli dağılımı (molekül, Allmer, en iyi tek atom)
// Kullanım: npm run figures

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

import { existsSync } from 'node:fs';

const RES = new URL('../../bench/results/', import.meta.url);
// Şekil 2 ve 3, hiçbir karar için kullanılmamış taze doğrulama kümesinden çizilir (varsa).
const VALIDATION = existsSync(new URL('validation-taze.json', RES)) ? 'validation-taze.json' : 'validation.json';
const OUT = new URL('../../docs/rapor/', import.meta.url);
mkdirSync(OUT, { recursive: true });

// Açık tema, referans kategorik palet (sabit sıra; renk atomu izler, sırasını değil)
const ATOMS = [
  ['WuManberSearch', 'WM', '#2a78d6'],
  ['AhoCorasickSearch', 'AC', '#eb6834'],
  ['HorspoolSearch', 'HP', '#1baf7a'],
  ['Bm4DnaDsSearch', 'DS', '#eda100'],
  ['BoyerMooreSearch', 'BM', '#e87ba4'],
  ['Bm4DnaHmbsSearch', 'HM', '#008300'],
  ['ShiftOrSearch', 'SO', '#6250d6'],
  ['KmpSearch', 'KMP', '#e34948'],
];
const COLOR = Object.fromEntries(ATOMS.map(([n, , c]) => [n, c]));
const ABBR = Object.fromEntries(ATOMS.map(([n, a]) => [n, a]));
const INK = '#0b0b0b';
const INK2 = '#52514e';
const MUTED = '#8a8984';
const GRID = '#e4e3df';
const SURFACE = '#fcfcfb';
const FONT = 'font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif"';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
/** Hücre rengine göre okunur yazı rengi (açık zeminde koyu, koyu zeminde beyaz). */
function onColor(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return L > 0.3 ? INK : '#ffffff';
}

function svg(w, h, body, title) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${esc(title)}">
<title>${esc(title)}</title>
<rect width="${w}" height="${h}" fill="${SURFACE}"/>
${body}
</svg>
`;
}

// ------------------------------------------------------------- Şekil 1
function figure1() {
  const cal = JSON.parse(readFileSync(new URL('calibration.json', RES), 'utf8'));
  const { alphabets, n: NS, m: MS, k: KS } = cal.grid;
  const names = { dna: 'DNA', protein: 'Protein', code: 'Kaynak kod' };
  const cw = 46, ch = 26, gap = 2;
  const panelW = KS.length * (cw + gap);
  const panelH = MS.length * (ch + gap);
  const left = 128, top = 64, colGap = 46, rowGap = 50;
  const W = left + alphabets.length * panelW + (alphabets.length - 1) * colGap + 20;
  const H = top + NS.length * panelH + (NS.length - 1) * rowGap + 112;
  let b = '';
  const used = new Set();
  alphabets.forEach((a, ai) => {
    const x0 = left + ai * (panelW + colGap);
    b += `<text x="${x0 + panelW / 2}" y="22" text-anchor="middle" ${FONT} font-size="14" font-weight="600" fill="${INK}">${names[a] ?? a}</text>`;
    b += `<text x="${x0 + panelW / 2}" y="40" text-anchor="middle" ${FONT} font-size="11" fill="${INK2}">desen sayısı k →</text>`;
    KS.forEach((k, ki) => {
      b += `<text x="${x0 + ki * (cw + gap) + cw / 2}" y="${top - 8}" text-anchor="middle" ${FONT} font-size="11" fill="${INK2}">${k}</text>`;
    });
    NS.forEach((n, ni) => {
      const y0 = top + ni * (panelH + rowGap);
      if (ai === 0) {
        const sup = { 4: '⁴', 5: '⁵', 6: '⁶' }[Math.round(Math.log10(n))];
        b += `<text x="14" y="${y0 + panelH / 2 + 4}" ${FONT} font-size="13" font-weight="600" fill="${INK}">n = 10${sup}</text>`;
      }
      MS.forEach((m, mi) => {
        if (ai === 0 || true) {
          b += `<text x="${x0 - 6}" y="${y0 + mi * (ch + gap) + ch / 2 + 4}" text-anchor="end" ${FONT} font-size="10" fill="${INK2}">m=${m}</text>`;
        }
        KS.forEach((k, ki) => {
          const c = cal.cases.find((x) => x.alphabet === a && x.n === n && x.m === m && x.k === k);
          const sorted = Object.entries(c.times).sort((p, q) => p[1].ms - q[1].ms);
          const [win, t] = sorted[0];
          const margin = sorted[1][1].ms / t.ms;
          used.add(win);
          const x = x0 + ki * (cw + gap);
          const y = y0 + mi * (ch + gap);
          b += `<rect x="${x}" y="${y}" width="${cw}" height="${ch}" rx="3" fill="${COLOR[win]}"><title>${esc(`${names[a]}, n=${n}, m=${m}, k=${k}: en hızlı ${win} (${t.ms.toFixed(3)} ms); ikinci ${sorted[1][0]} ${margin.toFixed(2)}× daha yavaş`)}</title></rect>`;
          b += `<text x="${x + cw / 2}" y="${y + ch / 2 + 4}" text-anchor="middle" ${FONT} font-size="10.5" font-weight="600" fill="${onColor(COLOR[win])}">${ABBR[win]}</text>`;
        });
      });
    });
  });
  // Lejant
  let lx = left;
  let ly = H - 66;
  b += `<text x="14" y="${ly + 11}" ${FONT} font-size="11" fill="${INK2}">En hızlı atom:</text>`;
  for (const [n, a, c] of ATOMS) {
    if (!used.has(n)) continue;
    const label = `${a} = ${n.replace('Search', '')}`;
    const w = 30 + label.length * 6.4;
    if (lx + w > W - 10) { lx = left; ly += 22; } // sığmazsa alt satıra geç
    b += `<rect x="${lx}" y="${ly}" width="14" height="14" rx="3" fill="${c}"/><text x="${lx + 19}" y="${ly + 11}" ${FONT} font-size="11" fill="${INK}">${label}</text>`;
    lx += w;
  }
  b += `<text x="14" y="${H - 12}" ${FONT} font-size="10" fill="${MUTED}">Kaynak: bench/results/calibration.json (ısınma + 5 tekrarın medyanı). Hücre = o (alfabe, n, m, k) vakasında en kısa süren atom.</text>`;
  writeFileSync(new URL('sekil1_kazanan.svg', OUT), svg(W, H, b, 'Kalibrasyon ızgarasında en hızlı atom'));
}

// ------------------------------------------------------------- Şekil 2
function figure2() {
  const val = JSON.parse(readFileSync(new URL(VALIDATION, RES), 'utf8'));
  const rows = Object.entries(val.metrics.all).sort((a, b) => a[1].geomeanSlowdown - b[1].geomeanSlowdown);
  const left = 200, right = 110, top = 58, bh = 20, gap = 8;
  const W = 760;
  const H = top + rows.length * (bh + gap) + 52;
  const max = Math.max(...rows.map(([, m]) => m.geomeanSlowdown));
  const ticks = [1, 1.5, 2, 3, 5, 10, 20].filter((t, i, a) => t <= max * 1.05 || a[i - 1] < max);
  const xMax = ticks[ticks.length - 1];
  const plotR = W - right - 40;
  const sx = (v) => left + (Math.log(v) / Math.log(xMax)) * (plotR - left);
  let b = '';
  b += `<text x="14" y="20" ${FONT} font-size="12" fill="${INK2}">Yavaşlamanın geometrik ortalaması (1 = her vakada en hızlı atom), log ölçek; ${val.cases.length} görülmemiş vaka</text>`;
  for (const t of ticks) {
    b += `<line x1="${sx(t)}" x2="${sx(t)}" y1="${top - 6}" y2="${H - 44}" stroke="${GRID}" stroke-width="1"/>`;
    b += `<text x="${sx(t)}" y="${H - 28}" text-anchor="middle" ${FONT} font-size="11" fill="${INK2}">${t}×</text>`;
  }
  b += `<text x="${W - right + 20}" y="${top - 14}" ${FONT} font-size="11" font-weight="600" fill="${INK2}">en kötü vaka</text>`;
  rows.forEach(([label, m], i) => {
    const y = top + i * (bh + gap);
    const mol = label.startsWith('ExactMatch');
    const fill = mol ? '#2a78d6' : label.startsWith('Allmer') ? '#eb6834' : '#b9b8b2';
    const w = Math.max(3, sx(m.geomeanSlowdown) - left);
    b += `<text x="${left - 8}" y="${y + bh / 2 + 4}" text-anchor="end" ${FONT} font-size="12" ${mol ? 'font-weight="700"' : ''} fill="${INK}">${esc(label.replace('Search', ''))}</text>`;
    b += `<rect x="${left}" y="${y}" width="${w}" height="${bh}" rx="4" fill="${fill}"><title>${esc(`${label}: yavaşlama geometrik ortalaması ${m.geomeanSlowdown.toFixed(3)}, en kötü ${m.worstSlowdown.toFixed(2)}×, en hızlıyı seçme %${(m.fastestRate * 100).toFixed(1)}`)}</title></rect>`;
    b += `<text x="${left + w + 6}" y="${y + bh / 2 + 4}" ${FONT} font-size="11" ${mol ? 'font-weight="700"' : ''} fill="${INK}">${m.geomeanSlowdown.toFixed(2)}</text>`;
    b += `<text x="${W - right + 20}" y="${y + bh / 2 + 4}" ${FONT} font-size="11" fill="${INK2}">${m.worstSlowdown.toFixed(1)}×</text>`;
  });
  b += `<text x="14" y="${H - 8}" ${FONT} font-size="10" fill="${MUTED}">Kaynak: bench/results/${VALIDATION}. Mavi: molekül; turuncu: Allmer 2016 kuralı; gri: hep aynı atomu kullanmak.</text>`;
  writeFileSync(new URL('sekil2_politikalar.svg', OUT), svg(W, H, b, 'Doğrulama: politikaların yavaşlaması'));
}

// ------------------------------------------------------------- Şekil 3
function figure3() {
  const val = JSON.parse(readFileSync(new URL(VALIDATION, RES), 'utf8'));
  const singles = Object.entries(val.metrics.all).filter(([l]) => l.startsWith('her zaman'));
  const bestSingle = singles.sort((a, b) => a[1].geomeanSlowdown - b[1].geomeanSlowdown)[0][0];
  const bestSingleName = bestSingle.replace('her zaman ', '');
  const series = [
    ['ExactMatch (auto)', '#2a78d6', (c) => c.selected],
    ['Allmer 2016 kuralı', '#eb6834', (c) => (c.shape.mMean < 50 ? 'Bm4DnaDsSearch' : 'Bm4DnaHmbsSearch')],
    [`her zaman ${bestSingleName.replace('Search', '')}`, '#1baf7a', () => bestSingleName],
  ];
  const W = 760, H = 380, left = 64, right = 190, top = 24, bottom = 54;
  const xmaxRaw = Math.max(...series.flatMap(([, , pick]) => val.cases.map((c) => c.times[pick(c)].ms / c.bestMs)));
  const xMax = Math.min(16, Math.pow(2, Math.ceil(Math.log2(Math.max(2, xmaxRaw)))));
  const sx = (v) => left + (Math.log2(Math.min(v, xMax)) / Math.log2(xMax)) * (W - left - right);
  const sy = (p) => top + (1 - p) * (H - top - bottom);
  let b = '';
  for (let p = 0; p <= 1.0001; p += 0.25) {
    b += `<line x1="${left}" x2="${W - right}" y1="${sy(p)}" y2="${sy(p)}" stroke="${GRID}"/>`;
    b += `<text x="${left - 8}" y="${sy(p) + 4}" text-anchor="end" ${FONT} font-size="11" fill="${INK2}">%${Math.round(p * 100)}</text>`;
  }
  for (let v = 1; v <= xMax; v *= 2) {
    b += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${top}" y2="${H - bottom}" stroke="${GRID}"/>`;
    b += `<text x="${sx(v)}" y="${H - bottom + 16}" text-anchor="middle" ${FONT} font-size="11" fill="${INK2}">${v}×</text>`;
  }
  b += `<line x1="${sx(1.1)}" x2="${sx(1.1)}" y1="${top}" y2="${H - bottom}" stroke="${MUTED}" stroke-dasharray="3 3"/>`;
  b += `<text x="${sx(1.1) + 4}" y="${H - bottom - 6}" ${FONT} font-size="10" fill="${MUTED}">%10 sınırı</text>`;
  b += `<text x="${(left + W - right) / 2}" y="${H - 14}" text-anchor="middle" ${FONT} font-size="11" fill="${INK2}">yavaşlama (seçilen / en hızlı), log ölçek</text>`;
  b += `<text x="16" y="${(top + H - bottom) / 2}" ${FONT} font-size="11" fill="${INK2}" transform="rotate(-90 16 ${(top + H - bottom) / 2})" text-anchor="middle">vakaların payı (≤ x)</text>`;
  series.forEach(([label, color, pick], si) => {
    const xs = val.cases.map((c) => c.times[pick(c)].ms / c.bestMs).sort((a, b) => a - b);
    let d = `M ${sx(1)} ${sy(0)}`;
    xs.forEach((x, i) => {
      d += ` L ${sx(x)} ${sy(i / xs.length)} L ${sx(x)} ${sy((i + 1) / xs.length)}`;
    });
    d += ` L ${sx(xMax)} ${sy(1)}`;
    b += `<path d="${d}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round"><title>${esc(label)}</title></path>`;
    const ly = top + 14 + si * 22;
    b += `<line x1="${W - right + 14}" x2="${W - right + 34}" y1="${ly}" y2="${ly}" stroke="${color}" stroke-width="3"/>`;
    b += `<text x="${W - right + 40}" y="${ly + 4}" ${FONT} font-size="11" fill="${INK}">${esc(label)}</text>`;
  });
  b += `<text x="${W - right + 14}" y="${top + 90}" ${FONT} font-size="10" fill="${MUTED}">Eğri ne kadar solda ve</text>`;
  b += `<text x="${W - right + 14}" y="${top + 103}" ${FONT} font-size="10" fill="${MUTED}">yukarıdaysa o kadar iyi.</text>`;
  if (xmaxRaw > xMax) b += `<text x="${W - right + 14}" y="${top + 122}" ${FONT} font-size="10" fill="${MUTED}">${xMax}× üstü kırpıldı (en büyük ${xmaxRaw.toFixed(1)}×).</text>`;
  b += `<text x="14" y="${H - 2}" ${FONT} font-size="10" fill="${MUTED}">Kaynak: bench/results/${VALIDATION}</text>`;
  writeFileSync(new URL('sekil3_dagilim.svg', OUT), svg(W, H, b, 'Doğrulama: yavaşlamanın birikimli dağılımı'));
}

figure1();
try {
  figure2();
  figure3();
} catch (err) {
  if (err.code !== 'ENOENT') throw err;
  process.stderr.write('validation.json yok: şekil 2 ve 3 atlandı (önce npm run bench)\n');
}
process.stdout.write('şekiller docs/rapor/ altına yazıldı\n');
