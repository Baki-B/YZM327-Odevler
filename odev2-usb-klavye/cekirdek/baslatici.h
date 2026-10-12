#pragma once
#include <memory>
#include <string>
#include "ayarlar.h"
#include "makro.h"

namespace makro {

// Strategy (Strateji) deseni: "tarayıcıyı/uygulamayı aç" işi işletim sistemine
// göre farklı tuş dizileri gerektirir. Her platform bu arabirimi ayrı uygular;
// çekirdek yalnızca soyut arabirimi tanır. Yeni bir platform eklemek, var olan
// kodu değiştirmeden yeni bir sınıf yazmaktır (Açık/Kapalı ilkesi).
struct PlatformBaslatici {
    virtual ~PlatformBaslatici() = default;
    // Verilen yapıcıya, tarayıcıyı açacak komutları ekler.
    virtual void komutlariEkle(MakroYapici& yapici, const Ayarlar& ayar) const = 0;
    virtual std::string ad() const = 0;
};

// Windows: Çalıştır kutusu (Win+R) → "chrome <url>" → Enter.
struct WindowsBaslatici : PlatformBaslatici {
    void komutlariEkle(MakroYapici& yapici, const Ayarlar& ayar) const override;
    std::string ad() const override { return "Windows"; }
};

// Linux: terminal kısayolu → "xdg-open <url>" → Enter.
// (Terminal kısayolu masaüstüne göre değişir; ayarlardan gelir.)
struct LinuxBaslatici : PlatformBaslatici {
    void komutlariEkle(MakroYapici& yapici, const Ayarlar& ayar) const override;
    std::string ad() const override { return "Linux"; }
};

// Factory (Fabrika): platforma göre doğru stratejiyi üretir. Çağıran kod
// hangi somut sınıfın kurulduğunu bilmez.
std::unique_ptr<PlatformBaslatici> baslaticiYap(Platform platform);

}  // namespace makro
