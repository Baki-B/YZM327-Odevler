// Site, slaytlar ve atölyedeki bütün göreli bağlantıları (href, src, data) yerel sunucudan ister;
// 200 dönmeyeni listeler. Kullanım (vize/ klasöründen): node scripts/baglanti-denetimi.js
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const VIZE = fileURLToPath(new URL('..', import.meta.url));
const PORT = 8392;
const BASE = `http://localhost:${PORT}/`;
const server = spawn(process.execPath, ['scripts/sunucu.js', '--port', String(PORT)], { cwd: VIZE, stdio: ['ignore', 'pipe', 'inherit'] });
await new Promise((r) => server.stdout.once('data', r));

const start = ['index.html', 'site/index.html', 'docs/sunum/index.html', 'web/index.html'];
const seen = new Set();
const queue = start.map((p) => new URL(p, BASE).href);
const broken = [];
let pages = 0;
let links = 0;
try {
  while (queue.length) {
    const url = queue.shift();
    if (seen.has(url)) continue;
    seen.add(url);
    const res = await fetch(url);
    if (res.status !== 200) { broken.push(`${res.status} ${url}`); continue; }
    if (!(res.headers.get('content-type') ?? '').includes('text/html')) continue;
    pages++;
    const html = await res.text();
    for (const m of html.matchAll(/(?:href|src|data)="([^"#][^"]*)"/g)) {
      const target = m[1];
      if (/^(https?:|mailto:|data:|javascript:)/.test(target)) continue;
      links++;
      const abs = new URL(target, url);
      abs.hash = '';
      if (!abs.href.startsWith(BASE)) { broken.push(`kök dışına çıkıyor: ${target} (${url})`); continue; }
      const sameSite = /\/(site|docs\/sunum|web)\/|\/index\.html$/.test(abs.pathname) && abs.pathname.endsWith('.html');
      if (sameSite) queue.push(abs.href);
      else if (!seen.has(abs.href)) {
        seen.add(abs.href);
        const r = await fetch(abs.href, { method: 'HEAD' });
        if (r.status !== 200) broken.push(`${r.status} ${target}  ←  ${url.replace(BASE, '')}`);
      }
    }
  }
} finally {
  server.kill();
}
console.log(`${pages} sayfa, ${links} bağlantı denetlendi; kırık: ${broken.length}`);
for (const b of broken) console.log('  ' + b);
process.exitCode = broken.length ? 1 : 0;
