#pragma once
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>
#include "fare.h"
#include "tuslar.h"

namespace makro {

enum class Platform { WINDOWS, LINUX };

// Tekrarlanan eylem klavye tuşu mu, fare tıklaması mı?
// TUS  : oyun tuşlarına bas (ör. a,s,d).
// FARE : fare düğmelerine tıkla (ör. sol/sağ) — .io farm oyunlarında asıl eylem.
enum class Eylem { TUS, FARE };

// Yapılandırma ayrıştırılırken oluşan hatalar.
struct AyarHatasi : std::runtime_error {
    using std::runtime_error::runtime_error;
};

// Ayarlar: cihazın davranışını belirleyen tüm seçenekler tek yerde.
// "Hangi tuşlara, ne sıklıkla, kaç kez; hangi adres; hangi işletim sistemi."
struct Ayarlar {
    Platform platform = Platform::WINDOWS;
    bool tarayiciAc = true;                       // false: tarayıcı açma, sadece eylemi tekrarla
    std::string url = "https://baki-b.github.io/YZM327-Odevler/";

    Eylem eylem = Eylem::TUS;                      // tekrarlanan eylem: tuş mu, fare mi
    std::vector<char> tuslar = {'a', 's', 'd'};    // eylem=TUS iken sırayla basılacak tuşlar
    std::vector<FareDugme> fareDugmeleri = {FareDugme::SOL};  // eylem=FARE iken tıklanacak düğmeler

    uint32_t aralikMs = 200;                       // her eylem arası bekleme
    uint32_t tekrar = 0;                           // kaç tur; 0 = sonsuz (cihazda)
    uint32_t baslangicGecikmeMs = 1500;            // tarayıcı açılsın diye ilk bekleme

    // Linux masaüstlerinde terminal açma kısayolu masaüstüne göre değişir;
    // bu yüzden ayarlanabilir (varsayılan: Ctrl+Alt+T).
    std::vector<OzelTus> linuxTerminalDegistiriciler = {OzelTus::CTRL, OzelTus::ALT};
    char linuxTerminalHarf = 't';

    // Basit, satır tabanlı metin yapılandırmasını ayrıştırır:
    //   # yorum
    //   platform = windows | linux
    //   tarayici_ac = evet | hayir
    //   url = https://...
    //   eylem = tus | fare
    //   tuslar = a,s,d
    //   fare_dugmeleri = sol,sag
    //   aralik_ms = 200
    //   tekrar = 0
    //   baslangic_gecikme_ms = 1500
    //   linux_terminal = ctrl+alt+t
    // Bilinmeyen anahtar ya da geçersiz değer AyarHatasi fırlatır.
    static Ayarlar metinden(const std::string& metin);
};

}  // namespace makro
