// Hazır paketleri Node'da iş akışı motoruyla çalıştırır ve her "Eşleşme → Bulgu" kutusunun
// bulgu sayısını aynı işi yapan komut satırının (bin/ios.js) çıktı satırı sayısıyla karşılaştırır.
// Kullanım (vize/ klasöründen): node scripts/paketler.js
import { execSync } from 'node:child_process';
import { createCatalog } from '../src/workflows/catalog.js';
import { deserializeWorkflow, runWorkflow } from '../src/workflows/engine.js';
import { PACKAGES } from '../src/workflows/packages.js';
import { loadSampleNode } from '../src/workflows/samplesNode.js';

const catalog = createCatalog();
const VIZE = new URL('..', import.meta.url).pathname;
let allOk = true;
for (const p of PACKAGES) {
  const wf = deserializeWorkflow(p.build(), catalog);
  const res = await runWorkflow(wf, catalog, { loadSample: loadSampleNode, now: () => performance.now(), yieldEvery: 0 });
  const counts = Object.fromEntries(wf.nodes.filter((n) => n.type === 'uyarlayici.bulgu').map((n) => [n.id, res.nodes[n.id].outputs.findings?.findings.length ?? null]));
  const cli = p.cli.map((cmd) => Number(execSync(`${cmd} 2>/dev/null | wc -l`, { cwd: VIZE, shell: '/bin/bash' }).toString().trim()));
  const selected = wf.nodes.filter((n) => n.type === 'molekul.ExactMatch').map((n) => `${n.id}: ${res.nodes[n.id].info?.record?.selected}`);
  const ok = res.ok && JSON.stringify(Object.values(counts)) === JSON.stringify(cli);
  allOk &&= ok;
  console.log(`${ok ? 'AYNI ' : 'FARK!'} ${p.id.padEnd(12)} atölye ${JSON.stringify(counts)}  komut satırı ${JSON.stringify(cli)}  seçilen [${selected.join('; ')}]`);
}
process.exitCode = allOk ? 0 : 1;
