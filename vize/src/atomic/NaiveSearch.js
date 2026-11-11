// Kaba kuvvet referans uygulama (test oracle'ı).
//
// Diğer atomlardan BAĞIMSIZ olsun diye ortak alfabe kodlamasını kullanmaz:
// doğrudan JavaScript dizgileri üzerinde indexOf ile arar. Hazır arama işlevlerini
// yalnızca bu dosya kullanabilir (ödev 4.3). Hızlı olması beklenmez; doğru olması beklenir.

import { ExactSearchAtom, TASK, validateEntry } from './ExactSearchAtom.js';

/** Yalnızca ASCII a–z → A–Z (alphabet.js'ten bağımsız, ayrı bir yazım). */
function upperAscii(s) {
  return s.replace(/[a-z]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 32));
}

export class NaiveSearch extends ExactSearchAtom {
  static manifest = {
    name: 'NaiveSearch', version: '0.1.0', kind: 'atom', task: TASK,
    title: 'Exact match (naive, test oracle)', references: [],
  };
  // selection yok: molekül "auto" kipinde bu atomu aday saymaz; adıyla seçilebilir.
  static selection = null;

  *process(entry) {
    validateEntry(entry);
    const text = this.ignoreCase ? upperAscii(entry.seq) : entry.seq;
    const found = [];
    for (let idx = 0; idx < this.patterns.length; idx++) {
      const pat = this.ignoreCase ? upperAscii(this.patterns[idx]) : this.patterns[idx];
      let pos = text.indexOf(pat);
      while (pos !== -1) {
        found.push([pos, idx]);
        pos = text.indexOf(pat, pos + 1); // örtüşen eşleşmeler için bir sonraki konumdan devam
      }
    }
    found.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    for (const [position, idx] of found) {
      const pattern = this.patterns[idx];
      yield { header: entry.header, pattern, position, length: pattern.length };
    }
  }
}
