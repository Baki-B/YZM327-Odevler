// Her atom için özel durum testleri (her biri NaiveSearch ile karşılaştırılır)
// ve algoritmalara özgü iç parçaların birim testleri.
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { ATOMS, collect, oracle, firstDiff } from './helpers.js';
import { failureFunction } from '../../src/functions/kmp.js';
import { goodSuffixShifts } from '../../src/functions/boyerMoore.js';
import { chooseQ, prepareBm4DnaHmbs } from '../../src/functions/bm4dnaHmbs.js';
import { prepareBm4DnaDs } from '../../src/functions/bm4dnaDs.js';
import { chooseBlock } from '../../src/functions/wuManber.js';
import { horspoolShift, qgramShift } from '../../src/functions/expect.js';
import { buildAlphabet, encode, foldAscii } from '../../src/functions/alphabet.js';

const CASES = [
  ['periyodik desen ABAB', ['ABAB'], 'ABABABABAB'],
  ['periyodik desen, uzun', ['ABABABABABAB'], 'ABABABABABABABABABABAB'],
  ['tek karakterlik desen', ['G'], 'GAGGTG'],
  ['desen alfabesinde olmayan metin karakterleri', ['ACG'], 'xxACGyyNNNACG--ACG'],
  ['desen = metin', ['TTAGGC'], 'TTAGGC'],
  ['metnin en başında ve en sonunda eşleşme', ['GAT'], 'GATTACAGAT'],
  ['tek harften oluşan metin ve desen (AAAA…)', ['AAA', 'AAAA'], 'A'.repeat(40)],
  ['son karakter desende tekrarlıyor', ['ABCAB', 'BB'], 'ABCABCABABBB'],
  ['31, 32 ve 33 uzunluk (Shift-Or kelime sınırı)', ['a'.repeat(31) + 'b', 'a'.repeat(32), 'a'.repeat(32) + 'b'], 'a'.repeat(40) + 'b' + 'a'.repeat(33) + 'b'],
  ['70 karakterlik uzun desen', ['ACGT'.repeat(17) + 'AC'], 'GG' + 'ACGT'.repeat(40)],
  ['BMP dışı karakter (emoji, vekil çift)', ['😀', '😀😀', 'a😀'], 'a😀😀😀b😁'],
  ['vekil çiftin yarısı', ['\uD83D'], 'a😀b😁'],
  ['boşluk ve satır sonu içeren metin', ['a b', '\n'], 'x a b\na b\n'],
  ['karışık uzunluklar ve tekrar eden desen', ['A', 'ACGTACGTAC', 'CG', 'A', 'GTACGTACGTACGTACGTAC'], 'ACGTACGTACGTACGTACGTACGT'],
  ['çok desen, ortak önekler', ['he', 'she', 'his', 'hers'], 'ushers and his heroes she'],
  ['metinden uzun desenle kısa desen birlikte', ['CCCCCCCCCC', 'C'], 'ACCA'],
];

for (const Atom of ATOMS) {
  describe(`özel durumlar: ${Atom.manifest.name}`, () => {
    for (const [title, patterns, seq] of CASES) {
      test(title, () => {
        for (const ignoreCase of [false, true]) {
          const params = { patterns, ignoreCase };
          const entries = [{ header: '>t', seq }];
          const got = collect(Atom, params, entries);
          const want = oracle(params, entries);
          assert.deepEqual(got, want, firstDiff(got, want) ?? '');
        }
      });
    }
  });
}

describe('iç parçalar', () => {
  const enc = (s) => Uint16Array.from(s, (c) => c.charCodeAt(0));

  test('KMP başarısızlık işlevi', () => {
    assert.deepEqual([...failureFunction(enc('ABABAC'))], [0, 0, 1, 2, 3, 0]);
    assert.deepEqual([...failureFunction(enc('AAAA'))], [0, 1, 2, 3]);
  });

  test('Boyer-Moore iyi sonek: tam eşleşmede kayma = periyot', () => {
    assert.equal(goodSuffixShifts(enc('ABAB'))[0], 2);
    assert.equal(goodSuffixShifts(enc('ABCD'))[0], 4);
    assert.equal(goodSuffixShifts(enc('AAAA'))[0], 1);
  });

  test('bm4DNADS: son karakterin kayması 0, shift2 ise gerçek Horspool kayması', () => {
    const { map, size } = buildAlphabet(['GCAGAG'], false);
    const prep = prepareBm4DnaDs(encode('GCAGAG', map), size);
    assert.equal(prep.skip[map['G'.charCodeAt(0)]], 0);
    assert.equal(prep.shift2, 2); // son G'den önceki en sağ G iki geride
    assert.equal(prepareBm4DnaDs(encode('A', map), size).shift2, 1);
  });

  test('bm4DNAHMbs: desende geçmeyen q-gram için kayma m − q + 1', () => {
    const { map, size } = buildAlphabet(['ACGTTGCA'], false);
    const prep = prepareBm4DnaHmbs(encode('ACGTTGCA', map), size);
    assert.equal(prep.dflt, 8 - prep.q + 1);
    assert.ok(prep.q >= 2 && prep.q <= 8);
    assert.equal(chooseQ(5, 3), 3); // q desen uzunluğunu aşmaz
    assert.equal(chooseQ(5, 100), 5); // DNA (σ+1=5 → 3 bit): 16/3 = 5
    assert.equal(chooseQ(21, 100), 3); // protein: 5 bit → 3
  });

  test('Wu-Manber blok uzunluğu en kısa desenden uzun olmaz', () => {
    assert.equal(chooseBlock(4, 1000, 2), 2);
    assert.ok(chooseBlock(4, 100, 20) >= 3);
    assert.equal(chooseBlock(90, 1, 1), 1);
  });

  test('beklenen kayma formülleri', () => {
    assert.equal(horspoolShift(1, 4), 1);
    assert.equal(horspoolShift(10, 1), 1);
    assert.ok(Math.abs(horspoolShift(1000, 4) - 4) < 0.01); // uzun desende ≈ σ
    assert.ok(horspoolShift(8, 100) > 7); // büyük alfabede ≈ m
    assert.ok(qgramShift(64, 4, 4) > horspoolShift(64, 4));
  });

  test('alfabe: ignoreCase yalnızca ASCII; kodlanmamış karakter 0', () => {
    assert.equal(foldAscii('abcİıß{}'), 'ABCİıß{}');
    const { map, size } = buildAlphabet(['aB'], true);
    assert.equal(size, 3);
    assert.equal(map[97], map[65]);
    assert.equal(map[98], map[66]);
    assert.equal(map['C'.charCodeAt(0)], 0);
  });
});
