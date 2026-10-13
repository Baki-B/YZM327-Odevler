#include "ayarlar.h"

#include <algorithm>
#include <cctype>
#include <sstream>

namespace makro {
namespace {

std::string kirp(const std::string& s) {
    std::size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
    return s.substr(b, e - b);
}

std::string kucuk(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return s;
}

std::vector<std::string> parcala(const std::string& s, char ayrac) {
    std::vector<std::string> parcalar;
    std::stringstream ss(s);
    std::string p;
    while (std::getline(ss, p, ayrac)) parcalar.push_back(kirp(p));
    return parcalar;
}

uint32_t sayiya(const std::string& anahtar, const std::string& deger) {
    try {
        std::size_t son = 0;
        unsigned long v = std::stoul(deger, &son);
        if (son != deger.size()) throw std::invalid_argument("artık karakter");
        return static_cast<uint32_t>(v);
    } catch (const std::exception&) {
        throw AyarHatasi("'" + anahtar + "' için sayı bekleniyordu: '" + deger + "'");
    }
}

OzelTus degistiriciye(const std::string& ad) {
    std::string a = kucuk(ad);
    if (a == "ctrl") return OzelTus::CTRL;
    if (a == "alt") return OzelTus::ALT;
    if (a == "shift") return OzelTus::SHIFT;
    if (a == "gui" || a == "win" || a == "super" || a == "cmd") return OzelTus::GUI;
    throw AyarHatasi("bilinmeyen değiştirici tuş: '" + ad + "'");
}

FareDugme fareDugmeye(const std::string& ad) {
    std::string a = kucuk(ad);
    if (a == "sol" || a == "left") return FareDugme::SOL;
    if (a == "sag" || a == "sağ" || a == "right") return FareDugme::SAG;
    if (a == "orta" || a == "middle") return FareDugme::ORTA;
    throw AyarHatasi("bilinmeyen fare düğmesi: '" + ad + "'");
}

bool evetMi(const std::string& anahtar, const std::string& deger) {
    std::string d = kucuk(deger);
    if (d == "evet" || d == "true" || d == "1" || d == "aç" || d == "ac") return true;
    if (d == "hayir" || d == "hayır" || d == "false" || d == "0" || d == "kapa") return false;
    throw AyarHatasi("'" + anahtar + "' evet/hayir olmalı: '" + deger + "'");
}

}  // namespace

Ayarlar Ayarlar::metinden(const std::string& metin) {
    Ayarlar a;
    std::stringstream ss(metin);
    std::string satir;
    while (std::getline(ss, satir)) {
        // Yorumu at.
        auto diyez = satir.find('#');
        if (diyez != std::string::npos) satir = satir.substr(0, diyez);
        satir = kirp(satir);
        if (satir.empty()) continue;

        auto esit = satir.find('=');
        if (esit == std::string::npos)
            throw AyarHatasi("'=' içermeyen satır: '" + satir + "'");
        std::string anahtar = kucuk(kirp(satir.substr(0, esit)));
        std::string deger = kirp(satir.substr(esit + 1));

        if (anahtar == "platform") {
            std::string d = kucuk(deger);
            if (d == "windows") a.platform = Platform::WINDOWS;
            else if (d == "linux") a.platform = Platform::LINUX;
            else throw AyarHatasi("platform windows ya da linux olmalı: '" + deger + "'");
        } else if (anahtar == "tarayici_ac") {
            a.tarayiciAc = evetMi(anahtar, deger);
        } else if (anahtar == "url") {
            if (deger.empty()) throw AyarHatasi("url boş olamaz");
            a.url = deger;
        } else if (anahtar == "eylem") {
            std::string d = kucuk(deger);
            if (d == "tus" || d == "tuş") a.eylem = Eylem::TUS;
            else if (d == "fare" || d == "mouse") a.eylem = Eylem::FARE;
            else throw AyarHatasi("eylem tus ya da fare olmalı: '" + deger + "'");
        } else if (anahtar == "fare_dugmeleri") {
            std::vector<FareDugme> d;
            for (const auto& parca : parcala(deger, ','))
                if (!parca.empty()) d.push_back(fareDugmeye(parca));
            if (d.empty()) throw AyarHatasi("en az bir fare düğmesi gerekli");
            a.fareDugmeleri = d;
        } else if (anahtar == "tuslar") {
            std::vector<char> t;
            for (const auto& parca : parcala(deger, ',')) {
                if (parca.size() != 1)
                    throw AyarHatasi("her tuş tek karakter olmalı: '" + parca + "'");
                t.push_back(parca[0]);
            }
            if (t.empty()) throw AyarHatasi("en az bir tuş gerekli");
            a.tuslar = t;
        } else if (anahtar == "aralik_ms") {
            a.aralikMs = sayiya(anahtar, deger);
        } else if (anahtar == "tekrar") {
            a.tekrar = sayiya(anahtar, deger);
        } else if (anahtar == "baslangic_gecikme_ms") {
            a.baslangicGecikmeMs = sayiya(anahtar, deger);
        } else if (anahtar == "linux_terminal") {
            auto parcalar = parcala(deger, '+');
            if (parcalar.size() < 2)
                throw AyarHatasi("linux_terminal en az bir değiştirici + bir harf olmalı (ör. ctrl+alt+t)");
            std::vector<OzelTus> mods;
            for (std::size_t i = 0; i + 1 < parcalar.size(); ++i)
                mods.push_back(degistiriciye(parcalar[i]));
            const std::string& son = parcalar.back();
            if (son.size() != 1)
                throw AyarHatasi("linux_terminal son parçası tek harf olmalı: '" + son + "'");
            a.linuxTerminalDegistiriciler = mods;
            a.linuxTerminalHarf = son[0];
        } else {
            throw AyarHatasi("bilinmeyen ayar anahtarı: '" + anahtar + "'");
        }
    }
    return a;
}

}  // namespace makro
