#pragma once
// Dışarıdan bağımlılık istemeyen küçük bir test çatısı (Agora'nın "ağır
// bağımlılık yok" anlayışıyla uyumlu). TEST(...) ile tanımlanan testler kendini
// kaydeder; mt::calistir() hepsini çalıştırır ve başarısızlıkta 1 döner (CI uyumlu).
#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace mt {

struct BasarisizlikHatasi : std::runtime_error {
    using std::runtime_error::runtime_error;
};

struct TestKaydi {
    std::string ad;
    std::function<void()> fn;
};

inline std::vector<TestKaydi>& kayitlar() {
    static std::vector<TestKaydi> v;
    return v;
}

struct Ekleyici {
    Ekleyici(const std::string& ad, std::function<void()> fn) {
        kayitlar().push_back({ad, std::move(fn)});
    }
};

template <class A, class B>
void esitMi(const A& a, const B& b, const char* ifade, const char* dosya, int satir) {
    if (!(a == b)) {
        std::ostringstream os;
        os << dosya << ":" << satir << "  BASARISIZ: " << ifade
           << "  (sol=" << a << ", sag=" << b << ")";
        throw BasarisizlikHatasi(os.str());
    }
}

inline void dogruMu(bool kosul, const char* ifade, const char* dosya, int satir) {
    if (!kosul) {
        std::ostringstream os;
        os << dosya << ":" << satir << "  BASARISIZ: " << ifade;
        throw BasarisizlikHatasi(os.str());
    }
}

inline int calistir() {
    int gecen = 0, kalan = 0;
    for (auto& t : kayitlar()) {
        try {
            t.fn();
            std::cout << "  [GECTI] " << t.ad << "\n";
            ++gecen;
        } catch (const std::exception& e) {
            std::cout << "  [KALDI] " << t.ad << "\n          " << e.what() << "\n";
            ++kalan;
        }
    }
    std::cout << "\n" << gecen << " gecti, " << kalan << " kaldi, toplam "
              << (gecen + kalan) << " test.\n";
    return kalan == 0 ? 0 : 1;
}

}  // namespace mt

#define TEST(ad)                                     \
    static void ad();                                \
    static ::mt::Ekleyici _mt_ekleyici_##ad(#ad, ad); \
    static void ad()

#define CHECK(kosul) ::mt::dogruMu((kosul), #kosul, __FILE__, __LINE__)
#define CHECK_EQ(a, b) ::mt::esitMi((a), (b), #a " == " #b, __FILE__, __LINE__)
