// Kesin kurallar (ödev 4.3): atomlarda hazır arama işlevi, ekrana yazma,
// dosya/ağ, saat ve rastgelelik kullanılmaz. Kaynak dosyalar taranarak denetlenir.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';

const ROOT = new URL('../../src/', import.meta.url);
const DIRS = ['functions', 'atomic'];
const ALLOWED = new Set(['atomic/NaiveSearch.js']); // test referansı hazır işlev kullanabilir

/** Yorumları çıkarır. */
function noComments(src) {
  return src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
}

/** Yorumları ve dizgi sabitlerini çıkarır; yalnızca kod kalır. */
function codeOnly(src) {
  return noComments(src)
    .replace(/`(?:\\.|[^`\\])*`/g, '``')
    .replace(/'(?:\\.|[^'\\])*'/g, "''")
    .replace(/"(?:\\.|[^"\\])*"/g, '""');
}

const RULES = [
  [/\.(indexOf|lastIndexOf|includes|startsWith|endsWith|search|match|matchAll|replace|replaceAll|split)\s*\(/, 'hazır arama işlevi'],
  [/\bRegExp\b/, 'RegExp'],
  // Bir regex sabiti ancak .test/.exec ya da yukarıdaki dizgi yöntemleriyle kullanılabilir.
  [/\.(test|exec)\s*\(/, 'düzenli ifade (regex) kullanımı'],
  [/\bconsole\./, 'console'],
  [/\brequire\s*\(|\bimport\s*\(/, 'dinamik içe aktarma'],
  [/\bfetch\s*\(|\bXMLHttpRequest\b|\bprocess\./, 'ağ / süreç erişimi'],
  [/\bMath\.random\b|\bDate\b|\bperformance\b/, 'rastgelelik / saat'],
];

// Bu kurallar dizgiler silinmeden (yalnızca yorumlar silinerek) uygulanır.
const IMPORT_RULES = [[/\bfrom\s+['"](node:[^'"]*|fs|path|os|http|https|net|child_process)['"]/, 'Node modülü içe aktarma']];

const files = [];
for (const d of DIRS) for (const f of readdirSync(new URL(d + '/', ROOT))) if (f.endsWith('.js')) files.push(`${d}/${f}`);

test('denetlenen dosya listesi boş değil', () => {
  assert.ok(files.length >= 18, files.join(', '));
});

for (const f of files) {
  if (ALLOWED.has(f)) continue;
  test(`yasaklı kullanım yok: src/${f}`, () => {
    const src = readFileSync(new URL(f, ROOT), 'utf8');
    const code = codeOnly(src);
    for (const [re, what] of RULES) {
      const m = code.match(re);
      assert.equal(m, null, `${what}: "${m?.[0]}"`);
    }
    for (const [re, what] of IMPORT_RULES) {
      const m = noComments(src).match(re);
      assert.equal(m, null, `${what}: "${m?.[0]}"`);
    }
  });
}

test('denetim gerçekten yakalıyor (negatif kontrol)', () => {
  const bad = ['process.stdout.write(1)', 'await fetch(u)', 't.indexOf(p)', 'new RegExp(p)', '/ab+c/g.test(s)', 'console.log(1)', "import fs from 'node:fs'", 'Math.random()'];
  for (const src of bad) {
    const hit = RULES.some(([re]) => re.test(codeOnly(src))) || IMPORT_RULES.some(([re]) => re.test(noComments(src)));
    assert.ok(hit, src);
  }
  assert.ok(!RULES.some(([re]) => re.test(codeOnly("// indexOf( yorumda\nconst a = 'console.log';\nconst x = a / b / c;"))));
});
