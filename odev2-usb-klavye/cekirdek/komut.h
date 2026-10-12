#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include "klavye_cikti.h"
#include "saat.h"
#include "tuslar.h"

// Command (Komut) deseni: her makro adımı, "kendini çalıştır" diyebilen küçük
// bir nesnedir. Böylece makro, türünü bilmeden komutları sırayla işleten tek
// bir döngüden ibaret olur (Açık/Kapalı ilkesi: yeni bir adım türü eklemek,
// var olan döngüyü değiştirmeden yeni bir Komut sınıfı yazmaktır).
namespace makro {

struct Komut {
    virtual ~Komut() = default;
    virtual void calistir(KlavyeCikti& cikti, Saat& saat) = 0;
    virtual std::string tanim() const = 0;  // günlük/test için okunur açıklama
};

// Düz metin yaz (URL, komut satırı).
struct MetinYazKomutu : Komut {
    std::string metin;
    explicit MetinYazKomutu(std::string m) : metin(std::move(m)) {}
    void calistir(KlavyeCikti& cikti, Saat&) override { cikti.metinYaz(metin); }
    std::string tanim() const override { return "metin:" + metin; }
};

// Tek özel tuşa bas (ENTER gibi).
struct OzelTusKomutu : Komut {
    OzelTus tus;
    explicit OzelTusKomutu(OzelTus t) : tus(t) {}
    void calistir(KlavyeCikti& cikti, Saat&) override { cikti.ozelTusVur(tus); }
    std::string tanim() const override { return std::string("ozel:") + ozelTusAdi(tus); }
};

// Kısayol: değiştiriciler basılıyken bir harf (GUI+R gibi).
struct KisayolKomutu : Komut {
    std::vector<OzelTus> degistiriciler;
    char harf;
    KisayolKomutu(std::vector<OzelTus> d, char h) : degistiriciler(std::move(d)), harf(h) {}
    void calistir(KlavyeCikti& cikti, Saat&) override { cikti.kisayol(degistiriciler, harf); }
    std::string tanim() const override;
};

// Tek harf tuşuna bas (oyun tuşu).
struct HarfKomutu : Komut {
    char harf;
    explicit HarfKomutu(char h) : harf(h) {}
    void calistir(KlavyeCikti& cikti, Saat&) override { cikti.harfVur(harf); }
    std::string tanim() const override { return std::string("harf:") + harf; }
};

// Belirtilen süre kadar bekle.
struct BeklemeKomutu : Komut {
    uint32_t ms;
    explicit BeklemeKomutu(uint32_t m) : ms(m) {}
    void calistir(KlavyeCikti&, Saat& saat) override { saat.bekle(ms); }
    std::string tanim() const override { return "bekle:" + std::to_string(ms); }
};

}  // namespace makro
