// USB Makro Klavye — STM32 (Arduino / STM32duino) donanım taslağı.
//
// Bu dosya DONANIM BAĞDAŞTIRICISIDIR: aynı çekirdeği (cekirdek/) kullanır ama
// soyut KlavyeCikti ve Saat arabirimlerini gerçek USB-HID klavye ve millis()/
// delay() ile uygular (Adapter deseni). Böylece bilgisayarda test edilen
// mantığın aynısı kartta çalışır; tek fark en alttaki ince donanım katmanıdır.
//
// Kart: STM32F411 "Black Pill" önerilir (USB-HID sağlam). USB aygıt desteği
// Arduino IDE'de "Tools > USB support: CDC + HID" (ya da en az HID) seçilerek
// açılmalıdır. Derleme/yükleme adımları: arduino/BENIOKU.md.

#include <Keyboard.h>  // STM32duino USB-HID klavye kütüphanesi

#include <memory>
#include <string>
#include <vector>

// Çekirdek arabirimleri ve sınıfları (tek kaynak — kopya yok).
#include "../../cekirdek/ayarlar.h"
#include "../../cekirdek/baslatici.h"
#include "../../cekirdek/gozlemci.h"
#include "../../cekirdek/klavye_cikti.h"
#include "../../cekirdek/saat.h"
#include "../../cekirdek/surucu.h"

// ---- Donanım bağdaştırıcıları -------------------------------------------

namespace {

// Soyut özel tuşu Arduino tuş koduna çevirir.
uint8_t arduinoKodu(makro::OzelTus t) {
    switch (t) {
        case makro::OzelTus::ENTER:  return KEY_RETURN;
        case makro::OzelTus::TAB:    return KEY_TAB;
        case makro::OzelTus::ESC:    return KEY_ESC;
        case makro::OzelTus::BOSLUK: return ' ';
        case makro::OzelTus::GUI:    return KEY_LEFT_GUI;
        case makro::OzelTus::CTRL:   return KEY_LEFT_CTRL;
        case makro::OzelTus::ALT:    return KEY_LEFT_ALT;
        case makro::OzelTus::SHIFT:  return KEY_LEFT_SHIFT;
    }
    return 0;
}

// KlavyeCikti'nin gerçek USB-HID uyarlaması.
class ArduinoKlavye : public makro::KlavyeCikti {
public:
    void metinYaz(const std::string& metin) override { Keyboard.print(metin.c_str()); }

    void ozelTusVur(makro::OzelTus tus) override { Keyboard.write(arduinoKodu(tus)); }

    void kisayol(const std::vector<makro::OzelTus>& degistiriciler, char harf) override {
        for (makro::OzelTus t : degistiriciler) Keyboard.press(arduinoKodu(t));
        Keyboard.press(harf);
        delay(20);
        Keyboard.releaseAll();
    }

    void harfVur(char harf) override { Keyboard.write(harf); }
};

// Saat'in gerçek uyarlaması (donanım zamanlayıcısı).
class ArduinoSaat : public makro::Saat {
public:
    void bekle(uint32_t ms) override { delay(ms); }
    uint32_t suAn() const override { return millis(); }
};

// Observer: durum değiştikçe kart üzerindeki LED'i yönetir (geri bildirim).
class LedGozlemci : public makro::DurumGozlemci {
public:
    void durumDegisti(makro::Durum yeni) override {
        digitalWrite(LED_BUILTIN, yeni == makro::Durum::CALISIYOR ? HIGH : LOW);
    }
};

// Nesneler setup()'tan sonra da yaşamalı: genel (global) tutulur.
ArduinoKlavye g_klavye;
ArduinoSaat g_saat;
LedGozlemci g_led;
std::unique_ptr<makro::Surucu> g_surucu;

}  // namespace

// ---- Arduino yaşam döngüsü ----------------------------------------------

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Keyboard.begin();

    // Ayarlar burada elle belirlenir ("basit yol"). Değiştirip yeniden yükle.
    // (Metinden ayrıştırma — "esnek yol" — bilgisayar/benzetim tarafındadır.)
    makro::Ayarlar ayar;
    ayar.platform = makro::Platform::WINDOWS;             // windows / linux
    ayar.url = "https://baki-b.github.io/YZM327-Odevler/";
    ayar.tuslar = {'a', 's', 'd'};
    ayar.aralikMs = 200;
    ayar.tekrar = 0;                                      // 0 = sonsuz
    ayar.baslangicGecikmeMs = 1500;

    g_surucu = std::make_unique<makro::Surucu>(
        ayar, makro::baslaticiYap(ayar.platform), g_klavye, g_saat, &g_led);

    delay(1500);         // bilgisayar yeni klavyeyi tanısın diye bekle
    g_surucu->baslat();  // tarayıcıyı aç, çalışmaya başla
}

void loop() {
    // Sonsuz tekrar burada sağlanır: her döngüde bir makro turu.
    // tekrar>0 ise çekirdek BITTI durumuna geçer ve turlar kendiliğinden durur.
    if (g_surucu && g_surucu->durum() == makro::Durum::CALISIYOR) {
        g_surucu->birTur();
    }
}

// ---- Çekirdek gerçekleştirmeleri (tek çeviri biriminde birleşik derleme) ---
// Arduino, sketch klasörü dışındaki .cpp dosyalarını ayrıca derlemez; bu yüzden
// çekirdeğin .cpp dosyaları buraya dahil edilir. ayarlar.cpp bilinçli olarak
// hariç tutulur (metin ayrıştırma yalnızca bilgisayar/test tarafında gerekir).
#include "../../cekirdek/baslatici.cpp"
#include "../../cekirdek/durum.cpp"
#include "../../cekirdek/komut.cpp"
#include "../../cekirdek/surucu.cpp"
#include "../../cekirdek/tuslar.cpp"
