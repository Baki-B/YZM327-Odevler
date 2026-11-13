// Web Worker: uzun aramalar arayüzü dondurmasın diye iş akışı ayrı bir iş parçacığında çalışır.
import { runSerialized, raceNode } from './core.js';

self.onmessage = async (ev) => {
  const { id, cmd, payload } = ev.data;
  try {
    if (cmd === 'run') {
      const result = await runSerialized(payload, (node, state) => self.postMessage({ id, progress: { node, ...state } }));
      self.postMessage({ id, result });
    } else if (cmd === 'race') {
      self.postMessage({ id, result: raceNode(payload.node, payload.reps) });
    } else {
      throw new Error(`Bilinmeyen komut: ${cmd}`);
    }
  } catch (err) {
    self.postMessage({ id, error: err?.message ?? String(err) });
  }
};
self.postMessage({ ready: true });
