#pragma once
#include <cstdint>

// Saat: zaman geçişini soyutlar (DIP). Gerçek cihazda milis/gecikme donanımdan
// gelir; testlerde sahte bir saat gerçek zaman beklemeden geçen süreyi sayar,
// böylece zamanlama mantığı saniyelerce beklemeden, kararlı biçimde test edilir.
namespace makro {

struct Saat {
    virtual ~Saat() = default;

    // ms kadar bekle (gerçek cihazda gerçekten bekler; testte yalnızca sayar).
    virtual void bekle(uint32_t ms) = 0;

    // Açılıştan beri geçen milisaniye (isteğe bağlı kullanım).
    virtual uint32_t suAn() const = 0;
};

}  // namespace makro
