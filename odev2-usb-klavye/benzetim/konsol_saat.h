#pragma once
#include <chrono>
#include <iostream>
#include <thread>
#include "../cekirdek/saat.h"

namespace makro {

// Saat'in benzetim uyarlaması: beklemeleri konsola yazar. gercekBekle açıkken
// gerçek zamanda da bekler; kapalıyken (varsayılan) yalnızca süreyi sayar,
// böylece benzetim anında akar.
class KonsolSaat : public Saat {
public:
    explicit KonsolSaat(bool gercekBekle = false, std::ostream& akis = std::cout)
        : gercekBekle_(gercekBekle), akis_(akis) {}

    void bekle(uint32_t ms) override {
        akis_ << "  (bekle " << ms << " ms)\n";
        toplam_ += ms;
        if (gercekBekle_) std::this_thread::sleep_for(std::chrono::milliseconds(ms));
    }
    uint32_t suAn() const override { return toplam_; }

private:
    bool gercekBekle_;
    std::ostream& akis_;
    uint32_t toplam_ = 0;
};

}  // namespace makro
