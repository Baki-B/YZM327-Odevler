// Aho-Corasick (Aho & Corasick 1975): bütün desenler için tek geçiş.
// Desenlerden bir harf ağacı (trie) kurulur, her düğüme "başarısızlık bağı"
// eklenir ve bunlardan tam bir otomat (DFA) çıkarılır. Metnin her karakteri
// otomatta tek bir adımdır; desen sayısı aramayı yavaşlatmaz.
// Karmaşıklık: ön işleme O(Σm · σ), arama O(n + eşleşme sayısı).

export function prepareAhoCorasick(patterns, sigma) {
  let total = 1;
  for (const p of patterns) total += p.length;

  const go = new Int32Array(total * sigma).fill(-1);
  const depth = new Int32Array(total);
  const word = new Int32Array(total).fill(-1); // bu düğümde biten benzersiz desen
  const fail = new Int32Array(total);
  const dict = new Int32Array(total).fill(-1); // en yakın "desen biten" başarısızlık atası
  let states = 1;

  // 1) Harf ağacı
  for (let u = 0; u < patterns.length; u++) {
    const p = patterns[u];
    let s = 0;
    for (let i = 0; i < p.length; i++) {
      const idx = s * sigma + p[i];
      if (go[idx] === -1) {
        depth[states] = depth[s] + 1;
        go[idx] = states++;
      }
      s = go[idx];
    }
    word[s] = u; // desenler benzersiz olduğundan her düğümde en fazla bir desen biter
  }

  // 2) Genişlik öncelikli dolaşma: başarısızlık bağları ve tam otomat
  const queue = new Int32Array(states);
  let head = 0;
  let tail = 0;
  for (let c = 0; c < sigma; c++) {
    const t = go[c];
    if (t === -1) go[c] = 0;
    else {
      fail[t] = 0;
      queue[tail++] = t;
    }
  }
  while (head < tail) {
    const s = queue[head++];
    const f = fail[s];
    dict[s] = word[f] !== -1 ? f : dict[f];
    const row = s * sigma;
    const frow = f * sigma;
    for (let c = 0; c < sigma; c++) {
      const t = go[row + c];
      if (t === -1) go[row + c] = go[frow + c];
      else {
        fail[t] = go[frow + c];
        queue[tail++] = t;
      }
    }
  }
  return { go, depth, word, dict, sigma, states };
}

export function searchAhoCorasick(prep, text, n, hits) {
  const { go, depth, word, dict, sigma } = prep;
  let s = 0;
  for (let i = 0; i < n; i++) {
    s = go[s * sigma + text[i]];
    let o = word[s] !== -1 ? s : dict[s];
    while (o !== -1) {
      hits.add(word[o], i - depth[o] + 1);
      o = dict[o];
    }
  }
}
