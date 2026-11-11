// Beklenen kayma miktarları (maliyet modelinin "özellik" hesapları için).
//
// Bu formüller rastgele (tekdüze dağılımlı) metin ve desen varsayar. Gerçek
// metinde harfler eşit sıklıkta değildir; bu yüzden σ yerine "etkin alfabe
// büyüklüğü" σe = 1 / Σ p_i² kullanılır (iki rastgele harfin aynı çıkma
// olasılığının tersi). Örnek: DNA'da 4 harf eşit sıklıktaysa σe = 4; İngilizce
// metinde 27 farklı karakter olsa da σe ≈ 15'tir.

/**
 * Horspool'un bir pencerede beklenen kayması.
 * Metin karakterinin desenin son m−1 karakteri içindeki en sağdaki yerine
 * uzaklığı d ise kayma d'dir; hiç yoksa m'dir.
 *   E = Σ_{d=1}^{m−1} d·(1/s)·(1−1/s)^{d−1} + m·(1−1/s)^{m−1}
 */
export function horspoolShift(m, s) {
  if (m <= 1) return 1;
  if (s <= 1) return 1;
  const p = 1 / s;
  const q = 1 - p;
  let e = 0;
  let qp = 1; // q^{d-1}
  const limit = Math.min(m - 1, 5000);
  for (let d = 1; d <= limit; d++) {
    e += d * p * qp;
    qp *= q;
  }
  // limit < m−1 ise kalan terimler çok küçüktür; m·q^{m−1} terimi eklenir.
  e += m * Math.pow(q, m - 1);
  return Math.max(1, e);
}

/** q-gram (q harflik parça) üzerinden kayan Horspool'un beklenen kayması. */
export function qgramShift(m, q, s) {
  if (q >= m) return 1;
  return horspoolShift(m - q + 1, Math.pow(Math.max(s, 1), q));
}

/** Bir sayıyı temsil etmek için gereken bit sayısı (en az 1). */
export function bitsFor(maxValue) {
  return Math.max(1, 32 - Math.clz32(maxValue));
}

/** Desen alfabesinin tahmini büyüklüğü: metnin alfabesinden ve desenlerin toplam uzunluğundan büyük olamaz. */
export function patternSigma(shape) {
  return Math.max(1, Math.min(shape.sigma, Math.round(shape.k * shape.mMean)));
}
