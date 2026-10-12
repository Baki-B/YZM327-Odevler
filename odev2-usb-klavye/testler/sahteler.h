#pragma once
// Test sahteleri (test doubles): gerçek klavye/saat/LED yerine davranışı kaydeden
// basit uygulamalar. KlavyeCikti ve Saat soyut olduğu için (DIP) test bunları
// sorunsuzca yerine koyabilir (Liskov: her yerde gerçeğinin yerini tutarlar).
#include <string>
#include <vector>

#include "../cekirdek/gozlemci.h"
#include "../cekirdek/klavye_cikti.h"
#include "../cekirdek/saat.h"

namespace makro {

// Gönderilen tuşları okunur dizgeler hâlinde kaydeder.
class KayitKlavye : public KlavyeCikti {
public:
    std::vector<std::string> olaylar;

    void metinYaz(const std::string& metin) override { olaylar.push_back("YAZ:" + metin); }
    void ozelTusVur(OzelTus tus) override {
        olaylar.push_back(std::string("OZEL:") + ozelTusAdi(tus));
    }
    void kisayol(const std::vector<OzelTus>& degistiriciler, char harf) override {
        std::string s = "KIS:";
        for (OzelTus t : degistiriciler) {
            s += ozelTusAdi(t);
            s += "+";
        }
        s += harf;
        olaylar.push_back(s);
    }
    void harfVur(char harf) override { olaylar.push_back(std::string("HARF:") + harf); }

    std::string birlesik(const std::string& ayrac = "|") const {
        std::string s;
        for (std::size_t i = 0; i < olaylar.size(); ++i) {
            if (i) s += ayrac;
            s += olaylar[i];
        }
        return s;
    }
};

// Gerçek zaman beklemeden, istenen beklemeleri kaydeder.
class SahteSaat : public Saat {
public:
    std::vector<uint32_t> beklemeler;
    uint32_t toplam = 0;

    void bekle(uint32_t ms) override {
        beklemeler.push_back(ms);
        toplam += ms;
    }
    uint32_t suAn() const override { return toplam; }
};

// Durum geçişlerini kaydeder.
class SahteGozlemci : public DurumGozlemci {
public:
    std::vector<Durum> gecisler;
    void durumDegisti(Durum yeni) override { gecisler.push_back(yeni); }
};

}  // namespace makro
