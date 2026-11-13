// v3 (calibration-v3.json) ve v4 (calibration.json) kalibrasyon ölçümlerini karşılaştırır:
// iki ölçüm aynı 180 vakayı, aynı atomlarla, farklı makinelerde ölçtü.
// Çıktı: bench/results/makine-karsilastirma.md
// Kullanım (vize/ klasöründen): node scripts/makine-karsilastir.js
import { readFileSync, writeFileSync } from 'node:fs';

const RES = new URL('../bench/results/', import.meta.url);
const a = JSON.parse(readFileSync(new URL('calibration-v3.json', RES), 'utf8'));
const b = JSON.parse(readFileSync(new URL('calibration.json', RES), 'utf8'));
const ratio = [];
const spread = [[], []];
for (let i = 0; i < a.cases.length; i++) {
  if (a.cases[i].seed !== b.cases[i].seed) throw new Error(`vaka ${i}: tohumlar farklı`);
  for (const k of Object.keys(a.cases[i].times)) {
    ratio.push(b.cases[i].times[k].ms / a.cases[i].times[k].ms);
    for (const [j, c] of [[0, a.cases[i]], [1, b.cases[i]]]) {
      const s = [...c.times[k].samples].sort((x, y) => x - y);
      spread[j].push(s[s.length - 1] / s[0]);
    }
  }
}
const q = (v, p) => [...v].sort((x, y) => x - y)[Math.floor(v.length * p)];
const f = (x) => x.toFixed(2);
let md = `# Ölçüm makineleri: v3 ve v4 kalibrasyonu\n\n`;
md += `v3: ${a.machine.cpu}, Node ${a.machine.node}, ${a.machine.date}\n\nv4: ${b.machine.cpu}, Node ${b.machine.node}, ${b.machine.date}\n\n`;
md += `Aynı ${a.cases.length} vaka, aynı atomlar (${ratio.length} atom-vaka çifti). Atom kodu iki ölçüm arasında değişmedi.\n\n`;
md += `| Ölçüt | Medyan | %10 | %90 |\n|---|---:|---:|---:|\n`;
md += `| v4 süresi / v3 süresi | ${f(q(ratio, 0.5))} | ${f(q(ratio, 0.1))} | ${f(q(ratio, 0.9))} |\n`;
md += `| tekrarlar arası en büyük / en küçük, v3 | ${f(q(spread[0], 0.5))} | ${f(q(spread[0], 0.1))} | ${f(q(spread[0], 0.9))} |\n`;
md += `| tekrarlar arası en büyük / en küçük, v4 | ${f(q(spread[1], 0.5))} | ${f(q(spread[1], 0.1))} | ${f(q(spread[1], 0.9))} |\n`;
md += `\nv4 makinesi aynı işi medyanda ${f(q(ratio, 0.5))} kat uzun sürede yaptı ve tekrarlar arasında daha çok oynadı. Bu yüzden v3 (A, B, C) ile v4 (D, E) arasındaki farkın ne kadarının modelden, ne kadarının makineden geldiği ayrılamaz.\n`;
writeFileSync(new URL('makine-karsilastirma.md', RES), md);
process.stdout.write(md);
