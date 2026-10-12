# 2. Ödev — USB Makro Klavye (STM32)

> Bu klasör **2. ödeve** aittir. 1. ödev (Agora forum) deponun kökünde durur; iki
> ödevin dosyaları birbirine karışmaz. 2. ödevle ilgili her şey bu
> `odev2-usb-klavye/` klasörünün içindedir.

## Tek cümleyle

Bilgisayara takılınca kendini **ikinci bir klavyeymiş gibi** tanıtan, takılır
takılmaz bir tarayıcı açıp sonra **önceden ayarladığın tuşlara otomatik basan**
küçük bir USB cihazı. Oyunlardaki (ör. Knight Online) "sürekli ASD'ye bas"
oto-tuş programlarının yazılım değil, **donanım** hâli. Teknik adıyla
programlanabilir bir **USB HID makro klavye**.

## Nasıl çalışır (kısaca)

İşletim sistemi, USB'den klavye dilinde konuşan her aygıtı sıradan bir klavye
sanar. Bu yüzden **sürücü kurulmaz** (tak-çalıştır) ve **işletim sisteminden
bağımsızdır**: cihaz aynı kalır, Windows da Linux da kendi klavyesi sanır
("Windows içinde Windows, Linux içinde Linux"). Takılınca cihaz önce bir tarayıcı
açar, sonra ayarladığın tuşlara belirli aralıklarla basar.

Ayrıntılı anlatım: [`belgeler/analiz.md`](belgeler/analiz.md).

## Mimari — mantık donanımdan ayrı

Projenin kalbi: **ne yapılacağı** (hangi tuşlar, tarayıcı nasıl açılır) ile
**nasıl yapılacağı** (gerçek USB sinyali) birbirinden ayrıdır.

- **`cekirdek/`** — donanım bilmeyen saf C++ mantık. Kart olmadan bilgisayarda
  derlenip test edilir.
- **`arduino/`** — çekirdeği gerçek USB-HID klavyeye bağlayan STM32 taslağı.
- **`benzetim/`** — çekirdeği konsola bağlar; cihazın ne yapacağını gösterir.
- **`testler/`** — çekirdeği test sahtelerine bağlar; birim testleri.

Uygulanan SOLID ilkeleri ve GoF desenleri (Strategy, Factory, Command, Builder,
State, Adapter, Observer, Facade) dosya dosya: [`belgeler/tasarim.md`](belgeler/tasarim.md)
(UML sınıf/durum/sıralı diyagramlarıyla).

## Çalıştır (kart gerekmez)

```bash
cd odev2-usb-klavye
make test        # birim testleri (çekirdek mantığı; ~1 sn)
make benzetim    # cihazın ne yapacağını konsolda gösterir
```

Kendi ayarınla benzetim:

```bash
make benzetim AYAR=ornek_ayar.conf
```

Örnek benzetim çıktısı (kısaltılmış):

```
[durum] BASLATILIYOR
  kisayol: [GUI]+'r'
  yaz    : "chrome https://baki-b.github.io/YZM327-Odevler/"
  tus    : [ENTER]
[durum] CALISIYOR
  bas    : 'a'   (bekle 200 ms)
  bas    : 's'   (bekle 200 ms)
  bas    : 'd'   (bekle 200 ms)
  ...
```

## Ayarlar

Satır tabanlı yapılandırma (`ornek_ayar.conf`):

| Anahtar | Ne | Varsayılan |
|---|---|---|
| `platform` | `windows` / `linux` | windows |
| `url` | açılacak adres | Agora sitesi |
| `tuslar` | sırayla basılacak tuşlar | `a,s,d` |
| `aralik_ms` | tuşlar arası bekleme | 200 |
| `tekrar` | kaç tur (0 = sonsuz) | 0 |
| `baslangic_gecikme_ms` | tarayıcı açılma beklemesi | 1500 |
| `linux_terminal` | Linux terminal kısayolu | `ctrl+alt+t` |

Kartta ayarlar doğrudan taslaktaki `setup()` içinde belirlenir (basit yol);
metinden ayrıştırma bilgisayar/benzetim tarafında kullanılır (esnek yol).

## Donanıma yükleme (kart gelince)

Önerilen kart: **STM32F411 "Black Pill"**. Taslak: `arduino/tusmatik/`. Derleme
ve yükleme adımları, Arduino ayarları ve bağlantı: [`arduino/BENIOKU.md`](arduino/BENIOKU.md).

Çekirdek tek kaynaktır: Arduino taslağı aynı `cekirdek/` kodunu kullanır, yalnızca
en alttaki ince katmanı (USB-HID, `delay/millis`, LED) ekler.

## Yol haritası (durum)

1. ✅ Klavye ol (çekirdek + USB-HID adaptörü yazıldı).
2. ✅ Tarayıcı aç (Windows ve Linux stratejileri, testli).
3. ✅ Makro döngüsü (tuşlar + aralık + tekrar, testli).
4. ✅ İki sistem (Windows/Linux ayarı, testli).
5. ✅ Ayarlanabilir (metin yapılandırma + ayrıştırıcı, testli).
6. ⬜ Karta yükleyip gerçek bilgisayarda doğrulama (donanım gelince).

## Kapsam ve dürüst not

Bu, kendi bilgisayarında, kendi oyun/otomasyon kullanımın için programladığın bir
makro klavyedir — piyasadaki oyuncu makro klavyeleriyle aynı fikir. Cihazı sen
takar, sen ayarlarsın, ne yaptığı görünür.

---

### Kısa terim listesi

| Terim | Türkçesi | Tek cümlelik tanım |
|---|---|---|
| **USB HID** | İnsan Arayüz Aygıtı | Klavye/fare gibi aygıtların bilgisayarla sürücüsüz konuştuğu standart; cihazımız kendini bu sınıfta "klavye" diye tanıtır. |
| **Firmware** | Cihaz yazılımı | Mikrodenetleyicinin içine yazılan, cihazın ne yapacağını belirleyen kalıcı program. |
| **Adapter (bağdaştırıcı)** | Bağdaştırıcı deseni | Soyut bir arabirimi farklı somut dünyalara (USB, konsol, test) uyarlayan ince katman. |
| **Bağımlılık enjeksiyonu** | Bağımlılık enjeksiyonu | Bir sınıfın ihtiyaçlarını (klavye, saat) dışarıdan, yapıcıdan vermek; böylece gerçeği yerine sahtesi konabilir. |
