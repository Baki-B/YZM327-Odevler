// Tohumlu (seeded) sentetik veri üretici.
// Aynı tohum (seed) her zaman aynı veriyi verir: ölçümler ve testler tekrarlanabilir.
//
// Alfabeler:
//   dna      A C G T, eşit olasılık
//   protein  20 amino asit, doğadaki yaklaşık sıklıklarıyla (UniProt ortalaması)
//   text     İngilizce benzeri: sık kelimelerden cümleler
//   binary   a b
//   code     bu deponun kendi kaynak kodundan rastgele satır blokları (bench/corpus/kod.txt)
//   log      sentetik uygulama logu: zaman damgası, düzey, modül, ileti
//   repeat   tek bir kısa birimin tekrarı (ör. ATATAT…), en kötü durumlar için

import { readFileSync } from 'node:fs';

/** mulberry32: küçük, hızlı, tohumlu rastgele sayı üretici. [0, 1) döndürür. */
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const AA = 'ACDEFGHIKLMNPQRSTVWY';
// UniProtKB/Swiss-Prot amino asit sıklıkları (%), AA sırasıyla
const AA_FREQ = [8.25, 1.38, 5.46, 6.72, 3.86, 7.07, 2.27, 5.91, 5.80, 9.65, 2.41, 4.06, 4.74, 3.93, 5.53, 6.64, 5.35, 6.86, 1.10, 2.92];

const WORDS = ('the of and to in a is that for it as was with be by on not he this are or his from at which but have ' +
  'an they you were their one all we can her has there been if more when will would who so no data model time system ' +
  'pattern match search string text algorithm fast result value number first other new used each between').split(' ');

const LEVELS = ['INFO', 'INFO', 'INFO', 'DEBUG', 'DEBUG', 'WARN', 'ERROR'];
const MODULES = ['auth', 'db.pool', 'http.server', 'scheduler', 'cache', 'forum.oylama', 'forum.denetim', 'mailer'];
const MSGS = ['request handled', 'connection opened', 'connection closed', 'user login ok', 'user login failed',
  'cache miss for key', 'query took', 'retrying operation', 'vote recorded', 'topic created', 'timeout after',
  'session expired', 'payload too large', 'rate limit exceeded', 'job finished'];

function pickWeighted(r, cum) {
  const x = r() * cum[cum.length - 1];
  let i = 0;
  while (cum[i] < x) i++;
  return i;
}

let corpusCache = null;
export function codeCorpus() {
  if (corpusCache === null) corpusCache = readFileSync(new URL('./corpus/kod.txt', import.meta.url), 'utf8');
  return corpusCache;
}

export const ALPHABETS = ['dna', 'protein', 'text', 'binary', 'code', 'log', 'repeat'];

/** n karakterlik tohumlu metin üretir. */
export function makeText(alphabet, n, seed) {
  const r = rng(seed);
  const parts = [];
  let len = 0;
  const push = (s) => { parts.push(s); len += s.length; };
  switch (alphabet) {
    case 'dna': {
      const a = 'ACGT';
      const buf = new Array(n);
      for (let i = 0; i < n; i++) buf[i] = a[(r() * 4) | 0];
      return buf.join('');
    }
    case 'binary': {
      const buf = new Array(n);
      for (let i = 0; i < n; i++) buf[i] = r() < 0.5 ? 'a' : 'b';
      return buf.join('');
    }
    case 'protein': {
      const cum = [];
      AA_FREQ.reduce((s, f, i) => (cum[i] = s + f), 0);
      const buf = new Array(n);
      for (let i = 0; i < n; i++) buf[i] = AA[pickWeighted(r, cum)];
      return buf.join('');
    }
    case 'text': {
      while (len < n) {
        const w = WORDS[Math.floor(Math.pow(r(), 2) * WORDS.length)]; // baştaki kelimeler daha sık
        push(len === 0 || r() < 0.08 ? w[0].toUpperCase() + w.slice(1) : w);
        push(r() < 0.07 ? '. ' : ' ');
      }
      break;
    }
    case 'code': {
      const c = codeCorpus();
      while (len < n) {
        const start = Math.floor(r() * (c.length - 2000));
        push(c.slice(start, start + 200 + Math.floor(r() * 1800)));
      }
      break;
    }
    case 'log': {
      let t = Date.UTC(2026, 10, 1, 8, 0, 0) + Math.floor(r() * 1e6);
      while (len < n) {
        t += Math.floor(r() * 5000);
        const lvl = LEVELS[(r() * LEVELS.length) | 0];
        const mod = MODULES[(r() * MODULES.length) | 0];
        const msg = MSGS[(r() * MSGS.length) | 0];
        push(`${new Date(t).toISOString()} ${lvl.padEnd(5)} [${mod}] ${msg} id=${(r() * 1e6) | 0} ms=${(r() * 900) | 0}\n`);
      }
      break;
    }
    case 'repeat': {
      const unit = ['A', 'AT', 'ATG', 'AAAAT'][(r() * 4) | 0];
      while (len < n) push(unit);
      break;
    }
    default:
      throw new Error(`Bilinmeyen alfabe: ${alphabet}`);
  }
  return parts.join('').slice(0, n);
}

/**
 * k desen üretir; uzunluklar `lengths` dizisinden döngüyle alınır.
 * Desenlerin yarısı metinden kesilir (kesin geçer), yarısı metinden kesilip bir
 * karakteri değiştirilir (çoğunlukla geçmez ama metnin dağılımına benzer).
 */
export function makePatterns(text, k, lengths, seed) {
  const r = rng(seed);
  const n = text.length;
  const out = [];
  for (let i = 0; i < k; i++) {
    const m = Math.min(lengths[i % lengths.length], n);
    const start = Math.floor(r() * (n - m + 1));
    let p = text.slice(start, start + m);
    if (i % 2 === 1 && m > 0) {
      const j = Math.floor(r() * m);
      const src = text[Math.floor(r() * n)];
      p = p.slice(0, j) + (src === p[j] ? (p[j] === 'Z' ? 'Y' : 'Z') : src) + p.slice(j + 1);
    }
    if (p.length === 0) p = 'A';
    out.push(p);
  }
  return out;
}
