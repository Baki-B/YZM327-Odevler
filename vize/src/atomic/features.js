// Atomların seçim özelliklerinde ortak kullanılan küçük yardımcılar.
// Özellik (feature) = girdi şeklinden hesaplanan, "kabaca kaç adım sürer" sayısı.
// Molekül her özelliği kalibrasyonla bulunan bir katsayıyla çarpıp toplar.

import { patternSigma } from '../functions/expect.js';

/** Bütün atomlarda ortak: metni kimliklere çevirme ve çıktı üretme işi. */
export function common(shape) {
  return { base: shape.n, out: shape.n * shape.k / Math.pow(Math.max(shape.sigmaEff, 1.0001), shape.mMin) };
}

/** Bir desen başına tablo kurma işi (tablo boyu × desen sayısı). */
export function tablePrep(shape) {
  return shape.k * (patternSigma(shape) + 1 + shape.mMean);
}

export { patternSigma };
