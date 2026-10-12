#pragma once
#include <cstdint>
#include <memory>
#include "ayarlar.h"
#include "baslatici.h"
#include "durum.h"
#include "gozlemci.h"
#include "klavye_cikti.h"
#include "makro.h"
#include "saat.h"

namespace makro {

// Surucu: tüm parçaları birleştiren üst katman (Facade/Cephe). Ayarlardan
// makroları kurar (Builder + Strategy), durum makinesini (State) yönetir,
// tuşları çıktıya (Adapter) gönderir. Dışarıya küçük bir arayüz sunar:
// baslat / birTur / durdur / calis.
//
// Donanımdan tamamen bağımsızdır: KlavyeCikti ve Saat soyut arabirimler olarak
// dışarıdan verilir (Bağımlılık Enjeksiyonu). Bu yüzden aynı Surucu hem gerçek
// STM32'de hem de bilgisayardaki benzetimde/testte çalışır.
class Surucu : public DurumBaglami {
public:
    Surucu(const Ayarlar& ayar,
           std::unique_ptr<PlatformBaslatici> baslatici,
           KlavyeCikti& cikti,
           Saat& saat,
           DurumGozlemci* gozlemci = nullptr);

    // Dışa açık komutlar (geçerli duruma devredilir).
    void baslat();   // tarayıcıyı aç, çalışmaya başla
    void birTur();   // bir makro turu (tüm tuşlara birer kez bas)
    void durdur();   // duraklat/bitir

    // Kolaylık: açılış + istenen sayıda tur (benzetim ve testler için).
    // Gerçek cihazda sonsuz tekrar, Arduino loop() içinde birTur() ile sağlanır.
    void calis(uint32_t turSayisi);

    Durum durum() const { return durum_->kimlik(); }
    uint32_t yapilanTur() const { return yapilanTur_; }

    // DurumBaglami arabirimi (durum sınıfları bunları çağırır):
    void tarayiciyiAc() override;
    void makroTuru() override;
    void durumaGec(Durum yeni) override;

private:
    void gozlemciBildir(Durum d);

    Ayarlar ayar_;
    std::unique_ptr<PlatformBaslatici> baslatici_;
    KlavyeCikti& cikti_;
    Saat& saat_;
    DurumGozlemci* gozlemci_;

    Makro acilisMakrosu_;  // tarayıcıyı açan komutlar
    Makro turMakrosu_;     // bir tur: her tuş + aralık
    std::unique_ptr<DurumSoyut> durum_;
    uint32_t yapilanTur_ = 0;
};

}  // namespace makro
