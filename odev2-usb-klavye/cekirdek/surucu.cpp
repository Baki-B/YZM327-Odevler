#include "surucu.h"

namespace makro {

namespace {

// Ayarlardan açılış makrosunu kurar: platform stratejisi + ardından tarayıcının
// açılması için bekleme.
Makro acilisMakrosuKur(const PlatformBaslatici& baslatici, const Ayarlar& ayar) {
    MakroYapici yapici;
    baslatici.komutlariEkle(yapici, ayar);
    yapici.bekle(ayar.baslangicGecikmeMs);
    return yapici.kur();
}

// Ayarlardan bir makro turunu kurar: her tuşa bas, aralık kadar bekle.
Makro turMakrosuKur(const Ayarlar& ayar) {
    MakroYapici yapici;
    for (char t : ayar.tuslar) yapici.harf(t).bekle(ayar.aralikMs);
    return yapici.kur();
}

}  // namespace

Surucu::Surucu(const Ayarlar& ayar,
               std::unique_ptr<PlatformBaslatici> baslatici,
               KlavyeCikti& cikti,
               Saat& saat,
               DurumGozlemci* gozlemci)
    : ayar_(ayar),
      baslatici_(std::move(baslatici)),
      cikti_(cikti),
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
    // BASLATILIYOR kalıcı bir durum değil, anlık bir evredir; yalnızca gözlemciye bildirilir.
    gozlemciBildir(Durum::BASLATILIYOR);
    acilisMakrosu_.calistir(cikti_, saat_);
}

void Surucu::makroTuru() {
    turMakrosu_.calistir(cikti_, saat_);
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
