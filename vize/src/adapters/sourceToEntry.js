// Uyarlayıcı (Adapter deseni): bir kaynak kod ya da log dosyasını FASTA.Entry'ye çevirir.
//
// Atomlar FASTA.Entry bekler: { header: ">...", seq: "..." }. Bir dosyayı bu
// biçime sokarsak, hiçbir atoma dokunmadan aynı arama altyapısını yazılım
// mühendisliği verisinde kullanabiliriz.
// Not: FASTA'da seq boşluk içermez; kaynak kodda ise boşluk ve satır sonu
// anlamlıdır, bu yüzden metin olduğu gibi bırakılır. Atomlar boşluk içeren
// metinde de doğru çalışır (testlerle gösterildi). Satır sonları \r\n ise
// konumlar yine dosyadaki UTF-16 indeksidir.

/** { path, text } → FASTA.Entry */
export function sourceToEntry(source) {
  if (!source || typeof source.path !== 'string' || typeof source.text !== 'string') {
    throw new TypeError('Kaynak { path: string, text: string } olmalı');
  }
  return { header: '>' + source.path, seq: source.text };
}

/** Satır başlarının konumları (satır/sütun hesabı için). Hazır arama işlevi kullanmaz. */
export function lineStarts(text) {
  const starts = [0];
  for (let i = 0; i < text.length; i++) if (text.charCodeAt(i) === 10) starts.push(i + 1);
  return starts;
}

/** Konum → { line, column } (ikisi de 1'den başlar). İkili arama. */
export function toLineColumn(starts, position) {
  let lo = 0;
  let hi = starts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (starts[mid] <= position) lo = mid;
    else hi = mid - 1;
  }
  return { line: lo + 1, column: position - starts[lo] + 1 };
}
