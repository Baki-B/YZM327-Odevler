#include "komut.h"

namespace makro {

std::string KisayolKomutu::tanim() const {
    std::string s = "kisayol:";
    for (OzelTus t : degistiriciler) {
        s += ozelTusAdi(t);
        s += "+";
    }
    s += harf;
    return s;
}

}  // namespace makro
