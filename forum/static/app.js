// Forum arayüz yardımcıları. Satır içi betik yok (içerik güvenlik politikası: script-src 'self').
(function () {
  "use strict";
  // Uygulamanın kök yolu: sunucuda "", tarayıcı sürümünde (GitHub Pages) ör. "/YZM327-Odevler/app"
  var KOK = document.body.getAttribute("data-kok") || "";

  // Açılır menüler (hesap, konu filtresi): dışarı tıklanınca kapansın
  document.addEventListener("click", function (e) {
    document.querySelectorAll(".hesap-menu[open], .acilir-filtre[open]").forEach(function (m) {
      if (!m.contains(e.target)) m.removeAttribute("open");
    });
  });

  // Toplu gizleme ("tartışmanın bir kısmı"): seçili mesaj sayısı ve seçimi temizleme
  var seciliSayi = document.querySelector("[data-secili-sayi]");
  function sayiyiGuncelle() {
    if (seciliSayi) seciliSayi.textContent = document.querySelectorAll(".toplu-sec:checked").length;
  }
  document.addEventListener("change", function (e) {
    if (e.target.classList && e.target.classList.contains("toplu-sec")) sayiyiGuncelle();
  });
  document.querySelectorAll("[data-secimi-temizle]").forEach(function (d) {
    d.addEventListener("click", function () {
      document.querySelectorAll(".toplu-sec:checked").forEach(function (k) { k.checked = false; });
      sayiyiGuncelle();
    });
  });

  // Onay isteyen düğmeler: data-onay="Emin misin?"
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-onay]");
    if (el && !window.confirm(el.getAttribute("data-onay"))) e.preventDefault();
  });

  // Seçim değişince formu gönder
  document.querySelectorAll("[data-otomatik-gonder]").forEach(function (el) {
    el.addEventListener("change", function () { el.form.submit(); });
  });

  // Panoya kopyala: data-kopyala="#hedef"
  document.querySelectorAll("[data-kopyala]").forEach(function (dugme) {
    dugme.addEventListener("click", function () {
      var hedef = document.querySelector(dugme.getAttribute("data-kopyala"));
      if (!hedef || !navigator.clipboard) return;
      navigator.clipboard.writeText(hedef.textContent.trim()).then(function () {
        var eski = dugme.textContent;
        dugme.textContent = "Kopyalandı ✓";
        setTimeout(function () { dugme.textContent = eski; }, 1500);
      });
    });
  });

  // İl seçilince ilçeleri doldur
  document.querySelectorAll(".konum-secici").forEach(function (kutu) {
    var ilceler = JSON.parse(kutu.dataset.ilceler || "{}");
    var ilSec = kutu.querySelector(".il-sec");
    var ilceSec = kutu.querySelector(".ilce-sec");
    var secili = kutu.dataset.seciliIlce;
    function doldur() {
      var liste = ilceler[ilSec.value] || [];
      ilceSec.innerHTML = "";
      var bos = document.createElement("option");
      bos.value = "";
      bos.textContent = liste.length ? "— ilçe seç (isteğe bağlı) —" : "— (bu il için ilçe listesi yok) —";
      ilceSec.appendChild(bos);
      liste.forEach(function (ilce) {
        var o = document.createElement("option");
        o.value = ilce.id;
        o.textContent = ilce.ad;
        if (String(ilce.id) === secili) o.selected = true;
        ilceSec.appendChild(o);
      });
      ilceSec.disabled = liste.length === 0;
    }
    ilSec.addEventListener("change", function () { secili = ""; doldur(); });
    doldur();
  });

  // Oy devri formu: kapsama göre kategori/konu alanı
  document.querySelectorAll(".devir-formu").forEach(function (form) {
    var sec = form.querySelector(".kapsam-sec");
    function guncelle() {
      ["KATEGORI", "KONU"].forEach(function (k) {
        form.querySelectorAll(".kapsam-" + k).forEach(function (el) { el.classList.toggle("gizle", sec.value !== k); });
      });
    }
    sec.addEventListener("change", guncelle);
    guncelle();
  });

  // Toplu bildirim formu: hedefe göre il/ilçe ya da alan seçimi
  document.querySelectorAll(".hedef-formu").forEach(function (form) {
    function guncelle() {
      var secili = form.querySelector("input[name=hedef]:checked");
      ["KONUM", "UZMAN"].forEach(function (h) {
        form.querySelectorAll(".hedef-" + h).forEach(function (el) { el.classList.toggle("gizle", !secili || secili.value !== h); });
      });
    }
    form.querySelectorAll("input[name=hedef]").forEach(function (r) { r.addEventListener("change", guncelle); });
    guncelle();
  });

  // Tasarı formu: yönetmelik denetimi önizlemesi
  document.querySelectorAll("form[data-denetim]").forEach(function (form) {
    var dugme = form.querySelector("[data-denetle]");
    var kutu = form.querySelector(".denetim-onizleme");
    if (!dugme || !kutu) return;
    dugme.addEventListener("click", function () {
      var veri = new URLSearchParams(new FormData(form));
      if (form.dataset.ust) veri.set("ust_id", form.dataset.ust);
      dugme.disabled = true;
      kutu.textContent = "Denetleniyor…";
      fetch(KOK + "/api/v1/denetim", {
        method: "POST", body: veri, credentials: "same-origin",
        headers: { "X-CSRF-Token": form.querySelector("input[name=csrf]").value }
      }).then(function (y) { return y.json().then(function (j) { return { ok: y.ok, j: j }; }); })
        .then(function (s) { goster(kutu, s.ok ? s.j : null, s.ok ? null : s.j.hata); })
        .catch(function () { goster(kutu, null, "Denetim yapılamadı; bağlantını kontrol et."); })
        .finally(function () { dugme.disabled = false; });
    });
  });

  function goster(kutu, rapor, hata) {
    kutu.innerHTML = "";
    if (hata) {
      var p = document.createElement("p");
      p.className = "uyari hata";
      p.textContent = hata;
      kutu.appendChild(p);
      return;
    }
    var bas = document.createElement("p");
    var engel = rapor.engel.length, uyari = rapor.uyarilar.length;
    bas.innerHTML = "<strong>Yönetmelik denetimi</strong> ";
    var puan = document.createElement("span");
    puan.className = "puan";
    puan.textContent = "%" + rapor.puan;
    bas.appendChild(puan);
    var durum = document.createElement("span");
    durum.className = "rozet " + (engel ? "teklif-ret" : uyari ? "teklif-acik" : "teklif-kabul");
    durum.textContent = engel ? "Engel var: gönderilemez" : uyari ? uyari + " uyarı" : "Temiz";
    bas.appendChild(document.createTextNode(" "));
    bas.appendChild(durum);
    kutu.appendChild(bas);
    var ul = document.createElement("ul");
    ul.className = "kontrol-listesi";
    rapor.bulgular.forEach(function (b) {
      if (b.ciddiyet === "KAPALI") return;
      var li = document.createElement("li");
      li.className = b.gecti ? "tamam" : (b.ciddiyet === "ENGEL" ? "eksik" : "uyari-madde");
      var s = document.createElement("strong");
      s.textContent = b.kod + " " + b.baslik + ": ";
      li.appendChild(s);
      li.appendChild(document.createTextNode(b.mesaj));
      ul.appendChild(li);
    });
    kutu.appendChild(ul);
  }

  // Uygulama (PWA): service worker kaydı
  // Tarayıcı sürümünde (data-sw="0") sayfaları kabuğun service worker'ı sunar; ikinci bir kayıt onu ezer.
  if (document.body.getAttribute("data-sw") !== "0" && "serviceWorker" in navigator && window.isSecureContext) {
    navigator.serviceWorker.register(KOK + "/sw.js", { scope: KOK + "/" }).catch(function () {});
  }

  // Android uygulaması (mobil/): geri tuşu önce sayfa geçmişinde geri gider, geçmiş bitince uygulamayı kapatır
  var cap = window.Capacitor;
  var yerel = !!(cap && cap.isNativePlatform && cap.isNativePlatform() && cap.Plugins);
  if (yerel && cap.Plugins.App) {
    cap.Plugins.App.addListener("backButton", function (olay) {
      if (olay.canGoBack) history.back(); else cap.Plugins.App.exitApp();
    });
  }
  // Uygulamada bildirime dokununca ilgili sayfayı aç
  if (yerel && cap.Plugins.PushNotifications) {
    cap.Plugins.PushNotifications.addListener("pushNotificationActionPerformed", function (a) {
      var url = a.notification && a.notification.data && a.notification.data.url;
      if (url && url.charAt(0) === "/") location.href = url;
    });
  }

  // "Bu cihaza kur" düğmesi: tarayıcı kurulumu destekliyorsa görünür
  var kurulum = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    kurulum = e;
    document.querySelectorAll("[data-uygulama-kur]").forEach(function (d) { d.classList.remove("gizle"); });
  });
  document.querySelectorAll("[data-uygulama-kur]").forEach(function (d) {
    d.addEventListener("click", function () {
      if (!kurulum) return;
      kurulum.prompt();
      kurulum = null;
      d.classList.add("gizle");
    });
  });

  // Görünüm seçici: Otomatik (cihaz ayarı) / Açık / Koyu; seçim bu cihazda saklanır (tema.js sayfa açılırken uygular)
  var temaDugmeleri = document.querySelectorAll("[data-tema-sec]");
  function temaGoster() {
    var t = document.documentElement.getAttribute("data-tema") || "otomatik";
    temaDugmeleri.forEach(function (d) { d.setAttribute("aria-pressed", d.getAttribute("data-tema-sec") === t ? "true" : "false"); });
  }
  temaDugmeleri.forEach(function (d) {
    d.addEventListener("click", function () {
      var t = d.getAttribute("data-tema-sec");
      if (t === "otomatik") document.documentElement.removeAttribute("data-tema");
      else document.documentElement.setAttribute("data-tema", t);
      try { if (t === "otomatik") localStorage.removeItem("tema"); else localStorage.setItem("tema", t); } catch (e) { /* saklanamazsa bu sayfada geçerli */ }
      temaGoster();
    });
  });
  temaGoster();

  // Anlık bildirim: Panelim › Bildirimler'deki "Bu cihazda aç / kapat" kutusu
  document.querySelectorAll("[data-anlik]").forEach(function (kutu) {
    var yazi = kutu.querySelector(".anlik-durum");
    var ac = kutu.querySelector("[data-anlik-ac]");
    var kapat = kutu.querySelector("[data-anlik-kapat]");
    var csrf = kutu.getAttribute("data-csrf");
    function yaz(m) { yazi.textContent = m; }
    function goster(acik) { ac.classList.toggle("gizle", acik); kapat.classList.toggle("gizle", !acik); }
    function gonder(yol, veri) {
      return fetch(yol, { method: "POST", credentials: "same-origin", body: JSON.stringify(veri),
                          headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf } })
        .then(function (y) { return y.json().then(function (j) { if (!y.ok) throw new Error(j.hata || "İşlem yapılamadı."); return j; }); });
    }
    function hata(e) { yaz(e && e.message ? e.message : "İşlem yapılamadı."); }

    fetch(KOK + "/api/v1/anlik", { credentials: "same-origin" }).then(function (y) { return y.json(); }).then(function (bilgi) {
      // 1) Android uygulaması: Firebase (FCM)
      var push = yerel && cap.Plugins.PushNotifications;
      if (push) {
        if (!bilgi.fcm) { yaz("Uygulama bildirimleri sunucuda henüz ayarlanmadı (mobil/BENIOKU.md, “Anlık bildirim”)."); return; }
        var kayitli = localStorage.getItem("anlik-fcm");
        push.checkPermissions().then(function (iz) {
          var acik = iz.receive === "granted" && !!kayitli;
          goster(acik);
          yaz(acik ? "Bu telefonda bildirimler açık." : "Bu telefonda bildirimler kapalı.");
        });
        push.addListener("registration", function (t) {
          gonder(KOK + "/api/v1/anlik/abone", { tur: "FCM", token: t.value, cihaz: "Android uygulaması" }).then(function () {
            localStorage.setItem("anlik-fcm", t.value);
            goster(true);
            yaz("Bu telefonda bildirimler açık.");
          }).catch(hata);
        });
        push.addListener("registrationError", function () { yaz("Telefon bildirim servisine kaydolamadı."); });
        ac.addEventListener("click", function () {
          push.requestPermissions().then(function (iz) {
            if (iz.receive !== "granted") { yaz("Bildirim izni verilmedi; telefonun ayarlarından açabilirsin."); return; }
            push.register();
          });
        });
        kapat.addEventListener("click", function () {
          gonder(KOK + "/api/v1/anlik/ayril", { adres: localStorage.getItem("anlik-fcm") }).then(function () {
            localStorage.removeItem("anlik-fcm");
            if (push.unregister) push.unregister();
            goster(false);
            yaz("Bu telefonda bildirimler kapalı.");
          }).catch(hata);
        });
        return;
      }

      // 2) Tarayıcı ve ana ekrana eklenen web uygulaması: Web Push
      if (!("serviceWorker" in navigator) || !("PushManager" in window)) { yaz("Bu tarayıcı anlık bildirimi desteklemiyor."); return; }
      if (!window.isSecureContext) { yaz("Anlık bildirim için site HTTPS adresinden açılmalı (bilgisayarda http://127.0.0.1 de olur)."); return; }
      if (!bilgi.web) { yaz("Sunucuda anlık bildirim kapalı (pip install pywebpush)."); return; }
      navigator.serviceWorker.ready.then(function (kayit) {
        kayit.pushManager.getSubscription().then(function (ab) {
          goster(!!ab);
          yaz(ab ? "Bu cihazda bildirimler açık." : "Bu cihazda bildirimler kapalı.");
        });
        ac.addEventListener("click", function () {
          Notification.requestPermission().then(function (izin) {
            if (izin !== "granted") { yaz("Bildirim izni verilmedi; tarayıcının site ayarlarından açabilirsin."); return; }
            var ham = atob(bilgi.vapid.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((bilgi.vapid.length + 3) % 4));
            var anahtar = new Uint8Array(ham.length);
            for (var i = 0; i < ham.length; i++) anahtar[i] = ham.charCodeAt(i);
            return kayit.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: anahtar }).then(function (ab) {
              return gonder(KOK + "/api/v1/anlik/abone", { tur: "WEB", abonelik: ab.toJSON(), cihaz: navigator.userAgent.slice(0, 80) });
            }).then(function () { goster(true); yaz("Bu cihazda bildirimler açık."); });
          }).catch(hata);
        });
        kapat.addEventListener("click", function () {
          kayit.pushManager.getSubscription().then(function (ab) {
            if (!ab) return;
            return gonder(KOK + "/api/v1/anlik/ayril", { adres: ab.endpoint }).then(function () { return ab.unsubscribe(); });
          }).then(function () { goster(false); yaz("Bu cihazda bildirimler kapalı."); }).catch(hata);
        });
      });
    }).catch(function () { yaz("Bildirim ayarı okunamadı."); });
  });
})();
