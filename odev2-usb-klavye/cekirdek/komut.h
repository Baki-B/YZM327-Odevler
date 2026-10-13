#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include "cihaz.h"
#include "fare.h"
#include "tuslar.h"

// Command (Komut) deseni: her makro adımı, "kendini çalıştır" diyebilen küçük
// bir nesnedir. Çalıştırırken cihazın giriş-çıkışını (klavye + fare + saat) tek
// bir Cihaz bağlamından alır. Yeni bir adım türü eklemek, var olan döngüyü
// değiştirmeden yeni bir Komut sınıfı yazmaktır (Açık/Kapalı ilkesi).
namespace makro {

struct Komut {
    virtual ~Komut() = default;
    virtual void calistir(Cihaz& cihaz) = 0;
    virtual std::string tanim() const = 0;  // günlük/test için okunur açıklama
};

// Düz metin yaz (URL, komut satırı).
struct MetinYazKomutu : Komut {
    std::string metin;
    explicit MetinYazKomutu(std::string m) : metin(std::move(m)) {}
    void calistir(Cihaz& c) override { c.klavye.metinYaz(metin); }
    std::string tanim() const override { return "metin:" + metin; }
};

// Tek özel tuşa bas (ENTER gibi).
struct OzelTusKomutu : Komut {
    OzelTus tus;
    explicit OzelTusKomutu(OzelTus t) : tus(t) {}
    void calistir(Cihaz& c) override { c.klavye.ozelTusVur(tus); }
    std::string tanim() const override { return std::string("ozel:") + ozelTusAdi(tus); }
};

// Kısayol: değiştiriciler basılıyken bir harf (GUI+R gibi).
struct KisayolKomutu : Komut {
    std::vector<OzelTus> degistiriciler;
    char harf;
    KisayolKomutu(std::vector<OzelTus> d, char h) : degistiriciler(std::move(d)), harf(h) {}
    void calistir(Cihaz& c) override { c.klavye.kisayol(degistiriciler, harf); }
    std::string tanim() const override;
};

// Tek harf tuşuna bas (oyun tuşu).
struct HarfKomutu : Komut {
    char harf;
    explicit HarfKomutu(char h) : harf(h) {}
    void calistir(Cihaz& c) override { c.klavye.harfVur(harf); }
    std::string tanim() const override { return std::string("harf:") + harf; }
};

// Fare tıkla (sol/sağ) — asıl farm eylemi.
struct FareTiklaKomutu : Komut {
    FareDugme dugme;
    explicit FareTiklaKomutu(FareDugme d) : dugme(d) {}
    void calistir(Cihaz& c) override { c.fare.tikla(dugme); }
    std::string tanim() const override { return std::string("fare:") + fareDugmeAdi(dugme); }
};

// Belirtilen süre kadar bekle.
struct BeklemeKomutu : Komut {
    uint32_t ms;
    explicit BeklemeKomutu(uint32_t m) : ms(m) {}
    void calistir(Cihaz& c) override { c.saat.bekle(ms); }
    std::string tanim() const override { return "bekle:" + std::to_string(ms); }
};

}  // namespace makro
