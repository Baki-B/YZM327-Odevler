// Benzetim: kart olmadan, cihazın bilgisayara takılınca ne yapacağını konsolda
// gösterir. İsteğe bağlı olarak bir yapılandırma dosyası alır:
//     ./benzetim [ayar_dosyasi]
// Dosya verilmezse varsayılan ayarlar (Windows, Agora adresi, a-s-d) kullanılır.
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "../cekirdek/ayarlar.h"
#include "../cekirdek/baslatici.h"
#include "../cekirdek/gozlemci.h"
#include "../cekirdek/surucu.h"
#include "konsol_fare.h"
#include "konsol_klavye.h"
#include "konsol_saat.h"

namespace {

// Observer: durum değiştikçe konsola yazar (gerçek cihazda bu bir LED olurdu).
class KonsolGozlemci : public makro::DurumGozlemci {
public:
    void durumDegisti(makro::Durum yeni) override {
        std::cout << "[durum] " << makro::durumAdi(yeni) << "\n";
    }
};

const char* platformAdi(makro::Platform p) {
    return p == makro::Platform::WINDOWS ? "Windows" : "Linux";
}

}  // namespace

int main(int argc, char** argv) {
    makro::Ayarlar ayar;

    if (argc > 1) {
        std::ifstream dosya(argv[1]);
        if (!dosya) {
            std::cerr << "Ayar dosyası açılamadı: " << argv[1] << "\n";
            return 2;
        }
        std::stringstream ss;
        ss << dosya.rdbuf();
        try {
            ayar = makro::Ayarlar::metinden(ss.str());
        } catch (const makro::AyarHatasi& e) {
            std::cerr << "Ayar hatası: " << e.what() << "\n";
            return 2;
        }
    }

    std::cout << "=== USB Makro Klavye+Fare — Benzetim ===\n";
    std::cout << "Platform    : " << platformAdi(ayar.platform) << "\n";
    std::cout << "Tarayici ac : " << (ayar.tarayiciAc ? "evet" : "hayir (sadece eylem)") << "\n";
    if (ayar.tarayiciAc) std::cout << "Adres       : " << ayar.url << "\n";
    if (ayar.eylem == makro::Eylem::FARE) {
        std::cout << "Eylem       : fare tik  ->  ";
        for (makro::FareDugme d : ayar.fareDugmeleri) std::cout << "[" << makro::fareDugmeAdi(d) << "] ";
    } else {
        std::cout << "Eylem       : tus       ->  ";
        for (char t : ayar.tuslar) std::cout << "'" << t << "' ";
    }
    std::cout << "\nAralik      : " << ayar.aralikMs << " ms\n";
    std::cout << "Tekrar      : " << (ayar.tekrar == 0 ? std::string("sonsuz (cihazda)") : std::to_string(ayar.tekrar)) << "\n";
    std::cout << "-----------------------------------\n";

    makro::KonsolKlavye klavye;
    makro::KonsolFare fare;
    makro::KonsolSaat saat;  // benzetimde gerçek bekleme yok
    KonsolGozlemci gozlemci;

    makro::Surucu surucu(ayar, makro::baslaticiYap(ayar.platform), klavye, fare, saat, &gozlemci);

    // Sonsuz tekrar benzetimde sonlanmaz; demo için 3 tur gösterilir.
    uint32_t turSayisi = (ayar.tekrar == 0) ? 3 : ayar.tekrar;
    surucu.calis(turSayisi);

    std::cout << "-----------------------------------\n";
    std::cout << "Gosterilen tur: " << surucu.yapilanTur()
              << "  |  Toplam benzetilen sure: " << saat.suAn() << " ms\n";
    if (ayar.tekrar == 0)
        std::cout << "(Gercek cihazda tekrar=0 oldugundan surekli devam eder.)\n";
    return 0;
}
