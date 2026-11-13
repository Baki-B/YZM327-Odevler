// Atölyenin örnek verilerini depodaki gerçek dosyalardan üretir (web/data/).
//   web/data/agora.json   ../forum klasöründeki metin dosyaları [{ path, text }]
//                         (ios scan'in dosya gezme kurallarıyla: gizli/derleme klasörleri,
//                         ikili dosyalar ve 5 MB'tan büyükler atlanır)
//   web/data/gizli.json   web/data/gizli/ içindeki SAHTE örnek dosyalar
//   web/data/ornek.log    bench/data.js log üreticisi (doğrulamadaki "log" alfabesi, tohum 20261113)
//                         + 3 örnek Traceback / Exception bloğu (elle yazıldı, açıkça örnek)
// Kullanım (vize/ klasöründen): node scripts/ornekler.js
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { makeText } from '../bench/data.js';

const VIZE = new URL('..', import.meta.url).pathname;
const ROOT = join(VIZE, '..');
const SKIP_DIRS = new Set(['.git', 'node_modules', '__pycache__', '_site', '.venv', 'venv', 'dist', 'build']);

function* walk(path) {
  const st = statSync(path);
  if (st.isDirectory()) {
    for (const name of readdirSync(path).sort()) {
      if (SKIP_DIRS.has(name) || name.startsWith('.')) continue;
      yield* walk(join(path, name));
    }
  } else if (st.isFile() && st.size <= 5 * 1024 * 1024) {
    const buf = readFileSync(path);
    if (buf.subarray(0, 8192).includes(0)) return;
    yield { abs: path, text: buf.toString('utf8') };
  }
}

const bundle = (dir, base) => [...walk(dir)].map((f) => ({ path: relative(base, f.abs), text: f.text }));

const agora = bundle(join(ROOT, 'forum'), ROOT);
writeFileSync(join(VIZE, 'web/data/agora.json'), JSON.stringify(agora));
const gizli = bundle(join(VIZE, 'web/data/gizli'), join(VIZE, 'web/data'));
writeFileSync(join(VIZE, 'web/data/gizli.json'), JSON.stringify(gizli));

const TRACES = [
  'Traceback (most recent call last):\n  File "forum/oylama.py", line 88, in tur_kapat\n    oran = agirlik / katilimci\nZeroDivisionError: division by zero\n',
  'Traceback (most recent call last):\n  File "forum/defter.py", line 41, in yaz\n    kayit = json.loads(satir)\njson.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)\n',
  'Unhandled Exception in worker mailer: TimeoutError: SMTP timeout after 30000 ms\n',
];
const lines = makeText('log', 48000, 20261113).split('\n');
lines.pop(); // son satır yarım kalmış olabilir
const at = [Math.floor(lines.length * 0.2), Math.floor(lines.length * 0.55), Math.floor(lines.length * 0.85)];
let out = '';
lines.forEach((l, i) => {
  out += l + '\n';
  const j = at.indexOf(i);
  if (j >= 0) out += TRACES[j];
});
writeFileSync(join(VIZE, 'web/data/ornek.log'), out);

console.log(`agora.json: ${agora.length} dosya, ${agora.reduce((s, f) => s + f.text.length, 0)} karakter`);
console.log(`gizli.json: ${gizli.length} dosya; ornek.log: ${out.length} karakter, ${out.split('\n').length - 1} satır`);
