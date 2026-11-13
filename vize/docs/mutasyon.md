# Mutasyon denetimi

Koda bilerek küçük hatalar yerleştirildi; her biri projenin geçici bir kopyasında tek başına uygulanıp bütün birim testleri çalıştırıldı. Bir mutasyon, en az bir test başarısız olursa ya da testler sonsuz döngü yüzünden bitmezse "yakalandı" sayılır.

Değiştirilmemiş kopyada: 360 test geçti, 0 başarısız. Sonuç: **12 mutasyonun 12 tanesi yakalandı.** Komut: `npm run mutation` (2026-11-13).

| # | Dosya | Yerleştirilen hata | Değişiklik | Yakalandı mı | Nasıl |
|---:|---|---|---|---|---|
| 1 | `src/functions/horspool.js` | Horspool kayması bir fazla (m − i) | `shift[p[i]] = m - 1 - i;` → `shift[p[i]] = m - i;` | evet | 41 test başarısız |
| 2 | `src/functions/kmp.js` | KMP uyuşmazlıkta sınırı unutur (q = 0) | `while (q > 0 && p[q] !== c) q = fail[q - 1];` → `while (q > 0 && p[q] !== c) q = 0;` | evet | 10 test başarısız |
| 3 | `src/functions/bm4dnaDs.js` | bm4DNADS sentinel denetiminde < yerine <= (j > n) | `if (j >= n) return;` → `if (j > n) return;` | evet | testler 90 sn içinde bitmedi (sonsuz döngü), süreç durduruldu |
| 4 | `src/functions/bm4dnaHmbs.js` | bm4DNAHMbs desende olmayan q-gram için m kadar kayar (ödevin ipucu hatası) | `const dflt = m - q + 1;` → `const dflt = m;` | evet | 34 test başarısız |
| 5 | `src/functions/shiftOr.js` | Shift-Or (m > 32) son pencereyi atlar | `const limit = n - m + w;` → `const limit = n - m + w - 1;` | evet | 3 test başarısız |
| 6 | `src/functions/wuManber.js` | Wu-Manber çakışmada en küçük kaymayı değil sonuncuyu tutar | `if (sft < shift[h]) shift[h] = sft;` → `shift[h] = sft;` | evet | 11 test başarısız |
| 7 | `src/functions/ahoCorasick.js` | Aho-Corasick sözlük bağlarını kurmaz (iç içe desenler kaçar) | `dict[s] = word[f] !== -1 ? f : dict[f];` → `dict[s] = -1;` | evet | 19 test başarısız |
| 8 | `src/functions/hits.js` | Sonuçlar sıralanmaz | `const keys = this.keys.subarray(0, this.count).sort();` → `const keys = this.keys.subarray(0, this.count);` | evet | 82 test başarısız |
| 9 | `src/functions/alphabet.js` | ignoreCase ASCII sınırı bir fazla ({ → [) | `return code >= 97 && code <= 122 ? code - 32 : code;` → `return code >= 97 && code <= 123 ? code - 32 : code;` | evet | 1 test başarısız |
| 10 | `src/atomic/ExactSearchAtom.js` | Metinden uzun bir desen varsa hiç aranmaz (minLen yerine maxLen) | `if (n > 0 && this.minLen <= n) {` → `if (n > 0 && this.maxLen <= n) {` | evet | 9 test başarısız |
| 11 | `src/functions/boyerMoore.js` | Boyer-Moore tam eşleşmeden sonra iyi sonek kayması yerine m kayar (örtüşen eşleşme kaçar) | `s += good[0];` → `s += m;` | evet | 18 test başarısız |
| 12 | `src/molecules/ExactMatch.js` | Molekül en pahalı atomu seçer (sıralama ters) | `ranked.sort((a, b) => a.seconds - b.seconds);` → `ranked.sort((a, b) => b.seconds - a.seconds);` | evet | 5 test başarısız |
