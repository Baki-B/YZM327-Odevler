#include "../cekirdek/ayarlar.h"
#include "../cekirdek/baslatici.h"
#include "../cekirdek/makro.h"
#include "mini_test.h"
#include "sahteler.h"

using namespace makro;

namespace {
// Başlatıcının ürettiği komutları sahte cihazda çalıştırıp olayları toplar.
std::string baslaticiOlaylari(const PlatformBaslatici& b, const Ayarlar& a) {
    MakroYapici yapici;
    b.komutlariEkle(yapici, a);
    Makro m = yapici.kur();
    KayitGirdi g;
    SahteSaat s;
    Cihaz c{g, g, s};
    m.calistir(c);
    return g.birlesik();
}
}  // namespace

TEST(windows_baslatici_dizisi) {
    Ayarlar a;
    a.url = "https://ornek.test/";
    WindowsBaslatici b;
    CHECK_EQ(baslaticiOlaylari(b, a),
             std::string("KIS:GUI+r|YAZ:chrome https://ornek.test/|OZEL:ENTER"));
}

TEST(linux_baslatici_dizisi) {
    Ayarlar a;
    a.platform = Platform::LINUX;
    a.url = "https://ornek.test/";
    LinuxBaslatici b;
    CHECK_EQ(baslaticiOlaylari(b, a),
             std::string("KIS:CTRL+ALT+t|YAZ:xdg-open https://ornek.test/|OZEL:ENTER"));
}

TEST(linux_baslatici_ozel_terminal_kisayolu) {
    Ayarlar a;
    a.platform = Platform::LINUX;
    a.url = "https://x.test/";
    a.linuxTerminalDegistiriciler = {OzelTus::GUI};
    a.linuxTerminalHarf = 'e';
    LinuxBaslatici b;
    CHECK_EQ(baslaticiOlaylari(b, a),
             std::string("KIS:GUI+e|YAZ:xdg-open https://x.test/|OZEL:ENTER"));
}

TEST(fabrika_dogru_stratejiyi_uretir) {
    CHECK_EQ(baslaticiYap(Platform::WINDOWS)->ad(), std::string("Windows"));
    CHECK_EQ(baslaticiYap(Platform::LINUX)->ad(), std::string("Linux"));
}
