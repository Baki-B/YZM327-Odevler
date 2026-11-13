// Örnek veri yükleyicisi, Node sürümü (testler ve scripts/paketler.js için).
// Tarayıcı sürümü web/samples.js'tedir; ikisi de catalog.js'teki SAMPLES tablosunu okur.
import { readFileSync } from 'node:fs';
import { SAMPLES } from './catalog.js';

const VIZE = new URL('../../', import.meta.url);

export async function loadSampleNode(name) {
  const s = SAMPLES[name];
  if (!s) throw new Error(`Bilinmeyen örnek: ${name}`);
  const text = readFileSync(new URL(s.url, VIZE), 'utf8');
  return s.kind === 'bundle' ? JSON.parse(text) : [{ path: s.path, text }];
}
