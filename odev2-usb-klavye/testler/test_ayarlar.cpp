#include <string>
#include "../cekirdek/ayarlar.h"
#include "mini_test.h"

using makro::Ayarlar;
using makro::AyarHatasi;
using makro::Eylem;
using makro::FareDugme;
using makro::OzelTus;
using makro::Platform;

TEST(ayarlar_varsayilanlar) {
    Ayarlar a;
    CHECK(a.platform == Platform::WINDOWS);
    CHECK_EQ(a.tuslar.size(), static_cast<std::size_t>(3));
    CHECK_EQ(a.aralikMs, static_cast<uint32_t>(200));
    CHECK_EQ(a.tekrar, static_cast<uint32_t>(0));
}

TEST(ayarlar_tam_yapilandirma) {
    std::string metin =
        "# ornek ayar\n"
        "platform = linux\n"
        "url = https://ornek.test/sayfa\n"
        "tuslar = w,a,s,d\n"
        "aralik_ms = 150\n"
        "tekrar = 5\n"
        "baslangic_gecikme_ms = 1000\n";
    Ayarlar a = Ayarlar::metinden(metin);
    CHECK(a.platform == Platform::LINUX);
    CHECK_EQ(a.url, std::string("https://ornek.test/sayfa"));
    CHECK_EQ(a.tuslar.size(), static_cast<std::size_t>(4));
    CHECK_EQ(a.tuslar[0], 'w');
    CHECK_EQ(a.tuslar[3], 'd');
    CHECK_EQ(a.aralikMs, static_cast<uint32_t>(150));
    CHECK_EQ(a.tekrar, static_cast<uint32_t>(5));
    CHECK_EQ(a.baslangicGecikmeMs, static_cast<uint32_t>(1000));
}

TEST(ayarlar_linux_terminal_kisayolu) {
    Ayarlar a = Ayarlar::metinden("linux_terminal = ctrl+shift+n\n");
    CHECK_EQ(a.linuxTerminalDegistiriciler.size(), static_cast<std::size_t>(2));
    CHECK(a.linuxTerminalDegistiriciler[0] == OzelTus::CTRL);
    CHECK(a.linuxTerminalDegistiriciler[1] == OzelTus::SHIFT);
    CHECK_EQ(a.linuxTerminalHarf, 'n');
}

TEST(ayarlar_yorum_ve_bos_satir_atlanir) {
    Ayarlar a = Ayarlar::metinden("\n  # sadece yorum\n\naralik_ms = 42 # satir sonu yorumu\n");
    CHECK_EQ(a.aralikMs, static_cast<uint32_t>(42));
}

TEST(ayarlar_fare_eylemi) {
    Ayarlar a = Ayarlar::metinden(
        "eylem = fare\n"
        "tarayici_ac = hayir\n"
        "fare_dugmeleri = sol,sag\n");
    CHECK(a.eylem == Eylem::FARE);
    CHECK(a.tarayiciAc == false);
    CHECK_EQ(a.fareDugmeleri.size(), static_cast<std::size_t>(2));
    CHECK(a.fareDugmeleri[0] == FareDugme::SOL);
    CHECK(a.fareDugmeleri[1] == FareDugme::SAG);
}

TEST(ayarlar_varsayilan_eylem_tus) {
    Ayarlar a;
    CHECK(a.eylem == Eylem::TUS);
    CHECK(a.tarayiciAc == true);
}

TEST(ayarlar_gecersiz_eylem_hata) {
    bool hata = false;
    try { Ayarlar::metinden("eylem = ayak\n"); } catch (const AyarHatasi&) { hata = true; }
    CHECK(hata);
}

TEST(ayarlar_gecersiz_fare_dugmesi_hata) {
    bool hata = false;
    try { Ayarlar::metinden("fare_dugmeleri = sol,ustmenu\n"); } catch (const AyarHatasi&) { hata = true; }
    CHECK(hata);
}

TEST(ayarlar_bilinmeyen_anahtar_hata) {
    bool hata = false;
    try {
        Ayarlar::metinden("bilinmeyen = 5\n");
    } catch (const AyarHatasi&) {
        hata = true;
    }
    CHECK(hata);
}

TEST(ayarlar_gecersiz_sayi_hata) {
    bool hata = false;
    try {
        Ayarlar::metinden("aralik_ms = abc\n");
    } catch (const AyarHatasi&) {
        hata = true;
    }
    CHECK(hata);
}

TEST(ayarlar_gecersiz_platform_hata) {
    bool hata = false;
    try {
        Ayarlar::metinden("platform = macos\n");
    } catch (const AyarHatasi&) {
        hata = true;
    }
    CHECK(hata);
}

TEST(ayarlar_cok_harfli_tus_hata) {
    bool hata = false;
    try {
        Ayarlar::metinden("tuslar = a,bc,d\n");
    } catch (const AyarHatasi&) {
        hata = true;
    }
    CHECK(hata);
}
