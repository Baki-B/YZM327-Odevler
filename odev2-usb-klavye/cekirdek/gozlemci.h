#pragma once

// Cihazın yaşam döngüsü durumları ve durum değişikliklerini dinleyen gözlemci.
namespace makro {

enum class Durum {
    BEKLIYOR,       // takıldı, henüz bir şey yapmadı
    BASLATILIYOR,   // tarayıcı/uygulama açılıyor
    CALISIYOR,      // makro (tuşlara basma) çalışıyor
    DURAKLATILDI,   // geçici durdu
    BITTI,          // tekrar sayısı dolunca
};

const char* durumAdi(Durum d);

// Observer (Gözlemci) deseni: sürücü durum değiştikçe bu arabirimi uygulayan
// nesnelere haber verir. Gerçek cihazda bir LED'i yakıp söndürmek, benzetimde
// konsola yazmak için kullanılır. Sürücü, kaç gözlemci olduğunu ya da ne
// yaptıklarını bilmez (gevşek bağ).
struct DurumGozlemci {
    virtual ~DurumGozlemci() = default;
    virtual void durumDegisti(Durum yeni) = 0;
};

inline const char* durumAdi(Durum d) {
    switch (d) {
        case Durum::BEKLIYOR:     return "BEKLIYOR";
        case Durum::BASLATILIYOR: return "BASLATILIYOR";
        case Durum::CALISIYOR:    return "CALISIYOR";
        case Durum::DURAKLATILDI: return "DURAKLATILDI";
        case Durum::BITTI:        return "BITTI";
    }
    return "?";
}

}  // namespace makro
