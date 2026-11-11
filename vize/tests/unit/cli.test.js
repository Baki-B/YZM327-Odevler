// Komut satırı uçtan uca testleri: bin/ios.js alt süreç olarak çalıştırılır.
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync, mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { oracle, assertSameMatches } from './helpers.js';
import { parseFasta } from '../../src/fasta.js';

const BIN = fileURLToPath(new URL('../../bin/ios.js', import.meta.url));
const LAMBDA = readFileSync(new URL('../data/lambda_NC_001416.fa', import.meta.url), 'utf8');

function ios(args, input = '') {
  const r = spawnSync(process.execPath, [BIN, ...args], { input, encoding: 'utf8' });
  return { code: r.status, out: r.stdout, err: r.stderr };
}

describe('bin/ios.js', () => {
  test('run: stdout yalnızca JSONL, oracle ile aynı; karar özeti stderr\'de', () => {
    const r = ios(['run', 'ExactMatch', '--patterns', 'GATC,GGATCC', '--strategy', 'auto'], LAMBDA);
    assert.equal(r.code, 0, r.err);
    const lines = r.out.trimEnd().split('\n').map((l) => JSON.parse(l));
    assertSameMatches(lines, oracle({ patterns: ['GATC', 'GGATCC'] }, parseFasta(LAMBDA)));
    assert.match(r.err, /seçilen: \w+Search/);
  });
  test('run: --ignoreCase ve bir atomun adıyla çalıştırma', () => {
    const input = '>a\nacgtACGT\n>b\nTTacg\n';
    const r1 = ios(['run', 'ExactMatch', '--patterns', 'ACG', '--ignoreCase'], input);
    const r2 = ios(['run', 'KmpSearch', '--patterns', 'ACG', '--ignoreCase'], input);
    assert.equal(r1.out, r2.out);
    assert.equal(r1.out.trimEnd().split('\n').length, 3);
    assert.match(r2.err, /KmpSearch/);
  });
  test('explain: yalnızca kararı JSON olarak yazar', () => {
    const r = ios(['explain', '--patterns', 'ACGT,GGCC'], LAMBDA);
    assert.equal(r.code, 0, r.err);
    const rec = JSON.parse(r.out);
    assert.deepEqual(Object.keys(rec), ['requested', 'selected', 'shape', 'estimates', 'why']);
    assert.equal(rec.shape.n, 48502);
  });
  test('hatalar: bilinmeyen strateji, boş desen, bilinmeyen komut', () => {
    const a = ios(['run', 'ExactMatch', '--patterns', 'A', '--strategy', 'Yok'], '>x\nA\n');
    assert.equal(a.code, 1);
    assert.match(a.err, /Geçerli seçenekler: auto, NaiveSearch/);
    assert.equal(ios(['run', 'ExactMatch'], '>x\nA\n').code, 1);
    assert.equal(ios(['ucur'], '').code, 2);
    assert.equal(ios(['run', 'ExactMatch', '--patterns'], '').code, 2);
    assert.equal(a.out, '');
  });
  test('scan: klasörde TODO ve gizli bilgi bulur, --fail ile çıkış kodu 1', () => {
    const dir = mkdtempSync(join(tmpdir(), 'ios-scan-'));
    mkdirSync(join(dir, 'src'));
    mkdirSync(join(dir, 'node_modules'));
    writeFileSync(join(dir, 'src', 'a.py'), 'x = 1\n# TODO: sil\nAPI_KEY = "abc"\n');
    writeFileSync(join(dir, 'node_modules', 'b.js'), '// TODO burası taranmaz\n');
    writeFileSync(join(dir, 'ikili.bin'), Buffer.from([0, 1, 2, 84, 79, 68, 79]));
    const r = spawnSync(process.execPath, [BIN, 'scan', '--preset', 'todo', '--json', '.'], { cwd: dir, encoding: 'utf8' });
    assert.equal(r.status, 0, r.stderr);
    const found = r.stdout.trimEnd().split('\n').map((l) => JSON.parse(l));
    assert.deepEqual(found.map((f) => [f.file, f.line, f.column, f.pattern]), [[join('src', 'a.py'), 2, 3, 'TODO']]);
    const s = spawnSync(process.execPath, [BIN, 'scan', '--preset', 'secrets', '--fail', 'src'], { cwd: dir, encoding: 'utf8' });
    assert.equal(s.status, 1);
    assert.match(s.stdout, /a\.py:3:1: api_key/);
  });
  test('list ve help', () => {
    assert.match(ios(['list']).out, /HorspoolSearch/);
    assert.match(ios(['help']).out, /Kullanım/);
  });
});
