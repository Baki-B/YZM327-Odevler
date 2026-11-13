#!/usr/bin/env node
// Bağımlılıksız, salt okunur statik dosya sunucusu (yalnızca Node'un kendi modülleri).
// Atölye ES modülleri ve Web Worker kullandığı için file:// ile değil, bir sunucudan açılmalıdır.
//   node scripts/sunucu.js            → http://localhost:8327/  (vize/ klasörünü sunar)
//   node scripts/sunucu.js --port 9000 --root ..
// Yalnızca 127.0.0.1'e bağlanır; klasör dışına çıkan yollar reddedilir.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve, sep } from 'node:path';

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : dflt;
};
const ROOT = resolve(opt('--root', new URL('..', import.meta.url).pathname));
const PORT = Number(opt('--port', process.env.PORT ?? 8327));
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.pdf': 'application/pdf', '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8', '.log': 'text/plain; charset=utf-8', '.fa': 'text/plain; charset=utf-8',
  '.fasta': 'text/plain; charset=utf-8', '.tsv': 'text/plain; charset=utf-8', '.py': 'text/plain; charset=utf-8',
  '.sh': 'text/plain; charset=utf-8', '.ico': 'image/x-icon', '.woff2': 'font/woff2',
};

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    let path = normalize(join(ROOT, decodeURIComponent(url.pathname)));
    if (path !== ROOT && !path.startsWith(ROOT + sep)) {
      res.writeHead(403).end('yasak');
      return;
    }
    let st = await stat(path).catch(() => null);
    if (st?.isDirectory()) {
      if (!url.pathname.endsWith('/')) {
        res.writeHead(301, { Location: url.pathname + '/' + url.search }).end();
        return;
      }
      path = join(path, 'index.html');
      st = await stat(path).catch(() => null);
    }
    if (!st?.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('bulunamadı: ' + url.pathname);
      return;
    }
    const body = await readFile(path);
    res.writeHead(200, { 'Content-Type': TYPES[extname(path).toLowerCase()] ?? 'application/octet-stream', 'Cache-Control': 'no-cache' });
    res.end(req.method === 'HEAD' ? undefined : body);
  } catch (err) {
    res.writeHead(500).end(String(err?.message ?? err));
  }
});
server.listen(PORT, '127.0.0.1', () => {
  process.stdout.write(`Sunucu: http://localhost:${PORT}/  (kök: ${ROOT})\n  Atölye: http://localhost:${PORT}/web/\n  Site:   http://localhost:${PORT}/site/\n  Sunum:  http://localhost:${PORT}/docs/sunum/\n`);
});
