// FASTA okuyucu.
// ">" ile başlayan satır yeni bir kaydın başlığıdır; sonraki satırlar dizinin
// parçalarıdır ve boşluklar atılarak birleştirilir. Boş satırlar yok sayılır.

/** FASTA metnini FASTA.Entry dizisine çevirir: [{ header: ">...", seq: "..." }]. */
export function parseFasta(text) {
  return [...readFasta(text.split('\n'))];
}

/** Satır satır okuyan üreteç; büyük dosyada bile kayıtları teker teker verir. */
export function* readFasta(lines) {
  let header = null;
  let parts = [];
  for (let raw of lines) {
    const line = raw.trim();
    if (line === '') continue;
    if (line[0] === '>') {
      if (header !== null) yield { header, seq: parts.join('') };
      header = line;
      parts = [];
    } else {
      if (header === null) throw new SyntaxError('FASTA: ilk satır ">" ile başlayan bir başlık olmalı');
      parts.push(line.replace(/\s+/g, ''));
    }
  }
  if (header !== null) yield { header, seq: parts.join('') };
}

/** FASTA.Entry dizisini metne çevirir (satır uzunluğu `width`). */
export function formatFasta(entries, width = 60) {
  let out = '';
  for (const { header, seq } of entries) {
    out += (header[0] === '>' ? header : '>' + header) + '\n';
    for (let i = 0; i < seq.length; i += width) out += seq.slice(i, i + width) + '\n';
  }
  return out;
}
