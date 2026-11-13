// Örnek veri yükleyicisi, tarayıcı sürümü (ana iş parçacığında ve Web Worker içinde çalışır).
// Dosyalar vize/ klasörüne göre göreli yollardan fetch ile okunur; bir kez okunan önbellekte kalır.
import { SAMPLES } from '../src/workflows/catalog.js';

const VIZE = new URL('../', import.meta.url);
const cache = new Map();

export async function loadSampleBrowser(name) {
  const s = SAMPLES[name];
  if (!s) throw new Error(`Bilinmeyen örnek: ${name}`);
  if (!cache.has(name)) {
    cache.set(name, (async () => {
      const res = await fetch(new URL(s.url, VIZE));
      if (!res.ok) throw new Error(`Örnek veri okunamadı (${s.url}: HTTP ${res.status}). Atölyeyi bir sunucudan açın: node scripts/sunucu.js`);
      return s.kind === 'bundle' ? res.json() : [{ path: s.path, text: await res.text() }];
    })());
  }
  try {
    return await cache.get(name);
  } catch (err) {
    cache.delete(name);
    throw err;
  }
}
