// CodeScan: ExactMatch molekülünü kaynak kod / log dosyalarında kullanan küçük iş akışı.
//
//   dosyalar ──(sourceToEntry)──▶ FASTA.Entry ──(ExactMatch)──▶ Sequence.Match ──▶ { file, line, column, pattern }
//
// Dosya okuma burada değil, komut satırında (bin/ios.js) yapılır; bu modül saf kalır.

import { ExactMatch } from '../molecules/ExactMatch.js';
import { sourceToEntry, lineStarts, toLineColumn } from '../adapters/sourceToEntry.js';

export class CodeScan {
  constructor({ patterns, ignoreCase = false, strategy = 'auto' }, options = {}) {
    this.molecule = new ExactMatch({ patterns, ignoreCase, strategy }, options);
  }

  get record() {
    return this.molecule.record;
  }

  /** sources: { path, text } nesnelerinin akışı. Her eşleşme için bir bulgu üretir. */
  *run(sources) {
    const index = new Map(); // header → satır başları
    const entries = (function* () {
      for (const src of sources) {
        const entry = sourceToEntry(src);
        index.set(entry.header, { path: src.path, starts: lineStarts(src.text) });
        yield entry;
      }
    })();
    for (const match of this.molecule.run(entries)) {
      const file = index.get(match.header);
      const { line, column } = toLineColumn(file.starts, match.position);
      yield { file: file.path, line, column, pattern: match.pattern, position: match.position };
    }
  }
}
