# 2. Ödev — USB Makro Klavye (STM32)

> Bu klasör **2. ödeve** aittir. 1. ödev (Agora forum) deponun kökünde durur; bu iki ödevin
> dosyaları birbirine karışmaz. 2. ödevle ilgili her şey bu `odev2-usb-klavye/` klasörünün içindedir.

## Tek cümleyle

Bilgisayara takılınca kendini **ikinci bir klavyeymiş gibi** tanıtan, takılır takılmaz bir tarayıcı
(ya da uygulama) açıp sonra **önceden ayarladığın tuşlara otomatik basan** küçük bir USB cihazı.
Knight Online gibi oyunlarda "sürekli ASD'ye bas" diyen oto-tuş programlarının yazılım değil,
**donanım** hâli.

## Neden ilginç / "sihir" nerede?

Normalde bir programın senin yerine tuşa basması için bilgisayara ayrıca bir yazılım kurman gerekir.
Burada ise basmayı yapan şey **cihazın kendisi**. İşletim sistemi (Windows ya da Linux) bu cihazı
sıradan bir klavye zanneder; çünkü cihaz USB üzerinden tam olarak gerçek bir klavyenin konuştuğu dilde
konuşur. Bu yüzden:

- **Hiçbir sürücü (driver) kurulmaz.** Tak-çalıştır. Her klavye zaten böyle çalışır.
- **İşletim sisteminden bağımsızdır.** Windows'a takınca Windows klavyesi, Linux'a takınca Linux
  klavyesi gibi görünür. Cihaz "harf gönderir", o harfi kim alırsa alsın fark etmez. Senin dediğin
  *"Windows içinde Windows, Linux içinde Linux"* kısmı tam olarak bu: cihaz aynı kalır, her sistem
  kendi klavyesi sanır.

Bu tür cihazların genel teknik adı **HID klavye** (bkz. alttaki terim listesi). Oyuncuların kullandığı
makro klavyeler, programlanabilir tuş takımları aynı prensiple çalışır.

## Cihaz takılınca ne oluyor? (akış)

1. Cihazı USB'ye takarsın.
2. Bilgisayar onu **yeni bir klavye** olarak görür (ekranda hiçbir kurulum çıkmaz).
3. Cihaz, ezbere bildiği tuş dizisini yazmaya başlar. Örneğin bir tarayıcı/uygulama açmak için:
   - **Windows:** `Win+R` → `chrome https://...` yazar → `Enter`. (Çalıştır kutusu)
   - **Linux:** masaüstüne göre `Win` / terminal kısayolu → komut → `Enter`.
4. Site/uygulama açıldıktan sonra cihaz asıl işine geçer: **senin ayarladığın tuşlara belirli aralıklarla
   basmaya** başlar (örn. `A`, `S`, `D` sırayla, her 200 ms'de bir).

## Ayarları nasıl yapacaksın?

"Hangi tuşlara, ne sıklıkla, ne kadar süre bassın?" bilgisini cihazın hatırlaması gerekir. İki yaygın yol var:

- **Basit yol:** Tuş dizisini ve zamanlamayı doğrudan cihazın yazılımına (firmware) gömmek. Değiştirmek
  için yeniden programlarsın. Ödev için en kolay başlangıç budur.
- **Esnek yol:** Cihazın küçük bir ayar modu olur. Mesela takılınca önce bir ayar sayfası/uygulaması açar,
  sen "A S D, 200 ms" dersin, cihaz bunu belleğine kaydeder, sonraki takmalarda onu uygular. Bu kısım
  ödevin "ileri seviye" hedefi olabilir.

## Donanım: neden STM32?

**STM32**, içinde USB donanımı hazır gelen ucuz bir mikrodenetleyici (küçük bilgisayar-çip). "Kendini
klavye gibi tanıtma" (USB HID) işini kütüphaneyle hazır verir, bu yüzden sıfırdan USB yazmak zorunda
kalmazsın. Başlangıç için uygun kartlar: **STM32F103 "Blue Pill"** ya da **STM32F4** serisi. (Alternatif
olarak aynı mantık Raspberry Pi Pico / ATmega32U4 ile de kurulabilir; ödevde STM32 istendiği için ona
odaklanıyoruz.)

Kabaca ihtiyaç listesi:

- 1 adet STM32 geliştirme kartı (USB'den beslenen ve veri gönderebilen)
- Programlamak için ST-Link ya da kartın USB bootloader'ı
- Yazılım tarafında: STM32 HID kütüphanesi (kartı klavye yapan hazır kod)

## Önerilen klasör düzeni (ileride dolacak)

```
odev2-usb-klavye/
├── README.md          ← bu dosya (ödevin açıklaması)
├── donanim/           ← kart seçimi, bağlantı şeması, fotoğraf
├── yazilim/           ← STM32 firmware kodu (kartı klavye yapan + tuş dizisi)
└── belgeler/          ← rapor, ekran görüntüleri, test notları
```

(Şimdilik yalnızca bu README var; kodu ve belgeleri yazdıkça bu alt klasörler eklenecek.)

## Yol haritası (sırayla)

1. **Klavye ol.** STM32'yi, bilgisayara takınca tek bir harf (örn. sürekli `A`) yazan bir klavye yap.
   Bu çalışırsa işin kalbi tamamdır.
2. **Tarayıcı aç.** Takılınca `Win+R` → `chrome ...` → `Enter` dizisini yazdır.
3. **Makroyu ekle.** Site açıldıktan sonra `A S D` döngüsünü belirli aralıkla bastır.
4. **İki sistemde dene.** Windows ve Linux'ta ayrı ayrı test et, farklı kısayolları ayarla.
5. **Ayarlanabilir yap** (isteğe bağlı/ileri): tuş ve süreyi dışarıdan değiştirilebilir hâle getir.

## Kapsam ve dürüst not

Bu, **kendi bilgisayarında, kendi oyun/otomasyon kullanımın** için yaptığın programlanabilir bir makro
klavyedir — piyasadaki oyuncu makro klavyeleriyle aynı fikir. Başkasının bilgisayarına gizlice bir şey
yaptırmak gibi bir amacı yoktur; cihazı sen takar, sen ayarlarsın, ne yaptığı görünür.

---

### Kısa terim listesi

| Terim | Türkçesi | Tek cümlelik tanım |
|---|---|---|
| **USB HID** | İnsan Arayüz Aygıtı | Klavye/fare gibi aygıtların bilgisayarla sürücüsüz konuştuğu standart; cihazımız kendini bu sınıfta "klavye" diye tanıtır. |
| **Firmware** | Cihaz yazılımı (gömülü yazılım) | Mikrodenetleyicinin içine yazılan, cihazın ne yapacağını belirleyen kalıcı program. |
| **Mikrodenetleyici** | Mikrodenetleyici | İçinde işlemci, bellek ve giriş-çıkış olan tek çipten minik bilgisayar (STM32 bir örnektir). |
| **Bootloader** | Önyükleyici | Çipe yeni yazılımı yüklemeyi sağlayan, çipte hazır gelen küçük program. |
| **Makro** | Makro | Önceden tanımlanmış, tek seferde tetiklenen tuş/işlem dizisi. |
