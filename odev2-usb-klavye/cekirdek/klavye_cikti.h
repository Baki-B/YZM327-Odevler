#pragma once
#include <string>
#include <vector>
#include "tuslar.h"

// KlavyeCikti: çekirdeğin dış dünyaya tuş göndermek için kullandığı SOYUT arabirim (port).
//
// Bağımlılığı Tersine Çevirme (DIP): üst katman olan çekirdek, somut bir
// donanıma değil bu arabirime bağlıdır. Gerçek cihazda STM32 USB-HID
// bağdaştırıcısı, testlerde kaydeden/yazan sahte bir sınıf bu arabirimi uygular
// (Bağdaştırıcı / Adapter deseni). Arabirim küçük ve tek amaçlı tutulur
// (Arabirim Ayrımı / ISP).
namespace makro {

struct KlavyeCikti {
    virtual ~KlavyeCikti() = default;

    // Düz metni (URL, komut satırı) harf harf yazar.
    virtual void metinYaz(const std::string& metin) = 0;

    // Tek bir özel tuşa bas-bırak (ör. ENTER).
    virtual void ozelTusVur(OzelTus tus) = 0;

    // Değiştirici tuşlar basılıyken bir harfe bas, sonra hepsini bırak (ör. GUI+R).
    virtual void kisayol(const std::vector<OzelTus>& degistiriciler, char harf) = 0;

    // Tek bir harf/karakter tuşuna bas-bırak (oyun tuşu; ör. 'a').
    virtual void harfVur(char harf) = 0;
};

}  // namespace makro
