#pragma once
// Farenin (mouse) soyut çıkışı. Cihaz bileşik bir USB-HID aygıttır: hem klavye
// hem fare. Oyun farmında asıl eylem fare tıklamasıdır (sol/sağ).
namespace makro {

enum class FareDugme { SOL, SAG, ORTA };

inline const char* fareDugmeAdi(FareDugme d) {
    switch (d) {
        case FareDugme::SOL:  return "SOL";
        case FareDugme::SAG:  return "SAG";
        case FareDugme::ORTA: return "ORTA";
    }
    return "?";
}

// KlavyeCikti'nin kardeşi: farenin soyut arabirimi (port). Gerçek cihazda USB-HID
// fare, benzetim/testlerde sahte uygulamalar bunu gerçekler (Adapter + DIP + ISP).
struct FareCikti {
    virtual ~FareCikti() = default;
    virtual void tikla(FareDugme dugme) = 0;  // bas + bırak (tek tık)
    virtual void bas(FareDugme dugme) = 0;     // basılı tut
    virtual void birak(FareDugme dugme) = 0;
};

}  // namespace makro
