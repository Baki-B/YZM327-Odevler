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
 * Yöntem: koordinat iniş (her katsayıyı sırayla, sıfırın altına inmeden en iyi
 * değerine çek). Az sayıda özellik (≤ 6) için yeterince hızlı ve kararlıdır.
 */
export function fitNonNegative(rows, targets, iterations = 3000) {
  const F = rows[0].length;
  const N = rows.length;
  // Ölçekleme: her sütunu göreli hata ağırlığıyla normalleştir.
  const A = rows.map((r, i) => r.map((x) => x / targets[i]));
  const b = new Array(N).fill(1);
  const scale = new Array(F).fill(0);
  for (let f = 0; f < F; f++) {
    let s = 0;
    for (let i = 0; i < N; i++) s += A[i][f] * A[i][f];
    scale[f] = s > 0 ? Math.sqrt(s) : 1;
    for (let i = 0; i < N; i++) A[i][f] /= scale[f];
  }
  const c = new Array(F).fill(0);
  const resid = b.slice(); // b − A·c
  for (let it = 0; it < iterations; it++) {
    let change = 0;
    for (let f = 0; f < F; f++) {
      let num = 0;
      for (let i = 0; i < N; i++) num += A[i][f] * resid[i];
      const next = Math.max(0, c[f] + num); // sütun normu 1 olduğu için adım = num
      const d = next - c[f];
      if (d !== 0) {
        for (let i = 0; i < N; i++) resid[i] -= d * A[i][f];
        c[f] = next;
        change = Math.max(change, Math.abs(d));
      }
    }
    if (change < 1e-12) break;
  }
  return c.map((x, f) => x / scale[f]);
}
