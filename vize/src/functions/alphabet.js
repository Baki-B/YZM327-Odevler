// Alfabe küçültme (alphabet reduction).
//
// Fikir: Desenlerde geçen her farklı karaktere 1'den başlayan küçük bir numara
// (kimlik) verilir. Desenlerde hiç geçmeyen bütün karakterler 0 olur. Böylece
// kaydırma tabloları 65 536 yerine (σ_desen + 1) elemanlı küçük dizilere sığar.
// İki farklı metin karakterinin ikisi de 0 olsa bile sonuç bozulmaz, çünkü 0
// hiçbir desen karakteriyle eşleşmez.
//
// ignoreCase açıksa yalnızca ASCII a–z, A–Z ile aynı kimliği alır (sözleşme 4.2).

const UNIT_COUNT = 0x10000; // UTF-16 kod birimi sayısı

/** ASCII küçük harfi büyüğe çevirir; diğer bütün kod birimlerine dokunmaz. */
export function foldAsciiUnit(code) {
  return code >= 97 && code <= 122 ? code - 32 : code;
}

/** Bir dizginin yalnızca ASCII harflerini büyük harfe çevirir (hazır işlev kullanmadan). */
export function foldAscii(str) {
  let out = '';
  let chunk = [];
  for (let i = 0; i < str.length; i++) {
    chunk.push(foldAsciiUnit(str.charCodeAt(i)));
    if (chunk.length === 8192) {
      out += String.fromCharCode.apply(null, chunk);
      chunk = [];
    }
  }
  if (chunk.length) out += String.fromCharCode.apply(null, chunk);
  return out;
}

/**
 * Desenlerden alfabe tablosu kurar.
 * @returns {{ map: Uint16Array, size: number }} map[kod birimi] = kimlik (0 = desende yok);
 *          size = en büyük kimlik + 1 (0 dahil).
 */
export function buildAlphabet(patterns, ignoreCase) {
  const map = new Uint16Array(UNIT_COUNT);
  let next = 1;
  for (const p of patterns) {
    for (let i = 0; i < p.length; i++) {
      let c = p.charCodeAt(i);
      if (ignoreCase) c = foldAsciiUnit(c);
      if (map[c] === 0) map[c] = next++;
    }
  }
  if (ignoreCase) {
    // Küçük harfler büyük harflerle aynı kimliği paylaşır.
    for (let c = 97; c <= 122; c++) map[c] = map[c - 32];
  }
  return { map, size: next };
}

/** Bir dizgiyi kimlik dizisine çevirir. `extra` kadar boş yer sona eklenir (sentinel için). */
export function encode(str, map, extra = 0) {
  const n = str.length;
  const out = new Uint16Array(n + extra);
  for (let i = 0; i < n; i++) out[i] = map[str.charCodeAt(i)];
  return out;
}
