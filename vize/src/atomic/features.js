// Atomların seçim özelliklerinde ortak kullanılan küçük yardımcılar.
// Özellik (feature) = girdi şeklinden hesaplanan, "kabaca kaç adım sürer" sayısı.
// Molekül her özelliği kalibrasyonla bulunan bir katsayıyla çarpıp toplar.

import { patternSigma } from '../functions/expect.js';

/**
 * Bütün atomlarda ortak özellikler:
 *   fixed       atom kurmanın sabit maliyeti (tablo ayırma vb.)
 *   base        metni kimliklere çevirme işi (n)
 *   perPattern  desen başına sabit iş (döngü kurma, tablo sıfırlama)
 *   out         tahmini eşleşme sayısı: rastgele metinde bir desen n/σe^m kez geçer;
 *               desenlerin yaklaşık yarısı metinden alındığı için + k/2
 */
export function common(shape) {
  const perPos = Math.pow(Math.max(shape.sigmaEff, 1.0001), -shape.mMin);
  return { fixed: 1, base: shape.n, perPattern: shape.k, out: shape.k * (0.5 + shape.n * perPos) };
}

/** Bir desen başına tablo kurma işi (tablo boyu × desen sayısı). */
export function tablePrep(shape) {
  return shape.k * (patternSigma(shape) + 1 + shape.mMean);
}

export { patternSigma };
