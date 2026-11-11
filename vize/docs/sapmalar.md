# Makaleden ve klasik tariflerden sapmalar

Ödev, Allmer 2016'daki sözde kodun bazı yerlerde eksik ya da hatalı olduğunu söylüyor ve algoritmanın "makalede böyle yazıyor" diye değil, doğru sonuç verecek şekilde yazılmasını istiyor.

**Önemli not:** Makalenin PDF'ine bu çalışma ortamından erişilemedi. Bu yüzden aşağıdaki maddeler makalenin satır satır karşılaştırması değil. Ödev tablosundaki tarif ve bu algoritma ailesinin bilinen tuzakları esas alındı. Hepsi kodda yorumla işaretli ve testlerle sınanıyor. Makale okunduktan sonra her madde "makalede de böyle / makalede farklı" diye güncellenmeli.

## bm4DNAHMbs (`src/functions/bm4dnaHmbs.js`)

| # | Konu | Uygulama | Neden |
|---|---|---|---|
| H1 | Desende hiç geçmeyen q-gram için kayma | **m − q + 1** | Ödevdeki ipucu sorusu. Pencerenin son q-gramı desende hiç geçmese bile pencereyi m kadar kaydırmak güvenli değildir, çünkü desen pencerenin son q − 1 karakterinden başlıyor olabilir. Örnek: desen `ACGTAC` (m = 6), q = 3, metin `TTTTxACGTAC`. Pencere `TTTxAC` (konum 1–6) iken son q-gram `xAC` desende yok. 6 kaydırılırsa pencere 7. konuma atlar ve 5. konumdaki eşleşme kaçar. Güvenli kayma 6 − 3 + 1 = 4'tür: pencere 5. konuma gelir ve eşleşme bulunur. Test: `tests/unit/atoms.test.js` → "bm4DNAHMbs: desende geçmeyen q-gram için kayma m − q + 1" ve oracle testleri. |
| H2 | Desenin son q-gramı | Kayma tablosunda 0 tutulur; pencere tam doğrulanır, sonra ayrı hesaplanan **shift2** kadar ilerlenir. | Son q-gramın kendisi tabloya "kayma 0" olarak girerse ve doğrulamadan sonra yine tablodaki değer kullanılırsa döngü yerinde sayar. shift2, aynı q-gramın desende son konumdan önceki en sağ yerinden hesaplanır (yoksa m − q + 1). |
| H3 | q-gram özeti | Karakter kimlikleri bit kaydırmayla birleştirilir ("bs"); her karakter ⌈log₂ σ⌉ bit, toplam en fazla 16 bit. q = min(m, ⌊16 / bit⌋). | DNA için 2 bit yetmez, çünkü 0 kimliği "desende olmayan karakter" için ayrılmıştır (N, küçük harf vb.). Bu yüzden 3 bit, q = 5. Özet çakışmasız (birebir) olduğundan yanlış kayma riski yoktur. |
| H4 | Desen q'dan kısa | q = m alınır, kayma 1'e düşer. | Algoritma kısa desen için tasarlanmamış. Yine de doğru sonuç vermesi gerekiyor. Molekül bu durumda başka atom seçer. |
| H5 | Tablo | Bütün desenler tek tabloyu paylaşır; her desen kendi girdilerini yazar, aramadan sonra yalnızca onları siler. Değer = kayma + 1, 0 = "yok". | Desen başına 64 K'lık tablo ayırmak çok desende belleği ve kurulum süresini patlatır. |

## bm4DNADS (`src/functions/bm4dnaDs.js`)

| # | Konu | Uygulama | Neden |
|---|---|---|---|
| D1 | Sentinel'in yeri | Metin kimlik dizisine çevrilirken sona en uzun desen kadar boş yer bırakılır; her desen aramadan önce kendi kopyasını oraya yazar. | Sentinel metnin içine yazılırsa (ya da metin kopyalanmadan) metin bozulur ve sonraki desen yanlış sonuç alır. |
| D2 | Döngünün bitişi | Atlama döngüsü durduğunda önce `j ≥ n` denetlenir; sentinel içindeki "eşleşme" raporlanmaz. | Sentinel her zaman bir eşleşme üretir. Denetim yapılmazsa metnin sonuna sahte bir sonuç eklenir. |
| D3 | Atlamanın sentinel'i aşmaması | Kanıt kodda yorumda: pencere sonu sentinel bölgesindeyken kayma, sentinel'in son karakterini geçemez. | Üç kez açılmış döngü her adımda sınır denetimi yapmaz. Bu yüzden dizinin dışına çıkmadığı ayrıca gösterilmeli. |
| D4 | shift2 | Son karakterin desenin İLK m − 1 karakterindeki en sağ yerinden hesaplanır (yoksa m). | Son karakterin kendisi sayılırsa kayma 0 olur ve döngü sonsuza kadar döner. |
| D5 | Uzun desen | Yalnızca kısa desen için önerilse de her m için doğru çalışır. | Gizli testler her atomu her girdiyle sınayabilir. |

## Diğer atomlar

| Atom | Sapma / ek | Neden |
|---|---|---|
| Shift-Or | m > 32'de süzgeç + doğrulama; `applicable()` "uygun değil" der. | Tablo "m ≤ 32 için" diyor. Atom yine de yanlış sonuç vermemeli. |
| Wu-Manber | Tablo boyu desenlerdeki blok sayısının ~8 katıyla sınırlı (en az 2⁸, en fazla 2¹⁸). Olası blok sayısı bunun altındaysa birebir indeks, üstündeyse karma (hash). Çakışmada en küçük kayma tutulur. | İlk sürüm hep 2¹⁸ elemanlı tablo kuruyordu. 10⁴ karakterlik metinde tabloyu sıfırlamak aramanın kendisinden uzun sürdü (kalibrasyon tanı çıktısı). Çakışmada küçük kaymanın tutulması doğruluğu korur. |
| Wu-Manber | Kovadaki her desen tam uzunluğuyla doğrulanır. Desen metnin sonunu aşıyorsa atlanır. | Desenler en kısa desenin uzunluğuna kırpılarak tabloya girer. Uzun desenin kalanı ancak doğrulamada kontrol edilir. |
| Aho-Corasick | Tam otomat (DFA); çıktılar "sözlük bağı" (en yakın desen biten başarısızlık atası) zinciriyle. Tablo 3·10⁷ hücreyi aşarsa `applicable()` "uygun değil" der. | Desen sayısı arttıkça tablo büyür; çok büyük tablo bellek sorunu çıkarır. |
| Bütün atomlar | ignoreCase ve alfabe küçültme ortak sınıfta yapılır. Desende olmayan her karakter 0 kimliğini alır. | Tablolar 65 536 yerine σ_desen + 1 elemanlı olur. İki farklı metin karakterinin ikisi de 0 olsa bile 0 hiçbir desen karakteriyle eşleşmediğinden sonuç değişmez. |
