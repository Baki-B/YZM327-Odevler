#!/usr/bin/env node
// Komut satırı.
//   node bin/ios.js run ExactMatch --patterns ACGT,GGCC [--ignoreCase] [--strategy auto] < girdi.fasta > cikti.jsonl
//   node bin/ios.js explain --patterns ACGT,GGCC [--ignoreCase] [--strategy auto] < girdi.fasta
//   node bin/ios.js scan (--patterns A,B | --preset todo|secrets|banned-api|errors) [--ignoreCase] [--json] [--fail] <dosya|klasör>...
//   node bin/ios.js list
// run: stdout'a yalnızca JSONL (satır başına bir Sequence.Match); karar özeti stderr'e.

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { parseFasta } from '../src/fasta.js';
import { ExactMatch } from '../src/molecules/ExactMatch.js';
import { registry } from '../src/registry.js';
import { CodeScan } from '../src/workflows/CodeScan.js';
import { PRESETS } from '../src/workflows/presets.js';

const USAGE = `Kullanım:
  ios run ExactMatch --patterns ACGT,GGCC [--ignoreCase] [--strategy auto|<atom>] < girdi.fasta > cikti.jsonl
  ios run <AtomAdı> --patterns ACGT,GGCC [--ignoreCase] < girdi.fasta
  ios explain --patterns ACGT,GGCC [--ignoreCase] [--strategy auto] < girdi.fasta
  ios scan (--patterns A,B | --preset ${Object.keys(PRESETS).join('|')}) [--ignoreCase] [--strategy auto] [--json] [--fail] <dosya|klasör>...
  ios list`;

class UsageError extends Error {}

function parseArgs(argv) {
  const opts = { patterns: [], ignoreCase: false, strategy: 'auto', json: false, fail: false, preset: null, quiet: false };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const value = () => {
      if (i + 1 >= argv.length) throw new UsageError(`${a} bir değer bekliyor`);
      return argv[++i];
    };
    if (a === '--patterns' || a === '-p') opts.patterns.push(...value().split(',').filter((s) => s !== ''));
    else if (a === '--pattern') opts.patterns.push(value());
    else if (a === '--ignoreCase' || a === '-i') opts.ignoreCase = true;
    else if (a === '--strategy' || a === '-s') opts.strategy = value();
    else if (a === '--preset') opts.preset = value();
    else if (a === '--json') opts.json = true;
    else if (a === '--fail') opts.fail = true;
    else if (a === '--quiet' || a === '-q') opts.quiet = true;
    else if (a === '--help' || a === '-h') opts.help = true;
    else if (a.startsWith('--')) throw new UsageError(`Bilinmeyen seçenek: ${a}`);
    else positional.push(a);
  }
  return { opts, positional };
}

function readStdinFasta() {
  return parseFasta(readFileSync(0, 'utf8'));
}

/** Çıktıyı küçük parçalar halinde yazar (büyük çıktıda bellek ve hız için). */
function writeLines(lines) {
  let buf = '';
  for (const line of lines) {
    buf += line + '\n';
    if (buf.length > 1 << 16) {
      process.stdout.write(buf);
      buf = '';
    }
  }
  if (buf) process.stdout.write(buf);
}

function cmdRun(component, opts) {
  if (!component) throw new UsageError('run: bileşen adı gerekli (ör. ExactMatch)');
  let strategy = opts.strategy;
  if (component !== 'ExactMatch') {
    if (!registry.has(component)) {
      throw new Error(`Bilinmeyen bileşen "${component}". Geçerli: ExactMatch, ${registry.names().join(', ')}`);
    }
    strategy = component;
  }
  const em = new ExactMatch({ patterns: opts.patterns, ignoreCase: opts.ignoreCase, strategy });
  const entries = readStdinFasta();
  writeLines((function* () {
    for (const m of em.run(entries)) yield JSON.stringify(m);
  })());
  if (!opts.quiet) process.stderr.write(`[ExactMatch] seçilen: ${em.record.selected} — ${em.record.why}\n`);
}

function cmdExplain(opts) {
  const em = new ExactMatch({ patterns: opts.patterns, ignoreCase: opts.ignoreCase, strategy: opts.strategy });
  const entries = readStdinFasta();
  em.decide(entries[0] ?? { header: '', seq: '' });
  process.stdout.write(JSON.stringify(em.record, null, 2) + '\n');
}

const SKIP_DIRS = new Set(['.git', 'node_modules', '__pycache__', '_site', '.venv', 'venv', 'dist', 'build']);

function* walk(path, root) {
  const st = statSync(path);
  if (st.isDirectory()) {
    for (const name of readdirSync(path).sort()) {
      if (SKIP_DIRS.has(name) || name.startsWith('.')) continue;
      yield* walk(join(path, name), root);
    }
  } else if (st.isFile() && st.size <= 5 * 1024 * 1024) {
    const buf = readFileSync(path);
    if (buf.subarray(0, 8192).includes(0)) return; // ikili dosya
    yield { path: relative(root, path) || path, text: buf.toString('utf8') };
  }
}

function cmdScan(targets, opts) {
  let { patterns, ignoreCase } = opts;
  if (opts.preset) {
    const p = PRESETS[opts.preset];
    if (!p) throw new UsageError(`Bilinmeyen hazır küme "${opts.preset}". Geçerli: ${Object.keys(PRESETS).join(', ')}`);
    patterns = [...p.patterns, ...patterns];
    ignoreCase = ignoreCase || p.ignoreCase;
  }
  if (targets.length === 0) throw new UsageError('scan: en az bir dosya ya da klasör verin');
  const scan = new CodeScan({ patterns, ignoreCase, strategy: opts.strategy });
  const sources = (function* () {
    for (const t of targets) yield* walk(t, process.cwd());
  })();
  let count = 0;
  writeLines((function* () {
    for (const f of scan.run(sources)) {
      count++;
      yield opts.json ? JSON.stringify(f) : `${f.file}:${f.line}:${f.column}: ${f.pattern}`;
    }
  })());
  if (!opts.quiet) process.stderr.write(`[scan] ${count} bulgu; seçilen atom: ${scan.record.selected}\n`);
  if (opts.fail && count > 0) process.exitCode = 1;
}

function cmdList() {
  for (const name of registry.names()) {
    const A = registry.get(name);
    const auto = A.selection ? 'auto adayı' : 'yalnızca adıyla';
    process.stdout.write(`${name.padEnd(20)} ${A.manifest.title} [${auto}] ${A.manifest.references.join('; ')}\n`);
  }
}

function main(argv) {
  const [cmd, ...rest] = argv;
  const { opts, positional } = parseArgs(rest);
  if (!cmd || cmd === 'help' || opts.help) {
    process.stdout.write(USAGE + '\n');
    return;
  }
  switch (cmd) {
    case 'run': return cmdRun(positional[0], opts);
    case 'explain': return cmdExplain(opts);
    case 'scan': return cmdScan(positional, opts);
    case 'list': return cmdList();
    default: throw new UsageError(`Bilinmeyen komut: ${cmd}`);
  }
}

try {
  main(process.argv.slice(2));
} catch (err) {
  process.stderr.write(`hata: ${err.message}\n`);
  if (err instanceof UsageError) process.stderr.write(USAGE + '\n');
  process.exitCode = err instanceof UsageError ? 2 : 1;
}
