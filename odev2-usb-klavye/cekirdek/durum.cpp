#include "durum.h"

namespace makro {
namespace {

// BEKLIYOR: takıldı, henüz bir şey yapmadı. "baslat" tarayıcıyı açar ve
// CALISIYOR'a geçer. Diğer istekler anlamsız olduğundan yok sayılır.
struct BekliyorDurumu : DurumSoyut {
    Durum kimlik() const override { return Durum::BEKLIYOR; }
    void baslat(DurumBaglami& ctx) override {
        ctx.tarayiciyiAc();
        ctx.durumaGec(Durum::CALISIYOR);  // sonrasında 'this' yok edilmiş olabilir
    }
    void birTur(DurumBaglami&) override {}  // önce baslat gerekir; yok say
    void durdur(DurumBaglami& ctx) override { ctx.durumaGec(Durum::BITTI); }
};

// CALISIYOR: makro çalışıyor. Her "birTur" bir makro turu çalıştırır.
struct CalisiyorDurumu : DurumSoyut {
    Durum kimlik() const override { return Durum::CALISIYOR; }
    void baslat(DurumBaglami&) override {}  // zaten başladı; yok say
    void birTur(DurumBaglami& ctx) override { ctx.makroTuru(); }
    void durdur(DurumBaglami& ctx) override { ctx.durumaGec(Durum::DURAKLATILDI); }
};

// DURAKLATILDI: geçici durdu. "baslat" kaldığı yerden devam ettirir.
struct DuraklatildiDurumu : DurumSoyut {
    Durum kimlik() const override { return Durum::DURAKLATILDI; }
    void baslat(DurumBaglami& ctx) override { ctx.durumaGec(Durum::CALISIYOR); }
    void birTur(DurumBaglami&) override {}  // duraklatıldı; yok say
    void durdur(DurumBaglami& ctx) override { ctx.durumaGec(Durum::BITTI); }
};

// BITTI: tekrar sayısı doldu. Artık hiçbir isteğe tepki vermez.
struct BittiDurumu : DurumSoyut {
    Durum kimlik() const override { return Durum::BITTI; }
    void baslat(DurumBaglami&) override {}
    void birTur(DurumBaglami&) override {}
    void durdur(DurumBaglami&) override {}
};

}  // namespace

std::unique_ptr<DurumSoyut> durumNesnesiYap(Durum d) {
    switch (d) {
        case Durum::BEKLIYOR:     return std::make_unique<BekliyorDurumu>();
        case Durum::CALISIYOR:    return std::make_unique<CalisiyorDurumu>();
        case Durum::DURAKLATILDI: return std::make_unique<DuraklatildiDurumu>();
        case Durum::BITTI:        return std::make_unique<BittiDurumu>();
        case Durum::BASLATILIYOR: return std::make_unique<BekliyorDurumu>();  // anlık evre; kalıcı durum değil
    }
    return std::make_unique<BekliyorDurumu>();
}

}  // namespace makro
