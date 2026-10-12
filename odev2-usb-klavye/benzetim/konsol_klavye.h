#pragma once
#include <iostream>
#include <string>
#include "../cekirdek/klavye_cikti.h"

namespace makro {

// KlavyeCikti'nin benzetim uyarlaması (Adapter): gerçek tuş göndermek yerine,
// cihazın ne yapacağını okunur biçimde konsola yazar. Böylece kart olmadan
// makronun davranışı gözle görülür.
class KonsolKlavye : public KlavyeCikti {
public:
    explicit KonsolKlavye(std::ostream& akis = std::cout) : akis_(akis) {}

    void metinYaz(const std::string& metin) override {
        akis_ << "  yaz    : \"" << metin << "\"\n";
    }
    void ozelTusVur(OzelTus tus) override {
        akis_ << "  tus    : [" << ozelTusAdi(tus) << "]\n";
    }
    void kisayol(const std::vector<OzelTus>& degistiriciler, char harf) override {
        akis_ << "  kisayol: ";
        for (OzelTus t : degistiriciler) akis_ << "[" << ozelTusAdi(t) << "]+";
        akis_ << "'" << harf << "'\n";
    }
    void harfVur(char harf) override {
        akis_ << "  bas    : '" << harf << "'\n";
    }

private:
    std::ostream& akis_;
};

}  // namespace makro
