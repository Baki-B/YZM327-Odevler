#include "../cekirdek/cihaz.h"
#include "../cekirdek/komut.h"
#include "mini_test.h"
#include "sahteler.h"

using namespace makro;

namespace {
// Her test için klavye+fare+saat'i tek bağlamda toplayan yardımcı.
struct Ortam {
    KayitGirdi g;
    SahteSaat s;
    Cihaz cihaz() { return Cihaz{g, g, s}; }
};
}  // namespace

TEST(komut_metin_yazar) {
    Ortam o;
    auto c = o.cihaz();
    MetinYazKomutu("merhaba").calistir(c);
    CHECK_EQ(o.g.birlesik(), std::string("YAZ:merhaba"));
}

TEST(komut_harf_vurur) {
    Ortam o;
    auto c = o.cihaz();
    HarfKomutu('a').calistir(c);
    CHECK_EQ(o.g.birlesik(), std::string("HARF:a"));
}

TEST(komut_ozel_tus) {
    Ortam o;
    auto c = o.cihaz();
    OzelTusKomutu(OzelTus::ENTER).calistir(c);
    CHECK_EQ(o.g.birlesik(), std::string("OZEL:ENTER"));
}

TEST(komut_kisayol) {
    Ortam o;
    auto c = o.cihaz();
    KisayolKomutu({OzelTus::GUI}, 'r').calistir(c);
    CHECK_EQ(o.g.birlesik(), std::string("KIS:GUI+r"));
}

TEST(komut_fare_tikla) {
    Ortam o;
    auto c = o.cihaz();
    FareTiklaKomutu(FareDugme::SOL).calistir(c);
    FareTiklaKomutu(FareDugme::SAG).calistir(c);
    CHECK_EQ(o.g.birlesik(), std::string("FARE:SOL|FARE:SAG"));
}

TEST(komut_bekleme_saati_cagirir) {
    Ortam o;
    auto c = o.cihaz();
    BeklemeKomutu(250).calistir(c);
    CHECK(o.g.olaylar.empty());  // tuş/tık göndermez
    CHECK_EQ(o.s.toplam, static_cast<uint32_t>(250));
}

TEST(komut_tanimlari) {
    CHECK_EQ(MetinYazKomutu("x").tanim(), std::string("metin:x"));
    CHECK_EQ(HarfKomutu('q').tanim(), std::string("harf:q"));
    CHECK_EQ(OzelTusKomutu(OzelTus::TAB).tanim(), std::string("ozel:TAB"));
    CHECK_EQ(BeklemeKomutu(100).tanim(), std::string("bekle:100"));
    CHECK_EQ(FareTiklaKomutu(FareDugme::SOL).tanim(), std::string("fare:SOL"));
    CHECK_EQ(KisayolKomutu({OzelTus::CTRL, OzelTus::ALT}, 't').tanim(),
             std::string("kisayol:CTRL+ALT+t"));
}
