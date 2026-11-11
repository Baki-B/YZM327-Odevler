// Mutasyon denetimi: koda bilerek küçük hatalar yerleştirip testlerin bunları
// yakalayıp yakalamadığına bakar. Her mutasyon projenin geçici bir kopyasında,
// tek başına uygulanır; `npm test` ile aynı komut çalıştırılır.
// Bir mutasyon "yakalandı" sayılır, eğer en az bir test başarısız olursa.
// Çıktı: docs/mutasyon.md
// Kullanım: npm run mutation

import { cpSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));

const MUTATIONS = [
  {
    file: 'src/functions/horspool.js', what: 'Horspool kayması bir fazla (m − i)',
    from: 'shift[p[i]] = m - 1 - i;', to: 'shift[p[i]] = m - i;',
  },
  {
    file: 'src/functions/kmp.js', what: 'KMP uyuşmazlıkta sınırı unutur (q = 0)',
    from: 'while (q > 0 && p[q] !== c) q = fail[q - 1];', to: 'while (q > 0 && p[q] !== c) q = 0;',
  },
  {
    file: 'src/functions/bm4dnaDs.js', what: 'bm4DNADS sentinel denetiminde < yerine <= (j > n)',
    from: 'if (j >= n) return;', to: 'if (j > n) return;',
  },
  {
    file: 'src/functions/bm4dnaHmbs.js', what: 'bm4DNAHMbs desende olmayan q-gram için m kadar kayar (ödevin ipucu hatası)',
    from: 'const dflt = m - q + 1;', to: 'const dflt = m;',
  },
  {
    file: 'src/functions/shiftOr.js', what: 'Shift-Or (m > 32) son pencereyi atlar',
    from: 'const limit = n - m + w;', to: 'const limit = n - m + w - 1;',
  },
  {
    file: 'src/functions/wuManber.js', what: 'Wu-Manber çakışmada en küçük kaymayı değil sonuncuyu tutar',
    from: 'if (sft < shift[h]) shift[h] = sft;', to: 'shift[h] = sft;',
  },
  {
    file: 'src/functions/ahoCorasick.js', what: 'Aho-Corasick sözlük bağlarını kurmaz (iç içe desenler kaçar)',
    from: 'dict[s] = word[f] !== -1 ? f : dict[f];', to: 'dict[s] = -1;',
  },
  {
    file: 'src/functions/hits.js', what: 'Sonuçlar sıralanmaz',
    from: 'const keys = this.keys.subarray(0, this.count).sort();', to: 'const keys = this.keys.subarray(0, this.count);',
  },
  {
    file: 'src/functions/alphabet.js', what: 'ignoreCase ASCII sınırı bir fazla ({ → [)',
    from: 'return code >= 97 && code <= 122 ? code - 32 : code;', to: 'return code >= 97 && code <= 123 ? code - 32 : code;',
  },
  {
    file: 'src/atomic/ExactSearchAtom.js', what: 'Metinden uzun bir desen varsa hiç aranmaz (minLen yerine maxLen)',
    from: 'if (n > 0 && this.minLen <= n) {', to: 'if (n > 0 && this.maxLen <= n) {',
  },
  {
    file: 'src/functions/boyerMoore.js', what: 'Boyer-Moore tam eşleşmeden sonra iyi sonek kayması yerine m kayar (örtüşen eşleşme kaçar)',
    from: 's += good[0];', to: 's += m;',
  },
  {
    file: 'src/molecules/ExactMatch.js', what: 'Molekül en pahalı atomu seçer (sıralama ters)',
    from: 'ranked.sort((a, b) => a.seconds - b.seconds);', to: 'ranked.sort((a, b) => b.seconds - a.seconds);',
  },
];

const work = mkdtempSync(join(tmpdir(), 'mutasyon-'));
cpSync(ROOT, work, { recursive: true, filter: (src) => !src.includes('/bench/results') && !src.includes('/.git') });

const run = () => {
  // Başarısız testlerin çıktısı büyük olabilir: tampon 256 MB. Normal tur ~4 sn sürer;
  // 90 sn'yi aşan tur sonsuz döngü sayılır ve süreç durdurulur.
  // (Varsayılan 1 MB tampon aşılınca alt süreçler boruyu açık tutup beklemeyi sonsuza uzatıyordu.)
  const r = spawnSync(process.execPath, ['--test', '--test-concurrency=2', 'tests/unit/**/*.test.js'], {
    cwd: work, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024, timeout: 90 * 1000, killSignal: 'SIGKILL',
  });
  const fail = Number((r.stdout.match(/^# fail (\d+)/m) ?? [])[1] ?? NaN);
  const pass = Number((r.stdout.match(/^# pass (\d+)/m) ?? [])[1] ?? NaN);
  const killed = r.status === null;
  const timedOut = r.error?.code === 'ETIMEDOUT';
  return { code: killed ? -1 : r.status, fail, pass, killed, timedOut, signal: r.signal };
};

const baseline = run();
if (baseline.code !== 0) throw new Error(`Değiştirilmemiş kopyada testler geçmiyor: ${JSON.stringify(baseline)}`);

const rows = [];
for (const mu of MUTATIONS) {
  const path = join(work, mu.file);
  const original = readFileSync(path, 'utf8');
  if (!original.includes(mu.from)) throw new Error(`${mu.file}: mutasyon yeri bulunamadı: ${mu.from}`);
  writeFileSync(path, original.replace(mu.from, mu.to));
  const r = run();
  writeFileSync(path, original);
  const how = r.timedOut
    ? 'testler 90 sn içinde bitmedi (sonsuz döngü), süreç durduruldu'
    : r.killed ? `süreç ${r.signal} sinyaliyle durdu (bellek sınırı)` : `${r.fail} test başarısız`;
  rows.push({ ...mu, caught: r.code !== 0, how });
  process.stderr.write(`${r.code !== 0 ? 'YAKALANDI ' : 'KAÇTI     '} ${mu.what} (${how})\n`);
}
rmSync(work, { recursive: true, force: true });

const caught = rows.filter((r) => r.caught).length;
let md = `# Mutasyon denetimi\n\n`;
md += `Koda bilerek küçük hatalar yerleştirildi; her biri projenin geçici bir kopyasında tek başına uygulanıp bütün birim testleri çalıştırıldı. `;
md += `Bir mutasyon, en az bir test başarısız olursa ya da testler sonsuz döngü yüzünden bitmezse "yakalandı" sayılır.\n\n`;
md += `Değiştirilmemiş kopyada: ${baseline.pass} test geçti, ${baseline.fail} başarısız. `;
md += `Sonuç: **${rows.length} mutasyonun ${caught}'i yakalandı.** Komut: \`npm run mutation\` (${new Date().toISOString().slice(0, 10)}).\n\n`;
md += '| # | Dosya | Yerleştirilen hata | Değişiklik | Yakalandı mı | Nasıl |\n|---:|---|---|---|---|---|\n';
rows.forEach((r, i) => {
  md += `| ${i + 1} | \`${r.file}\` | ${r.what} | \`${r.from}\` → \`${r.to}\` | ${r.caught ? 'evet' : '**hayır**'} | ${r.how} |\n`;
});
writeFileSync(join(ROOT, 'docs', 'mutasyon.md'), md);
process.stdout.write(md);
if (caught < rows.length) process.exitCode = 1;
