# Orman Farmı (.io) — makro klavyeyi deneme oyunu

20 yıl önce Metin2 / Knight Online gibi oyunlarda seviye atlamak için tuşa basan
makrolar kullanılırdı. Bu klasör, aynı fikri **basit ve kontrollü** bir oyunda
denemek içindir: **glor.io / dynast.io tarzı** tepeden bakışlı bir haritada
**W/A/S/D** ile gezersin; ağaçlara vurunca odun, taşlara vurunca taş farmlanır.
Tuşlar yön tuşlarıdır (yukarı/sol/aşağı/sağ) — yani makronun `w,a,s,d` ayarıyla
birebir. Toplanan kaynak biter, bir süre sonra yeniden büyür (sürekli farm).

## Dosyalar

| Dosya | Ne |
|---|---|
| `index.html` | Oyunun kendisi (tek dosya, klavyeyle oynanır). |
| `test_oyun.mjs` | Cihazın göndereceği a-s-d tuşlarını ekransız tarayıcıya bastırıp skorun yükseldiğini doğrulayan test. |
| `oyun_ayar.conf` | Oyunu hedefleyen makro ayarı (benzetim için). |
| `ekran_goruntusu.png` | Botun oynadıktan sonraki hâli (testin ürettiği kanıt). |

## Elle oyna

Tarayıcıda `index.html`'i aç, W/A/S/D ile haritada gez. Menzilindeki ağaç ve
taşlara otomatik vurulur; canları bitince kaynak toplanır (odun/taş), XP artar,
seviye atlanır. Kaynak bir süre sonra aynı yerde yeniden büyür.

## Otomatik test (donanım gerekmez)

Cihazın yaptığının aynısını yapar: w-a-s-d tuşlarını tur tur basar (haritada
gezinir) ve oyunun tepkisini ölçer. Ekransız (headless) Chromium kullanır;
`node` + `playwright` gerekir.

```bash
node oyun/test_oyun.mjs       # ya da:  make oyun-test
```

Beklenen sonuç: 40 tur × 4 tuş = **160 hamle**, hem odun hem taş farmlanır,
**seviye atlanır** ve `ekran_goruntusu.png` güncellenir. Bu, "otomatik klavyeye basan
cihaz oyunu oynatır mı?" sorusunun donanımsız kanıtıdır.

## Gerçek cihazla

Kart gelince `arduino/tusmatik/` taslağındaki `ayar.url`'yi oyunun adresine,
`ayar.tuslar`'ı `{'w','a','s','d'}`'ye ayarlayıp yükle. Takınca cihaz oyunu açıp
haritada gezip farmlamaya başlar.

## Not

Bu, kendi bilgisayarında, kendin için yaptığın bir deneme oyunudur. Başka
oyunların kurallarının makro/bot kullanımını yasaklayabileceğini unutma; bu test
oyunu tam da bu yüzden kendi kontrolümüzde, güvenli bir hedef olarak yazıldı.
