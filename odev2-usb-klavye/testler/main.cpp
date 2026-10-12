// Tüm testleri çalıştıran giriş noktası. Testler kendilerini TEST(...) ile
// kaydettiği için burada yalnızca mt::calistir() çağrılır.
#include "mini_test.h"

int main() {
    std::cout << "=== USB Makro Klavye — Birim Testleri ===\n";
    return mt::calistir();
}
