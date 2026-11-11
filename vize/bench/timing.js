// Zaman ölçümü.
// Kurallar (ödev, Görev 4): her ölçümden önce ısınma turu, en az 3 tekrarın medyanı.
// Ek: tek çalıştırma 5 ms'den kısaysa, aynı iş bir blok içinde birkaç kez
// çalıştırılıp ortalaması alınır (çok kısa sürelerde saat çözünürlüğü ve
// gürültü sonucu bozmasın diye). Her tekrardan önce (varsa) çöp toplayıcı çağrılır.

import os from 'node:os';

export function now() {
  return Number(process.hrtime.bigint()) / 1e6; // ms
}

export function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
}

/**
 * fn'in süresini ölçer.
 * @returns {{ ms: number, samples: number[], inner: number, reps: number }}
 */
export function measure(fn, { reps = 3, warmup = 1, minBlockMs = 5, maxInner = 2000 } = {}) {
  let first = 0;
  for (let w = 0; w < warmup; w++) {
    const t0 = now();
    fn();
    first = now() - t0;
  }
  const inner = first >= minBlockMs ? 1 : Math.min(maxInner, Math.ceil(minBlockMs / Math.max(first, 1e-3)));
  const samples = [];
  for (let r = 0; r < reps; r++) {
    globalThis.gc?.();
    const t0 = now();
    for (let i = 0; i < inner; i++) fn();
    samples.push((now() - t0) / inner);
  }
  return { ms: median(samples), samples, inner, reps };
}

export function machineInfo() {
  const cpus = os.cpus();
  return {
    cpu: cpus[0]?.model ?? 'bilinmiyor',
    cores: cpus.length,
    memoryGB: Math.round(os.totalmem() / 2 ** 30),
    node: process.version,
    platform: `${os.platform()} ${os.release()}`,
    gcExposed: typeof globalThis.gc === 'function',
    date: new Date().toISOString(),
  };
}
