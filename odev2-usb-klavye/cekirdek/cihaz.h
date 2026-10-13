#pragma once
#include "fare.h"
#include "klavye_cikti.h"
#include "saat.h"

namespace makro {

// Cihaz: komutların kullandığı giriş-çıkış bağlamı. Klavye, fare ve saat tek bir
// nesnede toplanır ve komutlara birlikte verilir (Parametre Nesnesi yaklaşımı).
// Böylece her komut imzasına ayrı ayrı klavye/fare/saat taşımak gerekmez ve yeni
// bir çıkış türü eklemek bu yapıyı genişletmekle olur.
struct Cihaz {
    KlavyeCikti& klavye;
    FareCikti& fare;
    Saat& saat;
};

}  // namespace makro
