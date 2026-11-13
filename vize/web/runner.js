// Çalıştırıcı: önce modül Web Worker'ı dener; tarayıcı desteklemiyorsa ya da Worker
// açılamazsa aynı çekirdeği ana iş parçacığında çalıştırır (motor düğümler arasında
// setTimeout ile arayüze nefes aldırır).
let worker = null;
let mode = 'yok';
let seq = 0;
const pending = new Map();

function startWorker() {
  return new Promise((resolve) => {
    try {
      const w = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
      const timer = setTimeout(() => resolve(null), 4000);
      w.onmessage = (ev) => {
        const m = ev.data;
        if (m.ready) {
          clearTimeout(timer);
          resolve(w);
          return;
        }
        const p = pending.get(m.id);
        if (!p) return;
        if (m.progress) p.onProgress?.(m.progress);
        else {
          pending.delete(m.id);
          if (m.error) p.reject(new Error(m.error));
          else p.resolve(m.result);
        }
      };
      w.onerror = () => {
        clearTimeout(timer);
        resolve(null);
      };
    } catch {
      resolve(null);
    }
  });
}

let ready = null;
export function init() {
  ready ??= startWorker().then((w) => {
    worker = w;
    mode = w ? 'worker' : 'ana iş parçacığı';
    return mode;
  });
  return ready;
}

export function runnerMode() {
  return mode;
}

async function call(cmd, payload, onProgress) {
  await init();
  if (worker) {
    const id = ++seq;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject, onProgress });
      worker.postMessage({ id, cmd, payload });
    });
  }
  const core = await import('./core.js');
  if (cmd === 'run') return core.runSerialized(payload, (node, st) => onProgress?.({ node, ...st }));
  await new Promise((r) => setTimeout(r, 0));
  return core.raceNode(payload.node, payload.reps);
}

export const runWorkflowRemote = (data, onProgress) => call('run', data, onProgress);
export const raceRemote = (node, reps = 5) => call('race', { node, reps });
