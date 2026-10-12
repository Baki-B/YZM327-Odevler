#include "../cekirdek/komut.h"
#include "mini_test.h"
#include "sahteler.h"

using namespace makro;

TEST(komut_metin_yazar) {
    KayitKlavye k;
    SahteSaat s;
    MetinYazKomutu("merhaba").calistir(k, s);
    CHECK_EQ(k.birlesik(), std::string("YAZ:merhaba"));
}

TEST(komut_harf_vurur) {
    KayitKlavye k;
    SahteSaat s;
    HarfKomutu('a').calistir(k, s);
    CHECK_EQ(k.birlesik(), std::string("HARF:a"));
}

TEST(komut_ozel_tus) {
    KayitKlavye k;
    SahteSaat s;
    OzelTusKomutu(OzelTus::ENTER).calistir(k, s);
    CHECK_EQ(k.birlesik(), std::string("OZEL:ENTER"));
}

TEST(komut_kisayol) {
    KayitKlavye k;
    SahteSaat s;
    KisayolKomutu({OzelTus::GUI}, 'r').calistir(k, s);
    CHECK_EQ(k.birlesik(), std::string("KIS:GUI+r"));
}

TEST(komut_bekleme_saati_cagirir) {
    KayitKlavye k;
    SahteSaat s;
    BeklemeKomutu(250).calistir(k, s);
    CHECK(k.olaylar.empty());  // tuş göndermez
    CHECK_EQ(s.toplam, static_cast<uint32_t>(250));
}

TEST(komut_tanimlari) {
    CHECK_EQ(MetinYazKomutu("x").tanim(), std::string("metin:x"));
    CHECK_EQ(HarfKomutu('q').tanim(), std::string("harf:q"));
    CHECK_EQ(OzelTusKomutu(OzelTus::TAB).tanim(), std::string("ozel:TAB"));
    CHECK_EQ(BeklemeKomutu(100).tanim(), std::string("bekle:100"));
    CHECK_EQ(KisayolKomutu({OzelTus::CTRL, OzelTus::ALT}, 't').tanim(),
             std::string("kisayol:CTRL+ALT+t"));
}
