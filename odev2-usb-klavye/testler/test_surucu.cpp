#include "../cekirdek/ayarlar.h"
#include "../cekirdek/baslatici.h"
#include "../cekirdek/surucu.h"
#include "mini_test.h"
#include "sahteler.h"

using namespace makro;

namespace {
Ayarlar temelAyar() {
    Ayarlar a;
    a.platform = Platform::WINDOWS;
    a.url = "https://ornek.test/";
    a.tuslar = {'a', 's', 'd'};
    a.aralikMs = 200;
    a.baslangicGecikmeMs = 1500;
    a.tekrar = 0;
    return a;
}
}  // namespace

TEST(surucu_acilis_sonra_turlar) {
    Ayarlar a = temelAyar();
    KayitKlavye k;
    SahteSaat s;
    SahteGozlemci g;
    Surucu surucu(a, baslaticiYap(a.platform), k, s, &g);

    surucu.calis(2);

    CHECK_EQ(k.birlesik(),
             std::string("KIS:GUI+r|YAZ:chrome https://ornek.test/|OZEL:ENTER|"
                         "HARF:a|HARF:s|HARF:d|HARF:a|HARF:s|HARF:d"));
    CHECK(surucu.durum() == Durum::CALISIYOR);  // tekrar=0, bitmez
    CHECK_EQ(surucu.yapilanTur(), static_cast<uint32_t>(2));
    // 400 (Win+R sonrası) + 1500 (baslangic) + 2 tur * 3 tus * 200
    CHECK_EQ(s.toplam, static_cast<uint32_t>(400 + 1500 + 2 * 3 * 200));
}

TEST(surucu_gozlemci_gecisleri) {
    Ayarlar a = temelAyar();
    KayitKlavye k;
    SahteSaat s;
    SahteGozlemci g;
    Surucu surucu(a, baslaticiYap(a.platform), k, s, &g);

    surucu.calis(1);

    CHECK_EQ(g.gecisler.size(), static_cast<std::size_t>(2));
    CHECK(g.gecisler[0] == Durum::BASLATILIYOR);
    CHECK(g.gecisler[1] == Durum::CALISIYOR);
}

TEST(surucu_tekrar_sinirinda_biter) {
    Ayarlar a = temelAyar();
    a.tekrar = 2;
    KayitKlavye k;
    SahteSaat s;
    SahteGozlemci g;
    Surucu surucu(a, baslaticiYap(a.platform), k, s, &g);

    surucu.calis(5);  // 5 istense de 2 turda biter

    CHECK_EQ(surucu.yapilanTur(), static_cast<uint32_t>(2));
    CHECK(surucu.durum() == Durum::BITTI);
    CHECK(g.gecisler.back() == Durum::BITTI);
}

TEST(surucu_baslatmadan_tur_yoksayilir) {
    Ayarlar a = temelAyar();
    KayitKlavye k;
    SahteSaat s;
    Surucu surucu(a, baslaticiYap(a.platform), k, s);

    surucu.birTur();  // önce baslat gerekir

    CHECK(k.olaylar.empty());
    CHECK(surucu.durum() == Durum::BEKLIYOR);
    CHECK_EQ(surucu.yapilanTur(), static_cast<uint32_t>(0));
}

TEST(surucu_durdur_ve_devam) {
    Ayarlar a = temelAyar();
    KayitKlavye k;
    SahteSaat s;
    Surucu surucu(a, baslaticiYap(a.platform), k, s);

    surucu.baslat();                              // CALISIYOR
    CHECK(surucu.durum() == Durum::CALISIYOR);
    surucu.durdur();                              // DURAKLATILDI
    CHECK(surucu.durum() == Durum::DURAKLATILDI);
    surucu.birTur();                              // duraklatıldı: yok sayılır
    CHECK_EQ(surucu.yapilanTur(), static_cast<uint32_t>(0));
    surucu.baslat();                              // devam -> CALISIYOR
    CHECK(surucu.durum() == Durum::CALISIYOR);
    surucu.birTur();                              // şimdi bir tur çalışır
    CHECK_EQ(surucu.yapilanTur(), static_cast<uint32_t>(1));
}
