#pragma once
#include <iostream>
#include "../cekirdek/fare.h"

namespace makro {

// FareCikti'nin benzetim uyarlaması (Adapter): gerçek tık yerine ne yapılacağını
// konsola yazar.
class KonsolFare : public FareCikti {
public:
    explicit KonsolFare(std::ostream& akis = std::cout) : akis_(akis) {}

    void tikla(FareDugme dugme) override { akis_ << "  fare   : [" << fareDugmeAdi(dugme) << " tik]\n"; }
    void bas(FareDugme dugme) override { akis_ << "  fare   : [" << fareDugmeAdi(dugme) << " bas]\n"; }
    void birak(FareDugme dugme) override { akis_ << "  fare   : [" << fareDugmeAdi(dugme) << " birak]\n"; }

private:
    std::ostream& akis_;
};

}  // namespace makro
