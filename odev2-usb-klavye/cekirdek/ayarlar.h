#pragma once
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>
#include "tuslar.h"

namespace makro {

enum class Platform { WINDOWS, LINUX };

// Yapılandırma ayrıştırılırken oluşan hatalar.
struct AyarHatasi : std::runtime_error {
    using std::runtime_error::runtime_error;
};

// Ayarlar: cihazın davranışını belirleyen tüm seçenekler tek yerde.
// "Hangi tuşlara, ne sıklıkla, kaç kez; hangi adres; hangi işletim sistemi."
struct Ayarlar {
    Platform platform = Platform::WINDOWS;
    std::string url = "https://baki-b.github.io/YZM327-Odevler/";
    std::vector<char> tuslar = {'a', 's', 'd'};  // sırayla basılacak oyun tuşları
    uint32_t aralikMs = 200;                      // her tuş arası bekleme
    uint32_t tekrar = 0;                          // kaç tur; 0 = sonsuz (cihazda)
    uint32_t baslangicGecikmeMs = 1500;           // tarayıcı açılsın diye ilk bekleme

    // Linux masaüstlerinde terminal açma kısayolu masaüstüne göre değişir;
    // bu yüzden ayarlanabilir (varsayılan: Ctrl+Alt+T).
    std::vector<OzelTus> linuxTerminalDegistiriciler = {OzelTus::CTRL, OzelTus::ALT};
    char linuxTerminalHarf = 't';

    // Basit, satır tabanlı metin yapılandırmasını ayrıştırır:
    //   # yorum
    //   platform = windows | linux
    //   url = https://...
    //   tuslar = a,s,d
    //   aralik_ms = 200
    //   tekrar = 0
    //   baslangic_gecikme_ms = 1500
    //   linux_terminal = ctrl+alt+t
    // Bilinmeyen anahtar ya da geçersiz değer AyarHatasi fırlatır.
    static Ayarlar metinden(const std::string& metin);
};

}  // namespace makro
