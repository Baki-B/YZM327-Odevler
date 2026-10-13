# Analiz — USB Makro Klavye

## 1. Problem

Bilgisayara takılınca kendini **klavye ve fare** olarak tanıtan (bileşik USB-HID),
önceden ayarlanan eylemi sürekli tekrarlayan bir USB cihazı. İki kullanım:
(1) **tuş modu** — tarayıcı açıp ayarlı tuşlara basar (Knight Online tarzı "sürekli
ASD"); (2) **fare modu** — glor.io / dynast.io gibi farm oyunlarında sol/sağ tık
spamlar. Teknik adıyla programlanabilir bir **USB HID makro aygıtı**.

## 2. Neden işe yarıyor (çekirdek gözlem)

İşletim sistemi, USB üzerinden klavyenin konuştuğu dilde konuşan her aygıtı
sıradan bir klavye kabul eder. Bu yüzden:

- **Sürücü (driver) kurulmaz** — tak-çalıştır.
- **İşletim sisteminden bağımsızdır** — cihaz yalnızca "tuş gönderir"; Windows da
  Linux da kendi klavyesi sanır. Kullanıcının "Windows içinde Windows, Linux
  içinde Linux" sözü budur.

## 3. Gereksinimler

**İşlevsel:**

1. Takılınca kendini USB-HID klavye **ve fare** olarak tanıtmak.
2. (İsteğe bağlı) ayarlanabilir bir adresi tarayıcıda açmak (Windows: Çalıştır
   kutusu; Linux: terminal + `xdg-open`). Oyuncu zaten oyundaysa bu adım atlanır.
3. Ayarlanan eylemi (tuşa basma ya da **fare tıklama**) ayarlanan aralıkla,
   ayarlanan tekrar sayısınca yapmak.
4. Yapılandırılabilir olmak: eylem türü (tus/fare), tuşlar/fare düğmeleri, aralık,
   tekrar, tarayıcı açma, adres, platform.

**İşlevsel olmayan:**

5. Çekirdek mantık donanımdan bağımsız ve **kart olmadan test edilebilir** olmalı.
6. Yeni platform/adım eklemek var olan kodu değiştirmeden mümkün olmalı (OCP).
7. Kod okunur, Türkçe adlandırmalı ve belgeli olmalı (Agora ile tutarlı).

## 4. İki yapılandırma yolu

- **Basit yol:** Ayarlar doğrudan koda yazılır (karttaki `setup()`); değiştirip
  yeniden yüklenir. Gömülü tarafta en az yük.
- **Esnek yol:** Satır tabanlı metin yapılandırması ayrıştırılır
  (`Ayarlar::metinden`); bilgisayar/benzetim tarafında ve testlerde kullanılır.

## 5. Kabul ölçütleri

| # | Ölçüt | Nasıl doğrulanır |
|---|---|---|
| 1 | Windows açılış dizisi doğru (Win+R → chrome url → Enter) | `test_baslatici` |
| 2 | Linux açılış dizisi doğru (terminal → xdg-open url → Enter) | `test_baslatici` |
| 3 | Tuşlar doğru sıra ve aralıkla basılır | `test_surucu` |
| 4 | tekrar>0 ise doğru sayıda turda biter | `test_surucu` |
| 5 | Yapılandırma ayrıştırma + hatalı girdi reddi | `test_ayarlar` |
| 6 | Durum geçişleri doğru | `test_surucu`, `test_durum` (State) |
| 7 | Çekirdek kart olmadan derlenir ve testler geçer | `make test` + CI |

## 6. Kısıtlar ve riskler

- Cihaz işletim sistemini algılayamaz → platform ayarla/derlemeyle verilir.
- Linux masaüstleri terminal kısayolunda farklılık gösterir → kısayol ayarlanabilir.
- F103 "Blue Pill"de USB-HID zahmetli olabilir → F411 "Black Pill" önerilir.
- Zamanlama gerçek makinede değişebilir → `baslangic_gecikme_ms` ayarlanabilir.

## 7. Kapsam ve etik sınır

Bu, kullanıcının **kendi bilgisayarında, kendi oyun/otomasyon kullanımı** için
programladığı bir makro klavyedir; piyasadaki oyuncu makro klavyeleriyle aynı
fikir. Cihazı kullanıcı takar, ayarları kullanıcı belirler, davranışı görünürdür.
Başkasının cihazında habersiz çalıştırmak amacı taşımaz.
