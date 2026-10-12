# Donanım tarafı — STM32'ye yükleme

Bu klasör, çekirdeği (`../cekirdek/`) gerçek bir USB klavyeye dönüştüren donanım
bağdaştırıcısını içerir. Taslak: [`tusmatik/tusmatik.ino`](tusmatik/tusmatik.ino).

> Çekirdeğin **mantığı** bilgisayarda test edilir (`make test`). Burada eklenen
> tek şey, o mantığı gerçek USB-HID klavyeye bağlayan ince katmandır. Yani kart
> gelmeden önce işin büyük kısmı zaten bitmiş ve doğrulanmış olur.

## Gerekli

- **STM32F411 "Black Pill"** kartı (önerilen; USB-HID sağlam çalışır). F103
  "Blue Pill" de olur ama USB tarafı daha zahmetlidir.
- USB veri kablosu (yalnızca şarj kablosu değil).
- Arduino IDE (2.x) ya da `arduino-cli`.

## Bir kez: STM32 kart desteğini kur

Arduino IDE → **Tools > Board > Boards Manager** → "STM32 MCU based boards"
(STMicroelectronics) paketini kur. `arduino-cli` ile:

```bash
arduino-cli config add board_manager.additional_urls \
  https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json
arduino-cli core update-index
arduino-cli core install STMicroelectronics:stm32
```

## Derleme ayarları (önemli)

Kartın kendini **klavye** olarak tanıtabilmesi için USB aygıt desteği açık olmalı:

- Arduino IDE → **Tools** altında:
  - **Board:** Generic STM32F4 series → **Black Pill F411CE**
  - **USB support (if available):** **CDC + HID** (ya da en az **HID**)
  - **Upload method:** kartına göre (STM32CubeProgrammer (DFU) ya da ST-Link)

## Yükleme

```bash
# Derle (FQBN kartına göre değişebilir):
arduino-cli compile \
  --fqbn STMicroelectronics:stm32:GenF4:pnum=BLACKPILL_F411CE,usb=CDCHID \
  arduino/tusmatik

# Karta yükle (port adını kendi sistemine göre değiştir):
arduino-cli upload -p /dev/ttyACM0 \
  --fqbn STMicroelectronics:stm32:GenF4:pnum=BLACKPILL_F411CE,usb=CDCHID \
  arduino/tusmatik
```

F411 DFU ile yüklüyorsan: BOOT0 düğmesini basılı tutarak tak (DFU kipi), yükle,
sonra çıkar tak.

## Nasıl çalışır (taslaktaki karşılıklar)

| Soyut çekirdek | Karttaki gerçek karşılığı |
|---|---|
| `KlavyeCikti` | `ArduinoKlavye` → `Keyboard.print / write / press` (USB-HID) |
| `Saat` | `ArduinoSaat` → `delay()` / `millis()` |
| `DurumGozlemci` | `LedGozlemci` → kart üzerindeki LED |
| `Surucu` | aynı çekirdek sınıfı; değişmez |

`setup()` ayarları belirler, klavyeyi başlatır, bilgisayarın cihazı tanıması için
kısa bekler ve `baslat()` ile tarayıcıyı açar. `loop()` her turda bir kez
tuşlara basar (sonsuz tekrar buradan gelir).

## Ayarı değiştirmek

Taslakta `setup()` içindeki `ayar` alanlarını değiştir (platform, url, tuslar,
aralikMs, tekrar) ve yeniden yükle. İşletim sistemi (Windows/Linux) kartta
derleme zamanında seçilir; cihaz işletim sistemini kendisi algılayamaz.

## Uyarı / kapsam

Bu, kendi bilgisayarında kendi kullanımın için programladığın bir makro
klavyedir. Taktığın bilgisayarı sen seçersin, ne yazacağını sen belirlersin ve
davranışı görünürdür. Başkasının cihazında habersiz çalıştırmak için değildir.
