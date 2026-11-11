// Maliyet modeli.
//   tahmini süre (saniye) = Σ katsayı_f × özellik_f
// Özellikleri atom kendi verir (selection.features). Katsayılar kalibrasyonla
// bulunur; bulunmamışsa atomun selection.defaults değerleri kullanılır.

/** Bir atom için tahmini süreyi ve dayandığı sayıları hesaplar. */
export function estimateCost(Atom, shape, calibrated) {
  const sel = Atom.selection;
  const features = sel.features(shape);
  const coef = calibrated ?? sel.defaults;
  let seconds = 0;
  for (const [f, x] of Object.entries(features)) {
    const c = coef[f] ?? sel.defaults[f] ?? 0;
    seconds += c * x;
  }
  return { seconds, features, coefficients: calibrated ? 'calibrated' : 'defaults' };
}

/**
 * Negatif olmayan en küçük kareler (NNLS), göreli hatayla:
 *   en küçükle  Σ_i ((Σ_f c_f·x_if − t_i) / t_i)²   koşul: c_f ≥ 0
 * Süreler mikro saniyeden saniyeye kadar yayıldığı için mutlak hata yerine göreli
 * hata kullanılır; yoksa yalnızca en büyük vakalar uydurulur.
 * Yöntem: Lawson & Hanson (1974) etkin küme algoritması. Özellik sayısı küçük
 * (≤ 10) olduğu için normal denklemlerle (AᵀA) çözülür.
 */
export function fitNonNegative(rows, targets, offsets = null) {
  const F = rows[0].length;
  const N = rows.length;
  // offsets: tahmine eklenecek bilinen (sabitlenmiş) kısım; hedef t − offset olur.
  const b = targets.map((t, i) => (offsets ? 1 - offsets[i] / t : 1));
  // Satırları 1/t ile ağırlıklandır (göreli hata), sütunları birim boya getir.
  const A = rows.map((r, i) => r.map((x) => x / targets[i]));
  const scale = new Array(F).fill(0);
  for (let f = 0; f < F; f++) {
    let s = 0;
    for (let i = 0; i < N; i++) s += A[i][f] * A[i][f];
    scale[f] = s > 0 ? Math.sqrt(s) : 1;
    for (let i = 0; i < N; i++) A[i][f] /= scale[f];
  }
  const G = Array.from({ length: F }, (_, a) => Array.from({ length: F }, (_, b) => {
    let s = 0;
    for (let i = 0; i < N; i++) s += A[i][a] * A[i][b];
    return s;
  }));
  const h = Array.from({ length: F }, (_, a) => {
    let s = 0;
    for (let i = 0; i < N; i++) s += A[i][a] * b[i];
    return s;
  });
  const x = new Array(F).fill(0);
  const passive = new Array(F).fill(false);
  const gradient = () => h.map((hv, a) => hv - G[a].reduce((s, g, b) => s + g * x[b], 0));
  const solvePassive = () => {
    const idx = [];
    for (let f = 0; f < F; f++) if (passive[f]) idx.push(f);
    const z = new Array(F).fill(0);
    const sol = solve(idx.map((a) => idx.map((b) => G[a][b] + (a === b ? 1e-12 : 0))), idx.map((a) => h[a]));
    idx.forEach((f, j) => (z[f] = sol[j]));
    return z;
  };
  for (let outer = 0; outer < 10 * F; outer++) {
    const w = gradient();
    let j = -1;
    for (let f = 0; f < F; f++) if (!passive[f] && w[f] > 1e-10 && (j === -1 || w[f] > w[j])) j = f;
    if (j === -1) break;
    passive[j] = true;
    for (let inner = 0; inner < 10 * F; inner++) {
      const z = solvePassive();
      let alpha = Infinity;
      for (let f = 0; f < F; f++) {
        if (passive[f] && z[f] <= 0) alpha = Math.min(alpha, x[f] / (x[f] - z[f]));
      }
      if (alpha === Infinity) {
        for (let f = 0; f < F; f++) x[f] = z[f];
        break;
      }
      for (let f = 0; f < F; f++) {
        x[f] += alpha * (z[f] - x[f]);
        if (passive[f] && x[f] <= 1e-15) {
          passive[f] = false;
          x[f] = 0;
        }
      }
    }
  }
  return x.map((v, f) => Math.max(0, v) / scale[f]);
}

/** Küçük doğrusal sistem: Gauss eleme, kısmi pivotlama. */
function solve(M, v) {
  const n = v.length;
  const a = M.map((row, i) => [...row, v[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(a[r][c]) > Math.abs(a[p][c])) p = r;
    [a[c], a[p]] = [a[p], a[c]];
    const d = a[c][c] || 1e-300;
    for (let r = 0; r < n; r++) {
      if (r === c) continue;
      const k = a[r][c] / d;
      for (let cc = c; cc <= n; cc++) a[r][cc] -= k * a[c][cc];
    }
  }
  return a.map((row, i) => row[n] / (row[i] || 1e-300));
}
