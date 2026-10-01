// Görünüm tercihi (Otomatik / Açık / Koyu). Sayfa çizilmeden önce çalışsın diye <head> içinde, defer olmadan yüklenir.
// "otomatik" ya da kayıt yoksa cihazın ayarı (prefers-color-scheme) geçerlidir.
(function () {
  try {
    var t = localStorage.getItem("tema");
    if (t === "acik" || t === "koyu") document.documentElement.setAttribute("data-tema", t);
  } catch (e) { /* gizli pencere vb.: cihaz ayarı geçerli */ }
})();
