# Talim Botu — makro klavyeyi deneme oyunu

20 yıl önce Metin2 / Knight Online gibi oyunlarda seviye atlamak için tuşa basan
makrolar kullanılırdı. Bu klasör, aynı fikri **basit ve kontrollü** bir oyunda
denemek içindir: kuklayı döv, seviye atla. Tuşlar **A** (sol kesik), **S**
(darbe), **D** (sağ kesik) — yani cihazın varsayılan `a,s,d` makrosuyla birebir.

## Dosyalar

| Dosya | Ne |
|---|---|
| `index.html` | Oyunun kendisi (tek dosya, klavyeyle oynanır). |
| `test_oyun.mjs` | Cihazın göndereceği a-s-d tuşlarını ekransız tarayıcıya bastırıp skorun yükseldiğini doğrulayan test. |
| `oyun_ayar.conf` | Oyunu hedefleyen makro ayarı (benzetim için). |
| `ekran_goruntusu.png` | Botun oynadıktan sonraki hâli (testin ürettiği kanıt). |

## Elle oyna

Tarayıcıda `index.html`'i aç, A/S/D'ye bas. Her tuş kuklaya vurur; can biterse
kukla yeniden gelir, XP ve seviye artar.

## Otomatik test (donanım gerekmez)

Cihazın yaptığının aynısını yapar: a-s-d tuşlarını tur tur basar ve oyunun
tepkisini ölçer. Ekransız (headless) Chromium kullanır; `node` + `playwright`
gerekir.

```bash
node oyun/test_oyun.mjs       # ya da:  make oyun-test
```

Beklenen sonuç: 40 tur × 3 tuş = **120 vuruş**, kuklalar ölür, **seviye atlanır**
ve `ekran_goruntusu.png` güncellenir. Bu, "otomatik klavyeye basan cihaz oyunu
oynatır mı?" sorusunun donanımsız kanıtıdır.

## Gerçek cihazla

Kart gelince `arduino/tusmatik/` taslağındaki `ayar.url`'yi oyunun adresine,
`ayar.tuslar`'ı `{'a','s','d'}`'ye ayarlayıp yükle. Takınca cihaz oyunu açıp
dövmeye başlar.

## Not

Bu, kendi bilgisayarında, kendin için yaptığın bir deneme oyunudur. Başka
oyunların kurallarının makro/bot kullanımını yasaklayabileceğini unutma; bu test
oyunu tam da bu yüzden kendi kontrolümüzde, güvenli bir hedef olarak yazıldı.
