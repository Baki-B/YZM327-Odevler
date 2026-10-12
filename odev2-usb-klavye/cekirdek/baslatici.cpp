#include "baslatici.h"

namespace makro {

void WindowsBaslatici::komutlariEkle(MakroYapici& yapici, const Ayarlar& ayar) const {
    // Win+R → Çalıştır kutusu açılır
    yapici.kisayol({OzelTus::GUI}, 'r')
        .bekle(400)                           // kutu açılsın
        .metin("chrome " + ayar.url)          // tarayıcıyı adresle çalıştır
        .ozel(OzelTus::ENTER);
}

void LinuxBaslatici::komutlariEkle(MakroYapici& yapici, const Ayarlar& ayar) const {
    // Terminal aç (varsayılan Ctrl+Alt+T; masaüstüne göre ayarlanabilir)
    yapici.kisayol(ayar.linuxTerminalDegistiriciler, ayar.linuxTerminalHarf)
        .bekle(600)                           // terminal açılsın
        .metin("xdg-open " + ayar.url)        // adresi varsayılan tarayıcıda aç
        .ozel(OzelTus::ENTER);
}

std::unique_ptr<PlatformBaslatici> baslaticiYap(Platform platform) {
    switch (platform) {
        case Platform::WINDOWS: return std::make_unique<WindowsBaslatici>();
        case Platform::LINUX:   return std::make_unique<LinuxBaslatici>();
    }
    return std::make_unique<WindowsBaslatici>();
}

}  // namespace makro
