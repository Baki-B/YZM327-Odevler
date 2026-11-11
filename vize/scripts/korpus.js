// Kaynak kod korpusunu üretir: bench/corpus/kod.txt
// Bu deponun kendi kaynak dosyaları (Agora projesi: Python, JavaScript, HTML)
// birleştirilir. Kalibrasyonda "kaynak kod" alfabesi buradan örneklenir.
// Kullanım: node scripts/korpus.js   (vize/ klasöründen)
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, extname } from 'node:path';

const ROOT = new URL('../..', import.meta.url).pathname;
const DIRS = ['forum', 'testler', 'tarayici', 'olcum', 'laboratuvar'];
const EXT = new Set(['.py', '.js', '.html', '.css']);

const files = [];
function walk(dir) {
  for (const name of readdirSync(dir).sort()) {
    const p = join(dir, name);
    if (name.startsWith('.') || name === '__pycache__' || name === 'node_modules') continue;
    const st = statSync(p);
    if (st.isDirectory()) walk(p);
    else if (EXT.has(extname(name))) files.push(p);
  }
}
for (const d of DIRS) {
  try { walk(join(ROOT, d)); } catch { /* klasör yoksa geç */ }
}
let out = '';
for (const f of files) out += readFileSync(f, 'utf8').replaceAll('\r\n', '\n') + '\n';
const target = new URL('../bench/corpus/kod.txt', import.meta.url).pathname;
writeFileSync(target, out);
console.log(`${files.length} dosya, ${out.length} karakter → bench/corpus/kod.txt`);
