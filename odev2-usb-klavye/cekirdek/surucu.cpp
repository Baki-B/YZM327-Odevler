#include "surucu.h"

namespace makro {

namespace {

// Ayarlardan açılış makrosunu kurar: platform stratejisi + tarayıcının açılması
// için bekleme. (Yalnızca tarayiciAc açıksa kullanılır.)
Makro acilisMakrosuKur(const PlatformBaslatici& baslatici, const Ayarlar& ayar) {
    MakroYapici yapici;
    baslatici.komutlariEkle(yapici, ayar);
    yapici.bekle(ayar.baslangicGecikmeMs);
    return yapici.kur();
}

// Ayarlardan bir makro turunu kurar. Eylem türüne göre:
//  - TUS  : her tuşa bas, aralık kadar bekle.
//  - FARE : her fare düğmesine tıkla, aralık kadar bekle (asıl farm eylemi).
Makro turMakrosuKur(const Ayarlar& ayar) {
    MakroYapici yapici;
    if (ayar.eylem == Eylem::FARE) {
        for (FareDugme d : ayar.fareDugmeleri) yapici.fareTikla(d).bekle(ayar.aralikMs);
    } else {
        for (char t : ayar.tuslar) yapici.harf(t).bekle(ayar.aralikMs);
    }
    return yapici.kur();
}

}  // namespace

Surucu::Surucu(const Ayarlar& ayar,
               std::unique_ptr<PlatformBaslatici> baslatici,
               KlavyeCikti& klavye,
               FareCikti& fare,
               Saat& saat,
               DurumGozlemci* gozlemci)
    : ayar_(ayar),
      baslatici_(std::move(baslatici)),
      klavye_(klavye),
      fare_(fare),
      saat_(saat),
      gozlemci_(gozlemci),
      acilisMakrosu_(acilisMakrosuKur(*baslatici_, ayar_)),
      turMakrosu_(turMakrosuKur(ayar_)),
      durum_(durumNesnesiYap(Durum::BEKLIYOR)) {}

void Surucu::baslat() { durum_->baslat(*this); }
void Surucu::birTur() { durum_->birTur(*this); }
void Surucu::durdur() { durum_->durdur(*this); }

void Surucu::calis(uint32_t turSayisi) {
    baslat();
    for (uint32_t i = 0; i < turSayisi; ++i) {
        if (durum() != Durum::CALISIYOR) break;  // BITTI olduysa dur
        birTur();
    }
}

void Surucu::tarayiciyiAc() {
    // Oyuncu zaten oyundaysa tarayıcı açmaya gerek yok; makro sadece eylemi tekrarlar.
    if (!ayar_.tarayiciAc) return;
    // BASLATILIYOR kalıcı bir durum değil, anlık bir evredir; yalnızca gözlemciye bildirilir.
    gozlemciBildir(Durum::BASLATILIYOR);
    Cihaz c = cihaz();
    acilisMakrosu_.calistir(c);
}

void Surucu::makroTuru() {
    Cihaz c = cihaz();
    turMakrosu_.calistir(c);
    ++yapilanTur_;
    if (ayar_.tekrar > 0 && yapilanTur_ >= ayar_.tekrar) durumaGec(Durum::BITTI);
}

void Surucu::durumaGec(Durum yeni) {
    durum_ = durumNesnesiYap(yeni);
    gozlemciBildir(yeni);
}

void Surucu::gozlemciBildir(Durum d) {
    if (gozlemci_) gozlemci_->durumDegisti(d);
}

}  // namespace makro
