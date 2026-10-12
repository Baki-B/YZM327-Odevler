#pragma once
// Klavyedeki özel (yazı olmayan) ve değiştirici (modifier) tuşlar.
// Çekirdek bu soyut tuş tanımlarını kullanır; her bir tuşun gerçek USB
// koduna çevrilmesi donanım bağdaştırıcısının işidir (bkz. arduino/).
namespace makro {

enum class OzelTus {
    ENTER,
    TAB,
    ESC,
    BOSLUK,
    GUI,    // Windows / Super (⊞) tuşu
    CTRL,
    ALT,
    SHIFT,
};

// Günlük ve testlerde okunur çıktı için tuşun adı.
const char* ozelTusAdi(OzelTus tus);

}  // namespace makro
