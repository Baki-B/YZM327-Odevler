# Orman Farmı (.io) — makro klavyeyi deneme oyunu

20 yıl önce Metin2 / Knight Online gibi oyunlarda seviye atlamak için tuşa/tıka
basan makrolar kullanılırdı. Bu klasör, aynı fikri **glor.io / dynast.io tarzı**
basit bir farm oyununda denemek içindir.

Gerçek kullanım: **oyuncu (insan)** karakteri kaynakların yanına götürür ve
oto-vuruşu ağaca/taşa ayarlar; **makro (cihaz)** ise sadece **sol/sağ fare tıkını**
sürekli spamlar. Oyunda oto-hedef, oyuncuya en yakın kaynağa kilitlidir; her tık
onu vurur, canı bitince odun/taş toplanır, kaynak bir süre sonra yeniden büyür
(sürekli farm). Yani makronun eylemi **tuş değil, fare tıklamasıdır**.

## Dosyalar

| Dosya | Ne |
|---|---|
| `index.html` | Oyunun kendisi (tek dosya, klavyeyle oynanır). |
| `test_oyun.mjs` | Cihazın göndereceği a-s-d tuşlarını ekransız tarayıcıya bastırıp skorun yükseldiğini doğrulayan test. |
| `oyun_ayar.conf` | Oyunu hedefleyen makro ayarı (benzetim için). |
| `ekran_goruntusu.png` | Botun oynadıktan sonraki hâli (testin ürettiği kanıt). |

## Elle oyna

Tarayıcıda `index.html`'i aç, **sol/sağ tık** ile vur. Oto-hedef en yakın kaynağa
kilitlidir (sarı halka ve nişan çizgisi); her tık onu keser, canı bitince odun/taş
toplanır, XP/seviye artar, kaynak bir süre sonra yeniden büyür. İstersen
<kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> ile oyuncuyu gezdirip hedefi
değiştirebilirsin (makro bunu yapmaz; onu sen yaparsın).

## Otomatik test (donanım gerekmez)

Cihazın yaptığının aynısını yapar: sol/sağ fare tıklarını tur tur basar ve oyunun
tepkisini ölçer. Ekransız (headless) Chromium kullanır; `node` + `playwright` gerekir.

```bash
node oyun/test_oyun.mjs       # ya da:  make oyun-test
```

Beklenen sonuç: 40 tur × 2 tık = **80 tık**, hem odun hem taş farmlanır,
**seviye atlanır** ve `ekran_goruntusu.png` güncellenir. Bu, "otomatik tıklayan
cihaz oyunu farmlar mı?" sorusunun donanımsız kanıtıdır.

## Gerçek cihazla

Kart gelince `arduino/tusmatik/` taslağındaki ayarı fare moduna koy:
`ayar.tarayiciAc = false; ayar.eylem = FARE; ayar.fareDugmeleri = {SOL, SAG};`
(taslakta örneği hazır). Takınca cihaz sadece tıklamaya başlar; sen oyuncuyu
kaynağın yanına koyup oto-vuruşu ayarladığın sürece farmlar.

## Not

Bu, kendi bilgisayarında, kendin için yaptığın bir deneme oyunudur. Başka
oyunların kurallarının makro/bot kullanımını yasaklayabileceğini unutma; bu test
oyunu tam da bu yüzden kendi kontrolümüzde, güvenli bir hedef olarak yazıldı.
