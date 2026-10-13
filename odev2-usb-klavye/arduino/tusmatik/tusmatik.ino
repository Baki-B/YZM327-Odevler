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
#include <Mouse.h>     // STM32duino USB-HID fare kütüphanesi

#include <memory>
#include <string>
#include <vector>

// Çekirdek arabirimleri ve sınıfları (tek kaynak — kopya yok).
#include "../../cekirdek/ayarlar.h"
#include "../../cekirdek/baslatici.h"
#include "../../cekirdek/fare.h"
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

// Soyut fare düğmesini Arduino fare koduna çevirir.
char arduinoFareKodu(makro::FareDugme d) {
    switch (d) {
        case makro::FareDugme::SOL:  return MOUSE_LEFT;
        case makro::FareDugme::SAG:  return MOUSE_RIGHT;
        case makro::FareDugme::ORTA: return MOUSE_MIDDLE;
    }
    return MOUSE_LEFT;
}

// FareCikti'nin gerçek USB-HID uyarlaması.
class ArduinoFare : public makro::FareCikti {
public:
    void tikla(makro::FareDugme d) override { Mouse.click(arduinoFareKodu(d)); }
    void bas(makro::FareDugme d) override { Mouse.press(arduinoFareKodu(d)); }
    void birak(makro::FareDugme d) override { Mouse.release(arduinoFareKodu(d)); }
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
ArduinoFare g_fare;
ArduinoSaat g_saat;
LedGozlemci g_led;
std::unique_ptr<makro::Surucu> g_surucu;

}  // namespace

// ---- Arduino yaşam döngüsü ----------------------------------------------

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Keyboard.begin();
    Mouse.begin();

    // Ayarlar burada elle belirlenir ("basit yol"). Değiştirip yeniden yükle.
    // (Metinden ayrıştırma — "esnek yol" — bilgisayar/benzetim tarafındadır.)
    //
    // Örnek: .io farm oyununda fare tıklama botu. Oyuncu karakteri ağacın yanına
    // götürüp oto-vuruşu ağaca ayarlar; cihaz takılınca sadece sol tık spamlar.
    makro::Ayarlar ayar;
    ayar.tarayiciAc = false;                 // oyuncu zaten oyunda; tarayıcı açma
    ayar.eylem = makro::Eylem::FARE;         // asıl eylem: fare tıklaması
    ayar.fareDugmeleri = {makro::FareDugme::SOL};  // sürekli sol tık (gerekirse SAG ekle)
    ayar.aralikMs = 150;                     // tıklar arası
    ayar.tekrar = 0;                         // 0 = sonsuz
    //
    // Alternatif — tarayıcı açıp tuş basan kullanım için:
    //   ayar.tarayiciAc = true; ayar.platform = makro::Platform::WINDOWS;
    //   ayar.url = "..."; ayar.eylem = makro::Eylem::TUS; ayar.tuslar = {'a','s','d'};

    g_surucu = std::make_unique<makro::Surucu>(
        ayar, makro::baslaticiYap(ayar.platform), g_klavye, g_fare, g_saat, &g_led);

    delay(1500);         // bilgisayar yeni aygıtı tanısın diye bekle
    g_surucu->baslat();  // (gerekiyorsa) tarayıcıyı aç, çalışmaya başla
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
