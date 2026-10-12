#pragma once
#include <memory>
#include "gozlemci.h"

// State (Durum) deseni: cihazın her yaşam döngüsü durumu ayrı bir sınıftır ve
// aynı isteğe (baslat / birTur / durdur) farklı tepki verir. Böylece "if durum
// == ... " zincirleri yerine, davranış durum sınıflarına dağılır; yeni bir
// durum eklemek var olanları değiştirmeden mümkün olur.
namespace makro {

// Durum sınıflarının üzerinde iş gördüğü bağlam (context). Sürücü bunu uygular.
// Durum sınıfları somut Sürücü'ye değil bu soyut arabirime bağlıdır (DIP).
struct DurumBaglami {
    virtual ~DurumBaglami() = default;
    virtual void tarayiciyiAc() = 0;        // açılış (launcher) komutlarını çalıştır
    virtual void makroTuru() = 0;           // bir makro turu çalıştır
    virtual void durumaGec(Durum yeni) = 0; // başka duruma geç
};

struct DurumSoyut {
    virtual ~DurumSoyut() = default;
    virtual Durum kimlik() const = 0;
    virtual void baslat(DurumBaglami& ctx) = 0;
    virtual void birTur(DurumBaglami& ctx) = 0;
    virtual void durdur(DurumBaglami& ctx) = 0;
};

// Durum kimliğine karşılık gelen durum nesnesini üretir (State için küçük fabrika).
std::unique_ptr<DurumSoyut> durumNesnesiYap(Durum d);

}  // namespace makro
