#include "tuslar.h"

namespace makro {

const char* ozelTusAdi(OzelTus tus) {
    switch (tus) {
        case OzelTus::ENTER:  return "ENTER";
        case OzelTus::TAB:    return "TAB";
        case OzelTus::ESC:    return "ESC";
        case OzelTus::BOSLUK: return "BOSLUK";
        case OzelTus::GUI:    return "GUI";
        case OzelTus::CTRL:   return "CTRL";
        case OzelTus::ALT:    return "ALT";
        case OzelTus::SHIFT:  return "SHIFT";
    }
    return "?";
}

}  // namespace makro
