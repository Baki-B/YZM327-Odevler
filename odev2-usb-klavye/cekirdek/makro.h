#pragma once
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include "cihaz.h"
#include "fare.h"
#include "komut.h"

namespace makro {

// Makro: sırayla çalıştırılacak komutlar dizisi. Komutların türünü bilmez,
// yalnızca hepsini sırayla çalıştırır.
class Makro {
public:
    void ekle(std::unique_ptr<Komut> k) { komutlar_.push_back(std::move(k)); }

    void calistir(Cihaz& cihaz) const {
        for (const auto& k : komutlar_) k->calistir(cihaz);
    }

    std::size_t boyut() const { return komutlar_.size(); }
    const std::vector<std::unique_ptr<Komut>>& komutlar() const { return komutlar_; }

private:
    std::vector<std::unique_ptr<Komut>> komutlar_;
};

// Builder (Yapıcı) deseni: makroyu adım adım, okunur bir akıcı arayüzle kurar.
class MakroYapici {
public:
    MakroYapici& metin(const std::string& m) {
        makro_.ekle(std::make_unique<MetinYazKomutu>(m));
        return *this;
    }
    MakroYapici& ozel(OzelTus t) {
        makro_.ekle(std::make_unique<OzelTusKomutu>(t));
        return *this;
    }
    MakroYapici& kisayol(std::vector<OzelTus> d, char h) {
        makro_.ekle(std::make_unique<KisayolKomutu>(std::move(d), h));
        return *this;
    }
    MakroYapici& harf(char h) {
        makro_.ekle(std::make_unique<HarfKomutu>(h));
        return *this;
    }
    MakroYapici& fareTikla(FareDugme d) {
        makro_.ekle(std::make_unique<FareTiklaKomutu>(d));
        return *this;
    }
    MakroYapici& bekle(uint32_t ms) {
        makro_.ekle(std::make_unique<BeklemeKomutu>(ms));
        return *this;
    }
    Makro kur() { return std::move(makro_); }

private:
    Makro makro_;
};

}  // namespace makro
